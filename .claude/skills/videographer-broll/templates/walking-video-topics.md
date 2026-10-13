# Template: Walking Video with Topic Chapters

## When to use
Handheld phone walking selfie monologue (5-30 min). User wants a polished long cut PLUS short chapter clips ("curiosity bits") with branded title cards per topic. Triggers: "edit my walking video", "chop my walk into topics", any walking_selfie source paired with chapter or topic-bit intent.

## Default tool
**CutSense --enhance** - auto-chapters from transcript, brand-pill captions, plus revideo brand title cards per chapter.

## Alternates (with pros/cons for the option block)
- **video-use** - pros: smarter chapter detection via semantic embeddings; cons: weaker brand title-card output.
- **HYBRID (CutSense + HyperFrames)** - pros: CutSense for the cut, HyperFrames for branded chapter intro cards; cons: 2-step pipeline, slower turnaround.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "long_cut_polish",
  "output": {
    "format": "mp4",
    "aspect": "16:9",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 600,
    "count": 1,
    "captions_style": "brand_pill",
    "music": "none"
  },
  "cleanup": {
    "remove_silences_over_sec": 1.5,
    "remove_filler_words": true,
    "remove_retakes": false,
    "loudness_target_lufs": -16,
    "true_peak_max_dbtp": -1.0,
    "normalize_audio": true
  },
  "qa_gates": ["face_safety", "loudness", "timing"]
}
```

Chapter clips ride along as a second outputs block: `aspect: "9:16"`, `length_target_sec: 60`, `count: 4`, `captions_style: "brand_pill"`. Each chapter clip = hook line in cyan pill (3-5s) + body in orange pill (rest).

## Expected outputs
- 1 x 5-15 min 16:9 long cut at `<output_dir>\cutsense\out_long.mp4`
- 3-5 x 30-90s 9:16 chapter clips at `<output_dir>\cutsense\chapter_NN.mp4` (each with branded title card on first 1.5s)

## QA passes for this template
- face_safety: YES (walking footage often has the face dead-center; brand pills must clear face bbox).
- loudness: -16 LUFS. Walking footage often has wind noise; check true peak after normalize.
- timing: keep walking pauses for natural feel - silences threshold is 1.5s here, not 1.0s.

## Caption MUSTs (walking selfies are caption-hostile - read this every time)

These four rules were learned the hard way on the 2026-04-26 walking-topics job. Every caption implementation MUST follow them or outputs get rejected.

1. **TRUE pill shape**: `border_radius >= height // 2`. libass `BorderStyle=4` is RECTANGULAR and is NOT acceptable. If your renderer can't draw real rounded pills, switch to PNG overlay via Pillow `rounded_rectangle` + ffmpeg `overlay` filter. Reference impl: `C:/Users/raviv/VideoJobs/2026-04-26-walking-topics-edit/merged/rebuild_captions.py`.
2. **Cut-aware reset**: phrases MUST NOT bridge EDL `range[]` boundaries. Iterate ranges separately; reset the phrase pointer at each boundary; compute cut-local timestamps from `cumulative_offset + (word.start - range.start)`.
3. **Filler removal from caption text**: drop `{um, uh, ah, er, hmm, mm, umm, uhh, ehh, uhm}` from the caption layer even if audio cleanup left them in. Match case-insensitive, strip trailing punctuation. Do NOT extend to ambiguous fillers (like, you know) without explicit user opt-in.
4. **Clear the mouth**: walking selfies move the face throughout the frame. Pills MUST be in the bottom 14-18% of the frame (margin_bottom_px ~80 on 1920h, two-pill stack ~240px tall). The face-safety QA gate FAILing means re-position lower, not just accept the warning.

See `brand/captions.preset.json -> implementation_rules` for the canonical specification.

## Tool-specific notes
- **CutSense --enhance**: enables the auto-chapter pass + revideo title cards. The orchestrator must set `brief.notes` to flag any must-keep walking pauses or natural beats.
- **video-use**: best for a fork-mode peer when the source has more than 5 distinct topics and chapter boundary precision matters.
- **HyperFrames hybrid path**: only invoke if the user explicitly asks for custom branded chapter intros; HyperFrames consumes the chapter list from CutSense's `chapters.json` and builds 1.5s intro cards per topic.
