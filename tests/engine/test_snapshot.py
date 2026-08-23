"""The §4.2 closed snapshot contract, with the §5.5 allergy record and §5.6 goals.

The snapshot is the evaluator's entire world (§8.1): `app` builds it and the
seam's data half keeps it closed, so every test here is about what the contract
admits and what it refuses.
"""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.canon.models import (
    MappingStatus,
    QualityState,
)
from noor.engine.snapshot import (
    ActionKind,
    AllergySeverity,
    AllergyStatus,
    CulpritSubstance,
    EvidenceSource,
    ReactionType,
    RequestedAction,
    SnapshotMedication,
    VerificationStatus,
)
from tests.conftest import T0, make_allergy, make_canonical, make_goal, make_snapshot


def test_a_well_formed_snapshot_is_accepted():
    # Arrange
    observation = make_canonical()
    medication = SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped)

    # Act
    snapshot = make_snapshot(
        observations=[observation],
        medications=[medication],
        allergies=[make_allergy()],
        conditions=frozenset({"cognitive_impairment"}),
        goals_of_care=[make_goal()],
    )

    # Assert
    assert snapshot.snapshot_id == "SNAP-1"
    assert snapshot.patient_id == "PAT-1"
    assert snapshot.age_years == 67
    assert snapshot.observations == (observation,)
    assert snapshot.medications == (medication,)
    assert len(snapshot.allergies) == 1
    assert snapshot.conditions == frozenset({"cognitive_impairment"})
    assert len(snapshot.goals_of_care) == 1


def test_a_naive_evaluated_at_is_refused():
    # Arrange / Act / Assert — time enters as data, and data carries its zone (§4.2)
    with pytest.raises(ValidationError):
        make_snapshot(evaluated_at=datetime(2026, 6, 12, 8, 20))


def test_evaluated_at_is_normalised_to_utc():
    # Arrange / Act
    snapshot = make_snapshot(
        evaluated_at=datetime(2026, 6, 12, 11, 20, tzinfo=timezone(timedelta(hours=3)))
    )

    # Assert — 11:20 at +03:00 is 08:20 UTC
    assert snapshot.evaluated_at.tzinfo is UTC
    assert snapshot.evaluated_at.hour == 8
    assert snapshot.evaluated_at.minute == 20


def test_rejected_observations_are_retained_in_the_snapshot():
    # Arrange — canon's verdict travels with the observation; dropping it would
    # hide a data-quality finding from the card (§8.3)
    rejected = make_canonical(state=QualityState.rejected)

    # Act
    snapshot = make_snapshot(observations=[rejected])

    # Assert
    assert snapshot.observations == (rejected,)
    assert snapshot.observations[0].quality.state is QualityState.rejected


def test_an_ambiguously_mapped_medication_is_accepted_into_the_snapshot():
    # Arrange — the requested-action projection names subjects; matching one
    # against an unresolved list entry is a finding, not a construction refusal
    medication = SnapshotMedication(
        ingredient_id="glipizide", mapping_status=MappingStatus.ambiguous
    )

    # Act
    snapshot = make_snapshot(medications=[medication])

    # Assert
    assert snapshot.medications == (medication,)
    assert snapshot.medications[0].mapping_status is MappingStatus.ambiguous


def test_not_asked_is_a_distinct_fact_from_an_empty_allergy_list():
    # Arrange — §5.5 rule 2: an unasked patient and a cleared patient are
    # opposite facts, even when neither list holds a record
    not_asked = make_snapshot(allergy_status=AllergyStatus.not_asked)
    cleared = make_snapshot(allergy_status=AllergyStatus.no_known_allergy)

    # Act / Assert
    assert not_asked.allergies == ()
    assert cleared.allergies == ()
    assert not_asked.allergy_status is AllergyStatus.not_asked
    assert cleared.allergy_status is AllergyStatus.no_known_allergy


def test_allergy_status_no_known_allergy_contradicts_non_empty_allergies():
    # Arrange — §5.5 rule 2: no_known_allergy and recorded allergies are opposite facts
    allergy = make_allergy(culprit=CulpritSubstance(ingredient_id="penicillin"))

    # Act / Assert
    with pytest.raises(ValidationError, match="no_known_allergy contradicts non-empty allergies"):
        make_snapshot(allergies=(allergy,), allergy_status=AllergyStatus.no_known_allergy)


def test_allergy_status_recorded_requires_at_least_one_allergy():
    # Arrange — §5.5 rule 2: recorded status requires at least one allergy record
    # Act / Assert
    with pytest.raises(ValidationError, match="recorded requires at least one allergy record"):
        make_snapshot(allergies=(), allergy_status=AllergyStatus.recorded)


def test_the_snapshot_refuses_undeclared_fields():
    # Arrange / Act / Assert — §4.2: a computed clinical value cannot enter by
    # inventing a key
    with pytest.raises(ValidationError):
        make_snapshot(encounter_state="active")


def test_a_well_formed_allergy_record_is_accepted():
    # Arrange / Act
    allergy = make_allergy()

    # Assert
    assert allergy.culprit.ingredient_id == "amoxicillin"
    assert allergy.reaction == ("anaphylaxis",)
    assert allergy.reaction_type is ReactionType.immediate_hypersensitivity
    assert allergy.severity is AllergySeverity.severe
    assert allergy.onset.date == "2019-03"
    assert allergy.verification_status is VerificationStatus.confirmed
    assert allergy.evidence_source is EvidenceSource.clinical_record
    assert allergy.recorder.person_id == "DR-7"
    assert allergy.recorded_at == T0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("reaction_type", "anaphylactic", id="reaction_type"),
        pytest.param("severity", "fatal", id="severity"),
        pytest.param("verification_status", "probably_real", id="verification_status"),
        pytest.param("evidence_source", "rumour", id="evidence_source"),
    ],
)
def test_an_allergy_enum_rejects_an_unknown_member(field, value):
    # Arrange
    overrides = {field: value}

    # Act / Assert — each enum is closed (§5.5); a member outside it is refused
    with pytest.raises(ValidationError):
        make_allergy(**overrides)


def test_allergy_status_rejects_an_unknown_member():
    # Arrange / Act / Assert — §5.5 rule 2: three states exist, nothing between them
    with pytest.raises(ValidationError):
        make_snapshot(allergy_status="maybe_asked")


def test_a_well_formed_goal_of_care_is_accepted():
    # Arrange / Act
    goal = make_goal()

    # Assert — §5.6: value, unit, op, reason, clinician, and the window; no status
    assert goal.observable == "systolic_bp"
    assert goal.value == Decimal("150")
    assert goal.unit == "mmHg"
    assert goal.op == "lt"
    assert goal.reason == "High orthostatic fall risk"
    assert goal.clinician_id == "DR-7"
    assert goal.effective_date == T0


@pytest.mark.parametrize(
    "expires_at",
    [
        pytest.param(T0, id="expires_at_equals_effective_date"),
        pytest.param(T0 - timedelta(days=1), id="expires_at_before_effective_date"),
    ],
)
def test_a_goal_whose_window_could_never_be_active_is_refused(expires_at):
    # Arrange / Act / Assert — §5.6: active means [effective_date, expires_at),
    # so an empty or inverted window names no active day at all
    with pytest.raises(ValidationError):
        make_goal(expires_at=expires_at)


def test_requested_action_has_exactly_kind_and_subject():
    # Arrange / Act / Assert — §11.6: this is the two-field projection of a
    # planned action; detail and state stay in the encounter
    assert set(RequestedAction.model_fields) == {"kind", "subject"}


def test_a_valid_action_kind_is_accepted():
    # Arrange / Act
    action = RequestedAction(kind=ActionKind.medication_stop, subject="metformin")

    # Assert
    assert action.kind is ActionKind.medication_stop
    assert action.subject == "metformin"


def test_an_invalid_action_kind_is_refused():
    # Arrange / Act / Assert — §11.6's kind enum is closed
    with pytest.raises(ValidationError):
        RequestedAction(kind="phone_the_patient", subject="metformin")
