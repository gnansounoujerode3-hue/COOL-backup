#!/usr/bin/env python3
"""Léger Akodjenou — Funnel Builder · film vertical SANS VOIX OFF (33,3 s).

Identité visuelle reprise **du portfolio réel** (tokens extraits du site
https://legerakodjenou6.systeme.io/47e3d8ba) :

    ink #0a0a0b · coal #101012 · panel #151517 · cream #f4f1ea
    muted #97938a · ember #ff4d00 · ember-soft #ff7a3d
    line rgba(244,241,234,.09)
    display Space Grotesk · serif Instrument Serif · texte Inter
    fond #0a0a0b + halo ember 8 % en haut à droite + dot-grid 34 px + grain
    easing cubic-bezier(.22,1,.36,1)

Rythme : 108 BPM, coupes sur les mesures, 8 plans, 33,33 s.
Audio : score original + impacts/SFX uniquement — aucune voix.

    python3 build_leger_film_v2.py --preview /tmp/preview.jpg
    python3 build_leger_film_v2.py
"""
import argparse
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy.signal import butter, sosfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film_lib import clamp01, eo, eob, ei, eio, prog  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
FILM_DIR = os.path.join(PROJECT, "film")
AUDIO_DIR = os.path.join(PROJECT, "assets", "audio")
os.makedirs(FILM_DIR, exist_ok=True)

OUT = os.path.join(FILM_DIR, "leger-akodjenou-funnel-builder-v2-motion-9x16.mp4")
MIX = os.path.join(AUDIO_DIR, "master_mix_v2.wav")
TMP_VIDEO = "/tmp/leger_v2_video.mp4"

# ------------------------------------------------------------------ tokens
INK = (10, 10, 11)
COAL = (16, 16, 18)
PANEL = (21, 21, 23)
CREAM = (244, 241, 234)
MUTED = (151, 147, 138)
EMBER = (255, 77, 0)
EMBER_SOFT = (255, 122, 61)
LINE = (244, 241, 234, 23)          # rgba(...,.09) sur ink
DIM = (86, 83, 78)

FB = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
FONTS = {
    "d5": f"{FB}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
    "d4": f"{FB}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
    "d6": f"{FB}/space-grotesk/600SemiBold/SpaceGrotesk_600SemiBold.ttf",
    "d7": f"{FB}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "ser": f"{FB}/instrument-serif/400Regular/InstrumentSerif_400Regular.ttf",
    "seri": f"{FB}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
    "i4": f"{FB}/inter/400Regular/Inter_400Regular.ttf",
    "i5": f"{FB}/inter/500Medium/Inter_500Medium.ttf",
    "i6": f"{FB}/inter/600SemiBold/Inter_600SemiBold.ttf",
}

BAR = 60.0 / 108 * 4          # 2,2222 s
CUTS = [round(BAR * k, 4) for k in (0, 2, 4, 6, 7, 8, 10, 12, 15)]
SCENES = ["hook", "problem", "noirson", "ascension", "horizon", "method", "proof", "cta"]
TOTAL = CUTS[-1]                  # 33,333 s
# numérotation identique aux sections du portfolio
CHAPTER = {
    "hook": "—",
    "problem": "(01) Qui suis-je",
    "noirson": "(02) Réalisations",
    "ascension": "(02) Réalisations",
    "horizon": "(02) Réalisations",
    "method": "(03) Processus",
    "proof": "(05) Ils ont converti",
    "cta": "(07) Parlons de votre projet",
}
INDEX = {n: c.split(" ")[0] for n, c in CHAPTER.items()}

M = 72
CW = W - M * 2

_F = {}


def F(kind, size):
    size = max(8, int(round(size)))
    key = (kind, size)
    if key not in _F:
        try:
            _F[key] = ImageFont.truetype(FONTS[kind], size)
        except Exception:
            _F[key] = ImageFont.load_default()
    return _F[key]


def tl(d, text, f, tracking=0.0):
    if not text:
        return 0.0
    return sum(d.textlength(c, font=f) + tracking for c in text) - tracking


def fit_size(kind, text, size, maxw, tracking):
    """Reduce the point size until the tracked text fits `maxw`."""
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while size > 12:
        if tl(tmp, text, F(kind, size), tracking) <= maxw:
            break
        size -= 2
    return size


def tracked(d, xy, text, f, fill, tracking=0.0, center=None):
    x, y = xy if center is None else (xy[0] - tl(d, text, f, tracking) / 2, xy[1])
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + tracking


def para(d, text, f, fill, x, y, maxw, lh=1.4, center=False, tracking=0.0):
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
    step = int(f.size * lh)
    for i, ln in enumerate(lines):
        if center:
            tracked(d, (x + maxw / 2, y + i * step), ln, f, fill, tracking, center=x + maxw / 2)
        else:
            tracked(d, (x, y + i * step), ln, f, fill, tracking)
    return len(lines) * step


def c_(c, a=255):
    return (c[0], c[1], c[2], int(max(0, min(255, a))))


def ac(canvas, im, xy=(0, 0)):
    canvas.alpha_composite(im, (int(xy[0]), int(xy[1])))


# ------------------------------------------------------------- text layers
def text_layer(lines, specs, w=W, h=400, tracking=-2.0, pad=40):
    """Render one or more tracked lines onto a transparent layer (for masks)."""
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    y = pad
    for text, kind, size, extra in zip(lines, specs, [s[0] for s in specs], specs):
        f = F(kind, size)
        tracked(d, (pad, y), text, f, 255, tracking)
        y += int(size * 1.06) + extra[1]
    return layer


def outline_from_mask(mask, color=CREAM, alpha=82, width=2):
    """-webkit-text-stroke equivalent: ring = mask - eroded(mask)."""
    k = width * 2 + 1
    inner = mask.filter(ImageFilter.MinFilter(k))
    ring = ImageChops.subtract(mask, inner)
    out = Image.new("RGBA", mask.size, c_(color, 0))
    solid = Image.new("RGBA", mask.size, c_(color, alpha))
    out.paste(solid, (0, 0), ring)
    return out


def panel(w, h, r=22, fill=PANEL, border=LINE):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=c_(fill, 255), outline=border, width=1)
    return im


_SH = {}


def shadow(w, h, r, blur, alpha):
    key = (w, h, r, blur, alpha)
    if key not in _SH:
        pad = blur * 2
        im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + w - 1, pad + h - 1], r,
                                             fill=(0, 0, 0, alpha))
        _SH[key] = im.filter(ImageFilter.GaussianBlur(blur))
    return _SH[key]


def place(canvas, im, x, y, blur=30, alpha=170, r=22, dy=18):
    sh = shadow(int(im.width), int(im.height), r, blur, alpha)
    ac(canvas, sh, (x - blur * 2, y - blur * 2 + dy))
    ac(canvas, im, (x, y))


def chip(text, size=20, fg=CREAM, border=LINE, bg=(21, 21, 23, 255), pad_x=22, pad_y=13, dot=None):
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = F("i5", size)
    tw = tl(tmp, text, f, 0.4)
    h = int(size * 1.5) + pad_y * 2
    w = int(tw + pad_x * 2 + (size if dot else 0))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=bg, outline=border, width=1)
    x = pad_x
    if dot:
        cy = h // 2
        d.ellipse([x, cy - size * 0.2, x + size * 0.4, cy + size * 0.2], fill=c_(dot, 255))
        x += int(size)
    d.text((x, (h - size * 1.28) / 2), text, font=f, fill=fg)
    return im


def button(text, w=None, h=104, size=32):
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = F("d6", size)
    tw = tl(tmp, text, f, 0.2)
    w = w or int(tw + 116)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=c_(EMBER, 255))
    d.text(((w - tw) / 2 - 18, (h - size * 1.3) / 2), text, font=f, fill=c_(INK, 255))
    ax = w - 62
    ay = h / 2
    d.line([(ax, ay), (ax + 24, ay)], fill=c_(INK, 255), width=3)
    d.polygon([(ax + 30, ay), (ax + 20, ay - 7), (ax + 20, ay + 7)], fill=c_(INK, 255))
    return im


# ------------------------------------------------------------------ stage
def dot_grid(d, spacing=34, color=(244, 241, 234, 18)):
    for y in range(0, H + spacing, spacing):
        for x in range(0, W + spacing, spacing):
            d.point((x, y), fill=color)


def build_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.full((H, W, 3), INK, np.float32)
    # halo ember : radial-gradient(1200px 800px at 85% -10%, rgba(255,77,0,.08))
    cx, cy = W * 0.85, H * -0.10
    d2 = ((xx - cx) ** 2 / (1200 ** 2)) + ((yy - cy) ** 2 / (800 ** 2))
    glow = np.exp(-d2 * 1.9) * 0.085
    img += glow[..., None] * np.array(EMBER, np.float32)
    # léger halo froid en bas pour la profondeur
    d3 = ((xx - W * 0.1) ** 2 + (yy - H * 0.95) ** 2) / (900 ** 2)
    img += (np.exp(-d3 * 2.2) * 0.05)[..., None] * np.array((90, 96, 120), np.float32)
    # vignette
    vx = (xx - W / 2) / (W * 0.78)
    vy = (yy - H / 2) / (H * 0.78)
    img *= np.clip(1.0 - 0.30 * (vx * vx + vy * vy), 0.45, 1.0)[..., None]
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dot_grid(ImageDraw.Draw(grid))
    base.alpha_composite(grid)

    # grain (opacity .055, animé dans le temps sur une texture désactivée ici)
    rng = np.random.default_rng(3)
    n = rng.normal(0, 7.0, (H, W, 1)).astype(np.float32)
    g = np.repeat(n, 3, axis=2)
    ga = np.full((H, W, 4), 0, np.uint8)
    ga[..., :3] = np.clip(128 + g, 0, 255).astype(np.uint8)
    ga[..., 3] = 16
    grain = Image.fromarray(ga)
    base.alpha_composite(grain)
    return base


def grain_shift(canvas, t):
    """Animated film grain (≈ .055), 10 steps like the site's keyframes."""
    rng = np.random.default_rng(int(t * 10) + 11)
    small = rng.normal(0, 26, (H // 3, W // 3, 1)).astype(np.float32)
    a = np.full((H // 3, W // 3, 4), 0, np.uint8)
    a[..., :3] = np.clip(128 + np.repeat(small, 3, 2), 0, 255).astype(np.uint8)
    a[..., 3] = 13
    im = Image.fromarray(a).resize((W, H), Image.BILINEAR)
    canvas.alpha_composite(im)


def marquee_strip(canvas, text, y, speed_t, size=26, color=MUTED, kind="i5", alpha=210, gap=54,
                  sep="·", clip=(M, CW)):
    f = F(kind, size)
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    unit = tl(tmp, text, f, 3.0) + gap
    x0 = clip[0] - ((speed_t * 46) % unit)
    strip = Image.new("RGBA", (clip[1], int(size * 2)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(strip)
    x = x0
    while x < clip[1] + unit:
        tracked(sd, (x, size * 0.18), text, f, c_(color, alpha), 3.0)
        sd.text((x + tl(sd, text, f, 3.0) + gap * 0.35, size * 0.16), sep,
                font=F("d4", int(size * 1.1)), fill=c_(EMBER, alpha))
        x += unit
    mask = Image.new("L", strip.size, 0)
    ImageDraw.Draw(mask).rectangle([0, 0, clip[1], strip.height], fill=255)
    canvas.alpha_composite(Image.composite(strip, Image.new("RGBA", strip.size, (0, 0, 0, 0)), mask),
                           (clip[0], y))


def hairline(d, y, a=1.0, x0=M, x1=W - M):
    d.line([(x0, y), (x1, y)], fill=c_(CREAM, 23 * a), width=1)


def label(d, text, y, a=1.0, color=MUTED, x=M, size=18):
    tracked(d, (x, y), text.upper(), F("i6", size), c_(color, 235 * a), 3.4)


def big_number(d, text, x, y, size, color=CREAM, a=1.0, tracking=-4.0):
    tracked(d, (x, y), text, F("d7", size), c_(color, 255 * a), tracking)


# ------------------------------------------------------------------ mockup
def browser(w, h, url, body, r=18, dark=True):
    f = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(f)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r,
                        fill=c_(COAL, 255), outline=(244, 241, 234, 26), width=1)
    bar = 42
    d.rounded_rectangle([0, 0, w - 1, bar + r], r, fill=(26, 26, 29, 255))
    d.rectangle([0, bar - r, w - 1, bar], fill=(26, 26, 29, 255))
    d.line([(0, bar), (w - 1, bar)], fill=(244, 241, 234, 22), width=1)
    for i, cc in enumerate([(255, 77, 0), (86, 83, 78), (86, 83, 78)]):
        d.ellipse([16 + i * 18, bar / 2 - 4, 24 + i * 18, bar / 2 + 4], fill=c_(cc, 200))
    d.rounded_rectangle([86, 10, w - 16, 32], 11, fill=(255, 255, 255, 10))
    d.text((98, 12), url, font=F("i4", 13), fill=c_(MUTED, 225))

    body = ImageOps.fit(body, (w, h - bar), Image.LANCZOS)
    mask = Image.new("L", (w, h - bar), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - bar - 1], r, fill=255)
    f.paste(body, (0, bar), mask)
    return f


def noirson_page(w, h):
    im = Image.new("RGBA", (w, h), (12, 12, 13, 255))
    d = ImageDraw.Draw(im)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([w * 0.35, -h * 0.3, w * 1.2, h * 0.8], fill=(255, 77, 0, 44))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))

    tracked(d, (30, 24), "NOIR·SON", F("d7", 19), c_(CREAM, 250), 3.2)
    x = w * 0.42
    for n in ["Casques", "Écouteurs", "Histoire"]:
        d.text((x, 28), n, font=F("i4", 12), fill=c_(MUTED, 220))
        x += d.textlength(n, font=F("i4", 12)) + 20
    d.text((w - 108, 28), "Panier (1)", font=F("i4", 12), fill=c_(CREAM, 230))
    d.line([(30, 62), (w - 30, 62)], fill=(244, 241, 234, 20), width=1)

    # casque
    cx, cy = w * 0.76, h * 0.50
    bw, bh = 178, 214
    halo = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([50, 60, 250, 260], fill=(255, 77, 0, 40))
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(30)), (int(cx - 150), int(cy - 130)))
    d.arc([cx - bw / 2, cy - bh * 0.66, cx + bw / 2, cy + bh * 0.26], 188, 352,
          fill=(214, 210, 200, 255), width=26)
    d.arc([cx - bw / 2 + 4, cy - bh * 0.66 + 6, cx + bw / 2 - 4, cy + bh * 0.26 - 6], 188, 352,
          fill=(150, 146, 138, 255), width=6)
    for sx in (-1, 1):
        ex = cx + sx * (bw / 2 - 6)
        d.rounded_rectangle([ex - 28, cy - 24, ex + 28, cy + 96], 26, fill=(22, 22, 25, 255),
                            outline=(200, 196, 186, 255), width=3)
        d.rounded_rectangle([ex - 19, cy - 12, ex + 19, cy + 84], 19, fill=(14, 14, 16, 255),
                            outline=(110, 106, 100, 220), width=2)
        d.ellipse([ex - 10, cy + 26, ex + 10, cy + 46], fill=(70, 67, 62, 255))

    tracked(d, (30, 88), "NOUVEAU", F("i6", 11), c_(EMBER, 245), 2.8)
    tracked(d, (30, 108), "Le silence,", F("d5", 34), c_(CREAM, 255), -0.8)
    tracked(d, (30, 148), "enfin.", F("d5", 34), c_(CREAM, 255), -0.8)
    para(d, "Casque à réduction de bruit\n40 h d'autonomie", F("i4", 12),
         c_(MUTED, 235), 30, 196, w * 0.42, lh=1.5)
    tracked(d, (30, 250), "249 €", F("d7", 26), c_(CREAM, 255), -0.6)
    d.rounded_rectangle([30, 290, 208, 328], 19, fill=c_(EMBER, 255))
    tracked(d, (48, 302), "AJOUTER AU PANIER", F("i6", 10), c_(INK, 255), 0.6)

    by = h - 78
    d.rounded_rectangle([30, by, w - 30, by + 50], 10, fill=(255, 255, 255, 8),
                        outline=(244, 241, 234, 24), width=1)
    d.rounded_rectangle([42, by + 16, 56, by + 30], 4, fill=c_(EMBER, 255))
    d.text((70, by + 11), "Étui de transport", font=F("i5", 11), fill=c_(CREAM, 235))
    d.text((70, by + 28), "Order bump automatique", font=F("i4", 10), fill=c_(MUTED, 215))
    d.text((w - 92, by + 17), "+ 19 €", font=F("i6", 13), fill=c_(EMBER, 245))
    return im


# ------------------------------------------------------------------ scenes
def s_hook(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.45))
    # badge
    ba = eob(prog(lt, 0.10, 0.5))
    if ba > 0:
        p = chip("Disponible pour nouveaux projets", size=19, fg=c_(CREAM, 240),
                 bg=(21, 21, 23, 235), pad_x=20, pad_y=12, dot=EMBER)
        ac(canvas, _alpha(p, ba), (M, 300 + (1 - ba) * 14))

    # H1 en trois lignes, masques de lignes (110 % → 0)
    lines = [("Des tunnels", CREAM, False),
             ("qui convertissent", CREAM, True),
             ("à +20 %", EMBER, False)]
    y = 430
    for i, (text, color, outline) in enumerate(lines):
        size = fit_size("d5", text, 126, CW, -5.5)
        if i == 2:
            size = fit_size("d5", text, 138, CW, -5.5)
        reveal = eob(prog(lt, 0.22 + i * 0.13, 0.62))
        rise = (1 - reveal) * size * 1.16
        layer = Image.new("L", (W, int(size * 1.6)), 0)
        ld = ImageDraw.Draw(layer)
        tracked(ld, (0, 12), text, F("d5", size), 255, -5.5)
        if outline:
            col_layer = outline_from_mask(layer, CREAM, 84, 2)
        else:
            col_layer = Image.new("RGBA", layer.size, c_(color, 255))
            col_layer.putalpha(layer)
        if rise > 0:
            mask = Image.new("L", layer.size, 0)
            ImageDraw.Draw(mask).rectangle([0, 0, W, layer.height - int(rise)], fill=255)
            keep = ImageChops.multiply(col_layer.getchannel("A"), mask)
            col_layer.putalpha(keep)
        ac(canvas, col_layer, (M, y + rise))
        y += int(size * 1.02)

    # filet + baseline
    la = eo(prog(lt, 0.95, 0.55))
    if la > 0:
        d.line([(M, 960), (M + CW * la, 960)], fill=c_(CREAM, 26), width=1)
        d.line([(M, 960), (M + 96 * la, 960)], fill=c_(EMBER, 240), width=2)
        tracked(d, (M, 982), "FUNNEL BUILDER — COTONOU, BÉNIN · MONDE ENTIER",
                F("i5", 17), c_(MUTED, 225 * la), 2.6)

    # sous-titre court (max 2 lignes)
    sa = eo(prog(lt, 1.30, 0.6))
    if sa > 0:
        para(d, "Des tunnels de vente qui transforment votre trafic en clients.",
             F("i4", 29), c_(CREAM, 232 * sa), M, 1050, 800, lh=1.5)

    # marquee du site
    if lt > 1.75:
        marquee_strip(canvas, "Scroll · Pour · Convertir", 1176, lt - 1.75,
                      size=22, alpha=165, gap=30, sep="")

    # stats hero du site
    stats = [("+20 %", "conversion visée"), ("5+", "types de tunnels"), ("24 h", "de réponse")]
    x = M
    for i, (v, lbl) in enumerate(stats):
        sa2 = eob(prog(lt, 1.75 + i * 0.12, 0.5))
        if sa2 <= 0:
            continue
        yy = 1470 + (1 - sa2) * 16
        tracked(d, (x, yy), v, F("d7", 40), c_(CREAM, 250 * sa2), -1.6)
        tracked(d, (x, yy + 52), lbl.upper(), F("i5", 14), c_(MUTED, 220 * sa2), 2.4)
        x += 320


def s_problem(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Le problème", 300, a)

    # citation en serif italique, 3 lignes
    q = ["« Une belle page", "qui ne vend pas,", "c'est de la décoration. »"]
    y = 372
    for i, line in enumerate(q):
        ra = eob(prog(lt, 0.16 + i * 0.11, 0.55))
        if ra <= 0:
            continue
        f = F("seri", 82)
        d.text((M, y + (1 - ra) * 34), line, font=f, fill=c_(CREAM, 250 * ra))
        y += 92

    # auteur du site
    aa = eo(prog(lt, 0.62, 0.5))
    tracked(d, (M, 690), "— LÉGER AKODJENOU", F("i6", 17), c_(EMBER, 235 * aa), 2.8)

    hairline(d, 760, eo(prog(lt, 0.75, 0.5)))

    # le diagnostic en trois points, style liste éditoriale
    rows = [("01", "Promesse absente", "Aucune raison de choisir."),
            ("02", "Zéro preuve", "Rien ne rassure avant l'achat."),
            ("03", "Zéro urgence", "Aucune raison d'agir maintenant.")]
    for i, (num, title, sub) in enumerate(rows):
        ra = eob(prog(lt, 0.85 + i * 0.14, 0.55))
        if ra <= 0:
            continue
        y = 812 + i * 132 + (1 - ra) * 18
        tracked(d, (M, y), num, F("i6", 17), c_(EMBER, 230 * ra), 1.6)
        tracked(d, (M + 74, y - 8), title, F("d5", 38), c_(CREAM, 250 * ra), -0.9)
        tracked(d, (M + 74, y + 40), sub, F("i4", 21), c_(MUTED, 225 * ra), 0)
        d.line([(M, y + 96), (W - M, y + 96)], fill=c_(CREAM, 18 * ra), width=1)

    # compteur cible
    ca = eob(prog(lt, 1.55, 0.7))
    if ca > 0:
        target = 20 * eob(prog(lt, 1.55, 1.0))
        yy = 1300
        hairline(d, yy, ca)
        tracked(d, (M, yy + 26), "TAUX DE CONVERSION VISÉ", F("i5", 17), c_(MUTED, 225 * ca), 3.0)
        tracked(d, (M, yy + 62), f"+{int(round(target))}", F("d7", 132), c_(EMBER, 255 * ca), -5.0)
        tracked(d, (M + 210, yy + 120), "%", F("d5", 52), c_(CREAM, 240 * ca), -2)

    # filet de clôture
    if lt > 1.7:
        hairline(d, 1560, eo(prog(lt, 1.7, 0.5)))


def s_noirson(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "01 / NOIR·SON — Page de vente", 300, a)

    ma = eob(prog(lt, 0.14, 0.62))
    if ma > 0:
        mw, mh = 880, 620
        mock = browser(mw, mh, "noirson.funnels.leger.studio", noirson_page(mw, mh - 42))
        place(canvas, _alpha(mock, ma), (W - mw) / 2, 356 + (1 - ma) * 30)

    ta = eo(prog(lt, 0.55, 0.55))
    if ta > 0:
        tracked(d, (M, 1030), "E-commerce · Audio", F("i4", 21), c_(MUTED, 225 * ta), 0.2)

    # +18 %
    ka = eob(prog(lt, 0.75, 0.62))
    if ka > 0:
        val = 18 * eob(prog(lt, 0.75, 0.9))
        tracked(d, (M, 1080), f"+{int(round(val))}", F("d7", 190), c_(EMBER, 255 * ka), -8)
        tracked(d, (M + 250, 1190), "%", F("d5", 62), c_(CREAM, 235 * ka), -2)
        tracked(d, (M + 6, 1292), "DE PANIER MOYEN", F("i6", 18), c_(MUTED, 225 * ka), 3.0)

    # tags du site
    for i, t_ in enumerate(["Page produit", "Order bump", "Upsell"]):
        ca = eob(prog(lt, 1.30 + i * 0.11, 0.45))
        if ca > 0:
            p = chip(t_, size=18, fg=c_(CREAM, 235), pad_x=18, pad_y=11)
            ac(canvas, _alpha(p, ca), (M + i * 176, 1360 + (1 - ca) * 12))

    # citation client
    qa = eo(prog(lt, 1.70, 0.6))
    if qa > 0:
        hairline(d, 1470, qa)
        para(d, "« L'order bump et l'upsell ont augmenté notre panier moyen de 18 %. »",
             F("seri", 40), c_(CREAM, 240 * qa), M, 1498, 900, lh=1.28)
        tracked(d, (M, 1620), "SANDRA M. · E-COMMERÇANTE, NOIR·SON", F("i6", 15),
                c_(MUTED, 215 * qa), 2.4)


def s_ascension(d, canvas, lt, dur):
    a = eo(prog(lt, 0.03, 0.34))
    label(d, "03 / ASCENSION — Tunnel complet", 300, a)

    ka = eob(prog(lt, 0.10, 0.55))
    if ka > 0:
        val = 412 * eob(prog(lt, 0.10, 0.9))
        tracked(d, (M, 372), f"{int(round(val))}", F("d7", 300), c_(CREAM, 255 * ka), -14)
        tracked(d, (M + 6, 712), "INSCRITS EN 14 JOURS", F("i6", 22), c_(EMBER, 245 * ka), 3.2)

    # mini-entonnoir
    steps = [("Page de capture", 1.00), ("Webinaire", 0.72), ("Séquence e-mail", 0.52),
             ("Page de vente", 0.34), ("Upsell", 0.22)]
    y0 = 830
    for i, (name, frac) in enumerate(steps):
        ra = eob(prog(lt, 0.42 + i * 0.09, 0.45))
        if ra <= 0:
            continue
        y = y0 + i * 92 + (1 - ra) * 14
        bw = (CW - 40) * frac * ra
        d.rounded_rectangle([M, y, M + max(8, bw), y + 60], 10, fill=c_(PANEL, 255),
                            outline=(244, 241, 234, 30), width=1)
        if i == 0:
            d.rounded_rectangle([M, y, M + max(8, bw), y + 60], 10, fill=c_(EMBER, 235))
        tracked(d, (M + 22, y + 17), name, F("i5", 21),
                c_(INK if i == 0 else CREAM, 240 * ra), 0.2)
        pct_txt = f"{int(frac * 100)} %"
        if i == 0:
            px = M + bw - tl(d, pct_txt, F("i6", 17)) - 22
            tracked(d, (px, y + 20), pct_txt, F("i6", 17), c_(INK, 240 * ra), 0.4)
        else:
            tracked(d, (M + max(8, bw) + 16, y + 20), pct_txt, F("i6", 17),
                    c_(MUTED, 220 * ra), 0.4)

    ta = eo(prog(lt, 1.30, 0.55))
    if ta > 0:
        tracked(d, (M, 1590), "7 E-MAILS AUTOMATISÉS · 1 SEUL TUNNEL", F("i5", 18),
                c_(MUTED, 220 * ta), 2.4)


def s_horizon(d, canvas, lt, dur):
    a = eo(prog(lt, 0.03, 0.34))
    label(d, "04 / HORIZON RETREAT — Réservation", 300, a)

    # deux grands chiffres séparés par un filet
    pairs = [("23", "%", "TAUX DE CONVERSION", 0.10),
             ("61", "%", "TAUX D'INSCRIPTION", 0.28)]
    for i, (num, sym, lbl, delay) in enumerate(pairs):
        ka = eob(prog(lt, delay, 0.6))
        if ka <= 0:
            continue
        val = int(round(int(num) * eob(prog(lt, delay, 0.85))))
        x = M + i * 470
        num_txt = f"{val:02d}"
        fnum = F("d7", 176)
        tracked(d, (x, 402), num_txt, fnum, c_(CREAM, 255 * ka), -8)
        tracked(d, (x + tl(d, num_txt, fnum, -8) + 10, 486), sym,
                F("d5", 58), c_(EMBER, 245 * ka), -2)
        tracked(d, (x + 4, 620), lbl, F("i6", 16), c_(MUTED, 220 * ka), 2.4)

    d.line([(W / 2, 372), (W / 2, 700)], fill=c_(LINE), width=1)

    # barres de preuve
    ta = eo(prog(lt, 0.55, 0.5))
    if ta > 0:
        hairline(d, 760, ta)
        tracked(d, (M, 786), "9 % → 23 % APRÈS REFONTE", F("i5", 19), c_(CREAM, 235 * ta), 1.2)
        # avant / après
        for i, (lbl, frac, colr) in enumerate([("AVANT", 0.09, DIM), ("APRÈS", 0.23, EMBER)]):
            ra = eob(prog(lt, 0.70 + i * 0.16, 0.6))
            if ra <= 0:
                continue
            y = 862 + i * 108
            tracked(d, (M, y - 26), lbl, F("i5", 14), c_(MUTED, 210 * ra), 2.4)
            d.rounded_rectangle([M, y + 24, W - M, y + 32], 4, fill=(244, 241, 234, 20))
            d.rounded_rectangle([M, y + 24, M + (CW) * frac * ra * 2.2, y + 32], 4,
                                fill=c_(colr, 245 * ra))

    # mockup retraite
    ma = eob(prog(lt, 1.05, 0.6))
    if ma > 0:
        mw, mh = 700, 300
        page = Image.new("RGBA", (mw, mh - 42), (18, 24, 22, 255))
        pd = ImageDraw.Draw(page)
        gg = Image.new("RGBA", page.size, (0, 0, 0, 0))
        ImageDraw.Draw(gg).ellipse([-80, 60, 520, 460], fill=(34, 122, 104, 70))
        page.alpha_composite(gg.filter(ImageFilter.GaussianBlur(46)))
        tracked(pd, (26, 22), "HORIZON RETREAT", F("d6", 14), c_(CREAM, 245), 3.0)
        pd.text((mw - 100, 24), "Réserver", font=F("i4", 11), fill=c_(CREAM, 210))
        pd.text((26, 96), "7 jours pour", font=F("ser", 30), fill=c_(CREAM, 250))
        pd.text((26, 132), "respirer.", font=F("seri", 30), fill=c_(CREAM, 250))
        pd.rounded_rectangle([26, mh - 100, 190, mh - 58], 21, fill=c_(EMBER, 250))
        tracked(pd, (44, mh - 88), "RÉSERVER", F("i6", 10), c_(INK, 255), 0.8)
        mock = browser(mw, mh, "horizonretreat.funnels.leger.studio", page)
        place(canvas, _alpha(mock, ma), (W - mw) / 2, 1150 + (1 - ma) * 24, blur=24, alpha=150)

    qa = eo(prog(lt, 1.35, 0.55))
    if qa > 0:
        tracked(d, (M, 1570), "« 9 % → 23 % de conversion après refonte. »", F("seri", 36),
                c_(CREAM, 240 * qa), 0)
        tracked(d, (M, 1630), "MARIAM S. · FONDATRICE", F("i6", 15), c_(MUTED, 210 * qa), 2.4)


def s_method(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Processus — 6 étapes", 300, a)
    ha = eob(prog(lt, 0.12, 0.55))
    if ha > 0:
        tracked(d, (M, 344), "Une méthode,", F("d5", 76), c_(CREAM, 250 * ha), -3.2)
        tracked(d, (M, 424), "zéro hasard.", F("d5", 76), c_(CREAM, 250 * ha), -3.2)

    steps = [("01", "Immersion & audit"), ("02", "Architecture du tunnel"),
             ("03", "Copywriting"), ("04", "Design & intégration"),
             ("05", "Automatisation"), ("06", "Tests & optimisation")]
    y0 = 580
    for i, (num, title) in enumerate(steps):
        ra = eob(prog(lt, 0.30 + i * 0.10, 0.5))
        if ra <= 0:
            continue
        y = y0 + i * 168 + (1 - ra) * 16
        d.line([(M, y - 18), (W - M, y - 18)], fill=c_(CREAM, 16 * ra), width=1)
        tracked(d, (M, y + 20), num, F("i6", 17), c_(EMBER, 230 * ra), 1.8)
        tracked(d, (M + 84, y + 4), title, F("d5", 46), c_(CREAM, 250 * ra), -1.4)
        # petit trait d'accent qui s'allonge
        d.line([(W - M - 90, y + 34), (W - M, y + 34)], fill=c_(EMBER, 120 * ra), width=2)
    d.line([(M, y0 + 6 * 168 - 18), (W - M, y0 + 6 * 168 - 18)], fill=c_(CREAM, 16), width=1)

    # délai de livraison (issu de la FAQ du site)
    fa = eob(prog(lt, 1.10, 0.55))
    if fa > 0:
        y = 1620 + (1 - fa) * 18
        tracked(d, (M, y), "DÉLAI DE LIVRAISON", F("i6", 14), c_(MUTED, 220 * fa), 2.8)
        tracked(d, (M, y + 30), "2 à 3 semaines", F("d5", 52), c_(CREAM, 250 * fa), -1.6)
        tracked(d, (M + 420, y + 46), "pour un tunnel complet", F("i4", 21),
                c_(MUTED, 225 * fa), 0.2)


def s_proof(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Services & outils", 300, a)

    ha = eob(prog(lt, 0.10, 0.55))
    if ha > 0:
        tracked(d, (M, 344), "Des tunnels", F("d5", 76), c_(CREAM, 250 * ha), -3.2)
        tracked(d, (M, 424), "en production.", F("d5", 76), c_(CREAM, 250 * ha), -3.2)

    # trois stats du site
    stats = [("5+", "types de tunnels", "de A à Z"),
             ("24 h", "de délai", "de réponse"),
             ("14 j", "de support", "après livraison")]
    for i, (v, l1, l2) in enumerate(stats):
        ra = eob(prog(lt, 0.34 + i * 0.12, 0.5))
        if ra <= 0:
            continue
        x = M + i * 320
        y = 560 + (1 - ra) * 16
        tracked(d, (x, y), v, F("d7", 72), c_(CREAM, 250 * ra), -3)
        tracked(d, (x, y + 90), l1, F("i5", 19), c_(MUTED, 225 * ra), 0.4)
        tracked(d, (x, y + 118), l2, F("i4", 17), c_(DIM, 220 * ra), 0.4)

    hairline(d, 760, eo(prog(lt, 0.62, 0.5)))

    # boîte à outils
    ta = eo(prog(lt, 0.70, 0.5))
    if ta > 0:
        tracked(d, (M, 790), "MA BOÎTE À OUTILS", F("i6", 16), c_(MUTED, 225 * ta), 3.2)
    tools = ["Systeme.io", "ClickFunnels", "GoHighLevel", "MailerLite",
             "Brevo", "Stripe", "Zapier", "Meta Ads"]
    x, y = M, 838
    for i, t_ in enumerate(tools):
        ca = eob(prog(lt, 0.78 + i * 0.06, 0.42))
        if ca <= 0:
            continue
        p = chip(t_, size=19, fg=c_(CREAM, 230), pad_x=20, pad_y=12)
        if x + p.width > W - M:
            x, y = M, y + 62
        ac(canvas, _alpha(p, ca), (x, y + (1 - ca) * 10))
        x += p.width + 10

    # filet de transition vers la citation
    if lt > 1.25:
        hairline(d, 1170, eo(prog(lt, 1.25, 0.5)))

    # citation + signature du portfolio
    qa = eo(prog(lt, 1.55, 0.6))
    if qa > 0:
        para(d, "« Léger ne dessine pas des pages,\nil construit des machines à vendre. »",
             F("seri", 44), c_(CREAM, 245 * qa), M, 1420, 900, lh=1.26)
        tracked(d, (M, 1548), "MARIAM S. · HORIZON RETREAT", F("i6", 15), c_(MUTED, 215 * qa), 2.4)

    na = eo(prog(lt, 1.95, 0.55))
    if na > 0:
        hairline(d, 1650, na)
        tracked(d, (M, 1682), "ILS ONT CONVERTI", F("i6", 14), c_(MUTED, 215 * na), 2.8)
        x = M
        for nm in ["Mariam S.", "David K.", "Sandra M."]:
            f = F("i5", 21)
            d.text((x, 1716), nm, font=f, fill=c_(CREAM, 230 * na))
            d.ellipse([x + d.textlength(nm, font=f) + 22, 1726,
                       x + d.textlength(nm, font=f) + 28, 1732], fill=c_(EMBER, 200 * na))
            x += d.textlength(nm, font=f) + 56


def s_cta(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Prêt à convertir ?", 292, a)

    lines = ["Votre tunnel mérite", "mieux qu'un template."]
    y = 360
    for i, line in enumerate(lines):
        ra = eob(prog(lt, 0.12 + i * 0.12, 0.6))
        if ra <= 0:
            continue
        d.text((M, y + (1 - ra) * 30), line, font=F("ser", 76), fill=c_(CREAM, 250 * ra))
        y += 88
    ua = eio(prog(lt, 0.55, 0.6))
    if ua > 0:
        d.rectangle([M, y + 8, M + 430 * ua, y + 12], fill=c_(EMBER, 240))

    # offre
    oa = eob(prog(lt, 0.62, 0.6))
    if oa > 0:
        card = panel(CW, 196, 20)
        cd = ImageDraw.Draw(card)
        cd.ellipse([30, 34, 44, 48], fill=c_(EMBER, 255))
        tracked(cd, (58, 30), "DISPONIBLE POUR NOUVEAUX PROJETS", F("i6", 15),
                c_(EMBER, 240), 2.4)
        tracked(cd, (30, 68), "Appel découverte · 30 min", F("d5", 44), c_(CREAM, 255), -1.4)
        tracked(cd, (30, 130), "Offert · sans engagement · réponse sous 24 h",
                F("i4", 21), c_(MUTED, 230), 0.2)
        ac(canvas, _alpha(card, oa), (M, 700 + (1 - oa) * 20))

    # bouton principal
    ba = eob(prog(lt, 1.02, 0.6))
    if ba > 0:
        btn = button("Démarrer un projet", w=CW, size=34)
        glow = btn.filter(ImageFilter.GaussianBlur(26))
        ac(canvas, _alpha(glow, 0.45 * ba), (M, 936))
        ac(canvas, _alpha(btn, ba), (M, 936 + (1 - ba) * 16))

    # contact
    rows = [("legerakodjenou6@gmail.com", "EMAIL"),
            ("+229 01 52 09 94 23", "WHATSAPP"),
            ("Cotonou, Bénin · monde entier", "BASÉ À")]
    for i, (val, lbl) in enumerate(rows):
        ra = eob(prog(lt, 1.30 + i * 0.11, 0.5))
        if ra <= 0:
            continue
        y = 1096 + i * 78 + (1 - ra) * 12
        tracked(d, (M, y), lbl, F("i6", 13), c_(DIM, 235 * ra), 2.6)
        tracked(d, (M + 132, y - 4), val, F("i5", 24), c_(CREAM, 240 * ra), 0.1)
        d.line([(M, y + 46), (W - M, y + 46)], fill=c_(CREAM, 14 * ra), width=1)

    # signature
    sa = eo(prog(lt, 1.80, 0.7))
    if sa > 0:
        tracked(d, (M, 1400), "LÉGER©", F("d7", 84), c_(CREAM, 250 * sa), -3)
        tracked(d, (M, 1500), "FUNNEL BUILDER — SYSTEME.IO", F("i5", 17), c_(MUTED, 220 * sa), 2.8)
        tracked(d, (M, 1536), "legerakodjenou6.systeme.io", F("i4", 19), c_(EMBER, 235 * sa), 0.2)

    # dernière ligne : promesse du site
    fa = eo(prog(lt, 2.45, 0.8))
    if fa > 0:
        hairline(d, 1620, fa)
        tracked(d, (W / 2, 1650), "Des tunnels qui convertissent.", F("d5", 38),
                c_(CREAM, 240 * fa), -1.0, center=W / 2)


def _alpha(im, a):
    if a >= 0.999:
        return im
    arr = np.array(im)
    arr[..., 3] = (arr[..., 3].astype(np.float32) * clamp01(a)).astype(np.uint8)
    return Image.fromarray(arr)


SCENE_FN = {"hook": s_hook, "problem": s_problem, "noirson": s_noirson,
            "ascension": s_ascension, "horizon": s_horizon, "method": s_method,
            "proof": s_proof, "cta": s_cta}


# ------------------------------------------------------------------ chrome
def chrome(canvas, t, name):
    d = ImageDraw.Draw(canvas)
    wa = eo(prog(t, 0.15, 0.6))
    if name != "cta":
        tracked(d, (M, 78), "LÉGER©", F("d7", 25), c_(CREAM, 240 * wa), -0.6)
    chap = CHAPTER[name].upper()
    tracked(d, (W - M - tl(d, chap, F("i5", 15), 2.2), 86), chap,
            F("i5", 15), c_(MUTED, 205 * wa), 2.2)
    d.line([(M, 126), (W - M, 126)], fill=c_(CREAM, 16 * wa), width=1)

    # barre de progression (ember)
    py = 1846
    d.line([(M, py), (W - M, py)], fill=c_(CREAM, 26), width=2)
    fw = (W - 2 * M) * clamp01(t / TOTAL)
    if fw > 2:
        d.line([(M, py), (M + fw, py)], fill=c_(EMBER, 255), width=2)


def flash(canvas, lt):
    if 0 <= lt < 0.20:
        p = lt / 0.20
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        x = -300 + p * (W + 600)
        ImageDraw.Draw(layer).polygon([(x, 0), (x + 150, 0), (x - 130, H), (x - 280, H)],
                                      fill=c_(EMBER, int(16 * (1 - p))))
        canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(46)))


_BG = None


def render_frame(fi):
    global _BG
    if _BG is None:
        _BG = build_bg()
    t = fi / FPS
    i = max(0, min(len(CUTS) - 2, np.searchsorted(CUTS, t, side="right") - 1))
    name = SCENES[i]
    lt = t - CUTS[i]

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    SCENE_FN[name](d, layer, lt, CUTS[i + 1] - CUTS[i])
    layer = _alpha(layer, eo(prog(lt, 0.0, 0.16)) * (1 - 0.42 * eo(prog(lt, (CUTS[i + 1] - CUTS[i]) - 0.10, 0.10))))

    frame = _BG.copy()
    ac(frame, layer)
    grain_shift(frame, t)
    chrome(frame, t, name)
    flash(frame, lt)
    return frame.convert("RGB")


# ------------------------------------------------------------------ audio
def _env(x, a=0.005, r=0.06):
    n = len(x)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e = np.ones(n, np.float32)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return x * e


def _noise(n, lo, hi, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n).astype(np.float32)
    sos = butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], btype="band", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def build_score(total, out_path):
    n = int(total * SR)
    beat = 60.0 / 108
    bar = beat * 4
    mixm = np.zeros(n, np.float32)

    # --- kick
    t0 = 0.0
    while t0 < total:
        s = int(t0 * SR)
        ln = min(n - s, int(0.3 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 96 * np.exp(-tt * 15) + 42
            k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 12)
            mixm[s:s + ln] += (k * 0.42).astype(np.float32)
        t0 += beat

    # --- clap / snare sur 2 & 4
    for b in range(int(total / beat) + 1):
        if b % 4 in (1, 3):
            s = int(b * beat * SR)
            ln = min(n - s, int(0.18 * SR))
            if ln > 0:
                c = _noise(ln, 1200, 5200, seed=b) * np.exp(-np.arange(ln) / SR * 26)
                mixm[s:s + ln] += (c * 0.16).astype(np.float32)

    # --- hats 1/8
    b = 0
    while b * beat / 2 < total:
        s = int(b * beat / 2 * SR)
        ln = min(n - s, int(0.045 * SR))
        if ln > 0:
            h = _noise(ln, 6500, 15000, seed=b + 50) * np.exp(-np.arange(ln) / SR * 150)
            mixm[s:s + ln] += (h * (0.045 if b % 2 == 0 else 0.026)).astype(np.float32)
        b += 1

    # --- basse 1/8 (A F C G)
    roots = [55.0, 43.65, 65.41, 49.0]
    k = 0
    while k * beat / 2 < total:
        s = int(k * beat / 2 * SR)
        ln = min(n - s, int(0.26 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[int((k * beat / 2) / bar) % 4]
            v = np.sin(2 * np.pi * r * tt) + 0.4 * np.sin(4 * np.pi * r * tt)
            e = np.exp(-tt * 9) * np.minimum(tt / 0.006, 1)
            sos = butter(2, 180 / (SR / 2), btype="low", output="sos")
            mixm[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * 0.30).astype(np.float32)
        k += 1

    # --- pad atmosphérique (aigu, discret)
    for bi in range(int(total / bar) + 1):
        s = int(bi * bar * SR)
        e_ = min(n, int((bi * bar + bar + .6) * SR))
        if s >= n:
            break
        tt = np.arange(e_ - s) / SR
        r = roots[bi % 4] * 4
        env = np.minimum(tt / .5, 1) * np.exp(-np.maximum(tt - bar * .5, 0) * 1.8)
        v = (np.sin(2 * np.pi * r * tt) * .5 + np.sin(2 * np.pi * r * 1.5 * tt + .7) * .32)
        sos = butter(2, 2600 / (SR / 2), btype="low", output="sos")
        mixm[s:e_] += (sosfilt(sos, (v * env).astype(np.float32)) * 0.10).astype(np.float32)

    # --- arp 16e à partir du 2e plan
    step = beat / 4
    k = 0
    t0 = CUTS[1]
    while t0 < total - .2:
        s = int(t0 * SR)
        ln = min(n - s, int(.22 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            note = roots[int(t0 / bar) % 4] * 8 * (2 ** ([0, 7, 12, 3][k % 4] / 12))
            a = np.sin(2 * np.pi * note * tt) * np.exp(-tt * 22)
            mixm[s:s + ln] += (a * 0.055).astype(np.float32)
        k += 1
        t0 += step

    # --- impacts sur chaque coupe
    for i, cut in enumerate(CUTS[:-1]):
        s = int(cut * SR)
        ln = min(n - s, int(1.0 * SR))
        if ln <= 0:
            continue
        tt = np.arange(ln) / SR
        boom = np.sin(2 * np.pi * (58 * tt - 14 * tt ** 2)) * np.exp(-tt * 6)
        air = _noise(ln, 250, 4000, seed=100 + i) * np.exp(-tt * 9)
        amp = 0.55 if i in (0, 2, 7) else 0.30
        mixm[s:s + ln] += ((boom * .8 + air * .5) * amp).astype(np.float32)

    # --- risers avant les plans 3 et 8
    for cut in (CUTS[2], CUTS[7]):
        d_ = 1.6
        s = max(0, int((cut - d_) * SR))
        ln = min(n - s, int(d_ * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = _noise(ln, 500, 9000, seed=int(cut)) * (tt / d_) ** 2.2
            mixm[s:s + ln] += (r * 0.20).astype(np.float32)

    # --- ticks UI (compteurs)
    for tp in (CUTS[3] + .10, CUTS[3] + .30, CUTS[4] + .10, CUTS[4] + .30,
               CUTS[1] + 1.55, CUTS[1] + 1.85):
        s = int(tp * SR)
        ln = min(n - s, int(.05 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            mixm[s:s + ln] += (np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 120) * .09)

    # --- ding final
    s = int((TOTAL - 2.2) * SR)
    ln = min(n - s, int(1.4 * SR))
    if ln > 0:
        tt = np.arange(ln) / SR
        v = (np.sin(2 * np.pi * 1318 * tt) * .6 + np.sin(2 * np.pi * 1975 * tt) * .4)
        mixm[s:s + ln] += (v * np.exp(-tt * 4.0) * .16).astype(np.float32)

    # stéréo + limiteur doux
    dly = int(.012 * SR)
    left = mixm
    right = np.concatenate([np.zeros(dly, np.float32), mixm[:-dly]])
    st = np.stack([left * .98 + right * .08, right * .98 + left * .08], axis=1)
    st = st / (np.abs(st).max() + 1e-9) * 0.90
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path


# ------------------------------------------------------------------ main
def preview(out_path):
    times = [(CUTS[i] + CUTS[i + 1]) / 2 for i in range(len(CUTS) - 1)]
    bg = build_bg()
    global _BG
    _BG = bg
    sheet = Image.new("RGB", (4 * (432 + 8) + 8, 2 * (768 + 8) + 8), (18, 18, 20))
    sd = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        im = render_frame(int(t * FPS)).resize((432, 768), Image.LANCZOS)
        x = 8 + (i % 4) * 440
        y = 8 + (i // 4) * 776
        sheet.paste(im, (x, y))
        sd.rectangle([x, y, x + 150, y + 26], fill=(0, 0, 0))
        sd.text((x + 6, y + 4), f"t={t:05.2f}s", font=F("i5", 17), fill=(255, 255, 255))
    sheet.save(out_path, quality=90)
    print("Saved preview:", out_path)


def render():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    nf = int(round(TOTAL * FPS))
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", "-movflags", "+faststart", TMP_VIDEO],
                            stdin=subprocess.PIPE)
    for fi in range(nf):
        proc.stdin.write(render_frame(fi).tobytes())
        if fi % 150 == 0:
            print(f"  {fi}/{nf} ({fi / nf * 100:.0f}%)", flush=True)
    proc.stdin.close()
    proc.wait()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP_VIDEO, "-i", MIX,
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
    print("Score + SFX (no voice) ...")
    raw = "/tmp/_leger_v2_raw.wav"
    build_score(TOTAL, raw)
    # mastering réseaux sociaux : EQ de présence + gain + limiteur
    from imageio_ffmpeg import get_ffmpeg_exe
    subprocess.run([get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", raw, "-af",
                    "highpass=f=34,"
                    "equalizer=f=180:width_type=o:width=1:g=-2.5,"
                    "equalizer=f=3200:width_type=o:width=1.2:g=4.0,"
                    "volume=8.0dB,alimiter=limit=0.94:level=disabled",
                    "-ar", str(SR), MIX], check=True)
    if a.audio_only:
        print("Audio ->", MIX)
        return
    render()


if __name__ == "__main__":
    main()
