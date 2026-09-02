"""The Physical Examination's required element list (§4.2).

Composed from the Patient's conditions and whatever surveillance is overdue, or the
complete examination when there is nothing to compose from. The Field Team may add
elements to what comes out of here; it does not decide which are required.
"""

from calendar import monthrange
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum

from noor.domain.states import DataState, Datum, VisitKind


class Composition(Enum):
    """Why the list looks the way it does. Two of the three are the same list."""

    COMPOSED = "composed from the conditions and the overdue surveillance"
    BASELINE = "complete — a Baseline Visit has no surveillance history to compose from"
    UNREACHABLE = "complete — the surveillance dates could not be read"


@dataclass(frozen=True)
class Element:
    """One row of `physical-examination-elements.md`."""

    id: str
    label: str
    conditions: tuple[str, ...]
    overdue: str | None = None


@dataclass(frozen=True)
class Item:
    """One row of `surveillance-intervals.md`. `months` is how long it stays current."""

    id: str
    label: str
    months: int
    conditions: tuple[str, ...]


def items(rows: Sequence[Mapping[str, object]]) -> tuple[Item, ...]:
    return tuple(
        Item(row["id"], row["label"], row["months"], tuple(row["conditions"]))
        for row in rows
    )


@dataclass(frozen=True)
class Composed:
    required: tuple[Element, ...]
    basis: Composition

    @property
    def is_composed(self) -> bool:
        return self.basis is Composition.COMPOSED


def elements(rows: Sequence[Mapping[str, object]]) -> tuple[Element, ...]:
    return tuple(
        Element(row["id"], row["label"], tuple(row["conditions"]), row.get("overdue"))
        for row in rows
    )


def months_by_item(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    """Surveillance id → how long the item stays current, which is all `compose` needs."""
    return {item.id: item.months for item in items(rows)}


def overdue(last_done: Datum, months: int, as_of: date) -> bool:
    """Absent from the record is overdue, per `surveillance-intervals.md` itself: an item
    nobody recorded is one to do now. An Unreachable read never reaches here — `compose`
    falls back before it asks."""
    if not last_done.is_present:
        return True
    return last_done.value < _months_before(as_of, months)


def applies(conditions: Sequence[str], held: set[str]) -> bool:
    """A content row with no condition against it is for every Patient — the convention
    every ADR 0007 file shares, so this is the one place that reads it."""
    return not conditions or bool(held & set(conditions))


def compose(
    catalogue: Sequence[Element],
    *,
    kind: VisitKind,
    conditions: Sequence[str],
    surveillance: Mapping[str, Datum],
    intervals: Mapping[str, int],
    as_of: date,
) -> Composed:
    """The required list, and the basis it was arrived at on."""
    if kind is VisitKind.BASELINE:
        return Composed(tuple(catalogue), Composition.BASELINE)
    if any(datum.state is DataState.UNREACHABLE for datum in surveillance.values()):
        return Composed(tuple(catalogue), Composition.UNREACHABLE)
    held = set(conditions)
    return Composed(
        tuple(
            element
            for element in catalogue
            if applies(element.conditions, held)
            and _due(element, surveillance, intervals, as_of)
        ),
        Composition.COMPOSED,
    )


def _due(
    element: Element,
    surveillance: Mapping[str, Datum],
    intervals: Mapping[str, int],
    as_of: date,
) -> bool:
    """An element tied to a surveillance item is required only while that item is overdue."""
    if element.overdue is None:
        return True
    return overdue(surveillance.get(element.overdue, Datum.absent()),
                   intervals[element.overdue], as_of)


def _months_before(day: date, months: int) -> date:
    """Stdlib only — no dateutil. A short month clamps, so three months before 31 May
    is 28 February and not a date that does not exist."""
    shifted = day.month - 1 - months
    year, month = day.year + shifted // 12, shifted % 12 + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))
