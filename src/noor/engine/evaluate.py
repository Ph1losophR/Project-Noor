"""The per-rule evaluator: one §8.2 record for every rule considered (SSOT §8.1-§8.5).

One pass over the release's rules, each independent (§8.4 invariants 5 and 7).
Per rule the order is fixed: governance suppression stops before scope, scope
stops before the requirements manifest, requirements gate the `when` tree, and
the tree's leaves read only requirement-validated values (§7.1 amendment 5).
Every degradation cause routes through the one shared severity cap, and any
exception a rule raises becomes that rule's `evaluation_failed` record — one
raising rule never ends the run (§8.5).
"""

from collections.abc import Callable, Mapping
from decimal import Decimal
from operator import eq, ge, gt, le, lt, ne
from typing import NamedTuple

from noor.canon.models import (
    ACCEPTED_FAMILY,
    WITHDRAWN_SOURCE_STATUSES,
    CanonicalObservation,
    EntryMode,
    InformantRole,
    MappingStatus,
    QualityState,
)
from noor.engine.content import EvaluationContext, Pins
from noor.engine.records import (
    DegradedBecause,
    EvaluationRecord,
    Outcome,
    RequirementReason,
    RequirementVerdict,
    RequirementVerdictValue,
    cap_below_stop_and_review,
)
from noor.engine.rules import Expression, OnUnusable, Operator, Requirement, Rule, Severity
from noor.engine.snapshot import (
    ActionKind,
    AllergyRecord,
    AllergyStatus,
    RequestedAction,
    Snapshot,
    VerificationStatus,
)

_BOOLEAN_OPS: frozenset[Operator] = frozenset({Operator.all, Operator.any, Operator.NOT})
_NUMERIC_OPS: frozenset[Operator] = frozenset(
    {Operator.lt, Operator.le, Operator.gt, Operator.ge, Operator.eq, Operator.ne}
)
_COMPARATORS: Mapping[Operator, Callable[[Decimal, Decimal], bool]] = {
    Operator.lt: lt,
    Operator.le: le,
    Operator.gt: gt,
    Operator.ge: ge,
    Operator.eq: eq,
    Operator.ne: ne,
}
# §11.6: only these two kinds propose putting the drug in play; a planned stop
# withdraws it and never matches drug_requested.
_IN_PLAY: frozenset[ActionKind] = frozenset(
    {ActionKind.medication_start, ActionKind.medication_dose_change}
)
# §5.5: delabelling and typo entries are the one place a more complete record
# quiets the engine; they are excluded before any leaf filter runs.
_NEVER_SURFACING: frozenset[VerificationStatus] = frozenset(
    {VerificationStatus.refuted, VerificationStatus.entered_in_error}
)


class _CannotAssessSafely(Exception):
    """A leaf met data the engine refuses to guess about (§5.1, §5.5).

    An ambiguous medication mapping and an unasked allergy history are
    refusals, not defects: they degrade the rule to indeterminate under
    requirements_unmet rather than to the §8.5 failure record, so the per-rule
    handler resolves this class before the generic catch.
    """


class _Manifest(NamedTuple):
    """What reading one rule's requires manifest produced (§7.1(a), §8.2)."""

    verdicts: tuple[RequirementVerdict, ...]
    validated: Mapping[str, Decimal]
    graded: frozenset[str]
    degrades: bool


def evaluate(
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
) -> tuple[EvaluationRecord, ...]:
    """Consider every rule in the release against one snapshot (SSOT §8.1).

    Pure: the inputs are read, never written; time is the snapshot's
    `evaluated_at`; every record pins the snapshot id; the tuple returns
    sorted by rule_id.
    """
    records = tuple(
        _evaluate_rule(rule, context, snapshot, requested_actions) for rule in context.release.rules
    )
    return tuple(sorted(records, key=lambda record: record.rule_id))


def _evaluate_rule(
    rule: Rule,
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
) -> EvaluationRecord:
    pins = context.pins.model_copy(update={"snapshot_id": snapshot.snapshot_id})
    try:
        return _consider(rule, context, snapshot, requested_actions, pins)
    except Exception as exc:  # §8.5: the exception type name only, never the message
        return _record(
            rule,
            Outcome.evaluation_failed,
            cap_below_stop_and_review(rule.severity),
            DegradedBecause.rule_raised,
            type(exc).__name__,
            (),
            pins,
        )


def _consider(
    rule: Rule,
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
    pins: Pins,
) -> EvaluationRecord:
    if rule.id in _disabled_ids(context):
        return _record(
            rule, Outcome.suppressed_by_governed_policy, rule.severity, None, None, (), pins
        )
    if not _in_scope(rule, context, snapshot):
        return _record(rule, Outcome.out_of_scope, rule.severity, None, None, (), pins)
    manifest = _resolve_manifest(rule.requires, snapshot)
    if manifest.degrades:
        return _indeterminate(rule, manifest.verdicts, pins)
    try:
        matched, graded = _decide(
            rule.when, context, snapshot, requested_actions, manifest.validated
        )
    except _CannotAssessSafely:
        return _indeterminate(rule, manifest.verdicts, pins)
    if not matched:
        return _record(
            rule, Outcome.not_triggered, rule.severity, None, None, manifest.verdicts, pins
        )
    if graded or manifest.graded:
        # §8.3: graded evidence caps the finding; it never manufactures indeterminacy
        return _record(
            rule,
            Outcome.triggered,
            cap_below_stop_and_review(rule.severity),
            DegradedBecause.evidence_grade,
            None,
            manifest.verdicts,
            pins,
        )
    return _record(rule, Outcome.triggered, rule.severity, None, None, manifest.verdicts, pins)


def _indeterminate(
    rule: Rule, verdicts: tuple[RequirementVerdict, ...], pins: Pins
) -> EvaluationRecord:
    return _record(
        rule,
        Outcome.indeterminate,
        cap_below_stop_and_review(rule.severity),
        DegradedBecause.requirements_unmet,
        None,
        verdicts,
        pins,
    )


def _record(
    rule: Rule,
    outcome: Outcome,
    effective: Severity,
    degraded: DegradedBecause | None,
    failure: str | None,
    verdicts: tuple[RequirementVerdict, ...],
    pins: Pins,
) -> EvaluationRecord:
    return EvaluationRecord(
        rule_id=rule.id,
        rule_version=rule.version,
        outcome=outcome,
        authored_severity=rule.severity,
        effective_severity=effective,
        degraded_because=degraded,
        failure_reason=failure,
        requirement_verdicts=verdicts,
        pins=pins,
    )


def _disabled_ids(context: EvaluationContext) -> frozenset[str]:
    return frozenset(disablement.rule_id for disablement in context.release.profile.disablements)


def _in_scope(rule: Rule, context: EvaluationContext, snapshot: Snapshot) -> bool:
    included = all(_decide(p, context, snapshot, (), {})[0] for p in rule.scope.include)
    excluded = any(_decide(p, context, snapshot, (), {})[0] for p in rule.scope.exclude)
    return included and not excluded


def _decide(
    node: Expression,
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
    validated: Mapping[str, Decimal],
) -> tuple[bool, bool]:
    """Evaluate one expression node to (matched, contributed evidence grade)."""
    if node.op in _BOOLEAN_OPS:
        return _decide_boolean(node, context, snapshot, requested_actions, validated)
    if node.op in _NUMERIC_OPS:
        return _compare(node, context, snapshot, validated)
    if node.op is Operator.drug_active:
        return _drug_active(node.ingredient_id, snapshot), False
    if node.op is Operator.drug_requested:
        return _drug_requested(node.ingredient_id, requested_actions), False
    if node.op is Operator.allergy:
        return _allergy(node, snapshot)
    if node.op is Operator.condition:
        return node.concept in snapshot.conditions, False
    return _age_within(node, snapshot), False


def _decide_boolean(
    node: Expression,
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
    validated: Mapping[str, Decimal],
) -> tuple[bool, bool]:
    outcomes = [
        _decide(child, context, snapshot, requested_actions, validated) for child in node.children
    ]
    if node.op is Operator.NOT:
        # A graded leaf is graded only alongside a True match; negated, it
        # contributed nothing to any finding.
        only = outcomes[0]
        return not only[0], False
    if node.op is Operator.all:
        matched = all(decision for decision, _ in outcomes)
    else:
        matched = any(decision for decision, _ in outcomes)
    return matched, matched and any(graded for decision, graded in outcomes if decision)


def _compare(
    node: Expression,
    context: EvaluationContext,
    snapshot: Snapshot,
    validated: Mapping[str, Decimal],
) -> tuple[bool, bool]:
    fact = node.fact
    assert fact is not None  # a numeric leaf always names its fact (load-time, §7.1)
    observed = validated.get(fact)
    if observed is None:
        # Silent-unusable: the leaf proceeds without the fact, never against raw data.
        return False, False
    if node.literal is not None:
        return _COMPARATORS[node.op](observed, node.literal), False
    ref = node.threshold_ref
    assert ref is not None  # §4.3.1: exactly one comparison source, validated at load
    target = context.resolve_threshold(snapshot, fact, ref)
    return _COMPARATORS[node.op](observed, target.value), False


def _drug_active(ingredient_id: str | None, snapshot: Snapshot) -> bool:
    entries = [entry for entry in snapshot.medications if entry.ingredient_id == ingredient_id]
    if any(entry.mapping_status is not MappingStatus.mapped for entry in entries):
        # Design §5.1: an unresolved identity is a refusal, never a guess.
        raise _CannotAssessSafely()
    return bool(entries)


def _drug_requested(
    ingredient_id: str | None, requested_actions: tuple[RequestedAction, ...]
) -> bool:
    return any(
        action.subject == ingredient_id and action.kind in _IN_PLAY for action in requested_actions
    )


def _allergy(node: Expression, snapshot: Snapshot) -> tuple[bool, bool]:
    if snapshot.allergy_status is AllergyStatus.not_asked:
        # §5.5 rule 2: unanswered is its own fact; "cleared" is never inferred.
        raise _CannotAssessSafely()
    surfaced = [
        record
        for record in snapshot.allergies
        if record.culprit.ingredient_id == node.ingredient_id
        and record.verification_status not in _NEVER_SURFACING
    ]
    if any(_leaf_satisfied(record, node) for record in surfaced):
        return True, False
    # Whatever surfaces but fails the leaf's filters is present data of lower grade.
    return bool(surfaced), bool(surfaced)


def _leaf_satisfied(record: AllergyRecord, leaf: Expression) -> bool:
    verified = (
        leaf.verification_status is None or record.verification_status is leaf.verification_status
    )
    return verified and (leaf.severity is None or record.severity is leaf.severity)


def _age_within(node: Expression, snapshot: Snapshot) -> bool:
    if node.minimum is not None and snapshot.age_years < node.minimum:
        return False
    return node.maximum is None or snapshot.age_years <= node.maximum


def _resolve_manifest(requirements: tuple[Requirement, ...], snapshot: Snapshot) -> _Manifest:
    verdicts: list[RequirementVerdict] = []
    validated: dict[str, Decimal] = {}
    graded: set[str] = set()
    degrades = False
    for requirement in requirements:
        verdict, observation = _resolve_requirement(requirement, snapshot)
        verdicts.append(verdict)
        if verdict.verdict is RequirementVerdictValue.usable:
            assert observation is not None  # usable means an observation was selected
            validated[requirement.observable] = _canonical_value(observation)
            if _evidence_is_graded(observation, requirement, snapshot):
                graded.add(requirement.observable)
        elif requirement.on_unusable is OnUnusable.indeterminate:
            degrades = True  # silent-unusable verdicts are recorded and proceed (§8.3)
    return _Manifest(tuple(verdicts), validated, frozenset(graded), degrades)


def _resolve_requirement(
    requirement: Requirement, snapshot: Snapshot
) -> tuple[RequirementVerdict, CanonicalObservation | None]:
    latest = _latest_observation(requirement.observable, snapshot)
    if latest is None:
        return _verdict(
            requirement.observable,
            RequirementVerdictValue.unusable,
            RequirementReason.no_result,
            None,
        ), None
    age_days = (snapshot.evaluated_at - latest.effective_time).days
    reason = _first_failure(requirement, latest, age_days)
    if reason is not None:
        return _verdict(
            requirement.observable, RequirementVerdictValue.unusable, reason, age_days
        ), latest
    # A usable verdict still carries the neutral reason: §8.2 links no member
    # to "met", and the vocabulary exists for failures, not successes.
    return _verdict(
        requirement.observable,
        RequirementVerdictValue.usable,
        RequirementReason.no_result,
        age_days,
    ), latest


def _verdict(
    observable: str,
    value: RequirementVerdictValue,
    reason: RequirementReason,
    age_days: int | None,
) -> RequirementVerdict:
    return RequirementVerdict(
        observable=observable, verdict=value, reason=reason, latest_age_days=age_days
    )


def _latest_observation(observable: str, snapshot: Snapshot) -> CanonicalObservation | None:
    matches = [o for o in snapshot.observations if o.observable == observable]
    return max(matches, key=lambda o: o.effective_time, default=None)


def _first_failure(
    requirement: Requirement, observation: CanonicalObservation, age_days: int
) -> RequirementReason | None:
    """The first failed check in §8.2's declared order; first failure wins."""
    if observation.mapping.status is not MappingStatus.mapped:
        return RequirementReason.ambiguous_mapping
    if observation.source_status in WITHDRAWN_SOURCE_STATUSES:
        return RequirementReason.withdrawn_source
    if requirement.accepted_status and observation.source_status not in requirement.accepted_status:
        return RequirementReason.wrong_source
    if not _quality_usable(requirement, observation):
        return RequirementReason.quality_below_minimum
    if requirement.max_age_days is not None and age_days > requirement.max_age_days:
        return RequirementReason.stale  # exactly max_age_days stays usable
    if requirement.prefer_source and observation.entry_mode not in requirement.prefer_source:
        return RequirementReason.wrong_source
    if not set(requirement.required_context) <= set(observation.context_flags):
        return RequirementReason.missing_context
    return None


def _quality_usable(requirement: Requirement, observation: CanonicalObservation) -> bool:
    state = observation.quality.state
    if state in ACCEPTED_FAMILY:
        return True
    # The one explicit loosening: an advisory rule may accept a flagged value.
    return (
        state is QualityState.needs_repeat_or_verification
        and requirement.min_quality is QualityState.needs_repeat_or_verification
    )


def _evidence_is_graded(
    observation: CanonicalObservation, requirement: Requirement, snapshot: Snapshot
) -> bool:
    informant = (
        observation.informant
    )  # patient_reported guarantees one (§5.4); None narrows the type
    manager_report = (
        observation.entry_mode is EntryMode.patient_reported
        and informant is not None
        and informant.role is InformantRole.medicine_manager
        and "cognitive_impairment" in snapshot.conditions
    )
    noor_substitute = (
        observation.entry_mode is EntryMode.noor_derived
        and EntryMode.interfaced in requirement.prefer_source
    )
    return manager_report or noor_substitute


def _canonical_value(observation: CanonicalObservation) -> Decimal:
    canonical = observation.canonical
    assert canonical is not None  # canon's invariant: accepted-family carries a value (§6.3)
    return canonical.value
