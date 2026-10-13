"""Scored tool selection + decision log for video-orchestrator (B2).

Turns the orchestrator's "surface 2-3 options" step into a transparent, weighted
score and writes a decisions.json audit trail. The human still picks - this just
makes the ranking legible and logged (Radical Transparency).

Scores each candidate tool across 7 dimensions (OpenMontage's rubric):
  task_fit 30% | quality 20% | control 15% | reliability 15% | cost 10% | latency 5% | continuity 5%

task_fit is derived from the brief (source.type + intent) against each tool's
good_for_* profile. The other six are static priors in selection/tool-profiles.json.

Usage:
  python select_tool.py --brief <brief.json | brief_id> --candidates cutsense,video-use,hyperframes --output decisions.json
  python select_tool.py --brief brief-example.json --candidates cutsense,video-use,hyperframes

Exit codes: 0 ok, 2 error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROFILES = SKILL_ROOT / "selection" / "tool-profiles.json"
JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (SKILL_ROOT / "VideoJobs"))

PRIOR_DIMS = ("quality", "control", "reliability", "cost", "latency", "continuity")


def die(msg: str) -> None:
    print(f"select_tool: {msg}", file=sys.stderr)
    sys.exit(2)


def load_brief(ref: str) -> dict[str, Any]:
    p = Path(ref)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    # treat as brief_id under a few likely roots
    for cand in (JOBS_ROOT / ref / "brief.json", SKILL_ROOT / ref):
        if cand.is_file():
            return json.loads(cand.read_text(encoding="utf-8"))
    die(f"brief not found (tried path, {JOBS_ROOT / ref / 'brief.json'})")
    return {}


def task_fit(profile: dict[str, Any], source_type: str, intent: str) -> float:
    fit = 0.2
    if source_type and source_type in profile.get("good_for_source", []):
        fit += 0.5
    if intent and intent in profile.get("good_for_intent", []):
        fit += 0.3
    return min(1.0, round(fit, 4))


def confidence_band(sep: float, n: int) -> str:
    if n < 2:
        return "n/a (single candidate)"
    if sep >= 0.12:
        return "high"
    if sep >= 0.05:
        return "medium"
    return "low"


def main() -> int:
    ap = argparse.ArgumentParser(description="Scored tool selection + decision log")
    ap.add_argument("--brief", required=True, help="path to brief.json or a brief_id")
    ap.add_argument("--candidates", required=True, help="comma-separated tool names")
    ap.add_argument("--output", default="", help="path to write decisions.json (default: <job>/decisions.json if brief_id resolvable, else stdout only)")
    ap.add_argument("--profiles", default=str(PROFILES))
    args = ap.parse_args()

    prof_doc = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    weights = prof_doc["weights"]
    profiles = prof_doc["tools"]
    metered_kinds = set(prof_doc.get("metered_kinds", []))

    brief = load_brief(args.brief)
    source_type = str((brief.get("source") or {}).get("type", "") or "")
    intent = str(brief.get("intent", "") or "")
    count = int((brief.get("output") or {}).get("count", 1) or 1)

    cands = [c.strip() for c in args.candidates.split(",") if c.strip()]
    if not cands:
        die("no candidates given")

    scored: list[dict[str, Any]] = []
    for tool in cands:
        prof = profiles.get(tool)
        if not prof:
            scored.append({"tool": tool, "error": "no profile; cannot score", "score": 0.0})
            continue
        fit = task_fit(prof, source_type, intent)
        dims = {"task_fit": fit}
        for d in PRIOR_DIMS:
            dims[d] = float(prof.get(d, 0.5))
        score = sum(weights[d] * dims[d] for d in weights)
        kind = prof.get("kind", "")
        unit_cost = float(prof.get("est_cost_usd", 0.0))
        est_cost = round(unit_cost * (count if kind in metered_kinds else 1), 2)
        # rationale: the two dims that helped and hurt most vs a 0.5 baseline
        deltas = sorted(((weights[d] * (dims[d] - 0.5), d) for d in weights), reverse=True)
        best = deltas[0][1]
        worst = deltas[-1][1]
        rationale = f"strongest on {best} ({dims[best]:.2f}); weakest on {worst} ({dims[worst]:.2f}); fit={fit:.2f} for {source_type or 'no-source'}/{intent or 'no-intent'}"
        scored.append({
            "tool": tool,
            "kind": kind,
            "score": round(score, 4),
            "dimensions": {d: round(dims[d], 3) for d in dims},
            "est_cost_usd": est_cost,
            "metered": kind in metered_kinds,
            "rationale": rationale,
        })

    scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    top = scored[0]
    runner = scored[1] if len(scored) > 1 else None
    sep = (top["score"] - runner["score"]) if runner and "score" in runner else 1.0
    confidence = confidence_band(sep, len([s for s in scored if "error" not in s]))

    decisions = {
        "brief_id": brief.get("brief_id"),
        "source_type": source_type,
        "intent": intent,
        "output_count": count,
        "weights": weights,
        "candidates": scored,
        "chosen": top["tool"],
        "runner_up": runner["tool"] if runner else None,
        "separation": round(sep, 4),
        "confidence": confidence,
        "note": "Scored recommendation only. The orchestrator surfaces the top 2-3 with pros/cons and the HUMAN approves or overrides. Free-first: prefer the $0 option when scores are within one separation band.",
    }

    out_path = None
    if args.output:
        out_path = Path(args.output)
    elif brief.get("brief_id"):
        out_path = JOBS_ROOT / brief["brief_id"] / "decisions.json"
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(decisions, indent=2), encoding="utf-8")

    # print table
    print(f"select_tool: {source_type or 'no-source'} / {intent or 'no-intent'} / x{count}")
    print(f"{'rank':<5}{'tool':<24}{'score':<8}{'est$':<7}{'rationale'}")
    for i, srow in enumerate(scored, 1):
        if "error" in srow:
            print(f"{i:<5}{srow['tool']:<24}{'--':<8}{'--':<7}{srow['error']}")
            continue
        print(f"{i:<5}{srow['tool']:<24}{srow['score']:<8.3f}{srow['est_cost_usd']:<7}{srow['rationale']}")
    print(f"\nchosen: {top['tool']}  (runner-up: {decisions['runner_up']}, sep {decisions['separation']}, confidence {confidence})")
    if out_path:
        print(f"decisions: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
