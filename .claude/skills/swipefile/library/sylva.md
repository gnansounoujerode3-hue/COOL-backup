# mengto.github.io/sylva

**Callable as: Sylva** (aliases: sylva, mengto sylva, meng to sylva)

Nature / land-restoration concept hero by product designer Meng To (author of
"Design+Code"). Captured 2026-08-19 @ 1440×900 (also swept 768×900, 390×900;
motion and fonts separately instrumented at 1424×805), headless Chrome over
CDP, hooks pre-injected before load. Stack: plain static HTML on GitHub Pages
(`Server: GitHub.com`), no framework or CMS fingerprint: one hand-written
inline `<script>` (2,647 lines) driving a shared `requestAnimationFrame` loop,
plus `three.min.js` (`data-engine="three.js r149"` on the canvas, confirmed at
runtime, not from a bundle comment). **Capture only (Audit)**: no mirror or
rebuild attempted.

The entire site is one `<main class="hero">` screen. `document.documentElement
.scrollHeight === window.innerHeight` exactly (ratio 1.000) at three
independently-checked viewports (1424×805, 1440×900, 375×812). This is a
fixed-viewport "stage," not a long page that failed to scroll. The nav items
(Grove/Habitats/Journal/Enter) and the "Discover ↓" cue are inert (`href="#"`);
there is nothing else on the site to capture.

## Type: one variable family, hierarchy by size/weight/tracking only

**Lexend**, a single self-hosted variable font (`weight: 100 900`,
`sylva-assets/lexend-latin.woff2`, format woff2) carries the entire interface:
98 of the 111 sampled elements at 1440. The only other painted families are
system fallbacks (`Arial` ×10, `"Times New Roman"` ×1) that show up nowhere a
weight/size combo was deliberately set, not a second authored typeface.
`document.fonts` confirms `Lexend 100 900 loaded`, and canvas-width probing at
four size/weight combinations proves the face is actually painting (not a
metric-compatible fallback): weight 500/size 10 (requested 230.64px vs.
fallback 212.92px), 300/56 (1236.09px vs. 1192.35px), 400/276 (6231.25px vs.
5876.59px, the giant background "SYLVA" wordmark), 600/12 (282.07px vs.
270.09px). All four `differs: true`.

Census at 1440 (size / weight / line-height / letter-spacing / count):

| Size / weight / lh / ls | Count | Role |
|---|---|---|
| 16px / 300 / normal / normal | 50 | base inherited size |
| 9.9px / 500 / normal / 1.35px | 31 | small uppercase UI label (nav / dock) |
| 13.3333px / 400 / normal / normal | 10 | secondary UI text |
| 56.7px / 300 / 58.5px / -0.36px | 5 | hero headline (h1 + 2 spans + 2 nested `i`) |
| 13.95px / 300 / normal / normal | 2 | - |
| 23.58px / 400 / 24.3px / -0.45px | 2 | card-title tier (2 `h2`s) |
| 12.15px / 300 / 17.1px / normal | 2 | `p.label` tier (2 labels) |
| 12.15px / 600 / 18.9px / normal | 2 | `dt` stat-label tier (2 stat blocks) |
| 9.9px / 400 / normal / 3.96px | 2 | - |
| 16px / 400 / normal / normal | 1 | - |
| 279px / 400 / 217.62px / 27px | 1 | background wordmark glyph |
| 14.85px / 300 / 19.8px / normal | 1 | - |

The 279px wordmark row is the same element the font-gate canvas probe measured
at size **276** (its own `census` field, unitless). A real, small, expected
difference: the probe ran at viewport width 1424, the census at 1440, and the
whole scale is fluid (see Layout), so 279×1424/1440 works out to within a
pixel of 276. Two independent instruments agreeing on a continuously-scaling
value, not a discrepancy.

Mobile is a **discrete second scale, not a vw-shrink of the desktop one**: the
56.7px headline tier becomes 62.6526px at breakpoint 768 and 31.82px at
breakpoint 390, larger
proportionally at 768 than a straight scale from 1440 would predict, because
768 crosses into a different unit reference frame entirely (see Layout).

## Layout: one fluid design-unit, three explicit tiers, no rem involved

Everything is built on a single custom property, `--u`, declared three times
with cascading media conditions (`mediaConditions` is byte-identical at all
three captured widths, so this is the complete breakpoint inventory, not a
partial view):

```css
--u: calc(100vw / 1600);              /* default, 900px–1900px viewport */
@media (min-width: 1900px) { --u: calc(1900px / 1600); }   /* fixed above 1900 */
@media (max-width: 900px)  { --u: calc(100vw / 760); }     /* narrower reference frame */
```

Root font-size is untouched. This is **not** a rem driver like landonorris's
(`--fluid-font` scaling the root, so `rem` carries the scale). Every value
here is an explicit `calc(N * var(--u))` multiplying a literal design-unit
into whatever property needs it. Verified: `--u` = 0.9 at 1440 (1440÷1600),
1.0105 at 768 (768÷760; 768 is already inside the narrow tier), 0.5132 at 390
(390÷760). Dividing each breakpoint's own smallest measured gap by its own
`--u` reproduces the same integer design-unit at all three widths (7.2px @1440
÷0.9, 8.08421px @768 ÷1.0105, 4.10526px @390 ÷0.5132 all land on the same
whole number), confirming one arithmetic system drives every breakpoint rather
than three independently-tuned sets of pixels.

The only two real `@media` conditions besides `prefers-reduced-motion` are
**`(max-width: 900px)`** and **`(min-width: 1900px)`**: nothing at 809.98,
1199.98, 767.98, or any other Framer-family edge. A hand-built site with its
own breakpoint arithmetic, not a template's.

Gap ladder (top values, px, by frequency): 1440 → 7.2 (5), 8.1 (2), 2.7 (1),
10.8 (1). 768 → 8.08421 (5), 11.1158 (2), 4.04211 (1), 12.1263 (1). 390 →
4.10526 (5), 5.64474 (2), 4 (1), 6.15789 (1).

Radius ladder (px, by frequency): 1440 → 9 (5), 50% (3), 41.4 (2), 30.6 (2),
12.6 (1). 768 → 13.1368 (5), 40.4211 (2), 34.3579 (2), 50% (2), 18.1895 (1).
390 → 12 (5), 20.5263 (2), 17.4474 (2), 50% (2), 17 (1).

Structure (document order, one screen, no scroll): a full-bleed `canvas#scene`
(the WebGL scene) → a nav dock (5 items) → 3 decorative vertical guide lines →
a large background wordmark glyph → an "about" card with an image-reveal
figure → a floating round icon button → a two-line headline → a lede
paragraph → a primary CTA (sandboxed iframe) → a secondary play CTA (sandboxed
iframe) → two `dl` stat blocks → a second content card → a scroll-cue link
with a looping track glyph.

## Colour: an achromatic dark-moss + cream system, zero saturated accent

Every distinct swatch the capture found, across all three breakpoints (16
total, identical set at each width; colour does not change with viewport):

`#000000` `#0a0e08` `#0c1109` `#10150d` `#1c2216` `#22281f` `#23261f` `#263025`
`#383b34` `#3f453a` `#4a4d44` `#7c8177` `#eef1e7` `#f2f3ef` `#fbfcf8` `#ffffff`

**Not one of the 16 is a saturated hue.** Every value is either a near-black
mossy green/graphite, a warm cream/off-white, or a pure endpoint (`#000`/
`#fff`). This is a harder version of polestar's "no brand accent in the UI at
all". Polestar still has two saturated status colours hidden in a chat
widget; here there is nothing anywhere in the captured palette that isn't
achromatic-to-olive. The colour comes from the WebGL scene and the two
photographic card thumbnails, not from any UI chrome.

Named tokens (`customProperties`, verbatim), three of which (`--card-ink`,
`--card-label`, `--card`) show up unchanged in the sampled census below,
confirming they are actually consumed and not just declared:

```css
--ink: #ffffff;
--ink-soft:  rgba(255,255,255,.62);
--ink-faint: rgba(255,255,255,.44);
--rule:      rgba(255,255,255,.055);
--card:      #f2f3ef;
--card-ink:  #23261f;
--card-label:#7c8177;
```

Text colours (1440, count): `#ffffff` (47) · `rgba(255,255,255,.34)` (17) ·
`#23261f` (13, = `--card-ink`) · `rgba(255,255,255,.44)` (13, = `--ink-faint`)
· `#3f453a` (8) · `#000000` (3) · `rgba(255,255,255,.62)` (3, = `--ink-soft`)
· `#7c8177` (2, = `--card-label`) · `rgba(255,255,255,.5)` (2) ·
`rgba(255,255,255,.055)` (1, = `--rule`, used as a text colour too: a
divider glyph, not only a border).

Backgrounds (1440, count): `#f2f3ef` (3, = `--card`) · `#383b34` (2) ·
`rgba(255,255,255,.04)` (2) · `#263025` (2) · `#fbfcf8` (2) · `#4a4d44` (1) ·
`rgba(34,40,31,.74)` (1) · `#eef1e7` (1) · `rgba(255,255,255,.075)` (1) ·
`rgba(255,255,255,.18)` (1).

**The white-alpha-on-dark pattern is present, at finer resolution than
elsewhere in the library.** The measured ramp, `.04 / .055 / .075 / .18 /
.34 / .44 / .5 / .62`, is eight distinct steps against youtube's three
(8/10/20%) and onefin's five (5/20/40/60/80%). One wrinkle worth flagging
honestly: the "dark" surface here is a WebGL canvas render, not a DOM
`background-color`, so a plain background census under-reports it. The
near-black end of the ramp only shows up by reading the `--ink*` custom
properties, not by sampling `background` on real elements.

Shadows (1440): `rgba(16,21,13,.3) 0 27px 63px` (2) · `rgba(16,21,13,.18) 0
5.4px 14.4px` (2) · `rgba(10,14,8,.3) 0 7.2px 19.8px, rgba(255,255,255,.06) 0
1px 0 inset` (1) · `rgba(12,17,9,.24) 0 5.4px 14.4px` (1). All four shadow
tints are in the same 16-swatch dark-moss family; even elevation is
colour-disciplined.

## Motion

**Motion fidelity: spec**

Measured via `motion-extract.js` pre-injected before load (`cdp-run.py --pre`),
14 scroll steps, `--settle 4`. **28 animations total, 0 zero-duration
dropped, 0 scroll-triggered**. Every one of the 28 fires at
`firedAtScrollY: 0`, verified as a genuine property of the page (there is no
scroll surface to trigger from; see the header note) rather than a capture
miss. This is a complete capture, not a partial one: the whole site is these
28 animations plus one always-running ticker, and all of them fire once,
keyed by an explicit delay after page load (a curtain-rise sequence, not a
scroll-reveal gate).

**Two named CSS custom properties carry the entire curve vocabulary**:

```css
--ease:     cubic-bezier(.22, .61, .36, 1);   /* 6 of 28 firings */
--ease-out: cubic-bezier(.16, 1, .3, 1);      /* 17 of 28 firings — the signature */
```

Plus the bare keyword `ease` (3 firings: the three zero-duration
orchestration markers below) and `steps(12)` (2 firings: the two portal-cut
image reveals). 17+6+3+2 = 28, exact.

Duration classes by firing count: 1050ms (9) · 900ms (5) · 0ms (3) · 1100ms
(3) · 1250ms (2) · 1300ms (2) · 1450ms (2) · 450ms (1) · 800ms (1).

**Character**: everything is `clip-path` or `opacity`. The single exception,
the only `transform`/translate on the whole page, is a 14.24px `translateY`
on the two headline lines, paired with their own opacity fade and finishing
200ms after it. No scale, no rotate, no other translate anywhere in the
capture. `prefers-reduced-motion` has a media condition declared in the CSS;
the capture ran with reduce off, so what it disables is unverified.

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| Canvas fade-in (1) | `canvas#scene` | load, delay 0ms | `opacity 0→1` | 450ms | `--ease` | - | N/A, no scroll |
| Dock fade-in (1) | `nav.dock` container | load, delay 80ms | `opacity 0→1` | 800ms | `--ease` | - | N/A |
| Dock-item reveal (5) | 5 dock nav items (logo + 4 links) | load, delays 120/180/230/280/330ms | `clip-path inset(0 0 105%)→inset(0 0 -30%)` | 900ms | `--ease-out` | 60/50/50/50ms | N/A |
| Panel reveal group (4) | lede paragraph, 2 stat blocks, scroll-cue link | load, delays 480/700/770/1040ms | `clip-path inset(100% 0 0)→inset(0)` | 1050ms | `--ease-out` | 220/70/270ms (irregular, hand-timed) | N/A |
| Pill-badge reveal (1) | primary CTA pill mask | load, delay 600ms | `clip-path inset(100% 0 0 round 133.5px)→inset(0 round 133.5px)` | 1050ms | `--ease-out` | - | N/A |
| Card reveal (2) | the two content cards | load, delays 760/880ms | `clip-path inset(100% 0 0 round 40.94px)→inset(0 round 40.94px)` | 1050ms | `--ease-out` | 120ms | N/A |
| Circular iris reveal (3) | float-icon knob, play-glass, play-ring | load, delays 840/900/1100ms | `clip-path circle(0% at 50% 50%)→circle(76% at 50% 50%)` | 1100ms | `--ease-out` | 60/200ms | N/A |
| Headline opacity (2) | the 2 headline lines | load, delays 260/360ms | `opacity 0→1` | 1050ms | `--ease` | 100ms | N/A |
| Headline rise (2) | same 2 headline lines | load, delays 260/360ms (paired with row above) | `transform translateY(14.24px)→none` | 1250ms | `--ease-out` | 100ms | N/A |
| Watermark + guide fade (2) | background wordmark glyph, decorative guide lines | load, delays 900/1150ms | `opacity 0→1` | 1300ms | `--ease` | 250ms | N/A |
| Portal-cut image wipe (2) | the 2 card thumbnail media layers | load, delays 920/1080ms | `clip-path inset(0 100% 0 0 round Nu)→inset(0 0 0 0 round Nu)` | 1450ms | `steps(12)` | 160ms | N/A |
| Orchestration markers (3) | scroll-track glyph + 2 portal-scan starts | load, delay 0ms | zero-duration: class-toggle hooks, not visible tweens | 0ms | `ease` | - | N/A |

That is all 28: 1+1+5+4+1+2+3+2+2+2+2+3 = 28.

**One genuinely infinite animation exists and it is not in the table above**:
a `@keyframes trickle` on the scroll-cue's track glyph (`translateY(-105%)
→translateY(255%)`, opacity ramping in at 22% and out at 78%), running
**2600ms, linear, `iterations: Infinity`, `playState: running`** per the
live-animation read. The per-animation extractor's own listing for this same
element instead shows it as one of the three zero-duration "orchestration
marker" rows above. Cross-checking against the live-animation state is what
catches this; trusting the zero-duration bucket alone would mean concluding
the only permanently-moving element on the page has no motion.

## Interaction states

```css
.card:hover .portal-media img       { transform: scale(1.13); filter: saturate(1.04) contrast(1.04); }
.card .knob:hover, .knob--about:hover { transform: scale(1.1) rotate(8deg); background: #fff; }
.card:hover                         { box-shadow: 0 calc(38*var(--u)) calc(84*var(--u)) rgba(16,21,13,.36); }
a:focus-visible, button:focus-visible { outline: rgba(255,255,255,.85) solid 2px; outline-offset: calc(4*var(--u)); border-radius: calc(6*var(--u)); }
.card .knob:focus-visible, .knob--about:focus-visible, .play:focus-visible { outline-color: rgba(28,34,22,.9); }
```

At 1440 (`--u`=0.9) the card hover shadow resolves to `0 34.2px 75.6px`; the
focus ring offset/radius resolve to 3.6px/5.4px. Five rules total, identical
at every breakpoint; this is the complete CSS interaction surface.

**The two CTAs are outside this system entirely.** Both are sandboxed
`<iframe sandbox="allow-scripts">` elements (`liquid-metal-explore.html`,
`liquid-metal-play.html`) with no origin, so the parent page receives no
`:hover`/pointer events while the cursor sits over them, confirmed directly
in the page's own source, which fakes hover with geometric band-testing
(`nearPlay(x, y)`) against the iframe's last-known bounding rect rather than
a real CSS or JS hover callback.

**The nav dock's magnification is inline-style JS, not CSS.** Each dock item
carries a live-computed `width/height/transform` in its `style` attribute,
driven by a macOS-dock-style proximity/spring loop in the shared rAF tick,
plus a rotating cursor-tracking rim-light. It is explicitly gated off for
coarse/touch pointers (a `fineHover()` check against `(hover:hover) and
(pointer:fine)`) with a separate keyboard-focus code path. Reading the
`interactionRules` CSS census alone would miss this whole mechanism.

## Structural patterns worth naming

- **Single fluid design-unit, discrete per-tier formula, not a continuous
  clamp.** landonorris drives its whole scale from one `clamp()`-based root
  font-size formula that interpolates continuously between two widths. Sylva
  instead declares `--u` three separate times behind three `@media`
  conditions: a fixed value above 1900px, one formula between 900–1900px,
  and a *different* reference frame (÷760 instead of ÷1600) below 900px. Same
  idea (one design-unit constant driving every measurement, pinned to a
  design width) executed as discrete tiers rather than one continuous curve,
  and via `calc()` multiplication rather than the root font-size/`rem`
  mechanism landonorris uses. See the INDEX cross-site note.
- **`pixel-reveal` canvas synced to a CSS clip-path wipe.** Each card carries
  a `canvas.pixel-reveal` that samples the underlying `<img>` into a coarse
  colour grid and paints a stepped dot-front timed against the `portal-cut`/
  `portal-scan` reveal; the canvas exists only for that one entrance and
  stops painting once it settles. The two effects (CSS clip-path, canvas
  paint) must share duration/easing or they visibly desync; this is not
  documented as a shared mechanism anywhere else in the library yet.
- **Procedural WebGL scene, not photography.** Per the script's own header
  comment, the moss/root/grass scene is tapered-tube geometry with
  shader-based bark/moss materials, instanced grass blades ("instanced a
  hundred thousand times" per an in-code comment), recursive offshoot
  branches, fern meshes, a drifting-pollen particle system, and a separate
  cursor-reactive butterfly (baked wing pattern, spring-based flee/perch/
  flight states keyed off a `SPOOK_R = 0.62` proximity radius). Only
  `three.js r149` was confirmed as a loaded library: no GSAP, no Framer
  Motion, no scroll library of any kind.

## Gotchas hit while capturing

1. **A sandboxed `allow-scripts` iframe with no origin gets no parent
   `:hover`/pointer events at all.** Symptom: a CTA that visually responds to
   the cursor with no corresponding CSS or JS event handler reachable from
   outside the frame. Root cause: `sandbox="allow-scripts"` with no
   `allow-same-origin` blocks cross-frame event delivery by design. Fix (as
   the source itself does it): track the last known pointer position in the
   parent document and geometrically test it against the iframe's own
   `getBoundingClientRect()`. This is measurable and reproducible without
   needing frame access. Verify by moving the pointer across the CTA boundary
   and watching the hover state update with the parent's own logic, not the
   frame's.
2. **A live-animation read and a per-animation-transition read can disagree
   about the same element**, and the disagreement itself is the signal. The
   scroll-track glyph's `trickle` keyframe reports `duration: 2600, iterations:
   Infinity, playState: running` from one instrument and `duration: 0` from
   the other. Do not pick one arbitrarily; cross-check both, and treat any
   element the live-animation read calls "running" as real motion regardless
   of what the transition-firing table says about it.
3. **The whole layout scale lives behind three separately-declared `--u`
   custom properties, not one formula**. Reading only the default-tier
   declaration and assuming it holds below 900px (or above 1900px) will
   silently produce wrong values at those breakpoints. Read all matches of
   the same custom-property name across `mediaConditions`, never just the
   first one found.
4. **`document.documentElement.scrollHeight === window.innerHeight` is a
   real, checkable signal that a "scroll capture" will legitimately return
   zero scroll-triggered animations**, confirmed independently at three
   different viewport sizes before trusting the 0-scroll-triggered result
   rather than treating it as a capture failure.

## What this entry is good for

The **named two-curve easing token system** (`--ease` /
`--ease-out`, mapped 1:1 to every firing in the spec table above), the
**achromatic dark-moss-and-cream palette with a zero-accent discipline**, and
the **discrete-tier fluid design-unit** are all directly reusable. It is a
poor donor for anything requiring a second page or a scroll-driven reveal;
there is only one screen and nothing on it scrolls.

## Verification achieved

Capture-only (Audit): no mirror was built and there is no pixel-diff number
for this entry. Structural extraction covered all 3 swept breakpoints (390 /
768 / 1440, `sampledElementCount` 111 at each, 0 blocked stylesheets),
`fonts-1440.json` proved the display face by canvas-width A/B at 4 size/weight
combinations, and `motion-1440.json` accounted for 28/28 animations with no
zero-duration drops. Not independently verified: the exact spring constants
of the cursor-reactive butterfly and the dock's magnification curve (both
confirmed present and gated correctly in source, but not measured live frame
by frame), and the shader/material recipe of the WebGL scene beyond what the
script's own comments describe. No further pages exist to capture: the nav
items are inert `href="#"` and the site is confirmed single-screen at every
tested viewport.
