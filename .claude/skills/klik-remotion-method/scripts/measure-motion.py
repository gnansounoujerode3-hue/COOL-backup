#!/usr/bin/env python3
"""measure-motion.py — arithmetic QA for the energy arc (A18) and the
rest ratio (A6), measured from RENDERED FRAMES, not from code.

  python3 measure-motion.py render.mp4 [--map music-map.json]
      [--rest-k 0.35] [--json out.json]

What it does
  1. Frame-diffs the video (ffmpeg tblend=difference, downscaled) into a
     per-frame motion-energy series — the piece's ACTUAL energy curve.
  2. Rest ratio: fraction of the timeline whose smoothed energy sits
     below a FLOOR-RELATIVE threshold `p10 + rest_k × (p90 − p10)` —
     checked against A6's 40–60% band. (Floor-relative because textural
     grounds elevate the baseline — see the in-code note.)
  3. With --map (the analyzer's music-map JSON): per-bar energy means vs
     `energy_tier_per_bar` — Pearson correlation + per-tier mean table.
     A piece that follows its arc shows rising means tier 1 → 5.
  4. ASCII sparkline of the smoothed curve (valleys and peaks at a
     glance — the arc SHAPE, for eyes; the numbers are the contract).

Scope note: camera-vs-element motion separation (klik-cam CAM-6 balance)
is a planned second stage; this tool measures TOTAL motion energy.
Requires ffmpeg on PATH. stdlib only.
"""
import argparse
import json
import math
import re
import subprocess
import sys

BLOCKS = " ▁▂▃▄▅▆▇█"


def frame_energy(path: str) -> list[float]:
    cmd = [
        "ffmpeg", "-i", path, "-vf",
        "tblend=all_mode=difference,scale=320:180,signalstats,"
        "metadata=mode=print:key=lavfi.signalstats.YAVG:file=-",
        "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    vals = [float(m) for m in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", proc.stdout)]
    if not vals:
        sys.exit("no frames measured — is ffmpeg on PATH and the file a video?")
    return vals


def smooth(xs: list[float], w: int) -> list[float]:
    out = []
    for i in range(len(xs)):
        a, b = max(0, i - w // 2), min(len(xs), i + w // 2 + 1)
        out.append(sum(xs[a:b]) / (b - a))
    return out


def pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = math.sqrt(sum((x - ma) ** 2 for x in a))
    vb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return cov / (va * vb) if va and vb else 0.0


def sparkline(xs: list[float], width: int = 66) -> str:
    if not xs:
        return ""
    step = max(1, len(xs) // width)
    pts = [sum(xs[i:i + step]) / len(xs[i:i + step]) for i in range(0, len(xs), step)]
    hi = max(pts) or 1
    return "".join(BLOCKS[min(8, int(p / hi * 8.999))] for p in pts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--map", dest="map_path")
    ap.add_argument("--rest-k", type=float, default=0.35,
                    help="rest threshold as a fraction of p90 energy")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    raw = frame_energy(args.video)
    fps = 30.0
    bars_meta = None
    if args.map_path:
        m = json.load(open(args.map_path))
        fps = float(m.get("fps", 30.0))
        bars_meta = m

    sm = smooth(raw, int(fps))  # ~1s window
    n = len(sm)
    srt = sorted(sm)
    p10 = srt[int(0.1 * (n - 1))]
    p50 = srt[int(0.5 * (n - 1))]
    p90 = srt[int(0.9 * (n - 1))]
    # Textural treatments (grain/boil grounds) elevate the energy FLOOR —
    # rest is measured against that baseline (p10), never against zero:
    # A6's own distinction between idle life and motion events.
    rest_thr = p10 + args.rest_k * (p90 - p10)
    rest = sum(1 for v in sm if v < rest_thr) / n
    contrast = (p90 - p10) / p50 if p50 else 0.0

    print(f"frames: {n}  duration: {n / fps:.1f}s @ {fps:g}fps")
    print(f"energy curve  |{sparkline(sm)}|")
    print(f"floor p10 {p10:.2f} · median {p50:.2f} · p90 {p90:.2f} · "
          f"event/rest contrast {contrast:.2f}")
    if contrast < 0.15:
        print("verdict: FLAT piece — no event/rest contrast (catalogue/glossary "
              "territory; a designed piece wants a shaped curve, A18)")
    else:
        band = "OK (A6 40-60%)" if 0.40 <= rest <= 0.60 else "OUT OF BAND (A6 wants 40-60%)"
        print(f"rest ratio: {rest * 100:.1f}%  (floor-relative, k={args.rest_k})  -> {band}")

    result = {"frames": n, "fps": fps, "rest_ratio": round(rest, 4),
              "contrast": round(contrast, 3), "p10": round(p10, 3),
              "p50": round(p50, 3), "p90": round(p90, 3),
              "energy_smoothed": [round(v, 3) for v in sm]}

    if bars_meta is not None:
        fpb = float(bars_meta["frames_per_beat"])
        f0 = int(bars_meta["first_downbeat_frame"])
        tiers = [int(c) for c in str(bars_meta["energy_tier_per_bar"])]
        bar_len = fpb * 4
        bar_means, bar_tiers = [], []
        for bi, tier in enumerate(tiers):
            a = int(f0 + bi * bar_len)
            b = int(f0 + (bi + 1) * bar_len)
            if a >= n:
                break
            seg = sm[a:min(b, n)]
            if seg:
                bar_means.append(sum(seg) / len(seg))
                bar_tiers.append(tier)
        r = pearson(bar_means, [float(t) for t in bar_tiers])
        print(f"arc correlation (per-bar energy vs designed tier): r = {r:.2f}  "
              f"[{len(bar_means)} bars]")
        per_tier: dict[int, list[float]] = {}
        for t, e in zip(bar_tiers, bar_means):
            per_tier.setdefault(t, []).append(e)
        mono_prev, mono = -1.0, True
        for t in sorted(per_tier):
            mean = sum(per_tier[t]) / len(per_tier[t])
            flag = "" if mean >= mono_prev else "  <-- non-monotonic"
            mono = mono and mean >= mono_prev
            print(f"  tier {t}: mean energy {mean:6.2f}  ({len(per_tier[t])} bars){flag}")
            mono_prev = mean
        print(f"tier means monotonic: {'YES' if mono else 'NO'} — "
              f"{'motion climbs with the designed arc' if mono else 'the piece is not following its arc'}")
        result.update({"arc_r": round(r, 3),
                       "bar_means": [round(v, 3) for v in bar_means],
                       "bar_tiers": bar_tiers})

    if args.json_out:
        json.dump(result, open(args.json_out, "w"))
        print(f"wrote {args.json_out}")


if __name__ == "__main__":
    main()
