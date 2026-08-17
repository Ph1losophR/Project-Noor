> Section 6 of the research programme. Indexed in SSOT §17.

# 6. Risk models and scores (only those we might actually compute)

## Decision summary

Noor should begin with **three computable, clinician-reviewed instruments**: the **four-variable Kidney Failure Risk Equation (KFRE)**, **FIB-4** as a *fibrosis triage* calculation, and **IWGDF diabetic-foot risk category**. These have low input burden, a clear clinical action pathway, and no dependency on an opaque model runtime. A hypoglycaemia score is useful as a **review-prioritisation flag**, but its imported absolute probability should not be presented as Saudi-calibrated; it needs local external validation before being used as a risk category. Cardiovascular risk should use the Saudi-adopted framework already resolved in the clinical-guidelines workstream, with its “not Saudi-calibrated” status retained. Noor should **not** compute a visit-to-visit BP-variability score or make an individual BP “trend” claim from 3–6 irregular clinic readings in the MVP. [^1]

The design principle is simple: a score may trigger **review, measurement, referral consideration, or a structured prevention plan**. It must never autonomously diagnose, prescribe, de-escalate, or deny referral. Every run needs the model version, source, input snapshot with unit/provenance/freshness, eligibility/exclusion result, output, explanation, clinician action, and override reason. [^2][^3]

## The score contract: common requirements before any calculation

A calculation is only valid when its inputs are clinically and technically valid. Noor should build a shared `RiskAssessmentRun` record rather than let each module invent its own audit trail:

- **Identity:** `model_id`, `model_version`, publisher/source, implementation version, release/approval date, and local configuration version.
- **Purpose and target:** the predicted outcome, time horizon, intended population, and whether the output is a probability, category, triage flag, or descriptive statistic.
- **Inputs:** source resource/version, code, raw value, unit, method/equation where relevant, final/corrected status, effective time, received time, and mapping confidence.
- **Eligibility gate:** satisfied / failed / indeterminate; with discrete reasons such as `age_outside_validated_range`, `acute_illness`, `missing_ACR`, `stale_result`, `unverified_medication`, or `current_foot_ulcer`.
- **Output and uncertainty:** numeric output where the instrument is validated to provide one; otherwise a named category. Store `local_calibration_status` separately from the result.
- **Action layer:** a bounded clinician-review task, not an automatic order. Record acknowledge / accept / defer / override, the responsible clinician, reason, and follow-up due date. [^2][^3]

This is necessary because a risk score is not a diagnosis and because model transportability cannot be inferred from a high discrimination statistic alone. [^2][^4] KFRE, for example, can distinguish people who will progress well yet still over- or under-predict absolute risk in a different setting. In UK primary care it overpredicted in lower-risk groups before recalibration; in a later 59-cohort analysis it showed subgroup calibration problems at eGFR 45–59 and among older adults on the 5-year horizon. [^2][^4]

## 1. Kidney Failure Risk Equation (KFRE)

### What Noor would calculate

**Recommendation: implement the published four-variable KFRE as the first probabilistic score, with a hard eligibility/data-quality gate and an explicit `not_locally_calibrated` label.** It estimates the probability of treated kidney failure—dialysis or transplantation—over **2 and 5 years** for people with CKD. The four inputs are age, recorded sex, eGFR, and urine ACR; the original intended population is CKD stage 3a–5 / eGFR below 60 mL/min/1.73 m². [^2][^5]

Noor should calculate the published **four-variable equation**, not invent a “Noor KFRE+” that adds diabetes, hypertension, eGFR slope, medication list, or an LLM summary. A 59-cohort evaluation found that adding prior eGFR slope or cardiovascular comorbidity did not meaningfully improve performance in most settings; it found the original model generally accurate with CKD-EPI 2021 eGFR at eGFR below 45. [^4]

### Inputs and data gates

| Field | Noor requirement | Reason / handling |
|---|---|---|
| Age, recorded sex | Date-stamped demographics; no inferred sex category | Required equation inputs. If the source semantics do not match the published model input, do not calculate. [^2] |
| eGFR | Final quantitative result, unit mL/min/1.73 m², equation retained, effective date recorded; default to the laboratory result rather than silently recomputing historical values | The current evidence tested KFRE with CKD-EPI 2021 eGFR, but performance is not uniform across all eGFR/age strata. [^4] |
| Urine ACR | Final quantitative ACR, unit explicitly converted/verified; no inferred ACR from dipstick protein | ACR is a required four-variable input. Missing ACR should produce “cannot calculate—obtain/reconcile ACR,” not an imputed score. [^2] |
| CKD confirmation | At least two eGFR values below 60 more than 90 days apart, or a clinician-confirmed CKD state | The primary-care external validation used this chronicity definition; applying a chronic-progression score during a transient AKI episode would change the target population. [^2] |
| Acute state | `defer / clinician review` during AKI, rapidly changing renal function, dialysis, transplant evaluation, or incomplete renal data | The score predicts treated kidney failure in its validated CKD population; it is not an acute-kidney-injury triage score. [^2][^5] |

### How Noor should present the result

Display: **“Published KFRE estimate: X% 2-year; Y% 5-year risk of treated kidney failure. Source model has not been locally recalibrated for Saudi home-care patients.”** Alongside it, show date/equation of eGFR, date/unit of ACR, chronicity evidence, and any reason the result may be unreliable. [^2][^4]

A score should create a **nephrology-review consideration**, not a referral order. KDIGO 2024 states that a 5-year kidney-failure risk of **3%–5%** can help determine the need for nephrology referral alongside eGFR, ACR, and other clinical considerations. [^6] The UK calculator’s linked NICE pathway uses a different **>5%** referral consideration plus other renal criteria, illustrating why Noor must not hard-code a foreign operational threshold as if it were universally transferable. [^5]

For the Saudi release, use a configurable threshold owned by the Saudi clinical governance group. Until Saudi or Gulf calibration/impact evidence is obtained, the output is a **decision-support input**, not a calibrated individual prognosis. The most relevant external evidence supports this restraint: in 35,539 UK primary-care patients, discrimination was high but the unmodified model overpredicted lower-risk patients, and the authors called for further validation of referral criteria before clinical implementation. [^2]

### Validation and licensing posture

KFRE has unusually broad external-validation evidence, including the 59-cohort/312,424-patient evaluation, but neither that evidence nor the public UK site establishes Saudi calibration. [^4][^5] Noor should commission a local retrospective validation before it is used to drive any population-management threshold: assess discrimination, calibration-in-the-large, calibration slope, observed versus predicted 2- and 5-year risk, missing-ACR selection bias, competing mortality, and clinical impact at proposed referral thresholds.

**Rights conclusion:** the public UK calculator identifies the underlying publications and notes that its web content applies only to UK individuals; it does not provide a commercial software licence in the retrieved material. [^5] Noor should not scrape, embed, copy the UI, reuse its graphics, or call the public calculator in production. Implement the peer-reviewed published equation independently, preserve citation/attribution, and obtain Saudi legal review of the intended commercial use, branding, and any source-code/content reuse. This is a rights-risk control, not a claim that the mathematical expression itself is licensed by that site.

**Build priority:** P0 for a clinician-reviewable calculator once ACR and eGFR provenance are reliable; P2 for local calibration and prospective impact evaluation.

## 2. Hypoglycaemia risk prediction in older adults

### Evidence landscape

There are credible outpatient models, but the evidence does **not** support importing a foreign absolute-risk probability into Noor as if it were Saudi-validated. The strongest operationally simple option located was the Karter et al. tool for adults with type 2 diabetes: it predicts 12-month hypoglycaemia-related ED/hospital use from six inputs—prior hypoglycaemia-related utilisation, insulin, sulfonylurea, prior-year ED use, CKD stage, and age. It was externally tested in a large US veterans cohort and another health-system cohort, with external discrimination around 0.79–0.81. [^7]

A separate six-variable model predicts a 6-month severe-hypoglycaemia event using age, diabetes type, HbA1c, eGFR, prior hypoglycaemia, and insulin use; it was externally validated across three US integrated-care cohorts with discrimination around 0.80–0.84. [^8] Larger models can perform well in their own populations—for example, a Korean 14-variable model included age, lifestyle, prior severe events, diabetes therapy, CKD, diabetes duration, glycaemia and comorbidity, with good internal validation—but that makes it less attractive for a sparse home-visit record and does not solve transportability. [^9]

### What Noor should do

**MVP decision: do not calculate and display a named model’s absolute percentage risk.** Instead implement a transparent **hypoglycaemia review-priority rule**, explicitly labelled as *not a prognostic score*. [^7][^8] Its trigger set should include:

- age / older-adult status;
- insulin and/or sulfonylurea exposure based on a reconciled current medication record;
- prior documented severe or clinically significant hypoglycaemia;
- reduced eGFR / CKD stage;
- recent ED/hospital utilisation where available;
- very low or unexpectedly low HbA1c only as a contextual signal, never as proof of overtreatment;
- food insecurity, missed meals, fasting intent, cognitive/functional limitation, and inability to self-manage as clinician-entered risk modifiers.

The first five factors map directly to the parsimonious externally validated models. [^7][^8] [^7][^8] The rule should prompt medication reconciliation, symptom/event review, hypoglycaemia education, nutrition/fasting assessment, and clinician review of target and regimen. It must not auto-reduce insulin or stop a secretagogue. [^7][^8]

**Phase-2 option:** reproduce the Karter six-input tree as `Hypoglycaemia Utilisation Risk — US model; local calibration unknown` only after (a) full medication reconciliation and reliable ED/event capture are available, (b) a Saudi retrospective external validation has been completed, and (c) clinical governance approves the action thresholds. Its original low/intermediate/high bands were <1%, 1%–5%, and >5% predicted 12-month utilisation, but those bands should remain disabled in Noor until local calibration supports their use. [^7]

### Older-adult safeguards

A severe-event/ED model will miss clinically meaningful symptomatic and CGM-detected hypoglycaemia, and a low modelled event probability must never override frailty, impaired awareness, Ramadan fasting intent, declining renal function, or a clinician’s concern. The model target must be displayed verbatim: **hypoglycaemia-related ED/hospital utilisation** is not the same as all hypoglycaemia. [^7] In Noor, risk output should therefore be separated from `documented_hypoglycaemia_history`, current glucose data, and medication-risk flags.

**Build priority:** P1 as a transparent review flag; P2/P3 as a locally validated numerical model.

## 3. FIB-4 and other MASLD/NAFLD fibrosis scores

### What FIB-4 is—and is not

**Recommendation: calculate FIB-4, not a “NAFLD score,” as Noor’s first liver-risk calculation.** FIB-4 is a low-cost, non-invasive *advanced-fibrosis triage* tool based on age, AST, ALT, and platelet count. The AASLD guidance identifies it as the most validated of common simple blood-based scores and recommends it as first-line assessment because it is simple and has little or no added cost. [^10] Its conventional formula is:

$$\mathrm{FIB\!\!\!-4}=\frac{\mathrm{age\ (years)}\times\mathrm{AST\ (U/L)}}{\mathrm{platelets\ (10^9/L)}\times\sqrt{\mathrm{ALT\ (U/L)}}}$$

Use a unit-checked implementation; do not accept platelets in an unlabelled unit or transcribe values from a narrative report. A public professional calculator also describes the score as based on age, AST, ALT and platelet count and publishes the formula, but Noor should retain the primary AASLD source and formula test vectors in its governed rule pack. [^11][^10]

FIB-4 **does not diagnose steatosis, MASH/NASH, cirrhosis, or alcohol-related liver disease**, and it does not replace ultrasound/elastography/specialist assessment. It categorises probability of advanced fibrosis. In biopsy-referenced data from 363 people with fatty liver disease, discrimination was materially poorer in people with diabetes than without diabetes, which is exactly Noor’s target population. [^12]

### Eligibility and data-quality gates

Calculate only when all four inputs are final, contemporaneous enough for a policy-defined window, and clinically interpretable. Noor should defer rather than score when there is acute hepatitis/acute systemic illness, haemolysis or sample problem, a platelet count likely distorted by an acute process, or a clearly discordant lab pattern requiring clinician review. A score generated from unrelated measurement dates should be labelled `input_time_mismatch`; an old platelet count should not be silently combined with a new transaminase result.

Start in adults **35 years and older** until the clinical owner approves a source-specific exception. A professional clinical calculator describes FIB-4 use for adults ≥35 and notes that accuracy is strongly age-dependent. [^11] The exact age policy, acute-illness exclusions, time window, and units must be configured and tested against the selected guideline version rather than left implicit in code. [^10][^13]

### Output and action pathway

Use a three-state clinical display: `low probability`, `indeterminate`, and `high probability of advanced fibrosis`, not “normal / disease.” AASLD describes the conventional bands as **<1.3**, **1.3–2.67**, and **>2.67**, and recommends FIB-4 as first-line triage; in the retrieved AASLD summary, a score ≥1.3 leads to secondary non-invasive testing, with a higher age-specific threshold of 2 for people older than 65, and >2.67 supports referral consideration. [^10][^13]

For Noor:

1. **Low probability:** surface metabolic-risk management and a scheduled reassessment task—not reassurance that excludes liver disease.
2. **Indeterminate:** create a clinician-review task for secondary testing/referral pathway (for example, elastography or ELF where locally available), not an automatic diagnosis.
3. **High probability:** create an expedited clinician-review/referral consideration, with the raw labs and competing explanations shown.
4. **Age >65:** apply the approved older-adult threshold configuration visibly; no hidden threshold switch.
5. **Type 2 diabetes:** ensure routine reassessment interval is an explicit policy field. The retrieved AASLD summary calls for repeat primary risk assessment every 1–2 years in people with type 2 diabetes or multiple metabolic risks. [^13]

### Why Noor should not lead with the NAFLD Fibrosis Score (NFS)

NFS is not needed for the MVP. It increases input burden and does not solve the central uncertainty. In a biopsy-proven NAFLD study, both FIB-4 and NFS were more useful for **excluding** advanced fibrosis than identifying it; FIB-4 >2.67 had very low sensitivity in that sample. [^14] A single FIB-4 pathway plus a secondary-test/referral hand-off is easier to explain, audit, and localise. Add NFS only if a Saudi hepatology partner specifies an independent clinical use case and supplies a versioned pathway.

**Build priority:** P1 as a triage calculation, conditional on reliable labs and a Saudi hepatology-approved secondary pathway; never as a diagnostic label.

## 4. IWGDF diabetic-foot-ulcer risk stratification

### What Noor should compute

**Recommendation: implement the IWGDF 2023 risk category.** This is not a probabilistic prediction equation. It is a clinically actionable four-level prevention classification for a person with diabetes **without a current foot ulcer**, based on loss of protective sensation (LOPS), peripheral artery disease (PAD), deformity, prior ulcer, lower-extremity amputation, and end-stage renal disease. [^3]

The current categorisation and examination frequency are:

| IWGDF category | Characteristics | Guidance-linked screening / examination frequency |
|---|---|---|
| 0 — very low | No LOPS and no PAD | Annually [^3] |
| 1 — low | LOPS **or** PAD | Every 6–12 months [^3] |
| 2 — moderate | LOPS + PAD; **or** LOPS + deformity; **or** PAD + deformity | Every 3–6 months [^3] |
| 3 — high | LOPS or PAD **and** prior ulcer, lower-extremity amputation, or end-stage renal disease | Every 1–3 months [^3] |

The guideline explicitly asks clinicians to screen IWGDF risk-0 patients annually for neuropathy and PAD, and the recommendation applies to people with diabetes at risk of ulceration rather than people already presenting with an ulcer. [^3]

### Eligibility and safety boundary

Run this classification only when `diabetes = confirmed` and `active_foot_ulcer = false`. A current ulcer, infection, ischaemia, suspected Charcot process, gangrene, systemic illness, or acute limb symptoms should bypass routine stratification to an urgent clinician pathway. Noor must never convert absence of a recorded monofilament or vascular exam into “no LOPS/PAD.” The correct result is `indeterminate—foot examination required`. [^3]

Minimum source fields should be separate and time-stamped:

- LOPS test method/result, examiner, site(s) and date;
- PAD signs/symptoms and vascular assessment status—not merely a problem-list code;
- deformity;
- prior ulcer date/site/outcome;
- prior amputation level/date;
- renal-replacement / end-stage-renal-disease status;
- active lesion, pre-ulcerative lesion, infection, ischaemia, footwear and self-care concerns. [^3]

The IWGDF prevention guidance identifies LOPS, PAD and foot deformity as central ulcer-risk factors and describes screening as the way to identify people at risk. [^3] [^3]

### Implementation and validation

Use the category to schedule foot review, prompt prevention counselling and bring a structured foot examination into the home-visit workflow. Do not portray category 3 as a numeric ulcer probability. In a 2,097-person primary-care cohort, the classification’s negative predictive value exceeded 99% and specificity exceeded 90%; that supports its value for identifying people at low risk in that setting, not a guarantee of safety in Noor’s population. [^15]

The same cohort concluded that very-low-risk status could be updated every two years rather than annually, but Noor should retain the IWGDF annual recommendation as the default until a Saudi governance group deliberately adopts a different interval. [^15][^3]

**Build priority:** P0/P1. It is directly aligned with home-visit assessment and produces an explainable prevention workflow without pretending to estimate an individual probability.

## 5. Ten-year cardiovascular risk

This item is **not a new model-selection exercise for this section**. It should inherit the decision in Project Noor’s clinical-guidelines workstream: use the Saudi-adopted cardiovascular-risk framework, retain model name/version/input date, and expose `model_not_Saudi_calibrated = true` until a locally externally validated/recalibrated model is available. Do not run multiple foreign calculators and choose the most favourable result; do not silently convert a foreign predicted percentage into a Saudi individual prognosis. [^2]

In this risk-model module, the deliverable is architectural: store the calculator as a named, versioned `RiskAssessment`, record its target/time horizon and all raw inputs, and keep the score separate from Saudi guideline risk-band modifiers such as established ASCVD, CKD, long-duration diabetes, familial hypercholesterolaemia, and target-organ damage. Noor should not release any statin-intensity automation until that upstream source table is clinically transcribed and dual verified. [^2]

**Build priority:** P1 after the Saudi guideline table and local-formulary layer are governed; not a standalone MVP calculator.

## 6. BP variability and the honest “trajectory” feature

### What the evidence supports

Clinic BP has substantial within-person variation. In a real-world cohort with more than 7.7 million readings, mean within-person systolic-BP SD was **10.6 mmHg** and the mean absolute difference between two visits was **11.6 mmHg**. In that dataset, even if a treatment’s true effect were a 10-mmHg systolic reduction, the next visit would show a reduction under 5 mmHg about **36.9%** of the time. [^16] This is a practical noise floor for Noor: a single new clinic reading, even a fairly different one, is weak evidence of a durable trajectory.

Long-term visit-to-visit variability (VVV) is not purely random, but it is only modestly reproducible in routine care. In treated older adults with 14 or more measurements, the first-seven versus second-seven systolic-variability estimate had an intraclass correlation of 0.28. [^17] A Malaysian primary-care cohort found that **six** readings gave reasonably reliable VVV relative to 20 readings, and the authors suggested six as a minimum for VVV estimation; that finding supports a practical lower bound, not a universal clinical threshold. [^18]

The European Society of Hypertension position paper is more cautious: it says that the minimum number of visits for VVV is unclear, calls for more evidence on minimum reliable requirements, and advises sensitivity analysis when only 3–4 visits are used. It also concludes that heterogeneous indices and populations prevent a definitive VVV risk-stratification threshold. [^1]

### Product decision

**Do not compute a VVV risk score, use a published VVV cut-off, or claim “unstable BP” from 3–6 irregular outpatient values.** The 12.9-mmHg cut-off reported in one small retrospective primary-care study is not a transferable clinical threshold; it was derived in a particular cohort and cannot serve as Noor’s universal alarm point. [^19]

Instead, Noor should implement three distinct capabilities:

1. **Measurement-quality gate:** classify each reading as usable / questionable / unusable based on setting, device validation, cuff/position/rest, repeated readings, arrhythmia context, and date/time. Do not mix home, office and ambulatory measurements in one series.
2. **Descriptive display for 1–5 comparable encounters:** show every reading, setting, measurement protocol, median/mean of same-setting repeat readings, and time gaps. Use language such as “values differ across visits; insufficient comparable data to establish a trajectory.”
3. **Clinician-reviewed trend summary for ≥6 comparable readings:** show a time-aware robust linear slope with 95% confidence interval, but label it **descriptive, not a validated risk estimate**. Only render “possible sustained rise/fall” when the confidence interval excludes zero, readings meet quality rules, no recent acute event/medication change obviously explains the shift, and the clinician confirms interpretation. Otherwise show `no confident directional trend`. [^16][^18]

This “≥6” policy is deliberately conservative. It is grounded in the empirical VVV reliability result, while recognising that six points are still insufficient to establish a validated individual CVD-risk metric. [^18][^1]

### Why CUSUM and Bayesian change-point methods are not the answer here

CUSUM and Bayesian change-point methods are valuable **research/quality-control** tools when the baseline process, sampling scheme, error distribution and alert operating characteristics have been prospectively specified. They do not repair a sparse, heterogeneous, outcome-driven series of office readings. Routine-care measurements are irregular and may be informative—patients may be measured more frequently when unwell. A systematic review explains that standard longitudinal methods can be biased when visit intensity relates to the outcome, and recommends first assessing visit frequency/gaps and predictors of visit times; population-level methods such as inverse-intensity weighting or joint models address a different research problem, not a bedside claim from four points. [^20]

Noor should therefore reserve CUSUM/change-point modelling for offline product research after it has a prospectively collected, protocolised BP dataset with an adjudicated clinical-change reference standard. It should not be a clinician-facing MVP feature. [^20]

### What to validate prospectively

Before Noor makes any trajectory claim, run a measurement study in the intended home-care workflow:

- repeat standardised BP measurements within a visit to estimate measurement error;
- compare home-visit readings with a reference home-BP/ambulatory protocol where feasible;
- predefine an observation schedule rather than learn from visits triggered by illness;
- test whether six-reading slope labels reproduce in a second time window;
- assess false-positive “rise/fall” alerts, clinician agreement, medication changes, symptoms, and subsequent confirmed BP control. [^16][^18]

The first release can show **measurement history and data completeness**, which is useful and honest. [^16][^1] It should not imply that an algorithm has detected clinically meaningful deterioration where the literature has not established that claim.

## Build order and release gates

| Priority | Build | Release gate |
|---|---|---|
| P0 | IWGDF category | Structured foot exam; no current ulcer; clinical owner validates action/escalation pathways; Arabic/home-visit workflow testing. |
| P0 | KFRE calculator | Final ACR/eGFR with units and chronicity; independent test vectors; local threshold configuration; Saudi calibration status displayed; no copied third-party calculator content. |
| P1 | FIB-4 triage | Stable, contemporaneous AST/ALT/platelets; age/unit handling; Saudi hepatology-approved secondary-test/referral route; deterministic test cases. |
| P1 | Hypoglycaemia review flag | Reconciled medication status, eGFR, event history and clinical action workflow; no absolute-probability claim. |
| P1 | CV-risk module integration | Source table dual verification, Saudi-adopted calculator configuration, versioned inputs/results, local-calibration disclosure. |
| Defer | BP VVV / trajectory classifier | Prospective measurement-validation study; protocolised data; predefined performance targets; clinician governance. [^1] |

## Final product posture

Noor’s advantage should be **careful computation**, not maximal computation. KFRE, FIB-4 and IWGDF turn readily auditable structured data into useful prompts because their target population, inputs and next actions can be stated plainly. Hypoglycaemia risk is best framed initially as transparent clinical review priority, and BP data as a measurement-history problem rather than an invented predictive model. A score that cannot state its population, calibration, inputs, uncertainty, and safe action is not decision support—it is a number with undeserved authority. [^2][^4]


[^1]: Blood pressure variability: methodological aspects, clinical relevance and practical indications for management - a European Society of Hypertension position paper ∗.

[^2]: Major et al., 2019. The Kidney Failure Risk Equation for prediction of end stage renal disease in UK primary care: An external validation and clinical impact projection cohort study. PLoS Medicine.

[^3]: Guidelines on the prevention of foot ulcers in persons with ...

[^4]: Grams et al., 2023. The Kidney Failure Risk Equation: Evaluation of Novel Input Variables including eGFR Estimated Using the CKD-EPI 2021 Equation in 59 Cohorts. Journal of the American Society of Nephrology.

[^5]: The Kidney Failure Risk Equation.

[^6]: KDIGO 2024 Clinical Practice Guideline for the Evaluation and ...

[^7]: Karter et al., 2017. Development and Validation of a Practical Tool to Identify Patients with Type 2 Diabetes at High Risk of Hypoglycemia-Related Utilization. JAMA Internal Medicine.

[^8]: Schroeder et al., 2017. Predicting the six-month risk of severe hypoglycemia among adults with diabetes: development and external validation of a prediction model. Journal of diabetes and its complications.

[^9]: Han et al., 2018. Development and validation of a risk prediction model for severe hypoglycemia in adult patients with type 2 diabetes: a nationwide population-based cohort study. Clinical Epidemiology.

[^10]: AASLD Practice Guidance on the clinical assessment and management of nonalcoholic fatty liver disease.

[^11]: FIB-4 Calculator - Liver Foundation.

[^12]: Kim et al., 2022. Noninvasive Fibrosis Screening in Fatty Liver Disease Among Vulnerable Populations: Impact of Diabetes and Obesity on FIB-4 Score Accuracy. Diabetes Care.

[^13]: AASLD 2023 Practice Guidelines on the Clinical Assessment and Management of Nonalcoholic Fatty Liver Disease.

[^14]: Alkayyali et al., 2020. Clinical utility of noninvasive scores in assessing advanced hepatic fibrosis in patients with type 2 diabetes mellitus: a study in biopsy-proven non-alcoholic fatty liver disease. Acta Diabetologica.

[^15]: Monteiro-Soares et al., 2024. The Utility of Annual Reassessment of the International Working Group on the Diabetic Foot Diabetes-Related Foot Ulcer Risk Classification in the Primary Care Setting—A Cohort Study. Diabetology.

[^16]: Lu et al., 2021. The Challenges of Episodic Office-based Blood Pressure Measurement for the Management of Hypertension. medRxiv.

[^17]: Muntner et al., 2011. Reproducibility of visit-to-visit variability of blood pressure measured as part of routine clinical care. Journal of Hypertension.

[^18]: Lim et al., 2019. Number of blood pressure measurements needed to estimate long-term visit-to-visit systolic blood pressure variability for predicting cardiovascular risk: a 10-year retrospective cohort study in a primary care clinic in Malaysia. BMJ Open.

[^19]: Ching et al., 2016. OS 04-05 LONG TERM VISIT-TO-VISIT VARIABILITY OF SYSTOLIC BLOOD PRESSURE AND CARDIOVASCULAR DISEASE EVENTS IN A PRIMARY CARE SETTING: A 10-YEAR RETROSPECTIVE COHORT STUDY. Journal of Hypertension.

[^20]: Longitudinal studies that use data collected as part of usual care risk reporting biased results: a systematic review, 2017.