from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from noor import content
from noor.domain.emergency import EntryKind
from noor.domain.opinions import Disposition, Outcome, OverrideLevel, Recommendation
from noor.domain.plans import (
    Axis, Band, BetweenVisitPlan, Comparison, GoalOfCare, MeasurementSchedule,
    Threshold,
)
from noor.domain.records import Reason, Resolution
from noor.domain.states import Datum, EscalationTier, Section, VisitKind
from noor.domain.visit import Addendum, Visit
from noor.domain.vitals import HomeReading, Source
from noor.domain.writeback import Kind, Response, addendum_item, assemble, response_due, windows

NOW = datetime(2026, 8, 28, 11, 0)
SUPERVISOR = "Dr Layla Al-Otaibi"
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
WINDOWS = windows(content.load("response-windows").data["windows"])


def recommendation(rec_id: str, tier: EscalationTier) -> Recommendation:
    """Phase 1 has no producer (§8), so a Recommendation is built here by hand."""
    return Recommendation(rec_id, "Increase metformin to 1g twice daily", tier,
                          executor="Junior Physician", provenance="SDGA 2024 §7.2",
                          strength="strong")


def accepted(rec_id: str) -> Disposition:
    return Disposition(rec_id, Outcome.ACCEPTED, by="Dr Nada Al-Ghamdi", at=NOW)


def proposed_goal() -> GoalOfCare:
    return GoalOfCare(
        "p-001", (Band(Axis.SYSTOLIC, 110.0, 140.0),),
        lineage="SHC hypertension pathway 2024, individualised for age 68",
        office_anchor="140/90 clinic", proposed_by="Dr Nada Al-Ghamdi",
        proposed_at=datetime(2026, 8, 28, 10, 50))


def ratified_goal() -> GoalOfCare:
    goal = proposed_goal()
    return replace(goal, ratified_by=SUPERVISOR, ratified_at=datetime(2026, 8, 29, 9, 0))


def worked() -> Visit:
    """A Visit that has not started yet, with the four content-bearing sections filled and
    the rest resolved by a reason — which is a passing Visit either way (§5.8). It holds no
    kind, because §5.5 settles that at the Start and each caller starts it itself."""
    visit = Visit("v-1", "p-001")
    visit.resolutions = {
        Section.VITALS: Resolution(Section.VITALS, {"bp-seated": "138/84"}),
        Section.PHYSICAL_EXAMINATION: Resolution(
            Section.PHYSICAL_EXAMINATION, {"foot-inspection": "no ulcer"}),
        Section.SELF_CARE_CHECK: Resolution(
            Section.SELF_CARE_CHECK, {"glucometer-technique": "not demonstrated"}),
        Section.MEDICATION_RECONCILIATION: Resolution(
            Section.MEDICATION_RECONCILIATION,
            {"in_house": ["Metformin"], "discrepancies": [],
             "detection": {"state": "present", "as_of": NOW.isoformat()}}),
    }
    visit.home_readings = [
        HomeReading("bp-seated", "150/92", datetime(2026, 8, 26, 7, 30), Source.DEVICE_MEMORY)]
    return visit


def completed(kind: VisitKind = VisitKind.ROUTINE, *, interrupted: bool = False) -> Visit:
    """A Visit all the way through §5.8's gate, with one shown Recommendation answered.

    `interrupted=True` walks In Progress → Emergency → In Progress, documented, so the
    Emergency record is one the state machine produced rather than one assigned past it.
    A Baseline is closed on a proposed Goal of Care, which its gate requires (§5.5).
    """
    visit = worked()
    for section in Section:
        visit.resolutions.setdefault(section, Resolution(section, reason=Reason("patient-declined")))
    visit.plan = BetweenVisitPlan(schedule=(MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3),))
    visit.shown = [recommendation("r-1", EscalationTier.TIER_1)]
    visit.dispositions = [accepted("r-1")]
    visit.start(NOW - timedelta(hours=1), kind,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    if interrupted:
        visit.enter_emergency(datetime(2026, 8, 28, 10, 10))
        visit.emergencies[-1].record(
            EntryKind.OBSERVED, "unresponsive, radial pulse absent",
            datetime(2026, 8, 28, 10, 12))
        visit.leave_emergency(datetime(2026, 8, 28, 10, 35))
    goal = proposed_goal() if kind is VisitKind.BASELINE else None
    visit.complete(by="Dr Nada Al-Ghamdi", at=NOW, goal=goal)
    return visit


def test_the_windows_come_from_the_content_file_and_not_from_this_module():
    """ADR 0007: a hospital restating its escalation policy edits the Markdown."""
    # Arrange / Act — WINDOWS is loaded at import, from response-windows.md

    # Assert
    assert (WINDOWS.tier_1_hours, WINDOWS.tier_2_hours,
            WINDOWS.ratification_days) == (72, 0, 7)


def test_a_tier_1_item_is_due_seventy_two_hours_after_the_visit_closed():
    # Arrange / Act
    due = response_due(EscalationTier.TIER_1, NOW, WINDOWS)

    # Assert
    assert due == NOW + timedelta(hours=72)


def test_an_offline_tier_2_item_is_due_the_moment_it_is_queued_and_so_arrives_overdue():
    """§5.11: Tier 2's window is zero by definition, so the item is late on arrival —
    the intended reading, not a defect to be smoothed away with a grace period."""
    # Arrange / Act
    due = response_due(EscalationTier.TIER_2, NOW, WINDOWS)

    # Assert
    assert due == NOW


@pytest.mark.parametrize("tier", [EscalationTier.TIER_0, EscalationTier.TIER_3])
def test_a_tier_with_no_supervisor_window_carries_no_due_time(tier):
    """Tier 0 is a note for the record; Tier 3 is now, with the Supervisor off the
    critical path (ADR 0001). Neither is a number `response-windows.md` records."""
    # Arrange / Act
    due = response_due(tier, NOW, WINDOWS)

    # Assert
    assert due is None


def test_a_manually_flagged_tier_0_item_borrows_tier_1s_window():
    """§5.12: 'asking for review of something already done is Tier 1's shape exactly.'"""
    # Arrange / Act
    due = response_due(EscalationTier.TIER_0, NOW, WINDOWS, manually_flagged=True)

    # Assert
    assert due == NOW + timedelta(hours=72)


def test_the_kinds_are_numbered_as_the_ssot_numbers_them():
    """§4.9's table is the source of the numbering, so the enum is checkable against it."""
    # Arrange / Act / Assert
    assert [(kind.name, kind.value) for kind in Kind] == [
        ("VISIT_OUTCOME", 1), ("OBSERVATIONS", 2), ("SELF_CARE_FINDINGS", 3),
        ("RECONCILIATION", 4), ("RECOMMENDATIONS", 5), ("BETWEEN_VISIT_PLAN", 6),
        ("PROPOSED_GOAL_OF_CARE", 7), ("ADDENDUM", 8)]


def test_the_handover_is_not_one_of_the_things_noor_writes_back():
    """§4.9: the Handover is rendered locally and handed to the ambulance crew (§5.7).
    A Kind for it would be the write this list deliberately does not have."""
    # Arrange / Act / Assert
    assert not [kind for kind in Kind if "HANDOVER" in kind.name]


def test_a_cancelled_visit_writes_nothing_at_all():
    """§4.9, §5.4. A Cancelled Visit reporting an attendance would be Noor telling the
    EMR about a Visit nobody travelled to."""
    # Arrange — never started, so it never had a kind either (§5.5)
    visit = Visit("v-1", "p-001")
    visit.cancel(Reason("patient-in-hospital"), by="Nurse Huda", at=NOW)

    # Act
    items = assemble(visit, goal=None, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)

    # Assert
    assert items == ()


def test_a_completed_routine_visit_writes_the_six_items_it_has_content_for():
    """Items 1–6. Item 7 is a Baseline Visit's only (§4.9)."""
    # Arrange
    visit = completed()

    # Act
    items = assemble(visit, goal=None, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)

    # Assert
    assert [item.kind for item in items] == [
        Kind.VISIT_OUTCOME, Kind.OBSERVATIONS, Kind.SELF_CARE_FINDINGS,
        Kind.RECONCILIATION, Kind.RECOMMENDATIONS, Kind.BETWEEN_VISIT_PLAN]


def test_the_visit_outcome_carries_the_attendance_record_and_the_terminal_state():
    """§4.9 item 1: the terminal state and the Start timestamp — §5.5's attendance
    record, which is what makes an attended Visit distinguishable from a scheduled one."""
    # Arrange
    visit = completed()

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert (outcome["state"], outcome["started_at"], outcome["closed_by"]) == (
        "completed", (NOW - timedelta(hours=1)).isoformat(), "Dr Nada Al-Ghamdi")


def test_the_visit_outcome_names_the_sections_that_never_ran():
    """§4.9 item 1. On an Ended Early these are the record's honest gaps; asserting the
    empty list on a Completed Visit is the other half of the same claim."""
    # Arrange
    visit = worked()
    visit.start(NOW - timedelta(hours=1), VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"), by="Nurse Huda", at=NOW)

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert outcome["sections_not_run"] == [
        "VISIT_REASON", "CONCERNS_AND_INTERVAL_HISTORY", "CARE_PLAN", "NOTES"]


def test_an_ended_early_visit_says_which_between_visit_plan_remains_in_force():
    """§5.6: the previous plan stands, and the EMR is told which one — with its date."""
    # Arrange
    visit = worked()
    visit.previous_plan = Datum.present(
        BetweenVisitPlan(schedule=(MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3),)),
        as_of=datetime(2026, 7, 30, 10, 0))
    visit.start(NOW - timedelta(hours=1), VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"), by="Nurse Huda", at=NOW)

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert outcome["previous_plan_in_force"] == {
        "state": "present", "as_of": "2026-07-30T10:00:00"}


def test_a_completed_visit_makes_no_statement_about_a_plan_still_in_force():
    """§4.9 scopes that statement to an Ended Early. A Completed Visit emitted a new
    Between-Visit Plan, so the previous one is superseded rather than standing."""
    # Arrange
    visit = completed()

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert "previous_plan_in_force" not in outcome


def test_an_unreachable_previous_plan_is_declared_rather_than_reported_as_none():
    """N6. 'There is no plan in force' and 'Noor could not read the plan' are different
    clinical facts, and the EMR is told which one it is holding."""
    # Arrange
    visit = worked()
    visit.previous_plan = Datum.unreachable()
    visit.start(NOW - timedelta(hours=1), VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"), by="Nurse Huda", at=NOW)

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert outcome["previous_plan_in_force"] == {"state": "unreachable"}


def test_the_emergency_start_and_end_times_fold_into_the_visit_outcome():
    """§4.9's third collapse: ADR 0004 makes the Emergency's duration clinical data, and
    duration is part of what happened during the attendance — so it is not a row of its own."""
    # Arrange
    visit = completed(interrupted=True)

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert outcome["emergencies"] == [
        {"started_at": "2026-08-28T10:10:00", "ended_at": "2026-08-28T10:35:00"}]


def test_the_observations_carry_the_home_readings_with_their_source():
    """§4.9 item 2, §4.8. Same quantities as Vitals, a different observer, and never
    merged into one series — so the source travels with every reading."""
    # Arrange
    visit = completed()

    # Act
    observations = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                            supervisor=SUPERVISOR)[1].payload

    # Assert
    assert observations["home_readings"] == [
        {"measurement": "bp-seated", "value": "150/92",
         "taken_at": "2026-08-26T07:30:00", "source": "device memory"}]


def test_the_observations_keep_vitals_and_home_readings_in_separate_fields():
    """`CONTEXT.md` on Home Readings: 'never **Vitals**'. One payload, two keys, and the
    EMR receives two series rather than one averaged fiction."""
    # Arrange
    visit = completed()

    # Act
    observations = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                            supervisor=SUPERVISOR)[1].payload

    # Assert
    assert observations["vitals"] == {"bp-seated": "138/84"}


def test_the_self_care_findings_are_their_own_write_and_not_folded_into_the_examination():
    """§4.9 item 3. ADR 0002 makes a Self-Care Finding capable of suppressing a
    Recommendation, so it is data in its own right and not a note on the exam."""
    # Arrange
    visit = completed()

    # Act
    findings = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                        supervisor=SUPERVISOR)[2].payload

    # Assert
    assert findings == {"glucometer-technique": "not demonstrated"}


def test_the_reconciliation_write_declares_that_discrepancy_detection_was_unreachable():
    """§4.9 item 4, §4.10. 'No discrepancies' and 'Noor could not read the prescribed
    list' are the two facts N6 exists to keep apart, and this is the boundary where
    collapsing them would hand the EMR a clean bill of health nobody issued."""
    # Arrange
    visit = worked()
    visit.resolutions[Section.MEDICATION_RECONCILIATION] = Resolution(
        Section.MEDICATION_RECONCILIATION,
        {"in_house": ["Metformin"], "discrepancies": [],
         "detection": {"state": "unreachable"}})
    visit.start(NOW - timedelta(hours=1), VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"), by="Nurse Huda", at=NOW)

    # Act
    reconciliation = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                              supervisor=SUPERVISOR)[3].payload

    # Assert
    assert reconciliation["detection"] == {"state": "unreachable"}


def test_a_section_resolved_by_a_reason_alone_produces_no_write_for_that_item():
    """§5.8: Resolved is content *or* a structured reason. A section with no content has
    nothing to report, and inventing an empty payload would tell the EMR the Field Team
    examined something they declared they could not."""
    # Arrange
    visit = completed()
    visit.resolutions[Section.SELF_CARE_CHECK] = Resolution(
        Section.SELF_CARE_CHECK, reason=Reason("patient-declined"))

    # Act
    items = assemble(visit, goal=None, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)

    # Assert
    assert Kind.SELF_CARE_FINDINGS not in [item.kind for item in items]


def test_a_recommendation_is_written_back_with_its_provenance_and_its_strength():
    """N5. The automation-bias mitigation *is* the display of the reasoning (RR 1.26),
    and a write-back that strips it hands the EMR an unsourced instruction."""
    # Arrange
    visit = completed()

    # Act
    recommendations = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                               supervisor=SUPERVISOR)[4].payload

    # Assert
    assert recommendations["recommendations"] == [{
        "id": "r-1", "text": "Increase metformin to 1g twice daily", "tier": 1,
        "executor": "Junior Physician", "provenance": "SDGA 2024 §7.2",
        "strength": "strong", "status": "accepted", "reason": None,
        "response": {"owner": SUPERVISOR,
                     "due_at": (NOW + timedelta(hours=72)).isoformat()}}]


def test_an_overridden_recommendation_is_written_back_with_the_row_that_was_chosen():
    """§4.9 item 5 and N4: an override never blocks, and it is never silent either — the
    structured reason is the input that tells the rule's owner whether to fix the rule."""
    # Arrange
    visit = completed()
    visit.dispositions = [Disposition(
        "r-1", Outcome.OVERRIDDEN, by="Dr Nada Al-Ghamdi", at=NOW,
        level=OverrideLevel.RULE_WRONG_HERE, reason=Reason("contraindicated"))]

    # Act
    recommendations = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                               supervisor=SUPERVISOR)[4].payload

    # Assert
    assert recommendations["recommendations"][0]["status"] == "overridden"
    assert recommendations["recommendations"][0]["reason"] == {
        "level": "rule_wrong_here", "row_id": "contraindicated", "free_text": None}


def test_a_tier_3_recommendation_carries_no_supervisor_response_obligation():
    """ADR 0001: 'Tier 3 exists specifically so a genuine emergency does not queue behind
    a human.' A due time on it would put the bottleneck back."""
    # Arrange
    visit = completed()
    visit.shown = [recommendation("r-1", EscalationTier.TIER_3)]

    # Act
    recommendations = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                               supervisor=SUPERVISOR)[4].payload

    # Assert
    assert recommendations["recommendations"][0]["response"] is None


def test_the_between_visit_plan_is_written_back_as_machine_testable_lines():
    """§4.9 item 6, §4.8: titration steps, the measurement schedule, the stop rules.
    Never prose — a line the household cannot test is not a stop rule."""
    # Arrange
    visit = completed()

    # Act
    plan = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                    supervisor=SUPERVISOR)[5].payload

    # Assert
    assert plan == {"titration": [], "stop_rules": [],
                    "schedule": [{"axis": "systolic", "times_per_week": 3}]}


def test_a_baseline_visit_writes_the_proposed_goal_of_care_with_its_ratification_window():
    """§4.9 item 7: 'the one write that is itself a request for a response.' The window is
    content (`response-windows.md`), and the owner is the Supervisor who must ratify."""
    # Arrange
    visit = completed(VisitKind.BASELINE)
    goal = proposed_goal()

    # Act
    items = assemble(visit, goal=goal, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)

    # Assert
    assert items[-1].payload["response"] == Response(
        SUPERVISOR, goal.proposed_at + timedelta(days=7)).as_json()


def test_a_routine_visit_never_writes_a_goal_of_care_even_when_one_is_in_force():
    """§4.9 item 7 is Baseline Visits only. A Routine Visit reasons against the ratified
    target (§4.4); it does not re-propose it, and a re-proposal would reopen a settled
    ratification and put the Supervisor's own decision back in their inbox."""
    # Arrange
    visit = completed(VisitKind.ROUTINE)

    # Act
    items = assemble(visit, goal=ratified_goal(), at=NOW, windows=WINDOWS,
                     supervisor=SUPERVISOR)

    # Assert
    assert Kind.PROPOSED_GOAL_OF_CARE not in [item.kind for item in items]


def test_a_baseline_visit_with_no_goal_proposed_writes_the_other_items_and_not_that_one():
    """The Junior Physician proposes it; nothing forces one into existence here. Six
    items and a missing seventh is a truthful write, an empty seventh is not."""
    # Arrange
    visit = completed(VisitKind.BASELINE)

    # Act
    items = assemble(visit, goal=None, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)

    # Assert
    assert Kind.PROPOSED_GOAL_OF_CARE not in [item.kind for item in items]


@pytest.mark.parametrize("kwargs", [
    {"owner": SUPERVISOR}, {"due_at": NOW}, {},
])
def test_a_response_cannot_be_built_with_only_one_half_of_the_pair(kwargs):
    """§4.9: 'A Write-Back with no owner and no due time is narrative text wearing
    structure's clothes.' Both fields are required, so the sentence is enforced by the
    constructor and there is no validation branch anyone can forget to call."""
    # Arrange / Act / Assert
    with pytest.raises(TypeError):
        Response(**kwargs)


def test_a_visit_that_ended_before_anything_was_captured_writes_only_its_outcome():
    """§5.6: what was captured is not discarded — and where nothing was captured, nothing
    is invented. One item, saying the Visit started and stopped and which sections never
    ran, is the whole truthful write."""
    # Arrange
    visit = Visit("v-1", "p-001")
    visit.start(NOW - timedelta(minutes=4), VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("household-unsafe"), by="Nurse Huda", at=NOW)

    # Act
    items = assemble(visit, goal=None, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)

    # Assert
    assert [item.kind for item in items] == [Kind.VISIT_OUTCOME]


def test_a_recommendation_nobody_answered_is_written_back_as_not_answered():
    """An Ended Early does not run §5.8's disposition gate, so a shown Recommendation can
    leave the house unanswered. Writing it as accepted would be Noor recording a decision
    the Field Team never made."""
    # Arrange
    visit = worked()
    visit.shown = [recommendation("r-1", EscalationTier.TIER_1)]
    visit.start(NOW - timedelta(hours=1), VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"), by="Nurse Huda", at=NOW)

    # Act
    items = assemble(visit, goal=None, at=NOW, windows=WINDOWS, supervisor=SUPERVISOR)
    written = [item for item in items if item.kind is Kind.RECOMMENDATIONS][0]

    # Assert
    assert [(r["status"], r["reason"]) for r in written.payload["recommendations"]] == [
        ("not answered", None)]


def test_a_plan_with_titration_and_stop_rules_writes_the_lines_that_make_them_testable():
    # Arrange — §4.8: a line the household can test, not prose with a number in it
    visit = completed()
    visit.plan = BetweenVisitPlan(
        titration=(Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 145.0, "add amlodipine 5 mg"),),
        schedule=(MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3),),
        stop_rules=(Threshold(Axis.SYSTOLIC, Comparison.BELOW, 100.0, "hold the evening dose"),))

    # Act
    plan = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                    supervisor=SUPERVISOR)[5].payload

    # Assert
    assert plan == {"titration": [{"axis": "systolic", "comparison": "above",
                                   "value": 145.0, "action": "add amlodipine 5 mg"}],
                    "schedule": [{"axis": "systolic", "times_per_week": 3}],
                    "stop_rules": [{"axis": "systolic", "comparison": "below",
                                    "value": 100.0, "action": "hold the evening dose"}]}


def test_a_baseline_ended_early_with_no_previous_plan_says_so_in_the_same_field():
    # Arrange — §5.6: 'no plan in force' is a sentence the EMR receives, not an omission
    visit = worked()
    visit.start(NOW - timedelta(hours=1), VisitKind.BASELINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"), by="Nurse Huda", at=NOW)

    # Act
    outcome = assemble(visit, goal=None, at=NOW, windows=WINDOWS,
                       supervisor=SUPERVISOR)[0].payload

    # Assert
    assert outcome["previous_plan_in_force"] == {"state": "absent"}


def test_an_addendums_write_back_carries_no_owner_and_no_due_time():
    # Arrange — §6.2, CONTEXT.md: an Addendum asks for nothing
    addendum = Addendum("a-1", "v-1", "BP rechecked, 128/82",
                        author="Dr Layla Al-Amri", written_at=NOW)

    # Act
    item = addendum_item(addendum)

    # Assert — the eighth kind, and a payload with neither owner nor due_at
    assert item.kind is Kind.ADDENDUM
    assert "owner" not in item.payload and "due_at" not in item.payload
