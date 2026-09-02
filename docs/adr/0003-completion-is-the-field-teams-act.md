# Completion is the Field Team's act, and the Supervisor does not gate it

A Visit reaches **Completed** when the Field Team closes it in the house, before leaving. Supervisor review attaches to individual items rather than to the Visit, the engine's Escalation Tier is a floor on Supervisor involvement rather than a ceiling, and the accuracy of Noor's silence is measured by sampling quiet Visits rather than asserted. The three belong in one decision because each one fails without the other two.

**The Supervisor does not gate completion**, for three reasons that compound. It would abolish Tier 0 — if every Visit needs the Supervisor before it counts, the ladder in `0001-time-to-action-not-severity.md` has no bottom rung and the bottleneck Tier 0 exists to remove is reinstated for every Visit including the silent ones. It contradicts §4.4: consultant-grade judgement scales here because *one Supervisor decision governs every field decision until the target is revised*, and a per-Visit gate inverts that into one Supervisor decision per Visit. And it cannot survive §4.10 — a state that depends on a remote human is unreachable from a house with no signal, so either the Visit stays open indefinitely or offline-by-default is false.

**Routing is a floor, not a ceiling.** The Junior Physician can send anything to the Supervisor at any time, whatever tier the engine assigned. A tier is a rule's opinion, and N4 already treats a clinician's disagreement with a rule as data about the rule rather than disobedience. Software that could *lower* the Supervisor's involvement below what a licensed clinician judged necessary is a hard stop wearing routing's clothes.

**Silence is audited.** A sampled fraction of Completed Visits that produced no Recommendation goes to the Supervisor precisely because nothing was found. §4.1 makes the accuracy of Noor's silence the property the whole deliverable is judged on, and N8 records that failures-to-*fire* are the malfunction class that existing detection approaches are "inadequate" against. Reviewing only the Visits that spoke measures precision and never once measures recall.

## Considered Options

- **An `Under Review` state between In Progress and Completed, with Completed meaning Supervisor-approved.** Rejected on the three grounds above, and on queue arithmetic: at 4–8 Visits per team per day, mandatory review makes the Supervisor's inbox the rate limit on the whole service. A review that must clear that volume becomes a rubber stamp, which is worse than no review because it launders unexamined work as examined.
- **Let the engine decide which Visits are reviewed** — routing as a ceiling. Rejected: it puts a static rule artifact in charge of its own oversight. N8's amiodarone failure is a rule that stopped firing undetected; an engine that also selects the review population decides, when broken, that there is nothing to review. That is the same failure with the auditor removed.
- **Sample randomly across all Completed Visits** rather than specifically the silent ones. Rejected: a random sample is dominated by Visits that produced Recommendations, which are the cases already visible to the Supervisor through the normal routes. The sample has to be drawn from the population nobody would otherwise look at.

## Consequences

**Completed becomes a clinical claim rather than an administrative one**, made by the people who were in the room. Because nothing downstream checks it, the state must be strict about what it requires — every section *resolved*, in the sense of §5.8 — and that strictness is only tolerable because **Ended Early** exists as an honest exit.

**Supervisor review must be modelled per item, never per Visit.** One Visit can hold three items in three review states at once, which no Visit-level state can represent. "This Visit has items awaiting review" is therefore derived on read and never stored.

**The Silence Audit's sample rate is a governance parameter, not a constant in code** — it carries an owner and a review date like any rule (N8). The audit also needs its own check: an audit that never finds a miss is equally consistent with an accurate engine and a broken audit, and only a deliberately seeded miss distinguishes the two.

Whether a consultant countersignature is legally required on a junior physician's home-visit record in Saudi Arabia is unverified (§6). If it is required, nothing in this decision changes: the obligation lands *after* the close, on the Write-Back axis, and never as a Visit state.
