# Pipeline: explainer

Research-grounded educational video. A claim, concept, or how-to explained with a
narration track and supporting visuals (b-roll, data cards, sparing title cards).

Default engine: **CutSense** (assembles narration + visuals).
Default tools: narration = ElevenLabs TTS, visuals = broll-retrieval, data =
HyperFrames cards, compose = Remotion.

## Stage-by-stage

### 0. research (`00-research.md`)
Gather the facts. Every non-obvious claim gets a source. Pick ONE angle - an
explainer that tries to say everything says nothing. Output: bullet facts +
citations + the chosen angle.

### 1. proposal (`01-proposal.md`) - HUMAN GATE
Logline, audience, tone, length target, platform, the one thing the viewer should
remember. Get a human yes here before any asset spend.

### 2. script (`02-script.md`)
Write the VO. ~150 wpm -> a 90s explainer is ~225 words. Mark where a visual must
change. The script drives shot count.

### 3. scene_plan (`03-scene_plan.json`) - SLIDESHOW-RISK GATE
Turn the script into shots (`schemas/scene-plan.schema.json`). For each line of VO,
decide the visual: real b-roll of the named noun, a data card, the speaker, or (rarely)
a title card. Then run:

```bash
python qa/slideshow-risk.py --scene-plan <job>/03-scene_plan.json --output <job>/03-risk.json
```

Explainers fail `typography_overreliance` and `weak_motion` first - they drift into a
slideshow of title cards. If the gate WARNs, swap title cards for b-roll + add camera
moves / Ken Burns, then re-run and confirm.

### 4. assets (`04-assets.md`)
Resolve each shot's visual. Most come from `adapters/broll-retrieval.md` (free-first,
license logged in `broll-manifest.json`). Data points become HyperFrames cards. Budget:
free-first default, so this stage is usually $0 (only ElevenLabs TTS is metered, low cost).

### 5. edit (`05-edit.md`)
Assemble the timeline in CutSense: VO track, cutaways per the b-roll manifest, captions
(brand-pill), an optional low music bed from `adapters/music-sfx.md`. Keep cutaway density
under ~1 per 6-8s.

### 6. compose (`06-compose.md`)
Apply the `render_profile` (e.g. `youtube_landscape` or `youtube_shorts`), render via
Remotion/CutSense, then `python qa/run-qa.py <brief_id>`. Ship on PASS/WARN with the path.

## Watch-outs
- Title-card slideshow is the #1 failure. Visuals should SHOW the noun, not spell it.
- Cite in `00-research.md`; an explainer that is wrong is worse than boring.
