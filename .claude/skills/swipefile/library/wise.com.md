# wise.com

**Callable as: Wise.com** (aliases: transferwise)

International money-transfer / multi-currency account product marketing site.
Captured 2026-08-08 @ 1280x900. **Mirror path**, 142-page crawl of the `/us/`
design surface. Stack: Next.js (`__NEXT_DATA__` present), server-rendered with
a heavy client-hydration layer; a separate WordPress-templated help/blog CMS
lives alongside it under the same domain.

## Type: Inter workhorse, one display face for weight alone

- Body/UI: **Inter**, fallback stack `Inter, Helvetica, Arial, sans-serif`.
- A second family, **Wise Sans**, is loaded and painted (canvas A/B confirmed
  a real width delta against the fallback, not a metric-compatible
  substitution) but used sparingly; it did not surface as the dominant family
  in the homepage's own font census, so treat it as a secondary/heading face
  until a targeted capture proves its role.
- Root font-size is a flat `16px`: **no fluid rem driver**, unlike the
  Framer-family entries already in this library. Type scales via fixed
  breakpoint rules, not `clamp()`/viewport units.
- 13 font faces loaded total on the homepage (font-gate.js census, agreeing
  on both reference and mirror).

## Layout

- Content container measured **1280px at 1280px viewport**: full-bleed to
  the breakpoint, no narrower fixed max-width on desktop.
- Mobile (390px) container reading came back wider than the viewport (500px)
  in this pass: a measurement artifact from a generic `main > *` selector
  picking the wrong element at that breakpoint, not a verified layout fact.
  Re-measure with a page-specific selector before relying on a mobile
  container width.
- Section rhythm on the homepage: 11 stacked `<section>` elements, each with
  a stable `id` (`hero-section`, `flags-section`, `benefits-section`,
  `pricing`, `availability-section`, `security-section-us`,
  `social-trust-section`, `business-section`, `app-section`,
  `coverage-section`, `disclaimer-section`): a durable naming convention
  worth grepping for on a re-capture rather than re-deriving structure from
  scratch.

## Colour

Bright-lime-on-dark-green brand pairing, with the dark colour also doing duty
as a low-alpha overlay, the light-mode inverse of this library's existing
"dark UIs layer white at low alpha" pattern (youtube.com):

| Hex | Use count (homepage) | Role |
|---|---|---|
| `#454745` | 1395 | body text grey |
| `#163300` | 660 | brand dark green: headline text, and reused at 8%/20% alpha as a background tint |
| `#0e0f0c` | 430 | near-black, secondary text/icons |
| `#e8ebe6` | 54 | off-white section background |
| `#9fe870` | 42 | brand accent: the signature lime-green (hero background, primary CTA) |
| `#ffffff` | 39 | white |
| `#868685` | 12 | muted grey, disabled/tertiary text |
| `#0b4c72` | 10 | blue: link or secondary-accent role, not yet confirmed which |

`rgba(22, 51, 0, 0.08)` and `rgba(22, 51, 0, 0.2)` (16 and 15 uses) are the
same `#163300` layered as a tint, not two separate colours. The alpha-layer
system extends to the BRAND colour here, not just neutrals.

## Motion

**Motion fidelity: partial** (real durations, curves, and a stagger ladder
measured and mapped to the site's structure; no confirmed per-animation
target/trigger table, so building from this entry means re-capturing the
mapping, not skipping capture).

**The signature.** `cubic-bezier(0.34, 1, 0.64, 1)` is the highest-frequency
real curve (8 uses), a back-eased "overshoot-then-settle" cubic, distinct
from every curve already in this library. A close sibling,
`cubic-bezier(0.34, 1.2, 0.64, 1)`, appears 4 times with a slightly stronger
overshoot (`y1` 1.2 vs 1), likely a second, deliberately punchier variant of
the same family rather than measurement noise, since both showed up
consistently across repeat captures. `cubic-bezier(0.8, 0.05, 0.2, 0.95)` (3
uses, a hard ease-in-out) and `linear` (12 uses, plain opacity/colour fades)
round out the vocabulary. Duration classes: **1500ms** (15 uses) and
**1600ms** (7 uses) are the structural pair, both far longer than this
library's other entries, reading as a deliberate "slow, confident settle"
character rather than a quick UI-feedback timing; **350ms** (3) and **3000ms**
(2) are secondary. Stagger ladder: **50ms, 100ms**. Mechanism: scroll reveals
are `IntersectionObserver`-driven through a shared component (class names
carry the literal string `RevealInteractive`), the same two-class-gate
pattern already documented for phenomenonstudio; load-time entrance uses
plain CSS `@keyframes` on the hero and app-download sections.
`prefers-reduced-motion` state was read as present on the reference during
capture.

**The gap that matters most about this entry:** the homepage's single
richest region, a real-time competitor-rate comparison widget
(`id="pricing"`), is 100% client-fetched from a live backend with **no
server-rendered fallback**, confirmed absent from the raw crawled HTML
before any client JS runs. It accounts for the large majority of the
reference's measured animation count (28 vs. 1 on a static mirror) and its
signature durations (1500/1600ms). **No mirror of this page can carry that
region's motion without impersonating Wise's own pricing API**. This is not
a capture-technique gap, it is architectural. Anyone re-deriving Wise's
motion character from this entry should know the *dominant* timing class
belongs to a widget they will not be able to rebuild from a static capture.

## Interaction states

Not separately captured in this pass. Homepage capture focused on load/scroll
motion and the pricing-widget gap. A re-capture should sample hover/focus on
the primary nav mega-menu (confirmed present, three top-level triggers:
Personal / Business / Platform, each opening a multi-column panel) and the
disabled-CTA pattern noted below.

## Template taxonomy (multi-page crawl)

| Template | Instances (this crawl) | Fixed | Varies |
|---|---|---|---|
| Product/marketing page (`/us/<product>/`) | ~20 | Section-based layout, shared nav/footer | Hero copy, feature grid content |
| Business sub-pages (`/us/business/*`) | ~15 | Same shell as product pages | Product-specific feature lists |
| Platform sub-pages (`/platform/*`) | ~10 | Same shell, no locale prefix | Industry-targeted copy |
| Pricing calculator variants (`/us/pricing/*`) | ~10 | Calculator widget shell | Currency pair, fee schedule |
| Legal/policy pages | ~15 | Plain prose template | Jurisdiction, policy text |
| Company pages (about/press/mission) | ~5 | Editorial template | - |

**Bulk, sampled by root page only, not crawled** (990 URLs skipped): currency
converter pairs, stock-ticker symbols, SWIFT/IBAN per-code lookups,
cost-of-living city pairs, routing numbers, airport-city pairs, per-country
send-money pages, and help-center articles across 20+ languages, each
confirmed as a real, working tool at its root path, with the deep per-instance
pages being genuine template repetition with no new design information.

## Gotchas hit while rebuilding

1. **The site is geo-personalized server-side, with no redirect to signal
   it.** A bare `curl`/crawl of `wise.com` from a non-US IP returns a
   fully different homepage (different copy, currency defaults, regulatory
   text; this capture's first pass silently got the Philippines variant).
   Fix: check the location/language switcher before committing to a crawl
   seed; the `/us/`, `/gb/`, etc. path prefix is stable once chosen. Verify:
   confirm the page banner ("You're on the X website") or the nav's locale
   prefix before treating a capture as canonical.

2. **The real sitemap is at `/sitemap` with no `.xml` extension**, and it is
   a 3-level-deep nested index (index → 27 category indexes → per-category
   leaf files). `crawl.py`'s sitemap loader resolves one level of nesting by
   design, so it safely undercounts here rather than exploding, but the
   "coverage vs sitemap" number it reports is not meaningful for a site
   nested this deep. Verify actual scope by histogramming crawled path
   prefixes, not by trusting the sitemap set-difference.

3. **A JS bundle's own template-literal interpolation can crash the mirror
   builder.** A dynamic-import spec like `` import(`//${n.value}/x.js`) ``
   matches the same backtick-quoted capture pattern real dynamic imports use,
   and `urljoin()` raises on the stray `${`. Fixed upstream in
   `scripts/build.py` (`safe_urljoin`); if re-deriving on an older copy of
   this skill, wrap every `urljoin()` call site.

4. **A CDN asset URL can contain a raw, unencoded space** (a CMS naming
   uploads after their alt text: `abc-United States.svg`). `urlopen` raises
   `InvalidURL` before any byte is requested. Fixed upstream
   (`scripts/build.py`'s `fetch_safe`); the fix percent-encodes only at the
   point of request, keeping the raw string as the rewrite key.

5. **Inline analytics trackers survive every markup-level rewrite and still
   fire against production.** Google Tag Manager's own published snippet
   builds its beacon URL by string concatenation at runtime
   (`'https://…/wisetag?id='+i+dl`), invisible to any `src=`/`url()` rewrite
   pass. Measured live: a mirror with 0 static origin references still made
   a real request to Wise's own analytics infrastructure on load. A bundled
   Mixpanel SDK reads its token from an embedded JSON config blob the same
   way. Both are neutralized upstream now (`scripts/build.py`'s
   `GTM_INLINE`/`GTM_NOSCRIPT`/`MIXPANEL_TOKEN`), matched by structural
   fingerprint rather than by this site's specific container ID, so the fix
   generalizes to any GTM/Mixpanel install. Verify by measuring
   `performance.getEntriesByType('resource')` filtered to off-origin entries
   on the SERVED mirror. Static grep cannot see a runtime-constructed URL.

6. **A native CSS `@keyframes` animation's easing can come back silently
   wrong, and doubled.** `motion-extract.js` had two independent bugs, both
   fixed upstream: a naive `.split(',')[0]` truncated any 4-parameter
   `cubic-bezier()` at its first internal comma (shipping
   `'cubic-bezier(0.34'` as a "curve"), and `CSSAnimation` objects were
   missing the same "already covered by events" exclusion `CSSTransition`
   already had from the WAAPI polling path, so every `@keyframes` animation
   was recorded twice, once correctly via the `animationstart` event and
   once via polling with a **wrong** `'linear'` easing (`getTiming().easing`
   reflects the raw `KeyframeEffect` option, which is unreliable for
   browser-parsed CSS animations). This silently doubled every real curve's
   weight and manufactured phantom `linear` entries in exactly the
   frequency tally signature-curve selection depends on. Verify a
   `motion-extract.js` capture's curve list contains no truncated
   `cubic-bezier(` values and no unexplained excess of `linear` relative to
   what a manual spot-check of the page's actual transitions suggests.

7. **A vendor SDK bundled INLINE (not as a separate file) can crash Next's
   entire hydrated tree, whiting the page even though the SSR HTML underneath
   is fine.** Wise loads Mixpanel two ways at once: an external
   `mixpanel-2-latest.min.js` (stub-able by filename: gotcha 5's treatment
   already covers this) AND a second, byte-identical copy of the same
   library's source webpack-bundled straight into 7 of Wise's own 8
   `_app-*.js` zone chunks, where no filename exists to intercept. That
   copy's own `get_config` accessor,
   `MixpanelLib.prototype.get_config=function(prop_name){return
   this.config[prop_name]}`, throws the instant any tracking call
   (`track`, `track_pageview`, a group helper) reaches an instance whose
   async `_init()` hasn't set `this.config` yet, which the library's own
   snippet-queue pattern (`window.mixpanel = window.mixpanel || []`, queued
   calls fire once the real script loads regardless of whether `init()`
   completed) and a consent-gated init a static mirror's missing CMP can
   never fire both make easy to hit. Confirmed via CDP: the exception is
   caught **inside React's commit-phase error boundary**, never reaching
   `window.onerror`/`unhandledrejection`. A global error-suppression shim
   cannot help here, because React/Next never let it become a genuine
   uncaught event. Next.js reacts by cancelling the in-flight render
   ("Cancel rendering route", `E503`, confirmed against the literal string
   in `main-*.js`) and mounting its own error fallback ("Sorry, looks like
   we lost this page") over real content, on every page, not just the
   pricing-widget-bearing homepage. Fixed upstream (`scripts/build.py`'s
   `MIXPANEL_GET_CONFIG`), matched on the accessor's own unguarded body text
   (`this.config[<param>]` inside a `get_config` function, two minified
   param-naming shapes confirmed present) and rewritten to
   `(this.config||{})[<param>]`: identical result once config is set,
   `undefined` instead of a throw before it is. Confirmed byte-identical
   stock `mixpanel-js` library code across every affected zone bundle, not
   Wise-authored glue, so the fix generalizes to any site bundling the same
   library version inline. Verify by loading the mirror in a real browser
   (not just checking the raw HTML) and confirming the console shows no
   "Cancel rendering route" / no fallback to a 404-shaped screen on first
   paint. A static HTML/pixel diff alone cannot catch this class of bug,
   since the SSR markup being diffed is correct; only a live render shows it.

## Verification achieved

Full REPORT.md/report.json at the build (`swipefile-builds/wise.com-clone/`).
Honest summary: **NOT DONE** by this skill's own strict measure. One
architectural gap (the live pricing-comparison widget, gotcha-free, see
Motion above) drives every other reported delta.

- **Structural**: 142 pages built (of 174 raw crawl-manifest entries, 32
  collapsed as query-string variants of already-captured pages), 0 missing
  link targets, 0 origin references remaining, 0 off-origin requests
  measured at runtime on the homepage (2 minor residuals on other templates:
  a cosmetic favicon re-fetch, a CDN library load whose tracking token is
  already neutered; neither affects visible content).
- **Font gate**: PASS. 13/13 faces agree on both sides, real widths
  confirmed via canvas A/B (not metric-compatible substitution).
- **Geometry**: 3 of 11 sections match within 1px; the 7 sections below the
  missing pricing widget are offset by 1081–1111px, matching the missing
  section's own 1110px height almost exactly, confirming one root cause
  explains every downstream delta.
- **Pixel diff**: top fold (above the gap) measures 98.87% similarity /
  97.03% within 16/255, against a 100%/100% reference-vs-itself ceiling,
  effectively pixel-perfect where content exists to compare.
- **Text layer**: 68.66% (8839 ref chars vs 6090 mirror). The ~2749-char
  shortfall matches the missing widget's content by direct inspection; every
  other section's text is programmatically extracted, never retyped.
- **Motion diff**: FAILS as expected. Reference measures 28 animations to
  the mirror's 1, entirely attributable to the missing widget's choreography
  (see Motion above).
- **Unresolved**: full per-item explanation lives in `report.json`'s
  `honesty.unresolved` (7 entries) rather than repeated here.
