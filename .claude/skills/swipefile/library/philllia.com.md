# philllia.com

**Callable as: Phillia** (aliases: phillia, philllia)

Captured 2026-07-30. Product/agency site for a "space where ideas get executed".
Next.js + Tailwind, server-rendered (204KB HTML, 14,191 characters of text in the
raw response). Captured for **Adapt**, not Match. The deliverable was a rebrand,
so this entry records the system and none of the content.

## Stack

Next.js, Tailwind utility classes in the markup, and, notably, **no JS
animation library at all**. `window.gsap`, `window.ScrollTrigger`,
`window.Motion`, `window.Lenis` and `window.THREE` are all undefined. Every
transition is CSS, driven from an unusually complete token set. After two Framer
captures where all the motion hid inside a JS bundle, this is the opposite case
and much easier to learn from.

`body { overflow: hidden }` with sections at zero height at capture time: the
page gates itself behind an intro before releasing scroll. Scroll the page fully
before extracting or the section geometry reads as empty.

## Tokens: the architecture is the lesson

59 custom properties, and the motion half is the most reusable token set in the
library so far. Not one duration or curve is left implicit:

```css
--dur-micro: .18s;   --dur-base: .42s;   --dur-slow: .72s;   --dur-marquee: 32s;
--ease-out-expo: cubic-bezier(.16, 1, .3, 1);
--ease-out-soft: cubic-bezier(.22, 1, .36, 1);
--ease-hover:    cubic-bezier(.33, 1, .68, 1);
--ease-swap:     cubic-bezier(.65, 0, .35, 1);
--stagger-tight: 40ms;  --stagger-base: 80ms;  --stagger-loose: .14s;
--shift-sm: 12px;  --shift-md: 24px;  --shift-lg: 48px;
--scale-in: .96;   --scale-hover: 1.02;
```

Four named curves for four *jobs* (reveal, soft settle, hover, swap) rather than
one signature curve reused everywhere. A stagger ladder and a travel ladder mean
"reveal this grid a bit looser" is a token change, not a hand-tuned delay. Copy
this architecture wholesale; the values are cheap to re-derive.

Note the site carries **two palettes**: a warm editorial one
(`--background #f9f4ec`, `--primary #b95b3d`, `--accent #efdcb5`,
`--secondary #cadeca` sage, chart hues) and a separate cooler `--sig-*` set
(`--sig-paper #fbfbf9`, `--sig-ink #12151a`, `--sig-signal #2f6bff`,
`--sig-verified #1f9d6b`, `--sig-slate #5b6472`) with its own display scale
`clamp(2.25rem, 4.6vw, 4.25rem)` at leading `.98` / tracking `-.035em`. Two
design languages coexisting in one stylesheet, worth checking for before
assuming a single system.

Root font-size is a flat **16px**; no fluid rem driver.

## Type

Three families, three roles: **Fraunces** display (20/24/30/48px, weight 400
only), **Geist** UI and body (10–16px, the workhorse at 14px/400 with 60
occurrences), **Geist Mono** for small metadata (10.5/14px). The serif appears
*only* at display sizes, the same discipline measured on osa.framer.website
(Instrument Serif only at 46–54px). Two independent confirmations now.

## Motion character
**Motion fidelity: signature-only**. Two curves with use counts, a duration cluster and a character sentence. The stagger and travel ladders noted in INDEX are a vocabulary, not a mapping.


Durations cluster at 150/200/400ms with a 1200ms outlier; the two highest-count
curves in the stylesheet are `cubic-bezier(.22,1,.36,1)` and
`cubic-bezier(.16,1,.3,1)` (four uses each). Character: quick, soft-landing,
nothing showy; motion supports reading rather than performing. No scroll-jacking
and no smooth-scroll library, so the page feels native.

`prefers-reduced-motion` **is** handled, including Tailwind's
`motion-reduce:animate-none` on the pulse elements. Good, and the opposite of
landonorris.

## Structural pattern

- **Two-class reveal gate**: `reveal-on-scroll` on the section, `reveal-item` on
  the children. Third independent confirmation of the library's strongest
  cross-site pattern (after phenomenonstudio's `.isview` → `.visible`).
- **Border-delimited bands with alternating fill**: `border-t border-border/40`
  plus `bg-card/30` on alternates, `py-24 md:py-32` (96/128px) throughout, and a
  `max-w-3xl` prose measure. 19 sections held together by nothing more than that
  rhythm: no second layout system anywhere. This pacing is most of why the page
  reads unhurried, and it is the cheapest thing here to reuse.
- 3 sticky elements; breakpoint list is tiny: effectively just
  `(max-width: 600px)` plus hover/pointer and reduced-motion queries.

## Note for Adapt work

This site sits squarely on the cream `#f9f4ec` + terracotta `#b95b3d` +
high-contrast-serif combination that `references/adaptation.md` names as the
first AI-default tell. That is a legitimate choice *for this brand*, but it
means an Adapt job that keeps the palette has almost certainly stopped adapting
and started defaulting. Keep the token architecture, the band rhythm, the reveal
gate and the type-role split; re-derive every colour and both faces.

## What was achieved

Captured for Adapt only: no mirror built, no diff number. Extraction covered
tokens, rendered type/colour frequency, easing and duration tallies, breakpoints,
section rhythm and the reveal mechanism. The derived build (a rebrand to a
collaboration tool) lives outside the library, per the rule that mirrors and
artifacts are content and the library is knowledge.
