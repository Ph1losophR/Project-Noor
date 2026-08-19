"""Layer 3 of canon: delta review (SSOT §6.1 layer 3).

Compares like with like only: same observable, same canonical unit, the
registry's named context fields equal, device class equal, and the prior inside
the policy's window. `to_canonical` (§6.6) writes every canonical value in the
entry's declared unit, so a prior carrying a different one means the registry
changed under stored data — history, not a baseline. Only accepted-quality
priors are baselines, and only current versions — §5 versions a source record so
a correction supersedes what it corrects. A suspicious delta is a review
trigger, never a correction: nothing here mutates a value.
"""

from collections.abc import Iterable
from datetime import timedelta
from decimal import Decimal

from noor.canon.models import (
    ACCEPTED_FAMILY,
    CanonicalObservation,
    DeltaVerdict,
    NotComparableReason,
    ObservationCapture,
)
from noor.canon.registry import ObservableEntry


def current_versions(
    priors: Iterable[CanonicalObservation],
) -> list[CanonicalObservation]:
    """The latest version of each source record (SSOT §5).

    A source may correct a record it already sent; the correction carries the
    same `source_identifier` and a higher `source_version`. Only the current
    version is a fact — the superseded one is history, and comparing against it
    would report a change the source never made.

    The key carries the observable too: one source record can hold two
    observables — FHIR sends blood pressure as a single resource with systolic
    and diastolic components, which §6.6 splits — so an identifier shared
    between them is not a version of anything, and dropping one would discard a
    baseline that exists.
    """
    latest: dict[tuple[str, str, str], CanonicalObservation] = {}
    for prior in priors:
        key = (prior.source_system, prior.source_identifier, prior.observable)
        seen = latest.get(key)
        if seen is None or prior.source_version > seen.source_version:
            latest[key] = prior
    return list(latest.values())


def is_comparable(
    prior: CanonicalObservation,
    capture: ObservationCapture,
    entry: ObservableEntry,
) -> bool:
    """True when `prior` may serve as the delta baseline for `capture`."""
    if prior.observable != capture.observable:
        return False
    if prior.quality.state not in ACCEPTED_FAMILY:
        return False
    # Past the state gate the canonical value exists — CanonicalObservation refuses
    # to hold an accepted state without one (models.py) — so a None here is a broken
    # invariant to raise on, not a prior to quietly drop.
    assert prior.canonical is not None
    if prior.canonical.ucum != entry.canonical_ucum:
        return False
    if not prior.effective_time < capture.effective_time:
        return False
    window = timedelta(hours=entry.delta_policy.within_hours)
    if capture.effective_time - prior.effective_time > window:
        return False
    if entry.delta_policy.compare_device_class:
        if prior.method.device_class is None or capture.method.device_class is None:
            return False
        if prior.method.device_class != capture.method.device_class:
            return False
    for field in entry.delta_policy.compare_context:
        prior_value = getattr(prior, field) if field == "setting" else getattr(prior.context, field)
        new_value = (
            getattr(capture, field) if field == "setting" else getattr(capture.context, field)
        )
        if prior_value is None or new_value is None or prior_value != new_value:
            return False
    return True


def review_delta(
    value: Decimal,
    capture: ObservationCapture,
    priors: Iterable[CanonicalObservation],
    entry: ObservableEntry,
) -> DeltaVerdict:
    """Compare a canonical value against the most recent comparable accepted prior.

    Always returns a verdict. When nothing was comparable the verdict says so
    and why — "not compared" is a fact of record, not a silent pass (§5), and
    §11.9 counts delta checks.
    """
    known = current_versions(priors)
    comparable = [prior for prior in known if is_comparable(prior, capture, entry)]
    if not comparable:
        had_any = any(prior.observable == capture.observable for prior in known)
        return DeltaVerdict(
            comparable=False,
            not_comparable_reason=(
                NotComparableReason.no_comparable_prior
                if had_any
                else NotComparableReason.no_prior_observation
            ),
        )
    # Priors sharing an effective_time are broken by source, not by arrival order:
    # the verdict is written into a record that is never rewritten (§5), so it
    # cannot depend on what order a query happened to return.
    latest = max(
        comparable,
        key=lambda prior: (prior.effective_time, prior.source_system, prior.source_identifier),
    )
    # Same invariant as in is_comparable, re-read in this scope.
    assert latest.canonical is not None
    change = value - latest.canonical.value
    return DeltaVerdict(
        comparable=True,
        compared_to=latest.source_identifier,
        change=change,
        suspicious=abs(change) > entry.delta_policy.max_abs_change,
    )
