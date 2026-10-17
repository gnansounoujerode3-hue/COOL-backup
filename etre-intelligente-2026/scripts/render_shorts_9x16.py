#!/usr/bin/env python3
"""
Vertical 9:16 (1080x1920, 30fps) Reels / YouTube Shorts / TikTok Generator (v3 — Inspired by `reference (2).mp4` in Rose-Pink)
for: 'Être Intelligente En 2026 Te Dessert'

Visual DNA harvested directly from `reference (2).mp4`, adapted to the original Rose-Pink palette (`#EC4899` / `#9D174D`):
  1. Clean, clutter-free A-Roll speaker framing with chest-level (`y=1235..1360`) multi-font editorial typography
     (strictly <= 2 lines at a time) over a subtle lower-chest dark gradient vignette:
     - Style A: Clean `Inter Regular` + Sharp Rose-Pink (`#EC4899`) rectangular highlight bar with 45° soft blurred drop shadow
     - Style B: Clean `Inter Regular` + `Plus Jakarta Sans ExtraBold` + Hand-drawn curved Rose-Pink brush-stroke underline
     - Style C: `Plus Jakarta Sans ExtraBold` / `Inter Regular` + Calligraphic `Great Vibes` script accent
  2. Full-screen Sunlit Window-Gobo White Paper Cutaways (`#F6F5F2` with diagonal window-blind sunlight/shadow beams & fine grain):
     - Cutaway 1A (`t=5.2s` style): Top-left offset `Inter Regular` + Half-height Rose-Pink (`#EC4899`) bar lockup with upper-letter shadow
     - Cutaway 1B (`t=6.4s` `10K` style): Radial Architectural Square Grid + 3D Extruded Glossy Rose-to-Deep-Berry Hero Display Text
     - Cutaway 2A (`t=14.2s->15.0s` style): Horizontal 3-Phase Nudge Camera Whip-Pan across two Rose-Pink (`#EC4899`) bars
     - Cutaway 2B (`t=17.6s` style): Floating 3D Tactile Stacked Paper Card & Magnifying Glass Icon above Rose-Pink bar + subtitle
     - Cutaway 3 (`t=27.6s` style): Calligraphic `Great Vibes` script + `Inter Regular` + Half-height Rose-Pink (`#EC4899`) bar
  3. Velocity-matched seam transitions (`zoom_through_seam`, `cut_the_curve_seam`, `rack_focus_blur_cut`) + cleaned/EQ'd voice & SFX.
"""

import json
import math
import os
import subprocess
import sys
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy.io import wavfile

REPO_ROOT = "/home/user/COOL-backup"
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))
sys.path.insert(0, f"{REPO_ROOT}/.claude/skills/motion-code-harvester/scripts")
sys.path.insert(0, f"{REPO_ROOT}/.claude/skills/animation-design-rules/scripts")

from motion_engine import (
    clamp,
    nudge_curve_3phase,
    zoom_through_seam,
    cut_the_curve_seam,
    rack_focus_blur_cut,
)
from animation_rules_engine import (
    emil_ease_out,
    emil_ease_in_out,
    disney_squash_stretch,
    disney_arc_position,
    disney_follow_through_layers,
)
from render_youtube_edit import (
    CLEAN_FRENCH_OVERRIDES,
    EMOTIONAL_PUNCH_WINDOWS,
    INTER_REG,
    INTER_MED,
    INTER_BOLD,
    JAKARTA_BOLD,
    JAKARTA_EBOLD,
    GREAT_VIBES,
    MONO_MED,
    get_font,
    build_youtube_audio,
)

CLEAN_VIDEO = os.path.join(PROJECT_DIR, "film", "etre-intelligente-en-2026-sans-sous-titres-1080p.mp4")
SEGMENTS_JSON = os.path.join(PROJECT_DIR, "assets", "segments.json")
SHORTS_DIR = os.path.join(PROJECT_DIR, "shorts")

W, H = 1080, 1920
FPS = 30.0

# Original Rose-Pink Palette applied to `reference (2).mp4` design system (RGB)
C_ROSE = (236, 72, 153)         # #EC4899 Primary Rose-Pink bar (replaces crimson red #D61C1C)
C_ROSE_LIGHT = (244, 114, 182)  # #F472B6 Soft Rose Quartz accent
C_ROSE_DARK = (157, 23, 77)     # #9D174D Deep Berry 3D extrusion bevel
C_PAPER = (246, 245, 242)       # #F6F5F2 Sunlit window-gobo paper cutaway background from reference (2).mp4
C_CHARCOAL = (22, 24, 28)       # Crisp editorial charcoal ink on white paper
C_MUTED_INK = (72, 76, 84)      # Secondary charcoal subtitle ink
C_GOLD_ROSE = (238, 174, 42)    # Tactile magnifying glass rim accent (from t=17.6s of reference (2).mp4)

_STATIC_CACHE = {}
_TRACKED_CX = [920.0]

# ---------------------------------------------------------------------------
# Definition of the 6 Shorts + their `reference (2).mp4` Cutaway Scenes
# ---------------------------------------------------------------------------
SHORTS_SPECS = [
    {
        "id": 1,
        "slug": "short-01-paraitre-intelligente-te-dessert-9x16.mp4",
        "t_start": 0.00,
        "t_end": 38.20,
        "cutaways": [
            # Cutaway 1: t=5.2s Half-height Rose bar -> t=6.4s Blueprint Grid + 3D Extruded Rose Hero
            {
                "t0": 5.18, "t_mid": 8.10, "t1": 10.10, "type": "grid_3d",
                "p1_top": "qui te dessert", "p1_bar": "dans ton business,",
                "p2_top": "qui te dessert", "p2_hero": "PARTOUT", "p2_sub": "absolument partout.",
            },
            # Cutaway 2: t=14.2s->15.0s Whip-Pan -> t=17.6s 3D Tactile Icon + Rose Bar
            {
                "t0": 18.00, "t_mid": 21.14, "t1": 23.18, "type": "pan_and_icon",
                "s1_top": "qu'aujourd'hui", "s1_bar": "tu dois performer",
                "s2_top": "aujourd'hui encore", "s2_bar": "prouver aux autres",
                "ic_bar": "prouver aux autres,", "ic_sub": "chaque matin.",
            },
            # Cutaway 3: t=27.6s Calligraphic Script + Half-height Rose bar
            {
                "t0": 32.90, "t_mid": 36.20, "t1": 38.20, "type": "script_and_bar",
                "p1_script": "je dois prouver", "p1_sub": "que je suis géniale,",
                "p2_top": "que je suis quelqu'un", "p2_bar": "d'intelligent.",
            },
        ],
    },
    {
        "id": 2,
        "slug": "short-02-le-piege-du-perfectionnisme-9x16.mp4",
        "t_start": 38.20,
        "t_end": 75.62,
        "cutaways": [
            {
                "t0": 46.88, "t_mid": 48.80, "t1": 51.60, "type": "grid_3d",
                "p1_top": "et d'être enfin", "p1_bar": "qui tu veux être,",
                "p2_top": "que vont penser", "p2_hero": "LES GENS", "p2_sub": "chaque matin ?",
            },
            {
                "t0": 59.30, "t_mid": 63.98, "t1": 66.96, "type": "pan_and_icon",
                "s1_top": "tu veux que tout", "s1_bar": "soit parfait,",
                "s2_top": "à force d'être", "s2_bar": "perfectionniste,",
                "ic_bar": "le contrôle absolu,", "ic_sub": "zéro lâcher-prise.",
            },
            {
                "t0": 69.30, "t_mid": 74.02, "t1": 75.62, "type": "script_and_bar",
                "p1_script": "qui dit résistance,", "p1_sub": "dit encore plus de peur,",
                "p2_top": "et encore plus", "p2_bar": "d'insécurité.",
            },
        ],
    },
    {
        "id": 3,
        "slug": "short-03-percer-sans-tout-calculer-9x16.mp4",
        "t_start": 75.62,
        "t_end": 119.98,
        "cutaways": [
            {
                "t0": 85.54, "t_mid": 88.22, "t1": 90.22, "type": "grid_3d",
                "p1_top": "ce sont des personnes", "p1_bar": "qui vivent vraiment,",
                "p2_top": "qui restent", "p2_hero": "100% VRAIES", "p2_sub": "elles-mêmes.",
            },
            {
                "t0": 95.98, "t_mid": 101.50, "t1": 103.82, "type": "pan_and_icon",
                "s1_top": "et qui pourtant", "s1_bar": "finissent par réussir",
                "s2_top": "et par percer avec", "s2_bar": "une vraie visibilité",
                "ic_bar": "sans tout calculer", "ic_sub": "chaque matin.",
            },
            {
                "t0": 114.54, "t_mid": 116.66, "t1": 119.98, "type": "script_and_bar",
                "p1_script": "plus tu calcules", "p1_sub": "quelque chose,",
                "p2_top": "moins tu as l'impression", "p2_bar": "d'être toi.",
            },
        ],
    },
    {
        "id": 4,
        "slug": "short-04-parler-avec-le-coeur-vs-etre-lisse-9x16.mp4",
        "t_start": 134.30,
        "t_end": 184.46,
        "cutaways": [
            {
                "t0": 144.90, "t_mid": 149.06, "t1": 153.26, "type": "grid_3d",
                "p1_top": "de mon expertise", "p1_bar": "et mon intelligence,",
                "p2_top": "les gens n'aiment pas", "p2_hero": "TROP LISSE", "p2_sub": "ni trop parfait.",
            },
            {
                "t0": 158.58, "t_mid": 161.34, "t1": 164.78, "type": "pan_and_icon",
                "s1_top": "parler simplement", "s1_bar": "avec le cœur,",
                "s2_top": "parce que tu reflètes", "s2_bar": "ta vraie passion,",
                "ic_bar": "transmettre & échanger", "ic_sub": "tes connaissances.",
            },
            {
                "t0": 175.30, "t_mid": 180.58, "t1": 183.26, "type": "script_and_bar",
                "p1_script": "la personne authentique", "p1_sub": "aux mots simples et sincères,",
                "p2_top": "et qui partage", "p2_bar": "son expérience.",
            },
        ],
    },
    {
        "id": 5,
        "slug": "short-05-la-vraie-intelligence-emotionnelle-9x16.mp4",
        "t_start": 184.46,
        "t_end": 224.74,
        "cutaways": [
            {
                "t0": 192.66, "t_mid": 196.78, "t1": 199.18, "type": "grid_3d",
                "p1_top": "tu n'as pas besoin", "p1_bar": "de plaire à tous,",
                "p2_top": "l'objectif n'est pas", "p2_hero": "TE PERDRE", "p2_sub": "toi-même.",
            },
            {
                "t0": 205.22, "t_mid": 210.18, "t1": 212.30, "type": "pan_and_icon",
                "s1_top": "elle se traduit par", "s1_bar": "l'émotionnel,",
                "s2_top": "ton empathie et", "s2_bar": "ce que tu ressens",
                "ic_bar": "percevoir l'invisible", "ic_sub": "au-delà des mots.",
            },
            {
                "t0": 218.62, "t_mid": 221.38, "t1": 224.74, "type": "script_and_bar",
                "p1_script": "libère ta parole,", "p1_sub": "viens telle que tu es,",
                "p2_top": "ce que tu as sur le cœur", "p2_bar": "avec authenticité.",
            },
        ],
    },
    {
        "id": 6,
        "slug": "short-06-parle-face-cam-comme-a-ta-pote-9x16.mp4",
        "t_start": 224.74,
        "t_end": 270.98,
        "cutaways": [
            {
                "t0": 236.34, "t_mid": 237.70, "t1": 241.14, "type": "grid_3d",
                "p1_top": "qui va tout calculer", "p1_bar": "avant de tourner,",
                "p2_top": "écrire un script", "p2_hero": "MOT À MOT", "p2_sub": "pendant des heures.",
            },
            {
                "t0": 246.86, "t_mid": 250.90, "t1": 254.18, "type": "pan_and_icon",
                "s1_top": "je prenais", "s1_bar": "1h à 2h de script,",
                "s2_top": "alors qu'aujourd'hui", "s2_bar": "je parle avec le cœur",
                "ic_bar": "même si ça dure 5 min", "ic_sub": "en toute simplicité.",
            },
            {
                "t0": 266.18, "t_mid": 269.94, "t1": 270.98, "type": "script_and_bar",
                "p1_script": "parle face caméra", "p1_sub": "comme à ta meilleure pote,",
                "p2_top": "fais exactement", "p2_bar": "la même chose !",
            },
        ],
    },
]


def reveal_state(age: float, delay: float = 0.0, dur: float = 0.32, dy_px: float = 22.0):
    loc = age - delay
    if loc <= 0.0:
        return 0.0, dy_px, 0.95
    p = emil_ease_out(clamp(loc / max(1e-4, dur)))
    return p, dy_px * (1.0 - p), 0.95 + 0.05 * p


# ---------------------------------------------------------------------------
# 1. Sunlit Window-Gobo White Paper Cutaway Canvas (`reference (2).mp4` style)
# ---------------------------------------------------------------------------
def get_sunlit_gobo_paper_canvas() -> Image.Image:
    if "gobo_base_rose" not in _STATIC_CACHE:
        base = Image.new("RGBA", (W, H), (*C_PAPER, 255))
        gobo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gobo)
        polygons = [
            [(380, -100), (1180, 320), (1180, 620), (180, 120)],
            [(-100, 420), (1180, 1080), (1180, 1420), (-100, 740)],
            [(-100, 1180), (980, 1780), (760, 1980), (-100, 1480)],
        ]
        for poly in polygons:
            gd.polygon(poly, fill=(198, 192, 195, 105))
        gobo = gobo.filter(ImageFilter.GaussianBlur(radius=68))
        base = Image.alpha_composite(base, gobo)

        rng = np.random.default_rng(42)
        arr = np.array(base, dtype=np.int16)
        grain = rng.integers(-4, 5, size=(H, W, 1), dtype=np.int16)
        arr[:, :, :3] = np.clip(arr[:, :, :3] + grain, 0, 255)
        _STATIC_CACHE["gobo_base_rose"] = Image.fromarray(arr.astype(np.uint8), mode="RGBA")

    return _STATIC_CACHE["gobo_base_rose"].copy()


# ---------------------------------------------------------------------------
# 2. Signature Typography Primitives from `reference (2).mp4` in Rose-Pink (`#EC4899`)
# ---------------------------------------------------------------------------
def fit_font(font_path: str, text: str, target_size: int, max_width: int = 940):
    sz = target_size
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    while sz > 32:
        f = get_font(font_path, sz)
        w = d.textbbox((0, 0), text, font=f)[2]
        if w <= max_width:
            return f
        sz -= 3
    return get_font(font_path, sz)


def draw_rose_bar_word(
    canvas: Image.Image,
    text: str,
    cx: int,
    cy: int,
    age: float,
    delay: float = 0.04,
    font_size: int = 74,
    half_height: bool = False,
    on_white_paper: bool = False,
):
    """
    Renders the signature Highlight Bar from `reference (2).mp4` (`t=5.2s`, `11.4s`, `15.0s`, `17.6s`, `27.6s`)
    in the original Rose-Pink (`#EC4899`) with:
    - Paired wipe animation (`emil_ease_in_out`)
    - Disney Follow-Through 45° soft blurred drop shadow (`+50ms` lag)
    - Optional `half_height=True` (`t=5.2s` `"growing &"` & `t=27.6s` `"simple way"`)
    """
    layers = disney_follow_through_layers(age - delay, base_dur=0.34)
    card_p = layers["card"]
    shadow_p = layers["shadow"]
    if card_p <= 0.02:
        return

    f_bold = fit_font(JAKARTA_EBOLD, text, font_size, max_width=920)
    tmp_d = ImageDraw.Draw(canvas)
    bb = tmp_d.textbbox((0, 0), text, font=f_bold)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]

    _, dy_off, _ = reveal_state(age, delay=delay, dur=0.32, dy_px=22.0)
    tx = cx - tw // 2
    ty = int(cy - th // 2 + dy_off)

    pad_x = 26
    bx0 = tx - pad_x
    bx1_full = tx + tw + pad_x
    wipe = emil_ease_in_out(clamp((age - delay) / 0.28))
    bx1 = bx0 + int((bx1_full - bx0) * wipe)

    if half_height:
        by0 = ty + int(th * 0.36)
        by1 = ty + th + 14
    else:
        by0 = ty - 10
        by1 = ty + th + 16

    # 45-degree soft drop shadow (+50ms Disney Follow-Through lag)
    if shadow_p > 0.05 and bx1 > bx0 + 8:
        sh_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh_d = ImageDraw.Draw(sh_layer)
        sh_alpha = int((125 if on_white_paper else 165) * shadow_p)
        sh_dx = int(8 * shadow_p)
        sh_dy = int(18 * shadow_p)
        sh_d.rounded_rectangle(
            [bx0 + sh_dx, by0 + sh_dy, bx1 + sh_dx, by1 + sh_dy],
            radius=4,
            fill=(18, 12, 18, sh_alpha),
        )
        if on_white_paper and half_height:
            sh_d.text((tx, ty - bb[1] + 2), text, font=f_bold, fill=(14, 12, 16, int(170 * shadow_p)))
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(radius=11))
        canvas.alpha_composite(sh_layer)

    d = ImageDraw.Draw(canvas)
    if bx1 > bx0 + 4:
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=(*C_ROSE, int(255 * card_p)))

    d.text((tx, ty - bb[1]), text, font=f_bold, fill=(255, 255, 255, int(255 * card_p)))


def draw_rose_brush_underline(
    d: ImageDraw.ImageDraw, cx: int, y: int, width: int, progress: float, alpha: int = 255
):
    """Draws the hand-drawn curved brush stroke from `t=1.2s` & `t=3.8s` of `reference (2).mp4` in Rose-Pink `#EC4899`."""
    p = emil_ease_out(clamp(progress))
    if p <= 0.04:
        return
    width = min(width, 680)
    x0 = cx - width // 2
    cur_w = int(width * p)
    pts = []
    for i in range(16):
        u = i / 15.0
        px = x0 + int(cur_w * u)
        py = y - int(7.0 * math.sin(u * math.pi))
        pts.append((px, py))
    if len(pts) >= 2:
        d.line(pts, fill=(*C_ROSE, alpha), width=6)


def draw_shadowed_text_centered(
    canvas: Image.Image,
    text: str,
    cx: int,
    cy: int,
    font,
    fill_rgb,
    age: float,
    delay: float = 0.0,
    dur: float = 0.30,
    on_white_paper: bool = False,
):
    a, dy, _ = reveal_state(age, delay=delay, dur=dur, dy_px=20.0)
    if a <= 0.02:
        return
    d = ImageDraw.Draw(canvas)
    bb = d.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    tx = cx - tw // 2
    ty = int(cy - th // 2 + dy) - bb[1]
    if not on_white_paper:
        d.text((tx + 3, ty + 5), text, font=font, fill=(0, 0, 0, int(175 * a)))
    d.text((tx, ty), text, font=font, fill=(*fill_rgb, int(255 * a)))


# ---------------------------------------------------------------------------
# 3. Cutaway Renderers Matching `reference (2).mp4` (`t=5.2s, 6.4s, 14.2s, 17.6s, 27.6s`)
# ---------------------------------------------------------------------------
def render_cutaway_scene(t: float, cw: dict) -> Image.Image:
    ctype = cw["type"]
    t0, t_mid, t1 = cw["t0"], cw["t_mid"], cw["t1"]

    if ctype == "grid_3d":
        # Phase A (t0 .. t_mid): Matches `t=5.2s` ("So as we are / growing &"):
        # Sunlit gobo paper + top-left offset small sans + Half-Height Rose-Pink bar
        if t < t_mid:
            age = t - t0
            canvas = get_sunlit_gobo_paper_canvas()
            a1, dy1, _ = reveal_state(age, delay=0.02, dur=0.28, dy_px=20.0)
            d = ImageDraw.Draw(canvas)
            f_sm = fit_font(INTER_REG, cw["p1_top"], 44, max_width=860)
            d.text((195, int(845 + dy1)), cw["p1_top"], font=f_sm, fill=(*C_CHARCOAL, int(255 * a1)))
            draw_rose_bar_word(
                canvas,
                cw["p1_bar"],
                cx=W // 2,
                cy=965,
                age=age,
                delay=0.07,
                font_size=82,
                half_height=True,
                on_white_paper=True,
            )
            return canvas

        # Phase B (t_mid .. t1): Matches `t=6.4s` ("cross / 10K / followers mark,"):
        # Radial Architectural Square Grid + 3D Extruded Glossy Rose-to-Deep-Berry Hero Text
        age = t - t_mid
        canvas = get_sunlit_gobo_paper_canvas()
        d = ImageDraw.Draw(canvas)

        grid_p = emil_ease_out(clamp(age / 0.35))
        gx0, gx1, gy0, gy1 = 160, 920, 660, 1260
        step = 45
        for gx in range(gx0, gx1 + 1, step):
            dist_x = abs(gx - W // 2) / 380.0
            al = int(145 * grid_p * max(0.15, 1.0 - 0.65 * dist_x))
            d.line([(gx, gy0), (gx, gy1)], fill=(205, 190, 198, al), width=2)
        for gy in range(gy0, gy1 + 1, step):
            dist_y = abs(gy - 960) / 300.0
            al = int(145 * grid_p * max(0.15, 1.0 - 0.65 * dist_y))
            d.line([(gx0, gy), (gx1, gy)], fill=(205, 190, 198, al), width=2)

        layers = disney_follow_through_layers(age, base_dur=0.38)
        hero_p = layers["card"]
        sh_p = layers["shadow"]
        sx_d, _ = disney_squash_stretch(clamp(age / 0.48), max_deform=0.04)
        hero_txt = cw["p2_hero"]
        f_hero = fit_font(JAKARTA_EBOLD, hero_txt, int(round(126 * sx_d)), max_width=900)
        bb = d.textbbox((0, 0), hero_txt, font=f_hero)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        hx = (W - tw) // 2
        hy = int(935 - th // 2 + 24 * (1.0 - hero_p)) - bb[1]

        # Top offset word ("cross" at t=6.4s)
        f_top = fit_font(INTER_REG, cw["p2_top"], 40, max_width=820)
        d.text((max(180, hx), int(hy + bb[1] - 58)), cw["p2_top"], font=f_top, fill=(*C_CHARCOAL, int(245 * hero_p)))

        if sh_p > 0.05:
            sh_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh_im)
            sd.text((hx + 16, hy + 24), hero_txt, font=f_hero, fill=(24, 10, 18, int(135 * sh_p)))
            sh_im = sh_im.filter(ImageFilter.GaussianBlur(radius=14))
            canvas.alpha_composite(sh_im)
            d = ImageDraw.Draw(canvas)

        # 3D Bevel Extrusion layers (Deep Berry-Obsidian -> Bright Rose-Pink `#EC4899`)
        for depth in range(10, 0, -1):
            u_d = depth / 10.0
            r_c = int(75 + 161 * (1.0 - u_d))
            g_c = int(10 + 62 * (1.0 - u_d))
            b_c = int(42 + 111 * (1.0 - u_d))
            d.text((hx + depth, hy + int(depth * 1.2)), hero_txt, font=f_hero, fill=(r_c, g_c, b_c, int(255 * hero_p)))

        d.text((hx, hy), hero_txt, font=f_hero, fill=(*C_ROSE, int(255 * hero_p)))
        return canvas

    elif ctype == "pan_and_icon":
        # Phase A (t0 .. t_mid): Horizontal Camera Whip-Pan across two Rose-Pink pills (`t=14.2s -> 15.0s`)
        if t < t_mid:
            age = t - t0
            pan_dur = max(0.5, t_mid - t0)
            pan_start = pan_dur * 0.42
            pan_p = nudge_curve_3phase(clamp((age - pan_start) / 0.50))
            cam_x = int(round(pan_p * 960))
            canvas = get_sunlit_gobo_paper_canvas()
            d = ImageDraw.Draw(canvas)

            s1_cx = (W // 2) - cam_x
            if -540 <= s1_cx <= W + 540:
                a1, dy1, _ = reveal_state(age, delay=0.02, dur=0.28, dy_px=20.0)
                f_top = fit_font(INTER_REG, cw["s1_top"], 42, max_width=860)
                w_t1 = d.textbbox((0, 0), cw["s1_top"], font=f_top)[2]
                d.text((s1_cx - w_t1 // 2, int(855 + dy1)), cw["s1_top"], font=f_top, fill=(*C_CHARCOAL, int(255 * a1)))
                draw_rose_bar_word(
                    canvas, cw["s1_bar"], cx=s1_cx, cy=965, age=age, delay=0.06, font_size=72, half_height=False, on_white_paper=True
                )

            s2_cx = (W // 2) + 960 - cam_x
            if -540 <= s2_cx <= W + 540:
                d = ImageDraw.Draw(canvas)
                f_top2 = fit_font(INTER_REG, cw["s2_top"], 42, max_width=860)
                w_t2 = d.textbbox((0, 0), cw["s2_top"], font=f_top2)[2]
                d.text((s2_cx - w_t2 // 2, 855), cw["s2_top"], font=f_top2, fill=(*C_CHARCOAL, 245))
                draw_rose_bar_word(
                    canvas, cw["s2_bar"], cx=s2_cx, cy=965, age=max(0.18, age - pan_start), delay=0.0, font_size=72, half_height=False, on_white_paper=True
                )
            return canvas

        # Phase B (t_mid .. t1): Matches `t=17.6s` (3D Tactile Stacked Paper Card + Magnifying Glass + Rose Bar + Subtitle)
        age = t - t_mid
        canvas = get_sunlit_gobo_paper_canvas()
        layers = disney_follow_through_layers(age, base_dur=0.36)
        ic_p = layers["card"]
        sh_p = layers["shadow"]

        ax, ay = disney_arc_position(540.0, 795.0, 540.0, 750.0, ic_p, arc_offset_px=12.0)
        icx, icy = int(round(ax)), int(round(ay))

        if sh_p > 0.05:
            sh_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh_im)
            sd.rounded_rectangle([icx - 84 + 14, icy - 98 + 22, icx + 84 + 14, icy + 98 + 22], radius=18, fill=(18, 14, 18, int(115 * sh_p)))
            sh_im = sh_im.filter(ImageFilter.GaussianBlur(radius=14))
            canvas.alpha_composite(sh_im)

        d = ImageDraw.Draw(canvas)
        # Back tilted sheet
        d.rounded_rectangle([icx - 78, icy - 96, icx + 86, icy + 90], radius=16, fill=(232, 224, 228, int(255 * ic_p)), outline=(210, 198, 204, int(255 * ic_p)), width=2)
        # Front white tactile sheet
        d.rounded_rectangle([icx - 86, icy - 88, icx + 78, icy + 98], radius=16, fill=(253, 251, 252, int(255 * ic_p)), outline=(220, 210, 215, int(255 * ic_p)), width=2)
        for li in range(4):
            ly = icy - 50 + li * 28
            d.rounded_rectangle([icx - 56, ly, icx + 46, ly + 10], radius=5, fill=(145, 132, 140, int(220 * ic_p)))

        # 3D Rose-Gold Magnifying Glass overlapping the sheet (exact match to `t=17.6s` of `reference (2).mp4`!)
        mg_x, mg_y = icx - 10, icy + 4
        d.line([(mg_x - 28, mg_y + 28), (mg_x - 64, mg_y + 74)], fill=(*C_ROSE_DARK, int(255 * ic_p)), width=18)
        d.line([(mg_x - 28, mg_y + 28), (mg_x - 64, mg_y + 74)], fill=(*C_ROSE, int(255 * ic_p)), width=12)
        d.ellipse([mg_x - 50, mg_y - 50, mg_x + 50, mg_y + 50], fill=(255, 236, 245, int(155 * ic_p)), outline=(*C_ROSE_DARK, int(255 * ic_p)), width=16)
        d.ellipse([mg_x - 46, mg_y - 46, mg_x + 46, mg_y + 46], outline=(*C_ROSE, int(255 * ic_p)), width=10)

        draw_rose_bar_word(
            canvas, cw["ic_bar"], cx=W // 2, cy=980, age=age, delay=0.05, font_size=68, half_height=False, on_white_paper=True
        )
        draw_shadowed_text_centered(
            canvas, cw["ic_sub"], cx=W // 2, cy=1078, font=fit_font(INTER_REG, cw["ic_sub"], 44), fill_rgb=C_CHARCOAL, age=age, delay=0.11, on_white_paper=True
        )
        return canvas

    # ctype == "script_and_bar": Matches `t=27.6s` ("rewrite / in a / simple way / that actually")
    # Split into two 2-line phases so there are NEVER more than 2 lines of text at once
    if t < t_mid:
        age = t - t0
        canvas = get_sunlit_gobo_paper_canvas()
        draw_shadowed_text_centered(
            canvas, cw["p1_script"], cx=W // 2, cy=880, font=fit_font(GREAT_VIBES, cw["p1_script"], 98, max_width=920), fill_rgb=C_CHARCOAL, age=age, delay=0.02, on_white_paper=True
        )
        f_sub1 = fit_font(INTER_REG, cw["p1_sub"], 46, max_width=900)
        draw_shadowed_text_centered(
            canvas, cw["p1_sub"], cx=W // 2, cy=985, font=f_sub1, fill_rgb=C_CHARCOAL, age=age, delay=0.07, on_white_paper=True
        )
        d = ImageDraw.Draw(canvas)
        w_sub1 = d.textbbox((0, 0), cw["p1_sub"], font=f_sub1)[2]
        draw_rose_brush_underline(d, W // 2, 1032, min(w_sub1, 480), (age - 0.12) / 0.28)
        return canvas

    age = t - t_mid
    canvas = get_sunlit_gobo_paper_canvas()
    draw_shadowed_text_centered(
        canvas, cw["p2_top"], cx=W // 2, cy=865, font=fit_font(INTER_REG, cw["p2_top"], 44, max_width=900), fill_rgb=C_CHARCOAL, age=age, delay=0.02, on_white_paper=True
    )
    draw_rose_bar_word(
        canvas, cw["p2_bar"], cx=W // 2, cy=970, age=age, delay=0.06, font_size=82, half_height=True, on_white_paper=True
    )
    return canvas


# ---------------------------------------------------------------------------
# 4. Speaker A-Roll Frame Preparation + Chest-Level Multi-Font Typography (`reference (2).mp4` style)
# ---------------------------------------------------------------------------
def prepare_speaker_frame_9x16(bgr_16x9: np.ndarray, t: float, reset_tracker: bool = False) -> Image.Image:
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

    # Continuous micro-dolly push-in (`reference (2).mp4` camera feel) + emotional punch-zooms
    zoom = 1.015 + 0.028 * math.sin(t * 0.55)
    for w_start, w_end, w_zoom in EMOTIONAL_PUNCH_WINDOWS:
        if w_start <= t <= w_end:
            p_in = emil_ease_out(clamp((t - w_start) / 0.32))
            p_out = emil_ease_out(clamp((w_end - t) / 0.35)) if (w_end - t) < 0.35 else 1.0
            capped_z = min(w_zoom, 1.08)
            zoom = max(zoom, 1.0 + (capped_z - 1.0) * min(p_in, p_out))
            break

    crop_h = int(round(h_src / zoom))
    crop_w = int(round(crop_h * (W / H)))

    cx = int(round(_TRACKED_CX[0]))
    cy = int(round(h_src * 0.44)) if head_top_y < 230 else int(round(h_src * 0.50))

    x0 = int(clamp(cx - crop_w // 2, 0, w_src - crop_w))
    y0 = int(clamp(cy - crop_h // 2, 0, h_src - crop_h))

    cropped = bgr_16x9[y0 : y0 + crop_h, x0 : x0 + crop_w]
    vertical = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_CUBIC)

    rgb = cv2.cvtColor(vertical, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.06)
    im = im.convert("RGBA")

    # Cached chest-to-bottom gradient vignette (`y=980..1920`) matching `reference (2).mp4`
    if "chest_vignette_rose" not in _STATIC_CACHE:
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig)
        for y in range(980, H, 4):
            u = (y - 980) / float(H - 980)
            alpha = int(170 * (u ** 1.38))
            vd.rectangle([0, y, W, y + 4], fill=(10, 8, 12, alpha))
        _STATIC_CACHE["chest_vignette_rose"] = vig

    im = Image.alpha_composite(im, _STATIC_CACHE["chest_vignette_rose"])
    return im


def overlay_speaker_typography(canvas: Image.Image, t: float, parsed_segments: list):
    """
    Renders chest-level (`y=1240..1360`) multi-font editorial typography over A-Roll
    (strictly <= 2 lines at a time) cycling between the 3 signature lockup styles of `reference (2).mp4`
    in the original Rose-Pink (`#EC4899`):
      - Style 0 (Rose Bar Lockup — like `t=11.4s`, `24.5s`, `33.2s` of `reference (2).mp4`):
        Line 1 in `Inter Regular`, Line 2 inside a sharp Rose-Pink `#EC4899` bar with 45° drop shadow.
      - Style 1 (Bold Sans + Hand-Drawn Rose Brush Curve — like `t=1.0s`, `3.8s`, `21.6s`):
        Line 1 in `Inter Regular`, Line 2 in `Plus Jakarta Sans ExtraBold` + curved Rose-Pink brush underline.
      - Style 2 (Sans + Calligraphic Script — like `t=3.8s`, `9.8s`, `11.4s`):
        Line 1 in `Plus Jakarta Sans ExtraBold` (or `Inter Regular`), Line 2 in flowing `Great Vibes` script.
    """
    active_seg = None
    for seg in parsed_segments:
        if seg["t0"] <= t < seg["t1"]:
            active_seg = seg
            break
    if active_seg is None:
        return

    age = t - active_seg["t0"]
    idx = active_seg["idx"]
    l1 = active_seg["line1"].strip()
    l2 = active_seg["line2"].strip()
    d = ImageDraw.Draw(canvas)

    # Single-line segment: render as bold Rose-Pink Bar (`reference (2).mp4` single-line punch style)
    if not l2:
        draw_rose_bar_word(canvas, l1, cx=W // 2, cy=1485, age=age, delay=0.02, font_size=74)
        return

    style = idx % 3
    if style == 0:
        # Style A: Line 1 = Inter Regular (`y=1425`), Line 2 = Sharp Rose-Pink `#EC4899` Bar (`y=1525`)
        f1 = fit_font(INTER_REG, l1, 48, max_width=920)
        draw_shadowed_text_centered(canvas, l1, W // 2, 1425, f1, (244, 242, 246), age, delay=0.02)
        draw_rose_bar_word(
            canvas, l2, cx=W // 2, cy=1525, age=age, delay=0.06, font_size=72, half_height=(idx % 6 == 0)
        )
    elif style == 1:
        # Style B: Line 1 = Inter Regular (`y=1425`), Line 2 = ExtraBold Sans (`y=1515`) + Hand-Drawn Rose Brush Underline
        f1 = fit_font(INTER_REG, l1, 48, max_width=920)
        f2 = fit_font(JAKARTA_EBOLD, l2, 72, max_width=920)
        draw_shadowed_text_centered(canvas, l1, W // 2, 1425, f1, (242, 240, 245), age, delay=0.02)
        draw_shadowed_text_centered(canvas, l2, W // 2, 1515, f2, (255, 255, 255), age, delay=0.06)
        w2 = d.textbbox((0, 0), l2, font=f2)[2]
        draw_rose_brush_underline(d, W // 2, 1572, min(w2, 560), (age - 0.09) / 0.25)
    else:
        # Style C: Line 1 = ExtraBold Sans (`y=1425`), Line 2 = Calligraphic `Great Vibes` Script (`y=1538`)
        if len(l2) <= 26:
            f1 = fit_font(JAKARTA_EBOLD, l1, 64, max_width=920)
            f2 = fit_font(GREAT_VIBES, l2, 98, max_width=920)
            draw_shadowed_text_centered(canvas, l1, W // 2, 1425, f1, (255, 255, 255), age, delay=0.02)
            draw_shadowed_text_centered(canvas, l2, W // 2, 1538, f2, (255, 232, 244), age, delay=0.06)
        else:
            f1 = fit_font(INTER_REG, l1, 48, max_width=920)
            f2 = fit_font(JAKARTA_EBOLD, l2, 70, max_width=920)
            draw_shadowed_text_centered(canvas, l1, W // 2, 1425, f1, (242, 240, 245), age, delay=0.02)
            draw_shadowed_text_centered(canvas, l2, W // 2, 1515, f2, (255, 255, 255), age, delay=0.06)
            w2 = d.textbbox((0, 0), l2, font=f2)[2]
            draw_rose_brush_underline(d, W // 2, 1572, min(w2, 560), (age - 0.09) / 0.25)


# ---------------------------------------------------------------------------
# 5. Master Frame Compositor with Velocity-Matched Seams (`cut-the-curve`)
# ---------------------------------------------------------------------------
def get_active_cutaway(t: float, spec: dict):
    for cw in spec["cutaways"]:
        if cw["t0"] <= t < cw["t1"]:
            return cw
    return None


def render_state_image(bgr_16x9: np.ndarray, t: float, spec: dict, parsed_segments: list, reset_tracker: bool = False) -> Image.Image:
    cw = get_active_cutaway(t, spec)
    if cw is not None:
        return render_cutaway_scene(t, cw)
    canvas = prepare_speaker_frame_9x16(bgr_16x9, t, reset_tracker=reset_tracker)
    overlay_speaker_typography(canvas, t, parsed_segments)
    return canvas


def compose_short_frame(bgr_16x9: np.ndarray, t: float, spec: dict, parsed_segments: list, reset_tracker: bool = False) -> np.ndarray:
    # Check velocity-matched seam transitions (`zoom_through`, `cut_the_curve`, `rack_focus`) around cutaway boundaries
    half_w = 0.16
    seam_modes = ["zoom_through", "cut_the_curve", "rack_focus"]
    for idx_c, cw in enumerate(spec["cutaways"]):
        mode_in = seam_modes[idx_c % 3]
        mode_out = seam_modes[(idx_c + 1) % 3]
        for t_seam, mode in ((cw["t0"], mode_in), (cw["t1"], mode_out)):
            if abs(t - t_seam) <= half_w:
                p = clamp((t - (t_seam - half_w)) / (2.0 * half_w))
                im_a = render_state_image(bgr_16x9, t_seam - half_w - 0.02, spec, parsed_segments, reset_tracker=reset_tracker)
                im_b = render_state_image(bgr_16x9, t_seam + half_w + 0.02, spec, parsed_segments, reset_tracker=False)
                if mode == "zoom_through":
                    out_im = zoom_through_seam(im_a, im_b, p, inverse=False)
                elif mode == "cut_the_curve":
                    out_im = cut_the_curve_seam(im_a, im_b, p, direction="left")
                else:
                    out_im = rack_focus_blur_cut(im_a, im_b, p)
                rgb = np.array(out_im.convert("RGB"), dtype=np.uint8)
                return rgb[:, :, ::-1].copy()

    out_im = render_state_image(bgr_16x9, t, spec, parsed_segments, reset_tracker=reset_tracker)
    rgb = np.array(out_im.convert("RGB"), dtype=np.uint8)
    return rgb[:, :, ::-1].copy()


def prepare_parsed_segments() -> list:
    with open(SEGMENTS_JSON, "r", encoding="utf-8") as f:
        raw_segments = json.load(f)
    parsed = []
    for idx, seg in enumerate(raw_segments):
        if idx in CLEAN_FRENCH_OVERRIDES:
            l1, l2, hl = CLEAN_FRENCH_OVERRIDES[idx]
        else:
            l1, l2, hl = seg["text"], "", ""
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
    """Generates a 12-panel 9:16 preview grid showing A-Roll + Cutaway frames across all 6 Shorts."""
    parsed_segments = prepare_parsed_segments()
    cap = cv2.VideoCapture(CLEAN_VIDEO)
    panels = []

    sample_pairs = [
        (1, 3.6, 9.0),      # Short 1: A-Roll Chest Type + 3D Extruded Rose Hero ('PARTOUT') on Square Grid
        (2, 41.2, 65.2),    # Short 2: A-Roll Chest Type + 3D Tactile Document/Magnifying Glass ('le contrôle absolu')
        (3, 78.5, 89.2),    # Short 3: A-Roll Chest Type + 3D Extruded Rose Hero ('100% VRAIES')
        (4, 137.0, 151.0),  # Short 4: A-Roll Chest Type + 3D Extruded Rose Hero ('TROP LISSE')
        (5, 188.0, 206.5),  # Short 5: A-Roll Chest Type + Whip-Pan Rose Bar ('l'émotionnel,')
        (6, 227.0, 268.0),  # Short 6: A-Roll Chest Type + Calligraphic Script ('parle face caméra')
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
            cv2.rectangle(thumb, (10, 10), (255, 48), (20, 16, 20), -1)
            cv2.putText(thumb, f"Short #{spec['id']} t={t_s:.1f}s", (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (180, 114, 244), 2, cv2.LINE_AA)
            panels.append(thumb)
    cap.release()

    row1 = np.hstack(panels[:6])
    row2 = np.hstack(panels[6:12])
    grid = np.vstack([row1, row2])
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    cv2.imwrite(preview_path, grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"Saved 6-Shorts ref2-Rose preview grid to {preview_path}")


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
            "-s", f"{W}x{H}",
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
    elif len(sys.argv) > 2 and sys.argv[1] == "--only":
        only_id = int(sys.argv[2])
        SHORTS_SPECS[:] = [s for s in SHORTS_SPECS if s["id"] == only_id]
        render_all_shorts()
    else:
        render_all_shorts()
