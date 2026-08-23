"""The §7.3 threshold, the §10.5 tenant profile and release, and the
EvaluationContext binding them to the observable registry.

The context is where rules, thresholds, the profile, and the registry meet, so
the load-time refusals land there: a rule never references an absent or
unpopulated threshold (§10.4 gate 1, §8.4 invariant 3), a threshold is stated in
its observable's canonical unit (§6.3), source families are never blended
(§10.4 gate 7), and a hard stop cannot be disabled by tenant policy (§10.5).
"""

from collections import Counter
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, Self

from pydantic import Field, PrivateAttr, model_validator

from noor.canon.models import NoorModel
from noor.canon.registry import ObservableRegistry, UnknownObservableError
from noor.engine.rules import Rule, Severity, _walk
from noor.engine.snapshot import Snapshot

ENGINE_VERSION = "0.1.0"


class ThresholdStatus(StrEnum):
    """A threshold's population state (SSOT §7.3).

    An `unpopulated` threshold is a placeholder no rule may reference;
    `clinician_approved` is `populated` plus a named approver and date.
    """

    unpopulated = "unpopulated"
    populated = "populated"
    clinician_approved = "clinician_approved"


class Citation(NoorModel):
    """Where a threshold's number comes from (SSOT §7.3).

    Uncited thresholds are a build failure, so every field is required.
    """

    organisation: str = Field(min_length=1)
    document: str = Field(min_length=1)
    version: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    evidence_grade: str = Field(min_length=1)
    review_date: date


class FallbackFrom(NoorModel):
    """Which other source families were tried before this one was pinned (§7.3)."""

    tried: tuple[str, ...] = ()
    reason: str = Field(min_length=1)


class Threshold(NoorModel):
    """One clinical decision boundary, cited and versioned (SSOT §7.3)."""

    ref: str = Field(min_length=1)
    value: Decimal
    unit: str = Field(min_length=1)
    source_family: str = Field(min_length=1)
    citation: Citation
    status: ThresholdStatus
    fallback_from: FallbackFrom | None = None
    approved_by: str | None = None
    approved_at: date | None = None

    @model_validator(mode="after")
    def _clinician_approval_names_its_approver(self) -> Self:
        if self.status is ThresholdStatus.clinician_approved and (
            self.approved_by is None or self.approved_at is None
        ):
            raise ValueError(
                "a clinician_approved threshold names its approver and the approval date (§7.3)"
            )
        return self


class RuleDisablement(NoorModel):
    """One governed disablement with its named accountability (SSOT §10.5).

    A disablement is never silent: it records why it was requested and who
    approved it, and evaluation records `suppressed_by_governed_policy` for the
    disabled rule rather than letting it disappear.
    """

    rule_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    requested_by: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)


class Profile(NoorModel):
    """The tenant profile: one pinned source family and the disablement set
    (SSOT §10.5)."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_family: str = Field(min_length=1)
    disablements: tuple[RuleDisablement, ...] = ()


class Pins(NoorModel):
    """The §8.2 pins copied onto every evaluation record.

    The snapshot id is unknown until a record is built, so it is the one
    optional field; the evaluator stamps it per record.
    """

    catalogue_release: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    source_family: str = Field(min_length=1)
    snapshot_id: str | None = None
    engine_version: str = Field(min_length=1)
    terminology_version: str = Field(min_length=1)


class CatalogueRelease(NoorModel):
    """An immutable release: rules, thresholds, and the tenant profile (§7.4).

    The release is where rules and the profile meet, so it refuses a disablement
    naming a hard stop — a stop_and_review rule cannot be disabled by tenant
    policy (§10.5).
    """

    release_id: str = Field(min_length=1)
    rules: tuple[Rule, ...] = ()
    thresholds: tuple[Threshold, ...] = ()
    profile: Profile

    @model_validator(mode="after")
    def _threshold_refs_are_unique(self) -> Self:
        counts = Counter(threshold.ref for threshold in self.thresholds)
        duplicates = sorted(ref for ref, count in counts.items() if count > 1)
        if duplicates:
            raise ValueError(
                f"threshold refs are a release's lookup keys and must be unique: {duplicates}"
            )
        return self

    @model_validator(mode="after")
    def _a_hard_stop_is_never_disabled(self) -> Self:
        severity_by_id = {rule.id: rule.severity for rule in self.rules}
        for disablement in self.profile.disablements:
            if severity_by_id.get(disablement.rule_id) is Severity.stop_and_review:
                raise ValueError(
                    f"`{disablement.rule_id}` is a stop_and_review rule — a hard stop "
                    f"cannot be disabled by tenant policy (§10.5)"
                )
        return self


class AmbiguousGoalOfCareError(Exception):
    """Two or more active goals of care apply to one patient and observable
    (SSOT §8.2).

    The engine refuses to choose between them — never by recency, never by
    narrowness — so the affected rule records `evaluation_failed` carrying this
    exception's type name only (§8.5). The message therefore names no patient,
    observable, or value.
    """

    def __init__(self) -> None:
        super().__init__(
            "two or more active goals of care apply to this patient and observable; "
            "resolve the conflict before the rule can produce a target (§8.2)"
        )


class ResolvedTarget(NoorModel):
    """The comparison target a rule resolves against (§7.3 precedence).

    `source` records which one won — a rule resolving against a goal records
    which one (§5.6 named accountability) — and `goal_reason` carries the
    goal's stated reason forward.
    """

    value: Decimal
    unit: str
    source: Literal["goal", "profile"]
    goal_reason: str | None = None


def _validate_pairing(
    thresholds: Mapping[str, Threshold], registry: ObservableRegistry, fact: str, ref: str
) -> None:
    """Check one (fact, ref) pairing from a numeric leaf against the release and
    the registry: present, populated, and stated in the canonical unit."""
    threshold = thresholds.get(ref)
    if threshold is None:
        raise ValueError(f"`{ref}` is referenced but absent from the release (§7.3)")
    if threshold.status is ThresholdStatus.unpopulated:
        raise ValueError(
            f"`{ref}` is unpopulated — no rule loads referencing an unpopulated "
            f"threshold (§10.4 gate 1, §8.4 invariant 3)"
        )
    try:
        entry = registry.entry(fact)
    except UnknownObservableError:
        raise ValueError(
            f"`{fact}` is not a governed observable — the registry declares what may "
            f"be compared (§6.6)"
        ) from None
    if threshold.unit != entry.canonical_ucum:
        raise ValueError(
            f"`{ref}` states {threshold.unit} but `{fact}` resolves to "
            f"{entry.canonical_ucum} — a threshold is stated in the canonical unit "
            f"(§6.3, §7.3)"
        )


class EvaluationContext(NoorModel):
    """The pinned evaluation world: release, registry, and pins (§7.3, §10.5).

    Construction walks every rule's `when` tree and refuses a threshold
    reference that is absent, unpopulated, or stated in a unit other than the
    observable's canonical one, so evaluation never meets an unusable target.
    Thresholds are keyed by ref for resolution.
    """

    release: CatalogueRelease
    registry: ObservableRegistry
    pins: Pins

    _thresholds_by_ref: Mapping[str, Threshold] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _every_threshold_belongs_to_the_pinned_source_family(self) -> Self:
        families = {threshold.source_family for threshold in self.release.thresholds}
        foreign = families - {self.release.profile.source_family}
        if foreign:
            raise ValueError(
                f"profile pins {self.release.profile.source_family} but thresholds also "
                f"resolve across {sorted(foreign)} — source families are never blended "
                f"(§7.3, §10.4 gate 7)"
            )
        return self

    @model_validator(mode="after")
    def _every_referenced_threshold_exists_populated_and_commensurable(self) -> Self:
        thresholds = {threshold.ref: threshold for threshold in self.release.thresholds}
        for rule in self.release.rules:
            for node in _walk(rule.when):
                # A threshold_ref rides only on numeric leaves, and a numeric leaf
                # always names its fact; every other node carries no pairing.
                if node.threshold_ref is None or node.fact is None:
                    continue
                _validate_pairing(thresholds, self.registry, node.fact, node.threshold_ref)
        self._thresholds_by_ref = MappingProxyType(thresholds)
        return self

    def resolve_threshold(self, snapshot: Snapshot, observable: str, ref: str) -> ResolvedTarget:
        """Resolve the comparison target for one observable (SSOT §7.3).

        Strict precedence: one active, unexpired goal of care for this patient on
        this observable wins; otherwise the profile's pinned threshold. Two
        active goals are a conflict the engine refuses (§8.2). A resolved goal
        whose unit differs from the threshold's is refused too: targets are
        compared in one unit and never rescaled (§6.1).
        """
        threshold = self._thresholds_by_ref[ref]
        matching = [
            goal
            for goal in snapshot.goals_of_care
            if goal.observable == observable
            and goal.effective_date <= snapshot.evaluated_at < goal.expires_at
        ]
        if len(matching) > 1:
            raise AmbiguousGoalOfCareError()
        if not matching:
            return ResolvedTarget(value=threshold.value, unit=threshold.unit, source="profile")
        goal = matching[0]
        if goal.unit != threshold.unit:
            raise ValueError(
                f"the goal target states {goal.unit} but the threshold it replaces states "
                f"{threshold.unit} — a target is never rescaled (§6.1)"
            )
        return ResolvedTarget(
            value=goal.value, unit=goal.unit, source="goal", goal_reason=goal.reason
        )
