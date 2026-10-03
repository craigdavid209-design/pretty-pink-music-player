"""Pretty Pink Vocal Intelligibility Witness (VIW), research-only.

Predicts risk that lyrics may be hard to parse from mixture evidence. It does
not transcribe lyrics, identify a singer, or change playback. Vocal presence is
not treated as lyric intelligibility.
"""
from dataclasses import dataclass
from production_context_witness import ProductionEvidence, understand


def _c(x):
    return max(0.0, min(1.0, float(x)))


@dataclass(frozen=True)
class VocalIntelligibilitySnapshot:
    label: str
    risk: float
    confidence: float
    reason: str
    scene_restraint_veto: bool


def evaluate(e: ProductionEvidence) -> VocalIntelligibilitySnapshot:
    if not e.valid() or e.confidence < 0.50 or e.vocal_compatible < 0.45:
        return VocalIntelligibilitySnapshot(
            "UNAVAILABLE", 0.0, _c(e.confidence),
            "vocal-compatible evidence is insufficient or uncertain", False)

    # Deliberately a risk score, not a word-correct estimate.
    risk = _c(e.vocal_compatible * (
        0.38 * e.masking_burden
        + 0.28 * e.temporal_smear
        + 0.20 * e.spatial_layering
        + 0.14 * (1.0 - e.articulation_support)))
    context = understand(e)

    if risk < 0.30:
        label = "LOW_OBSERVED_RISK"
    elif risk < 0.42:
        label = "ELEVATED_RISK"
    else:
        votes = sum([
            e.masking_burden >= 0.58,
            e.temporal_smear >= 0.62,
            e.spatial_layering >= 0.55,
            e.articulation_support <= 0.42,
        ])
        label = "HIGH_COMBINED_RISK" if votes >= 2 else "HIGH_SINGLE_AXIS_RISK"

    # VIW can only prevent SUL from taking existing optional help away.
    # It never creates positive authority or changes Core/targets/TELG.
    veto = e.confidence >= 0.65 and risk >= 0.42
    reason = (
        f"{context.label}; masking={e.masking_burden:.3f}; "
        f"smear={e.temporal_smear:.3f}; layering={e.spatial_layering:.3f}; "
        f"articulation={e.articulation_support:.3f}")
    return VocalIntelligibilitySnapshot(label, risk, e.confidence, reason, veto)
