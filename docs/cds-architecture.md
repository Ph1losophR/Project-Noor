# Project Noor — CDS Engine Architecture

**Status:** Approved. This document is the Single Source of Truth (SSOT).
**Version:** 1.1.0
**Date:** 2026-08-13 (amended 2026-08-17 — §3.2 medication-scope declaration)

---

## 0. How to use this document

Read this file before writing any code. Do not deviate from it without explicit
user approval.

If a prompt contradicts this document, this document wins — surface the conflict
and ask for a resolution. Never silently bypass it.

**Security-critical constants** are architectural decisions, not implementation
details. In this project they are: authentication timeouts, RBAC definitions,
break-glass and access-log invariants (all three defined in §2.6),
audit-record content, fail-open/fail-closed policies, the severity ladder
(§9.1), the degradation invariant (§8.3), the erasure model (§2.5), the device
boundary's data contract (§4.2), the visit state machine and its transition gates
(§11.2), the obligation closure invariant (§11.8), the emergency-hatch invariant
(§11.7), and the CI governance gates (§10.4). None may be changed without
explicit user approval.

Evidence in this document traces to the archived research programme under
`docs/research/archive/`, cited inline as (§R-N) and mapped to files in §17.
Those files carry the primary-source footnotes. Where the
research found no source, this document says so rather than filling the gap.

**Section-number convention.** A bare `§N` refers to a section of *this*
document. A reference of the form `§R-11 §11.5` names section 11.5 *inside
research file 11* and is not a reference to this document's numbering.

### 0.1 Document map

| Part | Sections | Subject |
|---|---|---|
| Framing | §1–§2 | What Noor is; regulatory posture |
| Stack | §3 | Language, database, dependencies, hosting |
| **Inside the device boundary** | §4–§10 | `canon`, `engine`, `catalogue`: data validity, rule schema, evaluation, governance |
| **Outside the device boundary** | §11 | Clinical operations: encounters, visits, obligations, surveillance |
| Delivery and closure | §12–§17 | Testing, gates, build sequence, deferred work, open questions |

The seam between the two middle parts is the device boundary (§2.2) and is
enforced by a test (§4.2), not by convention.

### 0.2 Table of contents

**Framing**

- **§1 What Noor is** — purpose and scope, what it is not, first build target.
- **§2 Regulatory and compliance posture** — SaMD assumption (§2.1); the device
  boundary (§2.2); data residency and privacy (§2.3); clinical content copyright
  (§2.4); erasure and the immutable record (§2.5); access control and the security
  audit log (§2.6).

**Stack**

- **§3 Technology stack** — decisions (§3.1); medication knowledge (§3.2);
  terminology (§3.3); not in the stack (§3.4); hosting (§3.5).

**Inside the device boundary**

- **§4 Module architecture** — layout (§4.1); the enforced seam (§4.2); why an
  evaluator and not an inference engine (§4.3).
- **§5 The observation model** — the record; the narrative and structured signals;
  freshness (§5.1); derived values (§5.2); context flags (§5.3); informant (§5.4);
  the allergy record (§5.5); goals of care (§5.6); the medicine-manager (§5.7).
- **§6 `canon` — the data-validity layer** — three layers (§6.1); quality states
  (§6.2); unit resolution (§6.3); three boundary types (§6.4); repeat before
  action (§6.5); the observable registry (§6.6).
- **§7 Rule schema and catalogue** — the rule (§7.1); authored prose and the card
  (§7.2); thresholds (§7.3); content layout (§7.4); storage and approval (§7.5).
- **§8 Evaluation** — the call (§8.1); the evaluation record (§8.2); the
  degradation invariant (§8.3); engine invariants (§8.4).
- **§9 Findings, alerts, overrides** — three severities (§9.1); overrides (§9.2);
  safety surveillance (§9.3).
- **§10 Clinical content governance** — release lifecycle (§10.1); roles (§10.2);
  role doubling (§10.3); CI gates (§10.4); tenant profiles (§10.5).

**Outside the device boundary**

- **§11 Clinical operations** — registration and baseline (§11.1); the visit state
  machine (§11.2); triggers (§11.3); the pre-visit brief (§11.4); the in-home visit
  loop (§11.5); planned actions (§11.6); the emergency hatch (§11.7); the
  obligation ledger (§11.8); surveillance and the content loop (§11.9); offline
  (§11.10).

**Delivery and closure**

- **§12 Testing and validation** — the ladder (§12.1); release comparison (§12.2);
  case selection (§12.3); synthetic data (§12.4); calibrated-reliance audit
  (§12.5); verification claims (§12.6); shadow mode (§12.7).
- **§13 Gates** — blocks code (§13.1); blocks patient use (§13.2); explicitly
  unresolved (§13.3).
- **§14 Build sequence** — the ordered build, step by step.
- **§15 Deferred** — needs a named provider (§15.1); needs evidence or validation
  (§15.2); rejected outright (§15.3).
- **§16 Open questions** — business-blocking (§16.1); behaviour-blocking (§16.2);
  genuinely unanswerable here (§16.3).
- **§17 Research index** — the §R-N evidence trail and where it lives.

---

## 1. What Noor is

A **provider-owned, Saudi-localised clinical safety workflow for supervised home
visits** to adults with diabetes and/or hypertension, CKD risk, and polypharmacy.

The engine converts a versioned clinical rule catalogue and a quality-checked
patient data snapshot into bounded, cited, clinician-facing findings — and
records what it did, including what it did *not* fire.

Around that engine sits a **stateful clinical workflow** (§11): visits that move
through explicit states, findings that survive the encounter that produced them,
and work that is owned by a named person until it is closed. Noor is not a form
filler and not an alert layer. The engine is the core; the workflow is what makes
it operable in a home.

### 1.1 What Noor is not

- Not a replacement EMR, national health record, or telemedicine marketplace.
  Noor begins when a patient record already exists, though its baseline visit does act as a quality control for that record (§11.1).
- Not a general free-text documentation platform for rules to magically read. While the workflow explicitly captures the patient narrative — Chief Complaint, History of Present Illness, and Physical Examination — rules are strictly separated from free text. The evaluator reads only the structured clinical signals extracted alongside the narrative (§5, §6.6).
- Not a general drug-information database. The MVP medication layer is a
  deliberately bounded curated set whose scope is displayed to the user (§3.2).
  **The polypharmacy element of the scope above is bounded by that cap, not by
  the published instruments.** STOPP/START and Beers each span far more
  ingredients than §3.2 covers, so Noor screens polypharmacy within the curated
  set and routes the remainder to pharmacist or clinical review. Claiming
  instrument-level polypharmacy coverage on a curated set would be the same false
  claim §3.2 exists to prevent.
- Not an autonomous prescriber. Noor recommends; a clinician decides.
- Not a source of admissions-avoided or cost-saving claims. The defensible value
  claim is "may help improve risk-factor control" (§R-7). Utilisation outcomes
  are exploratory only (§R-8).
- Not a risk-score product. Risk models are deferred (§15.2).

### 1.2 First build target

A **credible engine plus safety case**: the data-validity layer, the evaluator,
the rule catalogue, evaluation records, the visit state machine and obligation
ledger, a validation harness, and a thin server-rendered demo UI driven by
synthetic cases.

This is what earns the conversation with an accelerator, a clinician reviewer, or
a home-health medical director. There is no named provider, no EMR to integrate
with, and no observed home visit — so anything whose shape
depends on those facts is deferred (§15).

---

## 2. Regulatory and compliance posture

### 2.1 Assume regulated SaMD

No SFDA primary source retrieved contains the US FDA's clinician-independent-review
exclusion (§R-2). **Noor is treated as regulated Software as a Medical Device
unless and until SFDA provides a written contrary determination.**

Consequence: clinician-reviewable output is a **safety control**, not a
regulatory exit. Every design decision that makes reasoning inspectable is
justified on safety grounds and must survive even if a regulatory carve-out later
appears.

#### The safety case is a maintained artefact, not a submission scramble

§R-2 lists what a SaMD safety case holds, and §R-9 makes the same point from the
engineering side: these are preserved **from day one**, because a record that was
not kept as work happened cannot be reconstructed afterwards. Nine components,
each with a named home in this document:

| Component | Where it already lives | Status |
|---|---|---|
| Clinical association and source provenance | Threshold registry (§7.3), pinned records (§8.2) | Built by the architecture |
| Analytical validation | Validation ladder rungs 1–3 (§12.1) | Built by the architecture |
| Usability and override testing | Calibrated-reliance audit (§12.5), override analytics (§9.2) | Built by the architecture |
| Local workflow validation | Shadow mode (§12.7) | Built by the architecture |
| Cybersecurity | Access control, session policy, log integrity (§2.6) | Built by the architecture |
| Version and rollback history | Immutable releases, classified changelog (§10.1) | Built by the architecture |
| Complaint handling | — | **Operational process. Provider-facing, gated (§13.2 item 11)** |
| Incident log | — | **Operational process. Provider-facing, gated (§13.2 item 11)** |
| Post-market review | — | **Operational process. Provider-facing, gated (§13.2 item 11)** |

Six of the nine fall out of decisions made elsewhere in this document, which is
the intended result: a safety case assembled from artefacts the build already
produces is defensible, and one assembled from documents written for a submission
is not. The remaining three are business processes with owners and cadences,
not software, and they are recorded as a gate rather than pretended into
existence here.

The relevant SFDA companion guidance — MDS-G23 (SaMD), MDS-G10 (AI/ML), MDS-G38
(pre-market cybersecurity) — is named in §R-2. **Noor holds no ML component**
(§15.3), so MDS-G10 is out of scope today and would become in scope the moment
that changes.

### 2.2 The device boundary is a code boundary

The workflow/data layer sits outside the device boundary; the decision/alert/rules
module sits inside it (§R-2). The two halves carry different validation and
change-control obligations, so the seam is enforced mechanically (§4.2), not
described in prose.

This is why §11 is a separate section rather than prose distributed through
§4–§10: clinical operations sit **outside** the boundary and carry a lighter
change-control obligation than the evaluator, and the document's structure must
make that split legible to an auditor.

### 2.3 Data residency and privacy

PDPL imposes no absolute localisation ban, but the simplest defensible default is
Saudi-resident production, Saudi-resident backups, and no overseas
production-support access (§R-2).

**Patient data is never sent to a general-purpose external AI service.** No
exception in the MVP. LLM use is deferred (§15.2).

Controller/processor roles, DPIA, DPO designation, and 72-hour breach
notification are provider-contract obligations recorded as release gates (§13.2),
not engine features. Two PDPL requirements are **not** in that set because they
shape the schema rather than the contract: how destruction rights reconcile with
the immutable record (§2.5), and the access control and audit trail that make a
breach scopeable within 72 hours at all (§2.6).

### 2.4 Clinical content copyright

ADA, AGS (Beers), and Dalhousie (Clinical Frailty Scale) all prohibit
reproduction of their protected expression; STOPP/START v3 is CC BY 4.0;
PHQ-2/PHQ-9 is freely reproducible with fidelity requirements — which §13.2 item
14 enumerates, because one of them is a suicidality escalation pathway rather
than a copyright condition (§R-1).

**Structural rule:** the catalogue stores *clinical propositions and pointers*,
never quoted guideline expression. No copied tables, decision trees, figures,
KDIGO G/A grid art, or CFS descriptors enter the repository or the product. This
is a property of the schema (§7.3), not a policy someone must remember.

The same rule extends to terminology. Valuesets reference `system` + `code` and
carry no reproduced display strings, so the catalogue stays distributable while
the SNOMED CT affiliate licence (§13.2 item 3) is outstanding.

### 2.5 Erasure and the immutable record

Observations are write-once (§5), evaluation records are immutable (§8.2), and
releases are immutable (§10.1). PDPL grants data-subject destruction rights.
These do not reconcile by policy, so they are reconciled by construction.

**Erasure is key destruction, not row deletion.** Each patient holds an
encryption key. Clinical content is encrypted under it; destroying the key
renders that content permanently unreadable while every row, timestamp, and
outcome remains structurally intact. This is a **day-one storage commitment**,
for the same reason §8.2 is: a plaintext table cannot be retrofitted into a
shreddable one without migrating every record ever written.

An account-deletion request is **not** equivalent to immediate destruction of
every clinical and legal record (§R-2). Erasure executes a retention schedule; it
does not bypass one.

#### What is encrypted

| Encrypted under the patient key | Left readable |
|---|---|
| `observation.as_reported`, `canonical`, `raw_payload` (§5) | `observable`, `source_system`, `effective_time`, `entry_mode`, `quality.state` |
| `observation.informant` (§5.4) | The evaluation record in full (§8.2) |
| `medicine_manager` identity and contact (§5.7) | Visit states and their timestamps (§11.2) |
| `obligation.subject` (§11.8) | `obligation.kind`, `state`, `opened_at`, `closed.at` |

The split is not arbitrary. §8.2's record already separates *outcome* from
*content* — it stores `rule_id`, `outcome`, `requirement_verdicts`, and `pins`,
never clinical values. A shredded patient's records still testify that a rule was
considered and returned `indeterminate`, which is exactly what zero-firing
surveillance (§11.9) reads. **The audit trail survives shredding for free**, and
metadata stays readable so that no shredded record can be mistaken for one that
never existed.

#### Consequences, stated rather than discovered

- **Replaying a real patient's evaluation after shredding is impossible, and that
  is intended.** §8.2's replay commitment binds the catalogue and the engine, not
  the patient's data lifetime. Golden cases and release comparison (§12.2) run on
  synthetic data (§12.4), so the validation suite is unaffected.
- **Key destruction is itself an audit record and is never shreddable** — who
  destroyed it, when, for which patient, under which retention rule. This is the
  obligation-closure pattern (§11.8): a named human with a reason.
- **Keys are held so that a copy of the clinical database alone is useless.**
  §2.3 fixes Saudi residency; naming a key-management service here would be the
  fabrication §3.5 refuses. **Key custody is a procurement gate (§13.2).**
- **The retention schedule is tenant profile data (§10.5), not code** — it is
  provider-specific and changes under governance, like thresholds and calendar
  dates. The data inventory it governs distinguishes clinical record, derived
  finding, audit log, and support record (§R-2).

### 2.6 Access control and the security audit log

**Three logs, not one.** §R-9 is explicit that no single log satisfies all three
purposes. Noor already builds two of them well; this section is the third.

| Log | Records | Where |
|---|---|---|
| **Security/access audit** | Authentication, authorisation result, patient-record access, export, device and session events, configuration change, and every *failed* attempt at each | `app/audit/` — this section |
| **Clinical provenance** | Which data, which rule and catalogue versions, what was concluded | The evaluation record (§8.2) |
| **Workflow/action** | What a human was shown, chose, deferred, or closed | Overrides (§9.2), planned actions (§11.6), obligations (§11.8) |

**One `correlation_id` joins all three.** It is minted when `evaluate()` is called
(§8.1), stored on the evaluation record (§8.2), and carried by every downstream
workflow event. Without it, "who saw this recommendation and what did they do
about it" is a manual reconstruction across three tables — which is the question
a PDPL access request and an SFDA investigation both open with.

#### Roles

Four operational roles, least privilege, and **no shared clinician logins**
(§R-2). These are distinct from the content-governance roles of §10.2.

| Role | May |
|---|---|
| `field_clinician` | Open encounters for rostered patients; capture through `canon`; view findings; record overrides and planned actions |
| `supervisor` | The above, plus review `submitted` visits and close obligations routed to them |
| `pharmacist_reviewer` | Read-only clinical view; close medication-review obligations; read the data-quality queue (§9.2) |
| `administrator` | User, device, and profile administration. **No clinical read.** |

**Access is scoped per patient, not globally.** A clinician's routine reach is the
roster they are assigned. Reaching a record outside it is **break-glass**:
permitted, never blocked, and recorded with the user, the patient, the timestamp,
and a reason that cannot be skipped. Break-glass records are reviewed as a census,
exactly as `stop_and_review` overrides are (§9.2). An administrator touching a
patient record is always break-glass, because their role carries no clinical read
to begin with.

#### Session and re-authentication

The deployment target is a shared field device (§R-11 §11.6), which makes session
policy a safety control rather than a convenience setting:

- **Idle timeout ≤ 15 minutes; absolute session ≤ 12 hours.** A profile may set
  either tighter. Neither may be raised.
- **Re-authentication is required before a `stop_and_review` override, a
  break-glass access, and any patient-contact disclosure** (§5.7).
- **Nothing gates the emergency hatch (§11.7) — including this.** A locked
  session opens the hatch first and authenticates after, with the gap recorded.

No source supplies a number; §R-11 says "short session expiry" without one. These
are **ceilings chosen as ceilings, not benchmarks**: twelve hours is one shift,
and fifteen minutes is the point past which a tablet left on a patient's table is
no longer in the clinician's possession. Stating them as bounds is honest;
presenting either as a standard would be the fabrication §13.3 exists to prevent.

#### Log integrity

Append-only, retained under the schedule of §2.5, and **never shreddable** — an
access log a subject-erasure request can delete cannot evidence who read the
record before the request arrived. Administrator actions are additionally written
to a separately monitored trail, since an administrator can otherwise curate
their own history.

**All timestamps are stored in UTC and displayed in the tenant's local timezone**
(§R-9). Saudi Arabia observes no daylight saving, which makes the `+03:00`
literals used illustratively throughout this document survivable but not correct.
The sweep-window boundary (§11.3), obligation ageing (§11.9), and escalation due
times (§11.2) are all comparisons between records that may outlive one deployment
region.

---

## 3. Technology stack

The stack precedes the architecture because it constrains it. Every module
boundary in §4 is drawable in these tools; nothing below assumes a dependency
this section does not name.

### 3.1 Decisions

| Layer | Choice | Reason |
|---|---|---|
| Language | **Python 3.12+** | §R-9 specifies a deterministic Python service. §R-5 established no maintained Python CQL engine exists — which is why we write the evaluator rather than adopt one. |
| Database | **PostgreSQL 16+** | Append-only event model, JSONB for verbatim source payload retention (§R-4), temporal constraints, and range types. The visit state machine (§11.2) and obligation ledger (§11.8) are ordinary tables with check constraints; no state-machine framework is warranted. |
| Schema and validation | **Pydantic v2** | Fact model, rule schema, data-requirement manifests, and API contracts are one problem. Exports JSON Schema, which is how the YAML catalogue is validated in CI. |
| HTTP API | **FastAPI** | This SSOT eventually governs the whole API; OpenAPI generation matters for a later SMART on FHIR or CDS Hooks facade. |
| DB access | **SQLAlchemy 2.0 + Alembic** | Typed; migrations are auditable artifacts. |
| Tests | **pytest** (`parametrize`) + **hypothesis** | `parametrize` is the table-driven-row mandate verbatim. Property tests target `canon`, where the invariant is that nothing crosses the boundary uncanonicalised. |
| Demo UI | **Jinja2 + HTMX** | No npm, no build step, no second language. No offline client is in scope, so no JS application is warranted. |
| Tooling | **uv**, **ruff**, **mypy --strict** on `canon`/`engine`/`catalogue` | One command each; matters when the project owner does not write code. |
| Scheduling | PostgreSQL table + one worker loop | The nightly sweep (§11.3), pending-result follow-up, and obligation ageing do not need a broker. |
| CI | GitHub Actions | Catalogue compile, schema validation, unit suite, golden cases, and release comparison as merge gates. |

### 3.2 Medication knowledge

**MVP:** a bounded curated set of **45 distinct ingredients** — the 11 diabetes
and 34 cardiovascular agents of the SEML 2023-derived catalogue (the roadmap's
49 entries collapse to 45 once four duplicate placements are removed). The set
is declared, not approximate: it is enumerated in
`docs/research/cds-content-roadmap.md` §9, its SEML listing and strengths are
verified against `docs/research/saudi-essential-medicines-list-2023.md` (the
converted primary source; the formulation ambiguities it carried were resolved
against the original PDF on 2026-08-17), and its per-ingredient labels are
tracked in `docs/research/label-pin-register.md`. Clinician-reviewed, with its
**scope and version displayed in the product**. This declaration replaces the
earlier estimate of roughly 60–80 ingredients: the SEML-derived set covers both
chronic-disease programmes in the product scope and keeps every catalogue
ingredient auditable — one pinned label and one verified strength set per
ingredient — instead of approximating coverage. Noor explicitly does not claim
broad interaction coverage; non-covered cases route to pharmacist or clinical
review (§R-3, §R-8).

This is not a compromise dressed as a decision — 79% of unique interaction pairs
appear in only one of three commercial products, and alert volumes vary from 25
to 145 per 1,000 prescriptions across vendors (§R-3). Breadth without disclosure
would be a false claim regardless of budget.

**Structural requirement:** the medication-knowledge interface is a
**vendor-shaped seam**. A licensed layer (FDB, Medi-Span/Lexidrug, Micromedex)
must be able to slot in behind it without rewriting rules. DrugBank's public
terms prohibit commercial exploitation and safety-critical use (§R-3) and it is
therefore not an option.

Allergy modelling is phenotype- and structure-aware: cephalosporin
cross-reactivity differs by R1 side-chain similarity, carbapenem cross-reactivity
is under 1%, and sulfonamide non-antibiotic cross-reactivity is not structurally
supported — flag, do not block (§R-3). The *patient-side* allergy record that
feeds this is §5.5.

#### Medication identity

A medication is not a string. §R-4 sets the required identity model, and the
observation model (§5) would be indefensible beside a drug layer that carried
less provenance than a potassium result.

```yaml
medication:
  ingredient_id: metformin              # Noor concept, the stable anchor
  salt: hydrochloride
  atc: [A10BA02]                        # class views only, never the rule anchor
  product:                              # null for an ingredient-level fact
    sfda_registration: "..."
    trade_name: "..."
    dose_form: tablet
    strength: {value: 500, unit: mg}
    route: oral
    modified_release: true
    spc_version: "..."                  # the label the renal rule was written against
  mapping:
    status: mapped | ambiguous | unmapped
    confidence: ...
    method: sfda_registration | pharmacist_reviewed
    terminology_version: ...
    source_display: "..."               # verbatim, always retained
```

**Never auto-map on name similarity alone** (§R-4). An ambiguous mapping is a
visible workflow state routed to a pharmacist, never a silent best guess — the
same principle as `canon`'s refusal to guess a unit (§6.3).

#### The source label, and what to pin when the local SPC is unretrievable

`spc_version` pins the label a dosing, monitoring, or contraindication statement
was written against. §5.2 requires the **local SFDA SPC first**. As of 2026-08-12
the Saudi Drug Information System (SDI) e-service that publishes per-product SPCs
is not reachable, so for most ingredients there is no local label to pin.

This does not license writing a plausible version string. It resolves the same way
a missing threshold source resolves — with §7.3's existing `fallback_from`
mechanism, applied to the label pin:

```yaml
source_label:
  pinned:
    authority: ema | national_agency | sfda
    document: "..."            # product name as the label titles it
    revision_date: "..."       # the label's own revision date, not a fetch date
    locator: "..."             # e.g. "SmPC 4.2"
  fallback_from:
    tried: [sfda.sdi]
    reason: "SDI e-service unreachable 2026-08-12"
  status: unretrieved | pinned | clinician_confirmed
```

The ladder, in order: **local SFDA SPC → the EMA centrally-authorised SmPC →
the SmPC of an EU national agency that authorised the product.** The third rung
exists because it is load-bearing, not for completeness: metformin, gliclazide,
furosemide, methyldopa, hydralazine and most of the older cardiovascular agents
have **no EMA SmPC at all** — they were never centrally authorised — so "fall back
to EMA" alone would leave the majority of the MVP catalogue unpinnable.

**`status: unretrieved` is a first-class, shippable state.** A rule whose
`source_label.status` is `unretrieved` does not merge — CI gate 2 already refuses a
threshold missing a document, version, or locator, and the label pin is checked by
the same gate. The consequence is intended: an unsourced rule is visibly blocked
rather than quietly approximate, which is the §11.7 principle applied to labels
instead of red flags.

The SFDA's harmonisation with EMA and ICH is what makes the fallback *clinically*
defensible, and it does not make it invisible. **Every fallback is recorded, and
a fallback is not a substitute** — when SDI becomes reachable, each
`fallback_from` entry is a work item, and a local SPC that contradicts the pinned
EU label is a content incident under §11.9, not a silent correction.

`sfda_registration` is a **product-level** field and is legitimately null for the
ingredient-level facts the MVP is built from (`drug_scope_level: ingredient`,
§7.1e). SDI being unreachable therefore blocks no ingredient-level rule. It blocks
product-level rules, and those are not in the first build target (§1.2).

#### Local formulary

`content/formulary/*.yaml`, per tenant: ingredient, formulation, strength, SFDA
registration and SPC version, provider availability, coverage constraint, prior
authorisation, substitution policy, stock date, and source (§R-2).

**A rule surfaces "clinically preferred but unavailable or unauthorised" rather
than silently proposing it** (§R-2). This is a correction to a real gap: the only
place availability previously appeared in this architecture was
`formulary_or_availability` as an *override reason* (§9.2) — that is, Noor
proposed an unobtainable agent and then recorded the clinician rejecting it.
Availability is an input, not an excuse.

The Saudi Essential Medicines List 2023 configures a baseline; it is **not** proof
of stock, coverage, or reimbursement at any given provider, and neither is SDI
registration (§R-2).

**A dose no available strength can produce is not a recommendation.** The SEML
lists strengths, and a label instruction is only actionable if some combination of
them yields it — amlodipine's 2.5 mg hepatic starting dose against an SEML that
lists only a 5 mg tablet, or a 50% reduction of spironolactone 25 mg against an
SEML with no 12.5 mg, are not dosing advice but tablet-splitting advice, and for a
modified-release form they are neither. This is the same class of failure as
proposing an unstocked agent (§R-2) and it resolves the same way: the rule
surfaces the constraint. A dose-adjustment rule therefore declares whether the
target dose is **strength-achievable, achievable-by-division, or unachievable**,
and an unachievable target routes to pharmacist review rather than rendering as an
instruction.

#### Pregnancy, breast-feeding, and fertility

The FDA letter categories are retired and are **not** used. A letter category is a
conclusion with its reasoning discarded, which is the one thing §7.2 forbids a
card to be. The label structure is narrative, and the catalogue stores it that
way: **a proposition and a pointer per subsection, never a grade** (§R-3).

**The operative subsection structure is the EU SmPC's**, because that is the
structure of the labels Noor's content is actually written against (§3.2 source
label, below). SmPC **§4.6 — Fertility, pregnancy and lactation** carries three
propositions:

| Catalogue proposition | SmPC §4.6 sub-topic | US PLLR analogue |
|---|---|---|
| `pregnancy` | Pregnancy | 8.1 |
| `breast_feeding` | Breast-feeding | 8.2 |
| `fertility` | Fertility | 8.3 (females and males of reproductive potential) |

All three are stored per drug, each with its own pointer to §4.6 of the named
label version. **An absent proposition is recorded as absent, never as
reassurance** — `fertility: {state: not_stated_in_label}` is a different fact from
`fertility: {state: no_effect_observed}`, and collapsing them would be the letter
category re-invented. Where a US PLLR label is the source instead, the right-hand
column maps it onto the same three propositions; the catalogue shape does not
change with the label's country.

#### Two knowledge-layer rules that outlive the vendor seam

- **Hepatic severity is a Child-Pugh phenotype, never transaminase values**
  (§R-3). Transaminases measure injury, not function; a rule that reads them as
  severity is the same class of error as reading a lab-corrected HbA1c (§5.3).
  **One carve-out, narrow and explicit:** where a label states a transaminase
  value as an *initiation criterion* — pioglitazone's ALT above 2.5× the upper
  limit of normal is the known case — a rule may read it, because it is the
  label's own gate on starting the drug and not a claim about hepatic function.
  Such a rule declares `hepatic_criterion: label_initiation_gate`, cites the
  label locator that states it, and **may not** be reused to stratify severity or
  to scale a dose. Absent that declaration the compiler refuses a rule that reads
  a transaminase.
- **A maximum dose is multidimensional** — indication, route, formulation, age,
  renal and hepatic function, and duration (§R-3). A single scalar ceiling per
  ingredient is not a simplification of this; it is a different and wrong model.

### 3.3 Terminology

Dual-layer: preserve the source verbatim, plus a versioned normalised concept.
LOINC + UCUM for observations; SNOMED CT for clinical meaning; ICD-10-AM at the
NPHIES billing boundary only; ATC at class level only; SFDA SDI for
product-to-ingredient mapping. RxNorm is US-centric and is **not** the Saudi
master (§R-4).

Arabic UI labels live in a separate field from LOINC display strings —
translations are derivative works requiring prior notification (§R-4). Arabic
patient-facing content — which the patient-contact obligation (§11.8) depends on
— is a release gate, not a translation task (§13.2 item 9).

#### The terminology charter

Picking the code systems is the easy half. §R-4 requires that someone own their
lifecycle, so `content/terminology/charter.yaml` names, per code system: the
licence and its current status, the edition and release in use, the effective
time, the module, a named owner, and the review cadence. The build manifest
(§12.2) carries the same values, which is what makes "this finding was produced
under SNOMED CT Saudi Edition 2026-04" answerable a year later.

**Terminology is a versioned boundary, not a lookup.** Mapping code lives behind
one interface, its version is pinned in every evaluation record (§8.2), and a
terminology release is a catalogue release — it re-evaluates affected patients
(§11.3) and runs release comparison (§12.2) like any other content change.

**The charter is where attribution obligations are recorded**, because a licence
condition nobody wrote down is a licence condition nobody meets. §10.4 gate 17
refuses a rule citing a code system the charter does not name, or a charter entry
with no licence status. Two conditions are already known and specific:

- **LOINC** grants perpetual no-fee commercial use *conditionally*: the
  prescribed notice must appear, and the identifier and official display name
  must be preserved alongside every mapping. **An Arabic UI label goes in a
  separate field** — LOINC treats a translation as a derivative work requiring
  prior notification, so an Arabic string must never overwrite a LOINC display
  (§R-4, §13.2 item 13).
- **SNOMED CT** requires a Saudi Affiliate licence via MLDS, which is outstanding
  (§13.2 item 3). §2.4's rule — valuesets carry `system` + `code` and no
  reproduced display strings — is what keeps the catalogue distributable
  meanwhile.

### 3.4 Not in the stack

Redis, Celery, a message bus, GraphQL, Kubernetes, OpenTelemetry, and
`fhir.resources`. The last is real and correct but is a Phase-2 adapter
dependency, and there is no EMR to adapt to.

**The migration trigger is stated so the decision expires on evidence rather than
on opinion.** Introduce a broker when a sweep run exceeds **four hours** or the
active-patient count exceeds **200**, whichever comes first. Both are measured
from the sweep run record (§11.3) and reported by §11.9, so the threshold is
observed rather than guessed at. Below it, the work is a single-threaded pass of
pure in-memory evaluation (§8.4 invariant 8) writing one batch of rows per
patient; a broker would add operational surface without removing any.

### 3.5 Hosting: deliberately undecided

§2.3 fixes the *requirement*. Naming a provider or asserting region availability
from memory in an SSOT would be a fabrication. **Hosting selection is a
procurement gate (§13.2).**

The stack is plain PostgreSQL plus containers with no proprietary managed
services precisely so that this decision stays cheap when a provider is named.

---

## 4. Module architecture

### 4.1 Layout

```
src/noor/
  canon/        data validity: unit resolution, plausibility, delta review,
                quality states. Produces canonical observations.
  engine/       the evaluator. Pure. No I/O, no DB, no clock, no network.
                (snapshot, catalogue) -> evaluation records
  catalogue/    loader, compiler, and validator for clinical content
  app/          FastAPI, PostgreSQL, UI, task loop      <-- OUTSIDE device boundary
    audit/        access control, session policy, the security log (§2.6)
    encounters/   visit state machine, transition gates, capture loop (§11.2, §11.5)
    obligations/  the ledger, closure invariant, ageing (§11.8)
    briefing/     pre-visit brief assembly (§11.4)
    sweep/        the scheduled and calendar triggers (§11.3)
    surveillance/ zero-firing detection, override analytics, data quality (§11.9)
    ui/           Jinja2 templates, card renderer (§7.2)

content/        the clinical content itself (§7.4)
tests/
```

`app/` carries substructure because §11 gives it real work. The subpackages are
named after clinical concepts, not layers: an `encounters` package that owns the
state machine is greppable from the state name in a bug report.

### 4.2 The enforced seam

`app` imports from `canon`, `engine`, and `catalogue`. **Never the reverse.**

A test scans the import graph and fails the suite if `engine` acquires a database
session, a wall clock, an HTTP client, or a filesystem read. This single test is
what keeps the device boundary real, and it is also what makes evaluation
deterministic and replayable.

Time enters the engine as an explicit `evaluated_at` value on the snapshot. The
engine never calls `now()`.

**The import test enforces direction, not content — so it is not sufficient
alone.** `app` builds the snapshot. Nothing about import direction stops `app`
from computing a derived clinical value, placing it in the snapshot, and having a
rule consume it. Clinical logic would then live outside the device boundary while
the import test stayed green. Direction is the cheaper half of the seam; content
is the half that actually leaks.

The seam therefore has a second half, at the data level:

1. **The snapshot is a closed Pydantic model** (`extra="forbid"`). A field that is
   not declared cannot enter, so `app` cannot smuggle a computed clinical value
   past the boundary by inventing a key.
2. **The compiler validates every rule field reference against the snapshot's
   exported JSON Schema** (§3.1). A rule may name only declared fields. This is
   what makes §10.4 gate 11 enforceable: encounter state is absent from the
   snapshot schema, so a rule referencing it fails to compile whatever it calls
   it. A name-matching check would be defeated by the first author who wrote
   `encounter.state` instead of `encounter_id`.
3. **Every snapshot field is either a `canon` output or declared derived, with
   provenance.** A derived field names the code that produced it, and that code
   lives inside the boundary (§5.2 is the existing example: Noor-derived eGFR is
   stored separately from the laboratory's, never silently substituted).

Together these make the boundary a property of the data contract rather than of
author discipline. §12.6 claim 20 tests both halves.

**The seam is what makes §11 safe to iterate.** Visit states, brief layout, and
obligation routing will change as a real provider uses them. None of that
touches the evaluator, so none of it re-opens the device-boundary validation
that §2.2 imposes.

### 4.3 Why an evaluator and not an inference engine

Rejected for the MVP runtime, each with a reason (§R-9, §R-5):

- **Drools/KIE, `durable_rules`** — Rete forward chaining introduces
  evaluation-order effects and rule interaction that defeat the determinism
  invariant (§8.4).
- **CQL as primary runtime** — no maintained Python CQL execution engine exists;
  the reference implementations are JavaScript and JVM/Kotlin (§R-5).
- **CQF Ruler / OpenCDS** — Java/HAPI operational weight, and OpenCDS's vMR/SOAP
  model is dated.
- **Medplum** — evaluate commercially; do not build a dependency on it.

The evaluator's vocabulary is intentionally small: comparisons, membership in
versioned value sets, date/window functions, and explicitly named aggregations.
If a clinical question cannot be expressed in that vocabulary, it is not yet a
rule — it is a design conversation.

**The vocabulary is a closed enum in the rule schema, not a stated intention.**
Pydantic rejects an unrecognised operator at load time and §10.4 gate 12 refuses
it at merge. This is what keeps the standing objection — that a hand-written
evaluator grows into a poor imitation of CQL — answerable by the build rather
than by assurance: growing the vocabulary requires editing the enum, which is a
reviewed change to the device, not a rule author's private decision.

---

## 5. The observation model

An observation is written once and never overwritten. Corrections arrive as new
observations carrying a higher `source_version`.

```yaml
observation:
  # identity & provenance
  observable: hba1c_ngsp        # NGSP % and IFCC mmol/mol are DISTINCT observables,
                                # not two units of one observable (§R-4)
  source_system: "riyadh-hh-lis"
  source_identifier: "OBS-88213"
  source_version: 2             # tracks amendment/correction of the source record
  source_code: {system: "http://loinc.org", code: "4548-4", display: "..."}
  source_status: final          # registered|preliminary|final|amended|corrected|
                                # cancelled|entered-in-error
  absent_reason: null           # set INSTEAD of a value when the source says why
                                # a result is missing. Never a value. (§5.5)
  effective_time: 2026-06-12T08:20:00+03:00   # specimen drawn / measurement taken
  issued_at:     2026-06-12T14:02:00+03:00    # source released it
  received_at:   2026-06-13T09:11:00+03:00    # Noor received it
  recorded_at:   2026-06-13T09:11:04+03:00    # Noor wrote the row (§R-9)
  entry_mode: interfaced        # interfaced | staff_transcribed | patient_reported
                                # | device_memory | noor_derived
  informant: null               # set when entry_mode is patient_reported (§5.4)
  encounter_id: null            # set when captured during a visit (§11.5)
  method:  {device_class: null, specimen: serum, assay: "HPLC"}
  setting: null                 # BP only: office | home | ambulatory. NEVER pooled.

  # terminology mapping — how the source code became a Noor observable (§R-4)
  mapping:
    status: mapped              # mapped | ambiguous | unmapped
    confidence: ...
    terminology_version: ...    # the release that performed THIS mapping
    source_display: "..."       # verbatim, retained even when mapping succeeds

  # value
  as_reported: {value: "7.4", unit: "%"}      # immutable
  canonical:   {value: 7.4, ucum: "%"}        # derived, shows its work
  raw_payload: {...}                          # verbatim source, JSONB (§R-4)

  # intrinsic quality verdict from canon (§6)
  quality:
    state: accepted
    unit_resolution: explicit
    delta: {compared_to: "OBS-71904", change: +0.6, comparable: true}
  context_flags: [a1c_interpretation_caution]
```

`encounter_id` is the only field §11 adds to the observation model. It is what
makes "which visit produced this reading" answerable, and it is what lets an
abandoned encounter's observations survive while remaining attributable (§11.2).
It never affects evaluation: a rule cannot ask which encounter a fact came from,
for the same reason it cannot ask which trigger invoked it (§8.1).

#### The Encounter Narrative and Structured Signals

The system supports a **hybrid approach** to the patient narrative. 
The encounter object itself holds the `encounter_narrative` containing three free-text fields (Chief Complaint, History of Present Illness, Physical Examination) for documentation and supervisor review. **Free text lives outside the device boundary and is never evaluated.**

Instead, the workflow allows clinicians to concurrently capture **structured clinical signals** (e.g., `symptom_hypoglycaemia`, `finding_pedal_oedema`) alongside the narrative. These are ordinary observations with `entry_mode: patient_reported` (for CC/HPI) or `staff_transcribed` (for PE). They cross the boundary through `canon`, enter the snapshot, and allow rules to reason about the clinical picture without parsing text.

`mapping` exists because a pinned `terminology_version` on the evaluation record
(§8.2) answers *which release evaluated this fact*, not *which release mapped
it*. When a mapping is corrected six months later, the second question is the one
that identifies which stored observations are affected. **A `mapping.status` of
`ambiguous` or `unmapped` is a visible workflow state routed to a human, never a
silent best guess** (§R-4) — it reaches `canon` as unusable, exactly as an
unresolvable unit does (§6.3).

`absent_reason` is FHIR `dataAbsentReason` (§R-9). When a source states *why* a
result is missing, that reason is recorded in its own field and never as a value.
Absence with a stated reason and absence with no explanation are different
clinical facts, and neither is zero.

### 5.1 Freshness is not a property of an observation

The prior design stamped `status: fresh | stale | ...` onto each fact. That is
unsafe: a result usable for stable long-term monitoring may be unsuitable before
a renal-dose decision, an acute-illness assessment, or a recent RAAS change
(§R-11 §11.2).

**Freshness is computed per rule, at evaluation time, against that rule's own
data-requirement manifest (§7.1), and recorded in the evaluation record (§8.2).**
The observation carries intrinsic quality only.

This eliminates the "latest value wins" anti-pattern by construction.

### 5.2 Derived values preserve provenance

eGFR is the governing example (§R-4). Noor stores the reporting laboratory's
`reported_egfr`, `reported_loinc`, `reported_equation`, and `reported_unit`
separately from any `noor_derived_egfr`. Historical values are never silently
recomputed under a different equation. The default for Noor-derived eGFR is the
2021 CKD-EPI creatinine equation without race (§R-1); no Saudi-specific
replacement equation with sufficient authority was identified.

**eGFR and creatinine clearance are distinct observables, and a rule uses the one
its product label specifies** (§R-3). Renal dose guidance comes from the local
SPC first, and a label written against Cockcroft-Gault CrCl may not be evaluated
against CKD-EPI eGFR. The two diverge most in exactly the patients home care
serves — elderly, low body weight, low muscle mass — so substituting one for the
other is not an approximation but a different question answered confidently.

A rule therefore names `renal_metric: egfr | crcl` in its requirement, and the
compiler refuses a renal-dosing rule that omits it (§10.4 gate 15). Where the
label specifies CrCl, the inputs it needs — weight, age, sex — are ordinary
requirements with ordinary `max_age_days` windows, and a missing weight makes the
rule `indeterminate` rather than silently falling back to eGFR.

### 5.3 Context flags

Flags such as `a1c_interpretation_caution` attach to observations whose
interpretation is conditioned by patient context — haemoglobin variants,
thalassaemia trait, haemolysis, anaemia, recent transfusion, advanced CKD,
pregnancy. This matters materially in Saudi Arabia, where premarital screening
found sickle-cell-positive status at 45.1/1,000 and beta-thalassaemia-positive at
18.5/1,000 (§R-1).

**Noor never algorithmically "corrects" HbA1c.** The flag prompts review of assay
method and alternative measures. It does not adjust a number.

### 5.4 Informant

When `entry_mode` is `patient_reported`, the `informant` field records **who**
provided the information — the patient themself or the named medicine-manager
(§5.7). This is not optional.

```yaml
informant: {role: patient | medicine_manager, person_id: "..."}
```

A medication list reported by the person who fills the pill box and one reported
by a patient with cognitive impairment are different grades of evidence. The
observation must say which, for the same reason evaluation is replayable (§8.2).

### 5.5 The allergy record

§9.1 reserves the only order-blocking severity in the architecture for, among
other things, a **verified severe allergy**. That phrase needs a record behind it.
§R-4 sets the required fields:

```yaml
allergy:
  culprit_substance: {ingredient_id: ..., atc: ..., source_display: "..."}
  reaction: [anaphylaxis]
  reaction_type: immediate_hypersensitivity | delayed | intolerance | unknown
  severity: severe | moderate | mild | unknown
  onset: {timing: "within 1h of first dose", date: 2019-03, precision: month}
  verification_status: confirmed | unconfirmed | refuted | entered_in_error
  evidence_source: clinical_record | patient_reported | family_reported
  recorder: {person_id: ..., role: ...}
  recorded_at: ...
```

Three rules follow, and each closes a way a blocking rule could fire or fail to
fire on nothing:

1. **Only `verification_status: confirmed` with `severity: severe` satisfies
   "verified severe allergy."** Anything else degrades under §8.3 — the finding
   still surfaces, at `interruptive_review`, never blocking an order on hearsay.
2. **"No known allergy" is a recorded state, never inferred from an empty list**
   (§R-5). `allergy_status: no_known_allergy | not_asked | recorded` is a patient
   attribute with its own recorder and timestamp. An unasked patient and a cleared
   patient are opposite facts; only one of them may satisfy a requirement.
3. **`intolerance` is not allergy.** A GI upset recorded as an allergy blocks a
   drug the patient can take. The field is separate so a rule can ask for the one
   it means.

`not_asked` is what a requirement sees when nobody has asked, and it produces
`indeterminate` (§8.3) — which opens an obligation (§11.8) rather than passing
silently. That is the whole point of the state existing.

### 5.6 Individualized Goals of Care

A clinician may formally override a guideline-based target (e.g., `<130/80` for BP) with an individualized goal for a specific patient. This explicitly permits normalizing a pathological state (e.g., `150/90`) when attempting to reach the guideline target would be harmful (e.g., due to frailty or orthostatic risk).

```yaml
goal_of_care:
  observable: systolic_bp                 # the physiological parameter
  target_threshold: {value: 150, op: lt}  # the new threshold (e.g., <150)
  reason: "High orthostatic fall risk"    # free-text or coded reason for override
  clinician_id: ...                       # named accountability
  effective_date: 2026-08-13
  expires_at: 2027-08-13                  # requires periodic re-validation
```

This is an explicit override mechanism, recorded with named accountability. The CDS engine **never** deduces or assumes a goal of care autonomously based on a patient's past stable but pathological readings.

### 5.7 The named medicine-manager

Every patient has exactly one **medicine-manager**: the named person who actually
handles the medications. This is the patient themself, a family member, or a hired
caregiver. It is recorded at registration (§11.1) and is not optional.

```yaml
medicine_manager:
  person_id: ...
  relationship: self | family_member | hired_caregiver
  name: "..."
  contact: {method: phone | whatsapp, value: "...", language: ar | en}
  consent_ref: ...           # required before any patient_contact obligation (§11.8)
  literacy_note: null        # free text; never a score (§9.4)
  effective_from: 2026-08-07
```

`consent_ref` points at the recorded consent permitting disclosure of clinical
information to **this named person by this channel**. Enrolment consent (§11.1)
does not cover it: PDPL consent is per purpose, and a hired caregiver receiving a
medication change is a third-party disclosure that patient enrolment never
contemplated. A `patient_contact` obligation cannot open without it (§12.6 claim
26).

The `whatsapp` channel is listed because providers use it, **not because it is
cleared**. It is Meta-operated and not Saudi-resident, which sits against §2.3's
default. It is unavailable until the DPIA (§13.2 item 2) either clears it or
replaces it.

The field is a first-class actor, not a demographic attribute, because two things
depend on it:

1. **Every patient-contact obligation (§11.8) is addressed to this person.** An
   obligation addressed to "the patient" is unactionable when a daughter or a
   hired caregiver fills the pill box.
2. **`entry_mode: patient_reported` is ambiguous without it.** A medication list
   reported by the person who administers the doses and one reported by a patient
   with cognitive impairment are different grades of evidence, and the observation
   record must say which (§5).

Changes are versioned, not overwritten — the manager on the day of an encounter is
reconstructable, for the same reason evaluation is replayable (§8.2).

**No adherence score is derived from this field, or from any other.** MMAS-8 is
aggressively licensed, ARMS-D is non-commercial, and Voils DOSE requires a
per-project licence (§R-7). Noor uses its own structured non-score interview and
stores the answers as observations.

---

## 6. `canon` — the data-validity layer

Built first. No threshold logic is written until this passes (§13.1, §R-11 gate 1).

Every observation captured during a visit passes through `canon` before it
becomes a fact (§11.5 step 2). There is no capture path that bypasses it.

### 6.1 Three layers

1. **Parse and unit checks** — invalid characters, impossible unit/value
   combinations, decimal and transposition patterns, unit changed from the
   patient's prior record.
2. **Plausibility checks** — a configurable per-observable physiologic envelope
   and a narrower operational "expected measurement" envelope. Neither produces
   a diagnosis.
3. **Delta review** — compares like with like only: same observable, unit,
   context, device class, and a reasonable time interval. A suspicious delta
   raises `needs_repeat_or_verification`, displays prior and current values with
   context, and requires confirmation. It never silently converts, replaces, or
   suppresses (§R-11).

Delta checks are a **review trigger, not an automatic correction**. Published
evidence supports them for specimen misidentification and pre-analytical error,
with low positive yield; there is no validated universal delta threshold for
home-entered BP, pulse, weight, or glucose (§R-11).

### 6.2 Quality states

```
accepted
needs_repeat_or_verification
rejected
clinically_exceptional_accepted
```

Four states, not three. A very abnormal *real* value and a mistyped value must
not collapse to the same system outcome (§R-11).
`clinically_exceptional_accepted` is what stops the plausibility gate from
suppressing a genuine emergency.

**`accepted` carries how it got there.** §R-11 separates a value that was never
questioned from one that was questioned and confirmed, and collapsing them loses
the repeat-confirmation rate §11.9 measures:

```
accepted_via: unremarkable | repeat_confirmed | clinician_verified
```

A `needs_repeat_or_verification` observation that a repeat resolves becomes
`accepted` with `accepted_via: repeat_confirmed` and a pointer to the confirming
observation. It never silently becomes indistinguishable from a value nobody
looked at.

An observation in `needs_repeat_or_verification` **never blocks visit
submission** (§11.2). It is recorded as such and travels with the encounter.
Blocking a clinician inside a home over a data-quality flag they cannot resolve
there is how the flag gets clicked away without being read.

### 6.3 Unit resolution is a hard safety control

```
unit_resolution: explicit | inferred_from_code | ambiguous
```

**`ambiguous` is a hard failure.** A value whose unit cannot be resolved never
receives a canonical value and never reaches the engine. Unit detection is a
first-class safety control, not an import convenience (§R-11, citing
Fahrenheit-for-Celsius errors in a production vital-signs corpus).

This is the one capture-time hard stop in §11.5. It is a hard stop precisely
because it is resolvable in the home: the clinician knows which unit the device
displays, and no other party can recover that fact later.

Specific consequences:

- Glucose: preserve the original unit; convert only with displayed conversion and
  provenance. Both mg/dL and mmol/L are accepted — no national default was found
  (§R-4).
- HbA1c: never infer percent versus mmol/mol from the value alone when the unit
  is absent. They are distinct observables (§5).

**Every conversion is round-trip tested and carries its own provenance** (§R-4).
The registry (§6.6) declares the conversion factor, its precision, and its
rounding rule; a property test asserts that converting a value out and back
returns it within the declared precision, in both directions. A conversion that
does not round-trip is a build failure, not a rounding curiosity — mg/dL to
mmol/L and back is the exact operation an off-by-a-factor error hides inside.

### 6.4 Three separate boundary types per observable

Stored and versioned independently. **A treatment threshold is never reused as a
data-entry validator** (§R-11).

| Boundary | Question it answers |
|---|---|
| Technical / physiologic plausibility | Could the instrument or person generate this? |
| Clinical urgency | Does this require a workflow response? |
| Target / pathological range | Does this indicate control or disease state? |

### 6.5 Repeat before action

Conditional, not universal. Prompt an immediate standardised repeat and record
both readings when a result is unexpectedly extreme, measurement quality is
uncertain, or a decision would change on a single non-emergent value.

**Never delay emergency escalation to satisfy a repeat protocol** (§R-11). A
repeat prompt is never permitted to stand between a clinician and the emergency
hatch (§11.7).

### 6.6 The observable registry

`content/observables/registry.yaml` declares, per observable: canonical UCUM
unit, accepted units and conversions with precision and rounding, physiologic
envelope, operational envelope, delta policy and comparability rules, required
method/context fields, and a named owner. Canonical units are **declared, not
assumed** — no Saudi national unit mandate exists (§R-4). Display defaults to the
as-reported unit.

**Blood pressure's required context fields are named here, not left to the
registry's general clause**, because BP is the observable the architecture leans
on hardest and the one whose value is meaningless without them (§R-1, §R-4):
posture, arm, cuff size, rest duration, reading ordinal within the sitting, and
whether the recorded value is an average. `setting` (§5) is additionally
mandatory and never pooled across office, home, and ambulatory.

**Orthostatic BP is a paired observation, never a code invented for it** — supine
and standing readings at one and three minutes, linked, each carrying its own
posture and timestamp (§R-4). Deriving "orthostatic drop" as a single number
discards the pairing that makes it interpretable.

#### The Curated Clinical Signal Set

The registry must be expanded beyond vitals and labs to include a **bounded, curated set of clinical signals**. These represent the symptoms, signs, and physical exam findings relevant to DM, HTN, and their pharmacotherapies (e.g., DKA prodrome, hypoglycaemia symptoms, pedal oedema, injection site lipohypertrophy).

This is a strict governance boundary. An unbounded symptom picker is unusable. The set of structured signals is governed and curated exactly like the medication catalogue. While the free-text narrative (§5) can capture "uncoded" or "other" findings to reflect real-world clinical complexity, the CDS engine can only ever evaluate signals that exist in this curated registry.

---

## 7. Rule schema and catalogue

### 7.1 The rule

```yaml
id: metformin-egfr-contraindicated
version: 1.0.0
release_status: approved      # draft | technical_validation | clinical_review |
                              # approved | scheduled | active | retired
category: drug_safety
severity: stop_and_review     # stop_and_review | interruptive_review | passive_task

scope:
  include: [{condition: type_2_diabetes}]
  exclude: [{age_lt: 18}, {on_dialysis: true}]

# What a drug reference in this rule matches against (§R-4, §3.2)
drug_scope_level: ingredient   # ingredient | ingredient_route | product |
                               # atc_class | curated_set

# Data-requirement manifest — each rule declares its own windows (§5.1)
requires:
  - observable: egfr
    accepted_status: [final, corrected]
    min_quality: accepted
    max_age_days: 90              # THIS rule's window. Not a global TTL.
    prefer_source: [interfaced, staff_transcribed]
    required_context: [ckd_chronicity_confirmed]
    on_unusable: indeterminate    # silent | indeterminate
  - observable: active_medications
    max_age_days: 1
    on_unusable: indeterminate

# When this rule's action lands, what falls due later (§R-11 §11.2)
monitors:
  - observable: egfr
    due_in_days: 90
    reason: "renal function after a metformin decision"

when:
  all:
    - {fact: egfr, op: lt, threshold_ref: metformin.egfr_absolute_contraindication}
    - {drug_active: metformin}

then:
  blocks: {order_of: metformin}   # a block must NAME the order action it blocks
  meaning: "Metformin is contraindicated below this eGFR."
  action: "Discontinue metformin and select an alternative agent."
  uncertainty: "Based on a single eGFR. Confirm CKD chronicity before acting."

governance:
  clinical_owner:    {name: ..., credential: ..., scfhs_id: ...}
  clinical_approver: {name: ..., credential: ..., approved_at: ...}
  role_doubling: false
  effective_from: 2026-09-01
  next_review: 2027-09-01
  change_rationale: "..."
```

Six departures from the prior design, each forced by research:

**(a) `requires_facts` became a manifest.** Per-rule code, unit, accepted status,
effective time, source preference, maximum age, required context, and
`indeterminate` behaviour (§R-9, §R-11).

**(b) `on_missing_facts: assume_unsafe` is deleted.** When input is stale,
contradictory, missing, or an unverified patient report, the correct outcome is
"cannot assess safely" plus interruptive review — not an absolute block (§R-11
§11.5). `assume_unsafe` is that anti-pattern with a friendly name. Its
replacement is the degradation invariant (§8.3), which an author cannot opt out
of.

**(c) A block must name its order action.** `blocks: {order_of: X}` rather than
`action: refuse_order`. A hard stop blocks the unsafe *order action* only — never
visit documentation, note submission, emergency activation, or the encounter
(§R-7, §R-11). The list it acts on is the planned-actions list (§11.6); without
that list a block has no surface and degenerates into a general interruption.

**(d) Governance is structural.** Owner, approver, role-doubling declaration,
effective date, next review date, and change rationale are schema fields checked
by CI (§10.4), not comments. `next_review` exists because a rule with no expiry
is a rule nobody re-reads: thresholds carry one (§7.3), and the rule that uses
them cannot be the only artefact that never comes up for air (§R-9).

**(e) `drug_scope_level` is declared, never inferred.** `{drug_active: metformin}`
is ambiguous about whether it means the ingredient, the oral form, one SFDA
product, or the ATC class — and the four match different patients. §R-4 requires
the level to be explicit and the **narrowest defensible scope** to be chosen. The
compiler refuses a drug reference whose level the rule does not declare (§10.4
gate 14).

**(f) `monitors` is separate from `max_age_days`, and this is not duplication.**
§R-11 §11.2 is explicit that the two answer different questions: `max_age_days`
asks *may this rule use the result I have*, and `monitors` asks *is the patient
due for another one*. A stale eGFR makes a rule `indeterminate`; a due eGFR opens
a `pending_result` obligation (§11.8) on the sweep (§11.3). Previously only
the first existed, so "recheck potassium four weeks after starting this ACE
inhibitor" — and finerenone's four-week and RAAS's two-to-four-week rechecks
(§R-1) — were inexpressible. A rule's own `monitors` entry pins the product label
version it was written against (§3.2), because a monitoring interval belongs to a
label, not to a molecule.

### 7.2 Authored prose is three fields; the card renders seven

The disclosure bundle is `why now / data status / rule status / scope / meaning /
action / uncertainty` (§R-7). Four derive automatically from the rule and the
evaluation record. Only `meaning`, `action`, and `uncertainty` are authored.

Render order is fixed: **evidence and data status before recommendation**. This
is the primary automation-bias mitigation (§R-7: incorrect advice raised
incorrect decisions by 26%; 6–11% of originally correct decisions flipped). It is
enforced by the renderer, not by author discipline.

Wording for uncertain applicability uses "review", "consider", "verify" — not
imperatives.

**Multiple findings on one subject are merged, not stacked.** Sixty-plus rules
across drug safety, renal dosing, and polypharmacy will fire together on a single
medication. Rendering four independent cards on metformin defeats the very
mitigation this section exists to impose: the fixed disclosure order works
because it is read, and a stack of cards on one subject is skimmed.

**Fixed now, and not a clinical judgement:** findings sharing a subject render as
one card; the card carries the highest effective severity among them; every
contributing rule is enumerated inside it; and each keeps its own evaluation
record (§8.2). Merging is a presentation behaviour and never collapses the audit
trail.

**Open, and needing the clinician reviewer (§16 item 9):** the order in which
contributing rules appear within the card, how much of each rule's `meaning` and
`action` survives the merge, and whether some subjects should never merge. That
is a clinical presentation judgement. The structure above is the safe default it
will refine — it is required before the card renderer (§14 step 9), not after it.

#### The card names its patient

Every card carries the patient identifier, name, and date of birth it was
computed for, plus the encounter timestamp and the provenance summary the seven
parts already supply (§R-7). This is a wrong-patient control, not a header
decoration: the deployment target is one device carrying several patients through
one day (§2.6), and a card whose only tie to a patient is the screen it happens
to be on is a card that survives a navigation the clinician did not notice.

**A `stop_and_review` override and any patient-contact action re-confirm name and
date of birth before proceeding** (§R-7). Re-authentication is already required
at both points (§2.6); identity confirmation rides the same gate, because the
moment worth interrupting is the moment before an irreversible act.

The renderer refuses to display a card whose patient identifier does not match
the encounter in context. §R-7 found no home-visit-specific effect estimate for
wrong-patient interventions, so this is usability-tested in the pilot (§12.5)
rather than assumed solved.

### 7.3 Thresholds

```yaml
- ref: metformin.egfr_absolute_contraindication
  value: 30
  unit: "mL/min/1.73m2"
  source_family: ada-kdigo
  citation:
    organisation: "ADA / KDIGO"
    document: "Consensus Report on Diabetes Management in CKD"
    version: "2022"
    locator: "Metformin recommendations"
    jurisdiction: international
    evidence_grade: consensus
    review_date: 2027-01-01
  fallback_from:
    tried: [moh.diabetes, sfda.label]
    reason: "no Saudi molecule-level floor located"
  status: clinician_approved      # unpopulated | populated | clinician_approved
  approved_by: ...
  approved_at: ...
```

**No rule loads referencing an `unpopulated` threshold.** No threshold is
`clinician_approved` without a named approver and date. Uncited thresholds are a
build failure.

**`source_family` is never blended.** A profile pins exactly one family per
domain; the compiler refuses a rule set whose thresholds resolve across two
(§R-1: "Do not blend target systems" — the ESC 2024 systolic 120–129 target and
the ACC/AHA <130/80 target are different systems, not interchangeable numbers).

**Evaluation Precedence.** When a rule evaluates a clinical target (e.g., hypertension control), it resolves the threshold in this strict order:
1. An active, unexpired `goal_of_care` for this specific patient (§5.6).
2. The profile's pinned `source_family` threshold.

This ensures the engine respects individualized physiological baselines and prevents autonomous rules from inappropriately pushing a frail patient toward a guideline target that a clinician has explicitly overridden.

Where sources conflict, the engine **shows the conflict** rather than silently
merging (§R-1).

### 7.4 Content layout

```
content/
  observables/registry.yaml      # §6.6
  thresholds/*.yaml
  valuesets/*.yaml               # versioned drug and condition sets
  rules/<id>.yaml
  rules/<id>.cases.yaml          # table-driven rows, as data
  golden/*.yaml                  # whole-snapshot patient cases
  profiles/*.yaml                # tenant profile: source_family pin, variations
  releases/*.yaml                # immutable release manifests
  calendar/*.yaml                # dated clinical events per tenant (§11.3)
```

**Adding a rule is two YAML files and zero Python.** A single `pytest`
parametrize discovers every `*.cases.yaml` in the tree.

`calendar/` holds the administratively-set dates the calendar trigger fires
against (§11.3). It is content, not configuration code, because the dates are
clinically meaningful and change under governance like anything else here.

### 7.5 Storage and approval: YAML in git

Rules are files in the repository. Git supplies immutable versioned releases,
reviewable diffs, tags, and rollback. **A pull request is the four-eyes approval**
that §R-11 §11.12 requires, with the approver recorded permanently.

Rejected: a database-backed authoring UI (months of CRUD and approval-workflow
work before rule one, reimplementing version control), and rules as Python
functions (breaks clinician review outright and dissolves the device boundary by
putting clinical logic and application code in one artifact under one release
process).

The clinician-facing plain-language rendering is **generated from the same rule
object that runs in production** (§R-11 §11.12). A separate Word or PDF
specification would drift from executable logic and is prohibited.

**The approver signs against the rendering, not the diff.** CI posts the
generated plain-language rendering — and its diff against the previous release —
into the pull request. Without that, "a pull request *is* the four-eyes approval"
would rest on a clinician reading YAML, and the control would be weaker than the
claim. The rendering is what makes the claim true mechanically.

**Content is loaded with a schema-only YAML loader** (`yaml.safe_load` or a
`SafeLoader` subclass). A tag such as `!!python/name:` or
`!!python/object/apply:` in a rule file would otherwise execute arbitrary code
*inside the device boundary* at catalogue load. That is both a boundary breach
and remote code execution, and it is defeated by choosing the right loader once
(§10.4 gate 13, §12.6 claim 21).

---

## 8. Evaluation

### 8.1 The call

One internal entry point backs the UI, scheduled review, the REST API, and any
later CDS Hooks or SMART facade (§R-5):

```python
evaluate(context, snapshot, requested_actions) -> EvaluationRun
```

**Three triggers, one engine.** The trigger differs; the evaluator does not.

| Trigger | Fires when |
|---|---|
| `visit` | A clinician opens an encounter, and on each capture within it (§11.5) |
| `data` | A scheduled sweep finds new data landed, or data aged out of some rule's `max_age_days` window (§7.1) |
| `calendar` | A dated clinical event is approaching, independent of any new data |

`calendar` exists because the Ramadan pre-fasting assessment is time-driven, not
data-driven: IDF-DAR 2021 places risk stratification 6–8 weeks *before* Ramadan
(§R-1 §1.6), and a patient whose data has not changed still needs that
assessment. Without this trigger the sweep is silent precisely when the
assessment is due.

The trigger is recorded on the `EvaluationRun`. It never changes rule outcomes —
a rule cannot ask which trigger invoked it, or invariant 5 (§8.4) would not hold.

The operational behaviour of each trigger — how the sweep is scheduled, how
calendar dates are administered, what happens to the output — is §11.3. This
section owns only the call and its purity.

### 8.2 Every rule considered writes a record

Not just the ones that fired.

```yaml
evaluation_record:
  correlation_id: 01J8...        # the run's id — joins all three logs (§2.6)
  rule_id: metformin-egfr-contraindicated
  rule_version: 1.0.0
  outcome: indeterminate    # triggered | not_triggered | indeterminate
                            # | out_of_scope | suppressed_by_governed_policy
  authored_severity:  stop_and_review     # what the rule declares
  effective_severity: interruptive_review # what was presented, after §8.3
  degraded_because: requirements_unmet
  requirement_verdicts:
    - observable: egfr
      verdict: unusable
      reason: no_result_within_90d
      latest_age_days: 214
  latency_ms: 41                 # wall time inside evaluate(), per run (§R-9)
  pins:
    catalogue_release: 2026.09.1
    profile: riyadh-hh@3
    source_family: nhc-sha-2023
    snapshot_id: ...
    engine_version: ...
    terminology_version: ...
```

**`correlation_id` and `latency_ms`.** §R-9 asks a CDS log to answer two
operational questions the clinical fields cannot: *what else happened around this
decision*, and *was the engine fast enough to be used*. `correlation_id` is minted
once at `evaluate()` (§2.6) and stamped on every record the run produces, so a
single value joins the security log, this record, and the workflow log. `latency_ms`
is measured per run against §14's ≤ 500 ms p95 target — a number nobody records
is a target nobody can miss.

**What is deliberately *not* here: `displayed` and `opened`.** §R-9 wants to know
whether an alert was seen, not merely computed. Noor records that — in the
workflow log (§2.6, log 3), not here. Display happens in `app/`, outside the
device boundary (§4.2), and §8.4 invariant 8 requires evaluation to be pure and
in-memory. An engine record that grew a field only the UI could fill would make
the engine wait on its own presentation layer. The `correlation_id` closes the gap
without crossing the boundary: *was this card seen* is a join, not a column.

**Outcomes.** Three come from the evaluator (§R-9); `out_of_scope` and
`suppressed_by_governed_policy` are Noor's, both forced by §R-11 §11.9.

| Outcome | Meaning |
|---|---|
| `triggered` | In scope, requirements met, conditions matched |
| `not_triggered` | In scope, evaluated with usable data; conditions did not match |
| `indeterminate` | In scope, but one or more requirements were unusable. **Never conflated with `not_triggered`.** |
| `out_of_scope` | The rule's `scope` excluded this patient. Requirements were never checked. **Never conflated with `not_triggered`.** |
| `suppressed_by_governed_policy` | A governance-approved disablement applied (§10.5) |

**Scope is resolved before requirements, and the order is load-bearing.** A rule
that excludes a patient records `out_of_scope` and stops. It does not read its
`requires` manifest, so it cannot produce `indeterminate` merely because a
patient outside its scope lacks data the rule never needed.

Were `out_of_scope` folded into `indeterminate`, §8.3 would degrade it and §11.8
would open a `carried_forward` obligation for every non-applicable rule on every
patient — the ledger would fill with work nobody owes. Were it folded into
`not_triggered`, zero-firing surveillance could not distinguish "sixty in-scope
patients, none matched" from "a profile edit narrowed scope to nobody", which is
the exact discrimination §8.2 exists to make.

**Rationale.** The dominant CDS failure mode is the alert that silently stops
firing: users reliably notice a spurious alert and reliably fail to notice an
expected one that never appears; 93% of surveyed CMIOs had experienced at least
one malfunction (§R-7). Silent non-firing cannot be detected from a log of things
that fired.

With this record the question becomes answerable: *rule X fired zero times in 30
days — was it considered 400 times with 380 unusable eGFR requirements?* That is
a broken lab feed, not a quiet month.

A governance-disabled rule evaluates to `suppressed_by_governed_policy` and never
silently disappears (§R-11 §11.9).

Volume is not a concern: 60 rules × 100 patients × monthly ≈ 72k rows/year. That
figure already assumed every rule writes for every patient, which is what
`out_of_scope` makes true.

**This is not retrofittable.** It is a day-one storage commitment.

**The evaluation record is the unit the rest of the system builds on.** The
pinned record is what a reviewer sees (§11.2), what the pre-visit brief reads
(§11.4), what opens and closes obligations (§11.8), and what zero-firing
surveillance counts (§11.9). Everything durable in §11 is anchored to a record
written here.

### 8.3 The degradation invariant

> A rule whose severity is `stop_and_review` and whose data requirements are not
> met degrades to `interruptive_review`, carries "cannot assess safely", and
> names the specific unmet requirement. It never blocks.

Authors cannot opt out. Blocking on data you do not have is how clinicians are
trained to route around blocks (§R-11 §11.5).

**Interaction with `on_unusable`.** `on_unusable: silent` is refused for
`stop_and_review` rules (§10.4 gate 10). A rule severe enough to block an order is
never allowed to fail silently when its inputs are unusable — silence there is
indistinguishable from a broken data feed, which is the failure mode §8.2 exists
to catch. `silent` remains available to `interruptive_review` and `passive_task`.

**Degradation is not resolution.** A rule that degrades has not been answered; it
has been deferred. The operational consequence is §11.8: an `indeterminate`
outcome opens a `carried_forward` obligation, so the unanswered question leaves
the encounter with an owner instead of evaporating at visit close.

### 8.4 Engine invariants

Each is a test.

1. Only `stop_and_review` may block, and only the named order action.
2. No rule loads with an incomplete citation.
3. No rule loads referencing an `unpopulated` threshold.
4. `stop_and_review` rules cannot be tenant-disabled.
5. Evaluation order never affects output.
6. Identical snapshot + identical catalogue release ⇒ byte-identical records.
7. No rule reads another rule's output.
8. The engine performs no I/O and reads no clock (§4.2).
9. A rule is a pure function of the snapshot and the catalogue — preserving
   portability for a future on-device evaluator (§15.1).
10. No rule reads encounter state or free-text narrative. A rule cannot ask which visit state, trigger,
    or workflow step invoked it, and it cannot see the patient's textual complaint. §11 is a consumer of evaluation, never an input
    to it.

Invariant 10 is what keeps §11 outside the device boundary. The moment a rule
branches on visit state, the workflow becomes part of the regulated device and
every UI change re-opens clinical validation.

---

## 9. Findings, alerts, overrides

### 9.1 Three severities

| Severity | Behaviour | Reserved for |
|---|---|---|
| `stop_and_review` | Blocks the named order action. Requires a governed override route. | Verified severe allergy (§5.5), absolute contraindication with reliable data, gross dose-ceiling breach (§3.2) |
| `interruptive_review` | Must be acknowledged before signing; proceed with an explicit reason | Potentially serious medication, lab, or plan concern with adequate data |
| `passive_task` | Queue or task; no interruption | Missing monitoring, reconciliation discrepancy, lower-certainty advisory |

The prior four-level ladder (`hard_stop | warning | advisory | info`) collapses to
three; `info` was cosmetic.

**Two of the three reserved uses are narrower than they read.** "Verified severe
allergy" means a §5.5 record whose `verification_status` is `confirmed` and whose
`severity` is `severe` — an unverified or unknown-severity allergy degrades under
§8.3 rather than blocking. "Gross dose-ceiling breach" means a breach of the
ceiling that applies to *this* patient on *this* indication, route, and renal
band, resolved as §3.2 describes — not a breach of a single headline number.
A rule that blocks on the wrong ceiling is a hard stop the clinician was right to
route around, which is the failure §R-11 §11.5 documents.

Hard stops must be **rare and action-scoped**. In a systematic review, 11 of 32
studies reported unintended consequences including workarounds and delayed care
(§R-11 §11.5). Role-tailoring is the only alternative with a demonstrated
acceptance advantage — 61.57% versus 38.67% (§R-7).

**What each severity does at the visit-submission gate** is §11.2: an
unacknowledged `interruptive_review` holds submission; a `stop_and_review`
prevents its named planned action from being marked `final`; a `passive_task`
never holds anything. The ladder is defined here; the gate that applies it is
there.

### 9.2 Overrides

Structured taxonomy **and** free text, both. A Saudi study of 1,087 evaluated
medication-alert overrides judged 67.89% inappropriate and specifically
recommended both structured options and free-text capacity (§R-11 §11.5).

Captured: rule id and version; the data status at the time; selected reason;
free text; action taken or deferred; responsible user; co-sign requirement;
planned follow-up.

Initial taxonomy — a **Noor-owned** local taxonomy, since the CDS Hooks feedback
mechanism sends an empty notification body and is a suggestion-selection
telemetry channel, not an override-reason standard (§R-5):

```
patient_specific_benefit | alternative_monitoring_in_place | incorrect_or_incomplete_data
| already_addressed | guideline_exception | formulary_or_availability
| duplicate_or_irrelevant_alert | technical_issue | defer_or_escalate | other
```

`incorrect_or_incomplete_data` routes to the **data-quality queue**, not the
clinical queue. `defer_or_escalate` opens a `carried_forward` obligation (§11.8)
— deferring is a decision with an owner, not a dismissal. New categories require
clinical governance approval.

**Override rate is a stratified signal by rule, severity, role, and reason. It is
never a performance target.** The frequently quoted >60% acceptance figure is
arbitrary by its own authors' admission (§R-7).

Every `stop_and_review` override is reviewed initially; sampling may replace
census only after demonstrated rule performance.

### 9.3 Safety surveillance

Two channels, both first-class:

- **Zero-firing anomaly detection**, computed from §8.2 records.
- **"Expected alert absent" reports** — any clinician can file one in a single
  action, and it enters the same queue as a spurious-alert report.

Their operational loop — who reads the output, and how a finding becomes a rule
change — is §11.9.

---

## 10. Clinical content governance

### 10.1 Release lifecycle

```
draft → technical_validation → clinical_review → approved → scheduled → active → retired
```

Releases are immutable. Each emitted recommendation pins clinical source and
version, local profile, terminology and product mapping, executable rule version,
input snapshot, and runtime configuration (§8.2). This is a safety requirement,
not a software-engineering preference (§R-11 §11.9).

**`retired` carries a work list.** Retiring a rule enumerates the obligations it
opened that are still open and routes each for named human closure (§11.8). A
retired rule never evaluates again, so nothing else can ever close them.
Retirement does not affect replay: records pin `catalogue_release` (§8.2), and
that release still contains the rule.

**Activating a release makes affected patients due for re-evaluation** on the
next sweep (§11.3). A release that changes a threshold or a valueset changes live
findings, and §12.2 only compares the golden set.

#### The release note is classified, not narrated

Every release ships a changelog in which **each entry carries a clinical-impact
class**, assigned by the clinical content owner (§10.2), not by the person who
wrote the diff:

| Class | Meaning | Consequence |
|---|---|---|
| `safety_critical` | Changes when a patient is warned, blocked, or not | Named clinician sign-off; deploy announced, never silent; §12.2 diff attached |
| `clinical_substantive` | Changes wording, evidence, or a monitoring interval without changing who fires | Clinical review; summarised to users at next login |
| `editorial` | Typo, formatting, comment, non-clinical refactor | No clinical review beyond the standard PR |

The classification is the point. §R-8 finds that reference content updates are
consumed as undifferentiated bulk — a reader facing 200 changes with no severity
signal reads none of them, and a threshold change hides among the typos. A
changelog that does not rank its own entries is a changelog nobody reads.

An entry classified `editorial` that §12.2 release comparison shows changing a
finding is a **build failure**, not a reclassification request: the class was
wrong, and the gate that catches it is gate 9 (§10.4).

### 10.2 Roles

- **Clinical content owner** — named, credentialed, owns clinical meaning.
- **Technical custodian** — cannot silently alter clinical meaning; changes to
  `when`, `then`, thresholds, or severity require clinical re-approval.
- **Second clinical approver** — required for high-severity changes.

These are content-governance roles. They are distinct from the *operational*
roles in §11 (field clinician, supervisor, obligation owner), which govern
patient care rather than catalogue change. One person may hold both; the records
are separate.

### 10.3 Role doubling is recorded, not hidden

The project's content-governance roles were appointed on 2026-08-17: clinical
content owner, technical custodian, terminology owner, provider medical
director (interim), and privacy/security owner are the project owner; the
second clinical approver is Dr. Ahmed Sabry, a separate person. SCFHS licence
numbers were supplied 2026-08-17 for both clinicians. Governance decisions
recorded 2026-08-17: expired or changed credentials invalidate future
approvals only (historical approvals and releases stand), and active clinical
content is re-reviewed annually and immediately on pinned-source updates. A
governance model that pretends otherwise is theatre that fails its first
audit.

`governance.role_doubling: true` is **permitted and recorded** for
`passive_task` and `interruptive_review` rules. It is **refused** for
`stop_and_review`.

**Business consequence, stated plainly: Noor cannot ship a single hard stop until
a second credentialed clinician formally signs.** The architecture surfaces this
constraint rather than hiding it.

### 10.4 CI gates on content

A merge is refused if any of these hold:

1. A rule cites a threshold whose `status` is `unpopulated`.
2. A threshold lacks organisation, document, version, or locator.
3. A rule has `severity: stop_and_review` and `role_doubling: true`.
4. A rule has `severity: stop_and_review` and no `clinical_approver`.
5. A rule's `then` omits `meaning`, `action`, or `uncertainty`.
6. A `blocks` clause does not name an order action.
7. A profile resolves thresholds across two `source_family` values.
8. A rule has no `*.cases.yaml`, or its cases do not include at, just-below, and
   just-above rows for every threshold it references.
9. Release comparison (§12.2) shows a changed or disappeared finding that the
   release manifest does not explain.
10. A rule has `severity: stop_and_review` and any requirement with
    `on_unusable: silent` (§8.3).
11. A rule references encounter state, visit state, or trigger identity in its
    `scope` or `when` (§8.4 invariant 10).
12. A rule references a field absent from the snapshot schema, or uses an
    operator outside the evaluator's declared vocabulary (§4.2, §4.3).
13. A content file fails to parse under a schema-only YAML loader — any tag
    that would construct a Python object is a build failure, not a warning
    (§7.5).
14. A rule references a drug without declaring `drug_scope_level` — ingredient,
    ingredient+route, product, ATC class, or curated set (§3.2, §R-4).
15. A renal-dosing rule omits `renal_metric`, or names an eGFR observable in a
    rule whose source label specifies creatinine clearance (§5.2, §R-4).
16. A rule whose `severity` is `stop_and_review` matches on an allergy without
    requiring `verification_status: confirmed` and `severity: severe` (§5.5,
    §9.1).
17. A rule cites a code system absent from the terminology charter, or one whose
    charter entry has no licence status (§3.3, §R-4).

### 10.5 Tenant profiles

A profile inherits the vendor clinical baseline and declares each permitted
variation with rationale, source, approver, and effective date. It pins one
`source_family` per clinical domain. It runs the full affected golden-case set
before activation. Its version is emitted in every recommendation.

A tenant cannot edit a threshold in a live rule. A tenant cannot invisibly
disable an advisory — disablement produces `suppressed_by_governed_policy` with
named requester, reason, clinical-owner approval, dates, affected population,
replacement pathway, and test evidence (§R-11 §11.9).

A profile also carries the tenant's **operational policy**: the role-routing
table (§11.8), the calendar dates the calendar trigger fires against (§11.3),
the emergency pathway content (§13.2 item 7), the escalation policy — on-call
person by hour and the due-time bound (§11.2) — the obligation ageing thresholds
(§11.9), and the per-action-kind obligation defaults (§11.6). These are profile
data, not code, for the same reason thresholds are — they differ per provider and
change under governance.

**A profile that omits an operational policy does not get a silent default.** The
system falls back to an explicit human decision, recorded with the name of the
person who made it (§11.1, §11.2). Absent policy is thereby visible in the record
rather than resolved by whatever a constant happened to say.

Cross-tenant learning is human-approved only. HIPAA Safe Harbor is **not**
assumed to be a PDPL de-identification standard (§R-11).

---

## 11. Clinical operations

Everything in this section sits **outside** the device boundary (§2.2) and lives
in `app/` (§4.1). It consumes evaluation; it never influences it (§8.4 invariant
10).

This section is the sole architectural authority for the clinical workflow.

**The thesis.** Noor is a stateful safety workflow, not a form filler and not an
alert layer. Every rule considered writes a record (§8.2). Every unresolved
finding survives visit close as a durable obligation (§11.8). An obligation never
closes because data became unavailable — only when the condition resolves with
usable data, or a named human closes it with a reason.

### 11.1 Registration and baseline

Noor begins after the provider has enrolled the patient — eligibility, consent,
and contract sit outside the product (§1.1). Noor starts when a patient record
exists.

**Registration** records identifiers, conditions, and the named medicine-manager
(§5.7). The patient enters state `establishing_baseline`.

**Patient states** are deliberately few:

| State | Meaning |
|---|---|
| `establishing_baseline` | Registered. Only baseline data-capture encounters permitted; no routine visits. |
| `active` | Baseline bar met. Routine visits and the nightly sweep (§11.3) apply. |
| `inactive` | Discharged, transferred, or deceased. Sweep stops; open obligations are closed by a named human with a reason, never automatically (§11.8). |

**The baseline visit is its own workflow**, not a routine visit with extra
fields:

1. Identity confirmation
2. Medication reconciliation and brown-bag — **discrepancies are kept as
   discrepancies**. Noor does not force one authoritative list (§R-11 §11.8).
   Each reported list is an observation with an `informant` (§5.4).
3. **Comprehensive baseline patient narrative/history** — since Noor is not an EMR, it acts as a "quality control" check. If the EMR lacks a complete history of present illness or up-to-date physical exam, it is requested here.
4. Baseline vitals through `canon` (§6)
5. Home environment and caregiver capability as **non-score structured
   observations** (§5.7 — no licensed instrument, no derived score)
6. **Goals of care and individualized targets** — the clinician explicitly records individualized targets (e.g., `<150/90` BP) if the patient's baseline makes the profile's default guideline threshold unsafe to pursue. This creates the `goal_of_care` records (§5.6) that rules evaluate against.

**Clinical rules run during a baseline visit and return `indeterminate` by
design.** The output of a baseline visit is a set of data-acquisition
obligations, not recommendations. The UI states "not yet assessable — needs
HbA1c, eGFR" and never renders a blank card. This is §8.3 doing exactly what it
was built for, at the one moment when nearly every rule lacks data.

**Exit gate.** The patient moves to `active` when the baseline completeness bar
is met. **The bar is not yet defined** and needs the clinician reviewer (§16
item 7). Until it is, the transition is manual and recorded with the name of the
clinician who made it — an explicit human decision is an acceptable stand-in for
a rule; a silently-assumed default is not.

### 11.2 The visit state machine

A visit is the unit of clinical work. Its state governs one thing above all:
**whether observations may be written.**

#### States

| State | Description | Terminal | Observations writable |
|---|---|---|---|
| `scheduled` | Visit exists; pre-visit brief assembled (§11.4). No encounter data yet. | No | No |
| `in_progress` | Clinician capturing through `canon`, live `evaluate()` running, cards displayed, planned actions recorded. **The only state that creates clinical facts.** | No | **Yes** |
| `submitted` | Clinician finished; awaiting supervisor review. Evaluation is **pinned** — the reviewer sees exactly what the clinician saw (§8.2). Mandatory for every visit. | No | No |
| `escalated` | Red-flag path requiring immediate intervention. Names a responsible person and a due time on entry (§11.2). An alternate reality of `submitted`, not a detour around it. | No | No |
| `completed` | Terminal. Immutable. Visit note generated. Corrections arrive as a new addendum encounter, never an edit (§5). | Yes | No |
| `cancelled` | Terminal. Never started — patient not home, refused, rescheduled. No observations exist. | Yes | No |
| `abandoned` | Terminal. Started but not finished. **Partial observations survive** (§5). No visit note. Unresolved severe values open obligations automatically. | Yes | No |
| `interrupted_for_emergency` | The escape hatch (§11.7). Entered in one tap from `scheduled` or `in_progress`, with no gate of any kind. | No | No |

#### Transitions

```
scheduled ──────► in_progress ──────► submitted ──────► completed
    │                  │                   ▲   │
    │                  │                   │   └──► escalated ──┐
    │                  │                   │                    │
    │                  │                   └────────────────────┘
    │                  ├──────► escalated ─────────────────────►┘
    │                  ├──────► abandoned  (terminal)
    │                  └──────► interrupted_for_emergency ──► submitted
    ├──────► cancelled (terminal)
    └──────► interrupted_for_emergency ──► submitted
```

**Every visit passes through `submitted`.** Supervisor review is mandatory. No
Saudi regulation requires this (§13.2 item 6, §R-2); it is the provider's
operating model, and Noor encodes it as a profile-level policy rather than a
job-title rule.

**`escalated` exits only to `submitted`.** Three parties may enter it: the field
clinician mid-visit, the clinician acting on a CDS finding presented
pre-submission, and the supervisor during review. There is exactly one path into
`completed`, so the completion gate is enforced in exactly one place.

**Escalation ends capture.** A clinician who escalates from `in_progress` cannot
resume writing observations in that encounter. If care must continue after the
escalation resolves, the supervisor returns it as a **new visit**. This costs an
extra encounter record in an uncommon case and buys the no-rewind rule
everywhere else.

#### An escalation names a person

§11.8 requires every obligation to name an owner — "a named person, never a queue
alone." Escalation is the most urgent durable work the system holds, and it was
the one piece of it addressed to nobody.

**Entering `escalated` names a responsible person and stamps a due time.** Both
come from the tenant profile's escalation policy (§10.5): who is on call for this
tenant at this hour, and how long they have. An escalation that names a role but
no person has not escalated — it has queued, which §16 item 6 identifies as the
failure mode.

The *bound* is provider data because no Saudi benchmark exists (§13.3). The
*requirement* that one exists, and that a human name attaches, is architectural
and does not wait for a provider. Where a tenant has supplied no policy, the
escalating clinician names the recipient by hand and the system records that they
had to — an explicit human decision is an acceptable stand-in for a rule, exactly
as with the baseline bar (§11.1); a silent default recipient is not.

**A due time that passes is a surveillance event, never an auto-close** (§11.9).
Nothing about escalation expires on a timer: that is the failure §15.3 rejects
for obligations, and it is worse here.

#### The submission gate: `in_progress → submitted`

**Holds submission:**

- An `interruptive_review` finding not yet acknowledged; acknowledging requires a
  structured reason plus free text (§9.2)
- A planned action still marked `final` while blocked by a `stop_and_review` rule
  (§11.6)
- Identity not confirmed for this encounter

**Never holds submission:**

- An `indeterminate` outcome (§8.3) — it opens an obligation instead (§11.8)
- A missing optional field
- An open obligation — obligations are durable, not visit-scoped
- A `needs_repeat_or_verification` flag already recorded as such (§6.2)

> Blocking on data you do not have is how clinicians learn to route around Noor.

#### What the reviewer sees

The reviewer sees the **free-text patient narrative** (CC, HPI, PE) providing the full human story, alongside the **pinned evaluation record** — `snapshot_id`,
`catalogue_release`, `profile`, `engine_version` (§8.2) — plus a **separate "new
since submission" panel** if data landed in between.

**Never a silent re-evaluation.** The reviewer is judging a decision made with
specific information at a specific time. §8.2's replay commitment exists so that
record is reconstructable; re-running the catalogue underneath a reviewer would
destroy the thing being reviewed.

#### The review queue is ranked, and the ranking is inspectable

Review is mandatory, so the queue is where mandatory review either works or
quietly stops working. §R-11 §11.3 is directive on two points, and Noor follows
both.

**Three lanes, provider-defined at the boundaries:**

| Lane | Contents | Delay |
|---|---|---|
| `immediate_escalation` | Provider-defined emergency and high-harm conditions (§11.7) | None. Never queued |
| `same_day` | Potentially serious medication, lab, or plan-change concern with adequate data | Same day |
| `routine` | Missing monitoring, reconciliation discrepancy, lower-certainty advisory | Ordinary backlog |

The lanes are the §9.1 severity ladder expressed as time rather than as
interruption, and the mapping is deliberate: `stop_and_review` and any red flag
enter `immediate_escalation`, `interruptive_review` enters `same_day`,
`passive_task` enters `routine`. Which conditions count as emergency is profile
content, not Noor's judgement (§13.2 item 7).

**No machine-learning risk score orders this queue.** §R-11 §11.3 refuses it
explicitly and §15.3 rejects it outright. Ranking is a declared, inspectable
combination of named components — severity and urgency, time sensitivity, action
kind, data quality, patient vulnerability, an unresolved prior obligation on the
same subject, elapsed time, and whether patient contact is required. A reviewer
may ask why an item is at the top and receive the components, not a number. **A
high-risk but data-ambiguous item ranks for verification; it never presents as a
certain finding** — which is §8.3's degradation invariant applied to ordering
rather than to display.

The component weights are profile data (§10.5). An unranked queue would be
first-in-first-out, which is the same failure as a rubber stamp arriving in a
different order.

#### The review clock starts at evaluation, and a stalled review names a backup

**The SLA is measured from rule evaluation time to the responsible reviewer's
decision** — not from the moment a supervisor opened the chart, and not from
submission (§R-11 §11.3). The distinction is the whole point: a finding generated
at 09:00 and submitted at 17:00 has been outstanding for eight hours, and a clock
that starts at submission reports zero of them. What is at risk is the patient's
elapsed exposure, not the supervisor's screen time.

**A review that ages past the profile's threshold opens a `role_routing`
obligation naming a backup reviewer** (§11.8). Three things it deliberately is
not:

- **Not an auto-approval.** Nothing about ageing marks a visit reviewed.
- **Not a state change.** The visit stays in `submitted`; the state machine and
  its gates are untouched. An obligation is created *beside* the visit, owned by
  a named person, ageing visibly like every other obligation.
- **Not a timeout that closes anything.** A due time that passes is a
  surveillance event (§11.9), exactly as with escalation.

Where the profile supplies no review-ageing threshold and no backup, the system
does what it does everywhere else an operational policy is absent: it falls back
to an explicit human decision and records that it had to (§10.5). It does not
invent a number.

This closes the one durable-work gap the ledger had left open. §11.8 guarantees
that unresolved *clinical findings* survive; until now an unresolved *review*
survived only as a row nobody owned. Both are now work with a name attached.

#### Refused transitions

Each is a test (§12.6).

| Refused | Why |
|---|---|
| `scheduled → submitted` | Nothing was captured or evaluated |
| `in_progress → completed` | Every visit passes through `submitted` |
| `submitted → in_progress` | Would let a clinician edit after review began. The reviewer returns work as a new task, never a rewind |
| `escalated → completed` | `escalated` exits only to `submitted` |
| Entering `escalated` with no named person or no due time | An escalation addressed to nobody is a queue (§11.2) |
| `completed → *` | Terminal. Corrections are new addendum encounters (§5) |
| `cancelled → in_progress` | A cancelled visit is not resumable; schedule a new one |
| Any observation write outside `in_progress` | One state creates clinical facts |
| Any transition that gates the emergency hatch | Hard invariant (§11.7) |

### 11.3 Triggers in operation

§8.1 defines the three triggers and their purity. This section defines what runs
them.

| Trigger | Mechanism | Output |
|---|---|---|
| `visit` | The in-home loop calls `evaluate()` on encounter open and after each capture (§11.5) | Cards rendered live to the clinician |
| `data` | A nightly worker loop (§3.1) over every `active` patient. Fires when new data landed, or when data aged out of some rule's `max_age_days` window (§7.1) | Obligations opened, updated, or closed (§11.8); findings routed to owners |
| `calendar` | The same worker, matching today against dated clinical events in the tenant profile (§10.5) | Same as `data` |

**The sweep diffs, it does not merely evaluate.** A sweep run compares its
evaluation records against the patient's previous run. A finding that appeared,
disappeared, or changed severity is what routes to an owner. Without the diff the
sweep would re-notify every open finding nightly, which is alert fatigue
manufactured on a schedule (§R-7).

**The diff baseline is the patient's last *completed* evaluation, never the last
attempted one.** A sweep that dies partway through would otherwise leave the
patients it never reached diffing against a stale baseline on the following
night, silently dropping a night of change.

**Each sweep writes a run record**: `started_at`, `completed_at`,
`patients_evaluated`, `patients_failed`, `catalogue_release`. It is the same
argument as §8.2 applied one level up — a sweep that never ran produces no
records, and absence is not detectable from the records that exist. §11.9 reports
a missing or partial run as an anomaly rather than reporting silence. Re-running
after a failure is therefore safe: completed patients diff to no change and route
nothing (§12.6 claims 23, 24).

**A catalogue or terminology release re-evaluates affected patients.** §12.2
compares releases against the golden set at build time; nothing in that catches
live patients whose findings change under the new release. The sweep closes it
without a new trigger: a patient whose last evaluation pins a `catalogue_release`
or `terminology_version` other than the active one is due, exactly as if data had
aged out. Valueset membership and threshold revisions reach real patients on the
first night after activation rather than at their next visit.

**Ramadan dates are configuration, not computation.** The date for each Hijri
year is an administrative field set per tenant, because the local announcement
governs and a computed date can differ from it. IDF-DAR 2021 places risk
stratification 6–8 weeks before Ramadan (§R-1 §1.6); Noor fires the calendar
trigger at T−8 weeks against the configured date.

### 11.4 The pre-visit brief

Assembled when a visit is `scheduled`, from two sources: **open obligations**
(§11.8) and the **most recent evaluation record** (§8.2).

It answers three questions: what is overdue, what is unresolved, and what to
bring.

This is where the ledger pays for itself. The clinician arrives knowing that the
HbA1c ordered three weeks ago never came back — a fact no single encounter record
holds, and one that is invisible to any system that reasons only over what fired
today.

The brief is a **read view**. It creates no state and closes no obligation. An
obligation is not closed by having been read.

### 11.5 The in-home visit loop

```
1. Confirm identity
2. Chief Complaint (free text + structured signals)
3. History of Present Illness (free text + structured signals)
4. Capture vitals through canon (§6)
       ├─ unit ambiguous ──────────► hard stop, resolve here (§6.3)
       └─ implausible delta ───────► needs_repeat_or_verification, continue (§6.2)
5. Physical Examination (free text + structured signals)
6. evaluate()                                          ─┐
7. Render cards: seven parts, fixed order (§7.2)        │
8. Record planned actions (§11.6)                       │ loop
9. Re-evaluate with requested_actions                   │
10. Acknowledge / override with structured reason (§9.2)│
       └─ revise an action ────────────────────────────┘
11. Close (§11.8)
```

**Steps 5–6 are the load-bearing pair.** Evaluation is a loop, not a pass. The
clinician records intent, the evaluator runs again with that intent present, and
a `stop_and_review` rule whose `order_of` matches marks the action `blocked_by`.
Without the planned-actions list, §7.1(c)'s blocking semantics have no surface to
act on and a hard stop degenerates into a general-purpose interruption — exactly
what the schema was written to prevent.

Only two things stop the clinician inside the home: an unresolvable unit (§6.3)
and an unacknowledged `interruptive_review` at the submission gate (§11.2).
Neither can stand between the clinician and the emergency hatch.

### 11.6 Planned actions

*(Was §7.5. Moved here: a planned action is encounter state, not evaluation
state. The evaluator reads the list; the encounter owns it.)*

The **planned-actions list** is the structured set of things the clinician
intends to do in this encounter, recorded during the visit and passed to the
evaluator as `requested_actions` (§8.1).

```yaml
planned_action:
  encounter_id: ...
  kind: medication_start | medication_stop | medication_dose_change
      | lab_order | referral | plan_change
  subject: metformin           # what `order_of` matches against
  detail: {dose: "500 mg", frequency: "BD"}
  state: draft | final
  blocked_by: [rule_id, ...]   # set by the evaluator, never authored
```

Two consequences:

1. **A blocked action cannot be marked `final`.** This is the *only* thing a hard
   stop blocks. Documentation, note submission, visit close, and emergency
   activation are never blocked (§7.1c, §8.3, §11.7).
2. **Actions with durable consequences open obligations at close.** A `lab_order`
   opens a `pending_result`; a `plan_change` opens a `patient_contact` (§11.8).
   This is the join between an intention recorded in a home and work that
   outlives the visit.

**Which kinds open an obligation automatically is profile data (§10.5), and the
default is to open.** The asymmetry decides it: an obligation opened
unnecessarily is visible noise a clinician closes with a reason, while an
obligation never opened is clinical work that silently ceased to exist — the
failure the ledger exists to prevent (§11.8). `lab_order` and `plan_change` are
settled (above); `referral` and the remainder are provider-specific and open by
default until a provider says otherwise.

The clinician may override the default for a given action, with a reason. Those
overrides are the dataset that answers §16 item 8 (§11.9): the question is
settled by watching what clinicians actually do, not by choosing in advance.

Planned actions are encounter-scoped and are **not observations**: they record
intent, not a clinical fact. An action that is carried out produces observations
through the ordinary path (§5).

### 11.7 The emergency hatch

> One tap. Any state. No gate of any kind.

The encounter freezes to `interrupted_for_emergency` and the timestamp is
recorded.

**No required field, unsaved form, unacknowledged alert, blocked action, repeat
prompt, or data-quality flag may stand in the way.** This is a hard invariant
(§0) and it is tested from the most hostile state the system can construct (§12.6
claim 5).

Documentation is **retrospective, with the real time gap preserved**. Nothing is
backdated. The hatch exits only to `submitted`, so an emergency still receives
supervisor review.

Protocol content — who is called, what is done — is provider-supplied, locally
configured, and rehearsed (§13.2 item 7). Noor owns the guarantee that the hatch
opens; it does not own what happens next.

#### What counts as a red flag is governed content, not workflow prose

The hatch is a mechanism. **Which clinical picture should open it is a separately
governed, separately cited clinical-content package** — `content/red_flags/` —
carrying the same governance as any other catalogue content (§10): named clinical
owner, second approver, source citation, effective date, next review.

Five libraries, all named by §R-11 §11.10 and all in scope for Noor's two
conditions and their acute complications: **DKA and HHS, severe hypoglycaemia,
hypertensive emergency, ACS, and stroke.**

Each library must:

- **Separate symptoms that prompt emergency activation from values that prompt
  repeat or urgent review.** These are different actions with different costs. A
  number that triggers a re-check is not a number that triggers an ambulance, and
  collapsing them produces either an unusable hatch or a dangerous one.
- **Reflect patient context and measurement quality.** A `needs_repeat_or_verification`
  reading (§6.2) is not the basis for emergency activation on its own; §6.6's
  context fields and §5's provenance apply here as everywhere.
- **State explicit exclusions** — the patients and situations the flag does not
  apply to.

> **These thresholds are never written from memory.** §R-11 §11.10 says so
> directly, and it is the one place in this document where writing a plausible
> number would be indistinguishable from writing a correct one. A red-flag
> library with `status: unpopulated` thresholds fails §10.4 gate 1 like any other
> content, which means Noor ships with no red flag before a clinician has cited
> one — and the hatch still opens by hand on the clinician's own judgement, which
> is what it was built for.

### 11.8 The obligation ledger

*(Was §7.6. Moved here: an obligation is durable clinical work, created and
closed by the workflow. Evaluation supplies the evidence; operations own the
ledger.)*

An **obligation** is clinical work that outlives the encounter that created it.
One table; `kind` discriminates.

```yaml
obligation:
  kind: pending_result | carried_forward | role_routing | patient_contact
  patient_id: ...
  opened_by: {evaluation_record_id: ..., encounter_id: ...}
  owner: {role: ..., person_id: ...}      # a named person, never a queue alone
  subject: "HbA1c ordered 2026-06-12"
  state: open | closed
  stage: ordered                           # pending_result only — see below
  closed: null                             # {by: person_id, reason: ..., at: ...}
  opened_at: 2026-06-12T14:02:00+03:00
  last_seen_at: 2026-07-30T09:00:00+03:00  # ages visibly; never auto-expires
```

#### `stage` refines a `pending_result`; it does not weaken `state`

§R-9 specifies a six-state lifecycle for an awaited result: `ordered`,
`specimen_collected`, `pending`, `final_received`, `not_received`, `cancelled`.
Noor carries it as `stage`, **on `pending_result` obligations only**, and it is a
different axis from `state`:

| | |
|---|---|
| `state` | Is this work still owed? `open` or `closed`. Governed by the closure invariant below. Unchanged. |
| `stage` | Where in the pathway is the awaited result? Diagnostic detail on an open obligation. |

`stage` never closes anything. `final_received` records that the result landed;
the obligation closes only when re-evaluation is recorded and the change routed
(the table below), which is the same bar as before. `not_received` and
`cancelled` are the sharp cases and they behave identically to everything else in
this section: **both leave `state: open` and require a named human to close with
a reason.** A specimen that never arrived is unfinished clinical work, not a
resolved one, and a cancelled order is a decision somebody made and should sign.

The reason to carry `stage` at all is diagnostic. §11.9 already ages a
`pending_result` as a surveillance signal, but "open for 40 days" does not
distinguish *nobody drew the blood* from *the lab has it and the interface is
broken*. Those are different failures with different owners, and only `stage`
separates them.

#### Concurrency

Three writers touch this table: the nightly sweep (§11.3), visit close (§11.5
step 8), and a clinician acting directly. They contend on one field that matters
— `state`. A sweep closing an obligation on resolved data, racing a human closing
it with a reason, is a lost update inside a security-critical invariant (§0), and
a silently lost closure is indistinguishable from a correct one.

**Every state change acquires a row lock first** (`SELECT ... FOR UPDATE`) inside
the transaction that decides. All three writers route through one close path, so
this is one lock in one function, not a protocol spread across callers. With a
single worker loop (§3.1) there is no contention worth optimising and no retry
logic to get wrong.

**Closure is once-only, enforced by the database.** A row already `closed` cannot
be closed again or reopened; a correction is a new obligation, for the same
reason a corrected observation is a new observation (§5). Note what this makes
explicit: the ledger is the one mutable clinical table in an otherwise
append-only architecture, and the constraint is what keeps that mutability
bounded to a single irreversible transition (§12.6 claim 22).

`last_seen_at` is advisory ageing, not state. A lost update there costs a
timestamp, so it does not take the lock.

| Kind | Created when | Closes when | Status |
|---|---|---|---|
| `pending_result` | A `lab_order` planned action is finalised for a result Noor expects back (§11.6) | The result lands, re-evaluation is recorded, and the change is routed | **MVP** |
| `carried_forward` | A finding is deferred (§9.2 `defer_or_escalate`), or an outcome is `indeterminate` (§8.3) | The finding resolves with usable data, or a named human closes it with a reason | **MVP** |
| `role_routing` | A tenant profile routes a finding to another role (§10.5), or a `submitted` visit ages past the profile's review threshold and a backup reviewer is named (§11.2) | The named role acts | **Plumbing only for profile routing.** Default: no routing. §13.2 item 6 forbids encoding a job-title rule; a medical director supplies one in writing. The review-ageing use is MVP |
| `patient_contact` | The plan changed after the clinician left the home | Teach-back is confirmed with the medicine-manager (§5.7) | **MVP, gated.** Requires `consent_ref` (§5.7); Arabic patient-facing wording is §13.2 item 9 |

#### The closure invariant

> An obligation never closes because its rule became `indeterminate`.
>
> It closes only on `not_triggered` **with usable data** (§8.2), or by a named
> human recording a reason.

This is §8.2's thesis applied to durable state. A broken lab feed turns every
renal rule `indeterminate`; if that closed the corresponding obligations, the
ledger would empty itself during exactly the failure it exists to survive — and
an empty ledger is indistinguishable from good care.

Three supporting rules:

- **Sending is not closing.** A message to a patient or caregiver does not close
  a `patient_contact` obligation; only confirmed teach-back does (§R-11 §11.4).
- **Reading is not closing.** Appearing in a pre-visit brief (§11.4) does not
  close an obligation.
- **Terminal encounter states do not close obligations.** Abandoning an encounter
  holding an unresolved severe value opens a `carried_forward` obligation rather
  than discarding it — observations are write-once (§5), and a severe value must
  never be left with no owner.

Two cases the invariant reaches that are easy to miss:

- **`out_of_scope` does not close an obligation** (§8.2). A patient leaving a
  rule's scope means the rule stopped applying, not that the outstanding work was
  done. A named human closes it with a reason, as with any other unresolved
  obligation.
- **Retiring a rule does not close its obligations** (§10.1). A `retired` rule
  never evaluates again, so `not_triggered` can never arrive and the obligation
  would otherwise sit open forever with nobody told. Retirement therefore
  enumerates the open obligations that rule opened and routes each for named
  human closure. Retirement is a governance action with a work list attached, not
  a file deletion (§12.6 claim 25).

Obligations **age visibly** and are surfaced at the next encounter. They never
auto-expire: silent expiry is the same failure as silent non-firing (§8.2).

### 11.9 Surveillance and the content loop

The loop that turns operational evidence into catalogue change:

```
§8.2 evaluation records
   ├─► zero-firing anomaly detection (§9.3)
   ├─► "expected alert absent" reports — one action, any clinician (§9.3)
   └─► override patterns stratified by rule / severity / role / reason (§9.2)
            │
            ▼
   clinician review
            │
            ▼
   pull request → four-eyes approval (§7.5)
            │
            ▼
   release → release comparison (§12.2) → active catalogue
```

**Never auto-tuned.** A rule changes because a human approved a pull request
(§7.5). Self-tuning thresholds are rejected outright (§15.3).

Obligation ageing is a surveillance signal in its own right: a `pending_result`
still open well past the expected turnaround is either a broken lab pathway or an
order nobody placed. Both are worth knowing; neither is visible from a log of
alerts that fired. **The ageing threshold is profile data (§10.5), not a
constant** — no Saudi home-lab turnaround pathway is a public fact (§13.3), so a
number written into code would be a guess wearing the costume of a standard.

Sweep run records (§11.3) are the third signal. A missing run, a run that ended
with `patients_failed > 0`, or a run whose duration crosses the migration
threshold (§3.4) is reported here. The engine's own health is subject to the same
rule as its rules: silence is not evidence of correctness.

#### Capture quality is measured, not assumed

`canon` (§6) enforces unit safety, plausibility, and repeat-before-action. Whether
those defences are *working* — and whether they are costing more than they buy —
is not visible from the rules that fired.

§R-11 §11.1 refuses a universal EMR entry-error target and says instead that Noor
should establish its own baseline during a shadow pilot (§13.2). Seven counters,
all computed from data `canon` already writes:

| Counter | What a bad value means |
|---|---|
| Missing-unit rate | The intake path is losing units before `canon` sees them |
| Rejected-value rate | Either a real data problem or a `canon` rule too tight to work with |
| Delta-check rate | §6.2's plausibility bands are mis-set, in one direction or the other |
| Repeat-confirmation rate | How often a flagged reading is actually repeated rather than accepted |
| Correction rate | How often a written observation is superseded by an addendum (§5) |
| Time-to-correction | How long a wrong value stayed actionable |
| Proportion of clinically important changes after verification | **The one that justifies the whole mechanism.** If repeating a flagged reading almost never changes the clinical picture, the repeat prompt is friction with a safety costume |

These share §11.9's standing rule: **surveillance signals, never targets.** A
rejected-value rate managed downward is a `canon` that stopped rejecting things.

#### Instrumenting the open questions

§16 records questions Noor cannot answer from the desk. Several of them are
answerable from a pilot — but only if the system collects the evidence while the
question is open. An unmeasured unknown does not stay open; it gets closed
silently by whatever the code happened to do.

Four counters exist for that reason, and each maps to a question:

| Signal | Answers |
|---|---|
| Review SLA — rule evaluation time to responsible reviewer decision — by supervisor, plus backlog age and every backup routing (§11.2) | §16 item 5 — sustainable review load. A rising distribution is the rubber-stamp risk becoming visible before it becomes routine, and the clock starts where the patient's exposure starts, not where the supervisor's screen time does. |
| Time from entering `escalated` to acknowledgement by the named person, and every breach of the due time | §16 item 6 — the escalation bound. The pilot measures what the provider can actually sustain instead of asserting a number in advance. |
| Every manual `establishing_baseline → active` decision, with the data present at the moment it was made | §16 item 7 — the baseline completeness bar. The bar is a description of what clinicians already require; collect the decisions and it writes itself. |
| Every clinician override of the default obligation behaviour for a planned-action kind, with reason (§11.6) | §16 item 8 — which action kinds warrant an automatic `pending_result`. |

These are **surveillance signals, never targets** — the same rule §9.2 imposes on
override rate, for the same reason. A review-time counter that becomes a
performance metric produces fast reviews, not good ones.

### 11.10 Offline — specified, not built

With no signal, a small local set — verified allergy, absolute contraindication,
dose ceiling — still evaluates on-device. **Everything else is clearly marked
*not yet checked*, never silently skipped.** A blank card where a check would
have been is the silent-non-firing failure (§8.2) with a network cause.

Deferred to Phase 2 (§15.1). §8.4 invariant 9 keeps it buildable: rules are pure
functions of a snapshot, so the evaluator is portable. Invariant 10 matters here
too — an evaluator that read encounter state could not run identically on a
device that holds only part of the workflow.

---

## 12. Testing and validation

Governed by `docs/testing-standards.md`; the behavioural rules in `CLAUDE.md`
apply now. Where the two disagree, this document wins.

### 12.1 The ladder

1. **Schema and compile validation** — the catalogue is machine-checked (§10.4).
2. **Rule-unit rows** — `*.cases.yaml`, table-driven. Written first; must fail
   before the rule exists.
3. **Golden patient cases** — whole snapshots producing an expected finding set.
4. **State-machine tests** — every valid transition succeeds; every invalid one
   is refused (§11.2, §12.6).
5. **Integration** — through the HTTP layer.
6. **Release comparison** — §12.2.
7. **Independent clinical validation** — a clinician who did not author the rule.
8. **Shadow mode** — evaluate without displaying; compare against clinician
   action (§12.7).

### 12.2 Release comparison

Run catalogue *vN* and *vN+1* over the full golden set and diff. **Any finding
that changes or disappears must be explained in the release manifest or the
release is blocked.** This is build-time non-firing detection, complementing the
runtime detection in §8.2.

### 12.3 Case selection

Boundary plus pairwise, explicitly **not** exhaustive. A published CDS pathway
with 26 decision points yields 3,120 combinations; 100 well-chosen cases
exercised the major pathways at roughly 1% combination coverage (§R-9).

Minimum per threshold: three rows — at, just below, just above.

Invalid state-machine transitions are tested as rigorously as valid ones.

### 12.4 Synthetic data

Synthea is used for **plumbing and adversarial fixtures only**. Its Massachusetts
demographics make it unsuitable as a Saudi validation cohort, and it is never
described as one (§R-9).

### 12.5 Calibrated-reliance audit

Deliberately seeded wrong *and* seeded correct advice, used to measure whether
clinicians are over- or under-relying on Noor (§R-7). Training cases include
deliberately wrong and incomplete examples. Escalation is blame-free and fast.

### 12.6 Clinical-operations verification claims

Each row is a test written before the corresponding code.

| # | Claim | Verify | §|
|---|---|---|---|
| 1 | Only `in_progress` writes observations | Attempt an observation write in each of the other seven states → refused | §11.2 |
| 2 | `indeterminate` never blocks submission | A visit with an unmet data requirement submits successfully | §8.3 |
| 3 | Unacknowledged `interruptive_review` holds submission | The gate refuses; acknowledging with a structured reason releases it | §11.2 |
| 4 | `stop_and_review` degrades, never disappears | Remove a required datum → outcome becomes `interruptive_review`, not `not_triggered` | §8.3 |
| 5 | The emergency hatch cannot be blocked | From `in_progress` with an unacknowledged `stop_and_review`, a blocked `final` action, and an empty required field → the hatch still opens | §11.7 |
| 6 | An abandoned severe value survives and is owned | Abandon a visit holding BP 210/120 → the observation persists and an obligation opens | §11.2, §11.8 |
| 7 | An obligation survives `indeterminate` | Age a rule's data out of its window → the obligation stays open | §11.8 |
| 8 | The reviewer sees the pinned evaluation | Land new data after submission → the reviewer sees the original plus a separate "new since submission" panel | §11.2 |
| 9 | `submitted → in_progress` is refused | Attempt the rewind → refused | §11.2 |
| 10 | Every rule considered writes a record | Evaluate → record count equals every rule in the active catalogue under this profile, with no exclusions: `triggered`, `not_triggered`, `indeterminate`, `out_of_scope`, and `suppressed_by_governed_policy` together account for all of them | §8.2 |
| 11 | Every visit passes through `submitted` | Attempt `in_progress → completed` → refused | §11.2 |
| 12 | `escalated` exits only to `submitted` | Attempt `escalated → completed` → refused | §11.2 |
| 13 | Escalation ends capture | Escalate from `in_progress`, then attempt an observation write → refused | §11.2 |
| 14 | The calendar trigger fires without new data | Advance the clock to the configured Ramadan date minus eight weeks with no new observations → evaluation runs | §11.3 |
| 15 | A blocked action cannot be finalised | Mark a `blocked_by` action `final` → refused; the visit cannot submit while it stands | §11.6 |
| 16 | Sending is not closing | Send a `patient_contact` message → the obligation stays open until teach-back is confirmed | §11.8 |
| 17 | The sweep diffs rather than re-notifying | Run the sweep twice with unchanged data → the second run routes nothing | §11.3 |
| 18 | No rule reads encounter state | The catalogue compiler refuses a rule referencing visit state or trigger identity | §8.4, §10.4 gate 11 |
| 19 | Out-of-scope rules record without opening work | Evaluate a rule whose `scope` excludes the patient → outcome is `out_of_scope`, no `requirement_verdicts` are produced, and no obligation opens | §8.2, §11.8 |
| 20 | The snapshot is a closed contract | Add an undeclared field to the snapshot → refused; author a rule referencing a field absent from the snapshot schema → the compiler refuses it | §4.2, §10.4 gate 12 |
| 21 | The catalogue loader executes nothing | Load a rule file containing a `!!python/name:` or `!!python/object/apply:` tag → refused, with no object construction | §7.5 |
| 22 | An obligation cannot be closed twice | Two concurrent closers on one obligation → one succeeds, the other is refused; the surviving `closed` record names a single person and reason | §11.8 |
| 23 | A partial sweep does not corrupt the next diff | Kill the sweep mid-run, rerun it → patients not reached in the failed run diff against their last *completed* evaluation, and nothing double-routes | §11.3 |
| 24 | A missed sweep is visible | Skip a nightly run → surveillance reports the gap rather than reporting silence | §11.3, §11.9 |
| 25 | A retired rule does not orphan its work | Retire a rule holding open obligations → each is routed for named human closure, none closes automatically | §10.1, §11.8 |
| 26 | `patient_contact` requires consent | Open a `patient_contact` obligation for a medicine-manager with no recorded consent → refused | §5.7, §11.8 |
| 27 | An escalation names a person | Enter `escalated` with no responsible person or no due time → refused. With no profile escalation policy, the clinician's hand-named recipient is recorded together with the fact that no policy supplied one | §11.2, §11.8 |
| 28 | A passed due time surfaces, never auto-closes | Advance the clock past an escalation's due time → the escalation stays open, unchanged, and the breach appears in surveillance | §11.2, §11.9 |
| 29 | A missing operational policy is refused, not defaulted | Load a tenant profile omitting the escalation policy, an ageing threshold, or a per-kind obligation default → refused at load | §10.5 |
| 30 | A stalled review never auto-completes | Hold a visit in `submitted` past any ageing threshold → it stays `submitted`, is reported as ageing, and does not complete without a supervisor | §11.2, §11.9 |
| 31 | Baseline promotion records who and what | Move a patient `establishing_baseline → active` → the record names the deciding clinician and captures the data present at that moment | §11.1, §11.9 |
| 32 | An obligation-default override records its reason | Decline to open a `pending_result` obligation for a kind whose profile default is open → the override, its reason, and its author are recorded | §11.6, §11.9 |
| 33 | A break-glass access is never blocked and never silent | Access a patient outside the roster → access proceeds, and a break-glass record naming person, patient, reason, and time exists before the data is returned | §2.6 |
| 34 | An unverified allergy does not block | Author a `stop_and_review` allergy rule, evaluate against an allergy whose `verification_status` is `unconfirmed` → the outcome degrades to `interruptive_review` | §5.5, §8.3, §9.1 |
| 35 | "No known allergy" is recorded, never inferred | Evaluate a patient with an empty allergy list and `allergy_status: not_asked` → outcome is `indeterminate` and an obligation opens; it is never treated as `no_known_allergy` | §5.5, §11.8 |
| 36 | A missing weight does not become a silent eGFR | Evaluate a CrCl-based renal rule with no weight → outcome is `indeterminate`; no eGFR value is substituted | §5.2 |
| 37 | `stage` never closes an obligation | Set a `pending_result` to `not_received` or `cancelled` → `state` stays `open` and a named human is still required to close it | §11.8 |
| 38 | A stalled review routes to a named backup | Age a `submitted` visit past the profile's review threshold → a `role_routing` obligation opens naming a person; the visit stays `submitted` | §11.2, §11.8 |
| 39 | The review clock starts at evaluation | Evaluate at T, submit at T+8h, review at T+9h → the recorded SLA is 9 hours, not 1 | §11.2, §11.9 |
| 40 | A card cannot be rendered against the wrong patient | Render a card whose patient id does not match the encounter → refused | §7.2 |
| 41 | Unit conversion is reversible | For every registry conversion, convert a value out and back → the original is recovered within the declared precision | §6.3 |
| 42 | Free text does not enter the snapshot | Attempt to compile a rule referencing the encounter narrative text → refused by the compiler; attempt to load text into the snapshot → rejected by Pydantic | §5, §8.4 |

### 12.7 Shadow mode

Rung 8 of the ladder, and the last thing that happens before a clinician sees a
card. §R-9 is explicit that simulation and shadow running come **before**
clinician-facing use, not after a soft launch.

**What it is.** Noor evaluates real patients on the provider's real workflow and
writes real evaluation records (§8.2) — and displays nothing. The clinician works
as they did before. Nobody is asked to react to a card, and no card exists to
react to.

**What it monitors** — the four signals §R-9 names, all of which the architecture
already computes:

| Signal | Reads |
|---|---|
| No-fire | Zero-firing detection (§9.3), stratified by `out_of_scope` versus `indeterminate` versus `not_triggered` (§8.2) |
| Firing spikes | Rule-level counts against the shadow baseline |
| Data-quality rejection | The seven capture counters (§11.9) |
| Unexpected override patterns | Not available in shadow — nothing is displayed, so nothing is overridden. It becomes measurable only at first clinician-facing use, which is why shadow mode is a floor and not a ceiling |

**What it is not.** Shadow mode is not a pilot, and it does not substitute for the
independent clinical validation on rung 7 or for §12.2 release comparison. It
answers one question those cannot: *does this catalogue behave sanely against
this provider's actual patients and actual data feeds* — which no golden set can
answer, because a golden set contains the data somebody remembered to include.

**Two runs, not one.** Synthetic and de-identified cases first (§12.4), then
provider-approved silent running on live data. The first proves the plumbing;
only the second meets a real lab feed.

Shadow mode is §13.2 item 12 and §14 step 16. It carries **no fixed duration
here** — the exit criterion is that the four signals are stable and explained,
and how many days that takes is provider data, not an architectural constant
(§13.3). It is also where the capture counters (§11.9) and the review SLA
(§11.2) acquire their first real values, which is what §16's interim positions
are waiting for.

---

## 13. Gates

The research reads as one long list of things to verify. Almost none of it blocks
code. Separating the two classes is what allows building to start while every
clinical gate stays genuinely closed.

### 13.1 Blocks code (2)

1. **`canon` lands before any threshold logic.** Units, source/time/status,
   repeat and verification, delta review, and "cannot assess safely" come first
   (§R-11 gate 1).
2. **No hard stop ships without a second clinician approver** (§10.3).

### 13.2 Blocks patient use, not code (14)

1. SFDA classification determination.
2. PDPL DPIA, controller/processor contract, and Saudi hosting procurement.
3. SNOMED CT Saudi Affiliate licence via MLDS.
4. Written ICD-10-AM commercial-use position.
5. ATC redistribution rights.
6. Provider supervision and prescribing authority, in writing from the medical
   director, credentialing, and legal/compliance. **Noor does not encode a
   supervisor-sign-off model based on job title** — no universal Saudi rule was
   found (§R-2, §R-11). The mandatory-`submitted` policy (§11.2) and the
   `role_routing` obligation (§11.8) are both profile data awaiting this.
7. Provider-approved emergency pathway, locally configured and rehearsed
   (§R-11 §11.10). Noor guarantees the hatch opens (§11.7); the provider owns
   what follows.
8. Medication-knowledge scope disclosure text, clinician-approved.
9. Arabic patient-facing content: qualified translation and clinical validation.
   This gates the `patient_contact` obligation (§11.8). **Scope includes
   right-to-left rendering, not only translated strings** — layout direction,
   mirrored iconography, and mixed Arabic/Latin numeral and unit runs. A
   correctly translated card in a left-to-right layout is not Arabic content.
10. Saudi LDL-target table transcription — the source document renders it
    graphically; it requires transcription and dual verification by a clinical
    owner before becoming executable (§R-1).
11. **Safety-case operational processes**: complaint handling, incident log, and
    post-market review, each with a named owner and a stated cadence (§2.1,
    §R-2). These are business processes, not software; the architecture holds the
    other six components already.
12. **Shadow mode completed and its four signals explained** (§12.7). Synthetic
    and de-identified cases first, then provider-approved silent running on live
    data. No clinician sees a card before this closes (§R-9).
13. **LOINC attribution in place** (§3.3, §R-4). The licence is perpetual and
    no-fee but conditional: the prescribed notice must appear on Noor's
    legal/terms screen, the identifier and official display name must be
    preserved alongside every mapping, and any third-party rights named in the
    release must be respected. **Arabic UI labels live in a separate field** —
    LOINC treats a translation as a derivative work requiring prior
    notification, so an Arabic string must never overwrite a LOINC display.
    §10.4 gate 17 refuses a code system absent from the terminology charter,
    which is where this attribution is recorded.
14. **PHQ-9 licence terms and the item-9 escalation pathway**, if depression
    screening ships at all (§R-1 §1.7). PHQ-2/PHQ-9 is freely reproducible but
    **conditionally**: the official form, attribution, wording, response options,
    and scoring must be preserved verbatim, the Arabic version must come from the
    official PHQ repository, and **a positive item 9 — self-harm ideation — must
    have an explicit, clinician-validated escalation pathway before the
    questionnaire is embedded.** A screening instrument that can surface
    suicidality with no defined route out of the screen is the sharpest version
    of the failure §11.7 exists to prevent. This gate is the reason depression
    screening is **not** in the MVP scope: it is a fully separate clinical
    pathway, not a questionnaire.

### 13.3 Explicitly unresolved

The research established that these do **not** exist as public facts. They are
diligence questions for a named provider, not gaps to fill with extrapolation
(§R-11):

a Saudi national resident/consultant home-prescribing co-sign rule; a sustainable
supervisor visit-load benchmark; a Saudi public home-lab ordering, payment, and
turnaround pathway; a named point-of-care device configuration; a public Sehhaty
clinical API; a Saudi home-visit field-connectivity rate; a universal hard-stop
or override benchmark; a Saudi medication-error disclosure requirement applicable
to Noor; and MNGHA/Monsha'at sandbox clinical-data or regulatory-credit terms.

---

## 14. Build sequence

Each step states its verification. No step begins before the previous one
verifies.

1. **`git init`, repository skeleton, `uv`, `ruff`, `mypy`, CI.**
   *Verify:* CI runs green on an empty suite; the import-direction test exists
   and passes (§4.2).
   §7.5 makes git the clinical-content governance mechanism — a pull request
   *is* the four-eyes approval. This is a prerequisite, not housekeeping.

2. **`canon`: observable registry, unit resolution, plausibility, quality states.**
   *Verify:* property tests prove no observation reaches the engine with an
   unresolved unit, and that a real-but-extreme value and a mistyped value land
   in different states (§6.2). §12.6 claim 41: every registry conversion is
   reversible within its declared precision.

3. **`canon`: delta review and comparability.**
   *Verify:* like-with-like comparison only; a suspicious delta produces
   `needs_repeat_or_verification` and never mutates a value.

4. **`engine`: evaluator, outcome taxonomy, degradation invariant, evaluation
   records.**
   *Verify:* invariants §8.4 (1)–(10), each as a test. Determinism proven by
   running an identical snapshot twice in shuffled rule order. §12.6 claims 19,
   20 — scope resolves before requirements, and the snapshot refuses an
   undeclared field. §12.6 claims 34, 35, 36: an unconfirmed allergy degrades a
   `stop_and_review` rather than blocking; an unasked allergy history is
   `indeterminate` and never reads as "no known allergy"; a CrCl rule with no
   weight is `indeterminate` and never silently substitutes an eGFR.

5. **`catalogue`: loader, compiler, validator, CI gates.**
   *Verify:* the compiler refuses an uncited rule, an unpopulated threshold
   reference, a blended `source_family`, a `stop_and_review` with
   `role_doubling`, a rule referencing encounter state, a rule naming a field
   absent from the snapshot schema, an unrecognised operator, and a content file
   carrying an object-constructing YAML tag — each refusal is a test (§10.4,
   §12.6 claims 20, 21). §12.6 claim 29: a tenant profile omitting an
   operational policy is refused at load, never silently defaulted (§10.5).

6. **Content: the first workflow — renal-risk medication safety on new
   creatinine/eGFR.**
   *Verify:* cases written first and failing; golden snapshots pass; every
   threshold has three boundary rows.

7. **`app`: persistence, per-patient encryption, access control and the three
   logs, `evaluate` endpoint, evaluation-record storage.**
   *Verify:* golden cases produce the expected finding set through HTTP;
   evaluation records persist for non-firing rules; destroying a patient key
   renders that patient's clinical content unreadable while their evaluation
   records, timestamps, and outcomes remain intact and queryable (§2.5).
   The encryption boundary lands **here or not at all** — it is the same
   day-one commitment as §8.2, and for the same reason: a plaintext table
   cannot be retrofitted without migrating every row ever written. The same is
   true of the logs: §12.6 claim 33 — a break-glass access proceeds and its
   record naming person, patient, reason, and time exists *before* the data is
   returned (§2.6). Roles, session timeouts, and the `correlation_id` that joins
   the three logs are §0 constants and are built as written, not tuned later.

8. **`app/encounters`: the visit state machine, escalation ownership, and the
   patient lifecycle.**
   *Verify:* §12.6 claims 1, 9, 11, 12, 13 — every valid transition succeeds and
   every refused transition is refused. Observation writes are rejected in all
   seven non-`in_progress` states. §12.6 claims 27, 28, 30, 31: entering
   `escalated` without a named person and a due time is refused; a passed due
   time leaves the escalation untouched; a visit held in `submitted` past any
   ageing threshold does not auto-complete; promoting a patient
   `establishing_baseline → active` records the deciding clinician and the data
   present at that moment. §12.6 claims 38, 39: a `submitted` visit aged past the
   profile's review threshold opens a `role_routing` obligation naming a backup
   and stays `submitted`; the recorded SLA is measured from evaluation time, not
   from submission.

9. **`app`: card renderer with the fixed seven-part disclosure order, and
   override capture.**
   *Verify:* evidence and data status render before recommendation (§7.2); an
   override cannot be submitted without a reason code (§9.2); multiple findings
   on one subject render as one merged card at the highest effective severity,
   each contributing rule still holding its own evaluation record. §12.6 claim
   40: a card whose patient id does not match the encounter is refused rather
   than rendered (§7.2). Blocked on
   §16 item 9 — the merge policy needs the clinician reviewer.

10. **`app`: planned-actions loop and the submission gate.**
    *Verify:* §12.6 claims 2, 3, 15 — a `stop_and_review` rule marks a matching
    planned action `blocked_by`; that action cannot be marked `final`; the visit
    cannot submit while it stands; an `indeterminate` outcome never holds
    submission.

11. **`app/obligations`: the ledger and the closure invariant.**
    *Verify:* §12.6 claims 6, 7, 16, 22, 25, 26 — an obligation opened on a
    `triggered` finding does not close when the rule becomes `indeterminate`; an
    abandoned visit holding a severe value opens one; sending a message does not
    close a `patient_contact`; two concurrent closers produce exactly one
    closure; retiring a rule routes its open obligations for human closure; a
    `patient_contact` cannot open without `consent_ref`. §12.6 claim 32: a
    planned action opens or does not open an obligation according to the
    profile's per-kind default, and a clinician override records its reason and
    author (§11.6). §12.6 claim 37: setting a `pending_result` to `not_received`
    or `cancelled` leaves `state: open` — `stage` never closes anything.

12. **`app/sweep` and `app/briefing`: scheduled and calendar triggers, pre-visit
    brief.**
    *Verify:* §12.6 claims 14, 17, 23, 24 — the calendar trigger fires with no new
    data; a second sweep over unchanged data routes nothing; a sweep killed
    mid-run resumes without double-routing or losing a night of change; a missed
    run is reported. The brief assembles from open obligations and closes none.

13. **`app`: the emergency hatch.**
    *Verify:* §12.6 claim 5 — the hatch opens from the most hostile state the
    suite can construct. This is deliberately built after the gates it must
    defeat, so the test is meaningful.

14. **Content: second workflow — BP measurement quality, repeat, and severe-BP
    escalation with red-flag triage.**
    *Verify:* as step 6, plus the emergency path is never blocked by an
    incomplete form (§R-11 §11.10).

15. **Release comparison harness, zero-firing surveillance, and the
    open-question instruments.**
    *Verify:* a deliberately broken rule in a test release is caught by both.
    The four signals of §11.9 emit: the review SLA measured from evaluation time
    per supervisor, time from `escalated` to acknowledgement with every breach,
    every manual `establishing_baseline → active` decision with its data, and
    every override of a per-kind obligation default. The seven capture counters
    (§11.9) emit alongside them. These are the evidence that closes §16 items
    5–8, so they ship before the pilot rather than after it.

16. **Shadow mode.**
    *Verify:* Noor evaluates live patients on the provider's real data and
    displays nothing (§12.7). The four signals — no-fire, firing spikes,
    data-quality rejection, override patterns — are collected, stable, and
    explained before any clinician-facing use. This is a run, not a build step:
    its duration is provider data, and step 15 exists to make its output
    readable.

Steps 6 and 14 establish the content pattern. The remaining diabetes and
hypertension catalogue extends it incrementally — the schema and engine are
scoped to the full domain, while the catalogue fills in as citations and
clinician approvals are obtained. The engine refuses to run anything unfinished
(§8.4, §10.4), so partial content is safe by construction.

---

## 15. Deferred

### 15.1 Phase 2 — needs a named provider

Offline field client and local evaluation (§11.10); conflict-preserving sync with
append-only encounter events and explicit conflict objects (never
last-write-wins); FHIR R4 read adapters and CapabilityStatement discovery;
multi-tenancy beyond a single profile; conditional and adaptive forms; NPHIES.

**Partially deferred — the seam is at the ledger boundary.** §11.8 ships the
table, the four `kind` values, and the closure invariant. What remains Phase 2 is
everything whose shape depends on a provider's actual staffing:

| MVP (§11) | Phase 2 |
|---|---|
| A `patient_contact` obligation opens, names an owner, and closes only on confirmed teach-back | Messaging channel integration, retry cadence, unreachable-escalation ladder |
| A `role_routing` obligation opens and names a person, including the backup a stalled review routes to, and the review SLA is measured from evaluation time (§11.2) | The supervisor queue UI and the reviewer capacity model |
| Medication observations are captured and discrepancies preserved as discrepancies (§11.1) | The full reconciliation and brown-bag workflow |
| The visit state machine and its gates (§11.2) | Visit scheduling, routing, and caseload management |

The invariant is what ships now; the workflow around it needs a real provider.
Building the ledger later is not an option — an obligation that was never opened
cannot be reconstructed, for the same reason §8.2 is not retrofittable.

The MVP preserves the option: rules are pure functions over a snapshot (§8.4.9)
and read no encounter state (§8.4.10), so a portable evaluator remains possible.
The invariant "local evaluation produces results identical to server evaluation"
is a Phase-2 constraint, carried now as a design obligation on the schema rather
than as an MVP build.

#### The connectivity assumption, stated rather than implied

§R-11 §11.6 says something the rest of this document has been working around:
**public Saudi sources establish a highly digital health environment but do not
establish reliable connectivity at every home-visit location**, and they
therefore cannot justify treating offline as rare. The research recommends
designing *offline-first* for safety-critical documentation and local evaluation,
then quantifying actual connectivity by region, carrier, building type, and time
during discovery visits.

**Noor's MVP is online-first.** That is a departure from the recommendation, and
it is recorded here as one rather than left to be inferred from §11.10's position
in a deferred list.

The assumption being made, in full: *the first provider's home visits have
sufficient connectivity for live evaluation, and where they do not, the clinician
documents on paper and enters afterwards.* Two things follow.

1. **It is scoped, not universal.** It holds for one named provider in one
   deployment. It is not a claim about Saudi home care, and a second provider
   re-opens it.
2. **It is measured during discovery, not assumed away.** Region, carrier,
   building type, and time of day are the four dimensions §R-11 §11.6 names.
   Discovery visits collect them, and the result decides whether the Phase 2
   offline client is a convenience or a prerequisite.

**Why defer at all.** Offline-first is not a feature added to a system; it is a
property the whole data path either has or does not. Conflict-preserving sync,
append-only encounter events, explicit conflict objects, and on-device catalogue
distribution are each substantial, and building them against an unvalidated
clinical core means debugging sync and clinical logic simultaneously — with no
clinician yet able to say whether the logic is right. The order is deliberate:
get the decisions correct, then make them portable.

**What the MVP does not do is pretend the gap away.** §11.10 already forbids the
dangerous version: with no signal, the small local set still evaluates and
**everything else is marked *not yet checked*, never silently skipped.** A blank
card where a check would have been is the §8.2 failure with a network cause. That
guarantee is MVP. What is deferred is the offline *client* — the ability to keep
working through an outage — not honesty about being offline.

### 15.2 Phase 2 — needs evidence or validation

**Risk models** (KFRE, FIB-4, IWGDF foot category, SCORE2/SCORE2-OP). Each emits
a number the research then requires to be labelled "not locally recalibrated"
(§R-6, §R-1). A risk score nobody can act on is not MVP content. When
implemented: a shared `RiskAssessmentRun` record; published equations implemented
independently, never scraped from a calculator; `local_calibration_status`
displayed; an explicit eligibility gate; and `indeterminate — foot examination
required` rather than an inferred absence of LOPS or PAD.

**BP trajectory.** The evidence is decisive and it reshapes the feature:
within-person systolic SD is 10.6 mmHg, mean absolute between-visit difference
11.6 mmHg, ICC 0.28, and with a true 10-mmHg treatment effect the next visit
shows under 5 mmHg reduction 36.9% of the time (§R-6).

Therefore: **no variability score, no cut-off, and no trend claim from three to
six irregular readings.** What ships is (1) a measurement-quality gate, (2) a
descriptive display for one to five comparable encounters, and (3) for six or
more comparable readings, a robust time-aware linear slope with a 95% confidence
interval, **rendered only when the interval excludes zero**, and labelled
descriptive rather than a validated risk estimate. Home, office, and ambulatory
readings are never pooled.

This is a data-integrity feature, not a prediction feature, and it is described
that way to clinicians and to buyers. **Proactive escalation is never triggered autonomously by evaluating the velocity of this slope.** Instead, an escalating rule fires when a reading crosses the patient's explicit `goal_of_care` threshold (§5.6) or the profile's pinned guideline threshold (§7.3). Rules evaluate the state against the target; they do not predict the future.

**Adherence.** MMAS-8 is aggressively licensed with pooled sensitivity 0.43 at
cut-off 6; ARMS-D is non-commercial academic only; Voils DOSE requires a
per-project licence (§R-7). Noor uses its own structured, non-score
medication-use interview, explicitly labelled "clinical assessment, not a
validated adherence score." Pill counts are never used to label a patient
adherent — correlation is 0.52 for quantity and 0.17 for timing (§R-7).

**LLM features.** Deferred entirely. No patient data reaches a general-purpose
external AI service (§2.3).

### 15.3 Rejected outright

Autonomous action; EMR write-back; self-tuning thresholds; an unrestricted tenant
rule editor; machine-learned queue ranking (§R-11 requires an inspectable
safety-first ranking); a raw acceptance or override rate as a safety KPI; any
national prevalence or amputation claim (no current Saudi registry figure exists
— §R-1, §R-8).

Also rejected: **auto-expiring obligations**. An obligation that ages out on a
timer is silent non-firing with a calendar as its cause (§11.8). The escalation
due time (§11.2) is a deadline to be reported against, never an expiry — a
passed one leaves the escalation exactly where it was.

---

## 16. Open questions

Not blockers for the current build. Recorded so they are not silently resolved by
assumption.

**Recording is not enough.** A question left open without a stated interim
behaviour is not open — it is closed by whatever the code happens to do, at the
moment someone writes the code, by whoever writes it. So each question below
carries two things beyond the question itself: **what Noor does while the answer
is unknown**, and, where a pilot can produce the answer, **the signal that
produces it** (§11.9).

The interim behaviours share one shape. Where a fact is unknown, Noor takes an
explicit human decision and records who made it. That is worse than a rule and
much better than a constant: a recorded decision is visible, auditable, and
accumulates into the dataset that eventually replaces it. A default buried in
code is none of those things.

### 16.1 Questions that block business, not behaviour

No interim system behaviour is required. Noor's existing posture is already the
conservative one, and the answer changes commercial or regulatory position rather
than what the software does.

1. **Does SFDA offer a written pre-submission determination route Noor can use
   before a pilot?**
   *Interim:* §2.1 stands — Noor is treated as regulated SaMD until SFDA provides
   a written contrary determination. A favourable answer relaxes an obligation;
   it never adds one. Nothing waits on it.

2. **Which `source_family` does the first provider adopt for hypertension** —
   Saudi NHC/SHA 2023, ACC/AHA 2025, or ESC 2024?
   *Interim:* the default is NHC/SHA (§R-1). All three are supported, one is
   pinned per profile, and §10.4 gate 7 refuses blending. Switching later runs
   the affected golden set (§10.5) and re-evaluates live patients on the next
   sweep (§11.3) — so the answer is reversible, which is why it is not a blocker.

3. **What is the second clinician approver's engagement model, and when does it
   formalise?**
   *Interim:* §10.4 gate 4 refuses any `stop_and_review` rule without a named
   approver, so this enforces itself. Noor ships with zero hard stops until a
   credentialed second clinician signs (§10.3, §13.1). Everything else — engine,
   workflow, ledger, cards, sweep, hatch — is buildable meanwhile.

4. **Is the MNGHA–Monsha'at experimental AI-in-health environment a viable
   validation channel, and on what terms?**
   *Interim:* none needed. Ask in writing; participation is not regulatory
   clearance (§R-11 §11.11).

### 16.2 Questions that block behaviour

Each has an interim behaviour that is safe, explicit, and instrumented. None is
left to a constant.

5. **What is a sustainable review load per supervisor?** §11.2 makes supervisor
   review mandatory for every visit, and §R-11 §11.3 found no published
   benchmark. A review load high enough to become a rubber stamp is worse than no
   review, because it manufactures an audit trail nobody read.
   *Interim:* no cap and no timeout. A visit waits in `submitted`; care already
   happened and obligations already opened (§11.5 step 8), so a stalled review
   delays the note, not the patient. **What changed in 1.5.0:** a stalled review
   is no longer unowned. Past the profile's ageing threshold it opens a
   `role_routing` obligation naming a backup reviewer (§11.2, §11.8) — which is
   delegation of *attention*, not of sign-off. The visit stays `submitted`,
   nothing auto-completes, and the backup is a person rather than a queue.
   *Instrument:* the review SLA measured from **rule evaluation time** to
   reviewer decision, per supervisor, plus backlog age and every backup routing
   (§11.9, §R-11 §11.3). The clock starts where the patient's exposure starts.
   The pilot produces the number rather than waiting for someone to supply one.

6. **What is the escalation time bound, and who is paged?** An escalation with no
   SLA is a queue.
   *Interim:* entering `escalated` names a responsible person and stamps a due
   time (§11.2). Where the profile carries no escalation policy, the escalating
   clinician names the recipient by hand and the system records that they had to.
   A due time that passes is a surveillance event, never an auto-close.
   *Instrument:* time-to-acknowledgement and every breach (§11.9). The bound is
   provider data; the requirement that one exists is architectural.

7. **What is the baseline completeness bar** — the minimum data set that moves a
   patient from `establishing_baseline` to `active` (§11.1)?
   *Interim:* the transition is manual and recorded with the name of the
   clinician who made it.
   *Instrument:* every such decision is captured with the data present at the
   moment it was made (§11.9). The bar is a description of what clinicians
   already require; collect enough decisions and it writes itself.

8. **Which planned-action kinds open a `pending_result` obligation
   automatically, and which need the clinician to say so?**
   *Interim:* open by default, per-kind, as profile data (§11.6, §10.5).
   `lab_order` and `plan_change` are settled; the rest open until a provider says
   otherwise. The asymmetry decides the default — unnecessary noise is visible
   and closable, a missing obligation is silent.
   *Instrument:* every clinician override of the default, with reason (§11.9).

9. **How do multiple findings on one subject merge and order (§7.2)?**
   Polypharmacy makes this routine rather than exceptional, and it is a clinical
   presentation judgement, not an engineering one.
   *Interim:* merge by subject, highest effective severity, contributing rules
   enumerated, each keeping its own evaluation record (§7.2).
   *Blocked on:* the clinician reviewer, before §14 step 9. This is the one
   question a pilot cannot answer, because rendering the wrong merge to a
   clinician is the harm being avoided.

### 16.3 What is genuinely unanswerable here

§13.3 lists nine facts the research established do **not** exist publicly. They
are diligence questions for a named provider, not gaps to fill with
extrapolation. Every one of them now has either an interim behaviour above or a
profile field awaiting a value (§10.5) — which is the most an architecture can do
about a fact that does not yet exist.

The distinction that matters: **Noor has no unknown that resolves itself
silently.** Each is either enforced by a gate, recorded as a human decision, or
counted by a surveillance signal. That property is testable, and §12.6 claims
27–32 test it.

---

## 17. Research index

| Section | Subject | File |
|---|---|---|
| R-1 | Clinical guidelines and thresholds | `docs/research/archive/clinical-guidelines-and-thresholds.md` |
| R-2 | Saudi regulatory, PDPL, SFDA | `docs/research/archive/saudi-regulatory-pdpl-sfda.md` |
| R-3 | Drug knowledge base | `docs/research/archive/drug-knowledge-base.md` |
| R-4 | Terminology and units | `docs/research/archive/terminology-and-units.md` |
| R-5 | Interoperability and FHIR | `docs/research/archive/interoperability-and-fhir.md` |
| R-6 | Risk models and BP trajectory | `docs/research/archive/risk-models-and-bp-trajectory.md` |
| R-7 | CDS safety and human factors | `docs/research/archive/cds-safety-and-human-factors.md` |
| R-8 | Competitive and market landscape | `docs/research/archive/competitive-and-market-landscape.md` |
| R-9 | Technical architecture | `docs/research/archive/technical-architecture.md` |
| R-11 | Design-interview topics | `docs/research/archive/design-interview-topics.md` |

Section 10 of the research programme covered project constraints and produced no
separate file; its conclusions are stated directly in §1 and §10.3 of this
document. The closed research programme (sections 1–9, 11) is archived in
`docs/research/archive/`; nothing under it is maintained or read by the build.

**Clinical-content research** is tracked separately, because it is per-ingredient
and ongoing rather than a closed programme:

| Subject | File |
|---|---|
| Content coverage and per-ingredient research checklist | `docs/research/cds-content-roadmap.md` |
| Diabetes research (complications + pharmacotherapy) | `docs/research/diabetes-research.md` |
| Hypertension research (complications + pharmacotherapy) | `docs/research/hypertension-research.md` |
| Essential Medicines List of Saudi Arabia 2023 (verbatim, converted) | `docs/research/saudi-essential-medicines-list-2023.md` |

The SEML file is the only one of these that is a **primary source**, and it is the
authority for two claims and no others: whether an ingredient is listed, and which
strengths and dose forms are listed for it (§3.2 strength-achievability). It
carries no dosing, contraindication, interaction, or monitoring content.

