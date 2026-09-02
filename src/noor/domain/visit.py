"""The Visit: the one object that holds state, and the gates on closing it (§5.8)."""
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from noor.domain.emergency import EmergencyRecord, check_all_resolved
from noor.domain.opinions import (
    Disposition, Flag, Recommendation, check_all_dispositioned,
)
from noor.domain.plans import BetweenVisitPlan, GoalOfCare
from noor.domain.records import Reason, Resolution, unresolved
from noor.domain.states import (
    Datum, Section, VisitKind, VisitState, check_transition,
)
from noor.domain.vitals import HomeReading


class VisitError(ValueError):
    """A Visit was asked for something the Visit Protocol does not allow."""


class NotReadyToComplete(Exception):
    """§5.8's gate refused, and the message says which condition failed."""


@dataclass
class Visit:
    id: str
    patient_id: str
    # None until the Start settles it (§5.5). A kind on a Scheduled Visit would be the
    # roster label the SSOT forbids, so the type refuses to hold one.
    kind: VisitKind | None = None
    state: VisitState = VisitState.SCHEDULED
    resolutions: dict[Section, Resolution] = field(default_factory=dict)
    emergencies: list[EmergencyRecord] = field(default_factory=list)
    shown: list[Recommendation] = field(default_factory=list)
    dispositions: list[Disposition] = field(default_factory=list)
    # §5.11: sent to the Supervisor at any time, so there is no state gate here. The
    # store's terminal refusal (§5.9) is what stops one arriving after the close.
    flags: list[Flag] = field(default_factory=list)
    plan: BetweenVisitPlan | None = None
    # Absent is the starting truth for a Baseline and is correct there — and stays correct
    # for the Visit after one that ended early, because §5.6 lets no Care Plan emit a plan
    # on the way out. For a Routine Visit whatever opens the Visit sets this before the
    # Brief renders, to Present or to Unreachable — leaving the default in place would be
    # the N6 silent degrade.
    previous_plan: Datum = field(default_factory=Datum.absent)
    # Collected by the Nurse on arrival, off the device's memory or a Caregiver's paper
    # log (§4.8) — so they belong to the Visit and not to any of the eight sections, and
    # never to Vitals, which is what the Field Team measured in the house.
    home_readings: list[HomeReading] = field(default_factory=list)
    started_at: datetime | None = None
    closed_by: str | None = None
    closed_at: datetime | None = None
    closing_reason: Reason | None = None

    def start(self, at: datetime, kind: VisitKind) -> None:
        check_transition(self.state, VisitState.IN_PROGRESS)
        self.state = VisitState.IN_PROGRESS
        self.kind = kind
        self.started_at = at

    def cancel(self, reason: Reason | None, by: str, at: datetime) -> None:
        check_transition(self.state, VisitState.CANCELLED)
        self._require_reason(reason)
        self._close(VisitState.CANCELLED, reason, by, at)

    def enter_emergency(self, at: datetime) -> None:
        check_transition(self.state, VisitState.EMERGENCY)
        self.state = VisitState.EMERGENCY
        self.emergencies.append(EmergencyRecord(started_at=at))

    def leave_emergency(self, at: datetime) -> None:
        check_transition(self.state, VisitState.IN_PROGRESS)
        self.state = VisitState.IN_PROGRESS
        self.emergencies[-1].resolve(at)

    def complete(self, by: str, at: datetime, goal: GoalOfCare | None = None) -> None:
        check_transition(self.state, VisitState.COMPLETED)
        missing = unresolved(self.resolutions)
        if missing:
            raise NotReadyToComplete(
                "not resolved: " + ", ".join(section.name for section in missing))
        if self.plan is None:
            raise NotReadyToComplete(
                "the Care Plan section emits the Between-Visit Plan, and none was emitted")
        # A Baseline's final section is the proposed Goal of Care, not the Care Plan
        # (§5.5), so it owes one more artifact than a Routine Visit. Proposed is the
        # bar; ratified is not, because that is outside the house (§5.8, ADR 0003).
        if self.kind is VisitKind.BASELINE and goal is None:
            raise NotReadyToComplete(
                "a Baseline Visit's final section proposes a Goal of Care, and none was")
        check_all_resolved(self.emergencies)
        check_all_dispositioned(self.shown, self.dispositions)
        self._close(VisitState.COMPLETED, None, by, at)

    def end_early(self, reason: Reason | None, by: str, at: datetime) -> None:
        check_transition(self.state, VisitState.ENDED_EARLY)
        self._require_reason(reason)
        # `plan` is not cleared here: §5.6's fourth obligation puts that on the Care Plan
        # section, which declines to emit one on the way out. A plan already written could
        # not be honestly un-emitted, and refusing the exit is what N4 forbids.
        # An open Emergency is ended only once it has been written down, so a refused
        # close can be retried after the team writes it — check_all_resolved below is
        # what refuses the undocumented one, with the start time in the message.
        if self.state is VisitState.EMERGENCY and self.emergencies[-1].is_documented:
            self.emergencies[-1].resolve(at)
        check_all_resolved(self.emergencies)
        self._close(VisitState.ENDED_EARLY, reason, by, at)

    def _require_reason(self, reason: Reason | None) -> None:
        if reason is None:
            raise VisitError("a Visit that does not finish carries a reason (§5.10)")

    def _close(
        self, target: VisitState, reason: Reason | None, by: str, at: datetime
    ) -> None:
        self.state = target
        self.closing_reason = reason
        self.closed_by = by
        self.closed_at = at


def kind_for(history: Sequence[Visit]) -> VisitKind:
    """§5.5: a Baseline until a Baseline has *Completed*, so a Baseline that ended early
    makes the next Visit a Baseline again. Derived, never a label on the roster."""
    settled = any(
        past.kind is VisitKind.BASELINE and past.state is VisitState.COMPLETED
        for past in history
    )
    return VisitKind.ROUTINE if settled else VisitKind.BASELINE
