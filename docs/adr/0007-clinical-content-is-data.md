# Clinical content is data; the non-negotiables are code

Noor holds two kinds of rule, and they live in two places.

Clinical judgement that a consultant revises as guidelines change — surveillance intervals, the **Physical Examination** element lists, which Vitals are captured per condition, the **Self-Care Check** items, the stop-rule library, the interval-event tick-list (§4.2), the searchable drug list (§4.2), each tier's response window, and the four structured reason lists (§5.10) — lives in **versioned clinical content**, one file per subject under `docs/clinical-content/`, each carrying N8's owner, source, version and review date. The eight non-negotiables and everything derived from them are written in code: the eight sections and their order, the six Visit states — **Emergency** among them, as an interrupt — the four **Escalation Tiers**, the N3 cap of **three**, the withholding principle's four triggers (§4.11), and Present / Absent / Unreachable.

**The test is not "is it a number."** It is: *would a clinician revising a guideline touch this, or is it a safety limit with evidence behind it?* An interval is the first. The cap is the second.

**The cap of three is the case that makes the line necessary.** N3 exists because clinicians overrode 98.6% of alerts once they exceeded five a day — the number *is* the finding, not a default sitting near it. A cap in a configuration file can be raised by a service under pressure with no error, no failing test and no diff: the limit is still being obeyed, it is merely a different limit, and six months later nobody remembers where three came from. "Noor never shows more than three" would have quietly become "Noor ships with three." Welding it means the only way to change it is a code change that appears in the project history and has to survive the test suite — which is exactly the scrutiny that change deserves.

**This is a deliberate refusal of configurability, and the next engineer will want to undo it.** A hardcoded `3` looks like an oversight; it is not. The same holds for the tier count and the section order.

**The tier response windows are content; the tier count is not.** What Tier 2 *means* — reach the **Supervisor** before leaving the house — is service policy a hospital may legitimately state differently. That there are exactly four tiers ordered by time-to-action rather than severity is ADR 0001's argument, and it is structural.

## Considered Options

- **Put every number in the clinical content.** Maximum adaptability to local policy, and the right answer for a product with many customers. Rejected because it makes the prototype's central safety claim deniable — and the prototype has no customers, it has one argument to win.
- **Put almost nothing in content — only the element lists and the intervals §8 already names.** Smallest thing to build. Rejected because the edits a clinician makes most often ("also record weight", "add sick-day rules to the Self-Care Check") would each become a code change and a wait, which is the precise problem N8's owner/version/review-date fields exist to avoid.

## Consequences

**Every content file needs a named owner before Phase 1 ships.** N8 requires it as data, and every file under `docs/clinical-content/` currently declares the owner **Unassigned** and the review date **Unset** rather than inventing either (N6, §6). Unowned clinical content with a review date nobody holds is the failure mode N8 was written against.

**A content file can be wrong, and the tests must cover that.** Moving a surveillance interval out of code does not move it out of scope: a malformed or missing content file has to fail loudly at load, never silently produce an empty **Physical Examination** element list. That is §4.10's **Unreachable** discipline turned on Noor's own data — a missing input is declared, not treated as an absence.

**Editability is not authority.** A clinician editing an interval is not thereby permitted to edit anything the code holds, and nothing in the content can widen what Noor is allowed to do. It can only describe clinical detail inside limits the code already enforces.
