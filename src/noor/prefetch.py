"""§5.2's pre-departure read: what Noor asks the EMR in the office, so that the house
never has to ask.

Not in `domain/`, because it touches the store and the EMR both — it is the plumbing
between them, which is the thing `tests/test_seam.py` draws its line around. The clock
still arrives as an argument, because when the reads happened is a fact the caller holds.
"""
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from sqlite3 import Connection
from typing import NamedTuple

from noor import store
from noor.domain.examination import Item, applies
from noor.domain.reconciliation import Product, house_entry, read_entry
from noor.domain.states import DataState, Datum
from noor.emr import EMR

PRESCRIBED = "prescribed"
ALLERGIES = "allergies"
SURVEILLANCE = "surveillance"


def prepare(conn: Connection, records: EMR, patient_id: str, *,
            items: Sequence[Item], at: datetime) -> tuple[str, ...]:
    """Read, store, and return the subjects that came back Unreachable.

    Three reads and no more: the prescribed list, the surveillance dates, the allergies.
    Demographics and problems are the `patients` row already, and a read Noor does not
    need in the house is a read that can fail for nothing.

    Returning the failures is what makes this a departure step rather than a background
    job. §4.10 wants a failed input named where it can still be acted on, and the office
    is the only place with signal.
    """
    held = set(store.conditions(conn, patient_id))
    answers = {PRESCRIBED: _prescribed(records, patient_id),
               ALLERGIES: records.allergies(patient_id)}
    for item in items:
        if applies(item.conditions, held):
            answers[f"{SURVEILLANCE}:{item.id}"] = _last_done(records, patient_id, item.id)
    for subject, answer in answers.items():
        store.cache_read(conn, patient_id, subject, answer, at)
    return tuple(subject for subject, answer in answers.items()
                 if answer.state is DataState.UNREACHABLE)


def _prescribed(records: EMR, patient_id: str) -> Datum:
    """`house_entry`'s shape, so one decoder serves the cached list and a stored
    Reconciliation both."""
    answer = records.medications(patient_id)
    if not answer.is_present:
        return answer
    return Datum.present([house_entry(item) for item in answer.value], as_of=answer.as_of)


def _last_done(records: EMR, patient_id: str, item: str) -> Datum:
    """A date is not JSON. The state and the `as_of` are untouched; only the value moves."""
    answer = records.surveillance(patient_id, item)
    if not answer.is_present:
        return answer
    return Datum.present(answer.value.isoformat(), as_of=answer.as_of)


def surveillance(conn: Connection, patient_id: str) -> dict[str, Datum]:
    """Item id → when it was last done, which is what `brief()` and `compose()` both take.

    Empty where nobody prepared. Task 11 is where that becomes a sentence on the page
    rather than a silence.
    """
    prefix = f"{SURVEILLANCE}:"
    return {subject.removeprefix(prefix): _date_back(row.answer)
            for subject, row in store.cached(conn, patient_id).items()
            if subject.startswith(prefix)}


def _date_back(answer: Datum) -> Datum:
    if not answer.is_present:
        return answer
    return Datum.present(date.fromisoformat(answer.value), as_of=answer.as_of)


def prescribed(conn: Connection, patient_id: str, *,
               products: Mapping[str, Product]) -> Datum:
    """The list Reconciliation compares the house against.

    Unreachable where nobody prepared, because in the house the two are the same fact:
    Noor cannot see the prescribed list. §7.2 already has the shape that says so, and it
    names the consequence — discrepancies against the list are not shown.
    """
    row = store.cached(conn, patient_id).get(PRESCRIBED)
    if row is None:
        return Datum.unreachable()
    if not row.answer.is_present:
        return row.answer
    return Datum.present(tuple(read_entry(entry, products) for entry in row.answer.value),
                         as_of=row.answer.as_of)


def allergies(conn: Connection, patient_id: str) -> Datum:
    """The Handover's one EMR-sourced line. Strings, so there is nothing to decode."""
    row = store.cached(conn, patient_id).get(ALLERGIES)
    return Datum.unreachable() if row is None else row.answer


class Readiness(NamedTuple):
    """What the office knows about one Patient before the van leaves (§5.2)."""

    prepared_at: datetime | None
    unreadable: tuple[str, ...]


def readiness(conn: Connection, patient_id: str) -> Readiness:
    """Both halves of §5.2's question, from one query.

    `prepared_at` is the *earliest* of the reads, so the age the roster shows is the age
    of the oldest answer being carried and not the newest. `unreadable` names the read
    rather than the subject — seven surveillance items that all failed are one failure to
    report, and Task 8 has one sentence per read to name it with.
    """
    rows = store.cached(conn, patient_id)
    return Readiness(
        min((row.read_at for row in rows.values()), default=None),
        tuple(sorted({subject.split(":")[0] for subject, row in rows.items()
                      if row.answer.state is DataState.UNREACHABLE})))
