# Structured reason lists

Clinical content. Construction and rules: `project_noor_architecture.md` §5.10.

| N8 field | Value |
|---|---|
| Version | 0.1 |
| Dated | 2026-08-28 |
| Source | Clinical judgement, drafted in the §5.10 grilling session |
| Owner | **Unassigned.** N8 requires a named owner before Phase 1 ships. Declared, not hidden (N6) |
| Review date | **Unset.** Set with the owner |

Every list ends in **Other + free text**, and the rate of *Other* per list is a metric with the authority to change that list.

**`Other +` is shown by the code on every list and is not one of the rows below.** It is not clinical content: §5.10 makes it structural — every one of the four contexts has it, an owner cannot remove it, and a list that lost it would force the nearest wrong bucket. So it appears in the prose above and in each list here as the reminder that it exists, while the machine-readable rows carry only the choices an owner may actually edit. A loader that finds an `Other` row in this file should treat the file as wrong.

---

## 1. Cancelled — the Visit never started

- Patient not at home
- Patient declined the Visit
- Patient in hospital
- Patient died
- Field Team could not reach the house — access, transport, or safety
- Field Team unavailable or reassigned to an urgent case
- Scheduling error or duplicate
- **Other +**

## 2. Ended Early — started, stopped before the Visit Protocol finished

- Patient withdrew and asked the team to stop
- Patient too unwell to continue
- Patient transferred to hospital following an **Emergency**
- Patient died during the Visit
- Caregiver absent and required for the remainder
- Household circumstance made continuing unsafe
- Field Team called away to an urgent case
- Time exhausted
- **Other +**

Any row here may apply to a Visit that terminates out of an **Emergency**, because the Emergency's exit carries no reason of its own (§5.7) and this list is what covers it. The third and fourth rows are simply the two that an Emergency produces most often.

## 3. A section resolved with no content

**Shared core — all eight sections:**

- Patient declined
- Patient unable to participate
- Caregiver required and absent
- No time remaining in the Visit
- Visit ended before this section
- **Other +**

There is deliberately **no "not applicable to this Patient" row.** The **Visit Protocol** holds that no section may be absent, so nothing in it is optional, and a generic *not applicable* is the row that would swallow every meaningful reason below.

**Plus, per section:**

| Section | Additional rows |
|---|---|
| Visit Reason | *None.* The roster entry carries the reason the Visit was scheduled (§4.9), so in practice this section is never empty |
| Concerns & Interval History | Patient cannot communicate and no Caregiver present |
| Medication Reconciliation | No medication in the house at all · Caregiver could not locate the medication |
| Vitals | No working device in the household · No cuff of an appropriate size |
| Physical Examination | Bed-bound and could not be positioned · Declined to remove footwear · Declined examination by this Field Team — no chaperone or no same-gender examiner · No private space in the household |
| Self-Care Check | No device in the household to demonstrate on · No medication in the house to demonstrate technique on · Administered entirely by an absent Caregiver |
| Care Plan | *None.* **Completed** requires it, so it is empty only on an **Ended Early**, which the shared core covers |
| Notes | Nothing further to record |

Two rows here are **Findings, not shrugs**, and this is why the list is not flat: *no medication in the house at all* and *no device in the household* are each a clinical result in their own right — the second is the enrolment condition failing. And *declined to remove footwear* is the amputation pathway, which a generic *patient declined* would file as an ordinary skip.

**Not a skip reason:** Medication Reconciliation with the prescribed list **Unreachable** still has content — it records what is in the house and cannot name the discrepancy (§4.10). That is a declaration, not an empty section.

## 4. An overridden Recommendation

Two levels. The first is the one that matters, because it separates *fix the rule* from *fix the supply chain*.

**A — the rule was wrong here**

- Already addressed
- Clinically inappropriate for this Patient
- Contraindicated — comorbidity, interaction, or allergy
- The data it relied on is wrong
- **Other +**

**B — the rule was right; the Field Team could not act**

- Patient declined
- Caregiver declined
- Not executable here — no equipment
- Not executable here — no supply
- Deferred to the Supervisor
- Will address at the next Visit
- **Other +**

An override never blocks anything (N4), and the tier still routes regardless of which level was chosen (§5.11).

## The data

```toml
[meta]
version = "0.1"
dated = "2026-08-28"
source = "Clinical judgement, drafted in the §5.10 grilling session"
owner = "Unassigned"
review_date = "Unset"

[cancelled]
rows = [
  { id = "patient-not-at-home", label = "Patient not at home" },
  { id = "patient-declined", label = "Patient declined the Visit" },
  { id = "patient-in-hospital", label = "Patient in hospital" },
  { id = "patient-died", label = "Patient died" },
  { id = "house-unreachable", label = "Field Team could not reach the house — access, transport, or safety" },
  { id = "field-team-unavailable", label = "Field Team unavailable or reassigned to an urgent case" },
  { id = "scheduling-error", label = "Scheduling error or duplicate" },
]

[ended_early]
rows = [
  { id = "patient-withdrew", label = "Patient withdrew and asked the team to stop" },
  { id = "patient-too-unwell", label = "Patient too unwell to continue" },
  { id = "transferred-to-hospital", label = "Patient transferred to hospital following an Emergency" },
  { id = "patient-died-during-visit", label = "Patient died during the Visit" },
  { id = "caregiver-absent", label = "Caregiver absent and required for the remainder" },
  { id = "household-unsafe", label = "Household circumstance made continuing unsafe" },
  { id = "team-called-away", label = "Field Team called away to an urgent case" },
  { id = "time-exhausted", label = "Time exhausted" },
]

[no_content]
shared = [
  { id = "patient-declined", label = "Patient declined" },
  { id = "patient-unable", label = "Patient unable to participate" },
  { id = "caregiver-required-absent", label = "Caregiver required and absent" },
  { id = "no-time-remaining", label = "No time remaining in the Visit" },
  { id = "visit-ended-first", label = "Visit ended before this section" },
]

# All eight keys are present, and two are deliberately empty rather than absent —
# a missing key would read as "not written yet" (§5.10, N6).
[no_content.per_section]
visit_reason = []
concerns_and_interval_history = [
  { id = "cannot-communicate", label = "Patient cannot communicate and no Caregiver present" },
]
medication_reconciliation = [
  { id = "no-medication-in-house", label = "No medication in the house at all" },
  { id = "could-not-locate", label = "Caregiver could not locate the medication" },
]
vitals = [
  { id = "no-working-device", label = "No working device in the household" },
  { id = "no-appropriate-cuff", label = "No cuff of an appropriate size" },
]
physical_examination = [
  { id = "bed-bound", label = "Bed-bound and could not be positioned" },
  { id = "declined-footwear", label = "Declined to remove footwear" },
  { id = "no-chaperone", label = "Declined examination by this Field Team — no chaperone or no same-gender examiner" },
  { id = "no-private-space", label = "No private space in the household" },
]
self_care_check = [
  { id = "no-device-to-demonstrate", label = "No device in the household to demonstrate on" },
  { id = "no-medication-to-demonstrate", label = "No medication in the house to demonstrate technique on" },
  { id = "absent-caregiver-administers", label = "Administered entirely by an absent Caregiver" },
]
care_plan = []
notes = [
  { id = "nothing-further", label = "Nothing further to record" },
]

[override.rule_wrong_here]
rows = [
  { id = "already-addressed", label = "Already addressed" },
  { id = "clinically-inappropriate", label = "Clinically inappropriate for this Patient" },
  { id = "contraindicated", label = "Contraindicated — comorbidity, interaction, or allergy" },
  { id = "data-is-wrong", label = "The data it relied on is wrong" },
]

[override.could_not_act]
rows = [
  { id = "patient-declined", label = "Patient declined" },
  { id = "caregiver-declined", label = "Caregiver declined" },
  { id = "no-equipment", label = "Not executable here — no equipment" },
  { id = "no-supply", label = "Not executable here — no supply" },
  { id = "deferred-to-supervisor", label = "Deferred to the Supervisor" },
  { id = "next-visit", label = "Will address at the next Visit" },
]
```
