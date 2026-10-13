# Templates Index

These templates are scenario-specific extensions of the video-orchestrator flow. Each one names a default tool, lists alternates with pros/cons, seeds `brief.json` defaults, and lists the QA passes to run. The orchestrator (`SKILL.md`) reads this index after Step 1 (identify the source) to pick the closest template, then customizes the brief from the user's 6 batched answers.

## Source type x intent -> template

| Source type | Intent | Template |
|---|---|---|
| zoom_podcast | vertical_clips + long_cut_polish | `zoom-podcast-multi.md` |
| walking_selfie | long_cut_polish + vertical_clips (chaptered) | `walking-video-topics.md` |
| zoom_lecture | educational_verticals | `zoom-lecture-verticals.md` |
| zoom_podcast (short) / walking_selfie (short) | vertical_clips (3 shorts) | `talking-head-shorts.md` |
| avatar_script | avatar_explainer | `avatar-explainer.md` |
| url | promo | `branded-promo-from-url.md` |
| screen_recording | tutorial_chaptered | `screen-recording-tutorial.md` |
| any (existing clip or avatar_script) | ad_variants | `ad-hook-variations.md` |
| `none` (no source footage) | vague brief / no shot list / no `video-style-*` match | `scene-plan-from-vague-brief.md` |

## When no template fits

If the source/intent combo is not in the table above (e.g. mixed multi-source, music-video, animation-only), skip the template and build the brief from scratch using `<skill_root>/brief-schema.json` as the source of truth. Ask the 6 batched questions per `SKILL.md` Step 3, then write the brief directly to `${VIDEO_JOBS_DIR}/<brief_id>/brief.json` with `template: null`.

## Tool selection rules of thumb

- Footage with a face talking -> CutSense default
- Long content with semantic chapter detection needed -> video-use
- No source footage at all (script only) -> HeyGen or Hedra
- Branded title cards / kinetic type / promo composition -> HyperFrames
- Website as input -> website-to-hyperframes skill
- Multiple variants (ads, A/B hooks) -> fork mode with parallel sub-agents
