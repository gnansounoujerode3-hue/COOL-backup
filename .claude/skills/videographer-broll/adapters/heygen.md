# Adapter: HeyGen

## What this tool does

HeyGen V2 API generates avatar lipsync video from a text script. Pre-cloned avatar + voice IDs are picked from your HeyGen account; the API returns a clean MP4 of the avatar reading the script. No camera or microphone needed. Used as the "alternate" to Hedra in the typical `pickCloneProvider` rule - HeyGen wins when both `avatar_id` and `voice_id` are present in the brief.

## When the orchestrator dispatches here

| Source type | Intent | Notes |
|---|---|---|
| `avatar_script` | `avatar_explainer` | Primary path when no source footage exists |
| `avatar_script` | `ad_variants` | When ad copy needs an on-camera spokesperson but no shoot is feasible |
| `url` | `promo` (rare) | If the promo needs a talking spokesperson summarizing the page |
| `avatar_script` | `dialogue_2shot` | Multi-speaker dialogue (e.g. AI-generated podcast). Uses **Avatar IV** mode (see "Avatar IV: multi-speaker dialogue mode" section below). One HeyGen render per speaker turn, stitched in CapCut / ffmpeg. |

Picked over Hedra when the brief carries both `avatar_id` and `voice_id` (the typical 2-step provider-pick pattern: avatar_id present -> HeyGen, else Hedra).

## Inputs read from brief

- `brief.source.type` must be `avatar_script` (this adapter does not consume video)
- `brief.notes` - the script the avatar will read (verbatim, do not paraphrase)
- `brief.output.length_target_sec` - HeyGen renders to script length, but flag if expected vs actual mismatch > 5s
- `brief.output.aspect` - HeyGen supports 9:16, 16:9, 1:1 natively; 4:5 requires post-render crop
- `brief.output.captions_style` - drives the post-render ffmpeg subtitle burn-in step
- `brief.brand.colors_primary` / `colors_secondary` - ASS force-style for caption overlay
- `brief.source.language` - HeyGen voice locale
- `brief.output_dir` - where the final MP4 lands
- Custom field: `brief.avatar_id` and `brief.voice_id` (HeyGen-specific - these are NOT in the base schema; the orchestrator must read them from the user's response or a local avatar registry)

## Multi-clip consistency

If this dispatch is part of a **multi-clip avatar series** (Act 1 / Act 2 / Act 3 with the same speaker, multi-take spokesperson reel, brand-story arc), read [`../brand/consistency-rules.md`](../brand/consistency-rules.md) before drafting any clip script. HeyGen calls are stateless across clips — `avatar_id` locks the speaker's face, but the **described setting, outfit, props, and lighting in the script body** drift between clips unless you paste the same lock string verbatim into every clip's script. Don't say "the same speaker as before" — paste the full Character + Setting Lock block.

## Pre-flight checks

1. `HEYGEN_API_KEY` env var set. Set in `local/.env` (copy from `.env.example` at skill root) - never hardcode keys.
2. `brief.avatar_id` and `brief.voice_id` are present and non-empty. If missing, abort and ask the user. If `local/heygen-avatar-registry.md` exists, present its contents to the user as a picker. If the registry file does not exist yet, prompt the user to create it with their preferred avatar / voice combos.
3. `<brief.output_dir>/heygen/` exists
4. ffmpeg on PATH (for caption burn-in)

## Commands to run

```bash
# Step 1: write a small Node wrapper that follows the standard HeyGen V2 call shape

# File: <brief.output_dir>/heygen/run.mjs
# Structure (~30 lines):
#   1. read brief.json from <brief.output_dir>/brief.json
#   2. POST https://api.heygen.com/v2/video/generate
#      with { video_inputs: [{ character: { type: 'avatar', avatar_id, avatar_style: 'normal' },
#                              voice: { type: 'text', input_text: brief.notes, voice_id },
#                              background: { type: 'color', value: brief.brand.colors_bg || '#000000' } }],
#             dimension: { width, height } from brief.output.aspect mapping,
#             aspect_ratio: brief.output.aspect }
#      headers: { 'X-Api-Key': process.env.HEYGEN_API_KEY }
#   3. parse video_id from response
#   4. poll GET https://api.heygen.com/v1/video_status.get?video_id=<id>
#      every 5s, max 10 min, until status === 'completed'
#   5. download video_url to <brief.output_dir>/heygen/raw_01.mp4

# Step 2: run the wrapper
node <brief.output_dir>/heygen/run.mjs

# Step 3: caption burn-in via ffmpeg using brand_pill ASS preset
# Use the ASS template at <skill_root>/brand/captions.preset.json
# Expand into <brief.output_dir>/heygen/captions.ass with the script text + word timing
# (HeyGen does not return word-level timestamps - either run ElevenLabs Scribe on the
# raw_01.mp4 audio track to recover word timings, OR use sentence-level timing
# estimated from script length / video duration).

ffmpeg -i <brief.output_dir>/heygen/raw_01.mp4 \
  -vf "ass=<brief.output_dir>/heygen/captions.ass" \
  -c:a copy \
  <brief.output_dir>/heygen/out_01.mp4

# Step 4: if output.count > 1, regenerate with same avatar + voice but slightly varied
# script per ad_variant (rotated hooks, CTAs, etc).
```

## Output location

- Raw avatar video (no captions): `<brief.output_dir>/heygen/raw_NN.mp4`
- Final with brand-pill captions: `<brief.output_dir>/heygen/out_NN.mp4`

## Failure modes + recovery

1. **`avatar_id` not found**: HeyGen returns 404 with `error.code = "AVATAR_NOT_FOUND"`. Abort early - never silently swap to a different avatar. Tell the user the avatar_id was rejected and present the registry file.
2. **Rate limit (429)**: exponential backoff (5s, 15s, 45s) up to 3 retries. After 3, surface to the user.
3. **Render takes 90-180s** typical, up to 5 min on long scripts: poll status every 5s, show ETA in progress messages. Never go silent for more than 5s of polling without printing the current status.
4. **Caption burn-in fails because no word-level timings**: fall back to sentence-level captions via Scribe on the rendered MP4. Last resort: skip captions (style = none) and warn the user.

## Brief field -> CLI flag mapping

| Brief field | API field / behavior |
|---|---|
| `notes` | `video_inputs[0].voice.input_text` (the script) |
| `avatar_id` (custom) | `video_inputs[0].character.avatar_id` |
| `voice_id` (custom) | `video_inputs[0].voice.voice_id` |
| `output.aspect` | `dimension` (9:16 -> 720x1280, 16:9 -> 1280x720, 1:1 -> 720x720, 4:5 -> 720x900) + `aspect_ratio` field |
| `output.length_target_sec` | not directly settable - HeyGen renders to script length |
| `output.captions_style` | post-render ffmpeg ASS overlay |
| `brand.colors_bg` | `background.value` (default `#000000`) |
| `source.language` | `voice.locale` (or implicit via voice_id) |
| `output.count` | number of separate generate calls (with rotated script per call) |

## Notes for fork mode

HeyGen render is slow (90s-5min). When forked alongside Hedra, expect both to take similar time - they run in parallel via separate sub-agents. Warn the user up front: "HeyGen / Hedra forks add 2-5 min vs CutSense or video-use. Confirm fork_to_3 still desired." For ad-variant fork mode, batch all variants in one fork rather than running fork mode at the variant level.

## Avatar IV: multi-speaker dialogue mode

Opt-in mode for "two characters in conversation" deliverables (AI-generated podcast clip, debate-style ad, mock interview, two-host explainer). Triggered by the `dialogue_2shot` intent row above. Off by default — single-speaker explainer flow is unchanged.

**Source-to-deliverable pipeline** (single source of truth: the dialogue script):

1. **Generate two character images** (one per speaker). Use Sora / ChatGPT image gen (or any image model that produces a clean head-and-shoulders frame). Reference prompt shape that produces a naturally-angled "podcast guest" pose:
   > "head-and-shoulders photo of [CHARACTER] in a podcast studio, sitting in front of a podcast microphone, slight angle towards another person not visible in frame"
2. **Get reference audio for each speaker** (only if voice cloning a real voice; skip if using stock ElevenLabs voices). Pipeline: source URL -> download (e.g. snap-any.com or yt-dlp) -> trim a clean 10-30s sample (audiotrim.com or `ffmpeg -ss/-t`) -> upload to ElevenLabs **instant voice clone** (10s minimum, 30s+ recommended).
3. **Author the dialogue** in ElevenLabs **multi-speaker TTS Studio** as labeled turns (Speaker A / Speaker B). Click **Enhance** to auto-add emotional inflections per turn. Generate as a single audio file (the studio handles turn boundaries).
4. **Render lipsync per speaker turn** via HeyGen **Avatar IV** (NOT the standard `/v2/video/generate` avatar endpoint used elsewhere in this adapter). Avatar IV accepts `image_url` + `audio_url` instead of `avatar_id` + script. One render per speaker turn — the API does not natively cut between two characters in one call.
5. **Stitch turn renders** in CapCut or `ffmpeg concat` to produce the back-and-forth cut. This is where you also overlay any second-camera B-roll or cutaways.

**Inputs read from brief (Avatar IV mode only):**

- `brief.notes` — the dialogue script, formatted as `Speaker A: ...` / `Speaker B: ...` blocks (one block per turn)
- `brief.avatar_iv.speakers[]` — array of `{ name, image_url, voice_id }` (custom field, not in base schema; orchestrator reads from user's response or `local/heygen-avatar-iv-registry.md` if present)
- All other `brief.*` fields behave the same as single-speaker mode

**Pre-flight additions:**

- Confirm both speaker `image_url` values are reachable HTTPS (HeyGen pulls them server-side)
- Confirm both speakers' ElevenLabs `voice_id` exist (test with a 1-word TTS call before generating the full dialogue audio)
- If using cloned voices, confirm the source audio sample met ElevenLabs's quality bar (no cross-talk, no music bed, mono if possible)

**Failure modes specific to this mode:**

- **Mouth movement on the wrong syllable** — Avatar IV is more sensitive to audio quality than the standard avatar endpoint. Re-render with a higher-bitrate audio source (192k+ MP3 or WAV).
- **Lighting / color mismatch between the two character renders** — generate both character images with the same image-gen seed AND same lighting prompt fragment ("warm key light from camera-left, ambient fill"), or accept the mismatch as "two studio cameras."
- **Stitch jump cuts feel mechanical** — add a 200-400ms crossfade between turns in CapCut, or insert a 1-2s establishing wide shot (rendered separately) between Act-level breaks.

**Output location (Avatar IV mode):**

- Per-turn raw renders: `<brief.output_dir>/heygen/turn_NN_<speaker>.mp4`
- Stitched dialogue: `<brief.output_dir>/heygen/out_dialogue.mp4`
- Final with brand-pill captions: `<brief.output_dir>/heygen/out_dialogue_captioned.mp4`

**Caveats:**

- Avatar IV pricing tier differs from standard HeyGen avatar renders — confirm credits before committing to a long dialogue.
- The Sora/ChatGPT-generated character images are NOT consistent across separate generations. If the dialogue spans multiple sessions or you need to regenerate one character later, the character drift will be visible. To control for this, save each character's reference image alongside the brief and reuse.

## Reference

A typical multi-tenant production wires HeyGen via a `pickCloneProvider` rule (avatar_id present -> HeyGen, else Hedra). The wrapper script for this adapter should mirror that call shape exactly - same headers, same body structure, same polling pattern - so a future migration to a shared lib is trivial.
