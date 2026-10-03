# Pretty Pink SUL Phase A reference build — 2026-10-02

## Decision

Build **Scene Understanding Layer (SUL) Phase A** as two deliberately separated lanes:

1. **On-device structural witness** — deterministic, bounded, derived from verified scan evidence, zero playback authority.
2. **Offline semantic teacher fusion** — research/lab only, used to learn broad source-family and vocal-timbre concepts without ever feeding separated audio back into playback.

House rule: **Learn more without earning the right to touch more.**

## What is implemented in this lab

`tools/scene_understanding.py` is the reference fusion/truth-boundary engine. It turns mixture descriptors into measured structural flags without pretending they are instrument labels; accepts optional teacher observations; maps music-oriented instrument tags into broad Pretty Pink source families; surfaces disagreement; keeps vocal-timbre recognition separate from singer identity; and hard-codes Phase A playback authority to `OBSERVE_ONLY`.

`tools/teacher_contract.py` defines the teacher-neutral observation format and broad source-family vocabulary.

`tests/test_scene_understanding.py` checks the truth boundary, disagreement behavior, metadata/filename non-leakage, and zero playback authority.

## Source-family vocabulary

- vocals
- drums/percussion
- bass
- guitars
- keys/synths
- strings/orchestra
- winds/brass
- sampled/electronic

The purpose is to understand the mix, not to produce fragile instrument trivia.

## Research basis

Heavy separators are useful as **offline teachers**, not phone playback components: BS-RoFormer (arXiv:2309.02612), Mel-Band RoFormer (arXiv:2310.01809), and SCNet (arXiv:2401.13276).

Essentia's MTG-Jamendo instrumentation model exposes 40 music-oriented labels including voice, drums, bass, guitar, piano, sampler and synthesizer. SUL maps those labels into the smaller vocabulary above.

For a future compact student, EfficientAT (arXiv:2211.04772) demonstrates transformer-to-MobileNetV3 distillation for resource-constrained audio tagging. S-SONDO (ICASSP 2026 / arXiv:2604.24933) reports audio students up to 61x smaller while retaining up to 96.4% of teacher downstream performance in its evaluated tasks. These results support the **strategy**, not a claim that a ready-made model already solves Pretty Pink's exact scene task.

Slakh2100 supplies 2100 synthesized multitracks, 187 patches grouped into 34 classes, aligned MIDI, and a CC BY 4.0 license; it is appropriate for broad-source truth tests. Owned commercial music remains evaluation material only.

## 1999 / 2099 checkpoint

Applying the Phase A engine to existing mixture-only Scene Probe outputs for `1999`, `2099`, and three solo controls shows meaningful structural complexity across all five. Both duet tracks and the solo controls contain multiple acoustic-regime hypotheses, so mixture-only regimes cannot honestly be treated as singer count. With no semantic vocal teacher supplied, SUL reports vocal-timbre semantics as `UNAVAILABLE`, not a guessed duet label.

That is a pass: uncertainty is preserved.

## Android Phase A target

Work Mode Jane should implement a **separate research cache and snapshot**, not modify gain policy or trusted playback math.

Recommended classes:

- `SceneUnderstandingSnapshot.java`
- `SceneUnderstandingPolicy.java`
- `SceneUnderstandingCache.java`
- `SceneUnderstandingLens.java` or a small read-only bridge into the existing Intelligence Lens

Prefer reusing existing scan evidence first. Do **not** add a second audio decode merely for SUL on Galaxy A17.

## Hard no-touch boundary

Phase A SUL may not alter PCM; Everyday -14 LUFS or Quiet -19 LUFS targets; ReplayGain/core gain; Balance; QDI; TELG; comfort/dynamics/spectral authority; `PlaybackBalanceController` decisions; or infer singer identity from filenames, tags, credits, or metadata.

Any code path from SUL to a playback setter/controller is a failed implementation.

## Acceptance gates

1. Protected playback parity remains bit-identical with SUL disabled and observe-only enabled.
2. Existing host/release tests remain green.
3. New tests prove metadata non-leakage and zero audio/playback authority.
4. SUL truthfully supports `AVAILABLE`, `AMBIGUOUS`, `UNAVAILABLE`, and `NOT_NEEDED`.
5. No extra decode is scheduled during active playback on Galaxy A17.
6. Cache is bound to encoded-source SHA-256 + decoded-PCM SHA-256 and stale evidence is rejected.
7. UI uses measured/likely/possible/uncertain language and never singer names.
8. Phone tests include 1999, 2099, Gone, Cross You Out, Click, Shake It, February 2017, Peggy/Danny Brown material, and sample-heavy Peggy tracks.

## Future gate before any neural student

Do not ship a model merely because it is small. It must beat the deterministic structural witness on truth metrics, stay inside A17 CPU/RAM/thermal budgets, and improve useful understanding rather than producing prettier guesses.
