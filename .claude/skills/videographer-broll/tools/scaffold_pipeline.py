"""Scaffold a staged production pipeline run for video-orchestrator.

Reads pipelines/manifest.json, resolves the chosen pipeline's stages (common
stages + per-pipeline overrides), and writes one inspectable skeleton file per
stage into the job dir, plus a pipeline.json that tracks stage status. This is
the B1 "full production pipeline" front-end: research -> proposal -> script ->
scene_plan -> assets -> edit -> compose, each a file the human (and the agent)
can open and review.

Usage:
  python scaffold_pipeline.py --pipeline explainer --topic "how same-day flower delivery works" \
     --brief-id 2026-06-30-flower-explainer [--out <dir>]

If --out is omitted, the job dir is ${VIDEO_JOBS_DIR}/<brief_id> (or
<skill_root>/VideoJobs/<brief_id> when VIDEO_JOBS_DIR is unset).

Exit codes: 0 ok, 2 error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = SKILL_ROOT / "pipelines" / "manifest.json"
JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (SKILL_ROOT / "VideoJobs"))


def die(msg: str) -> None:
    print(f"scaffold: {msg}", file=sys.stderr)
    sys.exit(2)


def resolve_stages(manifest: dict[str, Any], pipeline: str) -> list[dict[str, Any]]:
    common = manifest.get("common_stages", [])
    pipe = manifest.get("pipelines", {}).get(pipeline)
    if not pipe:
        die(f"unknown pipeline '{pipeline}'. Available: {', '.join(manifest.get('pipelines', {}))}")
    overrides = pipe.get("stage_overrides", {}) or {}
    stages = []
    for st in common:
        merged = dict(st)
        if st["id"] in overrides:
            merged.update(overrides[st["id"]])
        stages.append(merged)
    return stages


def stage_skeleton_md(stage: dict[str, Any], topic: str, pipeline: str) -> str:
    gate = stage.get("gate") or "none"
    human = " (HUMAN APPROVAL REQUIRED before proceeding)" if stage.get("human_gate") else ""
    return (
        f"---\n"
        f"stage: {stage['id']}\n"
        f"pipeline: {pipeline}\n"
        f"status: pending\n"
        f"gate: {gate}\n"
        f"---\n\n"
        f"# {stage['id'].replace('_', ' ').title()}{human}\n\n"
        f"**Topic:** {topic}\n\n"
        f"**This stage produces:** {stage.get('produces', '')}\n\n"
        f"**Done when:** {stage.get('success', '')}\n\n"
        f"---\n\n"
        f"<!-- Fill this in. Keep it inspectable: a human should be able to read this\n"
        f"     file and understand the decision made at this stage. -->\n\n"
        f"TODO\n"
    )


def scene_plan_skeleton(topic: str) -> dict[str, Any]:
    return {
        "title": topic,
        "logline": "",
        "total_duration_sec": 0,
        "_schema": "../../schemas/scene-plan.schema.json",
        "_gate": "run qa/slideshow-risk.py on this file before the assets/compose stages",
        "shots": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a production pipeline run")
    ap.add_argument("--pipeline", required=True, help="explainer | documentary-montage | cinematic")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--brief-id", default="", help="YYYY-MM-DD-slug; defaults to a dated slug from --topic")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not MANIFEST.is_file():
        die(f"manifest not found: {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    brief_id = args.brief_id
    if not brief_id:
        slug = "-".join(args.topic.lower().split()[:3])
        slug = "".join(c for c in slug if c.isalnum() or c == "-") or "untitled"
        brief_id = f"{datetime.now(timezone.utc).date().isoformat()}-{slug}"

    out_dir = Path(args.out) if args.out else (JOBS_ROOT / brief_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    stages = resolve_stages(manifest, args.pipeline)
    created: list[str] = []
    state_stages: list[dict[str, Any]] = []

    for st in stages:
        fname = st["file"]
        fpath = out_dir / fname
        if fname.endswith(".json"):
            fpath.write_text(json.dumps(scene_plan_skeleton(args.topic), indent=2), encoding="utf-8")
        else:
            fpath.write_text(stage_skeleton_md(st, args.topic, args.pipeline), encoding="utf-8")
        created.append(str(fpath))
        state_stages.append({
            "id": st["id"],
            "file": fname,
            "status": "pending",
            "gate": st.get("gate"),
            "human_gate": bool(st.get("human_gate")),
        })

    pipe_meta = manifest["pipelines"][args.pipeline]
    state = {
        "brief_id": brief_id,
        "pipeline": args.pipeline,
        "topic": args.topic,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "default_engine": pipe_meta.get("default_engine"),
        "default_tools": pipe_meta.get("default_tools", {}),
        "notes": pipe_meta.get("notes", ""),
        "stages": state_stages,
    }
    (out_dir / "pipeline.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(f"scaffold: pipeline={args.pipeline} brief_id={brief_id}")
    print(f"scaffold: job dir -> {out_dir}")
    print(f"scaffold: {len(created)} stage files + pipeline.json")
    for c in created:
        print(f"  - {Path(c).name}")
    print("\nnext: fill 00-research.md, get the proposal approved, then work down the stages.")
    print("the scene_plan (03-scene_plan.json) must pass qa/slideshow-risk.py before assets/compose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
