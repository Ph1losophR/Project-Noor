"""Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1)."""

from decimal import Decimal

from noor.canon.parse import decimal_transposition_suspected, parse_value
from tests.conftest import make_entry


def test_a_plain_decimal_parses():
    # Arrange / Act / Assert
    assert parse_value("7.4") == Decimal("7.4")


def test_an_integer_parses():
    # Arrange / Act / Assert
    assert parse_value("140") == Decimal("140")


def test_a_negative_parses():
    # Arrange / Act / Assert — the parse layer does not judge plausibility
    assert parse_value("-2") == Decimal("-2")


def test_surrounding_whitespace_is_stripped():
    # Arrange / Act / Assert
    assert parse_value("  5.5\t") == Decimal("5.5")


def test_a_comma_decimal_separator_is_unparseable():
    # Arrange / Act / Assert — never silently read "7,4" as 7.4 or 74
    assert parse_value("7,4") is None


def test_a_double_decimal_point_is_unparseable():
    # Arrange / Act / Assert
    assert parse_value("7.4.2") is None


def test_letters_are_unparseable():
    # Arrange / Act / Assert
    assert parse_value("abc") is None


def test_scientific_notation_is_unparseable():
    # Arrange / Act / Assert — not a format a human enters for a vital
    assert parse_value("1e3") is None


def test_an_empty_string_is_unparseable():
    # Arrange / Act / Assert
    assert parse_value("") is None
    assert parse_value("   ") is None


def test_a_bare_sign_or_dot_is_unparseable():
    # Arrange / Act / Assert
    assert parse_value("-") is None
    assert parse_value(".") is None
    assert parse_value("+7") is None


def test_a_value_ten_times_too_large_matches_the_transposition_pattern():
    # Arrange — synthetic entry: operational [4, 8]
    entry = make_entry()

    # Act / Assert — 74 is outside; 7.4 is inside
    assert decimal_transposition_suspected(Decimal("74"), entry) is True


def test_a_value_ten_times_too_small_matches_the_transposition_pattern():
    # Arrange
    entry = make_entry()

    # Act / Assert — 0.5 is outside [4, 8]; 5.0 is inside
    assert decimal_transposition_suspected(Decimal("0.5"), entry) is True


def test_an_in_envelope_value_does_not_match_the_pattern():
    # Arrange
    entry = make_entry()

    # Act / Assert — neither 55 nor 0.55 lands in [4, 8]
    assert decimal_transposition_suspected(Decimal("5.5"), entry) is False


def test_an_extreme_value_with_no_plausible_shift_does_not_match_the_pattern():
    # Arrange
    entry = make_entry()

    # Act / Assert — 900 and 90 are both outside [4, 8]: extreme, not a slip
    assert decimal_transposition_suspected(Decimal("900"), entry) is False
