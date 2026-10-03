# Pretty Pink — Scene/Balance Comfort Restore v1

Date: 2026-10-03
Status: **RESEARCH PASSED FOR WORK MODE TEST CANDIDATE; NOT PRODUCTION-PROMOTED**

## Human-ear trigger

David reports that current 2.0.112 still sounds excellent overall but can feel too exposed / piercing again on difficult JPEGMAFIA and Danny Brown material at louder speaker listening. The concern is specifically human-ear comfort, not loudness-target accuracy.

## Historical anchor

The approved comfort lineage predates Scene authority. TELG / Human Ear Load Governor was human-ear approved on Galaxy A17, and later 2.0.83-lineage builds retained the accepted audio calculations while adding reliability / research scope work.

## Current architectural finding

In 2.0.112, Scene Restraint v3 is allowed to multiply an already-negative Balance request by a factor in [0.82, 1.0]. Because Balance cuts are negative, this makes the cut lighter around Scene-qualified events.

That is one-way in the sense of "less processing", but it can conflict with the older comfort purpose of Balance: an artist-intent event may also be the passage that is uncomfortable at delivered level.

## School decision

Do **not** add another comfort processor.

Instead, change authority ordering for the next Work Mode test candidate:

1. **Balance attenuation stays exactly as requested by the mature Balance/Quiet Guard path.**
2. **Scene v3 loses authority over negative Balance cuts.**
3. **Scene v3 keeps its current one-way authority over positive QDI lift.**
4. TELG, Spectral Margin, Comfort contour, Core, Shared Gain base/anchor, peak safety, seek safety and output control remain unchanged.
5. Vocal School v2 remains shadow-only.

Conceptually:

- 2.0.112: `finalBalance = originalBalance * sceneFactor`
- candidate: `finalBalance = originalBalance`
- QDI remains: `finalQdi = originalQdi * sceneFactor`

This is a removal of newer authority, not a new attenuation feature.

## Why this is conservative

- It cannot make Balance stronger than the already-existing approved Balance request.
- It cannot create a new cut where Balance requested zero.
- It does not change Balance coefficients, planning, recurrence logic, intent logic, or maximum cut.
- It restores the pre-Scene authority ordering for Balance while retaining newer Scene observation and QDI restraint.
- Shared Gain base/anchor remains untouched.

## Required Work Mode validation

The candidate must prove:

- exact 2.0.112 ancestry;
- only the Scene→Balance authority edge is removed;
- Balance planner / Perceptual Dynamics / Quiet Guard bytes or behavior are otherwise unchanged;
- Scene factor and Lens observations remain available;
- QDI Scene restraint remains byte-for-byte / numerically identical to 2.0.112;
- TELG / Spectral / Comfort / Core / Shared Gain / peak / seek / output remain exact;
- current 2.0.112 Scene-relaxed Balance output changes only where Scene factor < 1 and original Balance cut < 0;
- candidate Balance at every position equals the pre-Scene unrestrained Balance request;
- no candidate Balance value is below the mature planner request or above 0;
- real-song gauntlet includes JPEGMAFIA, JPEGMAFIA×Danny Brown, Danny Brown, Jane Remover, Breaking Benjamin, Ice Cube/Nas, Charli/Tkay/LISA controls;
- A17 resource cost is neutral (this should remove work from the playback decision, not add work).

## Promotion rule

Return as a **test candidate only**. David must perform human-ear listening at realistic louder speaker / normal listening levels. Do not auto-promote.

If the candidate restores comfort without making the music feel dulled or over-controlled, it may earn promotion. If comfort remains poor, do not stack another tweak on top; investigate Shared Gain/TELG delivery and route-specific Comfort-contour behavior separately.

## Philosophy

**Protective decisions outrank observational restraint.**

**Balance first. Understand more. Change less. Preserve the song. Ears decide.**

**Bring the feeling out. Preserve the song.**
