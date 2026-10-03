# Pretty Pink — Comfort Priority Interlock v1.1 Decision

Date: 2026-10-03
Baseline: **2.0.112 CURRENT**
Status: **IMPLEMENT AS NEW TEST CANDIDATE ONLY; DO NOT AUTO-PROMOTE**

## User-observed regression

On louder speaker listening after promotion of 2.0.112, difficult JPEGMAFIA / Danny Brown material again sounded capable of piercing the ear. The sound remained musically strong, but Pretty Pink felt too tame in its comfort correction.

This is a comfort observation, not a hearing-safety/SPL claim.

## Historical reference recovered

The human-ear reference David remembered is **2.0.68 — Human Ear Load Governor**. Its promotion record says difficult JPEGMAFIA sounded clearly more relaxed while preserving artist identity.

Direct source comparison shows `TargetAwareEarLoadGovernor.java` has no behavior change from 2.0.68 to 2.0.112; only its descriptive comment changed from Lab-only to existing production. TELG was not removed.

Later layers do differ. Most importantly for this first repair:
- Scene v3 may move an already-earned negative Balance cut toward zero around qualified events.
- QDI later became slightly more willing to recognize mildly recessed detail. **QDI is frozen for this experiment** so only one causal variable changes.

## Core hypothesis

The problem is not that comfort intelligence vanished. The conflict is that newer artist-intent restraint can reduce an already-earned optional Balance correction even when older, independent comfort intelligence has said the track carries persistent ear-load evidence.

**Comfort may veto Scene restraint; comfort may not invent correction.**

## Real-music school result

A local replay used the exact 2.0.112 K-weighted energy, EarComfortMeter, BassMeter, SpectralMarginPolicy and TemporalSceneWitness formulas. Commercial audio was not committed; only derived metrics were retained.

Five selected SCARING THE HOES tracks all earned non-zero SpectralMarginPolicy confidence:
- Lean Beef Patty: 1.000
- SCARING THE HOES: 1.000
- Garbage Pale Kids: 1.000
- Fentanyl Tester: 0.935
- God Loves You: 0.174

The raw Scene-v3 event gate found restraint opportunities in roughly 9–35% of those tracks before Production/Vocal veto is considered.

Initial controls — Wicked, It Was A Good Day, Failure, Ashes of Eden, Dawn — all had spectral confidence 0.0. In the existing 95-track corpus, only February 2017 had non-zero spectral confidence (~0.158).

## Candidate rule: Comfort Priority Interlock (CPI) v1.1

For **Balance only**:
1. Compute current Scene v3 factor exactly as 2.0.112 does.
2. Determine whether **existing** comfort authority has already been earned for this exact source-bound track:
   - positive valid `SpectralMarginPolicy.Evidence.confidence`; **or**
   - in single-track mode, TELG has earned additional delivered-level reserve above the spectral floor.
3. If comfort is earned, Scene loses permission to relax the negative Balance cut, so Balance uses factor `1.0`.
4. The result may equal the original pre-Scene Balance request but may never become more negative than it.

For **QDI**:
- keep current Scene v3 factor exactly unchanged;
- do not restore or increase positive QDI lift under CPI.

CPI is a veto on Scene's reduction authority, not new attenuation authority.

## Implementation truth

Prefer a tiny prepared/read-only boolean or helper such as `comfortPriorityEarned` rather than recomputing any scan evidence during playback.

TELG-extra determination must compare the already-prepared governor margins with the already-prepared spectral floor; do not parse `reason` strings. In Shared Gain, TELG intentionally adds no new per-track authority, so only valid per-track spectral evidence may qualify CPI. Album anchor/base/membership must remain exact.

Missing/stale/malformed/mismatched evidence => exact 2.0.112 Scene behavior.

## What stays frozen

- Everyday -14 / Quiet -19 targets
- Core / ReplayGain
- Balance planner and 0.55 dB maximum cut
- QDI planner and thresholds
- TELG math and thresholds
- SpectralMarginPolicy math and thresholds
- ComfortContourEffect / QuietDynamicsGuard
- Scene event detection / event radius / factor math
- peak/headroom/seek/output/focus behavior
- Shared Gain anchor/base plan
- source / decoded-PCM identity
- Vocal School v2 shadow-only / zero authority

## Required proof for 2.0.113 candidate

- exact 2.0.112 parity whenever CPI is not earned;
- current QDI requests exact everywhere;
- `original_balance_cut <= candidate_cut <= current_scene_cut <= 0` in signed dB terms;
- when CPI engages, candidate Balance cut equals original pre-Scene Balance cut;
- never exceed existing 0.55 dB Balance maximum;
- no Core/TELG/Spectral/Comfort/peak/seek/output changes;
- Shared Gain anchor/base exact;
- cached/fresh parity;
- stale source/PCM/generation/cache epoch fails closed;
- no second decode/read/worker/FFT/model;
- effectively zero A17 playback cost.

## Human-ear graduation set

Hard cases: Lean Beef Patty, SCARING THE HOES, Garbage Pale Kids, Fentanyl Tester, God Loves You, plus other Peggy/Danny material David reports as piercing.

Controls: Wicked, It Was A Good Day, Failure, Ashes of Eden, Dawn. Also inspect February 2017 as an overreach counterexample.

Jane Remover tracks such as Star People / Psychoboost / Experimental Skin remain useful controls; complexity alone must never trigger CPI.

## Promotion rule

Return **2.0.113 COMFORT PRIORITY TEST** only if digital proofs pass. Never auto-promote.

David then tests at normal and louder listening levels. Desired result: difficult material feels relaxed again without attacks, intentional grit, contrast or excitement becoming dull. If it feels flatter/darker/smaller, reject it and keep 2.0.112 current.

**Balance first. Understand more. Change less. Preserve the song. Ears decide.**

**Bring the feeling out. Preserve the song.**
