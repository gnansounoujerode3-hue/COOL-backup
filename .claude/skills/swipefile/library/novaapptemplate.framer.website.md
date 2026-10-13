# novaapptemplate.framer.website

**Callable as: Nova** (aliases: novaapptemplate, nova app template, nova budgeting app, nova framer)

Budgeting / personal-finance marketplace template: one indigo-blue accent on a
warm off-white base, income/expense demo data in a phone-mockup dashboard.
Captured 2026-08-18 @ 1440×900 (breakpoints swept 390/768/1440; motion
instrumented separately at 1424×805, `--settle 4`, 14-step scroll pass; fonts
probed separately at `--settle 3`). Stack: Framer
(`data-framer-generated-page`, `framerMotion` detected at runtime; no build
hash fingerprint retained this pass). **Capture-only (Audit)**: design system
measured for reference, not mirrored or rebuilt.

Tenth Framer template in this library by direct count (createstudio, osa,
onefin, fintechx, homy, fluence, agentwise, salix, hanzo, Nova). It reconfirms
the 0–809.98 / 810–1199.98 / 1200+ breakpoint triad for a fifth-plus time and
the flat-px-per-tier (no fluid rem/vw driver) pattern for a tenth, but it is
the first entry in the library where **one sans family carries the entire
scale, display included**, breaking the "separate face reserved for display
sizes" pattern this library had confirmed 4/4 up to fintechx.

## Type: one sans, all weights and sizes, one mono accent

No dedicated display face. **General Sans** (weights 400/500 only) runs the
whole scale from an 8px micro-label up through the 48px hero; hierarchy is
carried by size and weight, not by a second typeface. **DM Mono** 500 is the
only other rendering family, reserved narrowly for the eyebrow badge and a
handful of small mono labels. Declared-but-dead: **Fragment Mono** (3 faces,
all `unloaded`) and **Inter** (~25 faces across 400/700/900 + italics, every
one `unloaded`). Both sit in Framer's fallback stack (`var(--framer-font-family,
Inter, …)`) and are never actually requested by anything rendered.

Census, `sampled.typeScale` at 1440 (size / weight / line-height / tracking / count):

| Role (visually confirmed) | Size / LH (ratio) | Weight | Tracking | Count |
|---|---|---|---|---|
| Hero H1 (≥1200px) | 48 / 52.8px (1.1) | 500 | **-0.03em** | 230 |
| Hero H1 (<1200px, tablet=mobile) | 39 / 42.9px (1.1) | 500 | -0.03em | 230 |
| Section H2 (≥1200 only, see gotcha) | 33 / 39.6px (1.2) | 500 | -0.03em | 8 |
| Lead paragraph / body-large | 19 / 24.7px (1.3) | 400 | -0.02em | 29 |
| Card title | 19 / 24.7px (1.3) | 500 | -0.02em | 19 |
| Body | 16 / 20.8px (1.3) | 400 | -0.02em | 19 |
| List row / label | 14 / 16.8px (1.2) | 500 | -0.02em | 21 |
| Eyebrow / mono badge | **DM Mono** 13 / 13px (1.0) | 500 | normal | 25 |
| Meta, weight 400 | 12 / 14.4px (1.2) | 400 | -0.02em | 7 |
| Meta, weight 500 | 12 / 15.6px (1.3) | 500 | -0.02em | 7 |
| Micro label | **DM Mono** 8 / 9.6px (1.2) | 500 | -0.01em | 7 |
| Secondary body variant | 14 / 18.2px (1.3) | 400 | -0.02em | 4 |
| Baseline default (see gotcha, not a copy census) | 12 / normal | 400 | normal | 1070 |

**The tracking rule is exact, not approximate**: -1.44/48 = -1.17/39 = -0.99/33
= **-0.03em** at every display-tier size; -0.38/19 = -0.32/16 = -0.28/14 =
-0.24/12 = **-0.02em** at every interface-tier size; -0.08/8 = **-0.01em**
at the smallest tier. Three clean steps (-0.03 / -0.02 / -0.01em), no
intermediate values. Copy the em ratio per tier, not the px.

Rendering confirmed independently of the declaration, via `font-gate.js`
canvas-width differencing (`differs: true` = the glyph advance actually
changes vs. a serif fallback, not just a declared-but-silently-fallen-back
font): General Sans 500 @ 68px (1442.21px vs 1447.86px fallback), General Sans
400 @ 23px (474.56 vs 489.72), DM Mono 500 @ 13px (335.4 vs 276.8: the widest
gap, consistent with genuine monospace metrics).

Responsive: only the H1 is confirmed to reflow (48→39px, identical count both
sides, 768 and 390 share the tier exactly). The 33px section-H2 tier drops out
of the top-12 census below 1200px (not resolved by this pass); it may shrink
to a value ranked below the top 12, or fold into an existing tier.

## Layout

- Breakpoints (`mediaConditions`, byte-identical at all 3 widths): the site
  emits **both** integer and `.98` fractional edges simultaneously:
  `(max-width: 1199px) and (min-width: 810px)` **and**
  `(min-width: 810px) and (max-width: 1199.98px)`, same for 809/809.98. True
  tiers: **<810 / 810–1199 / 1200+**. (Corrects a same-day oversimplification
  in this capture's own field notes that reported only the `.98` pair; see
  Gotchas. Reconfirms onefin's "don't treat a missing `.98` as evidence a site
  isn't Framer" the other direction: both forms can coexist on one template.)
- Content container width was not retrievable as a CSS rule (class names
  survive in `markup.html`, the rule itself lives in a stylesheet not
  captured). Independently pixel-scanned the nav row instead (`nav-crop-{w}.png`
  against the page's own corner background, threshold 30 on summed RGB delta):
  **868px** (x 285–1153) at 1440, **726px** (x 21–747) at 768, **348px**
  (x 21–369) at 390. 768 and 390 share the same near-edge-to-edge ~21px
  margin; 1440 jumps to a ~285px centered inset. This is the *nav row's*
  measured span specifically, other sections were not independently
  re-measured and may use a different inner measure. (The scan's own corner
  background sample read `#F4F4F4`, one step off the CSS-confirmed
  `#F3F3F3` page background: plain PNG/anti-aliasing noise in the
  screenshot, not a second background token; not carried as a palette entry.)
- Radius ladder: **8px dominant (196)**, 80px pills (33), 16px (12), 12px (9),
  10.19px (7), 13.81px (6), 20px (6), 100% circles (6, avatars/icons), 30px
  (2), 6.9px (2), 11px (2), one compound `40px 40px 0 0` (1, a bottom-flush
  sheet/card).
- Gap ladder: **10px dominant (119)**, 20px (32), 12px (21), 8px (20), 16px
  (16), 24px (9), 4px (8), 5.1px (8), 10.19px (8), 2px (8), 7.64px (7), 6.9px
  (6).
- Vertical section padding pairs: 32/32 (8), 13.81/13.81 (6), 24/24 (6),
  20/20 (6), **164/0 (3: section top-pad only, no bottom)**, 128/128 (2),
  48/48 (2), 40/40 (2), 172/0 (1), 128/0 (1), 16/16 (1).
- Shadows: only **3 distinct values on the whole page**: a soft ambient
  (`rgba(0,0,0,.05) 0 2px 14px`, 2), a hard 1px inset ring (`rgb(0,0,0) 0 0 0
  1px inset`, 2), and one 3-layer soft card shadow (1 use). Effectively flat:
  cards read through radius + fill, not elevation.
- Transitions: `all` on 1466 elements (Framer's default hover safety net,
  meaningless for authorship) and `color 0.2s cubic-bezier(0.44, 0, 0.56, 1)`
  on 9: **the same curve onefin (45 uses) and fintechx (14 uses) carry**.
  Third confirmation this is a Framer/Motion default serialization, not a
  per-site design decision.

## Colour

Text (1440, hex + role + count):

| Hex/rgba | Role | Count |
|---|---|---|
| `#000000` | primary ink | 1265 |
| `#0000EE` | **UA default `:link` blue (not the brand, an artifact)** | 86 |
| `rgba(0,0,0,.6)` | secondary/muted text | 51 |
| `rgba(255,255,255,.56)` | muted text on dark/tinted surfaces | 19 |
| `#FFFFFF` | inverse text | 18 |
| `rgba(0,0,0,.56)` | secondary muted, alt alpha | 13 |
| `#1B2BB8` | **brand blue** | 12 |
| `#F23731` | expense / negative (dashboard demo data) | 3 |
| `#E2E4F6` | pale lavender tint | 2 |
| `rgb(27,42,183)` | brand-blue rounding variant (anti-aliased sample, not a second colour) | 1 |
| `#0C6946` | income / positive, deep | 1 |
| `#13BB5C` | income / positive, bright | 1 |

Backgrounds (1440):

| Hex/rgba | Role | Count |
|---|---|---|
| `rgba(255,255,255,.08)` | translucent card/chip fill | 58 |
| `#FFFFFF` | white surface | 28 |
| `#1B2BB8` | brand blue: CTA fill | 19 |
| `#E2E4F6` | pale lavender surface/badge | 13 |
| `rgba(0,0,0,.08)` | translucent dark overlay | 10 |
| `#F3F3F3` | **page background** (`html body` rule) | 9 |
| `#000000` | black card/surface | 9 |
| `#E6E6E6` | light grey divider/surface | 9 |
| `rgba(0,0,0,.6)` / `rgba(255,255,255,.12)` / `.76` / `.56` | overlay states | 3 each |

The system: one blue hue (`#1B2BB8`) doing double duty as both text-accent and
button-fill (no separate "link colour"); a strictly-sparing semantic pair
(green income / red expense, 1–3 uses each, confined to the demo dashboard
widget, not chrome); and a **white-alpha ramp on a light base** (.08/.12/.56/.76)
for card/chip layering: the same alpha-layering mechanism this library has
recorded on dark UIs (onefin, osa, youtube) now confirmed on a *light* one.

**The census is a top-12 list per breakpoint, not exhaustive, confirmed by
comparing all three widths.** Two colours rank into 768/390's top-12 that
1440's does not surface: `#F13730` (`rgb(241,55,48)`, text, 5 uses at
768/390), a one-digit-off near-duplicate of the expense red `#F23731`, both
present simultaneously at 768/390 (5 and 3 uses respectively), most likely two
distinct demo transaction rows sampled at slightly different sub-pixel
positions rather than two design tokens; and `#156949` (`rgb(21,105,73)`, a
**background** fill, 2 uses at 768/390 only, not in 1440's top-12
backgrounds), a fill-variant of the income green, unresolved whether it's
mobile-specific or just below 1440's rank cutoff. Read any `sampled.*` array
as "top 12 at this breakpoint," never as the page's complete set.

## Motion

**Motion fidelity: partial**

Instrumented via `getAnimations()` (pre-injected hook + 14-step scroll pass,
188 animations, 0 dropped) plus a separate `framer/appear` JSON payload scrape
(+3 tweens, not in the 188). Four elements/groups carry full target, trigger,
from→to, duration, easing and stagger, spec-grade for those specifically,
but **only 2 of 14 scroll steps ever registered new animations** on a 9989px
page, so the middle-to-lower two-thirds of the page has zero motion data, not
zero motion. Do not build the rest of the page's reveals from this entry;
re-capture them.

**The signature curve is a baked spring, not a bezier.** `linear(baked spring,
330 stops)` covers 185 of 188 animations (a `linear()` timing function long
enough that the capture tool labels rather than dumps it; the underlying
spring waypoints aren't retained). The only literal CSS keyword curve is
`linear` (2, the marquees) plus one shorter `linear(baked spring, 60 stops)`
(1). Durations: **3300ms ×185** (the spring's WAAPI-reported settle time:
reads faster than 3.3s visually; springs report duration-to-precision, not
perceived fade time), **57333ms ×2** (marquee loops), **600ms ×1** (one
scroll reveal). Separately, the `framer/appear` payload's 3 tweens use a
straight-line bezier `cubic-bezier(0,0,1,1)` at 600ms each, functionally
`linear`.

Stagger: one ladder, 100ms rungs (0/100/200/300/400/500ms), reconstructed by
grouping the 185 character-span animations by delay: 27/34/35/36/29/24
character-spans per rung (sums to 185), i.e. **six lines of one hero
paragraph, staggered by line at 100ms, every character within a line sharing
that line's delay** (not per-character stagger). A second, separate 100ms
ladder (0/0.1/0.2s) covers 3 named elements in the `framer/appear` payload,
almost certainly the eyebrow/heading/CTA entrance for the same hero, captured
through Framer's appear-effect JSON rather than WAAPI.

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| Hero paragraph reveal | `h2.framer-text` in the hero, per-character `<span>` | tool buckets as scroll (fires at scrollY 1312px); **treat as load/mount**, see Gotchas | `opacity: 0.001 → 1` | 3300ms | `linear(baked spring, 330 stops)` | 100ms per line (6 lines) | N/A: load-time, not scroll-linked |
| Marquee A | `ul` (logo/partner strip) | load (fires at scrollY 0) | `translateX(0) → translateX(-1720px)` | 57333ms, infinite | `linear` | none | always-running, not scroll-driven |
| Marquee B | `ul` (opposite-direction strip) | load (fires at scrollY 0) | `translateX(0) → translateX(1720px)` | 57333ms, infinite | `linear` | none | always-running |
| Budget-category chip reveal | category filter chip list, features section | scroll / IntersectionObserver, confirmed genuine (fires at scrollY 5248, ~52% down the page) | `opacity: 0 → 1` | 600ms | `linear(baked spring, 60 stops)` | none (single element) | starts ~46% viewport |
| Hero eyebrow/heading/CTA entrance | 3 named nodes, `framer/appear` payload | load | `opacity: 0.001 → 1` | 600ms | `cubic-bezier(0,0,1,1)` | 0/100/200ms | N/A: load-time |

Everything else on the page (features grid, how-it-works, testimonials,
pricing, blog) has **no motion data in this capture**: not confirmed static,
simply unswept.

`prefers-reduced-motion`: no media query present on the page; capture
environment itself was not in reduced-motion mode either, so this is unknown
territory, not confirmed-absent.

## Interaction states

Framer's own generic anchor-hover boilerplate is present in CSS this time
(17 of 18 `interactionRules`): a repeated `a.framer-text:hover` /
`code.framer-text a:hover` / current-page-link chain swapping colour via
nested `var(--framer-link-hover-*)` fallbacks. This is framework boilerplate,
not site-authored interaction design. Do not read it as Nova's hover system.
The one genuinely site-specific rule: `[data-framer-cursor="grab"]:active {
cursor: grabbing; }`, confirming a drag-scroll affordance (the testimonials
carousel). No button/card-level hover deltas were captured in CSS; if they
exist, they are JS-driven and were not instrumented this pass.

## Template taxonomy

Not applicable: only the homepage was captured (no `crawl.py` multi-page
pass). Nav links (Company / Support / Resources) were not followed, so
whether this template has further on-site pages is unknown.

## Gotchas hit while rebuilding

1. **`capture.py`'s `markup.html` write crashes on non-cp1252 bytes.**
   `pathlib.write_text()` with no explicit encoding defaults to the process
   locale (cp1252 on this machine) and raises `UnicodeEncodeError` the instant
   captured HTML contains a non-cp1252 character: this page's scripted AI-chat
   demo text contains a 👋 emoji. First run died immediately after writing
   `extraction-1440.json`. Worked around with `PYTHONUTF8=1` in the
   environment; verified the resulting `markup.html` byte-for-byte against a
   direct fetch of the live page afterward: no mojibake. Real defect in the
   script, not just this run: fix at the source with
   `(out_dir / "markup.html").write_text(text, encoding="utf-8")`.

2. **The tool's own field notes oversimplified the breakpoint edges.** A
   same-day summary of this capture reported only the `.98` fractional pair
   (809.98/1199.98). The raw `mediaConditions` array actually carries **both**
   the integer (`max-width:809px`, `max-width:1199px`) and fractional
   (`.98`) forms at every one of the 3 captured widths: not a rotation
   between builds, a single template emitting both simultaneously. Read
   `mediaConditions` directly; don't trust a paraphrase of it, including this
   one; that's the whole discipline this entry was written under.

3. **`sampled.typeScale`/`fontFamilies` count styled elements, not rendered
   text.** The dominant tier (12px/400/normal-lh/`sans-serif`, 1070 elements)
   looks like it should be the site's body-copy census. It is not: many
   12px-tagged nodes in the raw markup declare `--framer-font-family:"General
   Sans"…` as a custom property, yet the *computed* `font-family` several
   elements resolve to is the bare `sans-serif` UA fallback, a cascade gap
   between the custom property and the applied rule, not simply "Inter is
   unused" (a real, separate finding also confirmed: 25 of 30 loaded
   `@font-face` records are for Inter/Fragment Mono, neither of which
   `document.fonts` ever marks `loaded`). Cross-check any large flat tier in
   `sampled.typeScale` against `font-gate.json`'s canvas-width-verified census
   before trusting it as a copy count.

4. **The hero-paragraph reveal is very likely load-time, not scroll-triggered,
   despite how the tool classifies it.** It fires at `firedAtScrollY: 1312`
   and gets bucketed as `scrollTriggered`, but the target is the first content
   block on the page (visible at scroll 0); the capture's first snapshot is
   taken shortly after load at scrollY 0 (per the tool's own settle delay,
   not independently re-measured here), and if the animation hadn't started
   (or wasn't yet enumerable via `getAnimations()`) at that exact instant, it
   only shows up at the *next* scroll step and gets stamped with that step's
   scrollY. Across the whole capture only 2 of 14 scroll steps ever produced
   new animations at all, consistent with most "triggers" being load-time
   events caught late, not real scroll gates. Build this one as fires-on-mount.

5. **Design tokens are per-element, not a root sheet.** Root-scope
   `customProperties` holds exactly 2 unique entries, both Framer engine
   internals (`--overflow-clip-fallback`, `--one-if-corner-shape-supported`).
   The real values live as 22+ distinct hashed `--token-<uuid>` custom
   properties written inline in each element's `style` attribute, each
   carrying its own CSS fallback; the same UUID can even carry *different*
   fallback values at different call sites (one token in this markup resolves
   to `rgba(255,255,255,.24)` once and `.12)` forty-four times elsewhere).
   Read fallback values per element, never assume one token name means one
   value sitewide.

6. **Two independent font-measurement passes disagree on raw counts** (e.g.
   48px/500 General Sans: 230 in `extraction-1440.json`'s typeScale vs. 190 in
   `font-gate.json`'s census; 14px/500: 21 vs. 14) while agreeing on every
   *family* assignment and most smaller tiers exactly. They're separate
   scripts run at slightly different viewports (1440×900 vs. 1424×805) and
   likely different DOM-walk strategies. Use `extraction-*.json` for
   frequency ranking, `font-gate.json` for family/weight attribution and
   render-proof, and don't average the two into a single number.

## Verification achieved

Structural: 3 breakpoints (390/768/1440), 0 blocked stylesheets at any width,
1566–1668 elements sampled per breakpoint, `markup.html` verified
byte-for-byte against a direct fetch of the live page after the encoding
fix. Container width (868/726/348px), independently re-derived by this writer
via pixel-scan of `nav-crop-{w}.png` against the page's own background,
matched the field-note figures exactly; not cross-checked against a captured
CSS rule (none was retained) and not re-measured for any section besides the
nav row. Font rendering independently confirmed via canvas-width differencing,
not just declaration. Motion: single-viewport capture (1440/1424×805 only,
no 768/390 motion pass); 14-step scroll instrumentation returned new
animations at only 2 steps, so this entry's motion coverage is a genuine
subset (hero paragraph, both marquees, one mid-page reveal, and 3 appear-
payload entrance tweens) with the remainder of a 9989px page unswept, not
confirmed static. No mirror or visual diff was produced (capture-only Audit);
there is no pixel-diff percentage for this entry. No multi-page crawl was run.
