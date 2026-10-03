"""Teacher-neutral semantic evidence contract for Pretty Pink SUL.

Research-only. Teacher outputs are observations, never playback instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

SOURCE_FAMILIES = (
    "vocals",
    "drums_percussion",
    "bass",
    "guitars",
    "keys_synths",
    "strings_orchestra",
    "winds_brass",
    "sampled_electronic",
)

ESSENTIA_INSTRUMENT_TO_FAMILY = {
    "voice": "vocals",
    "beat": "drums_percussion", "bongo": "drums_percussion", "drummachine": "drums_percussion",
    "drums": "drums_percussion", "percussion": "drums_percussion",
    "acousticbassguitar": "bass", "bass": "bass", "doublebass": "bass",
    "acousticguitar": "guitars", "classicalguitar": "guitars", "electricguitar": "guitars", "guitar": "guitars",
    "electricpiano": "keys_synths", "keyboard": "keys_synths", "organ": "keys_synths", "pad": "keys_synths",
    "piano": "keys_synths", "pipeorgan": "keys_synths", "rhodes": "keys_synths", "synthesizer": "keys_synths",
    "cello": "strings_orchestra", "harp": "strings_orchestra", "orchestra": "strings_orchestra",
    "strings": "strings_orchestra", "viola": "strings_orchestra", "violin": "strings_orchestra",
    "brass": "winds_brass", "clarinet": "winds_brass", "flute": "winds_brass", "harmonica": "winds_brass",
    "horn": "winds_brass", "oboe": "winds_brass", "saxophone": "winds_brass", "trombone": "winds_brass", "trumpet": "winds_brass",
    "computer": "sampled_electronic", "sampler": "sampled_electronic",
}

SEPARATOR_TO_FAMILY = {
    "vocals": "vocals", "drums": "drums_percussion", "percussion": "drums_percussion",
    "bass": "bass", "guitar": "guitars", "piano": "keys_synths", "keys": "keys_synths",
    "synth": "keys_synths", "strings": "strings_orchestra", "wind": "winds_brass",
    "brass": "winds_brass", "other": "sampled_electronic",
}

@dataclass(frozen=True)
class TeacherObservation:
    name: str
    kind: str
    scores: Mapping[str, float]
    reliability: float = 1.0

    def clamped_reliability(self) -> float:
        return min(1.0, max(0.0, float(self.reliability)))


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, float(x)))


def map_instrument_tags(scores: Mapping[str, float]) -> Dict[str, float]:
    """Map semantic instrument tags to broad families using max evidence.

    This intentionally avoids pretending correlated instrument labels are independent.
    """
    out = {family: 0.0 for family in SOURCE_FAMILIES}
    for label, score in scores.items():
        family = ESSENTIA_INSTRUMENT_TO_FAMILY.get(str(label).lower())
        if family:
            out[family] = max(out[family], _clamp01(score))
    return out


def map_separator_activity(scores: Mapping[str, float]) -> Dict[str, float]:
    out = {family: 0.0 for family in SOURCE_FAMILIES}
    for label, score in scores.items():
        family = SEPARATOR_TO_FAMILY.get(str(label).lower())
        if family:
            out[family] = max(out[family], _clamp01(score))
    return out
