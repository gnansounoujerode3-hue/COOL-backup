# Reference analysis — pulling insights from what the user shows you

Load this whenever the user supplies a reference — a video link, a file, a
screenshot, "make it like X" — at any stage. Output lands in two places: the
SSOT §2 profile (global direction) and the **reference library** (reusable
catalogued animations).

## Principles

- **A reference is a question, not an instruction.** You extract and itemize;
  the user confirms per item (take / adapt / skip). Never absorb a reference
  wholesale — the user usually wants two attributes of it, not twelve.
- **Extract into the system's vocabulary** — dial estimates, C1 motif names,
  A-law terms, frame counts — so every takeaway is buildable. "Feels premium"
  is not an extraction; "camera ≈2, pacing ≈2, sequential type" is.
- **Catalogue, then confirm.** The library collects everything notable; the
  user's confirmation decides what the project actually uses.
- **Vague name-drops get narrowed first.** "Kinda like Apple" → ask *which
  video*. Deep-analyze only refs the user actually points at.

## How to look

- **Local video files are the PRIMARY path** — ask the user to download and
  drop the file. Vimeo blocks all automated access (yt-dlp OAuth, player
  config 403, fetch = bot page); other hosts rot too. A URL is the fallback,
  not the default.
- **Video URL** → the `watch` skill (frames + transcript).
- **Local video** → ffmpeg: a 1fps contact sheet for structure, plus dense
  bursts (~15fps for 1–2s) around transitions and hero moves — motion shape
  lives in the bursts, not the stills.
- **Images/screenshots** → read directly (photo profile below).

## The segment pass → the reference library

Don't analyze a video as one blob. **Split it into segments at shot/section
boundaries** (visible in the contact sheet), analyze each segment, and
catalogue every notable device as a library entry in
`klik/<project>_ref_library.md`:

```
## L-07 · transition · <ref name> @ 0:14 (≈f420–432)
Type: transition | camera-move | element-move | text-placement | asset-design
What: whip-pan left→right, ~12f, background streaks, incoming scene decelerates
Curve: whip-snap (near-vertical peak, hard landing) · Direction: L→R
Notes: sells continuity between unrelated scenes; needs motion blur at peak
Status: catalogued | CONFIRMED (take/adapt) | skipped
```

- Entry types: **transition · camera-move · element-move · text-placement ·
  asset-design · depth-rig** (parallax/plane constructions; add another type
  only if none fits).
- Every entry: source + timestamp/frames · what happens in plain terms ·
  curve/speed character · direction · duration in frames · status.
- The library is cumulative across all refs in a project — later stages pull
  from it: storyboard transition cards may cite entries by ID ("T 2→3: per
  L-07, adapted to brand palette"), and the execution plan carries the ID so
  the build reproduces the *catalogued* mechanics, not a memory of them.

## Video extraction profile (global summary — fill only rows with evidence)

| Attribute | Read it as | Evidence to cite |
|---|---|---|
| Camera — movement | Per move: type (**push/pull zoom · pan L/R · tilt · orbit · tracking · handheld shake · whip**), specific direction, and magnitude; overall C0 dial estimate | the moves, frame-ranged |
| Camera — speed curve | How each move accelerates: constant · ease-in/out · thin-peak burst · whip-snap; does it resolve into drift or stop dead? | 2–3 frame-counted moves |
| Pacing — curves | The motion vocabulary: smooth bezier · spring/bounce (count the overshoots) · ripple/wave (propagating stagger) · snap · elastic · linear (flag it — A1 bans it for us) | hero entrances/exits |
| Pacing — effects | Recurring motion effects: smear/motion blur, echo/trails, glow pulses, particle garnish, masking reveals | where each appears |
| Pacing — tempo | C0.5 dial estimate: avg shot length, hold lengths, move durations in frames | shot-length sample |
| Parallax & depth | Plane count and what sits on each; relative speeds (fg:mid:bg ratio); direction (lateral/vertical/zoom); camera-driven or autonomous; DOF on parked planes (A5)? Catalogue setups as **depth-rig** entries | one camera/scroll move |
| Transitions | Motifs in C1 terms, frame-counted (also catalogued as L-entries) | 2–3 cuts |
| Typography | Face character, scale, case; sequential vs composed; placement habits (also catalogue notable text-placements) | representative frames |
| Palette | Approximate hexes — **direction only**, never token-grade (screenshot compression shifts color) | sampled frames |
| Choreography | Stagger/chain patterns in A3 terms | one plural-entry moment |
| Density | One-idea-per-beat vs layered | busiest frame |
| Beat relationship | Do cuts/hits land on the grid? | audio + cut timing |
| Signature | The 1–2 devices that make this ref recognizable | name them precisely |

## Photo reference profile (images/screenshots)

| Attribute | Read it as |
|---|---|
| Gradients | Type (linear/radial/mesh), direction, hue span, where used (bg/type/accent) |
| Subject | What it is, treatment (photo/3D/flat/outline), how it's lit |
| Background | Flat/textured/gradient/scene; how it separates from subject |
| Negative space | How much, where it sits, what it's protecting |
| Positioning | Composition: centered/thirds/edge-bleed; alignment grid; margins |
| Type placement | Where text sits relative to subject; scale contrast; overlap or clear |
| Texture & finish | Grain, noise, shadows (hard/soft/none), corner radii, line weights |
| Asset recipes | Any notable asset gets the full decomposition pass (section below) → library entry |

## Asset decomposition (the deep pass for asset-design entries)

Applies to assets seen in video segments AND photo refs — backgrounds,
elements, subjects, frame devices. Don't log "nice background"; log the
**recipe**. Decompose bottom-up:

| Layer | Note |
|---|---|
| Role | background · midground element · subject · frame device · text container |
| Base | shape language (rounded/hard/organic/torn) · fill (flat / gradient type+direction / image) |
| Texture | paper grain · film grain · halftone · noise · fabric · riso — and how applied (blend mode, opacity, scale) |
| Edges | clean vector · outlined (weight) · torn/deckled · rough brush · feathered |
| Warp | subtle wave warp · ripple · skew · perspective tilt — **static or animated (cycle period in frames)** |
| Light | shadow type (hard/soft/inner/none), light direction — consistent across assets? |
| Motion attached | idle behavior (bob, breathe, warp cycle), entrance style |
| Reproduction | how to rebuild it deterministically in Remotion: seeded-noise overlay for grain, sine-offset points / SVG turbulence for wave warps (frame-based, A0), CSS gradient stack, SVG filter — name the technique |

```
## L-12 · asset-design · <ref> @ 0:22
Role: background. Base: organic blob, radial gradient coral→cream.
Texture: paper grain, multiply ~12%, large scale. Edges: torn/deckled.
Warp: subtle wave, animated ~90f cycle. Light: soft drop, top-left.
Motion: slow breathe ±0.5%. Repro: SVG blob + seeded turbulence displacement
(frame-based), grain via seeded noise overlay.
Status: catalogued
```

**When the user has no asset ideas, the library IS the design source.** Take
inspiration heavily: decompose the strongest reference assets, then propose
2–3 asset treatments built from those recipes **recolored to brand tokens**,
and confirm per item before building. Inspiration is ingredient-level — never
trace or copy a reference asset wholesale; rebuild from the decomposed recipe
in the brand's own palette and shape language.

## The confirm step (mandatory)

Present the profile **and the new library entries** as one itemized list —
"which of these do you want?" — take / adapt / skip per item. Then:

- Confirmed profile rows → the SSOT §2 reference table, in dial/motif terms.
- Library entries get their status set (CONFIRMED / skipped) — skipped entries
  stay in the library; they may fit a later scene and can be re-offered.
- Explicit skips on a liked ref → record as constraints ("like X but NOT its
  palette") — they prevent exactly the drift that gets builds rejected.
- **Anti-references get the same pass inverted:** extract, then record
  precisely what to avoid, in the same vocabulary.

## Storyboard-stage refs

Screenshots dropped on a specific card get the photo profile, scoped to that
card — noted in the card's description, confirmed at the next board review.
A card ref never silently changes the global SSOT profile; if it should,
that's an SSOT amendment, with the user. When filling transition cards, check
the library first and offer matching entries by ID before inventing new ones.
