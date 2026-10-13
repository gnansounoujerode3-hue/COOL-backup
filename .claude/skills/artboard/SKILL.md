---
name: artboard
description: Recut a static creative into other aspect ratios as a real re-layout rather than a crop, rebrand a captured composition with new brand and copy, audit why a creative works, or generate a new one from a compounding library. Use whenever someone shares an image ad, social creative, poster, banner or key visual and wants it in another size, wants it restyled for a different brand, wants to know what makes it work, or wants "one like that". Measures perspective angles and surface colours off the pixels instead of estimating them, lifts type and third-party logos rather than regenerating them, and remembers every composition it studies.
license: MIT
---

# Artboard

Static creative, moved between aspect ratios and brands without falling apart.

A finished ad is a *layout*, not a picture. The elements sit where they do because
of the shape of the frame. Change the frame and the layout has to be rebuilt, or
the thing that made it work stops working. Artboard treats a ratio change as a
re-layout problem, measures whatever it must reuse, and remembers the composition
in a library that compounds.

Sibling skills: `swipefile` does this for websites, `manifesto` for motion. This
is the still-image half. Artboard follows swipefile's library model deliberately.
(Checked, 2026-09-01: `manifesto` has no persistent memory. It measures a
reference, rebuilds it, and forgets. Do not copy that half of its design.)

---

## First: which job is this?

**Recut.** One creative, more ratios. "Make this 9:16." "I need it for stories and
the feed." The frame changes, so the layout changes. → *Steps 0-5 below.*

**Rebrand.** A composition that works, carrying someone else's brand or last
quarter's copy. "Do this but for us." The geometry is reused; the palette, type,
logos and words are replaced. → *Steps 0-5, with §Rebrand.*

**Audit.** No file needed at the end. "Why does this ad work?" "What's the grid?"
Measure, write the library entry, answer from it. An audit feeds the library
exactly like a recut does, and if the creative is already in the library the
audit is a file read. → *Steps 0-2, then §Record.*

**Generate.** No reference at hand. "Make us a launch creative." **Author it, do
not assemble it** - see the rule below, which is the one that decides whether the
result looks designed. → *§Generate.*

If the request is a website, stop and use `swipefile`. If it moves, use
`manifesto`.

### Then: is this a layout or a subject?

Decide this before anything else, because it decides whether the skill applies.

**Layout creative** — elements arranged in a frame: headline here, hero there,
cards down the side. A ratio change *moves* them. Everything below applies.

**Subject creative** — one thing on a background: a packshot, a portrait, a
product on seamless. There is no arrangement to preserve, and any type is printed
*on the object* in perspective rather than laid out. A ratio change is a **reframe**
(crop tighter) or an **outpaint** (extend the background). Almost none of this
skill applies, and reaching for a re-layout produces nonsense.

The tell: could you move one element without moving the others? If no, it is a
subject creative. `library/velor-svelte-brew-packshot.md` is a worked example of
one, including the measurement that failed on it.

---

## The constraint that shapes everything

**You cannot regenerate what you cannot re-author.**

A finished creative contains three kinds of pixel, and they have different rules:

| Kind | Examples | Rule |
|---|---|---|
| **Re-authorable** | Background fields, surfaces, rules, spacing, glows | Rebuild. Cheaper and cleaner than lifting. |
| **Liftable** | Set type, third-party logos, UI screenshots, charts | Lift. Never regenerate. |
| **Photographic** | People, places, product shots, rendered scenes | Lift, and reframe by cropping *tighter*, not by stretching. |

The failure this prevents: handing the whole image to a generative model and
asking for 9:16. Models garble set type and mangle real brand marks, and a
creative carrying twelve third-party logos will come back with twelve
approximations of them. Outpainting is no better for a *layout* — it extends a
scene, it cannot move a card from the right-hand side to underneath.

Generative reframing is right for one narrow case: a photograph with no layout on
it that needs more canvas. Everything else gets rebuilt.

---

## Step 0: Consult the library

`library/INDEX.md` first. If the creative, or its campaign, or a close sibling is
already there, most of Step 1 is a file read.

A library entry is a partial substitute and a scoped one. It carries the
composition *system* — grid, type scale, palette, element inventory, measured
tilts, safe zones. It does not carry assets. If you need the actual logo pixels,
you need the actual file.

---

## Step 1: Measure. Do not estimate.

```bash
node scripts/measure.mjs creative.png \
  --tilt "1420,1900,380,470;1420,1900,545,630" \
  --color "1660,430;1655,470"
```

Three things get measured, every time:

**Dimensions and true ratio.** Printed by default, with the nearest standard
delivery ratio and how far off it is.

**Perspective tilt of every panel you will reuse.** Panels in AI-generated and 3D
creatives are almost never axis-aligned, and the tilt usually *compounds* down a
stack. On the reference creative that produced this skill, four visually similar
cards measured **0.00°, 0.72°, 2.39° and 4.53°**. Lifted flat, the bottom two
visibly sloped. Counter-rotating each by its own measured angle fixed it.
Guessing a single angle for all four would not have.

**The true colour of any surface you will rebuild.** Sample the real interior,
average a few points, and fill with that. Being two or three values off reads as
a faint patch exactly where a lifted element sits.

> Do not skip measurement because the creative "looks straight". A 2° tilt is
> invisible in a source at full width and unmistakable once the element is lifted
> onto a clean field at a different scale.

---

## Step 2: Plan the re-layout on paper

Write the element inventory and the vertical (or horizontal) budget *before*
composing. The budget is what catches an impossible layout early.

```
1080 x 1920 target
  logo        60      y 60..115
  headline   270      y 142..416     lifted, 916 wide
  subline     68      y 422..484     lifted
  hero       766      y 502..1268    lifted, full bleed, bottom feathered
  cards      610      y 1234..1878   4 rebuilt surfaces, contents lifted
  margin      42
```

Three rules that decide most layouts:

1. **Reading order survives; geometry does not.** If the source reads
   logo → headline → visual → proof, the recut reads the same way. What moves is
   where those live.
2. **Elements that were beside each other stack.** This is the whole reason a
   crop cannot do the job.
3. **Prefer downscaling.** A lifted element placed *smaller* than native stays
   crisp. Above about 1.3× native it visibly softens; past 1.6× it looks like
   what it is. If an element must grow beyond that, rebuild it instead of lifting.

Check the target against `docs/platforms.json` before committing. Ratios that
seem reasonable are often not deliverable — see §Delivery reality.

---

## Step 3: Lift and compose

`scripts/lib.mjs` carries the primitives. It is deliberately not a layout DSL:
every creative is laid out differently, and a general schema for "where things
go" collapses on the second real job. Write the layout in plain code beside them.
`examples/systo-own-operate/` is a complete worked one.

```js
import { lift, feather, fadeEdges, bg, surface, place, heightOf } from '../scripts/lib.mjs'

const headline = await lift(SRC, [590, 92, 868, 260], { width: 916, feather: 18 })
const cardText = await lift(SRC, [1461, 708, 239, 126], { tilt: 2.39, width: 312, feather: 12 })
const hero     = await fadeEdges(await lift(SRC, [180, 400, 1060, 752], { width: 1080, feather: 0 }),
                                 { top: 0.06, bottom: 0.26 })
```

**`lift`** crops, counter-rotates by the measured tilt, trims the transparent
margin rotation adds, scales, and feathers. **Always crop with padding** so the
feather has margin to eat.

**`feather`** is the operation that separates a re-layout from a paste-up. Every
lifted element carries a rectangle of its original background; against a new
field that rectangle shows, and if the element was rotated the patch tilts too.

**`fadeEdges`** bleeds a photograph into the page. A photographic element that
stops on a straight horizontal line announces that it was cropped from something.

**`place`** validates every layer against the canvas before compositing and names
the offending layer if one does not fit, because elements grow during de-tilt.

---

## Step 4: Verify by looking, then by measuring

Render, then actually open the file. Three defects are invisible in code and
obvious on screen:

- **Patches.** Faint rectangles where a lifted element sits. Feather radius too
  small, or the rebuilt surface colour is wrong.
- **Slope.** Type that is not level. A tilt was missed or guessed.
- **Clipping the focal point.** The one element the eye goes to, half-covered by
  something stacked over it. On the reference creative, the first card cut across
  the glowing dial that the whole image is about.

Then check the numbers: output dimensions exact, file size within the platform's
limit, and every lifted element at or below ~1.3× its native scale.

---

## Step 5: Record what you learned

Write or update `library/<slug>.md` from `library/TEMPLATE.md`, and append one row
to `library/INDEX.md`. Do it whether the job was a recut, a rebrand or an audit.

The library holds **composition knowledge**: grid, type scale, palette, element
inventory, measured tilts, safe zones, which ratios were produced and what broke.
It does not hold assets, body copy or imagery. Knowledge, not content.

Declare fidelity honestly, the same way swipefile does:

- **`spec`** — every element measured with box, tilt and colour. Licenses a recut
  from the entry without re-opening the source.
- **`partial`** — real values for some elements. Saves most of a re-measure.
- **`signature-only`** — the palette and character. A vocabulary.
- **`none`** — recorded but not measured.

Under-claiming costs one cheap measure pass. Over-claiming silently ships a
crooked layout, and nobody checks a thumbnail closely enough to catch it.

---

## Rebrand

Same pipeline, one addition: the **swap set**. Before composing, list every
element that carries the old identity — wordmark, palette, typeface, product
shots, third-party logos, body copy — and what replaces it.

Anything on that list moves from *liftable* to *re-authorable*: you are not
lifting the old brand's type, you are setting the new brand's. Anything not on
the list stays lifted, because it is the composition you are keeping.

### Density is a visual property. Match it or resize the slot.

The single most expensive mistake in a rebrand is keeping a slot's footprint while
changing how much goes in it.

A tool palette measuring 105x730 holds around twenty icons. Substitute a brand
that has four, keep the footprint, and you get a tall slab with four things
floating in it. It reads as broken, and no amount of colour or type work rescues
it, because the original panel was not communicating twenty *functions* - it was
supplying **texture**, and texture cannot be made from four objects.

When the replacement's element count differs from the original's:

1. **Resize the slot to the new density.** Four icons want about 105x300. Shrink
   it and give the space back to the field.
2. **Supply more content**, if the composition genuinely needs that mass.
3. **Drop the slot** and let another element carry the weight.

What never works is keeping the footprint and stretching the spacing.

### Match opacity and layering, not just position

An element that was translucent recedes; an opaque one in the same box advances
and fights the subject it was meant to sit behind. Copy the original's *behaviour*
as well as its geometry.

The exception: anything placed to **conceal** something must be fully opaque. A
cover at 88% is not a cover, and whatever it was hiding will ghost through it.

Two hard rules:

- **Never ship someone else's brand marks in your creative.** If the reference is
  a competitor's ad, the geometry is fair to learn from; their logo, wordmark and
  product photography are not yours to re-use.
- **A rebrand of a stock or generated creative still inherits its licence.** Check
  before it goes into a paid placement.

---

## Generate

### Authored, not assembled. This is the whole rule.

Everything else in this skill is machinery for *lifting* - crop, de-tilt, feather,
place. That machinery is right for a recut or a rebrand, where an existing
composition is being carried across a frame or a brand. **It is actively wrong for
an original.**

Lifted rectangles dropped onto a field read as collage no matter how well each
piece was measured, and measuring is the seductive part: it feels like progress
while the composition gets worse. If the request is "make one", put the crop tools
down.

What authoring looks like instead, drawn from the build that finally worked:

- **One photograph, not four fragments.** Find the single image that carries the
  whole argument and cut everything that competes with it. If two elements are
  both doing the same job, one of them goes.
- **Feather to the subject's shape, not to a rectangle.** An oval or contour mask
  makes a photograph dissolve into the field as *light*. A rectangular feather
  still reads as a pasted crop with soft corners.
- **Motivate the lighting.** Put the field's warm key directly behind or beneath
  the bright part of the photograph, so the glow in the image reads as the thing
  lighting the frame rather than a gradient that happens to be there.
- **One margin, one alignment.** Hang everything off a single edge - eyebrow,
  rule, every headline line, sublines, the mark. Nothing centred, nothing nudged.
  Inconsistent alignment is the fastest way to look amateur.
- **Negative space is a component, not a gap.** Leave a large, deliberate empty
  region. The urge to fill it with a panel or a badge is exactly the assembling
  instinct, and it is what made every earlier attempt look busy.
- **Reach for the vector brand assets.** A logo cropped out of a raster creative
  brings its background with it and lands as a white sticker on a dark field.
  `brand/svg/*-dark.svg` and `*-light.svg` exist for this.

### Composing from the library

When there is a library to draw on, read N entries, extract the systems that
recur, and re-derive every specific for the new subject.

Say the N out loud. A library of three carries three opinions, not a consensus,
and blending three into an average produces mush. At low N, name the entry you
are leaning on and say so. The honesty is the feature.

---

## Delivery reality

`docs/platforms.json` carries the constraint table, marked `api-verified` or
`documented`. The lines that most often break a plan:

- **Instagram feed crops anything taller than 4:5.** A 9:16 in feed loses roughly
  a third, top and bottom. 4:5 is the correct answer to "make it vertical".
- **Stories render no caption.** Any words must be burned into the image.
- **TikTok cannot take a static image at all.** Note the failure mode: creating a
  draft succeeds and only scheduling rejects it, so verify by scheduling.
- **YouTube has no static post type.** A still creative has no home there.
- **Two posts to the same Page hours apart split its reach.** Separate them.

Produce the smallest set of correct files, not one file stretched everywhere. The
matrix at the bottom of `platforms.json` is the default.

---

## Copying, and where the line is

Learning a composition is normal practice; art directors have always kept swipe
files. Reproducing someone's assets is not.

- **Fine:** grid, ratios, type scale, colour relationships, element hierarchy,
  the structural idea.
- **Not fine:** their logo, their photography, their illustration, their copy,
  their fonts if licensed, or anything that would make a viewer think your
  creative is theirs.
- **The library enforces this by shape.** It stores measurements and patterns and
  refuses assets. If an entry would need an image to be useful, the entry is
  wrong.

When the source is the user's own creative, all of this collapses to: reuse
freely. Most jobs are that.

---

## Failure modes worth watching for

**Assuming the panels are straight.** They rarely are, and the tilt compounds.
Measure every panel, not the first one.

**Feathering into the content.** Radius larger than the padding you cropped with
eats the type. Crop generously.

**Upscaling a lift.** Past ~1.6× native it looks lifted. Rebuild instead.

**Cropping the focal point out.** In a tall recut the hero has less room; crop
*tighter on the subject* rather than shorter through the middle of it.

**Trusting a draft to prove a platform accepts something.** Drafts validate less
than schedules do. Verify with the real action.

**Date filters on UTC timestamps.** An 8:00 PM Eastern post is stored as the
*next day* in UTC. A substring match on the local date silently misses it. This
one cost a real debugging detour; match on parsed local time instead.

**Assuming a lifted crop contains only what you wanted.** This is the root cause
behind most rebrand defects, because crops are rectangular and compositions are
not. On one job it produced four separate bugs: the source's own headline came
along inside a menu crop and ghosted behind the new one; the subject crop carried
the very interface being replaced; a translucent cover let that interface show
through anyway; and an icon mask kept its whole background square.

Before compositing anything, ask what else is inside that rectangle. If the answer
includes something you are replacing, either move the crop boundary off it or
cover it completely.

**Using a colour mask where an alpha mask is needed.** `dest-in` reads the mask's
**alpha**, not its brightness. A thresholded greyscale is opaque everywhere, so
masking with it keeps the entire square; `normalise()` fails differently by
lifting the dark background until the mask is uniformly bright. To turn a bright
shape on a dark ground into a coloured glyph, join the threshold in **as the alpha
channel**, then tint.

**Declaring the job done from a thumbnail.** Patches, slope, seams and empty slabs
all disappear at small scale. Open the full-size file.
