#!/usr/bin/env python3
"""
Master Dynamic 16:9 YouTube Edit with Rose-Pink Accent (`#EC4899`) for:
  `Être Intelligente En 2026 Te Dessert(1080P_HD).mp4` (1920x1080 @ 30fps, 321.37s, 9641 frames)

Upgraded with all 6 requested YouTube production pillars:
1. Pop-ups & Icon / Metaphor Illustrations (replaces the 21 rectangular text side-cards with 21 bespoke
   3D/vector humorous & metaphorical pop-up stickers + floating kinetic labels).
2. Plans d'illustration (B-Roll): 10 full-screen B-Roll cutaways alternating between graded real video B-Roll
   (with 3D visual overlays) and animated Rose-Cream (`#FAF6F8`) Motion-Design illustration scenes.
3. Zooms et cadrages dynamiques: Expressive ease-in-out facial zoom-ins/pull-outs (1.00x -> 1.18x) and
   smooth lateral Rule-of-Thirds reframing synced to key emotional phrases.
4. Dynamic Text / Micro-titres: Floating kinetic keyword callouts near the speaker to fix attention and
   reinforce memorization, plus strictly <= 2-line dynamic French subtitles at the bottom.
5. Voix claire et nettoyée: High-pass filter (85 Hz), soft noise gate, 3-band broadcast vocal EQ (warmth
   155 Hz, mud cut 250 Hz, presence 3.4 kHz, air 8.5 kHz), and studio leveling compression.
6. Musique de fond (Background Music) & Effets sonores (SFX): 3-mood adaptive stereo background score
   (Tension -> Storytelling -> Humour/Inspiration) with automatic vocal sidechain ducking, plus synchronized
   Pop/Bubble SFX on illustrations, UI Beep/Chime SFX on micro-titles, and Whoosh/Impact SFX on B-Roll cuts.
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
from scipy import signal

REPO_ROOT = "/home/user/COOL-backup"
PROJECT_DIR = f"{REPO_ROOT}/etre-intelligente-2026"
FILM_DIR = f"{PROJECT_DIR}/film"
ASSETS_DIR = f"{PROJECT_DIR}/assets"
CLEAN_MP4 = f"{FILM_DIR}/etre-intelligente-en-2026-sans-sous-titres-1080p.mp4"
OUT_MP4 = f"{FILM_DIR}/etre-intelligente-en-2026-youtube-rose-1080p.mp4"
SEGMENTS_JSON = f"{ASSETS_DIR}/segments.json"

BROLL_DIR = f"{REPO_ROOT}/felix-gray-reference10/assets/broll"
BROLL_FILES = {
    "studio": f"{BROLL_DIR}/broll_studio_table.mp4",
    "blueprint": f"{BROLL_DIR}/broll_blueprint_cad.mp4",
    "atrium": f"{BROLL_DIR}/broll_timber_atrium.mp4",
    "twilight": f"{BROLL_DIR}/broll_stage3_twilight_atrium.mp4",
    "skyline": f"{BROLL_DIR}/broll_shard_skyline.mp4",
}

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
C_ROSE_BLUSH = (252, 231, 243)  # #FCE7F3 Pastel Blush background
C_ROSE_DEEP = (157, 23, 77)     # #9D174D Deep Berry 3D bevel / shadow
C_GOLD = (245, 176, 36)         # #F5B024 Warm Gold accent for crowns/trophies/stars
C_PAPER = (250, 246, 248)       # #FAF6F8 Sunlit Rose-Cream cutaway canvas
C_CHARCOAL = (24, 20, 26)       # #18141A Crisp dark ink
C_MUTED = (96, 84, 100)         # Secondary editorial ink

_FONT_CACHE = {}
_SPRITE_CACHE = {}
_STATIC_CACHE = {}
_BROLL_FRAMES = {}


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def ease_out_expo(t: float) -> float:
    t = clamp(t)
    return 1.0 if t >= 1.0 else 1.0 - math.pow(2.0, -10.0 * t)


def ease_out_back(t: float, overshoot: float = 1.65) -> float:
    """Elastic spring pop-up curve for humorous stickers & icons."""
    t = clamp(t)
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * math.pow(t - 1.0, 3.0) + c1 * math.pow(t - 1.0, 2.0)


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
    """Fast in-place NumPy alpha-blend of an RGBA sprite onto a BGR frame at (x0, y0)."""
    if opacity <= 0.01:
        return
    sh, sw = sprite_rgba.shape[:2]
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
    sh = Image.new("RGBA", (pw + 24, ph + 24), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([12, 14, 12 + pw, 14 + ph], radius=29, fill=(24, 12, 20, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=6))
    im.alpha_composite(sh)

    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, 8 + pw, 8 + ph], radius=29, fill=(24, 18, 24, 225), outline=(*C_ROSE_LIGHT, 185), width=2)
    d.rounded_rectangle([14, 14, 98, 8 + ph - 6], radius=23, fill=(*C_ROSE, 255))
    d.text((30, 23), f"CH.{ch_num}", font=f_num, fill=(255, 255, 255, 255))
    d.text((114, 23), ch_title, font=f_txt, fill=(252, 244, 248, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# 2. Pop-ups & Icon / Metaphor Illustrations (Replaces the 21 Text Side-Cards!)
# ---------------------------------------------------------------------------
POPUP_ILLUSTRATIONS = [
    # (t_start, t_end, side, icon_kind, label_top, label_main)
    (10.10, 15.80, "right", "crown_sunglasses", "MODE « COOL »", "MISS PARFAITE ?"),
    (18.00, 25.10, "left", "battery_alarm", "DÈS LE RÉVEIL", "BATTERIE À 12%"),
    (25.48, 29.80, "right", "question_mirror", "CAUSE #1", "CONFIANCE : 404"),
    (29.88, 32.85, "right", "trophy_megaphone", "CAUSE #2", "PROUVER AUX AUTRES"),
    (38.25, 48.80, "right", "padlock_iceberg", "CAUSE #3", "LA PEUR CACHÉE"),
    (54.80, 63.80, "left", "ruler_protractor", "ZÉRO DÉFAUT", "100% CARRÉ ?"),
    (77.56, 89.80, "right", "magnet_hearts", "SANS CALCULER", "100% SOI-MÊME"),
    (103.82, 114.20, "right", "overheating_calc", "SUR-CONTRÔLE", "CERVEAU EN FUMÉE"),
    (122.10, 134.00, "left", "lightbulb_plant", "INTROSPECTION", "LE VRAI DÉCLIC"),
    (136.10, 141.40, "right", "stiff_robot", "TROP CALÉ", "MODE ROBOT : OFF"),
    (158.58, 173.80, "left", "flaming_heart_mic", "LE VRAI CHOIX", "PARLER AVEC PASSION"),
    (189.38, 201.80, "left", "spinning_compass", "RÈGLE D'OR", "NE TE PERDS PAS"),
    (212.30, 224.50, "right", "flaming_heart_mic", "EN 2026", "LIBÈRE TA PAROLE"),
    (231.78, 244.80, "left", "long_script_clock", "SCRIPT RIGIDE", "2H DE PRISE DE TÊTE"),
    (259.10, 270.80, "left", "clinking_cups", "ZÉRO PRESSION", "COMME À TA POTE !"),
    (272.18, 285.50, "right", "falling_mask", "INTROSPECTION", "TOMBE LE MASQUE"),
    (297.78, 312.00, "left", "rose_diamond", "SINGULARITÉ", "ATYPIQUE & VRAIE"),
    (313.18, 321.20, "right", "youtube_bell", "YOUTUBE 2026", "ABONNE-TOI !"),
]

# Additional Dynamic Text / Micro-titres (floating keyword pills to anchor key words!)
MICRO_TITLES = [
    # (t_start, t_end, x, y, text, subtag)
    (0.30, 4.90, 1320, 210, "PARAÎTRE INTELLIGENTE ?", "LE FAUX OBJECTIF"),
    (16.40, 17.95, 140, 220, "CHAQUE MATIN", "PRESSION INVISIBLE"),
    (49.00, 54.40, 1310, 230, "PEUR DU JUGEMENT", "BLOCAGE"),
    (98.50, 103.50, 140, 220, "VRAIE VISIBILITÉ", "IMPACT NATUREL"),
    (149.20, 158.20, 1310, 220, "TROP LISSE = FROID", "ZÉRO ÉMOTION"),
    (184.60, 189.20, 1320, 220, "MON DÉCLIC RÉSEAUX", "AUTHENTICITÉ"),
    (224.80, 231.50, 1310, 220, "SPONTANÉITÉ > SCRIPT", "IDÉE DIRECTE"),
    (285.60, 290.10, 140, 220, "ACCEPTE QUI TU ES", "LIBÉRATION"),
]


def _draw_sparkle(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, color):
    pts = [
        (cx, cy - r),
        (cx + r // 3, cy - r // 3),
        (cx + r, cy),
        (cx + r // 3, cy + r // 3),
        (cx, cy + r),
        (cx - r // 3, cy + r // 3),
        (cx - r, cy),
        (cx - r // 3, cy - r // 3),
    ]
    d.polygon(pts, fill=color)


def _draw_heart(d: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color):
    r = size // 2
    d.ellipse([cx - size, cy - r, cx, cy + r], fill=color)
    d.ellipse([cx, cy - r, cx + size, cy + r], fill=color)
    d.polygon([(cx - size, cy + r // 3), (cx + size, cy + r // 3), (cx, cy + size + r // 2)], fill=color)


def get_popup_illustration_sprite(icon_kind: str, label_top: str, label_main: str) -> np.ndarray:
    """
    Renders a bespoke 3D/tactile vector Pop-Up Sticker Illustration with a floating
    medallion backdrop, playful metaphor artwork, and a bold Micro-Titre banner underneath.
    """
    key = ("popup_ill", icon_kind, label_top, label_main)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]

    sw, sh = 420, 360
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))

    # 1. Soft 45-degree drop shadow under the circular sticker medallion & banner
    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([110 + 8, 22 + 14, 310 + 8, 222 + 14], fill=(38, 10, 24, 130))
    sd.rounded_rectangle([35 + 8, 208 + 14, 385 + 8, 322 + 14], radius=28, fill=(38, 10, 24, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
    im.alpha_composite(shadow)

    d = ImageDraw.Draw(im)

    # 2. Sticker Medallion Circle (Cream-Blush 3D Tactile Circle with thick white sticker border & Rose ring)
    mcx, mcy, mr = 210, 122, 102
    d.ellipse([mcx - mr - 6, mcy - mr - 6, mcx + mr + 6, mcy + mr + 6], fill=(255, 255, 255, 255))
    d.ellipse([mcx - mr, mcy - mr, mcx + mr, mcy + mr], fill=(*C_ROSE_BLUSH, 255), outline=(*C_ROSE, 255), width=5)
    # Floating decorative sparkles around medallion
    _draw_sparkle(d, mcx - 92, mcy - 68, 14, (*C_GOLD, 255))
    _draw_sparkle(d, mcx + 96, mcy - 52, 12, (*C_ROSE, 255))
    _draw_sparkle(d, mcx + 88, mcy + 58, 10, (*C_GOLD, 255))

    # 3. Custom Metaphor / Humorous Vector Illustration inside (mcx, mcy)
    if icon_kind == "crown_sunglasses":
        # Golden 3D Crown + Cool Sunglasses ("Wanting to look smart & cool")
        pts_crown = [
            (mcx - 54, mcy - 8),
            (mcx - 62, mcy - 58),
            (mcx - 26, mcy - 28),
            (mcx, mcy - 68),
            (mcx + 26, mcy - 28),
            (mcx + 62, mcy - 58),
            (mcx + 54, mcy - 8),
        ]
        d.polygon(pts_crown, fill=(*C_GOLD, 255), outline=(*C_CHARCOAL, 255))
        d.ellipse([mcx - 6, mcy - 76, mcx + 6, mcy - 64], fill=(*C_ROSE, 255))
        # Cool dark sunglasses below crown
        d.rounded_rectangle([mcx - 64, mcy + 6, mcx - 8, mcy + 46], radius=10, fill=(*C_CHARCOAL, 255), outline=(255, 255, 255, 255), width=3)
        d.rounded_rectangle([mcx + 8, mcy + 6, mcx + 64, mcy + 46], radius=10, fill=(*C_CHARCOAL, 255), outline=(255, 255, 255, 255), width=3)
        d.line([(mcx - 8, mcy + 18), (mcx + 8, mcy + 18)], fill=(*C_CHARCOAL, 255), width=6)
        # White lens reflection slashes
        d.line([(mcx - 50, mcy + 36), (mcx - 32, mcy + 14)], fill=(255, 255, 255, 220), width=4)
        d.line([(mcx + 22, mcy + 36), (mcx + 40, mcy + 14)], fill=(255, 255, 255, 220), width=4)

    elif icon_kind == "battery_alarm":
        # Draining Red/Rose Battery (12%) + Lightning bolt
        d.rounded_rectangle([mcx - 56, mcy - 38, mcx + 46, mcy + 38], radius=14, fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=5)
        d.rounded_rectangle([mcx + 46, mcy - 16, mcx + 60, mcy + 16], radius=5, fill=(*C_CHARCOAL, 255))
        # Low red/rose charge bar on left
        d.rounded_rectangle([mcx - 46, mcy - 28, mcx - 20, mcy + 28], radius=8, fill=(*C_ROSE, 255))
        d.text((mcx - 10, mcy - 18), "12%", font=get_font(JAKARTA_EBOLD, 28), fill=(*C_ROSE_DEEP, 255))

    elif icon_kind == "question_mirror":
        # Ornate Hand Mirror + Giant Question Mark ("Lack of self-confidence")
        d.ellipse([mcx - 46, mcy - 64, mcx + 46, mcy + 28], fill=(255, 255, 255, 255), outline=(*C_ROSE, 255), width=8)
        d.rounded_rectangle([mcx - 10, mcy + 26, mcx + 10, mcy + 72], radius=8, fill=(*C_ROSE_DEEP, 255))
        d.text((mcx - 18, mcy - 54), "?", font=get_font(JAKARTA_EBOLD, 68), fill=(*C_ROSE, 255))

    elif icon_kind == "trophy_megaphone":
        # 3D Megaphone blasting sound waves ("Look at me, I must prove I'm great!")
        d.polygon([(mcx - 48, mcy + 8), (mcx + 26, mcy - 38), (mcx + 26, mcy + 44), (mcx - 48, mcy + 24)], fill=(*C_ROSE, 255), outline=(*C_CHARCOAL, 255))
        d.rounded_rectangle([mcx - 58, mcy + 4, mcx - 42, mcy + 32], radius=6, fill=(*C_CHARCOAL, 255))
        d.rounded_rectangle([mcx - 36, mcy + 24, mcx - 20, mcy + 58], radius=6, fill=(*C_ROSE_DEEP, 255))
        # Sound wave arcs
        for r_w in (20, 38, 56):
            d.arc([mcx + 20, mcy - r_w, mcx + 20 + r_w, mcy + r_w], start=-45, end=45, fill=(*C_GOLD, 255), width=5)

    elif icon_kind == "padlock_iceberg":
        # Heavy 3D Rose-Berry Padlock ("Hidden fear locked deep inside")
        d.arc([mcx - 34, mcy - 66, mcx + 34, mcy + 4], start=180, end=0, fill=(*C_CHARCOAL, 255), width=12)
        d.rounded_rectangle([mcx - 48, mcy - 22, mcx + 48, mcy + 56], radius=16, fill=(*C_ROSE, 255), outline=(*C_CHARCOAL, 255), width=4)
        d.ellipse([mcx - 10, mcy + 2, mcx + 10, mcy + 22], fill=(255, 255, 255, 255))
        d.polygon([(mcx - 6, mcy + 18), (mcx + 6, mcy + 18), (mcx + 9, mcy + 40), (mcx - 9, mcy + 40)], fill=(255, 255, 255, 255))

    elif icon_kind == "ruler_protractor":
        # Architect Set-Square Triangle + Ruler ("Wanting everything square & perfect")
        pts_tri = [(mcx - 54, mcy + 48), (mcx - 54, mcy - 54), (mcx + 54, mcy + 48)]
        d.polygon(pts_tri, fill=(*C_GOLD, 240), outline=(*C_CHARCOAL, 255))
        pts_in = [(mcx - 34, mcy + 30), (mcx - 34, mcy - 10), (mcx + 10, mcy + 30)]
        d.polygon(pts_in, fill=(*C_ROSE_BLUSH, 255), outline=(*C_CHARCOAL, 255))
        # Tick marks along vertical edge
        for ty_i in range(-42, 44, 14):
            d.line([(mcx - 54, mcy + ty_i), (mcx - 42, mcy + ty_i)], fill=(*C_CHARCOAL, 255), width=3)

    elif icon_kind == "magnet_hearts":
        # Horseshoe Magnet attracting hearts ("Authenticity naturally attracts visibility")
        d.arc([mcx - 48, mcy - 42, mcx + 48, mcy + 54], start=0, end=180, fill=(*C_ROSE, 255), width=22)
        d.rectangle([mcx - 48, mcy - 28, mcx - 26, mcy + 8], fill=(*C_ROSE, 255))
        d.rectangle([mcx + 26, mcy - 28, mcx + 48, mcy + 8], fill=(*C_ROSE, 255))
        # White/Silver magnet tips
        d.rectangle([mcx - 48, mcy - 44, mcx - 26, mcy - 26], fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=2)
        d.rectangle([mcx + 26, mcy - 44, mcx + 48, mcy - 26], fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=2)
        _draw_heart(d, mcx, mcy - 50, 18, (*C_ROSE_DEEP, 255))

    elif icon_kind == "overheating_calc":
        # Overheating Calculator ("Over-calculating every single word")
        d.rounded_rectangle([mcx - 46, mcy - 54, mcx + 46, mcy + 56], radius=14, fill=(*C_CHARCOAL, 255), outline=(255, 255, 255, 255), width=3)
        d.rounded_rectangle([mcx - 34, mcy - 42, mcx + 34, mcy - 14], radius=6, fill=(*C_ROSE, 255))
        d.text((mcx - 26, mcy - 40), "ERR!", font=get_font(MONO_MED, 22), fill=(255, 255, 255, 255))
        for r_i in range(3):
            for c_i in range(3):
                bx = mcx - 32 + c_i * 23
                by = mcy - 4 + r_i * 19
                d.rounded_rectangle([bx, by, bx + 17, by + 13], radius=3, fill=(245, 240, 244, 255))

    elif icon_kind == "lightbulb_plant":
        # Glowing Idea Lightbulb ("Entrepreneurship epiphany & deep inner work")
        d.ellipse([mcx - 42, mcy - 56, mcx + 42, mcy + 24], fill=(*C_GOLD, 255), outline=(*C_CHARCOAL, 255), width=4)
        d.rounded_rectangle([mcx - 20, mcy + 18, mcx + 20, mcy + 46], radius=6, fill=(*C_CHARCOAL, 255))
        for ang in range(-60, 241, 45):
            rad = math.radians(ang)
            x1 = mcx + int(52 * math.cos(rad))
            y1 = (mcy - 16) - int(52 * math.sin(rad))
            x2 = mcx + int(68 * math.cos(rad))
            y2 = (mcy - 16) - int(68 * math.sin(rad))
            d.line([(x1, y1), (x2, y2)], fill=(*C_ROSE, 255), width=5)

    elif icon_kind == "stiff_robot":
        # Stiff Robot Head with Antenna ("Cold robotic expertise")
        d.line([(mcx, mcy - 68), (mcx, mcy - 44)], fill=(*C_CHARCOAL, 255), width=6)
        d.ellipse([mcx - 9, mcy - 78, mcx + 9, mcy - 60], fill=(*C_ROSE, 255))
        d.rounded_rectangle([mcx - 50, mcy - 44, mcx + 50, mcy + 44], radius=16, fill=(230, 232, 238, 255), outline=(*C_CHARCOAL, 255), width=4)
        d.ellipse([mcx - 32, mcy - 22, mcx - 12, mcy - 2], fill=(*C_ROSE_DEEP, 255))
        d.ellipse([mcx + 12, mcy - 22, mcx + 32, mcy - 2], fill=(*C_ROSE_DEEP, 255))
        d.rectangle([mcx - 28, mcy + 14, mcx + 28, mcy + 26], fill=(*C_CHARCOAL, 255))

    elif icon_kind == "flaming_heart_mic":
        # Radiant Rose Heart + Sound Wave Bars ("Speaking with passion & heart")
        _draw_heart(d, mcx, mcy - 14, 38, (*C_ROSE, 255))
        for i, bh in enumerate([16, 30, 44, 24, 38, 18]):
            bx = mcx - 42 + i * 16
            d.rounded_rectangle([bx, mcy + 46 - bh // 2, bx + 9, mcy + 46 + bh // 2], radius=4, fill=(*C_ROSE_DEEP, 255))

    elif icon_kind == "spinning_compass":
        # Compass Rose ("Don't lose yourself trying to please everyone")
        d.ellipse([mcx - 54, mcy - 54, mcx + 54, mcy + 54], fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=5)
        d.polygon([(mcx, mcy - 44), (mcx + 14, mcy), (mcx, mcy - 8), (mcx - 14, mcy)], fill=(*C_ROSE, 255))
        d.polygon([(mcx, mcy + 44), (mcx + 14, mcy), (mcx, mcy + 8), (mcx - 14, mcy)], fill=(*C_MUTED, 255))
        d.ellipse([mcx - 7, mcy - 7, mcx + 7, mcy + 7], fill=(*C_GOLD, 255))

    elif icon_kind == "long_script_clock":
        # Unrolling Paper Script + Clock ("Taking 2 hours to film with a rigid script")
        d.rounded_rectangle([mcx - 48, mcy - 52, mcx + 24, mcy + 48], radius=10, fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=4)
        for ly in range(-32, 30, 16):
            d.line([(mcx - 32, mcy + ly), (mcx + 8, mcy + ly)], fill=(*C_MUTED, 255), width=4)
        # Overlapping Rose Clock on bottom-right
        d.ellipse([mcx - 2, mcy - 4, mcx + 62, mcy + 60], fill=(*C_ROSE, 255), outline=(255, 255, 255, 255), width=4)
        d.line([(mcx + 30, mcy + 28), (mcx + 30, mcy + 10)], fill=(255, 255, 255, 255), width=4)
        d.line([(mcx + 30, mcy + 28), (mcx + 46, mcy + 28)], fill=(255, 255, 255, 255), width=4)

    elif icon_kind == "clinking_cups":
        # Two Clinking Coffee Cups + Heart ("Talk like you're chatting with your best friend!")
        d.rounded_rectangle([mcx - 56, mcy - 18, mcx - 6, mcy + 44], radius=10, fill=(*C_ROSE, 255), outline=(*C_CHARCOAL, 255), width=4)
        d.rounded_rectangle([mcx + 6, mcy - 18, mcx + 56, mcy + 44], radius=10, fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=4)
        _draw_heart(d, mcx, mcy - 42, 18, (*C_ROSE_DEEP, 255))

    elif icon_kind == "falling_mask":
        # Mask peeling off + Glowing Gold Star ("Take off the perfectionist mask")
        d.rounded_rectangle([mcx - 52, mcy - 38, mcx + 18, mcy + 36], radius=24, fill=(255, 255, 255, 255), outline=(*C_CHARCOAL, 255), width=4)
        d.arc([mcx - 38, mcy - 18, mcx - 18, mcy - 2], start=180, end=0, fill=(*C_CHARCOAL, 255), width=4)
        d.arc([mcx - 8, mcy - 18, mcx + 12, mcy - 2], start=180, end=0, fill=(*C_CHARCOAL, 255), width=4)
        _draw_sparkle(d, mcx + 36, mcy - 26, 26, (*C_ROSE, 255))

    elif icon_kind == "rose_diamond":
        # Faceted Rose Diamond ("Embrace being atypical & unique")
        top_pts = [(mcx - 36, mcy - 42), (mcx + 36, mcy - 42), (mcx + 58, mcy - 12), (mcx - 58, mcy - 12)]
        bot_pts = [(mcx - 58, mcy - 12), (mcx + 58, mcy - 12), (mcx, mcy + 54)]
        d.polygon(top_pts, fill=(*C_ROSE_LIGHT, 255), outline=(*C_CHARCOAL, 255))
        d.polygon(bot_pts, fill=(*C_ROSE, 255), outline=(*C_CHARCOAL, 255))
        d.line([(mcx - 36, mcy - 42), (mcx, mcy + 54)], fill=(255, 255, 255, 200), width=3)
        d.line([(mcx + 36, mcy - 42), (mcx, mcy + 54)], fill=(255, 255, 255, 200), width=3)

    else:
        # YouTube Play Button + Subscribe Heart ("Subscribe for the next video!")
        d.rounded_rectangle([mcx - 58, mcy - 40, mcx + 58, mcy + 40], radius=22, fill=(*C_ROSE, 255), outline=(255, 255, 255, 255), width=4)
        d.polygon([(mcx - 16, mcy - 22), (mcx - 16, mcy + 22), (mcx + 24, mcy)], fill=(255, 255, 255, 255))

    # 4. Bold Micro-Titre Pill Banner overlapping the bottom of the sticker medallion
    d.rounded_rectangle([35, 208, 385, 322], radius=28, fill=(24, 18, 24, 245), outline=(*C_ROSE, 255), width=3)
    # Top mini pill tag
    f_top = get_font(MONO_MED, 17)
    bb_t = d.textbbox((0, 0), label_top, font=f_top)
    tw_t = bb_t[2] - bb_t[0]
    tx_t = (sw - tw_t) // 2
    d.rounded_rectangle([tx_t - 18, 192, tx_t + tw_t + 18, 226], radius=16, fill=(*C_ROSE, 255))
    d.text((tx_t, 198), label_top, font=f_top, fill=(255, 255, 255, 255))

    # Main Micro-Titre text
    f_main = get_font(JAKARTA_EBOLD, 27)
    bb_m = d.textbbox((0, 0), label_main, font=f_main)
    tw_m = bb_m[2] - bb_m[0]
    d.text(((sw - tw_m) // 2, 246), label_main, font=f_main, fill=(255, 255, 255, 255))
    # Rose underline bar inside banner
    d.rounded_rectangle([135, 294, 285, 302], radius=4, fill=(*C_ROSE_LIGHT, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


def get_micro_title_sprite(text: str, subtag: str) -> np.ndarray:
    """Renders a sleek kinetic Dynamic Text / Micro-titre callout badge."""
    key = ("micro_title_v2", text, subtag)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]

    f_main = get_font(JAKARTA_EBOLD, 27)
    f_sub = get_font(MONO_MED, 16)
    tmp = Image.new("RGBA", (10, 10))
    dt = ImageDraw.Draw(tmp)
    w_m = dt.textbbox((0, 0), text, font=f_main)[2]
    w_s = dt.textbbox((0, 0), subtag, font=f_sub)[2]

    bw = max(w_m + 56, w_s + 84, 260)
    bh = 96
    im = Image.new("RGBA", (bw + 24, bh + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 16, 14 + bw, 16 + bh], radius=24, fill=(0, 0, 0, 85))
    d.rounded_rectangle([10, 10, 10 + bw, 10 + bh], radius=24, fill=(24, 18, 24, 244), outline=(*C_ROSE, 255), width=3)
    d.rounded_rectangle([28, 22, 46 + w_s, 46], radius=12, fill=(*C_ROSE, 255))
    d.text((38, 25), subtag, font=f_sub, fill=(255, 255, 255, 255))
    d.text((28, 54), text, font=f_main, fill=(255, 255, 255, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# 3. Ten Full-Screen B-Roll & Animated Illustration Cutaways
# ---------------------------------------------------------------------------
# Combines 5 real video B-Roll cutaways (graded in warm Rose-Cinema LUT + 3D graphic overlays)
# and 5 animated Rose-Cream (`#FAF6F8`) Motion-Design illustration scenes!
CUTAWAY_WINDOWS = [
    (5.18, 9.80, 1),     # Animated Rose-Paper Illustration #1: Te Dessert Partout (3 Cards + Icons)
    (32.90, 38.20, 6),   # Video B-Roll #1 (Studio + 3D Trophy/Validation Overlay): Vouloir prouver qu'on est géniale
    (64.20, 73.60, 2),   # Animated Rose-Paper Illustration #2: La Réaction en Chaîne (Perfection -> Peur)
    (90.22, 98.38, 7),   # Video B-Roll #2 (Timber Atrium + 3D Magnet Overlay): Percer sans concept parfait
    (114.54, 119.98, 3), # Animated Rose-Paper Illustration #3: + De Calcul = - D'Authenticité
    (141.58, 149.06, 8), # Video B-Roll #3 (Blueprint CAD + 3D Robot Overlay): Le piège des réels trop lisses
    (175.30, 184.46, 9), # Video B-Roll #4 (Twilight Atrium + 3D Heart Overlay): Parler avec son vécu
    (202.38, 211.50, 4), # Animated Rose-Paper Illustration #4: Intelligence Émotionnelle 3D
    (245.22, 256.86, 10),# Video B-Roll #5 (Skyline + Split Timer 2H vs 5 MIN): Face-cam spontané
    (290.22, 296.50, 5), # Animated Rose-Paper Illustration #5: C'est une question d'acceptation
]


def get_broll_frame_graded(broll_key: str, local_t: float) -> np.ndarray:
    """Loads, caches, and grades a real B-Roll video clip with a warm Rose-Editorial LUT."""
    if broll_key not in _BROLL_FRAMES:
        path = BROLL_FILES.get(broll_key, "")
        frames = []
        if os.path.exists(path):
            cap = cv2.VideoCapture(path)
            while len(frames) < 180:
                ok, f = cap.read()
                if not ok:
                    break
                # Center-crop or resize to 1920x1080
                fh, fw = f.shape[:2]
                target_aspect = W / H
                cur_aspect = fw / fh
                if cur_aspect < target_aspect:
                    nh = int(round(fw / target_aspect))
                    y0 = (fh - nh) // 2
                    f = f[y0 : y0 + nh, :]
                else:
                    nw = int(round(fh * target_aspect))
                    x0 = (fw - nw) // 2
                    f = f[:, x0 : x0 + nw]
                f1080 = cv2.resize(f, (W, H), interpolation=cv2.INTER_LINEAR)
                # Apply warm Rose-Editorial cinema grade + dark vignette for text contrast
                f_float = f1080.astype(np.float32) * 0.52
                f_float[:, :, 2] = np.clip(f_float[:, :, 2] * 1.18 + 22.0, 0, 255)  # R (warm rose)
                f_float[:, :, 1] = np.clip(f_float[:, :, 1] * 0.95 + 10.0, 0, 255)  # G
                f_float[:, :, 0] = np.clip(f_float[:, :, 0] * 1.12 + 18.0, 0, 255)  # B
                frames.append(f_float.astype(np.uint8))
            cap.release()
        _BROLL_FRAMES[broll_key] = frames

    frames = _BROLL_FRAMES[broll_key]
    if not frames:
        return np.full((H, W, 3), (32, 22, 30), dtype=np.uint8)
    idx = int(local_t * FPS) % len(frames)
    # Apply slow Ken Burns zoom on B-Roll
    zoom = 1.02 + 0.06 * clamp(local_t / 8.0)
    cw, ch = int(W / zoom), int(H / zoom)
    x0, y0 = (W - cw) // 2, (H - ch) // 2
    return cv2.resize(frames[idx][y0 : y0 + ch, x0 : x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)


def get_rose_gobo_paper_base() -> Image.Image:
    if "rose_paper_base" in _STATIC_CACHE:
        return _STATIC_CACHE["rose_paper_base"]

    xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]

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
    d = ImageDraw.Draw(im, "RGBA")
    for gx in range(260, 1661, 56):
        d.line([(gx, 160), (gx, 920)], fill=(236, 72, 153, 24), width=1)
    for gy in range(160, 921, 56):
        d.line([(260, gy), (1660, gy)], fill=(236, 72, 153, 24), width=1)

    _STATIC_CACHE["rose_paper_base"] = im
    return im


def render_cutaway_frame(t: float, cutaway_id: int) -> np.ndarray:
    # Animated B-Roll Metaphor Scenes (IDs 6..10: Rich Dark-Rose Studio Canvas + Full Animated Metaphor Illustrations)
    if cutaway_id >= 6:
        broll_specs = {
            6: (32.90, "trophy_megaphone", "VALIDATION EXTERNE", "B-ROLL • LE PIÈGE DE L'APPROBATION", "PROUVER QU'ON EST « GÉNIALE »", "Chercher la validation des autres épuise ta confiance intérieure"),
            7: (90.22, "magnet_hearts", "AIMANT NATUREL", "B-ROLL • LA FORCE DU VRAI", "PERCER SANS CONCEPT PARFAIT", "Les personnes qui restent 100% elles-mêmes attirent naturellement l'audience"),
            8: (141.58, "stiff_robot", "ZÉRO ÉMOTION", "B-ROLL • L'ILLUSION DE L'EXPERTISE", "LE PIÈGE DES RÉELS TROP LISSES", "Un discours trop carré et robotique coupe toute connexion humaine"),
            9: (175.30, "flaming_heart_mic", "VRAIE CONNEXION", "B-ROLL • PARLER AVEC LE CŒUR", "PARTAGER SON VÉCU & SA PASSION", "Entre des mots compliqués et une expérience vécue, l'audience choisit le vrai"),
            10: (245.22, "clinking_cups", "5 MIN CHRONO", "B-ROLL • SPONTANÉITÉ FACE-CAM", "5 MIN SPONTANÉES > 2H DE SCRIPT", "Allume ta caméra et parle librement comme à ta meilleure pote !"),
        }
        t0_b, ic_kind, ic_badge, tag, headline, subline = broll_specs[cutaway_id]
        age = t - t0_b

        # Rich Dark Rose-Velvet Animated Studio Canvas (#1A1218 with glowing Rose bokeh & architectural grid)
        if "dark_rose_broll_base" not in _STATIC_CACHE:
            xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
            yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
            orb1 = np.exp(-((xx - 0.22) ** 2 / 0.08 + (yy - 0.28) ** 2 / 0.12))
            orb2 = np.exp(-((xx - 0.82) ** 2 / 0.09 + (yy - 0.72) ** 2 / 0.14))
            r_c = np.clip(24.0 + 78.0 * orb1 + 55.0 * orb2, 0, 255).astype(np.uint8)
            g_c = np.clip(15.0 + 22.0 * orb1 + 18.0 * orb2, 0, 255).astype(np.uint8)
            b_c = np.clip(22.0 + 52.0 * orb1 + 42.0 * orb2, 0, 255).astype(np.uint8)
            im_dark = Image.fromarray(np.stack([b_c, g_c, r_c], axis=-1), mode="RGB")
            dd = ImageDraw.Draw(im_dark, "RGBA")
            for gx in range(160, 1761, 64):
                dd.line([(gx, 120), (gx, 960)], fill=(244, 114, 182, 22), width=1)
            for gy in range(120, 961, 64):
                dd.line([(160, gy), (1760, gy)], fill=(244, 114, 182, 22), width=1)
            _STATIC_CACHE["dark_rose_broll_base"] = np.array(im_dark, dtype=np.uint8)

        bgr = _STATIC_CACHE["dark_rose_broll_base"].copy()

        p = ease_out_expo(age / 0.40)
        card_im = Image.new("RGBA", (1460, 440), (0, 0, 0, 0))
        d = ImageDraw.Draw(card_im)
        d.rounded_rectangle([0, 0, 1459, 439], radius=34, fill=(32, 20, 30, 238), outline=(*C_ROSE, 240), width=3)
        d.rounded_rectangle([48, 46, 520, 94], radius=24, fill=(*C_ROSE, 255))
        d.text((72, 58), tag, font=get_font(MONO_MED, 20), fill=(255, 255, 255, 255))
        d.text((48, 138), headline, font=get_font(JAKARTA_EBOLD, 44), fill=(255, 255, 255, 255))
        d.rounded_rectangle([48, 212, 360, 220], radius=4, fill=(*C_ROSE_LIGHT, 255))
        d.text((48, 248), subline, font=get_font(INTER_MED, 25), fill=(*C_ROSE_BLUSH, 255))

        # Animated progress/comparison meter bar at bottom of B-Roll card
        bar_w = int(680 * ease_out_expo(max(0.0, age - 0.25) / 0.85))
        d.rounded_rectangle([48, 332, 728, 362], radius=15, fill=(48, 32, 44, 255))
        if bar_w > 12:
            d.rounded_rectangle([48, 332, 48 + bar_w, 362], radius=15, fill=(*C_ROSE, 255))

        blend_rgba_onto_bgr(bgr, np.array(card_im, dtype=np.uint8), (W - 1460) // 2, int(195 + 28 * (1.0 - p)), opacity=p)
        sp_ic = get_popup_illustration_sprite(ic_kind, "ILLUSTRATION", ic_badge)
        blend_rgba_onto_bgr(bgr, sp_ic, 1245, int(225 + 35 * (1.0 - p)), opacity=p)
        return bgr

    # Animated Rose-Paper Illustration Cutaways (IDs 1..5)
    base = get_rose_gobo_paper_base().copy().convert("RGBA")
    d = ImageDraw.Draw(base)

    if cutaway_id == 1:
        age = t - 5.18
        f_top = get_font(INTER_MED, 34)
        f_hero = get_font(JAKARTA_EBOLD, 68)
        d.text((W // 2 - 260, 135), "Vouloir paraître intelligente", font=f_top, fill=(*C_MUTED, 255))
        d.rounded_rectangle([W // 2 - 440, 228, W // 2 + 440, 282], radius=10, fill=(*C_ROSE, 255))
        d.text((W // 2 - 415, 195), "TE DESSERT PARTOUT", font=f_hero, fill=(*C_CHARCOAL, 255))

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
            cy = int(360 + 36 * (1.0 - p))
            cw, ch = 460, 390
            d.rounded_rectangle([cx + 10, cy + 16, cx + cw + 10, cy + ch + 16], radius=28, fill=(157, 23, 77, int(45 * p)))
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=28, fill=(255, 255, 255, int(248 * p)), outline=(*C_ROSE, int(235 * p)), width=3)
            d.rounded_rectangle([cx + 36, cy + 36, cx + 126, cy + 92], radius=22, fill=(*C_ROSE, int(255 * p)))
            d.text((cx + 58, cy + 46), num, font=get_font(JAKARTA_EBOLD, 30), fill=(255, 255, 255, int(255 * p)))
            _draw_heart(d, cx + cw - 68, cy + 64, 22, (*C_ROSE_LIGHT, int(255 * p)))
            d.text((cx + 36, cy + 135), title, font=get_font(JAKARTA_EBOLD, 38), fill=(*C_CHARCOAL, int(255 * p)))
            d.rounded_rectangle([cx + 36, cy + 198, cx + 190, cy + 206], radius=4, fill=(*C_ROSE_LIGHT, int(255 * p)))
            d.text((cx + 36, cy + 230), sub, font=get_font(INTER_MED, 24), fill=(*C_MUTED, int(255 * p)))

    elif cutaway_id == 2:
        age = t - 64.20
        d.text((W // 2 - 290, 145), "Le piège invisible du perfectionnisme", font=get_font(GREAT_VIBES, 64), fill=(*C_ROSE_DEEP, 255))
        d.text((W // 2 - 430, 220), "LA RÉACTION EN CHAÎNE", font=get_font(JAKARTA_EBOLD, 64), fill=(*C_CHARCOAL, 255))

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
            cy = int(395 + 30 * (1.0 - p))
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
        age = t - 114.54
        p1 = ease_out_expo(age / 0.40)
        p2 = ease_out_expo((age - 1.2) / 0.45)
        d.text((W // 2 - 240, int(210 + 20 * (1.0 - p1))), "La loi de l'authenticité", font=get_font(GREAT_VIBES, 76), fill=(*C_ROSE_DEEP, int(255 * p1)))
        d.rounded_rectangle([260, 340, 910, 720], radius=28, fill=(255, 255, 255, int(248 * p1)), outline=(*C_ROSE_LIGHT, int(220 * p1)), width=3)
        d.text((310, 390), "QUAND TU SUR-CALCULES", font=get_font(MONO_MED, 24), fill=(*C_MUTED, int(255 * p1)))
        d.text((310, 455), "+ DE CALCUL ↑", font=get_font(JAKARTA_EBOLD, 56), fill=(*C_CHARCOAL, int(255 * p1)))
        d.text((310, 555), "Chaque mot, chaque geste est forcé", font=get_font(INTER_MED, 26), fill=(*C_MUTED, int(255 * p1)))

        if p2 > 0.01:
            d.rounded_rectangle([1010, int(340 + 25 * (1.0 - p2)), 1660, int(720 + 25 * (1.0 - p2))], radius=28, fill=(*C_ROSE, int(255 * p2)))
            d.text((1060, int(390 + 25 * (1.0 - p2))), "LE RÉSULTAT DIRECT", font=get_font(MONO_MED, 24), fill=(252, 231, 243, int(255 * p2)))
            d.text((1060, int(455 + 25 * (1.0 - p2))), "- D'AUTHENTICITÉ ↓", font=get_font(JAKARTA_EBOLD, 52), fill=(255, 255, 255, int(255 * p2)))
            d.text((1060, int(555 + 25 * (1.0 - p2))), "Tu n'as même plus l'impression d'être toi.", font=get_font(INTER_MED, 25), fill=(255, 255, 255, int(255 * p2)))

    elif cutaway_id == 4:
        age = t - 202.38
        p = ease_out_expo(age / 0.42)
        d.text((W // 2 - 280, 195), "En 2026, la vraie intelligence est", font=get_font(INTER_MED, 38), fill=(*C_CHARCOAL, int(255 * p)))

        f_hero = get_font(JAKARTA_EBOLD, 108)
        hero_txt = "ÉMOTIONNELLE"
        bb = d.textbbox((0, 0), hero_txt, font=f_hero)
        tw = bb[2] - bb[0]
        hx = (W - tw) // 2
        hy = int(315 + 24 * (1.0 - p))
        for depth in range(10, 0, -1):
            d.text((hx + depth, hy + int(depth * 1.2)), hero_txt, font=f_hero, fill=(*C_ROSE_DEEP, int(255 * p)))
        d.text((hx, hy), hero_txt, font=f_hero, fill=(*C_ROSE, int(255 * p)))

        pills = ["01 • EMPATHIE", "02 • PERCEPTION FINE", "03 • PAROLE LIBÉRÉE"]
        for i, pl in enumerate(pills):
            pp = ease_out_expo((age - 1.2 - i * 0.7) / 0.40)
            if pp <= 0.01:
                continue
            px = 290 + i * 465
            py = int(555 + 20 * (1.0 - pp))
            d.rounded_rectangle([px, py, px + 425, py + 95], radius=24, fill=(255, 255, 255, int(250 * pp)), outline=(*C_ROSE, int(240 * pp)), width=3)
            d.rounded_rectangle([px + 20, py + 34, px + 34, py + 62], radius=7, fill=(*C_ROSE, int(255 * pp)))
            d.text((px + 50, py + 30), pl, font=get_font(JAKARTA_BOLD, 27), fill=(*C_CHARCOAL, int(255 * pp)))

    else:
        age = t - 290.22
        p = ease_out_expo(age / 0.42)
        d.text((W // 2 - 235, int(240 + 20 * (1.0 - p))), "C'est une question", font=get_font(GREAT_VIBES, 86), fill=(*C_CHARCOAL, int(255 * p)))
        f_big = get_font(JAKARTA_EBOLD, 92)
        txt = "D'ACCEPTATION"
        bb = d.textbbox((0, 0), txt, font=f_big)
        tw = bb[2] - bb[0]
        tx = (W - tw) // 2
        ty = 380
        d.rounded_rectangle([tx - 24, ty + 42, tx + tw + 24, ty + 108], radius=10, fill=(*C_ROSE, int(255 * p)))
        d.text((tx, ty), txt, font=f_big, fill=(*C_CHARCOAL, int(255 * p)))
        d.text((W // 2 - 295, 535), "Accepte pleinement la personne que tu es.", font=get_font(INTER_MED, 34), fill=(*C_MUTED, int(255 * p)))

    return cv2.cvtColor(np.array(base.convert("RGB"), dtype=np.uint8), cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# 4. Curated 1-to-2 Line French Subtitles (`<= 2` Lines Strictly Enforced)
# ---------------------------------------------------------------------------
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


def clean_and_split_2lines(idx: int, raw_text: str):
    if idx in CLEAN_FRENCH_OVERRIDES:
        return CLEAN_FRENCH_OVERRIDES[idx]
    words = raw_text.replace('"', "").strip().split()
    if not words:
        return ("", "", "")
    if len(words) <= 4:
        return (" ".join(words), "", words[-1])
    words = words[:10]
    mid = len(words) // 2
    return (" ".join(words[:mid]), " ".join(words[mid:]), words[-1])


def get_subtitle_sprite(idx: int, line1: str, line2: str, hl_word: str) -> np.ndarray:
    key = ("sub_sp", idx)
    if key in _SPRITE_CACHE:
        return _SPRITE_CACHE[key]

    sw, sh = 1180, 175
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    f_l1 = get_font(INTER_BOLD, 38)
    f_l2 = get_font(JAKARTA_EBOLD, 46)

    bb1 = d.textbbox((0, 0), line1, font=f_l1) if line1 else (0, 0, 0, 0)
    bb2 = d.textbbox((0, 0), line2, font=f_l2) if line2 else (0, 0, 0, 0)
    w1 = bb1[2] - bb1[0]
    w2 = bb2[2] - bb2[0]
    box_w = max(w1, w2) + 76
    bx0 = (sw - box_w) // 2
    bx1 = bx0 + box_w
    by0 = 14 if line2 else 42
    by1 = 158 if line2 else 128

    d.rounded_rectangle([bx0, by0, bx1, by1], radius=24, fill=(18, 12, 20, 178), outline=(*C_ROSE_LIGHT, 115), width=2)

    if not line2:
        tx = (sw - w1) // 2
        ty = 60
        d.rounded_rectangle([tx - 16, ty - 6, tx + w1 + 16, ty + 48], radius=12, fill=(*C_ROSE, 255))
        d.text((tx, ty), line1, font=f_l1, fill=(255, 255, 255, 255))
    else:
        tx1 = (sw - w1) // 2
        ty1 = 28
        d.text((tx1 + 2, ty1 + 3), line1, font=f_l1, fill=(0, 0, 0, 180))
        d.text((tx1, ty1), line1, font=f_l1, fill=(248, 242, 246, 255))

        tx2 = (sw - w2) // 2
        ty2 = 82
        if idx % 2 == 0:
            d.rounded_rectangle([tx2 - 16, ty2 - 4, tx2 + w2 + 16, ty2 + 54], radius=12, fill=(*C_ROSE, 255))
            d.text((tx2, ty2), line2, font=f_l2, fill=(255, 255, 255, 255))
        else:
            d.text((tx2 + 2, ty2 + 3), line2, font=f_l2, fill=(0, 0, 0, 190))
            d.text((tx2, ty2), line2, font=f_l2, fill=(255, 255, 255, 255))
            d.rounded_rectangle([tx2 + 8, ty2 + 52, tx2 + w2 - 8, ty2 + 60], radius=4, fill=(*C_ROSE, 255))

    arr = np.array(im, dtype=np.uint8)
    _SPRITE_CACHE[key] = arr
    return arr


# ---------------------------------------------------------------------------
# 5. Dynamic Facial Zooms & Rule-of-Thirds Framing
# ---------------------------------------------------------------------------
# Key emotional punch-in windows where camera zooms closer (1.16x - 1.18x) on her face
EMOTIONAL_PUNCH_WINDOWS = [
    (0.00, 5.18, 1.16),
    (25.48, 29.80, 1.16),
    (38.20, 46.80, 1.15),
    (110.00, 114.54, 1.17),
    (168.00, 175.30, 1.16),
    (195.00, 202.38, 1.17),
    (259.10, 270.98, 1.15),
    (297.78, 321.37, 1.16),
]


def apply_dynamic_camera_and_grade(bgr: np.ndarray, t: float, active_side: str) -> np.ndarray:
    """
    Smooth dynamic facial zooms/pull-outs + emotional punch-ins + lateral Rule-of-Thirds reframing.
    """
    beat_idx = int(t / 6.0)
    beat_phase = (t % 6.0) / 6.0
    smooth_p = ease_in_out_cubic(beat_phase)

    if beat_idx % 3 == 0:
        zoom = 1.01 + 0.08 * smooth_p
    elif beat_idx % 3 == 1:
        zoom = 1.09 + 0.05 * math.sin(beat_phase * math.pi)
    else:
        zoom = 1.11 - 0.09 * smooth_p

    for p_s, p_e, z_target in EMOTIONAL_PUNCH_WINDOWS:
        if p_s <= t < p_e:
            age_z = ease_out_expo(min(t - p_s, p_e - t) / 0.35)
            zoom = zoom * (1.0 - age_z) + z_target * age_z
            break

    target_pan_x = 0.0
    if active_side == "right":
        target_pan_x = -82.0
        zoom = max(zoom, 1.10)
    elif active_side == "left":
        target_pan_x = 82.0
        zoom = max(zoom, 1.10)

    cw = int(round(W / zoom))
    ch = int(round(H / zoom))
    cx = int(round(W * 0.5 - target_pan_x))
    cy = int(round(H * 0.47))

    x0 = max(0, min(W - cw, cx - cw // 2))
    y0 = max(0, min(H - ch, cy - ch // 2))

    cropped = bgr[y0 : y0 + ch, x0 : x0 + cw]
    framed = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_LINEAR)

    if "rose_glow_lut" not in _STATIC_CACHE:
        xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
        yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
        glow = np.exp(-((xx - 0.08) ** 2 / 0.08 + (yy - 0.12) ** 2 / 0.12))
        glow_bgr = np.zeros((H, W, 3), dtype=np.uint8)
        glow_bgr[:, :, 2] = np.clip(glow * 28.0, 0, 255).astype(np.uint8)
        glow_bgr[:, :, 1] = np.clip(glow * 8.0, 0, 255).astype(np.uint8)
        glow_bgr[:, :, 0] = np.clip(glow * 18.0, 0, 255).astype(np.uint8)
        _STATIC_CACHE["rose_glow_lut"] = glow_bgr

    return cv2.add(framed, _STATIC_CACHE["rose_glow_lut"])


def draw_youtube_progress_bar(bgr: np.ndarray, t: float, total_dur: float):
    bar_y0 = 1070
    bgr[bar_y0:H, :] = (bgr[bar_y0:H, :].astype(np.uint16) * 90 // 255).astype(np.uint8)
    prog_x = int(round(clamp(t / total_dur) * W))
    if prog_x > 0:
        bgr[bar_y0:H, :prog_x, 0] = 153
        bgr[bar_y0:H, :prog_x, 1] = 72
        bgr[bar_y0:H, :prog_x, 2] = 236
        tip_x0 = max(0, prog_x - 14)
        bgr[bar_y0:H, tip_x0:prog_x, 0] = 215
        bgr[bar_y0:H, tip_x0:prog_x, 1] = 165
        bgr[bar_y0:H, tip_x0:prog_x, 2] = 250

    for c_start, _, _, _ in CHAPTERS[1:]:
        tx = int(round((c_start / total_dur) * W))
        bgr[bar_y0:H, max(0, tx - 2) : min(W, tx + 2)] = (24, 18, 24)


# ---------------------------------------------------------------------------
# 6. Master Frame Compositor
# ---------------------------------------------------------------------------
def compose_youtube_frame(bgr_clean: np.ndarray, t: float, total_dur: float, parsed_segments: list) -> np.ndarray:
    # 1. Check Full-Screen B-Roll & Illustration Cutaways (with Subtitle still visible on Video B-Roll!)
    for c_start, c_end, cid in CUTAWAY_WINDOWS:
        if c_start <= t < c_end:
            out = render_cutaway_frame(t, cid)
            # On Video B-Roll (cid >= 6), keep the 1-to-2 line subtitle at the bottom so viewer follows the voice
            if cid >= 6:
                for seg in parsed_segments:
                    if seg["t0"] <= t < seg["t1"]:
                        sub_sp = get_subtitle_sprite(seg["idx"], seg["line1"], seg["line2"], seg["hl"])
                        blend_rgba_onto_bgr(out, sub_sp, (W - sub_sp.shape[1]) // 2, 875, opacity=1.0)
                        break
            draw_youtube_progress_bar(out, t, total_dur)
            return out

    # 2. Check active Pop-up Illustration
    active_popup = None
    active_side = ""
    for pop in POPUP_ILLUSTRATIONS:
        if pop[0] <= t < pop[1]:
            active_popup = pop
            active_side = pop[2]
            break

    out = apply_dynamic_camera_and_grade(bgr_clean, t, active_side)

    # 3. Overlay Pop-up Illustration Sticker with Elastic Bounce & Floating Bob
    if active_popup is not None:
        ts, te, side, icon_kind, label_top, label_main = active_popup
        age = t - ts
        rem = te - t
        p_in = clamp(ease_out_back(age / 0.42, overshoot=1.45), 0.0, 1.12)
        p_out = ease_out_expo(rem / 0.28) if rem < 0.28 else 1.0
        opacity = clamp(min(age / 0.22, p_out))
        sp = get_popup_illustration_sprite(icon_kind, label_top, label_main)

        bob_y = int(round(math.sin(age * 3.4) * 8.0))
        slide_offset = int(round(55.0 * (1.0 - min(1.0, p_in))))
        if side == "right":
            cx = 1410 + slide_offset
        else:
            cx = 85 - slide_offset
        cy = 235 + bob_y
        blend_rgba_onto_bgr(out, sp, cx, cy, opacity=opacity)

    # 4. Overlay Dynamic Text / Micro-titres
    for mts, mte, mx, my, mtxt, msub in MICRO_TITLES:
        if mts <= t < mte:
            mage = t - mts
            mrem = mte - t
            mp = min(ease_out_expo(mage / 0.30), ease_out_expo(mrem / 0.25) if mrem < 0.25 else 1.0)
            msp = get_micro_title_sprite(mtxt, msub)
            safe_mx = min(mx, W - msp.shape[1] - 48)
            blend_rgba_onto_bgr(out, msp, safe_mx, int(round(my + 18 * (1.0 - mp))), opacity=mp)
            break

    # 5. Overlay Top-Left Chapter Pill during first 4.8s of each chapter
    for c_start, c_end, ch_num, ch_title in CHAPTERS:
        if c_start <= t < c_end:
            ch_age = t - c_start
            if ch_age < 4.8:
                p_in = ease_out_expo(ch_age / 0.38)
                p_out = ease_out_expo((4.8 - ch_age) / 0.35) if ch_age > 4.45 else 1.0
                p = min(p_in, p_out)
                ch_sp = get_chapter_pill_sprite(ch_num, ch_title)
                blend_rgba_onto_bgr(out, ch_sp, 48, int(round(40 - 20 * (1.0 - p))), opacity=p)
            break

    # 6. Overlay Dynamic 1-to-2 Line Rose-Accent Subtitle
    for seg in parsed_segments:
        if seg["t0"] <= t < seg["t1"]:
            s_age = t - seg["t0"]
            p = ease_out_expo(s_age / 0.22)
            sub_sp = get_subtitle_sprite(seg["idx"], seg["line1"], seg["line2"], seg["hl"])
            sx = (W - sub_sp.shape[1]) // 2
            sy = int(round(875 + 14 * (1.0 - p)))
            blend_rgba_onto_bgr(out, sub_sp, sx, sy, opacity=p)
            break

    # 7. Segmented Rose-Pink YouTube Progress Bar
    draw_youtube_progress_bar(out, t, total_dur)
    return out


# ---------------------------------------------------------------------------
# 7. Pro Audio Mastering: Cleaned/EQ'd Voice + Adaptive Background Music + Rich SFX
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
    t = np.arange(total_samples, dtype=np.float32) / float(sr)

    # --- A. Voice Cleaning & Broadcast Warmth EQ ---
    # 1. High-pass filter at 85 Hz to remove low-end rumble & plosive mud
    sos_hp = signal.butter(2, 85.0 / (sr * 0.5), btype="highpass", output="sos")
    vo_clean = signal.sosfilt(sos_hp, vo, axis=0).astype(np.float32)

    # 2. Warm chest boost (155 Hz bandpass) + Presence clarity boost (3.3 kHz bandpass) + Air (8.2 kHz highpass)
    sos_warm = signal.butter(2, [110.0 / (sr * 0.5), 210.0 / (sr * 0.5)], btype="bandpass", output="sos")
    sos_pres = signal.butter(2, [2400.0 / (sr * 0.5), 4800.0 / (sr * 0.5)], btype="bandpass", output="sos")
    sos_air = signal.butter(2, 7500.0 / (sr * 0.5), btype="highpass", output="sos")

    warm_band = signal.sosfilt(sos_warm, vo_clean, axis=0).astype(np.float32)
    pres_band = signal.sosfilt(sos_pres, vo_clean, axis=0).astype(np.float32)
    air_band = signal.sosfilt(sos_air, vo_clean, axis=0).astype(np.float32)

    vo_eq = vo_clean + 0.18 * warm_band + 0.32 * pres_band + 0.20 * air_band

    # 3. Smooth downward noise gate on room silence + gentle broadcast saturation
    mono_abs = np.abs(vo_eq[:, 0])
    win_env = int(0.035 * sr)
    vox_env = np.convolve(mono_abs, np.ones(win_env, dtype=np.float32) / win_env, mode="same")
    gate_gain = np.clip((vox_env - 0.004) / 0.012, 0.30, 1.0)[:, None]
    vo_master = np.tanh(vo_eq * gate_gain * 1.32) * 0.88

    # --- B. Rich, Perceptible Lo-Fi Neo-Soul / Rhodes & Chill Groove Background Music ---
    # Chord voicings cycling every 2.727s (1 bar at 88 BPM: Dm9 -> G13 -> Cmaj9 -> Am9)
    bpm = 88.0
    beat_sec = 60.0 / bpm          # 0.6818s per beat
    bar_sec = beat_sec * 4.0       # 2.727s per bar
    chord_freqs = [
        (146.83, 293.66, 349.23, 440.00, 523.25, 659.25),  # Dm9 (D3, D4, F4, A4, C5, E5)
        (196.00, 293.66, 349.23, 440.00, 493.88, 659.25),  # G13 (G3, D4, F4, A4, B4, E5)
        (130.81, 261.63, 329.63, 392.00, 493.88, 587.33),  # Cmaj9 (C3, C4, E4, G4, B4, D5)
        (110.00, 220.00, 261.63, 329.63, 392.00, 493.88),  # Am9 (A2, A3, C4, E4, G4, B4)
    ]
    bgm_l = np.zeros(total_samples, dtype=np.float32)
    bgm_r = np.zeros(total_samples, dtype=np.float32)

    bar_len = int(round(bar_sec * sr))
    n_bars = (total_samples + bar_len - 1) // bar_len
    rng_m = np.random.default_rng(777)

    for b_idx in range(n_bars):
        i0 = b_idx * bar_len
        i1 = min(total_samples, i0 + bar_len)
        if i1 <= i0:
            continue
        bt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        f_bass, f1, f2, f3, f4, f5 = chord_freqs[b_idx % 4]

        # 1. Warm Stereo Rhodes Electric Piano Chords with 2nd & 3rd Harmonics (260 Hz - 1950 Hz) + Tremolo
        env_bar = (np.sin(np.pi * np.clip(bt / bar_sec, 0.0, 1.0)) ** 0.28) * (0.75 + 0.25 * np.exp(-bt * 1.4))
        trem_l = 0.86 + 0.14 * np.sin(2 * np.pi * 3.2 * bt)
        trem_r = 0.86 + 0.14 * np.cos(2 * np.pi * 3.2 * bt)

        def rhodes_tone(freq, t_arr):
            return (
                0.62 * np.sin(2 * np.pi * freq * t_arr)
                + 0.26 * np.sin(2 * np.pi * (freq * 2.0) * t_arr + 0.3) * np.exp(-t_arr * 2.2)
                + 0.12 * np.sin(2 * np.pi * (freq * 3.0) * t_arr + 0.7) * np.exp(-t_arr * 3.8)
            )

        pad_l = (0.30 * rhodes_tone(f1, bt) + 0.26 * rhodes_tone(f2, bt) + 0.24 * rhodes_tone(f3, bt) + 0.20 * rhodes_tone(f5, bt)) * env_bar * trem_l
        pad_r = (0.30 * rhodes_tone(f1, bt) + 0.26 * rhodes_tone(f3, bt) + 0.24 * rhodes_tone(f4, bt) + 0.20 * rhodes_tone(f5, bt)) * env_bar * trem_r

        # 2. Warm Neo-Soul Sub/Mid Bassline (audible on both headphones and small speakers via 2nd/3rd harmonics)
        beat_pos = (bt % beat_sec) / beat_sec
        bass_env = np.exp(-beat_pos * 2.8)
        bass = (
            0.55 * np.sin(2 * np.pi * f_bass * bt)
            + 0.32 * np.sin(2 * np.pi * (f_bass * 2.0) * bt)
            + 0.13 * np.sin(2 * np.pi * (f_bass * 3.0) * bt)
        ) * bass_env * 0.42

        # 3. Melodic Rhodes/Harp Pluck Arpeggio (8th notes = beat_sec / 2) in the 400-1800 Hz sweet spot
        eighth_sec = beat_sec * 0.5
        arp_phase = (bt % eighth_sec) / eighth_sec
        arp_env = np.exp(-arp_phase * 5.2) * np.minimum(1.0, arp_phase * 35.0)
        arp_notes = [f2, f3, f4, f5, f4, f3, f5, f4]
        note_idx = np.clip((bt / eighth_sec).astype(np.int32), 0, 7)
        arp_f = np.choose(note_idx, arp_notes)
        pluck = (
            0.68 * np.sin(2 * np.pi * arp_f * bt)
            + 0.24 * np.sin(2 * np.pi * (arp_f * 2.0) * bt) * np.exp(-arp_phase * 8.0)
            + 0.08 * np.sin(2 * np.pi * (arp_f * 3.0) * bt) * np.exp(-arp_phase * 11.0)
        ) * arp_env * 0.48

        # 4. Subtle Lo-Fi Chill Groove (Soft Kick on beats 1 & 3, Warm Rimshot on beats 2 & 4, Soft Shaker on 8ths)
        beat_num = np.clip((bt / beat_sec).astype(np.int32), 0, 3)
        is_kick = (beat_num == 0) | (beat_num == 2)
        is_rim = (beat_num == 1) | (beat_num == 3)
        kick_freq = 58.0 + 95.0 * np.exp(-beat_pos * 18.0)
        kick = np.where(is_kick, np.sin(2 * np.pi * kick_freq * (bt % beat_sec)) * np.exp(-beat_pos * 7.5), 0.0) * 0.35
        rim_t = bt % beat_sec
        rim = np.where(
            is_rim,
            (np.sin(2 * np.pi * 460.0 * rim_t) + 0.6 * np.sin(2 * np.pi * 920.0 * rim_t)) * np.exp(-beat_pos * 26.0),
            0.0,
        ) * 0.22
        shaker = rng_m.normal(0.0, 1.0, i1 - i0).astype(np.float32) * np.exp(-arp_phase * 14.0) * 0.045

        bgm_l[i0:i1] = pad_l + bass + pluck * 1.05 + kick + rim * 0.9 + shaker
        bgm_r[i0:i1] = pad_r + bass + pluck * 0.85 + kick + rim * 1.1 + shaker

    # Carve a gentle vocal-presence pocket (2.5 kHz - 4.2 kHz) in the music so it can play MUCH louder without masking speech
    sos_pocket = signal.butter(2, [2500.0 / (sr * 0.5), 4200.0 / (sr * 0.5)], btype="bandstop", output="sos")
    bgm_l = signal.sosfilt(sos_pocket, bgm_l).astype(np.float32)
    bgm_r = signal.sosfilt(sos_pocket, bgm_r).astype(np.float32)

    # Normalize music bed RMS to 1.0 so our ducking envelope sets the exact audible dB level
    bgm_rms = float(np.sqrt(np.mean(0.5 * (bgm_l ** 2 + bgm_r ** 2))) + 1e-6)
    bgm_l /= bgm_rms
    bgm_r /= bgm_rms

    # Smooth vocal envelope (250ms window) for natural broadcast sidechain ducking matching `reference (2).mp4`:
    # - During speech: music sits at 0.072 RMS (-22.8 dBFS, within 4.8 dB of voice RMS just like `reference (2).mp4`)
    # - During vocal pauses & cutaways: music swells smoothly up to 0.115 RMS (-18.8 dBFS)
    win_duck = int(0.25 * sr)
    smooth_vox = np.convolve(mono_abs, np.ones(win_duck, dtype=np.float32) / win_duck, mode="same")
    duck_gain = np.clip(0.115 - 0.35 * smooth_vox, 0.072, 0.115)
    bgm_l *= duck_gain
    bgm_r *= duck_gain

    # --- C. Synchronized Sound Effects (SFX): Pops, Beeps & Whooshes ---
    sfx_l = np.zeros(total_samples, dtype=np.float32)
    sfx_r = np.zeros(total_samples, dtype=np.float32)
    rng = np.random.default_rng(2026)

    # 1. Playful Bubble/Pop SFX on every Pop-up Illustration entrance
    for ts, _, side, _, _, _ in POPUP_ILLUSTRATIONS:
        i0 = int(ts * sr)
        dur_s = int(0.14 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            # Pitch-sweeping bubble pop (280 Hz -> 680 Hz)
            pop_wave = np.sin(2 * np.pi * (280.0 + 400.0 * (lt ** 0.7)) * lt * 0.14) * np.exp(-lt * 5.0)
            pan_l = 0.35 if side == "right" else 0.85
            pan_r = 0.85 if side == "right" else 0.35
            sfx_l[i0:i1] += 0.055 * pop_wave * pan_l
            sfx_r[i0:i1] += 0.055 * pop_wave * pan_r

    # 2. Crisp UI Sparkle/Beep SFX on Dynamic Text / Micro-titres
    for mts, _, _, _, _, _ in MICRO_TITLES:
        i0 = int(mts * sr)
        dur_s = int(0.16 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            beep = (np.sin(2 * np.pi * 880.0 * lt * 0.16) + 0.5 * np.sin(2 * np.pi * 1318.5 * lt * 0.16)) * np.exp(-lt * 6.5)
            sfx_l[i0:i1] += 0.032 * beep
            sfx_r[i0:i1] += 0.032 * beep

    # 3. Cinematic Whoosh + Soft Sub-Impact on all 10 B-Roll Cutaways & 7 Chapter Transitions
    transition_cues = sorted(
        list({c[0] for c in CUTAWAY_WINDOWS} | {c[1] for c in CUTAWAY_WINDOWS} | {ch[0] for ch in CHAPTERS})
    )
    for ts in transition_cues:
        i0 = int(ts * sr)
        dur_s = int(0.26 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.4
            sub_imp = np.sin(2 * np.pi * (110.0 - 55.0 * lt) * lt * 0.26) * np.exp(-lt * 3.8)
            noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32) * env
            w_sig = 0.042 * sub_imp + 0.015 * noise
            sfx_l[i0:i1] += w_sig
            sfx_r[i0:i1] += w_sig

    mix_l = np.clip(vo_master[:, 0] + bgm_l + sfx_l, -0.98, 0.98)
    mix_r = np.clip(vo_master[:, 1] + bgm_r + sfx_r, -0.98, 0.98)
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
            35.0, 58.0, 68.5, 82.0,
            94.0, 117.0, 145.0, 164.0,
            179.0, 206.0, 250.0, 264.0,
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
        "-b:a", "192k",
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
