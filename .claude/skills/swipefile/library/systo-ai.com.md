# systo-ai.com

**Callable as: Systo** (aliases: systo, systo ai)

Kyle's own site: AI-operators service ("AIO"). Captured 2026-07-30 as the
*content source* of a two-URL Adapt (redesign composed from six library donors).
Stack: React SPA, Vite build, Google Fonts. **Capture path:** rendered-DOM
extraction (raw HTML is a 9KB shell; all 20 sections mount client-side).

## Type: three faces, three registers

| Face | Role | Measured use |
|---|---|---|
| Bricolage Grotesque | carries the whole UI | 12–27px, weights 400/600/700, top of census (38× @12px/400) |
| Newsreader italic | display serif ONLY | 56.32px/400, 22 occurrences (nothing below display size) |
| Space Grotesk | eyebrows/wayfinding caps | 11–13px/600 |

Native OSA-style discipline before we touched it: the serif never leaves
display size. Confirms the pattern a fourth time (osa, phillia, systo).

## Colour: warm editorial, one accent

Ink `#1c1a17` (warm near-black, 833× top of census) · cream ramp `#fff4e8` /
`#f7e7d3` / `#f0dcc4` · accent `#ff532e` (136×) with deep variant `#c62f10` ·
ink alphas .74/.55 for secondary text. Single-accent-over-neutral-ramp
(CreateStudio pattern) with a *warm* ramp instead of grey.

**Correction, 2026-08-18 (measured, not DOM-observed. This capture's
rendered-DOM pass records what the CSS declares, not what it resolves to):**
`#ff532e` accent text on the `#fff4e8` cream background computes to **2.96:1**
contrast (WCAG relative-luminance formula), under the 3:1 floor for large text
and well under 4.5:1 for body text, despite the project's own `BRAND.md`
claiming this pairing "passes WCAG AA for large text." Found while building two
HyperFrames videos from this same brand (`hyperframes-systo-intro`,
`hyperframes-systo-explainer`); `npx hyperframes check`'s contrast audit is
what caught it. Fix used there, verified: `#fa5029` for accent-as-text only
(3.10:1, visually near-identical to `#ff532e`); true `#ff532e` stays correct
for non-text use (fills, gradients, the logo tile). Secondary ink-alpha text
also measured short (72%-opacity ink on cream ≈ 3.8:1); solid `#76706a`
clears 4.51:1. Neither fix is live on the site itself as of this note.

## Structure: 20 sections, narrative spine

hero (word-reveal spans + count-up stats) → marquee → manifesto → problem
(obstruction) → turn (clearing) → operations ×4 → how-it-works hub-and-spoke
(dark stage) → offer/seat pricing → results → work carousel ×8 → team (AI
agents w/ "online" pulse) → named operator → ADAM internal tool → built-with →
receipts (client screenshots) → testimonials → recognition → FAQ ×12 → CTA →
footer. Long-form single-page sales narrative; every section has an eyebrow
label ("The problem", "The turn", "The offer").

## Motion (original site)

**Motion fidelity: partial**

Re-measured 2026-07-31 @ 1440×813, headless Chrome CDP, animation hooks
installed *before* page load. That ordering is the whole story: the earlier pass
saw **0** animations because the hooks went in after the SPA had mounted and
every loop had already started. This pass saw **35**, all `CSSAnimation`, all
`iterations: infinite` bar one.

`scrollTriggered: 0`, and all 35 fired at `scrollY 0`. Read that precisely:
**no reveal layer was measured, and this capture could not have measured one.**
The harness read `pageHeight: 0` (the 20 sections mount client-side, so document
height was still 0 when the scroll plan was computed), `triggerOffsets` came back
empty, and all 14 scroll steps therefore landed at 0. The rows below are exactly
the animations that self-start at load. The word-by-word hero reveal, the
count-ups and the scroll reveals described below remain unmeasured; `scroll
Triggered: 0` is evidence about the capture, not about the site.

Easing by use count: `linear` 21 · `ease-in-out` 9 · `ease-out` 4 · `ease` 1.
**No `cubic-bezier` anywhere in the captured set**: the entire ambient layer
runs on the four CSS keywords.

Durations by frequency: 60000ms ×9 · 5000 ×7 · 2400 ×3 · 4400 ×2 · 5600 ×2 ·
6400 ×2 · then one each at 2200 · 3200 · 4200 · 4500 · 19000 · 21000 · 27000 ·
38000 · 52000, plus one 0ms.

Character: this is an ambient layer, not a reveal layer. Two hero aurora blobs
drift on 21s and 27s cycles, one serif display word takes a 4.5s shine sweep, an
orbit ring and its eight nodes counter-rotate on a matched 60s pair, three
marquees run at 38s and 52s, and each AI-agent portrait runs its own blink/wave
sprite cycle on a deliberately non-harmonic period (4.4 / 5.0 / 5.6 / 6.4s), so
the four faces never blink together. Nothing shares a period; nothing settles.

`prefers-reduced-motion`: a `@media (prefers-reduced-motion)` block **is** present
in the page CSS. The capture ran with reduce **off**, so what that block actually
disables is unverified. Do not assume these loops stop.

From → To is absent on every row: the harness recorded animation name, timing and
target but not `@keyframes` bodies. The names below are the real keyframe
identifiers, so the bodies are one stylesheet read away; that read is the single
cheapest upgrade to this entry.

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| `auroraA` | `#top .hero__aurora > span:nth-of-type(1)` | load | not captured | 21000ms | ease-in-out | none | none: loop, infinite; at −30% |
| `auroraB` | `#top .hero__aurora > span:nth-of-type(2)` | load | not captured | 27000ms | ease-in-out | none | none: loop, infinite; at 53% |
| `shineSweep` | `h1.hero__title .hero__word.serif-italic` (1 word) | load | not captured | 4500ms | linear | none | none: loop, infinite; at 47% |
| `scrollDrop` | `.hero__scroll-hint .hero__scroll-line` | load | not captured | 2200ms | ease-in-out | none | none: loop, infinite; at 94% |
| `marqueeScroll` | `.marquee > .marquee__track` | load | not captured | 38000ms | linear | none | none: loop, infinite; at 106% |
| `auroraDrift` | `section.manifesto > .manifesto__aurora` | load | not captured | 19000ms | ease-in-out | none | none: loop, infinite; at 107% |
| `stack-spin` | `.stack__orbit > .stack__nodes` (ring) | load | not captured | 60000ms | linear | none | none: loop, infinite; at 800% |
| `stack-counterspin` | `.stack__node-arm > .stack__node.glass` ×8 | load | not captured | 60000ms | linear | none (delay 0 on all 8) | none: loop, infinite; at 797–861% |
| `headBob` | `.agent__card .agent__imgwrap` | load | not captured | 4200ms | ease-in-out | none | none: loop, infinite; at 1306% |
| `glowPulse` | `.agent__card .agent__glow` ×3 | load | not captured | 5000ms | ease-in-out | none | none: loop, infinite; at 1307% |
| `statusPulse` | `.agent__status > i` ×3 (the "online" dot) | load | not captured | 2400ms | ease-out | none | none: loop, infinite; at 1307% |
| `rubyBlink` / `rubyWave1` / `rubyWave2` | `.agent__sprite--ruby > img.agent__frame--*` | load | not captured | 5000ms | linear | none | none: loop, infinite; at 1306% |
| `astroBlink` / `astroThumb` | `.agent__sprite--astro > img.agent__frame--*` | load | not captured | 5600ms | linear | none | none: loop, infinite; at 1306% |
| `jekBlink` / `jekWave` | `.agent__sprite--jek > img.agent__frame--*` | load | not captured | 6400ms | linear | none | none: loop, infinite; at 1306% |
| `adamBlink` / `adamSquint` | `.adam__visual .agent__sprite--adam > img.agent__frame--*` | load | not captured | 4400ms | linear | none | none: loop, infinite; at 1589% |
| `headBob` (adam) | `.adam__visual .agent__sprite--adam` | load | not captured | 5000ms | ease-in-out | none | none: loop, infinite; at 1589% |
| `adamRing` | `article.adam .adam__ring` | load | not captured | 3200ms | ease-out | none | none: loop, infinite; at 1595% |
| `lovableScroll` | `#lovable .lovable__marquee > .lovable__track` | load | not captured | 52000ms | linear | none | none: loop, infinite; at 2111% |
| `engageBreath` | `section#contact` | load | not captured | **0ms**, iterations 1 | ease | none | none; at 2358% |

Trigger is `load` on every row; none of these is scroll-gated. The percentages
in the last column are where each element happened to sit in the viewport when
its loop started (the page never scrolled), so they read as a **section map**,
not as scroll offsets: hero at −30…107%, orbit stack ≈800%, agent cards ≈1306%,
ADAM ≈1589%, the second marquee ≈2111%, contact ≈2358%.

`engageBreath` registered with duration 0 and one iteration; it renders nothing.
Either a keyframe whose duration is set at a breakpoint this capture didn't hit,
or dead CSS.

What does not move: everything outside those six regions. Body copy, section
headings, cards, stats, pricing and every button carry **no loop at all**. The
ambient motion is confined to the hero, the marquees, the manifesto wash, the
orbit stack and the agent portraits. Count-ups remain a capture gotcha: the DOM
shows "$0M+"/"0 days", so the *target* values are JS-only and unrecoverable.
Ask the owner rather than inventing them.

## Gotchas

1. **Raw HTML lies about scale**: `curl` shows 316 words; the rendered page
   holds ~2,400+ across 20 sections. SPA shells undercount by ~8×. Always
   extract from the rendered DOM.
2. Count-up targets live only in JS; the DOM's initial "0" values are not
   content. Flag as [NEW COPY: confirm] rather than inventing.
3. Their portfolio includes Phillia. Library entries can be related through
   the user's own client work; check before assuming donors are strangers.

## What was achieved

Redesign built (12 of 20 sections) composed from YouTube/Phenomenon/Lando
Norris/CreateStudio/OSA/Phillia entries (see the project REPORT.md). Font gate
passed, fluid-root formula exact, 16/16 gates + 20/20 items on bottom-jump,
0 remote refs. New reveal-gate hardening discovered: **belt-and-braces interval
sweep** (self-retiring 500ms tick) on top of IO + scroll/resize survives panes
where neither IO nor scroll events fire and pages loaded while hidden
(innerHeight 0 at init). Candidate cross-site hardening for every reveal gate.
