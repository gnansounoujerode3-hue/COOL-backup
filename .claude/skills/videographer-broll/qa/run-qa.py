"""Run all QA gates (face-safety, loudness, timing) over every output in a job.

Walks <VideoJobs>/<brief_id>/<tool>/ for each tool listed in the brief, runs
the three gates against every out_*.mp4 found, and aggregates results into
per-output <tool>/out_NN.qa.json files plus a top-level QA.json summary.

Exit codes:
  0 = all PASS
  1 = at least one WARN, no FAIL
  2 = at least one FAIL or a fatal error (missing brief, missing scripts)

Usage:
  python run-qa.py <brief_id>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

QA_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = QA_ROOT.parent
JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (SKILL_ROOT / "VideoJobs"))

GATE_SCRIPTS = {
    "face_safety": QA_ROOT / "face-safety.py",
    "loudness": QA_ROOT / "loudness.py",
    "timing": QA_ROOT / "timing.py",
}

VERDICT_RANK = {"PASS": 0, "WARN": 1, "FAIL": 2}


def die(msg: str, code: int = 2) -> None:
    print(f"run-qa: {msg}", file=sys.stderr)
    sys.exit(code)


def worst(verdicts: list[str]) -> str:
    if not verdicts:
        return "PASS"
    return max(verdicts, key=lambda v: VERDICT_RANK.get(v, 2))


def run_gate(script: Path, brief_id: str, video: Path, gate_output: Path) -> dict[str, Any]:
    if not script.is_file():
        return {"verdict": "FAIL", "error": f"gate script missing: {script}"}
    cmd = [
        sys.executable,
        str(script),
        "--brief",
        brief_id,
        "--video",
        str(video),
        "--output",
        str(gate_output),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        return {"verdict": "FAIL", "error": f"could not exec gate: {exc}"}
    if not gate_output.is_file():
        return {"verdict": "FAIL", "error": f"gate produced no output: {gate_output}"}
    try:
        return json.loads(gate_output.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"verdict": "FAIL", "error": f"gate output not JSON: {exc}"}


def fmt_duration(sec: float | None) -> str:
    if sec is None:
        return "-"
    sec_int = int(round(sec))
    return f"{sec_int // 60}:{sec_int % 60:02d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all QA gates over a video-orchestrator job")
    parser.add_argument("brief_id", help=f"brief_id directory under {JOBS_ROOT}")
    args = parser.parse_args()

    job_dir = JOBS_ROOT / args.brief_id
    brief_path = job_dir / "brief.json"
    if not brief_path.is_file():
        die(f"brief not found: {brief_path}", 2)

    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"bad brief JSON: {exc}", 2)
        return 2

    tools: list[str] = list(brief.get("tools", []) or [])
    gates: list[str] = list(brief.get("qa_gates", ["face_safety", "loudness", "timing"]))
    if not tools:
        die("brief has no tools[]; nothing to QA", 2)

    summary: dict[str, Any] = {
        "brief_id": args.brief_id,
        "tools": [],
        "overall_verdict": "PASS",
    }
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    all_verdicts: list[str] = []

    for tool in tools:
        tool_dir = job_dir / tool
        if not tool_dir.is_dir():
            tool_entry = {"tool": tool, "outputs": [], "note": "tool dir missing"}
            summary["tools"].append(tool_entry)
            rows.append((tool, "-", "-", "-", "-", "-", "MISSING"))
            all_verdicts.append("FAIL")
            continue

        outputs = sorted(tool_dir.glob("out_*.mp4"))
        if not outputs:
            tool_entry = {"tool": tool, "outputs": [], "note": "no out_*.mp4 found"}
            summary["tools"].append(tool_entry)
            rows.append((tool, "-", "-", "-", "-", "-", "MISSING"))
            all_verdicts.append("FAIL")
            continue

        tool_outputs: list[dict[str, Any]] = []
        for video in outputs:
            stem = video.stem
            per_output_qa = tool_dir / f"{stem}.qa.json"
            gate_results: dict[str, Any] = {}
            verdicts: list[str] = []
            for gate in gates:
                if gate not in GATE_SCRIPTS:
                    gate_results[gate] = {"verdict": "FAIL", "error": f"unknown gate: {gate}"}
                    verdicts.append("FAIL")
                    continue
                gate_output = tool_dir / f"{stem}.{gate}.json"
                result = run_gate(GATE_SCRIPTS[gate], args.brief_id, video, gate_output)
                gate_results[gate] = result
                verdicts.append(str(result.get("verdict", "FAIL")))

            overall = worst(verdicts)
            all_verdicts.append(overall)

            duration = gate_results.get("timing", {}).get("actual_duration_sec")
            lufs = gate_results.get("loudness", {}).get("integrated_lufs")
            face_verdict = gate_results.get("face_safety", {}).get("verdict", "-")

            entry: dict[str, Any] = {
                "video": str(video),
                "duration_sec": duration,
                "integrated_lufs": lufs,
                "true_peak_dbtp": gate_results.get("loudness", {}).get("true_peak_dbtp"),
                "face_safety": face_verdict,
                "loudness": gate_results.get("loudness", {}).get("verdict", "-"),
                "timing": gate_results.get("timing", {}).get("verdict", "-"),
                "overall": overall,
                "gate_files": {
                    gate: str(tool_dir / f"{stem}.{gate}.json")
                    for gate in gates
                    if gate in GATE_SCRIPTS
                },
            }
            with per_output_qa.open("w", encoding="utf-8") as fh:
                json.dump(entry, fh, indent=2)
            tool_outputs.append(entry)

            rows.append(
                (
                    tool,
                    video.name,
                    fmt_duration(duration if isinstance(duration, (int, float)) else None),
                    f"{lufs:.1f}" if isinstance(lufs, (int, float)) else "-",
                    face_verdict,
                    gate_results.get("loudness", {}).get("verdict", "-"),
                    overall,
                )
            )

        summary["tools"].append({"tool": tool, "outputs": tool_outputs})

    summary["overall_verdict"] = worst(all_verdicts) if all_verdicts else "FAIL"

    qa_path = job_dir / "QA.json"
    with qa_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    # Print summary table
    headers = ("tool", "output", "duration", "LUFS", "face", "loud", "overall")
    widths = [
        max(len(headers[i]), max((len(r[i]) for r in rows), default=0))
        for i in range(len(headers))
    ]
    fmt = " | ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))
    print()
    print(f"overall: {summary['overall_verdict']}")
    print(f"summary: {qa_path}")

    if summary["overall_verdict"] == "PASS":
        return 0
    if summary["overall_verdict"] == "WARN":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
