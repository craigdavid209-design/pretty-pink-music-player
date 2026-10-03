# Pretty Pink — Vocal Presence & Uncertainty School v5 Decision

Date: 2026-10-03

## Decision

**RESEARCH-ONLY. DO NOT IMPLEMENT INTO CURRENT 2.0.112.**

Pretty Pink 2.0.112 remains the CURRENT production baseline unchanged.

The v5 lesson improved uncertainty behavior but did not clear the predeclared held-out research gate. We will not retune thresholds after looking at held-out results merely to manufacture a pass.

## What v5 taught

v4 selective calibration already introduced abstention, but calibrated raw 500 ms probabilities despite its student contract specifying 0.25 / 0.50 / 0.25 temporal smoothing.

v5 corrected that research mismatch:
- smooth only within each track; never across track boundaries;
- measure local probability disagreement;
- let disagreement force AMBIGUOUS;
- use explicit states: STRONG_VOICE, LIKELY_VOICE, AMBIGUOUS, LIKELY_NO_VOICE, STRONG_NO_VOICE;
- fit model on train songs only;
- choose thresholds/disagreement limits on validation songs only;
- report held-out test only after calibration;
- authority remains 0;
- lyric intelligibility remains UNKNOWN.

## Public truth source

Jamendo Corpus for Singing Voice Detection: 93 Creative-Commons music pieces annotated voice (sung or spoken) / no-voice.

## v4 selective held-out baseline

- voice precision: 0.7617
- no-voice precision: 0.7279
- claimed accuracy: 0.7389
- claim coverage: 0.4480
- ambiguous coverage: 0.5520

## v5 held-out result

- n: 7,045 windows
- voice precision: **0.7581**
- no-voice precision: **0.7761**
- claimed accuracy: **0.7710**
- claim coverage: **0.3583**
- ambiguous coverage: **0.6417**
- strong voice precision: **0.7816**
- strong no-voice precision: **0.8310**
- strong coverage: **0.2440**

Predeclared gate:
- voice precision >= 0.78
- no-voice precision >= 0.78
- claimed accuracy >= 0.78
- claim coverage >= 0.15

Result: **FAIL / KEEP RESEARCH-ONLY.**

## Interpretation

The uncertainty lesson is directionally successful: Pretty Pink is better at withholding a claim when evidence conflicts, and her no-voice side improved materially. However, the voice side still shifts enough on unseen songs that the current lightweight evidence is not trustworthy enough to become a production voice detector.

This is useful knowledge, not a reason to lower the threshold.

## Truth boundaries

Never infer from this research:
- singer identity;
- exact source count;
- lyric transcription;
- human word correctness;
- lyric intelligibility;
- production defect;
- playback advice.

The research state remains a **voice-presence hypothesis with explicit uncertainty**.

## Android boundary

The v4/v5 school uses same-FFT-style research evidence but is not yet exact production-geometry parity. Do not freeze learned coefficients into Android until the feature extraction is retrained/revalidated against the exact Pretty Pink production FFT/sample-rate/cadence definitions.

No second decode, second file read, neural runtime, or playback-path analysis is justified by this work.

## Production decision

**2.0.112 stays CURRENT. No APK change. No sound change. No Work Mode implementation handoff.**

Future voice research should require either:
1. an independent public music voice/no-voice truth set for external confirmation; or
2. a new training protocol with exact Android-parity features plus genuinely independent song-level evaluation.

Do not repeatedly tune the Jamendo held-out split after seeing its answers.

## Pretty Pink philosophy

**Balance first. Understand more. Change less. Preserve the song. Ears decide.**

**Bring the feeling out. Preserve the song.**
