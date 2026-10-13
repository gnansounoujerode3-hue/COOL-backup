# Template: Avatar Explainer from Script

## When to use
No source footage. User wrote a 60-180s narration script and wants an AI avatar talking-head explainer. Triggers: "make an avatar video of this", "have my avatar say this", any avatar_script source paired with avatar_explainer intent.

## Default tool
**HeyGen** - premade avatar lipsync from script using a registered avatar + voice; battle-tested standard V2 call shape.

## Alternates (with pros/cons for the option block)
- **Hedra** - pros: alternate lipsync engine, sometimes better for emotive/expressive delivery; cons: separate avatar registry, slower render queue at peak.

## Brief defaults (paste-ready JSON snippet)
```json
{
  "intent": "avatar_explainer",
  "output": {
    "format": "mp4",
    "aspect": "9:16",
    "resolution": "1080p",
    "fps": 30,
    "length_target_sec": 90,
    "count": 1,
    "captions_style": "brand_pill",
    "music": "none"
  },
  "cleanup": {
    "remove_silences_over_sec": null,
    "remove_filler_words": false,
    "remove_retakes": false,
    "loudness_target_lufs": -16,
    "true_peak_max_dbtp": -1.0,
    "normalize_audio": true
  },
  "qa_gates": ["face_safety", "loudness", "timing"]
}
```

Cleanup is N/A because the avatar IS the footage - no silences or filler to cut. Captions are overlaid AFTER the avatar render via a HyperFrames or CutSense follow-up pass.

## Expected outputs
- 1 x 60-180s talking-head at `<output_dir>\heygen\out_01.mp4` (default 9:16; switch to 16:9 if for web/embed)

## QA passes for this template
- face_safety: YES (brand_pill captions go on the avatar face just like a real face).
- loudness: -16 LUFS - HeyGen renders at variable LUFS, normalize after.
- timing: duration matches script-read time +/- 2s.

## Tool-specific notes
- **HeyGen**: requires `brief.avatar_id` and `brief.voice_id` from a registry. If no registry exists, ask the user to set one up at `local/heygen-avatar-registry.md` (1-line per persona: avatar_id + voice_id + 1-line description). HeyGen call shape: standard V2 endpoint with a typical `pickCloneProvider` rule (avatar_id present -> HeyGen, else Hedra).
- **Hedra**: alternate when the script has emotional beats that HeyGen renders flat. Same avatar/voice registry pattern; key in `local/.env` as `HEDRA_API_KEY`.
- After render, run a follow-up CutSense or HyperFrames pass to overlay brand_pill captions - the avatar tools do not produce them natively.
