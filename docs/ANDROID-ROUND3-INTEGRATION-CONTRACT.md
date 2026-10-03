# Android integration contract — selective SUL v3 + VIW + production context

Target next candidate: **2.0.111-scene-vocal-intelligence-test / code 311**, based on exact 2.0.110 source.

## 1. Correct Scene Restraint first

Keep `TemporalSceneWitness.Profile` descriptive for Lens only. Remove profile-wide authority from `SceneRestraintGate`.

### Local event evidence

Extend each retained scene event with:
- `timeSeconds`
- `strength` = existing normalized local motion score
- `support` = count of independent cue families materially changing at that edge
- `salience` = local peak elevation over surrounding/background motion

Treat level + active-energy fraction as one ENERGY family for consensus. Optional cue families are GLARE, AIR, BASS, STEREO. A qualifying authority event needs:
- strength >= 0.16
- support >= 2 independent families
- salience >= 0.04
- local-max / spacing rules retained

These are experimental candidate thresholds, not safety limits. Keep event cap 32.

### Authority

- no event / unavailable / stale / malformed / ambiguous => `1.0`
- no whole-song profile factor; `global(profile)` must disappear from authority
- smooth local radius: 2.5 s
- dynamic event floor from strength/support/salience, never below 0.82
- factor only multiplies existing negative Balance cut and positive QDI lift toward zero
- Core, ReplayGain, targets, Shared Gain anchor, TELG, SpectralMarginPolicy, Comfort, QuietDynamicsGuard, peak safety and seek safety remain exact

## 2. Add Vocal Production Evidence in the existing scan

Do **not** add a second decoder, second full-file read, neural model, ASR model or source separator on the Galaxy A17.

Preferred implementation: extend the existing optional same-pass `AuditoryEventEvidence.Collector`, because it already computes 20 ms high/presence-band level, fraction, tonal concentration, modulation, stereo correlation/asymmetry and novelty. Aggregate those measurements into bounded 2-second vocal/production windows. Reuse verified scan identity and cancellation rules.

For each 2-second window expose normalized evidence axes (0..1):
- `vocalCompatible` — evidence compatible with vocal/lead material; never a singer claim
- `articulationSupport` — modulation/novelty evidence compatible with recoverable syllabic/consonant structure
- `maskingBurden` — dense competing energy around vocal-relevant bands
- `spatialLayering` — decorrelated/wide competing structure; not proof of double tracking
- `temporalSmear` — persistent low-contrast energy that can obscure boundaries; not proof of reverb
- `productionDensity`
- `confidence`

Prefer reuse of existing FFT/filter/envelope work. Any new arithmetic must be O(1) per existing analysis window with bounded arrays only. Use floats for retained 2-second axes if practical.

## 3. Vocal Intelligibility Witness (VIW)

Fuse those axes into an **intelligibility-risk** snapshot. Never emit lyrics, word identities or singer identity. Never call a vocal `intelligible` merely because voice-like energy is present.

Candidate labels:
- `LOW_OBSERVED_RISK`
- `ELEVATED_RISK`
- `HIGH_SINGLE_AXIS_RISK`
- `HIGH_COMBINED_RISK`
- `UNAVAILABLE`

The GitHub reference formula is a calibration starting point, not psychoacoustic truth. The phone implementation must expose its raw evidence axes so later Cadenza/human calibration can replace constants without changing the evidence schema.

### Only allowed authority in 2.0.111

If a 2-second VIW window has confidence >= 0.65 and risk >= 0.42, VIW may **veto Scene Restraint** at that position by forcing scene factor to 1.0. This is not a vocal boost; it merely prevents experimental SUL from removing existing Balance/QDI help.

Production-context ambiguity >= 0.72 may also force scene factor 1.0 (abstention).

VIW/production context must have **no positive playback authority** in this build.

## 4. Shared Gain

No separate algorithm. SUL v3/VIW use the installed verified per-track portrait and operate after the base plan is established. Regression must prove:
- Shared Gain anchor bit/exact unchanged
- album/session target unchanged
- scene/vocal factor can only affect existing Balance/QDI optional requests
- same behavior/invalidation rules for track mode and Shared Gain mode

## 5. Required tests

Run all existing 2.0.110 suites plus new tests that prove:
1. Profile label alone never changes authority.
2. No qualifying local event => factor exactly 1.0 at every position.
3. One cue only => abstain.
4. Multi-cue salient event => bounded local factor in [0.82, 1].
5. Outside +/-2.5 s => exactly 1.0.
6. High-confidence VIW risk => factor exactly 1.0.
7. High production ambiguity => factor exactly 1.0.
8. Balance cuts remain between original cut and zero.
9. QDI lifts remain between zero and original lift.
10. Core/targets/TELG/spectral/Comfort/peak/seek outputs are exact.
11. Shared Gain anchor/base plan are exact.
12. Cached/fresh scan parity; stale source/PCM/generation/epoch abstains.
13. No second decode/read/worker is introduced.
14. A17 budget: report CPU time, memory retained per typical 3–5 min track, first scan delta, second/cached scan delta, temperature/skip observations.

## 6. Promotion rule

Return an APK/source/report as a **TEST CANDIDATE only**. Do not promote automatically. Human listening plus corpus evidence decide. If selective SUL cannot demonstrate genuinely local behavior, turn candidate authority off and retain the read-only intelligence.
