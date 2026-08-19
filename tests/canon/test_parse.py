"""Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1)."""

from decimal import Decimal

import pytest

from noor.canon.parse import decimal_transposition_suspected, parse_value
from tests.conftest import make_entry


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("7.4", Decimal("7.4"), id="a_plain_decimal"),
        pytest.param("140", Decimal("140"), id="an_integer"),
        # the parse layer does not judge plausibility
        pytest.param("-2", Decimal("-2"), id="a_negative"),
        pytest.param("  5.5\t", Decimal("5.5"), id="surrounding_whitespace_stripped"),
    ],
)
def test_a_well_formed_value_parses(raw, expected):
    # Arrange / Act / Assert
    assert parse_value(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        # never silently read "7,4" as 7.4 or 74
        pytest.param("7,4", id="a_comma_decimal_separator"),
        pytest.param("7.4.2", id="a_double_decimal_point"),
        pytest.param("abc", id="letters"),
        # not a format a human enters for a vital
        pytest.param("1e3", id="scientific_notation"),
        pytest.param("", id="an_empty_string"),
        pytest.param("   ", id="whitespace_only"),
        pytest.param("-", id="a_bare_sign"),
        pytest.param(".", id="a_bare_dot"),
        pytest.param("+7", id="a_leading_plus"),
        # Arabic-Indic 74, fullwidth 74, a mixed run, and 74 written with the
        # Arabic decimal separator U+066B: Decimal reads all four as 74 or 7.4
        # without complaint, so the pattern has to refuse them. Escaped rather
        # than literal because the digits are confusable by eye (ruff RUF001).
        pytest.param("\u0667\u0664", id="arabic_indic_digits"),
        pytest.param("\uff17\uff14", id="fullwidth_digits"),
        pytest.param("7\u0664", id="ascii_and_arabic_indic_digits_mixed"),
        pytest.param("\u0667\u066b\u0664", id="an_arabic_decimal_separator"),
    ],
)
def test_a_malformed_value_is_unparseable(raw):
    # Arrange / Act / Assert
    assert parse_value(raw) is None


@pytest.mark.parametrize(
    ("value", "suspected"),
    [
        # 74 is outside [4, 8]; 7.4 is inside
        pytest.param("74", True, id="ten_times_too_large"),
        # 0.5 is outside; 5.0 is inside
        pytest.param("0.5", True, id="ten_times_too_small"),
        # the shifted value lands on the bound itself, and bounds are inclusive
        pytest.param("40", True, id="a_shift_landing_on_the_operational_floor"),
        pytest.param("80", True, id="a_shift_landing_on_the_operational_ceiling"),
        # neither 55 nor 0.55 lands in [4, 8]
        pytest.param("5.5", False, id="an_in_envelope_value"),
        # 9000 and 90 are both outside: extreme, not a slip
        pytest.param("900", False, id="an_extreme_value_with_no_plausible_shift"),
    ],
)
def test_the_transposition_pattern_matches_only_a_plausible_one_place_slip(value, suspected):
    # Arrange — synthetic entry: operational [4, 8]
    entry = make_entry()

    # Act / Assert
    assert decimal_transposition_suspected(Decimal(value), entry) is suspected
