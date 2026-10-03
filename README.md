# Pretty Pink Music Player — Scene Understanding Lab

Read-only research for Pretty Pink's next intelligence layer.

## Non-negotiable rule

This repository does **not** remix, replace, or feed separated stems into playback. The production PCM remains the artist's mix. The lab asks a narrower question: can Pretty Pink understand the mixture deeply enough to recognize layered structure, uncertainty, contrast, and source diversity — then use that understanding to **abstain or protect** existing optional processing when appropriate?

The current listening engine is frozen unless a reproduced defect or separately approved experiment justifies a change.

## Current status — 2026-10-02

**Decision: RESEARCH-ONLY / SHADOW.** The Scene Understanding Layer is worth developing, but it has no playback authority.

Initial work includes:

- byte-parity check of the protected 2.0.108 brain against the audited 2.0.92 core;
- numeric summary of the inherited full-stack audit over the JPEGMAFIA-heavy corpus;
- a lightweight mixture-only Scene Probe (HPSS + stereo + NMF + acoustic-regime descriptors);
- synthetic truth tests that prove basic layer/stereo sensitivity without claiming source identity;
- Charli xcx anchor probes including `1999` and `2099`.

No copyrighted audio or stems are committed here — only code and derived numeric research results.

## Philosophy

**Balance first. Understand more. Change less. Preserve the song. Ears decide.**

A new witness must distinguish:

1. **measured fact** — e.g. verified stereo energy, spectral/onset structure;
2. **source hypothesis** — a latent layer suggested by multiple independent cues;
3. **semantic hypothesis** — probable vocals/drums/bass/etc., requiring a trained model;
4. **identity claim** — e.g. “Charli” vs “Troye,” which is *not* inferred unless specifically validated by a trustworthy identity model and suitable ground truth;
5. **uncertainty / abstention** — first-class output, never a failure.

See `docs/SCENE-UNDERSTANDING-ARCHITECTURE.md`.
