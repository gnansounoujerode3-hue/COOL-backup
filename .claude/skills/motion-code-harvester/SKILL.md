---
name: motion-code-harvester
description: Search, extract, and compile the best animation curves, GSAP/Framer/CSS/Shadertoy motion code, velocity-matched transitions (Cut-the-Curve, Zoom-Through, Inverse Zoom-Through, Rack-Focus Blur-Cut, Waterfall Entry, 3-Phase Nudge Curve), and Subject-Occluded Embedded Captions from top motion-design sites (animations.dev, Codrops, Awwwards, GSAP Showcase, HyperFrames) and apply them directly to COOL video edits.
---

# Motion Code Harvester & Animation Engine (`motion-code-harvester`)

## Overview

This skill bridges **web motion-design showcase sites** (Awwwards, Codrops, `animations.dev`, GSAP Showcase, Motion.dev, Shadertoy, HyperFrames) and **programmatic video editing (`felix-gray-reference6..10`)**:
1. **Extracts & Catalogs Production Motion Code** via companion skills:
   - `website-to-hyperframes` & `design-mirror` & `ux-extract` & `extract-design-system` (live site animation & token extraction)
   - `cut-the-curve` (`examples/gsap-implementation.md` — 5 velocity-matched seams + Waterfall Entry + 3-Phase Nudge Curve)
   - `embedded-captions` (`CATALOG.md`, `references/motion-vocabulary.md`, `references/typographic-moves.md` — 35 caption identities + 10 word-entry moves + subject-occluded depth embeds)
   - `emil-design-eng` (`animations.dev` — Emil Kowalski's unseen-details & easing engineering)
   - `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`, `framer-motion`, `lottie-bodymovin`, `canvas-procedural-animation`
2. **Provides a Zero-Dependency Python/PIL/NumPy Animation Engine (`scripts/motion_engine.py`)** that translates GSAP / CSS / WebGL motion primitives into frame-accurate (`30 fps` / `60 fps`, `1080×1920`) video compositing functions.

---

## Core Harvested Motion Primitives (`scripts/motion_engine.py`)

| Primitive | Source Skill / Site | Mathematical / Optical Formula | Video Montage Use Case |
|---|---|---|---|
| **`zoom_through_seam`** | `cut-the-curve` §1 (GSAP `power3.in` → `expo.out`) | Outgoing `scale: 1.0 → 1.20`, `blur: 0 → 12px`, `opacity: 1 → 0.15` (30% dur); Cut at peak blur; Incoming `scale: 0.78 → 1.0`, `blur: 12 → 0px`, `opacity: 0.15 → 1.0` (`expo.out`, 70% dur) | Pushing forward into a full-screen B-roll or cutaway scene |
| **`inverse_zoom_seam`** | `cut-the-curve` §2 (GSAP `power3.in` → `expo.out`) | Outgoing recedes `scale: 1.0 → 0.82`, `blur: 0 → 12px`; Incoming arrives oversized `scale: 1.24 → 1.0`, `blur: 12 → 0px` (`expo.out`) | Payoff / arrival beats returning from cutaway to talking head |
| **`cut_the_curve_seam`** | `cut-the-curve` §3 (`power4.in` + `power4.out`) | Partial travel `±12%` of frame (`±130px` X or `±230px` Y), mirrored halves of `power4.inOut` so velocity matches at the cut + directional motion blur | Scene-to-scene boundaries riding a single directional current |
| **`rack_focus_blur_cut`** | `cut-the-curve` §5 (`power2.in` + `power2.out`) | Optical DSLR focus pull: `scale: 1.0 → 1.05 → 1.0`, defocus `blur: 0 → 14px → 0`, hard swap at peak blur (`p = 0.5`) | State swaps within the same visual theme |
| **`waterfall_word_entry`** | `cut-the-curve` §6 (`power4.out` + `×0.84` gap decay) | Staggered arrival cascade where inter-word gaps shrink (`gap_i = gap_0 * 0.84^i`) and travel scales by word weight (`72px` anchor, `46px` normal, `32px` light) | Multi-word kinetic typography & title openers |
| **`nudge_curve_3phase`** | `cut-the-curve` §7 (`power3.in` → `linear` → `power4.out`) | 3-phase group slide: `10%` dist in `20%` time (`power3.in`) → `65%` dist in `18%` time (`linear` burst) → `25%` dist in `62%` time (`power4.out` creep) | Sliding a composed text/card group to make room for a new line |
| **`swipe_clip_reveal`** | `embedded-captions` §4 (`cubic-bezier(.77,0,.175,1)`) | High-contrast `clip-path: inset(0 100% 0 0 → 0 0 0 0)` with `expo.inOut` velocity peak | Calligraphic script overlays, highlight bars, and lower-thirds |
| **`subject_occluded_embed`** | `embedded-captions` (`Vogue-cover matte`) | Places oversized display typography (`18–28%` frame height) **behind** the foreground speaker cutout mask (`fg_mask`) and in front of the background wall | Apex hero words & halftone backdrops behind the speaker's shoulders |

---

## Usage in Video Montage Scripts

```python
import sys
sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
from motion_engine import (
    expo_out, power3_in, power4_in, power4_out,
    nudge_curve_3phase, waterfall_word_offset,
    swipe_clip_reveal, zoom_through_seam, inverse_zoom_seam,
    cut_the_curve_seam, rack_focus_blur_cut,
)
```
