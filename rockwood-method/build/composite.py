#!/usr/bin/env python3
"""Compositor : decode la vidéo source en RGB, dessine les incrustations animées,
puis repipe vers ffmpeg qui applique les sous-titres ASS, le fondu et l'audio.

Usage : python3 build/composite.py <sortie.mp4>
"""
import os
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import OVERLAYS, FADE_START, FADE_DUR, DURATION, FPS  # noqa: E402

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
W, H = 1080, 1920
WORK = "/home/user/work"
os.chdir(WORK)

out_path = sys.argv[1] if len(sys.argv) > 1 else "out/rockwood-method-montage-9x16.mp4"

# --- prerender de l'habillage : liste (nom, image RGBA, t0, t1, cx, cy, anim)
LAYERS = []
for asset, t0, t1, cx, cy, anim in OVERLAYS:
    img = Image.open(os.path.join(WORK, "build/assets", asset + ".png")).convert("RGBA")
    LAYERS.append((asset, img, t0, t1, cx, cy, anim))

F_IN, F_OUT = 0.24, 0.22


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def layer_state(layer, t):
    """Renvoie (image, x, y) à l'instant t, ou None."""
    asset, img, t0, t1, cx, cy, anim = layer
    if not (t0 <= t <= t1):
        return None

    a = 1.0
    if anim != "static":
        a = min(1.0, (t - t0) / F_IN, max(0.0, (t1 - t) / F_OUT))
        if a <= 0.003:
            return None
        a = max(0.0, min(1.0, a))

    scale = 1.0
    dy = 0
    if anim == "rise":
        p = min(1.0, (t - t0) / 0.34)
        dy = int(round(44 * (1 - ease_out_cubic(p))))
    elif anim == "pop":
        p = min(1.0, (t - t0) / 0.26)
        scale = 0.84 + 0.16 * ease_out_cubic(p)
    elif anim == "zoom":
        p = (t - t0) / max(0.01, (t1 - t0))
        scale = 1.0 + 0.045 * ease_out_cubic(p)

    im = img
    if scale != 1.0:
        im = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                        Image.LANCZOS)

    if a < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    else:
        im = im.copy()

    x = int(round(cx - im.width / 2))
    y = int(round(cy - im.height / 2)) + dy
    return im, x, y


# --- 1er ffmpeg : décodage de la source + mise à l'échelle/étalonnage
src = os.path.join(WORK, "AIDE-CHATGPT-main/video brut.mp4")
vin = [
    FF, "-hide_banner", "-loglevel", "error",
    "-i", src,
    "-vf", ("scale=1080:1920:flags=lanczos,unsharp=5:5:0.4:3:3:0.0,"
            "eq=contrast=1.035:saturation=1.06:brightness=0.008,"
            f"tpad=stop_mode=clone:stop_duration={DURATION - 27.6:.2f}"),
    "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "rgb24", "-an", "-",
]

# --- 2e ffmpeg : sous-titres + fondu + audio + encodage
vout = [
    FF, "-hide_banner", "-loglevel", "warning", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", os.path.join(WORK, "build/mix.wav"),
    "-filter_complex",
    (f"[0:v]ass=build/subs.ass:fontsdir=fonts,"
     f"fade=t=out:st={FADE_START}:d={FADE_DUR},format=yuv420p[v]"),
    "-map", "[v]", "-map", "1:a", "-t", str(DURATION),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", out_path,
]

env = dict(os.environ, FONTCONFIG_FILE=os.path.join(WORK, "fonts.conf"))
p_in = subprocess.Popen(vin, stdout=subprocess.PIPE, env=env)
p_out = subprocess.Popen(vout, stdin=subprocess.PIPE, env=env)

n_frames = int(round(DURATION * FPS))
frame_bytes = W * H * 3
done = 0

while True:
    buf = p_in.stdout.read(frame_bytes)
    if len(buf) < frame_bytes:
        break
    t = done / FPS

    base = Image.frombytes("RGB", (W, H), buf).convert("RGBA")
    for layer in LAYERS:
        st = layer_state(layer, t)
        if st is None:
            continue
        im, x, y = st
        base.alpha_composite(im, (x, y))

    p_out.stdin.write(base.convert("RGB").tobytes())
    done += 1

p_in.stdout.close()
p_in.wait()
p_out.stdin.close()
p_out.wait()

print(f"{done} images composées ({done / FPS:.2f}s) -> {out_path}")
print("ffmpeg sortie :", p_out.returncode, "| décodage :", p_in.returncode)
