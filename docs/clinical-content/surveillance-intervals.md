# Surveillance intervals

How long a surveillance item may go without being repeated before Noor calls it
overdue. Read by **Physical Examination** composition (§4.2) and by the Brief.

Starter values, unsourced. The named owner replaces this table; nothing here is a
clinical recommendation.

## The data

```toml
[meta]
version = "0.1"
dated = "2026-08-28"
source = "Starter values chosen to make Phase 1 runnable. Unsourced"
owner = "Unassigned"
review_date = "Unset"

# months = how long the item stays current. Absent from the record → overdue.
[intervals]
rows = [
  { id = "hba1c", label = "HbA1c", months = 3, conditions = ["diabetes"] },
  { id = "foot-examination", label = "Foot examination", months = 12, conditions = ["diabetes"] },
  { id = "retinal-screening", label = "Retinal screening", months = 12, conditions = ["diabetes"] },
  { id = "urine-acr", label = "Urine albumin-to-creatinine ratio", months = 12, conditions = ["diabetes", "hypertension"] },
  { id = "creatinine-egfr", label = "Serum creatinine and eGFR", months = 12, conditions = ["diabetes", "hypertension"] },
  { id = "potassium", label = "Serum potassium", months = 12, conditions = ["hypertension"] },
  { id = "lipid-profile", label = "Lipid profile", months = 12, conditions = ["diabetes", "hypertension"] },
]
```
