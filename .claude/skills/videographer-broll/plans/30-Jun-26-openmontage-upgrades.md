# Videographer (video-orchestrator) upgrades, learned from OpenMontage

**Date:** 2026-06-30
**Goal:** Close the genuine gaps between our `videographer-skill` (video-orchestrator, `~/.claude/skills/video-orchestrator/`) and OpenMontage, without adopting OpenMontage wholesale or duplicating what we already have (CutSense, HyperFrames, fal-seedance, the router).
**Interactive picker:** http://localhost:47800/drop/videographer-openmontage-upgrades.html

---

## What OpenMontage is (deep dive)

Open-source (MIT) "agentic video production system." The coding assistant IS the orchestrator. Production is made legible to the agent as files: YAML pipeline manifests, Markdown director skills, JSON checkpoints, stable-named asset folders.

- **12 pipelines**, each `research -> proposal -> script -> scene_plan -> assets -> edit -> compose`.
- **52 tools**: ~14 video-gen (Kling, Runway Gen-4, Veo3, Grok, Higgsfield, MiniMax, HeyGen, local WAN/Hunyuan/CogVideo/LTX, + stock), ~10 image-gen (FLUX, Imagen, DALL-E, Recraft, SD, ManimCE, stock), 4 TTS (ElevenLabs, Google, OpenAI, Piper-local), music/SFX (Suno, ElevenLabs), FFmpeg post, enhancement (Real-ESRGAN upscale, face restore, bg remove), analysis (WhisperX, scene detect, CLIP/BLIP-2).
- **Composition engines: Remotion + HyperFrames** (it adopted our HyperFrames engine - shared DNA).
- **Scored provider router** across 7 dimensions (task fit 30 / quality 20 / control 15 / reliability 15 / cost 10 / latency 5 / continuity 5) with a logged decision audit trail.
- **Budget governance**: estimate -> reserve -> reconcile, per-action approval ($0.50 default), total cap ($10 default), modes observe/warn/cap.
- **Slideshow-risk scoring** (6 dims) + pre-compose validation gates that BLOCK a render before spend.
- **Retrieval-first B-roll**: CLIP-searchable corpus from Archive.org / NASA / Wikimedia / Pexels / Unsplash, cut into a real timeline.
- **Zero-API-key floor**: Piper TTS + free archive footage + Remotion/HyperFrames + FFmpeg.
- **Provenance caveat**: multiple near-identical repos + SourceForge installer mirrors (.7z/.run/.dmg). Clone the source, never run an installer.

## What our videographer is (deep dive)

Router skill (Opus), `/edit-video`. Asks 6 batched questions -> surfaces 2-3 tool options -> builds a universal `brief.json` -> dispatches one tool OR forks to N parallel sub-agents -> QA -> COMPARE.md.

- **Adapters:** CutSense, HyperFrames, video-use, HeyGen, Hedra, Remotion, fal-seedance (Seedance 2.0), Veo3, Lottie.
- **Engines' strengths:** CutSense = video *understanding* (VUD: transcript/vision/entities/energy/key-moments) -> programmatic Remotion edit. HyperFrames = HTML/CSS/GSAP comps.
- **QA gates (POST-render):** face-safety (mediapipe), loudness (pyloudnorm), timing (ffprobe). PASS/WARN/FAIL + auto-retry.
- **Discipline:** multi-clip Lock Block (consistency across stateless gen clips), brand packs, voice+avatar cloning briefs, fork-to-3 compare.
- **Adjacent (same stack):** in-Premiere Testimonial Cutter (real NLE integration OpenMontage lacks).

## Gap map (what they have that we don't)

| # | OpenMontage capability | Our state | Plan item |
|---|---|---|---|
| 1 | Retrieval-first B-roll from free archives + CLIP corpus | None (only user footage or fresh gen) | **A1** |
| 2 | Pre-compose slideshow-risk gate (blocks before spend) | Only post-render technical QA | **A2** |
| 3 | Budget estimate/reserve/cap governance | No cost estimate or cap | **A3** |
| 4 | Full research->script->sceneplan->assets pipeline | Router + 8 scenario templates; starts at "have source / one clip" | **B1** |
| 5 | Scored 7-dim provider selection + decision audit log | Human picks from 2-3 surfaced options, no log | **B2** |
| 6 | Checkpoint / resumable production state | brief.json + QA.json, no checkpoint/decision log | **B3** |
| 7 | Music/SFX generation | None | **C1** |
| 8 | Enhancement (upscale / face-restore / bg-remove) | None | **C2** |
| 9 | Scene image-gen wired into the pipeline | kolbo client exists but not wired | **C3** |
| 10 | Platform render profiles (YT/Shorts/Reels/TikTok/LI/21:9) | Per-template verticals, no formal profiles | **C4** |
| 11 | Layer-3 per-provider knowledge packs | Adapters mix capability + know-how | **C5** |

## The plan (tiered)

### Tier 1 - biggest gaps, lowest overlap (recommended: all 3)
- **A1. B-roll retrieval engine.** New `adapters/broll-retrieval.md` + a corpus builder: pull free stock/archive (Archive.org, Wikimedia, NASA, Pexels, Pixabay, Unsplash), CLIP-embed, search by transcript/scene intent, cut clips onto the timeline. Slots between CutSense understand->edit; also exports cutaways for the in-Premiere Testimonial Cutter. Free-first; CLIP runs local/VPS.
- **A2. Pre-compose slideshow-risk gate.** New `qa/slideshow-risk.py` scoring 6 dims (repetition, decorative visuals, weak motion, shot intent, typography overreliance, unsupported cinematic claims). Runs on the scene_plan BEFORE render; WARN/FAIL blocks the spend. Complements the post-render gates.
- **A3. Budget governance.** Add `brief.budget {cap, per_action_approval, mode}` + `qa/budget.py`: estimate per metered adapter (fal-seedance/HeyGen/Hedra/Veo3) -> reserve -> ask above threshold -> reconcile actuals into the job. Default mode = free-first (prefer $0 paths). Directly enforces SUBSCRIPTION-FIRST.

### Tier 2 - formalize what we half-have
- **B1. Full production pipeline.** Extend `scene-plan-from-vague-brief.md` into a staged manifest (`research -> proposal -> script -> scene_plan -> assets -> edit -> compose`) for "make a whole video from a topic" (explainer / documentary montage / cinematic). Each stage is a reviewable file.
- **B2. Scored provider selection + decision log.** Put a transparent weighted scorer behind the "surface 2-3 options" UX; write `decisions.json` (chosen, alternatives, confidence, est. cost). Human still approves. Serves Radical Transparency.
- **B3. Checkpoint / resumable state.** `checkpoint.json` per stage so long jobs resume and are inspectable.

### Tier 3 - expand the toolbox
- **C1. Music + SFX adapter** (ElevenLabs Music/SFX, Suno) - score bed + stingers.
- **C2. Enhancement adapters** (Real-ESRGAN upscale, face-restore, bg-remove) - polish pass.
- **C3. Wire kolbo image-gen** as a scene-asset provider (reuse the existing client - cheap win).
- **C4. Platform render-profile system** - aspect/profile presets as a brief field, applied at compose.
- **C5. Layer-3 knowledge packs** - per-provider deep-usage docs so adapters stay thin.

### Explicitly NOT doing
- No wholesale OpenMontage adoption (overlaps our router + CutSense + HyperFrames).
- No local GPU video models (WAN/Hunyuan/CogVideo/LTX) - VRAM/ops weight not worth it now.
- No SourceForge installers - source clone + provenance check only.

## Recommended starter set
**A1 + A2 + A3 + B2 + C3** - the high-value / low-effort cluster. A1 is the standout (it also upgrades the Testimonial Cutter); A2+A3 add creative + cost discipline; B2 adds transparency; C3 reuses code we already own.

## Verification
Each item ships with: an adapter/gate file, a brief-schema enum addition, a SKILL.md table row, and a smoke test on one real source. Tier-1 items get a before/after on a real job in `VideoJobs/`. No metered API calls during dev beyond a single smoke render per adapter.

## Open questions
- B-roll: which free sources first (Archive.org + Wikimedia are fully free; Pexels/Pixabay/Unsplash need free keys)?
- Slideshow-risk: block on FAIL (hard gate) or warn-and-confirm (soft gate) by default?
- Budget: default cap value, and should free-first be the global default mode?
