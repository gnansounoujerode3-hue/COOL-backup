# Adapter: Gemini Omni (Google DeepMind)

> **Status: WIRED. Model bumped 2026-08-29 to GA `gemini-omni-1.1-flash`.**
> Edit / generate / identity-lock claims below were verified end-to-end on 2026-08-10 against the preview (`gemini-omni-flash-preview`). 1.1 is the same Interactions API with three documented additions (extension, first+last interpolation, resolution). Those three are marked **docs-only** until a live clip proves them. Preview dies 2026-09-30.

## What this tool does

`gemini-omni-1.1-flash` generates and edits video with native audio from text, images, audio and video. Its distinguishing feature versus fal-seedance is **conversational editing of an existing clip** - upload a video, describe a change in plain language, get the changed video back with everything else preserved.

## When the orchestrator dispatches here

| Source type | Intent | Why Omni over the alternatives |
|---|---|---|
| `video` | `restyle_existing_clip`, `change_background`, `change_weather`, `change_lighting` | The only wired tool that edits an existing clip by description while preserving subject, wardrobe and props. Verified: "make it rain outside the window" held the subject, wardrobe, counter props and correctly cooled the grade for overcast light. |
| `image` | `character_locked_multi_shot` | A reference still locks face **and room** across wildly different shots. See "Identity locking" - this is the strongest character-consistency mechanism in the toolkit. |
| `none` | `single_10s_clip_with_speech` | Native spoken audio. But prefer fal-seedance when you need a length other than 10s (see limits). |

**Do NOT dispatch here for:** anything showing real product UI (standing Kivi rule - product video uses real screen recording), music or SFX (Omni is voice-only), or any clip that must not be ~10 seconds (still no duration field we can send).

## Access and cost - read before dispatching

- Key: `GEMINI_API_KEY` already present in `/opt/{youtubeiq,instaiq,tiktokiq}/.env` on the VPS (`104.200.30.37`). GCP project `kivimedia-api-keys`, billing `01937A`, card MC ••8761. No new key needed.
- **Flat ~$1.03 per clip.** 57,920 video tokens every time (@ $17.50/1M), regardless of prompt.
- **A Google AI Pro/Ultra subscription grants NOTHING here.** Consumer plans give Flow credits in the app; the API bills the GCP account separately and Omni has **no free tier**. Never propose "upgrade the subscription" as a way to reduce API cost.
- Because cost is per-clip and not per-second at the default 720p, **always plan shots at the full 10s and trim in the edit.** A 2s reaction shot costs the same $1.03 as a 10s one.
- Stay on **720p** unless Ziv explicitly asks higher. 1.1 accepts 1080p/4K as upscales and they cost more.

## Hard limits

| Thing | Reality |
|---|---|
| Duration | **No duration field we can send.** Preview always returned 10.005s. 1.1 docs list 3s-10s. Plan 10s, trim after. |
| Resolution | Default 720p. 1.1 docs: 360p / 720p / 1080p / 4k in `response_format.resolution`. 1080p and 4K are upscaled. **Do not send 1080p unless asked.** |
| Aspect | 16:9 or 9:16 only |
| Audio | AAC, speech only. **No music, no SFX** - those come from the library or `music-sfx.md`. |
| Provenance | **C2PA metadata baked into every file** marking it AI-generated. Assume clients can detect it. |
| Region | Editing or extending uploaded video is blocked in the EEA, Switzerland, UK. Fine from Israel. Generated-clip edits work everywhere Omni is available. |
| Latency | 30-70s per clip at 720p. Higher res takes longer. |

## 🚨 Rule 1: identity comes from a reference still, never from words

**Verified failure:** two shots, the same room described identically in prose, no reference image, produced **a different man in a different room** - different face, brown chair instead of green, furniture that did not exist in the first shot. Uncuttable.

**Verified fix:** upload one frame of the character and pass it as an `image` input. Two wildly different shots against the same still (medium two-hands shot AND tight close-up) came back with the same face, beard, glasses, build and suit down to the pocket square and watch chain - **and the same room**: same armchair, lamp, couch, rug, clock.

So for any multi-clip brief:
1. Generate or choose ONE canonical still of the subject.
2. Upload it once, reuse the returned `files/...` URI for every shot.
3. Never describe the face again in prose.

This supersedes the verbatim Lock Block text approach from [`../brand/consistency-rules.md`](../brand/consistency-rules.md) **when the tool is Omni**. Keep the Lock Block for frame-independent tools that take no reference image. Weak fallback if no still exists: paste the exact same character sentence verbatim into every prompt - it gets adjacent shots to match, but is not reliable enough for a paid deliverable.

## 🚨 Rule 2: never direct a hand gesture that moves an object

**Verified failure, twice independently:** a prompt asking a character to "take a puff on a cigar, then deliver a line" caused the model to **spawn a second cigar** mid-gesture. He holds one in each hand for ~0.8s before it settles into the resting hand. At speed it reads as the object switching hands.

**Omni cannot fix this on request.** Uploading the clip and asking as narrowly as possible to keep the cigar in one hand returned the *identical* flaw. That is $1.03 for nothing - do not attempt it.

**The fix is staging, not prompting.** Direct the object to rest - on an armrest, in an ashtray, on a table - and never move. Put all performance in the face, eyes and pause. Verified: same character, same line, hands still, gesture removed → one object, one hand, whole clip, no duplication.

Applies to: picking up, putting down, passing, pouring, opening doors, handing over. **When building prompts from the Creative Director's `visual_direction`, strip any object-in-hand motion before dispatching.**

## Request shapes (working, tested)

Generate. Omit `response_format` entirely:

```json
POST https://generativelanguage.googleapis.com/v1beta/interactions?key=$GEMINI_API_KEY
{ "model": "gemini-omni-1.1-flash", "input": "<prompt>" }
```

With a reference image or an uploaded video for editing - `input` becomes an array. Video uses `type: document`, a reference image uses `type: image`:

```json
{ "model": "gemini-omni-1.1-flash",
  "input": [ {"type":"image","uri":"files/w5zwzys0rllv"},
             {"type":"text","text":"<prompt>"} ],
  "response_format": { "type": "video", "aspect_ratio": "16:9", "resolution": "720p" } }
```

Upload first via the **resumable** Files API (`POST /upload/v1beta/files` with `X-Goog-Upload-Protocol: resumable`, then PUT bytes with `X-Goog-Upload-Command: upload, finalize`), and **poll `files/{id}` until `state == ACTIVE`** before referencing it.

Output is **inline base64 MP4** at `steps[].content[].data` - NOT a URL. Decode and write to disk.

## `previous_interaction_id` is edit-only unless you ask to extend

It re-renders **the same moment** with edits applied. Use it for "make it rain outside the window".

**1.1 docs (not yet dogfooded here):** extension is now supported. Prompt "Continue the scene" / "Extend this video", or set `generation_config.video_config.task` to `extend`. Appends 3-10s at the tail only - no prepend, no mid-clip insert. Input for uploaded extend must be 10s or less. Do not add spoken dialogue when extending an uploaded talking clip.

Until a live 1.1 clip proves extension, treat multi-shot sequencing as reference stills (Rule 1), not chaining.

## Editing re-renders, including the audio

An edit generates a whole new video with **new audio**. Never send a take whose delivery is landing - you are gambling the performance to fix the picture. Edits succeed at broad changes (background, weather, restyle, light) and fail at fine physical continuity.

## QA checklist before returning a clip

1. **Scrub the whole 10s, never judge from one frame.** The duplicate-cigar artifact was missed twice by sampling frames that straddled it.
2. **Look hardest at 1.8-2.6s** - both verified failures landed in that band, right where the action starts.
3. Check hands and props specifically: count the objects.
4. To locate speech without listening:
   `ffmpeg -i x.mp4 -af "atrim=start=T:end=T+1,volumedetect" -f null -` per second.
   **Do NOT pass `-v error`** - it suppresses the measurement and returns blank.
5. State plainly in the handback that clip audio has not been listened to, if it has not.

## Unverified (1.1 docs, 2026-08-27)

- **Video extension** actually succeeding on our key (preview returned 400).
- **First + last frame interpolation** (two images in `input`).
- **`resolution: 1080p` / `4k`** producing a real upscale, and the extra cost.
- **`delivery: "uri"`** for clips larger than 4MB.
- Google Flow's **Ingredients / Scenebuilder / Camera Controls** UI.
