"""Pretty Pink research-only production-context witness.

Describes mixture conditions that can make vocals harder to parse. It does NOT
identify a named effect, declare a mix defective, or carry playback authority.
"""
from dataclasses import dataclass


def _c(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


@dataclass(frozen=True)
class ProductionEvidence:
    vocal_compatible: float
    articulation_support: float
    masking_burden: float
    spatial_layering: float
    temporal_smear: float
    production_density: float
    confidence: float

    def valid(self) -> bool:
        return all(0.0 <= float(v) <= 1.0 for v in self.__dict__.values())


@dataclass(frozen=True)
class ProductionContext:
    label: str
    complexity: float
    ambiguity: float
    explanation: str


def understand(e: ProductionEvidence) -> ProductionContext:
    if not e.valid() or e.confidence < 0.45:
        return ProductionContext(
            "UNAVAILABLE", 0.0, 1.0,
            "insufficient trustworthy production-context evidence")

    complexity = _c(
        0.34 * e.production_density
        + 0.25 * e.masking_burden
        + 0.22 * e.temporal_smear
        + 0.19 * e.spatial_layering)
    ambiguity = _c(
        (1.0 - e.confidence) * 0.55
        + min(e.spatial_layering, e.temporal_smear) * 0.20
        + (1.0 - e.vocal_compatible) * 0.25)

    high = []
    if e.masking_burden >= 0.62:
        high.append("masking-heavy")
    if e.temporal_smear >= 0.68:
        high.append("temporally smeared")
    if e.spatial_layering >= 0.60:
        high.append("spatially layered")
    if e.production_density >= 0.70:
        high.append("dense")

    if len(high) >= 2:
        label = "COMPLEX_PRODUCTION_CONTEXT"
    elif high:
        label = {
            "masking-heavy": "MASKING_HEAVY_CONTEXT",
            "temporally smeared": "SMEAR_HEAVY_CONTEXT",
            "spatially layered": "LAYERED_CONTEXT",
            "dense": "DENSE_CONTEXT",
        }[high[0]]
    else:
        label = "MIXTURE_CONTEXT"

    return ProductionContext(
        label,
        complexity,
        ambiguity,
        "mixture evidence only; consistent with production complexity but not proof of any named effect",
    )
