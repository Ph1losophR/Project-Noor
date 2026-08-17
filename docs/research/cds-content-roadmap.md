# CDS Content Roadmap & Status Register

**Project:** Noor CDS engine (inside Project Amal)
**Purpose:** Track what clinical content exists vs. what is speced-for-but-unbuilt,
and record the remediation state of every research, evidence, terminology,
governance, and provider-policy item on the path to executable content.

**Read this first:** nothing in this file is clinical content, and no rule or
content file exists. There is no `content/`, `src/`, or `tests/` tree. Every
status below is reconciled against `docs/research/diabetes-research.md`,
`docs/research/hypertension-research.md`, and the filesystem; if this register
disagrees with a research file or the filesystem, this register is wrong.

**Sources.** Per SSOT §3.2, the source-label ladder, in order: **local SFDA SPC →
EMA centrally-authorised SmPC → SmPC of an EU national agency that authorised the
product.** Every proposition must be verified at proposition level against its
pinned source; nothing is assumed correct because it came from a family of
sources. Local SFDA SPCs track EMA/ICH — not FDA — so FDA labels and
secondary sources are research input only and can never pin a rule.

**States.** This register tracks remediation work, not schema values. The SSOT
content-schema states (`unretrieved`, `unpopulated`) remain the values content
records must carry; this file does not rename them.

---

## 1. Content coverage table

| Domain | Architecture ready? | Content state (2026-08-17) | Priority |
|---|---|---|---|---|
| Drug contraindication / dose ceilings | Yes — full schema, vendor seam (§3.2, §7.1) | **No rule exists.** Research drafted in `diabetes-research.md` §11 and `hypertension-research.md` §10; thresholds `unpopulated`, labels `unretrieved` | First renal-risk medication-safety workflow (prioritization step 2) — **sources and observables pinned as candidates 2026-08-17** (`label-pin-register.md`, `signal-observable-catalogue.md` §6); verification + approval pending |
| Renal dose adjustment (eGFR vs CrCl) | Yes — `renal_metric` mandatory (§5.2, gate 15) | **No rule exists.** Same state as above | Same |
| Severe hypo/hyperglycemia emergencies | Yes — red-flag libraries named (§11.7) | Libraries drafted (`diabetes-research.md` §4, `hypertension-research.md` §3); source families pinned as candidates 2026-08-17 (`guideline-pin-register.md` §2.1, §3, §1, §4, §5); thresholds still `unpopulated` | **Do next** — named MVP requirement; unblocked at the source level, still needs approval |
| Missed monitoring / follow-up (repeat eGFR, repeat K+ after ACEi/MRA) | Yes — `monitors` + `pending_result` obligation (§7.1, §11.8) | None authored; domains drafted in the research screening sections (§5 / §4); interval sources pinned as candidates (`guideline-pin-register.md` §6) | **Highest untapped value** — no clinic recall system exists in home visits |
| BP target + first-line agent by compelling indication (e.g. CKD → ACEi/ARB) | Yes — `source_family` pinning ready (§10.5) | Research drafted — `hypertension-research.md` §2.8 (unpopulated); NHC/SHA 2023 pinned as the interim default (`guideline-pin-register.md` §1); §2.1 re-based | Pinning + clinical approval pending (approval only) |
| Albuminuria / CKD staging (KDIGO) | Referenced conceptually | KDIGO 2024 pinned as candidate (`label-pin-register.md` §6.1) | Add as thresholds + citation — no copyright blocker |
| Retinal exam reminder | Not mentioned | ADA SOC 2026 §12.3–12.5 pinned as candidate (`guideline-pin-register.md` §2.3) | Cheap — it's a reminder, not a risk model |
| Foot/neuropathy exam reminder | Only a *deferred risk score* exists (IWGDF, §15.2) | ADA SOC 2026 §12.17–12.24 pinned as candidate; IWGDF score stays deferred | The reminder is in scope; the score is deferred (§15.2) |
| SGLT2i / GLP-1 for CKD or HF benefit independent of A1c | Not mentioned | None | High evidence, sits at the diabetes+HTN+CKD intersection |
| Statin / ASCVD risk, aspirin | Deferred (SCORE2, §15.2) | None | Correctly deferred — needs local calibration that does not exist |
| Depression screening (PHQ-9) | Gated — licence + escalation pathway required (§13.2 item 14) | None | Correctly out of scope — see §11 |
| Clinical Signal Catalogue | Architecture ready — registry + `entry_mode` support (§4.2, §6) | Consolidated draft register (`signal-observable-catalogue.md`); candidate concepts in research §1.2; renal-risk workflow observable set pinned as candidate (§6); not approved registry records | **Do next** — every rule reads governed structured signals |

---

## 2. Status legend

| Token | State | Meaning |
|---|---|---|
| `NS` | `not_started` | No verified work product exists |
| `IR` | `in_research` | Source retrieval or reconciliation is underway |
| `BE` | `blocked_external` | A named external decision, source, licence, clinician, or provider is required |
| `P` | `populated` | Complete source-backed draft exists but lacks clinical approval |
| `CA` | `clinician_approved` | Named clinical owner approved it with date and review date |
| `TV` | `technically_validated` | Required schemas, cases, and automated gates pass |
| `A` | `active` | Completed the SSOT release lifecycle; in an immutable active release |
| `OOS` | `out_of_scope` | Deliberately excluded with rationale and approving owner |

For non-clinical items (governance, infrastructure), `A` means complete and in
use; the SSOT release-lifecycle clause applies to clinical content only.
`unretrieved` and `unpopulated` are the SSOT content-schema states and appear
where the schema requires those exact values.

---

## 3. Governance and infrastructure register (workstream 1)

| Item | Status | Evidence / dependency |
|---|---|---|
| Git repository initialized | `A` | Repo exists; commit `1910530`; origin `github.com/ph1losophrr/Project-Noor` (SSOT build step 1) |
| Protected remote workflow — branch protection + required review | `BE` | Requires remote admin; `gh` CLI not installed — configure in the GitHub UI or install `gh` |
| CI posts generated clinician-facing rendering + diff into content PRs | `BE` | Depends on the catalogue compiler (SSOT build steps 4–5), which does not exist yet; configure during software implementation (§7.5) |
| Sample non-clinical PR demonstrating review and merge path | `BE` | Needs branch protection first |
| Clinical content owner appointed | `P` | **Youssef Sabry** (Internal Medicine; SCFHS 100000, as supplied 2026-08-17), effective 2026-08-17. Review cadence pending |
| Technical custodian appointed | `P` | **Youssef Sabry**, effective 2026-08-17 |
| Second clinical approver appointed | `P` | **Dr. Ahmed Sabry** (Cardiologist; SCFHS 111111, as supplied 2026-08-17), effective 2026-08-17; required before any `stop_and_review` rule (§10.3) |
| Terminology owner appointed | `P` | **Youssef Sabry**, effective 2026-08-17; terminology charter (§3.3) is a software-implementation task |
| Provider medical director appointed | `P` | **Youssef Sabry**, effective 2026-08-17 — interim owner appointment; a real provider's medical director supersedes this when a provider signs on (§15.1) |
| Privacy/security owner appointed | `P` | **Youssef Sabry**, effective 2026-08-17: PDPL, hosting, key custody, access, operational safety gates |
| Credential verification and expiry policy | `P` | **Owner-approved 2026-08-17:** expired or changed SCFHS credentials invalidate *future* approvals only; historical approvals and releases stand. Credentials are re-verified at the annual review (SCFHS portal verification remains an external step) |
| Clinical-content and terminology review cadence | `P` | **Owner-approved 2026-08-17:** active clinical content is re-reviewed annually by the clinical content owner, and immediately whenever a pinned source updates (new SPC version or guideline edition) |
| Change rationale + clinical-impact class per release entry | `NS` | Release-manifest design; software implementation |
| Content-governance vs operational role separation (§10.2) | `NS` | Enforced in governed records once repository and schemas exist |

Role appointments are prerequisites to *clinical approval*, not to drafting the
software implementation plan. Do not put placeholder names into approver fields.

---

## 4. Clinical Signal Catalogue groups (workstream 6)

Per the hybrid narrative architecture, the evaluator reads only signals defined
here — never `encounter_narrative`. A consolidated draft register for all six
groups is `signal-observable-catalogue.md` (workstream 6); the research-file
§1.2 inventories remain as the disease-side seeds. **No concept is usable
until the registry assigns a stable terminology mapping, source display, value
constraints, and provenance** (both research §1.2 sections say exactly this).

| Signal group | Status | Reference / note |
|---|---|---|
| Diabetes acute illness | `IR` | `diabetes-research.md` §1.2 + catalogue §4.1 — hypoglycaemia, hyperglycaemia, DKA/HHS prodrome, vomiting, oral-intake failure, dehydration, breathing, mental status, swallowing, seizure, third-party assistance |
| Cardiovascular emergencies | `IR` | `hypertension-research.md` §1.2 + catalogue §4.2 — ACS phenotypes, stroke deficits/onset, hypertensive acute TOD, syncope, pulmonary oedema, aortic features |
| Heart-failure decompensation | `IR` | `hypertension-research.md` §1.2 + catalogue §4.3 — dyspnoea pattern, orthopnoea, oedema, weight change, perfusion findings, clinician-documented HF status |
| Pharmacotherapy effects | `IR` | `diabetes-research.md` §1.2/§11, `hypertension-research.md` §1.2/§10 + catalogue §4.4 — oedema, GI intolerance, injection-site reaction, lipohypertrophy/atrophy, hypoglycaemia symptoms, bleeding, muscle symptoms |
| Medication use | `IR` | Catalogue §4.5 (drafted 2026-08-17): medication confusion, missed dose, duplicate dose, refill gap, administration assistance, caregiver report, discrepancy state — structured assessments, not a proprietary adherence score |
| Physical examination | `IR` | `diabetes-research.md` §1.2, `hypertension-research.md` §1.2 + catalogue §4.6 — foot/wound findings, hydration and haemodynamics, infection and ischaemia, neuropathy, vascular |

---

## 5. Red-flag libraries (workstream 7)

Each library needs: exact structured inputs, activation propositions and
referenced threshold records, symptom-only activation paths, required
conjunctions (glucose alone never diagnoses DKA/HHS; BP alone never defines
hypertensive emergency), repeat/verification behavior that can never delay the
emergency hatch, data-quality behavior, patient modifiers, exclusions,
provider-facing meaning, and the provider emergency pathway (§8).

| Library | Status | Reference / note |
|---|---|---|
| DKA/HHS | `IR` | `diabetes-research.md` §2.1–§2.3, §4 — diagnostic boundaries cited from Umpierrez 2024 at proposition level; source pinned (candidate) in `guideline-pin-register.md` §3; thresholds `unpopulated` pending clinical approval |
| Severe hypoglycaemia | `IR` | `diabetes-research.md` §2.4, §4 — levels drafted against ADA; ADA 2026 §6 levels pinned (candidate) in `guideline-pin-register.md` §2.1 |
| Hypertensive emergency | `IR` | `hypertension-research.md` §2.7, §3 — terminology and triage drafted; NHC/SHA 2023 §3.7 pinned (candidate) as the family (`guideline-pin-register.md` §1); BP + acute TOD conjunction required |
| Acute coronary syndrome | `IR` | `hypertension-research.md` §3.1 — symptom phenotypes drafted; ESC 2023 ACS recognition pinned (candidate) (`guideline-pin-register.md` §4) |
| Stroke | `IR` | `hypertension-research.md` §3.2 — deficits and onset drafted; AHA/ASA F.A.S.T. + 2026 AIS guideline pinned (candidate) (`guideline-pin-register.md` §5) |

---

## 6. Screening and monitoring domains (workstream 8)

Every future `monitors` entry must pin source label or guideline, eligible
population and exclusions, trigger event, required observable and method,
`max_age_days` (may a rule use a result?) vs `monitors` due interval (when is
another result owed?), exceptions, obligation kind and owner-routing, closure
evidence, and clinical approval. A missing result opens or preserves an
obligation and never counts as normal.

| Domain | Status | Reference / note |
|---|---|---|
| Renal and K+ follow-up after RAASi/MRA initiation or dose change | `IR` | `hypertension-research.md` §4, §8 — interval and metric sourcing pending |
| Renal monitoring and sick-day/temporary-hold for diabetes medicines | `IR` | `diabetes-research.md` §5, §11 — e.g. metformin, SGLT2i holds |
| Retinal screening and referral | `IR` | `diabetes-research.md` §3.1, §5; `hypertension-research.md` §4 |
| Foot and neuropathy examination reminders | `IR` | `diabetes-research.md` §3.3–§3.4, §5; `hypertension-research.md` §4 |
| Glycaemic and HbA1c monitoring with context flags | `IR` | `diabetes-research.md` §5 — assay method, anaemia/haemoglobinopathy, CKD context |
| Lipid monitoring (no ASCVD risk model) | `IR` | `hypertension-research.md` §4 — reminder only; SCORE2 stays deferred (§15.2) |
| Orthostatic and BP measurement follow-up | `IR` | `hypertension-research.md` §2.1, §4 — setting, posture, treatment change, orthostatic risk |
| KDIGO albuminuria confirmation and CKD chronicity | `IR` | `diabetes-research.md` §3.2; `hypertension-research.md` §2.4 |
| SGLT2i / GLP-1 cardiorenal propositions | `IR` | `diabetes-research.md` §14.3 — HbA1c-independent, where the selected guideline and label scope support it |

**Interval pins (2026-08-17):** every domain's `monitors` interval source is
now pinned (candidate) in `guideline-pin-register.md` §6 — KDIGO 2024
(RAASi/MRA 2–4-week check, >30% creatinine rule, >5.5 mmol/L K+,
albuminuria/chronicity), EMA metformin referral (GFR ≥annual),
ADA SOC 2026 (HbA1c ≥2×/year, retinal 12.3–12.5, foot/neuropathy 12.17–12.24,
lipids), NHC/SHA 2023 (BP measurement, screening cadence, targets). Clinical
approval and `monitors` schema records still required before any obligation
can fire.

---

## 7. Guideline families (workstream 5)

One source family per tenant profile and clinical domain. Conflicting systems
stay separate and are never averaged or combined. Every proposition needs:
organisation, document, revision/version, exact locator, jurisdiction,
population, exclusions, review date, and inclusive/exclusive convention for
every numeric boundary.

| Family | Status | Reference / note |
|---|---|---|
| NHC-SHA 2023 (SSOT interim default) | `IR` | **Pinned (candidate) 2026-08-17** — `guideline-pin-register.md` §1: classification (>130/80), measurement context (§3.2.1), screening cadence (§3.3/Table 4), first-line selection (§3.6.2/Table 10), resistant HTN (§3.7.1), HF targets (§3.7.5/Table 15), pregnancy (§3.7.8), emergencies (§3.7). `hypertension-research.md` §2.1/§2.8 drafts ESC 2024/ESH 2023 — mismatch resolves in favor of the SSOT unless the project owner approves an SSOT amendment |
| ACC/AHA 2025 | `NS` | Profile-selectable only after independently pinned; not a default |
| ESC 2024 | `IR` | Drafted candidate (`hypertension-research.md` §2.1, §2.8); not a default; ESC 2023 ACS guideline pinned for the ACS library only (`guideline-pin-register.md` §4) |
| ESH 2023 | `IR` | Drafted candidate; support requires an explicit SSOT decision — never an implicit default |
| ADA Standards of Care 2026 | `IR` | **Pinned (candidate) 2026-08-17** — `guideline-pin-register.md` §2: hypoglycaemia levels (§6, dc26-S006), screening (§2, dc26-S002), retinopathy/foot/neuropathy (§12.3–12.24, dc26-S012), HbA1c cadence (§6.2), lipids (§10, dc26-S010) |
| Umpierrez 2024 DKA/HHS consensus | `IR` | **Pinned (candidate) 2026-08-17** — `guideline-pin-register.md` §3: Diabetes Care 2024;47(8):1257–1275, doi 10.2337/dci24-0032, Figure 2A/2B; exact proposition locators complete |
| KDIGO 2024 CKD | `IR` | **Pinned (candidate) 2026-08-17** — `label-pin-register.md` §6.1: G/A categories, chronicity >3 months, RASi/MRA monitoring (PP 3.6.2/3.6.4, Ch. 4), risk-cell frequencies (Ch. 3) |
| Retinopathy screening/referral source | `IR` | **Pinned (candidate) 2026-08-17** — ADA SOC 2026 §12.3–12.5 (`guideline-pin-register.md` §2.3); Saudi reference recorded as fallback pending domain-profile selection |
| Foot/wound classification (Wagner, UT + current infection/ischaemia guidance) | `IR` | `diabetes-research.md` §3.4, §17 — no approved classification-family pin yet; IWGDF unpinned; stays `IR` |
| Stroke recognition source | `IR` | **Pinned (candidate) 2026-08-17** — AHA/ASA F.A.S.T. warning signs + 2026 AIS guideline (STR.0000000000000513) (`guideline-pin-register.md` §5) |
| Current Saudi guidance (diabetes, CV prevention, home healthcare) | `IR` | Seek first where the selected domain profile requires it; record a fallback rather than silently substituting an international family |

---

## 8. Provider policies (tenant profile; workstreams 7 and 10)

These belong in a tenant profile, not in engine code or general research. None
can be inferred from public research. Each requires the provider medical
director's documented approval and a rehearsed pathway.

| Policy | Status | Note |
|---|---|---|
| Local emergency destination and contact pathway | `BE` | Named provider + medical director approval |
| Responsible role or person by operating period | `BE` | Named provider |
| Escalation acknowledgement deadline | `BE` | Named provider |
| Downtime and failed-contact behavior | `BE` | Named provider |
| Documentation, rehearsal, and review cadence | `BE` | Named provider |
| Supervision and prescribing-authority policy | `BE` | SSOT §13.2 item 7 |
| Clinician-approved medication-scope disclosure | `P` | SSOT §3.2 amended to the 45-ingredient set 2026-08-17 (v1.1.0); disclosure wording still needs the clinical content owner's sign-off |
| Per-tenant formulary (`content/formulary/*.yaml`) | `NS` | §3.2: ingredient, formulation, strength, SFDA registration and SPC version, availability, coverage, substitution policy, stock date, source |

---

## 9. Medication catalogue — 45 distinct ingredients

The original roadmap listed **49 rows**; four were duplicate placements, so the
catalogue holds **45 distinct identities: 11 diabetes and 34 cardiovascular**
(§10). Every ingredient below is listed in the Saudi Essential Medicines List
2023 — verified against `saudi-essential-medicines-list-2023.md` (the only
primary source in the repository; it is authoritative for exactly two claims:
listing, and strengths/dose forms). SFDA registration is the project owner's
2026-08-16 assertion recorded in both research files; registration numbers
remain unpinned while the SDI e-service is unreachable.

Per-ingredient fields (replacing the old binary checkboxes):

| Field | What it tracks |
|---|---|
| `identity` | `ingredient_id` + ATC class established |
| `seml` | SEML 2023 listing + strengths verified against the converted primary source |
| `source_label` | Pinned label with all four required fields (authority, document, revision date, locator) + auditable fallback record |
| `renal` | Renal dosing guidance and metric (eGFR vs CrCl — one metric only) |
| `hepatic` | Hepatic guidance; never transaminase-based, never Child-Pugh from transaminases |
| `interactions` | Interactions relevant to a polypharmacy, elderly, home-care population |
| `monitoring` | Monitoring interval after initiation/dose change, with label version |
| `pregnancy` / `breast_feeding` / `fertility` | Three distinct propositions, each populated or explicitly not stated |
| `achievability` | Strength achievability: `strength_achievable` / `achievable_by_division` / `unachievable` with supporting source facts |
| `complications_reconciled` | Complication profile reconciled against the pinned label |
| `clinical_approval` | Named clinical owner approval with date and review date |

**All cells are uniform as of 2026-08-17** because every ingredient shares the
same underlying state: identity and SEML listing are established; labels are all
`unretrieved` (SFDA rung `BE` — SDI e-service unreachable since 2026-08-12; EMA
and EU-national rungs attempted 2026-08-17 for the renal-risk set — metformin,
lisinopril, captopril, enalapril, losartan, spironolactone — with candidate
retrieval records in `label-pin-register.md` awaiting second-researcher
verification before any `source_label` flips to `pinned`); every
label-dependent field is a research draft from FDA/secondary sources pending
the label pin; and nothing has clinical approval. Do not copy a cell value —
reconcile against the research files, which are the source of truth for
per-ingredient content.

### 9.1 Diabetes — 11 ingredients

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Metformin | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Insulin aspart | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Insulin lispro | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Insulin glargine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Isophane insulin (NPH) | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Gliclazide | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Empagliflozin | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Sitagliptin | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Pioglitazone | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Liraglutide | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Glucagon | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

### 9.2 Cardiovascular — 34 ingredients

**Anti-anginal drugs**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Metoprolol tartrate | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Carvedilol | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Verapamil hydrochloride | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Nifedipine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Amlodipine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Glyceryl trinitrate | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Isosorbide dinitrate | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

**Anti-arrhythmic drugs**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Adenosine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Amiodarone | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Digoxin | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Lidocaine hydrochloride | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

**Anti-hypertensives**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Propranolol | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Hydralazine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Hydrochlorothiazide† | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Lisinopril | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Captopril | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Losartan (alias: losartan potassium‡) | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Methyldopa | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

**Drugs used in heart failure**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Metoprolol succinate | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Enalapril maleate | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Furosemide† | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Spironolactone† | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

**Vasopressors and inotropes**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Epinephrine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Norepinephrine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Dobutamine | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Milrinone | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Vasopressin | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Dopamine hydrochloride | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

**Anti-thrombotic agents**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Acetylsalicylic acid | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Clopidogrel | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Ticagrelor | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Tirofiban | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |
| Alteplase | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

**Lipid-lowering agents**

| Ingredient | identity | seml | source_label | renal | hepatic | interactions | monitoring | pregnancy | breast_feeding | fertility | achievability | complications | clinical_approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Atorvastatin | `P` | `P` | `unretrieved` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `IR` | `NS` |

† Also listed under **Diuretics** in the original roadmap — one identity, counted
once (§10).
‡ The original roadmap also listed **losartan potassium** under *Drugs used in
heart failure* — one identity, counted once (§10).

### 9.3 SEML formulation ambiguities (workstream 3) — resolved 2026-08-17

The converted SEML Markdown dropped drug-name cells on rows where the original
table merges a drug across multiple formulation rows. The project owner
confirmed all four affected Noor-catalogue rows against the original 2023 PDF on
2026-08-17; the drug-name cells are restored in
`saudi-essential-medicines-list-2023.md` with an annotation.

| Item | Resolution (owner-confirmed 2026-08-17) | Consequence |
|---|---|---|
| Insulin lispro | `Suspension for injection: 100 IU/ml` **and** `200 IU/ml` | Humalog's EMA SmPC covers both concentrations — one pin suffices; units-only rule stands (EMA/134145/2015) |
| Gliclazide | No release profile stated — `Tablet: 30 mg, 60 mg, 80 mg` | IR and MR remain distinct pins (`label-pin-register.md` §4); emitting an MR dose needs `drug_scope_level: product` |
| Verapamil | `Tablet: 40 mg, 80 mg` + `Solution for injection: 2.5 mg/ml` | Tablet strengths confirmed for the §12.1 and §12.2 listings |
| Nifedipine | `Tablet: 30 mg` (ER) + `Capsule: 10 mg` (IR) | Two distinct formulation pins; a 50% ER reduction target would be 15 mg — no listed strength delivers it |

Tablet score, divisibility, and modified-release restrictions come only from an
authoritative label or product record — a mathematically divisible dose is not
automatically licensed to divide. Acute parenteral pump-rate and
diluent-concentration achievability routes to a later acute-care model (§11).

---

## 10. Duplicate roadmap placements and aliases

The original roadmap's 49 rows contained four duplicate identities. All four are
recorded here so no placement can be silently dropped or double-counted:

| Identity | Original placements | Resolution |
|---|---|---|
| Losartan / losartan potassium | Anti-hypertensives; Drugs used in heart failure | One identity: `losartan`. Alias recorded in §9.2 |
| Furosemide | Drugs used in heart failure; Diuretics | One identity, listed under heart failure (§9.2) |
| Spironolactone | Drugs used in heart failure; Diuretics | One identity, listed under heart failure (§9.2) |
| Hydrochlorothiazide | Anti-hypertensives; Diuretics | One identity, listed under anti-hypertensives (§9.2) |

Metoprolol tartrate and metoprolol succinate are **two distinct identities**
(different salts, different sections) and are both counted.

**Count check:** 49 original rows − 4 duplicate identities = **45 distinct
ingredient_id candidates** = 11 diabetes + 34 cardiovascular.

---

## 11. Deferred work — `out_of_scope` with an SSOT reference

Preserved as deliberate exclusions, not as unchecked or forgotten items:

| Item | SSOT reference | Rationale |
|---|---|---|
| Depression screening (PHQ-9) | §13.2 item 14 | Licence terms and the item-9 escalation pathway are gated; outside the current MVP |
| Risk models — KFRE, FIB-4, IWGDF foot category, SCORE2/SCORE2-OP | §15.2 | Deferred: needs evidence or local validation; each emits a number that would need "not locally recalibrated" labelling |
| ASCVD risk-score driven statin rules | §15.2 | Needs local calibration that does not exist; lipid *monitoring reminders* remain in scope (§6) |
| Acute parenteral pump-rate / diluent-concentration achievability | Remediation plan workstream 3 | Routes to a later acute-care model; never forced into tablet-strength logic |
| Emergency destination / referral / escalation content | §11.7 + tenant profile | `out_of_scope` until provider policy exists (§8); never inferred from public research |

---

## 12. How to use this file

- **A status is evidence, not intent.** A state changes only with a verifiable
  work product, reconciled against the research files and the filesystem. A
  status change travels in a pull request with the evidence attached.
- **Nothing here is executable content.** Reaching `populated`/`CA` on a field
  means the draft and approval exist — not that a rule exists.
- **Test-first, one rule at a time.** Write the `.cases.yaml` rows first
  (at/below/above every threshold, plus the §12 boundary, degradation, quality,
  context, and pairwise requirements), watch them fail, then author the
  smallest rule that satisfies the approved proposition. Don't batch-research a
  whole tier before writing any rules — you'll lose what makes the catalogue
  trustworthy: every rule was checked against real cases before it shipped.
- **A rule begins only after its own entry gates close** — approved registry
  records for its inputs, pinned sources, resolved identity/formulation/scope,
  a selected source family, provider policy where the action depends on local
  operations, and named clinical approval (second approver for
  `stop_and_review`).

## 13. Self-verification (workstream 2 exit criteria)

Checked 2026-08-17:

- Exactly **45 unique `ingredient_id` candidates**: 11 diabetes (§9.1) + 34
  cardiovascular (§9.2).
- Losartan / losartan potassium holds **one** identity (§10).
- Furosemide, spironolactone, and hydrochlorothiazide are **not counted twice**
  for their two therapeutic-section placements (§10).
- Every status above is reconciled against `diabetes-research.md`,
  `hypertension-research.md`, and the filesystem (no `content/`, `src/`, or
  `tests/` tree exists — verified).
- No stale claims remain that rules or content files exist; the prior "1 rule
  (metformin/eGFR)" claim is removed, and this register states the true
  content state in §1.