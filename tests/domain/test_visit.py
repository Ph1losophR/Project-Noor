"""The Visit: what it takes to close one, and what refuses to (§5.1, §5.8)."""
from datetime import datetime

import pytest

from noor.domain import emergency, opinions, visit
from noor.domain.emergency import EntryKind
from noor.domain.opinions import Disposition, Outcome, OverrideLevel, Recommendation
from noor.domain.plans import (
    Axis, Band, BetweenVisitPlan, GoalOfCare, MeasurementSchedule,
)
from noor.domain.records import Reason, Resolution
from noor.domain.states import (
    DataState, EscalationTier, IllegalTransition, Section, VisitKind, VisitState,
)
from noor.domain.visit import Visit, kind_for

NINE = datetime(2026, 8, 28, 9, 0)
TEN = datetime(2026, 8, 28, 10, 0)
ELEVEN = datetime(2026, 8, 28, 11, 0)
NOON = datetime(2026, 8, 28, 12, 0)
PLAN = BetweenVisitPlan(schedule=(MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3),))
REC = Recommendation("check-potassium", "Take a potassium sample within two weeks",
                     EscalationTier.TIER_1, "Nurse", "rule-x", "policy")
GOAL = GoalOfCare("p-1", (Band(Axis.SYSTOLIC, 110.0, 140.0),),
                  "Saudi SHA 2023 treatment row", "140/90 office",
                  proposed_by="Dr Salma", proposed_at=ELEVEN)


def started(kind=VisitKind.ROUTINE):
    """A Visit In Progress with nothing resolved yet."""
    subject = Visit("v-1", "p-1")
    subject.start(NINE, kind)
    return subject


def ready_to_close(kind=VisitKind.ROUTINE):
    """A Visit meeting all of §5.8's conditions."""
    subject = started(kind)
    for section in Section:
        subject.resolutions[section] = Resolution(section, content={"noted": True})
    subject.plan = PLAN
    return subject


def closed(kind=VisitKind.BASELINE):
    """A Completed Visit of the given kind, for kind_for's history."""
    subject = ready_to_close(kind)
    subject.complete(by="Dr Salma", at=NOON, goal=GOAL)
    return subject


def test_a_scheduled_visit_becomes_in_progress_when_the_field_team_starts_it():
    # Arrange
    subject = Visit("v-1", "p-1")

    # Act
    subject.start(NINE, VisitKind.ROUTINE)

    # Assert
    assert subject.state is VisitState.IN_PROGRESS


def test_a_scheduled_visit_holds_no_kind_until_it_starts():
    # Arrange / Act — §5.5: the kind is settled by the Start, not by the roster
    subject = Visit("v-1", "p-1")

    # Assert
    assert subject.kind is None


def test_starting_a_visit_is_what_settles_its_kind():
    # Arrange
    subject = Visit("v-1", "p-1")

    # Act
    subject.start(NINE, VisitKind.BASELINE)

    # Assert
    assert subject.kind is VisitKind.BASELINE


def test_a_patient_with_no_visits_at_all_gets_a_baseline():
    # Arrange
    history = []

    # Act
    kind = kind_for(history)

    # Assert
    assert kind is VisitKind.BASELINE


def test_a_patient_whose_baseline_completed_gets_a_routine():
    # Arrange
    history = [closed(VisitKind.BASELINE)]

    # Act
    kind = kind_for(history)

    # Assert
    assert kind is VisitKind.ROUTINE


def test_a_baseline_that_ended_early_leaves_the_next_visit_a_baseline():
    # Arrange — §5.5: the data floor was never established, so it must be done again
    abandoned = started(VisitKind.BASELINE)
    abandoned.end_early(Reason("time-exhausted"), by="Nurse Huda", at=ELEVEN)

    # Act
    kind = kind_for([abandoned])

    # Assert
    assert kind is VisitKind.BASELINE


def test_a_visit_already_in_progress_cannot_be_started_again():
    # Arrange
    subject = started()

    # Act / Assert — the state machine refuses it; this method holds no flag of its own
    with pytest.raises(IllegalTransition):
        subject.start(TEN, VisitKind.ROUTINE)


def test_cancelling_a_visit_records_the_reason_and_the_individual():
    # Arrange
    subject = Visit("v-1", "p-1")

    # Act
    subject.cancel(Reason("patient-in-hospital"), by="Nurse Huda", at=NINE)

    # Assert
    assert (subject.state, subject.closing_reason, subject.closed_by) == (
        VisitState.CANCELLED, Reason("patient-in-hospital"), "Nurse Huda")


def test_a_cancelled_visit_with_no_reason_is_refused():
    # Arrange
    subject = Visit("v-1", "p-1")

    # Act / Assert — §5.10: Cancelled always carries a reason
    with pytest.raises(visit.VisitError):
        subject.cancel(None, by="Nurse Huda", at=NINE)


def test_a_visit_that_has_already_started_cannot_be_cancelled():
    # Arrange
    subject = started()

    # Act / Assert — Cancelled is the terminal state of a Visit that never started
    with pytest.raises(IllegalTransition):
        subject.cancel(Reason("patient-in-hospital"), by="Nurse Huda", at=TEN)


def test_entering_an_emergency_suspends_the_visit_and_opens_a_record():
    # Arrange
    subject = started()

    # Act
    subject.enter_emergency(TEN)

    # Assert
    assert subject.state is VisitState.EMERGENCY
    assert subject.emergencies[0].started_at == TEN


def test_leaving_an_emergency_ends_its_record_and_resumes_the_visit():
    # Arrange
    subject = started()
    subject.enter_emergency(TEN)
    subject.emergencies[0].record(EntryKind.DONE, "ambulance called", TEN)

    # Act
    subject.leave_emergency(ELEVEN)

    # Assert
    assert subject.state is VisitState.IN_PROGRESS
    assert subject.emergencies[0].ended_at == ELEVEN


def test_a_second_emergency_in_one_visit_opens_a_second_record():
    # Arrange — §5.7's re-entrancy, at the Visit rather than the record
    subject = started()
    subject.enter_emergency(TEN)
    subject.emergencies[0].record(EntryKind.DONE, "ambulance called", TEN)
    subject.leave_emergency(ELEVEN)

    # Act
    subject.enter_emergency(NOON)

    # Assert
    assert [record.started_at for record in subject.emergencies] == [TEN, NOON]


def test_a_visit_meeting_every_condition_reaches_completed():
    # Arrange
    subject = ready_to_close()

    # Act
    subject.complete(by="Dr Salma", at=NOON)

    # Assert
    assert subject.state is VisitState.COMPLETED


def test_completing_a_visit_names_who_closed_it_and_when():
    # Arrange
    subject = ready_to_close()

    # Act
    subject.complete(by="Dr Salma", at=NOON)

    # Assert — §5.13: closing the Visit is a decision, so it carries an individual
    assert (subject.closed_by, subject.closed_at) == ("Dr Salma", NOON)


def test_a_visit_with_an_unresolved_section_cannot_be_completed():
    # Arrange
    subject = ready_to_close()
    del subject.resolutions[Section.SELF_CARE_CHECK]

    # Act
    with pytest.raises(visit.NotReadyToComplete) as caught:
        subject.complete(by="Dr Salma", at=NOON)

    # Assert — the failure names the section, and the Visit has not moved
    assert "SELF_CARE_CHECK" in str(caught.value)
    assert subject.state is VisitState.IN_PROGRESS


def test_a_visit_with_no_between_visit_plan_cannot_be_completed():
    # Arrange — §5.8's third condition: the final section is what emits the plan
    subject = ready_to_close()
    subject.plan = None

    # Act / Assert
    with pytest.raises(visit.NotReadyToComplete):
        subject.complete(by="Dr Salma", at=NOON)


def test_a_visit_whose_emergency_was_never_written_down_cannot_be_completed():
    # Arrange
    subject = ready_to_close()
    subject.enter_emergency(TEN)
    subject.leave_emergency(ELEVEN)

    # Act / Assert — its own error, so the gate says which condition failed
    with pytest.raises(emergency.UnresolvedEmergency):
        subject.complete(by="Dr Salma", at=NOON)


def test_a_visit_with_an_undispositioned_recommendation_cannot_be_completed():
    # Arrange
    subject = ready_to_close()
    subject.shown.append(REC)

    # Act / Assert
    with pytest.raises(opinions.Undispositioned):
        subject.complete(by="Dr Salma", at=NOON)


def test_a_visit_whose_every_recommendation_was_overridden_reaches_completed():
    # Arrange — N4: an override never blocks. 36.5–39% of these are false positives
    subject = ready_to_close()
    subject.shown.append(REC)
    subject.dispositions.append(
        Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=ELEVEN,
                    level=OverrideLevel.RULE_WRONG_HERE, reason=Reason("already-addressed")))

    # Act
    subject.complete(by="Dr Salma", at=NOON)

    # Assert
    assert subject.state is VisitState.COMPLETED


def test_a_baseline_visit_with_no_proposed_goal_of_care_cannot_be_completed():
    # Arrange — §5.8: the Baseline's final section is the proposed Goal of Care
    subject = ready_to_close(VisitKind.BASELINE)

    # Act
    with pytest.raises(visit.NotReadyToComplete) as caught:
        subject.complete(by="Dr Salma", at=NOON)

    # Assert — the failure names the condition, and the Visit has not moved
    assert "Goal of Care" in str(caught.value)
    assert subject.state is VisitState.IN_PROGRESS


def test_a_baseline_visit_completes_on_a_goal_of_care_the_supervisor_has_not_ratified():
    # Arrange — ADR 0003: Completed depends on nothing outside the house
    subject = ready_to_close(VisitKind.BASELINE)

    # Act
    subject.complete(by="Dr Salma", at=NOON, goal=GOAL)

    # Assert — ratification is a separate axis with its own window, not a close gate
    assert (subject.state, GOAL.is_ratified) == (VisitState.COMPLETED, False)


def test_ending_early_keeps_everything_already_captured():
    # Arrange — the two sections done before the Visit stopped
    subject = started()
    subject.resolutions[Section.VISIT_REASON] = Resolution(
        Section.VISIT_REASON, content={"reason": "routine review"})
    subject.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, content={"systolic": 148, "diastolic": 92})

    # Act
    subject.end_early(Reason("patient-too-unwell"), by="Nurse Huda", at=ELEVEN)

    # Assert — an Ended Early Visit is partial data, not lost data
    assert subject.state is VisitState.ENDED_EARLY
    assert subject.resolutions[Section.VITALS].content == {"systolic": 148, "diastolic": 92}
    assert (subject.closed_by, subject.closed_at) == ("Nurse Huda", ELEVEN)


def test_ending_a_visit_early_with_no_reason_is_refused():
    # Arrange
    subject = started()

    # Act / Assert — §5.9: the reason is the record of why the data is partial
    with pytest.raises(visit.VisitError):
        subject.end_early(None, by="Nurse Huda", at=ELEVEN)


def test_ending_early_out_of_an_emergency_ends_that_emergency():
    # Arrange — the transfer-to-hospital path
    subject = started()
    subject.enter_emergency(TEN)
    subject.emergencies[0].record(EntryKind.DONE, "ambulance called", TEN)

    # Act
    subject.end_early(
        Reason("transferred-to-hospital"), by="Nurse Huda", at=ELEVEN)

    # Assert — §5.7: the Emergency's exit carries no reason of its own; this one does
    assert subject.state is VisitState.ENDED_EARLY
    assert subject.emergencies[0].ended_at == ELEVEN
    assert subject.closing_reason.row_id == "transferred-to-hospital"


def test_ending_early_out_of_an_emergency_nobody_wrote_down_is_refused():
    # Arrange
    subject = started()
    subject.enter_emergency(TEN)

    # Act / Assert — the gate is on both terminal states, not just Completed
    with pytest.raises(emergency.UnresolvedEmergency):
        subject.end_early(
            Reason("transferred-to-hospital"), by="Nurse Huda", at=ELEVEN)


def test_a_completed_visit_cannot_be_changed():
    # Arrange
    subject = ready_to_close()
    subject.complete(by="Dr Salma", at=NOON)

    # Act / Assert — Completed is terminal; the store enforces the same thing (Task 10)
    with pytest.raises(IllegalTransition):
        subject.end_early(Reason("time-exhausted"), by="Nurse Huda", at=NOON)


def test_a_baseline_visit_declares_that_no_previous_plan_exists():
    # Arrange / Act
    subject = started(VisitKind.BASELINE)

    # Assert — N6: Absent is a statement. Not Unreachable, and not an empty plan
    assert subject.previous_plan.state is DataState.ABSENT


def test_ending_early_after_an_undocumented_emergency_is_refused():
    # Arrange — ended but never written down: the gate fires from In Progress too
    subject = started()
    subject.enter_emergency(TEN)
    subject.leave_emergency(ELEVEN)

    # Act / Assert
    with pytest.raises(emergency.UnresolvedEmergency):
        subject.end_early(
            Reason("transferred-to-hospital"), by="Nurse Huda", at=NOON)
