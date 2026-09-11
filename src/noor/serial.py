"""The Visit as JSON text. One function per type — a generic codec is unreadable."""
import json
from collections.abc import Callable
from datetime import datetime
from operator import attrgetter

from noor.domain.emergency import EmergencyRecord, EntryKind, TimelineEntry
from noor.domain.opinions import (
    Disposition, Flag, Outcome, OverrideLevel, Recommendation,
)
from noor.domain.plans import (
    Axis, Band, BetweenVisitPlan, Comparison, GoalOfCare, MeasurementSchedule, Threshold,
)
from noor.domain.records import Reason, Resolution
from noor.domain.states import (
    DataState, Datum, EscalationTier, Section, VisitKind, VisitState,
)
from noor.domain.visit import Visit
from noor.domain.vitals import HomeReading, Source

_value = attrgetter("value")


def _maybe(value: object | None, encode: Callable[..., object]) -> object | None:
    """The only place None is handled on the way out. Eleven fields, one branch."""
    return None if value is None else encode(value)


def _maybe_read(raw: object | None, decode: Callable[..., object]) -> object | None:
    """The only place null is handled on the way in."""
    return None if raw is None else decode(raw)


def _reason(reason: Reason) -> dict:
    return {"row_id": reason.row_id, "free_text": reason.free_text}


def _read_reason(raw: dict) -> Reason:
    return Reason(raw["row_id"], raw["free_text"])


def _resolution(resolution: Resolution) -> dict:
    # content is whatever a form posted (Task 21), so it is already JSON-safe.
    return {"content": resolution.content,
            "reason": _maybe(resolution.reason, _reason)}


def _read_resolution(section: Section, raw: dict) -> Resolution:
    return Resolution(section, raw["content"], _maybe_read(raw["reason"], _read_reason))


def _entry(entry: TimelineEntry) -> dict:
    return {"kind": entry.kind.value, "text": entry.text, "at": entry.at.isoformat()}


def _read_entry(raw: dict) -> TimelineEntry:
    return TimelineEntry(
        EntryKind(raw["kind"]), raw["text"], datetime.fromisoformat(raw["at"]))


def _emergency(record: EmergencyRecord) -> dict:
    return {"started_at": record.started_at.isoformat(),
            "entries": [_entry(entry) for entry in record.entries],
            "ended_at": _maybe(record.ended_at, datetime.isoformat)}


def _read_emergency(raw: dict) -> EmergencyRecord:
    return EmergencyRecord(
        datetime.fromisoformat(raw["started_at"]),
        [_read_entry(entry) for entry in raw["entries"]],
        _maybe_read(raw["ended_at"], datetime.fromisoformat))


def _recommendation(rec: Recommendation) -> dict:
    return {"id": rec.id, "text": rec.text, "tier": rec.tier.value,
            "executor": rec.executor, "provenance": rec.provenance,
            "strength": rec.strength}


def _read_recommendation(raw: dict) -> Recommendation:
    return Recommendation(raw["id"], raw["text"], EscalationTier(raw["tier"]),
                          raw["executor"], raw["provenance"], raw["strength"])


def _disposition(item: Disposition) -> dict:
    return {"recommendation_id": item.recommendation_id, "outcome": item.outcome.value,
            "by": item.by, "at": item.at.isoformat(),
            "level": _maybe(item.level, _value),
            "reason": _maybe(item.reason, _reason)}


def _read_disposition(raw: dict) -> Disposition:
    return Disposition(raw["recommendation_id"], Outcome(raw["outcome"]), raw["by"],
                       datetime.fromisoformat(raw["at"]),
                       _maybe_read(raw["level"], OverrideLevel),
                       _maybe_read(raw["reason"], _read_reason))


def _flag(item: Flag) -> dict:
    return {"subject": item.subject, "by": item.by,
            "at": item.at.isoformat(), "note": item.note}


def _read_flag(raw: dict) -> Flag:
    return Flag(raw["subject"], raw["by"],
                datetime.fromisoformat(raw["at"]), raw["note"])


def _threshold(rule: Threshold) -> dict:
    return {"axis": rule.axis.value, "comparison": rule.comparison.value,
            "value": rule.value, "action": rule.action}


def _read_threshold(raw: dict) -> Threshold:
    return Threshold(Axis(raw["axis"]), Comparison(raw["comparison"]),
                     raw["value"], raw["action"])


def _schedule(item: MeasurementSchedule) -> dict:
    return {"axis": item.axis.value, "times_per_week": item.times_per_week}


def _read_schedule(raw: dict) -> MeasurementSchedule:
    return MeasurementSchedule(Axis(raw["axis"]), raw["times_per_week"])


def _plan(plan: BetweenVisitPlan) -> dict:
    return {"titration": [_threshold(rule) for rule in plan.titration],
            "schedule": [_schedule(item) for item in plan.schedule],
            "stop_rules": [_threshold(rule) for rule in plan.stop_rules]}


def _read_plan(raw: dict) -> BetweenVisitPlan:
    # tuple(), not list: BetweenVisitPlan's fields are tuples and equality is by type.
    return BetweenVisitPlan(
        titration=tuple(_read_threshold(rule) for rule in raw["titration"]),
        schedule=tuple(_read_schedule(item) for item in raw["schedule"]),
        stop_rules=tuple(_read_threshold(rule) for rule in raw["stop_rules"]))


def _datum(datum: Datum) -> dict:
    """The one Datum a Visit holds carries a Between-Visit Plan, so that is the shape."""
    return {"state": datum.state.value,
            "value": _maybe(datum.value, _plan),
            "as_of": _maybe(datum.as_of, datetime.isoformat)}


def _read_datum(raw: dict) -> Datum:
    return Datum(DataState(raw["state"]),
                 _maybe_read(raw["value"], _read_plan),
                 _maybe_read(raw["as_of"], datetime.fromisoformat))


def _home_reading(reading: HomeReading) -> dict:
    return {"measurement": reading.measurement, "value": reading.value,
            "taken_at": reading.taken_at.isoformat(), "source": reading.source.value}


def _read_home_reading(raw: dict) -> HomeReading:
    return HomeReading(raw["measurement"], raw["value"],
                       datetime.fromisoformat(raw["taken_at"]), Source(raw["source"]))


def dump_visit(visit: Visit) -> str:
    """JSON text, indented, because a stored Visit is also an audit record (N8)."""
    return json.dumps({
        "id": visit.id,
        "patient_id": visit.patient_id,
        "kind": _maybe(visit.kind, _value),
        "junior_physician": visit.junior_physician,
        "nurse": visit.nurse,
        "state": visit.state.value,
        # Section is an IntEnum, so .name is the key: JSON would stringify the integer
        # and Section("4") does not resolve. The name is also the readable one.
        "resolutions": {section.name: _resolution(resolution)
                        for section, resolution in visit.resolutions.items()},
        "emergencies": [_emergency(record) for record in visit.emergencies],
        "shown": [_recommendation(rec) for rec in visit.shown],
        "dispositions": [_disposition(item) for item in visit.dispositions],
        "flags": [_flag(item) for item in visit.flags],
        "plan": _maybe(visit.plan, _plan),
        "previous_plan": _datum(visit.previous_plan),
        "home_readings": [_home_reading(reading) for reading in visit.home_readings],
        "started_at": _maybe(visit.started_at, datetime.isoformat),
        "closed_by": visit.closed_by,
        "closed_at": _maybe(visit.closed_at, datetime.isoformat),
        "closing_reason": _maybe(visit.closing_reason, _reason),
    }, indent=2)


def load_visit(text: str) -> Visit:
    raw = json.loads(text)
    return Visit(
        id=raw["id"],
        patient_id=raw["patient_id"],
        kind=_maybe_read(raw["kind"], VisitKind),
        junior_physician=raw["junior_physician"],
        nurse=raw["nurse"],
        state=VisitState(raw["state"]),
        resolutions={Section[key]: _read_resolution(Section[key], value)
                     for key, value in raw["resolutions"].items()},
        emergencies=[_read_emergency(record) for record in raw["emergencies"]],
        shown=[_read_recommendation(rec) for rec in raw["shown"]],
        dispositions=[_read_disposition(item) for item in raw["dispositions"]],
        flags=[_read_flag(raw) for raw in raw["flags"]],
        plan=_maybe_read(raw["plan"], _read_plan),
        previous_plan=_read_datum(raw["previous_plan"]),
        home_readings=[_read_home_reading(raw) for raw in raw["home_readings"]],
        started_at=_maybe_read(raw["started_at"], datetime.fromisoformat),
        closed_by=raw["closed_by"],
        closed_at=_maybe_read(raw["closed_at"], datetime.fromisoformat),
        closing_reason=_maybe_read(raw["closing_reason"], _read_reason),
    )


def _band(band: Band) -> dict:
    return {"axis": band.axis.value, "floor": band.floor,
            "ceiling": band.ceiling, "rationale": band.rationale}


def _read_band(raw: dict) -> Band:
    return Band(Axis(raw["axis"]), raw["floor"], raw["ceiling"], raw["rationale"])


def dump_goal(goal: GoalOfCare) -> str:
    """The target as stored text. Same reason as `dump_visit`: it is an audit record."""
    return json.dumps({
        "patient_id": goal.patient_id,
        "bands": [_band(band) for band in goal.bands],
        "lineage": goal.lineage,
        "office_anchor": goal.office_anchor,
        "proposed_by": goal.proposed_by,
        "proposed_at": goal.proposed_at.isoformat(),
        "ratified_by": goal.ratified_by,
        "ratified_at": _maybe(goal.ratified_at, datetime.isoformat),
    }, indent=2)


def load_goal(text: str) -> GoalOfCare:
    raw = json.loads(text)
    return GoalOfCare(
        patient_id=raw["patient_id"],
        bands=tuple(_read_band(band) for band in raw["bands"]),
        lineage=raw["lineage"],
        office_anchor=raw["office_anchor"],
        proposed_by=raw["proposed_by"],
        proposed_at=datetime.fromisoformat(raw["proposed_at"]),
        ratified_by=raw["ratified_by"],
        ratified_at=_maybe_read(raw["ratified_at"], datetime.fromisoformat),
    )


def read_plan(raw: dict[str, object]) -> BetweenVisitPlan:
    """A Between-Visit Plan posted by a form, decoded the way stored ones are."""
    return _read_plan(raw)


def dump_datum(datum: Datum) -> str:
    """A Datum whose value is already JSON-safe, as stored text (§5.2's cache).

    Distinct from `_datum`, which is the codec for the one Datum a *Visit* holds: that one
    carries a Between-Visit Plan and needs `_plan` on both sides. Here the caller encoded
    the value before it arrived, so this pair is the state and the timestamp only.
    """
    return json.dumps({"state": datum.state.value,
                       "value": datum.value,
                       "as_of": _maybe(datum.as_of, datetime.isoformat)})


def load_datum(text: str) -> Datum:
    """A tuple stored as JSON returns a list. Nothing that reads a cached answer indexes
    it by identity — the Handover iterates the allergies and the decoder maps the
    medications — so the shape that matters is `Sequence`, and that survives.
    """
    raw = json.loads(text)
    return Datum(DataState(raw["state"]), raw["value"],
                 _maybe_read(raw["as_of"], datetime.fromisoformat))
