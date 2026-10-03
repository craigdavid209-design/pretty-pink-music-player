# Pretty Pink SUL Round 2 — Android integration contract

## Decision

Implement Temporal Scene Motion as a **shadow-only portrait derived from evidence already produced by the verified scan**. Do not port the Python research STFT literally to the Galaxy A17 and do not open a second decoder.

House rule: **Learn more without earning the right to touch more.**

## Existing evidence to reuse in 2.0.108

`ScanResult` already carries source-bound measurement lanes that are sufficient for a cheap first mobile witness:

- `energies` — K-weighted 100 ms loudness-energy hops from `Loudness`;
- `glareHops` and `airHops` — 100 ms spectral comfort ratios from `EarComfortMeter`;
- `bassHops` — 100 ms low-bass portrait from `BassMeter`;
- `stereoContrast` — optional source/PCM-bound per-channel 100 ms K-weighted energy lanes for stereo sources;
- `auditoryEvents` — optional retained event evidence measured in the same scan;
- source identity fields `sourceSha256` and `decodedPcmSha256`.

These lanes are already generated during scanning. Round 2 should aggregate them into coarse temporal windows rather than decode the file again.

## Mobile witness shape

Use 20 existing 100 ms hops per nominal 2 s scene window. For every valid window keep only bounded summary values such as:

- mean level / energy occupancy;
- glare / air / bass ratio summaries when those lanes are aligned and available;
- left/right energy asymmetry and its change when `StereoContrastWitness` is bound to the exact scan;
- retained event density or presence only when event evidence is valid;
- evidence-availability bits.

Then compare adjacent windows. The first implementation should report **descriptive temporal evidence**, for example:

- median transition magnitude;
- p90 transition magnitude;
- peak transition magnitude;
- section-contrast spread;
- bounded abrupt-change event count/timestamps;
- one research profile such as `LOW_MOTION`, `SPARSE_ABRUPT_CHANGES`, `MODERATE_MOTION`, `PUNCTUATED_MOTION`, `SUSTAINED_MOTION`, or `SUSTAINED_AND_PUNCTUATED_MOTION`.

The mobile score does **not** need to numerically equal the offline Python research score. Its job is to preserve the same ordering semantics and truth boundaries using evidence the app already owns. Record the mobile algorithm/schema separately so comparisons remain honest.

## NMF lesson

Do not add NMF to Android Phase A. The round-2 real-music gauntlet showed the research factorizer's effective-component count near its ceiling across musically different files. Keep factorization in the lab as a diagnostic; do not treat factor count as source count or as a dominant complexity signal.

## Truth boundary

Temporal motion may say the mixture changed substantially, remained stable, or contains abrupt scene changes. It may **not** say why without independent evidence.

Forbidden in Phase A:

- singer identity or singer-name inference;
- exact source count;
- instrument names from mixture-only evidence;
- declaring an unusual/bright/noisy scene a defect;
- converting temporal motion into EQ, gain, Balance, QDI, TELG, target, or controller authority.

Semantic source-family and multi-vocal-timbre claims stay behind the existing teacher-evidence contract.

## Placement

Prefer a new read-only package-private component such as `TemporalSceneWitness` or `SceneUnderstandingShadow` in `com.prettypink.player`.

The component may read a completed, trustworthy `ScanResult`. It must not receive `MediaPlayer`, `DynamicsProcessing`, `PlaybackBalanceController`, or any mutable playback-control object. Keep that separation structural, not merely conventional.

Bind/cached results to the same complete `sourceSha256` + `decodedPcmSha256` identity. If either identity is missing/mismatched, return `UNAVAILABLE` and do not infer zero motion.

Expose through `IntelligenceLens` / Behind the Sound only after the scan is complete. Opening the view must not initiate scanning or alter playback.

## Performance contract for Galaxy A17

- no second decoder;
- no second full-file read;
- no new per-sample allocation;
- O(number of existing 100 ms hops) post-scan work;
- bounded arrays / event list;
- cancel/interruption checks in long loops;
- cache source-bound result;
- no scan work admitted during playback beyond work already permitted by existing resource policy;
- gracefully return `UNAVAILABLE` when optional evidence is absent.

## Required tests before David's phone trial

1. Existing protected playback tests remain unchanged and green.
2. Add host tests with synthetic 100 ms portraits for stable, one-hard-transition, gradual-morph, and noisy-but-stationary scenes.
3. Verify filename/metadata changes cannot change acoustic output.
4. Verify source hash mismatch discards cached SUL evidence.
5. Verify SUL feature flag on/off produces bit-identical approved playback decisions and audio-control calls.
6. Verify incomplete/peak-only/silent/invalid scans do not fabricate scene claims.
7. Run existing low-RAM/budget-device tests.

## Phone trial display

For the first APK, make the Lens wording explicitly observational, for example:

`Scene motion: punctuated · several large structural changes measured across the verified source.`

and underneath:

`Research shadow only — this observation did not change gain, EQ, loudness target, Balance, QDI, TELG, or playback.`

If evidence is partial, say so. If the witness is unavailable, say `Scene understanding unavailable for this scan`; never substitute a zero.
