"""The two envelopes (SSOT §6.1 layer 2, §6.4). Bounds are inclusive and
declared in the canonical unit. Synthetic entry: physiologic [2, 10],
operational [4, 8] — every boundary row is exercised (testing standards)."""

from decimal import Decimal

import pytest

from noor.canon.plausibility import EnvelopePosition, locate
from tests.conftest import make_entry


@pytest.mark.parametrize(
    ("value", "position"),
    [
        pytest.param("6", EnvelopePosition.within_operational, id="an_ordinary_value"),
        pytest.param("4", EnvelopePosition.within_operational, id="the_operational_floor"),
        pytest.param("8", EnvelopePosition.within_operational, id="the_operational_ceiling"),
        pytest.param(
            "3.9", EnvelopePosition.outside_operational, id="just_below_the_operational_floor"
        ),
        pytest.param(
            "8.1", EnvelopePosition.outside_operational, id="just_above_the_operational_ceiling"
        ),
        # at a physiologic bound, so still generatable, but well outside operational
        pytest.param("2", EnvelopePosition.outside_operational, id="the_physiologic_floor"),
        pytest.param("10", EnvelopePosition.outside_operational, id="the_physiologic_ceiling"),
        pytest.param(
            "1.9", EnvelopePosition.outside_physiologic, id="just_below_the_physiologic_floor"
        ),
        pytest.param(
            "10.1", EnvelopePosition.outside_physiologic, id="just_above_the_physiologic_ceiling"
        ),
    ],
)
def test_a_value_is_placed_against_both_envelopes_with_inclusive_bounds(value, position):
    # Arrange / Act / Assert
    assert locate(Decimal(value), make_entry()) is position
