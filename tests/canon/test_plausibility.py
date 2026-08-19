"""The two envelopes (SSOT §6.1 layer 2, §6.4). Bounds are inclusive and
declared in the canonical unit. Synthetic entry: physiologic [2, 10],
operational [4, 8] — every boundary row is exercised (testing standards)."""

from decimal import Decimal

from noor.canon.plausibility import EnvelopePosition, locate
from tests.conftest import make_entry


def test_an_ordinary_value_is_within_operational():
    # Arrange / Act / Assert
    assert locate(Decimal("6"), make_entry()) is EnvelopePosition.within_operational


def test_the_operational_low_bound_is_inclusive():
    # Arrange / Act / Assert
    assert locate(Decimal("4"), make_entry()) is EnvelopePosition.within_operational


def test_the_operational_high_bound_is_inclusive():
    # Arrange / Act / Assert
    assert locate(Decimal("8"), make_entry()) is EnvelopePosition.within_operational


def test_just_below_the_operational_floor_is_outside_operational():
    # Arrange / Act / Assert
    assert locate(Decimal("3.9"), make_entry()) is EnvelopePosition.outside_operational


def test_just_above_the_operational_ceiling_is_outside_operational():
    # Arrange / Act / Assert
    assert locate(Decimal("8.1"), make_entry()) is EnvelopePosition.outside_operational


def test_the_physiologic_low_bound_is_inclusive():
    # Arrange / Act / Assert — at the physiologic bound but below operational
    assert locate(Decimal("2"), make_entry()) is EnvelopePosition.outside_operational


def test_the_physiologic_high_bound_is_inclusive():
    # Arrange / Act / Assert
    assert locate(Decimal("10"), make_entry()) is EnvelopePosition.outside_operational


def test_below_the_physiologic_floor_cannot_be_generated():
    # Arrange / Act / Assert
    assert locate(Decimal("1.9"), make_entry()) is EnvelopePosition.outside_physiologic


def test_above_the_physiologic_ceiling_cannot_be_generated():
    # Arrange / Act / Assert
    assert locate(Decimal("10.1"), make_entry()) is EnvelopePosition.outside_physiologic
