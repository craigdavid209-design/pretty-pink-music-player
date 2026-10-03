"""Pretty Pink Scene/Balance Comfort Restore v1 — research contract.

This is NOT a DSP, EQ, limiter, compressor, or new attenuation model.
It expresses one authority-ordering rule:

- mature Balance attenuation remains authoritative;
- Scene may continue reducing positive QDI lift;
- Scene must not make an existing negative Balance cut lighter.

The helper exists for research/tests and must not be mistaken for playback code.
"""


def clamp01(x: float) -> float:
    if x != x:
        return 1.0
    return max(0.0, min(1.0, x))


def old_scene_balance_cut(original_cut_db: float, scene_factor: float) -> float:
    """2.0.111/2.0.112 behavior: Scene can lighten Balance attenuation."""
    if original_cut_db > 0.0:
        return original_cut_db
    f = max(0.82, min(1.0, scene_factor))
    return original_cut_db * f


def comfort_restored_balance_cut(original_cut_db: float, scene_factor: float) -> float:
    """Proposed authority order: preserve the already-approved Balance cut exactly."""
    del scene_factor
    return original_cut_db


def scene_qdi_lift(original_lift_db: float, scene_factor: float) -> float:
    """Scene keeps its current one-way authority over optional positive QDI lift."""
    if original_lift_db <= 0.0:
        return original_lift_db
    f = max(0.82, min(1.0, scene_factor))
    return original_lift_db * f
