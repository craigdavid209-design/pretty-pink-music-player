# Pretty Pink round-3 decision — scene selectivity + vocal/production intelligence

## Project ruling

**Do not promote 2.0.110 Scene Restraint as-is.** Keep the sound engine frozen and replace only the candidate SUL authority logic.

House rule remains: **Learn more without earning the right to touch more.**

## Why 2.0.110 needs a correction

A 95-track cross-genre corpus pass showed the candidate gate acting across the full song on 94/95 tracks. The median whole-track optional-authority factor was 0.815583. The gate is mathematically one-way and safe, but profile labels were effectively becoming global authority. That is broader than the intended scene-local design.

### Scene Restraint v3

1. Global/profile factor is always **1.0**. Profile labels are descriptive only.
2. Restraint must be earned by a **local salient event**.
3. A qualifying event needs at least **two independent evidence cues**, enough local strength, and enough salience above its background.
4. Radius shrinks to a local 2.5-second neighborhood.
5. Maximum candidate restraint is bounded to factor **0.82**; still one-way toward zero only.
6. Unavailable/ambiguous evidence = exact previous behavior.
7. A high-confidence vocal-intelligibility-risk window may **veto scene restraint** so SUL cannot remove existing Balance/QDI help there. The vocal witness never creates new gain/EQ authority.

## Vocal Intelligibility Witness (VIW)

The witness predicts **risk**, not lyrics and not word-correct rate. Vocal presence is not treated as intelligibility.

Evidence axes:
- vocal-compatible evidence
- articulation support
- accompaniment/masking burden
- temporal-smear risk
- spatial/layering risk
- production density
- confidence / uncertainty

Outputs are deliberately cautious: `LOW_OBSERVED_RISK`, `ELEVATED_RISK`, `HIGH_SINGLE_AXIS_RISK`, `HIGH_COMBINED_RISK`, or `UNAVAILABLE`.

A 95-track / 2,850-window research pass found useful separation. `Star People` produced elevated local-risk windows (median 0.414, p90 0.446, peak 0.512, 43.3% >= 0.42). Cleaner controls were lower: `Official` p90 0.286 and `Wicked` p90 0.331. `Experimental Skin` was substantially harder in the mixture proxy (p90 0.570). These are **mixture-risk observations only**, not ground-truth lyric judgments.

## Production Context Witness

Production complexity is explanatory evidence, never a defect label. The witness may describe evidence as masking-heavy, temporally smeared, spatially layered, dense, complex, or ambiguous. It must not claim a named effect such as reverb, double tracking, compression, distortion, or vocal chopping unless a future validated semantic teacher earns that claim.

This distinction matters because current lyric-intelligibility research treats accompaniment masking, singing style, and production techniques as separate causes of reduced intelligibility. The 2026 Cadenza CLIP benchmark also shows that ordinary speech-intelligibility metrics are not sufficient for music; modern systems commonly combine learned audio representations with signal/perceptual features.

## Shared Gain

No separate SUL/VIW implementation is required for Shared Gain. Scene/vocal intelligence observes the same verified per-track scan portrait and acts only around optional Balance/QDI authority after the base plan is established. **Shared Gain anchor, target, album/session plan, Core gain, TELG, spectral margins, peak safety, and Comfort remain untouched.** Add explicit regression coverage to prove this.

## Android implementation constraint

Do not add a second decoder or second full-file read. Prefer evidence already measured during the verified scan. If VIW needs new mixture descriptors, collect them in the existing same-pass optional analysis path and cache them with the verified source/PCM identity. Any missing or invalid witness must abstain.

## Future teacher calibration

Before VIW ever receives positive playback authority, calibrate its risk score against a music-specific intelligibility benchmark such as the 2026 Cadenza CLIP dataset (human word-correct scores). Heavy foundation/separation models may be used offline as teachers; the Galaxy A17 production witness should remain tiny, bounded, and confidence-aware.
