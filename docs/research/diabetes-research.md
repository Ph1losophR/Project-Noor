> Consolidated from `diabetes-drug-research.md`, `diabetes-drug-complications.md`, and
> the diabetes portions of `diabetes-hypertension-complications.md` (all three deleted on
> consolidation, 2026-08-16). Based on the research requirements of
> `cds-content-roadmap.md` — read the referenced file first.

# Diabetes Research — Clinical and Pharmacotherapy Reference for Project Noor

This file is the single research source for diabetes within the Noor CDS engine. It
covers the disease itself (acute and chronic complications, red-flag libraries,
screening, coding) and the diabetes pharmacotherapy catalogue (dosing, interactions,
monitoring, pregnancy propositions, strength achievability, per-ingredient
complication profiles). The hypertension counterpart is `hypertension-research.md`.

## Implementation status — read before authoring any rule

Nothing in this file is authorable as-is. Three states are tracked per claim, and they
are different things:

| | Status |
|---|---|
| **SEML 2023 listing and strengths** | ✅ **Verified** against `saudi-essential-medicines-list-2023.md` §15.1, the converted primary source in this repository. All 11 ingredients are listed. Strengths are reproduced in the matrix below. |
| **Source label pin** | ❌ **`unretrieved` for every ingredient.** No local SFDA SPC could be retrieved — the SDI e-service is unreachable as of 2026-08-12 — and no EMA or EU national-agency SmPC has yet been pinned with a document name, revision date, and locator. |
| **Disease-complication claims** | ⚠️ **Source-populated, not clinician-approved.** The DKA/HHS diagnostic boundaries (Umpierrez 2024) are cited at proposition level but no threshold record has passed Noor clinical approval. Everything else in Part A is a research note pending source pinning per §15 below. |
| **Drug-complication profiles (Part B §11)** | ⚠️ **Research draft, FDA-sourced.** The profiles were compiled from FDA labels/DailyMed, StatPearls, and drug-safety-agency alerts because they surfaced most reliably in search. Local SFDA SPCs track EMA/ICH, **not** FDA — cross-check every complication or contraindication against the EMA SmPC or local SPC before it becomes rule content. FDA and EMA agree on the substance of almost all of these (especially boxed warnings), but exact wording, thresholds, and which warnings are boxed vs. standard precaution can differ. |

Per SSOT §3.2 (source-label ladder) and §7.3, **every threshold below is
`status: unpopulated` and no rule referencing one will merge** (CI gate 2). The
clinical content is a research draft awaiting a label pin, not a catalogue.

The pin each row owes, per SSOT §3.2:

```yaml
source_label:
  pinned: {authority: ..., document: ..., revision_date: ..., locator: ...}
  fallback_from: {tried: [sfda.sdi], reason: "SDI e-service unreachable 2026-08-12"}
  status: unretrieved
```

`sfda_registration` is **omitted deliberately**, not missing. It is a
product-level field (SSOT §3.2 medication identity) and is null for the
ingredient-level facts every rule here will be written from
(`drug_scope_level: ingredient`). A prior revision of the research carried a
registration-number column; it was deleted because its values were unverifiable
and internally contradictory — one number appeared under two different
ingredients in three separate cases, and the column also contained trade names
and a date. SDI being unreachable blocks no ingredient-level rule.

**Project-owner confirmation (2026-08-16): all 45 catalogue ingredients (11
diabetes, 34 cardiovascular) are SFDA-registered.** Recorded here as an
assertion by the project owner, not a citation — it does not fill the
registration numbers (which remain unpinned until the SDI e-service is
reachable) and does not change any label status above. SEML 2023 listing
remains the verified proxy.

---

# Part A — Clinical Reference: Diabetes Complications

## 1. Noor Content Contract

Every future rule derived from this reference must be split into four governed
artefacts:

| Artefact | Responsibility | Required content |
|---|---|---|
| `content/observables/registry.yaml` | What can enter the snapshot | LOINC/SNOMED concept, UCUM unit, value type, accepted methods, context, provenance, quality behavior |
| `content/thresholds/*.yaml` | Numeric or categorical boundary | Value, unit, operator, source family, complete citation, approval, review date, exclusions |
| `content/red_flags/*.yaml` | Emergency and urgent pathways | Activation criteria, repeat criteria, exclusions, context, data-quality behavior, owner and approvers |
| `content/rules/<id>.yaml` and `*.cases.yaml` | Executable evaluation | Scope, requirements, severity, meaning, action, uncertainty, monitors, boundary and pairwise cases |

Rules may read structured observations only. They may not read the encounter
narrative or infer a diagnosis from free text. A patient-reported symptom and a
staff-observed sign must remain distinguishable through `entry_mode` and
`informant`. A missing or unusable requirement produces `indeterminate`; it
never silently becomes normal, absent, or safe.

### 1.1 Common red-flag contract

Each red-flag library must separate these outcomes:

| Outcome | Meaning | Typical Noor behavior |
|---|---|---|
| Emergency activation | A clinical picture where delay may cause serious harm | Open the emergency hatch; provider pathway supplies local response |
| Immediate clinical review | Concerning finding without enough evidence for emergency activation | `interruptive_review` or provider-defined same-day lane |
| Repeat or verification | Measurement may be erroneous, incomplete, or not yet actionable | Repeat through `canon`; never delay an emergency hatch |
| Routine monitoring | Chronic risk or overdue surveillance | `passive_task`, `monitors`, or `pending_result` obligation |
| Indeterminate | Required evidence is absent, stale, contradictory, or unusable | Surface the missing requirement and open durable work where applicable |

Every library must declare:

- The structured inputs it uses and their units or permitted values.
- Required source status, quality state, measurement context, and maximum age.
- Patient-context modifiers, including pregnancy where relevant, CKD, age,
  frailty, fasting, medication exposure, and prior disease.
- Explicit exclusions and alternative explanations.
- Which symptoms activate the hatch independently of a numeric threshold.
- Which numeric values prompt repeat or review rather than emergency activation.
- The provider-facing action, without inventing a Saudi emergency protocol.
- At, just-below, just-above, missing-data, poor-quality, and pairwise cases.

### 1.2 Clinical signal inventory — diabetes-relevant

The following are candidate registry concepts, not yet approved terminology
entries. Each needs a terminology owner and source mapping before use. Signals
shared with `hypertension-research.md` are duplicated deliberately so each file
stands alone.

| Candidate identifier | Signal type | Values or data | Intended use |
|---|---|---|---|
| `symptom_polyuria` | Patient-reported symptom | Present, absent, unknown | Hyperglycaemic illness support |
| `symptom_polydipsia` | Patient-reported symptom | Present, absent, unknown | Hyperglycaemic illness support |
| `symptom_nausea_vomiting` | Patient-reported symptom | Present, absent, unknown | DKA/HHS support; emergency context |
| `symptom_abdominal_pain` | Patient-reported symptom | Present, absent, unknown | DKA support |
| `symptom_dyspnoea` | Patient-reported symptom | Present, absent, unknown | Kussmaul breathing, HF, ACS alternative |
| `finding_deep_rapid_breathing` | Staff-observed sign | Present, absent, unknown | DKA emergency context |
| `finding_altered_mental_status` | Staff-observed sign | Present, absent, unknown | DKA/HHS/hypoglycaemia/stroke |
| `finding_seizure` | Staff-observed sign | Present, absent, unknown | Severe hypoglycaemia or stroke |
| `finding_unable_to_swallow` | Staff-observed sign | Present, absent, unknown | Severe hypoglycaemia pathway |
| `finding_cool_pale_sweaty_skin` | Staff-observed sign | Present, absent, unknown | Hypoglycaemia support |
| `finding_pedal_oedema` | Staff-observed sign | Laterality and severity | HF/renal monitoring |
| `finding_orthostatic_symptoms` | Patient-reported symptom | Present, absent, unknown | Orthostatic BP interpretation; autonomic dysfunction |
| `finding_foot_ulcer` | Staff-observed sign | Depth, infection, ischaemia | Foot-care pathway |

No rule may use these names until the registry assigns a stable terminology
mapping, source display, value constraints, and provenance requirements.

---

## 2. Acute Metabolic Complications of Diabetes

### 2.1 Diabetic ketoacidosis (DKA)

The 2024 consensus diagnosis uses three components:

| Component | Clinical proposition | Noor implementation requirement |
|---|---|---|
| Diabetes or hyperglycaemia | Glucose at or above the consensus threshold, or known diabetes; euglycaemic DKA remains possible in known diabetes | Do not require high glucose when known diabetes and the other components are present; capture diabetes status and SGLT2 exposure |
| Ketosis | Beta-hydroxybutyrate at or above the consensus threshold, or urine ketones at or above the stated category | Prefer serum beta-hydroxybutyrate when available; preserve test type and timing; do not treat missing ketones as negative |
| Acidosis | pH below the consensus threshold and/or bicarbonate below the consensus threshold | Preserve venous/arterial source and assay; missing acidosis data is `indeterminate`, not normal |

**Source-verified diagnostic boundaries:** glucose >=200 mg/dL or known
diabetes, beta-hydroxybutyrate >=3.0 mmol/L or urine ketones >=2+, pH <7.30
and/or bicarbonate <18 mmol/L. Source: Umpierrez et al., *Hyperglycemic Crises
in Adults With Diabetes: A Consensus Report*, Diabetes Care 2024,
doi:10.2337/dci24-0032, Figure 2A and section "Diagnostic Criteria for DKA."
These boundaries are source-populated but remain non-authorable until the
threshold records receive Noor clinical approval.

**Important boundary conditions:**

- Euglycaemic DKA may occur with SGLT2 inhibitors, fasting, pregnancy, reduced
  carbohydrate intake, or acute illness. A glucose-only exclusion is unsafe.
- Mixed DKA-HHS requires both syndromes to be represented; it is not a separate
  biochemical rule that replaces the two component assessments.
- The removed anion-gap criterion must not be reintroduced as a required
  diagnostic gate. Anion gap may be recorded as supportive context if sourced.
- Mild or moderate DKA management location is a treatment-pathway decision, not
  an automatic home-health recommendation. Noor must route to the provider's
  emergency pathway and must not imply that home management is appropriate.
- A `needs_repeat_or_verification` glucose or ketone result may prompt repeat,
  but repeat must never delay emergency activation when the clinical picture is
  concerning.

**Candidate DKA emergency signals:** altered mental status, deep/rapid breathing,
shock or severe dehydration signs, persistent vomiting, inability to maintain
oral intake, severe abdominal pain with metabolic illness, or clinician concern.
These signals require individually sourced definitions and must not be treated
as a closed list.

### 2.2 Hyperosmolar hyperglycaemic state (HHS)

The 2024 consensus framework describes HHS using severe hyperglycaemia,
hyperosmolality, minimal or absent ketosis, and no significant acidosis. The
following diagnostic boundaries are verified against the consensus source but
still require Noor clinical approval before authoring:

- Glucose >=600 mg/dL.
- Effective serum osmolality >300 mOsm/kg or total serum osmolality >320
  mOsm/kg, according to the specified criterion.
- Beta-hydroxybutyrate <3.0 mmol/L or urine ketones below the DKA criterion.
- pH >=7.30 and bicarbonate >=15 mmol/L for the non-DKA HHS phenotype.

Source: Umpierrez et al., *Hyperglycemic Crises in Adults With Diabetes: A
Consensus Report*, Diabetes Care 2024, doi:10.2337/dci24-0032, Figure 2B and
section "Diagnostic Criteria for HHS." All four HHS components must be present.

The rule must name whether it uses measured total osmolality or a calculated
effective osmolality. If calculated, the formula, sodium unit, glucose unit,
rounding rule, and missing-sodium behavior must be declared. Effective
osmolality and total osmolality are not interchangeable observables.

Candidate calculated observables must be separately governed. A commonly used
effective-osmolality expression is `2 x sodium + glucose/18` when sodium is in
mmol/L and glucose is in mg/dL; total osmolality adds a urea/BUN term according
to the source's stated convention. This formula is included to identify the
required inputs, not to approve it: the content owner must pin the exact source,
analyte convention, unit conversion, precision, and rounding rule before use.

Altered mental status, severe dehydration, hypotension, or inability to drink
are clinical escalation signals. A high glucose value alone is not sufficient to
label HHS or open an emergency pathway.

### 2.3 Mixed DKA-HHS

Mixed disease is present when the patient satisfies the sourced DKA and HHS
propositions concurrently. It should trigger the highest provider-defined acute
pathway and prompt evaluation of renal function, potassium, sodium, osmolality,
and acid-base status. The cited retrospective cohort in the earlier draft is
not sufficient to define a Noor severity threshold; outcome percentages are
context, not decision rules.

### 2.4 Hypoglycaemia

Hypoglycaemia must be represented by both biochemical level and clinical need:

| ADA level | Definition | Rule meaning |
|---|---|---|
| Level 1 | Glucose <70 and >=54 mg/dL | Alert or treatment-support signal, not automatically severe |
| Level 2 | Glucose <54 mg/dL | Clinically significant low glucose; urgent review and recurrence assessment |
| Level 3 | Severe event requiring assistance of another person, regardless of glucose value | Emergency-capable clinical event; do not require a numeric value |

The exact ADA source locator must be pinned. Candidate Level 3 inputs include
altered consciousness, seizure, inability to swallow, or need for third-party
assistance. The pathway must distinguish an alert patient who can safely take
oral treatment from a patient who cannot swallow or has impaired consciousness.
Noor must not prescribe a local rescue medication protocol until the provider
supplies and approves it.

Rules must capture insulin or sulfonylurea exposure, recent food intake or
fasting, renal impairment, alcohol or acute illness context, recurrence, and
whether a third party was required. A low reading with poor measurement quality
requires verification unless the clinical picture itself warrants emergency
activation.

---

## 3. Chronic Diabetes Complications

### 3.1 Diabetic retinopathy and diabetic macular oedema

The International Clinical Diabetic Retinopathy (ICDR) scale is a candidate
severity vocabulary. It must be stored as a clinician- or image-reviewer-
documented observation with the examination method, image quality, laterality,
date, and reviewer provenance. Noor must not infer an ICDR category from a
screening reminder or an unreviewed image.

| ICDR category | Core finding | Candidate follow-up concept |
|---|---|---|
| No apparent DR | No visible retinopathy | Routine screening interval from the selected source |
| Mild NPDR | Microaneurysms only | More frequent than no-DR screening where the source specifies |
| Moderate NPDR | More than microaneurysms, less than severe | Source-specific interval |
| Severe NPDR | 4-2-1 pattern or equivalent documented criteria | Prompt specialist review |
| PDR | Neovascularisation or vitreous/preretinal haemorrhage | Prompt ophthalmology pathway |

DME is independent of NPDR stage and must include presence/absence and whether
it is centre-involving. It is a separate referral signal. Screening intervals
must be stratified by diabetes type, duration, pregnancy, prior treatment,
imageability, and documented retinopathy. The earlier draft's high-resource
interval table is not a universal Saudi schedule and must not be hard-coded as
one.

### 3.2 Diabetic kidney disease and CKD

Use KDIGO Cause-GFR-Albuminuria (CGA) terminology. GFR categories are:

| Category | eGFR mL/min/1.73 m2 |
|---|---:|
| G1 | >=90 |
| G2 | 60-89 |
| G3a | 45-59 |
| G3b | 30-44 |
| G4 | 15-29 |
| G5 | <15 |

Albuminuria categories use spot urine ACR:

| Category | ACR |
|---|---|
| A1 | <30 mg/g (<3 mg/mmol) |
| A2 | 30-300 mg/g (3-30 mg/mmol) |
| A3 | >300 mg/g (>30 mg/mmol) |

The unit, conversion, specimen context, chronicity evidence, and laboratory
source are mandatory. A single abnormal eGFR or ACR does not establish CKD
chronicity. The engine must keep reported eGFR separate from Noor-derived eGFR,
and eGFR separate from creatinine clearance. A renal-dose rule uses the metric
specified by its source label; it must never substitute one for the other.

KDIGO risk color is a communication aid, not a diagnosis or an automatic
severity ladder. If a risk category is implemented, the source version and
copyright-safe representation must be pinned; the protected heat-map artwork
must not be copied into the repository or product.

### 3.3 Diabetic neuropathy and autonomic dysfunction

Candidate domains include distal symmetric sensorimotor polyneuropathy, cardiac
autonomic neuropathy, gastroparesis, neurogenic bladder, sudomotor dysfunction,
sexual dysfunction, focal neuropathy, and diabetic amyotrophy.

The engine should use documented structured findings such as sensory loss,
monofilament result, vibration result, orthostatic symptoms and measurements,
resting tachycardia, and falls. The Dyck N0-N3 terminology may be stored when a
qualified clinician documents it, but Noor must not infer a Dyck stage from one
home screening maneuver.

### 3.4 Diabetic foot disease

The Wagner classification describes ulcer depth and gangrene but does not fully
represent infection or ischaemia. If used, it must be paired with separate
structured fields for infection, perfusion/ischaemia, neuropathy, location,
size, depth, laterality, and osteomyelitis evidence. The University of Texas
system may be used as an orthogonal wound classification only after a clinical
owner chooses one canonical representation and defines conflict handling.

Wagner grades are candidate observations, not automatic emergency diagnoses.
Any emergency pathway must separately define severe infection, spreading
cellulitis, systemic illness, critical ischaemia, gangrene, and suspected
osteomyelitis with source-backed criteria.

### 3.5 Diabetes-related macrovascular disease

Relevant domains are coronary artery disease/ACS, cerebrovascular disease,
peripheral artery disease, heart failure, and atrial fibrillation. A history of
these conditions should be represented as clinician-documented conditions with
status and onset, not inferred from a risk factor or a single symptom.

Risk associations and odds ratios are background evidence. They are not
patient-specific risk multipliers and must not be converted into a Noor risk
score; risk models are deferred by the SSOT.

Peripheral artery disease content should capture claudication or rest-pain
symptoms, pulses, skin and temperature changes, prior revascularisation or
amputation, ulcer location, and a clinician-documented diagnostic test. An
abnormal pulse examination alone should route to assessment rather than produce
a definitive PAD diagnosis.

---

## 4. Red-Flag Libraries — DKA/HHS and Severe Hypoglycaemia

SSOT §11.7 requires five governed red-flag libraries. **This file owns two of
them; the other three (hypertensive emergency, ACS, stroke) are tracked in
`hypertension-research.md`.** Red-flag thresholds are never written from memory,
and the values below are therefore recorded as **`status: unpopulated`** with
the action they will trigger, not as thresholds. Each needs an organisation,
document, version, and locator before CI gate 2 will pass it, and each needs the
three `.cases.yaml` rows (at / just below / just above) from SSOT §12.3 written
*before* the rule.

**Source pins (2026-08-17):** the Umpierrez 2024 DKA/HHS boundaries (§2.1–§2.3)
and the ADA 2026 hypoglycaemia levels (§2.4) are pinned as candidates with
exact locators in `guideline-pin-register.md` §3 and §2.1. The values below
stay `unpopulated` until the threshold records pass clinical approval.

| Library | Emergency activation must consider | Repeat/review must remain separate |
|---|---|---|
| DKA/HHS | Metabolic criteria plus dehydration, vomiting, altered mental status, breathing, haemodynamic status, or clinician concern | Single extreme glucose, unconfirmed ketone, missing acid-base data |
| Severe hypoglycaemia | Level 3 assistance, seizure, unconsciousness, inability to swallow, or provider-defined severe clinical picture | Level 1/2 low glucose in an alert patient; suspect device error |

| Red flag | Observable | Value | Status | Action once cited |
|---|---|---|---|---|
| Severe hypoglycaemia | blood glucose | ⛔ `unpopulated` — a prior revision stated `< 54 mg/dL (3.0 mmol/L)` with no source | `unpopulated` | Glucagon 1 mg IM (SEML §15.1.2) or IV dextrose; emergency escalation |
| DKA / HHS | blood glucose **+** ketones or acidosis | ⛔ `unpopulated` — a prior revision stated `> 300 mg/dL (16.7 mmol/L)` with no source | `unpopulated` | DKA/HHS protocol; suspend SGLT2 inhibitor; IV fluid resuscitation |

Two structural notes that survive independent of the numbers:

- The DKA/HHS flag is a **conjunction**, not a glucose threshold. Glucose alone must
  not raise it — euglycaemic DKA on an SGLT2 inhibitor is precisely the case a
  glucose-only trigger misses, and it is the case most relevant to this catalogue.
- Both flags carry units in **mg/dL and mmol/L**. Saudi laboratories report both;
  a threshold stored in one unit without the other is a conversion bug waiting for a
  night shift.

The DKA diagnostic components and the ADA hypoglycaemia levels in §2 supply the
structured inputs these libraries evaluate. Red-flag data-quality behavior (the
`canon` / `clinically_exceptional_accepted` flow) is in §3.3 of
`hypertension-research.md` and applies identically here.

---

## 5. Screening and Monitoring

The following are domains for monitoring content, not universal fixed schedules.
Each future `monitors` entry must pin the source label or guideline, eligible
population, maximum age for using a result, due interval, exceptions, and
obligation behavior. BP monitoring is tracked in `hypertension-research.md`.

| Domain | Candidate observation | Required stratification |
|---|---|---|
| Retinal | Dilated exam or validated fundus image | Diabetes type/duration, DR/DME stage, pregnancy, treatment |
| Renal | eGFR and urine ACR | Diabetes, CKD chronicity, G/A risk, progression, treatment decision |
| Neuropathy | Monofilament, vibration, symptoms, falls | Diabetes type/duration, prior ulcer, sensory loss, setting |
| Foot | Comprehensive exam and every-visit visual check where indicated | Ulcer, amputation, deformity, neuropathy, infection, ischaemia |
| Autonomic | Orthostatic vitals and symptoms | Type 1 duration, type 2 diagnosis, symptoms, medication changes |
| Glycaemia | HbA1c, glucose, or approved alternative | Assay method, anaemia/haemoglobinopathy, CKD, treatment change |
| Lipids | Lipid panel | Primary/secondary prevention status and treatment change |

Intervals must not be copied from the earlier high-resource table as if they
were Saudi policy. They require population-specific source verification and
provider review. A monitoring interval is not the same as a result freshness
window: `max_age_days` answers whether a rule may use a result; `monitors` answers
when another result is due. An overdue result creates the appropriate durable
obligation and never closes merely because the result is missing.

Ramadan or other dated assessments belong in Noor's calendar content, with
tenant-specific dates and a source-backed lead time. They are not inferred from
an observation and must not be hard-coded in this reference as a universal
date.

---

## 6. Terminology and Coding Boundary

Noor uses LOINC and UCUM for observations, SNOMED CT for clinical meaning, and
ICD-10-AM only at the NPHIES/billing boundary as specified by the SSOT. The
ICD-10-CM examples below are orientation only and must not be treated as Saudi
coding instructions.

### 6.1 Coding cautions — diabetes

- Diabetes and hypertension are generally coded separately. Do not infer a
  causal diabetes-to-hypertension relationship from co-occurrence.
- Diabetic CKD, hypertensive CKD, and combined hypertensive heart-and-CKD coding
  are not interchangeable. They may require diabetes, hypertension/combination,
  and N18 stage codes depending on the documented diagnoses.
- `E11.22` does not by itself represent every patient who has diabetes, CKD, and
  hypertension. The record must preserve documented etiologies and stage.
- `N18.1` through `N18.5` represent CKD stages 1 through 5; `N18.6` is ESRD.
- Retinopathy, neuropathy, foot disease, and PAD need mapped
  clinical concepts, not only broad ICD code ranges.
- A coding system is not a clinical severity system. Codes must never be used
  as a substitute for the red-flag criteria or clinical documentation.

### 6.2 Required mapping record

Every mapped concept must retain the source display, terminology release,
mapping method, confidence, and mapped code. Ambiguous or unmapped concepts are
visible workflow states and cannot silently enter the engine.

---

# Part B — Pharmacotherapy: Diabetes

## 7. Regulatory and Clinical Architecture Overview

Clinical Decision Support (CDS) engines require rigid evidence bases and precise regulatory alignment to deliver actionable, safety-critical alerts at the point of care. In the context of diabetes mellitus management within Saudi Arabia's healthcare ecosystem, local Summary of Product Characteristics (SPCs) published by the Saudi Food and Drug Authority (SFDA) serve as the primary legal and clinical benchmarks. These local SPCs are harmonized with international technical standards established by the European Medicines Agency (EMA) and the International Council for Harmonisation (ICH).

Implementing digital CDS rules—such as those within the Noor CDS engine—demands that clinical parameters, dose ceilings, contraindications, and monitoring obligations are derived strictly from authoritative regulatory documentation rather than clinical memory or unvalidated secondary literature. Every pharmacological agent listed on the Saudi Essential Medicines List (SEML) 2023 possesses structural Anatomical Therapeutic Chemical (ATC) classifications and defined physiological thresholds. Synthesizing these regulatory parameters enables CDS architecture to construct execution logic that mitigates severe adverse events, including drug-induced lactic acidosis, severe hypoglycemia, acute renal failure, and heart failure decompensation in vulnerable patient cohorts.

## 8. Quantitative Renal and Hepatic Dosing Principles

A critical requirement in CDS rule architecture is the explicit differentiation between estimated Glomerular Filtration Rate (eGFR) and Creatinine Clearance (CrCl) calculated via the Cockcroft-Gault equation. Conflating these two metrics introduces significant clinical risk, particularly in elderly, sarcopenic, or home-care populations. Sarcopenia decreases serum creatinine generation, which artificially inflates Cockcroft-Gault CrCl calculations if body weight is not carefully corrected. Modern EMA and SFDA product labels for oral antidiabetic agents, including biguanides, SGLT2 inhibitors, and DPP-4 inhibitors, express renal safety thresholds exclusively in eGFR (mL/min/1.73 m²).

**Noor's eGFR equation is not chosen here.** SSOT §5.2 pins the **2021 CKD-EPI
creatinine equation without race** for any Noor-derived eGFR, stores the reporting
laboratory's `reported_egfr` and `reported_equation` separately, and never
recomputes a historical value under a different equation. A prior revision of this
research printed an MDRD formula under a "CKD-EPI or MDRD" heading, as though the two
were interchangeable; they are not, and neither is the one this project uses. Refer
to §5.2 rather than restating an equation here.

**Metformin dosing exemplifies the necessity of eGFR-based logic:**
- eGFR ≥ 60 mL/min/1.73 m²: Full dosing up to 2000–3000 mg/day
- eGFR 45–59 mL/min/1.73 m²: Maximum 2000 mg/day (start ≤1000 mg/day)
- eGFR 30–44 mL/min/1.73 m²: Maximum 1000 mg/day (start ≤500 mg/day)
- eGFR < 30 mL/min/1.73 m²: Absolute contraindication (lethal lactic acidosis risk)

**SGLT2 inhibitors (e.g., empagliflozin):** Declining eGFR reduces glycemic efficacy but retains cardiorenal protective benefits, altering CDS logic from strict glycemic contraindication to indication-specific dosing paradigm down to eGFR threshold of 20 mL/min/1.73 m².

**Hepatic dosing guidance** must never be driven by serum transaminases (ALT/AST) alone in CDS rule engines. Transaminase elevations reflect acute or ongoing hepatocellular injury rather than actual functional metabolic and synthetic capacity. Validated CDS architecture mandates stratification based on the Child-Pugh classification system (Classes A, B, and C). Metformin is contraindicated in severe hepatic impairment (Child-Pugh Class C) because impaired hepatic lactate clearance dramatically increases incidence of fatal lactic acidosis.

**Pioglitazone is the one declared exception, and it is not a severity rule.** Its
label states ALT above 2.5× ULN as a gate on *starting* the drug. SSOT §3.2 admits
this under `hepatic_criterion: label_initiation_gate`, which the rule must declare
and cite; the same value may not be reused to stratify hepatic severity or scale a
dose. Pioglitazone's Child-Pugh contraindication is separate and stands on its own.

## 9. Geriatric Polypharmacy, Pharmacodynamics, and Maternal-Fetal Safety

Elderly patients enrolled in home-care programs frequently present with complex multimorbidity, receiving complex polypharmacy regimens that elevate the risk of dangerous drug-drug interactions. CDS engines must maintain dedicated rule libraries targeting severe, clinically relevant interactions rather than generating general interaction database dumps that induce alert fatigue.

**Key interaction clusters in geriatric diabetes management.** Each is annotated with
whether the *interacting partner* is on the SEML, because a rule whose partner is
unavailable in Saudi Arabia can never fire in this population and is not worth
authoring first (SSOT §3.2, local formulary):

- **OCT2 inhibition + metformin:** reduced renal tubular clearance of metformin raises lactic acidosis risk. **Dolutegravir is on the SEML** (§7.3.2.3, `Tablet: 50 mg`) — firable. **Cimetidine is not on the SEML** — unfirable; the SEML H2 antagonist is famotidine (§14.1, `Tablet: 20 mg, 40 mg`), which is not an OCT2 inhibitor, so this arm of the rule has no Saudi partner.
- **CYP2C9 inhibition + sulfonylureas:** impaired hepatic metabolism of gliclazide causes prolonged, potentially fatal hypoglycaemia. **Anchor this rule on fluconazole** (§7.2, `Capsule: 50 mg, 150 mg, 200 mg` and `Solution for injection: 2 mg/ml` — systemic) — firable. **Miconazole is on the SEML as `Cream: 2%` only** (§22.1, dermatological), so the label's *systemic*-miconazole contraindication has no Saudi dose form and must not be the rule's primary trigger. A prior revision of this research bolded systemic miconazole as the headline CONTRAINDICATED pair; as written it could never fire.
- **SGLT2 inhibitors + loop diuretics + ACEi/ARBs:** acute intravascular volume depletion, orthostatic hypotension, prerenal AKI in the frail elderly. All three classes are on the SEML — firable, and the highest-yield rule in this list.
- **Thiazolidinediones + insulin:** synergistic fluid retention, peripheral oedema, increased CHF exacerbation. Both on the SEML — firable.

**Pharmacotherapy during pregnancy and lactation** requires nuanced clinical narrative evaluations rather than simplistic letter-based risk categories. Per SSOT §3.2 the catalogue stores **three separate propositions per drug — `pregnancy`, `breast_feeding`, `fertility` — each with its own pointer into §4.6 of the named label version, and never a grade.** They are recorded in §12, not collapsed into one cell.

**Insulins (Aspart, Lispro, Glargine, NPH):** Do not cross placental barrier in clinically significant amounts. No teratogenic or embryotoxic effects. Safe during lactation (excreted in trace amounts, degraded in infant GI tract).

**Most oral antidiabetics contraindicated/restricted during pregnancy/lactation:**
- **Gliclazide:** Crosses placenta, induces severe neonatal hypoglycemia — strictly contraindicated
- **SGLT2 inhibitors:** Contraindicated 2nd/3rd trimesters (preclinical renal pelvis dilation, tubule damage)
- **Metformin:** Partial exception — EMA permits continuation/initiation during pregnancy under specialist supervision; excreted in breast milk (decision: stop nursing or stop drug)

## 10. Comprehensive Clinical and Regulatory Matrix

Every renal and hepatic value below is a **draft awaiting a label pin** (see
*Implementation status*). The SEML column is the one verified column. Per-ingredient
complication profiles follow in §11.

| Drug & ATC | SEML 2023 — listed strengths (verified) | Renal Dosing | Hepatic Dosing (Child-Pugh) | Major Interactions | Monitoring |
|------------|---------------------|--------------------------|----------------------------|-------------------|------------|
| **Metformin** A10BA02 | §15.1.1 `Tablet: 500 mg, 850 mg` | **eGFR ≥60:** 2000–3000 mg/day<br>**45–59:** max 2000 mg/day (start ≤1000)<br>**30–44:** max 1000 mg/day (start ≤500)<br>**<30:** Contraindicated | **Class C:** Contraindicated (impaired lactate clearance)<br>**A/B:** Caution; discontinue if severe liver dysfunction | • OCT2/OCT1 inhibitors: dolutegravir ↑ exposure (on SEML); cimetidine not on SEML<br>• Iodinated contrast (iohexol, §27.2): stop prior/at imaging; restart ≥48hr post if eGFR stable<br>• Alcohol ↑ lactic acidosis risk | • Baseline eGFR before initiation<br>• eGFR annually if normal<br>• eGFR q3–6mo if 30–59 or elderly<br>• Vitamin B12 q1–2 years |
| **Insulin Aspart** A10AB05 | §15.1.1 `Suspension for injection: 100 IU/ml` | Clearance independent of eGFR/CrCl formulas; renal impairment ↓ clearance. Dose reductions via clinical glucose titration. | **Class A/B/C:** ↓ insulin clearance & gluconeogenesis → ↓ requirements. Frequent glucose monitoring & dose reduction required. | • ACEi, salicylates, anabolic steroids ↑ hypoglycemia (all on SEML; the SEML androgen is testosterone, §15.4)<br>• Corticosteroids, thiazides, thyroid hormones ↓ effect<br>• Beta-blockers mask adrenergic signs<br>• MAOIs listed in the label are **not on the SEML** — unfirable | • Daily SMBG/CGM<br>• HbA1c q3mo<br>• eGFR & LFTs q6–12mo<br>• Injection site checks |
| **Insulin Lispro** A10AB04 | §15.1.1 `Suspension for injection: 100 IU/ml, 200 IU/ml` — both concentrations confirmed against the original PDF by the project owner (2026-08-17) | ↓ Clearance in renal impairment → ↑ hypoglycemia risk. Individualized dose reductions via glucose titration (no specific eGFR cutoffs). | **Class A/B/C:** ↓ Clearance & gluconeogenesis → ↓ requirements. Intense glucose monitoring mandatory. | • Oral antidiabetics, ACEi, ARBs, sulfonamides ↑ hypoglycemia<br>• Thiazides, loop diuretics, corticosteroids ↑ glucose<br>• Non-selective beta-blockers mask tachycardia | • SMBG multiple times daily<br>• HbA1c baseline & q3mo<br>• Annual renal function<br>• Periodic injection site inspection |
| **Insulin Glargine** A10AE04 | §15.1.1 `Solution for injection: 100 IU/ml, 300 IU/ml` | Declining eGFR ↓ clearance, prolongs half-life. Progressive dose reductions as renal function deteriorates. | **Class A/B/C:** ↓ Metabolic capacity → ↓ basal insulin requirements. Titration guided by fasting plasma glucose. | • Pioglitazone: ↑ fluid retention & cardiac failure risk<br>• Beta-blockers, clonidine: mask hypoglycemia<br>• Corticosteroids: severely attenuate glycemic control | • Daily FPG during titration<br>• HbA1c q3–6mo<br>• eGFR & K⁺ annually<br>• Weight tracking for fluid overload |
| **Isophane Insulin (NPH)** A10AC01 | §15.1.1 `Suspension for injection: 100 IU/ml` | Renal impairment ↓ metabolic clearance of protamine complexes. Dose reduction via glucose monitoring as eGFR declines. | **Class A/B/C:** ↓ Insulin clearance & blunted counter-regulatory gluconeogenesis → ↓ total daily doses. | • Salicylates, ACEi ↑ hypoglycemic response<br>• Glucocorticoids, OCPs, thiazides impair glycemic control<br>• Alcohol: unpredictable, exacerbates hypoglycemia<br>• MAOIs **not on the SEML** — unfirable | • Pre-prandial & bedtime glucose<br>• HbA1c q3–6mo<br>• eGFR & LFTs annually<br>• Injection site checks for lipoatrophy |
| **Gliclazide** A10BB09 | §15.1.1 `Tablet: 30 mg, 60 mg, 80 mg` — MR and IR **not distinguished**; release profile confirmed absent from the original PDF (2026-08-17) | **⚠ Metric unresolved — not authorable.** A prior revision wrote "eGFR/CrCl 30–80", slashing two distinct observables together; SSOT §5.2 and CI gate 15 require exactly one `renal_metric`. Which one, and whether the band is numeric at all, is decided by the pinned label — not here.<br>**<30:** Contraindicated (accumulation, protracted hypoglycemia) — same metric question applies | **Class C:** Contraindicated<br>**A/B:** Avoid or extreme caution (↓ metabolism, ↑ hypoglycemia risk) | • **Fluconazole (§7.2, systemic): primary trigger** — severe prolonged hypoglycemia<br>• Fluoroquinolones, ACEi ↑ hypoglycemia (both on SEML)<br>• Systemic miconazole is the label's CONTRAINDICATED pair but is **SEML-listed as `Cream: 2%` only** — cannot fire<br>• Danazol, chlorpromazine **not on the SEML** — unfirable | • Baseline eGFR & hepatic profile<br>• HbA1c q3mo<br>• eGFR & LFTs ≥annually<br>• Frequent SMBG during initial titration |
| **Empagliflozin** A10BK03 | §15.1.1 `Tablet: 10 mg, 25 mg` | **T2DM:** ≥60: 10–25 mg/day; 30–59: 10 mg/day (↓ efficacy <45)<br>**CKD/HF:** ≥20: 10 mg/day<br>**<20:** Do not initiate | **Class A/B/C:** No dose adjustment. Exposure ↑ in Class C; clinical caution. | • Loop/thiazide diuretics: severe volume depletion & hypotension<br>• Insulin/secretagogues: ↑ hypoglycemia (↓ secretagogue dose)<br>• RAASi/NSAIDs: prerenal AKI risk | • eGFR before initiation & ≥annually<br>• Volume status & BP periodically<br>• Monitor euglycemic DKA & perineal infections |
| **Sitagliptin** A10BH01 | §15.1.1 `Tablet: 50 mg, 100 mg` — **no 25 mg strength listed** | **≥45:** 100 mg/day<br>**30–44:** 50 mg/day<br>**<30 (incl. ESRD/dialysis):** 25 mg/day — **not strength-achievable** on the SEML (see achievability table) | **Class A/B:** No adjustment<br>**Class C:** Not studied; clinical caution | • Digoxin: slight ↑ AUC; monitor levels. Digoxin is SEML-listed as `Tablet: 0.125 mg, 0.25 mg`, `Oral solution: 0.05 mg/ml` and `Solution for injection: 0.25 mg/ml` (§12.2, §12.4)<br>• Sulfonylureas/Insulin: ↑ hypoglycemia (↓ secretagogue) | • eGFR prior to initiation<br>• eGFR annually if normal, q3–6mo if <45<br>• Monitor for acute pancreatitis (persistent abdominal pain) |
| **Pioglitazone** A10BG03 | §15.1.1 `Tablet: 15 mg, 30 mg` | No dose adjustment across eGFR spectrum (incl. ESRD). Caution in hemodialysis (fluid retention). | **Class A/B/C: CONTRAINDICATED.**<br>Separately: do not initiate if baseline ALT >2.5×ULN — declare `hepatic_criterion: label_initiation_gate` (SSOT §3.2); this value may not stratify severity or scale a dose. | • CYP2C8 inducers (rifampicin, §7.1.4): ↓ AUC — firable<br>• **Insulin: extreme heart failure risk** — firable<br>• Gemfibrozil (CYP2C8 inhibitor, label cap 15 mg/day) is **not on the SEML** — unfirable | • ALT/AST before initiation & periodically<br>• Monitor HF signs (weight, edema, dyspnea)<br>• Annual bone density (fracture risk)<br>• Monitor hematuria (bladder cancer) |
| **Liraglutide** A10BJ02 | §15.1.1 `Solution for injection: 6 mg/ml` | **≥15:** No adjustment<br>**<15 (ESRD):** Limited experience; caution or avoid | **Class A/B:** No adjustment<br>**Class C:** Limited experience; caution | • Sulfonylureas/Insulin: ↑ hypoglycemia (↓ secretagogue)<br>• Delays gastric emptying: may minorly affect oral med absorption | • Baseline & periodic amylase/lipase if pancreatitis symptoms<br>• Calcitonin/thyroid US if MTC suspected<br>• Renal function if severe GI fluid loss |
| **Glucagon** H04AA01 | §15.1.2 `Powder and solvent for solution for injection: 1 mg` | Clearance independent of eGFR/CrCl. No adjustment in renal impairment. | No adjustment required. **Ineffective** in severe hepatic impairment, prolonged starvation, alcoholism (depleted glycogen). | • Warfarin (§10.2): potentiates anticoagulant effect — firable<br>• Beta-blockers: severe transient hypertension & bradycardia — firable<br>• Indomethacin **not on the SEML** — unfirable | • Blood glucose immediately & q10–15min post-injection until conscious<br>• Emergency medical follow-up mandatory<br>• Serum K⁺ if used in beta-blocker overdose |

The renal-metric column is deliberately headed "Renal Dosing" without a
metric in the heading. A prior revision headed it "Renal Dosing (eGFR/CrCl)",
which invited exactly the conflation the gliclazide row now flags. Each cell
names its own observable, or says it cannot.

## 11. Per-Ingredient Complication Profiles

Adverse effects, boxed warnings, and contraindications ("what can go wrong").
**Sourcing caveat:** compiled from FDA labels/DailyMed, StatPearls, and
drug-safety-agency alerts (MHRA/Medsafe). Local SFDA SPCs track EMA/ICH, not
FDA — cross-check the specific complication/contraindication against the EMA
SmPC or local SPC before anything here becomes rule content. FDA and EMA agree
on the substance of almost all of these, but exact wording, thresholds, and
which warnings are boxed vs. standard precaution can differ.

### 11.1 Metformin (A10BA02 — biguanide)

| | |
|---|---|
| **Most serious complication** | Lactic acidosis — rare (estimates range ~0.03/1,000 to ~6/100,000 patient-years across sources) but historically fatal in up to ~50% of cases, with more recent series still showing up to ~25% mortality. Onset is subtle: malaise, myalgia, respiratory distress, somnolence, abdominal pain — can progress to hypothermia, hypotension, resistant bradyarrhythmia. |
| **Key risk factors** | Renal impairment (contraindicated at eGFR <30 mL/min/1.73m² per current literature), unstable/acute heart failure, hepatic impairment, sepsis, hypoxia, dehydration, iodinated contrast media, excess alcohol, age >65. |
| **Common AEs** | GI: diarrhea, nausea/vomiting, flatulence, abdominal discomfort, metallic taste — dose-dependent, typically transient. ~50% tolerate max dose; ~5% cannot tolerate any dose. |
| **CDS relevance** | The eGFR gate is covered in the matrix. Worth adding a rule for **temporary hold** around contrast-media procedures/acute illness — a common home-care scenario (patient goes for imaging, no one remembers to pause metformin). |

Not yet source-verified this pass (commonly cited but not directly confirmed in
search — check SPC before including): vitamin B12 deficiency with long-term use.

### 11.2 Insulins (Aspart, Lispro, Glargine, Isophane/NPH)

#### Shared across all four (ATC A10AB04/05, A10AE04, A10AC01)

| Complication | Detail |
|---|---|
| **Hypoglycemia** | The dominant safety issue for the whole class — severity ranges from mild to coma/death. |
| **Hypokalemia** | All insulins shift K⁺ intracellularly; can be life-threatening (respiratory paralysis, ventricular arrhythmia). Flagged explicitly in the lispro label as a monitoring priority — relevant given how many K⁺-affecting drugs (ACEi, spironolactone, furosemide) sit elsewhere on the formulary. |
| **Lipodystrophy** | Lipohypertrophy or lipoatrophy at injection/infusion site from failure to rotate sites; can impair absorption (clinically important — unexplained glycemic variability in a home-care patient may trace back to this). Localized cutaneous amyloidosis also specifically flagged in the lispro label. |
| **Fluid retention / heart failure** | Specifically called out when insulin is combined with thiazolidinediones (i.e., pioglitazone, also on this catalogue) — watch for this combination. |
| **Allergic reactions** | Local (erythema, edema, pruritus) usually resolve in days–weeks; systemic/anaphylaxis rare but reported. |
| **Weight gain** | Attributed to anabolic effect + reduced glucosuria. |

#### Insulin-specific notes

- **Glargine vs. NPH (isophane):** Glargine reduces nocturnal/severe hypoglycemia risk by roughly 40–60% vs. NPH across pooled trial data — directly relevant to basal-insulin choice in an elderly home-visit population where nocturnal hypoglycemia often goes unwitnessed.
- **Isophane/NPH:** Less predictable peak action → higher hypoglycemia and weight-gain burden than glargine in comparative studies, though a Cochrane-level review found no clinically relevant difference in *severe* hypoglycemia specifically, only in symptomatic/nocturnal events.
- **Aspart/Lispro (rapid-acting):** Timing-dependent (15 min before to immediately after meals) — mistimed dosing is a real-world hypoglycemia driver in home care. Pump malfunction is specifically flagged in the lispro label as a hyperglycemia/DKA risk pathway if the patient is pump-dependent.

### 11.3 Gliclazide (A10BB09 — 2nd-gen sulfonylurea)

| | |
|---|---|
| **Most serious complication** | Hypoglycemia — the chief and expected AE of the whole sulfonylurea class. Symptoms span autonomic (sweating, tachycardia, palpitations) and neuroglycopenic (confusion, seizure, coma). |
| **Risk factors** | Elderly, renal impairment (CKD blunts the kidney's own gluconeogenic hypoglycemia defense), polypharmacy. One real-world study found ~6.7-fold higher odds of severe hypoglycemia requiring ED admission vs. glimepiride in elderly patients — but that finding is contested by other evidence, so treat it as a flag, not a settled figure. |
| **Renal positioning** | Gliclazide has a comparatively better renal safety profile than glyburide/glibenclamide — one Swiss reference describes cautious use down to GFR 40–60 mL/min, stopped below ~40 — but this needs confirmation against the specific SFDA SPC before it becomes a rule threshold (the matrix's metric question applies). |
| **Other AEs** | Weight gain; rare hepatotoxicity; arthralgia/back pain reported with the MR formulation (causality unclear). |
| **CDS relevance** | Sulfonylurea + renal impairment + elderly is exactly the polypharmacy/home-care intersection this catalogue calls out — good candidate for an early rule. |

### 11.4 Empagliflozin (A10BK03 — SGLT2 inhibitor)

| Complication | Detail |
|---|---|
| **Euglycemic DKA** | Regulatory-flagged risk (Medsafe/MHRA-level alerts). Can present with near-normal glucose (<250 mg/dL), delaying recognition. Risk rises in the first months of treatment, perioperatively, and during acute illness/fasting/vomiting — sick-day-rule candidate. |
| **Fournier's gangrene** | Rare, life-threatening necrotizing fasciitis of the perineum — class-wide postmarketing signal. Symptoms: pain/tenderness/redness/swelling of genital or perineal area, often with fever/malaise. Surgical emergency. |
| **Genital mycotic infections / UTI / urosepsis / pyelonephritis** | Mechanistically expected from glycosuria. |
| **Volume depletion / hypotension** | Highest rates in heart-failure patients, the elderly, and those on diuretics/ACEi/ARB — an important intersection with the antihypertensive catalogue. |
| **Amputation signal** | Class-wide FDA-flagged risk, stronger for canagliflozin specifically; described as "numerically lower" for empagliflozin in some sources but still worth a flag given the foot-exam/PAD population. |
| **AKI / rising creatinine, falling eGFR** | Expected early hemodynamic effect — needs a monitoring rule, not necessarily a stop rule. |
| **Hypoglycemia** | Mainly when combined with insulin or a secretagogue (reported up to ~41% in combination therapy). |

### 11.5 Sitagliptin (A10BH01 — DPP-4 inhibitor)

| Complication | Detail |
|---|---|
| **Acute pancreatitis** | Including fatal/hemorrhagic/necrotizing forms — discontinue if suspected. |
| **Bullous pemphigoid** | Large, hard skin blisters — postmarketing signal serious enough to require hospitalization in some cases; discontinue and consider dermatology referral. |
| **Severe hypersensitivity** | Anaphylaxis, angioedema, Stevens-Johnson syndrome. |
| **Severe/disabling arthralgia** | New joint pain in a patient on sitagliptin should prompt consideration of the drug as cause. |
| **Renal function** | Worsening renal function, including AKI (sometimes requiring dialysis) and tubulointerstitial nephritis reported; drug is primarily renally eliminated, so dose adjustment is needed — exact eGFR bands need SPC confirmation (see matrix and achievability table). |
| **Heart failure** | Notably, sitagliptin (unlike saxagliptin) has **not** shown increased HF hospitalization risk in outcome trials — useful differentiator if choosing among DPP-4s, but class-level caution is still advised. |
| **Common AEs** | Upper respiratory infection, nasopharyngitis, headache; hypoglycemia mainly when combined with insulin/sulfonylurea (low risk as monotherapy). |

### 11.6 Pioglitazone (A10BG03 — thiazolidinedione)

| Complication | Detail |
|---|---|
| **Boxed warning: heart failure** | Causes/exacerbates fluid retention → new-onset or worsening CHF. Contraindicated in symptomatic (NYHA III/IV) heart failure. Watch for dyspnea, rapid weight gain, edema. |
| **Bladder cancer** | Contraindicated in active bladder cancer; caution with prior history — weigh glycemic benefit against unknown recurrence risk. Counsel patients to report hematuria, new/worsening urinary urgency, dysuria. |
| **Fracture risk** | ~50% increased risk in women in long-term studies (e.g., 5.1% vs 2.5% placebo over ~34 months); effect persists throughout treatment, mechanism is reduced osteoblast activity. |
| **Hepatotoxicity** | Rare, but LFT monitoring is standard practice. |
| **Macular edema, dilutional anemia, dose-related edema** | Also reported. |
| **Reproductive** | Can restore ovulation in premenopausal anovulatory women — pregnancy-risk counseling needed, an easy-to-miss point in a diabetes-focused visit. |
| **Not for** | Type 1 diabetes or pediatric patients. |

### 11.7 Liraglutide (A10BJ02 — GLP-1 receptor agonist)

| Complication | Detail |
|---|---|
| **Boxed warning: thyroid C-cell tumors / MTC** | Based on rodent carcinogenicity data (dose- and duration-dependent); human relevance undetermined. **Contraindicated** in personal/family history of medullary thyroid carcinoma or MEN2 syndrome. |
| **Acute pancreatitis** | Discontinue if suspected — class effect across GLP-1 receptor agonists. |
| **Acute gallbladder disease** | Cholelithiasis/cholecystitis — investigate if suspected. |
| **Hypoglycemia** | Mainly when combined with insulin or a secretagogue; dose reduction of the other agent is often needed. |
| **Renal impairment** | Usually secondary to GI-effect-driven dehydration (nausea/vomiting/diarrhea) rather than a direct nephrotoxic effect. |
| **Other precautions** | Heart rate increase, hypersensitivity reactions. |
| **Common AEs (≥5%)** | Nausea, diarrhea, vomiting, constipation, headache, decreased appetite, dyspepsia, fatigue, dizziness, abdominal pain, increased lipase. |
| **Home-care practical note** | Injection pens must never be shared between patients even with a new needle — worth a hard rule if the workflow ever touches multi-patient visits or shared supply stock. |

**Flag for SPC confirmation:** a trial-protocol source mentioned a pregnancy
contraindication and a suicidal-ideation precaution for liraglutide; both need
verification against the actual current label before use, since protocol
documents sometimes carry older or trial-specific language rather than the
current core SPC.

### 11.8 Glucagon (H04AA01 — anti-hypoglycemic hormone)

| Complication | Detail |
|---|---|
| **Contraindications** | Pheochromocytoma (glucagon can trigger catecholamine release → hypertensive crisis; IV phentolamine is the described rescue); insulinoma (paradoxical hypoglycemia — glucagon can stimulate exaggerated insulin release); glucagonoma (as diagnostic aid); known hypersensitivity. |
| **Common AEs** | Nausea (up to ~35% of administrations — the most common AE by far), vomiting, transient rise in BP/heart rate (up to ~2 hours post-dose). |
| **Rare but serious** | Anaphylaxis/hypersensitivity (urticaria, respiratory distress, hypotension) — rare, reported mostly with IV administration. |
| **Interactions** | Beta-blockers → exaggerated transient BP/pulse rise; indomethacin → may blunt or reverse the glucose-raising effect; potentiates warfarin's anticoagulant effect. |
| **Effectiveness caveat** | Requires adequate hepatic glycogen stores — **ineffective in starvation, adrenal insufficiency, chronic hypoglycemia, or alcohol-related hypoglycemia.** This is a real trap in a home-care population with malnutrition or heavy alcohol use — IV dextrose is the fallback, not a second glucagon dose. |
| **CDS relevance** | This is the emergency rescue drug — it directly feeds the severe-hypoglycaemia red-flag library in §4. The pheochromocytoma/insulinoma contraindications are largely theoretical at point-of-emergency-use (an undiagnosed pheo won't be known in the moment), but the glycogen-depletion caveat is operationally real and worth building into the protocol logic (e.g., "if known alcohol use disorder or malnutrition flag present, prefer IV dextrose over glucagon as first-line if IV access available"). |

### 11.9 What remains open before rule-writing

Per the roadmap checklist, each drug above still needs, sourced against the
actual local SPC: exact renal dosing table (eGFR vs. CrCl, per §5.2); hepatic
dosing (Child-Pugh, per §3.2); monitoring interval after initiation/dose
change, with label version (§7.1 `monitors`); pregnancy/lactation narrative
(§12 below), not a letter category; and confirmation of `source_family`
pinning per the architecture. This section covers only the "what can go wrong"
half of the picture.

---

## 12. Pregnancy, Breast-feeding, and Fertility — three propositions per SSOT §3.2

Each cell is a proposition plus a pointer to §4.6 of the pinned label. **Because
`source_label.status` is `unretrieved` for every ingredient, the pointer column is
empty and every proposition below is a research draft, not a catalogue entry.**
`not_stated_in_label` is a distinct, recorded state — never read as reassurance.

| Drug | `pregnancy` | `breast_feeding` | `fertility` | §4.6 pointer |
|---|---|---|---|---|
| **Metformin** | Permitted under specialist supervision where insulin unsuitable; insulin preferred | Excreted in human milk — decide between discontinuing nursing and discontinuing the drug | `not_stated_in_label` (to confirm against pinned label) | ⛔ unretrieved |
| **Insulin Aspart** | No restriction; no fetal risk identified | Compatible; trace amounts, degraded in infant GI tract. Maternal dose adjustment may be needed | `not_stated_in_label` | ⛔ unretrieved |
| **Insulin Lispro** | Permitted; used for tight control in GDM and pre-existing DM | Compatible; no restriction. Maternal dose adjustment may be needed | `not_stated_in_label` | ⛔ unretrieved |
| **Insulin Glargine** | No adverse effect on pregnancy or embryo-fetal development reported | Compatible; digested in infant GI tract | `not_stated_in_label` | ⛔ unretrieved |
| **Isophane Insulin (NPH)** | Long-standing use; preferred intermediate insulin where analogues unavailable | Compatible | `not_stated_in_label` | ⛔ unretrieved |
| **Gliclazide** | Contraindicated — placental transfer, severe neonatal hypoglycemia | Contraindicated — excreted in breast milk | `not_stated_in_label` | ⛔ unretrieved |
| **Empagliflozin** | Contraindicated in 2nd/3rd trimester (preclinical renal pelvis dilation, tubule damage) | Contraindicated — excreted in milk | `not_stated_in_label` | ⛔ unretrieved |
| **Sitagliptin** | Not recommended — animal reproductive toxicity at high exposure | Contraindicated — excreted in animal milk | `not_stated_in_label` | ⛔ unretrieved |
| **Pioglitazone** | Contraindicated — animal fetal growth restriction, delayed ossification | Contraindicated — excreted in animal milk | `not_stated_in_label` | ⛔ unretrieved |
| **Liraglutide** | Contraindicated — animal reproductive toxicity; switch to insulin | Contraindicated | `not_stated_in_label` | ⛔ unretrieved |
| **Glucagon** | Permitted for emergency severe hypoglycemia; does not cross placenta | Compatible — degraded in infant GI tract | `not_stated_in_label` | ⛔ unretrieved |

---

## 13. Strength Achievability against the SEML (SSOT §3.2)

A dose no listed strength can produce is not a recommendation. Each dose-adjustment
rule declares one of `strength_achievable | achievable_by_division | unachievable`;
an unachievable target routes to pharmacist review rather than rendering as an
instruction.

| Target dose | SEML strengths | Verdict |
|---|---|---|
| Metformin 500 / 1000 / 2000 / 3000 mg/day | `500 mg, 850 mg` | `strength_achievable` (multiples of 500 mg) |
| Sitagliptin 100 mg/day; 50 mg/day | `50 mg, 100 mg` | `strength_achievable` |
| **Sitagliptin 25 mg/day (eGFR <30)** | `50 mg, 100 mg` | **`unachievable`** — halving a film-coated tablet is not a licensed dose form. The renal-impairment arm of the sitagliptin rule therefore routes to pharmacist review; it cannot render "give 25 mg". |
| Empagliflozin 10 / 25 mg/day | `10 mg, 25 mg` | `strength_achievable` |
| Pioglitazone 15 / 30 mg/day | `15 mg, 30 mg` | `strength_achievable` |
| Gliclazide 30 mg MR/day | `30 mg, 60 mg, 80 mg` | `strength_achievable` **if** the 30 mg entry is the MR form. The SEML does not state release profile (confirmed absent from the original PDF 2026-08-17), and MR and IR gliclazide are not interchangeable mg-for-mg — so an ingredient-level rule cannot safely emit an MR dose. This needs `drug_scope_level: product` or `curated_set` (SSOT §7.1e), not `ingredient`; the IR/MR decision comes from the pinned label. |
| Glucagon 1 mg IM | `1 mg` powder for injection | `strength_achievable` |
| Insulin glargine, any unit dose | `100 IU/ml, 300 IU/ml` (one row, one drug) | `strength_achievable`, but **concentration-critical**. Two concentrations of the same insulin are on the formulary simultaneously, so any card that states an insulin *volume* rather than *units* is a dosing error — and a U-300 volume given from a U-100 assumption is a threefold overdose. **Units only, never millilitres, and the concentration is part of the drug identity** (`drug_scope_level: product`, not `ingredient`). |
| Insulin lispro, any unit dose | `100 IU/ml, 200 IU/ml` — both concentrations confirmed against the original PDF (2026-08-17) | Same units-only rule applies, and it is now concentration-critical on a stronger footing: both strengths are confirmed on the formulary, so any card that states a lispro *volume* rather than *units* is a dosing error — a U-200 volume given from a U-100 assumption is a twofold overdose. **Units only, never millilitres, and the concentration is part of the drug identity** (`drug_scope_level: product`, not `ingredient`). Humalog's EMA SmPC covers both concentrations under one authorisation; the EMA high-strength-insulin medication-error guidance (EMA/134145/2015) applies. |

---

## 14. Rule Execution and Validation Architecture

Translating regulatory parameters into active logic within the Noor CDS engine demands strict adherence to software verification standards. Prior to publishing any clinical rule into production, comprehensive test suites must validate rule execution against boundary conditions. The red-flag operational framework (SSOT §11.7) is governed in Part A §4; the two frameworks below are the remaining operational structures this catalogue bears on.

### 14.1 Metformin eGFR Dosing Logic Validation

Boundary-plus-pairwise case selection per SSOT §12.3 — **three rows per threshold: at
the boundary, just below, just above.** Four bands means three internal boundaries
(30, 45, 60), so nine rows minimum, not four:

| Band | eGFR (mL/min/1.73 m², 2021 CKD-EPI without race) |
|---|---|
| Normal | ≥ 60 |
| Stage 3a | 45–59 |
| Stage 3b | 30–44 |
| Severe | < 30 |

Test cases verify:
- Prescribed dose ≤ band ceiling → no card
- Dose above the band ceiling → card at the severity the rule declares
- eGFR < 30 → `stop_and_review` (SSOT §9.1) — the strongest of the three severities,
  and **still not a block.** §9.1 admits exactly `stop_and_review |
  interruptive_review | passive_task`; "stop-order" is not one of them, and a prior
  revision's "absolute contraindication stop-order with immediate withdrawal" reads as
  a hard stop the engine does not have. The card recommends withdrawal; the clinician
  decides.
- **eGFR absent or stale** → by the §8.3 degradation invariant, a `stop_and_review`
  rule whose data requirements are unmet degrades to `interruptive_review`. It never
  blocks and never silently disappears. This case needs its own test row, and it is the
  most likely case in a home visit — a patient with no recent eGFR is the norm, not the
  exception.

Note the two distinct fields §7.1f separates and this rule needs both of: `monitors`
(may this rule use the eGFR I have) and `max_age_days` (is the patient due for another
one). The monitoring column of the matrix above populates the second; the first is a
per-rule decision.

### 14.2 Automated Recall Systems for Missed Monitoring

- Home-care/elderly: lack of follow-up is a primary cause of preventable drug toxicity
- The engine tracks required follow-up intervals on drug initiation and on dose change

Two fields, not one (SSOT §7.1f), and the examples below need both:

| Field | Question it answers |
|---|---|
| `monitors` | May this rule use the result I already have? Must pin the label version it came from. |
| `max_age_days` | Is the patient due for another one? |

- **Example:** eGFR not reassessed within `max_age_days` of empagliflozin initiation → `passive_task` recall for mobile phlebotomy. The interval is ⛔ `unpopulated` — a prior revision stated 90 days with no source.
- **Example:** LFTs not recorded within `max_age_days` of pioglitazone initiation → `passive_task` recall. Interval ⛔ `unpopulated` — a prior revision stated 180 days with no source.

Both intervals must come from the pinned label's monitoring section and carry its
version, per `monitors`. Neither is authorable while `source_label.status` is
`unretrieved`.

### 14.3 Cardiorenal Optimization Logic (HbA1c-Independent)

- SGLT2 inhibitors (empagliflozin) and GLP-1 RAs (liraglutide) evaluated for organ-protective benefits
- Patient profile with CKD or symptomatic HF → CDS recommends empagliflozin regardless of baseline HbA1c
- **The eGFR band and the albuminuria criterion are ⛔ `unpopulated`.** A prior revision stated "eGFR 20–60 or persistent albuminuria" without a source. This one is not a label claim at all — it is a guideline claim, so it needs a `source_family` pinned per SSOT §7.3 (KDIGO for the CKD staging and albuminuria definition), not an SmPC locator. Albuminuria in particular has no number here: "persistent albuminuria" is a KDIGO category with a threshold and a confirmation interval, and both must be cited before this rule can select patients.

---

# Part C — Governance

## 15. Evidence and Authorability Checklist

Before a claim moves from this reference into Noor content, the author must
record:

```yaml
claim:
  id: dka.bhb_diagnostic_threshold
  proposition: "..."
  value: 3.0
  unit: mmol/L
  source:
    organisation: "..."
    document: "..."
    version_or_revision: "..."
    locator: "..."
    jurisdiction: international | saudi | product_label
    evidence_grade: "..."
  population: "..."
  exclusions: ["..."]
  fallback_from:
    tried: ["..."]
    reason: "..."
  status: unretrieved | populated | clinician_approved
  approved_by: null
  approved_at: null
  review_date: "..."
```

The status remains `unretrieved` when the source cannot be checked. A document
title in a bibliography is not a citation. A citation without a locator is not
a usable threshold source. A source-backed proposition without a clinical
owner is not approved content.

### 15.1 Required test rows

For every numeric threshold, the rule case file must contain at least:

- Just below the boundary.
- Exactly at the boundary.
- Just above the boundary.
- Missing required input.
- Stale or unusable input.
- Conflicting measurements or wrong context.
- A clinically severe presentation that must not be suppressed by a repeat.

Pairwise cases must cover the important combinations: diabetes status, SGLT2
exposure, CKD, fasting, pregnancy when in scope, medication exposure,
measurement quality, and competing acute findings. Tests must assert exact
outcomes: `triggered`, `not_triggered`, `indeterminate`, or the applicable
out-of-scope/governance outcome.

---

## 16. Scope Exclusions and Deferred Work

The following are intentionally not automatic Noor conclusions unless separately
approved and sourced:

- Broad ASCVD, HF, stroke, CKD progression, or foot risk scores.
- A diagnosis of DKA or HHS from glucose alone.
- A hypoglycaemia severity level from a meter value without clinical context.
- Automatic treatment, admission, discharge, or medication prescribing.
- Saudi emergency response times or referral destinations without provider policy.
- Copying protected guideline tables, heat maps, instrument descriptors, or
  proprietary decision trees into the repository or UI.

(Cross-disease exclusions — hypertensive nephrosclerosis from routine labs,
hypertensive emergency from BP alone, universal ACS troponin/ECG or stroke
algorithms — are tracked in `hypertension-research.md` §15.)

---

## 17. Source Register

The following sources are candidates for verification and pinning. The source
register for executable content must include the exact edition, revision date,
locator, and jurisdiction; this bibliography alone does not satisfy that
requirement.

- American Diabetes Association Professional Practice Committee. *Standards of
  Care in Diabetes-2026*. Relevant sections must be cited at proposition level.
- Umpierrez GE et al. *Hyperglycemic Crises in Adults With Diabetes: A
  Consensus Report*. Diabetes Care. 2024;47(8):1257-1275.
  doi:10.2337/dci24-0032. Figure 2 and the diagnostic-criteria sections supply
  the DKA and HHS propositions recorded in §2.
- KDIGO. *2024 Clinical Practice Guideline for the Evaluation and Management of
  Chronic Kidney Disease*. G/A categories and monitoring principles.
- International Clinical Diabetic Retinopathy severity terminology and current
  ophthalmology screening guidance.
- Wagner and University of Texas wound classification references, with current
  infection/ischaemia guidance added before authoring foot rules.
- Current Saudi diabetes, cardiovascular prevention, and home-healthcare
  guidance where available.
- Current ICD-10-AM/NPHIES coding guidance and the official ICD-10-CM guidance
  only where a CM comparison is necessary.

**Compiled:** August 2026. The reference is intentionally conservative: where a
claim is clinically plausible but the source, jurisdiction, population, or
action is incomplete, it remains a research note and cannot become a Noor rule.

---

## 18. References

**A bare domain is not a citation.** CI gate 2 requires four fields per threshold —
organisation, document, version, and locator — and every entry in a prior revision of
this research supplied one of them (the domain) and no more. Several also pointed at
Scribd, Ovid, and a retail pharmacy blog, none of which is a regulatory source.
That list is replaced by the two things that can be stated truthfully today: what is
actually verified, and the shape each outstanding citation owes.

### 18.1 Verified primary source (in repository)

| Organisation | Document | Version | Locator |
|---|---|---|---|
| Ministry of Health / SFDA, Kingdom of Saudi Arabia | Essential Medicines List of Saudi Arabia — `saudi-essential-medicines-list-2023.md` | 2023 | §15.1.1 (hyperglycaemia), §15.1.2 (hypoglycaemia); interaction partners as cited inline |

This is the authority for **two claims and no others**: whether an ingredient is
listed, and which strengths and dose forms are listed for it (SSOT §17). It carries
no dosing, contraindication, interaction, or monitoring content, so it can source the
SEML column of the matrix and the achievability table — and nothing else in this file.

### 18.2 Outstanding — one row per ingredient, none yet satisfied

Each of the 11 ingredients owes one pinned label. The required shape, per SSOT §3.2:

| Field | Value |
|---|---|
| `authority` | `sfda` (preferred) → `ema` → `national_agency` |
| `document` | product name exactly as the label titles it |
| `revision_date` | the label's own revision date — **not** the date it was fetched |
| `locator` | e.g. `SmPC 4.2` for posology, `SmPC 4.3` contraindications, `SmPC 4.5` interactions, `SmPC 4.6` pregnancy |
| `fallback_from` | `{tried: [sfda.sdi], reason: "SDI e-service unreachable 2026-08-12"}` |
| `status` | `unretrieved` until all four `pinned` fields are filled |

Ladder order and the reason for its third rung are in SSOT §3.2 — briefly: the local
SFDA SPC first; the EMA centrally-authorised SmPC second; an EU national-agency SmPC
third, which is load-bearing here because **metformin and gliclazide were never
centrally authorised and have no EMA SmPC at all** — an EMA-only fallback would leave
the two oldest and most-prescribed agents in this file unpinnable.

Work rung 2 first for the newer agents — empagliflozin, sitagliptin, pioglitazone,
liraglutide and the insulin analogues are the likeliest to have a centrally-authorised
SmPC, which makes them the cheapest to unblock. Confirm each on the EMA register
rather than assuming; do not treat the grouping in this paragraph as verified.

### 18.3 Not sources

Fixed-dose-combination labels were cited in a prior revision as though they sourced
their single-ingredient constituents — dapagliflozin/metformin for metformin,
pioglitazone/glimepiride for pioglitazone, sitagliptin/metformin and
vildagliptin/metformin for the DPP-4 class. A combination SmPC states the posology of
the combination. It is not the label for either ingredient alone, and rules here are
written at `drug_scope_level: ingredient`. Retrieve the single-ingredient SmPC.

### 18.4 Complication-profile sources (FDA-based; not EMA-equivalent)

FDA drug labels / DailyMed (metformin, insulin lispro, sitagliptin, pioglitazone,
liraglutide, glucagon/GlucaGen/Gvoke); StatPearls (NCBI Bookshelf) — insulin lispro,
empagliflozin, glucagon; Medsafe (NZ) and MHRA-linked prescriber alerts —
empagliflozin DKA/Fournier's gangrene; Drugs.com clinical monographs — pioglitazone,
liraglutide, sitagliptin, insulin lispro; ScienceDirect pharmacology topic reviews —
gliclazide; PubMed/Cochrane comparative trials — insulin glargine vs. NPH; American
Diabetes Association *Clinical Diabetes* — SGLT2i and Fournier's gangrene case
series; NCBI Bookshelf appendix on FDA metformin safety communications; Cureus case
reports — metformin-associated lactic acidosis (2020, 2025).

*Cross-check every claim in §11 against the current SFDA-registered SPC or EMA SmPC
before any threshold is cited in a rule.*