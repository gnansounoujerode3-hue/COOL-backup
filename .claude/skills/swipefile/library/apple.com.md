# apple.com

**Callable as: Apple** (aliases: apple.com, apple)

Apple's global marketing homepage and top-level product pages. Captured
2026-08-03 @ 1440×900. Stack: server-rendered, hand-built (no detectable
framework signature: no React/Vue/Framer globals, no build-tool query params).
**Mirror path**, static (scripts stripped).

## Type: SF Pro, two roles, no fluid driver

`SF Pro Display` for headlines (56px/60 line-height on the hero H2, weight 600),
`SF Pro Text` for everything else (12–21px, weights 400/600). Both are Apple's
own system faces, served locally via `@font-face`, not a Google Fonts or
Adobe Fonts dependency. Root font-size is a flat value, no `vw`-clamped fluid
driver (contrast with the Framer sites in this library, which mostly use one).
72 face variants load on the live reference across nav, footer and interactive
states; a static mirror loads 18. The two families agree on both sides, which
is the actual font-gate condition, not the face count.

## Layout

1440px+ desktop breakpoint captured. Hero content is centered, ~570px measure
for the primary headline block. Sections are full-bleed, alternating flat
background colors (`#f5f5f7`-class greys) with occasional light-blue gradient
bands between product sections. Confirm exact tokens on a full breakpoint
pass; only the primary width was measured this round.

## Colour

Near-black text (`rgb(29,29,31)`) on light grey/white surfaces. Accent blue for
CTAs (`Shop` pill button). Restrained palette: no bold hero background colours
observed on this pass; product photography and the signature "cutout" halftone
illustration style (dot-pattern die-cut photos, seen on the back-to-school
promo) carry most of the visual interest instead of the palette.

## Motion

**Motion fidelity: partial**

43 animations measured via `motion-extract.js` (two-phase capture, hooks
installed before load). By kind: 28 `CSSTransition`, 15 `CSSAnimation`. Durations
by frequency: **1000ms ease-in-out ×20** (hero/section fades), 320ms ×12 across
two curves (`cubic-bezier(0.4,…)` and `linear`, both used for UI-state
transitions), 250/400ms minor. Only **1 of 43** animations fired scroll-triggered;
this homepage's motion is almost entirely load-time and interaction-driven,
not scroll-choreographed, a real contrast with every Framer/marketing-site
entry elsewhere in this library.

The one named component-level system found: the **global nav search overlay**
(`globalnav-searchresults`) stages its result list in on a **20ms per-item
stagger**, `cubic-bezier(0.4,…)` @ 320ms. This is the richest single mechanism
on the page and it is interaction-gated (fires when a visitor types a query),
not part of the passive homepage experience.

`prefers-reduced-motion`: **absent** on the live reference. Notable given
Apple's public accessibility position: worth re-checking on a future capture
in case it is conditionally injected by a script this pass didn't trigger.

No per-animation spec table yet; this entry is `partial`: real curves and
durations, no target/trigger/from-to mapping. Promote to `spec` with a full
`motion-diff.py`-verified pass before building motion from this entry by name.

## Interaction states

Not captured this pass (no dedicated hover/focus sweep run). Add on a future
capture.

## Template taxonomy (multi-page crawl)

Scoped crawl, 30 of 846 sitemap pages. See gotcha below for why 30, not more.

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Product marketing page (Mac, iPad, iPhone, Watch, Vision Pro, AirPods, TV) | 7 | Global nav, footer, hero-then-feature-sections structure | Hero copy, feature count, media type (video vs photo) |
| Shop/buy configurator (`shop/buy-*`) | 5 | Same nav/footer shell | Product options, price panel |
| Accessory/compare/specs sub-pages | ~10 | Table-driven layout | Row count, comparison targets |

## Gotchas hit while rebuilding

1. **Sitemap seeding order starves a scoped crawl of its own nav breadth.**
   `crawl.py`'s default sitemap seeding queues all 846 sitemap URLs
   *alphabetically*, and they sit in the queue ahead of the homepage's own
   extracted nav links (FIFO: sitemap seeding happens before the homepage's
   own links are appended). A capped scoped crawl (`--max-pages 26`) burned
   its entire budget on `accessibility/*` and `airpods-*` query-string variants
   before reaching Mac/iPhone/Watch at all. **Fix:** run with `--sitemap ""` for
   a scoped homepage crawl, pure breadth-first from the page's own nav order,
   which is what "the design surface" actually means for a site this size.
   Verify by checking page 2–5 of the crawl log are real top-level nav targets,
   not alphabetically-early sitemap noise.
2. **`srcset` was harvested for fetching but never rewritten for serving: a
   real bug, now fixed in `scripts/build.py`.** Every `<picture><source
   srcset="...">` still pointed at the origin's root-relative path after the
   build, even though `harvest()` correctly fetched the referenced assets into
   `cdn/`. Symptom: three real photographs in the homepage hero rendered as
   blank grey boxes. The reason it's silent: a `<picture>` element does **not**
   fall back to its `<img>` when the `<source>` it selected 404s; fallback
   only triggers when no `<source>` matches the media query at all. So the
   failure looks like a missing-image bug, and the actual asset is sitting
   right there in `cdn/`, just never pointed at. Fixed with a dedicated
   `srcset`-list rewrite pass (comma-separated candidates, each with an
   optional `Nx`/`Nw` descriptor to preserve) and covered by 4 new assertions
   in `scripts/tests/test_build.py` using this exact `<picture>`/root-relative
   shape. Re-verify on any future capture: `grep -c '/v/' site/*.html` should
   be 0, or the site-specific asset path prefix equivalent.
3. **A live geolocation banner adds real layout height and must be measured,
   not guessed.** Headless Chrome resolved to a Philippines IP and apple.com
   served a "Choose another country or region" banner absent from the mirror
   (correctly: it's server-driven and transient, the same class as a cookie
   banner). Guessing its height for the diff crop (74px) left enough residual
   ghosting to look like a real layout bug; measuring the actual banner height
   via a live CDP box-geometry query on a stable heading (**70px**, confirmed
   because font/color/width/height were otherwise pixel-identical) resolved it
   immediately. Lesson generalizes: always measure the crop offset from a
   live DOM query, never estimate it from a screenshot by eye.
4. **The homepage's below-the-fold content appears to vary between separate
   page loads.** Two live CDP queries for the same landmark text, seconds
   apart, returned different DOM neighborhoods (footer-nav headings vs.
   content headings at the same viewport position), consistent with real
   session-to-session personalization/promotional rotation, the same
   mechanism serving the geolocation banner. A pixel diff residual in the
   footer transition band (54.73% within-16 vs. 94–99% elsewhere) was
   **not resolved** and is recorded honestly rather than claimed fixed; a
   second reference capture in the same session would confirm whether it is
   personalization or a genuine mirroring defect.
5. **No JS framework globals, no build-tool fingerprint.** Confirmed by
   probing runtime globals rather than grepping bundle comments (this
   library's standing rule): no `window.React`, no Vue, no Framer-style
   content-hash class names. Apple's frontend appears to be a hand-built,
   heavily componentized system (`globalnav-*`, `-elevated`, `-flyout`
   naming) rather than a framework output.

## Verification achieved

Whole-page pixel diff (1440×900, banner-cropped by measured 70px): **98.32%
similarity, 88.45% within 16/255**: clears the similarity floor, just under
the within-16 target. Region-split: photo band (the srcset fix) **99.99%/
99.94%**; nav+hero text 96.66%/94.57%; footer transition band 97.12%/54.73%
(unresolved, see gotcha 4). Font gate: families agree (SF Pro Display, SF Pro
Text) on both sides, `zeroFaces: false` both. Motion gate: **fails**, entirely
on the interaction-gated search overlay (see Motion section); homepage
content motion (1000ms fades, 320ms UI transitions) reproduces correctly.
Copy/SEO/GEO gate (`--match`, captured copy never rewritten): **passes** on
homepage and `/mac/`; real `Organization`/`WebSite`/`WebPage`/`Brand` JSON-LD
present, one of the few references in this library shipping real structured
data. Assets: 5725/5800 mirrored (75 failures: Apple Pay favicons, ~10 Apple
Music thumbnails, one stray non-asset URL; none on the design surface
crawled). Scope: 30 of 846 sitemap pages (bulk excluded and quoted: 140 legal,
127 locale variants, 94 education, 79 feedback, 51 business).

---

# Addendum: 2026-08-11 · Liquid Glass (Adapt capture)

Second capture against a different surface set, for an **Adapt** job (a dark
finance dashboard "like Apple's Liquid Glass"). Three pages, headless CDP,
1440×900: `developer.apple.com/design/human-interface-guidelines/materials`,
`apple.com/os/macos/`, and the June 2025 newsroom design announcement.

**The finding that governs any Liquid Glass job.** Apple's *web* properties are
NOT rendered in Liquid Glass. Liquid Glass is the OS material (iOS 26 / macOS
Tahoe 26); apple.com and developer.apple.com ship Apple's ordinary marketing
chrome. Confirmed across all three pages: **no lensing, no refraction, no
specular or edge highlight, no displacement filter and no inset highlight
anywhere in their CSS.** So a capture of an Apple web page cannot supply a
Liquid Glass recipe, and any entry that implies otherwise will produce a
confidently wrong build. Split the job in two: measure the web chrome, and take
the material's behaviour from Apple's own documentation.

## MEASURED: Apple's real web glass recipe

The whole system, and it is smaller than people assume:

- **Bars and scrims:** `backdrop-filter: saturate(180%) blur(20px)` over a
  **70–80% alpha** fill. Light `rgba(250,250,252,.8)` / dark `rgba(22,22,23,.8)`;
  the sticky sub-nav uses `rgba(255,255,255,.7)` → `rgba(29,29,31,.7)` dark.
- **Small round controls:** `blur(10px)` over **80%** white, `border-radius: 50%`
  at 44×44 (a pill variant at 92×44 / radius 22).
- **The entire edge treatment is one 1px hairline**, `rgba(29,29,31,0.2)`, drawn
  as a `::after` with `inset: 100% auto auto 0`. **No border on the glass
  element, no inset highlight, no box-shadow, no gradient.**
- **Surface transition:** `backdrop-filter, background-color` @ **0.4s
  `cubic-bezier(0.4,0,0.25,1)`**.
- Every declaration is wrapped in `@supports (backdrop-filter: initial)` with an
  **alpha-bump-to-0.9 fallback** and an explicit `-noblur` class escape hatch.
- Declared-but-unmounted extremes worth knowing: a notification container at
  `blur(80px)` / radius 100px, and `.modal-curtain-blur` at `blur(20px)`.

## MEASURED: motion (newsroom page, two-phase `--pre` capture)

34 animations, 32 CSSAnimation / 2 CSSTransition, 20 scroll-triggered.
Durations by frequency: **800ms ×20**, **320ms ×12**, 300ms ×2.
Resolved curves: the 800ms reveal is `cubic-bezier(0.4, 0, 0.25, 1)`; the 320ms
nav ladder is `cubic-bezier(0.4, 0, 0.6, 1)`.

Reveal spec (`nr-scroll-animation`, 10 instances): IntersectionObserver, **no
library**, fires once, arms when the element top crosses **~97–101% of viewport
height** (the bottom edge). `opacity 0→1` + `translate(0, 20%)→0`, 800ms, no
stagger (each block independent). Note the trigger-offset histogram also showed
39–81% readings; those are artefacts of an 805px scroll step overshooting, not
real triggers. Read the cluster, not the outliers.

## DOCUMENTED: the Liquid Glass rules that change how you build

From Apple's HIG "Materials" and "Color" pages. These are behaviour rules, not
measurements, and the first one is the one people get wrong:

1. **Liquid Glass is the FUNCTIONAL layer only**: controls and navigation (tab
   bars, sidebars, toolbars) floating above content. Apple **explicitly
   prohibits it in the content layer**, prescribing *standard materials* there;
   the stated reason is that it otherwise produces confusing hierarchy. The one
   exception is transient interactive controls (sliders, toggles) which adopt it
   *while being activated*. Practical consequence: a build wants **two** surface
   systems, not one glass class on every card.
2. **Two variants.** *Regular* blurs and adjusts background luminosity for
   legibility: most components, and anything text-heavy (alerts, sidebars,
   popovers). *Clear* is highly translucent, for floating over media.
3. **The one hard number on the page:** clear glass over bright content wants a
   **35% dark dimming layer**.
4. **No inherent colour**: it takes colour from the content behind it. Tint is
   for emphasis only (a primary action, a status indicator); colour the
   background, never the symbols or text; never tint several controls at once.
5. **Larger elements read more opaque** (sidebars vs toolbars), to hold
   legibility over complex backgrounds. So alpha should scale with surface size.
6. **Small elements adapt light/dark** to the content behind them, with
   monochromatic symbols/text.
7. **Use it sparingly**: limited to the most important functional elements.
8. Accessibility settings that **reduce transparency or increase contrast**
   change the material, and macOS 27 adds a user slider spanning "ultraclear to
   fully tinted".
9. Prefer a **scroll edge effect** over a filled background to separate the
   control area from content.

macOS Tahoe's marketing page documents almost nothing (Liquid Glass is named
twice, both marketing copy) but does assert two things: **refraction is real**
and was made *more uniform* in 27, and **contrast/readability** was the goal of
that revision.

## Gotchas from this pass

6. **The browser-level CDP endpoint has no Page/Runtime domains.** Connecting to
   `/json/version`'s `webSocketDebuggerUrl` and calling `Page.navigate` returns
   `-32601 'Page.navigate' wasn't found` for every call, which reads as a broken
   script rather than a wrong socket. Attach to a **page target** from
   `/json/list` instead. Cost ~20 minutes here; it is a one-line fix.
7. **Sheets silently coerces `N/M` strings into dates in the xlsx export.**
   Installment markers like `6/6`, `11/12`, `1/9` are stored as real datetimes
   wherever N≤12 and M≤31; `16/18` and `20/36` survive as text because they are
   not valid dates. The **CSV export keeps the display text**. Any xlsx-only
   parse of a spreadsheet with fraction-shaped cells emits garbage for the
   majority of them and looks fine for the rest. Parse both and cross-verify.
8. **The CSV export rounds to whole units while the xlsx keeps decimals.** Same
   sheet, two exports, different values: on a finance sheet that is silent data
   loss. The xlsx numerics are authoritative; keep the CSV text as `raw`.
9. **Glass needs a high-contrast environment, not a pretty one.** A smooth
   gradient env map reflects as a smooth wash and `MeshPhysicalMaterial`
   transmission renders as matte plastic no matter how the material is tuned.
   A dark surround with a few bright, tight, soft-edged sources (a studio rig)
   is what makes it read as glass. Equally: **transmission refracts what is
   behind the object**, so glass in front of a flat colour field looks like a
   solid ball. Either give the background structure or accept the orb.
10. **Emissive panels in an env scene refract as hard-edged rectangles** inside
    the glass, which read as rendering artefacts. Use a gradient/blob canvas
    texture through `PMREMGenerator.fromEquirectangular` instead, and expect to
    push `envMapIntensity` to ~3, because a canvas texture tops out at 1.0 per
    channel where emissive panels ran to 6.

## Verification achieved (this pass)

Capture only: no mirror, no pixel diff (Adapt mode). 3 surfaces, ~40 JSON
extracts and ~50 screenshots. Motion captured two-phase with `--pre`. The
translucency recipe above is complete for the pages captured; **no Liquid Glass
values were measured, because none exist on the web**. Everything in the
DOCUMENTED section is Apple's stated behaviour, quoted, not observed.
