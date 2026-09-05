# Baseline labels are read-time planning indicators

The Field Team needs to know what kind of Visit they are preparing for before
leaving the building. The architecture also needs the actual Visit kind to remain
correct when a Visit starts, because a Baseline is determined by the Patient's
completed history and a Baseline that ended early does not establish the data floor.

## Decision

The Visit List shows one of these words on every Scheduled row:

- **Baseline Visit** when the Patient has no Completed Baseline Visit.
- **Routine Visit** after the Patient has a Completed Baseline Visit.

This is a read-time planning indicator (§4.3). It is computed from the Patient's current
completed history so the Field Team can understand the protocol shape before
departure. It is not a clinical event, it does not change the roster, and it is not
stored as `Visit.kind`.

When the Field Team performs Start Visit (§5.5), Noor recomputes the kind from the
completed history available at that moment and stores the result as `Visit.kind`.
The Start transition is the source of truth for the Visit record and never trusts
the display label. If the history changes between two roster reads, the planning
indicator may change; that is a truthful update, not a state transition.

Started and terminal Visits that actually started show their settled kind. A
Cancelled Visit never started and therefore has no settled type.

## Considered Options

- **Hide Baseline/Routine until Start.** Rejected because the Field Team would not
  know which protocol shape to expect while checking readiness and preparing to
  leave.
- **Persist the type when the Visit is scheduled.** Rejected because scheduling
  can happen before the relevant history is complete, and a Baseline that ended
  early must leave the next Visit as Baseline.
- **Use the display label as the domain kind.** Rejected because a read-time
  planning signal must never be allowed to bypass the Start transition's history
  check or mutate the clinical record.

## Consequences

The Visit List becomes clear before departure without adding a second domain state
or changing the Visit state machine. The web view model and tests must distinguish
the planning label from the persisted kind, and the Start route must continue to
derive `VisitKind` from completed history. The label can change after a roster
refresh, which is expected and safer than displaying a stale type.
