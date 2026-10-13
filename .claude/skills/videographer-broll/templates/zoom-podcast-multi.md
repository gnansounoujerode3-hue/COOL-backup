# Template: Zoom Podcast Multi-Output

## When to use
Zoom recording (30-90 min, usually 2 speakers) where the user wants BOTH a polished long cut AND vertical clips for social. Triggers: "cut my podcast", "edit this Zoom", "make verticals from this episode", or any zoom_podcast source paired with vertical_clips + long_cut_polish intent.

## Default tool
**CutSense** - native multi-output (1 long cleaned cut + N verticals) from a single transcript pass; brand-pill captions wired in.

## Alternates (with pros/cons for the option block)
- **video-use** - pros: better at semantic clip picking from long content (embedding-based); cons: no built-in long-cut polish, must compose with another tool.
- **HyperFrames** - pros: brand-perfect per-vertical control with custom title cards; cons: manual per-clip composition, no automatic transcript -> clip mapping.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "vertical_clips",
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 60,
    "count": 5,
    "captions_style": "brand_pill",
    "music": "none"
  },
  "cleanup": {
    "remove_silences_over_sec": 1.0,
    "remove_filler_words": true,
    "remove_retakes": true,
    "loudness_target_lufs": -16,
    "true_peak_max_dbtp": -1.0,
    "normalize_audio": true
  },
  "qa_gates": ["face_safety", "loudness", "timing"]
}
```

Note: this template produces TWO output sets. The brief above describes the verticals. The long cut is rendered by the same CutSense run with `aspect: "16:9"`, `length_target_sec: <source_duration>`, `count: 1`, `captions_style: "none"`, and the same cleanup block. CutSense reads both targets from a single brief extension; see `adapters/cutsense.md` for the multi-output flag.

## Expected outputs
- 1 x 30-60 min 16:9 long cut at `<output_dir>\cutsense\out_long.mp4`
- 5 x 30-60s 9:16 verticals at `<output_dir>\cutsense\out_01.mp4` through `out_05.mp4`

## QA passes for this template
- face_safety: YES on verticals (brand_pill captions on faces is the most common ship-blocker for this template).
- loudness: -16 LUFS for both long cut and verticals (social default).
- timing: long cut duration within +/-2s of source minus removed silences; verticals 30-60s each.

## Tool-specific notes
- **CutSense**: invoke via `watch-video` skill OR direct `node ${CUTSENSE_DIR}/packages/renderer/scripts/render-cut.mjs --brief <path>`. Multi-output mode reads a `outputs[]` array if present in the brief (the orchestrator must add this when picking this template). Long cut has no captions because audience reads the YouTube/podcast transcript on the platform.
- **video-use**: clone at `${VIDEO_USE_DIR}/`. Best run as a fork-mode peer alongside CutSense to compare clip selection.
- **HyperFrames**: useful if any vertical needs a branded intro card; use as a follow-up step on a CutSense vertical, not as the primary cutter.
