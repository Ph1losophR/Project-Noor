"""The required element list: composed from conditions and overdue surveillance,
or the complete examination when there is nothing to compose from (§4.2, §4.3, §4.10)."""

from datetime import date

from noor import content
from noor.domain.examination import (
    Composition,
    Element,
    compose,
    elements,
    months_by_item,
    overdue,
)
from noor.domain.states import Datum, VisitKind

TODAY = date(2026, 8, 28)

# A small catalogue, so a test says what it is about instead of pointing at row 7.
# The ids are real ones from the file; the labels are shortened.
EVERYONE = Element("general-appearance", "General appearance", ())
DIABETES = Element("foot-inspection", "Foot inspection, both feet", ("diabetes",))
ANNUAL = Element("monofilament", "10 g monofilament, ten sites", ("diabetes",), "foot-examination")
CATALOGUE = (EVERYONE, DIABETES, ANNUAL)
MONTHS = {"foot-examination": 12}


def _composed(conditions, surveillance=None, kind=VisitKind.ROUTINE):
    return compose(
        CATALOGUE,
        kind=kind,
        conditions=conditions,
        surveillance=surveillance or {},
        intervals=MONTHS,
        as_of=TODAY,
    )


def test_an_element_with_no_condition_against_it_is_required_for_every_patient():
    routine = _composed(("hypertension",))

    assert EVERYONE in routine.required


def test_an_element_for_a_condition_the_patient_does_not_have_is_left_out():
    routine = _composed(("hypertension",))

    assert DIABETES not in routine.required


def test_an_element_for_a_condition_the_patient_has_is_required():
    routine = _composed(("diabetes",))

    assert DIABETES in routine.required


def test_a_patient_with_both_conditions_gets_the_elements_for_both():
    routine = _composed(("diabetes", "hypertension"))

    assert EVERYONE in routine.required and DIABETES in routine.required


def test_an_element_tied_to_surveillance_is_left_out_while_that_surveillance_is_current():
    current = {"foot-examination": Datum.present(date(2026, 3, 1), as_of=date(2026, 3, 1))}

    routine = _composed(("diabetes",), current)

    assert ANNUAL not in routine.required


def test_an_element_tied_to_surveillance_is_required_once_that_surveillance_is_overdue():
    stale = {"foot-examination": Datum.present(date(2024, 11, 3), as_of=date(2024, 11, 3))}

    routine = _composed(("diabetes",), stale)

    assert ANNUAL in routine.required


def test_surveillance_absent_from_the_record_counts_as_overdue():
    """A foot examination nobody ever recorded is one to do now, not one to assume."""
    never = {"foot-examination": Datum.absent()}

    routine = _composed(("diabetes",), never)

    assert ANNUAL in routine.required


def test_a_surveillance_date_exactly_on_the_interval_is_not_yet_overdue():
    due_today = Datum.present(date(2025, 8, 28), as_of=date(2025, 8, 28))

    assert overdue(due_today, 12, TODAY) is False


def test_the_interval_arithmetic_clamps_a_short_month():
    """Three months before 31 May is the 28th, not a date that does not exist."""
    end_of_february = Datum.present(date(2026, 2, 28), as_of=date(2026, 2, 28))

    assert overdue(end_of_february, 3, date(2026, 5, 31)) is False


def test_a_baseline_visit_asks_for_every_element_in_the_file():
    baseline = _composed(("hypertension",), kind=VisitKind.BASELINE)

    assert baseline.required == CATALOGUE


def test_a_baseline_visit_records_that_it_had_no_history_to_compose_from():
    baseline = _composed(("hypertension",), kind=VisitKind.BASELINE)

    assert baseline.basis is Composition.BASELINE and not baseline.is_composed


def test_unreachable_surveillance_falls_back_to_the_complete_examination():
    down = {"foot-examination": Datum.unreachable()}

    routine = _composed(("hypertension",), down)

    assert routine.required == CATALOGUE


def test_one_unreachable_read_is_enough_to_force_the_fallback():
    """A partly composed list looks composed and is not, which is the §4.1 failure."""
    partly = {
        "foot-examination": Datum.unreachable(),
        "hba1c": Datum.present(date(2026, 7, 1), as_of=date(2026, 7, 1)),
    }

    routine = _composed(("diabetes",), partly)

    assert routine.required == CATALOGUE


def test_the_fallback_says_it_is_a_fallback_and_not_a_composed_list():
    down = {"foot-examination": Datum.unreachable()}

    routine = _composed(("diabetes",), down)

    assert routine.basis is Composition.UNREACHABLE and not routine.is_composed


def test_a_composed_list_says_so():
    current = {"foot-examination": Datum.present(date(2026, 3, 1), as_of=date(2026, 3, 1))}

    routine = _composed(("diabetes",), current)

    assert routine.basis is Composition.COMPOSED and routine.is_composed


def test_the_element_catalogue_is_built_from_the_shipped_rows():
    catalogue = elements(content.load("physical-examination-elements").data["elements"]["rows"])

    assert catalogue and all(element.label for element in catalogue)


def test_an_element_row_with_no_overdue_key_carries_no_surveillance_tie():
    catalogue = elements(content.load("physical-examination-elements").data["elements"]["rows"])

    assert any(element.overdue is None for element in catalogue)


def test_the_intervals_are_built_from_the_shipped_rows():
    months = months_by_item(content.load("surveillance-intervals").data["intervals"]["rows"])

    assert months["foot-examination"] == 12


def test_every_element_that_names_a_surveillance_item_names_a_real_one():
    """The drift guard for the two content files: they meet by id and nothing checks
    that at runtime, because a KeyError during a Visit is not the place to find out."""
    catalogue = elements(content.load("physical-examination-elements").data["elements"]["rows"])
    months = months_by_item(content.load("surveillance-intervals").data["intervals"]["rows"])

    unknown = {element.overdue for element in catalogue if element.overdue} - set(months)

    assert unknown == set()
