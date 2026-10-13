# Adapter: fal-seedance (Bytedance Seedance 2.0 via fal.ai)

## What this tool does

Generates a fresh 4-15s video from a text prompt (and optionally up to 9 reference images, 3 reference clips, 3 audio clips). Bytedance Seedance 2.0, hosted on fal.ai. Native audio in the output. No source footage required.

The orchestrator dispatches here whenever the user wants to **make** a clip rather than **edit** existing footage.

## When the orchestrator dispatches here

| Source type | Intent | Notes |
|---|---|---|
| `none` (no source footage) | `cinematic_clip`, `hero_brand_film`, `founder_portrait`, `lone_figure_mood`, `dialogue_2shot`, `brand_hero_reveal`, `product_reveal_in_environment` | Pair with kmboards skill `video-style-cinematic` to produce the prompt body |
| `none` | `ecom_ad`, `product_demo_ad`, `apparel_ad`, `food_ad`, `electronics_ad`, `beauty_ad` | Pair with `video-style-ecom-ad` |
| `none` | `social_short`, `pov`, `before_after`, `walk_and_talk`, `screen_record_short`, `tutorial_handcam` | Pair with `video-style-social-hook` |
| `none` | `brand_origin`, `customer_testimonial`, `team_culture_day`, `mission_statement`, `anniversary` | Pair with `video-style-brand-story` |
| `none` | `turntable`, `product_360`, `multi_angle_showcase` | Pair with `video-style-product-360` |
| `none` | `lookbook`, `apparel_campaign`, `jewelry_hero`, `eyewear_lookbook`, `sneaker_drop`, `seasonal_reel` | Pair with `video-style-fashion-lookbook` |
| `image` (1 still, no video) | `animate_still`, `start_frame_only` | Use image-to-video variant (skip the kmboards style skill, prompt is short) |
| `references` (1+ images / 1+ clips / 1+ audio) | `reference_to_video`, any of the cinematic / ad / social style intents above WITH provided assets | Use reference-to-video variant. Strip `@image1` / `@video1` / `@audio1` markers from the prompt body, pass URLs as `image_urls` / `video_urls` / `audio_urls`. |

fal-seedance is the **only option** when there is no source footage and the user is not asking for an avatar lipsync (HeyGen / Hedra). For avatar lipsync, route to those instead.

## Two-skill pattern (recommended)

For cinematic / e-com / social / brand-story / product-360 / fashion-lookbook intents, the prompt body is too detailed to draft inline. The pattern is:

1. **Step A**: invoke the matching kmboards `video-style-*` skill (via the kmboards Standalone Agents tab, or call its system prompt directly via the Anthropic SDK if you have its body cached) with the user's brief. It returns a 15-25 line prompt with named camera moves, lighting, sound, beat timeline.
2. **Step B**: feed that prompt body into fal-seedance.

Direct fal calls without going through a style skill produce noticeably less coherent output (no beat timeline, no named camera language, no Rembrandt / Loop / Split lighting recipe). Use the style skill unless the user has already supplied a prompt in that format.

## Endpoints (raw fal API)

CRITICAL gotcha: Seedance is published under bare `bytedance/...`, NOT `fal-ai/bytedance/...`. The wrong prefix accepts the request and returns COMPLETED but the response body is `"Path not found"`. Empirically confirmed.

- text-to-video:       `POST https://queue.fal.run/bytedance/seedance-2.0/text-to-video`
- image-to-video:      `POST https://queue.fal.run/bytedance/seedance-2.0/image-to-video`
- reference-to-video:  `POST https://queue.fal.run/bytedance/seedance-2.0/reference-to-video`
- fast tier (~50% cost): insert `fast/` between `seedance-2.0/` and the variant.

Auth: `Authorization: Key <FAL_KEY>` (key format `<key_id>:<key_secret>` from fal dashboard).

## Inputs read from brief

- `brief.prompt` - the prompt body (probably from a `video-style-*` skill, possibly hand-written)
- `brief.output.aspect` - 16:9 / 9:16 / 1:1 -> passed as `aspect_ratio`
- `brief.output.length_target_sec` - 4-15 -> passed as `duration` (clamped)
- `brief.output.resolution` - `480p` / `720p` (default) / `1080p`
- `brief.source.image_url` (image-to-video only) -> `image_url`
- `brief.source.end_image_url` (image-to-video only) -> `end_image_url`
- `brief.source.references` (reference-to-video only):
  - `image_urls` (up to 9)
  - `video_urls` (up to 3)
  - `audio_urls` (up to 3)
- `brief.fast` - boolean, switches to fast/ tier
- `brief.negative_prompt` - optional

## Request body shape

```json
{
  "prompt": "<full prompt body, 15-25 lines for style-skill output>",
  "aspect_ratio": "16:9",
  "duration": 8,
  "resolution": "720p",
  "image_url": "<for image-to-video only>",
  "end_image_url": "<optional, for image-to-video>",
  "image_urls": ["...", "...", "..."],
  "video_urls": ["..."],
  "audio_urls": ["..."],
  "negative_prompt": "<optional>"
}
```

Only include the fields relevant to the chosen variant.

## Submit + poll pattern

```bash
# 1. Submit
RESP=$(curl -s -X POST "https://queue.fal.run/bytedance/seedance-2.0/text-to-video" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d @brief-body.json)
REQ=$(echo "$RESP" | jq -r '.request_id')
STATUS_URL=$(echo "$RESP" | jq -r '.status_url')
RESP_URL=$(echo "$RESP" | jq -r '.response_url')

# 2. Poll every 8s until COMPLETED or FAILED
for i in $(seq 1 60); do
  S=$(curl -s -H "Authorization: Key $FAL_KEY" "$STATUS_URL" | jq -r '.status')
  echo "tick $i: $S"
  case $S in COMPLETED|FAILED|ERROR) break;; esac
  sleep 8
done

# 3. Fetch result
curl -s -H "Authorization: Key $FAL_KEY" "$RESP_URL" | jq '.video.url'
# -> "https://v3b.fal.media/files/b/.../video.mp4"
```

## Outputs

Result JSON shape: `{video: {url, content_type, file_name, file_size}, seed}`.

Save the mp4 to `${VIDEO_JOBS_DIR}/<brief_id>/fal-seedance/out_01.mp4` (download from `video.url`; the URL is signed and expires ~24h, so don't rely on it long-term).

## Performance + cost

- Standard tier 8s/720p: ~3min queue-to-mp4
- Standard tier 4s/720p: ~90s
- Fast tier (insert `fast/` in path): ~50% time + ~50% cost
- Output: H.264 + AAC stereo @ 44.1kHz, 24fps

## Character + Product Consistency Across Multi-Clip Sequences

**Canonical source: [../brand/consistency-rules.md](../brand/consistency-rules.md). Read it before dispatching ANY multi-clip fal-seedance brief.**

TLDR for fal-seedance specifically:

When the brief calls for more than one fal-seedance clip in a row (Brand Story arc, Fashion Lookbook with multiple looks, Product 360 across angles, any chained sequence), each clip is an independent fal API call. The model has NO memory between calls. The 3 rules: clothing verbatim across clips, items verbatim across clips, only setting / background / time of day / lighting recipe / subject action change.

How the orchestrator applies this for fal-seedance:
- Draft a **Lock Block** once (Character / Casting / Product per the doc), ~50-100 words.
- Paste the Lock Block verbatim into the SUBJECT line of every clip's `prompt` field. Do not paraphrase between clips. Do not say "the founder from Act 1" - the model cannot back-reference.
- Per-clip variation: only the setting, time of day, lighting recipe, camera move, and subject action.
- For products in macro / hero / detail close-ups: the Lock stays in the SUBJECT line even when only a sliver of the product is on-camera - the model needs the off-screen description to render the on-screen part consistent.

Pair with kmboards' Phase B style skills (`video-style-brand-story`, `video-style-fashion-lookbook`, `video-style-product-360`) which bake their own Lock-Block sections into the prompt output contract. If those skills have produced the prompts, the Locks are already in place - just verify they appear in every clip.

Original source: Million Dollar Group Method, Lesson 13 - "Generating Content with AI" (kmboards Education Hub: https://kmboards.co/agents/dashboards/viral-content?tab=education).

## QA gates (specific to generated video)

- ffprobe duration matches expected (+/-2s)
- Audio track present (Seedance 2.0 has native audio - if missing, the model fell through to a silent variant)
- File size sanity-check: ~300-450KB per second at 720p (much smaller may indicate failed generation that returned a placeholder)
- Visual spot-check: extract frame 1 with `ffmpeg -ss 1 -i out.mp4 -frames:v 1 frame1.jpg` and inline it; confirm the prompt's hook frame is present

`run-qa.py` does the duration + audio checks automatically. The visual frame check is the orchestrator's job for fal-seedance outputs (since face-safety isn't relevant to a generated clip; we replace that gate with hook-frame match).

## Anti-patterns

- Calling fal with the `fal-ai/bytedance/...` prefix. Use bare `bytedance/...`.
- Using fal-seedance to "edit" existing footage. It can't. Route to CutSense.
- Pasting a hand-written 1-line prompt for a complex shot ("a cinematic founder portrait"). Always run through `video-style-cinematic` first to get the beat / camera / lighting / sound structure.
- Storing the `v3b.fal.media` URL in a database without downloading. The URL expires.
- Asking for >15s. Seedance 2.0 caps at 15s per clip. For longer pieces, generate multiple clips and concatenate via the editor agent.
- Generating multi-clip sequences without a Character + Product Lock block. Every detail you do not byte-repeat across clips will drift. See "Character + Product Consistency Across Multi-Clip Sequences" above.
- Paraphrasing the lock block between clips ("the founder from Act 1"). The model cannot resolve the back-reference - paste the full lock string verbatim.

## See also

- **[`../knowledge/fal-seedance.md`](../knowledge/fal-seedance.md)** — Layer-3 depth: the bare-prefix silent failure, poll pattern, caps, cost posture.
- **[`veo3.md`](veo3.md)** — alternative generator with native synced dialogue audio. Documented as a reference adapter; not yet wired into the default tool table. Pick over fal-seedance only when (a) the deliverable needs spoken dialogue with mouth-sync inside the generated clip itself, or (b) authentic Hebrew-accented English dialogue is required (see the Hebrew accent trick in veo3.md). For all other `none`-source dispatches, fal-seedance remains the default.
