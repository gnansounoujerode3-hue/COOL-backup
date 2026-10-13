# Motion

Raw extraction output is not a spec. Convert it into the form below and confirm
it before building. Vague motion descriptions are what let a rebuild drift.

## Spec template

One block per animation:

```
NAME:      hero headline reveal
TRIGGER:   page load, 200ms after fonts settle
TARGET:    h1 > span (5 spans, split by word)
FROM:      opacity 0, translateY 24px
TO:        opacity 1, translateY 0
DURATION:  700ms
EASING:    cubic-bezier(0.16, 1, 0.3, 1)
STAGGER:   60ms between spans
```

For scroll-triggered motion, replace TRIGGER with offsets:

```
TRIGGER:   scroll
START:     element top hits 85% of viewport height
END:       element top hits 40% of viewport height
SCRUB:     yes — progress tracks scroll position, no fixed duration
```

Those offsets are not optional detail. Something that starts at 85% feels
responsive; the same animation at 50% feels late and sluggish, and the
difference is obvious side by side.

## Easing

Extracted `cubic-bezier` values go in verbatim. When the extraction only yielded
a keyword, or the user is describing motion from memory:

| Character | Curve |
|---|---|
| Fast out, long settle (most modern marketing sites) | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Standard material-ish ease | `cubic-bezier(0.4, 0, 0.2, 1)` |
| Gentle symmetric | `cubic-bezier(0.65, 0, 0.35, 1)` |
| Slight overshoot | `cubic-bezier(0.34, 1.56, 0.64, 1)` |
| Sharp exit | `cubic-bezier(0.4, 0, 1, 1)` |

GSAP's default with no ease specified is `power1.out` ≈ `cubic-bezier(0.25,
0.46, 0.45, 0.94)`; `power2.out` ≈ `cubic-bezier(0.22, 0.61, 0.36, 1)`.

Durations that read as intentional: micro-interactions 120–200ms, element
reveals 400–800ms, section or page transitions 600–1200ms. Past about 1200ms
motion starts registering as latency.

## Springs: use linear(), not a bezier approximation

A cubic-bezier is a single S-curve: it cannot cross itself, so it can't
overshoot and settle. Any real spring or bounce approximated with one loses the
thing that made it feel good.

`linear()` interpolates between an arbitrary list of points, and values outside
0–1 overshoot, which is exactly what a spring does. It has been Baseline since
2024, so it's safe to use without a fallback:

```css
/* generated from a spring, not hand-written */
transition: transform 600ms linear(0, 0.42, 0.94, 1.08, 1.02, 1);
```

Don't write these by hand. Jake Archibald's Linear Easing Generator
(`linear-easing-generator.netlify.app`) takes spring parameters or a JS easing
function and emits the `linear()` string; Chrome DevTools has had an interactive
`linear()` editor since Chrome 114 for tuning what you extracted.

This is the correct answer for Framer Motion's default spring, which has no
cubic-bezier equivalent. Approximating it with `ease-out` is the single most
common way a Framer-built reference gets rebuilt wrong.

## Scroll-driven CSS: usable, not yet Baseline

`animation-timeline: scroll()` and `view()` let you tie animation progress to
scroll with no JavaScript. Status as of mid-2026: Chrome and Edge since 115
(2023), Safari since 26 (threaded in 26.4, accuracy fixes in 26.5). Firefox
stable still has it behind `layout.css.scroll-driven-animations.enabled`, though
it's on by default in Nightly and a named Interop 2026 priority. Global support
sits around 83%, so it is **not** Baseline.

It's still usually the right choice, because the failure mode is "no animation"
rather than "broken page", provided you write it in this order:

```css
/* revealed state is the default, so unsupported browsers show content */
.section { opacity: 1; transform: none; }

@supports (animation-timeline: view()) {
  .section {
    animation: fade-up linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 40%;
  }
}
```

Write the finished state as the default and layer the motion on top. Getting this
backwards (animating from `opacity: 0` with no fallback) hides content
entirely in Firefox stable.

Keep animated properties to `transform` and `opacity`; those run on the
compositor. Animating `width`, `height`, or `margin` triggers layout on every
frame. Don't add `will-change` preemptively; the browser promotes layers on its
own.

`animation-trigger` is Chrome/Edge only. Don't reach for it in a rebuild meant
to work anywhere.

## Translating between libraries

**GSAP ScrollTrigger → CSS.** A non-scrubbed trigger (fires once, plays through)
maps cleanly onto `IntersectionObserver` plus a class toggle. A scrubbed one
(progress tied to scroll position) needs `animation-timeline: view()` or a
scroll listener driving a custom property. Don't rebuild a scrubbed animation as
a triggered one. The feel is completely different.

**Framer Motion → CSS.** `whileInView` is `IntersectionObserver`. Variants with
`staggerChildren` become `transition-delay` computed per index. `layout`
animations have no CSS equivalent: they need FLIP or the View Transitions API.
Springs go through `linear()`, per above.

**Lenis / Locomotive.** These smooth the scroll itself. If the reference feels
weighty and slightly delayed as you scroll, that's the library, not the
animations; no amount of easing work on individual elements reproduces it.
Either pull in Lenis or tell the user native scroll is what you're shipping.

## Reduced motion

Every build gets this, whether or not the reference has it:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Make sure end states stay reachable: anything animating in from `opacity: 0`
must still end up visible when motion is suppressed. Writing the revealed state
as the default (as in the `@supports` pattern above) gets you this for free. A
reduced-motion user staring at a blank page is worse than the animation was.
