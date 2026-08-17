# Project Noor Pre-Plan Gap Remediation Plan

**Status:** Proposed remediation programme
**Date:** 2026-08-16
**Authority:** Subordinate to `docs/cds-architecture.md` v1.0.0 (the SSOT)

## Purpose

This plan closes the known research, evidence, terminology, governance, and
provider-policy gaps before Project Noor's software implementation plan depends
on executable clinical content.

It does not replace the SSOT and does not authorize clinical rules. If this plan
conflicts with the SSOT, the SSOT wins. The two endpoints are deliberately
separate:

1. **Software-plan ready:** enough is known to plan and build the repository,
   `canon`, evaluator, catalogue compiler, governance gates, persistence, and
   workflow without inventing clinical content.
2. **Clinical-content ready:** a particular rule has complete evidence,
   terminology, tests, clinical approval, and provider policy and may enter the
   SSOT release lifecycle.

The project is already software-plan ready for SSOT build steps 1-5. It is not
clinical-content ready. Clinical work remains gated while the independent
engineering foundation proceeds.

## Governing Constraints

- Do not change any SSOT §0 security-critical constant through this plan.
- Do not treat text in a research file as executable content.
- Do not infer that described source code, content files, tests, dependencies,
  database objects, or CI jobs exist. They do not exist at the start of this
  plan.
- Use the source-label ladder in SSOT §3.2 in order: local SFDA SPC, EMA
  centrally-authorised SmPC, then an SmPC from an EU national agency.
- An unretrieved local SPC does not permit an invented version or locator.
- The SEML 2023 source supports exactly ingredient listing, strengths, and dose
  forms. It does not support dosing, contraindications, interactions, or
  monitoring.
- Keep eGFR and Cockcroft-Gault creatinine clearance as distinct observables.
- Keep pregnancy, breast-feeding, and fertility as three distinct propositions.
- No numeric or categorical threshold becomes executable before its source pin
  and clinical approval are complete.
- Every new clinical rule is test-first and follows the validation requirements
  in SSOT §12 and `docs/testing-standards.md`.
- No `stop_and_review` rule may use role doubling or proceed without a separate
  credentialed clinical approver.
- No provider-specific emergency destination, escalation deadline, staffing
  policy, stock position, or workflow is inferred from public research.
- Protected guideline expression, figures, scales, and decision trees are not
  copied into the repository or product.

## Completion States

Every tracked item uses one of these states:

| State | Meaning |
|---|---|
| `not_started` | No verified work product exists |
| `in_research` | Source retrieval or reconciliation is underway |
| `blocked_external` | A named external decision, source, licence, clinician, or provider is required |
| `populated` | Complete source-backed draft exists but lacks clinical approval |
| `clinician_approved` | Named clinical owner approved it with date and review date |
| `technically_validated` | Required schemas, cases, and automated gates pass |
| `active` | It completed the SSOT release lifecycle and is in an immutable active release |
| `out_of_scope` | Deliberately excluded with rationale and approving owner |

`unretrieved` and `unpopulated` remain the SSOT content-schema states where the
SSOT requires those exact values. The states above track remediation work; they
do not rename schema values.

## Roles and Accountability

The following appointments are prerequisites to clinical approval, not
prerequisites to drafting the software implementation plan:

| Role | Required responsibility | Appointment evidence |
|---|---|---|
| Clinical content owner | Owns clinical meaning, scope, source-family selection, and impact classification | Name, credential, SCFHS identifier where applicable, effective date, review cadence |
| Technical custodian | Maintains schemas and executable representation without changing clinical meaning | Name, role, effective date |
| Second clinical approver | Independently approves every `stop_and_review` rule | Name, credential, approval timestamp on each affected rule or release |
| Terminology owner | Owns code-system editions, mappings, licences, and review cadence | Named owner in the terminology charter |
| Provider medical director | Approves local emergency, supervision, prescribing, and escalation policies | Provider-approved policy version and effective date |
| Privacy/security owner | Owns PDPL, hosting, key custody, access, and operational safety gates | Named owner and linked approval records |

Role appointments must be recorded in governed project records once the
repository and schemas exist. Until then, record the decision in the pull
request that introduces the relevant governed artefact. Do not put placeholder
names into approver fields.

## Workstream 1: Establish the Governance Foundation

**Goal:** Make the approval trail real before any clinical content is promoted.

### Actions

- Initialize Git as SSOT build step 1. A pull request is the four-eyes approval
  record required by SSOT §7.5.
- Establish branch protection and required review after a remote repository is
  selected. Do not claim four-eyes governance from local commits alone.
- Appoint the roles above before their first approval is required.
- Define how credentials are verified and how expired or changed credentials
  invalidate future approvals without altering historical releases.
- Define a review cadence for clinical content and terminology.
- Require a change rationale and clinical-impact class for every clinical
  release entry.
- Configure CI to post the generated clinician-facing plain-language rendering
  and its diff into each clinical-content pull request. The clinical approver
  signs that rendering, not YAML alone, as required by SSOT §7.5.
- Keep content-governance roles distinct from operational care roles, as required
  by SSOT §10.2.

### Evidence

- Git repository exists.
- Protected remote workflow exists before the first clinical approval.
- Role appointment records contain the required identities and effective dates.
- A sample non-clinical pull request demonstrates the review and merge path.
- A sample content pull request demonstrates that CI posts the generated
  plain-language rendering and rendering diff for review.

### Exit Criteria

- Every clinical artefact has an accountable owner path.
- No high-severity content can merge with a missing or doubled approver.
- Approval history is permanent and reviewable.

## Workstream 2: Repair the Content Roadmap

**Goal:** Make `docs/research/cds-content-roadmap.md` a truthful status register.

### Actions

- Remove the claim that one metformin rule exists; there is no `content/`,
  `src/`, or `tests/` tree at the start of this plan.
- Replace the instruction to assume EMA/ICH-derived values are correct with the
  SSOT source-label ladder and proposition-level verification requirement.
- Replace the local-SPC-only checklist item with the three-rung SSOT ladder,
  while retaining local SFDA SPC as the preferred source.
- Normalize the medication list to 45 distinct ingredients: 11 diabetes and 34
  cardiovascular. Record aliases and duplicate roadmap placements without
  assigning separate ingredient identities.
- Replace each ingredient's binary checkbox with the following fields:
  `identity`, `seml`, `source_label`, `renal`, `hepatic`, `interactions`,
  `monitoring`, `pregnancy`, `breast_feeding`, `fertility`, `achievability`,
  `complications_reconciled`, and `clinical_approval`.
- Track each of the five red-flag libraries, signal-catalogue groups, screening
  domains, guideline families, and provider policies as separate items.
- Record source research, clinical approval, technical validation, and release
  activation as different states.
- Preserve intentionally deferred work as `out_of_scope` with an SSOT reference,
  not as an unchecked or apparently forgotten item.

### Verification

- Count exactly 45 unique `ingredient_id` candidates.
- Confirm losartan/losartan potassium has one ingredient identity.
- Confirm furosemide, spironolactone, and hydrochlorothiazide are not counted
  twice because they appear in two therapeutic sections.
- Reconcile every status against `diabetes-research.md`,
  `hypertension-research.md`, and the filesystem.
- Search the roadmap for stale claims that rules or content files already exist.

### Exit Criteria

- Every roadmap status is evidence-backed and independently verifiable.
- The roadmap no longer contradicts SSOT §3.2 or the research-file
  implementation-status sections.
- No duplicate roadmap placement inflates catalogue coverage.

## Workstream 2A: Reconcile the Medication Catalogue Scope

**Goal:** Resolve the mismatch between the roadmap's 45 distinct ingredients
and SSOT §3.2's disclosed curated MVP target of roughly 60-80 high-severity
ingredients.

The current research files cover the 45 diabetes and cardiovascular ingredients
listed in the roadmap. Completing those files does not by itself complete the
SSOT medication-knowledge scope.

### Actions

- Have the clinical content owner define the intended first-release claim: the
  exact patient population, medication-safety use cases, interaction classes,
  and ingredient count the product will display.
- Build a candidate-gap inventory from the target population and prioritized
  rules. Include high-severity interacting partners that can enter through the
  reconciled medication list even when they are absent from the SEML.
- Rank candidates by severity, expected exposure in the intended population,
  firability from available structured medication data, and whether inclusion
  closes a known interaction cluster.
- For every added ingredient, apply the same identity, source-label, dosing,
  interaction, monitoring, reproductive, complication, achievability, testing,
  and approval requirements as the original 45.
- Record the final curated set and its version in the product scope disclosure.
- If the project owner instead wants an MVP set of 45, obtain explicit approval
  to amend SSOT §3.2 before planning or claiming that narrower catalogue as the
  completed SSOT scope. Do not reinterpret "roughly 60-80" silently.

### Exit Criteria

One of two outcomes is recorded:

1. A versioned curated set within the SSOT's roughly 60-80 target is completely
   researched and governed.
2. The SSOT is explicitly amended to a narrower target with rationale and
   corresponding scope-disclosure changes.

- The product disclosure states the exact covered set and does not claim general
  interaction or polypharmacy coverage.
- Every ingredient in the declared set meets the per-ingredient completion
  criteria in Workstream 4.

## Workstream 3: Resolve SEML and Formulation Ambiguities

**Goal:** Prevent a strength-, route-, or formulation-dependent rule from using
an ambiguous converted table row.

### Actions

- Re-check the original SEML 2023 PDF rather than the converted Markdown for:
  insulin lispro 100 IU/mL versus 200 IU/mL, gliclazide IR versus MR, verapamil
  tablet strengths, and nifedipine immediate-release versus extended-release.
- Record the visible PDF page, table position, drug name, formulation, strength,
  route, and whether merged-cell attribution is definitive.
- Record tablet score, divisibility, and modified-release restrictions only from
  an authoritative label or product record. A mathematically divisible dose is
  not automatically licensed or safe to divide.
- Classify each medicine/formulation as `home_active`, `transition_or_reconciliation`,
  or `acute_care_only` for the first provider profile. This is a scope decision,
  not a statement that an ingredient is generally unsuitable for home care.
- Route pump-rate and diluent-concentration achievability to a later acute-care
  model rather than forcing it into tablet-strength logic.
- Recalculate every existing strength-achievability draft after the source facts
  are resolved.

### Required Decisions

- Whether product/formulation-level rules are in the first catalogue release.
- Whether any divided tablet is supported by the pinned label and local
  formulary policy.
- Whether acute parenteral medicines are reconciliation-only in Noor's first
  provider deployment.

### Exit Criteria

- No strength-dependent proposition relies on an orphan Markdown row.
- Every formulation-sensitive rule declares the narrowest defensible
  `drug_scope_level`.
- Every target dose is classified as `strength_achievable`,
  `achievable_by_division`, or `unachievable` with supporting source facts.
- Unachievable doses route to pharmacist review and never render as dosing
  instructions.

## Workstream 4: Pin and Reconcile All 45 Medication Labels

**Goal:** Replace generic or secondary-source medication claims with exact,
versioned regulatory propositions.

### Retrieval Procedure Per Ingredient

1. Search the SFDA SDI e-service and record the attempt, date, result, and reason
   if inaccessible or no matching product is retrievable.
2. Search the EMA centrally-authorised medicine register.
3. If no appropriate EMA SmPC exists, search an official EU national medicines
   agency.
4. Select a current single-ingredient SmPC matching the required route and
   formulation. Do not use a fixed-dose-combination label to source a
   single-ingredient rule.
5. Record `authority`, exact `document` title, label `revision_date`, and exact
   `locator`, plus the required `fallback_from` record.
6. Retain a stable official-source pointer and enough bibliographic metadata to
   retrieve the same label version. Store a local copy only after checking
   redistribution and repository-access constraints.
7. Have a second researcher or the clinical content owner verify identity,
   version, and locator before marking the label `pinned`.

### Extraction Matrix Per Ingredient

Extract distinct propositions from the applicable label sections:

| Topic | Typical SmPC locator | Required output |
|---|---|---|
| Posology and organ impairment | §4.2 | Indication, route, formulation, population, renal metric, bands, dose/interval action, dialysis behavior |
| Contraindications | §4.3 | Exact clinical proposition and scope |
| Warnings and precautions | §4.4 | Serious complications, risk factors, temporary holds, monitoring triggers |
| Interactions | §4.5 | Interacting substance/class, mechanism where stated, action, timing, and firability |
| Reproductive propositions | §4.6 | Separate pregnancy, breast-feeding, and fertility states and pointers |

### Reconciliation Procedure

- Compare every row in the pharmacotherapy matrices and every complication
  profile against the pinned label.
- Classify each draft statement as `confirmed`, `corrected`, `removed`,
  `not_stated_in_label`, or `requires_non_label_guideline_source`.
- Do not preserve an FDA boxed-warning classification as an EMA/SFDA boxed
  warning. Preserve only the proposition and regulatory status supported by the
  pinned source.
- Use pharmacovigilance alerts or guidelines only under an appropriate
  `source_family`, with their own exact source records.
- Record contradictions between an EU fallback and a subsequently retrieved
  SFDA SPC as content incidents under SSOT §11.9.

### Exit Criteria Per Ingredient

- Source label has all four required pin fields and an auditable fallback record.
- Renal guidance names exactly one metric where a metric is used.
- Hepatic guidance does not treat transaminases as Child-Pugh severity; any
  label initiation gate is explicitly typed and separately sourced.
- Monitoring due intervals are separate from result freshness windows.
- Pregnancy, breast-feeding, and fertility are each populated or explicitly
  recorded as not stated.
- Important interactions are reconciled against actual formulary and medication
  reconciliation inputs.
- Complication profile is reconciled and clinically reviewed.
- Strength achievability is re-evaluated against the resolved formulation.

### Workstream Exit Criteria

- All 45 distinct ingredients meet the per-ingredient criteria.
- No medication rule candidate depends only on FDA labels, DailyMed,
  StatPearls, Drugs.com, trial summaries, or uncited clinical memory.
- Every unresolved proposition remains visibly blocked and cannot pass catalogue
  compilation.

## Workstream 5: Select and Pin Guideline Families

**Goal:** Provide internally consistent disease and monitoring content without
blending target systems.

### Hypertension

- Resolve the research/SSOT mismatch in favor of the SSOT unless the project
  owner explicitly approves an SSOT amendment.
- Research and pin `nhc-sha-2023`, the SSOT's interim default, at proposition
  level for classification, measurement context, targets, populations,
  exceptions, and first-line selection.
- Maintain ACC/AHA 2025 and ESC 2024 as separate profile-selectable families only
  after each is independently pinned.
- Do not use ESH 2023 as an implicit default. If support for ESH is desired, add
  it only through an explicit SSOT decision and keep it as a separate family.
- Obtain the first provider's documented source-family selection before
  activating BP target or treatment-selection content.

### Diabetes, CKD, and Monitoring

- Pin ADA sources for hypoglycaemia levels and diabetes screening propositions.
- Complete the existing Umpierrez DKA/HHS source records with exact proposition
  locators and clinical approval.
- Pin KDIGO propositions for GFR and albuminuria categories, chronicity,
  confirmation intervals, monitoring, and cardiorenal treatment.
- Pin current sources for retinopathy screening/referral, foot and neuropathy
  examination, ACS recognition, stroke recognition, and severe-hypertension
  terminology.
- Seek current Saudi guidance first where the selected domain profile requires
  it; record a fallback rather than silently substituting an international
  family.

### Exit Criteria Per Domain

- One source family is selected per tenant profile and clinical domain.
- Organisation, document, revision/version, exact locator, jurisdiction,
  population, exclusions, and review date are present for every proposition.
- Conflicting systems remain separate and are never averaged or combined.
- Every numeric boundary has an explicit inclusive/exclusive convention.
- A named clinician approves the selected propositions and records a review
  date.

## Workstream 6: Complete the Structured Signal and Observable Catalogue

**Goal:** Ensure every planned rule reads governed structured observations and
never free text.

### Required Signal Groups

- Diabetes acute illness: hypoglycaemia, hyperglycaemia, DKA/HHS prodrome,
  vomiting, oral-intake failure, dehydration, breathing pattern, mental status,
  swallowing ability, seizure, and third-party assistance.
- Cardiovascular emergencies: ACS symptom phenotypes, stroke deficits and onset,
  hypertensive acute target-organ damage, syncope, pulmonary oedema, and aortic
  emergency features.
- Heart-failure decompensation: dyspnoea pattern, orthopnoea where sourced,
  oedema, weight change, perfusion findings, and clinician-documented HF status.
- Pharmacotherapy effects: oedema, GI intolerance, injection-site reaction,
  lipohypertrophy/lipoatrophy, hypoglycaemia symptoms, bleeding, muscle symptoms,
  and other effects required by prioritized rules.
- Medication use: medication confusion, missed dose, duplicate dose, refill gap,
  administration assistance, caregiver report, and discrepancy state. These are
  structured assessments, not a proprietary adherence score.
- Physical examination: hydration and haemodynamic findings, diabetic foot and
  wound findings, infection and ischaemia, neuropathy examination, and vascular
  assessment.

### Required Record Per Observable or Signal

- Stable Noor identifier and clinical definition.
- Value type, permitted values, and UCUM unit where numeric.
- LOINC mapping for observations or SNOMED CT mapping for clinical meaning where
  applicable.
- Official source display retained separately from Arabic UI text.
- Terminology edition/release, mapping method, confidence, and owner.
- Permitted `entry_mode`, mandatory `informant` behavior, and source provenance.
- Method, specimen, setting, posture, laterality, or timing fields required for
  correct interpretation.
- Accepted source status and intrinsic quality behavior through `canon`.
- Rules for contradictory, ambiguous, unmapped, or absent data.
- Clinical source and owner for any bounded symptom or examination definition.

### Terminology Prerequisites

- Create the SSOT terminology charter during software implementation before
  executable mappings are introduced.
- Record licence status, edition, effective time, module, owner, review cadence,
  and attribution obligations per code system.
- Do not reproduce SNOMED CT display strings in distributable content while the
  Saudi Affiliate licence is outstanding.
- Keep Arabic labels separate and route translation through the patient-use
  gate.

### Exit Criteria

- Every input named by a candidate rule has an approved registry record.
- No rule reads `encounter_narrative` or an undeclared snapshot field.
- Ambiguous and unmapped signals are visible unusable states, not guessed values.
- Patient-reported and staff-observed facts remain distinguishable.
- Every registry conversion is reversible within declared precision.

## Workstream 7: Complete the Five Red-Flag Libraries

**Goal:** Produce approved emergency-recognition content without inventing local
response protocols.

### Libraries

1. DKA/HHS.
2. Severe hypoglycaemia.
3. Hypertensive emergency.
4. Acute coronary syndrome.
5. Stroke.

### Required Specification Per Library

- Exact structured inputs, units, methods, and permitted values.
- Activation propositions and all referenced threshold records.
- Which symptoms or signs activate the hatch independently of a numeric value.
- Required conjunctions; for example, glucose alone must not diagnose DKA/HHS,
  and BP alone must not define hypertensive emergency.
- Immediate-review criteria that do not meet emergency activation.
- Repeat/verification criteria and behavior for questionable measurements.
- Missing, stale, contradictory, poor-quality, and wrong-context behavior.
- Patient modifiers including pregnancy, CKD, age, frailty, fasting,
  medication exposure, and prior disease where applicable.
- Explicit exclusions and alternative explanations without claiming Noor ruled
  out a diagnosis.
- Provider-facing meaning, action, and uncertainty.
- Clinical owner, approver, review date, and source-family pin.
- At, just-below, just-above, missing, stale, poor-quality, wrong-context, and
  clinically severe pairwise cases.

### Provider Policy Dependency

The software can guarantee that the emergency hatch opens from every state. A
named provider must supply and approve:

- Local emergency destination and contact pathway.
- Responsible role or person by operating period.
- Escalation acknowledgement deadline.
- Downtime and failed-contact behavior.
- Documentation, rehearsal, and review cadence.

These values belong in a tenant profile, not in engine code or general research.

### Exit Criteria

- Every library has complete source records and clinical approval.
- All required structured inputs exist in the observable registry.
- Every numeric threshold has boundary cases and every composite rule has
  clinically important pairwise cases.
- Repeat logic can never delay or disable the emergency hatch.
- The first provider has approved and rehearsed the local response pathway.

## Workstream 8: Complete Monitoring and Screening Content

**Goal:** Turn monitoring and screening domains into sourced obligations without
confusing freshness with due dates.

### Required Domains

- Renal and potassium follow-up after RAAS inhibitor or MRA initiation and dose
  change.
- Renal monitoring and sick-day/temporary-hold propositions for applicable
  diabetes medicines.
- Retinal screening and referral.
- Foot and neuropathy examination reminders.
- Glycaemic and HbA1c monitoring with context flags.
- Lipid monitoring without introducing a deferred ASCVD risk model.
- Orthostatic and BP measurement follow-up.
- KDIGO albuminuria confirmation and CKD chronicity.
- HbA1c-independent SGLT2 inhibitor or GLP-1 receptor agonist cardiorenal
  propositions where supported by the selected guidelines and label scope.

### Required Fields Per Monitoring Proposition

- Eligible population and exclusions.
- Trigger event: initiation, titration, result, calendar event, or condition.
- Required observable and method/context.
- `max_age_days` for whether a result may be used by a rule.
- `monitors` due interval for when another result is owed.
- Exceptions and provider-determined lanes.
- Obligation kind, owner-routing policy, and closure evidence.
- Exact source record and clinical approval.

### Exit Criteria

- Every interval is source-backed and clinically approved.
- Missing results open or preserve obligations and never count as normal.
- A missing, cancelled, or not-received result never auto-closes an obligation.
- Screening reminders remain reminders and do not infer disease or implement a
  deferred risk score.

## Workstream 9: Author and Validate Governed Clinical Content

**Goal:** Promote only remediated propositions into executable content.

This workstream begins per rule only after its inputs, sources, terminology, and
provider-policy dependencies have met the preceding exit criteria. It does not
wait for all 45 ingredients if the selected rule is independently complete.

### Rule Promotion Sequence

1. Create or approve every required observable registry record.
2. Create threshold and valueset records with complete citations and approval
   metadata.
3. Write the rule's `.cases.yaml` rows before writing the rule.
4. Run the cases and demonstrate the expected failure because the rule is absent.
5. Author the smallest rule that satisfies the approved proposition.
6. Add golden synthetic patient cases for cross-rule behavior.
7. Run catalogue schema validation, rule cases, golden cases, invariant tests,
   and release comparison.
8. Complete technical validation.
9. Complete clinical review and, for `stop_and_review`, independent second
   clinical approval.
10. Promote through `draft → technical_validation → clinical_review → approved
    → scheduled → active` in an immutable release.

### Minimum Case Coverage

- Exactly at, just below, and just above every numeric boundary.
- Missing, stale, unusable, ambiguous, and wrong-context requirements.
- Conflicting measurements and relevant methods/settings.
- Scope inclusion and exclusion.
- Clinically important pairwise combinations.
- Degradation of unmet `stop_and_review` requirements to
  `interruptive_review` with the unmet requirement named.
- Emergency activation that is not suppressed by repeat or workflow gates.
- Strength-unachievable and formulary-unavailable outcomes where applicable.

### CI Exit Criteria

All 17 SSOT §10.4 content gates pass. Release comparison contains no unexplained
changed or disappeared finding. Required validation claims in SSOT §12.6 are
covered by tests. Independent clinical validation and shadow mode remain
separate later rungs and are not implied by a green automated suite.

## Workstream 10: Close Patient-Use Gates

**Goal:** Resolve the external conditions that block clinician-facing use rather
than code construction.

Track and close the SSOT §13.2 gates applicable to the intended release:

- SFDA classification determination.
- PDPL DPIA, controller/processor agreement, and Saudi hosting procurement.
- Encryption-key custody and retention schedule.
- SNOMED CT Saudi Affiliate licence.
- Written ICD-10-AM commercial-use position.
- ATC redistribution rights.
- Provider supervision and prescribing-authority policy.
- Provider-approved and rehearsed emergency pathway.
- Clinician-approved medication-scope disclosure.
- Qualified Arabic translation, clinical validation, RTL rendering, and mixed
  numeral/unit verification where patient contact ships.
- Saudi LDL table transcription and dual verification if that content is in the
  release.
- Complaint handling, incident log, and post-market review with owners and
  cadences.
- LOINC attribution and derivative-translation controls.
- PHQ-9 licence and item-9 escalation only if depression screening is added; it
  remains outside the current MVP.
- Shadow mode completed with no-fire, firing-spike, data-quality rejection, and
  override patterns explained before clinicians see cards.

### Exit Criteria

- Every applicable patient-use gate has dated evidence, an owner, and an approval
  decision.
- No inapplicable gate is silently ignored; it is marked out of release scope
  with rationale.
- Shadow mode completes after independent clinical validation and before any
  clinician-facing activation.

## Dependency and Execution Order

Work proceeds in parallel where governance permits:

| Sequence | Work | Dependency |
|---|---|---|
| 1 | Governance foundation, roadmap repair, and catalogue-scope decision | None |
| 2 | SEML ambiguity resolution | Access to original SEML PDF |
| 3 | Label retrieval and guideline pinning | Source access; may proceed ingredient/domain at a time |
| 4 | Signal and observable curation | Terminology owner and source research |
| 5 | Red flags, monitoring, and screening specifications | Pinned sources and approved observables |
| 6 | Rule cases and executable content | Complete per-rule evidence, terminology, and clinical owner |
| 7 | Clinical approval and active release | Technical validation; second approver for `stop_and_review` |
| 8 | Patient-use activation | All applicable SSOT §13.2 gates, independent validation, shadow mode |

The later software implementation plan may begin after sequence 1 and may cover
SSOT build steps 1-5 without waiting for sequences 2-5. SSOT build step 6 must
name the exact renal-risk rule it intends to implement and demonstrate that
rule's remediation dependencies are complete. Build step 14 must remain blocked
until its BP and red-flag content meets the same standard.

## Prioritization

Do not batch all clinical content before proving the content path. Use this
order, subject to source availability and clinical-owner approval:

1. Resolve governance and roadmap truthfulness.
2. Pin the minimum sources and observables for one renal-risk medication-safety
   workflow.
3. Implement the catalogue gates and prove they reject unfinished content.
4. Complete DKA/HHS and severe-hypoglycaemia libraries.
5. Complete BP measurement quality and hypertensive-emergency triage under one
   selected source family.
6. Complete high-value monitoring obligations for RAAS inhibitors, MRAs, and
   renal-risk diabetes medicines.
7. Extend medication content one independently reviewable ingredient or
   interaction cluster at a time.
8. Complete the remaining screening/reminder content.

This order does not lower the completion standard. It produces small,
independently validated releases while the remaining items stay visibly blocked.

## Master Definition of Done

### Software-Plan Ready

- The repaired roadmap describes the actual filesystem and content state.
- Governance roles and external dependencies are explicit and not replaced by
  invented values.
- The software plan can map every SSOT build step to files, tests, commands, and
  verification without depending on unapproved clinical propositions.
- Clinical-content milestones contain explicit entry gates.

### Per-Rule Clinical-Content Ready

- All inputs have approved registry records.
- Every threshold and proposition has a complete, exact source record.
- Medication identity, formulation, route, scope, and achievability are resolved.
- The selected source family is internally consistent.
- Provider policy exists where the action depends on local operations.
- Required cases were written first and cover boundaries, degradation, quality,
  context, and pairwise risks.
- Technical validation and named clinical approval are complete.
- A separate approver signed every `stop_and_review` rule.
- All applicable SSOT §10.4 gates pass.

### Catalogue Complete for the Declared Scope

- All 45 currently researched ingredient profiles are pinned and reconciled.
- The SSOT medication-scope mismatch is closed: either the governed curated set
  reaches the roughly 60-80 target, with every added ingredient meeting the same
  standard, or an explicitly approved SSOT amendment defines a narrower target.
- Any ingredient excluded from an approved release scope is visibly excluded,
  with no product claim of coverage for it.
- All five red-flag libraries are sourced, approved, tested, and linked to a
  provider emergency pathway.
- Required monitoring and screening propositions are sourced and approved.
- No source, formulation, terminology, or ownership ambiguity remains hidden in
  active content.
- Every active item belongs to an immutable release with a classified changelog
  and explained release comparison.

### Patient-Use Ready

- Independent clinical validation is complete.
- All applicable SSOT §13.2 gates are closed.
- Shadow-mode findings are stable and explained.
- Provider emergency and operational policies are configured and rehearsed.
- No rule or workflow relies on an unresolved fact without the explicit interim
  behavior required by SSOT §16.

## Final Deliverables

Completion of this plan produces:

- A corrected `docs/research/cds-content-roadmap.md`.
- A versioned, clinically owned medication-scope inventory and exact product
  disclosure covering the final curated set.
- Reconciled `docs/research/diabetes-research.md` and
  `docs/research/hypertension-research.md` with exact source status.
- Verified SEML formulation and strength attributions.
- One source-label record per distinct ingredient.
- Proposition-level guideline source records per supported domain and family.
- An approved clinical signal and observable inventory ready for the governed
  registry.
- Five complete red-flag specifications.
- Sourced monitoring and screening specifications.
- Named governance and provider-policy decisions.
- A traceable list of clinically ready rules and explicitly blocked rules.
- The evidence needed for the subsequent software implementation plan to state
  precise content entry gates without assuming clinical facts.
