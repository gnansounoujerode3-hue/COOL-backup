# Template: Branded Promo from URL

## When to use
User provides a URL (product page, landing page, app site) and wants a short branded promo video built from it. Triggers: "make a promo from this site", "turn this URL into a video", any url source paired with promo intent.

## Default tool
**website-to-hyperframes** - existing skill that captures the site, builds a HyperFrames composition with brand cyan/orange overlay treatment.

## Alternates (with pros/cons for the option block)
- **HyperFrames manual** - pros: full control over composition layout and timing; cons: no automatic web capture, manual screenshot + asset assembly, slower.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "promo",
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 20,
    "count": 1,
    "captions_style": "brand_pill",
    "music": "auto"
  },
  "cleanup": {
    "remove_silences_over_sec": null,
    "remove_filler_words": false,
    "remove_retakes": false,
    "loudness_target_lufs": -16,
    "true_peak_max_dbtp": -1.0,
    "normalize_audio": true
  },
  "qa_gates": ["loudness", "timing"]
}
```

Aspect: 9:16 default; switch to 1:1 if the placement is IG feed. Cleanup gates are N/A because web capture has no source audio to clean - music is auto-selected from the brand pack's `music_palette`.

## Expected outputs
- 1 x 15-30s promo at `<output_dir>\hyperframes\out_01.mp4` (or `<output_dir>\website-to-hyperframes\out_01.mp4` depending on which adapter handles the dispatch).

## QA passes for this template
- face_safety: NO (no face in web-capture promos by default; skip this gate unless the URL itself contains a hero image with a face that gets featured).
- loudness: -16 LUFS for the music bed.
- timing: 15-30s exactly.

## Tool-specific notes
- **website-to-hyperframes**: delegate to that skill for the capture step. It produces a HyperFrames project with the site's hero image, headline, and CTA already laid out. The brand pack at `<skill_root>/brand/pack-personal-social.json` ensures cyan #40DCE0 + orange #FCA529 overlay treatment matches the rest of the channel.
- **HyperFrames manual**: only when the user wants a non-standard composition (vertical scroll, multi-page narrative, animated logo reveal). Slower but full control.
