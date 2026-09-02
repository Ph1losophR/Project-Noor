"""§5.2's pre-departure read, and what the house reads back out of it."""
from datetime import date, datetime

from noor import content, emr, prefetch, store
from noor.domain.examination import items
from noor.domain.reconciliation import Medication, house_entry, read_entry
from noor.domain.states import DataState, Datum

OFFICE = datetime(2026, 8, 28, 7, 0)
ITEMS = items(content.load("surveillance-intervals").data["intervals"]["rows"])
PRODUCTS = {product.id: product for product in emr.catalogue()}
# The short tags `applies()` matches on, which is what `add_patient` stores (test_journeys).
BOTH = ["diabetes", "hypertension"]


def _enrolled(tmp_path, patient_id, conditions):
    """Arrange only: the store knows the Patient, and nothing has been read yet."""
    conn = store.connect(tmp_path / "noor.db")
    store.add_patient(conn, patient_id, emr.FIXTURES[patient_id].name, conditions)
    return conn


def test_what_the_office_read_is_what_the_house_reads_back(tmp_path):
    conn = _enrolled(tmp_path, "p-001", BOTH)

    unreadable = prefetch.prepare(conn, emr.FixtureEMR(now=OFFICE), "p-001",
                                  items=ITEMS, at=OFFICE)

    assert unreadable == ()
    dates = prefetch.surveillance(conn, "p-001")
    assert dates["hba1c"] == Datum.present(date(2025, 2, 10), as_of=OFFICE)
    assert dates["retinal-screening"] == Datum.absent()
    assert len(dates) == 7            # both conditions, so every row applies
    prescribed = prefetch.prescribed(conn, "p-001", products=PRODUCTS)
    assert [item.label for item in prescribed.value] == [
        "Metformin", "Gliclazide", "Amlodipine"]
    assert prescribed.value[0].product.id == "metformin-500"
    assert prefetch.allergies(conn, "p-001").value == ["Sulfa — rash, per daughter"]
    assert prefetch.readiness(conn, "p-001") == prefetch.Readiness(OFFICE, ())


def test_a_read_that_timed_out_is_named_in_the_office_and_not_found_in_the_house(tmp_path):
    conn = _enrolled(tmp_path, "p-004", BOTH)

    unreadable = prefetch.prepare(conn, emr.FixtureEMR(now=OFFICE), "p-004",
                                  items=ITEMS, at=OFFICE)

    assert unreadable == ("prescribed",)
    assert prefetch.readiness(conn, "p-004").unreadable == ("prescribed",)
    assert prefetch.prescribed(conn, "p-004", products=PRODUCTS).state is (
        DataState.UNREACHABLE)
    # The other two reads still landed. One input failing is not the visit failing.
    assert prefetch.surveillance(conn, "p-004")["hba1c"].value == date(2026, 5, 20)
    assert prefetch.allergies(conn, "p-004").value == ["Iodine contrast"]


def test_a_patient_nobody_prepared_reads_back_as_unreachable(tmp_path):
    conn = _enrolled(tmp_path, "p-001", BOTH)

    assert prefetch.prescribed(conn, "p-001", products=PRODUCTS).state is (
        DataState.UNREACHABLE)
    assert prefetch.allergies(conn, "p-001").state is DataState.UNREACHABLE
    assert prefetch.surveillance(conn, "p-001") == {}
    assert prefetch.readiness(conn, "p-001") == prefetch.Readiness(None, ())


def test_an_allergy_nobody_recorded_is_absent_and_never_none_known(tmp_path):
    conn = _enrolled(tmp_path, "p-003", ["hypertension"])

    prefetch.prepare(conn, emr.FixtureEMR(now=OFFICE), "p-003", items=ITEMS, at=OFFICE)

    assert prefetch.allergies(conn, "p-003") == Datum.absent()
    dates = prefetch.surveillance(conn, "p-003")
    assert len(dates) == 4            # hypertension only
    assert all(datum == Datum.absent() for datum in dates.values())


def test_an_item_the_drug_list_does_not_hold_survives_the_round_trip_as_written(tmp_path):
    conn = _enrolled(tmp_path, "p-002", BOTH + ["chronic-kidney-disease"])

    prefetch.prepare(conn, emr.FixtureEMR(now=OFFICE), "p-002", items=ITEMS, at=OFFICE)

    unmatched = [item for item in prefetch.prescribed(conn, "p-002", products=PRODUCTS).value
                 if not item.is_matched]
    assert [item.label for item in unmatched] == [
        "Cordarone 200 mg (brought from Cairo)"]


def test_a_box_with_a_count_and_an_expiry_survives_the_round_trip():
    box = Medication("Metformin", PRODUCTS["metformin-500"], 14, date(2026, 11, 30))

    assert read_entry(house_entry(box), PRODUCTS) == box
