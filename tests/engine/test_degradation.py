"""The §8.3 degradation invariant, driven through `evaluate`.

Three causes, three records: unmet requirements degrade a hard stop to
indeterminate at interruptive_review (claim 4); graded evidence keeps the
finding triggered and caps it (claims 34 and 48), never manufacturing
indeterminacy; an unasked allergy history is indeterminate and never reads as
cleared (claim 35). One shared cap, so no double demotion.
"""

from decimal import Decimal

import pytest

from noor.canon.models import EntryMode, Informant, InformantRole
from noor.engine.evaluate import evaluate
from noor.engine.records import DegradedBecause, Outcome, RequirementReason, RequirementVerdictValue
from noor.engine.rules import Expression, Operator, Severity
from noor.engine.snapshot import (
    ActionKind,
    AllergySeverity,
    AllergyStatus,
    CulpritSubstance,
    RequestedAction,
    VerificationStatus,
)
from tests.conftest import (
    make_allergy,
    make_canonical,
    make_context,
    make_release,
    make_requirement,
    make_rule,
    make_snapshot,
    make_then,
)

CONFIRMED_SEVERE_PENICILLIN = Expression(
    op=Operator.allergy,
    ingredient_id="penicillin",
    verification_status=VerificationStatus.confirmed,
    severity=AllergySeverity.severe,
)


def hard_stop_allergy_rule():
    """A stop_and_review penicillin rule asking for verified severe allergy."""
    return make_rule(
        id="penicillin-allergy-hard-stop",
        requires=(),
        monitors=(),
        when=CONFIRMED_SEVERE_PENICILLIN,
        then=make_then(blocks=None),
    )


def hyperkalemia_hard_stop(**requirement_overrides):
    """A stop_and_review potassium comparison; override its requirement."""
    fields = {
        "observable": "potassium",
        "accepted_status": (),
        "min_quality": None,
        "max_age_days": None,
        "prefer_source": (),
        "required_context": (),
        "renal_metric": None,
    }
    fields.update(requirement_overrides)
    requirement = make_requirement(**fields)
    return make_rule(
        id="hyperkalemia-hard-stop",
        requires=(requirement,),
        monitors=(),
        when=Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.0")),
        then=make_then(blocks=None),
    )


def manager_reported_potassium(**snapshot_overrides):
    """Potassium 6.5 reported by the medicine manager of an impaired patient."""
    observation = make_canonical(
        observable="potassium",
        value="6.5",
        entry_mode=EntryMode.patient_reported,
        informant=Informant(role=InformantRole.medicine_manager, person_id="MM-1"),
    )
    fields = {"observations": (observation,), "conditions": frozenset({"cognitive_impairment"})}
    fields.update(snapshot_overrides)
    return make_snapshot(**fields)


def noor_derived_potassium():
    """Potassium 6.5 derived by Noor where interfaced results are expected."""
    observation = make_canonical(
        observable="potassium", value="6.5", entry_mode=EntryMode.noor_derived
    )
    return make_snapshot(observations=(observation,))


def evaluate_one(rule, snapshot):
    """Evaluate a single-rule release and return its only record."""
    context = make_context(release=make_release(rules=(rule,)))
    records = evaluate(context, snapshot, ())
    assert len(records) == 1
    return records[0]


def test_claim_4_unmet_requirements_degrade_a_hard_stop_to_indeterminate():
    # Arrange — the metformin hard stop against a snapshot with no eGFR at all
    record = evaluate_one(make_rule(), make_snapshot())

    # Assert — §8.3: degraded, capped, authored intact, requirement named
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review
    (verdict,) = record.requirement_verdicts
    assert verdict.observable == "egfr"
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.reason is RequirementReason.no_result


def test_claim_34_an_unconfirmed_allergy_degrades_the_finding_never_the_answer():
    # Arrange — the leaf demands confirmed severe; the record is hearsay
    unverified = make_allergy(
        culprit=CulpritSubstance(ingredient_id="penicillin"),
        verification_status=VerificationStatus.unconfirmed,
    )

    # Act
    record = evaluate_one(hard_stop_allergy_rule(), make_snapshot(allergies=(unverified,)))

    # Assert — present data of lower grade: triggered, capped, never indeterminate,
    # and never allowed to block an order on hearsay (§5.5, §8.3)
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review
    assert record.effective_severity is not Severity.stop_and_review


def test_claim_35_an_unasked_history_is_indeterminate_and_never_reads_as_cleared():
    # Arrange — nobody asked; the engine may not pass silently (§5.5)
    snapshot = make_snapshot(allergies=(), allergy_status=AllergyStatus.not_asked)

    # Act
    record = evaluate_one(hard_stop_allergy_rule(), snapshot)

    # Assert — exactly indeterminate, never not_triggered, obligation-opening
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet
    assert record.effective_severity is Severity.interruptive_review


GRADED_CASES = ("unconfirmed_allergy", "manager_report", "noor_derived_value")


def _graded_case(case):
    """The graded-input half of claim 48: data present, grade lower."""
    if case == "unconfirmed_allergy":
        unverified = make_allergy(
            culprit=CulpritSubstance(ingredient_id="penicillin"),
            verification_status=VerificationStatus.unconfirmed,
        )
        return hard_stop_allergy_rule(), make_snapshot(allergies=(unverified,))
    if case == "manager_report":
        return hyperkalemia_hard_stop(), manager_reported_potassium()
    tolerated = {"prefer_source": (EntryMode.interfaced, EntryMode.noor_derived)}
    return hyperkalemia_hard_stop(**tolerated), noor_derived_potassium()


def _absent_case(case):
    """The same input absent: an unanswered question, not a graded finding."""
    if case == "unconfirmed_allergy":
        snapshot = make_snapshot(allergies=(), allergy_status=AllergyStatus.not_asked)
        return hard_stop_allergy_rule(), snapshot
    if case == "manager_report":
        return hyperkalemia_hard_stop(), make_snapshot()
    tolerated = {"prefer_source": (EntryMode.interfaced, EntryMode.noor_derived)}
    return hyperkalemia_hard_stop(**tolerated), make_snapshot()


@pytest.mark.parametrize("case", GRADED_CASES)
def test_claim_48_each_graded_input_keeps_the_finding_triggered_at_the_cap(case):
    # Arrange / Act
    record = evaluate_one(*_graded_case(case))

    # Assert — evidence grade caps severity without ever producing indeterminate
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review


@pytest.mark.parametrize("case", GRADED_CASES)
def test_claim_48_the_same_input_absent_leaves_the_question_indeterminate(case):
    # Arrange / Act
    record = evaluate_one(*_absent_case(case))

    # Assert — absence degrades as requirements_unmet, never as evidence_grade
    assert record.outcome is Outcome.indeterminate
    assert record.degraded_because is DegradedBecause.requirements_unmet


def test_a_noor_derived_value_is_not_graded_when_interfaced_is_not_preferred():
    # Arrange — §5.7: the substitution grade keys on interfaced ∈ prefer_source
    rule = hyperkalemia_hard_stop(prefer_source=(EntryMode.noor_derived,))

    # Act
    record = evaluate_one(rule, noor_derived_potassium())

    # Assert — an expected derivation, not a substitute: full authored severity
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is None
    assert record.effective_severity is Severity.stop_and_review


def test_a_graded_child_inside_a_boolean_parent_propagates_its_grade():
    # Arrange — a start guard whose allergy arm matches hearsay data
    rule = make_rule(
        id="metformin-start-guard",
        requires=(),
        monitors=(),
        when=Expression(
            op=Operator.all,
            children=(
                Expression(op=Operator.drug_requested, ingredient_id="metformin"),
                CONFIRMED_SEVERE_PENICILLIN,
            ),
        ),
        then=make_then(blocks=None),
    )
    unverified = make_allergy(
        culprit=CulpritSubstance(ingredient_id="penicillin"),
        verification_status=VerificationStatus.unconfirmed,
    )
    actions = (RequestedAction(kind=ActionKind.medication_start, subject="metformin"),)

    # Act
    context = make_context(release=make_release(rules=(rule,)))
    records = evaluate(context, make_snapshot(allergies=(unverified,)), actions)

    # Assert — the graded child caps the composed finding; no double demotion
    assert len(records) == 1
    record = records[0]
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade
    assert record.effective_severity is Severity.interruptive_review
    assert record.authored_severity is Severity.stop_and_review


def test_the_cap_is_single_a_graded_passive_task_stays_passive_task():
    # Arrange — the softest severity with a graded input behind it
    rule = make_rule(
        id="hyperkalemia-note",
        severity=Severity.passive_task,
        requires=(
            make_requirement(
                observable="potassium",
                accepted_status=(),
                min_quality=None,
                max_age_days=None,
                prefer_source=(EntryMode.interfaced, EntryMode.noor_derived),
                required_context=(),
                renal_metric=None,
            ),
        ),
        monitors=(),
        when=Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.0")),
        then=make_then(blocks=None),
    )

    # Act
    record = evaluate_one(rule, noor_derived_potassium())

    # Assert — one cap, applied once: recorded cause, unchanged severity
    assert record.outcome is Outcome.triggered
    assert record.degraded_because is DegradedBecause.evidence_grade
    assert record.effective_severity is Severity.passive_task
