# CDS Content Roadmap & Drug Research Checklist

**Project:** Noor CDS engine (inside Project Amal)
**Purpose:** Track what clinical content exists vs. what's speced-for-but-unbuilt, and give you a
concrete list of ingredients to research before writing rules against them.

**Read this first:** nothing in this file is clinical content. No dosing numbers, no thresholds,
no contraindication values are stated here — that would violate your own architecture's rule
that thresholds are never written from memory (§7.3, §11.7). This is a checklist of *what to go
find sources for*, not the sources themselves.

**Note:** all drugs listed in this file are included in the Saudi Essential Medicines List 2023 and have SFDA registration.
**Important Consideration to Note:** The local SFDA drug SPCs are based on the EMA and ICH values. Values in the `diabetes-research.md` and `hypertension-research.md` files are based directly off of either the EMA or ICH documents. Assume all info from there sources correct until proven otherwise.

---

## 1. Content coverage table

| Domain | Architecture ready? | Content written? | Priority |
|---|---|---|---|
| Drug contraindication / dose ceilings | Yes — full schema, vendor seam | 1 rule (metformin/eGFR) | Keep building |
| Renal dose adjustment (eGFR vs CrCl) | Yes, explicitly | 1 rule | Keep building |
| Severe hypo/hyperglycemia emergencies | Yes — red-flag libraries named (§11.7) | Thresholds not yet cited | **Do next** — named MVP requirement, currently empty |
| Missed monitoring / follow-up (repeat eGFR, repeat K+ after ACEi/MRA) | Yes — `monitors` + `pending_result` obligation | None authored | **Highest untapped value** — no clinic recall system exists in home visits |
| BP target + first-line agent by compelling indication (e.g. CKD → ACEi/ARB) | Yes — `source_family` pinning ready | Research drafted — `hypertension-research.md` §2.8 (unpopulated) | Pinning + clinical approval pending |
| Albuminuria / CKD staging (KDIGO) | Referenced conceptually | None | Add as thresholds + citation — no copyright blocker |
| Retinal exam reminder | Not mentioned | None | Cheap — it's a reminder, not a risk model |
| Foot/neuropathy exam reminder | Only exists as a *deferred risk score* (IWGDF, §15.2) | None | Don't confuse a reminder with a score — build the reminder now |
| SGLT2i / GLP-1 for CKD or HF benefit independent of A1c | Not mentioned | None | High evidence, sits at your diabetes+HTN+CKD intersection — rank above several speced items |
| Statin / ASCVD risk, aspirin | Deferred (SCORE2 risk model) | None | Correctly deferred — needs local calibration you don't have |
| Depression screening (PHQ-9) | Gated — licensing + escalation pathway required | Deliberately not MVP | Correctly deferred |
| Clinical Signal Catalogue | Architecture ready — `encounter_narrative` + registry support | None | **Do next** — required to power the new hybrid patient narrative workflow |

---

## 2. Clinical Signal Catalogue

Per the hybrid patient narrative architecture, we must curate a bounded set of structured clinical signals (symptoms, signs, physical exam findings) for the CDS engine to reason about. 

Before we can use these in rules, we must define:
- [ ] **Diabetes Complication Signals:** Hypoglycaemia, hyperglycaemia, DKA/HHS prodrome.
- [ ] **Hypertension Complication Signals:** Orthostatic symptoms, ACS symptoms (especially atypical presentations), stroke red flags, heart failure decompensation.
- [ ] **Pharmacotherapy Side Effects:** e.g., pedal oedema, GI upset, injection site lipohypertrophy, medication confusion/adherence issues.
- [ ] **Physical Exam Templates:** Diabetic foot exam findings, generalized vascular assessment, hydration status.

*Note: Free text captures everything else, but the evaluator only sees signals defined here.*

---

## 3. Drug research list

For every ingredient below, before it can become a rule you need (per §3.2 and §7.3 of the
architecture):

- [ ] `ingredient_id` and ATC class
- [ ] Whether it's on the **Saudi Essential Medicines List 2023** and has an SFDA registration
- [ ] The **local SPC version** the rule will be written against (not a US/EU label)
- [ ] Renal dosing guidance from that SPC — and whether it's expressed in eGFR or CrCl (§5.2 — this
      distinction is mandatory, don't skip it)
- [ ] Hepatic dosing guidance, if Child-Pugh–stratified (§3.2 — never transaminase-based)
- [ ] Major interactions relevant to a **polypharmacy, elderly, home-care** population specifically
      (not a general interaction database dump)
- [ ] Monitoring interval after initiation or dose change, if one exists, and which label version it
      came from (§7.1 `monitors`)
- [ ] Pregnancy/lactation narrative (8.1/8.2/8.3 sections), not a letter category (§3.2)

Don't pull any of the above from memory — yours or mine. Source it against the SPC, ADA/KDIGO,
or whatever `source_family` your profile has pinned (§7.3), and get it clinician-approved before
it's `clinician_approved` status.

### Diabetes
- [] Metformin
- [] Insulin Aspart
- [] Insulin Lispro
- [] Insulin Glargine
- [] Isophane Insulin
- [] Gliclazide
- [] Empagliflozin
- [] Sitagliptin
- [] Pioglitazone
- [] Liraglutide
- [] Glucagon

---

### Hypertension

**Anti-anginal Drugs**
- [] Metoprolol tartrate
- [] Carvedilol
- [] Verapamil hydrochloride
- [] Nifedipine
- [] Amlodipine
- [] Glyceryl trinitrate
- [] Isosorbide dinitrate

**Anti-arrhythmic Drugs**
- [] Adenosine
- [] Amiodarone
- [] Digoxin
- [] Lidocaine hydrochloride

**Anti-hypertensives**
- [] Propranolol
- [] Hydralazine
- [] Hydrochlorothiazide
- [] Lisinopril
- [] Captopril
- [] Losartan
- [] Methyldopa

**Drugs used in Heart Failure**
- [] Metoprolol succinate
- [] Enalapril maleate
- [] Furosemide
- [] Losartan potassium
- [] Spironolactone

**Vasopressors and Inotropes**
- [] Epinephrine
- [] Norepinephrine
- [] Dobutamine
- [] Milrinone
- [] Vasopressin
- [] Dopamine hydrochloride

**Anti-thrombotic Agents**
- [] Acetylsalicylic Acid
- [] Clopidogrel
- [] Ticagrelor
- [] Tirofiban
- [] Alteplase

**Diuretics**
- [] Furosemide
- [] Spironolactone
- [] Hydrochlorothiazide

**Lipid-lowering Agents**
- [] Atorvastatin

---

## 3. How to use this file

One ingredient at a time, following your own `testing-standards.md`
pattern: write the `.cases.yaml` rows first (at/below/above every threshold), watch them fail,
then write the rule. Don't batch-research a whole tier before writing any rules — you'll lose the thing that makes this catalogue trustworthy, which is that every rule was checked against real cases before it shipped.
