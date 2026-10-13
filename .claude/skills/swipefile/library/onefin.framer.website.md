# onefin.framer.website

**Callable as: OneFin** (aliases: onefin, onefin framer)

Fintech SaaS marketing template: dark UI, indigo accent, condensed-heavy
display type. Captured 2026-07-30 @ 1280×900 (breakpoints swept 390–1920).
Stack: Framer (`Framer 1a21bd5`), server-rendered and script-dependent.
**Mirror path, scripted variant.**

Third Framer capture in the library. The hardened build from
[createstudio](createstudio.framer.media.md) and [osa](osa.framer.website.md)
carried over intact, but this site exposed **four defects the first two never
surfaced**, three of which are framework-independent and belong to any CDN-backed
mirror. See Gotchas; they are the value of this entry.

## Type: one condensed heavy grotesque, one geometric sans, nothing else

Root font-size a flat **16px**, no fluid driver (third Framer confirmation).
Census by frequency off the rendered homepage:

| count | size / weight / family | role |
|---|---|---|
| 183 | **72px 900 Roboto Condensed** | display: the site's whole voice |
| 93 | 20px 500 Geist | lead paragraph / card title |
| 49 | 14px 400 Geist | body small, metadata |
| 40 | 16px 400 Geist | body |
| 29 | 56px 400 Geist | section headings |
| 18 | 14px 900 Roboto Condensed | eyebrow / label, uppercase |
| 16 | 16px 600 Geist | button, nav |
| 12 | 18px 600 Geist | subhead |
| 7 | **128px 900 Roboto Condensed** | hero display |
| 6 | 48px 900 Roboto Condensed | secondary display |

The system: **Roboto Condensed at weight 900 only, and only at display sizes
(48/72/128px) plus a 14px uppercase label**. Geist carries the entire interface
across 14/16/18/20/24/56 at weights 400/500/600. Two families, two jobs, no
overlap.

This is the same *architecture* the library already recorded on osa (display
face reserved for display sizes, geometric sans doing all interface work) with a
different casting, a condensed heavy grotesque instead of a high-contrast
serif. The rule generalises past serifs: it is about reserving one voice for
display, not about which voice.

Also loaded: Inter and Fragment Mono, both declared in fallback stacks but
**not loaded on the homepage**; `document.fonts.check()` returns false for both
on the reference itself. 67 faces total in `document.fonts`.

## Layout

- Design width **1440**; content container **1200px**, wide boxes at 1184/1280.
- Breakpoints `0–809` / `810–1199` / `1200+`: Framer's standard three-tier
  ladder. **New:** this site emits *both* integer edges (`max-width:809px`,
  `max-width:1199px`, 145 uses each) and the `.98` fractional edges
  (`max-width:809.98px`, 50 uses). The library's "Framer always uses `.98`"
  note is therefore too strong: `.98` marks the generated variant switches,
  integers appear alongside them. Do not treat a missing `.98` as evidence the
  site is not Framer.
- Inner measures 480 / 580 / 720 / 824 / 858 / 900 / 1000 / 1120 / 1160 / 1344.
- Spacing ladder by use count: **10** (58), 8 (45), 16 (27), 24 (20), 32 (17),
  12 (14), 64 (12), 40 (11), 48 (10), 4 (8). An 8px base with a 10px gutter
  used more than any other single value.
- Radius: **0px dominant** (32 uses), then 48 (11), 8 (7), 80 (3), 12 (3), and
  single uses of 32/40/56/64/72. Squared-off by default with fully-rounded pills
  for buttons and chips, not a uniform radius token.

## Colour

20 UUID-named tokens (Framer names carry nothing; the values are the system).
Body background `#121214`.

- **Indigo ramp, five steps:** `#28119c` → `#381ac9` → **`#6262fe`** (primary) →
  `#9696ff` → `#bebeff`. One hue family doing shadow, base, accent, and tint.
- **Near-black ramp:** `#121214` · `#1b1b1f` · `#212124` · `#292929`, four
  values inside 23 levels of each other, which is what makes the dark surfaces
  read as layered rather than flat.
- **Greys:** `#525252` · `#8f8f8f`. **Lights:** `#d9d9d9` · `#efefef` ·
  `#f5f5f5` · `#fff`.
- **White-alpha ramp:** `#ffffff0d` (5%) · `#fff3` (20%) · `#fff6` (40%) ·
  `#fff9` (60%) · `#fffc` (80%).

The alpha ramp is the reusable part and confirms the standing cross-site
pattern for a third time (youtube, osa, here): dark UIs layer white at low alpha
so every surface composites over whatever sits behind it, rather than using
opaque greys.

## Motion
**Motion fidelity: partial**. Properties, spring-vs-tween split, duration inventory and a 0.1-0.6s delay ladder measured across 46 entering elements, plus the per-character blur(10px)->0 @400ms / 50ms-per-char reveal. No per-element mapping.


**Framer ships CSS easing after all.** The two previous Framer captures each
tallied *zero* `cubic-bezier` in CSS and the library generalised from that. This
site has **one curve, 45 occurrences**:

```
cubic-bezier(.44,0,.56,1)   @ .4s   — colour/link transitions
```

Symmetric ease-in-out, near-sinusoidal. Duration inventory across all pages:
**0.18s ×225** (background/transform/opacity, plain `ease`), **0.4s ×45** (the
signature curve), 0.15s ×2.

The bulk of the choreography is still JS, via `type="framer/appear"` JSON
payloads executed by the bundled Motion library:

- **46 elements** entering on `opacity` + `scale` + `rotate`
- **22 spring, 1 tween**: springs are the default here, not tweens
- durations 2.5s (×15) and 1.2s (×6)
- delay stagger ladder **0.1 / 0.2 / 0.3 / 0.4 / 0.6s**

The single tween's explicit ease is `[0.44,0,0.56,1]`, **the same curve as the
45 CSS transitions**. One curve serves both layers, which is the cleanest
version of "name curves by job" this library has measured: one curve, one job
(colour and simple state), springs for everything spatial.

A **horizontally scrolling logo marquee** runs continuously near the bottom of
the hero. It is the only permanently-moving element and it caps mobile
breakpoint diffs (see Verification).

## Interaction states

**Zero CSS `:hover` rules on the page.** All hover, focus and active state runs
through Motion in JS, consistent with the Framer pattern. Do not go looking for
a hover census in the stylesheet on a Framer site. There isn't one; read the
appear/gesture payloads instead.

## Template taxonomy

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Homepage | 1 | full nav + footer, marquee, hero display type | - |
| Marketing page | 6 | nav/footer, 56px Geist section heads | section count and order |
| Blog index | 1 | card grid, CMS-driven | - |
| Blog article | 10 | 3.4k–4.8k chars, identical furniture | body length only |
| Careers index | 1 | role list, CMS-driven | - |
| Careers detail | 4 | ~3.75k chars, near-identical | role fields |
| Legal | 2 | prose column, no marquee | body length |
| Changelog | 1 | dated entry list | - |

The homepage plus one blog article and one careers detail page capture the
entire system; the remaining 22 pages add no new design information.

## Gotchas hit while rebuilding

The first three are **framework-independent**: they apply to any mirror of any
CDN-backed site, and each was invisible to every structural check (geometry,
text, fonts and node counts all verified perfectly while they were live).

1. **The CDN content-negotiates image format, and `Accept: */*` gets the wrong
   one.** `framerusercontent.com` answers `vary: Accept`: Chrome's
   `image/avif,image/webp,…` gets **AVIF**, while a mirroring fetch with
   `Accept: */*` gets **PNG**. The reference renders lossy AVIF; the mirror
   rendered lossless PNG.
   *Symptom:* a uniform ~1.2–1.6 level delta across ~90% of background pixels
   with **text essentially untouched** (max delta 3). No layout inspection can
   explain it, because nothing is misplaced.
   *Fix:* refetch every raster under Chrome's Accept header. 128 of 160 came
   back AVIF, 19 WebP. Keep the original filenames so every reference stays
   valid, and set `Content-Type` from **magic bytes** in the server. The
   extensions are now a lie.
   *Verify:* `curl -I '<asset>' -H 'Accept: */*'` vs the Chrome Accept string
   and compare `content-type`.

2. **Dropping query strings collapses CDN-resize variants onto the full-size
   original.** srcset candidates here are one base file plus resize
   instructions: `?scale-down-to=512&width=1024` (512w) and `?width=1024`
   (1024w). The standard recipe strips the query when naming the local file, so
   every candidate resolves to the same untouched original and the browser
   downscales a far larger source.
   *Symptom:* identical geometry, identical text, but diffuse edge-halo deltas
   wherever an image appears; decode sizes differ (e.g. 256×162 vs 443×280,
   1440×644 vs 2025×907).
   *Fix:* fetch each distinct `(path, query)` as its own file. 186 here.
   *Verify:* compare `img.naturalWidth/naturalHeight` for every image across
   both sides; it is a fast, exact check that no pixel diff is needed for.

3. **Runtime-built image srcs live in module bodies and no markup scan sees
   them.** Bundled components construct `src:'/cdn/X.png?width=172&height=96'`
   inside `.mjs`, so a pass over HTML fixes the markup and leaves these behind.
   Because the components doing it were the mobile ones, the residual showed up
   **only at 390px and 768px**. The desktop pages measured at ceiling with 157
   references still broken. Sweep every text asset, not just markup. This
   extends the standing "runtime-built asset paths are invisible to static
   analysis" pattern from a 404-hunting problem to a *silent wrong-variant*
   problem: nothing 404s, so the network log is clean.

4. **Framer's editor bootstrap survives inside a module and the mirror phones
   home.** `build.py` strips `framer.com/edit` at tag level, but one bundle
   contains `await import('https://framer.com/edit/init.mjs')`. Left live, every
   page load fetched that module, pulled a chunk from `app.framerstatic.com`,
   and injected an **iframe to `framer.com/edit` carrying the site id and
   `source=localhost`**: 3 off-origin requests per page on a mirror that
   reported "0 origin refs".
   *Fix:* the import is awaited at module top level and its result is used as
   `{default: createEditorBar()}`, so deleting it rejects the module and takes
   the surrounding lazy factory down. Point it at a local stub exporting
   `createEditorBar()` that returns a component rendering `null`.
   *Verify:* `performance.getEntriesByType('resource')` filtered to entries not
   starting with `location.origin` must be **empty**. Do this on several pages;
   a grep for the origin cannot find a URL that a bundle assembles.

5. **`grep -r` does not follow symlinks, so the origin sweep can silently skip
   the assets.** `build.py` symlinks `cdn/` into `site/` and `site-js/`, and a
   recursive grep over the page directories therefore covers markup only. The
   sweep reported a clean 0 while a live editor iframe was loading on every
   page. Sweep `cdn/` explicitly (or use `grep -R`), and treat the network
   measurement, not the grep, as the authority.

6. Everything in the createstudio and osa entries applied unchanged and cost no
   time: `new URL()` bases kept absolute via `${location.origin}`, root-absolute
   rewriting inside module bodies, relative dynamic imports followed to a fixed
   point, `.framercms` as a real extension, `#inert` never `#`, and a server
   honouring both `?range=a-b` and multi-range `?range=a-b,c-d`. One derived
   `-indexes-` CMS sibling 404s on the origin and is never requested: expected
   and harmless.

## Verification achieved

**25 / 25 sitemap pages: 100% coverage**, set-differenced in both directions.

- **Text layer 100% identical**: 132,607 characters, 25/25 pages, 0 differing.
- **Geometry 100.00% exact**: 873 boxes matched by name+ordinal at 1280×900,
  873 exact on x/y/w/h, **worst delta 0px**.
- **Pixel: every one of 25 pages at its own reference-vs-itself ceiling**, mean
  gap **−0.000 points**, worst +0.020. Ceilings 99.97–100.00%.
- **Breakpoints**: 1024px 100.00% (ceiling 100.00%), 1440px 99.99% (99.99%),
  1920px 99.99% (100.00%). 390px and 768px measure 99.63% / 99.57% against
  99.96% / 99.84% ceilings: **entirely the logo marquee**. Excluding that strip
  they are **99.96%** and **100.00%** against 100.00% ceilings, and every band
  outside it is pixel-identical (max delta 0).
- **Fonts gate passed**: 67 faces both sides, probe output byte-identical.
  Geist 743.1px vs 723.2px fallback, Roboto Condensed 660.7px. Both prove the
  real face is painting.
- **456 assets, 56.6MB, 0 integrity problems.** 0 live origin refs in markup,
  **0 off-origin network requests** measured. 1,403 links wired, 0 missing
  targets, all 25 targets serve 200. 0 exceptions, 0 failed requests.

**Ceiling method worth reusing:** the marquee residual was proved to be phase,
not error, by capturing the *mirror against itself one second apart*. That
scored 98.07% on the marquee band, reproducing the 98.02% reference-vs-mirror
score, while two mirror captures at the same wait scored 99.84% against the
reference's own 99.79%. When an animated region caps a diff, measure the same
side at two different waits; it separates phase from fidelity in one step and
costs two screenshots.

---

# Addendum: 1440px runtime capture (2026-07-30, Adapt job)

Re-measured off the running mirror at `localhost:8834` @1440×900 for an Adapt
build. The original capture above read the **`framer/appear` JSON payloads** at
1280; this pass instrumented `Element.prototype.animate` and read what actually
runs. Both are true and they describe **two different systems**: the appear
payload choreographs *sections* (46 elements, springs, 2.5s/1.2s, 0.1–0.6s
ladder); what follows choreographs *text*, and the original entry missed it.

## The three things that carry its character

1. **Two type sizes: enormous and small.** 128px display against 16px body, an
   8:1 contrast with almost nothing between. Display is set *tighter* than body
   (line-height **0.9**, tracking **-0.05em**) so big type reads as one dense
   shape, centered.
2. **Per-character blur-focus reveal.** Headings split to one span per character:
   ```
   trigger    element top crosses ~84% of viewport height, fires once
   properties filter: blur(10px) → blur(0px)   AND   opacity: 0.001 → 1
   duration   400ms
   stagger    50ms per character, UNCAPPED (measured ladder 0 … 2250ms)
   easing     linear(0, .024, .0823, .1594, .2448, …, 1)  — spring, no overshoot
   ```
   Measured headings run 18–46 characters → **1.75s to 2.65s each**. Text does
   not slide in, it pulls into focus letter by letter. This is the entire pace of
   the page, and capping the stagger destroys the effect.
3. **Light → dark → light, bridged by 800px gradients.** White page; a **6,389px**
   near-black slab (`#121214`) holds the whole feature story; white again. The
   seams are 807px and 798px absolutely-positioned gradient overlays, never a
   hard edge. Card radii inside reach **80px** at 1440.

## Motion, as executed (WAAPI)

- **Card reveal:** same 400ms, easing overshoots to **1.0151** (~1.5% bounce)
  rather than settling flat. Text springs do not overshoot; cards do.
- **Marquees:** two `<ul>` tickers, `linear`, `infinite`, at **48,140ms** and
  **43,911ms** per loop, deliberately mismatched so they never re-sync.
- **Hover:** `opacity 1 → 0.5` on siblings (dim-the-others).
- **Sticky spans** are CSS `position: sticky`, not a pin library: marquee stage
  900px, Number Cards 1340px, Testimonials 900px inside a 3040px track followed
  by 900px + 1080px of dedicated scroll space.
- **0 CSS `@keyframes`** on the page, confirming the JS-only motion note above.

## Geometry @1440 (the original entry measured 1280)

| vw | container | gutter | section pad-Y | dark-card radius |
|---|---|---|---|---|
| 1440 | 1344px | 48px | 80px | 80px |
| 1024 | 976px | 24px | 60px | 64px |
| 768 | 736px | 16px | 48px | 32px |
| 390 | 358px | 16px | 48px | 32px |

Display steps are **discrete Framer variants, not a `clamp()`**: 48 / 96 / 128px
(hero), with 72px for section titles. Line-height stays 0.9 and tracking -0.05em
at every step. Nav shell fixed, 116px tall, padding `32px 48px`.

Page height **22,789px** = 25.3 viewport heights over 33 bands.

## Section map @1440 (top, height)

| top | h | band | bg |
|---|---|---|---|
| 0 | 1306 | Hero: aurora gradient, phone mockup, floating UI cards | light |
| 1306 | 710 | Benefits: tilted eyebrow pill + centered display title | white |
| 2016 | 1800 | About: 40px statement word-filling on scroll, inline dark pill chips, floating violet icon tiles, 900px sticky stage | white |
| 3816 | 3140 | Stats: 900px sticky display marquee + three 508px rotated gradient cards stacking | white |
| 6750 | 807 | **Top Gradient**: the white→ink bridge | - |
| 6956 | 6389 | **Features: the dark slab** | `#121214` |
| ↳ 7390 | 780 | Feature 1, 2-col: lavender product panel / dark card + 4-row accordion | |
| ↳ 8170 | **4029** | Feature 2: vertical stepper, 4 steps ≈1000px each, active expands | |
| ↳ 12200 | 1065 | Feature 3 | |
| 12782 | 798 | **Bottom Gradient**: the ink→white bridge | - |
| 13345 | 933 | Integrations: rounded top corners riding over the dark slab | white |
| 14278 | 3040 | Testimonials: scattered rotated card pile on a dark rounded panel, giant display word behind, 900px sticky | white |
| 17318 | 1343 | Pricing | white |
| 18661 | 843 | Blog | white |
| 19503 | 1566 | FAQ | `#121214` |
| 21069 | 1080 | Closing CTA: 3 stacked display words + phone mockup + floating social chips | `#121214` |
| 22149 | 640 | Footer | `#121214` |

## Component recipes (measured, @1440)

- **Eyebrow pill**: `#525252` fill, radius 8px, pad `1px 6px 0 6px`, **rotated
  +9°** (`matrix(0.9877,0.1564,-0.1564,0.9877)`), label Roboto Condensed 14/900
  uppercase `#D9D9D9`. The tilt lives on a wrapper, not the pill itself.
- **Buttons**: radius 22px, height 60px (hero) / 52px (nav), layered material
  shadow `0 1px 2px rgba(0,0,0,.37), 0 3px 3px rgba(0,0,0,.32), …`.
- **Dark card**: `#212124`, radius 80/64/32, pad `48px 24px`.
- **Feature eyebrow**: Roboto Condensed 14/900 uppercase `#9696FF` on dark.
- **Stat card**: 508px wide, diagonal gradient (lavender / blue / magenta →
  white), soft shadow, alternating few-degree rotations, index numeral top-right.
- Body grey on white `#525252`; secondary on dark `rgba(255,255,255,.6)`.

## Capture gotchas (additional to the mirror gotchas above)

4. **A full-page screenshot captures un-revealed sections as blank.** Reveals are
   fire-once and gated at 84% viewport, so everything below the first fold sits at
   `opacity: 0.001` in a `fullPage` shot. Shoot each band at its own scroll offset
   and wait **3.2s**; the longest character stagger runs 2.65s.
5. **Headings are split one span per character**, so `textContent.startsWith()`
   matches a wrapper rather than the styled node. Select the *deepest* match.
6. **Root-walking from `#main` to find sections fails** on this DOM. Query
   `[data-framer-name]`, filter `width >= 1400 && height > 200`, sort by document
   offset, dedupe co-located wrappers.

---

# Addendum 2: the About/statement section, audited at SPEC depth

Written after this entry's `Motion fidelity: partial` caused three failed
rebuilds of this one section. The skill's own rule applies and is the lesson:
below `spec`, motion must be re-captured, not remembered. Recording it properly
so the next build does not pay again.

## What the section is

Band `About`, doc y 2016, **1800px tall**, containing a **900px sticky stage**.
Statement paragraph, centred, max-width ~1160. Five floating tiles. Three inline
chips inside the sentence.

**Its text is split per character with no spaces in `textContent`**: the string
reads `FromseamlessSpendingtoconfidentGrowthour…`, so any selector matching on a
phrase (`includes('platform unites every tool')`) finds nothing. Match on a
single word, or walk to the band and take the smallest element by height.

## The three motions, and how each was actually determined

**1. Statement fill: scroll-scrubbed opacity. Not a timed reveal.**

The discriminator matters because the two are indistinguishable under naive
sampling: an opacity rising across consecutive scroll steps looks the same
whether it is a scrub or a 400ms animation caught mid-flight. Park at one scroll
position and sample over *time*: a timed reveal completes and holds; a scrub
holds whatever the scroll dictates. Parked inside the band, **zero `animate()`
calls fire for the statement**: the only two are feature-list hover dims
(`opacity 1↔0.5`, 400ms). Framer drives the fill per frame, outside WAAPI.

Chips ride the same fill and arrive in reading order:

| chip | bottoms at | value | resolved by |
|---|---|---|---|
| Spending | band +80 | 0.578 | +560 |
| Growth | band +200 | 0.642 | +800 |
| Financial Future | band +560 | 0.100 | +1280 |

**2. The tiles float with the POINTER, not with scroll.**

They carry Framer's `data-parallaxfloating`. Three separate probes reported
"static": a 19-point scroll sweep (zero drift from page-fixed), an entry-opacity
trace (opacity 1 throughout, no reveal), and a WAAPI capture (nothing fired),
because **not one of them moved the mouse.** Measured at five cursor positions:

```
pointer top-left     ->  translate( +22, +17 )
pointer top-right    ->  translate( -22, +17 )
pointer centre       ->  translate(   0,   0 )
pointer bottom-left  ->  translate( +22, -19 )
pointer bottom-right ->  translate( -22, -19 )
```

Uniform across all five tiles: one float, not per-tile depth. Roughly linear in
the pointer's offset from viewport centre: **≈ −0.035 × dx, ≈ −0.055 × dy**,
saturating near ±22 / ±19px at the edges. Eased, not rigid (~600ms settle).

Rendered tile sizes **93 · 86 · 95 · 64 · 121**, radius 24, flat `#6262FE`, each
rotated (+21 / −5 / +18 / −13 / −13). The rotation lives on a Framer **wrapper**;
reading a tile's own computed transform returns identity and reports rot 0.

**3. Everything else on the page** is the per-character blur reveal already in
this entry: `filter: blur(10px)→blur(0)` + `opacity`, 400ms, 50ms/char, on a
40-stop baked spring. The extractor confirms 62 of 64 animations are that, and
the remaining two are the marquees.

## Gotchas for the next capture

7. **`scripts/motion-extract.js` steps 14 times across the page.** On a 21,710px
   page that is ~1,550px per step, so a 1,800px band can fall entirely between
   snapshots: it recorded fires at scroll 0 / 11941 / 16419 and never touched
   the About band. Fine for a page-level signature; for one section, drive a
   focused sweep at 100–150px.
8. **Test the pointer.** Scroll, entry and WAAPI probes all miss a
   `data-parallaxfloating` effect completely, and it is the section's most
   visible motion. Grep the DOM for `data-parallaxfloating` and, more generally,
   move the mouse before concluding anything is static.

## Addendum 3: corrections to Addendum 2, and the nav island

### The About tiles have TWO motions, not one

Addendum 2 said the pointer float "IS the motion". That was wrong, and it was
wrong in the way this file keeps warning about: another probe with another
blind spot.

**The tiles are not inside the sticky stage.** `stage.contains(tile)` is `false`
for all five. The stage pins at `top:0` for its whole 900px while the tiles, in
the track, travel **−900px relative to it**. They rise one full viewport height
up through the pinned statement as the text fills. That is the section's primary
motion. The pointer float is a secondary garnish on top of it.

Why five probes missed it: every sweep sampled from ~2700 up, past the end of
the pin window (2016→2916). Outside the pin, stage and tiles both move with the
page and the relative drift is zero *by construction*, so each probe faithfully
measured a real zero and drew the wrong conclusion. **Measure a sticky section
inside its pin window or do not measure it.**

Also corrected: a `0×0` wrapper in the ancestor chain reports a rect that never
changes, which reads as "pinned" in a diff. Check `width>0` before calling an
element pinned.

Band geometry: About 1800px over a 900px stage, exactly **2.0×**, which is what
makes the pin one viewport and the travel exactly −100vh. Tiles (wrapper size,
left % of 1440, top % of band, rot): 93/21.8/67.4/+21 · 86/60.2/58.2/−5 ·
95/78.1/73.0/−13 · 64/69.9/84.2/+18 · 121/19.0/86.2/−13. The glyph is a raster
`<img>` at ~50% of the wrapper; the squircle and its gloss are baked into the
PNG, not CSS (`border-radius: 0`, no background, no shadow on the img).

### Nav island: `Motion fidelity: spec` for this component

Flips at **scrollY 120** exactly.

| | open | collapsed |
|---|---|---|
| row width | 1344 | 723 |
| logo | 101×40 wordmark | 48×48 badge, radius 20, black |
| pill background | `rgba(0,0,0,.15)` | `rgba(0,0,0,.4)` |
| pill backdrop-blur | 24px | 80px |
| container | `space-between`, gap normal | `center`, gap 8px |

It is a **spring, not a snap**: sampling every frame shows overshoot and return
(48 → 47.5 → 47.9 → 48), settling ~470ms. Solves to ζ≈0.83, ωn≈22.5 rad/s
(≈ stiffness 500, damping 37, mass 1). Zero WAAPI calls fire and every CSS
`transition-duration` reads `0s`, so **do not conclude "no animation" from those
two signals**. Framer drives it with motion values off the style attribute.
`justify-content` cannot animate; the smoothness comes from the row's *width*
contracting while the parent centres it. Reproduce it that way.

### Section curvature

Colour/white boundaries are cut with geometry, never faded:

- Into colour: white panel, `border-radius: 0 0 120px 120px`.
- Out of colour: three **bottom-aligned** bars (1162+144 = 1191+115 = 1226+80 =
  1306): widths 1210/1316/1440, heights 144/115/80, radii `80 80 0 0`,
  `80 80 0 0`, `120 120 0 0`, fills `rgb(150,150,255)` → `rgb(190,190,255)` →
  white. Shared bottom edge is what makes the tints read as rim light rather
  than three stacked blocks.

### Giant marquee

`48140ms linear infinite`, mask
`linear-gradient(to right, transparent 0%, #000 12.5%, #000 87.5%, transparent 100%)`.
Text is split per character, so any search filtering on `children.length < N`
will not find it.
