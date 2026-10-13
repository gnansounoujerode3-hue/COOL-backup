# Adapter: Remotion

## What this tool does

Remotion is a React-based programmatic video framework. Pixel-perfect compositions, deterministic output, Lambda-based parallel rendering when needed. The orchestrator uses it for **branded title cards, lower thirds, outro CTAs, and any short brand-aligned card** where pixel precision matters.

For full footage cuts CutSense uses Remotion under the hood. The standalone adapter is for **brand cards composed from props alone** - no source footage required.

## When the orchestrator dispatches here

- `intent = promo` when the request is for a 5-15s brand card (vs a longer narrative promo - that goes to HyperFrames)
- `intent = ad_variants` when the user wants 3 brand cards with different headlines (perfect Remotion fit - same composition, different inputProps, parallelize with `npx remotion render` invocations)
- Any time the user says "use remotion" by name
- As a chained step inside a HyperFrames or CutSense pipeline (a Remotion-rendered intro card concatenated to the main edit)

NOT for: long footage cuts (use CutSense), audio-reactive visuals (use HyperFrames), avatar lipsync (HeyGen / Hedra).

## Inputs read from brief

- `brief.output.aspect` -> composition width/height (9:16 = 1080x1920, 16:9 = 1920x1080, 1:1 = 1080x1080)
- `brief.output.fps` (default 30)
- `brief.output.length_target_sec` -> composition `durationInFrames` (sec * fps)
- `brief.output.resolution`
- `brief.brand.colors_primary` -> inputProps.colors_primary
- `brief.brand.colors_secondary` -> inputProps.colors_secondary
- `brief.brand.colors_text` -> inputProps.colors_text
- `brief.brand.colors_bg` -> inputProps.colors_bg
- `brief.brand.fonts[0]` -> inputProps.font_headline
- `brief.notes` -> parsed for headline/subhead (or extract from `provider_specific.heygen.script` if avatar_script source)
- `brief.output_dir` -> destination

## Pre-flight checks

1. `node --version` >= 18 (Remotion 4 requires Node 18+)
2. `ffmpeg --version` exits 0 (Remotion bundles its own but verifies)
3. The skill's `remotion-templates/brand-card/` directory exists with `package.json`, `src/Root.tsx`, `src/BrandCard.tsx`
4. On first dispatch ever: `npm install` inside the staging copy (slow, ~90s, one-time per job)
5. Chromium for the headless render - Remotion downloads its own bundled Chrome on first run

## Commands to run

```bash
# Step 1: copy the template into the staging area
mkdir -p "<brief.output_dir>/remotion"
cp -r "<skill_root>/remotion-templates/brand-card/." "<brief.output_dir>/remotion/"
cd "<brief.output_dir>/remotion"

# Step 2: install deps (~90s on first run, cached afterward via per-project node_modules)
npm install --no-fund --no-audit

# Step 3: build inputProps JSON from brief
# Write it to props.json so we don't fight Windows shell quoting
cat > props.json <<'PROPS'
{
  "variant": "title",
  "headline": "<derived from brief.notes or brief.provider_specific.heygen.script first line>",
  "subhead": "<derived from brief.notes second line, optional>",
  "colors_primary": "<brief.brand.colors_primary>",
  "colors_secondary": "<brief.brand.colors_secondary>",
  "colors_text": "<brief.brand.colors_text>",
  "colors_bg": "<brief.brand.colors_bg>",
  "font_headline": "<brief.brand.fonts[0]>"
}
PROPS

# Step 4: render
npx remotion render \
  src/index.ts \
  BrandCard \
  out_01.mp4 \
  --props=props.json \
  --image-format=jpeg \
  --codec=h264 \
  --concurrency=auto \
  --width=<derived from brief.output.aspect> \
  --height=<derived from brief.output.aspect>

# Step 5: copy final to standardized location (already there)
# out_01.mp4 IS already at <brief.output_dir>/remotion/out_01.mp4
```

For multiple variants (ad_variants intent), run step 4 N times with different headlines, output to `out_01.mp4`, `out_02.mp4`, `out_03.mp4`.

## Variant selection (composition.variant prop)

- `variant: "title"` - centered headline + subhead. Use for opening title card.
- `variant: "lower_third"` - bottom-left headline + subhead, slides in. Use during footage to identify speaker or key point.
- `variant: "outro_cta"` - centered, but with secondary pill emphasized as the CTA action ("Book a session", "Watch full episode", etc.). Use for closing card.

## Output location

`<brief.output_dir>/remotion/out_NN.mp4` (matches the universal convention).

## Failure modes + recovery

1. **`npm install` fails (network, registry)**: retry once. If still fails, fall back to CutSense (which has Remotion deps already installed at `${CUTSENSE_DIR}/packages/renderer/node_modules/`).
2. **Chrome download fails on first render**: Remotion will print a download URL - either run `npx remotion browser install` manually or set `REMOTION_CHROME_PATH` to an existing Chrome binary.
3. **Font not installed locally**: Remotion uses system fonts. If `Outfit` / `Poppins` / `JetBrains Mono` aren't installed, Remotion falls back to system sans-serif. To avoid: load fonts via `<link>` from Google Fonts inside the composition (TODO for V2).
4. **Render slower than expected for ad_variants**: parallelize - run 3 `npx remotion render` invocations in parallel (different output filenames, same project dir).

## Brief field -> CLI flag / inputProp mapping

| Brief field | Maps to |
|---|---|
| `output.fps` | composition `fps` (already 30 in template) |
| `output.aspect` | `--width` / `--height` flags |
| `output.length_target_sec` | composition `durationInFrames = sec * fps` (modify in Root.tsx if needed) |
| `output.format` | `--codec` (mp4 -> h264, webm -> vp9) |
| `brand.colors_primary` | `inputProps.colors_primary` |
| `brand.colors_secondary` | `inputProps.colors_secondary` |
| `brand.colors_text` | `inputProps.colors_text` |
| `brand.colors_bg` | `inputProps.colors_bg` |
| `brand.fonts[0]` | `inputProps.font_headline` |
| `notes` (parsed) | `inputProps.headline` + `inputProps.subhead` |

## Notes for fork mode

Remotion is fast (sub-30s for a 5s brand card after first npm install). Good fork candidate when comparing brand-card-shaped outputs (Remotion vs HyperFrames vs HeyGen avatar). First run per job has the npm install overhead (~90s) - subsequent renders in the same job dir reuse node_modules.

## Adding new compositions later

To add a new composition variant (e.g. `BrandQuoteCard`, `BrandStatCard`):
1. Add a TSX file in `remotion-templates/brand-card/src/`
2. Register in `Root.tsx` with a new Composition id and Zod schema
3. Document the new variant in this adapter MD under "Variant selection"

## V2 follow-ups (still deferred)

- Lambda support for renders > 60s (currently local-only)
- Brand-pill caption Remotion component port (currently lives in CutSense's render-cut.mjs)
- Audio-reactive shader compositions (currently belongs to HyperFrames)
- Stat / chart / data-viz compositions (deferred until first request)
