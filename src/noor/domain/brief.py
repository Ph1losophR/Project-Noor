"""The Brief (§5.3): the Vitals series, what the last Visit concluded, what surveillance
is overdue, and what Noor could not see. Findings only — never a Recommendation.

Computed from its arguments and returned. Nothing here writes anything down: a stored
Brief is a second, ageing copy of the truth.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from noor.domain.examination import Item, applies, overdue
from noor.domain.records import Reason
from noor.domain.states import DataState, Datum, Section, VisitState
from noor.domain.visit import Visit
from noor.domain.vitals import Measurement


@dataclass(frozen=True)
class Point:
    on: date
    value: str


@dataclass(frozen=True)
class Trend:
    """One measurement across the Visits that recorded it, oldest first."""

    measurement: str
    label: str
    unit: str
    points: tuple[Point, ...]


@dataclass(frozen=True)
class Due:
    """An overdue surveillance item. `last_done` is Present with a date, or Absent."""

    item: str
    label: str
    last_done: Datum


@dataclass(frozen=True)
class LastVisit:
    """What the last Visit concluded — out of Noor's own store, so always readable."""

    on: date
    state: VisitState
    reason: Reason | None


@dataclass(frozen=True)
class Brief:
    """No `recommendation` field and no `home_readings` field, both on purpose (§5.3)."""

    patient_id: str
    trends: tuple[Trend, ...]
    last_visit: LastVisit | None
    previous_plan: Datum
    due: tuple[Due, ...]
    blind_spots: tuple[str, ...]


def brief(
    visit: Visit,
    *,
    history: Sequence[Visit],
    conditions: Sequence[str],
    catalogue: Sequence[Item],
    measures: Sequence[Measurement],
    surveillance: Mapping[str, Datum],
    as_of: date,
) -> Brief:
    """`history` is oldest first, as `store.history` returns it."""
    held = set(conditions)
    mine = tuple(item for item in catalogue if applies(item.conditions, held))
    return Brief(
        visit.patient_id,
        _trends(history, measures),
        _last(history),
        visit.previous_plan,
        _due(mine, surveillance, as_of),
        _blind_spots(visit, mine, surveillance),
    )


def _trends(history: Sequence[Visit], measures: Sequence[Measurement]) -> tuple[Trend, ...]:
    """A measurement nobody recorded gets no series: an empty one reads as a flat one."""
    found = []
    for measure in measures:
        points = _points(measure.id, history)
        if points:
            found.append(Trend(measure.id, measure.label, measure.unit, points))
    return tuple(found)


def _points(measurement: str, history: Sequence[Visit]) -> tuple[Point, ...]:
    found = []
    for visit in history:
        recorded = _recorded(visit)
        if measurement in recorded:
            # Vitals content means the Visit was In Progress, so it has a start time.
            found.append(Point(visit.started_at.date(), str(recorded[measurement])))
    return tuple(found)


def _recorded(visit: Visit) -> Mapping[str, object]:
    """The Vitals content, or nothing — a section resolved with a reason has none (§5.8),
    and a Visit that ended before Vitals has no resolution at all."""
    resolution = visit.resolutions.get(Section.VITALS)
    if resolution is None or resolution.content is None:
        return {}
    return resolution.content


def _last(history: Sequence[Visit]) -> LastVisit | None:
    if not history:
        return None
    visit = history[-1]
    return LastVisit(visit.closed_at.date(), visit.state, visit.closing_reason)


def _due(
    catalogue: Sequence[Item], surveillance: Mapping[str, Datum], as_of: date
) -> tuple[Due, ...]:
    """Overdue, and readable. An item whose date could not be read is a blind spot, not
    a due item — listing it would make a clinical claim out of a failed request."""
    found = []
    for item in catalogue:
        last = surveillance.get(item.id, Datum.absent())
        if last.state is not DataState.UNREACHABLE and overdue(last, item.months, as_of):
            found.append(Due(item.id, item.label, last))
    return tuple(found)


def _blind_spots(
    visit: Visit, catalogue: Sequence[Item], surveillance: Mapping[str, Datum]
) -> tuple[str, ...]:
    """N6, in sentences, because this is displayed rather than acted on."""
    spots = [
        f"{item.label}: the date could not be read from the record"
        for item in catalogue
        if surveillance.get(item.id, Datum.absent()).state is DataState.UNREACHABLE
    ]
    if visit.previous_plan.state is DataState.UNREACHABLE:
        spots.append(
            "The previous Between-Visit Plan could not be read, so this Visit's Home "
            "Readings have nothing to be scored against"
        )
    return tuple(spots)
