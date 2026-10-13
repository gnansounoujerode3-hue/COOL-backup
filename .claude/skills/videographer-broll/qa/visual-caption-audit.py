"""Visual caption audit gate (Sonnet vision spot-check).

Samples N frames from the output, sends them to Claude Sonnet 4.6 with a
structured prompt, parses the response into a verdict + remediation block.

Catches the four failure modes that bbox math + transcript parsing miss:
  1. Pill SHAPE: rounded vs rectangular vs raw text. Spec says rounded;
     libass rectangles violate the brand and a bbox check can't tell the
     difference.
  2. Mouth coverage: a face-bbox-vs-caption-bbox check passes if they
     don't overlap, but pills riding the chin still feel covered to a
     viewer. Vision catches the soft case.
  3. Filler text in captions: "um", "uh" appearing as burned-in text.
     Vision reads the captions directly.
  4. Cut bridging: captions that span a visible cut/scene change.
     Hard for math (would need EDL + caption manifest); easy for vision.

Usage:
  python visual-caption-audit.py --brief <id> --video <out.mp4> --output <audit.json>

Cost: ~$0.05 per call (10 frames at sonnet rates).
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (Path(__file__).resolve().parent.parent / "VideoJobs"))

MODEL = "claude-sonnet-4-6"
N_FRAMES = 10
PROMPT = """You are auditing burned-in captions on a vertical (9:16) social-media video.
The brand spec requires:
  1. Captions must be PILL-shaped (rounded ends, border-radius >= half height). Rectangular boxes are NOT acceptable.
  2. Captions must NOT cover the speaker's mouth area.
  3. Captions must NOT contain filler words: um, uh, ah, er, hmm, mm.
  4. Captions must reset cleanly across cuts/scene changes (no caption text appearing on the wrong shot).

I will give you ${N} sample frames from the video at evenly-spaced timestamps.
For each issue, judge across all frames and return a single verdict.

Return STRICT JSON in exactly this shape:
{
  "shape_verdict": "PASS" | "WARN" | "FAIL",
  "shape_evidence": "<one sentence>",
  "mouth_verdict": "PASS" | "WARN" | "FAIL",
  "mouth_evidence": "<one sentence>",
  "fillers_verdict": "PASS" | "WARN" | "FAIL",
  "fillers_evidence": "<one sentence: list any filler words you saw>",
  "cuts_verdict": "PASS" | "WARN" | "FAIL",
  "cuts_evidence": "<one sentence: did captions appear on a wrong/mismatched shot?>",
  "overall_verdict": "PASS" | "WARN" | "FAIL",
  "overall_summary": "<one paragraph>"
}

Verdict bands:
  PASS = no issues observed
  WARN = minor or borderline issues (e.g. one frame slightly clips the chin)
  FAIL = clear violation in multiple frames

Output ONLY the JSON object, no preamble or markdown fences."""


def die(msg: str, code: int = 2) -> None:
    print(f"visual-caption-audit: {msg}", file=sys.stderr)
    sys.exit(code)


def video_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def extract_frames(video: Path, n: int, dest_dir: Path) -> list[Path]:
    """Extract n evenly-spaced frames as PNG. Skips first 1.5s (intro card)
    and last 0.5s (likely freeze/black) to focus on body content."""
    duration = video_duration(video)
    start = 1.5  # skip intro card if present
    end = max(start + 1.0, duration - 0.5)
    timestamps = [start + (end - start) * i / max(1, n - 1) for i in range(n)]
    paths = []
    for i, t in enumerate(timestamps):
        out = dest_dir / f"frame_{i:02d}.png"
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{t:.3f}", "-i", str(video),
            "-frames:v", "1",
            "-vf", "scale=540:-1",  # downsample to keep payload small
            str(out),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        paths.append(out)
    return paths


def call_vision(frames: list[Path]) -> dict[str, Any]:
    try:
        import anthropic
    except ImportError:
        die("missing dep: anthropic. install with: uv pip install anthropic", 2)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        die("ANTHROPIC_API_KEY not set in environment", 2)

    client = anthropic.Anthropic(api_key=api_key)
    content: list[dict[str, Any]] = [{"type": "text", "text": PROMPT.replace("${N}", str(len(frames)))}]
    for fp in frames:
        b64 = base64.b64encode(fp.read_bytes()).decode("ascii")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })

    msg = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    # Strip optional ```json fences
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        die(f"vision returned non-JSON: {exc}; response was:\n{text[:500]}", 2)
        return {}


def compute_remediation(audit: dict[str, Any]) -> dict[str, Any] | None:
    """Translate the vision verdicts into a single actionable remediation."""
    fixes: list[dict[str, Any]] = []
    if audit.get("shape_verdict") == "FAIL":
        fixes.append({
            "action": "swap_to_png_overlay_pills",
            "reason": audit.get("shape_evidence", "captions appear rectangular not pill-shaped"),
            "ref_impl": "C:/Users/raviv/VideoJobs/2026-04-26-walking-topics-edit/merged/rebuild_captions.py",
        })
    if audit.get("mouth_verdict") in ("WARN", "FAIL"):
        fixes.append({
            "action": "lower_caption_position",
            "reason": audit.get("mouth_evidence", "captions cover speaker's mouth"),
            "suggested_margin_bottom_pct": 6.0,
            "suggested_margin_bottom_px_at_1920h": 80,
        })
    if audit.get("fillers_verdict") in ("WARN", "FAIL"):
        fixes.append({
            "action": "filter_filler_words_from_caption_text",
            "reason": audit.get("fillers_evidence", "filler words visible in captions"),
            "filter_set": ["um", "uh", "ah", "er", "hmm", "mm", "umm", "uhh", "ehh", "uhm"],
        })
    if audit.get("cuts_verdict") in ("WARN", "FAIL"):
        fixes.append({
            "action": "make_captions_cut_aware",
            "reason": audit.get("cuts_evidence", "captions span across cut boundaries"),
            "rule": "iterate EDL ranges separately, restart phrase pointer at each boundary, compute cut-local timestamps",
        })
    if not fixes:
        return None
    return {"fixes": fixes, "summary": audit.get("overall_summary", "")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual caption audit gate")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--n-frames", type=int, default=N_FRAMES)
    args = parser.parse_args()

    brief_path = JOBS_ROOT / args.brief / "brief.json"
    if not brief_path.is_file():
        die(f"brief not found: {brief_path}", 2)
    video_path = Path(args.video)
    if not video_path.is_file():
        die(f"video not found: {video_path}", 2)

    tmp_dir = Path(tempfile.mkdtemp(prefix="visual-caption-audit-"))
    try:
        frames = extract_frames(video_path, args.n_frames, tmp_dir)
        audit = call_vision(frames)
        remediation = compute_remediation(audit)
        verdict = audit.get("overall_verdict", "FAIL")
        report = {
            "video": str(video_path),
            "model": MODEL,
            "n_frames_sampled": len(frames),
            "audit": audit,
            "verdict": verdict,
            "remediation": remediation,
        }
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if verdict == "PASS":
            return 0
        if verdict == "WARN":
            return 1
        return 2
    finally:
        for p in tmp_dir.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass
        try:
            tmp_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
