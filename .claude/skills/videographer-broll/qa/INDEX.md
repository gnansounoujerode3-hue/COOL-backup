# video-orchestrator QA gates

There are two phases of gate. **Post-render** gates (the original three) run on
rendered `out_*.mp4` files via `run-qa.py`. **Pre-compose** gates run on the
`scene_plan.json` BEFORE any render spend, so a boring or broken plan is caught
before credits/time are burned.

Three automated post-render gates run after every render. They never block a
render; they flag issues so the orchestrator can decide whether to ship, rework,
or pick a different fork. The orchestrator invokes them via `run-qa.py` after a
tool (or all forks) finish writing to `${VIDEO_JOBS_DIR}/<brief_id>/<tool>/`.

## Pre-compose gate: slideshow-risk

| Gate | Script | What it asserts | Verdict bands |
|------|--------|-----------------|---------------|
| Slideshow risk | `<skill_root>/qa/slideshow-risk.py` | A `scene_plan.json` will not render as a static "slideshow". Scores 6 dims (repetition, decorative visuals, weak motion, shot intent, typography overreliance, unsupported cinematic claims), weighted into one 0..1 risk. | PASS = risk < 0.34. WARN = 0.34 to 0.67 (and, in soft mode, anything above). FAIL = >= 0.67 only in `--mode hard`. |

Default mode is **soft** (project decision "warn & confirm"): it NEVER hard-blocks.
High risk surfaces as WARN with `recommendation: "rework strongly advised"` and the
orchestrator asks the human to confirm or rework. Pass `--mode hard` to make
>= 0.67 a FAIL that blocks the compose step.

```bash
python <skill_root>/qa/slideshow-risk.py --scene-plan <plan.json> --output <risk.json>
# or, against a job dir:
python <skill_root>/qa/slideshow-risk.py --brief <brief_id> --output <risk.json>
```

It reads a scene plan (schema: `<skill_root>/schemas/scene-plan.schema.json`), NOT a
video, so it is NOT registered in `run-qa.py`. The orchestrator runs it between the
`scene_plan` and `assets`/`compose` stages of the production pipeline (see
`pipelines/`). Brief field: `precompose_gates: ["slideshow_risk"]`. Worked examples:
`qa/examples/scene-plan-slideshow.json` (high) and `qa/examples/scene-plan-good.json` (low).

## Post-render gates

## Gates

| Gate | Script | What it asserts | Verdict bands |
|------|--------|-----------------|---------------|
| Face safety | `<skill_root>/qa/face-safety.py` | Caption pill rect (from `brand/captions.preset.json`) does not overlap any detected face bbox at any sampled frame (4 fps via MediaPipe). | PASS = 0 violations. WARN = 1 to 3 violations or violations under 5 percent of frames. FAIL = violations over 5 percent of frames. |
| Loudness | `<skill_root>/qa/loudness.py` | Integrated LUFS within tolerance of `brief.cleanup.loudness_target_lufs`, plus true peak under `brief.cleanup.true_peak_max_dbtp`. | PASS = within +/-1 LUFS and peak OK. WARN = within +/-2 LUFS and peak OK. FAIL = beyond +/-2 LUFS or peak over max. |
| Timing | `<skill_root>/qa/timing.py` | Duration within tolerance of `brief.output.length_target_sec`. For 9:16 with a sibling `edl.json`, no cut shorter than 0.4s. | PASS = within +/-2s and no spacing violation. WARN = within +/-2 to +/-5s. FAIL = beyond +/-5s or spacing under 0.4s. |

Each gate writes its own JSON next to the source video:

```
${VIDEO_JOBS_DIR}/<brief_id>/<tool>/out_01.mp4
${VIDEO_JOBS_DIR}/<brief_id>/<tool>/out_01.face_safety.json
${VIDEO_JOBS_DIR}/<brief_id>/<tool>/out_01.loudness.json
${VIDEO_JOBS_DIR}/<brief_id>/<tool>/out_01.timing.json
${VIDEO_JOBS_DIR}/<brief_id>/<tool>/out_01.qa.json
```

The aggregated job summary is written to:

```
${VIDEO_JOBS_DIR}/<brief_id>/QA.json
```

## Install

The QA gates use `mediapipe`, `opencv-python`, `pyloudnorm`, `soundfile`, and
`numpy`. `ffmpeg` and `ffprobe` must be on PATH.

```bash
cd <skill_root>
uv venv .venv
.\.venv\Scripts\activate
uv pip install mediapipe opencv-python pyloudnorm soundfile numpy
```

Note: `mediapipe` does not yet ship a Python 3.13 wheel. Use Python 3.11 or
3.12 (`uv venv --python 3.12 .venv`). If you hit a missing-wheel error,
that is the cause.

## How the orchestrator invokes it

After single-tool dispatch or after all fork sub-agents return, the
orchestrator runs:

```bash
python <skill_root>/qa/run-qa.py <brief_id>
```

Exit code is 0 (all PASS), 1 (any WARN, no FAIL), or 2 (any FAIL or fatal
setup error). The orchestrator must read `QA.json` and surface the overall
verdict + path before saying done.

## Adding a new gate

1. Drop a new script into `<skill_root>/qa/`
   (for example `aspect-ratio.py`). It must accept `--brief`, `--video`, and
   `--output` and write a JSON with at least a `verdict` field of
   `PASS` / `WARN` / `FAIL`. Exit code 0 / 1 / 2 must match.
2. Add the gate name to the `qa_gates` enum in
   `<skill_root>/brief-schema.json`.
3. Register the script path in the `GATE_SCRIPTS` dict at the top of
   `<skill_root>/qa/run-qa.py`.
4. Update this INDEX.md row table.
5. Update the COMPARE template at
   `<skill_root>/fork/compare-template.md`
   if the new gate should appear in the side-by-side fork table.
