"""A stored Visit that loses a field is a Visit that lied — so: round trips."""
from datetime import datetime

import pytest

from noor import content
from noor.domain.emergency import EmergencyRecord, EntryKind
from noor.domain.opinions import (
    Disposition, Flag, Outcome, OverrideLevel, Recommendation,
)
from noor.domain.plans import (
    Axis, Band, BetweenVisitPlan, Comparison, GoalOfCare, MeasurementSchedule, Threshold,
)
from noor.domain.records import OTHER, Reason, Resolution
from noor.domain.states import (
    DataState, Datum, EscalationTier, Section, VisitKind, VisitState,
)
from noor.domain.visit import Visit
from noor.domain.vitals import HomeReading, Source
from noor.serial import dump_goal, dump_visit, load_goal, load_visit

NINE = datetime(2026, 8, 28, 9, 0)
TEN = datetime(2026, 8, 28, 10, 0)
NOON = datetime(2026, 8, 28, 12, 0)
WEEKLY = MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3)
STEP = Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 140.0, "add 5mg amlodipine")
STOP = Threshold(Axis.SYSTOLIC, Comparison.BELOW, 100.0, "hold the evening dose")
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


def scheduled():
    """A Visit with every optional field still empty."""
    return Visit("v-1", "p-1")


def reloaded(subject):
    return load_visit(dump_visit(subject))


def test_a_scheduled_visit_round_trips_its_identity_and_state():
    # Arrange
    subject = scheduled()

    # Act
    result = reloaded(subject)

    # Assert
    assert (result.id, result.patient_id, result.state) == (
        "v-1", "p-1", VisitState.SCHEDULED)


def test_a_scheduled_visit_comes_back_with_no_kind_rather_than_a_routine_one():
    # Arrange — §5.5: the kind is the Start's, and a default here would invent one
    subject = scheduled()

    # Act
    result = reloaded(subject)

    # Assert
    assert result.kind is None


def test_a_started_visits_kind_round_trips():
    # Arrange
    subject = scheduled()
    subject.start(NINE, VisitKind.BASELINE,
                  junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)

    # Act
    result = reloaded(subject)

    # Assert
    assert result.kind is VisitKind.BASELINE


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


def test_a_section_resolved_with_content_round_trips_that_content():
    # Arrange
    subject = scheduled()
    subject.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, content={"systolic": 148, "diastolic": 92})

    # Act
    result = reloaded(subject)

    # Assert
    assert result.resolutions[Section.VITALS].content == {
        "systolic": 148, "diastolic": 92}


def test_a_section_resolved_with_a_reason_round_trips_the_reason():
    # Arrange — Resolved is content *or* a reason (§5.8), so both halves must survive
    subject = scheduled()
    subject.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, reason=Reason("no-working-device"))

    # Act
    result = reloaded(subject)

    # Assert
    assert result.resolutions[Section.VITALS] == Resolution(
        Section.VITALS, reason=Reason("no-working-device"))


def test_an_other_reason_round_trips_its_free_text():
    # Arrange — the free text is the only record of what the list was missing (§5.10)
    subject = scheduled()
    subject.resolutions[Section.NOTES] = Resolution(
        Section.NOTES, reason=Reason(OTHER, free_text="the family asked us to come back"))

    # Act
    result = reloaded(subject)

    # Assert
    assert result.resolutions[Section.NOTES].reason.free_text == (
        "the family asked us to come back")


def every_reason_row() -> list[str]:
    """Every row id in `reason-lists.md`, flattened and de-duplicated, read out of the file
    rather than listed here. A row a content owner adds joins this list with no code change,
    which is what ADR 0007 means by clinical judgement being data. Forty-three rows across
    the four lists, forty-one distinct — `patient-declined` is on three of them, and one
    round trip covers it.

    `Other` is deliberately not in it: §5.10 makes that row structural and the file says a
    loader finding an `Other` row should treat the file as wrong. The test above is the one
    that covers it."""
    table = content.load("reason-lists").data
    groups = [
        table["cancelled"]["rows"],
        table["ended_early"]["rows"],
        table["no_content"]["shared"],
        table["override"]["rule_wrong_here"]["rows"],
        table["override"]["could_not_act"]["rows"],
        *table["no_content"]["per_section"].values(),
    ]
    return list(dict.fromkeys(row["id"] for group in groups for row in group))


@pytest.mark.parametrize("row_id", every_reason_row())
def test_every_reason_row_in_the_content_file_round_trips(row_id):
    """`docs/testing-standards.md` rung 4: *every list's every row* round-trips. The rest of
    this file exercises four row ids out of the forty-one, and a row that comes back as
    something else is a Cancelled Visit whose reason quietly changed meaning in the store —
    the one place nobody would look."""
    # Arrange
    subject = scheduled()
    subject.resolutions[Section.NOTES] = Resolution(Section.NOTES, reason=Reason(row_id))

    # Act
    result = reloaded(subject)

    # Assert
    assert result.resolutions[Section.NOTES].reason == Reason(row_id)


def test_an_open_emergency_round_trips_with_no_end_time_and_no_entries():
    # Arrange
    subject = scheduled()
    subject.emergencies.append(EmergencyRecord(started_at=TEN))

    # Act
    result = reloaded(subject)

    # Assert
    assert result.emergencies[0] == EmergencyRecord(started_at=TEN)


def test_an_ended_emergency_round_trips_its_whole_timeline():
    # Arrange
    subject = scheduled()
    record = EmergencyRecord(started_at=TEN)
    record.record(EntryKind.OBSERVED, "unresponsive, breathing", TEN)
    record.record(EntryKind.DONE, "ambulance called", TEN)
    record.resolve(NOON)
    subject.emergencies.append(record)

    # Act
    result = reloaded(subject)

    # Assert — order and kind both matter; the timeline is the whole record (§5.7)
    assert result.emergencies[0] == record


def test_a_shown_recommendation_round_trips_its_provenance_and_its_strength():
    # Arrange
    subject = scheduled()
    subject.shown.append(Recommendation(
        "check-potassium", "Take a potassium sample within two weeks",
        EscalationTier.TIER_1, "Nurse", "rule-x", "policy"))

    # Act
    result = reloaded(subject)

    # Assert — N5: a Recommendation without its provenance is an unattributable order
    assert result.shown[0] == Recommendation(
        "check-potassium", "Take a potassium sample within two weeks",
        EscalationTier.TIER_1, "Nurse", "rule-x", "policy")


def test_an_accepted_disposition_round_trips_carrying_no_override_fields():
    # Arrange
    subject = scheduled()
    subject.dispositions.append(
        Disposition("check-potassium", Outcome.ACCEPTED, by="Dr Salma", at=NOON))

    # Act
    result = reloaded(subject)

    # Assert
    assert result.dispositions[0] == Disposition(
        "check-potassium", Outcome.ACCEPTED, by="Dr Salma", at=NOON)


def test_an_overridden_disposition_round_trips_its_level_and_its_reason():
    # Arrange
    subject = scheduled()
    override = Disposition("check-potassium", Outcome.OVERRIDDEN, by="Dr Salma", at=NOON,
                           level=OverrideLevel.COULD_NOT_ACT,
                           reason=Reason("no-supply"))
    subject.dispositions.append(override)

    # Act
    result = reloaded(subject)

    # Assert — N4: the structured reason is engine data, so it is the field that pays
    assert result.dispositions[0] == override


def test_a_between_visit_plans_three_tuples_come_back_as_tuples():
    # Arrange
    subject = scheduled()
    subject.plan = BetweenVisitPlan(
        titration=(STEP,), schedule=(WEEKLY,), stop_rules=(STOP,))

    # Act
    result = reloaded(subject)

    # Assert — lists would compare unequal and defeat every other assertion here
    assert result.plan == BetweenVisitPlan(
        titration=(STEP,), schedule=(WEEKLY,), stop_rules=(STOP,))


def test_an_absent_previous_plan_comes_back_absent():
    # Arrange — a Visit's starting truth, and the one a Baseline keeps
    subject = Visit("v-2", "p-1")

    # Act
    result = reloaded(subject)

    # Assert
    assert result.previous_plan.state is DataState.ABSENT


def test_an_unreachable_previous_plan_does_not_come_back_absent():
    # Arrange — §1.1: the two must not collapse, and storage is where they usually do
    subject = scheduled()
    subject.previous_plan = Datum.unreachable()

    # Act
    result = reloaded(subject)

    # Assert
    assert result.previous_plan.state is DataState.UNREACHABLE


def test_a_present_previous_plan_round_trips_the_plan_and_the_time_it_was_read():
    # Arrange — a schedule-only plan, which is what a Baseline emits (§4.8)
    subject = scheduled()
    subject.previous_plan = Datum.present(BetweenVisitPlan(schedule=(WEEKLY,)), NINE)

    # Act
    result = reloaded(subject)

    # Assert — §5.2: staleness is this timestamp, so losing it invents a fourth state
    assert result.previous_plan == Datum.present(
        BetweenVisitPlan(schedule=(WEEKLY,)), NINE)


def test_a_closed_visit_round_trips_whole():
    # Arrange — every field populated at once; the smaller tests say which one broke
    subject = Visit("v-3", "p-1", VisitKind.ROUTINE)
    subject.junior_physician = JUNIOR_PHYSICIAN
    subject.nurse = NURSE
    subject.state = VisitState.ENDED_EARLY
    subject.resolutions[Section.VISIT_REASON] = Resolution(
        Section.VISIT_REASON, content={"reason": "routine review"})
    subject.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, reason=Reason("no-appropriate-cuff"))
    subject.emergencies.append(EmergencyRecord(started_at=TEN))
    subject.shown.append(Recommendation(
        "check-potassium", "Take a potassium sample", EscalationTier.TIER_1,
        "Nurse", "rule-x", "policy"))
    subject.dispositions.append(
        Disposition("check-potassium", Outcome.ACCEPTED, by="Dr Salma", at=NOON))
    subject.plan = BetweenVisitPlan(schedule=(WEEKLY,))
    subject.previous_plan = Datum.present(BetweenVisitPlan(stop_rules=(STOP,)), NINE)
    subject.started_at = NINE
    subject.closed_by = "Nurse Huda"
    subject.closed_at = NOON
    subject.closing_reason = Reason("time-exhausted")

    # Act
    result = reloaded(subject)

    # Assert
    assert result == subject


def test_a_home_reading_survives_the_round_trip_with_its_source_intact():
    """§4.8: which of the two sources a reading came from is never optional, so it is
    never the field that gets dropped in the codec either."""
    # Arrange
    visit = scheduled()
    visit.home_readings = [
        HomeReading("bp-seated", "138/84", datetime(2026, 8, 26, 7, 30), Source.PAPER_LOG)]

    # Act
    restored = load_visit(dump_visit(visit))

    # Assert
    assert restored.home_readings == visit.home_readings


def test_a_goal_of_care_round_trips_with_every_field_populated():
    # Arrange — a ratified target with one numeric band and one that is not
    subject = GoalOfCare(
        patient_id="p-1",
        bands=(Band(Axis.SYSTOLIC, 120, 135, "ADA older-adult band"),
               Band(Axis.HBA1C, None, None, "avoid reliance on A1C")),
        lineage="ADA Standards of Care 2025, Table 13.1",
        office_anchor="140/90",
        proposed_by="Dr Hana Saleh",
        proposed_at=datetime(2026, 8, 31, 9, 0),
        ratified_by="Dr Omar Farouk",
        ratified_at=datetime(2026, 9, 2, 11, 0))

    # Act / Assert
    assert load_goal(dump_goal(subject)) == subject


def test_a_visit_round_trips_the_flags_it_carries():
    # Arrange
    subject = scheduled()
    subject.flags = [Flag("r-1", by="Dr Hana Saleh", at=NINE,
                          note="the daughter disagrees with the dose change")]

    # Act / Assert
    assert reloaded(subject).flags == subject.flags
