# Adapter: Lottie (text-to-lottie)

## What this tool does

Lottie authoring via the **`text-to-lottie`** skill. The agent writes a Lottie
(Bodymovin) animation as JSON to `public/lottie.json` and previews it live in the
official Diffusion Studio player - a Vite + React harness that renders with
**Skia's Skottie** module (`canvaskit-wasm`), not the JS `lottie-web` runtime.

The deliverable is a **vector motion-graphics asset**, not a rendered MP4. A
`lottie.json` is tiny, infinitely scalable, and embeds anywhere: web (lottie-web /
dotLottie), React, React Native, iOS, Android, After Effects. It is the right tool
for short, single-scene, usually-looping vector pieces:

- animated icons, loaders / spinners, success-checkmarks, toggles
- logo reveals and brand flourishes
- UI micro-interactions
- animating an exported SVG (e.g. from Figma)
- data-driven animations (values bound to live controls / slots)

It is **not** for footage cutting (CutSense / video-use), AI generative video
(fal-seedance), avatar lipsync (HeyGen / Hedra), or HTML+GSAP title cards rendered
to MP4 (HyperFrames). If the user wants a finished `.mp4`/`.gif` and not an
embeddable vector asset, prefer HyperFrames; only use Lottie + a screen-record when
they specifically want a Lottie/vector animation as a video file.

## When the orchestrator dispatches here

Lottie is a **Source = none generation** path (like fal-seedance), not an editing
path. Route here when the user asks for a reusable vector animation rather than a
video file. Trigger language:

| User says | Route |
|---|---|
| "make a Lottie of...", "a Lottie animation" | Lottie |
| "an animated icon / loader / spinner / checkmark" | Lottie |
| "animate our logo" (vector, for the app/site) | Lottie |
| "a UI micro-interaction / button animation" | Lottie |
| "animate this SVG / this Figma export" | Lottie |
| "a data-driven animation with adjustable X" | Lottie (use slots) |

If the user instead wants a social clip, ad, title card, or anything with audio /
captions / a finished MP4, that is **not** Lottie - send it to HyperFrames or
fal-seedance.

## This is an asset brief, not the video brief

Lottie does **not** use the full video brief contract (no audio, no captions, no
LUFS, no cleanup, no face-safety). Like fal-seedance it has its own small brief
shape. Skip Step 2's template lookup and the 6 video questions. Ask instead:

1. **What to animate** (the subject + the motion in one or two sentences)
2. **Composition size** (square 512x512 default, or match a target aspect)
3. **Loop?** seamless loop vs one-shot
4. **Brand colors** (mapped to fills; default to the brand pack)
5. **Which properties should be live-editable** (exposed as slots / controls -
   color, size, speed, a data value)

## Inputs read from brief (when present)

The orchestrator may still pass a brief; read only what applies:

- `brief.notes` - the animation description (subject + motion). The primary input.
- `brief.output.aspect` / `resolution` -> composition `w`x`h`
  (9:16 -> 1080x1920, 1:1 / square -> 512x512 or 1080x1080, 16:9 -> 1920x1080).
- `brief.output.length_target_sec` + a chosen `fr` (default 60 fps) ->
  top-level `op = round(length_sec * fr)`.
- `brief.brand.colors_primary` / `_secondary` / `_bg` -> fill colors
  (**normalized 0-1 RGBA**, not 0-255) and the mandatory `bgColor` slot default.
- `brief.output_dir` - where the player harness is scaffolded.

Ignore `brief.cleanup`, `brief.captions_style`, audio, and `qa_gates` - they do not
apply to a vector asset.

## Pre-flight checks

1. Node on PATH (the harness is a standard Vite + React app).
2. `<brief.output_dir>/lottie/` is the scaffold target (or reuse a persistent
   `~/lottie-player` clone to avoid re-installing CanvasKit each run).
3. A browser tool (Orellius) is available for frame-pinned verification.

## Commands to run

```bash
# Step 0: scaffold the official player harness ONCE, reuse afterward.
# NEVER hand-roll a viewer or swap in lottie-web - the slot panel, the
# ?frame= URL controls, and the Skottie wasm wiring only hold in this exact repo.
cd <brief.output_dir>
npx degit diffusionstudio/lottie lottie
cd lottie
npm install          # postinstall copies canvaskit.wasm into public/
npm run dev          # Vite dev server, prints http://localhost:5173

# If the harness already exists, skip degit: just `npm install && npm run dev`.

# Step 1: author the animation -> write public/lottie.json
# Invoke the `text-to-lottie` skill to produce the JSON. The Vite plugin watches
# the file and full-reloads the page on save, so edits appear immediately.
# Validate before/after each save:
node -e "JSON.parse(require('fs').readFileSync('public/lottie.json','utf8'))"

# Step 2 (required): expose a background-color control + any brand controls.
# Every animation MUST expose a bgColor slot (full-comp background rect, last layer)
# plus a controls.json label. Add more slots for brand color / size / data values.
# public/controls.json hot-reloads on save too.

# Step 3: verify in the Skottie player (browser tool, do NOT drag the slider).
# Pin an exact frame in the URL and screenshot the canvas:
#   http://localhost:5173/?frame=<N>&paused=1
# The canvas carries data-testid="lottie-canvas". A blank canvas with no on-screen
# error usually means a shape wasn't wrapped in a "ty":"gr" group (the #1 gotcha).

# Step 4 (only if a VIDEO FILE is the deliverable): record the player canvas.
# The harness previews but has no built-in MP4 exporter. To hand back an .mp4/.gif,
# screen-record the playing canvas via the Orellius record_video tool over
# http://localhost:5173/  (autoplay, no query params), then trim with ffmpeg.
# The native, preferred deliverable stays public/lottie.json.
```

## Output location

- Primary deliverable: `<brief.output_dir>/lottie/public/lottie.json` (+ optional
  `public/controls.json`). Copy `lottie.json` to the consuming project to embed.
- Optional video file: `<brief.output_dir>/lottie/out_NN.mp4` if Step 4 was run.

The COMPARE.md row for a Lottie dispatch lists the json path (and the mp4 path if
recorded), composition `w`x`h`, fps, frame count `op`, loop yes/no, and the list of
exposed control slots - not LUFS / face-safe (those are video-only QA gates).

## Skottie authoring rules the skill enforces (so the orchestrator knows the shape)

- Top-level needs `v, fr, ip, op, w, h, assets, layers`. Duration = `(op-ip)/fr`.
- **Every shape/fill/stroke must be wrapped in a Group (`"ty":"gr"`)**, and each
  group ends with a `"tr"` transform. A flat shapes list renders blank.
- Colors are **0-1 RGBA**. `[1,0,0,1]` is opaque red.
- Keyframe `s` values are always arrays, even scalars (`"s":[360]`). To loop
  seamlessly, the last keyframe value equals the first.
- Live-editable values use Skottie **slots**: a top-level `"slots"` object + a
  property pointing at it with `"sid"`. The panel auto-discovers via
  `getSlotInfo()`; `controls.json` only adds labels / slider ranges.
- Prefer shape layers (`"ty":4`) so no external assets are needed.

## Failure modes + recovery

1. **Blank canvas, no error**: a shape primitive or fill is not inside a
   `"ty":"gr"` group's `it` array. Re-wrap. This is the single most common failure.
2. **"CanvasKit could not parse the Lottie file."**: invalid JSON (trailing comma /
   comment) or a malformed property. Re-run the `node -e JSON.parse` check; remove
   any JSONC comments before saving (the file must be pure JSON).
3. **CanvasKit wasm missing** (canvas never initializes): `npm install` did not run
   the postinstall copy. Run `node scripts/copy-canvaskit.mjs` to copy
   `canvaskit.wasm` into `public/`.
4. **Animation looks frozen / no loop**: last keyframe value does not equal the
   first, or layer `op` / top-level `op` does not cover the animated frames.
5. **Need a finished MP4 but only have json**: the harness has no exporter - record
   the canvas (Step 4). Do not claim a video deliverable exists until the file is on
   disk and ffprobe passes.

## Multi-clip consistency (does not apply here)

The 3 Consistency Rules in [`../brand/consistency-rules.md`](../brand/consistency-rules.md)
prevent drift between independently-generated **AI** clips. Lottie is deterministic
hand-authored JSON rendered by Skottie - the same `lottie.json` renders
byte-identically every time, so character / brand / prop drift is impossible by
construction. Skip the Lock-Block step for Lottie dispatches.

## Notes for fork mode

Lottie is fast and cheap (no render farm, no API credits - just JSON + a local Vite
server), so it forks well against HyperFrames when the user is unsure whether they
want an embeddable vector asset or a finished MP4. In a fork, scaffold each variant
into its own `lottie/<variant>/` dir (or reuse one harness and swap `public/lottie.json`
between captures) and verify each with a frame-pinned screenshot.
