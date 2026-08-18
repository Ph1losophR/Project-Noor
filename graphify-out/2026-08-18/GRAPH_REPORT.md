# Graph Report - cds_engine  (2026-08-18)

## Corpus Check
- 16 files · ~4,193,549 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 454 nodes · 439 edges · 22 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc55cdcf`
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

## God Nodes (most connected - your core abstractions)
1. `Project Noor — Testing Standards` - 21 edges
2. `Project Noor — CDS Engine Architecture` - 19 edges
3. `11. Topics raised during the design interview` - 17 edges
4. `5. Interoperability and integration` - 12 edges
5. `4. Terminology, coding, and identifiers` - 12 edges
6. `11. Clinical operations` - 11 edges
7. `1. Clinical guidelines — the content source of truth` - 11 edges
8. `3. Drug knowledge base — the build-vs-license decision` - 11 edges
9. `6. Risk models and scores (only those we might actually compute)` - 11 edges
10. `11.2 The visit state machine` - 10 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (22 total, 0 thin omitted)

### Community 0 - "Project Noor — CDS Engine Architecture"
Cohesion: 0.04
Nodes (44): 0.1 Document map, 0.2 Table of contents, 0. How to use this document, 12.1 The ladder, 12.2 Release comparison, 12.3 Case selection, 12.4 Synthetic data, 12.5 Calibrated-reliance audit (+36 more)

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

## Knowledge Gaps
- **343 isolated node(s):** `Current State`, `SSOT Integrity Rules`, `1. Think Before Coding`, `2. Simplicity First`, `3. Surgical Changes` (+338 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Project Noor — CDS Engine Architecture` connect `Project Noor — CDS Engine Architecture` to `11. Clinical operations`, `2. Regulatory and compliance posture`, `3.2 Medication knowledge`, `5. The observation model`, `6. `canon` — the data-validity layer`, `10. Clinical content governance`, `7. Rule schema and catalogue`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `11. Clinical operations` connect `11. Clinical operations` to `Project Noor — CDS Engine Architecture`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `2. Regulatory and compliance posture` connect `2. Regulatory and compliance posture` to `Project Noor — CDS Engine Architecture`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `Current State`, `SSOT Integrity Rules`, `1. Think Before Coding` to the rest of the system?**
  _343 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Project Noor — CDS Engine Architecture` be split into smaller, more focused modules?**
  _Cohesion score 0.044444444444444446 - nodes in this community are weakly interconnected._
- **Should `11. Topics raised during the design interview` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._
- **Should `Project Noor — Testing Standards` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._