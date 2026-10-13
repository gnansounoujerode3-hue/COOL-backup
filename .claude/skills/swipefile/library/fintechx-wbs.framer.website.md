# fintechx-wbs.framer.website

**Callable as: FintechX** (aliases: fintechx, fintechx-wbs, "the bento fintech one")

AI finance / investment marketing template. Captured 2026-07-30 @ 1440×900 from the
live site (no mirror). Stack: **Framer `010e00d`**, server-rendered, script-dependent.
**Capture-only (Adapt donor)**: captured to supply two regions to myRA's /v6, not
rebuilt.

Fourth Framer capture in the library. Its value here is (a) a genuinely reusable
**bento composition** with measured cell geometry, (b) a **dashboard-showcase**
pattern, and (c) it settles a question the [onefin](onefin.framer.website.md) entry
raised about whether Framer's CSS easing is a site choice or a framework default.

Page 14,490px, 19 full-width bands, 1,166 named nodes (121 distinct, and the names are
generic Framer component names like `Content`/`Top`/`Bottom`, not descriptive section
names, so band identification has to run on geometry).

---

## Type: one display grotesque, one interface sans

| Role | Family | Size / LH | Weight | Tracking |
|---|---|---|---|---|
| Hero H1 | **Bricolage Grotesque** | 100px | 600 | - |
| Section H2 | **Bricolage Grotesque** | 48 / 57.6 (1.2) | 600 | **-1px** |
| H3 | Bricolage Grotesque | 32px | 600 | - |
| H4 | Bricolage Grotesque | 24px | 600 | - |
| Sub / button label | Inter Display | 18 / 23.4 (1.3) | 500 / 600 | normal |
| Card body | Inter Display | 16 / 20.8 (1.3) | 500 | normal |
| Eyebrow, pill labels | Inter Display | 14 / 18.2 (1.3) | 500 | normal |
| Ghost display (BUY/SELL) | Inter Display | 86 / 61.92 | 700 | uppercase |

Same architecture the library has now recorded four times: **one voice reserved for
display sizes, one geometric/neo-grotesque sans doing all interface work**. Note the
interface line-height here is a tight **1.3**, not the 1.5 onefin uses.

## Colour

| Hex | Role | Uses |
|---|---|---|
| `#000000` | dark card, buttons, dominant | 2596 |
| `#4D585F` | secondary text (the workhorse) | 218 |
| `#1D1D1D` | primary text, **not** pure black | 195 |
| `#FFFFFF` | surfaces | 140 |
| `#EDF1F4` | **the light card fill** | 40 |
| `#BABABA` | secondary text on dark | 20 |
| `#10B981` | positive / gain | 2 |
| `rgba(255,13,13,0.05)` | the red glow behind the BUY state | 2 |

White-alpha ramp on dark: `0.1` · `0.3`. (`rgb(0,0,238)` at 348 uses is the UA default
link colour on unstyled anchors: an artifact, not a design token.)

## Geometry

- Container **1260**, content **1200**, so a 30px gutter each side at 1440.
- **Radius ladder: 100px (pills, 66 uses) · 50% (circles, 78) · 30px (42) · 20px (31) ·
  10px (13) · 24px (3).** Cards are 20–30px; pills are fully round. Not a single token.
- Section padding-top **200px** on both captured regions, very generous.
- Inner measures: 1260 / 1200 / 860 / 800 / 760 / 380.

## Motion
**Motion fidelity: partial**. Instrumented via `Element.prototype.animate`: 63 starts with durations, a 12-step delay ladder, and reveal travel (20/10/50px). No per-element mapping.


**One curve, and it is the same one onefin uses.** `cubic-bezier(.44,0,.56,1) @ .4s`
appears 14× in CSS here and 45× on onefin (two unrelated templates, byte-identical).
Combined with the `linear(0, 0.024, 0.0823, 0.1594, 0.2448, …)` spring appearing in the
JS layer of **both** sites, this is **Framer/Motion's default serialization, not a
design decision**. Do not report it as a site's signature; do reach for it as a safe
Framer-native default.

Only **1 CSS `@keyframes`** on the page (`__framer-loading-spin`), confirming the
JS-only motion pattern for a fourth time.

Instrumented via `Element.prototype.animate` (63 starts):

- **Durations:** 1000ms (×27) · 600ms (×18) · 400ms (×16) · one 10000ms.
- **Delay ladder:** 0 / 50 / 100 / 150 / 200 / 250 / 300 / 400 / 500 / 600 / 700 / 1200
  (a coarse ~100ms element-level stagger, nothing per-character).
- **Reveal:** `opacity 0.001 → 1` (×23) plus `transform: translateY(N) → 0`, travel
  **20px (×10) · 10px (×6) · 50px (×1) · ±15px**. One variant adds a `rotate(-0.064deg)`.
- **The spring is pre-baked into the keyframe array** (every intermediate value written
  out, `easing: "linear"`) rather than expressed as a `linear()` easing, a different
  Motion output mode from onefin's. Either is fine to reproduce; the baked form is
  what you will see if you read keyframes rather than timing.

So: a conventional, well-tuned **fade-up**. It is *not* distinctive, and that matters
when composing. See Reuse notes.

## The two regions worth taking

### 1. Core features: the bento

Band `Features`, 1440×1211 @3218, padding `200px 0 0`.

Header row is **two columns of 575px, gap 50**: left holds a level (untilted) eyebrow
pill + the 48px H2 on two lines; right holds the sub paragraph and a black pill button
with a circular arrow chip, right-aligned.

The grid is **3 × 380px, gap 30px** (380·3 + 30·2 = 1200), split into a 790px left
sub-grid and a 380px right column:

```
┌─────────────┬─────────────┬─────────────┐
│ 01  380×393 │ 02  380×393 │             │  ← left sub-grid: 380 380, gap 30
├─────────────┴─────────────┤ 01  380×528 │  ← right col, THE BLACK CARD
│ 03        790×374         │   (#000)    │
└───────────────────────────┼─────────────┤
                            │ 02  380×239 │
                            └─────────────┘
```

Light cells are `#EDF1F4`, radius **20px**. Every cell puts its **title at the top,
centred**, and lets a visual fill the rest. The load-bearing quality is **variety of
treatment across cells**: a 3D object, a photographic panel with a glass overlay,
pure oversized type on black, a wide composite, and a compact utility card. Five
identical boxes is the failure mode.

### 2. Platform overview: the dashboard showcase

Band `Overview`, 1440×1654 @4429, padding `200px 0`.

Centred header, 800px wide: eyebrow pill, 48px H2 on two lines, sub, then two buttons
(gap 20, height 59): a light/blue gradient pill with a circular arrow chip, and a
solid black pill.

Below, `Bottom` 1200×885, gap 30:
- **the frame**: 1200×701, radius 20, `#fff`, holding a full app-UI mockup (sidebar +
  topbar + stat cards + trending-assets row + table + donut). The UI **bleeds off the
  bottom edge** of the frame rather than being fully contained, which is what sells it
  as a real screen rather than a picture of one.
- **three benefit cards**: 1200×154, grid 3×380, gap 30, each an icon chip plus two
  lines of copy.

The whole band sits on a **full-bleed photograph** with `BG Top` / `BG Bottom` 1460×200
image strips handling the fade into the white sections above and below.

## Gotchas

1. **Band names are useless here.** Unlike onefin, the `data-framer-name` values are
   generic (`Content`, `Top`, `Bottom`, `Desktop`, `Default`). Identify bands by
   geometry (full width, height > 200) and dedupe co-located wrappers, then read the
   text inside to label them.
2. **The spring is inside the keyframes, not the timing.** A motion audit that reads
   `getTiming().easing` sees `"linear"` 39 times and concludes there is no easing.
   Read `getKeyframes()` / the `animate()` argument instead.
3. Two of the five bento cells and the whole overview band depend on **photography**.
   Any adaptation without an image budget has to replace those with CSS/SVG, and that
   is the single hardest part of reusing this page.

## Rebuilding the bento: the two things that decide whether it works

Measured while adapting this board onto a 1344 container for myRA's /v6.

**1. The misaligned seam is the whole composition.** The wide field's
horizontal gap sits at **51.2%** of block height; the narrow rail's sits at
**68.1%** (135px apart at 1200, 152px at 1344). Line those up and you have a
2×3 table. The failure is silent: every cell is still the right size, the board
just goes dead. If you verify one number after rebuilding this, verify the seam
offset, not the cell sizes.

**2. `grid-template-rows: 596fr 272fr` does not do what it looks like.** A bare
`Nfr` row carries an implicit `auto` minimum, so any cell whose content is taller
than its share grows its row and steals the difference from its sibling, which
drags the seam off its percentage with no error anywhere. This bit during the
rebuild: a four-row notification stack pushed the rail's short row from 272 to
364 and pulled the tall one down to 504, moving the seam from 68.2% to 57.9%.
**Write `minmax(0, 596fr) minmax(0, 272fr)`** and let the cells' `overflow: clip`
do the clipping, which is the intent anyway; this board clips deliberately in
three places.

Corollary for React: if each cell is wrapped by a reveal component, every
wrapper in the chain needs `height: 100%` or the `fr` rows collapse to content
height and the same silent failure occurs.

## Reuse notes

Take the **compositions**, not the tokens. The bento's cell-size relationship
(393/393/374-wide-span against a 528+239 right column) is the transferable idea and it
re-derives cleanly onto any container width; the `#EDF1F4`-on-white palette and the
20px radius are ordinary and worth overriding with the host system's own.

The motion is explicitly **not** worth taking if the host page already has a
distinctive reveal. This is a stock fade-up, and onefin's per-character blur beats it
on character. Composition from here, motion from there.

**Cross-site (see [INDEX.md](INDEX.md) patterns):** display-face-reserved-for-display-sizes
now holds at 4/4 Framer captures; `cubic-bezier(.44,0,.56,1) @ .4s` + the
`linear(0, 0.024, 0.0823, …)` spring are confirmed Framer defaults across two
unrelated templates, so neither is evidence of authorship.
