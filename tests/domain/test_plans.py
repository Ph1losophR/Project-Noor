"""The Goal of Care (§4.4) and the Between-Visit Plan the final section emits (§4.8)."""
from datetime import datetime

import pytest

from noor.domain import plans
from noor.domain.plans import Axis, Band, BetweenVisitPlan, Comparison, GoalOfCare, Threshold

PROPOSED = datetime(2026, 8, 28, 12, 0)
BANDS = (Band(Axis.SYSTOLIC, 110.0, 140.0),
         Band(Axis.GLUCOSE_PRE_PRANDIAL, 4.4, 8.0))
LINEAGE = "Saudi SHA 2023 treatment row"
ANCHOR = "140/90 office"
SCHEDULE = (plans.MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3),)
STOP_RULE = (Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180.0, "call the Supervisor"),)
TITRATION = (Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 145.0, "add amlodipine 5 mg"),)


def unratified():
    return GoalOfCare("p-1", BANDS, LINEAGE, ANCHOR,
                      proposed_by="Dr Salma", proposed_at=PROPOSED)


def ratified():
    return GoalOfCare("p-1", BANDS, LINEAGE, ANCHOR,
                      proposed_by="Dr Salma", proposed_at=PROPOSED,
                      ratified_by="Dr Nour", ratified_at=datetime(2026, 9, 1, 9, 0))


def test_a_band_whose_floor_is_above_its_ceiling_is_refused():
    # Act / Assert
    with pytest.raises(plans.PlanError):
        Band(Axis.SYSTOLIC, 140.0, 110.0)


def test_a_band_with_a_ceiling_but_no_floor_is_refused():
    # Act / Assert — §4.4: every axis is a band. A ceiling alone cannot say "too low"
    with pytest.raises(plans.PlanError):
        Band(Axis.HBA1C, None, 8.0)


def test_a_band_with_no_numbers_and_no_rationale_is_refused():
    # Act / Assert — that is *not yet set*, which is what the ratification gate means
    with pytest.raises(plans.PlanError):
        Band(Axis.HBA1C, None, None)


def test_no_numeric_target_is_a_value_when_it_carries_its_rationale():
    # Arrange / Act — ADA's very-complex band is literally "avoid reliance on A1C"
    band = Band(Axis.HBA1C, None, None, rationale="avoid reliance on A1C — frailty")

    # Assert — a deliberate decision, distinguishable from a target nobody set yet
    assert band.is_numeric is False


def test_a_numeric_band_says_so():
    # Assert
    assert Band(Axis.SYSTOLIC, 110.0, 140.0).is_numeric is True


def test_a_goal_of_care_stores_the_lineage_and_the_office_anchor_beside_the_numbers():
    # Act
    goal = unratified()

    # Assert — N5: displayed to explain the target, never used to recompute it (§4.4)
    assert (goal.lineage, goal.office_anchor) == (LINEAGE, ANCHOR)


def test_a_goal_of_care_with_no_lineage_against_it_is_refused():
    # Act / Assert — N5: a target whose origin nobody can name is unreviewable
    with pytest.raises(plans.PlanError):
        GoalOfCare("p-1", BANDS, "", ANCHOR,
                   proposed_by="Dr Salma", proposed_at=PROPOSED)


def test_a_goal_of_care_with_two_bands_on_one_axis_is_refused():
    # Act / Assert — a band per axis, so two is an argument the engine cannot settle
    with pytest.raises(plans.PlanError):
        GoalOfCare("p-1",
                   (Band(Axis.SYSTOLIC, 110.0, 140.0), Band(Axis.SYSTOLIC, 115.0, 135.0)),
                   LINEAGE, ANCHOR, proposed_by="Dr Salma", proposed_at=PROPOSED)


def test_a_goal_of_care_with_no_band_at_all_is_refused():
    # Act / Assert
    with pytest.raises(plans.PlanError):
        GoalOfCare("p-1", (), LINEAGE, ANCHOR,
                   proposed_by="Dr Salma", proposed_at=PROPOSED)


def test_a_proposed_goal_of_care_is_not_yet_ratified():
    # Assert — §4.4: proposed by the Junior Physician, ratified by the Supervisor
    assert unratified().is_ratified is False


def test_a_ratified_goal_of_care_names_who_ratified_it_and_when():
    # Act
    goal = ratified()

    # Assert
    assert (goal.is_ratified, goal.ratified_by) == (True, "Dr Nour")


def test_a_ratification_time_with_no_name_against_it_is_refused():
    # Act / Assert — N5's automation bias is a person rubber-stamping, so name them
    with pytest.raises(plans.PlanError):
        GoalOfCare("p-1", BANDS, LINEAGE, ANCHOR,
                   proposed_by="Dr Salma", proposed_at=PROPOSED,
                   ratified_at=datetime(2026, 9, 1, 9, 0))


def test_ratification_is_due_seven_days_after_the_proposal():
    # Act — the seven comes from response-windows.md, never from this module
    due = plans.ratification_due(unratified(), days=7)

    # Assert
    assert due == datetime(2026, 9, 4, 12, 0)


def test_a_threshold_with_no_action_against_it_is_refused():
    # Act / Assert — §4.8: a threshold nobody is told to act on is prose with a number
    with pytest.raises(plans.PlanError):
        Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180.0, "")


def test_a_measurement_schedule_of_zero_times_a_week_is_refused():
    # Act / Assert
    with pytest.raises(plans.PlanError):
        plans.MeasurementSchedule(Axis.SYSTOLIC, times_per_week=0)


def test_a_plan_with_no_lines_at_all_is_refused():
    # Act / Assert — §4.8: a plan is titration, a schedule and stop rules, not prose
    with pytest.raises(plans.PlanError):
        BetweenVisitPlan()


def test_a_baseline_shaped_plan_carries_the_schedule_and_the_stop_rules():
    # Arrange — no titration, and no Goal of Care in existence yet
    plan = BetweenVisitPlan(schedule=SCHEDULE, stop_rules=STOP_RULE)

    # Act / Assert — the household is not empty-handed during the ratification week
    assert plans.check_titration_allowed(plan, None) is None


def test_a_plan_that_titrates_with_no_goal_of_care_at_all_is_refused():
    # Arrange
    plan = BetweenVisitPlan(titration=TITRATION, schedule=SCHEDULE, stop_rules=STOP_RULE)

    # Act / Assert — §4.8, and §4.11's second withholding trigger, in one rule
    with pytest.raises(plans.PlanError):
        plans.check_titration_allowed(plan, None)


def test_a_plan_that_titrates_against_an_unratified_goal_of_care_is_refused():
    # Arrange — the case neither §4.8 nor §4.11 names on its own
    plan = BetweenVisitPlan(titration=TITRATION, schedule=SCHEDULE, stop_rules=STOP_RULE)

    # Act / Assert
    with pytest.raises(plans.PlanError):
        plans.check_titration_allowed(plan, unratified())


def test_a_plan_may_titrate_once_the_goal_of_care_is_ratified():
    # Arrange
    plan = BetweenVisitPlan(titration=TITRATION, schedule=SCHEDULE, stop_rules=STOP_RULE)

    # Act / Assert
    assert plans.check_titration_allowed(plan, ratified()) is None


def test_a_band_whose_floor_equals_its_ceiling_is_refused():
    # Act / Assert — the threshold row: a band is a band, not a point (§4.4)
    with pytest.raises(plans.PlanError):
        Band(Axis.SYSTOLIC, 140.0, 140.0)


def test_a_ratification_name_with_no_time_against_it_is_refused():
    # Act / Assert — the pair carries both or neither (N5)
    with pytest.raises(plans.PlanError):
        GoalOfCare("p-1", BANDS, LINEAGE, ANCHOR,
                   proposed_by="Dr Salma", proposed_at=PROPOSED,
                   ratified_by="Dr Nour")


@pytest.mark.parametrize("goal", [unratified(), ratified()])
def test_a_plan_without_titration_needs_no_goal_of_care_at_all(goal):
    # Arrange — §4.8's table: the schedule and the stop rules carry no target dependency
    plan = BetweenVisitPlan(schedule=SCHEDULE, stop_rules=STOP_RULE)

    # Act / Assert — mid-ratification-window or long since ratified, both proceed
    assert plans.check_titration_allowed(plan, goal) is None
