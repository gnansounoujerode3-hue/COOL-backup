# Template: Scene Plan from Vague Brief

## When to use

User wants to generate a video from scratch (no source footage) but **the brief is too vague to feed directly to fal-seedance / Veo / HeyGen.** The user said something like:

- "make me a 30s video about [vague topic]"
- "I need a short ad for my product, surprise me"
- "do a launch video for X — figure out the shots"
- any "no source footage + no shot list + no story arc" combo

If the user already supplied a shot list, scene-by-scene table, or a fully-fleshed prompt body, **do not use this template** — go straight to the relevant generator adapter (fal-seedance, veo3, heygen).

## Default tool

**Pre-generation planning step. No render tool runs in this template.** This template's output is a **scene-by-scene shot table** that becomes the input for one of the generation adapters in step 2.

The template injects a "5-question intake -> shot table" turn between the orchestrator's Step 4 (surface options) and Step 5 (build the brief). It does **not** replace any existing flow step — it adds a planning conversation that produces a structured shot list before any prompt body is finalized.

## The 5 intake questions

Use `AskUserQuestion` in **one tool call** with these 5 questions. Phrase the options so the user can pick a default fast.

1. **Length and shot count**: "1 long shot (15s)" / "3-shot sequence (3x5s)" / "5-shot sequence (5x3s)" / "Other (specify)"
2. **Tone**: cinematic / documentary / playful / luxe / energetic / mysterious / corporate
3. **Subject**: founder-on-camera / product-only / lifestyle-with-people / abstract-no-people / mixed
4. **Setting**: real-world (specify location type) / studio / surreal / generated-environment / use-existing-footage-as-reference
5. **Audio intent**: native (let the model generate sound) / dialogue-needed (specify language) / music-bed-only / silent-with-overlay-text

If the user picks options that conflict (e.g. dialogue-needed + fal-seedance default tool), surface the conflict at the end of the intake and offer to switch tool (e.g. "Veo 3 handles native dialogue; fal-seedance does not — switch?").

## The shot table output

After the user answers, produce a markdown table with one row per shot. Use this exact schema so downstream adapters can parse it:

| # | Duration | Subject | Action | Environment | Camera move | Lighting | Audio |
|---|----------|---------|--------|-------------|-------------|----------|-------|
| 1 | 5s | ... | ... | ... | ... | ... | ... |
| 2 | 5s | ... | ... | ... | ... | ... | ... |
| 3 | 5s | ... | ... | ... | ... | ... | ... |

The fields map directly onto:
- fal-seedance: each row becomes one fal generation call. Concatenate via ffmpeg.
- veo3: each row's fields drop into the JSON prompt template at `adapters/veo3.md` (`subject`, `action`, `environment`, `camera_movement`, `lighting`, `audio`).
- heygen Avatar IV: shot table is bypassed; use this template's "Subject" + "Setting" answers for the speaker-image prompts instead.

Show the shot table to the user inline. Get their **explicit yes** before proceeding to Step 5 (build the brief). If they want changes to specific rows, edit those rows and re-confirm.

## Brief defaults (paste-ready JSON snippet)

```json
{
  "intent": "scene_planned_generation",
  "source": {
    "type": "none"
  },
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 15,
    "count": 1,
    "captions_style": "none",
    "music": "from_audio_field"
  },
  "cleanup": {
    "remove_silences_over_sec": null,
    "remove_filler_words": false,
    "remove_retakes": false,
    "loudness_target_lufs": -16
  },
  "scene_plan": {
    "shots": []
  },
  "tools": ["fal-seedance"],
  "fork_mode": "single",
  "qa_gates": ["timing", "audio_present", "hook_frame_match"],
  "output_dir": "${VIDEO_JOBS_DIR}/<brief_id>"
}
```

`scene_plan.shots[]` is an array of objects matching the shot table schema above. The orchestrator fills it from the user's confirmed table before dispatching.

## Multi-clip consistency

If the table has more than one row, the brief is a **multi-clip generation** — read [`../brand/consistency-rules.md`](../brand/consistency-rules.md) before dispatching to fal-seedance / veo3 / heygen. Each shot's `Subject` field MUST be the same byte-for-byte across rows when the same subject appears (e.g. founder, hero product). Only `Action`, `Environment`, `Camera move`, `Lighting`, and `Audio` may vary per row.

The shot-table schema above accommodates this: copy the Subject column from row 1 into every subsequent row that features the same subject. Do not paraphrase ("the founder from shot 1") — paste the full description.

## Alternates (when the user wants to skip the intake)

- **Skip directly to fal-seedance** with a single-shot one-liner — the user accepts mediocre output for speed. Useful when the brief is genuinely throwaway.
- **Pair with a kmboards `video-style-*` skill** for cinematic / e-com / social / brand-story / product-360 / fashion-lookbook intents — the style skill produces a beat-timeline prompt body without needing the 5-question intake. Use this when the intent matches one of those named buckets.

## Orchestrator integration notes

This template lives at `templates/scene-plan-from-vague-brief.md`. The orchestrator picks it during Step 2 (template lookup) when:

- `source.type == "none"` AND
- the user's request is too vague for any other `none`-source path (e.g. doesn't match a `video-style-*` intent, no explicit shot list provided)

When picked, this template REPLACES the standard 6-batched-questions of Step 3 (since the 5 intake questions above subsume them and add the shot-list output). After the user confirms the shot table, return to the standard Step 4 (surface options) and Step 5 (build the brief), passing `scene_plan.shots[]` along.

## Source

Pattern adapted from a "Let's make a movie" GPT-prompt-chain documented in the Guy Aga course (Module 5 - Video Generation). See [`course_gems.md`](C:\Users\raviv\Downloads\courseiq-package\courseiq\outputs\guyaga_manual_2026-05-03\deliverables\course_gems.md) item Tier 1 #4 for the original framing. Adapted to fit the orchestrator's brief schema and tool-routing flow.
