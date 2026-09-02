# Response windows and the audit rate

Service policy. Clinical content under `docs/adr/0007-clinical-content-is-data.md` — a hospital may legitimately state these differently. Routing and roles: §5.12, ADR 0001.

| N8 field | Value |
|---|---|
| Version | 0.1 |
| Dated | 2026-08-28 |
| Source | Reasoned in the §5.12 grilling session. No external policy source — declared, not implied |
| Owner | **Unassigned.** N8 requires a named owner before Phase 1 ships |
| Review date | **Unset.** Set with the owner |

## The tier windows

A tier's window is what "derived from the tier" resolves to wherever the SSOT uses that phrase.

| Tier | Deadline |
|---|---|
| Tier 0 | *No Supervisor.* The Field Team acts alone, no response is required, and no due time exists (§4.9) |
| Tier 1 — act, then review | **72 hours** |
| Tier 2 — reach the Supervisor before acting | **During the Visit.** Zero window by definition (ADR 0001). Unreachable → shown, marked not executable, queued as a pending Write-Back item **due immediately, arriving already overdue** (§5.11) |
| Tier 3 — emergency | **Now**, with the Supervisor off the critical path |

## The four Supervisor routes

The routes are §5.12's, and every one of them carries a response obligation.

| Route | Obligation |
|---|---|
| Tier 1 and above | The tier's window, above |
| **Goal of Care** ratification | **7 days** |
| Manual flag | The flagged item's tier window — or **Tier 1's 72 hours** where that item is Tier 0, since asking for review of something already done is Tier 1's shape (§5.12) |
| **Silence Audit** | Not a deadline but a sampling rate: **10% of silent Visits, and no fewer than one per week** |

## Why these numbers

**Tier 1 is 72 hours because a permanently overdue queue is an unread queue.** The Field Team has already acted; this review is a safety net, not a gate. Three days of a marginally wrong titration is tolerable in chronic disease. A queue where everything is red carries no information, and the next thing that happens is that nobody opens it — which is the 6.0% app-fatigue failure §4.9 warns about, relocated one actor downstream to the Supervisor's inbox. The tighter window buys a faster catch and risks losing the reviewer entirely.

**The one item class that is meant to arrive red is the offline Tier 2.** Its window is zero, so it is overdue from creation, and that is the signal rather than a defect: it marks the Visits where the routing did not work. Giving it a grace period would hide exactly those (§5.11).

**Ratification is 7 days because a target ratified in ten minutes is a target rubber-stamped.** N5 puts automation bias at RR **1.26**, and rubber-stamping is precisely the failure this step exists to prevent — the Supervisor is supposed to read the lineage, the comorbidities and the **Self-Care Findings** from inside the house, and to disagree where they should. Seven days is also short enough not to block the first **Routine Visit**, and the household is not empty-handed meanwhile: the **Baseline Visit** already emits a **Between-Visit Plan** carrying the measurement schedule and the stop rules (§4.8).

It is not open-ended, and that is deliberate. §4.4 records that therapeutic inertia is the disease an explicit target exists to treat. A safeguard with no deadline becomes the inertia it was meant to cure, and Noor stays silent for the whole of it.

**The audit floor matters more than the percentage.** At prototype volume, 10% of four Visits is zero Visits — the audit never runs, and the one property §4.1 says the deliverable is judged on is never once demonstrated. The floor keeps it alive at low volume; the percentage takes over as volume grows.

## What must be measured, not assumed

§4.4 requires ratification **latency** to be measured rather than asserted, because the only analogous evidence — radiology over-read — found *delay*, not error, to be the quantified cost of a ratification safeguard. These numbers are the target. The measured distribution is the finding, and where the two disagree, the measurement wins and this file changes.

## The data

```toml
[meta]
version = "0.1"
dated = "2026-08-28"
source = "Reasoned in the §5.12 grilling session. No external policy source — declared, not implied"
owner = "Unassigned"
review_date = "Unset"

[windows]
tier_1_hours = 72
tier_2_hours = 0            # zero by definition (ADR 0001) — offline, already overdue
ratification_days = 7

[audit]
silent_visit_rate = 0.10
minimum_per_week = 1
```
