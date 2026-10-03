#!/usr/bin/env python3
"""Pretty Pink Comfort Priority Interlock v1.1 — research contract.

This module does not process audio. It encodes one narrow authority rule discovered
while auditing 2.0.112 after louder-speaker listening and comparing current source
against the human-ear-approved 2.0.68 TELG baseline:

- Scene v3 may normally move an existing negative Balance cut toward zero.
- If an *existing* comfort system has already earned protection — either
  SpectralMarginPolicy positive confidence or TELG additional delivered-level
  reserve above the spectral floor — Scene must not relax that Balance cut.
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


def comfort_earned(spectral_available: bool, spectral_confidence: float,
                   telg_extra_reserve: bool) -> bool:
    """Existing comfort evidence only; malformed evidence never invents authority."""
    spectral = False
    if spectral_available and isinstance(spectral_confidence, (int, float)):
        confidence = float(spectral_confidence)
        spectral = confidence == confidence and 0.0 < confidence <= 1.0
    return spectral or bool(telg_extra_reserve)


def balance_scene_factor(scene_factor: float, spectral_available: bool,
                         spectral_confidence: float,
                         telg_extra_reserve: bool = False) -> float:
    """Return the factor Scene may apply to an already-negative Balance cut.

    Comfort can veto Scene's *reduction* authority only. It cannot create a cut,
    deepen a cut, alter TELG/Spectral thresholds, or affect QDI.
    """
    scene = clamp_scene_factor(scene_factor)
    return 1.0 if comfort_earned(spectral_available, spectral_confidence,
                                 telg_extra_reserve) else scene


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
    print("Comfort Priority Interlock v1.1: research-only policy contract")
