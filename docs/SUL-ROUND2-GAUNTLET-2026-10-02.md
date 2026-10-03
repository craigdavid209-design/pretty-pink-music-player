# Pretty Pink SUL — Round-2 real-music gauntlet — 2026-10-02

## Decision

**Implement the Temporal Scene Motion witness in Phase-A shadow mode. Keep playback authority at zero.**

**Demote raw NMF effective-component count to diagnostic-only.** It remains useful as an unlabeled factorization diagnostic, but this real-music pass showed it clustering near the eight-factor ceiling across very different recordings. It must not be treated as source count or as a dominant scene-complexity vote.

House rule: **Learn more without earning the right to touch more.**

## What changed

SUL schema moves from 1 to 2 for the research reference. The new `temporalSceneMotion` witness looks at adjacent two-second windows of the original stereo mixture and measures bounded changes in:

- coarse spectral-band distribution;
- level;
- mid/side geometry;
- left/right decorrelation;
- spectral flatness;
- spectral centroid;
- transient/onset activity.

The result is a structural time-series descriptor, not a source separator. It reports median motion, p90 motion, peak motion, section contrast, absolute abrupt-change events, and a bounded descriptive profile.

Profiles are descriptive only: `LOW_MOTION`, `SPARSE_ABRUPT_CHANGES`, `MODERATE_MOTION`, `PUNCTUATED_MOTION`, `SUSTAINED_MOTION`, or `SUSTAINED_AND_PUNCTUATED_MOTION`.

## Why this is better than the old factor-count emphasis

On the ten new real tracks in this pass, NMF `effectiveComponents` stayed roughly 7.37–7.85 despite large musical differences. That is evidence of factorizer saturation, not evidence that every song has the same scene structure.

Temporal motion separated the recordings much more usefully:

- Breaking Benjamin — `Failure`: mostly low median motion with sparse abrupt changes.
- Breaking Benjamin — `Ashes of Eden`: punctuated scene motion.
- Charli xcx — `Shake It`: punctuated, high section contrast.
- Charli xcx — `February 2017`: sustained plus punctuated motion.
- JPEGMAFIA — `Bridges on Fire`: moderate motion despite dense/experimental production.
- JPEGMAFIA x Danny Brown — `Garbage Pale Kids`: moderate motion with abrupt-change evidence.
- JPEGMAFIA x Danny Brown — `Fentanyl Tester`: sustained plus punctuated motion.
- LISA — `MONEY`: sustained plus punctuated motion.
- Nas — `N.Y. State of Mind`: low scene motion.
- Nas — `The World Is Yours`: moderate scene motion.

This distinction is valuable because **unusual production is not a defect and high texture-factor count is not source count**.

## Research grounding

This direction follows established music-information-retrieval ideas: novelty functions measure frame-to-frame spectral change, while recurrence/self-similarity representations are used to reason about repeated structure and section changes. Pretty Pink's witness is deliberately smaller and more conservative than a full structural-segmentation system because the Galaxy A17 is the target and Phase A remains observation-only.

References used for this pass:

- Essentia `NoveltyCurve` documentation (frequency-band novelty from log-compressed energy differences).
- librosa temporal segmentation / recurrence-matrix documentation and the Laplacian segmentation example.

## Synthetic truth checks

New exact synthetic regression contains three known scenes:

1. constant stereo tone -> `LOW_MOTION`, no abrupt events;
2. one known hard transition at ~12 s -> `SPARSE_ABRUPT_CHANGES`, transition detected near the known boundary;
3. smooth continuous morph -> more motion than the constant case, less peak change than the hard-transition case.

These checks validate the semantics of the descriptor without requiring copyrighted music in CI.

## Production boundary

Still forbidden in Phase A:

- PCM changes;
- gain changes;
- EQ changes;
- loudness-target changes;
- QDI/Balance/TELG authority changes;
- extra correction merely because a scene is complex;
- singer-name inference;
- instrument/source-family naming without semantic-teacher evidence.

The only approved implementation change for the app is a **read-only shadow snapshot** that can be logged or displayed for testing. It must be source-identity-bound, deterministic, cacheable, and not trigger a second decode on the A17.

## Next gate after phone testing

If A17 CPU/RAM/thermal behavior is clean and the descriptor remains stable across the wider library, the next research step is recurrence/repetition evidence and offline semantic-teacher comparison. Neither earns playback authority automatically.
