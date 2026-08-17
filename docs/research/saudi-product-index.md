# Saudi Product Index — demo seed (45-ingredient slice)

> **Status: mock/demo data.** Curated 2026-08-17 from the Kaggle snapshot `meshalfalah/ksa-drug-database-metadata-pils-and-spcs-aren` (version 1, uploaded 2025-10-23; author claims a scrape of the SFDA public drug portal). License **CC BY-NC-SA 4.0** — non-commercial. This index **keys** the demo rules; it is **not** a pin source under SSOT §3.2 (third-party snapshot, no SPC revision dates, no stable official locator). When the real SFDA-backed database exists, it swaps in behind the same shape.

**Records:** 8380 unique registrations in the snapshot; 730 match the 45-ingredient catalogue (105 combination products involving catalogue ingredients flagged separately).

## Match notes

- **Salt disambiguation:** metoprolol tartrate vs succinate, losartan (potassium), enalapril (maleate) etc. are kept separate by generic-name token where the registration states the salt; a bare `METOPROLOL` registration is listed under *metoprolol (salt unstated)* and needs manual salt assignment at review.

- **ER/IR:** for gliclazide, nifedipine, metoprolol the *form* field decides release class (`form says release` → ER/MR).

- **Combination products** (e.g. losartan + HCTZ, metformin + sitagliptin) are excluded from the per-ingredient tables and listed in the combos section — never a silent ingredient match.

- **Insulin concentrations** come from the strength/unit fields (100 vs 200 vs 300 IU/ml) — separate identities for lispro and glargine.

- **`mixed`** = the registration also contains active(s) outside the 45-ingredient catalogue (e.g. Soliqua = glargine + lixisenatide; Humulin 70-30 = NPH + regular). The generic-name column shows the full registered composition; a demo rule must treat mixed products distinctly from monotherapy.


## Demo findings worth knowing

- Nifedipine: **ER 30 mg tablet (Adalat LA) + IR 10 mg soft capsule (Epilat)** — matches the SEML resolution exactly; no other strengths registered in the snapshot.

- Insulin lispro: **only 100 IU/ml products** in the snapshot (no 200 IU/ml); Humalog Mix 25/50 are premixed lispro products (mixed).

- Insulin glargine: 100 IU/ml (Lantus, Basaglar, Basalog One, Semglee, Vivaro) + **Toujeo 300 IU/ml**;

- Isosorbide dinitrate: only **modified-release capsules 20/40 mg** — no sublingual form registered.

- Metoprolol: tartrate IR tablets 50/100 mg; succinate ER tablets 25–200 mg (Carelio).

- Methyldopa: single product (Sembrina 250 mg). Norepinephrine and alteplase: single products each.

- Metformin: 76 registrations (largest diabetes set); amlodipine 142 and HCTZ 118 dominate CV — mostly generics.


## metformin — 76 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mixed | 0202221671 | 2022 | Amaglime-Met | 500,2 | mg | Tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 19.40 | QA10BA02 |
| mixed | 2610222819 | 2017 | AMARYL M 2/500 mg film-coated tablet | 500,2 | mg | Film-coated tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 32 | A10BD02 |
| mixed | 2611246339 | 2024 | CRONOXAM PLUS | 50,1000 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 91.20 | A10BD07 |
| mixed | 2611246338 | 2024 | CRONOXAM PLUS | 50,850 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 88 | A10BD07 |
| mixed | 1-848-12 | 2012 | DAONIL M 250/1.25MG TABLETS | 250,1.25 | mg | Tablet | Oral use | Prescription | Generic | Sanofi Arabia Trading Co. Ltd | 8.75 | A10BD02 |
| mixed | 2-848-12 | 2012 | DAONIL M 500/2.5MG TABLETS | 500,2.5 | mg | Tablet | Oral use | Prescription | Generic | Sanofi Arabia Trading Co. Ltd | 14.85 | A10BD02 |
| mixed | 3-848-12 | 2012 | DAONIL M 500/5MG TABLETS | 500,5 | mg | Tablet | Oral use | Prescription | Generic | Sanofi Arabia Trading Co. Ltd | 21.1 | A10BD02 |
| pure | 2011234507 | 2023 | Diafor XR | 500 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Saudi Amarox | 13.20 | QA10BA02 |
| pure | 2011234511 | 2023 | Diafor XR | 750 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Saudi Amarox | 19.85 | QA10BA02 |
| pure | 2011234517 | 2023 | Diafor XR | 1000 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Saudi Amarox | 26.45 | QA10BA02 |
| pure | 2011234508 | 2023 | Diafor XR | 500 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Saudi Amarox | 26.45 | QA10BA02 |
| pure | 2011234510 | 2023 | Diafor XR | 750 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Saudi Amarox | 39.65 | QA10BA02 |
| pure | 2011234518 | 2023 | Diafor XR | 1000 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Saudi Amarox | 52.85 | QA10BA02 |
| pure | 1807222307 | 2009 | DIALON 1000MG F.C. TABLETS | 1000 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 6.95 | A10BA02 |
| pure | 1310222729 | 2002 | DIALON 500 MG F.C TAB | 500 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 6.05 | A10BA02 |
| pure | 1310222731 | 2009 | DIALON 850MG F.C. TABLETS | 850 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 3.8 | A10BA02 |
| pure | 45-271-19 | 2019 | DIAPHAGE 1 G SR TABLET | 1000 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 23.8 | A10BA02 |
| mixed | 0206210764 | 2021 | Divinusmet | 1000,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 116.10 | A10BD15 |
| mixed | 0206210763 | 2021 | Divinusmet | 1000,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 119.40 | A10BD15 |
| pure | 1611234489 | 2001 | FORMIT 850 MG TABLETS | 850 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 26.15 | A10BA02 |
| pure | 1104221936 | 2022 | Formit XR | 500 | mg | Extended-release tablet | Oral use | Prescription | Generic | SPIMACO | 25.00 | QA10BA02 |
| pure | 1004221932 | 2022 | Formit XR | 500 | mg | Extended-release tablet | Oral use | Prescription | Generic | SPIMACO | 12.50 | QA10BA02 |
| pure | 1302233242 | 2017 | FORMIT XR 750 MG TABLETS | 750 | mg | Extended-release tablet | Oral use | Prescription | Generic | SPIMACO | 22.50 | A10BA02 |
| pure | 0206222128 | 2017 | FORMIT XR 750 MG TABLETS | 750 | mg | Extended-release tablet | Oral use | Prescription | Generic | SPIMACO | 45.00 | A10BA02 |
| mixed | 285-11-10 | 2010 | GALVUS MET | 850,50 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 100.40 | A10BD08 |
| mixed | 286-11-10 | 2010 | GALVUS MET | 1000,50 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 105.75 | A10BD08 |
| pure | 0908222454 | 2016 | GLUCARE 1000 mg XR Tablet | 1000 | mg | Extended-release tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 56.65 | A10BA02 |
| pure | 2504245216 | 2002 | GLUCARE 500MG TAB | 500 | None | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 14.90 | A10BA02 |
| pure | 2504245214 | 2001 | GLUCARE 850 TAB. | 850 | None | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 27.75 | A10BA02 |
| pure | 2301221627 | 2016 | GLUCARE XR 500 mg tablet | 500 | None | Extended-release tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 15.85 | A10BA02 |
| pure | 2301221626 | 2016 | GLUCARE XR 500 mg tablet | 500 | None | Extended-release tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 31.70 | A10BA02 |
| pure | 2301221630 | 2016 | GLUCARE XR 500 mg tablet | 500 | None | Extended-release tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 47.55 | A10BA02 |
| pure | 2301221628 | 2016 | GLUCARE XR 750 mg tablet | 750 | None | Extended-release tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 23.75 | A10BA02 |
| pure | 2301221629 | 2016 | GLUCARE XR 750 mg tablet | 750 | None | Extended-release tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 47.50 | A10BA02 |
| pure | 5-331-03 | 2003 | GLUCOPHAGE 1 g tablet | 1000 | None | Film-coated tablet | Oral use | Prescription | NCE | ALHAYA MEDICAL CO | 19.85 | A10BA02 |
| pure | 1-331-00 | 2000 | GLUCOPHAGE 500 mg tablet | 500 | None | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 16.55 | A10BA02 |
| pure | 3-331-00 | 2000 | GLUCOPHAGE 850 mg tablet | 850 | None | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 15.4 | A10BA02 |
| pure | 1010211109 | 2021 | Glucophage XR | 1000 | None | Prolonged-release tablet | Oral use | Prescription | NCE | Salehiya Trading Co. | 33.35 | A10BA02 |
| pure | 1-5564-21 | 2012 | GLUCOPHAGE XR 750MG TABLET | 750 | None | Prolonged-release tablet | Oral use | Prescription | NCE | ALHAYA MEDICAL CO | 25 | A10BA02 |
| mixed | 3006222290 | 2022 | Glucovance | 5,1000 | mg | Film-coated tablet | Oral use | Prescription | NCE | ALHAYA MEDICAL CO | 25.50 | A10BD02 |
| mixed | 0801256552 | 2012 | GLUCOVANCE 2.5/500 | 2.5,500 | mg | Film-coated tablet | Oral use | Prescription | NCE | ALHAYA MEDICAL CO | 16.5 | A10BD02 |
| mixed | 1609245916 | 2012 | GLUCOVANCE 5/500 | 5,500 | mg | Film-coated tablet | Oral use | Prescription | NCE | ALHAYA MEDICAL CO | 23.45 | A10BD02 |
| mixed | 56-370-15 | 2015 | JALRA M | 850,50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 93.70 | A10BD08 |
| mixed | 57-370-15 | 2015 | JALRA M | 1000,50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Arabian Japanese Pharmaceutical Co. Ltd. | 98.70 | A10BD08 |
| pure | 1503221849 | 2022 | Lodiab XR | 750 | None | Prolonged-release tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 63.75 | A10BA02 |
| pure | 0603221816 | 2022 | Lodiab XR | 750 | None | Prolonged-release tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 42.50 | A10BA02 |
| pure | 0603221815 | 2022 | Lodiab XR | 1000 | None | Prolonged-release tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 85.05 | A10BA02 |
| pure | 0603221814 | 2022 | Lodiab XR | 1000 | None | Prolonged-release tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 56.70 | A10BA02 |
| pure | 0603221817 | 2022 | Lodiab XR | 750 | None | Prolonged-release tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 21.25 | A10BA02 |
| pure | 0603221813 | 2022 | Lodiab XR | 1000 | None | Prolonged-release tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 28.35 | A10BA02 |
| mixed | 0612222983 | 2022 | Meligamet 50 m / 1000 mg | 1000,50 | mg | Tablet | Oral use | Prescription | Generic | Saudi Amarox | 98.80 | A10BD07 |
| mixed | 0412222968 | 2022 | Meligamet 50 mg / 850 mg | 850,50 | mg | Tablet | Oral use | Prescription | Generic | Saudi Amarox | 95.35 | A10BD07 |
| pure | 1110211114 | 2001 | METFOR 500 | 500 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 15.70 | A10BA02 |
| pure | 1110211115 | 2000 | METFOR 850 MG TAB | 850 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 29.25 | A10BA02 |
| pure | 16-349-10 | 2010 | METFORMIN HEXAL 1000 MG FILM COATED TABLETS | 1000 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 25.00 | A10BA02 |
| pure | 2606257633 | 2006 | OMFORMIN 500MG F.C. TABLETS | 500 | None | Film-coated tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 4.70 | A10BA02 |
| mixed | 429-277-20 | 2020 | PIRAMYL-MET 2/500 mg Film-coated Tablet | 500,2 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 26 | A10BD02 |
| mixed | 1107233857 | 2023 | Sensityn | 850,50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Alpha Pharma Industry | 87.05 | None |
| mixed | 1107233858 | 2023 | Sensityn | 1000,50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Alpha Pharma Industry | 91.65 | None |
| mixed | 2907257880 | 2025 | Sitavia-MET | 50,500 | mg | Film-coated tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 85.00 | None |
| mixed | 2907257879 | 2025 | Sitavia-MET | 50,850 | mg | Film-coated tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 88 | None |
| mixed | 2907257878 | 2025 | Sitavia-MET | 50,1000 | mg | Film-coated tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 91.20 | None |
| mixed | 2201233133 | 2019 | VIPDOMET 12.5 mg/1000 mg TABLETS | 1000,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 117.45 | A10BD13 |
| mixed | 2201233131 | 2019 | VIPDOMET 12.5 mg/500 mg TABLETS | 500,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 109.9 | A10BD13 |
| mixed | 2108258086 | 2025 | Vtreat Met | 50,1000 | mg | Film-coated tablet | Oral use | Prescription | Generic | AL-TAIF PHARMACEUTICALS COMPANY (SPECTRO PHARMA) | 84.60 | None |
| mixed | 2108258085 | 2025 | Vtreat Met | 50,850 | mg | Film-coated tablet | Oral use | Prescription | Generic | AL-TAIF PHARMACEUTICALS COMPANY (SPECTRO PHARMA) | 80.35 | None |
| mixed | 1309234198 | 2018 | XIGDUO XR 10 mg/1000 mg Film Coted Tablet | 1000,10 | mg | Film-coated tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 124.40 | A10BD15 |
| mixed | 1309234196 | 2018 | XIGDUO XR 10 mg/500 mg Film Coted Tablet | 500,10 | mg | Film-coated tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 122.45 | A10BD15 |
| mixed | 1309234197 | 2018 | XIGDUO XR 5 mg/1000 mg Film Coted Tablet | 1000,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 128.00 | A10BD15 |
| mixed | 0306257538 | 2025 | Xitamet | 1000,50 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 91.20 | None |
| mixed | 0306257537 | 2025 | Xitamet | 850,50 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 88 | None |
| mixed | 1305257383 | 2025 | Zylinamet | 2.5,500 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 124.35 | None |
| mixed | 1305257382 | 2025 | Zylinamet | 2.5,850 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 134.60 | None |
| mixed | 1305257381 | 2025 | Zylinamet | 2.5,1000 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 142.90 | None |
| mixed | 36-590-19 | 2019 | ZYTERO PLUS 12.5 mg/ 1000 mg Film Coated Tablet | 1000,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | BATTERJEE PHARMACEUTICAL FACTORY | 117.45 | A10BH04 |
| mixed | 35-590-19 | 2019 | ZYTERO PLUS 12.5 mg/ 500 mg Film Coated Tablet | 500,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | BATTERJEE PHARMACEUTICAL FACTORY | 109.9 | A10BH04 |

## insulin aspart — 8 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mixed | 2208222530 | 2004 | NOVOMIX 30 FLEXPEN 100U\ML | 30,70 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 189.00 | A10AB05 |
| mixed | 63-100-14 | 2014 | NOVOMIX 50 FLEXPEN | 50,50 | IU/ml | Suspension for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 156.90 | A10AB05 |
| pure | 0405233591 | 2023 | NovoRapid | 100 | U/ml | Solution for injection | Intravenous, Subcutaneous | Prescription | Biological | Salehiya Trading Co. | 81.65 | QA10AB05 |
| pure | 1601256675 | 2004 | NOVORAPID FLEXPEN 100U\ML | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 189.00 | A10AB05 |
| pure | 1601256674 | 2004 | NOVORAPID PEN FILL 100 I.U - ML | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 134.90 | A10AB05 |
| mixed | 3001256783 | 2025 | Ryzodeg FlexPen | 100 | U/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | Novo Nordisk | 378.90 | A10AD06 |
| mixed | 2308222536 | 2016 | RYZODEG FlexTouch 100 u/ml | 70,30 | IU/ml | Solution for injection | Subcutaneous use | Prescription | NCE | Salehiya Trading Co. | 378.90 | A10AD06 |
| pure | 2306222250 | 2022 | Truvelog | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 141.75 | A10AB05 |

## insulin lispro — 6 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 0907245509 | 1998 | HUMALOG 100 I.U VIALS | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 89.80 | A10AB04 |
| pure | 1405245298 | 2019 | HUMALOG KWIK-PEN 100IU/ML | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 161.30 | None |
| mixed | 1405245297 | 2019 | HUMALOG KWIK-PEN MIX 25 | 25,75 | IU/ml | Suspension for injection | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 161.30 | None |
| mixed | 0205245244 | 2018 | HUMALOG KWIK-PEN MIX 50 | 50,50 | IU/ml | Suspension for injection | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 161.30 | None |
| pure | 3003210651 | 2021 | Humalog Tempo Pen | 100 | IU/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 167.95 | A10AD04 |
| pure | H0000034199 | 2023 | Lyumjev Tempo Pen | 100 | IU/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 167.95 | A10AB04 |

## insulin glargine — 16 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 21-5117-20 | 2020 | BASAGLAR 100 u/ml Solution For Injection In Pre-Filled Pen | 100 | IU/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 191.75 | A10AE04 |
| pure | 2711234554 | 2018 | BASAGLAR 100 u/ml solution for injection in Pre-Filled pen | 100 | IU/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 163.20 | A10AE04 |
| pure | 3003210650 | 2021 | Basaglar Tempo Pen | 100 | IU/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 191.75 | 10E04 |
| pure | 2-5291-20 | 2020 | BASALOG ONE | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | EBRAHIM M. ALMANA & BROS. CO. | 115.05 | A10AE04 |
| pure | 3-5291-20 | 2020 | BASALOG ONE | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | EBRAHIM M. ALMANA & BROS. CO. | 191.75 | A10AE04 |
| pure | 1-5291-20 | 2020 | BASALOG ONE | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | EBRAHIM M. ALMANA & BROS. CO. | 38.35 | A10AE04 |
| pure | 45-23-03 | 2003 | LANTUS 100 I.U - ML VIAL | 100 | None | Solution | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 220.10 | A10AE04 |
| pure | 2705257464 | 2007 | LANTUS SOLOSTAR 100I.U-ML DISPOSABLE PEN | 100 | None | Solution | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 296.45 | A10AE04 |
| pure | 1802244936 | 2024 | semglee | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Cigalah Group | 163.05 | A10AE04 |
| mixed | 0701256537 | 2018 | SOLIQUA SOLOSTAR (33 mcg/ml) /100 U Solution for Injection | 100,0.33 | µg/ml | Solution for injection in pre-filled syringe | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 748.75 | A10BX10 |
| mixed | 0701256535 | 2018 | SOLIQUA SOLOSTAR (33 mcg/ml) /100 U Solution for Injection | 100,0.33 | µg/ml | Solution for injection in pre-filled syringe | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 449.25 | A10BX10 |
| mixed | 0701256536 | 2018 | SOLIQUA SOLOSTAR 50 mcg/ml) /100 U Solution for Injection | 100,0.5 | µg/ml | Solution for injection in pre-filled syringe | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 898.4 | A10BX10 |
| mixed | 0701256538 | 2018 | SOLIQUA SOLOSTAR 50 mcg/ml) /100 U Solution for Injection | 100,0.5 | µg/ml | Solution for injection in pre-filled syringe | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 539.05 | A10BX10 |
| pure | 56-23-17 | 2017 | TOUJEO 300 IU/ml Solution for Injection in Pre-filled Pen | 300 | IU/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 216.95 | A10AE04 |
| pure | 3005233745 | 2017 | TOUJEO 300 IU/ml Solution for Injection in Pre-filled Pen | 300 | None | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | Sanofi Arabia Trading Co. Ltd | 356.35 | A10AE04 |
| pure | 58-370-15 | 2015 | VIVARO 100 IU/ml pre-filled pen, disposable | 100 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Farouk, Maamoun Tamer & CO | 216.60 | A10AE04 |

## isophane insulin (NPH) — 4 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 36-42-92 | 1992 | HUMULIN 70-30 100U-ML | 100 | IU/ml | Suspension for injection | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 53.55 | A10AD01 |
| pure | 26-42-85 | 1985 | HUMULIN-N-NPH 100 U-ML | 100 | IU/ml | Suspension for injection | Subcutaneous use | Prescription | Biological | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 53.55 | A10AC01 |
| mixed | 0311222870 | 1989 | MIXTARD 30 | 70,30 | IU/ml | Suspension | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 65 | A10AB05 |
| mixed | 18-100-95 | 1995 | MIXTARD 30 PENFILL | 70,30 | IU/ml | Suspension for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 103.35 | A10AD01 |

## gliclazide — 5 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 65-249-18 | 2018 | CLAZ MR 30 mg tablet | 30 | mg | modified-release tablet | Oral use | Prescription | Generic | Cigalah Group | 21.6 | A10BB09 |
| pure | 2110246083 | 2019 | CLAZ MR 60 mg tablet | 60 | None | modified-release tablet | Oral use | Prescription | Generic | Cigalah Group | 21.6 | A10BB09 |
| pure | 2308200132 | 2020 | DIAOPTIM MR | 60 | mg | modified-release tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 24.00 | A10BB09 |
| pure | 0809258183 | 2025 | Zyglic MR | 30 | mg | modified-release tablet | Oral use | Prescription | Generic | QOMEL MEDICAL DRUG STORE | 20.4 | None |
| pure | 0809258184 | 2025 | Zyglic MR | 60 | mg | modified-release tablet | Oral use | Prescription | Generic | QOMEL MEDICAL DRUG STORE | 20.40 | None |

## empagliflozin — 8 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 0207257657 | 2025 | EMBA | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 128.40 | None |
| pure | 0207257667 | 2025 | EMBA | 25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 128.40 | None |
| pure | 1308245764 | 2024 | Empagliflozin SPC | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SUDAIR PHARMA COMPANY | 135.15 | A10BK03 |
| pure | 1308245763 | 2024 | Empagliflozin SPC | 25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SUDAIR PHARMA COMPANY | 135.15 | A10BK03 |
| mixed | 117-68-18 | 2022 | GLYXAMBI | 10,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Cigalah Group | 226.05 | A10BH05 |
| mixed | 118-68-18 | 2022 | GLYXAMBI | 25,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Cigalah Group | 226.05 | A10BH05 |
| pure | 2810211247 | 2016 | JARDIANCE 10 mg film-coated tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | NCE | Cigalah Group | 159.00 | A10BX12 |
| pure | 2810211246 | 2016 | JARDIANCE 25 mg film-coated tablet | 25 | mg | Film-coated tablet | Oral use | Prescription | NCE | Cigalah Group | 159.00 | A10BX12 |

## sitagliptin — 8 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 280-212-13 | 2013 | GLIPTEN 100MG F.C. TABLET | 100 | mg | Film-coated tablet | Oral use | Prescription | NCE | SPIMACO | 98.20 | A10BH01 |
| pure | 1101210399 | 2016 | JANUVIA 100MG F.C. TABLETS | 100 | None | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 105.25 | A10BH01 |
| pure | 1304233539 | 2023 | JANUVIA 25 mg | 25 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 44.65 | A10BH01 |
| pure | 1304233541 | 2023 | JANUVIA 50 mg | 50 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 81.70 | A10BH01 |
| pure | 1406222187 | 2022 | Sitagen | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 90.20 | A10BH01 |
| pure | 1406222188 | 2022 | Sitagen | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 74.40 | A10BH01 |
| pure | 0708245736 | 2024 | SITAVIA | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 90.20 | A10BH01 |
| pure | 0708245735 | 2024 | SITAVIA | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 74.40 | A10BH01 |

## pioglitazone — 16 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2112234623 | 2004 | ACTOS 15MG TABLET | 15 | mg | Tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 51.7 | A10BG03 |
| pure | 1209245904 | 2002 | ACTOS 30MG TAB | 30 | None | Tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 87.75 | A10BG03 |
| mixed | 2705257465 | 2019 | CYERO 25/15 mg Tablet | 25,15 | mg | Film-coated tablet | Oral use | Prescription | NCE | BATTERJEE PHARMACEUTICAL FACTORY | 137.6 | A10BD09 |
| mixed | 2705257466 | 2019 | CYERO 25/30 mg Tablet | 25,30 | mg | Film-coated tablet | Oral use | Prescription | NCE | BATTERJEE PHARMACEUTICAL FACTORY | 159.75 | A10BD09 |
| mixed | 0802221700 | 2016 | DUETACT 30/2 mg tablet | 30,2 | mg | Tablet | Oral use | Prescription | NCE | Jazeera Pharmaceutical Industries (JPI) | 108.65 | A10BD06 |
| mixed | 0802221696 | 2016 | DUETACT 30/4 mg tablet | 30,4 | mg | Tablet | Oral use | Prescription | NCE | Jazeera Pharmaceutical Industries (JPI) | 125.8 | A10BD06 |
| pure | 1211246190 | 2014 | GLACERA 15MG TABLET | 15 | None | Tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 37.8 | A10BG03 |
| pure | 1211246192 | 2014 | GLACERA 30MG TABLET | 30 | None | Tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 64.15 | A10BG03 |
| pure | 3112246509 | 2019 | GLERAN 15MG TABLET | 15 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 22.6 | A10BG03 |
| pure | 3112246510 | 2019 | GLERAN 30MG TABLET | 30 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 45.2 | A10BG03 |
| mixed | 0603245026 | 2019 | INCRESYNC 25/15 mg Tablet | 25,15 | mg | Tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 137.6 | A10BD09 |
| mixed | 0603245025 | 2019 | INCRESYNC 25/30 mg Tablet | 25,30 | mg | Tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 159.75 | A10BD09 |
| mixed | 321-334-19 | 2019 | INCRESYNC 25/45 mg Tablet | 25,45 | mg | Tablet | Oral use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 175.75 | A10BD09 |
| pure | 1904221951 | 2014 | OGLITON 15 MG Tablet | 15 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 34 | A10BG03 |
| pure | 1904221953 | 2014 | OGLITON 30 MG Tablet | 30 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 57.75 | A10BG03 |
| pure | 1904221952 | 2014 | OGLITON 45 MG Tablet | 45 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 74.9 | A10BG03 |

## liraglutide — 6 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1405245294 | 2024 | Evonanz 18 mg per 3 ml | 6 | mg/ml | Solution for injection | Subcutaneous use | Prescription | Generic | Boston Oncology Arabia | 297.75 | A10BJ02 |
| pure | 2407245648 | 2024 | Ligra | 6 | mg/ml | Solution for injection in pre-filled pen | Subcutaneous use | Prescription | Biological | AJA PHARMACEUTICAL INDUSTRIES | 258.05 | QA10BX07 |
| pure | 2606222257 | 2016 | SAXENDA 6 mg/ml sloution for injection in pre-filled pen | 6 | None | Solution for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 709.90 | A10BX07 |
| pure | 0602256841 | 2011 | VICTOZA 6MG/ML SOLUTION FOR INJECTION | 6 | None | Solution for injection in pre-filled pen | Intravenous use | Prescription | Biological | Salehiya Trading Co. | 317.60 | A10BJ02 |
| mixed | 2510234393 | 2018 | XULTOPHY 100 U/ml + 3.6 mg/ml Solution for Injection | 100,3.6 | IU/ml | Solution for injection | Subcutaneous use | Prescription | Biological | Salehiya Trading Co. | 821.30 | A10AE56 |
| pure | 1405245295 | 2024 | Zelyssa 18 mg per 3 ml | 6 | mg/ml | Solution for injection | Subcutaneous use | Prescription | Generic | Boston Oncology Arabia | 665.55 | A10BJ02 |

## glucagon — 2 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | H0000004831 | 2020 | Baqsimi | 3 | mg | Nasal spray | Nasal use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 139.50 | None |
| pure | 23-100-98 | 1998 | GLUCAGEN HYPOKIT | 1 | None | Powder and solvent for solution for injection | Subcutaneous use | Prescription | Generic | Salehiya Trading Co. | 86.55 | H04AA01 |

## metoprolol tartrate — 4 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 0710246013 | 2024 | Matroda | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 29.40 | C07AB02 |
| pure | 0710246014 | 2024 | Matroda | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 17.05 | C07AB02 |
| pure | 2111200276 | 2020 | Metolina | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Aurobindo Pharma Saudi Arabia Limited | 13.45 | C07AB02 |
| pure | 2207200118 | 2020 | Metolina | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | Aurobindo Pharma Saudi Arabia Limited | 23.199 | C07AB02 |

## metoprolol succinate — 4 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 22-5083-20 | 2021 | CARELIO | 200 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 42.25 | C07AB02 |
| pure | 21-5083-20 | 2021 | CARELIO | 100 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 36.40 | C07AB02 |
| pure | 20-5083-20 | 2021 | CARELIO | 50 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 23.40 | C07AB02 |
| pure | 19-5083-20 | 2021 | CARELIO | 25 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 14.25 | C07AB02 |

## metoprolol (salt unstated) — 0 product(s)

_No match in snapshot._


## carvedilol — 11 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2802210560 | 2003 | CARVIDOL 25 MG TAB | 25 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 47.25 | C07AG02 |
| pure | 2802210559 | 2004 | CARVIDOL 6.25MG TABLET | 6.25 | None | Tablet | Oral use | Prescription | Generic | SPIMACO | 26.40 | C07AG02 |
| pure | 0803221824 | 2020 | DILATREND 25MG TABLET | 25 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 47.25 | C07AG02 |
| pure | 0803221825 | 2020 | DILATREND 6.25 MG TABLET | 6.25 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 27.80 | C07AG02 |
| pure | 0509245871 | 2019 | Ravildo 12.5 mg F.C Tablets | 12.5 | None | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 17.6 | C07AG02 |
| pure | 0509245869 | 2019 | Ravildo 25 mg F.C Tablets | 25 | None | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 26.65 | C07AG02 |
| pure | 4-5286-19 | 2019 | Ravildo 3.125 mg F.C Tablets | 3.125 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 6.45 | C07AG02 |
| pure | 0509245870 | 2019 | Ravildo 6. 25 mg F.C Tablets | 6.25 | None | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 12.9 | C07AG02 |
| pure | 195-325-07 | 2007 | RIACAVILOL 12.5 MG TAB | 12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 24.1 | C07AG02 |
| pure | 196-325-07 | 2007 | RIACAVILOL 25MG TABLET | 25 | mg | Film-coated tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 42.5 | C07AG02 |
| pure | 194-325-07 | 2007 | RIACAVILOL 6.25 MG TABLET | 6.25 | mg | Film-coated tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 15.95 | C07AG02 |

## verapamil — 6 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 9-63-82 | 1982 | ISOPTIN AMP 2.5MG-ML | 2.5 | mg/ml | Solution for injection | Intravenous use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 14.20 | C08DA01 |
| pure | 10-63-82 | 1982 | ISOPTIN RETARD TAB 120MG | 120 | mg | Prolonged-release tablet | Oral use | Prescription | NCE | AL-KAMAL IMPORT OFFICE CO. LTD. | 20.15 | C08DA01 |
| pure | 22-63-97 | 1997 | ISOPTIN S.R 240MG F.COATED TAB | 240 | mg | Prolonged-release tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 41.95 | C08DA01 |
| pure | 6-63-82 | 1982 | ISOPTIN TABLETS 40 MG. | 40 | mg | Tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 18.10 | C08DA01 |
| pure | 7-63-82 | 1982 | ISOPTIN TABLETS 80 MG. | 80 | mg | Tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 14.70 | C08DA01 |
| pure | 3007257897 | 2025 | Verapamil QO | 2.5 | mg | Solution for injection | Intravenous use | Prescription | Generic | QOMEL MEDICAL DRUG STORE | 14.20 | None |

## nifedipine — 2 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 44-4-01 | 2001 | ADALAT 30MG LA TAB | 30 | mg | modified-release tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 46.40 | C08CA05 |
| pure | 30-201-02 | 2002 | EPILAT 10MG CAPS | 10 | mg | Capsule, soft | Oral use | Prescription | Generic | Khalid Bin Saad Int. Company LTD | 6.45 | C08CA05 |

## amlodipine — 142 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1611234490 | 2018 | AMEP 10 mg Tablet | 10 | None | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 27.2 | C08CA01 |
| pure | 1611234491 | 2018 | AMEP 5 mg Tablet | 5 | None | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 13 | C08CA01 |
| pure | 1309234209 | 2023 | AMLOCARD 10 mg tablets | 10 | mg | Tablet | Oral use | Prescription | Generic | BATTERJEE PHARMACEUTICAL FACTORY | 43.35 | C08CA01 |
| pure | 0904233509 | 2010 | AMLOCARD 5MG TABLETS | 5 | mg | Tablet | Oral use | Prescription | Generic | BATTERJEE PHARMACEUTICAL FACTORY | 26.45 | C08CA01 |
| mixed | 0905233611 | 2017 | AMLOHOPE 10 mg/10 mg Capsule | 10,10 | mg | Capsule, hard | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 50.85 | C09BB07 |
| mixed | 0905233603 | 2017 | AMLOHOPE 10 mg/5 mg Capsule | 10,5 | mg | Capsule, hard | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 45.2 | C09BB07 |
| mixed | 0905233610 | 2017 | AMLOHOPE 5 mg/10 mg Capsule | 5,10 | mg | Capsule, hard | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 45.2 | C09BB07 |
| mixed | 0905233609 | 2017 | AMLOHOPE 5 mg/5 mg Capsule | 5,5 | mg | Capsule, hard | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 40.25 | C09BB07 |
| pure | 0805257360 | 2010 | AMLOPHAR 5MG CAPSULES | 5 | None | Capsule, hard | Oral use | Prescription | Generic | Cigalah Group | 29.4 | C08CA01 |
| pure | 0711211264 | 2009 | AMLOPINE 10MG CAPSULES | 10 | None | Capsule | Oral use | Prescription | Generic | SPIMACO | 64.40 | C08CA01 |
| pure | 1803257094 | 2004 | AMLOPINE 5MG CAPSULE | 5 | None | Capsule | Oral use | Prescription | Generic | SPIMACO | 53.35 | C08CA01 |
| pure | 2811211383 | 2006 | AMLOPRESS 5MG CAPSULES | 5 | None | Capsule | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 32.65 | C08CA01 |
| pure | 0202233206 | 2013 | AMLOR 10MG CAPSULES | 10 | None | Capsule, hard | Oral use | Prescription | NCE | Viatris Arabia Limited | 64.40 | C08CA01 |
| pure | 0202233207 | 2013 | AMLOR CAPS 5MG | 5 | None | Capsule, hard | Oral use | Prescription | NCE | Viatris Arabia Limited | 60.65 | C08CA01 |
| mixed | 1306233798 | 2023 | Amlovan | 160,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 56.85 | None |
| mixed | 1306233794 | 2023 | Amlovan | 160,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 62.90 | None |
| pure | 0201221545 | 2016 | AMODIP 5 mg capsule | 5 | mg | Capsule | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 26.45 | C08CA01 |
| pure | 85-124-10 | 2010 | AMOLAR 10MG CAPSULES | 10 | mg | Capsule | Oral use | Prescription | Generic | Salehiya Trading Co. | 29.15 | C08CA01 |
| mixed | 0201221547 | 2022 | Amstar | 160,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 42.20 | C09DB01 |
| mixed | 3012211531 | 2022 | Amstar | 160,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 42.20 | C09DB01 |
| pure | 0811211271 | 2004 | AMVASC 10MG CAPSULE | 10 | None | Capsule | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 64.40 | C08CA01 |
| pure | 2111211346 | 2004 | AMVASC 2.5MG CAPSULE | 2.5 | mg | Capsule | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 27.45 | C08CA01 |
| pure | 1108222469 | 2004 | AMVASC 5MG CAPSULE | 5 | None | Capsule | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 53.35 | C08CA01 |
| mixed | 2-5307-19 | 2019 | APROVASC 150MG/10MG F.C.TABLET | 150,10 | mg | Tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 95.65 | C09CA04 |
| mixed | 1-5307-19 | 2019 | APROVASC 150MG/5MG F.C.TABLET | 150,5 | mg | Tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 95.65 | C09CA04 |
| mixed | 4-5307-19 | 2019 | APROVASC 300MG/10MG F.C.TABLET | 300,10 | mg | Tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 135.95 | C09CA04 |
| mixed | 3-5307-19 | 2019 | APROVASC 300MG/5MG F.C.TABLET | 300,5 | mg | Tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 135.95 | C09CA04 |
| mixed | 1907222315 | 2016 | Avysk Plus 10/160 mg film-coated tablet | 160,10 | None | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 56.6 | C09DB01 |
| mixed | 0404221910 | 2016 | Avysk Plus 5/160 mg film-coated tablet | 160,5 | None | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 51.15 | C09DB01 |
| mixed | 3009200168 | 2020 | BITENS | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 64.549 | C09DB02 |
| mixed | 3009200171 | 2020 | BITENS | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 61.8 | C09DB02 |
| mixed | 3009200170 | 2020 | BITENS | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 49.75 | C09DB02 |
| pure | 1802165984 | 2016 | BLOCAL 5 mg capsule | 5 | None | Capsule, hard | Oral use | Prescription | Generic | DEEF MARKITING COMPANY | 23.8 | C08CA01 |
| mixed | 1309234204 | 2023 | Clodipan 16 mg and 5 mg | 16,5 | mg | Capsule, hard | Oral use | Prescription | NCE | ALNAGHI COMPANY | 64.65 | C09DB07 |
| mixed | 1309234203 | 2023 | Clodipan 8 mg and 5mg | 8,5 | mg | Capsule, hard | Oral use | Prescription | NCE | ALNAGHI COMPANY | 58.80 | C09DB07 |
| mixed | 0812211437 | 2021 | Concor Amlo | 5,10 | mg | Tablet | Oral use | Prescription | NCE | Salehiya Trading Co. | 55.55 | C07FB07 |
| mixed | 0812211438 | 2021 | Concor Amlo | 5,5 | mg | Tablet | Oral use | Prescription | NCE | Salehiya Trading Co. | 41.10 | C07FB07 |
| mixed | 1501256629 | 2019 | COVATEL | 40,5 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 45.7 | C09DB04 |
| mixed | 401-277-19 | 2019 | COVATEL | 80,5 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 59.2 | C09DB04 |
| mixed | 400-277-19 | 2019 | COVATEL | 80,10 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 59.2 | C09DB04 |
| mixed | 1501256630 | 2019 | COVATEL 40MG/10MG TABLET | 40,10 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 45.7 | C09DB04 |
| mixed | 10-597-09 | 2009 | COVERAM 10MG-10MG TABLETS | 10,10 | mg | Tablet | Oral use | Prescription | Generic | ALNAGHI COMPANY | 117.2 | C09BB04 |
| mixed | 9-597-09 | 2009 | COVERAM 10MG-5MG TABLETS | 5,10 | mg | Tablet | Oral use | Prescription | Generic | ALNAGHI COMPANY | 102.7 | C09BB04 |
| mixed | 8-597-09 | 2009 | COVERAM 5MG-10MG TABLETS | 10,5 | mg | Tablet | Oral use | Prescription | Generic | ALNAGHI COMPANY | 82.9 | C09BB04 |
| mixed | 7-597-09 | 2009 | COVERAM 5MG-5MG TABLETS | 5,5 | mg | Tablet | Oral use | Prescription | Generic | ALNAGHI COMPANY | 68.45 | C09BB04 |
| mixed | 1005210727 | 2021 | Erastapecs Co | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Apex Pharma | 47.05 | C09DB02 |
| mixed | 1005210729 | 2021 | Erastapecs Co | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Apex Pharma | 61.55 | C09DB02 |
| mixed | 1005210728 | 2021 | Erastapecs Co | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Apex Pharma | 66 | C09DB02 |
| mixed | 3010246128 | 2007 | EXFORGE 10 MG-160 MG F-C TABLETS | 160,10 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 74 | C09DB03 |
| mixed | 3010246129 | 2007 | EXFORGE 5MG-160 MG F.C. TABLETS | 160,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 66.9 | C09DB01 |
| mixed | 0604221923 | 2022 | Gizamlo | 150,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 61.10 | C09DB05 |
| mixed | 0604221922 | 2022 | Gizamlo | 300,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 61.10 | C09DB05 |
| mixed | 0604221921 | 2022 | Gizamlo | 300,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 61.10 | C09DB05 |
| pure | 2104257263 | 2012 | GLODIP 5MG CAPSULE | 5 | None | Capsule | Oral use | Prescription | Generic | MANAYER NAJD TRADING MEDICAL NEEDS CO. | 23.8 | C08CA01 |
| pure | 24-346-08 | 2008 | HYPODIPINE 5MG CAPSULES | 5 | mg | Capsule | Oral use | Prescription | Generic | United Pharmaceutical Establishment | 21.8 | C08CA01 |
| pure | 2109222626 | 2017 | LODIPAM 10 mg Film-Coated Tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 45.95 | C08CA01 |
| pure | 2109222628 | 2017 | LODIPAM 2.5 mg Film-Coated Tablet | 2.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 22.25 | C08CA01 |
| pure | 2109222630 | 2017 | LODIPAM 5 mg Film-Coated Tablet | 5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 23.8 | C08CA01 |
| pure | 0403256978 | 2007 | LOFRAL 10MG TABLETS | 10 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 26.6 | C08CA01 |
| pure | 0403256979 | 2007 | LOFRAL 5MG TABLETS | 5 | None | Tablet | Oral use | Prescription | Generic | Cigalah Group | 16.2 | C08CA01 |
| pure | 175-277-06 | 2006 | LOTENSE 10MG CAPSULES | 10 | mg | Capsule, hard | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 64.40 | C08CA01 |
| pure | 0902221711 | 2003 | LOTENSE 5MG CAP | 5 | mg | Capsule, hard | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 53.35 | C08CA01 |
| mixed | 1501256636 | 2012 | LOTEVAN 10/160MG FILM COATED TABLET | 160,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 62.9 | C09DB01 |
| mixed | 240-277-12 | 2012 | LOTEVAN 10/320MG FILM COATED TABLET | 320,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 93.25 | C09DB01 |
| mixed | 1501256627 | 2012 | LOTEVAN 5/160MG FILM COATED TABLET | 160,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 65.00 | C09DB01 |
| mixed | 238-277-12 | 2012 | LOTEVAN 5/320MG FILM COATED TABLET | 320,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 79.95 | C09DB01 |
| pure | 1111246167 | 2006 | LOWRAC 5MG CAPSULE | 5 | None | Capsule | Oral use | Prescription | Generic | Dallah Health Care Company | 21 | C08CA01 |
| pure | 126-119-22 | 2005 | LOWVASC 5MG CAPSULE | 5 | mg | Capsule | Oral use | Prescription | Generic | Salehiya Trading Co. | 27.35 | C08CA01 |
| mixed | 1509211056 | 2021 | Olcontro Plus | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 57.45 | C09DB02 |
| mixed | 1509211055 | 2021 | Olcontro Plus | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 43.90 | C09DB02 |
| mixed | 3103210654 | 2021 | Olmevasc | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 47.05 | C09DB02 |
| mixed | 3103210656 | 2021 | Olmevasc | 20,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 57.95 | C09DB02 |
| mixed | 3103210653 | 2021 | Olmevasc | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 61.55 | C09DB02 |
| mixed | 3103210657 | 2021 | Olmevasc | 40,10 | None | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 66 | C09DB02 |
| mixed | 2005257425 | 2025 | Olmexa | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 51.25 | None |
| mixed | 2005257429 | 2025 | Olmexa | 20,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 63.10 | None |
| mixed | 2005257438 | 2025 | Olmexa | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 66.95 | None |
| mixed | 2005257435 | 2025 | Olmexa | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 71.85 | None |
| mixed | 1004257220 | 2020 | OLMIDIP 20/5 mg FILM COATED TABLET | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 55.3 | C09DB02 |
| mixed | 2403257152 | 2020 | OLMIDIP 40/10 mg FILM COATED TABLET | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 71.75 | C09DB02 |
| mixed | 2403257154 | 2020 | OLMIDIP 40/5 mg FILM COATED TABLET | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 68.65 | C09DB02 |
| mixed | 0408210903 | 2021 | Olneda | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 77 | C09DB02 |
| mixed | 0408210901 | 2021 | Olneda | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 71.75 | C09DB02 |
| mixed | 0408210904 | 2021 | Olneda | 20,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 67.60 | C09DB02 |
| mixed | 0408210902 | 2021 | Olneda | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 54.90 | C09DB02 |
| mixed | H0000018708 | 2022 | Perinam | 14,10 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 88.40 | None |
| mixed | H0000018707 | 2022 | Perinam | 7,5 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 66.40 | None |
| mixed | H0000018659 | 2022 | Perinam | 3.5,2.5 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 40.25 | None |
| mixed | 2708245832 | 2024 | Pratima Duo | 5,5 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 50.15 | C09BB04 |
| mixed | 2708245831 | 2024 | Pratima Duo | 10,5 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 75.35 | C09BB04 |
| mixed | 2708245830 | 2024 | Pratima Duo | 10,10 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 85.90 | C09BB04 |
| mixed | 2708245829 | 2024 | Pratima Duo | 5,10 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 60.70 | C09BB04 |
| mixed | 0108233945 | 2023 | Pratima Trio | 5,1.25,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 94.95 | QC09BX01 |
| mixed | 0108233946 | 2023 | Pratima Trio | 5,1.25,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 83.20 | QC09BX01 |
| mixed | 0108233943 | 2023 | Pratima Trio | 10,2.5,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 138.65 | QC09BX01 |
| mixed | 0108233944 | 2023 | Pratima Trio | 10,10,2.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 150.40 | QC09BX01 |
| mixed | 2509305982 | 2024 | Prestoprix Plus | 10,10 | mg | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 85.90 | C09BB04 |
| mixed | 0509245865 | 2024 | Prestoprix Plus | 5,10 | mg | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 75.35 | C09BB04 |
| mixed | 0509245864 | 2024 | Prestoprix Plus | 5,5 | mg | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 50.15 | C09BB04 |
| mixed | 3107245712 | 2024 | PROVINDA PLUS | 5,5 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 50.15 | C09BB04 |
| mixed | 3107245714 | 2024 | PROVINDA PLUS | 5,10 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 60.70 | C09BB04 |
| mixed | 3107245713 | 2024 | PROVINDA PLUS | 10,5 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 75.35 | C09BB04 |
| mixed | 3107245711 | 2024 | PROVINDA PLUS | 10,10 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 85.90 | C09BB04 |
| mixed | 420-277-19 | 2019 | REDUVASC 150MG/10MG F.C.TABLET | 150,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 81.3 | C09DB05 |
| mixed | 419-277-19 | 2019 | REDUVASC 150MG/5MG F.C.TABLET | 150,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 81.3 | C09DB05 |
| mixed | 422-277-19 | 2019 | REDUVASC 300MG/10MG F.C.TABLET | 300,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 115.55 | C09DB05 |
| mixed | 421-277-19 | 2019 | REDUVASC 300MG/5MG F.C.TABLET | 300,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 115.55 | C09DB05 |
| mixed | 2201256734 | 2019 | SENERGY 10 MG/160 MG F.C. TABLET | 160,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 42.2 | C09DB01 |
| mixed | 2201256733 | 2019 | SENERGY 5 MG/160 MG F.C. TABLET | 160,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 42.2 | C09DB01 |
| mixed | 50-370-13 | 2013 | SEVIKAR 20/10MG FILM COATED TABLET | 20,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 86.90 | C09DB02 |
| mixed | 49-370-13 | 2013 | SEVIKAR 20/5MG FILM COATED TABLET | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 70.60 | C09DB02 |
| mixed | 48-370-13 | 2013 | SEVIKAR 40/10MG FILM COATED TABLET | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 99.05 | C09DB02 |
| mixed | 47-370-13 | 2013 | SEVIKAR 40/5MG FILM COATED TABLET | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 92.35 | C09DB02 |
| mixed | 0802244881 | 2018 | SEVITENSE 20/10 MG FILM COATED TABLET | 20,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 78.20 | C09DB02 |
| mixed | 0802244882 | 2018 | SEVITENSE 20/5 MG FILM COATED TABLET | 20,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 63.55 | C09DB02 |
| mixed | 0802244879 | 2018 | SEVITENSE 40/10 MG FILM COATED TABLET | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 89.15 | C09DB02 |
| mixed | 0802244880 | 2018 | SEVITENSE 40/5 MG FILM COATED TABLET | 40,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 83.10 | C09DB02 |
| mixed | 2504245211 | 2024 | Tenival | 5,160 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 56.85 | C09DB01 |
| mixed | 2504245212 | 2024 | Tenival | 10,160 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 62.90 | C09DB01 |
| mixed | 3010222839 | 2016 | TENORYL PLUS 10 mg/10 mg TABLET | 10,10 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 95.2 | C09BB04 |
| mixed | 3010222841 | 2016 | TENORYL PLUS 10 mg/5 mg TABLET | 5,10 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 83.45 | C09BB04 |
| mixed | 3010222842 | 2016 | TENORYL PLUS 5 mg/10 mg TABLET | 10,5 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 67.35 | C09BB04 |
| mixed | 3010222840 | 2016 | TENORYL PLUS 5 mg/5 mg TABLET | 5,5 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 55.6 | C09BB04 |
| mixed | 0510234306 | 2023 | Triplixam | 10,2.5,10 | mg | Film-coated tablet | Oral use | Prescription | NCE | Servier Saudi Arabia Trading LLC | 133.30 | C09BX01 |
| mixed | 0510234305 | 2023 | Triplixam | 5,1.25,10 | mg | Film-coated tablet | Oral use | Prescription | NCE | Servier Saudi Arabia Trading LLC | 94.95 | C09BX01 |
| mixed | 0510234309 | 2023 | Triplixam | 10,2.5,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Servier Saudi Arabia Trading LLC | 133.30 | C09BX01 |
| mixed | 0510234308 | 2023 | Triplixam | 5,1.25,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Servier Saudi Arabia Trading LLC | 83.20 | C09BX01 |
| mixed | 96-68-14 | 2014 | TWYNSTA | 80,5 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 72.85 | C09DB04 |
| mixed | 95-68-14 | 2014 | TWYNSTA | 80,10 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 72.85 | C09DB04 |
| mixed | 2207245626 | 2018 | UNISIA 8 MG/2.5 MG TABLET | 8,2.5 | mg | Tablet | Oral use | Prescription | NCE | Jazeera Pharmaceutical Industries (JPI) | 67 | C09DB07 |
| mixed | 2207245627 | 2018 | UNISIA 8 MG/5MG TABLET | 8,5 | mg | Tablet | Oral use | Prescription | NCE | Jazeera Pharmaceutical Industries (JPI) | 68.55 | C09DB07 |
| pure | 0408222409 | 2004 | VASCODIPINE | 10 | mg | Tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 63 | C08CA01 |
| pure | 0408222410 | 2004 | VASCODIPINE | 2.5 | mg | Tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 24.7 | C08CA01 |
| pure | 0408222408 | 2004 | VASCODIPINE | 5 | mg | Tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 43.2 | C08CA01 |
| mixed | 44-972-19 | 2021 | VIDONORM 10MG/4MG TABLET | 10,4 | mg | Tablet | Oral use | Prescription | NCE | AJA PHARMACEUTICAL INDUSTRIES | 79.30 | C09BB04 |
| mixed | 45-972-19 | 2021 | VIDONORM 10MG/8MG TABLET | 10,8 | mg | Tablet | Oral use | Prescription | NCE | AJA PHARMACEUTICAL INDUSTRIES | 90.40 | C09BB04 |
| mixed | 42-972-19 | 2021 | VIDONORM 5MG/4MG TABLET | 5,4 | mg | Tablet | Oral use | Prescription | NCE | AJA PHARMACEUTICAL INDUSTRIES | 52.80 | C09BB04 |
| mixed | 43-972-19 | 2021 | VIDONORM 5MG/8MG TABLET | 5,8 | mg | Tablet | Oral use | Prescription | NCE | AJA PHARMACEUTICAL INDUSTRIES | 63.90 | C09BB04 |
| mixed | 1502210517 | 2021 | Vittoria | 160,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 56.85 | C09DB01 |
| mixed | 1502210514 | 2021 | Vittoria | 320,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 71.95 | C09DB01 |
| mixed | 1502210518 | 2021 | Vittoria | 160,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 62.90 | C09DB01 |
| mixed | 1502210519 | 2021 | Vittoria | 320,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 83.90 | C09DB01 |

## glyceryl trinitrate — 5 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 17-5287-20 | 2020 | GLYCERYL TRINITRATE 50MG-10ML I-V AMP | 5 | mg/ml | Solution for injection | Intravenous use | Prescription | Generic | Pfizer Saudi Trading | 131.1 | C01DA02 |
| pure | 3007245699 | 1986 | NITRODERM TTS 5 PATCHES | 25 | mg | Transdermal patch | Transdermal use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 58.30 | C01DA02 |
| pure | 12-5773-23 | 1986 | NITRODERM TTS 5 PATCHES | 25 | mg | Transdermal patch | Transdermal use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 17.6 | C01DA02 |
| pure | 3007245700 | 1988 | NITRODERM TTS-10 SYSTEM | 50 | mg | Transdermal patch | Topical | Prescription | NCE | Farouk, Maamoun Tamer & CO | 33.75 | C01DA02 |
| pure | 131-11-94 | 1994 | NITRODERM TTS-10 SYSTEM | 50 | mg | Transdermal patch | Topical | Prescription | NCE | Farouk, Maamoun Tamer & CO | 62.6 | C01DA02 |

## isosorbide dinitrate — 2 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2111222917 | 2006 | ISOBIDE | 40 | mg | Modified-release capsule | Oral use | Prescription | Generic | RIYADH PHARMA | 23.75 | C01DA08 |
| pure | 0108222392 | 2006 | ISOBIDE | 20 | mg | Modified-release capsule | Oral use | Prescription | Generic | RIYADH PHARMA | 16.40 | C01DA08 |

## adenosine — 6 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1209234181 | 2016 | ADENOCOR 6MG-2ML VIAL | 3 | mg/ml | Solution for injection | Intravenous use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 153.45 | C01EB10 |
| pure | 12-178-13 | 2013 | ADENOHARDT 30MG/10ML SOLUTION FOR INFUSION | 3 | mg/ml | Solution for injection | Intravenous use | Prescription | NCE | Abdulrehman Algosaibi G.T.C. | 339.40 | C01EB10 |
| pure | 0801233066 | 2013 | ADENOHARDT 6MG/2ML SOLUTION FOR INFUSION | 3 | mg/ml | Solution for injection | Intravenous use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 140.50 | C01EB10 |
| pure | 2207257794 | 2020 | Cardesine 6mg/2ml Solution for Injection | 3 | None | Solution for injection | Intravenous use | Prescription | Generic | Cigalah Group | 122.20 | C01EB10 |
| pure | 28-993-20 | 2020 | REVARDIA | 3 | mg/ml | Solution for injection | Intravenous use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 156.15 | C01EB10 |
| pure | 0212200305 | 2020 | Xoria | 3 | mg/ml | Solution for injection | Intravenous use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 110 | C01EB10 |

## amiodarone — 4 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2310246095 | 1993 | CORDARONE 150MG-3ML AMP. | 50 | None | Solution for injection | Intravenous use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 82.20 | C01BD01 |
| pure | 1905222046 | 2016 | CORDARONE 200MG TAB | 200 | mg | Tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 25.30 | C01BD01 |
| pure | 28-355-02 | 2002 | SEDACORON 200MG TAB | 200 | mg | Tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 25.35 | C01BD01 |
| pure | 27-355-02 | 2002 | SEDACORON solution for injection | 50 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 17.25 | C01BD01 |

## digoxin — 4 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 10-887-16 | 2016 | LANOXIN 0.05MG-ML ELIXIR | 0.05 | None | Solution | Oral use | Prescription | NCE | ALNAGHI COMPANY | 22.75 | C01AA05 |
| pure | 59-887-20 | 2020 | LANOXIN 0.125MG TAB | 0.125 | None | Tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 16.1 | C01AA05 |
| pure | 1806257576 | 2020 | LANOXIN 0.25MG TAB | 0.25 | None | Tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 11.7 | C01AA05 |
| pure | 1607257768 | 2016 | LANOXIN 0.25MG/ML INJ | 0.25 | mg/ml | Solution for injection | Intravenous use | Prescription | Generic | ALNAGHI COMPANY | 13.2 | C01AA05 |

## lidocaine — 58 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mixed | 1210222707 | 2016 | 0.4% LIDOCAINE HCL AND 5% DEXTROSE IV infusion USP | 5,0.4 | % | Solution | Intravenous use | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 35 | N01BB52 |
| pure | 0108222387 | 2000 | 1% W-V LIDOCAINE HCL INJECTION USP | 1 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 9.00 | N01BB02 |
| pure | 0108222389 | 2000 | 1% W-V LIDOCAINE HCL INJECTION USP | 1 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 8.60 | N01BB02 |
| pure | 3005222094 | 2002 | 2% W-V LIDOCAINE HCL INJECTION USP | 2 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 8.40 | N01BB02 |
| pure | 0108222386 | 2002 | 2% W-V LIDOCAINE HCL INJECTION USP | 2 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 7.75 | N01BB02 |
| pure | 0108222388 | 2002 | 2% W-V LIDOCAINE HCL INJECTION USP | 2 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 6.75 | N01BB02 |
| pure | 246-149-02 | 2002 | 2% W-V LIDOCAINE HCL INJECTION USP | 2 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 4.15 | N01BB02 |
| pure | 1109234161 | 2008 | AVALON AVOCAINE | 10 | % | Spray | Topical | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 24.45 | D04AB01 |
| mixed | 1603200038 | 2020 | DERMALSTYLE forte Lidocaine | 23,0.3 | mg/ml | Gel for injection | Subcutaneous use | Prescription | Generic | ELAGY ESTABLISHMENT FOR TRADING | 342.352 | None |
| mixed | 1603200039 | 2020 | DERMALSTYLE smile Lidocaine | 23,0.3 | mg/ml | Gel for injection | Subcutaneous use | Prescription | Generic | ELAGY ESTABLISHMENT FOR TRADING | 342.352 | None |
| mixed | 109-539-19 | 2019 | ENNLA 5% Cream | 25,25 | mg/g | Cream | Topical | Prescription | Generic | DEEF MARKITING COMPANY | 9.9 | N01BB02 |
| mixed | 2503257161 | 2019 | ENNLA 5% Cream | 25,25 | mg/g | Cream | Topical | Prescription | Generic | DEEF MARKITING COMPANY | 29.7 | N01BB02 |
| mixed | 111-539-19 | 2019 | ENNLA 5% Cream | 25,25 | mg/g | Cream | Topical | Prescription | Generic | DEEF MARKITING COMPANY | 59.4 | N01BB02 |
| mixed | 275-186-09 | 2009 | HAEMOPROCT | 5,2 | % | Rectal ointment | Rectal use | Prescription | Generic | Cigalah Group | 11.6 | C05AX05 |
| mixed | 2106233832 | 2023 | Imla | 2.50,2.50 | % (W/W) | Cream | Topical | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 47.00 | None |
| pure | 14-590-10 | 2010 | LEDO 5% W-W OINTMENT | 5 | % | Ointment | Topical | Prescription | Generic | BATTERJEE PHARMACEUTICAL FACTORY | 4.4 | D04AB01 |
| mixed | 0508245724 | 2024 | Lidapro | 2.5,2.5 | % (W/W) | Cream | Topical | Prescription | Generic | Dallah Health Care Company | 47.00 | N01BB20 |
| pure | 150-186-01 | 2001 | LIDOCAINE 5 % OINTMENT | 5 | % | Ointment | Topical | Prescription | Generic | Cigalah Group | 8.15 | D04AB01 |
| pure | 2911211391 | 2000 | LIDOCAINE HCL 1% AMPOULE | 1 | % | Solution for injection | Intravenous use | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 4 | N01BB02 |
| pure | 217-149-00 | 2000 | LIDOCAINE HCL 1% AMPOULE | 1 | % | Solution for injection | Intravenous use | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 3.15 | N01BB02 |
| pure | 2107222336 | 2000 | LIDOCAINE HCL 1% AMPOULE | 1 | % | Solution for injection | Intravenous use | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 3.80 | N01BB02 |
| pure | 0401244677 | 1994 | LIDOCAINE HCL 2% INJ 20ML | 2 | % | Solution for injection | Intravenous use | Prescription | Generic | Medical Supplies And Services Co Ltd (Mediserv) | 80.10 | N01BB02 |
| pure | 2405222058 | 1990 | LIDOCAINE HCL EMERGENCY SYRINGE 1% | 1 | % | Solution for injection | Intravenous use | Prescription | Generic | Pfizer Saudi Trading | 21.45 | N01BB02 |
| pure | 2405222059 | 1990 | LIDOCAINE HCL EMERGENCY SYRINGE 2% | 2 | % | Solution for injection | Intravenous use | Prescription | Generic | Pfizer Saudi Trading | 21.45 | N01BB02 |
| pure | 0512211423 | 2016 | LIDOCAINE HYDROCHLORIDE 1% solution for injection | 1 | % | Solution for injection | Parenteral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 247.5 | N01BB02 |
| pure | 0905233615 | 2023 | lidocaine Hydrochloride 2% w/v | 2 | % | Solution for injection | intramuscular, subcutaneous | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 5.40 | N01BB02 |
| mixed | 2512246493 | 2024 | Lignox | 2.5,2.5 | % (W/W) | Cream | Topical | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 9.40 | N01BB20 |
| mixed | 2512246492 | 2025 | Lignox | 2.5,2.5 | % (W/W) | Cream | Topical | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 47 | N01BB20 |
| mixed | 2512246494 | 2024 | Lignox | 2.5,2.5 | % (W/W) | Cream | Topical | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 56.40 | N01BB20 |
| pure | 2610222823 | 2013 | LIOCAINE 2% GEL | 2 | None | Gel | Topical | OTC | Generic | Salehiya Trading Co. | 7.70 | D04AB01 |
| pure | 2401244801 | 2024 | LIPRO SPRAY 10% | 100 | mg/g | Solution for spray | Topical | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 22.30 | N01BB02 |
| mixed | 1311234464 | 1987 | MINIMS LIDOCAINE and FLUORESCEIN | 4,0.25 | % | Eye drops, solution | Ophthalmic use | Prescription | NCE | ALNAGHI COMPANY | 60.05 | S01JA51 |
| mixed | 2807257873 | 2025 | Mydrane | 0.2,3.1,10 | mg/ml | Solution for injection | Ophthalmic use | Prescription | NCE | PharmaZone (Netaq Al Dawa) Pharmaceuticals | 763.60 | None |
| mixed | 5-120-85 | 1985 | NEO-HAEMORRHAN OINT | None | None | Ointment | Topical | Prescription | Generic | United Pharmaceutical Establishment | 3.65 | C05AA04 |
| mixed | 6-120-85 | 1985 | NEO-HAEMORRHAN SUPP. | None | None | Suppository | Rectal use | Prescription | Generic | United Pharmaceutical Establishment | 3 | C05AA04 |
| mixed | 27-993-20 | 2021 | NEURODERM | 70,70 | mg/g | Cream | Topical | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 39.60 | N01BB52 |
| mixed | 8-222-95 | 1995 | OLFEN-75 | 75,20 | mg/ml | Solution for injection | Parenteral use | Prescription | Generic | Cigalah Group | 23.6 | M01AB05 |
| mixed | 0411200253 | 2020 | Otipax | 4,1 | g | Ear drops, solution | Auricular use | Prescription | Generic | Al-Safa Warehouse For Pharmaceuticals Ltd | 8.558 | S02DA30 |
| mixed | 1610234339 | 2018 | PILOCIN | 50,20 | mg/g | Cream | Rectal use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 15.00 | C05AD01 |
| mixed | 2311234539 | 2023 | Pliaglis 15 gram Cream | 7,7 | % | Cream | Topical | Prescription | NCE | Salehiya Trading Co. | 76.90 | N01BB52 |
| mixed | 2311234540 | 2023 | Pliaglis 30 gram Cream | 7,7 | % | Cream | Topical | Prescription | NCE | Salehiya Trading Co. | 139.15 | N01BB52 |
| mixed | 0412222973 | 2022 | Prila | 2.5,2.5 | % | Cream | Topical | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 66.00 | N01BB02 |
| mixed | 0407245483 | 2010 | PRILA 5% CREAM | 2.5,2.5 | % | Cream | Topical | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 55 | N01BB52 |
| mixed | 2302221760 | 1996 | PROCTO GLYVENOL | 5,2 | None | Cream | Topical | Prescription | Generic | Haleon Arabia Limited | 35.45 | C05AX05 |
| mixed | 2012211492 | 1980 | PROCTO GLYVENOL | 400,40 | None | Suppository | Rectal use | Prescription | NCE | ALNAGHI COMPANY | 26.70 | C05AX05 |
| mixed | 97-334-05 | 2005 | RECTACURE | 5,2 | % | Cream | Rectal use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 15 | C05AX05 |
| pure | 0309234089 | 2018 | RIALOCAINE 2 % Gel | 2 | % | Gel | Topical | OTC | Generic | RIYADH PHARMA | 11 | D04AB01 |
| pure | 2509222636 | 2001 | RIALOCAINE 2 % Gel | 2 | % | Gel | Topical | OTC | Generic | RIYADH PHARMA | 7.35 | D04AB01 |
| pure | 2403257139 | 2025 | Senso | 5 | % | Transdermal patch | Transdermal use | Prescription | Generic | Saudi Amarox | 326.15 | N01BB02 |
| pure | 3112200376 | 2020 | SOLYO | 10 | None | Solution for injection | Intravenous use | Prescription | Generic | UNITED CORPORATION FOR PHARMACEUTICAL & MEDICAL SERVICES LTD. | 7 | N01BB02 |
| mixed | H0000006644 | 2021 | TEOSYAL PureSence ULTRA DEEP | 25,0.3 | % | Gel for injection | Subcutaneous use | Prescription | Generic | AME compant for Medical Supplies | 725.05 | None |
| mixed | H0000006281 | 2021 | Teosyal PureSense KISS | 25,0.3 | % | Gel for injection | Intradermal use | Prescription | Generic | AME compant for Medical Supplies | 707.85 | None |
| mixed | H0000006421 | 2021 | TEOSYAL PureSense REDENSITY 2 | 15,0.3 | % | Gel for injection | Intradermal use | Prescription | Generic | AME compant for Medical Supplies | 418.60 | None |
| mixed | H0000006622 | 2021 | TEOSYAL PureSense ULTIMATE | 22,0.3 | % | Gel for injection | Subcutaneous use | Prescription | Generic | AME compant for Medical Supplies | 531.70 | None |
| pure | 10-328-25 | 2011 | VERSATIS 5% MEDICATED PLASTER | 5 | None | Medicated plaster | Topical | Prescription | Generic | AL-KAMAL IMPORT OFFICE CO. LTD. | 98.05 | D04AB01 |
| pure | 2609222650 | 2011 | VERSATIS 5% MEDICATED PLASTER | 5 | None | Medicated plaster | Topical | Prescription | Generic | AL-KAMAL IMPORT OFFICE CO. LTD. | 465.90 | D04AB01 |
| mixed | 1-258-98 | 1998 | XYLONOR SPRAY | 15,0.15 | % | Spray | Nasal use | Prescription | NCE | Abdulrauf Ibrahim Batterjee & Bros. Company | 22.6 | N01BB52 |
| pure | 1411246223 | 2005 | XYLOPHIL 2% GEL | 2 | None | Gel | Topical | OTC | Generic | ZIMMO TRADING ESTABLISHMENT | 6 | D04AB01 |

## propranolol — 5 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 15-7-81 | 1981 | INDERAL TABLETS 10 MG. | 10 | mg | Tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 20 | C07AA05 |
| pure | 16-7-81 | 1981 | INDERAL TABLETS 40 MG. | 40 | mg | Tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 40 | C07AA05 |
| pure | 94-119-00 | 2000 | INDICARDIN 10 mg tablet | 10 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 7 | C07AA05 |
| pure | 95-119-00 | 2000 | INDICARDIN 40 mg tablet | 40 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 15 | C07AA05 |
| pure | 1902233259 | 2016 | PROTENSE 40 mg/5 ml oral solution | 8 | mg/ml | Oral solution | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 110 | C07AA05 |

## hydralazine — 9 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1607245584 | 2024 | Aprolin | 10 | mg | Tablet | Oral use | Prescription | Generic | Saudi Amarox | 20 | C02DB02 |
| pure | 1607245585 | 2024 | Aprolin | 50 | mg | Tablet | Oral use | Prescription | Generic | Saudi Amarox | 100 | C02DB02 |
| pure | 1106233783 | 2023 | Aprolin | 25 | mg | Tablet | Oral use | Prescription | Generic | Saudi Amarox | 50.00 | None |
| pure | 0306257544 | 2025 | Barolex | 25 | mg | Tablet | Oral use | Prescription | Generic | Medical and Pharmaceutical Services Company | 15.00 | None |
| pure | 0306257543 | 2025 | Barolex | 50 | mg | Tablet | Oral use | Prescription | Generic | Medical and Pharmaceutical Services Company | 30.00 | None |
| pure | 306257544 | 2025 | Barolex | 25 | mg | Tablet | Oral use | Prescription | Generic | Medical and Pharmaceutical Services Company | 15.00 | None |
| pure | 306257543 | 2025 | Barolex | 50 | mg | Tablet | Oral use | Prescription | Generic | Medical and Pharmaceutical Services Company | 30.00 | None |
| pure | 2303257129 | 2025 | Hydralazine Sciegen | 25 | mg | Tablet | Oral use | Prescription | Generic | ARABIAN OASIS | 15.00 | None |
| pure | 2303257127 | 2025 | Hydralazine Sciegen | 50 | mg | Tablet | Oral use | Prescription | Generic | ARABIAN OASIS | 30.00 | None |

## hydrochlorothiazide — 118 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mixed | 56-124-00 | 2000 | AMURETIC 5MG/50MG TAB | 50,5 | mg | Tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 8.75 | C03EA01 |
| mixed | 2803221891 | 2015 | ARBAVAL PLUS | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 27.25 | C09DA03 |
| mixed | 2803221889 | 2015 | ARBAVAL PLUS | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 27.25 | C09DA03 |
| mixed | 2803221890 | 2015 | ARBAVAL PLUS | 320,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 37.15 | C09DA03 |
| mixed | 1301256602 | 2012 | ARBITEN PLUS | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | AL-DAWAA MEDICAL SERVICES CO. LTD | 29.8 | C09DA03 |
| mixed | 1102256877 | 2012 | ARBITEN PLUS | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | AL-DAWAA MEDICAL SERVICES CO. LTD | 32.5 | C09DA03 |
| mixed | 1102256879 | 2012 | ARBITEN PLUS | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | AL-DAWAA MEDICAL SERVICES CO. LTD | 32.5 | C09DA03 |
| mixed | 0309234095 | 2017 | ARENA PLUS 150 mg/12.5 mg Film Coated Tablet | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 45.80 | C09CA04 |
| mixed | 0309234094 | 2017 | ARENA PLUS 300 mg/12.5 mg Film Coated Tablet | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 55.95 | C09CA04 |
| mixed | 0309234096 | 2017 | ARENA PLUS 300 mg/25 mg Film Coated Tablet | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 55.95 | C09CA04 |
| mixed | 18-5444-25 | 2020 | ATACAND PLUS TABLET | 16,12.5 | mg | Tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 75.90 | C09DA06 |
| mixed | 2005245323 | 2024 | Avysk HCT | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 27.80 | C09DA03 |
| mixed | 2005245324 | 2024 | Avysk HCT | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 30.30 | C09DA03 |
| mixed | 2005245325 | 2024 | Avysk HCT | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 30.30 | C09DA03 |
| mixed | 119-119-09 | 2009 | BLOPRESS 16 PLUS TABLETS | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 54.65 | C09DA06 |
| mixed | 118-119-09 | 2009 | BLOPRESS 8 PLUS TABLETS | 8,12.5 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 47.7 | C09DA06 |
| mixed | 7-849-13 | 1980 | CAFERGOT 1 MG TAB | 100,1,12.5,600 | mg | Tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 16.3 | None |
| mixed | 2811211379 | 2016 | CANDAN PLUS 16/12.5 mg tablet | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | Middle East Pharmaceutical Industries Co Ltd Avalon Pharma | 51.35 | C09DA06 |
| mixed | 1706257566 | 2018 | CANDEZA 16/12.5 mg TABLETS | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 34.45 | C09DA06 |
| mixed | 1706257568 | 2018 | CANDEZA 8/12.5 mg TABLETS | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 23.45 | C09DA06 |
| mixed | 1809234222 | 2018 | CARDEX PLUS 10/25 mg F.C TABLETS | 25,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 38.85 | C07BB07 |
| mixed | 1809234221 | 2018 | CARDEX PLUS 5/12.5 mg F.C TABLETS | 12.5,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 25.25 | C07BB07 |
| mixed | 0501221563 | 2013 | CARDICOR PLUS 5/12.5MG FILM COATED TABLET | 12.5,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 22.7 | C07BB07 |
| mixed | 2702256959 | 2019 | CO-ANGINET | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 22.4 | C09DA03 |
| mixed | 2702256957 | 2019 | CO-ANGINET | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 24.5 | C09DA03 |
| mixed | 2702256960 | 2019 | CO-ANGINET | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 24.5 | C09DA03 |
| mixed | 5-244-03 | 2003 | Co-Aprovel 150-12.5 MG TABLET | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 63 | C09DA04 |
| mixed | 1211246205 | 2018 | CO-CINFAVAL | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 22.85 | C09CA03 |
| mixed | 1211246208 | 2018 | CO-CINFAVAL | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 22.85 | C09CA03 |
| mixed | 1211246209 | 2018 | CO-CINFAVAL | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 11.45 | C09CA03 |
| mixed | 2204245191 | 2008 | CO-DIOVAN | 320,25 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 57.85 | C09DA03 |
| mixed | 2204245192 | 2008 | CO-DIOVAN | 320,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 57.85 | C09DA03 |
| mixed | 1408222483 | 2003 | CO-DIOVAN | 160,25 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 42.5 | C09DA03 |
| mixed | 1408222488 | 2002 | CO-DIOVAN | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 42.5 | C09DA03 |
| mixed | 1408222487 | 2000 | CO-DIOVAN | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Novartis Saudi Limited | 38.95 | C09DA03 |
| mixed | 308-212-14 | 2014 | CO-IRBETEL 162.5 mg film-coated tablet | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 53.55 | C09DA04 |
| mixed | 309-212-14 | 2014 | CO-IRBETEL 312.5 mg film-coated tablet | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 65.45 | C09DA04 |
| mixed | 310-212-14 | 2014 | CO-IRBETEL 325 mg film-coated tablet | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 65.45 | C09DA04 |
| mixed | 1301256594 | 2019 | CO-OLMEPRESS 20 mg/12.5 mg F.C. Tablet | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 48.8 | C09DA08 |
| mixed | 1301256596 | 2019 | CO-OLMEPRESS 40 mg/12.5 mg F.C. Tablet | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 66.15 | C09DA08 |
| mixed | 1301256597 | 2019 | CO-OLMEPRESS 40 mg/25 mg F.C. Tablet | 40,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 66.15 | C09DA08 |
| mixed | 0303210582 | 2021 | CO-Ribex | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 29.85 | C03AA03 |
| mixed | 0303210583 | 2021 | CO-Ribex | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 28.90 | C03AA03 |
| mixed | 0303210584 | 2021 | CO-Ribex | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 24.55 | C03AA03 |
| mixed | 2208245814 | 2012 | CO-TABUVAN | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 33.1 | C09DA03 |
| mixed | 2208245812 | 2012 | CO-TABUVAN | 320,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 49.15 | C09DA03 |
| mixed | 2208245905 | 2012 | CO-TABUVAN | 320,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 49.15 | C09DA03 |
| mixed | 2208245815 | 2012 | CO-TABUVAN | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 36.1 | C09DA03 |
| mixed | 2208245813 | 2012 | CO-TABUVAN | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 36.1 | C09DA03 |
| mixed | 318-212-14 | 2014 | CO-VALISTA | 320,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 41.3 | C09DA03 |
| mixed | 317-212-14 | 2014 | CO-VALISTA | 320,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 41.3 | C09DA03 |
| mixed | 316-212-14 | 2014 | CO-VALISTA | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 30.3 | C09DA03 |
| mixed | 315-212-14 | 2014 | CO-VALISTA | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 30.3 | C09DA03 |
| mixed | 314-212-14 | 2014 | CO-VALISTA | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 27.8 | C09DA03 |
| mixed | 56-968-20 | 2020 | CO-ZANSOR 150/12.5MG F.C TABLETS | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 39.05 | C09DA04 |
| mixed | 54-968-20 | 2020 | CO-ZANSOR 300/12.5MG F.C. TABLETS | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 47.70 | C09DA04 |
| mixed | 55-968-20 | 2020 | CO-ZANSOR 300/25MG F.C. TABLETS | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 47.70 | C09DA04 |
| mixed | 1003221840 | 2018 | COAPROVEL 300-12.5 MG TABLET | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 77 | C09DA04 |
| mixed | 1512223018 | 2016 | COAPROVEL 300-25MG F.C. TABLETS | 300,25 | mg | Film-coated tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 77 | C09DA04 |
| mixed | 0311211255 | 2016 | CoDICERAN 16/12.5 film-coated tablet | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 41.35 | C09DA06 |
| mixed | 2904257310 | 1999 | CONCOR 5 PLUS F.C. TABLETS | 12.5,5 | mg | Film-coated tablet | Oral use | Prescription | NCE | ALHAYA MEDICAL CO | 19.5 | C07BB07 |
| mixed | 1109234163 | 2018 | COVAZ | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 30.30 | C09CA03 |
| mixed | 1109234162 | 2018 | COVAZ | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 27.80 | C09CA03 |
| mixed | 1109234164 | 2018 | COVAZ | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 30.30 | C09CA03 |
| mixed | 2006222223 | 2017 | DIOSTAR PLUS | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 22.40 | C09DA03 |
| mixed | 2006222221 | 2017 | DIOSTAR PLUS | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 24.5 | C09DA03 |
| mixed | 2006222222 | 2017 | DIOSTAR PLUS | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 24.5 | C09DA03 |
| mixed | 1-5130-19 | 2019 | DIOZAD | 160,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Razy Al Madina Pharmaceutical | 24.5 | C03AA03 |
| mixed | 2-5130-19 | 2019 | DIOZAD | 160,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Razy Al Madina Pharmaceutical | 24.5 | C03AA03 |
| mixed | 3-5130-19 | 2019 | DIOZAD | 80,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Razy Al Madina Pharmaceutical | 22.4 | C03AA03 |
| mixed | 4-5130-19 | 2019 | DIOZAD | 320,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Razy Al Madina Pharmaceutical | 30.1 | C03AA03 |
| mixed | 5-5130-19 | 2019 | DIOZAD | 320,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Razy Al Madina Pharmaceutical | 33.45 | C03AA03 |
| mixed | 10-5492-21 | 2021 | Erastapecs Plus 20/12.5MG F.C.TABLET | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Apex Pharma | 47.95 | None |
| mixed | 11-5492-21 | 2021 | Erastapecs Plus 40/12.5MG F.C.TABLET | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Apex Pharma | 63.80 | None |
| pure | 1009234160 | 2019 | ESIDREX TAB. 25 MG | 25 | mg | Tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 17.25 | C03AA03 |
| mixed | 58-5286-20 | 2020 | GARDIA PLUS 16/12.5MG TABLETS | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 34.45 | C09DA06 |
| mixed | 59-5286-20 | 2020 | GARDIA PLUS 8/12.5MG TABLETS | 16,12.5 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 23.45 | C09DA06 |
| mixed | 2812211515 | 2021 | Gizlan HCT | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 29.65 | C09DA04 |
| mixed | 2812211517 | 2021 | Gizlan HCT | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 29.65 | C09DA04 |
| mixed | 0410211104 | 2021 | Gizlan HCT | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 29.65 | C09DA04 |
| mixed | 5-5035-17 | 2017 | IRBEGEN PLUS 150/12.5 mg Film Coated Tablet | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SCIENTIFIC PRODUCTS PHARMACEUTICAL CO. LTD | 36 | C09CA04 |
| mixed | 6-5035-17 | 2017 | IRBEGEN PLUS 300/12.5 mg Film Coated Tablet | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | SCIENTIFIC PRODUCTS PHARMACEUTICAL CO. LTD | 47.70 | C09CA04 |
| mixed | 7-5035-17 | 2017 | IRBEGEN PLUS 300/25 mg Film Coated Tablet | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | SCIENTIFIC PRODUCTS PHARMACEUTICAL CO. LTD | 47.70 | C09CA04 |
| mixed | 47-444-20 | 2021 | Irma-HCT 150 mg / 12.5 mg | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 36 | C09DA04 |
| mixed | 48-444-20 | 2021 | IRMA-HCT 300 mg / 12.5 mg | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 47.75 | C09DA04 |
| mixed | 0712211432 | 2016 | IROVEL PLUS 150/12.5 mg film-coated tablet | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 48.20 | C09DA04 |
| mixed | 0712211435 | 2016 | IROVEL PLUS 300/12.5 mg film-coated tablet | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 58.90 | C09DA04 |
| mixed | 0712211436 | 2016 | IROVEL PLUS 300/25 mg film-coated tablet | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 58.90 | C09DA04 |
| mixed | 86-68-05 | 2005 | MICARDIS PLUS | 40,12.5 | mg | Tablet | Oral use | Prescription | NCE | Cigalah Group | 65.05 | C09DA07 |
| mixed | 1707245588 | 2005 | MICARDIS PLUS | 80,12.5 | mg | Tablet | Oral use | Prescription | NCE | Cigalah Group | 65.05 | C09DA07 |
| pure | 2304245198 | 2000 | MONOZIDE 12.5MG TAB | 12.5 | mg | Tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 8.4 | C03AA03 |
| pure | 83-171-21 | 2021 | MONOZIDE 25MG TAB | 25 | mg | Tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 327.05 | C03AA03 |
| pure | 2706245454 | 2000 | MONOZIDE 25MG TAB | 25 | mg | Tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 14.2 | C03AA03 |
| mixed | 1501256625 | 2019 | NIZORTAN PLUS | 40,12.5 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 53.3 | C09DA07 |
| mixed | 1501256631 | 2019 | NIZORTAN PLUS | 80,12.5 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 53.3 | C09DA07 |
| mixed | 1501256634 | 2019 | NIZORTAN PLUS | 80,25 | mg | Tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 53.3 | C09DA07 |
| mixed | 2906222284 | 2016 | NORMATEC PLUS 20/12.5 mg film-coated tablet | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 59.2 | C09DA08 |
| mixed | 2906222282 | 2016 | NORMATEC PLUS 40/12.5 mg film-coated tablet | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 78.8 | C09DA08 |
| mixed | 2906222283 | 2016 | NORMATEC PLUS 40/25 mg film-coated tablet | 40,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 78.8 | C09DA08 |
| mixed | 0806210770 | 2021 | Olcontro HCT | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 63.80 | C09DA08 |
| mixed | 0806210771 | 2021 | Olcontro HCT | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 47.95 | C09DA08 |
| mixed | 13-5362-20 | 2020 | OLMAZIDE 20/12.5MG F.C.TABLET | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 47.95 | C09DA08 |
| mixed | 14-5362-20 | 2020 | OLMAZIDE 40/12.5MG | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 63.80 | C09DA08 |
| mixed | 15-5362-20 | 2020 | OLMAZIDE 40/25MG | 40,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 63.80 | C09DA08 |
| mixed | 40-370-08 | 2008 | OLMETEC PLUS 20MG-12.5MG F.C. TABLETS | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 65.60 | C09DA08 |
| mixed | 41-370-08 | 2008 | OLMETEC PLUS 40MG-12.5MG F.C. TABLETS | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 87.30 | C09DA08 |
| mixed | 42-370-08 | 2008 | OLMETEC PLUS 40MG-25MG F.C. TABLETS | 40,25 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 87.30 | C09DA08 |
| mixed | 0502244845 | 2024 | Olmetrol Plus | 40,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 63.80 | C09DA08 |
| mixed | 0502244843 | 2024 | Olmetrol Plus | 20,12.50 | mg | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 47.95 | C09DA08 |
| mixed | 0502244844 | 2024 | Olmetrol Plus | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | ALHAYA MEDICAL CO | 63.80 | C09DA08 |
| mixed | 1510200208 | 2020 | Olsar Plus | 20,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 53.30 | C09DA08 |
| mixed | 1510200209 | 2020 | Olsar Plus | 40,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 70.90 | C09DA08 |
| mixed | 1510200211 | 2020 | Olsar Plus | 40,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 70.90 | C09DA08 |
| mixed | 1506222196 | 2009 | SELECTA PLUS 5MG-12.5MG F.C. TABLETS | 12.5,5 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 19.55 | C07AB07 |
| mixed | 1704245170 | 2005 | TEVETEN PLUS 600-12.5MG FILM COATED TAB. | 12.5,600 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 76.50 | C09DA02 |
| mixed | 53-271-19 | 2019 | VIVAZAC PLUS 150MG/12.5MG F.C.TABLET | 150,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 36 | C09DA04 |
| mixed | 52-271-19 | 2019 | VIVAZAC PLUS 300MG/12.5MG F.C.TABLET | 300,12.5 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 47.70 | C09DA04 |
| mixed | 51-271-19 | 2019 | VIVAZAC PLUS 300MG/25MG F.C.TABLET | 300,25 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 47.70 | C09DA04 |

## lisinopril — 21 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 11-399-04 | 2004 | LINOPRIL 10MG TABLET | 10 | None | Tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 26.00 | C09AA03 |
| pure | 12-399-04 | 2004 | LINOPRIL 20MG TABLET | 20 | None | Tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 41.25 | C09AA03 |
| pure | 10-399-04 | 2004 | LINOPRIL 5MG TABLET | 5 | None | Tablet | Oral use | Prescription | Generic | SAUDI ARABIAN DRUG STORE COMPANY | 15.80 | C09AA03 |
| pure | 2611246341 | 2006 | LISINO 10MG TABLETS | 10 | None | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 27.85 | C09AA03 |
| pure | 0707245490 | 2006 | LISINO 20MG TABLETS | 20 | None | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 47.50 | C09AA03 |
| pure | 0701256531 | 2006 | LISINO 5MG TABLET | 5 | None | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 16.85 | C09AA03 |
| pure | 1303257061 | 2025 | Omace | 5 | mg | Tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 474.00 | C09AA03 |
| pure | 1303257059 | 2025 | Omace | 10 | mg | Tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 779.75 | C09AA03 |
| pure | 1303257057 | 2025 | Omace | 20 | mg | Tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 1279.60 | C09AA03 |
| pure | 1303257058 | 2006 | OMACE 10MG TABLETS | 10 | None | Tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 26.00 | C09AA03 |
| pure | 1303257056 | 2006 | OMACE 20MG TABLETS | 20 | None | Tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 44.35 | C09AA03 |
| pure | 1303257060 | 2006 | OMACE 5MG TABLETS | 5 | None | Tablet | Oral use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 15.80 | C09AA03 |
| pure | 0406257547 | 1991 | ZESTRIL 10MG TAB | 10 | None | Tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 26 | C09AA03 |
| pure | 0406257546 | 1991 | ZESTRIL 20MG TAB | 20 | None | Tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 44.35 | C09AA03 |
| pure | 0406257548 | 1991 | ZESTRIL 5MG TAB | 5 | None | Tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 15.8 | C09AA03 |
| pure | 0310246009 | 2024 | ZINOPRIL | 20 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 376.95 | C09AA03 |
| pure | 0310246008 | 2024 | ZINOPRIL | 10 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 221.00 | C09AA03 |
| pure | 0310246007 | 2024 | ZINOPRIL | 5 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 134.30 | C09AA03 |
| pure | 2610222809 | 2002 | ZINOPRIL 10 MG TAB | 10 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 26.00 | C09AA03 |
| pure | 1911246270 | 2002 | ZINOPRIL 20 MG TABLET | 20 | None | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 44.35 | C09AA03 |
| pure | 2610222817 | 2002 | ZINOPRIL 5 MG TABLETS | 5 | mg | Tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 15.80 | C09AA03 |

## captopril — 8 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2511246334 | 2004 | ACETAB 25 MG TABLETS | 25 | None | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 20.25 | C09AA01 |
| pure | 0801256558 | 2004 | ACETAB 50 MG TABLETS | 50 | None | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 34.2 | C09AA01 |
| pure | 38-124-95 | 1995 | CAPOCARD 25MG TAB | 25 | mg | Tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 15.15 | C09AA01 |
| pure | 39-124-95 | 1995 | CAPOCARD 50MG TAB | 50 | mg | Tablet | Oral use | Prescription | Generic | Salehiya Trading Co. | 25.4 | C09AA01 |
| pure | 90-212-98 | 1998 | CAPRIL 25MG TAB | 25 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 18.65 | C09AA01 |
| pure | 91-212-98 | 1998 | CAPRIL 50MG TAB | 50 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 31.55 | C09AA01 |
| pure | 1806257574 | 2019 | NOYADA 25MG/5ML ORAL SOLUTION | 5 | None | Oral solution | Oral use | Prescription | NCE | Faisal Musaed El Seif Saudi Pharmaceutical Co. | 165 | C09AA01 |
| pure | 1806257573 | 2019 | NOYADA 5MG/5ML ORAL SOLUTION | 1 | None | Oral solution | Oral use | Prescription | NCE | Faisal Musaed El Seif Saudi Pharmaceutical Co. | 140.4 | C09AA01 |

## losartan — 12 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2109234235 | 2014 | AZAR 100 mg film-coated tablet | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | ARAC HEALTHCARE | 47.50 | C09CA01 |
| pure | 2109234234 | 2014 | AZAR 50 mg film-coated tablet | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | ARAC HEALTHCARE | 40.80 | C09CA01 |
| pure | 0302210491 | 1997 | COZAAR | 50 | None | Film-coated tablet | Oral use | Prescription | NCE | ALNAGHI COMPANY | 45.35 | C09CA01 |
| pure | 0609211012 | 2003 | COZAAR 100 mg film-coated tablet | 100 | None | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 52.80 | C09CA01 |
| pure | 1012246387 | 2007 | LACINE 50MG F.C. TABLETS | 50 | None | Film-coated tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 42.2 | C09CA01 |
| pure | 2512223039 | 2022 | Osart | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | Elixir Pharmaceutical Company LLC | 40.80 | C09CA01 |
| pure | 2512223040 | 2022 | Osart | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | Elixir Pharmaceutical Company LLC | 47.50 | C09CA01 |
| pure | 2805257483 | 2014 | SARTAN 100 mg Film coated Tablets | 100 | None | Film-coated tablet | Oral use | Prescription | Generic | MANAYER NAJD TRADING MEDICAL NEEDS CO. | 47.50 | C09CA01 |
| pure | 2905257496 | 2014 | SARTAN 50 mg Film coated Tablets | 50 | None | Film-coated tablet | Oral use | Prescription | Generic | MANAYER NAJD TRADING MEDICAL NEEDS CO. | 40.80 | C09CA01 |
| pure | 203-212-04 | 2004 | SORTIVA 50 MG FILM COATED TABLETS | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 45.35 | C09CA01 |
| pure | 215-212-07 | 2007 | SORTIVA FORTE 100MG F.C. TABLETS | 100 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 52.80 | C09CA01 |
| pure | 2705245352 | 2014 | STRAVIS 50MG FILM COATED TABLETS | 50 | mg | Film-coated tablet | Oral use | Prescription | Generic | RIYADH PHARMA | 40.80 | C09CA01 |

## methyldopa — 1 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 23-91-86 | 1986 | SEMBRINA TABLETS 250 MG. | 250 | mg | Tablet | Oral use | Prescription | Generic | Saudi Import Company - BANAJA | 22.85 | C02AB01 |

## enalapril — 6 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 166-212-02 | 2002 | ENAPRIL 10 MG TAB | 10 | mg | Tablet | Oral use | Prescription | Generic | SPIMACO | 44.4 | C09AA02 |
| pure | 1202256892 | 2007 | KORANDIL | 20 | None | Tablet | Oral use | Prescription | Generic | International Teriaqi for medicines ESt | 14.75 | C09AA02 |
| pure | 15-346-05 | 2005 | LAPRIL 10 mg tablet | 10 | mg | Tablet | Oral use | Prescription | Generic | United Pharmaceutical Establishment | 20.2 | C09AA02 |
| pure | 16-346-05 | 2005 | LAPRIL 20 MG TABLET | 20 | mg | Tablet | Oral use | Prescription | Generic | United Pharmaceutical Establishment | 33.15 | C09AA02 |
| pure | 32-346-10 | 2010 | LAPRIL 20MG TABLETS | 20 | mg | Tablet | Oral use | Prescription | Generic | United Pharmaceutical Establishment | 39.8 | C09AA02 |
| pure | 14-346-05 | 2005 | LAPRIL 5 mg tablet | 5 | mg | Tablet | Oral use | Prescription | Generic | United Pharmaceutical Establishment | 12.35 | C09AA02 |

## furosemide — 14 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2806222277 | 1996 | DIUSEMIDE 20MG-2ML AMP | 10 | None | Solution for injection | Intravenous use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 17.70 | C03CA01 |
| pure | 10-119-82 | 1982 | DIUSEMIDE 40 MG TAB | 40 | mg | Tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 7 | C03CA01 |
| pure | 2101244770 | 2024 | DROLINA | 20 | mg | Tablet | Oral use | Prescription | Generic | Alpha Pharma Industry | 30.00 | C03CA01 |
| pure | 2101244771 | 2024 | DROLINA | 40 | mg | Tablet | Oral use | Prescription | Generic | Alpha Pharma Industry | 60.00 | C03CA01 |
| pure | 2703233422 | 2023 | DROLINA | 1 | mg/ml | Oral solution | Oral use | Prescription | Generic | Alpha Pharma Industry | 19.40 | QC03CA01 |
| pure | 2407233926 | 2023 | Furosemide PSI 250 mg per 25 ml | 10 | mg/ml | Solution for injection/infusion | Intramuscular and intravenous use | Prescription | Generic | Pharmaceutical Solution Industries (PSI) | 18.20 | C03CA01 |
| pure | 0804257208 | 2004 | FUSIX 40MG TABLET | 40 | None | Tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 18 | C03CA01 |
| pure | 2111246318 | 2016 | LASIX AMP 20MG-2ML | 10 | None | Solution for injection | Intravenous use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 20.80 | C03CA01 |
| pure | 1708222505 | 1980 | LASIX TAB 40 MG | 40 | mg | Tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 20.2 | C03CA01 |
| pure | 3-152-87 | 1987 | OEDEMAX | 40 | mg | Tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 5.85 | C03CA01 |
| pure | 4-152-87 | 1987 | OEDEMAX | 40 | mg | Tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 28.4 | C03CA01 |
| pure | 1807222309 | 2008 | SALURIN 20MG-2ML AMPOULES | 10 | mg/ml | Solution for injection | Intravenous use | Prescription | Generic | Cigalah Group | 9.65 | C03CA01 |
| pure | 205-186-03 | 2003 | SALURIN 40 MG TABLETS | 40 | mg | Tablet | Oral use | Prescription | Generic | Cigalah Group | 14.15 | C03CA01 |
| pure | 183-186-02 | 2002 | SALURIN 5MG-5ML SYRUP | 1 | mg/ml | Syrup | Oral use | Prescription | Generic | Cigalah Group | 15.25 | C03CA01 |

## spironolactone — 4 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1812246449 | 2017 | ALDACTONE TAB | 100 | None | Tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 25.05 | C03DA01 |
| pure | 0105245234 | 1983 | ALDACTONE TAB | 25 | mg | Tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 18 | C03DA01 |
| pure | 82-171-20 | 2021 | NORACTONE | 25 | mg | Tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 207.90 | C03DA01 |
| pure | 0907245514 | 1985 | NORACTONE | 25 | mg | Tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 9.05 | C03DA01 |

## epinephrine — 16 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1304210679 | 2021 | Adijet | 1 | mg/ml | Solution for injection | Intramuscular and intravenous use | Prescription | Generic | SAUDI PHARMACEUTICAL INDUSTRIES | 80 | C01CA24 |
| pure | 2908210994 | 2021 | ADRENALINE 0.1mg/mL | 1 | mg/ml | Solution for injection in pre-filled syringe | Intravenous use | Prescription | Generic | Arabian Health Care Co. | 504.50 | C01CA24 |
| pure | 2-5077-19 | 2019 | ADRENALINE 0.1MG/ML INJECTION | 0.1 | mg/ml | Solution for injection | Intrathecal, Intravenous, Intramuscular | Prescription | Generic | Faisal Musaed El Seif Saudi Pharmaceutical Co. | 50.45 | C01CA24 |
| pure | 1-239-86 | 1986 | ADRENALINE 1:1000 INJ | 1 | mg/ml | Solution for injection | Intravenous use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 12.45 | C01CA24 |
| pure | 1810222749 | 2016 | ADRENALINE/EPINEPHRINE INJ 1:1000 INJECTION | 1 | mg/ml | Solution for injection | Intramuscular use | Prescription | Generic | Faisal Musaed El Seif Saudi Pharmaceutical Co. | 19.15 | C01CA24 |
| pure | 2301221625 | 2022 | Aronep | 1 | mg/ml | Solution for injection | Intramuscular use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 80 | C01CA24 |
| pure | 0706222144 | 2015 | DILUTE ADRENALINE (Epinephrine) 1:10,000 solution for injection | 100 | µg/ml | Solution for injection | Parenteral use | Prescription | Generic | Faisal Musaed El Seif Saudi Pharmaceutical Co. | 243.00 | C01CA24 |
| pure | 1810211191 | 1989 | EPINEPHRINE INJ | 100 | µg/ml | Solution for injection | Intravenous use | Prescription | NCE | Pfizer Saudi Trading | 32.60 | C01CA24 |
| pure | 2009222618 | 2022 | EpiPen 150 mcg per 0.3 ml | 150 | µg | Solution for injection | Intramuscular use | Prescription | NCE | Cigalah Group | 363.00 | None |
| pure | 2009222619 | 2022 | EpiPen 300 mcg per 0.3 ml | 300 | µg | Solution for injection | Intramuscular use | Prescription | NCE | Cigalah Group | 363.00 | None |
| pure | 1801221611 | 2022 | JEXT | 300 | µg | Solution for injection | Intramuscular use | Prescription | NCE | ZIMMO TRADING ESTABLISHMENT | 363.00 | C01CA24 |
| pure | 1801221610 | 2022 | JEXT | 150 | µg | Solution for injection | Intramuscular use | Prescription | NCE | ZIMMO TRADING ESTABLISHMENT | 363.00 | C01CA24 |
| mixed | 2207257803 | 2012 | MEDICAINE 2% CARTRIDGE | 20,0.01819 | mg | Solution for injection in cartridge | Dental use | Prescription | NCE | Salehiya Trading Co. | 94.60 | N01BB53 |
| mixed | 0603245028 | 1998 | SCANDICAINE 2% SPECIALE CARTRIDGE | 0.020 ,0.010 | mg/ml | Solution for injection | Dental use | Prescription | NCE | Manarh United Medical | 99.60 | N01BB53 |
| mixed | 2407233922 | 2001 | SEPTANEST N 1-200000 DENTAL CARTRIDGE | 0.005,40 | mg/ml | Solution for injection | Dental use | Prescription | NCE | Abdulrauf Ibrahim Batterjee & Bros. Company | 104.35 | N01BB58 |
| mixed | 2407233923 | 2001 | SEPTANEST SP 1-100000 DENTAL CARTRIDGE | 0.01,40 | mg/ml | Solution for injection | Dental use | Prescription | NCE | Manarh United Medical | 104.35 | N01BB58 |

## norepinephrine — 1 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2802245005 | 2024 | Norepinephrine Kalceks | 1 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | AL JEDAANI STORE | 75.15 | C01CA03 |

## dobutamine — 5 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2111222914 | 2022 | Cardutrex | 12.5 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 157.75 | C01CA07 |
| pure | 1-881-13 | 2013 | DOBUJECT 50MG-ML(250MG-5ML) AMPOULE | 50 | mg/ml | Concentrate for peritoneal dialysis solution | Intravenous use | Prescription | Generic | EBRAHIM M. ALMANA & BROS. CO. | 101.55 | C01CA09 |
| pure | 1506257553 | 1998 | DOBUTAMINE HCL 250MG-20ML VIAL | 12.5 | None | Solution for injection | Intravenous use | Prescription | Generic | Pfizer Saudi Trading | 31.55 | C01CA07 |
| pure | 0911211295 | 2016 | DOBUTAMINE JPI 250 mg/20 ml solution for IV infusion | 12.5 | mg/ml | Solution for infusion | Intravenous use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 31.55 | C01CA07 |
| pure | 1406222191 | 2017 | DOBUTAMINE JPI 250 mg/20 ml solution for IV infusion | 12.5 | mg/ml | Solution for infusion | Intravenous use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 203.1 | C01CA07 |

## milrinone — 2 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 1103210598 | 2021 | Milrinone BOS | 1 | mg/ml | Solution for injection | Intravenous use | Prescription | NCE | Boston Oncology Arabia | 786.5 | C01CE02 |
| pure | 0807257709 | 2025 | RINOMEL | 1 | mg/ml | Solution for injection/infusion | Intravenous use | Prescription | Generic | Alpha Pharma Industry | 747.15 | None |

## vasopressin — 3 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2308222532 | 2022 | Progecta | 20 | IU/ml | Solution for injection | Intrathecal, Intravenous, Intramuscular | Prescription | NCE | Jamjoom Medicine Store | 1489.05 | H01BA01 |
| pure | 2205245337 | 2024 | Vasopressin BOS | 20 | U/ml | Solution for infusion | Intravenous use | Prescription | Generic | Boston Oncology Arabia | 1389.80 | H01BA01 |
| pure | 2808258125 | 2025 | Vatowis | 20 | U/ml | Injection | Intravenous use | Prescription | Generic | AL HOBAIL MEDICAL OFFICE COMPANY LTD. | 2421.20 | None |

## dopamine — 7 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2212211500 | 2016 | DOMINE 40 mg/ml concentrate for solution for infusion | 40 | None | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 113.85 | C01CA04 |
| pure | 7-549-89 | 1989 | DOPAMIN HCL 40MG-ML INJ VIAL | 40 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | NCE | Pfizer Saudi Trading | 33.7 | C01CA04 |
| pure | 9-549-89 | 1989 | DOPAMIN HCL INJ 40MG-ML | 40 | mg/ml | Injection | Intravenous use | Prescription | NCE | Pfizer Saudi Trading | 25.3 | C01CA04 |
| pure | 2007222317 | 2022 | Dopamine Fresenius 200 mg/5 ml | 40 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Jamjoom Medicine Store | 163.40 | C01CA04 |
| mixed | H0000037040 | 2024 | Dopamine Hydrochloride in 5% Dextrose | 800,50 | g/l | Solution for injection/infusion | Intravenous use | Prescription | NCE | Arabian Health Care Co. | 343.55 | None |
| pure | 0309245856 | 2024 | Dopamine Hydrochloride in 5% Dextrose, 1600 mcg/ml | 1600 | µg/ml | Solution for injection/infusion | Intravenous use | Prescription | None | Arabian Health Care Co. | 687.10 | C01CA04 |
| pure | 0509245863 | 2024 | Dopamine Hydrochloride in 5% Dextrose, 3200 mcg/ml | 3200 | µg/ml | Solution for injection/infusion | Intravenous use | Prescription | NCE | Arabian Health Care Co. | 1374.20 | C01CA04 |

## acetylsalicylic acid — 11 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mixed | 2-735-10 | 2010 | ALGESAL BAUME CREAM | 6.54,3.46 | g | Cream | Topical | OTC | Generic | Farouk, Maamoun Tamer & CO | 10.8 | M02AC |
| pure | 0902221712 | 1999 | ASPICARD 81MG TAB | 81 | mg | Enteric-coated tablet | Oral use | OTC | Generic | Tabuk Pharmaceutical Manufacturing Company | 30.00 | N02BA01 |
| pure | 3-404-09 | 2009 | ASPICOT 100 MG E.C. TABLETS | 2 | mg | Enteric-coated tablet | Oral use | OTC | Generic | Abdulrehman Algosaibi G.T.C. | 2 | N02BA01 |
| pure | 2-404-09 | 2009 | ASPICOT 100 MG E.C. TABLETS | 100 | mg | Enteric-coated tablet | Oral use | OTC | Generic | Abdulrehman Algosaibi G.T.C. | 0.7 | N02BA01 |
| pure | 9-949-17 | 2017 | ASPIRIN ADULT TAB 300MG | 300 | mg | Tablet | Oral use | OTC | Generic | Cigalah Group | 3.5 | N02BA01 |
| mixed | 11-949-17 | 2017 | ASPIRIN EFFERVESCENT WITH VITAMIN C | 400,240 | mg | Effervescent tablet | Oral use | OTC | NCE | Cigalah Group | 8.15 | N02BA51 |
| pure | 0902221714 | 2016 | ASPIRIN PROTECT 100MG E.C. TABLETS | 100 | mg | Enteric-coated tablet | Oral use | OTC | NCE | Cigalah Group | 19.05 | N02BA01 |
| pure | 1906257582 | 2014 | AZERA 100 mg enteric-coated tablet | 100 | mg | Enteric-coated tablet | Oral use | OTC | Generic | Cigalah Group | 6.35 | N02BA01 |
| pure | 0706222152 | 2005 | DISPRIN | 81 | mg | Enteric-coated tablet | Oral use | OTC | Generic | RIYADH PHARMA | 25.00 | N02BA01 |
| pure | 1306245423 | 2024 | Jusprin | 81 | mg | Enteric-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 22.50 | N02BA01 |
| pure | 2102221746 | 1999 | JUSPRIN 81MG ENTERIC COATED TABLETS | 81 | mg | Enteric-coated tablet | Oral use | OTC | Generic | Cigalah Group | 7.50 | N02BA01 |

## clopidogrel — 10 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2707200128 | 2015 | CLOGREL 75 mg film-coated tablet | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 118.15 | B01AC04 |
| pure | 0604233503 | 2017 | CLOPACIN 75mg film-coated tablets | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 80.95 | B01AC04 |
| pure | 3006257638 | 2025 | clopidogrel ALH | 75 | mg | Tablet | Oral use | Prescription | Generic | AL HOBAIL MEDICAL OFFICE COMPANY LTD. | 118.15 | None |
| pure | 0811222883 | 2013 | CUPIDO | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 115.55 | B01AC04 |
| pure | 1302233247 | 2023 | Devasc | 75 | mg | Tablet | Oral use | Prescription | Generic | Saudi Amarox | 118.15 | B01AC04 |
| pure | 1901233118 | 2023 | Oneclapz | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | AL-TAIF PHARMACEUTICALS COMPANY (SPECTRO PHARMA) | 118.15 | B01AC04 |
| pure | 1506233808 | 2014 | PALETA 75mg film-coated tablets | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 91.90 | B01AC04 |
| pure | 1411211315 | 2021 | Pedovex | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 173.70 | QB01AC04 |
| pure | 2-5143-21 | 2001 | PLAVIX 75 MG TABLET | 75 | mg | Film-coated tablet | Oral use | Prescription | NCE | Sanofi Arabia Trading Co. Ltd | 230.00 | B01AC04 |
| pure | 3103210659 | 2021 | Ravixa | 75 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 158.00 | B01AC04 |

## ticagrelor — 16 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2405257451 | 2025 | Briglor | 60 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 142.50 | None |
| pure | 2405257449 | 2025 | Briglor | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 167.65 | None |
| pure | 100-15-17 | 2021 | BRILINTA 60 MG FILM COATED TABLET | 60 | mg | Film-coated tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 153.50 | B01AC24 |
| pure | 88-15-13 | 2013 | BRILINTA 90 MG FILM COATED TABLET | 90 | mg | Film-coated tablet | Oral use | Prescription | NCE | SAUDI INTERNATIONAL TRADING COMPANY LTD (SITCO) | 195.60 | B01AC24 |
| pure | 1301256592 | 2025 | Domassel | 60 | mg | Film-coated tablet | Oral use | Prescription | Generic | Pharma Pharmaceutical Industries (PPI) | 131.55 | B01AC24 |
| pure | 0911222894 | 2022 | Domassel | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Pharma Pharmaceutical Industries (PPI) | 167.65 | B01AC24 |
| pure | 2503233417 | 2023 | Lotac | 60 | mg | Film-coated tablet | Oral use | Prescription | Generic | Alrai Pharmaceutical industry Co. (L.L.C) | 153.50 | B01AC24 |
| pure | 2503233416 | 2023 | Lotac | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 167.65 | B01AC24 |
| pure | 2003221857 | 2022 | Platica | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 182.55 | QB01AC24 |
| pure | 2803233436 | 2023 | Prasido | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | ZIMMO TRADING ESTABLISHMENT | 156.50 | B01AC24 |
| pure | 2307257810 | 2025 | Survilor | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Apex Pharma | 156.40 | None |
| pure | 2804257292 | 2025 | Tagbro | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 167.65 | None |
| pure | 1505257387 | 2025 | Ticaglob | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 77.15 | None |
| pure | 0902256853 | 2025 | Ticagrelor | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | AJA PHARMACEUTICAL INDUSTRIES | 83.80 | B01AC24 |
| pure | 2205233681 | 2023 | Ticagrelor SPC F.C. Tablets | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | SUDAIR PHARMA COMPANY | 83.80 | B01AC24 |
| pure | 1408258029 | 2025 | Torrenta | 90 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 167.60 | None |

## tirofiban — 3 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 2208234024 | 2010 | AGGRASTAT 0.25MG/ML I.V. VIAL | 0.25 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Salehiya Trading Co. | 980.15 | B01AC17 |
| pure | 0308222393 | 2017 | AGRIPLAT 12.5 MG SOLUTION FOR INFUSION | 0.25 | mg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 796.4 | B01AC17 |
| pure | 1804245173 | 2024 | Fibrosta | 250 | µg/ml | Concentrate for solution for infusion | Intravenous use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 753.20 | B01AC17 |

## alteplase — 1 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 3007245698 | 1989 | ACTILYSE SET(2VLS+2SOLV&INFSET) | 50 | mg | Powder and solvent for solution for injection | Intravenous use | Prescription | Biological | Cigalah Group | 5336.10 | B01AD02 |

## atorvastatin — 54 product(s)

| Match | Reg. no. | Year | Trade name | Strength | Unit | Form | Route | Class | Type | Agent | Price (SAR) | ATC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure | 0912211439 | 2007 | ASTATIN 10MG F.C TABLETS | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 43.45 | C10AA05 |
| pure | 0912211440 | 2007 | ASTATIN 20MG F.C TABLETS | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 43.45 | C10AA05 |
| pure | 1111211302 | 2007 | ASTATIN 40MG F.C TABLETS | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | JAMJOOM PHARMACEUTICALS CO. LTD. | 86.90 | C10AA05 |
| mixed | 0110245998 | 2024 | Atomibe | 40,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 126.10 | C10BA05 |
| mixed | 0110245997 | 2024 | Atomibe | 20,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 120.60 | C10BA05 |
| mixed | 0110245996 | 2024 | Atomibe | 10,10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Saudi Amarox | 116.25 | C10BA05 |
| pure | 37-444-15 | 2015 | ATORLIP 10 mg film-coated tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | MANAYER NAJD TRADING MEDICAL NEEDS CO. | 43.45 | C10AA05 |
| pure | 38-444-15 | 2015 | ATORLIP 20 mg film-coated tablet | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | MANAYER NAJD TRADING MEDICAL NEEDS CO. | 43.45 | C10AA05 |
| pure | 39-444-15 | 2015 | ATORLIP 40 mg film-coated tablet | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | MANAYER NAJD TRADING MEDICAL NEEDS CO. | 86.90 | C10AA05 |
| pure | 2208245807 | 2024 | Atorva | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 172.60 | C10AA05 |
| pure | 2208245805 | 2024 | Atorva | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 304.80 | C10AA05 |
| pure | 2208245804 | 2024 | Atorva | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 172.60 | C10AA05 |
| pure | 361-334-22 | 2022 | ATORVA 10MG F.C. TABLETS | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 724.00 | C10AA05 |
| pure | 0807245492 | 2007 | ATORVA 10MG F.C. TABLETS | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 43.45 | C10AA05 |
| pure | 362-334-22 | 2022 | ATORVA 20MG F.C. TABLETS | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 724.00 | C10AA05 |
| pure | 0807245491 | 2007 | ATORVA 20MG F.C. TABLETS | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 43.45 | C10AA05 |
| pure | 363-334-22 | 2022 | ATORVA 40MG F.C. TABLETS | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 1448.00 | C10AA05 |
| pure | 0807245497 | 2007 | ATORVA 40MG F.C. TABLETS | 40 | None | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 86.90 | C10AA05 |
| pure | 364-334-22 | 2022 | ATORVA 80MG F.C. TABLETS | 80 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 1448.00 | C10AA05 |
| pure | 0807245496 | 2007 | ATORVA 80MG F.C. TABLETS | 80 | mg | Film-coated tablet | Oral use | Prescription | Generic | Jazeera Pharmaceutical Industries (JPI) | 86.90 | C10AA05 |
| mixed | 22-262-10 | 2016 | ATOZET 10/10 mg film-coated tablet | 10,10 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 124.55 | C10BA05 |
| mixed | 22-262-11 | 2016 | ATOZET 10/20 mg film-coated tablet | 10,20 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 129.20 | C10BA05 |
| mixed | 22-262-12 | 2016 | ATOZET 10/40 mg film-coated tablet | 10,40 | mg | Film-coated tablet | Oral use | Prescription | NCE | Farouk, Maamoun Tamer & CO | 135.10 | C10BA05 |
| pure | 2012234600 | 2023 | Aztolyp | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 43.45 | QC10AA05 |
| pure | 2012234602 | 2023 | Aztolyp | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 43.45 | QC10AA05 |
| pure | 2012234603 | 2023 | Aztolyp | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 86.90 | QC10AA05 |
| pure | 2405233718 | 2014 | LD-NOR 10 mg film-coated tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | ARAC HEALTHCARE | 43.45 | C10AA05 |
| pure | 2405233717 | 2014 | LD-NOR 20 mg film-coated tablet | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | ARAC HEALTHCARE | 43.45 | C10AA05 |
| pure | 2405233716 | 2014 | LD-NOR 40 mg film-coated tablet | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | ARAC HEALTHCARE | 86.90 | C10AA05 |
| pure | 1-968-15 | 2015 | LIPICURE 10 mg film-coated tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | DAMMAM PHARMA | 43.45 | C10AA05 |
| pure | 2-968-15 | 2015 | LIPICURE 20 mg film-coated tablet | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | DAMMAM PHARMA | 43.45 | C10AA05 |
| pure | 3-968-15 | 2015 | LIPICURE 40 mg film-coated tablet | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | DAMMAM PHARMA | 86.90 | C10AA05 |
| pure | 297-186-17 | 2017 | LIPIGARD 10 mg film-coated tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 31.70 | C10AA05 |
| pure | 298-186-17 | 2017 | LIPIGARD 20 mg film-coated tablet | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 31.70 | C10AA05 |
| pure | 299-186-17 | 2017 | LIPIGARD 40 mg film-coated tablet | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 63.35 | C10AA05 |
| pure | 2201256732 | 2007 | LORVAST 10 MG F-C TABLETS | 10 | None | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 43.45 | C10AA05 |
| pure | 2201256728 | 2007 | LORVAST 20 MG F-C TABLETS | 20 | None | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 43.45 | C10AA05 |
| pure | 2201256723 | 2007 | LORVAST 40 MG F-C TABLETS | 40 | None | Film-coated tablet | Oral use | Prescription | Generic | Tabuk Pharmaceutical Manufacturing Company | 86.90 | C10AA05 |
| pure | 2305245343 | 2019 | STORVAS 10MG F.C.TABLET | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 15.35 | C10AA05 |
| pure | 2305245344 | 2019 | STORVAS 20MG F.C.TABLET | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 22.65 | C10AA05 |
| pure | 1306245424 | 2019 | STORVAS 40MG F.C.TABLET | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | Cigalah Group | 30.9 | C10AA05 |
| pure | 55-171-07 | 2007 | TORVACOL 10MG F.C. TABLETS | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 43.45 | C10AA05 |
| pure | 1808195987 | 2007 | TORVACOL 20MG F.C. TABLETS | 20 | None | Film-coated tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 43.45 | C10AA05 |
| pure | 2909245967 | 2007 | TORVACOL 40MG F.C. TABLETS | 40 | None | Film-coated tablet | Oral use | Prescription | Generic | Dallah Health Care Company | 86.9 | C10AA05 |
| pure | 1411211317 | 2007 | TOVAST 10 MG F-C TABLETS | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 43.45 | C10AA05 |
| pure | 1411211318 | 2007 | TOVAST 20 MG F-C TABLETS | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 43.45 | C10AA05 |
| pure | 1411211319 | 2007 | TOVAST 40 MG F-C TABLETS | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | SPIMACO | 86.90 | C10AA05 |
| pure | 0905233605 | 2017 | TULIP 10 mg film-coated tablet | 10 | None | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 15.35 | C10AA05 |
| pure | 0905233604 | 2017 | TULIP 20 mg film-coated tablet | 20 | None | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 22.65 | C10AA05 |
| pure | 0905233607 | 2017 | TULIP 40 mg film-coated tablet | 40 | None | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 31.9 | C10AA05 |
| pure | 0905233608 | 2017 | TULIP 80 mg film-coated tablet | 80 | None | Film-coated tablet | Oral use | Prescription | Generic | Farouk, Maamoun Tamer & CO | 48.7 | C10AA05 |
| pure | 20-170-15 | 2015 | VASTALIP 10 mg film-coated tablet | 10 | mg | Film-coated tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 15.35 | C10AA05 |
| pure | 19-170-15 | 2015 | VASTALIP 20 mg film-coated tablet | 20 | mg | Film-coated tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 22.65 | C10AA05 |
| pure | 18-170-15 | 2015 | VASTALIP 40 mg film-coated tablet | 40 | mg | Film-coated tablet | Oral use | Prescription | Generic | Abdulrehman Algosaibi G.T.C. | 31.9 | C10AA05 |

## Combination products involving catalogue ingredients

| Reg. no. | Trade name | Generic name (as registered) | Catalogue ingredients |
|---|---|---|---|
| 0206222125 | ACTOSMET 15/850 mg tablet | METFORMIN HYDROCHLORIDE,PIOGLITAZONE | metformin, pioglitazone |
| 440-212-20 | AMLOVAN-HCT 10/160/12.5MG F.C.TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 443-212-20 | AMLOVAN-HCT 10/160/25MG F.C.TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2307257833 | AMLOVAN-HCT 10/320/25MG F.C.TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 441-212-20 | AMLOVAN-HCT 5/160//25MG F.C.TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 442-212-20 | AMLOVAN-HCT 5/160/12.5MG F.C.TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0409234113 | ARBAVASC HCT 160/10/12.5 mg Film-coated Tablet | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0409234115 | ARBAVASC HCT 160/10/25 mg Film-coated Tablet | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0409234116 | ARBAVASC HCT 160/5/12.5 mg Film-coated Tablet | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0409234114 | ARBAVASC HCT 160/5/25 mg Film-coated Tablet | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 11-809-14 | AZAR-D 100/25 mg film-coated tablet | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 0105245238 | AZAR-D 50/12.5 mg film-coated tablet | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 2812234638 | Acloran Plus | CANDESARTAN CILEXETIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2812234637 | Acloran Plus | CANDESARTAN CILEXETIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2108234008 | Amlohope Plus | RAMIPRIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2108234011 | Amlohope Plus | RAMIPRIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2108234013 | Amlohope Plus | RAMIPRIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 6-5825-23 | CADUET 10-10 | ATORVASTATIN CALCIUM,AMLODIPINE BESILATE | amlodipine, atorvastatin |
| 7-5825-23 | CADUET 10-20 | ATORVASTATIN CALCIUM,AMLODIPINE BESILATE | amlodipine, atorvastatin |
| 8-5825-23 | CADUET 10-40 | ATORVASTATIN CALCIUM,AMLODIPINE BESILATE | amlodipine, atorvastatin |
| 3-5825-23 | CADUET 5-10 | ATORVASTATIN CALCIUM,AMLODIPINE BESILATE | amlodipine, atorvastatin |
| 4-5825-23 | CADUET 5-20 | ATORVASTATIN CALCIUM,AMLODIPINE BESILATE | amlodipine, atorvastatin |
| 5-5825-23 | CADUET 5-40 | ATORVASTATIN CALCIUM,AMLODIPINE BESILATE | amlodipine, atorvastatin |
| 0609211013 | CO-RENITEC | ENALAPRIL MALEATE,HYDROCHLOROTHIAZIDE | enalapril, hydrochlorothiazide |
| 1205257376 | Closa | CLOPIDOGREL,ACETYLSALICYLIC ACID | acetylsalicylic acid, clopidogrel |
| 2010222767 | EXFORGE HCT 10MG/160MG/12.5MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2010222770 | EXFORGE HCT 10MG/160MG/25MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2010222766 | EXFORGE HCT 10MG/320MG/25MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2010222768 | EXFORGE HCT 5MG/160MG/12.5MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2010222769 | EXFORGE HCT 5MG/160MG/25MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2805257482 | Empamac Met | EMPAGLIFLOZIN,METFORMIN HYDROCHLORIDE | empagliflozin, metformin |
| 2001210439 | Erastapecs Trio | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2001210437 | Erastapecs Trio | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2001210438 | Erastapecs Trio | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 3003221896 | FORTZAAR 100/25 mg film-coated tablet | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 1802256911 | GLACERA PLUS 15MG/500MG F.C.TABLET | METFORMIN HYDROCHLORIDE,PIOGLITAZONE | metformin, pioglitazone |
| 1802256910 | GLACERA PLUS 15MG/850MG F.C.TABLET | METFORMIN HYDROCHLORIDE,PIOGLITAZONE | metformin, pioglitazone |
| 1501256659 | GLADOS MET 15/500 TABLETS | METFORMIN HYDROCHLORIDE,PIOGLITAZONE | metformin, pioglitazone |
| 1501256640 | GLADOS MET 15/850 TABLETS | METFORMIN HYDROCHLORIDE,PIOGLITAZONE | metformin, pioglitazone |
| 2307257840 | GLIPTAMET | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 2307257835 | GLIPTAMET | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 1506257555 | Glycimille | METFORMIN HYDROCHLORIDE , SITAGLIPTIN | metformin, sitagliptin |
| 1802256913 | HYZAAR 50/12.5 mg film-coated tablet | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 2501210468 | JANUMET | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 2501210469 | JANUMET | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 3-5061-18 | JANUMET XR | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 2-5061-18 | JANUMET XR | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 1-5061-18 | JANUMET XR | METFORMIN HYDROCHLORIDE,SITAGLIPTIN PHOSPHATE | metformin, sitagliptin |
| 40-972-19 | LISONORM 10 - 5 | LISINOPRIL,AMLODIPINE BESILATE | amlodipine, lisinopril |
| 41-972-19 | LISONORM 20 -10 | LISINOPRIL,AMLODIPINE BESILATE | amlodipine, lisinopril |
| 2011246302 | LOTEVAN PLUS 10MG/160MG/25MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2011246294 | LOTEVAN PLUS 10MG/320MG/25MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2011246298 | LOTEVAN PLUS 5MG/160MG/12.5MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2011246296 | LOTEVAN PLUS 5MG/160MG/25MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2011246301 | LOTEVAN PLUS10MG/160MG/12.5MG FILM COATED TABLET | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0205200066 | MILORA HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0205200067 | MILORA HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0205200068 | MILORA HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0205200069 | MILORA HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2-343-09 | OCTACAINE 100 CARTRIDGE | LIDOCAINE HYDROCHLORIDE,EPINEPHRINE | epinephrine, lidocaine |
| 2005257437 | Olmexa Plus | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2005257436 | Olmexa Plus | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2005257432 | Olmexa Plus | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2005257426 | Olmexa Plus | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2005257427 | Olmexa Plus | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 0707257705 | Olmidip HCT | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 0707257704 | Olmidip HCT | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 0707257703 | Olmidip HCT | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 0707257702 | Olmidip HCT | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 0707257706 | Olmidip HCT | OLMESARTAN MEDOXOMIL,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 66-5286-20 | SENERGY PLUS (10/160/12.5)MG F.C TABLETS | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 67-5286-20 | SENERGY PLUS (10/160/25)MG F.C TABLETS | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 64-5286-20 | SENERGY PLUS (5/160/12.5)MG F.C TABLETS | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 65-5286-20 | SENERGY PLUS (5/160/25)MG F.C TABLETS | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 1701233106 | SEVIKAR HCT 20/5/12.5MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 1701233107 | SEVIKAR HCT 40/10/12.5MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 1701233105 | SEVIKAR HCT 40/10/25MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 1701233104 | SEVIKAR HCT 40/5/12.5MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 1701233108 | SEVIKAR HCT 40/5/25MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0802244884 | SEVITENSE PLUS 20/5/12.5 MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0802244885 | SEVITENSE PLUS 40/10/12.5 MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0802244883 | SEVITENSE PLUS 40/10/25 MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0802244886 | SEVITENSE PLUS 40/5/12.5 MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0802244887 | SEVITENSE PLUS 40/5/25 MG FILM COATED TABLET | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 214-212-07 | SORTIVA H 100-25MG F.C. TABLETS | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 215-212-15 | SORTIVA H 100/12.5 mg film-coated tablet | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 213-212-07 | SORTIVA H 50-12.5MG F.C. TABLETS | LOSARTAN POTASSIUM,HYDROCHLOROTHIAZIDE | hydrochlorothiazide, losartan |
| 2903233445 | SYNJARDY 12.5/1000 mg Film-coated Tablet | METFORMIN HYDROCHLORIDE,EMPAGLIFLOZIN | empagliflozin, metformin |
| 2903233443 | SYNJARDY 12.5/850 mg Film-coated Tablet | METFORMIN HYDROCHLORIDE,EMPAGLIFLOZIN | empagliflozin, metformin |
| 2903233444 | SYNJARDY 5/1000 mg Film-coated Tablet | METFORMIN HYDROCHLORIDE,EMPAGLIFLOZIN | empagliflozin, metformin |
| 2903233442 | SYNJARDY 5/850 mg Film-coated Tablet | METFORMIN HYDROCHLORIDE,EMPAGLIFLOZIN | empagliflozin, metformin |
| 0810246015 | Sitavic | SITAGLIPTIN PHOSPHATE,METFORMIN HYDROCHLORIDE | metformin, sitagliptin |
| 0810246016 | Sitavic | SITAGLIPTIN PHOSPHATE,METFORMIN HYDROCHLORIDE | metformin, sitagliptin |
| 1003257023 | Sitfort | SITAGLIPTIN PHOSPHATE,METFORMIN HYDROCHLORIDE | metformin, sitagliptin |
| 1003257024 | Sitfort | SITAGLIPTIN PHOSPHATE,METFORMIN HYDROCHLORIDE | metformin, sitagliptin |
| 0911211291 | Trioltan | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 0911211290 | Trioltan | OLMESARTAN MEDOXOMIL,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2004210688 | Vittoria-HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2004210687 | Vittoria-HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2004210689 | Vittoria-HCT | VALSARTAN,HYDROCHLOROTHIAZIDE,AMLODIPINE BESILATE | amlodipine, hydrochlorothiazide |
| 2004257243 | Volcardy Plus | VALSARTAN,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2004257240 | Volcardy Plus | VALSARTAN,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2004257239 | Volcardy Plus | VALSARTAN,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 2004257241 | Volcardy Plus | VALSARTAN,AMLODIPINE BESILATE,HYDROCHLOROTHIAZIDE | amlodipine, hydrochlorothiazide |
| 0303256972 | XYLOCAINE DENTAL ADRENALINE SOLU FOR INJ | LIDOCAINE HYDROCHLORIDE,EPINEPHRINE | epinephrine, lidocaine |