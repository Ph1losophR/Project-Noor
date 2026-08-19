"""Unit resolution and registry-declared conversion (SSOT §6.3).

Resolution is blind to the value: NGSP % and IFCC mmol/mol are distinct
observables (§5), and no magnitude ever hints at a unit.
"""

from decimal import Decimal

from noor.canon.models import CanonicalQuantity, ConversionApplied, SourceCode, UnitResolution
from noor.canon.registry import ObservableEntry


class UnknownUnitError(ValueError):
    """No registry declaration covers the requested unit, or a value's recorded
    conversion does not match it. Raised by both directions of conversion."""


def resolve_unit(
    reported_unit: str | None,
    source_code: SourceCode | None,
    entry: ObservableEntry,
) -> tuple[UnitResolution, str | None]:
    """Resolve the unit a value arrived in (§6.3).

    explicit: the source stated a unit the registry accepts, consistent with any
    code-implied unit. inferred_from_code: no stated unit, and the source code
    maps to exactly one. ambiguous: everything else — a hard failure.
    """
    code_unit: str | None = None
    if source_code is not None:
        code_unit = entry.code_unit_map.get(f"{source_code.system}|{source_code.code}")

    if reported_unit is not None:
        if reported_unit in entry.accepted_units and (
            code_unit is None or code_unit == reported_unit
        ):
            return UnitResolution.explicit, reported_unit
        return UnitResolution.ambiguous, None
    if code_unit is not None:
        return UnitResolution.inferred_from_code, code_unit
    return UnitResolution.ambiguous, None


def to_canonical(value: Decimal, unit: str, entry: ObservableEntry) -> CanonicalQuantity:
    """Convert a resolved unit to the canonical UCUM unit (§6.6).

    A converted value carries the conversion that produced it: §6.3 requires that
    every conversion carry its own provenance, so `5.00 mmol/L` can always be
    traced back to the declared factor and version that made it. An identity
    conversion carries none — there is no work to show.
    """
    if unit == entry.canonical_ucum:
        return CanonicalQuantity(value=value, ucum=entry.canonical_ucum)
    for conversion in entry.conversions:
        if conversion.from_unit == unit:
            scaled = (value + conversion.add) * conversion.multiply
            quantum = Decimal(1).scaleb(-conversion.precision)
            return CanonicalQuantity(
                value=scaled.quantize(quantum, rounding=conversion.rounding),
                ucum=entry.canonical_ucum,
                conversion_applied=ConversionApplied(
                    from_unit=conversion.from_unit,
                    add=conversion.add,
                    multiply=conversion.multiply,
                    precision=conversion.precision,
                    rounding=conversion.rounding,
                    version=conversion.version,
                ),
            )
    raise UnknownUnitError(f"{entry.observable}: no conversion declared from {unit!r}")


def from_canonical(quantity: CanonicalQuantity, unit: str, entry: ObservableEntry) -> Decimal:
    """The exact inverse of `to_canonical`, before quantisation.

    Exists for the round-trip property test (§12.6 claim 41) and for displayed
    conversions (§6.3: convert only with displayed conversion and provenance).

    A value that carries provenance is replayed with its own historical factors,
    never the registry's current ones: a value stored under `glucose-mgdl-v1`
    must convert back the way it converted in, even after a factor is corrected.

    Raises `UnknownUnitError` when `quantity` is not in `entry`'s canonical unit,
    when `unit` is not an accepted unit, or when recorded provenance names a
    source unit `entry` does not accept as non-canonical or that disagrees with
    `unit`.
    """
    if quantity.ucum != entry.canonical_ucum:
        raise UnknownUnitError(
            f"{entry.observable}: quantity is not in the declared canonical unit"
        )
    if unit not in entry.accepted_units:
        raise UnknownUnitError(f"{entry.observable}: no reverse unit declared for {unit!r}")
    applied = quantity.conversion_applied
    if applied is not None:
        provenance_source_is_noncanonical = (
            applied.from_unit in entry.accepted_units and applied.from_unit != entry.canonical_ucum
        )
        if not provenance_source_is_noncanonical:
            raise UnknownUnitError(
                f"{entry.observable}: provenance source unit is not an accepted non-canonical unit"
            )
        if unit != entry.canonical_ucum and applied.from_unit != unit:
            raise UnknownUnitError(
                f"{entry.observable}: conversion provenance does not match {unit!r}"
            )
    if unit == entry.canonical_ucum:
        return quantity.value
    if applied is not None:
        return (quantity.value / applied.multiply) - applied.add
    conversion = next(
        conversion for conversion in entry.conversions if conversion.from_unit == unit
    )
    return (quantity.value / conversion.multiply) - conversion.add
