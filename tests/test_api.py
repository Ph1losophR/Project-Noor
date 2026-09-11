"""The JSON API: the roster's day, the Brief before the knock, the Cancelled write."""
import asyncio
from datetime import date, datetime, timedelta

import httpx
import pytest

from noor import api, store
from noor.domain.emergency import EntryKind
from noor.domain.plans import (
    Axis,
    Band,
    BetweenVisitPlan,
    Comparison,
    GoalOfCare,
    MeasurementSchedule,
    Threshold,
)
from noor.domain.records import Reason, Resolution
from noor.domain.opinions import (
    Disposition,
    Flag,
    Outcome,
    OverrideLevel,
    Recommendation,
)
from noor.domain.states import Datum, EscalationTier, Section, VisitKind
from noor.domain.supervisor import Route, Verdict, VerdictKey, week_start
from noor.domain.visit import Addendum, Visit

DAY = date(2026, 8, 28)
BASELINE_DAY = date(2026, 5, 25)
KNOCK = datetime(2026, 8, 28, 9, 20)
SET_AT = datetime(2026, 8, 28, 18, 40)
READ_AT = datetime(2026, 8, 28, 7, 0)
BASELINE_CLOSE = datetime(2026, 5, 25, 10, 30)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
SUPERVISOR = "Dr Tariq Mansoor"
REASON = "three months since the last review"

PLAN = BetweenVisitPlan(
    titration=(Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 150, "step up the dose"),),
    schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),),
    stop_rules=(
        Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180, "call the Supervisor"),
    ),
)

GOAL = GoalOfCare(
    "p-1",
    bands=(Band(Axis.SYSTOLIC, 110, 135, "home band, frailty considered"),),
    lineage="Proposed at the Baseline Visit from the household's own readings",
    office_anchor="146/88 at the referring clinic, 12 May 2026",
    proposed_by=JUNIOR_PHYSICIAN,
    proposed_at=BASELINE_CLOSE,
)


@pytest.fixture
def placed(tmp_path):
    """One file with one Patient and one Scheduled Visit, plus a client talking
    to the app over that file — the demo's shape, thrown away afterwards."""
    db = tmp_path / "noor.db"
    conn = store.connect(db)
    store.add_patient(
        conn,
        "p-1",
        "Fatima Ali",
        ["diabetes", "hypertension"],
        junior_physician=JUNIOR_PHYSICIAN,
        nurse=NURSE,
    )
    store.schedule(conn, Visit("v-1", "p-1"), DAY, REASON)
    conn.close()
    transport = httpx.ASGITransport(app=api.build(db))
    yield httpx.AsyncClient(transport=transport, base_url="http://noor"), db


def _get(client, url, params=None):
    """One GET through the app. Async underneath, sync at the call site, so the
    suite stays dependency-free (`FIRST`: no test runner plugins to install)."""

    async def run():
        return await client.get(url, params=params)

    return asyncio.run(run())


def _post(client, url, json=None, bare=False):
    """One POST. `bare` sends no body at all — an empty post is its own refusal."""

    async def run():
        if bare:
            return await client.post(url)
        return await client.post(url, json=json)

    return asyncio.run(run())


def _open(db):
    return store.connect(db)


def _completed_baseline(conn):
    """The Visit that makes p-1 a Routine Patient: a Completed Baseline carrying
    Vitals and a plan, so the Brief has a series and a standing plan to show."""
    visit = Visit("v-0", "p-1")
    store.schedule(conn, visit, BASELINE_DAY, "Enrolment — newly referred")
    visit.start(
        datetime(2026, 5, 25, 9, 0),
        VisitKind.BASELINE,
        junior_physician=JUNIOR_PHYSICIAN,
        nurse=NURSE,
    )
    for section in Section:
        visit.resolutions[section] = Resolution(section, content={"baseline": True})
    visit.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, content={"bp-seated": "148/92"}
    )
    visit.plan = PLAN
    visit.complete(by=JUNIOR_PHYSICIAN, at=BASELINE_CLOSE, goal=GOAL)
    store.save(conn, visit)


def test_the_roster_names_the_days_visits_with_their_planning_indicator(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/roster", params={"day": "2026-08-28"}).json()

    # Assert — no history behind her, so the indicator reads Baseline (§5.5)
    assert result == {
        "day": "2026-08-28",
        "visits": [
            {
                "visit_id": "v-1",
                "patient_id": "p-1",
                "patient_name": "Fatima Ali",
                "reason": REASON,
                "state": "scheduled",
                "planning": "baseline",
                "readiness": {"prepared_at": None, "unreadable": []},
            }
        ],
    }


def test_a_completed_baseline_behind_her_turns_the_indicator_to_routine(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    _completed_baseline(conn)
    conn.close()

    # Act
    result = _get(client, "/api/roster", params={"day": "2026-08-28"}).json()

    # Assert
    assert result["visits"][0]["planning"] == "routine"


def test_readiness_names_what_the_office_could_not_read(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    store.cache_read(conn, "p-1", "prescribed", Datum.unreachable(), READ_AT)
    store.cache_read(
        conn, "p-1", "allergies", Datum.present(("Penicillin",), as_of=READ_AT), READ_AT
    )
    conn.close()

    # Act
    result = _get(client, "/api/roster", params={"day": "2026-08-28"}).json()

    # Assert
    assert result["visits"][0]["readiness"] == {
        "prepared_at": READ_AT.isoformat(),
        "unreadable": ["prescribed"],
    }


def test_an_empty_day_is_an_empty_roster_not_an_error(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/roster", params={"day": "2026-09-01"}).json()

    # Assert
    assert result == {"day": "2026-09-01", "visits": []}


def test_a_roster_without_a_day_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/roster")

    # Assert
    assert response.status_code == 400


def test_a_roster_with_a_day_that_is_not_a_date_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/roster", params={"day": "friday"})

    # Assert
    assert response.status_code == 400


def test_the_brief_before_any_history_has_no_last_visit_and_no_plan(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/visits/v-1/brief", params={"as_of": "2026-08-28"}).json()

    # Assert
    assert result["patient_id"] == "p-1"
    assert result["last_visit"] is None
    assert result["previous_plan"] == {"state": "absent", "value": None, "as_of": None}
    assert result["trends"] == []
    assert result["blind_spots"] == []
    assert {
        "item": "hba1c",
        "label": "HbA1c",
        "last_done": {"state": "absent", "value": None, "as_of": None},
    } in result["due"]


def test_the_brief_after_a_completed_visit_names_what_it_concluded(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    _completed_baseline(conn)
    store.cache_read(
        conn,
        "p-1",
        "surveillance:hba1c",
        Datum.present("2025-02-10", as_of=READ_AT),
        READ_AT,
    )
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1/brief", params={"as_of": "2026-08-28"}).json()

    # Assert — the series, the conclusion, the standing plan, the stale date
    assert result["last_visit"] == {
        "on": "2026-05-25",
        "state": "completed",
        "reason": None,
    }
    assert result["trends"] == [
        {
            "measurement": "bp-seated",
            "label": "Blood pressure, seated",
            "unit": "mmHg",
            "points": [{"on": "2026-05-25", "value": "148/92"}],
        }
    ]
    assert result["previous_plan"] == {
        "state": "present",
        "value": {
            "titration": [
                {
                    "axis": "systolic",
                    "comparison": "above",
                    "value": 150,
                    "action": "step up the dose",
                }
            ],
            "schedule": [{"axis": "systolic", "times_per_week": 3}],
            "stop_rules": [
                {
                    "axis": "systolic",
                    "comparison": "above",
                    "value": 180,
                    "action": "call the Supervisor",
                }
            ],
        },
        "as_of": BASELINE_CLOSE.isoformat(),
    }
    assert {
        "item": "hba1c",
        "label": "HbA1c",
        "last_done": {
            "state": "present",
            "value": "2025-02-10",
            "as_of": READ_AT.isoformat(),
        },
    } in result["due"]


def test_the_brief_after_an_ended_early_visit_carries_its_reason(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    visit = Visit("v-0", "p-1")
    store.schedule(conn, visit, BASELINE_DAY, "Enrolment — newly referred")
    visit.start(
        datetime(2026, 5, 25, 9, 0),
        VisitKind.BASELINE,
        junior_physician=JUNIOR_PHYSICIAN,
        nurse=NURSE,
    )
    visit.end_early(
        Reason("other", "the road flooded"),
        JUNIOR_PHYSICIAN,
        datetime(2026, 5, 25, 9, 40),
    )
    store.save(conn, visit)
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1/brief", params={"as_of": "2026-08-28"}).json()

    # Assert
    assert result["last_visit"] == {
        "on": "2026-05-25",
        "state": "ended_early",
        "reason": {"row_id": "other", "free_text": "the road flooded"},
    }


def test_a_brief_for_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/visits/v-9/brief", params={"as_of": "2026-08-28"})

    # Assert
    assert response.status_code == 404


def test_a_brief_without_a_date_for_the_check_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/visits/v-1/brief")

    # Assert
    assert response.status_code == 400


def test_a_brief_with_a_date_that_is_not_a_date_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/visits/v-1/brief", params={"as_of": "yesterday"})

    # Assert
    assert response.status_code == 400


def test_cancelling_a_scheduled_visit_closes_it_with_the_given_reason(placed):
    # Arrange
    client, db = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/cancel",
        json={
            "row_id": "patient-not-at-home",
            "by": JUNIOR_PHYSICIAN,
            "at": SET_AT.isoformat(),
        },
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "cancelled"}
    assert store.load(_open(db), "v-1").state.value == "cancelled"


def test_cancelling_with_other_carries_its_words(placed):
    # Arrange
    client, db = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/cancel",
        json={
            "row_id": "other",
            "free_text": "the building gate was locked",
            "by": NURSE,
            "at": SET_AT.isoformat(),
        },
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "cancelled"}
    assert store.load(_open(db), "v-1").closing_reason == Reason(
        "other", "the building gate was locked"
    )


def test_cancelling_without_a_body_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/cancel", bare=True)

    # Assert
    assert response.status_code == 400


def test_cancelling_with_a_body_that_is_not_an_object_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/cancel", json=["patient-not-at-home"])

    # Assert
    assert response.status_code == 400


def test_cancelling_without_the_required_fields_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/cancel", json={"row_id": "patient-died"})

    # Assert
    assert response.status_code == 400


def test_cancelling_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/cancel",
        json={"row_id": "patient-died", "by": JUNIOR_PHYSICIAN, "at": "friday"},
    )

    # Assert
    assert response.status_code == 400


def test_cancelling_for_a_reason_not_on_the_list_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/cancel",
        json={
            "row_id": "because",
            "by": JUNIOR_PHYSICIAN,
            "at": SET_AT.isoformat(),
        },
    )

    # Assert
    assert response.status_code == 400


def test_cancelling_with_other_but_no_words_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/cancel",
        json={"row_id": "other", "by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.status_code == 400


def test_cancelling_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-9/cancel",
        json={
            "row_id": "patient-died",
            "by": JUNIOR_PHYSICIAN,
            "at": SET_AT.isoformat(),
        },
    )

    # Assert
    assert response.status_code == 404


def test_cancelling_a_visit_that_already_started_is_refused(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.start(
        KNOCK, VisitKind.BASELINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE
    )
    store.save(conn, visit)
    conn.close()

    # Act
    response = _post(client, 
        "/api/visits/v-1/cancel",
        json={
            "row_id": "patient-died",
            "by": JUNIOR_PHYSICIAN,
            "at": SET_AT.isoformat(),
        },
    )

    # Assert — a Cancelled never started, so a started Visit cannot take one (§5.4)
    assert response.status_code == 409


def test_cancelling_twice_is_refused(placed):
    # Arrange
    client, _ = placed
    posted = {
        "row_id": "patient-died",
        "by": JUNIOR_PHYSICIAN,
        "at": SET_AT.isoformat(),
    }
    _post(client, "/api/visits/v-1/cancel", json=posted)

    # Act
    response = _post(client, "/api/visits/v-1/cancel", json=posted)

    # Assert — terminal states are immutable; only an Addendum writes next (§5.9)
    assert response.status_code == 409


PLAN_JSON = {
    "titration": [
        {
            "axis": "systolic",
            "comparison": "above",
            "value": 150,
            "action": "step up the dose",
        }
    ],
    "schedule": [{"axis": "systolic", "times_per_week": 3}],
    "stop_rules": [
        {
            "axis": "systolic",
            "comparison": "above",
            "value": 180,
            "action": "call the Supervisor",
        }
    ],
}

GOAL_JSON = {
    "bands": [
        {"axis": "systolic", "floor": 110, "ceiling": 135, "rationale": "home band"}
    ],
    "lineage": "Proposed at the Baseline Visit from the household's own readings",
    "office_anchor": "146/88 at the referring clinic, 12 May 2026",
    "proposed_by": JUNIOR_PHYSICIAN,
    "proposed_at": BASELINE_CLOSE.isoformat(),
    "ratified_by": None,
    "ratified_at": None,
}


def _started(db, kind=VisitKind.BASELINE):
    """v-1 under way, the way a tablet leaves it after the Start (§5.5)."""
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.start(KNOCK, kind, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, visit)
    conn.close()


def _resolved(db, kind=VisitKind.ROUTINE):
    """v-1 worked through and planned, but not yet closed — what the §5.8 gate
    reads. The loop lives here so no test carries one (testing-standards)."""
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.start(KNOCK, kind, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    for section in Section:
        visit.resolutions[section] = Resolution(section, content={"recorded": True})
    visit.plan = PLAN
    store.save(conn, visit)
    conn.close()


def test_the_visit_detail_names_the_visit_and_what_is_resolved(placed):
    # Arrange
    client, db = placed
    _started(db)
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, content={"bp-seated": "132/78"}
    )
    visit.resolutions[Section.NOTES] = Resolution(
        Section.NOTES, reason=Reason("nothing-further")
    )
    visit.plan = PLAN
    store.save(conn, visit)
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert
    assert result == {
        "visit_id": "v-1",
        "patient_id": "p-1",
        "patient_name": "Fatima Ali",
        "scheduled_for": "2026-08-28",
        "scheduled_reason": REASON,
        "state": "in_progress",
        "kind": "baseline",
        "junior_physician": JUNIOR_PHYSICIAN,
        "nurse": NURSE,
        "started_at": KNOCK.isoformat(),
        "closed_at": None,
        "closed_by": None,
        "closing_reason": None,
        "resolutions": {
            "VITALS": {
                "content": {"bp-seated": "132/78"},
                "reason": None,
            },
            "NOTES": {
                "content": None,
                "reason": {"row_id": "nothing-further", "free_text": None},
            },
        },
        "emergencies": [],
        "allergies": {"state": "unreachable", "value": None, "as_of": None},
        "shown": [],
        "dispositions": [],
        "flags": [],
        "plan": PLAN_JSON,
    }


def test_a_scheduled_visit_has_no_kind_yet(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert — the kind is settled by the Start, never scheduled (§5.5)
    assert result["kind"] is None
    assert result["resolutions"] == {}
    assert result["plan"] is None


def test_detail_for_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/visits/v-9")

    # Assert
    assert response.status_code == 404


def test_the_visit_detail_names_its_emergencies(placed):
    # Arrange
    client, db = placed
    _started(db)
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.enter_emergency(SET_AT)
    store.save(conn, visit)
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert — when it started, whether it ended, and whether it was written
    # down (§5.7). The timeline itself stays in the record, not the summary.
    assert result["emergencies"] == [
        {"started_at": SET_AT.isoformat(), "ended_at": None, "entries": []}
    ]


def test_the_visit_detail_carries_the_timeline_entries(placed):
    # Arrange
    client, db = placed
    _started(db)
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.enter_emergency(KNOCK)
    visit.record_timeline(EntryKind.DONE, "ambulance called", SET_AT)
    store.save(conn, visit)
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert — the record itself travels, and the Handover renders from it (§5.7)
    assert result["emergencies"] == [
        {
            "started_at": KNOCK.isoformat(),
            "ended_at": None,
            "entries": [
                {"kind": "done", "text": "ambulance called", "at": SET_AT.isoformat()}
            ],
        }
    ]


def test_the_visit_detail_carries_the_handover_allergy_line(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert — nobody prepared this Patient, and the Handover says so (§4.10)
    assert result["allergies"] == {"state": "unreachable", "value": None, "as_of": None}


def test_a_cached_allergy_line_reaches_the_visit_detail(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    store.cache_read(
        conn, "p-1", "allergies", Datum.present(("Penicillin",), as_of=READ_AT), READ_AT
    )
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert
    assert result["allergies"] == {
        "state": "present",
        "value": ["Penicillin"],
        "as_of": READ_AT.isoformat(),
    }


def test_starting_a_scheduled_visit_stamps_the_standing_pair(placed):
    # Arrange
    client, db = placed

    # Act
    response = _post(client, "/api/visits/v-1/start", json={"at": KNOCK.isoformat()})

    # Assert — copied from the assignment, not chosen at the door (§5.13)
    assert response.json() == {"visit_id": "v-1", "state": "in_progress", "kind": "baseline"}
    stored = store.load(_open(db), "v-1")
    assert (stored.junior_physician, stored.nurse) == (JUNIOR_PHYSICIAN, NURSE)


def test_a_completed_baseline_behind_her_starts_a_routine_visit(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    _completed_baseline(conn)
    conn.close()

    # Act
    response = _post(client, "/api/visits/v-1/start", json={"at": KNOCK.isoformat()})

    # Assert
    assert response.json()["kind"] == "routine"


def test_starting_without_a_time_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/start", json={})

    # Assert
    assert response.status_code == 400


def test_starting_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/start", json={"at": "at dawn"})

    # Assert
    assert response.status_code == 400


def test_starting_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-9/start", json={"at": KNOCK.isoformat()})

    # Assert
    assert response.status_code == 404


def test_starting_twice_is_refused(placed):
    # Arrange
    client, _ = placed
    started = {"at": KNOCK.isoformat()}
    _post(client, "/api/visits/v-1/start", json=started)

    # Act
    response = _post(client, "/api/visits/v-1/start", json=started)

    # Assert — In Progress has no road back to In Progress (§5.1)
    assert response.status_code == 409


def test_saving_section_content_resolves_it(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/vitals", json={"content": {"bp-seated": "132/78"}}
    )

    # Assert
    assert response.json() == {
        "visit_id": "v-1",
        "section": "VITALS",
        "resolved": "content",
    }
    stored = store.load(_open(db), "v-1").resolutions[Section.VITALS]
    assert stored.content == {"bp-seated": "132/78"}


def test_saving_a_structured_reason_resolves_it(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/notes", json={"reason": {"row_id": "nothing-further"}}
    )

    # Assert — resolved is not filled (§5.8)
    assert response.json()["resolved"] == "reason"


def test_saving_to_a_section_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/sections/triage", json={"content": {}})

    # Assert — the Protocol has eight sections, none may be absent (§4.2)
    assert response.status_code == 404


def test_saving_to_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-9/sections/vitals", json={"content": {}})

    # Assert
    assert response.status_code == 404


def test_saving_a_reason_not_on_the_sections_list_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/vitals", json={"reason": {"row_id": "patient-died"}}
    )

    # Assert — a Cancellation row explains no Vitals gap (§5.10)
    assert response.status_code == 400


def test_saving_other_without_its_words_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/notes", json={"reason": {"row_id": "other"}}
    )

    # Assert
    assert response.status_code == 400


def test_saving_a_reason_that_is_not_an_object_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/sections/notes", json={"reason": "tired"})

    # Assert
    assert response.status_code == 400


def test_saving_both_content_and_a_reason_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/notes",
        json={"content": {"late": "addition"}, "reason": {"row_id": "nothing-further"}},
    )

    # Assert — content or a reason for having none, never both (§5.8)
    assert response.status_code == 400


def test_saving_neither_content_nor_a_reason_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/sections/notes", json={})

    # Assert — and never neither (§5.8)
    assert response.status_code == 400


def test_saving_empty_content_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/sections/vitals", json={"content": {}})

    # Assert — empty content is not content (§5.8)
    assert response.status_code == 400


def test_the_care_plan_waits_for_the_other_seven(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/care_plan", json={"content": {"accepted": []}}
    )

    # Assert — assembled after all seven others, Notes included (§4.2)
    assert response.status_code == 409


def _seven_resolved(db):
    """Everything but the Care Plan, so it may assemble (§4.2). The loop lives
    here so no test carries one (testing-standards)."""
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.start(KNOCK, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    for section in Section:
        if section is not Section.CARE_PLAN:
            visit.resolutions[section] = Resolution(section, content={"recorded": True})
    store.save(conn, visit)
    conn.close()


def test_the_care_plan_assembles_after_the_other_seven(placed):
    # Arrange
    client, db = placed
    _seven_resolved(db)

    # Act
    response = _post(
        client, "/api/visits/v-1/sections/care_plan", json={"content": {"accepted": []}}
    )

    # Assert
    assert response.json()["resolved"] == "content"


def test_a_care_plan_carrying_plan_lines_sets_the_visits_plan(placed):
    # Arrange
    client, db = placed
    _seven_resolved(db)

    # Act
    response = _post(
        client,
        "/api/visits/v-1/sections/care_plan",
        json={"content": {"accepted": [], "plan": PLAN_JSON}},
    )

    # Assert — the final section emits the Between-Visit Plan (§4.8)
    assert response.json()["resolved"] == "content"
    assert _get(client, "/api/visits/v-1").json()["plan"] == PLAN_JSON


def test_a_care_plan_carrying_broken_plan_lines_is_refused(placed):
    # Arrange
    client, db = placed
    _seven_resolved(db)

    # Act
    response = _post(
        client,
        "/api/visits/v-1/sections/care_plan",
        json={"content": {"plan": {"schedule": [{"axis": "nope", "times_per_week": 3}]}}},
    )

    # Assert — a plan no machine can test is prose, not a plan (§4.8)
    assert response.status_code == 400


def test_a_care_plan_carrying_no_plan_lines_sets_no_plan(placed):
    # Arrange
    client, db = placed
    _seven_resolved(db)

    # Act
    response = _post(
        client, "/api/visits/v-1/sections/care_plan", json={"content": "done"}
    )

    # Assert — a resolution without lines is still a resolution; the gate,
    # not the save, decides whether the Visit may close
    assert response.json()["resolved"] == "content"
    assert _get(client, "/api/visits/v-1").json()["plan"] is None


def test_saving_to_a_closed_visit_is_refused(placed):
    # Arrange
    client, _ = placed
    _post(client, 
        "/api/visits/v-1/cancel",
        json={"row_id": "patient-died", "by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()},
    )

    # Act
    response = _post(client, 
        "/api/visits/v-1/sections/vitals", json={"content": {"bp-seated": "132/78"}}
    )

    # Assert — terminal states are immutable; an Addendum is the only write (§5.9)
    assert response.status_code == 409


def test_ending_early_closes_the_visit_with_its_reason(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/end-early",
        json={"row_id": "time-exhausted", "by": NURSE, "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "ended_early"}
    assert store.load(_open(db), "v-1").closing_reason == Reason("time-exhausted")


def test_ending_early_with_other_carries_its_words(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/end-early",
        json={
            "row_id": "other",
            "free_text": "the generator failed",
            "by": NURSE,
            "at": SET_AT.isoformat(),
        },
    )

    # Assert
    assert response.json()["state"] == "ended_early"


def test_ending_early_without_the_required_fields_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/end-early", json={"row_id": "time-exhausted"})

    # Assert
    assert response.status_code == 400


def test_ending_early_for_a_reason_not_on_the_list_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/end-early",
        json={"row_id": "because", "by": NURSE, "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.status_code == 400


def test_ending_early_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-9/end-early",
        json={"row_id": "time-exhausted", "by": NURSE, "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.status_code == 404


def test_ending_early_a_scheduled_visit_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/end-early",
        json={"row_id": "time-exhausted", "by": NURSE, "at": SET_AT.isoformat()},
    )

    # Assert — Ended Early is exited from In Progress, never Scheduled (§5.1)
    assert response.status_code == 409


def test_entering_emergency_suspends_the_visit(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "emergency"}


def test_entering_emergency_without_a_time_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/emergency", json={})

    # Assert
    assert response.status_code == 400


def test_entering_emergency_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/emergency", json={"at": "at dawn"})

    # Assert
    assert response.status_code == 400


def test_entering_emergency_for_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-9/emergency", json={"at": KNOCK.isoformat()})

    # Assert
    assert response.status_code == 404


def test_entering_emergency_twice_is_refused(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _started(db)
    entered = {"at": KNOCK.isoformat()}
    _post(client, "/api/visits/v-1/emergency", json=entered)

    # Act
    response = _post(client, "/api/visits/v-1/emergency", json=entered)

    # Assert — Emergency exits back to In Progress first (§5.1)
    assert response.status_code == 409


def test_writing_a_timeline_entry_during_the_emergency_appends_it(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act
    response = _post(
        client,
        "/api/visits/v-1/emergency/entries",
        json={"kind": "done", "text": "ambulance called", "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "entries": 1}
    stored = store.load(_open(db), "v-1")
    assert [entry.text for entry in stored.emergencies[-1].entries] == [
        "ambulance called"]


def test_a_timeline_entry_without_its_fields_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act
    response = _post(client, "/api/visits/v-1/emergency/entries", json={})

    # Assert
    assert response.status_code == 400


def test_a_timeline_entry_of_an_unknown_kind_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act — the timeline tags each entry observed or done, never a severity (§5.7)
    response = _post(
        client,
        "/api/visits/v-1/emergency/entries",
        json={"kind": "shouted", "text": "loud ward", "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.status_code == 400


def test_a_timeline_entry_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act
    response = _post(
        client,
        "/api/visits/v-1/emergency/entries",
        json={"kind": "done", "text": "ambulance called", "at": "at dusk"},
    )

    # Assert
    assert response.status_code == 400


def test_a_timeline_entry_predating_the_emergency_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act
    response = _post(
        client,
        "/api/visits/v-1/emergency/entries",
        json={"kind": "done", "text": "ambulance called", "at": READ_AT.isoformat()},
    )

    # Assert — a line cannot predate the record it belongs to (§5.7)
    assert response.status_code == 400


def test_a_timeline_entry_with_no_open_emergency_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(
        client,
        "/api/visits/v-1/emergency/entries",
        json={"kind": "done", "text": "ambulance called", "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.status_code == 409


def test_a_timeline_entry_for_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(
        client,
        "/api/visits/v-9/emergency/entries",
        json={"kind": "done", "text": "ambulance called", "at": SET_AT.isoformat()},
    )

    # Assert
    assert response.status_code == 404


def test_resuming_after_the_emergency_returns_the_visit_to_in_progress(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})
    _post(
        client,
        "/api/visits/v-1/emergency/entries",
        json={"kind": "done", "text": "ambulance called", "at": SET_AT.isoformat()},
    )

    # Act — Option A of the exit binary: the Patient stayed, the Protocol resumes
    response = _post(
        client, "/api/visits/v-1/emergency/resume", json={"at": SET_AT.isoformat()}
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "in_progress"}


def test_resuming_without_a_time_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act
    response = _post(client, "/api/visits/v-1/emergency/resume", json={})

    # Assert
    assert response.status_code == 400


def test_resuming_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)
    _post(client, "/api/visits/v-1/emergency", json={"at": KNOCK.isoformat()})

    # Act
    response = _post(client, "/api/visits/v-1/emergency/resume", json={"at": "at dusk"})

    # Assert
    assert response.status_code == 400


def test_resuming_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(
        client, "/api/visits/v-9/emergency/resume", json={"at": SET_AT.isoformat()}
    )

    # Assert
    assert response.status_code == 404


def test_resuming_without_an_emergency_is_refused(placed):
    # Arrange
    client, db = placed
    _started(db)

    # Act
    response = _post(
        client, "/api/visits/v-1/emergency/resume", json={"at": SET_AT.isoformat()}
    )

    # Assert — only an Emergency exits back to In Progress (§5.1)
    assert response.status_code == 409


def test_the_ended_early_reasons_list_the_real_rows_ending_in_other(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/reasons/ended_early").json()

    # Assert — §5.10's list as rendered, with the structural Other row last
    assert [row["id"] for row in result["rows"]] == [
        "patient-withdrew",
        "patient-too-unwell",
        "transferred-to-hospital",
        "patient-died-during-visit",
        "caregiver-absent",
        "household-unsafe",
        "team-called-away",
        "time-exhausted",
        "other",
    ]


def test_completing_a_routine_visit_closes_it(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _resolved(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()}
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "completed"}


def test_completing_without_the_required_fields_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN})

    # Assert
    assert response.status_code == 400


def test_completing_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN, "at": "at dusk"}
    )

    # Assert
    assert response.status_code == 400


def test_completing_a_visit_that_does_not_exist_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-9/complete", json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()}
    )

    # Assert
    assert response.status_code == 404


def test_completing_a_scheduled_visit_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()}
    )

    # Assert — Completed is entered from In Progress, never Scheduled (§5.1)
    assert response.status_code == 409


def test_completing_with_sections_unresolved_is_refused(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _started(db)

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()}
    )

    # Assert — every section resolved before Completed (§5.8)
    assert response.status_code == 409


def test_completing_without_a_plan_is_refused(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.start(KNOCK, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    for section in Section:
        visit.resolutions[section] = Resolution(section, content={"recorded": True})
    store.save(conn, visit)
    conn.close()

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()}
    )

    # Assert — no Care Plan ran, so no new plan was emitted (§5.6)
    assert response.status_code == 409


def test_completing_a_baseline_without_its_goal_is_refused(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _resolved(db, VisitKind.BASELINE)

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete", json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat()}
    )

    # Assert — a Baseline's final section proposes a Goal of Care (§5.8)
    assert response.status_code == 409


def test_completing_a_baseline_with_a_goal_that_does_not_hold_is_refused(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _resolved(db, VisitKind.BASELINE)

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete",
        json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat(), "goal": {"bands": []}},
    )

    # Assert — a Goal of Care with no band in it is not a target (§4.4)
    assert response.status_code == 400


def test_saving_without_a_body_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/visits/v-1/sections/vitals", bare=True)

    # Assert
    assert response.status_code == 400


def test_completing_with_a_goal_that_is_not_an_object_is_refused(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _resolved(db, VisitKind.BASELINE)

    # Act
    response = _post(
        client,
        "/api/visits/v-1/complete",
        json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat(), "goal": ["bands"]},
    )

    # Assert
    assert response.status_code == 400


def test_completing_a_baseline_with_its_goal_closes_it(placed):
    # Arrange
    client, _ = placed
    _, db = placed
    _resolved(db, VisitKind.BASELINE)

    # Act
    response = _post(client, 
        "/api/visits/v-1/complete",
        json={"by": JUNIOR_PHYSICIAN, "at": SET_AT.isoformat(), "goal": GOAL_JSON},
    )

    # Assert
    assert response.json() == {"visit_id": "v-1", "state": "completed"}


SUPERVISOR_WEEK = "2026-08-23"
"""The Sunday of the demo day's week — what the Silence Audit samples."""

TIER_DUE = KNOCK + timedelta(hours=72)
"""A Tier 1 item raised at the Start answers within 72 hours (§5.12)."""


def _tiered(db):
    """v-1 In Progress carrying one shown Tier 1 Recommendation — the least
    Arrange that raises a TIER route (§5.12)."""
    _started(db, VisitKind.ROUTINE)
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.shown = [
        Recommendation("r-1", "Increase metformin", EscalationTier.TIER_1,
                       executor="Junior Physician", provenance="SDGA 2024",
                       strength="strong")
    ]
    store.save(conn, visit)
    conn.close()


def test_the_inbox_lists_the_tier_item_awaiting_review(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    result = _get(client, "/api/inbox", params={"week": SUPERVISOR_WEEK}).json()

    # Assert — grouped by Patient, carrying the Visit's date and the item's due time
    assert result == {
        "week": SUPERVISOR_WEEK,
        "patients": [
            {
                "patient_id": "p-1",
                "patient_name": "Fatima Ali",
                "rows": [
                    {
                        "route": "tier",
                        "visit_id": "v-1",
                        "patient_id": "p-1",
                        "subject": "r-1",
                        "due_at": TIER_DUE.isoformat(),
                        "patient_name": "Fatima Ali",
                        "visit_date": "2026-08-28",
                    }
                ],
            }
        ],
    }


def test_an_empty_week_is_an_empty_inbox_not_an_error(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/inbox", params={"week": SUPERVISOR_WEEK}).json()

    # Assert
    assert result == {"week": SUPERVISOR_WEEK, "patients": []}


def test_the_inbox_defaults_its_week_to_the_current_one(placed):
    # Arrange
    client, _ = placed

    # Act
    result = _get(client, "/api/inbox").json()

    # Assert
    assert result == {"week": week_start(date.today()).isoformat(), "patients": []}


def test_an_inbox_with_a_week_that_is_not_a_date_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/inbox", params={"week": "friday"})

    # Assert
    assert response.status_code == 400


def test_a_verdict_closes_its_row(placed):
    # Arrange
    client, db = placed
    _tiered(db)
    conn = _open(db)
    store.record_verdict(conn, VerdictKey("v-1", Route.TIER, "r-1"),
                         Verdict(agreed=True, by=SUPERVISOR, at=SET_AT))
    conn.close()

    # Act
    result = _get(client, "/api/inbox", params={"week": SUPERVISOR_WEEK}).json()

    # Assert — the Verdict removed the only row, so the Patient is gone too (ADR 0009)
    assert result["patients"] == []


def test_agreeing_closes_the_routed_item(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "tier", "subject": "r-1",
        "agreed": True, "by": SUPERVISOR, "at": SET_AT.isoformat(),
    })

    # Assert
    assert response.json() == {
        "visit_id": "v-1", "route": "tier", "subject": "r-1", "closed": True,
    }
    remaining = _get(client, "/api/inbox", params={"week": SUPERVISOR_WEEK}).json()
    assert remaining["patients"] == []


def test_a_disagreement_without_its_note_is_refused(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "tier", "subject": "r-1",
        "agreed": False, "by": SUPERVISOR, "at": SET_AT.isoformat(),
    })

    # Assert — a disagreement nobody can read is a mark, not an answer (§5.12)
    assert response.status_code == 400


def test_a_disagreement_with_its_note_closes_the_routed_item(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "tier", "subject": "r-1",
        "agreed": False, "by": SUPERVISOR, "at": SET_AT.isoformat(),
        "note": "Dose already at ceiling — holding is correct",
    })

    # Assert
    assert response.json()["closed"] is True
    remaining = _get(client, "/api/inbox", params={"week": SUPERVISOR_WEEK}).json()
    assert remaining["patients"] == []


def test_a_note_that_is_not_words_is_refused(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "tier", "subject": "r-1",
        "agreed": True, "by": SUPERVISOR, "at": SET_AT.isoformat(), "note": 42,
    })

    # Assert
    assert response.status_code == 400


def test_a_ratification_disagreement_is_recorded_but_stays_open(placed):
    # Arrange — a Baseline proposing its target raises the second route (§4.4)
    client, db = placed
    _started(db, VisitKind.BASELINE)
    conn = _open(db)
    store.propose_goal(conn, GOAL)
    conn.close()

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "ratification", "subject": "goal-of-care",
        "agreed": False, "by": SUPERVISOR, "at": SET_AT.isoformat(),
        "note": "Band too tight for her frailty — repropose wider",
    })

    # Assert — disagreeing leaves no ratified target, so the item stays open (ADR 0009)
    assert response.json()["closed"] is False
    remaining = _get(client, "/api/inbox", params={"week": SUPERVISOR_WEEK}).json()
    assert [row["route"] for row in remaining["patients"][0]["rows"]] == ["ratification"]


def test_a_verdict_without_its_fields_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/inbox/verdict", json={"agreed": True})

    # Assert
    assert response.status_code == 400


def test_a_verdict_whose_agreement_is_not_a_boolean_is_refused(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "tier", "subject": "r-1",
        "agreed": "yes", "by": SUPERVISOR, "at": SET_AT.isoformat(),
    })

    # Assert
    assert response.status_code == 400


def test_a_verdict_on_an_unknown_route_is_refused(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act — four routes, and no fifth (§5.12)
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "triage", "subject": "r-1",
        "agreed": True, "by": SUPERVISOR, "at": SET_AT.isoformat(),
    })

    # Assert
    assert response.status_code == 400


def test_a_verdict_at_a_time_that_is_not_a_datetime_is_refused(placed):
    # Arrange
    client, db = placed
    _tiered(db)

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-1", "route": "tier", "subject": "r-1",
        "agreed": True, "by": SUPERVISOR, "at": "at dusk",
    })

    # Assert
    assert response.status_code == 400


def test_a_verdict_for_an_item_that_is_not_open_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/inbox/verdict", json={
        "visit_id": "v-9", "route": "tier", "subject": "r-9",
        "agreed": True, "by": SUPERVISOR, "at": SET_AT.isoformat(),
    })

    # Assert
    assert response.status_code == 404


def test_the_goal_read_names_the_proposed_bands(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    store.propose_goal(conn, GOAL)
    conn.close()

    # Act
    result = _get(client, "/api/patients/p-1/goal").json()

    # Assert — the lineage travels with the number, or ratification is a rubber stamp (N5)
    assert result == {
        "patient_id": "p-1",
        "bands": [
            {
                "axis": "systolic",
                "floor": 110,
                "ceiling": 135,
                "rationale": "home band, frailty considered",
            }
        ],
        "lineage": "Proposed at the Baseline Visit from the household's own readings",
        "office_anchor": "146/88 at the referring clinic, 12 May 2026",
        "proposed_by": JUNIOR_PHYSICIAN,
        "proposed_at": BASELINE_CLOSE.isoformat(),
        "ratified_by": None,
        "ratified_at": None,
    }


def test_a_goal_for_a_patient_with_none_proposed_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _get(client, "/api/patients/p-1/goal")

    # Assert
    assert response.status_code == 404


def test_ratifying_records_the_supervisor_and_the_time(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    store.propose_goal(conn, GOAL)
    conn.close()

    # Act — agreeing is ratifying, and the Goal carries it (§5.12, ADR 0009)
    response = _post(client, "/api/patients/p-1/goal/ratify",
                     json={"by": SUPERVISOR, "at": SET_AT.isoformat()})

    # Assert
    assert response.json() == {"patient_id": "p-1", "ratified_by": SUPERVISOR}
    assert store.goal(_open(db), "p-1").is_ratified


def test_ratifying_without_its_fields_is_refused(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/patients/p-1/goal/ratify", json={"by": SUPERVISOR})

    # Assert
    assert response.status_code == 400


def test_ratifying_with_no_proposal_is_a_404(placed):
    # Arrange
    client, _ = placed

    # Act
    response = _post(client, "/api/patients/p-1/goal/ratify",
                     json={"by": SUPERVISOR, "at": SET_AT.isoformat()})

    # Assert
    assert response.status_code == 404


def test_ratifying_twice_is_refused(placed):
    # Arrange
    client, db = placed
    conn = _open(db)
    store.propose_goal(conn, GOAL)
    conn.close()
    ratify = {"by": SUPERVISOR, "at": SET_AT.isoformat()}
    _post(client, "/api/patients/p-1/goal/ratify", json=ratify)

    # Act
    response = _post(client, "/api/patients/p-1/goal/ratify", json=ratify)

    # Assert — a decision carries one name (§5.13)
    assert response.status_code == 409


def test_the_visit_detail_carries_its_shown_dispositions_and_flags(placed):
    # Arrange
    client, db = placed
    _started(db, VisitKind.ROUTINE)
    conn = _open(db)
    visit = store.load(conn, "v-1")
    visit.shown = [
        Recommendation("r-1", "Increase metformin", EscalationTier.TIER_1,
                       executor="Junior Physician", provenance="SDGA 2024",
                       strength="strong")
    ]
    visit.dispositions = [
        Disposition("r-1", Outcome.OVERRIDDEN, JUNIOR_PHYSICIAN, SET_AT,
                    OverrideLevel.COULD_NOT_ACT, Reason("deferred-to-supervisor"))
    ]
    visit.flags = [Flag("r-1", JUNIOR_PHYSICIAN, SET_AT, "please confirm the dose")]
    store.save(conn, visit)
    conn.close()

    # Act
    result = _get(client, "/api/visits/v-1").json()

    # Assert — what the Supervisor reads beside the routed item (N5, §5.11)
    assert result["shown"] == [
        {
            "id": "r-1",
            "text": "Increase metformin",
            "tier": "tier_1",
            "executor": "Junior Physician",
            "provenance": "SDGA 2024",
            "strength": "strong",
        }
    ]
    assert result["dispositions"] == [
        {
            "recommendation_id": "r-1",
            "outcome": "overridden",
            "by": JUNIOR_PHYSICIAN,
            "at": SET_AT.isoformat(),
            "level": "could_not_act",
            "reason": {"row_id": "deferred-to-supervisor", "free_text": None},
        }
    ]
    assert result["flags"] == [
        {
            "subject": "r-1",
            "by": JUNIOR_PHYSICIAN,
            "at": SET_AT.isoformat(),
            "note": "please confirm the dose",
        }
    ]


QUEUE_AT = datetime(2026, 8, 28, 19, 0)
"""When the Field Team presses Transmit — evening, back where there is signal (§4.10)."""

QUEUE_DUE = SET_AT + timedelta(hours=72)
"""A Tier 1 answer owed within 72 hours of the close (§4.9, §5.11)."""


@pytest.fixture
def unserved(tmp_path):
    """An empty file with a client over it. Queue tests enrol Patients the
    fixture EMR knows, so a send either lands or is refused for a stated reason."""
    db = tmp_path / "noor.db"
    store.connect(db).close()
    transport = httpx.ASGITransport(app=api.build(db))
    yield httpx.AsyncClient(transport=transport, base_url="http://noor"), db


def _queued(db, visit_id="v-1", patient_id="p-001", name="Fatima Al-Harbi",
            shown=(), dispositions=()):
    """A closed Routine Visit waiting on the queue — the least Arrange that has
    anything to send. p-001's record accepts; p-005's refuses (§4.9)."""
    conn = _open(db)
    store.add_patient(conn, patient_id, name, ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit = Visit(visit_id, patient_id)
    store.schedule(conn, visit, DAY, REASON)
    visit.start(KNOCK, VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    for section in Section:
        visit.resolutions[section] = Resolution(section, content={"recorded": True})
    visit.shown = list(shown)
    visit.dispositions = list(dispositions)
    visit.plan = PLAN
    visit.complete(by=JUNIOR_PHYSICIAN, at=SET_AT)
    store.save(conn, visit)
    conn.close()


def test_an_empty_queue_reads_as_no_visits_and_no_addenda(unserved):
    # Arrange
    client, _ = unserved

    # Act
    result = _get(client, "/api/queue").json()

    # Assert
    assert result == {"visits": [], "addenda": []}


def test_a_completed_visit_waits_in_the_queue_with_its_write_back_items(unserved):
    # Arrange
    client, db = unserved
    _queued(
        db,
        shown=[Recommendation("r-1", "Increase metformin", EscalationTier.TIER_1,
                              executor="Junior Physician", provenance="SDGA 2024",
                              strength="strong")],
        dispositions=[Disposition("r-1", Outcome.ACCEPTED,
                                  by=JUNIOR_PHYSICIAN, at=SET_AT)],
    )

    # Act
    result = _get(client, "/api/queue").json()

    # Assert — the envelope, and the owner and due time its answer carries (§4.9)
    assert result == {
        "visits": [
            {
                "visit_id": "v-1",
                "patient_id": "p-001",
                "patient_name": "Fatima Al-Harbi",
                "state": "completed",
                "scheduled_for": "2026-08-28",
                "scheduled_reason": REASON,
                "closed_at": SET_AT.isoformat(),
                "closed_by": JUNIOR_PHYSICIAN,
                "refused_at": None,
                "refusal": None,
                "items": [
                    {
                        "kind": "VISIT_OUTCOME",
                        "payload": {
                            "state": "completed",
                            "started_at": KNOCK.isoformat(),
                            "closed_by": JUNIOR_PHYSICIAN,
                            "closed_at": SET_AT.isoformat(),
                            "reason": None,
                            "emergencies": [],
                            "sections_not_run": [],
                        },
                    },
                    {
                        "kind": "OBSERVATIONS",
                        "payload": {
                            "vitals": {"recorded": True},
                            "examination": {"recorded": True},
                            "home_readings": [],
                        },
                    },
                    {"kind": "SELF_CARE_FINDINGS", "payload": {"recorded": True}},
                    {"kind": "RECONCILIATION", "payload": {"recorded": True}},
                    {
                        "kind": "RECOMMENDATIONS",
                        "payload": {
                            "recommendations": [
                                {
                                    "id": "r-1",
                                    "text": "Increase metformin",
                                    "tier": EscalationTier.TIER_1.value,
                                    "executor": "Junior Physician",
                                    "provenance": "SDGA 2024",
                                    "strength": "strong",
                                    "status": "accepted",
                                    "reason": None,
                                    "response": {
                                        "owner": api.SUPERVISOR,
                                        "due_at": QUEUE_DUE.isoformat(),
                                    },
                                }
                            ]
                        },
                    },
                    {
                        "kind": "BETWEEN_VISIT_PLAN",
                        "payload": {
                            "titration": [
                                {
                                    "axis": "systolic",
                                    "comparison": "above",
                                    "value": 150,
                                    "action": "step up the dose",
                                }
                            ],
                            "schedule": [
                                {"axis": "systolic", "times_per_week": 3}
                            ],
                            "stop_rules": [
                                {
                                    "axis": "systolic",
                                    "comparison": "above",
                                    "value": 180,
                                    "action": "call the Supervisor",
                                }
                            ],
                        },
                    },
                ],
            }
        ],
        "addenda": [],
    }


def test_an_addendum_waits_in_the_queue_with_its_author_and_time(unserved):
    # Arrange
    client, db = unserved
    _queued(db)
    conn = _open(db)
    store.add_addendum(conn, Addendum("a-1", "v-1", "BP rechecked on the doorstep",
                                      author=JUNIOR_PHYSICIAN, written_at=QUEUE_AT))
    conn.close()

    # Act
    result = _get(client, "/api/queue").json()

    # Assert — its own send, after the Visit's, asking for nothing (§5.9)
    assert result["addenda"] == [
        {
            "addendum_id": "a-1",
            "visit_id": "v-1",
            "patient_id": "p-001",
            "patient_name": "Fatima Al-Harbi",
            "text": "BP rechecked on the doorstep",
            "author": JUNIOR_PHYSICIAN,
            "written_at": QUEUE_AT.isoformat(),
            "refused_at": None,
            "refusal": None,
        }
    ]


def test_a_refused_visit_stays_queued_with_what_the_emr_said(unserved):
    # Arrange — the last attempt was refused, and the refusal was recorded
    client, db = unserved
    _queued(db, visit_id="v-5", patient_id="p-005", name="Sara Al-Dossari")
    conn = _open(db)
    store.mark_refused(conn, "v-5", QUEUE_AT, "the EMR refused the write for 'p-005'")
    conn.close()

    # Act
    result = _get(client, "/api/queue").json()

    # Assert — still waiting, carrying the refusal instead of hiding it (§4.10)
    [visit] = result["visits"]
    assert (visit["refused_at"], visit["refusal"]) == (
        QUEUE_AT.isoformat(), "the EMR refused the write for 'p-005'")


def test_dispatching_the_queue_sends_every_queued_visit(unserved):
    # Arrange
    client, db = unserved
    _queued(db)

    # Act
    response = _post(client, "/api/queue/dispatch",
                     json={"at": QUEUE_AT.isoformat()})

    # Assert — named as sent, and gone from the queue afterwards
    assert response.json() == {"sent": ["v-1"], "failed": []}
    conn = _open(db)
    assert store.pending(conn) == []
    conn.close()


def test_a_visit_the_emr_refuses_on_dispatch_stays_queued_with_the_reason(unserved):
    # Arrange
    client, db = unserved
    _queued(db, visit_id="v-5", patient_id="p-005", name="Sara Al-Dossari")

    # Act
    response = _post(client, "/api/queue/dispatch",
                     json={"at": QUEUE_AT.isoformat()})

    # Assert — the refusal is named, and the Visit still waits afterwards
    assert response.json() == {
        "sent": [],
        "failed": [
            {"id": "v-5", "refusal": "the EMR refused the write for 'p-005'"}
        ],
    }
    conn = _open(db)
    assert store.queued(conn) == ["v-5"]
    conn.close()


def test_transmitting_one_visit_leaves_the_rest_queued(unserved):
    # Arrange
    client, db = unserved
    _queued(db)
    _queued(db, visit_id="v-9", patient_id="p-009", name="Noura Al-Otaibi")

    # Act
    response = _post(client, "/api/visits/v-1/dispatch",
                     json={"at": QUEUE_AT.isoformat()})

    # Assert — one envelope sent, the other still waiting
    assert response.json() == {"visit_id": "v-1", "sent": True}
    conn = _open(db)
    assert store.queued(conn) == ["v-9"]
    conn.close()


def test_transmitting_a_visit_the_emr_refuses_names_the_refusal(unserved):
    # Arrange
    client, db = unserved
    _queued(db, visit_id="v-5", patient_id="p-005", name="Sara Al-Dossari")

    # Act
    response = _post(client, "/api/visits/v-5/dispatch",
                     json={"at": QUEUE_AT.isoformat()})

    # Assert — refused, recorded, and still queued for the next attempt
    assert response.json() == {
        "visit_id": "v-5",
        "sent": False,
        "refusal": "the EMR refused the write for 'p-005'",
    }
    conn = _open(db)
    assert store.queued(conn) == ["v-5"]
    conn.close()


def test_transmitting_a_visit_that_does_not_exist_is_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _post(client, "/api/visits/v-9/dispatch",
                     json={"at": QUEUE_AT.isoformat()})

    # Assert
    assert response.status_code == 404


def test_transmitting_a_visit_that_has_not_closed_is_refused(unserved):
    # Arrange — Scheduled, so there is nothing to report about it yet (§4.9)
    client, db = unserved
    conn = _open(db)
    store.add_patient(conn, "p-001", "Fatima Al-Harbi", ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.schedule(conn, Visit("v-1", "p-001"), DAY, REASON)
    conn.close()

    # Act
    response = _post(client, "/api/visits/v-1/dispatch",
                     json={"at": QUEUE_AT.isoformat()})

    # Assert
    assert response.status_code == 409


def test_dispatching_the_queue_without_a_body_is_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _post(client, "/api/queue/dispatch", bare=True)

    # Assert
    assert response.status_code == 400


def test_transmitting_a_visit_without_a_body_is_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _post(client, "/api/visits/v-1/dispatch", bare=True)

    # Assert
    assert response.status_code == 400


def _closed_early(db, visit_id="v-2", patient_id="p-002", name="Layla Al-Otaibi"):
    """A Visit that Ended Early — terminal, so it takes an Addendum (§5.9)."""
    conn = _open(db)
    store.add_patient(conn, patient_id, name, ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit = Visit(visit_id, patient_id)
    store.schedule(conn, visit, DAY, REASON)
    visit.start(KNOCK, VisitKind.ROUTINE,
                junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("patient-asked-to-stop", None), JUNIOR_PHYSICIAN, SET_AT)
    store.save(conn, visit)
    conn.close()


def _cancelled(db, visit_id="v-3", patient_id="p-003", name="Noura Al-Shammari"):
    """A Cancelled Visit — terminal, so it takes an Addendum (§5.9)."""
    conn = _open(db)
    store.add_patient(conn, patient_id, name, ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit = Visit(visit_id, patient_id)
    store.schedule(conn, visit, DAY, REASON)
    visit.cancel(Reason("patient-not-at-home", None), NURSE, SET_AT)
    store.save(conn, visit)
    conn.close()


def test_an_addendum_is_committed_to_a_completed_visit_with_its_author_and_time(
    unserved,
):
    # Arrange
    client, db = unserved
    _queued(db)

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "BP rechecked on the doorstep, 128/82",
        "author": JUNIOR_PHYSICIAN,
        "at": QUEUE_AT.isoformat(),
    })

    # Assert — kept, queued for its own send, and the closed Visit untouched
    body = response.json()
    assert response.status_code == 200
    conn = _open(db)
    [kept] = store.addenda(conn, "v-1")
    assert (kept.text, kept.author, kept.written_at) == (
        "BP rechecked on the doorstep, 128/82", JUNIOR_PHYSICIAN, QUEUE_AT)
    assert body["addendum_id"] == kept.id
    assert [row.addendum_id for row in store.pending_addenda(conn)] == [kept.id]
    assert store.load(conn, "v-1").flags == []
    conn.close()


def test_an_addendum_is_committed_to_a_visit_that_ended_early(unserved):
    # Arrange
    client, db = unserved
    _closed_early(db)

    # Act
    response = _post(client, "/api/visits/v-2/addenda", json={
        "text": "Meter read from the doorstep before leaving",
        "author": NURSE,
        "at": QUEUE_AT.isoformat(),
    })

    # Assert — Ended Early is terminal, so the addition lands (§5.9)
    assert response.status_code == 200
    conn = _open(db)
    assert [kept.text for kept in store.addenda(conn, "v-2")] == [
        "Meter read from the doorstep before leaving"]
    conn.close()


def test_an_addendum_is_committed_to_a_cancelled_visit(unserved):
    # Arrange
    client, db = unserved
    _cancelled(db)

    # Act
    response = _post(client, "/api/visits/v-3/addenda", json={
        "text": "Neighbour said the Patient moved floors",
        "author": NURSE,
        "at": QUEUE_AT.isoformat(),
    })

    # Assert — Cancelled is terminal, so the addition lands (§5.9)
    assert response.status_code == 200
    conn = _open(db)
    assert [kept.text for kept in store.addenda(conn, "v-3")] == [
        "Neighbour said the Patient moved floors"]
    conn.close()


def test_an_addendum_to_a_visit_still_open_is_refused_and_nothing_is_kept(placed):
    # Arrange — Scheduled, so an addition to it is the section write (§5.9)
    client, db = placed

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "correction typed a moment too late",
        "author": JUNIOR_PHYSICIAN,
        "at": SET_AT.isoformat(),
    })

    # Assert — refused before anything was written, and nothing was kept
    assert response.status_code == 409
    conn = _open(db)
    assert store.addenda(conn, "v-1") == []
    assert store.load(conn, "v-1").flags == []
    conn.close()


def test_an_addendum_to_a_visit_that_does_not_exist_is_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _post(client, "/api/visits/v-9/addenda", json={
        "text": "an addition with nowhere to attach",
        "author": JUNIOR_PHYSICIAN,
        "at": QUEUE_AT.isoformat(),
    })

    # Assert
    assert response.status_code == 404


def test_an_addendum_with_only_blank_text_is_refused(unserved):
    # Arrange — whitespace passes the presence check, so the domain refuses it
    client, db = unserved
    _queued(db)

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "   ",
        "author": JUNIOR_PHYSICIAN,
        "at": QUEUE_AT.isoformat(),
    })

    # Assert — an addition with nothing to add (§5.9), and nothing kept
    assert response.status_code == 400
    conn = _open(db)
    assert store.addenda(conn, "v-1") == []
    conn.close()


def test_an_addendum_with_only_a_blank_author_is_refused(unserved):
    # Arrange
    client, db = unserved
    _queued(db)

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "BP rechecked on the doorstep",
        "author": "  ",
        "at": QUEUE_AT.isoformat(),
    })

    # Assert — every addition carries who wrote it (§5.13), and nothing kept
    assert response.status_code == 400
    conn = _open(db)
    assert store.addenda(conn, "v-1") == []
    conn.close()


def test_an_addendum_without_its_fields_is_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={"text": "half a write"})

    # Assert
    assert response.status_code == 400


def test_an_addendum_at_a_time_that_is_not_a_datetime_is_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "BP rechecked on the doorstep",
        "author": JUNIOR_PHYSICIAN,
        "at": "after lunch",
    })

    # Assert
    assert response.status_code == 400


def test_a_flagged_addendum_reaches_the_supervisor_as_a_manual_flag(unserved):
    # Arrange
    client, db = unserved
    _queued(db)

    # Act — the author also sends it to the Supervisor (§5.9)
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "evening dose watched, review the plan",
        "author": JUNIOR_PHYSICIAN,
        "at": QUEUE_AT.isoformat(),
        "flagged": True,
    })

    # Assert — stored flagged, and a manual flag on the closed Visit (§5.12)
    body = response.json()
    assert response.status_code == 200
    assert body["flagged"] is True
    conn = _open(db)
    [kept] = store.addenda(conn, "v-1")
    assert kept.flagged is True
    assert [flag.subject for flag in store.load(conn, "v-1").flags] == [kept.id]
    conn.close()


def test_an_unflagged_addendum_leaves_the_closed_visit_without_a_flag(unserved):
    # Arrange
    client, db = unserved
    _queued(db)

    # Act
    response = _post(client, "/api/visits/v-1/addenda", json={
        "text": "meter serial noted for the record",
        "author": NURSE,
        "at": QUEUE_AT.isoformat(),
        "flagged": False,
    })

    # Assert
    assert response.status_code == 200
    conn = _open(db)
    assert store.load(conn, "v-1").flags == []
    conn.close()


def test_prior_addenda_read_oldest_first_with_author_text_time_and_flag(unserved):
    # Arrange — two committed, the later one flagged
    client, db = unserved
    _queued(db)
    first = _post(client, "/api/visits/v-1/addenda", json={
        "text": "first note",
        "author": NURSE,
        "at": QUEUE_AT.isoformat(),
    }).json()["addendum_id"]
    second = _post(client, "/api/visits/v-1/addenda", json={
        "text": "second note",
        "author": JUNIOR_PHYSICIAN,
        "at": (QUEUE_AT + timedelta(hours=1)).isoformat(),
        "flagged": True,
    }).json()["addendum_id"]

    # Act
    result = _get(client, "/api/visits/v-1/addenda").json()

    # Assert — oldest first, carrying who wrote what and when (§5.9, §5.13)
    assert result == {
        "visit_id": "v-1",
        "addenda": [
            {
                "addendum_id": first,
                "text": "first note",
                "author": NURSE,
                "written_at": QUEUE_AT.isoformat(),
                "flagged": False,
            },
            {
                "addendum_id": second,
                "text": "second note",
                "author": JUNIOR_PHYSICIAN,
                "written_at": (QUEUE_AT + timedelta(hours=1)).isoformat(),
                "flagged": True,
            },
        ],
    }


def test_a_visit_with_no_addenda_reads_as_empty(unserved):
    # Arrange
    client, db = unserved
    _queued(db)

    # Act
    result = _get(client, "/api/visits/v-1/addenda").json()

    # Assert
    assert result == {"visit_id": "v-1", "addenda": []}


def test_addenda_for_a_visit_that_does_not_exist_are_refused(unserved):
    # Arrange
    client, _ = unserved

    # Act
    response = _get(client, "/api/visits/v-9/addenda")

    # Assert
    assert response.status_code == 404
