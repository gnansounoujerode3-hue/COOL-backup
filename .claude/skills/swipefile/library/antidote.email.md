# antidote.email

**Callable as: Antidote** (aliases: antidote, antidote.email)

Captured 2026-08-17, portfolio + testimonial sections only (Transfer, not a
full-site capture). Webflow. Path: DOM inspection via CDP at 1280 viewport
(`.logo-wrapper_scrolling`, `.tesimonial_image-grid`).

## Portfolio wall (`section_portfolio`, "brand communication that engages all senses")

Despite Webflow class names implying a marquee (`logo-wrapper_scrolling`,
`logov3_marquee-3`), **this component does not move**: `transform` on the
track measured identical (`none`) across two reads 1.2s apart, and its
`position` is `static`, not `sticky`/`fixed`. No scroll-jacking either. It
is a plain `display:flex; gap:32px` row of cards, wider than the viewport,
simply cropped by the section's container with no scroll affordance shown.
**Motion fidelity: none**. Zero interaction/hover captured on the cards
(no hover swept; treat as static until proven otherwise).

Card = a single `<img>`, no extra wrapper:
- **400 × 901.92px** at 1280 viewport (ratio ≈ 0.4435, a tall single-column
  email-newsletter screenshot, not a website screenshot)
- `border-radius: 8px`
- `box-shadow: rgb(2,0,52) -6px 6px 0px 0px`: a **hard, zero-blur, zero-spread
  offset shadow** (a "sticker" pop), not a soft elevation shadow. Offset is
  left+down (negative x, positive y).
- Gap between cards: 32px

Section: heading "brand communication that engages all senses" is
**PP Neue, 120px/144px line-height, weight 400, lowercase, `rgb(2,0,52)`**
(a deep navy-black, not pure black). Sub-line sits directly under it, same
family at 18.88px, same navy: "put simply, when you look good, we look
good ✨": short, lowercase, one emoji, direct address ("we"). Page
background (not the section itself, which is transparent) is a solid
lavender **`rgb(136,142,255)` / #888EFF**.

## Testimonial collage (`section_testimonials`, "never prompted, always appreciated")

A **flex-wrap masonry, not a grid and not absolute positioning**. The
scattered look is an emergent property of `justify-content: center` on a
wrapping flex row of variably-sized screenshots, nothing more:

```css
.tesimonial_image-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 64px 32px; }
```

Verified by measurement: row 1 holds 2 cards (387px + 585px + 32px gap =
1004.5px, well under the 1138.5px container), row 2's first card sits at
x=250 with only 214px width: 186.75px of empty left margin, which equals
`(container 1138.5 − (214+519+32)) / 2`, i.e. the row's own content is
centered independently of the rows above/below it. No transform, no
rotation, no position:absolute anywhere in this component. Every card is
in normal flow. Card widths in this capture ranged 187–938px (real
screenshots at native aspect ratio, not a fixed card size), each
`border-radius: 16px`, `box-shadow: rgba(0,0,0,.2) 0 2px 5px 0` (soft,
5px blur: a different, gentler shadow language than the portfolio wall's
hard sticker shadow). Same lavender page background carries through.

Section motion: none (not swept for hover/entrance this pass. If a
build wants this section animated, that motion needs to be authored, not
copied from here; nothing scroll- or hover-driven was observed on the
static cards during this capture).

## Reusable pattern

Two genuinely different shadow languages on one page used deliberately:
hard offset ("sticker", 0 blur) for the curated portfolio wall vs. soft
blurred for the candid testimonial screenshots. The harder shadow reads as
"designed object", the softer one reads as "found/screenshotted", which
matches what each section is actually showing.
