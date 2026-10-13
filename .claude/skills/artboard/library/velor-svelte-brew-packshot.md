# velor-svelte-brew-packshot

**Callable as: Svelte Brew packshot** (aliases: velor pouch, svelte brew, the coffee packshot)

Product packshot for Velor Marketing's Svelte Brew slimming coffee: a single
stand-up pouch, three-quarter view, on a lit seamless sweep. Measured 2026-09-01.
Source: 1664x2080, 0.800 (4:5). Origin: 3D render / AI-generated product mockup.
One of a set of ten near-identical variants.

## Fidelity — partial

Frame, background and subject class are measured. The subject bounding box is
**not** reliably measured — see below. Reframing rules here are stated from the
composition, not from a verified box.

## Composition — one subject, no layout

**This is a SUBJECT creative, not a LAYOUT creative, and that distinction decides
the whole treatment.**

There is nothing to re-lay out. All the type — brand mark, product name, variant
line, ingredient list, weight, manufacturer block — is printed *on the pouch*, in
perspective, as part of the render. It is not a layout element that can move; it
is texture on an object.

So the operations this skill is built around do not apply. Lifting the type would
mean lifting the product. Counter-rotating it would mean un-rotating the pouch.
The correct move for a ratio change here is a **reframe**: crop tighter or extend
the sweep. This is the one case where generative outpainting is the right tool, as
SKILL.md says, because there is no arrangement to preserve.

Recording it is the point. A library of only layout creatives would teach the
skill to reach for a re-layout every time.

## Frame and grid

4:5 at 1664x2080. Subject roughly centred, occupying about the middle half of the
frame, standing on its own contact shadow. Generous headroom above, more footroom
below. No margins, no grid, no safe zones: nothing is aligned to anything except
the subject's own vertical axis.

## Type

All type is printed on the pouch and rendered in perspective. Navy display serif
for the product name, gold letter-spaced sans for the variant, light sans for the
ingredient and manufacturer copy. **None of it is liftable as type** — it is part
of the photograph.

## Colour

Sampled at the four corners, which is how the gradient was found:

| Point | Value |
|---|---|
| Top-left | `#cbbeb4` |
| Top-right | `#cdc0b7` |
| Bottom-left | `#e5dcd3` |
| Bottom-right | `#f0e6df` |

Warm neutral throughout, brightening toward the bottom-right. Brand colours on the
pouch itself: navy and gold on white.

## The background is not flat, and that broke a measurement

Corner values span roughly 40 levels. A first pass at `--bbox` compared every
pixel against a single corner reference, flagged the whole gradient as subject,
and returned 100% of the frame.

Fitting the background as a plane from the border ring fixed the ramp — the fit
came out `197.9 + 0.0069x + 0.0124y`, a **37-level corner-to-corner ramp**,
correctly identified. But the box still over-reports (100% wide at tol 10, 95% at
tol 24) because this sweep is **radially vignetted**, and a plane cannot model
radial falloff. Residuals at the frame edges stay above tolerance.

**Status: the subject box for this creative is not reliably measured.** Set it by
hand, or implement edge-energy segmentation, which is the real fix and is not
built. This entry records the failure rather than a plausible-looking number.

## Reframing rules

Stated from the composition, not from a verified box:

- The pouch's vertical axis is the composition. Any crop keeps it centred.
- Going **wider** (16:9, 1.91:1) means cropping the generous head and foot room.
  Safe: the sweep continues past the frame in both directions.
- Going **taller** (9:16) means extending the sweep, not cropping the sides — the
  pouch is already close to the frame's width. This is the outpaint case.
- Never crop through the contact shadow: it is what puts the product on a surface.

## Ratios produced

None yet. Recorded as a reference class, not as a job.

## Licence and provenance

Velor Marketing's product and packaging. Kyle's client work. Contains Velor's own
brand mark and product copy only — no third-party marks, so nothing here is
entangled with another party's rights. Reusable within Velor work; not
transferable to another brand, where both the pouch and its printed type would
have to be replaced entirely, which means re-rendering rather than re-laying out.
