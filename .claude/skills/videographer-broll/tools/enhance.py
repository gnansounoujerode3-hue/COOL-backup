"""Enhancement / finishing pass for video-orchestrator (C2).

Optional polish: upscale, background-remove, face-restore. Local + free first.
Everything has an FFmpeg fallback so the baseline always runs with zero extra
deps; the higher-quality engines activate only if their tool is installed.

  upscale      : 2x/4x. Engine 'realesrgan' if realesrgan-ncnn-vulkan is on PATH,
                 else FFmpeg lanczos (always works, no deps). Image or video.
  bg-remove    : image background removal via `rembg` (pip install rembg). For video,
                 prefer a chroma key or a dedicated matting tool - documented, not forced.
  face-restore : via GFPGAN (pip install gfpgan) if available; else prints the install
                 path. No silent FFmpeg fake (FFmpeg cannot restore faces).

This spends $0 - all engines are local.

Usage:
  python enhance.py upscale      --in frame.png --scale 2 --out frame_2x.png
  python enhance.py upscale      --in clip.mp4  --scale 2 --engine realesrgan --out clip_2x.mp4
  python enhance.py bg-remove    --in portrait.png --out cutout.png
  python enhance.py face-restore --in face.png --out face_restored.png

Exit codes: 0 ok, 2 error, 3 optional engine not installed (with install hint).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def err(msg: str, code: int = 2) -> None:
    print(f"enhance: {msg}", file=sys.stderr)
    sys.exit(code)


def is_image(p: Path) -> bool:
    return p.suffix.lower() in IMAGE_EXTS


def ffprobe_dims(p: Path) -> tuple[int, int] | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(p)],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        w, h = out.split("x")[:2]
        return int(w), int(h)
    except Exception:  # noqa: BLE001
        return None


def upscale(inp: Path, out: Path, scale: int, engine: str) -> int:
    if not inp.is_file():
        err(f"input not found: {inp}")
    out.parent.mkdir(parents=True, exist_ok=True)
    before = ffprobe_dims(inp)

    if engine == "realesrgan" and shutil.which("realesrgan-ncnn-vulkan"):
        cmd = ["realesrgan-ncnn-vulkan", "-i", str(inp), "-o", str(out), "-s", str(scale)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"enhance upscale: realesrgan {scale}x -> {out}")
        except subprocess.CalledProcessError as exc:
            err(f"realesrgan failed: {exc.stderr or exc}")
    else:
        if engine == "realesrgan":
            print("enhance: realesrgan-ncnn-vulkan not on PATH; falling back to FFmpeg lanczos", file=sys.stderr)
        vf = f"scale=iw*{scale}:ih*{scale}:flags=lanczos"
        if is_image(inp):
            cmd = ["ffmpeg", "-y", "-i", str(inp), "-vf", vf, str(out)]
        else:
            cmd = ["ffmpeg", "-y", "-i", str(inp), "-vf", vf, "-c:a", "copy", str(out)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"enhance upscale: ffmpeg lanczos {scale}x -> {out}")
        except subprocess.CalledProcessError as exc:
            err(f"ffmpeg upscale failed: {(exc.stderr or '')[-300:]}")

    after = ffprobe_dims(out)
    if before and after:
        print(f"  {before[0]}x{before[1]} -> {after[0]}x{after[1]}")
    if not out.is_file():
        err("upscale produced no output")
    return 0


def bg_remove(inp: Path, out: Path) -> int:
    if not inp.is_file():
        err(f"input not found: {inp}")
    if not is_image(inp):
        err("bg-remove handles still images. For video, use a chroma key or a matting "
            "tool (e.g. backgroundremover / RVM) - see adapters/enhance.md.")
    try:
        from rembg import remove  # type: ignore
    except Exception:
        print("enhance: bg-remove needs `rembg` (local, free). Install:", file=sys.stderr)
        print("  pip install rembg onnxruntime", file=sys.stderr)
        sys.exit(3)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(remove(inp.read_bytes()))
    print(f"enhance bg-remove: rembg -> {out}")
    return 0


def face_restore(inp: Path, out: Path) -> int:
    if not inp.is_file():
        err(f"input not found: {inp}")
    try:
        import gfpgan  # type: ignore  # noqa: F401
    except Exception:
        print("enhance: face-restore needs GFPGAN (local, free). Install:", file=sys.stderr)
        print("  pip install gfpgan basicsr", file=sys.stderr)
        print("  (FFmpeg cannot restore faces - no fake fallback is offered.)", file=sys.stderr)
        sys.exit(3)
    # Minimal GFPGAN invocation; model auto-downloads on first run.
    from gfpgan import GFPGANer  # type: ignore
    import cv2  # type: ignore

    restorer = GFPGANer(model_path=None, upscale=2, arch="clean", channel_multiplier=2)
    img = cv2.imread(str(inp), cv2.IMREAD_COLOR)
    _, _, restored = restorer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), restored)
    print(f"enhance face-restore: GFPGAN -> {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Enhancement / finishing pass")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pu = sub.add_parser("upscale")
    pu.add_argument("--in", dest="inp", required=True)
    pu.add_argument("--out", required=True)
    pu.add_argument("--scale", type=int, default=2, choices=[2, 3, 4])
    pu.add_argument("--engine", default="ffmpeg", choices=["ffmpeg", "realesrgan"])

    pb = sub.add_parser("bg-remove")
    pb.add_argument("--in", dest="inp", required=True)
    pb.add_argument("--out", required=True)

    pf = sub.add_parser("face-restore")
    pf.add_argument("--in", dest="inp", required=True)
    pf.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "upscale":
        return upscale(Path(args.inp), Path(args.out), args.scale, args.engine)
    if args.cmd == "bg-remove":
        return bg_remove(Path(args.inp), Path(args.out))
    if args.cmd == "face-restore":
        return face_restore(Path(args.inp), Path(args.out))
    return 2


if __name__ == "__main__":
    sys.exit(main())
