# systo-you-own-the-ai

**Callable as: Systo Own/Operate** (aliases: systo hero ad, you own the AI, systo capabilities card)

Capability ad for Systo, an AI-operator service: one headline claim, a hero scene
of a human operating an AI console, and four capability cards carrying the tool
logos behind each service. Measured 2026-09-01.
Source: 2048x1152, 1.778 (16:9). Origin: AI-generated (Bloom), single flat PNG.

## Fidelity — spec

Every reused element carries a measured box, a measured tilt and a sampled surface
colour. A recut can be built from this entry without re-opening the source, except
for the pixels themselves, which the source still has to supply.

## Composition — claim, proof-of-human, capability ladder

Reads logo → headline → hero → capabilities. The headline makes the claim
("You own the AI. We operate it."), the hero *proves the human* — a person's hand
on a physical dial, badged "Human-checked" — and the four cards discharge the
promise into named services with recognisable third-party logos as evidence.

The focal point is the glowing dial under the operator's hand. It is the only
saturated warm element in an otherwise cream field, and everything else defers to
it. **Any recut that covers or clips the dial loses the argument of the image.**

Structural move worth stealing: capability cards float *beside* the hero in
landscape, overlapping nothing. They are a separate reading column, not a caption.

## Frame and grid

Native 16:9, 2048x1152. Cream field with a soft warm radial glow centred around
52% / 60%. Hero scene occupies the left ~64% and bleeds off the bottom and left
edges. Cards occupy a right-hand column starting x≈1340, each ~600 wide.
Headline is optically centred across the upper third, not the full frame — it sits
right of centre to clear the operator's head.

No platform safe zones: built as a standalone 16:9, not for a cropping surface.

## Type

Live in the source, lifted in every recut (see inventory). Geometric grotesque,
heavy weight, tight tracking on the headline. Two-line headline at roughly 96px on
the native 2048 frame, second line in accent orange. Subline roughly 30px, muted
grey, sentence case. Card titles roughly 34px semibold; card body roughly 24px in
two lines at ~1.35 leading.

Scale ratio headline:subline ≈ 3.2:1, headline:card-title ≈ 2.8:1.

## Colour

Sampled, not read from tokens — the render drifts from the brand values.

| Role | Value | Note |
|---|---|---|
| Field, top-left | `#faf4ec` | Gradient origin |
| Field, top-mid | `#f9f2e9` | |
| Field, mid-right | `#f6e8da` | |
| Field, bottom-right | `#e6ddd2` | Gradient terminus |
| **Card surface** | **`#fef8f2`** | Averaged over four interior points. Rebuilt surfaces must use this. |
| Accent (headline, icon discs) | warm orange, approx `#f4501e` | Read from the "We operate it." line |

The card surface is *lighter than the field it sits on*, which is what makes the
cards read as floating. Filling rebuilt cards with white instead reads as flat.

## Element inventory

| Element | Box (l,t,w,h) | Tilt | Class | Notes |
|---|---|---|---|---|
| Wordmark | 30,40,240,80 | 0.00 | liftable | Mark plus wordmark, one unit |
| Headline (2 lines) | 590,92,868,260 | 0.00 | liftable | Must be cut at x<1340 or the first card bleeds a white block into it |
| Subline | 682,340,664,64 | 0.00 | liftable | Sits *below* the card top edge; crop separately from the headline |
| Hero scene | 180,400,1060,752 | n/a | photographic | Operator, dashboard, console, dial, mug |
| Card 1 icon / text / logos | 1372,392,96,96 / 1471,380,244,120 / 1686,386,252,120 | **0.00** | liftable | Content — Adobe, OpenAI, Anthropic |
| Card 2 icon / text / logos | 1370,552,96,96 / 1471,542,234,124 / 1680,552,260,124 | **0.72** | liftable | Growth — Meta, Google Ads, HubSpot |
| Card 3 icon / text / logos | 1362,716,96,96 / 1461,708,239,126 / 1670,724,272,128 | **2.39** | liftable | Website — WordPress, Webflow, Squarespace |
| Card 4 icon / text / logos | 1344,878,100,100 / 1443,878,244,124 / 1654,894,280,134 | **4.53** | liftable | AI Agents — n8n and two others |
| Card surfaces | — | — | re-authorable | Rebuild at `#fef8f2`, radius ≈ 33 at 1080 width |
| Field and glow | — | — | re-authorable | Rebuild as gradient; never lift |

**The tilt is the trap.** The four cards look identical and are not: the
perspective compounds down the stack, 0.00 → 0.72 → 2.39 → 4.53 degrees, measured
off each shell's top edge between x=1420 and x=1900. Lifted flat, cards 3 and 4
visibly slope. Counter-rotate each by its own angle.

Logo clusters are lifted as one block per card rather than twelve separate tiles,
which preserves the original spacing and rounding for free.

## Photography

Over-the-shoulder shot of a seated operator, left third of frame, facing a dark
console. Floating dashboard panel upper-centre. The dial with its orange ring sits
centre-right at roughly y 820-930; a "Human-checked" badge sits just above it.

Reframing rule: for taller targets crop *tighter on the operator and console*,
never shorter through the middle. The head begins around y=380 and the dial ends
around y=930, so any hero crop must span roughly y 400-950 to keep both. Cutting
below y=944 clips the dial glow, which is the thing the ad is about.

## Ratios produced

| Ratio | Size | What changed | Gotcha |
|---|---|---|---|
| 9:16 | 1080x1920 | Cards moved from right column to a stack below the hero; headline centred; hero full-bleed with feathered top and bottom | Headline crop must stop before x=1340 or it lifts a white block from the Content card |
| 4:5 | 1080x1350 | Same stack, subline dropped, hero cropped to a wider strip, cards compacted to 104px | First attempt clipped the dial behind the first card; hero must end at source y≈944 and the card overlap reduced to ~6px |

## Licence and provenance

Systo's own creative, generated for them. Reuse is unrestricted **for Systo**.

Contains twelve third-party brand marks (Adobe, OpenAI, Anthropic, Meta, Google
Ads, HubSpot, WordPress, Webflow, Squarespace, n8n and two others). Those are
liftable within Systo's own creative as tool attribution. They are **not**
transferable to any other brand's ad built from this composition — a rebrand must
replace the entire logo set with the new brand's actual stack.
