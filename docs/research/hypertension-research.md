> Consolidated from `hypertension-drug-research.md`, `hypertension-drug-complications.md`,
> and the hypertension portions of `diabetes-hypertension-complications.md` (all three
> deleted on consolidation, 2026-08-16). Based on the research requirements of
> `cds-content-roadmap.md` — read the referenced file first.

# Hypertension Research — Clinical and Pharmacotherapy Reference for Project Noor

This file is the single research source for hypertension within the Noor CDS engine. It
covers the disease itself (hypertension-mediated organ damage, the hypertensive-
emergency/ACS/stroke red-flag libraries, screening, coding) and the cardiovascular
pharmacotherapy catalogue (dosing, interactions, monitoring, pregnancy propositions,
strength achievability, per-ingredient complication profiles). The diabetes counterpart
is `diabetes-research.md`.

## Implementation status — read before authoring any rule

Nothing in this file is authorable as-is. Four states are tracked per claim, and they
are different things:

| | Status |
|---|---|
| **SEML 2023 listing and strengths** | ✅ **Verified** against `saudi-essential-medicines-list-2023.md` §12 and §13, the converted primary source in this repository. All 34 ingredients are listed. Strengths are reproduced in the matrices below and analysed in *Strength achievability* (§12). |
| **Source label pin** | ❌ **`unretrieved` for every ingredient.** No local SFDA SPC could be retrieved — the SDI e-service is unreachable as of 2026-08-12 — and no EMA or EU national-agency SmPC has yet been pinned with a document name, revision date, and locator. |
| **Disease-complication claims** | ⚠️ **Source-populated, not clinician-approved.** BP classification, targets, and first-line selection content is drafted against the ESC 2024 and ESH 2023 candidates recorded in §2.1 and §2.8 (KDIGO 2024 for CKD), but no threshold record has passed Noor clinical approval. Everything else in Part A is a research note pending source pinning per §16 below. |
| **Drug-complication profiles (Part B §10)** | ⚠️ **Research draft, FDA-sourced.** The profiles were compiled from FDA labels/DailyMed, StatPearls, and drug-safety-agency alerts because they surfaced most reliably in search. Local SFDA SPCs track EMA/ICH, **not** FDA — cross-check every complication or contraindication against the EMA SmPC or local SPC before it becomes rule content. FDA and EMA agree on the substance of almost all of these (especially boxed warnings), but exact wording, thresholds, and which warnings are boxed vs. standard precaution can differ. |

Per SSOT §3.2 (source-label ladder) and §7.3, **every threshold below is
`status: unpopulated` and no rule referencing one will merge** (CI gate 2). The
clinical content is a research draft awaiting a label pin, not a catalogue.

A prior revision of the pharmacotherapy research wrote `Listed SEML 2023; SFDA/EMA
SmPC` in the regulatory column of all six matrices. "SFDA/EMA SmPC" names no
document, no version, and no locator, so it satisfies none of the four fields CI
gate 2 requires (SSOT §10.4). It is replaced below by the SEML strengths, which are
verifiable, plus an explicit `unretrieved` pin.

**Project-owner confirmation (2026-08-16): all 45 catalogue ingredients (11
diabetes, 34 cardiovascular) are SFDA-registered.** Recorded here as an
assertion by the project owner, not a citation — it does not fill the
registration numbers (which remain unpinned until the SDI e-service is
reachable) and does not change any label status above. SEML 2023 listing
remains the verified proxy. This replaces the registration-number column a
prior revision carried; that column was deleted because its values were
unverifiable and internally contradictory (see `diabetes-research.md`).

The pin each row owes, per SSOT §3.2:

```yaml
source_label:
  pinned: {authority: ..., document: ..., revision_date: ..., locator: ...}
  fallback_from: {tried: [sfda.sdi], reason: "SDI e-service unreachable 2026-08-12"}
  status: unretrieved
```

**A note on the SEML source file.** Its PDF-to-markdown conversion left orphan
strength rows whose drug-name cell is empty — an artifact of merged cells in the
original table. Attribution is unambiguous where the strength is characteristic
(digoxin `0.125 mg, 0.25 mg`; amiodarone `200 mg`; furosemide `40 mg`). The two
§12.1 ambiguous cases were resolved by the project owner against the original
PDF on 2026-08-17: verapamil carries `Tablet: 40 mg, 80 mg` in addition to
`Solution for injection: 2.5 mg/ml`, and nifedipine carries `Tablet: 30 mg` in
addition to `Capsule: 10 mg`. The restored cells are annotated in the converted
source file itself. Where this file states a strength it is one of the
unambiguous or owner-confirmed cases.

---

# Part A — Clinical Reference: Hypertension Complications

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

### 1.2 Clinical signal inventory — hypertension-relevant

The following are candidate registry concepts, not yet approved terminology
entries. Each needs a terminology owner and source mapping before use. Signals
shared with `diabetes-research.md` are duplicated deliberately so each file
stands alone.

| Candidate identifier | Signal type | Values or data | Intended use |
|---|---|---|---|
| `symptom_chest_discomfort` | Patient-reported symptom | Structured symptom phenotype | ACS pathway |
| `symptom_dyspnoea` | Patient-reported symptom | Present, absent, unknown | ACS alternative, HF, pulmonary oedema |
| `symptom_syncope` | Patient-reported symptom | Present, absent, unknown | ACS, arrhythmia, crisis context |
| `finding_altered_mental_status` | Staff-observed sign | Present, absent, unknown | Stroke, hypertensive emergency, hypoglycaemia |
| `finding_seizure` | Staff-observed sign | Present, absent, unknown | Stroke or hypoglycaemia |
| `finding_focal_neurologic_deficit` | Staff-observed sign | Coded deficit or absent | Stroke pathway |
| `finding_new_speech_or_vision_change` | Patient/staff signal | Present, absent, unknown | Stroke pathway |
| `finding_cool_pale_sweaty_skin` | Staff-observed sign | Present, absent, unknown | ACS, shock context |
| `finding_pedal_oedema` | Staff-observed sign | Laterality and severity | HF/renal monitoring |
| `finding_orthostatic_symptoms` | Patient-reported symptom | Present, absent, unknown | Orthostatic BP interpretation |
| `finding_retinal_acute_damage` | Clinician-documented finding | Coded finding | Hypertensive emergency context |

No rule may use these names until the registry assigns a stable terminology
mapping, source display, value constraints, and provenance requirements.

---

## 2. Hypertension-Mediated Organ Damage (HMOD)

### 2.1 Blood pressure classification

Noor must select and pin one source family per tenant and domain. It must not
blend NHC/SHA, ESC, and ESH target systems.

**NHC/SHA 2023 — the SSOT interim default (pinned candidate 2026-08-17, see
`guideline-pin-register.md` §1):** BP 120/80 mmHg is normal; BP >130/80 mmHg is
hypertension; diagnosis depends on measurement method (office, ABPM, home BP —
§3.2.1); treatment-start thresholds are higher than diagnosis thresholds
(Table 2, §3.1); screening all adults >18 with cadence per §3.3/Table 4. In
2026-08-17 the SSOT's interim default wins; the ESC/ESH candidates below stay
profile-selectable only after independent pins, and only if the project owner
keeps them in scope.

**ESC 2024 candidate classification (not a default):** non-elevated, elevated,
and hypertension using office BP. The exact boundaries and treatment target
require a source record and explicit population scope. Out-of-office thresholds
must be separate observables and must not be pooled with office measurements.

**ESH 2023 candidate classification (not a default — requires an explicit SSOT
decision):** Grade 1, Grade 2, and Grade 3 by BP range, with stage/risk concepts
incorporating HMOD, CKD, diabetes, and established CVD. The fact that diabetes
places a patient in an ESH stage does not mean Noor should infer HMOD or an
acute complication.

Every BP observation must preserve setting, posture, arm, cuff size, rest
duration, reading ordinal, average status, device class, and timestamp. An
orthostatic assessment is a linked set of supine and standing observations at
the specified times, not a single invented "orthostatic drop" observation.

### 2.2 Cardiac HMOD

Candidate domains are LVH, diastolic dysfunction, HFpEF, HFrEF, atrial
fibrillation, CAD, valve disease, and aortic disease. LVH requires a documented
ECG or echocardiographic criterion and method. Heart failure requires a
clinician-documented diagnosis or a separately governed diagnostic pathway;
pedal oedema alone is not sufficient.

### 2.3 Cerebrovascular HMOD

Relevant conditions include ischaemic stroke, intracerebral haemorrhage,
subarachnoid haemorrhage, TIA, and hypertensive encephalopathy. Noor's stroke
red flag must use structured new focal neurological findings or a provider-
approved stroke screen. A headache or high BP alone must not be labelled stroke.

### 2.4 Renal HMOD

Hypertensive nephrosclerosis is often an exclusion-based clinical diagnosis. It
must not be inferred automatically from hypertension plus low eGFR or low-grade
proteinuria. Noor may record a clinician-documented suspected or established
cause and use the shared KDIGO G/A staging pathway (see `diabetes-research.md`
§3.2), while preserving uncertainty and alternative causes.

### 2.5 Ocular HMOD

Keith-Wagener-Barker grades are legacy descriptive findings. Grades I-II may
support chronic vascular risk review; grades III-IV may support acute target-
organ-damage assessment. Neither grade alone is a complete hypertensive
emergency diagnosis. The overall clinical picture, BP context, and clinician-
documented acute damage are required.

### 2.6 Vascular HMOD

Aortic aneurysm, dissection, and intramural haematoma are clinician-diagnosed
conditions. Sudden severe chest, back, or abdominal pain with pulse or neurologic
asymmetry belongs in the provider's emergency pathway, not in a chronic HMOD
classification rule.

### 2.7 Hypertensive emergency and severe hypertension

**Hypertensive emergency** means severe BP elevation with acute target-organ
damage. The emergency rule must evaluate acute brain, heart, kidney, eye, or
aortic findings. BP alone is insufficient.

**Severe hypertension without acute target-organ damage** should be represented
using the selected current terminology and source family — NHC/SHA 2023 §3.7
(pinned candidate, `guideline-pin-register.md` §1) until a profile
independently selects ACC/AHA 2025 or ESC 2024. The legacy term "hypertensive
urgency" and newer "severe hypertension" label must not be silently treated as
identical pathways. No universal 24-48 hour action should be encoded without
provider-approved policy and source support.

Candidate emergency signals include focal neurologic deficit, altered mental
status, seizure, acute pulmonary oedema, acute coronary syndrome, aortic
dissection features, acute kidney injury with compatible context, retinal
acute damage, and pregnancy-specific emergency findings where pregnancy is in
scope. Each signal needs its own source and explicit exclusions.

### 2.8 BP treatment targets and first-line agent selection by compelling indication

This section fills the roadmap's "BP target + first-line agent by compelling
indication (e.g. CKD → ACEi/ARB)" row. **It is a guideline claim, not a label
claim** — `source_family: guideline` per SSOT §7.3, pinned against the named
guideline documents below, never against a SmPC. The values recorded are
**source-populated but non-authorable**: they become thresholds only after the
threshold records receive Noor clinical approval, exactly as with the Umpierrez
boundaries in `diabetes-research.md` §2.

**Per §2.1, Noor must select and pin one source family per tenant and domain —
it must not blend ESC and ESH target systems.** That choice is material here
because the two families diverge on structure *and* on beta-blockers: ESC 2024
makes beta-blockers **third-line** (after a mineralocorticoid antagonist),
reserved for compelling indications; ESH 2023 retains beta-blockers among
first-line classes. The compelling-indication table in §2.8.2 is largely robust
to either choice — beta-blockers *with* a compelling indication are Class I in
both — but the "first-line for uncomplicated hypertension" statement and every
target number are not.

#### 2.8.1 Candidate source records and target positions (drafted, not pinned)

| Source | Document and revision | Position as recorded | Status |
|---|---|---|---|
| ESC | *2024 ESC Guidelines for the Management of Elevated Blood Pressure and Hypertension*, European Heart Journal, published 2024-08-30; press release and PharmaPulse summary consulted, section 6.5 (targets) and 6.4 (initiation) | Classification: non-elevated (<120/70), elevated BP (120–139/70–89), hypertension (≥140/90). **Target: SBP 120–129 mmHg for most adults on pharmacotherapy** (Class I), provided treatment is well tolerated; otherwise "as low as reasonably achievable" (ALARA) in frail, older, or intolerant patients (Class I). DBP target 70–79 mmHg (Class 2b). Initiation: all confirmed hypertension (Class I); also elevated BP with sufficiently high CVD risk and repeated ≥130/80 despite 3 months of lifestyle measures (Class I). First-line classes: ACEi, ARB, dihydropyridine CCB, thiazide/thiazide-like diuretic (Class I). Beta-blockers third-line unless compelling indication. Upfront two-drug low-dose combination for most patients (Class I); monotherapy option for ≥85 years, moderate/severe frailty, symptomatic orthostatic hypotension, and high-risk elevated BP (130–139/80–89) | Source-populated, not clinician-approved |
| ESH | *2023 ESH Guidelines for the Management of Arterial Hypertension*, Journal of Hypertension 2023;41(12):1874–2071, doi:10.1097/hjh.0000000000003480; classification table verified against the journal page, target summary via secondary literature | Classification: optimal <120/<80; normal 120–129/80–84; high-normal 130–139/85–89; Grade 1–3; isolated systolic hypertension ≥140/<90. Targets as summarized in secondary literature: 120–129/80 for ages 18–64; <140/80 for 65–79 (120–129 may be considered if tolerated); SBP 140–150 for ≥80. **Verify the target band text directly against the guideline before pinning — the classification table is verified, the targets are not yet** | Source-populated (classification), `unretrieved` (targets) |
| KDIGO | *KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of CKD*, Kidney International 2024;105(4S), March 2024; BP chapter endorses the KDIGO BP-in-CKD position | **CKD with hypertension: aim SBP <120 mmHg (standardized office BP), individualized in frailty, high fall/fracture risk, very limited life expectancy, or symptomatic postural hypotension. First-line: ACEi or ARB (RASi) at maximum tolerated dose.** Even mild albuminuria indicates RASi benefit in CKD without diabetes; severe albuminuria indicates substantial SGLT2i benefit; RASi + SGLT2i delay progression | Source-populated, not clinician-approved |

Every number above is a **band or a boundary that needs its three §12.3 case
rows (at / just below / just above)** when it becomes a rule — "120–129" is a
range, and ranges need an explicit at-boundary convention like every other
threshold in this file. Note also that "tolerated" (ESC) and "frailty" (both)
are not observables: whichever family is pinned, the rule must declare what it
reads instead (e.g., documented adverse-effect report, documented frailty
assessment) or state that the exception lane is provider-determined.

#### 2.8.2 First-line agent by compelling indication (draft mapping)

Compelling indications are **clinician-documented conditions** (per the content
contract and §2.2–§2.6) — never inferred from a risk factor or a single
symptom. Agents are restricted to this catalogue (SEML §12/§13; all 34
verified). This table is the research draft; the recommendation itself needs
the pinned guideline family's section locator per row.

| Compelling indication (clinician-documented) | First-line class(es) | SEML-available agents in this catalogue | Notes |
|---|---|---|---|
| CKD with albuminuria (A2/A3; KDIGO staging, `diabetes-research.md` §3.2) | ACEi or ARB at maximum tolerated dose | lisinopril, captopril, enalapril, losartan | KDIGO + ESC/ESH. Never dual RAAS blockade (§8 — VA NEPHRON-D). K+/eGFR 7–14 day follow-up applies (§13.3). The eGFR-decline tolerance is a two-observable rule (§9.2) |
| CKD (diabetic or non-diabetic) with albuminuria | add SGLT2i regardless of BP | empagliflozin (diabetes catalogue §10.4, §14.3) | Cardiorenal benefit, not BP; empagliflozin is `strength_achievable` at 10/25 mg |
| HFrEF | ACEi (or ARB if ACEi-intolerant) + beta-blocker + MRA + SGLT2i | enalapril, captopril, lisinopril / losartan; carvedilol, metoprolol succinate; spironolactone; empagliflozin | ARNI (sacubitril/valsartan) is **not on the SEML** (§8.2) — the HFrEF combination this catalogue can actually deliver excludes it. Carvedilol and metoprolol succinate are the HF-indicated beta-blockers (§10.1). Spironolactone baseline-eligibility and K⁺ bands apply (§9.3) |
| Post-myocardial infarction | Beta-blocker + ACEi | metoprolol tartrate, carvedilol, propranolol + ACEi | ESC Class I; never stop a beta-blocker abruptly (§10.1) |
| Angina pectoris | Beta-blocker or dihydropyridine CCB | metoprolol, carvedilol, propranolol; amlodipine, nifedipine ER | ESC Class I. Nifedipine IR is contraindicated in ACS (§10.1) — formulation matters |
| Atrial fibrillation, rate control | Beta-blocker or non-DHP CCB | metoprolol, carvedilol; verapamil | Verapamil contraindicated with severe LV dysfunction (§10.1) |
| Elderly / frail (≥85, or documented frailty) | Monotherapy option; CCB or thiazide reasonable for isolated systolic hypertension | amlodipine, nifedipine ER, HCTZ | ESC monotherapy allowance; the ESH ≥80 target band differs from the general target — the pinned family decides |
| Pregnancy (hypertension of pregnancy / pre-eclampsia) | Methyldopa, hydralazine, nifedipine | methyldopa, hydralazine, nifedipine | Labetalol is **not on the SEML**; hydralazine IV is `unachievable` (§12). Methyldopa is the drug of choice (§10.2). Nifedipine IR contraindicated before week 20 (§9.1) |
| Diabetes without albuminuria | Any first-line class | ACEi/ARB, CCB, HCTZ | No class preference absent albuminuria (ESC 2024); the general first-line set applies |
| Gout history | Avoid thiazide | HCTZ raises uric acid and can precipitate attacks (§10.3) | Drafting consideration, not yet a sourced recommendation |
| Asthma / COPD | Avoid non-selective beta-blockers | propranolol, carvedilol contraindicated (§10.1) | Drafting consideration; β1-selective agents less risky but still cautioned |
| Severe LV dysfunction | Avoid non-DHP CCB | verapamil (§10.1) | Drafting consideration |

#### 2.8.3 Structural requirements before any of this becomes a rule

- **Measurement context is part of the threshold.** The ESC SBP target is
  predicated on standardized office measurement and strengthened out-of-office
  verification; out-of-office thresholds are separate observables and must not
  be pooled with office readings (§2.1).
- **The target is a range, not a point.** "120–129" needs an at-boundary
  convention and three rows per boundary (§12.3), plus a missing-data row —
  a home visit with no recent BP is the common case (§8.3 degradation).
- **Two distinct rule shapes live here.** "BP above target → intensify" is a
  monitoring rule; "compelling indication present but first-line class absent
  from the regimen → recommend" is a treatment-gap rule. They have different
  requirements, severities, and test rows.
- **Guideline claims pin per SSOT §7.3** (`source_family: guideline`) with
  organisation, document, revision date, and section locator — the rows in
  §2.8.1 supply the first three fields where verified; the section locators
  remain the pinning work item.
- **The divergence between ESC 2024 and ESH 2023 is not an implementation
  detail.** The beta-blocker first-line question changes which rules exist;
  the tenant must pin one family before any §2.8 content is authored.

---

## 3. Red-Flag Libraries — Hypertensive Emergency, ACS, and Stroke

SSOT §11.7 requires five governed red-flag libraries. **This file owns three of
them; the other two (DKA/HHS and severe hypoglycaemia) are tracked in
`diabetes-research.md` §4.** Red-flag thresholds are never written from memory,
and the values below are therefore recorded as **`status: unpopulated`** with
the action they will trigger, not as thresholds. Each needs an organisation,
document, version, and locator before CI gate 2 will pass it, and each needs the
three `.cases.yaml` rows (at / just below / just above) from SSOT §12.3 written
*before* the rule.

**Source pins (2026-08-17):** the source family for this file's three libraries
is pinned as a candidate — NHC/SHA 2023 §3.7 for hypertensive-emergency
terminology, ESC 2023 ACS (doi 10.1093/eurheartj/ehad191) for ACS recognition,
and AHA/ASA F.A.S.T. + the 2026 AIS guideline for stroke recognition — with
proposition-level records in `guideline-pin-register.md` §1, §4, §5. The values
below stay `unpopulated` until the threshold records pass clinical approval.

| Library | Emergency activation must consider | Repeat/review must remain separate |
|---|---|---|
| Hypertensive emergency | Severe BP plus acute brain, heart, kidney, eye, or aortic damage | Severe BP without damage; isolated unreliable reading |
| ACS | New concerning chest or equivalent symptoms, ischemic signs, or provider-approved ECG/troponin pathway | Atypical or uncertain symptoms without emergency features; abnormal value requiring confirmation |
| Stroke | New focal deficit or provider-approved stroke-screen finding with time last known well | Non-focal dizziness/headache without deficit, or uncertain history requiring review |

| Red flag | Observable | Value | Status | Action once cited |
|---|---|---|---|---|
| Hypertensive emergency | systolic and diastolic BP **+** evidence of acute target-organ damage | ⛔ `unpopulated` | `unpopulated` | Emergency hatch. A BP number alone is hypertensive *urgency*, not emergency, and the two have different destinations. A BP-only trigger in a home visit will fire constantly and be dismissed — alert fatigue that costs the rules around it their credibility |
| Acute coronary syndrome | symptom cluster; ECG where available | ⛔ `unpopulated` | `unpopulated` | Emergency hatch. Symptom-based, not threshold-based. Presentation is frequently atypical in the diabetic elderly — the population this catalogue is for — so a chest-pain-anchored trigger under-detects exactly where it is needed most |
| Stroke | focal deficit onset **+** time of onset | ⛔ `unpopulated` | `unpopulated` | Transfer at `stop_and_review` — the strongest of §9.1's three severities, and still not a block. Time of onset is the operative field, because it gates thrombolysis. Alteplase is on the SEML (§12.6.2) but is not a home-visit medicine — this flag's only correct output is transfer |

For ACS and stroke, this file must not invent a numeric troponin cutoff,
ECG interpretation, stroke score, or time window. Those are source- and
provider-dependent content requiring separate governance. The absence of a
numeric threshold does not justify a passive rule when symptoms are concerning.

### 3.1 ACS library specification

The candidate structured presentation includes chest pressure, tightness,
heaviness or discomfort; discomfort in the arm, shoulder, back, neck, jaw, or
epigastrium; acute dyspnoea; diaphoresis; nausea or vomiting; syncope; and sudden
unexplained weakness. Diabetes, older age, CKD, and sex may affect presentation,
but they do not permit Noor to diagnose ACS from an atypical symptom alone.

The library must preserve symptom onset, current versus resolved state,
duration, recurrence, exertional relationship, associated symptoms, known CAD,
and any ECG or troponin provenance. A laboratory-specific troponin assay and its
upper reference limit are distinct from a universal number. Serial change,
timing from symptom onset, ECG interpretation, and alternative diagnoses require
a separately sourced pathway. A normal home vital sign or absent chest pain
must not exclude ACS when other concerning features are present.

Explicit exclusions are not a list of diagnoses Noor rules out. They are
conditions under which the ACS-specific rule cannot conclude, such as a missing
symptom onset time, uninterpreted ECG, assay-ambiguous troponin, or contradictory
reports. Those states produce review or `indeterminate`, not reassurance.

### 3.2 Stroke library specification

The candidate structured presentation includes new unilateral face, arm, or leg
weakness or numbness; new speech or language disturbance; new visual loss or
field deficit; new severe gait or coordination disturbance; neglect; and altered
consciousness. The record must capture time last known well, time first noticed,
who observed the deficit, anticoagulant exposure, glucose at assessment, recent
head trauma, seizure at onset, and whether symptoms resolved.

Hypoglycaemia can mimic stroke, but checking glucose must not become a gate that
delays emergency activation. A resolved focal deficit remains compatible with
TIA and still requires the provider-approved urgent pathway. Dizziness,
headache, or confusion without focal findings may still be serious, but Noor
must not label them stroke without a separately governed clinical pathway.

Noor may store the result of a provider-approved stroke screen with its version,
items, administrator, and timestamp. It must not reproduce a protected
instrument or derive a score whose licence and clinical workflow have not been
approved.

### 3.3 Red-flag data-quality behavior

An extreme value that fails `canon` plausibility review is not discarded. If the
clinician verifies it as real, it enters as `clinically_exceptional_accepted`.
If uncertainty remains and the situation is non-emergent, the system records the
original and repeat. If symptoms or clinical judgement indicate an emergency,
the hatch remains available before, during, and after verification.

---

## 4. Screening and Monitoring

The following are domains for monitoring content, not universal fixed schedules.
Each future `monitors` entry must pin the source label or guideline, eligible
population, maximum age for using a result, due interval, exceptions, and
obligation behavior. Shared rows are duplicated deliberately so each file
stands alone; glycaemia monitoring specifics are in `diabetes-research.md` §5.

| Domain | Candidate observation | Required stratification |
|---|---|---|
| BP | Office, home, or ambulatory BP | Setting, treatment change, target profile, orthostatic risk |
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

## 5. Terminology and Coding Boundary

Noor uses LOINC and UCUM for observations, SNOMED CT for clinical meaning, and
ICD-10-AM only at the NPHIES/billing boundary as specified by the SSOT. The
ICD-10-CM examples below are orientation only and must not be treated as Saudi
coding instructions.

### 5.1 Coding cautions — hypertension and cardiovascular disease

- Diabetes and hypertension are generally coded separately. Do not infer a
  causal diabetes-to-hypertension relationship from co-occurrence.
- Hypertension has presumed causal relationships with hypertensive heart disease
  and hypertensive CKD under ICD-10-CM conventions, but the applicable code
  combination must be checked against the current official guideline.
- Diabetic CKD, hypertensive CKD, and combined hypertensive heart-and-CKD coding
  are not interchangeable. They may require diabetes, hypertension/combination,
  and N18 stage codes depending on the documented diagnoses.
- `N18.1` through `N18.5` represent CKD stages 1 through 5; `N18.6` is ESRD.
- Stroke, ACS, PAD, and hypertensive heart/renal disease need mapped
  clinical concepts, not only broad ICD code ranges.
- A coding system is not a clinical severity system. Codes must never be used
  as a substitute for the red-flag criteria or clinical documentation.

### 5.2 Required mapping record

Every mapped concept must retain the source display, terminology release,
mapping method, confidence, and mapped code. Ambiguous or unmapped concepts are
visible workflow states and cannot silently enter the engine.

---

# Part B — Pharmacotherapy: Hypertension

## 6. Regulatory and Clinical Architecture Overview

Clinical Decision Support (CDS) engines require rigid evidence bases and precise
regulatory alignment to deliver actionable, safety-critical alerts at the point
of care. Within the Kingdom of Saudi Arabia, the Saudi Food and Drug Authority
(SFDA) registers therapeutic agents and publishes Summary of Product
Characteristics (SmPC) standards that are harmonized directly with the European
Medicines Agency (EMA) and the International Council for Harmonisation (ICH)
frameworks. Consequently, constructing deterministic safety rules for
cardiovascular agents listed on the Saudi Essential Medicines List 2023 (SEML)
necessitates pulling pharmacovigilance thresholds, renal adjustment metrics,
hepatic safety parameters, and monitoring obligations directly from EMA/ICH
SmPC guidelines.

Every pharmacological agent listed on the SEML possesses a structural
Anatomical Therapeutic Chemical (ATC) classification and defined physiological
thresholds. Synthesizing these regulatory parameters enables CDS architecture to
construct execution logic that mitigates severe adverse events — including
hyperkalaemia, AKI, severe hypotension, and arrhythmia — in vulnerable
home-care patient cohorts.

### 6.1 Data flow: patient profile → CDS safety rules engine

```
                          [Patient Profile Data]
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                             ▼
   [Renal Function Metric]                      [Hepatic Function Metric]
   ├── eGFR (mL/min/1.73m²)                      └── Child-Pugh Score (A/B/C)
   └── CrCl (mL/min, Cockcroft-Gault)                (Avoid ALT/AST Transaminases)
              │                                             │
              └─────────────────────┬─────────────────────┘
                                    ▼
                       [CDS Safety Rules Engine]
                                    │
      ┌──────────────────────────────┼──────────────────────────────┐
      ▼                              ▼                              ▼
[Dose Ceilings / CIs]     [Polypharmacy Interactions]     [Temporal Protocol Obligations]
(e.g., eGFR <30 mL/min)   (e.g., CYP2D6/CYP3A4 Cascades)  (e.g., Day 7-14 K+/eGFR Re-check)
```

---

## 7. Quantitative Renal and Hepatic Dosing Principles

A primary failure mode in clinical informatics is the conflation of renal
function units. Regulatory SmPCs explicitly differentiate between **Estimated
Glomerular Filtration Rate (eGFR)**, normalized to body surface area in
mL/min/1.73m², and **Creatinine Clearance (CrCl)**, unadjusted absolute
clearance in mL/min calculated via Cockcroft-Gault. In elderly home-care
populations characterized by sarcopenia and low muscle mass, eGFR frequently
overestimates true absolute clearance, leading to drug accumulation if applied
to narrow therapeutic index agents like digoxin or milrinone whose labels
specify CrCl thresholds. Conversely, RAAS inhibitors (ACE inhibitors and ARBs)
define nephrotoxicity thresholds and hyperkalemia safety cutoffs primarily
using eGFR.

**Noor's eGFR equation is not chosen here.** SSOT §5.2 pins the **2021 CKD-EPI
creatinine equation without race** for any Noor-derived eGFR, stores the reporting
laboratory's `reported_egfr` and `reported_equation` separately, and never
recomputes a historical value under a different equation. And eGFR and CrCl are
two **distinct observables**, not two views of one number — CI gate 15 makes
`renal_metric` mandatory on every renal-dosing rule for exactly this reason. Two
consequences this file has to respect and a prior revision did not:

- **A band may not be written with a slash or a parenthetical equivalence.**
  "eGFR <30 mL/min/1.73m² (CrCl <30 mL/min)" asserts the two are interchangeable
  at the boundary. They are not, and in the sarcopenic 80-year-old the gap is
  exactly where the dosing decision changes.
- **A band expressed in the wrong metric is a defect even when the number is
  right.** Where a label states CrCl, the rule declares CrCl. Restating it in
  eGFR because eGFR is what the lab reports inverts the label.

Similarly, hepatic dosing safety rules cannot rely on serum transaminases (ALT
or AST). Transaminases reflect acute hepatocellular injury rather than
functional drug clearance capability. SmPC section 4.2 guidelines mandate
stratification using the **Child-Pugh classification system** (incorporating
serum bilirubin, serum albumin, INR, ascites, and hepatic encephalopathy). For
lipophilic agents undergoing extensive hepatic first-pass extraction (e.g.,
metoprolol, propranolol, carvedilol), advanced cirrhosis (Child-Pugh Class B or
C) increases systemic bioavailability by several fold, turning standard
therapeutic doses into severe hypotensive hazards.

Furthermore, clinical decision algorithms must incorporate **temporal
monitoring obligations** rather than static contraindication checks alone.
Initiating or titrating RAAS modulators or mineralocorticoid receptor
antagonists (MRAs) introduces an absolute obligation to perform repeat
laboratory evaluations of serum potassium and eGFR between 7 and 14 days
post-initiation. The failure to enforce these temporal monitoring windows
represents a major source of preventable emergency hospitalizations among
polypharmacy patients.

Renal metric selection is **not a runtime rule and does not belong in a rule
table.** It is **CI gate 15** (SSOT §10.4): every renal-dosing rule declares
`renal_metric`, and the compiler refuses one that does not. Enforced at build
time, it cannot be violated at run time — as a runtime rule it would be both
redundant and unable to fail closed.

---

## 8. Geriatric Polypharmacy, Pharmacodynamics, and Maternal-Fetal Safety

Elderly patients enrolled in home-care programs frequently present with complex
multimorbidity, receiving complex polypharmacy regimens that elevate the risk
of dangerous drug-drug interactions. CDS engines must maintain dedicated rule
libraries targeting severe, clinically relevant interactions rather than
generating general interaction database dumps that induce alert fatigue.

**Key interaction clusters in geriatric cardiovascular management.** Each is
annotated with whether the *interacting partner* is on the SEML, because a rule
whose partner is unavailable in Saudi Arabia can never fire in this population
and is not worth authoring first (SSOT §3.2, local formulary):

- **CYP2D6 inhibition + metoprolol:** impaired clearance elevates metoprolol
  plasma concentration multiple fold, precipitating sinus bradycardia, high-
  grade AV block, and orthostatic collapse. **Anchor on fluoxetine (§16.2.1,
  `Capsule: 20 mg`) — the SEML CYP2D6-inhibiting SSRI. Citalopram and paroxetine
  are not on the SEML; escitalopram (§16.2.1) is** — firable.
- **CYP2C19 inhibition + clopidogrel:** esomeprazole is on the SEML (§14.1) so
  the alert fires; **pantoprazole is *not* on the SEML**, so "switch to
  pantoprazole" recommends an unavailable drug (SSOT §R-2). The SEML non-CYP2C19
  acid suppressant is famotidine (§14.1) — an H2 antagonist, not a PPI, so
  substituting it is a therapeutic downgrade the prescriber must decide on, not
  a swap the engine can assert. The honest card states the interaction and the
  two available options with that tradeoff named; it does not name a winner.
- **RAAS inhibition + MRA (spironolactone):** potentially fatal hyperkalemia,
  especially with renal impairment — lisinopril, captopril, enalapril, losartan
  and spironolactone are all on the SEML. This combination is sometimes used
  deliberately for proteinuria/HF benefit under close monitoring (real trial
  evidence exists), which makes explicit potassium-monitoring logic more
  important, not less, than a blanket "don't combine" rule.
- **Dual RAAS blockade (ACE inhibitor + losartan):** significantly increases
  hyperkalemia, hypotension, and AKI risk with no added benefit. **The VA
  NEPHRON-D trial (losartan + lisinopril in diabetic nephropathy) was stopped
  early for exactly this reason** — not a theoretical interaction, a
  trial-terminating one — and both drugs are on this same catalogue. Firable.
- **P-glycoprotein inhibition + digoxin:** amiodarone and verapamil double
  digoxin concentration via P-gp inhibition — both on the SEML, firable.
  **Quinidine is not on the SEML** — unfirable.
- **Y-site incompatibility, milrinone + furosemide:** co-infusing in a shared
  IV line causes immediate chemical precipitation, obstructing vascular access
  and disrupting vasoactive therapy. Both on the SEML — firable.
- **Nifedipine + IV magnesium sulfate:** dual neuromuscular and vascular
  blockade can produce unpredictable maternal hypotension and severe fetal
  hypoxia. Magnesium sulfate is on the SEML, so this rule is firable — at
  `stop_and_review`, the strongest of §9.1's three severities. A prior revision
  called for a "strict hard-stop"; the engine has none, and inventing one here
  would contradict the ladder the whole catalogue is built on.
- **NSAID + RAAS inhibitor + diuretic ("triple whammy"):** the classic AKI
  pattern, one of the most preventable admissions in this population. NSAIDs
  are over-the-counter, so the rule must trigger on the reconciled medication
  list, not the dispensing record.
- **Nitrates + PDE-5 inhibitors:** absolutely contraindicated — synergistic
  vasodilation can be fatal. **Neither sildenafil nor tadalafil is on the SEML**,
  but PDE-5 inhibitors are among the most common non-formulary and
  privately-obtained medicines in this population, so the rule must trigger on
  the reconciled medication list. Timing matters: avoid sildenafil/vardenafil
  within 24h and tadalafil within 48h of nitrate use.
- **Non-selective beta-blockers + insulin or gliclazide:** masked hypoglycaemia
  symptoms (tachycardia, tremor) — cross-disease pair with the diabetes
  catalogue (`diabetes-research.md`). Propranolol and carvedilol are the
  non-selective agents here.
- **Furosemide + digoxin:** furosemide's potassium-depleting effect raises
  digoxin toxicity risk — a very common real-world combination (loop diuretic +
  digoxin in HF), and a higher-value rule than either drug's isolated profile.
- **Atorvastatin + verapamil or amiodarone:** CYP3A4 inhibition raises
  atorvastatin levels roughly 2–3x, increasing myopathy/rhabdomyolysis risk;
  sources suggest capping atorvastatin at 20 mg/day if the combination is
  necessary. All three on the SEML — firable. A published case report describes
  rhabdomyolysis, AKI, and transaminitis from the three-way statin + amiodarone
  + ticagrelor interaction.
- **Alteplase + ACE inhibitor:** orolingual angioedema — one study found an
  odds ratio of 7.72 for severe angioedema in ACE-inhibitor users receiving
  alteplase, mechanism plasmin-driven bradykinin accumulation (the same pathway
  that causes ACEi cough). Any patient on lisinopril, captopril, or enalapril
  who might receive alteplase is a meaningfully higher angioedema risk.
- **Epinephrine + non-selective beta-blocker (propranolol):** unopposed alpha-1
  vasoconstriction produces severe hypertension with reflex bradycardia,
  potentially progressing to stroke or cardiac arrest. Despite the theoretical
  risk, emergency-medicine literature is clear that epinephrine should still be
  given at the standard dose for anaphylaxis in a beta-blocker patient — glucagon
  is the described second-line option, which is a second link back to the
  diabetes catalogue's glucagon entry. The flag should soften guidance toward
  "give anyway, but be prepared to also administer glucagon," not toward
  withholding.
- **Ticagrelor + aspirin >100 mg/day:** maintenance aspirin dose must stay at
  75–100 mg/day — above 100 mg measurably reduces ticagrelor's effectiveness
  (PLATO trial). An unusual "more of drug A makes drug B worse" interaction,
  and a clean dose-ceiling rule if aspirin dose is tracked (not just
  presence/absence).
- **Hydralazine + beta-blocker + diuretic:** an *intentional* combination to
  offset reflex tachycardia and fluid retention — a "usually fine together"
  pattern worth documenting alongside the danger-flagged ones (a
  "usually-combined-with" pattern, not only a danger list).

### 8.1 Cross-category interaction map

This catalogue has an unusual density of drugs that are dangerous specifically
*together*. Every combination below is between agents already on the SEML unless
stated otherwise:

| Combination | Risk | Members |
|---|---|---|
| **Verapamil + metoprolol/carvedilol (IV, or aggressive oral titration)** | Additive AV-nodal depression → severe bradycardia/heart block, worsened heart failure | §9.1 |
| **Digoxin + amiodarone** | Amiodarone raises digoxin levels — classic cause of digoxin toxicity | §9.4 |
| **Digoxin + verapamil** | Same mechanism — raised digoxin levels | §9.1/§9.4 |
| **Digoxin or verapamil + adenosine** | Rare but specifically labeled risk of ventricular fibrillation | §9.1/§9.4 |
| **Carvedilol + digoxin/amiodarone** | Significantly slows heart rate and AV conduction beyond either agent alone | §9.1/§9.4 |
| **Metoprolol succinate + verapamil or digoxin** | Additive bradycardia/AV depression (label names glycosides, clonidine, diltiazem, verapamil) | §9.1/§9.4 |
| **Nitrates + PDE-5 inhibitor** | Contraindicated — severe/fatal hypotension; trigger on reconciled list | §9.1 |
| **Nitrates + verapamil/nifedipine/amlodipine** | Additive orthostatic hypotension | §9.1 |
| **Nifedipine (immediate-release) + acute coronary syndrome** | Contraindicated formulation/context combination, independent of any second drug | §9.1 |
| **ACE inhibitor or ARB + spironolactone** | Potentially fatal hyperkalemia, especially with renal impairment | §9.2/§9.3 |
| **ACE inhibitor + losartan (dual RAAS blockade)** | Hyperkalemia, hypotension, AKI — trial-terminating evidence (VA NEPHRON-D) | §9.2 |
| **ACEi/ARB + diuretic + NSAID ("triple whammy")** | AKI — classic, well-documented pattern; NSAIDs enter via reconciled list | §9.2/§9.3 |
| **Furosemide + digoxin** | Hypokalemia potentiates digoxin toxicity | §9.3/§9.4 |
| **Any thiazide/loop diuretic + digoxin** | Same hypokalemia-potentiates-toxicity mechanism | §9.3/§9.4 |
| **Propranolol or metoprolol succinate + insulin/sulfonylurea (gliclazide)** | Masked hypoglycemia symptoms — cross-disease to diabetes catalogue | §9.1 + diabetes |
| **Epinephrine + propranolol (non-selective beta-blocker)** | Unopposed alpha vasoconstriction → hypertensive crisis; also blunts epinephrine's anaphylaxis efficacy | §9.5 |
| **Alteplase + ACE inhibitor (lisinopril/captopril/enalapril)** | OR 7.72 for severe orolingual angioedema — same bradykinin mechanism as ACEi cough | §9.2/§9.6 |
| **Alteplase + aspirin/clopidogrel or any anticoagulant** | Increased hemorrhagic transformation/ICH risk | §9.6 |
| **Alteplase in a diabetic or hypertensive patient** | Both independently raise hemorrhagic-transformation risk | §9.6 + diabetes |
| **Atorvastatin + verapamil or amiodarone** | CYP3A4 inhibition → 2–3x atorvastatin levels → myopathy/rhabdomyolysis risk | §9.1/§9.4 |
| **Ticagrelor + aspirin >100 mg/day** | Reduces ticagrelor's own effectiveness — a dose-ceiling rule, not a danger-flag rule | §9.6 |
| **Clopidogrel + esomeprazole** | CYP2C19 inhibition blunts clopidogrel's antiplatelet effect | §9.6 |
| **Tirofiban in a diabetic, CKD, or heart-failure patient** | All three independently raise thrombocytopenia risk | §9.6 + diabetes |
| **Dopamine/norepinephrine/vasopressin in a PAD/occlusive-vascular-disease patient** | Elevated gangrene/digital ischemia risk — diabetic macrovascular disease is the population | §9.5 + diabetes |
| **Hydralazine + beta-blocker + diuretic** | *Intentional* combination — "usually fine together," documented alongside the danger-flagged ones | §9.2 internal |

### 8.2 Interaction partners absent from the SEML — rules that cannot fire

Authoring these first would produce a catalogue that looks complete and detects
nothing. Recorded so the omission is deliberate rather than forgotten:

**simvastatin · pantoprazole · omeprazole · cimetidine · citalopram · paroxetine ·
gemfibrozil · aliskiren · sacubitril/valsartan · sildenafil · tadalafil · MAOIs ·
tricyclic antidepressants · dipyridamole · mexiletine · quinidine · indomethacin ·
danazol · chlorpromazine**

Two exceptions worth authoring anyway, both for the same reason — the SEML records
what the *system* stocks, not what the *patient takes*:

- **PDE-5 inhibitors with nitrates.** Commonly obtained privately. Trigger on
  the reconciled medication list.
- **NSAIDs with RAAS inhibitors or diuretics.** Over-the-counter, and the
  triple-whammy AKI it causes is one of the most preventable admissions in this
  population.

---

## 9. Comprehensive Clinical and Regulatory Matrix

Every renal and hepatic value below is a **draft awaiting a label pin** (see
*Implementation status*). The SEML column is the one verified column.
Per-ingredient complication profiles follow in §10.

The renal column is deliberately headed "Renal Dosing Guidance (metric named per
cell)" — no metric in the heading. Each cell names its own observable, or says it
cannot (SSOT §5.2, CI gate 15).

**Data-model notes that carry across all six categories:**

- **Formulation matters more than ingredient name** in at least two cases:
  nifedipine immediate-release vs. extended-release (§9.1) and metoprolol
  tartrate vs. succinate (§9.1). Decide early whether the data model treats
  these as one ingredient with variants or as distinct entities — it changes how
  contraindication rules attach.
- **The vasopressor/inotrope six (§9.5) are IV, ICU/ambulance-acuity drugs** — a
  meaningfully different context from the oral home-care formulary. If Noor's
  actual patient-facing scope is home visits rather than acute/inpatient care,
  these six are most useful for **medication-reconciliation and care-transition
  logic** (a patient discharged from ICU on a weaning inotrope, or an ambulance
  protocol reference) rather than active in-home dosing rules.

### 9.1 Category 1: Beta-Adrenergic Antagonists and Calcium Channel Blockers

Beta-adrenergic receptor antagonists and calcium channel blockers (CCBs)
constitute core first-line options for hypertension, angina pectoris, and rate
control. Lipophilic beta-blockers undergo major hepatic metabolism, whereas
hydrophilic agents rely heavily on renal elimination. Non-dihydropyridine
calcium channel blockers act as potent CYP3A4 and P-glycoprotein (P-gp)
inhibitors, generating complex polypharmacy interaction profiles in elderly
patients.

| Ingredient | ATC Code | Saudi SEML / label pin | Renal Dosing Guidance (metric named per cell) | Hepatic Dosing Guidance (Child-Pugh) | Major Interactions (Polypharmacy/Elderly) | Monitoring Interval | `pregnancy` proposition only — SmPC §4.6 |
|---|---|---|---|---|---|---|---|
| **Metoprolol Tartrate** | C07AB02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No adjustment required across eGFR or CrCl ranges | Reduce dose in severe hepatic impairment (Child-Pugh C); high first-pass clearance | CYP2D6 inhibitors double metoprolol exposure. **Anchor on fluoxetine (§16.2.1, `Capsule: 20 mg`) — the SEML CYP2D6-inhibiting SSRI. Citalopram and paroxetine are not on the SEML; escitalopram (§16.2.1) is** | HR and BP weekly during dose titration | Reduced placental perfusion; risk of fetal bradycardia, hypoglycemia, IUGR |
| **Metoprolol Succinate** | C07AB02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No adjustment required for renal impairment | Initiate at 12.5–25 mg daily in Child-Pugh B/C; slow clearance kinetics — **⚠ the SEML lists `Tablet: 50 mg, 100 mg` only. 12.5 mg is `unachievable`; 25 mg needs quartering a modified-release tablet, which destroys the release mechanism. This dose is not deliverable in Saudi Arabia and must route to pharmacist review, not render as an instruction** | Strong CYP2D6 inhibitors increase toxicity risk; additive AV block with verapamil | HR, BP, fluid retention signs every 1–2 weeks during titration | Decreases uterine blood flow; monitor fetal growth; discontinue 48–72h before delivery if possible |
| **Carvedilol** | C07AG02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dose adjustment required in mild-to-severe renal failure | Contraindicated in severe hepatic impairment (Child-Pugh B/C or manifest liver failure) | Increases digoxin trough concentrations by 20%; CYP2D6 and P-gp inhibition cascades | BP, HR, blood glucose (diabetics) every 1–2 weeks post-dose change | Embryotoxic in animal studies; fetal bradycardia and neonatal hypoglycemia risk; avoid during pregnancy |
| **Propranolol** | C07AA05 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Caution in severe renal impairment; lower initial doses due to altered clearance | Reduce initial dose by 50% in Child-Pugh B/C; significant reduction in first-pass metabolism | CYP1A2 and CYP2D6 inhibitors ↑ propranolol exposure.<br>**Mexiletine is not on the SEML** — the dysrhythmia-risk rule is unfirable | HR and BP weekly; blood glucose monitoring in diabetic home-care patients | Placental hypoperfusion; fetal hypoglycemia, bradycardia, respiratory depression at birth |
| **Verapamil HCl** | C08DA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Caution if eGFR <30 mL/min/1.73m²; parent drug and active metabolites accumulate | Reduce daily dose by 50–70% in Child-Pugh B/C; markedly prolonged elimination half-life | Strong P-gp and CYP3A4 inhibitor; increases digoxin levels by 50–70%; severe AV block with beta-blockers | HR, BP, ECG (PR interval) at day 7 and day 14 post-initiation | Crosses placenta; risk of fetal bradycardia, hypotension, uterine relaxation; use only if compelling |
| **Nifedipine** | C08CA05 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No adjustment required for renal dysfunction | Titrate carefully in Child-Pugh B/C; reduce extended-release maintenance dose by 50% | CYP3A4 inhibitors (clarithromycin, azoles) increase AUC; concurrent IV MgSO4 causes severe hypotension | BP, orthostatic vitals, peripheral edema at 1 and 2 weeks | Contraindicated before week 20; severe maternal hypotension and fetal hypoxia if combined with IV MgSO4 |
| **Amlodipine** | C08CA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No adjustment required in renal impairment or hemodialysis | Initiate at 2.5 mg daily in Child-Pugh A/B/C; clearance prolonged in liver impairment — **`achievable_by_division` only: the SEML lists `Tablet: 5 mg` and no 2.5 mg** | CYP3A4 inhibitors increase bioavailability (clarithromycin, azoles — both on SEML).<br>**Simvastatin is not on the SEML**, so the label's 20 mg simvastatin cap is unfirable; the SEML statin is atorvastatin (§12.7), which has its own, different CYP3A4 profile — do not transfer the cap to it | BP and lower extremity edema at 2 to 4 weeks post-titration | Safety in human pregnancy not established; potential for prolonged labor; use only when safer alternatives lack |
| **Glyceryl Trinitrate** | C01DA02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required in renal dysfunction | Caution in severe hepatic cirrhosis (Child-Pugh C); risk of methemoglobinemia | Absolute contraindication with PDE-5 inhibitors — **sildenafil and tadalafil are not on the SEML, so this rule cannot fire on SEML data alone. It is still worth authoring: PDE-5 inhibitors are among the most common non-formulary and privately-obtained medicines in this population, so the rule must trigger on the reconciled medication list, not the dispensing record** | BP and symptom relief; assess nitrate tolerance (10–12h nitrate-free window daily) | Animal studies insufficient; presence in breast milk unknown; prescribe only under critical maternal need |
| **Isosorbide Dinitrate** | C01DA08 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Caution in severe renal impairment; risk of systemic metabolite accumulation | Caution in severe Child-Pugh B/C hepatic impairment; reduced clearance capacity | Absolute contraindication with PDE-5 inhibitors; additive arterial vasodilation with antihypertensives | BP and orthostatic changes at baseline and day 7 post-initiation | No definitive human pregnancy data; maternal hypotension impairs uteroplacental perfusion |

#### Pharmacological analysis — Category 1

When configuring automated rule sets for beta-adrenergic blockers within
home-care environments, CYP2D6 metabolic cascades represent a critical safety
focus. In elderly patients taking metoprolol tartrate or succinate alongside
selective serotonin reuptake inhibitors such as citalopram or fluoxetine, CYP2D6
inhibition significantly impairs metoprolol clearance. This pharmacokinetic
interaction elevates metoprolol plasma concentration multiple fold, precipitating
sinus bradycardia, high-grade AV block, and orthostatic collapse. Clinical
decision support engines must trigger high-priority alerts when CYP2D6 inhibitors
are added to fixed-dose beta-blocker regimens.

For dihydropyridine calcium channel blockers, particularly nifedipine,
co-administration with parenteral magnesium sulfate in obstetrical hypertensive
emergencies introduces a major vascular risk. Dual neuromuscular and vascular
blockade can produce unpredictable maternal hypotension and severe fetal
hypoxia. Magnesium sulfate is on the SEML, so this rule is firable — at
`stop_and_review`, the strongest of §9.1's three severities. A prior revision
called for a "strict hard-stop"; the engine has none, and inventing one here
would contradict the ladder the whole catalogue is built on.

### 9.2 Category 2: Renin-Angiotensin-Aldosterone System Modulators and Centrally Acting Agents

RAAS inhibitors — comprising ACE inhibitors (ACEi) and Angiotensin II Receptor
Blockers (ARBs) — form the foundational pillar for managing hypertension,
diabetic nephropathy, and chronic heart failure. Centrally acting alpha-2
agonists and direct arterial vasodilators provide secondary options in
refractory hypertension and pregnancy-induced vascular disorders.

| Ingredient | ATC Code | Saudi SEML / label pin | Renal Dosing Guidance (metric named per cell) | Hepatic Dosing Guidance (Child-Pugh) | Major Interactions (Polypharmacy/Elderly) | Monitoring Interval | `pregnancy` proposition only — SmPC §4.6 |
|---|---|---|---|---|---|---|---|
| **Lisinopril** | C09AA03 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Initial dose 2.5–5 mg if eGFR <30 mL/min/1.73m²; excreted unchanged renally — **the 2.5 mg end is `achievable_by_division` only: the SEML lists `Tablet: 5 mg, 10 mg`** | No hepatic metabolism; no dosage adjustment required in liver disease | K+-sparing diuretics/K+ supplements cause hyperkalemia; NSAIDs reduce eGFR | Serum K+ and eGFR at 7–14 days post-initiation or titration | Contraindicated in 2nd/3rd trimesters; fetal renal failure, oligohydramnios, skull hypoplasia |
| **Captopril** | C09AA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | CrCl 20–50 mL/min: reduce dose by 25%; CrCl <20: reduce by 50% or extend interval | Caution in severe liver disease; half-life altered by fluid balance changes in cirrhosis | Dual RAAS blockade with ARBs (losartan is on the SEML — firable).<br>Lithium toxicity — lithium carbonate is on the SEML (§16.2.2) — firable.<br>**Aliskiren and sacubitril/valsartan are not on the SEML** — the 36h-washout rule is unfirable | eGFR, serum K+, WBC count (neutropenia risk) at 1–2 weeks | Teratogenic; severe fetal renal dysplasia, neonatal hypotension, death if exposed in 2nd/3rd trimesters |
| **Enalapril Maleate** | C09AA02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Start at 2.5 mg/day if eGFR <30 mL/min/1.73m² — **metric to confirm against the pinned label; do not restate it in CrCl.** A prior revision wrote "eGFR <30 mL/min/1.73m² (CrCl <30 mL/min)", equating two distinct observables | Hepatic conversion to enalaprilat decreased in cirrhosis, but dose driven by renal function | Absolute CI with aliskiren if eGFR <60 mL/min/1.73m² — **aliskiren is not on the SEML; unfirable**<br>NSAIDs blunt hypotensive effect | eGFR, serum K+, BP at day 7 and day 14 post-titration | Strictly contraindicated in 2nd/3rd trimesters; fetotoxicity, fetal hypotension, renal injury |
| **Losartan Potassium** | C09CA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No initial adjustment; monitor eGFR and K+ post-initiation (25% eGFR decline acceptable) | Initiate at 25 mg once daily in Child-Pugh A/B; reduced active metabolite (E-3174) conversion | Hyperkalemia risk with K+ supplements, spironolactone; NSAIDs cause acute kidney injury | eGFR and serum K+ mandatory re-check at 7 to 14 days post-initiation | Contraindicated during 2nd/3rd trimesters; damages fetal kidney development, causes oligohydramnios |
| **Methyldopa** | C02AB01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | **⚠ Metric mismatch — not authorable.** A prior revision wrote the interval-extension bands in eGFR (`10–50`, `<10 mL/min/1.73m²`). Methyldopa's renal guidance is a **CrCl** band in the label; restating it in eGFR because eGFR is what the lab reports inverts the source. Confirm the metric and the band against the pinned label, then declare `renal_metric: crcl` | Contraindicated in active hepatic disease (Child-Pugh B/C) due to severe hepatotoxicity risks | Additive CNS sedation with sedatives; blunts levodopa efficacy<br>MAOIs (severe hypertension) are **not on the SEML — unfirable** | LFTs, CBC (Coombs test) at baseline, 1 month, and 3 months post-initiation | Drug of choice for pregnancy-induced hypertension; extensive safety history; monitor infant |
| **Hydralazine** | C02DB02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | CrCl 10–50 mL/min: extend interval to q8h; CrCl <10: extend to q8–12h | Dose reduction required in Child-Pugh B/C; hepatic acetylation phenotype dictates clearance | Potentiates peripheral vasodilators; additive hypotensive collapse with nitrates. **MAOIs are not on the SEML** — unfirable | BP, HR, ANA titer (lupus-like syndrome risk during long-term maintenance) | Established safety in pregnancy-induced hypertension and pre-eclampsia; monitor fetal heart rate |

#### Pharmacological analysis — Category 2

A fundamental requirement for RAAS inhibition algorithms involves evaluating
post-initiation renal function shifts. Initiating enalapril, lisinopril, or
losartan alters glomerular hemodynamics by reducing efferent arteriolar
resistance. A self-limiting reduction in eGFR from baseline within 1 to 2 weeks
reflects expected intraglomerular pressure adjustments rather than acute renal
toxicity, and automated rules must not trigger false-positive alerts or mandate
cessation for variation inside that tolerance.

**The tolerance is ⛔ `unpopulated`.** A prior revision gave "up to 25% eGFR
reduction (or a serum creatinine rise up to 30%), provided serum potassium
remains below 5.5 mmol/L" with no source. Three things to fix before it becomes a
rule:

- Two thresholds, one meaning. A 25% eGFR fall and a 30% creatinine rise are not
  the same patient — they are two different observables with two different
  tolerances, and the rule must pick which one it reads (SSOT §5.2) rather than
  offering both.
- The potassium condition makes this a **two-observable rule**. Tolerating the
  eGFR fall is conditional on potassium; if potassium is absent, the rule cannot
  conclude tolerance and §8.3 governs what it does instead.
- A percentage change needs a baseline, and a baseline needs an age limit.
  `monitors` answers whether the pre-initiation eGFR on file is still usable as
  that baseline (SSOT §7.1f) — without it, "25% below baseline" silently
  compares against whatever the last value happened to be.

Conversely, combining RAAS inhibitors with direct renin inhibitors such as
aliskiren in patients with reduced eGFR or underlying diabetes mellitus is an
absolute contraindication: dual blockade increases hyperkalemia, severe
hypotension, and acute renal impairment without incremental cardiovascular
benefit. **Aliskiren is not on the SEML, so no aliskiren rule can fire** — the
eGFR threshold for it is not worth sourcing before the rest of this file is
pinned.

### 9.3 Category 3: Diuretic Therapies and Mineralocorticoid Receptor Antagonists

Diuretics — encompassing thiazides, loop diuretics, and mineralocorticoid
receptor antagonists (MRAs) — are critical for fluid overload management and
blood pressure reduction. Their efficacy and safety profiles depend directly on
underlying renal clearance mechanics.

| Ingredient | ATC Code | Saudi SEML / label pin | Renal Dosing Guidance (metric named per cell) | Hepatic Dosing Guidance (Child-Pugh) | Major Interactions (Polypharmacy/Elderly) | Monitoring Interval | `pregnancy` proposition only — SmPC §4.6 |
|---|---|---|---|---|---|---|---|
| **Hydrochlorothiazide** | C03AA03 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Ineffective if eGFR <30 mL/min/1.73m²; switch to loop diuretic for fluid management | Caution in Child-Pugh B/C; minor electrolyte shifts can precipitate hepatic encephalopathy | Lithium toxicity due to reduced renal lithium excretion; NSAIDs decrease diuretic efficacy | Serum K+, Na+, uric acid, eGFR at 2 and 4 weeks post-initiation | Avoid routine use; reduces plasma volume and placental perfusion; risk of fetal/neonatal thrombocytopenia |
| **Furosemide** | C03CA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | High doses required in eGFR <15 mL/min/1.73m²; maximum bolus rate 4 mg/min to prevent ototoxicity | Careful titration in Child-Pugh B/C with concurrent spironolactone; prevents rapid fluid shifts | Ototoxicity with aminoglycosides/cisplatin; enhanced digitalis toxicity via hypokalemia | Serum electrolytes (K+, Na+, Mg2+), eGFR, BP at 1–2 weeks | Crosses placenta; causes fetal diuresis; avoid unless treating maternal cardiac edema; monitor fetal growth |
| **Spironolactone** | C03DA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Contraindicated if eGFR <30 mL/min/1.73m² or serum Cr >221 µmol/L; extreme hyperkalemia risk | Caution in Child-Pugh B/C; altered metabolism of active canrenone metabolites | ACEi/ARBs, potassium supplements, NSAIDs induce life-threatening hyperkalemia | Serum K+ and eGFR mandatory at Day 7, Day 14, 1 month, then 3-monthly | Contraindicated in pregnancy; feminization of male fetus in animal studies; excreted in breast milk |

#### Pharmacological analysis — Category 3

Spironolactone requires defined temporal monitoring protocols within home-care
decision support systems. In elderly patients with chronic heart failure or
resistant hypertension, initiating spironolactone alongside baseline ACE
inhibitor therapy introduces a significant hyperkalemia risk. Baseline safety
eligibility (serum potassium and eGFR thresholds — both ⛔ `unpopulated` pending
the label pin) is followed by structured laboratory reassessment at day 7 and
day 14 post-initiation.

**None of the escalations below is a hard stop, because Noor has none.** SSOT
§9.1 admits exactly three severities — `stop_and_review`, `interruptive_review`,
`passive_task` — and `stop_and_review`, the strongest, still lets the clinician
proceed with a reason. A prior revision of this section specified a "hard-stop
requiring immediate drug withholding" at K⁺ ≥6.0 mmol/L. Mapped onto the real
ladder:

| Finding | Severity | Card content |
|---|---|---|
| Baseline K⁺ at or above the eligibility threshold | `interruptive_review` | Not `stop_and_review`. **A single baseline potassium is one measurement, and haemolysis is the commonest cause of a spuriously high one** — especially on a home draw with a long transit to the lab. The card asks for a repeat before it asks for a decision. |
| Post-initiation K⁺ in the mid band | `interruptive_review` | Recommends the label's dose reduction. Achievability: spironolactone is SEML-listed as `Tablet: 25 mg, 100 mg`, so a 50% reduction of 25 mg needs 12.5 mg — `achievable_by_division` at best, and the rule must say so rather than print "halve the dose". |
| Post-initiation K⁺ in the top band | `stop_and_review` | Recommends withholding and urgent assessment. Still not a block: the clinician can proceed with a documented reason, and §8.3 means that if the potassium result is missing or stale this degrades to `interruptive_review` rather than firing on absent data. |

The band boundaries themselves — a prior revision gave 5.0, 5.5–5.9 and ≥6.0
mmol/L — are ⛔ `unpopulated`. Each needs its three §12.3 case rows (at / just
below / just above), and note that consecutive bands stated as `5.5–5.9` and
`≥6.0` leave K⁺ between 5.9 and 6.0 unclaimed. Real analysers report to one
decimal, so 5.95 is a value the engine can actually receive and currently no
rule owns it.

### 9.4 Category 4: Specialized Anti-Arrhythmic Agents

Anti-arrhythmic agents possess narrow therapeutic indices, complex metabolic
pathways, and substantial toxicity profiles. Managing these agents requires
precise adherence to organ-specific dosing limits and continuous electro-
mechanical safety monitoring.

| Ingredient | ATC Code | Saudi SEML / label pin | Renal Dosing Guidance (metric named per cell) | Hepatic Dosing Guidance (Child-Pugh) | Major Interactions (Polypharmacy/Elderly) | Monitoring Interval | `pregnancy` proposition only — SmPC §4.6 |
|---|---|---|---|---|---|---|---|
| **Adenosine** | C01EB10 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dose adjustment required; rapid cellular uptake and metabolism by red blood cells | No dose adjustment required; clearance independent of hepatic mechanisms | **Dipyridamole is not on the SEML** — the "reduce dose by 75%" rule is unfirable; caffeine/theophylline block receptors | Continuous ECG during rapid IV push; monitor for transient high-grade AV block | Safe for acute SVT conversion in pregnancy; short half-life (<10 sec) limits fetal exposure |
| **Amiodarone** | C01BD01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No adjustment required for renal impairment; minimal renal excretion | Caution in severe Child-Pugh B/C; monitor LFTs closely; risk of acute hepatotoxicity | Inhibits CYP3A4, CYP2C9, P-gp; doubles digoxin, warfarin, and statin exposure; QT prolongers | Baseline and 6-monthly LFTs, TFTs, Chest X-ray, ophthalmic examination | Crosses placenta; fetal goiter, hypothyroidism, growth retardation; reserve for life-threatening dysrhythmias |
| **Digoxin** | C01AA05 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Dose reduction based on CrCl mandatory; 50–70% excreted unchanged renally | Minimal adjustment; monitor electrolyte balance (hypokalemia increases toxicity risk) | Amiodarone and verapamil double digoxin concentration via P-gp inhibition — both on the SEML, firable.<br>**Quinidine is not on the SEML** — unfirable | Trough serum digoxin level (target 0.5–0.9 ng/mL = **0.6–1.2 nmol/L**), serum K+, CrCl at day 7 and 14 | Crosses placenta; altered maternal volume of distribution requires serum level monitoring to maintain efficacy |
| **Lidocaine HCl** | C01BB01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Reduce prolonged infusion rate in severe renal failure; metabolite (MEGX) accumulates | Reduce maintenance infusion dose by 50% in Child-Pugh B/C; hepatic blood-flow dependent clearance | Beta-blockers (propranolol, metoprolol) reduce lidocaine clearance; additive toxicity with mexiletine | Continuous ECG, neurological status, serum lidocaine levels (>5 mcg/mL toxic) | Crosses placenta rapidly; fetal neuro-behavioral depression and bradycardia at high maternal doses |

#### Pharmacological analysis — Category 4

Digoxin dosing safety requires relying on unadjusted Creatinine Clearance (CrCl
via Cockcroft-Gault) rather than normalized eGFR. Because renal tubular
excretion and filtration of digoxin correlate directly with unadjusted
glomerular filtration capacity, utilizing eGFR in underweight elderly patients
overestimates clearance, resulting in toxic drug accumulation. In sarcopenic
patients, eGFR calculations normalized to 1.73 m² mask reduced absolute
filtration, elevating systemic drug exposure.

Co-administration of digoxin with P-glycoprotein inhibitors such as amiodarone,
verapamil, or quinidine requires an automatic 50% empiric dose reduction of
digoxin at the point of order, accompanied by a scheduled trough serum level
measurement at 7 to 10 days post-initiation. Only the amiodarone and verapamil
arms can fire in Saudi Arabia; quinidine is not on the SEML.

### 9.5 Category 5: Acute Vasopressors and Inotropic Agents

Vasopressors and inotropes are high-alert therapeutic agents used for
hemodynamic stabilization in cardiogenic, septic, or anaphylactic shock. Given
their rapid onset, short half-lives, and requirement for continuous parenteral
titration, regulatory safety profiles focus on infusion mechanics, extravasation
prevention, and continuous invasive hemodynamic monitoring. **Scope caveat:** all
six are IV, ICU/ambulance-acuity drugs (see the data-model note in §9) — most
useful for reconciliation and care-transition logic, not in-home dosing rules.

| Ingredient | ATC Code | Saudi SEML / label pin | Renal Dosing Guidance (metric named per cell) | Hepatic Dosing Guidance (Child-Pugh) | Major Interactions (Polypharmacy/Elderly) | Monitoring Interval | `pregnancy` proposition only — SmPC §4.6 |
|---|---|---|---|---|---|---|---|
| **Epinephrine** | C01CA24 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required; rapidly inactivated by tissue enzymes (COMT/MAO) | No dosage adjustment required; clearance independent of hepatic parenchymal capacity | Non-selective beta-blockers cause uninhibited alpha-1 stimulation (severe hypertension, bradycardia) | Continuous arterial BP, HR, continuous ECG, invasive hemodynamic monitoring | Uterine artery vasoconstriction; reduces uterine blood flow; reserve for maternal anaphylaxis or cardiac arrest |
| **Norepinephrine** | C01CA03 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required; short half-life (1–2 min); clearance unchanged | No dosage adjustment required; rapid plasma and tissue enzymatic cleavage | Tricyclic antidepressants markedly potentiate the pressor response — **no TCA is on the SEML** (the SEML antidepressants are fluoxetine, escitalopram, venlafaxine, mirtazapine, §16.2.1), so this arm is unfirable. MAOIs likewise are not on the SEML | Continuous arterial line BP, central venous pressure, urine output, infusion site evaluation | Severe uterine vasoconstriction; reduces placental perfusion; perform continuous fetal heart monitoring |
| **Dobutamine** | C01CA08 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required in renal failure | No dosage adjustment required; rapid metabolism by tissue COMT | Beta-blockers antagonize inotropic response; additive hypotensive effect with vasodilators | Continuous ECG (arrhythmia monitoring), HR, blood pressure, urine output | Safety in human pregnancy not established; potential fetal tachycardia; reserve for severe cardiogenic shock |
| **Milrinone** | C01CE02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Dose reduction mandatory for CrCl <50 mL/min — see the CrCl band table below, which is authoritative over this cell | No dosage adjustment required; clearance primarily dependent on renal filtration | Chemical precipitation if infused in same IV line as furosemide; additive hypotension with nitrates | Continuous BP, continuous ECG, platelet count, serum potassium, CrCl | Crosses placenta; insufficient human data; potential for fetal hypotension; restrict to refractory maternal HF |
| **Vasopressin** | H01BA01 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required; metabolized by vascular and tissue peptidases | No dosage adjustment required in hepatic impairment | Enhances pressor response of norepinephrine; furosemide potentiates diuretic response | Continuous arterial BP, serum sodium (hyponatremia risk), peripheral vascular perfusion | Oxytocic action; stimulates uterine contractions and vasoconstriction; avoid unless refractory shock |
| **Dopamine HCl** | C01CA04 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required; tissue and hepatic MAO/COMT degradation | No dosage adjustment required; metabolic pathways remain active in liver disease | **MAOIs are not on the SEML** — the 90%-dose-reduction rule is unfirable. Phenytoin (on SEML) causes acute hypotension and bradycardia — firable | Continuous HR, BP, urine output, extremity warmth/perfusion, infusion site checks | May cause maternal ventricular arrhythmias and uterine hypoperfusion; reserve for severe hemodynamics |

#### Pharmacological analysis — Category 5

Milrinone provides a primary example of an inotropic agent requiring strict
CrCl-based dose scaling. Because milrinone is eliminated predominantly unchanged
via urinary excretion, renal insufficiency prolongs drug clearance,
predisposing patients to drug accumulation, severe hypotension, and ventricular
dysrhythmias. Maintenance dose reductions scale directly to Cockcroft-Gault
Creatinine Clearance — `renal_metric: crcl`, never eGFR:

| CrCl Range (mL/min) | Maintenance Infusion Rate |
|---|---|
| >50 | 0.43 mcg/kg/min (standard) |
| 30–50 | 0.33–0.38 mcg/kg/min |
| 10–30 | 0.23–0.28 mcg/kg/min |
| <10 | 0.20 mcg/kg/min |

**The boundary at CrCl 50 needs resolving before this becomes a rule.** A prior
revision's prose said "dose reduction mandatory for CrCl <50" while listing 0.43
mcg/kg/min *at* CrCl 50 and 0.33–0.38 for the 30–50 band — so CrCl exactly 50
falls in two rows and gets two different rates. Which side owns the boundary is a
decision the pinned label makes, and until it does the whole table is ⛔
`unpopulated`. This is precisely what SSOT §12.3's three rows per threshold —
**at 50, just below, just above** — exist to catch, and the reason the cases are
written before the rule.

The 0.20–0.43 mcg/kg/min range is also the narrowest dosing window in this file,
on a `Solution for injection: 1 mg/ml` presentation. A weight-based infusion rate
that lands between achievable pump increments is the infusion analogue of an
unachievable tablet strength (SSOT §3.2) — the rule reports the rate; it does
not assume the pump can deliver it.

Additionally, critical care decision support systems must evaluate Y-site
intravenous compatibility. Co-infusing milrinone and furosemide in a shared
intravenous line causes immediate chemical precipitation, obstructing vascular
access lines and disrupting vasoactive therapy.

Two profile-level notes carry over from the complication research:

- **Epinephrine + non-selective beta-blocker (propranolol, §9.1):** see §8 — the
  flag softens toward "give anyway, with glucagon as second line," never toward
  withholding.
- **The "renal-dose dopamine" myth:** the historical idea of a protective
  low-dose ("renal-dose") dopamine has been discredited in the critical-care
  literature. Confirm against current SPC/guideline text before encoding any
  dose-tier logic that implies renal benefit at low doses.

### 9.6 Category 6: Anti-Thrombotic and Lipid-Lowering Therapeutics

Anti-thrombotic and lipid-lowering agents are essential for secondary
cardiovascular prevention and treating acute ischemic events. Anti-platelet and
fibrinolytic therapies pose major bleeding risks in organ dysfunction, while
statins require defined hepatic and skeletal muscle monitoring.

| Ingredient | ATC Code | Saudi SEML / label pin | Renal Dosing Guidance (metric named per cell) | Hepatic Dosing Guidance (Child-Pugh) | Major Interactions (Polypharmacy/Elderly) | Monitoring Interval | `pregnancy` proposition only — SmPC §4.6 |
|---|---|---|---|---|---|---|---|
| **Acetylsalicylic Acid** | B01AC06 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Avoid if eGFR <30 mL/min/1.73m²; induces acute renal impairment via prostaglandin inhibition | Contraindicated in severe hepatic impairment (Child-Pugh C); increased bleeding diathesis | Anticoagulants, SSRIs, NSAIDs increase GI bleeding risk; blunts ACEi hypotensive action | Hemoglobin, stool occult blood, eGFR annually or post-bleeding event | Low-dose (75–150 mg) safe for pre-eclampsia; high doses in 3rd trimester cause premature closure of ductus arteriosus |
| **Clopidogrel** | B01AC04 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dose adjustment required in renal impairment; safety established | Caution in moderate hepatic impairment (Child-Pugh B); contraindicated in severe liver disease (Child-Pugh C) | Omeprazole and esomeprazole inhibit CYP2C19 activation — **esomeprazole is on the SEML (§14.1) so the alert fires; pantoprazole is *not* on the SEML, so "switch to pantoprazole" recommends an unavailable drug (SSOT §R-2). The SEML non-CYP2C19 acid suppressant is famotidine (§14.1)**<br>NSAIDs | Platelet count, hemoglobin, signs of bleeding post-initiation | Lack of clinical data; as a precaution, avoid during pregnancy and breast-feeding |
| **Ticagrelor** | B01AC24 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No dosage adjustment required in renal impairment or dialysis | Contraindicated in severe hepatic impairment (Child-Pugh C); caution in Child-Pugh B | Strong CYP3A4 inhibitors increase exposure; high-dose aspirin (>100 mg daily) reduces ticagrelor efficacy | Platelet count, dyspnea symptoms, serum uric acid, hemoglobin | Avoid during pregnancy; animal studies demonstrate reproductive toxicity and reduced fetal weight |
| **Tirofiban** | B01AC17 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | Reduce IV infusion rate by 50% if CrCl ≤60 mL/min (e.g., 0.075 mcg/kg/min maintenance) | Caution in severe liver disease; bleeding risk elevated due to coagulopathy | Synergistic bleeding risk with anticoagulants, thrombolytics, NSAIDs | Platelet count at 2–6 hours post-initiation (thrombocytopenia check), hemoglobin, CrCl | Avoid during pregnancy unless absolutely necessary; potential risk of maternal and fetal hemorrhage |
| **Alteplase (rt-PA)** | B01AD02 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No clearance adjustment required, but severe renal disease increases bleeding risk | Contraindicated in severe hepatic impairment (Child-Pugh C) or active hepatic bleeding | Anticoagulants, antiplatelet agents severely increase risk of intracranial hemorrhage | Continuous neurological status (NIHSS), blood pressure q15m during infusion, fibrinogen | High bleeding risk for placenta; reserve for life-threatening maternal PE or ischemic stroke |
| **Atorvastatin** | C10AA05 | Listed SEML 2023 ✅ · label pin ⛔ `unretrieved` | No adjustment required for renal impairment or eGFR decline | Contraindicated in active liver disease or unexplained transaminase elevations (Child-Pugh B/C) | CYP3A4 inhibitors (clarithromycin, azoles, HIV protease inhibitors) dramatically increase myopathy/rhabdomyolysis risk | Baseline LFTs (ALT/AST); CK if muscle pain/weakness occurs; lipid panel at 4–12 weeks | Strictly contraindicated in pregnancy and lactation; lipophilic statins disrupt essential fetal cholesterol synthesis |

#### Pharmacological analysis — Category 6

For clopidogrel therapy, decision support rules must evaluate CYP2C19 metabolic
interactions. Clopidogrel is an inactive prodrug requiring two-step hepatic
bioactivation via CYP2C19. Co-prescribing clopidogrel with potent CYP2C19
inhibitors — specifically omeprazole or esomeprazole — decreases active
clopidogrel metabolite formation, reducing antiplatelet efficacy and increasing
stent thrombosis risk.

**The alert may not recommend pantoprazole.** Pantoprazole is not on the SEML,
and SSOT §R-2 forbids proposing an agent the patient cannot obtain — a
recommendation to substitute an unstocked drug is worse than no recommendation,
because it costs the clinician a phone call to discover. The SEML acid-
suppression alternatives are **esomeprazole** (§14.1 — a CYP2C19 inhibitor
itself, so not a substitute) and **famotidine** (§14.1, `Tablet: 20 mg, 40 mg` —
an H2 antagonist, not a PPI, so substituting it is a therapeutic downgrade the
prescriber must decide on, not a swap the engine can assert). The honest card
states the interaction and the two available options with that tradeoff named;
it does not name a winner.

In parenteral antiplatelet therapy with tirofiban, renal adjustment depends on
an unadjusted CrCl calculation. If a patient's CrCl drops to ≤60 mL/min, the
maintenance infusion rate must be reduced by 50%. Failure to adjust tirofiban
doses in renal impairment leads to drug accumulation and major bleeding
complications.

---

## 10. Per-Ingredient Complication Profiles

Adverse effects, boxed warnings, and contraindications ("what can go wrong"),
organized by the six categories of §9. **Sourcing caveat:** compiled from FDA
labels/DailyMed, StatPearls, and specialist pharmacology/toxicology references
(StatPearls, LiverTox, EMCrit, LITFL). Local SFDA SPCs track EMA/ICH, not FDA —
cross-check the specific complication/contraindication against the EMA SmPC or
local SPC before anything here becomes rule content. FDA and EMA agree on the
substance of almost all of these, but exact wording, thresholds, and which
warnings are boxed vs. standard precaution can differ. Renal/hepatic dosing
thresholds, monitoring intervals, and pregnancy/lactation narrative still need a
separate per-ingredient SPC pass (§3.2/§7.1/§7.3).

This catalogue is unusually interaction-dense — several of these drugs are
dangerous specifically *in combination with each other*, which is captured in
§8/§8.1 rather than buried in per-drug tables.

### 10.1 Category 1 profiles — beta-blockers and calcium channel blockers

#### Metoprolol tartrate (C07AB02 — β1-selective blocker)

| | |
|---|---|
| **Boxed warning** | Do **not** stop abruptly, especially in ischemic heart disease — exacerbation of angina, MI, and ventricular arrhythmias have followed abrupt beta-blocker discontinuation. Taper over 1–2 weeks. |
| **Contraindications** | Severe bradycardia; 2nd/3rd-degree heart block; cardiogenic shock; SBP <100 mmHg; decompensated heart failure; sick sinus syndrome (unless paced); known hypersensitivity. |
| **Key precautions** | Bronchospastic disease — avoid beta-blockers generally. Pheochromocytoma — must initiate alpha-blocker first. Abrupt withdrawal in thyrotoxicosis can precipitate thyroid storm. Can blunt epinephrine response in patients with severe anaphylaxis history. Can aggravate peripheral arterial insufficiency. |
| **Common AEs** | Tiredness/dizziness (~10%), depression (~5% — can rarely progress to catatonia, more so than with other beta-blockers), erectile dysfunction, confusional state, ↑triglycerides/↓HDL. |
| **Rare but serious** | Intensification of AV block, agranulocytosis, non-thrombocytopenic/thrombocytopenic purpura, hypersensitivity with laryngospasm. |
| **CDS relevance** | The hard SBP <100 and heart-block contraindications are clean rule candidates. Abrupt-stop protection (e.g., flag if a refill gap >X days is detected) fits the missed-monitoring/adherence theme. |

#### Carvedilol (C07AG02 — non-selective β + α1 blocker)

| | |
|---|---|
| **Critical warning** | Never stop abruptly — same rebound risk as metoprolol (severe angina, MI, ventricular arrhythmias), taper over 1–2 weeks. |
| **Hepatotoxicity** | Documented but rare — idiosyncratic liver injury (elevated LFTs, sometimes pruritus) that resolves on discontinuation and can recur if switched to another beta-blocker. Contraindicated in severe hepatic impairment. |
| **Diabetes interaction** | Non-selective beta-blockade masks hypoglycemia symptoms (tachycardia) more than selective agents, and can worsen hyperglycemia — monitor glucose closely at initiation/discontinuation/dose change. Directly relevant given how many diabetes drugs are also on the SEML. |
| **Contraindications** | Bronchospastic disease (can cause life-threatening bronchospasm — non-selective, so higher risk than metoprolol); decompensated heart failure requiring IV inotropes; severe bradycardia; 2nd/3rd-degree AV block (unless paced); cardiogenic shock. |
| **Common AEs** | Bradycardia (reduce dose if HR <55 bpm), hypotension, fatigue, dizziness, depression, memory loss, impotence, cold extremities. |
| **Key interactions flagged in the label itself** | **Digoxin and amiodarone** — carvedilol increases digoxin blood levels, and combining with either can significantly slow heart rate and AV conduction. Both are on the SEML (§9.4). |

#### Verapamil hydrochloride (C08DA01 — non-dihydropyridine CCB)

| | |
|---|---|
| **Contraindications** | Severe LV dysfunction; hypotension (SBP <90) or cardiogenic shock; sick sinus syndrome or 2nd/3rd-degree AV block (unless paced); atrial flutter/fibrillation with an accessory bypass tract (WPW) — can cause **ventricular fibrillation**. |
| **Cardiac risks** | Can precipitate new or worsening heart failure, especially with pre-existing LV dysfunction. Can cause marked first-degree AV block or progress to 2nd/3rd-degree block — dose reduction or discontinuation needed if this occurs. In hypertrophic cardiomyopathy specifically: sinus bradycardia, pulmonary edema, severe hypotension, AV block, sinus arrest, and death have all been reported. |
| **Common AEs** | Constipation (notably common for a cardiac drug — relevant for elderly home-care patients already prone to it), headache, peripheral edema, dizziness. Reversible paralytic ileus reported infrequently. |
| **Rare** | Elevated liver enzymes, rare serious hepatotoxicity. |
| **Critical interaction** | **IV verapamil + IV beta-blocker is flagged in the label as producing serious adverse reactions**, especially in severe cardiomyopathy/heart failure/recent MI — both drugs depress myocardial contractility and AV conduction. Given metoprolol and carvedilol are both in this catalogue, this combination (if it ever occurs, e.g., IV in an acute setting) deserves a hard interaction rule, not just a soft flag. |

#### Nifedipine (C08CA05 — dihydropyridine CCB)

| | |
|---|---|
| **Contraindication — formulation-specific** | **Immediate-release nifedipine is contraindicated in acute coronary syndromes / STEMI and hypertrophic cardiomyopathy** — associated with increased MI, arrhythmia, and stroke risk, historically linked to increased total mortality in coronary disease when used in moderate-to-high doses without beta-blocker coverage. This distinction (IR vs. extended-release) matters a lot for a rule engine — the two formulations should probably be modeled as functionally different drugs. |
| **Mechanism-driven AEs** | Peripheral edema — dose-related (18% at 30 mg/day, rising to ~29% at 90 mg/day); reflex tachycardia (more pronounced with IR than ER); flushing, headache, dizziness — mostly a vasodilation effect. |
| **Other reported effects** | Worsening angina in a small subset (excessive BP drop, coronary steal, or reflex tachycardia); gingival hyperplasia (rare); elevated liver enzymes. |
| **Overdose picture** | Systemic vasodilation, severe hypotension, reflex tachycardia. |
| **Practical note from the pharmacology literature** | Co-administering a beta-blocker with nifedipine is a standard mitigation for reflex tachycardia — relevant if building a "safe combination" reference alongside interaction-flagging rules, not just a danger list. |

#### Amlodipine (C08CA01 — dihydropyridine CCB)

| | |
|---|---|
| **Contraindication** | Known hypersensitivity to amlodipine/dihydropyridines only — otherwise a comparatively "clean" drug relative to others in this catalogue. |
| **Most common AE by far** | Peripheral edema — roughly 1 in 3 patients, dose-related; mechanism is arterial-selective vasodilation causing a fluid shift, **not** a sign of heart or kidney failure on its own — worth encoding as a distinguishing note so a home-care nurse doesn't over-escalate ordinary amlodipine edema as new heart failure. |
| **Cardiac caution** | Can cause worsening angina or acute MI after starting or increasing the dose, particularly with severe obstructive CAD — gradual titration reduces this risk. |
| **Hepatic** | Extensively liver-metabolized; elimination half-life prolonged in hepatic impairment (t½ ~56h) — titrate slowly, no formal dose cap defined in the label itself. Rare but serious jaundice/hepatic enzyme elevation (cholestatic or hepatitic pattern) reported postmarketing, occasionally requiring hospitalization. |
| **Elderly** | Reduced clearance → ~40–60% higher AUC — lower starting dose generally warranted. |
| **Other AEs** | Headache, flushing, dizziness, palpitation, gynecomastia (rare, uncertain causality), fatigue. |
| **CDS relevance** | Because both amlodipine and nifedipine are dihydropyridine CCBs with an almost identical edema mechanism, a combined-therapy rule (don't stack two DHP-CCBs without a clear reason) is a sensible addition. |

#### Glyceryl trinitrate (C01DA02) and isosorbide dinitrate (C01DA08)

Grouping these — the safety profile is essentially shared across the nitrate class.

| | |
|---|---|
| **The single most important interaction in this catalogue** | **Nitrates + any PDE5 inhibitor (sildenafil, tadalafil, vardenafil, avanafil) is absolutely contraindicated** — synergistic vasodilation causes severe, potentially fatal hypotension. This is not formulary-visible risk (PDE5i are often bought over-the-counter or informally, especially in an elderly male home-care population) — worth a hard patient-education flag as well as a formulary interaction rule. Timing matters: avoid sildenafil/vardenafil within 24h and tadalafil within 48h of nitrate use; if a PDE5i patient develops chest pain, nitrates should be withheld for the same windows. |
| **Also contraindicated with** | Riociguat (soluble guanylate cyclase stimulator) — same mechanism, same severe-hypotension risk. |
| **Other contraindications** | Severe hypotension, uncorrected hypovolemia, increased intracranial pressure (head trauma, cerebral hemorrhage), severe anemia, constrictive pericarditis/tamponade, restrictive cardiomyopathy, hypertrophic cardiomyopathy (caution). |
| **Common AEs** | Headache (very common — a marker of therapeutic vasodilation, sometimes treated symptomatically with paracetamol rather than stopping the nitrate), hypotension, dizziness, flushing, tachycardia. |
| **Tolerance** | Continuous use without a nitrate-free interval (typically 10–12h, often overnight) leads to tolerance and loss of efficacy — a scheduling/dosing-window rule, not just a safety rule. |
| **Other interactions** | Marked symptomatic orthostatic hypotension when combined with a calcium channel blocker (verapamil, nifedipine, and amlodipine are all in this same category) — additive vasodilation. Alcohol significantly enhances the hypotensive effect. |
| **Administration note** | Do not switch nitrate brands/formulations unintentionally — not all are bioequivalent, relevant if the supply chain substitutes generics. |

#### Propranolol (C07AA05 — non-selective β-blocker)

| | |
|---|---|
| **Contraindications** | Sinus bradycardia; hypotension; greater-than-first-degree heart block; decompensated heart failure; cardiogenic shock; bronchospastic disease (contraindicated more strictly here than for β1-selective agents, since propranolol blocks β2 as well); hypersensitivity. |
| **CNS burden — the standout feature of this drug** | Because propranolol is highly lipophilic and crosses the blood-brain barrier more than metoprolol/carvedilol, it carries a heavier CNS load: sleep disturbance, nightmares, night terrors (2–18.5% of patients), impaired memory/psychomotor function, mood changes, and dose-dependent depression that can rarely progress to catatonia. |
| **Endocrine masking** | Masks hypoglycemia symptoms (tachycardia, tremor) — same mechanism as other non-selective beta-blockers but flagged here specifically because propranolol is also widely used off-label (migraine prophylaxis, anxiety, essential tremor), so it can end up prescribed by a different clinician than the one managing a patient's diabetes. Also masks hyperthyroidism signs and can precipitate thyroid storm on abrupt withdrawal. |
| **Boxed-warning-equivalent** | Do not stop abruptly, particularly with ischemic heart disease — same rebound risk as the rest of this drug class. |
| **Pregnancy/neonatal** | Reports of low birth weight, neonatal hypoglycemia, bradycardia, and respiratory depression in infants of mothers on propranolol at term. |
| **CDS relevance** | If the system tracks indication alongside drug, propranolol showing up for a non-cardiac indication (tremor, anxiety, migraine) in a diabetic or asthmatic patient is a genuinely useful cross-check that a narrower "cardiac drugs" filter would miss. |

#### Metoprolol succinate — extended-release (C07AB02, same molecule/base code as tartrate, different salt/formulation)

| | |
|---|---|
| **Distinct indication from tartrate** | Specifically studied and FDA-approved for chronic heart failure (MERIT-HF trial: 34% relative reduction in all-cause mortality vs. placebo in NYHA class II–III patients) — this is a meaningfully different clinical role than the tartrate salt, which is not HF-indicated. **Worth modeling succinate and tartrate as related-but-distinct CDS entities**, not interchangeable formulations of "metoprolol." |
| **Contraindications** | Same as tartrate: severe bradycardia, >first-degree heart block, cardiogenic shock, **decompensated heart failure** (note the nuance — succinate treats *chronic stable* HF but is contraindicated in *decompensated* HF; initiation timing matters enormously here). |
| **Initiation risk** | MERIT-HF safety data show ER metoprolol succinate is well-tolerated **when started at low dose and slowly titrated** in stabilized HF patients already on other HF therapy — but the same drug can worsen decompensated HF if started at the wrong time. This isn't a simple "safe/unsafe" flag; it's initiation-context-dependent. |
| **Additive bradycardia risk** | Label specifically names concomitant glycosides (digoxin, §9.4), clonidine, diltiazem, and **verapamil** (§9.1) as increasing bradycardia risk — a direct cross-category interaction. |
| **Perioperative caution** | Avoid initiating high-dose extended-release metoprolol right before non-cardiac surgery; equally, don't routinely stop chronic beta-blocker therapy before surgery. |
| **Otherwise** | Shares the rest of the class profile with tartrate (masks hypoglycemia, bronchospasm risk, abrupt-withdrawal rebound, hepatic-impairment dose caution). |

### 10.2 Category 2 profiles — RAAS modulators and centrally acting agents

**This category is where the whole formulary starts talking to itself.** Three
of these drugs (the ACE inhibitors + losartan + spironolactone in §10.3) form
the single highest-value interaction cluster in the catalogue, with a direct
connection back to digoxin (§9.4) that is easy to miss if each drug is only
reviewed in isolation.

#### ACE inhibitors — lisinopril, captopril, enalapril maleate (class-shared profile, then per-drug differences)

**Shared across the whole ACE-inhibitor class**

| | |
|---|---|
| **Boxed warning: fetal toxicity** | Discontinue as soon as pregnancy is detected — second/third-trimester exposure causes oligohydramnios, fetal renal failure, lung hypoplasia, skull hypoplasia, and death. |
| **Angioedema** | Can occur at any point in therapy, not just initiation; involves face/lips/tongue/larynx and can be fatal via airway obstruction; intestinal angioedema (presenting as abdominal pain, easy to misattribute) is also reported. **Risk is 2–4x higher in Black patients** per FAERS analysis — relevant to document as a risk-stratification factor, not a contraindication. History of ACEi-associated or hereditary/idiopathic angioedema is an absolute contraindication for the whole class. |
| **Hyperkalemia** | Class effect from reduced aldosterone — monitor serum potassium periodically, especially with renal impairment or concurrent potassium-sparing agents (see spironolactone, §10.3). |
| **Renal** | Can worsen renal function, particularly in bilateral renal artery stenosis (or stenosis of a single functioning kidney) — this is a hard contraindication-level risk, not just a caution. |
| **Cough** | Dry, hacking, non-productive — 5–20% of users, more common in women, caused by bradykinin/substance P accumulation (this is why the cough doesn't respond to antitussives and only resolves on discontinuation or switching to an ARB). |
| **Cholestatic jaundice / hepatic failure** | Rare but a specifically named boxed-warning-adjacent risk across the class — discontinue if it occurs. |
| **Dual RAAS blockade** | Combining an ACE inhibitor with an ARB (losartan, also in this category), or with a renin inhibitor (aliskiren — not on the SEML), significantly increases hyperkalemia, hypotension, and AKI risk with no added benefit. **The VA NEPHRON-D trial (losartan + lisinopril in diabetic nephropathy) was stopped early for exactly this reason** — this is not a theoretical interaction, it's a trial-terminating one, and directly relevant since losartan is on the same catalogue. |

**Captopril-specific (sulfhydryl-group effects — distinct from the newer, non-sulfhydryl ACE inhibitors)**

| | |
|---|---|
| **Neutropenia/agranulocytosis** | A specifically captopril-associated risk tied to its sulfhydryl group, more so than lisinopril or enalapril — the label recommends monitoring blood counts, especially early in therapy. |
| **Dysgeusia (taste disturbance)** | 2–4% of patients, diminished or lost taste perception, reversible and usually self-limited (2–3 months) even with continued use — can cause enough appetite/weight change to be worth tracking in a home-care nutrition context. |
| **Rash** | 4–7% of patients, usually in the first four weeks, typically mild and resolves with dose reduction or a brief antihistamine course. |
| **Proteinuria** | ~1% of patients, immune-complex membranous glomerulopathy — usually resolves within 6 months even if captopril is continued. |

**Enalapril-specific**

| | |
|---|---|
| **First-dose hypotension** | Specifically flagged for patients already on a diuretic — symptomatic hypotension can occur after the very first enalapril dose. The label's own mitigation: stop the diuretic 2–3 days before starting enalapril where feasible, then resume if BP isn't controlled on enalapril alone. This is a clean, encodable sequencing rule. |
| **Neprilysin inhibitor interaction** | Contraindicated in combination with sacubitril (a neprilysin inhibitor) — do not administer within 36 hours of switching to/from sacubitril/valsartan, due to angioedema risk. **Sacubitril/valsartan is not on the SEML** — the 36h-washout rule cannot fire on SEML data alone. |
| **Renal dosing note** | Not recommended in neonates or pediatric patients with GFR <30 mL/min/1.73m² per the manufacturer (no data available) — a hard eligibility gate rather than a dose adjustment. |

#### Losartan (C09CA01 — angiotensin receptor blocker / ARB)

| | |
|---|---|
| **Shares most ACE-inhibitor class risks** | Fetal toxicity (contraindicated in pregnancy, same discontinue-on-detection logic), hyperkalemia, renal impairment risk, dual-RAAS-blockade danger with the ACE inhibitors in this same category. Angioedema is possible but less frequent than with ACE inhibitors (no bradykinin accumulation via this mechanism). |
| **No cough** | The absence of ACEi-associated cough is losartan's main practical differentiator — the standard switch target when an ACE inhibitor causes intolerable cough. |
| **Hepatic impairment** | Specific dose guidance exists (starting dose 25 mg once daily) — losartan hasn't been studied in severe hepatic impairment, so caution there is stronger than a simple dose adjustment. |
| **Rare hepatotoxicity** | Case reports of severe/fulminant liver injury exist despite losartan's generally favorable safety reputation — worth noting since it contradicts the "losartan is the safe option" framing that sometimes gets applied reflexively. |
| **First-dose/volume-depletion hypotension** | Same mechanism as enalapril — more likely in volume-depleted or salt-restricted patients. |
| **CDS relevance** | Losartan + either lisinopril, captopril, or enalapril on the same active med list should be a **hard interaction flag**, not a soft one — this is the VA NEPHRON-D scenario described above, playing out with drugs literally on the SEML. |

#### Methyldopa (C02AB01 — central α2-agonist)

| | |
|---|---|
| **Contraindications** | Active hepatic disease (acute hepatitis, active cirrhosis); prior liver disorder associated with methyldopa specifically; concurrent MAO inhibitor therapy (**no MAOI is on the SEML** — unfirable); hypersensitivity. |
| **Hepatotoxicity** | Usually presents within the first 3–4 weeks of therapy — ranges from asymptomatic transaminase elevation to fulminant hepatic necrosis; fatalities reported. Monitor LFTs, particularly early in treatment. |
| **Coombs-positive hemolytic anemia** | 10–20% of patients on prolonged therapy develop a positive direct Coombs test; actual hemolytic anemia is much rarer (<1%) but can be fatal if unrecognized. A positive Coombs test *alone* is not a reason to stop — active hemolysis is. |
| **CNS/psychiatric** | Sedation (most common, often used therapeutically by dosing increases in the evening), depression, nightmares, decreased mental acuity, Parkinsonism, Bell's palsy — an important differential to keep in mind for elderly home-care patients presenting with new confusion or mood change. |
| **Other autoimmune-flavored effects** | Drug-induced lupus-like syndrome, myocarditis, pericarditis, vasculitis, drug fever. |
| **Clinical niche today** | Primarily used now for hypertension in pregnancy given its long safety track record there — worth noting since this narrows who on a general home-care roster is actually likely to be on it. |

#### Hydralazine (C02DB02 — direct arteriolar vasodilator)

| | |
|---|---|
| **Reflex tachycardia** | The defining mechanism-driven effect — direct vasodilation triggers baroreceptor-mediated sympathetic activation, raising heart rate and myocardial oxygen demand. Reported in up to 10% of patients. This is why hydralazine is almost always paired with a beta-blocker (to blunt the reflex) and a diuretic (to offset the fluid retention below) — worth encoding as a "usually-combined-with" pattern rather than only a danger list. |
| **Drug-induced lupus (DILE)** | The signature long-term risk — arthralgia, myalgia, fever, rash, positive ANA; incidence 5–10%, dose- and duration-dependent, more common in slow acetylators and in women. Kidneys and CNS are usually spared (unlike idiopathic SLE), and it's reversible on discontinuation, though resolution can take months to years. Rare cases of pericardial tamponade and hemolytic anemia associated with hydralazine-induced lupus have been reported. |
| **Ischemic risk** | Contraindicated / flagged as high-hazard in coronary artery disease — the sympathetic activation can precipitate angina or MI. Also worsens pulmonary artery pressure in patients with pulmonary hypertension or COPD, especially during hypoxia. |
| **Peripheral neuropathy** | Dose-related, more common in slow acetylators — thought to relate to hydralazine's antagonism of vitamin B6 (pyridoxine). |
| **Fluid retention** | Sodium/water retention requiring concurrent diuretic use — this is the mechanistic link to why furosemide/HCTZ so often appear alongside hydralazine on a med list. |
| **Rare but serious** | ANCA-associated vasculitis and severe AKI have been reported in case series — described in the literature as a reason to weigh hydralazine carefully against newer alternatives given how many other agents are now available. |

### 10.3 Category 3 profiles — diuretics and mineralocorticoid receptor antagonists

#### Hydrochlorothiazide (C03AA03 — thiazide diuretic)

| | |
|---|---|
| **Electrolyte/metabolic profile** | Hypokalemia (mild decrease ~0.5 mEq/L in up to 50% of patients — dose-related, minimal at 12.5 mg/day, rising sharply above 25–50 mg/day with little added antihypertensive benefit), hyponatremia, hypomagnesemia, hypercalcemia, hyperuricemia (can precipitate gout), hyperglycemia/glucose intolerance (~3% of patients, generally reversible within 6 months of stopping), and an adverse lipid effect (↑total cholesterol ~11%, ↑LDL ~12%, ↑VLDL ~50%). |
| **Non-melanoma skin cancer** | A genuine, regulator-confirmed signal — IARC classifies HCTZ as possibly carcinogenic (Group 2B), and EMA's pharmacovigilance committee concluded a causal relationship with non-melanoma skin cancer (predominantly squamous cell carcinoma) in 2018, dose- and cumulative-exposure-dependent. Worth a long-term-use skin-check reminder rather than just a one-time counseling note. |
| **Photosensitivity** | Mechanistically linked to the skin cancer signal — both are UV-interaction effects at the cellular level, not two unrelated side effects. |
| **Sulfonamide cross-reactivity** | Structurally a sulfonamide — patients with sulfa allergy may react; hypersensitivity reactions reported include anaphylaxis, vasculitis, and severe skin reactions (Stevens-Johnson syndrome, toxic epidermal necrolysis). |
| **Renal** | Interstitial nephritis, renal dysfunction/failure reported. |
| **CDS relevance** | The dose-response curve here is unusually clean for a rule: little added benefit and rising hypokalemia risk above ~25–50 mg/day is a good candidate for a dose-ceiling soft-alert rather than a hard block. |

#### Furosemide (C03CA01 — loop diuretic)

| | |
|---|---|
| **Ototoxicity** | The signature loop-diuretic risk, largely absent from thiazides — tinnitus and reversible/irreversible hearing loss, associated with rapid IV injection (label caps infusion at 4 mg/min in adults), high doses, severe renal impairment, hypoproteinemia, or concurrent ototoxic drugs (aminoglycosides, cisplatin, ethacrynic acid). This is one of the few complications in this research pass that's specifically an **administration-technique** risk, not just a dose or patient-factor risk — worth a hard rate-limit rule for IV protocols. |
| **Electrolyte profile** | Hypokalemia, hyponatremia (elderly at particular SIADH-related risk per Beers Criteria), hypomagnesemia, hypochloremic metabolic alkalosis — worse with brisk diuresis, poor oral intake, or concurrent corticosteroids/laxatives. |
| **Sulfonamide cross-reactivity** | Same structural class concern as HCTZ. |
| **Hyperuricemia/gout** | Can precipitate an acute attack. |
| **Digoxin interaction** | The label explicitly flags that furosemide's potassium-depleting effect raises digoxin toxicity risk — a direct, concrete link to digoxin (§9.4), and arguably a higher-value rule than either drug's isolated profile since it's a very common real-world combination (loop diuretic + digoxin in HF). |
| **Photosensitivity** | Phototoxic potential similar in mechanism to HCTZ, per in-vitro skin-cell studies — less clinically prominent than the HCTZ signal but mechanistically related. |
| **Skin reactions** | SJS, TEN, and erythema multiforme reported — discontinue at first sign of rash. |

#### Spironolactone (C03DA01 — potassium-sparing / aldosterone antagonist)

| | |
|---|---|
| **Hyperkalemia — the central risk** | Contraindicated in patients with existing hyperkalemia or significant hyperkalemia risk. Explicitly flagged in multiple sources as potentially **fatal when combined with ACE inhibitors in patients with pre-existing renal impairment** — and lisinopril, captopril, and enalapril are all in this catalogue, plus losartan. This combination is sometimes used deliberately for proteinuria/HF benefit under close monitoring (there's real trial evidence for it), which makes it more important, not less, to have explicit potassium-monitoring logic rather than a blanket "don't combine" rule. |
| **Contraindication combination** | Should not be combined with other potassium-sparing diuretics; extreme caution with indomethacin/NSAIDs plus a diuretic (the classic "triple whammy" AKI pattern, applicable across this whole catalogue given how many diuretics and RAAS-blockers are on it). |
| **Endocrine/reproductive effects** | Gynecomastia (dose- and duration-dependent, ~9% of men in the RALES heart-failure trial, usually reversible), decreased libido, erectile dysfunction; in women — menstrual irregularities, amenorrhea, postmenopausal bleeding, breast tenderness (13–33% of women, rising to >70% at doses ≥200mg/day). These are a common reason for non-adherence that's easy to miss unless specifically asked about. |
| **Hepatic caution** | Can precipitate hepatic coma in patients with decompensated cirrhosis via minor fluid/electrolyte shifts — use with caution, and reversible hyperchloremic metabolic acidosis has been reported in this population even with normal renal function. |
| **Rare** | Agranulocytosis (labeled as "potentially fatal" alongside the ACEi-hyperkalemia combination); mixed cholestatic/hepatocellular liver toxicity (rare, one reported fatality in the label). |

### 10.4 Category 4 profiles — specialized anti-arrhythmic agents

#### Adenosine (C01EB10 — AV-nodal blocker)

| | |
|---|---|
| **Contraindications** | Known/suspected bronchoconstrictive or bronchospastic lung disease (asthma) — can precipitate bronchospasm/respiratory compromise via mast-cell degranulation and histamine release; 2nd/3rd-degree AV block or sick sinus syndrome (unless paced). |
| **Expected/self-limiting effects** | Facial flushing (~18%), chest discomfort, dyspnea, headache — half-life is under 10 seconds, so adverse effects are generally rapidly self-terminating, which is itself a useful clinical/CDS framing point (most reactions need reassurance and observation, not intervention). |
| **Serious but rare** | Prolonged asystole, new/worsened arrhythmias including ventricular tachycardia/fibrillation and Torsades de Pointes; seizures; hemorrhagic/ischemic stroke has been reported in association with adenosine's hemodynamic effects. |
| **Critical drug interaction** | **Digoxin or verapamil use may be rarely associated with ventricular fibrillation when combined with adenosine** — the label calls this out explicitly. Both digoxin and verapamil are in this same catalogue, making this a concrete, encodable interaction rule rather than a generic caution. |
| **Other interactions** | Dipyridamole potentiates adenosine's effects — withhold 5 half-lives before dosing (**dipyridamole is not on the SEML**). Methylxanthines (caffeine, theophylline) are competitive antagonists and blunt adenosine's effect — also withhold 5 half-lives before dosing if clinically feasible. |

#### Amiodarone (C01BD01 — Class III antiarrhythmic)

The most multi-system-toxic drug in this catalogue — overall adverse reaction
rate is roughly three-quarters of patients at maintenance dose, with
discontinuation in 7–18%.

| Organ system | Complication |
|---|---|
| **Pulmonary** | The signature toxicity — pulmonary infiltrates/fibrosis, interstitial pneumonitis, ARDS; incidence reported up to ~17% with up to ~10% of *those* cases fatal in some analyses. Risk factors: high daily dose (>400 mg/day), high cumulative dose (>2 months therapy), male sex, age >60, pre-existing lung disease, recent surgery/pulmonary angiography. Requires excluding heart failure, infection, PE, and malignancy as mimics before attributing dyspnea to amiodarone. |
| **Hepatic** | Discontinue if signs/symptoms of clinical liver injury appear. Asymptomatic transaminase elevation in ~24% of patients; overt drug-induced liver injury (hepatitis, micronodular cirrhosis, hepatic failure requiring transplant) is rare but reported. |
| **Thyroid** | Both hyper- and hypothyroidism — amiodarone is iodine-rich and structurally resembles thyroid hormone. |
| **Ocular** | Corneal microdeposits (common, reversible, largely benign); optic neuropathy/neuritis (rare, can cause permanent vision loss). |
| **Cardiac** | Can itself exacerbate arrhythmias — initiate only where continuous ECG and resuscitation capability exist (this is a hospital-initiation drug, relevant if the platform ever handles medication reconciliation post-discharge). |
| **Persistence** | Because of its very long half-life, adverse reactions and drug interactions **can persist for weeks after discontinuation** — an important nuance for any "time since last dose" logic in the rules. |
| **Pregnancy** | High-risk in pregnancy — crosses the placenta, can affect fetal heart rate, thyroid function, growth, and neurodevelopment; not formally contraindicated but treated as high-risk. |
| **Key interactions** | Increases digoxin levels (both in this catalogue — direct interaction rule candidate); additive AV-nodal/SA-nodal depression with verapamil, digoxin, adenosine — all four are here, so amiodarone effectively touches every other rate-control/rhythm drug in this catalogue. |

#### Digoxin (C01AA05 — cardiac glycoside)

| | |
|---|---|
| **Core risk** | Narrow therapeutic index — the entire safety profile is about the therapeutic/toxic margin being small, not a single boxed warning. |
| **Toxicity presentation** | Early: nausea, vomiting, anorexia, diarrhea, fatigue, malaise. Neuro: confusion, headache, dizziness, classic yellow-green visual halos. Cardiac (most dangerous): AV block, bradycardia, atrial tachycardia with block, ventricular ectopy, VT/VF. ECG signs: scooped ST segments, flattened/biphasic T waves, shortened QT, prolonged PR. |
| **Absolute/relative contraindications** | Hypersensitivity to digitalis glycosides; **severe hypokalemia is an absolute contraindication** (sensitizes myocardium to digoxin — toxicity can occur even at "therapeutic" drug levels); hypercalcemia (increases arrhythmia risk via delayed afterdepolarizations); relative: renal failure, thyrotoxicosis (digoxin often ineffective), pre-cardioversion (stop >24h before if possible). |
| **Key risk factors for toxicity** | Advanced age, low body weight/lean muscle mass, renal impairment (dose based on GFR — reduce below GFR 60 mL/min), hypokalemia, hypomagnesemia, hypercalcemia, and drug interactions — **amiodarone, verapamil**, macrolide antibiotics, and diuretics are specifically named. Amiodarone and verapamil are both in this catalogue. |
| **Mortality** | Chronic digoxin toxicity carries a one-week mortality of 15–30% in the toxicology literature — this is not a "monitor and move on" drug. |
| **Antidote** | Digoxin-specific antibody fragments (DigiFab/digoxin immune Fab) is the definitive treatment for severe toxicity; standard antiarrhythmics are often refractory. |
| **CDS relevance** | This is probably the single highest-value renal + electrolyte + interaction rule in the whole catalogue — it sits at the intersection of renal dosing, potassium monitoring (shared with the ACEi/diuretic drugs elsewhere), and two other drugs in this exact category (amiodarone, verapamil). |

#### Lidocaine hydrochloride, IV antiarrhythmic use (C01BB01)

| | |
|---|---|
| **Toxicity is CNS-first, then cardiac** | Early/mild: lightheadedness, nervousness, confusion, tinnitus, blurred vision, perioral numbness — these are **warning signs**, not benign side effects, and can progress rapidly to twitching, tremor, seizures, unconsciousness, and respiratory arrest. Cardiovascular toxicity (bradycardia, hypotension, heart block, cardiovascular collapse) typically follows CNS symptoms and occurs at higher plasma levels. |
| **Contraindications** | Wolff-Parkinson-White syndrome; Adams-Stokes syndrome; advanced SA, AV, or intraventricular conduction block unless a functioning pacemaker is present; should not be used when the arrhythmia is itself caused by local-anesthetic systemic toxicity (a different drug's overdose). |
| **Who's most at risk of toxicity at "normal" doses** | Elderly, heart failure, and hepatic impairment patients — lidocaine is hepatically cleared, so reduced hepatic blood flow (as in HF or cirrhosis) raises levels at unchanged doses. |
| **Interaction flagged in the label** | Use with caution in **digitalis toxicity** specifically, and additive/antagonistic cardiac effects with other antiarrhythmics (phenytoin, procainamide, propranolol/beta-blockers, quinidine). |
| **Practical note** | Because early toxicity is entirely neurological and easy to mistake for something else (anxiety, intoxication, a TIA) in a home-care or ambulance setting, a documented "recent lidocaine dose" flag on any new confusion/dysarthria presentation would have real clinical value. |

### 10.5 Category 5 profiles — vasopressors and inotropes

**Scope caveat specific to this category:** the six vasopressors/inotropes are
IV, ICU/ambulance-acuity drugs — a meaningfully different context from the oral
home-care formulary in the other categories. If Noor's actual patient-facing
scope is home visits rather than acute/inpatient care, these six are probably
most useful for **medication-reconciliation and care-transition logic** (a
patient discharged from ICU on a weaning inotrope, or an ambulance protocol
reference) rather than active in-home dosing rules.

#### Epinephrine (C01CA24)

| | |
|---|---|
| **The critical interaction — not a side effect of epinephrine itself, but of what it's given with** | In a patient on a **non-selective** beta-blocker (propranolol, §9.1), systemic epinephrine leaves alpha-1 vasoconstriction unopposed, producing severe hypertension with reflex bradycardia, potentially progressing to stroke or cardiac arrest. Cardioselective beta-blockers (metoprolol, atenolol, bisoprolol) are much less likely to cause this, though risk rises at high plasma concentrations. |
| **Practical nuance** | Despite the theoretical risk above, emergency-medicine literature is clear that **epinephrine should still be given at the standard dose for anaphylaxis** even in a beta-blocker patient — the risk of withholding it outweighs the theoretical hypertensive-crisis risk. Glucagon is the described second-line option if epinephrine is ineffective in this scenario (bypasses the beta-receptor blockade) — a second link to the diabetes catalogue's glucagon entry. |
| **Other interactions** | MAO inhibitors and tricyclic antidepressants both potentiate epinephrine's pressor effect, risking hypertensive crisis (**neither class is on the SEML**). Exogenous thyroid hormone increases arrhythmogenic potential. |
| **CDS relevance** | If Noor ever supports anaphylaxis/emergency protocols, a "patient is on a non-selective beta-blocker" flag should soften the epinephrine-dosing guidance toward "give anyway, but be prepared to also administer glucagon," not toward withholding or reducing the epinephrine dose. |

#### Norepinephrine (C01CA03)

| | |
|---|---|
| **Extravasation → tissue necrosis** | The dominant, well-documented risk, especially via peripheral IV — case reports describe bulla formation and subcutaneous ischemia within 48 hours of peripheral infusion. Antidote is local phentolamine (an alpha-1 antagonist) infiltration, effective if given within 12 hours. Central line is preferred above ~0.1 mcg/kg/min, though peripheral administration for up to 24 hours at lower doses/larger-gauge catheters is increasingly considered acceptable in the emergency-medicine literature — this is evolving practice, not a fixed rule. |
| **Gangrene** | Reported specifically in patients with pre-existing occlusive/thrombotic vascular disease or on prolonged/high-dose infusions — an important risk-stratifier if diabetic PAD patients (macrovascular complications) end up on this drug. |
| **Cardiac** | Arrhythmias; reflex bradycardia from the hypertensive response; abrupt discontinuation can cause marked rebound hypotension — taper, don't stop suddenly. |
| **Hypersensitivity** | Formulations containing sodium metabisulfite (a sulfite) can trigger allergic-type reactions in susceptible individuals. |

#### Dobutamine (C01CA07)

| | |
|---|---|
| **Contraindication** | Idiopathic hypertrophic subaortic stenosis (HOCM) — increases the LV outflow pressure gradient and worsens cardiac output in this specific population. |
| **Cardiac risk** | Can cause marked increases in heart rate (≥30 bpm in ~10% of patients) and systolic BP (≥50 mmHg in ~7.5%) — usually reverses with dose reduction. Facilitates AV conduction, so **atrial fibrillation patients are at risk of rapid ventricular response**. Toxicity can progress to tachyarrhythmias, myocardial ischemia, and ventricular fibrillation. |
| **Hypotension** | Can occur via beta-2-mediated vasodilation, especially in dehydrated/hypovolemic patients — correct hypovolemia first. |
| **Other** | Hypokalemia; local tissue necrosis with extravasation (less severe than norepinephrine/dopamine, but still reported); increased mortality with prolonged infusion, thought to relate to increased myocardial oxygen demand — this drug is meant to be short-term support, not a chronic therapy. |
| **Antagonist relationship** | Beta-blockers can blunt dobutamine's inotropic effect (opposing mechanisms) — worth flagging if a patient is transitioned between the two in a care-setting change. |

#### Milrinone (C01CE02)

| | |
|---|---|
| **Most feared complication** | Ventricular tachyarrhythmia — can lead to cardiac ischemia or sudden cardiac death; **not clearly dose-dependent**, which limits the value of a simple dose-ceiling rule and argues for continuous monitoring instead. |
| **Thrombocytopenia** | Specifically documented with milrinone (more historically with amrinone) — dose-dependent, more common with prolonged therapy; one cohort found platelet counts falling to a minimum of ~82,000/µL in 2% of patients, attributed to milrinone in 1%. Reduce dose or discontinue if platelets fall below 150,000/mm³ or symptoms develop. |
| **Other** | Elevated LFTs; increased mortality with long-term use (same "short-term bridge, not chronic therapy" framing as dobutamine); headache (~4%); myocardial ischemia symptoms (~1%). |
| **CDS relevance** | If milrinone and digoxin (§9.4) or spironolactone (§9.3) ever appear together in a discharge summary, a platelet-count check makes sense as a shared monitoring point given milrinone's own thrombocytopenia risk plus spironolactone's potassium interactions. |

#### Vasopressin (H01BA01)

| | |
|---|---|
| **Ischemia — the class-defining risk** | As a pure, potent vasoconstrictor (unlike the catecholamines, which have some vasodilating beta-effect), vasopressin can cause coronary, mesenteric, skin, and digital ischemia — including reported myocardial infarction and bowel ischemia. Caution specifically flagged in coronary artery disease, prior thrombosis, and heart failure with impaired myocardial function (afterload increase can worsen stroke volume). |
| **Hyponatremia** | Mechanistically distinct from the other vasopressors — via V2-receptor-mediated water reabsorption at the renal collecting duct. Can become severe enough to cause altered mental status, seizures, coma. |
| **Extravasation** | Tissue necrosis, same central-line preference as norepinephrine. |
| **Other** | Bronchoconstriction/bronchospasm; hypersensitivity up to anaphylaxis; rare Torsades de Pointes at overdose; thrombotic risk via enhanced platelet aggregation (V2-receptor-mediated von Willebrand factor release) in patients with existing thrombosis risk factors. |
| **Interactions** | Additive pressor effect with catecholamines (i.e., stacking with norepinephrine/epinephrine/dopamine, which is sometimes intentional in refractory shock — not automatically an error, but worth a "expected combination, monitor accordingly" flag rather than a hard stop). Indomethacin prolongs its effect (**indomethacin is not on the SEML**). |

#### Dopamine hydrochloride (C01CA04)

| | |
|---|---|
| **Contraindication** | Pheochromocytoma — absolute. |
| **Extravasation → necrosis, and gangrene at high/prolonged doses** | Same phentolamine-infiltration antidote as the other catecholamines above. Occlusive vascular disease (atherosclerosis, Raynaud's, diabetic endarteritis — again, a direct link to the diabetic macrovascular population) is a specific risk factor for this. |
| **Paradox worth flagging explicitly** | In hypovolemic hypotension, dopamine can produce severe visceral/peripheral vasoconstriction, reduced renal perfusion, tissue hypoxia, and lactic acidosis **despite a "normal" blood pressure reading** — correcting volume status before/alongside dopamine matters more than the BP number alone. |
| **Cardiac** | Arrhythmias — monitor closely; abrupt discontinuation risks marked rebound hypotension, same taper logic as norepinephrine. |
| **Interactions** | MAO inhibitors and tricyclic antidepressants both risk severe hypertension (same mechanism as the epinephrine interaction above) — dose reduction specifically recommended with MAOIs (**neither class is on the SEML**). Halogenated anesthetics sensitize the myocardium to dopamine, risking ventricular arrhythmias. |
| **Note on the "renal-dose dopamine" myth** | Not directly sourced in this pass, but worth flagging since it's a commonly outdated belief still circulating clinically — the historical idea of a protective "renal-dose" (low-dose) dopamine for kidney protection has been discredited in the critical-care literature. Confirm against current SPC/guideline text before encoding any dose-tier logic that implies renal benefit at low doses. |

### 10.6 Category 6 profiles — anti-thrombotic and lipid-lowering therapeutics

#### Acetylsalicylic acid / aspirin (B01AC06)

| | |
|---|---|
| **GI bleeding** | The headline risk — irreversibly inhibits platelet COX-1 for the platelet's lifetime (7–10 days), so bleeding risk persists well after the last dose. Risk rises with age, alcohol use (≥3 drinks/day specifically flagged), prior GI disease, and concurrent NSAID use. |
| **Reye's syndrome** | Absolute contraindication in children/teenagers with viral illness (flu, chickenpox) — acute encephalopathy plus fatty liver degeneration, often fatal. |
| **Aspirin-exacerbated respiratory disease (AERD / Samter's Triad)** | Asthma + nasal polyps + aspirin sensitivity — can trigger severe, life-threatening bronchospasm. |
| **Contraindications** | Active peptic ulcer disease, bleeding disorders (hemophilia, von Willebrand disease), severe hepatic impairment, known NSAID hypersensitivity. |
| **Other** | Tinnitus at high/salicylate-toxic doses; hyperkalemia and reduced renal function reported (shared mechanism with other NSAIDs) — relevant given how many potassium-sensitive drugs (ACE inhibitors, spironolactone) are already on the catalogue. |
| **CDS relevance** | Aspirin's renal/potassium effect plus ACEi/spironolactone is a smaller version of the "triple whammy" pattern flagged in §8 — worth folding into that same rule rather than treating as a separate one. |

#### Clopidogrel (B01AC04)

| | |
|---|---|
| **Boxed warning: CYP2C19 poor metabolizers** | Clopidogrel is a prodrug requiring CYP2C19 activation. Poor/intermediate metabolizers get materially less antiplatelet effect and have higher rates of major adverse cardiovascular events (stent thrombosis, recurrent MI/stroke) at standard dosing. Genetic testing exists to identify this; the label recommends considering an alternative P2Y12 inhibitor (i.e., ticagrelor, also in this category) for confirmed poor metabolizers. This is a pharmacogenomic rule the CDS could genuinely encode if genotype data is ever available. |
| **Bleeding** | Class effect, same mechanism-driven risk as the rest of this section. |
| **Thrombotic thrombocytopenic purpura (TTP)** | Rare but specifically labeled — a medical emergency, distinct from ordinary bleeding risk. |
| **Key interaction** | **Omeprazole and esomeprazole significantly reduce clopidogrel's antiplatelet activity** via CYP2C19 inhibition — avoid this specific combination; pantoprazole/lansoprazole/dexlansoprazole have materially less effect and are the preferred PPI choice alongside clopidogrel. This is a very common real-world prescribing collision (cardiac patient + reflux) worth a direct rule. **Only esomeprazole is on the SEML, and the card may not recommend pantoprazole** (SSOT §R-2) — see §9.6 analysis. |
| **Discontinuation risk** | Premature discontinuation raises cardiovascular event risk — don't stop without a clear plan; discontinue 5 days before elective major-bleeding-risk surgery specifically. |

#### Ticagrelor (B01AC24)

| | |
|---|---|
| **Boxed warning: bleeding** | Same class-level fatal-bleeding risk as clopidogrel, framed strongly enough to be its own boxed warning. |
| **Unique boxed-warning-adjacent rule: aspirin dose cap** | Maintenance aspirin dose **must stay at 75–100 mg/day** when combined with ticagrelor — doses above 100 mg measurably reduce ticagrelor's effectiveness (shown in the PLATO trial). This is a genuinely unusual "more of drug A makes drug B worse" interaction, and a clean, encodable dose-ceiling rule if the system ever tracks aspirin dose specifically (not just presence/absence). |
| **Contraindications** | History of intracranial hemorrhage (high recurrence risk), active pathological bleeding, severe hepatic impairment, hypersensitivity (including angioedema). Not for patients heading to urgent CABG. |
| **Dyspnea** | Reported meaningfully more often than with clopidogrel (~14% in some trial data) — mechanism thought to be adenosine-mediated, unrelated to any cardiac or pulmonary pathology, and typically self-limiting; doesn't usually require stopping the drug. Worth encoding as "expected, don't over-escalate" rather than an automatic red flag, though ruling out a cardiac/pulmonary cause first is still standard practice. |
| **Ventricular pauses / bradyarrhythmia** | A real, labeled signal (6.0% vs. 3.5% with clopidogrel in a Holter substudy) — patients with sick sinus syndrome, high-grade AV block, or bradycardia-related syncope without a pacemaker were excluded from ticagrelor's pivotal trials, so caution is warranted in exactly that population. |
| **CYP3A4 interaction** | Ticagrelor is metabolized via CYP3A4 — avoid strong CYP3A inhibitors. |

#### Tirofiban (B01AC17 — GP IIb/IIIa inhibitor)

| | |
|---|---|
| **Profound thrombocytopenia** | The signature risk — can occur acutely (platelets have dropped to critically low levels within 24 hours in reported cases). Monitor platelets ~6 hours after starting, then daily. If count falls below 90,000/mm³, rule out pseudothrombocytopenia; if confirmed, **discontinue both tirofiban and any concurrent heparin**. Risk factors identified in one large cohort: age ≥65, elevated WBC, diabetes, heart failure, CKD — notably, diabetes and CKD are both squarely in the existing patient population. |
| **Bleeding** | The single most common adverse reaction overall, mostly at the arterial catheterization access site. |
| **Renal dosing** | Explicitly dose-reduced in severe renal insufficiency (clearance drops sharply below CrCl 30 mL/min) — a clean renal-gate candidate matching the architecture's existing eGFR/CrCl pattern. |
| **Contraindications** | Active internal bleeding, bleeding diathesis, intracranial hemorrhage/neoplasm/AVM/aneurysm history, hemorrhagic stroke or any stroke, major surgery/trauma within 30 days, aortic dissection, severe hypertension, acute pericarditis, concurrent use of another GP IIb/IIIa inhibitor. |

#### Alteplase (B01AD02 — tissue plasminogen activator)

| | |
|---|---|
| **Intracranial hemorrhage** | The dominant, dreaded complication — in stroke trials, total intracranial bleeding occurred in 15.4% of alteplase patients vs. 6.4% placebo. This is why eligibility screening for thrombolysis is so exhaustive (time window, BP control, no recent surgery/trauma, no bleeding diathesis, etc.) — a narrow-window, high-consequence drug where the exclusion checklist essentially *is* the safety profile. |
| **Orolingual angioedema — and the direct connection to Category 2** | Can partially obstruct the airway; **ACE inhibitor use is a specifically identified risk multiplier** — one study found an odds ratio of 7.72 for severe angioedema in ACE-inhibitor users receiving alteplase, with a proposed mechanism of plasmin-driven bradykinin accumulation (the exact same bradykinin pathway that causes ACEi cough). **Any patient on lisinopril, captopril, or enalapril (all §9.2) who might ever receive alteplase is a meaningfully higher angioedema risk** — one of the strongest, most concrete cross-category findings in this whole project. |
| **Combination bleeding risk** | Co-administration with antiplatelets (aspirin, clopidogrel — same category) or anticoagulants significantly raises hemorrhagic transformation/intracranial hemorrhage risk in stroke patients, per a large Japanese adverse-event-database analysis. Hypertension and diabetes were both independently identified as risk factors for alteplase-induced hemorrhagic transformation — again, directly the patient population. |
| **Other** | Cholesterol embolism syndrome (rare, can present as pancreatitis, renal failure, gangrenous digits); reperfusion arrhythmias after coronary thrombolysis; hypersensitivity/anaphylaxis. |
| **Practical note** | Blood glucose should be checked before administration — hypo/hyperglycemia can mimic stroke and lead to inappropriate alteplase use. Direct link to the diabetes catalogue's glucose-management content. |

#### Atorvastatin (C10AA05 — HMG-CoA reductase inhibitor / statin)

| | |
|---|---|
| **Myopathy / rhabdomyolysis** | The class-defining serious risk — muscle aches or weakness with CPK >10x ULN defines myopathy; rare progression to rhabdomyolysis can cause myoglobinuria-driven acute kidney injury and, rarely, death. Renal impairment is itself a risk factor for developing rhabdomyolysis (even though atorvastatin dosing doesn't need adjustment for renal impairment — an easy point of confusion worth flagging explicitly in a rule's documentation). |
| **Hepatotoxicity** | Transaminase elevation is dose-related; contraindicated in active liver disease or unexplained persistent transaminase elevation. Hepatic impairment dramatically increases exposure — mild (Child-Pugh A): ~4-fold increase in levels; moderate (Child-Pugh B): ~16-fold; **acute liver failure or decompensated cirrhosis is a contraindication outright.** |
| **New-onset diabetes / glycemic effects** | A regulator-acknowledged class signal — increases in HbA1c and fasting glucose have been reported; monitor more closely in the existing diabetic population rather than treating this as a reason to avoid statins, since the cardiovascular benefit still generally outweighs this risk in patients who need one. |
| **Key interaction — direct connection to Category 1/4** | **Verapamil (§9.1) is a moderate CYP3A4 inhibitor and measurably raises atorvastatin levels (roughly 2–3x)**, increasing myopathy/rhabdomyolysis risk — sources specifically suggest capping atorvastatin at 20 mg/day if the combination is necessary. **Amiodarone (§9.4)** carries the same CYP3A4-inhibition mechanism; a published case report describes rhabdomyolysis, AKI, and transaminitis from a three-way interaction between a statin, amiodarone, and ticagrelor (itself also a CYP3A4 substrate/inhibitor, and in this same category) — a genuinely concrete example of exactly the kind of multi-drug polypharmacy risk the architecture is trying to catch. |
| **Common AEs** | Nasopharyngitis (~7%), arthralgia (~10.6%), diarrhea (~14.1%), pain in extremity (~9.3%), UTI (~8%) — none individually alarming, but worth having as expected-noise baseline so a home-care nurse doesn't over-escalate routine statin-associated aches. |

### 10.7 What remains open before rule-writing

Per the roadmap checklist, each drug above still needs, sourced against the
actual local SPC: exact renal dosing table (eGFR vs. CrCl, per SSOT §5.2);
hepatic dosing (Child-Pugh, per §3.2); monitoring interval after
initiation/dose change, with label version (§7.1 `monitors`);
pregnancy/lactation narrative (§11 below), not a letter category; and
confirmation of `source_family` pinning per the architecture. This section
covers only the "what can go wrong" half of the picture.

---

## 11. Pregnancy, Breast-feeding, and Fertility — three propositions per SSOT §3.2

The matrices above carry the **`pregnancy` proposition only**. SSOT §3.2
requires three per drug, each with its own pointer into §4.6 of the pinned
label, and **`not_stated_in_label` is a distinct recorded state — never read as
reassurance.** Collapsing an absent statement into "no known risk" is the FDA
letter category re-invented, which §R-3 forbids.

Because `source_label.status` is `unretrieved` throughout, **all three
propositions are unpopulated for all 34 ingredients** and the pointer column is
empty. What the table below holds is a research draft of the first proposition,
nothing more.

| Proposition | SmPC §4.6 sub-topic | US PLLR analogue | Current state in this file |
|---|---|---|---|
| `pregnancy` | Pregnancy | 8.1 | draft narrative in the table below |
| `breast_feeding` | Breast-feeding | 8.2 | **absent for all 34** — only glyceryl trinitrate's row mentions milk at all |
| `fertility` | Fertility | 8.3 | **absent for all 34** |

`fertility` is not a formality in this catalogue. Spironolactone, amiodarone,
methyldopa and the statins all carry fertility-relevant statements, and home
healthcare in Saudi Arabia includes women of reproductive age on chronic
antihypertensives — the proposition that gets skipped is the one that matters
to them.

| Ingredient | `pregnancy` (draft) | §4.6 pointer |
|---|---|---|
| **Metoprolol tartrate** | Reduced placental perfusion; risk of fetal bradycardia, hypoglycemia, IUGR | ⛔ unretrieved |
| **Metoprolol succinate** | Decreases uterine blood flow; monitor fetal growth; discontinue 48–72h before delivery if possible | ⛔ unretrieved |
| **Carvedilol** | Embryotoxic in animal studies; fetal bradycardia and neonatal hypoglycemia risk; avoid during pregnancy | ⛔ unretrieved |
| **Propranolol** | Placental hypoperfusion; fetal hypoglycemia, bradycardia, respiratory depression at birth | ⛔ unretrieved |
| **Verapamil** | Crosses placenta; risk of fetal bradycardia, hypotension, uterine relaxation; use only if compelling | ⛔ unretrieved |
| **Nifedipine** | Contraindicated before week 20; severe maternal hypotension and fetal hypoxia if combined with IV MgSO4 | ⛔ unretrieved |
| **Amlodipine** | Safety in human pregnancy not established; potential for prolonged labor; use only when safer alternatives lack | ⛔ unretrieved |
| **Glyceryl trinitrate** | Animal studies insufficient; presence in breast milk unknown; prescribe only under critical maternal need | ⛔ unretrieved |
| **Isosorbide dinitrate** | No definitive human pregnancy data; maternal hypotension impairs uteroplacental perfusion | ⛔ unretrieved |
| **Lisinopril** | Contraindicated in 2nd/3rd trimesters; fetal renal failure, oligohydramnios, skull hypoplasia | ⛔ unretrieved |
| **Captopril** | Teratogenic; severe fetal renal dysplasia, neonatal hypotension, death if exposed in 2nd/3rd trimesters | ⛔ unretrieved |
| **Enalapril** | Strictly contraindicated in 2nd/3rd trimesters; fetotoxicity, fetal hypotension, renal injury | ⛔ unretrieved |
| **Losartan** | Contraindicated during 2nd/3rd trimesters; damages fetal kidney development, causes oligohydramnios | ⛔ unretrieved |
| **Methyldopa** | Drug of choice for pregnancy-induced hypertension; extensive safety history; monitor infant | ⛔ unretrieved |
| **Hydralazine** | Established safety in pregnancy-induced hypertension and pre-eclampsia; monitor fetal heart rate | ⛔ unretrieved |
| **Hydrochlorothiazide** | Avoid routine use; reduces plasma volume and placental perfusion; risk of fetal/neonatal thrombocytopenia | ⛔ unretrieved |
| **Furosemide** | Crosses placenta; causes fetal diuresis; avoid unless treating maternal cardiac edema; monitor fetal growth | ⛔ unretrieved |
| **Spironolactone** | Contraindicated in pregnancy; feminization of male fetus in animal studies; excreted in breast milk | ⛔ unretrieved |
| **Adenosine** | Safe for acute SVT conversion in pregnancy; short half-life (<10 sec) limits fetal exposure | ⛔ unretrieved |
| **Amiodarone** | Crosses placenta; fetal goiter, hypothyroidism, growth retardation; reserve for life-threatening dysrhythmias | ⛔ unretrieved |
| **Digoxin** | Crosses placenta; altered maternal volume of distribution requires serum level monitoring to maintain efficacy | ⛔ unretrieved |
| **Lidocaine** | Crosses placenta rapidly; fetal neuro-behavioral depression and bradycardia at high maternal doses | ⛔ unretrieved |
| **Epinephrine** | Uterine artery vasoconstriction; reduces uterine blood flow; reserve for maternal anaphylaxis or cardiac arrest | ⛔ unretrieved |
| **Norepinephrine** | Severe uterine vasoconstriction; reduces placental perfusion; perform continuous fetal heart monitoring | ⛔ unretrieved |
| **Dobutamine** | Safety in human pregnancy not established; potential fetal tachycardia; reserve for severe cardiogenic shock | ⛔ unretrieved |
| **Milrinone** | Crosses placenta; insufficient human data; potential for fetal hypotension; restrict to refractory maternal HF | ⛔ unretrieved |
| **Vasopressin** | Oxytocic action; stimulates uterine contractions and vasoconstriction; avoid unless refractory shock | ⛔ unretrieved |
| **Dopamine** | May cause maternal ventricular arrhythmias and uterine hypoperfusion; reserve for severe hemodynamics | ⛔ unretrieved |
| **Acetylsalicylic acid** | Low-dose (75–150 mg) safe for pre-eclampsia; high doses in 3rd trimester cause premature closure of ductus arteriosus | ⛔ unretrieved |
| **Clopidogrel** | Lack of clinical data; as a precaution, avoid during pregnancy and breast-feeding | ⛔ unretrieved |
| **Ticagrelor** | Avoid during pregnancy; animal studies demonstrate reproductive toxicity and reduced fetal weight | ⛔ unretrieved |
| **Tirofiban** | Avoid during pregnancy unless absolutely necessary; potential risk of maternal and fetal hemorrhage | ⛔ unretrieved |
| **Alteplase** | High bleeding risk for placenta; reserve for life-threatening maternal PE or ischemic stroke | ⛔ unretrieved |
| **Atorvastatin** | Strictly contraindicated in pregnancy and lactation; lipophilic statins disrupt essential fetal cholesterol synthesis | ⛔ unretrieved |

---

## 12. Strength Achievability against the SEML (SSOT §3.2)

A dose no listed strength can produce is not a recommendation. Every
dose-adjustment rule declares one of `strength_achievable | achievable_by_division
| unachievable`; an unachievable target routes to pharmacist review rather than
rendering as an instruction. This is the same failure class as proposing an
unstocked agent (§R-2).

Strengths below are verbatim from `saudi-essential-medicines-list-2023.md`
§12–§13.

| Ingredient | SEML strengths | Target dose in this file | Verdict |
|---|---|---|---|
| Metoprolol tartrate | §12.1/12.2/12.3 `Tablet: 50 mg, 100 mg` | no reduced start specified | — |
| **Metoprolol succinate** | §12.4 `Tablet: 50 mg, 100 mg` | 12.5–25 mg in Child-Pugh B/C | **`unachievable`** — 12.5 mg needs quartering; and quartering a modified-release tablet destroys the release mechanism, so even division is not a workaround. Route to pharmacist review |
| Carvedilol | §12.1 `Tablet: 3.125 mg, 6.25 mg, 12.5 mg, 25 mg`; §12.2/12.3/12.4 list to 12.5 mg | contraindicated Child-Pugh B/C, no reduced dose | `strength_achievable` — the widest strength range in this file, and the one agent whose titration the formulary genuinely supports |
| Propranolol | §12.3 `Tablet: 10 mg, 40 mg, 80 mg`, `Oral solution: 8 mg/ml`, `Solution for injection: 1 mg/ml` | 50% reduction in Child-Pugh B/C | `strength_achievable` — the oral solution makes any halving exact, which no tablet-only agent here can claim |
| Verapamil | §12.1/12.2 `Tablet: 40 mg, 80 mg` + `Solution for injection: 2.5 mg/ml` — tablet strengths owner-confirmed against the original PDF (2026-08-17) | 50–70% reduction in Child-Pugh B/C | A 50–70% reduction is a *range*, not a dose, and needs a target before achievability can be judged at all; the 40/80 mg strengths make halved doses representable (`achievable_by_division`) once the pinned label names the absolute target |
| Nifedipine | §12.1 `Tablet: 30 mg` (extended-release) + `Capsule: 10 mg` (immediate-release) — owner-confirmed against the original PDF (2026-08-17) | 50% reduction of extended-release maintenance | The capsule is immediate-release and the 30 mg tablet is extended-release — **they are not interchangeable**, and a 50% ER reduction cannot be met by IR capsules. A label-stated 50% target of 30 mg would be 15 mg, which no listed strength delivers — `unachievable` unless the label names a different absolute target |
| **Amlodipine** | §12.1/12.3 `Tablet: 5 mg` **only** | 2.5 mg initial in Child-Pugh A/B/C | **`achievable_by_division`** — halving the only listed strength. The hepatic starting dose for the most-prescribed antihypertensive in the catalogue cannot be dispensed as a whole tablet in Saudi Arabia |
| **Glyceryl trinitrate** | §12.1 `Solution for injection: 5 mg/ml` **only** | anti-anginal use with a 10–12h nitrate-free window | **`unachievable` for home care** — no sublingual tablet, spray, patch, or ointment is listed. An IV-only nitrate has no home-visit dose form, so **isosorbide dinitrate `Sublingual tablet: 2.5, 5, 10, 20 mg` (§12.1) is the home-relevant nitrate** and should carry the nitrate rules |
| Isosorbide dinitrate | §12.1 `Sublingual tablet: 2.5 mg, 5 mg, 10 mg, 20 mg` | no reduced dose specified | `strength_achievable` |
| **Lisinopril** | §12.3 `Tablet: 5 mg, 10 mg` | 2.5 mg initial if eGFR low | **`achievable_by_division`** |
| Captopril | §12.3 `Tablet: 25 mg, 50 mg` | 25% then 50% reduction by CrCl band | `achievable_by_division` — a 25% reduction of 25 mg is 18.75 mg, which no combination of halves and quarters yields. Reductions expressed as percentages of a two-strength formulary are not dosing advice; the rule needs an absolute target from the label |
| **Enalapril maleate** | §12.4 `Tablet: 5 mg, 10 mg` | 2.5 mg/day start if eGFR low | **`achievable_by_division`** |
| Losartan / losartan potassium | §12.3 and §12.4 `Tablet: 25 mg, 50 mg, 100 mg` | 25 mg in Child-Pugh A/B | `strength_achievable`. **These are one ingredient**, listed under two names in the roadmap and in two SEML subsections — one `ingredient_id`, not two. Furosemide, spironolactone and hydrochlorothiazide are likewise each listed twice (heart failure and diuretics); the roadmap's 38 cardiovascular entries are **34 distinct ingredients** |
| **Methyldopa** | §12.3 `Tablet: 250 mg` **only** | interval extension by renal band | `strength_achievable` **because the adjustment is to the interval, not the dose** — which is the one renal adjustment a single-strength formulary can actually deliver |
| **Hydralazine** | §12.3 `Tablet: 25 mg` **only** | interval extension q8h / q8–12h by CrCl; plus IV use in pre-eclampsia | oral: `strength_achievable`. **IV: `unachievable` — no injection is listed.** The pre-eclampsia claim in this file rests on the parenteral form and has no SEML dose form; the SEML parenteral agents for that indication are labetalol-class alternatives not present here, so this must not render as an obstetric recommendation |
| Hydrochlorothiazide | §12.3/12.4/13 `Tablet: 12.5 mg, 25 mg` | ineffective below an eGFR threshold → switch | `strength_achievable`; the switch target (furosemide) is on the SEML |
| Furosemide | §12.4/13 `Tablet: 40 mg`, `Oral solution: 1 mg/ml`, `Syrup: 1 mg/ml`, `Solution for injection: 10 mg/ml` | high doses in low eGFR; max bolus rate | `strength_achievable` |
| **Spironolactone** | §12.4/13 `Tablet: 25 mg, 100 mg` | 50% reduction on mid-band K⁺ | **`achievable_by_division`** — 12.5 mg from a 25 mg tablet, 50 mg from a 100 mg tablet. No 12.5 mg or 50 mg strength is listed, so the card must state division explicitly rather than print "halve the dose" |
| Digoxin | §12.2/12.4 `Tablet: 0.125 mg, 0.25 mg`, `Oral solution: 0.05 mg/ml`, `Solution for injection: 0.25 mg/ml` | 50% empiric reduction with P-gp inhibitors | `strength_achievable` — 0.25 → 0.125 mg is a listed strength, and the oral solution covers finer steps |
| Amiodarone | §12.2 `Tablet: 200 mg`, `Solution for injection: 50 mg/ml` | no renal/hepatic dose reduction | `strength_achievable` |
| Milrinone | §12.5 `Solution for injection: 1 mg/ml` | 0.20–0.43 mcg/kg/min by CrCl | pump-rate constrained, not strength-constrained — see *Category 5* |
| Tirofiban | §12.6.1 `solution for infusion: 0.25 mg/ml` | 50% infusion-rate reduction below a CrCl threshold | infusion-rate adjustment; `strength_achievable` |
| Acetylsalicylic acid | §12.6.1 `Tablet: 81 mg, 100 mg, 300 mg` | low-dose 75–150 mg | `strength_achievable` — 81 mg and 100 mg both fall in the band; **75 mg specifically is not listed**, so a rule must state the band, not the number |
| Clopidogrel | §12.6.1 `Tablet: 75 mg` | no renal adjustment | `strength_achievable` |
| Ticagrelor | §12.6.1 `Tablet: 60 mg, 90 mg` | no renal adjustment | `strength_achievable` |
| Atorvastatin | §12.7 `Tablet: 10 mg, 20 mg, 40 mg, 80 mg` | — | `strength_achievable`. **The amlodipine–simvastatin 20 mg cap does not transfer to it** — different statin, different CYP3A4 exposure, and simvastatin is not on the SEML at all |

Eight of the 34 ingredients are absent from the table by design, not oversight:
**adenosine, lidocaine, epinephrine, norepinephrine, dopamine, dobutamine,
vasopressin, alteplase.** All are single-concentration parenteral agents dosed by
weight or by infusion rate, so their deliverability constraint is pump resolution
and diluent concentration, not tablet division — the same class of problem as
milrinone (*Category 5*), and none of them is a home-visit medicine. They need an
achievability model, just not this one.

---

## 13. Rule Execution and Validation Architecture

To operationalize these pharmacologic requirements within the Saudi Essential
Medicines List framework, the decision engine must implement a structured
three-tiered execution model.

**The tier names below describe *when* a rule runs, not how hard it hits.**
Severity is always one of SSOT §9.1's three values, and **"hard stop" is not one
of them** — a prior revision used it in three places. The Action column is
restated in the real ladder throughout. The red-flag operational framework (SSOT
§11.7) is governed in Part A §3; the three tiers below are the remaining
operational structures this catalogue bears on.

### 13.1 Tier 1: Static Thresholds

Tier 1 execution evaluates absolute contraindications and fixed safety cutoffs
synchronously, before order signing.

| Rule | Condition | Severity & action |
|---|---|---|
| RAAS Inhibitor Pregnancy Check | ACE inhibitor (lisinopril, captopril, enalapril) or ARB (losartan) ordered for a patient confirmed in the 2nd or 3rd trimester | `stop_and_review` — documented fetotoxicity. The strongest severity the engine has, and still not a block: the clinician may proceed with a documented reason. If trimester is unknown, §8.3 degrades this to `interruptive_review` — **which is the common case**, so it needs its own test row |
| MRA Baseline Eligibility Check | Spironolactone ordered with a baseline serum potassium at or above the eligibility threshold, or eGFR below it (both ⛔ `unpopulated`) | `interruptive_review` — one baseline potassium, possibly haemolysed, is not grounds for the top severity. Ask for the repeat first |
| Nitrate–PDE5 Intercept | Glyceryl trinitrate or isosorbide dinitrate ordered for a patient with an active PDE-5 inhibitor | `stop_and_review`. **Neither sildenafil nor tadalafil is on the SEML**, so this must trigger on the reconciled medication list rather than the dispensing record, or it never fires |

### 13.2 Tier 2: Organ Clearance and Metabolic Intercepts

Tier 2 execution evaluates organ function metrics and pharmacokinetic
interaction pathways. Renal metric selection is not a rule and does not belong
in this table — it is **CI gate 15** (SSOT §10.4); see §7.

| Rule | Condition | Severity & action |
|---|---|---|
| CYP2C19 Interaction Intercept | Clopidogrel co-prescribed with esomeprazole (on SEML) or omeprazole (not on SEML) | `interruptive_review` — state the loss of antiplatelet efficacy and the two SEML options with their tradeoff. **Do not recommend pantoprazole**; it is not on the SEML (SSOT §R-2) |
| CYP2D6 Interaction Intercept | Metoprolol co-prescribed with fluoxetine (§16.2.1). **Citalopram and paroxetine are not on the SEML** | `interruptive_review` — monitor for symptomatic bradycardia, consider dose reduction |

### 13.3 Tier 3: Temporal Monitoring Obligations

Tier 3 execution establishes automated post-initiation monitoring workflows.
Every row here is an **obligation**, and SSOT §11.8's closure invariant applies:
an obligation that is opened must be closed or explicitly deferred with a reason
— it cannot be left hanging when the visit ends.

| Rule | Trigger | Follow-up action |
|---|---|---|
| RAAS Initiation Follow-up | Initiating or titrating lisinopril, captopril, enalapril, or losartan | `passive_task`: schedule serum potassium and eGFR at 7–14 days. Tolerate the expected eGFR decline — magnitude ⛔ `unpopulated`, a prior revision gave 25% (or a 30% creatinine rise) with no source. **The tolerance is conditional on potassium staying below a stated ceiling, so it is a two-observable rule, not an eGFR rule**, and both observables must be present for it to evaluate |
| Spironolactone Protocol Execution | Following spironolactone initiation | `passive_task`: schedule serum potassium and eGFR at Day 7, Day 14, Month 1. Escalation bands and their severities are in *Category 3* (§9.3); all band values ⛔ `unpopulated` |

### 13.4 Automated Recall Systems for Missed Monitoring

Home-care/elderly: lack of follow-up is a primary cause of preventable drug
toxicity. The engine tracks required follow-up intervals on drug initiation and
on dose change.

Two fields, not one (SSOT §7.1f), and the examples below need both:

| Field | Question it answers |
|---|---|
| `monitors` | May this rule use the result I already have? Must pin the label version it came from. |
| `max_age_days` | Is the patient due for another one? |

- **Example:** serum potassium and eGFR not reassessed within `max_age_days` of
  RAAS initiation → `passive_task` recall for mobile phlebotomy. The interval is
  ⛔ `unpopulated` — a prior revision stated 7–14 days with no source.
- **Example:** potassium not rechecked within `max_age_days` of spironolactone
  initiation → `passive_task` recall. Interval ⛔ `unpopulated` — a prior
  revision stated Day 7, Day 14, Month 1 with no source.

Both intervals must come from the pinned label's monitoring section and carry
its version, per `monitors`. Neither is authorable while `source_label.status`
is `unretrieved`.

---

# Part C — Governance

## 14. Evidence and Authorability Checklist

Before a claim moves from this reference into Noor content, the author must
record:

```yaml
claim:
  id: htn.hypertensive_emergency_threshold
  proposition: "..."
  value: "..."
  unit: "..."
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

### 14.1 Required test rows

For every numeric threshold, the rule case file must contain at least:

- Just below the boundary.
- Exactly at the boundary.
- Just above the boundary.
- Missing required input.
- Stale or unusable input.
- Conflicting measurements or wrong context.
- A clinically severe presentation that must not be suppressed by a repeat.

Pairwise cases must cover the important combinations: pregnancy when in scope,
CKD, diabetes status, medication exposure, measurement quality, and competing
acute findings. Tests must assert exact outcomes: `triggered`,
`not_triggered`, `indeterminate`, or the applicable out-of-scope/governance
outcome.

---

## 15. Scope Exclusions and Deferred Work

The following are intentionally not automatic Noor conclusions unless separately
approved and sourced:

- Broad ASCVD, HF, stroke, CKD progression, or foot risk scores.
- A diagnosis of hypertensive nephrosclerosis from routine labs alone.
- A hypertensive emergency from BP alone.
- A universal ACS troponin/ECG algorithm.
- A universal stroke score or ambulance protocol.
- Automatic treatment, admission, discharge, or medication prescribing.
- Saudi emergency response times or referral destinations without provider
  policy.
- Copying protected guideline tables, heat maps, instrument descriptors, or
  proprietary decision trees into the repository or UI.

(Cross-disease exclusions — a diagnosis of DKA or HHS from glucose alone, and a
hypoglycaemia severity level from a meter value without clinical context — are
tracked in `diabetes-research.md` §16.)

---

## 16. Source Register

The following sources are candidates for verification and pinning. The source
register for executable content must include the exact edition, revision date,
locator, and jurisdiction; this bibliography alone does not satisfy that
requirement.

- ESC. *2024 Guidelines for the Management of Elevated Blood Pressure and
  Hypertension*. Relevant sections must be cited at proposition level.
- ESH. *2023 Guidelines for the Management of Arterial Hypertension*.
- Current AHA or other selected authority for severe-hypertension terminology,
  with the selected terminology explicitly pinned. The legacy term "hypertensive
  urgency" and the newer "severe hypertension" label must not be silently
  treated as identical pathways.
- KDIGO. *2024 Clinical Practice Guideline for the Evaluation and Management of
  Chronic Kidney Disease*. G/A categories and monitoring principles (shared
  with `diabetes-research.md` §3.2).
- Current Saudi hypertension, cardiovascular prevention, and home-healthcare
  guidance where available.
- Current ICD-10-AM/NPHIES coding guidance and the official ICD-10-CM guidance
  only where a CM comparison is necessary.

**Compiled:** August 2026. The reference is intentionally conservative: where a
claim is clinically plausible but the source, jurisdiction, population, or
action is incomplete, it remains a research note and cannot become a Noor rule.

---

## 17. References

**A bare domain is not a citation.** CI gate 2 requires four fields per threshold
— organisation, document, version, and locator — and a prior revision of the
pharmacotherapy research had **no reference section at all**: its only sourcing
was the string `SFDA/EMA SmPC` repeated in 30 table cells, which names no
document, no version, and no locator. Nothing in it could pass CI gate 2. That
is replaced by the two things that can be stated truthfully today: what is
actually verified, and the shape each outstanding citation owes.

### 17.1 Verified primary source (in repository)

| Organisation | Document | Version | Locator |
|---|---|---|---|
| Ministry of Health / SFDA, Kingdom of Saudi Arabia | Essential Medicines List of Saudi Arabia — `saudi-essential-medicines-list-2023.md` | 2023 | §12.1–§12.7 (cardiovascular), §13 (diuretics); other sections as cited inline |

Per SSOT §17 this is the authority for **two claims and no others**: whether an
ingredient is listed, and which strengths and dose forms are listed for it. It
carries no dosing, contraindication, interaction, or monitoring content — so it
sources the SEML columns of the matrices and the achievability table (§12), and
nothing else in this file.

Its conversion artifact dropped drug-name cells on merged rows; the rows
relevant to this catalogue were restored by the project owner against the
original PDF on 2026-08-17 (verapamil `Tablet: 40 mg, 80 mg`; nifedipine
`Tablet: 30 mg`; see the annotated converted source file).

### 17.2 Outstanding — one pinned label per ingredient, none yet satisfied

Each of the 34 ingredients owes one pinned label. The required shape, per SSOT
§3.2:

| Field | Value |
|---|---|
| `authority` | `sfda` (preferred) → `ema` → `national_agency` |
| `document` | product name exactly as the label titles it |
| `revision_date` | the label's own revision date — **not** the date it was fetched |
| `locator` | `SmPC 4.2` posology, `4.3` contraindications, `4.4` warnings, `4.5` interactions, `4.6` pregnancy |
| `fallback_from` | `{tried: [sfda.sdi], reason: "SDI e-service unreachable 2026-08-12"}` |
| `status` | `unretrieved` until all four `pinned` fields are filled |

The ladder's third rung — an EU national-agency SmPC — carries most of the
weight in this file. **Furosemide, methyldopa, hydralazine, captopril, digoxin,
propranolol and most of the older cardiovascular agents here were never
centrally authorised and have no EMA SmPC**, so an EMA-only fallback would leave
the majority of this catalogue unpinnable. That is the concrete reason SSOT §3.2
has three rungs rather than two. Confirm each on the EMA register rather than
assuming; do not treat this grouping as verified.

Where an SFDA SPC later contradicts a pinned EU label, SSOT §11.9 makes it a
**content incident**, not a silent correction.

### 17.3 Not a source

`cds-content-roadmap.md` states that SFDA SPCs are based on EMA and ICH values.
That is what makes the EU fallback *clinically* defensible, and it is not a
citation — it justifies the ladder, it does not fill in `document`,
`revision_date`, or `locator` for any of the 34 ingredients. A fallback is
recorded, never invisible, and every `fallback_from` entry is a work item for
when SDI becomes reachable.

### 17.4 Complication-profile sources (FDA-based; not EMA-equivalent)

FDA labels / DailyMed / accessdata.fda.gov (metoprolol tartrate/succinate,
verapamil, amiodarone, digoxin, lidocaine, adenosine, lisinopril, enalapril,
losartan, methyldopa, furosemide, spironolactone, hydralazine combination
products, epinephrine, norepinephrine, dopamine, vasopressin, dobutamine,
tirofiban, ticagrelor/Brilinta, clopidogrel/Plavix, alteplase, atorvastatin,
aspirin); StatPearls (NCBI Bookshelf) — nifedipine, lidocaine toxicity,
captopril, enalapril, losartan, furosemide, spironolactone, norepinephrine,
dopamine, milrinone, alteplase, atorvastatin, GP IIb/IIIa inhibitors,
inotropes/vasopressors overview; LiverTox (NIH) — carvedilol and methyldopa
hepatotoxicity; Medscape drug reference — GTN/nitroglycerin PDE5 interaction,
dosing cautions; Medsafe (NZ) — amiodarone pulmonary toxicity; EMCrit / LITFL /
RECAPEM / OpenAnesthesia — digoxin toxicity mechanisms and risk factors,
vasopressin and dopamine practical dosing/administration context; Drugs.com
clinical monographs and interaction checker — hydralazine, HCTZ, captopril,
methyldopa, furosemide, spironolactone, aspirin, atorvastatin-verapamil
interaction, ticagrelor; AMBOSS and Biomedicus clinical references — aspirin
adverse effect classification; PMC/PubMed case reports and reviews — amiodarone
multi-organ toxicity, carvedilol hepatotoxicity, lidocaine CNS toxicity at
therapeutic dose, norepinephrine extravasation, tirofiban-induced
thrombocytopenia, alteplase-ACEi angioedema odds-ratio study, alteplase
hemorrhagic transformation database analysis (Japanese ADR database),
atorvastatin-amiodarone-ticagrelor rhabdomyolysis case report,
dobutamine/milrinone arrhythmia management review, HCTZ non-melanoma skin cancer
(IARC/EMA classification), losartan hepatotoxicity case reports,
hydralazine-induced ANCA vasculitis, MERIT-HF trial data; HealthRx/FAERS-sourced
pharmacovigilance summary — lisinopril angioedema demographic risk;
ScienceDirect topic reviews — digoxin toxicity, lidocaine CNS toxicity; CHEST/
CMAJ case reports — alteplase angioedema mechanism.

*Cross-check every claim in §10 against the current SFDA-registered SPC or EMA
SmPC before any threshold is cited in a rule.*

---

Implementing these parameter-rich rules aligns decision support software with
SFDA and EMA/ICH SmPC standards, supporting medication safety across
cardiovascular populations — **once the labels behind them are pinned.** Until
then this file is a research draft, and the CI gates will say so.