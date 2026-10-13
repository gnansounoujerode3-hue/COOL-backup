# Production pipelines (make a whole video from a topic)

The orchestrator's single-clip flow starts at "you have a source" or "make one
clip." This is the other front-end: **generate a whole video from a topic** -
the OpenMontage-style staged production, ported to our brief + tool model.

## When to use a pipeline (vs the 6-question single-clip flow)

Use a pipeline when `source.type == "none"` AND the ask is a full production, not
one clip:

- "make a 90s explainer about X"
- "a 2-minute documentary montage on Y"
- "a cinematic brand film for Z"

For a single generated clip ("a 10s product shot of...") stay on fal-seedance /
veo3 via `templates/scene-plan-from-vague-brief.md`. Pipelines are for multi-shot
pieces that need research, a script, and an assembled timeline.

## The stages

Every pipeline walks the same 7 stages, each producing one **inspectable file**
in the job dir (`${VIDEO_JOBS_DIR}/<brief_id>/`):

| # | Stage | File | Gate |
|---|-------|------|------|
| 0 | research | `00-research.md` | - |
| 1 | proposal | `01-proposal.md` | **human approval** (before any spend) |
| 2 | script | `02-script.md` | - |
| 3 | scene_plan | `03-scene_plan.json` | **slideshow-risk** (pre-compose) |
| 4 | assets | `04-assets.md` | budget within cap + license logged |
| 5 | edit | `05-edit.md` | - |
| 6 | compose | `06-compose.md` | post-render QA (`run-qa.py`) |

`pipeline.json` tracks each stage's status. The machine-readable definition (stages,
success criteria, default tools per pipeline) is `manifest.json`.

## Scaffold a run

```bash
python tools/scaffold_pipeline.py --pipeline explainer \
  --topic "how same-day flower delivery works" \
  --brief-id 2026-06-30-flower-explainer
```

This writes the 7 stage skeletons + `pipeline.json` into the job dir. Then fill them
in order. Two hard checkpoints: get `01-proposal.md` human-approved before spending,
and run the slideshow-risk gate on `03-scene_plan.json` before assets/compose.

## The three pipelines

- **[explainer.md](explainer.md)** - research-grounded educational video.
- **[documentary-montage.md](documentary-montage.md)** - retrieval-first montage from free archives.
- **[cinematic.md](cinematic.md)** - generated mood piece (fal-seedance / veo3) with a music bed.

## How this composes with the rest of the skill

- **scene_plan** uses `schemas/scene-plan.schema.json` (same shape the slideshow-risk
  gate reads).
- **assets** dispatches to `adapters/broll-retrieval.md` (documentary/explainer) or
  `adapters/fal-seedance.md` (cinematic), logging provenance + budget.
- **edit** can pull a music bed + stingers via `adapters/music-sfx.md` and a polish
  pass via `adapters/enhance.md`.
- **compose** applies a `render_profile` (see `render-profiles.json`) and runs the
  post-render QA gates.

This is still human-in-the-loop: the proposal gate and the slideshow-risk WARN both
pause for a human yes before proceeding.
