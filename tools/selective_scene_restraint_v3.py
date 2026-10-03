"""Pretty Pink selective Scene Restraint v3 research reference.

Fixes 2.0.110's over-broad behavior: profile labels carry ZERO whole-track
authority. Restraint is earned only by a local, multi-cue, salient event.
Vocal-intelligibility risk can veto restraint, never add correction authority.
"""
from dataclasses import dataclass
from math import isfinite


def _c(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(x)))


@dataclass(frozen=True)
class SceneEvent:
    time_s: float
    strength: float
    support: int
    salience: float

    def valid(self):
        return (
            isfinite(self.time_s) and self.time_s >= 0
            and 0 <= self.strength <= 1
            and 0 <= self.salience <= 1
            and 0 <= self.support <= 6)


def qualifies(e: SceneEvent) -> bool:
    # Busy/global motion is insufficient. Require local salience + independent cues.
    return e.valid() and e.support >= 2 and e.strength >= 0.16 and e.salience >= 0.04


def event_floor(e: SceneEvent) -> float:
    if not qualifies(e):
        return 1.0
    strength = _c((e.strength - 0.16) / 0.34)
    salience = _c((e.salience - 0.04) / 0.20)
    consensus = _c((e.support - 2) / 3)
    depth = 0.06 + 0.07 * strength + 0.03 * salience + 0.02 * consensus
    return _c(1.0 - depth, 0.82, 1.0)


def factor_at(events, position_s: float, *, enabled=True, vocal_veto=False,
              production_ambiguity=0.0, radius_s=2.5) -> float:
    if not enabled or position_s < 0 or vocal_veto:
        return 1.0
    if production_ambiguity >= 0.72:
        return 1.0

    factor = 1.0
    for event in events:
        if not qualifies(event):
            continue
        distance = abs(position_s - event.time_s)
        if distance >= radius_s:
            continue
        x = distance / radius_s
        smooth = x * x * (3 - 2 * x)
        floor = event_floor(event)
        local = floor + (1.0 - floor) * smooth
        factor = min(factor, local)
    return _c(factor, 0.82, 1.0)


def balance_cut(cut_db: float, factor: float) -> float:
    return cut_db * _c(factor, 0.82, 1.0) if isfinite(cut_db) and cut_db <= 0 else cut_db


def qdi_lift(lift_db: float, factor: float) -> float:
    return lift_db * _c(factor, 0.82, 1.0) if isfinite(lift_db) and lift_db > 0 else lift_db
