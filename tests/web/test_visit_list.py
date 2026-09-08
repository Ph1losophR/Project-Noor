"""The Visit List: the day's roster as a page (web_plan §4.1)."""
from datetime import datetime

import pytest

from noor import store
from noor.domain.states import Datum
from noor.domain.visit import Visit

SEVEN = "2026-08-28T07:00:00"


@pytest.fixture
def rostered(conn, day):
    """One Patient with one Scheduled Visit on the day the client thinks it is, and
    nothing prepared for it."""
    store.add_patient(conn, "p-001", "Fatima Al-Harbi", ["hypertension"],
                      junior_physician="Dr Layla Al-Amri",
                      nurse="Nurse Huda Al-Zahrani")
    store.schedule(conn, Visit("v-001", "p-001"), day, "Three-month review")


def test_the_day_is_the_page_and_the_row_carries_all_four_of_its_facts(client, rostered):
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert
    assert answer.status_code == 200
    assert "Friday 28 August 2026" in answer.text
    assert "Fatima Al-Harbi" in answer.text
    assert "Three-month review" in answer.text
    assert "Scheduled" in answer.text
    assert "Baseline Visit" in answer.text


def test_a_row_links_to_the_visit_it_is_about(client, rostered):
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert
    assert 'href="/visits/v-001"' in answer.text


def test_a_visit_nobody_prepared_still_links_to_its_own_page(client, rostered):
    """§5.2 and N4: readiness never keeps a row from opening."""
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert
    assert "The office prepared nothing for this Visit." in answer.text
    assert 'href="/visits/v-001"' in answer.text


def test_a_row_states_what_the_office_could_not_read(client, conn, rostered):
    # Arrange
    store.cache_read(conn, "p-001", "prescribed", Datum.unreachable(),
                     datetime.fromisoformat(SEVEN))

    # Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert
    assert "Could not be read: the prescribed list." in answer.text


def test_no_day_in_the_address_means_today(client, rostered):
    # Arrange / Act — the client's clock is fixed at 2026-08-28 09:30
    answer = client.get("/visits")

    # Assert
    assert "Fatima Al-Harbi" in answer.text


def test_a_day_with_nothing_on_it_says_so_rather_than_showing_an_empty_list(
        client, rostered):
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-29")

    # Assert
    assert answer.status_code == 200
    assert "The office scheduled no Visits for this day." in answer.text
    assert "Fatima Al-Harbi" not in answer.text


def test_a_day_nobody_could_have_written_is_refused_in_words(client):
    # Arrange / Act
    answer = client.get("/visits?day=the-28th")

    # Assert — a 500 says Noor is broken; this says what a day looks like
    assert answer.status_code == 400
    assert "Not a day" in answer.text
    assert "2026-08-28" in answer.text


def test_the_page_reaches_the_day_before_and_the_day_after_by_tapping(client, rostered):
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert
    assert 'href="/visits?day=2026-08-27"' in answer.text
    assert 'href="/visits?day=2026-08-29"' in answer.text


def test_flipping_the_mode_here_comes_back_to_the_same_day(client, rostered):
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert
    assert ('<input type="hidden" name="back" value="/visits?day=2026-08-28">'
            in answer.text)


def test_the_visit_list_carries_the_one_link_up_a_level(client, rostered):
    # Arrange / Act
    answer = client.get("/visits?day=2026-08-28")

    # Assert — web_plan §7: the wordmark, one link up, the toggle, and no trail
    assert 'class="up" href="/"' in answer.text
