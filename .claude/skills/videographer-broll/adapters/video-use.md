# Adapter: video-use

## What this tool does

[video-use](https://github.com/browser-use/video-use) is an LLM-driven CLI editor: ElevenLabs Scribe word-level transcription -> phrase-level packed transcript -> editor sub-agent picks an EDL -> per-segment ffmpeg extract + lossless concat + overlays + subtitles. Best when you want smarter semantic chapter detection than CutSense's default, or when you need parallel animation sub-agents for inline visualizations (Manim / PIL / Remotion slots).

## When the orchestrator dispatches here

| Source type | Intent | Why over CutSense |
|---|---|---|
| `zoom_podcast` | `vertical_clips`, `long_cut_polish` | Better at picking the actual best 60s out of a 60-min raw call |
| `zoom_lecture` | `educational_verticals` | Semantic chapter detection across many topics |
| `walking_selfie` | `vertical_clips`, `long_cut_polish` | When the user has many takes and wants the LLM to dedupe + pick |
| any of above | when CutSense WhisperX fails on Windows | Fallback path |

Routes here when the user says things like "pick the best 5 moments", "find the highlights yourself", or when they explicitly mention `video-use`.

## Inputs read from brief

- `brief.source.path` - absolute path to the source video
- `brief.source.duration_sec` - sanity check
- `brief.source.language` - passed to Scribe
- `brief.intent` - drives the editor sub-agent's strategy prompt
- `brief.output.length_target_sec` + `output.count` - drives EDL target duration
- `brief.output.aspect` - drives crop / scale in render
- `brief.output.captions_style` - drives subtitle ASS force-style
- `brief.cleanup.*` - silences and fillers handled by the editor sub-agent natively
- `brief.brand.colors_primary` / `colors_secondary` - injected into ASS subtitle style
- `brief.notes` - PRESERVE / CUT moments fed verbatim to the editor sub-agent
- `brief.output_dir` - where final MP4s land

## Pre-flight checks

1. `${VIDEO_USE_DIR}/` exists. If missing, prompt to install:
   ```bash
   git clone https://github.com/browser-use/video-use ${VIDEO_USE_DIR}
   cd ${VIDEO_USE_DIR}
   uv sync
   ```
2. `${VIDEO_USE_DIR}/.env` contains:
   ```
   ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
   GROQ_API_KEY=${GROQ_API_KEY}
   ```
   Set both in `local/.env` (copy from `.env.example` at skill root) - never write keys outside the local env file.
3. `ffmpeg` and `ffprobe` on PATH
4. `<brief.output_dir>/video-use/edit/` is the per-session edit dir (per video-use SKILL.md rule: never write inside the `video-use/` project dir)

## Commands to run

```bash
# Step 1: prepare the per-session edit dir
mkdir -p <brief.output_dir>/video-use/edit

# Step 2: transcribe (cached - skipped if the source file hash matches an existing transcript)
python ${VIDEO_USE_DIR}/helpers/transcribe.py "<brief.source.path>"

# Step 3: pack the transcript into phrase-level view for the editor sub-agent
python ${VIDEO_USE_DIR}/helpers/pack_transcripts.py \
  --edit-dir <brief.output_dir>/video-use/edit/

# This writes <output_dir>/video-use/edit/takes_packed.md

# Step 4: spawn an editor sub-agent (in-conversation, NOT shell)
# The sub-agent receives:
#   - takes_packed.md path
#   - brief JSON (read-only)
#   - target output: <output_dir>/video-use/edit/edl.json
# It must follow video-use SKILL.md hard rules (subtitles last, lossless concat,
# 30ms fades, word-boundary cuts, 30-200ms padding, parallel animation sub-agents).
# Strategy MUST be confirmed before render - in fork mode, the editor sub-agent
# proposes-and-executes in one shot using brief.intent + brief.notes as the confirm.

# Step 5 (optional): if the editor sub-agent identified animation slots,
# spawn parallel animation sub-agents (one Agent call PER slot, all in one
# assistant turn). Each writes:
#   <output_dir>/video-use/edit/animations/slot_<id>/render.mp4

# Step 6: render the final cut
python ${VIDEO_USE_DIR}/helpers/render.py \
  <brief.output_dir>/video-use/edit/edl.json \
  -o <brief.output_dir>/video-use/out_01.mp4 \
  --build-subtitles

# Step 7: if output.count > 1, repeat steps 4-6 with edl_02.json, edl_03.json...
# OR ask the editor sub-agent to produce an EDL that emits multiple ranges as
# separate output files in one pass (preferred when count > 2).
```

## Output location

Per-session artifacts live at `<brief.output_dir>/video-use/edit/`:

```
edit/
  project.md                  (memory, append per session)
  takes_packed.md             (LLM's primary reading view)
  edl.json                    (cut decisions)
  transcripts/<name>.json     (Scribe cache - keep)
  animations/slot_<id>/       (per-slot render dirs)
  master.srt                  (compiled subtitles)
  preview.mp4                 (optional preview pass)
```

Final MP4s go to `<brief.output_dir>/video-use/out_NN.mp4`.

## Failure modes + recovery

1. **`ELEVENLABS_API_KEY` missing or invalid**: abort. Tell the user to set it in `${VIDEO_USE_DIR}/.env`. Never silently fall back to local Whisper - per video-use SKILL.md hard rule, word-level verbatim ASR only.
2. **video-use install missing at `${VIDEO_USE_DIR}/`**: prompt the user with the clone + `uv sync` command above. Do not auto-clone without confirmation.
3. **Cached transcript stale** (source file modified since transcript was cached): delete `<brief.output_dir>/video-use/edit/transcripts/<name>.json` and rerun step 2. Detection: compare `mtime` of source file vs transcript JSON.
4. **Editor sub-agent picks cuts that fail QA timing gate** (e.g. mid-word): the EDL must be regenerated. Hard rule: cuts snap to Scribe word boundaries with 30-200ms padding.
5. **Animation slot fails**: the render falls back to no-overlay for that slot rather than blocking the whole edit.

## Brief field -> CLI flag mapping

| Brief field | CLI flag / behavior |
|---|---|
| `source.path` | positional argument to `transcribe.py` |
| `source.language` | passed to Scribe via env or default auto-detect |
| `intent` | embedded in editor sub-agent strategy prompt |
| `output.length_target_sec` | EDL `total_duration_s` field |
| `output.count` | number of EDL ranges or repeat invocations |
| `output.aspect` | render.py crop / scale params |
| `output.captions_style` | ASS force-style (brand_pill maps to cyan/orange pill ASS template) |
| `cleanup.remove_silences_over_sec` | editor sub-agent prompt constraint |
| `cleanup.remove_filler_words` | editor sub-agent prompt constraint |
| `cleanup.remove_retakes` | editor sub-agent prompt constraint |
| `brand.colors_primary` / `colors_secondary` | ASS subtitle style overrides |
| `notes` | PRESERVE / CUT directives in editor sub-agent prompt |

## Caption MUSTs (read brand/captions.preset.json -> implementation_rules)

video-use's default ASS-subtitle pipeline produces RECTANGULAR boxes via `BorderStyle=4`, which violates the brand spec (real pill shape required). For any `brand_pill*` captions_style, the adapter MUST switch to PNG overlay rendering:

1. Build phrase PNGs via Pillow (`rounded_rectangle` with `radius = height // 2`).
2. Render each phrase at the cut-local time, never bridging EDL `range[]` boundaries.
3. Drop filler words `{um, uh, ah, er, hmm, mm, umm, uhh, ehh, uhm}` from caption text (audio cleanup is separate).
4. Position in bottom 14-18% of frame (margin_bottom ~80px on 1920h verticals).
5. Use ffmpeg `overlay` filter chain (one overlay per phrase with `enable='between(t,start,end)'`).

Reference implementation: `C:/Users/raviv/VideoJobs/2026-04-26-walking-topics-edit/merged/rebuild_captions.py` (cut-aware, filler-clean, true pill, mouth-clear).

If `brief.output.captions_style == "natural_sentence"` or `"jumbo"` (no pill required), the legacy ASS path is fine. Pill styles MUST go through PNG overlay.

## Notes for fork mode

video-use produces the highest-quality cut on talking-head sources but takes 2-4 min for transcription on a 60-min source (Scribe API), plus 30-60s for the editor sub-agent and 1-2 min for render. Total: ~5-7 min for a 60-min source. Faster than HyperFrames, slower than CutSense. Forks against CutSense and HyperFrames safely - all three use distinct working dirs and do not share state.

In fork mode, the editor sub-agent runs without confirm-and-wait - it uses `brief.intent` + `brief.notes` as the implicit confirmation. This trades safety for parallelism and is acceptable when the user has explicitly chosen `tool_mode = fork_to_3`.

## Multi-clip consistency (does not apply here)

The 3 Consistency Rules in [`../brand/consistency-rules.md`](../brand/consistency-rules.md) are about preventing drift between independently-generated AI clips. video-use cuts existing recorded footage based on transcript - the speaker / wardrobe / location are whatever was filmed, identical across every output. Skip the Lock-Block step for video-use dispatches.
