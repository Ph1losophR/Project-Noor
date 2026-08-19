"""Layer 1 of canon: parsing and the two mistype shapes (SSOT §6.1).

Strict plain-decimal notation only, in ASCII digits. A comma separator, a stray
character, scientific notation, or an Arabic-Indic numeral is unparseable —
never "probably meant 7.4". The digit class is spelled out rather than written
as the regex digit shorthand, which matches every Unicode decimal digit and
would have let `Decimal` normalise Arabic-Indic digits to a silent 74. A legible
number the clinician can retype in the home is worth a visible `parse_failure`,
the same argument §6.3 makes for an unresolvable unit; how Noor should handle
Arabic numerals is part of what §13.2 item 9 gates.

§6.1 names two mistype shapes — the decimal point in the wrong place, and two
digits in the wrong order — and both are recorded the same way: a suspicion on a
record a human must already resolve. A shape hint never changes a value, never
changes a state, and never lowers the resolution bar (§6.2). It says only what to
re-check, which makes one property essential: it has to *discriminate*. A hint
that is true of every flagged value carries no information about the reading in
front of the reader, and trains them to skim the flag that matters. Each shape
below is therefore silent wherever its own arithmetic makes it a foregone
conclusion.
"""

import re
from decimal import Decimal
from itertools import pairwise

from noor.canon.registry import ObservableEntry
from noor.canon.units import to_canonical

_VALUE_PATTERN = re.compile(r"-?[0-9]+(\.[0-9]+)?")
_ASCII_DIGITS = frozenset("0123456789")

# An operational envelope spanning this factor or more has a ten-times-larger or
# ten-times-smaller partner for essentially every value outside it, which is what
# makes the decimal question vacuous there rather than merely often true.
_VACUOUS_DECIMAL_SPAN = Decimal(10)


def parse_value(raw: str) -> Decimal | None:
    """Parse an as-reported value, or return None when it is unparseable.

    The pattern is total: anything it matches, Decimal accepts.
    """
    text = raw.strip()
    if not _VALUE_PATTERN.fullmatch(text):
        return None
    return Decimal(text)


def decimal_shift_suspected(value: Decimal, entry: ObservableEntry) -> bool:
    """True when sliding the decimal point one place would move the value inside
    the operational envelope — the classic 7.4-recorded-as-74 mistype.

    Silent for observables whose operational envelope spans a factor of ten or
    more, and for one straddling zero. There, a shifted partner sits inside the
    envelope for the whole flagged band, so "yes" describes the envelope rather
    than the reading: measured against the shipped registry the answer is yes for
    100% of flagged glucose, creatinine and eGFR values, and 99% of weights. The
    span is read from the envelope rather than declared, so it cannot drift when
    a pull request widens one.

    Answers the pattern question only; the pipeline asks it only for values
    already outside the operational envelope.
    """
    operational = entry.operational
    if operational.low <= 0 or operational.high / operational.low >= _VACUOUS_DECIMAL_SPAN:
        return False
    return any(
        operational.low <= shifted <= operational.high for shifted in (value * 10, value / 10)
    )


def digit_transposition_suspected(
    reported: str, resolved_unit: str, entry: ObservableEntry
) -> bool:
    """True when exchanging two neighbouring digits of the *reported* text would
    move the value inside the operational envelope — 47 entered as 74.

    The swap is applied to what the source reported, not to the canonical value:
    the mistype happened before conversion and digit positions do not survive
    one. Body temperature converts from `[degF]` with a -32 offset, so
    transposing the digits of a canonical Celsius value would model an error
    nobody made.

    Unlike the decimal shape this one needs no vacuity guard — it is bounded by
    the digits actually present, and holds for a minority of the flagged band on
    every observable in the shipped registry.

    Answers the pattern question only; the pipeline asks it only for values
    already outside the operational envelope.
    """
    operational = entry.operational
    for candidate in _adjacent_digit_swaps(reported.strip()):
        # Exchanging two digits of a string that already parsed leaves a string
        # that still parses: the sign, the digit counts either side of the point,
        # and the point itself all keep their places.
        converted = to_canonical(Decimal(candidate), resolved_unit, entry)
        if operational.low <= converted.value <= operational.high:
            return True
    return False


def _adjacent_digit_swaps(text: str) -> set[str]:
    """Every distinct text formed by exchanging two digits adjacent in the digit
    sequence. The decimal point holds its place, so "7.4" yields "4.7"."""
    positions = [index for index, char in enumerate(text) if char in _ASCII_DIGITS]
    swaps: set[str] = set()
    for left, right in pairwise(positions):
        if text[left] == text[right]:
            continue
        chars = list(text)
        chars[left], chars[right] = chars[right], chars[left]
        swaps.add("".join(chars))
    return swaps
