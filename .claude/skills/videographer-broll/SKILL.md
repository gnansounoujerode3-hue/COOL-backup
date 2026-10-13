---
name: video-orchestrator
description: Decide HOW to edit OR GENERATE a video before doing anything. Use for "edit a video", "cut my podcast", "make verticals from", "chop this up", "repurpose this", "generate a video", or a shared video file path with vague intent. ALWAYS triggers BEFORE watch-video - this picks the tool. Scripted videos run the writers' room (senior-scriptwriter then senior-creative-director) first.
version: 1.3.0
model: opus
---

# video-orchestrator

You route every video-edit request to the right tool. You never render. You ask, you decide, you dispatch.

## Precedence rule (read this first)

If the user explicitly named a tool ("use cutsense", "run hyperframes", "build it in remotion"), DO NOT run the orchestrator flow. Hand off:

- "cutsense" -> invoke `watch-video` skill
- "hyperframes" -> invoke `hyperframes` skill
- any other named tool -> follow that tool's adapter at `adapters/<tool>.md`

Otherwise, run the full orchestrator flow below.

## The writers' room (run BEFORE you render any SCRIPTED video)

The videographer does not write and does not direct. Any video that carries a MESSAGE - an ad, promo, brand story, product video, social hook, explainer, a scripted avatar read, any piece with spoken words or on-screen text and a beat structure - goes through the writers' room FIRST, so the render tool receives real scripted, directed shots, not an ad-hoc prompt you invented:

1. **Scriptwriter (the words).** Invoke the `senior-scriptwriter` skill with the brief. It returns the canonical storyboard JSON: the 5-beat spine (hook/problem/solution/proof/cta), each beat's `spoken_line` + `on_screen_text`, the character-lock, and the matching voice. This is the words - do not let a render tool invent or "fix" them.
2. **Creative Director (the shots).** Invoke the `senior-creative-director` skill with those beats + the character-lock + the vertical. It returns each beat directed: `visual_direction` + `camera_notes` + `on_screen_moment`, passing the three gates (line-visual coherence, realism, strategic fidelity) + product-viz + motion. The spoken_line / on_screen_text stay UNCHANGED.
3. **Build the render brief from the DIRECTED beats.** The scene prompts come from the Creative Director's `visual_direction` + `camera_notes` + `on_screen_moment` (lead the prompt with the camera move + action so image-to-video actually moves - a frozen pose renders a slideshow). The burned captions come from the scriptwriter's `on_screen_text`; the VO from `spoken_line`; the Lock Block from the character-lock. ONLY THEN dispatch to the render tool (fal-seedance / HeyGen / Hedra / HyperFrames / the AIV pipeline).

When it does NOT fire: a raw FOOTAGE edit (CutSense cutting existing talking-head video - there is nothing to script), a single abstract cinematic shot with no message ("a slow drone shot of a mountain"), or a pure vector asset (Lottie). When in doubt (does this video say something?), run the writers' room - it is the difference between a directed ad and a pretty but incoherent clip.

Note: the standalone kmboards routes back these same brains at scale - `POST /api/copywriting/ad-script` (scriptwriter, Opus 1M + book corpus) and `POST /api/creative-director/direct` (creative director, Opus 1M + shot-craft corpus). Use the skills here in Claude Code; use those routes inside kmboards / the Daily Cookie pipeline.

## Multi-clip consistency (read before any multi-clip dispatch)

When the brief calls for **more than one clip with a recurring subject** (Brand Story arc, Fashion Lookbook, Product 360, multi-clip avatar series, "Act 1 / Act 2 / Act 3" structures), **read [`brand/consistency-rules.md`](brand/consistency-rules.md) first**. Every frame-independent video tool below — fal-seedance, HeyGen, Hedra, Kling, Veo — generates each clip statelessly, so without a Character + Product Lock block pasted byte-identical into every prompt, details drift between clips (shirt color flips, props change, hair length changes).

The rules apply regardless of which tool the orchestrator picks. Single-clip dispatches don't need this discipline.

## Available tools

You route to one or more of these. Each has a corresponding adapter in `adapters/`.

| Tool | Adapter | Strength |
|------|---------|----------|
| CutSense | `adapters/cutsense.md` | Footage cuts with brand-pill captions, silence/filler removal, multi-vertical. Default for talking-head footage. |
| HyperFrames | `adapters/hyperframes.md` | HTML+CSS+GSAP compositions. Branded title cards, kinetic type, audio-reactive visuals. |
| video-use | `adapters/video-use.md` | LLM-driven cut picking from raw transcript. Best when you have many takes or need semantic chapter detection. |
| HeyGen | `adapters/heygen.md` | AI avatar lipsync from script. No camera needed. |
| Hedra | `adapters/hedra.md` | AI avatar lipsync, alternate to HeyGen. |
| Remotion | `adapters/remotion.md` | Standalone brand cards (title / lower-third / outro CTA), pixel-perfect, fast. Composition source at `remotion-templates/brand-card/`. Also used internally by CutSense for footage rendering. |
| **fal-seedance** | `adapters/fal-seedance.md` | **Generate a fresh 4-15s video from a text prompt** (and optionally up to 9 reference images / 3 reference clips / 3 audio clips). Bytedance Seedance 2.0 via fal.ai. Native audio. Default when there is no source footage and the user wants a single cinematic / ad / social / brand-story / product / fashion clip. Pairs with the kmboards Phase B video-style skills (`video-style-cinematic`, `video-style-ecom-ad`, `video-style-social-hook`, `video-style-brand-story`, `video-style-product-360`, `video-style-fashion-lookbook`) which produce the prompt body. |
| **Gemini Omni** | `adapters/gemini-omni.md` | **Edit an EXISTING clip by describing the change** (background / weather / lighting / restyle) while preserving subject, wardrobe and props - the only wired tool that does this. Also the strongest **character lock**: one reference still holds face AND room across completely different shots. Google `gemini-omni-1.1-flash` (GA 2026-08-27), native speech. 🚨 **No duration field** - plan 10s at **flat ~$1.03/clip** at 720p, so use fal-seedance when the length must differ. 🚨 **Never direct a hand gesture that moves an object** - it spawns a duplicate and cannot be edited out. Preview (`gemini-omni-flash-preview`) dies 2026-09-30. |
| **Lottie (text-to-lottie)** | `adapters/lottie.md` | **Generate a vector motion-graphics asset** - an animated icon, loader / spinner, logo reveal, UI micro-interaction, animated SVG (e.g. Figma export), or data-driven animation - as a Lottie / Bodymovin `lottie.json`, previewed live in a Skia / Skottie player. Tiny, infinitely scalable, embeds in web / React / React Native / iOS / Android. Best for short, single-scene, looping vector pieces. The deliverable is JSON, NOT an MP4 - only screen-record the player if the user explicitly wants a video file. Authored by the `text-to-lottie` skill. |
| **broll-director** | `adapters/broll-director.md` | **Decide WHEN a talking-head video should cut away and WHAT KIND of b-roll to use** (prop cutaway, graphic card, BTS activity footage, screen recording, before/after split, VFX composite, etc), styled on the researched "Re:Vision method" (`knowledge/revision-style.md`, 117 timestamped inserts across 18 studied videos). Runs BEFORE broll-retrieval - it's the creative-direction layer, broll-retrieval is just the generic-stock sourcing layer it dispatches into. |
| **broll-retrieval** | `adapters/broll-retrieval.md` | **Retrieve real B-roll cutaways from free archives** (Archive.org, Wikimedia, NASA, Pexels, Pixabay, Unsplash), ranked by transcript/scene intent (text now, CLIP if installed), cut onto the timeline. Asset-stage helper - slots between CutSense understand->edit and exports cutaways for the in-Premiere Testimonial Cutter. Free-first, $0. |
| **music-sfx** | `adapters/music-sfx.md` | **Generate a music bed + SFX/stingers** via ElevenLabs (optional Suno). Used in the edit/compose stage. Metered but low cost; free-first. |
| **enhance** | `adapters/enhance.md` | **Optional finishing pass**: upscale / face-restore / bg-remove. Local + free (FFmpeg baseline, Real-ESRGAN/GFPGAN/rembg if installed). |

## The flow

### Step 1: Identify the source

Read what the user said and what they attached. If you have a file path, run `ffprobe` on it to get duration + resolution. If you have a URL, note it.

If neither, the request is one of four things:
- **They want to generate a fresh clip from a prompt** ("a cinematic shot of...", "a 10s product ad for...", "make me a video of..."). Source = none. Route to **fal-seedance** (and optionally pair with a kmboards `video-style-*` skill to produce the prompt body). Skip Step 2's template lookup - fal-seedance has its own brief shape (see `adapters/fal-seedance.md`).
- **They want a reusable vector motion-graphics asset** ("an animated icon", "a loading spinner", "animate our logo", "a Lottie of...", "animate this SVG / Figma export", "a data-driven animation"). Source = none. Route to **Lottie (text-to-lottie)**. Skip Step 2's template lookup AND the 6 video questions - Lottie has its own small asset brief (see `adapters/lottie.md`): what to animate, composition size, loop?, brand colors, which properties to expose as live controls. The deliverable is `lottie.json` (vector, embeds anywhere), NOT an MP4 - only record the player to a clip if the user explicitly wants a video file. If they want audio / captions / a finished MP4 instead, that is HyperFrames or fal-seedance, not Lottie.
- **They want a talking-head from a script** with no on-camera footage. Route to HeyGen / Hedra (avatar lipsync).
- **They want an EXISTING clip changed by description** ("make it rain outside the window", "restyle this", "change the background", "make it night"). Source = video. Route to **Gemini Omni** (`adapters/gemini-omni.md`) - it is the only wired tool that edits a clip conversationally while preserving subject, wardrobe and props. 🚨 Warn first that the edit **re-renders the audio too**, so a take with a good delivery should not be sent.
- **The brief needs the SAME character across several shots.** Route to **Gemini Omni** and lock identity with a single reference still (`adapters/gemini-omni.md`, Rule 1) rather than the prose Lock Block - verified far stronger. 🚨 Before dispatching, strip any object-in-hand gesture from the directed beats (Rule 2): raising / lowering / passing an object reliably spawns a duplicate that cannot be edited out.
- **They actually have source but didn't attach it.** Ask for the path / URL.

Ask which it is BEFORE running the 6 batched questions, because Source = none changes the question set materially.

### Step 2: Match to a template

Check `templates/INDEX.md` for the closest template. Most requests match one of:
- `zoom-podcast-multi.md`
- `walking-video-topics.md`
- `zoom-lecture-verticals.md`
- `talking-head-shorts.md`
- `avatar-explainer.md`
- `branded-promo-from-url.md`
- `screen-recording-tutorial.md`
- `ad-hook-variations.md`

If no template matches cleanly, build the brief from scratch.

### Step 3: Ask the 6 batched questions

Use `AskUserQuestion` in **one tool call** with these 6 questions. Phrase options to match the matched template's likely intent.

1. **Source type**: zoom_podcast / zoom_lecture / walking_selfie / screen_recording / url / other
2. **Primary intent**: vertical_clips / long_cut_polish / educational_verticals / promo / ad_variants / avatar_explainer
3. **Output count + length**: e.g. "1 x 60s vertical", "5 x 30-60s verticals + 1 x long cut", "3 x 30s ads"
4. **Captions**: brand_pill (cyan/orange) / jumbo / none
5. **Cleanup level**: heavy (silences + fillers + retakes) / standard (silences only) / off
6. **Tool mode**: pick_best / show_3_options / fork_to_3

### Step 4: Surface 2-3 options

Even if `tool_mode = pick_best`, present 2-3 candidate tools with one-line pros and cons EACH. Format:

```
Three tools fit this:

1. <tool_name> - <one-line summary>
   pros: <best fit reason>
   cons: <trade-off>

2. <tool_name> - <one-line summary>
   pros: ...
   cons: ...

3. <tool_name> - <one-line summary>
   pros: ...
   cons: ...

Pick: 1, 2, 3, or "fork all three".
```

The first option is the recommended default. Bold it. The user can override or fork.

### Step 5: Build the brief

Fill `brief-schema.json` with the user's answers + template defaults + sensible inferences. Save to `${VIDEO_JOBS_DIR}/<brief_id>/brief.json`. Show the brief inline before executing.

`brief_id` format: `YYYY-MM-DD-<3-word-slug>` (e.g. `2026-04-26-podcast-acme-launch`).

### Step 6: Dispatch

**Single-tool mode:**
1. Read `adapters/<tool>.md`
2. Run the commands listed there with values from the brief
3. Wait for output at `<output_dir>\<tool>\out_NN.mp4`
4. Run QA: `python qa/run-qa.py <brief_id>` (write QA.json per output)
5. Write `<output_dir>\COMPARE.md` (single-tool variant: tool, output link, duration, LUFS, face-safe, notes)

**Fork mode (`tool_mode = fork_to_3` or user said "fork all three"):**
1. Write `<output_dir>\brief.json`
2. **In ONE assistant turn**, spawn N parallel `Agent` calls (`subagent_type: general-purpose`). Each call receives:
   - The full brief JSON
   - One tool name they own
   - Path to that tool's adapter MD
   - Output dir `<output_dir>\<tool>\`
3. After all sub-agents return, run `python qa/run-qa.py <brief_id>` once over all forks
4. Write `<output_dir>\COMPARE.md` with the multi-tool table (see `fork/compare-template.md`)
5. Show COMPARE.md inline; surface the local file paths

### Step 7: Verify before handoff

Before saying "done":
- ffprobe each output to confirm duration matches expected
- Check QA.json - if any FAIL, fix or flag explicitly
- For fork mode, confirm all N outputs exist
- Show the user the absolute path(s) they can click

Per the verify-before-handoff rule: never say "test at <path>" without confirming the file is present and ffprobe passes.

## Universal brief contract

Every adapter takes the same brief JSON. Schema at `brief-schema.json`. Filled example at `brief-example.json`.

Required top-level keys: `brief_id`, `source`, `intent`, `output`, `cleanup`, `brand`, `tools`, `fork_mode`, `qa_gates`, `output_dir`.

Adapters MUST NOT mutate the brief. They read it, run their tool, write to `<output_dir>/<tool_name>/`.

## Brand defaults

Default brand pack: `brand/pack-personal-social.json` (cyan #40DCE0 + orange #FCA529 + near-black #0A0A0A, Outfit + JetBrains Mono).

This is wired in CutSense's `render-cut.mjs`. Override per-job by setting `brief.brand.pack` to `local/brand-pack-mine.json` (your custom site brand pack, generated locally) or any other file.

## QA gates (always run)

Three checks at `qa/`:
- `face-safety.py` (mediapipe) - no captions/overlays on face bbox
- `loudness.py` (pyloudnorm) - integrated LUFS within +/-1 of target, true peak < -1.0 dBTP
- `timing.py` (ffprobe) - duration within +/-2s of target, no cut spacing < 0.4s

`run-qa.py` orchestrates and writes QA.json per output. These are POST-render.

## Pre-compose gate: slideshow-risk (run BEFORE you spend a render)

When a job has a `scene_plan` (any pipeline, or a scene-planned generation), score it
BEFORE rendering with `qa/slideshow-risk.py`. It catches the "boring slideshow" failure
(static stills, title-card overload, no motion, unbacked cinematic claims) while it is
still cheap to fix.

```bash
python qa/slideshow-risk.py --scene-plan <job>/03-scene_plan.json --output <job>/03-risk.json
```

Default mode is **soft** (project decision "warn & confirm"): it NEVER hard-blocks. A high
score returns WARN with "rework strongly advised" - surface it and ask the human to confirm
or rework. Set `brief.precompose_gates: ["slideshow_risk"]`. Details: `qa/INDEX.md`.

## Production pipelines (make a whole video from a topic)

For `source.type == "none"` AND a full production (not one clip) - "make a 90s explainer
about X", "a documentary montage on Y", "a cinematic brand film for Z" - use a staged
pipeline instead of the 6-question single-clip flow:

```bash
python tools/scaffold_pipeline.py --pipeline explainer --topic "..." --brief-id <id>
```

Stages: research -> proposal (HUMAN GATE) -> script -> scene_plan (slideshow-risk gate) ->
assets -> edit -> compose (post-render QA). Each is one inspectable file in the job dir;
`pipeline.json` tracks status. Three pipelines: `explainer`, `documentary-montage`,
`cinematic`. See `pipelines/README.md` and `pipelines/manifest.json`.

## Scored tool selection + decision log (Step 4 upgrade)

Behind the "surface 2-3 options" step, score the candidates transparently and log the choice:

```bash
python tools/select_tool.py --brief <brief.json|brief_id> --candidates cutsense,video-use,hyperframes --output <job>/decisions.json
```

7 weighted dimensions (task_fit 30 / quality 20 / control 15 / reliability 15 / cost 10 /
latency 5 / continuity 5). Writes `decisions.json` (chosen, alternatives, confidence, est cost).
The HUMAN still approves - this just makes the ranking legible and logged. **Free-first
tie-break:** when a metered tool only narrowly beats a $0 tool, lead with the free one.
Rubric + profiles: `selection/scoring.md`, `selection/tool-profiles.json`.

## Platform render profiles (apply at compose)

Set `brief.output.render_profile` to a platform key and apply it at compose:

```bash
python tools/apply_profile.py resolve --profile youtube_shorts     # see dims + fit filter + safe margins
python tools/apply_profile.py apply --profile youtube_shorts --in in.mp4 --out out.mp4 --mode cover
```

Profiles (dimensions, fps, loudness, safe-margins, caption sizing): `render-profiles.json`
(`youtube_landscape`, `youtube_4k`, `youtube_shorts`, `instagram_reels`, `instagram_feed`,
`instagram_portrait`, `tiktok`, `linkedin`, `cinematic`).

## Knowledge packs (Layer 3, pull depth on demand)

Adapters stay thin and link to `knowledge/<provider>.md` for deep provider behaviour
(endpoints, gotchas, failure modes). Index: `knowledge/INDEX.md`. Validate links with
`python tools/check_knowledge.py`.

## Multi-clip consistency (READ BEFORE DISPATCHING MULTI-CLIP)

If the brief produces more than one independent clip - a Brand Story arc (3-4 clips), a Fashion Lookbook reel (multi-shot), a Product 360 set (multi-angle), a chained avatar series, any "Act 1 / Act 2 / Act 3" structure - read [brand/consistency-rules.md](brand/consistency-rules.md) before dispatching to the adapter.

The 3 rules in one breath: clothing must be byte-identical across clips, items must be byte-identical across clips, only setting / background / time of day / lighting recipe / subject action change. The model has NO memory between clips. Without these rules, the founder's shirt color changes between Act 1 and Act 3, the fashion model in shot 1 becomes a different person by shot 4, the product gains a logo it didn't have. Source: Million Dollar Group Method, Lesson 13.

The orchestrator's job for multi-clip dispatch: build a **Lock Block** ONCE in the brief, paste it verbatim into every clip prompt the adapter generates. Adapters affected: `fal-seedance.md`, `heygen.md`, `hedra.md`. Editing adapters (`cutsense.md`, `video-use.md`, `hyperframes.md`) are unaffected because they work on existing footage.

## Anti-patterns

- Rendering a SCRIPTED video (ad/promo/story/hook/explainer) from an ad-hoc prompt you invented, skipping the writers' room. Run senior-scriptwriter (words) then senior-creative-director (shots) first, then render from the directed beats.
- Picking a tool without surfacing alternatives. Always show 2-3 options.
- Skipping the question batch and inferring from a one-liner. Ask.
- Letting watch-video grab the turn. The orchestrator's description must trigger first.
- Sequential sub-agents in fork mode. Always parallel, always in one assistant turn.
- Saying "done" before QA passes. Always verify, always include the path.
- Mutating the brief inside an adapter. Brief is read-only contract.
- Burying captions on faces. Face-safety QA is non-optional.
- Em-dashes anywhere in user-facing output (project rule).
- Dispatching a multi-clip generation without applying the Lock Block from `brand/consistency-rules.md`. Drift is silent and only visible at QA - by then you've burned the credits.
- Paraphrasing a Lock Block between clips ("the founder from Act 1"). The model cannot resolve back-references. Paste verbatim.

## Where things live

- Skill root: `<skill_root>/`
- Output jobs: `${VIDEO_JOBS_DIR}/<brief_id>/`
- video-use install: `${VIDEO_USE_DIR}/` (clone from https://github.com/browser-use/video-use)
- CutSense source: `${CUTSENSE_DIR}/` (your local CutSense clone)
- HyperFrames CLI: `npx hyperframes` (junctioned skill at `~/.claude/skills/hyperframes/`)
- Lottie player harness: scaffold with `npx degit diffusionstudio/lottie <dir>` then `npm install && npm run dev` (Vite, http://localhost:5173). JSON authored by the `text-to-lottie` skill (`~/.claude/skills/text-to-lottie/`). Reuse one clone to skip re-installing CanvasKit.
- HeyGen call shape: a typical 2-step provider-pick pattern (avatar_id present -> HeyGen, else Hedra)

## Keys (read from `local/.env`, never hardcode)

All API keys live in `local/.env` (copy from `.env.example` at skill root). Required keys:

- `ELEVENLABS_API_KEY` (Scribe + TTS)
- `GROQ_API_KEY` (Whisper alternate)
- `HEYGEN_API_KEY`
- `HEDRA_API_KEY`
