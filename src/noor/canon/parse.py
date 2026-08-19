"""Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1).

Strict plain-decimal notation only. A comma separator, a stray character, or
scientific notation is unparseable — never "probably meant 7.4".
"""

import re
from decimal import Decimal

from noor.canon.registry import ObservableEntry

_VALUE_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")


def parse_value(raw: str) -> Decimal | None:
    """Parse an as-reported value, or return None when it is unparseable.

    The pattern is total: anything it matches, Decimal accepts.
    """
    text = raw.strip()
    if not _VALUE_PATTERN.fullmatch(text):
        return None
    return Decimal(text)


def decimal_transposition_suspected(value: Decimal, entry: ObservableEntry) -> bool:
    """True when sliding the decimal point one place would move the value inside
    the operational envelope — the classic 7.4-recorded-as-74 mistype.

    Answers the pattern question only; the pipeline asks it only for values
    already outside the operational envelope.
    """
    operational = entry.operational
    return any(
        operational.low <= shifted <= operational.high for shifted in (value * 10, value / 10)
    )
