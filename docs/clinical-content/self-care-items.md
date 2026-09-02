# Self-Care Check items

What the **Self-Care Check** observes or asks to be demonstrated (§4.2). Every item
is observed or demonstrated, never asked, and every one is attributed to the person
who actually performs the task — which is frequently the **Caregiver** and not the
**Patient**.

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

# mode = "observed" | "demonstrated". requires = what must be in the house for the
# item to be possible at all — its absence is a Finding, not a skip (§5.10).
[items]
rows = [
  { id = "medication-storage", label = "Where the medication is kept", mode = "observed", conditions = [], requires = "medication" },
  { id = "insulin-storage", label = "Insulin storage — refrigerated, in date, not frozen", mode = "observed", conditions = ["diabetes"], requires = "insulin" },
  { id = "injection-technique", label = "Injection technique, including site rotation", mode = "demonstrated", conditions = ["diabetes"], requires = "insulin" },
  { id = "meter-technique", label = "Glucose meter technique", mode = "demonstrated", conditions = ["diabetes"], requires = "glucose-meter" },
  { id = "cuff-technique", label = "Blood pressure cuff placement and posture", mode = "demonstrated", conditions = ["hypertension"], requires = "bp-monitor" },
  { id = "foot-routine", label = "Daily foot inspection routine", mode = "demonstrated", conditions = ["diabetes"] },
  { id = "sick-day-rules", label = "What to do on a day of vomiting or fever", mode = "demonstrated", conditions = ["diabetes"] },
  { id = "hypo-response", label = "What to do for a low reading, and what is in the house to treat it", mode = "demonstrated", conditions = ["diabetes"], requires = "hypo-treatment" },
]
```
