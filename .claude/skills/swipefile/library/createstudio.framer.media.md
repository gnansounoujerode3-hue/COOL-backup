# createstudio.framer.media

**Callable as: CreateStudio** (aliases: create studio, createstudio)

Captured 2026-07-30. Design-studio portfolio site, a Framer template showcase.
Path taken: **mirror (scripted)**. Confirms the standing Framer prior, the raw
HTML is fully server-rendered (2.7MB, all 39,803 characters of text present), but
adds an important qualifier: Framer *renders* the markup server-side and then
*hides* most of it, revealing it through its own runtime. Server-rendered does
not mean script-independent.

## Stack

Framer. One `script_main.*.mjs` entry that pulls ~75 ES-module chunks (rolldown
output: react, motion, framer, plus one chunk per component), 13 `.framercms`
CMS data chunks, and `type="framer/appear"` JSON payloads that define entrance
animations.

- **No CSS easing at all.** A `cubic-bezier` tally across every readable
  stylesheet returns **zero**. All motion runs through the bundled Motion
  library in JS. Do not go looking for a CSS motion signature on a Framer site;
  read the appear-animation payloads instead.
- Root font-size is a plain **16px**: no fluid rem driver.
- `@font-face` lives in **inline `<style>` blocks** (1540 occurrences across 191
  blocks on this site), not a linked stylesheet. Confirms the standing pattern.

## Tokens

Framer names colour tokens by UUID (`--token-2a8eec97-…`), so the names carry no
meaning and the values are the system. 16 tokens, and the palette is a
near-monochrome stack with a single hot accent:

- accent `#ff6041` (orange-red), the only chromatic value in the entire palette
- darks `#000` · `#050609` · `#141414`
- lights `#fff` · `#fafafa` · `#f2f2f2` · `#ebebeb` · `#d9d9d9` · `#d5d7de`
- greys `#5c6063` · `#797d82` · `#888d92`

That is the whole idea of the design: one saturated accent against a greyscale
ramp, with photography carrying all the remaining colour. Worth stealing.

Type: Figtree (display/UI), Inter (body), Fragment Mono (all the small
uppercase metadata: timestamps, section numbers, captions). Framer also
registers "Figtree Placeholder" / "Inter Placeholder" metric-compatible faces to
prevent layout shift before the real font loads; they show up in
`document.fonts` and are not a mirroring error.

## Breakpoints

`0–809` · `810–1199` · `1200+`. Framer's standard three-tier ladder, emitted as
`(max-width: 809.98px)` / `(min-width: 810px) and (max-width: 1199.98px)`. The
`.98` fractional edges are Framer's, not a rounding artifact.

## Structural pattern: SSR variants

Framer emits **every breakpoint variant** into the server-rendered HTML and
switches them with `display: contents` vs `display: none` on `div.ssr-variant`
wrappers. Consequence when diffing: the un-hydrated DOM has roughly **2× the
node count** of the hydrated one (13,228 vs 7,042 here). A doubled node count is
a symptom of hydration not completing, not of a broken mirror.

## Motion

**Motion fidelity: spec**

Measured 2026-07-31 @ 1440×813, headless Chrome CDP, hooks installed before load,
14 scroll steps over a 28,476px page. **1427 animations, 0 zero-duration rows
dropped, 1339 scroll-triggered.** Both `framer/appear` payloads were read this
time, the read the previous entry said to do and never did. Between the runtime
capture (what actually fired, with ladders and offsets) and the payloads (the
authored from-states, springs and delays), the motion system is reconstructable
without re-capturing.

Scope of that claim, stated plainly: the mapping is **per group and per authored
recipe, not per named section**. Framer's class names are content hashes, so a
row identifies "the 800ms opacity ladder on split-text spans", not "the pricing
headline". Assign recipes to sections by matching the trigger offset and the
delay ladder, and the result will read correctly; it will not be provably the
same assignment element for element.

Easing by use count:

| Curve | Uses | Note |
|---|---|---|
| `linear(baked spring, 80 stops)` | 1095 | signature: Motion's baked spring, not a hand curve |
| `linear(baked spring, 40 stops)` | 122 | same spring, 400ms |
| `ease-in-out` | 77 | CSS keyword, interaction only |
| `cubic-bezier(0.48, 0, 0.17, 0.96)` | 68 | hero character reveal |
| `linear(baked spring, 20 stops)` | 28 | same spring, 200ms |
| `cubic-bezier(0.44, 0, 0.13, 0.96)` | 26 | stat and pricing word reveals |
| `linear` | 8 | ambient loops and baked transforms |
| `cubic-bezier(0.05, 0.88, 0.56, 1)` | 3 | one late deep-page reveal |

`linear(baked spring, N stops)` is **Motion's baked-spring serialisation**: a
spring integrated and emitted as a `linear()` stop list, at a constant **one stop
per 10ms** of duration (80/800ms, 40/400ms, 20/200ms). Do not read those as
authored curves and do not approximate them with a bezier; the authored
parameters are in the appear payloads below (`type: "spring"`, `bounce: 0.2`).
Two of the authored beziers have a control point outside 0–1,
`(0, 1.2, 0.56, 1)` and `(0.55, 0.58, 0.34, 1.04)`, i.e. deliberate overshoot,
which is why the site feels springy even where it is technically a tween.

Durations by frequency: 800ms ×1095 · 400 ×123 · 200 ×106 · 1000 ×71 · 600 ×20 ·
900 ×6 · 4000 ×2 · 24000 ×1 · 45340 ×1 · 83840 ×1 (and, from the full capture,
167133 ×1). Everything ≥24000ms is an **ambient loop**, never a reveal.

Trigger-offset histogram (viewport % at fire, count): 69→178 · 77→123 · 64→122 ·
73→120 · 59→114 · 54→111 · 49→104 · 74→75 · 3→68 · 24→66 · 61→34 · 96→31. The
reveal band is **49–77%**, with 69% the mode and the median of the dominant group.
The 3% spike is the hero firing at load, not on scroll.

Character: almost nothing translates. 1095 of 1427 firings are a bare
`opacity 0.001 → 1` over 800ms, Framer's `0.001` rather than `0`, which keeps the
element composited and measurable. Travel lives in the appear payloads, is
overwhelmingly vertical, and is small at the leaf level (y 20–40px) and large only
on whole blocks (y 140px, x −240px). The house rhythm is a **split-text ladder**:
text is broken into per-word or per-character spans and released on a stagger
(3ms for the hero's character sweep, 50ms for the blur-in paragraphs, 75/100/125ms
for the main body ladder, 15ms and 20ms for stat and pricing words).

`prefers-reduced-motion`: **no media query present anywhere in the page CSS.**
1427 animations, including scroll reveals and four infinite tickers, with no
reduced-motion branch. This is a defect to fix in a rebuild, not a pattern to
copy.

### Runtime spec: what actually fired

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| Body split-text ladder (1095) | `p.framer-text > span > span` across the page | scroll | `opacity 0.001` → `1` | 800ms | `linear(baked spring, 80 stops)` | 75 / 100 / 125ms; delays 0, 75, 200, 300, 400, 500, 600 | START 49–105%, mode 69%; no scrub |
| Button icon fade (77) | `button > div[class*=-container] > div` | hover / state, not scroll | `opacity 0` → `1` | 200ms | ease-in-out | none | none: interaction state |
| Hero character sweep (68) | `p.framer-styles-preset-1yf9dob > span > span` (per character) | load | `opacity 0.001` → `1` | 1000ms | `cubic-bezier(0.48, 0, 0.17, 0.96)` | **3ms**; delays 0→33 in 3ms steps | START 3%: fires at load |
| Paragraph blur-in, blur track (61) | `p.framer-styles-preset-1kdkkta > span > span` (per character) | scroll | `blur(10px)` → `blur(0px)` | 400ms | `linear(baked spring, 40 stops)` | **50ms**; delays 100→650 | START 24–69%, mode 24%; no scrub |
| Paragraph blur-in, opacity track (61) | same elements, same tick | scroll | `opacity 0.001` → `1` | 400ms | `linear(baked spring, 40 stops)` | 50ms; delays 100→650 | START 24–69%; no scrub |
| Small-caps ladder (28) | `p.framer-styles-preset-d7xix7 > span > span` | scroll | `opacity 0.001` → `1` | 200ms | `linear(baked spring, 20 stops)` | 100 / 200ms; delays 1200→2400 | START 12–21%; no scrub |
| Stat word reveal (20) | `.framer-19v92ce > p > span` (whole words) | scroll | `opacity 0.001` → `1` | 600ms | `cubic-bezier(0.44, 0, 0.13, 0.96)` | **15ms** within a group, 525ms between groups; delays 200–275 then 800–845 | START 14–89%, median 49%; no scrub |
| Pricing word reveal (6) | `.framer-dzda04 / .framer-kriw1r > p > span` | scroll | `opacity 0.001` → `1` | 900ms | `cubic-bezier(0.44, 0, 0.13, 0.96)` | 20ms; delays 200, 220 | START 27–101%; no scrub |
| Deep-page block lift, transform (1) | `.framer-13wwho4` | scroll | `translateY(140px)` → `none` | 1000ms | `cubic-bezier(0.05, 0.88, 0.56, 1)` | none | START 3498% (far below fold); delay **4000ms** |
| Deep-page block lift, opacity (2) | same element | scroll | `opacity 0.001` → `1` | 1000ms | `cubic-bezier(0.05, 0.88, 0.56, 1)` | none | START 3498%; delay 4000ms |
| Slow footer reveal, opacity (1) | `.framer-120s37d-container` | scroll | `opacity 0.001` → `1` | 4000ms | linear (401 baked stops) | none | START 2026%; delay 600ms |
| Slow footer reveal, transform (1) | same element | scroll | endpoints read as `none` → `none` | 4000ms | linear (401 baked stops) | none | START 2026%; delay 600ms |
| Nav transform (1) | `.framer-n8qde0-container` | load | endpoints read as `none` → `none` | 200ms | linear (21 baked stops) | none | START 0%; delay 1300ms |
| Eyebrow transform (1) | `.framer-16m2tn2` ("A DESIGN STUDIO TRUSTED BY…") | scroll | endpoints read as `none` → `none` | 400ms | linear (41 baked stops) | none | START 65%; delay 700ms |
| Vertical ticker (1) | `.framer-19nythf-container > section > ul` | load | `translateY(0)` → `translateY(-480px)` | 24000ms, infinite | linear | none | none: ambient loop; at 23% |
| Horizontal ticker A (1) | `.framer-ht9onv-container > section > ul` | load | `translateX(0)` → `translateX(-2267px)` | 45340ms, infinite | linear | none | none: ambient loop; at 1010% |
| Horizontal ticker B (1) | same container, second track | load | `translateX(0)` → `translateX(-5014px)` | 167133ms, infinite | linear | none | none: ambient loop; at 2787% |
| Testimonial ticker (1) | `.framer-4x2apm-container > section > ul` | load | `translateX(0)` → `translateX(-4192px)` | 83840ms, infinite | linear | none | none: ambient loop; at 2799% |

Ticker speeds, which is the transferable number: **50px/s** for both the 45340ms
and 83840ms rows, **30px/s** for the 167133ms row, **20px/s** for the vertical
24000ms one. Duration is track length ÷ speed; copy the speed.

Four rows record `transform: none → none`. That is a capture limit, not a
no-op; they are baked-spring transforms whose computed value was sampled outside
the animating window. Their travel is in the payload table below.

### Authored source: the two `framer/appear` payloads

65 element hashes, **115 breakpoint-specific variants, 28 distinct recipes**.
Framer authors motion **per breakpoint**: the second payload is the hash→media
map. `197f1xr` and `159vcat` = `(min-width: 1200px)`, `th3w5` and `np8a8r` =
`(min-width: 810px) and (max-width: 1199.98px)`, `1ehmg2z` and `1byf3s2` =
`(max-width: 809.98px)`. A `null` variant means that breakpoint has no entrance
animation at all.

| Uses | From (initial) | Transition | Delay |
|---|---|---|---|
| 20 | `opacity 1, x −100` | tween 1000ms `(0.55, 0.58, 0.34, 1.04)` | 0 |
| 18 | `opacity 0.001, y 40` | spring 1000ms, bounce 0.2 | 200ms |
| 15 | `opacity 0.001` | spring 1000ms, bounce 0.2 | 400ms |
| 6 | `opacity 0.001, scale 1.14` | tween 500ms `(0.68, 0, 0.16, 0.97)` | 0 |
| 4 | `opacity 1, x −30` | tween 1000ms `(0.55, 0.58, 0.34, 1.04)` | 0 |
| 4 | `opacity 1, x 85` | tween 1000ms `(0.55, 0.58, 0.34, 1.04)` | 0 |
| 4 | `opacity 0.001` | spring 400ms, bounce 0.2 | 0 |
| 4 | `opacity 0.001` | tween 600ms `(0, 1.2, 0.56, 1)` | 800ms |
| 3 | `opacity 0.001, y 80` | tween 2000ms `(0, 1.2, 0.56, 1)` | 1000ms |
| 3 | `opacity 0.001, y −20` | spring 1000ms, bounce 0.2 | 300ms |
| 3 | `opacity 0.001, y 140` | spring, no duration set | 300ms |
| 3 | `opacity 0.001, y 140` | spring, no duration set | 500ms |
| 3 | `opacity 0.001, y 20` | spring 2000ms, bounce 0.2 | 2000ms |
| 3 | `opacity 0.001, y −60` | spring 1000ms, bounce 0.2 | 400ms |
| 3 | `opacity 1, y 40` | tween 1000ms `(0, 1.2, 0.56, 1)` | 600ms |
| 3 | `opacity 0.001` | tween 600ms `(0, 1.2, 0.56, 1)` | 1000ms |
| 2 | `opacity 0.001, y −48` | tween 1000ms `(0.29, 0.84, 0.56, 1)` | 500ms |
| 2 | `opacity 1, x −160` | tween 1000ms `(0.55, 0.58, 0.34, 1.04)` | 0 |

Ten further recipes appear once each, all within the same vocabulary; the widest
outliers are `x −240` (tween 1000ms `(0.32, 0.43, 0.22, 1)`, delay 1000ms),
`y 140` (tween 1000ms `(0.05, 0.88, 0.56, 1)`, delay **4000ms**) and
`y 40, scale 1.3` (tween 1000ms `(0.68, 0, 0.2, 0.89)`). Every recipe animates to
the same end state: `opacity 1, x 0, y 0, scale 1, rotate 0, skew 0`. No recipe
rotates or skews anything; all 115 variants carry `rotate/rotateX/rotateY/skewX/
skewY: 0` at both ends.

Trigger caveat for every scroll offset above: the capture scrolls in 14 jumps of
~2034px against an 813px viewport, so each step overshoots by ~2.5 viewports and
an element can already be up the screen before its reveal is observed. An
observed offset is a **lower bound on how early the reveal fires**; the true
threshold sits at or above the top of each range. For the dominant ladder that
is ~105%, i.e. the reveal starts as the element crosses the fold.

What does not move: no rotation, no skew, no scale beyond two isolated recipes
(1.14 and 1.3), and no scrubbed motion at all. Every scroll animation is a
one-shot with a fixed duration, so nothing tracks scroll position. Navigation,
buttons and cards have no entrance animation of their own; they inherit the
ladder of the block they sit in. The only continuous motion on the page is the
four tickers.

## Gotchas: all four are Framer-general, not site-specific

1. **`new URL(rel, base)` bases must stay absolute.** CMS collections resolve
   their data with
   `new URL('./X.framercms', 'https://framerusercontent.com/modules/A/B')`.
   Rewrite that *second* argument to a relative path and the constructor throws
   `TypeError: Failed to construct 'URL': Invalid base URL`. The uncaught error
   kills the whole render, and the failure mode is deceptive: images and layout
   boxes paint normally while **all text is missing** and every count-up and
   clock sits at its initial value. It reads like a font or CSS problem and is
   neither. Fix: these bases sit inside template literals, so injecting
   `${location.origin}` keeps them absolute with no hardcoded port.
2. **Root-absolute, not `./`, when rewriting inside module bodies.** A URL in a
   module body is used two ways: as an import specifier (resolved against the
   *module*) and as a DOM `src` assigned at runtime (resolved against the
   *document*). `./x.svg` is correct for the first and 404s at the site root for
   the second. `/cdn/x.svg` is correct for both.
3. **Relative dynamic imports are invisible to a host-based URL scan.** Framer
   chunks reference each other as `import('./X.mjs')`. Resolve relative
   specifiers against each module's own origin URL and iterate, or you ship a
   404 plus an uncaught "Failed to fetch dynamically imported module".
4. **`.framercms` is a real asset extension.** Not in any default list.

Two smaller ones: Framer's editor bootstrap (`framer.com/edit/init.mjs`) and its
analytics beacon must be *removed*, not pointed at `about:blank`; a script
element with an `about:` src raises `ERR_UNKNOWN_URL_SCHEME` and clutters the
console while you are trying to diagnose. And the `__framer_events` /
`__framer_editorBarDependencies` globals come from those very scripts, so their
absence on a mirror is expected and is **not** evidence that the runtime failed.

## What was achieved

20 pages (the full sitemap bar one URL-encoded duplicate), 333 assets plus 13 CMS
chunks, 87MB. Fonts verified by canvas A/B. Zero live external references across
all 40 built pages.

Static variant 73.38% vs scripted 98.52% on the homepage, the widest
static/scripted gap in the library so far, and the clearest demonstration that a
server-rendered page can still be script-dependent.

Homepage scores against a **97.95%** ceiling rather than 100%: the hero embeds an
autoplaying showreel, a live clock and a count-up, so the reference is not
identical to itself across loads. Static pages measure at ceiling (work 99.90% of
100.00%, studio 99.78% of 100.00%).

Residual: three hero elements driven by client effects (header logo opacity, the
count-up, the clock) do not reach the reference's state, because serving Framer's
markup as static HTML rather than through its edge renderer produces a
*recoverable* hydration mismatch and those effects do not re-run.
