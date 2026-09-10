# The Supervisor reviews in Noor; the EMR records the outcome

Supervisor review of a Visit's items — Tier 1-and-above Recommendations, **Goal of Care** ratification, manually flagged items, and the **Silence Audit** (§5.12) — happens in Noor. The **Write-Back** to the EMR (§4.9) is unchanged and remains the record. What this decision fixes is where the *decision* is made, not where it is stored.

**The reason is N5, and it is the same reason the Field Team uses Noor at all.** Automation bias runs at RR **1.26** — clinicians follow erroneous advice more often than they follow no advice — and inexperience raises the risk. The mitigations with evidence behind them are to display the system's reasoning, show per-recommendation confidence, and reduce the prominence of weak advice. A Supervisor asked to ratify *"target 135/85"* from a task queue has none of that. The number is meaningless without the guideline lineage it came from, the office anchor it was **not** derived by offsetting (§4.4), the comorbidities that set the band, and the **Self-Care Findings** from inside the house that may already contradict it. §4.9 names this failure in its own words: structure without reasoning "reproduces the 6.0% app-fatigue finding one actor downstream, in the Supervisor's inbox instead of the clinician's chart."

**The two-actor handoff is the design's largest unvalidated assumption (§3), and it is the one thing a prototype can put in front of a hospital.** Routing an item into a queue Noor cannot see makes the handoff unobservable — and §4.12 already concedes the prototype cannot demonstrate that a Supervisor *acts*. Hosting the review is what converts that concession from permanent to testable.

**§1's boundary generalises rather than bends.** Noor owns the visit and its review; the EMR owns the record of both. The Supervisor's surface is read-mostly — review, ratify, return with comment, sign off — and it never edits a Visit. §5.9's terminal-state immutability holds unchanged, and corrections remain **Addenda**.

## Considered Options

- **Write structured tasks to the EMR and let the Supervisor work from their existing worklist.** Operationally cheaper, integrates with a habit that already exists, and needs no second surface. Rejected because the EMR task is the wrong *shape*, not the wrong *destination*: a due-dated one-line instruction is exactly the "narrative text wearing structure's clothes" inversion — structure with the reasoning stripped out. It also makes N4 unusable at the review layer, because a Supervisor's disagreement recorded in someone else's queue never returns to Noor as data about the rule.
- **No Supervisor surface at all; prove the Write-Back with tests.** Rejected: §3 requires the handoff to be the spine of the Golden Case, and a spine that exists only in test output cannot be shown to the people whose objection decides whether Noor is adopted.
- **Build the inbox as prototype scaffolding, to be deleted at EMR integration.** Rejected because the provenance display is the entire clinical argument. Scaffolding by definition skips it, which would demonstrate the queue and not the thing that makes the queue worth having.

## Consequences

**Noor has two surfaces and two roles.** The Field Team's is a capture surface on a shared tablet (§5.13); the Supervisor's is a review surface, remote, and asynchronous by design (§4.4). They share the Visit and share nothing else. The Supervisor is never an actor inside a Visit and never appears in §5.13's attribution table.

**Review remains per item, never per Visit** — ADR 0003, unchanged. The inbox is therefore a list of items drawn from many Visits, not a list of Visits, and "this Visit has items awaiting review" stays derived on read.

**Amended 2026-09-05: the inbox groups those items by Patient** (`docs/frontend_ssot.md` and the web page design, now integrated in the React frontend) — most pressing first under the same three bands, Tier 3 first, then due time, then the Silence Audit — because a Tier 2 item and an unratified Goal of Care for one Patient are one conversation. Grouping changes the arrangement, not the grain: answering stays per item, and only a Review Verdict closes one (ADR 0009).

**The latency of ratification becomes measurable, and must be measured.** §4.4 records that the only analogous evidence — radiology over-read — found *delay*, not error, to be the quantified cost of a ratification safeguard, and that therapeutic inertia is the disease an explicit target exists to treat. A queue Noor hosts is a queue Noor can instrument; a queue in someone else's EMR is not.

**A hospital may hear this as "Noor wants to replace our consultant worklist."** It does not: the Write-Back still lands in the EMR with an owner and a due time, and that entry remains the system of record. What happens in Noor is the review of Noor's own output, in the place where Noor's own reasoning lives. Both are true simultaneously, and the pitch has to say both.

**Reversal is cheap in correctness and expensive in argument.** If a service insists that review happen in its own queue, nothing about ADR 0003 or §4.9 changes — **Completed** is still the Field Team's act and the Write-Back is still structured. What is lost is provenance at the point of decision, which is a clinical regression rather than a technical one.
