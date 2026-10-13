# Template: Zoom Lecture to Educational Verticals

## When to use
One speaker, educational content, 30-90 min, possibly with slides or screen-share visible. User wants 4-8 short shareable insight verticals. Triggers: "cut my talk into shorts", "make educational shorts from this lecture", any zoom_lecture source paired with educational_verticals intent.

## Default tool
**CutSense** - transcript-driven topic detection finds the "one insight per clip" beats; brand-pill captions are mandatory for sound-off readability.

## Alternates (with pros/cons for the option block)
- **video-use** - pros: stronger at finding the single-insight beats from a long lecture via embeddings; cons: no native brand caption pass, must hand off to CutSense or HyperFrames for finishing.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "educational_verticals",
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 75,
    "count": 6,
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

Heavy cleanup is the default here because lectures have repetitive examples and filler. Each vertical structure: hook (cyan pill, 3-5s) -> teach (10-50s, no pill or orange pill for context) -> CTA or punchline (cyan pill, 3-5s).

## Expected outputs
- 4-8 x 60-90s 9:16 verticals at `<output_dir>\cutsense\out_NN.mp4`

## QA passes for this template
- face_safety: YES, MANDATORY. Educational verticals are the highest face-safety risk because brand_pill captions are required and viewers focus on the speaker's face.
- loudness: -16 LUFS. Lecture audio often inconsistent (mic gain shifts) - normalize_audio must be on.
- timing: each clip 60-90s exactly; cut spacing > 0.4s (no jump-cut chains).

## Tool-specific notes
- **CutSense**: prompt the topic-detection pass to find "one teachable insight" per clip rather than "interesting moment". The orchestrator should add a `brief.notes` line: "One teachable insight per clip. Hook + teach + CTA structure."
- **video-use**: fork-mode peer when source > 60 min and the user wants 8+ outputs - embedding-based selection scales better than transcript scoring at that length.
