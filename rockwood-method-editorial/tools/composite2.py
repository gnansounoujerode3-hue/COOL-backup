#!/usr/bin/env python3
"""Compositor v2 : étalonnage filmique + habillage éditorial + sous-titres v2.

Chaîne :
  1. ffmpeg : upscale, étalonnage, vignettage, grain, gel de la dernière image -> RGB brut
  2. Python : composition des calques (bandeau, barre de progression, titres, filets)
  3. ffmpeg : sous-titres ASS, fondu, mixage audio, encodage H.264

Usage : python3 build2/composite2.py <sortie.mp4>
"""
import os
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan2 import OVERLAYS, FADE_START, FADE_DUR, DURATION, FPS, X_L, RULE_Y  # noqa: E402

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
W, H = 1080, 1920
WORK = "/home/user/work2"
os.chdir(WORK)

out_path = sys.argv[1] if len(sys.argv) > 1 else "out2/rockwood-method-editorial-9x16.mp4"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

# marges d'ombre (pad) autour du contenu utile de chaque PNG
PAD = {
    "hl_method": 78, "hl_foundation": 78, "hl_after": 78,
    "big100": 74, "rows01": 74, "rows02": 74, "rows03": 74,
    "sticker": 58, "stamp": 74, "pill": 66,
    "masthead": 0, "progress": 0, "scrim_top": 0, "scrim_bottom": 0,
    "glow": 0, "endcard": 0,
}

LAYERS = []
for asset, t0, t1, anchor, x, y, anim in OVERLAYS:
    img = Image.open(os.path.join(WORK, "build2/assets2", asset + ".png")).convert("RGBA")
    LAYERS.append({"name": asset, "img": img, "t0": t0, "t1": t1,
                   "anchor": anchor, "x": x, "y": y, "anim": anim,
                   "pad": PAD.get(asset, 0)})

MASTHEAD = Image.open(os.path.join(WORK, "build2/assets2/masthead.png")).convert("RGBA")
PROGRESS = Image.open(os.path.join(WORK, "build2/assets2/progress.png")).convert("RGBA")
PROG_X, PROG_W = X_L, PROGRESS.width

F_IN, F_OUT = 0.50, 0.28

# Caméra : (début, fin, zoom, décalage x, décalage y) — coupes alignées sur les silences
SEGMENTS = [
    (0.00, 6.55, 1.000, 0, 0),
    (6.55, 13.45, 1.048, -12, 8),
    (13.45, 17.05, 1.020, 8, -6),
    (17.05, 19.55, 1.058, -10, 12),
    (19.55, 22.55, 1.030, 6, 4),
    (22.55, 25.85, 1.066, -8, 14),
    (25.85, 29.10, 1.040, 0, 0),
]


def camera(base, t):
    """Applique le cadrage caméra (zoom + dérive lente dans chaque plan)."""
    seg = SEGMENTS[-1]
    for sgm in SEGMENTS:
        if sgm[0] <= t < sgm[1]:
            seg = sgm
            break
    z0, dx, dy = seg[2], seg[3], seg[4]
    p = (t - seg[0]) / max(0.01, seg[1] - seg[0])
    z = z0 * (1 + 0.012 * p)
    cw, ch = W / z, H / z
    cx, cy = W / 2 + dx * (0.4 + 0.6 * p), H / 2 + dy * (0.4 + 0.6 * p)
    x0 = int(max(0, min(W - cw, cx - cw / 2)))
    y0 = int(max(0, min(H - ch, cy - ch / 2)))
    return base.crop((x0, y0, x0 + int(cw), y0 + int(ch))).resize((W, H), Image.LANCZOS)


def ease_out(x):
    return 1 - (1 - x) ** 3


def place(layer, t):
    """Renvoie (image, x, y) pour un calque à l'instant t, ou None."""
    img, a, pad = layer["img"], layer["anchor"], layer["pad"]
    cw, ch = img.width - 2 * pad, img.height - 2 * pad     # contenu utile

    if a == "rt":        # bord droit du contenu / haut du contenu
        x = layer["x"] - cw - pad
        y = layer["y"] - pad
    elif a == "lb":      # bord gauche / bas du contenu
        x = layer["x"] - pad
        y = layer["y"] - ch - pad
    elif a == "lt":      # bord gauche / haut
        x, y = layer["x"] - pad, layer["y"] - pad
    else:                # centre
        x = int(round(layer["x"] - img.width / 2))
        y = int(round(layer["y"] - img.height / 2))

    return img, x, y


def alpha_at(layer, t):
    t0, t1, anim = layer["t0"], layer["t1"], layer["anim"]
    if not (t0 <= t <= t1):
        return None
    if anim == "none":
        return 1.0
    if anim == "glow":
        fin, fout = 0.7, 0.8
    elif anim == "slap":
        fin, fout = 0.30, 0.25
    elif anim == "card":
        fin, fout = 0.5, 0.45
    else:
        fin, fout = F_IN, F_OUT
    return max(0.0, min(1.0, (t - t0) / fin, (t1 - t) / fout))


def transform(layer, t):
    """(échelle, décalage vertical) selon l'animation."""
    anim, t0, t1 = layer["anim"], layer["t0"], layer["t1"]
    if anim == "rise":
        p = min(1.0, (t - t0) / 0.55)
        return 1.0, int(round(26 * (1 - ease_out(p))))
    if anim == "zoom":
        p = min(1.0, (t - t0) / 0.6)
        return 0.955 + 0.045 * ease_out(p), 0
    if anim == "slap":
        p = min(1.0, (t - t0) / 0.34)
        return 1.075 - 0.075 * ease_out(p), 0
    return 1.0, 0


GRADE = ("scale=1080:1920:flags=lanczos,"
         "unsharp=5:5:0.5:3:3:0.0,"
         "eq=contrast=1.055:brightness=0.006:saturation=1.05:gamma=0.985,"
         "curves=master='0/0 0.22/0.20 0.5/0.52 0.78/0.81 1/1',"
         "colorbalance=rs=-0.012:gs=-0.006:bs=0.018:rm=0.010:gm=0.005:bm=-0.012:"
         "rh=0.028:gh=0.013:bh=-0.026,"
         "vignette=angle=PI/4.9:mode=forward,"
         "noise=alls=4:allf=t+u,"
         f"tpad=stop_mode=clone:stop_duration={DURATION - 27.6:.2f}")

src = os.path.join(WORK, "AIDE-CHATGPT-main/video brut.mp4")
vin = [FF, "-hide_banner", "-loglevel", "error", "-i", src,
       "-vf", GRADE, "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "rgb24", "-an", "-"]

vout = [FF, "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", os.path.join(WORK, "build2/mix2.wav"),
        "-filter_complex",
        (f"[0:v]ass=build2/subs2.ass:fontsdir=fonts,"
         f"fade=t=out:st={FADE_START}:d={FADE_DUR},format=yuv420p[v]"),
        "-map", "[v]", "-map", "1:a", "-t", str(DURATION),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", out_path]

env = dict(os.environ, FONTCONFIG_FILE=os.path.join(WORK, "fonts.conf"))
p_in = subprocess.Popen(vin, stdout=subprocess.PIPE, env=env)
p_out = subprocess.Popen(vout, stdin=subprocess.PIPE, env=env)

frame_bytes = W * H * 3
done, n_frames = 0, int(round(DURATION * FPS))
prog_cache = {}

while True:
    buf = p_in.stdout.read(frame_bytes)
    if len(buf) < frame_bytes:
        break
    t = done / FPS

    frame = Image.frombytes("RGB", (W, H), buf)
    base = camera(frame, t).convert("RGBA")

    for layer in LAYERS:
        a = alpha_at(layer, t)
        if a is None:
            continue
        img, x, y = place(layer, t)
        sc, dy = transform(layer, t)

        im = img
        if sc != 1.0:
            key = (layer["name"], round(sc, 4))
            if key not in prog_cache:
                prog_cache[key] = img.resize(
                    (max(1, int(img.width * sc)), max(1, int(img.height * sc))),
                    Image.LANCZOS)
            im = prog_cache[key]
            x = int(round(layer["x"] - im.width / 2)) if layer["anchor"] == "c" else x
            y = int(round(layer["y"] - im.height / 2)) if layer["anchor"] == "c" else y

        if a < 1.0 or dy:
            im = im.copy()
            if a < 1.0:
                im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            base.alpha_composite(im, (x, y + dy))
        else:
            base.alpha_composite(im, (x, y))

    # bandeau persistant
    base.alpha_composite(MASTHEAD, (0, 0))
    # barre de progression dans le filet
    fill = int(PROG_W * min(1.0, t / (DURATION - 0.6)))
    if fill > 2:
        base.alpha_composite(PROGRESS.crop((0, 0, fill, PROGRESS.height)), (PROG_X, RULE_Y - 3))

    p_out.stdin.write(base.convert("RGB").tobytes())
    done += 1

p_in.stdout.close()
p_in.wait()
p_out.stdin.close()
p_out.wait()

print(f"{done} images ({done / FPS:.2f}s) -> {out_path}")
print("encodage :", p_out.returncode, "| décodage :", p_in.returncode)
