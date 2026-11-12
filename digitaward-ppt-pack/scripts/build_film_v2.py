#!/usr/bin/env python3
"""Digitaward — Pack 1 500 modèles PowerPoint · publicité Facebook 9:16 · v2.

Réécriture « anti-slop » du film, pilotée par les skills installés
(`motionmaxxing`, `business-motion-film`, `hallmark`) :

  - une seule idée : le temps perdu, puis le temps rendu (horloge diégétique)
  - un vrai monde : sol, faisceau, poussière, grain animé, caméra qui respire
  - 29 plans (1,5 s en moyenne) au lieu de 7 plans de 6,5 s
  - aucune décoration d'interface : ni logo en coin, ni barre de progression,
    ni sur-titre en capitales espacées, ni mur de chiffres
  - chaque plan démarre en mouvement et se coupe en mouvement
  - typographie révélée par masque et déplacement, jamais par fondu

L'audio (voix off, musique, SFX) est reconstruit sur les nouveaux points de coupe.

    python3 build_film_v2.py --preview /tmp/preview2.jpg
    python3 build_film_v2.py --audio-only
    python3 build_film_v2.py
"""
import argparse
import math
import os
import subprocess
import sys
import wave as wavemod

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_film import (  # noqa: E402
    W, H, FPS, SR, OUT, MIX, AUD, IMG, FILM, TOTAL, VO,
    NAVY, ROYAL, ROYAL_BRIGHT, YELLOW, YELLOW_DEEP, ORANGE, WHITE, ICE, MUTED,
    F, tl, tracked, para, ac, alpha, rounded, shadow, place, glow_blob, load,
    logo_on_card, slide_card, shot, clamp01, prog, eo, eob, eio, c_,
)

_CARD_CACHE = {}


def _card_mask(w, h, r=18):
    k = (w, h, r)
    if k not in _CARD_CACHE:
        _CARD_CACHE[k] = rounded(w, h, r)
    return _CARD_CACHE[k]


def place(canvas, im, x, y, r=26, blur=30, sa=150, dy=18, scale=1.0):
    """Pose avec ombre portée, compatible RGBA pleine frame (alpha_composite)."""
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))),
                       Image.LANCZOS)
    p = blur * 2
    sh = Image.new("RGBA", (im.width + p * 2, im.height + p * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([p, p, p + im.width - 1, p + im.height - 1],
                                         r, fill=(0, 0, 0, sa))
    ac(canvas, sh.filter(ImageFilter.GaussianBlur(blur)), (x - p, y - p + dy))
    ac(canvas, im, (x, y))


OUT2 = os.path.join(FILM, "digitaward-pack-1500-powerpoint-fb-9x16-v2.mp4")
MIX2 = os.path.join(AUD, "master_mix_v2.wav")
os.makedirs(FILM, exist_ok=True)

# ---------------------------------------------------------------- découpage
# (nom, début, fin) — 29 plans, 1,56 s de moyenne
SHOTS = [
    ("open_macro",  0.00,  1.55),
    ("room",        1.55,  3.10),
    ("timelapse",   3.10,  4.70),
    ("draft",       4.70,  6.60),
    ("picker",      6.60,  7.90),
    ("fonts",       7.90,  9.20),
    ("image",       9.20, 10.60),
    ("mess",       10.60, 12.80),
    ("power_on",   12.80, 14.50),
    ("pack_rise",  14.50, 16.10),
    ("pack_macro", 16.10, 17.60),
    ("pack_hero",  17.60, 19.30),
    ("pack_open",  19.30, 21.20),
    ("fan_track",  21.20, 22.70),
    ("use_cases",  22.70, 24.80),
    ("slide_a",    24.80, 26.40),
    ("slide_b",    26.40, 27.90),
    ("slide_c",    27.90, 29.40),
    ("slide_d",    29.40, 30.80),
    ("rewind",     30.80, 32.90),
    ("pack_shut",  32.90, 34.30),
    ("wall",       34.30, 35.60),
    ("claim",      35.60, 37.10),
    ("stamp",      37.10, 38.80),
    ("proof_macro",38.80, 39.60),
    ("cta_press",  39.60, 40.80),
    ("burst",      40.80, 41.60),
    ("brand",      41.60, 43.80),
    ("end",        43.80, 45.20),
]

# coupes destinées au son (les plus structurantes)
AUDIO_CUTS = [1.55, 4.70, 6.60, 10.60, 12.80, 14.50, 17.60, 19.30,
              22.70, 24.80, 30.80, 34.30, 35.60, 37.10, 39.60, 41.60]


# ---------------------------------------------------------------- cinéma
def build_stage():
    """Un plateau : ciel nuit, sol réfléchissant, faisceau, poussière."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    f = np.clip(yy / H, 0, 1)
    stops = [0.00, 0.22, 0.48, 0.74, 1.00]
    cols = [(0, 14, 78), (0, 34, 150), (0, 52, 214), (0, 30, 138), (0, 12, 66)]
    img = np.zeros((H, W, 3), np.float32)
    for ch in range(3):
        img[..., ch] = np.interp(f, stops, [c[ch] for c in cols])

    # halo d'horizon (lumière de projecteur au fond)
    d1 = ((xx - W * .50) ** 2) / (740 ** 2) + ((yy - H * .52) ** 2) / (620 ** 2)
    img += (np.exp(-d1) * .34)[..., None] * np.array((40, 130, 255), np.float32)
    # halo jaune très bas, discret
    d2 = ((xx - W * .5) ** 2 + (yy - H * .99) ** 2) / (640 ** 2)
    img += (np.exp(-d2 * 1.7) * .07)[..., None] * np.array((255, 194, 26), np.float32)

    # sol : surface sombre mais lisible, avec une flaque de lumière
    fl = np.clip((yy - H * .795) / (H * .205), 0, 1)
    img = img * (1 - fl[..., None] * .55) + fl[..., None] * np.array((2, 10, 44), np.float32) * .55
    pool = ((xx - W * .5) ** 2) / (520 ** 2) + ((yy - H * .86) ** 2) / (190 ** 2)
    img += (np.exp(-pool) * .22)[..., None] * np.array((60, 140, 255), np.float32)

    # vignette
    vx = (xx - W / 2) / (W * .86)
    vy = (yy - H * .52) / (H * .86)
    img *= np.clip(1 - .40 * (vx * vx + vy * vy), .52, 1)[..., None]

    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

    # faisceau volumétrique (fixe, animé à la composition)
    beam = Image.new("RGBA", (1500, 2400), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(980, -200), (1500, -200), (620, 2400), (-180, 2400)],
               fill=(130, 190, 255, 34))
    beam = beam.filter(ImageFilter.GaussianBlur(150))
    ac(base, beam, (-210, -240))

    # ligne d'horizon : le sol existe, il reflète la lumière du fond
    hz = Image.new("RGBA", (W, 60), (0, 0, 0, 0))
    ImageDraw.Draw(hz).rectangle([0, 28, W, 32], fill=(150, 205, 255, 70))
    base.alpha_composite(hz.filter(ImageFilter.GaussianBlur(9)), (0, int(H * .795) - 30))
    # flaque de lumière sur le sol
    pool = Image.new("RGBA", (1300, 420), (0, 0, 0, 0))
    ImageDraw.Draw(pool).ellipse([60, 90, 1240, 330], fill=(70, 150, 255, 60))
    base.alpha_composite(pool.filter(ImageFilter.GaussianBlur(70)), (-110, int(H * .80) - 120))
    return base


_STAGE = None


def stage_base():
    global _STAGE
    if _STAGE is None:
        _STAGE = build_stage()
    return _STAGE


_DUST = None


def dust():
    global _DUST
    if _DUST is None:
        rng = np.random.default_rng(11)
        _DUST = [(float(rng.uniform(0, W)), float(rng.uniform(0, H)),
                  float(rng.uniform(.6, 2.6)), float(rng.uniform(4, 22)),
                  float(rng.uniform(0, 6.28)), int(rng.integers(18, 64)))
                 for _ in range(72)]
    return _DUST


_GRAIN = None


def grain_tiles():
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(3)
        tiles = []
        for _ in range(5):
            n = rng.normal(0, 1, (H // 2, W // 2, 1)).astype(np.float32)
            g = np.full((H // 2, W // 2, 4), 0, np.uint8)
            g[..., :3] = np.clip(128 + n * 26, 0, 255).astype(np.uint8)
            g[..., 3] = 11
            tiles.append(Image.fromarray(g).resize((W, H), Image.BILINEAR))
        _GRAIN = tiles
    return _GRAIN


def stage_frame(t, flare=0.0):
    img = stage_base().copy()
    d = ImageDraw.Draw(img)
    # poussière : trois profondeurs, dérive lente
    for x0, y0, r, sp, ph, a in dust():
        y = (y0 - t * sp) % H
        x = (x0 + math.sin(t * .35 + ph) * 26) % W
        d.ellipse([x, y, x + r, y + r], fill=(190, 216, 255, a))
    # nappe de brume qui dérive (parallaxe)
    haze = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    hd.ellipse([-260 + math.sin(t * .18) * 90, H * .62, W + 260, H * 1.08],
               fill=(30, 80, 200, 46))
    img.alpha_composite(haze.filter(ImageFilter.GaussianBlur(120)))
    # réflecteur qui balaie lentement
    sw = Image.new("RGBA", (900, 2400), (0, 0, 0, 0))
    ImageDraw.Draw(sw).polygon([(300, 0), (900, 0), (620, 2400), (20, 2400)],
                               fill=(150, 200, 255, 16))
    sw = sw.filter(ImageFilter.GaussianBlur(90))
    ac(img, sw, (int(-160 + 260 * math.sin(t * .11)), -240))
    if flare > 0:
        glow_blob(img, W * .5, H * .46, 420, (255, 236, 170), int(90 * flare), 150)
    return img


def camera(img, zoom=1.0, dx=0.0, dy=0.0, t=0.0, handheld=1.0):
    sx = (3.6 * math.sin(t * 1.63) + 1.8 * math.sin(t * 3.71)) * handheld
    sy = (3.0 * math.cos(t * 1.27) + 1.4 * math.sin(t * 4.31)) * handheld
    a = 1.0 / zoom
    cx, cy = W / 2, H / 2
    coeffs = (a, 0, cx - a * cx - dx - sx,
              0, a, cy - a * cy - dy - sy)
    return img.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC)


def finish(img, t, light=1.0):
    """Grain animé + micro-vignette : la texture « filmée »."""
    tiles = grain_tiles()
    ti = int(t * FPS) % len(tiles)
    img.alpha_composite(tiles[ti])
    if light < 1.0:
        black = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - light))))
        img.alpha_composite(black)
    return img


# ---------------------------------------------------------------- typographie
def text_w(text, f, tracking=0.0):
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    return tl(d, text, f, tracking)


def words(layer, text, f, fill, x, baseline, p, tracking=0.0,
          stagger=.05, rise=30, mask=True, maxw=None):
    """Révélation par mot : masque + montée, jamais de fondu."""
    if maxw is not None:
        lines = []
        cur = ""
        for w_ in text.split(" "):
            test = (cur + " " + w_).strip()
            if text_w(test, f, tracking) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
        out = []
        for i, ln in enumerate(lines):
            out.append(words(layer, ln, f, fill, x, baseline + i * f.size * 1.16,
                             p, tracking, stagger, rise, mask))
        return out
    ws = text.split(" ")
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    gap = d.textlength(" ", font=f)
    total = sum(d.textlength(w_, font=f) + tracking * len(w_) for w_ in ws) + gap * (len(ws) - 1)
    cx = x - total / 2 if x is None else x
    for i, w_ in enumerate(ws):
        pw = d.textlength(w_, font=f) + tracking * len(w_)
        pi = clamp01((p * 1.22 - i * stagger) / .58)
        if pi > 0:
            e = eob(pi)
            yy = baseline + (1 - e) * rise
            wi, hi = int(pw) + 12, int(f.size * 1.7)
            im = Image.new("RGBA", (wi, hi), (0, 0, 0, 0))
            dd = ImageDraw.Draw(im)
            dd.text((6, hi * .76), w_, font=f, fill=fill, anchor="ls")
            if mask:
                keep = Image.new("L", (wi, hi), 0)
                ImageDraw.Draw(keep).rectangle([0, 0, wi, hi * (1 - (1 - e) * .92)], fill=255)
                im.putalpha(ImageChops.multiply(im.getchannel("A"), keep))
            ac(layer, im, (cx - 6, yy - hi * .76))
        cx += pw + gap


def center_x(text, f, tracking=0.0):
    return (W - text_w(text, f, tracking)) / 2


# ---------------------------------------------------------------- objets
_CUR = None


def cursor_img(scale=1.0):
    global _CUR
    if _CUR is None:
        s = 3
        im = Image.new("RGBA", (44 * s, 60 * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = [(4, 2), (4, 46), (15, 35), (23, 54), (32, 50), (24, 31), (39, 30)]
        d.polygon([(x * s, y * s) for x, y in pts], fill=(255, 255, 255, 255),
                  outline=(10, 16, 40, 255))
        d.line([(x * s, y * s) for x, y in pts] + [(4 * s, 2 * s)],
               fill=(10, 16, 40, 255), width=3 * s)
        _CUR = im
    return _CUR.resize((int(44 * scale), int(60 * scale)), Image.LANCZOS)


def draw_cursor(layer, x, y, scale=1.0, press=0.0):
    c = cursor_img(scale * (1 - .07 * press))
    sh = shadow(c.width, c.height, 6, 8, 110)
    ac(layer, sh, (x - 16, y - 16 + 5))
    ac(layer, c, (x, y))


def find_coeffs(pa, pb):
    m = []
    for p1, p2 in zip(pa, pb):
        m.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        m.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    return np.linalg.solve(np.matrix(m, dtype=float), np.array(pb, dtype=float).reshape(8))


def persp(im, dw, dh, top=.9, skew=0.0):
    sw, sh = im.size
    dx = dw * (1 - top) / 2
    dst = [(dx + skew, 0), (dw - dx + skew, 0), (dw, dh), (0, dh)]
    src = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
    co = find_coeffs(dst, src)
    return im.transform((dw, dh), Image.PERSPECTIVE, co, resample=Image.BICUBIC)


def card(im, w, tilt=0.0, top=1.0, radius=18, glow=False):
    h = int(w * im.height / im.width)
    out = im.resize((w, h), Image.LANCZOS)
    if top != 1.0:
        out = persp(out, w, h, top)
    mask = rounded(out.width, out.height, radius)
    o = Image.new("RGBA", out.size, (0, 0, 0, 0))
    o.paste(out, (0, 0), mask)
    if tilt:
        o = o.rotate(tilt, resample=Image.BICUBIC, expand=True)
    return o


_SH_CACHE = {}


def shadowed(layer, im, x, y, blur=34, a=150, dy=26, r=18):
    """Ombre portée recalée sur l'image, sans débordement de cadre."""
    p = blur * 2
    k = (im.width, im.height, r, blur, a)
    if k not in _SH_CACHE:
        sh = Image.new("RGBA", (im.width + p * 2, im.height + p * 2), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([p, p, p + im.width - 1, p + im.height - 1],
                                             r, fill=(0, 0, 0, a))
        _SH_CACHE[k] = sh.filter(ImageFilter.GaussianBlur(blur))
    ac(layer, alpha(_SH_CACHE[k], 1.0), (x - p, y - p + dy))
    ac(layer, im, (x, y))


def ground_contact(layer, im, x, y, strength=1.0):
    """Contact au sol : reflet court (dégradé + flou) et ombre douce."""
    rh = max(18, int(im.height * .17))
    ref = im.transpose(Image.FLIP_TOP_BOTTOM).crop(
        (0, im.height - rh, im.width, im.height))
    grad = Image.linear_gradient("L").resize((1, rh), Image.BILINEAR).point(
        lambda v: int(200 * (1 - v / 255) ** 2))
    mask = Image.new("L", (im.width, rh), 0)
    mask.paste(grad.resize((im.width, rh)), (0, 0))
    ref.putalpha(ImageChops.multiply(ref.getchannel("A"),
                                     ImageChops.multiply(mask, Image.new("L", mask.size, int(48 * strength)))))
    ref = ref.filter(ImageFilter.GaussianBlur(9))
    ac(layer, ref, (x, y + im.height - 2))
    sh = Image.new("RGBA", (im.width + 260, 200), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([130, 30, im.width + 130, 170],
                               fill=(0, 6, 26, int(120 * strength)))
    ac(layer, sh.filter(ImageFilter.GaussianBlur(50)),
       (x - 130, y + im.height - 70))


def shadowed(layer, im, x, y, blur=34, a=150, dy=26, r=18):
    sh = shadow(im.width, im.height, r, blur, a)
    ac(layer, sh, (x - blur * 2, y - blur * 2 + dy))
    ac(layer, im, (x, y))


# --- diapositive « brouillon » (l'avant, volontairement ratée) -------------
def ugly_slide(w, h, seed=0, stage=0):
    rng = np.random.default_rng(seed)
    tones = [(232, 228, 219), (211, 215, 224), (236, 231, 239)]
    bg = tones[seed % 3]
    im = Image.new("RGBA", (w, h), c_(bg, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, int(h * .07)], fill=c_((196, 198, 206), 255))
    fonts = ["m", "r", "sb", "b"]
    fk = fonts[seed % len(fonts)]
    fs = int(w * (.09 + .02 * ((seed + 1) % 3)))
    tx = int(w * (.09 + .03 * ((seed * 7) % 3)))
    ty = int(h * .14)
    d.text((tx, ty), ["Mon exposé", "Le sujet", "PARTIE 1"][seed % 3],
           font=F(fk, fs), fill=c_((56, 56, 64), 255))
    # barres de texte décalées
    y = ty + int(fs * 1.5)
    for i in range(5):
        bw = int(w * (.72 - .05 * ((i + seed) % 3)))
        dx = int(rng.integers(-6, 7))
        d.rectangle([tx + dx, y, tx + dx + bw, y + int(h * .022)],
                    fill=c_((150 + 8 * i, 152 + 6 * i, 160), 255))
        y += int(h * .042)
    # image mal placée
    if seed % 2 == 0:
        bx = int(w * .58)
        by = y + int(h * .03)
        d.rectangle([bx, by, bx + int(w * .34), by + int(h * .26)],
                    outline=c_((196, 88, 80), 255), width=max(3, w // 220))
        d.line([(bx, by), (bx + int(w * .34), by + int(h * .26))], fill=c_((196, 88, 80), 255), width=3)
        d.line([(bx + int(w * .34), by), (bx, by + int(h * .26))], fill=c_((196, 88, 80), 255), width=3)
    # clip-art qui jure
    if seed % 3 == 1:
        cx, cy = int(w * .78), int(h * .3)
        pts = [(cx + math.cos(a) * w * .05, cy + math.sin(a) * w * .05)
               for a in np.linspace(-math.pi / 2, 1.5 * math.pi, 10, endpoint=False)]
        d.polygon(pts, fill=(255, 176, 32, 255))
    return im


def laptop_img(w, screen, glow_col=(120, 180, 255)):
    """Portable de trois quarts face : écran + clavier, lumière qui fuit."""
    sh = int(w * screen.height / screen.width)
    bez = 12
    base = Image.new("RGBA", (w + bez * 2, sh + bez * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([0, 0, base.width - 1, base.height - 1], 14,
                        fill=(9, 12, 24, 255), outline=(70, 90, 130, 120), width=2)
    sc = screen.resize((w, sh), Image.LANCZOS)
    base.paste(sc, (bez, bez))
    body = Image.new("RGBA", (w + bez * 4, int(w * .10)), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([0, 0, body.width - 1, body.height - 1], 10,
                         fill=(16, 20, 34, 255), outline=(80, 100, 140, 90), width=2)
    bd.rounded_rectangle([body.width * .32, 6, body.width * .68, body.height * .42],
                         4, fill=(38, 46, 66, 255))
    return base, body


# ---------------------------------------------------------------- plans
def s_open_macro(layer, lt, dur):
    """Macro : une diapo posée dans la pénombre ; l'horloge tourne déjà."""
    # l'horloge murale, dans le haut du cadre : elle donne l'heure du calvaire
    clock(layer, W * .50, 250, 104, 23 * 3600 + 41 * 60 + lt * 900, 1.0)

    sw, sh_ = int(W * .90), int(W * .56)
    sl = Image.new("RGBA", (sw, sh_), c_((246, 247, 250), 255))
    d = ImageDraw.Draw(sl)
    for gx in range(0, sw, 96):
        d.line([(gx, 0), (gx, sh_)], fill=c_((233, 235, 241), 255), width=1)
    for gy in range(0, sh_, 96):
        d.line([(0, gy), (sw, gy)], fill=c_((233, 235, 241), 255), width=1)
    d.text((int(sw * .09), int(sh_ * .16)), "Mon exposé", font=F("m", 76),
           fill=c_((52, 56, 68), 255))
    d.rectangle([int(sw * .09), int(sh_ * .30), int(sw * .46), int(sh_ * .306)],
                fill=c_((158, 164, 178), 255))
    x0, y0, x1, y1 = int(sw * .09), int(sh_ * .38), int(sw * .52), int(sh_ * .62)
    d.rectangle([x0, y0, x1, y1], outline=c_((146, 152, 168), 255), width=3)
    for px, py in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        d.rectangle([px - 8, py - 8, px + 8, py + 8], fill=(255, 255, 255, 255),
                    outline=c_((110, 118, 138), 255), width=2)
    for i in range(3):
        yy = y0 + 34 + i * 46
        d.rectangle([x0 + 20, yy, x0 + 20 + int((x1 - x0) * (.72 - i * .1)), yy + 18],
                    fill=c_((176, 180, 192), 255))
    c = card(sl, sw, tilt=-6, radius=6)
    shadowed(layer, c, (W - c.width) / 2 + lt * 6, 500 + lt * 5, blur=70, a=195, dy=46)
    glow_blob(layer, W * .18, 560, 250, (140, 190, 255), 48, 110)
    p = eo(prog(lt, .15, .95))
    draw_cursor(layer, W * .72 - p * 120, 800 + p * 50, 1.7,
                press=eob(prog(lt, 1.05, .18)))
    a2 = eob(prog(lt, .45, .55))
    if a2 > 0:
        tracked(ImageDraw.Draw(layer), (W / 2, 430), "23:41", F("xb", 46),
                c_(WHITE, 210 * a2), 6, center=W / 2)


def s_room(layer, lt, dur):
    w = int(W * .92)
    sl = ugly_slide(640, 400, seed=0)
    base, body = laptop_img(w, sl)
    ang = -4 + lt * .6
    lap = base.rotate(ang, resample=Image.BICUBIC, expand=True)
    x = (W - lap.width) / 2 - 30
    y = 500 + (1 - eob(prog(lt, 0, 1.0))) * 40
    # lumière qui fuit de l'écran sur le sol
    glow_blob(layer, W / 2, y + lap.height * .55, 360, (90, 150, 255), 80, 120)
    shadowed(layer, lap, x, y, blur=40, a=170, dy=26)
    kb = body.rotate(ang, resample=Image.BICUBIC, expand=True)
    shadowed(layer, kb, x + 10, y + lap.height - 26, blur=26, a=150, dy=14)
    # horloge murale, à droite
    clock(layer, W * .845, 360, 86, 23 * 3600 + 41 * 60 + lt * 30, 1.0, alpha_=255)


def clock(layer, cx, cy, r, secs, speed=1.0, alpha_=255):
    im = Image.new("RGBA", (int(r * 2.5), int(r * 2.5)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = im.width / 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=(6, 12, 30, 210),
              outline=(200, 214, 245, 60), width=3)
    for i in range(12):
        a = i * math.pi / 6
        x0, y0 = c + math.sin(a) * r * .84, c - math.cos(a) * r * .84
        x1, y1 = c + math.sin(a) * r * .92, c - math.cos(a) * r * .92
        d.line([(x0, y0), (x1, y1)], fill=(230, 238, 255, 210), width=3 if i % 3 == 0 else 2)
    hh = (secs / 3600) % 12 * math.pi / 6
    mm = (secs / 60) % 60 * math.pi / 30
    ss = (secs % 60) * math.pi / 30
    for ang_, ln, wd, col in [(hh, r * .46, 9, (255, 255, 255, 245)),
                              (mm, r * .68, 6, (255, 255, 255, 235)),
                              (ss, r * .78, 2, (255, 194, 26, 245))]:
        d.line([(c, c), (c + math.sin(ang_) * ln, c - math.cos(ang_) * ln)],
               fill=col, width=wd)
    d.ellipse([c - 7, c - 7, c + 7, c + 7], fill=(255, 194, 26, 255))
    ac(layer, alpha(im, alpha_ / 255), (cx - c, cy - c))


def s_timelapse(layer, lt, dur):
    w = int(W * .92)
    sl = ugly_slide(640, 400, seed=0)
    base, body = laptop_img(w, sl)
    lap = base.rotate(-3.4, resample=Image.BICUBIC, expand=True)
    x = (W - lap.width) / 2 - 30
    y = 500
    glow_blob(layer, W / 2, y + lap.height * .55, 380, (110, 165, 255), 90, 130)
    shadowed(layer, lap, x, y, blur=40, a=170, dy=26)
    kb = body.rotate(-3.4, resample=Image.BICUBIC, expand=True)
    shadowed(layer, kb, x + 10, y + lap.height - 26, blur=26, a=150, dy=14)
    # l'horloge tourne : le temps file
    clock(layer, W * .845, 360, 86, 23 * 3600 + 41 * 60 + lt * 3000, 1.0)
    # la lumière de la pièce change (aube)
    a = clamp01(lt / dur)
    dawn = Image.new("RGBA", (W, H), (255, 186, 120, int(26 * a)))
    layer.alpha_composite(dawn)


def s_draft(layer, lt, dur):
    # gros plan sur l'écran : la diapo vide, le compteur qui monte
    w = int(W * 1.0)
    sl = ugly_slide(700, 440, seed=1)
    d0 = ImageDraw.Draw(sl)
    secs = int(3 * 3600 + 12 * 60 * eo(prog(lt, .2, 1.4)))
    d0.rounded_rectangle([int(700 * .66), 18, int(700 * .95), 76], 12, fill=(24, 24, 30, 255))
    tracked(d0, (int(700 * .70), 28), f"{secs // 3600} h {secs % 3600 // 60:02d}",
            F("b", 34), c_(WHITE, 240))
    z = 1.06 + .04 * lt / dur
    card_ = card(sl, w)
    shadowed(layer, card_, -(card_.width - W) / 2 - 40, 430 - lt * 10, blur=60, a=180, dy=30)
    # curseur qui tourne en rond
    ang = lt * 2.4
    draw_cursor(layer, W * .58 + math.cos(ang) * 120, 700 + math.sin(ang) * 70, 1.3)


def s_picker(layer, lt, dur):
    sl = ugly_slide(700, 440, seed=1)
    c1 = card(sl, int(W * .96), tilt=-4, radius=8)
    shadowed(layer, c1, (W - c1.width) / 2 - 20, 330, blur=46, a=170, dy=30)

    pw, ph = 400, 300
    pan = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(pan)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], 18, fill=(20, 26, 46, 242),
                        outline=(140, 170, 235, 90), width=2)
    tracked(d, (26, 18), "Couleur du thème", F("sb", 22), c_(ICE, 235))
    cols = [(216, 210, 196), (198, 206, 220), (232, 226, 236), (206, 188, 170),
            (176, 192, 210), (222, 204, 176)]
    for i, cc in enumerate(cols):
        x = 24 + (i % 3) * 122
        y = 62 + (i // 3) * 112
        d.rounded_rectangle([x, y, x + 102, y + 92], 10, fill=c_(cc, 255))
    ac(layer, pan, (W - pw - 46, 760))
    p = eo(prog(lt, .10, .75))
    draw_cursor(layer, W * .52 + p * 210, 700 + p * 210, 1.6,
                press=eob(prog(lt, .92, .16)))
    if lt > 1.0:
        a = eob(prog(lt, 1.0, .5))
        tint = Image.new("RGBA", c1.size, (206, 188, 170, int(80 * a)))
        tint.putalpha(ImageChops.multiply(tint.getchannel("A"), c1.getchannel("A")))
        ac(layer, tint, ((W - c1.width) / 2 - 40, 380))


def s_fonts(layer, lt, dur):
    sl = ugly_slide(700, 440, seed=1, stage=1)
    c1 = card(sl, int(W * .96))
    shadowed(layer, c1, -(c1.width - W) / 2 - 24, 400, blur=50, a=160, dy=24)

    # liste de polices qui défile
    names = ["Times New Roman", "Comic Sans MS", "Arial", "Georgia", "Impact", "Calibri"]
    lw, lh = 430, 92
    idx = int(lt * 4.2) % len(names)
    off = (lt * 4.2) % 1
    pan = Image.new("RGBA", (lw, lh * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(pan)
    d.rounded_rectangle([0, 0, lw - 1, lh * 3 - 1], 18, fill=(255, 255, 255, 246))
    for i in range(-1, 4):
        k = idx + i
        y = 12 + (i + off) * lh
        if 0 <= y < lh * 3 - 40:
            col = (0, 48, 208, 255) if i == 0 else (58, 62, 76, 210)
            d.text((26, y), names[k % len(names)], font=F("r", 34), fill=col)
    ac(layer, pan, (W - lw - 44, 900))
    # le titre se recompose et déborde
    p = prog(lt, .2, 1.2)
    draw_cursor(layer, W * .58 + math.sin(lt * 2) * 40, 760, 1.5, press=eob(prog(lt, .5, .2)))


def s_image(layer, lt, dur):
    sl = ugly_slide(700, 440, seed=2)
    c1 = card(sl, int(W * .96), tilt=-4, radius=8)
    shadowed(layer, c1, (W - c1.width) / 2 - 20, 330, blur=46, a=160, dy=28)
    im = card(load("slide_chiffres.png"), 470, tilt=-9, radius=8)
    p = eob(prog(lt, .10, .95))
    x = (W - im.width) / 2 + 120 * (1 - p)
    y = 690 + 110 * (1 - p)
    shadowed(layer, im, x, y, blur=30, a=160, dy=22)
    draw_cursor(layer, x + im.width - 40, y + im.height - 30, 1.5,
                press=eob(prog(lt, .92, .16)))
    if lt > 1.05:
        q = eob(prog(lt, 1.05, .45))
        d = ImageDraw.Draw(layer)
        d.rectangle([x + 8, y + 8, x + im.width - 8, y + im.height - 8],
                    outline=c_((255, 120, 100), int(150 * q)), width=3)


def s_mess(layer, lt, dur):
    # trois brouillons étalés sur le bureau, éclairés durement
    items = [(0, -14, 700, 560, 60), (1, 7, 980, 560, 470), (2, -8, 1240, 470, 300)]
    for i, (seed, ang, y, wd, x) in enumerate(items):
        sl = ugly_slide(640, 400, seed=seed)
        c1 = card(sl, wd, tilt=ang, radius=12)
        shadowed(layer, c1, x, y + math.sin(lt * .8 + i) * 4, blur=34, a=160, dy=20)
    # balayage de lumière qui emporte tout
    if lt > 1.55:
        p = prog(lt, 1.55, .55)
        wipe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        wd = ImageDraw.Draw(wipe)
        edge = -200 + p * (W + 400)
        wd.polygon([(edge - 300, 0), (edge, 0), (edge - 180, H), (edge - 480, H)],
                   fill=(120, 170, 255, 70))
        layer.alpha_composite(wipe.filter(ImageFilter.GaussianBlur(40)))
        if p > .55:
            veil = min(1.0, (p - .55) / .35) * (1 - clamp01((p - .82) / .18))
            layer.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(120 * veil))))


def s_power_on(layer, lt, dur):
    """Le pack s'allume : la lumière part de la tranche et balaie la face."""
    box = load("box.png")
    bw = 640
    bh = int(box.height * bw / box.width)
    x, y = (W - bw) / 2, H * .30
    # pack d'abord éteint (silhouette bleu nuit)
    dark = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    dark.paste(Image.new("RGBA", (bw, bh), (4, 10, 34, 235)), (0, 0),
               box.resize((bw, bh), Image.LANCZOS).getchannel("A"))
    p = eo(prog(lt, .25, .95))
    if p < 1:
        ac(layer, dark, (x, y))
    # la face s'allume du centre vers les bords
    if p > 0:
        lit = box.resize((bw, bh), Image.LANCZOS).copy()
        grad = Image.new("L", (bw, bh), 0)
        gd = ImageDraw.Draw(grad)
        rr = int(p * bw * 1.15)
        gd.ellipse([bw / 2 - rr, bh / 2 - rr, bw / 2 + rr, bh / 2 + rr], fill=255)
        grad = grad.filter(ImageFilter.GaussianBlur(70))
        lit.putalpha(ImageChops.multiply(lit.getchannel("A"), grad))
        glow_blob(layer, W / 2, y + bh * .5, 300, (120, 180, 255), int(40 + 70 * p), 120)
        ac(layer, lit, (x, y))
    # liseré de lumière qui court sur la tranche
    d = ImageDraw.Draw(layer)
    trav = eob(prog(lt, .1, .9))
    if 0 < trav < 1.02:
        ly = y + bh * trav
        d.line([(x + 2, ly), (x + 26, ly - 6)], fill=c_((200, 230, 255), 210), width=5)
    # le sol s'éclaire sous le pack
    a2 = eob(prog(lt, .7, .7))
    if a2 > 0:
        ground_contact(layer, box.resize((bw, bh), Image.LANCZOS), x, y, a2)


def s_pack_rise(layer, lt, dur):
    box = load("box.png")
    bw = 700
    bh = int(box.height * bw / box.width)
    p = eob(prog(lt, .05, 1.05))
    y = H * .30 + (1 - p) * 700
    glow_blob(layer, W / 2, y + bh * .5, 330, (120, 175, 255), 80, 110)
    place(layer, alpha(box.resize((bw, bh), Image.LANCZOS), p), (W - bw) / 2, y,
          r=8, blur=36, sa=160, dy=30)
    # liseré lumineux sur le bord gauche du pack
    if p > .5:
        a = eob(prog(lt, .5, .7))
        d = ImageDraw.Draw(layer)
        d.line([(W / 2 - bw / 2 - 4, y + 60), (W / 2 - bw / 2 - 4, y + bh - 40)],
               fill=c_((200, 226, 255), int(120 * a)), width=3)
    # contact au sol
    a = eob(prog(lt, .55, .8))
    if a > 0:
        ground_contact(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y, a)


def s_pack_macro(layer, lt, dur):
    box = load("box.png")
    bw = 1010
    bh = int(box.height * bw / box.width)
    p = eo(prog(lt, 0, dur))
    y = H * .30 - 40 * p
    place(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y, r=8,
          blur=40, sa=150, dy=30)
    # balayage de lumière sur le « 1 500 »
    a = eob(prog(lt, .35, .55))
    if a > 0:
        sweep = Image.new("RGBA", (420, 260), (0, 0, 0, 0))
        ImageDraw.Draw(sweep).polygon([(0, 0), (150, 0), (300, 260), (150, 260)],
                                      fill=(255, 255, 255, 60))
        sweep = sweep.filter(ImageFilter.GaussianBlur(40))
        ac(layer, alpha(sweep, a), (W * .32 + p * 300, y + 120))


def s_pack_hero(layer, lt, dur):
    box = load("box.png")
    bw = 780
    bh = int(box.height * bw / box.width)
    k = eob(prog(lt, 0, .55))
    sc = 1.16 - .16 * k
    w2, h2 = int(bw * sc), int(bh * sc)
    y = H * .27 - 20 * lt / dur
    glow_blob(layer, W / 2, y + h2 * .52, 380, (120, 180, 255), 90, 130)
    place(layer, box.resize((w2, h2), Image.LANCZOS), (W - w2) / 2, y,
          r=8, blur=40, sa=170, dy=34)
    # contact au sol, discret
    ground_contact(layer, box.resize((w2, h2), Image.LANCZOS), (W - w2) / 2, y, .75)


def s_pack_open(layer, lt, dur):
    box = load("box.png")
    bw = 660
    bh = int(box.height * bw / box.width)
    y = H * .28
    names = ["slide_racontez", "slide_chiffres", "slide_merci",
             "slide_vision", "slide_quatre", "slide_clarte"]
    for i, nm in enumerate(names):
        p = eob(prog(lt, .10 + i * .09, .85))
        if p <= 0:
            continue
        side = -1 if i % 2 == 0 else 1
        row = i // 2
        im = card(load(f"{nm}.png"), 300, tilt=side * (7 + row * 3), radius=9)
        x = (W - im.width) / 2 + side * (110 + 220 * p)
        yy = y + 60 + row * 150 + 30 * (1 - p)
        shadowed(layer, alpha(im, min(1, p * 1.7)), x, yy, blur=26, a=150, dy=16)
    glow_blob(layer, W / 2, y + bh * .5, 330, (120, 180, 255), 72, 110)
    place(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y,
          r=8, blur=36, sa=175, dy=30)


def s_fan_track(layer, lt, dur):
    """Un travelling latéral sur une pile de diapos réelles, toutes lisibles."""
    names = ["slide_racontez", "slide_merci", "slide_chiffres", "slide_quatre"]
    for i, nm in enumerate(names):
        im = card(load(f"{nm}.png"), 430, tilt=(-6 if i % 2 == 0 else 4), radius=10)
        x = 46 + i * 84 + lt * 10
        y = 450 + i * 238
        shadowed(layer, alpha(im, .98), x, y, blur=32, a=150, dy=22)


def s_four_cuts(layer, lt, dur):
    seq = [("slide_racontez", -3), ("slide_chiffres", 2), ("slide_merci", -2), ("slide_vision", 3)]
    slot = dur / 4
    i = min(3, int(lt / slot))
    nm, ang = seq[i]
    lt2 = lt - i * slot
    p = eo(prog(lt2, 0, slot * .85))
    im = card(load(f"{nm}.png"), int(W * .98), tilt=ang, radius=8)
    x = (W - im.width) / 2
    y = 620 - 30 * p
    if lt2 < .10:
        ac(layer, alpha(im, .30), (x + ang * 8 + 52, y))
    shadowed(layer, im, x, y, blur=34, a=150, dy=22)
    if lt2 > slot * .82:
        q = prog(lt2, slot * .82, slot * .18)
        ac(layer, Image.new("RGBA", (W, H), (0, 0, 0, int(90 * q))), (0, 0))


def s_slide_a(layer, lt, dur):
    im = card(load("slide_racontez.png"), int(W * 1.02), tilt=-5, radius=8)
    p = eo(prog(lt, 0, dur))
    shadowed(layer, im, (W - im.width) / 2 - 26 - p * 30, 600 - p * 26,
             blur=44, a=170, dy=28)
    sweep(layer, lt, (W - im.width) / 2 + 40, 560, 1.0)


def sweep(layer, lt, x, y, k=1.0):
    """Balayage de lumière sur la surface : la texture du projecteur."""
    a = eob(prog(lt, .15, .55))
    if a <= 0:
        return
    st = Image.new("RGBA", (520, 700), (0, 0, 0, 0))
    ImageDraw.Draw(st).polygon([(0, 0), (170, 0), (390, 700), (220, 700)],
                               fill=(255, 255, 255, int(34 * k)))
    st = st.filter(ImageFilter.GaussianBlur(50))
    ac(layer, alpha(st, a), (x + lt * 180 * k, y))


def s_slide_b(layer, lt, dur):
    im = card(load("slide_merci.png"), int(W * 1.0), tilt=3, radius=8)
    p = eo(prog(lt, 0, .5))
    x = (W - im.width) / 2
    for k, aa in [(-90, .10), (0, 1.0)]:
        shadowed(layer, alpha(im, aa), x + (1 - p) * (240 + abs(k)), 590,
                 blur=40, a=int(150 * aa), dy=24)
    sweep(layer, lt, x + 60, 540, .8)


def s_slide_c(layer, lt, dur):
    im = card(load("slide_chiffres.png"), int(W * 1.02), tilt=-2, radius=8)
    x = (W - im.width) / 2
    shadowed(layer, im, x, 590, blur=44, a=165, dy=26)
    p = eob(prog(lt, .2, .7))
    d = ImageDraw.Draw(layer)
    for i in range(3):
        xx = x + 120 + i * 250
        h = int(160 * p * (0.55 + .22 * i))
        d.line([(xx, 1060), (xx, 1060 - h)], fill=c_(YELLOW, 200), width=4)
    sweep(layer, lt, x + 40, 560, .7)


def s_slide_d(layer, lt, dur):
    im = card(load("slide_quatre.png"), int(W * 1.02), tilt=2, radius=8)
    p = eo(prog(lt, 0, dur))
    shadowed(layer, im, (W - im.width) / 2, 600 - p * 34, blur=42, a=175, dy=26)
    sweep(layer, lt, (W - im.width) / 2 + 40, 570, .9)


def s_use_cases(layer, lt, dur):
    """Quatre usages réels : chaque diapo arrive avec son mot, tout reste lisible."""
    names = ["slide_racontez", "slide_merci", "slide_chiffres", "slide_vision"]
    labels = ["exposé", "soutenance", "formation", "réunion"]
    for i, (nm, lb) in enumerate(zip(names, labels)):
        col, row = i % 2, i // 2
        p = eob(prog(lt, .04 + i * .11, .42))
        if p <= 0:
            continue
        im = card(load(f"{nm}.png"), 462, tilt=(-3 if i % 2 == 0 else 2), radius=9)
        x = 58 + col * 486
        y = 470 + row * 530 + (1 - p) * 26
        shadowed(layer, alpha(im, p), x, y, blur=26, a=int(140 * p), dy=16)
        tracked(ImageDraw.Draw(layer), (x + 6, y + im.height + 16), lb, F("r", 30),
                c_(ICE, int(225 * p)))


def s_rewind(layer, lt, dur):
    # l'horloge rembobine : le temps rendu
    secs = 3 * 3600 + 12 * 60 - lt * 5200
    clock(layer, W / 2, H * .38, 230, secs, 1.0)
    # arc de minuterie qui se vide
    q = eob(prog(lt, .1, dur * .8))
    r = 286
    lay = Image.new("RGBA", (r * 2 + 60, r * 2 + 60), (0, 0, 0, 0))
    ImageDraw.Draw(lay).arc([30, 30, 30 + r * 2, 30 + r * 2], -90, -90 + 360 * (1 - q),
                            fill=c_(YELLOW, 235), width=8)
    ac(layer, lay, (W / 2 - r - 30, H * .38 - r - 30))
    # anneau de lumière qui pulse
    a = eob(prog(lt, .1, .6))
    for i in range(3):
        r = 270 + i * 34 + lt * 40
        lay = Image.new("RGBA", (int(r * 2 + 80), int(r * 2 + 80)), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([40, 40, 40 + r * 2, 40 + r * 2],
                                    outline=c_(YELLOW, int((50 - i * 12) * a)), width=3)
        ac(layer, lay, (W / 2 - r - 40, H * .40 - r - 40))


def s_pack_shut(layer, lt, dur):
    box = load("box.png")
    bw = 760
    bh = int(box.height * bw / box.width)
    y = H * .28
    # les diapos rentrent dans le pack
    for i, nm in enumerate(["slide_merci", "slide_chiffres", "slide_racontez"]):
        p = 1 - eo(prog(lt, .05 + i * .08, .55))
        side = -1 if i % 2 == 0 else 1
        im = card(load(f"{nm}.png"), 360, tilt=side * 8, radius=12)
        x = (W - im.width) / 2 + side * (300 * p)
        shadowed(layer, alpha(im, p), x, y + 120 + i * 60, blur=28, a=int(140 * p), dy=18)
    k = eob(prog(lt, .45, .35))
    squash = 1 - .035 * math.sin(min(1, k) * math.pi)
    w2, h2 = int(bw * squash), int(bh * (2 - squash))
    glow_blob(layer, W / 2, y + h2 * .5, 300, (140, 190, 255), 70, 110)
    place(layer, box.resize((w2, h2), Image.LANCZOS), (W - w2) / 2, y,
          r=8, blur=34, sa=170, dy=28)
    ground_contact(layer, box.resize((w2, h2), Image.LANCZOS), (W - w2) / 2, y, .8)
    # poussière soulevée
    if k > .4:
        d = ImageDraw.Draw(layer)
        for i in range(14):
            ang = i / 14 * math.pi * 2
            rr = 60 + (k - .4) * 260
            d.ellipse([W / 2 + math.cos(ang) * rr, y + h2 - 20 + math.sin(ang) * rr * .3,
                       W / 2 + math.cos(ang) * rr + 3, y + h2 - 20 + math.sin(ang) * rr * .3 + 3],
                      fill=(200, 220, 255, 60))


def s_wall(layer, lt, dur):
    # la diapo projetée sur un mur, cône de lumière
    im = load("slide_merci.png")
    w = int(W * .84)
    h = int(w * im.height / im.width)
    quad = persp(im.resize((w, h)), w, int(h * 1.02), top=.94, skew=0)
    x = (W - w) / 2
    y = 470 - lt * 8
    cone = Image.new("RGBA", (w + 400, h + 500), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cone)
    cd.polygon([(200, 0), (w + 200, 0), (w + 380, h + 480), (20, h + 480)],
               fill=(140, 190, 255, 26))
    ac(layer, cone.filter(ImageFilter.GaussianBlur(90)), (x - 200, y - 300))
    shadowed(layer, quad, x, y, blur=46, a=170, dy=30)


def s_claim(layer, lt, dur):
    """La promesse, en typographie qui arrive surdimensionnée et se pose."""
    box = load("box.png")
    bw, bh = 600, int(box.height * 600 / box.width)
    pa = eob(prog(lt, 0, .6))
    glow_blob(layer, W / 2, 1500, 320, (120, 180, 255), 70, 120)
    place(layer, alpha(box.resize((bw, bh), Image.LANCZOS), pa * .95),
          (W - bw) / 2, 1120 + (1 - pa) * 40, r=8, blur=30, sa=150, dy=24)

    y = 470
    for i, (txt, col) in enumerate([("Prévente", WHITE), ("ouverte.", YELLOW)]):
        p = prog(lt, .06 + i * .14, .55)
        if p <= 0:
            continue
        e = eob(p)
        sc = 1.55 - .55 * e
        f = F("xb", int(104 * sc))
        w_ = tl(ImageDraw.Draw(Image.new("RGBA", (4, 4))), txt, f, -2)
        lay = Image.new("RGBA", (int(w_) + 40, int(f.size * 1.6)), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((20, lay.height * .78), txt, font=f,
                                 fill=c_(col, int(255 * min(1, p * 2.2))), anchor="ls")
        ac(layer, lay, ((W - w_) / 2 - 20, y))
        y += 165

    if lt > .55:
        q = eob(prog(lt, .55, .6))
        sub = "1 500 modèles animés, 100 % modifiables"
        f2 = F("r", 30)
        d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        tracked(ImageDraw.Draw(layer), ((W - tl(d0, sub, f2)) / 2, 860), sub, f2,
                c_(WHITE, int(240 * q)))


def stamp_img(text="LIVRAISON 24 H"):
    w, h = 620, 240
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w - 8, h - 8], 18, fill=(214, 58, 42, 238),
                        outline=(255, 226, 220, 255), width=7)
    tracked(d, ((w - tl(d, text, F("xb", 56), 1.0)) / 2, h / 2 - 40), text,
            F("xb", 56), c_(WHITE, 255), 1.0)
    tracked(d, ((w - tl(d, "SOUS 24 H APRÈS CONFIRMATION", F("sb", 20), 1.4)) / 2, h / 2 + 40),
            "SOUS 24 H APRÈS CONFIRMATION", F("sb", 20), c_((255, 232, 226), 255), 1.4)
    return im.rotate(-7, resample=Image.BICUBIC, expand=True)


def s_stamp(layer, lt, dur):
    box = load("box.png")
    bw = 660
    bh = int(box.height * bw / box.width)
    y = H * .28
    place(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y,
          r=8, blur=36, sa=170, dy=30)
    ground_contact(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y, .85)
    st = stamp_img()
    p = prog(lt, .25, .30)
    if p > 0:
        e = eob(p)
        sc = 1.30 - .30 * e
        sw2, sh2 = int(st.width * sc), int(st.height * sc)
        sx = W / 2 - sw2 / 2
        sy = y + bh + 6 + (1 - e) * -50
        ac(layer, alpha(st.resize((sw2, sh2), Image.LANCZOS), min(1, p * 2.2)), (sx, sy))
        if p >= 1:
            # secousse du pack + poussière
            d = ImageDraw.Draw(layer)
            for i in range(18):
                ang = i / 18 * math.pi * 2
                rr = 90 + (lt - .55) * 320
                d.ellipse([W / 2 + math.cos(ang) * rr, sy + sh2 / 2 + math.sin(ang) * rr * .4,
                           W / 2 + math.cos(ang) * rr + 5, sy + sh2 / 2 + math.sin(ang) * rr * .4 + 5],
                          fill=(255, 226, 214, 70))


def s_proof_macro(layer, lt, dur):
    """Macro sur la rangée de preuves imprimée sur le pack, pleine largeur."""
    box = load("box.png")
    crop = box.crop((0, int(box.height * .755), box.width, int(box.height * .975)))
    w = int(W * 1.12)
    h = int(crop.height * w / crop.width)
    im = crop.resize((w, h), Image.LANCZOS)
    # bords fondus : la bande sort du cadre, elle ne flotte pas
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rectangle([40, 0, w - 40, h], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(46))
    im.putalpha(ImageChops.multiply(im.getchannel("A"), m))
    p = eo(prog(lt, 0, dur))
    x = -(w - W) / 2 - 10 + p * 34
    place(layer, im, x, 690, r=0, blur=26, sa=140, dy=18)


def cta_pill(text="Commande ton pack"):
    d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = F("xb", 42)
    tw = tl(d0, text, f, .2)
    w, h = int(tw + 150), 132
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=c_(YELLOW, 255))
    d.text((52, h / 2), text, font=f, fill=c_(NAVY, 255), anchor="lm")
    # flèche
    ax = w - 76
    d.line([(ax - 4, h / 2), (ax + 26, h / 2)], fill=c_(NAVY, 255), width=6)
    d.line([(ax + 10, h / 2 - 14), (ax + 26, h / 2)], fill=c_(NAVY, 255), width=6)
    d.line([(ax + 10, h / 2 + 14), (ax + 26, h / 2)], fill=c_(NAVY, 255), width=6)
    return im


def s_cta_press(layer, lt, dur):
    p = cta_pill()
    px = (W - p.width) / 2
    py = H * .40
    press = eob(prog(lt, .55, .18))
    squish = 1 - .05 * press
    pp = p.resize((int(p.width * (1 + .02 * press)), int(p.height * squish)), Image.LANCZOS)
    glow_blob(layer, W / 2, py + 66, 300, (255, 200, 60), int(60 + 60 * press), 90)
    shadowed(layer, pp, (W - pp.width) / 2, py + (1 - .05 * press) * 8,
             blur=30, a=170, dy=22, r=60)
    # ripple
    if lt > .62:
        q = prog(lt, .62, .55)
        r = 120 + q * 380
        lay = Image.new("RGBA", (int(r * 2 + 60), int(r * 2 + 60)), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([30, 30, 30 + r * 2, 30 + r * 2],
                                    outline=c_((255, 220, 110), int(160 * (1 - q))), width=4)
        ac(layer, lay, (W / 2 - r - 30, py + 66 - r - 30))
    # curseur : arrive surdimensionné, se pose, appuie
    e = eob(prog(lt, .05, .5))
    draw_cursor(layer, W / 2 + 30 + (1 - e) * 220, py + 150 + (1 - e) * 120,
                2.3 - 1.3 * e, press=press)


def s_burst(layer, lt, dur):
    a = eob(prog(lt, 0, .45))
    glow_blob(layer, W / 2, H * .40, 300, (255, 236, 180), int(140 * (1 - .35 * a)), 190)
    box = load("box.png")
    bw = 780
    bh = int(box.height * bw / box.width)
    y = H * .18 + (1 - a) * 30
    place(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y,
          r=8, blur=36, sa=170, dy=28)
    p = cta_pill()
    ac(layer, p, ((W - p.width) / 2, H * .70))
    d = ImageDraw.Draw(layer)
    for i in range(16):
        ang = i / 16 * math.pi * 2 + lt * .18
        r0, r1 = 210, 210 + 340 * a
        d.line([(W / 2 + math.cos(ang) * r0, H * .40 + math.sin(ang) * r0),
                (W / 2 + math.cos(ang) * r1, H * .40 + math.sin(ang) * r1)],
               fill=c_((255, 226, 150), int(30 * a)), width=3)


def s_brand(layer, lt, dur):
    box = load("box.png")
    bw = 560
    bh = int(box.height * bw / box.width)
    y = 900 - lt * 10
    place(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y,
          r=8, blur=34, sa=160, dy=26)
    # le mot de marque se dévoile par masque depuis le centre
    p = eob(prog(lt, .15, .9))
    f = F("xb", 96)
    txt = "Digitaward"
    tw = tl(ImageDraw.Draw(Image.new("RGBA", (4, 4))), txt, f, -1.5)
    lay = Image.new("RGBA", (int(tw) + 40, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.text((20, 150), txt, font=f, fill=c_(WHITE, 255), anchor="ls")
    keep = Image.new("L", lay.size, 0)
    ImageDraw.Draw(keep).rectangle([0, 0, int((lay.width) * p), lay.height], fill=255)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), keep))
    ac(layer, lay, ((W - tw) / 2 - 20, 330))
    q = eob(prog(lt, .55, .8))
    if q > 0:
        f2 = F("r", 34)
        t2 = "Le savoir à portée de clic."
        tracked(ImageDraw.Draw(layer), ((W - tl(ImageDraw.Draw(Image.new("RGBA", (4, 4))), t2, f2)) / 2, 520),
                t2, f2, c_(YELLOW, int(240 * q)))


def s_end(layer, lt, dur):
    box = load("box.png")
    bw = 700
    bh = int(box.height * bw / box.width)
    y = 250 - lt * 8
    glow_blob(layer, W / 2, y + bh * .5, 320, (120, 175, 255), 74, 110)
    place(layer, box.resize((bw, bh), Image.LANCZOS), (W - bw) / 2, y,
          r=8, blur=36, sa=160, dy=26)
    p = cta_pill()
    ac(layer, p, ((W - p.width) / 2, 1170))
    t = "Livraison sous 24 h · 100 % modifiable"
    f = F("r", 27)
    tracked(ImageDraw.Draw(layer),
            ((W - tl(ImageDraw.Draw(Image.new("RGBA", (4, 4))), t, f)) / 2, 1300),
            t, f, c_(ICE, 235))
    lc = logo_on_card(300)
    ac(layer, lc, ((W - lc.width) / 2, 1390))
    t2 = "Le savoir à portée de clic."
    f2 = F("r", 28)
    tracked(ImageDraw.Draw(layer),
            ((W - tl(ImageDraw.Draw(Image.new("RGBA", (4, 4))), t2, f2)) / 2, 1610),
            t2, f2, c_(YELLOW, 235))


SCENE_FN = {n: globals()["s_" + n] for n, _, _ in SHOTS}

# recadrage par plan (zoom, (décalage x, décalage y))
FRAMING = {
    "open_macro": 1.0, "room": 1.0, "timelapse": 1.0, "draft": 1.0,
    "picker": 1.0, "fonts": 1.0, "image": 1.0, "mess": 1.02,
    "power_on": 1.02, "pack_rise": 1.0, "pack_macro": 1.0, "pack_hero": 1.0,
    "pack_open": 1.0, "fan_track": 1.06, "four_cuts": 1.02,
    "slide_a": 1.02, "slide_b": 1.02, "slide_c": 1.02, "slide_d": 1.02,
    "use_cases": 1.04, "rewind": 1.0, "pack_shut": 1.0, "wall": 1.06,
    "claim": 1.0, "stamp": 1.0, "proof_macro": 1.0, "cta_press": 1.0, "burst": 1.0,
    "brand": 1.0, "end": 1.0,
}
# valeurs négatives = sujet descendu dans le cadre
FRAMING_SHIFT = {
    "open_macro": (0, 20), "room": (0, 60), "timelapse": (0, 60),
    "draft": (0, 90), "picker": (0, 130), "fonts": (0, 130), "image": (0, 130),
    "mess": (0, 90), "power_on": (0, 90), "pack_open": (0, 90),
    "fan_track": (0, 40), "four_cuts": (0, 130), "slide_a": (0, 120),
    "slide_b": (0, 120), "slide_c": (0, 120), "slide_d": (0, 120),
    "use_cases": (0, 30), "rewind": (0, 40), "pack_shut": (0, 90),
    "wall": (0, 120), "brand": (0, 100), "end": (0, 120), "cta_press": (0, 10),
}


def shot_at(t):
    for i, (n, a, b) in enumerate(SHOTS):
        if a <= t < b:
            return i, n, t - a, b - a
    return len(SHOTS) - 1, SHOTS[-1][0], t - SHOTS[-1][1], SHOTS[-1][2] - SHOTS[-1][1]


def render_frame(fi):
    t = fi / FPS
    i, name, lt, dur = shot_at(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENE_FN[name](layer, lt, dur)
    # cadrage : le sujet occupe 60-85 % de la hauteur utile
    z = FRAMING.get(name, 1.0)
    if z:
        sx_, sy_ = FRAMING_SHIFT.get(name, (0, 0))
        layer = layer.transform((W, H), Image.AFFINE,
                                (1 / z, 0, W / 2 - W / (2 * z) - sx_,
                                 0, 1 / z, H / 2 - H / (2 * z) - sy_),
                                resample=Image.BICUBIC)
    base = stage_frame(t, flare=(1.0 if name == "burst" else 0.0))
    base.alpha_composite(layer)

    # caméra : poussée permanente + micro-tremblement
    p = clamp01(lt / max(dur, 1e-4))
    zoom = 1.045 + .050 * p
    if name in ("pack_hero",):
        zoom = 1.16 - .13 * eob(prog(lt, 0, .6))
    if name in ("open_macro",):
        zoom = 1.10 - .06 * p
    if name in ("line",):
        zoom = 1.02 + .05 * p
    img = camera(base, zoom, 0, 0, t)
    img = finish(img, t)
    return img.convert("RGB")


def preview(path):
    cols, rows = 4, 4
    tw, th = 336, 597
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (8, 10, 26))
    sd = ImageDraw.Draw(sheet)
    picks = []
    for i, (n, a, b) in enumerate(SHOTS):
        if i % 2 == 0 or i == len(SHOTS) - 1:
            picks.append(((a + b) / 2, n))
    picks = picks[:cols * rows]
    for k, (t, n) in enumerate(picks):
        im = render_frame(int(t * FPS)).resize((tw, th), Image.LANCZOS)
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)
        sheet.paste(im, (x, y))
        sd.rectangle([x, y, x + 132, y + 22], fill=(0, 0, 0))
        sd.text((x + 4, y + 4), f"{t:05.2f}s {n}", font=F("sb", 15), fill=(255, 255, 255))
    sheet.save(path, quality=90)
    print("Saved preview:", path)


# ---------------------------------------------------------------- audio
def _noise(n, lo, hi, seed=0):
    from build_film import _noise as nz
    return nz(n, lo, hi, seed)


def build_audio_v2():
    from imageio_ffmpeg import get_ffmpeg_exe
    from scipy.signal import butter, sosfilt
    ff = get_ffmpeg_exe()
    n = int(TOTAL * SR)
    m = np.zeros(n, np.float32)
    bpm = 122.0
    beat = 60 / bpm

    # cœur : kick, clap, hats, basse — même grammaire que la v1
    t0 = 0
    while t0 < TOTAL:
        s = int(t0 * SR)
        ln = min(n - s, int(.28 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 118 * np.exp(-tt * 18) + 46
            m[s:s + ln] += (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 13) * .40).astype(np.float32)
        t0 += beat
    for b in range(int(TOTAL / beat) + 1):
        if b % 4 in (1, 3):
            s = int(b * beat * SR)
            ln = min(n - s, int(.2 * SR))
            if ln > 0:
                m[s:s + ln] += (_noise(ln, 1400, 6000, seed=b) * np.exp(-np.arange(ln) / SR * 24) * .15).astype(np.float32)
    b = 0
    while b * beat / 2 < TOTAL:
        s = int(b * beat / 2 * SR)
        ln = min(n - s, int(.05 * SR))
        if ln > 0:
            m[s:s + ln] += (_noise(ln, 7000, 16000, seed=b + 9) * np.exp(-np.arange(ln) / SR * 160) * (.045 if b % 2 == 0 else .028)).astype(np.float32)
        b += 1
    roots = [65.41, 87.31, 98.0, 73.42]
    bar = beat * 4
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
            m[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * .28).astype(np.float32)
        k += 1

    # impacts sur les coupes structurantes
    for c in AUDIO_CUTS:
        s = int(c * SR)
        ln = min(n - s, int(.7 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            boom = np.sin(2 * np.pi * (68 * tt - 16 * tt ** 2)) * np.exp(-tt * 8)
            m[s:s + ln] += (boom * .30).astype(np.float32)

    # whooshs doux sur les transitions de scène
    for c in AUDIO_CUTS[1:]:
        s = int((c - .16) * SR)
        ln = min(n - max(s, 0), int(.40 * SR))
        if ln > 0 and s >= 0:
            tt = np.arange(ln) / SR
            m[s:s + ln] += (_noise(ln, 320, 6500, seed=int(c * 10)) *
                            np.sin(np.pi * tt / .40) ** 1.6 * .11).astype(np.float32)

    # clic du curseur, tampon, bouton pressé
    for tp, kind in [(6.75, "click"), (7.55, "click"), (9.35, "click"),
                     (36.10, "thud"), (39.40, "click"), (39.52, "pop")]:
        s = int(tp * SR)
        ln = min(n - s, int((.25 if kind != "thud" else .45) * SR))
        if ln <= 0:
            continue
        tt = np.arange(ln) / SR
        if kind == "click":
            v = _noise(ln, 1800, 9000, seed=int(tp * 100)) * np.exp(-tt * 220) * .22
        elif kind == "thud":
            v = (np.sin(2 * np.pi * (92 * tt - 30 * tt ** 2)) * np.exp(-tt * 11) * .42 +
                 _noise(ln, 200, 3000, seed=5) * np.exp(-tt * 40) * .18)
        else:
            v = np.sin(2 * np.pi * 880 * tt) * np.exp(-tt * 26) * .10
        m[s:s + ln] += v.astype(np.float32)

    # voix off (mêmes prises, mêmes départs)
    vo = np.zeros(n, np.float32)
    for k_i, (fname, start, tempo) in enumerate(VO, start=1):
        dst = f"/tmp/_dwvo2_{k_i}.wav"
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", os.path.join(AUD, fname), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                        f"areverse,atempo={tempo:.4f}", "-ar", str(SR), "-ac", "1", dst], check=True)
        with wavemod.open(dst, "rb") as w:
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        s = int(start * SR)
        e = min(n, s + len(a))
        if s < n:
            vo[s:e] += a[:e - s] * 1.12

    # ducking + stéréo
    env = np.abs(vo)
    win = int(.12 * SR)
    env = np.convolve(env, np.ones(win, np.float32) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 3.4, 0, 1)
    m *= (1 - .62 * env)
    dly = int(.011 * SR)
    mix = m + vo
    left = mix
    right = np.concatenate([np.zeros(dly, np.float32), mix[:-dly]])
    st = np.stack([left * .97 + right * .09, right * .97 + left * .09], axis=1)
    st = st / (np.abs(st).max() + 1e-9) * .9
    raw = "/tmp/_dw_raw2.wav"
    with wavemod.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", raw, "-af",
                    "highpass=f=42,equalizer=f=2100:width_type=o:width=1.2:g=2.2,"
                    "volume=5.0dB,alimiter=limit=0.88:level=disabled",
                    "-ar", str(SR), MIX2], check=True)
    return MIX2


def render():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    nf = int(round(TOTAL * FPS))
    tmp = "/tmp/dw_v2_video.mp4"
    p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
                         stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(render_frame(fi).tobytes())
        if fi % 200 == 0:
            print(f"  {fi}/{nf} ({fi / nf * 100:.0f}%)", flush=True)
    p.stdin.close()
    p.wait()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", tmp, "-i", MIX2,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", OUT2], check=True)
    print("Rendered", OUT2, f"({os.path.getsize(OUT2) / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--frame", type=int)
    a = ap.parse_args()
    if a.frame is not None:
        render_frame(a.frame).save(f"/tmp/dw_v2_f{a.frame}.jpg", quality=92)
        print("frame", a.frame)
        return
    if a.preview:
        preview(a.preview)
        return
    print("Voix off + musique ...")
    build_audio_v2()
    if a.audio_only:
        print("Audio ->", MIX2)
        return
    render()


if __name__ == "__main__":
    main()
