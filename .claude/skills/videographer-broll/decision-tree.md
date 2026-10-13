# Decision Tree

Quick lookup. Map (source_type x intent) -> recommended template.
For details, open the template file in `templates/`.

## Lookup table

| source_type | intent | Default template | Default tool |
|---|---|---|---|
| zoom_podcast | vertical_clips | zoom-podcast-multi.md | cutsense |
| zoom_podcast | long_cut_polish | zoom-podcast-multi.md | cutsense |
| zoom_podcast | educational_verticals | zoom-lecture-verticals.md | cutsense |
| zoom_lecture | educational_verticals | zoom-lecture-verticals.md | cutsense |
| zoom_lecture | vertical_clips | zoom-lecture-verticals.md | cutsense |
| walking_selfie | long_cut_polish | walking-video-topics.md | cutsense (--enhance) |
| walking_selfie | vertical_clips | walking-video-topics.md | cutsense (--enhance) |
| walking_selfie | tutorial_chaptered | walking-video-topics.md | cutsense |
| screen_recording | tutorial_chaptered | screen-recording-tutorial.md | cutsense |
| screen_recording | educational_verticals | zoom-lecture-verticals.md | cutsense |
| url | promo | branded-promo-from-url.md | website-to-hyperframes |
| url | ad_variants | ad-hook-variations.md | hyperframes + cutsense |
| avatar_script | avatar_explainer | avatar-explainer.md | heygen |
| avatar_script | ad_variants | ad-hook-variations.md | heygen (3 variants) |
| any (short clip) | vertical_clips | talking-head-shorts.md | cutsense |
| any | ad_variants | ad-hook-variations.md | hyperframes + cutsense |

## When no row matches

Build the brief from scratch. Ask the user the 6 batched questions in `SKILL.md`. Pick the closest template as a starting point and override fields based on answers.

## Tool selection cheatsheet (when user picks "show me 3 options")

For ANY footage-based source (zoom, walking, screen recording):
1. **cutsense** - default, brand pill captions, fastest
2. **video-use** - smarter clip picking via LLM
3. **hyperframes** - manual per-clip, brand-perfect, slowest

For URL or "make a promo from this site":
1. **website-to-hyperframes** - capture and compose in one
2. **hyperframes manual** - more control
3. **cutsense + hyperframes hybrid** - cut a screen recording of the site, then frame it

For avatar/script (no footage):
1. **heygen** - avatar lipsync, premade or cloned
2. **hedra** - alternate lipsync, more emotive
3. **hyperframes + elevenlabs tts** - no avatar, kinetic typography over narration

For ad variants:
1. **hyperframes hooks + cutsense body** - 3 hook intros + shared body
2. **heygen (3 variants)** - 3 avatar variants reading 3 hooks
3. **cutsense (3 cut points)** - 3 different cuts from same source
