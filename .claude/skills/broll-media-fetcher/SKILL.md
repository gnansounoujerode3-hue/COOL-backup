---
name: broll-media-fetcher
description: Search, download, and prepare images and short B-roll video clips (MP4) to insert into edited videos (Picture-in-Picture 3D cards, full-screen B-roll cutaways, and paper-cut photo evidence cards). Integrates Arena image_search, Wikimedia Commons, Openverse, Pexels, and Pixabay with automatic FFmpeg 30fps Ken-Burns clip generation and broll-manifest.json creation.
---

# B-Roll & Image Media Fetcher for Video Montage (`broll-media-fetcher`)

## Purpose

When editing a talking-head or documentary video (`9:16` vertical or `16:9` horizontal), this skill searches and downloads **real images** and **short B-roll videos (`3s–5s` MP4 clips)** and inserts them directly into the video timeline as:
1. **3D Floating Picture-in-Picture (PiP) B-Roll Video Cards (`placement_mode: "overlay"`)** — Tilted in 3D perspective (`warp_plane_3d`) with frosted glass borders, ambient occlusion drop shadows, and live HUD corner tags (`SITE B-ROLL // 01`, `STUDIO B-ROLL // 02`).
2. **Dark HUD / Spotlight B-Roll Windows (`broll_type: "activity_broll"`)** — Embedded inside dark atmospheric cutaway scenes with dual spotlight cones and cinema color grading.
3. **Paper-Cut Editorial Photo Evidence Cards (`broll_type: "graphic_card"`)** — Layered onto cream drafting-paper cutaway scenes (`#EBE7DF`) with physical paper borders, corner tape, and directional drop shadows (`paper-cut-motion` protocol).
4. **Full-Screen Cutaways (`placement_mode: "full_replacement"`)** — Color-matched 30fps MP4 B-roll clips replacing the talking-head A-roll on concrete transcript nouns.

---

## Workflow

### Step 1: Identify Transcript Nouns & Visual Beats (`broll-director`)
Read the transcript with word-level timestamps and classify visual opportunities using `.claude/skills/videographer-broll/adapters/broll-director.md`:
- `prop_cutaway` — Concrete objects/tools named by the speaker (e.g., architectural blueprints, CAD floor plans).
- `activity_broll` — Actions/places named by the speaker (e.g., building construction sites, scaffolding, helpers on site).
- `graphic_card` — Conceptual/editorial terms (e.g., 3D architectural scale model on drafting paper).
- `finished_product_broll` — Studio/process shots (e.g., reviewing floor plans at the studio table).

### Step 2: Download Images & Short B-Roll Videos
1. **In Arena Agent Mode**: Call `image_search` with concrete noun phrases (e.g., `"architectural blueprint floor plan drafting table"`, `"building construction site scaffolding workers"`, `"architectural 3d scale model modern building"`).
2. **Via CLI Script (`scripts/fetch_broll_media.py`)**: Normalizes downloaded images into `assets/images/*.jpg`, generates 30fps Ken-Burns / parallax short MP4 B-roll videos in `assets/broll/*.mp4`, extracts any real B-roll segments from source footage, and writes `assets/broll-manifest.json`.

```bash
python3 .claude/skills/broll-media-fetcher/scripts/fetch_broll_media.py \
  --project-dir felix-gray-reference9 \
  --source-video "video brut 9.mp4"
```

### Step 3: Composite Downloaded Images & Short Videos into the Edit
Load `assets/broll/*.mp4` and `assets/images/*.jpg` inside `scripts/render_video.py` and project each B-roll video frame or photo card through `warp_plane_3d()` with spring-physics entry/exit (`spring_1d(dt, zeta=0.74, omega0=17.0)`) and ambient contact shadows.
