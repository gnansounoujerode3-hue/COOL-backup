#!/usr/bin/env python3
"""Compositor v3 « Pinterest premium ».

1. ffmpeg  : upscale Lanczos, unsharp, courbe en S, colorimétrie chaude, vignettage -> RGB brut
2. Python  : caméra (8 segments), flous de fouet aux coupes, halation, aberration
             chromatique, grain film, scènes de coupe avec médaillon du sujet,
             habillage typographique, sous-titres cinétiques, chrome (bandeau + progression)
3. ffmpeg  : fondu de sortie, mixage audio, encodage H.264
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan4 import (CAMERA, CUTAWAYS, CUTS, DURATION, FADE_DUR, FADE_START,  # noqa: E402
                   FPS, GOLD, H, INK, OVERLAYS, SCENES, W, X_L, X_R, RULE_Y, PRODUCTS)
import captions3  # noqa: E402

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
WORK = "/home/user/w3"
A = os.path.join(WORK, "tools3/assets3")
os.chdir(WORK)

out_path = sys.argv[1] if len(sys.argv) > 1 else "out3/rockwood-method-signature-9x16.mp4"
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

# ------------------------------------------------------------------ calques
PAD = {
    "hl_title": 78, "hl_foundation": 78, "card01": 80, "card02": 80, "card03": 80,
    "sticker": 58, "stamp": 76, "count_base": 84, "split_top": 54, "split_bot": 54,
    "split_rule": 0, "pill": 66, "glow": 0, "scrim_top": 0, "scrim_bottom": 0,
    "arrow": 42, "endcard": 0,
}
LAYERS = []
for name, t0, t1, anchor, x, y, anim in OVERLAYS:
    img = Image.open(os.path.join(A, name + ".png")).convert("RGBA")
    LAYERS.append({"name": name, "img": img, "t0": t0, "t1": t1, "anchor": anchor,
                   "x": x, "y": y, "anim": anim, "pad": PAD.get(name, 0)})

MASTHEAD = Image.open(os.path.join(A, "masthead.png")).convert("RGBA")
HEADS = [Image.open(os.path.join(A, f"head{i}.png")).convert("RGBA") for i in range(len(SCENES))]
PROGRESS = Image.open(os.path.join(A, "progress.png")).convert("RGBA")
ARROW = Image.open(os.path.join(A, "arrow.png")).convert("RGBA")
RING = Image.open(os.path.join(A, "ring.png")).convert("RGBA")
MASK = Image.open(os.path.join(A, "mask_circle.png")).convert("L")
CUT_SCENES = {c[0]: Image.open(os.path.join(A, f"cutaway_{c[2].split()[0]}.png")).convert("RGBA")
              for c in CUTAWAYS}

# masque du médaillon (cercle net + bord adouci)
_soft = Image.new("L", (400, 400), 0)
ImageDraw.Draw(_soft).ellipse((4, 4, 395, 395), fill=255)
MED_MASK = _soft.filter(ImageFilter.GaussianBlur(2))

# ------------------------------------------------------------------ polices compteur
F_BIG = ImageFont.truetype(f"{WORK}/node_modules/@expo-google-fonts/space-grotesk/"
                           "700Bold/SpaceGrotesk_700Bold.ttf", 150)

# ------------------------------------------------------------------ grain (tuiles)
GRAIN = []
rng = np.random.default_rng(2026)
for _ in range(10):
    g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    g = np.clip(g, -2.6, 2.6) / 2.6
    GRAIN.append(g)


def grain(frame, t):
    """Grain argentique animé, plus marqué dans les tons moyens."""
    g = GRAIN[int(t * 25) % len(GRAIN)]
    a = np.asarray(frame, dtype=np.float32)
    luma = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    w = 1.0 - np.abs(luma / 255.0 - 0.5) * 1.1
    w = np.clip(w, 0.0, 1.0)[..., None]
    gi = np.asarray(Image.fromarray(((g + 1) * 127.5).astype(np.uint8)).resize((W, H),
                                                                              Image.BILINEAR),
                    dtype=np.float32)
    gi = (gi - 127.5) / 127.5
    a += gi[..., None] * 5.2 * w
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def halation(frame):
    """Bloom chaud des hautes lumières (peau, écran) — matière filmique."""
    a = np.asarray(frame, dtype=np.float32)
    luma = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    hi = np.clip((luma - 188.0) / 67.0, 0, 1)
    if hi.max() <= 0.01:
        return frame
    small = Image.fromarray((hi * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    bloom = small.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR)
    b = np.asarray(bloom, dtype=np.float32) / 255.0
    tint = np.array([1.0, 0.62, 0.36], dtype=np.float32)          # ambre
    add = (b * 26.0)[..., None] * tint
    a = 255.0 - (255.0 - a) * (1.0 - 0.17 * b[..., None])          # screen doux
    a = a + add
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def chroma(frame):
    """Aberration chromatique latérale discrète (bords chauds / froids)."""
    a = np.asarray(frame)
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], 2, axis=1)      # rouge vers la droite
    out[..., 2] = np.roll(a[..., 2], -2, axis=1)     # bleu vers la gauche
    return Image.fromarray(out)


def camera(base, t):
    seg = CAMERA[-1]
    for s in CAMERA:
        if s[0] <= t < s[1]:
            seg = s
            break
    z0, dx, dy = seg[2], seg[3], seg[4]
    p = (t - seg[0]) / max(0.01, seg[1] - seg[0])
    z = z0 * (1 + 0.014 * p)
    cw, ch = W / z, H / z
    cx, cy = W / 2 + dx * (0.35 + 0.65 * p), H / 2 + dy * (0.35 + 0.65 * p)
    x0 = int(max(0, min(W - cw, cx - cw / 2)))
    y0 = int(max(0, min(H - ch, cy - ch / 2)))
    return base.crop((x0, y0, x0 + int(cw), y0 + int(ch))).resize((W, H), Image.LANCZOS)


def whip(frame, t):
    """Flou de fouet autour des coupes."""
    near = min((abs(t - c) for c in CUTS), default=1.0)
    if near > 0.12:
        return frame
    p = 1 - near / 0.12
    p = p * p
    k = 1 + int(15 * p)
    if k % 2 == 0:
        k += 1
    return frame.filter(ImageFilter.GaussianBlur(0)).filter(
        ImageFilter.BoxBlur(radius=k / 2)) if False else _box_h(frame, k)


def _box_h(frame, k):
    """Flou directionnel horizontal via BoxBlur sur image transposée."""
    tr = frame.transpose(Image.ROTATE_90)
    tr = tr.filter(ImageFilter.BoxBlur(radius=k / 2))
    return tr.transpose(Image.ROTATE_270)


def ease_out(x):
    return 1 - (1 - x) ** 3


def layer_place(layer, t):
    img, anchor, pad = layer["img"], layer["anchor"], layer["pad"]
    cw, ch = img.width - 2 * pad, img.height - 2 * pad
    if anchor == "rt":
        return img, layer["x"] - cw - pad, layer["y"] - pad, cw
    if anchor == "lb":
        return img, layer["x"] - pad, layer["y"] - ch - pad, cw
    if anchor == "lt":
        return img, layer["x"] - pad, layer["y"] - pad, cw
    return img, int(round(layer["x"] - img.width / 2)), int(round(layer["y"] - img.height / 2)), cw


def layer_alpha(layer, t):
    t0, t1, anim = layer["t0"], layer["t1"], layer["anim"]
    if not (t0 <= t <= t1):
        return None
    if anim == "none":
        return 1.0
    fin, fout = {"glow": (0.7, 0.8), "slap": (0.3, 0.25), "draw": (0.45, 0.3),
                 "card": (0.65, 0.5)}.get(anim, (0.5, 0.28))
    return max(0.0, min(1.0, (t - t0) / fin, (t1 - t) / fout))


def layer_transform(layer, t):
    """(échelle, décalage x, décalage y)"""
    anim, t0 = layer["anim"], layer["t0"]
    if anim == "rise":
        return 1.0, 0, int(round(26 * (1 - ease_out(min(1.0, (t - t0) / 0.55)))))
    if anim == "slap":
        return 1.075 - 0.075 * ease_out(min(1.0, (t - t0) / 0.34)), 0, 0
    if anim == "slide_l":
        return 1.0, int(-46 * (1 - ease_out(min(1.0, (t - t0) / 0.5)))), 0
    if anim == "slide_r":
        return 1.0, int(46 * (1 - ease_out(min(1.0, (t - t0) / 0.5)))), 0
    return 1.0, 0, 0


def draw_count(base, t):
    """Compteur 0 → 100 % synchronisé sur la voix (17,26 → 19,38 s)."""
    if not (17.10 <= t <= 19.50):
        return
    p = max(0.0, min(1.0, (t - 17.24) / 1.55))
    p = ease_out(p)
    val = int(round(p * 100))
    txt = f"{val}%"
    im = Image.new("RGBA", (700, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((676, 34), txt, font=F_BIG, fill=(10, 5, 4, 130), anchor="ra")
    d.text((674, 30), txt, font=F_BIG, fill=GOLD + (255,), anchor="ra")
    a = min(1.0, (t - 17.10) / 0.4, (19.50 - t) / 0.3)
    if a < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(im, (X_R - 700, 296))


def draw_cutaway(base, frame_for_med, t):
    """Scène plein cadre + sujet en médaillon cerclé."""
    active = None
    for c in CUTAWAYS:
        if c[0] <= t <= c[1]:
            active = c
            break
    if active is None:
        return
    t0, t1, idx, kicker, l1, l2, sub, accent, px, py, r = active

    # transition en glissé latéral (0,22 s)
    slide = 0.0
    if t - t0 < 0.22:
        slide = (1 - ease_out((t - t0) / 0.22)) * 90
    if t1 - t < 0.18:
        slide = -(1 - ease_out((t1 - t) / 0.18)) * 70

    scene = CUT_SCENES[t0].copy()
    if slide:
        scene = scene.transform(scene.size, Image.AFFINE, (1, 0, slide, 0, 1, 0),
                                resample=Image.BICUBIC)

    # médaillon : recadrage du sujet dans l'image d'origine (avant caméra)
    r_src = 330
    cx, cy = 456, 596
    box = (max(0, cx - r_src), max(0, cy - r_src),
           min(W, cx + r_src), min(H, cy + r_src))
    face = frame_for_med.crop(box)
    side = 2 * r
    face = face.resize((side, side), Image.LANCZOS)
    face.putalpha(MED_MASK.resize((side, side), Image.LANCZOS))

    a = min(1.0, (t - t0 - 0.10) / 0.45)
    if a > 0.02:
        sc = 0.93 + 0.07 * ease_out(min(1.0, (t - t0 - 0.10) / 0.5))
        sd = int(side * sc)
        f2 = face.resize((sd, sd), Image.LANCZOS)
        if a < 1:
            f2 = f2.copy()
            f2.putalpha(f2.getchannel("A").point(lambda v: int(v * a)))
        ring = RING.resize((int(sd * 1.06), int(sd * 1.06)), Image.LANCZOS)
        if a < 1:
            ring = ring.copy()
            ring.putalpha(ring.getchannel("A").point(lambda v: int(v * a)))
        scene.alpha_composite(f2, (int(px - sd / 2), int(py - sd / 2)))
        scene.alpha_composite(ring, (int(px - ring.width / 2), int(py - ring.height / 2)))

    base.alpha_composite(scene)


def draw_chrome(base, t):
    base.alpha_composite(MASTHEAD, (0, 0))
    for i, (s0, s1, label) in enumerate(SCENES):
        if s0 <= t < s1:
            a = min(1.0, (t - s0) / 0.35, (s1 - t) / 0.3)
            head = HEADS[i]
            if a < 1:
                head = head.copy()
                head.putalpha(head.getchannel("A").point(lambda v: int(v * a)))
            base.alpha_composite(head, (X_R - head.width + 60, 96))
            break
    fill = int(PROGRESS.width * min(1.0, t / (DURATION - 0.6)))
    if fill > 3:
        base.alpha_composite(PROGRESS.crop((0, 0, fill, PROGRESS.height)), (X_L, RULE_Y - 3))


def draw_arrow(base, t):
    """Flèche du CTA : va-et-vient doux."""
    if not (22.80 <= t <= 25.80):
        return
    base.alpha_composite(ARROW, (770 + int(7 * np.sin((t - 22.8) * 5.2)), 1344 - ARROW.height // 2))


# ------------------------------------------------------------------ ffmpeg
GRADE = ("scale=1080:1920:flags=lanczos,"
         "unsharp=5:5:0.55:3:3:0.0,"
         "eq=contrast=1.075:brightness=0.004:saturation=1.04:gamma=0.98,"
         "curves=master='0/0 0.18/0.155 0.5/0.52 0.8/0.84 1/1',"
         "colorbalance=rs=-0.016:gs=-0.008:bs=0.024:rm=0.012:gm=0.005:bm=-0.014:"
         "rh=0.034:gh=0.016:bh=-0.030,"
         "vignette=angle=PI/4.8:mode=forward,"
         f"tpad=stop_mode=clone:stop_duration={DURATION - 27.6:.2f}")

src = os.path.join(WORK, "AIDE-CHATGPT-main/video brut.mp4")
vin = [FF, "-hide_banner", "-loglevel", "error", "-i", src, "-vf", GRADE,
       "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "rgb24", "-an", "-"]

vout = [FF, "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", os.path.join(WORK, "tools3/mix3.wav"),
        "-filter_complex",
        f"[0:v]fade=t=out:st={FADE_START}:d={FADE_DUR},format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a", "-t", str(DURATION),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", out_path]

env = dict(os.environ, FONTCONFIG_FILE=os.path.join(WORK, "fonts.conf"))
p_in = subprocess.Popen(vin, stdout=subprocess.PIPE, env=env)
p_out = subprocess.Popen(vout, stdin=subprocess.PIPE, env=env)

# ------------------------------------------------------------------ boucle
import json  # noqa: E402
words = json.load(open(os.path.join(WORK, "words.json"), encoding="utf-8"))
cues = captions3.build(words)

frame_bytes = W * H * 3
done = 0
n_frames = int(round(DURATION * FPS))
step = max(1, n_frames // 12)

while True:
    buf = p_in.stdout.read(frame_bytes)
    if len(buf) < frame_bytes:
        break
    t = done / FPS

    raw = Image.frombytes("RGB", (W, H), buf)
    framed = camera(raw, t)

    base = framed
    base = whip(base, t)
    base = chroma(base)
    base = halation(base)
    base = grain(base, t)
    base = base.convert("RGBA")

    draw_cutaway(base, raw, t)

    for layer in LAYERS:
        a = layer_alpha(layer, t)
        if a is None:
            continue
        img, x, y, cw = layer_place(layer, t)
        sc, dx, dy = layer_transform(layer, t)
        x += dx
        im = img
        if layer["anim"] == "draw":          # filet qui se trace
            p = min(1.0, (t - layer["t0"]) / 0.5)
            im = img.crop((0, 0, max(4, int(img.width * ease_out(p))), img.height))
        if sc != 1.0:
            im = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
            if layer["anchor"] == "c":
                x, y = int(round(layer["x"] - im.width / 2)), int(round(layer["y"] - im.height / 2))
        if a < 1.0:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        base.alpha_composite(im, (x, y + dy))

    draw_count(base, t)
    draw_arrow(base, t)

    ci = captions3.active_index(cues, t)
    if ci is not None:
        captions3.draw(base, cues, t, ci)

    draw_chrome(base, t)

    p_out.stdin.write(base.convert("RGB").tobytes())
    done += 1
    if done % step == 0:
        print(f"  {done}/{n_frames} images…", flush=True)

p_in.stdout.close()
p_in.wait()
p_out.stdin.close()
p_out.wait()
print(f"{done} images ({done / FPS:.2f}s) -> {out_path}")
print("encodage :", p_out.returncode, "| décodage :", p_in.returncode)
