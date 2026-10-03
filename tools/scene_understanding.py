"""Pretty Pink Scene Understanding Layer (SUL) research reference.

This module fuses deterministic mixture descriptors with optional independent
semantic teachers. It is deliberately incapable of changing audio.

House rule: learn more without earning the right to touch more.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence
import math
import statistics

from teacher_contract import (
    SOURCE_FAMILIES,
    TeacherObservation,
    map_instrument_tags,
    map_separator_activity,
)

SUL_SCHEMA_VERSION = 1
SUL_AUTHORITY = "OBSERVE_ONLY"


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, float(x)))


def _score01(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return _clamp01((float(x) - lo) / (hi - lo))


def _safe_get(d: Mapping[str, Any], path: Sequence[str], default: float = 0.0) -> float:
    cur: Any = d
    try:
        for key in path:
            cur = cur[key]
        if cur is None:
            return default
        x = float(cur)
        return x if math.isfinite(x) else default
    except (KeyError, TypeError, ValueError):
        return default


def measured_scene(probe: Mapping[str, Any]) -> Dict[str, Any]:
    """Create claims supported by mixture measurements only.

    These descriptors may describe structure and complexity but never name a
    human, singer, or specific instrument.
    """
    side_mid = _safe_get(probe, ("stereo", "sideToMidEnergy"))
    corr = _safe_get(probe, ("stereo", "correlation"), 1.0)
    effective = _safe_get(probe, ("textureFactorization", "effectiveComponents"), 1.0)
    dominance = _safe_get(probe, ("textureFactorization", "dominantComponentFraction"), 1.0)
    regimes = int(round(_safe_get(probe, ("acousticRegimes", "bestClusterCount"), 1.0)))
    silhouette = _safe_get(probe, ("acousticRegimes", "silhouette"), 0.0)
    percussive = _safe_get(probe, ("layerEvidence", "percussiveEnergyRatio"))
    harmonic = _safe_get(probe, ("layerEvidence", "harmonicEnergyRatio"))
    residual = _safe_get(probe, ("layerEvidence", "unassignedEnergyRatio"))
    onset_rate = _safe_get(probe, ("onsetRatePerMinute",), 0.0)
    flatness = _safe_get(probe, ("spectralFlatness", "p50"), 0.0)

    flags: List[str] = []
    if side_mid >= 0.03 or corr <= 0.88:
        flags.append("STEREO_SPATIAL_STRUCTURE")
    if side_mid >= 0.12 or corr <= 0.55:
        flags.append("WIDE_OR_DECORRELATED_LAYERS")
    if effective >= 3.0 and dominance <= 0.72:
        flags.append("MULTIPLE_TEXTURE_FACTORS")
    if regimes >= 3 and silhouette >= 0.12:
        flags.append("MULTIPLE_ACOUSTIC_REGIMES")
    if percussive >= 0.08 or onset_rate >= 80.0:
        flags.append("PERSISTENT_TRANSIENT_ACTIVITY")
    if residual >= 0.10 or flatness >= 0.08:
        flags.append("NOISE_OR_INHARMONIC_TEXTURE")
    if harmonic >= 0.30:
        flags.append("STRONG_HARMONIC_STRUCTURE")

    complexity_terms = [
        _score01(side_mid, 0.01, 0.20),
        _score01(effective, 1.5, 6.0),
        _score01(max(1, regimes), 1.0, 5.0),
        _score01(onset_rate, 20.0, 180.0),
        _score01(residual + flatness, 0.02, 0.35),
    ]
    complexity = float(sum(complexity_terms) / len(complexity_terms))

    return {
        "mixtureComplexity": complexity,
        "flags": flags,
        "stereoStructure": {
            "sideToMidEnergy": side_mid,
            "leftRightCorrelation": corr,
        },
        "texture": {
            "effectiveComponents": effective,
            "dominantComponentFraction": dominance,
        },
        "regimes": {
            "countHypothesis": max(1, regimes),
            "silhouette": silhouette,
            "claim": "acoustic regimes only; not source identity",
        },
        "activity": {
            "harmonicRatio": harmonic,
            "percussiveRatio": percussive,
            "unassignedRatio": residual,
            "onsetRatePerMinute": onset_rate,
        },
    }


def _semantic_projection(obs: TeacherObservation) -> Dict[str, float]:
    kind = obs.kind.lower()
    if kind == "instrument_tags":
        return map_instrument_tags(obs.scores)
    if kind == "stem_activity":
        return map_separator_activity(obs.scores)
    if kind == "source_family":
        return {f: _clamp01(obs.scores.get(f, 0.0)) for f in SOURCE_FAMILIES}
    return {f: 0.0 for f in SOURCE_FAMILIES}


def _fuse_semantics(teachers: Sequence[TeacherObservation]) -> Dict[str, Any]:
    semantic_teachers = [t for t in teachers if t.kind.lower() in {"instrument_tags", "stem_activity", "source_family"}]
    if not semantic_teachers:
        return {
            "status": "UNAVAILABLE",
            "families": [],
            "uncertainty": "HIGH",
            "teacherCount": 0,
            "claim": "No semantic teacher evidence supplied; mixture features are not renamed as instruments.",
        }

    projected = [(t, _semantic_projection(t)) for t in semantic_teachers]
    rows = []
    disagreement_values: List[float] = []
    for family in SOURCE_FAMILIES:
        vals = []
        weights = []
        support = 0
        for teacher, scores in projected:
            v = _clamp01(scores.get(family, 0.0))
            w = max(0.05, teacher.clamped_reliability())
            vals.append(v)
            weights.append(w)
            if v >= 0.35:
                support += 1
        fused = sum(v*w for v, w in zip(vals, weights)) / max(sum(weights), 1e-9)
        spread = statistics.pstdev(vals) if len(vals) >= 2 else 0.0
        if len(vals) >= 2:
            disagreement_values.append(spread)
        status = "SUPPORTED" if fused >= 0.55 and support >= min(2, len(vals)) else "POSSIBLE" if fused >= 0.35 else "LOW_EVIDENCE"
        rows.append({
            "family": family,
            "probability": float(fused),
            "supportingTeachers": support,
            "teacherCount": len(vals),
            "disagreement": float(spread),
            "status": status,
        })

    active = [r for r in rows if r["status"] in {"SUPPORTED", "POSSIBLE"}]
    active_disagreements = [r["disagreement"] for r in rows if r["status"] in {"SUPPORTED", "POSSIBLE"}]
    mean_disagreement = sum(active_disagreements)/len(active_disagreements) if active_disagreements else (sum(disagreement_values)/len(disagreement_values) if disagreement_values else 0.0)
    max_disagreement = max(active_disagreements or disagreement_values or [0.0])
    if len(semantic_teachers) == 1:
        uncertainty = "MEDIUM_HIGH"
    elif max_disagreement >= 0.32 or mean_disagreement >= 0.28:
        uncertainty = "HIGH"
    elif max_disagreement >= 0.18 or mean_disagreement >= 0.14:
        uncertainty = "MEDIUM"
    else:
        uncertainty = "LOW_MEDIUM"

    return {
        "status": "AVAILABLE",
        "families": active,
        "uncertainty": uncertainty,
        "teacherCount": len(semantic_teachers),
        "meanTeacherDisagreement": float(mean_disagreement),
        "maxTeacherDisagreement": float(max_disagreement),
        "claim": "Broad source-family hypotheses from semantic teachers; not separated PCM and not identity recognition.",
    }


def _vocal_timbre_claim(teachers: Sequence[TeacherObservation], measured: Mapping[str, Any]) -> Dict[str, Any]:
    evidence = []
    for t in teachers:
        if t.kind.lower() == "vocal_timbres":
            p = _clamp01(t.scores.get("multipleDistinctVocalTimbres", 0.0))
            evidence.append((t.name, p, t.clamped_reliability()))

    if not evidence:
        return {
            "status": "UNAVAILABLE",
            "probability": None,
            "supportingTeachers": 0,
            "claim": "No dedicated vocal-timbre teacher evidence.",
        }

    denom = sum(max(0.05, r) for _, _, r in evidence)
    p = sum(v*max(0.05, r) for _, v, r in evidence) / max(denom, 1e-9)
    support = sum(1 for _, v, _ in evidence if v >= 0.60)
    regime_support = (
        measured["regimes"]["countHypothesis"] >= 2
        and measured["regimes"]["silhouette"] >= 0.10
    )

    if p >= 0.65 and support >= 2:
        status = "MULTIPLE_DISTINCT_VOCAL_TIMBRES"
    elif p >= 0.55 and support >= 1:
        status = "POSSIBLE_MULTIPLE_DISTINCT_VOCAL_TIMBRES"
    else:
        status = "AMBIGUOUS"

    return {
        "status": status,
        "probability": float(p),
        "supportingTeachers": support,
        "acousticRegimeCorroboration": bool(regime_support),
        "claim": "Distinct vocal timbres only; never singer identity or name.",
    }


def understand_scene(probe: Mapping[str, Any], teachers: Iterable[TeacherObservation] = ()) -> Dict[str, Any]:
    teachers = tuple(teachers)
    measured = measured_scene(probe)
    semantics = _fuse_semantics(teachers)
    vocal = _vocal_timbre_claim(teachers, measured)

    return {
        "schemaVersion": SUL_SCHEMA_VERSION,
        "layer": "Pretty Pink Scene Understanding Layer",
        "phase": "A_RESEARCH_SHADOW",
        "authority": {
            "mode": SUL_AUTHORITY,
            "enabled": False,
            "audioMutationAllowed": False,
            "playbackPlanInfluenceAllowed": False,
            "allowedActions": [],
            "rule": "Learn more without earning the right to touch more.",
        },
        "measured": measured,
        "semantic": semantics,
        "vocalTimbres": vocal,
        "provenance": {
            "teacherNames": [t.name for t in teachers],
            "teacherKinds": [t.kind for t in teachers],
            "metadataUsedForAcousticClaims": False,
            "filenameUsedForAcousticClaims": False,
        },
        "truthBoundary": [
            "Mixture measurements are measured facts or bounded structural hypotheses.",
            "Source-family labels require semantic teacher evidence.",
            "Vocal-timbre claims never imply singer identity.",
            "Uncertainty and disagreement must remain visible.",
            "This result cannot change PCM, gain, EQ, dynamics, targets, or playback plans.",
        ],
    }
