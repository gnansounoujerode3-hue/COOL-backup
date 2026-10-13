# Template: Screen Recording Tutorial

## When to use
Software demo or tutorial captured via OBS/Loom/Mac screen recording (5-30 min). User wants a cleaned, chaptered tutorial with YouTube-format chapter markers. Triggers: "edit my tutorial", "clean up this Loom", any screen_recording source paired with tutorial_chaptered intent.

## Default tool
**CutSense** - aggressive silence removal + chapter markers extracted from transcript, jumbo captions for at-desk muted viewing.

## Alternates (with pros/cons for the option block)
- **video-use** - pros: smarter chapter boundary detection via semantic similarity (e.g. "now let's open settings" -> chapter break); cons: no native silence removal pass, must compose with CutSense for finishing.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "tutorial_chaptered",
  "output": {
    "format": "mp4",
    "aspect": "16:9",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 900,
    "count": 1,
    "captions_style": "jumbo",
    "music": "none"
  },
  "cleanup": {
    "remove_silences_over_sec": 0.6,
    "remove_filler_words": true,
    "remove_retakes": true,
    "loudness_target_lufs": -16,
    "true_peak_max_dbtp": -1.0,
    "normalize_audio": true
  },
  "qa_gates": ["face_safety", "loudness", "timing"]
}
```

Aggressive 0.6s silence threshold because tutorials have lots of "now I'm typing..." dead air. Captions use `jumbo` style (not `brand_pill`) because technical tutorials are watched muted at desks and the screen content needs maximum readability.

## Expected outputs
- 1 x 5-30 min cleaned chaptered tutorial at `<output_dir>\cutsense\out_long.mp4`
- 1 x chapter description text file at `<output_dir>\cutsense\chapters.txt` in YouTube format (e.g. `00:00 Intro`, `02:15 Setup`, `08:42 Running the demo`)

## QA passes for this template
- face_safety: YES IF a webcam corner exists in the recording (face-cam overlay). NO if pure screen-only.
- loudness: -16 LUFS. Screen recordings often have wildly inconsistent mic gain - normalize is mandatory.
- timing: keep screen visible at all times - timing QA must verify no black frames or scene drops introduced by aggressive silence cuts.

## Tool-specific notes
- **CutSense**: special flag `brief.notes = "Keep screen visible at all times. Silence cuts must not drop video frames, only collapse audio gaps with a smooth jump-cut on screen content."` The chapters.txt sidecar is produced from the transcript topic-segmentation pass and lives next to the MP4 for direct paste into YouTube descriptions.
- **video-use**: fork-mode peer when the tutorial covers 5+ distinct topics or features - embedding-based chapter boundaries beat transcript-keyword detection for technical content.
