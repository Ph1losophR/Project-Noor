> Section 7 of the research programme. Indexed in SSOT §17.

## 7. CDS safety, effectiveness, and human factors

## Decision summary

Noor should be designed as **quiet, explainable, clinician-accountable decision support**, not as an alert engine. The evidence supports targeted CDS for medication-error prevention, but it also shows a substantial safety burden from excessive, ambiguous, or poorly timed interruptive alerts. A 2024 evidence review judged medication-related CPOE/CDS associated with fewer medication errors with moderate-certainty evidence and fewer adverse drug events with low-certainty evidence; it also found that benefits, harms, and implementation context were too heterogeneous to estimate a single net effect. [^1]

For Project Noor’s home-visit workflow, the governing design rule should be: **the engine may identify, explain, and route a concern; a clinician remains responsible for verification, action, and communication.** This aligns with the project’s deterministic, reviewer-in-the-loop posture and directly addresses alert fatigue, automation bias, malfunction risk, and the limited transportability of home-care effectiveness evidence. [^2][^3]

## 1. Alert fatigue: treat high override rates as a signal to investigate, not a benchmark to accept

The commonly repeated claim that “most alerts are overridden” is real, but the relevant number is not one universal rate. A systematic review of 23 studies found mean override rates spanning **46.2%–96.2%** and wide variation in appropriateness by alert type. For example, appropriateness of overridden geriatric alerts was 14.3%–57%, renal alerts 27%–87.5%, dose alerts 43.9%–88.8%, and drug–drug interaction alerts 0%–95%. [^4] Those ranges reflect heterogeneous settings, rules, patient data, and review methods; they are not a defensible Noor target.

What matters is that inappropriate overrides are clinically consequential. In the same evidence base, inappropriate overrides were associated with more adverse drug events; one analysis reported an adjusted odds ratio of 6.14 for an adverse event and a longer ICU stay, though this is observational evidence rather than proof that every override causes harm. [^4] The operational implication is to measure **alert volume, override, appropriateness, and downstream action/outcome separately**, stratified by rule and severity. “Accepted” cannot mean merely clicking acknowledge: in one review, documented monitoring followed an “intention to monitor” selection in only 36% of instances. [^5]

### What reduces fatigue—and the evidence strength

- **Suppress low-value, repetitive alerts; preserve a very small interruptive tier.** Low specificity and unclear content are associated with excess overrides. The review recommends patient-specific context, severity prioritisation, clear explanation, periodic pruning, and distinct treatment of minor versus high-risk alerts. [^4]
- **Use role-tailoring rather than assuming every issue belongs in the junior doctor’s foreground.** In a 39-study systematic review, alternatives to prescriber-interrupting modal alerts—including pharmacist-targeted support—were accepted more often than interruptive modals (61.57% versus 38.67%). The authors found role-tailoring to be the only alternative with an apparent acceptance advantage, but designs and outcome measures were too inconsistent for a clean causal ranking. [^5]
- **Make the corrective action easy.** A dose concern should offer the relevant clinical rationale, current renal function/date, suggested safe range or review route, and a non-autonomous “amend order” path—not simply a red warning. Common successful design patterns include severity tiers, shortcuts for an appropriate correction, and structured override reasons. [^5]
- **Do not use a raw acceptance/override target as a safety KPI.** The old “Ten Commandments” proposes an empirical aspiration of more than roughly 60% positive responses for strongly action-oriented suggestions, but even its authors call this threshold arbitrary and context-dependent. [^6] Noor should instead set rule-specific review triggers: a sudden firing-volume change, a rising override rate, a low rate of documented clinical action when action should follow, or a cluster of overrides later judged unsafe.

### Noor alert policy

| Alert tier | Noor behaviour | Required evidence in the card | Measurement / governance |
|---|---|---|---|
| **Stop-and-review** | Block the unsafe *order action* pending correction or authorised override; never block documentation of the visit or emergency escalation. Reserve for a narrowly governed set such as verified anaphylaxis-level allergy, a gross dose ceiling breach, or an absolute contraindication with reliable patient data. | Triggering data, source/date, severity basis, safe alternative or escalation path, and rule/version. | Mandatory structured override; pharmacist/clinical-owner review of every initial deployment and sampled overrides. |
| **Interruptive review** | Requires acknowledgement before signing, but clinician can proceed with an explicit reason. Appropriate for potentially serious, context-sensitive renal dose, interaction, duplicate therapy, or monitoring issues. | Patient-specific reason, why the issue matters now, relevant laboratory/medication provenance, and recommended next step. | Rule-level firing, override, appropriateness, and completion-of-recommended-action review. |
| **Passive task / queue** | Appears in the visit checklist or supervisor queue without breaking workflow. Appropriate for missing monitoring, care gaps, adherence follow-up, stale data, and lower-certainty concerns. | Specific next task, due date, source guideline/rule, and data missingness. | Completion, deferral, and expiry measured; no implication that the underlying care is unsafe. |

This is a proposed product policy, not a universal classification from the literature. It deliberately avoids turning a generic high/medium/low severity vendor label into a hard stop. Hard stops can themselves create harm when they delay time-sensitive treatment. [^5] The release-gate and measurement elements follow the documented need for ongoing impact monitoring and maintenance of knowledge-based systems. [^6]

## 2. What makes CDS effective: retain the principles, operationalise them

The *Ten Commandments* remain useful as implementation principles rather than proof that a particular feature improves outcomes. The source describes experiential lessons from one integrated US delivery system; it does not establish a Saudi home-care effect size. Its still-relevant core is speed, real-time delivery, workflow fit, usability, offering an alternative rather than simply blocking, simplicity, minimal extra data entry, feedback, and active knowledge-base maintenance. [^6]

The compatible **CDS Five Rights** are: right information, right person, right intervention format, right channel, and right point in workflow. [^4] For Noor, translate them into acceptance tests:

1. **Right information:** every displayed threshold must be traceable to a source/version/section, and every patient input must expose value, unit, effective date, source, and missingness. A recommendation based on stale or ambiguous data should say so and default to review rather than certainty.
2. **Right person:** route medication-safety detail to the clinician or pharmacist with authority to act; send senior-review triggers to the supervisor queue; give the field user a concise action request rather than an undifferentiated alert dump.
3. **Right format:** one-screen decision card: `what changed / why it matters / data used / uncertainty or exclusion / recommended next action / alternatives / provenance`. Provide a link to the full guideline rather than placing an opaque paragraph in an alert.
4. **Right channel and time:** pre-visit preparation for missing labs or high-risk reconciliation; at-order review for dose/interaction/allergy concerns; post-result task when a result returns after the visit; supervisor queue for changes requiring cosignature. A passive reference page is insufficient when a time-sensitive decision is being made. [^6]
5. **Right maintenance loop:** track every firing and action; periodically retire, retune, or reclassify rules. The original framework explicitly warns that recurring low-value suggestions extinguish attention and that knowledge content needs named ownership and ongoing maintenance. [^6]

Noor should therefore define success in a staged way: **technical correctness → usable completion in simulation → clinician action → patient-process outcome → patient outcome**, rather than counting alert clicks as effectiveness. The distinction is necessary because the alert-design literature finds acceptance measures method-dependent and notes that few studies report both acceptance and patient outcomes. [^5]

## 3. Known CDS harms: build the safety case around concrete failure modes

CDS can fail by giving wrong advice, by creating a barrier that delays appropriate care, by inducing overreliance, or by silently failing to fire. The latter is especially dangerous because users usually notice a spurious alert but not an expected alert that never appears. [^3]

A case series documented four distinct malfunction mechanisms: a drug-identifier change stopped a monitoring alert, inadvertent rule editing stopped a lead-screening alert, an EHR upgrade generated widespread spurious alerts, and a defect in an external drug-classification service produced inappropriate antiplatelet suggestions. In a small, nonrepresentative CMIO survey, 93% reported at least one CDS malfunction and two-thirds reported malfunctions at least annually. [^3] These figures are not a population prevalence estimate, but the failure modes are directly relevant to Noor’s planned dependency on terminology mappings, drug data, rule versions, and offline synchronisation.

### Required safety controls

- **Rule and dependency release gates:** fixture-based tests for every cited threshold; unit, boundary, missing-data, and stale-data cases; regression tests after any terminology, formulary, mapping, or platform change; independent clinical review of high-severity rule edits. The malfunction case series specifically recommends testing by someone other than the content author and regression testing beyond the rule intentionally changed. [^3]
- **Production surveillance:** daily/weekly rule-firing baselines; anomaly detection for zero firing, spikes, unusual override patterns, and sudden changes in data completeness; a safety incident channel that accepts “expected alert absent” reports.
- **Fail-safe presentation:** when a prerequisite is absent, ambiguous, stale, or locally unavailable, show `cannot assess safely` / `clinician review required`; do not silently evaluate a rule as negative.
- **Change provenance:** store the clinical content source, rule version, input snapshot, output, user action, override reason, and follow-up completion. A change log that does not correspond to the executable rule is not adequate; in the case series, manual logs were incomplete and reconstructing history required backups. [^3]
- **Wrong-patient prevention:** bind the alert card to a persistent patient identifier, name/date of birth confirmation in high-risk actions, encounter timestamp, and a visible “data provenance” summary. The retrieved literature did not provide a strong, home-visit-specific wrong-patient-alert intervention estimate; this should be usability-tested in Noor’s own prototype rather than assumed solved by a generic banner.

## 4. Automation bias in junior clinicians: a real concern, but not one with a junior-doctor-only effect estimate

The most relevant evidence is not restricted to junior doctors. A systematic review found that task-specific experience, user trust and confidence, workload, complexity, and time pressure mediate automation bias. [^2] In the small pooled subset of healthcare experiments, incorrect decision-support advice increased the risk of an incorrect decision by 26%; studies also found that 6%–11% of originally correct decisions were changed to incorrect decisions after support. [^2] This is controlled-study evidence, much of it from diagnostic support and not Noor’s specific rule-based setting; it supports a hazard model, not a predicted rate in Saudi home care.

Junior clinicians are plausibly more exposed because task inexperience was associated with more automation-related errors, even though less experienced users may gain more overall from support. [^2] Noor should neither deny this risk nor remove useful support. It should design for **appropriate reliance**:

- **Show evidence before the recommendation:** display the patient facts and the deterministic logic/threshold that triggered the card, with a direct guideline citation and date. Do not lead with an authoritative command.
- **Use “review / consider / verify” when data or applicability are uncertain; reserve directive language for genuine safety constraints.** Information/supportive displays can reduce automation bias relative to command-like advice, while excessive display prominence can increase it. [^2]
- **Require an active, patient-specific action for high-stakes recommendations:** select a rationale, identify a conflicting fact, document a supervised plan, or explicitly defer. Do not require ritual clicks for low-value alerts.
- **Train with deliberately wrong and incomplete cases:** onboarding should include data-quality failure, missing-result, medication-list discrepancy, and misleading-but-plausible alert scenarios. Training and accountability are among the mitigators identified in the review, though evidence is mixed and should not be oversold. [^2]
- **Make escalation easy and blame-free:** “request pharmacist review,” “send to supervisor,” and “report rule concern” must be quicker than trying to work around the system.
- **Audit calibrated reliance:** in simulation and pilot work, measure both unsafe acceptance of seeded wrong advice and failure to act on seeded correct high-risk advice. Measure performance separately by user seniority, workload, and visit complexity.

## 5. Communicating uncertainty and provenance

Noor’s first release is deterministic, but uncertainty still exists in input validity, guideline applicability, evidence strength, and the distinction between a rule trigger and a clinical decision. A scoping review of 130 deployed data-driven CDS studies found that most outputs provided a probability or a risk class, but only 35 studies explicitly described their classification rule; 17 of those used arbitrary thresholds. [^7] The review found that 90 systems expressed some uncertainty, usually only as a bare probability; only a minority used confidence intervals or visual uncertainty, and few tested whether their uncertainty display improved decisions. [^7]

For Noor, **provenance is the more immediate safety intervention than numerical confidence**. Every card should show:

- `why now`: trigger and specific patient data;
- `data status`: source, time, unit, final/preliminary state, reconciliation status, and missing/stale/discordant flags;
- `rule status`: content source, source version/section, local policy version, executable rule version, and last clinical review date;
- `scope`: eligible / excluded / indeterminate and the reason;
- `meaning`: what outcome or harm the rule addresses, and what it does *not* establish;
- `action`: bounded next step, alternatives, responsible role, and due date;
- `uncertainty`: local calibration/applicability statement where relevant and an explicit “do not use alone” statement for probabilistic models.

This proposed disclosure bundle makes the input, rule, and scope conditions inspectable; it responds to the review’s finding that many deployed systems leave classification rules and clinically meaningful uncertainty unclear. [^7]

Avoid naked risk percentages and binary labels that invite clinicians to treat a threshold as a command. The uncertainty review warns that a high/low classification can obscure whether a probability is calibrated or clinically meaningful, and that clinicians may read a high-risk label as a correct decision rather than a decision-support input. [^7]

## 6. Does home-based chronic disease management improve outcomes?

The answer is **yes for intermediate control measures, with substantial caveats about the bundle, setting, and durability.** A home-visit meta-analysis of seven RCTs (686 participants) reported an average HbA1c reduction of 0.79 percentage points versus usual care and, in only two small trials, systolic/diastolic BP reductions of about 6 mmHg. The interventions were multifaceted and varied in duration; the authors found no economic analyses and noted short follow-up and limited study quality. [^8]

A later meta-analysis of 27 remote-management RCTs (about 9,100 participants) found small but statistically significant improvements in HbA1c, lipids, and BP. Its interventions combined education, monitoring, coaching, remote consultation, and medication management, so it cannot isolate the contribution of CDS. Twelve trials were at high risk of bias, and exclusion of high-risk studies made the systolic-BP result borderline; pooled adverse outcomes, mortality, hypoglycaemia, and admissions were not significantly different. [^9]

**Value-claim boundary for Noor:** say that a governed home-visit workflow *may help improve risk-factor control*, not that the CDS itself reduces admissions, prevents complications, or is cost-saving. The evidence does not yet identify the active component, and the remote-management review found no pooled cost-benefit analysis. [^9] Noor’s pilot should prospectively measure process outcomes (reconciliation completion, closure of safety tasks, guideline-concordant monitoring) alongside BP/HbA1c/lipid control, medication harms, ED visits, admissions, patient burden, and cost per completed high-risk review.

## 7. Medication reconciliation and pill counts: useful evidence, not a truth test

Pill count measures pills removed from a container—not ingestion, timing, correct dose, intentional use, or use of medicines stored elsewhere. In an antihypertensive study using electronic monitoring as the comparator, concurrent pill count correlated moderately with dose quantity (r=0.52) and weakly with timing (r=0.17); refill data showed a similar quantity-versus-timing limitation. [^10] Pill counts should therefore never cause Noor to label a patient “adherent,” suppress a safety concern, or infer a causal explanation for poor control.

The protocol matters. A study of unannounced telephone counts in HIV found high agreement with unannounced home counts, but office-based counts were described as among the least reliable approaches and the study itself documented missed bottles and pillboxes. [^11] That is evidence for a carefully designed, unannounced research protocol in antiretroviral therapy—not validation of a scheduled, one-time pill count in a Saudi home visit.

### Noor medication-reconciliation design

1. **Reconcile each product before counting:** ingredient/strength/form, intended schedule, prescriber, indication, start/stop date, bottle/pack identity, dispensing/refill evidence where available, patient report, caregiver report, OTC/herbal use, and observed containers.
2. **Record a count as an observation:** `counted quantity`, `expected quantity under stated regimen`, interval, all containers present? pillbox? loose doses? recent refill? travel supply? shared medicine? Do not convert a single count into a percentage without these assumptions.
3. **Interpret discordance as a conversation trigger:** “possible supply/use discrepancy—clarify,” not “noncompliant.” Ask separately about cost/access, forgetfulness, fasting, side effects, understanding, stigma, deliberate dose changes, and caregiver administration.
4. **Triangulate where feasible:** patient/caregiver report + physical products + dispense history + clinical response, while retaining disagreement rather than forcing a single truth value. The literature explicitly notes that dispensing, container opening, pill removal, biomarkers, and self-report each measure different stages rather than a gold standard. [^10]

## 8. Adherence instruments and licensing: do not put a proprietary scale into the MVP by accident

### MMAS-8

MMAS-8 is familiar but is a poor default for a zero-budget commercial product. The licensor states that permission is required for the scale and coding, restricts distribution and disclosure of its scoring algorithm, and treats the scale, content, name, and trademarks as protected. [^12] A meta-analysis of 28 validation studies found acceptable reproducibility in some settings but, at the cut-off of 6, low pooled sensitivity (0.43) and only moderate specificity (0.73); it concluded that criterion validity was insufficient for screening individual patients for nonadherence. [^13]

**Decision:** do not use MMAS-8 in Noor’s product, internal pilot, or marketing materials unless a written commercial licence, Arabic version rights, score/display rights, and use-case validation are secured. Do not reproduce its items or reword them so closely that the product becomes a derivative-work question. [^12]

### ARMS / ARMS-D

ARMS was designed for lower health-literacy populations and consists of 12 questions that can be administered verbally or in writing; its developers explicitly note that cultural context can make refill/cost items less relevant. [^14] But ARMS is not automatically free for a startup: the ARMS-D academic licence is free only for non-commercial academic/research use and expressly excludes commercial use and unauthorised modification. [^15]

**Decision:** ARMS could be a future licensed, Arabic-cognitively-tested instrument, but it is not a no-cost product component. Obtain written terms for the original ARMS and for any Arabic translation before use. [^15]

### Voils DOSE-Nonadherence

DOSE separates extent of missed doses from reasons for nonadherence, and its authors state that the extent domain is broadly applicable while reasons should be tailored to the disease/population. [^16] It is also copyrighted and requires a licence per project; the published FAQ says it is free for research and healthcare implementation but directs commercial users to obtain terms. [^16]

**Decision:** methodologically attractive because Noor needs reasons, not just a score; legally not a default unless the commercial licence is confirmed and Arabic adaptation is governed.

### Recommended MVP: Noor’s own structured, non-score interview

Until a licensed measure is approved, implement a short **structured medication-use conversation**, explicitly labelled *clinical assessment, not a validated adherence score*. It should not output “high/medium/low adherence” or a percentage. This avoids importing a tool whose individual-screening validity or rights do not match Noor’s intended use. [^13][^12] Record:

- missed, delayed, stopped, reduced, or doubled doses by medication and recall period;
- refill/access/supply gap;
- reason taxonomy (cost/access, forgetfulness/routine, understanding, adverse effects, belief/preference, fasting, swallowing/administration, cognitive/physical limitation, caregiver/communication, other);
- patient confidence and desired support;
- observed reconciliation evidence and uncertainty;
- agreed next action and owner.

These elements reflect the evidence that adherence measures represent distinct stages of medication use and that a clinically useful assessment must distinguish causes rather than merely assign a score. [^10]

This preserves a clinically useful, culturally localisable assessment while avoiding false validation and licensing exposure. Before claiming psychometric validity, Noor should conduct Arabic cognitive interviews with homebound older adults, caregivers, and clinicians; then compare the structured findings with dispense data and carefully specified clinical outcomes. A measure used in multiple conditions must not assume that one global answer accurately represents oral, injectable, and condition-specific medication behaviour; the DOSE guidance itself reports that patients considered separate condition- and route-specific questions more accurate in cognitive interviews. [^16]

## Build order and pilot evaluation

**P0 — before patient-facing pilot:** versioned rule cards with provenance; non-firing and spike detection; test suites and change control; patient/encounter identity protections; a narrow interruptive-alert policy; structured override reasons; a supervisor/pharmacist escalation path; user testing with junior doctors and home-visit simulations. [^3]

**P1 — first pilot:** dashboard by rule and severity (firings, interrupts per visit, overrides, override rationale, action completion, time-to-resolution, and safety incidents); simulations seeded with wrong/incomplete data and wrong recommendations; independent review of all high-severity overrides; outcome capture for medication discrepancies, overdue monitoring, BP/HbA1c, ED visits, admissions, and patient contact completion. [^5][^2]

**P2 — value and effectiveness claim:** a controlled or stepped rollout with pre-specified patient-process and harm endpoints. Do not use alert acceptance as the primary effectiveness endpoint. The key decision is whether Noor improves safe completion of work **without** increasing unresolved high-risk issues, clinician burden, inappropriate therapy changes, or delayed care. [^1][^5]

## Final product posture

Noor should earn clinician trust through restraint: cards that show their evidence, inputs, limits, and ownership; a small number of truly interruptive hazards; structured but non-punitive overrides; and surveillance for both alerts that fire too often and alerts that fail silently. Existing home-visit and remote-management evidence supports measuring improvements in risk-factor control, but it does not yet establish that Noor’s CDS architecture will improve admissions or be cost-saving. The pilot should therefore be framed as a safety-and-workflow validation first, an effectiveness study second, and a commercial value claim only after both are demonstrated. [^3][^9]


[^1]: Syrowatka et al., 2024. Computerized Clinical Decision Support To Prevent Medication Errors and Adverse Drug Events.

[^2]: Goddard et al., 2012. Automation bias: a systematic review of frequency, effect mediators, and mitigators. J. Am. Medical Informatics Assoc.

[^3]: Wright et al., 2016. Analysis of clinical decision support system malfunctions: a case series and survey. J. Am. Medical Informatics Assoc.

[^4]: Poly et al., 2019. Appropriateness of Overridden Alerts in Computerized Physician Order Entry: Systematic Review. JMIR Medical Informatics.

[^5]: Hussain et al., 2019. Medication safety alert fatigue may be reduced via interaction design and clinical role tailoring: a systematic review. J. Am. Medical Informatics Assoc.

[^6]: Ten Commandments for Effective Clinical Decision Support - PMC - NIH.

[^7]: Gray et al., 2024. Risk and Uncertainty Communication in Deployed AI-based Clinical Decision Support Systems: A scoping review. medRxiv.

[^8]: Han et al., 2017. Are home visits an effective method for diabetes management? A quantitative systematic review and meta‐analysis. Journal of Diabetes Investigation.

[^9]: Fernando et al., 2022. Effectiveness of Remotely Delivered Interventions to Simultaneously Optimize Management of Hypertension, Hyperglycemia and Dyslipidemia in People With Diabetes: A Systematic Review and Meta-Analysis of Randomized Controlled Trials. Frontiers in Endocrinology.

[^10]: Choo et al., 1999. Validation of patient reports, automated pharmacy records, and pill counts with electronic monitoring of adherence to antihypertensive therapy. Medical Care.

[^11]: Kalichman et al., 2008. Monitoring Medication Adherence by Unannounced Pill Counts Conducted by Telephone: Reliability and Criterion-Related Validity. HIV Clinical Trials.

[^12]: What are the Licensing terms for using the Morisky Scale.

[^13]: Moon et al., 2017. Accuracy of a screening tool for medication adherence: A systematic review and meta-analysis of the Morisky Medication Adherence Scale-8. PLoS ONE.

[^14]: Adherence to Refills and Medications Scale | Emory University | Atlanta GA.

[^15]: ARMS-D Application: Academic License | ARMS-D.

[^16]: DOSE-Nonadherence Measure FAQs | Internal Medicine | U of U School of Medicine, 2025.