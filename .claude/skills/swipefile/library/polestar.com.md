# polestar.com

**Callable as: Polestar** (aliases: polestar, polestar.com)

EV manufacturer. Captured 2026-08-16 @ 1440x900 (reported viewport 1424x805),
headless Chrome over CDP, `/us/` locale. Path taken: **capture only (Adapt
donor)**, captured as a genre reference for the Systo Cars wrap-studio build,
not rebuilt.

Page height 5,832px. Salesforce Embedded Service chat is bundled (LWC classes,
`--lwc-sidebarWidth`), so a chunk of the custom-property census belongs to that
widget rather than to the design system. Filter `embeddedService*` and `lwc-*`
before tallying or you will conclude the palette is twice its real size.

## Type: one family, one weight, and that is the whole system

**762 of 763 sampled elements are `Polestar Unica` at weight 400.** The single
outlier is a `Times New Roman` node. No second family, no bold, no italic. This
is the most disciplined type system in the library by a wide margin, and it is
worth understanding *why it still reads as hierarchy*: the work is done entirely
by size, line-height and tracking, never by weight.

| Role | Size | Line-height | Tracking (px) | Tracking (em) |
|---|---|---|---|---|
| Display | 110px | 110px (**1.0**) | −4.95 | −0.045 |
| Section | 48px | - | −0.3 | - |
| Sub | 30px | 30px (**1.0**) | −1.2 | −0.040 |
| Body | 16px | 18px (1.125) | −0.3 | −0.019 |
| Caption | 12px | 14px (1.17) | −0.1 | −0.008 |

Two rules fall straight out of that table and both transfer:

1. **Line-height is 1.0 at display sizes and only opens at body size.** 110/110
   and 30/30 are both exactly 1.0; body is 1.125. Setting display type at 1.2
   is the single most common way a rebuild of this genre looks soft.
2. **Negative tracking scales with size, and it scales in `em`, not px.**
   −0.045em at 110px down to −0.008em at 12px. Copying the px values instead of
   the ratio gives you type that is too tight at small sizes and too loose at
   large ones. Same principle as phenomenonstudio, measured independently here.

Self-hosted `.woff2` at `/shared-assets/fonts/polestar-unica/`.

## Colour: a green-shifted graphite ramp, no true neutral

```
--signalWhite   rgb(236,236,231)   warm off-white, NOT #fff
--greyWhite     #d9d9d6
--greyNurse     rgb(200,201,199)
--agatheGrey    rgb(177,179,179)
--stormGrey     rgb(117,120,123)
--ironGrey      rgb(83,86,90)
--ironGrey60    rgb(109,111,115)
--graphiteBlack rgb(16,24,32)      near-black with a BLUE cast, NOT #000
--graphiteBlack60/15               alpha variants of the same ink
--graphiteBlackWhite15 #343b41
--offlineRed    #e03c31            status only
--onlineGreen   #00e676            status only
```

The ink is `rgb(16,24,32)`: blue-shifted, exactly the same move
phenomenonstudio makes at `rgb(8,13,16)`. **Two independent premium sites, both
refusing `#000`.** The greys are subtly green/warm-shifted rather than neutral,
which is the same idea landonorris uses more aggressively. Nothing on the page
is a pure neutral.

There is **no brand accent in the UI at all**: `offlineRed` and `onlineGreen`
are status indicators inside the chat widget. The product photography carries
all the colour. That is a real option for this genre and worth knowing before
assuming an accent is required.

## Radius and shadow

Radii: `12px` (3 uses), `8px` (1), `50%` (2). Small and few: no pill UI.
Shadows are almost absent: four `0 0 0 1px inset` rings (borders drawn as
shadows) and one real `rgba(0,0,0,0.2) 0 0 18px`. Depth is not part of the
language.

## Motion

**Motion fidelity: partial**

Measured 2026-08-16, hooks installed pre-load via `cdp-run.py --pre`, 14 scroll
steps over 5,832px. **8 animations kept, 0 zero-duration dropped, 1
scroll-triggered.**

That is not a capture failure, and it is the most useful thing in this entry.
Of the 8: four are `pulse` skeleton loaders on `<picture>` placeholders, one is
the OneTrust cookie banner fade, two are loading spinners
(`stroke-dashoffset` + rotate, 3400ms `ease-in-out`, `iterations: infinite`),
and one is a 300ms transition. **There is no reveal layer and no scroll motion
on this page.**

Easing by count: `ease` 4 · `ease-in-out` 3 · `linear` 1.
Durations: 3400ms x2 · 400 x1 · 300 x1.
Only 3 real `@keyframes` exist site-wide, two of them spinners.

The buildable part is the **transition** layer, from the computed census:

| Declaration | Uses |
|---|---|
| `all` | 493 |
| `color 0.2s` | 56 |
| `color 0.2s cubic-bezier(0,0,1,1), opacity 0.15s cubic-bezier(0.65,0,0,1)` | **52** |
| `width 0.3s, height 0.3s` | 48 |
| `color 0.2s, background-image 0.2s` | 43 |
| `opacity 0.2s cubic-bezier(0,0,1,1)` | 32 |

**`cubic-bezier(0.65, 0, 0, 1)` is the signature curve**: hard out, very long
settle. See the cross-site note below; this is the entry's single most reusable
number.

`prefers-reduced-motion: reduce` **is** present in the page CSS (two media
conditions). Capture ran with reduce off, so what it disables is unverified.

## Breakpoints

`768`, `960`, `1248` are the structural three. Also present: `400`, `460`,
`550`, `600`, `1600`, plus `(hover: hover)` / `(pointer: coarse)` pairs and a
`prefers-contrast: more` block. Note the landscape-phone guards
(`max-height: 425px and orientation: landscape`), rare, and a reminder that a
full-bleed hero needs a short-viewport branch.

## Gotchas

1. **Filter the Salesforce chat widget out of every census.** Its `lwc-*` and
   `embeddedService*` rules dominate the `interactionRules` tally: a raw read
   suggests ~40 hover rules where the actual design has a handful.
2. **`liveAnimations` came back empty while `keyframes` was not.** The
   extractor's own note flags this as "the page probably was not scrolled"; on
   this page it is genuinely correct that nothing is running. Do not take the
   empty array as evidence the capture failed; cross-check against the
   `motion-extract` run, which independently found 8.
3. `--base-fontSize: 16px` / `--base-lineHeight: 18px` are chat-widget tokens,
   not the page's type scale. The real scale only shows up in the sampled census.

## What this entry is good for

The **type discipline** (one family, one weight, hierarchy by size/tracking/
line-height), the **blue-shifted graphite ink + warm off-white** pairing, and
the **signature curve**. It is a poor motion donor and cannot carry a build's
reveal layer; take that from phenomenonstudio (spec) instead.
