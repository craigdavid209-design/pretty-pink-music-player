# Pretty Pink project decision — 2026-10-02

## Production decision

**FREEZE THE APPROVED SOUND.** No new playback tuning is justified by today's audit.

Pretty Pink 2.0.108 keeps the protected 2.0.92 audio brain byte-identical across the 76 protected Java classes compared in the lab. The current UI/media integration changes do not change approved gain-policy math.

The existing full-stack corpus evidence covered 228 audio files / 226 unique encoded sources, both listening modes, and 328,640 production-policy/controller playback ticks at 1e-9 dB tolerance, plus bit-identical before/after parity for the audited display-only truth fix.

A fresh Library census on 2026-10-02 again found **228 audio files** under `/Pretty Pink Home/04 Music Collection/04 Album Archives/Reference Tracks`. Two intentionally duplicated-looking JPEGMAFIA files — `PROTECT THE CROSS` and `TAKE AN` — are present in two Library locations and are consistent with the prior 228-file / 226-unique-source accounting. This census is a file-count/catalog consistency check, not a newly computed SHA-256 of every Library object.

## Grade

**Current playback brain: A+ for correctness, restraint, and protected-sound continuity on the available corpus evidence.**

That grade does not claim perfect semantic source recognition, perfect Android scheduling under every real-world condition, or that no future bug can exist. It means the installed decision math and protections have earned a freeze: do not change them without a reproduced need.

## Scene Understanding Layer (SUL)

**Decision: KEEP AND DEVELOP AS RESEARCH-ONLY / SHADOW. Do not give it playback authority yet.**

Today's mixture-only Scene Probe successfully measures stereo geometry, harmonic/percussive evidence, texture factors, acoustic-regime changes, spectral shape and onset structure. Synthetic exact-truth regression passed locally and in GitHub CI.

On `1999` and `2099`, the probe measures meaningful scene differences, but solo controls also contain multiple acoustic regimes. Therefore mixture-only clustering cannot honestly say “Charli” versus “Troye,” or label every instrument. That uncertainty is a design requirement, not a failure.

The correct final-brain direction is a compact, uncertainty-aware scene graph trained/evaluated with heavyweight semantic/source-separation teachers offline. Original PCM remains the artist's mix and teacher stems are never played.

## Next research gates

1. Add offline semantic teachers for broad source families and instrumentation. Candidate families include modern music source separation plus compact audio tagging/embeddings. Keep all teacher outputs outside playback.
2. Validate source-family/count behavior against exact stem truth (synthetic fixtures plus appropriately licensed multitrack datasets such as Slakh2100). Owned commercial music remains evaluation material, not committed/public training audio.
3. Expand multi-vocal tests: `1999`, `2099`, `Gone`, `Cross You Out`, `Click`, `Shake It`, `February 2017`, Peggy/Danny Brown collaborations and other features. The target is `MULTIPLE_DISTINCT_VOCAL_TIMBRES` / layered-source evidence with confidence, not singer-name guessing.
4. Treat JPEGMAFIA/sample-heavy/noisy music as a mandatory false-positive gauntlet. Unusual production is not a defect.
5. Distill only the useful teacher knowledge into a tiny on-device witness and benchmark CPU, memory, thermal and scan scheduling on Galaxy A17-class hardware.
6. Require bit-identical approved playback with SUL authority disabled. Only after strong truth metrics and listening validation may SUL earn **protective veto/reduction authority** over optional adjustments. It may not increase existing gain/EQ authority or exceed existing caps.

## Household rule for Future Jane

**Learn more without earning the right to touch more.**

Pretty Pink's approved sound is not a science-project substrate. Build deeper understanding beside it, prove that understanding independently, and let uncertainty produce abstention. If the new intelligence does not clearly improve understanding without compromising artist intent, resource discipline, or truthfulness, keep it in research.

Balance first. Understand more. Change less. Preserve the song. Ears decide.
