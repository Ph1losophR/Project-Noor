# Frontend SSOT — Project Noor Design System

## 1. Scope and standing

This document governs **how Noor looks and behaves as a surface**: colour, type,
space, the marks that carry clinical meaning, and how all four are delivered and
enforced. Page composition, routing and navigation are part of the React frontend
(`src/frontend/`), which consumes the JSON API and follows the design tokens here.

`project_noor_architecture.md` remains the single source of truth. Where this
document and the architecture SSOT disagree, **the architecture SSOT wins**, and
the conflict is raised rather than silently resolved.

Every colour value here was measured, not chosen by eye. Contrast is WCAG 2.1
against the surface named. Colourblind separation is OKLab ΔE ×100 under
simulated deuteranopia and tritanopia. Where a number appears, it is
reproducible.

## 2. The design condition

Noor is read on a **768 × 1024 portrait tablet, held at arm's length, in a
patient's home, often in direct sunlight**, by a clinician who may be wearing
gloves and may be sixty years old.

That sentence is the reason for every floor in this document.

| Constraint | Value |
|---|---|
| Authoritative viewport | 768 × 1024, portrait |
| Arrangement | one arrangement at every width; centred with a max width on wider screens, never rearranged |
| Minimum touch target | 48 × 48px; larger for anything that commits a clinical decision |
| Text contrast floor | 4.5:1 — no exception for "decorative" labels |
| Non-text contrast floor | 3:1 for any mark, border or fill that carries meaning |

Noor has **no patient-facing surface**. §5.13 puts the Patient and the Caregiver
outside the software, and this document does not invent a screen for them. But
the screen **will be turned around** — toward a patient, a family member, an
ambulance crew — so nothing on it may be illegible to someone who did not open
it.

## 3. Brand law

Noor should feel **luxurious, calming and confident**. Two laws make that
compatible with a clinical instrument, and they outrank every aesthetic rule
below them.

**The visible-looking law.** Nothing Noor examined is ever invisible. An item
checked and found normal is *rendered*, not omitted. **Absence of a mark is never
how Noor says "fine."** §4.1 makes the silent visit the Golden Case, and a Golden
Case that renders as an empty screen is indistinguishable from a broken one.

**The colour-scarcity law.** Colour scarcity is a safety mechanism, not a mood.
If the interface is loud everywhere, the one place that must shout — a Tier 3
stop, an **Unreachable** input — has nothing left to shout with.

Seven rules follow from the brief:

1. **Space before ornament.** Emptiness is the material. Anything that fills it must earn the room.
2. **Few hues, low saturation, a warm neutral ground.** Nine neutrals per mode and three status hues. That is the whole budget.
3. **Type carries hierarchy, not boxes.** Size, weight and letter-spacing do the work that borders and chips would otherwise do.
4. **One spacing scale, obeyed without exception.** §6.
5. **Depth at exactly one level.** Something is raised or it is not. There is no third plane.
6. **Motion is slow, rare, and nothing bounces.** §10.
7. **Confidence lives in the copy.** Noor states what it found and what it could not. It does not hedge, apologise or exclaim.

Excluded by name, because each is how "luxury" usually goes wrong: gradients as
decoration, gold and metallics, glass blur, more than one accent, shadows on
everything, more than two type families, and any logo beyond
the wordmark. Icons are allowed only under §7.3 — never decoration, never alone. Ambient washes below 8% opacity are not gradients and are
permitted.

**"Addicting" means satisfying, not engaging.** No streaks, no badges, no
progress gamification, no celebration of a completed Visit. The reward is that
the work was easy and the record is right.

## 4. Colour

Colour is declared in **two layers**, and the distinction is load-bearing rather
than stylistic. The **palette layer** names each measured value once and carries a
mode prefix — `--l-` for light, `--d-` for dark — because the two palettes are
independent and several steps share a name across them: the light text floor and
dark mode's second text step are both called *muted* and are not the same colour.
One custom property cannot hold both, so both are declared, and neither is ever
referenced by a rule. The **role layer** — `--text`, `--page`, `--rule`,
`--status-now` — is what every rule and every component surface actually uses. Switching
mode remaps the role layer and touches nothing else, which is what makes §9's
toggle possible in both directions.

The mapping table at the end of §4.2 is the whole of it. A colour that is not in
one of the two palettes does not exist (§4.4), and a rule that reaches past the
role layer to a `--l-` or `--d-` name is a defect.

### 4.1 Light mode

Ground is `--l-linen`. Only three steps may carry text; the rest are fills, rules
and hairlines, and using one of them for text is a defect.

| Token | Hex | vs `#F7F5F2` | May carry |
|---|---|---|---|
| `--l-ink` | `#282825` | 13.59:1 | text, AAA |
| `--l-lede` | `#66625A` | 5.58:1 | text, AA |
| `--l-muted` | `#716E66` | 4.68:1 | text, AA — the floor |
| `--l-pewter` | `#7E7C75` | 3.84:1 | marks and borders only |
| `--l-mushroom` | `#9A9486` | 2.78:1 | fill only |
| `--l-stone` | `#A6A39A` | 2.32:1 | fill only |
| `--l-greige` | `#B9B4AA` | 1.90:1 | fill only |
| `--l-oat` | `#CFC9BF` | 1.51:1 | fill only |
| `--l-sand` | `#DED9CF` | 1.29:1 | fill only |
| `--l-bone` | `#ECE9E3` | 1.11:1 | fill only |
| `--l-surface-raised` | `#FBFAF8` | — | the raised card, above the page |
| `--l-linen` | `#F7F5F2` | — | the page |
| `--l-hairline` | `rgba(40,40,37,.13)` | — | every border, one value |

Eyebrows, field labels and captions use `--l-muted`, **not** `--l-pewter`. At 13px
uppercase in sunlight, 3.84:1 is decoration pretending to be a label.

The primary button is `--l-ink`. **Light mode has no accent hue at all** — colour in
light mode is spent exclusively on status.

### 4.2 Dark mode

Dark mode is its own palette, not an inversion. It lifts with a **lighter surface
step** rather than with shadow, because shadow does not read on near-black.

| Token | Hex | vs `#0D0F0E` | May carry |
|---|---|---|---|
| `--d-paper` | `#D8D4C9` | 12.99:1 | text, AAA |
| `--d-muted` | `#9B968A` | 6.52:1 | text, AA |
| `--d-soft-greige` | `#7A7363` | 4.09:1 | marks and borders only |
| `--d-aged-bronze` | `#5B5342` | 2.53:1 | fill only — the primary button |
| `--d-bronze-label` | `#F1EEE6` | — | the primary button's label, 6.56:1 on it |
| `--d-sage` | `#48594B` | 2.57:1 | fill only |
| `--d-dark-moss` | `#3A4336` | 1.86:1 | fill only |
| `--d-walnut` | `#3B342C` | 1.57:1 | fill only |
| `--d-pine` | `#2C3A33` | 1.61:1 | fill only |
| `--d-forest` | `#1F2B24` | 1.31:1 | fill only — content modules |
| `--d-charcoal` | `#171B1A` | 1.11:1 | the raised card, above the page |
| `--d-deep-onyx` | `#0D0F0E` | — | the page |
| `--d-hairline` | `rgba(216,212,201,.12)` | — | every border, one value |

Eyebrows and footers use `--d-muted`. `--d-soft-greige` at 4.09:1 fails the text
floor and is a border colour.

Dark mode's one accent is `--d-aged-bronze` on the primary button, with a
`--d-bronze-label` `#F1EEE6` label at 6.56:1. It is not gold: chroma 0.029, a
desaturated brown.

**The role layer.** Eighteen roles, remapped per mode and nothing else remapped.
Every rule in the stylesheet and every component surface resolves through this
table; §13's lint is what keeps a hex from bypassing it.

| Role | Light | Dark | What it is |
|---|---|---|---|
| `--page` | `--l-linen` | `--d-deep-onyx` | the ground |
| `--raised` | `--l-surface-raised` | `--d-charcoal` | the one raised level, §6 |
| `--well` | `--l-bone` | `--d-forest` | a recessed content module |
| `--text` | `--l-ink` | `--d-paper` | primary ink |
| `--text-2` | `--l-lede` | `--d-muted` | secondary |
| `--text-3` | `--l-muted` | `--d-muted` | eyebrows, labels, captions |
| `--rule` | `--l-pewter` | `--d-soft-greige` | marks and borders |
| `--hairline` | `--l-hairline` | `--d-hairline` | every border, one value |
| `--fill-strong` | `--l-mushroom` | `--d-sage` | a filled mark |
| `--fill-soft` | `--l-sand` | `--d-walnut` | a filled band |
| `--button` | `--l-ink` | `--d-aged-bronze` | the primary button |
| `--button-label` | `--l-linen` | `--d-bronze-label` | its label |
| `--depth` | `--l-depth` | `--d-depth` | §6's one level: a shadow, or `none` |
| `--status-clear` | `--l-clear` | `--d-clear` | §4.3 |
| `--status-review` | `--review` | `--review` | §4.3, identical in both modes |
| `--status-now` | `--l-now` | `--d-now` | §4.3 |
| `--status-now-ring` | `--l-now` | `--d-now-ring` | light Tier 3 is fill alone, so its ring is the fill colour and has no edge |
| `--status-now-label` | `--l-linen` | `--d-now-label` | the label on a Tier 3 fill |

`--l-stone`, `--l-greige`, `--l-oat`, `--d-dark-moss` and `--d-pine` are declared and
unmapped. §4.4 forbids adding a tenth neutral; it does not require spending all nine.

### 4.3 Status — three hues, and what they are for

Three hues, fixed. Never themed for decoration, never reused as a chart series
colour. Tier 0 carries **no status colour**, because it carries no escalation.

| Role | Light | vs linen | Dark | vs charcoal |
|---|---|---|---|---|
| `--status-clear` — examined, normal | `--l-clear` `#2A7A52` | 4.82:1 | `--d-clear` `#4FA36E` | 5.63:1 |
| `--status-review` — Tier 1 and Tier 2 | `--review` `#A87F1C` | 3.38:1 | `--review` `#A87F1C` | 4.73:1 |
| `--status-now` — Tier 3 | `--l-now` `#8E2A24` | 7.70:1 | `--d-now` `#A32F27` fill | ring `--d-now-ring` `#BC443A` 3.33:1 |

`--status-review` is the one step that is identical in both modes.

The light triad passes every gate:

```
[PASS] Lightness band       all 3 inside L 0.43–0.77
[PASS] Chroma floor         all 3 >= 0.1
[PASS] CVD separation       worst #8E2A24 <-> #2A7A52  ΔE 8.2 deutan · 20.0 tritan
[PASS] Normal-vision floor  worst #A87F1C <-> #2A7A52  ΔE 16.7
[PASS] Contrast vs surface  all 3 >= 3:1
```

Three rules keep it that way:

- **A status colour never appears without its word.** Type is the primary
non-colour channel; an icon may repeat the word under §7.3, never replace it.
A bare coloured dot is a defect.
- **Tier 3's solid fill is a safety channel, not styling.** With hue removed — photocopied, faxed, or read by a deuteranopic clinician — the fill weight and the L 0.520 / 0.438 lightness gap between clear and now are what remain.
- **Status never sits on `--d-forest`, `--d-pine`, `--d-dark-moss` or `--d-walnut`.** Those surfaces are themselves green and brown; a status mark on them reads as part of the card. Status lives on the page or on `--d-charcoal`.

In dark mode the Tier 3 badge is an `#A32F27` fill with a 1px `#BC443A` ring and a
`--d-now-label` `#F7F5F2` label at 6.45:1. The fill alone is 2.48:1 against
`--d-charcoal` — the ring is what makes the badge a shape rather than a smudge.

### 4.4 What colour may not do

- It may not be the sole carrier of any meaning. Ever.
- It may not encode a **data state**. §7.2.
- It may not encode tier *level*. A tier is a deadline and an owner, not a severity ([ADR 0001](adr/0001-time-to-action-not-severity.md)), so Tier 1 and Tier 2 share `--status-review` and are separated by their written window.
- It may not encode Baseline versus Routine. Those Visit-type indicators are words: the Roster shows a read-time planning indicator before Start, and a started Visit shows the settled type (ADR 0008).
- It may not be introduced. Nine neutrals per mode, three status hues, one accent in dark. A tenth is an edit to this document, not a decision in a component.

## 5. Typography

Two families. **EB Garamond** for display and the wordmark, **DM Sans** for
everything else.

**Every number is DM Sans.** Vitals, doses, dates, counts, tier labels, axis
ticks — without exception. A misread digit is a clinical error, and EB Garamond's
figures are narrower and lower-contrast at small sizes in bright light. Use
`tabular-nums` in anything that aligns vertically (table columns, axis ticks) and
proportional figures for a standalone readout.

The scale is **mode-independent**. Light and dark are the same document,
recoloured.

| Step | Size | Use |
|---|---|---|
| 7 | 49px | the one page title |
| 6 | 39px | section heading |
| 5 | 31px | sub-heading |
| 4 | 25px | the **serif floor** — the smallest size EB Garamond may appear at |
| 3 | 20px | large readout |
| 2 | 16px | body |
| 1 | 13px | uppercase labels, captions, eyebrows — the floor |

Ratio 1.25. Nothing is smaller than 13px. Below step 4, DM Sans only.

| Property | Value |
|---|---|
| Line height, body | 1.6 |
| Line height, long-form paragraph | 1.75 |
| Line height, display (steps 5–7) | 1.0 |
| Line height, 13px uppercase | 1.4 |
| Weights | EB Garamond 500; DM Sans 400 and 600 |
| Letter-spacing, display | −0.03em |
| Letter-spacing, 13px uppercase | 0.16em |

Three weights exist and no more. Both palette studies declared EB Garamond 600
and DM Sans 500 and then never used either; a weight nobody uses is still a font
file that has to download in a house with no signal.

## 6. Space, radius, depth

**Spacing — 4px base, and no other values:**

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`

16 is body size and 48 is the minimum touch target, so a button's padding and its
minimum height come from the same scale instead of fighting each other.

**Radius — four values:**

| Value | Applies to |
|---|---|
| `8px` | controls: inputs, selects, the Tier 3 badge |
| `16px` | containers: cards, panels, tables |
| `24px` | **one** primary container per screen — the subject of that screen |
| `999px` | buttons and pills |

The 24px step is hierarchy, not decoration. A screen has one subject — the Visit
Brief, the Emergency panel — and it may be visibly the largest thing on it. Two
24px containers on one screen is a defect.

**Depth — one level, two mechanisms:**

| Mode | Raised means |
|---|---|
| Light | `--l-surface-raised` `#FBFAF8` plus `--l-depth` `0 18px 55px rgba(48,43,36,.08), 0 2px 8px rgba(48,43,36,.05)` |
| Dark | `--d-charcoal` `#171B1A` above `--d-deep-onyx`, and `--d-depth: none` — no shadow at all |

In light mode the raised surface is *lighter* than the page. There is no second
raised plane in either mode: a raised thing does not contain another raised thing.

## 7. The mark vocabulary

### 7.1 Escalation Tiers

A tier is **a deadline and an owner** (ADR 0001), so it renders as a written
who-and-when. Colour marks only the boundary between "handle it" and "stop".

| Tier | Colour | Renders as |
|---|---|---|
| 0 | none — ink only | "Field Team acts" |
| 1 | `--status-review` outline | "Supervisor · within 72 hours" |
| 2 | `--status-review` outline | "Supervisor · during this visit" |
| 3 | `--status-now` **solid fill** | "Now — Supervisor not in the path" |

The badge is a **rectangle at radius 8**, not a pill, because a pill reads as a tag
or a filter chip and Tier 3 is a stop. Tier 3 is the only solid-filled badge in the
product, and that scarcity is the point.

`--status-clear` marks an item Noor examined and found normal — the instrument of
the visible-looking law. It is a mark **plus a word**, never a mark alone.

### 7.2 Present, Absent, Unreachable

The three data states carry **no status colour and no badge**. They are
typographic and structural.

[CONTEXT.md](../CONTEXT.md) forbids the vocabulary a UI would normally reach for —
*"null, missing, unknown, N/A, no data, empty — each of them collapses at least two
of the three"* — which means **an empty cell, an em dash and "N/A" are all
prohibited** in every table Noor renders.

| State | Renders as |
|---|---|
| **Present** | the value, in `--text`; a timestamp beside it when stale |
| **Absent** | a written finding **in the value's place**, in primary ink — "None in the house." It is a clinical fact, not an emptiness |
| **Unreachable** | a hairline-bounded block naming the input **and** the consequence — "The prescribed list could not be read. Discrepancies against it are not shown." |

**Absent** and **Unreachable** cannot be confused because they are different
*shapes*: one is inline text where a value goes, the other is a bounded block that
also states what was withheld. That, and not colour, is what satisfies §4.11's
requirement to name the input that was missing.

Only **Medication Reconciliation** and **Physical Examination** can ever be
Unreachable (§4.10), and Noor does not distinguish "no signal" from "EMR is down".
It is a rare state, so it must be unmistakable when it appears rather than quiet.

### 7.3 Icons

Noor has a small icon set. Every icon is inline, self-hosted SVG — never an
icon font, never a Unicode symbol, never fetched from a network.

The restriction is failure modes, not taste: an icon font renders a tofu box
on a missing glyph — the "Noor is broken" appearance §4.1 forbids — and
Unicode `✓` and `⚠` are in neither DM Sans's nor EB Garamond's charset, so
they fall through to the OS emoji font, where on Windows `⚠` arrives in full
colour and breaks both the colour budget and greyscale legibility.

Five rules keep the set safe:

1. Inline SVG stored beside the component. No font, no symbol, no URL.
2. Always beside its word, never instead of it — §4.3's word rule extends
from colour to shape. An icon that carries meaning alone is a defect.
3. 3:1 contrast against its surface (§2's floor), legible in greyscale and
under `forced-colors`, like every other mark.
4. One stroke weight and one size step per context; Tier 3's solid fill and
the status words in §7.1–§7.2 are unchanged by any icon beside them.
5. A new icon is an edit to this document, not a decision in a component —
the same standing as §4.4's tenth colour.

Consequences to build to:

- The **Write-Back queue** indicator, which §4.10 requires be visible and survive a device restart, is a count and a word — "3 Write-Backs pending". An icon may stand beside the words, never instead of them.
- The **theme switch** keeps drawn marks rather than joining the icon set — see below.
- A sort direction, a disclosure state and a validation error are words first; an icon may repeat them.

**The drawn exception — the theme switch.** A sliding pill carrying a sun and
a moon, top right of the chrome. It is exempt because the theme is the only control
in Noor that carries no clinical meaning: reading it wrong changes the brightness of
the screen and nothing else, so §4.4's "never the sole carrier" has nothing to
carry here. The two marks are **drawn in CSS — a filled disc, and a disc with a
transparent bite taken out of it — and never set in type**, because the charset
objection above applies at full force: neither DM Sans nor EB Garamond carries `☀`
or `☾`, so a glyph would arrive from the OS emoji font in colour. Each half keeps
its word as its accessible name, so the channel is removed from the screen and not
from the accessibility tree. Nothing else in Noor may cite this exception.

### 7.4 Confirmations

A confirmation is a `popover`: declarative HTML, `popover="manual"` so a stray glove
cannot dismiss it, a form inside it, no script required. §11 exempts it from the page
transition because it navigates nowhere.

**Three exist. Two acts are screens instead, and that is not an inconsistency.**

| Action | Guard | Why |
|---|---|---|
| **End Early** | popover carrying §5.10's reason list | The reason is required before the state changes, so it is asked where the decision is taken |
| **Cancelled** | popover carrying §5.10's reason list | §5.4 requires the reason on the same terms as End Early. Only the page differs — the act belongs to a **Scheduled** Visit, which has no action row — and one act asked two ways would be the real inconsistency |
| **Emergency** | popover, one confirming button, no fields | §5.7 demands nothing at entry; a guard asks about intent, never about content |
| **Complete Visit** | a screen | §5.8 checks eight sections, every Emergency and every Recommendation's disposition. That does not fit in a top layer, and the Junior Physician should read it rather than dismiss it |
| **Addendum** | a screen | Nothing but a script can open the top layer without a tap, and §12.1 admits none. §5.9 has the server render this one already carrying text — a write a closed Visit refused, kept rather than dropped — and a render is not a confirmation |

**Three copy rules.** These are §3's seventh rule with teeth:

- **It states what will be true afterwards**, not what the button is called.
- **It may not claim an irreversibility the state machine does not have.** Emergency exits back to In Progress (§5.1), so *"this cannot be undone"* is false and is forbidden. What is true is the documentation the close will demand: *"Entering the Emergency Protocol suspends the Visit Protocol. This Emergency must be documented — an end time and at least one timeline entry — before this Visit can close."*
- **The confirming button carries the verb, and the dismissing one says what dismissing does.** Neither may be "OK" or "Cancel": **Cancelled** is one of the six Visit states, and a button meaning *never mind* may not wear the name of a terminal state.

## 8. Language and direction

Chrome is **English, left-to-right, Western numerals**. Every field that accepts
free text, and every rendering of free text, applies **automatic direction
detection**, so an Arabic name or an Arabic note reads correctly without the page
flipping around it.

Noto Naskh Arabic is scoped to `[dir="rtl"]` and loads only where it is needed.

## 9. Modes and the toggle

Both modes are first-class. Neither is derived from the other, and the type,
spacing and radius scales are identical in both.

The toggle is a **form POST → cookie → server-side stamp**: the layout writes
`data-theme` onto `<html>` before the page is sent. That stays true now that §12.1
admits a script file, and for the two reasons it was chosen: a script that sets the
theme after the document has arrived *is* a flash of the wrong theme, and a route is
testable in Python where a listener is not — [ADR 0006](adr/0006-offline-by-locality.md)
puts branch coverage at 100% with no exclusions and coverage cannot see inside a
`.js` file. The toggle is a route.

Both modes' values are declared under **both** scopes — a `prefers-color-scheme`
media query for the OS setting, and a `[data-theme]` scope for the toggle — with
the toggle winning in both directions.

## 10. The Handover

The **Handover** is the record the ambulance crew leaves with. It is
clinician-to-clinician, and it is the only artifact that leaves Noor for a third
party.

- **Language:** English labels, Western numerals. The Patient's name and any free text render as stored, under §8's direction detection.
- **On screen:** follows the theme toggle like every other view.
- **In print:** forced light, always. A dark-mode print is illegible and empties a toner cartridge.
- **The print path is reachable from the Handover screen**, because most homes have no printer and the realistic delivery is the screen turned around or photographed.
- **No network dependency of any kind.** [ADR 0004](adr/0004-emergency-is-an-interrupt-state.md): *"Anything in them that requires a read is a feature that fails in the exact circumstance it was built for."* No remote font, no fetched image, no map tile.
- **Legible in greyscale.** A photocopied or faxed Handover is plausible. Tier 3's solid fill and the lightness gaps in §4.3 are what make that hold.

## 11. Motion

`@view-transition { navigation: auto; }` — 200ms, ease-out, wrapped in a
`prefers-reduced-motion` guard. One CSS declaration, no build step;
browsers without support ignore it and the page simply loads.

**The Emergency Protocol is exempt from the transition at both steps.** §5.7 says Noor
demands nothing at entry and does not manage the emergency — 200ms of fade between a
nurse deciding an ambulance is needed and the screen agreeing is 200ms taken from the
Patient. Its confirmation (§7.4) appears with no animation, and the Emergency screen
behind it arrives with none either. Entry is two taps and neither of them fades.

Nothing else animates, and `:hover`, `:focus` and `:active` are the only other
transitions that exist. **Every interaction that changes the record is a full page
load, with two named exceptions**: §12.1's autosave, which changes the record without
one, and a `popover`, which changes no record at all — a confirmation asked and
answered in the top layer, then submitted as a form like anything else.

## 12. Delivery

> `src/noor/web/` was removed. `src/frontend/` holds the Next.js SPA;
> `src/frontend/initial/` is the Roster throwaway — demo only, carrying
> documented violations (see its README), never the pattern to copy.
> This section fixes where each asset lives.

| Asset | Detail |
|---|---|
| Token layer (`src/frontend/`) | CSS custom properties mapped from the design tokens |
| `src/frontend/src/app/globals.css` | Tailwind v4 import + the `:root` token blocks + shadcn theme |
| `src/frontend/src/components/` | shadcn components and custom clinical components |
| `src/frontend/src/lib/` | shadcn helpers (no clinical logic — ADR 0006) |
| `public/fonts/*.woff2` | the four self-hosted faces: EB Garamond Medium (500, display and wordmark), DMSans Regular (400), DMSans SemiBold (600), Noto Naskh Arabic Regular (scoped to `[dir="rtl"]`) |
| `src/frontend/src/app/` | App Router routes: roster, Visit, and Supervisor surfaces (`initial/` is the throwaway roster) |
| `src/frontend/next.config.ts` | dev proxy `/api/*` → `http://localhost:8000`; production is a static export served by the same Python process (ADR 0006) |
| Icons | inline self-hosted SVG beside the component, per §7.3 — no font, no symbol, no URL |

Latin subset, self-hosted, `font-display: block`.

**No CDN, ever.** Offline is the default (§4.10), and a font request that hangs in
a house with no signal is the one moment Noor must not look broken. The
`fonts.googleapis.com` link in both palette studies is a study artifact and does
not survive into the product. `font-display: swap` is forbidden for the same
reason: it flashes a fallback and reflows the page, which is exactly the momentary
"looks broken" §4.1 rules out.

A `forced-colors` pass is required before ship: every meaning must survive the OS
replacing the entire palette, which it does here because no meaning is
colour-alone.

### 12.1 Autosave

Autosave is handled by the React section component: it posts to the JSON API endpoint
(`/visits/{id}/sections/{slug}`) on change, so no typed measurement is lost to a tablet
that dies, a closed lid, or a mis-tap, and no Save button competes with the three actions
in the Visit's action row. The server validates it exactly as it validates a button press.

Three rules that do not move:

- **No clinical logic in the browser, ever.** [ADR 0006 amended](adr/0006-offline-by-locality.md) draws this line and it is the load-bearing one. The Visit state machine, the withholding principle (§4.11), the N3 cap and every rule that decides what is true stay in Python where the coverage gate can see them. The component decides *when* to post, never *what is true*.
- **Self-hosted, no framework dependency in the browser.** The built SPA is a static bundle; the fonts are self-hosted; nothing is fetched from a network a house may not have.
- **The form works without autosave.** Every section still saves on the submit that navigates away from it, so the record survives without the component's change listener — which is also what makes autosave a convenience rather than a dependency.

## 13. Enforcement

A token lint (stdlib `re` + `pathlib`, no new dependency) will read `src/frontend/src/app/globals.css` and every component file and fail if a hex colour, a `font-size` in px outside the design scale, a `border-radius`, or a padding/value appears outside the token layer mapped in `docs/frontend_ssot.md` §4. It will live in `tests/`, so it will add no covered source to the 100% branch-coverage gate. It also fails on an icon font, a Unicode symbol standing in for an icon, or any icon fetched from a network (§7.3) — anywhere outside `src/frontend/initial/`, which is grandfathered as the throwaway.

**It enforces the vocabulary, not the grammar.** It can prove nobody wrote
`#8E2A24` into a component instead of `var(--status-now)`. It cannot prove that a
status colour appeared beside its word, or that Tier 3 kept its solid fill — those
stay human review. Raw-value drift is the failure that actually happens, and it is
the one a regex catches perfectly.

## 14. Named limits

Out of scope deliberately, and named here rather than solved:

- **Full Arabic localisation.** Chrome is English. Arabic free text renders correctly by direction and typeface; it is not translated. Clinical translation needs a bilingual clinician's review, not a string table.
- **Clinical translation of the Handover.** Same reason, and higher stakes.
- **No patient or caregiver surface.** §5.13 — they are outside the software.
- **No authentication, localhost only.** A device-security limit, not a design one, stated here because a design system that implied a login screen would be lying about what exists.
- **Chromium is the demo target.** The view transition in §11 is progressive enhancement; nothing else depends on it.
- **Autosave is covered by the Python gate.** The React component calls the JSON API endpoint (`/visits/{id}/sections/{slug}` with `POST`); the endpoint validates the payload exactly like any form submission, and that route is covered by the suite. What the browser chose to post — when it decided to post — is handled by the component, not by a standalone script, so the coverage argument of §12.1 no longer applies.







