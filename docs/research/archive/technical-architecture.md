> Section 9 of the research programme. Indexed in SSOT §17.

# 9. Technical architecture references

## Decision

Build Noor’s MVP as a **clinician-readable, declarative rule catalogue evaluated by a small deterministic Python service**. Keep the execution adapter separate from the clinical content; prohibit rule-side effects; persist immutable evaluation records; and expose a review view that renders the same versioned rule content and evidence citations used at runtime. Do **not** make a generic inference engine, Drools, or CQL the initial runtime dependency. This is the best fit for a product whose near-term risks are clinical-content traceability, data quality, and review capacity—not high-throughput event correlation. The broader evidence base does not identify a universally superior CDS technology; a 2022 systematic review found few evaluated rule-based systems, limited standards/EHR integration, and no RCTs among its 15 outcome-evaluated studies. [^1]

This section complements the prior interoperability architecture: use FHIR R4 at exchange boundaries, but do not force the internal rule engine to execute directly against raw FHIR. Convert verified source data into a typed clinical fact snapshot; retain source-resource/version references; then evaluate pure rules against that snapshot. The substantial engineering issue is not merely choosing a rule engine: clinical data must be mapped consistently from heterogeneous sources to rule variables. [^2]

## 1. Rule-engine choice

### Recommended architecture: constrained declarative catalogue + deterministic evaluator

A Noor rule should be a versioned data object—not an opaque Python function—with: (1) a stable rule ID and semantic version; (2) scope and exclusion criteria; (3) typed input definitions; (4) an explicit temporal/data-quality requirement for each input; (5) decision tables or simple `all/any/not` predicates; (6) a bounded output template and severity; (7) citations to guideline or label clauses; (8) clinical author, approver, effective dates and release status; and (9) test fixtures. The evaluator should expose only a small approved operator vocabulary—comparisons, membership in versioned value sets, date/window functions, and explicitly named aggregations. It should return `triggered`, `not_triggered`, or `indeterminate` rather than silently treating absent or unsafe-to-use data as a negative. [^3]

This is deliberately less expressive than general Python. It makes a clinician review the actual decision conditions, makes a test author enumerate boundaries, and prevents an author from concealing clinical policy in helper functions. The natural-language advantage of a dedicated knowledge syntax is real: in a comparison of Drools with Arden Syntax, the authors judged Arden’s medical-logic representation more understandable because it resembles natural language, while Drools’ Java-like syntax was less so. [^4] Noor can obtain most of that reviewability without adopting Arden or its surrounding platform by rendering structured rule data into a clinician-facing decision table and plain-language explanation.

### Options evaluated

**Hand-rolled Python conditionals — reject as the *content* format; retain only for the evaluator.** Pure functions, typed facts, dependency injection, unit tests, and code review are excellent implementation primitives. But threshold changes would be code changes; clinical review would require reading programming control flow; and a source citation can easily drift from the line that implements it. Use Python to validate schemas, compile approved predicates, calculate date windows, and persist evidence—not to hold the rule catalogue itself. [^1]

**`business-rules` — useful design inspiration, not a safe unmodified clinical engine.** It stores rules as JSON over declared variables, operators and actions, and its stated purpose is to let non-programmers configure logic without code. [^5] That is closer to Noor’s hard requirement than Python conditionals. Its built-in model, however, is a generic business-automation model in which rules invoke actions, including persistence-changing actions in the example. [^5] Noor should borrow the restricted JSON/decision-table concept but replace generic actions with non-autonomous clinical outputs (`review`, `task`, `escalate`, `cannot-assess`) and add mandatory provenance, approval, terminology and temporal semantics. Do not give clinicians an unrestricted production rule editor.

**`durable_rules` — do not select for the MVP.** It is a Python-accessible event/rules framework with forward-chaining Rete evaluation, facts/events, statecharts, and optional external state storage. [^6] Those features are appropriate for high-volume event correlation and long-running workflow state, but Noor’s first rules are mostly bounded patient-snapshot checks. Its Python rules are still embedded in decorators and consequent functions. That fails the strong clinician-review criterion and introduces inference-order/state debugging that is unnecessary for renal dosing, reconciliation, missing-monitoring, or contraindication checks. Reconsider only if a later, independently governed workflow genuinely needs state-machine/event reasoning.

**Drools through a separate service — defer.** Drools can support large rule sets and separation from application deployment; the comparative study found its use case could be implemented efficiently, in part because it provides rich features. [^4] But it introduces a Java operational boundary and a programming-like rule language, neither of which makes a solo, non-coding clinical-content owner safer. A service boundary does not itself solve provenance, terminology, source mapping, or clinical approval. It becomes reasonable only if Noor acquires a Java-capable delivery team and a substantial rule-authoring programme that needs a mature production-rule platform.

**CQL — retain as a future interoperability lane, not an MVP dependency.** CQL is explicitly intended for CDS, quality reporting, computable guidelines, trial eligibility, and related FHIR use cases. [^7] The current CQL-with-FHIR guide is R4-based but Trial Use, includes an authoring/integration/ELM/terminology stack, and targets specialist authors and integrators. [^7] It is therefore a sensible export/pilot target when a named provider or programme requires portable computable logic, not a shortcut around Noor’s immediate clinical-governance work. If adopted later, compile CQL to ELM in the release pipeline, run the same golden fixtures against CQL and Noor’s canonical evaluator, and designate a clinical owner for each semantic change.

### Practical recommendation

Implement the rule catalogue in human-readable YAML or JSON with a strict schema, store it in version control, and compile/validate it before release. Give clinicians a generated review page—not raw files—that shows the rule title, eligibility, exclusions, inputs and freshness constraints, decision table, output language, citations, effective dates, test cases, change rationale and approval signatures. The review artefact must be generated from the executable object; maintaining a separate Word/PDF description invites divergence. [^8]

## 2. Making rules genuinely clinician-reviewable

A reviewable rule is not merely one with comments. It should answer, on one screen or expandable structured page:

1. **Who is in scope?** Inclusion and exclusion logic, with unknown/ambiguous status made visible.
2. **What facts qualify?** Data elements in clinical names, codes/value sets, units, source preference, effective-time requirement and maximum age.
3. **What exact decision logic applies?** A decision table with named branches and explicit precedence. No hidden helper calculation or default.
4. **What happens?** Non-autonomous recommendation/task/escalation, severity, responsible role, expiry, and reason an evaluation becomes indeterminate.
5. **Why is it justified?** Guideline/label publisher, version, section/clause, local-policy rationale, and the source excerpt or link where licensing permits.
6. **Who approved this release?** Author, clinical reviewer, date, status and next review date.
7. **What proves it works as encoded?** Happy-path, boundary, exclusion, stale/missing, unit and terminology fixtures plus expected output. [^8]

Use **decision tables** for most Noor rules: each row is a mutually intelligible clinical scenario, each column a named fact, and every rule outcome is explicit. For example, a renal-dose rule should not say “eGFR low”; it should declare the eGFR code/unit/equation/status, the agent/product mapping, dose, timing, allowed renal thresholds, whether dialysis applies, and its behaviour when the newest result is preliminary, stale or discordant. This directly mitigates the general CDS integration problem of mapping diverse data sources into rule variables. [^2]

Use a two-stage authoring workflow: a clinician drafts/reviews the structured logic in a controlled staging environment; a technical custodian maps only approved clinical terms to data sources and may not alter clinical meaning; then a second clinician approves the executable release and test evidence. The product must enforce four-eyes approval for new high-severity rules and material threshold/logic changes. A “non-programmer editable” interface should expose only allowed concepts, enumerated terminology and approved operators—not arbitrary expressions. [^1]

## 3. Versioning, provenance, and reproducibility

### Separate four things that are often conflated

- **Clinical-source version:** guideline/label/local policy identity, publication/version, section/clause, retrieval date and applicable jurisdiction.
- **Knowledge version:** Noor rule package semantic version, rule ID, content hash, terminology/value-set release, author/reviewer/approver and change rationale.
- **Runtime version:** evaluator/container build, schema version, library dependency lock, configuration and feature-flag state.
- **Patient-input version:** source resource identifier and version, mapping version, effective time, receipt time, status, unit, reconciliation/verification state, and evaluation snapshot hash. [^9]

Pin all four in every evaluation. A recommendation cannot be reconstructed if it stores only “rule 12 fired”: it must identify the exact rule content, source material, terminology, input snapshot and runtime that produced it. This aligns with FHIR Provenance’s purpose: it records entities and processes involved in producing/delivering a resource, supports trust and reproducibility, and can target a specific resource version. [^9]

### Release practice

Use immutable releases. A proposed change moves through `draft → technical validation → clinical review → approved → scheduled → active → retired`; production content is never edited in place. Hotfixes get a new patch version, a narrow impact statement, focused regression evidence and retrospective clinical review. Maintain a machine-readable changelog that classifies each change as editorial, mapping/terminology, evidence refresh, threshold/logic, output wording, or safety correction. Threshold/logic and terminology changes must require re-execution of affected golden cases and comparison against the previous release. [^8]

At evaluation, write one immutable `RuleExecution` record per run: patient/encounter pseudonymous references; trigger context; rule and package version/hash; source citations; input resource versions and normalized facts; result (`triggered/not_triggered/indeterminate`); emitted recommendation IDs; latency; display/suppression reason; and user response/override linked later. Preserve raw inbound source payload references separately under the data-retention policy; do not overwrite a source value just because a later mapping changes. [^9]

## 4. Temporal clinical-data model

Noor needs an **append-only event model**, not a “latest value” table. For every vital/lab/clinical fact store:

- `observed_at` (physiologically relevant time or specimen/measurement time);
- `issued_at` (when the result became available);
- `received_at` (when Noor received it);
- `recorded_at` and source-resource version;
- result `status` (`registered`, `preliminary`, `final`, `amended`, `corrected`, `cancelled`, `entered-in-error`, as mapped from the source);
- value, canonical UCUM unit and original display/unit; method/device/specimen where relevant;
- identity/encounter/source and mapping/verification status; and
- `valid_for_rule` plus an explicit reason when false. [^3]

FHIR R4 provides the conceptual separation Noor needs: `Observation.status` is required and is a modifier because some statuses mean the resource is not valid; it distinguishes result status from the overall report and notes that an individual result can be final before the whole report. [^3] `effective[x]` is the physiologically relevant time needed for relevance and trend analysis, while `issued` is when the version became available to providers. [^3] FHIR also provides explicit `dataAbsentReason`; it should be used or mapped for a missing/unperformed/invalid result rather than treating absence as a normal value. [^3]

### Pending-HbA1c and post-visit result workflow

At visit close, persist a `ResultExpectation` linked to the order/service request and encounter: requested analyte, due/window, intended rule family, responsible queue and state (`ordered`, `specimen-collected`, `pending`, `final-received`, `expired/not-received`, `cancelled`). The visit assessment must say “not assessed—result pending,” not infer a current HbA1c. When the final result arrives, create a new evaluation context tied to the original encounter and current medication/condition snapshot; run only rules whose data-requirement manifests declare a post-result trigger; route material changes as a tracked follow-up task. Do not retroactively rewrite the visit conclusion. [^9]

### Freshness and irregular trajectories

Freshness is a rule-level clinical policy, not a database TTL. Each input requirement must declare: accepted statuses; max age from `effective_at`; whether receipt delay matters; source-preference and reconciliation rules; required measurement context; and an `indeterminate` action. Keep all measurements—even those unsuitable for automated advice—so a reviewer can see conflicts. Use the most recent *eligible* fact only after evaluating those criteria; do not substitute a preliminary, unit-ambiguous or device-incompatible value merely because it is newer. [^3]

For the trajectory feature, do not impute a regular time series from three to six irregular observations and label it a clinical trend. Display raw dated values and a conservative “insufficient density / possible change / review” state until the specific BP variability and measurement evidence in the risk-model workstream defines the minimum observation/duration rule. This is a safety guardrail, not a statistical limitation disguised as a model feature. [^3]

## 5. Audit logging: security audit, clinical provenance, and workflow evidence

No single log satisfies all three purposes.

- **Security/access audit:** record authentication, authorization result, patient/chart access, data export, device/session, API call, configuration change and failed actions. FHIR `AuditEvent` is a record for maintaining a security log; it carries event type/action, recorded time, outcome, active agents, source and accessed entities. [^10]
- **Clinical provenance:** record source data, rule/source versions, transformed inputs and generated clinical finding. FHIR distinguishes this from AuditEvent: Provenance captures creation/revision/signature context while AuditEvent records events as they occur. [^9]
- **Workflow/action audit:** record whether the recommendation was rendered, opened, acknowledged, accepted, rejected, deferred, overridden, escalated, acted on, completed or expired; who acted; when; structured reason; and links to resulting orders/tasks/notes. This is Noor’s product-specific execution ledger, not something to infer from a click.

For every displayed recommendation, emit a correlation ID linking all three layers. Capture `evaluated`, `eligible`, `displayed`, `suppressed` (and why), `opened`, `action-selected`, `override-reason-recorded`, `task-created`, `task-completed`, `communication-attempted`, and `closed`. Store clocks in UTC plus local display timezone; protect log integrity with append-only storage, restrictive access, retention controls, and a separately monitored admin-audit trail. [^10]

This needs to exist before a pilot. A study using EHR audit logs to observe responses to noninterruptive alerts found that longitudinal interpretation required clinician/data-manager work and that planning log data before deployment was necessary. [^11] It also demonstrates why “alert opened” is not equivalent to action: only 208 of 627 PCP-opened alerts had immediate action, while additional actions appeared later. [^11]

## 6. Testing and validation strategy

### The safety case

Treat each rule release as a testable clinical-content change, not merely an application deployment. The architecture should support the following pyramid:

1. **Schema/compile validation:** required citations, cited source version/section, vocabulary bindings, units, approval state, no prohibited free-text expressions, stable IDs, semantic version and deterministic serialization.
2. **Rule-unit tests:** every branch, threshold boundary, unit conversion, negation, exclusion, missing/stale/preliminary/corrected value, duplicate medication, terminology synonym and expected `indeterminate` case.
3. **Golden patient cases:** clinician-authored patient vignettes with FHIR-like input fixtures, expected output, rationale and source citation. Make them executable regression assets.
4. **Integration tests:** raw import → mapping → validation → fact snapshot → evaluation → audit event → rendered card/task. Include partial failures, late results, changed source resource versions, offline re-sync and duplicate events.
5. **Release comparison:** run the full golden corpus against old and candidate rule packages; require a reviewed explanation for every changed output.
6. **Independent clinical validation:** a clinician who did not encode the rule reviews high-severity test design/results and signs the release record.
7. **Simulation and shadow mode:** run against synthetic/de-identified cases and then provider-approved silent/shadow workflow before permitting clinician-facing use. Monitor no-fire, firing spikes, data-quality rejection and unexpected override patterns. [^8][^12]

A published hypertension-CDS testing study illustrates why test cases need explicit selection: 26 decision points produced 3,120 possible output combinations; 100 selected cases exercised major pathways but only 1% of all combinations. [^8] Noor should therefore use risk-based/path coverage, boundary analysis and pairwise combinations for low-risk dimensions, then add exhaustive tests only for small, high-harm decision tables. “All combinations” is neither realistic nor a useful safety claim.

### Synthetic patients and Synthea

Synthea is valuable for plumbing, load, FHIR import/export, basic demographic variation and test-data privacy. It has a modular rule system and can emit FHIR R4, bulk FHIR, C-CDA and CSV. [^13] But it is **not a Saudi validation cohort**. Its defaults use Massachusetts census demographics; custom geography requires replacing demographics, postal/provider locations and potentially names, and non-US output can retain US address artefacts without post-processing. [^14] Its source code documentation allows configurable statistics/demographics, but that is not equivalent to Saudi disease prevalence, care pathways, medication availability, laboratory practices, Arabic names, home-health workflows or missing-data patterns. [^13]

The independent validation evidence reinforces that boundary: Synthea modeled general demographics/service probabilities reasonably in one Massachusetts comparison, but did not model deviations from care or health outcomes after care deviations well. [^12] Use Synthea for interface and adversarial fixture generation, not performance, clinical-validity or Saudi-localisation claims. Build a Noor-specific synthetic “golden library” from clinician-authored scenarios: frail older adult with duplicate brands, conflicting medication sources, eGFR near a threshold, corrected potassium, missing unit, pending HbA1c, fasting status, and late-arriving result. Avoid real identifiers; a later regulated pilot needs an approved de-identified/shadow-data plan rather than an invented national synthetic population.

### What regulators typically need from this architecture

Saudi-specific regulatory classification and submission expectations belong to the Saudi regulatory section, so this report does not import US requirements as Saudi law. Nevertheless, the FDA’s device-software submission guidance demonstrates the kind of evidence package a regulated software programme should expect to maintain: software documentation is a distinct submission concern, and CDS guidance is a distinct document category. [^15][^16] Noor should preserve traceable requirements, hazard controls, source-to-rule links, review records, verification evidence, release history, cybersecurity change records and post-deployment monitoring from day one; this is defensible engineering regardless of the ultimate SFDA classification.

## 7. Build sequence and concrete deliverables

**P0 — before any clinical pilot**

1. Define the typed fact snapshot and data-requirement manifest; reject unsafe inputs rather than coercing them.
2. Implement the constrained declarative rule schema, evaluator and clinician-review renderer.
3. Implement immutable content release, four-eyes approval, source/version pinning and a rule-execution ledger.
4. Implement `Observation` temporal/status handling and the pending-result state machine.
5. Create the first golden-case library and CI regression gate; no rule may be active without tests, citations and approval.
6. Implement separate access audit, provenance and workflow-action records with correlation IDs. [^10][^9]

**P1 — before provider-facing integration**

1. Map provider data to canonical facts with code/unit/status/time/provenance checks.
2. Add raw-to-normalized mapping test fixtures and data-quality dashboards.
3. Build the post-result re-evaluation/task workflow and clinician-facing reason/override capture.
4. Add release comparison, no-fire/spike monitoring and independently reviewed high-severity regression tests.
5. Test an R4 import/export simulator with Synthea plus Noor-specific adversarial cases. [^13][^12]

**Defer until a named need exists**

- durable_rules/event statecharts;
- Drools service deployment;
- production CQL runtime and FHIR Clinical Reasoning infrastructure;
- an unrestricted tenant rule editor;
- any autonomous action, medication/order write-back or self-tuning threshold mechanism. [^1]

## Bottom line

Noor’s design constraint—one clinician reviewer and a non-programming product owner—should determine the architecture. The first engine should be intentionally boring: structured clinical rules, a short allowed operator set, explicit data/freshness guards, deterministic outputs, version-pinned provenance, immutable execution records and executable golden cases. CQL and heavier rule engines remain credible interoperability options, but they do not replace the central safety work: showing a clinician precisely what the rule means, what data it used, which source authorizes it, when it cannot assess safely, and exactly what version produced a recommendation. [^9][^3]


[^1]: Papadopoulos et al., 2022. A systematic review of technologies and standards used in the development of rule-based clinical decision support systems. Health technology.

[^2]: Zhang et al., 2016. An integration profile of rule engines for clinical decision support systems. IEEE International Conference on Progress in Informatics and Computing.

[^3]: http://hl7.org/fhir. Observation - FHIR v4.0.1.

[^4]: Seifter et al., 2018. A Comparison of Business Rule Management Systems and Standards for the Implementation of Clinical Decision Support Systems Using Data from Structured CDA Documents.

[^5]: venmo/business-rules: Python DSL for setting ...

[^6]: jruizgit. jruizgit/rules: Durable Rules Engine.

[^7]: http://hl7.org/fhir. Home - Using CQL With FHIR v2.0.0.

[^8]: Tso et al., 2016. Test Case Selection in Pre-Deployment Testing of Complex Clinical Decision Support Systems. Summit on Clinical Research Informatics.

[^9]: http://hl7.org/fhir. Provenance - FHIR v4.0.1.

[^10]: http://hl7.org/fhir. AuditEvent - FHIR v4.0.1.

[^11]: Amroze et al., 2019. Use of Electronic Health Record Access and Audit Logs to Identify Physician Actions Following Noninterruptive Alert Opening: Descriptive Study. JMIR Medical Informatics.

[^12]: Chen et al., 2019. The validity of synthetic clinical data: a validation study of a leading synthetic data generator (Synthea) using clinical quality measures. BMC Medical Informatics and Decision Making.

[^13]: README.md at master · synthetichealth/synthea.

[^14]: synthetichealth. Demographics for Other Areas · synthetichealth/synthea Wiki · GitHub.

[^15]: Content of Premarket Submissions for Device Software Functions: Guidance for Industry and Food and Drug Administration Staff | Guidance Portal.

[^16]: Clinical Decision Support Software: Guidance for Industry and Food and Drug Administration Staff | Guidance Portal.