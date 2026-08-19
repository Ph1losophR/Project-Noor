"""The canon pipeline (SSOT §6.1). Every observation captured during a visit
passes through here before it becomes a fact — there is no path around it
(§11.5 step 2). Pure: no I/O, no clock; time arrives on the captures.
"""

from collections.abc import Iterable

from noor.canon.delta import current_versions, review_delta
from noor.canon.models import (
    ACCEPTED_FAMILY,
    WITHDRAWN_SOURCE_STATUSES,
    AcceptedVia,
    CanonicalObservation,
    CanonicalQuantity,
    DeltaVerdict,
    MappingStatus,
    ObservationCapture,
    QualityState,
    QualityVerdict,
    RejectionReason,
    SuspicionReason,
    UnitResolution,
)
from noor.canon.parse import decimal_transposition_suspected, parse_value
from noor.canon.plausibility import EnvelopePosition, locate
from noor.canon.registry import ObservableEntry, ObservableRegistry
from noor.canon.units import resolve_unit, to_canonical


class AbsentObservationError(ValueError):
    """An absent_reason observation carries no value; there is nothing to
    canonicalise (§5). The store records it verbatim without a canon verdict."""


def _missing_required_fields(capture: ObservationCapture, entry: ObservableEntry) -> list[str]:
    missing: list[str] = []
    for field in entry.required_context:
        value = getattr(capture, field) if field == "setting" else getattr(capture.context, field)
        if value is None:
            missing.append(field)
    for field in entry.required_method:
        if getattr(capture.method, field) is None:
            missing.append(field)
    return missing


def _unusable_source(capture: ObservationCapture) -> list[RejectionReason]:
    """§5's two "this record cannot be used at all" conditions.

    Both are properties of the record rather than of the value, so they are
    decided before parsing and neither hides the other.
    """
    reasons: list[RejectionReason] = []
    if capture.mapping.status is not MappingStatus.mapped:
        reasons.append(RejectionReason.mapping_unusable)
    if capture.source_status in WITHDRAWN_SOURCE_STATUSES:
        reasons.append(RejectionReason.source_status_unusable)
    return reasons


def _unit_changed_from_prior(
    capture: ObservationCapture,
    priors: Iterable[CanonicalObservation],
) -> bool:
    """§6.1 layer 1: the unit changed from the patient's prior accepted record.

    The priors are already current versions (§5) — canonicalise deduplicated
    them once, before this layer ran.
    """
    if capture.as_reported.unit is None:
        return False
    candidates = [
        prior
        for prior in priors
        if prior.observable == capture.observable
        and prior.quality.state in ACCEPTED_FAMILY
        and prior.as_reported.unit is not None
        and prior.effective_time < capture.effective_time
    ]
    if not candidates:
        return False
    # Priors sharing an effective_time are broken by source, not by arrival order:
    # the verdict is written into a record that is never rewritten (§5), so it
    # cannot depend on what order a query happened to return.
    latest = max(
        candidates,
        key=lambda prior: (prior.effective_time, prior.source_system, prior.source_identifier),
    )
    return capture.as_reported.unit != latest.as_reported.unit


def canonicalise(
    capture: ObservationCapture,
    registry: ObservableRegistry,
    priors: Iterable[CanonicalObservation] = (),
) -> CanonicalObservation:
    """Run the three canon layers over one capture.

    `priors` are the patient's existing canonical observations; non-matching
    observables are ignored. The capture is never mutated (§6.1).
    """
    entry = registry.entry(capture.observable)

    if capture.absent_reason is not None:
        raise AbsentObservationError(
            f"{capture.observable}: absent_reason observations carry no value to canonicalise"
        )

    unusable = _unusable_source(capture)
    if unusable:
        # §6.3: both reasons here precede unit resolution, so the verdict reports no
        # resolution outcome rather than a guess — hence the call below, not above.
        quality = QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=None,
            rejection_reasons=tuple(unusable),
        )
        return CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)

    # Dedup once, on the normal path only: the priors are re-walked below — the
    # unit-change check, then review_delta — and a caller may pass a generator,
    # which would come back empty on the later walks. `review_delta` dedups
    # again inside, which is idempotent over the already-current list.
    known_priors = current_versions(priors)

    unit_resolution, resolved_unit = resolve_unit(
        capture.as_reported.unit, capture.source_code, entry
    )

    rejection_reasons: list[RejectionReason] = []
    suspicions: list[SuspicionReason] = []
    canonical: CanonicalQuantity | None = None
    delta: DeltaVerdict | None = None

    parsed = parse_value(capture.as_reported.value) if capture.as_reported.value else None
    if parsed is None:
        rejection_reasons.append(RejectionReason.parse_failure)

    if unit_resolution is UnitResolution.ambiguous:
        rejection_reasons.append(RejectionReason.unit_ambiguous)

    if _missing_required_fields(capture, entry):
        rejection_reasons.append(RejectionReason.missing_required_context)

    if parsed is not None and resolved_unit is not None:
        canonical = to_canonical(parsed, resolved_unit, entry)
        position = locate(canonical.value, entry)
        if position is EnvelopePosition.outside_physiologic:
            rejection_reasons.append(RejectionReason.outside_physiologic_envelope)
        elif position is EnvelopePosition.outside_operational:
            suspicions.append(SuspicionReason.outside_operational_envelope)
            if decimal_transposition_suspected(canonical.value, entry):
                suspicions.append(SuspicionReason.decimal_transposition_suspected)

    if not rejection_reasons and canonical is not None:
        if _unit_changed_from_prior(capture, known_priors):
            suspicions.append(SuspicionReason.unit_changed_from_prior)
        delta = review_delta(canonical.value, capture, known_priors, entry)
        if delta.suspicious:
            suspicions.append(SuspicionReason.delta_exceeded)

    if rejection_reasons:
        quality = QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=unit_resolution,
            rejection_reasons=tuple(rejection_reasons),
            suspicions=tuple(suspicions),
        )
    elif suspicions:
        quality = QualityVerdict(
            state=QualityState.needs_repeat_or_verification,
            unit_resolution=unit_resolution,
            suspicions=tuple(suspicions),
            delta=delta,
        )
    else:
        quality = QualityVerdict(
            state=QualityState.accepted,
            unit_resolution=unit_resolution,
            accepted_via=AcceptedVia.unremarkable,
            delta=delta,
        )
    return CanonicalObservation(**capture.model_dump(), canonical=canonical, quality=quality)
