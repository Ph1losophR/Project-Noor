# Backend Pass 2 — the four things the web layer needs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the four backend facts `docs/web_plan.md` §9 items 1–5 say Phase 1 has not built yet, so the web layer (item 6, its own plan) has a store and a domain to render.

**Architecture:** Four independent tasks, each a store read/write plus the pure domain it needs. Task 1 (Field Team) has the widest blast radius and lands first. Task 2 (Review Verdict) and Task 3 (Addendum) are independent of each other. Task 4 (the inbox) consumes Task 2's verdict filter and Task 1's Visit fields, so it lands last. Nothing here builds a screen, a route, or a template — item 6 owns all of that.

**Tech Stack:** Python 3.12, SQLite via the stdlib `sqlite3` (no ORM), `pytest` with branch coverage. No new dependencies.

## Global Constraints

- **The SSOT ranking holds:** `project_noor_architecture.md` > `docs/frontend_ssot.md` > `docs/web_plan.md`. This plan implements web_plan §9; where it would contradict a higher document, stop and raise it.
- **Vocabulary is enforced (`CONTEXT.md`).** The pair is the **Field Team**: a **Junior Physician** and a **Nurse**. Never `attending`, `doctor`, `resident`, `care team`, `crew`, `RN`, `nursing staff`. The Supervisor's answer is a **Review Verdict**. The closed-Visit addition is an **Addendum**.
- **No migration story (ADR 0006).** One SQLite file, one process; deleting the file is the migration. Schema changes edit the `create table` statement only — every test opens a fresh `tmp_path` database, so a changed `CREATE` takes effect with no `ALTER`.
- **The seam holds (`tests/test_seam.py`).** `src/noor/domain/*` imports nothing from `noor.store`, `noor.serial`, `noor.dispatch`, `noor.emr`, `noor.web`, or `sqlite3`. Store-may-import-domain; domain-may-not-import-store. No domain module reads the wall clock — time is always a parameter.
- **Branch coverage at `fail_under = 100`, `exclude_lines = []`.** One untested branch fails the suite. Every `if` added here needs both outcomes exercised. Run `pytest` (whole suite) before and after every task; it must be green.
- **Test design (`docs/testing-standards.md`):** Arrange–Act–Assert, one act per test, test names are full sentences describing behaviour, no branching or looping inside a test, invalid transitions tested as hard as valid ones.
- **Comments short (1–3 sentences). Surgical changes only** — every changed line traces to §9 items 1–5.

---

## File Structure

**Modified — source:**
- `src/noor/schema.sql` — three new tables (`verdicts`, `addenda`) and two new columns on `patients`.
- `src/noor/domain/visit.py` — two new `Visit` fields, a widened `start()`, and the `Addendum` record.
- `src/noor/domain/supervisor.py` — the `Verdict` record, `VerdictKey`, `key()`, `unanswered()`, and `band()`.
- `src/noor/domain/writeback.py` — `Kind.ADDENDUM` and the `addendum_item()` builder.
- `src/noor/serial.py` — the two new `Visit` fields into `dump_visit`/`load_visit`.
- `src/noor/store.py` — `FieldTeam`/`field_team`, the verdict trio, the addendum group, and `inbox`.
- `src/noor/dispatch.py` — `send_addendum` and a second loop in `drain`.

**Modified — tests:** `tests/test_store.py`, `tests/test_dispatch.py`, `tests/domain/test_visit.py`, `tests/domain/test_supervisor.py`, `tests/domain/test_writeback.py`, `tests/test_serial.py`, `tests/test_journeys.py`, `tests/test_prefetch.py` (the last four only for the Task 1 call-site propagation).

No new files. Every fact belongs in a module that already holds its neighbours.

---

## Task 1: The Field Team pair

**Files:**
- Modify: `src/noor/schema.sql` (the `patients` table)
- Modify: `src/noor/domain/visit.py` (the `Visit` dataclass and `start()`)
- Modify: `src/noor/serial.py` (`dump_visit`, `load_visit`)
- Modify: `src/noor/store.py` (`add_patient`, new `FieldTeam` + `field_team`)
- Test: `tests/domain/test_visit.py`, `tests/test_serial.py`, `tests/test_store.py`
- Propagate: `tests/test_journeys.py`, `tests/test_dispatch.py`, `tests/test_prefetch.py`, `tests/domain/test_supervisor.py`, `tests/domain/test_writeback.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces:
  - `Visit.junior_physician: str | None` and `Visit.nurse: str | None` (fields, `None` until Start).
  - `Visit.start(self, at: datetime, kind: VisitKind, *, junior_physician: str, nurse: str) -> None` — the two are now **required keyword-only**.
  - `store.FieldTeam(junior_physician: str, nurse: str)` (NamedTuple).
  - `store.field_team(conn, patient_id: str) -> FieldTeam` — raises `StoreError` on an unknown Patient.
  - `store.add_patient(conn, patient_id, name, conditions, *, junior_physician: str, nurse: str) -> None` — the two are now **required keyword-only**.

**Why this shape (§5.13, CONTEXT.md "Field Team"):** the pair is a standing assignment to the *Patient*; the Visit *records the pair that attended, copied at its Start, so a later reassignment never restates who performed a Visit that has already closed*. The store holds the standing pair; `start()` snapshots it onto the Visit. The domain cannot import the store (seam), so `start()` takes two strings rather than a `FieldTeam`, and the web layer (item 6) will read `field_team()` and pass its two fields in.

- [ ] **Step 1: Write the failing test — Start stamps the pair onto the Visit**

In `tests/domain/test_visit.py`, add two module constants below the existing `NINE`/`TEN` block (near line 27) and one test. The existing `started()` helper (line 30) and every other `.start(` call will be updated in Step 6; write this test using explicit values so it stands alone:

```python
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


def test_the_start_records_the_field_team_that_attended():
    # Arrange — §5.13: the pair is copied onto the Visit at its Start
    subject = Visit("v-1", "p-1")

    # Act
    subject.start(NINE, VisitKind.ROUTINE,
                  junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)

    # Assert
    assert (subject.junior_physician, subject.nurse) == (JUNIOR_PHYSICIAN, NURSE)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/domain/test_visit.py::test_the_start_records_the_field_team_that_attended -v`
Expected: FAIL — `TypeError: start() got an unexpected keyword argument 'junior_physician'`.

- [ ] **Step 3: Add the two fields and widen `start()`**

In `src/noor/domain/visit.py`, insert the two fields immediately after `kind` (line 32), before `state`:

```python
    kind: VisitKind | None = None
    # The Field Team that attended, copied off the Patient at the Start (§5.5, §5.13).
    # None until then, like `kind`: a Scheduled Visit has no attendance record yet, and a
    # later reassignment must never restate a closed Visit's pair.
    junior_physician: str | None = None
    nurse: str | None = None
    state: VisitState = VisitState.SCHEDULED
```

Replace `start()` (lines 57–61):

```python
    def start(self, at: datetime, kind: VisitKind, *,
              junior_physician: str, nurse: str) -> None:
        check_transition(self.state, VisitState.IN_PROGRESS)
        self.state = VisitState.IN_PROGRESS
        self.kind = kind
        self.junior_physician = junior_physician
        self.nurse = nurse
        self.started_at = at
```

- [ ] **Step 4: Write the failing serial round-trip test**

In `tests/test_serial.py`, add below `test_a_started_visits_kind_round_trips` (line 71):

```python
def test_the_field_team_round_trips():
    # Arrange
    subject = scheduled()
    subject.start(NINE, VisitKind.BASELINE,
                  junior_physician="Dr Layla Al-Amri", nurse="Nurse Huda Al-Zahrani")

    # Act
    result = reloaded(subject)

    # Assert
    assert (result.junior_physician, result.nurse) == (
        "Dr Layla Al-Amri", "Nurse Huda Al-Zahrani")
```

Run: `python -m pytest tests/test_serial.py::test_the_field_team_round_trips -v`
Expected: FAIL — `KeyError: 'junior_physician'` from `load_visit`.

- [ ] **Step 5: Serialise the two fields**

In `src/noor/serial.py`, in `dump_visit` (after the `"kind"` line, ~169):

```python
        "kind": _maybe(visit.kind, _value),
        "junior_physician": visit.junior_physician,
        "nurse": visit.nurse,
```

In `load_visit` (after the `kind=` line, ~194):

```python
        kind=_maybe_read(raw["kind"], VisitKind),
        junior_physician=raw["junior_physician"],
        nurse=raw["nurse"],
```

Plain nullable strings — no codec, `None` survives JSON as `null`.

Run: `python -m pytest tests/test_serial.py::test_the_field_team_round_trips -v`
Expected: PASS.

- [ ] **Step 6: Propagate the now-required arguments to every existing call site**

Widening `start()` and (next step) `add_patient` breaks every existing caller until each passes the two new keyword arguments. The transformation is uniform:

```
X.start(<at>, <kind>)
  →  X.start(<at>, <kind>, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
```

Where a test file has no `JUNIOR_PHYSICIAN`/`NURSE` module constant yet, add this block near its other module constants first:

```python
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
```

Files and their `.start(` sites (constants already present in `test_journeys.py`; add them to the other four):
- `tests/domain/test_visit.py` — the `started()` helper (line 33) and the three direct calls (lines 58, 77, 123). The new test from Step 1 already passes them.
- `tests/test_serial.py` — one call (line 65). The Step 4 test already passes them.
- `tests/test_store.py` — five calls: lines 55, 68, 162, 201, and the `ended_early()` helper (line 179).
- `tests/test_dispatch.py` — the `completed()` helper (line 51) and lines 238, 248, 271.
- `tests/domain/test_writeback.py` — the `worked()`-family helper (line 82) and lines 205, 224, 256, 336, 492, 509, 544.
- `tests/domain/test_supervisor.py` — the `visit()` helper (line 33).
- `tests/test_journeys.py` — `a_completed_baseline` (line 171) and lines 241, 369, 504, 532, 575, 632, 668, 681, using the existing `JUNIOR_PHYSICIAN`/`NURSE`.

Do not run the suite yet — `add_patient` is still narrow, so the fixtures fail. The next step closes it.

- [ ] **Step 7: Write the failing `field_team` store test, then widen `add_patient`**

In `tests/test_store.py`, add the two constants near line 16 and three tests below `test_enrolled_returns_all_patient_ids` (line 504). The fixture `conn` (line 19) and line 501 will be updated in the same step:

```python
def test_field_team_returns_the_patients_standing_pair(conn):
    # Act / Assert — the pair the fixture enrolled p-1 with
    assert store.field_team(conn, "p-1") == store.FieldTeam(
        JUNIOR_PHYSICIAN, NURSE)


def test_field_team_raises_when_the_patient_is_missing(conn):
    # Act / Assert — mirrors patient_name(): 400 in the web layer (§4.1), not 500
    with pytest.raises(store.StoreError, match="no Patient"):
        store.field_team(conn, "p-unknown")


def test_reassigning_a_patient_never_restates_who_performed_a_closed_visit(conn):
    # Arrange — a closed Visit that recorded its pair, then the Patient is reassigned
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.start(NINE, VisitKind.ROUTINE,
                  junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    subject.state = VisitState.COMPLETED
    store.save(conn, subject)
    conn.execute("update patients set junior_physician = ?, nurse = ? where id = ?",
                 ("Dr Someone Else", "Nurse Someone Else", "p-1"))
    conn.commit()

    # Act — §5.13: the Visit carries the pair that attended, not today's assignment
    result = store.load(conn, "v-1")

    # Assert
    assert (result.junior_physician, result.nurse) == (JUNIOR_PHYSICIAN, NURSE)
```

Add the constants near line 16:

```python
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
```

Update the fixture (line 22) and line 501:

```python
    store.add_patient(connection, "p-1", "Fatima Ali", ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
```
```python
    store.add_patient(conn, "p-2", "Sara Al-Harbi", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
```

Run: `python -m pytest tests/test_store.py::test_field_team_returns_the_patients_standing_pair -v`
Expected: FAIL — `TypeError: add_patient() got an unexpected keyword argument 'junior_physician'`.

- [ ] **Step 8: Add the columns, `FieldTeam`, `field_team`, and widen `add_patient`**

In `src/noor/schema.sql`, replace the `patients` table:

```sql
create table if not exists patients (
    id                text primary key,
    name              text not null,
    conditions        text not null,  -- json array: "diabetes", "hypertension"
    junior_physician  text not null,  -- §5.13: the Patient's standing Field Team, Noor's
    nurse             text not null   -- own fact, snapshotted onto the Visit at its Start
);
```

In `src/noor/store.py`, widen `add_patient` (lines 62–67):

```python
def add_patient(
    conn: sqlite3.Connection, patient_id: str, name: str, conditions: Sequence[str],
    *, junior_physician: str, nurse: str,
) -> None:
    conn.execute(
        "insert into patients (id, name, conditions, junior_physician, nurse) "
        "values (?, ?, ?, ?, ?)",
        (patient_id, name, json.dumps(list(conditions)), junior_physician, nurse))
    conn.commit()
```

Add `FieldTeam` beside the other NamedTuples (after `Pending`, ~line 47) and `field_team` beside `patient_name` (after line 361):

```python
class FieldTeam(NamedTuple):
    """The Patient's standing pair (§5.13), read here and stamped onto the Visit at its
    Start. A NamedTuple rather than a bare (str, str) so nothing between the store and the
    Start can swap the two."""

    junior_physician: str
    nurse: str
```
```python
def field_team(conn: sqlite3.Connection, patient_id: str) -> FieldTeam:
    """The pair standing assigned to this Patient (§5.13). Mirrors patient_name(): a
    missing Patient raises StoreError so the web layer renders 400 (§4.1), not 500."""
    row = conn.execute(
        "select junior_physician, nurse from patients where id = ?",
        (patient_id,)).fetchone()
    if row is None:
        raise StoreError(f"no Patient {patient_id!r}")
    return FieldTeam(row["junior_physician"], row["nurse"])
```

- [ ] **Step 9: Run the whole suite green**

Run: `python -m pytest -q`
Expected: PASS, 100% coverage. If a call site was missed in Step 6, a `TypeError` names the file and line — fix it and re-run.

- [ ] **Step 10: Commit**

```bash
git add src/noor/schema.sql src/noor/domain/visit.py src/noor/serial.py src/noor/store.py tests/
git commit -m "feat: the Field Team pair, on the Patient and snapshotted at Start (web_plan §9.1)"
```

---

## Task 2: The Review Verdict

**Files:**
- Modify: `src/noor/schema.sql` (new `verdicts` table)
- Modify: `src/noor/domain/supervisor.py` (`Verdict`, `VerdictError`, `VerdictKey`, `key`, `unanswered`, `_closed`)
- Modify: `src/noor/store.py` (`record_verdict`, `answered`, `verdict`, and the supervisor import)
- Test: `tests/domain/test_supervisor.py`, `tests/test_store.py`

**Interfaces:**
- Consumes: `Route` and `Review` (already in `supervisor.py`).
- Produces:
  - `supervisor.Verdict(agreed: bool, by: str, at: datetime, note: str | None = None)` — a `VerdictError` if a disagreement carries no note.
  - `supervisor.VerdictKey(visit_id: str, route: Route, subject: str)` (NamedTuple).
  - `supervisor.key(review: Review) -> VerdictKey`.
  - `supervisor.unanswered(rows: Sequence[Review], answered: set[VerdictKey]) -> tuple[Review, ...]`.
  - `store.record_verdict(conn, verdict_key: VerdictKey, verdict: Verdict) -> None`.
  - `store.answered(conn) -> set[VerdictKey]`.
  - `store.verdict(conn, verdict_key: VerdictKey) -> Verdict | None`.

**Why this shape (ADR 0009):** the Review Verdict *is the only thing that removes an item from the inbox*. It never reopens a Visit, never gates a close. **Goal-of-Care ratification keeps its own record** — agreeing *is* ratifying (via `store.ratify_goal`, already built), so a Verdict on a `RATIFICATION` row would be a second copy; and `_ratification()` already stops raising that route once the Goal is ratified. So `unanswered` never closes a `RATIFICATION` row on a Verdict: a disagreement's note is still recorded and readable, but the row stays open because the clinical question is (§4.11).

- [ ] **Step 1: Write the failing domain tests for `Verdict`**

In `tests/domain/test_supervisor.py`, extend the `supervisor` import (line 11) to include `Verdict`, `VerdictError`, `VerdictKey`, `key`, `unanswered`, then add:

```python
def test_a_disagreement_without_a_note_is_refused():
    # Act / Assert — §5.12: an answer nobody can read is a mark, not an answer
    with pytest.raises(VerdictError, match="note"):
        Verdict(agreed=False, by="Dr Omar Farouk", at=NOW)


def test_a_disagreement_with_a_note_is_recorded():
    # Act
    result = Verdict(agreed=False, by="Dr Omar Farouk", at=NOW,
                     note="the office anchor looks wrong")

    # Assert
    assert result.note == "the office anchor looks wrong"


def test_an_agreement_needs_no_note():
    # Act / Assert — a plain agreement is complete on its own
    assert Verdict(agreed=True, by="Dr Omar Farouk", at=NOW).note is None
```

Run: `python -m pytest tests/domain/test_supervisor.py::test_a_disagreement_without_a_note_is_refused -v`
Expected: FAIL — `ImportError: cannot import name 'Verdict'`.

- [ ] **Step 2: Add `Verdict`, `VerdictKey`, `key`, `unanswered`, `_closed`**

In `src/noor/domain/supervisor.py` (which already imports `dataclass`, `NamedTuple`, and `Sequence` — no import change needed), add below the `Review` class (after line 51):

```python
class VerdictError(ValueError):
    """A Review Verdict missing the note a disagreement must carry (§5.12)."""


@dataclass(frozen=True)
class Verdict:
    """The Supervisor's answer to one routed item (§5.12, ADR 0009): agreed or not, who,
    when, and the note a disagreement must carry. It removes the inbox row and does nothing
    else — never reopens a Visit, never gates a close (§5.9)."""

    agreed: bool
    by: str
    at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.agreed and not (self.note or "").strip():
            raise VerdictError(
                "a disagreement carries a note (§5.12) — an answer nobody can read is a "
                "mark, not an answer")


class VerdictKey(NamedTuple):
    """What identifies the item a Verdict answers: the Visit, the route, and the subject
    within it. The same triple the `verdicts` table is keyed on."""

    visit_id: str
    route: Route
    subject: str


def key(review: Review) -> VerdictKey:
    """The identity of the item this row raises, so a stored Verdict matches back to it."""
    return VerdictKey(review.visit_id, review.route, review.subject)


def unanswered(
    rows: Sequence[Review], answered: set[VerdictKey]
) -> tuple[Review, ...]:
    """The inbox: the derived rows no Verdict has closed (ADR 0009). A row leaves only when
    its Verdict is recorded — nothing here clears by being read (§5.1)."""
    return tuple(row for row in rows if not _closed(row, answered))


def _closed(row: Review, answered: set[VerdictKey]) -> bool:
    """A Ratification row is never closed by a Verdict: agreeing *is* ratifying, and a
    ratified Goal stops raising the route through `reviews()` itself, so a Verdict on it
    would be a second copy (ADR 0009). Every other route closes on its Verdict."""
    return row.route is not Route.RATIFICATION and key(row) in answered
```

Run: `python -m pytest tests/domain/test_supervisor.py -k verdict -v` and the three new tests.
Expected: PASS.

- [ ] **Step 3: Write the failing `unanswered` tests**

In `tests/domain/test_supervisor.py`, add (the file's `visit`, `recommendation`, `WINDOWS`, `NOW`, `reviews`, `Route` are already in scope):

```python
def test_an_item_with_a_recorded_verdict_leaves_the_inbox():
    # Arrange — one Tier 1 review, and the key that answers it
    subject = visit(tiers=(EscalationTier.TIER_1,))
    rows = reviews(subject, goal=None, windows=WINDOWS, at=NOW)
    answered = {key(rows[0])}

    # Act
    remaining = unanswered(rows, answered)

    # Assert
    assert remaining == ()


def test_an_item_with_no_verdict_stays_in_the_inbox():
    # Arrange
    subject = visit(tiers=(EscalationTier.TIER_1,))
    rows = reviews(subject, goal=None, windows=WINDOWS, at=NOW)

    # Act / Assert — an empty answer set removes nothing
    assert unanswered(rows, set()) == rows


def test_a_ratification_is_never_closed_by_a_verdict():
    # Arrange — a Baseline with an unratified Goal raises the RATIFICATION route
    subject = visit(VisitKind.BASELINE)
    rows = reviews(subject, goal=proposed(), windows=WINDOWS, at=NOW)

    # Act — even with its key marked answered, the row stays (ADR 0009)
    remaining = unanswered(rows, {key(rows[0])})

    # Assert
    assert remaining == rows
```

Run: `python -m pytest tests/domain/test_supervisor.py -k "inbox or ratification_is_never" -v`
Expected: PASS (Step 2 already implemented `unanswered`). If `proposed()` is not already defined in this file, it is at line 45 — reuse it.

- [ ] **Step 4: Write the failing store tests**

In `tests/test_store.py`, extend imports with `from noor.domain.supervisor import Route, Verdict, VerdictKey` and add below the Task 1 tests:

```python
VERDICT_KEY = VerdictKey("v-1", Route.TIER, "r-1")


def test_a_recorded_verdict_comes_back_by_its_key(conn):
    # Arrange
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")
    answer = Verdict(agreed=True, by="Dr Omar Farouk", at=NINE)

    # Act
    store.record_verdict(conn, VERDICT_KEY, answer)

    # Assert
    assert store.verdict(conn, VERDICT_KEY) == answer


def test_an_item_with_no_verdict_reads_back_none(conn):
    # Act / Assert — the ordinary case: nothing answered yet
    assert store.verdict(conn, VERDICT_KEY) is None


def test_answered_returns_the_keys_that_have_a_verdict(conn):
    # Arrange
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")
    store.record_verdict(conn, VERDICT_KEY,
                         Verdict(agreed=True, by="Dr Omar Farouk", at=NINE))

    # Act / Assert
    assert store.answered(conn) == {VERDICT_KEY}


def test_re_answering_an_item_replaces_the_earlier_verdict(conn):
    # Arrange — the Supervisor answers, then answers again before the page reloads
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")
    store.record_verdict(conn, VERDICT_KEY,
                         Verdict(agreed=True, by="Dr Omar Farouk", at=NINE))

    # Act
    store.record_verdict(conn, VERDICT_KEY, Verdict(
        agreed=False, by="Dr Layla Nasser", at=NINE, note="reconsidered"))

    # Assert — one record per item, the last answer standing
    assert store.verdict(conn, VERDICT_KEY).note == "reconsidered"
```

Run: `python -m pytest tests/test_store.py::test_a_recorded_verdict_comes_back_by_its_key -v`
Expected: FAIL — `AttributeError: module 'noor.store' has no attribute 'record_verdict'`.

- [ ] **Step 5: Add the `verdicts` table and the store trio**

In `src/noor/schema.sql`, append:

```sql
-- §5.12, ADR 0009: the Supervisor's answer to one routed item, the only record that
-- removes it from the inbox. Keyed on the item's identity — the Visit, the route, and the
-- subject within it — so a re-answer replaces rather than duplicates.
create table if not exists verdicts (
    visit_id     text not null references visits(id),
    route        integer not null,  -- supervisor.Route's integer, one column, no json
    subject      text not null,     -- a Recommendation id, GOAL_OF_CARE, or SILENT_VISIT
    agreed       integer not null,  -- 0/1
    answered_by  text not null,     -- §5.13: a decision carries a name. `by` is a SQL keyword
    answered_at  text not null,
    note         text,              -- required on a disagreement, enforced by Verdict
    primary key (visit_id, route, subject)
);
```

In `src/noor/store.py`, add to the imports (after line 11): `from noor.domain.supervisor import Route, Verdict, VerdictKey`. Add the three functions after `ratify_goal`/`_ratified` (~line 222):

```python
def record_verdict(
    conn: sqlite3.Connection, verdict_key: VerdictKey, verdict: Verdict
) -> None:
    """The one record that removes an item from the inbox (ADR 0009). `insert or replace`,
    because a Supervisor may answer twice before the page reloads — the last answer stands,
    and there is only ever one per item."""
    conn.execute(
        "insert or replace into verdicts "
        "(visit_id, route, subject, agreed, answered_by, answered_at, note) "
        "values (?, ?, ?, ?, ?, ?, ?)",
        (verdict_key.visit_id, verdict_key.route.value, verdict_key.subject,
         int(verdict.agreed), verdict.by, verdict.at.isoformat(), verdict.note))
    conn.commit()


def answered(conn: sqlite3.Connection) -> set[VerdictKey]:
    """Every item that has a Verdict, as keys — what `supervisor.unanswered` filters on.
    One query for the whole inbox, never one per row."""
    rows = conn.execute("select visit_id, route, subject from verdicts").fetchall()
    return {VerdictKey(row["visit_id"], Route(row["route"]), row["subject"])
            for row in rows}


def verdict(conn: sqlite3.Connection, verdict_key: VerdictKey) -> Verdict | None:
    """The recorded answer to one item, or None where none was given. The Patient's page
    reads this to show a disagreement's note beside the item it answered."""
    row = conn.execute(
        "select agreed, answered_by, answered_at, note from verdicts "
        "where visit_id = ? and route = ? and subject = ?",
        (verdict_key.visit_id, verdict_key.route.value, verdict_key.subject)).fetchone()
    if row is None:
        return None
    return Verdict(bool(row["agreed"]), row["answered_by"],
                   datetime.fromisoformat(row["answered_at"]), row["note"])
```

- [ ] **Step 6: Run the whole suite green, then commit**

Run: `python -m pytest -q`
Expected: PASS, 100% coverage.

```bash
git add src/noor/schema.sql src/noor/domain/supervisor.py src/noor/store.py tests/
git commit -m "feat: the Review Verdict, recorded and filtered but never enforced (web_plan §9.2)"
```

---

## Task 3: The Addendum

**Files:**
- Modify: `src/noor/schema.sql` (new `addenda` table)
- Modify: `src/noor/domain/visit.py` (`Addendum`, `AddendumError`)
- Modify: `src/noor/domain/writeback.py` (`Kind.ADDENDUM`, `addendum_item`)
- Modify: `src/noor/store.py` (`add_addendum`, `PendingAddendum`, `pending_addenda`, `queued_addenda`, `mark_addendum_written_back`, `mark_addendum_refused`)
- Modify: `src/noor/dispatch.py` (`send_addendum`, second loop in `drain`)
- Test: `tests/domain/test_visit.py`, `tests/domain/test_writeback.py`, `tests/test_store.py`, `tests/test_dispatch.py`

**Interfaces:**
- Consumes: `TERMINAL`, `dump_visit`, `Flag` (all already available to the store).
- Produces:
  - `visit.Addendum(id, visit_id, text, author, written_at: datetime, flagged: bool = False)` — `AddendumError` on empty text.
  - `writeback.Kind.ADDENDUM = 8` and `writeback.addendum_item(addendum: Addendum) -> WriteBack`.
  - `store.add_addendum(conn, addendum: Addendum) -> None` — `StoreError` if the Visit is not terminal.
  - `store.PendingAddendum(addendum_id, visit_id, patient_id, text, author, written_at, refused_at, said)`.
  - `store.pending_addenda(conn) -> list[PendingAddendum]`, `store.queued_addenda(conn) -> list[str]`.
  - `store.mark_addendum_written_back(conn, addendum_id, at) -> None`, `store.mark_addendum_refused(conn, addendum_id, at, said) -> None`.
  - `dispatch.send_addendum(conn, emr, row: PendingAddendum, *, attempted_at) -> None`.

**Why this shape (§5.9, §6.2, CONTEXT.md "Addendum"):** the Addendum is *the only way a closed Visit changes, because a Write-Back may already have created work the original record justified*. It *sends a Write-Back of its own, after the Visit's*, carrying no owner and no due time *because it asks for nothing*. Its optional flag reuses the existing manual-flag route (`Route.MANUAL_FLAG`) — a `Flag` appended to the closed Visit's `flags` list — so the inbox needs no new path. The `flags` append is the sanctioned addition §5.9 allows; it never touches resolutions, plan, or state, and it bypasses `save()` (which refuses a terminal row) with a direct `update`.

- [ ] **Step 1: Write the failing `Addendum` domain test**

In `tests/domain/test_visit.py`, extend the `noor.domain.visit` import (line 16) to add `Addendum`, `AddendumError`, then add:

```python
def test_an_addendum_with_no_text_is_refused():
    # Act / Assert — §6.2: an addition to a closed record with nothing to add
    with pytest.raises(AddendumError):
        Addendum("a-1", "v-1", "   ", author="Dr Layla Al-Amri", written_at=NINE)


def test_an_addendum_keeps_its_text_and_author():
    # Act
    result = Addendum("a-1", "v-1", "BP rechecked, 128/82",
                      author="Dr Layla Al-Amri", written_at=NINE)

    # Assert
    assert (result.text, result.author) == ("BP rechecked, 128/82", "Dr Layla Al-Amri")
```

Run: `python -m pytest tests/domain/test_visit.py::test_an_addendum_with_no_text_is_refused -v`
Expected: FAIL — `ImportError: cannot import name 'Addendum'`.

- [ ] **Step 2: Add `Addendum` and `AddendumError`**

In `src/noor/domain/visit.py`, add after `kind_for` (end of file):

```python
class AddendumError(ValueError):
    """An Addendum with no text — an addition to a closed record with nothing to add."""


@dataclass(frozen=True)
class Addendum:
    """A timestamped, attributed addition to a terminal Visit (§5.9, §6.2). The only way a
    closed Visit changes, because a Write-Back may already have created work the original
    record justified. `flagged` is the author also sending it to the Supervisor (§5.12)."""

    id: str
    visit_id: str
    text: str
    author: str
    written_at: datetime
    flagged: bool = False

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise AddendumError(
                "an Addendum is an addition to a closed record; there is nothing to add")
```

Run: `python -m pytest tests/domain/test_visit.py -k addendum -v`
Expected: PASS.

- [ ] **Step 3: Write the failing `addendum_item` test**

In `tests/domain/test_writeback.py`, add (the module already imports `writeback` symbols; add `Kind` and `addendum_item` to its `noor.domain.writeback` import, and `Addendum` to its `noor.domain.visit` import):

```python
def test_an_addendums_write_back_carries_no_owner_and_no_due_time():
    # Arrange — §6.2, CONTEXT.md: an Addendum asks for nothing
    addendum = Addendum("a-1", "v-1", "BP rechecked, 128/82",
                        author="Dr Layla Al-Amri", written_at=NOW)

    # Act
    item = addendum_item(addendum)

    # Assert — the eighth kind, and a payload with neither owner nor due_at
    assert item.kind is Kind.ADDENDUM
    assert "owner" not in item.payload and "due_at" not in item.payload
```

Run: `python -m pytest tests/domain/test_writeback.py::test_an_addendums_write_back_carries_no_owner_and_no_due_time -v`
Expected: FAIL — `AttributeError: ADDENDUM` / `addendum_item` undefined.

- [ ] **Step 4: Add `Kind.ADDENDUM` and `addendum_item`**

In `src/noor/domain/writeback.py`, amend the `Kind` docstring and add the eighth value:

```python
class Kind(IntEnum):
    """§4.9's seven writes, in that table's order — the integer *is* the row number. The
    eighth is not one of the seven: it is the Addendum's own Write-Back (§6.2, §5.9), sent
    after the Visit's and carrying no owner and no due time because it asks for nothing."""

    VISIT_OUTCOME = 1
    OBSERVATIONS = 2
    SELF_CARE_FINDINGS = 3
    RECONCILIATION = 4
    RECOMMENDATIONS = 5
    BETWEEN_VISIT_PLAN = 6
    PROPOSED_GOAL_OF_CARE = 7
    ADDENDUM = 8
```

Add `Addendum` to the `noor.domain.visit` import (line 16: `from noor.domain.visit import Addendum, Visit`) and add the builder below `assemble`/`_add` (end of file):

```python
def addendum_item(addendum: Addendum) -> WriteBack:
    """The Addendum's own Write-Back item (§6.2). No owner and no due time — it records an
    addition and asks for nothing (§4.9, CONTEXT.md). `assemble` is untouched: this is a
    separate send, after the Visit's, not one of the close's seven."""
    return WriteBack(Kind.ADDENDUM, {
        "visit_id": addendum.visit_id,
        "text": addendum.text,
        "author": addendum.author,
        "written_at": addendum.written_at.isoformat(),
    })
```

Run: `python -m pytest tests/domain/test_writeback.py::test_an_addendums_write_back_carries_no_owner_and_no_due_time -v`
Expected: PASS. Confirm the seam still holds: `python -m pytest tests/test_seam.py -v`.

- [ ] **Step 5: Write the failing store tests**

In `tests/test_store.py`, add `Addendum` to the `noor.domain.visit` import and add. `closed()` (line 385) and `scheduled()` (line 27) helpers already exist:

```python
ADDENDUM = Addendum("a-1", "v-1", "BP rechecked on the doorstep, 128/82",
                    author="Dr Layla Al-Amri", written_at=datetime(2026, 8, 31, 13, 0))


def test_an_addendum_is_accepted_only_after_the_visit_has_closed(conn):
    # Arrange — the Visit is still Scheduled (open)
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")

    # Act / Assert — an addition to an open Visit is the section write, not an Addendum
    with pytest.raises(store.StoreError):
        store.add_addendum(conn, ADDENDUM)


def test_an_addendum_on_a_closed_visit_is_stored_and_queued(conn):
    # Arrange
    closed(conn, "v-1", MONDAY)

    # Act
    store.add_addendum(conn, ADDENDUM)

    # Assert — queued for its own Write-Back, carrying its Patient
    queued = store.pending_addenda(conn)
    assert [(row.addendum_id, row.patient_id) for row in queued] == [("a-1", "p-1")]


def test_a_flagged_addendum_puts_a_manual_flag_on_the_closed_visit(conn):
    # Arrange
    closed(conn, "v-1", MONDAY)

    # Act — the author also sends it to the Supervisor (§5.12)
    store.add_addendum(conn, replace(ADDENDUM, flagged=True))

    # Assert — a Flag on the closed Visit, the existing manual-flag route
    assert [flag.subject for flag in store.load(conn, "v-1").flags] == ["a-1"]


def test_an_unflagged_addendum_leaves_the_closed_visit_untouched(conn):
    # Arrange
    closed(conn, "v-1", MONDAY)

    # Act
    store.add_addendum(conn, ADDENDUM)

    # Assert
    assert store.load(conn, "v-1").flags == []


def test_marking_an_addendum_written_back_twice_is_refused(conn):
    # Arrange
    closed(conn, "v-1", MONDAY)
    store.add_addendum(conn, ADDENDUM)
    store.mark_addendum_written_back(conn, "a-1", datetime(2026, 8, 31, 19, 0))

    # Act / Assert — a second acceptance is a delivery nobody made (§4.10)
    with pytest.raises(store.StoreError):
        store.mark_addendum_written_back(conn, "a-1", datetime(2026, 8, 31, 21, 0))


def test_marking_an_addendum_the_store_does_not_have_is_refused(conn):
    # Act / Assert
    with pytest.raises(store.StoreError):
        store.mark_addendum_written_back(conn, "a-nope", datetime(2026, 8, 31, 19, 0))


def test_recording_a_refusal_against_an_addendum_the_store_does_not_have_is_refused(conn):
    # Act / Assert
    with pytest.raises(store.StoreError):
        store.mark_addendum_refused(conn, "a-nope", datetime(2026, 8, 31, 19, 0), "no route")


def test_a_refused_addendum_stays_queued(conn):
    # Arrange
    closed(conn, "v-1", MONDAY)
    store.add_addendum(conn, ADDENDUM)

    # Act
    store.mark_addendum_refused(conn, "a-1", datetime(2026, 8, 31, 19, 0), "no route home")

    # Assert — still queued, with what the EMR said
    row = store.pending_addenda(conn)[0]
    assert (row.addendum_id, row.said) == ("a-1", "no route home")
```

Run: `python -m pytest tests/test_store.py::test_an_addendum_on_a_closed_visit_is_stored_and_queued -v`
Expected: FAIL — `AttributeError: module 'noor.store' has no attribute 'add_addendum'`.

- [ ] **Step 6: Add the `addenda` table and the store group**

In `src/noor/schema.sql`, append:

```sql
-- §6.2, §5.9: the one write a closed Visit accepts. Its own Write-Back columns mirror
-- `visits` so `pending_addenda` derives the queue the same way `pending` does.
create table if not exists addenda (
    id               text primary key,
    visit_id         text not null references visits(id),
    text             text not null,
    author           text not null,  -- §5.13, asked for and not proved (§10)
    written_at       text not null,
    written_back_at  text,           -- null until the EMR accepted it
    last_refused_at  text,
    last_refusal     text
);
```

In `src/noor/store.py`, add `Flag` to the imports (`from noor.domain.opinions import Flag`) and `Addendum` to the `noor.domain.visit` import. Add the group after `mark_refused` (~line 292):

```python
class PendingAddendum(NamedTuple):
    """One Addendum the EMR has not accepted (§6.2), mirroring Pending for a Visit."""

    addendum_id: str
    visit_id: str
    patient_id: str
    text: str
    author: str
    written_at: datetime
    refused_at: datetime | None
    said: str | None


def add_addendum(conn: sqlite3.Connection, addendum: Addendum) -> None:
    """The one write a closed Visit accepts (§5.9, §6.2). Refuses an open Visit — an
    addition to a Visit not yet closed is the section write, which `save` takes. When
    `flagged`, the author also sends it to the Supervisor via the existing manual-flag
    route (Route.MANUAL_FLAG), a Flag appended to the closed Visit with a direct update
    that bypasses `save`'s terminal refusal — the sanctioned addition §5.9 allows."""
    visit = load(conn, addendum.visit_id)
    if visit.state not in TERMINAL:
        raise StoreError(
            f"Visit {addendum.visit_id} is {visit.state.value}; an addition to a Visit "
            f"still open is the section write, not an Addendum (§6.2)")
    conn.execute(
        "insert into addenda (id, visit_id, text, author, written_at) "
        "values (?, ?, ?, ?, ?)",
        (addendum.id, addendum.visit_id, addendum.text, addendum.author,
         addendum.written_at.isoformat()))
    if addendum.flagged:
        visit.flags.append(Flag(addendum.id, addendum.author,
                                addendum.written_at, addendum.text))
        conn.execute("update visits set body = ? where id = ?",
                     (dump_visit(visit), addendum.visit_id))
    conn.commit()


def pending_addenda(conn: sqlite3.Connection) -> list[PendingAddendum]:
    """Addenda whose Write-Back the EMR has not accepted, oldest first. Derived on read
    from `written_back_at`, exactly as `pending` derives the Visit queue (§5.1)."""
    rows = conn.execute(
        "select a.id, a.visit_id, v.patient_id, a.text, a.author, a.written_at, "
        "a.last_refused_at, a.last_refusal "
        "from addenda a join visits v on v.id = a.visit_id "
        "where a.written_back_at is null "
        "order by a.written_at, a.id").fetchall()
    return [
        PendingAddendum(
            row["id"], row["visit_id"], row["patient_id"], row["text"], row["author"],
            datetime.fromisoformat(row["written_at"]),
            datetime.fromisoformat(row["last_refused_at"]) if row["last_refused_at"] else None,
            row["last_refusal"])
        for row in rows
    ]


def queued_addenda(conn: sqlite3.Connection) -> list[str]:
    """The ids alone, for `dispatch.drain`'s second loop."""
    return [row.addendum_id for row in pending_addenda(conn)]


def mark_addendum_written_back(
    conn: sqlite3.Connection, addendum_id: str, at: datetime
) -> None:
    """Record that the EMR accepted this Addendum's Write-Back. A second acceptance fails
    rather than silently overwriting, the same guard `mark_written_back` has (§4.10)."""
    cursor = conn.execute(
        "update addenda set written_back_at = ? "
        "where id = ? and written_back_at is null", (at.isoformat(), addendum_id))
    if cursor.rowcount == 0:
        raise StoreError(
            f"no Addendum {addendum_id!r} awaiting a Write-Back — either it does not "
            f"exist or the EMR already accepted it")
    conn.commit()


def mark_addendum_refused(
    conn: sqlite3.Connection, addendum_id: str, at: datetime, said: str
) -> None:
    """Record that the EMR refused this Addendum's Write-Back, and what it said (§4.10).
    Like `mark_refused`: the Addendum stays queued for the next attempt."""
    cursor = conn.execute(
        "update addenda set last_refused_at = ?, last_refusal = ? where id = ?",
        (at.isoformat(), said, addendum_id))
    if cursor.rowcount == 0:
        raise StoreError(f"no Addendum {addendum_id!r} to record a refusal against")
    conn.commit()
```

Run: `python -m pytest tests/test_store.py -k addendum -v`
Expected: PASS (all eight).

- [ ] **Step 7: Write the failing dispatch tests**

In `tests/test_dispatch.py`, the `conn` fixture, `FlakyEMR`/`FixtureEMR`, `WINDOWS`, `SUPERVISOR`, `EVENING`, and the `closed`-style helpers exist. Add `Addendum` to the visit import and add:

```python
def test_a_queued_addendum_is_delivered_and_marked(conn, emr):
    # Arrange — a closed Visit with an Addendum queued behind it
    stored(conn, completed("v-1"))
    store.add_addendum(conn, Addendum(
        "a-1", "v-1", "BP rechecked, 128/82",
        author="Dr Nada Al-Ghamdi", written_at=NOON))

    # Act
    result = drain(conn, emr)

    # Assert — sent, and no longer queued
    assert "a-1" in result.sent
    assert store.queued_addenda(conn) == []


def test_a_refused_addendum_is_reported_and_stays_queued(conn):
    # Arrange — the EMR with no route home (p-005 rejects writes in the fixture)
    stored(conn, completed("v-2", patient_id="p-005"))
    store.add_addendum(conn, Addendum(
        "a-2", "v-2", "note added late",
        author="Dr Nada Al-Ghamdi", written_at=NOON))

    # Act
    result = drain(conn, FixtureEMR(now=NOON))

    # Assert — reported with what the EMR said, and still queued for the next drive
    assert any(addendum_id == "a-2" for addendum_id, _ in result.failed)
    assert store.queued_addenda(conn) == ["a-2"]
```

If the module's `completed()` does not take `patient_id`, it does (line 44: `completed(visit_id="v-1", patient_id="p-001", ...)`) — use `"p-005"`, the fixture's rejecting Patient. Confirm the fixture enrols `p-005`; `test_dispatch.py` line 34 does.

Run: `python -m pytest tests/test_dispatch.py::test_a_queued_addendum_is_delivered_and_marked -v`
Expected: FAIL — `AttributeError: module 'noor.dispatch' has no attribute 'send_addendum'` (once wired into drain) or a plain no-op leaving `a-1` unsent.

- [ ] **Step 8: Add `send_addendum` and the second drain loop**

In `src/noor/dispatch.py`, add `Addendum` to the `noor.domain.visit` import and `addendum_item` to the `noor.domain.writeback` import. Add `send_addendum` after `send` (~line 72):

```python
def send_addendum(
    conn: sqlite3.Connection,
    emr: EMR,
    row: store.PendingAddendum,
    *,
    attempted_at: datetime,
) -> None:
    """Submit one queued Addendum's Write-Back (§6.2). Its own envelope, built inline: one
    item, no owner, no due time. A refusal is recorded and re-raised so `drain` alone
    decides whether to continue, exactly as `send` does for a Visit."""
    item = addendum_item(Addendum(
        row.addendum_id, row.visit_id, row.text, row.author, row.written_at))
    payload = {"addendum_id": row.addendum_id,
               "items": [{"kind": item.kind.name, "payload": item.payload}]}
    try:
        emr.submit(row.patient_id, payload)
    except WriteRejected as refusal:
        store.mark_addendum_refused(conn, row.addendum_id, attempted_at, str(refusal))
        raise
    store.mark_addendum_written_back(conn, row.addendum_id, attempted_at)
```

In `drain`, after the existing Visit loop and before `return Delivery(...)` (line 100), add:

```python
        for addendum in store.pending_addenda(conn):
            try:
                send_addendum(conn, emr, addendum, attempted_at=attempted_at)
            except WriteRejected as refusal:
                failed.append((addendum.addendum_id, str(refusal)))
            else:
                sent.append(addendum.addendum_id)
```

Run: `python -m pytest tests/test_dispatch.py -k addendum -v`
Expected: PASS.

- [ ] **Step 9: Run the whole suite green, then commit**

Run: `python -m pytest -q`
Expected: PASS, 100% coverage.

```bash
git add src/noor/schema.sql src/noor/domain/visit.py src/noor/domain/writeback.py src/noor/store.py src/noor/dispatch.py tests/
git commit -m "feat: the Addendum, its own Write-Back and optional flag (web_plan §9.3)"
```

---

## Task 4: The Supervisor's inbox

**Files:**
- Modify: `src/noor/domain/supervisor.py` (`band`)
- Modify: `src/noor/store.py` (`InboxRow`, `InboxPatient`, `inbox`, `_obligation_start`, `_open_and_closed`, `_inbox_lines`, `_by_patient`, imports)
- Test: `tests/domain/test_supervisor.py`, `tests/test_store.py`

**Interfaces:**
- Consumes: `reviews`, `silence_audit`, `unanswered`, `Sampling`, `Route`, `Review` (`supervisor.py`); `Windows` (`writeback.py`); `answered`, `completed_between`, `goal`, `load_visit` (`store.py`); `Visit.closed_at`/`started_at` (Task 1's neighbours).
- Produces:
  - `supervisor.band(review: Review) -> tuple[int, datetime | None]` — the §5.2 sort key.
  - `store.InboxRow(review: Review, patient_name: str, visit_date: date)` (NamedTuple) — item 5's Visit date, carried on the row.
  - `store.InboxPatient(patient_id: str, patient_name: str, rows: tuple[InboxRow, ...])`.
  - `store.inbox(conn, *, windows: Windows, policy: Sampling, week: date) -> list[InboxPatient]`.

**Why this shape (web_plan §5.1–§5.3, §9.4, §9.5, ADR 0009):** the inbox is *derived on read* — the per-Visit routes from `reviews`, the week's Silence Audit, minus the items a Verdict has closed (Task 2's `unanswered`). It groups by Patient because *the items are not independent questions*, and orders by §5.2's three bands. The Visit's date rides on `InboxRow` (item 5) rather than on `Review`, because it is the store's fact, not the domain's — this dissolves web_plan §9 item 5 into item 4.

**Stated assumption (flag to the user):** `_obligation_start` measures a review's due time from `visit.closed_at or visit.started_at` — the close where there is one, so the inbox and the EMR's task agree on the deadline (`dispatch.send` derives from `closed_at`); the Start for a flag raised while a Visit is still In Progress, so a deadline never moves between two reads of the same inbox. A Scheduled Visit is excluded upstream (`_open_and_closed`), so `started_at` is always set for the Visits `reviews` sees.

- [ ] **Step 1: Write the failing `band` tests**

In `tests/domain/test_supervisor.py`, add `band` to the `supervisor` import and add. The `visit`, `recommendation`, `WINDOWS`, `NOW`, `reviews`, `silence_audit`, `Sampling` helpers are in scope:

```python
def test_a_tier_three_review_is_in_the_first_band():
    # Arrange — a Tier 3 item owes an answer now, so it carries no due time (ADR 0001)
    subject = visit(tiers=(EscalationTier.TIER_3,))
    row = reviews(subject, goal=None, windows=WINDOWS, at=NOW)[0]

    # Act / Assert
    assert band(row)[0] == 1


def test_a_due_timed_review_is_in_the_second_band():
    # Arrange
    subject = visit(tiers=(EscalationTier.TIER_1,))
    row = reviews(subject, goal=None, windows=WINDOWS, at=NOW)[0]

    # Act / Assert — soonest-first is handled by the due time in the second slot
    assert band(row)[0] == 2


def test_a_silence_audit_review_is_in_the_last_band():
    # Arrange — one silent Completed Visit, sampled
    subject = visit()
    subject.state = VisitState.COMPLETED
    row = silence_audit([subject], Sampling(silent_visit_rate=0.1, minimum_per_week=1))[0]

    # Act / Assert
    assert band(row)[0] == 3
```

Run: `python -m pytest tests/domain/test_supervisor.py -k band -v`
Expected: FAIL — `ImportError: cannot import name 'band'`.

- [ ] **Step 2: Add `band`**

In `src/noor/domain/supervisor.py`, add below `_review` (~line 106):

```python
def band(review: Review) -> tuple[int, datetime | None]:
    """§5.2's three bands as a sort key, lowest first: Tier 3 (due now, no due time), then
    whatever carries a due time soonest-first, then the Silence Audit (a rate, never late).
    Within a band the second slot is homogeneous — all None in bands 1 and 3, all datetimes
    in band 2 — so a None due time is never compared against a real one."""
    if review.route is Route.SILENCE_AUDIT:
        return (3, None)
    if review.due_at is None:
        return (1, None)
    return (2, review.due_at)
```

Run: `python -m pytest tests/domain/test_supervisor.py -k band -v`
Expected: PASS.

- [ ] **Step 3: Write the failing inbox store tests**

In `tests/test_store.py`, add `from noor.domain.supervisor import Sampling` (and reuse the Task 2 `Route`, `Verdict`, `VerdictKey` imports) and `from noor.domain.writeback import Windows`. Add an inbox helper and the tests. `NINE` (line 16) and `proposed()` (line 211) already exist:

```python
INBOX_WINDOWS = Windows(tier_1_hours=72, tier_2_hours=0, ratification_days=7)
SAMPLING = Sampling(silent_visit_rate=0.1, minimum_per_week=1)
WEEK = date(2026, 8, 24)  # the Sunday of MONDAY's (2026-08-31) week is 2026-08-24


def a_started_visit_with_a_tier_item(conn, visit_id, tier):
    """A Visit In Progress carrying one shown Recommendation of the given tier — the least
    Arrange that raises a TIER route. Not closed, so no Silence Audit interferes."""
    subject = scheduled(visit_id)
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.start(NINE, VisitKind.ROUTINE,
                  junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    subject.shown = [Recommendation(f"r-{visit_id}", "Increase metformin", tier,
                                    executor="Junior Physician", provenance="SDGA 2024",
                                    strength="strong")]
    store.save(conn, subject)
    return subject


def test_a_visit_with_a_tiered_item_appears_in_the_inbox(conn):
    # Arrange
    a_started_visit_with_a_tier_item(conn, "v-1", EscalationTier.TIER_1)

    # Act
    result = store.inbox(conn, windows=INBOX_WINDOWS, policy=SAMPLING, week=WEEK)

    # Assert — one Patient, one row, carrying the Patient's name and the Visit's date
    assert len(result) == 1 and len(result[0].rows) == 1
    row = result[0].rows[0]
    assert (row.patient_name, row.visit_date) == ("Fatima Ali", MONDAY)


def test_an_answered_item_is_absent_from_the_inbox(conn):
    # Arrange
    a_started_visit_with_a_tier_item(conn, "v-1", EscalationTier.TIER_1)
    store.record_verdict(conn, VerdictKey("v-1", Route.TIER, "r-v-1"),
                         Verdict(agreed=True, by="Dr Omar Farouk", at=NINE))

    # Act
    result = store.inbox(conn, windows=INBOX_WINDOWS, policy=SAMPLING, week=WEEK)

    # Assert — the Verdict removed the only row, so the Patient is gone too (ADR 0009)
    assert result == []


def test_tier_three_sorts_before_a_due_timed_item_for_one_patient(conn):
    # Arrange — one Patient, a Tier 3 and a Tier 1 item on two Visits
    a_started_visit_with_a_tier_item(conn, "v-1", EscalationTier.TIER_1)
    a_started_visit_with_a_tier_item(conn, "v-2", EscalationTier.TIER_3)

    # Act
    rows = store.inbox(conn, windows=INBOX_WINDOWS, policy=SAMPLING, week=WEEK)[0].rows

    # Assert — Tier 3 (band 1) first, the due-timed Tier 1 (band 2) second
    assert [row.review.visit_id for row in rows] == ["v-2", "v-1"]


def test_patients_are_ordered_by_their_most_pressing_item(conn):
    # Arrange — p-2 has a Tier 3 (band 1); p-1 has a Tier 1 (band 2)
    store.add_patient(conn, "p-2", "Sara Al-Harbi", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    a_started_visit_with_a_tier_item(conn, "v-1", EscalationTier.TIER_1)  # p-1
    p2 = scheduled("v-2", "p-2")
    store.schedule(conn, p2, MONDAY, "post-discharge follow-up")
    p2.start(NINE, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    p2.shown = [Recommendation("r-2", "Call an ambulance", EscalationTier.TIER_3,
                               executor="Junior Physician", provenance="SDGA 2024",
                               strength="strong")]
    store.save(conn, p2)

    # Act
    result = store.inbox(conn, windows=INBOX_WINDOWS, policy=SAMPLING, week=WEEK)

    # Assert — the Patient with the Tier 3 item comes first
    assert [patient.patient_id for patient in result] == ["p-2", "p-1"]


def test_a_disagreed_ratification_stays_in_the_inbox(conn):
    # Arrange — a Completed Baseline with an unratified, disagreed Goal of Care
    store.schedule(conn, scheduled("v-1"), MONDAY, "Enrolment")
    baseline = Visit("v-1", "p-1", VisitKind.BASELINE, state=VisitState.COMPLETED,
                     started_at=NINE, closed_at=datetime(2026, 8, 31, 11, 0))
    store.save(conn, baseline)
    store.propose_goal(conn, proposed())
    store.record_verdict(conn, VerdictKey("v-1", Route.RATIFICATION, "goal-of-care"),
                         Verdict(agreed=False, by="Dr Omar Farouk", at=NINE,
                                 note="the office anchor looks wrong"))

    # Act
    result = store.inbox(conn, windows=INBOX_WINDOWS, policy=SAMPLING, week=WEEK)

    # Assert — a disagreed ratification is not closed: the target is still unratified (§4.11)
    assert any(row.review.route is Route.RATIFICATION
               for patient in result for row in patient.rows)
```

Run: `python -m pytest tests/test_store.py::test_a_visit_with_a_tiered_item_appears_in_the_inbox -v`
Expected: FAIL — `AttributeError: module 'noor.store' has no attribute 'inbox'`.

- [ ] **Step 4: Add the inbox to the store**

In `src/noor/store.py`, add `timedelta` to the datetime import (`from datetime import date, datetime, timedelta`) and widen the supervisor import to `from noor.domain.supervisor import Review, Route, Sampling, Verdict, VerdictKey, band, reviews, silence_audit, unanswered`, and add `from noor.domain.writeback import Windows`. Add at the end of the file:

```python
class InboxRow(NamedTuple):
    """One review row with what §5.3 needs beside the item: the Patient's name and the
    date of the Visit it came from. The date rides here rather than on `Review` because it
    is the store's fact, not the domain's (web_plan §9.5)."""

    review: Review
    patient_name: str
    visit_date: date


class InboxPatient(NamedTuple):
    """The inbox groups by Patient (web_plan §5.1): a door carrying the name and the rows,
    the rows already in §5.2's order."""

    patient_id: str
    patient_name: str
    rows: tuple[InboxRow, ...]


def inbox(
    conn: sqlite3.Connection,
    *,
    windows: Windows,
    policy: Sampling,
    week: date,
) -> list[InboxPatient]:
    """Every unanswered review, grouped by Patient and ordered by §5.2's three bands.

    Derived on read (§5.1, ADR 0009): the per-Visit routes from `reviews`, the week's
    Silence Audit, minus the items a Verdict has closed. `week` is the Sunday the audit
    samples — the caller passes `supervisor.week_start(today)`.
    """
    # ponytail: loads every non-Scheduled Visit and reads the goal per Visit on each call.
    # Correct and fast enough for one clinician against one SQLite file (ADR 0006); if the
    # store ever holds a year of Visits, index the routes at the close instead.
    lines = _inbox_lines(conn)
    closed = answered(conn)
    derived: list[Review] = [
        review
        for visit in _open_and_closed(conn)
        for review in reviews(visit, goal=goal(conn, visit.patient_id),
                              windows=windows, at=_obligation_start(visit))
    ]
    derived += silence_audit(
        completed_between(conn, week, week + timedelta(days=7)), policy)
    rows = [InboxRow(review, *lines[review.visit_id])
            for review in unanswered(derived, closed)]
    return _by_patient(rows)


def _obligation_start(visit: Visit) -> datetime:
    """The time a review's due time is measured from: the close where there is one, so the
    inbox and the EMR's task agree on the deadline; the Start for a flag raised while the
    Visit is still In Progress, so a deadline never moves between two reads of one inbox."""
    return visit.closed_at or visit.started_at


def _open_and_closed(conn: sqlite3.Connection) -> list[Visit]:
    """Every Visit past Scheduled — the only ones that can raise a route. A Scheduled Visit
    has no shown items, no flags and no proposed Goal, so it raises nothing; excluding it
    keeps the read off a whole roster's worth of empty Visits."""
    rows = conn.execute(
        "select body from visits where state != ?",
        (VisitState.SCHEDULED.value,)).fetchall()
    return [load_visit(row["body"]) for row in rows]


def _inbox_lines(conn: sqlite3.Connection) -> dict[str, tuple[str, date]]:
    """Per Visit: the Patient's name and the Visit's scheduled date, in one join, so a row
    is assembled without a query per row."""
    rows = conn.execute(
        "select v.id, p.name, v.scheduled_for "
        "from visits v join patients p on p.id = v.patient_id").fetchall()
    return {row["id"]: (row["name"], date.fromisoformat(row["scheduled_for"]))
            for row in rows}


def _by_patient(rows: Sequence[InboxRow]) -> list[InboxPatient]:
    """Group by Patient, each Patient's rows in §5.2's band order, the Patients themselves
    ordered by their most pressing row (web_plan §5.1, §5.2)."""
    by_id: dict[str, list[InboxRow]] = {}
    for row in rows:
        by_id.setdefault(row.review.patient_id, []).append(row)
    patients = [
        InboxPatient(patient_id, group[0].patient_name,
                     tuple(sorted(group, key=lambda r: band(r.review))))
        for patient_id, group in by_id.items()
    ]
    return sorted(patients, key=lambda p: band(p.rows[0].review))
```

Run: `python -m pytest tests/test_store.py -k inbox -v` and the five inbox tests.
Expected: PASS.

- [ ] **Step 5: Run the whole suite green, then commit**

Run: `python -m pytest -q`
Expected: PASS, 100% coverage. If a branch in `_obligation_start`'s `or` is reported uncovered, add a flag-on-an-open-Visit case; the five tests above already exercise both closed (`visit_date`/ratification) and open (started) Visits, so it should be covered.

```bash
git add src/noor/domain/supervisor.py src/noor/store.py tests/
git commit -m "feat: the Supervisor's inbox, derived and grouped by Patient (web_plan §9.4, §9.5)"
```

---

## After the four tasks: amend the web plan

web_plan §9 item 5 predicted the Visit's date would be *the thing `Review` does not carry*. This plan carries it on `store.InboxRow` instead (a store fact, not a domain one), folding item 5 into item 4. Record that decision — the web plan is the most volatile of the three SSOT documents, and this is exactly the kind of screen/data decision it exists to track.

- [ ] **Step 6: Edit `docs/web_plan.md` §9 item 5**

Replace the item 5 line (line 300):

```markdown
5. **Done as part of item 4:** the Visit's date §5.3 needs rides on the store's inbox row
   (`InboxRow.visit_date`), not on `Review` — it is the store's fact, not the domain's.
```

```bash
git add docs/web_plan.md
git commit -m "docs: web_plan §9.5 — the Visit date rides on the inbox row (backend pass 2)"
```

---

## Self-Review

**1. Spec coverage (web_plan §9 items 1–5):**
- Item 1 — Field Team on the Patient, snapshotted at Start → Task 1 (columns, `Visit` fields, `start()`, `field_team`, the reassignment test).
- Item 2 — Review Verdict, the record and the inbox filtering → Task 2 (`verdicts` table, `Verdict`, `unanswered`, `record_verdict`/`answered`/`verdict`) and consumed by Task 4.
- Item 3 — Addendum, the one closed-Visit write, its own Write-Back, its optional flag → Task 3 (`addenda` table, `Addendum`, `Kind.ADDENDUM`, `add_addendum` with the flag, `send_addendum`, drain's second loop).
- Item 4 — store query for Patients with unanswered items → Task 4 (`store.inbox`).
- Item 5 — the Visit's date on a review row → Task 4 (`InboxRow.visit_date`) plus the web_plan amendment. Item 6 (the whole web layer) is deliberately out of scope — its own plan.

**2. Placeholder scan:** every code step carries complete code; every test step carries a runnable test with explicit Arrange/Act/Assert; every run step names the command and the expected result. No "TBD", no "add validation", no "similar to Task N". The Task 1 call-site propagation enumerates every file and site with the exact transformation, not a hand-wave.

**3. Type consistency:** `FieldTeam(junior_physician, nurse)` and the `Visit` fields share names. `start()` and `add_patient` both take `*, junior_physician: str, nurse: str`. `VerdictKey(visit_id, route: Route, subject)` is the same triple in the domain, the SQL primary key, and `record_verdict`/`answered`/`verdict`. `Verdict.by`/`.at` match `Disposition.by`/`.at`; the SQL columns are `answered_by`/`answered_at` (because `by` is a keyword) and the codec maps between them. `unanswered(rows, answered)` in Task 2 is called with `store.answered(conn)` in Task 4. `band()` returns the same `tuple[int, datetime | None]` used to sort rows and Patients. `send_addendum(conn, emr, row: PendingAddendum, *, attempted_at)` matches drain's call.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-09-06-backend-pass-2.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
