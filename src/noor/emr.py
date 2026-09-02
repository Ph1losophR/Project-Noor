"""The EMR boundary (§4.9): seven reads, one write, and a fixture that misbehaves."""
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import cache
from typing import Protocol, runtime_checkable

from noor import content
from noor.domain.reconciliation import Medication, Product, products
from noor.domain.states import Datum


class WriteRejected(RuntimeError):
    """The EMR refused a Write-Back. Never swallowed: §4.10 forbids a quiet failure."""


@runtime_checkable
class EMR(Protocol):
    """What Noor needs from an EMR, which §4.9 calls a pitch asset in its own right.

    Every read answers with a `Datum`, so Present, Absent and Unreachable all arrive as
    values the caller has to handle. `submit` is the only member that raises.

    There is no `schedule` and no `cancel`. That absence is the interface making a
    promise: Noor records what became of a Visit it was given, and moves nobody's
    appointment.
    """

    # One-line bodies on purpose. A `...` on its own line is a statement that never
    # executes, and `exclude_lines = []` leaves nowhere to hide it from branch coverage.
    def demographics(self, patient_id: str) -> Datum: ...
    def problems(self, patient_id: str) -> Datum: ...
    def medications(self, patient_id: str) -> Datum: ...
    def lab(self, patient_id: str, analyte: str) -> Datum: ...
    def surveillance(self, patient_id: str, item: str) -> Datum: ...
    def allergies(self, patient_id: str) -> Datum: ...
    def roster(self, day: date) -> Datum: ...
    def submit(self, patient_id: str, payload: dict) -> None: ...


@dataclass(frozen=True)
class RosterLine:
    """One Scheduled Visit as the EMR hands it over (§4.9). Read-only, always.

    No Visit kind: §5.5 derives that from Patient state at the Start, and a label here
    would be the one it forbids.
    """

    visit_id: str
    patient_id: str
    patient_name: str
    scheduled_for: date
    reason: str


@cache
def catalogue() -> tuple[Product, ...]:
    """The shipped drug list. ADR 0007: a broken content file fails at load, loudly."""
    return products(content.load("drug-list").data["products"]["rows"])


def _prescribed(*items: str) -> tuple[Medication, ...]:
    """Each product id resolves against the shipped list. Anything else is unmatched —
    genuinely, because the list has no row matching it, not because a fixture said so."""
    rows = {product.id: product for product in catalogue()}
    return tuple(
        Medication(rows[item].generic, rows[item]) if item in rows else Medication(item)
        for item in items
    )


@dataclass(frozen=True)
class FixturePatient:
    """A fake record that misbehaves the way real ones do (§4.9).

    `unreachable` names the reads that time out for this Patient, and `rejects_writes`
    refuses the Write-Back. Hostility is data here, so the sixth misbehaviour is a row.
    """

    id: str
    name: str
    year_of_birth: int
    problems: tuple[str, ...]
    allergies: tuple[str, ...]
    medications: tuple[Medication, ...]
    labs: dict[str, tuple[float, datetime]]
    surveillance: dict[str, date]
    unreachable: frozenset[str] = frozenset()
    rejects_writes: bool = False


DIABETES_AND_HYPERTENSION = ("Type 2 diabetes mellitus", "Essential hypertension")


FIXTURES: dict[str, FixturePatient] = {
    "p-001": FixturePatient(
        "p-001", "Fatima Al-Harbi", 1958,
        problems=DIABETES_AND_HYPERTENSION,
        allergies=("Sulfa — rash, per daughter",),
        medications=_prescribed("metformin-500", "gliclazide-80", "amlodipine-5"),
        # Eighteen months old. Present, with the day it was drawn (§5.2)
        labs={"hba1c": (9.1, datetime(2025, 2, 10)),
              "creatinine": (78.0, datetime(2026, 6, 14))},
        surveillance={"hba1c": date(2025, 2, 10), "foot-examination": date(2025, 9, 2),
                      "creatinine-egfr": date(2026, 6, 14)}),
    "p-002": FixturePatient(
        "p-002", "Abdullah Al-Qahtani", 1949,
        problems=DIABETES_AND_HYPERTENSION + ("Chronic kidney disease, stage 3a",),
        allergies=("Penicillin",),
        # The last item is not on the drug list, and is kept as written (§4.2)
        medications=_prescribed("metformin-500", "insulin-glargine-100", "losartan-50",
                                "Cordarone 200 mg (brought from Cairo)"),
        labs={"hba1c": (7.6, datetime(2026, 6, 2)), "egfr": (48.0, datetime(2026, 6, 2)),
              "potassium": (5.2, datetime(2026, 6, 2))},
        surveillance={"hba1c": date(2026, 6, 2), "foot-examination": date(2024, 11, 3),
                      "creatinine-egfr": date(2026, 6, 2)}),
    "p-003": FixturePatient(
        "p-003", "Noura Al-Otaibi", 1965,
        problems=("Essential hypertension",),
        allergies=(),                       # nobody recorded one. Absent, not "none known"
        medications=_prescribed("amlodipine-5"),
        labs={},                            # no HbA1c ever. Absent, not Fatima's stale one
        surveillance={}),
    "p-004": FixturePatient(
        "p-004", "Mohammed Al-Shammari", 1955,
        problems=DIABETES_AND_HYPERTENSION,
        allergies=("Iodine contrast",),
        medications=_prescribed("metformin-1000", "empagliflozin-10", "lisinopril-20"),
        labs={"hba1c": (8.2, datetime(2026, 5, 20))},
        surveillance={"hba1c": date(2026, 5, 20)},
        unreachable=frozenset({"medications"})),        # §4.10's trigger
    "p-005": FixturePatient(
        "p-005", "Sara Al-Dossari", 1971,
        problems=("Type 2 diabetes mellitus",),
        allergies=("Metformin — severe nausea, self-reported",),
        medications=_prescribed("sitagliptin-100"),
        labs={"hba1c": (6.9, datetime(2026, 7, 11))},
        surveillance={"hba1c": date(2026, 7, 11)},
        rejects_writes=True),
}


ROSTER: tuple[RosterLine, ...] = (
    RosterLine("v-001", "p-001", "Fatima Al-Harbi", date(2026, 8, 28),
               "Three-month review — blood pressure above the band at the last Visit"),
    RosterLine("v-002", "p-002", "Abdullah Al-Qahtani",
               date(2026, 8, 28), "Medication review after a hospital discharge"),
    RosterLine("v-003", "p-003", "Noura Al-Otaibi",
               date(2026, 8, 28), "Enrolment — newly referred from the primary care clinic"),
    RosterLine("v-004", "p-004", "Mohammed Al-Shammari",
               date(2026, 8, 28), "Three-month review"),
    RosterLine("v-005", "p-005", "Sara Al-Dossari",
               date(2026, 8, 28), "Enrolment — referred after an emergency department visit"),
)


def _some(collection, as_of: datetime):
    """An empty collection is Absent. Noor cannot upgrade silence into a finding (N6)."""
    return (collection, as_of) if collection else None


@dataclass
class FixtureEMR:
    """The hostile fixture EMR (§4.9).

    `now` is a constructor argument, not a clock read: a test that asserts an HbA1c is
    eighteen months old would otherwise start failing next month.
    """

    now: datetime
    accepted: list[tuple[str, dict]] = field(default_factory=list)

    def demographics(self, patient_id: str) -> Datum:
        return self._answer(patient_id, "demographics", lambda patient: (
            {"name": patient.name, "year_of_birth": patient.year_of_birth}, self.now))

    def problems(self, patient_id: str) -> Datum:
        return self._answer(patient_id, "problems",
                            lambda patient: _some(patient.problems, self.now))

    def medications(self, patient_id: str) -> Datum:
        return self._answer(patient_id, "medications",
                            lambda patient: _some(patient.medications, self.now))

    def allergies(self, patient_id: str) -> Datum:
        return self._answer(patient_id, "allergies",
                            lambda patient: _some(patient.allergies, self.now))

    def lab(self, patient_id: str, analyte: str) -> Datum:
        # The stored pair is already (value, drawn), which is what _answer wants: the
        # as_of of a lab is the day of the draw, never the day Noor asked
        return self._answer(patient_id, "lab", lambda patient: patient.labs.get(analyte))

    def surveillance(self, patient_id: str, item: str) -> Datum:
        return self._answer(patient_id, "surveillance", lambda patient: _some(
            patient.surveillance.get(item), self.now))

    def roster(self, day: date) -> Datum:
        lines = tuple(line for line in ROSTER if line.scheduled_for == day)
        if not lines:
            return Datum.absent()
        return Datum.present(lines, as_of=self.now)

    def submit(self, patient_id: str, payload: dict) -> None:
        """The one member that raises. §4.10: a Write-Back that fails quietly is worse
        than none, because the Supervisor's task never arrives and nobody knows."""
        patient = FIXTURES.get(patient_id)
        if patient is None:
            raise WriteRejected(f"the EMR has no Patient {patient_id!r}")
        if patient.rejects_writes:
            raise WriteRejected(f"the EMR refused the write for {patient_id!r}")
        self.accepted.append((patient_id, payload))

    def _answer(self, patient_id: str, read: str, extract) -> Datum:
        """The three data states, decided once for all six per-Patient reads.

        `extract` returns a `(value, as_of)` pair, or None for nothing recorded — so
        Absent and Unreachable are decided here and never in a caller.
        """
        patient = FIXTURES.get(patient_id)
        if patient is None:
            return Datum.absent()
        if read in patient.unreachable:
            return Datum.unreachable()
        found = extract(patient)
        if found is None:
            return Datum.absent()
        value, as_of = found
        return Datum.present(value, as_of=as_of)
