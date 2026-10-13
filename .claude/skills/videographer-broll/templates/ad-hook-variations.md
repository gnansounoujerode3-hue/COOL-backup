# Template: Ad Hook Variations (3-Up)

## When to use
User has an existing video clip OR an avatar_script and wants 3 ad variants with different hook lines but the same body content. Triggers: "make 3 ad hooks", "test 3 versions of this ad", any source paired with ad_variants intent.

## Default tool
**HyperFrames + CutSense (hybrid)** - HyperFrames builds 3 hook intros (different colors/fonts/words per variant), CutSense produces the body cut once; concatenation produces 3 final variants.

## Alternates (with pros/cons for the option block)
- **HeyGen (3-variant)** - pros: 3 avatar variants reading 3 different hooks, useful when no source footage exists; cons: avatar render queue cost x3, less spontaneous feel than real footage.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "ad_variants",
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 22,
    "count": 3,
    "captions_style": "brand_pill",
    "music": "auto"
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

Hooks render in cyan #40DCE0 pill (the "main thing being said" per brand pack), body context in orange #FCA529 pill. Each variant is hook A/B/C + identical body cut.

## Expected outputs
- 3 x 15-30s ad variants at `<output_dir>\hyperframes\hook_A.mp4`, `hook_B.mp4`, `hook_C.mp4` (each a hook intro concatenated with the shared body cut at `<output_dir>\cutsense\body.mp4`).

## QA passes for this template
- face_safety: YES (brand pills overlay on hooks must clear face if hook intros use real footage; N/A if hooks are pure-type HyperFrames compositions).
- loudness: -16 LUFS. Hook + body audio levels must match across the cut for clean concatenation.
- timing: each variant 15-30s. Hook portion should be 3-5s, body portion 12-25s.

## Tool-specific notes
- **Fork-mode-friendly**: this is the canonical fork-mode template. Each hook = one parallel sub-agent (3 HyperFrames hook compositions in parallel), CutSense body cut runs as a 4th parallel agent. Final assembly (concat) runs after all 4 return. Use `tool_mode = fork_to_3` even if the user said `pick_best` - the parallelism is built into the template.
- **HyperFrames hook composition**: each variant uses the brand pack but varies hook word count (short/medium/long) and pill color emphasis. The 3 hooks are different ANGLES on the same offer, not variations of the same line.
- **HeyGen alternate**: when no source footage exists, swap CutSense for HeyGen on the body and use HyperFrames for hook intros. Avatar registry rules from `avatar-explainer.md` apply.
