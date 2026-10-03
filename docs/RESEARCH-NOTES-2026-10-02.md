# Research notes — 2026-10-02

## External direction

Modern music source separation strongly supports a teacher-student research design. Band-split / Mel-band RoFormer and SCNet demonstrate strong broad-stem separation, while models in this class are much too expensive to treat as an always-on budget-phone playback dependency. The useful idea is therefore to use heavyweight models offline/research-side as **teachers**, then retain only compact scene descriptors or distill a small witness for on-device use.

Dataset notes:

- **Slakh2100**: 2,100 synthetic multitracks, 4–48 sources, 34 instrument classes, aligned MIDI; CC BY 4.0. Excellent for source-count/instrument-layer truth, though synthetic timbre/mixing limits realism.
- **MUSDB18/HQ**: established 4-stem benchmark, but use is restricted/academic and the source licenses are mixed; valuable for research comparisons, not something to casually fold into a distributable/commercial training corpus.
- **MoisesDB / MedleyDB**: richer real multitrack/source annotations but non-commercial terms; research/evaluation only unless permissions change.
- **FUSS**: variable 1–4 source mixtures across hundreds of sound classes; helpful for open-domain source-count/unknown-source behavior, not specifically music arrangement semantics.

## Local findings

The existing production brain is already conservative on multi-vocal anchor tracks. The inherited 2.0.92 full-stack audit shows `1999` abstains from Balance in both modes and uses only tiny QDI. `2099` uses a small Balance cut, small presence reserve and tiny average QDI; Quiet Guard adds only tiny relief in Quiet mode.

The new mixture-only Scene Probe can distinguish layer geometry and texture changes, but **cannot honestly identify speakers/instruments**. That is a feature, not a failure: it defines the boundary between deterministic acoustic evidence and semantic teacher evidence.
