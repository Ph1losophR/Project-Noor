# Web plan — Project Noor

## 1. Scope and standing

This document is the page plan. It records **which screens exist, who sees each one,
and how you get from one to the next**. `docs/frontend_ssot.md` §1 delegates page
composition and routing here; that document keeps colour, type, space, the marks,
motion, delivery, and the form every guard takes (§7.4).

It is the third of three ranked documents and the lowest of them:
`project_noor_architecture.md` wins over `docs/frontend_ssot.md`, which wins over
this. Where any two disagree the conflict is raised, never silently resolved.

**It is also the most volatile of the three.** A screen moving is ordinary; the
behaviour behind it moving is not.

Unqualified `§` references point at `project_noor_architecture.md`. References to the
design system name it.

## 2. The addresses

Twelve pages, and no thirteenth without a decision recorded here.

| Address | What it is | Who opens it |
|---|---|---|
| `/` | two doors | either surface |
| `/visits?day=YYYY-MM-DD` | the **Visit List** — today unless the day says otherwise | Field Team |
| `/visits/{id}` | the Visit, rendered by its state | Field Team; the Supervisor reaches a terminal one |
| `/visits/{id}/brief` | the **Brief** (§5.3) | Field Team |
| `/visits/{id}/sections/{section}` | one of the eight | Field Team |
| `/visits/{id}/home-readings` | **Home Readings** (§4.8) | Field Team |
| `/visits/{id}/review` | what the close requires (§5.8) | Field Team |
| `/visits/{id}/emergency` | the **Emergency Protocol** | Field Team |
| `/visits/{id}/handover` | the **Handover**, and its print path | Field Team, then the ambulance crew |
| `/visits/{id}/addendum` | an **Addendum** (§5.9) | Field Team |
| `/supervisor` | the inbox: Patients | Supervisor |
| `/supervisor/patients/{patient_id}` | that Patient's open items | Supervisor |

Every transition is a POST to the thing it changes, answering with a redirect to the
page that shows the result:

| POST | What it does |
|---|---|
| `/theme` | the mode toggle — the one POST on every page (design system §9) |
| `/visits/{id}/start` | Scheduled → In Progress (§5.5) |
| `/visits/{id}/cancel` | Scheduled → Cancelled, with §5.10's reason |
| `/visits/{id}/sections/{section}` | saves one section; also the autosave's target (design system §12.1) |
| `/visits/{id}/home-readings` | saves the readings with each one's source (§4.8) |
| `/visits/{id}/complete` | In Progress → Completed (§5.8), from the review screen only |
| `/visits/{id}/end-early` | In Progress or Emergency → Ended Early, with §5.10's reason |
| `/visits/{id}/emergency` | In Progress → Emergency |
| `/visits/{id}/emergency/entry` | one timeline entry, tagged *observed* or *done* (§5.7) |
| `/visits/{id}/emergency/exit` | §5.7's binary: resume, or terminate as Ended Early |
| `/visits/{id}/addendum` | the Addendum, and its optional manual flag (§5.9) |
| `/visits/{id}/write-back` | sends what the close could not (§4.10) |
| `/supervisor/reviews/{review_id}` | one **Review Verdict** (§5.12) |
| `/supervisor/patients/{patient_id}/goal` | ratifies the **Goal of Care** (§4.4) |

## 3. Two doors

`/` offers the **Field Team** and the **Supervisor**. It picks a surface, not a
person: there is no login (§6), so nothing here identifies anybody, and every act
that needs a name asks for one at the moment it happens (§5.13).

The doors exist because both halves of the workflow run in one process (ADR 0006).
Walking from one to the other is how the prototype shows a handoff it cannot
demonstrate any other way.

## 4. The Field Team's Visit

```
/  →  /visits?day=…                       the day, all six states
        └── /visits/{id}                  the Visit, rendered by its state
              ├── /brief                  before the knock, and during
              ├── /sections/{section}      ←→  the strip moves sideways
              ├── /home-readings
              ├── /review        →  Complete Visit
              ├── /emergency     →  /handover
              └── /addendum               terminal Visits only
```

### 4.1 The Visit List

Today by default; `?day=` reaches any other day in either direction, because
yesterday's Completed Visits are what a **Silence Audit** reviews (§5.12) and what an
Addendum is written against (§5.9).

A row carries the Patient, why the Visit was scheduled, and its state. A **Scheduled**
row also carries the readiness of its cache (§5.2) and the **Baseline Visit** or
**Routine Visit** planning indicator (ADR 0008); a row that has started shows the kind
Start settled; a **Cancelled** row shows no kind, having never started. Readiness never
keeps a row from opening (§5.2, N4).

### 4.2 The Visit page renders by state

One address, and what it shows is what the Visit is:

| State | The page is | Its actions |
|---|---|---|
| Scheduled | readiness, the planning indicator, the way to the Brief | **Start Visit**; **Cancelled** behind a popover |
| In Progress | the eight sections with their resolved marks, Home Readings, and any Emergency the Visit passed through | **Complete Visit** → the review screen; **End Early**; **Emergency** |
| Emergency | nothing — every Visit route redirects to `/visits/{id}/emergency` | there |
| Completed, Ended Early | the record, read-only, and what the Write-Back is doing | send what is queued; write an Addendum |
| Cancelled | the reason and who set it, read-only | write an Addendum |

Three buttons in the action row, in that order, and no fourth. **Emergency** sits with
the others rather than off in a corner: the design system §7.4 guards it with a
popover, and a guard is what separates a grave act from an ordinary one — distance
only makes it slower to reach.

**Emergency suspends the Visit Protocol literally.** While the state is Emergency, every
address under `/visits/{id}` redirects to `/visits/{id}/emergency`, the Handover
excepted. §5.7 says the Protocol stops; this is the whole of what that means for
navigation, and it is one rule with one branch.

### 4.3 The eight sections, and the strip

One page per section. The slug is the section's name, so no address invents a synonym
`CONTEXT.md` forbids: `visit-reason`, `concerns-and-interval-history`,
`medication-reconciliation`, `vitals`, `physical-examination`, `self-care-check`,
`care-plan`, `notes`.

Above the form sits the **section strip**: the eight in the record's order, each with
its own resolved mark, scrolling sideways so it stays one row at 768px. It carries the
eight and nothing else. It is the whole of lateral movement, and it is a strip rather
than a next-and-back pair because the Visit Protocol is explicitly not a wizard —
the Field Team works in parallel and completes sections out of order (`CONTEXT.md`).

The strip renders on the eight section pages only. On the Visit page those eight are
already the body, and a strip there would be the page printed twice.

The **Care Plan** is reachable like any other section and refuses to assemble until the
other seven are resolved (§4.3, §5.6). Reachable and refusing is not a hard stop: the
refusal names what is unresolved, and the Field Team can act on it or leave.

One submit per section — **Save and return**, to the Visit page. The autosave posts to
that same route while the form is open (design system §12.1). With `noor.js` deleted the
submit is the only save, and leaving sideways from the strip without pressing it costs
that section's edits. §12.1 accepts that cost by name.

### 4.4 Kept out of the strip

- **The Brief** (§5.3) has its own page, open while the Visit is Scheduled and still
  open while it is In Progress. Reading it starts nothing, and it is computed when
  opened rather than stored.
- **Home Readings** (§4.8) has its own page, reached from the Visit. It is not one of
  the eight, and a ninth tile in a strip of eight would say it was. Each reading records
  which source it came from — the device's memory, or a Caregiver's paper log — because
  §4.8 requires that of every one.

### 4.5 The close is a screen

`/visits/{id}/review` states §5.8's four requirements, the met ones as plainly as the
unmet ones, and links each unmet one to the section that would satisfy it. **Complete
Visit** is offered here and nowhere else, and is absent until all four are met.

That absence is not a hard stop, because **End Early** is on the Visit page and never
withheld (§5.6, N4): a Field Team that must leave a house with three of four met leaves,
and what was captured survives. Who closed the Visit is asked here, from the two names
the Visit is carrying (§5.13).

### 4.6 Emergency

Entry is one popover with one button and no fields (design system §7.4, §5.7). Neither
step animates — the design system §11 exempts this act from the transition at both.

`/visits/{id}/emergency` is the Emergency Protocol: the timeline, a form that adds one
entry tagged *observed* or *done*, and the exit. Every value on it is already on the
device (ADR 0004).

The exit is §5.7's binary and nothing gates it: **Resume** returns the Visit to In
Progress, **End Early** takes the same reason popover as anywhere else. What §5.7
demands — an end time and at least one timeline entry, with no reason path — is demanded
at the close, so it is checked on the review screen alongside the other three.

`/visits/{id}/handover` renders whenever the Visit has an Emergency record, during and
after, and holds the print path. Forced light, no network of any kind, legible in
greyscale (design system §10).

## 5. The Supervisor

```
/  →  /supervisor                              Patients, the most pressing first
        └── /supervisor/patients/{id}          the items, answered here
              └── /visits/{id}                 a terminal Visit, read-only
```

### 5.1 The inbox is a list of Patients

Each Patient is a door carrying their name, how many items are open, and when the
soonest answer is owed. Nothing is answered on the inbox itself.

Grouped by Patient because the items are not independent questions (ADR 0005, amended for Patient grouping). A Tier 2 item and
an unratified **Goal of Care** for the same Patient are one conversation — the Goal is
the target that item was measured against (§4.11) — and answering them apart is
answering half of each.

### 5.2 The order of the work

One rule, three bands, on the inbox and inside a Patient alike:

1. **Tier 3 first.** It carries no due time because the answer is *now* (ADR 0001).
   Sorting on due time would file it behind everything due next week.
2. **Then whatever carries a due time, soonest first.** A Tier 2 queued from a house
   with no signal arrives already past its window, and §5.11 wants that visible rather
   than smoothed away.
3. **The Silence Audit last.** A sampling rate is not a deadline, and nothing about it
   is late (§5.12).

A Patient's own place in the inbox is set by their most pressing item under the same
three bands.

The word *urgency* appears nowhere on this surface. `CONTEXT.md` gives this ordering to
the **Escalation Tier** and forbids the synonym, along with severity, priority, acuity
and criticality.

### 5.3 The verdict

A row on a Patient's page carries what answering it requires: the item, the Visit it
came from and that Visit's date, the reasoning behind it (N5), and which of §5.12's four
routes sent it.

The answer is one **Review Verdict** — agreed or disagreed, which Supervisor, and the
note a disagreement must carry (§5.12). It is the only thing that removes the row;
nothing here clears by being read (§5.1, ADR 0009).

**Ratifying a Goal of Care is its own control, not a verdict.** Agreeing *is* ratifying,
and the Goal already records its ratifier and the time, so a second record would be a
second copy. Disagreeing leaves the row open, correctly — the Patient still has no
ratified target, and Noor is still withholding everything that depends on one (§4.11).

A **Silence Audit** row opens the Completed Visit at `/visits/{id}`, the same address
the Field Team uses, because a terminal Visit is read-only for everyone (§5.9). This
surface never edits a Visit and never holds one open (§5.12).

## 6. After the close

### 6.1 The Write-Back

**The close attempts the send once.** Where there is signal it goes, and the closed
Visit says so. Where there is none it fails, and the closed Visit shows the queue with
the EMR's refusal in words and a control that sends it. Nothing retries by itself: no
background loop, no timer, no polling. §4.10 requires the queue to be visible and
forbids the silent failure; it does not require a robot.

The close is committed before the send is attempted — structurally, since a send refuses
a Visit that has not closed — so no refusal can cost the close (§5.8, ADR 0003).

### 6.2 The Addendum

`/visits/{id}/addendum` is a screen, per the design system §7.4. It takes the text, which
member is writing it (§5.13), and one control that also sends it to the Supervisor as a
manual flag (§5.9, §5.12). It queues a Write-Back of its own, with no owner and no due
time, because it asks for nothing (§5.9, §4.9).

**A write that arrives for a Visit that has already closed lands here.** The section
POST is refused and answered with this screen, the submitted text already in the field —
nothing typed is discarded (§5.9). The autosave posts to that same route and is refused
the same way; its caller discards the response and stays quiet, so nothing on screen is
lost and the recovery happens on the submit a person actually pressed.

## 7. What every page carries

One header: the wordmark, one link up a level, and the theme toggle — a form POST to
`/theme` (design system §9), and the only mark on any page that is drawn rather than
written (design system §7.3).

No sidebar, no tab bar, no breadcrumb trail beyond that one link. The design system §2
fixes one arrangement at every width, and 768px of portrait has no column to spare.

Nothing polls, nothing refreshes itself, and nothing arrives that was not asked for.

## 8. Deliberate absences

- **No patient-facing screen.** §5.13 leaves the Patient and the Caregiver outside the
  software; the design system §2 assumes the tablet still gets turned toward them.
- **No screen schedules, reschedules, or moves a Visit.** The Roster is a read (§4.9).
  **Cancelled** records what became of an attendance and touches nobody's calendar (§5.4).
- **No screen edits a closed Visit** (§5.9). The Addendum adds.
- **No screen assigns a Field Team.** §5.13 makes the pair a standing assignment to the
  Patient; in the prototype it arrives as fixture data, and neither enrolment nor
  reassignment has a screen in Phase 1.
- **No inbox for the Field Team.** Nothing pushes work at them. The day's Visit List is
  the whole of what they are asked to do.
- **No dashboard and no metric screen.** Override rate per rule and the rate of *Other*
  per list belong to the phase that has rules to measure (N4, §5.10, §8).
- **No search.** Twelve addresses and one day of Visits do not need one.
- **No separate screen per terminal state.** `/visits/{id}` renders what the Visit is.

## 9. What this plan needs that Phase 1 has not built

A build list, not a wish list:

1. The Field Team pair on the **Patient**, snapshotted onto the **Visit** at Start
   (§5.5, §5.13).
2. The **Review Verdict** — the record, and the inbox filtering that reads it (§5.12).
3. The **Addendum** — the one write a closed Visit accepts, its own Write-Back, and its
   optional flag (§5.9).
4. A store query for Patients with unanswered items. Nothing answers that today.
5. **Done as part of item 4:** the Visit's date §5.3 needs rides on the store's inbox row
   (`InboxRow.visit_date`), not on `Review` — it is the store's fact, not the domain's.
6. The whole of `src/noor/web/` — routes, templates, view models, and the tests the
   design system §13 and the coverage gate require.

## 10. Named limits

- **No authentication (§6).** Either door opens for anyone, and every attribution is
  asked for rather than proved — the Addendum names a member without verifying them.
  §5.13 is a record of who acted, not a check on who may.
- **One process, so *remote* is simulated (§6, ADR 0006).** The handoff is demonstrable
  end to end and still unproven against real latency and two people working at once
  (§4.12, ADR 0009).
- **No Recommendation has a producer in Phase 1 (§8).** Every Tier mark and every
  disposition on the review screen renders from hand-built Recommendations, which is
  what §8 already requires the Completed gate to be tested against.
- **`popover` and `@view-transition` are Chromium-first.** Both degrade to a plain page
  (design system §7.4, §11), and the demo names its browser.
- **Losing `noor.js` costs lateral movement**, in the one place it is felt: leaving a
  section from the strip without pressing Save. The design system §12.1 states that cost;
  §4.3 above is where it lands.

