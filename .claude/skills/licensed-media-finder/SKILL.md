---
name: content-asset-licensed-media-finder
description: Search, review, cache, select, and download licensed video, image, audio, and GIF assets across public providers such as Pexels, Pixabay, Coverr, Freesound, Unsplash, Openverse, Wikimedia Commons, and GIPHY. Use when Codex is asked to find footage, B-roll, tutorial visuals, photos, sound effects, ambience, GIFs, stickers, or reusable media for a video production.
---

# Licensed Media Finder

Use the bundled CLI instead of writing provider requests manually. Keep optional API keys in `~/.config/content-studio/media-assets.env`; process environment values override that file. Never copy credentials into manifests, HTML, logs, output JSON, or chat.

## Workflow

1. Translate the requested scene into one concise English search query. Preserve named entities.
2. Choose relevant media types: `video`, `image`, `audio`, `gif`.
3. Run the search from the target project root:

```bash
<plugin-root>/bin/content-studio run \
  --output-dir ./outputs/content-studio/content-asset-licensed-media-finder \
  content-asset-licensed-media-finder search-assets.mjs -- \
  --query "developer using an AI coding assistant" \
  --types video,image,audio,gif \
  --orientation portrait \
  --limit 6 \
  --output productions/<id>/research-assets
```

4. Open `<output>/index.html` through a localhost static server and let the user review candidates.
5. Download only explicitly selected assets:

```bash
<plugin-root>/bin/content-studio run \
  content-asset-licensed-media-finder select-assets.mjs -- \
  --manifest productions/<id>/research-assets/asset-manifest.json \
  --ids pexels:4974882,pixabay:10822
```

6. Keep `asset-manifest.json` with the production. Treat it as the attribution and license audit record.

## License Rules

- Download originals automatically only when `eligibility` is `usable` or `conditional`.
- Preserve attribution text for every `conditional` asset.
- Never download originals marked `preview_only` without a new explicit license decision.
- Treat unknown, noncommercial, editorial-only, GIPHY, and unlicensed paid assets as `preview_only`.
- Trigger Unsplash's download tracking endpoint before downloading a selected image.
- Use Freesound originals only with `FREESOUND_OAUTH_TOKEN`; otherwise retain the preview.

## Provider Selection

- B-roll video: Pexels, Pixabay, Coverr.
- Photos and backgrounds: Pexels, Pixabay, Unsplash, Openverse, Wikimedia Commons.
- Historical/scientific media: Wikimedia Commons, Openverse.
- Sound effects and ambience: Freesound, Openverse.
- Reactions/stickers: GIPHY, preview-only.
- Paid catalogs: Adobe Stock and Shutterstock are configuration placeholders; search/licensing is not automated.

Read [references/providers.md](references/providers.md) when adding credentials or changing provider behavior. Read [references/manifest-schema.md](references/manifest-schema.md) when consuming the manifest from another tool.

## Verification

Before delivery, confirm each selected file exists, its manifest entry retains the original source and license, and any required attribution is present in the production.
