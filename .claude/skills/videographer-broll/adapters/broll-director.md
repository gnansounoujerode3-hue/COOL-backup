# Adapter: broll-director (decides WHEN and WHAT KIND, not just WHERE to find it)

## What this tool does

`broll-retrieval` answers "what free stock clip matches this noun". It does not
answer "should this moment even get a cutaway, and what KIND". `broll-director`
is the creative-direction layer that sits in front of it: it reads a CutSense
VUD (or a raw transcript + timestamps) and classifies every span into one of 9
b-roll types, styled on the researched "Re:Vision method"
(`knowledge/revision-style.md`) - then dispatches each opportunity to whichever
existing tool can actually produce that type of asset.

Think of it as the `senior-creative-director` skill's counterpart for FOOTAGE
you already have, instead of a script you're generating from scratch.

## Where it slots in (the seam - read `adapters/broll-retrieval.md`'s seam first)

```
CutSense ingest -> CutSense understand (VUD)
                          |
                          v
                 [ broll-director ]   <- you are here, runs FIRST
                  1. read the VUD's segments/entities/energy
                  2. classify each span against the 13-rule ruleset
                     (knowledge/revision-style.md) into a broll_type
                  3. for each opportunity, pick a caption/graphic style preset
                     by content register (see "Style presets" below)
                  4. dispatch by broll_type (see "Sourcing decision table")
                          |
                          v
                 [ broll-retrieval ]   <- only for the generic-noun subset
                          |
                          v
CutSense edit (overlay cutaways + graphics per manifest) -> render -> QA
```

## When the orchestrator dispatches here

| Trigger | Notes |
|---|---|
| User says "add b-roll", "make this feel like an ad not a talking head", "direct this like Re:Vision" | Direct request |
| `brief.broll.enabled == true` AND `brief.broll.style == "directed"` (vs `"retrieval-only"`) | Explicit opt-in to the craft layer, not just generic stock |
| A testimonial/interview cut has NO existing b-roll plan and reads visually flat on review | Same trigger as broll-retrieval, but prefer this adapter first - it decides retrieval is even the right move for a given span |

Not for: scripted/generated videos with no source footage (that's the writers'
room + fal-seedance path) - this adapter only directs cutaways INTO existing
talking-head footage.

## The ruleset

Full 13-rule ruleset with rationale lives in `knowledge/revision-style.md`. Do
not duplicate it here - read it before classifying spans. Summary of the 9
`broll_type` values it can assign: `graphic_card`, `motion_graphic`,
`prop_cutaway`, `activity_broll`, `screen_recording`, `vfx_composite`,
`second_angle`, `before_after_split`, `finished_product_broll`.

## Placement mode: full-screen replacement vs overlay

Every classified opportunity gets a SECOND, independent tag beyond `broll_type`:
`placement_mode`, either `full_replacement` or `overlay`. This decides the
render mechanics, not the content choice — two inserts with the same
`broll_type` can need opposite placement modes. A `prop_cutaway` showing a
product alone on a backdrop is `full_replacement`; a `prop_cutaway` floating
next to the still-visible speaker's head is `overlay`.

**`full_replacement`** — the talking-head frame disappears entirely for the
insert's duration; the new content (real footage OR a synthetic render) IS
the frame, cut in and cut back out. Confirmed in ~44 of 125 catalogued
inserts (every `motion_graphic`, every `vfx_composite`, the full-bleed half
of `graphic_card`) plus every real-footage cutaway type (`activity_broll`,
`second_angle`, `finished_product_broll`, `before_after_split`, most
`screen_recording`).

**`overlay`** — the original footage keeps playing underneath; the new
content is composited ON TOP in a specific screen region (a lower-third
badge, a stat popping up beside the speaker's gesturing hand, a floating
object near their head). The speaker never leaves frame. Roughly 8 of 21
`graphic_card` inserts and a handful of `prop_cutaway` inserts follow this
pattern.

**How to classify which one fired**: language like "next to X's head",
"alongside the speaker", "over the presenter's chest", "beside their hand",
or "lower-third" → `overlay`. Language like "cut to", "cuts away to", a scene
with no mention of the speaker/presenter at all, or an established BTS /
screen-recording / second-angle moment → `full_replacement`.

**Execution — both modes end the same way (a clip spliced into the timeline
at `t_start`–`t_end`), they just differ in what that clip contains:**

- `full_replacement` + synthetic asset (`motion_graphic` / `vfx_composite` /
  full-bleed `graphic_card`) → HyperFrames renders a standalone scene with no
  source video at all. The output clip replaces that span outright — a
  straight cut-in, cut-out, same as inserting any other clip.
- `full_replacement` + real footage (`activity_broll` / `second_angle` /
  `finished_product_broll` / `before_after_split` / most `screen_recording`)
  → source the real clip (client footage, a screen capture, an archive
  pull), splice in the same way. No rendering beyond the cut itself.
- `overlay` (`graphic_card` badges, `prop_cutaway` floating objects, an
  inset `screen_recording`) → HyperFrames re-ingests the EXACT `t_start`–
  `t_end` slice of the original source video as its own background media
  layer (a plain `<video data-start>` element — confirmed supported,
  muted/inline/FFmpeg-decoded, see `hyperframes-core`'s
  `references/variables-and-media.md`) and renders the graphic on top of it
  in the same composition. Output is one clip that already has both the
  original footage AND the overlay baked in, which then replaces that span
  in the timeline exactly like `full_replacement` does. No separate
  alpha-channel export or ffmpeg overlay-filter step needed — it's one
  HyperFrames render, not two tools chained together.

Position matters for `overlay` in a way it doesn't for `full_replacement`:
read the opportunity's language for where ("beside their hand" → lower-right
near the gesture, "over their chest" → center-low, "lower-third" → bottom
band) and pass that through as the graphic layer's anchor position.

## Style presets (typography + color, matched to content register)

Read the full spec in `knowledge/revision-style.md` ("Typography system"). Four
named presets to pick from per `brief.broll.register` (or infer from the
transcript's topic):

| Preset | Accent color | Register |
|---|---|---|
| `revision-analytical` | cyan/teal `#00F5D4` | tech, real-estate/solar, "system"/process pitches |
| `revision-energy` | lime/mint `#00FFCC` | fitness, DJ/nightlife-adjacent |
| `revision-authority` | gold `#FFD700` + heavy black shadow | listicle/educational, BTS chapter tags |
| `revision-provoke` | magenta/purple gradient | provocative-question hooks, finance/insurance |

These map to caption styling only (color, weight, motion-in). They are separate
from CutSense's hardcoded brand-pill cyan/orange - when this adapter is active,
its style preset OVERRIDES the default brand-pill caption for the graphic-card
and motion-graphic inserts it creates (running dialogue captions can stay on
brand-pill; the cutaway-specific graphics use the matched preset).

## Sourcing decision table (where each broll_type's asset actually comes from)

| broll_type | primary source | fallback | needs from user? |
|---|---|---|---|
| `graphic_card` | HyperFrames (kinetic type composition) | - | just the text/number to display |
| `motion_graphic` | HyperFrames (HTML+CSS+GSAP metaphor animation) | - | a one-line description of the metaphor (funnel, pyramid, etc) |
| `screen_recording` | user must supply the recording, or `orellius` browser bridge to capture a live UI | skip the insert | the actual UI/app to record |
| `activity_broll` | **client's own BTS/product footage** (ask for it) | `archival-broll` generic film-crew/activity clip (weak substitute) | real footage - this is the #1 most-used type in the corpus and the hardest to fake |
| `prop_cutaway` | a real photo/video of the actual object -> `fal-seedance` image-to-video, or a literal product shot if supplied | `broll-retrieval` if the object is generic (a book, a laptop) | a photo of the specific object if it's the client's own product |
| `before_after_split` | client's real before/after photo pair, composited via HyperFrames split template | skip the insert - never fabricate | the two real photos |
| `finished_product_broll` | an existing finished deliverable (another video/asset the client already has) | skip | the asset itself |
| `vfx_composite` | Gemini Omni (edit the existing shot: add a crowd, change environment) or `fal-seedance` (generate the composite from scratch) | skip if budget-constrained - this is the highest-effort tier | none, but confirm budget - this is metered generation, not free |
| `second_angle` | only fires if a second camera/take actually exists in the source footage | falls back to a `motion_graphic` punch-zoom instead | - |
| (idle-timer fallback, rule 9) | pure FFmpeg punch-zoom crop on the SAME shot | - | none - always available, $0 |

Anything routed to `broll-retrieval` (the free-stock path) is for the narrow
subset broll-director determines is a truly GENERIC noun (a city, a season, an
abstract object with no client-specific version) - most of this corpus's power
comes from real client-specific assets, not stock.

🚨 Every row that dispatches to **HyperFrames** (`graphic_card`,
`motion_graphic`, `prop_cutaway` when synthetic, `before_after_split`) needs
`placement_mode` resolved FIRST (see "Placement mode" above) - it changes
whether HyperFrames renders a bare standalone scene or re-ingests the
original footage slice as its background layer. Resolve placement_mode
before filling in `asset_spec`, not after.

## Manifest output (extends broll-retrieval's schema)

Write `${VIDEO_JOBS_DIR}/<brief_id>/broll/broll-manifest.json` with the same
shape as `broll-retrieval.md` documents, plus per-cutaway:

```json
{
  "t_start": 12.4, "t_end": 15.1,
  "broll_type": "graphic_card",
  "placement_mode": "overlay",
  "rule_fired": "2 - quantitative metric mentioned",
  "trigger_words": "reached half a million views",
  "style_preset": "revision-energy",
  "source_tool": "hyperframes",
  "asset_spec": {
    "text": "503.5K views",
    "animation": "roll-up counter",
    "anchor": "lower-right, beside speaker's gesture"
  },
  "overlay_source_slice": { "t_start": 12.4, "t_end": 15.1 },
  "needs_client_asset": false,
  "status": "ready"
}
```

`overlay_source_slice` is present only when `placement_mode == "overlay"` — it
tells HyperFrames exactly which span of the ORIGINAL source video to re-ingest
as its background media layer (normally identical to `t_start`/`t_end`, kept
as its own field so a future re-timed edit can't silently desync the overlay
from the footage it's meant to sit on). Omit it entirely for
`full_replacement` — there is no original footage to re-ingest.

When `needs_client_asset: true` (activity_broll, before_after_split,
finished_product_broll, and specific-object prop_cutaway), set
`"status": "blocked_on_client_asset"` and surface a single consolidated ask to
the user listing everything blocked, rather than one question per cutaway.

## QA + gates

Same post-render gates as `broll-retrieval.md` (face-safety, loudness, timing)
plus the density rules from `knowledge/revision-style.md` #11-12: fail QA if any
gap between visual changes exceeds ~8s, or if any two graphic overlays fire
within 0.5s of each other.

## Anti-patterns

- Routing an `activity_broll` opportunity straight to `broll-retrieval` - generic
  stock of "a person in a gym" is not what makes this style work; it needs the
  ACTUAL client's own footage. Ask for it or flag as blocked, don't fake it.
- Firing rule 2 or 7 (metric/before-after) with an invented number or photo.
  These rules only fire on REAL data already present in the transcript/assets.
- Defaulting every job to the `revision-provoke` magenta preset because it looks
  the flashiest - match the preset to the content register.
- Skipping the density-floor rule (#11) and only inserting cutaways where a
  semantic trigger literally fires - long silent stretches still need a punch-
  zoom or angle change to avoid flatlining.
- Forcing IG-track VFX set-pieces (rule 8's more extreme end) onto a restrained
  client testimonial - reserve that tier for house/demo-reel work per
  `knowledge/revision-style.md`'s "Two registers" section.
- Guessing `placement_mode` wrong in either direction: rendering a bare
  standalone scene (`full_replacement`) when the opportunity actually called
  for the speaker staying visible loses continuity mid-sentence; compositing
  a badge over footage (`overlay`) when the moment actually called for a full
  cutaway reads as cluttered rather than energetic. When the opportunity's
  language is ambiguous about whether the speaker stays in frame, default to
  `full_replacement` for `motion_graphic`/`vfx_composite` (they were never
  overlay material in the corpus - 0 counterexamples) and `overlay` for a
  lower-third-shaped `graphic_card` (badges are never full-screen in the
  corpus either).

## See also

`knowledge/revision-style.md` (the full ruleset + research this adapter is
built from), `adapters/broll-retrieval.md` (the generic-stock sourcing path
this adapter dispatches into), `adapters/hyperframes.md` (executes
`graphic_card`/`motion_graphic`/`before_after_split`), `adapters/gemini-omni.md`
and `adapters/fal-seedance.md` (execute `vfx_composite`). The `overlay`
placement mode's video-re-ingest mechanism is grounded in
`~/.claude/skills/hyperframes-core/references/variables-and-media.md`'s
documented `<video data-start>` support (muted/inline, FFmpeg-decoded, works
nested in sub-compositions) - verify that reference still holds if HyperFrames
gets a major version bump.
