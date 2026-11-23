#!/usr/bin/env python3
"""DISCIPLINE — « La discipline bat la motivation » · 9:16 · ~56 s.

Film composé de **visuels trouvés sur le web** (recherche d'images : photos
libres de banques + un GIF de pluie), de **motion design généré** et d'une
**voix off FR**. Aucun rush du dépôt n'est utilisé.

Méthode MOTION-DESIGN.md :
  - un seul point focal animé par plan (la typo), le reste est discret ;
  - chaque groupe de mots entre par masque + montée décalée (40–80 ms/word) ;
  - transitions franches (whip-pan, flash 2 images), jamais de fondu mou ;
  - durées 160–520 ms, courbes cubic-bezier(.22,1,.36,1).

Plans :
  1. 0,0 → 8,4    motivation vs discipline (crosswalk, compteur 1 jour sur 3)
  2. 8,4 → 18,6   la décision répétée (bureau de nuit + GIF pluie)
  3. 18,6 → 28,4  trois règles (motion design pur, chiffres qui se dessinent)
  4. 28,4 → 37,4  un jour d'avance (course, grille de jours J+1 → J+30)
  5. 37,4 → 44,0  des répétitions, pas de la vitesse (barre, reps)
  6. 44,0 → 52,4  tiens ta promesse (carnet, checklist animée)
  7. 52,4 → 56,4  carton final

    python3 build_discipline.py --preview /tmp/prev.jpg
    python3 build_discipline.py --audio-only
    python3 build_discipline.py
"""
import argparse
import os
import re
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PHOTOS = os.path.join(PROJ, "assets", "photos")
AUDIO = os.path.join(PROJ, "assets", "audio")
FILM = os.path.join(PROJ, "film")
OUT = os.path.join(FILM, "discipline-bat-la-motivation-9x16.mp4")
MIX = os.path.join(AUDIO, "mix_discipline.wav")
TMP = "/tmp/discipline_video.mp4"
GIF = os.path.join(PROJ, "assets", "gifs", "rain_window.gif")

W, H, FPS, SR = 1080, 1920, 30, 48000
M = 84
CW = W - 2 * M

# ---------------------------------------------------------------- tokens
INK = (9, 9, 10)
INK2 = (16, 16, 18)
CREAM = (244, 241, 234)
MUTED = (163, 158, 148)
AMBER = (255, 122, 46)
AMBER_D = (214, 88, 20)
DIM = (74, 70, 64)

FB = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
FONTS = {
    "d7": f"{FB}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "d6": f"{FB}/space-grotesk/600SemiBold/SpaceGrotesk_600SemiBold.ttf",
    "d5": f"{FB}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
    "d4": f"{FB}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
    "ser": f"{FB}/instrument-serif/400Regular/InstrumentSerif_400Regular.ttf",
    "seri": f"{FB}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
    "i4": f"{FB}/inter/400Regular/Inter_400Regular.ttf",
    "i5": f"{FB}/inter/500Medium/Inter_500Medium.ttf",
    "i6": f"{FB}/inter/600SemiBold/Inter_600SemiBold.ttf",
}
_F = {}


def F(kind, size):
    size = max(8, int(round(size)))
    k = (kind, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(FONTS[kind], size)
    return _F[k]


def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def eo(t):            # ease-out cubic
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def eob(t):           # ease-out quint (plus sec, "premium")
    t = clamp01(t)
    return 1 - (1 - t) ** 5


def eio(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < .5 else 1 - ((-2 * t + 2) ** 3) / 2


def prog(t, a, d):
    return clamp01((t - a) / d) if d > 0 else float(t >= a)


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


def para(d, text, f, fill, x, y, maxw, lh=1.4, tracking=0.0):
    """Paragraphe avec retours à la ligne explicites (\n) respectés."""
    lines = []
    for block in text.split("\n"):
        cur = ""
        for word in block.split(" "):
            test = (cur + " " + word).strip()
            if tl(d, test, f, tracking) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    step = int(f.size * lh)
    for i, ln in enumerate(lines):
        tracked(d, (x, y + i * step), ln, f, fill, tracking)
    return len(lines) * step


# ---------------------------------------------------------------- timeline
CUTS = [0.00, 8.40, 18.60, 28.40, 37.40, 44.00, 52.40, 56.40]
SCENES = ["hook", "decision", "regles", "avance", "reps", "promesse", "outro"]
TOTAL = CUTS[-1]
NFR = int(round(TOTAL * FPS))

# voix off : (fichier, démarrage) — mesuré, aucune prise ne se chevauche
VO = [("vo1.mp3", 0.55), ("vo2.mp3", 8.75), ("vo3.mp3", 18.85),
      ("vo4.mp3", 28.65), ("vo5.mp3", 37.60), ("vo6.mp3", 44.20)]

# ---------------------------------------------------------------- images
def _cover(im, w, h, zoom=1.0, ox=0.5, oy=0.5):
    """Recadre « cover » avec zoom et point d'intérêt, puis redimensionne."""
    src = im
    sw, sh = src.size
    scale = max(w / sw, h / sh) * zoom
    nw, nh = int(sw * scale) + 1, int(sh * scale) + 1
    src = src.resize((nw, nh), Image.LANCZOS)
    x = int((nw - w) * ox)
    y = int((nh - h) * oy)
    return src.crop((x, y, x + w, y + h))


def grade(im, warm=1.06, desat=0.78, contrast=1.10, lift=0.0):
    im = ImageEnhance.Color(im).enhance(desat)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * warm)))
    b = b.point(lambda v: min(255, int(v * (2 - warm) * 0.96)))
    im = Image.merge("RGB", (r, g, b))
    if lift:
        im = Image.blend(im, Image.new("RGB", im.size, INK), lift)
    return im


def scrim(im, top=0.20, bottom=0.85, side=0.0):
    """Dégradé sombre haut/bas pour la lisibilité du texte."""
    ov = Image.new("L", (1, H))
    px = ov.load()
    for y in range(H):
        u = y / (H - 1)
        a = top * (1 - min(1, u / 0.45)) if u < 0.45 else 0
        if u > 0.42:
            a = max(a, bottom * ((u - 0.42) / 0.58) ** 1.25)
        px[0, y] = int(a * 255)
    ov = ov.resize((W, H))
    shade = Image.new("RGB", (W, H), INK)
    return Image.composite(shade, im, ov)


def vignette(im, strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vx = (xx - W / 2) / (W * 0.62)
    vy = (yy - H / 2) / (H * 0.62)
    m = np.clip(1.0 - strength * (vx * vx + vy * vy), 0.25, 1.0)
    arr = np.asarray(im, np.float32) * m[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


_PHOTO_CACHE = {}


def photo(name, zoom=1.08, ox=0.5, oy=0.5, blur=0.0, warm=1.06, desat=0.78):
    """Photo recadrée + étalonnée, mise en cache par état (zoom quantifié)."""
    key = (name, round(zoom, 3), round(ox, 3), round(oy, 3), blur, warm, desat)
    if key in _PHOTO_CACHE:
        return _PHOTO_CACHE[key].copy()
    im = Image.open(os.path.join(PHOTOS, name)).convert("RGB")
    im = _cover(im, W, H, zoom, ox, oy)
    if im.width < W:
        pass
    im = grade(im, warm=warm, desat=desat)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if len(_PHOTO_CACHE) > 40:
        _PHOTO_CACHE.clear()
    _PHOTO_CACHE[key] = im
    return im.copy()


def kenburns(name, t, dur, z0=1.05, z1=1.22, ox0=.5, ox1=.5, oy0=.5, oy1=.5, **kw):
    u = clamp01(t / max(dur, .001))
    e = 0.35 * u + 0.65 * eio(u)
    return photo(name, z0 + (z1 - z0) * e, ox0 + (ox1 - ox0) * e, oy0 + (oy1 - oy0) * e, **kw)


def add_grain(im, t, amount=3.4, scale=2):
    """Grain fin (2 px) et stable ~12 fois/s : texture, pas de fourmillement."""
    rng = np.random.default_rng(int(t * 12) + 7)
    hh, ww = H // scale, W // scale
    n = rng.normal(0, amount, (hh, ww, 1)).astype(np.float32)
    n = np.repeat(n, 3, axis=2).repeat(scale, axis=0).repeat(scale, axis=1)[:H, :W]
    arr = np.asarray(im, np.float32) + n
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


_GIF_FRAMES = None


def gif_frames():
    global _GIF_FRAMES
    if _GIF_FRAMES is None:
        im = Image.open(GIF)
        frames = []
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i)
            f = im.convert("RGB").resize((W, H), Image.LANCZOS)
            frames.append(f)
        _GIF_FRAMES = frames or [im.convert("RGB").resize((W, H))]
    return _GIF_FRAMES


# ---------------------------------------------------------------- typo animée
def words_in(canvas, d, text, x, y, size, kind="d5", color=CREAM, p=0.0,
             stagger=0.055, tracking=-2.0, lead=1.05, weight=None):
    """Chaque mot entre par un masque vertical décalé (40–80 ms)."""
    if p <= 0:
        return 0
    f = F(kind, size)
    words = text.split(" ")
    widths = [tl(d, w, f, tracking) for w in words]
    space = size * 0.28
    cx = x
    for i, (w, wd) in enumerate(zip(words, widths)):
        pw = prog(p, i * stagger, 0.42)
        if pw > 0:
            e = eob(pw)
            lay = Image.new("L", (int(wd) + 24, int(size * 1.5)), 0)
            ld = ImageDraw.Draw(lay)
            tracked(ld, (0, size * 0.16), w, f, 255, tracking)
            col = Image.new("RGBA", lay.size, c_(color, 255))
            col.putalpha(lay)
            keep = Image.new("L", lay.size, 0)
            ImageDraw.Draw(keep).rectangle([0, 0, lay.width, int(lay.height * min(1, e * 1.1))],
                                           fill=255)
            col.putalpha(ImageChops.multiply(col.getchannel("A"), keep))
            canvas.alpha_composite(col, (int(cx), int(y + (1 - e) * size * 0.35)))
        cx += wd + space
    return cx - x


def line_in(canvas, d, text, x, y, size, kind="d5", color=CREAM, p=0.0, tracking=-3.0):
    if p <= 0:
        return 0
    e = eob(p)
    f = F(kind, size)
    wd = tl(d, text, f, tracking)
    lay = Image.new("L", (int(wd) + 30, int(size * 1.5)), 0)
    tracked(ImageDraw.Draw(lay), (0, size * 0.16), text, f, 255, tracking)
    col = Image.new("RGBA", lay.size, c_(color, 255))
    col.putalpha(lay)
    keep = Image.new("L", lay.size, 0)
    ImageDraw.Draw(keep).rectangle([0, 0, lay.width, int(lay.height * min(1, e * 1.08))], fill=255)
    col.putalpha(ImageChops.multiply(col.getchannel("A"), keep))
    canvas.alpha_composite(col, (int(x), int(y + (1 - e) * size * 0.2)))
    return wd


def big_line(canvas, d, parts, x, y, size, p=0.0, tracking=-4.0, lead=None):
    """Ligne mixte grotesk + serif italique, révélée d'un bloc (masque commun)."""
    if p <= 0:
        return 0
    e = eob(p)
    fonts, widths = [], []
    for txt, kind in parts:
        f = F(kind, size * (1.05 if kind in ("seri", "ser") else 1.0))
        fonts.append(f)
        widths.append(tl(d, txt, f, tracking))
    total = sum(widths) + size * 0.05 * (len(parts) - 1)
    lh = int(size * 1.18)
    lay = Image.new("L", (int(total) + 80, int(lh * 1.35)), 0)
    ld = ImageDraw.Draw(lay)
    cx = 0
    for (txt, kind), f, wd in zip(parts, fonts, widths):
        tracked(ld, (cx, lh * (0.27 if kind in ("seri", "ser") else 0.20)), txt, f, 255,
                tracking * (0.8 if kind in ("seri", "ser") else 1))
        cx += wd + size * 0.05
    col = Image.new("RGBA", lay.size, c_(CREAM, 255))
    col.putalpha(lay)
    keep = Image.new("L", lay.size, 0)
    ImageDraw.Draw(keep).rectangle([0, 0, lay.width, int(lay.height * min(1, e * 1.08))], fill=255)
    col.putalpha(ImageChops.multiply(col.getchannel("A"), keep))
    acol = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    # les mots serif prennent l'ambre
    am = Image.new("RGBA", lay.size, c_(AMBER, 255))
    am.putalpha(0)
    canvas.alpha_composite(col, (int(x), int(y + (1 - e) * size * 0.18)))
    return total


def amber_serif(d, canvas, text, x, y, size, p=0.0, tracking=-2.0):
    if p <= 0:
        return
    e = eob(p)
    f = F("seri", size)
    wd = tl(d, text, f, tracking)
    lay = Image.new("L", (int(wd) + 30, int(size * 1.5)), 0)
    tracked(ImageDraw.Draw(lay), (0, size * 0.14), text, f, 255, tracking)
    col = Image.new("RGBA", lay.size, c_(AMBER, 255))
    col.putalpha(lay)
    keep = Image.new("L", lay.size, 0)
    ImageDraw.Draw(keep).rectangle([0, 0, lay.width, int(lay.height * min(1, e * 1.08))], fill=255)
    col.putalpha(ImageChops.multiply(col.getchannel("A"), keep))
    canvas.alpha_composite(col, (int(x), int(y + (1 - e) * size * 0.2)))


def chip(canvas, text, x, y, p=0.0, color=CREAM, dot=AMBER, size=20):
    if p <= 0:
        return
    e = eob(p)
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = F("i5", size)
    wd = tl(d, text, f, 0.6) + size * 2.2 + size * 1.1
    h = int(size * 1.7)
    im = Image.new("RGBA", (int(wd), h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, im.width - 1, h - 1], h // 2, fill=(18, 18, 20, 232),
                         outline=(244, 241, 234, 44), width=1)
    dd.ellipse([size * 1.1, h / 2 - size * .17, size * 1.1 + size * .34, h / 2 + size * .17],
               fill=c_(dot, 240))
    dd.text((size * 1.9, (h - size * 1.25) / 2), text, font=f, fill=c_(color, 238))
    canvas.alpha_composite(Image.blend(Image.new("RGBA", im.size, (0, 0, 0, 0)), im, e),
                           (int(x), int(y + (1 - e) * 12)))


def hairline(d, y, p=1.0, x0=M, x1=W - M, col=CREAM, alpha=40):
    if p <= 0:
        return
    w = int((x1 - x0) * eob(p))
    d.line([(x0, y), (x0 + w, y)], fill=c_(col, alpha), width=1)


def flash(canvas, lt, dur=0.14, strength=34):
    if 0 <= lt < dur:
        k = 1 - lt / dur
        lay = Image.new("RGBA", (W, H), c_(AMBER, int(strength * k)))
        canvas.alpha_composite(lay.filter(ImageFilter.GaussianBlur(90)))


def whip(canvas, lt, dur=0.18, amp=90):
    """Whip-pan vertical : flou directionnel + décalage sur l'entrée de plan."""
    if 0 <= lt < dur:
        k = 1 - lt / dur
        arr = np.asarray(canvas.convert("RGB"), np.float32)
        sh = int(amp * k)
        if sh > 1:
            arr = np.roll(arr, sh, axis=0)
            for i in range(1, 4):
                arr += np.roll(arr, i * sh // 4, axis=0) * 0.25
            arr /= 1.75
        canvas.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 0))


# ---------------------------------------------------------------- scènes
def s_hook(canvas, t, dur):
    d = ImageDraw.Draw(canvas)
    # photo : passage piéton au petit matin, très légère avance
    bg = kenburns("crosswalk.jpg", t, dur, 1.06, 1.20, .52, .48, .40, .55, desat=.50, warm=1.02)
    bg = Image.blend(bg, Image.new("RGB", (W, H), INK), 0.34)
    canvas.paste(scrim(bg, .46, .90), (0, 0))

    # badge
    chip(canvas, "DISCIPLINE · ENTREPRENEURIAT", M, 236, prog(t, 0.15, 0.5), size=18)
    hairline(d, 320, prog(t, 0.25, 0.6), x1=W - M, alpha=60)

    # titre : « La motivation » plein / « va et vient. » serif
    words_in(canvas, d, "La motivation", M, 400, 118, "d5", CREAM, prog(t, 0.30, 0.9), 0.07, -4.5)
    amber_serif(d, canvas, "va et vient.", M, 556, 132, prog(t, 0.75, 0.6))
    words_in(canvas, d, "La discipline, elle,", M, 760, 62, "d4", CREAM, prog(t, 1.15, 0.8), 0.05, -1.6)
    words_in(canvas, d, "ne dépend pas de ton humeur.", M, 830, 62, "d4", MUTED,
             prog(t, 1.5, 0.8), 0.045, -1.6)

    # compteur « 1 jour sur 3 » (motion design)
    pa = prog(t, 3.05, 0.7)
    if pa > 0:
        y = 1086
        d.rounded_rectangle([M, y, W - M, y + 330], 26, fill=(13, 13, 15, 238),
                            outline=(244, 241, 234, 40), width=1)
        tracked(d, (M + 40, y + 38), "SUR 3 JOURS", F("i6", 19), c_(MUTED, 220 * eo(pa)), 3.4)
        # trois cases, une seule pleine
        for i in range(3):
            bx = M + 40 + i * 150
            fill_p = prog(t, 3.35 + i * 0.22, 0.45)
            on = i == 0
            d.rounded_rectangle([bx, y + 90, bx + 116, y + 206], 14,
                                fill=c_(AMBER if on else (22, 22, 25), 255 * eo(fill_p)),
                                outline=(244, 241, 234, 55), width=1)
            if on:
                tracked(d, (bx + 34, y + 118), "1", F("d7", 56), c_(INK, 245 * eo(fill_p)), -2)
            else:
                tracked(d, (bx + 40, y + 124), "0", F("d7", 44), c_(DIM, 200 * eo(fill_p)), -2)
        # grand chiffre animé
        cnt = int(round(3 * eo(prog(t, 3.3, 0.9))))
        tracked(d, (M + 520, y + 84), f"{max(1, cnt)}", F("d7", 120),
                c_(CREAM, 250 * eo(pa)), -6)
        tracked(d, (M + 620, y + 128), "/ 3", F("d5", 40), c_(MUTED, 230 * eo(pa)), -2)
        para(d, "jours où l'envie est là.\nLes deux autres, c'est la discipline qui travaille.",
             F("i4", 25), c_(CREAM, 225 * eo(prog(t, 4.0, 0.6))), M + 40, y + 240, CW - 80, 1.4)

    # sortie : ligne + mot-clé
    words_in(canvas, d, "Pas ton humeur. Ta décision.", M, 1580, 44, "d5",
             c_(CREAM, 240), prog(t, 5.5, 0.8), 0.06, -1.2)


def s_decision(canvas, t, dur):
    d = ImageDraw.Draw(canvas)
    bg = kenburns("desk_night.jpg", t, dur, 1.10, 1.26, .45, .55, .45, .40, desat=.40, warm=1.10)
    canvas.paste(scrim(bg, .34, .86), (0, 0))

    # GIF de pluie en surimpression (texture animée trouvée sur le web)
    ga = 0.20 * eo(prog(t, 0.2, 1.2))
    if ga > 0:
        gf = gif_frames()[int(t * 12) % len(gif_frames())]
        gf = ImageOps.colorize(ImageOps.grayscale(gf), INK, CREAM)
        mask = Image.new("L", (W, H), int(255 * ga))
        canvas.alpha_composite(Image.composite(gf.convert("RGBA"),
                                               Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))

    chip(canvas, "LA DÉCISION", M, 236, prog(t, 0.12, 0.45), size=18)

    words_in(canvas, d, "Une décision", M, 392, 104, "d5", CREAM, prog(t, 0.3, 0.8), 0.07, -4)
    words_in(canvas, d, "que tu répètes", M, 508, 104, "d5", CREAM, prog(t, 0.62, 0.8), 0.07, -4)
    amber_serif(d, canvas, "quand personne", M, 628, 112, prog(t, 0.95, 0.6))
    amber_serif(d, canvas, "ne regarde.", M, 738, 112, prog(t, 1.12, 0.6))

    # deux règles : créneau + priorité
    rows = [("01", "Un créneau non négociable", "la même heure, chaque jour"),
            ("02", "Une priorité par jour", "une seule — pas dix")]
    for i, (num, title, sub) in enumerate(rows):
        p = prog(t, 2.35 + i * 0.55, 0.55)
        if p <= 0:
            continue
        y = 986 + i * 214
        e = eob(p)
        d.rounded_rectangle([M, y + (1 - e) * 26, W - M, y + 182 + (1 - e) * 26], 18,
                            fill=(12, 12, 14, 232), outline=(244, 241, 234, 42), width=1)
        d.rectangle([M, y + (1 - e) * 26, M + 6, y + 182 + (1 - e) * 26], fill=c_(AMBER, 240 * e))
        tracked(d, (M + 34, y + 26 + (1 - e) * 26), num, F("i6", 18), c_(AMBER, 235 * e), 3)
        tracked(d, (M + 34, y + 60 + (1 - e) * 26), title, F("d5", 40), c_(CREAM, 245 * e), -1.6)
        d.text((M + 34, y + 122 + (1 - e) * 26), sub, font=F("i4", 24), fill=c_(MUTED, 220 * e))

    # phrase de sortie
    p = prog(t, 4.4, 0.9)
    if p > 0:
        words_in(canvas, d, "Ce n'est pas un trait de caractère.", M, 1478, 32,
                 "i4", c_(CREAM, 240), p, 0.05, -0.5)
        words_in(canvas, d, "C'est une habitude qui se protège.", M, 1526, 32,
                 "i4", c_(AMBER, 240), prog(t, 4.9, 0.9), 0.05, -0.5)


def s_regles(canvas, t, dur):
    """Motion design pur : trois règles qui se dessinent."""
    d = ImageDraw.Draw(canvas)
    canvas.paste(Image.new("RGB", (W, H), INK), (0, 0))
    # halo
    hal = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(hal).ellipse([-200, -260, W + 200, 900], fill=(255, 122, 46, 26))
    canvas.alpha_composite(hal.filter(ImageFilter.GaussianBlur(150)))

    # photo très sombre en texture de fond
    bg = photo("weights.jpg", 1.15, .5, .5, blur=2.4, desat=.15, warm=1.0)
    canvas.alpha_composite(Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                                       bg.convert("RGBA"), 0.22))
    canvas.alpha_composite(Image.new("RGBA", (W, H), (9, 9, 10, 120)))

    tracked(d, (M, 240), "TROIS RÈGLES", F("i6", 18), c_(MUTED, 235), 3.6)
    hairline(d, 300, prog(t, 0.1, 0.5), alpha=45)
    words_in(canvas, d, "Tu ne gagnes pas", M, 360, 96, "d5", CREAM, prog(t, 0.2, 0.8), 0.07, -4)
    words_in(canvas, d, "avec de la volonté.", M, 468, 96, "d5", CREAM, prog(t, 0.5, 0.8), 0.07, -4)
    amber_serif(d, canvas, "Tu gagnes avec un système.", M, 600, 74, prog(t, 0.85, 0.7))

    rules = [("01", "UNE priorité", "pas trois, pas dix"),
             ("02", "90 minutes", "sans téléphone, sans onglet"),
             ("03", "Zéro renégociation", "la décision est prise la veille")]
    for i, (num, title, sub) in enumerate(rules):
        p = prog(t, 1.55 + i * 0.95, 0.62)
        if p <= 0:
            continue
        e = eob(p)
        y = 830 + i * 262
        # trait qui se dessine
        d.line([(M, y - 26), (M + CW * eio(p), y - 26)], fill=c_(CREAM, 46), width=2)
        # pastille numéro
        r = 44 * e
        d.ellipse([M, y + 26 + (1 - e) * 20, M + 2 * r, y + 26 + 2 * r + (1 - e) * 20],
                  outline=c_(AMBER, 245 * e), width=2)
        tracked(d, (M + r - 16, y + 40 + (1 - e) * 20), num, F("d6", 26), c_(AMBER, 245 * e), 1)
        words_in(canvas, d, title, M + 140, y + 10, 74, "d5", CREAM, prog(p, 0.08, 0.7), 0.06, -2.4)
        words_in(canvas, d, sub, M + 140, y + 100, 30, "i4", MUTED, prog(p, 0.22, 0.7), 0.03, -0.4)
        # marqueur chiffré, aligné à droite sur la ligne du filet (jamais sur le titre)
        marks = {0: "×1", 1: "90 min", 2: "0"}
        mw = tl(d, marks[i], F("d6", 26), 1.4)
        tracked(d, (W - M - mw, y - 60), marks[i], F("d6", 26), c_(AMBER, 230 * e), 1.4)

    words_in(canvas, d, "C'est tout. Le reste, c'est du bruit.", M, 1652, 30, "i4",
             c_(MUTED, 235), prog(t, 4.6, 0.9), 0.04, -0.2)


def s_avance(canvas, t, dur):
    d = ImageDraw.Draw(canvas)
    # plan large : la course dans le brouillard, puis un panneau pour la grille de jours
    bg = kenburns("run_fog.jpg", t, dur, 1.04, 1.16, .62, .50, .5, .5, desat=.40, warm=1.02)
    bg = Image.blend(bg, Image.new("RGB", (W, H), INK), 0.40)
    canvas.paste(scrim(bg, .55, .52), (0, 0))

    tracked(d, (M, 250), "UN JOUR D'AVANCE", F("i6", 18), c_(AMBER, 240), 3.4)
    words_in(canvas, d, "Chaque jour où", M, 330, 88, "d5", CREAM, prog(t, 0.2, 0.7), 0.06, -3.4)
    words_in(canvas, d, "tu tiens,", M, 424, 88, "d5", CREAM, prog(t, 0.45, 0.7), 0.06, -3.4)
    words_in(canvas, d, "tu prends de l'avance.", M, 518, 88, "d5", CREAM, prog(t, 0.7, 0.8), 0.05, -3.4)

    # grille de jours J+1 → J+30 dans un panneau (motion design)
    pa = prog(t, 1.95, 1.5)
    if pa > 0:
        pw = 980
        d.rounded_rectangle([M, 940, M + pw, 1560], 26, fill=(11, 11, 13, 236),
                            outline=(244, 241, 234, 40), width=1)
        x0, y0 = M + 46, 1024
        cols, cell, gap = 10, 74, 14
        shown = int(30 * eo(pa))
        for i in range(30):
            r_, c = divmod(i, cols)
            x = x0 + c * (cell + gap)
            y = y0 + r_ * (cell + gap)
            on = i < shown
            done = i < 7            # une semaine tenue
            if on:
                d.rounded_rectangle([x, y, x + cell, y + cell], 12,
                                    fill=c_(AMBER if done else (28, 28, 32), 255 if done else 235),
                                    outline=(244, 241, 234, 40), width=1)
            else:
                d.rounded_rectangle([x, y, x + cell, y + cell], 12,
                                    outline=(244, 241, 234, 24), width=1)
        tracked(d, (W - M - 46 - 96, 962), f"J+{shown:02d}", F("d7", 38), c_(CREAM, 250), -1.6)
        para(d, "Sept jours tenus changent la trajectoire.\nTrente jours changent la réputation.",
             F("i4", 24), c_(CREAM, 232 * eo(prog(t, 3.4, 0.8))), x0, y0 + 3 * (cell + gap) + 24,
             pw - 110, 1.4)

    p = prog(t, 5.0, 0.9)
    if p > 0:
        words_in(canvas, d, "La constance bat le talent.", M, 1640, 46, "d5", CREAM, p, 0.06, -1.6)
        if prog(t, 5.6, 0.35) > 0:
            f = F("d5", 46)
            wd = tl(d, "La constance bat ", f, -1.6)
            tw_ = tl(d, "le talent.", f, -1.6)
            seg = tw_ * eob(prog(t, 5.6, 0.35))
            d.line([(M + wd, 1666), (M + wd + seg, 1666)], fill=c_(AMBER, 245), width=4)


def s_reps(canvas, t, dur):
    d = ImageDraw.Draw(canvas)
    bg = kenburns("barbell.jpg", t, dur, 1.22, 1.06, .5, .5, .52, .48, desat=.30, warm=1.06)
    canvas.paste(scrim(bg, .40, .82), (0, 0))

    tracked(d, (M, 250), "RÉPÉTITIONS", F("i6", 18), c_(AMBER, 240), 3.6)
    words_in(canvas, d, "Ce n'est pas", M, 360, 96, "d5", CREAM, prog(t, 0.15, 0.7), 0.07, -3.6)
    words_in(canvas, d, "une question", M, 456, 96, "d5", CREAM, prog(t, 0.4, 0.7), 0.07, -3.6)
    words_in(canvas, d, "de vitesse.", M, 552, 96, "d5", CREAM, prog(t, 0.65, 0.7), 0.07, -3.6)
    amber_serif(d, canvas, "C'est une question", M, 700, 86, prog(t, 1.0, 0.6))
    amber_serif(d, canvas, "de répétitions.", M, 800, 92, prog(t, 1.15, 0.6))

    # compteur de répétitions : 4 barres qui se remplissent
    counts = [1, 3, 7, 14, 30]
    for i, n in enumerate(counts):
        p = prog(t, 2.3 + i * 0.42, 0.5)
        if p <= 0:
            continue
        e = eob(p)
        y = 1020 + i * 104
        d.line([(M, y - 18), (W - M, y - 18)], fill=c_(CREAM, 26 * e), width=1)
        tracked(d, (M, y), f"×{n}", F("d7", 40), c_(AMBER if i == 4 else CREAM, 246 * e), -1.6)
        bw = int((CW - 330) * (n / 30) * e)
        d.rounded_rectangle([M + 150, y + 8, M + 150 + max(6, bw), y + 40], 8,
                            fill=c_(AMBER if i == 4 else (66, 62, 56), 245 * e))
        tracked(d, (W - M - 92, y + 6), f"J+{n}", F("i6", 20),
                c_(CREAM if i == 4 else MUTED, 230 * e), 1.6)

    words_in(canvas, d, "Ce que tu répètes devient facile.", M, 1600, 42, "d5", CREAM,
             prog(t, 4.4, 0.8), 0.055, -1.4)
    words_in(canvas, d, "Ce que tu évites devient lourd.", M, 1660, 42, "d5", AMBER,
             prog(t, 4.85, 0.8), 0.055, -1.4)


def s_promesse(canvas, t, dur):
    d = ImageDraw.Draw(canvas)
    bg = kenburns("write_candle.jpg", t, dur, 1.18, 1.06, .5, .52, .5, .48, desat=.55, warm=1.10)
    canvas.paste(scrim(bg, .42, .84), (0, 0))

    tracked(d, (M, 250), "CE SOIR", F("i6", 18), c_(AMBER, 240), 3.6)
    words_in(canvas, d, "Choisis ton heure.", M, 360, 92, "d5", CREAM, prog(t, 0.15, 0.8), 0.07, -3.6)
    words_in(canvas, d, "Écris ce que tu feras.", M, 470, 72, "d4", CREAM, prog(t, 0.55, 0.8), 0.05, -2.2)
    words_in(canvas, d, "Et tiens ta promesse.", M, 570, 72, "d4", AMBER, prog(t, 0.9, 0.8), 0.05, -2.2)

    # checklist animée (chaque ligne se coche au rythme de la voix)
    items = [("Une heure fixe", 1.55), ("Trois tâches écrites", 2.35), ("Aucune excuse", 3.15)]
    for i, (txt, at) in enumerate(items):
        p = prog(t, at, 0.55)
        if p <= 0:
            continue
        e = eob(p)
        y = 790 + i * 132
        d.line([(M, y - 26), (M + CW * eio(p), y - 26)], fill=c_(CREAM, 34), width=1)
        box = 46
        d.rounded_rectangle([M, y + 4, M + box, y + 4 + box], 12,
                            outline=c_(AMBER if i == 2 else CREAM, 180 * e), width=2)
        if i <= 1 or prog(t, at + 0.3, 0.3) > 0:
            ck = eob(prog(t, at + 0.25, 0.35))
            if ck > 0:
                d.line([(M + 12, y + 28), (M + 20, y + 36), (M + 34, y + 16)],
                       fill=c_(AMBER, 255 * ck), width=4)
        tracked(d, (M + 76, y + 6), txt, F("d5", 42), c_(CREAM, 245 * e), -1.4)
        tracked(d, (W - M - 60, y + 14), "✓" if i <= 1 else "→", F("i6", 26),
                c_(AMBER, 220 * e), 0)

    # bloc citation / engagement
    p = prog(t, 4.35, 0.8)
    if p > 0:
        y = 1240
        d.rounded_rectangle([M, y, W - M, y + 250], 24, fill=(12, 12, 14, 235),
                            outline=(255, 122, 46, 120), width=1)
        d.rectangle([M, y, M + 6, y + 250], fill=c_(AMBER, 240 * eo(p)))
        tracked(d, (M + 38, y + 34), "LA SEULE PROMESSE QUI COMPTE", F("i6", 16), c_(AMBER, 238 * p), 2.6)
        para(d, "Celle que tu te fais à toi-même,\nquand personne ne te regarde.",
             F("seri", 42), c_(CREAM, 240 * p), M + 38, y + 78, CW - 90, 1.3)

    words_in(canvas, d, "Recommence demain. Même heure.", M, 1600, 40, "d5", CREAM,
             prog(t, 6.0, 0.9), 0.06, -1.4)


def s_outro(canvas, t, dur):
    d = ImageDraw.Draw(canvas)
    # dernière image : la route au brouillard, très assombrie, en zoom lent
    bg = kenburns("road_fog.jpg", t, dur, 1.10, 1.02, .5, .5, .55, .35, desat=.22, warm=1.04)
    bg = Image.blend(bg, Image.new("RGB", (W, H), INK), 0.78)
    canvas.paste(bg, (0, 0))
    hal = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(hal).ellipse([-260, 420, W + 260, 1500], fill=(255, 122, 46, 34))
    canvas.alpha_composite(hal.filter(ImageFilter.GaussianBlur(160)))

    # petit lockup
    p = prog(t, 0.1, 0.6)
    tracked(d, (M, 700), "DISCIPLINE", F("i6", 20), c_(MUTED, 225 * eo(p)), 6.0)

    e = eob(prog(t, 0.3, 0.9))
    words_in(canvas, d, "La discipline", M, 770, 128, "d5", CREAM, prog(t, 0.35, 0.9), 0.08, -5)
    amber_serif(d, canvas, "bat la motivation.", M + 4, 930, 116, prog(t, 0.85, 0.8))

    p2 = prog(t, 1.6, 0.9)
    if p2 > 0:
        hairline(d, 1150, p2, alpha=50)
        words_in(canvas, d, "Choisis ton heure.", M, 1206, 46, "d4", CREAM, p2, 0.06, -1.2)
        words_in(canvas, d, "Tiens-la trente jours.", M, 1268, 46, "d4", AMBER,
                 prog(t, 2.05, 0.9), 0.06, -1.2)

    p3 = prog(t, 2.8, 0.9)
    if p3 > 0:
        chip(canvas, "IMAGES & GIF DU WEB · MOTION DESIGN · VOIX OFF", M, 1620, p3, size=16,
             dot=AMBER)


SCENE_FN = {"hook": s_hook, "decision": s_decision, "regles": s_regles,
            "avance": s_avance, "reps": s_reps, "promesse": s_promesse,
            "outro": s_outro}

# ---------------------------------------------------------------- chrome
def chrome(canvas, t, idx, name):
    d = ImageDraw.Draw(canvas)
    if name != "outro":
        tracked(d, (M, 74), "DISCIPLINE", F("d7", 22), c_(CREAM, 225), 4.0)
        tracked(d, (W - M - 54, 78), f"{idx + 1:02d}", F("i6", 16), c_(MUTED, 190), 1.0)
        d.line([(M, 128), (W - M, 128)], fill=c_(CREAM, 22), width=1)
    # barre de progression + chapitrage
    py = 1866
    d.line([(M, py), (W - M, py)], fill=c_(CREAM, 28), width=2)
    fw = (W - 2 * M) * clamp01(t / TOTAL)
    if fw > 2:
        d.line([(M, py), (M + fw, py)], fill=c_(AMBER, 255), width=2)
    for i in range(1, 7):
        x = M + (W - 2 * M) * i / 7
        d.line([(x, py - 5), (x, py + 5)], fill=c_(CREAM, 80), width=1)


def render_frame(fi):
    t = fi / FPS
    i = max(0, min(len(CUTS) - 2, int(np.searchsorted(CUTS, t, side="right") - 1)))
    name = SCENES[i]
    lt, dur = t - CUTS[i], CUTS[i + 1] - CUTS[i]

    frame = Image.new("RGBA", (W, H), (9, 9, 10, 255))
    SCENE_FN[name](frame, lt, dur)
    whip(frame, lt)
    flash(frame, lt)
    chrome(frame, t, i, name)
    out = add_grain(frame.convert("RGB"), t, amount=3.4, scale=2)
    out = vignette(out, 0.42)
    # respiration de contraste entre les plans
    return out


# ---------------------------------------------------------------- audio
def _ffmpeg():
    from imageio_ffmpeg import get_ffmpeg_exe
    return get_ffmpeg_exe()


def decode(path):
    from scipy.signal import butter, sosfilt
    p = subprocess.run([_ffmpeg(), "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1",
                        "-f", "f32le", "-"], stdout=subprocess.PIPE, check=True)
    a = np.frombuffer(p.stdout, dtype=np.float32).copy()
    a = sosfilt(butter(2, 80 / (SR / 2), btype="high", output="sos"), a)
    a = a + 0.35 * sosfilt(butter(2, [2000 / (SR / 2), 5200 / (SR / 2)], btype="band",
                                  output="sos"), a)
    idx = np.where(np.abs(a) > 10 ** (-48 / 20))[0]
    if idx.size:
        a = a[max(0, idx[0] - int(.04 * SR)): idx[-1] + int(.05 * SR)]
    return a


def build_audio(out_path):
    from scipy.signal import butter, sosfilt
    n = int(TOTAL * SR)
    voice = np.zeros(n, np.float32)
    prev_end = 0.0
    for name, at in VO:
        a = decode(os.path.join(AUDIO, name))
        dur = len(a) / SR
        if at < prev_end + 0.15:
            raise SystemExit(f"{name} chevauche la prise précédente ({prev_end:.2f}s)")
        a = a / max(float(np.abs(a).max()), 1e-6) * 0.72
        s = int(round(at * SR))
        voice[s:s + len(a)] += a
        print(f"  {name}: {dur:5.2f}s  [{at:5.2f} → {at + dur:5.2f}]", flush=True)
        prev_end = at + dur

    # ---- lit musical : 92 BPM, nappe grave + pulsation + verre
    beat = 60 / 92
    mus = np.zeros(n, np.float32)
    roots = [49.0, 55.0, 43.65, 58.27]
    k = 0
    while k * beat < TOTAL:
        s = int(k * beat * SR)
        ln = min(n - s, int(0.55 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[(k // 8) % 4]
            env = np.minimum(tt / 0.05, 1) * np.exp(-tt * 3.2)
            v = (np.sin(2 * np.pi * r * tt) * 0.55 + np.sin(2 * np.pi * r * 2 * tt) * 0.22 +
                 np.sin(2 * np.pi * r * 3 * tt) * 0.08)
            mus[s:s + ln] += (v * env * 0.24).astype(np.float32)
        k += 1
    # pulsation sourde (2 temps)
    k = 0
    while k * beat / 2 < TOTAL:
        s = int(k * beat / 2 * SR)
        ln = min(n - s, int(0.18 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            env = np.exp(-tt * 22)
            mus[s:s + ln] += (np.sin(2 * np.pi * (70 * np.exp(-tt * 8) + 38) * tt) *
                              env * (0.30 if k % 4 == 0 else 0.10)).astype(np.float32)
        k += 1
    # shimmer haut (tension)
    k = 0
    while k * beat * 2 < TOTAL:
        s = int(k * beat * 2 * SR)
        ln = min(n - s, int(1.4 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[(k // 2) % 4] * 4
            v = np.sin(2 * np.pi * r * tt) + 0.4 * np.sin(2 * np.pi * r * 1.5 * tt + .4)
            env = np.minimum(tt / .4, 1) * np.exp(-np.maximum(tt - .5, 0) * 2.4)
            sos = butter(2, 5200 / (SR / 2), btype="low", output="sos")
            mus[s:s + ln] += (sosfilt(sos, (v * env).astype(np.float32)) * 0.055).astype(np.float32)
        k += 1
    # bruit filtré (souffle) très bas
    mus += (_noise(n, 200, 1800, 3) * 0.012).astype(np.float32)

    mus /= max(float(np.abs(mus).max()), 1e-6)
    mus *= 0.30
    env = np.abs(voice).astype(np.float32)
    env = sosfilt(butter(1, 2.2 / (SR / 2), btype="low", output="sos"), env)
    env /= max(float(env.max()), 1e-6)
    mus *= 1.0 - 0.78 * np.clip(env * 2.4, 0, 1)

    # ---- SFX : whoosh sur chaque coupe, ticks sur les cases / coches
    sfx = np.zeros(n, np.float32)
    for c_ in CUTS[1:-1]:
        s = int(c_ * SR)
        ln = min(n - s, int(0.5 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            sweep = np.exp(-tt * 7)
            sfx[s:s + ln] += (_noise(ln, 400, 7000, int(c_ * 13)) * sweep * 0.16).astype(np.float32)
            sfx[s:s + ln] += (np.sin(2 * np.pi * (60 + 220 * np.exp(-tt * 12)) * tt) *
                              np.exp(-tt * 8) * 0.20).astype(np.float32)
    for at in (3.35, 3.57, 3.79, 18.9 + 2.35, 18.9 + 3.45, 44.3 + 1.55, 44.3 + 2.35,
               44.3 + 3.15):
        s = int(at * SR)
        ln = min(n - s, int(0.12 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            sfx[s:s + ln] += (np.sin(2 * np.pi * 1480 * tt) * np.exp(-tt * 55) * 0.10).astype(np.float32)

    mix = voice + mus + sfx
    peak = float(np.abs(mix).max())
    if peak > 0.97:
        mix *= 0.97 / peak
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    print("  mix ->", out_path, flush=True)


def _noise(n, lo, hi, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n).astype(np.float32)
    f = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    f[(freqs < lo) | (freqs > hi)] = 0
    y = np.fft.irfft(f).astype(np.float32)
    return y / max(float(np.abs(y).max()), 1e-6)


def _measure(path):
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-i", path, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], stderr=subprocess.PIPE, text=True)
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)[-1])
    return i, tp


def render():
    ff = _ffmpeg()
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                             "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                             "-x264-params", "aq-mode=3:psy-rd=0.6,0.0",
                             "-pix_fmt", "yuv420p", "-movflags", "+faststart", TMP],
                            stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(render_frame(fi).tobytes())
        if fi % 150 == 0:
            print(f"  {fi}/{NFR} ({fi / NFR * 100:.0f}%)", flush=True)
    proc.stdin.close()
    proc.wait()

    base = _measure(MIX)[0]
    gain = -14.0 - base
    for _ in range(4):
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP, "-i", MIX,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89:level=disabled,"
                               "aresample=48000",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                        "-shortest", "-movflags", "+faststart", OUT], check=True)
        i, tp = _measure(OUT)
        print(f"  audio: {i} LUFS / {tp} dBTP", flush=True)
        if abs(i + 14.0) <= 0.3:
            break
        gain += (-14.0 - i)
    print("Rendered", OUT, f"({os.path.getsize(OUT) / 1e6:.1f} MB)")


def preview(out_path):
    cols, rows = 4, 2
    tw, th = 300, 533
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (12, 12, 14))
    d = ImageDraw.Draw(sheet)
    for k, name in enumerate(SCENES):
        mid = (CUTS[k] + CUTS[k + 1]) / 2
        im = render_frame(int(mid * FPS)).resize((tw, th), Image.LANCZOS)
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 170, y + 24], fill=(0, 0, 0))
        d.text((x + 5, y + 4), f"{CUTS[k]:05.2f}s {name}", font=F("i6", 15), fill=(255, 255, 255))
    sheet.save(out_path, quality=90)
    print("Saved preview:", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default=None)
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--frames", default=None, help="ex: 0,120,300 → PNG dans /tmp")
    a = ap.parse_args()
    if a.frames:
        for fi in [int(x) for x in a.frames.split(",")]:
            render_frame(fi).save(f"/tmp/disc_{fi:05d}.jpg", quality=92)
        return
    if a.preview:
        preview(a.preview)
        return
    os.makedirs(FILM, exist_ok=True)
    print("Voix off + musique ...")
    build_audio(MIX)
    if a.audio_only:
        return
    render()


if __name__ == "__main__":
    main()
