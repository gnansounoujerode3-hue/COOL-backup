"""Face-safety QA gate for video-orchestrator outputs.

Samples the video at 4 fps, runs MediaPipe face detection on each frame, and
checks whether the brand caption rectangle (derived from
brand/captions.preset.json) intersects any detected face bounding box.

Verdict bands:
  PASS = 0 violations
  WARN = 1 to 3 violations OR violations < 5% of frames sampled
  FAIL = violations > 5% of frames sampled

Usage:
  python face-safety.py --brief <brief_id> --video <out.mp4> --output <face_safety.json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
JOBS_ROOT = Path(os.environ.get("VIDEO_JOBS_DIR") or (SKILL_ROOT / "VideoJobs"))
DEFAULT_PRESET = SKILL_ROOT / "brand" / "captions.preset.json"


def die(msg: str, code: int = 2) -> None:
    print(f"face-safety: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        die(f"missing file: {path}", 2)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"bad JSON at {path}: {exc}", 2)
        return {}  # unreachable, satisfies type checker


def rects_intersect(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    """Each rect is (x, y, w, h) in normalized 0..1 coords."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def caption_rect_norm(preset: dict[str, Any], frame_w: int, frame_h: int) -> tuple[float, float, float, float]:
    """Infer the caption pill rect in normalized coords from the preset."""
    layout = preset.get("layout", {}) or {}
    margin_bottom_pct = float(layout.get("margin_bottom_pct", 18))
    max_width_pct = float(layout.get("max_width_pct", 86))
    max_lines = int(layout.get("max_lines", 2))

    font = preset.get("font", {}) or {}
    # Pick the right size for the orientation
    if frame_h >= frame_w:
        size_px = float(font.get("size_px_at_1080h_vertical", 64))
    else:
        size_px = float(font.get("size_px_at_1080w", 56))

    pad = preset.get("padding_px", {}) or {}
    pad_v = float(pad.get("vertical", 12))

    # Estimate pill height: line-height ~1.25 of font size, plus vertical padding.
    line_h_px = size_px * 1.25
    pill_h_px = (line_h_px * max_lines) + (2.0 * pad_v)

    # Scale font/padding assumptions referenced 1080-tall vertical or 1080-wide horizontal.
    # Convert px to normalized using the actual frame height for vertical pill height.
    pill_h_norm = min(0.5, pill_h_px / float(frame_h))

    width_norm = max_width_pct / 100.0
    x_norm = (1.0 - width_norm) / 2.0
    margin_bottom_norm = margin_bottom_pct / 100.0
    y_norm = max(0.0, 1.0 - margin_bottom_norm - pill_h_norm)

    return (x_norm, y_norm, width_norm, pill_h_norm)


def main() -> int:
    parser = argparse.ArgumentParser(description="Face-safety QA gate")
    parser.add_argument("--brief", required=True, help="brief_id")
    parser.add_argument("--video", required=True, help="absolute path to output mp4")
    parser.add_argument("--output", required=True, help="absolute path to write face_safety.json")
    args = parser.parse_args()

    brief_path = JOBS_ROOT / args.brief / "brief.json"
    if not brief_path.is_file():
        die(f"brief not found: {brief_path}", 2)
    brief = load_json(brief_path)

    video_path = Path(args.video)
    if not video_path.is_file():
        die(f"video not found: {video_path}", 2)

    # Pick the preset path: brief.brand.pack may point elsewhere, but caption preset is
    # always the captions.preset.json under that pack's brand dir or the default.
    preset_path = DEFAULT_PRESET
    pack_path_str = brief.get("brand", {}).get("pack")
    if pack_path_str:
        candidate = Path(pack_path_str).parent / "captions.preset.json"
        if candidate.is_file():
            preset_path = candidate
    preset = load_json(preset_path)

    try:
        import cv2  # type: ignore
        import mediapipe as mp  # type: ignore
    except ImportError as exc:
        die(
            f"missing dep: {exc}. install with: uv pip install mediapipe opencv-python",
            2,
        )
        return 2  # unreachable

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        die(f"could not open video: {video_path}", 2)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if frame_w <= 0 or frame_h <= 0:
        cap.release()
        die("video reported zero dimensions", 2)

    sample_every_sec = 0.25  # 4 fps sampling
    sample_every_frames = max(1, int(round(fps * sample_every_sec)))

    cap_rect = caption_rect_norm(preset, frame_w, frame_h)

    violations: list[dict[str, Any]] = []
    frames_checked = 0

    mp_face = mp.solutions.face_detection
    detector = mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    try:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_every_frames != 0:
                frame_idx += 1
                continue
            frames_checked += 1
            t_sec = frame_idx / fps

            # MediaPipe expects RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = detector.process(rgb)
            detections = result.detections or []
            for det in detections:
                bbox = det.location_data.relative_bounding_box
                fx = max(0.0, float(bbox.xmin))
                fy = max(0.0, float(bbox.ymin))
                fw = max(0.0, float(bbox.width))
                fh = max(0.0, float(bbox.height))
                face_rect = (fx, fy, fw, fh)
                if rects_intersect(face_rect, cap_rect):
                    violations.append(
                        {
                            "t_sec": round(t_sec, 3),
                            "face": [round(v, 4) for v in face_rect],
                            "caption": [round(v, 4) for v in cap_rect],
                        }
                    )
            frame_idx += 1
    finally:
        detector.close()
        cap.release()

    # Verdict
    pct = (len(violations) / frames_checked) if frames_checked else 0.0
    if not violations:
        verdict = "PASS"
    elif pct > 0.05:
        verdict = "FAIL"
    elif len(violations) <= 3 or pct < 0.05:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    report: dict[str, Any] = {
        "video": str(video_path),
        "frame_w": frame_w,
        "frame_h": frame_h,
        "total_frames": total_frames,
        "fps": round(fps, 3),
        "frames_checked": frames_checked,
        "caption_rect_norm": [round(v, 4) for v in cap_rect],
        "violations": violations,
        "violations_pct": round(pct, 4),
        "verdict": verdict,
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
