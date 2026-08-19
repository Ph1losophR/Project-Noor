"""The registry validates itself at load (SSOT §6.4, §6.6)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.canon.registry import (
    Conversion,
    DeltaPolicy,
    Envelope,
    ObservableEntry,
    ObservableRegistry,
    UnknownObservableError,
)
from tests.conftest import make_entry


def test_a_well_formed_entry_validates():
    # Arrange / Act
    entry = make_entry()

    # Assert
    assert entry.observable == "test_obs"
    assert entry.canonical_ucum == "mmol/L"


def test_the_canonical_unit_must_be_an_accepted_unit():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(canonical_ucum="mg/dL", accepted_units=["mmol/L"])


def test_the_operational_envelope_must_sit_inside_the_physiologic_envelope():
    # Arrange — operational low below the physiologic floor
    bad_operational = Envelope(low=Decimal("1"), high=Decimal("8"), version="t1")

    # Act / Assert — the two boundary types are versioned independently but
    # nested (§6.4): an operational bound outside "cannot be generated" is a
    # registry authoring error, caught at load
    with pytest.raises(ValidationError):
        make_entry(operational=bad_operational)


def test_an_envelope_must_be_ordered():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Envelope(low=Decimal("8"), high=Decimal("2"), version="t1")


def test_the_two_envelope_types_are_versioned_independently():
    # Arrange — §6.4: stored and versioned independently, and neither is a
    # treatment threshold. Nothing derives one version from the other.
    entry = make_entry(
        physiologic=Envelope(low=Decimal("2"), high=Decimal("10"), version="physio-2026-01"),
        operational=Envelope(low=Decimal("4"), high=Decimal("8"), version="oper-2026-07"),
    )

    # Assert
    assert entry.physiologic.version == "physio-2026-01"
    assert entry.operational.version == "oper-2026-07"


def test_the_registry_declares_no_treatment_threshold_field():
    # Arrange / Act — the other half of the boundary-separation proof (§6.4,
    # docs/testing-standards.md): the data-validity schema has nowhere to put a
    # clinical decision boundary, so no code can read one from here
    fields = set(ObservableEntry.model_fields)

    # Assert
    assert not {name for name in fields if "threshold" in name or "target" in name}


def test_a_conversion_must_convert_from_an_accepted_non_canonical_unit():
    # Arrange
    bad = Conversion(
        from_unit="mmol/L",
        precision=2,
        tolerance=Decimal("0.5"),
        canonical_tolerance=Decimal("0.01"),
        version="t1",
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        make_entry(conversions=[bad])


def test_a_conversion_multiplier_must_be_positive():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Conversion(
            from_unit="mg/dL",
            multiply=Decimal("0"),
            precision=2,
            tolerance=Decimal("0.5"),
            canonical_tolerance=Decimal("0.01"),
            version="t1",
        )


def test_a_code_unit_map_entry_must_name_an_accepted_unit():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(code_unit_map={"http://loinc.org|9999-9": "furlong"})


@pytest.mark.parametrize(
    "key",
    ["4548-4", "|4548-4", "http://loinc.org|", "http://loinc.org|4548-4|extra"],
)
def test_a_code_unit_map_key_must_be_a_nonempty_system_pipe_code_pair(key):
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(code_unit_map={key: "%"})


def test_required_context_must_name_known_fields():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(required_context=["mood"])


def test_required_method_must_name_known_fields():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(required_method=["reagent_lot"])


def test_a_delta_policy_must_not_name_unknown_context_fields():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        DeltaPolicy(max_abs_change=Decimal("1"), within_hours=1, compare_context=["mood"])


def test_registry_keys_must_match_their_entries():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        ObservableRegistry(entries={"wrong_key": make_entry(observable="test_obs")})


def test_registry_lookup_raises_unknown_observable_for_a_missing_id():
    # Arrange
    registry = ObservableRegistry(entries={"test_obs": make_entry()})

    # Act / Assert
    with pytest.raises(UnknownObservableError):
        registry.entry("tsh")
