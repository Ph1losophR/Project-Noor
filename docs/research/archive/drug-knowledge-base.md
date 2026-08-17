> Section 3 of the research programme. Indexed in SSOT §17.

# 3. Drug knowledge base — the build-vs-license decision

## Decision

**Do not build a general-purpose drug knowledge base. License a production medication-knowledge service for broad, patient-specific checking, and build Noor’s narrow Saudi clinical-policy layer around it.** A home-grown core would have to maintain drug concepts, product/formulation changes, interaction pairs, severity and management text, allergy cross-sensitivity, dose ranges, organ-impairment logic, pregnancy/lactation evidence, and drug–disease contraindications. Commercial knowledge bases disagree substantially on interaction-pair coverage even when they agree more on the most serious category: in one comparison, 79% of unique interaction pairs appeared in only one of three commercial products, while all three covered 99.8–99.9% of the ONC high-priority alerts. [^1]

For Noor, the viable architecture is a **hybrid**:

1. **Licensed global medication layer** for drug identity normalization, DDI, drug–allergy, drug–disease, duplicate therapy, dose range, renal/hepatic adjustment indicators, maximum dose, and clinical-management text.
2. **Saudi product layer** built from SFDA’s Saudi Drug Information (SDI) and the selected provider/payer formulary: ingredient, local brand, route, strength, current SPC/PIL version, availability, prior authorization, and substitute options. SDI is SFDA’s reference system for registered medicines and hosts company/agent-uploaded PILs and SPCs. [^2]
3. **Noor-owned local rules** limited to guidelines, explicit high-severity “must-review” alerts, data-quality gates, escalation workflow, Arabic/English presentation, and vendor-independent provenance. Every alert must retain source, source version, drug concept, patient facts used, rule version, severity, rationale, display time, and clinician disposition.

The build option becomes defensible only for a **bounded safety subset**—not a substitute for licensed comprehensive checking—and only after pharmacist ownership, formal evidence review, regression testing, and release/change control are funded. This is a product-safety decision as much as a cost decision. [^1]

## 1. What the base must cover

A usable medication engine is more than a DDI lookup. It needs separate, versioned objects for:

- **Drug/product identity:** ingredient(s), salt, route, dose form, strength, release type, local brand, and status. Interaction logic must normally run at ingredient level but sometimes depends on route, dose, formulation, or schedule.
- **Clinical assertions:** interaction/contraindication type; direction and mechanism; seriousness; patient modifiers; action; evidence/documentation level; and precise source/version.
- **Patient context:** current and recently stopped medication, renal measure and date, liver disease phenotype/severity, pregnancy/lactation state, age/weight, allergy phenotype and culprit, relevant disease state, laboratory values, and medication indication.
- **Governance:** effective/review/retirement dates, clinical owner, source licence, localization status, test cases, override/disposition, and post-market safety signal. [^1]

Commercial systems package many of these capabilities. DrugBank’s clinical product describes ingredient/product searching and optional interaction, allergy, contraindication, label, and condition modules; its interaction module includes severity, description, and management information. [^3] Medi-Span’s dose database describes checks using patient parameters and includes renal screening, hepatic-adjustment indicators, maximum doses, route constraints, and lifetime maximum dose where applicable. [^4] FDB MedKnowledge similarly markets dosing, drug–disease, drug–interaction, and drug-allergy support, including a Middle East regional version. [^5]

## 2. Vendor and source options

| Option | What the public material establishes | Fit for Noor | Commercial/licensing reality |
|---|---|---|---|
| **DrugBank Clinical API** | Modular API: product concepts, ATC cross-mapping, drug interactions, allergy cross-sensitivity, contraindications and US labels. [^3] | A credible integration-first candidate if an acceptable Saudi/local product-mapping plan is demonstrated in a sandbox. | Its public terms allow only internal non-clinical educational/research use unless a commercial subscriber order is executed; they prohibit commercial exploitation and safety-critical use under the public terms. [^6] Price is quote-only on the retrieved public page; request a production, Saudi deployment, caching/offline, audit, indemnity, update-SLA, and sublicensing quote. |
| **Micromedex (Merative)** | Reference content covers dosing, interactions, toxicology, alternative medicines/botanicals and international drug names; it is described as daily updated and usable in EHR workflows. [^7] | Strong shortlist candidate where broad monographs, toxicology and botanicals matter. Confirm that the contracted product exposes machine-readable CDS/API rights, not merely human point-of-care access. | Public material is subscription/demo oriented and no production API price was posted in the retrieved material. Obtain a written enterprise quote and data-rights schedule. |
| **UpToDate Lexidrug / Medi-Span (Wolters Kluwer)** | Lexidrug advertises renal/hepatic dosing, drug–drug and herb interactions; Medi-Span offers API/web-service/flat-file delivery and robust DDI, allergy, duplicate therapy, dosing, and contraindication modules. [^8][^9] | Strong shortlist candidate for an embedded medication-safety layer. Its differentiated strength is breadth of discrete content modules, but much public detail is US-centric, so Saudi product coverage must be proven rather than assumed. | Enterprise pricing is not public in retrieved material. Demand an executable data licence, not a clinician-seat subscription; ask about regional catalog, Arabic content, local-brand mapping, cloud location, cache rights, and Saudi support. |
| **First Databank (FDB) MedKnowledge / Cloud Connector** | Supports drug–drug, allergy, disease, and dosing checks; FDB says its offering covers US, Canada, Australia, **Middle East**, and other regional product versions, with a web API option. [^5] | Probably the most directly relevant commercial option to test for Gulf product coverage and embedded deployment. Request a Saudi-market sample of the actual medications Noor expects. | Quote-only in retrieved material. The key diligence issue is whether “Middle East” contains Saudi registrations/brands and current SPC-equivalent information rather than a generic regional set. |
| **Elsevier / Multum** | The requested search did not yield primary vendor documentation sufficient to confirm a Saudi product catalog, embedded API, current content modules, or licence terms. | Keep as an RFP comparator, not a selection assumption. | Ask Elsevier directly for the exact named product, content domains, Saudi mapping, API/offline terms, safety/update SLA, and quote. |
| **ONC high-priority DDI list** | A useful public benchmark subset, not a comprehensive medication knowledge base. Commercial databases in the JAMIA comparison covered almost all of its alerts, but generated materially different alert volumes. [^1] | Use for acceptance testing and as one input to the fallback high-severity set; do not expose it as the sole production DDI service. | Not a replacement for an editorially maintained, worldwide/local product knowledge base. |
| **openFDA / DailyMed / SPL** | FDA SPL label data are machine-readable and weekly updated; SPL download data are public domain/CC0. Labels include structured sections such as dosage/administration, contraindications, interactions and pregnancy/lactation fields. [^10][^11][^12] | Excellent **source-document and data-ingestion layer** for US-labelled products; useful for clinician drill-down and internal evidence extraction. It cannot safely be converted automatically into a complete interaction engine. | Credible free data, but not credible free **curated CDS**. FDA warns that openFDA reformatting is not FDA-verified and the returned label may not be the label on currently distributed or approved products. [^10] |
| **WHO sources** | WHO classifications and essential-medicine resources can support terminology and class-level policies but are not a complete, maintained patient-specific DDI/dosing/contraindication service. | Use as a supplementary reference, not as a medication-screening engine. | No evidence in this research that WHO supplies the required production DDI content/API. |

### Price conclusion

No reliable public price sheet for a clinical, embedded, production-grade API from DrugBank, Micromedex, Lexidrug/Medi-Span, FDB, or Elsevier was found in the retrieved official material; the vendor pages direct buyers to sales/contact workflows. **Do not create a budget from consumer subscriptions, web API aggregators, or third-party “pricing guides.”** Price depends on data modules, deployment mode, patient volume, geography, local product catalog, caching, support/SLA, and redistribution rights. [^3][^7][^13]

Run a short, comparable RFP with a 2–3 week proof of concept. Require each vendor to quote (a) one production environment plus test environment, (b) named user/patient-volume basis, (c) Saudi deployment and data-processing geography, (d) API plus permitted local cache/offline use, (e) annual update cadence and urgent-safety update SLA, (f) local brands/ingredients supplied, (g) all modules and whether each is structured versus display-only text, (h) Arabic patient/professional content rights, (i) audit/provenance fields, (j) indemnity/liability cap, (k) termination/export terms, and (l) three-year total cost including implementation. Test the same representative Saudi medication set and clinical scenarios against each response. [^1]

## 3. Is there a credible free source usable commercially?

**There is a credible free *source-document stack*, but not a credible free *complete clinical interaction knowledge base*.** NLM’s machine-readable data terms state that no charge, usage fee, or royalty is paid to NLM, require source acknowledgment, and require redistributors to maintain currency or disclose noncurrency. [^14] FDA SPL/openFDA data are public domain/CC0, but the data are US product submissions, vary across labels, and carry FDA’s explicit warning not to rely on openFDA for medical-care decisions. [^11][^10]

Therefore:

- **Permissible and useful:** ingest public label text/metadata; link clinicians to source documents; build a versioned evidence queue; support US product attributes where a local pharmacist verifies Saudi equivalence; and use a curated high-severity subset.
- **Not defensible without editorial work:** parse free labels into automated universal DDI severity, therapeutic action, cross-reactivity, max-dose, organ-dosing, or pregnancy decisions. Product labels are product-specific and not a normalized patient-context decision model.
- **Not Saudi sufficient:** FDA/NLM data do not prove a product is registered, stocked, reimbursed, or labelled equivalently in Saudi Arabia. SDI/SPCs and the provider formulary must be the local anchor. [^2]

LactMed is a valuable free reference for breastfeeding: it synthesizes milk/infant levels, infant effects, and alternatives from the literature, and supports bulk download. [^15] NLM terms make government-created material broadly reusable with acknowledgment but caution that some linked/contributed content can have separate rights; conduct a record-level rights check before redistributing full monograph text in Noor. [^16]

## 4. Concrete fallback: a bounded high-severity set

A fallback is feasible **only as a clinician-reviewed safety net**, not as a “free interaction database.” Scope it to the active ingredients/formulations actually used in Noor’s diabetes, hypertension, CKD, HF, AF/anticoagulation, lipid, common analgesic/antimicrobial, and geriatric cohorts—roughly 60–80 ingredients after formulary confirmation. [^1]

### Minimum release scope

1. **Normalize the formulary** to a unique ingredient/concept plus strength, route, release type, and local brand synonyms; reconcile fixed-dose combinations.
2. **Curate only “avoid/contraindicated” and selected “urgent review” DDI pairs** with a concrete patient-harm mechanism, an explicit action, and a severity rule approved by pharmacist and relevant specialty owner. Use ONC high-priority interactions as a test/seed, not as the full corpus. [^1]
3. **Add a few high-value condition gates:** advanced CKD/AKI, hyperkalemia, bradycardia/QT risk when data are available, active/recent major bleeding, decompensated HF, severe hepatic impairment, pregnancy/lactation, and severe immediate allergy history.
4. **Attach source evidence**: Saudi SPC first; a current international label/guideline if the Saudi SPC is incomplete; a recorded clinical-review decision where sources conflict.
5. **Exclude by design:** low/moderate theoretical interactions, exhaustive off-label dosing, herbal dose calculations, vague “monitor closely” alerts without a measurable monitoring plan, and automatic treatment substitution.

### Illustrative high-severity categories—not a ready-to-deploy rule list

- dual renin–angiotensin blockade; RAAS/MRA/potassium combinations in a patient with impaired renal function or elevated potassium;
- anticoagulant/antiplatelet plus NSAID or a strong pharmacokinetic inhibitor/inducer, with indication/renal function and bleeding history considered;
- QT-prolonging combinations only when the agent pair, risk factors, and feasible action are explicit;
- hypoglycemia-prone combinations, especially insulin or sulfonylurea with poor intake, renal decline, fasting, or another glucose-lowering supplement;
- metformin in acute high-risk illness/AKI context rather than an oversimplified static “renal contraindication” label;
- NSAID use in CKD, HF, high bleeding risk, or cirrhosis; and
- non-dihydropyridine calcium-channel blocker/beta-blocker combinations when bradycardia/conduction risk is clinically relevant. [^1]

This design minimizes alert volume. That matters: the commercial-KB comparison projected 25, 145, and 84 alerts per 1,000 prescriptions from FDB, Micromedex, and Multum respectively, despite near-complete coverage of the ONC list. [^1] A systematic review also found poor agreement between database alerts and clinician assessment in some studies, with overlap as low as 11%. [^17]

### Build effort and governance

The fallback needs a named medication-safety pharmacist, physician sign-off for each clinical domain, a medical-information librarian/source process, and software QA. Each assertion needs: `drug_A`, `drug_B/condition`, patient modifiers, trigger criterion, severity, recommended action, rationale, source locator/version, evidence grade, owner, effective/review/expiry dates, test patients, and change history. No rule goes live without two independent clinical reviews, deterministic unit tests, end-to-end integration tests, and scenario review in the target home-health workflow. Review high-severity content monthly and immediately after an SFDA/SPC safety update. [^14]

## 5. Allergy cross-reactivity: the model should be phenotype- and structure-aware

### Beta-lactams

Do **not** implement “penicillin allergy = avoid all cephalosporins/carbapenems.” A meta-analysis of patients with confirmed penicillin allergy found cross-reactivity depended on cephalosporin R1 side-chain similarity: about 16% for identical-side-chain aminocephalosporins, 5.6% for intermediate similarity, and 2.1% for low similarity; carbapenem cross-reactivity was under 1%. [^18]

The record and rule must distinguish the original agent, reaction phenotype (immediate anaphylaxis/urticaria versus delayed benign rash versus severe cutaneous adverse reaction), timing, certainty/testing status, and proposed agent’s side-chain relationship. For anaphylaxis, severe cutaneous reactions, organ involvement, or an uncertain history when an alternative is not obvious, route to allergy/infectious-disease/pharmacy review rather than a generic allow/block. The knowledge source must carry an explicit side-chain mapping—not merely an antibiotic class label. [^18]

### Sulfonamides

Do **not** code “sulfa allergy = avoid all non-antibiotic sulfonamides.” The large cohort study found more reactions after a non-antibiotic sulfonamide among people with previous sulfonamide-antibiotic reactions, but an even stronger association after later penicillin; the authors concluded that the pattern reflected an overall predisposition to reactions rather than structural cross-reactivity. [^19] Store the culprit as a specific antibiotic/non-antibiotic and the reaction phenotype; permit a **review flag**, not a blanket contraindication, for thiazides, loop diuretics, sulfonylureas, celecoxib, and other non-antibiotic sulfonamides.

### NSAIDs

A safe model cannot reduce NSAID “allergy” to a single class check. It should capture the phenotype: cross-reactive COX-1-mediated respiratory disease, cross-reactive urticaria/angioedema, single-agent immediate allergy, delayed reaction, or unknown. Unknown/severe histories require clinician review; a future licensed database or allergy-specialist-reviewed protocol should provide the phenotype-specific alternative rules. This is a release gate because the naive all-NSAID block both over-alerts and can remove clinically important options. [^1]

## 6. Renal, hepatic, maximum-dose, and drug–disease logic

### Renal dosing

**Use local SPC as the first source for every Saudi-marketed formulation; do not use one generic renal table.** Store the renal metric specified by the product (eGFR versus creatinine clearance), the calculation/equation, body-size convention, dose/interval change, initiation/continuation distinction, dialysis modality/timing, indication, and the date/trajectory of renal function. The drug knowledge layer should offer dose screening; Noor must supply validated, current patient facts and show when those facts are stale. [^4]

A public label stack can seed human review but does not replace it. FDA SPL has structured dosage and interaction fields, but labels differ by product and openFDA labels are neither FDA-verified nor guaranteed to match currently distributed/approved labelling. [^12][^10] In a production licence, require explicit creatinine-clearance/eGFR threshold fields, route and formulation logic, dialysis content, source/version, and update SLA; FDB describes precisely these attributes in its dose-checking module. [^4]

### Hepatic dosing

Hepatic logic is lower-volume but not a simple “reduce by x%” table. The evidence-based cirrhosis project found that safety depended on Child–Pugh class for 26% of its recommendations, that 31% of drugs needed dose adjustment, and that evidence was unknown for many drugs; it also notes that product information was often not specific to cirrhosis. [^20] Its publication is CC BY-NC, so it can inform design and clinical review but must not be copied into a commercial rule corpus without another permission path. [^20]

For Noor v1: require a structured liver-disease phenotype and severity; screen only high-confidence “avoid/urgent review” drug–disease rules; defer all granular dose-adjustment automation to a licensed source or a specifically licensed, pharmacist-maintained corpus. Do not treat transaminases alone as hepatic functional severity. [^20]

### Maximum dose / dose range

Maximum dose is multidimensional: indication, age, route, formulation, renal/hepatic function, loading versus maintenance, treatment duration, and sometimes cumulative/lifetime exposure. The product should call a licensed dose-range module or hold a small, reviewed local table for the formulary. Never show a “max daily dose” without the context and source version that define it. Medi-Span and FDB specifically package max single/daily/lifetime dose logic with patient modifiers, illustrating why this is not a single spreadsheet field. [^9][^4]

### Drug–disease contraindications

Keep “contraindication,” “avoid,” “use caution,” and “monitor” separate. A rules engine should model condition phenotype/severity and supporting clinical facts, not just a problem-list label. High-value Noor v1 examples include renal/acute-illness risk with metformin; NSAID risk with CKD/HF/cirrhosis; thiazolidinedione risk with symptomatic/decompensated HF; and beta-blocker risk with active bronchospasm. The rule’s action must say whether it is an urgent clinician review, a monitoring requirement, or a hard stop under the local clinical-governance policy. A vendor source that only delivers an undifferentiated caution list is insufficient. [^5]

## 7. Pregnancy and lactation

FDA’s former letter categories are retired in favour of the Pregnancy and Lactation Labeling Rule. The relevant label structure is: **8.1 Pregnancy** (risk summary, clinical considerations, data), **8.2 Lactation** (risk summary including milk/infant/milk-production effects and clinical considerations), and **8.3 Females and Males of Reproductive Potential** (testing, contraception, infertility where relevant). [^21][^22]

This requires a different product model: store narrative evidence and decision context rather than a single category. For each drug/formulation, record pregnancy stage, indication and risk of untreated disease, human/animal evidence, dose/route, contraception/testing requirements, lactation exposure and infant age/prematurity, alternatives, and the exact label/source version. Use LactMed as a referenced, free lactation evidence source and local SPCs as the Saudi product source; do not create an autonomous “safe in pregnancy” output. [^15][^2]

## 8. Herbal and traditional remedies: flag-and-ask, not deterministic rules

This is locally important and poorly suited to deterministic dosing rules. A Saudi-focused systematic review reports common use of cinnamon, fenugreek, black seed/Nigella sativa, ginger, garlic, aloe, and olive products among people with diabetes, but identified only four Saudi clinical studies; the studies had low methodological quality, so safety/effectiveness conclusions are uncertain. [^23] A review of sulfonylurea interactions identifies bitter melon, fenugreek, cinnamon and several other supplements as potentially increasing hypoglycemic activity, but this is a pharmacologic-potential review rather than a sufficiently reliable basis for automatic dose changes. [^24]

Implement an Arabic/English structured intake prompt for product name, ingredients if known, dose, frequency, reason for use, source/brand, and start date. Trigger a **“flag and ask” pharmacy/clinician review** when a patient uses a glucose-lowering herb with insulin/sulfonylurea, an anticoagulant/antiplatelet with an herb associated with bleeding concern, or an unknown mixed/honey preparation. Do not infer composition from “natural,” use a mechanism-only interaction as a contraindication, or recommend stopping a prescribed drug based on an herbal claim. The evidence base supports discussion and medication reconciliation—not automated therapeutic substitution. [^23][^24]

## 9. Procurement recommendation and release gates

### Recommended path

1. **Run a paid, time-boxed evaluation** of FDB, Medi-Span/Lexidrug, Micromedex, and DrugBank against the same Saudi formulary and synthetic patient set. Include at least 40 high-risk DDI/allergy/renal/hepatic/pregnancy/duplicate-therapy cases and document false positives, false negatives, rationale/action quality, source/version, and response latency.
2. **Select one licensed core** only if it grants production embedded-CDS rights, proves current Saudi/Gulf product mapping or supports a maintainable SDI mapping, returns structured facts and source version, permits the required hosting/caching model, and provides an update/safety-notice SLA.
3. **Build Noor’s Saudi localization layer** independently: SDI/SPC evidence links, provider formulary/availability, Arabic-validated display text, guideline-based local rules, rule provenance, overrides, and audit trail.
4. **Keep a narrow fallback safety set** so that a contract outage, a new local product, or a vendor coverage gap does not leave the system silent. It remains a clinician-reviewed supplement, not a claim of broad DDI coverage. [^1]

### No-go conditions

Do not launch patient-facing or clinician-facing medication advice if the chosen source cannot demonstrate: commercial production rights; versioned, current content; local product mapping; a structured severity/action distinction; source provenance; a workable Saudi data/hosting arrangement; pharmacist-led local governance; and a clinical safety case with test evidence. A low-cost reference website, a consumer drug checker, or an unstructured label corpus does not meet this bar. [^10]

### Open decisions to close in the RFP

- Which Saudi providers/payers and exact 60–80 active ingredients/formulations define the launch formulary?
- Does “Middle East” coverage contain Saudi brands, ingredients, strengths and active registration status for that formulary?
- Which modules are structured/API-addressable versus display-only content?
- Can content and patient facts remain in Saudi-hosted infrastructure, and can data be cached locally?
- What are the contract’s rights to derive Noor-owned rules from source material, retain prior versions for audit, and display concise rationale to clinicians/patients?
- What is the vendor’s urgent safety-update SLA, recall/withdrawal flow, release notes, and historical-version access?
- Which clinical pharmacist and specialty owners will approve, test, and review every local rule? [^1]

This research supports a **license-first, localize-and-govern** decision. It does not support buying a consumer reference subscription, scraping commercial content, or claiming that public labels alone constitute a production medication-safety knowledge base. [^6][^10]


[^1]: Fung et al., 2017. Comparison of three commercial knowledge bases for detection of drug-drug interactions in clinical decision support. J. Am. Medical Informatics Assoc.

[^2]: Saudi Drugs information system (SDI).

[^3]: DrugBank | Clinical Drug Data API.

[^4]: Drug Dosing Database | Dose Range Database | FDB (First Databank).

[^5]: Databank. Deciding on healthcare’s leading drug knowledge solution is simple.

[^6]: Terms of Use | DrugBank Trust Center.

[^7]: Micromedex drug database.

[^8]: Drug Decision Support | UpToDate | Wolters Kluwer.

[^9]: Embedded Drug Data | Medi-Span | Wolters Kluwer.

[^10]: Label.

[^11]: Spl.

[^12]: Searchable fields.

[^13]: Medi-Span: Drug Databases and APIs.

[^14]: National Library of Medicine Terms and Conditions.

[^15]: Fact Sheet.  Drugs and Lactation Database (LactMed ® ).

[^16]: NCBI Website and Data Usage Policies and Disclaimers.

[^17]: Roblek et al., 2014. Drug-drug interaction software in clinical practice: a systematic review. European Journal of Clinical Pharmacology.

[^18]: Picard et al., 2019. Cross-reactivity to cephalosporins and carbapenems in penicillin-allergic patients: Two systematic reviews and meta-analyses. Journal of Allergy and Clinical Immunology: In Practice.

[^19]: Strom et al., 2003. Absence of cross-reactivity between sulfonamide antibiotics and sulfonamide nonantibiotics. New England Journal of Medicine.

[^20]: Weersink. Evidence-Based Recommendations to Improve the Safe Use of Drugs in Patients with Liver Cirrhosis.

[^21]: Pregnancy, Lactation, and Reproductive Potential: Labeling for Human Prescription Drug and Biological Products — Content and Format Guidance for Industry (Small Entity Compliance Guide) | FDA.

[^22]: Outline of Section 8.1 – 8.3 on Drug Labeling | FDA.

[^23]: Saudi Clinical Studies on Traditional Herbal Medicines for Diabetes: A Systematic Review

            | Bentham Science.

[^24]: Maideen & Balasubramaniam, 2018. Pharmacologically relevant drug interactions of sulfonylurea antidiabetics with common herbs. Journal of HerbMed Pharmacology.