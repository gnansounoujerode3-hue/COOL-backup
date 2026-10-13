# Claude Code — 3D & Motion Design Skills Registry (`COOL-backup`)

Ce dépôt intègre **79 skills Claude Code** dédiés au montage vidéo, au motion design 2.5D/3D, à Three.js (WebGL / WebGPU / TSL / React Three Fiber), à Remotion 3D et à la direction artistique.

## 1. Architecture & Méthodologie Maîtresse
- **`MOTION-DESIGN.md`** (racine) : Méthodologie de motion design COOL (`--motion-ease-out: cubic-bezier(.2, .8, .2, 1)`, `[data-reveal]` `translateY(14px) -> 0`, une animation principale par écran, repères de rythme `100–180 ms` active, `150–220 ms` hover/focus, `220–400 ms` transition d'état, `400–650 ms` entrée de section, `500–900 ms` séquence narrative, `40–80 ms` stagger).
- **`.claude/skills/motion-graphics-director/SKILL.md`** : Pipeline de direction en 5 portes (Concept $\rightarrow$ Shot list $\rightarrow$ Style frames $\rightarrow$ Animatic $\rightarrow$ Critique).
- **`.claude/skills/motion-design/SKILL.md`** (*Howseen pipeline*) : Moteur déterministe `seek(t)`, interpolation de zoom caméra en espace logarithmique, micro-drift continu (`+1,5 %`, aucune image figée), flou de mouvement temporel (`180°` shutter).
- **`.claude/skills/hyperframes-render-discipline/SKILL.md`** : Discipline de rendu, vérification `ffprobe`, source unique de durée et contrôle de contraste sur fond réel.

## 2. Skills Vidéo 3D & Motion Design (`Remotion` / `Shotcraft` / `Talkcraft`)
- **`.claude/skills/remotion-markup/3d.md`** & **`.claude/skills/remotion-best-practices/SKILL.md`** : Intégration `@remotion/three`, `<ThreeCanvas>`, animations pilotées par frame, light leaks, motion blur, transitions, sous-titres et SFX.
- **`.claude/skills/video-shotcraft/SKILL.md`** & **`recipes/basic-3d-scene.md`** :
  - **Caméra spatiale 3D** : `camera = stepTransform.inverse()` avec poses 3D `(x, y, z, rx, ry, rz, s)`, perspective `2600px`, rebond de survol spatial (`hop 30%` en `sin(π·p)`) entre les stations, `70` particules 3D en coordonnées monde avec profondeur de champ (`opacity 0.22–1.0`, `blur 0–7px`) et dérive lente `1,5 %` pendant les lectures.
- **`.claude/skills/video-talkcraft/SKILL.md`** : Synchronisation mot à mot, système caméra anti-slideshow à 7 couches et transitions par continuité de mouvement.

## 3. Skills Rendu 3D Physique, Caméra, Éclairage & Post-Processing (`Three.js` / `WebGPU` / `R3F`)
- **Caméra & Parallaxe 3D** :
  - `.claude/skills/threejs-camera-controls-and-rigs/SKILL.md`
  - `.claude/skills/threejs-parallax/README.md`
  - `.claude/skills/threejs-scroll-sites/SKILL.md`
- **Éclairage PBR, Ombres de Contact (GTAO) & Matériaux** :
  - `.claude/skills/threejs-lighting/SKILL.md`
  - `.claude/skills/threejs-ambient-contact-shading/SKILL.md`
  - `.claude/skills/threejs-scalable-real-time-shadows/SKILL.md`
  - `.claude/skills/threejs-materials/SKILL.md`
  - `.claude/skills/threejs-procedural-materials/SKILL.md`
- **Post-Processing, Bloom HDR & Color Grading** :
  - `.claude/skills/threejs-postprocessing/SKILL.md`
  - `.claude/skills/threejs-bloom/SKILL.md`
  - `.claude/skills/threejs-exposure-color-grading/SKILL.md`
  - `.claude/skills/threejs-image-pipeline/SKILL.md`
- **Géométrie Procédurale, Architecture 3D & Particules** :
  - `.claude/skills/threejs-procedural-buildings-and-cities/SKILL.md`
  - `.claude/skills/threejs-procedural-geometry/SKILL.md`
  - `.claude/skills/threejs-object-sculptor/SKILL.md`
  - `.claude/skills/threejs-particles-trails-and-effects/SKILL.md`
  - `.claude/skills/threejs-shaders/SKILL.md`
  - `.claude/skills/threejs-r3f/SKILL.md`
  - `.claude/skills/threejs-webgpu/SKILL.md`
