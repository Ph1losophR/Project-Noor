# `initial/` — Roster, Brief, Workspace, Verification, Emergency, Supervisor + Queue + Addendum throwaways (demo only)

Exact-look copies of the pasted Roster, Pre-Visit Brief, Clinical Encounter
Workspace, Clinical Verification, Emergency Protocol, Supervisor Inbox,
Write-Back Queue, and Clinical Addendum designs, wired to the
Phase 1 backend for demo purposes.
Approved as throwaways: they knowingly violate the SSOTs, and nothing here may
be mistaken for the shippable frontend.

`roster.html` / `brief.html` / `visit.html` / `verify.html` / `emergency.html` /
`inbox.html` / `queue.html` / `addendum.html`
are the byte-exact pasted references — open one directly to check its Next.js
page against the design. The working copies live at `/initial` (roster),
`/brief/[visitId]?day=` (brief), `/visit/[visitId]?day=` (workspace),
`/visit/[visitId]/review?day=` (verification),
`/visit/[visitId]/emergency?day=` (emergency), `/inbox` (supervisor),
`/queue` (write-back), and `/visit/[visitId]/addendum?day=` (addendum) and
differ from the references only where noted below.

## What is wired (real backend data)

Roster (`/initial`):

- Card name, Visit Reason, state word, Baseline/Routine indicator,
  and the readiness line — from `GET /api/roster?day=` (`src/noor/api.py`).
- Search box, type filter, and day stepper — real behaviour over that data.
- Open Brief links to `/brief/{visit_id}?day={day}`.

Brief (`/brief/[visitId]?day=`):

- Banner name, planning indicator, scheduled reason — from the roster read.
- Last-Visit conclusion line, surveillance-due cards, and blind spots — from
  `GET /api/visits/{id}/brief?as_of=` (the Brief, §5.3: Findings only, never a
  Recommendation).
- Section 1 history table, both graphs, and both Goal of Care cards stay demo:
  the backend has no five-encounter history, no graph coordinates (computing
  them in the browser would put clinical presentation logic outside the
  coverage gate), and no Goal of Care read endpoint yet. The measured-series
  and plan-in-force boxes were removed at the owner's request.

Workspace (`/visit/[visitId]?day=`):

- Header state/kind/patient/reason line, Visit Reason input (saves on blur to
  the `visit_reason` section), Emergency confirm (enters the Emergency state
  and opens the Emergency Protocol page), Review & Complete link, and a
  Return-to-Emergency link in place of Escalate while the state is Emergency —
  from the visit endpoints in `src/noor/api.py`.
- Brief Start now POSTs the start and opens the workspace; roster Resume and
  View Closed link to it; Back to Roster returns to `/initial`.
- Sections 2–8 content and the End Early modal's four rows stay demo: the End
  Early rows are not the eight real `ended_early` rows (same convention as the
  roster Cancel popover).

Verification (`/visit/[visitId]/review?day=`):

- Gate box, per-section statuses (any unresolved section renders the red
  alert card), emergency record check, plan line count, and the bottom-bar
  lock — all computed from the visit detail read. Complete runs the real §5.8
  gate; refusals show the backend's reason.
- Workspace Review & Complete now navigates here instead of posting directly.
- Vitals snapshot, transmission target, banner extras, attestation copy, and
  the three recommendation cards stay demo: Phase 1 has no producer, so no
  Recommendation exists to disposition. The cards hold the layout until
  Phase 1.5.

Emergency (`/visit/[visitId]/emergency?day=`):

- Banner dossier name, live protocol clock from the record's start, ingress
  time, timeline stream, allergy line (Present shows the cached list, Absent
  and Unreachable say so — §4.10), and both exits — from the visit detail
  read. Committing an entry POSTs the timeline endpoint; Resume POSTs the
  resume endpoint and returns to the workspace; Transfer opens the real eight
  §5.10 `ended_early` rows plus Other and POSTs the end-early endpoint, which
  refuses an undocumented record with the backend's reason. A closed record
  renders read-only with the way back.
- New backend for this page, all test-first: `Visit.record_timeline`
  (`src/noor/domain/visit.py`), `POST .../emergency/entries`, `POST
  .../emergency/resume`, `GET /api/reasons/ended_early`, and the full timeline
  plus allergies in the visit detail (`src/noor/api.py`). Late entries after
  the leave land on the same record, per §5.7.
- Dossier extras (MRN line, dispatch note), handover meds and vitals
  trajectory, and per-entry authorship stay demo: Phase 1 has no source for
  them, so entries render under a generic Field Team line. The
  "Escalation Protocol active" pill and "Section 10" label are kept verbatim
  from the paste; the shippable page uses CONTEXT.md's words (Emergency
  Protocol, never escalation for a Visit state).

Supervisor (`/inbox`):

- Patient-grouped rows, per-route badges, due countdowns, and the pending
  count — from `GET /api/inbox` (derived on read, §5.1). Row detail reads the
  visit detail (recommendation with tier/executor/provenance/strength,
  disposition, flag note) and, for ratification, the goal read (bands,
  lineage, office anchor, proposer). Agree posts the verdict — on ratification
  it posts the ratify endpoint instead, since agreeing *is* ratifying (ADR
  0009); Disagree posts the verdict with its mandatory note and, on
  ratification, correctly stays open. Refusals show the backend's reason.
- New backend for this page, all test-first: `GET /api/inbox` (week stated or
  current), `POST /api/inbox/verdict` (refuses ghost rows with 404),
  `GET /api/patients/{id}/goal`, `POST .../goal/ratify`, and shown /
  dispositions / flags in the visit detail (`src/noor/api.py`).
- The Supervisor's name stands in for a sign-in Phase 1 does not have; the
  bedside-context card, diagnosis paragraph (detail shows kind, state, and
  scheduled reason instead), search-date button, and nav badges stay demo.
  Search and route filter run for real over the loaded rows. The page keeps
  the paste's wider 1280px shell — the review workstation is a desktop
  surface, not the tablet capture shell — and "Most pressing first" replaces
  the paste's "Sorted by SLA Expiry", since Tier 3 sorts before due time.
- Every page's nav now links here; the inbox badge carries the real pending
  count.

Write-Back (`/queue`):

- Queued envelopes, per-item owners and due times, refusal text, and queued
  Addenda — from `GET /api/queue` (closed Visits the EMR has not accepted,
  §4.10). Transmit Now posts `POST /api/visits/{id}/dispatch`; Attempt
  Dispatch for All Queued posts `POST /api/queue/dispatch` (one explicit
  resend each — the close tried once, nothing retries by itself). A sent
  envelope leaves the queue on the next read; a refusal stays queued carrying
  what the EMR said. Refusals show the backend's reason.
- New backend for this page, all test-first: `GET /api/queue`, `POST
  /api/queue/dispatch`, `POST /api/visits/{visit_id}/dispatch` (404 unknown,
  409 not closed, 200 with `sent: false` plus the recorded refusal where the
  EMR says no). The drain runs over the fixture EMR — §1.1 defines the
  boundary against fixtures — and answers as the cluster's Supervisor
  (`SUPERVISOR` in `src/noor/api.py`; Phase 1 has no sign-in, the same fiction
  the inbox's verdicts carry in `by`).
- The dispatched-example card, envelope IDs, payload sizes, SHA keys, FHIR
  transaction IDs, endpoint URLs, NFC/export, signature verification, and
  storage-meter figures stay demo: Phase 1 lists no delivery receipts, so a
  confirmed send has nothing to read back. The paste's "Active Encounter"
  interim card is dropped, not demoed: only closed Visits queue (§4.9), so a
  static open-Visit card would assert a falsehood. The hostile-fixture refusal
  wires the real refusal text; the paste's 422/national-identifier specifics
  have no source in the EMR seam and stay demo.
- Every page's nav now links here; the queue badge carries the real pending
  count (queued Visits plus queued Addenda).

Addendum (`/visit/[visitId]/addendum?day=`):

- Opens only on terminal Visits (Completed / Cancelled / Ended Early) — any
  other state renders the refusal notice with the way back to the workspace,
  since a non-closed Visit is edited there, never by Addendum (§5.9).
- Header name, state word, closed date/time and closed-by line — from the
  visit detail read. Statement text, author (prefilled with the attending
  Junior Physician, editable), device timestamp, and flagged switch commit
  through `POST /api/visits/{visit_id}/addenda`; refusals show the backend's
  reason. Prior addenda (author/text/time/flagged, oldest first) read through
  `GET /api/visits/{visit_id}/addenda`. A flagged commit lands on the
  Supervisor's inbox as a manual flag on Tier 1's window (§5.9 + §5.12).
- New backend for this page, all test-first: `POST
  /api/visits/{visit_id}/addenda` (404 unknown, 409 still open checked before
  writing, 400 empty text/author) and `GET /api/visits/{visit_id}/addenda`
  (`src/noor/api.py`; the store's `add_addendum` / `addenda` already carried
  the flagged-manual-flag path and the queue drain).
- Entry point: the workspace shows a "Write Addendum" link only when the
  Visit state is terminal (the roster's closed-Visit rows land on the
  workspace, so that is where the closed record is viewed).
- The MRN/age line, author role line, NTP timestamp line, supervisor
  name/licence (no sign-in — the inbox's fiction, one demo-text constant),
  hash/encryption copy, envelope labels, and "ENVELOPE TYPE N6" chrome stay
  demo: Phase 1 has no source for them.

## What is demo text (no source — delete with `demo-text.ts`)

MRN, address, time chips, overdue badge, target windows, durations, nav count
badges, header team names, dates in the chrome. None of these exists in Phase 1.

Queue (`QUEUE_DEMO`): the sync line, the per-card size line, the endpoint
line under a refusal, the NFC/export and signature-verification toasts, the
storage-meter line, and the dispatched-example card's envelope ID, patient
line, sent line, and transaction ID.

Addendum (`ADDENDUM_DEMO`): the MRN/age line, author role line, NTP timestamp
line, supervisor role/licence/note, hash line, envelope title/subtitle, and
staged-confirmation paragraph. The supervisor's name reuses `INBOX_SUPERVISOR`.

## Requested fixes carried by the working copies (not the references)

- Roster: header chrome matches the Brief page exactly (greeting style, icon
  toggle, date strip, tab style with inline count badges).
- Brief: text aligned left, not right (staging header, banner groups, table
  Action column).
- Brief: the boxes under the graphs sit at the columns' top (`justify-start`),
  not pushed to the bottom (`justify-between`).
- Workspace: header chrome identical to the other two pages; stock/meter
  figures aligned left with the rest of the text.
- Verification taste pass (design-taste skill, inside the tokens — no new
  hues, no new type): med-rec chip `rounded-lg` → `rounded-full` like its
  siblings; "View details →" capitalized; locked CTA shortened to "Complete
  Visit (Locked)" with the reason beside it (CTA wrap ban); `<dialog>` →
  conditional overlays with backdrop-click and Esc close like the other
  pages; `text-error`/`bg-error` → the identical-hex `status-now` token;
  dead markup removed.
- Emergency taste pass (same skill, same rule): every `#8E2A24` arbitrary
  value → the identical-hex `status-now` token (banner rule, pill, clock dot,
  transfer card, allergy box); print button relabelled "PRINT HANDOVER" since
  it prints rather than flips (the paste's rotate-180 demo behaviour is gone —
  §10 wants a print path, and the realistic delivery is the screen turned
  around or photographed); transfer drawer renders the real eight §5.10 rows
  instead of the paste's three invented codifications; `dir="auto"` on
  timeline text, entry box, and allergy line (§8).
- Queue taste pass (same skill, same rule): the paste's malformed `<nav
  data-path href>` opener → real `<a>` anchors like every sibling page; the
  "Rejected by EMR" pill and the resubmit CTA `rounded-lg` → `rounded-full`
  like every other pill and CTA on the page (shape-consistency lock); fake
  per-card kilobyte figures and SHA keys → the neutral "sealed on this
  device" line (lying-labels fix — attempts are not counted in Phase 1);
  `dir="auto"` on patient names, refusal text, and addendum text (§8).
- Addendum taste pass (same skill, same rule): the paste's arbitrary
  `focus-within:shadow-[0_0_0_2px_…]` ring → `shadow-sm` like the sibling
  wells (no off-token values); the author name is an input, so it keeps a
  hairline bottom border for affordance (`border-outline-variant/40`, the
  inbox search field's treatment); the confirmation's "Return to Active
  Visit Ledger" → "Return to Closed Visit" (lying-labels fix — the Visit is
  terminal, not active); the paste's custom geometric checkbox → a native
  checkbox (the throwaway's CSS marker carries no state a test can see);
  prior-addenda rows are new (the paste lists none) and follow the inbox
  row pattern — pill status, `dir="auto"` on names and text (§8).

## What is deliberately unwired

The Start Visit button only changes its own label: starting is a §5.5 state
transition and belongs to a POST the API does not have yet.

The Cancel popover's four reasons are the pasted demo list, not the seven real
`cancelled` rows in `docs/clinical-content/reason-lists.md`. Confirm shows the
toast and writes nothing. `POST /api/visits/{id}/cancel` is tested and ready;
wiring this popover to the real list is the shippable rebuild's first job.

## Known SSOT violations carried by this folder

CDN Tailwind + remote Google Fonts (breaks offline §4.10 / no-CDN §12);
~35-colour palette outside the 9+3 budget (§4); Material Symbols icon font
(§7.3 allows self-hosted inline SVG only); JS theme toggle instead of the
POST→cookie route (§9); non-glossary state words (CONTEXT.md). The rebuild
keeps this layout and swaps each one out.
