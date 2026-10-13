# youtube.com

**Callable as: YouTube** (aliases: youtube, yt)

Consumer video platform, logged-out desktop homepage, dark theme.
Captured 2026-07-29 @ 1280×720. Stack: Polymer web components (`ytd-*`), asset
build `cd0ebe65`. **Rebuild path**: client-rendered, mirror not available.

## Type: rem against a 10px root

`html { font-size: 10px }`, so every token below is authored in rem where 1rem = 10px.
Recognising this first saves a lot of confusion.

| Step | Size | Leading (default / tall) |
|---|---|---|
| display-l | 6.4rem | 7.8 / 9.0 |
| headline-l | 3.6rem | 4.4 / 5.0 |
| headline-m | 2.8rem | 3.4 / 3.8 |
| headline-s | 2.4rem | 3.0 / 3.2 |
| headline-xs | 2.0rem | 2.4 / 2.8 |
| body-xl → body-xs | 1.8 / 1.6 / 1.4 / 1.2 / 1.0rem | size + 0.4rem |

Steps: 10 → 12 → 14 → 16 → 18 → 20 → 24 → 28 → 36 → 64. Leading is size + 4px at small
sizes, widening to +8px at display. Weights 300/400/500/700. Body is 400, and anything
that *identifies* a thing (video title, active nav item) steps to 500.

Font: Roboto. YouTube Sans exists for brand only.

## Colour: a tonal alpha system, not opaque greys

| Role | Value |
|---|---|
| base bg | `#0f0f0f` |
| raised / menu | `#212121` / `#282828` |
| text primary / secondary | `#f1f1f1` / `#aaa` |
| CTA (+hover) | `#3ea6ff` → `#65b8ff` |
| brand accent | `#f03` |
| interactive rest / hover | `rgba(255,255,255,.1)` → `.2` |
| search field / border | `#121212` / `#303030` |

**The system is white at 8/10/20% alpha over the base**, so every interactive surface
composites over whatever is behind it. That is what makes the chrome read as one
material. Copying the resolved greys instead of the alphas loses this.

## Layout

- Masthead 56px, container padding `0 16px`. Guide rail 72px fixed; full guide 240px.
- Content offset by margin (`margin: 56px 0 0 72px`), not flow; the rail is fixed.
- Breakpoints: **656px** (search collapses to icon), **792px** (rail appears),
  **876px** (logo gets its 129px), **1312px** (full guide inline).

### The grid is a formula, not a media query

```css
--items-per-row: 4;       /* set once on html, recomputed in JS */
--item-margin: 16px;
--row-margin: 32px;
width: calc(100% / var(--items-per-row) - var(--item-margin));
```

Gap comes from **half-margins on each side** (8+8=16), and the row rhythm (32px) is
exactly 2× the column gap. Column count is a variable the JS writes. Grep for the
variable before assuming a breakpoint ladder exists.

Card: thumbnail `padding-top: 56.25%` (16:9), radius 12px on a 4/8/12 small/medium/large
scale. Title 1.6rem/2.2rem weight 500, `-webkit-line-clamp: 2`. Avatar 36px.

## Motion
**Motion fidelity: partial**. Curves, duration inventory and interaction deltas are complete, and the "nothing moves in space, no scroll-driven motion anywhere" constraint is measured, enough to rebuild the interaction tier. No per-animation mapping.


| Curve | Uses | Role |
|---|---|---|
| **`cubic-bezier(.05,0,0,1)`** | **73** | signature: near-instant departure, long glide |
| `cubic-bezier(.4,0,.2,1)` | 26 | Material standard, secondary |
| `cubic-bezier(.2,0,.6,1)` | 14 | tertiary |

Confirmed by their own token `--yt-live-chat-universal-motion-curve`.
Durations: `.3s` (59), `.5s` (35), `.2s` (31), `.25s` (22), `.15s` (22).

**Character: this is a utility interface.** Keyframes are minimal: `fade-in`, `spinner`,
`simple-shimmer` (opacity 1→.5→1, the skeleton pulse). Nothing moves in space except the
guide drawer and spinners. There is no scroll-driven motion anywhere. A rebuild that adds
reveal-on-scroll or parallax is wrong regardless of how good it looks.

Interaction: background steps `.1` → `.2` alpha on hover; active nav additionally steps
weight 400 → 500. A circular ripple layer (`.stroke` + `.fill`) sits in every icon button.

## Gotchas hit while rebuilding

1. **Feed serves zero items logged-out** (`richItems: 0`, `chips: 0`, scrollHeight = viewport).
   Only the chrome is replicable. Report, don't fill in.
2. **Polymer defers rendering when `document.visibilityState === 'hidden'`.** A headless or
   backgrounded pane stamps nothing. Force visibility before extracting.
3. Obfuscated custom properties (`--t7f4f2c6d54836ce0`) read as `initial` in the raw CSS.
   Resolve them off the live page instead.
4. Leading-icon buttons use **asymmetric padding** (10px left inset vs 16px right).
   Symmetric padding makes them 6px too wide.

## Verification achieved

Chrome rebuild: 14/14 boxes exact, worst delta **0.0px** @1280×720.
