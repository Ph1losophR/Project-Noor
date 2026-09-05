# Project Noor — Testing Standards

**Status:** Reference, v0.2, 2026-09-05. Subordinate to `project_noor_architecture.md` (the SSOT).

This document says *how* to test. The SSOT says *what must be true*. Where the two
disagree, the SSOT wins and this file is wrong — fix it here, not there.

Section references in the form §N point at the SSOT; **N1**–**N8** are its eight
non-negotiables (§2); ADRs are cited by filename.

This is engineering practice, not clinical content. ADR 0007's governance — a named
owner, a source, a version, a review date, as data — applies to
`docs/clinical-content/`, not to this file.

**Phase 1 Backend Pass 1 exists** under `src/noor/` — store, domain, EMR seam,
dispatch, content and serialisation — and the rungs below are verified against
that tree. The web layer (`src/noor/web/`) is next. Where a rung cannot exist
until a later phase, it says so rather than sitting there looking overdue. Where
a name is illustrative rather than decided, it says that too — the module and
function names are fixed in `src/noor/`, not in this file.

---

## Core mental model

Tests are executable documentation of intended behaviour. If the source were
deleted, the suite alone should say what the system does.

For Noor there is a second reason, and it is the larger one. §4.1 makes **the
accuracy of Noor's silence** the property the whole deliverable is judged on: a
Visit that produces no **Recommendation** must be distinguishable from an engine
that has stopped working. Nothing about a quiet system is visible by looking at
it, and 93% of CMIOs have seen a CDS malfunction (N8). **An invariant that is not
a test is a comment.** The suite is the safety case — and on the Golden Case it
is the *only* evidence that anything ran at all.

---

## The FIRST properties

- **Fast** — the domain logic performs no I/O. A slow domain test means something
  crossed the seam.
- **Independent** — no test depends on another having run, and order is arbitrary.
  One SQLite file (`docs/adr/0006-offline-by-locality.md`) makes isolation cheap
  and also makes it easy to lose: a test that leaves rows behind is a bug in the
  test.
- **Repeatable** — same inputs, same result, always. No wall clock inside the
  logic under test, no randomness, no network. Time enters as an explicit value.
  This is not test hygiene borrowed from elsewhere: §5.5 requires it of the
  product, because *starting a Visit freezes the engine's inputs*. A test that
  cannot pin the clock is exercising something the SSOT forbids.
- **Self-validating** — binary pass/fail. Never "read the log and see".
- **Timely** — and for a rule, more than timely: its case row is written *before*
  the rule and must fail first.

---

## Structure: Arrange–Act–Assert

Every test, no exceptions. Three blocks, in that order, separated by a blank line.

- **Arrange** — build the world. One Patient, one Visit, the inputs under test.
- **Act** — one call. If a test has two acts it is two tests.
- **Assert** — the observable outcome. Prefer one assertion of a whole value over
  five assertions of its parts; a diff of the whole object says more on failure
  than the first field that happened to differ.

No logic in a test — no `if`, no loop, no `try`. A branch in a test means the test
does not know what it expects. Table-driven rows are the exception that proves the
rule: the *data* varies, the *code path* does not.

### Names are sentences

A test name states the behaviour, so a failure list reads as a specification of
what broke. Noor's vocabulary is fixed in `CONTEXT.md` — use it, and never the
words that entry marks *Avoid*.

Good:

```
test_a_visit_cannot_reach_completed_while_an_emergency_record_is_unresolved
test_an_unreachable_prescribed_list_is_never_recorded_as_absent
test_the_fourth_recommendation_is_filed_rather_than_dropped
```

Bad — these name the code, not the behaviour, so a failure says nothing:

```
test_complete_visit
test_engine_returns_correctly
test_edge_case_2
```

### Behaviour, not implementation

Never assert that an internal function was called. `assert engine._score.called`
passes on an engine that computed the wrong answer and fails on a correct one that
was refactored, which is exactly backwards. Assert what a clinician would see: the
**Findings**, the **Recommendations** and their **Escalation Tiers**, the Visit's
state, what reached the **Write-Back**.

### Assert the distinction, not the truthiness

Two of Noor's taxonomies exist precisely because collapsing them is the failure
mode. A test that collapses them passes on a broken engine.

**Inputs have three states — Present, Absent, Unreachable (§4.10).** `Absent` is a
clinical fact; `Unreachable` is Noor not knowing. In most languages both are falsy,
so `assert not value` is the assertion that hides the bug N6 exists to catch. Every
test touching a missing input asserts *which of the three* is held. There is one
Unreachable state and not two (§4.10) — do not test for a distinction the SSOT
declines to make.

**A Recommendation that did not appear has four different reasons, and they are
not interchangeable.** Which one is a claim the test must make:

| Outcome | Meaning | First exists in |
|---|---|---|
| Fired | A Recommendation was produced | Phase 1.5 |
| Evaluated, did not fire | The rule ran; the Patient did not meet it. N8's log | Phase 1.5 |
| Withheld | An input did not support an opinion, and the missing input is named (§4.11) | Phase 1.5 |
| Suppressed | Produced, then withheld because a **Self-Care Finding** corrupted its signal, recorded and visible to the **Supervisor** (ADR 0002) | Phase 3 |

Separately, a Recommendation that fired is either shown or **Filed** — valid,
wanted, and out of slots (§4.7). Filed is not an outcome above; it is what happened
to one of them.

A test that accepts *evaluated, did not fire* where *withheld* is correct is a bug
in the test, and the bug it lets through is the one §4.1 says the deliverable is
judged on.

### Suppression needs a row in both directions

ADR 0002 states the obligation: a Suppression test asserts both that the
Recommendation is absent **when** the corrupting Finding is present, *and* that it
is present when that Finding is not. Asserting only the non-firing half would pass
against an engine that had simply stopped working. The same shape applies to every
withholding trigger in §4.11's table — including the fourth, where the absent
suppressor must not be read as evidence that the condition is absent.

### Boundaries, not the middle

The happy path is the least informative test in the file. Spend the effort on the
edges, because that is where a clinical system does harm:

- **On the threshold, either side of it, and one step away.** A rule that fires
  above a number gets a row *at* the number. Which side the boundary falls on is a
  clinical decision and belongs in the clinical content, not in a test's guess.
- **Empty, one, many, and the cap.** For the N3 cap that means zero, one, three,
  and four Recommendations — four being where **Filed** first appears.
- **Every enum's every member**, including the `Other + free text` row that ends
  every reason list (§5.10).
- **Resolved with no content**, for every section that can be. §5.8's bar is
  *resolved*, not *filled*, so a section carrying only a structured reason is a
  passing Visit and must be tested as one. The Emergency record is the one thing
  this does not apply to, and it needs the opposite row: an Emergency with no
  timeline entry is refused (§5.7).

### Invalid transitions carry at least the weight of valid ones

The six-state machine (§5.1) has **seven** valid transitions:

| From | To |
|---|---|
| Scheduled | In Progress, Cancelled |
| In Progress | Completed, Ended Early, Emergency |
| Emergency | In Progress, Ended Early |

Completed, Cancelled and Ended Early are terminal and immutable (§5.9); the only
way a closed Visit changes is an **Addendum**.

The suite therefore walks the whole grid, not the seven. Six states against six
targets is thirty-six ordered pairs; seven are legal, and the remaining twenty-nine
are each asserted to be refused. Those twenty-nine are worth more than the seven,
because the seven are what a developer writes anyway and the refusals are what a
rushed Field Team will find. Two properties deserve their own tests:

- **Emergency is re-entrant.** In Progress → Emergency → In Progress → Emergency
  again is legal, and each entry has its own start and end time (§5.7). A test that
  assumes one Emergency per Visit encodes a rule the SSOT does not have.
- **No terminal state is reachable while an Emergency record is unresolved** —
  Completed *and* Ended Early, since Ended Early is the Emergency's other exit
  (§5.7, §5.8). Gating one of the two enforces nothing, so both get a test.
  *Unresolved* has two shapes and each gets its own row: no end time, and no
  timeline entry. The Emergency's bar is stricter than a section's — an end time
  *and* at least one entry, with no structured-reason path (§5.7) — so a test that
  closes an Emergency by ending it alone is asserting the wrong rule.

---

## The rungs, in build order

§8 fixes the build order, so it fixes the order these arrive in. A rung that cannot
exist yet is named here anyway, with the phase that brings it — an absent rung
should look scheduled, not forgotten.

### Phase 1 — the workflow shell

1. **Clinical content loads, or the process refuses to start.** ADR 0007 makes
   clinical judgement versioned data. A malformed file, an unknown field, a missing
   N8 header field (owner, source, version, review date) fails at load with the
   file and the field named. Content that silently half-loads is the 93% CMIO
   malfunction with a config file in front of it. Both directions: a valid file
   loads, an invalid one raises.
2. **The six-state machine** — the seven transitions, the twenty-nine refusals, the
   re-entrant Emergency, the terminal-immutability rule and the **Addendum** as its
   one exception. Start settles the Visit's kind from completed history (ADR 0008)
   and copies the attending pair from the Patient's standing assignment (§5.5,
   §5.13) — copied, not referenced. The inbox is derived on read and only a
   **Review Verdict** closes a row: agreed or disagreed with author and time, a
   note required on disagreement, Goal ratification keeping its own record, and a
   missing verdict blocking nothing (ADR 0009). An **Addendum** sends a Write-Back
   of its own with no owner and no due time, and its author may also flag it to
   the Supervisor as a manual flag on Tier 1's window (§5.9).
3. **The eight sections** — the fixed record order, none absent, **Resolved** in
   both of its forms, and the one place the record's order and the working order
   differ: **Notes** is eighth in the record, and the **Care Plan** is assembled
   after all seven others including Notes (§4.2).
4. **Structured reasons are engine data, not prose** (§5.10, `docs/clinical-content/reason-lists.md`). Every list's every
   row round-trips, `Other` carries its free text, and a **Cancelled** or **Ended
   Early** Visit without a reason is refused.
5. **The Completed gate, with Recommendations built by hand.** Phase 1 has no
   producer, so the override and disposition path is exercised by constructing
   Recommendations in the Arrange block. This is not a workaround; it is what §8
   means by *"the `Recommendation` type and its disposition lifecycle exist with no
   producer"*. **An override never blocks (N4)** — the test that proves it is a
   Visit reaching Completed with every Recommendation overridden.
6. **A whole Visit completes with the EMR unreachable** (§4.10). Not a unit test of
   a fallback — the full path from **Scheduled** to **Completed** with the boundary
   refusing every call. Six of the eight sections must be unaffected; the other two
   must degrade *and say so*.
7. **The fixtures are hostile** (§4.9). A fixture that cannot fail cannot
   demonstrate N6, so the suite carries the misbehaviour the SSOT names: no HbA1c
   in eighteen months, a free-text allergy, a request that times out, an
   unrecognised drug name, a write the EMR rejects. Each one is a test, not a
   scenario in a document.
8. **The Golden Case — the silent Visit** (§4). One end-to-end test asserting the
   **whole Finding set**, not that it is non-empty and not that it contains a
   particular Finding. Equality against the complete expected set is what makes a
   Finding that quietly stops being produced a failure. In Phase 1 the
   zero-Recommendation half of the case is trivially true, because nothing produces
   one; it becomes a real assertion in Phase 1.5, and the test is written now so
   that it does.
9. **The Silence Audit's floor** (`docs/clinical-content/response-windows.md`). At
   four silent Visits, 10% is zero and the floor must still yield one per week.
   The floor is the whole point of the rule, so it is the row that must exist —
   the percentage is the easy case.
10. **The Write-Back's shape** (§4.9). Every item requiring a response carries a
    named **Executor** and a due time derived from the route that produced it.
    An item with neither is refused: *"a Write-Back with no owner and no due time
    is narrative text wearing structure's clothes."* The offline Tier 2 is the
    boundary — due immediately, arriving already overdue, and that is the pass
    condition rather than a defect (§5.11).

### Phase 1.5 — the evaluation harness

11. **One rule, one row, discovered as data.** Rule cases live beside the clinical
    content they exercise and are collected by a single parametrised test, so
    adding a rule means adding a row and no test code. The row is written first and
    must fail before the rule exists (`CLAUDE.md`).
12. **"Evaluated, did not fire" is asserted, not just logged** (N8). A rule that
    silently stops being evaluated is indistinguishable from a rule that evaluated
    and declined — unless a test asserts the log entry.
13. **Release comparison catches the failure to fire.** Running the whole case
    corpus against the previous content version and diffing the outcomes is the
    only cheap way to notice that a content edit made a rule stop firing. A rule
    that fires less is a finding, not an improvement.

### Phase 3 — the full engine

14. **Suppression, both directions** (ADR 0002, §4.6), including that Suppression
    runs *before* the cap so a suppressed Recommendation never competes for a slot.
15. **The N3 cap's ordering, as a strict three-key comparison** — descending
    **Escalation Tier**, then what changes today's action, then descending deferral
    count, and nothing else in the comparison (§4.7). One row per key, plus one
    where the first two keys tie and the third decides.
16. **Tier assignment** (ADR 0001), which is the piece Phase 1.5 deliberately does
    not have.

---

## Invariant tests

Three tests that guard the architecture rather than a behaviour. They fail when
someone innocently breaks a decision, which is the only time anyone will read them.

**The seam.** ADR 0006 puts Noor in one process against one SQLite file, with both
surfaces as routes. That is cheap to build and equally cheap to smear: the first
piece of clinical reasoning written inside a request handler ends the separation
permanently. One test asserts the import direction — the domain logic imports
nothing from the web layer, the store, or the EMR boundary. The module names are the
Phase 1 plan's to fix; the direction is not negotiable.

**Determinism.** The same Visit evaluated twice yields the same Findings and the
same Recommendations. Cheap to write, and it fails the moment a wall clock, a
dictionary iteration order, or an unseeded random gets into the decision path —
each of which puts non-determinism where N7 allows only deterministic rules.

**No clock in the decision path.** Time is a parameter. A test that must sleep, or
that behaves differently after midnight, is reporting a design defect in the source
and gets fixed there (§5.5).

---

## Isolation and the store

Default: **each test gets its own database file**, created empty and discarded at
teardown. One SQLite file is the production shape (ADR 0006), and a temporary copy
of it per test costs microseconds — cheap enough that nothing is gained by being
clever, and it makes cross-test leakage structurally impossible rather than a thing
to remember. If the suite ever gets slow enough to matter, the upgrade is a
per-test transaction rolled back at teardown; do that when the clock says to, not
before.

Never share a database between tests, never rely on insertion order, never assert on
an auto-generated identifier's value.

**Mock at the EMR boundary and nowhere else.** The hostile fixtures *are* that mock,
so nothing else needs one. Mocking the engine or the state machine tests the mock.

---

## Coverage

**Branch** coverage, no exclusions (`CLAUDE.md`). An untested branch fails the
suite. That setting is only survivable because ADR 0006 keeps the logic out of the
browser — which is another way of saying: if a branch is hard to cover, the answer
is usually that it is in the wrong layer.

Coverage measures which lines ran, not whether the assertions were right. A
Golden Case with no assertions at all reports 100%. It is a floor and never
evidence.

---

## Layout

Tests mirror the source tree under `tests/`, one test module per source module, plus a small number
of end-to-end modules named after the journey they walk rather than the code they
touch — the Golden Case, the offline Visit, the Emergency. Shared setup lives in
fixtures; shared *assertions* do not, because a helper that asserts hides which
property failed.

The rule that outlives the tree:
a developer looking for the test that covers a behaviour should find it by guessing.

---

## Routine changes and what each one owes

| Change | Owes |
|---|---|
| A new rule | A case row, written first, failing first. Plus a row for the boundary and one for each §4.11 trigger that applies |
| A new Visit state | A full redraw of the transition grid — the new refusals as well as the new successes |
| A new section in the Visit Protocol | Its **Resolved with no content** case, its reason rows (§5.10), and its position in the record's fixed order |
| A new reason row | A round-trip test, and a check that it does not duplicate a row already there — §5.10 makes the *Other* rate a metric with authority over the list |
| A content edit | The release comparison (rung 13). A rule that now fires less is a finding |
| Any change to a documented behaviour | The doc surface that documents it, in the same change |

---

## The non-negotiables

Short enough to check against before committing:

1. Arrange–Act–Assert, always. One act per test.
2. Test names are sentences about behaviour, in `CONTEXT.md`'s vocabulary.
3. Never assert that an internal function was called.
4. Present / Absent / Unreachable are asserted as three, never as truthiness.
5. Every withholding and every Suppression is tested in both directions.
6. Invalid transitions carry at least the weight of valid ones.
7. A new rule's case row is written first and must fail first.
8. Time is a parameter. No sleeping, no wall clock, no randomness.
9. No branching or looping inside a test.
10. Branch coverage, no exclusions.
11. A hard-to-write test is a source defect. Fix the source.
12. No flaky test survives. Fix it or delete it — a test nobody trusts is worse than
    no test, because it teaches the team to ignore a red suite, which is N3's
    alert-fatigue failure relocated into the toolchain.

---

## What a green suite does not mean

A green suite means Noor does what this project decided it should do. It is not
clinical validation, it does not establish that the rules are right, and it says
nothing about whether the numbers in `docs/clinical-content/` are the correct
numbers — those need the named owner N8 requires and still does not have (§6).

Do not let anyone report it as clinical validation, including in the pitch.

Out of scope by decision rather than omission, each recorded in §6 rather than here:
authentication and device security; real network latency between the two surfaces;
performance and load; and anything requiring a purchased service, since the project
is zero-cost by constraint.
