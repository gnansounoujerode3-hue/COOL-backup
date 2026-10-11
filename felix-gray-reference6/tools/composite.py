#!/usr/bin/env python3
"""Main 1080x1920 24fps compositor for Felix Gray (inspired by REFERENCE 6.mp4)."""
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import (
    W, H, FPS, DURATION, FADE_START, FADE_DUR,
    CAMERA_SEGMENTS, CUTAWAY_WINDOWS, TRANSITION_TIMES,
)
import render_graphics


GRADE = (
    "scale=1080:2160:flags=lanczos,crop=1080:1920:0:210,"
    "unsharp=5:5:0.50:3:3:0.0,"
    "eq=contrast=1.10:brightness=-0.020:saturation=0.94:gamma=0.96,"
    "colorbalance=rs=-0.030:gs=-0.012:bs=0.050:rm=-0.008:gm=0.000:bm=0.022:rh=0.015:gh=0.010:bh=-0.010"
)

CUTAWAY_EDGES = [12.10, 16.45, 25.15, 30.05, 42.25, 46.63]


def apply_camera(frame, t):
    """Applies smooth zoom-in and subtle pan per segment on live footage."""
    seg = None
    for s in CAMERA_SEGMENTS:
        if s[0] <= t < s[1]:
            seg = s
            break
    if seg is None:
        return frame
    t0, t1, z0, z1, dx, dy = seg
    p = max(0.0, min(1.0, (t - t0) / max(0.01, t1 - t0)))
    z = z0 + (z1 - z0) * p
    if abs(z - 1.0) < 0.003 and dx == 0 and dy == 0:
        return frame
    cw = W / z
    ch = H / z
    cx = W / 2.0 + dx * p
    cy = H / 2.0 + dy * p
    x0 = int(round(max(0.0, min(W - cw, cx - cw / 2.0))))
    y0 = int(round(max(0.0, min(H - ch, cy - ch / 2.0))))
    return frame.crop((x0, y0, x0 + int(round(cw)), y0 + int(round(ch)))).resize((W, H), Image.BICUBIC)


def apply_transition_whip(frame_rgb, t):
    """Applies a short directional motion blur + subtle sapphire flash around cutaway transitions."""
    d_cutaway = min((abs(t - c) for c in CUTAWAY_EDGES), default=1.0)
    d_raw = min((abs(t - c) for c in TRANSITION_TIMES), default=1.0)

    if d_cutaway < 0.13:
        p = (1.0 - d_cutaway / 0.13) ** 2
        rad = max(1, int(round(14 * p)))
        tr = frame_rgb.transpose(Image.ROTATE_90).filter(ImageFilter.BoxBlur(rad)).transpose(Image.ROTATE_270)
        arr = np.asarray(tr, dtype=np.float32)
        # Subtle electric-blue flash at the exact frame of cutaway entry/exit
        arr[..., 0] = np.clip(arr[..., 0] * (1.0 - 0.25 * p) + 12 * p, 0, 255)
        arr[..., 1] = np.clip(arr[..., 1] * (1.0 - 0.20 * p) + 38 * p, 0, 255)
        arr[..., 2] = np.clip(arr[..., 2] + 65 * p, 0, 255)
        return Image.fromarray(arr.astype(np.uint8), "RGB")

    if d_raw < 0.09:
        p = (1.0 - d_raw / 0.09) ** 2
        rad = max(1, int(round(8 * p)))
        return frame_rgb.transpose(Image.ROTATE_90).filter(ImageFilter.BoxBlur(rad)).transpose(Image.ROTATE_270)

    return frame_rgb


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(here)
    repo_root = os.path.dirname(proj_dir)

    raw_video = os.path.join(repo_root, "video brut 5 - Copie.mp4")
    mix_wav = "/home/user/.cache/fg_audio/mix.wav"
    if not os.path.exists(mix_wav):
        import gen_audio
        gen_audio.main()

    out_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(proj_dir, "film", "felix-gray-reference6-9x16.mp4")
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    vin_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", raw_video,
        "-vf", GRADE,
        "-r", str(FPS),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-an", "-"
    ]

    vout_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", mix_wav,
        "-filter_complex", f"[0:v]fade=t=out:st={FADE_START}:d={FADE_DUR},format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a",
        "-t", str(DURATION),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart",
        out_path
    ]

    p_in = subprocess.Popen(vin_cmd, stdout=subprocess.PIPE)
    p_out = subprocess.Popen(vout_cmd, stdin=subprocess.PIPE)

    frame_bytes = W * H * 3
    n_frames = int(round(DURATION * FPS))
    step = max(1, n_frames // 10)
    done = 0

    print(f"Rendering {n_frames} frames ({DURATION}s @ {FPS}fps) -> {out_path}")
    while done < n_frames:
        buf = p_in.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        t = done / float(FPS)

        # Check if timestamp is inside one of the 3 full-screen dark UI cutaways
        active_cutaway = None
        for c0, c1, kind in CUTAWAY_WINDOWS:
            if c0 <= t < c1:
                active_cutaway = (c0, c1, kind)
                break

        if active_cutaway is not None:
            c0, c1, kind = active_cutaway
            if kind == "ui_card":
                comp = render_graphics.render_cutaway_ui_card(t, c0, c1)
            elif kind == "orbital":
                comp = render_graphics.render_cutaway_orbital(t, c0, c1)
            else:
                comp = render_graphics.render_cutaway_question(t)
            out_rgb = comp.convert("RGB")
        else:
            raw_im = Image.frombytes("RGB", (W, H), buf)
            framed = apply_camera(raw_im, t)
            comp = framed.convert("RGBA")
            render_graphics.draw_chest_graphics(comp, t)
            out_rgb = comp.convert("RGB")

        out_rgb = apply_transition_whip(out_rgb, t)
        p_out.stdin.write(out_rgb.tobytes())
        done += 1
        if done % step == 0 or done == n_frames:
            print(f"  [{done:4d}/{n_frames}] ({done / FPS:5.2f}s)", flush=True)

    p_in.stdout.close()
    p_in.wait()
    p_out.stdin.close()
    p_out.wait()
    print(f"Done! Encoded {done} frames -> {out_path} (rc={p_out.returncode})")


if __name__ == "__main__":
    main()
