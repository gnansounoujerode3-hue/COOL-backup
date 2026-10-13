# Adapter: broll-retrieval (free-first stock + archive B-roll)

## What this tool does

Finds real motion B-roll (and stills for Ken Burns) from open sources, ranks it
against transcript / scene-intent text, and cuts the chosen clips onto the
timeline as cutaways. It is **retrieval**, not generation: every frame is a real
clip with a real license. $0 out of pocket - all sources are free (some need a
free API key). This is the "OpenMontage documentary-montage" capability ported
to our stack.

Engine: [`../tools/broll_corpus.py`](../tools/broll_corpus.py).
Deep provider notes: [`../knowledge/broll-sources.md`](../knowledge/broll-sources.md).

## Where it slots in (the seam)

B-roll retrieval is **not** a standalone render tool. It runs **between CutSense's
understand and edit stages**, and it also exports cutaways for the in-Premiere
Testimonial Cutter. 🚨 **When `broll-director` is in play** (`adapters/broll-director.md`
- the creative-direction layer that decides WHAT KIND of cutaway a moment needs,
styled on the researched Re:Vision method), this tool only handles the narrow
subset broll-director routes to it: truly generic nouns with no client-specific
version. Don't run this tool standalone on a job that wants directed, styled
b-roll - broll-director dispatches here, not the other way around.

```
CutSense ingest -> CutSense understand (VUD: transcript, topics, energy curve, key moments)
                          |
                          v
              [ broll-director, if enabled ]  <- classifies WHAT KIND first
                          |
                          v
                 [ broll-retrieval ]   <- you are here
                  1. read the VUD
                  2. find B-roll OPPORTUNITIES (talking-head-only spans, low-energy
                     spans, spans where the speaker NAMES a concrete noun)
                  3. turn each opportunity into a search query (the topic / entity /
                     the literal noun phrase from the transcript at that timestamp)
                  4. retrieve + rank candidates per opportunity
                  5. write broll-manifest.json (timestamp -> chosen clip + license)
                          |
                          v
CutSense edit (overlay cutaways per the manifest) -> render -> QA
```

For the **in-Premiere Testimonial Cutter**: instead of feeding CutSense, write the
same `broll-manifest.json` to the job dir and hand it to the cutter's
`kmBuildCutFromListFile` step as a B-track cutaway list (each entry = insert clip
X over the A-track from t_start to t_end). See "Export for Testimonial Cutter".

## When the orchestrator dispatches here

| Trigger | Notes |
|---|---|
| A talking-head / podcast / testimonial cut feels visually flat (long static face spans) | Add cutaways over the named concepts |
| `brief.broll.enabled == true` | Explicit B-roll pass requested |
| Documentary / explainer pipeline `assets` stage (see `pipelines/documentary-montage.md`) | Primary footage source is retrieval |
| User says "add b-roll", "cut to footage when I mention X", "make it less of a talking head" | Direct request |

Not for: pure generated clips (that is fal-seedance / veo3), or footage the user
already supplied.

## Inputs read from brief

```jsonc
"broll": {
  "enabled": true,
  "sources": ["archive", "wikimedia", "nasa", "pexels", "pixabay", "unsplash"],
  "max_per_opportunity": 3,      // candidates to retrieve per query
  "min_score": 0.25,             // drop weak matches (text method) - tune up for CLIP
  "prefer_motion": true,         // rank video over stills
  "queries": []                  // optional explicit query list; else derived from the VUD
}
```

Default `sources` is free-first. With the keyed sources enabled (Pexels +
Pixabay + Unsplash), keys are read from `local/.env`
(`PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`). Missing keys are
skipped with a warning, never an error - the free sources still run.

## Commands

```bash
# Build a corpus for one query across sources, then rank (one shot):
python tools/broll_corpus.py find --query "ocean waves at sunrise" \
  --sources archive,wikimedia,nasa,pexels,pixabay --limit 12 --topk 3 --out shot.json

# Or split it: build a wide corpus once, search it many times (cheaper for a montage):
python tools/broll_corpus.py build  --query "renewable energy" --sources archive,pexels --out corpus.json
python tools/broll_corpus.py search --corpus corpus.json --query "wind turbines on a hill" --topk 3
python tools/broll_corpus.py search --corpus corpus.json --query "solar panels close up"   --topk 3

# Download the chosen clip:
python tools/broll_corpus.py fetch --corpus corpus.json --id archive:NewYorkSkylineTimeLapseMarch2008 --out broll/
```

`find`/`search` print a ranked list and (with `--out`) write the ranked JSON. Each
candidate carries `source`, `media_type`, `duration_sec`, `license`, `page_url`,
`file_url`/`thumb_url`, and a `score` + `rank_method`.

## Ranking: text now, CLIP when installed

- **Default (no deps):** pure-stdlib text relevance over title + tags + description.
  Runs everywhere, $0, good enough to shortlist.
- **CLIP upgrade (opt-in):** `pip install sentence-transformers pillow` and the tool
  auto-switches to true visual retrieval - it embeds the query text and each
  candidate's **thumbnail image** with `clip-ViT-B-32` and ranks by cosine. No code
  change; it detects the import. Use this when a montage needs the clip to actually
  *look* like the scene, not just be tagged with the word.

## Building the opportunity list from a VUD

CutSense's VUD (`packages/core/src/types/vud.ts`) gives `segments`, `topics`,
`entities`, `energy` curve, and `key_moments`. To derive B-roll queries:

1. Walk `segments`. Flag spans that are talking-head-only AND either (a) below a
   median energy threshold, or (b) contain a concrete entity/noun-phrase.
2. For each flagged span, the query = the entity name or the noun phrase spoken at
   that timestamp (e.g. transcript says "...when we shipped to **Tokyo**..." ->
   query "Tokyo city street").
3. Cap density: no more than ~1 cutaway per 6-8s, and never over a face the speaker
   is emphasizing (defer to face-safety on the final render).

## broll-manifest.json (the output contract + provenance)

Write to `${VIDEO_JOBS_DIR}/<brief_id>/broll/broll-manifest.json`:

```json
{
  "brief_id": "2026-06-30-acme-explainer",
  "source_video": "E:/.../talking-head.mp4",
  "cutaways": [
    {
      "t_start": 12.4, "t_end": 15.1,
      "reason": "speaker says 'Tokyo'; low-energy talking-head span",
      "query": "Tokyo city street",
      "clip_id": "pexels:1234567",
      "file": "broll/pexels-1234567.mp4",
      "license": "Pexels License (free, no attribution required)",
      "page_url": "https://www.pexels.com/video/1234567/"
    }
  ]
}
```

Every cutaway records its **license + source page** - that is the Radical
Transparency requirement. Never ship a clip whose license you did not log here.
Stills (`media_type: image`, e.g. Unsplash) get a Ken Burns note: the editor
should pan/zoom them, not freeze-frame.

## Export for the in-Premiere Testimonial Cutter

The Testimonial Cutter consumes a list file. Convert `broll-manifest.json` to the
cutter's B-track insert list (one row per cutaway: `t_start`, `t_end`, `file`) and
hand it to `kmBuildCutFromListFile` so each retrieved clip is dropped onto the
B-track over the A-track talking head. Keep the manifest as the provenance record
so the cutter's output carries the same license log.

## QA + gates

- Run the **slideshow-risk pre-gate** (`qa/slideshow-risk.py`) on the scene_plan
  BEFORE rendering a montage built largely from stills - it catches "this is a
  slideshow of stock photos", which is exactly the failure mode retrieval can
  drift into. See `qa/INDEX.md`.
- After render, the normal post-render gates (timing, loudness, face-safety) apply.

## Anti-patterns

- Shipping a clip without logging its license in `broll-manifest.json`. Always log.
- Using stills as if they were motion - Unsplash/Wikimedia images need Ken Burns.
- Over-cutting: more than ~1 cutaway per 6-8s reads as frantic. Respect density caps.
- Treating archive/NASA `file_url` as known at build time - it is resolved lazily at
  `fetch` (Archive.org via its metadata API, NASA via the item collection.json).
- Relying on Pexels/Pixabay signed/CDN URLs long-term - download at fetch, do not
  store the URL.
- Assuming CLIP is active. If visual fidelity matters, confirm `sentence-transformers`
  is installed; otherwise you are on the text ranker (tags, not pixels).
