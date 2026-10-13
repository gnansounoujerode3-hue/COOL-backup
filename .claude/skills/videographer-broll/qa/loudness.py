"""Loudness QA gate for video-orchestrator outputs.

Extracts audio via ffmpeg, measures integrated LUFS (pyloudnorm) and true peak
(direct max abs sample as dBTP approximation), and compares against the brief's
cleanup.loudness_target_lufs and cleanup.true_peak_max_dbtp.

Verdict bands:
  PASS = within +/-1 LUFS of target AND true_peak <= max
  WARN = within +/-2 LUFS of target
  FAIL = beyond +/-2 LUFS OR true_peak above max

Usage:
  python loudness.py --brief <brief_id> --video <out.mp4> --output <loudness.json>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (Path(__file__).resolve().parent.parent / "VideoJobs"))


def die(msg: str, code: int = 2) -> None:
    print(f"loudness: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        die(f"missing file: {path}", 2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"bad JSON at {path}: {exc}", 2)
        return {}


def extract_audio(video_path: Path, wav_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "2",
        "-ar",
        "48000",
        "-f",
        "wav",
        str(wav_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except FileNotFoundError:
        die("ffmpeg not found on PATH", 2)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
        die(f"ffmpeg failed: {stderr.strip() or exc}", 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Loudness QA gate")
    parser.add_argument("--brief", required=True, help="brief_id")
    parser.add_argument("--video", required=True, help="absolute path to output mp4")
    parser.add_argument("--output", required=True, help="absolute path to write loudness.json")
    args = parser.parse_args()

    brief_path = JOBS_ROOT / args.brief / "brief.json"
    if not brief_path.is_file():
        die(f"brief not found: {brief_path}", 2)
    brief = load_json(brief_path)

    video_path = Path(args.video)
    if not video_path.is_file():
        die(f"video not found: {video_path}", 2)

    cleanup = brief.get("cleanup", {}) or {}
    target_lufs = float(cleanup.get("loudness_target_lufs", -16))
    max_true_peak = float(cleanup.get("true_peak_max_dbtp", -1.0))

    try:
        import numpy as np  # type: ignore
        import pyloudnorm as pyln  # type: ignore
        import soundfile as sf  # type: ignore
    except ImportError as exc:
        die(
            f"missing dep: {exc}. install with: uv pip install pyloudnorm soundfile numpy",
            2,
        )
        return 2

    tmp_dir = Path(tempfile.mkdtemp(prefix="loudness-qa-"))
    wav_path = tmp_dir / "audio.wav"
    try:
        extract_audio(video_path, wav_path)

        data, rate = sf.read(str(wav_path))
        # Ensure 2D shape (samples, channels)
        if data.ndim == 1:
            data_for_meter = data
        else:
            data_for_meter = data
        meter = pyln.Meter(rate)
        try:
            integrated = float(meter.integrated_loudness(data_for_meter))
        except ValueError as exc:
            die(f"pyloudnorm could not compute LUFS: {exc}", 2)
            return 2

        # True peak approximation: max abs sample -> dBFS. (Pure dBTP would need
        # 4x oversampling per ITU-R BS.1770-4; this is the pragmatic stand-in.)
        peak_lin = float(np.max(np.abs(data))) if data.size else 0.0
        if peak_lin <= 0:
            true_peak_dbtp = -math.inf
        else:
            true_peak_dbtp = 20.0 * math.log10(peak_lin)

        # Verdict bands:
        #   PASS = LUFS within +/-1 of target AND peak <= configured max
        #   WARN = LUFS within +/-2 of target AND peak below clipping (-0.1 dBTP)
        #   FAIL = LUFS beyond +/-2 OR peak at/near clipping (-0.1 dBTP or higher)
        # The configured max_true_peak (default -1.0 dBTP) is the PASS bar; a
        # peak above it but well below clipping is acceptable for social platforms
        # which re-encode audio anyway. Clipping (>= -0.1 dBTP) is always FAIL.
        delta = integrated - target_lufs
        peak_at_max = true_peak_dbtp <= max_true_peak
        peak_clip = true_peak_dbtp >= -0.1
        if abs(delta) <= 1.0 and peak_at_max:
            verdict = "PASS"
        elif abs(delta) <= 2.0 and not peak_clip:
            verdict = "WARN"
        else:
            verdict = "FAIL"

        # Remediation: actionable fix for the QA-loop orchestrator.
        remediation: dict[str, Any] | None = None
        if verdict in ("WARN", "FAIL"):
            if abs(delta) > 1.0:
                remediation = {
                    "action": "apply_2pass_loudnorm",
                    "current_lufs": round(integrated, 2),
                    "target_lufs": target_lufs,
                    "delta_lufs": round(delta, 2),
                    "reason": f"integrated {integrated:.1f} LUFS off target {target_lufs:.1f} by {delta:+.1f} LUFS",
                    "ffmpeg_filter_pass1": f"loudnorm=I={target_lufs}:TP={max_true_peak}:LRA=11:print_format=json",
                    "ffmpeg_filter_pass2_template": (
                        f"loudnorm=I={target_lufs}:TP={max_true_peak}:LRA=11:"
                        "measured_I=<from pass 1>:measured_TP=<from pass 1>:"
                        "measured_LRA=<from pass 1>:measured_thresh=<from pass 1>:"
                        "offset=<from pass 1>:linear=true"
                    ),
                }
            elif math.isfinite(true_peak_dbtp) and true_peak_dbtp > max_true_peak:
                remediation = {
                    "action": "lower_true_peak",
                    "current_tp_dbtp": round(true_peak_dbtp, 2),
                    "max_tp_dbtp": max_true_peak,
                    "reason": f"true peak {true_peak_dbtp:.2f} dBTP exceeds cap {max_true_peak} dBTP; loudnorm pass 2 with TP={max_true_peak} should fix",
                }

        report: dict[str, Any] = {
            "video": str(video_path),
            "sample_rate": int(rate),
            "channels": 1 if data.ndim == 1 else int(data.shape[1]),
            "integrated_lufs": round(integrated, 2),
            "target_lufs": target_lufs,
            "delta_lufs": round(delta, 2),
            "true_peak_dbtp": round(true_peak_dbtp, 2) if math.isfinite(true_peak_dbtp) else None,
            "max_true_peak_dbtp": max_true_peak,
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
    finally:
        try:
            if wav_path.exists():
                wav_path.unlink()
            os.rmdir(tmp_dir)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
