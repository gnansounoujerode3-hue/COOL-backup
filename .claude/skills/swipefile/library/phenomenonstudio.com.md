# phenomenonstudio.com

**Callable as: Phenomenon** (aliases: phenomenon studio, phenomenonstudio)

Product design & development studio. Captured 2026-07-30 @ 1440×900.
Stack: WordPress (custom theme `phnmn`) behind Cloudflare. **Mirror path**, scripted variant.

## Type: fluid, pinned to a 1440 design width

The whole scale is `vw`-based, with px fallbacks below 1180px. Do not copy the px
values; copy the vw ratios. That is the system.

| Class | ≥1180px | at 1440 | ≤1180px | Letter-spacing |
|---|---|---|---|---|
| `title--xxxl` | `8.3333vw` | 120px | 60px | - |
| `title--xxl` | `5.5556vw` | 80px | 40px | −0.8px |
| `title--xl` | `4.7222vw` | 68px | 34px | −0.68px |
| `title--l` | `3.3333vw` | 48px | 30px | −0.48px |
| `title--m` | `2.7778vw` | 40px | 28px (weight 440) | - |

Line-height tightens as size grows: 100% at xxxl → 110% → 120% → 125% at body sizes.
Negative tracking scales with size (−0.8 → −0.48), which is why large type reads tight
and small type stays open. **Weight 440** on `title--m`: a variable-font weight, not a
standard 400/500 step.

Fonts: **Bricolage Grotesque** (variable, `opsz` axis) for display, **Albert Sans**
(variable, `wght`) for body. Both self-hosted `.woff2`.

## Layout

- Container: `padding: 0 2.2222vw` (32px @1440) → 24px ≤1180 → 12px ≤992. Max-width `100vw`.
- Content measure: `mw1040` (1040px) caps headline blocks.
- Breakpoints (only two matter): **1180px** (462 rules) and **992px** (335 rules).
  A single `768px` rule exists. Everything else is fluid `vw`.

## Colour

- Ink `rgb(8,13,16)`: near-black with a blue cast, not `#000`.
- Dark sections use that same ink as background; light sections are white.
- Accent: saturated orange on primary CTA. Secondary CTA is a neutral dark fill.
- Section colour alternates light/dark down the page as the primary rhythm device.

## Motion

**Motion fidelity: spec**

Re-measured 2026-07-31 @ 1440×813, headless Chrome CDP, hooks installed before
load, 14 scroll steps over a 22,200px page. **626 animations kept, 1143
zero-duration rows discarded, 583 scroll-triggered.** The open question the
previous pass left (at what viewport offset `.visible` is applied) is now
measured, so this entry carries per-group from→to, duration, easing, delay
ladder, stagger and trigger offset. It is buildable without a re-capture.

**All 626 are `CSSTransition`. Zero CSS `@keyframes`, zero JS-driven
animations.** The entire motion layer is CSS transitions fired by class toggles,
which is exactly what the two-class gate below describes, now confirmed at
runtime rather than inferred from the stylesheet.

Easing by use count at runtime:

| Curve | Firings | Role |
|---|---|---|
| `ease` | 542 | the actual workhorse: the CSS keyword, unmodified |
| `cubic-bezier(0.22, 1, 0.36, 1)` | 84 | signature: hard out, long settle; word reveals only |

Previously recorded as "`cubic-bezier(.22,1,.36,1)` 2 uses, `cubic-bezier(.2,.8,
.2,1)` 1 use". Those were *declaration* counts in the stylesheet. Re-measured
2026-07-31 as **84 firings** for the signature curve, which confirms it, and
**0 firings** for `cubic-bezier(.2,.8,.2,1)`: it is declared but never runs on the
homepage. The correction that matters for a rebuild is the other way round: by
firing count the house default is the bare keyword `ease`, and the signature
curve is reserved for one thing only, the word-by-word headline reveal.

Durations by firing count: **300ms ×490 · 400 ×91 · 800 ×31 · 200 ×14.**
Previously recorded from declarations as `.3s` (71), `.2s` (17), `.4s` (8), `.5s`
(4). Re-measured: `.3s` remains the house default and covers 78% of firings;
`.5s` **never fires**; and **800ms, absent from the declaration census, is
real**, carrying the media reveal. Do not build the 800ms move at 300ms.

Trigger-offset histogram (viewport % at fire, count): 1→38 · 16→35 · 13→22 ·
54→22 · 60→22 · 78→22 · −14→21 · 38→18 · 103→17 · 49→16 · 10→15 · 37→15. There is
no single threshold, because `.visible` is stamped by the site's own observer per
block; the reveal groups have medians of 38–49% and tops near 103%.

Character: short, small, and almost entirely opacity plus 5px of settle, with
two exceptions that carry the whole personality. Headlines split into `.a-word`
spans and rise a **full 100% of their own height** from behind a mask on the
signature curve at an 80ms stagger; media blocks unmask from the centre
(`clip-path: inset(50%)` → `inset(0)`) while simultaneously **un-rotating from
−15°** over 800ms. The header inverts its text and background between light and
dark sections on a 300ms colour transition. Everything else is the 5px gate.

`prefers-reduced-motion`: a `@media (prefers-reduced-motion)` block **is** present
in the page CSS. The capture ran with reduce **off**, so what it disables is
unverified. Verify before claiming this site handles it.

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| Reveal gate: visibility track (239) | `.isview` blocks page-wide | scroll (`.visible` stamped) | `visibility` hidden → visible | 300ms | ease | 100 / 200ms; delays 0, 100, 200, 400 | START −76…554%, median 46%; no scrub |
| Reveal gate: opacity track (95) | same `.isview` blocks | scroll | `opacity 0` → `1` | 300ms | ease | 100 / 200ms; delays 0, 100, 200, 400 | START −49…1190%, median 38%; no scrub |
| Reveal gate: slide track (85) | `.isview.slidetop` | scroll | `translateY(5px)` → `translateY(0)` | 300ms | ease | 200ms; delays 0, 200, 400 | START −43…91%, median 38%; no scrub |
| **Word reveal (84)** | `h2 > span.a-word > span` | scroll | `translateY(100%)` → `translateY(0)` | 400ms | `cubic-bezier(0.22, 1, 0.36, 1)` | **80ms**; delays 0→880 in 80ms steps (12 words) | START 13–103%, median 49%; no scrub |
| Header invert, text → dark (23) | `header.button-after-invert`, nav, `.main-btn-wrap` | scroll past a section edge | `color rgb(255,255,255)` → `rgb(8,13,16)` | 300ms | ease | none | START 0–10% (fires at the header's own position) |
| Header invert, text → light (22) | same | scroll past a section edge | `color rgb(8,13,16)` → `rgb(255,255,255)` | 300ms | ease | none | START 0–10% |
| **Media unmask (11)** | `.animated-media`, `.animated-media-wrapper .video_player.radius-12` | scroll | `clip-path inset(50% round 12px)` → `inset(0px round 12px)` | 800ms | ease | 100 / 200 / 600ms; delays 0, 200, 800, 900 | START −28…79%, median 16%; no scrub |
| **Media un-rotate (11)** | same elements, same tick | scroll | `rotate(-15deg)` → `rotate(0deg)` | 800ms | ease | 100 / 200 / 600ms; delays 0, 200, 800, 900 | START −28…79%, median 16%; no scrub |
| Service-card state (10) | `.services_cards .card.bg--gray`, its `.icon > img` | hover | `visibility` toggle | 200ms | ease | none | none: interaction state |
| Image gate (7) | `.col.flex > a.media_wrap.radius-12 > picture > img` | scroll | `visibility` toggle | 400ms | ease | none | START −26…80% |
| Video-player gate (6) | `.animated-media-wrapper .video_player` | scroll | `visibility` hidden → hidden (no visual delta) | 800ms | ease | none | START 16% |
| Video fade-out (5) | `.video_player video.fullw.isview` | scroll out | `opacity 1` → `0` | 300ms | ease | none; delay 100ms | START −43…554% |
| Header bg → light (5) | `header.button-after-invert`, `a.btn--white` | scroll past a section edge | `background-color rgb(8,13,16)` → `rgb(255,255,255)` | 300ms | ease | none | START 0–1% |
| Header bg → dark (5) | `header.button-white`, `a.btn--white` | scroll past a section edge | `background-color rgb(255,255,255)` → `rgb(8,13,16)` | 300ms | ease | none | START 0–1% |

Tail: 18 further firings. `filter: none → none` ×5, two `width` transitions whose
endpoints are identical (1073.27px and 1378px, delay 100ms), a 200ms copy of the
opacity+slide pair, and one `border-bottom-color`. None carries a visual delta;
they are transition declarations catching a class change.

Trigger caveat for every offset above: the capture scrolls in 14 jumps of
~1586px against an 813px viewport, so each step overshoots by nearly two
viewports and an element can already be up the screen before its reveal is
observed. An observed offset is a **lower bound on how early the reveal fires**;
the true threshold sits at or above the top of each range, near 100% for the
word reveal, i.e. it starts as the headline crosses the fold. Negative offsets in
the ranges are elements observed after they had already scrolled past the top,
not a design decision.

### Scroll-reveal: a two-class gate

```
.isview                     { opacity:0; visibility:hidden; transition:.3s }
.isview.visible             { visibility:visible }
.isview.fadein.visible      { opacity:1 }
.isview.slidetop            { transform:translateY(5px) }
.isview.slidetop.visible    { opacity:1; transform:translateY(0) }
.isview.slidebottom         { transform:translateY(-5px) }
```

Plus `trd01`…`trd20` delay classes in 0.1s steps for stagger, and `.a-word` spans for
word-by-word headline reveals. **Travel is only 5px**: the reveal reads as a settle,
not a slide. Copying this pattern with a 40px travel gets the feel wrong.

Runtime confirms both halves and separates them, which the stylesheet read did
not: the `.isview.slidetop` gate fired 85 times at exactly `translateY(5px)` →
`translateY(0)`, while `.a-word > span` fired 84 times at `translateY(100%)` →
`translateY(0)`. **Two different mechanisms, not one.** The 5px settle is the
site-wide default; 100% masked travel is the headline treatment only, and it is
the only place the signature curve appears. The measured stagger between words is
**80ms**, not a `trd` class. The 0.1s `trd` ladder drives block-level delays
(0/100/200/400ms observed), the 80ms ladder drives words.

### Sticky-stacking choreography: the defining structural pattern

`main.next_block_sticky` + `section { position:sticky; top:0 }` + `*-checker` classes
(`checker-header`, `awards-sticky-checker`, `contact-position-checker`). Sections pin
and the next scrolls over the previous. Section edges carry a decorative notch via a
~80-point `clip-path: polygon(...)` using `calc(50% ± Npx)`, so the notch stays centred
at any width.

The sticky stacking itself produced **no animation rows**. It is layout, driven
by `position: sticky` and the checker classes, with nothing transitioning. Do not
look for a scroll animation to reproduce it.

### What does not move

No scale, no blur, no `@keyframes`, no infinite loop, and **no scrubbed motion
anywhere**. All 626 firings are fixed-duration one-shots, so nothing tracks
scroll position. Type never animates its weight or tracking despite both fonts
being variable. The only rotation on the page is the media block's −15° release;
the only travel over 5px is the headline's masked 100%. Buttons and cards change
colour, not position.

0. **`@font-face` lives in an inline `<style>` block, not `main.css`.** The
   scripted variant was rebuilt from raw HTML with attribute-level rewriting only
   (`src`, stylesheets), so both variable-font URLs stayed absolute → CORS
   silently blocked them → system-font fallback on every headline. Detection trap:
   computed `fontFamily` still reported the right family, and `document.fonts`
   listed the faces. Truth test: `document.fonts.check('440 68px "Bricolage
   Grotesque"')` + canvas width A/B (requested face vs forced `sans-serif`;
   identical widths = fallback rendering). Fixed by sweeping every remaining
   origin URL in the built page; verified 1183.3px vs 1208.3px.

1. **Static mirror renders header-only.** 233 elements sit at `opacity:0` behind the
   `.isview` gate. Fix without running their JS: stamp `visible` into the markup. Their
   own CSS defines the end state. Revealed 182 elements.
2. **44 elements legitimately stay at `opacity:0`.** `.services_section .col .btn-wrap`
   is `position:absolute; opacity:0` by design: hover-revealed. Not a defect; contributes
   no height. Check before "fixing".
3. **Sticky-stacking cannot be faked statically.** With scripts stripped, sections overlap.
   Headline text lands on top of the cards below. This *requires* the scripted variant.
   Measured: height delta 412px → 177px, worst top drift 352.5px → 123.7px, overlap gone.
4. Two assets 404 on their own origin (`sparkle-white.svg`, and the `swiper-bundle.min.css`
   the page links). Not mirror failures.
5. One `<script src>` is emitted with an unrendered PHP tag: drop it.

## Template taxonomy (2026-07-30 crawl, 89 pages)

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Homepage | 1 | - | - |
| Service page | 19 + services index | 12-section spine: dark hero (title--xl + orange CTA pair) → media strip → alternating light/dark feature sections → contact form | copy, section media, mid-page proof stats |
| Industry / SEO landing | ~45 | same spine as service pages, lighter media | keyword-targeted copy, localized titles |
| Case study (`/projects/`) | 6 mirrored of 114 | long-scroll: dark hero with outcome metric in title, ~30 sections, screen-heavy imagery | project imagery, metric numbers, palette accents per client |
| Listing (`/projects/` index) | 1 | card grid + filter chips | - |
| Company / about / contacts | 4 | team grids, awards strips | - |

One design system, four spines. The service and landing templates are the same
skeleton with different copy. Mirroring one of each captures the full system;
the other ~60 pages add content, not design.

## Verification achieved

Scripted mirror: 11/11 sections, 96/96 images, both fonts local, 0 JS errors,
document height within **0.78%** (22,847 vs 22,670px).

Full-site crawl (2026-07-30): **89 pages, 0 errors, 1.1 GB, 862 assets**
(+9,334 cache hits; the dedupe is what makes 89 pages feasible). 12,847 wired
internal links, **0 missing targets**, 0 origin refs remaining in any page.
Fonts verified by width-test on three template types (home, service, case study).
Excluded as bulk: 368 blog/FAQ/tag URLs, ~108 unlinked case studies.
