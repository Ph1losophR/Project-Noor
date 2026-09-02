"""What is in the house against what was prescribed (§4.2), and §4.10's degradation."""
from datetime import date, datetime

import pytest

from noor.domain import reconciliation as recon
from noor.domain.reconciliation import Discrepancy, DiscrepancyKind, Medication, Product
from noor.domain.states import DataState, Datum

TODAY = date(2026, 8, 28)
AS_OF = datetime(2026, 8, 28, 9, 0)

AMLO_5 = Product("amlodipine-5", "Amlodipine", "5 mg", "tablet", "calcium-channel-blocker")
AMLO_10 = Product("amlodipine-10", "Amlodipine", "10 mg", "tablet",
                  "calcium-channel-blocker")
METFORMIN = Product("metformin-500", "Metformin", "500 mg", "tablet", "biguanide")


def in_house(product, expiry=date(2027, 1, 31)):
    return Medication(product.generic, product, quantity_remaining=20, expiry=expiry)


def prescribed(*items):
    return Datum.present(tuple(items), as_of=AS_OF)


def kinds(result):
    return [found.kind for found in result.discrepancies]


def test_a_matched_item_carries_the_product_the_team_picked_and_the_two_typed_fields():
    # Act
    item = Medication("Amlodipine", AMLO_5, quantity_remaining=26, expiry=TODAY)

    # Assert — §4.2: name, strength and form come off the list; these two are typed
    assert (item.is_matched, item.product.strength, item.quantity_remaining) == (
        True, "5 mg", 26)


def test_a_product_the_drug_list_does_not_contain_is_kept_as_free_text_and_unmatched():
    # Act — Wright's amiodarone: in the house, no row for it
    item = Medication("Cordarone 200mg from Cairo")

    # Assert — recorded, not dropped (N6)
    assert (item.is_matched, item.label) == (False, "Cordarone 200mg from Cairo")


def test_an_item_with_no_name_at_all_is_refused():
    # Act / Assert
    with pytest.raises(recon.ReconError):
        Medication("")


def test_a_negative_quantity_remaining_is_refused():
    # Act / Assert — the adherence signal is only a signal if it is a real count
    with pytest.raises(recon.ReconError):
        Medication("Amlodipine", AMLO_5, quantity_remaining=-1)


def test_the_search_matches_on_the_generic_name():
    # Act
    found = recon.search((AMLO_5, AMLO_10, METFORMIN), "amlo")

    # Assert — Phase 1 searches `generic`; brand names are a later synonym field
    assert found == [AMLO_5, AMLO_10]


def test_the_search_returns_nothing_for_a_drug_the_list_does_not_have():
    # Act / Assert — which is what produces an unmatched item, by design
    assert recon.search((AMLO_5, METFORMIN), "amiodarone") == []


def test_an_empty_search_returns_nothing_rather_than_the_whole_list():
    # Act / Assert
    assert recon.search((AMLO_5, METFORMIN), "   ") == []


def test_every_row_of_the_shipped_drug_list_builds_a_product():
    # Arrange — the drift guard: a renamed column in `drug-list.md` fails right here.
    # This is the first domain test that reads a content file, and it earns the exception
    # because the file and this type have to agree and neither one owns the other.
    from noor import content

    # Act — a column this type has no field for raises inside products()
    catalogue = recon.products(content.load("drug-list").data["products"]["rows"])

    # Assert — a count would be brittle: the named owner is expected to add rows
    assert catalogue and catalogue[0].generic


def test_a_house_that_matches_the_prescribed_list_has_nothing_to_report():
    # Act
    result = recon.reconcile([in_house(AMLO_5)], prescribed(in_house(AMLO_5)), TODAY)

    # Assert
    assert result.discrepancies == ()


def test_a_prescribed_drug_that_is_not_in_the_house_is_an_omission():
    # Act
    result = recon.reconcile([in_house(AMLO_5)],
                             prescribed(in_house(AMLO_5), in_house(METFORMIN)), TODAY)

    # Assert
    assert result.discrepancies == (
        Discrepancy(DiscrepancyKind.OMISSION, "Metformin"),)


def test_a_drug_in_the_house_that_nobody_prescribed_is_reported():
    # Act
    result = recon.reconcile([in_house(AMLO_5), in_house(METFORMIN)],
                             prescribed(in_house(AMLO_5)), TODAY)

    # Assert
    assert result.discrepancies == (
        Discrepancy(DiscrepancyKind.UNPRESCRIBED, "Metformin"),)


def test_the_same_drug_at_a_different_strength_is_a_strength_mismatch():
    # Act — the 10 mg box in the house, the 5 mg on the list
    result = recon.reconcile([in_house(AMLO_10)], prescribed(in_house(AMLO_5)), TODAY)

    # Assert — not an omission and not unprescribed; the drug is right, the box is not
    assert result.discrepancies == (
        Discrepancy(DiscrepancyKind.STRENGTH_MISMATCH, "Amlodipine"),)


def test_two_boxes_of_the_same_drug_in_the_house_are_a_duplicate():
    # Arrange — the old 5 mg box beside the new 10 mg one, the classic double dose
    house = [in_house(AMLO_5), in_house(AMLO_10)]

    # Act
    result = recon.reconcile(house, prescribed(in_house(AMLO_10)), TODAY)

    # Assert
    assert Discrepancy(DiscrepancyKind.DUPLICATE, "Amlodipine") in result.discrepancies


def test_a_box_in_the_house_that_is_past_its_expiry_is_reported():
    # Arrange
    house = [in_house(AMLO_5, expiry=date(2026, 7, 31))]

    # Act — the date is a parameter, never `date.today()` inside the module
    result = recon.reconcile(house, prescribed(in_house(AMLO_5)), TODAY)

    # Assert
    assert result.discrepancies == (Discrepancy(DiscrepancyKind.EXPIRED, "Amlodipine"),)


def test_a_box_with_no_expiry_recorded_is_not_reported_as_expired():
    # Arrange — the label was gone, which is not the same as an expired box
    house = [Medication("Amlodipine", AMLO_5, quantity_remaining=20, expiry=None)]

    # Act
    result = recon.reconcile(house, prescribed(in_house(AMLO_5)), TODAY)

    # Assert
    assert DiscrepancyKind.EXPIRED not in kinds(result)


def test_an_unmatched_item_is_reported_once_and_never_compared():
    # Arrange — no product, so there is no generic to compare against anything
    house = [in_house(AMLO_5), Medication("Cordarone 200mg from Cairo")]

    # Act
    result = recon.reconcile(house, prescribed(in_house(AMLO_5)), TODAY)

    # Assert — §4.2: Noor states it cannot reconcile the item instead of guessing
    assert kinds(result) == [DiscrepancyKind.UNMATCHED]


def test_an_unreachable_prescribed_list_still_records_what_is_in_the_house():
    # Arrange — §4.10's first degrading section, with no EMR in the moment
    house = [in_house(AMLO_5), in_house(METFORMIN)]

    # Act
    result = recon.reconcile(house, Datum.unreachable(), TODAY)

    # Assert — the section has content; only the comparison is missing
    assert (len(result.house), result.discrepancies) == (2, ())


def test_an_unreachable_prescribed_list_declares_itself_rather_than_looking_clean():
    # Act
    result = recon.reconcile([in_house(AMLO_5)], Datum.unreachable(), TODAY)

    # Assert — N6: the Write-Back carries this, so "no discrepancy" is never implied
    assert (result.comparison, result.is_complete) == (DataState.UNREACHABLE, False)


def test_an_unreachable_prescribed_list_still_reports_what_the_cupboard_alone_shows():
    # Arrange — an expired box and a duplicate need no EMR to be found
    house = [in_house(AMLO_5, expiry=date(2026, 7, 31)), in_house(AMLO_10)]

    # Act
    result = recon.reconcile(house, Datum.unreachable(), TODAY)

    # Assert — offline is not a notepad
    assert set(kinds(result)) == {DiscrepancyKind.EXPIRED, DiscrepancyKind.DUPLICATE}


def test_a_patient_with_nothing_prescribed_is_not_the_same_as_an_unreachable_list():
    # Arrange — the EMR answered, and the answer was "no medication"
    house = [in_house(AMLO_5)]

    # Act
    result = recon.reconcile(house, Datum.absent(), TODAY)

    # Assert — the comparison happened, and every box in the house is unprescribed
    assert (result.comparison, kinds(result)) == (
        DataState.PRESENT, [DiscrepancyKind.UNPRESCRIBED])


def test_the_sections_content_carries_the_comparison_as_a_word_and_the_day_it_held():
    # Arrange
    result = recon.reconcile([in_house(AMLO_5)], prescribed(in_house(AMLO_5)), TODAY)

    # Act
    content = recon.as_content(result, AS_OF)

    # Assert — JSON-safe throughout: no `Datum` reaches the store or the EMR
    assert content == {"in_house": [{"label": "Amlodipine", "product_id": "amlodipine-5",
                                     "quantity_remaining": 20, "expiry": "2027-01-31"}],
                       "discrepancies": [],
                       "detection": {"state": "present",
                                     "as_of": "2026-08-28T09:00:00"}}


def test_an_unreachable_comparison_says_so_in_the_content_and_carries_no_as_of():
    # Arrange
    result = recon.reconcile([in_house(AMLO_5)], Datum.unreachable(), TODAY)

    # Act
    content = recon.as_content(result, AS_OF)

    # Assert — N6, in both directions with the test above: an empty `discrepancies`
    # list means nothing until this key says which of the two produced it
    assert content == {"in_house": [{"label": "Amlodipine", "product_id": "amlodipine-5",
                                     "quantity_remaining": 20, "expiry": "2027-01-31"}],
                       "discrepancies": [],
                       "detection": {"state": "unreachable"}}


def test_a_prescribed_drug_missing_from_the_drug_list_is_reported_not_dropped():
    # Arrange — the EMR named a drug the bundled list has no row for
    house = [in_house(AMLO_5)]
    lines = (in_house(AMLO_5), Medication("Cordarone 200mg from Cairo"))

    # Act
    result = recon.reconcile(house, prescribed(*lines), TODAY)

    # Assert — §4.9's hostile fixture: recorded, never dropped (N6)
    assert kinds(result) == [DiscrepancyKind.UNMATCHED]


def test_a_box_expiring_exactly_today_is_not_expired():
    # Arrange — the threshold row: "expires today" is still good, and that is a decision
    house = [in_house(AMLO_5, expiry=TODAY)]

    # Act
    result = recon.reconcile(house, prescribed(in_house(AMLO_5)), TODAY)

    # Assert
    assert DiscrepancyKind.EXPIRED not in kinds(result)


def test_the_sections_content_serialises_a_populated_reconciliation():
    # Arrange — matched, unmatched, and no-expiry boxes at once: every shape survives
    house = [in_house(AMLO_5, expiry=date(2026, 7, 31)),
             Medication("Cordarone 200mg from Cairo"),
             Medication("Metformin", METFORMIN, quantity_remaining=6, expiry=None)]
    result = recon.reconcile(house, prescribed(in_house(AMLO_5)), TODAY)

    # Act
    content = recon.as_content(result, AS_OF)

    # Assert — the shape Task 11 stores and Task 17 sends, with data in it
    assert content["in_house"] == [
        {"label": "Amlodipine", "product_id": "amlodipine-5",
         "quantity_remaining": 20, "expiry": "2026-07-31"},
        {"label": "Cordarone 200mg from Cairo", "product_id": None,
         "quantity_remaining": None, "expiry": None},
        {"label": "Metformin", "product_id": "metformin-500",
         "quantity_remaining": 6, "expiry": None},
    ]
    assert content["discrepancies"] == [
        {"kind": "not on the drug list — Noor cannot reconcile this item",
         "subject": "Cordarone 200mg from Cairo"},
        {"kind": "in the house, past its expiry", "subject": "Amlodipine"},
        {"kind": "in the house, not on the prescribed list", "subject": "Metformin"},
    ]
