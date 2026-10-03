#!/usr/bin/env python3
"""Pretty Pink Comfort Priority Interlock v1 — research contract.

This module does not process audio. It encodes one narrow authority rule discovered
while auditing 2.0.112 after louder-speaker listening:

- Scene v3 may normally move an existing negative Balance cut toward zero.
- If the *existing* SpectralMarginPolicy has already earned non-zero confidence
  from persistent energetic presence + upper-air evidence, Scene must not relax
  that Balance cut.
- QDI keeps the existing Scene factor unchanged.

This creates no new attenuation authority: the strongest possible Balance request
is exactly the already-planned pre-Scene cut.
"""
from __future__ import annotations


def clamp_scene_factor(value: float) -> float:
    if not isinstance(value, (int, float)):
        return 1.0
    if value != value:  # NaN
        return 1.0
    return max(0.82, min(1.0, float(value)))


def balance_scene_factor(scene_factor: float, spectral_available: bool,
                         spectral_confidence: float) -> float:
    """Return the factor Scene is allowed to apply to a negative Balance cut.

    Existing SpectralMarginPolicy only emits positive confidence after its own
    strict persistence / energetic / upper-air gates pass. In that case comfort
    gets priority and Scene loses its *reduction* authority for Balance only.
    """
    scene = clamp_scene_factor(scene_factor)
    if not spectral_available:
        return scene
    if not isinstance(spectral_confidence, (int, float)):
        return scene
    confidence = float(spectral_confidence)
    if confidence != confidence or confidence < 0.0 or confidence > 1.0:
        return scene
    return 1.0 if confidence > 0.0 else scene


def qdi_scene_factor(scene_factor: float) -> float:
    """QDI behavior is intentionally unchanged from current Scene v3."""
    return clamp_scene_factor(scene_factor)


def apply_balance_cut(original_cut_db: float, factor: float) -> float:
    """Reference monotonic projection used only by research tests."""
    if not isinstance(original_cut_db, (int, float)):
        return original_cut_db
    cut = float(original_cut_db)
    if cut != cut or cut > 0.0:
        return cut
    return cut * clamp_scene_factor(factor)


if __name__ == "__main__":
    print("Comfort Priority Interlock v1: research-only policy contract")
