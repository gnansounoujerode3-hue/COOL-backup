# Adapter: HyperFrames

## What this tool does

HyperFrames is an HTML+CSS+GSAP composition engine driven by `npx hyperframes`. Compositions are a single `index.html` with `data-*` timing attributes, GSAP timelines, and embedded fonts. The CLI lints, previews, and renders to MP4 via headless Chrome. Best for branded title cards, kinetic typography, audio-reactive visuals, and ad hooks where there is no source footage to cut from.

## When the orchestrator dispatches here

| Source type | Intent | Template |
|---|---|---|
| `url` or `avatar_script` (no footage) | `promo` | `branded-promo-from-url.md` |
| `avatar_script` | `ad_variants` | `ad-hook-variations.md` |
| any | `talking_head_shorts` (when no source clips, generate fully composed from script) | `talking-head-shorts.md` |
| any | hook intros / outros that prepend or append CutSense / video-use cuts | sub-asset, never primary |

HyperFrames is the right answer when the brief says "make me a 30s ad" with copy + brand but no footage. Pair with HeyGen or Hedra when an avatar is needed - render the avatar separately, drop the MP4 into a HyperFrames composition as a `<video>` clip.

## Inputs read from brief

- `brief.intent` - selects the starter template (see mapping below)
- `brief.output.aspect` - 9:16 -> 1080x1920, 1:1 -> 1080x1080, 16:9 -> 1920x1080, 4:5 -> 1080x1350
- `brief.output.length_target_sec` - sets root composition `data-duration`
- `brief.output.count` - number of variants (rendered sequentially in the same project, different output filenames, OR forked into N projects for parallel renders)
- `brief.output.captions_style` - jumbo or natural_sentence drives caption sub-composition; brand_pill is the default
- `brief.brand.colors_primary` / `colors_secondary` / `colors_text` / `colors_bg` - injected as CSS variables
- `brief.brand.fonts` - injected as `font-family` (Outfit + JetBrains Mono default)
- `brief.brand.logo_path` - optional `<img>` in the composition
- `brief.notes` - copy / script / messaging to put on screen
- `brief.output.fps` - `--fps` flag at render time
- `brief.output.resolution` - 720p / 1080p / 4k (HF defaults to 1080p; 4k requires more workers)
- `brief.output_dir` - destination root

## Pre-flight checks

1. `npx hyperframes doctor` - all green (Chrome + FFmpeg + memory)
2. Node >= 22 on PATH
3. `<brief.output_dir>/hyperframes/` exists
4. `<brief.output_dir>/hyperframes/project/` is the staging dir for the composition project

## Commands to run

```bash
# Step 1: pick a starter template based on brief.intent
# promo                  -> product-promo
# ad_variants            -> kinetic-type
# talking_head_shorts    -> warm-grain
# educational_verticals  -> swiss-grid
# default                -> blank

cd <brief.output_dir>/hyperframes
npx hyperframes init project --example <template> --non-interactive

# Step 2: open project\index.html and inject brand pack values
# Replace the :root block with values from brief.brand:
#   :root {
#     --primary: <brief.brand.colors_primary>;
#     --secondary: <brief.brand.colors_secondary>;
#     --text: <brief.brand.colors_text>;
#     --bg: <brief.brand.colors_bg>;
#   }
# Update body { font-family: '<brief.brand.fonts[0] || Outfit>', system-ui, sans-serif; }
# Add to <head>: <link rel="preconnect" href="https://fonts.googleapis.com">
#                <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">

# Step 3: replace placeholder copy with brief.notes script
# Each scene's headline + subhead text comes from brief.notes (parsed by the orchestrator
# into a 3-5 scene structure based on output.length_target_sec)

# Step 4: set root composition dimensions from brief.output.aspect
#   9:16  -> data-width="1080" data-height="1920"
#   1:1   -> data-width="1080" data-height="1080"
#   16:9  -> data-width="1920" data-height="1080"
#   4:5   -> data-width="1080" data-height="1350"
# And data-duration="<brief.output.length_target_sec>"

# Step 5 (optional): generate narration with HF's TTS
# Skip if no narration needed.
npx hyperframes tts "<narration text from brief.notes>" \
  --voice af_nova \
  --output project/narration.wav

# Step 6: lint
cd project
npx hyperframes lint

# Step 7: render
npx hyperframes render \
  --quality high \
  --fps <brief.output.fps> \
  --format mp4 \
  --output <brief.output_dir>/hyperframes\out_01.mp4

# For fork mode preview, use --quality medium or draft to cut render time roughly in half.
# Re-render the user's chosen winner at high after fork comparison.
```

## CSS variables to set

Open `<brief.output_dir>/hyperframes\project\index.html` and inject these in `:root`:

| CSS variable | Source field |
|---|---|
| `--primary` | `brief.brand.colors_primary` |
| `--secondary` | `brief.brand.colors_secondary` |
| `--text` | `brief.brand.colors_text` |
| `--bg` | `brief.brand.colors_bg` |
| `--font-headline` | `brief.brand.fonts[0]` (default `Outfit`) |
| `--font-mono` | `brief.brand.fonts[1]` (default `JetBrains Mono`) |

If the starter composition uses different variable names (some templates use `--accent` or `--ink`), map by role and rename in the composition CSS - never invent new colors.

## Output location

`<brief.output_dir>/hyperframes\out_NN.mp4`. The HF render command writes there directly via `--output`. Each variant `count > 1` runs the render command once per output, varying the script content per variant.

## Failure modes + recovery

1. **FFmpeg path missing on Windows**: HyperFrames bundles its own FFmpeg. If the system FFmpeg is broken, point HF at the bundled one via `npx hyperframes doctor` output, or set `FFMPEG_PATH` env var. Do not fall back to a different tool.
2. **Outfit / JetBrains Mono not installed locally**: the composition `@import`s from Google Fonts in `<head>`, so local install is not required. The HF compiler embeds Google Fonts during render. Verify with `lint`.
3. **Render too slow for fork mode**: switch to `--quality medium` for fork preview comparison, then re-render the chosen winner at `--quality high`. Warn the user up front: HyperFrames adds 2-5 min vs CutSense / video-use forks.
4. **Lint errors**: never `--strict` in fork mode (one fork failing kills the option). Run lint, log warnings to `<output_dir>\hyperframes\lint.log`, render anyway.

## Brief field -> CLI flag mapping

| Brief field | CLI flag / behavior |
|---|---|
| `intent` | picks `--example` template at init |
| `output.aspect` | composition `data-width` / `data-height` |
| `output.length_target_sec` | composition `data-duration` |
| `output.count` | number of render invocations |
| `output.fps` | `--fps <n>` |
| `output.resolution` | composition dimensions (1080p default) |
| `output.format` | `--format mp4|webm` |
| `brand.colors_*` | CSS variables in `:root` |
| `brand.fonts` | `font-family` + Google Fonts `<link>` |
| `brand.logo_path` | optional `<img src>` (absolute file URL) |
| `notes` | parsed into scene scripts + narration text |

## Notes for fork mode

HyperFrames is typically the slowest fork. For a 30s composition at 1080p / 30fps, expect 2-5 min on a workstation, longer at 4k or 60fps. Tell the user up front so they don't think the fork hung. In fork mode, use `--quality medium` for the preview render. Each fork must scaffold into its own `project/` dir to avoid file collisions.

## Multi-clip consistency (does not apply here)

The 3 Consistency Rules in [`../brand/consistency-rules.md`](../brand/consistency-rules.md) are about preventing drift between independently-generated AI clips. HyperFrames is deterministic HTML+CSS+GSAP rendering - same composition produces byte-identical output every time, every scene of a multi-scene composition draws from the same DOM, so character / brand / prop drift is impossible by construction. Skip the Lock-Block step for HyperFrames dispatches.
