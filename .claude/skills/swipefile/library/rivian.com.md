# rivian.com

**Callable as: Rivian** (aliases: rivian)

EV manufacturer. Captured 2026-08-16 @ 1440x900, headless Chrome over CDP,
hooks installed pre-load. Path taken: **motion-only capture**, taken as a
second data point on how automotive OEM homepages spend their motion budget,
not as a build donor.

**Scope warning: this entry holds motion only.** No type scale, no palette, no
spacing, no layout was captured. It cannot carry a build on its own; pair it
with a donor that has the proportional systems.

## Motion

**Motion fidelity: partial**

Page height 16,443px: a genuinely long scrolling homepage. **13 animations
kept, 0 zero-duration dropped, and `scrollTriggered: 0`.**

That zero is the finding. On a 16,443px page, across 14 scroll steps, with hooks
installed before the page's own scripts, **not one animation fired on scroll**.
Of the 13: five are `animate-pulse` skeleton loaders in the nav
(`div.animate-pulse.bg-accent`, 2000ms `cubic-bezier(0.4,0,0.6,1)`), two are
1400ms `linear` loops, and the rest are short UI transitions.

Easing by count: `cubic-bezier(0.4, 0, 0.6, 1)` 5 · `linear` 2 · `ease-in-out` 2
· `ease-out` 2 · `cubic-bezier(0.83, 0, 0.17, 1)` 1 · `ease` 1.
Durations: 2000ms x5 · 1400 x4 · 300 x2 · 400 x1 · 500 x1.

`cubic-bezier(0.4, 0, 0.6, 1)` and `animate-pulse` are **Tailwind defaults**,
not authorship. The class names in the captured targets are Tailwind utilities
(`animate-pulse`, `bg-accent`, `col-start-3`, `min-h-[var(--consumer-ui-navbar-toolbar-height)]`).
Read them as framework, the same way FintechX settled the Framer/Motion
defaults question.

`prefers-reduced-motion`: media query **present** (`mediaQueryPresent: true`),
capture ran with reduce off.

## Why the entry exists

Purely to corroborate the cross-site pattern recorded in `INDEX.md`: automotive
OEM homepages are motion-light in CSS because their motion budget is spent on
**video**, not on scroll animation. Polestar measured 8 animations with 1
scroll-triggered; Rivian measures 13 with 0, on a page nearly three times as
long. Against phenomenonstudio's 626 and createstudio's 1427, that is a
different discipline, not a smaller version of the same one.

The practical consequence, and the reason this was worth capturing: **if you are
building a scroll-driven car site, the genre gives you the visual language but
cannot give you the motion system.** Take motion from a `spec`-grade entry and
say so, rather than assuming a car brand's own site will supply it.
