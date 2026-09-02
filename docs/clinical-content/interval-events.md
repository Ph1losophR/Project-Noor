# Interval events

The fixed tick-list in **Concerns & Interval History** (§4.2). Clinical content, same rules as the reason lists.

| N8 field | Value |
|---|---|
| Version | 0.1 |
| Dated | 2026-08-28 |
| Source | Clinical judgement, drafted in the §4.2 grilling session |
| Owner | **Unassigned.** N8 requires a named owner before Phase 1 ships |
| Review date | **Unset.** Set with the owner |

## Since the last Visit

- Admitted to hospital
- Attended an emergency department
- Seen by another doctor
- Medication started or changed elsewhere
- A fall
- A hypoglycaemic episode
- Ran out of medication
- **None of these**

**"None of these" is a positive answer, not an empty one.** It is the difference between *nothing happened* and *nobody asked* — the same distinction §4.1 draws between Noor finding nothing and Noor being broken. A section left blank is resolved with a reason (§5.10); a section with *none of these* ticked is resolved with content.

**Every row is here because a rule will need it, not because it is interesting.** *Hypoglycaemic episode* is the Finding that blocks a sulfonylurea or insulin increase, and §4.4 records that hypoglycaemia hospitalisations now exceed hyperglycaemia. *Medication started or changed elsewhere* is the interaction Noor would otherwise miss entirely, because it never reached the prescribed list. *Ran out of medication* explains an uncontrolled reading without any change of dose being the answer. A row that no rule will ever read belongs in Notes.

## Concerns

Not a list. Free text, one item per concern, each attributed to the **Patient** or the **Caregiver** who raised it. A closed list would force *"his feet burn at night"* into *pain*, which is the §5.10 failure — data that looks clean and means nothing. Burning feet at night is neuropathy, and *pain* does not say that.

## The data

```toml
[meta]
version = "0.1"
dated = "2026-08-28"
source = "Clinical judgement, drafted in the §4.2 grilling session"
owner = "Unassigned"
review_date = "Unset"

# "None of these" is a row, not the absence of rows — a positive answer (§4.2).
[events]
rows = [
  { id = "admitted-to-hospital", label = "Admitted to hospital" },
  { id = "attended-emergency-department", label = "Attended an emergency department" },
  { id = "seen-by-another-doctor", label = "Seen by another doctor" },
  { id = "medication-changed-elsewhere", label = "Medication started or changed elsewhere" },
  { id = "a-fall", label = "A fall" },
  { id = "hypoglycaemic-episode", label = "A hypoglycaemic episode" },
  { id = "ran-out-of-medication", label = "Ran out of medication" },
  { id = "none-of-these", label = "None of these" },
]
```
