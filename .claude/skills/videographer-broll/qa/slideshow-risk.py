"""Slideshow-risk PRE-COMPOSE gate for video-orchestrator.

Scores a scene_plan (NOT a rendered video) on 6 dimensions that predict a
boring, static "slideshow" result, BEFORE any render spend happens:

  1. repetition                  - same subject / environment / camera repeated
  2. decorative_visuals          - shots that look nice but don't advance meaning
  3. weak_motion                 - stills / static cameras with no movement
  4. shot_intent                 - shots with no clear action or subject
  5. typography_overreliance     - meaning carried by on-screen text, not visuals
  6. unsupported_cinematic_claims- "epic / cinematic" language not backed by craft

Each dimension -> a 0..1 risk. Weighted sum -> overall risk -> verdict.

Mode (default = soft, per project decision "warn & confirm"):
  soft : PASS (<0.34) or WARN (>=0.34). NEVER FAIL-blocks. High risk is reported
         as WARN with recommendation="rework strongly advised". The orchestrator
         surfaces it and asks the human to confirm or rework.
  hard : adds FAIL (>=0.67) which blocks the render (exit 2).

Input: a scene_plan JSON ({shots:[...]}, schema at schemas/scene-plan.schema.json)
       via --scene-plan PATH, or --brief <brief_id> (reads the job's scene_plan.json,
       falling back to brief.json's embedded scene_plan).

Usage:
  python slideshow-risk.py --scene-plan plan.json --output risk.json [--mode soft|hard]
  python slideshow-risk.py --brief 2026-06-30-acme-explainer --output risk.json

Exit codes: 0 PASS, 1 WARN, 2 FAIL (hard mode only) or fatal error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (Path(__file__).resolve().parent.parent / "VideoJobs"))

WARN_AT = 0.34
FAIL_AT = 0.67

WEIGHTS = {
    "repetition": 0.22,
    "weak_motion": 0.22,
    "decorative_visuals": 0.16,
    "shot_intent": 0.16,
    "typography_overreliance": 0.14,
    "unsupported_cinematic_claims": 0.10,
}

STILL_KINDS = {"image", "title_card", "data_viz"}
MOTION_MOVES = {"pan", "tilt", "push-in", "pull-out", "dolly", "handheld", "orbit", "ken-burns", "crane", "whip", "zoom", "track", "truck"}
STATIC_MOVES = {"", "static", "none", "hold", "locked", "still", "fixed"}
VAGUE_ACTIONS = {"", "n/a", "none", "abstract", "various", "misc", "tbd", "-", "shows", "appears", "displayed", "displays"}
DECOR_TERMS = {"abstract", "background", "gradient", "bokeh", "particles", "texture", "overlay", "pattern", "wallpaper", "ambient", "aesthetic", "vibe", "mood"}
CLAIM_TERMS = {"cinematic", "epic", "dramatic", "breathtaking", "sweeping", "stunning", "beautiful", "gorgeous", "masterpiece", "award-winning", "emotional", "powerful", "majestic", "spectacular", "jaw-dropping", "mesmerizing"}


def die(msg: str, code: int = 2) -> None:
    print(f"slideshow-risk: {msg}", file=sys.stderr)
    sys.exit(code)


def s(shot: dict[str, Any], key: str) -> str:
    return str(shot.get(key, "") or "").strip().lower()


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9-]+", text.lower())


# --------------------------------------------------------------------------- #
# dimension scorers -> (risk 0..1, flagged_ids, note)
# --------------------------------------------------------------------------- #
def dim_repetition(shots: list[dict[str, Any]]) -> tuple[float, list[Any], str]:
    n = len(shots)
    if n <= 1:
        return 0.0, [], "single shot - n/a"
    keys = ("subject", "environment", "camera_move")
    risks = []
    flagged: set[Any] = set()
    for k in keys:
        vals = [s(sh, k) for sh in shots]
        nonempty = [v for v in vals if v]
        distinct = len(set(nonempty))
        ratio = (1 - distinct / len(nonempty)) if nonempty else 0.0
        risks.append(ratio)
    # consecutive-duplicate bump: back-to-back identical subject+environment
    consec = 0
    for i in range(1, n):
        if s(shots[i], "subject") and s(shots[i], "subject") == s(shots[i - 1], "subject") and \
           s(shots[i], "environment") == s(shots[i - 1], "environment"):
            consec += 1
            flagged.add(shots[i].get("id", i))
    consec_risk = consec / (n - 1)
    risk = min(1.0, 0.7 * (sum(risks) / len(risks)) + 0.3 * consec_risk)
    return round(risk, 3), sorted(flagged, key=str), f"{consec} back-to-back same subject+environment"


def dim_decorative(shots: list[dict[str, Any]]) -> tuple[float, list[Any], str]:
    flagged = []
    for i, sh in enumerate(shots):
        action = s(sh, "action")
        env_words = set(words(s(sh, "environment"))) | set(words(s(sh, "subject")))
        decorative = (
            (action in VAGUE_ACTIONS and bool(env_words & DECOR_TERMS))
            or (not action and not s(sh, "subject"))
            or (bool(env_words & DECOR_TERMS) and not s(sh, "narration") and not s(sh, "action"))
        )
        if decorative:
            flagged.append(sh.get("id", i))
    risk = len(flagged) / len(shots) if shots else 0.0
    return round(risk, 3), flagged, f"{len(flagged)}/{len(shots)} shots are decorative filler"


def dim_weak_motion(shots: list[dict[str, Any]]) -> tuple[float, list[Any], str]:
    flagged = []
    for i, sh in enumerate(shots):
        move = s(sh, "camera_move")
        kind = s(sh, "asset_kind")
        has_motion = move in MOTION_MOVES or any(m in move for m in MOTION_MOVES)
        still_asset = kind in STILL_KINDS
        weak = (still_asset and not has_motion) or (move in STATIC_MOVES and not has_motion)
        if weak:
            flagged.append(sh.get("id", i))
    risk = len(flagged) / len(shots) if shots else 0.0
    return round(risk, 3), flagged, f"{len(flagged)}/{len(shots)} shots are still / static with no camera move"


def dim_shot_intent(shots: list[dict[str, Any]]) -> tuple[float, list[Any], str]:
    flagged = []
    for i, sh in enumerate(shots):
        action = s(sh, "action")
        subject = s(sh, "subject")
        vague = action in VAGUE_ACTIONS or len(words(action)) < 2
        no_subject = not subject
        # a strong narration line can carry intent even with a thin action
        rescued = bool(s(sh, "narration")) and not no_subject
        if (vague or no_subject) and not rescued:
            flagged.append(sh.get("id", i))
    risk = len(flagged) / len(shots) if shots else 0.0
    return round(risk, 3), flagged, f"{len(flagged)}/{len(shots)} shots lack a clear action or subject"


def dim_typography(shots: list[dict[str, Any]]) -> tuple[float, list[Any], str]:
    flagged = []
    for i, sh in enumerate(shots):
        kind = s(sh, "asset_kind")
        has_text = bool(s(sh, "on_screen_text"))
        weak_visual = (kind in {"title_card"}) or (
            has_text and s(sh, "action") in VAGUE_ACTIONS and not s(sh, "subject")
        )
        if weak_visual:
            flagged.append(sh.get("id", i))
    risk = len(flagged) / len(shots) if shots else 0.0
    return round(risk, 3), flagged, f"{len(flagged)}/{len(shots)} shots lean on on-screen text instead of visuals"


def dim_claims(shots: list[dict[str, Any]]) -> tuple[float, list[Any], str]:
    flagged = []
    for i, sh in enumerate(shots):
        blob = " ".join(s(sh, k) for k in ("subject", "action", "environment", "lighting", "audio"))
        toks = set(words(blob))
        makes_claim = bool(toks & CLAIM_TERMS)
        move = s(sh, "camera_move")
        backed = (move in MOTION_MOVES or any(m in move for m in MOTION_MOVES)) and bool(s(sh, "lighting"))
        if makes_claim and not backed:
            flagged.append(sh.get("id", i))
    risk = len(flagged) / len(shots) if shots else 0.0
    return round(risk, 3), flagged, f"{len(flagged)}/{len(shots)} shots claim 'epic/cinematic' without a camera move + lighting to back it"


DIMS = {
    "repetition": dim_repetition,
    "decorative_visuals": dim_decorative,
    "weak_motion": dim_weak_motion,
    "shot_intent": dim_shot_intent,
    "typography_overreliance": dim_typography,
    "unsupported_cinematic_claims": dim_claims,
}


def load_scene_plan(args) -> dict[str, Any]:
    if args.scene_plan:
        p = Path(args.scene_plan)
        if not p.is_file():
            die(f"scene plan not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))
    if args.brief:
        job = JOBS_ROOT / args.brief
        sp = job / "scene_plan.json"
        if sp.is_file():
            return json.loads(sp.read_text(encoding="utf-8"))
        bp = job / "brief.json"
        if bp.is_file():
            brief = json.loads(bp.read_text(encoding="utf-8"))
            if isinstance(brief.get("scene_plan"), dict):
                return brief["scene_plan"]
        die(f"no scene_plan.json or embedded scene_plan for brief {args.brief}")
    die("provide --scene-plan PATH or --brief <brief_id>")
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Slideshow-risk pre-compose gate")
    ap.add_argument("--scene-plan", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--output", required=True)
    ap.add_argument("--mode", choices=["soft", "hard"], default="soft")
    args = ap.parse_args()

    plan = load_scene_plan(args)
    shots = plan.get("shots") or []
    if not isinstance(shots, list) or not shots:
        die("scene plan has no shots[]")

    dims: dict[str, Any] = {}
    overall = 0.0
    remediation: list[str] = []
    for name, fn in DIMS.items():
        risk, flagged, note = fn(shots)
        w = WEIGHTS[name]
        overall += w * risk
        dims[name] = {"risk": risk, "weight": w, "weighted": round(w * risk, 4), "flagged_shots": flagged, "note": note}
        if risk >= 0.5:
            remediation.append(f"{name} (risk {risk}): {note}. Shots: {flagged}")

    overall = round(overall, 3)
    if overall < WARN_AT:
        severity = "low"
        verdict = "PASS"
    elif overall < FAIL_AT:
        severity = "medium"
        verdict = "WARN"
    else:
        severity = "high"
        verdict = "FAIL" if args.mode == "hard" else "WARN"

    if severity == "high":
        recommendation = "rework strongly advised before render"
    elif severity == "medium":
        recommendation = "review flagged shots; add motion / vary shots, then confirm to proceed"
    else:
        recommendation = "ok to compose"

    report = {
        "n_shots": len(shots),
        "mode": args.mode,
        "overall_risk": overall,
        "severity": severity,
        "verdict": verdict,
        "thresholds": {"warn_at": WARN_AT, "fail_at": FAIL_AT},
        "dimensions": dims,
        "remediation": remediation,
        "recommendation": recommendation,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"slideshow-risk: overall={overall} severity={severity} verdict={verdict} (mode={args.mode})")
    for name, d in sorted(dims.items(), key=lambda kv: kv[1]["weighted"], reverse=True):
        bar = "#" * int(round(d["risk"] * 20))
        print(f"  {name:30s} {d['risk']:.2f} |{bar:<20}| {d['note']}")
    print(f"  -> {recommendation}")
    print(f"  report: {out}")

    if verdict == "PASS":
        return 0
    if verdict == "WARN":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
