# Recommendations are routed by time-to-action, not clinical severity

Every recommendation Noor produces carries one ordered Escalation Tier (0–3) answering "by when must someone respond, and who" — Tier 0 Field Team acts alone, Tier 1 Field Team acts with asynchronous Supervisor review, Tier 2 Field Team must reach the Supervisor during the visit before acting, Tier 3 emergency with the Supervisor removed from the critical path. Clinical severity is an *input* to choosing the tier, never the tier itself, because severity and urgency come apart routinely in chronic disease: an HbA1c of 11% is a severe finding with almost no urgency, while a mildly infected diabetic foot ulcer is a mild finding with 48-hour urgency — a single severity scale routes both wrongly.

## Considered Options

- **Clinical severity scale** (mild/moderate/severe/critical, routing derived from it). Rejected: conflates two independent quantities, producing false alarms on severe-but-slow findings and dangerous delays on mild-but-fast ones.
- **Two independent axes** ("can the Field Team act?" × "when must the Supervisor respond?"). Rejected: the 8 combinations collapse to the same 4 meaningful tiers, and the other 4 are incoherent — it reaches the ladder the long way while doubling what every rule, screen, and test must handle.

## Consequences

Tier 3 exists specifically so a genuine emergency does not queue behind a human. Without it, the ladder tops out at "reach the Supervisor," placing a bottleneck in front of time-critical care.

Because the tier is attached to each recommendation rather than to the visit or the patient, one visit can legitimately produce recommendations at several tiers at once. How those combine — and the per-visit cap in N3 — is still open.

*Resolved since: the cap is three, and it is welded into the code rather than configurable (`0007-clinical-content-is-data.md`). Each tier's response window went the other way — service policy, in `docs/clinical-content/response-windows.md`.*
