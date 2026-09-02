# Vitals by condition

Which measurements the **Vitals** section asks for, given the Patient's conditions
(§4.2). Home Readings are a different series with a different observer and are never
merged into these (`CONTEXT.md`).

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

# conditions = [] means every Patient, every Visit.
# baseline_only = true means the Baseline Visit asks and a Routine Visit does not.
[measurements]
rows = [
  { id = "bp-seated", label = "Blood pressure, seated", unit = "mmHg", conditions = [] },
  { id = "pulse", label = "Pulse", unit = "bpm", conditions = [] },
  { id = "weight", label = "Weight", unit = "kg", conditions = [] },
  { id = "bp-standing", label = "Blood pressure, standing", unit = "mmHg", conditions = ["hypertension"] },
  { id = "bp-other-arm", label = "Blood pressure, other arm", unit = "mmHg", conditions = ["hypertension"], baseline_only = true },
  { id = "capillary-glucose", label = "Capillary blood glucose", unit = "mmol/L", conditions = ["diabetes"] },
  { id = "height", label = "Height", unit = "cm", conditions = [], baseline_only = true },
]
```
