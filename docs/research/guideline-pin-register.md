# Guideline Pin Register (workstream 5)

**Status:** Proposition-level pins for the guideline families the roadmap §7
tracks. Each proposition records organisation, document, version, locator,
jurisdiction, and boundary convention. Status: `pinned` (candidate) — named
clinical-owner approval with review date is still required before any
proposition feeds a rule. Every numeric boundary below keeps its
inclusive/exclusive convention written next to it; where the source does not
state one explicitly, the convention is flagged `convention_unstated`.

Conflicting families are never averaged: ACC/AHA 2025 and ESC 2024 remain
profile-selectable only after independent pins; ESH 2023 requires an explicit
SSOT decision; ADA and KDIGO pins are for their declared domains.

## 1. Hypertension — NHC/SHA 2023 (SSOT interim default)

**Source record (applies to every proposition in this section):**
- Organisation: National Heart Center (NHC) and Saudi Heart Association (SHA), Kingdom of Saudi Arabia
- Document: "National Heart Center/Saudi Heart Association 2023 Guidelines on the Management of Hypertension"
- Version: 2023 (published 2023-03; J Saudi Heart Assoc 35(1): Article 3)
- Locators: journal `https://doi.org/10.37616/2212-5043.1328`; full text PMC `https://pmc.ncbi.nlm.nih.gov/articles/PMC10069676/`; publisher PDF `https://saudi-heart.com/wp-content/uploads/2023/12/NHC_SHA-2023-Guidelines-on-the-management-of-Hypertension..pdf`
- Jurisdiction: Saudi Arabia; population: Saudi adults; evidence classes: Recommended / Should be considered / May be considered / Not recommended

| Proposition | Locator | Boundary convention |
|---|---|---|
| BP 120/80 mmHg is normal; **BP >130/80 mmHg = hypertension** | §3.1 Definition and classification | >130/80 (exceeds) — hypertension threshold is >, not ≥ (verify exact wording in document) |
| Diagnosis depends on measurement method: office, ABPM, or home BP measurement; measure per §3.2.1 | §3.1, §3.2.1 | setting-specific — no pooling |
| Screen all adults >18; BP at least at each healthcare-facility visit; annual screening for >40 years or with risk factors; 3–5 years otherwise | §3.3, Table 4 | >18, >40 (verify exact wording) |
| First-line pharmacological agents: thiazide/thiazide-like diuretics, ACEi, ARB, long-acting dihydropyridine CCB; beta-blockers first-line only for specific indications (e.g. younger people with sympathetic overdrive; compelling indications in Table 10) | §3.6.2, Table 10 | — |
| Treatment priority is BP control regardless of drug class; single-pill combinations favoured | §3.6.2 | — |
| Resistant hypertension: seated office BP >140/90 mmHg on ≥3 antihypertensives at optimal/maximally tolerated doses including a diuretic; exclude secondary/pseudo-resistant causes; confirm with ABPM or HBPM; spironolactone considered | §3.7.1 | >140/90, ≥3 (verify exact wording) |
| Heart failure with hypertension: start treatment at BP >140/90, target SBP <130 but preferably not lower than 120 mmHg | §3.7.5, Table 15 | >140/90 start; <130 target; ≥120 floor |
| Pregnancy: treat at SBP ≥150 or DBP ≥95; lower threshold (140/90) with gestational hypertension with organ damage or pre-existing HTN with subclinical/symptomatic organ damage; ACEi/ARB/DRI not recommended in pregnancy | §3.7.8 | ≥150/95; ≥140/90 with organ damage (verify exact wording) |
| Hypertensive emergencies and the severe-elevation terminology used by Noor's hypertensive-emergency red-flag library come from this family | §3.7 (emergency subsections) | in-document subsection number pending verification |

Mismatch note (plan workstream 5): `hypertension-research.md` §2.1/§2.8 currently
drafts ESC 2024/ESH 2023 classification. Resolution: re-base classification,
measurement-context, targets, and first-line content on NHC/SHA 2023 above
unless the project owner explicitly approves an SSOT amendment. ACC/AHA 2025 and
ESC 2024 stay `NS`/candidate for profile-selectable use.

## 2. Diabetes — ADA Standards of Care in Diabetes 2026

**Source record:**
- Organisation: American Diabetes Association (Professional Practice Committee)
- Document: *Standards of Care in Diabetes—2026*, Diabetes Care 2026;49(Suppl 1)
- Jurisdiction: international; population: all people with/prediabetes; evidence grading A–E

### 2.1 Hypoglycaemia levels (§6; DOI 10.2337/dc26-S006; pages S132–S149)

| Proposition | Locator | Boundary convention |
|---|---|---|
| Level 1: glucose <70 mg/dL (<3.9 mmol/L) and ≥54 mg/dL (≥3.0 mmol/L) — alert/treatment-support signal | §6, Table "Glycemic criteria/description" | <70 and ≥54 (half-open interval) |
| Level 2: glucose <54 mg/dL (<3.0 mmol/L) — clinically significant; urgent review | §6 | <54 |
| Level 3: severe event with altered mental and/or physical status requiring assistance for treatment, irrespective of glucose level | §6 | no numeric gate — symptom-defined |
| CGM time-below goals: <70 mg/dL for <4% of time (<1% for older adults); <54 mg/dL for <1% (6.3c) | §6.3c | <4% / <1% / <1% |
| Conscious individual with glucose <70: glucose is preferred treatment (15–20 g); repeat at 15 minutes if hypoglycaemia persists (6.15) | §6.15 | <70 |

### 2.2 Diabetes screening (§2; DOI 10.2337/dc26-S002)

- Screen asymptomatic adults who are overweight/obese (BMI ≥25, or ≥23 Asian-American) with one or more risk factors, including age over 35, family history, hypertension (BP ≥130/80 or treated), HDL <35 mg/dL and/or triglycerides >250 mg/dL, PCOS, physical inactivity, high-risk medications, HIV, pancreatitis history. (Recorded against the 2025 edition text; confirm the 2026 §2 wording in-document at verification.)

### 2.3 Retinopathy, neuropathy, foot (§12; DOI 10.2337/dc26-S012; pages S261–S282)

| Proposition | Locator | Boundary convention |
|---|---|---|
| T1D: initial dilated and comprehensive eye exam 5 years after diabetes onset | 12.3 | at 5 years |
| T2D: initial dilated and comprehensive eye exam at diagnosis | 12.4 | at diagnosis |
| No retinopathy on ≥1 annual exam + glycaemic indicators in range: every 1–2 years may be considered; any retinopathy present: at least annually; progressing or sight-threatening: more frequently (ophthalmologist) | 12.5 | 1–2 years; ≥1 year |
| Diabetic peripheral neuropathy assessment: start at T2D diagnosis / 5 years after T1D diagnosis, at least annually thereafter | 12.17 | annual |
| DSPN assessment: history + temperature or pinprick (small fibre) and 128-Hz tuning fork (large fibre); annual 10-g monofilament for at-risk feet | 12.18 | annual monofilament |
| Comprehensive foot evaluation at least annually to identify ulcer/amputation risk factors | 12.23 | annual |
| Foot exam components: skin inspection, deformities, neurological (10-g monofilament or Ipswich touch test + one additional: pinprick/temperature/vibration), vascular (leg and foot pulses) | 12.24 | — |

## 3. DKA/HHS — Umpierrez et al. 2024 consensus

**Source record:** Umpierrez GE, et al. *Hyperglycemic Crises in Adults With Diabetes: A Consensus Report.* Diabetes Care 2024;47(8):1257–1275. DOI 10.2337/dci24-0032.
- Already recorded at proposition level in `diabetes-research.md` §2.1–§2.3 with Figure 2A/2B and the "Diagnostic Criteria for DKA/HHS" section locators; locators complete.
- DKA boundaries: glucose ≥200 mg/dL or known diabetes; BHB ≥3.0 mmol/L or urine ketones ≥2+; pH <7.30 and/or bicarbonate <18 mmol/L.
- HHS boundaries: glucose ≥600 mg/dL; effective osmolality >300 mOsm/kg or total >320; BHB <3.0 mmol/L; pH ≥7.30 and bicarbonate ≥15 mmol/L.

## 4. ACS recognition — ESC 2023

**Source record:**
- Organisation: European Society of Cardiology
- Document: *2023 ESC Guidelines for the management of acute coronary syndromes* (Byrne RA, et al.)
- Version: 2023-08-25; European Heart Journal 2023;44(38):3720–3826
- Locator: `https://doi.org/10.1093/eurheartj/ehad191`
- Jurisdiction: Europe; population: adults with suspected ACS

| Proposition | Locator | Boundary convention |
|---|---|---|
| >80% of men and women with ACS present with chest pain or pressure; other common symptoms: diaphoresis, shoulder/arm pain, indigestion/epigastric pain; women more often: dizziness/syncope, nausea/vomiting, jaw/neck pain, dyspnoea, interscapular pain, palpitations, fatigue — sex-specific chest-pain features not supported for early MI diagnosis | §3.1.1 | — |
| Chest pain classified cardiac / possible cardiac / non-cardiac | §3.1.1 | — |
| Nitroglycerin relief is not specific for ACS; not recommended as a diagnostic manoeuvre in working STEMI | §3.1.1 | — |
| Differential diagnoses for acute chest pain: aortic dissection, pulmonary embolism, tension pneumothorax, Takotsubo, myopericarditis, aortic stenosis, musculoskeletal, GI | §3.5, Table S5 | — |
| Noor's ACS library must not invent numeric troponin cutoffs, ECG interpretation, or time windows (per `hypertension-research.md` §3) — those stay provider-approved pathway content | §3 of research file | — |

## 5. Stroke recognition — AHA/ASA

**Source records (two, complementary):**
1. American Stroke Association public warning signs — F.A.S.T. (Face drooping, Arm weakness, Speech difficulty, Time to call emergency number); other signs: sudden numbness/weakness one side, confusion, trouble speaking/understanding, severe headache with no known cause, sudden vision changes, sudden trouble walking/dizziness/loss of balance. Locator: `https://www.stroke.org/en/about-stroke/stroke-symptoms` (version: current public page; capture date 2026-08-17).
2. 2026 AHA/ASA Guideline for the Early Management of Patients With Acute Ischemic Stroke. Stroke, DOI 10.1161/STR.0000000000000513. Prehospital stroke scales (CPSS, LAPSS, RACE, FAST) remain nondiagnostic; symptom-onset / last-seen-well time is critical for reperfusion eligibility.

Noor constraints already recorded in `hypertension-research.md` §3: headache or high BP alone never labels stroke; glucose check must not become a gate that delays stroke activation (hypoglycaemia can mimic stroke); Noor may store the result of a provider-approved stroke screen with its version.

## 6. Monitoring and screening proposition pins (workstream 8)

Maps the roadmap §6 domains to their pinned proposition sources. Each interval
is `monitors`-class (due date), never `max_age_days` (result freshness) — the
distinction stays per SSOT §5.1 and the research files' §5/§4.

| Domain | Pinned proposition | Source record | Status |
|---|---|---|---|
| Renal + K+ follow-up after RAASi/MRA initiation or dose change | BP, creatinine, potassium within **2–4 weeks** of initiation/escalation; continue unless creatinine rises **>30% within 4 weeks**; hyperkalaemia threshold **>5.5 mmol/L** | KDIGO 2024 PP 3.6.2/3.6.4, Ch. 4 (`label-pin-register.md` §6.1) | pinned (candidate) |
| Renal monitoring for metformin | Assess GFR before initiation and **at least annually** thereafter; contraindication GFR <30 | EMA/603690/2016 Article-31 referral, EC decision 2016-12-12 | pinned (candidate, supplementary — not a label) |
| Retinal screening and referral | T1D initial dilated exam at 5 years; T2D at diagnosis; ≥annual if retinopathy; 1–2 years after normal exams | ADA SOC 2026 §12.3–12.5 (DOI 10.2337/dc26-S012) | pinned (candidate) |
| Foot and neuropathy examination | Neuropathy assessment at T2D diagnosis / 5 years T1D, then ≥annual (12.17); annual 10-g monofilament + 128-Hz tuning fork (12.18); comprehensive foot evaluation ≥annual (12.23–12.24) | ADA SOC 2026 §12.17–12.24 | pinned (candidate) |
| Glycaemic / HbA1c monitoring | Assess glycemic status **at least 2×/year**; every ~3 months for those not meeting goals, recent treatment changes, frequent/severe hypo/hyperglycaemia, or health-status changes (6.2) | ADA SOC 2026 §6.2 (DOI 10.2337/dc26-S006) | pinned (candidate) |
| Lipid monitoring (reminder only — no ASCVD model) | Lipid profile at diabetes diagnosis, 4–12 weeks after initiation/dose change, and annually; LDL goals <70 mg/dL primary (40–75 y), <55 mg/dL secondary — threshold content stays provider-approved, rule is a reminder only | ADA SOC 2026 §10 (DOI 10.2337/dc26-S010; wording verified via official ADA professional handout 2026-04; in-document §10 verification pending) | pinned (candidate) |
| Orthostatic and BP measurement follow-up | Setting-specific measurement (§3.2.1); screening cadence §3.3/Table 4; BP targets per NHC/SHA (this register §1) | NHC/SHA 2023 §3.2.1, §3.3, §3.6.2 | pinned (candidate) |
| KDIGO albuminuria confirmation and CKD chronicity | CKD = abnormality present >3 months; A1–A3 categories; risk-cell monitoring frequencies (low annual → very high ≥4×/year) | KDIGO 2024 Ch. 1 Table 2, Ch. 3 | pinned (candidate) |
| SGLT2i/GLP-1 cardiorenal propositions | HbA1c-independent; where the selected guideline and label scope support it — deferred to `diabetes-research.md` §14.3; no pin until the first profile selects the family | — | IR |

## 7. Open items

- Named clinical-owner approval + review date for every proposition above.
- In-document verification of the flagged boundary conventions and the NHC/SHA §3.7 emergency subsection number.
- Saudi-first fallback records where a domain profile requires Saudi guidance (plan workstream 5): Saudi diabetes / CV-prevention / home-healthcare guidance — record the fallback family when the first provider profile is defined.
- Current Saudi diabetic-retinopathy screening guidance: ADA 12.x pinned as the family until a Saudi reference is selected for the domain profile.
- Foot/wound classification (Wagner, UT) remains a research note (`diabetes-research.md` §3.4, §17) — needs an approved classification-family pin before foot rules; IWGDF not yet pinned.
- The ACC/AHA 2025 severe-asymptomatic-hypertension (>180/120) terminology in `archive/clinical-guidelines-and-thresholds.md` is archived context, not the active family; NHC/SHA §3.7 governs until a profile selects ACC/AHA 2025 independently.