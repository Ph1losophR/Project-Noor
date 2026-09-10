# The Supervisor's answer is recorded, not enforced

The Supervisor's inbox has to be able to empty. Every route into it is derived from
the Visit each time it is read (§5.1), so an item that is merely looked at is still
there tomorrow, and an inbox that never empties is the alert fatigue this project
exists to avoid, reproduced one actor downstream.

The obvious way to make an answer matter is to require it before the Field Team may
act. That is the opposite of what N4 admits, and the place it would bite is a house
with no signal.

## Decision

Each item routed to the Supervisor (§5.12) can be closed by one record, a **Review
Verdict**: **agreed** or **disagreed**, the Supervisor's name, the time, and a note
that a disagreement must carry. That record is the only thing that removes an item
from the inbox.

It is an answer and nothing more. It never undoes an override, never reopens a Visit,
never gates a close, and never makes the next Visit conditional on itself. It is not a
fifth structured reason (§5.10): nothing routes on it, and those four lists are engine
data precisely because something does.

**Goal of Care ratification keeps its own record.** Agreeing *is* ratifying the
target, which the Goal already carries with its ratifier and its time, so a second
record would be a second copy of the same fact. Disagreeing leaves the Patient with no
ratified target, and that item stays open — correctly, because the clinical question
is still open and Noor is still withholding everything that depends on a target
(§4.11).

## Considered Options

- **Require the Supervisor's agreement before an override takes effect.** Rejected.
  N4 admits no hard stops, and this is one at the worst address: a Field Team in a
  house with no connectivity could neither close (§5.8, ADR 0003) nor leave (§4.10).
  The evidence points the same way — reviewers agreed with the clinician in **95.6%**
  of overrides of *valid* alerts, and adverse events followed only **2.3–6%** — so the
  gate would obstruct nineteen decisions out of twenty to catch the twentieth, and
  would catch it after the team had gone home either way. §5.13 finishes the argument:
  attribution is not permission, and gating the record does not gate the act.
- **Keep routing only, and store no answer.** Rejected. The inbox then never empties,
  the **Silence Audit** measures recall no better than not sampling at all, and
  *answered past its window* is uncountable — which leaves the one thing §4.12 calls
  the largest unvalidated assumption in the design unmeasured by the prototype built
  to test it.
- **Let opening an item clear it.** Rejected. *Seen* is not an answer, and a surface
  that empties on being read is the 6.0% app-fatigue finding with extra steps. It also
  has nothing to store: the inbox is derived, so a read leaves no trace to derive from.

## Consequences

The store gains a verdict per review row and the inbox filters on its absence. Two
numbers become countable that were not: time-to-answer against each route's window,
and the disagreement rate on the Silence Audit, which is the only reading Noor gets on
a rule that never fired (N8). The Supervisor's surface stays read-mostly and still
never edits a Visit, so §5.9 holds unchanged.

What this does not do is demonstrate that a real Supervisor answers. The prototype
runs as one process with both surfaces in it (ADR 0006), so it shows that the question
arrives, is answerable, and is measured — not that the handoff survives real latency
and two people working at once. §4.12's limit stands exactly as written.
