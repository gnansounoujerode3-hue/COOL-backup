# Knowledge pack: fal-seedance (Bytedance Seedance 2.0 via fal.ai)

Layer-3 depth behind `adapters/fal-seedance.md`. The adapter has the dispatch logic;
this is the provider behaviour you need when it misbehaves.

## The prefix gotcha (the #1 silent failure)

Seedance is published under bare `bytedance/...`, NOT `fal-ai/bytedance/...`. The wrong
prefix is accepted, returns `COMPLETED`, and the response body is `"Path not found"`.
Always use:
- `https://queue.fal.run/bytedance/seedance-2.0/text-to-video`
- `.../image-to-video`, `.../reference-to-video`
- fast tier: insert `fast/` after `seedance-2.0/` (~50% time + cost).

Auth: `Authorization: Key <FAL_KEY>` where the key is `<key_id>:<key_secret>`.

## Submit + poll (async queue)

1. POST the body -> `{ request_id, status_url, response_url }`.
2. Poll `status_url` every ~8s until `COMPLETED | FAILED | ERROR`.
3. GET `response_url` -> `{ video: { url }, seed }`. Download the mp4 immediately - the
   `v3b.fal.media` URL is signed and expires ~24h.

Standard 8s/720p ~ 3min; 4s/720p ~ 90s. Fast tier roughly halves both.

## Caps + inputs

- Duration: 4-15s per clip. For longer, generate multiple and concatenate (editor agent).
- Resolution: 480p / 720p (default) / 1080p.
- Aspect: 16:9 / 9:16 / 1:1 via `aspect_ratio`.
- Reference-to-video: up to 9 `image_urls`, 3 `video_urls`, 3 `audio_urls`. Strip the
  `@image1/@video1/@audio1` markers from the prompt body; pass the URLs in the arrays.
- Native audio: Seedance 2.0 outputs sound. If the result is silent, the model fell through
  to a silent variant - regen.

## Multi-clip consistency

Each call is stateless - no memory between clips. Paste a **Lock Block** (character / product
/ casting per `../brand/consistency-rules.md`) byte-identical into the SUBJECT line of every
clip's prompt. Never "the founder from Act 1" - the model cannot back-reference. The kmboards
`video-style-brand-story / -fashion-lookbook / -product-360` skills bake Locks into their output.

## Prompt quality

Hand-written one-liners produce incoherent output. Run the brief through a kmboards
`video-style-*` skill first to get a 15-25 line body with named camera moves, lighting recipe,
sound, and a beat timeline. Direct fal calls without that structure look noticeably worse.

## Cost posture

Metered. Free-first means: if a shot could be a real free b-roll clip instead of a paid
generation, prefer the b-roll. Use the fast tier for drafts. Estimate against the pipeline's
budget cap before generating a batch, and never batch metered generation without the human
proposal-gate approval.

## QA

ffprobe duration (+/-2s), audio-present, file-size sanity (~300-450KB/s at 720p; far smaller =
failed/placeholder), and a frame-1 visual spot-check (face-safety is irrelevant to a generated
clip; replace it with a hook-frame match).

## See also

- Adapter: `../adapters/fal-seedance.md`
- Alternative generator with synced dialogue: `../adapters/veo3.md`
