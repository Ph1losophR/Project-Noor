"""Which measurements the Vitals section asks for, and the Home Readings that are a
separate series with a different observer (§4.2, §4.8, `CONTEXT.md`)."""

from dataclasses import fields
from datetime import datetime

import pytest

from noor import content
from noor.domain.states import VisitKind
from noor.domain.vitals import (
    HomeReading,
    Measurement,
    Source,
    VitalsError,
    asked_for,
    measurements,
)

EVERYONE = Measurement("bp-seated", "Blood pressure, seated", "mmHg", ())
DIABETES = Measurement("capillary-glucose", "Capillary blood glucose", "mmol/L", ("diabetes",))
ONCE = Measurement("height", "Height", "cm", (), baseline_only=True)
HYPERTENSION_ONCE = Measurement(
    "bp-other-arm", "Blood pressure, other arm", "mmHg", ("hypertension",), baseline_only=True)
CATALOGUE = (EVERYONE, DIABETES, ONCE, HYPERTENSION_ONCE)


def test_a_measurement_with_no_condition_against_it_is_asked_of_every_patient():
    routine = asked_for(CATALOGUE, conditions=("hypertension",), kind=VisitKind.ROUTINE)

    assert EVERYONE in routine


def test_a_measurement_for_a_condition_the_patient_does_not_have_is_not_asked():
    routine = asked_for(CATALOGUE, conditions=("hypertension",), kind=VisitKind.ROUTINE)

    assert DIABETES not in routine


def test_a_measurement_for_a_condition_the_patient_has_is_asked():
    routine = asked_for(CATALOGUE, conditions=("diabetes",), kind=VisitKind.ROUTINE)

    assert DIABETES in routine


def test_a_routine_visit_does_not_ask_again_for_something_measured_once():
    routine = asked_for(CATALOGUE, conditions=("hypertension",), kind=VisitKind.ROUTINE)

    assert ONCE not in routine


def test_a_baseline_visit_asks_for_the_once_only_measurements():
    baseline = asked_for(CATALOGUE, conditions=("hypertension",), kind=VisitKind.BASELINE)

    assert ONCE in baseline and HYPERTENSION_ONCE in baseline


def test_a_baseline_visit_still_filters_by_condition():
    """Baseline widens what is asked once; it does not ask about a condition nobody has."""
    baseline = asked_for(CATALOGUE, conditions=("diabetes",), kind=VisitKind.BASELINE)

    assert HYPERTENSION_ONCE not in baseline


def test_the_order_of_the_file_is_the_order_of_the_form():
    routine = asked_for(CATALOGUE, conditions=("diabetes",), kind=VisitKind.ROUTINE)

    assert routine == (EVERYONE, DIABETES)


def test_the_catalogue_is_built_from_the_shipped_rows():
    catalogue = measurements(content.load("vitals-by-condition").data["measurements"]["rows"])

    assert catalogue and all(m.unit for m in catalogue)


def test_a_row_with_no_baseline_only_key_is_asked_at_every_visit():
    catalogue = measurements(content.load("vitals-by-condition").data["measurements"]["rows"])

    assert any(not m.baseline_only for m in catalogue)


@pytest.mark.parametrize("source", list(Source))
def test_every_home_reading_says_which_of_the_two_sources_it_came_from(source):
    reading = HomeReading("bp-seated", "142/88", datetime(2026, 8, 20, 7, 30), source)

    assert reading.source is source


def test_a_home_reading_carries_a_source_and_a_vitals_measurement_has_no_such_field():
    """The two series stay apart because the types do, not because someone remembers
    to keep them apart (`CONTEXT.md`)."""
    assert "source" in {f.name for f in fields(HomeReading)}
    assert "source" not in {f.name for f in fields(Measurement)}


def test_a_home_reading_with_no_value_is_refused():
    with pytest.raises(VitalsError, match="bp-seated"):
        HomeReading("bp-seated", "", datetime(2026, 8, 20, 7, 30), Source.PAPER_LOG)


def test_the_two_sources_are_labelled_so_a_clinician_can_tell_them_apart():
    """These strings are displayed with every Finding derived from the reading (N5), so
    they are the copy, not an internal key."""
    assert (Source.DEVICE_MEMORY.value, Source.PAPER_LOG.value) == (
        "device memory", "Caregiver paper log")
