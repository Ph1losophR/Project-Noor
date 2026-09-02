# Drug list

The searchable product list **Medication Reconciliation** selects from (§4.2).
Products are chosen from this list rather than typed — and a product the list does
not contain is still recorded, marked unmatched, and never silently dropped. The
unmatched rate is a metric with authority over this file, exactly as the *Other* rate
is over the reason lists (§5.10).

Starter list, unsourced. It covers the two conditions Noor reasons about and nothing
else; a real household holds products this file has never heard of, which is why
*unmatched* is a first-class state rather than an error. The named owner replaces
this table; nothing here is a clinical recommendation.

## The data

```toml
[meta]
version = "0.1"
dated = "2026-08-28"
source = "Starter list chosen to make Phase 1 runnable. Unsourced"
owner = "Unassigned"
review_date = "Unset"

[products]
rows = [
  { id = "metformin-500", generic = "Metformin", strength = "500 mg", form = "tablet", drug_class = "biguanide" },
  { id = "metformin-1000", generic = "Metformin", strength = "1000 mg", form = "tablet", drug_class = "biguanide" },
  { id = "metformin-xr-750", generic = "Metformin XR", strength = "750 mg", form = "tablet", drug_class = "biguanide" },
  { id = "gliclazide-80", generic = "Gliclazide", strength = "80 mg", form = "tablet", drug_class = "sulfonylurea" },
  { id = "gliclazide-mr-60", generic = "Gliclazide MR", strength = "60 mg", form = "tablet", drug_class = "sulfonylurea" },
  { id = "glimepiride-2", generic = "Glimepiride", strength = "2 mg", form = "tablet", drug_class = "sulfonylurea" },
  { id = "glimepiride-4", generic = "Glimepiride", strength = "4 mg", form = "tablet", drug_class = "sulfonylurea" },
  { id = "sitagliptin-100", generic = "Sitagliptin", strength = "100 mg", form = "tablet", drug_class = "dpp4-inhibitor" },
  { id = "empagliflozin-10", generic = "Empagliflozin", strength = "10 mg", form = "tablet", drug_class = "sglt2-inhibitor" },
  { id = "empagliflozin-25", generic = "Empagliflozin", strength = "25 mg", form = "tablet", drug_class = "sglt2-inhibitor" },
  { id = "pioglitazone-30", generic = "Pioglitazone", strength = "30 mg", form = "tablet", drug_class = "thiazolidinedione" },
  { id = "insulin-glargine-100", generic = "Insulin glargine", strength = "100 U/mL", form = "pen", drug_class = "basal-insulin" },
  { id = "insulin-nph-100", generic = "Insulin isophane (NPH)", strength = "100 U/mL", form = "vial", drug_class = "basal-insulin" },
  { id = "insulin-aspart-100", generic = "Insulin aspart", strength = "100 U/mL", form = "pen", drug_class = "bolus-insulin" },
  { id = "insulin-mix-70-30", generic = "Insulin 70/30 premixed", strength = "100 U/mL", form = "pen", drug_class = "premixed-insulin" },
  { id = "amlodipine-5", generic = "Amlodipine", strength = "5 mg", form = "tablet", drug_class = "calcium-channel-blocker" },
  { id = "amlodipine-10", generic = "Amlodipine", strength = "10 mg", form = "tablet", drug_class = "calcium-channel-blocker" },
  { id = "lisinopril-10", generic = "Lisinopril", strength = "10 mg", form = "tablet", drug_class = "ace-inhibitor" },
  { id = "lisinopril-20", generic = "Lisinopril", strength = "20 mg", form = "tablet", drug_class = "ace-inhibitor" },
  { id = "enalapril-10", generic = "Enalapril", strength = "10 mg", form = "tablet", drug_class = "ace-inhibitor" },
  { id = "losartan-50", generic = "Losartan", strength = "50 mg", form = "tablet", drug_class = "arb" },
  { id = "losartan-100", generic = "Losartan", strength = "100 mg", form = "tablet", drug_class = "arb" },
  { id = "valsartan-80", generic = "Valsartan", strength = "80 mg", form = "tablet", drug_class = "arb" },
  { id = "valsartan-160", generic = "Valsartan", strength = "160 mg", form = "tablet", drug_class = "arb" },
  { id = "hydrochlorothiazide-25", generic = "Hydrochlorothiazide", strength = "25 mg", form = "tablet", drug_class = "thiazide" },
  { id = "indapamide-1-5", generic = "Indapamide", strength = "1.5 mg", form = "tablet", drug_class = "thiazide-like" },
  { id = "bisoprolol-5", generic = "Bisoprolol", strength = "5 mg", form = "tablet", drug_class = "beta-blocker" },
  { id = "atenolol-50", generic = "Atenolol", strength = "50 mg", form = "tablet", drug_class = "beta-blocker" },
  { id = "carvedilol-12-5", generic = "Carvedilol", strength = "12.5 mg", form = "tablet", drug_class = "beta-blocker" },
  { id = "spironolactone-25", generic = "Spironolactone", strength = "25 mg", form = "tablet", drug_class = "aldosterone-antagonist" },
  { id = "furosemide-40", generic = "Furosemide", strength = "40 mg", form = "tablet", drug_class = "loop-diuretic" },
  { id = "atorvastatin-20", generic = "Atorvastatin", strength = "20 mg", form = "tablet", drug_class = "statin" },
  { id = "atorvastatin-40", generic = "Atorvastatin", strength = "40 mg", form = "tablet", drug_class = "statin" },
  { id = "rosuvastatin-10", generic = "Rosuvastatin", strength = "10 mg", form = "tablet", drug_class = "statin" },
  { id = "aspirin-81", generic = "Aspirin", strength = "81 mg", form = "tablet", drug_class = "antiplatelet" },
]
```
