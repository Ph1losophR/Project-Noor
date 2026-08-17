> Section 11 of the research programme. Indexed in SSOT §17.

# 11. Topics raised during the design interview

## Scope and decision posture

This briefing addresses only checklist §11. It combines targeted literature and Saudi operational/regulatory discovery with the project’s prior regulatory, interoperability, safety, architecture, and market work. Several questions in §11 ask for provider-specific practice or an authoritative Saudi legal interpretation; where no public primary authority was located, this report marks the item as an **external validation gate**, rather than converting an assumption into product logic. [^1][^2]

**Cross-cutting conclusion.** Noor should be a conservative, stateful safety workflow rather than a form, alert, or scoring layer: distinguish data that are *present* from data that are *usable*; retain an explicit `cannot assess safely` outcome; never make patient contact or supervisory review implicit; and delay claims about integrations, supervision law, sandbox access, or field connectivity until a named Saudi deployment partner confirms them. [^3][^4] The most mature evidence supports structured medication reconciliation and narrowly governed CDS, while the Saudi-specific operational facts remain much thinner. [^4][^5][^6]

## 11.1 Data validity and error mitigation

### Delta checks: use as a review trigger, not an automatic correction

Laboratory delta checks compare a current result with a prior result as an absolute, percentage, or rate-of-change difference. They are established laboratory-quality tools, primarily to detect specimen misidentification or analytical/pre-analytical error; their positive yield is generally low and investigations consume staff time. Published reviews consequently recommend selecting analyte, calculation method, and threshold carefully, then monitoring false positives and false negatives. [^7]

That evidence does **not** validate a universal delta threshold for home-entered BP, pulse, weight, or glucose. A vital-sign data-quality engine did use physiologic parameters and quality scores to identify malformed ED entries, and found Fahrenheit-for-Celsius temperature errors among the common problems, but that was a data-warehouse study—not a basis for a clinical vital-sign delta cutoff. [^3]

**Implementation decision:** implement a *three-layer data-quality gate*:

1. **Parse/unit checks** — invalid characters, impossible unit/value combinations, decimal/transposition patterns, and changed unit from the patient’s prior record.
2. **Plausibility checks** — a configurable field-specific physiologic envelope and a narrower operational “expected measurement” envelope; neither produces a diagnosis.
3. **Delta review checks** — compare only like-with-like measurements (same observable, unit, context, device class, and reasonable time interval). A suspicious delta creates `needs_repeat_or_verification`, displays prior/current value and context, and requires confirmation—not silent conversion, replacement, or suppression. [^7]

Maintain separate states for `raw`, `converted`, `confirmed`, `repeated`, `rejected`, and `clinically exceptional but accepted`. This is essential: a very abnormal real value and a mistyped value should not collapse to the same system outcome. [^3]

### Boundaries and units

Store three separately versioned boundary types per observable: **technical/physiologic plausibility** (could the instrument/person generate it?), **clinical urgency** (does it require a workflow response?), and **target/pathological range** (does it indicate control or disease state?). Do not reuse a treatment threshold as a data-entry validator. The literature found that technique and equipment problems can materially distort patient BP readings; after a five-minute rest, the patient–nurse difference narrowed, yet variability remained large. [^8]

For glucose, preserve original unit and convert only with a displayed conversion and provenance; unit ambiguity must be a hard data-quality failure. For HbA1c, retain both the reported unit and assay/result source; do not infer percent versus mmol/mol from value alone when a unit is absent. The vital-sign study’s Fahrenheit/Celsius issue shows why unit detection must be a first-class safety control rather than an import convenience. [^3]

### Repeat measurement before action

There is good measurement-method rationale, but no retrieved home-care trial establishing a universal error-reduction percentage from “repeat any threshold-crossing measurement.” The defensible product rule is conditional: if a result is unexpectedly extreme, measurement quality is uncertain, or a decision would change because of a single non-emergent value, prompt an immediate standardized repeat and record both readings. Do **not** delay emergency escalation merely to satisfy a repeat protocol. Patient self-measurement research found that inadequate preparation, technique, and inaccurate equipment were common, with 42% of initial readings producing a different hypertension classification from a trained nurse’s reading. [^8]

### Entry-error expectations

Do not set an unsupported universal EMR “error rate” target. The retrieved evidence shows context-specific free-text vital-sign quality can be high after validation but still contains unit and workflow-related errors. Noor should instead establish its own baseline during a shadow pilot: missing-unit rate, rejected-value rate, delta-check rate, repeat-confirmation rate, correction rate, time-to-correction, and the proportion of clinically important changes after verification. [^3]

## 11.2 Lab validity windows and pre-visit gating

### Separate biological look-back from guideline monitoring cadence

A result can be analytically valid yet no longer clinically informative. Treat each data requirement as a four-part policy: `test + clinical context/stage + status + maximum age`. The *maximum age* answers whether Noor may use the result in a particular rule; the *monitoring interval* answers whether the patient is due for another test. They are not interchangeable. [^9]

For CKD stage 3, a 2025 rapid review/consensus found support for routine eGFR, HbA1c, and haemoglobin monitoring, but not indiscriminate repeated testing of a broad panel in stable patients; patients receiving ACE inhibitor/ARB treatment still needed potassium monitoring. This is useful context, but it is UK consensus/preprint evidence—not a Saudi-specific interval policy. [^9]

**Noor policy structure (not final clinical thresholds):**

- **HbA1c:** a historical measure of glycaemia, not a current bedside value. Mark an old result as `not_current_for_treatment_review` rather than merely “present.” Final window and cadence must be sourced to the selected diabetes guideline and individualized by therapy/control.
- **Creatinine/eGFR:** freshness is medication- and risk-context dependent. A result usable for stable long-term monitoring may be unsuitable before a renal-dose decision, acute illness assessment, dehydration concern, or recent RAAS/SGLT2i/diuretic change.
- **ACR:** retain specimen date, specimen type, repeat/confirmation status and collection context; do not treat a single old ACR as stable renal-risk classification.
- **Potassium:** require final/corrected status, specimen/haemolysis information where received, timing relative to relevant medicines, and a short action-specific window.
- **Lipids:** use a longer preventive-care cadence, but do not confuse that with medication-safety data freshness. [^9]

This context-sensitive model follows the retrieved CKD monitoring evidence’s distinction between stable routine monitoring and treatment-linked monitoring; final interval values need the named clinical guideline, not a generic platform TTL. [^9]

Each rule should declare its own data-requirement manifest: code, unit, accepted status, effective/specimen time, source preference, maximum age, required context, and `indeterminate` behavior. This avoids the unsafe “latest value wins” pattern. [^9]

### Saudi home-lab and POC workflow

The Ministry of Health describes home-health services as including laboratory tests, but its public service page does not establish who orders, collects, pays, transports, or returns results for a specific provider or home-visit cohort. [^10] Therefore, “pre-visit labs” is a **workflow hypothesis**, not an MVP dependency. Interview the first provider’s home-health lead, laboratory manager, and finance lead to map: order authority, draw location, phlebotomy capacity, collection cut-off, results interface, abnormal-result ownership, payment/coverage, and typical turnaround by analyte.

POC use is likewise an evaluation project, not an assumption. SFDA has a point-of-care-device manufacturing guidance page, but the public landing page retrieved does not identify a Noor-ready, SFDA-authorised HbA1c or creatinine device, performance claim, consumable price, or operating model. [^11] Before adopting POC testing, build a device dossier: exact SFDA registration/authorisation, intended setting/operator, sample type, analytical performance versus the receiving laboratory, external/internal QC, connectivity/result provenance, consumables, maintenance, training, infection control, and total cost per actionable result. A POC result must retain `method/device` and cannot silently substitute for a central-lab result in a rule that depends on a particular assay context.

## 11.3 Supervisor review and queue triage

### Legal sign-off and operational capacity are separate questions

No public source retrieved establishes a universal Saudi rule that a resident’s home-visit prescription must receive consultant co-signature within a named time. Noor must not encode a made-up national rule. The public Saudi material retrieved for home healthcare describes services but not resident prescribing/co-sign authority. [^10] The release gate is written confirmation from the sponsoring provider’s medical director, credentialing office, and legal/compliance function covering: clinician category, privileges, permitted prescribing acts, high-risk medicines, remote versus in-person supervision, documentation, escalation, and signature timing.

Until then, Noor should remain non-prescriptive: it generates an evidence/provenance-rich recommendation, records the responsible clinician, and routes pre-defined high-risk actions to the provider’s authorization pathway. This is consistent with the broader Saudi regulatory finding that patient-specific clinical interpretation is a regulated design concern and that provider governance cannot be inferred from job title alone. [^11]

### Queue design

Do not apply a generic machine-learning “risk score” to the supervisor queue. Use an inspectable, safety-first ranking with explicit components: severity/urgency, time sensitivity, action type, data quality, patient vulnerability, unresolved prior task, elapsed time, and whether patient contact is required. A high-risk *but data-ambiguous* event should rank for verification, not be shown as a certain diagnosis. [^3]

Published CDS evidence supports this restraint. Hard stops improved outcomes/processes in many studies but also produced avoidance, extra alerts, and delayed care; favorable implementations used strong user involvement and iterative design. [^6] Start with three lanes:

- **Immediate escalation:** provider-defined emergency/high-harm conditions; no queue delay.
- **Same-day clinician/supervisor review:** potentially serious medication, lab, or plan-change concern with adequate data.
- **Routine review/task:** missing monitoring, reconciliation discrepancy, or lower-certainty advisory. [^6]

Track review SLA from *rule evaluation time* to *responsible reviewer decision*, not merely from chart opening. There is no retrieved evidence for a universal sustainable visits-per-supervisor ratio or a standard auto-escalation deadline; measure local queue arrivals, active review minutes, backlog age, completion, and adverse near-misses in a shadow period before committing to a service level. [^6]

### Prospective versus retrospective review

For high-risk prescribing or major plan change, prospective authorization is the safer default; retrospective review is better suited to audit, learning, and lower-risk documentation. The precise boundary should be a provider policy tied to permitted scope, drug/action, patient instability, and availability of reliable data—not an unsupported claim that every act requires a consultant. Noor should treat an expired review SLA as an operational safety event: escalate to a named backup role, continue documenting, and never manufacture approval automatically. [^6]

## 11.4 Care-plan amendment and patient contact

A supervisor amendment after a patient has acted on a plan is a **closed-loop task**, not a note amendment. Model: `change approved → recipient/communication mode selected → contact attempted → comprehension/teach-back documented → plan delivered → acknowledgement or failure recorded → escalation/closure`. The task needs owner, urgency, due-by time, contact attempts, alternative contact/caregiver permission, outcome, and source rule/clinical rationale. [^4]

The home-health reconciliation evidence shows why this cannot be treated as administrative polish: in a field study, two-thirds of observations required a nurse to call a provider, and medication-list changes were frequent even with interoperable data. [^4]

**Failed-contact protocol:** define provider-approved successive attempts, channel sequence, caregiver/authorized contact pathway, risk-based supervisor escalation, and a final documented status such as `contacted`, `message delivered`, `unreachable`, `declined`, `emergency referral`, or `handover required`. Do not mark a plan change complete merely because a message was sent. [^4]

No primary Saudi source was retrieved that establishes a general medication-error disclosure script or fixed deadline applicable to Noor. Treat this as a provider legal/clinical-policy gate; the product must support factual incident documentation and escalation without pre-judging whether an error occurred or who is liable. [^12]

## 11.5 Alert and override design

### Hard stops should be rare and action-scoped

The evidence supports hard stops as powerful but potentially harmful. In a systematic review, 11 of 32 studies reported unintended consequences, including workarounds and delays to care; the authors recommend judicious, iteratively monitored deployment. [^6] Noor’s proposed scope—verified severe allergy, absolute contraindication, and gross dose ceiling—fits the evidence **only if** the patient identity, drug mapping, allergy status, dose, and contraindication input are reliable and the provider has approved an escape/escalation path.

**Product rule:** block the *unsafe order action*, never documentation, note submission, emergency activation, or the entire encounter. When the required input is stale, contradictory, missing, or an unverified patient report, prefer `cannot assess safely` and an interruptive review—not an absolute block. [^6]

### Overrides

A structured override should capture: alert/rule/version; patient facts and data status; selected reason; optional free text; action taken or deferred; responsible user; reviewer/co-sign requirement; and planned follow-up. A Saudi study of 1,087 evaluated medication-alert overrides judged 67.89% inappropriate; seven medication errors were found among a sampled set of inappropriate overrides and none among the sampled appropriate overrides. It also recommended both better dose context and free-text capacity alongside structured options. [^12]

There is no universal published taxonomy or single “normal” override rate. Author a controlled local taxonomy from observed reasons—e.g., patient-specific benefit, alternative monitoring, incorrect/incomplete data, already addressed, guideline exception, formulary/availability, duplicate/irrelevant alert, technical issue, defer/escalate—and require clinical governance for new categories. Treat override rate as a *signal*, stratified by rule, severity, role, and reason; never as a standalone performance target. [^12]

A two-key/co-sign override is reasonable for the small set of pre-approved high-harm actions, but it is a governance design choice, not a substitute for valid data or a blanket workflow. Review every hard-stop override initially; later sampling can follow demonstrated rule performance. [^6]

## 11.6 Offline and field-device reality

Public Saudi material establishes a highly digital health environment but does not prove reliable connectivity at every home-visit location. The available national/mobile sources retrieved are either high-level or access-restricted; they cannot justify treating offline as rare. [^13] Design offline-first for safety-critical documentation and local evaluation, then quantify actual connectivity by region, carrier, building type, and time during discovery visits.

### Local evaluation boundary

Evaluate on device only rules whose required data are stored locally, version-pinned, and safe to update atomically: verified allergy, curated contraindications, product/dose ceiling, duplicate ingredient/class, selected interaction pairs, unit checks, and data freshness checks. Interaction checking can become substantially larger and context dependent as it adds active ingredients, route, dose, renal/hepatic function, labs, duration, and product mappings. Therefore, Noor must not claim comprehensive interaction coverage from a small tablet table; display the scope/version and route non-covered cases for pharmacist/clinical review. [^12]

### Sync and local protection

Use append-only encounter events and explicit conflict objects—not last-write-wins—for simultaneous or delayed edits. Preserve author/device/time, base version, changed field, clinical status, and resolution actor. Clinical interpretation must not run on an unresolved conflict. [^3] Separate: (1) local draft, (2) signed clinical observation, (3) synced source fact, (4) rule evaluation snapshot, and (5) follow-up task.

For shared devices: encrypted storage, device-managed enrolment, short session expiry, role-based access, biometric/PIN re-authentication for high-risk actions, remote wipe, no patient data in notifications, offline audit queue, and a lost-device procedure are release gates. Saudi PDPL-specific controls remain subject to the provider’s DPIA/data-processing design. [^13]

Existing home-health EHR products demonstrate that offline charting followed by later synchronization is a real design pattern; it is not proof that any particular conflict model is safe for Noor. [^4] Study OpenMRS/CommCare/DHIS2 as implementation references only after defining Noor’s clinical conflict semantics.

## 11.7 Patient self-monitoring data

### Separate home from office measurements

Do not pool home and clinic BP readings or render one control label without measurement context. [^8] Store setting, device, cuff, method, training/validation status, posture/rest information where available, date/time, and whether the value is device-imported, device-memory-verified, patient-entered, or transcribed by staff.

The literature retrieved confirms the risk: in a 69-person observational study, nearly half of initial patient readings classified hypertension differently from trained-nurse readings; adequate rest, training, and equipment assessment materially changed the comparison. [^8] This supports a **density and provenance gate**, not a claim that all self-monitoring is unreliable.

Use the selected hypertension guideline—not this research brief—as the source for exact home thresholds and number/timing of readings. The minimum data structure should permit duplicate morning/evening readings, a multi-day protocol, and a `below_minimum_density` status. The trajectory feature should remain silent or say `insufficient data` below a pre-specified density/quality gate. [^8]

### Data reliability and ingestion

Prefer automatic device memory or validated-device data transfer where possible; distinguish it from manually reported values. The evidence retrieved includes a direct comparison of self-reported home BP with automatically stored values, but the returned abstract did not expose quantifiable discrepancy results, so it cannot support a numeric fabrication or under-reporting rate. [^14]

For glucometers/CGM, start with practical evidence collection: device make/model, whether data can be shown in device memory/app/export, timeframe, signal of missing days, and whether staff can verify the patient/device match. Do not make vendor integration a prerequisite for the first pilot. Build a `source_confidence` field and preserve uncertainty. [^14]

Saudi Sehhaty publicly describes medication tracking and vital-sign follow-up/updates, but the public service material does **not** establish an external API or provider ingestion route. Treat it as an adjacent patient data source to investigate with Lean/MOH and the deploying provider, not a build assumption. [^10][^15]

## 11.8 Conditional/adaptive form generation

Adaptive documentation is established as a workflow concept, but it must be clinically governed. The strongest directly relevant study retrieved compared a home-health electronic medication-reconciliation module against paper workflow: it reduced unaddressed discrepancies but did not reduce task time in a simulated study. [^5] That supports structured, context-aware reconciliation—not the broader claim that conditional forms will automatically save time or preserve completeness.

**Design:** a core minimum dataset for every visit plus profile-driven modules that are visibly triggered by documented patient facts, not hidden assumptions. Each displayed or suppressed question needs a rule/version and reason; clinicians must be able to open the full form and record “not assessed” with a reason. Measure completion, time, missed critical fields, rework, and user-perceived burden in simulation. [^5]

For home environment, medication storage, falls, and caregiver capacity, adopt a validated instrument only after confirming population, language rights, training, scoring, and commercial use rights. The current evidence set did not establish one suitable, freely reusable Saudi home-health caregiver-competence instrument. Until then, use non-score structured observations, clearly labelled as such, and avoid claiming a validated risk classification. [^4]

Brown-bag review should be operationalized as reconciliation evidence: request all prescription, OTC, herbal, topical, injectable, and device supplies; record what is physically present; map ingredient/strength/form; compare with orders, patient/caregiver report, dispense evidence, and plan; retain discrepancies rather than forcing one “correct” list. Home-health observations found a high medication and high-risk medication burden, frequent list changes, and persistent provider calls even with interoperability. [^4]

## 11.9 Multi-tenancy, profiles, and governance

Tenant-specific thresholds are legitimate only if profiles are versioned, constrained, and testable. Do not let a tenant edit a threshold in a live rule or disable an advisory invisibly. A profile should inherit a vendor clinical baseline, declare each permitted variation and its rationale/source/approver/effective date, run the full affected golden-case set, and emit the profile version in every recommendation. [^6]

Rule disablement needs the same discipline: named requester, reason, clinical owner approval, start/end date, affected population, replacement pathway, test evidence, and post-change monitoring. A rule that is disabled should evaluate to `suppressed_by_governed_policy`, never silently disappear. [^6] This makes operational choice inspectable without implying a legal conclusion about liability.

Cross-tenant learning must stay human-approved, as the design interview requires. Aggregate only a governance-defined minimum dataset; separate product analytics from clinical records; treat override data as potentially sensitive operational data; and contractually specify controller/processor roles, permitted use, retention, re-identification prohibition, access, export, and deletion. Do not assume HIPAA Safe Harbor is a Saudi PDPL de-identification standard; obtain Saudi privacy advice and a provider-approved data-sharing design before any cross-tenant analytics. [^13]

Clinical content releases should be immutable and staged: draft → technical validation → clinical review → approved → scheduled → active → retired. Each emitted recommendation pins clinical source/version, local profile, terminology/product mapping, executable rule version, input snapshot, and runtime configuration. This is a safety requirement, not merely a software-engineering preference. [^6]

## 11.10 Emergency handling

The available Saudi evidence identifies national prehospital emergency-care research priorities but does not provide a public, home-health-specific emergency protocol that Noor can safely encode. [^16] Consequently, Noor must have a provider-approved emergency pathway that is locally configured and rehearsed: immediate scene safety; emergency-service activation under the current Saudi route; concurrent clinical escalation; time-stamped minimal event capture; and an encounter state of `interrupted_for_emergency`. [^16]

Do not make a field user complete documentation before escalation. After the event, permit retrospective completion with separate occurrence, action, and documentation timestamps; preserve the time gap rather than backdating. The provider must supply required handover information, emergency contact path, medical director notification, and incident-reporting procedure. [^16]

Red-flag libraries for DKA/HHS, severe hypoglycaemia, hypertensive emergency, ACS, and stroke must be a separately governed, cited clinical-content package. Each must distinguish symptoms prompting emergency activation from values prompting repeat/urgent review, reflect patient context and measurement quality, and contain explicit exclusions. Do not construct those thresholds from memory in a general workflow specification. [^16]

## 11.11 Validation sandbox and accelerator path

The recalled name is now clearer: the public record identifies an **experimental AI-in-health-sector environment** launched by Ministry of National Guard Health Affairs with Monsha’at in connection with Biban 2025. It aims to let entrepreneurs develop and test AI solutions in a secure, governed environment with attention to regulatory compliance and data protection. [^2] The page does not state cohort access, synthetic-data availability, eligibility, fees, application timetable, whether the environment is a shadow or live deployment, or whether participation has any SFDA legal effect.

**Decision:** contact the named program with a one-page intended-use and validation proposal; ask those exact questions in writing. Do not represent participation as regulatory clearance or a replacement for SFDA determination. [^2]

Monsha’at’s general Business Accelerators program is publicly described as free, lasting roughly 3–6 months/12 weeks, with eligibility varying by program and a process of application, document upload, evaluation, and interview. It offers mentoring, training, workspaces, grants and investor access; its public page does not provide health-tech-specific equity terms or guarantee a current healthcare cohort. [^1]

For a solo nontechnical medical-student founder, the immediate route is: form/confirm an eligible entity as required, prepare a non-patient prototype and safety case, apply to current calls rather than relying on historic accelerator names, and separately investigate Monsha’at, MNGHA/Lean partnerships, KACST, university-linked programmes where accessible, and Health Cluster innovation offices. Funding, equity, eligibility and timeline must be recorded per call because public programme pages change. [^1]

## 11.12 Rule authoring and clinical governance

The architecture should generate a clinician-facing plain-language rendering from the **same structured rule object** that runs in production. Every rendering needs: clinical purpose; in-scope/excluded population; required facts and freshness/unit/status gates; decision table; output and urgency; source/version/section; assumptions; test cases; author; reviewer; approver; effective/retirement date; and change rationale. A separate Word or PDF specification will drift from executable logic. [^6]

The evidence supports continuous user involvement and iterative design for high-impact CDS, rather than one-time approval. [^6] Governance should therefore include a named clinical content owner, a technical custodian who cannot silently alter clinical meaning, a second clinical approver for high-severity changes, formal release evidence, rollback, and post-release monitoring for no-fire/spike/override anomalies. [^6][^12]

No public source in this research set established a definitive SFDA format for clinical-logic sign-off or a blanket Arabic requirement for clinician-facing rule-review documentation. Treat both as open regulatory/provider questions. English clinician rule review may be operationally workable, but Arabic patient-facing outputs, emergency wording, consent, and communication templates should undergo qualified translation and clinical validation before use. [^10]

## 11.13 Duplicate data entry: the friction problem

### What is established

Home-health medication reconciliation entails substantial reconciliation work even where interoperable systems exist. In the observed three-agency study, 91% of patients had fewer medicines after reconciliation, 41% of medicines required changes, and interoperability reduced—but did not eliminate—changes and calls to providers. [^4] A separate simulated electronic module reduced unaddressed discrepancies versus paper but did not shorten task time. [^5]

That supports a narrow claim: Noor may reduce *unresolved safety-relevant re-entry and discrepancy work* if it presents source data, enables structured comparison, and carries unresolved tasks forward. It does **not** prove that Noor will shorten visits, nor establish why Saudi apps currently force re-entry. [^4][^5]

### Saudi integration reality and MVP response

The public Sehhaty description establishes a unified consumer health platform with appointments, health reports, medication list/search, and vital-sign follow-up, but not a third-party clinical read/write interface. [^10] Therefore, the stated Saudi “re-entry” problem may stem from any mix of missing interface access, commercial/contractual restriction, source-data incompleteness, local workflow, or technical format mismatch. Noor must confirm the cause in each provider discovery before making a competitive claim.

Start with safe, low-integration alternatives:

- verified structured import or supervised paste of a medication/lab list, retaining raw source text and mapping confidence;
- guided photo/document capture only with approved privacy/security and human verification—never autonomous clinical extraction in the MVP;
- a BP-notebook entry grid that records transcription source and measurement context;
- generated, provider-approved structured visit note/PDF as a **read-only handoff** for staff filing, not a claim of EMR write-back. [^10]

Whether staff may file a Noor-generated note in a Saudi hospital record is a provider records-governance question. Require medical-records, clinical governance, privacy, and IT approval on authorship, attestation, document type, correction, retention, and record-of-truth before deployment. Measure baseline and pilot app switches, fields re-entered, import-verification time, discrepancy resolution, note-filing time, and missed tasks. That produces an honest friction and value claim rather than assuming integration is the obstacle. [^4][^5]

## Priority implementation gates

1. **Do not build threshold logic before data validity semantics.** Implement units, source/time/status, repeat/verification, delta-review workflow, and `cannot assess safely` first.
2. **Do not promise pre-visit labs or POC testing before provider workflow and device dossiers.** Central lab/POC result provenance must be part of every rule input.
3. **Do not encode residency supervision law.** Obtain named-provider written authorization and build configurable routing until then.
4. **Treat plan amendment and patient contact as a durable state machine.** No plan change is closed merely because a note was amended or message sent.
5. **Start with a tiny hard-stop set.** Block only an unsafe action with reliable facts and a governed override route; never block emergency action or visit documentation.
6. **Assume offline and no API until measured otherwise.** Build safe local capture/evaluation and conflict-preserving sync before claiming field integration.
7. **Keep self-monitoring and adaptive forms conservative.** Preserve setting/source/density and show `insufficient data`; validate usability and capture before claiming reduced burden.
8. **Keep tenants and learning governed.** Immutable profiles, approval, testing, provenance, and human-only cross-tenant change proposals.
9. **Use the MNGHA–Monsha’at experimental environment and current accelerator calls as discovery channels, not as proof of regulatory readiness.** [^2][^1]

## Evidence gaps that should not be papered over

The sources found did **not** establish: a Saudi national resident/consultant home-prescribing co-sign rule; a sustainable supervisor visit-load benchmark; a Saudi public home-lab ordering/payment/turnaround pathway; a named POC device/cost configuration for Noor; a public Sehhaty clinical API; a Saudi field-connectivity rate specific to home visits; a universal hard-stop/override benchmark; a Saudi medication-error disclosure requirement applicable to the product; or sandbox clinical-data/regulatory-credit terms. These are material provider, regulator, and programme diligence questions—not missing citations to be filled with extrapolation. [^10][^11][^2]


[^1]: Business Accelerators | Monsha'at.

[^2]: Experimental Environment for AI In Health Sector.

[^3]: Genes et al., 2013. Validating Emergency Department Vital Signs Using a Data Quality Engine for Data Warehouse. Open Medical Informatics Journal.

[^4]: Champion et al., 2020. Getting to Complete and Accurate Medication Lists During the Transition to Home Health Care. Journal of the American Medical Directors Association.

[^5]: Gibson et al., 2016. Evaluation of an Electronic Module for Reconciling Medications in Home Health Plans of Care. Applied Clinical Informatics.

[^6]: Powers et al., 2018. Efficacy and unintended consequences of hard-stop alerts in electronic health record systems: a systematic review. J. Am. Medical Informatics Assoc.

[^7]: Randell & Yenice, 2019. Delta Checks in the clinical laboratory. Critical reviews in clinical laboratory sciences.

[^8]: Campbell et al., 2001. Self‐measurement of blood pressure: accuracy, patient preparation for readings, technique and equipment. Blood Pressure Monitoring.

[^9]: Elwenspoek et al., 2025. Evidence-based blood tests for monitoring adults with chronic kidney disease stage 3 in primary care: rapid review, routine data analysis, and consensus study. medRxiv.

[^10]: الصحة. Sehhaty» Platform.

[^11]: (MDS – G009) Guidance for Points of Care (POC) Medical Devices Manufacturing | The official website of the Saudi Food and Drug Authority.

[^12]: Justinia et al., 2021. Medication Errors and Patient Safety: Evaluation of Physicians’ Responses to Medication-Related Alert Overrides in Clinical Decision Support Systems. Acta informatica medica : AIM : journal of the Society for Medical Informatics of Bosnia & Herzegovina : casopis Drustva za medicinsku informatiku BiH.

[^13]: Mobile quality of service and market status: Saudi Arabia ...

[^14]: Nordmann, 2000. Comparison of Self-reported Home Blood Pressure Measurements with Automatically Stored Values and Ambulatory Blood Pressure. Blood Pressure.

[^15]: Download Sehhaty.

[^16]: Arabia, 2022. National research guideline for prehospital emergency medical care | Saudi Medical Journal.