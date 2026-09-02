"""Delivering the Write-Back (§4.9). Above the seam: it may touch the store and the EMR.

Separate from `domain/writeback.py` on purpose. That module decides *what* is written and
is pure; this one decides *when it leaves the tablet* and touches both boundaries. The
seam test in Task 1 asserts the direction — `writeback.py` never imports this file.
"""
import sqlite3
from datetime import datetime
from threading import Lock
from typing import NamedTuple

from noor import store
from noor.domain.visit import Visit
from noor.domain.writeback import WRITTEN_BACK, WriteBack, Windows, assemble
from noor.emr import EMR, WriteRejected


# ADR 0006 gives the prototype one process; coalescing drains closes its double-click race.
_DRAIN_LOCK = Lock()


class NotClosed(RuntimeError):
    """Delivery was asked for a Visit that has not closed. The Write-Back is the
    close's last act (§4.9) — there is nothing to report about a Visit in progress."""


class Delivery(NamedTuple):
    """What one drain did. Both halves, because §4.10 forbids a quiet failure: the
    caller is handed every refusal with what the EMR said, not a shorter `sent` list."""

    sent: tuple[str, ...]
    failed: tuple[tuple[str, str], ...]


def envelope(visit: Visit, items: tuple[WriteBack, ...]) -> dict:
    """One submit per Visit, carrying every item. The EMR either has this Visit's
    Write-Back or does not have it, so a retry cannot duplicate item 3 while item 5 is
    still missing. `kind.name` rather than the integer: §4.9's row number is stable,
    but a reader of the EMR's inbox should not have to look it up."""
    return {"visit_id": visit.id,
            "items": [{"kind": item.kind.name, "payload": item.payload}
                      for item in items]}


def send(
    conn: sqlite3.Connection,
    emr: EMR,
    visit_id: str,
    *,
    windows: Windows,
    supervisor: str,
    attempted_at: datetime,
) -> None:
    """Submit one Visit, keeping clinical time separate from delivery time.

    Response deadlines derive from the stored close. `attempted_at` records the receipt or
    refusal, and the refusal is re-raised so `drain` alone decides whether to continue.
    """
    visit = store.load(conn, visit_id)
    if visit.state not in WRITTEN_BACK:
        raise NotClosed(
            f"Visit {visit_id} is {visit.state.value}; a Write-Back is the close's "
            f"last act (§4.9)")
    items = assemble(visit, goal=store.goal(conn, visit.patient_id), at=visit.closed_at,
                     windows=windows, supervisor=supervisor)
    try:
        emr.submit(visit.patient_id, envelope(visit, items))
    except WriteRejected as refusal:
        store.mark_refused(conn, visit_id, attempted_at, str(refusal))
        raise
    store.mark_written_back(conn, visit_id, attempted_at)


def drain(
    conn: sqlite3.Connection,
    emr: EMR,
    *,
    windows: Windows,
    supervisor: str,
    attempted_at: datetime,
) -> Delivery:
    """Try every queued Visit once, coalescing overlapping drains in this process.

    A refusal is recorded and the next Visit is tried, so one rejected Patient record
    cannot hold up the day's deliveries.
    """
    if not _DRAIN_LOCK.acquire(blocking=False):
        return Delivery((), ())
    try:
        sent: list[str] = []
        failed: list[tuple[str, str]] = []
        for visit_id in store.queued(conn):
            try:
                send(conn, emr, visit_id, windows=windows, supervisor=supervisor,
                     attempted_at=attempted_at)
            except WriteRejected as refusal:
                failed.append((visit_id, str(refusal)))
            else:
                sent.append(visit_id)
        return Delivery(tuple(sent), tuple(failed))
    finally:
        _DRAIN_LOCK.release()
