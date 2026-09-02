# Project Noor — Architecture (SSOT)

> **Status:** Sections 1–8. §1–§3 written 2026-08-27 after Phase 2 research; §4 (the Golden Case) written 2026-08-27 and revised 2026-08-28; §5 (the Visit lifecycle) written 2026-08-28; §6–§8 maintained continuously. Phase 1's documentation closed 2026-08-28 with ADRs 0005–0007 (§7). Audited for internal consistency 2026-08-28.
>
> This document is built **incrementally** — one section per phase discussion. It states *what must be true*, not *how* the system is built. Implementation detail is written only after the relevant phase has been grilled.
>
> **Conflict resolution:** if a prompt contradicts this document, this document wins. Raise the conflict; never silently bypass it.

## 1. What Noor is

Project Noor is a workflow orchestration layer over a clinical decision support (CDS) engine for home healthcare in Saudi Arabia, aimed at chronic disease management — diabetes and hypertension.

**Noor owns the visit and its review. The EMR owns the record of both.**

In production, Noor is EMR-integrated: it reads patient demographics and labs from the EMR, and writes visit data back. Clinicians never document from scratch. Noor keeps its own interface for the visit itself.

Noor is not standalone third-party software, and it is not an alerting module living inside someone else's chart. It is the destination for the home visit.

### 1.1 The integration boundary

The EMR is a **data source and a data sink**. It is never the host of the experience, and never the thing that decides whether the clinician enters Noor.

This matters because of a measured failure. The JAMIA Epic deployment study in `docs/research/how_cds_engines_work.md` found that when a SMART on FHIR app was an optional side-trip from charting, overall app use was **6.0% of interactions** — the authors name it "app fatigue," analogous to alert fatigue. Single-click launch was not available for the prompt type involved.

Noor avoids this by shape rather than by hope: the clinician opens Noor because Noor runs the visit. **The moment Noor becomes something a clinician could skip, it is in the 6%.**

Three data states must remain distinct at all times. Conflating any two of them is how silent malfunctions happen:

| State | Meaning |
|---|---|
| Present | The value exists in the record |
| Absent | The record has no such value |
| Unreachable | The EMR could not be queried |

Write-back to the EMR must be **structured** — an order suggestion, a task, a flagged item. Never narrative text buried in a visit note. Narrative write-back recreates the two-actor handoff problem inside the solution.

**Prototype constraint:** the integration boundary is defined now and backed by fixtures, not by a purchased EMR. Real FHIR calls replace the fixtures later without changing anything above the boundary.

## 2. The eight non-negotiables

Each rule is derived from `docs/research/why_cds_engines_fail.md` and `docs/research/how_cds_engines_work.md`. Evidence is cited so that any rule can be re-argued against its source rather than against opinion.

### N1 — Fire automatically, inside the visit. Never a "look it up" button.

**Evidence:** Kawamoto et al. (BMJ 2005, 70 controlled trials): **0% success** when clinicians had to seek the system out, versus 75% when advice was provided automatically. Automatic provision in workflow was the most statistically significant of the four predictors (P<0.00001).

**Workflow consequence:** if Noor ever requires the nurse to tap "check guidelines," the quality of the rules is irrelevant. This also forbids depending on the EMR to nudge the clinician into Noor.

### N2 — One executable action, scoped to whoever is standing in the room.

**Evidence:** providing a recommendation rather than an assessment is one of the four independent success predictors in Kawamoto's meta-regression (P=0.0187); systems with all four succeeded in 94% of trials against 46% without. The source publishes significance per predictor, not effect size, so no percentage-point figure is claimable for actionability alone.

**Workflow consequence:** "Poor glycemic control" is a failure. "Titrate metformin to 1000mg BD" is a pass *only if the person present can do it*. A recommendation the field clinician has no authority to execute is an assessment wearing an action's clothes, and must be routed to whoever can act on it instead.

### N3 — Cap the recommendations per visit.

**Evidence:** override rates reach **98.6%** among providers receiving more than 5 alerts/day, and burden is hyper-concentrated — 88% of providers see fewer than 1/day, so the intervention fails precisely where it fires.

**Workflow consequence:** if the engine has six things to say, it says the one that changes today's action and files the rest. The cap is **three**, with the reasoning and the mechanics in §4.7.

### N4 — No hard stops. Every dismissal captures a structured reason, and that reason is engine data.

**Evidence:** hard stops are "unacceptable… because decision support cannot replace the physicians' responsibility for the treatment of the patient." Reviewers agreed with clinicians in **95.6%** of overrides of *valid* alerts; 36.5–39% of alerts are outright false positives; adverse events followed only 2.3–6% of overrides. HL7 CDS Hooks makes override-reason capture part of the standard itself (Feedback API).

**Workflow consequence:** an override is a bug report about the rule, not disobedience by the clinician. Override rate per rule is a first-class metric with the authority to **retire a rule**.

### N5 — Every recommendation shows its provenance and its strength.

**Evidence:** automation bias RR **1.26** (95% CI 1.11–1.44) — clinicians follow erroneous advice more often than no advice at all; 6–11% of consultations flip a correct unaided answer to a wrong one. The mitigations with evidence behind them are precisely: display the system's reasoning, show per-recommendation confidence, and reduce the prominence of weak advice.

**Workflow consequence:** no bare imperatives. Every output names the guideline it came from and the patient data that triggered it.

### N6 — Declare missing data. Never silently degrade.

**Evidence:** sensitivity dies invisibly through uncoded/free-text allergies, missing weight, absent lab triggers, and stale drug databases. Wright et al.: an amiodarone thyroid-monitoring alert stopped firing when a *different* system changed amiodarone's internal identifier — undetected.

**Workflow consequence:** a rule that cannot evaluate must say so out loud ("no HbA1c in the last 6 months"). A quiet engine and a broken engine are otherwise indistinguishable.

### N7 — Deterministic rules in the decision path. LLM only outside it.

**Evidence:** Epic Sepsis Model — external AUC **0.63** versus 0.76–0.83 vendor-reported, PPV 12%, 67% of septic patients missed while alerting on 18% of all hospitalizations. RAG's pooled gain is only OR 1.35, with publication bias flagged (Egger P=.001). Hallucination persists at 11.3% in rare and complex cases, and one KG-RAG case scored perfect answer correctness with **0.00** faithfulness and context recall. The field's own verdict: the future "lies not in autonomous clinical decision-making, but in guideline-based, human-supervised, agent-managed architectures."

**Workflow consequence:** nothing that produces a clinical recommendation may be probabilistic or generative. LLMs are permitted only in non-decision roles — summarising, drafting, translating — where the output is never the basis of an action. This is also the zero-cost choice, and it keeps a static rule artifact outside the FDA's adaptive-AI PCCP regime.

### N8 — Rules are versioned, tested, observable artifacts.

**Evidence:** 93% of CMIOs had experienced at least one CDS malfunction, two-thirds at least annually; failures-to-*fire* are especially hard to detect and existing detection approaches are "inadequate." The governance study is blunt: "In the absence of effective governance practices, implementation of CDS may fail, despite the purchase or development of a sophisticated system" — Cedars-Sinai's system was shut down over usability. Arden Syntax encodes maintenance, library, and knowledge slots per module precisely for change control.

**Workflow consequence:** each rule carries an owner, a source guideline, a version, and a review date — as data, not buried in a function. Each rule has a test proving it fires (per `CLAUDE.md`: new rule = new table-driven test row, written first, must fail). The engine logs **"evaluated, did not fire"**, not only "fired."

## 3. Context correction on the failure research

The failure literature is overwhelmingly hospital CPOE — order-entry volume, prescribing-driven, 196,225-alert datasets. Noor is a home visit: roughly 4–8 patients a day, one at a time, around 30 minutes each. Two consequences shape the design:

- **Alert fatigue is a structurally smaller risk for Noor** than the raw literature implies.
- **Actionability is a structurally larger one**, because the field clinician frequently cannot execute the recommendation — no prescribing authority, no lab on the spot.

The upside: Kawamoto's predictor "delivery at the time and location of decision-making" is exactly where hospital CDS cannot reach. In home chronic care, the decision point is the living room. That is Noor's structural advantage — inherited from the setting, not built.

The corresponding risk has no coverage in the research at all: home healthcare is a **two-actor workflow** — field clinician plus supervising physician. A recommendation must survive the handoff and still be acted upon. Structured EMR write-back (§1.1) is the mechanism; whether it works is the largest unvalidated assumption in the design, and it must be the spine of the Golden Case.

## 4. The Golden Case — the routine visit

> Grilled 2026-08-27. This section states what must be true of a Visit. Bolded terms are used strictly in the sense defined in `CONTEXT.md`.

### 4.1 Why the silent visit is the primary case

The Golden Case is a **Routine Visit** in which Noor issues **no Recommendation at all**, because nothing in the Patient's data warrants one. This is the common case in chronic disease management — surveillance, not diagnosis — and it is deliberately the case the prototype is built around.

Zero is a boundary condition, and boundary conditions are where systems fail invisibly. A Visit producing three Recommendations proves the rules can fire. A Visit producing none proves something harder: that the engine ran, evaluated everything it was meant to evaluate, found nothing, and can demonstrate as much. **"Noor found nothing" and "Noor is broken" must never look alike.** That is N6 promoted from a rule about individual data points to the property the whole deliverable is judged on.

The consequence is that a Routine Visit normally produces **many Findings and zero Recommendations**. This is the load-bearing reason the two concepts stay separate: Findings are how Noor shows its work when it has no instruction to give.

A Field Team that reads its first quiet Visit as a malfunction is not recoverable. Nothing later in the design earns that trust back.

### 4.2 The Visit Protocol

Eight sections, fixed order, none may be absent: **Visit Reason**, Concerns & Interval History, **Medication Reconciliation**, Vitals, **Physical Examination**, **Self-Care Check**, **Care Plan**, Notes.

The sequence above is the order the sections occupy **in the record**. It is fixed; the content inside each section varies with the Patient. Sections may be *completed* out of that order, because the Junior Physician and the Nurse work in parallel in the same room — with one exception: **the Care Plan is assembled after all seven others, Notes included**, because it is assembled from what they produced. So Notes sits last in the record and is completed before the Care Plan, and that is the only place where the record's order and the working order come apart.

Both Visit types run this same spine. There is no separate Baseline form.

**Visit Reason is not a chief complaint.** Chief complaint is an acute-presentation concept; a Routine Visit usually has no complaint at all, so a complaint-led engine systematically misses exactly what surveillance exists to find. Visit Reason records why this Visit is happening — scheduled review, post-discharge follow-up, Patient-initiated concern — and never a symptom.

**Concerns & Interval History has two halves, shaped differently on purpose.** The interval history is a fixed tick-list of the events Noor must be able to reason about — a hospital admission, an emergency department attendance, review by another doctor, medication started or changed elsewhere, a fall, a hypoglycaemic episode, running out of medication. *"Had a bit of a turn last week"* is unusable; a ticked *hypoglycaemic episode* is the **Finding** that stops a sulfonylurea dose being pushed higher. The concerns half is free text, one item per concern, attributed to the **Patient** or the **Caregiver** who raised it — because *"his feet burn at night"* appears on no list and is the sentence that matters. The event list is clinical content (ADR 0007) and lives in `docs/clinical-content/interval-events.md`; the concerns are deliberately not a list at all.

**Medication Reconciliation records what is physically in the house, product by product, from a searchable local drug list.** The Field Team searches and selects; name, strength and form come from the list, and only the quantity remaining and the expiry are typed, because those differ per box. A drug name is the one field where a typo is dangerous — and free text would make an unrecognised drug indistinguishable from a misspelt one. **A product the list does not contain is an outcome, not a workaround:** it is recorded as free text, marked *unmatched*, and Noor states that it cannot reconcile that item rather than dropping it (N6, and Wright's amiodarone failure). Noor then compares the house against the prescribed list and reports the differences itself — omissions, products nobody prescribed, strength mismatches, duplicates, expired stock. **The quantity remaining is the design's only objective adherence signal:** thirty tablets dispensed a month ago with twenty-six left is a problem you can see, without asking a question the Patient has every reason to answer politely. That is the **Self-Care Check**'s own rule — observed, never asked (§4.5) — applied to the medicine cupboard.

**The Physical Examination's required element list is composed by Noor**, from the Patient's conditions and whatever surveillance is overdue. The Field Team may add elements; it does not decide which are required. This is where the diabetic foot examination stops depending on whether anyone remembered.

### 4.3 The Baseline Visit

A Patient's first Visit runs the same eight sections with three differences:

1. The **Physical Examination** is complete rather than composed — there is no surveillance history to compose from.
2. **Goal of Care** takes the place of **Care Plan** — and like the Care Plan, it emits a **Between-Visit Plan**, restricted to the parts that need no ratified target (§4.8).
3. Noor issues **no Recommendation that depends on a target or a trend** — because neither exists yet.

**The Baseline label is visible before attendance.** On the Roster, Noor shows a
**Baseline Visit** or **Routine Visit** planning indicator computed from the
Patient's completed history. This gives the Field Team the protocol shape to
expect before leaving the building. It is a read-time indicator, not a stored
`VisitKind`; the Visit's recorded kind is settled again at Start (§5.5; ADR 0008).

That third rule is deliberately narrower than "no Recommendations." Tier 3 is never off, and insulin found in a freezer must fire on the first Visit as readily as the tenth. What the Baseline Visit withholds is comparison, not judgement.

It is also where the **Caregiver** is identified by name, the household's measuring devices are inspected, and the data floor the engine reasons over is established.

### 4.4 The Goal of Care and the ratification gate

The **Goal of Care** is proposed by the Junior Physician at the Baseline Visit and ratified asynchronously by the **Supervisor**. Until it is ratified, Noor withholds every Recommendation that depends on a target (§4.11). Ratification is due within seven days, and its latency is measured rather than assumed (`docs/clinical-content/response-windows.md`).

**Noor stores the home numbers. It never derives them.** Evidence for this section: `docs/research/individualised_targets_and_goal_setting.md`.

| Axis | Stored as |
|---|---|
| Home BP | floor and ceiling, systolic and diastolic |
| HbA1c | floor and ceiling |
| Home glucose | pre-prandial and post-prandial ranges |

Three rules govern the shape, and each one closes a documented failure:

- **The office-to-home offset is not a constant, so Noor never computes one.** The −5/−5 mapping holds only for a **140/90**-anchored target (ISH 2020, NICE, the Saudi SHA *treatment* row → 135/85). ACC/AHA anchors at **130/80**, and its own outcome-derived home thresholds are **129–131** — an offset of roughly **zero**. Saudi SHA uses both anchors in one document: classification at ≥130/80, treatment consideration at >140/90. An engine hard-coding "home = office − 5" double-offsets half the guideline space and titrates toward a number nobody published. The **guideline lineage and the office anchor are stored beside the numbers as provenance** (N5) — displayed to explain where the target came from, never used to recompute it.

- **Every axis is a band, never a ceiling.** ACP directs de-intensification below HbA1c 6.5%; Saudi SHA sets DBP floors of 70 with CAD and 60 with LVH. Roughly one million US older adults are potentially overtreated on insulin or a sulfonylurea, and hypoglycaemia hospitalisations in older adults now **exceed** hyperglycaemia ones. A target with no floor makes overtreatment unrepresentable — Noor could only ever say *too high*.

- **"No numeric target" is a value, not an empty field.** ADA's very-complex/poor-health band is literally "avoid reliance on A1C" — a deliberate clinical decision, and not the same thing as *not yet set*, which is the state the ratification gate withholds against. Collapsing the two would silence Noor permanently on the frailest Patients while looking exactly like the malfunction §4.1 forbids.

This is how consultant-grade judgement scales without consultant hours: **one Supervisor decision governs every field decision until the target is revised.** How many Visits that spans depends on the surveillance interval, which is clinical content (ADR 0007) and is not yet set — so the multiplier is real and its size is not yet a number Noor may claim.

The cost of the gate is **latency**, and it is measured rather than hypothetical. Senior ratification of a junior-set target has no evidence base anywhere in the target-setting literature; the closest analogy with data is radiology over-read, where junior major-discrepancy rates were low (1.7%) and the quantified harm of the safeguard was **delay** — 8.6% of management-changing discrepancies delayed care. Since therapeutic inertia is the disease an explicit target exists to treat, a ratification queue that becomes slow reintroduces it in a new costume.

### 4.5 The Self-Care Check

The section that establishes whether the prescribed treatment is reaching the Patient at all — medication storage and handling, administration technique, measurement technique, foot care, sick-day rules. Evidence for this section: `docs/research/medication_technique_and_self_care.md`. Two rules govern it:

- **Every item is observed or demonstrated, never asked.** "Do you rotate your injection sites?" returns *yes* from every patient alive. The Nurse looks at the abdomen, holds the pen, reads the meter, opens the fridge.
- **Every task is attributed to whoever actually performs it** — Patient or Caregiver. A Recommendation aimed at the wrong executor is an assessment wearing an action's clothes (N2), and between Visits the Caregiver is frequently the only executor present.

This section is the prototype's structural advantage. It captures a class of clinical finding that exists only inside the home and appears in no health record anywhere: insulin stored above range or frozen, lipohypertrophy on palpation, needle reuse, missing resuspension, the pen withdrawn too early, a sulfonylurea taken before a meal that is then skipped, metformin on an empty stomach driving quiet discontinuation, heat-damaged test strips, date residue on the fingers producing falsely high readings, a cuff two sizes too small, decanted unlabelled pill boxes, an over-the-counter NSAID stacked on an ACE inhibitor and a diuretic, bare feet on hot tiles with established neuropathy.

**Every competitor's data starts at the front door. Noor's starts inside it.**

### 4.6 Suppression

A Self-Care Check failure suppresses the titration Recommendation it undermines, and Noor issues the correction instead. Full reasoning, rejected alternatives, and testing obligations: `docs/adr/0002-self-care-failure-suppresses-the-recommendation-it-undermines.md`.

**Suppression runs before the cap in §4.7.** A suppressed Recommendation never competes for a display slot; the correction that replaced it competes in its place.

### 4.7 The N3 cap is three

The per-visit cap left open in N3 is **three Recommendations**.

The 98.6% override figure is per provider per *day*, not per encounter. Transplanted literally into a 4–8 patient day it would permit fewer than one Recommendation per Visit — the thin-transplantation error §3 warns against. The honest anchor is **execution capacity**: roughly three actionable items can be carried out and taught inside a 30-minute Visit, and the Caregiver's retention ceiling for new instructions lands in the same place.

Mechanics:

- **Tier 3 sits outside the cap.** An emergency does not queue behind a display limit.
- Slots fill in one order, and it has three keys: **descending Escalation Tier**, then **what changes today's action**, then **descending deferral count**. Each key breaks ties in the one before it, and nothing else enters the comparison.
- **Deferral count is the third key, not a promotion.** A Recommendation carries the number of Visits it has been **Filed** across. Between items a tier apart it changes nothing; between items equal on today's action it decides the slot. Without it, an item that never changes today's action starves permanently behind its own peers. Whether a long-deferred item should ever outrank one that changes today's action is a Phase 3 question, left open here on purpose.
- The cap counts **decisions, not plan lines.** One titration decision with four steps in the Between-Visit Plan is one Recommendation.
- The cap is a **display** constraint, not a data constraint. Everything unshown is **Filed** — generated, recorded, written back, still valid — never deleted.

**Three is a ceiling, never a quota.** Noor is allowed to say nothing, and on the Golden Case it does.

### 4.8 Closing the loop without new infrastructure

The **Care Plan** emits a **Between-Visit Plan**: pre-agreed titration steps, a home measurement schedule, and stop rules. Every line is machine-testable — a threshold, a schedule, or a rule — never prose. This is the delegated-titration mechanism that moved outcomes in TASMIN-SR and HyperLink; monitoring without it is inert.

A Routine Visit **opens by scoring the previous Between-Visit Plan.** The Nurse reads the glucose meter's and the BP device's stored memory on arrival, so the plan emitted at Visit N is scored at Visit N+1 entirely inside the Visit. No transmission, no connectivity, no device procurement, no cost.

**The three parts have different dependencies, and the Baseline Visit is where that matters.** Only titration needs a ratified **Goal of Care**, because titrating means titrating *toward* something. A schedule is a calendar, not a comparison; a stop rule is an absolute threshold of exactly the Tier 3 shape that §4.3 and §4.10 both certify as needing neither a target nor a trend.

| Part | Needs a ratified Goal of Care |
|---|---|
| Titration steps | **Yes** |
| Measurement schedule | No |
| Stop rules | No |

So **a Baseline Visit emits a Between-Visit Plan carrying the measurement schedule and the stop rules, with titration resolved by its reason** — *no ratified Goal of Care*. This is §4.11's withholding scoped by §5.8's resolved-not-filled, not a new mechanism. The alternative sends a household home from an enrolment visit holding a glucose meter, with no schedule and no number that means *call someone* — and leaves the first Routine Visit nothing to score, delaying the loop by a full Visit cycle.

**Every Home Reading carries its source.** The devices already in these homes are not verified to store timestamped readings (§6), and the zero-cost fallback is a **Caregiver** paper log. Both produce the same shape — a value and a time — and not the same truth: a log is *self-reported*, which is the one thing §4.5 refuses to accept anywhere else in the Visit. So the source is recorded as data — *device memory* or *Caregiver paper log* — and displayed with every **Finding** derived from it (N5). Noor closes the loop on whichever the household has, and never presents a remembered number as a measured one.

A between-visit runner is therefore a clean upgrade rather than a redesign: it reads the identical artifact and fires earlier. The Between-Visit Plan is the reason that upgrade needs no new data model.

### 4.9 The integration boundary in practice

Noor reads seven things: demographics, problem list, medication list, labs with dates, surveillance dates, allergies, and the roster of **Scheduled** Visits.

**The roster is a read, never a write.** Noor does not schedule, reschedule, or cancel on anyone's behalf. It records what became of a Visit it was given (§5.2). A roster entry carries the Patient, the date, and the Visit's **reason for being scheduled** — which is what the **Visit Reason** section opens with, and the reason that section needs no connectivity in the house (§4.10). For clarity before departure, each Scheduled entry also shows a **Baseline Visit** or **Routine Visit** planning indicator from the Patient's current completed history. That indicator does not create a clinical write and is recomputed when the Visit starts.

Noor writes seven, all structured:

| # | Write-Back item |
|---|---|
| 1 | **Visit outcome** — terminal state, the Start timestamp (the attendance record, §5.5), any **Emergency**'s start and end times, the structured reason where one applies, which sections never ran, and on an **Ended Early** the statement that the previous **Between-Visit Plan** remains in force, with its date (§5.6) |
| 2 | **Observations taken in the house** — Vitals, the **Home Readings** with their source (§4.8), and the **Physical Examination** against the element list Noor composed |
| 3 | **Self-Care Findings** |
| 4 | **Medication Reconciliation outcome** — what is in the house, the discrepancies against the prescribed list, or the declaration that discrepancy detection was **Unreachable** (§4.10) |
| 5 | **Recommendations — every one generated, with its status.** Accepted; overridden with its structured reason (N4); **suppressed**, with the Self-Care **Finding** that suppressed it (ADR 0002); or **Filed**, with its deferral count (§4.7). Each carries its provenance and strength (N5) |
| 6 | **The Between-Visit Plan** — titration steps, measurement schedule, stop rules. Machine-testable lines, never prose (§4.8) |
| 7 | **The proposed Goal of Care** — **Baseline Visit**s only, and the one write that is itself a request for a response |

Three collapses hold the list at seven, and each is load-bearing:

- **A Supervisor task is not an item on this list.** Owner-and-due-time is a *property* of anything requiring a response, carried by items 5 and 7, not a row beside them.
- **Shown, suppressed and Filed Recommendations are one item, not three,** because the N3 cap is a display constraint and not a data constraint (§4.7). Everything generated is written back.
- **The Emergency record folds into item 1.** ADR 0004 makes its duration clinical data, and duration is part of what happened during the attendance.

Two things are deliberately not on this list. The **Handover** is rendered locally and handed to the ambulance crew (§5.7), never to the EMR. And a **Cancelled** Visit writes nothing at all (§5.4).

Anything requiring a response carries a **named owner** and a **due time derived from its Escalation Tier**, because a work queue understands urgency only as a due date. **A Write-Back with no owner and no due time is narrative text wearing structure's clothes** — it reproduces the 6.0% app-fatigue finding one actor downstream, in the Supervisor's inbox instead of the clinician's chart.

The "evaluated, did not fire" log (N8) stays inside Noor. It is engine telemetry, not part of the patient record.

**The fixtures must be hostile.** A fixture serving only clean patients is a demo prop. The fake patients must misbehave the way real records do: no HbA1c in eighteen months, a free-text allergy, a request that times out, a drug name the system does not recognise (Wright's amiodarone failure), a write the EMR rejects. A fixture that cannot fail cannot demonstrate N6.

The list of what Noor needs from an EMR is itself a pitch asset: it answers the first question any hospital IT department asks.

### 4.10 Offline is the default, not the fallback

A Visit completes with no connectivity. Noor runs on the device in the home and holds the Patient's Goal of Care and last Between-Visit Plan locally; the EMR is contacted opportunistically and never depended on in the moment.

Turning a Field Team away because software cannot reach a server is software preventing care — the same category of error N4 forbids. The team is standing in the house.

Six of the eight sections never needed the EMR in the moment: **Visit Reason** (carried on the roster entry, cached when the Visit was **Scheduled** — §4.9), Concerns & Interval History, Vitals, Self-Care Check, Notes, and the Care Plan's assembly. The remaining two degrade, and must declare the **Unreachable** state when they do:

| Section | Degradation when Unreachable |
|---|---|
| Medication Reconciliation | Records what is in the house; cannot name the discrepancy against the prescribed list |
| Physical Examination | Cannot compose the required list from surveillance dates → **falls back to the complete examination** |

That fallback is the safe direction and costs nothing new — it is the Baseline Visit's configuration reused. An unnecessary foot examination costs three minutes; one skipped because Noor could not read a date is the amputation pathway.

Also required:

- **Tier 3 fires offline.** 205/125 is a threshold, not a comparison against anything.
- **Write-Back queues visibly**, survives a device restart, and shows the Field Team that it is still pending. A silently failed Write-Back is worse than none: the Supervisor's task never arrives and nobody knows it did not.
- **One Unreachable state.** "No signal" and "EMR is down" are not distinguished — operationally identical, and two states would mean two code paths and two test sets for one outcome.

### 4.11 The withholding principle

Four separate decisions have the same shape:

| Trigger | What is withheld |
|---|---|
| A Self-Care Finding corrupts the signal (ADR 0002) | The titration it would have justified |
| No ratified Goal of Care yet (§4.4) | Everything depending on a target |
| An input is Unreachable (§4.10) | Everything depending on that input |
| A section never ran (§5.6) | Everything depending on it — **including** whatever that section's Findings would have suppressed |

One mechanism, not four: **Noor declines to opine when its inputs do not support an opinion, and names the input that was missing.** Tier 3 is exempt from all four.

The fourth row is the sharpest, and it is why an **Ended Early** Visit is not merely a Visit with less data. A **Self-Care Check** that never ran withholds the titration it never got the chance to veto — the absence of a suppressor is not evidence that the condition it suppresses is absent (ADR 0002).

This is the design's thesis. The engine earns trust through the accuracy of its silence, not the volume of its output — which is why the Golden Case is the silent visit.

### 4.12 What this section does not validate

The two-actor handoff remains the largest unvalidated assumption in the design (§3). A working prototype demonstrates that Noor can produce a due-dated, owned, structured Write-Back. It does not demonstrate that a Supervisor acts on one, and it does not demonstrate that a real EMR accepts one. Both limits must be stated plainly rather than implied, because overclaiming is precisely the failure mode `docs/research/why_cds_engines_fail.md` documents.

## 5. The Visit lifecycle

> Grilled 2026-08-28. Where §4 states what must be true *inside* a Visit, this section states what must be true across its whole span — from the roster to a terminal state. Bolded terms are used strictly in the sense defined in `CONTEXT.md`.

### 5.1 One Visit, six states

A **Visit** is one object from the moment it appears on the roster to the moment it closes. Not a slot plus an encounter.

Any two-object split has to answer which object owns the **Findings** Noor computed before anyone arrived, and both answers are wrong: a scheduling slot that owns clinical data, or an encounter that must exist before the attendance it records. One object, six states:

| State | Entered from | Exits to |
|---|---|---|
| **Scheduled** | the roster | In Progress, Cancelled |
| **In Progress** | Scheduled | Completed, Ended Early, Emergency |
| **Emergency** | In Progress | In Progress, Ended Early |
| **Completed** | In Progress | *terminal* |
| **Cancelled** | Scheduled | *terminal* |
| **Ended Early** | In Progress, Emergency | *terminal* |

**The state machine terminates at the front door.** Everything that happens afterwards is a separate axis and must not be modelled as a Visit state:

- **Write-Back** has its own status — queued, confirmed, rejected (§4.10) — and a rejected Write-Back does not reopen a **Completed** Visit.
- **Supervisor** review attaches to *items*, never to the Visit. One Visit can have three items in three different review states at once, which is unrepresentable as a Visit state.
- "This Visit has items awaiting review" is therefore **derived on read, never stored.** A stored flag is a second copy of the truth that goes stale the moment an item is signed.

Why the Supervisor does not gate **Completed**: `docs/adr/0003-completion-is-the-field-teams-act.md`.

### 5.2 Scheduled — the state that makes offline possible

§4.10 requires a Visit to complete with no connectivity. That is only achievable because **Scheduled** is a working state, not a waiting one. While a Visit is Scheduled, Noor caches opportunistically:

- the seven EMR reads (§4.9)
- the **Goal of Care** and its ratification status
- the last **Between-Visit Plan**, to be scored on arrival
- **Filed** Recommendations with their deferral counts
- the version of the rule artifact that will evaluate the Visit (N8)

Three rules govern the cache:

- **Every cached value carries an as-of time.** Staleness is a timestamp on a **Present** value, never a fourth data state — §1.1 admits exactly three, and a fourth would double the code paths and the test sets for one outcome.
- **The Field Team can see readiness per Visit before leaving the building**, and it has no power to block departure. Software that refuses to let a team travel is software preventing care (N4).
- **The Field Team can see the planned Visit type per Visit before leaving the building.** The Roster shows a Baseline Visit or Routine Visit planning indicator from current completed history. It is not a stored VisitKind and never blocks departure; Start recomputes the recorded kind from the history that exists then.
- **An unprepared Visit still starts.** It runs as **Unreachable** for everything, which is the degradation §4.10 already defines — the complete **Physical Examination**, **Medication Reconciliation** without discrepancy detection, and the withholding of everything that depends on a target. No new failure mode is introduced by a team that left before the cache filled.

**A Scheduled Visit whose time has passed is derived on read, never acted on.** Noor runs no scheduled job to sweep the roster, and never auto-cancels. An automatic cancellation would manufacture a clinical fact — that nobody attended — out of a clock reading. A human sets **Cancelled**, with a reason (§5.4).

### 5.3 The Brief — Findings before the knock, never Recommendations

The engine runs while the Visit is still Scheduled, over the record alone, and produces the **Brief**: what the Field Team reads before knocking.

It contains the **Vitals** trend across previous Visits, what the last Visit concluded, what surveillance is due — HbA1c, eGFR, retinal examination, foot examination — and, per N6, an explicit statement of what Noor could not see.

**The Brief cannot plot Home Readings**, and this is a consequence of the zero-cost constraint rather than an oversight. **Home Readings** do not exist outside a Visit: they are read from the devices' own stored memory on arrival (§4.8), so the between-Visit trend becomes visible when the Nurse reads the meter, not before. Transmitting devices would change this and nothing else.

**The Brief contains no Recommendation.** This is deliberate and it is the rule most likely to be "fixed" by a future reader, so the reason is recorded here: a Recommendation formed before anyone has examined the Patient is advice about a record rather than about a person, and it arrives in the room as an anchor. N5's automation bias is RR **1.26** with inexperience raising the risk, and the whole exposure of the design is a **Junior Physician**. Findings inform; a pre-visit Recommendation commits.

Two consequences:

- **The Brief is computed on open, never stored.** It must reflect the cache as it stands when it is read, and a stored Brief is a second, ageing copy of the truth.
- **Reading the Brief does not start the Visit.** Preparation is not attendance, and the Start timestamp (§5.5) is the attendance record.

### 5.4 Cancelled — the Visit that never started

Set by **either member of the Field Team**, from **Scheduled** only, always with a structured reason (§5.10). The Patient has no access to Noor, so a Patient-sourced cancellation is *recorded by* whichever member takes the call; the reason names the Patient as its source. Who set it is recorded either way (§5.13).

**No clinical Write-Back is produced, because no clinical content exists.** The state and its reason are recorded in Noor. Whether the EMR is told that a planned attendance did not happen is a scheduling concern belonging to whatever owns the roster (§4.9), not a clinical Write-Back.

### 5.5 In Progress — the deliberate start

A Visit becomes **In Progress** when either member of the Field Team performs a Start Visit action. It is deliberate, and its timestamp is the attendance record.

**Starting freezes the engine's inputs.** The engine reasons over one consistent snapshot for the duration of the Visit; a refresh is an explicit act and is timestamped. N5 requires every Recommendation to show the Patient data that triggered it — and inputs that shift underneath a Visit make "why did it say that?" unanswerable an hour later.

Two things are settled by the Start rather than earlier:

- **The Physical Examination's required element list is composed at Start** from the cached inputs (§4.2). Composing it while the Visit is still Scheduled would compose it from data that may be refreshed before the team arrives.
- **The Visit's recorded kind is Baseline if the Patient has no *Completed* Baseline Visit.** The Roster may show a Baseline Visit or Routine Visit planning indicator before this point so the Field Team knows what to expect, but the indicator is not the source of truth and is never persisted as `VisitKind`. Start recomputes the kind from the completed history that exists then. A Baseline Visit that ended without completing left the data floor unestablished, so the next Visit must be a Baseline again.

**Every Visit passes through Scheduled.** There is no attendance that creates a Visit at the door. A Visit arranged an hour beforehand is created Scheduled and then started, so the roster stays the complete record of intended attendance — which is what makes planned-versus-happened answerable at all.

### 5.6 Ended Early — the honest exit

Set by **either member of the Field Team**, from **In Progress** or from **Emergency**, always with a structured reason (§5.10). Where the decision was the **Patient**'s or the household's, the reason names them as its source, exactly as a cancellation does (§5.4). **What was captured is not discarded.**

Either member sets it because the alternative is a **Junior Physician** who has stepped outside to take a call becoming the reason a team cannot leave a house — software standing between a team and the door, which is N4's shape precisely (§5.13). Noor records *who* set it; it does not ration the act.

Four obligations follow, and they are the reason this state is not merely a Visit with fewer fields:

1. **Noor goes quiet on anything a section that never ran would have informed** — §4.11's fourth trigger. A **Self-Care Check** that never happened is an unreachable input, not a clean one.
2. **Recommendations that depend on nothing missing still fire**, and **Tier 3 fires regardless.** The team is still in the house, and an insulin vial found in the freezer is not less true because the Visit is ending.
3. **The Write-Back declares which sections never ran** — and states that **the previous Between-Visit Plan remains in force, with its date.** No **Care Plan** ran, so no new plan was emitted, and the Patient is measuring and titrating at home tonight against the old one. Silence about the plan reads as *no plan*, which is the one reading that is clinically unsafe. Where there *is* no previous plan — a **Baseline Visit** that ended early — the Write-Back states that in the same field rather than leaving it empty: **no Between-Visit Plan is in force**, and the household has no schedule and no stop rules tonight. An omitted line and a genuine absence must never share one appearance (N6).
4. **No Care Plan emits a Between-Visit Plan on a Visit that ends early, and the Care Plan section is where that is enforced.** Obligation 3 holds only while nothing new was written. The next Routine Visit opens by scoring whatever plan the last terminal Visit emitted (§4.8), so a plan written on the way out would quietly *become* the plan the household is measuring against — ratified by no Visit that finished, and contradicting the same Write-Back's statement that the old plan still stands. The state machine does not police this and should not: a plan already in the record cannot be un-emitted, and refusing the exit until the record is tidy is N4's shape exactly (§5.13). The obligation sits on the section that emits plans, which declines to emit one on the way out.

### 5.7 Emergency — an interrupt, not a terminal

**Emergency** is entered from **In Progress** when the Patient or **Caregiver** needs an ambulance now, and it exits either back to In Progress or to **Ended Early**. It suspends the **Visit Protocol** and it has a start time and an end time. Reasoning and rejected alternatives: `docs/adr/0004-emergency-is-an-interrupt-state.md`.

**Noor demands nothing at entry.** One action, zero required fields. The **Handover** the ambulance crew leaves with is rendered from data already on the device, offline (§4.10). Documentation of the Emergency is retrospective, and closing the Visit is what enforces it: **no Visit reaches a terminal state while an Emergency record is unresolved** — **Completed** by §5.8's gate, and **Ended Early** by the same requirement, because Ended Early is the Emergency's *other* exit and a gate on one of the two enforces nothing. **Resolved is stricter here than §5.8's bar for a section: an end time *and* at least one timeline entry.** Ending alone is not enough, and there is no structured-reason path — §5.10's four reason-bearing cases deliberately do not include an Emergency. A section can be honestly empty; the minutes of an ambulance call cannot be, because those minutes are what a receiving hospital, a later clinical review and any medico-legal enquiry all ask about, and *there was nothing to record* is not an answer any of the three can use. The cost is one deliberate act at worst: the start and end times are the state machine's own timestamps and are never typed, so one entry is the whole of what the close demands — and it is demanded after the ambulance has gone rather than during (ADR 0004), so it never stands between a team and the door (N4).

**Noor does not manage the emergency. It documents it and hands over the record.** Anything Noor demanded of a Field Team during those minutes would be taken from the Patient.

**The exit is a binary, and it carries no reason of its own.** Either the Visit **resumes**, or it terminates as **Ended Early** — and Ended Early already requires a structured reason (§5.10), so there is nothing left for the Emergency to add. The outcome decides which: the Patient left the house, by ambulance or otherwise → terminate; the Patient remained at home → the Field Team decides whether to resume the **Visit Protocol** or end it. A Patient who dies during the Visit terminates as **Ended Early**, with that reason.

Nothing here is an "Other with free text", and that is the point: a disposition the state machine has to route on cannot be a sentence someone typed.

**What the Emergency records is a timeline, not an enum.** Entries tagged *observed* or *done*, each carrying a time, free text inside. It is also the evidence the close requires, which is why every resolved Emergency carries at least one entry. An emergency cannot be enumerated in advance, and this is the one place in Noor where free text is safe — the **Handover** is rendered locally and handed to the ambulance crew, never written to the EMR (§4.9), so it never has to be machine-readable. The Emergency's start and end times *are* structured, and they *are* written back.

### 5.8 Completed — resolved, not filled

**Completed** requires all of:

- every section of the Visit Protocol **resolved**
- **any Emergency the Visit passed through resolved** — its record, not a section, and therefore named here rather than assumed (§5.7). Its bar is the stricter one: an end time and at least one timeline entry, with no structured-reason path
- the Visit's final section complete: on a **Routine Visit**, the **Care Plan**; on a **Baseline Visit**, a proposed **Goal of Care** in its place (§4.3). **Both emit a Between-Visit Plan** — the Baseline's restricted to the schedule and the stop rules (§4.8)
- every Recommendation that was *shown* dispositioned — accepted, or overridden with a structured reason (N4)

**Resolved is not filled.** A section is resolved when it has content, *or* a structured reason for having none — the Emergency record above being the one exception, and stricter rather than looser (§5.7). This distinction is load-bearing: a mandatory field a clinician cannot honestly satisfy gets satisfied dishonestly, and fabricated data in a surveillance record is strictly worse than a declared gap — a gap is visible to N6, an invention is not.

Noor can afford to be this strict about the front door only because **Ended Early** exists. Strictness with no honest exit is a hard stop, which N4 forbids.

**Completed depends on nothing outside the house** — not the Supervisor, not the EMR, not connectivity (ADR 0003).

### 5.9 Terminal states are immutable

**Cancelled**, **Ended Early**, and **Completed** close the record. Corrections are addenda, never edits.

The Write-Back may already have created tasks in the Supervisor's queue carrying owners and due times (§4.9). Editing the record underneath a live task means the task and the record disagree, with no way to tell which one was acted on. An **Addendum** is timestamped, attributed, and additive, so both versions survive.

The addendum interface is out of scope for the prototype; the immutability it depends on is not.

### 5.10 Structured reasons are engine data

Four things in this section require a reason: a **Cancelled** Visit, an **Ended Early** Visit, a section resolved with no content, and an overridden Recommendation. Nothing about an **Emergency** is among them, deliberately: its exit is a binary the state machine routes on, and where it terminates, Ended Early's reason already covers it — while its record has no reason path at all, because closing it requires a timeline entry rather than an excuse for having none (§5.7).

All four use the same construction: **a fixed list for that context, plus an additive "Other" with free text.** Free text alone is unanalysable, and a closed list forces the clinician into the nearest wrong bucket — which produces data that looks clean and means nothing.

**The rate of "Other" per context is a first-class metric with the authority to change the list.** This is N4's shape reused: an override is a bug report about a rule, and an "Other" is a bug report about a reason list.

**The lists are therefore clinical content, versioned the same way as the Physical Examination element lists and the surveillance intervals** (`docs/adr/0007-clinical-content-is-data.md`), and recorded in `docs/clinical-content/reason-lists.md`. A list that a metric has the authority to change cannot be an enumeration in the source code, because changing one needs a release and the release will not happen. N8 applies unchanged: owner, source, version and review date, as data.

**Two of the four are shaped rather than flat.**

| List | Shape |
|---|---|
| A section resolved with no content | A short core every section shares, plus rows only that section can raise. *No medication in the house at all* is a **Finding**; a generic *not applicable* files it as a shrug. *Declined to remove footwear* is the amputation pathway; *patient declined* is not |
| An overridden Recommendation | Two levels — whether the rule was **wrong here** or **right but not executable**, then the reason. A flat list cannot separate *fix the rule* from *fix the supply chain*, and N4 exists to drive the first |

### 5.11 Overrides, and routing as a floor

**Every tier is overridable, including Tier 3**, with a structured reason, recorded as an override. N4 admits no hard stops, and a tier that could not be overridden would be one.

**Overriding a Recommendation is not the same as acting outside its tier.** The tier still routes: an overridden Tier 2 item still requires the Supervisor to be reached during the Visit, because the override is itself a clinical decision of the kind that tier exists to review.

**A Tier 2 with no connectivity** is shown, marked not executable, and carried as a pending Write-Back item with the Supervisor as named owner and a due time of **immediately, on queueing**. Tier 2's window is zero by definition — the Supervisor was meant to be reached *during* the Visit (ADR 0001) — so the item arrives already overdue, and that is the intended reading rather than a defect to be smoothed away with a grace period. It is the one item class whose lateness is a fact about the house's connectivity, not about the Supervisor's diligence, and flattening it into a 72-hour queue would hide the only Visits where the routing did not work. `docs/clinical-content/response-windows.md` records it. The Visit completes normally — §4.10 does not permit connectivity to hold a Visit open.

**The Junior Physician can send anything to the Supervisor at any time.** The engine's routing is a floor, not a ceiling: software may add Supervisor involvement and may never subtract it (ADR 0003).

### 5.12 Which Visits reach the Supervisor

Not all of them. Four routes, and no fifth:

| Route | Trigger | Deadline |
|---|---|---|
| Tier 1 and above | The item's Escalation Tier (ADR 0001) | Derived from the tier |
| Goal of Care ratification | A **Baseline Visit** proposed a target (§4.4) | Its own window |
| Manual flag | The Junior Physician chose to (§5.11) | The flagged item's tier — or **Tier 1's window** where that item is Tier 0, since asking for review of something already done is Tier 1's shape exactly |
| **Silence Audit** | Sampling of Completed Visits that produced no Recommendation | A sampling rate, not a deadline |

The **Silence Audit** exists because §4.1 makes the accuracy of Noor's silence the property the deliverable is judged on, and N8 records that failures-to-*fire* are especially hard to detect. Reviewing only the Visits that spoke would measure precision and never once measure recall. Reasoning: ADR 0003.

**Every route carries a response obligation, and every one of them is clinical content** (`docs/adr/0007-clinical-content-is-data.md`), recorded in `docs/clinical-content/response-windows.md`. Three routes carry a deadline; the **Silence Audit** carries a percentage *with a floor* instead, because a percentage of a small number is zero, and an audit that never runs measures nothing at all.

**All four routes land in Noor, not in the EMR's task queue.** A task reading *"ratify target 135/85"* has stripped the guideline lineage, the reason that band was chosen, and the Self-Care **Findings** from inside the house that a ratification may depend on — and N5's automation-bias mitigation *is* the display of that reasoning. The **Write-Back** is unchanged and remains the record (§4.9). The Supervisor's surface is read-mostly — review, ratify, return with comment, sign off — and never edits a Visit, so §5.9 holds. Full reasoning and rejected alternatives: `docs/adr/0005-the-supervisor-reviews-in-noor.md`.

### 5.13 Actors, and what carries a name

The **Field Team** shares one tablet. One member examines while the other documents, so there is one pair of hands on the device at any moment. Noor is built for that rather than around it.

**Both members are named on the Visit. Observations belong to the Field Team; decisions carry an individual name.**

| What | Attributed to |
|---|---|
| Vitals, **Physical Examination**, Self-Care **Findings**, **Home Readings**, Notes | The Field Team |
| Dispositioning a Recommendation — accepted or overridden (N4) | The member who confirmed it |
| Setting **Cancelled** or **Ended Early** (§5.4, §5.6) | The member who set it |
| Closing the Visit (§5.8) | The member who closed it |
| An **Addendum** (§5.9) | The member who wrote it |

**Per-item attribution is deliberately refused.** On a shared tablet, whoever unlocks it stays signed in for the whole Visit — nobody switches user to type one examination finding. Attributing every observation would therefore record the *documenter* as the *observer*: false precision, which N6 rates as strictly worse than a declared gap, and the same reasoning that made §5.8 choose resolved-not-filled. Both members were in the room and both are accountable for the record. The distinction Noor cannot honestly obtain is one it does not claim to have.

**Decisions are different, and few** — three or four in a Visit, on exactly the acts where authorship carries clinical and medico-legal weight, and where a moment's pause is a feature rather than friction. An override is N4's bug report about a rule, with the authority to retire it; *"the Field Team overrode this"* cannot distinguish a prescriber's considered refusal from a tap-through, and those are opposite facts sharing one field.

**Attribution is not permission.** Noor records who confirmed a decision; it does not withhold the decision from the other member. A **Junior Physician** who has stepped outside to take a call must never be the reason a Visit cannot close — that is N4's shape precisely, software standing between a team and the door. Role restriction, if a service requires it, belongs to that service's governance and not to this prototype.

**Executors are not actors.** §4.5 attributes home tasks to the **Patient** or the **Caregiver**; §4.9 gives every responding Write-Back item a named owner, usually the **Supervisor**. None of the three uses Noor during a Visit. A Recommendation's executor and its author are separate fields, because N2's question — *can the person who must act actually do it?* — is unanswerable if they share one.

Members are chosen from a list, with no credential verification in the prototype (§6).

### 5.14 What this section does not validate

- **That a Field Team will choose Ended Early over pushing through.** Resolved-not-filled (§5.8) is a design bet that an honest exit beats a fabricated field. It is reasoned from N4 and N6, not measured, and only field use settles it.
- **That the Field Team's close is legally sufficient.** Whether a **Junior Physician** may close a home-visit record in Saudi Arabia without a consultant countersignature is unverified (§6). If a countersignature is required, ADR 0003's clinical argument survives unchanged and a signature obligation is added downstream of **Completed** — on the Write-Back axis, never as a Visit state.

## 6. Open items

- **NPHIES scope — unverified.** Saudi Arabia's national FHIR-based exchange platform exists; whether its scope covers clinical data exchange, or is still mainly claims and eligibility, is not established. This materially shapes the Phase 4 national-scaling argument. Verify before writing Phase 4.
- **Which EMR MOH home-healthcare facilities actually run — unknown.** It determines whether a due-dated, owned task (§4.9) is even accepted. Phase 3 concern, not Phase 1.
- **The Junior Physician's grade and independent prescribing authority** are not pinned down. Tier 0 and Tier 1 depend on where that line sits.
- **Whether a consultant countersignature is required on a junior physician's home-visit record in Saudi Arabia — unverified.** ADR 0003 makes **Completed** the Field Team's act inside the house. A countersignature requirement would not overturn that; it would add an obligation *after* the close, on the Write-Back axis (§5.14). Verify before the pitch, because it is a question a hospital will ask.
- **Device security and clinician authentication — out of scope, and the second question a hospital IT department will ask.** §5.13 chooses members from a list with no credential verification, and the tablet holds Patient data in someone's home. The workflow argument does not depend on this being solved, but the pitch must name it rather than let it be discovered.
- **The prototype runs as one local process, so "remote" is simulated.** Noor is a single Python application against one local store (`docs/adr/0006-offline-by-locality.md`); the Field Team's surface and the **Supervisor**'s review surface are two roles in the same application, not two devices across a network. This is deliberate — it makes §4.10's offline guarantee a property of where Noor runs rather than a synchronisation layer to be written — and it costs nothing in the workflow argument, because ADR 0005 fixes *where the decision is made*, not how the bytes travel. What the prototype therefore cannot show is that the handoff survives real latency, real authentication, and two people working at once. That is a deployment problem, and it is the one place the demo is not the product.
- **Whether the glucose meters and BP devices already in these homes store timestamped readings — unverified, and no longer blocking.** §4.8 records the source on every **Home Reading**, so the loop closes on either a storing device or a **Caregiver** paper log, and says which. What remains to verify is which of the two the field actually presents — it changes how much weight the scoring deserves, not whether Noor runs. Transmitting devices or a patient-facing capture surface would remove the question entirely; both are out of scope for the prototype and belong to the scaling argument.
- **The drug list is a demonstration subset, not a formulary.** §4.2's Medication Reconciliation searches a list bundled with Noor, covering diabetes, hypertension and the common comorbid drugs. It is clinical content under ADR 0007, and it is deliberately incomplete — so *unmatched* will fire more often in the prototype than it would in production. The demonstration should say that plainly rather than curate the fixtures to hide it. Production needs a real registered-products list; whether Saudi Arabia publishes one usable at zero cost is unverified.
- **No clinical content has a named owner or a review date yet, and N8 requires both before Phase 1 ships.** Every file in `docs/clinical-content/` carries `Owner: Unassigned` and `Review date: Unset`. N8 makes those fields *data*, not documentation, so an unowned list is a rule nobody can retire — the exact condition behind the 93%-of-CMIOs malfunction finding. The mechanism is built in Phase 1 regardless; what is missing is a person, and that is a service decision rather than a design one.
- **Most clinical content is still unsourced.** The Physical Examination element list per condition, the surveillance intervals, which Vitals are taken for which condition, and the **Self-Care Check** item list now carry unsourced starter values in `docs/clinical-content/` — chosen to make Phase 1 runnable, marked as such in every file, and replaced by the named owner with sourced values in Phase 1.5, each with the guideline it came from (N5, N8). The stop-rule library still exists only as a shape in this document, with no values behind it.
- **Banked Phase 3 edge cases:** the Suppression demonstration (the Golden Case does not exercise ADR 0002), and a Goal of Care left unratified before the first Routine Visit, which blocks the engine.
- **Excluded from the pitch as insufficiently sourced:** the 74%/50%/41% agentic-CDS adoption shares (single-source review, flagged for citation sloppiness in our own research file), and anything attributed to the Zymr vendor blog.

## 7. Section status

| Section | Phase | Status |
|---|---|---|
| Constraints + integration boundary (§1–§3) | 2 | Written 2026-08-27, §1 boundary widened 2026-08-28 (ADR 0005) |
| Golden Case — routine visit workflow (§4) | 1 | Grilled and written 2026-08-27, revised 2026-08-28 |
| Visit lifecycle — roster to terminal state (§5) | 1 | Grilled and written 2026-08-28, §5.6 fourth obligation added 2026-09-02 |
| Phase 1 blockers — stack, content boundary, section shapes, windows | 1 | Grilled and closed 2026-08-28 (ADRs 0005–0007) |
| CDS engine design + clinical rules | 3 | Not yet grilled — Phases 1 and 1.5 build first |
| Scaling + technical report | 4 | Blocked on Phase 3 |

## 8. Implementation phases

> Agreed 2026-08-28. §7 tracks which *sections of this document* are written. This table tracks what gets *built*, and in what order. The seam exists so the workflow can be finished and tested before any rule produces a **Recommendation**.
>
> **The two axes share their numbers, and they are not the same axis.** A phase number here means a build phase; the same number in §7 means a documentation phase. There is no build **Phase 2** because documentation Phase 2 was the research, which produced no software. Where this document says "Phase 1", "Phase 1.5" or "Phase 3" without qualification, it means this table.

| Phase | Delivers | Deliberately excluded |
|---|---|---|
| **1 — Workflow shell** | The Visit lifecycle (§5), the eight sections (§4.2), **Findings**, the **Brief** (§5.3), **Write-Back** (§4.9), the **Supervisor** review surface (§5.12, ADR 0005), the four structured reason lists (§5.10), the interval-event list (§4.2), the searchable drug list (§4.2, §6), the versioned clinical content (ADR 0007), the local offline store (ADR 0006), and the hostile fixtures (§4.9). The `Recommendation` type and its disposition lifecycle exist with no producer. | Every rule that produces a Recommendation |
| **1.5 — Evaluation harness** | Rule evaluation over that same clinical content, the "evaluated, did not fire" log (N8), and **Tier 3 rules only** — the one class §4.3 and §4.10 both certify as needing neither a target nor a trend | The *logic that assigns* a tier, **Suppression**, the N3 cap |
| **3 — Full engine** | The complete rule set, tier assignment (ADR 0001), Suppression (§4.6), the N3 cap (§4.7) | — |

What Phase 1.5 excludes is the **assignment** of tiers, not the tier itself. Its rules are Tier 3 by definition — a stop-rule threshold is what Tier 3 *means* (§4.10) — so the field is populated, by the rule's own content, and nothing chooses. Deciding a tier from a Patient's circumstances is Phase 3, and so is everything the cap and Suppression need in order to compare two Recommendations against each other.

Four consequences, all load-bearing:

- **Findings are Phase 1, not Phase 1.5.** §4.1 makes Findings the way Noor shows its work when it has no instruction to give, and three Phase 1 deliverables consist of nothing else: the **Brief**, the scoring of the previous **Between-Visit Plan** on arrival (§4.8), and every N6 missing-data declaration. A Finding carries no **Escalation Tier**, so pulling Findings forward drags no Phase 3 decision with them.
- **Clinical content is versioned from Phase 1.** The **Physical Examination**'s composed element list (§5.5) and every surveillance interval are clinical content with a source guideline, and N8 requires an owner, a source, a version and a review date *as data*. Phase 1.5 therefore adds Tier 3 rows to content that already carries all four, rather than building the versioning mechanism a second time. **What is content and what is welded into the code is a decided line, not a convenience:** clinical judgement a consultant revises is content; the eight non-negotiables and anything derived from them — including the N3 cap of three — are code, where changing them costs a diff and a passing test suite. Reasoning: `docs/adr/0007-clinical-content-is-data.md`.
- **The Completed gate is tested with hand-built Recommendations.** With no producer in Phase 1, the collection §5.8 gates on is always empty — and a gate tested only against an empty collection passes against an engine that has stopped working. That is ADR 0002's warning about asserting only the non-firing case, applied to the front door.
- **The Supervisor's surface is Phase 1 because Phase 1 already produces something only a Supervisor can resolve.** A **Baseline Visit** cannot reach **Completed** without a proposed **Goal of Care** (§5.8), and that proposal is the one **Write-Back** item that is itself a request for a response (§4.9). Shipping the emitter without the receiver would leave Phase 1's own output permanently unresolved, and would push the two-actor handoff — the largest unvalidated assumption in §3 — past the phase whose whole purpose is that the workflow is finished and tested. The **Silence Audit** has the same shape: it is a review of Visits that produced nothing, so it needs no engine.


