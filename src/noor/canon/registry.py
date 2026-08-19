"""The observable registry: per-observable data-validity declarations (SSOT §6.6).

The registry declares — never assumes — canonical units, accepted units and
their conversions, the two validity envelopes (§6.4), delta policy, required
context/method fields, and a named owner per observable.
"""

from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Self

from pydantic import Field, field_serializer, field_validator, model_validator

from noor.canon.models import NoorModel


class UnknownObservableError(KeyError):
    """A capture named an observable the registry does not govern."""


class Envelope(NoorModel):
    """Inclusive bounds in the canonical unit, versioned independently (§6.4)."""

    low: Decimal
    high: Decimal
    version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if not self.low < self.high:
            raise ValueError("an envelope's low must be below its high")
        return self


class Conversion(NoorModel):
    """canonical = (value + add) * multiply, quantised to `precision` (§6.3).

    `tolerance` is the round-trip bound in the SOURCE unit and
    `canonical_tolerance` the bound in the CANONICAL unit: §6.3 requires
    reversibility "in both directions", and a single bound can only express one of
    them (§12.6 claim 41).

    `version` is this conversion's own content version. Every canonical value it
    produces carries it (`ConversionApplied`), so a stored value can always be
    traced to the factor that produced it and a later correction to a factor can
    identify the values it affected. Bump it in the same PR that changes any of
    `add`, `multiply`, `precision`, or `rounding`.
    """

    from_unit: str = Field(min_length=1)
    add: Decimal = Decimal("0")
    multiply: Decimal = Decimal("1")
    precision: int = Field(ge=0)
    rounding: Literal["ROUND_HALF_UP", "ROUND_HALF_EVEN"] = "ROUND_HALF_UP"
    tolerance: Decimal = Field(gt=0)
    canonical_tolerance: Decimal = Field(gt=0)
    version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _positive_multiplier(self) -> Self:
        if self.multiply <= 0:
            raise ValueError("a conversion multiplier must be positive")
        return self


CONTEXT_FIELDS = frozenset(
    {
        "setting",
        "posture",
        "arm",
        "cuff_size",
        "rest_duration_seconds",
        "reading_ordinal",
        "is_average",
    }
)
METHOD_FIELDS = frozenset({"device_class", "specimen", "assay"})


class DeltaPolicy(NoorModel):
    """Like-with-like comparison rules (§6.1 layer 3)."""

    max_abs_change: Decimal = Field(gt=0)
    within_hours: int = Field(gt=0)
    compare_context: tuple[str, ...] = ()
    compare_device_class: bool = True

    @model_validator(mode="after")
    def _known_context_fields(self) -> Self:
        unknown = set(self.compare_context) - CONTEXT_FIELDS
        if unknown:
            raise ValueError(f"delta policy names unknown context fields: {sorted(unknown)}")
        return self


class ObservableEntry(NoorModel):
    """One observable's data-validity declaration (SSOT §6.6).

    Quantity observables only (assumption 13): §6.6's Curated Clinical Signal Set
    has no canonical unit and no envelopes, and is not modelled here. Nothing in
    this schema is a treatment threshold — §6.4's three boundary types are
    separate, and there is deliberately nowhere here to put a clinical decision
    boundary.
    """

    observable: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    owner: str = Field(min_length=1)
    canonical_ucum: str = Field(min_length=1)
    accepted_units: tuple[str, ...] = Field(min_length=1)
    conversions: tuple[Conversion, ...] = ()
    code_unit_map: Mapping[str, str] = Field(default_factory=dict)
    physiologic: Envelope
    operational: Envelope
    delta_policy: DeltaPolicy
    repeat_tolerance: Decimal = Field(gt=0)
    required_context: tuple[str, ...] = ()
    required_method: tuple[str, ...] = ()

    @field_validator("code_unit_map", mode="after")
    @classmethod
    def _freeze_code_unit_map(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        return MappingProxyType(dict(value))

    @field_serializer("code_unit_map")
    def _serialise_code_unit_map(self, value: Mapping[str, str]) -> dict[str, str]:
        return dict(value)

    @model_validator(mode="after")
    def _internally_consistent(self) -> Self:
        if self.canonical_ucum not in self.accepted_units:
            raise ValueError("the canonical unit must be an accepted unit")
        for conversion in self.conversions:
            if conversion.from_unit == self.canonical_ucum:
                raise ValueError("a conversion from the canonical unit is identity; omit it")
            if conversion.from_unit not in self.accepted_units:
                raise ValueError(f"conversion from unaccepted unit {conversion.from_unit!r}")
        missing_conversions = (set(self.accepted_units) - {self.canonical_ucum}) - {
            conversion.from_unit for conversion in self.conversions
        }
        if missing_conversions:
            raise ValueError(
                f"accepted non-canonical units need conversions: {sorted(missing_conversions)}"
            )
        for key, unit in self.code_unit_map.items():
            if key.count("|") != 1 or any(not component for component in key.split("|")):
                raise ValueError("code_unit_map keys are 'system|code'")
            if unit not in self.accepted_units:
                raise ValueError(f"code_unit_map names unaccepted unit {unit!r}")
        if not (
            self.physiologic.low <= self.operational.low
            and self.operational.high <= self.physiologic.high
        ):
            raise ValueError("the operational envelope must sit inside the physiologic one")
        unknown = (set(self.required_context) - CONTEXT_FIELDS) | (
            set(self.required_method) - METHOD_FIELDS
        )
        if unknown:
            raise ValueError(f"required fields that do not exist: {sorted(unknown)}")
        return self


class ObservableRegistry(NoorModel):
    entries: dict[str, ObservableEntry]

    @model_validator(mode="after")
    def _keys_match_entries(self) -> Self:
        for key, entry in self.entries.items():
            if key != entry.observable:
                raise ValueError(f"registry key {key!r} does not match entry {entry.observable!r}")
        return self

    def entry(self, observable: str) -> ObservableEntry:
        try:
            return self.entries[observable]
        except KeyError:
            raise UnknownObservableError(observable) from None
