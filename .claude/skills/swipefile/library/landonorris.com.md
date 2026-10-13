# landonorris.com

**Callable as: Lando Norris** (aliases: lando, landonorris)

Captured 2026-07-30. Official driver site, built by OFF+BRAND on Webflow with a
large custom WebGL + Rive runtime bolted on. Path taken: **mirror (scripted)**.
The raw HTML is fully server-rendered, but the hero, the background, and most of
the character of the site live in the JS layer, so the static variant freezes.

## Stack

Webflow shell (one shared stylesheet, 1171 rules) + a ~1.3MB custom bundle from
`lando.itsoffbrand.io`. Worth knowing before you guess:

- **No GSAP global, no THREE global, no ScrollTrigger.** The bundle name-drops
  gsap.com and rive.app in licence comments, which is misleading; `window.gsap`
  and `window.ScrollTrigger` are both undefined. Motion is CSS transitions on one
  token curve, plus Rive state machines, plus a hand-rolled WebGL renderer.
- `window.landoGL` is the WebGL control surface and it is *fully introspectable*
  at runtime: `landoGL.params.<scene>` exposes every tunable (colours, speeds,
  reveal sizes, livery variant) and `landoGL.assets` exposes every model, HDRI
  and texture URL. Read it before doing any static analysis of the bundle; it
  answers in one call what grepping the minified source cannot.
- Lenis for smooth scroll (`<html class="lenis">`). It owns scroll.
- **dat.GUI ships in production** (hidden). Its `.dg` rules pollute any
  hover/focus-state tally. Filter them out or you will conclude the site has 41
  hover rules when ~12 are actually the design.

## Tokens as a system

61 custom properties on `:root`. The important part is not the values, it is the
rem driver:

```css
--design-unit:  16;
--design-width: 1728;
--fluid-container: clamp(var(--min-width), 100vw, var(--max-width)); /* 992 → 1920 */
--fluid-font: calc(var(--fluid-container) / var(--design-width)
                   * var(--design-unit) * var(--scale-factor));
```

Root font-size is viewport-derived against a **1728px design width**, clamped
between 992 and 1920. Verified: at a 1280 viewport the computed root is
`11.8519px` (= 1280/1728×16). Every `rem` in the type and spacing scale therefore
scales fluidly and stops scaling outside the clamp. This is the single most
reusable idea on the site: the whole scale is one formula, not a breakpoint
ladder.

Type scale (in rem, so multiply by the fluid root):
`impact 7.9375 · h2 4.5 · h1 4 · med 2.76 · h3 2 · reg 1.6 · h4 1.5 · h5 1.2 ·
h6/btn-primary 1 · eyebrow 0.578125`

Note `--text--h2` (4.5) is **larger** than `--text--h1` (4): h1 is not the top of
the scale here; `--text--impact` is, at nearly 2× h2.

Spacing: `mini 1 · container 1.25 · small 2 · med 3 · large 4 · xlarge 5` rem,
`--gap: 1.25rem`, `--section-padding: calc(3.5rem + (var(--gap) * 2))`.
Radius: `small 1rem · med 3rem · large 6.25rem`, an unusually wide range; the
large radius is what gives the pill/lozenge UI its character.

Palette (a warm off-white/green system, not grey-on-white):
`lime #d2ff00` (the signature accent) · `lime-off #b2c73a` · `orange #ff6b00` ·
`dark-green #282c20` · `cream #efefe5` · `white #f4f4ed` · `black #111112` ·
plus a green-tinted neutral ramp (`#ebeee0 → #c8cbbd → #b4b8a5`). Nothing is a
pure neutral; every "grey" is green-shifted.

## Motion signature
**Motion fidelity: signature-only**. Signature curve, duration and character measured. The actual motion budget is spent in WebGL and 8 Rive state machines, none of which were specced.


```css
--cubic-default:     cubic-bezier(0.65, 0.05, 0, 1);
--duration-default:  0.75s;
--animation-default: var(--duration-default) var(--cubic-default);
```

Confirmed by frequency, not by reading one component: of 12 live animations after
a full-page scroll, **7 run at exactly `750ms cubic-bezier(0.65,0.05,0,1)`**. A
slow, heavily back-loaded ease; it leaves fast and settles for a long time.
Secondary curve `cubic-bezier(0.19,1,0.22,1)` (expo-out) appears once.

Character: almost no CSS keyframe animation (only 3 keyframes site-wide, and one
is a 40px loading spinner). The motion budget is spent on the WebGL scene and
Rive state machines instead. Utility UI transitions are a separate, much faster
tier at `100ms ease-in-out`.

**Zero `prefers-reduced-motion` rules.** On a site with a permanent WebGL render
loop, smooth-scroll hijack, and 8 Rive files. Do not copy this part.

## Structural pattern: the runtime-parameterised hero

The hero is not an image or a video. It is a WebGL scene compositing a photo
plane, a `.glb` helmet, and a wireframe shader, with the helmet livery **chosen
at random per page load** from a variant set (`Dark`, `Google`, `Grid`, `Lime`,
`Disco`) and the gold texture revealed along the cursor path
(`REVEAL_DURATION 1.1`, `REVEAL_SIZE 25`, `CURSOR_SCALE 3`).

Consequences that matter for anyone rebuilding or diffing this:

- Texture format is picked at runtime by `innerWidth > 991 ? 'webp' : 'ktx2'`.
  Both sets must be mirrored or narrow viewports 404.
- The scene never idles. `IS_WIREFRAME_ANIMATING: true` with `SPEED: 0.1` runs
  forever, so **the page is not self-consistent between two loads of itself**.
- Every parameter is writable at runtime, which is the only practical way to make
  the hero comparable: pin `VARIANT`, `IS_WIREFRAME_ANIMATING` and
  `SHOW_HELMET_PERMANENTLY` identically on both sides before capturing.

Asset layout: `lando.itsoffbrand.io/gl/{models,hdri,textures,fonts,draco,basis}`
and `assets.itsoffbrand.io/lando/rive/`. Rive files: `btn-ui`, `circuits`, `ln4`,
`mob-landscape`, `page-transition`, `phrases`, `reef`, `signature`.

## Breakpoints

`479 · 497 · 767 · 768 · 991 · 992 · 1920`. The real desktop/mobile split is
991/992 (it also switches the WebGL texture format). 1920 is the top of the fluid
clamp, not a layout change.

## Interaction states

Global focus ring is good and worth stealing:

```css
:where(:focus-visible) { outline: 2px solid var(--color--lime); outline-offset: 2px; }
```

Hover is almost entirely a **fill inversion** on grid rows,
`background-color: var(--color--lime); color: var(--color--black)`, with
`--color--lime-zero` (`#d2ff0000`, lime at zero alpha) used so the transition
animates to transparent in the same hue rather than fading to white. That
zero-alpha-of-the-accent trick is the reusable detail. No `:active` rules at all.

## Gotchas

1. **SRI silently kills the mirror.** Webflow serves the stylesheet with
   `integrity="sha384-…"`. Rewriting its `url()`s changes the bytes, the hash no
   longer matches, and Chrome drops the *entire* stylesheet with no visible
   error; the page renders in Times with `document.fonts.size === 0`. Strip
   `integrity` and `crossorigin` from every `<link>`/`<script>` in the mirror.
   This is the single highest-value line in this file. Note `document.fonts.check()`
   still returns **true** in this state, so only the canvas width A/B catches it.
2. **Parentheses are legal in Webflow filenames** (`Britain-25 (1).webp`). A URL
   regex with `)` in its exclusion class truncates the match, the asset is never
   mirrored, and the reference survives in the page. Allow parens and strip a
   trailing one only when the token does not already end in a real extension.
3. **The runtime builds texture paths from a descriptor**, so no literal string
   for them exists in the bundle. Static analysis found ~20 of them; loading the
   mirror and reading the network log found 13 more. Always do the browser sweep.
4. **Webflow's CMS placeholder 403s** to non-Webflow clients
   (`/plugins/Basic/assets/placeholder.60f9b1840c.svg`). It only appears inside
   `.w-condition-invisible` (display:none) wrappers, so a local 1×1 is fine.
5. **Consent (iubenda) and Klaviyo are commented out** in production markup, so
   no cookie banner to fight, unusually. But the legal pages inject iubenda from
   an *inline* loader via `document.createElement`, which no `<script src>`
   pattern catches. Neutralise third-party hosts at the string level.
6. **`/partnerships` 404s on their own site** while being linked from every
   page's nav. Not a crawl failure; verify before chasing it.
7. Three malformed tokens ship in their CSS and are worth not "fixing" in a
   Match: `--nav-height: calc(3.75rem (var(--gap) * 2))` (missing operator, so
   the variable is invalid), `--gap--med<deleted|variable-…>` (a Webflow
   variable-deletion artifact leaked into the output), and
   `--text--btn-tertiary: .875px` (px where the rest of the scale is rem).

## What was achieved

Full 6-page mirror (the entire design surface; no bulk sections exist), 477
assets, fonts verified loaded by canvas A/B, zero live references to the origin
across all 12 built pages, navigation wired between all mirrored pages.

Measured against the reference with the WebGL scene hidden on both sides (the
deterministic layer) and separately as a distribution for the hero. See the
project's `NOTES.md` for the numbers; the short version is that the static layer
sits at the reference's own self-similarity ceiling, and the hero sits inside the
reference-vs-reference distribution, which is the ceiling for a scene that
randomises its livery every load.

---

# Addendum: the "What's up on socials" fanned deck (2026-07-31, Transfer)

Captured for a Transfer into myRA's /v6. The original entry had the site's
motion signature but never measured this component.

Seven cards share one origin and one base box (**266.66 × 466.66**, aspect
0.571, radius **16.6% of width** = 44.2px); the fan is entirely transform,
measured at 1440:

| step | rotate | scale | tx | ty | z |
|---|---|---|---|---|---|
| 0 | 0° | 1.000 | 0 | 0 | 10 |
| ±1 | ±7° | 0.935 | ±147 | +17 | 3 |
| ±2 | ±14° | 0.850 | ±293 | +53 | 2 |
| ±3 | ±21° | 0.776 | ±400 | +97 | 1 |

Rotation is a clean 7°/step; scale and offset are **not** on any formula.
Transcribe them. Section heading is the site's split register (Mona Sans 32/700
uppercase + the serif line), with the deck bleeding below the fold.

Verified reconstruction check: rotating the base box 21° at scale 0.776
yields exactly the measured 323×412 outer bounding box.

> **⚠ 2026-08-17 CORRECTION: this addendum was wrong about motion.** It
> originally read "No shadow, no transition, no animation, no hover state: it
> is a static fan." **The deck has a scroll-triggered entrance AND a rich
> per-card hover**, both GSAP. The error came from measuring only the settled
> end-state and inferring "static" from a still. See the section below, which
> is read from the site's own bundle source and supersedes that sentence.
> Standing lesson: **never conclude "no motion" from geometry alone**; a
> settled end-state is indistinguishable from a static layout. Confirm against
> the bundle or a runtime tween list before writing "no animation" into an entry.

---

# Addendum 2: the socials deck's REAL motion (2026-08-17, source-read)

**Motion fidelity for this component: `spec`.** Not measured off the DOM;
extracted from `lando.itsoffbrand.io/dev-js/lando.OFF+BRAND.gold-android-fix-03.js`
(search `data-social-callout`, ~offset 1.24MB). This is the authoritative version.

**Correction to the entry's Stack section too:** it says "No GSAP global". True
for `window.gsap`, but **`window.gsapVersions` reports `["3.13.0"]`** and
`window.themeScrollTriggers` exists. GSAP + ScrollTrigger are bundled and used
heavily. Probe `gsapVersions`/`themeScrollTriggers`, not just `gsap`.

## Geometry is in `rem`, and the root font-size is fluid

The single most important correction: the table above is px-at-1440. The source
stores **rem**, against this site's fluid root (`clamp(992,100vw,1920)/1728*16`;
11.8519px at a 1280 viewport). So the whole fan scales fluidly with the
viewport and stops at the clamps. Porting the px values pins it to one width.

Two arrays, switched at `innerWidth <= 991` (x roughly halves; scale/rotation/y
are identical):

| i | scale | rotation | x desktop | x mobile | y | zIndex |
|---|---|---|---|---|---|---|
| 0 | 0.7756 | −21° | −30rem | −15rem | 7.3rem | 1 |
| 1 | 0.8498 | −14° | −22rem | −11rem | 4rem | 2 |
| 2 | 0.9346 | −7° | −11rem | −6rem | 1.3rem | 3 |
| 3 | 1 | 0° | 0 | 0 | 0 | 10 |
| 4 | 0.9346 | 7° | 11rem | 6rem | 1.3rem | 3 |
| 5 | 0.8498 | 14° | 22rem | 11rem | 4rem | 2 |
| 6 | 0.7756 | 21° | 30rem | 15rem | 7.3rem | 1 |

`transformOrigin: "center center"` (**not** a top-biased origin).
Note desktop x deltas are 11/11/8, not linear.

## Entrance (scroll-triggered, fires once)

```js
gsap.set(cards, {x:0, y:"10rem", scale:1, rotation:0,
                 transformOrigin:"center center", opacity:1})
cards.forEach((c,i) => c.style.zIndex = arr[i].zIndex)

gsap.timeline({scrollTrigger:{trigger:wrap, start:"top 90%", once:true},
               onComplete:installHover})
  .to(cards, {y:0, duration:0.8, ease:"power2.out",
              stagger:{amount:0.5, from:"end"}})
  .to(cards, {x:i=>arr[i].x+"rem", y:i=>arr[i].y+"rem",
              scale:i=>arr[i].scale, rotation:i=>arr[i].rotation,
              duration:1.2, ease:"elastic.out(1, 0.75)",
              stagger:{amount:0.2, from:"center"}}, "-=0.4")
```

A closed stack rises 10rem (0.8s `power2.out`, 0.5s stagger **from "end"**),
then **overlapping by 0.4s** fans open (1.2s `elastic.out(1,0.75)`, 0.2s stagger
**from "center"**). `opacity` is 1 throughout: there is no fade, only travel.

## Hover: the part that was missing entirely

Installed only `onComplete` of the entrance. Per-card `mouseenter`/`mouseleave`
plus a container-level `mouseleave`. `E` = centre index = `floor(n/2)`.

For hovered index `N`, each card `z` at distance `T = |z − N|`:

```
h = (z − E)/E          // −1..1 by fan position
p = 1 − |h|            // 1 at centre, 0 at the outermost card
c = 1 + 0.2·max(0, 3−T)  // 1.6 / 1.4 / 1.2 / 1.0 for T = 0/1/2/≥3
```

- **hovered** (`z === N`): `y = base.y − 2.5rem`, `x = base.x` (unchanged),
  `scale = base.scale × 1.08`, **`rotation = base.rotation` (unchanged)**
- **before** (`z < N`): `x = base.x − 8·p·c rem`, `rotation = base.rotation − 3/(T+1)`
- **after** (`z > N`): `x = base.x + 8·p·c rem`, `rotation = base.rotation + 3/(T+1)`;
  the **last** card is special-cased to `x` offset `0` and `y = base.y − 1rem`
- every tween: `duration 0.5`, `ease "elastic.out(1, 0.75)"`, `overwrite:"auto"`,
  placed in the timeline at **`T × 0.02`s**

Reset `D()` returns every card to base with the same 0.5s elastic, staggered at
`|index − E| × 0.02`. Card `mouseleave` resets after a **50ms** debounce (and
only if that card is still the active one); container `mouseleave` resets
immediately with no debounce.

**The behavioural headline, and the thing a still cannot show you:** the hovered
card **does not translate to centre and does not straighten**. It keeps its own
x and its own fan angle, lifts 2.5rem, grows 8%, and *shoves its neighbours
outward*: the fan opens around the pointer. Any rebuild that snaps the hovered
card to centre/rotation-0/scale-1.1 is a different interaction, and reads as a
jump. `overwrite:"auto"` + the 50ms debounce are what keep it from flickering
between adjacent cards; there is no nearest-centre hit-testing anywhere.

## Porting `elastic.out(1, 0.75)` without GSAP

With amplitude 1 and period 0.75, GSAP's `s = p/(2π)·asin(1/a) = 0.1875`:

```js
const elasticOut = (t) =>
  Math.pow(2, -10*t) * Math.sin((t - 0.1875) * (2*Math.PI/0.75)) + 1
// f(0) = 0, f(1) ≈ 1.0005
```

Exact, and usable as a custom easing function in framer-motion's `animate()`,
so the feel ports with no new dependency. Verified end to end against this
spec in headless Chrome: entrance holds, rises on `power2.out`, overshoots the
fan target (x −429 against a −390 target, rot −23 against −21) and settles
exact; hover lift, ×1.08 scale, `3/(T+1)` neighbour rotations and the
last-card special case all reproduce.

**Three porting traps, all measured, none of which raise an error:**

1. **framer-motion does not read a `transform` shorthand string back out of
   the DOM.** It keeps its own record of `x/y/rotate/scale` per element. Seed
   the pre-entrance state with `animate(el, {...}, {duration: 0})`, never
   `el.style.transform = "translate(0px,130px)…"`; with the hand-written
   string framer believed `y` was still 0, saw a target of 0, and applied it in
   one frame, so the closed stack **snapped** instead of rising (y went 130→0
   inside 63ms against a 0.8s tween).
2. **Two `animate()` calls created in the same tick both claim a shared
   property immediately**: the second wins at *creation*, not when its `delay`
   elapses. Both entrance phases animate `y`, so queueing the fan with a delay
   silently destroyed the rise. GSAP is immune because a timeline instantiates
   each tween when the playhead reaches it; reproduce that by scheduling
   *creation* (`setTimeout`), not by passing a delay.
3. **GSAP's `"-=0.4"` is relative to the end of the previous tween INCLUDING
   its stagger**, not its duration. Here that is `0.8 + 0.5 = 1.3`, so the fan
   starts at `0.9s`. Using `duration − 0.4 = 0.4s` starts it while most cards
   are still rising and swallows the first beat.

Occlusion math for anyone re-skinning it (AABB half-extent
`(w·cosθ + h·sinθ)/2`, each card occluded by its inner neighbour): visible
strips are ~164px (±1), ~154px (±2), ~110px (±3) of page width. Design each
flanking card as ONE dominant form anchored to the outer edge and bleeding
inward; anything neatly contained gets guillotined by the neighbour.

Gotcha: the heading text uses a **curly apostrophe** ("what's up"); a
straight-quote regex finds nothing. Match on "on socials" instead.
