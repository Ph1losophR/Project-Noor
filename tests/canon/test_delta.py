"""Layer 3 of canon: delta review compares like with like only (SSOT §6.1),
and a suspicious delta never mutates anything. Where nothing was comparable the
verdict says so with a reason — §11.9 counts delta checks, so "not compared"
has to be a recorded fact."""

from datetime import timedelta
from decimal import Decimal

from noor.canon.delta import review_delta
from noor.canon.models import (
    Arm,
    CaptureContext,
    CuffSize,
    MethodContext,
    NotComparableReason,
    Posture,
    QualityState,
    Setting,
)
from tests.conftest import T0, make_canonical, make_capture


def glucose_prior(value: str, *, hours_before: float = 1, device: str | None = "accu-chek", **kw):
    return make_canonical(
        value=value,
        effective_time=T0 - timedelta(hours=hours_before),
        method=MethodContext(device_class=device),
        source_identifier=f"PRIOR-{value}-{hours_before}h",
        **kw,
    )


def glucose_capture(value: str, *, device: str | None = "accu-chek", **kw):
    return make_capture(
        value=value,
        effective_time=T0,
        method=MethodContext(device_class=device),
        source_identifier="CURRENT",
        **kw,
    )


def test_a_comparable_prior_produces_a_recorded_delta(registry):
    # Arrange — glucose: max 8.0 mmol/L within 4h, device class compared
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("6.0")

    # Act
    delta = review_delta(Decimal("6.0"), capture, [prior], entry)

    # Assert
    assert delta.comparable is True
    assert delta.compared_to == prior.source_identifier
    assert delta.change == Decimal("0.5")
    assert delta.suspicious is False


def test_a_delta_beyond_the_registry_bound_is_suspicious(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert
    assert delta.comparable is True
    assert delta.suspicious is True


def test_a_delta_exactly_at_the_registry_bound_is_not_suspicious(registry):
    # Arrange — boundary row: at, not over
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("13.5")

    # Act
    delta = review_delta(Decimal("13.5"), capture, [prior], entry)

    # Assert
    assert delta.change == Decimal("8.0")
    assert delta.suspicious is False


def test_a_superseded_prior_is_not_a_baseline(registry):
    # Arrange — §5: a correction supersedes what it corrects. The source sent
    # 5.5, then corrected the same record to 13.9. Only v2 is the baseline;
    # comparing against v1 would flag a +8.5 jump the source never reported.
    entry = registry.entry("glucose")
    superseded = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
        source_version=1,
    )
    correction = make_canonical(
        value="13.9",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
        source_version=2,
    )
    capture = glucose_capture("14.0")

    # Act — oldest version first, so the reducer has to replace, not just keep
    delta = review_delta(Decimal("14.0"), capture, [superseded, correction], entry)

    # Assert
    assert delta.compared_to == "PRIOR-1"
    assert delta.change == Decimal("0.1")
    assert delta.suspicious is False


def test_a_superseded_prior_is_not_a_baseline_whichever_order_it_arrives_in(registry):
    # Arrange — the same two versions, newest first: the reducer must keep what
    # it has rather than let v1 overwrite v2. Sources do not promise an order.
    entry = registry.entry("glucose")
    versions = [
        make_canonical(
            value=value,
            effective_time=T0 - timedelta(hours=1),
            method=MethodContext(device_class="accu-chek"),
            source_identifier="PRIOR-1",
            source_version=version,
        )
        for value, version in (("13.9", 2), ("5.5", 1))
    ]
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, versions, entry)

    # Assert
    assert delta.change == Decimal("0.1")
    assert delta.suspicious is False


def test_two_records_at_one_version_pick_the_same_baseline_either_way(registry):
    # Arrange — a source that sends two different values under one identifier at
    # one version has a bug, but §5 writes the verdict into a record that is never
    # rewritten: 1.0 and 9.0 disagree about whether the new 9.5 is a +8.5 jump, and
    # which of them wins cannot depend on the order a query returned them in.
    entry = registry.entry("glucose")
    duplicates = [
        make_canonical(
            value=value,
            effective_time=T0 - timedelta(hours=1),
            method=MethodContext(device_class="accu-chek"),
            source_identifier="PRIOR-1",
            source_version=1,
        )
        for value in ("1.0", "9.0")
    ]
    capture = glucose_capture("9.5")

    # Act
    forwards = review_delta(Decimal("9.5"), capture, duplicates, entry)
    backwards = review_delta(Decimal("9.5"), capture, list(reversed(duplicates)), entry)

    # Assert — the version tie breaks on content, so the same record wins both times
    assert forwards == backwards
    assert forwards.change == Decimal("0.5")
    assert forwards.suspicious is False


def test_a_prior_from_a_different_device_class_is_not_comparable(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", device="cgm-different-class")
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert — a prior of this observable exists, none like with like
    assert delta.comparable is False
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior
    assert delta.change is None


def test_a_prior_from_another_device_class_is_comparable_when_the_policy_says_so(registry):
    # Arrange — hba1c_ngsp sets compare_device_class false: a lab analyser and a
    # point-of-care analyser both report the same 90 days of glycation, so
    # refusing to compare them would discard the only baseline most patients have
    entry = registry.entry("hba1c_ngsp")
    prior = make_canonical(
        observable="hba1c_ngsp",
        value="7.4",
        unit="%",
        effective_time=T0 - timedelta(days=30),
        method=MethodContext(device_class="lab-analyser"),
        source_identifier="PRIOR-A1C",
    )
    capture = make_capture(
        observable="hba1c_ngsp",
        value="8.0",
        unit="%",
        effective_time=T0,
        method=MethodContext(device_class="poct-analyser"),
        source_identifier="CURRENT",
    )

    # Act
    delta = review_delta(Decimal("8.0"), capture, [prior], entry)

    # Assert — max_abs_change 2.0 %: +0.6 over a month is an ordinary trajectory
    assert delta.comparable is True
    assert delta.change == Decimal("0.6")
    assert delta.suspicious is False


def test_a_prior_with_no_recorded_device_class_is_not_comparable(registry):
    # Arrange — §5's own observation carries device_class: null. Glucose compares
    # device class, and an unrecorded device cannot be claimed to match this one.
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", device=None)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_capture_with_no_recorded_device_class_has_no_comparable_prior(registry):
    # Arrange — the same gap on the incoming side
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("14.0", device=None)

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_prior_in_a_stale_canonical_unit_is_not_comparable(registry):
    # Arrange — glucose canonicalises to mmol/L, so a stored prior carrying
    # mg/dL means the registry's canonical unit changed under stored data.
    # Subtracting 99 mg/dL from 14 mmol/L reports an -85 fall that never
    # happened — the exact arithmetic layer 3 exists to refuse.
    entry = registry.entry("glucose")
    prior = glucose_prior("99", unit="mg/dL", canonical_ucum="mg/dL")
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_prior_older_than_the_policy_window_is_not_comparable(registry):
    # Arrange — glucose window is 4h
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", hours_before=5)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_flagged_prior_is_not_a_baseline(registry):
    # Arrange — a needs_repeat observation proves nothing about the next one
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", state=QualityState.needs_repeat_or_verification)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_rejected_prior_is_not_a_baseline(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", state=QualityState.rejected)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_later_observation_is_not_a_prior(registry):
    # Arrange — results land out of order; "prior" means earlier effective_time
    entry = registry.entry("glucose")
    later = glucose_prior("5.5", hours_before=-1)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [later], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_prior_of_another_observable_is_ignored(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = make_canonical(observable="pulse", value="80", unit="/min")
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert — nothing of this observable was on record at all
    assert delta.comparable is False
    assert delta.not_comparable_reason is NotComparableReason.no_prior_observation


def test_the_most_recent_comparable_prior_wins(registry):
    # Arrange
    entry = registry.entry("glucose")
    older = glucose_prior("4.0", hours_before=3)
    newer = glucose_prior("5.5", hours_before=1)
    capture = glucose_capture("6.0")

    # Act
    delta = review_delta(Decimal("6.0"), capture, [older, newer], entry)

    # Assert
    assert delta.compared_to == newer.source_identifier


def test_two_priors_at_the_same_effective_time_pick_the_same_baseline_either_way(registry):
    # Arrange — a meter sync and a staff transcription land on one effective_time.
    # 1.0 and 9.0 disagree about whether the new 9.5 is a +8.5 jump, and the
    # verdict is written into a record that is never rewritten (§5), so it cannot
    # depend on the order a query happened to return.
    entry = registry.entry("glucose")
    meter_sync = glucose_prior("1.0")
    transcribed = glucose_prior("9.0")
    capture = glucose_capture("9.5")

    # Act
    forwards = review_delta(Decimal("9.5"), capture, [meter_sync, transcribed], entry)
    backwards = review_delta(Decimal("9.5"), capture, [transcribed, meter_sync], entry)

    # Assert — the tie breaks on source, so the same prior wins both times
    assert forwards == backwards
    assert forwards.compared_to == "PRIOR-9.0-1h"
    assert forwards.change == Decimal("0.5")
    assert forwards.suspicious is False


def bp(observable: str, value: str, *, context: CaptureContext, setting: Setting, **kw):
    defaults = {
        "observable": observable,
        "value": value,
        "unit": "mm[Hg]",
        "setting": setting,
        "context": context,
        "method": MethodContext(device_class="home-bp-monitor"),
    }
    defaults.update(kw)
    return make_canonical(**defaults)


def test_a_bp_delta_requires_matching_context(registry):
    # Arrange — §6.6: BP is meaningless without posture, arm, cuff; never pooled
    entry = registry.entry("systolic_bp")
    sitting = CaptureContext(
        posture=Posture.sitting,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=300,
        reading_ordinal=1,
        is_average=False,
    )
    standing = CaptureContext(
        posture=Posture.standing,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=60,
        reading_ordinal=1,
        is_average=False,
    )
    prior = bp(
        "systolic_bp",
        "160",
        context=sitting,
        setting=Setting.home,
        effective_time=T0 - timedelta(hours=2),
    )
    capture = make_capture(
        observable="systolic_bp",
        value="118",
        unit="mm[Hg]",
        setting=Setting.home,
        context=standing,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act / Assert — sitting vs standing is not like with like
    delta = review_delta(Decimal("118"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_bp_delta_with_matching_context_is_recorded(registry):
    # Arrange
    entry = registry.entry("systolic_bp")
    context = CaptureContext(
        posture=Posture.sitting,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=300,
        reading_ordinal=1,
        is_average=False,
    )
    prior = bp(
        "systolic_bp",
        "160",
        context=context,
        setting=Setting.home,
        effective_time=T0 - timedelta(hours=2),
    )
    capture = make_capture(
        observable="systolic_bp",
        value="118",
        unit="mm[Hg]",
        setting=Setting.home,
        context=context,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act
    delta = review_delta(Decimal("118"), capture, [prior], entry)

    # Assert — |-42| > 40: suspicious
    assert delta.comparable is True
    assert delta.change == Decimal("-42")
    assert delta.suspicious is True


def test_a_prior_with_incomplete_context_is_not_comparable(registry):
    # Arrange — cuff size unknown on the prior: cannot claim like-with-like
    entry = registry.entry("systolic_bp")
    incomplete = CaptureContext(
        posture=Posture.sitting,
        arm=Arm.left,
        cuff_size=None,
        rest_duration_seconds=300,
        reading_ordinal=1,
        is_average=False,
    )
    complete = CaptureContext(
        posture=Posture.sitting,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=300,
        reading_ordinal=1,
        is_average=False,
    )
    prior = bp(
        "systolic_bp",
        "160",
        context=incomplete,
        setting=Setting.home,
        effective_time=T0 - timedelta(hours=2),
    )
    capture = make_capture(
        observable="systolic_bp",
        value="118",
        unit="mm[Hg]",
        setting=Setting.home,
        context=complete,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act / Assert
    delta = review_delta(Decimal("118"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_bp_pair_sharing_one_source_identifier_keeps_both_baselines(registry):
    # Arrange — one FHIR BP resource carries systolic and diastolic components,
    # which §6.6 splits into two observables that inherit the resource's single
    # identifier. Reducing versions on (system, identifier) alone treated the
    # second component as a correction of the first and dropped it, so a
    # +52 mmHg systolic jump reported "no prior observation" on one list order
    # and a suspicious delta on the other.
    entry = registry.entry("systolic_bp")
    context = CaptureContext(
        posture=Posture.sitting,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=300,
        reading_ordinal=1,
        is_average=False,
    )
    components = [
        bp(
            observable,
            value,
            context=context,
            setting=Setting.home,
            effective_time=T0 - timedelta(hours=2),
            source_identifier="OBS-500",
        )
        for observable, value in (("systolic_bp", "118"), ("diastolic_bp", "76"))
    ]
    capture = make_capture(
        observable="systolic_bp",
        value="170",
        unit="mm[Hg]",
        setting=Setting.home,
        context=context,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act / Assert — the systolic baseline survives either arrival order
    for priors in (components, list(reversed(components))):
        delta = review_delta(Decimal("170"), capture, priors, entry)
        assert delta.compared_to == "OBS-500"
        assert delta.change == Decimal("52")
        assert delta.suspicious is True


def test_delta_review_never_mutates_either_observation(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("14.0")

    # Act
    review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert — the testing standard: assert the stored value is unchanged,
    # not merely that a flag was set
    assert prior.as_reported.value == "5.5"
    assert prior.canonical is not None and prior.canonical.value == Decimal("5.5")
    assert capture.as_reported.value == "14.0"
