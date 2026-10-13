# visual-design-blindfold-poster

**Callable as: Visual Design poster** (aliases: blindfold statue, photoshop poster, the design poster)

Social poster: a blindfolded classical bust under a layered Photoshop interface,
with two-weight display type across the upper third. Measured 2026-09-01.
Source: 736x1308, 0.5627 (9:16). Origin: composite, photographic subject with a
real application screenshot layered over it.

## Fidelity — spec

Element boxes below are measured. Note the native size: **736 wide**. Any delivery
at 1080 is a 1.47x upscale, inside the soft zone, so re-author the field and type
at full resolution and upscale only the photographic and UI pixels.

## Composition — dense chrome, bold type, one subject

Reads type first, then subject, with the interface as texture behind both. The
tool palette and cascading menus are not information; they are **atmosphere**.
They are translucent, monochrome and densely packed, and they unify the frame
because everything sits in one grey range.

The two-weight type move: a heavy sans word over a serif-italic word, the second
offset right and overlapping the first's baseline, both in white with a soft
gradient falloff.

## Frame and grid

9:16 at 736x1308. Toolbar hard left. Menu bar and cascading dropdowns upper
centre-right. Type spans the upper third. Statue fills the lower 60% and bleeds
off the bottom and left.

## Type

Heavy grotesque for "visual", calligraphic italic for "design". White with a
gradient to light grey. The italic's descender crosses into the menu below, which
is what makes the two layers read as one composition rather than two stickers.

## Colour

Entirely monochrome. Near-black field, mid-grey chrome, light grey statue. The
single chromatic element in the whole frame is the menu's **blue selection bar**,
which is why it draws the eye and why it must be dealt with in any recolour.

## Element inventory

| Element | Box (l,t,w,h) | Class | Notes |
|---|---|---|---|
| Tool palette | 60,175,105,730 | liftable | ~20 icons, dense, translucent. **Density matters, see below** |
| Menu bar | 220,140,445,30 | liftable | |
| Dropdown | 265,165,265,460 | liftable | **The display type is baked into this region** |
| Submenu | 520,450,140,105 | liftable | Extends to y550 |
| Statue | 70,554,600,754 | photographic | Crop from y554 or the submenu comes with it |
| Field | — | re-authorable | Dark, softly textured |

## Four failure modes, all one root cause

Every defect in this job came from the same thing: **a lifted crop already
contained the element being placed on top of it.** Cropping is rectangular;
compositions are not.

1. **Baked-in type.** Lifting the dropdown brought the poster's own "visual
   design" with it, ghosting behind the re-authored type. Fix: lift the dropdown
   as two bands that skip the type's y-range (165-203 and 425-625). Costs a small
   gap in the menu, which is cheaper than a double-exposed headline.
2. **The subject carried the chrome.** The statue crop overlaps the toolbar column
   and the submenu, so "replacing" the interface still left it visible inside the
   statue. Fix: start the statue at y554, below the submenu, and cover the toolbar
   column completely.
3. **A translucent cover is not a cover.** The replacement rail was drawn at 88%
   opacity, so the toolbar it was hiding ghosted straight through it. Anything
   placed to *conceal* must be fully opaque.
4. **`dest-in` reads alpha, not luminance.** Building an icon by masking a colour
   with a thresholded greyscale fails: the threshold output is opaque everywhere,
   so the whole square survives. `normalise()` fails differently, lifting the dark
   background until the mask is uniformly bright. The working form joins the
   threshold in **as the alpha channel** (`joinChannel`), then tints.

## Density: the lesson that actually cost the most

The tool palette is **105x730 holding roughly twenty icons**. Substituting a brand
that has **four** icons and keeping the footprint produces a tall black slab with
four things floating in it. It looks broken, and no amount of colour or type work
rescues it.

**When the replacement's element count differs from the original's, the footprint
must change with it.** Options, in order of preference:

- **Resize the slot to the new density.** Four icons want roughly 105x300, not
  105x730. Shrink it and let the field take the rest.
- **Find more content.** If the composition needs that mass, supply enough
  elements to justify it.
- **Drop the slot entirely** and let another element carry the weight.

What does *not* work is keeping the footprint and stretching the spacing. Density
is a visual property in its own right: the original panel reads as *texture*, and
texture cannot be made from four objects.

Corollary: match the original element's **opacity and layering**, not just its
position. The reference's chrome is translucent and monochrome, which is why it
recedes. An opaque slab in the same place advances instead, and fights the subject
it was supposed to sit behind.

## Ratios produced

| Ratio | Size | What changed | Gotcha |
|---|---|---|---|
| 9:16 | 1080x1920 | Rebuilt at 1.47x from native | Menu gap where the type band was skipped |

## Licence and provenance

Not Systo's. A third-party poster, sourced from a social feed, containing a
statue photograph of unknown origin and **Adobe Photoshop's interface**.

The composition is fair to study. Its assets are not reusable: the statue is
someone's photograph, and the chrome is Adobe's product UI. A Systo derivative
must replace both, which is what the rebrand does.
