"""web_plan §4.4: Home Readings has its own page, reached from the Visit, and is not one
of the eight. §4.8: every reading records which source it came from."""
from datetime import datetime

import pytest

from noor import store
from noor.domain.states import VisitKind
from noor.domain.visit import Visit
from noor.domain.vitals import Source

KNOCK = datetime(2026, 8, 28, 9, 20)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


@pytest.fixture
def visit(conn, day):
    """One In Progress Visit for a Patient with both conditions, so the page offers the
    glucose measurement and the seated blood pressure. `conn`, `client` and `day` come from
    `tests/web/conftest.py` — do not redefine them here."""
    store.add_patient(conn, "p-1", "Fatima Al-Otaibi", ["diabetes", "hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record = Visit("v-1", "p-1")
    store.schedule(conn, record, day, "Three-month review")
    record.start(KNOCK, VisitKind.ROUTINE,
                 junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, record)
    return record


def test_the_page_offers_the_measurements_this_patients_conditions_ask_for(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/home-readings")

    # Assert
    assert answer.status_code == 200
    assert "Capillary blood glucose (mmol/L)" in answer.text
    assert "Blood pressure, seated (mmHg)" in answer.text


def test_the_page_offers_neither_of_the_measurements_taken_once_at_enrolment(
        client, visit):
    """A between-Visit series is a series. Height and the other-arm blood pressure are
    `baseline_only` precisely because they are taken once and do not recur, so a device
    memory holding a series of them is not a thing that happens."""
    # Arrange / Act
    answer = client.get("/visits/v-1/home-readings")

    # Assert
    assert "Height" not in answer.text
    assert "other arm" not in answer.text


def test_the_page_offers_both_sources_and_neither_is_preselected(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/home-readings")

    # Assert
    assert "Read off the device" in answer.text
    assert "Copied from a Caregiver" in answer.text
    assert "checked" not in answer.text


def test_an_empty_series_says_so_rather_than_showing_an_empty_list(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/home-readings")

    # Assert
    assert "nothing has been entered yet" in answer.text


def test_a_reading_is_recorded_against_the_visit_with_its_source(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/home-readings",
                         data={"measurement": "capillary-glucose", "value": "7.2",
                               "taken_at": "2026-08-26T07:30", "source": "device memory"},
                         follow_redirects=False)

    # Assert
    assert answer.headers["location"] == "/visits/v-1/home-readings"
    stored = store.load(conn, "v-1").home_readings
    assert len(stored) == 1
    assert stored[0].measurement == "capillary-glucose"
    assert stored[0].value == "7.2"
    assert stored[0].taken_at == datetime(2026, 8, 26, 7, 30)
    assert stored[0].source is Source.DEVICE_MEMORY


def test_a_second_reading_of_the_same_measurement_is_a_second_reading(client, conn, visit):
    """A series, not a field. Two readings of the same axis on different days are the whole
    point of §4.8, and the second must not overwrite the first."""
    # Arrange
    client.post("/visits/v-1/home-readings",
                data={"measurement": "capillary-glucose", "value": "7.2",
                      "taken_at": "2026-08-26T07:30", "source": "device memory"},
                follow_redirects=False)

    # Act
    client.post("/visits/v-1/home-readings",
                data={"measurement": "capillary-glucose", "value": "9.1",
                      "taken_at": "2026-08-27T07:15", "source": "device memory"},
                follow_redirects=False)

    # Assert
    assert [r.value for r in store.load(conn, "v-1").home_readings] == ["7.2", "9.1"]


def test_a_recorded_series_reads_back_on_the_page(client, visit):
    # Arrange
    client.post("/visits/v-1/home-readings",
                data={"measurement": "capillary-glucose", "value": "7.2",
                      "taken_at": "2026-08-26T07:30", "source": "Caregiver paper log"},
                follow_redirects=False)

    # Act
    answer = client.get("/visits/v-1/home-readings")

    # Assert
    assert "7.2 mmol/L" in answer.text
    assert "07:30, 26 August" in answer.text
    assert "Caregiver paper log" in answer.text
    assert "Home Readings collected on this Visit: 1." in answer.text


def test_a_reading_with_no_value_is_refused_by_the_domain(client, conn, visit):
    """`HomeReading.__post_init__` raises `VitalsError`. The handler does not re-check it —
    one rule, one place."""
    # Arrange / Act
    answer = client.post("/visits/v-1/home-readings",
                         data={"measurement": "capillary-glucose", "value": "",
                               "taken_at": "2026-08-26T07:30", "source": "device memory"})

    # Assert
    assert answer.status_code == 400
    assert "a reading with no value is not a reading" in answer.text
    assert store.load(conn, "v-1").home_readings == []


def test_a_measurement_this_patient_is_not_asked_for_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/home-readings",
                         data={"measurement": "height", "value": "170",
                               "taken_at": "2026-08-26T07:30", "source": "device memory"})

    # Assert
    assert answer.status_code == 400
    assert "not one of the measurements" in answer.text


def test_a_time_that_is_not_a_time_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/home-readings",
                         data={"measurement": "capillary-glucose", "value": "7.2",
                               "taken_at": "last Tuesday", "source": "device memory"})

    # Assert
    assert answer.status_code == 400
    assert "when it was taken" in answer.text


def test_a_reading_with_no_source_on_it_is_refused(client, conn, visit):
    """§4.8 requires the source of every reading, so a reading without one is not a
    reading Noor can hold."""
    # Arrange / Act
    answer = client.post("/visits/v-1/home-readings",
                         data={"measurement": "capillary-glucose", "value": "7.2",
                               "taken_at": "2026-08-26T07:30", "source": ""})

    # Assert
    assert answer.status_code == 400
    assert "where this reading came from" in answer.text


def test_the_page_is_refused_while_the_visit_is_still_scheduled(client, conn, day):
    """The readings are collected on arrival (§4.8). Before the Start nobody has arrived."""
    # Arrange
    store.add_patient(conn, "p-2", "Ahmed Al-Harbi", ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.schedule(conn, Visit("v-2", "p-2"), day, "Three-month review")

    # Act
    answer = client.get("/visits/v-2/home-readings")

    # Assert
    assert answer.status_code == 400
    assert "Scheduled" in answer.text
