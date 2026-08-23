"""The §7.3 threshold, the §10.5 profile and release, and the EvaluationContext.

Every refusal here is a load-time gate landing where rules, thresholds, the
tenant profile, and the observable registry meet: no rule references an absent
or unpopulated threshold (§10.4 gate 1, §8.4 invariant 3), a threshold is stated
in its observable's canonical unit (§6.3), source families are never blended
(§10.4 gate 7), and a hard stop cannot be disabled by tenant policy (§10.5).
Threshold resolution follows §7.3's strict precedence — one active goal of care,
then the pinned threshold — and refuses to choose between two conflicting goals
(§8.2), never by recency or narrowness.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.engine.content import (
    ENGINE_VERSION,
    AmbiguousGoalOfCareError,
    FallbackFrom,
    ResolvedTarget,
    ThresholdStatus,
)
from noor.engine.rules import Expression, Operator, Severity
from tests.conftest import (
    T0,
    make_citation,
    make_context,
    make_disablement,
    make_goal,
    make_pins,
    make_profile,
    make_release,
    make_requirement,
    make_rule,
    make_snapshot,
    make_then,
    make_threshold,
)

EGFR_REF = "metformin.egfr_absolute_contraindication"
# The braces are a UCUM annotation carrying no arithmetic meaning; "mL/min" is a
# different unit (§7.3).
EGFR_UNIT = "mL/min/{1.73_m2}"


def test_the_threshold_status_vocabulary_holds_exactly_the_ssot_members():
    # Arrange / Act / Assert — §7.3's three population states, closed like every
    # vocabulary inside the device boundary
    assert tuple(status.value for status in ThresholdStatus) == (
        "unpopulated",
        "populated",
        "clinician_approved",
    )


def test_a_citation_names_its_source_completely():
    # Arrange / Act
    citation = make_citation()

    # Assert — §7.3's example shape, field for field
    assert citation.organisation == "ADA / KDIGO"
    assert citation.document == "Consensus Report on Diabetes Management in CKD"
    assert citation.version == "2022"
    assert citation.locator == "Metformin recommendations"
    assert citation.jurisdiction == "international"
    assert citation.evidence_grade == "consensus"
    assert citation.review_date.year == 2027


@pytest.mark.parametrize(
    "missing",
    [
        "organisation",
        "document",
        "version",
        "locator",
        "jurisdiction",
        "evidence_grade",
        "review_date",
    ],
)
def test_an_incomplete_citation_is_refused(missing):
    # Arrange / Act / Assert — an uncited threshold is a build failure (§7.3)
    with pytest.raises(ValidationError):
        make_citation(**{missing: None})


def test_a_threshold_carries_value_unit_family_citation_and_status():
    # Arrange / Act
    threshold = make_threshold(
        fallback_from=FallbackFrom(
            tried=("moh.diabetes", "sfda.label"),
            reason="no Saudi molecule-level floor located",
        )
    )

    # Assert — §7.3's example, field for field
    assert threshold.ref == EGFR_REF
    assert threshold.value == Decimal("30")
    assert threshold.unit == EGFR_UNIT
    assert threshold.source_family == "ada-kdigo"
    assert threshold.status is ThresholdStatus.clinician_approved
    assert threshold.approved_by == "Dr. Approver"
    assert threshold.fallback_from is not None
    assert threshold.fallback_from.tried == ("moh.diabetes", "sfda.label")


@pytest.mark.parametrize(
    "absent",
    [
        {"approved_by": None},
        {"approved_at": None},
        {"approved_by": None, "approved_at": None},
    ],
)
def test_clinician_approval_without_a_named_approver_and_date_is_refused(absent):
    # Arrange / Act / Assert — §7.3: no threshold is clinician_approved without both
    with pytest.raises(ValidationError):
        make_threshold(**absent)


def test_a_release_holds_its_rules_thresholds_and_profile():
    # Arrange / Act
    release = make_release()

    # Assert
    assert release.release_id == "rel-2026-09-01"
    assert release.rules[0].id == "metformin-egfr-contraindicated"
    assert release.thresholds[0].ref == EGFR_REF
    assert release.profile.source_family == "ada-kdigo"


def test_duplicate_threshold_refs_are_refused():
    # Arrange / Act / Assert — the ref is the release's lookup key; two thresholds
    # answering to one ref would make resolution order-dependent
    with pytest.raises(ValidationError):
        make_release(thresholds=(make_threshold(), make_threshold()))


def test_disabling_a_hard_stop_is_refused():
    # Arrange — §10.5: disablement is tenant policy, and a stop_and_review rule is
    # the one rule it can never touch
    disablement = make_disablement(rule_id="metformin-egfr-contraindicated")

    # Act / Assert
    with pytest.raises(ValidationError):
        make_release(profile=make_profile(disablements=(disablement,)))


def test_disabling_a_soft_rule_carries_named_accountability():
    # Arrange — §10.5: every governed disablement records its reason, requester,
    # and clinical-owner approval; below a hard stop one may stand
    soft_rule = make_rule(
        id="foot-screening-annual",
        severity=Severity.interruptive_review,
        then=make_then(blocks=None),
    )
    disablement = make_disablement(rule_id="foot-screening-annual")

    # Act
    release = make_release(rules=(soft_rule,), profile=make_profile(disablements=(disablement,)))

    # Assert
    assert release.profile.disablements[0].reason.startswith("Screening already delivered")
    assert release.profile.disablements[0].requested_by == "Dr. Requester"
    assert release.profile.disablements[0].approved_by == "Dr. Owner"


def test_a_context_binds_the_release_registry_and_pins():
    # Arrange — a second rule compares a literal, so the context's walk also meets
    # a numeric leaf that names no threshold
    literal_rule = make_rule(
        id="bp-severe-high",
        severity=Severity.interruptive_review,
        then=make_then(blocks=None),
        requires=(make_requirement(observable="systolic_bp"),),
        when=Expression(op=Operator.lt, fact="systolic_bp", literal=Decimal("180")),
    )

    # Act
    context = make_context(release=make_release(rules=(literal_rule,)))

    # Assert
    assert context.release.release_id == "rel-2026-09-01"
    assert context.registry.entry("egfr").canonical_ucum == EGFR_UNIT
    assert context.pins.profile == "riyadh-hh@3"


def test_a_rule_referencing_an_unknown_threshold_ref_is_refused():
    # Arrange
    rule = make_rule(when=Expression(op=Operator.lt, fact="egfr", threshold_ref="no.such_ref"))

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(rules=(rule,)))


def test_a_threshold_ref_buried_in_composition_is_still_checked():
    # Arrange — under not(any(...)) the reference is still a reference
    buried = Expression(
        op=Operator.NOT,
        children=(
            Expression(
                op=Operator.any,
                children=(
                    Expression(op=Operator.gt, fact="egfr", threshold_ref="no.such_buried_ref"),
                    Expression(op=Operator.drug_active, ingredient_id="metformin"),
                ),
            ),
        ),
    )
    rule = make_rule(when=buried)

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(rules=(rule,)))


def test_a_rule_referencing_an_unpopulated_threshold_is_refused():
    # Arrange — §10.4 gate 1, §8.4 invariant 3: a context never loads one
    unpopulated = make_threshold(
        status=ThresholdStatus.unpopulated, approved_by=None, approved_at=None
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(thresholds=(unpopulated,)))


def test_a_threshold_unit_off_the_canonical_unit_is_refused():
    # Arrange — dropping the UCUM annotation names a different unit (§7.3), and
    # the evaluator compares numbers in the canonical unit only (§6.3)
    mismatched = make_threshold(unit="mL/min")

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(thresholds=(mismatched,)))


def test_a_comparison_against_a_fact_outside_the_registry_is_refused():
    # Arrange — the registry declares what may be compared (§6.6); it does not
    # govern sodium, so the pairing has no canonical unit to agree with
    rule = make_rule(
        requires=(make_requirement(observable="sodium"),),
        when=Expression(op=Operator.gt, fact="sodium", threshold_ref="sodium.strict_floor"),
    )
    thresholds = (
        make_threshold(),
        make_threshold(ref="sodium.strict_floor", value=Decimal("130"), unit="mmol/L"),
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(rules=(rule,), thresholds=thresholds))


def test_a_context_whose_thresholds_span_two_source_families_is_refused():
    # Arrange — §10.4 gate 7: the second threshold resolves in a family the
    # profile does not pin
    thresholds = (
        make_threshold(),
        make_threshold(
            ref="metformin.hba1c_control",
            value=Decimal("53"),
            unit="mmol/mol",
            source_family="sfda-label",
        ),
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(thresholds=thresholds))


def test_profile_pinning_refuses_a_foreign_family_threshold():
    # Arrange — even one threshold outside the pin poisons the context (§7.3:
    # source_family is never blended)
    foreign = make_threshold(source_family="sfda-label")

    # Act / Assert
    with pytest.raises(ValidationError):
        make_context(release=make_release(thresholds=(foreign,)))


def test_profile_fallback_returns_the_pinned_threshold_when_no_goal_applies():
    # Arrange — a snapshot with no goals of care at all
    context = make_context()

    # Act
    target = context.resolve_threshold(make_snapshot(), "egfr", EGFR_REF)

    # Assert — §7.3 precedence step 2
    assert target == ResolvedTarget(value=Decimal("30"), unit=EGFR_UNIT, source="profile")


def test_an_active_goal_wins_over_the_profile_threshold():
    # Arrange — §5.6: the clinician's individualized target, with its stated reason
    goal = make_goal(
        observable="egfr",
        value=Decimal("25"),
        unit=EGFR_UNIT,
        reason="High orthostatic fall risk",
    )
    context = make_context()

    # Act
    target = context.resolve_threshold(make_snapshot(goals_of_care=(goal,)), "egfr", EGFR_REF)

    # Assert — §7.3 precedence step 1, accountability carried forward
    assert target == ResolvedTarget(
        value=Decimal("25"),
        unit=EGFR_UNIT,
        source="goal",
        goal_reason="High orthostatic fall risk",
    )


@pytest.mark.parametrize(
    ("offset", "expected_source"),
    [
        (timedelta(0), "goal"),  # the window opens at effective_date
        (timedelta(days=-1), "profile"),  # not yet effective
        (timedelta(days=365), "profile"),  # expires_at itself closes the window
        (timedelta(days=400), "profile"),  # long expired
    ],
)
def test_a_goal_is_active_exactly_on_the_half_open_window(offset, expected_source):
    # Arrange — §5.6: active means evaluated_at ∈ [effective_date, expires_at)
    goal = make_goal(observable="egfr", value=Decimal("25"), unit=EGFR_UNIT)
    snapshot = make_snapshot(goals_of_care=(goal,), evaluated_at=T0 + offset)
    context = make_context()

    # Act
    target = context.resolve_threshold(snapshot, "egfr", EGFR_REF)

    # Assert
    assert target.source == expected_source


def test_a_goal_in_a_foreign_unit_is_refused():
    # Arrange — "mL/min" is not the annotated unit the threshold is stated in;
    # the engine compares targets in one unit and never rescales (design §6.1)
    goal = make_goal(observable="egfr", value=Decimal("25"), unit="mL/min")

    # Act / Assert
    with pytest.raises(ValueError):
        make_context().resolve_threshold(make_snapshot(goals_of_care=(goal,)), "egfr", EGFR_REF)


def test_two_active_goals_for_one_observable_raise_and_neither_is_chosen():
    # Arrange — §8.2: a conflict is refused, never disambiguated by recency or scope
    goals = (
        make_goal(observable="egfr", value=Decimal("25"), unit=EGFR_UNIT, reason="frailty"),
        make_goal(
            observable="egfr", value=Decimal("45"), unit=EGFR_UNIT, reason="dialysis planning"
        ),
    )

    # Act / Assert
    with pytest.raises(AmbiguousGoalOfCareError) as raised:
        make_context().resolve_threshold(
            make_snapshot(goals_of_care=goals),
            "egfr",
            EGFR_REF,
        )
    # §8.5: the evaluator records only the exception type name, so the message
    # carries neither the patient, nor the observable, nor either target
    message = str(raised.value)
    assert "PAT-1" not in message
    assert "egfr" not in message
    assert "25" not in message
    assert "45" not in message


def test_a_goal_on_another_observable_does_not_block_resolution():
    # Arrange — one systolic goal alongside one renal goal is not a conflict
    goals = (make_goal(), make_goal(observable="egfr", value=Decimal("25"), unit=EGFR_UNIT))

    # Act
    target = make_context().resolve_threshold(make_snapshot(goals_of_care=goals), "egfr", EGFR_REF)

    # Assert
    assert target.source == "goal"


def test_pins_carry_the_release_level_values_and_default_to_no_snapshot():
    # Arrange / Act
    pins = make_pins()

    # Assert — §8.2's six fields; the snapshot id is stamped per record later
    assert pins.catalogue_release == "rel-2026-09-01"
    assert pins.profile == "riyadh-hh@3"
    assert pins.source_family == "ada-kdigo"
    assert pins.snapshot_id is None
    assert pins.engine_version == ENGINE_VERSION
    assert pins.terminology_version == "term-2026-06-01"

    stamped = make_pins(snapshot_id="SNAP-9")
    assert stamped.snapshot_id == "SNAP-9"
