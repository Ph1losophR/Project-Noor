"""The per-rule evaluator through its one entry point (SSOT §8.1-§8.3).

Every rule considered writes exactly one record, and the tests drive all six
outcomes through `evaluate` itself: suppression stops before scope, scope stops
before requirements (§8.2, claim 19), each closed requirement-reason fires in
its declared precedence, leaves read requirement-validated values only, §7.3's
goal-over-threshold precedence holds, and the returned tuple is sorted by
rule_id.
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from noor.canon.models import (
    EntryMode,
    Informant,
    InformantRole,
    MappingInfo,
    MappingStatus,
    QualityState,
    SourceStatus,
)
from noor.engine.evaluate import evaluate
from noor.engine.records import (
    DegradedBecause,
    Outcome,
    RequirementReason,
    RequirementVerdictValue,
)
from noor.engine.rules import Expression, OnUnusable, Operator, Scope, Severity
from noor.engine.snapshot import (
    ActionKind,
    AllergySeverity,
    AllergyStatus,
    CulpritSubstance,
    RequestedAction,
    SnapshotMedication,
    VerificationStatus,
)
from tests.conftest import (
    T0,
    make_allergy,
    make_canonical,
    make_context,
    make_disablement,
    make_goal,
    make_profile,
    make_release,
    make_requirement,
    make_rule,
    make_snapshot,
    make_then,
)

EGFR_REF = "metformin.egfr_absolute_contraindication"
CKD_FLAG = "ckd_chronicity_confirmed"

CONFIRMED_SEVERE_PENICILLIN = Expression(
    op=Operator.allergy,
    ingredient_id="penicillin",
    verification_status=VerificationStatus.confirmed,
    severity=AllergySeverity.severe,
)


def egfr_observation(value, *, age_days=0, **overrides):
    """A fresh, accepted, context-complete eGFR result; override anything."""
    fields = {
        "observable": "egfr",
        "value": value,
        "context_flags": (CKD_FLAG,),
        "effective_time": T0 - timedelta(days=age_days),
    }
    fields.update(overrides)
    return make_canonical(**fields)


def metformin_snapshot(**overrides):
    """A snapshot that fires the default hard stop: eGFR 25, metformin active."""
    fields = {
        "observations": (egfr_observation("25"),),
        "medications": (
            SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped),
        ),
    }
    fields.update(overrides)
    return make_snapshot(**fields)


def potassium_requirement(**overrides):
    """A requirement with every gate opened except quality-family acceptance."""
    fields = {
        "observable": "potassium",
        "accepted_status": (),
        "min_quality": None,
        "max_age_days": None,
        "prefer_source": (),
        "required_context": (),
        "renal_metric": None,
    }
    fields.update(overrides)
    return make_requirement(**fields)


def potassium_rule(rule_id="hyperkalemia-review", **overrides):
    """A passive_task literal comparison over potassium, silent on gaps."""
    fields = {
        "id": rule_id,
        "severity": Severity.passive_task,
        "requires": (potassium_requirement(on_unusable=OnUnusable.silent),),
        "monitors": (),
        "when": Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.5")),
        "then": make_then(blocks=None),
    }
    fields.update(overrides)
    return make_rule(**fields)


def hyperkalemia_hard_stop(**overrides):
    """The same comparison at stop_and_review, degrading on unusable input."""
    fields = {
        "id": "hyperkalemia-hard-stop",
        "requires": (potassium_requirement(),),
        "monitors": (),
        "when": Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.0")),
        "then": make_then(blocks=None),
    }
    fields.update(overrides)
    return make_rule(**fields)


def allergy_rule(**overrides):
    """A filterless penicillin-allergy rule with no data requirements."""
    fields = {
        "id": "penicillin-allergy-alert",
        "severity": Severity.interruptive_review,
        "requires": (),
        "monitors": (),
        "when": Expression(op=Operator.allergy, ingredient_id="penicillin"),
        "then": make_then(blocks=None),
    }
    fields.update(overrides)
    return make_rule(**fields)


def allergy_snapshot(**overrides):
    """A recorded severe penicillin allergy; override anything."""
    fields = {
        "allergies": (make_allergy(culprit=CulpritSubstance(ingredient_id="penicillin")),),
        "allergy_status": AllergyStatus.recorded,
    }
    fields.update(overrides)
    return make_snapshot(**fields)


def evaluate_one(rule, snapshot, requested_actions=()):
    """Evaluate a single-rule release and return its only record."""
    context = make_context(release=make_release(rules=(rule,)))
    records = evaluate(context, snapshot, requested_actions)
    assert len(records) == 1
    return records[0]


def test_a_metformin_hard_stop_triggers_on_fresh_contraindicating_data():
    # Arrange / Act — §7.3: no goal of care applies, so the profile threshold wins
    record = evaluate_one(make_rule(), metformin_snapshot())

    # Assert — triggered at authored severity, verdict usable, pins stamped
    assert record.outcome is Outcome.triggered
    assert record.authored_severity is Severity.stop_and_review
    assert record.effective_severity is Severity.stop_and_review
    assert record.degraded_because is None
    assert record.rule_version == "1.0.0"
    (verdict,) = record.requirement_verdicts
    assert verdict.verdict is RequirementVerdictValue.usable
    assert verdict.reason is RequirementReason.met
    assert verdict.latest_age_days == 0
    assert record.pins.snapshot_id == "SNAP-1"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("29", Outcome.triggered),  # below
        ("30", Outcome.not_triggered),  # exactly at — the boundary is exclusive
        ("31", Outcome.not_triggered),  # above
    ],
)
def test_the_profile_threshold_holds_at_below_and_above_its_boundary(value, expected):
    # Arrange
    rule = make_rule()

    # Act
    record = evaluate_one(rule, metformin_snapshot(observations=(egfr_observation(value),)))

    # Assert — testing standards: every threshold proves at, just below, just above
    assert record.outcome is expected


def test_an_active_goal_of_care_overrides_the_pinned_threshold():
    # Arrange — §5.6/§7.3: the clinician's goal replaces the guideline number
    goal = make_goal(observable="egfr", value=Decimal("20"), unit="mL/min/{1.73_m2}")
    overridden = metformin_snapshot(goals_of_care=(goal,))

    # Act
    without_goal = evaluate_one(make_rule(), metformin_snapshot())
    with_goal = evaluate_one(make_rule(), overridden)

    # Assert — 25 < 30 fires; the same value against the goal's 20 does not
    assert without_goal.outcome is Outcome.triggered
    assert with_goal.outcome is Outcome.not_triggered


def test_suppression_stops_before_scope_for_a_disabled_and_excluded_patient():
    # Arrange — the disablement applies whatever the patient (§10.5, design §6);
    # a hard stop cannot be disabled, so the disabled rule here is advisory
    profile = make_profile(disablements=(make_disablement(rule_id="penicillin-allergy-alert"),))
    rule = allergy_rule(scope=Scope(exclude=(Expression(op=Operator.age, minimum=18),)))
    context = make_context(release=make_release(profile=profile, rules=(rule,)))

    # Act
    (record,) = evaluate(context, allergy_snapshot(), ())

    # Assert — suppressed even though the patient was also out of scope
    assert record.outcome is Outcome.suppressed_by_governed_policy
    assert record.authored_severity is Severity.interruptive_review
    assert record.effective_severity is Severity.interruptive_review
    assert record.degraded_because is None
    assert record.requirement_verdicts == ()
    assert record.pins.snapshot_id == "SNAP-1"


def test_scope_resolves_before_requirements_for_an_excluded_patient_with_no_data():
    # Arrange — claim 19: the excluded patient never reads the requires manifest
    rule = make_rule(scope=Scope(exclude=(Expression(op=Operator.age, minimum=18),)))

    # Act
    record = evaluate_one(rule, make_snapshot())

    # Assert — out_of_scope with empty verdicts, never indeterminate
    assert record.outcome is Outcome.out_of_scope
    assert record.requirement_verdicts == ()
    assert record.degraded_because is None


def test_a_scope_include_admits_only_patients_matching_the_declared_condition():
    # Arrange — §7.1: include is all-of, so a missing concept excludes
    rule = make_rule(
        scope=Scope(include=(Expression(op=Operator.condition, concept="type_2_diabetes"),))
    )

    # Act
    matching = evaluate_one(rule, metformin_snapshot(conditions=frozenset({"type_2_diabetes"})))
    other = evaluate_one(rule, metformin_snapshot())

    # Assert
    assert matching.outcome is Outcome.triggered
    assert other.outcome is Outcome.out_of_scope


@pytest.mark.parametrize(
    ("older", "newer", "expected"),
    [
        ("29", "35", Outcome.not_triggered),  # newest alone decides
        ("35", "29", Outcome.triggered),
    ],
)
def test_the_latest_observation_is_selected_whatever_it_compares_to(older, newer, expected):
    # Arrange — an older result that would fire differently than the newest one;
    # the older is also stale, proving selection precedes freshness
    observations = (
        egfr_observation(older, age_days=91, source_identifier="OBS-old"),
        egfr_observation(newer, age_days=10, source_identifier="OBS-new"),
    )

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=observations))

    # Assert
    assert record.outcome is expected
    assert record.requirement_verdicts[0].latest_age_days == 10


def test_a_corrected_observation_supersedes_the_original_at_same_effective_time():
    # Arrange — same effective_time, same source, different source_version.
    # v1 value 25 (would trigger), v2 value 55 (would not trigger).
    # The correction (v2) must win per §5 / canon.delta.current_versions.
    observations = (
        egfr_observation("25", age_days=10, source_version=1, source_identifier="OBS-1"),
        egfr_observation("55", age_days=10, source_version=2, source_identifier="OBS-1"),
    )

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=observations))

    # Assert — the corrected value 55 wins, so rule does not trigger
    assert record.outcome is Outcome.not_triggered
    assert record.requirement_verdicts[0].latest_age_days == 10


def test_an_observation_exactly_max_age_days_old_is_still_usable():
    # Arrange — testing standards: the boundary itself sits inside the window
    observation = egfr_observation("25", age_days=90)

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert
    assert record.outcome is Outcome.triggered
    assert record.requirement_verdicts[0].verdict is RequirementVerdictValue.usable
    assert record.requirement_verdicts[0].latest_age_days == 90


def test_a_future_dated_observation_is_unusable():
    # Arrange — an observation with effective_time after evaluated_at is corrupt data
    future_obs = egfr_observation("25", age_days=-5)  # 5 days in the future

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(future_obs,)))

    # Assert — corrupt timestamp makes the requirement unusable
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    (verdict,) = record.requirement_verdicts
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.latest_age_days is None  # age_days not computed for future-dated


def test_freshness_window_uses_exact_timedelta_comparison():
    # Arrange — 90 days 12 hours old should be stale (exceeds 90-day window)
    # The .days truncation bug would have allowed this as 90 days
    from datetime import timedelta

    obs = make_canonical(
        observable="egfr",
        value="25",
        effective_time=T0 - timedelta(days=90, hours=12),
        context_flags=("ckd_chronicity_confirmed",),
    )

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(obs,)))

    # Assert — timedelta comparison correctly rejects 90d 12h as stale
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    (verdict,) = record.requirement_verdicts
    assert verdict.reason is RequirementReason.stale
    assert verdict.latest_age_days == 90  # days truncation for reporting only


def test_an_observation_one_day_past_max_age_is_stale_and_degrades_the_hard_stop():
    # Arrange
    observation = egfr_observation("25", age_days=91)

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert — §8.3: unusable requirement, capped severity, authored intact
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review
    (verdict,) = record.requirement_verdicts
    assert verdict.reason is RequirementReason.stale
    assert verdict.latest_age_days == 91


def test_a_rejected_observation_is_unusable_as_quality_below_minimum():
    # Arrange — rejected data exists but may never be evaluated (§6.2)
    observation = egfr_observation("25", state=QualityState.rejected)

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert
    assert record.outcome is Outcome.indeterminate
    assert record.requirement_verdicts[0].reason is RequirementReason.quality_below_minimum


def test_needs_repeat_is_usable_only_under_an_explicit_loosening():
    # Arrange — the flagged state is acceptable exactly when the requirement says so
    flagged = egfr_observation("25", state=QualityState.needs_repeat_or_verification)
    loosened = make_requirement(min_quality=QualityState.needs_repeat_or_verification)

    # Act
    strict = evaluate_one(make_rule(), metformin_snapshot(observations=(flagged,)))
    advisory = evaluate_one(
        make_rule(requires=(loosened,)), metformin_snapshot(observations=(flagged,))
    )

    # Assert
    assert strict.outcome is Outcome.indeterminate
    assert strict.requirement_verdicts[0].reason is RequirementReason.quality_below_minimum
    assert advisory.outcome is Outcome.triggered
    assert advisory.degraded_because is None


@pytest.mark.parametrize("status", [SourceStatus.cancelled, SourceStatus.entered_in_error])
def test_a_withdrawn_source_status_is_unusable_as_withdrawn_source(status):
    # Arrange — accepted_status also mismatches, but withdrawal outranks it
    observation = egfr_observation("25", source_status=status)

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert
    assert record.outcome is Outcome.indeterminate
    assert record.requirement_verdicts[0].reason is RequirementReason.withdrawn_source


@pytest.mark.parametrize("status", [MappingStatus.ambiguous, MappingStatus.unmapped])
def test_an_ambiguous_or_unmapped_observation_mapping_is_unusable(status):
    # Arrange — canon refused to commit to an observable identity (§5)
    observation = egfr_observation("25", mapping=MappingInfo(status=status))

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert
    assert record.outcome is Outcome.indeterminate
    assert record.requirement_verdicts[0].reason is RequirementReason.ambiguous_mapping


def test_an_observation_missing_required_context_is_unusable_as_missing_context():
    # Arrange — the chronicity flag the requirement demands is absent
    observation = egfr_observation("25", context_flags=())

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert
    assert record.outcome is Outcome.indeterminate
    assert record.requirement_verdicts[0].reason is RequirementReason.missing_context


def test_a_source_status_outside_accepted_status_is_wrong_source():
    # Arrange — preliminary is live data, just not the provenance declared (§8.2)
    observation = egfr_observation("25", source_status=SourceStatus.preliminary)

    # Act
    record = evaluate_one(make_rule(), metformin_snapshot(observations=(observation,)))

    # Assert
    assert record.outcome is Outcome.indeterminate
    assert record.requirement_verdicts[0].reason is RequirementReason.wrong_source


def test_an_entry_mode_outside_the_preferred_sources_is_graded_not_indeterminate():
    # Arrange — the requirement prefers interfaced results; staff_transcribed is
    # present data of lower grade (§8.2: prefer_source miss grades, never indeterminate)
    rule = make_rule(
        requires=(
            make_requirement(
                prefer_source=(EntryMode.interfaced,),
            ),
        )
    )

    # Act
    record = evaluate_one(rule, metformin_snapshot())  # staff_transcribed by default

    # Assert — present data grades the finding; it never manufactures indeterminacy
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review
    (verdict,) = record.requirement_verdicts
    assert verdict.verdict is RequirementVerdictValue.usable
    assert verdict.reason is RequirementReason.met


def test_a_silently_unusable_fact_makes_its_leaf_false_without_degrading():
    # Arrange — the conjunction needs both arms; potassium is absent and the
    # requirement chose silence, so the leaf proceeds as False (§7.1 amendment 5)
    rule = potassium_rule(
        when=Expression(
            op=Operator.all,
            children=(
                Expression(op=Operator.drug_requested, ingredient_id="metformin"),
                Expression(op=Operator.gt, fact="potassium", literal=Decimal("4.9")),
            ),
        ),
    )
    actions = (RequestedAction(kind=ActionKind.medication_start, subject="metformin"),)

    # Act
    record = evaluate_one(rule, make_snapshot(), actions)

    # Assert — recorded-but-silent never degrades; not_triggered, not indeterminate
    assert record.outcome is Outcome.not_triggered
    assert record.degraded_because is None
    (verdict,) = record.requirement_verdicts
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.reason is RequirementReason.no_result


def test_a_not_over_a_silent_unusable_fact_raises_cannot_assess():
    # Arrange — §8.3 A8: not(lt(potassium, 6)) with no potassium and silent
    # requirement must not manufacture a positive; it raises _CannotAssessSafely
    # which becomes indeterminate / requirements_unmet
    rule = potassium_rule(
        when=Expression(
            op=Operator.NOT,
            children=(Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.0")),),
        ),
    )

    # Act
    record = evaluate_one(rule, make_snapshot())

    # Assert — indeterminate with the requirement named, not a fabricated positive
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    (verdict,) = record.requirement_verdicts
    assert verdict.observable == "potassium"
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.reason is RequirementReason.no_result


def test_cannot_assess_safely_without_observable_still_works():
    # Arrange — edge case: _CannotAssessSafely raised without an observable
    # (should not happen in practice, but branch coverage requires it)
    from noor.engine.evaluate import _indeterminate
    from noor.engine.records import DegradedBecause, Outcome
    from noor.engine.rules import Severity
    from tests.conftest import make_pins

    rule = make_rule(id="test-rule", severity=Severity.stop_and_review)
    pins = make_pins()

    # Act — raise without observable
    record = _indeterminate(rule, (), pins)

    # Assert — indeterminate with empty verdicts
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert record.requirement_verdicts == ()


def test_cannot_assess_safely_none_observable_in_catch_block():
    # Arrange — directly test the catch block with observable=None
    # This covers the branch where e.observable is None
    from noor.engine.evaluate import _CannotAssessSafely, _consider
    from noor.engine.records import DegradedBecause, Outcome
    from noor.engine.rules import (
        DrugScopeLevel,
        Expression,
        Operator,
        ReleaseStatus,
        Rule,
        Severity,
    )
    from tests.conftest import (
        make_context,
        make_governance,
        make_pins,
        make_release,
        make_snapshot,
        make_then,
    )

    # Create a minimal rule with no requirements and a simple when expression
    rule = Rule(
        id="test-rule",
        version="1.0.0",
        release_status=ReleaseStatus.active,
        category="test",
        severity=Severity.stop_and_review,
        scope=Scope(),
        drug_scope_level=DrugScopeLevel.ingredient,
        requires=(),
        monitors=(),
        when=Expression(op=Operator.condition, concept="test_condition"),
        then=make_then(blocks=None),
        governance=make_governance(),
    )
    context = make_context(release=make_release(rules=(rule,)))
    snapshot = make_snapshot()
    pins = make_pins()

    # Monkeypatch _decide to raise _CannotAssessSafely without observable
    import noor.engine.evaluate as evaluate_module

    original_decide = evaluate_module._decide

    def mock_decide(*args, **kwargs):
        raise _CannotAssessSafely()  # No observable

    evaluate_module._decide = mock_decide
    try:
        # Act
        record = _consider(rule, context, snapshot, (), pins)
    finally:
        evaluate_module._decide = original_decide

    # Assert — indeterminate with empty verdicts (no synthesis)
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert record.requirement_verdicts == ()


def test_decide_raises_on_unknown_operator():
    # Arrange — the _decide function must be exhaustive over the Operator enum.
    # This test covers the NotImplementedError branch by constructing an
    # expression with an operator value that doesn't exist in the enum.
    from noor.engine.evaluate import _decide
    from tests.conftest import make_context, make_snapshot

    class UnknownOpExpression:
        op = "unknown_operator"
        children = ()
        fact = None
        literal = None
        threshold_ref = None
        ingredient_id = None
        verification_status = None
        severity = None
        reaction_type = None
        concept = None
        minimum = None
        maximum = None

    # Act / Assert
    context = make_context()
    snapshot = make_snapshot()
    with pytest.raises(NotImplementedError, match="no evaluation rule for"):
        _decide(UnknownOpExpression(), context, snapshot, (), {}, {})


@pytest.mark.parametrize(
    ("operator", "observed", "literal", "expected"),
    [
        (Operator.lt, "5.4", "5.5", Outcome.triggered),
        (Operator.le, "5.5", "5.5", Outcome.triggered),
        (Operator.gt, "5.6", "5.5", Outcome.triggered),
        (Operator.ge, "5.5", "5.5", Outcome.triggered),
        (Operator.eq, "5.5", "5.5", Outcome.triggered),
        (Operator.ne, "5.4", "5.5", Outcome.triggered),
        (Operator.lt, "5.6", "5.5", Outcome.not_triggered),
        (Operator.ne, "5.5", "5.5", Outcome.not_triggered),
    ],
)
def test_each_numeric_operator_compares_the_validated_value_against_its_literal(
    operator, observed, literal, expected
):
    # Arrange
    rule = potassium_rule(when=Expression(op=operator, fact="potassium", literal=Decimal(literal)))
    snapshot = make_snapshot(observations=(make_canonical(observable="potassium", value=observed),))

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert — the closed comparator vocabulary behaves on Decimals
    assert record.outcome is expected


@pytest.mark.parametrize(
    ("minimum", "maximum", "age_years", "expected"),
    [
        (18, 80, 67, Outcome.triggered),
        (67, 80, 67, Outcome.triggered),  # minimum is inclusive
        (18, 67, 67, Outcome.triggered),  # maximum is inclusive
        (68, None, 67, Outcome.not_triggered),
        (None, 66, 67, Outcome.not_triggered),
        (68, 80, 67, Outcome.not_triggered),
    ],
)
def test_an_age_leaf_bounds_the_range_inclusively_with_each_side_optional(
    minimum, maximum, age_years, expected
):
    # Arrange
    rule = make_rule(
        id="adult-age-gate",
        severity=Severity.passive_task,
        requires=(),
        monitors=(),
        when=Expression(op=Operator.age, minimum=minimum, maximum=maximum),
        then=make_then(blocks=None),
    )

    # Act
    record = evaluate_one(rule, make_snapshot(age_years=age_years))

    # Assert
    assert record.outcome is expected


def test_boolean_composition_nests_not_any_and_all():
    # Arrange — continue metformin unless hepatic impairment or advanced age
    rule = make_rule(
        when=Expression(
            op=Operator.all,
            children=(
                Expression(op=Operator.drug_active, ingredient_id="metformin"),
                Expression(
                    op=Operator.NOT,
                    children=(
                        Expression(
                            op=Operator.any,
                            children=(
                                Expression(op=Operator.condition, concept="hepatic_impairment"),
                                Expression(op=Operator.age, minimum=80),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    # Act
    plain = evaluate_one(rule, metformin_snapshot())
    impaired = evaluate_one(rule, metformin_snapshot(conditions=frozenset({"hepatic_impairment"})))
    elderly = evaluate_one(rule, metformin_snapshot(age_years=81))

    # Assert
    assert plain.outcome is Outcome.triggered
    assert impaired.outcome is Outcome.not_triggered
    assert elderly.outcome is Outcome.not_triggered


def test_an_absent_medication_entry_is_not_active():
    # Arrange — the continuation rule finds nothing on the list
    rule = make_rule()

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=()))

    # Assert
    assert record.outcome is Outcome.not_triggered


@pytest.mark.parametrize("status", [MappingStatus.ambiguous, MappingStatus.unmapped])
def test_an_ambiguous_or_unmapped_medication_entry_refuses_to_answer(status):
    # Arrange — design §5.1: guessing identity is never an option; the eGFR half
    # of the rule was fine, so this indeterminacy comes from the medication fact.
    # The rule has an eGFR requirement, so the manifest has an eGFR verdict.
    # The medication refusal synthesizes a second verdict for metformin.
    rule = make_rule()
    medications = (SnapshotMedication(ingredient_id="metformin", mapping_status=status),)

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=medications))

    # Assert
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert record.effective_severity is Severity.interruptive_review
    # Two verdicts: eGFR (from manifest) + metformin (synthesized from refusal)
    assert len(record.requirement_verdicts) == 2
    metformin_verdict = next(v for v in record.requirement_verdicts if v.observable == "metformin")
    assert metformin_verdict.verdict is RequirementVerdictValue.unusable
    assert metformin_verdict.reason is RequirementReason.no_result


def test_mapped_medication_alongside_unrelated_unmapped_entry_is_active():
    # Arrange — A7 fix: mapped metformin + unrelated ambiguous entry should
    # return True (known present), not raise. Only same-ingredient unresolved
    # entries cause refusal.
    rule = make_rule()
    medications = (
        SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped),
        SnapshotMedication(ingredient_id="other-drug", mapping_status=MappingStatus.ambiguous),
    )

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=medications))

    # Assert — known present answers cleanly
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is None
    assert record.effective_severity is Severity.stop_and_review


def test_mapped_medication_with_same_ingredient_ambiguous_is_active():
    # Arrange — A7 fix: known-present (mapped) answers True even alongside
    # same-ingredient ambiguous entries. Only absence needs to worry about
    # unresolved entries.
    rule = make_rule()
    medications = (
        SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped),
        SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.ambiguous),
    )

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=medications))

    # Assert — known present answers cleanly
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is None
    assert record.effective_severity is Severity.stop_and_review


@pytest.mark.parametrize(
    "kind",
    [ActionKind.medication_start, ActionKind.medication_dose_change],
)
def test_a_planned_start_or_dose_change_puts_the_drug_in_play(kind):
    # Arrange — §11.6's projection: these two kinds propose adding the drug
    rule = make_rule(when=_requested_metformin_conjunction())
    actions = (RequestedAction(kind=kind, subject="metformin"),)

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=()), actions)

    # Assert
    assert record.outcome is Outcome.triggered


@pytest.mark.parametrize(
    "kind",
    [
        ActionKind.medication_stop,
        ActionKind.lab_order,
        ActionKind.referral,
        ActionKind.plan_change,
    ],
)
def test_a_planned_stop_or_unrelated_action_does_not_match_the_request(kind):
    # Arrange — medication_stop withdraws the drug; it never matches (§11.6)
    rule = make_rule(when=_requested_metformin_conjunction())
    actions = (RequestedAction(kind=kind, subject="metformin"),)

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=()), actions)

    # Assert
    assert record.outcome is Outcome.not_triggered


def test_a_requested_action_for_another_subject_does_not_match():
    # Arrange
    rule = make_rule(when=_requested_metformin_conjunction())
    actions = (RequestedAction(kind=ActionKind.medication_start, subject="insulin"),)

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=()), actions)

    # Assert — ingredient-level matching, exact on the subject (§7.1(e))
    assert record.outcome is Outcome.not_triggered


def _requested_metformin_conjunction():
    return Expression(
        op=Operator.all,
        children=(
            Expression(op=Operator.lt, fact="egfr", threshold_ref=EGFR_REF),
            Expression(op=Operator.drug_requested, ingredient_id="metformin"),
        ),
    )


def test_a_confirmed_allergy_satisfying_the_leaf_filters_triggers_cleanly():
    # Arrange — §5.5: verified severe allergy is exactly what the leaf asks for
    rule = allergy_rule(when=CONFIRMED_SEVERE_PENICILLIN)

    # Act
    record = evaluate_one(rule, allergy_snapshot())

    # Assert — clean finding: nothing graded, nothing degraded
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is None
    assert record.effective_severity is Severity.interruptive_review
    assert record.requirement_verdicts == ()


def test_an_unconfirmed_allergy_failing_the_filters_still_surfaces_graded():
    # Arrange — the leaf asks confirmed+severe; the record is unconfirmed severe.
    # It surfaces anyway (§5.5 table) but only as graded evidence.
    rule = allergy_rule(when=CONFIRMED_SEVERE_PENICILLIN)
    unverified = make_allergy(
        culprit=CulpritSubstance(ingredient_id="penicillin"),
        verification_status=VerificationStatus.unconfirmed,
    )

    # Act
    record = evaluate_one(rule, allergy_snapshot(allergies=(unverified,)))

    # Assert
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade


def test_a_severity_below_the_leaf_filter_surfaces_graded():
    # Arrange — §5.5: confirmed moderate triggers, capped to documented severity
    rule = allergy_rule(when=CONFIRMED_SEVERE_PENICILLIN)
    moderate = make_allergy(
        culprit=CulpritSubstance(ingredient_id="penicillin"),
        severity=AllergySeverity.moderate,
    )

    # Act
    record = evaluate_one(rule, allergy_snapshot(allergies=(moderate,)))

    # Assert
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade


def test_an_unconfirmed_record_grades_a_filterless_leaf_unconditionally():
    # Arrange — §5.5 table: unconfirmed grades the finding whatever filters the
    # leaf declares (here none); a hard stop proves the cap
    rule = allergy_rule(severity=Severity.stop_and_review)
    unverified = make_allergy(
        culprit=CulpritSubstance(ingredient_id="penicillin"),
        verification_status=VerificationStatus.unconfirmed,
    )

    # Act
    record = evaluate_one(rule, allergy_snapshot(allergies=(unverified,)))

    # Assert — the grade attaches to the data, not to a failed filter
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review


def test_a_confirmed_record_satisfies_a_filterless_leaf_cleanly():
    # Arrange — the negative control: same leaf, verified record
    rule = allergy_rule(severity=Severity.stop_and_review)

    # Act — allergy_snapshot() is a confirmed severe penicillin allergy
    record = evaluate_one(rule, allergy_snapshot())

    # Assert — clean finding at full authored severity, nothing graded
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is None
    assert record.effective_severity is Severity.stop_and_review


@pytest.mark.parametrize(
    "status", [VerificationStatus.refuted, VerificationStatus.entered_in_error]
)
def test_refuted_and_entered_in_error_records_never_surface(status):
    # Arrange — claim 47: delabelling and typo entries are silent at any filter
    rule = allergy_rule(when=CONFIRMED_SEVERE_PENICILLIN)
    record_entry = make_allergy(
        culprit=CulpritSubstance(ingredient_id="penicillin"),
        verification_status=status,
    )

    # Act
    outcome_record = evaluate_one(rule, allergy_snapshot(allergies=(record_entry,)))

    # Assert
    assert outcome_record.outcome is Outcome.not_triggered


def test_a_record_for_another_ingredient_does_not_satisfy_the_leaf():
    # Arrange
    rule = allergy_rule(when=CONFIRMED_SEVERE_PENICILLIN)  # penicillin

    # Act — the snapshot's allergy is amoxicillin (the underlying factory default)
    record = evaluate_one(rule, allergy_snapshot(allergies=(make_allergy(),)))

    # Assert
    assert record.outcome is Outcome.not_triggered


def test_an_unasked_allergy_history_leaves_the_leaf_unanswerable():
    # Arrange — §5.5 rule 2: not_asked is unanswered, never cleared
    rule = allergy_rule()

    # Act
    record = evaluate_one(
        rule, allergy_snapshot(allergies=(), allergy_status=AllergyStatus.not_asked)
    )

    # Assert — the rule has no requirements, so the manifest has empty verdicts.
    # The allergy refusal synthesizes a verdict for penicillin.
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert len(record.requirement_verdicts) == 1
    pen_verdict = record.requirement_verdicts[0]
    assert pen_verdict.observable == "penicillin"
    assert pen_verdict.verdict is RequirementVerdictValue.unusable
    assert pen_verdict.reason is RequirementReason.no_result


def test_two_active_goals_fail_the_rule_without_silencing_other_rules():
    # Arrange — §8.2 conflicting goals: the engine refuses to choose, and the
    # neighbouring rule still runs (invariant 11 territory, claim 43 shape)
    goals = (
        make_goal(observable="egfr", value=Decimal("20"), unit="mL/min/{1.73_m2}"),
        make_goal(
            observable="egfr",
            value=Decimal("22"),
            unit="mL/min/{1.73_m2}",
            clinician_id="DR-9",
            reason="Second opinion, unresolved",
        ),
    )
    guard = make_rule(
        id="metformin-start-guard",
        severity=Severity.interruptive_review,
        requires=(),
        monitors=(),
        when=Expression(op=Operator.drug_requested, ingredient_id="metformin"),
        then=make_then(blocks=None),
    )
    context = make_context(release=make_release(rules=(make_rule(), guard)))

    # Act
    records = evaluate(context, metformin_snapshot(goals_of_care=goals), ())
    by_id = {record.rule_id: record for record in records}

    # Assert — the conflicted rule fails with the exception type name only
    failed = by_id["metformin-egfr-contraindicated"]
    assert failed.outcome is Outcome.evaluation_failed
    assert failed.failure_reason == "AmbiguousGoalOfCareError"
    assert failed.degraded_because is DegradedBecause.rule_raised
    assert failed.effective_severity is Severity.interruptive_review
    assert failed.authored_severity is Severity.stop_and_review
    assert failed.requirement_verdicts == ()
    assert failed.pins.snapshot_id == "SNAP-1"
    assert by_id["metformin-start-guard"].outcome is Outcome.not_triggered


def test_records_are_returned_sorted_by_rule_id():
    # Arrange — release order deliberately unsorted
    rules = (
        potassium_rule(
            "c-rule", when=Expression(op=Operator.gt, fact="potassium", literal=Decimal("7"))
        ),
        potassium_rule(
            "a-rule", when=Expression(op=Operator.gt, fact="potassium", literal=Decimal("5"))
        ),
        potassium_rule("b-rule"),
    )
    context = make_context(release=make_release(rules=rules))
    snapshot = make_snapshot(observations=(make_canonical(observable="potassium", value="6.5"),))

    # Act
    records = evaluate(context, snapshot, ())

    # Assert
    assert [record.rule_id for record in records] == ["a-rule", "b-rule", "c-rule"]


def test_a_planned_start_catches_the_contraindicated_new_order():
    # Arrange — design §8.1's owed pair: not on metformin, eGFR 25, start planned
    rule = make_rule(when=_requested_metformin_conjunction())
    actions = (RequestedAction(kind=ActionKind.medication_start, subject="metformin"),)

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=()), actions)

    # Assert — the whole point of drug_requested: it blocks before the first dose
    assert record.outcome is Outcome.triggered
    assert record.effective_severity is Severity.stop_and_review
    assert record.degraded_because is None


def test_the_same_patient_without_a_planned_action_is_not_triggered():
    # Arrange — identical patient, empty planned-action list
    rule = make_rule(when=_requested_metformin_conjunction())

    # Act
    record = evaluate_one(rule, metformin_snapshot(medications=()), ())

    # Assert
    assert record.outcome is Outcome.not_triggered


def test_a_continuation_rule_still_triggers_when_nothing_is_planned():
    # Arrange — design §8.1: on metformin, eGFR 25, nothing ordered today
    rule = make_rule()  # keys on drug_active

    # Act
    record = evaluate_one(rule, metformin_snapshot(), ())

    # Assert — discontinuation advice survives a visit with no order
    assert record.outcome is Outcome.triggered
    assert record.effective_severity is Severity.stop_and_review


def test_a_crcl_requirement_is_never_satisfied_by_egfr_or_creatinine():
    # Arrange — claim 36: the snapshot holds both renal cousins, neither is CrCl
    rule = make_rule(
        id="crcl-metformin-guard",
        requires=(make_requirement(observable="crcl", renal_metric="crcl"),),
        when=Expression(
            op=Operator.all,
            children=(
                Expression(op=Operator.lt, fact="crcl", literal=Decimal("45")),
                Expression(op=Operator.drug_requested, ingredient_id="metformin"),
            ),
        ),
    )
    snapshot = metformin_snapshot(
        medications=(),
        observations=(
            egfr_observation("25"),
            make_canonical(observable="creatinine", value="2.1"),
        ),
    )
    actions = (RequestedAction(kind=ActionKind.medication_start, subject="metformin"),)

    # Act
    record = evaluate_one(rule, snapshot, actions)

    # Assert — no substitution: the missing metric degrades the rule
    assert record.outcome is Outcome.indeterminate
    (verdict,) = record.requirement_verdicts
    assert verdict.observable == "crcl"
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.reason is RequirementReason.no_result
    assert verdict.latest_age_days is None


@pytest.mark.parametrize(
    ("role", "conditions"),
    [
        (InformantRole.patient, frozenset()),
        (InformantRole.medicine_manager, frozenset()),  # manager, but no impairment
    ],
)
def test_a_patient_reported_value_without_the_grade_tripwire_is_not_graded(role, conditions):
    # Arrange — the grade keys on impairment + manager together (§5.4, §5.7)
    observation = make_canonical(
        observable="potassium",
        value="6.5",
        entry_mode=EntryMode.patient_reported,
        informant=Informant(role=role, person_id="P-1"),
    )

    # Act
    record = evaluate_one(
        hyperkalemia_hard_stop(),
        make_snapshot(observations=(observation,), conditions=conditions),
    )

    # Assert — solid evidence: the finding presents at full authored severity
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is None
    assert record.effective_severity is Severity.stop_and_review
