"""§5.12: which Visits reach the Supervisor. Four routes, and no fifth."""
from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from noor import content
from noor.domain.opinions import Flag, OpinionError, Recommendation
from noor.domain.plans import Axis, Band, GoalOfCare
from noor.domain.states import EscalationTier, Section, VisitKind, VisitState
from noor.domain.supervisor import (
    GOAL_OF_CARE, Review, Route, SILENT_VISIT, Sampling,
    reviews, sampling, silence_audit, week_start,
)
from noor.domain.visit import Visit
from noor.domain.writeback import Windows

NOW = datetime(2026, 8, 31, 12, 0)
WINDOWS = Windows(tier_1_hours=72, tier_2_hours=0, ratification_days=7)


def recommendation(rec_id: str, tier: EscalationTier) -> Recommendation:
    """Phase 1 has no producer (§8), so a Recommendation is built here by hand."""
    return Recommendation(rec_id, "Increase metformin to 1g twice daily", tier,
                          executor="Junior Physician", provenance="SDGA 2024 §7.2",
                          strength="strong")


def visit(kind: VisitKind = VisitKind.ROUTINE, *, tiers=(), flags=()) -> Visit:
    """Started, because §5.5 settles the kind at the Start and `_ratification` reads it.
    A Scheduled Visit holding a kind would be the roster label the SSOT forbids."""
    subject = Visit("v-1", "p-1")
    subject.start(NOW - timedelta(hours=1), kind)
    subject.shown = [recommendation(f"r-{index}", tier)
                     for index, tier in enumerate(tiers, start=1)]
    subject.flags = list(flags)
    return subject


def flag(subject: str) -> Flag:
    return Flag(subject, by="Dr Hana Saleh", at=NOW,
                note="the daughter disagrees with the dose change")


def proposed() -> GoalOfCare:
    return GoalOfCare(
        patient_id="p-1",
        bands=(Band(Axis.SYSTOLIC, 120, 135, "ADA older-adult band"),),
        lineage="ADA Standards of Care 2025, Table 13.1",
        office_anchor="140/90",
        proposed_by="Dr Hana Saleh",
        proposed_at=NOW)


def ratified() -> GoalOfCare:
    return replace(proposed(), ratified_by="Dr Omar Farouk",
                   ratified_at=NOW + timedelta(days=1))


def queue(subject: Visit, goal: GoalOfCare | None = None):
    return reviews(subject, goal=goal, windows=WINDOWS, at=NOW)


def test_a_tier_1_recommendation_reaches_the_supervisor_with_seventy_two_hours_to_answer():
    # Act
    result = queue(visit(tiers=(EscalationTier.TIER_1,)))

    # Assert — the whole Review, so a wrong route or a wrong subject fails here too
    assert result == (
        Review(Route.TIER, "v-1", "p-1", "r-1", NOW + timedelta(hours=72)),)


def test_a_tier_0_recommendation_never_reaches_the_supervisor_on_its_own():
    # Act / Assert — Tier 0 is the Field Team acting alone (ADR 0001)
    assert queue(visit(tiers=(EscalationTier.TIER_0,))) == ()


def test_a_tier_2_recommendation_reaches_the_supervisor_already_overdue():
    # Act
    result = queue(visit(tiers=(EscalationTier.TIER_2,)))

    # Assert — zero hours by definition (§5.11): the intended reading, not a defect
    assert result == (Review(Route.TIER, "v-1", "p-1", "r-1", NOW),)


def test_a_tier_3_recommendation_reaches_the_supervisor_with_no_deadline_of_its_own():
    # Act
    result = queue(visit(tiers=(EscalationTier.TIER_3,)))

    # Assert — ADR 0001 removes the Supervisor from the critical path; a deadline
    # would imply they were waited for. It still appears: they are accountable.
    assert result == (Review(Route.TIER, "v-1", "p-1", "r-1", None),)


def test_a_baseline_visits_proposed_target_reaches_the_supervisor_with_its_own_window():
    # Act
    result = queue(visit(VisitKind.BASELINE), proposed())

    # Assert — seven days, from `response-windows.md` (§5.12's second route)
    assert result == (Review(Route.RATIFICATION, "v-1", "p-1", GOAL_OF_CARE,
                             NOW + timedelta(days=7)),)


def test_a_ratified_target_is_not_put_back_in_the_supervisors_inbox():
    # Act / Assert — their own settled decision returning is the inbox losing meaning
    assert queue(visit(VisitKind.BASELINE), ratified()) == ()


def test_a_routine_visit_does_not_re_propose_the_target_it_reasons_against():
    # Act / Assert — §4.4: a Routine Visit compares against the target, never resets it
    assert queue(visit(VisitKind.ROUTINE), proposed()) == ()


def test_a_baseline_visit_that_proposed_no_target_raises_no_ratification_route():
    # Act / Assert — a Baseline that Ended Early before the Goal of Care was set
    assert queue(visit(VisitKind.BASELINE), None) == ()


def test_a_manually_flagged_tier_0_recommendation_borrows_tier_1s_window():
    # Arrange
    subject = visit(tiers=(EscalationTier.TIER_0,), flags=(flag("r-1"),))

    # Act
    result = queue(subject)

    # Assert — §5.12: asking for review of something already done is Tier 1's shape
    assert result == (Review(Route.MANUAL_FLAG, "v-1", "p-1", "r-1",
                             NOW + timedelta(hours=72)),)


def test_a_flag_on_something_that_is_not_a_recommendation_borrows_tier_1s_window():
    # Arrange — §5.11 lets the Junior Physician send anything, a whole section included
    subject = visit(flags=(flag(Section.SELF_CARE_CHECK.name),))

    # Act
    result = queue(subject)

    # Assert — nothing untiered has a tier to borrow, so it takes Tier 0's path
    assert result == (Review(Route.MANUAL_FLAG, "v-1", "p-1", "SELF_CARE_CHECK",
                             NOW + timedelta(hours=72)),)


def test_a_manually_flagged_tier_2_recommendation_keeps_its_own_zero_window():
    # Arrange
    subject = visit(tiers=(EscalationTier.TIER_2,), flags=(flag("r-1"),))

    # Act
    result = queue(subject)

    # Assert — the flag's window is the flagged item's tier, and Tier 2's is zero
    assert result[-1] == Review(Route.MANUAL_FLAG, "v-1", "p-1", "r-1", NOW)


def test_a_flagged_recommendation_reaches_the_supervisor_by_both_routes():
    # Arrange
    subject = visit(tiers=(EscalationTier.TIER_1,), flags=(flag("r-1"),))

    # Act
    result = queue(subject)

    # Assert — routing is a floor (§5.11, ADR 0003). Collapsing these two would be
    # software subtracting Supervisor involvement, and they say different things.
    assert result == (
        Review(Route.TIER, "v-1", "p-1", "r-1", NOW + timedelta(hours=72)),
        Review(Route.MANUAL_FLAG, "v-1", "p-1", "r-1", NOW + timedelta(hours=72)))


def test_a_visit_that_produced_nothing_and_flagged_nothing_reaches_the_supervisor_not_at_all():
    # Act / Assert — §5.12: not all of them. The Silence Audit (Task 21) is the reason
    # this Visit is still seen, and it is a sample across Visits, not a property of one.
    assert queue(visit()) == ()


def test_the_routes_arrive_in_the_order_the_ssot_lists_them():
    # Arrange — a Baseline that produced a Tier 1 item and flagged its Vitals
    subject = visit(VisitKind.BASELINE, tiers=(EscalationTier.TIER_1,),
                    flags=(flag(Section.VITALS.name),))

    # Act
    result = queue(subject, proposed())

    # Assert — §5.12's table, top to bottom, so a screen renders it without sorting
    assert tuple(review.route for review in result) == (
        Route.TIER, Route.RATIFICATION, Route.MANUAL_FLAG)


def test_a_flag_with_no_reason_for_being_sent_is_refused():
    # Act / Assert — a Supervisor guessing why something is in their inbox is the
    # flag not working
    with pytest.raises(OpinionError):
        Flag("r-1", by="Dr Hana Saleh", at=NOW, note="")


def test_a_flag_that_does_not_say_who_sent_it_is_refused():
    # Act / Assert — §5.13: sending a decision for review is itself a decision
    with pytest.raises(OpinionError):
        Flag("r-1", by="", at=NOW, note="the daughter disagrees with the dose change")


SAMPLING = Sampling(silent_visit_rate=0.10, minimum_per_week=1)


def week(silent: int, noisy: int = 0) -> list[Visit]:
    """A week of Completed Visits: `silent` that produced nothing, then `noisy` that did.
    Ids are zero-padded, so sorting them sorts the week the sample is spread across."""
    quiet = [_closed(f"v-{index:02d}") for index in range(1, silent + 1)]
    return quiet + [_that_produced_something(f"v-{index:02d}")
                    for index in range(silent + 1, silent + noisy + 1)]


def _closed(visit_id: str) -> Visit:
    """Closed, and so carrying a kind — this is the shape the store hands back. A kind on a
    Visit that never started would be the roster label §5.5 forbids."""
    return Visit(visit_id, "p-1", VisitKind.ROUTINE, VisitState.COMPLETED)


def _that_produced_something(visit_id: str) -> Visit:
    subject = _closed(visit_id)
    subject.shown = [recommendation("r-1", EscalationTier.TIER_1)]
    return subject


def test_a_week_of_four_silent_visits_still_reaches_the_supervisor_once():
    # Act — 10% of four truncates to nothing, so the floor is the whole rule here
    result = silence_audit(week(4), SAMPLING)

    # Assert — the whole row: the Visit, the Patient, and no deadline (§5.12)
    assert result == (Review(Route.SILENCE_AUDIT, "v-01", "p-1", SILENT_VISIT, None),)


def test_a_bigger_weeks_sample_is_spread_across_it_rather_than_taken_from_the_front():
    # Act
    result = silence_audit(week(40), SAMPLING)

    # Assert — four, evenly spaced: a sample of Sunday is not a sample of the week
    assert tuple(review.visit_id for review in result) == (
        "v-01", "v-11", "v-21", "v-31")


def test_the_rate_is_read_against_the_silence_and_not_against_the_weeks_caseload():
    # Act — forty Completed Visits, twenty of them silent
    result = silence_audit(week(20, 20), SAMPLING)

    # Assert — two, from the twenty. Four would be 10% of the wrong denominator
    assert tuple(review.visit_id for review in result) == ("v-01", "v-11")


def test_a_week_in_which_every_visit_produced_something_reaches_the_supervisor_not_at_all():
    # Act / Assert — there is no silence here whose accuracy needs checking
    assert silence_audit(week(0, 3), SAMPLING) == ()


def test_a_week_with_no_visits_in_it_at_all_is_not_a_week_of_silence():
    # Act / Assert — the floor cannot invent a Visit to review
    assert silence_audit([], SAMPLING) == ()


def test_the_sampling_policy_is_read_from_the_clinical_content_and_not_hard_coded():
    # Act — ADR 0007: the rate and the floor belong to the content's owner, not to code
    policy = sampling(content.load("response-windows").data["audit"])

    # Assert — if this fails the content changed, and the rows above want rereading
    assert policy == SAMPLING


def test_the_audit_week_starts_on_the_sunday_before_the_day_it_is_asked_about():
    # Act — Friday 28 August 2026
    result = week_start(date(2026, 8, 28))

    # Assert — the Saudi working week runs Sunday to Thursday
    assert result == date(2026, 8, 23)


def test_a_sunday_is_the_start_of_its_own_audit_week():
    # Act / Assert — the boundary, from the inside
    assert week_start(date(2026, 8, 23)) == date(2026, 8, 23)
