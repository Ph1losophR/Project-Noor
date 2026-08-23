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
from datetime import timedelta
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
from noor.engine.content import (
    EvaluationContext,
    Pins,
)
from noor.engine.records import (
    DegradedBecause,
    EvaluationRecord,
    Outcome,
    RequirementReason,
    RequirementVerdict,
    RequirementVerdictValue,
    cap_below_stop_and_review,
)
from noor.engine.rules import (
    BOOLEAN_OPERATORS,
    NUMERIC_OPERATORS,
    Expression,
    OnUnusable,
    Operator,
    Requirement,
    Rule,
    Severity,
)
from noor.engine.snapshot import (
    ActionKind,
    AllergyRecord,
    AllergySeverity,
    AllergyStatus,
    RequestedAction,
    Snapshot,
    VerificationStatus,
)

_BOOL_OPS = BOOLEAN_OPERATORS
_NUMERIC_OPS = NUMERIC_OPERATORS
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

    May carry an `observable` name for verdict synthesis when the rule has
    no declared requirement for the refused leaf (§8.3).
    """

    def __init__(self, observable: str | None = None) -> None:
        super().__init__()
        self.observable = observable


class _Manifest(NamedTuple):
    """What reading one rule's requires manifest produced (§7.1(a), §8.2)."""

    verdicts: tuple[RequirementVerdict, ...]
    validated: Mapping[str, Decimal]
    graded: Mapping[str, bool]
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
            rule.when, context, snapshot, requested_actions, manifest.validated, manifest.graded
        )
    except _CannotAssessSafely as e:
        verdicts = manifest.verdicts
        if e.observable is not None and not any(v.observable == e.observable for v in verdicts):
            # Synthesize a verdict for the refused observable (§8.3)
            synthesized = _verdict(
                e.observable,
                RequirementVerdictValue.unusable,
                RequirementReason.no_result,
                None,
            )
            verdicts = (synthesized, *verdicts)
        return _indeterminate(rule, verdicts, pins)
    if not matched:
        return _record(
            rule, Outcome.not_triggered, rule.severity, None, None, manifest.verdicts, pins
        )
    if graded:
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
    included = all(_decide(p, context, snapshot, (), {}, {})[0] for p in rule.scope.include)
    excluded = any(_decide(p, context, snapshot, (), {}, {})[0] for p in rule.scope.exclude)
    return included and not excluded


def _decide(
    node: Expression,
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
    validated: Mapping[str, Decimal],
    graded: Mapping[str, bool],
    *,
    under_negation: bool = False,
) -> tuple[bool, bool]:
    """Evaluate one expression node to (matched, contributed evidence grade)."""
    if node.op in _BOOL_OPS:
        return _decide_boolean(
            node,
            context,
            snapshot,
            requested_actions,
            validated,
            graded,
            under_negation=under_negation,
        )
    if node.op in _NUMERIC_OPS:
        return _compare(node, context, snapshot, validated, graded, under_negation=under_negation)
    if node.op is Operator.drug_active:
        return _drug_active(node.ingredient_id, snapshot), False
    if node.op is Operator.drug_requested:
        return _drug_requested(node.ingredient_id, requested_actions), False
    if node.op is Operator.allergy:
        return _allergy(node, snapshot)
    if node.op is Operator.condition:
        return node.concept in snapshot.conditions, False
    if node.op is Operator.age:
        return _age_within(node, snapshot), False
    raise NotImplementedError(f"no evaluation rule for `{node.op}`")


def _decide_boolean(
    node: Expression,
    context: EvaluationContext,
    snapshot: Snapshot,
    requested_actions: tuple[RequestedAction, ...],
    validated: Mapping[str, Decimal],
    graded: Mapping[str, bool],
    *,
    under_negation: bool = False,
) -> tuple[bool, bool]:
    if node.op is Operator.NOT:
        # A graded leaf is graded only alongside a True match; negated, it
        # contributed nothing to any finding. Under negation, a silent-unusable
        # fact cannot manufacture a positive finding (§8.3, A8).
        only = _decide(
            node.children[0],
            context,
            snapshot,
            requested_actions,
            validated,
            graded,
            under_negation=True,
        )
        return not only[0], False
    outcomes = [
        _decide(
            child,
            context,
            snapshot,
            requested_actions,
            validated,
            graded,
            under_negation=under_negation,
        )
        for child in node.children
    ]
    if node.op is Operator.all:
        matched = all(decision for decision, _ in outcomes)
    else:
        matched = any(decision for decision, _ in outcomes)
    return matched, matched and any(g for d, g in outcomes if d)


def _compare(
    node: Expression,
    context: EvaluationContext,
    snapshot: Snapshot,
    validated: Mapping[str, Decimal],
    graded: Mapping[str, bool],
    *,
    under_negation: bool = False,
) -> tuple[bool, bool]:
    fact = node.fact
    assert fact is not None  # a numeric leaf always names its fact (load-time, §7.1)
    observed = validated.get(fact)
    if observed is None:
        # Silent-unusable: the leaf proceeds without the fact, never against raw data.
        # But under negation, a missing fact cannot manufacture a positive (§8.3, A8).
        if under_negation:
            raise _CannotAssessSafely(fact)
        return False, False
    if node.literal is not None:
        return _COMPARATORS[node.op](observed, node.literal), graded.get(fact, False)
    ref = node.threshold_ref
    assert ref is not None  # §4.3.1: exactly one comparison source, validated at load
    target = context.resolve_threshold(snapshot, fact, ref)
    return _COMPARATORS[node.op](observed, target.value), graded.get(fact, False)


def _drug_active(ingredient_id: str | None, snapshot: Snapshot) -> bool:
    # Known-present: any mapped entry for this ingredient means the drug is active
    if any(
        e.ingredient_id == ingredient_id and e.mapping_status is MappingStatus.mapped
        for e in snapshot.medications
    ):
        return True
    # Cannot assert absence if there are unresolved entries for this ingredient
    if any(
        e.ingredient_id == ingredient_id and e.mapping_status is not MappingStatus.mapped
        for e in snapshot.medications
    ):
        raise _CannotAssessSafely(ingredient_id)
    # No entries for this ingredient at all
    return False


def _drug_requested(
    ingredient_id: str | None, requested_actions: tuple[RequestedAction, ...]
) -> bool:
    return any(
        action.subject == ingredient_id and action.kind in _IN_PLAY for action in requested_actions
    )


def _allergy(node: Expression, snapshot: Snapshot) -> tuple[bool, bool]:
    if snapshot.allergy_status is AllergyStatus.not_asked:
        # §5.5 rule 2: unanswered is its own fact; "cleared" is never inferred.
        raise _CannotAssessSafely(node.ingredient_id)
    surfaced = [
        record
        for record in snapshot.allergies
        if record.culprit.ingredient_id == node.ingredient_id
        and record.verification_status not in _NEVER_SURFACING
    ]
    satisfying = [record for record in surfaced if _leaf_satisfied(record, node)]
    if satisfying:
        # §5.5 table: only a confirmed record with severity: severe answers cleanly.
        # All other satisfying records grade the finding.
        return True, any(
            record.verification_status is not VerificationStatus.confirmed
            or record.severity is not AllergySeverity.severe
            for record in satisfying
        )
    # Whatever surfaces but fails the leaf's filters is present data of lower grade.
    return bool(surfaced), bool(surfaced)


def _leaf_satisfied(record: AllergyRecord, leaf: Expression) -> bool:
    verified = (
        leaf.verification_status is None or record.verification_status is leaf.verification_status
    )
    severe = leaf.severity is None or record.severity is leaf.severity
    reaction = leaf.reaction_type is None or record.reaction_type is leaf.reaction_type
    return verified and severe and reaction


def _age_within(node: Expression, snapshot: Snapshot) -> bool:
    if node.minimum is not None and snapshot.age_years < node.minimum:
        return False
    return node.maximum is None or snapshot.age_years <= node.maximum


def _resolve_manifest(requirements: tuple[Requirement, ...], snapshot: Snapshot) -> _Manifest:
    verdicts: list[RequirementVerdict] = []
    validated: dict[str, Decimal] = {}
    graded: dict[str, bool] = {}
    degrades = False
    for requirement in requirements:
        verdict, observation = _resolve_requirement(requirement, snapshot)
        verdicts.append(verdict)
        if verdict.verdict is RequirementVerdictValue.usable:
            assert observation is not None  # usable means an observation was selected
            validated[requirement.observable] = _canonical_value(observation)
            graded[requirement.observable] = _evidence_is_graded(observation, requirement, snapshot)
        elif requirement.on_unusable is OnUnusable.indeterminate:
            degrades = True  # silent-unusable verdicts are recorded and proceed (§8.3)
    return _Manifest(tuple(verdicts), validated, graded, degrades)


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
    elapsed = snapshot.evaluated_at - latest.effective_time
    if elapsed < timedelta(0):
        # Future-dated observation: corrupt timestamp, refuse to use it.
        return _verdict(
            requirement.observable,
            RequirementVerdictValue.unusable,
            RequirementReason.no_result,
            None,
        ), latest
    age_days = elapsed.days
    reason = _first_failure(requirement, latest, elapsed)
    if reason is not None:
        return _verdict(
            requirement.observable, RequirementVerdictValue.unusable, reason, age_days
        ), latest
    # A usable verdict carries reason=met per §8.2's vocabulary.
    return _verdict(
        requirement.observable,
        RequirementVerdictValue.usable,
        RequirementReason.met,
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
    from noor.canon.delta import current_versions

    matches = [o for o in snapshot.observations if o.observable == observable]
    if not matches:
        return None
    # Use canon's current_versions to get the latest version per source record
    # (§5), then break cross-source ties by effective_time then source identity.
    current = current_versions(matches)
    return max(current, key=lambda o: (o.effective_time, o.source_system, o.source_identifier))


def _first_failure(
    requirement: Requirement, observation: CanonicalObservation, elapsed: timedelta
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
    if requirement.max_age_days is not None and elapsed > timedelta(days=requirement.max_age_days):
        return RequirementReason.stale  # exactly max_age_days stays usable
    # prefer_source is a preference, not a hard filter (§8.2, §8.3). A miss grades
    # the finding via _evidence_is_graded instead of making it indeterminate.
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
    prefer_source_miss = bool(
        requirement.prefer_source
        and observation.entry_mode not in requirement.prefer_source
    )
    return manager_report or noor_substitute or prefer_source_miss


def _canonical_value(observation: CanonicalObservation) -> Decimal:
    canonical = observation.canonical
    assert canonical is not None  # canon's invariant: accepted-family carries a value (§6.3)
    return canonical.value
