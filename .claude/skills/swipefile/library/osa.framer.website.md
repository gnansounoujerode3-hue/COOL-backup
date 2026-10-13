# osa.framer.website

**Callable as: OSA** (aliases: osa framer)

Captured 2026-07-30. Agency template site built in Framer. Path taken: **mirror
(scripted)**. Second Framer capture in the library, and the value of the first
showed immediately: reusing the hardened Framer `build.py` from
[createstudio.framer.media](createstudio.framer.media.md) produced a homepage at
**99.37% against a 99.46% ceiling on the first build**: inside 0.1 points, with
none of the debugging the first Framer site required.

## Stack

Framer, same shape as createstudio: one `script_main.*.mjs` entry pulling ~30
rolldown chunks, `.framercms` collection data, `type="framer/appear"` payloads
for entrance animation, and `@font-face` in inline `<style>` blocks.

- **Zero `cubic-bezier` in CSS**, again. Confirms the Framer pattern: all motion
  runs through the bundled Motion library in JS, so there is no CSS motion
  signature to extract. Read the appear payloads instead.
- Root font-size a flat **16px**; no fluid rem driver.
- Breakpoints `0–809` / `810–1199` / `1200+` with the same `.98` fractional
  edges. This is Framer's fixed three-tier ladder, not a per-site decision.
  Worth treating as a constant for any Framer capture.

## Tokens

18 UUID-named tokens. The palette is far more chromatic than createstudio's:

- primary blue `#0319ff` / `#0103ec`, with a lighter `#5684ff`
- accents `#b80d7c` (magenta), `#830fbd` (violet), `#048063` (green)
- near-blacks `#000` · `#0f1012` · `#1a1a1a` · `#212121`
- white plus a **white-alpha ramp**: `#ffffff0d` (5%), `#ffffff1a` (10%),
  `#ffffff26` (15%), `#fff9`, `#fffc`

That alpha ramp is the reusable part and confirms a standing cross-site pattern:
dark UIs layer white at low alpha rather than using opaque greys, so every
surface composites over whatever gradient sits behind it. Seen previously on
youtube; here it is doing the same job over a photographic hero.

## Type

A two-family split, sampled by frequency off the rendered page rather than read
from source:

| count | size / weight / family |
|---|---|
| 172 | 16px 500 Satoshi |
| 60 | 14px 400 Satoshi |
| 46 | 14px 500 Satoshi |
| 15 | 20px 500 Satoshi |
| 10 | **54px 400 Instrument Serif** |
| 5 | **46px 400 Instrument Serif** |
| 4 | 72px 500 Satoshi |

Satoshi at 500 carries essentially the whole interface: one weight, sizes
14/16/20/28/32/72. **Instrument Serif appears only at display sizes (46–54px)
and only at weight 400.** That is the entire typographic idea: a single
geometric sans doing all the work, with a high-contrast serif reserved for
headlines. Fragment Mono is also loaded but barely used.

Framer registers metric-compatible "… Placeholder" faces (Satoshi Placeholder,
Instrument Serif Placeholder, Inter Placeholder) to avoid layout shift before
the real font loads. They appear in `document.fonts` and are **not** a mirroring
artifact, but they do mean a naive font A/B can report `differs: false` for a
family that is genuinely loaded, because the placeholder is metric-matched by
design. Probe the display face (Instrument Serif here) where the difference is
unmistakable.

## Motion

**Motion fidelity: partial**

Measured 2026-07-31 @ 1440×813, headless Chrome CDP, hooks installed before load,
14 scroll steps over a 17,378px page. **7 animations total, 0 zero-duration rows
dropped.** Five are infinite tickers; exactly **two** are reveals, and both belong
to the same single paragraph.

**Finding: the entry's stated motion source was not there.** The Stack section
above says entrance motion lives in `type="framer/appear"` payloads and to read
those instead of the CSS. Re-measured 2026-07-31: **`framerAppearCount: 0`**. No
appear payload was present in the document at this viewport. Two readings are
open and the capture cannot separate them: the site changed since 2026-07-30, or
the payloads are emitted only for breakpoints/pages this pass did not hit. Either
way, seven animations on a 17,378px agency page is not the site's real motion
inventory, so fidelity stays at `partial` and this entry does **not** license
building the reveal layer. Re-capture with the appear payloads confirmed present
before trusting any per-element reveal claim.

Easing by use count: `linear` 5 · `linear(baked spring, 180 stops)` 2. The second
is not a hand-authored curve: it is Motion's baked-spring serialisation, a
spring sampled into a `linear()` stop list at one stop per 10ms of duration
(180 stops / 1800ms). Reproduce it by generating a `linear()` from spring
parameters, never by substituting a cubic-bezier. Consistent with the standing
Framer prior: zero `cubic-bezier` in the CSS, all motion in JS.

Durations by frequency: 400000ms ×3 · 122400ms ×2 · 1800ms ×2. Only the 1800ms
pair is a reveal; the two long durations are **ambient loops**: infinite
horizontal tickers whose "duration" is a track length divided by a speed, not a
perceived timing. Derived speeds: 1200px / 400000ms = **3px/s**;
2448px / 122400ms = **20px/s**. Copy the speed, not the duration. The duration
is a function of how wide the duplicated track happens to be.

Character: three logo/marquee rows near 900% of the page run at a crawl (3px/s,
one of the three reversed), a testimonial pair at 20px/s runs in mutual
opposition (−2448px against +2448px), and one paragraph blurs and fades in. The
reveal is a 10px blur release paired with an opacity ramp from Framer's
`0.001`, not `0`, over 1800ms, which is long for a text reveal and reads as a
slow focus-pull rather than a fade.

`prefers-reduced-motion`: **no media query present anywhere in the page CSS.**
The tickers run regardless of the OS setting. A rebuild must add the query;
copying this site's handling means copying its absence.

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| Logo ticker, forward ×2 | `.framer-1jggt1v-container` / `.framer-1nefvk2-container` → `section > ul` | load | `translateX(0)` → `translateX(1200px)` | 400000ms, infinite | linear | none | none: ambient loop; at 885% / 920% |
| Logo ticker, reverse | `.framer-whj237-container > … > section > ul` | load | `translateX(0)` → `translateX(-1200px)` | 400000ms, infinite | linear | none | none: ambient loop; at 902% |
| Testimonial ticker, reverse | `.framer-12u4frq-container > … > section > ul` | load | `translateX(0)` → `translateX(-2448px)` | 122400ms, infinite | linear | none | none: ambient loop; at 1476% |
| Testimonial ticker, forward | `.framer-1b2r3h3-container > … > section > ul` | load | `translateX(0)` → `translateX(2448px)` | 122400ms, infinite | linear | none | none: ambient loop; at 1513% |
| Paragraph reveal: blur | `.framer-bwypwm > p.framer-styles-preset-1onz4t4` | scroll | `blur(10px)` → `blur(0px)` | 1800ms, once | `linear(baked spring, 180 stops)` | none | START 38% of viewport height; no scrub |
| Paragraph reveal: fade | same element, same tick | scroll | `opacity 0.001` → `opacity 1` | 1800ms, once | `linear(baked spring, 180 stops)` | none | START 38% of viewport height; no scrub |

The two reveal rows fire together on one element (`firedAtScrollY: 1183`), so
blur and opacity are one animation authored as two tracks. Run them on the same
timeline, not sequentially.

Trigger caveat for the 38% figure: the capture scrolls in 14 jumps of ~1241px
against an 813px viewport, so each step overshoots by more than a viewport and an
element can already be well up the screen before its reveal is observed. An
observed offset is therefore a **lower bound on how early the reveal fires**;
the true threshold is at or above 38%.

What does not move: on the evidence of this capture, everything else, but that
statement is not trustworthy here, because the missing appear payloads are the
likeliest home of the entrance motion. Treat "does not move" on this entry as
"was not observed moving" until a capture with payloads present says otherwise.

## Gotchas

Two of these were found only because a single page in a 21-page run scored
**9.76%** while its twenty siblings sat at 99.7%+. Both were invisible to the
aggregate and to the homepage.

1. **`href="#"` breaks Framer.** The standard mirroring recipe neutralises dead
   links to `#`, but Framer's anchor component calls
   `document.querySelector(href)`, and `querySelector('#')` raises
   `SyntaxError: '#' is not a valid selector`. On this site that throw stopped
   one page's component tree rendering at all. Neutralise to `#inert`, a valid
   selector that matches nothing and is equally dead as a link target.
2. **The CMS loader issues multi-range requests.** Beyond `?range=a-b` it also
   sends `?range=12650-18880,25241-31599` (comma encoded `%2C`) and expects the
   concatenation of every slice. A server honouring only the first pair returns
   too few bytes and triggers the same fatal `Unexpected response length`, but
   *only* on pages whose collections are large enough to be split, which is why
   it survived the homepage and the first 20 pages.

Everything in the createstudio entry applies unchanged: `new URL()` bases must
stay absolute, rewrite to root-absolute inside module bodies, follow relative
dynamic imports, `.framercms` is a real extension, and the server must honour
`?range=a-b`. Two additions from this capture:

1. **CMS collections come in `-chunk-` / `-indexes-` pairs, and only one name is
   a literal in the bundle.** The sibling is built at runtime by substitution, so
   a scan finds one and the loader 404s on the other; the collection then
   renders empty with no error. Derive the sibling from every chunk you find. A
   derived name that 404s upstream is fine and expected; a *needed* one that is
   missing is not. Two here belonged to collections whose literal lives in a
   page module that is not the homepage, so they had to be pinned by hand after
   reading the mirror's 404s.
2. **The skill's default `AUTH_PAT` skips `/projects/`**, which is right for app
   dashboards and wrong for a portfolio. It silently dropped 5 case-study pages,
   reported as "auth-gated". Check what the pattern actually excluded before
   trusting a crawl's page count, and confirm the pages are public (200, no
   login redirect) before overriding.

Also: a sitemap can list pages that no crawl reaches. Three here
(`/waitlist` and two articles) are unreachable by link-following because the
articles index paginates. Diff the crawl against the sitemap and seed the
remainder rather than assuming link-following is complete.

## What was achieved

21 pages: **100% sitemap coverage**, verified by set-differencing the crawl
against `/sitemap.xml`. 216 assets plus 5 CMS chunks, 35MB. Text layer
**100% identical** across all 21 pages (93,297 characters). Zero live external
references across all 42 built pages. Zero failed requests in the browser.

Homepage 99.37% against a 99.46% ceiling; the ceiling sits below 100% because
the hero runs an animated gradient.
