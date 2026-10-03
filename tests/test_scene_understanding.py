import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from scene_understanding import understand_scene
from teacher_contract import TeacherObservation

PROBE = {
    "file": "anything.flac",
    "stereo": {"sideToMidEnergy": 0.11, "correlation": 0.71},
    "textureFactorization": {"effectiveComponents": 4.2, "dominantComponentFraction": 0.48},
    "acousticRegimes": {"bestClusterCount": 3, "silhouette": 0.24},
    "layerEvidence": {"harmonicEnergyRatio": 0.38, "percussiveEnergyRatio": 0.14, "unassignedEnergyRatio": 0.12},
    "onsetRatePerMinute": 112.0,
    "spectralFlatness": {"p50": 0.06},
}

r0 = understand_scene(PROBE)
assert r0["authority"]["audioMutationAllowed"] is False
assert r0["authority"]["playbackPlanInfluenceAllowed"] is False
assert r0["semantic"]["status"] == "UNAVAILABLE"
assert r0["vocalTimbres"]["status"] == "UNAVAILABLE"
assert "MULTIPLE_TEXTURE_FACTORS" in r0["measured"]["flags"]

teachers = [
    TeacherObservation(
        name="essentia-mtg-jamendo-instrument",
        kind="instrument_tags",
        reliability=0.9,
        scores={"voice": 0.92, "drums": 0.88, "synthesizer": 0.79, "guitar": 0.10},
    ),
    TeacherObservation(
        name="offline-separator",
        kind="stem_activity",
        reliability=0.95,
        scores={"vocals": 0.95, "drums": 0.90, "synth": 0.70, "bass": 0.42},
    ),
]
r1 = understand_scene(PROBE, teachers)
rows = {x["family"]: x for x in r1["semantic"]["families"]}
assert rows["vocals"]["status"] == "SUPPORTED"
assert rows["drums_percussion"]["status"] == "SUPPORTED"
assert rows["keys_synths"]["status"] == "SUPPORTED"
assert r1["authority"]["allowedActions"] == []

one_vocal = teachers + [
    TeacherObservation("vocal-embedding-a", "vocal_timbres", {"multipleDistinctVocalTimbres": 0.86}, 0.9)
]
r2 = understand_scene(PROBE, one_vocal)
assert r2["vocalTimbres"]["status"] == "POSSIBLE_MULTIPLE_DISTINCT_VOCAL_TIMBRES"

two_vocal = one_vocal + [
    TeacherObservation("vocal-embedding-b", "vocal_timbres", {"multipleDistinctVocalTimbres": 0.81}, 0.85)
]
r3 = understand_scene(PROBE, two_vocal)
assert r3["vocalTimbres"]["status"] == "MULTIPLE_DISTINCT_VOCAL_TIMBRES"
assert "never singer identity" in r3["vocalTimbres"]["claim"]

disagree = [
    TeacherObservation("tagger-a", "source_family", {"vocals": 0.92, "bass": 0.1}, 1.0),
    TeacherObservation("tagger-b", "source_family", {"vocals": 0.05, "bass": 0.9}, 1.0),
]
r4 = understand_scene(PROBE, disagree)
assert r4["semantic"]["uncertainty"] in {"MEDIUM", "HIGH"}

p2 = copy.deepcopy(PROBE)
p2["file"] = "CHARLI_xcx_TROYE_SIVAN_DUET_DO_NOT_CHEAT.flac"
a = understand_scene(PROBE, two_vocal)
b = understand_scene(p2, two_vocal)
assert a["measured"] == b["measured"]
assert a["semantic"] == b["semantic"]
assert a["vocalTimbres"] == b["vocalTimbres"]
assert b["provenance"]["filenameUsedForAcousticClaims"] is False

print("PASS: SUL Phase A reference preserves the truth boundary and zero playback authority")
