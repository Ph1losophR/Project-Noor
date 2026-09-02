# Physical Examination elements

The element list Noor composes for the **Physical Examination** from the Patient's
conditions and their overdue surveillance (§4.2). The Field Team may add elements;
it does not decide which are required. A **Baseline Visit**'s examination is
complete rather than composed, so it asks for every row in the file.

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

# conditions = [] → every Patient. overdue = "<surveillance id>" → required only
# when that surveillance item is overdue, which is how the two files meet.
[elements]
rows = [
  { id = "general-appearance", label = "General appearance", conditions = [] },
  { id = "peripheral-oedema", label = "Peripheral oedema", conditions = [] },
  { id = "heart-sounds", label = "Heart sounds", conditions = ["hypertension"] },
  { id = "chest-auscultation", label = "Chest auscultation", conditions = ["hypertension"] },
  { id = "foot-inspection", label = "Foot inspection — skin, nails, ulceration, footwear", conditions = ["diabetes"] },
  { id = "pedal-pulses", label = "Pedal pulses", conditions = ["diabetes"] },
  { id = "monofilament", label = "Monofilament sensation, ten sites", conditions = ["diabetes"], overdue = "foot-examination" },
  { id = "injection-sites", label = "Injection sites — lipohypertrophy, bruising", conditions = ["diabetes"] },
  { id = "fundoscopy-referral", label = "Confirm retinal screening arranged", conditions = ["diabetes"], overdue = "retinal-screening" },
]
```
