# framer.media (homy.framer.media)

**Callable as: Homy** (aliases: homy.framer.media, framer.media, homy)

Real-estate marketing template: property listings, detail pages, buy/rent
services, testimonials, FAQ. Captured 2026-08-10 @ 1440x900 (crawl + scripted
mirror; also spot-checked @ 1280x800).
Stack: Framer (SSR + React hydration, bundled Motion library, `rolldown`
runtime chunks). **Mirror path**, scripted (`crawl.py` + `build.py`), 21/21
pages, 371 assets, 0 external requests after cleanup.

**Motion, type, colour, radius and section geometry re-captured 2026-08-17
@ 1424x805** over a 14,156px page: real headless Chrome through
`cdp-run.py --pre motion-extract.js`, 14 scroll steps, hooks installed before
load. That pass is what promotes this entry from `none` to `spec`. It ran
against the **rebranded mirror ("Systo Estate")**, so every string reading
`SYSTO`/`ESTATE` in the censuses below is build-side; the sizes, weights,
colours and geometry around those strings are the reference's.

Raw capture JSON, under `E:/New Claude/PC Care/swipefile-builds/systo-electrics/docs/`:
`estate-motion.json` (88 animations), `estate-sections.json` (type/colour/
radius/gap census), `estate-named.json` (56 named layers found, 45 recorded
with geometry). Every number below traces to one of those three.

## Type: one family, and line-height tightens as size climbs

**Switzer carries the entire UI.** Confirmed twice now: 71 of 74 `font-family`
declarations on the 2026-08-10 homepage read, and every meaningful row of the
2026-08-17 runtime census below. **Special Gothic appears exactly once**, the
H1, which is the strictest version of this library's standing display-only
discipline (compare onefin/osa's serif-at-46–54px-only rule).

Faces actually `loaded` at runtime: **Switzer 400 / 500 / 600 / 700 / 900**,
**Special Gothic 700**, **Inter 400**. Declared but `unloaded` (shipped by the
Framer template, never rendered): Plus Jakarta Sans 700, Fragment Mono 400,
Great Vibes 400, Inter 700. The single Inter 400 element is the "Crafted by"
badge. Do not read it as part of the type system.

Runtime census, homepage @ 1424 (n = elements at that exact step):

| Step | Family | px | Weight | Line-height | Tracking | n | Role |
|---|---|---|---|---|---|---|---|
| Body | Switzer | 18 | 500 | 28.8 (**1.6**) | normal | **620** | the workhorse, 620 of ~1000 sampled elements |
| Label / eyebrow | Switzer | 14 | 400 | 22.4 (1.6) | normal | 83 | nav, eyebrows (`PROPERTIES`, `OUR IMPACT`) |
| Section head (H3) | Switzer | 48 | 600 | 67.2 (1.4) | normal | 48 | every section heading on the page |
| Meta | Switzer | 16 | 500 | 25.6 (1.6) | normal | 23 | addresses |
| Stat label | Switzer | 22 | 500 | 30.8 (1.4) | normal | 21 | `TOTAL VALUE` etc. |
| Statement | Switzer | 54 | 500 | 64.8 (1.2) | −2.16px (**−0.04em**) | 20 | the About per-word reveal |
| Card meta | Switzer | 16 | 400 | 22.4 (1.4) | normal | 20 | property names in cards |
| Count-up numeral | Switzer | 48 | 600 | 48 (**1.0**) | −0.96px (−0.02em) | 13 | Our Impact digits |
| Card head | Switzer | 28 | 500 | 33.6 (1.2) | normal | 7 | service card titles |
| Marquee head (H2) | Switzer | 56 | 600 | 78.4 (1.4) | normal | 6 | Highlighted Home word marquee |
| Property title | Switzer | 34 | 500 | 47.6 (1.4) | normal | 4 | featured card titles |
| Service numeral | Switzer | 120 | 500 | 96 (**0.8**) | −5.12px (**−0.0427em**) | 3 | `.01` `.02` `.03` |
| Statement emphasis | Switzer | 54 | 700 | 48.6 (0.9) | −2.16px (−0.04em) | 2 | two emphasised words inside the statement |
| Display (H1) | Special Gothic | 100 | 700 | 100 (**1.0**) | −1px (−0.01em) | 1 | the only Special Gothic element on the page |

Two systems fall straight out of that table and both transfer:

1. **Line-height is a function of size, not a constant.** 1.6 at 14–18px →
   1.4 at 16–56px → 1.2 at 28–54px → 1.0 at 48/100px → **0.9 at 54px/700 and
   0.8 at 120px**. Big type is set tighter than its own em box. Copying an 18px
   body ratio up to the 120px numeral is the single easiest way to get this
   page wrong.
2. **Negative tracking scales in em, so copy the ratio not the px.** −0.02em @
   48px · −0.04em @ 54px · −0.0427em @ 120px · −0.01em @ 100px (Special
   Gothic). Everything at or below 34px is `normal`. Same finding as polestar
   (−0.045em @110px → −0.008em @12px): this is now the second entry
   confirming it, so treat em-scaled tracking as the house pattern rather than
   a per-site quirk.

Root font-size is the flat Framer default, `16px` (no fluid-rem driver on
this site, unlike landonorris/onefin).

Build-side, ignore for design purposes: the 14.5px/800/−0.3px + 6.1px/600/2px
`SYSTO` `ESTATE` pair is this build's own logo lockup. The three 800-weight
`SYSTO` sizes (67.111 / 140.521 / 212.519px, −2px) read as the reference's own
Highlighted Home word marquee with the brand word swapped, so their *sizes*
are reference data and the string is not.

## Layout

- **Breakpoints: 0–809.98 / 810–1199.98 / 1200+**, integer+`.98` edges. This
  is now the *fourth* Framer capture in this library confirming the same
  triad (youtube isn't Framer; createstudio/osa/onefin/homy all are).
  Framer emits one full SSR variant per breakpoint gated by
  `hidden-<hash>` classes, so expect ~3x the "real" DOM node count.
- The 2026-08-17 capture confirms the triad **from the runtime payload rather
  than the stylesheet**: `script[type="framer/appear"]` carries its own
  hash → media-query map: `72rtr7` and `121ozb9` → `(min-width: 1200px)`,
  `1f3ehr3` and `jrq0h9` → `(min-width: 810px) and (max-width: 1199.98px)`,
  `778dr6` and `43eknw` → `(max-width: 809.98px)`. Two hashes per band, one
  per SSR variant pair. Useful because it means **you can read a Framer site's
  breakpoints out of one inline `<script>` without touching CSS.**
- Multi-page site: home, about-us, contact-us, privacy-policy,
  terms-of-service, a `properties` listing, and **15** individual
  `properties/<slug>` detail pages, all nav-reachable, all mirrored (no bulk
  section to scope down; sitemap listed 22, one 404'd `/404` page correctly
  excluded).
- Gap census: `0px` ×90 · **`10px` ×84 · `12px` ×53** · `4px` ×27 · `6px` ×16 ·
  then a long tail (16/7/5/3px ×8 each, 64px ×7, 20/17px ×6, 8px ×5, 24px ×4).
  Two working gaps carry the page; the tail is Framer per-frame drift, not a
  scale.
- Radius census: **`7px` ×54 · `15px` ×32 · `10px` ×19 · `16px` ×19 ·
  `99px` ×11 · `100px` ×10**, tail `8px`/`12px` ×8, `20px`/`2px` ×6,
  `18px`/`9px` ×4, `0px 0px 10px 10px` ×3, `38px` ×3. **14 distinct values.**
  99 and 100 are the same pill intent written twice; 15 and 16 likewise. This
  is the specific thing an Adapt from this entry must tighten (see the gate
  warning below).

## Section architecture: measured, homepage, 14,156px tall

45 named layers carry geometry. The structural spine:

| Band | Top | Height | Position | Ground | What it does |
|---|---|---|---|---|---|
| Hero Section | 0 | 1434 | **sticky** | transparent | H1 at 100px Special Gothic; four absolutely-positioned "Hero Smoke Image" layers (609/978/481/949px tall, up to 1752px wide, wider than the viewport) plus two 464px "Cloud Image" layers overhanging at 1174 and 1304 |
| Our Impact | 1434 | 736 | relative | white | count-ups; digits at 48/600/48 |
| About | 2170 | 965 | relative | `rgb(246,246,246)` | holds **"About Text Reveal", top 2250, 259 tall, 980 wide, `position: sticky`**: the signature, spec'd below. A "Text Reveal ID" layer (2250, 644 tall) is the scroll runway the sticky band tracks against |
| Signature Property | 3135 | 2732 | relative | white | wrapper only |
| Featured Properties | 3452 | 2415 | relative | **`rgb(8,11,15)` ink** | **3 × "Property Card", each exactly 805px tall (= 1.0 viewport), each `position: sticky`, tops 3452 / 4257 / 5062; they stack, they do not scroll past** |
| Our Services | 5867 | 950 | relative | white | `.01 .02 .03` at 120px/500/−5.12px beside one ink-filled expanded card and grey collapsed ones |
| Property Listing | 6817 | 1252 | relative | white | grid, cards 855 tall inside a 1256 container |
| Highlighted Home | 8068 | 2843 | relative | white | **"Sticky Section" 8331, 2500 tall**, containing "Sticky Wrap" 8331 × 805 `position: sticky` and a 282px absolute **"Mask Layer"** at 8593, a 2500px scroll-scrubbed masked reveal with the H2 word marquee (`Explore Homes` / `Live Better` / `Modern Spaces`, each emitted twice) |
| Client Review | 10911 | 897 | relative | white | "Ticker Container" / "Desktop" / "Ticker" all at 11273, 450 tall: the marquee spec'd below |

Content containers are **1320px** wide (Our Impact, About, Services, Listing)
with an inner **1256px** rail; the hero's is 1320 too. Full-bleed bands run the
full 1424.

Below 11,808px the capture records no named band for the remaining ~2,348px.
The heading census confirms a FAQ ("Things You Should Know") and a closing CTA
("Discover homes designed for your lifestyle") live there, both 48/600/67.2
like every other section head, plus the footer.

**The structural idea in one line:** three of the nine bands are sticky, and
each does something different with it. The hero pins and is scrolled over,
the three featured cards pin and stack on each other, and the Highlighted Home
band pins for 2500px while its mask animates. This site's whole feel is
`position: sticky` used three ways, not an animation library.

## Colour

Fully **achromatic**: no accent color anywhere. Confirmed twice: the 10
distinct `--token-*` custom properties sampled 2026-08-10, and the runtime
census 2026-08-17.

| Role | Value | Runtime count |
|---|---|---|
| Ink (primary dark) | `rgb(8, 11, 15)` | 136 text · 34 bg |
| Secondary text | `rgb(75, 91, 99)` | **767 text** · 8 bg |
| Pure black | `rgb(0, 0, 0)` | 905 text |
| Surface, warm grey | `rgb(246, 246, 246)` | 34 bg · 7 text |
| Surface, cool grey | `rgb(245, 245, 245)` | 31 bg · 30 text |
| Paper | `rgb(255, 255, 255)` | 26 bg · 20 text (`bodyBg` is white) |
| Near-blacks in Framer chrome | `rgb(25,25,25)` ×21 · `rgb(38,38,38)` ×18 | text |
| Hairlines | `rgb(199, 199, 199)` | 3 text |
| Overlays | `rgba(255,255,255,.25/.3/.1/.07)`, `rgba(0,0,0,.2)`, `rgba(11,17,23,.35)` | 1–4 bg each |
| Statement spans, pre-reveal | `rgba(209, 213, 219, 0)` | **43 text**, one per span |

The two facts worth carrying: **`rgb(75,91,99)` is the real body colour, not
black** (767 elements against 136 at ink), and a CTA-button accent is the
obvious place to introduce a hue and the template deliberately doesn't. Reuse
that restraint on an Adapt rather than defaulting to a brand accent.

That last row reconciles a small discrepancy between the two instruments: the
colour census reads the un-revealed statement spans as `rgba(209,213,219,0)`
(exactly 43 of them, one per span), while `motion-extract.js` serialises the
same transition's `from` as `rgba(0,0,0,0)`. Both are alpha 0, so the triplet
is invisible either way, but if you build the reveal, start from
`rgba(209,213,219,0)`, since that is the declared value.

**`rgb(0,0,238)` appears 242 times in the colour census and is not a design
value.** It is the UA default link colour showing through unstyled `<a>`
elements in the *mirror*. Filter it out of any palette derived from this
capture, and see gotcha 11: the design gate scores CTA contrast against it and
reports a failure that does not exist on the reference.

## Motion

**Motion fidelity: spec**

Re-measured 2026-08-17 @ 1424×805, headless Chrome CDP through
`cdp-run.py --pre motion-extract.js`, 14 scroll steps over a 14,156px page.
**88 animations kept, 0 zero-duration rows discarded, 87 scroll-triggered.**
By kind: **87 `CSSTransition`, 1 `Animation`.** Every row below carries target,
trigger, from→to, duration, easing, stagger and scroll offset, so this entry is
buildable without a re-capture.

**Easing: `ease-out` ×87, `linear` ×1. Durations: 400ms ×87, 36857ms ×1.**
That is the whole vocabulary. There is no curve library here, no cubic-bezier,
no `@keyframes`: one bare CSS keyword at one duration, plus a single
long-running linear marquee. Anything you add beyond `ease-out @ 400ms` is
your authorship, not this reference's.

Trigger-offset histogram (viewport % at fire time, from the per-animation
records): **0% ×24 · 8% ×20 · 42% ×19 · 16% ×14 · −8% ×10 · 1400% ×1.**
Note that `estate-motion.json`'s own `triggerOffsets` field lists only four
buckets (`8→20, 42→19, 16→14, −8→10`) because the extractor's `tally()`
helper drops falsy keys, so the **largest bucket (0%, 24 firings) is silently
missing from that field.** Read the histogram off `animations[].
triggerViewportPct`, not off `triggerOffsets`. The `1400%` outlier is the
review ticker, which is simply 14 viewports below the fold when it autoplays;
it is a position, not a threshold.

**Character.** Two things move and nothing else does. A statement paragraph
un-blurs and inks itself in one word at a time as a sticky band tracks scroll,
and a review ticker slides forever. No fades, no scale, no rotation, no
parallax, no hover motion in the record. The three sticky mechanisms that give
the page its feel (hero pin, card stack, masked reveal) produce **zero**
animation rows; they are `position: sticky` plus layout, exactly as
phenomenon's sticky-stacking did. Do not go looking for an animation to
reproduce them.

**Entrance motion does not live in CSS**: Framer runs it from
`script[type="framer/appear"]`, and this page carries two such payloads (the
id→animation map, and the hash→media-query map quoted under Layout). All four
appear targets share one initial `{opacity: 0.001, y: 60}` and one spring:
**`{type: "spring", stiffness: 320, damping: 60, mass: 1}`**. That spring is
**overdamped** (ω₀ = √(320/1) = **17.889 rad/s**, ζ = 60 / (2√(320·1)) =
**1.677**), so it settles with **no overshoot and no bounce**. Record that
loudly: substituting a lively spring (ζ < 1) here is the most likely way to
get the feel wrong while believing you copied the values.

`prefers-reduced-motion`: **`reducedMotion.mediaQueryPresent: false`.** The
reference ships **no** `prefers-reduced-motion` rule at all. This entry cannot
supply one; any build adapting from it must add its own (see gotcha 10).

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| **Statement reveal: ink (43)** | `div.framer-74eks5-container > div.ssr-variant.hidden-1f3ehr3 > div > span:nth-of-type(N)`, N = 1…43 | scroll, inside the sticky "About Text Reveal" band (top 2250, 259 tall, 980 wide) | `color rgba(209,213,219,0)` → `rgb(8,11,15)` | 400ms | `ease-out` | **none in the record**: `delays [0]`, `stagger null`; the ladder is scroll position, not time | spans 1–10 fire at scrollY 1907 / **42%** viewport; spans 10–43 at scrollY 2861 / **−8, 0, 8, 16%**. Fixed-duration one-shots, not scrubbed |
| **Statement reveal: un-blur (44 firings / 43 spans)** | same 43 spans, same tick | scroll, same band | `filter blur(10px)` → `blur(0px)` | 400ms | `ease-out` | none: as above | as above. **One span was caught mid-flight and re-fired** (`blur(10px)→blur(6.48001px)` then `blur(6.48001px)→blur(0px)`), which is why this track has 44 rows for 43 spans, and is direct evidence the transition is interruptible by continued scrolling |
| **Review ticker (1)** | `div.framer-ffzsuh:nth-of-type(1) > div.framer-19qtf58-container > section > ul` (the "Ticker" layer, top 11273, 450 tall) | autoplay at load: `firedAtScrollY: 0` | `transform translateX(0px)` → `translateX(-2580px)` | **36857ms** | `linear` | none | none: time-driven, `iterations: infinite`. Its `triggerViewportPct` of 1400 is where it sits, not when it starts |
| Appear: lead (`i39zze`) | `script[type="framer/appear"]` id `i39zze` | mount (entrance) | `{opacity 0.001, y 60}` → `{opacity 1, y 0}` | spring, no fixed duration (ω₀ 17.889, ζ 1.677; overdamped, no overshoot) | `spring` stiffness 320 / damping 60 / mass 1 | **delay 0** | none: fires on mount |
| Appear: second (`14vijjc`) | appear id `14vijjc` | mount | `{opacity 0.001, y 60}` → `{opacity 1, y 0}` | same spring | same spring | **delay 0.2s** | none |
| Appear: third (`1w84dc4`) | appear id `1w84dc4` | mount | `{opacity 0.001, y 60}` → `{opacity 1, y 0}` | same spring | same spring | **delay 0.2s** | none |
| Appear: fourth (`rsopd1`) | appear id `rsopd1` | mount | `{opacity 0.001, y 60}` → `{opacity 1, y 0}` | same spring | same spring | **delay 0.3s** | none |

The appear ladder is therefore **0 / 0.2 / 0.2 / 0.3s**: four targets, three
steps, with two sharing 0.2s. Not an even ladder; do not regularise it to
0/0.1/0.2/0.3.

**The signature, in build terms.** The statement is split into **43 `<span>`s
= 22 words + 21 separator spans**, and *every* span animates, separators
included, confirmed from the captured `text` field (span 1 `Focused`, 3 `on`,
5 `discovery,`, 7 `built`, 9 `for`, 11 `real`, 13 `choices.`, 15 `We`,
17 `design`, 19 `platforms`, …; even-indexed spans carry `null`). So it is a
**per-word** reveal, not per-character: an important correction, because a
per-character implementation at the same 400ms produces roughly 6× the firings
and reads as noise. Each span carries the same 400ms `ease-out` transition on
two properties at once (`color` and `filter`) with **zero delay**; the
staircase you see is produced entirely by the sticky band advancing through
scroll and stamping spans progressively. Build it that way (a scroll-position
gate per span), not with a `transition-delay` ladder.

**The one known gap in this spec.** The 2026-08-10 pass observed a text band
scaling **12px → 54px** as a function of Lenis's own internal scroll progress
(gotcha 1 below), on what the 2026-08-17 census confirms is this same 54px
statement band. That effect produced **zero animation rows** in the 88: it is
neither a `CSSTransition` nor a Web-Animations `Animation`, so per-frame
inline style writes from Lenis are invisible to this instrument. Treat the
scale as real but unspec'd: the colour/blur reveal above is complete and
buildable, the font-size scrub on the same band is not, and if you need it you
must measure it with wheel-driven sampling (gotcha 1), not with
`motion-extract.js`.

**What deliberately does not move:** the hero (pinned, not animated), the three
featured property cards (sticky stack, no transition), the Highlighted Home
mask band (2500px of pinning, no captured animation), every hover state, and
all type (no weight, tracking or size animation anywhere in the record).

## Template taxonomy

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Property detail | 15 | Hero image, price, sq ft, gallery layout, CTA | Address, photo set, description |
| Marketing page | 5 (home/about/contact/privacy/terms) | Nav, footer | Section composition |
| Listing | 1 (`properties`) | Filter/grid chrome | Card count (15) |

One property-detail page plus the homepage captures the full system; the
other 14 detail pages are template repeats with no new design information.

## Adapt warning: this reference does not clear the house gate

`design-gate.py --mode adapt`, run 2026-08-17 against the served mirror,
returned **NOT DONE with 7 checks failing.** This is the single most useful
thing to know before ordering this reference by name: it is a beautiful page
that fails our own standards, so an Adapt from it is a *correction*, not a
transcription.

| Gate failure | Reading | What an Adapt must do |
|---|---|---|
| Eyebrow count over budget: 2 on 3 resolved sections | real | cut to the budget; the reference double-stacks a label above a heading |
| **Nav 84px tall, measuring 2 rows at 1440** | real | one row, under 80px |
| **8 distinct border-radius values** (census shows 14) | real | tighten to ≤3; `99`/`100` and `15`/`16` are the same intent written twice |
| 4 CTA labels wrapping to 2 lines | real | shorten the label or widen the button |
| **No `prefers-reduced-motion` anywhere** | real, and confirmed independently by `reducedMotion.mediaQueryPresent: false` | add one; the reference cannot supply it |
| 4 CTAs at 2.098:1 (`#0000ee` on `#080b0f`) | **artifact** | this is the mirror's unstyled-link colour (see Colour), not a design decision. Style the links and the failure disappears |

## Gotchas hit while rebuilding

1. **Synthetic `window.scrollTo()` does not drive Lenis-owned scroll effects.**
   Step-scrolling a mirror with `page.evaluate('window.scrollTo(...)')` (the
   standard fix for the library's own documented IntersectionObserver-miss
   gotcha) correctly revealed every IO-gated section but left one Lenis-driven
   scale-text effect frozen at its 0% state (12px instead of 54px) even after
   a full top-to-bottom sweep. Fix/verify: drive real `page.mouse.wheel(0, dy)`
   events instead of `scrollTo` for any page confirmed to carry `class="lenis"`
   on `<html>`. Wheel events land on Lenis's own listener and update its
   virtual position; `scrollTo` doesn't. Confirmed live: 12px before, 54px
   after switching to wheel events on the same page.
2. **A live analytics tag can be an *async* tag build.py's asset pass never
   touches.** `<script async src="https://events.framer.com/script?v=2">`
   survived the mirror untouched: it's a bare external `<script src>`, not a
   `url()`/asset reference build.py's rewrite pass looks for. Grep every
   mirrored page for the site's own analytics domain before calling a build
   clean; don't assume "0 origin refs in the asset scan" covers script tags.
3. **Framer's hydration reverts *static text nodes* you edited in place, not
   just components.** This is a step beyond what this library already knew
   (that Framer re-renders hidden content from its own runtime): editing the
   served HTML's `<title>`, a `meta[content]`, or even an ordinary footer
   `<p>` (a contact email) is not durable. Framer's bundle sets these from
   page-config data baked into its own JS at mount, independent of the HTML
   it hydrates against, and silently overwrites the edit within the first
   render pass. Confirmed live with a raw-HTML vs. live-DOM diff: served HTML
   read the corrected string, `document.title` read the original. Fix: don't
   rely on a static edit for anything Framer might treat as page metadata;
   guard it with a live corrector instead (next gotcha).
4. **A MutationObserver-based text corrector must scope to the mutation
   records, never re-walk the whole document.** First version called a
   full-document `TreeWalker` inside the observer callback on every mutation;
   this page has live count-up/countdown elements that mutate text every
   animation frame, so the callback fired dozens of times a second and each
   one re-scanned the entire DOM. Measured effect: `page.goto()` with
   `wait_until: 'load'` timed out at 30s (never fired) with the naive
   version, and completed in under a second once the callback was rewritten
   to only inspect `mutation.target`/`mutation.addedNodes` from its own
   records. A full sweep is fine at fixed points (init, `DOMContentLoaded`,
   `load`); it must never live inside the observer's own callback.
5. **Anything inserted *inside* `#main` (Framer's hydration root) gets wiped
   on mount if it doesn't match Framer's own render output, including a
   plain `<canvas>`, not just text.** Confirmed with React error #418
   (hydration mismatch) the moment a hand-authored Three.js canvas was
   inserted as a child of `<main id="hero">`. This generalizes the library's
   existing "redefine the svg def, don't touch the `<use>` site" logo lesson
   to injected content generally: build anything new as a sibling *outside*
   `#main` (this site's `#svg-templates` container is one confirmed-safe
   landing spot, sitting immediately after `#main` closes) and self-position
   it against the target element's `getBoundingClientRect()` instead of
   relying on DOM nesting for placement.
6. **A sibling of a `position:static` ancestor can still lose a z-index fight
   to a `position:sticky` descendant inside it, in practice, against the
   plain CSS2.1 painting-order reading.** The new canvas sat as a sibling of
   `#main` with `z-index:0`; `#main` itself is `position:static`, so by the
   spec's painting order (step 3, in-flow non-positioned content, before
   step 6, positioned z-index:0 siblings) the canvas should have painted on
   top of everything in `#main` regardless of what's nested inside it. It
   didn't: `#hero` (`position:sticky`, Framer's own `z-index:1`, nested well
   inside `#main`) painted over it every time, confirmed with a zoomed
   screenshot in a real GPU-accelerated browser (not just a headless one;
   see the false lead below). Fix: give the sibling a z-index that beats the
   *page's* highest relevant z-index directly (`2` here), not `0`. Don't
   trust that a non-positioned ancestor "contains" its positioned
   descendants' stacking for the purpose of a fight against an outside
   sibling.
   - `document.elementFromPoint()` is **not evidence either way** for this
     kind of check if the element in question has `pointer-events:none`
     (as any purely-decorative overlay should): it performs a hit-test,
     which skips non-interactive elements entirely regardless of visual
     paint order, so it will report the same "element underneath" result
     at z-index 0 and at z-index 999999 alike. Diagnose actual paint order
     with a screenshot (zoomed into the exact region), never with
     `elementFromPoint`, whenever `pointer-events:none` is in play.
   - A red herring worth recording precisely because it looked so
     convincing: `renderer.info.render.calls/triangles/points/lines` were
     all correctly non-zero and a same-task `gl.readPixels()` (with
     `preserveDrawingBuffer: true`, since the default `false` clears the
     buffer before a *later* separate `evaluate()` call can read it) showed
     real drawn color/alpha (strong, correct evidence the GL layer itself
     was rendering) and headless Playwright's `page.screenshot()` still
     showed nothing, which pattern-matched this library's existing
     "the in-app browser pane isn't a measurement instrument" finding
     closely enough to nearly get written up as a second confirmed instance
     of it. It wasn't: the *same* real GPU browser that finally revealed the
     globe also showed nothing at `z-index:0`, and correctly showed it the
     moment the z-index changed. API-level rendering evidence is real
     evidence that the GL layer works; it is not evidence about *paint
     order relative to other page content*, which is a separate question
     answerable only by looking at (or hit-testing correctly around) the
     actual composited page.
7. **A correct `href` does not stop Framer's own client router from
   hijacking the click.** build.py rewrote every internal link's `href`
   correctly (confirmed: "Explore Homes" → `href="properties.html"`), but
   clicking it still did a client-side `pushState` to the site's *original*
   pretty URL (`/properties`, no `.html`) and left `#main` nearly empty;
   there's no backend here to resolve that route. Reported live by the user
   as "buttons go to a blank page." Fix: a capture-phase `document` click
   listener (`addEventListener('click', fn, true)`) that resolves the
   nearest `<a>`'s real `href`, calls `stopImmediatePropagation()` to keep
   Framer's bubble-phase handler from ever seeing the event, and forces
   `window.location.href` instead. Applies to every mirrored Framer page,
   not just this one: worth promoting to a general mirror-hardening step
   in `build.py`/`references/mirror.md` rather than a per-site patch next
   time this comes up on a second Framer capture.
8. Also reported live in the same pass: the giant **"Made in Framer"**
   free-plan badge (`#__framer-badge-container`, fixed bottom-right,
   `z-index: calc(var(--infinity,2147480000))`) survives the mirror and
   reads as obviously wrong on a rebranded site. Remove the div outright
   rather than hide it with CSS (its `pointer-events:none` doesn't stop it
   from being visually present). And the hero globe (gotcha 6) initially
   spun with unbounded acceleration under mouse movement: the tilt term was
   added directly to `rotation.y` every frame (`+= targetTiltY * 0.4`)
   instead of eased toward it like `rotation.x` was: an uncapped per-frame
   velocity term. Fix: ease every rotation component toward a target every
   frame, never add a raw pointer-derived value as a velocity.
9. **CMS collection chunk/index `.framercms` files 404 as usual** (23 of 371
   assets): the library's existing `-chunk-`/`-indexes-` pairing gotcha,
   unremarkable here since all property content was already server-rendered
   into the static HTML; the client-side collection loader failing to
   re-fetch doesn't blank anything visible.
10. **This reference ships no `prefers-reduced-motion` rule at all**:
    `reducedMotion.mediaQueryPresent: false` in the 2026-08-17 capture, and
    `design-gate.py --mode adapt` independently failed the same check. The
    signature effect is a 43-span un-blur that fires as a sticky band tracks
    scroll, which is exactly the class of motion a reduced-motion user needs
    disabled. **The entry cannot give you this rule; you must author it.**
    The safe reduction is to drop the `filter` track and the `y: 60` appear
    travel and keep the colour/opacity, since colour changes alone carry no
    vestibular risk.
11. **A mirror's unstyled links poison a colour census and a contrast gate at
    the same time.** `rgb(0,0,238)`, the UA default link colour, is the
    *third* most common text colour in this capture at 242 occurrences, ahead
    of the site's actual ink (136), and `design-gate.py` then scored 4 CTAs at
    2.098:1 for `#0000ee` on `#080b0f` and reported a contrast failure the
    reference does not have. Two lessons, both general: filter UA defaults
    (`rgb(0,0,238)`, `rgb(0,0,255)`) out of any palette derived from a mirror
    before ranking it; and when a gate reports a contrast failure on a colour
    that appears in *no* stylesheet, suspect the mirror before the design.
12. **`motion-extract.js`'s own `triggerOffsets` field silently drops the 0%
    bucket.** Its `tally()` helper accumulates with `v && (m[v] = …)`, so a
    `triggerViewportPct` of `0` is falsy and never counted. On this page that
    hid the **largest** bucket: 24 of 87 scroll-triggered firings. The four
    buckets the field does report sum to 63, not 87, which is the tell.
    Always reconcile `triggerOffsets` against a count of
    `animations[].triggerViewportPct` before quoting it; a histogram that
    doesn't sum to `scrollTriggered` is missing its zeros.

## Verification achieved

Full 21-page mirror served locally, 0 external requests, 0 console errors
after the hydration-guard/analytics fixes above. Text/brand-swap verified
against the **live DOM** (not just served HTML) via Playwright, including a
sweep for residual case-insensitive brand mentions (0 found outside an
intentional build-attribution comment). The Three.js hero globe (gotcha 6)
is confirmed visually correct in a real GPU-accelerated browser after the
z-index fix: a zoomed screenshot shows the wireframe globe and pulsing
pins clearly composited behind the hero headline on a fresh page load, not
just under a live debugging patch. No pixel-diff run against the reference
(rebrand target, not a pure Match).

Motion, type, colour, radius, gap and section geometry are all measured as of
2026-08-17 through `cdp-run.py --pre motion-extract.js` at 1424×805
(88 animations, 45 named layers with geometry, ~1000 sampled type elements), and
the spec table above is complete for every animation the instrument can see.
Two things remain honestly unresolved and are flagged in place rather than
papered over: the Lenis-driven 12px→54px font-size scrub on the statement band
produced no animation rows and is **not** spec'd, and no `motion-diff.py` run
has been made against a build from this spec yet, so the spec is verified as a
*measurement* and not yet as a *reproduction*.
