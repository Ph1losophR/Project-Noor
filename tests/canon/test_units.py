"""Unit resolution is a hard safety control (SSOT §6.3)."""

from decimal import Decimal

import pytest

from noor.canon.models import CanonicalQuantity, ConversionApplied, SourceCode, UnitResolution
from noor.canon.registry import Conversion
from noor.canon.units import UnknownUnitError, from_canonical, resolve_unit, to_canonical
from tests.conftest import make_entry

LOINC_HBA1C = SourceCode(system="http://loinc.org", code="4548-4")


def test_a_reported_accepted_unit_resolves_explicitly():
    # Arrange
    entry = make_entry(accepted_units=["mmol/L", "mg/dL"])

    # Act
    resolution, unit = resolve_unit("mg/dL", None, entry)

    # Assert
    assert resolution is UnitResolution.explicit
    assert unit == "mg/dL"


def test_an_unrecognised_unit_is_ambiguous():
    # Arrange — "mg%" is a real-world spelling drift; never guessed (§6.3)
    entry = make_entry(accepted_units=["mmol/L", "mg/dL"])

    # Act
    resolution, unit = resolve_unit("mg%", None, entry)

    # Assert
    assert resolution is UnitResolution.ambiguous
    assert unit is None


def test_a_reported_unit_conflicting_with_the_code_implied_unit_is_ambiguous():
    # Arrange — the source says %, the code says mmol/mol: somebody is wrong
    entry = make_entry(
        accepted_units=["%", "mmol/mol"],
        canonical_ucum="mmol/mol",
        code_unit_map={"http://loinc.org|59261-8": "mmol/mol"},
    )
    ifcc_code = SourceCode(system="http://loinc.org", code="59261-8")

    # Act
    resolution, unit = resolve_unit("%", ifcc_code, entry)

    # Assert
    assert resolution is UnitResolution.ambiguous
    assert unit is None


def test_an_absent_unit_is_inferred_from_the_source_code():
    # Arrange
    entry = make_entry(
        accepted_units=["%"],
        canonical_ucum="%",
        code_unit_map={"http://loinc.org|4548-4": "%"},
    )

    # Act
    resolution, unit = resolve_unit(None, LOINC_HBA1C, entry)

    # Assert
    assert resolution is UnitResolution.inferred_from_code
    assert unit == "%"


def test_an_absent_unit_and_an_unknown_code_is_ambiguous():
    # Arrange
    entry = make_entry(code_unit_map={})
    unknown = SourceCode(system="http://loinc.org", code="0000-0")

    # Act
    resolution, _ = resolve_unit(None, unknown, entry)

    # Assert
    assert resolution is UnitResolution.ambiguous


def test_an_absent_unit_and_no_code_is_ambiguous():
    # Arrange / Act
    resolution, _ = resolve_unit(None, None, make_entry())

    # Assert
    assert resolution is UnitResolution.ambiguous


def test_resolution_never_looks_at_the_value():
    # Arrange — 42 "looks like" mmol/mol and 7.4 "looks like" %; §6.3 forbids
    # inferring either. Both hba1c observables carry exactly one accepted unit,
    # so a missing unit with no code is ambiguous even so.
    ngsp = make_entry(observable="hba1c_ngsp", canonical_ucum="%", accepted_units=["%"])
    ifcc = make_entry(
        observable="hba1c_ifcc", canonical_ucum="mmol/mol", accepted_units=["mmol/mol"]
    )

    # Act / Assert
    assert resolve_unit(None, None, ngsp)[0] is UnitResolution.ambiguous
    assert resolve_unit(None, None, ifcc)[0] is UnitResolution.ambiguous


def test_identity_conversion_preserves_the_value_exactly():
    # Arrange
    entry = make_entry()

    # Act
    quantity = to_canonical(Decimal("7.40"), "mmol/L", entry)

    # Assert — identity is not quantised; the as-reported precision survives
    assert quantity.value == Decimal("7.40")
    assert quantity.ucum == "mmol/L"
    assert quantity.conversion_applied is None  # no conversion, no work to show


def test_a_declared_conversion_records_the_provenance_of_its_result():
    # Arrange — §6.3: every conversion carries its own provenance, so a stored
    # canonical value can be traced to the exact factor that produced it
    entry = make_entry(
        accepted_units=["mmol/L", "mg/dL"],
        conversions=[
            Conversion(
                from_unit="mg/dL",
                multiply=Decimal("0.055507"),
                precision=2,
                tolerance=Decimal("0.5"),
                canonical_tolerance=Decimal("0.01"),
                version="glucose-mgdl-v1",
            )
        ],
    )

    # Act
    quantity = to_canonical(Decimal("90"), "mg/dL", entry)

    # Assert
    assert quantity.value == Decimal("5.00")
    applied = quantity.conversion_applied
    assert applied is not None
    assert applied.from_unit == "mg/dL"
    assert applied.add == Decimal("0")
    assert applied.multiply == Decimal("0.055507")
    assert applied.precision == 2
    assert applied.rounding == "ROUND_HALF_UP"
    assert applied.version == "glucose-mgdl-v1"


def test_an_unconvertible_unit_raises():
    # Arrange / Act / Assert
    with pytest.raises(UnknownUnitError):
        to_canonical(Decimal("100"), "mg/dL", make_entry())


def test_reverse_identity_rejects_a_quantity_outside_the_declared_canonical_unit():
    # Arrange
    quantity = CanonicalQuantity(value=Decimal("7.40"), ucum="mg%")

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "mg%", make_entry())


def test_reverse_identity_rejects_malformed_recorded_provenance():
    # Arrange
    entry = make_entry()
    malformed = ConversionApplied.model_construct(
        from_unit="",
        add=Decimal("0"),
        multiply=Decimal("1"),
        precision=2,
        rounding="ROUND_HALF_UP",
        version="test-v1",
    )
    quantity = CanonicalQuantity(
        value=Decimal("7.40"),
        ucum="mmol/L",
        conversion_applied=malformed,
    )

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "mmol/L", entry)


@pytest.mark.parametrize(
    "multiplier", [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")]
)
def test_reverse_conversion_rejects_a_non_positive_or_non_finite_recorded_multiplier(
    multiplier: Decimal,
):
    # Arrange
    entry = make_entry(
        accepted_units=["mmol/L", "mg/dL"],
        conversions=[
            Conversion(
                from_unit="mg/dL",
                multiply=Decimal("0.055507"),
                precision=2,
                tolerance=Decimal("0.5"),
                canonical_tolerance=Decimal("0.01"),
                version="glucose-mgdl-v1",
            )
        ],
    )
    malformed = ConversionApplied.model_construct(
        from_unit="mg/dL",
        add=Decimal("0"),
        multiply=multiplier,
        precision=2,
        rounding="ROUND_HALF_UP",
        version="test-v1",
    )
    quantity = CanonicalQuantity(
        value=Decimal("5.00"),
        ucum="mmol/L",
        conversion_applied=malformed,
    )

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "mg/dL", entry)


def test_reverse_identity_returns_a_valid_canonical_quantity_value():
    # Arrange
    entry = make_entry()
    quantity = CanonicalQuantity(value=Decimal("7.40"), ucum="mmol/L")

    # Act
    value = from_canonical(quantity, "mmol/L", entry)

    # Assert
    assert value == Decimal("7.40")


def test_reverse_conversion_rejects_an_undeclared_target_unit():
    # Arrange
    quantity = to_canonical(Decimal("90"), "mmol/L", make_entry())

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "mg%", make_entry())


def test_reverse_conversion_uses_the_recorded_conversion_provenance():
    # Arrange
    entry = make_entry(
        accepted_units=["mmol/L", "mg/dL"],
        conversions=[
            Conversion(
                from_unit="mg/dL",
                multiply=Decimal("0.055507"),
                precision=2,
                tolerance=Decimal("0.5"),
                canonical_tolerance=Decimal("0.01"),
                version="glucose-mgdl-v2",
            )
        ],
    )
    quantity = CanonicalQuantity(
        value=Decimal("5.00"),
        ucum="mmol/L",
        conversion_applied=ConversionApplied(
            from_unit="mg/dL",
            add=Decimal("1"),
            multiply=Decimal("0.05"),
            precision=2,
            rounding="ROUND_HALF_UP",
            version="glucose-mgdl-v1",
        ),
    )

    # Act
    value = from_canonical(quantity, "mg/dL", entry)

    # Assert
    assert value == Decimal("99")


def test_reverse_conversion_rejects_a_target_that_does_not_match_provenance():
    # Arrange
    entry = make_entry(
        accepted_units=["mmol/L", "mg/dL", "g/L"],
        conversions=[
            Conversion(
                from_unit="mg/dL",
                multiply=Decimal("0.055507"),
                precision=2,
                tolerance=Decimal("0.5"),
                canonical_tolerance=Decimal("0.01"),
                version="glucose-mgdl-v2",
            ),
            Conversion(
                from_unit="g/L",
                multiply=Decimal("0.1"),
                precision=2,
                tolerance=Decimal("0.5"),
                canonical_tolerance=Decimal("0.01"),
                version="glucose-gl-v1",
            ),
        ],
    )
    quantity = CanonicalQuantity(
        value=Decimal("5.00"),
        ucum="mmol/L",
        conversion_applied=ConversionApplied(
            from_unit="mg/dL",
            add=Decimal("0"),
            multiply=Decimal("0.05"),
            precision=2,
            rounding="ROUND_HALF_UP",
            version="glucose-mgdl-v1",
        ),
    )

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "g/L", entry)
