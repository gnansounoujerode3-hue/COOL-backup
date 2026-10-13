# Pipeline: documentary-montage

A thematic montage cut from **real archive / stock footage** over a narration track.
Retrieval-first: the footage IS the video. This is the OpenMontage documentary
capability - free archives (Archive.org, NASA, Wikimedia) plus free-key stock
(Pexels, Pixabay, Unsplash) searched and cut into a timeline.

Default engine: **CutSense**.
Default tools: narration = ElevenLabs TTS, visuals = broll-retrieval, music =
music-sfx, compose = CutSense.

## Stage-by-stage

### 0. research (`00-research.md`)
Find the throughline and the beats. List the concrete nouns/scenes the montage needs
to show (each becomes a retrieval query). Sourced, with an angle.

### 1. proposal (`01-proposal.md`) - HUMAN GATE
Logline, tone, length, platform. Human yes before spend (here spend is ~$0 anyway,
but the proposal still anchors the cut).

### 2. script (`02-script.md`)
Narration over the montage. Each VO beat maps to one or more shots.

### 3. scene_plan (`03-scene_plan.json`) - SLIDESHOW-RISK GATE
One shot per beat: `asset_kind: "broll"`, a `query`, a target duration. Stills
(`asset_kind: "image"` from Wikimedia/Unsplash) MUST declare `camera_move: "ken-burns"`
or they trip `weak_motion`. Run the gate; a montage of frozen stills is the exact thing
it catches.

### 4. assets (`04-assets.md`) - the heart of this pipeline
Retrieve real footage per shot:

```bash
# wide corpus once, then search per beat (cheapest):
python tools/broll_corpus.py build  --query "<theme>" --sources archive,wikimedia,nasa,pexels,pixabay --out <job>/broll/corpus.json
python tools/broll_corpus.py search --corpus <job>/broll/corpus.json --query "<beat 1>" --topk 3
python tools/broll_corpus.py fetch  --corpus <job>/broll/corpus.json --id <chosen> --out <job>/broll/
```

Write `broll-manifest.json` (per-shot clip + **license + page_url**). Provenance is
mandatory - never ship a clip whose free license you did not log. Install
`sentence-transformers` to switch the ranker from text to true CLIP visual match.

### 5. edit (`05-edit.md`)
Cut the clips to the narration in CutSense. Add a music bed + transition stingers via
`adapters/music-sfx.md`. Ken-burns the stills. Cross-dissolve between archival clips for
a doc feel.

### 6. compose (`06-compose.md`)
Apply the `render_profile`, render, run `qa/run-qa.py`. The license log travels with the
output.

## Watch-outs
- License logging is non-negotiable (Radical Transparency + actual rights).
- Stills need motion. Frozen stock photos = slideshow.
- Mixed sources have mixed quality; CLIP ranking helps pick clips that actually look right.
