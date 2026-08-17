> Section 4 of the research programme. Indexed in SSOT §17.

# 4. Terminology, coding, and identifiers

## Decision

Adopt a **dual-layer clinical data model**: preserve every source-system identifier and display string exactly as received, while attaching a versioned normalized concept for clinical computation. Use **LOINC + UCUM** for observations, **SNOMED CT** for clinical meaning, **ICD-10-AM** only where a Saudi billing/NPHIES transaction requires it, **ATC** for medication-class analytics and carefully bounded class logic, and an **SFDA product-to-ingredient mapping layer** for medicines. Do not make any one of these terminologies serve the others’ job. [^1][^2][^3][^4][^5]

This is not terminology “cleanup.” It is a patient-safety control: a rule must know whether a result is fasting or random, laboratory or point-of-care, serum or capillary, calculated by which eGFR equation, and reported in which unit before it evaluates a threshold. NPHIES already exposes LOINC, SNOMED CT and ICD-10-AM in its published FHIR material, but its financial-services implementation guide is not a complete clinical-record specification. [^6][^3]

## 1. Canonical roles and non-negotiable record fields

| Data object | Canonical vocabulary | What it is for | Do not use it for |
|---|---|---|---|
| Laboratory, vital-sign, anthropometric and calculated measurements | LOINC plus UCUM | Identifying the *question/result* and its unit, specimen, timing, method and calculation provenance | Diagnoses or drug identity |
| Findings, conditions, allergy manifestations, procedures, care context | SNOMED CT | Computable clinical meaning, hierarchy and synonymy | Reimbursement/billing claims |
| Claim and authorization diagnosis coding | ICD-10-AM, where the NPHIES profile requires it | Saudi financial/administrative exchange | The sole clinical problem list or an inference engine |
| Drug class | WHO ATC | Hierarchical class/grouping for duplicate-therapy review, population analytics and carefully reviewed class-level policies | Local trade-name normalization or a full medication knowledge base |
| Saudi medicine product | SFDA registration/product record, local provider formulary and a Noor ingredient concept | Local trade name, presentation, registration status, SPC/PIL, availability and formulary facts | A generic international identifier substitute |
| Dose/unit expression | UCUM | Machine-safe conversion, validation and display normalization | A unit-free string such as “7” or “normal” |

[^1][^2][^3][^4][^5]

Each incoming item should retain: `source_system`, `source_identifier`, `source_display`, `received_at`, `reported_at`, `effective_time`, `mapping_status`, `mapping_version`, `terminology_version`, `normalization_confidence`, and the original payload. Each normalized observation additionally needs `loinc`, `value`, `ucum_unit`, `specimen`, `method`, `device_or_assay`, `fasting_status`, `collection_context`, `reference_range`, and `result_status`. A medication needs separate identity fields for product, brand, ingredient(s), salt, dose form, strength, route, modified-release status, local registration identifier, ATC code(s), and mapping provenance. This preserves auditability when a mapping or terminology release changes. [^1][^7]

## 2. LOINC: permitted commercial use and the initial observation compendium

LOINC is not merely “free with registration.” Its published license grants perpetual, no-fee use, copying and distribution for commercial or non-commercial purposes, subject to conditions. A product incorporating LOINC must carry the prescribed attribution, preserve the associated identifier/display name, and respect any separate third-party rights identified in the release. [^1]

**Implementation consequence:** use a pinned LOINC release and store its version alongside every mapping. Put the required LOINC notice in Noor’s legal/terms screen. Do not translate or alter LOINC terms as if they were Noor-owned text; keep an Arabic user-interface label in a separate field. LOINC specifically treats translations as derivative works and requires prior notification. [^1]

### Initial LOINC/UCUM configuration list

These are **preferred starting mappings**, not permission to overwrite an inbound laboratory’s more specific valid code. The receiving-lab compendium and test method decide the final mapping. Maintain a `local_test_code → LOINC` map approved by that laboratory’s pathologist/clinical chemist, with a test-case specimen for every production interface. [^7][^1]

| Clinical datum | Preferred LOINC | Preferred UCUM representation | Required qualifiers / selection rationale |
|---|---:|---|---|
| HbA1c, NGSP/DCCT-style percentage | `4548-4` | `%` | Store assay/method and standardization. Use only when the source reports the conventional percentage result; do not treat this as interchangeable with IFCC mmol/mol. |
| HbA1c, IFCC reference-system result | `59261-8` | `mmol/mol` | The LOINC term is explicitly IFCC-standardized. It is a distinct observation from percentage reporting; retain the source’s result, and calculate/display a converted companion only when clinically approved. [^8] |
| Plasma/serum glucose, unspecified/random | `2345-7` | `mg/dL` or `mmol/L` | Never infer fasting state from the value. Store the timing/fasting assertion separately. |
| Plasma/serum fasting glucose | `1558-6` | `mg/dL` or `mmol/L` | Use only when fasting is explicitly documented by the laboratory/order/workflow. |
| Point-of-care capillary glucose by glucometer | `41653-7` | `mg/dL` or `mmol/L` | Preserve device, capillary specimen and POC context; do not substitute a serum/plasma code. |
| Serum/plasma creatinine | `2160-0` | `mg/dL` or `umol/L` | Preserve specimen and method; result feeds eGFR only if temporally suitable. |
| eGFR, CKD-EPI 2021 creatinine calculation | `98979-8` | `mL/min/{1.73_m2}` | Prefer when the reporting laboratory confirms CKD-EPI 2021 creatinine. LOINC distinguishes the 2021 creatinine-only calculation from creatinine-plus-cystatin-C; it recommends a new result field/code when the calculation changes. [^7] |
| eGFR, CKD-EPI 2021 creatinine+cystatin C | `98980-6` | `mL/min/{1.73_m2}` | Use only when that combined equation actually generated the result. |
| Potassium, serum/plasma | `2823-3` | `mmol/L` | Capture hemolysis/index and result status where supplied; a spurious potassium result must not trigger a medication alert unqualified. |
| Sodium, serum/plasma | `2951-2` | `mmol/L` | Store specimen/method rather than assuming all sodium results are equivalent. |
| Urine albumin:creatinine ratio | `9318-7` | `mg/g` or `mg/mmol` | Store the laboratory-reported ratio and unit; do not calculate from separately timed albumin/creatinine measurements unless the laboratory and clinical owner approve the derivation. |
| Lipid panel | `24331-1` | panel (member units below) | Preserve individual members; a panel code alone is not enough for risk logic. |
| Total cholesterol | `2093-3` | `mg/dL` or `mmol/L` | Record fasting status where provided, but do not make it a universal validity gate. |
| HDL cholesterol | `2085-9` | `mg/dL` or `mmol/L` | Preserve assay/method where supplied. |
| LDL cholesterol, calculated | `13457-7` | `mg/dL` or `mmol/L` | Label as *calculated*; it is not equivalent to direct LDL in every clinical setting. |
| Triglycerides | `2571-8` | `mg/dL` or `mmol/L` | Keep fasting state and analytic context. |
| Blood-pressure panel | `85354-9` | panel | Use a panel/linked readings when possible so systolic and diastolic values retain the same measurement event. |
| Systolic blood pressure | `8480-6` | `mm[Hg]` | Required metadata: posture, arm, cuff size, device, rest duration, reading ordinal, setting (home/office/ambulatory), and averaged/not-averaged status. |
| Diastolic blood pressure | `8462-4` | `mm[Hg]` | Same event metadata as systolic. |
| Orthostatic BP | posture-specific LOINC terms selected from the receiving device/lab compendium | `mm[Hg]` | Do **not** collapse “orthostatic BP” into one made-up code. Represent each systolic/diastolic reading with posture (`lying`, `seated`, `standing`) and elapsed time after standing; calculate the paired change from linked observations. |
| Body weight | `29463-7` | `kg` | Store measurement conditions where material (e.g., dry weight/edema context) rather than only a number. |
| Body height | `8302-2` | `cm` | Store measured versus patient-reported status. |
| Body mass index | `39156-5` | `kg/m2` | Prefer storing height and weight too; BMI can be recomputed and quality-checked. |
| Heart rate | `8867-4` | `/min` | Store measurement modality and rhythm context when available; pulse rate is not necessarily ECG rate. |

### “LOINC versus the right LOINC” rules

1. **Never normalize by display name alone.** Map the full axis set—component, property, time, system/specimen, scale and method—plus clinical workflow context.
2. **HbA1c is a standardization problem, not a simple unit conversion.** IFCC and NGSP values are linked by a validated equation but represent differently scaled reporting conventions; retain both the original unit/standard and the instrument/laboratory identity. IFCC reports mmol/mol, while conventional clinical targets often use NGSP percentage. [^9]
3. **eGFR must preserve equation provenance.** LOINC’s own guidance states that the 2021 creatinine and creatinine+cystatin-C equations have separate codes and advises a new result field after a calculation change to preserve historical integrity. [^7]
4. **Do not recompute an eGFR silently.** Keep `reported_egfr`, `reported_loinc`, `reported_equation`, `reported_unit`, creatinine, patient demographic variables used by the laboratory if available, and a separate `noor_derived_egfr` only if a clinical owner approves an explicit calculation policy.
5. **Do not convert a result merely for display without retaining the original.** Conversions must be deterministic, version-tested, round-trip tested and visibly labelled.

## 3. SNOMED CT: Saudi availability, licensing, and scope

Saudi Arabia is a SNOMED International Member; the National Health Information Center (NHIC) is the Kingdom’s representative and is responsible for distributing/managing SNOMED CT and developing content for Saudi requirements. [^2][^10] This removes the expected licence fee for use **in Saudi Arabia**, but it does not remove the licence/registration step. SNOMED International states that deployment in a Member country requires a free Affiliate License through that country’s national-release route, and that use across multiple Member countries requires separate licences. [^11]

**Decision:** register Noor’s Saudi use and obtain the current International Edition and any Saudi extension through the documented Saudi/MLDS route before production. Do not rely on a public browser or copied spreadsheet as a production terminology service. The Saudi distribution listing currently routes Saudi Arabia through MLDS; the integration owner should record the Edition, release date, effective-time and module dependencies in the build manifest. [^12]

**Use SNOMED CT for:**

- active diagnoses and clinical findings, including phenotype/severity rather than only billing labels;
- allergy/intolerance *substance plus reaction manifestation* and certainty/status;
- procedures, care activities, symptoms, family history, smoking status and relevant social context;
- clinical observations where a coded value is needed beyond the numerical LOINC result;
- a versioned reference set for the Noor minimum data set. [^2]

**Do not use SNOMED CT as:** a substitute for local product identity, a billing code, a dose instruction language, or a generic reason to infer a disease from a medication. A `Condition` should retain both its asserted SNOMED concept and, when available, its source ICD-10-AM code/mapping; neither should overwrite the other. [^3][^2]

For allergies, require `culprit_substance`, `reaction`, `onset/timing`, `reaction_type` (immune/immediate, delayed, intolerance, unknown), `severity`, `verification_status`, `recorder`, and `evidence_source`. A bare “penicillin allergy” is insufficient for safe class logic. [^2]

## 4. ICD-10-AM and Saudi billing: use as a bounded administrative layer

The published NPHIES healthcare financial-services guide exposes an **ICD-10-AM** diagnosis value set, versioned as 1.0.0 and active on 9 January 2025, based on the ICD-10-AM system. [^3] NPHIES also identifies the related Saudi Billing System as an ACHI-derived system extended by the Council of Health Insurance. [^6]

**Decision:** for any NPHIES claim/authorization interface, emit the NPHIES-required ICD-10-AM representation exactly as its current profile/terminology service dictates. For the Noor internal longitudinal problem list and clinical rules, use SNOMED CT as the primary clinical concept and retain the billing code as an additional, purpose-limited coding. This prevents loss of clinical detail and prevents an administrative code from being treated as a diagnosis assertion. [^3][^2]

**Licensing caveat:** WHO states that it owns ICD-10 copyright and licences commercial incorporation; it also says national modifications are governed by their relevant authorities. The NPHIES implementation guide itself carries ICD-10-AM copyright/permission notices. Therefore, a commercial product that distributes an ICD-10-AM browser, code descriptions or derived coding service needs written licensing/usage confirmation from the relevant Saudi/NPHIES and Australian/WHO rights holders—not an assumption based on public web access. [^13][^6]

## 5. Medicines: RxNorm is not the Saudi identifier; build a Saudi product mapping layer

RxNorm can be a useful **optional international crosswalk**, especially to normalized ingredients and ATC relationships, but it cannot be Noor’s canonical Saudi medication catalogue. NLM explicitly describes RxNorm as US-centric, containing few if any non-US drugs; its product mapping supports US NDC identifiers, which are not Saudi registrations. [^14]

The Saudi anchor is the SFDA Drugs List and Saudi Drug Information system (SDI): SFDA’s public Drugs List exposes searches by trade name, scientific name, manufacturer and registration number, while SDI is designed as a reference for registered medicines and holds company/agent-uploaded PILs and SPCs. [^15][^16]

### Required medication identity model

| Layer | Identifier/content | Use |
|---|---|---|
| Local product | SFDA registration number; product/trade name; manufacturer/agent; local formulation/strength/route; registration/status query date | Dispensing/formulary identity, Saudi label and availability review |
| Noor normalized medicinal product | Stable internal identifier with ingredient set, salt/base relationship, dose form, route, strength, release type and source mapping | Safe joining of provider medication lists and rules |
| Ingredient | A normalized active-ingredient concept, with mapping provenance to SFDA scientific name and optional RxNorm/SNOMED identifier | Interaction, allergy, duplicate-therapy and guideline logic |
| Class | ATC code(s), edition/year, level and mapping source | Cohort/group logic; never the only determinant of a patient-specific alert |
| Knowledge source | Local SPC/PIL version, provider formulary version, medication-knowledge vendor identifier/version | Decision support provenance and audit |

[^15][^16][^14][^4]

**Mapping workflow:** (1) ingest SFDA trade/scientific name and registration number; (2) normalize to ingredient(s), salt, form, route, strength and release type; (3) confirm against the relevant Saudi SPC and provider formulary; (4) attach ATC and optional RxNorm/SNOMED crosswalks; (5) route ambiguous combination products, transliterations and near-name matches to pharmacist review; (6) version every accepted mapping and never auto-map on fuzzy name similarity alone. A local product can change presentation or registration while preserving the same ingredient; a fixed-dose combination must remain a multi-ingredient product, not a single string. [^15][^16]

## 6. ATC: appropriate for classes, not clinical equivalence

The WHO Collaborating Centre maintains ATC/DDD; the classification has five hierarchical levels from anatomical group to chemical substance and is updated annually. [^4] It is useful for class-level views, duplicate-therapy candidates, formulary reporting and a first-pass scope filter for a rule review.

It is **not** enough for a medication decision. One ingredient can have multiple ATC codes depending on therapeutic use, and a shared ATC group does not prove equal contraindications, renal thresholds, route, dose or allergy cross-reactivity. Make each rule declare whether it operates at `ingredient`, `ingredient+route`, `product`, `ATC level`, or explicit manually curated set; use the narrowest defensible scope. [^4]

The retrieved official material identifies a WHOCC copyright contact, but did not establish a blanket commercial redistribution right for the full ATC index. Obtain current WHOCC terms or a written licence determination before packaging/distributing the ATC code and title set in a commercial product; do not assume that access through RxNorm grants independent redistribution rights. [^4]

## 7. UCUM and unit safety

UCUM is a direct fit for Noor. Its current license grants a worldwide, royalty-free licence to reproduce, display and distribute the work and to develop/commercialize interoperating software, provided the standard’s meaning is not changed and attribution/notice conditions are respected on redistribution. [^5]

### Unit policy

- Store the **received unit string** and the normalized **UCUM code** separately.
- Permit calculations only after a `unit_validated = true` check against the LOINC/local-test mapping.
- Reject or quarantine impossible/mismatched pairs—e.g., creatinine recorded as mmol/L, a BP without `mm[Hg]`, or HbA1c percentage stored as mmol/mol.
- Keep raw and converted result values; record conversion algorithm/version, precision and rounding policy.
- Convert only for internal display/rules when the observation type is unambiguous. Never convert an untyped “glucose” or “cholesterol” field. [^5][^1]

**Saudi unit conclusion:** this search did not find a single authoritative national Saudi laboratory-unit mandate covering all vendors and care settings. Treat unit as an interface-level fact, not a national default. Noor should accept both `mg/dL` and `mmol/L` for glucose and lipids and both `%` and `mmol/mol` for HbA1c, then normalize only with explicit LOINC/unit context. The Saudi dyslipidaemia guideline itself uses mmol/L values alongside mg/dL equivalents, which reinforces the need to support both rather than assume one. [^9][^17]

For HbA1c, use the source laboratory’s reported unit as authoritative. International standardization recognizes the NGSP-to-IFCC relationship, but country reporting choices differ. Noor should display the original measurement first and, if a companion value is displayed, label it as converted rather than reported. [^9]

## 8. Release-ready implementation plan

1. **Publish a terminology charter.** Name the canonical system per data type; prohibit rules from consuming free text or an unqualified numeric value.
2. **Create a terminology service boundary.** Versioned tables/API for LOINC, UCUM, SNOMED CT, ICD-10-AM and ATC, with `effective_time`, release ID, mapping provenance, deprecation status and local overrides.
3. **Build the observation compendium first.** Start with the list above, then validate it against each target provider laboratory/device feed. Add test fixtures for every LOINC/unit/specimen/method combination.
4. **Implement context gates before clinical rules.** No eGFR rule without equation/date/unit; no glucose rule without specimen/context/unit; no BP trend without setting/posture/measurement metadata; no drug rule without a resolved ingredient/form/route.
5. **Register and license.** Add LOINC attribution; obtain SNOMED CT Saudi Affiliate access; obtain a written ICD-10-AM/NPHIES commercial-use position; and resolve ATC redistribution rights before distributing code descriptions.
6. **Build the SFDA medication mapper.** Start from the target provider formulary, record product registration and local SPC version, and require pharmacist approval for every ambiguous mapping.
7. **Prove reversibility and safety.** Test each unit conversion bidirectionally; test mappings against real de-identified examples; log every unmapped/ambiguous input; make “cannot safely normalize” a visible workflow state rather than a silent best guess.
8. **Version in the clinical audit trail.** Every rule execution should record the observation code/unit, terminology release, mapping version, medication concept version, source payload timestamp and any conversion/derivation. [^1][^7][^11][^15][^5]

## Decisions that should not be deferred

- **Adopt LOINC + UCUM now.** Their licensing paths are compatible with commercial product use if Noor includes the required notices and preserves the standard’s semantics. [^1][^5]
- **Adopt SNOMED CT now, but complete free Saudi Affiliate registration before production.** National membership reduces cost; it does not make a copied terminology dump a compliant distribution path. [^2][^11]
- **Use ICD-10-AM only at the NPHIES/billing boundary unless a provider mandates more.** It is visible in current NPHIES terminology material, but needs a separate commercial rights check. [^3][^13]
- **Do not use RxNorm as the Saudi drug master.** Keep it as an optional crosswalk; make SFDA registration and local SPC/formulary data the Saudi product anchor. [^14][^15][^16]
- **Do not code a single national unit convention.** Enforce UCUM and per-interface validation instead. [^5][^9]

## Open release gates

1. Obtain the exact LOINC mapping and result-unit catalogue for the first laboratory and point-of-care devices; no generic code list replaces this.
2. Confirm the current NPHIES ICD-10-AM/Saudi Billing System terminology release and contractual access route with the deployment provider/insurer.
3. Obtain written confirmation from the relevant authority on commercial distribution/display of ICD-10-AM descriptions and ATC index content.
4. Register Noor’s SNOMED CT Affiliate use in Saudi Arabia and capture the release/extension provenance.
5. Select the first 60–80 Saudi formulary ingredients/products and complete pharmacist-approved SFDA-to-ingredient-to-ATC mapping.
6. Establish an interface acceptance test suite including unit mistakes, duplicate names, fixed-dose combinations, local Arabic/English brand synonyms, hemolysed potassium, calculated versus direct LDL, and historical eGFR equation changes. [^7][^12][^15]

The resulting architecture is intentionally conservative: missing context blocks an automated recommendation and prompts reconciliation. That behaviour is safer—and more auditable—than treating a plausible-looking code or number as clinically equivalent to a validated observation. [^7][^5]


[^1]: LOINC License (KB).

[^2]: Saudi Arabia.

[^3]: http://hl7.org/fhir. ICD-10-AM - Healthcare Financial Services IG Edition 1 v1. ...

[^4]: ATC Source Information.

[^5]: UCUM / License.

[^6]: IP Review.

[^7]: Choosing the Correct LOINC for Estimated Glomerular Filtration Rate (KB) - LOINC.

[^8]: 59261-8.

[^9]: IFCC Standardization of HbA1c.

[^10]: The Kingdom of Saudi Arabia joins the SNOMED CT Community.

[^11]: SNOMED CT License : SNOMED International.

[^12]: Member Affiliate Licensing Information - Member Licensing and Distribution Service - SNOMED Spaces.

[^13]: ABOU MRAD. FAQ Licensing ICD-10.

[^14]: RxNorm Frequently Asked Questions.

[^15]: Drugs List | The official website of the Saudi Food and Drug Authority.

[^16]: Saudi Drugs information system (SDI) | The official website of the Saudi Food and Drug Authority.

[^17]: 2022 Saudi Guidelines for the Management of Dyslipidemia.