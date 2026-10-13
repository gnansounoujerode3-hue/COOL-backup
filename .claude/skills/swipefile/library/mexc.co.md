# mexc.co

**Callable as: MEXC** (aliases: mexc.co, mexc, mexc philippines)

Crypto exchange marketing/product site (Next.js SSR): homepage, market/price
listing, per-coin price pages, fee schedule. Captured 2026-08-08 @ 1440×1000,
`en-PH` locale. Stack: Next.js (webpack chunk names, `__NEXT_DATA__` JSON
island, `_app`/`_buildManifest`/`_ssgManifest`), server-rendered with a large
client hydration layer for live data (prices, fee tables, charts). **Mirror
path** (static, scripts stripped; see Gotchas).

## Type: one custom sans, weight does the work

Single custom variable-ish family, **MEXCSans** (with an alternate label
"MEXC Sans" also present; treat as the same face, two `font-family` strings
seen), falling back to `-apple-system, "Segoe UI", Roboto, "Helvetica Neue",
Helvetica, sans-serif, BlinkMacSystemFont`. Weights observed in the on-page
census: 400 (body/labels), 500 (secondary emphasis), 600 (headings/buttons),
700 (rare, big display numbers). No serif or mono anywhere in the sampled
pages. Sizes run roughly 12–14px (table/meta text), 16–20px (body), 32–52px
(section/hero headings): a fairly conventional 4–5 step scale, not a fluid
`clamp()`/`vw` system like the Framer captures elsewhere in this library.

## Layout

Fixed top nav bar (~64–70px), full-bleed hero sections, then a centered
content column (max width ≈1200–1280px) with generous side padding at 1440.
Cards (trending tokens, fee tiles, promo tiles) sit in simple CSS grids, not
JS-computed column counts. The BTC price page uses a classic three-column
app-shell: left sidebar nav (~190px, "More About BTC"), center content
column, right rail (~300px) for promo/calculator widgets, a pattern likely
shared by the whole `/price/<TICKER>` template family (see Template
taxonomy).

## Colour

Pure black background, `rgb(0,0,0)`, not a near-black like `#0a0a0a`. Primary
accent is a saturated blue, `rgb(20,99,255)` / `#1463FF`, used for primary
buttons and links; buttons are fully pill-shaped (`border-radius: 999px`).
Body text mostly white/light-grey on black; secondary/muted text drops to a
mid-grey. Green/red are used conventionally for price up/down deltas. A
starfield/gradient dark-navy background image appears behind hero sections
(fee page, price page), a static image asset, not canvas-generated.

**Theme note (gotcha):** the site ships both `data-theme="light"` and
`data-theme="dark"` variants of the same markup via an `html[data-theme]`
attribute that drives the whole CSS variable system. Anonymous requests with
no theme cookie inconsistently receive `light` in the raw SSR HTML on some
routes (`/price`, `/price/<TICKER>`, `/fee` returned `light` on `curl`) while
the homepage returned `dark`, but the live, hydrated site always renders
**dark** regardless of which the SSR shell shipped (confirmed via headless
Chrome screenshots of all four pages). Mirroring the raw SSR `light` attribute
verbatim silently themes 3 of 4 pages wrong (near-total colour inversion,
pixel similarity dropped to ~5% before the fix). Fix: force
`data-theme="dark"` on every captured page regardless of what the raw fetch
shipped, unless the specific job wants the light variant.

## Motion

**Motion fidelity: none**

Not measured this pass: scripts were stripped from the mirror for safety
(see Gotchas), and `motion-extract.js` was not run against the live reference
this session. The site is a heavy Next.js SPA and almost certainly has
JS-driven reveals/counters; treat any future motion work here as a from-scratch
capture with `--pre motion-extract.js` before scrolling.

## Interaction states

Not systematically probed this pass (hover/focus deltas). Buttons show the
conventional slight-darken-on-hover pattern typical of the framework; nothing
unusual observed in passing.

## Template taxonomy (multi-page site)

| Template | Instances (sitemap) | Fixed | Varies |
|---|---|---|---|
| Homepage | 1 | nav, footer, promo modal | hero copy/campaign, trending-token cards (live data) |
| `/price` (market overview) | 1 | hero, FAQ, nav | the coin table itself (live-fetched; even the live reference showed "No data" during a headless capture with no session) |
| `/price/<TICKER>` | ~1,700+ (one per listed coin, per `/price/sitemap.xml`) | 3-col shell, sidebar link list, calculator widget, "More About X" nav | ticker name/symbol/icon, price, chart (canvas, JS), the info blocks below the fold |
| `/fee` | 1 | hero, tier cards, tab strip | fee numbers and per-pair table (live-fetched) |

Only **one** `/price/<TICKER>` instance (BTC) was mirrored as the template
exemplar; the other ~1,700 were deliberately not crawled (see Gotchas /
scope).

## Gotchas

- **Sitemap is enormous and almost entirely per-coin/per-locale pages.**
  `/sitemap.xml` is an index of ~13+ sub-sitemaps (`price`, `price-converter`,
  `price-prediction`, `price/tokenomics`, `price/info`, `price/analysis`,
  `how-to-buy`, `news`, `memecoin`, `markets`, each further split per-locale).
  The design surface any human means by "the site" is homepage + market
  overview + fee page + one coin-page template (a few pages, not thousands).
  Scope explicitly rather than trusting `crawl.py`'s default BFS from the
  homepage: the homepage nav links to `/buy-crypto`, `/exchange/<PAIR>`,
  `/futures/<PAIR>`, `/earn`, `/launchpool`, etc. (all real *transactional*
  UI, not marketing/design surface, and out of scope for a safety-constrained
  study mirror of a live exchange).
- **This is a live crypto exchange with real trading/account functionality.**
  For any Match of this domain: strip all `<script>` tags from the mirror
  (the live JS bundle is the full trading app and will attempt real hydration
  / API calls if left in), neutralize every `href` to login/register/trade/
  deposit/withdraw endpoints, and confirm zero off-origin requests at runtime
  with a CDP performance-entries probe before calling it done. Static,
  script-stripped mirroring costs real functionality: live price tickers, fee
  tables, and the BTC-page price chart are all client-fetched and render
  blank/loading in a static mirror. This is a correct, expected trade-off
  here, not a defect to chase, but say so plainly in the report rather than
  silently reporting a lower similarity number with no explanation.
- **MSYS/Git-Bash path-mangling silently corrupts `crawl.py --include`/
  `--exclude` regex arguments that start with `^/`.** Git Bash's automatic
  POSIX→Windows path conversion rewrites `^/en-PH/price$` into
  `^C:/Program Files/Git/en-PH/price$` inside the argument, and the exclude
  silently stops matching. Pages that should have been scoped out (whole
  trading/futures UI) get crawled anyway, with no error. Fix: export
  `MSYS_NO_PATHCONV=1` before invoking `crawl.py` from Git Bash on Windows.
  Confirmed by tracing `should_follow()` with and without the env var.
- **`crawl.py`'s `should_follow()` filters the pre-redirect href, not the
  final URL.** A same-looking excluded link can still end up mirrored if the
  origin 302s it somewhere no exclude pattern covers (observed: an excluded
  homepage link redirected to `/en-PH/earn`, which then got crawled despite
  `earn` being in the exclude list). For a small, hand-picked page set this is
  moot: fetch the exact URLs directly and hand-build `crawl-manifest.json`
  rather than fighting redirect-aware scoping through BFS flags.
- **A promotional modal ("Get $5 for Free — Claim Now") is JS-triggered on
  load** across most pages in the live reference and is not part of the
  persistent page design. It inflates a naive whole-page pixel diff by ~3
  points on every page it appears on; score it as a documented ceiling
  exclusion (crop the modal's box out of both sides before diffing), not as a
  mirror defect.
- One BTC-page icon (`/api/file/download/<id>`, no file extension) is served
  from an authenticated-looking internal file API rather than a static CDN
  path and was not captured by the asset mirror: renders as a broken image.
  Minor, isolated, not investigated further this pass.

## What was achieved

Four pages mirrored (homepage, `/price` overview, `/price/BTC` exemplar,
`/fee`), 486 assets (147MB), 0 scripts remaining, 0 off-origin runtime
requests (measured via CDP `performance.getEntriesByType('resource')` on all
four pages), 0 unresolved live references to the reference origin (one inert
mention in the mirror's own "do not publish" stamp comment). Font gate: pass.
`MEXCSans` renders as a real (non-fallback) face on both sides with matching
canvas-measured widths (825.47px / 1203.59px for shared samples). Pixel
similarity vs the live reference, same viewport, headless Chrome: **home
94.27%, price 94.33%, BTC 91.10%, fee 96.27%** (whole-page, raw); with the
transient promo-modal box excluded as a documented ceiling: **home 97.09%,
price 97.20%, BTC 93.70%** (fee had no modal in its reference capture). The
BTC page is the one page that stays meaningfully below the others even after
that adjustment, because its price chart is a JS-only canvas and one icon
asset didn't mirror (both accepted trade-offs of the safety-motivated
script-strip, not unexplained defects).
