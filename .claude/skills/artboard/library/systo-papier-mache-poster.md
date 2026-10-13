# systo-papier-mache-poster

**Callable as: Systo papier-mache poster** (aliases: torn paper poster, cut paper
Systo, paper mache mark)

Social poster, 1080x1920 (9:16). The Systo mark exploded to hero scale and built
out of torn, pulped card on a warm sheet, with the headline printed on the same
sheet. Authored 2026-09-01. Origin: **original, no reference** - every element is
drawn, nothing is lifted.

Runnable: `examples/systo-papier-mache/poster.mjs`.

## Fidelity — spec

The script reproduces it exactly (seeded noise throughout, no `Math.random`), so
this entry is a full specification rather than a set of measurements taken off a
picture.

## Why the mark works as the subject

The Systo mark is *already* papercraft geometry: three stacked bars, a beacon dot,
one counter-notch. Enlarging it and tearing it out of card needs no metaphor and
no photograph. **Look for this before inventing a subject** - a mark built from
simple filled shapes usually has a material it wants to be made of.

## Frame and grid

Single left margin at **x=104**, and everything hangs off it: eyebrow, rule, both
headline lines, both sublines, the lockup. Only the URL is right-aligned, as the
opposing corner to the mark.

| Band | y | Content |
|---|---|---|
| Eyebrow | 228 | Mono, letter-spaced 6.5, Flare, with a 78x3 rule under it at 260 |
| Headline | 420, 536 | Arial Black 112, tracking -4, ink |
| *(air)* | 570-740 | Deliberate. Roughly 170px of nothing |
| Art | 742-1270 | Three bars at 156 tall, offset ~186 apart, rotations -2.6 / 1.6 / -1.1 |
| *(air)* | 1270-1440 | Deliberate |
| Sublines | 1466, 1538, 1580 | Georgia italic 40, then Segoe 28 |
| Footer | 1716-1790 | Hairline rule, lockup at 208 wide, URL right |

## The five things that make paper read as paper

1. **Torn contours.** Every edge is a dense polyline (n=520) whose points are
   pushed along their own outward normals by smooth 1D value noise. Three octaves:
   a slow one for lumpy mass (feature 58), a mid one for the tear (17), a fine one
   for fringe detail (5). Cosine-interpolated, never per-vertex random - raw random
   per vertex gives spiky static, not a tear.
2. **A pale core fringe.** Torn card shows its white middle. Draw a cream layer
   beneath a copy of the contour grown outward by a *varying* amount, so the
   fringe widens and narrows the way a real tear does.
3. **Pulp surface.** Two-octave value noise multiplying the fill, plus a gentle
   top-to-bottom falloff so the form reads as rounded mass.
4. **Two shadows.** A tight one (offset 4/9, blur 6) glues the piece to the sheet;
   a wide one (offset 14/30, blur 26) gives it height. Both warm brown `#5E3214` -
   paper never casts a black shadow on paper. One shadow alone always reads as CSS.
5. **Shared tooth.** The sheet's grain goes over *everything* at the end, type
   included. This is what makes the frame read as one photographed surface rather
   than art with type floating above it.

## Four defects, and what each one actually was

**The fringe must share the colour path's own noise.** Generating the core contour
with an independent seed looks equivalent and is not: in places the core sinks
inside the colour layer and the fringe vanishes. The core has to be the *same*
contour plus a varying positive offset. That offset **is** the fringe.

**Pulp must modulate the fill in pixel space.** Overlay-blending a blurred noise
layer does almost nothing - heavy blur collapses uniform noise toward flat grey,
and overlay against mid-grey is close to a no-op. Normalise each octave to unit
standard deviation and multiply the base colour by it.

**A counter-notch is a hole, not a disc.** Built as a torn disc with its own drop
shadow it reads as a cotton ball stuck on the bar. A hole shows the sheet through
the piece and takes an **inner** shadow on the wall nearest the light, computed as
`mask - translate(mask) blurred`, rather than casting one.

**Beware synthesised texture that carries structure.** See below - this one cost
the most.

## Smooth noise: generate it yourself

Both obvious routes to a smooth 2D field are contaminated, and the contamination
is invisible until you measure it:

- **Blurring full-res white noise.** `sharp`'s blur is a box approximation and
  leaves a faint periodic residue. Heavy blur then collapses the real signal, so
  normalising to unit sd amplifies the *residue* rather than the noise.
- **Upscaling a small noise image.** libvips' upscale interpolator leaves a
  period-3 row artifact at every cell size tried, including cells whose scale
  factors are nowhere near integers.

Either one produced a visible ~7-level scanline through every filled shape.

**Diagnostic worth reusing:** take row means down a flat region and compare mean
absolute differences at several lags. A clean field rises monotonically with lag
(nearby rows similar, distant rows less so). The broken field gave lag-1 2.83,
lag-2 2.74, **lag-3 0.29**, lag-4 2.86 - one lag far *below* its neighbours is a
period at that lag. Note the trap: a low lag-3 diff means rows three apart are
nearly identical, which is the artifact, not the absence of it. Misreading that
sign cost a whole diagnostic pass.

**The fix is to interpolate the lattice directly** - random values on a grid,
smoothstep-bilinear between them, roughly twenty lines of JS. No library, no
periodic structure to leak. Use two octaves per scale: a single octave has one
feature size and reads as distinct blobs, mouldy rather than fibrous.

For texture finer than a few pixels, skip interpolation entirely and use per-pixel
grain. It cannot have a period.

## Colour

Warm sheet `#EDDCC4`, ink `#251D14`, torn core `#F4EAD6`. Pieces run brand-true -
Ember `#FF8C4E`, Flare `#FD5836`, Deep `#D84424`, Honey `#FFBE3C`.

Two colour traps, both hit: a dark stop in the vertical falloff at 0.30 opacity
dragged Deep into a muddy maroon, and pulp amplitude high enough to be clearly
visible read as *scorching* rather than texture. Falloff wants to be gentle
(1.035 down to ~0.945) and pulp weights want to be low (0.072 / 0.038 / 0.020).

## Ratios produced

| Ratio | Size | Notes |
|---|---|---|
| 9:16 | 1080x1920 | Native. Authored at full resolution, nothing upscaled |

## Licence and provenance

Entirely Systo's. No third-party imagery, no lifted assets, no reference. The only
external file is Systo's own `brand/svg/systo-lockup-light.svg`. Free to reuse and
to open-source with the skill.

Typography is Arial Black and Georgia Italic, not Bricolage and Newsreader - the
brand faces were not available to the renderer. See [[systo-you-own-the-ai]],
which carries the same substitution.
