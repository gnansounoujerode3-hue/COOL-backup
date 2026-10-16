#!/usr/bin/env python3
"""
Master 9:16 100% Faceless Pure Motion-Design Video Compositor (`whatsapp-motion-faceless`)
For `WhatsApp Video 2026-10-16 at 13.20.43.mp4` with new French voiceover (`voice-01`).

Zero human faces — 100% pure 3D & 2.5D Motion Design:
  - Act I   (00.00s - 09.00s): 3D Perspective Calendar Grid (`1 MOIS DE CONTENU`) +
                               3D Stopwatch (`1 À 2H / SEMAINE`) + 3D NLE Short Timeline.
  - Act II  (09.00s - 20.05s): Phase A (09.00s - 14.20s): Editorial Ivory Canvas with 4
                               Tilted 3D Short/Reels UI Cards (`TON UNIVERS`, `TON STYLE`,
                               `TON BRANDING`).
                               Phase B (14.20s - 20.05s): Dark 3D Analytics & Revenue Stage
                               (`80k Abonnés` badge, Orange `36 157 vues qualifiées` chart,
                               `Stripe +1 000 €` notifications, Neon Green `+Chiffre d'affaires`).
  - Act III (20.05s - 28.95s): 3D Studio Softbox & Workstation (`2 À 3 HEURES / MOIS`) +
                               3D Cloud Rush Transfer (`TU M'ENVOIES TES RUSHS -> PLUS RIEN À FAIRE ✕`).
  - Act IV  (28.95s - 36.75s): Phase A (28.95s - 32.80s): Editorial Ivory Poster (`PACKS DE
                               10 À 15 VIDÉOS` + `EN 1 SEMAINE OUVRÉE` + `PRÊTES À ÊTRE POSTÉES ✓`).
                               Phase B (32.80s - 36.75s): Dark 3D Monthly Calendar Grid with
                               Golden Circled Posting Days (`TOUS LES 2 À 3 JOURS SUR LE MOIS`).
  - Act V   (36.75s - 52.95s): Phase A (36.75s - 43.20s): 3D Leverage Dashboard (`3H CRÉATION`
                               -> `PUBLIER RÉGULIÈREMENT` -> `DÉVELOPPER TON ACTIVITÉ`).
                               Phase B (43.20s - 52.95s): Editorial White/Gold Triptych:
                               3D Golden Pocket Watch (`NE PERDS PLUS DES HEURES`),
                               3D Neural Expertise Sphere (`TA ZONE D'EXPERTISE`),
                               3D Architectural Monolith (`DÉVELOPPEMENT DE TON ENTREPRISE`).
  - Act VI  (52.95s - 63.95s): 3D Value Pillars (`GAIN DE TEMPS`, `VIDÉOS DE QUALITÉ`,
                               `IMAGE DE MARQUE SÉRIEUSE`) -> Final 3D Contact Portal
                               (`CONTACTE-MOI • ON PARLE DE TON PROJET ENSEMBLE`).
"""

import argparse
import json
import math
import os
import subprocess
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/animation-design-rules/scripts")
from motion_engine import (
    cubic_bezier,
    expo_in_out,
    expo_out,
    power3_in,
    power4_out,
    nudge_curve_3phase,
    waterfall_word_state,
    zoom_through_seam,
    cut_the_curve_seam,
    rack_focus_blur_cut,
)
from animation_rules_engine import (
    emil_ease_out,
    emil_ease_in_out,
    emil_drawer_ease,
    md3_emphasized_decelerate,
    md3_emphasized_accelerate,
    disney_overshoot_ease,
    disney_squash_stretch,
    disney_anticipation_launch,
    disney_arc_position,
    disney_follow_through_layers,
    counter_motion_ambient,
    audit_animation_spec,
)

W, H = 1080, 1920
FPS = 30.0
TOTAL_DURATION = 63.95
TOTAL_FRAMES = int(round(TOTAL_DURATION * FPS))

PROJECT_DIR = "/home/user/COOL-backup/whatsapp-motion-faceless"
AUDIO_DIR = f"{PROJECT_DIR}/assets/audio"
FILM_DIR = f"{PROJECT_DIR}/film"
TIMELINE_JSON = f"{AUDIO_DIR}/timeline.json"
MIXED_WAV = f"{AUDIO_DIR}/master_voiceover_mix.wav"
OUT_MP4 = f"{FILM_DIR}/motion-design-sans-visage-9x16.mp4"

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"

# Palette inspired by the original WhatsApp video's motion graphics + MOTION-DESIGN.md
C_DARK_BG = (11, 13, 18)        # Deep obsidian studio canvas
C_IVORY_BG = (248, 245, 238)    # Clean editorial off-white/ivory canvas
C_AMBER = (245, 166, 35)        # #F5A623 warm amber/gold highlight from original captions
C_PEACH = (238, 178, 124)       # Soft warm peach-gold accent
C_GREEN = (34, 218, 92)         # #22DA5C neon growth green
C_STRIPE = (99, 91, 255)        # #635BFF Stripe indigo badge
C_RED = (230, 38, 45)           # #E6262D YouTube/Subscriber red badge
C_CYAN = (56, 224, 216)         # #38E0D8 electric cyan accent
C_INK = (20, 22, 28)

_FONT_CACHE = {}
_BG_CACHE = {}


def get_font(path: str, size: int):
    size = max(12, int(round(size)))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def ease_motion(p: float) -> float:
    """Emil Kowalski strong UI entrance deceleration: cubic-bezier(0.23, 1, 0.32, 1)"""
    return emil_ease_out(clamp(p))


def ease_out_back(t: float, s: float = 1.4) -> float:
    return disney_overshoot_ease(clamp(t))


def data_reveal(age: float, delay: float = 0.0, dur: float = 0.42, offset_y: float = 28.0):
    t_loc = age - delay
    if t_loc <= 0.0:
        return 0.0, offset_y
    e = emil_ease_out(clamp(t_loc / max(1e-4, dur)))
    return e, offset_y * (1.0 - e)


# ---------------------------------------------------------------------------
# 3D Projective Homography (`warp_plane_3d`) + Disney Squash & Stretch
# ---------------------------------------------------------------------------
def _solve_perspective_coeffs(src_pts, dst_pts):
    matrix = []
    rhs = []
    for (x, y), (u, v) in zip(src_pts, dst_pts):
        matrix.append([u, v, 1, 0, 0, 0, -x * u, -x * v])
        matrix.append([0, 0, 0, u, v, 1, -y * u, -y * v])
        rhs.extend([x, y])
    A = np.array(matrix, dtype=np.float64)
    B = np.array(rhs, dtype=np.float64)
    res = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(float(x) for x in res)


def warp_plane_3d(
    img: Image.Image,
    rx_deg: float = 0.0,
    ry_deg: float = 0.0,
    rz_deg: float = 0.0,
    scale: float = 1.0,
    focal: float = 1400.0,
    squash_progress: float = 1.0,
    squash_intensity: float = 0.032,
) -> Image.Image:
    w, h = img.size
    cx, cy = w * 0.5, h * 0.5
    rx, ry, rz = math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)
    cx_r, sx_r = math.cos(rx), math.sin(rx)
    cy_r, sy_r = math.cos(ry), math.sin(ry)
    cz_r, sz_r = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx_r, -sx_r], [0, sx_r, cx_r]], dtype=np.float64)
    Ry = np.array([[cy_r, 0, sy_r], [0, 1, 0], [-sy_r, 0, cy_r]], dtype=np.float64)
    Rz = np.array([[cz_r, -sz_r, 0], [sz_r, cz_r, 0], [0, 0, 1]], dtype=np.float64)
    R = Rz @ Ry @ Rx
    eff_scale = max(0.90, scale)
    sx_d, sy_d = disney_squash_stretch(squash_progress, max_deform=squash_intensity)
    corners = np.array(
        [
            [-cx * sx_d, -cy * sy_d, 0.0],
            [cx * sx_d, -cy * sy_d, 0.0],
            [cx * sx_d, cy * sy_d, 0.0],
            [-cx * sx_d, cy * sy_d, 0.0],
        ],
        dtype=np.float64,
    ) * eff_scale
    src_pts = [(0.0, 0.0), (float(w), 0.0), (float(w), float(h)), (0.0, float(h))]
    dst_pts = []
    for pt in corners:
        p3 = R @ pt
        z = max(200.0, focal + p3[2])
        dst_pts.append((cx + (p3[0] * focal) / z, cy + (p3[1] * focal) / z))
    coeffs = _solve_perspective_coeffs(src_pts, dst_pts)
    return img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BILINEAR)


def _get_cached_shadow(cw: int, ch: int) -> Image.Image:
    key = ("shadow", cw, ch)
    if key not in _BG_CACHE:
        sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([18, 22, cw - 18, ch - 10], radius=38, fill=(0, 0, 0, 125))
        _BG_CACHE[key] = sh
    return _BG_CACHE[key]


def composite_hero_card_3layers(
    canvas: Image.Image,
    card: Image.Image,
    target_x: int,
    target_y: int,
    age: float,
    delay: float = 0.0,
    dur: float = 0.44,
    rx_deg: float = 0.0,
    ry_deg: float = 0.0,
    rz_deg: float = 0.0,
    arc_px: float = 12.0,
):
    """
    Implements the LottieFiles Card Entrance Recipe & Disney Principles 1, 5, 7, 8:
    1. Start 26px below target at scale=0.95 (never scale(0))
    2. Parabolic Arc path (`disney_arc_position`, 12px X midpoint offset)
    3. Easing: `md3_emphasized_decelerate` / `emil_ease_out`
    4. Follow-through: 3D ambient shadow arrives +50ms after card lands
    5. Squash & Stretch: subtle volume-preserving settle on arrival
    """
    local_age = age - delay
    if local_age <= 0.0:
        return
    layers = disney_follow_through_layers(local_age, base_dur=dur)
    shadow_p = layers["shadow"]
    sc = layers["scale"]  # 0.95 -> 1.00

    ax, ay = disney_arc_position(
        float(target_x), float(target_y + 28), float(target_x), float(target_y), clamp(local_age / dur), arc_offset_px=arc_px
    )
    warped = warp_plane_3d(
        card,
        rx_deg=rx_deg,
        ry_deg=ry_deg,
        rz_deg=rz_deg,
        scale=sc * 0.96,
        squash_progress=clamp(local_age / (dur * 1.15)),
        squash_intensity=0.032,
    )

    if shadow_p > 0.15:
        cw, ch = card.size
        sh = _get_cached_shadow(cw, ch)
        sh_y_off = int(12 + 10 * shadow_p)
        sh_x_off = int(6 * shadow_p)
        canvas.alpha_composite(sh, (int(round(ax)) + sh_x_off, int(round(ay)) + sh_y_off))

    canvas.alpha_composite(warped, (int(round(ax)), int(round(ay))))


# ---------------------------------------------------------------------------
# Cached Studio Canvases (Dark Obsidian Grid & Editorial Ivory Grid +
# Rule 6 Ambient Counter-Motion Layer & Klik Chapter HUD)
# ---------------------------------------------------------------------------
def get_dark_canvas(t: float, age: float = 0.5) -> Image.Image:
    if "dark_base" not in _BG_CACHE:
        bg = Image.new("RGBA", (W, H), (*C_DARK_BG, 255))
        d = ImageDraw.Draw(bg)
        for gx in range(0, W, 72):
            d.line([(gx, 0), (gx, H)], fill=(26, 32, 44, 255), width=1)
        for gy in range(0, H, 72):
            d.line([(0, gy), (W, gy)], fill=(26, 32, 44, 255), width=1)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([80, 240, W - 80, H - 240], fill=(245, 166, 35, 34))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=90))
        bg = Image.alpha_composite(bg, glow)
        _BG_CACHE["dark_base"] = bg
    im = _BG_CACHE["dark_base"].copy()
    d = ImageDraw.Draw(im)
    _, hero_dy = data_reveal(age, delay=0.0, dur=0.45, offset_y=28.0)
    _, amb_dy = counter_motion_ambient(0.0, hero_dy, ratio=0.28)
    for i in range(28):
        seed = (i + 1) * 137.5
        px = (seed * 29.3 + math.sin(t * 0.8 + i) * 22.0) % W
        py = (seed * 67.1 - t * (22.0 + (i % 5) * 8.0) + amb_dy) % H
        r = 2 + (i % 4)
        col = (*C_AMBER, 115) if i % 2 == 0 else (255, 255, 255, 80)
        d.ellipse([px - r, py - r, px + r, py + r], fill=col)
    draw_bottom_rule_hud(d, t, dark_theme=True)
    return im


def get_ivory_canvas(t: float, age: float = 0.5) -> Image.Image:
    if "ivory_base" not in _BG_CACHE:
        bg = Image.new("RGBA", (W, H), (*C_IVORY_BG, 255))
        d = ImageDraw.Draw(bg)
        for gx in range(0, W, 72):
            d.line([(gx, 0), (gx, H)], fill=(230, 224, 212, 255), width=1)
        for gy in range(0, H, 72):
            d.line([(0, gy), (W, gy)], fill=(230, 224, 212, 255), width=1)
        _BG_CACHE["ivory_base"] = bg
    im = _BG_CACHE["ivory_base"].copy()
    d = ImageDraw.Draw(im)
    _, hero_dy = data_reveal(age, delay=0.0, dur=0.45, offset_y=28.0)
    _, amb_dy = counter_motion_ambient(0.0, hero_dy, ratio=0.25)
    for i in range(18):
        seed = (i + 3) * 97.3
        px = (seed * 31.7 + math.cos(t * 0.7 + i) * 18.0) % W
        py = (seed * 53.9 - t * 14.0 + amb_dy) % H
        r = 3 + (i % 3)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(235, 165, 55, 75))
    draw_bottom_rule_hud(d, t, dark_theme=False)
    return im


def draw_bottom_rule_hud(d: ImageDraw.ImageDraw, t: float, dark_theme: bool = True):
    prog = clamp(t / TOTAL_DURATION)
    bar_y = 1852
    bg_c = (24, 28, 40, 215) if dark_theme else (232, 226, 214, 235)
    fg_c = (190, 198, 214, 230) if dark_theme else (60, 64, 74, 230)
    d.rounded_rectangle([64, bar_y - 18, W - 64, bar_y + 28], radius=22, fill=bg_c)

    tx0, tx1 = 250, W - 230
    d.rounded_rectangle([tx0, bar_y, tx1, bar_y + 10], radius=5, fill=(60, 68, 86, 160))
    fill_w = max(12, int((tx1 - tx0) * prog))
    d.rounded_rectangle([tx0, bar_y, tx0 + fill_w, bar_y + 10], radius=5, fill=(*C_AMBER, 255))

    f_tc = get_font(MONO_MED, 19)
    d.text((88, bar_y - 8), f"TC {int(t // 60):02d}:{int(t % 60):02d}.{int((t % 1) * 30):02d}", font=f_tc, fill=fg_c)

    for bi in range(10):
        bx = W - 205 + bi * 12
        bh = int(6 + 12 * abs(math.sin(t * 7.5 + bi * 0.65)))
        d.rounded_rectangle([bx, bar_y + 5 - bh // 2, bx + 6, bar_y + 5 + bh // 2], radius=2, fill=(*C_AMBER, 240))


def draw_top_header(canvas: Image.Image, age: float, act_num: str, label: str, dark_theme: bool = True):
    a, dy = data_reveal(age, delay=0.02, dur=0.38, offset_y=20.0)
    if a <= 0.02:
        return
    d = ImageDraw.Draw(canvas)
    f_mono = get_font(MONO_MED, 22)
    txt = f"{act_num}   //   {label}"
    bb = d.textbbox((0, 0), txt, font=f_mono)
    tw = bb[2] - bb[0]
    pw = tw + 68
    px = (W - pw) // 2
    py = int(68 + dy)
    bg_c = (20, 24, 34, int(230 * a)) if dark_theme else (255, 255, 255, int(240 * a))
    bd_c = (*C_AMBER, int(220 * a)) if dark_theme else (20, 22, 28, int(210 * a))
    fg_c = (245, 247, 252, int(250 * a)) if dark_theme else (20, 22, 28, int(250 * a))
    d.rounded_rectangle([px, py, px + pw, py + 48], radius=24, fill=bg_c, outline=bd_c, width=2)
    d.ellipse([px + 20, py + 18, px + 32, py + 30], fill=(*C_AMBER, int(255 * a)))
    d.text((px + 44, py + 10), txt, font=f_mono, fill=fg_c)


def draw_kinetic_caption_stack(
    canvas: Image.Image,
    age: float,
    line1: str,
    line2_highlight: str,
    line3: str = "",
    cy: int = 1480,
    dark_theme: bool = True,
    accent=C_AMBER,
):
    d = ImageDraw.Draw(canvas)
    f_l1 = get_font(JAKARTA_BOLD, 48)
    f_l2 = get_font(JAKARTA_EBOLD, 78)
    f_l3 = get_font(JAKARTA_BOLD, 46)

    fg_main = (255, 255, 255) if dark_theme else C_INK

    a1, dy1 = data_reveal(age, delay=0.0, dur=0.28, offset_y=22.0)
    if line1 and a1 > 0.02:
        bb1 = d.textbbox((0, 0), line1, font=f_l1)
        x1 = (W - (bb1[2] - bb1[0])) // 2
        y1 = int(cy - 82 + dy1)
        d.text((x1, y1), line1, font=f_l1, fill=(*fg_main, int(250 * a1)))

    a2, dy2 = data_reveal(age, delay=0.055, dur=0.30, offset_y=26.0)
    if line2_highlight and a2 > 0.02:
        bb2 = d.textbbox((0, 0), line2_highlight, font=f_l2)
        w2 = bb2[2] - bb2[0]
        h2 = bb2[3] - bb2[1]
        x2 = (W - w2) // 2
        y2 = int(cy + dy2)
        wipe = emil_ease_in_out(clamp((age - 0.055) / 0.28))
        bw = int((w2 + 52) * wipe)
        if bw > 6:
            sh_a = int(110 * clamp((age - 0.095) / 0.25))
            if sh_a > 5:
                d.rounded_rectangle(
                    [x2 - 22, y2 - 4, x2 - 22 + bw, y2 + h2 + 24],
                    radius=18,
                    fill=(0, 0, 0, sh_a),
                )
            d.rounded_rectangle(
                [x2 - 26, y2 - 10, x2 - 26 + bw, y2 + h2 + 18],
                radius=18,
                fill=(*accent, int(248 * a2)),
            )
        txt_c = (14, 16, 22) if accent in (C_AMBER, C_PEACH, C_GREEN, C_CYAN) else (255, 255, 255)
        d.text((x2, y2 - bb2[1]), line2_highlight, font=f_l2, fill=(*txt_c, int(255 * a2)))

    a3, dy3 = data_reveal(age, delay=0.101, dur=0.28, offset_y=22.0)
    if line3 and a3 > 0.02:
        bb3 = d.textbbox((0, 0), line3, font=f_l3)
        x3 = (W - (bb3[2] - bb3[0])) // 2
        y3 = int(cy + 106 + dy3)
        d.text((x3, y3), line3, font=f_l3, fill=(*fg_main, int(245 * a3)))


# ---------------------------------------------------------------------------
# ACT I (00.00s - 09.00s): 3D Calendar Grid ("1 MOIS DE CONTENU") +
# 3D Stopwatch ("1 À 2 HEURES") + 3D Short Montage Timeline
# ---------------------------------------------------------------------------
def render_act1_hook(t: float) -> Image.Image:
    age = t
    canvas = get_dark_canvas(t)
    draw_top_header(canvas, age, "ACTE 01", "PRODUCTION SHORT-FORM AUTOMATISÉE", dark_theme=True)

    if t < 4.50:
        # Phase 1A (0.00s - 4.50s): 3D Perspective Calendar Card + Stopwatch Badge
        cw, ch = 880, 860
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=38, fill=(18, 22, 32, 245), outline=(*C_AMBER, 225), width=3)
        cd.rounded_rectangle([28, 28, cw - 28, 128], radius=22, fill=(28, 34, 48, 255))
        cd.text((58, 52), "PLANNING CONTENU  •  30 JOURS PRÊTS", font=get_font(JAKARTA_EBOLD, 36), fill=(*C_AMBER, 255))

        # 5x6 Calendar Grid with animated glowing checkmarks
        cell_w, cell_h = 122, 96
        gx0, gy0 = 56, 165
        n_lit = int(clamp(age / 2.6) * 30)
        f_day = get_font(JAKARTA_BOLD, 28)
        for d_idx in range(30):
            r, c = divmod(d_idx, 6)
            cx = gx0 + c * (cell_w + 12)
            cy = gy0 + r * (cell_h + 14)
            lit = d_idx < n_lit
            bg_c = (*C_AMBER, 235) if lit else (28, 34, 46, 220)
            fg_c = (14, 16, 22, 255) if lit else (160, 168, 182, 220)
            cd.rounded_rectangle([cx, cy, cx + cell_w, cy + cell_h], radius=16, fill=bg_c, outline=(255, 255, 255, 45), width=1)
            cd.text((cx + 16, cy + 12), f"{d_idx + 1:02d}", font=f_day, fill=fg_c)
            if lit and d_idx % 2 == 0:
                cd.text((cx + 68, cy + 44), "✓", font=get_font(JAKARTA_EBOLD, 32), fill=(14, 16, 22, 255))

        # Bottom Stopwatch bar inside card (`1 À 2 HEURES / SEMAINE`)
        cd.rounded_rectangle([42, 725, cw - 42, 825], radius=22, fill=(14, 18, 26, 255), outline=(*C_CYAN, 230), width=3)
        # Clock icon
        cd.ellipse([72, 745, 132, 805], outline=(*C_CYAN, 255), width=4)
        ang = t * 4.5
        cd.line([(102, 775), (102 + int(20 * math.sin(ang)), 775 - int(20 * math.cos(ang)))], fill=(*C_CYAN, 255), width=4)
        cd.text((158, 752), "TEMPS REQUIS : 1 À 2H / SEMAINE", font=get_font(JAKARTA_EBOLD, 36), fill=(255, 255, 255, 255))

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            230,
            age,
            delay=0.04,
            dur=0.45,
            rx_deg=6.0 * math.sin(t * 1.1),
            ry_deg=-5.5 * math.cos(t * 0.9),
            arc_px=14.0,
        )

        if t < 2.25:
            draw_kinetic_caption_stack(canvas, age, "ATTENDS, TU SAIS QUE TU PEUX AVOIR", "1 MOIS DE CONTENU", "PRÊT À ÊTRE POSTÉ ?", cy=1420)
        else:
            draw_kinetic_caption_stack(canvas, t - 2.25, "PRÊT À ÊTRE POSTÉ EN SEULEMENT", "1 À 2 HEURES", "PAR SEMAINE ?", cy=1420, accent=C_CYAN)
    else:
        # Phase 1B (4.50s - 9.00s): 3D NLE Video Editing Workstation & Short 9:16 Preview
        p_age = t - 4.50
        cw, ch = 900, 880
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=36, fill=(16, 20, 30, 248), outline=(*C_CYAN, 225), width=3)

        # Top window dots + title
        for idx_d, col_d in enumerate((C_RED, C_AMBER, C_GREEN)):
            cd.ellipse([34 + idx_d * 30, 30, 52 + idx_d * 30, 48], fill=(*col_d, 255))
        cd.text((140, 24), "STUDIO MONTAGE PRO  //  FORMAT SHORT 9:16", font=get_font(MONO_MED, 24), fill=(220, 226, 238, 255))

        # Center 9:16 Vertical Phone Preview inside NLE
        cd.rounded_rectangle([295, 86, 605, 550], radius=28, fill=(26, 32, 46, 255), outline=(*C_AMBER, 255), width=4)
        # Abstract geometric motion graphics inside the 9:16 phone preview
        for ri in range(3):
            rr = 40 + ri * 32 + int(8 * math.sin(t * 3.0 + ri))
            cd.ellipse([450 - rr, 280 - rr, 450 + rr, 280 + rr], outline=(*C_CYAN, 210 - ri * 50), width=3)
        cd.rounded_rectangle([330, 430, 570, 490], radius=14, fill=(*C_AMBER, 255))
        cd.text((356, 444), "SHORT 9:16 HD", font=get_font(JAKARTA_EBOLD, 28), fill=(14, 16, 22, 255))

        # Multi-track NLE Timeline at bottom of card (`y=585..835`)
        track_colors = [C_AMBER, C_CYAN, C_STRIPE, C_GREEN]
        track_labels = ["VIDÉO 9:16", "MOTION 3D", "SOUS-TITRES", "SOUND DESIGN"]
        for ti in range(4):
            ty = 590 + ti * 58
            cd.text((34, ty + 10), track_labels[ti], font=get_font(MONO_MED, 20), fill=(180, 188, 202, 240))
            for seg_i in range(4):
                sx0 = 215 + seg_i * 160 + (ti % 2) * 18
                sw_seg = 138
                cd.rounded_rectangle([sx0, ty + 6, sx0 + sw_seg, ty + 44], radius=10, fill=(*track_colors[ti], 215))

        # Moving playhead across timeline
        ph_x = int(215 + ((p_age * 165.0) % 620.0))
        cd.line([(ph_x, 575), (ph_x, 840)], fill=(255, 255, 255, 255), width=4)
        cd.polygon([(ph_x - 10, 575), (ph_x + 10, 575), (ph_x, 592)], fill=(*C_RED, 255))

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            220,
            p_age,
            delay=0.02,
            dur=0.42,
            rx_deg=5.0,
            ry_deg=6.0 * math.sin(p_age * 1.2),
            arc_px=-14.0,
        )

        draw_kinetic_caption_stack(
            canvas,
            p_age,
            "JE PRENDS EN CHARGE LE MONTAGE",
            "AU FORMAT SHORT",
            "POUR TOUS TES RÉSEAUX",
            cy=1420,
            accent=C_AMBER,
        )

    return canvas


# ---------------------------------------------------------------------------
# ACT II (09.00s - 20.05s):
# Phase 2A (09.00s - 14.20s): Editorial Ivory Canvas + 4 Tilted Short UI Cards
# Phase 2B (14.20s - 20.05s): Dark Analytics Stage (80k Abonnés + 36 157 vues + Stripe 1000€)
# ---------------------------------------------------------------------------
def render_act2_branding_roi(t: float) -> Image.Image:
    age = t - 9.00
    if t < 14.20:
        # Matches `t=8s-12s` of the original WhatsApp video, 100% faceless with 4 geometric Short cards!
        canvas = get_ivory_canvas(t)
        draw_top_header(canvas, age, "ACTE 02", "IDENTITÉ VISUELLE & BRANDING SUR-MESURE", dark_theme=False)
        d = ImageDraw.Draw(canvas)

        cards_spec = [
            (95, 190, "UNIVERS", "EXPÉRIENCE", (34, 139, 94), -4.5),
            (575, 190, "STYLE", "SUR-MESURE", (235, 138, 44), 4.5),
            (95, 1140, "IMPACT", "RÉTENTION", (24, 28, 38), 3.5),
            (575, 1140, "BRANDING", "PREMIUM", (214, 38, 54), -3.5),
        ]
        for idx, (cx, cy, tag1, tag2, col, tilt) in enumerate(cards_spec):
            ca, cdy = data_reveal(age, delay=idx * 0.07, dur=0.44, offset_y=32.0)
            if ca <= 0.02:
                continue
            cw, ch = 410, 560
            scard = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            sd = ImageDraw.Draw(scard)
            sd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=32, fill=(255, 255, 255, 255), outline=(210, 205, 195, 255), width=3)
            sd.rounded_rectangle([18, 18, cw - 18, 370], radius=22, fill=(*col, 245))
            # Abstract 3D geometric emblem inside each card (zero faces!)
            icx, icy = cw // 2, 194
            for ring in range(3):
                rr = 42 + ring * 28
                sd.ellipse([icx - rr, icy - rr, icx + rr, icy + rr], outline=(255, 255, 255, 195 - ring * 45), width=4)
            sd.polygon([(icx, icy - 48), (icx + 46, icy + 32), (icx - 46, icy + 32)], fill=(255, 255, 255, 235))
            sd.text((34, 398), tag1, font=get_font(MONO_MED, 24), fill=(110, 115, 125, 255))
            sd.text((34, 438), tag2, font=get_font(JAKARTA_EBOLD, 40), fill=(18, 20, 26, 255))

            rot = scard.rotate(tilt * math.cos(age * 1.1 + idx), resample=Image.BICUBIC, expand=True)
            canvas.alpha_composite(rot, (cx, int(cy + cdy)))

        # Center kinetic typography exactly like `t=8s-12s` of original video
        if t < 11.40:
            draw_kinetic_caption_stack(
                canvas,
                age,
                "AVEC DES VIDÉOS",
                "QUALITATIVES",
                "ET PROFESSIONNELLES",
                cy=885,
                dark_theme=False,
                accent=C_AMBER,
            )
        else:
            sub_age = t - 11.40
            active_word = "TON UNIVERS" if t < 12.30 else ("TON STYLE" if t < 13.20 else "TON BRANDING")
            draw_kinetic_caption_stack(
                canvas,
                sub_age,
                "QUI CORRESPONDENT À",
                active_word,
                "SUR TOUS TES RÉSEAUX",
                cy=885,
                dark_theme=False,
                accent=C_AMBER,
            )
        return canvas

    # Phase 2B (14.20s - 20.05s): Dark 3D Analytics, 80k Abonnés, 36 157 Vues & Stripe Notifications
    p_age = t - 14.20
    canvas = get_dark_canvas(t)
    draw_top_header(canvas, p_age, "ACTE 02 // ROI", "NOTORIÉTÉ • VUES QUALIFIÉES • VENTES", dark_theme=True)
    d = ImageDraw.Draw(canvas)

    # 1. Animated Neon-Green Exponential Revenue Curve in background (`t=17s-18s` of original!)
    pts = []
    prog_curve = ease_motion(clamp(p_age / 2.2))
    for i in range(24):
        u = (i / 23.0) * prog_curve
        px = int(70 + u * 940)
        py = int(1260 - (u ** 1.85) * 760 + 28 * math.sin(u * 14.0 + t * 2.0))
        pts.append((px, py))
    if len(pts) >= 2:
        d.line(pts, fill=(*C_GREEN, 255), width=12)

    # 2. Top-Left `80k Abonnés` Rolling Counter Pill (`t=14s` of original!)
    a_sub, dy_sub = data_reveal(p_age, delay=0.05, dur=0.40, offset_y=28.0)
    if a_sub > 0.02:
        sy = int(200 + dy_sub)
        d.rounded_rectangle([68, sy, 520, sy + 118], radius=24, fill=(24, 28, 38, 245), outline=(*C_RED, 255), width=3)
        d.rounded_rectangle([245, sy + 14, 502, sy + 104], radius=18, fill=(*C_RED, 255))
        cnt_k = int(round(80 * ease_motion(clamp(p_age / 1.1))))
        d.text((92, sy + 20), f"{cnt_k}k", font=get_font(JAKARTA_EBOLD, 64), fill=(255, 255, 255, 255))
        d.text((266, sy + 30), "Abonnés", font=get_font(JAKARTA_EBOLD, 46), fill=(255, 255, 255, 255))

    # 3. Center-Left Orange Analytics Card `36 157 Vues Qualifiées` (`t=15s-16s` of original!)
    a_v, dy_v = data_reveal(p_age, delay=0.45, dur=0.44, offset_y=32.0)
    if a_v > 0.02:
        vy = int(365 + dy_v)
        d.rounded_rectangle([68, vy, 580, vy + 330], radius=28, fill=(*C_AMBER, int(245 * a_v)))
        views_num = int(round(36157 * ease_motion(clamp((p_age - 0.45) / 1.2))))
        d.text((98, vy + 24), f"{views_num:,}".replace(",", " "), font=get_font(JAKARTA_EBOLD, 58), fill=(18, 20, 26, 255))
        d.text((98, vy + 94), "VUES QUALIFIÉES  •  +340%", font=get_font(MONO_MED, 22), fill=(35, 38, 46, 240))
        # Sparkline inside orange card
        sp_pts = []
        for si in range(12):
            su = si / 11.0
            spx = int(98 + su * 440)
            spy = int(vy + 275 - su * 115 - 24 * math.sin(su * 9.0 + t * 3.0))
            sp_pts.append((spx, spy))
        d.line(sp_pts, fill=(18, 20, 26, 255), width=6)

    # 4. Stacked Stripe Payment Notification Cards (`t=16s-17s` of original!)
    for s_idx in range(3):
        sa, sdy = data_reveal(p_age, delay=1.25 + s_idx * 0.18, dur=0.42, offset_y=28.0)
        if sa <= 0.02:
            continue
        ny = int(740 + s_idx * 150 + sdy)
        d.rounded_rectangle([120, ny, 960, ny + 128], radius=26, fill=(22, 26, 36, int(248 * sa)), outline=(*C_STRIPE, int(245 * sa)), width=3)
        # Stripe 'S' badge
        d.rounded_rectangle([148, ny + 22, 232, ny + 106], radius=20, fill=(*C_STRIPE, int(255 * sa)))
        d.text((174, ny + 26), "S", font=get_font(JAKARTA_EBOLD, 58), fill=(255, 255, 255, int(255 * sa)))
        d.text((262, ny + 22), "Stripe  •  Maintenant", font=get_font(JAKARTA_BOLD, 30), fill=(255, 255, 255, int(255 * sa)))
        d.text((262, ny + 66), "Vous avez reçu un paiement de 1 000,00 €", font=get_font(INTER_MED, 27), fill=(*C_GREEN, int(255 * sa)))

    if t < 16.0:
        draw_kinetic_caption_stack(canvas, p_age, "ET QUI VONT T'APPORTER", "+ DE NOTORIÉTÉ", "ET D'AUTORITÉ", cy=1440, accent=C_AMBER)
    elif t < 17.8:
        draw_kinetic_caption_stack(canvas, t - 16.0, "PLUS DE VUES QUALIFIÉES", "+ DE VENTES", "CHAQUE SEMAINE", cy=1440, accent=C_AMBER)
    else:
        draw_kinetic_caption_stack(canvas, t - 17.8, "ET DONC AUGMENTER TON", "CHIFFRE D'AFFAIRES", "DURABLEMENT", cy=1440, accent=C_GREEN)

    return canvas


# ---------------------------------------------------------------------------
# ACT III (20.05s - 28.95s): 3D Studio Softbox & Cloud Rush Transfer
# "De ton côté, tu as juste à bloquer deux à trois heures seulement dans le mois..."
# ---------------------------------------------------------------------------
def render_act3_workflow(t: float) -> Image.Image:
    age = t - 20.05
    canvas = get_dark_canvas(t)
    draw_top_header(canvas, age, "ACTE 03", "PROCESSUS ULTRA-SIMPLE & DÉLÉGATION TOTALE", dark_theme=True)

    cw, ch = 900, 920
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=38, fill=(18, 22, 32, 246), outline=(255, 255, 255, 65), width=2)

    if t < 25.40:
        # Phase 3A: 3D Geometric Studio Softbox Octagon + "2 À 3 HEURES / MOIS" Gauge
        # Octagonal softbox diffuser (inspired by the studio softbox in t=20s-23s of original, 100% faceless!)
        scx, scy = 450, 310
        r_oct = 165
        oct_pts = []
        for k in range(8):
            ang = k * (math.pi / 4.0) + math.pi / 8.0
            oct_pts.append((scx + int(r_oct * math.cos(ang)), scy + int(r_oct * math.sin(ang))))
        cd.polygon(oct_pts, fill=(242, 246, 255, 245), outline=(*C_AMBER, 255), width=5)
        # Diffuser grid lines inside octagon
        for off in (-80, -28, 28, 80):
            cd.line([(scx - 110, scy + off), (scx + 110, scy + off)], fill=(180, 190, 210, 190), width=2)
            cd.line([(scx + off, scy - 110), (scx + off, scy + 110)], fill=(180, 190, 210, 190), width=2)

        # Time allocation bar: 2-3h out of 720h in a month!
        cd.rounded_rectangle([58, 540, cw - 58, 840], radius=28, fill=(26, 32, 46, 255), outline=(*C_AMBER, 235), width=3)
        cd.text((92, 572), "TEMPS BLOQUÉ DANS TON AGENDA MENSUEL :", font=get_font(MONO_MED, 24), fill=(190, 198, 212, 255))
        cd.text((92, 624), "2 À 3 HEURES / MOIS", font=get_font(JAKARTA_EBOLD, 64), fill=(*C_AMBER, 255))
        cd.text((92, 725), "Pour écrire & tourner tous tes contenus (0,4 % du mois)", font=get_font(INTER_MED, 28), fill=(255, 255, 255, 245))
    else:
        # Phase 3B (25.40s - 28.95s): Cloud Rush Upload -> "PLUS RIEN À FAIRE ✕"
        u_age = t - 25.40
        p_up = ease_motion(clamp(u_age / 1.4))
        cd.text((76, 56), "TRANSFERT DES RUSHS  //  AUTOMATISATION", font=get_font(MONO_MED, 25), fill=(*C_CYAN, 255))

        # 3 Rush video file cards flying into the Studio Cloud with Disney Anticipation + Arc Trajectory!
        for fi in range(3):
            f_loc = clamp((u_age - fi * 0.08) / 0.52)
            ant_p = disney_anticipation_launch(f_loc, dip_ratio=0.18, dip_amount=0.05)
            fx_base = 88 + fi * 260
            fy_base = 150 + int(16 * math.sin(t * 3.0 + fi))
            ax_f, ay_f = disney_arc_position(float(fx_base - 24), float(fy_base + 34), float(fx_base), float(fy_base), clamp(ant_p), arc_offset_px=12.0)
            fx, fy = int(round(ax_f)), int(round(ay_f))
            cd.rounded_rectangle([fx, fy, fx + 220, fy + 160], radius=22, fill=(28, 36, 52, 255), outline=(*C_CYAN, 230), width=3)
            cd.polygon([(fx + 88, fy + 45), (fx + 88, fy + 105), (fx + 142, fy + 75)], fill=(*C_AMBER, 255))
            cd.text((fx + 38, fy + 118), f"RUSH_0{fi+1}.MP4", font=get_font(MONO_MED, 21), fill=(255, 255, 255, 255))

        # Progress bar 100%
        cd.rounded_rectangle([88, 370, cw - 88, 426], radius=28, fill=(26, 32, 46, 255))
        bar_w = int((cw - 176) * p_up)
        if bar_w > 8:
            cd.rounded_rectangle([88, 370, 88 + bar_w, 426], radius=28, fill=(*C_GREEN, 255))

        # Big badge: "TU N'AS PLUS RIEN À FAIRE ✕" (`t=27s` of original!)
        cd.rounded_rectangle([72, 485, cw - 72, 835], radius=32, fill=(28, 20, 26, 255), outline=(*C_RED, 245), width=4)
        cd.text((395, 510), "✕", font=get_font(JAKARTA_EBOLD, 110), fill=(*C_RED, 255))
        cd.text((135, 650), "TU N'AS PLUS RIEN À FAIRE", font=get_font(JAKARTA_EBOLD, 48), fill=(*C_PEACH, 255))
        cd.text((195, 725), "Je m'occupe de 100 % du montage", font=get_font(INTER_MED, 32), fill=(255, 255, 255, 245))

    composite_hero_card_3layers(
        canvas,
        card,
        (W - cw) // 2,
        210,
        age if t < 25.40 else (t - 25.40),
        delay=0.02,
        dur=0.44,
        rx_deg=5.0 * math.sin(age * 1.1),
        ry_deg=-4.5 * math.cos(age * 0.9),
        arc_px=12.0,
    )

    if t < 25.40:
        draw_kinetic_caption_stack(canvas, age, "TU AS JUSTE À BLOQUER", "2 À 3 HEURES", "DANS LE MOIS POUR TOURNER", cy=1420, accent=C_PEACH)
    else:
        draw_kinetic_caption_stack(canvas, t - 25.40, "TU M'ENVOIES TOUS TES RUSHS", "PLUS RIEN À FAIRE", "ZÉRO CHARGE MENTALE", cy=1420, accent=C_AMBER)

    return canvas


# ---------------------------------------------------------------------------
# ACT IV (28.95s - 36.75s):
# Phase 4A (28.95s - 32.80s): Editorial Ivory Poster ("PACKS DE 10 À 15 VIDÉOS / EN 1 SEMAINE OUVRÉE")
# Phase 4B (32.80s - 36.75s): Dark Monthly Posting Grid ("TOUS LES 2 À 3 JOURS SUR LE MOIS")
# ---------------------------------------------------------------------------
def render_act4_delivery(t: float) -> Image.Image:
    age = t - 28.95
    if t < 32.80:
        # Exact match to `t=28s-31s` white editorial kinetic poster of original video!
        canvas = get_ivory_canvas(t)
        draw_top_header(canvas, age, "ACTE 04", "LIVRAISON RAPIDE & CLÉ EN MAIN", dark_theme=False)
        d = ImageDraw.Draw(canvas)

        # Fan of 12 vertical 9:16 video cards in upper stage (`y=220..740`)
        for idx in range(7):
            ang = (idx - 3) * 7.5 * ease_motion(clamp(age / 0.55))
            vc = Image.new("RGBA", (220, 360), (0, 0, 0, 0))
            vd = ImageDraw.Draw(vc)
            col = C_AMBER if idx == 3 else (28, 32, 42)
            vd.rounded_rectangle([0, 0, 219, 359], radius=24, fill=(*col, 250), outline=(255, 255, 255, 220), width=3)
            vd.text((36, 150), f"SHORT #{idx+1:02d}", font=get_font(JAKARTA_EBOLD, 28), fill=(255, 255, 255, 255))
            rot = vc.rotate(-ang, resample=Image.BICUBIC, expand=True)
            rx = W // 2 - rot.size[0] // 2 + int((idx - 3) * 82)
            ry = 250 + abs(idx - 3) * 18
            canvas.alpha_composite(rot, (rx, ry))

        # Center editorial typography (`Je te livre / des packs / de 10 à 15 vidéos / en une semaine ouvrée`)
        f_top = get_font(JAKARTA_EBOLD, 56)
        f_big = get_font(JAKARTA_EBOLD, 92)
        d.text((365, 760), "Je te livre", font=f_top, fill=C_INK)
        d.text((275, 825), "des packs", font=f_big, fill=C_PEACH)
        d.text((215, 935), "de 10 à 15 vidéos", font=get_font(JAKARTA_EBOLD, 76), fill=C_INK)

        if t >= 30.30:
            s_age = t - 30.30
            sa, sdy = data_reveal(s_age, delay=0.0, dur=0.40, offset_y=28.0)
            sy = int(1120 + sdy)
            # Calendar icon + "en une semaine ouvrée" (`t=30s` of original!)
            d.rounded_rectangle([140, sy, 940, sy + 210], radius=32, fill=(255, 255, 255, int(250 * sa)), outline=(20, 22, 28, int(220 * sa)), width=3)
            # Mini calendar icon on left
            d.rounded_rectangle([185, sy + 38, 315, sy + 168], radius=20, fill=(20, 22, 28, int(255 * sa)))
            d.rounded_rectangle([185, sy + 38, 315, sy + 76], radius=20, fill=(*C_AMBER, int(255 * sa)))
            d.text((222, sy + 88), "5J", font=get_font(JAKARTA_EBOLD, 46), fill=(255, 255, 255, int(255 * sa)))
            d.text((355, sy + 38), "en une semaine ouvrée", font=get_font(JAKARTA_EBOLD, 44), fill=(*C_PEACH, int(255 * sa)))
            # Green checkmark + "prêtes à être postées" (`t=31s` of original!)
            d.rounded_rectangle([355, sy + 110, 415, sy + 170], radius=14, fill=(*C_GREEN, int(255 * sa)))
            d.text((369, sy + 112), "✓", font=get_font(JAKARTA_EBOLD, 44), fill=(255, 255, 255, int(255 * sa)))
            d.text((435, sy + 118), "prêtes à être postées", font=get_font(JAKARTA_EBOLD, 42), fill=(20, 22, 28, int(255 * sa)))

        return canvas

    # Phase 4B (32.80s - 36.75s): Dark Monthly Calendar Grid with Golden Circled Days (`t=34s-35s` of original!)
    p_age = t - 32.80
    canvas = get_dark_canvas(t)
    draw_top_header(canvas, p_age, "ACTE 04 // RÉGULARITÉ", "PUBLICATION CONTINUE SUR TOUT LE MOIS", dark_theme=True)

    cw, ch = 880, 860
    cal = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cal)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=38, fill=(14, 16, 22, 250), outline=(*C_AMBER, 220), width=3)
    cd.text((64, 42), "CALENDRIER DE PUBLICATION  •  1 POST TOUS LES 2–3 JOURS", font=get_font(MONO_MED, 23), fill=(*C_AMBER, 255))

    # Days 1..31 with golden circles on days 1, 3, 5, 8, 10, 12, 14, 16, 18, 21, 23, 26, 28, 30
    circled_days = {1, 3, 5, 8, 10, 12, 14, 16, 18, 21, 23, 26, 28, 30}
    f_num = get_font(JAKARTA_BOLD, 38)
    for day in range(1, 32):
        idx = day - 1
        r, c = divmod(idx, 7)
        cx = 76 + c * 112
        cy = 140 + r * 135
        is_post = day in circled_days
        if is_post:
            cd.ellipse([cx - 14, cy - 10, cx + 74, cy + 78], fill=(*C_AMBER, 48), outline=(*C_AMBER, 255), width=4)
            cd.text((cx + (18 if day < 10 else 6), cy + 10), str(day), font=f_num, fill=(*C_AMBER, 255))
        else:
            cd.text((cx + (18 if day < 10 else 6), cy + 10), str(day), font=f_num, fill=(210, 216, 228, 220))

    composite_hero_card_3layers(
        canvas,
        cal,
        (W - cw) // 2,
        220,
        p_age,
        delay=0.02,
        dur=0.44,
        rx_deg=5.5 * math.sin(p_age * 1.3),
        ry_deg=-4.5 * math.cos(p_age * 1.0),
        arc_px=-12.0,
    )

    draw_kinetic_caption_stack(
        canvas,
        p_age,
        "POUVOIR POSTER TOUS LES",
        "2 À 3 JOURS",
        "SUR TOUT LE MOIS",
        cy=1420,
        accent=C_PEACH,
    )
    return canvas


# ---------------------------------------------------------------------------
# ACT V (36.75s - 52.95s):
# Phase 5A (36.75s - 43.20s): 3D Leverage Dashboard ("3H PASSÉES -> PUBLIER RÉGULIÈREMENT")
# Phase 5B (43.20s - 52.95s): Editorial White/Gold Triptych (Pocket Watch + Brain Core + Enterprise)
# ---------------------------------------------------------------------------
def render_act5_expertise(t: float) -> Image.Image:
    if t < 43.20:
        age = t - 36.75
        canvas = get_dark_canvas(t)
        draw_top_header(canvas, age, "ACTE 05", "EFFET DE LEVIER MAXIMAL", dark_theme=True)

        # 3D Leverage Cards: [3H CRÉATION] ===> [PUBLICATION RÉGULIÈRE] + [CROISSANCE RÉSEAUX]
        cw, ch = 880, 900
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=38, fill=(18, 22, 32, 246), outline=(*C_AMBER, 225), width=3)

        steps = [
            (0.05, "01", "3H PASSÉES SEULEMENT", "Création & tournage concentrés", C_CYAN),
            (1.40, "02", "PUBLIER RÉGULIÈREMENT", "Présence constante toute l'année", C_AMBER),
            (3.10, "03", "DÉVELOPPER TON ACTIVITÉ", "Avec des vidéos travaillées & pro", C_GREEN),
        ]
        for idx, (delay, num_s, t1, t2, col) in enumerate(steps):
            sa, sdy = data_reveal(age, delay=delay, dur=0.44, offset_y=28.0)
            if sa <= 0.02:
                continue
            ry = int(76 + idx * 265 + sdy)
            cd.rounded_rectangle([46, ry, cw - 46, ry + 225], radius=28, fill=(26, 32, 46, int(248 * sa)), outline=(*col, int(245 * sa)), width=3)
            cd.rounded_rectangle([76, ry + 36, 176, ry + 136], radius=22, fill=(*col, int(255 * sa)))
            cd.text((98, ry + 54), num_s, font=get_font(JAKARTA_EBOLD, 52), fill=(14, 16, 22, int(255 * sa)))
            cd.text((210, ry + 42), t1, font=get_font(JAKARTA_EBOLD, 42), fill=(255, 255, 255, int(255 * sa)))
            cd.text((210, ry + 112), t2, font=get_font(INTER_MED, 30), fill=(190, 198, 214, int(245 * sa)))

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            210,
            age,
            delay=0.02,
            dur=0.44,
            rx_deg=4.5 * math.sin(age * 1.1),
            ry_deg=-4.0 * math.cos(age * 0.9),
            arc_px=12.0,
        )

        if t < 39.80:
            draw_kinetic_caption_stack(canvas, age, "EN SEULEMENT 3H PASSÉES", "PUBLIER RÉGULIÈREMENT", "SANS INTERRUPTION", cy=1420, accent=C_AMBER)
        else:
            draw_kinetic_caption_stack(canvas, t - 39.80, "POUR DÉVELOPPER TON ACTIVITÉ", "VIDÉOS TRAVAILLÉES", "SUR TOUS TES RÉSEAUX", cy=1420, accent=C_GREEN)
        return canvas

    # Phase 5B (43.20s - 52.95s): Exact match to `t=42s-50s` White/Ivory Editorial Triptych!
    p_age = t - 43.20
    canvas = get_ivory_canvas(t)
    draw_top_header(canvas, p_age, "ACTE 05 // FOCUS", "CONCENTRE-TOI SUR TA ZONE D'EXPERTISE", dark_theme=False)
    d = ImageDraw.Draw(canvas)

    if t < 47.20:
        # Sub-scene 1 (`t=42s-46s` of original): 3D Golden Pocket Watch + "Et tu ne perds plus des heures chaque semaine à faire toi-même tes contenus et tes montages"
        # Draw detailed 3D Golden Pocket Watch in center (`x=540, y=680`)
        wcx, wcy = 540, 650
        # Top crown & ring
        d.ellipse([wcx - 48, wcy - 285, wcx + 48, wcy - 195], outline=(185, 138, 42, 255), width=10)
        d.rounded_rectangle([wcx - 26, wcy - 210, wcx + 26, wcy - 165], radius=8, fill=(215, 168, 58, 255))
        # Outer gold case
        d.ellipse([wcx - 185, wcy - 185, wcx + 185, wcy + 185], fill=(228, 182, 72, 255), outline=(160, 115, 28, 255), width=8)
        d.ellipse([wcx - 155, wcy - 155, wcx + 155, wcy + 155], fill=(252, 250, 244, 255), outline=(185, 142, 48, 255), width=4)
        # Roman/Arabic numerals & animated hands
        f_num = get_font(JAKARTA_BOLD, 28)
        for hr in range(1, 13):
            ang = math.radians(hr * 30 - 90)
            nx = wcx + int(122 * math.cos(ang)) - 12
            ny = wcy + int(122 * math.sin(ang)) - 16
            d.text((nx, ny), str(hr), font=f_num, fill=C_INK)
        ang_fast = t * 6.0
        d.line([(wcx, wcy), (wcx + int(95 * math.cos(ang_fast)), wcy + int(95 * math.sin(ang_fast)))], fill=C_INK, width=6)
        d.line([(wcx, wcy), (wcx + int(65 * math.cos(ang_fast * 0.2)), wcy + int(65 * math.sin(ang_fast * 0.2)))], fill=C_RED, width=8)
        d.ellipse([wcx - 10, wcy - 10, wcx + 10, wcy + 10], fill=C_INK)

        draw_kinetic_caption_stack(
            canvas,
            p_age,
            "ET TU NE PERDS PLUS",
            "DES HEURES",
            "À FAIRE TOI-MÊME TES MONTAGES",
            cy=1180,
            dark_theme=False,
            accent=C_PEACH,
        )
    else:
        # Sub-scene 2 (`t=47s-52.95s` of original): Dashed Circle + 3D Neural Brain/Expertise Core + "ta zone d'expertise / développement de ton entreprise"
        b_age = t - 47.20
        bcx, bcy = 540, 660
        # Rotating dashed circle (`t=47s-48s` of original!)
        r_dash = 210
        for seg in range(24):
            a0 = seg * 15 + t * 25.0
            d.arc([bcx - r_dash, bcy - r_dash, bcx + r_dash, bcy + r_dash], start=a0, end=a0 + 8, fill=(90, 95, 108, 220), width=4)

        # Stylized 3D Neural Brain / Expertise Core inside dashed circle
        d.ellipse([bcx - 135, bcy - 105, bcx + 135, bcy + 105], fill=(238, 148, 142, 255), outline=(185, 88, 84, 255), width=5)
        # Neural folds & glowing synapse nodes
        nodes = [
            (bcx - 75, bcy - 45), (bcx - 20, bcy - 65), (bcx + 55, bcy - 45),
            (bcx - 85, bcy + 15), (bcx, bcy + 5), (bcx + 75, bcy + 20),
            (bcx - 35, bcy + 60), (bcx + 35, bcy + 55),
        ]
        for n1, n2 in zip(nodes[:-1], nodes[1:]):
            d.line([n1, n2], fill=(175, 72, 68, 255), width=5)
        for nx, ny in nodes:
            d.ellipse([nx - 10, ny - 10, nx + 10, ny + 10], fill=(255, 235, 180, 255), outline=(175, 72, 68, 255), width=3)

        if t < 50.10:
            draw_kinetic_caption_stack(
                canvas,
                b_age,
                "EN LAISSANT DE CÔTÉ",
                "TA ZONE D'EXPERTISE",
                "ET CE QUE TU MAÎTRISES VRAIMENT",
                cy=1180,
                dark_theme=False,
                accent=C_PEACH,
            )
        else:
            draw_kinetic_caption_stack(
                canvas,
                t - 50.10,
                "CONCENTRE-TOI SUR LE",
                "DÉVELOPPEMENT",
                "DE TON ENTREPRISE",
                cy=1180,
                dark_theme=False,
                accent=C_AMBER,
            )

    return canvas


# ---------------------------------------------------------------------------
# ACT VI (52.95s - 63.95s): 3D Value Pillars & Final Contact CTA Portal
# "Alors si tu veux gagner énormément de temps chaque mois, avoir des vidéos de qualité,
#  développer tes réseaux et ton image de marque de manière sérieuse, je t'invite à me
#  contacter et on parle de ton projet ensemble."
# ---------------------------------------------------------------------------
def render_act6_cta(t: float) -> Image.Image:
    age = t - 52.95
    canvas = get_dark_canvas(t)
    draw_top_header(canvas, age, "ACTE 06 // PASSER À L'ACTION", "GAGNE DU TEMPS • DÉVELOPPE TON IMAGE DE MARQUE", dark_theme=True)

    # 3 Value Pillar Bento Cards in upper half (`y=170..880`)
    pillars = [
        (0.05, "01 • GAIN DE TEMPS", "Économise des dizaines d'heures chaque mois", C_CYAN),
        (1.65, "02 • VIDÉOS DE QUALITÉ", "Montage pro 9:16 adapté à ton branding", C_AMBER),
        (3.40, "03 • IMAGE DE MARQUE", "Développe tes réseaux de manière sérieuse", C_GREEN),
    ]
    for idx, (delay, title_p, sub_p, col) in enumerate(pillars):
        if age - delay <= 0.02:
            continue
        cw, ch = 880, 205
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=28, fill=(18, 22, 32, 245), outline=(*col, 245), width=3)
        cd.rounded_rectangle([24, 24, 42, ch - 24], radius=8, fill=(*col, 255))
        cd.text((68, 34), title_p, font=get_font(JAKARTA_EBOLD, 42), fill=(*col, 255))
        cd.text((68, 108), sub_p, font=get_font(INTER_MED, 30), fill=(240, 244, 252, 250))
        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            175 + idx * 230,
            age,
            delay=delay,
            dur=0.42,
            rx_deg=3.5 * math.sin(age + idx),
            ry_deg=-3.5 * math.cos(age + idx),
            arc_px=10.0 if idx % 2 == 0 else -10.0,
        )

    # Final 3D Contact Portal Card (`y=890..1310`)
    cta_age = max(0.0, age - 4.80)
    pw, ph = 880, 380
    portal = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(portal)
    is_final = t >= 57.80
    border_c = C_AMBER if is_final else C_CYAN
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=36, fill=(22, 26, 38, 250), outline=(*border_c, 255), width=4)
    pd.text((76, 42), "PRÊT À DÉLÉGUER TES MONTAGES SHORT ?", font=get_font(MONO_MED, 26), fill=(*C_PEACH, 255))
    pd.rounded_rectangle([56, 115, pw - 56, 255], radius=28, fill=(*C_AMBER, 255))
    f_cta = get_font(JAKARTA_EBOLD, 42)
    cta_txt = "CONTACTE-MOI MAINTENANT"
    bb_cta = pd.textbbox((0, 0), cta_txt, font=f_cta)
    pd.text(((pw - (bb_cta[2] - bb_cta[0])) // 2, 152), cta_txt, font=f_cta, fill=(14, 16, 22, 255))
    sub_cta = "On parle de ton projet ensemble  →"
    f_sub = get_font(JAKARTA_BOLD, 34)
    bb_sub = pd.textbbox((0, 0), sub_cta, font=f_sub)
    pd.text(((pw - (bb_sub[2] - bb_sub[0])) // 2, 288), sub_cta, font=f_sub, fill=(255, 255, 255, 255))

    composite_hero_card_3layers(
        canvas,
        portal,
        (W - pw) // 2,
        905,
        cta_age if cta_age > 0 else age,
        delay=0.10,
        dur=0.45,
        rx_deg=4.5 * math.sin(t * 1.4),
        ry_deg=4.5 * math.cos(t * 1.1),
        arc_px=12.0,
    )

    if t < 57.80:
        draw_kinetic_caption_stack(canvas, age, "GAGNER DU TEMPS CHAQUE MOIS", "VIDÉOS DE QUALITÉ", "ET DÉVELOPPER TON IMAGE", cy=1460, accent=C_CYAN)
    else:
        draw_kinetic_caption_stack(canvas, t - 57.80, "JE T'INVITE À ME CONTACTER", "PARLONS DE TON PROJET", "ENSEMBLE DÈS AUJOURD'HUI", cy=1460, accent=C_AMBER)

    return canvas


# ---------------------------------------------------------------------------
# Master Frame Dispatcher + Velocity-Matched Seam Transitions
# ---------------------------------------------------------------------------
def _render_scene(t: float) -> Image.Image:
    if t < 9.00:
        return render_act1_hook(t)
    if t < 20.05:
        return render_act2_branding_roi(t)
    if t < 28.95:
        return render_act3_workflow(t)
    if t < 36.75:
        return render_act4_delivery(t)
    if t < 52.95:
        return render_act5_expertise(t)
    return render_act6_cta(t)


SEAMS = [
    (9.00, 0.24, "zoom_through"),
    (14.20, 0.24, "cut_the_curve"),
    (20.05, 0.24, "rack_focus"),
    (28.95, 0.24, "cut_the_curve"),
    (32.80, 0.24, "zoom_through"),
    (36.75, 0.24, "rack_focus"),
    (43.20, 0.24, "cut_the_curve"),
    (52.95, 0.26, "zoom_through"),
]


def render_frame(t: float) -> np.ndarray:
    for t_seam, half_w, mode in SEAMS:
        if abs(t - t_seam) <= half_w:
            p = clamp((t - (t_seam - half_w)) / (2.0 * half_w))
            im_a = _render_scene(t_seam - 0.03)
            im_b = _render_scene(t_seam + 0.03)
            if mode == "zoom_through":
                out = zoom_through_seam(im_a, im_b, p, inverse=False)
            elif mode == "cut_the_curve":
                out = cut_the_curve_seam(im_a, im_b, p, direction="left")
            else:
                out = rack_focus_blur_cut(im_a, im_b, p)
            return np.array(out.convert("RGB"), dtype=np.uint8)

    im = _render_scene(t)
    return np.array(im.convert("RGB"), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Master Audio Mixer (New Voiceover + Procedural Cinema Soundtrack & SFX)
# ---------------------------------------------------------------------------
def build_master_audio():
    with open(TIMELINE_JSON, "r") as f:
        tl = json.load(f)

    sr = 48000
    total_samples = int(round(TOTAL_DURATION * sr))
    t = np.arange(total_samples, dtype=np.float32) / float(sr)

    vo_l = np.zeros(total_samples, dtype=np.float32)
    vo_r = np.zeros(total_samples, dtype=np.float32)

    for seg in tl["segments"]:
        wav_path = seg["file"]
        start_s = int(round(seg["start"] * sr))
        with wave.open(wav_path, "rb") as wf:
            n_f = wf.getnframes()
            raw = wf.readframes(n_f)
        arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0
        end_s = min(total_samples, start_s + arr.shape[0])
        length = end_s - start_s
        if length > 0:
            vo_l[start_s:end_s] += arr[:length, 0] * 1.12
            vo_r[start_s:end_s] += arr[:length, 1] * 1.12

    # Warm ambient electronic bed (-23 dB)
    pad_l = 0.020 * np.sin(2 * np.pi * 65.41 * t) + 0.012 * np.sin(2 * np.pi * 130.81 * t + 0.3)
    pad_r = 0.020 * np.sin(2 * np.pi * 65.41 * t) + 0.012 * np.sin(2 * np.pi * 196.00 * t - 0.3)

    sfx_l = np.zeros_like(t)
    sfx_r = np.zeros_like(t)
    rng = np.random.default_rng(77)

    for t_seam, _, _ in SEAMS:
        i0 = int(t_seam * sr)
        dur_s = int(0.30 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.6
            noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32)
            sweep = np.sin(2 * np.pi * (100.0 + 260.0 * lt) * lt * 0.30)
            w_sig = (0.045 * sweep + 0.016 * noise) * env
            sfx_l[i0:i1] += w_sig
            sfx_r[i0:i1] += w_sig

    # Synchronized UI Micro-Pop & Chime Transients (`klik-anim/references/music-motion.md`)
    pop_times = [
        0.15, 2.30, 4.55, 9.10, 9.17, 9.24, 9.31,
        14.30, 14.70, 15.50, 15.68, 15.86,
        20.15, 25.50, 25.58, 25.66,
        29.05, 30.35, 32.90,
        36.85, 38.20, 39.90, 43.30, 47.25,
        53.05, 54.65, 56.40, 57.85,
    ]
    for pt in pop_times:
        i0 = int(pt * sr)
        dur_p = int(0.085 * sr)
        i1 = min(total_samples, i0 + dur_p)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-28.0 * lt)
            freq = 660.0 if int(pt * 10) % 2 == 0 else 880.0
            chime = 0.032 * np.sin(2 * np.pi * freq * lt * 0.085) * env
            sfx_l[i0:i1] += chime
            sfx_r[i0:i1] += chime

    mix_l = np.clip(vo_l + pad_l + sfx_l, -0.98, 0.98)
    mix_r = np.clip(vo_r + pad_r + sfx_r, -0.98, 0.98)
    stereo_int16 = (np.stack([mix_l, mix_r], axis=-1) * 32767.0).astype(np.int16)

    with wave.open(MIXED_WAV, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo_int16.tobytes())


def _render_frame_bytes(fi: int) -> bytes:
    return render_frame(fi / FPS).tobytes()


# ---------------------------------------------------------------------------
# Main Preview & Full Renderer
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=str, default="", help="Save a 16-frame preview contact sheet")
    args = parser.parse_args()

    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        sample_times = [
            1.5, 3.2, 6.2, 10.4,
            12.6, 15.6, 18.2, 22.4,
            26.8, 31.2, 34.6, 38.8,
            41.5, 45.2, 49.5, 59.5,
        ]
        cols, rows = 4, 4
        tw, th = 270, 480
        sheet = Image.new("RGB", (cols * tw, rows * th), (12, 12, 16))
        for idx, st in enumerate(sample_times):
            rgb = render_frame(st)
            thumb = Image.fromarray(rgb).resize((tw, th), Image.LANCZOS)
            td = ImageDraw.Draw(thumb)
            td.rectangle([8, 8, 128, 38], fill=(0, 0, 0))
            td.text((14, 13), f"t={st:05.2f}s", fill=(245, 166, 35))
            sheet.paste(thumb, ((idx % cols) * tw, (idx // cols) * th))
        sheet.save(args.preview, quality=92)
        print(f"Saved preview contact sheet to {args.preview}")
        return

    from concurrent.futures import ProcessPoolExecutor
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(FILM_DIR, exist_ok=True)
    build_master_audio()

    encode_cmd = [
        ffmpeg_exe,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        f"{FPS}",
        "-i",
        "-",
        "-i",
        MIXED_WAV,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        OUT_MP4,
    ]
    proc_out = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    with ProcessPoolExecutor(max_workers=2) as pool:
        for fi, raw_bytes in enumerate(pool.map(_render_frame_bytes, range(TOTAL_FRAMES), chunksize=24)):
            proc_out.stdin.write(raw_bytes)
            if (fi + 1) % 240 == 0 or fi == TOTAL_FRAMES - 1:
                print(f"Rendered {fi + 1}/{TOTAL_FRAMES} frames ({(fi + 1) / TOTAL_FRAMES * 100:.1f}%)", flush=True)
    proc_out.stdin.close()
    ret = proc_out.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")
    print(f"Successfully rendered {OUT_MP4}")


if __name__ == "__main__":
    main()
