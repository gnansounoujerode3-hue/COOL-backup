#!/usr/bin/env python3
"""Digitaward — Pack 1 500 modèles PowerPoint · publicité Facebook 9:16.

Identité reprise des visuels fournis :
    bleu royal #0030D0 → navy #001070, jaune #FFC21A / #FFB817, blanc #FFFFFF
    orange PowerPoint #D24726, typo Poppins (ExtraBold/SemiBold) + Manrope
    vagues lumineuses blanches, cartes flottantes, pack 3D

45 s · 1080x1920 · 30 fps · voix off FR + musique + SFX.

    python3 build_film.py --preview /tmp/preview.jpg
    python3 build_film.py
"""
import argparse
import math
import os
import subprocess
import sys
import wave as wavemod

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy.signal import butter, sosfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

W, H, FPS, SR = 1080, 1920, 30, 48000
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
IMG = os.path.join(PROJECT, "assets", "img")
AUD = os.path.join(PROJECT, "assets", "audio")
FILM = os.path.join(PROJECT, "film")
os.makedirs(FILM, exist_ok=True)
OUT = os.path.join(FILM, "digitaward-pack-1500-powerpoint-fb-9x16.mp4")
MIX = os.path.join(AUD, "master_mix.wav")
TMP = "/tmp/dw_video.mp4"

# ---------------------------------------------------------------- palette
NAVY = (0, 16, 112)
ROYAL = (0, 48, 208)
ROYAL_BRIGHT = (0, 64, 224)
YELLOW = (255, 194, 26)
YELLOW_DEEP = (255, 184, 23)
ORANGE = (210, 71, 38)
WHITE = (255, 255, 255)
ICE = (232, 240, 255)
MUTED = (176, 194, 240)
GREY = (120, 128, 148)

FB = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
FONTS = {
    "xb": f"{FB}/poppins/800ExtraBold/Poppins_800ExtraBold.ttf",
    "b": f"{FB}/poppins/700Bold/Poppins_700Bold.ttf",
    "sb": f"{FB}/poppins/600SemiBold/Poppins_600SemiBold.ttf",
    "m": f"{FB}/manrope/700Bold/Manrope_700Bold.ttf",
    "r": f"{FB}/manrope/600SemiBold/Manrope_600SemiBold.ttf",
}
M_ = 64
CW = W - M_ * 2

# scènes : (nom, début, fin)
SCENES = [
    ("hook", 0.00, 6.60),
    ("pain", 6.60, 12.80),
    ("turn", 12.80, 17.60),
    ("reveal", 17.60, 24.80),
    ("slides", 24.80, 31.40),
    ("benefit", 31.40, 35.60),
    ("offer", 35.60, 41.20),
    ("end", 41.20, 45.20),
]
TOTAL = SCENES[-1][2]
VO = [("vo1.mp3", 0.55, 1.00), ("vo2.mp3", 7.00, 1.02), ("vo3.mp3", 13.00, 1.00),
      ("vo4.mp3", 18.00, 1.05), ("vo5.mp3", 25.20, 1.02), ("vo6.mp3", 31.80, 1.02),
      ("vo7.mp3", 36.00, 1.05)]

_F = {}


def F(kind, size):
    size = max(8, int(round(size)))
    k = (kind, size)
    if k not in _F:
        # Pas de repli silencieux vers la bitmap 10 px : un rendu sans Poppins
        # ressemble à une vidéo cassée, et le défaut se voit à l'image seulement.
        if not os.path.exists(FONTS[kind]):
            raise FileNotFoundError(
                f"Police absente : {FONTS[kind]}\n"
                "Installe les paquets :\n"
                "  mkdir -p /tmp/work_cache/fonts && cd /tmp/work_cache/fonts\n"
                "  npm i @expo-google-fonts/poppins @expo-google-fonts/manrope"
            )
        _F[k] = ImageFont.truetype(FONTS[kind], size)
    return _F[k]


def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def prog(t, start, dur):
    return clamp01((t - start) / max(dur, 1e-4))


def eo(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def eob(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 5


def eio(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def spring(t):
    t = clamp01(t)
    return 1 - math.exp(-7.0 * t) * math.cos(13.0 * t)


def c_(c, a=255):
    return (c[0], c[1], c[2], int(max(0, min(255, a))))


def tl(d, text, f, tracking=0.0):
    if not text:
        return 0.0
    return sum(d.textlength(ch, font=f) + tracking for ch in text) - tracking


def tracked(d, xy, text, f, fill, tracking=0.0, center=None):
    x, y = xy if center is None else (xy[0] - tl(d, text, f, tracking) / 2, xy[1])
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tracking


def wrap(text, f, maxw, d, tracking=0.0):
    lines = []
    for block in text.split("\n"):
        cur = ""
        for w_ in block.split(" "):
            test = (cur + " " + w_).strip()
            if tl(d, test, f, tracking) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
    return lines


def para(d, text, f, fill, x, y, maxw, lh=1.28, tracking=0.0, center=False, max_lines=None):
    lines = wrap(text, f, maxw, d, tracking)
    if max_lines:
        lines = lines[:max_lines]
    step = int(f.size * lh)
    for i, ln in enumerate(lines):
        if center:
            tracked(d, (x + maxw / 2, y + i * step), ln, f, fill, tracking, center=x + maxw / 2)
        else:
            tracked(d, (x, y + i * step), ln, f, fill, tracking)
    return len(lines) * step


def ac(canvas, im, xy=(0, 0)):
    canvas.alpha_composite(im, (int(xy[0]), int(xy[1])))


def alpha(im, a):
    if a >= .999:
        return im
    arr = np.array(im)
    arr[..., 3] = (arr[..., 3].astype(np.float32) * clamp01(a)).astype(np.uint8)
    return Image.fromarray(arr)


def rounded(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    return m


_SH = {}


def shadow(w, h, r, blur, a):
    k = (w, h, r, blur, a)
    if k not in _SH:
        p = blur * 2
        im = Image.new("RGBA", (w + p * 2, h + p * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([p, p, p + w - 1, p + h - 1], r, fill=(0, 0, 0, a))
        _SH[k] = im.filter(ImageFilter.GaussianBlur(blur))
    return _SH[k]


def place(canvas, im, x, y, r=26, blur=30, sa=150, dy=18, scale=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    sh = shadow(im.width, im.height, r, blur, sa)
    ac(canvas, sh, ((x - blur * 2, y - blur * 2 + dy)))
    ac(canvas, im, ((x, y)))


def pill(text, size=26, fg=WHITE, bg=(255, 255, 255, 30), border=(255, 255, 255, 80),
         pad_x=26, pad_y=14, tracking=0.0, kind="sb"):
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = F(kind, size)
    tw = tl(tmp, text, f, tracking)
    h = int(size * 1.5) + pad_y * 2
    w = int(tw + pad_x * 2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=bg, outline=border, width=2)
    tracked(d, (pad_x, (h - size * 1.32) / 2), text, f, fg, tracking)
    return im


# ------------------------------------------------------------------ décor
def wave(d, cx, cy, rw, rh, a, width=3, start=200, end=340):
    d.arc([cx - rw, cy - rh, cx + rw, cy + rh], start, end, fill=(255, 255, 255, int(a)),
          width=width)


def build_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # dégradé navy -> royal
    f = np.clip(yy / H, 0, 1)
    img = np.zeros((H, W, 3), np.float32)
    stops_y = [0.0, 0.35, 0.72, 1.0]
    stops_c = [(0, 36, 170), (0, 48, 214), (0, 34, 160), (0, 14, 96)]
    for ch in range(3):
        img[..., ch] = np.interp(f, stops_y, [c[ch] for c in stops_c])
    # halo lumineux haut-gauche
    d2 = ((xx - W * 0.18) ** 2 + (yy - H * 0.06) ** 2) / (900 ** 2)
    img += (np.exp(-d2 * 1.5) * 0.30)[..., None] * np.array((70, 130, 255), np.float32)
    # halo jaune bas
    d3 = ((xx - W * 0.85) ** 2 + (yy - H * 0.93) ** 2) / (700 ** 2)
    img += (np.exp(-d3 * 2.0) * 0.13)[..., None] * np.array((255, 194, 26), np.float32)
    # vignette
    vx = (xx - W / 2) / (W * .8)
    vy = (yy - H / 2) / (H * .8)
    img *= np.clip(1 - .34 * (vx * vx + vy * vy), .42, 1)[..., None]

    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    # vagues lumineuses (motif du visuel)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (cx, cy, rw, rh, a) in enumerate([
            (W * .95, H * .16, 700, 520, 26), (W * .95, H * .16, 780, 600, 16),
            (W * .05, H * .82, 760, 620, 20), (W * .05, H * .82, 860, 700, 12)]):
        # pas d'arc passant par le sommet de l'ellipse : sinon une ligne droite traverse le cadre
        wave(d, cx, cy, rw, rh, a, 3, *((170, 350) if i < 2 else (58, 202 - i * 4)))
    base.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))

    # grille de points discrète en bas à droite (comme le visuel)
    dots = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for iy in range(0, 240, 26):
        for ix in range(0, 240, 26):
            dd.ellipse([ix, iy, ix + 5, iy + 5], fill=(255, 255, 255, 30))
    base.alpha_composite(dots, (W - 300, H - 340))

    # grain léger
    rng = np.random.default_rng(5)
    n = rng.normal(0, 5.0, (H, W, 1)).astype(np.float32)
    g = np.full((H, W, 4), 0, np.uint8)
    g[..., :3] = np.clip(128 + np.repeat(n, 3, 2), 0, 255).astype(np.uint8)
    g[..., 3] = 14
    base.alpha_composite(Image.fromarray(g))
    return base


def glow_blob(canvas, cx, cy, r, color, a=90, blur=80):
    lay = Image.new("RGBA", (int(r * 2 + blur * 2), int(r * 2 + blur * 2)), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([blur, blur, blur + r * 2, blur + r * 2], fill=c_(color, a))
    ac(canvas, lay.filter(ImageFilter.GaussianBlur(blur)), ((cx - r - blur, cy - r - blur)))


IMG_CACHE = {}


def load(name, scale=1.0):
    k = (name, scale)
    if k not in IMG_CACHE:
        im = Image.open(os.path.join(IMG, name)).convert("RGBA")
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        IMG_CACHE[k] = im
    return IMG_CACHE[k]


def logo_on_card(w=360):
    """Le logo du visuel est bleu sur blanc : on le pose sur une carte blanche."""
    lg = Image.open(os.path.join(IMG, "logo_raw.png")).convert("RGB")
    ratio = lg.height / lg.width
    iw = w - 44
    ih = int(iw * ratio)
    card = Image.new("RGBA", (w, ih + 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, w - 1, card.height - 1], 22, fill=(255, 255, 255, 255))
    card.paste(lg.resize((iw, ih), Image.LANCZOS), (22, 22))
    return card


def shot(name, w, feather=34):
    """Capture de diapositive aux bords fondus : se fond dans le fond, sans cadre."""
    im = load(name)
    h = int(w * im.height / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w, h), 0)
    pad = max(2, feather)
    ImageDraw.Draw(m).rounded_rectangle([pad, pad, w - pad, h - pad], 10, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(pad * 0.75))
    out = im.copy()
    out.putalpha(ImageChops.multiply(im.getchannel("A"), m))
    return out


def slide_card(name, w, angle=0.0):
    im = load(name)
    h = int(w * im.height / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    mask = rounded(w, h, 16)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 16, outline=(255, 255, 255, 120), width=2)
    if angle:
        out = out.rotate(angle, resample=Image.BICUBIC, expand=True)
    return out


# ------------------------------------------------------------------ scènes
def s_hook(d, canvas, t, lt):
    a = eo(prog(lt, .04, .4))
    # badge d'accroche
    ba = eob(prog(lt, .10, .5))
    if ba > 0:
        p = pill("POWERPOINT · LE CASSE-TÊTE", size=21, fg=c_(YELLOW, 245),
                 bg=(255, 255, 255, 22), border=c_(YELLOW, 90), tracking=2.0)
        ac(canvas, alpha(p, ba), ((M_, 250 + (1 - ba) * 14)))

    lines = [("3 heures", WHITE), ("perdues.", YELLOW)]
    y = 330
    for i, (txt, colr) in enumerate(lines):
        ra = eob(prog(lt, .16 + i * .13, .6))
        if ra <= 0:
            continue
        size = 148
        f = F("xb", size)
        lay = Image.new("L", (W, int(size * 1.5)), 0)
        tracked(ImageDraw.Draw(lay), (0, 8), txt, f, 255, -4)
        cm = Image.new("RGBA", lay.size, c_(colr, 255))
        cm.putalpha(lay)
        keep = Image.new("L", lay.size, 0)
        ImageDraw.Draw(keep).rectangle([0, 0, W, lay.height - int((1 - ra) * size * 1.1)], fill=255)
        cm.putalpha(ImageChops.multiply(cm.getchannel("A"), keep))
        ac(canvas, cm, ((M_, y + (1 - ra) * size)))
        y += int(size * 1.02)

    sa = eo(prog(lt, .55, .5))
    if sa > 0:
        para(d, "Tu ouvres PowerPoint…\net tu ne sais pas par où commencer.",
             F("r", 33), c_(ICE, 240 * sa), M_, 672, 900, lh=1.34)

    # faux slide "brouillon" gris
    ma = eob(prog(lt, .95, .7))
    if ma > 0:
        mw, mh = 750, 452
        card = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, mw - 1, mh - 1], 20, fill=(236, 238, 244, 255))
        cd.rectangle([0, 0, mw - 1, 54], fill=(214, 217, 226, 255))
        for i, cc in enumerate([(198, 201, 210)] * 3):
            cd.ellipse([18 + i * 22, 20, 32 + i * 22, 34], fill=c_(cc, 255))
        # contenu "raté"
        cd.rectangle([40, 92, 380, 128], fill=(150, 154, 168, 255))
        cd.rectangle([40, 148, 520, 168], fill=(184, 187, 198, 255))
        cd.rectangle([40, 186, 470, 206], fill=(184, 187, 198, 255))
        cd.rectangle([40, 240, 300, 330], fill=(200, 203, 212, 255))
        cd.rectangle([320, 240, 560, 330], fill=(200, 203, 212, 255))
        cd.rectangle([40, 372, 640, 392], fill=(184, 187, 198, 255))
        cd.rectangle([40, 406, 560, 426], fill=(184, 187, 198, 255))
        # curseur + toast "en cours…"
        cd.rounded_rectangle([mw - 254, mh - 76, mw - 34, mh - 30], 12, fill=(255, 92, 92, 255))
        tracked(cd, (mw - 236, mh - 68), "3 h 12", F("b", 24), c_(WHITE, 255))
        g = card.filter(ImageFilter.GaussianBlur(0))
        place(canvas, alpha(g, ma), (W - mw) / 2, 832 + (1 - ma) * 30)

    # petits mots "couleurs / textes / images" qui tournent
    words = [("couleurs", -5, 1356), ("textes", 3, 1356), ("images", -4, 1356)]
    for i, (w_, ang, yy) in enumerate(words):
        wa = eob(prog(lt, 1.5 + i * .16, .5))
        if wa <= 0:
            continue
        p = pill(w_, size=23, fg=c_(WHITE, 235), bg=(255, 255, 255, 26),
                 border=(255, 255, 255, 70), pad_x=22, pad_y=12)
        p = p.rotate(ang, resample=Image.BICUBIC, expand=True)
        x = [108, 400, 690][i]
        ac(canvas, alpha(p, wa), ((x, yy + (1 - wa) * 14)))
    ta = eo(prog(lt, 2.0, .6))
    if ta > 0:
        tracked(d, (W / 2, 1520), "…et le résultat n'est toujours pas celui que tu imaginais.",
                F("r", 25), c_(ICE, 200 * ta), 0, center=W / 2)


def s_pain(d, canvas, t, lt):
    a = eo(prog(lt, .04, .4))
    if a > 0:
        p = pill("LE VRAI PROBLÈME", size=20, fg=c_(YELLOW, 245),
                 bg=(255, 255, 255, 22), border=c_(YELLOW, 90), tracking=2.0)
        ac(canvas, alpha(p, a), ((M_, 236)))

    ra = eob(prog(lt, .10, .55))
    if ra > 0:
        d.text((M_, 300), "Tu passes des heures", font=F("xb", 70), fill=c_(WHITE, 255 * ra))
        d.text((M_, 380), "à tout retoucher.", font=F("xb", 70), fill=c_(WHITE, 255 * ra))
        d.text((M_, 470), "…et ça ne te plaît pas.", font=F("sb", 40), fill=c_(ICE, 235 * ra))

    # empilement de diapos qui tournent (les vrais screenshots)
    items = [("slide_quatre", 560, -7, 610), ("slide_clarte", 520, 6, 760),
             ("slide_vision", 560, -4, 900)]
    for i, (nm, wd, ang, yy) in enumerate(items):
        ia = eob(prog(lt, .30 + i * .18, .7))
        if ia <= 0:
            continue
        card = slide_card(f"{nm}.png", wd, ang)
        x = (W - card.width) / 2 + math.sin(lt * .8 + i) * 8
        place(canvas, alpha(card, ia), x, yy + (1 - ia) * 40, r=16, blur=26, sa=130)

    # chrono qui tourne
    ca = eob(prog(lt, 1.5, .6))
    if ca > 0:
        cw_, ch_ = 380, 128
        card = Image.new("RGBA", (cw_, ch_), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw_ - 1, ch_ - 1], 26, fill=(0, 20, 120, 235),
                             outline=(255, 255, 255, 60), width=2)
        secs = 3 * 3600 + int(12 * 60 * eo(prog(lt, 1.5, 1.2)))
        txt = f"{secs // 3600} h {secs % 3600 // 60:02d}"
        cd.text((26, 22), txt, font=F("xb", 56), fill=c_(ORANGE, 255))
        tracked(cd, (28, 88), "TEMPS PERDU", F("sb", 16), c_(ICE, 225), 2.4)
        ac(canvas, alpha(card, ca), ((W - cw_) / 2, 1246 + (1 - ca) * 16))


    la = eo(prog(lt, 2.4, .7))
    if la > 0:
        para(d, "Pendant ce temps, les autres présentent des slides modernes, nettes, organisées.",
             F("r", 25), c_(ICE, 215 * la), M_, 1408, 940, lh=1.34)
    ba = eob(prog(lt, 2.35, .7))
    if ba > 0:
        tracked(d, (W / 2, 1612), "Et pendant ce temps, les autres avancent.",
                F("sb", 30), c_(YELLOW, 235 * ba), 0, center=W / 2)


def s_turn(d, canvas, t, lt):
    # flash blanc puis bascule vers un fond clair
    fa = eo(prog(lt, 0.0, .45))
    glow_blob(canvas, W / 2, 700, 420, (255, 255, 255), 110, 90)

    a = eob(prog(lt, .10, .5))
    if a > 0:
        p = pill("ET SI…", size=22, fg=c_(NAVY, 255), bg=c_(YELLOW, 255),
                 border=c_(YELLOW, 255), tracking=3.0, kind="b")
        ac(canvas, alpha(p, a), (((W - p.width) / 2, 560 + (1 - a) * 16)))

    ra = eob(prog(lt, .22, .7))
    if ra > 0:
        para(d, "Et si tu pouvais obtenir\nun rendu professionnel\nsans repartir de zéro ?",
             F("xb", 74), c_(WHITE, 255 * ra), M_, 700, 940, lh=1.24, center=True, tracking=-1.5)

    qa = eo(prog(lt, 1.15, .65))
    if qa > 0:
        # trois atouts
        items = [("Sans partir de zéro", YELLOW), ("En quelques minutes", WHITE),
                 ("Rendu pro garanti", YELLOW)]
        y = 1330
        for i, (txt, colr) in enumerate(items):
            ia = eob(prog(lt, 1.15 + i * .16, .5))
            if ia <= 0:
                continue
            yy = y + i * 92 + (1 - ia) * 14
            d.ellipse([M_, yy + 8, M_ + 34, yy + 42], fill=c_(YELLOW, 235 * ia))
            d.line([(M_ + 10, yy + 25), (M_ + 17, yy + 32), (M_ + 27, yy + 17)],
                   fill=c_(NAVY, 255 * ia), width=4)
            d.text((M_ + 56, yy), txt, font=F("sb", 38), fill=c_(colr, 245 * ia))

    ta = eo(prog(lt, 1.9, .6))
    if ta > 0:
        d.line([(M_, 1620), (W - M_, 1620)], fill=c_(WHITE, 55 * ta), width=2)
        items = [("1 500", "modèles"), ("100 %", "modifiable"), ("15", "styles")]
        for i, (v, lbl) in enumerate(items):
            ia = eob(prog(lt, 1.95 + i * .1, .45))
            if ia <= 0:
                continue
            x = M_ + i * 300
            tracked(d, (x, 1656), v, F("xb", 46), c_(YELLOW, 250 * ia), -1.5)
            tracked(d, (x, 1714), lbl.upper(), F("sb", 15), c_(ICE, 205 * ia), 2.4)


def s_reveal(d, canvas, t, lt):
    a = eo(prog(lt, .04, .4))
    if a > 0:
        p = pill("LE PACK DIGITAWARD", size=20, fg=c_(NAVY, 255), bg=c_(YELLOW, 255),
                 border=c_(YELLOW, 255), tracking=2.6, kind="b")
        ac(canvas, alpha(p, a), (((W - p.width) / 2, 210)))

    # pack 3D
    ba = spring(prog(lt, .10, .85))
    if ba > 0:
        box = load("box.png")
        bw = int(700 * (0.86 + 0.14 * ba))
        bh = int(box.height * bw / box.width)
        box = box.resize((bw, bh), Image.LANCZOS)
        box = alpha(box, min(1, ba * 1.6))
        glow_blob(canvas, W / 2, 760, 300, (120, 180, 255), 90, 90)
        place(canvas, box, (W - bw) / 2, 300 + (1 - ba) * 90, r=8, blur=34, sa=150, dy=24)

    # compteur 1 500
    ca = eob(prog(lt, .95, .7))
    if ca > 0:
        val = int(round(1500 * eob(prog(lt, .95, 1.1))))
        txt = f"{val:,}".replace(",", " ")
        f = F("xb", 150)
        wpx = tl(d, txt, f, -4)
        tracked(d, ((W - wpx) / 2, 1105), txt, f, c_(YELLOW, 255 * ca), -4)
        sub = "MODÈLES POWERPOINT"
        tracked(d, ((W - tl(d, sub, F("b", 32), 4)) / 2, 1262), sub,
                F("b", 32), c_(WHITE, 250 * ca), 4)

    # trois preuves
    badges = [("Gain\nde temps", "⚡"), ("Qualité\npro", "◆"), ("100 %\nmodifiable", "⚙")]
    for i, (lbl, ic) in enumerate(badges):
        ia = eob(prog(lt, 1.7 + i * .14, .55))
        if ia <= 0:
            continue
        bw_, bh_ = 296, 150
        card = Image.new("RGBA", (bw_, bh_), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, bw_ - 1, bh_ - 1], 22, fill=(255, 255, 255, 26),
                             outline=(255, 255, 255, 70), width=2)
        # icône simple dessinée
        cx = bw_ / 2
        if i == 0:
            cd.polygon([(cx + 2, 16), (cx - 14, 46), (cx - 2, 46), (cx - 8, 74), (cx + 16, 38),
                        (cx + 2, 38)], fill=c_(YELLOW, 245))
        elif i == 1:
            cd.polygon([(cx, 16), (cx + 22, 40), (cx, 74), (cx - 22, 40)], outline=c_(YELLOW, 245), width=3)
        else:
            cd.ellipse([cx - 13, 28, cx + 13, 54], outline=c_(YELLOW, 245), width=3)
            cd.ellipse([cx - 4, 37, cx + 4, 45], fill=c_(YELLOW, 245))
        for j, ln in enumerate(lbl.split("\n")):
            tracked(cd, (cx, 86 + j * 26), ln, F("sb", 22), c_(WHITE, 245 * ia), 0, center=cx)
        ac(canvas, alpha(card, ia), ((M_ + i * 316, 1452 + (1 - ia) * 18)))


def s_slides(d, canvas, t, lt):
    a = eo(prog(lt, .04, .4))
    if a > 0:
        p = pill("15 STYLES · DES DIZAINES DE MISES EN PAGE", size=18, fg=c_(NAVY, 255),
                 bg=c_(YELLOW, 255), border=c_(YELLOW, 255), tracking=1.6, kind="b")
        ac(canvas, alpha(p, a), (((W - p.width) / 2, 200)))

    ra = eob(prog(lt, .10, .55))
    if ra > 0:
        d.text((M_, 260), "Diapositives animées,", font=F("xb", 62), fill=c_(WHITE, 255 * ra))
        d.text((M_, 332), "prêtes à personnaliser.", font=F("xb", 62), fill=c_(YELLOW, 255 * ra))

    # collage de vraies captures, bords fondus (les crops sont déjà inclinés)
    fan = [("slide_racontez", 520, 30, 424), ("slide_merci", 500, 548, 664),
           ("slide_chiffres", 520, 44, 906), ("slide_quatre", 500, 536, 1152)]
    for i, (nm, wd, x, yy) in enumerate(fan):
        sa = eob(prog(lt, .20 + i * .12, .7))
        if sa <= 0:
            continue
        im = shot(f"{nm}.png", wd)
        x = max(18, min(x, W - im.width - 18))
        place(canvas, alpha(im, sa), x, yy + (1 - sa) * 30, r=10, blur=30, sa=140, dy=22)

    la = eo(prog(lt, 1.5, .6))
    if la > 0:
        tags = ["Exposés", "Soutenances", "Formations", "Réunions"]
        x = M_
        for i, s_ in enumerate(tags):
            ia = eob(prog(lt, 1.5 + i * .1, .45))
            if ia <= 0:
                continue
            p = pill(s_, size=20, fg=c_(NAVY, 255), bg=(255, 255, 255, 235),
                     border=(255, 255, 255, 255), pad_x=20, pad_y=11)
            if x + p.width > W - M_:
                break
            ac(canvas, alpha(p, ia), ((x, 1566 + (1 - ia) * 12)))
            x += p.width + 10


def s_benefit(d, canvas, t, lt):
    glow_blob(canvas, W / 2, 900, 380, (255, 255, 255), 70, 100)
    big = [("Moins de temps", WHITE), ("à concevoir.", WHITE),
           ("Plus de temps", YELLOW), ("pour convaincre.", YELLOW)]
    y = 452
    for i, (txt, colr) in enumerate(big):
        ra = eob(prog(lt, .08 + i * .13, .55))
        if ra <= 0:
            continue
        size = 78 if i % 2 == 0 else 78
        f = F("xb", size)
        lay = Image.new("L", (W, int(size * 1.5)), 0)
        tracked(ImageDraw.Draw(lay), (0, 8), txt, f, 255, -2.5)
        cm = Image.new("RGBA", lay.size, c_(colr, 255))
        cm.putalpha(lay)
        ac(canvas, alpha(cm, ra), ((M_, y + (1 - ra) * 30)))
        y += int(size * 1.16)

    la = eo(prog(lt, 1.0, .7))
    if la > 0:
        d.line([(M_, 1000), (W - M_, 1000)], fill=c_(WHITE, 60 * la), width=2)
        para(d, "Tes idées méritent des slides à la hauteur de tes efforts.",
             F("r", 32), c_(ICE, 235 * la), M_, 1040, 900, lh=1.4)

    # petit pack + logo
    ba = eob(prog(lt, 1.25, .7))
    if ba > 0:
        box = load("box.png")
        bw = 300
        bh = int(box.height * bw / box.width)
        place(canvas, alpha(box.resize((bw, bh), Image.LANCZOS), ba), (W - bw) / 2, 1188, r=6, blur=26, sa=120)
        lc = logo_on_card(300)
        ac(canvas, alpha(lc, ba), (((W - lc.width) / 2, 1548)))


def s_offer(d, canvas, t, lt):
    a = eo(prog(lt, .04, .4))
    if a > 0:
        p = pill("OFFRE SPÉCIALE · PRÉVENTE", size=21, fg=c_(NAVY, 255), bg=c_(YELLOW, 255),
                 border=c_(YELLOW, 255), tracking=2.0, kind="b")
        ac(canvas, alpha(p, a), (((W - p.width) / 2, 250)))

    ra = eob(prog(lt, .10, .55))
    if ra > 0:
        d.text((M_, 316), "Réserve ton pack", font=F("xb", 72), fill=c_(WHITE, 255 * ra))
        d.text((M_, 400), "dès maintenant.", font=F("xb", 72), fill=c_(YELLOW, 255 * ra))

    # carte livraison
    ca = eob(prog(lt, .40, .6))
    if ca > 0:
        cw_, ch_ = CW, 200
        card = Image.new("RGBA", (cw_, ch_), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw_ - 1, ch_ - 1], 26, fill=(255, 255, 255, 245))
        cd.ellipse([30, 34, 96, 100], fill=(232, 240, 255, 255))
        # icône colis
        cd.rectangle([48, 56, 78, 78], outline=c_(ROYAL, 255), width=3)
        cd.line([(48, 56), (63, 46), (78, 56)], fill=c_(ROYAL, 255), width=3)
        cd.line([(63, 46), (63, 70)], fill=c_(ROYAL, 255), width=3)
        tracked(cd, (122, 34), "LIVRAISON SOUS 24 H", F("b", 20), c_(ROYAL, 255), 2.2)
        tracked(cd, (122, 70), "après confirmation de ta commande", F("r", 26), c_(NAVY, 235), 0)
        tracked(cd, (122, 116), "Accès à la collection complète dès finalisation", F("r", 22),
                (110, 120, 145, 255), 0)
        ac(canvas, alpha(card, ca), (M_, 508 + (1 - ca) * 20))

    # quatre bénéfices
    rows = ["1 500 modèles PowerPoint", "Diapositives animées", "Entièrement modifiables",
            "Styles variés pour tous tes besoins"]
    for i, s_ in enumerate(rows):
        ia = eob(prog(lt, .70 + i * .11, .45))
        if ia <= 0:
            continue
        y = 748 + i * 72 + (1 - ia) * 12
        d.ellipse([M_, y + 6, M_ + 32, y + 38], fill=c_(YELLOW, 240 * ia))
        d.line([(M_ + 9, y + 22), (M_ + 15, y + 29), (M_ + 25, y + 15)], fill=c_(NAVY, 255 * ia), width=4)
        d.text((M_ + 50, y), s_, font=F("sb", 31), fill=c_(WHITE, 245 * ia))

    # CTA jaune
    ga = eob(prog(lt, 1.25, .6))
    if ga > 0:
        bw_, bh_ = CW, 116
        btn = Image.new("RGBA", (bw_, bh_), (0, 0, 0, 0))
        arr = np.zeros((bh_, bw_, 4), np.uint8)
        for ch in range(3):
            arr[..., ch] = np.linspace(255, 240, bh_)[:, None].astype(np.uint8)
            arr[..., ch] = np.clip(arr[..., ch].astype(int) - (0 if ch else 0), 0, 255)
        arr[..., 0] = 255
        arr[..., 1] = np.linspace(214, 196, bh_)[:, None].astype(np.uint8)
        arr[..., 2] = 26
        arr[..., 3] = 255
        grad = Image.fromarray(arr)
        btn.paste(grad, (0, 0), rounded(bw_, bh_, 28))
        bd = ImageDraw.Draw(btn)
        # icône téléchargement
        bd.line([(66, 26), (66, 62)], fill=c_(NAVY, 255), width=6)
        bd.polygon([(66, 76), (50, 56), (82, 56)], fill=c_(NAVY, 255))
        bd.line([(44, 84), (88, 84)], fill=c_(NAVY, 255), width=6)
        tracked(bd, (116, 26), "OBTENEZ VOTRE PACK", F("xb", 40), c_(NAVY, 255), 0.5)
        tracked(bd, (116, 74), "Commande maintenant · livraison 24 h", F("r", 20),
                (26, 40, 90, 235), 0)
        glow_blob(canvas, W / 2, 1332, 300, (255, 194, 26), 70, 70)
        ac(canvas, alpha(btn, ga), ((M_, 1252 + (1 - ga) * 18)))

    sa = eo(prog(lt, 2.0, .7))
    if sa > 0:
        lc = logo_on_card(300)
        ac(canvas, alpha(lc, sa), (((W - lc.width) / 2, 1424)))
        tracked(d, (W / 2, 1600), "Le savoir à portée de clic.", F("r", 24),
                c_(ICE, 220 * sa), 0, center=W / 2)


def s_end(d, canvas, t, lt):
    a = eob(prog(lt, .05, .5))
    if a > 0:
        lc = logo_on_card(340)
        ac(canvas, alpha(lc, a), (((W - lc.width) / 2, 236 + (1 - a) * 18)))

    ba = eob(prog(lt, .18, .7))
    if ba > 0:
        box = load("box.png")
        bw = 420
        bh = int(box.height * bw / box.width)
        glow_blob(canvas, W / 2, 800, 300, (150, 195, 255), 80, 90)
        place(canvas, alpha(box.resize((bw, bh), Image.LANCZOS), ba), (W - bw) / 2,
              400 + (1 - ba) * 34, r=6, blur=28, sa=130)

    ra = eob(prog(lt, .50, .6))
    if ra > 0:
        para(d, "1 500 modèles PowerPoint", F("xb", 60), c_(WHITE, 255 * ra), M_, 1084, 950,
             lh=1.18, center=True, tracking=-1.2)
        para(d, "animés et modifiables", F("sb", 40), c_(YELLOW, 250 * ra), M_, 1156, 950,
             lh=1.18, center=True)

    ca = eob(prog(lt, .80, .55))
    if ca > 0:
        p = pill("Commande ton pack maintenant", size=33, fg=c_(NAVY, 255), bg=c_(YELLOW, 255),
                 border=(255, 255, 255, 255), pad_x=40, pad_y=24, kind="b")
        glow_blob(canvas, W / 2, 1362, 260, (255, 194, 26), 70, 70)
        ac(canvas, alpha(p, ca), (((W - p.width) / 2, 1300 + (1 - ca) * 16)))

    ta = eo(prog(lt, 1.10, .6))
    if ta > 0:
        tracked(d, (W / 2, 1444), "Livraison sous 24 h · 100 % modifiable",
                F("r", 25), c_(ICE, 225 * ta), 0.5, center=W / 2)
        d.line([(M_, 1512), (W - M_, 1512)], fill=c_(WHITE, 45 * ta), width=1)
        tracked(d, (W / 2, 1544), "DIGITAWARD", F("xb", 38), c_(WHITE, 240 * ta), 3.4, center=W / 2)
        tracked(d, (W / 2, 1612), "Le savoir à portée de clic.", F("r", 26),
                c_(YELLOW, 230 * ta), 0, center=W / 2)


SCENE_FN = {"hook": s_hook, "pain": s_pain, "turn": s_turn, "reveal": s_reveal,
            "slides": s_slides, "benefit": s_benefit, "offer": s_offer, "end": s_end}


def chrome(canvas, t, name):
    d = ImageDraw.Draw(canvas)
    wa = eo(prog(t, .2, .6))
    if name not in ("reveal", "benefit", "end"):
        lc = logo_on_card(210)
        ac(canvas, alpha(lc, .95 * wa), ((M_, 64)))
    # barre de progression jaune
    py = 1850
    d.rounded_rectangle([M_, py, W - M_, py + 6], 3, fill=(255, 255, 255, 45))
    fw = int((W - 2 * M_) * clamp01(t / TOTAL))
    if fw > 4:
        d.rounded_rectangle([M_, py, M_ + fw, py + 6], 3, fill=c_(YELLOW, 255))


_BG = None


def render_frame(fi):
    global _BG
    if _BG is None:
        _BG = build_bg()
    t = fi / FPS
    i = len(SCENES) - 1
    for k, (_, s, e) in enumerate(SCENES):
        if s <= t < e:
            i = k
            break
    name, s, e = SCENES[i]
    lt = t - s
    dur = e - s

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    SCENE_FN[name](d, layer, t, lt)
    layer = alpha(layer, eo(prog(lt, 0, .18)) * (1 - .35 * eo(prog(lt, dur - .12, .12))))

    frame = _BG.copy()
    ac(frame, layer)
    chrome(frame, t, name)
    return frame.convert("RGB")


# ------------------------------------------------------------------ audio
def _noise(n, lo, hi, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n).astype(np.float32)
    sos = butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], btype="band", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def _read(path):
    with wavemod.open(path, "rb") as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        raw = w.readframes(n)
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    if sr != SR:
        idx = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(idx, np.arange(len(a)), a)
    return a


def build_audio():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    n = int(TOTAL * SR)
    m = np.zeros(n, np.float32)
    bpm = 122.0
    beat = 60 / bpm
    bar = beat * 4
    roots = [65.41, 87.31, 98.0, 73.42]  # C F G D

    # kick
    t0 = 0
    while t0 < TOTAL:
        s = int(t0 * SR)
        ln = min(n - s, int(.28 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 118 * np.exp(-tt * 18) + 46
            m[s:s + ln] += (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 13) * .40).astype(np.float32)
        t0 += beat

    # clap 2 & 4
    for b in range(int(TOTAL / beat) + 1):
        if b % 4 in (1, 3):
            s = int(b * beat * SR)
            ln = min(n - s, int(.2 * SR))
            if ln > 0:
                m[s:s + ln] += (_noise(ln, 1400, 6000, seed=b) * np.exp(-np.arange(ln) / SR * 24) * .18).astype(np.float32)

    # hats 1/8
    b = 0
    while b * beat / 2 < TOTAL:
        s = int(b * beat / 2 * SR)
        ln = min(n - s, int(.05 * SR))
        if ln > 0:
            m[s:s + ln] += (_noise(ln, 7000, 16000, seed=b + 9) * np.exp(-np.arange(ln) / SR * 160) * (.05 if b % 2 == 0 else .032)).astype(np.float32)
        b += 1

    # basse 1/8
    k = 0
    while k * beat / 2 < TOTAL:
        s = int(k * beat / 2 * SR)
        ln = min(n - s, int(.24 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[int((k * beat / 2) / bar) % 4]
            v = np.sin(2 * np.pi * r * tt) + .35 * np.sin(4 * np.pi * r * tt)
            e = np.exp(-tt * 10) * np.minimum(tt / .005, 1)
            sos = butter(2, 200 / (SR / 2), btype="low", output="sos")
            m[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * .30).astype(np.float32)
        k += 1

    # pad brillant
    for bi in range(int(TOTAL / bar) + 1):
        s = int(bi * bar * SR)
        e_ = min(n, int((bi * bar + bar + .5) * SR))
        if s >= n:
            break
        tt = np.arange(e_ - s) / SR
        r = roots[bi % 4] * 4
        env = np.minimum(tt / .4, 1) * np.exp(-np.maximum(tt - bar * .55, 0) * 1.6)
        v = np.sin(2 * np.pi * r * tt) * .5 + np.sin(2 * np.pi * r * 1.5 * tt + .6) * .3
        sos = butter(2, 3200 / (SR / 2), btype="low", output="sos")
        m[s:e_] += (sosfilt(sos, (v * env).astype(np.float32)) * .085).astype(np.float32)

    # arpèges 16e
    step = beat / 4
    k, t0 = 0, 6.0
    while t0 < TOTAL - .3:
        s = int(t0 * SR)
        ln = min(n - s, int(.2 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            note = roots[int(t0 / bar) % 4] * 8 * (2 ** ([0, 7, 12, 15][k % 4] / 12))
            m[s:s + ln] += (np.sin(2 * np.pi * note * tt) * np.exp(-tt * 24) * .05).astype(np.float32)
        k += 1
        t0 += step

    # impacts de coupe + riser
    for i, (_, s0, _) in enumerate(SCENES[:-1]):
        s = int(s0 * SR)
        ln = min(n - s, int(.8 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            boom = np.sin(2 * np.pi * (70 * tt - 18 * tt ** 2)) * np.exp(-tt * 7)
            m[s:s + ln] += (boom * .40).astype(np.float32)
    # riser avant le reveal
    rs = int((SCENES[3][1] - 1.6) * SR)
    ln = min(n - rs, int(1.6 * SR))
    if ln > 0:
        tt = np.arange(ln) / SR
        m[rs:rs + ln] += (_noise(ln, 600, 10000, seed=77) * (tt / 1.6) ** 2.2 * .18).astype(np.float32)

    # whoosh à chaque transition
    for _, s0, _ in SCENES[1:-1]:
        s = int((s0 - .18) * SR)
        ln = min(n - max(s, 0), int(.45 * SR))
        if ln > 0 and s >= 0:
            tt = np.arange(ln) / SR
            m[s:s + ln] += (_noise(ln, 300, 6000, seed=int(s0 * 10)) * np.sin(np.pi * tt / .45) ** 1.5 * .13).astype(np.float32)

    # ding CTA
    for tp in (SCENES[5][1] + 1.3, SCENES[7][1] + 1.0):
        s = int(tp * SR)
        ln = min(n - s, int(1.2 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            v = np.sin(2 * np.pi * 1568 * tt) * .6 + np.sin(2 * np.pi * 2093 * tt) * .4
            m[s:s + ln] += (v * np.exp(-tt * 5) * .14).astype(np.float32)

    # voix off
    vo = np.zeros(n, np.float32)
    for k_i, (fname, start, tempo) in enumerate(VO, start=1):
        dst = f"/tmp/_dwvo{k_i}.wav"
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", os.path.join(AUD, fname), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                        f"areverse,atempo={tempo:.4f}", "-ar", str(SR), "-ac", "1", dst], check=True)
        a = _read(dst)
        s = int(start * SR)
        e = min(n, s + len(a))
        if s < n:
            vo[s:e] += a[:e - s] * 1.10

    env = np.abs(vo)
    win = int(.12 * SR)
    env = np.convolve(env, np.ones(win, np.float32) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 3.4, 0, 1)
    m *= (1 - .62 * env)

    dly = int(.012 * SR)
    mix = m + vo
    left = mix
    right = np.concatenate([np.zeros(dly, np.float32), mix[:-dly]])
    st = np.stack([left * .97 + right * .09, right * .97 + left * .09], axis=1)
    st = st / (np.abs(st).max() + 1e-9) * .90
    raw = "/tmp/_dw_raw.wav"
    with wavemod.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())

    subprocess.run([ff, "-y", "-loglevel", "error", "-i", raw, "-af",
                    "highpass=f=45,equalizer=f=2200:width_type=o:width=1.3:g=2.4,volume=4.5dB,"
                    "alimiter=limit=0.94:level=disabled", "-ar", str(SR), MIX], check=True)
    return MIX


def preview(path):
    global _BG
    _BG = build_bg()
    sheet = Image.new("RGB", (4 * (432 + 8) + 8, 2 * (768 + 8) + 8), (12, 16, 40))
    sd = ImageDraw.Draw(sheet)
    for i, (_, s, e) in enumerate(SCENES):
        t = (s + e) / 2
        im = render_frame(int(t * FPS)).resize((432, 768), Image.LANCZOS)
        x, y = 8 + (i % 4) * 440, 8 + (i // 4) * 776
        sheet.paste(im, (x, y))
        sd.rectangle([x, y, x + 150, y + 26], fill=(0, 0, 0))
        sd.text((x + 6, y + 4), f"t={t:05.2f}s", font=F("sb", 17), fill=(255, 255, 255))
    sheet.save(path, quality=90)
    print("Saved preview:", path)


def render():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    nf = int(round(TOTAL * FPS))
    p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", TMP],
                         stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(render_frame(fi).tobytes())
        if fi % 200 == 0:
            print(f"  {fi}/{nf} ({fi / nf * 100:.0f}%)", flush=True)
    p.stdin.close()
    p.wait()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP, "-i", MIX,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", OUT], check=True)
    print("Rendered", OUT, f"({os.path.getsize(OUT) / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default=None)
    ap.add_argument("--audio-only", action="store_true")
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
        return
    print("Voix off + musique ...")
    build_audio()
    if a.audio_only:
        print("Audio ->", MIX)
        return
    render()


if __name__ == "__main__":
    main()
