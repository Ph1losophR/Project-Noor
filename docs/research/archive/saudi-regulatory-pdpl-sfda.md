> Section 2 of the research programme. Indexed in SSOT §17.

# 2. Saudi regulatory, legal, and health-system context

## Decision summary

**Treat the proposed patient-specific, rule-based chronic-disease CDS as regulated SaMD unless SFDA gives a written contrary determination.** The decisive feature is not whether a clinician may override it. SFDA’s current digital-health guidance asks whether the manufacturer intends the product to analyse or interpret medical information for diagnosis, treatment, mitigation, cure, or prevention; it gives real-time patient-data alerting and clinical decision support as examples of regulated medical-device functionality. It does **not** publish a US-FDA-style exemption based on the clinician’s ability to independently review the recommendation’s basis. [^1]

This does not prevent a low-risk, non-device first release. A separate module that only stores, displays, transmits, schedules, or documents information—without patient-specific clinical interpretation—can be outside the device definition. But a Noor feature that identifies drug–disease risk, interprets eGFR/HbA1c/BP, ranks treatments, or produces patient-specific recommendation/alert logic crosses the line described in SFDA guidance. The prudent product boundary is therefore: **workflow/data layer outside the device boundary; decision/alert/rules module inside it.** Document the separation, intended purposes, interfaces, and claims. [^1]

Health data is PDPL sensitive data. The safe default is a Saudi-hosted deployment with no routine overseas access; this is a risk-control choice, not a statement that PDPL creates an absolute localisation ban. Cross-border transfer is permitted only under statutory conditions and safeguards, while continuous/large-scale sensitive-data transfer triggers a documented transfer-risk assessment. [^2][^3]

## 2.1 SFDA: device status, scope, classification, and route

### What the current SFDA material says

SFDA’s **MDS-G27 Guidance on Digital Health Products (version 1.0, 11 August 2025)** is the most directly applicable primary guidance found. It says that qualification turns on the manufacturer-defined intended use, as conveyed in labels, technical specifications, instructions for use, and accompanying material. A standalone software product intended for a medical purpose is SaMD; educational information, general communication, and population-only analytics without individual diagnostic/treatment targeting are examples of non-SaMD. [^1]

For Noor, this produces a functional map:

- **Likely regulated SaMD:** patient-specific medication contraindication or dose flags; interpretation of laboratory/vital-sign trends; renal-risk logic; a recommendation to initiate/stop/titrate/refer; alerts requiring medical intervention; a risk score intended to guide an individual’s treatment or diagnosis. SFDA specifically names a CDSS that monitors patient data and generates alerts requiring intervention as a medical-device example. [^1]
- **Potentially non-device HIT:** patient record display, visit documentation, appointment/referral workflow, secure messaging, source-document retrieval, data-format conversion, and unanalysed lab-result display. This remains true only if the module does not add clinical interpretation. [^1]
- **General wellness is a narrow alternative, not a relabelling device.** A product may make a general wellness claim related to a chronic condition only where the claim is unrelated to diagnosis, cure, mitigation, prevention, or treatment. If clinicians prescribe/recommend it for a medical purpose and the manufacturer knows, SFDA can assess it as a device. General-wellness labelling must say in Arabic and English that it is not intended for medical purposes. [^1]

**The requested “override carve-out.”** No SFDA primary source retrieved contains the US FDA’s clinician-independent-review exclusion. MDS-G27 instead treats patient-specific analysis/interpretation and clinical alerts as the relevant boundary. A clinician override is therefore a necessary safety control and a good design feature, but **not a demonstrated route out of SFDA medical-device regulation**. This point should be resolved by a written SFDA pre-submission/qualification question before claims, architecture, or commercial timeline are fixed. [^1]

### Guidance set and likely evidence burden

If the device boundary is retained, MDS-G27 directs the manufacturer to MDMA requirements and identifies **MDS-G23 (SaMD), MDS-G10 (AI/ML medical devices), and MDS-G38 (pre-market cybersecurity)** as the relevant companion documents. [^1]

The original rule-based engine is not AI/ML merely because it uses algorithms. If later functionality learns from data, MDS-G27 says that AI/ML medical devices need validation/verification on appropriate data, data governance and traceability, explainability/limitations/bias documentation, risk management including cybersecurity/privacy, defined human oversight, and lifecycle/change controls. Build those artefacts now even for deterministic rules: rule version, clinical-source version, test cases, known exclusions, input-data quality checks, audit log, override/reason capture, release approval, rollback, and post-market signal monitoring. [^1]

MDS-G23 also shows why a “clinician in the loop” does not remove the product from scrutiny: the IMDRF framework used in the guidance categorises software by the significance of its information to the clinical decision and the seriousness/criticality of the situation. It frames lifecycle quality, clinical evaluation, transparency about limitations and assumptions, feedback, and change control as central safety controls. It is guidance rather than itself a classification rule, so do not convert its I–IV categories into an SFDA class without an SFDA classification assessment. [^4]

### Classification, conformity route, costs, timeline, and entity status

**Classification cannot be responsibly assigned from the retrieved public material alone.** It depends on the final intended purpose, the condition/clinical context, whether the output merely informs or drives management, and the risk if it is wrong or delayed. A CDS covering polypharmacy, CKD, diabetes, older/frail people, and escalation flags could span non-serious through serious conditions; the highest-risk intended-use claim may control. Do not market “decision support,” “dose recommendation,” or “risk prediction” before an SFDA determination has been mapped to the exact current classification rule and MDMA submission route. [^4]

**Conformity/MDMA.** The retrieved current digital-health guidance is unambiguous only at the high level: a product qualifying as a medical device must comply with **MDS-REQ 1, Requirements for Medical Devices Marketing Authorization**. The submission package, acceptance route, and any reliance on foreign approvals must be checked against the current MDS-REQ 1 and the applicable establishment-licensing rule at the point of application; these documents change. [^1]

**Costs and timeline.** No official publicly citable fee schedule or service-level timeline specific to a domestic SaMD/MDMA submission surfaced in this search. They should therefore not be budgeted as a known fixed number. Obtain a written estimate from SFDA/authorized representative or a Saudi regulatory adviser after intended-purpose and classification confirmation. [^1] A defensible plan has gates rather than dates: (1) written qualification/classification, (2) establishment/manufacturer eligibility, (3) QMS/technical and clinical-evidence dossier, (4) MDMA application and questions, (5) post-market and change-control operations.

**Can a student/solo entity hold registration?** The SaMD concept of manufacturer is broad—an entity responsible for design/manufacture and placing the product under its name—but establishment licensing, Saudi commercial presence, authorized representation, and accountable personnel are separate requirements. A student status is not a regulatory category that creates an exemption. Treat a Saudi legal entity/establishment strategy, quality lead, and named regulatory contact as a launch prerequisite; confirm the exact allowable arrangement in writing before spending on the route. [^1][^4]

### Product consequences

1. Separate the product into a non-device **record/workflow shell** and a versioned **clinical-rules module**.
2. Use a formal intended-purpose statement that is narrower than the roadmap. Do not call it “diagnostic,” “treatment-planning,” or “dose-adjusting” unless that claim is the intended regulated product.
3. Maintain a safety case: clinical association/source provenance, analytical validation, usability/override testing, local workflow validation, cybersecurity, complaint handling, incident log, version/rollback history, and post-market review.
4. Seek SFDA written qualification/classification feedback before a real-patient pilot. This is the single highest-value external question in this section. [^1]

## 2.2 PDPL and SDAIA: health-data operating model

### Legal roles and data scope

PDPL defines health data as data on a person’s physical, mental, or psychological condition or health services received, and makes health data sensitive data. The **controller** determines the purpose and manner of processing; the **processor** processes for and on behalf of the controller. For a Noor deployment inside a hospital/home-health provider, the provider will often be the controller for care delivery and Noor the processor; Noor becomes a controller, or a joint-controller candidate needing legal analysis, if it determines its own purposes such as product analytics, model/rule improvement, or direct outreach. Contract labels do not decide this—actual decision rights do. [^2]

### Consent and lawful operation

The law’s default is consent before processing or changing purpose, subject to listed exceptions. The legitimate-interest exception expressly excludes sensitive data; it should not be used as a shortcut for patient health data. Consent must not be forced as a condition of a service unless directly related to the processing, and it may be withdrawn. In a provider-led care pathway, separate what is necessary to deliver the contracted/legally required health service from optional product research, secondary analytics, marketing, or non-essential sharing. [^2]

Build a layered patient notice before collection: controller identity and contact, purposes, mandatory/optional fields, categories of recipients, storage/retention, transfers outside KSA, legal basis, consequences of refusal, and how to exercise access/correction/destruction rights. PDPL requires a privacy policy before collection and information on legal basis, purpose, collection/processing/storage/destruction, rights, disclosure recipients and cross-border processing. [^2]

### Health-data controls

The law requires health-data access and processing to be restricted to the minimum people and extent necessary for health services/insurance. The Implementing Regulations add safeguards against unauthorized use/misuse, role separation, processing-stage documentation and accountable persons, controller–processor contractual clauses, and minimisation to what is necessary for health services/products or insurance. [^2][^5]

For Noor, this means:

- role-based access and least privilege; no shared clinician logins;
- explicit home-health team/supervisor access roles and break-glass logging;
- patient-level audit trail for view, import, recommendation, override, and export;
- a data inventory that distinguishes clinical record, derived risk/alert, audit log, support record, and de-identified product-improvement dataset;
- retention/deletion schedules that respect provider records obligations and do not equate an account deletion request with immediate deletion of every clinical/legal record;
- data-processing agreements that forbid secondary use, subcontracting, and cross-border transfer without documented controller approval and applicable safeguards. [^5][^2]

### DPIA, DPO, breaches, and transfers

A documented impact assessment is mandatory for sensitive-data processing and other high-risk situations. Noor’s continuous patient monitoring/automated decision logic and sensitive health data give it a strong case for a DPIA even before scale. A controller with core activities based on sensitive-data processing must appoint a data-protection officer; the DPO can be an executive, employee, or external contractor. [^5]

A potentially harmful breach must be notified to SDAIA within **72 hours** of awareness; affected people must be notified without undue delay where their data/rights may be harmed. The controller must retain the report and corrective-evidence record. This must be an incident-response runbook, not a privacy-policy sentence. [^5]

**Residency/cross-border conclusion:** PDPL does *not* say “all PHI must remain in Saudi Arabia.” It allows transfer/disclosure outside KSA subject to purpose, national-security/vital-interest, adequate-protection and data-minimisation conditions, with regulatory exceptions for extreme clinical necessity. The 2025 SDAIA transfer guideline says a risk assessment is mandatory for a transfer outside the Kingdom and for continuous/large-scale sensitive-data transfer; its scope includes overseas storage, processing, collection and remote access. [^2][^3]

For a solo/early product, a Saudi-resident production environment, Saudi-based backups, and no overseas production-support access is the simplest defensible default. If any foreign cloud-region, telemetry, error-reporting, LLM, support-desk, code-log, or subcontractor access is proposed, document the exact flow, conduct the transfer assessment, minimise/segregate data, use a contract with processor clauses, and obtain current Saudi privacy counsel advice. Do not expose patient data to general-purpose external AI services by default. [^3][^2]

### SDAIA AI guidance and services

SDAIA offers an AI Service Provider Accreditation path. The public service page requires entity registration on the National Data Governance Platform, appointment of an AI officer, a product questionnaire/files, and committee review before certification. It is a compliance/ethics accreditation service; the retrieved page does not establish that it replaces SFDA MDMA for a medical AI product. [^6]

Whether the initial deterministic rule engine is “AI” for this service should be clarified with SDAIA, but the operational answer is still useful: name an accountable AI/data officer, maintain human-oversight and fairness/traceability documentation, and separate AI-service accreditation from medical-device authorization. If ML is later introduced, SFDA’s AI/ML medical-device requirements apply in addition to the PDPL framework. [^1]

## 2.3 MOH digital health, NPHIES, and integration reality

### MOH policy and certification

The sources retrieved establish a live MOH digital-health ecosystem but did not yield one universal MOH “CDS certification” for all products. The regulatory gate for patient-specific medical functionality is SFDA, while an integration with a specific MOH facility will carry that organization’s procurement, cybersecurity, identity, data-sharing, and interface-approval process. Do not assume a public application endpoint or a generic approval grants access to patient records. [^7]

The practical approach is to launch first as a provider-hosted workflow integrated by controlled import/manual verified entry or a provider-approved interface, then pursue institutional integration. Treat each facility as a separate deployment and information-governance negotiation. [^5]

### NPHIES

NPHIES is not a general national longitudinal EHR API in the material retrieved. Its public Healthcare Financial Services implementation guide describes an exchange between healthcare providers, insurers, and TPAs through the central NPHIES clearinghouse for **eligibility, authorizations, eClaims, clinical supporting information, cancellations, deferred responses, and payment**. It uses **HL7 FHIR R4.0.1** and mutual X.509-authenticated FHIR messaging. [^8][^7]

It does profile useful base resources—Patient, Practitioner, Encounter, MedicationRequest, ServiceRequest, Coverage, Claim, and others—but only for its financial-services transactions. The guide says systems need transform internal representations to FHIR for the defined exchanges; it does not require permanent internal storage as FHIR. [^7]

**Implication for Noor:** design an R4 mapping layer and use NPHIES profiles only when implementing a provider/insurer-approved eligibility, authorization, claim, or supporting-information transaction. Do **not** make NPHIES integration a P0 dependency for a clinical CDS MVP, and do not infer access to comprehensive clinical history from NPHIES. The retrieved public guide includes downloadable specification/support material, but it did not establish a publicly self-service sandbox or an access route available to an unaffiliated solo developer. Confirm provider/insurer onboarding, certificates, test environment, and contractual eligibility directly with NPHIES before budgeting integration work. [^8][^7]

## 2.4 Workforce, home healthcare, formulary, and prescribing

### Scope of practice and supervisory model

The source set did not produce a primary SCFHS/MOH document that states a universal “resident may prescribe independently at home / consultant must co-sign” rule. That absence is important: **do not encode a supervisor-sign-off model as law based on title alone.** Authority depends on the clinician’s SCFHS registration/classification, employer credentialing and privileges, care setting/health-facility license, local formulary/e-prescribing policy, and the clinical act. This must be resolved with the sponsoring home-health provider’s medical director, credentialing office, and legal/compliance team before any live prescription or treatment-change workflow. [^9]

Until then, Noor should operate as decision support only: recommendations never write a prescription, clinician identity and supervisor/escalation path are captured, and high-risk actions (initiation/titration/stop of insulin, sulfonylurea, anticoagulant, RAAS drug, diuretic, or renal-risk medication) require the service’s defined human authorization. This is a safety and governance design choice—not a claim about national co-sign law. [^1]

### Home healthcare context

MOH explicitly provides home-health services across chronic disease, including diabetes and hypertension. The published service description includes education, psychosocial support, medicines/supplies, laboratory testing, physiotherapy, IV therapy, palliative care, wound/bed-sore care, and chronic-disease care. It is not limited to older people. [^9]

Referral and eligibility are operational rather than an automatic app enrolment: an in-hospital referral must state condition and required service 72 hours before discharge; the Home Healthcare Department performs an initial assessment. For outside-hospital requests, the MOH page calls for a treatment plan, national ID, medical report of at least three months, completed request, and needs assessment. The source points to an Arabic-only Home Healthcare Guide, which should be obtained and translated by a qualified reviewer before converting it into eligibility rules. [^9]

The retrieved sources did not establish national program scale, a single private-provider regulatory pathway, or that Sehhaty/Mawid gives third parties home-health clinical-data access. Sehhaty and appointment services should be treated as patient-facing MOH services, not assumed integration endpoints. The right commercial unit is a licensed provider/home-health department with a defined cohort and clinical governance, not an unsupported “integrate with MOH apps” assumption. [^9]

### Medicines, availability, and reimbursement

The **Saudi Essential Medicines List 2023** is useful for a baseline availability configuration, but it is not proof of stock at a given facility, patient coverage, formulary restriction, prior authorization, or reimbursement. The chronic-disease subset includes metformin, gliclazide, empagliflozin, sitagliptin, pioglitazone, liraglutide and common insulin preparations; it also lists many commonly used antihypertensives. [^10]

For the executable drug layer, use **SFDA’s Saudi Drug Information system (SDI)** as the source of registered-medicine product information because it is designed as a reference for registered medicines and hosts PILs/SPCs uploaded by companies/agents. Combine it with the named provider/payer formulary and pharmacy stock/authorization rules. Do not treat the national essential list or SDI registration as a reimbursement decision. [^11]

Build a local formulary table with: ingredient, formulation, strength, SFDA registration/SPC version, provider availability, payer/coverage constraints, prior authorization, substitution policy, stock date, and source. A rule should surface “clinically preferred but unavailable/unauthorized” rather than silently proposing it. [^11][^10]

## 2.5 Liability, accountability, and language

### Medical liability and CDS

No primary Saudi authority retrieved provides a device-specific liability allocation saying who pays when a clinician follows or ignores CDS. It would be unsafe to infer that a clinician override transfers all liability, or that software is only a passive tool. In practice, exposure will turn on the health practitioner’s duty/standard of care, the provider’s clinical governance, the manufacturer’s product safety/claims and quality-system evidence, causation, contracts/insurance, and the facts of the incident. [^4]

Design for shared accountability rather than a disclaimer:

- show recommendation, source/version, patient inputs, contraindication/exclusion logic, uncertainty and data-staleness flags;
- require a clinician decision and allow override with structured reason;
- route time-critical/high-risk alerts to the service’s escalation protocol rather than a generic notification;
- preserve an immutable, time-stamped audit record of inputs, rule version, outputs, user response, supervisor involvement, and subsequent correction;
- maintain a manufacturer complaint/incident/CAPA process and a provider clinical-incident process;
- obtain Saudi health-law advice and appropriate product/professional-liability insurance before live deployment. [^4]

These controls follow the safety/lifecycle concerns identified by SFDA guidance; they do not settle legal liability. [^4]

### Arabic requirements

The only explicit language requirement established by the retrieved primary materials is SFDA’s direction that **general-wellness device** labelling must state in both Arabic and English that the device is not intended for medical purposes. [^1]

This search did not establish a universal legal requirement that all patient-facing CDS output or all clinician-facing screens must be Arabic. Nevertheless, Arabic must be treated as a release-critical usability and informed-consent requirement for a patient-facing Saudi product, with clinical and legal review of the translation. Do not use machine translation for emergency instructions, dose changes, consent, or risk explanations without expert validation. Obtain the applicable SFDA labelling/IFU requirement and provider policy before finalising language strategy. [^1]

## P0 implementation plan

1. **Freeze claims and functions.** Produce a one-page intended-use matrix marking every Noor feature as workflow, display, patient-specific analysis, alert, recommendation, or prescription-writing.
2. **Obtain SFDA written position.** Ask for qualification/classification of the patient-specific rules/alerts and the applicable MDMA route; include representative screenshots, data inputs, user, override, and escalation design.
3. **Choose the accountable deployment model.** Identify controller/processor roles with the first provider, execute health-data DPA, appoint DPO/AI officer where applicable, complete DPIA and incident/rights processes.
4. **Adopt Saudi-first hosting.** Block patient data from overseas analytics/AI/support by default; document any exception under PDPL transfer assessment.
5. **Make human authority explicit.** Implement provider-approved sign-off/escalation paths; no autonomous prescribing, no silent medication changes, and no dependency on an assumed resident scope.
6. **Build the local medication configuration.** Ingest SDI/SPC and provider formulary/coverage fields; bind each rule to a current source/product version.
7. **Treat NPHIES as later integration.** Implement an FHIR R4 adapter capability, but do not represent it as a general EHR integration or require it for MVP.
8. **Set a release gate.** No real-patient use until SFDA status, provider clinical governance, PDPL DPIA/DPA, incident response, Arabic patient content, and audit/override records are complete. [^1][^5]

## Remaining primary-source questions to close before launch

- Written SFDA qualification/classification and current MDMA/establishment route, fees, service levels, and Saudi representative/entity requirements.
- Exact SCFHS/employer privileging and prescribing/supervision rules for the sponsoring home-health service.
- MOH/provider-specific digital-health/cybersecurity/data-sharing approval and any integration prerequisites.
- NPHIES onboarding, certificate, test/sandbox, and eligibility terms for the target provider/insurer—not generic assumptions.
- Current provider and payer formulary/reimbursement/stock rules, which cannot be inferred from the essential list or product registration.
- Applicable medical-liability interpretation and insurance structure for provider, supervising clinician, and manufacturer.
- SFDA patient-facing labelling/IFU language requirements beyond the general-wellness statement, and provider-approved Arabic clinical content. [^1]

This is a regulatory and operational research briefing, not Saudi legal advice or an SFDA determination. The unresolved points are material design gates, not paperwork to postpone. [^1][^2]


[^1]: Guidance on Digital Health Products.

[^2]: Personal Data English V2-23April2023- Reviewed-.

[^3]: Risk Assessment Guideline for Transferring.

[^4]: MDS-G23 Guidance on Software as a Medical Device.

[^5]: Alsowayan. ExecutiveRegulationsEn.

[^6]: AI Service Provider Accreditation.

[^7]: http://hl7.org/fhir. Background - Healthcare Financial Services IG Edition 1 v1.0.0.

[^8]: http://hl7.org/fhir. Home - Healthcare Financial Services IG Edition 1 v1.0.0.

[^9]: الصحة. Home Health Care Services.

[^10]: Essential Medicines List of Saudi Arabia 2023.

[^11]: Saudi Drugs information system (SDI) | The official website of the Saudi Food and Drug Authority.