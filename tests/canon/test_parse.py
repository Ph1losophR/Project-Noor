"""Layer 1 of canon: parsing and the two mistype shapes (SSOT §6.1).

A shape hint never changes a value or a state, so its only job is to say what to
re-check — which makes discrimination the property under test here, not just
arithmetic. Each shape is asserted to be silent where its own answer would be a
foregone conclusion.
"""

from decimal import Decimal

import pytest

from noor.canon.parse import (
    decimal_shift_suspected,
    digit_transposition_suspected,
    parse_value,
)
from noor.canon.registry import Envelope
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
def test_the_decimal_shape_matches_only_a_plausible_one_place_slip(value, suspected):
    # Arrange — synthetic entry: operational [4, 8], a span of 2.0
    entry = make_entry()

    # Act / Assert
    assert decimal_shift_suspected(Decimal(value), entry) is suspected


@pytest.mark.parametrize(
    ("high", "suspected"),
    [
        # 59 / 6 is 9.83: a shifted partner is still news about this reading
        pytest.param("59", True, id="a_span_just_under_ten_still_discriminates"),
        # 60 / 6 is exactly 10, and the guard is inclusive
        pytest.param("60", False, id="a_span_of_exactly_ten_is_vacuous"),
    ],
)
def test_the_decimal_shape_is_silent_where_the_envelope_makes_its_answer_a_constant(
    high, suspected
):
    # Arrange — an envelope spanning a factor of ten or more has a ten-times
    # partner inside it for essentially the whole flagged band, so "yes" describes
    # the envelope rather than the reading. Measured against the shipped registry,
    # eGFR spans 30x and answered yes for 100% of flagged values.
    entry = make_entry(
        physiologic=Envelope(low=Decimal("1"), high=Decimal("200"), version="t1"),
        operational=Envelope(low=Decimal("6"), high=Decimal(high), version="t1"),
    )

    # Act / Assert — 5.9 is below the floor either way, and shifts to 59
    assert decimal_shift_suspected(Decimal("5.9"), entry) is suspected


def test_the_decimal_shape_is_silent_for_an_envelope_that_reaches_zero():
    # Arrange — no shipped observable straddles zero, but the schema asks only for
    # low < high, so a pull request can declare one. The span is read by dividing
    # the envelope by its own floor, and a floor of zero has no reciprocal.
    entry = make_entry(
        physiologic=Envelope(low=Decimal("-10"), high=Decimal("10"), version="t1"),
        operational=Envelope(low=Decimal("0"), high=Decimal("8"), version="t1"),
    )

    # Act / Assert — 40 shifts to 4.0, inside [0, 8]; the guard answers first
    assert decimal_shift_suspected(Decimal("40"), entry) is False


@pytest.mark.parametrize(
    ("reported", "suspected"),
    [
        # 5.0 is inside [4, 8]; the point holds its place while the digits move
        pytest.param("0.5", True, id="two_digits_exchanged_across_the_point"),
        # 04 is 4, the operational floor, and bounds are inclusive
        pytest.param("40", True, id="a_swap_landing_on_the_operational_floor"),
        # 061 is 61, 601 is 601: neither is plausible
        pytest.param("601", False, id="no_swap_lands_inside_the_envelope"),
        # the only exchange available is one digit with itself
        pytest.param("55", False, id="a_repeated_digit_has_no_distinct_swap"),
        # 4 is already inside, so nothing here is a slip to re-check
        pytest.param("4", False, id="a_single_digit_cannot_be_transposed"),
    ],
)
def test_the_digit_shape_matches_only_a_swap_that_lands_inside_the_envelope(reported, suspected):
    # Arrange — synthetic entry: operational [4, 8], canonical mmol/L
    entry = make_entry()

    # Act / Assert
    assert digit_transposition_suspected(reported, "mmol/L", entry) is suspected


def test_the_digit_shape_swaps_the_reported_text_and_not_the_converted_value(registry):
    # Arrange — 98.6 degF is 37.0 Cel. Typed as 89.6 it converts to 32.0 Cel and is
    # flagged, and the swap that explains it is a Fahrenheit one: the mistype
    # happened before the -32 offset. Swapping the digits of the canonical 32.0
    # models an error nobody made, which is why the reported text is what moves.
    entry = registry.entry("body_temperature")

    # Act / Assert
    assert digit_transposition_suspected("89.6", "[degF]", entry) is True
    assert digit_transposition_suspected("32.0", "Cel", entry) is False
