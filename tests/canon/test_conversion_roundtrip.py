"""Every registry conversion is reversible within its declared precision
(SSOT §12.6 claim 41, §6.3). Parametrised over the REAL registry: a conversion
added to content/observables/registry.yaml is tested here automatically.
§6.3 requires reversibility in BOTH directions, so there are two properties: one
bounded by `tolerance` in the source unit, one by `canonical_tolerance`.

Reversibility alone cannot catch a wrong factor — the round trip divides by the
number it multiplied by, so a 10x error round-trips perfectly. `GOLDEN_VALUES`
is where the factor itself is checked, and a conversion added without one fails.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from noor.canon.models import CanonicalQuantity
from noor.canon.units import UnknownUnitError, from_canonical, to_canonical
from noor.catalogue.registry_loader import load_registry
from tests.conftest import REGISTRY_PATH

REGISTRY = load_registry(REGISTRY_PATH)
CONVERSIONS = [
    (observable, conversion)
    for observable, entry in REGISTRY.entries.items()
    for conversion in entry.conversions
]

# One hand-computed (source value, canonical value) pair per declared conversion.
GOLDEN_VALUES = {
    # 90 x 0.055507 = 4.99563, quantised to 2dp
    ("glucose", "mg/dL"): (Decimal("90"), Decimal("5.00")),
    # the §R-11 incident class: °F mistaken for °C. (98.6 - 32) x 0.5555556, 1dp
    ("body_temperature", "[degF]"): (Decimal("98.6"), Decimal("37.0")),
    # 1.0 x 88.4, 1dp
    ("creatinine", "mg/dL"): (Decimal("1.0"), Decimal("88.4")),
}


def test_the_registry_declares_conversions_to_test():
    # Arrange / Act / Assert — a registry with zero conversions makes this file
    # vacuous; fail loudly instead of passing vacuously
    assert CONVERSIONS, "no registry conversions declared — claim 41 has no object"


def test_every_registry_conversion_declares_a_hand_computed_golden_value():
    # Arrange / Act — the round-trip properties below are self-consistent by
    # construction, so a new conversion is unverified until its factor is checked
    # against a value computed by hand
    unchecked = [
        (observable, conversion.from_unit)
        for observable, conversion in CONVERSIONS
        if (observable, conversion.from_unit) not in GOLDEN_VALUES
    ]

    # Assert
    assert not unchecked, f"conversions with no golden value: {unchecked}"


@pytest.mark.parametrize(
    "observable,from_unit,source_value,expected_canonical",
    [(observable, unit, *pair) for (observable, unit), pair in GOLDEN_VALUES.items()],
    ids=[f"{observable}:{unit}" for observable, unit in GOLDEN_VALUES],
)
def test_a_declared_conversion_produces_its_hand_computed_canonical_value(
    observable, from_unit, source_value, expected_canonical
):
    # Arrange
    entry = REGISTRY.entry(observable)

    # Act
    quantity = to_canonical(source_value, from_unit, entry)

    # Assert
    assert quantity.value == expected_canonical
    assert quantity.ucum == entry.canonical_ucum


def test_from_canonical_in_a_canonical_unit_returns_the_value():
    # Arrange
    entry = REGISTRY.entry("glucose")
    quantity = to_canonical(Decimal("5.5"), "mmol/L", entry)

    # Act / Assert
    assert from_canonical(quantity, "mmol/L", entry) == Decimal("5.5")


def test_from_canonical_to_an_undeclared_unit_raises():
    # Arrange
    entry = REGISTRY.entry("glucose")
    quantity = to_canonical(Decimal("5.5"), "mmol/L", entry)

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "mg%", entry)


@pytest.mark.parametrize(
    "observable,conversion",
    CONVERSIONS,
    ids=[f"{observable}:{conversion.from_unit}" for observable, conversion in CONVERSIONS],
)
@given(
    value=st.decimals(
        min_value=Decimal("0.1"),
        max_value=Decimal("2000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    )
)
def test_every_registry_conversion_round_trips_within_declared_precision(
    observable, conversion, value
):
    # Arrange
    entry = REGISTRY.entry(observable)

    # Act
    canonical = to_canonical(value, conversion.from_unit, entry)
    recovered = from_canonical(canonical, conversion.from_unit, entry)

    # Assert — the declared precision is the whole contract (§12.6 claim 41)
    assert canonical.ucum == entry.canonical_ucum
    assert abs(recovered - value) <= conversion.tolerance
    # …and the result says which conversion produced it (§6.3 provenance)
    assert canonical.conversion_applied is not None
    assert canonical.conversion_applied.version == conversion.version


@pytest.mark.parametrize(
    "observable,conversion",
    CONVERSIONS,
    ids=[f"{observable}:{conversion.from_unit}" for observable, conversion in CONVERSIONS],
)
@given(
    value=st.decimals(
        min_value=Decimal("0.1"),
        max_value=Decimal("2000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    )
)
def test_every_registry_conversion_round_trips_from_the_canonical_side(
    observable, conversion, value
):
    # Arrange — the other direction. §6.3 says reversible "in both directions",
    # and the source-unit tolerance cannot express the canonical-side bound. The
    # starting value is quantised to the conversion's own precision because that
    # is the only shape a stored canonical value ever has.
    entry = REGISTRY.entry(observable)
    canonical_value = value.quantize(Decimal(1).scaleb(-conversion.precision))
    canonical = CanonicalQuantity(value=canonical_value, ucum=entry.canonical_ucum)

    # Act
    out = from_canonical(canonical, conversion.from_unit, entry)
    back = to_canonical(out, conversion.from_unit, entry)

    # Assert
    assert back.ucum == entry.canonical_ucum
    assert abs(back.value - canonical_value) <= conversion.canonical_tolerance
