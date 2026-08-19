# Graph Report - cds_engine  (2026-08-19)

## Corpus Check
- 65 files · ~4,247,725 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 985 nodes · 1323 edges · 72 communities (56 shown, 16 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 174 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `54684659`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Project Noor — CDS Engine Architecture|Project Noor — CDS Engine Architecture]]
- [[_COMMUNITY_11. Topics raised during the design interview|11. Topics raised during the design interview]]
- [[_COMMUNITY_Project Noor — Testing Standards|Project Noor — Testing Standards]]
- [[_COMMUNITY_5. Interoperability and integration|5. Interoperability and integration]]
- [[_COMMUNITY_6. Risk models and scores (only those we might actually compute)|6. Risk models and scores (only those we might actually compute)]]
- [[_COMMUNITY_11. Clinical operations|11. Clinical operations]]
- [[_COMMUNITY_3. Drug knowledge base — the build-vs-license decision|3. Drug knowledge base — the build-vs-license decision]]
- [[_COMMUNITY_2. Saudi regulatory, legal, and health-system context|2. Saudi regulatory, legal, and health-system context]]
- [[_COMMUNITY_1. Clinical guidelines — the content source of truth|1. Clinical guidelines — the content source of truth]]
- [[_COMMUNITY_8. Competitive and market landscape|8. Competitive and market landscape]]
- [[_COMMUNITY_cds-safety-and-human-factors|cds-safety-and-human-factors.md]]
- [[_COMMUNITY_9. Technical architecture references|9. Technical architecture references]]
- [[_COMMUNITY_4. Terminology, coding, and identifiers|4. Terminology, coding, and identifiers]]
- [[_COMMUNITY_Behavioral Guidelines|Behavioral Guidelines]]
- [[_COMMUNITY_Behavioral Guidelines|Behavioral Guidelines]]
- [[_COMMUNITY_2. Regulatory and compliance posture|2. Regulatory and compliance posture]]
- [[_COMMUNITY_3.2 Medication knowledge|3.2 Medication knowledge]]
- [[_COMMUNITY_saudi-essential-medicines-list-2023|saudi-essential-medicines-list-2023.md]]
- [[_COMMUNITY_5. The observation model|5. The observation model]]
- [[_COMMUNITY_6. `canon` — the data-validity layer|6. `canon` — the data-validity layer]]
- [[_COMMUNITY_10. Clinical content governance|10. Clinical content governance]]
- [[_COMMUNITY_7. Rule schema and catalogue|7. Rule schema and catalogue]]
- [[_COMMUNITY_File structure|File structure]]
- [[_COMMUNITY_12. Testing and validation|12. Testing and validation]]
- [[_COMMUNITY_test_models.py|test_models.py]]
- [[_COMMUNITY_Task 3 Report The Observation Model and Quality Verdicts|Task 3 Report: The Observation Model and Quality Verdicts]]
- [[_COMMUNITY_models.py|models.py]]
- [[_COMMUNITY_Task 2 Report CI and the Import-Direction Seam Test|Task 2 Report: CI and the Import-Direction Seam Test]]
- [[_COMMUNITY_test_import_direction.py|test_import_direction.py]]
- [[_COMMUNITY_Task 1 Implementation Report|Task 1 Implementation Report]]
- [[_COMMUNITY_8. Evaluation|8. Evaluation]]
- [[_COMMUNITY_15. Deferred|15. Deferred]]
- [[_COMMUNITY_13. Gates|13. Gates]]
- [[_COMMUNITY_16. Open questions|16. Open questions]]
- [[_COMMUNITY_4. Module architecture|4. Module architecture]]
- [[_COMMUNITY_9. Findings, alerts, overrides|9. Findings, alerts, overrides]]
- [[_COMMUNITY_test_smoke.py|test_smoke.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_task-1-brief|task-1-brief.md]]
- [[_COMMUNITY_task-2-brief|task-2-brief.md]]
- [[_COMMUNITY_task-3-brief|task-3-brief.md]]
- [[_COMMUNITY_noor|noor]]
- [[_COMMUNITY_test_registry.py|test_registry.py]]
- [[_COMMUNITY_task-4-brief|task-4-brief.md]]
- [[_COMMUNITY_Task 4 Implementation Report|Task 4 Implementation Report]]
- [[_COMMUNITY_Task 5 Report Unit Resolution|Task 5 Report: Unit Resolution]]
- [[_COMMUNITY_load_registry|load_registry]]
- [[_COMMUNITY_task-5-brief|task-5-brief.md]]
- [[_COMMUNITY_Task 6 Report Conversion Round-Trip Property|Task 6 Report: Conversion Round-Trip Property]]
- [[_COMMUNITY_task-6-brief|task-6-brief.md]]
- [[_COMMUNITY_Coverage Fix Report|Coverage Fix Report]]
- [[_COMMUNITY_Whole-Branch Review Remediation Report|Whole-Branch Review Remediation Report]]
- [[_COMMUNITY_Final Whole-Branch Review Fix Report|Final Whole-Branch Review Fix Report]]
- [[_COMMUNITY_Global Constraints|Global Constraints]]
- [[_COMMUNITY_Whole-Branch Review Remediation Design|Whole-Branch Review Remediation Design]]
- [[_COMMUNITY_make_entry|make_entry]]
- [[_COMMUNITY_test_parse.py|test_parse.py]]
- [[_COMMUNITY_test_units.py|test_units.py]]
- [[_COMMUNITY_ObservableEntry|ObservableEntry]]
- [[_COMMUNITY_Task 7 Implementation Report|Task 7 Implementation Report]]
- [[_COMMUNITY_task-7-brief|task-7-brief.md]]
- [[_COMMUNITY_task-8-brief|task-8-brief.md]]
- [[_COMMUNITY_task-9-brief|task-9-brief.md]]
- [[_COMMUNITY_review_delta|review_delta]]
- [[_COMMUNITY_Task 9 Implementation Report|Task 9 Implementation Report]]
- [[_COMMUNITY_Task 8 Implementation Report|Task 8 Implementation Report]]
- [[_COMMUNITY_conftest.py|conftest.py]]

## God Nodes (most connected - your core abstractions)
1. `make_entry()` - 46 edges
2. `make_capture()` - 33 edges
3. `review_delta()` - 31 edges
4. `QualityVerdict` - 26 edges
5. `Project Noor — Testing Standards` - 21 edges
6. `glucose_capture()` - 20 edges
7. `NoorModel` - 19 edges
8. `ObservableEntry` - 19 edges
9. `Project Noor — CDS Engine Architecture` - 19 edges
10. `Task 5 Report: Unit Resolution` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_a_recorded_conversion_multiplier_must_be_positive()` --calls--> `ConversionApplied`  [INFERRED]
  tests/canon/test_models.py → src/noor/canon/models.py
- `test_a_canonical_value_requires_a_resolved_unit()` --calls--> `CanonicalQuantity`  [INFERRED]
  tests/canon/test_models.py → src/noor/canon/models.py
- `test_an_accepted_observation_with_a_canonical_value_is_accepted()` --calls--> `CanonicalQuantity`  [INFERRED]
  tests/canon/test_models.py → src/noor/canon/models.py
- `test_a_comparable_delta_names_its_baseline_and_its_change()` --calls--> `DeltaVerdict`  [INFERRED]
  tests/canon/test_models.py → src/noor/canon/models.py
- `test_a_comparable_delta_without_a_baseline_is_refused()` --calls--> `DeltaVerdict`  [INFERRED]
  tests/canon/test_models.py → src/noor/canon/models.py

## Import Cycles
- None detected.

## Communities (72 total, 16 thin omitted)

### Community 0 - "Project Noor — CDS Engine Architecture"
Cohesion: 0.18
Nodes (10): 0.1 Document map, 0.2 Table of contents, 0. How to use this document, 14. Build sequence, 17. Research index, 4.1 Layout, 4.2 The enforced seam, 4.3 Why an evaluator and not an inference engine (+2 more)

### Community 1 - "11. Topics raised during the design interview"
Cohesion: 0.06
Nodes (34): 11.10 Emergency handling, 11.11 Validation sandbox and accelerator path, 11.12 Rule authoring and clinical governance, 11.13 Duplicate data entry: the friction problem, 11.1 Data validity and error mitigation, 11.2 Lab validity windows and pre-visit gating, 11.3 Supervisor review and queue triage, 11.4 Care-plan amendment and patient contact (+26 more)

### Community 2 - "Project Noor — Testing Standards"
Cohesion: 0.06
Nodes (31): Adding a new CDS rule, Authentication, Case file shape, Case selection: boundary plus pairwise, Core mental model, Coverage targets, Database test strategy, Invariant tests (+23 more)

### Community 3 - "5. Interoperability and integration"
Cohesion: 0.07
Nodes (29): 1. FHIR version policy: R4 now, R5 only behind an adapter, 2. Noor R4 profile set, 3. CDS Hooks: excellent adapter target, wrong MVP dependency, 4. CQL and FHIR Clinical Reasoning: adopt the information model, defer CQL as the primary runtime, 5. Engines and reusable components, 5. Interoperability and integration, 6. IPS: support as an export/import boundary, not the internal database, 7. Saudi EMR integration reality (+21 more)

### Community 4 - "6. Risk models and scores (only those we might actually compute)"
Cohesion: 0.07
Nodes (29): 1. Kidney Failure Risk Equation (KFRE), 2. Hypoglycaemia risk prediction in older adults, 3. FIB-4 and other MASLD/NAFLD fibrosis scores, 4. IWGDF diabetic-foot-ulcer risk stratification, 5. Ten-year cardiovascular risk, 6. BP variability and the honest “trajectory” feature, 6. Risk models and scores (only those we might actually compute), Build order and release gates (+21 more)

### Community 5 - "11. Clinical operations"
Cohesion: 0.08
Nodes (26): 11.10 Offline — specified, not built, 11.1 Registration and baseline, 11.2 The visit state machine, 11.3 Triggers in operation, 11.4 The pre-visit brief, 11.5 The in-home visit loop, 11.6 Planned actions, 11.7 The emergency hatch (+18 more)

### Community 6 - "3. Drug knowledge base — the build-vs-license decision"
Cohesion: 0.08
Nodes (25): 1. What the base must cover, 2. Vendor and source options, 3. Drug knowledge base — the build-vs-license decision, 3. Is there a credible free source usable commercially?, 4. Concrete fallback: a bounded high-severity set, 5. Allergy cross-reactivity: the model should be phenotype- and structure-aware, 6. Renal, hepatic, maximum-dose, and drug–disease logic, 7. Pregnancy and lactation (+17 more)

### Community 7 - "2. Saudi regulatory, legal, and health-system context"
Cohesion: 0.08
Nodes (25): 2.1 SFDA: device status, scope, classification, and route, 2.2 PDPL and SDAIA: health-data operating model, 2.3 MOH digital health, NPHIES, and integration reality, 2.4 Workforce, home healthcare, formulary, and prescribing, 2.5 Liability, accountability, and language, 2. Saudi regulatory, legal, and health-system context, Arabic requirements, Classification, conformity route, costs, timeline, and entity status (+17 more)

### Community 8 - "1. Clinical guidelines — the content source of truth"
Cohesion: 0.08
Nodes (23): 1.1 Diabetes (P0), 1.2 Hypertension (P0), 1.3 Chronic kidney disease (P0), 1.3 CKD — explicit potassium/creatinine schedule, 1.4 Lipids and cardiovascular risk (P1), 1.4 Lipids — Saudi risk bands, statins, and calibration, 1.5 Geriatrics — Clinical Frailty Scale rights are resolved, 1.5 Geriatrics, polypharmacy, and deprescribing (P1) (+15 more)

### Community 9 - "8. Competitive and market landscape"
Cohesion: 0.09
Nodes (22): 1. Health Clusters / Health Holding Company: primary strategic buyer, 2. Integrated private hospital groups and home-health providers: best first commercial pilot, 3. Payers/CHI and insurer-sponsored disease management: secondary buyer and partnership route, 4. Pharma-sponsored programmes: channel, not clinical-governance owner, 8.1 Competitive map: global CDS and knowledge incumbents, 8.2 Saudi and Gulf adjacent players, 8.3 Why an apparent home-health “gap” exists—and why that is not automatically white space, 8.4 Buyers, budget holders, and routes to market (+14 more)

### Community 10 - "cds-safety-and-human-factors.md"
Cohesion: 0.10
Nodes (20): 1. Alert fatigue: treat high override rates as a signal to investigate, not a benchmark to accept, 2. What makes CDS effective: retain the principles, operationalise them, 3. Known CDS harms: build the safety case around concrete failure modes, 4. Automation bias in junior clinicians: a real concern, but not one with a junior-doctor-only effect estimate, 5. Communicating uncertainty and provenance, 6. Does home-based chronic disease management improve outcomes?, 7. CDS safety, effectiveness, and human factors, 7. Medication reconciliation and pill counts: useful evidence, not a truth test (+12 more)

### Community 11 - "9. Technical architecture references"
Cohesion: 0.10
Nodes (20): 1. Rule-engine choice, 2. Making rules genuinely clinician-reviewable, 3. Versioning, provenance, and reproducibility, 4. Temporal clinical-data model, 5. Audit logging: security audit, clinical provenance, and workflow evidence, 6. Testing and validation strategy, 7. Build sequence and concrete deliverables, 9. Technical architecture references (+12 more)

### Community 12 - "4. Terminology, coding, and identifiers"
Cohesion: 0.12
Nodes (16): 1. Canonical roles and non-negotiable record fields, 2. LOINC: permitted commercial use and the initial observation compendium, 3. SNOMED CT: Saudi availability, licensing, and scope, 4. ICD-10-AM and Saudi billing: use as a bounded administrative layer, 4. Terminology, coding, and identifiers, 5. Medicines: RxNorm is not the Saudi identifier; build a Saudi product mapping layer, 6. ATC: appropriate for classes, not clinical equivalence, 7. UCUM and unit safety (+8 more)

### Community 13 - "Behavioral Guidelines"
Cohesion: 0.13
Nodes (14): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, 5. Skill & MCP Use, 6. Before Implementing Any Business Logic, Behavioral Guidelines, Behavioral Rules (+6 more)

### Community 14 - "Behavioral Guidelines"
Cohesion: 0.13
Nodes (14): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, 5. Skill & MCP Use, 6. Before Implementing Any Business Logic, Behavioral Guidelines, Behavioral Rules (+6 more)

### Community 15 - "2. Regulatory and compliance posture"
Cohesion: 0.15
Nodes (13): 2.1 Assume regulated SaMD, 2.2 The device boundary is a code boundary, 2.3 Data residency and privacy, 2.4 Clinical content copyright, 2.5 Erasure and the immutable record, 2.6 Access control and the security audit log, 2. Regulatory and compliance posture, Consequences, stated rather than discovered (+5 more)

### Community 16 - "3.2 Medication knowledge"
Cohesion: 0.17
Nodes (12): 3.1 Decisions, 3.2 Medication knowledge, 3.3 Terminology, 3.4 Not in the stack, 3.5 Hosting: deliberately undecided, 3. Technology stack, Local formulary, Medication identity (+4 more)

### Community 17 - "saudi-essential-medicines-list-2023.md"
Cohesion: 0.17
Nodes (11): 7.1.1 Access group antibiotics, 7.1 Antibiotics for systemic use, 7.3.1 Anti-herpes medicines, 7.3.2.1 Nucleoside/Nucleotide reverse transcriptase inhibitors, 7.3.2 Antiretrovirals, 7.3 Antiviral medicines, 7. Anti-infective medicines, 9.2.1 Cytotoxic medicines (+3 more)

### Community 18 - "5. The observation model"
Cohesion: 0.22
Nodes (9): 5.1 Freshness is not a property of an observation, 5.2 Derived values preserve provenance, 5.3 Context flags, 5.4 Informant, 5.5 The allergy record, 5.6 Individualized Goals of Care, 5.7 The named medicine-manager, 5. The observation model (+1 more)

### Community 19 - "6. `canon` — the data-validity layer"
Cohesion: 0.25
Nodes (8): 6.1 Three layers, 6.2 Quality states, 6.3 Unit resolution is a hard safety control, 6.4 Three separate boundary types per observable, 6.5 Repeat before action, 6.6 The observable registry, 6. `canon` — the data-validity layer, The Curated Clinical Signal Set

### Community 20 - "10. Clinical content governance"
Cohesion: 0.29
Nodes (7): 10.1 Release lifecycle, 10.2 Roles, 10.3 Role doubling is recorded, not hidden, 10.4 CI gates on content, 10.5 Tenant profiles, 10. Clinical content governance, The release note is classified, not narrated

### Community 21 - "7. Rule schema and catalogue"
Cohesion: 0.29
Nodes (7): 7.1 The rule, 7.2 Authored prose is three fields; the card renders seven, 7.3 Thresholds, 7.4 Content layout, 7.5 Storage and approval: YAML in git, 7. Rule schema and catalogue, The card names its patient

### Community 22 - "File structure"
Cohesion: 0.10
Nodes (20): Assumptions and interpretations (read before executing), Claims the persistence plan must carry, Execution record — Tasks 1–3 (reviewed 2026-08-19), Exit verification — SSOT §14 steps 1–3, File structure, Foundation + `canon` Implementation Plan, Global Constraints, Task 10: The `canonicalise` pipeline (+12 more)

### Community 23 - "12. Testing and validation"
Cohesion: 0.25
Nodes (8): 12.1 The ladder, 12.2 Release comparison, 12.3 Case selection, 12.4 Synthetic data, 12.5 Calibrated-reliance audit, 12.6 Clinical-operations verification claims, 12.7 Shadow mode, 12. Testing and validation

### Community 24 - "test_models.py"
Cohesion: 0.06
Nodes (58): datetime, CanonicalObservation, DeltaVerdict, Informant, QualityVerdict, Exactly as captured. The value stays a string until parse validates it., What delta review compared, or why it compared nothing (§5, §6.1).      Always r, Canon's intrinsic verdict on one observation (SSOT §6.2).      `unit_resolution` (+50 more)

### Community 25 - "Task 3 Report: The Observation Model and Quality Verdicts"
Cohesion: 0.05
Nodes (43): Baseline, Changed Files, Commit, Coverage Concern, Cyclic Payload Fix, Final Container Fix, Final Edge-Case Fixes, Final Review Findings Addressed (+35 more)

### Community 26 - "models.py"
Cohesion: 0.07
Nodes (35): AcceptedVia, Arm, CuffSize, EntryMode, _freeze_mapping(), _freeze_payload(), InformantRole, MappingInfo (+27 more)

### Community 27 - "Task 2 Report: CI and the Import-Direction Seam Test"
Cohesion: 0.08
Nodes (25): Branch Protection, CI-equivalent coverage command, Clean initial seam run, Concerns, Context and Scope, Exact repository-wide checks, Files Implemented, Fix Commit and Self-Review (+17 more)

### Community 28 - "test_import_direction.py"
Cohesion: 0.29
Nodes (14): _called_attributes(), _called_builtin_functions(), _identifiers(), _imported_modules(), Path, _python_files(), The device-boundary seam test (SSOT §4.2).  `app` imports from `canon`, `engine`, Every name the code *uses* — not comments or docstrings, which may say     "thre (+6 more)

### Community 29 - "Task 1 Implementation Report"
Cohesion: 0.22
Nodes (8): Changed Files, Commands And Results, Commit, Concerns, Self-Review, Status, Task 1 Implementation Report, TDD Evidence

### Community 30 - "8. Evaluation"
Cohesion: 0.33
Nodes (6): 8.1 The call, 8.2 Every rule considered writes a record, 8.3 The degradation invariant, 8.4 Engine invariants, 8.5 Engine failure semantics, 8. Evaluation

### Community 31 - "15. Deferred"
Cohesion: 0.40
Nodes (5): 15.1 Phase 2 — needs a named provider, 15.2 Phase 2 — needs evidence or validation, 15.3 Rejected outright, 15. Deferred, The connectivity assumption, stated rather than implied

### Community 32 - "13. Gates"
Cohesion: 0.50
Nodes (4): 13.1 Blocks code (2), 13.2 Blocks patient use, not code (14), 13.3 Explicitly unresolved, 13. Gates

### Community 33 - "16. Open questions"
Cohesion: 0.50
Nodes (4): 16.1 Questions that block business, not behaviour, 16.2 Questions that block behaviour, 16.3 What is genuinely unanswerable here, 16. Open questions

### Community 34 - "4. Module architecture"
Cohesion: 0.67
Nodes (3): 1.1 What Noor is not, 1.2 First build target, 1. What Noor is

### Community 35 - "9. Findings, alerts, overrides"
Cohesion: 0.50
Nodes (4): 9.1 Three severities, 9.2 Overrides, 9.3 Safety surveillance, 9. Findings, alerts, overrides

### Community 47 - "test_registry.py"
Cohesion: 0.12
Nodes (27): CanonicalQuantity, ConversionApplied, The conversion that produced a canonical value (SSOT §6.3: "every     conversion, Derived, and it shows its work (§5, §6.3).      `conversion_applied` is None exa, from_canonical(), Decimal, Unit resolution and registry-declared conversion (SSOT §6.3).  Resolution is bli, No registry declaration covers the requested unit, or a value's recorded     con (+19 more)

### Community 49 - "Task 4 Implementation Report"
Cohesion: 0.20
Nodes (9): Concerns, Files changed, Implementation, Important Finding Fixes, Status, Task 4 Implementation Report, TDD Evidence, Verification (+1 more)

### Community 50 - "Task 5 Report: Unit Resolution"
Cohesion: 0.11
Nodes (18): Blocking Conflict, Changes Made, Uncommitted, Clarification Applied, Commit, Context Verified, Final Commit, Final Files, Final Verification (+10 more)

### Community 51 - "load_registry"
Cohesion: 0.15
Nodes (16): MappingNode, _ContentLoader, load_registry(), Any, Path, Loads registry content into validated models (SSOT §7.4).  Schema-only YAML (§7., The `SafeLoader` subclass §7.5 allows, refusing a repeated mapping key.      Sto, Load and validate an observable registry file (content/observables/registry.yaml (+8 more)

### Community 53 - "Task 6 Report: Conversion Round-Trip Property"
Cohesion: 0.25
Nodes (7): Concerns, Implementation, Review Remediation, Status, Task 6 Report: Conversion Round-Trip Property, Verification, Verification After Remediation

### Community 55 - "Coverage Fix Report"
Cohesion: 0.29
Nodes (6): Commit(s), Concerns, Coverage Fix Report, Report Path, Status, Test Summary

### Community 56 - "Whole-Branch Review Remediation Report"
Cohesion: 0.20
Nodes (9): Commits, Finding 1: Deep Registry Immutability, Finding 2: Quality Verdict Contradictions, Finding 3: Missing Noncanonical Conversion, Finding 4: Bogus Provenance Source Unit, Scope and Concerns, Status, Verification (+1 more)

### Community 57 - "Final Whole-Branch Review Fix Report"
Cohesion: 0.20
Nodes (9): Commits, Final Whole-Branch Review Fix Report, Finding 1: Registry Immutability, Finding 2: Quality Verdict Consistency, Finding 3: Duplicate Conversion Sources, Finding 4: Testing Standards Documentation, Scope and Concerns, Status (+1 more)

### Community 58 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Task 1: Registry Immutability and Validation, Task 2: Verdict Consistency, Task 3: Provenance Source-Unit Validation, Task 4: Full Verification and Report, Whole-Branch Review Remediation Implementation Plan

### Community 59 - "Whole-Branch Review Remediation Design"
Cohesion: 0.40
Nodes (4): Design, Goal, Verification, Whole-Branch Review Remediation Design

### Community 60 - "make_entry"
Cohesion: 0.15
Nodes (22): Envelope, Inclusive bounds in the canonical unit, versioned independently (§6.4)., The registry validates itself at load (SSOT §6.4, §6.6)., test_a_code_unit_map_entry_must_name_an_accepted_unit(), test_a_code_unit_map_key_must_be_a_nonempty_system_pipe_code_pair(), test_a_conversion_from_an_unaccepted_unit_is_rejected(), test_a_conversion_must_convert_from_an_accepted_non_canonical_unit(), test_a_well_formed_entry_validates() (+14 more)

### Community 61 - "test_parse.py"
Cohesion: 0.23
Nodes (10): decimal_transposition_suspected(), parse_value(), Decimal, Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1).  Stric, Parse an as-reported value, or return None when it is unparseable.      The patt, True when sliding the decimal point one place would move the value inside     th, Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1)., test_a_malformed_value_is_unparseable() (+2 more)

### Community 62 - "test_units.py"
Cohesion: 0.21
Nodes (16): SourceCode, Conversion, canonical = (value + add) * multiply, quantised to `precision` (§6.3).      `tol, Resolve the unit a value arrived in (§6.3).      explicit: the source stated a u, resolve_unit(), test_a_conversion_multiplier_must_be_positive(), Unit resolution is a hard safety control (SSOT §6.3)., test_a_declared_conversion_records_the_provenance_of_its_result() (+8 more)

### Community 64 - "ObservableEntry"
Cohesion: 0.15
Nodes (12): BaseModel, KeyError, NoorModel, DeltaPolicy, ObservableEntry, ObservableRegistry, The observable registry: per-observable data-validity declarations (SSOT §6.6)., A capture named an observable the registry does not govern. (+4 more)

### Community 65 - "Task 7 Implementation Report"
Cohesion: 0.22
Nodes (8): Concerns, Files Changed, GREEN, RED, Self-Review, Task 7 Implementation Report, TDD Evidence, Verification

### Community 69 - "review_delta"
Cohesion: 0.14
Nodes (39): current_versions(), is_comparable(), Decimal, Layer 3 of canon: delta review (SSOT §6.1 layer 3).  Compares like with like onl, The latest version of each source record (SSOT §5).      A source may correct a, True when `prior` may serve as the delta baseline for `capture`., Compare a canonical value against the most recent comparable accepted prior., review_delta() (+31 more)

### Community 70 - "Task 9 Implementation Report"
Cohesion: 0.17
Nodes (11): Concerns, Files Changed, Fixture Corrections, GREEN, RED, Reviewer Fix, Self-Review, Status (+3 more)

### Community 71 - "Task 8 Implementation Report"
Cohesion: 0.29
Nodes (6): Commands and Results, Concerns, Files Changed, Self-Review, Task 8 Implementation Report, TDD Evidence

### Community 72 - "conftest.py"
Cohesion: 0.29
Nodes (5): The two envelopes (SSOT §6.1 layer 2, §6.4). Bounds are inclusive and declared i, test_a_value_is_placed_against_both_envelopes_with_inclusive_bounds(), Shared builders and fixtures (docs/testing-standards.md: factories live here)., The real content/observables/registry.yaml, loaded and validated., registry()

## Knowledge Gaps
- **511 isolated node(s):** `noor`, `Status`, `Finding 1: Deep Registry Immutability`, `Finding 2: Quality Verdict Contradictions`, `Finding 3: Missing Noncanonical Conversion` (+506 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Project Noor — CDS Engine Architecture` connect `Project Noor — CDS Engine Architecture` to `13. Gates`, `16. Open questions`, `4. Module architecture`, `9. Findings, alerts, overrides`, `11. Clinical operations`, `2. Regulatory and compliance posture`, `3.2 Medication knowledge`, `5. The observation model`, `6. `canon` — the data-validity layer`, `10. Clinical content governance`, `7. Rule schema and catalogue`, `12. Testing and validation`, `8. Evaluation`, `15. Deferred`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `ObservableEntry` connect `ObservableEntry` to `review_delta`, `test_registry.py`, `models.py`, `make_entry`, `test_parse.py`, `test_units.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `make_entry()` connect `make_entry` to `ObservableEntry`, `conftest.py`, `test_registry.py`, `test_models.py`, `test_parse.py`, `test_units.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `make_entry()` (e.g. with `DeltaPolicy` and `Envelope`) actually correct?**
  _`make_entry()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `review_delta()` (e.g. with `test_a_bp_delta_requires_matching_context()` and `test_a_bp_delta_with_matching_context_is_recorded()`) actually correct?**
  _`review_delta()` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `QualityVerdict` (e.g. with `test_a_canonical_value_requires_a_resolved_unit()` and `test_a_consistent_flagged_verdict_is_accepted()`) actually correct?**
  _`QualityVerdict` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `noor`, `Project Noor — a clinical decision support engine for supervised home visits.`, `app — FastAPI, persistence, and the clinical workflow (SSOT §11).  Lives OUTSIDE` to the rest of the system?**
  _570 weakly-connected nodes found - possible documentation gaps or missing edges._