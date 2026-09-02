# A Self-Care Check failure suppresses the Recommendation it undermines

When the Self-Care Check finds that a treatment is not reaching the Patient as prescribed — insulin stored above range, lipohypertrophy at every injection site, a sulfonylurea taken before a meal that is then skipped, a BP cuff two sizes too small — Noor withholds the titration Recommendation that the corrupted signal would otherwise justify, and issues the correction instead. It does not show both and let the Field Team choose, and it does not rank them. It suppresses one, and records that it did.

The reason is that delegated titration is the mechanism of effect in every trial that moved an outcome (TASMIN-SR, HyperLink, and the co-intervention principle throughout `docs/research/art_of_chronic_disease_management.md`) — and titration against a signal corrupted by the home environment is not a weaker version of that mechanism, it is a harm generator. Degraded insulin reads as treatment failure; escalating the dose either continues the hyperglycaemia toward a metabolic-crisis admission or calibrates the Patient to a dead drug and produces hypoglycaemia when properly stored insulin arrives. Both terminal branches are admissions, and neither has anything to do with the prescription being wrong. A monitoring-and-titration system without this rule escalates faster and more confidently against a false signal than an unaided clinician would.

**Suppression is never silent.** The suppressed Recommendation, and the Self-Care Finding that suppressed it, are both visible to the Supervisor and both written back to the EMR as structured data. N6 exists because a quiet engine and a broken engine are indistinguishable; a suppression Noor declines to declare would be exactly the failure mode the constraint forbids.

## Considered Options

- **Show both Recommendations and let the Field Team decide.** Rejected: it presents a dose increase and the reason that dose increase is wrong as peer options, to a Junior Physician whose defining limitation is experience rather than authority. This is the junior-staff trap in `docs/research/why_cds_engines_fail.md` — automation bias RR 1.26, with task inexperience raising the risk — and the dose change is the more familiar-looking action of the two.
- **Show the titration with a warning attached.** Rejected: a warning is an assessment, which fails N2, and it survives dismissal. The pairing degrades into a pop-up the team learns to click past, and then the dose increase is what remains on screen.
- **Rank them, titration second.** Rejected: ranking still asserts that both are valid actions today. One of them is not an action, it is an error.

## Consequences

Every rule that can produce a titration Recommendation must declare which Self-Care Findings undermine it. This is a precedence relationship between rules rather than a property of a single rule, and it is the first structure in the engine that is not evaluable in isolation — a rule's own test can no longer prove its behaviour alone.

Suppression must therefore be tested in both directions. Per `CLAUDE.md`, a new rule is a new table-driven test row; a suppression relationship needs a row proving the titration fires when the Self-Care Check is clean, and a row proving it does not fire, *and is recorded as suppressed*, when it is not. Asserting only the non-firing case would pass against an engine that had simply stopped working.

Suppression runs before the N3 cap is applied. A suppressed Recommendation never competes for a display slot, and the correction that replaced it competes in its place.
