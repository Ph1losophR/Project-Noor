# Project Noor

Home healthcare clinical decision support for chronic disease management — diabetes and hypertension — in Saudi Arabia. This glossary fixes the language of the home visit. It is a glossary only: no implementation detail, no architecture. Architecture lives in `project_noor_architecture.md`.

## Language

### People

**Field Team**:
The two clinicians physically present in the patient's home for a visit: a Junior Physician and a Nurse, together. A standing assignment to the Patient rather than a per-Visit choice — the same pair until someone reassigns them. The Visit records the pair that attended, copied at its Start, so a later reassignment never restates who performed a Visit that has already closed (§5.5, §5.13).
_Avoid_: care team, home team, visiting team, crew

**Junior Physician**:
The licensed prescribing decision-maker in the Field Team. Holds the authority to act but not yet the experience.
_Avoid_: doctor, resident, MD, junior doc

**Nurse**:
The Field Team member responsible for measurement, patient education, and hands-on care during the visit.
_Avoid_: RN, nursing staff, HCA

**Supervisor**:
The remote consultant-grade clinician accountable for the Field Team's clinical decisions. Reachable, but not present. Answers the items routed to them with a Review Verdict, and never edits a Visit or holds one open.
_Avoid_: supervising physician, senior doctor, consultant, attending, on-call

**Patient**:
The person receiving care in their own home, enrolled for chronic disease management.
_Avoid_: client, service user, case

**Caregiver**:
The family member — most often an adult son or daughter — present in the home and responsible for the Patient's care between Visits. Their presence is a condition of enrolment, not a courtesy. A Caregiver can be the executor of a Recommendation; between Visits they are frequently the only executor available.
_Avoid_: family, relative, carer, next of kin, attendant

**Executor**:
The person who carries out a Recommendation — a Patient, a Caregiver, a Field Team member, or a Supervisor. Always distinct from the Recommendation's author, because N2 asks whether the Executor can actually act, and that is unanswerable if the two share a field. A Write-Back item's *named owner* is its Executor.
_Avoid_: assignee, responsible party, actor

### The visit

**Visit**:
The unit of work Noor orchestrates: one planned attendance by the Field Team at the Patient's home, from the moment it is scheduled until it closes. Attendance happens during a Visit rather than defining one — a Visit nobody attended is still a Visit.
_Avoid_: appointment, encounter, session, call

**Roster**:
The list of Scheduled Visits Noor reads and does not own. An entry carries the Patient, the date, why the Visit was scheduled, and a Baseline Visit or Routine Visit planning indicator based on the Patient's completed history (ADR 0008). Noor records what became of a Visit on it; it never schedules, reschedules, or cancels one.
_Avoid_: schedule, calendar, diary, worklist

**Visit Protocol**:
The fixed ordered sequence of eight sections every Visit passes through — Visit Reason, Concerns & Interval History, Medication Reconciliation, Vitals, Physical Examination, Self-Care Check, Care Plan, Notes. That order is the record's order and no section may be absent; the content inside a section may vary. Both Visit types share it. Sections may be completed out of order, because the Field Team works in parallel — except the Care Plan, which is assembled after all seven others.
_Avoid_: template, form, checklist, flow, wizard

**Baseline Visit**:
A Visit for a Patient who has no Completed Baseline Visit — normally their first, and again after a Baseline that ended early, because the data floor was never established. Before attendance, the Roster shows a Baseline Visit planning indicator when this rule currently applies, so the Field Team knows which protocol shape to expect. The indicator does not settle the Visit's recorded type; Start confirms the kind from the completed history that exists then. Runs the same Visit Protocol with three differences: the Physical Examination is complete rather than composed, Goal of Care takes the place of Care Plan, and Noor issues no Recommendation that depends on a target or a trend. It establishes the Caregiver, the household's devices, and the data floor the engine will reason over.
_Avoid_: initial assessment, intake, onboarding visit, first visit, enrolment visit

**Routine Visit**:
Every Visit after a Completed Baseline Visit. Before attendance, the Roster shows a Routine Visit planning indicator; Start confirms the kind from the completed history that exists then. Opens by scoring the Between-Visit Plan the previous Visit emitted.
_Avoid_: normal visit, regular visit, standard visit, follow-up

**Visit Reason**:
Why this Visit is happening — scheduled review, post-discharge follow-up, or a Patient-initiated concern. Never a symptom. A routine Visit has a Visit Reason and usually no complaint at all.
_Avoid_: chief complaint, presenting complaint, reason for encounter

**Concerns & Interval History**:
The section of the Visit Protocol covering what has happened since the last Visit and what the Patient or Caregiver wants raised. Two halves: a fixed list of events Noor must be able to reason about, and the concerns themselves in the words they were said in, attributed to whoever raised them.
_Avoid_: history of present illness, HPI, presenting complaint, review of systems

**Medication Reconciliation**:
The section of the Visit Protocol that establishes what medication is physically in the house, product by product, and how that differs from what was prescribed. Products are selected from a searchable drug list rather than typed. A product the list does not contain is still recorded, and marked unmatched — never silently dropped.
_Avoid_: med rec, drug history, medication review, medication list

**Vitals**:
The section of the Visit Protocol holding the measurements the Field Team takes in the house during the Visit. Distinct from Home Readings, which the household took between Visits and the Nurse collects on arrival — same quantities, different observer, and never merged into one series.
_Avoid_: obs, observations, readings, measurements

**Physical Examination**:
The examination section of the Visit Protocol, whose required element list Noor composes from the Patient's conditions and overdue surveillance. The Field Team may add elements; it does not decide which are required.
_Avoid_: exam, physical, exam checklist

**Self-Care Check**:
The section of the Visit Protocol that establishes whether the prescribed treatment is actually reaching the Patient — medication storage and handling, administration technique, measurement technique, foot care, sick-day rules. Every item is observed or demonstrated, never asked, and every task is attributed to the person who actually performs it. Where the Physical Examination asks what the disease has done to the Patient, the Self-Care Check asks whether the treatment is arriving at all.
_Avoid_: education, counselling, adherence check, compliance review, lifestyle assessment

**Care Plan**:
The Visit's final section to be assembled, and the seventh in the record's order. Built from the Recommendations the Field Team accepted or overrode plus the Field Team's own additions. Assembled, never composed from scratch. Emits the Between-Visit Plan.
_Avoid_: plan, management plan, treatment plan, disposition

**Notes**:
The eighth section in the record's order, holding what the Field Team wants recorded that no other section asked for. Free text, and resolved by a structured reason when there is nothing to add — like every other section. Last in the record, but not the last one completed: the Care Plan is assembled after it.
_Avoid_: comments, remarks, free text, other

**Between-Visit Plan**:
The artifact a Visit's final section emits: the titration steps agreed in advance, the home measurement schedule, and the stop rules that say when to call. Every line is a machine-testable condition — a threshold, a schedule, or a rule — never prose. A Baseline Visit's carries no titration steps, having no ratified target to titrate toward.
_Avoid_: discharge instructions, follow-up plan, home plan, self-management plan

**Home Readings**:
The blood pressure and blood glucose measurements the Patient or Caregiver takes at home on the Between-Visit Plan's schedule. Collected by the Nurse on arrival — from the device's own stored memory, or from a Caregiver paper log where the device has none — and always carrying which of the two it came from. The thing the Between-Visit Plan is scored against.
_Avoid_: self-monitoring, telemetry, remote monitoring — and never **Vitals**, which is the separate section for what the Field Team measured in the house

**Goal of Care**:
The Patient's individualised targets, set at the Baseline Visit — proposed by the Junior Physician, ratified asynchronously by the Supervisor. A band per axis — floor and ceiling — stated as the home numbers themselves, never as an office number to be adjusted. Persistent, and the thing Noor compares every later reading against. Until it is ratified, Noor withholds every Recommendation that depends on a target.
_Avoid_: goals, targets, treatment goals, care goals, objectives

### The six Visit states

These six are the whole state machine. Nothing else is a Visit state — Supervisor review and Write-Back are separate axes.

**Scheduled**:
A Visit that exists on the roster and has not yet started. No one has travelled.
_Avoid_: booked, planned, pending, upcoming

**In Progress**:
A Visit the Field Team has started and not yet closed. The only state in which the Visit Protocol is worked through.
_Avoid_: active, open, ongoing, started

**Completed**:
The terminal state of a Visit whose every section is resolved — content, or a structured reason for having none — with any Emergency it passed through documented, closed by the Field Team before leaving the house. It depends on nothing outside the house — not the Supervisor, not the EMR, not connectivity.
_Avoid_: closed, finished, done, signed off, submitted

**Cancelled**:
The terminal state of a Visit that never started. Set by either member of the Field Team, and always carries a reason — which names the Patient as its source where the decision was theirs.
_Avoid_: dropped, no-show, DNA, not held

**Ended Early**:
The terminal state of a Visit that started and stopped before the Visit Protocol was finished. Set by either member of the Field Team, always carries a reason, and what was captured is not discarded.
_Avoid_: abandoned, aborted, incomplete, partial

**Emergency**:
An interrupt state entered from In Progress when the Patient or Caregiver needs an ambulance now. It suspends the Visit Protocol and exits either back to In Progress or to Ended Early, so it has a start and an end time. One of the six states, not a mode alongside them.
_Avoid_: crisis, code, urgent mode — and never *escalation*, which belongs to Escalation Tier and describes a Recommendation, not a Visit

### Beyond the state machine

**Emergency Protocol**:
The short sequence that replaces the Visit Protocol for the duration of an Emergency: a timed record of what was observed and what was done, and the handover the ambulance crew leaves with. Its exit is a binary — the Visit resumes, or it becomes Ended Early — and it carries no reason of its own. Closing the record takes an end time and at least one timeline entry; unlike a section, it has no structured reason for having none, because those minutes are what a receiving hospital and any later review will ask about.
_Avoid_: emergency workflow, code protocol, crash protocol

**Addendum**:
A timestamped, attributed addition to a Visit that has already reached a terminal state. The only way a closed Visit changes, because a Write-Back may already have created work that the original record justified. It sends a Write-Back of its own, after the Visit's, and its author may also flag it to the Supervisor (§5.9).
_Avoid_: edit, correction, amendment, revision

**Review Verdict**:
The Supervisor's answer to one item routed to them: agreed or disagreed, with their name, the time, and a note that a disagreement must carry. What lets an item leave the Supervisor's inbox, since nothing there is cleared by being read. It never holds up a Visit, a close, or a Write-Back, and it is not a structured reason — nothing routes on it (§5.12, ADR 0009).
_Avoid_: approval, acknowledgement, ack, countersignature

### What Noor produces

**Finding**:
Something Noor observed about the Patient from the record or from data captured during the Visit. An observation, never an instruction.
_Avoid_: issue, problem, flag, result

**Recommendation**:
A single action Noor proposes, carrying exactly one Escalation Tier. Always an instruction someone can execute, never an assessment.
_Avoid_: alert, advice, suggestion, prompt, nudge, warning

**Escalation Tier**:
The ordered 0–3 routing attached to every Recommendation, answering by when a response is required and from whom. Defined in `docs/adr/0001-time-to-action-not-severity.md`.
_Avoid_: severity, priority, urgency, acuity, criticality

**Suppression**:
Noor withholding a Recommendation because a Finding elsewhere in the Visit shows the signal that justified it is corrupted. The Recommendation and its reason for suppression are always recorded and always visible to the Supervisor. Defined in `docs/adr/0002-self-care-failure-suppresses-the-recommendation-it-undermines.md`.
_Avoid_: filtering, hiding, silencing, deduplication, muting

**Filed**:
A Recommendation Noor generated but did not show, because the per-Visit cap was already spent on work that outranked it. Distinct from Suppression: a Filed Recommendation is still valid and still wanted, it simply lost its slot. It carries a **deferral count** — the number of Visits it has been Filed across — and that count is the last of the three keys that decide the next slot.
_Avoid_: dismissed, backlogged, queued, hidden. *Deferral count* is the field's name and stays; the state itself is **Filed**, never "deferred", which in an override reason means something else entirely — that a Field Team sent the decision to the Supervisor.

**Write-Back**:
What Noor sends to the EMR at the close of a Visit. Every item is structured, and anything requiring a response carries a named owner and a due time from the route that produced it — an Escalation Tier's window for a Recommendation, the ratification window for a proposed Goal of Care. A Write-Back with no owner and no due time is narrative text wearing structure's clothes. An Addendum sends one of its own afterwards, which carries neither, because it asks for nothing.
_Avoid_: sync, push, export, upload, documentation

**Silence Audit**:
The sampled review of Completed Visits that produced no Recommendation, sent to the Supervisor precisely because nothing was found. How the accuracy of Noor's silence is measured rather than asserted.
_Avoid_: spot check, QA pass, random review, sampling

**Brief**:
What the Field Team reads before knocking: the Findings Noor derived from the record alone, while the Visit is still Scheduled. Never contains a Recommendation.
_Avoid_: summary, pre-visit report, handover, dashboard

**Handover**:
The record the ambulance crew leaves with when a Visit enters an Emergency: what Noor already knew about the Patient, what was observed, and what was done. Rendered from data already on the device, so it survives having no connectivity.
_Avoid_: referral, transfer note, summary, discharge letter

### How Noor describes what it knows

**Present / Absent / Unreachable**:
The three — and only three — states any input Noor reasons over can be in. **Present**: Noor has the value. **Absent**: Noor established that there is none, which is itself a clinical fact. **Unreachable**: Noor could not find out. Staleness is not a fourth state; it is a timestamp on a Present value. Noor never silently treats Unreachable as Absent, and says which of the three it is holding.
_Avoid_: null, missing, unknown, N/A, no data, empty — each of them collapses at least two of the three

**Resolved**:
What a section needs to be before a Visit can reach Completed: it has content, *or* it has a structured reason for having none. Resolved is not *filled* — a mandatory field a clinician cannot honestly satisfy gets satisfied dishonestly, and a declared gap is visible where an invention is not. An Emergency record is resolved on a stricter bar and is the only thing that is: an end time and at least one timeline entry, with no reason path.
_Avoid_: complete, filled, done, validated, required
