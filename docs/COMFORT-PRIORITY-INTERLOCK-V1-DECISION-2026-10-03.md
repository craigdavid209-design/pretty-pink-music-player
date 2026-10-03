# Pretty Pink — Comfort Priority Interlock v1 Decision

Date: 2026-10-03
Baseline: **2.0.112 CURRENT**
Status: **IMPLEMENT AS NEW TEST CANDIDATE ONLY; DO NOT AUTO-PROMOTE**

## User-observed regression

On louder speaker listening after promotion of 2.0.112, difficult JPEGMAFIA / Danny Brown material again sounded capable of piercing the ear. The sound remained musically strong, but the balance felt too tame in its *correction*: Pretty Pink appeared to preserve difficult production more than the listener wanted for comfort.

This is a comfort observation, not a hearing-safety/SPL claim.

## Code-level finding

2.0.112 Scene Restraint v3 is allowed to multiply an existing negative Balance request toward zero around qualified scene events. That is intentionally one-way and artist-intent-preserving, but it creates a conflict on tracks where independent existing spectral evidence already says persistent energetic presence / upper-air energy is significant.

The important distinction:

- **Balance planner** already earned a bounded cut and already contains intent protections.
- **Scene v3** can reduce that cut to preserve a dramatic scene.
- **SpectralMarginPolicy / TELG** may independently say the track has persistent ear-load evidence.

When those two goals conflict, human-ear comfort should win *only by restoring the already-earned Balance cut*.

## Real-music school result

A local research replay used the exact 2.0.112 formulas for K-weighted 100 ms energy, EarComfortMeter, BassMeter, SpectralMarginPolicy and TemporalSceneWitness. Commercial audio was not committed; only derived metrics were recorded.

Five SCARING THE HOES examples all earned non-zero SpectralMarginPolicy confidence:

- Lean Beef Patty: 1.000
- SCARING THE HOES: 1.000
- Garbage Pale Kids: 1.000
- Fentanyl Tester: 0.935
- God Loves You: 0.174

The raw Scene-v3 event gate also found restraint opportunities in roughly 9–35% of these tracks before Production/Vocal veto is considered.

Five initial controls (Wicked, It Was A Good Day, Failure, Ashes of Eden, Dawn) all had spectral confidence 0.0. Across the already-materialized 95-track corpus, only one track earned non-zero spectral confidence: Charli xcx — February 2017 at about 0.158.

This is unusually selective evidence: it targets a strict existing comfort witness rather than a genre or metadata rule.

## Candidate rule: Comfort Priority Interlock (CPI) v1

For **Balance only**:

1. Compute current Scene v3 factor exactly as 2.0.112 does.
2. If the installed source-bound `SpectralMarginPolicy.Evidence` is available and its confidence is strictly greater than 0, Scene is **not allowed to relax the negative Balance cut**.
3. Therefore Balance uses factor `1.0` at those moments.
4. The resulting cut may equal the original pre-Scene Balance request, but may never become more negative than it.

For **QDI**:

- keep current Scene v3 factor exactly unchanged.
- do not restore or increase a positive QDI lift under the comfort interlock.

This is a veto on Scene's reduction authority, not new attenuation authority.

## What must stay frozen

- Everyday -14 LUFS / Quiet -19 LUFS
- Core / ReplayGain semantics
- Balance planner and its maximum cut (0.55 dB)
- QDI planner
- TELG
- SpectralMarginPolicy thresholds and maximum margins
- ComfortContourEffect
- QuietDynamicsGuard
- Scene event detection / qualification / radius / factor math
- peak/headroom safety
- Shared Gain anchor/base plan
- source / decoded-PCM identity
- Vocal School v2 shadow-only / zero authority

## Shared Gain

CPI must operate only on the per-track optional Balance request downstream of the verified shared base plan. It must not alter album anchor, album Core gain, spectral shared margin, membership, or session-set semantics.

The per-track `SpectralMarginPolicy.Evidence` may be used as the CPI witness even when Shared Gain base authority is album-wide, because CPI changes only whether Scene may reduce that track's already-existing optional Balance cut.

## Failure behavior

Missing, stale, malformed, mismatched, unavailable, or zero-confidence spectral evidence => exact 2.0.112 Scene behavior.

No metadata or genre shortcuts. No artist-name rules.

## Required Work Mode proof

A 2.0.113 candidate must demonstrate:

- current 2.0.112 parity whenever spectral confidence == 0;
- current QDI requests remain exact everywhere;
- on CPI-qualified tracks: `original_balance_cut <= candidate_cut <= current_scene_cut <= 0` in signed dB terms;
- candidate cut is exactly the original pre-Scene Balance cut when CPI engages;
- no request ever exceeds the existing 0.55 dB Balance maximum;
- no Core/TELG/Spectral/Comfort/peak/seek/output changes;
- Shared Gain anchor/base exact;
- cached/fresh parity;
- stale source/PCM/generation/epoch fails closed to current behavior;
- no second decode, full read, worker, FFT, or neural model;
- A17 cost effectively zero beyond one prepared boolean / tiny branch.

## Real-song graduation set

Hard cases:
- SCARING THE HOES — Lean Beef Patty
- SCARING THE HOES — SCARING THE HOES
- SCARING THE HOES — Garbage Pale Kids
- SCARING THE HOES — Fentanyl Tester
- SCARING THE HOES — God Loves You
- additional JPEGMAFIA/Danny Brown hard tracks available in Pretty Pink Home

Controls:
- Ice Cube — Wicked
- Ice Cube — It Was A Good Day
- Breaking Benjamin — Failure
- Breaking Benjamin — Ashes of Eden
- Breaking Benjamin — Dawn
- Jane Remover — Star People / Psychoboost / Experimental Skin should not be altered by CPI merely because they are complex; current local research gave them zero SpectralMarginPolicy confidence.

Also inspect February 2017 because the 95-track audit found it as the only pre-existing corpus track with non-zero spectral confidence. It is a crucial overreach check.

## Promotion rule

Return as **2.0.113 COMFORT PRIORITY TEST** only if all digital proofs pass.

Do not promote automatically. David must do louder speaker/headphone human-ear testing, with special attention to whether the harsh passages become comfortable without making attacks, excitement, or intentional grit feel dull.

If the candidate sounds flatter, darker, smaller, or less emotionally alive, reject it and keep 2.0.112 current.

## Philosophy

**Comfort may veto restraint; comfort may not invent correction.**

**Balance first. Understand more. Change less. Preserve the song. Ears decide.**

**Bring the feeling out. Preserve the song.**
