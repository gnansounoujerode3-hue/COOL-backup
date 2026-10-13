# Pipeline: cinematic

A mood-driven generated piece - trailer, brand film, hero reveal - built from
**generated** shots (fal-seedance / veo3) over a music bed. This is the only
pipeline that spends metered API money, so budget governance (free-first default)
and the multi-clip Lock Block both apply.

Default engine: **fal-seedance**.
Default tools: visuals = fal-seedance, music = music-sfx, enhance = enhance,
compose = Remotion.

## Stage-by-stage

### 0. research (`00-research.md`)
The reference board: mood, palette, era, comparable films. Less fact-finding, more
visual language. Output the look you are chasing.

### 1. proposal (`01-proposal.md`) - HUMAN GATE
Logline, tone, length, platform, and a **budget cap**. Because this pipeline spends,
the human gate here also approves the spend ceiling. Default mode is free-first, so the
agent must justify any metered generation against the cap.

### 2. script (`02-script.md`)
A beat sheet, not a VO script. For multi-shot consistency, draft ONE Lock Block
(character + product + casting per `brand/consistency-rules.md`) and reuse it byte-for-byte
across every shot prompt. Pair with the kmboards `video-style-*` skills to author the
prompt bodies (cinematic / brand-story / product-360 / fashion-lookbook).

### 3. scene_plan (`03-scene_plan.json`) - SLIDESHOW-RISK GATE
Shots with rich `camera_move` + `lighting`. Cinematic plans usually pass weak_motion
easily but can trip `unsupported_cinematic_claims` - "epic" in the prompt without a real
camera move + lighting recipe. The gate forces the craft to back the adjective.

### 4. assets (`04-assets.md`) - METERED, budget-gated
Generate each shot via `adapters/fal-seedance.md` (or `veo3.md` for synced dialogue).
BEFORE generating: estimate cost, check it against the cap from the proposal, and prefer
the fast tier. Log each generation's cost + seed. Free-first means: if a shot could be a
free b-roll clip instead of a paid generation, prefer the b-roll.

### 5. edit (`05-edit.md`)
Concatenate shots, place a music bed + stingers (`adapters/music-sfx.md`), optional
upscale / face-restore polish (`adapters/enhance.md`). Transitions per the mood.

### 6. compose (`06-compose.md`)
Apply the `render_profile` (often `cinematic` 21:9 or `youtube_landscape`), render, run
`qa/run-qa.py`. The visual frame-check matters here (generated clips can fail silently to
a placeholder - see fal-seedance QA notes).

## Watch-outs
- Lock Block byte-identical across shots or the subject drifts between clips.
- Budget: this is the one pipeline that costs real money. Free-first, estimate before
  spend, respect the cap. Never batch metered generation without the human gate's approval.
- "Cinematic" is earned by camera + lighting, not by the word. The gate enforces this.
