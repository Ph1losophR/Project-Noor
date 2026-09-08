"""The three end-to-end journeys (`docs/testing-standards.md` rungs 6 and 8).

The only module in the suite that composes. Everything is real except the EMR: the store
is a SQLite file, the clinical content is the shipped files, the walk is the eight
sections in §4.2's order. A content file that stops loading fails at import here, which is
ADR 0007's loud failure arriving before a single test runs.
"""
from datetime import date, datetime, timedelta

import pytest

from noor import content, dispatch, store
from noor.domain.brief import Brief, Due, LastVisit, Point, Trend, brief
from noor.domain.emergency import EntryKind, UnresolvedEmergency
from noor.domain.examination import Composition, compose, elements, items, months_by_item
from noor.domain.plans import (
    Axis, Band, BetweenVisitPlan, Comparison, GoalOfCare, MeasurementSchedule, Threshold)
from noor.domain.reconciliation import Medication, as_content, reconcile
from noor.domain.records import Reason, Resolution, check_care_plan_ready
from noor.domain.states import DataState, Datum, Section, VisitKind, VisitState
from noor.domain.supervisor import (
    SILENT_VISIT, Review, Route, reviews, sampling, silence_audit, week_start)
from noor.domain.visit import Visit, kind_for
from noor.domain.vitals import measurements
from noor.domain.writeback import windows
from noor.emr import EMR, FixtureEMR, WriteRejected, catalogue

def _rows(subject: str, table: str) -> list[dict]:
    return content.load(subject).data[table]["rows"]


ITEMS = items(_rows("surveillance-intervals", "intervals"))
MONTHS = months_by_item(_rows("surveillance-intervals", "intervals"))
MEASURES = measurements(_rows("vitals-by-condition", "measurements"))
ELEMENTS = elements(_rows("physical-examination-elements", "elements"))
WINDOWS = windows(content.load("response-windows").data["windows"])
SAMPLING = sampling(content.load("response-windows").data["audit"])
PRODUCTS = {product.id: product for product in catalogue()}

# The roster's day (Task 13), a Friday, so `week_start` lands on Sunday 23 August.
ROSTER_DAY = date(2026, 8, 28)
REASON = "Three-month review — blood pressure above the band at the last Visit"
EMR_NOW = datetime(2026, 8, 28, 7, 0)       # the clinic, before the team left
KNOCK = datetime(2026, 8, 28, 9, 20)
CLOSE = datetime(2026, 8, 28, 10, 5)
DISPATCHED = datetime(2026, 8, 28, 18, 40)  # back on a signal, hours later

BASELINE_DAY = date(2026, 5, 25)
BASELINE_START = datetime(2026, 5, 25, 9, 0)
BASELINE_CLOSE = datetime(2026, 5, 25, 10, 30)
RATIFIED_AT = datetime(2026, 5, 27, 11, 0)

JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
SUPERVISOR = "Dr Omar Farouk"
CONDITIONS = ["diabetes", "hypertension"]

GOAL = GoalOfCare(
    "p-001",
    bands=(Band(Axis.SYSTOLIC, 110, 135, "home band, frailty considered"),
           Band(Axis.DIASTOLIC, 65, 85, "home band"),
           Band(Axis.HBA1C, 7.0, 8.0, "relaxed for age and hypoglycaemia risk"),
           Band(Axis.GLUCOSE_PRE_PRANDIAL, 4.4, 7.8, "pre-meal, home meter")),
    lineage="Proposed at the Baseline Visit from the household's own readings (§4.4)",
    office_anchor="146/88 at the referring clinic, 12 May 2026",
    proposed_by=JUNIOR_PHYSICIAN,
    proposed_at=BASELINE_CLOSE,
)

# A Baseline's plan carries no titration: there is no ratified target to titrate toward
# (`CONTEXT.md`, Between-Visit Plan), and `check_titration_allowed` refuses one.
BASELINE_PLAN = BetweenVisitPlan(
    schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),
              MeasurementSchedule(Axis.GLUCOSE_PRE_PRANDIAL, 3)),
    stop_rules=(Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180, "call the Supervisor"),
                Threshold(Axis.GLUCOSE_PRE_PRANDIAL, Comparison.BELOW, 4.0,
                          "treat the hypoglycaemia and call"),))

# The Golden Case's own plan: same measurements, same stop rules, nothing titrated,
# because nothing changed. A silent Visit still emits a plan (§5.8 requires one).
ROUTINE_PLAN = BASELINE_PLAN

BASELINE_VITALS = {"bp-seated": "148/92", "pulse": "80", "capillary-glucose": "11.4"}
IN_THE_HOUSE = {"bp-seated": "132/78", "pulse": "74", "capillary-glucose": "7.2"}
SELF_CARE = {"items": [
    {"item": "medication-storage", "observed": True, "performed_by": "Caregiver"},
    {"item": "glucose-meter-technique", "demonstrated": True, "performed_by": "Patient"}]}


def house(*product_ids: str) -> tuple[Medication, ...]:
    """What the Nurse found in the cupboard. The product comes off the shipped list and
    only the two fields §4.2 says are typed are typed."""
    return tuple(Medication(PRODUCTS[pid].generic, PRODUCTS[pid],
                            quantity_remaining=14, expiry=date(2027, 3, 1))
                 for pid in product_ids)


# Exactly `p-001`'s prescribed list, so the Golden Case has no discrepancy to report and
# the silence is the record's, not the fixture's.
HOUSE = house("metformin-500", "gliclazide-80", "amlodipine-5")

@pytest.fixture
def conn(tmp_path):
    """One database file per test (`docs/testing-standards.md`) — the production shape
    (ADR 0006), created empty and thrown away, so leakage between journeys is impossible
    rather than something to remember."""
    connection = store.connect(tmp_path / "noor.db")
    yield connection
    connection.close()


@pytest.fixture
def ehr():
    """The hostile fixture EMR (Task 13), reading as of the morning in the clinic."""
    return FixtureEMR(EMR_NOW)


class Offline:
    """The EMR from a house with no signal: every read Unreachable, every write refused.

    Local rather than a sixth `FixturePatient`, because hostility that belongs to the
    *network* has no business being a property of a Patient — `p-004`'s unreachable
    medication list is one record failing, and this is the drive to Diriyah.
    """

    def demographics(self, patient_id: str) -> Datum:
        return Datum.unreachable()

    def problems(self, patient_id: str) -> Datum:
        return Datum.unreachable()

    def medications(self, patient_id: str) -> Datum:
        return Datum.unreachable()

    def allergies(self, patient_id: str) -> Datum:
        return Datum.unreachable()

    def lab(self, patient_id: str, analyte: str) -> Datum:
        return Datum.unreachable()

    def surveillance(self, patient_id: str, item: str) -> Datum:
        return Datum.unreachable()

    def roster(self, day: date) -> Datum:
        return Datum.unreachable()

    def submit(self, patient_id: str, payload: dict) -> None:
        raise WriteRejected("no route to the EMR from this house")

def enrol(conn, ehr, patient_id: str) -> str:
    """Enrolment and the roster read (§4.9). Noor never schedules, so the Visit id, the day
    and the reason all come off the EMR's line — read in the clinic, before the drive."""
    line = [row for row in ehr.roster(ROSTER_DAY).value
            if row.patient_id == patient_id][0]
    store.add_patient(conn, patient_id, line.patient_name, CONDITIONS,
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.schedule(conn, Visit(line.visit_id, patient_id), line.scheduled_for, line.reason)
    return line.visit_id


def a_completed_baseline(conn) -> None:
    """The Visit that made `p-001` a Routine Patient: a Completed Baseline, a ratified
    Goal of Care, and a Between-Visit Plan for the next Visit to be scored against.

    Only the Vitals content matters downstream — it is what the Brief's series is built
    from. The other seven are resolved with a placeholder rather than with a structured
    reason, because a Completed Baseline that declined its own Care Plan is not a thing
    (`reason-lists.md`: the Care Plan is empty only on an Ended Early).
    """
    visit = Visit("v-000", "p-001")
    store.schedule(conn, visit, BASELINE_DAY, "Enrolment — newly referred")
    visit.start(BASELINE_START, VisitKind.BASELINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    for section in Section:
        visit.resolutions[section] = Resolution(section, content={"baseline": True})
    visit.resolutions[Section.VITALS] = Resolution(Section.VITALS, content=BASELINE_VITALS)
    visit.resolutions[Section.NOTES] = Resolution(
        Section.NOTES, reason=Reason("nothing-further"))
    visit.plan = BASELINE_PLAN
    visit.complete(by=JUNIOR_PHYSICIAN, at=BASELINE_CLOSE, goal=GOAL)
    store.save(conn, visit)
    store.propose_goal(conn, GOAL)
    store.ratify_goal(conn, "p-001", by=SUPERVISOR, at=RATIFIED_AT)
    # Its own Write-Back went out three months ago. Left queued it would join every later
    # drain, and a journey about one Visit would quietly be about two.
    store.mark_written_back(conn, "v-000", datetime(2026, 5, 25, 12, 0))


def opened(conn, visit_id: str) -> tuple[Visit, list[Visit]]:
    """The Visit off the device with §5.3's declaration made. Which plan is in force is
    the store's question — §5.6 keeps one standing across a Visit that emitted none, and
    Absent is the truth only before the first one (N6)."""
    visit = store.load(conn, visit_id)
    visit.previous_plan = store.standing_plan(conn, visit.patient_id)
    return visit, store.history(conn, visit.patient_id)


def surveillance_of(ehr, patient_id: str) -> dict[str, Datum]:
    """One read per item, so a boundary that answers some and not others produces a
    mapping that says which — never one Datum standing for all seven."""
    return {item.id: ehr.surveillance(patient_id, item.id) for item in ITEMS}

def work_through(visit, ehr, *, reason: str, as_of: date):
    """The eight sections, in the order the Field Team works in (§4.2).

    Two of them ask the EMR and six do not, which is the whole of rung 6: the same call,
    a boundary that answers or does not, and two sections that say which happened.
    """
    reconciliation = reconcile(HOUSE, ehr.medications(visit.patient_id), as_of)
    examination = compose(ELEMENTS, kind=visit.kind, conditions=CONDITIONS,
                          surveillance=surveillance_of(ehr, visit.patient_id),
                          intervals=MONTHS, as_of=as_of)
    _resolve(visit, Section.VISIT_REASON, {"reason": reason})
    _resolve(visit, Section.CONCERNS_AND_INTERVAL_HISTORY, {"events": [], "concerns": []})
    _resolve(visit, Section.MEDICATION_RECONCILIATION, as_content(reconciliation, CLOSE))
    _resolve(visit, Section.VITALS, IN_THE_HOUSE)
    _resolve(visit, Section.PHYSICAL_EXAMINATION, {
        "basis": examination.basis.value,
        "required": [element.id for element in examination.required],
        "findings": []})
    _resolve(visit, Section.SELF_CARE_CHECK, SELF_CARE)
    visit.resolutions[Section.NOTES] = Resolution(
        Section.NOTES, reason=Reason("nothing-further"))
    # §4.2: the Care Plan is assembled after all seven others, Notes included. Calling the
    # guard here rather than trusting the write order is what proves the order.
    check_care_plan_ready(visit.resolutions)
    _resolve(visit, Section.CARE_PLAN, {"accepted": [], "added": []})
    visit.plan = ROUTINE_PLAN
    return reconciliation, examination


def _resolve(visit, section: Section, content: dict) -> None:
    visit.resolutions[section] = Resolution(section, content=content)


def walked(conn, ehr, visit_id: str = "v-001"):
    """Scheduled → In Progress → Completed, saved at each edge the way a tablet saves.

    The kind is settled here and only here: §5.5 derives it from Patient state at the
    Start, and `kind_for(past)` is the only thing that decides it.
    """
    visit, past = opened(conn, visit_id)
    visit.start(KNOCK, kind_for(past), junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, visit)
    reconciliation, examination = work_through(visit, ehr, reason=REASON, as_of=ROSTER_DAY)
    visit.complete(by=JUNIOR_PHYSICIAN, at=CLOSE)
    store.save(conn, visit)
    return visit, reconciliation, examination


def the_brief(conn, ehr, visit_id: str = "v-001") -> Brief:
    """What the Field Team reads before knocking (§5.3) — the store's history and the
    EMR's surveillance dates, and no Recommendation, ever."""
    visit, past = opened(conn, visit_id)
    return brief(visit, history=past,
                 conditions=store.conditions(conn, visit.patient_id),
                 catalogue=ITEMS, measures=MEASURES,
                 surveillance=surveillance_of(ehr, visit.patient_id), as_of=ROSTER_DAY)

BRIEF = Brief(
    "p-001",
    trends=(
        Trend("bp-seated", "Blood pressure, seated", "mmHg",
              (Point(BASELINE_DAY, "148/92"),)),
        Trend("pulse", "Pulse", "bpm", (Point(BASELINE_DAY, "80"),)),
        Trend("capillary-glucose", "Capillary blood glucose", "mmol/L",
              (Point(BASELINE_DAY, "11.4"),)),
    ),
    last_visit=LastVisit(BASELINE_DAY, VisitState.COMPLETED, None),
    previous_plan=Datum.present(BASELINE_PLAN, as_of=BASELINE_CLOSE),
    due=(
        # Eighteen months old against a three-month interval, and Present with the day it
        # was drawn — stale is a timestamp on a Present value, never a fourth state (§4.10)
        Due("hba1c", "HbA1c", Datum.present(date(2025, 2, 10), as_of=EMR_NOW)),
        # Absent from the record, which `surveillance-intervals.md` itself calls overdue
        Due("retinal-screening", "Retinal screening", Datum.absent()),
        Due("urine-acr", "Urine albumin-to-creatinine ratio", Datum.absent()),
        Due("potassium", "Serum potassium", Datum.absent()),
        Due("lipid-profile", "Lipid profile", Datum.absent()),
    ),
    blind_spots=(),
)
"""Everything Noor derived about Fatima Al-Harbi before anyone knocked.

Not in it, and each absence is a decision: the foot examination (done 2 September 2025,
inside twelve months) and the creatinine (June 2026) are current, so neither is Due;
weight and blood pressure standing have no series because no past Visit recorded them,
and an empty series reads as a flat one; there are no blind spots because every read
answered.
"""


def test_the_brief_before_the_knock_is_this_whole_value_and_nothing_else(conn, ehr):
    """Rung 8, and in Phase 1 the Brief *is* the whole derived set — nothing produces a
    Finding yet. Asserted whole rather than probed, because a series that quietly stops
    being built or a Due row that quietly stops appearing is the failure §4.1 says the
    deliverable is judged on, and `assert len(result.due) > 0` passes straight through it.
    """
    # Arrange — enrolment first: it adds the Patient the older Baseline Visit hangs off
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)

    # Act
    result = the_brief(conn, ehr)

    # Assert
    assert result == BRIEF

def test_the_silent_visit_writes_back_five_items_and_no_recommendation(conn, ehr):
    """Rung 8's other half. Five items, and the two that are absent are the assertion: no
    **Recommendations**, because Noor produced none, and no proposed **Goal of Care**,
    because a Routine Visit reasons against the ratified target rather than re-proposing it
    (§4.4). The first of those becomes a claim about the engine in Phase 1.5 with no edit
    to this file — which is why it is written as an equality now.
    """
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    walked(conn, ehr)

    # Act
    result = dispatch.drain(conn, ehr, windows=WINDOWS, supervisor=SUPERVISOR,
                            attempted_at=DISPATCHED)

    # Assert
    assert (result.sent, [item["kind"] for item in ehr.accepted[0][1]["items"]],
            store.queued(conn)) == (
        ("v-001",),
        ["VISIT_OUTCOME", "OBSERVATIONS", "SELF_CARE_FINDINGS", "RECONCILIATION",
         "BETWEEN_VISIT_PLAN"],
        [])


def to_the_supervisor(conn, visit) -> tuple[Review, ...]:
    """Every route this Visit takes to the Supervisor: §5.12's three per-Visit routes, and
    whatever the week's sample makes of it. Returned as one tuple so a test can assert the
    whole of where a Visit went rather than checking one route at a time."""
    week = week_start(ROSTER_DAY)
    return reviews(visit, goal=store.goal(conn, visit.patient_id), windows=WINDOWS,
                   at=CLOSE) + silence_audit(
        store.completed_between(conn, week, week + timedelta(days=7)), SAMPLING)


def test_the_only_route_a_silent_visit_takes_to_the_supervisor_is_the_audit(conn, ehr):
    """§4.1's argument, executable. This Visit raises none of the three routes that come
    from finding something — no Recommendation to escalate, nothing flagged, a target
    ratified three months ago — so without the fourth it would reach nobody at all, and an
    engine that had stopped working would produce this same silence. N8: a mean of twenty
    months before a CDS malfunction is noticed.
    """
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    visit, _, _ = walked(conn, ehr)

    # Act
    result = to_the_supervisor(conn, visit)

    # Assert — one row, and it is there *because* nothing was found
    assert result == (Review(Route.SILENCE_AUDIT, "v-001", "p-001", SILENT_VISIT, None),)

UNAFFECTED = [Section.VISIT_REASON, Section.CONCERNS_AND_INTERVAL_HISTORY, Section.VITALS,
              Section.SELF_CARE_CHECK, Section.CARE_PLAN, Section.NOTES]
"""The six sections that never ask the EMR. Written out rather than computed as the
complement of the two: a complement would agree with whatever the code did."""


def in_progress(kind: VisitKind = VisitKind.ROUTINE) -> Visit:
    """A started Visit with no store behind it, for the control walk."""
    visit = Visit("v-001", "p-001")
    visit.start(KNOCK, kind, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    return visit


def sections_that_agree(one: Visit, other: Visit) -> list[Section]:
    """Which sections two walks of the same Visit resolved identically, in record order."""
    return [section for section in Section
            if one.resolutions[section] == other.resolutions[section]]


def written(ehr, kind: str) -> dict:
    """One item out of the envelope the EMR accepted, by name."""
    return [item for item in ehr.accepted[0][1]["items"] if item["kind"] == kind][0]


def test_the_offline_stub_is_the_same_boundary_the_real_emr_implements():
    """The guard that keeps this whole journey from testing a fiction. `EMR` is
    `@runtime_checkable`, so a method renamed in Task 13 and not here fails here instead of
    passing against a stub nothing else in the system would accept."""
    # Arrange / Act / Assert
    assert isinstance(Offline(), EMR)


def test_a_whole_visit_completes_with_the_emr_unreachable_and_the_write_back_waits(
        conn, ehr):
    """Rung 6's full path, and ADR 0003's claim: **Completed** depends on nothing outside
    the house. The roster was read in the clinic before the drive (§5.2), which is why an
    offline Visit is walkable at all; everything from the doorstep on refuses. The Visit
    closes anyway, and the Write-Back is still owed — `queued` is where it waits, not where
    it is lost, because a write that fails quietly is worse than none (§4.10).
    """
    # Arrange — the morning's reads, then the drive
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)

    # Act
    visit, _, _ = walked(conn, Offline())

    # Assert
    assert (visit.state, store.queued(conn)) == (VisitState.COMPLETED, ["v-001"])

def test_the_two_sections_that_ask_the_emr_degrade_and_the_other_six_do_not():
    """Rung 6's second half, in both directions at once. The Arrange is a *control walk* —
    the same eight sections, the same house, against a boundary that answers — so the
    comparison is against observed behaviour rather than against a constant this file chose.
    Six sections come out identical. The two that asked come out different, and each says
    which of the three states it is holding: an Unreachable comparison and an Unreachable
    basis. An empty discrepancy list and a short element list would have read as *clean*,
    which is the N6 failure this test exists to catch.

    What is in the cupboard is recorded either way — §4.10 is explicit that a
    Reconciliation with the prescribed list **Unreachable** still has content. Only the
    comparison is missing, and only the comparison is what degrades.
    """
    # Arrange — the same Visit walked twice, once against each boundary. No store: this
    # test is about the eight sections, and the store is not one of them.
    control = in_progress()
    work_through(control, FixtureEMR(EMR_NOW), reason=REASON, as_of=ROSTER_DAY)
    visit = in_progress()

    # Act
    reconciliation, examination = work_through(
        visit, Offline(), reason=REASON, as_of=ROSTER_DAY)

    # Assert
    assert (sections_that_agree(visit, control),
            reconciliation.comparison, examination.basis) == (
        UNAFFECTED, DataState.UNREACHABLE, Composition.UNREACHABLE)


def test_the_degraded_reconciliation_reaches_the_emr_declaring_it_could_not_compare(
        conn, ehr):
    """N6 travelling the whole distance — cupboard, section, Visit, envelope, EMR. The Visit
    was walked with no signal; the drive home found one; item 4 arrives carrying the word
    `unreachable` and no `as_of`, because an `as_of` on a comparison nobody made would
    date a fact that does not exist. Every other layer has a unit test for this. This is the
    only place the chain is proved not to lose it at a seam.
    """
    # Arrange — walked offline, closed in the house, still queued
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    walked(conn, Offline())

    # Act — back at the clinic, on a signal
    dispatch.drain(conn, ehr, windows=WINDOWS, supervisor=SUPERVISOR,
                   attempted_at=DISPATCHED)

    # Assert
    assert written(ehr, "RECONCILIATION")["payload"]["detection"] == {
        "state": "unreachable"}

FIRST_IN = datetime(2026, 8, 28, 9, 31)
FIRST_OUT = datetime(2026, 8, 28, 9, 46)
SECOND_IN = datetime(2026, 8, 28, 9, 54)
SECOND_OUT = datetime(2026, 8, 28, 10, 2)
TRANSFER = datetime(2026, 8, 28, 10, 4)


def two_emergencies(visit) -> None:
    """Two entries with the Visit Protocol resumed between them, each one written down.

    Neither ends in a transfer, which is the case worth walking: a Caregiver calls for a
    fall and the crew finds no injury, then a hypoglycaemic episode answers to oral
    glucose. An Emergency is entered when somebody needs an ambulance *now* (`CONTEXT.md`),
    not when one arrives — so *back to In Progress* is the ordinary exit, and §5.7 lets it
    happen twice.
    """
    visit.enter_emergency(FIRST_IN)
    visit.emergencies[-1].record(
        EntryKind.OBSERVED, "found on the floor beside the bed, oriented, no head injury",
        FIRST_IN)
    visit.emergencies[-1].record(
        EntryKind.DONE, "997 called, crew attended and stood down, Handover given",
        datetime(2026, 8, 28, 9, 44))
    visit.leave_emergency(FIRST_OUT)
    visit.enter_emergency(SECOND_IN)
    visit.emergencies[-1].record(
        EntryKind.OBSERVED, "sweating and confused, capillary glucose 2.9 mmol/L",
        SECOND_IN)
    visit.emergencies[-1].record(
        EntryKind.DONE, "15g oral glucose given, repeat 5.1 mmol/L, symptoms resolved",
        datetime(2026, 8, 28, 10, 1))
    visit.leave_emergency(SECOND_OUT)


def episodes(visit) -> list[tuple[datetime, datetime | None]]:
    """Each Emergency's own pair of times. Two records make two pairs, never one span."""
    return [(record.started_at, record.ended_at) for record in visit.emergencies]


def walked_through_two_emergencies(conn, ehr) -> Visit:
    """Scheduled → In Progress → Emergency → In Progress → Emergency → In Progress →
    Completed. Seven of the state machine's seven transitions are not all here, but the
    re-entrant loop is, and it is the one no unit test can walk from a stored Visit."""
    visit, past = opened(conn, "v-001")
    visit.start(KNOCK, kind_for(past), junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    two_emergencies(visit)
    work_through(visit, ehr, reason=REASON, as_of=ROSTER_DAY)
    visit.complete(by=JUNIOR_PHYSICIAN, at=CLOSE)
    store.save(conn, visit)
    return visit


def test_two_emergencies_in_one_visit_each_carry_their_own_start_and_end(conn, ehr):
    """§5.7's re-entrancy, walked rather than asserted at the record. The Visit Protocol is
    suspended twice and finished afterwards, so this also says the interrupt gives the
    sections back — an Emergency that swallowed the rest of the Visit would be a terminal
    state, which ADR 0004 is the decision not to make."""
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)

    # Act
    visit = walked_through_two_emergencies(conn, ehr)

    # Assert
    assert (visit.state, episodes(visit)) == (
        VisitState.COMPLETED, [(FIRST_IN, FIRST_OUT), (SECOND_IN, SECOND_OUT)])

def an_undocumented_emergency(conn, ehr) -> Visit:
    """A Visit whose Emergency ended and was never written down, off the store rather than
    out of memory. Everything else about it is ready to close."""
    visit, past = opened(conn, "v-001")
    visit.start(KNOCK, kind_for(past), junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.enter_emergency(FIRST_IN)
    visit.leave_emergency(FIRST_OUT)
    work_through(visit, ehr, reason=REASON, as_of=ROSTER_DAY)
    store.save(conn, visit)
    return store.load(conn, "v-001")


def test_an_emergency_nobody_wrote_down_still_refuses_the_close_after_a_reload(conn, ehr):
    """§5.7's bar is *ended and documented*, and an ended-and-empty record is the shape a
    rushed Visit actually produces — the ambulance is gone, the sections are done, and
    nobody typed anything. §5.8 gates Completed on it, and the gate has to survive the
    round trip or it only ever guarded the object the test happened to still be holding."""
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    reloaded = an_undocumented_emergency(conn, ehr)

    # Act / Assert
    with pytest.raises(UnresolvedEmergency):
        reloaded.complete(by=JUNIOR_PHYSICIAN, at=CLOSE)


def test_writing_the_timeline_down_after_the_reload_lets_the_visit_close(conn, ehr):
    """The other direction, which is the half that proves the gate is a gate and not a wall.
    One entry is the floor, and one entry is what it takes to open it."""
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    reloaded = an_undocumented_emergency(conn, ehr)
    reloaded.emergencies[-1].record(
        EntryKind.OBSERVED, "unresponsive, radial pulse absent", FIRST_IN)

    # Act
    reloaded.complete(by=JUNIOR_PHYSICIAN, at=CLOSE)

    # Assert
    assert reloaded.state is VisitState.COMPLETED

def stopped_at_the_second_emergency(conn, ehr) -> Visit:
    """Four sections in, then the Patient goes to hospital. The remaining four never ran,
    and the Visit's terminal state is the Emergency's other exit (§5.7)."""
    visit, past = opened(conn, "v-001")
    visit.start(KNOCK, kind_for(past), junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    two_emergencies(visit)
    _resolve(visit, Section.VISIT_REASON, {"reason": REASON})
    _resolve(visit, Section.CONCERNS_AND_INTERVAL_HISTORY, {"events": [], "concerns": []})
    _resolve(visit, Section.MEDICATION_RECONCILIATION,
             as_content(reconcile(HOUSE, ehr.medications("p-001"), ROSTER_DAY), CLOSE))
    _resolve(visit, Section.VITALS, IN_THE_HOUSE)
    visit.enter_emergency(datetime(2026, 8, 28, 10, 3))
    visit.emergencies[-1].record(
        EntryKind.OBSERVED, "central chest pain, clammy, blood pressure 88/54",
        datetime(2026, 8, 28, 10, 3))
    visit.emergencies[-1].record(
        EntryKind.DONE, "997 called, aspirin 300mg given, Handover given to the crew",
        TRANSFER)
    visit.end_early(Reason("transferred-to-hospital"), by=JUNIOR_PHYSICIAN, at=TRANSFER)
    store.save(conn, visit)
    return visit


def test_a_transfer_to_hospital_ends_the_visit_early_and_the_emr_gets_every_episode(
        conn, ehr):
    """Three Emergencies, one Visit, one of them ending it. The EMR is told each episode's
    times, which four sections never ran, and that the previous Between-Visit Plan is still
    in force — §4.9 makes that last one an explicit statement, because a Visit that emitted
    no new plan leaves the old one standing and an omission would read as *no plan*.

    The *timeline* does not travel: item 1 carries a start and an end, and the entries
    themselves live only in Noor's store and in the Handover the crew left with. That is
    precisely why §5.7's bar is stricter than a section's — nothing downstream will
    reconstruct those minutes, so the refusal above is the only thing that gets them
    written, and it is what a later review or a medico-legal question will be asking for.
    """
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    stopped_at_the_second_emergency(conn, ehr)

    # Act
    dispatch.drain(conn, ehr, windows=WINDOWS, supervisor=SUPERVISOR,
                   attempted_at=DISPATCHED)

    # Assert
    outcome = written(ehr, "VISIT_OUTCOME")["payload"]
    assert (outcome["emergencies"], outcome["sections_not_run"],
            outcome["previous_plan_in_force"]) == (
        [{"started_at": FIRST_IN.isoformat(), "ended_at": FIRST_OUT.isoformat()},
         {"started_at": SECOND_IN.isoformat(), "ended_at": SECOND_OUT.isoformat()},
         {"started_at": "2026-08-28T10:03:00", "ended_at": TRANSFER.isoformat()}],
        ["PHYSICAL_EXAMINATION", "SELF_CARE_CHECK", "CARE_PLAN", "NOTES"],
        {"state": "present", "as_of": BASELINE_CLOSE.isoformat()})

def a_baseline_that_ended_early(conn) -> None:
    """The Baseline that never settled the data floor. One section in, the Patient was too
    unwell to continue — so there is no Goal of Care, no Between-Visit Plan, and no
    Completed Baseline for `kind_for` to find."""
    visit = Visit("v-000", "p-001")
    store.schedule(conn, visit, BASELINE_DAY, "Enrolment — newly referred")
    visit.start(BASELINE_START, VisitKind.BASELINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    _resolve(visit, Section.VISIT_REASON, {"reason": "Enrolment — newly referred"})
    visit.end_early(Reason("patient-too-unwell"), by=JUNIOR_PHYSICIAN,
                    at=datetime(2026, 5, 25, 9, 40))
    store.save(conn, visit)
    store.mark_written_back(conn, "v-000", datetime(2026, 5, 25, 12, 0))


def test_the_kind_is_derived_from_the_store_at_the_start_and_never_from_the_roster(
        conn, ehr):
    """The whole composition, which no unit test reaches: a Completed Baseline in the store
    makes the next Visit Routine. What makes this more than a restatement of `kind_for` is
    `enrol` — it copies the id, the day and the reason off the roster line and there is no
    fourth field to copy, so the roster *cannot* have said which kind this is."""
    # Arrange
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)

    # Act
    visit, _, _ = walked(conn, ehr)

    # Assert
    assert visit.kind is VisitKind.ROUTINE


def test_a_baseline_that_ended_early_makes_the_next_visit_a_baseline_again(conn, ehr):
    """§5.5's other half, and the reason the rule is *Completed* rather than *exists*: an
    Ended Early Baseline established nothing, so the next Visit does that work again. The
    previous plan comes out **Absent** and not Unreachable — Noor knows there is no plan,
    which is a clinical fact, rather than having failed to look (N6, §4.10)."""
    # Arrange
    enrol(conn, ehr, "p-001")
    a_baseline_that_ended_early(conn)
    visit, past = opened(conn, "v-001")

    # Act
    visit.start(KNOCK, kind_for(past), junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)

    # Assert
    assert (visit.kind, visit.previous_plan.state) == (
        VisitKind.BASELINE, DataState.ABSENT)


def test_a_plan_remains_in_force_after_a_visit_that_emitted_none(conn, ehr):
    # Arrange — §5.6: a Routine Visit ended early before emitting a plan; the
    # Baseline's plan is still what the household measures against
    enrol(conn, ehr, "p-001")
    a_completed_baseline(conn)
    visit, past = opened(conn, "v-001")
    visit.start(KNOCK, kind_for(past), junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    _resolve(visit, Section.VISIT_REASON, {"reason": REASON})
    visit.end_early(Reason("household-unsafe"), by=JUNIOR_PHYSICIAN, at=CLOSE)
    store.save(conn, visit)
    store.schedule(conn, Visit("v-002", "p-001"), ROSTER_DAY + timedelta(days=90),
                   "the next three-month review")

    # Act
    visit, _ = opened(conn, "v-002")

    # Assert — Present with the Baseline's plan and its date, not Absent (N6)
    assert visit.previous_plan == Datum.present(BASELINE_PLAN, as_of=BASELINE_CLOSE)
