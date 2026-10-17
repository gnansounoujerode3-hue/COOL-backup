#!/usr/bin/env python3
"""
Dynamic 16:9 YouTube Edit with Rose-Pink Accent (`#EC4899`) for:
  `Être Intelligente En 2026 Te Dessert(1080P_HD).mp4` (1920x1080 @ 30fps, 321.37s, 9641 frames)

Applies:
- `MOTION-DESIGN.md` & `.claude/skills/animation-design-rules/` (10 Animation Design Laws)
- Strict maximum of 2 lines of subtitle at any instant
- Signature Rose-Pink (`#EC4899` / `#F472B6` / `#9D174D`) visual identity matching the speaker's pink crochet heart mic:
  1. Dynamic YouTube Camera Cadence (Punch-ins 1.12x/1.16x, slow Ken Burns push-ins, Rule-of-Thirds lateral reframing when side-cards appear)
  2. 5 Full-Screen Rose-Cream (`#FAF7F9`) Sunlit Window-Gobo Motion-Design Cutaways (3D Extruded Rose Typography, Blueprint Grid, Flowchart, Balance Graph)
  3. 20 Floating 3D Glassmorphic Side-Cards & Split-Screen Comparisons in the 16:9 negative space
  4. 7 Animated Top-Left Chapter Pills + Continuous Segmented Rose-Pink YouTube Progress Bar
  5. Curated 1-to-2 Line French Subtitles with Rose-Pink Highlight Bars, Brush Underlines, and Calligraphic Script accents
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
import wave
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = "/home/user/COOL-backup"
PROJECT_DIR = f"{REPO_ROOT}/etre-intelligente-2026"
FILM_DIR = f"{PROJECT_DIR}/film"
CLEAN_MP4 = f"{FILM_DIR}/etre-intelligente-en-2026-sans-sous-titres-1080p.mp4"
OUT_MP4 = f"{FILM_DIR}/etre-intelligente-en-2026-youtube-rose-1080p.mp4"
SEGMENTS_JSON = "/tmp/yt_inspect/segments.json"

W, H = 1920, 1080
FPS = 30.0

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"

# Signature Rose-Pink Palette (RGB)
C_ROSE = (236, 72, 153)         # #EC4899 Primary Rose-Pink accent
C_ROSE_LIGHT = (244, 114, 182)  # #F472B6 Soft Rose Quartz
C_ROSE_BLUSH = (252, 231, 243)  # #FCE7F3 Pastel Blush pill background
C_ROSE_DEEP = (157, 23, 77)     # #9D174D Deep Berry 3D bevel / shadow
C_PAPER = (250, 246, 248)       # #FAF6F8 Sunlit Rose-Cream cutaway canvas
C_CHARCOAL = (24, 20, 26)       # #18141A Crisp dark ink
C_MUTED = (96, 84, 100)         # Secondary editorial ink

_FONT_CACHE = {}
_SPRITE_CACHE = {}
_STATIC_CACHE = {}


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def ease_out_expo(t: float) -> float:
    t = clamp(t)
    return 1.0 if t >= 1.0 else 1.0 - math.pow(2.0, -10.0 * t)


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t)
    return 4.0 * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 3.0) / 2.0


def get_font(path: str, size: int):
    size = max(12, int(round(size)))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def blend_rgba_onto_bgr(bgr: np.ndarray, sprite_rgba: np.ndarray, x0: int, y0: int, opacity: float = 1.0):
    """Ultra-fast in-place NumPy alpha-blend of an RGBA sprite onto a BGR frame at (x0, y0)."""
    if opacity <= 0.01:
        return
    sh, sw = sprite_rgba.shape[:2]
    # Clip to frame bounds
    fx0 = max(0, x0)
    fy0 = max(0, y0)
    fx1 = min(W, x0 + sw)
    fy1 = min(H, y0 + sh)
    if fx1 <= fx0 or fy1 <= fy0:
        return

    sx0 = fx0 - x0
    sy0 = fy0 - y0
    sx1 = sx0 + (fx1 - fx0)
    sy1 = sy0 + (fy1 - fy0)

    sub_sp = sprite_rgba[sy0:sy1, sx0:sx1]
    a = sub_sp[:, :, 3:4].astype(np.uint16)
    if opacity < 0.999:
        a = (a * int(round(opacity * 256))) >> 8
    if not np.any(a):
        return

    dst = bgr[fy0:fy1, fx0:fx1].astype(np.uint16)
    # Convert sprite RGB -> BGR
    src_bgr = sub_sp[:, :, [2, 1, 0]].astype(np.uint16)
    inv_a = 255 - a
    bgr[fy0:fy1, fx0:fx1] = ((dst * inv_a + src_bgr * a) // 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# 1. Seven YouTube Chapters & Top-Left Chapter Pill Sprites
# ---------------------------------------------------------------------------
CHAPTERS = [
    (0.00, 16.34, "01", "LE PIÈGE D'ÊTRE « INTELLIGENTE »"),
    (16.34, 51.60, "02", "LES 3 CAUSES CACHÉES"),
    (51.60, 75.62, "03", "LA SPIRALE DU PERFECTIONNISME"),
    (75.62, 119.98, "04", "POURQUOI L'AUTHENTICITÉ PERCE"),
    (119.98, 184.46, "05", "EXPERTISE FROIDE VS PASSION"),
    (184.46, 270.98, "06", "INTELLIGENCE ÉMOTIONNELLE & SPONTANÉITÉ"),
    (270.98, 321.37, "07", "ACCEPTATION DE SOI & CONCLUSION"),
]


def get_chapter_pill_sprite(ch_num: str, ch_title: str) -> np.ndarray:
    key = ("ch_pill", ch_num, ch_title)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]

    f_num = get_font(JAKARTA_EBOLD, 22)
    f_txt = get_font(JAKARTA_BOLD, 22)
    tmp = Image.new("RGBA", (10, 10))
    d_tmp = ImageDraw.Draw(tmp)
    bb = d_tmp.textbbox((0, 0), ch_title, font=f_txt)
    tw = bb[2] - bb[0]

    pw = 115 + tw + 36
    ph = 58
    im = Image.new("RGBA", (pw + 24, ph + 24), (0, 0, 0, 0))
    # Soft drop shadow
    sh = Image.new("RGBA", (pw + 24, ph + 24), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([12, 14, 12 + pw, 14 + ph], radius=29, fill=(24, 12, 20, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=6))
    im.alpha_composite(sh)

    d = ImageDraw.Draw(im)
    # Frosted dark-rose glass pill
    d.rounded_rectangle([8, 8, 8 + pw, 8 + ph], radius=29, fill=(24, 18, 24, 225), outline=(*C_ROSE_LIGHT, 185), width=2)
    # Rose-Pink badge on left
    d.rounded_rectangle([14, 14, 98, 8 + ph - 6], radius=23, fill=(*C_ROSE, 255))
    d.text((30, 23), f"CH.{ch_num}", font=f_num, fill=(255, 255, 255, 255))
    d.text((114, 23), ch_title, font=f_txt, fill=(252, 244, 248, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# 2. Twenty-Two Floating 3D Side-Cards & Split-Screen Visual Callouts
# ---------------------------------------------------------------------------
SIDE_CARDS = [
    # (t_start, t_end, side, badge, title, subtitle, accent_stat)
    (10.10, 16.00, "right", "PIÈGE #1", "PARAÎTRE « COOL »", "Épuise ton énergie chaque matin", "100% PRESSION"),
    (18.00, 25.20, "left", "CHAQUE MATIN", "DEVOIR PERFORMER", "Prouver sa valeur aux autres", "STOP"),
    (25.48, 29.80, "right", "CAUSE 01 / 03", "MANQUE DE CONFIANCE", "Douter de sa propre valeur", "01"),
    (29.88, 38.00, "right", "CAUSE 02 / 03", "CHERCHER LA VALIDATION", "Vouloir prouver qu'on est géniale", "02"),
    (38.20, 48.80, "right", "CAUSE 03 / 03", "LA PEUR CACHÉE", "Bloque ta vraie voix intérieure", "03"),
    (54.80, 63.50, "left", "ILLUSION", "TOUT VOULOIR CARRÉ", "Le piège du perfectionnisme", "100% RIGIDE"),
    (77.56, 90.00, "right", "RÉSEAUX SOCIAUX", "ÊTRE SOI-MÊME", "Pas besoin d'un concept parfait", "AUTHENTICITÉ"),
    (90.22, 101.50, "left", "VISIBILITÉ", "PERCER SANS CALCULER", "La spontanéité attire l'audience", "IMPACT"),
    (103.82, 113.80, "right", "SUR-CONTRÔLE", "TOUT CALCULER", "« Il faut que je parle comme ça… »", "BLOCAGE"),
    (122.10, 134.00, "left", "MON DÉCLIC", "1 AN D'INTROSPECTION", "Travail profond sur l'identité", "EXPÉRIENCE"),
    (136.10, 148.80, "right", "ERREUR CLASSIQUE", "MONTRER SON EXPERTISE", "Vouloir que chaque réel soit lisse", "TROP FROID"),
    (158.58, 173.50, "left", "LE VRAI CHOIX", "PASSION VS RIGIDITÉ", "Partager son vécu avec le cœur", "CONNEXION"),
    (175.30, 184.40, "right", "AUDIENCE", "PARLER AVEC SON VÉCU", "Les gens choisissent le vrai", "VÉRITÉ"),
    (189.38, 201.50, "left", "RÈGLE D'OR", "NE PAS SE PERDRE", "Arrête de vouloir plaire à tous", "LIBERTÉ"),
    (212.30, 224.50, "right", "EN 2026", "LIBÈRE TA PAROLE", "Dis ce que tu ressens vraiment", "VOIX LIBRE"),
    (231.78, 244.50, "left", "MÉTHODE 1", "SCRIPT RIGIDE", "Tout calculer mot par mot", "2 HEURES"),
    (245.22, 258.50, "right", "MÉTHODE 2", "FACE-CAM SPONTANÉ", "1 à 5 min avec le cœur", "5 MINUTES"),
    (259.10, 270.50, "left", "ASTUCE FACE-CAM", "COMME À TA POTE", "Pas besoin de mots complexes", "NATUREL"),
    (272.18, 285.00, "right", "INTROSPECTION", "ENLÈVE LE MASQUE", "Comprends d'où vient ta peur", "PROFONDEUR"),
    (297.78, 312.00, "left", "SINGULARITÉ", "ASSUME QUI TU ES", "Atypique, unique & authentique", "100% TOI"),
    (313.18, 321.20, "right", "YOUTUBE 2026", "ABONNE-TOI !", "On se retrouve très vite !", "PROCHAINE VIDÉO"),
]


def get_side_card_sprite(badge: str, title: str, subtitle: str, stat: str) -> np.ndarray:
    key = ("side_card", badge, title, subtitle, stat)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]

    cw, ch = 470, 235
    im = Image.new("RGBA", (cw + 36, ch + 36), (0, 0, 0, 0))

    # 45-degree soft Rose-Berry drop shadow
    sh = Image.new("RGBA", (cw + 36, ch + 36), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([20, 24, 20 + cw, 24 + ch], radius=26, fill=(38, 10, 24, 125))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=10))
    im.alpha_composite(sh)

    d = ImageDraw.Draw(im)
    # Editorial cream-blush card with rose border
    d.rounded_rectangle([14, 14, 14 + cw, 14 + ch], radius=26, fill=(252, 248, 250, 246), outline=(*C_ROSE, 220), width=3)
    # Left vertical Rose-Pink accent bar
    d.rounded_rectangle([14, 14, 28, 14 + ch], radius=8, fill=(*C_ROSE, 255))

    # Top Rose pill badge
    f_badge = get_font(JAKARTA_EBOLD, 19)
    d.rounded_rectangle([44, 32, 225, 68], radius=18, fill=(*C_ROSE_BLUSH, 255), outline=(*C_ROSE_LIGHT, 200), width=1)
    d.text((60, 38), badge, font=f_badge, fill=(*C_ROSE_DEEP, 255))

    # Top-right stat pill
    f_stat = get_font(MONO_MED, 18)
    bb_s = d.textbbox((0, 0), stat, font=f_stat)
    sw_t = bb_s[2] - bb_s[0]
    d.rounded_rectangle([14 + cw - sw_t - 46, 32, 14 + cw - 20, 68], radius=18, fill=(*C_ROSE, 255))
    d.text((14 + cw - sw_t - 33, 39), stat, font=f_stat, fill=(255, 255, 255, 255))

    # Main Title
    f_title = get_font(JAKARTA_EBOLD, 31)
    d.text((44, 86), title, font=f_title, fill=(*C_CHARCOAL, 255))

    # Rose brush divider line
    d.rounded_rectangle([44, 134, 185, 140], radius=3, fill=(*C_ROSE_LIGHT, 255))

    # Subtitle
    f_sub = get_font(INTER_MED, 22)
    d.text((44, 154), subtitle, font=f_sub, fill=(*C_MUTED, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# 3. Five Full-Screen Motion-Design Cutaways (Sunlit Rose-Paper `#FAF6F8`)
# ---------------------------------------------------------------------------
CUTAWAY_WINDOWS = [
    (5.18, 9.80, 1),
    (64.20, 73.60, 2),
    (114.54, 119.98, 3),
    (202.38, 211.50, 4),
    (290.22, 296.50, 5),
]


def get_rose_gobo_paper_base() -> Image.Image:
    if "rose_paper_base" in _STATIC_CACHE:
        return _STATIC_CACHE["rose_paper_base"]

    xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]

    # Diagonal Venetian window-blind gobo bands
    diag = xx * 0.72 + yy * 1.15
    blinds = 0.5 + 0.5 * np.cos(2.0 * np.pi * (diag * 4.2 - 0.15))
    pane_gap = np.exp(-((xx - 0.28) ** 2) / 0.008)
    shadow = np.clip((1.0 - blinds) * (1.0 - 0.65 * pane_gap), 0.0, 1.0)
    vig = 0.08 * ((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    shade = np.clip(1.0 - 0.12 * shadow - vig, 0.84, 1.0)

    rng = np.random.default_rng(2026)
    grain = rng.normal(0.0, 1.2, (H, W)).astype(np.float32)

    r = np.clip(C_PAPER[0] * shade + grain, 220, 255).astype(np.uint8)
    g = np.clip(C_PAPER[1] * shade - 2.0 * shadow + grain, 212, 253).astype(np.uint8)
    b = np.clip(C_PAPER[2] * shade + grain, 218, 255).astype(np.uint8)

    im = Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")
    # Subtle architectural square grid in center
    d = ImageDraw.Draw(im, "RGBA")
    for gx in range(260, 1661, 56):
        d.line([(gx, 160), (gx, 920)], fill=(236, 72, 153, 24), width=1)
    for gy in range(160, 921, 56):
        d.line([(260, gy), (1660, gy)], fill=(236, 72, 153, 24), width=1)

    _STATIC_CACHE["rose_paper_base"] = im
    return im


def render_cutaway_frame(t: float, cutaway_id: int) -> np.ndarray:
    base = get_rose_gobo_paper_base().copy().convert("RGBA")
    d = ImageDraw.Draw(base)

    if cutaway_id == 1:
        # Cutaway 1 (5.18s - 9.80s): "ÇA TE DESSERT ABSOLUMENT PARTOUT" (3 Rose Cards)
        age = t - 5.18
        f_top = get_font(INTER_MED, 34)
        f_hero = get_font(JAKARTA_EBOLD, 68)
        d.text((W // 2 - 260, 145), "Vouloir paraître intelligente", font=f_top, fill=(*C_MUTED, 255))
        # Rose highlight bar under hero title
        d.rounded_rectangle([W // 2 - 440, 238, W // 2 + 440, 292], radius=10, fill=(*C_ROSE, 255))
        d.text((W // 2 - 415, 205), "TE DESSERT PARTOUT", font=f_hero, fill=(*C_CHARCOAL, 255))

        cards = [
            ("01", "DANS LA VIE", "Pression constante au quotidien", 0.05),
            ("02", "EN BUSINESS", "Bloque ton authenticité & tes ventes", 0.95),
            ("03", "EN RELATIONS", "Empêche les vraies connexions", 2.00),
        ]
        for idx, (num, title, sub, delay) in enumerate(cards):
            p = ease_out_expo((age - delay) / 0.42)
            if p <= 0.01:
                continue
            cx = 220 + idx * 510
            cy = int(390 + 36 * (1.0 - p))
            cw, ch = 460, 390
            d.rounded_rectangle([cx + 10, cy + 16, cx + cw + 10, cy + ch + 16], radius=28, fill=(157, 23, 77, int(45 * p)))
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=28, fill=(255, 255, 255, int(248 * p)), outline=(*C_ROSE, int(235 * p)), width=3)
            d.rounded_rectangle([cx + 36, cy + 36, cx + 126, cy + 92], radius=22, fill=(*C_ROSE, int(255 * p)))
            d.text((cx + 58, cy + 46), num, font=get_font(JAKARTA_EBOLD, 30), fill=(255, 255, 255, int(255 * p)))
            d.text((cx + 36, cy + 135), title, font=get_font(JAKARTA_EBOLD, 38), fill=(*C_CHARCOAL, int(255 * p)))
            d.rounded_rectangle([cx + 36, cy + 198, cx + 190, cy + 206], radius=4, fill=(*C_ROSE_LIGHT, int(255 * p)))
            d.text((cx + 36, cy + 230), sub, font=get_font(INTER_MED, 24), fill=(*C_MUTED, int(255 * p)))

    elif cutaway_id == 2:
        # Cutaway 2 (64.20s - 73.60s): "LA SPIRALE DU PERFECTIONNISME" (4-Node Domino Chain)
        age = t - 64.20
        d.text((W // 2 - 290, 155), "Le piège invisible du perfectionnisme", font=get_font(GREAT_VIBES, 64), fill=(*C_ROSE_DEEP, 255))
        d.text((W // 2 - 430, 230), "LA RÉACTION EN CHAÎNE", font=get_font(JAKARTA_EBOLD, 64), fill=(*C_CHARCOAL, 255))

        steps = [
            ("01", "PERFECTION", "Tout vouloir carré", 0.0),
            ("02", "CONTRÔLE", "Zéro lâcher-prise", 1.2),
            ("03", "RÉSISTANCE", "Tension intérieure", 2.8),
            ("04", "PEUR & DOUTE", "Insécurité constante", 4.6),
        ]
        for idx, (num, title, sub, delay) in enumerate(steps):
            p = ease_out_expo((age - delay) / 0.45)
            if p <= 0.01:
                continue
            cx = 130 + idx * 425
            cy = int(420 + 30 * (1.0 - p))
            cw, ch = 375, 320
            is_last = idx == 3
            bg_c = (*C_ROSE, int(255 * p)) if is_last else (255, 255, 255, int(250 * p))
            txt_c = (255, 255, 255, int(255 * p)) if is_last else (*C_CHARCOAL, int(255 * p))
            sub_c = (252, 231, 243, int(255 * p)) if is_last else (*C_MUTED, int(255 * p))
            d.rounded_rectangle([cx + 8, cy + 14, cx + cw + 8, cy + ch + 14], radius=26, fill=(157, 23, 77, int(55 * p)))
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=26, fill=bg_c, outline=(*C_ROSE, int(255 * p)), width=3)
            d.text((cx + 32, cy + 36), f"ÉTAPE {num}", font=get_font(MONO_MED, 22), fill=sub_c)
            d.text((cx + 32, cy + 105), title, font=get_font(JAKARTA_EBOLD, 36), fill=txt_c)
            d.text((cx + 32, cy + 175), sub, font=get_font(INTER_MED, 24), fill=sub_c)
            if idx < 3:
                ax = cx + cw + 12
                ay = cy + ch // 2
                d.line([(ax, ay), (ax + 32, ay)], fill=(*C_ROSE, int(255 * p)), width=6)

    elif cutaway_id == 3:
        # Cutaway 3 (114.54s - 119.98s): "Plus tu calcules, moins tu es toi"
        age = t - 114.54
        p1 = ease_out_expo(age / 0.40)
        p2 = ease_out_expo((age - 1.2) / 0.45)
        d.text((W // 2 - 240, int(230 + 20 * (1.0 - p1))), "La loi de l'authenticité", font=get_font(GREAT_VIBES, 76), fill=(*C_ROSE_DEEP, int(255 * p1)))
        # Left card: + TU CALCULES
        d.rounded_rectangle([260, 360, 910, 740], radius=28, fill=(255, 255, 255, int(248 * p1)), outline=(*C_ROSE_LIGHT, int(220 * p1)), width=3)
        d.text((310, 410), "QUAND TU SUR-CALCULES", font=get_font(MONO_MED, 24), fill=(*C_MUTED, int(255 * p1)))
        d.text((310, 475), "+ DE CALCUL ↑", font=get_font(JAKARTA_EBOLD, 56), fill=(*C_CHARCOAL, int(255 * p1)))
        d.text((310, 575), "Chaque mot, chaque geste est forcé", font=get_font(INTER_MED, 26), fill=(*C_MUTED, int(255 * p1)))

        if p2 > 0.01:
            d.rounded_rectangle([1010, int(360 + 25 * (1.0 - p2)), 1660, int(740 + 25 * (1.0 - p2))], radius=28, fill=(*C_ROSE, int(255 * p2)))
            d.text((1060, int(410 + 25 * (1.0 - p2))), "LE RÉSULTAT DIRECT", font=get_font(MONO_MED, 24), fill=(252, 231, 243, int(255 * p2)))
            d.text((1060, int(475 + 25 * (1.0 - p2))), "- D'AUTHENTICITÉ ↓", font=get_font(JAKARTA_EBOLD, 52), fill=(255, 255, 255, int(255 * p2)))
            d.text((1060, int(575 + 25 * (1.0 - p2))), "Tu n'as même plus l'impression d'être toi.", font=get_font(INTER_MED, 25), fill=(255, 255, 255, int(255 * p2)))

    elif cutaway_id == 4:
        # Cutaway 4 (202.38s - 211.50s): 3D Extruded Rose-Berry "INTELLIGENCE ÉMOTIONNELLE"
        age = t - 202.38
        p = ease_out_expo(age / 0.42)
        d.text((W // 2 - 280, 210), "En 2026, la vraie intelligence est", font=get_font(INTER_MED, 38), fill=(*C_CHARCOAL, int(255 * p)))

        f_hero = get_font(JAKARTA_EBOLD, 108)
        hero_txt = "ÉMOTIONNELLE"
        bb = d.textbbox((0, 0), hero_txt, font=f_hero)
        tw = bb[2] - bb[0]
        hx = (W - tw) // 2
        hy = int(330 + 24 * (1.0 - p))
        # 3D Berry-Rose Extrusion
        for depth in range(10, 0, -1):
            d.text((hx + depth, hy + int(depth * 1.2)), hero_txt, font=f_hero, fill=(*C_ROSE_DEEP, int(255 * p)))
        d.text((hx, hy), hero_txt, font=f_hero, fill=(*C_ROSE, int(255 * p)))

        pills = ["01 • EMPATHIE", "02 • PERCEPTION FINE", "03 • PAROLE LIBÉRÉE"]
        for i, pl in enumerate(pills):
            pp = ease_out_expo((age - 1.2 - i * 0.7) / 0.40)
            if pp <= 0.01:
                continue
            px = 290 + i * 465
            py = int(575 + 20 * (1.0 - pp))
            d.rounded_rectangle([px, py, px + 425, py + 95], radius=24, fill=(255, 255, 255, int(250 * pp)), outline=(*C_ROSE, int(240 * pp)), width=3)
            d.rounded_rectangle([px + 20, py + 34, px + 34, py + 62], radius=7, fill=(*C_ROSE, int(255 * pp)))
            d.text((px + 50, py + 30), pl, font=get_font(JAKARTA_BOLD, 27), fill=(*C_CHARCOAL, int(255 * pp)))

    else:
        # Cutaway 5 (290.22s - 296.50s): "ACCEPTE LA PERSONNE QUE TU ES"
        age = t - 290.22
        p = ease_out_expo(age / 0.42)
        d.text((W // 2 - 235, int(260 + 20 * (1.0 - p))), "C'est une question", font=get_font(GREAT_VIBES, 86), fill=(*C_CHARCOAL, int(255 * p)))
        # Half-height Rose-Pink bar under "D'ACCEPTATION"
        f_big = get_font(JAKARTA_EBOLD, 92)
        txt = "D'ACCEPTATION"
        bb = d.textbbox((0, 0), txt, font=f_big)
        tw = bb[2] - bb[0]
        tx = (W - tw) // 2
        ty = 400
        d.rounded_rectangle([tx - 24, ty + 42, tx + tw + 24, ty + 108], radius=10, fill=(*C_ROSE, int(255 * p)))
        d.text((tx, ty), txt, font=f_big, fill=(*C_CHARCOAL, int(255 * p)))
        d.text((W // 2 - 295, 555), "Accepte pleinement la personne que tu es.", font=get_font(INTER_MED, 34), fill=(*C_MUTED, int(255 * p)))

    return cv2.cvtColor(np.array(base.convert("RGB"), dtype=np.uint8), cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# 4. French Transcript Polisher & Strict 2-Line Subtitle Sprite Generator
# ---------------------------------------------------------------------------
# Clean grammatical French overrides for Whisper's phonetic approximations
CLEAN_FRENCH_OVERRIDES = {
    0: ("Vouloir paraître intelligente,", "vouloir paraître cool.", "intelligente,"),
    1: ("C'est exactement ça", "qui te dessert dans la vie,", "te dessert"),
    2: ("qui te dessert", "dans ton business,", "business,"),
    3: ("qui te dessert", "dans tes relations,", "relations,"),
    4: ("qui te dessert", "absolument partout.", "partout."),
    5: ("Pourquoi ? Parce que dès que", "tu veux paraître intelligente,", "Pourquoi ?"),
    6: ("et ça revient au même", "que vouloir paraître cool,", "paraître cool,"),
    7: ("c'est te lever", "chaque matin,", "chaque matin,"),
    8: ("avec l'impression qu'aujourd'hui", "tu dois encore performer.", "performer."),
    9: ("Aujourd'hui tu dois encore", "prouver aux autres,", "prouver"),
    10: ("et sans même", "t'en rendre compte,", "rendre compte,"),
    11: ("1° Tu n'as pas confiance", "en qui tu es vraiment.", "pas confiance"),
    12: ("2° Tu n'acceptes pas", "la personne que tu es,", "n'acceptes pas"),
    13: ("parce que tu veux toujours", "montrer aux autres,", "aux autres,"),
    14: ("« Regardez, je dois prouver", "que je suis géniale, »", "géniale, »"),
    15: ("que je suis quelqu'un", "d'intelligent, etc.", "d'intelligent,"),
    16: ("3° Il y a une peur", "que tu caches,", "une peur"),
    17: ("au plus profond", "de toi-même,", "profond"),
    18: ("qui t'empêche de parler", "de ce qui t'anime vraiment,", "t'anime"),
    19: ("et d'être enfin", "qui tu as envie d'être,", "envie d'être,"),
    20: ("au lieu de te lever", "chaque matin en te disant :", "chaque matin"),
    21: ("« Que vont penser", "les gens ? »", "les gens ? »"),
    22: ("« Je vais dire ça", "pour paraître intelligente, »", "intelligente, »"),
    23: ("alors que même si", "tu es intelligente,", "intelligente,"),
    24: ("tu peux être", "très intelligente,", "intelligente,"),
    25: ("mais le piège, c'est de vouloir", "que tout soit carré,", "soit carré,"),
    26: ("tu veux que les choses", "soient parfaites,", "parfaites,"),
    27: ("et à force de vouloir", "être perfectionniste,", "perfectionniste,"),
    28: ("tu cherches à garder", "le contrôle absolu,", "contrôle"),
    29: ("et qui dit contrôle,", "dit forcément résistance,", "résistance,"),
    30: ("et qui dit résistance,", "dit encore plus de peur,", "plus de peur,"),
    31: ("et encore plus", "d'insécurité.", "d'insécurité."),
    32: ("Ce que j'ai remarqué,", "et que tu as remarqué aussi,", "remarqué"),
    33: ("c'est qu'à travers", "les personnes sur les réseaux,", "les réseaux,"),
    34: ("qui se permettent simplement", "d'être elles-mêmes,", "elles-mêmes,"),
    35: ("de poster des choses", "sans tout calculer,", "sans calculer,"),
    36: ("ce sont des personnes", "qui vivent vraiment,", "vivent"),
    37: ("des personnes qui restent", "100% elles-mêmes,", "elles-mêmes,"),
    38: ("qui n'ont pas besoin", "d'un concept hyper original,", "original,"),
    39: ("ni de jouer un rôle", "devant les autres,", "un rôle"),
    40: ("et qui pourtant", "finissent par réussir,", "réussir,"),
    41: ("et par percer", "avec une vraie visibilité,", "visibilité,"),
    42: ("parce qu'elles ne se lèvent pas", "chaque matin,", "chaque matin,"),
    43: ("en se disant : « Il faut", "que je paraisse intelligente, »", "intelligente, »"),
    44: ("« Il faut absolument", "que je parle de ce sujet, »", "ce sujet, »"),
    45: ("« Il faut que j'en parle", "de cette manière-là, »", "manière-là, »"),
    46: ("« Il faut que je commence", "la vidéo comme ça, »", "comme ça, »"),
    47: ("« et que je la termine", "exactement comme ça, »", "comme ça, »"),
    48: ("en calculant", "absolument tout.", "tout."),
    49: ("Parce que plus", "tu calcules quelque chose,", "tu calcules"),
    50: ("et moins en réalité,", "tu as l'impression d'être toi.", "d'être toi."),
    51: ("Pour te donner", "mon propre exemple,", "exemple,"),
    52: ("quand je me suis lancée", "dans l'entrepreneuriat,", "l'entrepreneuriat,"),
    53: ("ça a été un vrai déclic", "pour moi,", "vrai déclic"),
    54: ("c'est à ce moment-là", "que tout a changé,", "a changé,"),
    55: ("que j'ai compris", "énormément de choses,", "compris"),
    56: ("et que j'ai travaillé", "un an en profondeur,", "profondeur,"),
    57: ("sur mon identité", "et sur qui j'étais,", "identité"),
    58: ("j'ai compris", "beaucoup de choses sur moi,", "sur moi,"),
    59: ("mais quand j'ai voulu", "me lancer sur les réseaux,", "les réseaux,"),
    60: ("je voulais que tout", "soit absolument parfait,", "parfait,"),
    61: ("je voulais que mes réels", "plaisent à tout le monde,", "tout le monde,"),
    62: ("je voulais que mes vidéos", "soient le reflet parfait,", "reflet parfait,"),
    63: ("de mon expertise", "et de mon intelligence,", "intelligence,"),
    64: ("mais les gens", "n'attendent pas ça.", "pas ça."),
    65: ("Les gens n'aiment pas", "quand c'est trop lisse,", "trop lisse,"),
    66: ("« Je connais mon sujet »,", "c'est bien de le maîtriser,", "maîtriser,"),
    67: ("mais il y a", "une vraie différence,", "différence,"),
    68: ("entre parler simplement", "avec le cœur,", "avec le cœur,"),
    69: ("parce que tu reflètes", "ta vraie passion,", "passion,"),
    70: ("parce que tu aimes", "transmettre et échanger,", "transmettre"),
    71: ("pour partager", "tes connaissances,", "partager"),
    72: ("et de l'autre côté,", "être hyper carrée,", "hyper carrée,"),
    73: ("restreinte et figée", "devant la caméra,", "figée"),
    74: ("où tu es moins toi,", "et tu ne t'exprimes pas,", "moins toi,"),
    75: ("sans jamais montrer", "ta vraie personnalité.", "personnalité."),
    76: ("Et je pense", "qu'entre les deux,", "les deux,"),
    77: ("tu vas très vite choisir", "la personne authentique,", "authentique,"),
    78: ("qui utilise des mots simples", "et sincères,", "sincères,"),
    79: ("et qui partage", "sa propre expérience,", "expérience,"),
    80: ("à travers ce qu'elle", "a réellement compris.", "compris."),
    81: ("Et c'est ce que j'ai", "très vite compris,", "compris,"),
    82: ("en me lançant", "sur les réseaux sociaux :", "réseaux sociaux :"),
    83: ("tu n'as pas besoin", "de paraître intelligente,", "intelligente,"),
    84: ("tu n'as pas besoin", "de paraître cool,", "cool,"),
    85: ("tu n'as pas besoin", "de plaire à tout le monde,", "tout le monde,"),
    86: ("parce qu'au final,", "tu te perds toi-même.", "toi-même."),
    87: ("Et l'objectif,", "ce n'est pas de te perdre,", "te perdre,"),
    88: ("au point de ne même plus", "te reconnaître.", "reconnaître."),
    89: ("L'intelligence se traduit", "par tellement de choses :", "L'intelligence"),
    90: ("elle se traduit par", "l'intelligence émotionnelle,", "émotionnelle,"),
    91: ("ton empathie et ce que", "tu ressens profondément,", "empathie"),
    92: ("ta capacité à percevoir", "ce que d'autres ne voient pas,", "percevoir"),
    93: ("c'est bien plus riche", "qu'un simple discours,", "plus riche"),
    94: ("et au-delà de toutes", "tes connaissances,", "connaissances,"),
    95: ("ce qu'on veut,", "c'est que tu viennes telle que tu es,", "telle que tu es,"),
    96: ("et que tu libères", "vraiment ta parole,", "ta parole,"),
    97: ("que tu exprimes", "tout simplement,", "simplement,"),
    98: ("ce que tu as sur le cœur", "avec authenticité.", "authenticité."),
    99: ("Je préfère mille fois", "écouter une personne,", "mille fois"),
    100: ("qui explique les choses", "avec simplicité,", "simplicité,"),
    101: ("dès qu'elle a une idée", "qui lui traverse l'esprit :", "une idée"),
    102: ("« Je vais faire une vidéo,", "je vais me filmer,", "me filmer,"),
    103: ("face caméra,", "et je vais en parler ! »", "en parler ! »"),
    104: ("plutôt qu'une personne", "qui a une idée,", "une idée,"),
    105: ("comme je le faisais", "auparavant,", "auparavant,"),
    106: ("qui va tout calculer", "avant même de tourner,", "calculer"),
    107: ("écrire un script", "mot par mot,", "un script"),
    108: ("en se disant : « Il faut", "absolument dire ça, »", "dire ça, »"),
    109: ("« Il faut absolument", "ajouter cette phrase, »", "cette phrase, »"),
    110: ("« Il ne faut surtout pas", "que j'oublie ce point… »", "ce point… »"),
    111: ("Et au final,", "ce qui se passe,", "au final,"),
    112: ("c'est qu'au lieu de tourner", "en quelques minutes,", "quelques minutes,"),
    113: ("je prenais une heure", "à deux heures,", "deux heures,"),
    114: ("juste pour enregistrer", "une seule vidéo,", "une seule vidéo,"),
    115: ("alors qu'aujourd'hui,", "je me dis simplement :", "simplement :"),
    116: ("« Je vais parler avec le cœur,", "même si ça dure 5 minutes ! »", "avec le cœur,"),
    117: ("Parfois ça dure 1 minute,", "parfois 5 minutes : sois simple !", "sois simple !"),
    118: ("Parle librement", "de ce que tu vis,", "librement"),
    119: ("quand tu discutes", "avec ta meilleure pote,", "meilleure pote,"),
    120: ("tu n'utilises pas", "des mots hyper complexes,", "complexes,"),
    121: ("en essayant de paraître", "parfaite à chaque phrase.", "parfaite"),
    122: ("Tu peux te tromper,", "tu peux bafouiller,", "bafouiller,"),
    123: ("peu importe : parle face cam", "comme à ta pote,", "comme à ta pote,"),
    124: ("fais exactement", "la même chose !", "même chose !"),
    125: ("Ce que je veux te transmettre,", "c'est d'enlever ce masque :", "ce masque :"),
    126: ("cette image de :", "« Je dois être carrée, »", "être carrée, »"),
    127: ("« Je dois être parfaite,", "tout le monde doit m'aimer, »", "parfaite,"),
    128: ("« Il faut qu'on me perçoive", "de telle manière… »", "me perçoive"),
    129: ("Enlève cette étiquette", "que tu t'imposes,", "étiquette"),
    130: ("et creuse en profondeur", "car derrière ce contrôle,", "en profondeur"),
    131: ("il y a souvent une peur : fais", "ton introspection,", "introspection,"),
    132: ("essaie de comprendre", "pourquoi tu fonctionnes ainsi,", "comprendre"),
    133: ("et apprends simplement", "à t'accepter telle que tu es.", "t'accepter"),
    134: ("C'est une question d'acceptation :", "accepte la personne que tu es,", "d'acceptation :"),
    135: ("permets-toi d'avancer", "avec bienveillance,", "bienveillance,"),
    136: ("pose-toi la question :", "« Qui suis-je vraiment ? »", "Qui suis-je"),
    137: ("Es-tu la même personne", "quand tu es face caméra,", "face caméra,"),
    138: ("ou essaies-tu juste", "de paraître parfaite ?", "parfaite ?"),
    139: ("Ça m'a énormément aidée", "quand je voulais être parfaite :", "énormément aidée"),
    140: ("aujourd'hui peu m'importe", "qu'on me trouve bizarre,", "peu m'importe"),
    141: ("atypique ou différente :", "je suis 100% moi-même,", "100% moi-même,"),
    142: ("et je crée librement", "ce qui me ressemble vraiment.", "librement"),
    143: ("Applique ça dès aujourd'hui,", "tu verras toute la différence !", "la différence !"),
    144: ("On se retrouve très vite", "pour une prochaine vidéo !", "prochaine vidéo !"),
}

PHONETIC_FIXES = [
    ("Blour paraître", "Vouloir paraître"),
    ("déceère", "dessert"),
    ("au sa par la touton à", "au même que vouloir"),
    ("cette tepe-là", "pas"),
    ("d'un des légantes", "d'intelligent"),
    ("d'avantage tant même", "davantage"),
    ("t'envite", "tu as envie de"),
    ("t'envide", "tu as envie d'"),
    ("d'une géraleur", "dans le jugement"),
    ("bêtons-envient", "tu en viens"),
    ("non d'approprovise", "sans lâcher prise"),
    ("d'un sécurité", "d'insécurité"),
    ("la réseau", "les réseaux"),
    ("le réseau", "les réseaux"),
    ("en délisant", "en te disant"),
    ("notre prenant", "l'entrepreneuriat"),
    ("mérélent", "mes réels"),
    ("mensuie", "mon sujet"),
    ("son sui", "son sujet"),
    ("hypercaré", "hyper carré"),
    ("le biettif", "l'objectif"),
    ("tu les baires", "tu libères"),
    ("fasse cam", "face cam"),
    ("fasses cam", "face cam"),
    ("ta pottec", "ta pote"),
    ("ta potte", "ta pote"),
    ("c'est timage", "cette image"),
    ("père métoie", "permets-toi"),
    ("atypile", "atypique"),
]


def clean_and_split_2lines(idx: int, raw_text: str):
    """Guarantees strictly <= 2 lines of clean French text + a highlighted keyword."""
    if idx in CLEAN_FRENCH_OVERRIDES:
        return CLEAN_FRENCH_OVERRIDES[idx]

    txt = raw_text.replace('"', "").strip()
    for bad, good in PHONETIC_FIXES:
        txt = txt.replace(bad, good)
    words = txt.split()
    if not words:
        return ("", "", "")
    if len(words) <= 4:
        line1 = " ".join(words)
        line2 = ""
        hl = words[-1]
        return (line1, line2, hl)

    # Cap total words to 10 so 2 lines are always airy and punchy
    if len(words) > 10:
        words = words[:10]
    mid = len(words) // 2
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])
    # Pick longest impactful word in line2 as highlight keyword
    hl = max(words[mid:], key=lambda w: len(w.strip(".,?!»«")))
    return (line1, line2, hl)


def get_subtitle_sprite(idx: int, line1: str, line2: str, hl_word: str) -> np.ndarray:
    """Renders a 1-or-2-line lower-third subtitle sprite with Rose-Pink (`#EC4899`) accent."""
    key = ("sub_sp", idx)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]

    sw, sh = 1180, 175
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    f_l1 = get_font(INTER_BOLD, 38)
    f_l2 = get_font(JAKARTA_EBOLD, 46)

    # Soft dark backdrop pill for 100% legibility over any clothing/hand
    bb1 = d.textbbox((0, 0), line1, font=f_l1) if line1 else (0, 0, 0, 0)
    bb2 = d.textbbox((0, 0), line2, font=f_l2) if line2 else (0, 0, 0, 0)
    w1 = bb1[2] - bb1[0]
    w2 = bb2[2] - bb2[0]
    box_w = max(w1, w2) + 76
    bx0 = (sw - box_w) // 2
    bx1 = bx0 + box_w
    by0 = 14 if line2 else 42
    by1 = 158 if line2 else 128

    d.rounded_rectangle([bx0, by0, bx1, by1], radius=24, fill=(18, 12, 20, 175), outline=(*C_ROSE_LIGHT, 110), width=2)

    if not line2:
        # Single line centered with Rose-Pink bar
        tx = (sw - w1) // 2
        ty = 60
        d.rounded_rectangle([tx - 16, ty - 6, tx + w1 + 16, ty + 48], radius=12, fill=(*C_ROSE, 255))
        d.text((tx, ty), line1, font=f_l1, fill=(255, 255, 255, 255))
    else:
        # Strict 2 lines: Line 1 (Clean White) + Line 2 (ExtraBold with Rose-Pink Pill or Brush Underline)
        tx1 = (sw - w1) // 2
        ty1 = 28
        d.text((tx1 + 2, ty1 + 3), line1, font=f_l1, fill=(0, 0, 0, 180))
        d.text((tx1, ty1), line1, font=f_l1, fill=(248, 242, 246, 255))

        tx2 = (sw - w2) // 2
        ty2 = 82
        if idx % 2 == 0:
            # Rose-Pink pill behind Line 2
            d.rounded_rectangle([tx2 - 16, ty2 - 4, tx2 + w2 + 16, ty2 + 54], radius=12, fill=(*C_ROSE, 255))
            d.text((tx2, ty2), line2, font=f_l2, fill=(255, 255, 255, 255))
        else:
            # Crisp white ExtraBold Line 2 + Vibrant Rose-Pink brush underline
            d.text((tx2 + 2, ty2 + 3), line2, font=f_l2, fill=(0, 0, 0, 190))
            d.text((tx2, ty2), line2, font=f_l2, fill=(255, 255, 255, 255))
            d.rounded_rectangle([tx2 + 8, ty2 + 52, tx2 + w2 - 8, ty2 + 60], radius=4, fill=(*C_ROSE, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# 5. Dynamic Camera Framing & Rose Rim Lighting on Speaker A-Roll
# ---------------------------------------------------------------------------
def apply_dynamic_camera_and_grade(bgr: np.ndarray, t: float, active_side: str) -> np.ndarray:
    """
    Applies YouTube jump-cut zoom cadence (1.00x / 1.08x / 1.14x), smooth Ken Burns drift,
    and lateral Rule-of-Thirds reframing when a side-card is active on the left or right.
    """
    # Base beat zoom cycle (alternating every ~7.5s between medium 1.02x, close 1.11x, and punch-in 1.15x)
    beat_idx = int(t / 7.5)
    beat_phase = (t % 7.5) / 7.5
    if beat_idx % 3 == 0:
        zoom = 1.02 + 0.04 * beat_phase
    elif beat_idx % 3 == 1:
        zoom = 1.11 + 0.03 * math.sin(beat_phase * math.pi)
    else:
        zoom = 1.06 + 0.06 * (1.0 - beat_phase)

    # Extra punch-in on hook (0..5s) and conclusion (310..321s)
    if t < 5.18 or t > 310.0:
        zoom = max(zoom, 1.13)

    # Lateral pan to make room for side-cards while keeping speaker's face well framed
    target_pan_x = 0.0
    if active_side == "right":
        target_pan_x = -85.0  # Shift view window right -> speaker moves slightly left
        zoom = max(zoom, 1.10)
    elif active_side == "left":
        target_pan_x = 85.0   # Shift view window left -> speaker moves slightly right
        zoom = max(zoom, 1.10)

    cw = int(round(W / zoom))
    ch = int(round(H / zoom))
    # Center slightly higher on her face (y_center = 490)
    cx = int(round(W * 0.5 - target_pan_x))
    cy = int(round(H * 0.48))

    x0 = max(0, min(W - cw, cx - cw // 2))
    y0 = max(0, min(H - ch, cy - ch // 2))

    cropped = bgr[y0 : y0 + ch, x0 : x0 + cw]
    framed = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_LINEAR)

    # Subtle Rose-Pink Top-Left Studio Light Glow & Bottom Rose Progress Bar
    if "rose_glow_lut" not in _STATIC_CACHE:
        xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
        yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
        glow = np.exp(-((xx - 0.08) ** 2 / 0.08 + (yy - 0.12) ** 2 / 0.12))
        glow_bgr = np.zeros((H, W, 3), dtype=np.uint8)
        glow_bgr[:, :, 2] = np.clip(glow * 28.0, 0, 255).astype(np.uint8)  # R
        glow_bgr[:, :, 1] = np.clip(glow * 8.0, 0, 255).astype(np.uint8)   # G
        glow_bgr[:, :, 0] = np.clip(glow * 18.0, 0, 255).astype(np.uint8)  # B
        _STATIC_CACHE["rose_glow_lut"] = glow_bgr

    framed = cv2.add(framed, _STATIC_CACHE["rose_glow_lut"])
    return framed


def draw_youtube_progress_bar(bgr: np.ndarray, t: float, total_dur: float):
    """Draws a sleek Rose-Pink segmented YouTube chapter progress bar along y=1070..1080."""
    bar_y0 = 1070
    # Dark track
    bgr[bar_y0:H, :] = (bgr[bar_y0:H, :].astype(np.uint16) * 90 // 255).astype(np.uint8)
    prog_x = int(round(clamp(t / total_dur) * W))
    if prog_x > 0:
        # Rose-Pink fill (#EC4899 -> BGR: 153, 72, 236)
        bgr[bar_y0:H, :prog_x, 0] = 153
        bgr[bar_y0:H, :prog_x, 1] = 72
        bgr[bar_y0:H, :prog_x, 2] = 236
        # Brighter Rose-Blush leading tip
        tip_x0 = max(0, prog_x - 14)
        bgr[bar_y0:H, tip_x0:prog_x, 0] = 215
        bgr[bar_y0:H, tip_x0:prog_x, 1] = 165
        bgr[bar_y0:H, tip_x0:prog_x, 2] = 250

    # Chapter separator ticks
    for c_start, _, _, _ in CHAPTERS[1:]:
        tx = int(round((c_start / total_dur) * W))
        bgr[bar_y0:H, max(0, tx - 2) : min(W, tx + 2)] = (24, 18, 24)


# ---------------------------------------------------------------------------
# 6. Master Frame Compositor
# ---------------------------------------------------------------------------
def compose_youtube_frame(bgr_clean: np.ndarray, t: float, total_dur: float, parsed_segments: list) -> np.ndarray:
    # 1. Check if we are inside a Full-Screen Motion-Design Cutaway
    for c_start, c_end, cid in CUTAWAY_WINDOWS:
        if c_start <= t < c_end:
            out = render_cutaway_frame(t, cid)
            draw_youtube_progress_bar(out, t, total_dur)
            return out

    # 2. Check active side-card (for camera Rule-of-Thirds reframing + side-card overlay)
    active_card = None
    active_side = ""
    for sc in SIDE_CARDS:
        if sc[0] <= t < sc[1]:
            active_card = sc
            active_side = sc[2]
            break

    out = apply_dynamic_camera_and_grade(bgr_clean, t, active_side)

    # 3. Overlay Floating 3D Side-Card if active
    if active_card is not None:
        ts, te, side, badge, title, subtitle, stat = active_card
        age = t - ts
        rem = te - t
        p_in = ease_out_expo(age / 0.38)
        p_out = ease_out_expo(rem / 0.30) if rem < 0.30 else 1.0
        p = min(p_in, p_out)
        sp = get_side_card_sprite(badge, title, subtitle, stat)
        if side == "right":
            cx = int(round(1365 + 45 * (1.0 - p)))
        else:
            cx = int(round(50 - 45 * (1.0 - p)))
        cy = int(round(290 + 18 * (1.0 - p)))
        blend_rgba_onto_bgr(out, sp, cx, cy, opacity=p)

    # 4. Overlay Top-Left Chapter Pill during first 4.8s of each chapter (and throughout Hook)
    for c_start, c_end, ch_num, ch_title in CHAPTERS:
        if c_start <= t < c_end:
            ch_age = t - c_start
            if ch_age < 5.0:
                p_in = ease_out_expo(ch_age / 0.38)
                p_out = ease_out_expo((5.0 - ch_age) / 0.35) if ch_age > 4.65 else 1.0
                p = min(p_in, p_out)
                ch_sp = get_chapter_pill_sprite(ch_num, ch_title)
                blend_rgba_onto_bgr(out, ch_sp, 48, int(round(40 - 20 * (1.0 - p))), opacity=p)
            break

    # 5. Overlay Dynamic 1-to-2 Line Rose-Accent Subtitle
    for seg in parsed_segments:
        if seg["t0"] <= t < seg["t1"]:
            s_age = t - seg["t0"]
            p = ease_out_expo(s_age / 0.22)
            sub_sp = get_subtitle_sprite(seg["idx"], seg["line1"], seg["line2"], seg["hl"])
            sx = (W - sub_sp.shape[1]) // 2
            sy = int(round(875 + 14 * (1.0 - p)))
            blend_rgba_onto_bgr(out, sub_sp, sx, sy, opacity=p)
            break

    # 6. Segmented Rose-Pink YouTube Progress Bar
    draw_youtube_progress_bar(out, t, total_dur)
    return out


# ---------------------------------------------------------------------------
# 7. Audio Mastering (Original Voice + Subtle Rose-Chime & Whoosh Transitions)
# ---------------------------------------------------------------------------
def build_youtube_audio(ffmpeg_exe: str, total_dur: float) -> str:
    raw_wav = "/tmp/yt_inspect/clean_voice.wav"
    mixed_wav = "/tmp/yt_inspect/youtube_mixed.wav"
    subprocess.run(
        [ffmpeg_exe, "-y", "-i", CLEAN_MP4, "-vn", "-ar", "44100", "-ac", "2", raw_wav],
        check=True,
        capture_output=True,
    )
    with wave.open(raw_wav, "rb") as wf:
        sr = wf.getframerate()
        n_f = wf.getnframes()
        raw_bytes = wf.readframes(n_f)

    vo = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0
    total_samples = vo.shape[0]
    sfx = np.zeros(total_samples, dtype=np.float32)
    rng = np.random.default_rng(2026)

    # Soft YouTube whoosh + warm rose chime on cutaway & chapter transitions
    cues = [0.05, 5.18, 9.80, 16.34, 25.48, 51.60, 64.20, 73.60, 75.62, 114.54, 119.98, 184.46, 202.38, 211.50, 270.98, 290.22, 296.50]
    for ts in cues:
        i0 = int(ts * sr)
        dur_s = int(0.24 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.5
            chime = np.sin(2.0 * np.pi * 528.0 * lt * 0.24) * np.exp(-lt * 4.0)
            whoosh = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32) * env
            sfx[i0:i1] += 0.022 * chime + 0.010 * whoosh

    mix_l = np.clip(vo[:, 0] * 1.12 + sfx, -0.98, 0.98)
    mix_r = np.clip(vo[:, 1] * 1.12 + sfx, -0.98, 0.98)
    out_i16 = (np.stack([mix_l, mix_r], axis=-1) * 32767.0).astype(np.int16)

    with wave.open(mixed_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out_i16.tobytes())
    os.remove(raw_wav)
    return mixed_wav


def load_parsed_segments() -> list:
    with open(SEGMENTS_JSON, "r") as f:
        raw_segs = json.load(f)
    parsed = []
    for idx, s in enumerate(raw_segs):
        l1, l2, hl = clean_and_split_2lines(idx, s["text"])
        if l1:
            parsed.append({"idx": idx, "t0": s["t0"], "t1": s["t1"], "line1": l1, "line2": l2, "hl": hl})
    return parsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=str, default="", help="Save a 16-frame 16:9 preview contact sheet")
    args = parser.parse_args()

    parsed_segments = load_parsed_segments()

    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        cap = cv2.VideoCapture(CLEAN_MP4)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps

        sample_times = [
            1.5, 6.8, 12.5, 27.0,
            34.0, 58.0, 68.5, 82.0,
            117.0, 128.0, 164.0, 193.0,
            206.0, 236.0, 293.0, 316.0,
        ]
        cols, rows = 4, 4
        tw, th = 360, 202
        sheet = Image.new("RGB", (cols * tw, rows * th), (18, 14, 20))
        for i, st in enumerate(sample_times):
            cap.set(cv2.CAP_PROP_POS_MSEC, st * 1000.0)
            ok, bgr = cap.read()
            if not ok:
                continue
            composed_bgr = compose_youtube_frame(bgr, st, total_dur, parsed_segments)
            rgb = cv2.cvtColor(composed_bgr, cv2.COLOR_BGR2RGB)
            thumb = Image.fromarray(rgb).resize((tw, th), Image.LANCZOS)
            td = ImageDraw.Draw(thumb)
            td.rectangle([6, 6, 118, 30], fill=(24, 14, 22))
            td.text((12, 9), f"t={st:05.1f}s", fill=(244, 114, 182))
            sheet.paste(thumb, ((i % cols) * tw, (i // cols) * th))
        cap.release()
        sheet.save(args.preview, quality=92)
        print(f"Saved preview sheet to {args.preview}")
        return

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cap = cv2.VideoCapture(CLEAN_MP4)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_dur = total_frames / fps

    mixed_wav = build_youtube_audio(ffmpeg_exe, total_dur)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgr24",
        "-r", f"{fps:.02f}",
        "-i", "-",
        "-i", mixed_wav,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "24",
        "-maxrate", "1550k",
        "-bufsize", "3100k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-movflags", "+faststart",
        "-shortest",
        OUT_MP4,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    t0 = time.time()
    idx = 0
    try:
        while True:
            ok, bgr = cap.read()
            if not ok:
                break
            t = idx / fps
            out_bgr = compose_youtube_frame(bgr, t, total_dur, parsed_segments)
            proc.stdin.write(out_bgr.tobytes())
            idx += 1
            if idx % 1500 == 0 or idx == total_frames:
                el = time.time() - t0
                print(f"Rendered {idx}/{total_frames} frames ({100.0 * idx / total_frames:.1f}%) at {idx / max(0.01, el):.1f} fps", flush=True)
    finally:
        cap.release()
        if proc.stdin:
            proc.stdin.close()
        proc.wait()

    if os.path.exists(mixed_wav):
        os.remove(mixed_wav)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg exited with code {proc.returncode}")

    sz_mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"Successfully rendered {OUT_MP4} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    main()
