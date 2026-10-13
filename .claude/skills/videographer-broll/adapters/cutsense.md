# Adapter: CutSense

## What this tool does

CutSense is a 3-layer AI video pipeline (ingest -> understand -> edit) at `${CUTSENSE_DIR}/` (your local CutSense clone). It transcribes word-level, builds a Video Understanding Document (VUD), and renders cuts via Remotion with brand-pill captions baked in. Default for any talking-head footage where you have raw source and want fast multi-vertical output without hand-authoring the cut.

## When the orchestrator dispatches here

| Source type | Intent | Template |
|---|---|---|
| `zoom_podcast` | `vertical_clips`, `long_cut_polish` | `zoom-podcast-multi.md` |
| `zoom_lecture` | `educational_verticals` | `zoom-lecture-verticals.md` |
| `walking_selfie` | `vertical_clips` | `walking-video-topics.md` |
| `screen_recording` | `tutorial_chaptered` | `screen-recording-tutorial.md` |
| any of above | `ad_variants` (when source footage exists) | `ad-hook-variations.md` |

CutSense is the **default first option** any time `brief.source.path` points to a real recorded file.

## Inputs read from brief

- `brief.source.path` - absolute path to the source video
- `brief.intent` - drives the natural-language prompt passed to `cutsense run --prompt`
- `brief.output.length_target_sec` - target duration per output
- `brief.output.count` - number of outputs (CutSense produces N variants in one run)
- `brief.output.aspect` - 9:16, 1:1, 16:9, or 4:5
- `brief.output.captions_style` - mapped to `--captions` flag (see table below)
- `brief.cleanup.remove_silences_over_sec` - mapped to `--silence` flag
- `brief.cleanup.remove_filler_words` - if true, included in prompt
- `brief.source.language` - mapped to `--language` flag
- `brief.brand.pack` - already wired via `render-cut.mjs`, no extra hand-off needed
- `brief.output_dir` - where final MP4s land
- `brief.notes` - appended to the prompt (preserve / cut moments)

## Pre-flight checks

1. `cutsense --version` returns a version (or `cd ${CUTSENSE_DIR} && npx cutsense --version`)
2. `ffprobe "<brief.source.path>"` succeeds and reports duration > 0
3. At least one of `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_AI_API_KEY` is set in the environment
4. `<brief.output_dir>/cutsense/` exists (mkdir -p if not)
5. Free disk on the working drive > 10GB (CutSense caches frames + transcripts in `~/.cutsense/jobs/`)

## Commands to run

```bash
# Step 1: build the prompt from intent + notes
PROMPT="<derived from brief.intent + brief.output.length_target_sec + brief.output.count + brief.notes>"
# Example for vertical_clips: "Cut <count> vertical clips of ~<length>s each, keep highlights, remove false starts. Notes: <brief.notes>"

# Step 2: map captions_style -> CutSense flag
# brand_pill -> standard
# jumbo      -> jumbo
# none       -> none
# natural_sentence -> standard

# Step 3: run CutSense
cd ${CUTSENSE_DIR}
npx cutsense run "<brief.source.path>" \
  --prompt "<PROMPT>" \
  --captions <mapped captions> \
  --silence <brief.cleanup.remove_silences_over_sec> \
  --language <brief.source.language> \
  --enhance \
  --duration <brief.output.length_target_sec>

# Step 4: capture the job-id from stdout
# CutSense prints "job-id: <uuid>" - parse and store as JOB_ID

# Step 5: copy outputs into the orchestrator convention
# Source: ~/.cutsense/jobs/<JOB_ID>/output/*.mp4
# Dest:   <brief.output_dir>/cutsense/out_NN.mp4 (NN = 01, 02, ... in original order)
```

## Output location

CutSense writes to `~/.cutsense/jobs/<job-id>/output/`. After the run, copy each `.mp4` into `<brief.output_dir>/cutsense/out_01.mp4`, `out_02.mp4`, etc. Preserve the original CutSense filename in a sidecar `.json` so QA can trace back.

## Failure modes + recovery

1. **WhisperX crashes on Windows** (most common): rerun with `--no-enhance`. If still failing, the orchestrator falls back to `video-use` adapter for the same brief.
2. **Python venv missing**: CutSense auto-creates on first run. If creation fails, run `npx cutsense doctor` and follow its hint. Usually means Python 3.10+ is missing from PATH.
3. **Remotion `--props` inline JSON breaks** on long prompts: CutSense already writes props to a temp file path. If you see "argument list too long", confirm CutSense is current (`git pull` in the repo).

## Brief field -> CLI flag mapping

| Brief field | CLI flag / behavior |
|---|---|
| `source.path` | positional argument to `cutsense run` |
| `intent` | embedded in `--prompt` string |
| `output.length_target_sec` | `--duration <n>` |
| `output.count` | embedded in prompt ("Cut N clips...") |
| `output.aspect` | embedded in prompt ("output 9:16 vertical") |
| `output.captions_style` | `--captions standard|jumbo|none` (brand_pill -> standard, brand colors are hardcoded in `render-cut.mjs`) |
| `cleanup.remove_silences_over_sec` | `--silence <n>` |
| `cleanup.remove_filler_words` | embedded in prompt |
| `source.language` | `--language <code>` |
| `notes` | appended to prompt verbatim |

## Notes for fork mode

CutSense is the fastest fork to complete on talking-head footage (most cuts under 4 min for a 60-min source). Safe to fork against `video-use` and `hyperframes` simultaneously - their working dirs do not collide. Each fork must use its own job dir and copy outputs into its own `<output_dir>/cutsense/` slot.

## Hand-off rule

If the user explicitly said "use cutsense" (per orchestrator precedence rule), do NOT run this adapter directly. Hand off to the `watch-video` skill instead - it owns the direct CLI invocation. This adapter is for when the orchestrator picks CutSense.

## Brand wiring (already done)

The cyan `#40DCE0` + orange `#FCA529` brand-pill captions are hardcoded in `${CUTSENSE_DIR}/packages/renderer/scripts/render-cut.mjs`. Do not pass brand colors through the CLI - they will be ignored. Brand override only happens by editing `render-cut.mjs` or swapping the brand pack.

## Multi-clip consistency (does not apply here)

The 3 Consistency Rules in [`../brand/consistency-rules.md`](../brand/consistency-rules.md) are about preventing drift between independently-generated AI clips. CutSense edits existing recorded footage - the source is byte-stable across every cut, so character / clothing / prop drift is impossible by construction. Skip the Lock-Block step for CutSense dispatches.
