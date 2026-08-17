> Section 5 of the research programme. Indexed in SSOT §17.

# 5. Interoperability and integration

## Decision

Build Noor as an **R4-native clinical application with a versioned canonical data model and adapter boundary**, not as an “integrate with any EMR” product. The first deployable integration should support: (1) verified manual/import workflows, (2) a provider-specific FHIR R4 adapter where available, and (3) a provider-specific HL7 v2/file adapter where FHIR is not exposed. Keep every adapter read-first; do not write prescriptions, orders, or source-record data in the MVP. [^1]

Saudi Arabia’s published NPHIES Healthcare Financial Services guide is based on **FHIR R4.0.1** and uses FHIR messages for provider–insurer/TPA financial and administrative transactions through the NPHIES clearinghouse. It requires transformation *for those transactions*, not that a hospital persist its whole clinical record in FHIR. NPHIES is therefore a useful R4 compatibility anchor—not evidence of a national longitudinal-EHR API or of a third-party clinical-CDS integration channel. [^2]

The following architecture recommendations intentionally limit scope to interfaces that can be verified and clinically governed. [^2][^1]

**Product consequence:** Noor should advertise “provider-approved integration” rather than “connects to any EMR.” Its integration roadmap is a sequence of contracted, tested interface deployments; the customer’s EMR, security policy, available data, and permitted workflow trigger decide what is possible. [^1]

## 1. FHIR version policy: R4 now, R5 only behind an adapter

### Why R4 is the production baseline

FHIR R5 is the current published core release, but R5 remains an STU release and FHIR resources have differing maturity and change risk. HL7 explicitly notes that the pace of R5 adoption is uncertain, while R4 is the version used by both the current NPHIES financial-services implementation guide and the current IPS guide. [^3][^2][^4]

**Adopt:** JSON FHIR R4/R4.0.1 at external Noor interfaces; the NPHIES package/version only where implementing an NPHIES transaction. Require every connection to expose a `CapabilityStatement`, its `fhirVersion`, supported resource interactions, search parameters, profiles, terminology bindings, authentication method, and rate/timeout limits before Noor makes a clinical claim about an interface. FHIR itself identifies `CapabilityStatement`, `StructureDefinition`, and `ImplementationGuide` as places where version can be declared. [^3]

The integration contract below operationalizes those version, conformance, and data-provenance requirements. [^2]

**Do not:** silently treat R4, R4B, and R5 payloads as interchangeable. Trial-use content can change incompatibly across releases; version conversion can lose semantic detail. Preserve the received payload and version; convert through an explicit adapter with a documented loss report and test corpus. [^3]

### Required external contract

For every provider connection, create a signed interface profile containing:

- FHIR release/package and named profiles; source EHR/vendor/version; base URL or transport; tenant/environment.
- Authentication, authorization scopes, JWT issuer/JWK rotation, mTLS requirement, and token lifetime.
- Supported read/search/write operations; pagination, `_include`, date semantics, time-zone convention, error behavior, rate limits, and outage behavior.
- Resource-level data availability and freshness: e.g., whether medications are orders, reconciled patient reports, dispensing events, or all three; whether laboratory results carry LOINC/UCUM/specimen/status; and whether allergies are coded and verified.
- Provenance: source system, source resource ID/version, author/recorder, effective time, received time, and terminology release.
- A clinical acceptance test pack: abnormal renal function, ambiguous medication, duplicate trade name, hemolysed potassium, stale vital sign, inactive allergy, missing unit, and a patient with no known medications/allergies. [^2][^1]

NPHIES’s own guide makes the core point: resource profiles must be followed for a given use case, and an organization may retain its own internal format while translating only the exchange payload. [^2]

## 2. Noor R4 profile set

The resources in the checklist are the right starting set, but they need **purpose-specific profiles** rather than generic resource storage. Profile only what Noor needs for safe data capture/evaluation; do not create an unofficial national profile by accident. [^2][^5]

The tables specify Noor’s minimum local constraints, which must be reconciled with each provider’s approved interface profile. [^2]

### Patient and care context

| Resource | Noor role | Minimum safe constraints |
|---|---|---|
| `Patient` | Identity, demographic and contact context | Retain source identifiers and assigning system; administrative gender, birth date, preferred language, deceased status where available. Do not rely on a display name as an identity key. |
| `Encounter` | The clinical/home-visit context for data and decisions | Class/type, status, period, service location, participant, provider organization, and encounter source. A home visit must be distinguishable from clinic, ED, telephone, and patient-reported context. |
| `Practitioner` + `PractitionerRole` | Authorship, authority, and routing | Source identity, organization, role/specialty, active status. Noor must not infer prescribing/supervisory authority from a text title alone. |
| `CarePlan` | Human-authored longitudinal plan and goals | Status, intent, subject, period, contributors, goal/action references, and source/version. It is not a substitute for a rule audit trail. | [^5]
| `ServiceRequest` | Requested lab, referral, monitoring, or service | Status/intent, subject, authored time, requester, performer, order code, priority, reason, and linked results. |

### Clinical facts and results

| Resource | Noor role | Minimum safe constraints |
|---|---|---|
| `Condition` | Problem list and clinically relevant status | Coded condition plus clinical/verification status, onset/abatement where known, recorder, encounter and asserted date. Separate source assertion from Noor’s derived risk label. |
| `Observation` | Vitals, laboratory values, scores, derived calculations | Code, value, UCUM unit, status, effective time, issued time, specimen/method/device, interpretation/reference range, performer, encounter and provenance. Reject clinical-rule use of an unqualified number. |
| `DiagnosticReport` | Laboratory/radiology report envelope | Status, code, effective/issued time, performer, conclusion, and references to the component `Observation` resources. Do not replace component results with report narrative. | [^5]
| `AllergyIntolerance` | Allergy/intolerance safety input | Clinical and verification status, type/category, code, reaction manifestation, severity, criticality, recorded date/recorder, and source. “No known allergy” must be an explicit, source-supported state, not an absence inference. |

### Medicines and decisions

| Resource | Noor role | Minimum safe constraints |
|---|---|---|
| `MedicationRequest` | Prescribed/ordered medicine | Status/intent, authored time, requester, medication concept/product mapping, dose/route/frequency, dispense instructions, reason, substitution, and link to the source order. It represents an order—not proof of patient use. |
| `MedicationStatement` | Reconciled/patient-reported current use | Status, effective period/date, information source, medication concept/product mapping, dosage and reason. It must remain distinct from `MedicationRequest`; this distinction is central to reconciliation. |
| `RiskAssessment` | A bounded risk-model output | Subject, occurrence time, method/version, basis inputs, prediction/outcome/probability when applicable, and mitigation. Use only for an actual risk-model result; do not overload it with every alert. |
| `DetectedIssue` | A patient-specific medication/clinical safety finding | Status, identified time, implicated resources, coded issue category, severity, evidence/detail, author, and source rule/version. Use it as an auditable finding; it must not be silently written into a provider record. |
| `Flag` | A persistent, user-visible warning | Status, category, code, period, author and subject. Reserve for clinically governed, durable flags—not transient rule output. | [^5]

The profile tables above are designed to preserve those separations and to prevent category errors during rule evaluation. [^5]

This model aligns with the IPS’s separation of problems, allergies/intolerances, medicines, diagnostic results, plan of care, vital signs, and alerts. IPS explicitly represents medications through `MedicationStatement` or `MedicationRequest`, results through `Observation`/`DiagnosticReport`, and alerts through `Flag`; it is a useful interchange minimum, not a complete chronic-disease record or Noor’s internal safety model. [^5]

### Cross-cutting profiles Noor must add

1. **Provenance and raw source:** retain original source identifiers/display strings/payload references, ingestion time, mapping status/version, and an immutable relationship between the Noor normalized entity and incoming source item.
2. **Data-quality gate:** add a local, explicitly named profile/extension or a parallel data-quality record for missing unit, unknown mapping, invalid date, contradictory status, result correction, staleness, and manual verification. Never encode clinical uncertainty as a normal value. [^1]
3. **Rule-execution record:** record rule ID/version, guideline/source version, knowledge-base version, input resource IDs/versions, evaluation time, output, severity, surfaced/not surfaced, user action, override/reason, and responsible clinician. `DetectedIssue` is a clinical finding; the full execution audit should not be reduced to it.
4. **Saudi terminology binding:** bind Noor’s incoming/outgoing concepts to the LOINC, UCUM, SNOMED CT, ICD-10-AM/NPHIES, and local SFDA product mappings established in the terminology workstream; terminology version must travel with the result.

## 3. CDS Hooks: excellent adapter target, wrong MVP dependency

CDS Hooks describes a REST/JSON interaction in which an EHR invokes a registered CDS service from workflow events. Its standard model is exactly the *shape* Noor needs: the EHR supplies workflow context plus optional FHIR prefetch or an access token; the service returns cards that can carry information, one selectable suggestion, or a link to a deeper app. [^1]

### The hooks relevant to Noor

- **`patient-view`:** evaluate a patient when the chart/summary opens. Use for non-interruptive reconciliation prompts, overdue monitoring, documented risk, and “review before visit” summaries. It should not spray all possible chronic-care reminders.
- **`order-select` / `order-sign`:** evaluate a proposed order set or the moment before signature, if the host EHR implements the current hook. Use for drug–drug, drug–disease, allergy, renal-dose, duplicate therapy, and monitoring checks. Do not assume either exists merely because the EHR has FHIR.
- **`medication-prescribe` / `order-review`:** earlier CDS Hooks material used these names; a partner’s implemented CDS Hooks version and catalog must be discovered and tested rather than inferred from marketing. The standard has evolved, which is another reason not to hard-code hook names before conformance testing. [^6]

### Card and suggestion policy

- Return a concise `summary`, evidence/provenance in `detail`, severity/indicator, and a source label/link. Cards distinguish `info`, `warning`, and `hard-stop`; Noor should use hard stops only for the narrow, provider-approved cases where a workflow must not proceed. [^1]
- Make suggestions **non-autonomous**. The EHR is responsible for display and application behavior; a suggestion can propose FHIR create/update/delete actions, but Noor’s first release should use a “review in Noor” SMART/deep link rather than a direct medication/order mutation. [^1]
- Treat the card source as patient-safety data: show guideline/label name, rule version, patient-specific input snapshot/time, exclusions, and a link to the full reasoning. The CDS Hooks source field identifies the guidance source, but it is too small by itself for Noor’s legal/clinical audit requirements. [^1]

### Prefetch and freshness

Use a narrow prefetch contract—patient demographics, active/reconciled medication resources, allergies, relevant conditions, recent renal/electrolyte/diabetes observations, and encounter—rather than a whole chart. The CDS Hooks specifications say that stale clinical data is a safety threat; prefetch is optional, may be only partly honored, and the service must recognize what it did not receive. [^1]

For each rule, declare a data-requirement manifest: resource/profile, code/value-set, look-back interval, freshness maximum, source preference, minimum completeness, and behavior if unavailable. Example: an eGFR-sensitive medication rule needs a recent, final, unit-validated eGFR/creatinine result with equation provenance; if it is absent, Noor returns “cannot safely evaluate—obtain/reconcile result,” not an invented recommendation. [^1]

### Feedback and override: correct the checklist assumption

**The CDS Hooks feedback/analytics mechanism is not an override-reason standard.** The classic Card model can notify a service that a user clicked a suggestion carrying a UUID, and the notification body is empty. That supports suggestion-selection telemetry, not a structured clinical rationale for accepting, rejecting, deferring, or overriding a recommendation. [^1]

Noor should implement override capture in its own review workflow—preferably a SMART app launched from a card or a provider-approved embedded/deep-link workflow—and store it in Noor’s audit record. [^1] If the host permits write-back, send a governed FHIR representation such as a task/communication/note or a locally profiled `DetectedIssue` disposition **only after the provider defines the record-of-truth and retention policy**. Do not use analytics clicks as evidence of clinician agreement, outcome, or a legally adequate override.

### Native implementation vs later adapter

Implement a small CDS Hooks facade **after** the internal evaluation API and audit model are stable, not before. The facade is low-value until a named partner confirms support for the selected hooks, authentication and prefetch. It nevertheless protects Noor from custom one-off EHR APIs: one internal `evaluate(context, facts, requested_actions)` call can back a Noor UI, scheduled review, REST integration, and later CDS Hooks adapter. [^1][^6]

CDS Hooks is not plug-and-play: the standard leaves provider/EHR vetting, data provision, and service registration to local arrangements. It expects registered clients, least-necessary data access, TLS/JWT trust, and provider/vendor agreement on prefetch and access scope. [^1]

## 4. CQL and FHIR Clinical Reasoning: adopt the information model, defer CQL as the primary runtime

FHIR Clinical Reasoning provides a serious standard framework for sharing and evaluating knowledge artifacts. It defines `Library`, `PlanDefinition`, `ActivityDefinition`, `GuidanceResponse`, and expression support, and identifies CQL/FHIRPath as logic languages. `PlanDefinition` can represent rules, order sets, and protocols; `ActivityDefinition` defines reusable activities. [^7]

CQL is not inherently a “standards tarpit.” It is a clinically focused query language for CDS, quality measurement, computable guidelines, and research eligibility; the current CQL-with-FHIR guide is R4-based and has an established translator, JavaScript execution framework, tooling, and server-side options. [^8][^9]

But it is the wrong **primary first runtime** for a solo Noor product because Noor’s early work is local-source integration, Saudi product normalization, data-quality gates, explainable deterministic recommendations, and clinical governance—not cross-organization knowledge-artifact distribution or electronic quality-measure reporting. CQL adds an authoring/translation (CQL→ELM), terminology/value-set, model-info, FHIR-version, test-fixture, and execution-engine stack. Its standard resources are still evolving: the R5 Clinical Reasoning module is informative and explicitly describes continuing maturation toward normative status for key resources. [^9][^7]

### Recommended rule architecture

**Phase 1: internal deterministic rule package.** Use a typed, versioned rule representation in the application’s primary language (Python is acceptable), with a declarative data-requirement manifest, pure evaluation functions, test cases, explanation templates, source citations, release approvals, and structured outputs. [^7] Maintain a direct mapping between each rule and a guideline/label clause; prohibit free-text-only input.

**Phase 2: FHIR-shaped knowledge artifacts.** Store rule metadata that can map to `Library`/`PlanDefinition`/`ActivityDefinition`: canonical URL, semantic version, status, effective period, author/approver, evidence/source, dependencies, data requirements, expected actions, and test package. Use FHIRPath selectively for simple navigation/validation, not as a general-purpose business-rule language. [^7]

**Phase 3: CQL pilot only when a named use case requires portable computable logic.** Good triggers: sharing with a partner that already consumes CQL; formal quality reporting; multiple rule authors needing a common executable language; or a need to reuse one definition across a measure and point-of-care rule. Pilot a bounded rule family, compile it in CI, compare CQL/ELM output against the canonical internal evaluator on the same R4 fixtures, and retain one clinical owner for semantic sign-off. [^9][^8]

**Do not** make `PlanDefinition`/`ActivityDefinition` a requirement for every internal rule before there is an interoperating consumer. That would front-load complexity without solving Noor’s immediate data-quality and deployment constraints. [^7]

## 5. Engines and reusable components

| Option | What it is | Fit for Noor | Decision |
|---|---|---|---|
| **Custom typed rule service** | Deterministic application rules plus a strict FHIR adapter and a test/audit harness | Best fit for early-stage, Saudi-localized rules and data-quality gating; fastest to debug and version | **Use for MVP** |
| **CQL translator + JavaScript execution framework** | Open-source CQL-to-ELM translator and JS engine; a FHIR data provider is documented | Viable experimental sidecar when portable CQL becomes necessary; requires strong CQL/ELM and terminology discipline | **Pilot later, not core MVP** [^9] |
| **CQF Ruler** | HAPI FHIR JPA-server plugins that implement FHIR Clinical Reasoning, evaluation, knowledge repository and point-of-care recommendations | Strong reference platform for an R4/FHIR/CQL-heavy deployment, but Java/HAPI-server operational weight is disproportionate for a solo MVP | **Learn from / consider for enterprise phase** [^10] |
| **OpenCDS** | Older CDS framework with vMR/SOAP roots; supports FHIR/REST and Drools plug-ins | Useful historically, but its own functional introduction is dated 2017 and foregrounds vMR/SOAP/Drools 5; poor greenfield default | **Do not select as core platform** [^11] |
| **Drools/KIE** | Mature Java rule-engine family | Powerful where a Java rule-authoring organization already exists; adds a separate language/runtime and rule-network debugging burden | **Avoid for MVP; reassess only for scale/complex rule authoring** |
| **Medplum / generic FHIR platforms** | FHIR-centric application/back-end platforms | Potential acceleration only after Saudi hosting, security, data residency, tenant isolation, licensing, and local integration fit are verified; not a replacement for rule governance | **Evaluate commercially, do not make architecture depend on it** |

The official CQL reference-implementation list documents JavaScript and JVM/Kotlin-oriented tooling and CQF Ruler/server options; it does **not** identify a maintained Python CQL execution engine. Treat Python as the host for Noor’s deterministic rule service, not as a presumed CQL runtime. [^9]

## 6. IPS: support as an export/import boundary, not the internal database

The International Patient Summary is an R4-based, minimal, non-exhaustive, specialty-agnostic extract intended primarily for unplanned cross-border care, though it can support local/planned-care uses. [^4]

For Noor, IPS is valuable in three bounded cases:

1. **Clinician-curated handover/export:** an agreed summary for referral, ED presentation, travel, or cross-provider home-care handover.
2. **Import/reconciliation starter:** consume an IPS as a source document, then reconcile every condition, allergy, medication, and key result into Noor’s source-preserving model.
3. **Interoperability contract:** use IPS section/profile expectations as a check that a provider-export contains problems, allergies, medications, results, plan, vital signs and alerts. [^5]

IPS is insufficient as Noor’s native chronic-care record because it is intentionally minimal and does not supply Noor’s local medication-product mapping, rule versions, data-quality states, home-visit measurement metadata, detailed reconciliation/override history, or Saudi provider-specific governance. A valid IPS may omit condition-specific material; therefore absence in IPS must not be interpreted as clinical absence. [^4][^5]

## 7. Saudi EMR integration reality

### What public material establishes

- NPHIES gives a concrete national FHIR R4.0.1 implementation guide, but for healthcare financial services. It describes eligibility, authorization, claims, supporting information and payment exchanges—not a public general clinical-record API. Its public capability statement supports JSON and a `$process-message` operation with national-authority-issued X.509 mutual authentication. [^2][^12]
- Historical Saudi eHealth standards and IHE activity show that interoperability work exists, but public documents alone do not prove live third-party FHIR, SMART, CDS Hooks, or bulk-data access at a particular hospital.
- A vendor having FHIR/SMART documentation elsewhere does not establish that its Saudi installation exposes the relevant endpoint, scopes, sandbox, hook catalog, or third-party onboarding path.

### Practical expectation by interface type

| Integration surface | What it can provide | Main Noor risk/control |
|---|---|---|
| Provider-exposed FHIR R4 API | Best case for patient, problem, allergy, medication, result, encounter and practitioner reads; possibly SMART launch | Confirm named profiles/searches/scopes and test real data completeness; “FHIR API” alone does not mean CDS Hooks or write access. |
| SMART on FHIR launch | Contextual, user-facing Noor app inside a supporting EHR | Technically plausible because SMART passes user/patient launch context and uses OAuth 2.0, but requires the local EHR’s authorization server, app registration, scopes, and vendor/provider approval. [^13] |
| CDS Hooks | Synchronous in-workflow cards/actions | Highest workflow fit but lowest assumption: requires a supporting EHR hook catalog plus low-latency invocation, service registration, prefetch/access-token negotiation and safety vetting. |
| HL7 v2 feed/interface engine | Often the realistic route for ADT, orders, results and some medication events where a hospital does not expose FHIR | Build a provider-specific parser/mapping; v2 messages do not guarantee reconciled medication, verified allergy, or complete outpatient history. |
| Document/flat-file export | Lowest-barrier starting point for medication lists, labs, encounter summaries | Treat as reconciliation input; retain import provenance and require data-quality checks before decision support. |
| NPHIES | Financial/administrative exchange and specified supporting information | Later, only with eligible provider/insurer onboarding; not a clinical-history dependency. [^2][^12] |

### EMR discovery protocol before sales claims

For each target provider, obtain—not just ask about—the following:

1. Vendor/product/version and deployed modules; whether it is hosted, on-premise, or regional cloud.
2. A `CapabilityStatement` or signed interface specification; sample de-identified payloads; named profiles and terminology policy.
3. Read access by resource, search capability, refresh latency and result correction behavior.
4. Whether a SMART authorization server exists; supported launch types; client-registration path; test tenant; scopes; auditing expectations.
5. Whether CDS Hooks exists; supported version/catalog; invocation latency SLA; prefetch limits; card rendering; suggestion/write behavior; feedback/analytics support; JWT/mTLS configuration.
6. HL7 v2/interface-engine options where FHIR is unavailable; exact message/event feeds and field ownership.
7. Contractual data-processing/security review, Saudi hosting/access constraints, penetration-testing requirements, incident reporting, change approvals, and service desk.
8. Named clinical owner who will validate mapped labs, medication status semantics, allergy data and alert workflow.

Noor should price and schedule each integration only after this discovery produces an accepted interface profile and a test environment. An integration that returns displayable data but lacks coded units, medication reconciliation, freshness, or source provenance is a **viewer integration**, not a safe CDS integration. [^1]

## 8. SMART on FHIR: a credible later distribution channel, not a Saudi market assumption

SMART App Launch defines OAuth 2.0-based patterns for a user-facing app to authenticate/authorize against a FHIR system and receive launch context such as the selected patient; SMART Backend Services serves headless/automated clients. [^13]

**Recommended sequence:**

- Design Noor’s frontend so it can accept a signed launch-context envelope (issuer, patient, encounter, practitioner, org, FHIR endpoint, scopes, expiry) while also working as a provider-hosted standalone application.
- Implement SMART authorization code launch only after a first provider confirms its FHIR server, authorization server, registration process and approved scopes.
- Use SMART app launch for complex review/override and provenance display. Use CDS Hooks only to invoke a short card and launch Noor; do not put a multi-step chronic-care plan into a card.
- Do not assume marketplace-style distribution. A valid SMART app still needs each hospital/vendor’s clinical, security, privacy, and application-registration approval.

CDS Hooks itself recognizes the architectural link: a card can link to a SMART app, while automated hooks require a short-lived service token scoped to the service/current user; direct FHIR access remains controlled by the EHR. [^1]

## 9. Recommended build order and release gates

### Build order

1. **Canonical clinical model and provenance first.** Implement the profile set above internally, terminology mapping, source preservation, data-quality gates, and immutable rule audit. Keep FHIR serialization at the boundary.
2. **Read-only import path.** Start with a provider-approved import/verified-entry workflow. Demonstrate clinical safety without assuming an EMR integration.
3. **R4 adapter kit.** Build JSON validation, CapabilityStatement inspection, resource mapping, terminology/unit validation, pagination/error handling, and a simulator containing adverse data cases.
4. **One provider-specific interface.** Prefer read-only FHIR R4; otherwise use an HL7 v2/file adapter. Validate mapping with the provider’s pathologist/pharmacist/clinical lead and run user acceptance tests.
5. **Standalone clinician review workflow.** Capture acknowledgement, accept/reject/defer/override reasons, escalation, and follow-up—not analytics clicks.
6. **SMART launch pilot.** Only if that provider supports it.
7. **CDS Hooks facade.** Only once that provider has confirmed catalog/support and Noor can satisfy its latency/security/audit requirements.
8. **CQL/Clinical Reasoning pilot.** Only for a portable-logic or measure-reporting use case with an identified consuming partner.
9. **IPS export/import.** Add after mapping/reconciliation is robust; it is a valuable handover capability but not a substitute for step 1.

### Non-negotiable release gates

- A named provider has accepted the exact interface scope, security model, data-processing arrangement and test plan.
- Every data item used in a rule has code/unit/status/time/provenance requirements and an explicit behavior when those requirements fail.
- A clinician/pharmacist has validated source semantics for medication orders versus statements, allergy status, laboratory final/corrected values, and home-visit context.
- The integration has an outage/staleness policy: fail closed for automated recommendation, show last-sync time, and preserve the source record.
- No Noor write-back, order mutation, or prescription workflow exists without explicit clinical governance, provider authorization, rollback/reconciliation design, and regulator/provider approval.
- SMART/CDS Hooks token handling, JWT validation, TLS, narrow scopes, audit logs and key-rotation procedures pass security review. CDS Hooks explicitly treats data interception, impersonation, dangerous suggestions, and stale data as safety/security risks. [^1]

## Bottom-line architecture

Noor should be **FHIR-literate rather than FHIR-dependent**: R4 at exchange boundaries; a strict normalized internal model; controlled adapter per provider; read-first integration; a standalone review/override workflow; and portable standards (IPS, SMART, CDS Hooks, CQL) introduced only when a real partner can consume them. This gives Noor a credible path from home-health workflow to EHR-embedded CDS without making unverified hospital integration its product premise.


[^1]: 1.0 - CDS Hooks.

[^2]: http://hl7.org/fhir. Background - Healthcare Financial Services IG Edition 1 v1.0.0.

[^3]: http://hl7.org/fhir. Versions - FHIR v5.0.0.

[^4]: http://hl7.org/fhir. Home - International Patient Summary Implementation Guide v2.0.1.

[^5]: http://hl7.org/fhir. Structure of the International Patient Summary - International Patient Summary Implementation Guide v2.0.1.

[^6]: API Reference.

[^7]: http://hl7.org/fhir. Clinicalreasoning-module - FHIR v5.0.0.

[^8]: http://hl7.org/fhir. Home - Using CQL With FHIR v2.0.0.

[^9]: http://hl7.org/fhir. Appendix C - Reference Implementations - Clinical Quality Language Specification v2.0.0.

[^10]: CQF Ruler | eCQI Resource Center.

[^11]: OpenCDS Functional Introduction - OpenCDS - OpenCDS Wiki.

[^12]: http://hl7.org/fhir. CapabilityStatement - nphies - Healthcare Financial Services IG Edition 1 v1.0.0.

[^13]: HL7 FHIR Implementation Guide: SMART App Launch v2.1.0.