> Section 1 of the research programme. Indexed in SSOT §17.

# 1. Clinical guidelines — the content source of truth

## Decision standard

This report treats clinical guidelines as a **versioned evidence layer**, not executable medical advice. A rule should carry: source organization, document/version/date, section/table/recommendation locator, evidence grade where supplied, jurisdiction, review date, and a clinician-override/escalation path. Where sources conflict, the engine should show the conflict rather than silently merge thresholds.

The principal Saudi-facing stack should be **Saudi national guidance where it exists**, then current international source guidance, then product labels for agent-specific dosing. The search found recent Saudi hypertension (2023), dyslipidemia (2022), diabetic kidney disease (2025), and cardiovascular-prevention (2025, published January 2026) documents; the latter was explicitly developed for Saudi epidemiology and health-system needs. [^1][^2][^3]

## 1.1 Diabetes (P0)

### Primary source set and version control

**Use ADA *Standards of Care in Diabetes—2026* as the current core source.** ADA updates the Standards annually; the 2026 chapter records are dated January 1, 2026. [^4][^5] The rule-library index should, at minimum, map:

- **Section 6** — glycemic goals, hypoglycemia, and crises;
- **Section 9** — pharmacologic approaches;
- **Section 11** — chronic kidney disease and risk management;
- **Section 12** — retinopathy, neuropathy, and foot care;
- **Section 13** — older adults.

This is a practical index, not a replacement for section-level ingestion. [^4][^5][^6][^7] ADA’s 2026 older-adult chapter is publicly readable but expressly limits use to educational, noncommercial use when unaltered; it says ADA permission is required for third-party posting and for reproduction, distribution, adaptation, or comparable use. [^7] **Commercial-product conclusion:** citing a guideline and independently implementing clinical propositions after clinical/legal review is materially different from reproducing its protected expression. Do **not** copy tables, figures, decision trees, or substantial text into the product. The retrieved licence language does not grant commercial reuse; obtain written permission for any content reuse and obtain Saudi legal advice before launch.

**ADA/EASD consensus.** The published consensus currently in the corpus is the 2022 management-of-hyperglycaemia report. ADA/EASD announced a 2026 update, but at the time indexed it was in public-comment/finalization rather than a final report. Treat the 2022 report as the current final consensus reference and set an urgent review trigger on release of the final 2026 version. [^8][^9]

### Glycemia, hypoglycemia, and individualized targets

The engine should not use a single HbA1c goal. For older adults, ADA 2026 gives an implementation-grade framework:

- **Healthy** (few stable comorbidities and intact cognition/function): HbA1c **<7.0–7.5%** is reasonable.
- **Complex/intermediate** health (multiple chronic illnesses, ≥2 ADL impairments, or mild–moderate cognitive impairment): usually **<8.0%**, explicitly weighing comorbidity severity, function, frailty, medication benefit/harm, and preferences.
- **Very complex/poor health** (long-term care, end-stage illness, moderate–severe cognitive impairment, or ≥2 ADL impairments): avoid reliance on HbA1c; aim to prevent hypoglycemia and symptomatic hyperglycemia. [^7]

The trigger for deintensification is **not an age cutoff**. It is recurrent/severe hypoglycemia, impaired awareness, difficulty self-administering treatment, frailty/cognitive or functional decline, reduced life expectancy, or treatment burden. ADA specifically identifies sulfonylureas, meglitinides, and insulin as hypoglycemia-relevant in older adults and notes that intensive complex regimens targeting HbA1c below 6% increased severe hypoglycemia in ACCORD and VADT. [^7]

**Implementation recommendation:** encode risk flags and a clinician-review prompt, rather than automatic deprescribing: `hypoglycemia_event`, `impaired_awareness`, `insulin_or_secretagogue`, `eGFR_decline`, `frailty`, `ADL_dependence`, `cognitive_impairment`, `limited_life_expectancy`, `food_insecurity/irregular_intake`, and `support_available`. Require a documented reason if a high-hypoglycemia regimen persists in a person flagged complex/very complex. [^7]

### Metformin, SGLT2 inhibitors, and GLP-1 receptor agonists

The ADA–KDIGO consensus gives a sourceable renal framework:

- **Metformin:** use in T2D with CKD when eGFR is **≥30 mL/min/1.73 m²**; reduce to **1,000 mg/day at eGFR 30–44** and consider a reduction at **45–59** if there is additional lactic-acidosis risk. Monitor eGFR at least annually, increasing to every 3–6 months once eGFR is below 60; use a sick-day hold protocol during acute illness/AKI risk. [^10]
- **SGLT2 inhibitor:** for T2D with CKD, use an agent with proven kidney or cardiovascular benefit from **eGFR ≥20**; once started, it may continue below that threshold if tolerated. The KDIGO update frames SGLT2 inhibitors as CKD therapy, not merely glucose-lowering therapy. [^10][^11]
- **GLP-1 RA:** choose an agent with proven cardiovascular benefit when individualized glycemic targets remain unmet despite metformin and/or SGLT2i, or when those drugs cannot be used. [^10]

These are **class-level guideline thresholds, not a substitute for product labels**. Exact initiation, escalation, and renal-dose rules can differ by molecule and indication. For a Saudi deployment, maintain an SFDA-labelled-product configuration table by active ingredient and formulation; do not infer a molecule-level floor solely from the class rule. [^10][^11]

### HbA1c reliability and Saudi relevance

Do not treat HbA1c as an unquestioned ground truth. ADA 2026 notes inaccurate values after transfusion and in conditions that alter red-cell turnover, and suggests adjunctive glycated-protein testing where appropriate. [^7] Add an `a1c_interpretation_caution` flag for hemoglobin variants, hemolysis/altered erythrocyte survival, anemia, recent blood loss/transfusion, advanced CKD, and pregnancy; prompt review of assay method and use of CGM/SMBG or fructosamine/glycated albumin as clinically appropriate.

This is especially material in Saudi Arabia: national premarital-screening data found major regional variation, with sickle-cell-positive status in 45.1 per 1,000 and beta-thalassemia-positive status in 18.5 per 1,000 screened people. [^12] A Saudi laboratory study found that one immunoassay gave falsely high HbA1c values in beta-thalassemia minor, while sickle trait did not affect that particular assay—an assay-specific result, not a universal rule. [^13] Collect variant/thalassemia history and laboratory assay metadata where possible; never algorithmically “correct” HbA1c without laboratory validation.

## 1.2 Hypertension (P0)

### Source choice and conflicts

The current US source is the **2025 AHA/ACC multi-society hypertension guideline**. The European source is **ESC 2024** (European Heart Journal, October 2024), which replaced the earlier ESC/ESH framework. [^14][^15] ISH’s resource-variable global guideline is **2020**; it remains useful as an implementation reference but is not the most current of the three. Saudi-specific guidance is the **National Heart Center/Saudi Heart Association 2023 hypertension guideline**, developed by a Saudi expert panel for local population, practice and health-system context. [^1]

**Recommendation for Noor:** make the target source configurable. Default to the Saudi NHC/SHA guideline, with an explicit source-switch when the supervising service adopts ACC/AHA or ESC. Do not blend target systems. [^1][^14][^15]

The decisive difference is target intensity: ESC 2024 proposes treated systolic BP **120–129 mmHg when tolerated** in most adults, with relaxed targets for symptomatic orthostasis, age ≥85, moderate–severe frailty, or predicted survival below three years; ACC/AHA uses <130/80 mmHg broadly but also makes treatment initiation risk-based. [^16][^14]

### Valid BP data model

A valid record needs `setting` (office/home/ambulatory), device validation, cuff size, posture, arm, rest duration, reading sequence, average, date/time, and whether an observer was present. Saudi guidance specifies a quiet seated rest of at least **5 minutes**, back and arm supported, feet on the floor, a calibrated device, and extra readings if values differ by >10 mmHg; home monitoring should be two to three readings twice daily. [^1] ACC/AHA likewise states that a single reading is inadequate and office BP should be an average of at least two readings on at least two occasions. [^14]

The checklist’s “discard first reading” should **not** be hard-coded as universal guideline logic: use the specific local validated-device protocol and retain every reading plus calculation rule. Home/ambulatory values must not be stored as office values. Saudi guidance describes white-coat hypertension as office-only elevation and masked hypertension as out-of-office-only elevation; ABPM/HBPM are the confirmation tools. [^1]

**Orthostatic protocol:** measure after standing at **1 and 3 minutes** from seated (Saudi) and record symptoms; ESC describes diagnostic orthostasis as a fall of at least **20/10 mmHg** at 1 or 3 minutes after standing following 5 minutes lying/sitting. [^1][^16]

### Treatment and escalation rules

First-line uncomplicated classes are thiazide/thiazide-like diuretics, ACE inhibitors, ARBs, and long-acting dihydropyridine CCBs. [^1][^16] Do not code a Saudi-specific “Black ethnicity” branch: the ethnicity modification in some US guidance arose from particular US cohorts and has not been established as a Saudi ancestry rule in the material retrieved. Make comorbidity, albuminuria, pregnancy potential, potassium/eGFR, prior intolerance, and drug availability the selection variables.

For diabetes/CKD, the 2025 AHA/ACC document recommends ACEi or ARB with CKD (eGFR <60) or albuminuria ≥30 mg/g; do not combine ACEi and ARB. [^14] Saudi hypertension guidance recommends starting therapy at ≥130/80 and targeting <130/80 in diabetes/CKD, but a frailty/orthostasis exception must be clinician-led. [^1]

**Severe BP:** reserve “hypertensive emergency” for severe elevation *with acute target-organ damage*. The 2025 AHA/ACC guidance defines severe asymptomatic hypertension as >180/120 without acute organ damage and directs timely outpatient oral treatment initiation/reinstitution/intensification—not reflex IV lowering or ED escalation. [^14] Implement a red-flag triage set for neurologic deficit/encephalopathy, chest pain/ACS, acute dyspnea/pulmonary edema, AKI/oliguria, retinal hemorrhage/papilledema, aortic-syndrome symptoms, and pregnancy; attach human review rather than a purely numerical threshold.

## 1.3 Chronic kidney disease (P0)

**Current core source:** KDIGO **2024 Clinical Practice Guideline for Evaluation and Management of CKD**, which updates 2012 and covers evaluation/risk, progression delay, medication stewardship, and care models. [^17]

Use the **2021 CKD-EPI creatinine equation without race** as the default calculated eGFR, with cystatin-C-containing CKD-EPI confirmation where clinically indicated; ADA/KDIGO cites the ASN/NKF recommendation and explains that cystatin C improves precision and reduces racial/ethnic bias. [^10] The search did not identify a Saudi-specific replacement equation with sufficient authority to override this default. Preserve the reporting laboratory’s eGFR and equation used; do not silently recompute historical values using a different equation.

**CKD phenotype/risk fields:** persistent eGFR <60 and/or persistent ACR ≥30 mg/g establish CKD; capture both eGFR G-category and albuminuria A-category, not either alone. [^10] Embed the KDIGO G/A grid as a licensed/rendered reference if required, but store its inputs and risk category as data—not copied table art.

**RAAS safety logic:** after initiating or increasing ACEi/ARB, check BP, serum creatinine, and potassium within **2–4 weeks**. Continue/titrate if creatinine rise is <30%; an increase >30% warrants evaluation. Manage hyperkalemia where possible rather than automatically stopping RAAS blockade; dose-reduce/stop for symptomatic hypotension or persistent uncontrolled hyperkalemia, while recognizing the guideline supports continuation even below eGFR 30 when otherwise indicated. [^18][^19]

**Diabetes-in-CKD reconciliation:** make ADA/KDIGO the pharmacotherapy crosswalk and KDIGO 2024 the CKD monitoring/risk source. The ADA–KDIGO joint document explicitly says its aligned consensus statements represent broad agreement and covers RAS blockade, metformin, SGLT2i, GLP-1 RA, and ns-MRA. [^10]

## 1.4 Lipids and cardiovascular risk (P1)

Do not call ASCVD PCE, SCORE2, QRISK3, WHO/ISH, or PREVENT “Saudi validated” without documentation. The 2022 Saudi dyslipidemia guideline explicitly says international guidelines cannot be directly applied unchanged to Saudi populations and adapted ESC recommendations/thresholds to the local setting. [^2] More recently, the NHC/SHA 2025 prevention guideline was written specifically for Saudi epidemiology and healthcare needs. [^3]

**Product decision:** use the Saudi NHC/SHA 2025 prevention/risk-assessment framework as the Saudi-facing clinical reference, but retain the chosen calculator name, input date, version, result, and “not locally calibrated” flag in the record. Do not substitute PREVENT for a Saudi calculator merely because the 2025 US hypertension guideline uses it; ACC/AHA’s own lower-risk threshold is expressed in PREVENT terms. [^14]

Statin logic should be a separate versioned module. In CKD, KDIGO’s clinician takeaways endorse moderate- or high-intensity statin-based therapy and statins for most people with CKD; exact intensity/threshold should be resolved through the Saudi risk band and secondary-prevention status. [^18]

## 1.5 Geriatrics, polypharmacy, and deprescribing (P1)

**Beers.** The current AGS Beers Criteria is the **2023** update. It is a screening tool for potentially inappropriate medication, not a substitution for shared clinical decision-making; it was designed for US use, so formulary and local-context mapping are required. [^20] AGS’s posted copyright policy prohibits reproduction, display, or distribution without prior written permission and describes permission as case-by-case/noncommercial. [^21] Use Beers as a reviewed ruleset with legal clearance—not copied criteria in a commercial interface.

**STOPP/START.** Current version is **v3 (2023)**, with 133 STOPP and 57 START criteria, validated by an international European expert panel. The article is CC BY 4.0, permitting commercial use/adaptation with attribution and change marking, but verify whether any implementation reproduces third-party material. [^22]

**Deprescribing.** Evidence-based antihyperglycemic guidance recommends deprescribing agents that cause hypoglycemia in at-risk older adults and individualizing targets for frailty, dementia, or limited life expectancy. [^23] For antihypertensives, trials underrepresent frailty/multimorbidity/limited life expectancy; deprescribing may be considered after checking non-BP indications such as HFrEF, diabetic nephropathy, and AF, with tapering and monitoring because BP can rebound. [^24]

**Implementation:** assess frailty/function, falls/syncope, orthostasis, cognition, medication indication(s), life expectancy/prognosis, goals of care, BP/glucose trend, and withdrawal plan. Do not present a PIM flag as an automatic stop order. Beers specifically identifies alpha-1 blockers and central alpha-agonists as problematic antihypertensives in older adults because of orthostasis/CNS/bradycardia risk. [^20]

**Frailty and falls.** For a home visit, a brief functional screen plus a structured frailty instrument is more defensible than an unlicensed copy of a named score. The Clinical Frailty Scale’s exact use terms still need primary-source clearance; the search did not establish commercial rights. Use STEADI-style fall assessment and a medication review, while treating the fall-risk evidence as a trade-off rather than proof that BP control is harmful. Anticholinergic burden should be a configurable, named scale with version and local formulary mapping; cumulative anticholinergic exposure is associated with falls, delirium, and dementia, but a score alone should not force deprescribing. [^20][^24]

## 1.6 Ramadan and fasting (P1)

**Source of truth:** IDF–DAR **Practical Guidelines 2021** remains the identified authoritative practical document; it provides dedicated chapters on risk stratification, pre-Ramadan assessment, type 1 and type 2 diabetes, pregnancy, older adults, and cardiovascular/cerebrovascular/renal complications. [^25] The currently retrieved IDF-DAR risk framework has **three**, not four, categories: low, moderate, high. [^26][^27]

**Timing:** start assessment and education **6–8 weeks before Ramadan** (no later than 12 weeks in the Endotext synthesis); a longer three-month preparation window is reasonable for medication stabilization/training. [^27]

**Risk action:** high-risk people should generally be advised not to fast. Recent severe or recurrent hypoglycemia, hypoglycemia unawareness, unstable CVD or recent stroke, CKD stage 4–5, and several type 1 diabetes situations place people at high/very high risk in related summaries; if fasting proceeds despite advice, require specialist-supervised individualized planning and frequent monitoring. [^27]

**Medication layer — encode as a clinician-reviewed plan, not generic reminders:**

- Metformin is low hypoglycemia risk; the cited Ramadan protocol keeps a once-daily dose unchanged and takes it at iftar. [^27]
- Sulfonylureas and insulin are associated with Ramadan hypoglycemia; trigger a pre-Ramadan review for dose/timing reduction, switch options, glucose-monitoring plan, and break-fast criteria. [^27][^26]
- For basal-bolus analogue insulin, the cited synthesis suggests starting with basal reduction of roughly 20–40% and taking it at iftar/earlier evening, then individualized SMBG-guided titration. This is a **starting protocol**, not an autoprescription. [^27]
- SGLT2 inhibitors require dehydration/volume-status, ketone/DKA-risk, renal function, diuretic, and illness review; the cited Ramadan reference advises starting an SGLT2 inhibitor 2–4 weeks before Ramadan when initiating, rather than immediately before fasting. [^27]
- Diuretics and antihypertensives require individualized volume/orthostasis and timing review; do not invent a universal dose reduction from diabetes guidance.

No Saudi MOH/Saudi Diabetes Association Ramadan clinical guideline with enough authority to replace IDF-DAR was identified in this search. Treat Hajj/Umrah and recurrent non-Ramadan voluntary fasts as distinct protocol-development/primary-source-verification work; do not extrapolate the Ramadan algorithm without review. [^25]

## 1.7 Co-occurring conditions (P2)

- **Heart failure:** use the 2022 AHA/ACC/HFSA guideline plus Saudi focused update where applicable. In HFrEF, guideline-directed therapy includes four medication classes including SGLT2 inhibitors; SGLT2 inhibitors also have a recommendation in HFmrEF/HFpEF. [^28] Make HF phenotype, volume status, eGFR/potassium, and current GDMT mandatory inputs before any BP/diabetes medication change.
- **Atrial fibrillation/anticoagulation:** use the 2023 ACC/AHA/ACCP/HRS guideline as the international source and a locally approved anticoagulation pathway/formulary. It covers thromboembolic risk assessment, anticoagulation, LAA occlusion, ablation, and risk-factor modification. [^29] Require renal function, weight, age, indication, bleeding history, interacting medicines, and valve status before any dosing suggestion.
- **Obesity/GLP-1:** source from ADA section 8 and the Saudi obesity guideline; treat obesity indication, diabetes status, CKD/HF/ASCVD, pregnancy potential, contraindications, and local availability as separate fields. Do not reuse a diabetes dose for obesity treatment.
- **Diabetic foot:** retain ADA section 12 plus IWGDF guidance. Capture annual comprehensive foot screen, prior ulcer/amputation, neuropathy, deformity, PAD/ischaemia, callus, footwear, and urgent infection/ischaemia red flags. The search identified Saudi diabetic-foot burden studies but no single estimate suitable for nationwide product claims; local burden should be cited only with region/population qualifiers.
- **Retinopathy:** retain diabetes type, duration, prior retinal result, pregnancy, symptoms, and last dilated/photo screen. The exact interval belongs to an ADA section-12 versioned rule, with an automatic ophthalmology/retinal-referral pathway for abnormal findings rather than relying on a generic annual reminder.
- **Depression:** Arabic PHQ-2/PHQ-9 has been used in Saudi primary-care research and PHQ-2 correlated strongly with PHQ-9 in one Riyadh cross-sectional study, but that is not equivalent to a universal licensing/validation determination. [^30] Secure the official PHQ licence/Arabic translation terms and validate the intended workflow before embedding the questionnaire.

## Build priorities and unresolved items

**P0 before rule execution:** (1) lock ADA 2026 source bundle and permissions posture; (2) choose Saudi NHC/SHA versus ACC/AHA versus ESC target configuration; (3) ingest the KDIGO G/A grid and RAAS safety process; (4) obtain SFDA/local formulary product labels for molecule-level renal dosing; (5) set a Ramadan risk and human-review workflow.

**Still requiring primary-document verification before release:** exact SFDA-labelled eGFR floors by SGLT2i/GLP-1 product. These are not gaps to fill with guesswork.

## Release-gap resolution update

### 1.4 Lipids — Saudi risk bands, statins, and calibration

**Resolution:** use the NHC/SHA 2025 prevention guideline’s **Saudi-adopted risk-band framework**, but label SCORE2/SCORE2-OP as an *adopted international estimator*, not a Saudi-recalibrated model. The guideline defines low risk as SCORE2 <2.5% (SCORE2-OP <5%), moderate risk as SCORE2 2.5–<7.5% (SCORE2-OP 5–<10%), high risk as SCORE2 7.5–<10% (SCORE2-OP 10–<15%), and very high risk as SCORE2 ≥10% (SCORE2-OP ≥15%); it also assigns people with marked single risk factors, moderate CKD, or long-duration diabetes to high risk, and established ASCVD, severe CKD, diabetes with target-organ damage/≥3 major risk factors, or FH with ASCVD/another major factor to very high risk. [^3]

No release-ready Saudi recalibration was identified. A 2023 Saudi prediction model was derived from only 451 people at one Riyadh centre with 35 events; its authors explicitly report no external validation and say it should not be used broadly until validation. [^31] **Engine rule:** calculate and retain SCORE2/SCORE2-OP plus the Saudi guideline risk band; display `model_not_Saudi_calibrated = true`; never represent its percentage as an individualized, locally validated Saudi risk probability.

The Saudi prevention guideline directs lipid targets by risk stratum and specifically endorses LDL-C <1.0 mmol/L (<40 mg/dL) for recurrent ASCVD or extremely high risk. [^3] The 2022 Saudi dyslipidemia guidance treats CKD stage 3 as high and stages 4–5 as very high risk, and recommends high-intensity statin initiation in ACS. [^2] **Important implementation boundary:** the exact full risk-band LDL-target table was embedded as a graphical table in the primary document retrieved here; have a clinical owner transcribe-and-dually-verify it from the controlled source before it becomes executable. Do not fill the missing cells from an international guideline by assumption.

### 1.3 CKD — explicit potassium/creatinine schedule

The original “2–4 weeks” is now made operational as an **ACEi/ARB rule**: obtain baseline creatinine/eGFR and potassium; repeat **within 2–4 weeks after initiation or every dose increase**; assess sooner when acute illness, volume depletion, interacting medicines, baseline potassium elevation, advanced CKD, or prior hyperkalemia creates a clinical reason. This preserves KDIGO’s actual interval rather than inventing a one-size-fits-all tighter schedule. [^18][^32]

The clinical response is equally important: investigate an eGFR/creatinine deterioration of ≥30%, review volume status, NSAIDs and interacting medicines, and manage hyperkalemia where feasible before reducing/stopping RAAS blockade. [^18][^19] This should be encoded as: `baseline → 2–4-week lab task → clinician review → dose decision → repeat 2–4-week task after any change`. A persistent “normal” result does not create a universal interval thereafter; subsequent frequency belongs to CKD stage, potassium history, concurrent medications, and local standard of care.

Do **not** use that ACEi/ARB schedule for every potassium-raising drug. For example, the finerenone product guidance calls for potassium and eGFR reassessment **four weeks after initiation, restart, or dose increase**. [^33] Keep `drug_class` and `specific_product_label_version` as required fields in the monitoring scheduler.

### 1.5 Geriatrics — Clinical Frailty Scale rights are resolved

CFS is not a free-to-embed commercial asset. Dalhousie states that it exercises copyright over the CFS; commercial/for-profit incorporation, including incorporation into a commercial product, requires a permission request and may require a negotiated licence and fee. [^34] CFS also requires clinical judgement; its creators describe it as a judgement-based summary of a clinical encounter, not a questionnaire, and caution that inexperienced scoring may not reflect expert judgement. [^35]

**Release rule:** do not render the CFS descriptors, images, classification tree, or Arabic translation in Noor until Dalhousie permission/licensing is confirmed for the intended commercial deployment. A permitted CFS workflow should store `CFS_version = 2.0`, rater role/training, score, and clinician attestation; it must not treat a simple questionnaire algorithm as equivalent to clinician-rated CFS. [^34][^35]

### 1.6 Ramadan, Hajj/Umrah, and voluntary fasting

The search still did not identify an official Saudi MOH/Saudi Diabetes Association Ramadan document that supersedes IDF-DAR. That is no longer a blocker: use IDF-DAR 2021 as the fasting rule source, retain a jurisdiction/source tag, and monitor for a Saudi authority update. [^25]

**Hajj is now sourceable.** The 2024 Hajj update identifies altered meals, fluid intake, and physical activity, and emphasizes a “killer triad” of hypoglycemia, foot injury, and infection; it calls for risk stratification, medication adjustment, clinical assessment, and education before travel. [^36] Its full-text summary also notes that walking can exceed 40 miles and Arafat exposure occurs in high temperatures. [^37] Add a Hajj/Umrah profile that triggers a pre-travel clinician review for treatment plan, glucose/ketone plan, hydration/heat advice, footwear/foot inspection, infection/wound triage, medication supplies, and medical identification. Do not reuse a Ramadan dose schedule automatically: Ramadan is a daily fast, while pilgrimage risk is exertion/heat/variable meals and travel.

**Voluntary non-Ramadan fasting remains a true guidance gap.** IDF-DAR’s scoped practical chapters address Ramadan. Until a condition-specific source is approved, Noor should record voluntary fasting intent and surface a clinician-reviewed “individualized plan required” prompt; it should not apply Ramadan risk scores or dose reductions by default. [^25]

### 1.7 Co-occurring conditions — diabetic-foot burden and PHQ-9

**Foot burden:** no contemporary nationwide registry-derived Saudi amputation rate was identified. The most directly relevant national article explicitly reports the absence of a national registry and generates approximate, model-based estimates rather than a measured national rate; its authors themselves call for registry data. [^38] Therefore, Noor should not claim a national prevalence/amputation statistic. It can accurately state that Saudi evidence is geographically fragmented and that local diabetic-foot prevention remains a high-priority concern.

**PHQ-9 validation and rights:** the Arabic PHQ was validated in a Saudi student sample (n=731); the PHQ-9 internal-consistency value was 0.857, but that evidence does not by itself validate a diagnostic cutoff for every clinical population or home-visit workflow. [^39] Rights are comparatively favourable: Pfizer announced unrestricted, no-charge access to PHQ/GAD tools and their translations, and the PHQ-9 form states that no permission is required to reproduce, translate, display, or distribute it. [^40][^41]

**Release rule:** PHQ-2/PHQ-9 may be used in product subject to preserving the official form, attribution, wording, response options, scoring, and an explicit positive-suicidality (item 9) escalation pathway. Use it as a screen, not a diagnosis; choose the Arabic version through the official PHQ repository and clinically validate the intended referral workflow in Saudi home-care practice. [^40][^41]


[^1]: Waleed Alhabeeb. National Heart Center/Saudi Heart Association 2023 Guidelines on the Management of Hypertension.

[^2]: 2022 Saudi Guidelines for the Management of Dyslipidemia.

[^3]: National Heart Center/Saudi Heart Association 2025 Guidelines for Cardiovascular Diseases Prevention and Risk Assessment | Saudi Medical Journal, 2026.

[^4]: 6. Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises: Standards of Care in Diabetes-2026 - PubMed.

[^5]: 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026, 2026.

[^6]: 12. Retinopathy, Neuropathy, and Foot Care: Standards of Care in Diabetes-2026 - PubMed.

[^7]: 13. Older Adults: Standards of Care in Diabetes—2026 - PMC.

[^8]: Management of hyperglycaemia in type 2 diabetes, 2022. A consensus report by the American Diabetes Association (ADA) and the European Association for the Study of Diabetes (EASD).

[^9]: Management of Type 2 Diabetes, 2026. A Consensus Report by the American Diabetes Association and the European Association for the Study of Diabetes | American Diabetes Association.

[^10]: ADA-KDIGO-Consensus-Report-Diabetes-CKD-KI-2022.pdf.

[^11]: KDIGO-2022-Clinical-Practice-Guideline-for-Diabetes- ...

[^12]: Marked regional variations in the prevalence of sickle cell disease and β-thalassemia in Saudi Arabia: Findings from the premarital screening and genetic counseling program | Journal of Epidemiology and Global Health | Springer Nature Link, 2011.

[^13]: Effect of sickle cell trait and B-Thalassemia minor on determinations of HbA1c by an immunoassay method | Saudi Medical Journal, 2001.

[^14]: 2025 AHA/ACC/AANP/AAPA/ABC/ACCP/ACPM/AGS/AMA/ASPC/NMA/PCNA/SGIM Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults: A Report of the American College of Cardiology/American Heart Association Joint Committee on Clinical Practice Guidelines | JACC.

[^15]: 2024 ESC Guidelines for the management of elevated ...

[^16]: 2024 ESC Guidelines for the Management of Elevated Blood Pressure and Hypertension.

[^17]: Executive summary of the KDIGO 2024 Clinical Practice ...

[^18]: Key Takeaways PCPs - Management.

[^19]: Prasad, 2024. The KDIGO 2024 CKD Guidelines: part 2.

[^20]: American Geriatrics Society 2023 updated AGS Beers Criteria® for potentially inappropriate medication use in older adults - PMC.

[^21]: Copyright & Permissions | American Geriatrics Society.

[^22]: STOPP/START criteria for potentially inappropriate prescribing in older people: version 3 | European Geriatric Medicine | Springer Nature Link, 2023.

[^23]: Deprescribing antihyperglycemic agents in older persons | The College of Family Physicians of Canada.

[^24]: Deprescribing antihypertensive drugs in frail older adults - PMC.

[^25]: IDF-DAR Practical Guidelines 2021.

[^26]: IDF_DaR_Practical_Guidelines_...

[^27]: Almalki MH, 2022. Diabetes Management During Ramadan - Endotext - NCBI - NIH.

[^28]: 2022 AHA/ACC/HFSA Guideline for the Management of ...

[^29]: 2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis and Management of Atrial Fibrillation: A Report of the American College of Cardiology/American Heart Association Joint Committee on Clinical Practice Guidelines - PubMed.

[^30]: Adult depression screening in Saudi primary care: prevalence, instrument and cost | BMC Psychiatry | Springer Nature Link, 2014.

[^31]: Alkhenizan. Development of a Cardiovascular Disease Risk Prediction Model: A Preliminary Retrospective Cohort Study of a Patient Sample in Saudi Arabia.

[^32]: Optimizing Renin-Angiotensin System Inhibitor Use in CKD - PMC.

[^33]: Kerendia® Prescriber Guide.

[^34]: Permission for Use - Geriatric Medicine Research.

[^35]: Clinical Frailty Scale - Geriatric Medicine Research.

[^36]: Ibrahim et al., 2024. Recommendations for management of diabetes and its complications during Hajj (Muslim Pilgrimage) - 2024 update. Diabetes Research and Clinical Practice.

[^37]: Review Recommendations for management of diabetes and its complications during Hajj (Muslim Pilgrimage) – 2024 update.

[^38]: Diabetes-Related Lower Extremities Amputations in Saudi ...

[^39]: AlHadi et al., 2017. An arabic translation, reliability, and validation of Patient Health Questionnaire in a Saudi sample. Annals of General Psychiatry.

[^40]: Inc., 2010. Pfizer to Offer Free Public Access to Mental Health Assessment Tools to Improve Diagnosis and Patient Care.

[^41]: cg014193. Pfizer Inc. No permission required to reproduce, translate, display or distribute.