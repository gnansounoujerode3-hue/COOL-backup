"""Platform render-profile resolver + applier for video-orchestrator (C4).

Resolves brief.output.render_profile (e.g. 'youtube_shorts') to concrete delivery
specs and an FFmpeg fit filter, and can apply it to a clip at the compose stage.

  resolve : print the profile's dimensions, fps, loudness, safe-margins, caption
            guidance, and the exact FFmpeg fit filter (cover-crop or contain-pad).
  apply   : run FFmpeg to conform a clip to the profile.

Fit modes:
  cover   (default) - scale to fill, crop the overflow. No bars. May cut frame edges.
  contain           - scale to fit, pad with bars. Whole frame kept. Letterboxed.

Usage:
  python apply_profile.py resolve --profile youtube_shorts
  python apply_profile.py apply   --profile youtube_shorts --in in.mp4 --out out.mp4 [--mode cover|contain]

Exit codes: 0 ok, 2 error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROFILES_PATH = SKILL_ROOT / "render-profiles.json"


def die(msg: str) -> None:
    print(f"apply_profile: {msg}", file=sys.stderr)
    sys.exit(2)


def load_profiles() -> dict[str, Any]:
    if not PROFILES_PATH.is_file():
        die(f"render-profiles.json not found: {PROFILES_PATH}")
    return json.loads(PROFILES_PATH.read_text(encoding="utf-8"))


def get_profile(doc: dict[str, Any], name: str) -> dict[str, Any]:
    prof = doc.get("profiles", {}).get(name)
    if not prof:
        die(f"unknown profile '{name}'. Available: {', '.join(doc.get('profiles', {}))}")
    return prof


def fit_filter(w: int, h: int, mode: str) -> str:
    if mode == "contain":
        return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1")
    # cover (default)
    return (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1")


def cmd_resolve(name: str, mode: str) -> int:
    doc = load_profiles()
    p = get_profile(doc, name)
    w, h, fps = p["width"], p["height"], p["fps"]
    vf = fit_filter(w, h, mode)
    sm = p["safe_margins_pct"]
    cap = p["caption"]
    print(f"profile: {name}  ({p['platform']})")
    print(f"  canvas:        {w}x{h} @ {fps}fps  ({p['aspect']})")
    print(f"  max bitrate:   {p['max_bitrate_kbps']} kbps")
    print(f"  loudness:      {p['loudness_lufs']} LUFS")
    print(f"  safe margins:  top {sm['top']}%  bottom {sm['bottom']}%  left {sm['left']}%  right {sm['right']}%")
    print(f"  captions:      {cap['size_pct']}% height, {cap['position']}")
    print(f"  notes:         {p['notes']}")
    print(f"  fit mode:      {mode}")
    print(f"  ffmpeg -vf:    {vf}")
    print(f"  full cmd:      ffmpeg -y -i IN -vf \"{vf}\" -r {fps} -b:v {p['max_bitrate_kbps']}k -c:a aac OUT")
    # also emit machine-readable for the orchestrator to consume
    print("\n" + json.dumps({
        "profile": name, "width": w, "height": h, "fps": fps,
        "loudness_lufs": p["loudness_lufs"], "safe_margins_pct": sm,
        "caption": cap, "fit_mode": mode, "vf": vf,
    }))
    return 0


def cmd_apply(name: str, inp: Path, out: Path, mode: str) -> int:
    doc = load_profiles()
    p = get_profile(doc, name)
    if not inp.is_file():
        die(f"input not found: {inp}")
    w, h, fps = p["width"], p["height"], p["fps"]
    vf = fit_filter(w, h, mode)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(inp), "-vf", vf, "-r", str(fps),
        "-b:v", f"{p['max_bitrate_kbps']}k", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-c:a", "aac", str(out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        die(f"ffmpeg failed: {(exc.stderr or '')[-300:]}")
    # verify dims
    try:
        dims = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(out)],
            check=True, capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        dims = "?"
    print(f"apply_profile: {name} ({mode}) -> {out}  [{dims}]")
    if not out.is_file():
        die("apply produced no output")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Render-profile resolver + applier")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("resolve")
    pr.add_argument("--profile", required=True)
    pr.add_argument("--mode", default="cover", choices=["cover", "contain"])
    pa = sub.add_parser("apply")
    pa.add_argument("--profile", required=True)
    pa.add_argument("--in", dest="inp", required=True)
    pa.add_argument("--out", required=True)
    pa.add_argument("--mode", default="cover", choices=["cover", "contain"])
    args = ap.parse_args()
    if args.cmd == "resolve":
        return cmd_resolve(args.profile, args.mode)
    if args.cmd == "apply":
        return cmd_apply(args.profile, Path(args.inp), Path(args.out), args.mode)
    return 2


if __name__ == "__main__":
    sys.exit(main())
