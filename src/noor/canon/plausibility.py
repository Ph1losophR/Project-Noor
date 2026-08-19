"""Layer 2 of canon: the two envelopes (SSOT §6.1, §6.4).

The physiologic envelope asks "could the instrument or person generate this?"
The operational envelope asks "is this the sort of value we expect to act on?"
Neither produces a diagnosis.
"""

from decimal import Decimal
from enum import StrEnum

from noor.canon.registry import ObservableEntry


class EnvelopePosition(StrEnum):
    within_operational = "within_operational"
    outside_operational = "outside_operational"
    outside_physiologic = "outside_physiologic"


def locate(value: Decimal, entry: ObservableEntry) -> EnvelopePosition:
    """Position of a canonical value against the entry's inclusive envelopes."""
    if not (entry.physiologic.low <= value <= entry.physiologic.high):
        return EnvelopePosition.outside_physiologic
    if not (entry.operational.low <= value <= entry.operational.high):
        return EnvelopePosition.outside_operational
    return EnvelopePosition.within_operational
