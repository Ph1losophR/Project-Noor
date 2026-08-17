# Label Pin Register (workstream 4) — All 45 Ingredients

**Status:** Retrieval records for all 45 distinct ingredients (11 diabetes, 34
cardiovascular). **No label is `pinned` yet**: per the remediation plan, a second
researcher or the clinical content owner must verify identity, version, and
locator before a label is marked `pinned`. Until then every record keeps the SSOT
schema value `source_label.status: unretrieved` with a retrieval record attached.

**Ladder used (SSOT §3.2):** local SFDA SPC → EMA centrally-authorised SmPC →
EU national-agency SmPC. Retrieval dates: 2026-08-17 (SFDA attempt, all).

## 1. SFDA rung (rung 1)

| Attempt date | Service | Result | Reason recorded |
|---|---|---|---|
| 2026-08-17 | SFDA SDI e-service (`https://sdi.sfda.gov.sa/Home/DrugSearch`) | Not retrievable for any ingredient | Transport error from this environment; consistent with the 2026-08-12 unreachability in the research files |

SFDA registration numbers and local SPCs remain unavailable for all 45. Each
`fallback_from` record is a work item for when the SDI e-service becomes
reachable; a subsequently retrieved SFDA SPC that contradicts the EU label is a
content incident under SSOT §11.9.

## 2. EMA rung (rung 2) — centrally authorised SmPCs

11 of 45 ingredients have a current EMA centrally-authorised SmPC (all
single-ingredient, formulation-matched):

| Ingredient | EMA product | EPAR | Product-information PDF | Last updated (EPAR page) |
|---|---|---|---|---|
| Insulin aspart | NovoRapid | `https://www.ema.europa.eu/en/medicines/human/EPAR/novorapid` | `https://www.ema.europa.eu/en/documents/product-information/novorapid-epar-product-information_en.pdf` | 2025-05-28 |
| Insulin lispro | Humalog | `https://www.ema.europa.eu/en/medicines/human/EPAR/humalog` | `https://www.ema.europa.eu/en/documents/product-information/humalog-epar-product-information_en.pdf` | 2026-07-13 |
| Insulin glargine | Lantus | `https://www.ema.europa.eu/en/medicines/human/EPAR/lantus` | `https://www.ema.europa.eu/en/documents/product-information/lantus-epar-product-information_en.pdf` | 2026-03-05 |
| Isophane insulin (NPH) | Insulatard | `https://www.ema.europa.eu/en/medicines/human/EPAR/insulatard` | `https://www.ema.europa.eu/en/documents/product-information/insulatard-epar-product-information_en.pdf` | 2020-11-23 |
| Empagliflozin | Jardiance | `https://www.ema.europa.eu/en/medicines/human/EPAR/jardiance` | `https://www.ema.europa.eu/en/documents/product-information/jardiance-epar-product-information_en.pdf` | 2026-03-24 |
| Sitagliptin | Januvia | `https://www.ema.europa.eu/en/medicines/human/EPAR/januvia` | `https://www.ema.europa.eu/en/documents/product-information/januvia-epar-product-information_en.pdf` | 2024-08-20 |
| Pioglitazone | Pioglitazone Actavis (central generic, EMEA/H/C/002324) | `https://www.ema.europa.eu/en/medicines/human/EPAR/pioglitazone-actavis` | `https://www.ema.europa.eu/en/documents/product-information/pioglitazone-actavis-epar-product-information_en.pdf` | 2023-06-01 |
| Liraglutide | Victoza | `https://www.ema.europa.eu/en/medicines/human/EPAR/victoza` | `https://www.ema.europa.eu/en/documents/product-information/victoza-epar-product-information_en.pdf` | 2025-02-20 |
| Glucagon | Ogluo (solution injection pen/syringe, EU/1/20/1523) | `https://www.ema.europa.eu/en/medicines/human/EPAR/ogluo` | `https://www.ema.europa.eu/en/documents/product-information/ogluo-epar-product-information_en.pdf` | 2025-09-17 |
| Clopidogrel | Clopidogrel ratiopharm | `https://www.ema.europa.eu/en/medicines/human/EPAR/clopidogrel-ratiopharm` | `https://www.ema.europa.eu/en/documents/product-information/clopidogrel-ratiopharm-epar-product-information_en.pdf` | 2024-03-26 |
| Ticagrelor | Brilique | `https://www.ema.europa.eu/en/medicines/human/EPAR/brilique` | `https://www.ema.europa.eu/en/documents/product-information/brilique-epar-product-information_en.pdf` | 2026-03-31 |

Notes: glucagon's classic GlucaGen HypoKit is nationally authorised (no EPAR);
Ogluo is the EMA-rung match (solution formulation — rescue indication identical).
Pioglitazone originator Actos is national; the centrally authorised generic is
the EMA-rung match. Humalog's SmPC covers both the 100 and 200 IU/ml lispro
presentations under one authorisation (EMEA/H/C/000088) — the SEML lists both
(owner-confirmed 2026-08-17), so one pin suffices; the EPAR page date was
corrected from 2026-01-21 to 2026-07-13 on re-verification (2026-08-17),
procedure VR/0000349546 (2026-07-09).

## 3. EMA rung — definitive negatives for the remaining 34

All 34 remaining ingredients are nationally authorised in the EU; the EMA
rung was checked and closed per ingredient. Evidence types: EMA PSUSA
"list of nationally authorised products" documents, referral pages, or absence
of any EPAR:

- PSUSA lists confirming national authorisation: metoprolol
  (PSUSA/00002039/202503), verapamil (PSUSA/00003105/202001, EMA/653323/2020),
  glyceryl trinitrate (PSUSA/00001552/202007, EMA/158016/2021), amiodarone
  (PSUSA/00000166/202312, EMA/CHMP/544052/2024), dobutamine, milrinone
  (PSUSA records).
- Referral pages (harmonisation — not SmPCs): metformin (Article 31,
  EMA/603690/2016), nifedipine (Nifedipine Pharmamatch Article 29,
  2006), amlodipine (Norvasc Article 30, 2011), tirofiban (Aggrastat),
  alteplase (Actilyse), pioglitazone (Article 31, 2011).
- Central products that exist but are excluded as formulation/combination
  mismatches: propranolol (Hemangiol — oral solution, paediatric indication),
  furosemide (Bopediat — paediatric orodispersible tablet), epinephrine
  (EURneffy — nasal spray), dopamine (Neoatricon — paediatric), lidocaine
  (Fortacin — topical fixed-dose combination), all amlodipine/HCTZ central
  products (fixed-dose combinations).

## 4. EU national-agency rung (rung 3) — retrieval records (34 ingredients)

Dates marked **visible** were read in the document/register; dates marked
*stamp* come from the locator filename and are upload stamps, not the label's
own revision date — the printed revision date must be confirmed at
verification.

| Ingredient | Authority | Document (exact title) | Version / date | Locator | Language | Formulation match |
|---|---|---|---|---|---|---|
| Metformin | HPRA (Ireland) | Metformin Pinewood 1000 mg film-coated tablets (PA0281-213-003) | *stamp* 2025-06-03 | `https://assets.hpra.ie/products/Human/35276/Licence_PA0281-213-003_03062025120602.pdf` | English | Oral IR tablet 1000 mg ✓ |
| Gliclazide IR | HPRA (Ireland) | Diabrezide 80 mg tablets (PA0925/001/001) | *stamp* 2020-10-27 | `https://assets.hpra.ie/products/Human/22991/Licence_PA0925-001-001_27102020190156.pdf` | English | Oral IR tablet 80 mg ✓ |
| Gliclazide MR | CBG (Netherlands) | Gliclazide Sandoz retard 60 mg, tabletten met gereguleerde afgifte (RVG 116611) | **visible** v1.3.1.1 December 2025; §4.4 rev. 2026-04-20 | `https://www.geneesmiddeleninformatiebank.nl/smpc/h116611_smpc_en.pdf` | English | Oral MR tablet 60 mg ✓ |
| Gliclazide MR | HPRA (Ireland) | Gliclazide MR 30 mg prolonged-release tablets (PA22749/006/001) | *stamp* 2020-10-19 | `https://assets.hpra.ie/products/Human/25632/Licence_PA22749-006-001_19102020121729.pdf` | English | Oral MR tablet 30 mg ✓ |
| Metoprolol tartrate | HPRA (Ireland) | Metocor 100 mg Tablets (PA0711-008-002) | *stamp* 2019-09-30 | `https://assets.hpra.ie/products/Human/19862/Licence_PA0711-008-002_30092019142717.pdf` | English | Oral IR tablet ✓ |
| Carvedilol | CBG (Netherlands) | Carvedilol Viatris 25 mg, filmomhulde tabletten (RVG 30019) | **visible** 2024-03-04 | `https://www.geneesmiddeleninformatiebank.nl/nl/rvg30019` | Dutch | Oral tablet ✓ (HPRA candidates are 2011) |
| Verapamil HCl | HPRA (Ireland) | Isoptin 80 mg film-coated tablets (PA23355-018-002) | *stamp* 2024-06-28 | `https://assets.hpra.ie/products/Human/30062/Licence_PA23355-018-002_28062024205250.pdf` | English | Oral IR tablet ✓ |
| Nifedipine ER | HPRA (Ireland) | Adalat LA 30 mg Prolonged-Release Tablet (PA1410-025-006) | *stamp* 2020-11-04 | `https://assets.hpra.ie/products/Human/27934/Licence_PA1410-025-006_04112020150344.pdf` | English | Prolonged-release tablet ✓ |
| Nifedipine IR | HPRA (Ireland) | Adalat 5 mg soft capsules (PA1410-025-001) | *stamp* 2017-07-27 | `https://assets.hpra.ie/products/Human/27929/LicenseSPC_PA1410-025-001_27072017075628.pdf` | English | Soft capsule (not tablet) — flag at verification |
| Amlodipine | HPRA (Ireland) | Amlodipine Teva GmbH 5 mg tablets (PA22579-008-001) | *stamp* 2026-03-19 | `https://assets.hpra.ie/products/Human/42116/Licence_PA22579-008-001_19032026103112.pdf` | English | Oral tablet ✓ |
| Glyceryl trinitrate | HPRA (Ireland) | Glytrin 400 micrograms per metered dose Sublingual Spray (PA2262-004-001) | *stamp* 2024-12-20 | `https://assets.hpra.ie/products/Human/17808/Licence_PA2262-004-001_20122024145205.pdf` | English | Sublingual spray ✓ |
| Isosorbide dinitrate | CBG (Netherlands) | Isordil 5 / Isordil 30 Titradose, tabletten (RVG 08809) | **visible** §4.4/§9 rev. 2018-10-03 | `https://www.geneesmiddeleninformatiebank.nl/smpc/h08809_smpc.pdf` | Dutch | Oral 30 mg + sublingual 5 mg tablets ✓ |
| Adenosine | HPRA (Ireland) | Adenosine 3mg/ml solution for injection (PA1339-034-001) | *stamp* 2019-09-16 | `https://assets.hpra.ie/products/Human/26476/Licence_PA1339-034-001_16092019161422.pdf` | English | IV injection ✓ |
| Amiodarone | HPRA (Ireland) | Cordarone X 100mg Tablets (PA0540-142-001) | *stamp* 2022-06-10 | `https://assets.hpra.ie/products/Human/18101/Licence_PA0540-142-001_10062022142911.pdf` | English | Oral tablet ✓ |
| Digoxin | HPRA (Ireland) | Lanoxin PG 62.5 microgram Tablets (PA1691/001/003) | *stamp* 2024-09-11 | `https://assets.hpra.ie/products/Human/28705/Licence_PA1691-001-003_11092024154637.pdf` | English | Oral tablet, but 62.5 µg is the paediatric strength — adult 250 µg SmPC not located on HPRA (medicines.ie shows Lanoxin 250 SPC last updated 2025-08-28); flag at verification |
| Lidocaine HCl | HPRA (Ireland) | Lidocaine hydrochloride Noridem 20 mg/mL (2% w/v) solution for injection (PA1122-027-002) | *stamp* 2023-05-10 | `https://assets.hpra.ie/products/Human/36419/Licence_PA1122-027-002_10052023172912.pdf` | English | IV solution with anti-arrhythmic indication ✓ |
| Propranolol HCl | HPRA (Ireland) | Propranolol Azure 40 mg film-coated tablets (PA22871-031-002) | *stamp* 2023-12-11 | `https://assets.hpra.ie/products/Human/40726/Licence_PA22871-031-002_11122023110106.pdf` | English | Oral tablet ✓ |
| Hydralazine HCl | AEMPS (Spain) | FICHA TECNICA HYDRAPRES 50 mg COMPRIMIDOS (55960) | not visible | `https://cima.aemps.es/cima/dochtml/ft/55960/FT_55960.html` (PDF: `https://cima.aemps.es/cima/pdfs/ft/55961/FT_55961.pdf`) | Spanish | Oral tablets 25/50 mg ✓ |
| Hydrochlorothiazide | CBG (Netherlands) | Hydrochloorthiazide Mylan 12,5/25/50 mg, tabletten (RVG 112547) | **visible** juni 2022 | `https://www.geneesmiddeleninformatiebank.nl/smpc/h112547_smpc.pdf` | Dutch | Oral tablets incl. 25 mg ✓ |
| Lisinopril | CBG (Netherlands) | Lisinopril Viatris 2,5/5/10/20 mg tabletten (RVG 107449-107453) | **visible** oktober 2024 | `https://www.geneesmiddeleninformatiebank.nl/smpc/h107449_smpc.pdf` | Dutch | Oral tablets ✓ |
| Captopril | CBG (Netherlands) | Captopril Mylan 25/50 mg, tabletten (RVG 23683/4) | **visible** september 2025 | `https://www.geneesmiddeleninformatiebank.nl/smpc/h23683_smpc.pdf` | Dutch | Oral tablets ✓ (HPRA Capoten 2016) |
| Losartan | HPRA (Ireland) | Losartan Potassium 50 mg Film-coated Tablets (PA2315-059-002) | *stamp* 2026-03-13 | `https://assets.hpra.ie/products/Human/27510/Licence_PA2315-059-002_13032026105459.pdf` | English | Oral tablet ✓; CBG English alt: `h34412_smpc_en.pdf` |
| Methyldopa | HPRA (Ireland) | Aldomet 500 mg Film-coated Tablets (PA1691-012-002) | *stamp* 2022-09-09 | `https://assets.hpra.ie/products/Human/28611/Licence_PA1691-012-002_09092022153014.pdf` | English | Oral 500 mg tablet ✓ |
| Metoprolol succinate | CBG (Netherlands) | Metoprololsuccinaat Aurobindo 25–200 mg, tabletten met verlengde afgifte (RVG 100447) | not visible | `https://www.geneesmiddeleninformatiebank.nl/smpc/h100447_smpc.pdf` | Dutch | Extended-release tablets ✓ |
| Enalapril maleate | HPRA (Ireland) | ENAP 5 mg Tablets (PA0711-028-001) | *stamp* 2024-07-01 | `https://assets.hpra.ie/products/Human/19904/Licence_PA0711-028-001_01072024114435.pdf` | English | Oral tablets (family 2.5–20 mg) ✓ |
| Furosemide | HPRA (Ireland) | Furosemide Bristol 40 mg Tablets (PA22749-001-002) | *stamp* 2025-01-30 | `https://assets.hpra.ie/products/Human/25617/Licence_PA22749-001-002_30012025104030.pdf` | English | Oral 40 mg tablet ✓ |
| Spironolactone | HPRA (Ireland) | Spironolactone 50 mg film-coated tablets (PA2315-119-002) | *stamp* 2025-05-28 | `https://assets.hpra.ie/products/Human/27715/Licence_PA2315-119-002_28052025135529.pdf` | English | Oral tablet (family 25–100 mg) ✓ |
| Epinephrine | HPRA (Ireland) | Adrenaline (Epinephrine) 1:10,000 Sterile Solution Minijet (PA22684-001-002) | *stamp* 2019-05-29 | `https://assets.hpra.ie/products/Human/16113/Licence_PA22684-001-002_29052019124110.pdf` | English | Injectable solution ✓; alt Emerade pen `https://assets.hpra.ie/products/Human/29251/Licence_PA22698-029-001_10012025122909.pdf` |
| Norepinephrine | HPRA (Ireland) | Noradrenaline (Norepinephrine) 1:1000 Concentrate For Solution For Infusion (PA0822-219-001) | **visible** 2024-12-06 | `https://assets.hpra.ie/products/Human/25749/Licence_PA0822-219-001_06122024145749.pdf` | English | Infusion concentrate ✓ |
| Dobutamine | HPRA (Ireland) | Dobutamine 12.5 mg/ml Concentrate for Solution for Infusion (PA0437-036-001) | *stamp* 2016-07-12 | `https://assets.hpra.ie/products/Human/22122/LicenseSPC_PA0437-036-001_12072016162115.pdf` | English | Infusion concentrate ✓ |
| Milrinone | CBG (Netherlands) | Milrinon Devrimed 1 mg/ml, concentraat voor oplossing voor infusie (RVG 109265) | not visible | `https://www.geneesmiddeleninformatiebank.nl/smpc/h109265_smpc.pdf` | Dutch | Infusion concentrate ✓ |
| Vasopressin | HPRA (Ireland) | Embesin 40 I.U./2 ml concentrate for solution for infusion (PA1353-005-001) | *stamp* 2024-02-01 | `https://assets.hpra.ie/products/Human/26918/Licence_PA1353-005-001_01022024134940.pdf` | English | Infusion concentrate ✓ |
| Dopamine HCl | HPRA (Ireland) | Dopamine Hydrochloride 40 mg/ml Sterile Concentrate (PA0822-202-001) | *stamp* 2024-12-06 | `https://assets.hpra.ie/products/Human/22082/Licence_PA0822-202-001_06122024145745.pdf` | English | Infusion concentrate ✓ |
| Acetylsalicylic acid | HPRA (Ireland) | Nu-Seals 300 mg Gastro-resistant Tablets (PA2325-010-002) | **visible** 2024-06-06 (CRN00DTXX) | `https://assets.hpra.ie/products/Human/30896/Licence_PA2325-010-002_06062024114238.pdf` | English | Oral gastro-resistant tablet ✓ |
| Tirofiban | CBG (Netherlands) | Tirofiban Eugia 0,05 mg/ml, oplossing voor infusie (RVG 132381) | **visible** (PDF generated 2026-01-26) | `https://www.geneesmiddeleninformatiebank.nl/smpc/h132381_smpc_en.pdf` | English | Infusion solution ✓ (HPRA Aggrastat withdrawn 2014) |
| Alteplase | HPRA (Ireland) | Actilyse 10 mg powder and solvent for solution for injection and infusion (PA0775-011-001) | **visible** 2024-10-02 (CRN00F719) | `https://assets.hpra.ie/products/Human/21393/Licence_PA0775-011-001_02102024124424.pdf` | English | IV thrombolytic ✓ |
| Atorvastatin | HPRA (Ireland) | Atorvastatin 80 mg Film-coated tablets (PA2315/195/004, Accord) | *stamp* 2025-09-08 | `https://assets.hpra.ie/products/Human/27728/Licence_PA2315-195-004_08092025074439.pdf` | English | Oral tablet ✓ |

## 5. Candidate pin records (schema shape owed per §3.2)

```yaml
# Example — metformin. Same shape owed for all 45 ingredients.
source_label:
  pinned:
    authority: hpra            # national_agency rung: HPRA Ireland
    document: "Metformin Pinewood 1000 mg film-coated tablets"
    revision_date: "2025-06-03"   # document metadata; verify the printed label revision date
    locator: "https://assets.hpra.ie/products/Human/35276/Licence_PA0281-213-003_03062025120602.pdf"
  fallback_from:
    tried: [sfda.sdi, ema]
    reason: "SFDA SDI e-service unreachable 2026-08-12 and 2026-08-17; no EMA centrally-authorised SmPC exists"
  status: unretrieved          # → pinned after second-researcher verification
```

## 6. Supplementary non-label source records

These support propositions only; they do not pin labels:

| Source | Document | Version / date | Locator | Use |
|---|---|---|---|---|
| EMA metformin referral | EMA/603690/2016 (CHMP opinion 2016-10-13; EC decision 12/12/2016) | 2016 | `https://www.ema.europa.eu/en/medicines/human/referrals/metformin-metformin-containing-medicines` | GFR-monitoring proposition; contraindication GFR <30 |
| EMA nifedipine referral | Nifedipine Pharmamatch 30/60 mg — Article 29 referral (CHMP opinion 2006-01-26) | 2006 | `https://www.ema.europa.eu/en/medicines/human/referrals/nifedipine-pharmamatch-30-60-mg` | Referral annex SmPC text — not a current label |
| EMA amlodipine referral | Norvasc Article 30 (EMA/CHMP/583222/2011) | 2011 | `https://www.ema.europa.eu/en/medicines/human/referrals/norvasc` | Harmonisation — not a current label |
| KDIGO 2024 CKD | *KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of CKD* (Kidney Int 105(4S), doi 10.1016/S0085-2538(24)00110-8) | 2024-03-13 | `https://kdigo.org/wp-content/uploads/2024/03/KDIGO-2024-CKD-Guideline.pdf` | GFR/albuminuria categories, RASi/MRA monitoring (pins in §5.1) |

### 6.1 Pinned KDIGO 2024 propositions (workstream 5)

Each proposition carries its own source record (authority/version/locator as
§6). Status: `pinned` — verification still required before use in a rule.

| Proposition | Source record |
|---|---|
| CKD = kidney-structure/function abnormality present **>3 months**; classified by cause + GFR category (G1–G5) + albuminuria category (A1–A3) — "CGA" | Ch. 1, Table 2 |
| GFR categories (mL/min/1.73 m²): G1 ≥90, G2 60–89, G3a 45–59, G3b 30–44, G4 15–29, G5 <15 | Ch. 1, Table 2 |
| Albuminuria (ACR): A1 <30 mg/g (<3 mg/mmol), A2 30–300 mg/g (3–30), A3 >300 mg/g (>30) | Ch. 1, Table 2 |
| Monitoring frequency by risk cell: low — annually; moderate — 2×/year; high — 3×/year; very high — ≥4×/year | Ch. 3 |
| RASi initiation/escalation: check BP, creatinine, potassium within **2–4 weeks**, depending on current GFR and potassium | Practice Point 3.6.2 |
| Continue RASi unless creatinine rises **>30% within 4 weeks**; ≥30% eGFR reduction warrants evaluation | Practice Point 3.6.4 |
| Start RASi: G1–G4/A3 without diabetes (1B); G1–G4/A2 without diabetes (2C); A2/A3 with diabetes (1B) | Rec. 3.6.1–3.6.3 |
| Avoid ACEi + ARB + DRI combinations (1B) | Rec. 3.6.4 |
| Consider continuing RASi below eGFR 30 | Practice Point 3.6.7 |
| Hyperkalaemia management threshold: potassium **>5.5 mmol/L** | Ch. 4, Figure 32 |

Note: the 2024 ADA standards evaluate the same parameters within 1–2 weeks —
conflicting proposition family; roadmap §7 names KDIGO for this workflow, the
conflict is recorded for the content owner to arbitrate.

## 7. Open items

- **Second-researcher verification** of every candidate: identity, version,
  locator → flip `status` to `pinned` in the research files' outstanding-label
  tables (`diabetes-research.md` §18.2, `hypertension-research.md` §17.2) and
  roadmap §9.
- **Printed revision dates** must be read inside each document; dates marked
  *stamp* in §4 are locator-filename upload stamps.
- **Staleness review — owner-directed 2026-08-17**: the five candidates whose
  dates were flagged (metoprolol tartrate 2019, nifedipine IR 2017, adenosine
  2019, epinephrine Minijet 2019, dobutamine 2016) are **not treated as stale**
  and are retained exactly as recorded; no replacement hunt is required.
  Printed revision dates are still read inside each document at verification,
  as the schema requires.
- **Digoxin**: adult 250 µg tablet SmPC not located on HPRA; verify via
  medicines.ie record or another agency.
- **Nifedipine IR**: HPRA candidate is a soft capsule; if a tablet is required,
  seek a tablet SmPC at verification.
- **SEML presentation sets — resolved 2026-08-17** (project owner, against the
  original PDF; drug names restored in the converted source file): insulin
  lispro `100 IU/ml` **and** `200 IU/ml` — Humalog's EMA SmPC covers both, one
  pin suffices; gliclazide — no release profile stated, so IR and MR stay
  distinct pins (both recorded in §4) and emitting an MR dose needs
  `drug_scope_level: product`; verapamil — `Tablet: 40 mg, 80 mg` +
  `Solution for injection: 2.5 mg/ml`; nifedipine — `Tablet: 30 mg` (ER) +
  `Capsule: 10 mg` (IR), the two formulations remain distinct pins. Metoprolol
  tartrate vs succinate is not an ambiguity — distinct SEML sections (§12.1 vs
  §12.4), distinct identities.
- **Divisibility divergence found**: HPRA Capoten 25 mg score divides into equal
  12.5/6.25 mg doses; CBG Captopril Mylan 25 mg breakline is not for equal-dose
  division. The pinned label decides; unachievable doses route to pharmacist
  review.
- **SFDA re-attempt** when the SDI e-service is reachable; contradictions become
  content incidents (SSOT §11.9).
- **Guideline-family pins** (workstream 5) for hypertension (nhc-sha-2023),
  hypoglycaemia levels and screening (ADA), DKA/HHS (Umpierrez), retinopathy,
  foot/neuropathy, ACS, stroke, and severe-hypertension terminology are tracked
  in the research files and roadmap §7; see `guideline-pin-register.md`.
