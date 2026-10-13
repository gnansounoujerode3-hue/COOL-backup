"""Timing QA gate for video-orchestrator outputs.

Reads duration via ffprobe and compares to brief.output.length_target_sec. For
9:16 outputs, if a sibling EDL file exists at <output_dir>/<tool>/edl.json,
asserts no two adjacent cut spacings are below 0.4s.

Verdict bands:
  PASS = within +/-2s of target
  WARN = within +/-2s to +/-5s of target
  FAIL = beyond +/-5s of target OR cut spacing < 0.4s on a 9:16 output

Usage:
  python timing.py --brief <brief_id> --video <out.mp4> --output <timing.json>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (Path(__file__).resolve().parent.parent / "VideoJobs"))
MIN_CUT_SPACING_SEC = 0.4


def die(msg: str, code: int = 2) -> None:
    print(f"timing: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        die(f"missing file: {path}", 2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"bad JSON at {path}: {exc}", 2)
        return {}


def ffprobe_duration(video_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        die("ffprobe not found on PATH", 2)
        return 0.0
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        die(f"ffprobe failed: {stderr or exc}", 2)
        return 0.0
    raw = (result.stdout or "").strip()
    if not raw:
        die("ffprobe returned empty duration", 2)
    try:
        return float(raw)
    except ValueError:
        die(f"ffprobe returned non-numeric duration: {raw!r}", 2)
        return 0.0


def cut_spacings_from_edl(edl_path: Path) -> list[float]:
    """Parse common EDL shapes and return a list of segment durations.

    Tolerates a few schemas: a list of {start,end}, {in,out}, {t_start,t_end},
    or a {cuts: [...]} / {segments: [...]} envelope.
    """
    data = load_json(edl_path)
    if isinstance(data, dict):
        for key in ("cuts", "segments", "clips", "items"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        else:
            items = []
    elif isinstance(data, list):
        items = data
    else:
        items = []

    spacings: list[float] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        start = item.get("start")
        if start is None:
            start = item.get("in")
        if start is None:
            start = item.get("t_start")
        end = item.get("end")
        if end is None:
            end = item.get("out")
        if end is None:
            end = item.get("t_end")
        if start is None or end is None:
            continue
        try:
            dur = float(end) - float(start)
        except (TypeError, ValueError):
            continue
        if dur > 0:
            spacings.append(dur)
    return spacings


def main() -> int:
    parser = argparse.ArgumentParser(description="Timing QA gate")
    parser.add_argument("--brief", required=True, help="brief_id")
    parser.add_argument("--video", required=True, help="absolute path to output mp4")
    parser.add_argument("--output", required=True, help="absolute path to write timing.json")
    args = parser.parse_args()

    brief_path = JOBS_ROOT / args.brief / "brief.json"
    if not brief_path.is_file():
        die(f"brief not found: {brief_path}", 2)
    brief = load_json(brief_path)

    video_path = Path(args.video)
    if not video_path.is_file():
        die(f"video not found: {video_path}", 2)

    output_cfg = brief.get("output", {}) or {}
    target = float(output_cfg.get("length_target_sec", 60))
    aspect = str(output_cfg.get("aspect", "9:16"))
    target_source = "brief.output.length_target_sec"

    # Per-output expected duration overrides the brief default. Fork adapters
    # write a sibling qa_inputs.json listing each output's expected_duration_sec
    # so shorts and mediums can be checked against their actual targets, not a
    # single brief-level value.
    qa_inputs_path = video_path.parent / "qa_inputs.json"
    if qa_inputs_path.is_file():
        try:
            qa_inputs = json.loads(qa_inputs_path.read_text(encoding="utf-8"))
            for entry in qa_inputs.get("outputs", []):
                if entry.get("filename") == video_path.name:
                    expected = entry.get("expected_duration_sec")
                    if expected is not None:
                        target = float(expected)
                        target_source = f"qa_inputs.json[{video_path.name}]"
                    break
        except (json.JSONDecodeError, ValueError):
            pass

    actual = ffprobe_duration(video_path)
    delta = actual - target

    # Cut spacing check (only meaningful for verticals where pacing matters).
    min_spacing: float | None = None
    spacing_violations: list[float] = []
    edl_path = video_path.parent / "edl.json"
    if aspect == "9:16" and edl_path.is_file():
        spacings = cut_spacings_from_edl(edl_path)
        if spacings:
            min_spacing = min(spacings)
            spacing_violations = [s for s in spacings if s < MIN_CUT_SPACING_SEC]

    # Verdict
    duration_ok = abs(delta) <= 2.0
    duration_warn = 2.0 < abs(delta) <= 5.0
    spacing_fail = len(spacing_violations) > 0

    if duration_ok and not spacing_fail:
        verdict = "PASS"
    elif duration_warn and not spacing_fail:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    # Remediation hint for the QA-loop orchestrator.
    remediation: dict[str, Any] | None = None
    if verdict in ("WARN", "FAIL"):
        if delta > 2.0:
            remediation = {
                "action": "trim_output",
                "trim_amount_sec": round(delta, 2),
                "reason": f"actual {actual:.2f}s exceeds expected {target:.2f}s by {delta:+.2f}s; trim from longest segment or tighten cleanup",
            }
        elif delta < -2.0:
            remediation = {
                "action": "verify_expected_duration_or_extend",
                "shortfall_sec": round(abs(delta), 2),
                "reason": (
                    f"actual {actual:.2f}s shorter than expected {target:.2f}s by {abs(delta):.2f}s; "
                    "first verify qa_inputs.json expected_duration_sec is correct (often a stale theoretical EDL total vs real rendered duration); "
                    "if target was right, extend by adding back segments"
                ),
            }
        elif spacing_fail:
            remediation = {
                "action": "increase_min_cut_spacing",
                "min_spacing_sec_observed": min_spacing,
                "min_spacing_sec_required": MIN_CUT_SPACING_SEC,
                "violating_spacings": [round(s, 3) for s in spacing_violations],
                "reason": f"adjacent cut spacing < {MIN_CUT_SPACING_SEC}s on a vertical output - merge tight cuts or pad with held frames",
            }

    report: dict[str, Any] = {
        "video": str(video_path),
        "actual_duration_sec": round(actual, 3),
        "target_duration_sec": target,
        "target_source": target_source,
        "delta_sec": round(delta, 3),
        "aspect": aspect,
        "min_cut_spacing_sec": round(min_spacing, 3) if min_spacing is not None else None,
        "cut_spacing_violations": [round(s, 3) for s in spacing_violations],
        "edl_checked": str(edl_path) if (aspect == "9:16" and edl_path.is_file()) else None,
        "verdict": verdict,
        "remediation": remediation,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    if verdict == "PASS":
        return 0
    if verdict == "WARN":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
