# Pretty Pink Scene Understanding Layer (SUL)

## Recommendation

Build SUL as a **read-only, source-grounded witness** first. Do not change Pretty Pink's approved sound.

The goal is not literal stem playback. The goal is a compact, uncertainty-aware **scene graph** describing what the original stereo mix appears to contain and how that structure evolves.

## Why this is the right final brain layer

Pretty Pink already knows loudness, peaks, dynamics, spectral pressure, retained auditory events, local contrast, stereo channel energy, mode targets, and protective arbitration. What she does not yet explicitly represent is **coexisting source structure**: multiple voices, drums under synths, bass under noisy samples, centered vs wide layers, repeated vs unique textures, and abrupt source entrances/exits.

That missing representation is exactly where a scene-understanding layer helps — while preserving the original mix.

## Architecture

### Tier 0 — Verified source identity

Reuse existing encoded-source SHA-256 / decoded-PCM identity, frame count, sample rate, channel count and complete-scan trust. SUL evidence must be bound to the same source/PCM identity or it is discarded.

### Tier 1 — Deterministic mixture witnesses (cheap, on-device capable)

Multi-resolution STFT descriptors:

- harmonic / percussive / residual energy hypotheses;
- onset density and transient persistence;
- spectral flux, centroid, flatness and rolloff trajectories;
- chroma/tonal stability where valid;
- mid/side energy, L/R correlation and channel asymmetry;
- low/mid/presence/air occupancy through time;
- NMF-style latent texture components, used only as unlabeled source hypotheses.

These are **not stems** and must never be named as speakers or instruments by themselves.

### Tier 2 — Semantic teacher ensemble (research/off-device first)

Use high-quality separation/tagging systems as microscopes:

- a music source separator (e.g. BS-/Mel-Band RoFormer, SCNet, HTDemucs) for broad stem hypotheses;
- an instrument/music tagger for semantic probabilities;
- optional vocal-activity / multi-speaker research for sections likely containing multiple distinct voices.

Teacher outputs are never played. They generate labels/descriptors for evaluating and potentially distilling a much smaller on-device witness.

### Tier 3 — Agreement + uncertainty engine

A claim becomes stronger only when independent families agree.

Example evidence for a “distinct vocal layer change” might require agreement among:

- separator vocal-mask change;
- harmonic/timbre embedding change;
- center/side spatial change;
- voiced-region confidence;
- persistence across a minimum duration.

Conflicting evidence yields `AMBIGUOUS`, not a forced label.

### Tier 4 — Scene graph

Per time region, store compact descriptors such as:

- likely active source-family count range, e.g. `2–4`, never fake exactness;
- vocal-likeness probability;
- percussion/bass/harmonic/noise likelihoods;
- center/wide spatial occupancy;
- source-change events;
- overlap / masking likelihood;
- exposed-detail likelihood;
- confidence and provenance.

No separated PCM is required in the production cache.

### Tier 5 — playback authority policy

**Phase A: none.** Lens/research only.

**Phase B, only after validation: protective authority only.** SUL may reduce/veto an *optional* adjustment when the scene is complex, identity-sensitive, exposed, or uncertain. It may not invent a larger cut/lift.

**Phase C, only with strong evidence and listening approval:** narrowly allow SUL to choose among already-approved optional plans, never exceed existing caps.

## 1999 / 2099 test meaning

The correct first milestone is *not* “Pretty Pink says this is Charli and this is Troye.”

The milestone is:

1. detect that multiple persistent source/timbre regimes overlap or alternate;
2. preserve spatial and level contrast among those regimes;
3. avoid interpreting a singer/source change as a loudness defect;
4. expose uncertainty honestly;
5. later, with a semantic teacher, test whether the vocal lane supports `MULTIPLE_DISTINCT_VOCAL_TIMBRES` without attaching human identity names.

Singer identity is a separate problem and should not be inferred from metadata or filenames.

## Training / evaluation data

Use owned music as **evaluation**, not as public training material or committed audio.

For truth-labeled training/evaluation, prefer datasets whose terms fit the intended use. Slakh2100 is useful for many-instrument stem truth and is CC BY 4.0. MUSDB18, MedleyDB and MoisesDB are valuable research references but carry non-commercial/academic restrictions that must be respected. FUSS is useful for variable unknown source counts outside music.

Synthetic fixtures remain essential because they give exact known source count, pan, level, onset and overlap truth.

## Acceptance gates before any production authority

SUL stays research-only until all are true:

- deterministic output for identical verified PCM;
- no metadata/filename leakage into acoustic claims;
- bounded memory and runtime on Galaxy A17-class hardware;
- no additional scan during active playback on low-RAM devices unless already admitted;
- source-count / family metrics validated on stem truth, not only commercial mixes;
- duet/multi-vocal false-positive tests;
- experimental/noisy/sample-heavy music false-positive tests;
- bit-identical approved playback when SUL is present but authority disabled;
- Lens can say `AVAILABLE`, `AMBIGUOUS`, `NOT NEEDED`, `UNAVAILABLE` truthfully;
- human listening finds no artist-intent regressions after any future protective integration.

## Current decision

**KEEP AS RESEARCH-ONLY AND BUILD THE LAB.** This is a promising intelligence direction. Do not alter production sound yet.
