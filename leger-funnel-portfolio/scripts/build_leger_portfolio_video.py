#!/usr/bin/env python3
"""Léger Akodjenou — Funnel Builder | vertical marketing film (9:16, 30 fps).

Built from the content of https://legerakodjenou6.systeme.io/47e3d8ba

    python3 build_leger_portfolio_video.py --preview /tmp/preview.jpg
    python3 build_leger_portfolio_video.py
"""
import argparse
import math
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from film_lib import *  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
FILM_DIR = os.path.join(PROJECT, "film")
AUDIO_DIR = os.path.join(PROJECT, "assets", "audio")
os.makedirs(FILM_DIR, exist_ok=True)

OUT = os.path.join(FILM_DIR, "leger-akodjenou-funnel-builder-9x16.mp4")
TMP_VIDEO = "/tmp/leger_video_only.mp4"
MIX = os.path.join(AUDIO_DIR, "master_mix.wav")

M = 84
CW = W - M * 2

# name, start, end
SCENES = [
    ("hook", 0.00, 5.00),
    ("problem", 5.00, 9.32),
    ("reveal", 9.32, 17.43),
    ("noirson", 17.43, 24.30),
    ("ascension", 24.30, 30.15),
    ("horizon", 30.15, 36.27),
    ("method", 36.27, 42.79),
    ("cta", 42.79, 52.10),
]
TOTAL = SCENES[-1][2]
CHAPTERS = {
    "hook": "01 / 08",
    "problem": "02 / 08",
    "reveal": "03 / 08",
    "noirson": "04 / 08",
    "ascension": "05 / 08",
    "horizon": "06 / 08",
    "method": "07 / 08",
    "cta": "08 / 08",
}

VO = [(f"{AUDIO_DIR}/vo-s{i}.mp3", SCENES[i - 1][1] + 0.40, tempo)
      for i, tempo in enumerate([1.00, 1.00, 1.05, 1.10, 1.12, 1.08, 1.10, 1.05], start=1)]


# ------------------------------------------------------------------ helpers
def ac(canvas, im, xy=(0, 0)):
    """alpha_composite with guaranteed integer destination (Pillow needs ints)."""
    canvas.alpha_composite(im, (int(xy[0]), int(xy[1])))

def fit(kind, text, size, maxw, d, min_size=12):
    while size > min_size and tlen(d, text, F(kind, size)) > maxw:
        size -= 2
    return size


def eyebrow(d, text, y, a=1.0, color=AMBER, x=M):
    if a <= 0:
        return
    d.line([(x, y + 13), (x + 30, y + 13)], fill=col(color, 230 * a), width=3)
    tracked(d, (x + 48, y), text.upper(), F("isb", 21), col(color, 225 * a), tracking=4.2)


def h1(d, lines, y, size, color=TEXT, a=1.0, lh=1.06, x=M, tracking=-1.6, rise=0.0):
    """Multi-line display headline with optional rise offset."""
    f = F("xb", size)
    for i, line in enumerate(lines):
        tracked(d, (x, y + i * size * lh - rise), line, f, col(color, 255 * a), tracking)


def stat_chip(d, x, y, value, label, color=MINT, a=1.0):
    f1, f2 = F("xb", 30), F("isb", 19)
    wpx = max(tlen(d, value, f1), tlen(d, label, f2, 2)) + 52
    im = glass_card(int(wpx), 86, 22, top_a=26, bot_a=8, border_a=36)
    d2 = ImageDraw.Draw(im)
    tracked(d2, (26, 14), value, f1, col(color, 255 * a))
    tracked(d2, (26, 54), label.upper(), f2, col(MUTED, 235 * a), tracking=2.0)
    return im


def ring(canvas, d, cx, cy, r, pct, color, width=16, track=(255, 255, 255, 26), glow=True):
    if glow and pct > 0.004:
        pad = 34
        size = int(r * 2 + pad * 2)
        gl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(gl).arc([pad, pad, pad + r * 2, pad + r * 2], -90, -90 + 360 * pct,
                               fill=col(color, 150), width=width + 12)
        gl = gl.filter(ImageFilter.GaussianBlur(15))
        ac(canvas, gl, (int(cx - r - pad), int(cy - r - pad)))
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, 270, fill=track, width=width)
    if pct > 0.004:
        d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * pct, fill=col(color, 255), width=width)
        ang = math.radians(-90 + 360 * pct)
        ex, ey = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        d.ellipse([ex - width / 2 - 1, ey - width / 2 - 1, ex + width / 2 + 1, ey + width / 2 + 1],
                  fill=col(color, 255))


# ------------------------------------------------------------ mockup: browser
def browser_frame(w, h, url, content, radius=24, dark=True):
    frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius,
                        fill=(12, 10, 20, 255) if dark else (250, 248, 244, 255),
                        outline=(255, 255, 255, 40), width=2)
    bar = 46
    d.rounded_rectangle([0, 0, w - 1, bar + radius], radius,
                        fill=(20, 17, 32, 255) if dark else (238, 234, 226, 255))
    d.rectangle([0, bar - radius, w - 1, bar], fill=(20, 17, 32, 255) if dark else (238, 234, 226, 255))
    d.line([(0, bar), (w - 1, bar)], fill=(255, 255, 255, 26), width=1)
    for i, c in enumerate([(255, 106, 120), (255, 190, 92), (72, 209, 156)]):
        d.ellipse([18 + i * 20, bar / 2 - 5, 28 + i * 20, bar / 2 + 5], fill=col(c, 235))
    px, py, ph = 92, 11, 24
    d.rounded_rectangle([px, py, w - 20, py + ph], ph / 2, fill=(255, 255, 255, 22) if dark else (0, 0, 0, 16))
    d.rounded_rectangle([px + 11, py + 8, px + 17, py + 15], 2, outline=col(MINT if dark else (60, 120, 90), 220), width=1)
    d.arc([px + 11, py + 3, px + 17, py + 11], 180, 360, fill=col(MINT if dark else (60, 120, 90), 220), width=1)
    tracked(d, (px + 27, py + 4), url, F("ir", 15), col(MUTED if dark else (110, 104, 96), 235), tracking=0.3)

    body = content.copy()
    if body.size != (w, h - bar):
        body = ImageOps.fit(body, (w, h - bar), Image.LANCZOS)
    mask = rounded_mask(w, h - bar, radius)
    frame.paste(body, (0, bar), mask)
    return frame


# ------------------------------------------------- mockup: NOIR·SON product page
def noirson_page(w, h):
    im = Image.new("RGBA", (w, h), (9, 9, 14, 255))
    d = ImageDraw.Draw(im)
    # atmosphere
    gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.ellipse([w * 0.45, -h * 0.25, w * 1.15, h * 0.75], fill=(78, 58, 150, 90))
    gl = gl.filter(ImageFilter.GaussianBlur(60))
    im.alpha_composite(gl)

    # nav
    tracked(d, (36, 30), "NOIR·SON", F("xb", 21), col(TEXT, 245), tracking=3.4)
    nav = ["Casques", "Écouteurs", "Histoire"]
    x = w * 0.40
    for n in nav:
        d.text((x, 34), n, font=F("im", 14), fill=col(MUTED, 225))
        x += d.textlength(n, font=F("im", 14)) + 22
    d.text((w - 118, 34), "Panier (1)", font=F("im", 14), fill=col(TEXT, 235))
    d.line([(36, 72), (w - 36, 72)], fill=(255, 255, 255, 26), width=1)

    # headphone illustration (right)
    cx, cy = w * 0.755, h * 0.50
    bw, bh = 210, 250
    # halo
    halo = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([40, 60, 320, 340], fill=(124, 92, 255, 46))
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(34)), (int(cx - 180), int(cy - 170)))
    # headband
    d.arc([cx - bw / 2, cy - bh * 0.68, cx + bw / 2, cy + bh * 0.26], 188, 352,
          fill=(206, 208, 220, 255), width=30)
    d.arc([cx - bw / 2 + 5, cy - bh * 0.68 + 7, cx + bw / 2 - 5, cy + bh * 0.26 - 7], 188, 352,
          fill=(154, 156, 176, 255), width=7)
    d.arc([cx - bw / 2 - 1, cy - bh * 0.68 - 1, cx + bw / 2 + 1, cy + bh * 0.26 + 1], 246, 320,
          fill=col(VIOLET_SOFT, 220), width=5)
    # ear cups
    for sx in (-1, 1):
        ex = cx + sx * (bw / 2 - 8)
        d.rounded_rectangle([ex - 34, cy - 26, ex + 34, cy + 118], 30, fill=(26, 26, 36, 255),
                            outline=(190, 192, 208, 255), width=4)
        d.rounded_rectangle([ex - 24, cy - 12, ex + 24, cy + 104], 22, fill=(16, 16, 24, 255),
                            outline=(120, 122, 140, 200), width=2)
        d.ellipse([ex - 13, cy + 34, ex + 13, cy + 60], fill=(88, 84, 110, 255))
    # violet rim light
    d.arc([cx - bw / 2 - 2, cy - bh * 0.62 - 2, cx + bw / 2 + 2, cy + bh * 0.30 + 2], 250, 330,
          fill=col(VIOLET_SOFT, 230), width=4)

    # copy (left)
    tracked(d, (36, 96), "NOUVEAU", F("isb", 12), col(AMBER, 240), tracking=3.0)
    tracked(d, (36, 118), "Le silence,", F("xb", 40), col(TEXT, 255), tracking=-1.0)
    tracked(d, (36, 166), "enfin.", F("xb", 40), col(TEXT, 255), tracking=-1.0)
    para(d, "Casque à réduction de bruit active\n40 h d'autonomie · Bluetooth 5.3", F("ir", 13),
         col(MUTED, 240), 36, 222, w * 0.42, lh=1.5)
    tracked(d, (36, 282), "249 €", F("xb", 30), col(TEXT, 255))
    d.rounded_rectangle([36, 322, 240, 366], 12, fill=(245, 243, 255, 245))
    tracked(d, (54, 336), "AJOUTER AU PANIER", F("isb", 12), col((10, 9, 16), 255), tracking=0.8)

    # order bump
    by = h - 96
    d.rounded_rectangle([36, by, w - 36, by + 62], 12, fill=(255, 255, 255, 10),
                        outline=(255, 255, 255, 32), width=1)
    d.rounded_rectangle([50, by + 20, 68, by + 38], 5, fill=col(MINT, 255))
    d.line([(54, by + 29), (58, by + 34), (65, by + 24)], fill=(8, 30, 24, 255), width=2)
    d.text((82, by + 14), "Étui de transport en cuir", font=F("isb", 13), fill=col(TEXT, 240))
    d.text((82, by + 34), "Ajouté automatiquement au panier", font=F("ir", 11), fill=col(MUTED, 220))
    d.text((w - 116, by + 22), "+ 19 €", font=F("isb", 15), fill=col(AMBER, 245))
    return im


# ---------------------------------------------------- mockup: editorial page
def editorial_page(w, h):
    im = Image.new("RGBA", (w, h), (244, 239, 231, 255))
    d = ImageDraw.Draw(im)
    ink = (23, 20, 28)
    tracked(d, (36, 28), "MAISON ÉLAN", F("xb", 18), col(ink, 255), tracking=3.6)
    x = w * 0.44
    for n in ["Collections", "Journal", "À propos"]:
        d.text((x, 31), n, font=F("im", 12), fill=(90, 84, 78, 255))
        x += d.textlength(n, font=F("im", 12)) + 18
    d.line([(36, 66), (w - 36, 66)], fill=(23, 20, 28, 40), width=1)

    # terracotta arch (all coordinates clamped so it stays valid at any height)
    ax0, ay0, ax1, ay1 = int(w * 0.60), int(h * 0.16), int(w * 0.92), int(h * 0.86)
    aw = ax1 - ax0
    body_top = ay0 + int(aw * 0.42)
    d.rounded_rectangle([ax0, body_top, ax1, ay1], 10, fill=(188, 104, 76, 255))
    d.pieslice([ax0, ay0, ax1, ay0 + int(aw * 1.02)], 180, 360, fill=(188, 104, 76, 255))
    inner_top = body_top + int((ay1 - body_top) * 0.18)
    d.ellipse([ax0 + int(aw * 0.16), inner_top, ax1 - int(aw * 0.16), ay1 - int(h * 0.06)],
              fill=(214, 132, 100, 255))
    d.ellipse([ax0 + int(aw * 0.30), inner_top + int(h * 0.07),
               ax1 - int(aw * 0.30), ay1 - int(h * 0.14)], fill=(168, 88, 62, 255))
    d.rectangle([ax0, ay1 - 16, ax1, ay1], fill=(232, 224, 212, 255))

    # copy
    tracked(d, (36, h * 0.24), "PRINTEMPS · ÉDITION 04", F("isb", 10), (150, 92, 66, 255), tracking=2.6)
    tracked(d, (36, h * 0.29), "La collection", F("xb", 38), col(ink, 255), tracking=-1.0)
    tracked(d, (36, h * 0.29 + 46), "qui respire.", F("xb", 38), col(ink, 255), tracking=-1.0)
    para(d, "Des matières naturelles,\ndes coupes qui laissent\nle corps libre.", F("ir", 13),
         (96, 90, 84, 255), 36, h * 0.29 + 108, w * 0.46, lh=1.6)
    d.rounded_rectangle([36, h * 0.29 + 210, 186, h * 0.29 + 252], 21, outline=(40, 34, 30, 255), width=1)
    tracked(d, (56, h * 0.29 + 222), "DÉCOUVRIR", F("isb", 11), col(ink, 255), tracking=1.6)
    return im


# ------------------------------------------------------- mockup: retreat page
def retreat_page(w, h):
    im = Image.new("RGBA", (w, h), (14, 26, 24, 255))
    d = ImageDraw.Draw(im)
    gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([-w * 0.2, h * 0.35, w * 0.8, h * 1.3], fill=(26, 120, 104, 95))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(56)))
    tracked(d, (30, 26), "HORIZON RETREAT", F("xb", 16), col((240, 236, 224), 250), tracking=3.2)
    d.text((w - 92, 28), "Réserver", font=F("im", 12), fill=col((240, 236, 224), 225))
    tracked(d, (30, h * 0.24), "7 jours pour", F("xb", 30), col((244, 240, 228), 255), tracking=-0.8)
    tracked(d, (30, h * 0.24 + 40), "respirer.", F("xb", 30), col((244, 240, 228), 255), tracking=-0.8)
    para(d, "Bali · 12–19 mars\nYoga, silence, océan.", F("ir", 12), col((176, 200, 190), 245),
         30, h * 0.24 + 96, w * 0.55, lh=1.55)
    d.rounded_rectangle([30, h - 96, 196, h - 48], 12, fill=(238, 232, 214, 250))
    tracked(d, (48, h - 83), "RÉSERVER MA PLACE", F("isb", 10), col((12, 32, 28), 255), tracking=0.6)
    d.rounded_rectangle([212, h - 96, 330, h - 48], 12, outline=(255, 255, 255, 60), width=1)
    tracked(d, (230, h - 83), "4 PLACES", F("isb", 10), col((255, 216, 150), 250), tracking=0.8)
    return im


# ------------------------------------------------------------------ scenes
def scene_hook(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    eyebrow(d, "Le problème", 292, a)
    h1(d, ["Du trafic."], 348, 104, TEXT, a, rise=(1 - eob(prog(lt, 0.10, 0.62))) * 44)
    h1(d, ["Zéro client."], 470, 104, AMBER, a, rise=(1 - eob(prog(lt, 0.28, 0.62))) * 44)
    tracked(d, (M, 610), "Vos visiteurs arrivent. Puis repartent.",
            F("im", 30), col(MUTED, 240 * a), tracking=0.2)

    ca = eob(prog(lt, 0.55, 0.7))
    cw_, ch_ = CW, 420
    card = glass_card(cw_, ch_, 30, top_a=34, bot_a=10)
    cd = ImageDraw.Draw(card)
    tracked(cd, (40, 34), "TRAFIC DU SITE · 30 DERNIERS JOURS", F("isb", 17), col(MUTED, 235), tracking=2.4)
    tracked(cd, (40, 74), "1 240", F("xb", 78), col(TEXT, 255))
    tracked(cd, (40, 170), "VISITEURS", F("isb", 16), col(DIM, 240), tracking=2.2)
    tracked(cd, (cw_ - 40, 74), "0", F("xb", 78), col(ROSE, 255), center=cw_ - 40 - 22)
    cd.text((cw_ - 96, 170), "VENTES", font=F("isb", 16), fill=col(DIM, 240))

    # sparkline
    sx0, sx1 = 40, cw_ - 40
    top, bot = 212, 322
    n = 46
    reveal = eio(prog(lt, 0.9, 1.5))
    pts = []
    for i in range(n):
        f = i / (n - 1)
        y = bot - (bot - top) * (0.10 + 0.80 * f ** 1.35 + 0.06 * math.sin(f * 8.2))
        pts.append((sx0 + (sx1 - sx0) * f, y))
    cut = max(2, int(len(pts) * reveal))
    vis = pts[:cut]
    area = Image.new("L", (cw_ - 80, 160), 0)
    ImageDraw.Draw(area).polygon([(x - sx0, y - 200) for x, y in vis] + [(vis[-1][0] - sx0, 140), (0, 140)], fill=255)
    grad = np.zeros((160, cw_ - 80, 4), np.uint8)
    grad[..., 0], grad[..., 1], grad[..., 2] = VIOLET
    grad[..., 3] = (np.linspace(58, 0, 160)[:, None] * np.array(area) / 255).astype(np.uint8)
    card.alpha_composite(Image.fromarray(grad), (40, 200))
    cd.line(vis, fill=col(VIOLET_SOFT, 255), width=5, joint="curve")
    cd.ellipse([vis[-1][0] - 7, vis[-1][1] - 7, vis[-1][0] + 7, vis[-1][1] + 7], fill=col(TEXT, 255))

    # conversion bar
    tracked(cd, (40, 352), "TAUX DE CONVERSION", F("isb", 15), col(DIM, 235), tracking=2.0)
    tracked(cd, (cw_ - 40 - 54, 344), "0,8 %", F("xb", 24), col(ROSE, 255))
    cd.rounded_rectangle([40, 382, cw_ - 40, 390], 4, fill=(255, 255, 255, 26))
    cd.rounded_rectangle([40, 382, 40 + (cw_ - 80) * 0.035 * reveal, 390], 4, fill=col(ROSE, 255))

    place(canvas, with_alpha(card, ca), M, 720 + (1 - ca) * 26, blur=30, alpha=130, dy=22)

    # the leak: three shrinking bars
    la = eo(prog(lt, 1.55, 0.5))
    if la > 0:
        tracked(d, (M, 1200), "OÙ PART L'ARGENT", F("isb", 17), col(DIM, 235 * la), tracking=2.8)
        rows = [("Visiteurs", "1 240", 1.00, VIOLET_SOFT),
                ("Demandes de devis", "12", 0.34, AMBER),
                ("Clients signés", "0", 0.045, ROSE)]
        for i, (label, val, frac, c_) in enumerate(rows):
            ra = eob(prog(lt, 1.65 + i * 0.17, 0.62))
            if ra <= 0:
                continue
            y = 1252 + i * 92 + (1 - ra) * 16
            d.text((M, y), label, font=F("im", 23), fill=col(MUTED, 240 * ra))
            d.text((W - M - tlen(d, val, F("xb", 28)), y - 4), val,
                   font=F("xb", 28), fill=col(c_, 250 * ra))
            bw_ = max(10, (CW - 250) * frac * ra)
            d.rounded_rectangle([M, y + 38, M + CW - 250, y + 44], 3, fill=(255, 255, 255, 22))
            d.rounded_rectangle([M, y + 38, M + bw_, y + 44], 3, fill=col(c_, 235 * ra))

    # bottom nudge
    na = eo(prog(lt, 2.9, 0.6))
    if na > 0:
        arrow_v(d, W // 2, 1568, 40 + 8 * math.sin(lt * 3), col(AMBER, 210 * na), width=3, head=11)
        tracked(d, (M, 1650), "Et si le problème n'était pas le trafic ?", F("im", 27),
                col(MUTED, 220 * na), tracking=0.2)


def scene_problem(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    eyebrow(d, "Le vrai problème", 250, a)
    h1(d, ["Joli.", "Mais il ne vend pas."], 302, 74, TEXT, a,
       rise=(1 - eob(prog(lt, 0.12, 0.6))) * 36)

    ma = eob(prog(lt, 0.22, 0.66))
    mw, mh = 860, 500
    page = editorial_page(mw, mh - 46)
    mock = browser_frame(mw, mh, "maison-elan.com", page, dark=False)
    grey = grayscale(mock, 0.90 * eo(prog(lt, 0.9, 1.6)))
    grey = with_alpha(grey, ma)
    rot = rotate_soft(grey, -2.2)
    place(canvas, rot, (W - rot.width) // 2, 570 + (1 - ma) * 40, blur=34, alpha=140, dy=26)

    # "0 conversion" chip pinned on the mockup
    ca = eo(prog(lt, 1.5, 0.5))
    if ca > 0:
        chip = pill("0 conversion", size=22, fg=col(ROSE, 255), bg=(40, 12, 24, 230),
                    border=col(ROSE, 140), dot=True, dot_col=ROSE)
        chip = with_alpha(chip, ca)
        ac(canvas, chip, (W - 330, 1030))

    # caption
    qa = eo(prog(lt, 1.55, 0.7))
    if qa > 0:
        d.rectangle([M, 1122, M + 5, 1226], fill=col(AMBER, 230 * qa))
        para(d, "Une belle page qui ne vend pas,\nc'est de la décoration.", F("isb", 37),
             col(TEXT, 250 * qa), M + 34, 1122, 790, lh=1.34)
        tracked(d, (M + 34, 1218), "— Léger Akodjenou", F("im", 22), col(MUTED, 230 * qa), tracking=0.4)

    # diagnostic statement
    la = eo(prog(lt, 2.02, 0.6))
    if la > 0:
        tracked(d, (M, 1320), "LE DIAGNOSTIC", F("isb", 17), col(DIM, 235 * la), tracking=2.8)
        tracked(d, (M, 1362), "Ce n'est pas le trafic.", F("sb", 45), col(TEXT, 250 * la), tracking=-0.8)
        tracked(d, (M, 1416), "C'est le parcours.", F("sb", 45), col(AMBER, 250 * la), tracking=-0.8)

        for i, item in enumerate(["Promesse absente", "Zéro preuve", "Zéro urgence"]):
            ia = eob(prog(lt, 2.32 + i * 0.13, 0.5))
            if ia <= 0:
                continue
            p = with_alpha(pill(item, size=20, fg=col(ROSE, 240), bg=(255, 255, 255, 10),
                                border=col(ROSE, 95), pad_x=20, pad_y=11), ia)
            x = M + i * 248
            ac(canvas, p, (x, 1502 + (1 - ia) * 12))

    # bottom nudge
    na = eo(prog(lt, 3.0, 0.6))
    if na > 0:
        arrow_v(d, W // 2, 1622, 38 + 8 * math.sin(lt * 3), col(AMBER, 210 * na), width=3, head=11)
        tracked(d, (M, 1680), "Et si le problème n'était pas le trafic ?", F("im", 26),
                col(MUTED, 220 * na), tracking=0.2)


def scene_reveal(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.55))
    eyebrow(d, "Le funnel builder", 250, a)

    # name with shine sweep
    name_layer = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    nd = ImageDraw.Draw(name_layer)
    rise = (1 - eob(prog(lt, 0.08, 0.7))) * 46
    tracked(nd, (M, 6 + rise), "LÉGER", F("xb", 120), col(TEXT, 255 * a), tracking=-2.4)
    tracked(nd, (M, 148 + rise), "AKODJENOU", F("xb", 120), col(TEXT, 255 * a), tracking=-2.4)

    sh = prog(lt, 1.10, 0.95)
    if 0 < sh < 1:
        band = Image.new("L", (W, 330), 0)
        bx = -300 + sh * (W + 600)
        ImageDraw.Draw(band).polygon([(bx, 0), (bx + 130, 0), (bx - 90, 330), (bx - 220, 330)], fill=210)
        band = band.filter(ImageFilter.GaussianBlur(26))
        mask = ImageChops.multiply(name_layer.getchannel("A"), band)
        shine = Image.new("RGBA", (W, 330), col((255, 232, 190), 235))
        shine.putalpha(mask)
        name_layer.alpha_composite(shine)
    ac(canvas, name_layer, (0, 300))

    sa = eo(prog(lt, 0.75, 0.6))
    if sa > 0:
        f = F("im", 31)
        d.text((M, 616), "Cotonou, Bénin", font=f, fill=col(MUTED, 240 * sa))
        ax = M + d.textlength("Cotonou, Bénin", font=f) + 16
        arrow_h(d, ax, 632, 44, col(AMBER, 235 * sa), width=2, head=8)
        d.text((ax + 58, 616), "monde entier", font=f, fill=col(MUTED, 240 * sa))

    # +20% counter
    ca = eo(prog(lt, 2.05, 1.15))
    val = 20 * eob(prog(lt, 1.15, 1.35))
    if ca > 0:
        fnum = F("xb", 200)
        num = f"{int(round(val))}"
        fsym = F("b", 66)
        wnum = tlen(d, num, fnum)
        x = M
        d.text((x, 730), "+", font=fsym, fill=col(AMBER, 245 * ca))
        d.text((x + 46, 700), num, font=fnum, fill=col(TEXT, 255 * ca))
        d.text((x + 46 + wnum + 6, 762), "%", font=fsym, fill=col(AMBER, 245 * ca))
        tracked(d, (M + 4, 930), "TAUX DE CONVERSION VISÉ", F("isb", 20), col(MUTED, 240 * ca), tracking=3.0)

    # chips
    chips = [("6", "étapes"), ("24 h", "de réponse"), ("14 j", "de support")]
    y = 1010
    x = M
    for i, (v, l) in enumerate(chips):
        ca2 = eob(prog(lt, 2.5 + i * 0.16, 0.5))
        if ca2 > 0:
            ch = stat_chip(d, x, y, v, l, [MINT, AMBER, VIOLET_SOFT][i], ca2)
            ac(canvas, with_alpha(ch, ca2), (x, y + (1 - ca2) * 18))
            x += ch.width + 14

    # skills marquee
    ma = eo(prog(lt, 3.0, 0.8))
    if ma > 0:
        band_h = 96
        band = glass_card(CW, band_h, 24, top_a=20, bot_a=6, border_a=26)
        ac(canvas, with_alpha(band, ma), (M, 1160))
        items = ["Pages de capture", "Pages de vente", "Upsells & order bumps", "Séquences e-mail",
                 "Webinaires automatisés", "Copywriting", "Systeme.io", "A/B testing"]
        f = F("isb", 24)
        sep = 26
        widths = [tlen(d, s, f) for s in items]
        cycle = sum(widths) + sep * len(items)
        off = (lt * 48) % cycle
        clip = Image.new("RGBA", (CW - 40, band_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(clip)
        x = -off
        for rep in range(3):
            for s, wd in zip(items, widths):
                if -300 < x < CW:
                    cd.text((x, 32), s, font=f, fill=col(TEXT if rep else TEXT, 235 * ma))
                    cd.ellipse([x + wd + 10, 45, x + wd + 16, 51], fill=col(AMBER, 230 * ma))
                x += wd + sep
        mask = rounded_mask(CW - 40, band_h, 20)
        ac(canvas, Image.composite(clip, Image.new("RGBA", clip.size, (0, 0, 0, 0)), mask),
                               (M + 20, 1160))

    # testimonial
    ta = eo(prog(lt, 2.80, 0.8))
    if ta > 0:
        para(d, "« Léger ne dessine pas des pages,\nil construit des machines à vendre. »",
             F("isb", 33), col(TEXT, 245 * ta), M, 1300, 860, lh=1.4)
        tracked(d, (M, 1418), "MARIAM S. · HORIZON RETREAT", F("isb", 17),
                col(MUTED, 225 * ta), tracking=2.4)

    # tool stack
    sta = eo(prog(lt, 3.38, 0.7))
    if sta > 0:
        tracked(d, (M, 1492), "MA BOÎTE À OUTILS", F("isb", 17), col(DIM, 230 * sta), tracking=2.8)
        tools = ["Systeme.io", "ClickFunnels", "GoHighLevel", "MailerLite",
                 "Brevo", "Stripe", "Zapier", "Meta Ads"]
        x, y = M, 1540
        for i, tl_ in enumerate(tools):
            pa = eob(prog(lt, 3.44 + i * 0.05, 0.45))
            if pa <= 0:
                continue
            p = with_alpha(pill(tl_, size=20, fg=col(TEXT, 230), bg=(255, 255, 255, 12),
                                border=(255, 255, 255, 30), pad_x=20, pad_y=11), pa)
            if x + p.width > W - M:
                x, y = M, y + 58
            ac(canvas, p, (x, y + (1 - pa) * 10))
            x += p.width + 10


def scene_noirson(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    tracked(d, (M, 250), "01 / NOIR·SON", F("xb", 23), col(AMBER, 240 * a), tracking=2.2)
    cat, cf = "E-COMMERCE · AUDIO", F("isb", 16)
    tracked(d, (W - M - tlen(d, cat, cf, 2.2) + 2.2, 254), cat, cf, col(DIM, 230 * a), tracking=2.2)
    d.rectangle([W - M - 2, 250, W - M, 276], fill=col(VIOLET, 200 * a))

    ma = eob(prog(lt, 0.16, 0.62))
    mw, mh = 880, 590
    mock = browser_frame(mw, mh, "noirson.funnels.leger.studio", noirson_page(mw, mh - 46))
    mock = with_alpha(mock, ma)
    place(canvas, mock, (W - mw) // 2, 320 + (1 - ma) * 34, blur=34, alpha=150, dy=24)

    ta = eo(prog(lt, 1.1, 0.6))
    h1(d, ["Une page qui vend."], 975, 62, TEXT, ta, rise=(1 - eob(prog(lt, 1.1, 0.6))) * 26)
    tracked(d, (M, 1054), "Hero cinématique · preuve sociale · order bump",
            F("im", 26), col(MUTED, 235 * ta), tracking=0.2)

    ka = eob(prog(lt, 1.85, 0.7))
    val = 18 * eob(prog(lt, 1.85, 1.0))
    if ka > 0:
        d.text((M, 1120), "+", font=F("b", 58), fill=col(MINT, 245 * ka))
        d.text((M + 40, 1096), f"{int(round(val))}", font=F("xb", 150), fill=col(MINT, 255 * ka))
        d.text((M + 40 + tlen(d, f"{int(round(val))}", F("xb", 150)) + 4, 1150), "%",
               font=F("b", 58), fill=col(MINT, 245 * ka))
        tracked(d, (M + 6, 1262), "PANIER MOYEN", F("isb", 20), col(MUTED, 240 * ka), tracking=3.2)

    # tags
    for i, (t_, c_) in enumerate([("Page produit", VIOLET), ("Order bump", MINT), ("Upsell", AMBER)]):
        ca = eob(prog(lt, 2.28 + i * 0.13, 0.5))
        if ca > 0:
            p = with_alpha(pill(t_, size=22, fg=col(c_, 245), bg=(255, 255, 255, 14),
                                border=col(c_, 110)), ca)
            x = M + i * 210
            ac(canvas, p, (x, 1340 + (1 - ca) * 14))

    ta2 = eo(prog(lt, 2.85, 0.8))
    if ta2 > 0:
        para(d, "« L'order bump a augmenté notre\npanier moyen de 18 %. »", F("isb", 31),
             col(TEXT, 245 * ta2), M, 1470, 820, lh=1.42)
        tracked(d, (M, 1585), "SANDRA M. · E-COMMERÇANTE, NOIR·SON", F("isb", 16),
                col(MUTED, 225 * ta2), tracking=2.2)


def scene_ascension(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    tracked(d, (M, 220), "03 / ASCENSION", F("xb", 23), col(AMBER, 240 * a), tracking=2.2)
    tracked(d, (W - M - 220, 224), "COACHING · FORMATION", F("isb", 16), col(DIM, 230 * a), tracking=2.2)

    h1(d, ["Un tunnel complet.", "De A à Z."], 272, 68, TEXT, a,
       rise=(1 - eob(prog(lt, 0.12, 0.65))) * 34)

    # funnel
    stages = [("Page de capture", "4 800 vues"), ("Webinaire", "1 870 inscrits"),
              ("Séquence e-mail", "7 messages"), ("Page de vente", "412 clients"),
              ("Upsell & bump", "+ panier moyen")]
    top_w, bot_w = 700, 250
    st_h, gap = 86, 14
    y0 = 560
    for i, (label, meta) in enumerate(stages):
        sa = eob(prog(lt, 0.38 + i * 0.12, 0.5))
        if sa <= 0:
            continue
        f0 = i / len(stages)
        f1 = (i + 1) / len(stages)
        w_top = lerp(top_w, bot_w, f0)
        w_bot = lerp(top_w, bot_w, f1)
        y = y0 + i * (st_h + gap) + (1 - sa) * 26
        cx = W / 2
        pts = [(cx - w_top / 2, y), (cx + w_top / 2, y),
               (cx + w_bot / 2, y + st_h), (cx - w_bot / 2, y + st_h)]
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        c1 = mix(VIOLET, (86, 60, 200), f0)
        c2 = mix(VIOLET_SOFT, (150, 120, 255), f0)
        # vertical gradient inside the trapezoid
        gw, gh = int(max(w_top, w_bot)) + 4, st_h + 2
        gx = int(cx - gw / 2)
        arr = np.zeros((gh, gw, 4), np.uint8)
        for ch in range(3):
            arr[..., ch] = np.linspace(c1[ch], c2[ch], gh)[:, None].astype(np.uint8)
        arr[..., 3] = 235
        grad = Image.fromarray(arr)
        tr = Image.new("L", (gw, gh), 0)
        ImageDraw.Draw(tr).polygon([(p[0] - gx, p[1] - y) for p in pts], fill=255)
        layer.paste(grad, (gx, int(y)), tr)
        ld.line(pts + [pts[0]], fill=(255, 255, 255, 90), width=2, joint="curve")
        # label inside
        fs = 30 if i < 3 else 30
        ld.text((cx - tlen(ld, label, F("sb", fs)) / 2, y + st_h / 2 - 20), label,
                font=F("sb", fs), fill=col(TEXT, 250))
        if i < 3:
            ld.text((cx - tlen(ld, meta, F("im", 17)) / 2, y + st_h / 2 + 14), meta,
                    font=F("im", 17), fill=(255, 255, 255, 200))
        ac(canvas, with_alpha(layer, sa))

    # flowing particles
    for k in range(14):
        ph = (lt * 0.42 + k / 14) % 1.0
        y = y0 + ph * (5 * (st_h + gap) - gap)
        f = (y - y0) / (5 * (st_h + gap) - gap)
        width_here = lerp(top_w, bot_w, f)
        x = W / 2 + math.sin(k * 2.1 + lt * 1.6) * width_here * 0.22
        rr_ = 2.6 + 1.4 * math.sin(k + lt)
        d.ellipse([x - rr_, y - rr_, x + rr_, y + rr_], fill=col((235, 228, 255), 120))

    # KPI card
    ka = eob(prog(lt, 2.15, 0.7))
    if ka > 0:
        card = glass_card(CW, 200, 28, top_a=34, bot_a=10)
        cd = ImageDraw.Draw(card)
        val = int(round(412 * eob(prog(lt, 2.15, 1.1))))
        cd.text((40, 34), f"{val}", font=F("xb", 96), fill=col(MINT, 255))
        tracked(cd, (40, 140), "INSCRITS EN 14 JOURS", F("isb", 19), col(MUTED, 240), tracking=2.6)
        cd.line([(CW - 300, 34), (CW - 300, 166)], fill=(255, 255, 255, 34), width=2)
        tracked(cd, (CW - 262, 44), "7 E-MAILS", F("xb", 30), col(TEXT, 250))
        tracked(cd, (CW - 262, 84), "automatisés", F("im", 20), col(MUTED, 235))
        tracked(cd, (CW - 262, 124), "1 SEUL TUNNEL", F("isb", 16), col(AMBER, 235), tracking=1.6)
        ac(canvas, with_alpha(card, ka), (M, 1330 + (1 - ka) * 22))

    for i, (t_, c_) in enumerate([("Webinaire", VIOLET), ("Séquence e-mail", MINT), ("Page de vente", AMBER)]):
        ca = eob(prog(lt, 2.55 + i * 0.12, 0.5))
        if ca > 0:
            p = with_alpha(pill(t_, size=21, fg=col(c_, 245), bg=(255, 255, 255, 13), border=col(c_, 105)), ca)
            ac(canvas, p, (M + i * 250, 1585 + (1 - ca) * 12))

    ta = eo(prog(lt, 3.25, 0.7))
    if ta > 0:
        tracked(d, (M, 1690), "« 412 inscrits en deux semaines. »  — David K.",
                F("im", 24), col(MUTED, 225 * ta), tracking=0.2)


def scene_horizon(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    tracked(d, (M, 220), "04 / HORIZON RETREAT", F("xb", 23), col(AMBER, 240 * a), tracking=2.2)
    tracked(d, (W - M - 210, 224), "BIEN-ÊTRE · VOYAGE", F("isb", 16), col(DIM, 230 * a), tracking=2.2)

    h1(d, ["Un tunnel qui", "remplit le séjour."], 272, 66, TEXT, a,
       rise=(1 - eob(prog(lt, 0.12, 0.65))) * 34)

    # rings
    r = 128
    specs = [(W * 0.31, 800, 0.23, AMBER, "23", "CONVERSION"),
             (W * 0.69, 800, 0.61, MINT, "61", "INSCRIPTION")]
    for i, (cx, cy, target, color, num, label) in enumerate(specs):
        ra = eob(prog(lt, 0.55 + i * 0.26, 1.0))
        pct = target * ra
        ring(canvas, d, cx, cy, r, pct, color, width=15)
        d.text((cx - tlen(d, f"{int(round(target * 100 * ra))}", F("xb", 68)) / 2, cy - 52),
               f"{int(round(target * 100 * ra))}", font=F("xb", 68), fill=col(TEXT, 255 * min(1, ra * 2)))
        d.text((cx - tlen(d, "%", F("sb", 30)) / 2 - 42, cy + 22), "%", font=F("sb", 30),
               fill=col(color, 245 * min(1, ra * 2)))
        tracked(d, (0, cy + 92), label, F("isb", 16), col(MUTED, 225 * min(1, ra * 2)), tracking=2.6,
                center=cx)

    # retreat mockup
    ma = eob(prog(lt, 1.15, 0.7))
    if ma > 0:
        mw, mh = 700, 330
        mock = browser_frame(mw, mh, "horizonretreat.funnels.leger.studio", retreat_page(mw, mh - 46), radius=20)
        mock = with_alpha(mock, ma)
        place(canvas, mock, (W - mw) // 2, 1140 + (1 - ma) * 30, blur=28, alpha=135, dy=20)

    # tags
    for i, (t_, c_) in enumerate([("Storytelling", VIOLET), ("Acompte en ligne", MINT), ("Témoignages vidéo", AMBER)]):
        ca = eob(prog(lt, 2.6 + i * 0.13, 0.5))
        if ca > 0:
            p = with_alpha(pill(t_, size=21, fg=col(c_, 245), bg=(255, 255, 255, 13), border=col(c_, 105)), ca)
            ac(canvas, p, (M + i * 264, 1530 + (1 - ca) * 12))

    ta = eo(prog(lt, 2.95, 0.7))
    if ta > 0:
        tracked(d, (M, 1640), "« 9 % → 23 % de conversion après refonte. »",
                F("im", 25), col(MUTED, 230 * ta), tracking=0.2)
        tracked(d, (M, 1684), "MARIAM S. · FONDATRICE, HORIZON RETREAT",
                F("isb", 15), col(DIM, 220 * ta), tracking=2.0)


def scene_method(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    eyebrow(d, "La méthode", 240, a)
    h1(d, ["Zéro hasard."], 292, 92, TEXT, a, rise=(1 - eob(prog(lt, 0.12, 0.6))) * 34)
    tracked(d, (M, 412), "Six étapes, un seul système.", F("im", 27), col(MUTED, 235 * a), tracking=0.2)

    steps = [("Immersion & audit", "Offre, audience, chiffres, concurrence"),
             ("Architecture", "Le parcours complet, du clic à l'achat"),
             ("Copywriting", "Promesse, preuve, urgence"),
             ("Design & intégration", "Sur mesure, rapide, mobile-first"),
             ("Automatisation", "Tags, paiements, relances 24 h/24"),
             ("Tests & optimisation", "Heatmaps, A/B tests, conversion")]
    y0, row = 510, 178

    # connector
    line_a = eo(prog(lt, 0.45, 1.6))
    if line_a > 0:
        d.line([(M + 27, y0 + 40), (M + 27, y0 + 40 + (row * 5 + 40) * line_a)],
               fill=(255, 255, 255, 34), width=2)

    for i, (title, sub) in enumerate(steps):
        sa = eob(prog(lt, 0.42 + i * 0.17, 0.6))
        if sa <= 0:
            continue
        y = y0 + i * row + (1 - sa) * 22
        active = i == int((lt - 0.42) / 0.17) or (i == 5 and lt > 1.9)
        colr = AMBER if active else VIOLET_SOFT
        d.ellipse([M, y, M + 56, y + 56], outline=col(colr, 220 * sa), width=2,
                  fill=(124, 92, 255, 30) if not active else (255, 184, 77, 34))
        d.text((M + 15, y + 13), f"{i + 1:02d}", font=F("xb", 20), fill=col(colr, 245 * sa))
        tracked(d, (M + 86, y + 2), title, F("sb", 37), col(TEXT, 250 * sa), tracking=-0.4)
        tracked(d, (M + 86, y + 50), sub, F("ir", 23), col(MUTED, 225 * sa), tracking=0.1)

    ta = eo(prog(lt, 2.55, 0.8))
    if ta > 0:
        card = glass_card(CW, 156, 26, top_a=28, bot_a=8)
        cd = ImageDraw.Draw(card)
        tracked(cd, (30, 24), "LE RÉSULTAT", F("isb", 16), col(AMBER, 235), tracking=2.6)
        tracked(cd, (30, 54), "Un tunnel qui travaille", F("sb", 31), col(TEXT, 250))
        tracked(cd, (30, 94), "pour vous, 24 h/24.", F("sb", 31), col(TEXT, 250))
        ac(canvas, with_alpha(card, ta), (M, 1630))


def scene_cta(d, canvas, lt, dur):
    a = eo(prog(lt, 0.05, 0.5))
    eyebrow(d, "Prêt à convertir ?", 210, a)
    h1(d, ["Votre tunnel mérite", "mieux qu'un template."], 262, 60, TEXT, a,
       rise=(1 - eob(prog(lt, 0.12, 0.62))) * 32)

    # underline sweep on second line
    ua = eio(prog(lt, 1.0, 0.8))
    if ua > 0:
        d.rounded_rectangle([M + 2, 392, M + 2 + 452 * ua, 399], 4, fill=col(AMBER, 235))

    # offer card
    oa = eob(prog(lt, 0.55, 0.7))
    card = glass_card(CW, 196, 28, top_a=38, bot_a=12)
    cd = ImageDraw.Draw(card)
    pulse = 0.5 + 0.5 * math.sin(lt * 3.4)
    cd.ellipse([34, 38, 58, 62], fill=col(MINT, 120 + 80 * pulse))
    cd.ellipse([39, 43, 53, 57], fill=col(MINT, 255))
    tracked(cd, (74, 36), "DISPONIBLE POUR NOUVEAUX PROJETS", F("isb", 16),
            col(MINT, 235), tracking=2.2)
    tracked(cd, (34, 80), "Appel découverte · 30 min", F("xb", 40), col(TEXT, 255), tracking=-0.6)
    tracked(cd, (34, 138), "Offert · sans engagement · réponses sous 24 h",
            F("im", 23), col(MUTED, 235), tracking=0.1)
    off = pill("OFFERT", size=19, fg=(16, 11, 4, 255), bg=(255, 184, 77, 255),
               border=(255, 205, 120, 255), pad_x=18, pad_y=9)
    ac(canvas, with_alpha(card, oa), (M, 470 + (1 - oa) * 24))
    ac(canvas, with_alpha(off, oa), (M + CW - off.width - 28, 470 + 28 + (1 - oa) * 24))

    # contact rows
    ca = eob(prog(lt, 1.1, 0.7))
    if ca > 0:
        rows = [("mail", "legerakodjenou6@gmail.com"),
                ("phone", "+229 01 52 09 94 23"),
                ("pin", "Cotonou, Bénin · clients dans le monde entier")]
        ry = 720
        for i, (kind, text_) in enumerate(rows):
            ra = eob(prog(lt, 1.1 + i * 0.12, 0.5))
            if ra <= 0:
                continue
            yy = ry + i * 76 + (1 - ra) * 14
            d.rounded_rectangle([M, yy - 6, M + 56, yy + 50], 16, fill=(255, 255, 255, 12),
                                outline=(255, 255, 255, 30), width=1)
            if kind == "mail":
                icon_mail(d, M + 16, yy + 12, 24, col(VIOLET_SOFT, 240 * ra))
            elif kind == "phone":
                icon_phone(d, M + 16, yy + 6, 24, col(MINT, 240 * ra))
            else:
                icon_pin(d, M + 16, yy + 6, 24, col(AMBER, 240 * ra))
            d.text((M + 76, yy + 8), text_, font=F("im", 25), fill=col(TEXT, 245 * ra))

    # CTA button
    ba = eob(prog(lt, 1.9, 0.65))
    if ba > 0:
        bh = 104
        btn = Image.new("RGBA", (CW, bh), (0, 0, 0, 0))
        arr = np.zeros((bh, CW, 4), np.uint8)
        for ch in range(3):
            arr[..., ch] = np.linspace(AMBER[ch], (255, 138, 60)[ch], bh)[:, None].astype(np.uint8)
        arr[..., 3] = 255
        grad = Image.fromarray(arr)
        m = rounded_mask(CW, bh, 26)
        btn.paste(grad, (0, 0), m)
        bd = ImageDraw.Draw(btn)
        bd.text((44, 28), "Réserver mon appel découverte", font=F("xb", 34), fill=(22, 15, 6, 255))
        arrow_h(bd, CW - 96, bh / 2, 40, (22, 15, 6, 255), width=4, head=11)
        glow = btn.filter(ImageFilter.GaussianBlur(22))
        ac(canvas, with_alpha(glow, 0.55 * ba * (0.75 + 0.25 * pulse)), (M, 1020))
        ac(canvas, with_alpha(btn, ba), (M, 1020 + (1 - ba) * 18))

    # guarantees
    ga = eo(prog(lt, 2.6, 0.8))
    if ga > 0:
        items = ["Réponse sous 24 h", "Devis détaillé sous 48 h", "14 jours de support offerts"]
        x = M
        for i, s in enumerate(items):
            ia = eob(prog(lt, 2.6 + i * 0.13, 0.5))
            d.ellipse([x, 1186, x + 22, 1208], fill=col(MINT, 40 * ia), outline=col(MINT, 190 * ia), width=2)
            d.line([(x + 6, 1197), (x + 10, 1202), (x + 17, 1192)], fill=col(MINT, 245 * ia), width=2)
            d.text((x + 32, 1184), s, font=F("im", 19), fill=col(MUTED, 235 * ia))
            x += int(tlen(d, s, F("im", 19)) + 58)

    # closing line
    fa = eo(prog(lt, 3.2, 0.9))
    if fa > 0:
        d.line([(M, 1330), (W - M, 1330)], fill=col((255, 255, 255), 30 * fa), width=1)
        tracked(d, (M, 1370), "LÉGER AKODJENOU", F("xb", 34), col(TEXT, 250 * fa), tracking=1.0)
        tracked(d, (M, 1420), "FUNNEL BUILDER · SYSTEME.IO · COTONOU", F("isb", 16),
                col(MUTED, 225 * fa), tracking=2.4)
        tracked(d, (M, 1468), "legerakodjenou6.systeme.io", F("im", 22), col(VIOLET_SOFT, 225 * fa),
                tracking=0.2)

    # final mark
    ma = eo(prog(lt, 4.2, 1.0))
    if ma > 0:
        tracked(d, (0, 1600), "Des tunnels qui convertissent.", F("xb", 40),
                col(AMBER, 245 * ma), tracking=-0.8, center=W / 2)


# ------------------------------------------------------------------ chrome
def chrome(canvas, t, scene_name):
    d = ImageDraw.Draw(canvas)
    # wordmark
    wa = eo(prog(t, 0.2, 0.9))
    d.ellipse([M, 74, M + 10, 84], fill=col(AMBER, 230 * wa))
    tracked(d, (M + 22, 68), "LÉGER", F("xb", 24), col(TEXT, 235 * wa), tracking=1.2)
    tracked(d, (M + 22 + 118, 74), "FUNNEL BUILDER", F("isb", 14), col(DIM, 230 * wa), tracking=2.4)

    # chapter
    tracked(d, (W - M - 74, 72), CHAPTERS[scene_name], F("isb", 16), col(MUTED, 210), tracking=1.6)
    d.rectangle([W - M - 2, 96, W - M, 100], fill=col(VIOLET, 170))

    # progress
    py = 1846
    d.rounded_rectangle([M, py, W - M, py + 4], 2, fill=(255, 255, 255, 26))
    frac = clamp01(t / TOTAL)
    fw = int((W - 2 * M) * frac)
    if fw > 4:
        arr = np.zeros((4, fw, 4), np.uint8)
        for ch in range(3):
            arr[..., ch] = np.linspace(VIOLET[ch], AMBER[ch], max(fw, 2))[None, :].astype(np.uint8)
        arr[..., 3] = 255
        bar = Image.fromarray(arr)
        ac(canvas, bar, (M, py))


def transition_flash(canvas, t, scene_start):
    """Thin light sweep on each cut for a filmic feel."""
    lt = t - scene_start
    if 0 <= lt < 0.34:
        p = lt / 0.34
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x = -400 + p * (W + 800)
        d.polygon([(x, 0), (x + 170, 0), (x - 120, H), (x - 290, H)],
                  fill=(180, 160, 255, int(26 * (1 - p))))
        ac(canvas, layer.filter(ImageFilter.GaussianBlur(40)))


# ------------------------------------------------------------------ render
def scene_at(t):
    for i, (name, s, e) in enumerate(SCENES):
        if s <= t < e:
            return i, name, s, e
    return len(SCENES) - 1, SCENES[-1][0], SCENES[-1][1], SCENES[-1][2]


SCENE_FN = {
    "hook": scene_hook,
    "problem": scene_problem,
    "reveal": scene_reveal,
    "noirson": scene_noirson,
    "ascension": scene_ascension,
    "horizon": scene_horizon,
    "method": scene_method,
    "cta": scene_cta,
}

_BG = None


def render_frame(fi, bg=None):
    global _BG
    if bg is None:
        if _BG is None:
            _BG = build_bg()
        bg = _BG
    t = fi / FPS
    idx, name, s, e = scene_at(t)
    lt, dur = t - s, e - s

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    SCENE_FN[name](d, layer, lt, dur)

    # enter / exit fade
    fade_in = eo(prog(lt, 0.0, 0.18))
    fade_out = 1.0 - 0.45 * eo(prog(lt, dur - 0.20, 0.20))
    layer = with_alpha(layer, fade_in * fade_out)

    frame = bg.copy()
    dust(frame, t)
    frame.alpha_composite(layer)
    chrome(frame, t, name)
    transition_flash(frame, t, s)
    return frame.convert("RGB")


def build_audio():
    starts = [s for (_, s, _) in SCENES]
    sfx = []
    for i, s in enumerate(starts):
        sfx.append(("whoosh", max(0.0, s - 0.05), 0.10 if i else 0.06, 0))
    add = [
        ("pop", 1.35, 0.10, 0), ("pop", 2.6, 0.07, 0),
        ("pop", 6.2, 0.08, 0), ("pop", 10.9, 0.09, 0),
        ("pop", 11.6, 0.11, 0), ("tick", 12.4, 0.05, 0), ("tick", 12.6, 0.05, 0),
        ("pop", 19.6, 0.11, 0), ("pop", 26.8, 0.11, 0),
        ("pop", 31.3, 0.09, 0), ("pop", 31.7, 0.09, 0),
        ("tick", 37.0, 0.05, 0), ("tick", 37.2, 0.05, 0), ("tick", 37.4, 0.05, 0),
        ("tick", 37.6, 0.05, 0), ("tick", 37.8, 0.05, 0), ("tick", 38.0, 0.05, 0),
        ("ding", 44.6, 0.14, 0), ("ding", 45.4, 0.09, 0),
    ]
    sfx += add
    print("Mixing score + 8 VO clips ...")
    raw = "/tmp/_leger_mix_raw.wav"
    build_score(TOTAL, VO, starts, sfx, raw)
    # social-ready loudness: +6 dB then true-peak limiting
    from imageio_ffmpeg import get_ffmpeg_exe
    subprocess.run([get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", raw,
                    "-af", "volume=6.0dB,alimiter=limit=0.93:level=disabled",
                    "-ar", str(SR), MIX], check=True)
    print("Audio ->", MIX)


def preview(times, out_path):
    bg = build_bg()
    thumbs = []
    for t in times:
        fi = int(t * FPS)
        im = render_frame(fi, bg)
        thumbs.append(im.resize((432, 768), Image.LANCZOS))
    cols, rows = 4, 2
    pad = 10
    sheet = Image.new("RGB", (cols * (432 + pad) + pad, rows * (768 + pad) + pad), (18, 16, 26))
    from PIL import ImageDraw as _ID
    sd = _ID.Draw(sheet)
    for i, im in enumerate(thumbs):
        x = pad + (i % cols) * (432 + pad)
        y = pad + (i // cols) * (768 + pad)
        sheet.paste(im, (x, y))
        t = times[i]
        sd.rectangle([x, y, x + 148, y + 30], fill=(0, 0, 0))
        sd.text((x + 8, y + 6), f"t={t:05.2f}s", font=F("isb", 19), fill=(255, 255, 255))
    sheet.save(out_path, quality=90)
    print("Saved preview contact sheet to", out_path)


def render_full():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    nframes = int(round(TOTAL * FPS))
    cmd = [ff, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-vcodec", "rawvideo", "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
           "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", TMP_VIDEO]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    bg = build_bg()
    for fi in range(nframes):
        proc.stdin.write(render_frame(fi, bg).tobytes())
        if fi % 180 == 0:
            print(f"  rendered {fi}/{nframes} ({fi / nframes * 100:.1f}%)", flush=True)
    proc.stdin.close()
    proc.wait()

    subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP_VIDEO, "-i", MIX,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("Rendered", OUT, f"({os.path.getsize(OUT) / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default=None)
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    if args.preview:
        mids = [(s + e) / 2 for (_, s, e) in SCENES]
        preview(mids, args.preview)
        return
    if not args.no_audio:
        build_audio()
    render_full()


if __name__ == "__main__":
    main()
