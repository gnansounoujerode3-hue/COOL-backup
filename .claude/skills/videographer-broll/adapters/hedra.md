# Adapter: Hedra

## What this tool does

Hedra (Character-3 model) generates avatar lipsync video from a portrait image + audio track. Stronger emotion modeling than HeyGen for some content - your `pickCloneProvider` rule typically returns Hedra as the V1 primary when only a `portrait_url` is present (no pre-cloned HeyGen avatar). Used as the alternate to HeyGen in the orchestrator's option block.

## When the orchestrator dispatches here

| Source type | Intent | Notes |
|---|---|---|
| `avatar_script` | `avatar_explainer` | Primary path when the user has a portrait image but no HeyGen avatar |
| `avatar_script` | `ad_variants` | When emotive delivery matters more than perfect lip-sync precision |

Picked over HeyGen when the brief carries `portrait_url` but no `avatar_id` (a typical 2-step provider-pick pattern: avatar_id present -> HeyGen, else Hedra). The orchestrator treats them as user-pickable alternates in the option block.

## Inputs read from brief

- `brief.source.type` must be `avatar_script`
- `brief.notes` - the script the avatar will read
- `brief.output.length_target_sec` - target duration; Hedra clamps to audio length
- `brief.output.aspect` - 9:16 native, others require post-render crop
- `brief.output.captions_style` - drives post-render ASS caption burn-in
- `brief.brand.colors_primary` / `colors_secondary` - ASS subtitle style overrides
- `brief.source.language` - drives the TTS voice for narration generation
- `brief.output_dir` - destination
- Custom fields: `brief.portrait_url` (absolute file path or HTTPS URL), `brief.voice_id` (ElevenLabs voice ID for TTS narration; Hedra ingests audio, not text)

## Multi-clip consistency

If this dispatch is part of a **multi-clip avatar series** (Act 1 / Act 2 / Act 3 with the same speaker, multi-take spokesperson reel), read [`../brand/consistency-rules.md`](../brand/consistency-rules.md) before generating any clip. Hedra calls are stateless across clips — `portrait_url` and `voice_id` lock the face and voice, but **anything described in the prompt body or surrounding context** (extended setting, props, secondary subjects) drifts between calls unless pasted byte-identical. Don't say "the same speaker as before" — paste the full Character + Setting Lock block.

## Pre-flight checks

1. `HEDRA_API_KEY` env var set. Set in `local/.env` (copy from `.env.example` at skill root) - never hardcode keys.
2. `brief.portrait_url` is reachable - either an absolute file path that exists, or a 200-status HTTPS URL.
3. `ELEVENLABS_API_KEY` env var set (Hedra needs an audio track; we generate it via ElevenLabs TTS). Set in `local/.env`.
4. `<brief.output_dir>/hedra/` exists
5. ffmpeg on PATH (for caption burn-in)

## Commands to run

```bash
# Step 1: generate narration audio via ElevenLabs TTS (Hedra needs audio input)
# POST https://api.elevenlabs.io/v1/text-to-speech/<voice_id>
# headers: { 'xi-api-key': process.env.ELEVENLABS_API_KEY }
# body: { text: brief.notes, model_id: 'eleven_multilingual_v2' }
# Save MP3 to <brief.output_dir>/hedra/narration.mp3

# Step 2: write a small Node wrapper that calls Hedra Character-3 endpoint

# File: <brief.output_dir>/hedra/run.mjs (~30 lines):
#   1. read brief.json from <brief.output_dir>/brief.json
#   2. upload portrait + narration to Hedra (POST https://api.hedra.com/web-app/public/assets
#      with multipart form: name, type=image|audio, file)
#      -> capture asset IDs
#   3. POST https://api.hedra.com/web-app/public/generations
#      body: { type: 'video',
#              ai_model_id: '<character-3 model ID>',
#              start_keyframe_id: <portrait asset ID>,
#              audio_id: <narration asset ID>,
#              generated_video_inputs: { text_prompt: 'realistic lip-sync, neutral expression',
#                                        resolution: '720p',
#                                        aspect_ratio: brief.output.aspect } }
#      headers: { 'X-API-Key': process.env.HEDRA_API_KEY }
#   4. poll GET https://api.hedra.com/web-app/public/generations/<id>/status
#      every 5s, max 10 min, until status === 'complete'
#   5. download URL from response.url to <brief.output_dir>/hedra/raw_01.mp4

# Step 3: run the wrapper
node <brief.output_dir>/hedra/run.mjs

# Step 4: caption burn-in via ffmpeg using brand_pill ASS preset
# Run ElevenLabs Scribe on raw_01.mp4 to recover word-level timings, then build
# <brief.output_dir>/hedra/captions.ass

ffmpeg -i <brief.output_dir>/hedra/raw_01.mp4 \
  -vf "ass=<brief.output_dir>/hedra/captions.ass" \
  -c:a copy \
  <brief.output_dir>/hedra/out_01.mp4

# Step 5: if output.count > 1, regenerate with rotated script per variant.
```

## Output location

- Raw avatar video (no captions): `<brief.output_dir>/hedra/raw_NN.mp4`
- Narration audio cache: `<brief.output_dir>/hedra/narration.mp3`
- Final with brand-pill captions: `<brief.output_dir>/hedra/out_NN.mp4`

## Failure modes + recovery

1. **`portrait_url` invalid or unreadable**: Hedra returns a 400 on asset upload. Abort early - never silently swap portraits. Ask the user for a different image.
2. **Rate limit (429)**: exponential backoff (5s, 15s, 45s) up to 3 retries.
3. **Render takes 2-5 min** typical: poll every 5s, log status at every poll (be transparent during long waits).
4. **Caption burn-in fails because no word-level timings**: run ElevenLabs Scribe on the raw MP4's audio track to recover word timings. Last resort: sentence-level captions estimated from audio duration.
5. **Hedra credit balance exhausted**: if 402 / billing error, surface immediately.

## Brief field -> CLI flag mapping

| Brief field | API field / behavior |
|---|---|
| `notes` | text fed to ElevenLabs TTS, then audio to Hedra |
| `portrait_url` (custom) | uploaded as start_keyframe asset |
| `voice_id` (custom) | ElevenLabs voice for narration |
| `output.aspect` | `aspect_ratio` field on generation request |
| `output.length_target_sec` | implicit (clamped to narration length) |
| `output.captions_style` | post-render ffmpeg ASS overlay |
| `brand.colors_*` | ASS force-style for caption overlay |
| `source.language` | drives ElevenLabs TTS model selection |
| `output.count` | number of separate generation runs |

## Notes for fork mode

Hedra and HeyGen produce visually different output - Hedra tends to be more emotive but less precise, HeyGen tends to be precise but flatter. They are natural fork pair candidates when the user wants to compare avatar styles. Both add 2-5 min per fork. Each fork runs an independent generation - no shared state, safe to parallelize.

Within video-orchestrator we treat Hedra and HeyGen as ALTERNATES the user picks between in the option block, not as a default fork pair. Only fork them together when the user explicitly says "fork hedra vs heygen" or `tool_mode = fork_to_3` includes both.

## Reference

The typical multi-tenant production wires Hedra as the V1 primary clone provider via a `pickCloneProvider` rule (avatar_id present -> HeyGen, else Hedra). This adapter mirrors the same call shape (asset upload -> generation -> poll -> download) so a future shared lib migration is straightforward.
