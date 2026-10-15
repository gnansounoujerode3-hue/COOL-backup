# COOL — Master Claude Code Registry (206 Skills: Motion-Design Code Harvesting, 3D Rendering & B-Roll Fetching)

This repository contains **206 specialized Claude Code skills** under `.claude/skills/` organized into 5 pillars:
1. **Motion-Design Website Scraping & Animation Code Harvesting** (`motion-code-harvester`, `website-to-hyperframes`, `design-mirror`, `ux-extract`, `extract-design-system`, `extract-design-md`, `video-clone`, `cut-the-curve`, `seam-craft`, `motion-doctrine`, `embedded-captions`, `emil-design-eng`, `gsap-*`, `framer-motion`, `lottie-bodymovin`, `hyperframes-*`).
2. **B-Roll Video & Image Downloading for Video Montage** (`broll-media-fetcher`, `videographer-broll`, `assetseeker`, `stock-sourcing`, `video-download`, `video-resource-finder`, `montage-studio`, `05-image-sourcing`, `asset-source`, `pexels-media`, `licensed-media-finder`, `media-use`, `paper-cut-motion`, `remove-background`, `speaker-cutout`, `video-spotlight`, `scavenger`, `archivist`).
3. **High-End 3D Rendering & Shader Pipelines** (`threejs-*`, `threejs-webgl-shaders`, `threejs-tsl-shaders`, `r3f-best-practices`, `blender-product-film`).
4. **Remotion 3D & Programmatic Video Editing** (`remotion-best-practices`, `remotion-render`, `remotion-to-hyperframes`).
5. **3D Camera Choreography & Voiceover-Driven Motion Direction** (`shotcraft-*`, `talkcraft-*`, `howseen-*`, `systo-*`, `MOTION-DESIGN.md`).

---

## 0A. Motion-Design Site Scraping & Animation Code Harvesting Skills

- **`.claude/skills/motion-code-harvester/SKILL.md` + `scripts/motion_engine.py`**
  - **Executable Python Animation Engine for COOL**: Implements the mathematical & optical formulas harvested from top motion-design sites (`animations.dev`, Codrops, Awwwards, GSAP Showcase, HyperFrames):
    - `zoom_through_seam` & `inverse_zoom_seam` (`cut-the-curve` §1–2: `power3.in` 30% exit + `14px` peak optical blur swap + `expo.out` 70% entry)
    - `cut_the_curve_seam` (`cut-the-curve` §3: `±12%` partial-travel velocity-matched `power4.in` / `power4.out` seam)
    - `rack_focus_blur_cut` (`cut-the-curve` §5: DSLR focus-pull `scale 1→1.06→1` + `13px` defocus spike)
    - `waterfall_word_state` (`cut-the-curve` §6: shrinking inter-word gaps `gap × 0.84^i` + weight-scaled travel `72px / 46px / 32px` on `expo.out`)
    - `nudge_curve_3phase` (`cut-the-curve` §7: `10% / 65% / 25%` distance over `20% / 18% / 62%` time — `power3.in` → `linear` burst → `power4.out` tail)
    - `swipe_clip_reveal` (`embedded-captions` §4: `clip-path: inset(0 100% 0 0 → 0 0 0 0)` on `expo.inOut` `cubic-bezier(0.77, 0, 0.175, 1)`)
    - `subject_occluded_embed` (`embedded-captions` Vogue-cover depth occlusion behind the speaker cutout)
- **`.claude/skills/website-to-hyperframes/SKILL.md`, `.claude/skills/design-mirror/SKILL.md`, `.claude/skills/ux-extract/SKILL.md`, `.claude/skills/extract-design-system/SKILL.md` & `.claude/skills/extract-design-md/SKILL.md`**
  - **Live Website & Motion-Design Code Scrapers**: Capture live websites and motion-design showcases, extract CSS/JS/GSAP/Framer Motion keyframes, easing curves, typography tokens, and layout structures, and convert them into video compositions.
- **`.claude/skills/cut-the-curve/SKILL.md` + `examples/gsap-implementation.md`, `.claude/skills/seam-craft/SKILL.md` & `.claude/skills/motion-doctrine/SKILL.md`**
  - **Velocity-Matched Transitions & GSAP Code Templates**: Complete GSAP source code and mathematical rules for Zoom-Through, Inverse Zoom-Through, Cut-the-Curve, Waterfall Cut, Rack-Focus Blur-Cut, Waterfall Entry, and the 3-Phase Nudge Curve.
- **`.claude/skills/embedded-captions/SKILL.md` + `CATALOG.md` + `references/motion-vocabulary.md` + `references/typographic-moves.md`**
  - **35 Named Motion Caption Identities & 10 Word-Entry Moves**: Full CSS/GSAP code for `typewriter`, `word-fade-up`, `word-pop`, `swipe-reveal`, `drop-and-settle`, `etch`, and subject-occluded Vogue-cover depth embeds.
- **`.claude/skills/emil-design-eng/SKILL.md` (`animations.dev`)**
  - **Emil Kowalski's Design Engineering Philosophy**: Custom `ease-out` curves, `scale(0.95)` floor rule, and compound micro-interactions.
- **`.claude/skills/gsap-core/`, `gsap-timeline/`, `gsap-scrolltrigger/`, `gsap-plugins/`, `gsap-utils/`, `gsap-react/`, `gsap-frameworks/`, `gsap-performance/`**
  - **Complete GSAP Animation Code Suite**: Timelines, SplitText, MorphSVG, Flip, ScrollTrigger, CustomEase, and MotionPath.
- **`.claude/skills/framer-motion/`, `lottie-bodymovin/`, `text-to-lottie/`, `canvas-procedural-animation/`, `css-animation-skill/`, `animate-css-skill/`, `d3-viz/`, `manim-composer/`**
  - **Web & Procedural Animation Engines**: Framer Motion spring physics, Lottie JSON generation, HTML5 Canvas procedural shaders, D3 data-viz motion, and Manim mathematical animations.
- **`.claude/skills/video-clone/SKILL.md`, `talking-head-recut/SKILL.md`, `reference-grade-product-film/SKILL.md`, `animation-vocabulary/SKILL.md`, `find-animation-opportunities/SKILL.md`, `improve-animations/SKILL.md`, `review-animations/SKILL.md`**
  - **Reference Motion Cloning & QA Suite**: Reverse-engineering reference reels and auditing frame-by-frame motion curves.

---

## 0B. B-Roll Video & Image Downloading Skills (for Video Montage)

- **`.claude/skills/broll-media-fetcher/SKILL.md` + `scripts/fetch_broll_media.py`**
  - **End-to-End B-Roll & Image Pipeline for COOL**: Searches & downloads high-resolution images (`image_search` / Wikimedia / Openverse / Pexels / Pixabay), converts stills or source subclips into 30fps Ken-Burns / parallax short MP4 B-roll videos (`assets/broll/*.mp4`), generates `assets/broll-manifest.json`, and composites them into `9:16` edits.
- **`.claude/skills/videographer-broll/` (`SKILL.md`, `adapters/broll-director.md`, `adapters/broll-retrieval.md`, `knowledge/broll-sources.md`, `adapters/cutsense.md`)**
  - **Directed B-Roll & Cutaway Engine**: Classifies transcript opportunities into 9 `broll_type` categories and 2 `placement_mode` layers (`full_replacement` vs `overlay`), then retrieves and cuts real B-roll clips onto the timeline.
- **`.claude/skills/assetseeker/` (`SKILL.md`, `scripts/seek_assets.py`, `references/asset_catalog.md`)**
  - **Multi-Source Creative Asset Downloader**: Searches and downloads royalty-free stock photos, short B-roll video footage, vector icons (Iconify), illustrations, SFX, and fonts.
- **`.claude/skills/stock-sourcing/SKILL.md`, `.claude/skills/video-download/SKILL.md`, `.claude/skills/video-resource-finder/SKILL.md`, `.claude/skills/local-asset-import/SKILL.md`, `.claude/skills/pexels-media/SKILL.md`, `.claude/skills/licensed-media-finder/SKILL.md`**
- **`.claude/skills/montage-studio/SKILL.md`, `.claude/skills/paper-cut-motion/SKILL.md`, `.claude/skills/media-use/SKILL.md`, `.claude/skills/remove-background/SKILL.md`, `.claude/skills/speaker-cutout/SKILL.md`, `.claude/skills/video-spotlight/SKILL.md`**

---

## 1. Core 3D Rendering & Shader Skills (Three.js / WebGL / WebGPU / PBR / Post-Processing)

- **`.claude/skills/threejs-skills/SKILL.md`**, **`threejs-fundamentals`**, **`threejs-geometry`**, **`threejs-materials`**, **`threejs-lighting`**, **`threejs-postprocessing`**, **`threejs-shaders`**, **`threejs-animation`**, **`threejs-textures`**, **`threejs-loaders`**, **`threejs-webgl-shaders`**, **`threejs-tsl-shaders`**, **`r3f-best-practices`**, **`blender-product-film`**.

---

## 2. Remotion 3D & Programmatic Video Editing Skills

- **`.claude/skills/remotion-best-practices/SKILL.md`** + **`rules/3d.md`**, **`.claude/skills/remotion-render/SKILL.md`**, **`.claude/skills/remotion-to-hyperframes/SKILL.md`**.

---

## 3. 3D Camera Choreography & Voiceover-Driven Motion (`shotcraft-*`, `talkcraft-*`, `howseen-*`, `systo-*`)

- **`.claude/skills/shotcraft-3d-world/SKILL.md`**, **`shotcraft-camera-rig`**, **`shotcraft-lighting-color`**, **`shotcraft-physics-motion`**, **`shotcraft-4k-mastering`**, **`talkcraft-voiceover-sync`**, **`talkcraft-editorial-cutaways`**, **`howseen-motion-design`**, **`systo-video-director`**.
