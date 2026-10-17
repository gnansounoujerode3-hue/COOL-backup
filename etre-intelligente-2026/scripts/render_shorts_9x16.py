#!/usr/bin/env python3
"""
Vertical 9:16 (1080x1920, 30fps) Reels / YouTube Shorts / TikTok Generator (v2)
for: 'Être Intelligente En 2026 Te Dessert'

Updates per user feedback:
1. Hook Header at start of each Short: NO background box and NO 'REEL #01 • ...' badge — just the bold title directly on the video.
2. B-Roll Cutaway Cards: NO 'B-ROLL • ...' badge (and no 'ILLUSTRATION' meta-tag on the cutaway icon).
3. Removed 'ABONNE-TOI • PARTIE X/6' pill from all Shorts.
4. Subtitles: Removed the framing box around subtitles, added a smooth dark gradient at the bottom of the Reels, and increased subtitle font size (48px ExtraBold with crisp shadow/stroke + Rose highlight pill, max 2 lines).
5. Pop-ups: Increased the size of the 3D/vector Pop-up Illustrations by ~32% (554x422).
6. Short #6 starts cleanly on A-Roll at t=224.74s ('Je préfère mille fois écouter une personne qui explique les choses avec simplicité...') through t=270.98s ('parle face cam comme à ta pote, fais exactement la même chose !').
"""

import json
import math
import os
import subprocess
import sys
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))

from render_youtube_edit import (
    CLEAN_FRENCH_OVERRIDES,
    POPUP_ILLUSTRATIONS,
    EMOTIONAL_PUNCH_WINDOWS,
    CUTAWAY_WINDOWS,
    C_ROSE,
    C_ROSE_LIGHT,
    C_ROSE_DEEP,
    C_ROSE_BLUSH,
    C_CHARCOAL,
    C_MUTED as C_SLATE,
    JAKARTA_EBOLD,
    JAKARTA_BOLD,
    INTER_MED,
    INTER_BOLD as INTER_SEMI,
    GREAT_VIBES as SERIF_ITALIC,
    MONO_MED,
    get_font,
    clamp,
    ease_out_expo,
    ease_out_back,
    ease_in_out_cubic,
    get_popup_illustration_sprite,
    build_youtube_audio,
)

CLEAN_VIDEO = os.path.join(PROJECT_DIR, "film", "etre-intelligente-en-2026-sans-sous-titres-1080p.mp4")
SEGMENTS_JSON = os.path.join(PROJECT_DIR, "assets", "segments.json")
SHORTS_DIR = os.path.join(PROJECT_DIR, "shorts")

SW, SH = 1080, 1920
FPS = 30.0

# ---------------------------------------------------------------------------
# Definition of the 6 Viral Reels / Shorts / TikToks (9:16, 1080x1920)
# ---------------------------------------------------------------------------
SHORTS_SPECS = [
    {
        "id": 1,
        "slug": "short-01-paraitre-intelligente-te-dessert-9x16.mp4",
        "t_start": 0.00,
        "t_end": 38.20,
        "hook_line1": "VOULOIR PARAÎTRE INTELLIGENTE",
        "hook_line2": "TE DESSERT PARTOUT",
    },
    {
        "id": 2,
        "slug": "short-02-le-piege-du-perfectionnisme-9x16.mp4",
        "t_start": 38.20,
        "t_end": 75.62,
        "hook_line1": "POURQUOI TOUT CONTRÔLER",
        "hook_line2": "CRÉE ENCORE PLUS DE PEUR",
    },
    {
        "id": 3,
        "slug": "short-03-percer-sans-tout-calculer-9x16.mp4",
        "t_start": 75.62,
        "t_end": 119.98,
        "hook_line1": "CEUX QUI NE CALCULENT RIEN",
        "hook_line2": "PERCENT SUR LES RÉSEAUX",
    },
    {
        "id": 4,
        "slug": "short-04-parler-avec-le-coeur-vs-etre-lisse-9x16.mp4",
        "t_start": 134.30,
        "t_end": 184.46,
        "hook_line1": "LES GENS N'AIMENT PAS",
        "hook_line2": "LES VIDÉOS TROP LISSES",
    },
    {
        "id": 5,
        "slug": "short-05-la-vraie-intelligence-emotionnelle-9x16.mp4",
        "t_start": 184.46,
        "t_end": 224.74,
        "hook_line1": "LA VRAIE INTELLIGENCE",
        "hook_line2": "EST ÉMOTIONNELLE",
    },
    {
        "id": 6,
        "slug": "short-06-parle-face-cam-comme-a-ta-pote-9x16.mp4",
        "t_start": 224.74,
        "t_end": 270.98,
        "hook_line1": "PARLE FACE CAMÉRA",
        "hook_line2": "COMME À TA MEILLEURE POTE",
    },
]

_SHORT_CACHE = {}
_TRACKED_CX = [920.0]

# Precompute smooth bottom darkening gradient multiplier (1920x1)
# Slightly darkens y = 1280..1920 so frameless subtitles pop cleanly
_BOTTOM_GRAD = np.ones((SH, 1, 1), dtype=np.float32)
_y_idx = np.linspace(0.0, 1.0, SH - 1260, dtype=np.float32)
_BOTTOM_GRAD[1260:, 0, 0] = 1.0 - 0.52 * (_y_idx ** 1.35)


def blend_rgba_onto_bgr(bgr: np.ndarray, sprite_rgba: np.ndarray, x0: int, y0: int, opacity: float = 1.0):
    """Fast in-place NumPy alpha-blend of an RGBA sprite onto a BGR frame of any resolution."""
    if opacity <= 0.01:
        return
    bh, bw = bgr.shape[:2]
    sh, sw = sprite_rgba.shape[:2]
    fx0 = max(0, x0)
    fy0 = max(0, y0)
    fx1 = min(bw, x0 + sw)
    fy1 = min(bh, y0 + sh)
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
    bgr[fy0:fy1, fx0:fx1] = ((src_bgr * a + dst * (256 - a)) >> 8).astype(np.uint8)


def get_large_popup_sprite(icon_kind: str, label_top: str, label_main: str, scale: float = 1.30) -> np.ndarray:
    """Returns an enlarged (1.30x = 546x416) 3D/vector Pop-up Illustration sprite for mobile 9:16."""
    key = ("large_popup_v2", icon_kind, label_top, label_main, round(scale, 2))
    if key in _SHORT_CACHE:
        return _SHORT_CACHE[key]
    base_sp = get_popup_illustration_sprite(icon_kind, label_top, label_main)
    bh, bw = base_sp.shape[:2]
    nw, nh = int(round(bw * scale)), int(round(bh * scale))
    large_sp = cv2.resize(base_sp, (nw, nh), interpolation=cv2.INTER_CUBIC)
    _SHORT_CACHE[key] = large_sp
    return large_sp


def get_short_paper_bg() -> np.ndarray:
    if "paper_9x16" in _SHORT_CACHE:
        return _SHORT_CACHE["paper_9x16"]
    xx = np.linspace(0.0, 1.0, SW, dtype=np.float32)[None, :]
    yy = np.linspace(0.0, 1.0, SH, dtype=np.float32)[:, None]
    diag = np.sin((xx * 2.2 + yy * 3.8) * math.pi) * 0.5 + 0.5
    blush = np.exp(-((xx - 0.5) ** 2 / 0.25 + (yy - 0.35) ** 2 / 0.25))
    r = np.clip(250.0 + 4.0 * blush - 6.0 * (1.0 - diag), 0, 255).astype(np.uint8)
    g = np.clip(244.0 - 8.0 * blush - 8.0 * (1.0 - diag), 0, 255).astype(np.uint8)
    b = np.clip(248.0 - 3.0 * blush - 5.0 * (1.0 - diag), 0, 255).astype(np.uint8)
    im = Image.fromarray(np.stack([b, g, r], axis=-1), mode="RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for gx in range(90, SW, 90):
        d.line([(gx, 120), (gx, SH - 120)], fill=(236, 72, 153, 18), width=1)
    for gy in range(120, SH - 119, 90):
        d.line([(60, gy), (SW - 60, gy)], fill=(236, 72, 153, 18), width=1)
    arr = np.array(im, dtype=np.uint8)
    _SHORT_CACHE["paper_9x16"] = arr
    return arr


def get_short_dark_bg() -> np.ndarray:
    if "dark_9x16" in _SHORT_CACHE:
        return _SHORT_CACHE["dark_9x16"]
    xx = np.linspace(0.0, 1.0, SW, dtype=np.float32)[None, :]
    yy = np.linspace(0.0, 1.0, SH, dtype=np.float32)[:, None]
    orb1 = np.exp(-((xx - 0.25) ** 2 / 0.12 + (yy - 0.28) ** 2 / 0.12))
    orb2 = np.exp(-((xx - 0.78) ** 2 / 0.14 + (yy - 0.72) ** 2 / 0.14))
    r = np.clip(24.0 + 78.0 * orb1 + 56.0 * orb2, 0, 255).astype(np.uint8)
    g = np.clip(15.0 + 22.0 * orb1 + 18.0 * orb2, 0, 255).astype(np.uint8)
    b = np.clip(22.0 + 52.0 * orb1 + 42.0 * orb2, 0, 255).astype(np.uint8)
    im = Image.fromarray(np.stack([b, g, r], axis=-1), mode="RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for gx in range(90, SW, 90):
        d.line([(gx, 140), (gx, SH - 140)], fill=(244, 114, 182, 22), width=1)
    for gy in range(140, SH - 139, 90):
        d.line([(60, gy), (SW - 60, gy)], fill=(244, 114, 182, 22), width=1)
    arr = np.array(im, dtype=np.uint8)
    _SHORT_CACHE["dark_9x16"] = arr
    return arr


def get_hook_title_sprite(l1: str, l2: str) -> np.ndarray:
    """
    Renders ONLY the 2-line Hook Title directly on the video:
    - NO dark background box
    - NO 'REEL #01 • ...' badge
    """
    key = ("hook_clean_v2", l1, l2)
    if key in _SHORT_CACHE:
        return _SHORT_CACHE[key]
    cw, ch = 1020, 210
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Line 1: Bold white text with crisp dark stroke + drop shadow directly over the video
    f_1 = get_font(JAKARTA_EBOLD, 44)
    w1 = d.textbbox((0, 0), l1, font=f_1)[2]
    x1 = (cw - w1) // 2
    y1 = 22
    d.text((x1, y1 + 4), l1, font=f_1, fill=(16, 10, 16, 180), stroke_width=8, stroke_fill=(16, 10, 16, 180))
    d.text((x1, y1), l1, font=f_1, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(24, 16, 24, 245))

    # Line 2: Glowing Rose #EC4899 pill with bold white text
    f_2 = get_font(JAKARTA_EBOLD, 44)
    w2 = d.textbbox((0, 0), l2, font=f_2)[2]
    px = (cw - w2) // 2
    py = 96
    d.rounded_rectangle([px - 26, py + 6, px + w2 + 26, py + 76], radius=22, fill=(16, 10, 16, 110))
    d.rounded_rectangle([px - 26, py, px + w2 + 26, py + 70], radius=22, fill=(*C_ROSE, 255), outline=(255, 255, 255, 220), width=3)
    d.text((px, py + 9), l2, font=f_2, fill=(255, 255, 255, 255))

    arr = np.array(im, dtype=np.uint8)
    _SHORT_CACHE[key] = arr
    return arr


def get_short_subtitle_sprite(seg_idx: int, line1: str, line2: str, hl: str) -> np.ndarray:
    """
    Renders strict <= 2-line French subtitle WITHOUT any framing box,
    in large 48px ExtraBold typography with crisp stroke/drop-shadow and Rose keyword pill.
    """
    key = ("sub_frameless_v2", seg_idx, line1, line2, hl)
    if key in _SHORT_CACHE:
        return _SHORT_CACHE[key]

    lines = [l for l in [line1.strip(), line2.strip()] if l][:2]

    # Pick largest font size (up to 54px) that fits comfortably within 1000px width
    font_size = 54
    tmp = Image.new("RGBA", (10, 10))
    dt = ImageDraw.Draw(tmp)
    while font_size >= 38:
        f_test = get_font(JAKARTA_EBOLD, font_size)
        max_w = max([dt.textbbox((0, 0), l, font=f_test)[2] for l in lines]) if lines else 300
        if max_w <= 980:
            break
        font_size -= 2

    f_sub = get_font(JAKARTA_EBOLD, font_size)
    cw, ch = SW, 230
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    line_step = int(round(font_size * 1.40))
    start_y = 60 if len(lines) == 1 else 24

    for i, line in enumerate(lines):
        bb = d.textbbox((0, 0), line, font=f_sub)
        lw = bb[2] - bb[0]
        lx = (cw - lw) // 2
        ly = start_y + i * line_step

        # Highlight pill on the keyword of the active last line
        if i == len(lines) - 1 and hl and hl.lower() in line.lower():
            idx_pos = line.lower().find(hl.lower())
            prefix = line[:idx_pos]
            match_str = line[idx_pos : idx_pos + len(hl)]
            pw = d.textbbox((0, 0), prefix, font=f_sub)[2] if prefix else 0
            mw = d.textbbox((0, 0), match_str, font=f_sub)[2]
            hx0 = lx + pw - 14
            hy0 = ly - 4
            hx1 = lx + pw + mw + 14
            hy1 = ly + int(round(font_size * 1.24))
            d.rounded_rectangle([hx0, hy0 + 5, hx1, hy1 + 5], radius=16, fill=(0, 0, 0, 120))
            d.rounded_rectangle([hx0, hy0, hx1, hy1], radius=16, fill=(*C_ROSE, 255))

        # Crisp soft shadow + dark outline stroke so frameless white text pops on any background
        d.text((lx, ly + 4), line, font=f_sub, fill=(0, 0, 0, 185), stroke_width=7, stroke_fill=(0, 0, 0, 185))
        d.text((lx, ly), line, font=f_sub, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(18, 12, 18, 240))

    arr = np.array(im, dtype=np.uint8)
    _SHORT_CACHE[key] = arr
    return arr


def render_vertical_cutaway(t: float, cutaway_id: int) -> np.ndarray:
    """Renders full-screen 1080x1920 vertical Motion-Design & B-Roll cutaways (NO 'B-ROLL • ...' badge)."""
    if cutaway_id >= 6:
        broll_specs = {
            6: (32.90, "trophy_megaphone", "VALIDATION ?", "APPROBATION", "PROUVER QU'ON EST", "« GÉNIALE »", "Chercher la validation des autres épuise ta confiance"),
            7: (90.22, "magnet_hearts", "AIMANT NATUREL", "FORCE DU VRAI", "PERCER SANS", "CONCEPT PARFAIT", "Ceux qui restent 100% eux-mêmes attirent l'audience"),
            8: (141.58, "stiff_robot", "ZÉRO ÉMOTION", "TROP CARRÉ", "LE PIÈGE DES RÉELS", "TROP LISSES", "Un discours robotique coupe toute connexion humaine"),
            9: (175.30, "flaming_heart_mic", "VRAIE CONNEXION", "AVEC LE CŒUR", "PARTAGER SON VÉCU", "& SA PASSION", "L'audience choisit toujours la sincérité et le vécu"),
            10: (245.22, "clinking_cups", "5 MIN CHRONO", "SPONTANÉITÉ", "5 MIN SPONTANÉES", "> 2H DE SCRIPT", "Allume ta caméra et parle comme à ta meilleure pote !"),
        }
        t0_b, ic_kind, ic_badge, ic_top, hl1, hl2, subline = broll_specs[cutaway_id]
        age = max(0.0, t - t0_b)
        bgr = get_short_dark_bg().copy()
        p = ease_out_expo(age / 0.40)

        # Enlarged 3D Pop-up Medallion above the card
        sp_ic = get_large_popup_sprite(ic_kind, ic_top, ic_badge, scale=1.28)
        blend_rgba_onto_bgr(bgr, sp_ic, (SW - sp_ic.shape[1]) // 2, int(210 + 35 * (1.0 - p)), opacity=p)

        # Card WITHOUT 'B-ROLL • ...' top badge
        card_im = Image.new("RGBA", (940, 480), (0, 0, 0, 0))
        d = ImageDraw.Draw(card_im)
        d.rounded_rectangle([0, 0, 939, 479], radius=38, fill=(32, 20, 30, 242), outline=(*C_ROSE, 245), width=3)

        f_h = get_font(JAKARTA_EBOLD, 54)
        w1 = d.textbbox((0, 0), hl1, font=f_h)[2]
        w2 = d.textbbox((0, 0), hl2, font=f_h)[2]
        d.text(((940 - w1) // 2, 68), hl1, font=f_h, fill=(255, 255, 255, 255))
        d.rounded_rectangle([(940 - w2) // 2 - 24, 146, (940 + w2) // 2 + 24, 220], radius=20, fill=(*C_ROSE, 255))
        d.text(((940 - w2) // 2, 152), hl2, font=f_h, fill=(255, 255, 255, 255))

        f_s = get_font(INTER_MED, 29)
        ws = d.textbbox((0, 0), subline, font=f_s)[2]
        d.text(((940 - ws) // 2, 272), subline, font=f_s, fill=(*C_ROSE_BLUSH, 255))

        bar_w = int(760 * ease_out_expo(max(0.0, age - 0.20) / 0.85))
        d.rounded_rectangle([90, 374, 850, 408], radius=17, fill=(52, 34, 48, 255))
        if bar_w > 16:
            d.rounded_rectangle([90, 374, 90 + bar_w, 408], radius=17, fill=(*C_ROSE, 255))

        blend_rgba_onto_bgr(bgr, np.array(card_im, dtype=np.uint8), (SW - 940) // 2, int(690 + 30 * (1.0 - p)), opacity=p)
        return bgr

    bgr = get_short_paper_bg().copy()
    im = Image.fromarray(bgr[:, :, ::-1], mode="RGB").convert("RGBA")
    d = ImageDraw.Draw(im)

    if cutaway_id == 1:
        age = max(0.0, t - 5.18)
        f_sub = get_font(INTER_SEMI, 32)
        f_big = get_font(JAKARTA_EBOLD, 54)
        s1 = "Vouloir paraître intelligente"
        s2 = "TE DESSERT PARTOUT"
        w1 = d.textbbox((0, 0), s1, font=f_sub)[2]
        w2 = d.textbbox((0, 0), s2, font=f_big)[2]
        d.text(((SW - w1) // 2, 210), s1, font=f_sub, fill=(*C_SLATE, 255))
        d.rounded_rectangle([(SW - w2) // 2 - 24, 268, (SW + w2) // 2 + 24, 346], radius=20, fill=(*C_ROSE, 255))
        d.text(((SW - w2) // 2, 276), s2, font=f_big, fill=(255, 255, 255, 255))

        cards = [
            ("01", "DANS TA VIE", "Pression de performer dès le réveil", 0.15),
            ("02", "DANS TON BUSINESS", "Bloque ton authenticité & tes ventes", 0.85),
            ("03", "TES RELATIONS", "Empêche d'être aimée pour qui tu es", 1.55),
        ]
        for idx, (num, title, desc, delay) in enumerate(cards):
            p = clamp(ease_out_back((age - delay) / 0.45), 0.0, 1.0)
            if p <= 0.01:
                continue
            cy = int(420 + idx * 280 + 35 * (1.0 - p))
            d.rounded_rectangle([96, cy + 10, SW - 84, cy + 240], radius=30, fill=(*C_ROSE, int(45 * p)))
            d.rounded_rectangle([88, cy, SW - 92, cy + 230], radius=30, fill=(255, 255, 255, int(252 * p)), outline=(*C_ROSE, int(245 * p)), width=3)
            d.rounded_rectangle([128, cy + 34, 210, cy + 84], radius=16, fill=(*C_ROSE, int(255 * p)))
            d.text((148, cy + 44), num, font=get_font(MONO_MED, 26), fill=(255, 255, 255, int(255 * p)))
            d.text((238, cy + 40), title, font=get_font(JAKARTA_EBOLD, 36), fill=(*C_CHARCOAL, int(255 * p)))
            d.text((128, cy + 125), desc, font=get_font(INTER_MED, 28), fill=(*C_SLATE, int(255 * p)))

    elif cutaway_id == 2:
        age = max(0.0, t - 64.20)
        f_it = get_font(SERIF_ITALIC, 48)
        f_big = get_font(JAKARTA_EBOLD, 48)
        s1 = "Le piège du perfectionnisme"
        s2 = "LA RÉACTION EN CHAÎNE"
        w1 = d.textbbox((0, 0), s1, font=f_it)[2]
        w2 = d.textbbox((0, 0), s2, font=f_big)[2]
        d.text(((SW - w1) // 2, 185), s1, font=f_it, fill=(*C_ROSE_DEEP, 255))
        d.text(((SW - w2) // 2, 250), s2, font=f_big, fill=(*C_CHARCOAL, 255))

        chain = [
            ("ÉTAPE 01", "PERFECTIONNISME", "Tout vouloir carré & lisse", False, 0.15),
            ("ÉTAPE 02", "CONTRÔLE ABSOLU", "Zéro lâcher-prise", False, 1.35),
            ("ÉTAPE 03", "RÉSISTANCE", "Tension intérieure permanente", False, 2.85),
            ("ÉTAPE 04", "PEUR & INSÉCURITÉ", "Paralysie face au regard des autres", True, 4.50),
        ]
        for idx, (st, title, sub, is_final, delay) in enumerate(chain):
            p = clamp(ease_out_back((age - delay) / 0.45), 0.0, 1.0)
            if p <= 0.01:
                continue
            cy = int(350 + idx * 235 + 30 * (1.0 - p))
            bg_c = (*C_ROSE, int(255 * p)) if is_final else (255, 255, 255, int(252 * p))
            fg_m = (255, 255, 255, int(255 * p)) if is_final else (*C_CHARCOAL, int(255 * p))
            fg_s = (255, 235, 245, int(255 * p)) if is_final else (*C_SLATE, int(255 * p))
            d.rounded_rectangle([88, cy, SW - 88, cy + 200], radius=28, fill=bg_c, outline=(*C_ROSE_DEEP, int(255 * p)), width=3)
            d.text((128, cy + 26), st, font=get_font(MONO_MED, 21), fill=fg_s)
            d.text((128, cy + 66), title, font=get_font(JAKARTA_EBOLD, 36), fill=fg_m)
            d.text((128, cy + 128), sub, font=get_font(INTER_MED, 26), fill=fg_s)

    elif cutaway_id == 3:
        age = max(0.0, t - 114.54)
        f_it = get_font(SERIF_ITALIC, 54)
        s1 = "La loi de l'authenticité"
        w1 = d.textbbox((0, 0), s1, font=f_it)[2]
        d.text(((SW - w1) // 2, 220), s1, font=f_it, fill=(*C_ROSE_DEEP, 255))

        p1 = ease_out_expo((age - 0.1) / 0.45)
        if p1 > 0.01:
            y1 = int(360 + 30 * (1.0 - p1))
            d.rounded_rectangle([88, y1, SW - 88, y1 + 370], radius=34, fill=(255, 255, 255, int(252 * p1)), outline=(*C_CHARCOAL, int(220 * p1)), width=3)
            d.text((135, y1 + 55), "QUAND TU SUR-CALCULES TOUT", font=get_font(MONO_MED, 24), fill=(*C_SLATE, int(255 * p1)))
            d.text((135, y1 + 130), "+ DE CALCUL ↑", font=get_font(JAKARTA_EBOLD, 64), fill=(*C_CHARCOAL, int(255 * p1)))
            d.text((135, y1 + 245), "Chaque mot et chaque geste est forcé", font=get_font(INTER_MED, 30), fill=(*C_SLATE, int(255 * p1)))

        p2 = ease_out_expo((age - 1.1) / 0.45)
        if p2 > 0.01:
            y2 = int(810 + 30 * (1.0 - p2))
            d.rounded_rectangle([88, y2, SW - 88, y2 + 370], radius=34, fill=(*C_ROSE, int(252 * p2)), outline=(*C_ROSE_DEEP, int(255 * p2)), width=3)
            d.text((135, y2 + 55), "LE RÉSULTAT DIRECT", font=get_font(MONO_MED, 24), fill=(255, 235, 245, int(255 * p2)))
            d.text((135, y2 + 130), "- D'AUTHENTICITÉ ↓", font=get_font(JAKARTA_EBOLD, 60), fill=(255, 255, 255, int(255 * p2)))
            d.text((135, y2 + 245), "Tu n'as même plus l'impression d'être toi", font=get_font(INTER_MED, 30), fill=(255, 240, 248, int(255 * p2)))

    elif cutaway_id == 4:
        age = max(0.0, t - 202.38)
        f_top = get_font(INTER_SEMI, 32)
        f_big = get_font(JAKARTA_EBOLD, 76)
        s1 = "En 2026, la vraie intelligence est"
        s2 = "ÉMOTIONNELLE"
        w1 = d.textbbox((0, 0), s1, font=f_top)[2]
        w2 = d.textbbox((0, 0), s2, font=f_big)[2]
        d.text(((SW - w1) // 2, 230), s1, font=f_top, fill=(*C_SLATE, 255))
        d.text(((SW - w2) // 2 + 5, 305 + 5), s2, font=f_big, fill=(*C_ROSE_DEEP, 255))
        d.text(((SW - w2) // 2, 305), s2, font=f_big, fill=(*C_ROSE, 255))

        pills = [
            ("01 • EMPATHIE PROFONDE", "Ressentir sincèrement les émotions", 0.8),
            ("02 • PERCEPTION FINE", "Voir ce que les autres ne voient pas", 2.4),
            ("03 • PAROLE LIBÉRÉE", "Venir telle que tu es, sans masque", 4.0),
        ]
        for idx, (lbl, desc, delay) in enumerate(pills):
            p = clamp(ease_out_back((age - delay) / 0.45), 0.0, 1.0)
            if p <= 0.01:
                continue
            cy = int(470 + idx * 255 + 30 * (1.0 - p))
            d.rounded_rectangle([88, cy, SW - 88, cy + 210], radius=32, fill=(255, 255, 255, int(252 * p)), outline=(*C_ROSE, int(245 * p)), width=3)
            d.text((135, cy + 45), lbl, font=get_font(JAKARTA_EBOLD, 36), fill=(*C_ROSE_DEEP, int(255 * p)))
            d.text((135, cy + 120), desc, font=get_font(INTER_MED, 28), fill=(*C_SLATE, int(255 * p)))

    elif cutaway_id == 5:
        age = max(0.0, t - 290.22)
        f_it = get_font(SERIF_ITALIC, 52)
        f_big = get_font(JAKARTA_EBOLD, 72)
        s1 = "Tout commence par une"
        s2 = "ACCEPTATION"
        w1 = d.textbbox((0, 0), s1, font=f_it)[2]
        w2 = d.textbbox((0, 0), s2, font=f_big)[2]
        d.text(((SW - w1) // 2, 340), s1, font=f_it, fill=(*C_SLATE, 255))
        d.rounded_rectangle([(SW - w2) // 2 - 32, 430, (SW + w2) // 2 + 32, 545], radius=28, fill=(*C_ROSE, 255))
        d.text(((SW - w2) // 2, 444), s2, font=f_big, fill=(255, 255, 255, 255))

        s3 = "Sois 100% la même personne"
        s4 = "face caméra et dans la vraie vie."
        f_m = get_font(JAKARTA_BOLD, 38)
        w3 = d.textbbox((0, 0), s3, font=f_m)[2]
        w4 = d.textbbox((0, 0), s4, font=f_m)[2]
        d.text(((SW - w3) // 2, 650), s3, font=f_m, fill=(*C_CHARCOAL, 255))
        d.text(((SW - w4) // 2, 710), s4, font=f_m, fill=(*C_ROSE_DEEP, 255))

    rgb = np.array(im.convert("RGB"), dtype=np.uint8)
    return rgb[:, :, ::-1].copy()


def crop_and_grade_9x16(bgr_16x9: np.ndarray, t: float, local_t: float = 10.0, reset_tracker: bool = False) -> tuple:
    """
    Crops 1920x1080 source into a vertical 9:16 (1080x1920) frame dynamically centered on the speaker,
    applying emotional punch-zooms, smooth breathing zoom, and warm Rose LUT.
    """
    h_src, w_src = bgr_16x9.shape[:2]

    roi = bgr_16x9[60:640, 520:1440]
    mask = roi.mean(axis=2) < 55
    ys, xs = np.where(mask)
    if len(xs) > 400:
        raw_cx = float(np.median(xs) + 520)
        head_top_y = int(np.percentile(ys, 5) + 60)
    else:
        raw_cx = _TRACKED_CX[0]
        head_top_y = 260

    if reset_tracker:
        _TRACKED_CX[0] = raw_cx
    else:
        _TRACKED_CX[0] = 0.90 * _TRACKED_CX[0] + 0.10 * raw_cx

    cycle = (t % 11.0) / 11.0
    smooth_wave = math.sin(cycle * math.pi)
    zoom = 1.00 + 0.035 * ease_in_out_cubic(smooth_wave)

    if local_t >= 3.6:
        for w_start, w_end, w_zoom in EMOTIONAL_PUNCH_WINDOWS:
            if w_start <= t <= w_end:
                p_in = ease_out_expo((t - w_start) / 0.32)
                p_out = ease_out_expo((w_end - t) / 0.35) if (w_end - t) < 0.35 else 1.0
                capped_z = min(w_zoom, 1.09)
                zoom = max(zoom, 1.0 + (capped_z - 1.0) * min(p_in, p_out))
                break
    else:
        # Keep zoom at 1.00 during the opening Hook Title so there is maximum space above her head
        zoom = 1.00

    crop_h = int(round(h_src / zoom))
    crop_w = int(round(crop_h * (SW / SH)))

    cx = int(round(_TRACKED_CX[0]))
    cy = int(round(h_src * 0.44)) if head_top_y < 230 else int(round(h_src * 0.50))

    x0 = int(clamp(cx - crop_w // 2, 0, w_src - crop_w))
    y0 = int(clamp(cy - crop_h // 2, 0, h_src - crop_h))

    cropped = bgr_16x9[y0 : y0 + crop_h, x0 : x0 + crop_w]
    vertical = cv2.resize(cropped, (SW, SH), interpolation=cv2.INTER_CUBIC)

    out = vertical.copy()
    out[:, :, 2] = cv2.add(out[:, :, 2], 4)
    out[:, :, 0] = cv2.add(out[:, :, 0], 2)
    return out, head_top_y


def compose_short_frame(bgr_16x9: np.ndarray, t: float, spec: dict, parsed_segments: list, reset_tracker: bool = False) -> np.ndarray:
    local_t = t - spec["t_start"]
    short_dur = spec["t_end"] - spec["t_start"]

    # 1. Check Full-Screen Vertical 9:16 B-Roll & Illustration Cutaways
    in_cutaway = False
    head_top_y = 260
    for c_start, c_end, cid in CUTAWAY_WINDOWS:
        if c_start <= t < c_end:
            out = render_vertical_cutaway(t, cid)
            in_cutaway = True
            break

    if not in_cutaway:
        out, head_top_y = crop_and_grade_9x16(bgr_16x9, t, local_t=local_t, reset_tracker=reset_tracker)

    # 2. Slightly darken the bottom of the Reel (y = 1260..1920) so frameless subtitles pop
    out[1260:, :, :] = (out[1260:, :, :].astype(np.float32) * _BOTTOM_GRAD[1260:]).astype(np.uint8)

    # 3. Clean Frameless Hook Title during first 3.6s of the Short (NO background box, NO 'REEL #01' badge)
    if local_t < 3.6 and not in_cutaway:
        hp_in = ease_out_back(local_t / 0.40, overshoot=1.35)
        hp_out = ease_out_expo((3.6 - local_t) / 0.30) if (3.6 - local_t) < 0.30 else 1.0
        hop = clamp(min(local_t / 0.20, hp_out))
        h_sp = get_hook_title_sprite(spec["hook_line1"], spec["hook_line2"])
        hy = int(round(105 + 30 * (1.0 - min(1.0, hp_in))))
        blend_rgba_onto_bgr(out, h_sp, (SW - h_sp.shape[1]) // 2, hy, opacity=hop)

    # 4. Enlarged 3D/Vector Pop-up Metaphor & Humor Illustrations (1.32x larger = 554x422)
    if not in_cutaway and local_t >= 3.3:
        for ts, te, side, icon_kind, label_top, label_main in POPUP_ILLUSTRATIONS:
            if ts <= t < te:
                age = t - ts
                rem = te - t
                p_in = clamp(ease_out_back(age / 0.40, overshoot=1.40), 0.0, 1.12)
                p_out = ease_out_expo(rem / 0.26) if rem < 0.26 else 1.0
                opacity = clamp(min(age / 0.20, p_out))
                sp = get_large_popup_sprite(icon_kind, label_top, label_main, scale=1.32)
                bob_y = int(round(math.sin(age * 3.5) * 8.0))
                px = 16
                py = 995 + bob_y
                blend_rgba_onto_bgr(out, sp, px, py, opacity=opacity)
                break

    # 5. Synchronized Frameless <= 2-line Large French Subtitles (y = 1465)
    for seg in parsed_segments:
        if seg["t0"] <= t < seg["t1"]:
            s_age = t - seg["t0"]
            s_rem = seg["t1"] - t
            sp_in = ease_out_expo(s_age / 0.14)
            sp_out = clamp(s_rem / 0.10) if s_rem < 0.10 else 1.0
            sop = min(sp_in, sp_out)
            sub_sp = get_short_subtitle_sprite(seg["idx"], seg["line1"], seg["line2"], seg["hl"])
            sx = (SW - sub_sp.shape[1]) // 2
            sy = int(round(1465 + 16 * (1.0 - sp_in)))
            blend_rgba_onto_bgr(out, sub_sp, sx, sy, opacity=sop)
            break

    # 6. Bottom Rose Progress Bar (y = 1908..1920)
    prog = clamp(local_t / max(0.1, short_dur))
    pw = int(round(SW * prog))
    out[SH - 12 : SH, :, :] = (28, 22, 28)
    if pw > 0:
        out[SH - 12 : SH, :pw, 0] = C_ROSE[2]
        out[SH - 12 : SH, :pw, 1] = C_ROSE[1]
        out[SH - 12 : SH, :pw, 2] = C_ROSE[0]

    return out


def prepare_parsed_segments() -> list:
    with open(SEGMENTS_JSON, "r", encoding="utf-8") as f:
        raw_segments = json.load(f)
    parsed = []
    for idx, seg in enumerate(raw_segments):
        if idx in CLEAN_FRENCH_OVERRIDES:
            l1, l2, hl = CLEAN_FRENCH_OVERRIDES[idx]
        else:
            l1, l2, hl = seg["text"], "", ""
        # Clean standalone opening for Short #2 (remove '3° ' prefix so Short #2 opens naturally)
        if idx == 16 and l1.startswith("3° "):
            l1 = l1[3:]
        parsed.append({
            "idx": idx,
            "t0": float(seg["t0"]),
            "t1": float(seg["t1"]),
            "line1": l1,
            "line2": l2,
            "hl": hl,
        })
    return parsed


def generate_preview_grid(preview_path: str):
    """Generates a 12-panel 9:16 preview grid showing Hook + Mid/Cutaway frames for all 6 Shorts."""
    parsed_segments = prepare_parsed_segments()
    cap = cv2.VideoCapture(CLEAN_VIDEO)
    panels = []

    sample_pairs = [
        (1, 1.4, 34.5),     # Short 1: Hook + B-Roll card (without B-ROLL badge)
        (2, 39.6, 59.2),    # Short 2: Hook + Large Pop-up
        (3, 77.0, 94.0),    # Short 3: Hook + B-Roll card
        (4, 135.7, 165.8),  # Short 4: Hook + Large Pop-up
        (5, 185.9, 212.8),  # Short 5: Hook + Large Pop-up
        (6, 226.0, 264.0),  # Short 6: Clean A-Roll Hook at 226.0s + Large Pop-up at 264.0s
    ]

    for s_id, t_a, t_b in sample_pairs:
        spec = SHORTS_SPECS[s_id - 1]
        for t_s in (t_a, t_b):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t_s * FPS)))
            ok, bgr = cap.read()
            if not ok:
                continue
            v_frame = compose_short_frame(bgr, t_s, spec, parsed_segments, reset_tracker=True)
            thumb = cv2.resize(v_frame, (360, 640), interpolation=cv2.INTER_AREA)
            cv2.rectangle(thumb, (10, 10), (250, 48), (20, 16, 20), -1)
            cv2.putText(thumb, f"Short #{spec['id']} t={t_s:.1f}s", (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (180, 114, 244), 2, cv2.LINE_AA)
            panels.append(thumb)
    cap.release()

    row1 = np.hstack(panels[:6])
    row2 = np.hstack(panels[6:12])
    grid = np.vstack([row1, row2])
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    cv2.imwrite(preview_path, grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"Saved 6-Shorts v2 preview grid to {preview_path}")


def render_all_shorts():
    os.makedirs(SHORTS_DIR, exist_ok=True)
    parsed_segments = prepare_parsed_segments()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cap_info = cv2.VideoCapture(CLEAN_VIDEO)
    total_frames = int(cap_info.get(cv2.CAP_PROP_FRAME_COUNT))
    total_dur = total_frames / FPS
    cap_info.release()

    master_wav = "/tmp/yt_inspect/youtube_mixed.wav"
    if not os.path.exists(master_wav):
        os.makedirs("/tmp/yt_inspect", exist_ok=True)
        print("Building broadcast-cleaned & equalized master audio + ducking music + SFX...")
        master_wav = build_youtube_audio(ffmpeg_exe, total_dur)

    sr, full_audio = wavfile.read(master_wav)

    for spec in SHORTS_SPECS:
        out_mp4 = os.path.join(SHORTS_DIR, spec["slug"])
        t0, t1 = spec["t_start"], spec["t_end"]
        dur = t1 - t0

        s0 = max(0, int(t0 * sr))
        s1 = min(len(full_audio), int(t1 * sr))
        clip_audio = full_audio[s0:s1].astype(np.float32) / 32767.0
        fade_in_n = min(len(clip_audio), int(0.22 * sr))
        fade_out_n = min(len(clip_audio), int(0.30 * sr))
        if fade_in_n > 0:
            clip_audio[:fade_in_n] *= np.linspace(0.0, 1.0, fade_in_n, dtype=np.float32)[:, None]
        if fade_out_n > 0:
            clip_audio[-fade_out_n:] *= np.linspace(1.0, 0.0, fade_out_n, dtype=np.float32)[:, None]

        short_wav = f"/tmp/short_{spec['id']:02d}.wav"
        wavfile.write(short_wav, sr, (np.clip(clip_audio, -0.99, 0.99) * 32767.0).astype(np.int16))

        cap = cv2.VideoCapture(CLEAN_VIDEO)
        start_f = int(round(t0 * FPS))
        end_f = int(round(t1 * FPS))
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)

        cmd = [
            ffmpeg_exe, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{SW}x{SH}",
            "-pix_fmt", "bgr24",
            "-r", f"{FPS:.2f}",
            "-i", "-",
            "-i", short_wav,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-maxrate", "2500k",
            "-bufsize", "5000k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            out_mp4,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        for f_idx in range(start_f, end_f):
            ok, bgr = cap.read()
            if not ok:
                break
            t = f_idx / FPS
            frame_9x16 = compose_short_frame(bgr, t, spec, parsed_segments, reset_tracker=(f_idx == start_f))
            proc.stdin.write(frame_9x16.tobytes())

        proc.stdin.close()
        proc.wait()
        cap.release()
        size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
        print(f"[Short #{spec['id']}] Rendered {spec['slug']} ({dur:.1f}s, {size_mb:.2f} MB)")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        generate_preview_grid(sys.argv[2])
    else:
        render_all_shorts()
