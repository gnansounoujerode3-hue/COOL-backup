#!/usr/bin/env python3
"""Compositor v5 « cinématographique ».

Nouveautés par rapport à la v4 premium :
  1. Les scènes de coupe ne sont plus posées sur un aplat noir : leur fond est
     **fabriqué à partir de l'image du film** (flou profond, miroir, vignettage,
     bokeh doré) — on garde la matière, la couleur et la lumière de la prise.
  2. Le bloc typographique est transparent (plus de carton peint).
  3. La carte finale devient un plan large flouté + typographie serif pleine largeur.
  4. Les visuels produit flottent dans la lumière chaude du fond, avec ombre douce.

Chaîne : ffmpeg (étalonnage + prémultiplication alpha) -> Python (caméra, fonds,
médaillon, habillage, sous-titres) -> ffmpeg (mixage + encodage).
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan4 import (CAMERA, CUTAWAYS, CUTS, DURATION, FADE_DUR, FADE_START,  # noqa: E402
                   FPS, GOLD, H, INK, OVERLAYS, PRODUCTS, SCENES, W, X_L, X_R, RULE_Y)
import captions3  # noqa: E402

FF = os.environ.get("FFMPEG_BIN",
                    "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/"
                    "ffmpeg-linux-x86_64-v7.0.2")
# Racine du projet = dossier de la version ; tout est surchargeable par variable
WORK = os.environ.get("ROCKWOOD_WORK", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.dirname(os.path.abspath(__file__))
A = os.environ.get("ROCKWOOD_ASSETS", os.path.join(WORK, "assets"))
FONTS = os.environ.get("ROCKWOOD_FONTS", os.path.join(WORK, "node_modules"))
MIX = os.environ.get("ROCKWOOD_MIX", os.path.join(WORK, "audio/mix3.wav"))
WORDS = os.environ.get("ROCKWOOD_WORDS", os.path.join(WORK, "audio/words.json"))
os.chdir(WORK)

QC_TIMES = [float(x) for x in os.environ.get("V5_QC_TIMES", "").split(",") if x.strip()]
QC_FRAMES = []

out_path = sys.argv[1] if len(sys.argv) > 1 else "out5/rockwood-method-cinema-9x16.mp4"
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

PAD = {
    "hl_title": 78, "hl_foundation": 78, "card01": 80, "card02": 80, "card03": 80,
    "sticker": 58, "stamp": 76, "count_base": 84, "split_top": 54, "split_bot": 54,
    "split_rule": 0, "pill": 66, "glow": 0, "scrim_top": 0, "scrim_bottom": 0,
    "arrow": 42, "endcard": 0, "cut01": 54, "cut02": 54, "cut03": 54, "endtype": 59,
}
LAYERS = []
for name, t0, t1, anchor, x, y, anim in OVERLAYS:
    if name == "endcard":       # remplacée par la carte cinéma (fond + endtype)
        continue
    img = Image.open(os.path.join(A, name + ".png")).convert("RGBA")
    LAYERS.append({"name": name, "img": img, "t0": t0, "t1": t1, "anchor": anchor,
                   "x": x, "y": y, "anim": anim, "pad": PAD.get(name, 0)})

def make_plate(img, peak=140, blur=76, margin=74, radius=None):
    """Plaque sombre à bords très fondus, calquée sur l'encre du calque.

    Le type garde ainsi tout son contraste quel que soit l'arrière-plan (sujet,
    lumière chaude, bokeh) sans peindre un carton plein cadre. Le canevas est
    élargi pour que le flou ne soit jamais coupé par un bord franc.
    """
    bb = img.getchannel("A").getbbox()
    if bb is None:
        return None
    P = int(blur * 3)
    x0, y0, x1, y1 = bb
    x0, y0 = max(0, x0 - margin), max(0, y0 - margin)
    x1, y1 = min(img.width, x1 + margin), min(img.height, y1 + margin)
    w, h = x1 - x0, y1 - y0
    m = Image.new("L", (img.width + 2 * P, img.height + 2 * P), 0)
    ImageDraw.Draw(m).rounded_rectangle((x0 + P, y0 + P, x1 + P, y1 + P),
                                        radius=int(min(w, h) * 0.34 if radius is None else radius),
                                        fill=peak)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    plate = Image.new("RGBA", m.size, (18, 10, 8, 0))
    plate.putalpha(m)
    return plate, P


PLATE = {}


for _n, _peak, _bl in (("hl_title", 118, 90), ("hl_foundation", 106, 86)):
    for _l in LAYERS:
        if _l["name"] == _n:
            PLATE[_n] = make_plate(_l["img"], peak=_peak, blur=_bl, margin=66)

MASTHEAD = Image.open(os.path.join(A, "masthead.png")).convert("RGBA")
HEADS = [Image.open(os.path.join(A, f"head{i}.png")).convert("RGBA") for i in range(len(SCENES))]
PROGRESS = Image.open(os.path.join(A, "progress.png")).convert("RGBA")
ARROW = Image.open(os.path.join(A, "arrow.png")).convert("RGBA")
RING = Image.open(os.path.join(A, "ring.png")).convert("RGBA")
PILL = Image.open(os.path.join(A, "pill.png")).convert("RGBA")
ENDTYPE = Image.open(os.path.join(A, "endtype.png")).convert("RGBA")
CUT_TYPES = {i: Image.open(os.path.join(A, f"cut{i:02d}.png")).convert("RGBA")
             for i in range(1, len(CUTAWAYS) + 1)}
PROD = {t: Image.open(os.path.join(A, PRODUCTS[t][0] + ".png")).convert("RGBA")
        for t in PRODUCTS}

_soft = Image.new("L", (400, 400), 0)
ImageDraw.Draw(_soft).ellipse((4, 4, 395, 395), fill=255)
MED_MASK = _soft.filter(ImageFilter.GaussianBlur(2))

F_BIG = ImageFont.truetype(f"{FONTS}/@expo-google-fonts/space-grotesk/"
                           "700Bold/SpaceGrotesk_700Bold.ttf", 150)
PLATE_CUT = {i: make_plate(im, peak=116, blur=94, margin=86)
             for i, im in CUT_TYPES.items()}
PLATE_END = make_plate(ENDTYPE, peak=64, blur=104, margin=104)

F_SMALL = ImageFont.truetype(f"{FONTS}/@expo-google-fonts/inter/"
                             "300Light/Inter_300Light.ttf", 30)

# grain (tuiles)
GRAIN = []
rng = np.random.default_rng(2026)
for _ in range(10):
    g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    GRAIN.append(np.clip(g, -2.6, 2.6) / 2.6)

# ------------------------------------------------------------------ fonds cinéma
_bg_cache = {}
# voile : assombrit les bords (vignette) et pose la lumière dorée en haut à droite
VOILE = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_dv = ImageDraw.Draw(VOILE)
for y in range(H):
    t = y / (H - 1)
    _dv.line((0, y, W, y), fill=(14, 8, 6, int(150 + 60 * (1 - t) ** 1.4)))
_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_dg = ImageDraw.Draw(_glow)
for i in range(26, 0, -1):
    t = i / 26
    r = int(760 * t)
    a = int(30 * (1 - t) ** 2.2)
    if a:
        _dg.ellipse((X_R - r, 300 - r, X_R + r, 300 + r), fill=(233, 189, 124, a))
VOILE = Image.alpha_composite(VOILE, _glow.filter(ImageFilter.GaussianBlur(60)))
VIGN = Image.new("L", (W, H), 0)
_dvi = ImageDraw.Draw(VIGN)
for i in range(60, 0, -1):
    t = i / 60
    _dvi.ellipse((-W * 0.35 * t, -H * 0.28 * t, W + W * 0.35 * t, H + H * 0.28 * t),
                 fill=int(255 * (1 - t) ** 1.5 * 0.6))
VIGN = VIGN.filter(ImageFilter.GaussianBlur(70))


def cine_bg(key, frame):
    """Fond de scène fabriqué depuis une image du film : flou, miroir, lumière."""
    if key in _bg_cache:
        return _bg_cache[key]
    small = frame.convert("RGB").resize((W // 7, H // 7), Image.BILINEAR)
    bg = small.resize((W, H), Image.BICUBIC)
    bg = bg.filter(ImageFilter.GaussianBlur(26))
    # miroir vertical partiel : évite l'effet « tache »
    bg = Image.blend(bg, bg.transpose(Image.FLIP_TOP_BOTTOM), 0.22)
    # bokeh doré : quelques disques lumineux flous
    bok = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bok)
    r2 = np.random.default_rng(abs(hash(key)) % 9999)
    for _ in range(9):
        cx, cy = int(r2.uniform(0, W)), int(r2.uniform(120, H - 300))
        rad = int(r2.uniform(50, 190))
        a = int(r2.uniform(10, 26))
        db.ellipse((cx - rad, cy - rad * 0.8, cx + rad, cy + rad * 0.8), fill=(233, 189, 124, a))
    bg = Image.alpha_composite(bg.convert("RGBA"), bok.filter(ImageFilter.GaussianBlur(40)))
    bg = Image.composite(Image.new("RGBA", (W, H), (16, 9, 7, 255)), bg, VIGN)
    bg = Image.alpha_composite(bg, VOILE)
    _bg_cache[key] = bg
    return bg


def grain(frame, t):
    g = GRAIN[int(t * 25) % len(GRAIN)]
    a = np.asarray(frame, dtype=np.float32)
    luma = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    w = np.clip(1.0 - np.abs(luma / 255.0 - 0.5) * 1.1, 0.0, 1.0)[..., None]
    gi = np.asarray(Image.fromarray(((g + 1) * 127.5).astype(np.uint8)).resize((W, H),
                                                                              Image.BILINEAR),
                    dtype=np.float32)
    gi = (gi - 127.5) / 127.5
    a += gi[..., None] * 5.0 * w
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def halation(frame):
    a = np.asarray(frame, dtype=np.float32)
    luma = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    hi = np.clip((luma - 188.0) / 67.0, 0, 1)
    if hi.max() <= 0.01:
        return frame
    small = Image.fromarray((hi * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    bloom = small.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR)
    b = np.asarray(bloom, dtype=np.float32) / 255.0
    tint = np.array([1.0, 0.62, 0.36], dtype=np.float32)
    a = 255.0 - (255.0 - a) * (1.0 - 0.17 * b[..., None])
    a = a + (b * 26.0)[..., None] * tint
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def chroma(frame):
    a = np.asarray(frame)
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], 2, axis=1)
    out[..., 2] = np.roll(a[..., 2], -2, axis=1)
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
    near = min((abs(t - c) for c in CUTS), default=1.0)
    if near > 0.12:
        return frame
    p = 1 - near / 0.12
    k = 1 + int(15 * p * p)
    if k % 2 == 0:
        k += 1
    tr = frame.transpose(Image.ROTATE_90).filter(ImageFilter.BoxBlur(radius=k / 2))
    return tr.transpose(Image.ROTATE_270)


def ease_out(x):
    return 1 - (1 - x) ** 3


def layer_place(layer, t):
    img, anchor, pad = layer["img"], layer["anchor"], layer["pad"]
    cw, ch = img.width - 2 * pad, img.height - 2 * pad
    if anchor == "rt":
        return img, layer["x"] - cw - pad, layer["y"] - pad
    if anchor == "lb":
        return img, layer["x"] - pad, layer["y"] - ch - pad
    if anchor == "lt":
        return img, layer["x"] - pad, layer["y"] - pad
    return img, int(round(layer["x"] - img.width / 2)), int(round(layer["y"] - img.height / 2))


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
    if not (17.10 <= t <= 19.50):
        return
    p = ease_out(max(0.0, min(1.0, (t - 17.14) / 0.80)))   # 100 % atteint avant 18 s
    im = Image.new("RGBA", (700, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    txt = f"{int(round(p * 100))}%"
    d.text((676, 34), txt, font=F_BIG, fill=(10, 5, 4, 130), anchor="ra")
    d.text((674, 30), txt, font=F_BIG, fill=GOLD + (255,), anchor="ra")
    a = min(1.0, (t - 17.10) / 0.4, (19.50 - t) / 0.3)
    if a < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(im, (X_R - 700, 296))


def draw_arrow(base, t):
    if not (22.80 <= t <= 25.80):
        return
    base.alpha_composite(ARROW, (770 + int(7 * np.sin((t - 22.8) * 5.2)),
                                 1344 - ARROW.height // 2))


def active_cut(t):
    for i, c in enumerate(CUTAWAYS, start=1):
        if c[0] <= t <= c[1]:
            return i, c
    return None, None


def draw_cine_scene(base, raw, t):
    """Scène de coupe : fond construit depuis l'image + typo + visuel + médaillon."""
    idx, c = active_cut(t)
    if idx is None:
        return
    t0, t1, num, kicker, l1, l2, sub, accent, px, py, r = c
    bg = cine_bg(f"cut{idx}", raw)
    # respiration très lente du fond
    p = (t - t0) / max(0.01, t1 - t0)
    sc = 1.0 + 0.022 * ease_out(p)
    bgi = bg.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
    bgi = bgi.crop(((bgi.width - W) // 2, (bgi.height - H) // 2,
                    (bgi.width - W) // 2 + W, (bgi.height - H) // 2 + H))
    # fondu d'entrée / sortie global de la scène
    a = min(1.0, (t - t0) / 0.30, (t1 - t) / 0.24)
    if a < 1:
        bgi = bgi.copy()
        bgi.putalpha(bgi.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(bgi)

    if a <= 0.02:
        return

    # bloc typographique (montée douce + fondu)
    block = CUT_TYPES[idx]
    pad = PAD["cut01"]
    at = min(1.0, (t - t0 - 0.12) / 0.42)
    if at > 0:
        dy = int(round(30 * (1 - ease_out(at))))
        im = block
        if at < 1:
            im = block.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * at)))
        pl = PLATE_CUT[idx]
        if pl is not None:
            pe, poff = pl
            if at < 1:
                pe = pe.copy()
                pe.putalpha(pe.getchannel("A").point(lambda v: int(v * at)))
            base.alpha_composite(pe, (X_L - pad - poff, 470 - pad + dy - poff))
        base.alpha_composite(im, (X_L - pad, 470 - pad + dy))

    # visuel produit (flotte dans la lumière, ombre portée)
    t_prod = c[0]
    if t_prod in PROD:
        _, pxp, pyp, anim = PRODUCTS[t_prod]
        prod = PROD[t_prod]
        ap = min(1.0, max(0.0, (t - t0 - 0.35) / 0.5))
        if ap > 0:
            pp = 1.0 + 0.02 * ease_out(max(0.0, min(1.0, (t - t0) / 1.2)))
            im = prod.resize((int(prod.width * pp), int(prod.height * pp)), Image.LANCZOS) \
                if pp != 1.0 else prod
            x = pxp - im.width
            y = pyp - int(26 * (1 - ease_out(ap)))
            if ap < 1:
                im = im.copy()
                im.putalpha(im.getchannel("A").point(lambda v: int(v * ap)))
            base.alpha_composite(im, (x, y))

    # médaillon du sujet, cerclé d'or
    r_src = 330
    cx, cy = 456, 596
    box = (max(0, cx - r_src), max(0, cy - r_src), min(W, cx + r_src), min(H, cy + r_src))
    face = raw.crop(box).resize((2 * r, 2 * r), Image.LANCZOS)
    face.putalpha(MED_MASK.resize((2 * r, 2 * r), Image.LANCZOS))
    am = min(1.0, (t - t0 - 0.10) / 0.45)
    if am > 0.02:
        sc2 = 0.93 + 0.07 * ease_out(min(1.0, (t - t0 - 0.10) / 0.5))
        sd = int(2 * r * sc2)
        f2 = face.resize((sd, sd), Image.LANCZOS)
        ring = RING.resize((int(sd * 1.06), int(sd * 1.06)), Image.LANCZOS)
        if am < 1:
            f2 = f2.copy()
            f2.putalpha(f2.getchannel("A").point(lambda v: int(v * am)))
            ring = ring.copy()
            ring.putalpha(ring.getchannel("A").point(lambda v: int(v * am)))
        base.alpha_composite(f2, (int(px - sd / 2), int(py - sd / 2)))
        base.alpha_composite(ring, (int(px - ring.width / 2), int(py - ring.height / 2)))


def draw_endcard(base, raw, t):
    """Carte finale : plan large flouté + typographie serif pleine largeur + CTA."""
    t0, t1 = 25.85, 29.10
    if not (t0 <= t <= t1):
        return
    a = min(1.0, (t - t0) / 0.6, (t1 - t) / 0.6)
    bg = cine_bg("end", raw)
    p = (t - t0) / (t1 - t0)
    sc = 1.0 + 0.03 * ease_out(p)
    bgi = bg.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
    bgi = bgi.crop(((bgi.width - W) // 2, (bgi.height - H) // 2,
                    (bgi.width - W) // 2 + W, (bgi.height - H) // 2 + H))
    if a < 1:
        bgi = bgi.copy()
        bgi.putalpha(bgi.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(bgi)

    at = min(1.0, (t - t0 - 0.25) / 0.6)
    if at <= 0:
        return
    pad = PAD["endtype"]
    im = ENDTYPE
    if at < 1:
        im = ENDTYPE.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * at)))
    dy = int(round(24 * (1 - ease_out(at))))
    if PLATE_END is not None:
        pe, poff = PLATE_END
        if at < 1:
            pe = pe.copy()
            pe.putalpha(pe.getchannel("A").point(lambda v: int(v * at)))
        base.alpha_composite(pe, (X_L - pad - poff, 470 - pad + dy - poff))
    base.alpha_composite(im, (X_L - pad, 470 - pad + dy))

    # CTA doré + lien en bio
    ap = min(1.0, (t - t0 - 0.75) / 0.5)
    if ap > 0:
        pill = PILL
        if ap < 1:
            pill = PILL.copy()
            pill.putalpha(pill.getchannel("A").point(lambda v: int(v * ap)))
        base.alpha_composite(pill, (int(W / 2 - pill.width / 2), 1290))
        d = ImageDraw.Draw(base)
        txt = "link in bio"
        lw = d.textlength(txt, font=F_SMALL)
        d.text((W / 2 - lw / 2, 1442), txt, font=F_SMALL,
               fill=(241, 231, 215, int(255 * ap)))


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


# ------------------------------------------------------------------ ffmpeg
GRADE = ("scale=1080:1920:flags=lanczos,"
         "unsharp=5:5:0.55:3:3:0.0,"
         "eq=contrast=1.075:brightness=0.004:saturation=1.04:gamma=0.98,"
         "curves=master='0/0 0.18/0.155 0.5/0.52 0.8/0.84 1/1',"
         "colorbalance=rs=-0.016:gs=-0.008:bs=0.024:rm=0.012:gm=0.005:bm=-0.014:"
         "rh=0.034:gh=0.016:bh=-0.030,"
         "vignette=angle=PI/4.8:mode=forward,"
         f"tpad=stop_mode=clone:stop_duration={DURATION - 27.6:.2f}")

src = os.environ.get("ROCKWOOD_RUSH", os.path.join(WORK, "../AIDE-CHATGPT-main/video brut.mp4"))
vin = [FF, "-hide_banner", "-loglevel", "error", "-i", src, "-vf", GRADE,
       "-r", str(FPS), "-f", "rawvideo", "-pix_fmt", "rgb24", "-an", "-"]

vout = [FF, "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", MIX,
        "-filter_complex",
        f"[0:v]fade=t=out:st={FADE_START}:d={FADE_DUR},"
        f"format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a", "-t", str(DURATION),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", out_path]

env = dict(os.environ, FONTCONFIG_FILE=os.path.join(TOOLS, "fonts.conf"))
p_in = subprocess.Popen(vin, stdout=subprocess.PIPE, env=env)
p_out = subprocess.Popen(vout, stdin=subprocess.PIPE, env=env)

import json  # noqa: E402
words = json.load(open(WORDS, encoding="utf-8"))
cues = captions3.build(words)

frame_bytes = W * H * 3
done, n_frames = 0, int(round(DURATION * FPS))
step = max(1, n_frames // 12)

while True:
    buf = p_in.stdout.read(frame_bytes)
    if len(buf) < frame_bytes:
        break
    t = done / FPS

    if QC_TIMES and not any(abs(t - q) <= 1e-6 for q in QC_TIMES):
        done += 1
        continue

    base = Image.frombytes("RGB", (W, H), buf).convert("RGBA")
    raw = camera(base.convert("RGB"), t)       # image caméra (sert aux médaillons)

    framed = camera(base, t).convert("RGB")
    framed = whip(framed, t)
    framed = chroma(framed)
    framed = halation(framed)
    framed = grain(framed, t)
    out = framed.convert("RGBA")

    draw_cine_scene(out, raw, t)
    draw_endcard(out, raw, t)

    for layer in LAYERS:
        a = layer_alpha(layer, t)
        if a is None:
            continue
        img, x, y = layer_place(layer, t)
        sc, dx, dy = layer_transform(layer, t)
        x += dx
        im = img
        if layer["anim"] == "draw":
            p = min(1.0, (t - layer["t0"]) / 0.5)
            im = img.crop((0, 0, max(4, int(img.width * ease_out(p))), img.height))
        if sc != 1.0:
            im = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
            if layer["anchor"] == "c":
                x = int(round(layer["x"] - im.width / 2))
                y = int(round(layer["y"] - im.height / 2))
        if a < 1.0:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        pl = PLATE.get(layer["name"])
        if pl is not None:
            pe, poff = pl
            if a < 1.0:
                pe = pe.copy()
                pe.putalpha(pe.getchannel("A").point(lambda v: int(v * a)))
            out.alpha_composite(pe, (x - poff, y + dy - poff))
        out.alpha_composite(im, (x, y + dy))

    draw_count(out, t)
    draw_arrow(out, t)

    ci = captions3.active_index(cues, t)
    if ci is not None:
        captions3.draw(out, cues, t, ci)

    draw_chrome(out, t)

    if QC_TIMES:
        QC_FRAMES.append((t, out.convert("RGB").copy()))
    else:
        p_out.stdin.write(out.convert("RGB").tobytes())
    done += 1
    if done % step == 0:
        print(f"  {done}/{n_frames} images…", flush=True)

if QC_TIMES:
    p_in.stdout.close()
    p_in.kill()
    p_out.stdin.close()
    p_out.kill()
    tw, th, cols = 390, 693, min(5, len(QC_FRAMES))
    rows = -(-len(QC_FRAMES) // cols)
    sh = Image.new("RGB", (cols * tw, rows * th), (8, 8, 8))
    d = ImageDraw.Draw(sh)
    for i, (tt, im) in enumerate(QC_FRAMES):
        cx, cy = (i % cols) * tw, (i // cols) * th
        sh.paste(im.resize((tw, th)), (cx, cy))
        d.text((cx + 8, cy + 8), f"{tt:.1f}s", fill=(255, 240, 160))
    sh.save(os.environ.get("V5_QC_OUT", os.path.join(WORK, "qc_preview.jpg")), quality=92)
    print(f"QC : {len(QC_FRAMES)} images -> {os.environ.get('V5_QC_OUT')}")
    sys.exit(0)

p_in.stdout.close()
p_in.wait()
p_out.stdin.close()
p_out.wait()
print(f"{done} images ({done / FPS:.2f}s) -> {out_path}")
print("encodage :", p_out.returncode, "| décodage :", p_in.returncode)
