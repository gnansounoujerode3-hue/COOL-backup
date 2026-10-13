# COOL — Claude Code 3D, Motion-Design & B-Roll/Image Fetching Skills Registry

This repository contains **117 specialized Claude Code skills** under `.claude/skills/` for:
1. **Searching, downloading & inserting images and short B-roll videos (`3s–5s` MP4 clips) into edited videos** (`broll-media-fetcher`, `videographer-broll`, `assetseeker`, `stock-sourcing`, `video-download`, `video-resource-finder`, `montage-studio`, `05-image-sourcing`, `asset-source`, `pexels-media`, `licensed-media-finder`, `media-use`, `paper-cut-motion`, `remove-background`, `speaker-cutout`, `video-spotlight`, `scavenger`, `archivist`).
2. **High-end 3D video editing, WebGL/WebGPU/Three.js rendering, Remotion 3D compositing, 3D camera choreography, and broadcast motion design** (`threejs-*`, `remotion-best-practices`, `shotcraft-*`, `talkcraft-*`, `howseen-*`, `systo-*`, `MOTION-DESIGN.md`).

---

## 0. B-Roll Video & Image Downloading Skills (for Video Montage)

- **`.claude/skills/broll-media-fetcher/SKILL.md` + `scripts/fetch_broll_media.py`**
  - **End-to-End B-Roll & Image Pipeline for COOL**: Searches & downloads high-resolution images (`image_search` / Wikimedia / Openverse / Pexels / Pixabay), converts stills or source subclips into 30fps Ken-Burns / parallax short MP4 B-roll videos (`assets/broll/*.mp4`), generates `assets/broll-manifest.json`, and composites them into `9:16` edits as 3D Picture-in-Picture cards (`warp_plane_3d`), Dark HUD spotlight windows, and paper-cut editorial photo cards.
- **`.claude/skills/videographer-broll/` (`SKILL.md`, `adapters/broll-director.md`, `adapters/broll-retrieval.md`, `knowledge/broll-sources.md`, `adapters/cutsense.md`)**
  - **Directed B-Roll & Cutaway Engine**: Reads transcript timestamps and classifies every visual opportunity into 9 `broll_type` categories (`prop_cutaway`, `activity_broll`, `graphic_card`, `finished_product_broll`, `motion_graphic`, `second_angle`, `before_after_split`, `screen_recording`, `vfx_composite`) and 2 `placement_mode` layers (`full_replacement` vs `overlay`), then retrieves and cuts real B-roll clips onto the timeline.
- **`.claude/skills/assetseeker/` (`SKILL.md`, `scripts/seek_assets.py`, `references/asset_catalog.md`)**
  - **Multi-Source Creative Asset Downloader**: Searches and downloads royalty-free stock photos, short B-roll video footage, vector icons (Iconify), illustrations, SFX, and fonts from Pexels, Unsplash, Pixabay, Iconify, and Freesound.
- **`.claude/skills/stock-sourcing/SKILL.md` & `.claude/skills/video-download/SKILL.md`**
  - **Stock Video & Image Sourcing Adapter**: Query construction, aspect-ratio/duration filtering, and local corpus downloading for `pexels_video`, `pixabay_video`, `pexels_image`, `pixabay_image`, `direct_clip_search`, and `corpus_builder` (Pexels, Pixabay, Unsplash, Archive.org, Wikimedia, NASA, Mixkit, Coverr, Videvo).
- **`.claude/skills/video-resource-finder/SKILL.md` & `.claude/skills/local-asset-import/SKILL.md`**
  - **Scene-Driven Video Resource Finder**: Extracts visual queries per scene from script/timeline JSON, fetches matching B-roll videos and images, and imports selected clips into `imports/{videos,images,music,sfx}/`.
- **`.claude/skills/05-image-sourcing/SKILL.md`, `.claude/skills/04-scene-assembly/SKILL.md` & `.claude/skills/08-bank-builder/SKILL.md`**
  - **Story Video Studio Image & B-Roll Bank**: Curates per-scene image/video banks and assembles multi-layer visual sequences.
- **`.claude/skills/pexels-media/SKILL.md` & `.claude/skills/licensed-media-finder/SKILL.md`**
  - **Pexels CLI & Licensed Media Finder**: Bulk deduplicated photo/video B-roll downloading with license verification and attribution manifests.
- **`.claude/skills/montage-studio/SKILL.md`, `.claude/skills/paper-cut-motion/SKILL.md`, `.claude/skills/media-use/SKILL.md`, `.claude/skills/remove-background/SKILL.md`, `.claude/skills/speaker-cutout/SKILL.md` & `.claude/skills/video-spotlight/SKILL.md`**
  - **Montage & Visual Integration Skills**: Animating downloaded photos and short B-roll videos inside the edit via tactile paper-cut evidence boards (`paper-cut-motion`), isolated subject cutouts (`remove-background`, `speaker-cutout`), spotlight callouts (`video-spotlight`), and 3D title sequences (`title-sequence-3d`).
- **`.claude/skills/asset-source/SKILL.md`, `.claude/skills/scavenger/SKILL.md` & `.claude/skills/archivist/SKILL.md`**
  - **Archival & Documentary Media Scavenging**: Sourcing archival photos, diagrams, and documentary B-roll clips with verified provenance.

---

## 1. Core 3D Rendering & Shader Skills (Three.js / WebGL / WebGPU / PBR / Post-Processing)

- **`.claude/skills/threejs-skills/SKILL.md`** — Master orchestrator for 3D scene creation, PBR rendering, environment maps, and post-processing.
- **`.claude/skills/threejs-fundamentals/SKILL.md`** — PerspectiveCamera, Scene graph, WebGLRenderer, ACESFilmicToneMapping, and coordinate spaces.
- **`.claude/skills/threejs-geometry/SKILL.md`** — Procedural 3D meshes, BufferGeometry, InstancedMesh (particles/crowds), extrusion, and bevels.
- **`.claude/skills/threejs-materials/SKILL.md`** — Physically Based Rendering (`MeshStandardMaterial`, `MeshPhysicalMaterial`, clearcoat, transmission/glass, IOR, metalness/roughness).
- **`.claude/skills/threejs-lighting/SKILL.md`** — 3-point studio lighting, HDRI IBL, soft PCF/VSM shadow maps, and volumetric spotlights.
- **`.claude/skills/threejs-postprocessing/SKILL.md`** — `EffectComposer`, `UnrealBloomPass` (selective emissive bloom), `BokehPass` (3D Depth-of-Field), SSAO, chromatic aberration, film grain, and vignette.
- **`.claude/skills/threejs-shaders/SKILL.md`** — Custom GLSL vertex/fragment shaders, procedural noise (Simplex/Perlin/FBM), Fresnel rim lighting, and holographic HUD shaders.
- **`.claude/skills/threejs-animation/SKILL.md`** — Keyframe tracks, morph targets, skeletal rigs, spring damped physics, and camera path splines.
- **`.claude/skills/threejs-textures/SKILL.md`** — UV mapping, normal/roughness/displacement maps, anisotropic filtering, and video textures.
- **`.claude/skills/threejs-loaders/SKILL.md`** — GLTF/GLB, DRACO, KTX2, RGBELoader (HDR), and SVG-to-3D extrusion.
- **`.claude/skills/threejs-webgl-shaders/SKILL.md`** — Advanced custom WebGL shader pipelines and signed-distance-field (SDF) 3D rendering.
- **`.claude/skills/threejs-tsl-shaders/SKILL.md`** — Three.js Shading Language (TSL) node materials and WebGPU compute shaders.
- **`.claude/skills/r3f-best-practices/SKILL.md`** — React Three Fiber (`@react-three/fiber` + `@react-three/drei` + `@react-three/postprocessing`) declarative 3D scenes.

---

## 2. Remotion 3D & Programmatic Video Editing Skills

- **`.claude/skills/remotion-best-practices/SKILL.md`** + **`rules/3d.md`**
  - Integrating `@remotion/three` (`<ThreeCanvas>`) for frame-accurate, deterministic 3D video rendering (`useCurrentFrame()`, `interpolate()`, `spring()`).
  - Full ruleset in `.claude/skills/remotion-best-practices/rules/` covering `3d.md`, `animations.md`, `charts.md`, `ffmpeg.md`, `light-leaks.md`, `lottie.md`, `sfx.md`, `subtitles.md`, `text-animations.md`, ` timing.md`, `transitions.md`, and `transparent-videos.md`.
- **`.claude/skills/remotion-render/SKILL.md`** — High-bitrate MP4/ProRes rendering with multi-frame concurrency and WebGL angle backends.

---

## 3. 3D Camera Choreography & Cinematic Shotcraft (`shotcraft-*`)

- **`.claude/skills/shotcraft-3d-world/SKILL.md`** — Multi-plane 3D Z-space world building (`Z = -600` background to `Z = +200` foreground bokeh), parallax depth, and camera flights through 3D space.
- **`.claude/skills/shotcraft-camera-rig/SKILL.md`** — 6-DOF 3D camera rig (`pos_x, pos_y, pos_z`, `pitch, yaw, roll`, `fov`) with `hop` arcs, dolly-zooms, and Dutch angles.
- **`.claude/skills/shotcraft-lighting-color/SKILL.md`** — Cinematic color grading, teal-and-amber contrast, volumetric light cones, and specular highlights.
- **`.claude/skills/shotcraft-physics-motion/SKILL.md`** — Under-damped harmonic oscillators ($\zeta \in [0.68, 0.78]$), anticipation frames, and impact camera shake.
- **`.claude/skills/shotcraft-4k-mastering/SKILL.md`** — Anti-aliased supersampling, sub-pixel affine/projective warping, and mastering for 9:16 Reels/Shorts.

---

## 4. Voiceover-Driven 3D & Motion Editing (`talkcraft-*`, `howseen-*`, `systo-*`)

- **`.claude/skills/talkcraft-voiceover-sync/SKILL.md`** — Word-level timestamp synchronization (`Whisper` JSON) driving 3D camera cuts, kinetic typography, and visual callouts.
- **`.claude/skills/talkcraft-editorial-cutaways/SKILL.md`** — Full-canvas 3D/2.5D editorial cutaways (`dark HUD viewfinder`, `drafting paper blueprint`, `glassmorphic cards`).
- **`.claude/skills/howseen-motion-design/SKILL.md`** — Code-driven motion design principles.
- **`.claude/skills/systo-video-director/SKILL.md`** — Creative direction, visual variety rules, and retention pacing.
