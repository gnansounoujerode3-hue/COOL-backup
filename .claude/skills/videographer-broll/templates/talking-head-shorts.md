# Template: Talking-Head Shorts (3-Up)

## When to use
Already-short talking-head footage (under 5 min) OR a specific bit pulled from longer source. User wants 3 different short cuts from one piece. Triggers: "make 3 shorts from this", "give me 3 cuts of this clip", any talking-head source paired with vertical_clips intent and `count: 3`.

## Default tool
**CutSense** - 3 different cut points from the same source in one pass; brand-pill captions wired in.

## Alternates (with pros/cons for the option block)
- **HyperFrames-only** - pros: TTS the script + brand composition, no original footage needed (useful when source audio quality is poor); cons: no original speaker face, less authentic feel.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "vertical_clips",
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 45,
    "count": 3,
    "captions_style": "brand_pill",
    "music": "none"
  },
  "cleanup": {
    "remove_silences_over_sec": 0.8,
    "remove_filler_words": true,
    "remove_retakes": true,
    "loudness_target_lufs": -16,
    "true_peak_max_dbtp": -1.0,
    "normalize_audio": true
  },
  "qa_gates": ["face_safety", "loudness", "timing"]
}
```

## Expected outputs
- 3 x 30-60s 9:16 verticals at `<output_dir>\cutsense\out_01.mp4`, `out_02.mp4`, `out_03.mp4` - each a different cut/angle of the same source.

## QA passes for this template
- face_safety: YES (brand_pill on close-up talking-head is the highest-risk caption placement).
- loudness: -16 LUFS.
- timing: each clip 30-60s; if all 3 cuts produce nearly identical durations, the cut points are too close - flag for re-pick.

## Tool-specific notes
- **CutSense**: orchestrator must pass `brief.notes` saying "3 distinct cut points - each clip should highlight a different beat of the source, not 3 variations of the same beat."
- **HyperFrames-only fallback**: when the user flags poor source audio, switch to HyperFrames + ElevenLabs TTS using the brand voice. The script becomes the source; output composition is brand-styled with kinetic type, no face. Brief tools array becomes `["hyperframes"]` instead of `["cutsense"]`.
