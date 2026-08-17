# Clinical Signal and Observable Catalogue — Draft Register (workstream 6)

**Status:** Research draft — **not approved terminology. Nothing in this file is
authorable or executable.** No identifier, value set, mapping, or unit becomes a
governed registry record until the terminology owner and clinical content owner
approve it and the SSOT terminology charter (SSOT §3.3) exists.

**Relationship to the research files.** `diabetes-research.md` §1.2 and
`hypertension-research.md` §1.2 hold candidate concepts; this file consolidates
them and completes the six signal groups required by the remediation plan's
workstream 6. Signals shared across files are deliberately single records here;
the research files keep their deliberate duplication so each stands alone.
Candidate identifiers from the research files are preserved verbatim.

**Rules that read signals.** Rules read structured observations only. They never
read `encounter_narrative` and never infer a diagnosis from free text (SSOT §5,
remediation plan workstream 6 exit criteria). A patient-reported fact and a
staff-observed fact remain distinguishable through `entry_mode` and
`informant`.

---

## 1. Naming convention (proposal, pending registry assignment)

| Prefix | Meaning | Typical `entry_mode` |
|---|---|---|
| `symptom_` | Patient-reported symptom | `patient_reported` |
| `finding_` | Staff-observed sign or measurement finding | `staff_transcribed` |
| `medication_` | Structured medication-use assessment | `staff_transcribed` or `patient_reported` |
| `measure_` | Numeric measurement or laboratory observable | `interfaced` (labs), `staff_transcribed`, `device_memory`, `noor_derived` |
| `clinician_` | Clinician-documented finding or status | `staff_transcribed` |

## 2. Shared record contract (applies to every record below)

Per SSOT §5 and §6, each registry record will carry: stable Noor identifier and
clinical definition; value type, permitted values, and UCUM unit where numeric;
source-code mapping (LOINC/SNOMED); official source display retained separately
from Arabic UI text; terminology edition/release, mapping method, confidence,
and owner; permitted `entry_mode` values and mandatory `informant` behavior;
method/specimen/setting/posture/laterality/timing context fields; accepted
`source_status` values; and quality behavior through `canon`.

- **Absence.** A missing or absent value is never normal, safe, or zero. An
  `absent_reason` recorded by the source is its own field; absence with a
  reason and absence without one are different facts (SSOT §5).
- **Ambiguity and unmapped.** `mapping.status: ambiguous | unmapped` is a
  visible workflow state routed to a human; the observation reaches `canon` as
  unusable, never as a guessed value (SSOT §5, §6.3).
- **Contradiction.** Observations are written once and never overwritten;
  corrections arrive as new observations with a higher `source_version`.
  Contradictory values are preserved as separate facts and never averaged; how
  a rule handles them is rule-level behavior, not a registry decision.
- **Freshness.** No record carries a freshness stamp. `max_age_days` is per
  rule, per evaluation (SSOT §5.1). This catalogue records context that affects
  interpretation — not ages.
- **Quality.** `canon` verdicts (unit resolution, accepted `source_status`,
  delta comparability) gate what enters the snapshot (§6). A signal that fails
  quality is unusable, not silently approximated.
- **Derived values.** Every derived observable records its inputs and
  conversion. Conversions are reversible within declared precision; e.g. the
  glucose mg/dL ↔ mmol/L factor and the reported-eGFR vs noor-derived-eGFR
  split (SSOT §5.2).
- **Informant.** `entry_mode: patient_reported` requires `informant`:
  `patient` or the named `medicine_manager` (SSOT §5.4, §5.7). Medication-use
  signals in particular must say who reported them — the person who fills the
  pill box and a patient with cognitive impairment are different grades of
  evidence. "Caregiver report" is carried by the informant field, not by a
  separate signal.

## 3. Terminology mapping policy (pending the charter)

- **LOINC** for laboratory and measurement observables. Codes below are
  **candidates only**, marked with confidence; every code must be verified
  against the current LOINC release by the terminology owner, and the edition
  recorded. LOINC attribution requirements apply (§13.2).
- **SNOMED CT** for clinical meaning. **No SNOMED CT concept IDs or display
  strings are reproduced in this file** while the Saudi Affiliate licence is
  outstanding (remediation plan workstream 6 terminology prerequisites). The
  `snomed_domain` column names the concept area only.
- **Arabic labels** are kept separate and route through the patient-use gate
  (§13.2); none are proposed here.
- **Owner.** Mapping owner for every record: **Youssef Sabry (terminology
  owner, appointed 2026-08-17)**. Mapping method and confidence are recorded
  per record at approval time.

---

## 4. Signal groups

### 4.1 Diabetes acute illness

| Identifier | Clinical definition | Permitted values / unit | entry_mode | informant | Context / method | Mapping |
|---|---|---|---|---|---|---|
| `symptom_polyuria` | Increased urine output reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | — | snomed_domain: symptom; LOINC: none applicable |
| `symptom_polydipsia` | Increased thirst reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | — | snomed_domain: symptom |
| `symptom_nausea_vomiting` | Nausea or vomiting reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | vomiting frequency/volume pending clinical source | snomed_domain: symptom |
| `symptom_abdominal_pain` | Abdominal pain reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | location, severity pending clinical source | snomed_domain: symptom |
| `symptom_oral_intake_failure` | Patient unable or unwilling to maintain oral intake | normal / reduced / stopped / unknown | patient_reported | patient, medicine_manager | relates to sick-day rules | snomed_domain: finding |
| `finding_hydration_status` | Staff assessment of hydration | well_hydrated / dehydrated / overloaded / unknown | staff_transcribed | — | skin turgor, mucous membranes, sunken eyes | snomed_domain: finding |
| `finding_deep_rapid_breathing` | Kussmaul-type breathing observed | present / absent / unknown | staff_transcribed | — | respiratory rate context | snomed_domain: finding |
| `finding_altered_mental_status` | Any change in consciousness or orientation | present / absent / unknown | staff_transcribed | — | severity (lethargy, confusion, coma) pending clinical source | snomed_domain: finding |
| `finding_unable_to_swallow` | Swallowing impairment observed or reported | present / absent / unknown | staff_transcribed | — | severe-hypoglycaemia pathway | snomed_domain: finding |
| `finding_seizure` | Seizure activity observed or reported | present / absent / unknown | staff_transcribed | — | severe-hypoglycaemia and stroke pathways | snomed_domain: finding |
| `finding_third_party_assistance_required` | Episode required another person's help (severe hypoglycaemia defining feature) | present / absent / unknown | staff_transcribed | patient, medicine_manager | ADA severe-hypoglycaemia definition; source pin pending | snomed_domain: finding |
| `measure_glucose` | Blood glucose | numeric, mg/dL (canonical; mmol/L accepted, declared conversion factor 1 mmol/L = 18.016 mg/dL) | interfaced, staff_transcribed, device_memory | — | specimen (capillary/venous), timing (fasting/random/acute illness) | LOINC candidate: 2339-0 (medium confidence) |

### 4.2 Cardiovascular emergencies

| Identifier | Clinical definition | Permitted values / unit | entry_mode | informant | Context / method | Mapping |
|---|---|---|---|---|---|---|
| `symptom_chest_discomfort` | Chest discomfort reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | structured phenotype (quality, radiation, exertion relation) pending clinical source | snomed_domain: symptom |
| `symptom_dyspnoea` | Breathlessness reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | pattern field (see §4.3) | snomed_domain: symptom |
| `symptom_syncope` | Transient loss of consciousness reported | present / absent / unknown | patient_reported | patient, medicine_manager | prodrome, witnessed/unwitnessed pending clinical source | snomed_domain: symptom |
| `finding_altered_mental_status` | Shared with §4.1 | present / absent / unknown | staff_transcribed | — | — | snomed_domain: finding |
| `finding_focal_neurologic_deficit` | Focal neurological deficit on exam | coded deficit / absent / unknown | staff_transcribed | — | deficit type coded per clinical source | snomed_domain: finding |
| `finding_new_speech_or_vision_change` | New speech or vision disturbance | present / absent / unknown | staff_transcribed | — | stroke pathway | snomed_domain: finding |
| `finding_stroke_onset_time` | Time symptoms first noted, or last-seen-well | datetime, or `unknown_last_seen_well` | staff_transcribed | patient, medicine_manager | critical for thrombolysis window; never defaulted | snomed_domain: finding |
| `finding_retinal_acute_damage` | Acute retinal findings on exam (clinician-documented) | coded finding / absent / unknown | staff_transcribed | — | hypertensive emergency context | snomed_domain: finding |
| `clinician_documented_acute_target_organ_damage` | Clinician-documented acute hypertensive target-organ damage | present / absent / unknown | staff_transcribed | — | cardiac, renal, neurological, ocular; never inferred from BP alone | snomed_domain: finding |
| `finding_pulmonary_oedema` | Signs of pulmonary oedema on exam | suspected / absent / unknown | staff_transcribed | — | crackles, pink frothy sputum, respiratory distress | snomed_domain: finding |
| `symptom_tearing_pain` | Tearing or ripping chest/back pain reported | present / absent / unknown | patient_reported | patient, medicine_manager | aortic-emergency feature | snomed_domain: symptom |
| `finding_pulse_deficit` | Pulse deficit or BP differential between limbs | present / absent / unknown | staff_transcribed | — | laterality; aortic-emergency feature | snomed_domain: finding |

### 4.3 Heart-failure decompensation

| Identifier | Clinical definition | Permitted values / unit | entry_mode | informant | Context / method | Mapping |
|---|---|---|---|---|---|---|
| `symptom_dyspnoea` | Shared with §4.2; pattern is a context field | present / absent / unknown | patient_reported | patient, medicine_manager | pattern: exertional / rest / paroxysmal nocturnal / sudden | snomed_domain: symptom |
| `symptom_orthopnoea` | Breathlessness lying flat, relieved by elevation (where sourced) | present / absent / unknown | patient_reported | patient, medicine_manager | pillows required pending clinical source | snomed_domain: symptom |
| `finding_pedal_oedema` | Pedal oedema on exam | present / absent / unknown | staff_transcribed | — | laterality; severity scale pending clinical source | snomed_domain: finding |
| `measure_weight` | Body weight | numeric, kg | staff_transcribed, device_memory | — | weight change computed vs prior documented weight (derived, reversible) | LOINC candidate: 29463-7 (medium confidence) |
| `finding_perfusion_abnormal` | Abnormal peripheral perfusion on exam | present / absent / unknown | staff_transcribed | — | cool extremities, mottling, slow capillary refill | snomed_domain: finding |
| `clinician_documented_hf_status` | Clinician-documented heart-failure status | compensated / decompensated / unknown | staff_transcribed | — | clinician assessment, not inferred from signs alone | snomed_domain: finding |

### 4.4 Pharmacotherapy effects

| Identifier | Clinical definition | Permitted values / unit | entry_mode | informant | Context / method | Mapping |
|---|---|---|---|---|---|---|
| `finding_pedal_oedema` | Shared with §4.3 (RAAS/CCB effect) | present / absent / unknown | staff_transcribed | — | — | snomed_domain: finding |
| `symptom_gi_intolerance` | GI intolerance reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | nausea, vomiting, diarrhoea, dyspepsia | snomed_domain: symptom |
| `finding_injection_site_reaction` | Reaction at injection site | present / absent / unknown | staff_transcribed | patient, medicine_manager | redness, swelling, pain, induration | snomed_domain: finding |
| `finding_lipohypertrophy` | Lipohypertrophy on exam | present / absent / unknown | staff_transcribed | — | injection-site rotation assessment | snomed_domain: finding |
| `finding_lipoatrophy` | Lipoatrophy on exam | present / absent / unknown | staff_transcribed | — | injection-site rotation assessment | snomed_domain: finding |
| `finding_cool_pale_sweaty_skin` | Cool, pale, sweaty skin (hypoglycaemia or shock context) | present / absent / unknown | staff_transcribed | — | — | snomed_domain: finding |
| `symptom_tremor` | Tremor reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | hypoglycaemia and beta-agonist effect | snomed_domain: symptom |
| `symptom_palpitations` | Palpitations reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | hypoglycaemia and CV context | snomed_domain: symptom |
| `finding_bleeding` | Any bleeding on exam or reported | present / absent / unknown | staff_transcribed | patient, medicine_manager | site and severity; anticoagulant monitoring | snomed_domain: finding |
| `symptom_muscle_pain` | Myalgia reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | statin effect | snomed_domain: symptom |

### 4.5 Medication use (structured assessments, not a proprietary adherence score)

Every record below is a structured assessment with a bounded value set. None
computes a score. "Caregiver report" is the mandatory `informant:
medicine_manager` option on every record here; a record that does not say who
reported it is unusable.

| Identifier | Clinical definition | Permitted values / unit | entry_mode | informant | Context / method | Mapping |
|---|---|---|---|---|---|---|
| `medication_confusion` | Patient confused about which medicines to take or when | present / absent / unknown | patient_reported | patient, medicine_manager | pill-box context | snomed_domain: finding |
| `medication_missed_dose` | A dose was missed | missed / not_missed / unknown | patient_reported | patient, medicine_manager | names the medication (medication identity) and time window | snomed_domain: finding |
| `medication_duplicate_dose` | A dose was taken twice | present / absent / unknown | patient_reported | patient, medicine_manager | names the medication | snomed_domain: finding |
| `medication_refill_gap` | Refill overdue or supply exhausted | present / absent / unknown | staff_transcribed | patient, medicine_manager | names the medication | snomed_domain: finding |
| `medication_administration_assistance` | Assistance required to administer | none / partial / full / unknown | staff_transcribed | patient, medicine_manager | who assists (medicine-manager relationship) | snomed_domain: finding |
| `medication_discrepancy_state` | Reconciliation discrepancy between charted and actual medication use | consistent / discrepancy_present / unknown | staff_transcribed | — | staff-performed reconciliation finding | snomed_domain: finding |

### 4.6 Physical examination

| Identifier | Clinical definition | Permitted values / unit | entry_mode | informant | Context / method | Mapping |
|---|---|---|---|---|---|---|
| `finding_hydration_status` | Shared with §4.1 | well_hydrated / dehydrated / overloaded / unknown | staff_transcribed | — | — | snomed_domain: finding |
| `measure_bp_systolic` | Systolic blood pressure | numeric, mmHg | staff_transcribed, device_memory | — | setting: office / home / ambulatory — **never pooled**; posture, arm side, cuff size recorded | LOINC candidate: 8480-6 (medium confidence) |
| `measure_bp_diastolic` | Diastolic blood pressure | numeric, mmHg | staff_transcribed, device_memory | — | same context fields as systolic | LOINC candidate: 8462-4 (medium confidence) |
| `measure_heart_rate` | Heart rate | numeric, bpm | staff_transcribed, device_memory | — | palpation vs monitor | LOINC candidate: 8867-4 (medium confidence) |
| `finding_foot_ulcer` | Diabetic foot ulcer on exam | present / absent / unknown | staff_transcribed | — | depth, infection, ischaemia fields (see below) | snomed_domain: finding |
| `finding_wound_infection` | Clinical signs of wound infection | present / absent / unknown | staff_transcribed | — | redness, warmth, pus, odour | snomed_domain: finding |
| `finding_wound_ischaemia` | Clinical signs of wound ischaemia | present / absent / unknown | staff_transcribed | — | pale, cold, absent pulses | snomed_domain: finding |
| `finding_monofilament_sensation` | Monofilament sensation test result | normal / reduced / absent / unknown | staff_transcribed | — | laterality and site; 10 g monofilament | snomed_domain: finding |
| `symptom_neuropathy_symptoms` | Neuropathic symptoms reported by patient | present / absent / unknown | patient_reported | patient, medicine_manager | numbness, tingling, burning | snomed_domain: symptom |
| `finding_pedal_pulses` | Pedal pulse palpation | palpable / absent / unknown | staff_transcribed | — | laterality | snomed_domain: finding |

---

## 5. Measurement and laboratory observables (inputs named by candidate rules)

| Identifier | Clinical definition | Unit | entry_mode | Context / method | Mapping |
|---|---|---|---|---|---|
| `measure_glucose` | Blood glucose | mg/dL canonical; mmol/L accepted with declared conversion (1 mmol/L = 18.016 mg/dL) | interfaced, staff_transcribed, device_memory | specimen (capillary/venous); timing | LOINC candidate: 2339-0 (medium confidence) |
| `measure_hba1c_ngsp` | HbA1c, NGSP reporting | % | interfaced | assay method; context flag `a1c_interpretation_caution` (haemoglobinopathy, anaemia, transfusion, CKD, pregnancy) — Noor never "corrects" HbA1c (§5.3) | LOINC candidate: 4548-4 (medium confidence) |
| `measure_hba1c_ifcc` | HbA1c, IFCC reporting — **distinct observable from NGSP** | mmol/mol | interfaced | same context flags | LOINC candidate: 59261-8 (low confidence) |
| `measure_egfr_reported` | eGFR as reported by the laboratory, with `reported_equation` retained | mL/min/1.73 m² | interfaced | equation and version retained; historical values never silently recomputed (§5.2) | LOINC candidate: 33914-3 (medium confidence) |
| `measure_egfr_noor_derived` | Noor-derived eGFR, 2021 CKD-EPI creatinine without race — distinct observable | mL/min/1.73 m² | noor_derived | records its inputs (creatinine, age, sex) and equation; reversible | LOINC candidate: 33914-3 (medium confidence, derived) |
| `measure_crcl_cockcroft_gault` | Creatinine clearance by Cockcroft-Gault — **distinct from eGFR; never substituted** | mL/min | noor_derived | records weight, age, sex inputs | LOINC candidate: 33908-5 (low confidence) |
| `measure_creatinine` | Serum creatinine | unit per Saudi laboratory convention — confirm in charter (µmol/L or mg/dL); conversion declared and reversible | interfaced | specimen | LOINC candidate: 2160-0 (medium confidence) |
| `measure_potassium` | Serum potassium | mmol/L | interfaced | specimen | LOINC candidate: 6299-2 (medium confidence) |
| `measure_beta_hydroxybutyrate` | Blood beta-hydroxybutyrate | mmol/L | interfaced | specimen | LOINC candidate: 6873-4 (medium confidence) — molar concentration in serum/plasma; 29512-1 is the mass-concentration variant and must not be mixed with it |
| `measure_urine_ketones` | Urine ketones (semiquantitative) | categorical: trace / 1+ / 2+ / 3+ / unknown | interfaced, staff_transcribed | specimen | LOINC candidate: 2518-9 (low confidence) |
| `measure_venous_ph` | Venous pH (DKA criterion) | pH units | interfaced | specimen | LOINC candidate: 2744-1 (low confidence) |
| `measure_bicarbonate` | Bicarbonate | mmol/L | interfaced | specimen | LOINC candidate: 1963-8 (low confidence) |
| `measure_urine_acr` | Urine albumin-to-creatinine ratio | mg/g canonical; mg/mmol accepted with declared conversion | interfaced | specimen | LOINC candidate: 14585-1 (low confidence) |

---

## 6. Renal-risk medication-safety workflow — minimum pinned observable set (plan prioritization step 2)

Scope: the first renal-risk medication-safety workflow — metformin renal
contraindication/dosing, RAAS-inhibitor and MRA renal-and-potassium monitoring
(lisinopril, captopril, enalapril, losartan, spironolactone). Source pins live
in `label-pin-register.md`; this section pins the **minimum observable set** the
workflow's rules read, with the exact provenance rules each rule must declare.

Status: candidate set, same approval gate as every record in this file. A rule
in this workflow may read only these observables; anything else is a content
change with its own pin.

| Identifier | Role in workflow | Unit | entry_mode | Context / provenance rule | Mapping |
|---|---|---|---|---|---|
| `measure_egfr_reported` | Metformin GFR bands; RAAS/MRA eGFR check | mL/min/1.73 m² | interfaced | equation retained; historical values never silently recomputed (§5.2) | LOINC candidate: 33914-3 |
| `measure_egfr_noor_derived` | Same rules when no interfaced value; **a rule declares which eGFR observable it reads — never both interchangeably** | mL/min/1.73 m² | noor_derived | inputs (creatinine, age, sex) + 2021 CKD-EPI creatinine equation recorded; reversible | LOINC candidate: 33914-3 (derived) |
| `measure_creatinine` | Input to noor-derived eGFR; RAAS 30% creatinine-rise rule (PP 3.6.4) | unit per Saudi convention — pending charter (µmol/L or mg/dL) | interfaced | specimen; conversion declared and reversible | LOINC candidate: 2160-0 |
| `measure_potassium` | RASi/MRA hyperkalaemia monitoring; KDIGO threshold >5.5 mmol/L (register §5.1) | mmol/L | interfaced | specimen | LOINC candidate: 6299-2 |
| `measure_urine_acr` | KDIGO A1–A3 category (monitoring frequency by risk cell) | mg/g canonical; mg/mmol accepted, declared conversion factor 0.113 (1 mg/g = 0.113 mg/mmol; KDIGO pairs 30 mg/g = 3 mg/mmol, 300 mg/g = 30 mg/mmol) | interfaced | specimen; random urine; never 24-hour without flagging | LOINC candidate: 14585-1 |
| `measure_bp_systolic` | RASi initiation/escalation BP check (PP 3.6.2) | mmHg | staff_transcribed, device_memory | setting office/home/ambulatory — never pooled; posture, arm, cuff recorded | LOINC candidate: 8480-6 |
| `measure_bp_diastolic` | Same as systolic | mmHg | staff_transcribed, device_memory | same context fields | LOINC candidate: 8462-4 |
| `medication_*` (active-medication identity) | Metformin/RAAS/MRA exposure, dose, strength, last-change date — every rule names the medication identity it reads | structured medication-use records | staff_transcribed, patient_reported | mandatory `informant` (patient or medicine_manager); names the medication | snomed_domain: medication |

**Interval pin for this workflow** (rules declare `max_age_days` per evaluation;
freshness is never a registry field — §5.1): KDIGO 2024 risk-cell monitoring
frequencies (register §5.1) and the 2–4-week RASi post-initiation/escalation
check (PP 3.6.2) determine the workflow's monitoring obligations, not the
registry.

---

## 7. Open items before any record can be approved

- **Terminology charter** (SSOT §3.3) must exist: licence status, edition,
  effective time, module, owner, review cadence, and attribution obligations
  per code system. This is a software-implementation prerequisite.
- **SNOMED CT Saudi Affiliate licence** is outstanding; concept IDs and display
  strings stay out of all content until it is settled.
- **LOINC edition** to pin, and every candidate code verified against it.
  Confidence levels above are the drafter's estimate, not verification.
- **Units for creatinine** (and confirmation of glucose canonical unit) —
  Saudi laboratory convention to be recorded in the charter.
- **Bounded symptom/exam definitions** (e.g. severity scales for oedema,
  vomiting, chest-pain phenotype, dyspnoea pattern) need a clinical source from
  the selected guideline family (workstream 5) and a clinical owner.
- **Clinical content owner and terminology owner** — appointed 2026-08-17
  (Youssef Sabry; roadmap §3); records may now reach `clinician_approved`
  once their sources and credentials are in place.
- Signals beyond this set that prioritized rules require are added through the
  same record shape; this register is complete only for the six groups the
  remediation plan names.