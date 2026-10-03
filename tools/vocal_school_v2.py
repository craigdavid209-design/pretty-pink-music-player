"""Pretty Pink Vocal School v2 research witness.

Pure read-only reasoning over normalized evidence. No PCM/gain/EQ authority.
Every claim is a mixture hypothesis and can abstain.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Tuple
import math


def _u(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _ok01(x: float) -> bool:
    return math.isfinite(float(x)) and 0.0 <= float(x) <= 1.0


class VocalLabel(str, Enum):
    UNAVAILABLE = "UNAVAILABLE"
    LIKELY_VOCAL_LOW_RISK = "LIKELY_VOCAL_LOW_RISK"
    LIKELY_VOCAL_ELEVATED_RISK = "LIKELY_VOCAL_ELEVATED_RISK"
    LIKELY_VOCAL_HIGH_COMBINED_RISK = "LIKELY_VOCAL_HIGH_COMBINED_RISK"


@dataclass(frozen=True)
class VocalResult:
    label: VocalLabel
    presence: float
    confidence: float
    articulation_clarity: float
    masking_burden: float
    production_smear: float
    layering: float
    risk: float
    ambiguity: float
    support_routes: int

    @property
    def available(self) -> bool:
        return self.label is not VocalLabel.UNAVAILABLE

    @property
    def authority(self) -> float:
        return 0.0


_REQUIRED = (
    "active", "body", "vowel", "articulation_band", "air", "tonal",
    "modulation", "flux", "center", "broadband_density", "side_activity",
    "persistence",
)


def evaluate(e: Mapping[str, float]) -> VocalResult:
    if any(k not in e or not _ok01(e[k]) for k in _REQUIRED):
        return VocalResult(VocalLabel.UNAVAILABLE, 0, 0, 0, 0, 0, 0, 0, 1, 0)

    active = float(e["active"]); body = float(e["body"]); vowel = float(e["vowel"])
    art_band = float(e["articulation_band"]); air = float(e["air"]); tonal = float(e["tonal"])
    mod = float(e["modulation"]); flux = float(e["flux"]); center = float(e["center"])
    density = float(e["broadband_density"]); side = float(e["side_activity"])
    persistence = float(e["persistence"])

    spectral_route = _u(.36 * vowel + .22 * body + .22 * art_band + .20 * tonal)
    temporal_route = _u(.43 * mod + .32 * flux + .25 * persistence)
    articulation_route = _u(.48 * art_band + .27 * flux + .25 * mod)
    voiced_route = _u(.42 * body + .34 * tonal + .24 * vowel)
    breathy_route = _u(.40 * vowel + .28 * art_band + .20 * mod + .12 * (1.0 - tonal))

    routes = (spectral_route, temporal_route, articulation_route, voiced_route, breathy_route)
    support_routes = sum(r >= .43 for r in routes)
    ordered = sorted(routes, reverse=True)
    agreement = .58 * ordered[1] + .42 * ordered[2]
    presence = active * _u(.72 * agreement + .18 * persistence + .10 * max(center, .35))
    confidence = active * _u(.28 * ordered[1] + .24 * ordered[2] + .20 * persistence
                             + .16 * min(1.0, support_routes / 3.0) + .12 * max(center, .30))

    articulation_clarity = _u(.46 * art_band + .28 * flux + .20 * mod + .06 * air)
    layering = _u(.50 * side + .22 * (1.0 - center) + .18 * density + .10 * (1.0 - tonal))
    production_smear = _u(.38 * (1.0 - flux) + .27 * (1.0 - mod) + .21 * density + .14 * layering)
    masking_burden = _u(.42 * density + .24 * side + .18 * (1.0 - center) + .16 * art_band)
    risk = presence * _u(.31 * masking_burden + .25 * production_smear
                         + .17 * layering + .27 * (1.0 - articulation_clarity))
    complexity = _u(.36 * density + .26 * layering + .22 * production_smear + .16 * masking_burden)
    ambiguity = _u((1.0 - confidence) * .58 + complexity * .27 + (1.0 - presence) * .15)

    spectral_support = max(spectral_route, voiced_route, breathy_route) >= .45
    dynamic_support = max(temporal_route, articulation_route) >= .40
    if active < .28 or support_routes < 2 or not spectral_support or not dynamic_support \
            or presence < .38 or confidence < .43:
        return VocalResult(VocalLabel.UNAVAILABLE, presence, confidence, articulation_clarity,
                           masking_burden, production_smear, layering, risk, ambiguity,
                           support_routes)

    high_axes = sum((masking_burden >= .58, production_smear >= .62,
                     layering >= .55, articulation_clarity <= .38))
    if risk >= .40 and high_axes >= 2 and confidence >= .58:
        label = VocalLabel.LIKELY_VOCAL_HIGH_COMBINED_RISK
    elif risk >= .27:
        label = VocalLabel.LIKELY_VOCAL_ELEVATED_RISK
    else:
        label = VocalLabel.LIKELY_VOCAL_LOW_RISK
    return VocalResult(label, presence, confidence, articulation_clarity,
                       masking_burden, production_smear, layering, risk,
                       ambiguity, support_routes)


def production_context(e: Mapping[str, float]) -> Tuple[str, ...]:
    """Descriptive context only; never a defect diagnosis or authority request."""
    if any(k not in e or not _ok01(e[k]) for k in _REQUIRED):
        return ("UNAVAILABLE",)
    tags = []
    density = float(e["broadband_density"]); side = float(e["side_activity"])
    center = float(e["center"]); flux = float(e["flux"]); mod = float(e["modulation"])
    if density >= .62: tags.append("DENSE_MIXTURE_CONTEXT")
    if side >= .55 or center <= .42: tags.append("LAYERED_OR_WIDE_CONTEXT")
    if flux <= .30 and mod <= .34 and density >= .48: tags.append("SMEAR_OR_SUSTAINED_CONTEXT")
    if not tags: tags.append("NO_STRONG_PRODUCTION_CONTEXT_CLAIM")
    return tuple(tags)
