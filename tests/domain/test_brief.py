"""The Brief: the Vitals series, what the last Visit concluded, what surveillance is
overdue, and an explicit statement of what Noor could not see (§5.3, N6)."""

from dataclasses import fields
from datetime import date, datetime, time

import pytest

from noor.domain.brief import Brief, brief
from noor.domain.examination import Item
from noor.domain.records import Reason, Resolution
from noor.domain.states import DataState, Datum, Section, VisitKind, VisitState
from noor.domain.vitals import Measurement
from noor.domain.visit import Visit

HBA1C = Item("hba1c", "HbA1c", 3, ("diabetes",))
POTASSIUM = Item("potassium", "Serum potassium", 12, ("hypertension",))
ITEMS = (HBA1C, POTASSIUM)

BP = Measurement("bp-seated", "Blood pressure, seated", "mmHg", ())
GLUCOSE = Measurement("capillary-glucose", "Capillary blood glucose", "mmol/L", ("diabetes",))
MEASURES = (BP, GLUCOSE)

TODAY = date(2026, 8, 28)


def _finished(day, *, vitals=None, no_vitals_because=None,
              state=VisitState.COMPLETED, reason=None):
    """A closed Visit, optionally carrying a Vitals resolution of either shape (§5.8)."""
    visit = Visit(f"v-{day.isoformat()}", "p-1", VisitKind.ROUTINE, state=state)
    visit.started_at = datetime.combine(day, time(9, 0))
    visit.closed_at = datetime.combine(day, time(10, 30))
    visit.closing_reason = reason
    if vitals is not None:
        visit.resolutions[Section.VITALS] = Resolution(Section.VITALS, content=vitals)
    elif no_vitals_because is not None:
        visit.resolutions[Section.VITALS] = Resolution(
            Section.VITALS, reason=Reason(no_vitals_because))
    return visit


def _read(*, history=(), conditions=("diabetes",), surveillance=None,
          previous_plan=None):
    # No kind: the Brief is read while the Visit is still Scheduled, and §5.5 settles the
    # kind at the Start. `brief()` never reads it — an argument here would imply it did.
    visit = Visit("v-next", "p-1")
    if previous_plan is not None:
        visit.previous_plan = previous_plan
    return brief(
        visit,
        history=history,
        conditions=conditions,
        catalogue=ITEMS,
        measures=MEASURES,
        surveillance=surveillance or {},
        as_of=TODAY,
    )


def test_the_vitals_series_runs_oldest_first():
    earlier = _finished(date(2026, 5, 4), vitals={"bp-seated": "150/94"})
    later = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(earlier, later))

    assert [point.value for point in result.trends[0].points] == ["150/94", "138/84"]


def test_a_series_point_carries_the_date_of_the_visit_that_took_it():
    visit = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(visit,))

    assert result.trends[0].points[0].on == date(2026, 7, 6)


def test_a_measurement_no_visit_ever_recorded_gets_no_series_at_all():
    """An empty series would look like a flat one. There is nothing to show."""
    visit = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(visit,))

    assert [trend.measurement for trend in result.trends] == ["bp-seated"]


def test_a_visit_that_resolved_vitals_with_a_reason_contributes_no_point():
    skipped = _finished(date(2026, 5, 4), no_vitals_because="no-working-device")
    taken = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(skipped, taken))

    assert len(result.trends[0].points) == 1


def test_a_visit_that_never_reached_vitals_contributes_no_point():
    ended = _finished(date(2026, 5, 4), state=VisitState.ENDED_EARLY,
                      reason=Reason("time-exhausted"))
    taken = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(ended, taken))

    assert len(result.trends[0].points) == 1


def test_the_series_keeps_the_value_exactly_as_it_was_recorded():
    """No parsing, no averaging, no direction — a slope is a Phase 3 rule (N7)."""
    visit = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(visit,))

    assert result.trends[0].points[0].value == "138/84"


def test_the_series_carries_the_unit_the_content_file_gives_it():
    visit = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(visit,))

    assert result.trends[0].unit == "mmHg"


def test_the_last_visit_is_the_most_recent_finished_one():
    earlier = _finished(date(2026, 5, 4), vitals={"bp-seated": "150/94"})
    later = _finished(date(2026, 7, 6), vitals={"bp-seated": "138/84"})

    result = _read(history=(earlier, later))

    assert result.last_visit.on == date(2026, 7, 6)


def test_the_last_visit_says_how_it_ended_and_why():
    ended = _finished(date(2026, 7, 6), state=VisitState.ENDED_EARLY,
                      reason=Reason("patient-too-unwell"))

    result = _read(history=(ended,))

    assert (result.last_visit.state, result.last_visit.reason) == (
        VisitState.ENDED_EARLY, Reason("patient-too-unwell"))


def test_a_patient_with_no_finished_visit_has_no_last_visit():
    result = _read(history=())

    assert result.last_visit is None


def test_surveillance_overdue_for_a_condition_the_patient_has_is_listed():
    stale = {"hba1c": Datum.present(date(2025, 2, 10), as_of=date(2025, 2, 10))}

    result = _read(surveillance=stale)

    assert [due.item for due in result.due] == ["hba1c"]


def test_surveillance_for_a_condition_the_patient_does_not_have_is_not_listed():
    result = _read(conditions=("diabetes",), surveillance={"potassium": Datum.absent()})

    assert "potassium" not in {due.item for due in result.due}


def test_surveillance_still_within_its_interval_is_not_listed():
    fresh = {"hba1c": Datum.present(date(2026, 8, 1), as_of=date(2026, 8, 1))}

    result = _read(surveillance=fresh)

    assert result.due == ()


def test_surveillance_that_was_never_recorded_is_listed_and_says_so():
    result = _read(surveillance={"hba1c": Datum.absent()})

    assert result.due[0].last_done.state is DataState.ABSENT


def test_surveillance_that_could_not_be_read_is_not_listed_as_due():
    """Calling it due would manufacture a clinical fact out of a failed request."""
    result = _read(surveillance={"hba1c": Datum.unreachable()})

    assert result.due == ()


def test_surveillance_that_could_not_be_read_is_declared_as_a_blind_spot():
    result = _read(surveillance={"hba1c": Datum.unreachable()})

    assert any("HbA1c" in spot for spot in result.blind_spots)


def test_an_unreachable_previous_plan_says_what_cannot_be_scored():
    result = _read(previous_plan=Datum.unreachable())

    assert any("Between-Visit Plan" in spot for spot in result.blind_spots)


def test_an_absent_previous_plan_declares_no_blind_spot():
    """Absent is the truth for a first Visit, not a failure to read (§5.3, N6). The Datum
    carries that, not the Visit's kind, which is not settled until the Start (§5.5)."""
    result = _read(previous_plan=Datum.absent())

    assert result.blind_spots == ()


def test_a_readable_previous_plan_is_carried_through_untouched():
    plan = Datum.present("the previous plan", as_of=datetime(2026, 7, 6, 10, 30))

    result = _read(previous_plan=plan)

    assert result.previous_plan is plan


@pytest.mark.parametrize(
    "forbidden, why",
    [
        ("recommend", "a Recommendation before anyone has examined the Patient is an anchor"),
        ("home", "Home Readings do not exist outside a Visit"),
    ],
)
def test_the_brief_carries_no_such_field(forbidden, why):
    """§5.3 names the no-Recommendation rule as the one most likely to be 'fixed'."""
    assert not [f.name for f in fields(Brief) if forbidden in f.name], why
