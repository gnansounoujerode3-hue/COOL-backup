#!/usr/bin/env python3
"""
Master 9:16 Studio Motion-Design Video Compositor (`devis-designer-motion` v2)
For `https://devis-designer-app.jerode.workers.dev/` (Devis Designer — Devis & Factures Pro en ligne).

Built with:
  - `.claude/skills/motion-code-harvester/scripts/motion_engine.py`
    (`zoom_through_seam`, `cut_the_curve_seam`, `rack_focus_blur_cut`)
  - `.claude/skills/animation-design-rules/scripts/animation_rules_engine.py`
    (`emil_ease_out`, `emil_ease_in_out`, `disney_overshoot_ease`, `disney_squash_stretch`,
     `disney_arc_position`, `disney_follow_through_layers`, `counter_motion_ambient`)
  - Official 3D Blue Glass Logo (`devis-designer-motion/assets/logo.png`)
  - French Advertising Voiceover (`voice-02`) + Procedural Cinema Soundtrack & UI SFX
  - Strictly <= 2 subtitle lines at a time (`draw_two_line_caption`)
"""

import argparse
import json
import math
import os
import subprocess
import sys
import wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/animation-design-rules/scripts")
from motion_engine import (
    zoom_through_seam,
    cut_the_curve_seam,
    rack_focus_blur_cut,
)
from animation_rules_engine import (
    emil_ease_out,
    emil_ease_in_out,
    disney_overshoot_ease,
    disney_squash_stretch,
    disney_arc_position,
    disney_follow_through_layers,
    counter_motion_ambient,
)

W, H = 1080, 1920
FPS = 30.0
TOTAL_DURATION = 56.45
TOTAL_FRAMES = int(round(TOTAL_DURATION * FPS))

PROJECT_DIR = "/home/user/COOL-backup/devis-designer-motion"
ASSETS_DIR = f"{PROJECT_DIR}/assets"
AUDIO_DIR = f"{ASSETS_DIR}/audio"
FILM_DIR = f"{PROJECT_DIR}/film"
LOGO_PATH = f"{ASSETS_DIR}/logo.png"
TIMELINE_JSON = f"{AUDIO_DIR}/timeline.json"
MIXED_WAV = f"{AUDIO_DIR}/master_voiceover_mix.wav"
OUT_MP4 = f"{FILM_DIR}/devis-designer-motion-design-9x16.mp4"

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"

# Studio Color System (Dark Obsidian Stage + Editorial Ivory Stage + Royal Blue & Gold Accents)
C_DARK_BG = (10, 13, 22)        # Deep obsidian studio canvas
C_IVORY_BG = (247, 244, 237)    # Warm editorial ivory paper canvas
C_BLUE = (37, 99, 235)          # #2563EB Devis Designer royal blue
C_CYAN = (56, 189, 248)         # #38BDF8 sky cyan highlight
C_INDIGO = (99, 102, 241)       # #6366F1 studio indigo
C_PURPLE = (139, 92, 246)       # #8B5CF6 creative purple
C_AMBER = (245, 166, 35)        # #F5A623 warm gold highlight
C_GREEN = (16, 185, 129)        # #10B981 emerald validation green
C_ORANGE = (249, 115, 22)       # #F97316 corporate orange
C_RED = (239, 68, 68)           # #EF4444 stamp / alert red
C_INK = (17, 20, 28)            # Deep charcoal ink for ivory stage

_FONT_CACHE = {}
_BG_CACHE = {}
_LOGO_CACHE = {}


def get_font(path: str, size: int):
    size = max(12, int(round(size)))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def get_logo(size: int) -> Image.Image:
    if size not in _LOGO_CACHE:
        im = Image.open(LOGO_PATH).convert("RGBA")
        _LOGO_CACHE[size] = im.resize((size, size), Image.LANCZOS)
    return _LOGO_CACHE[size]


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def ease_motion(p: float) -> float:
    return emil_ease_out(clamp(p))


def data_reveal(age: float, delay: float = 0.0, dur: float = 0.40, offset_y: float = 28.0):
    t_loc = age - delay
    if t_loc <= 0.0:
        return 0.0, offset_y
    e = emil_ease_out(clamp(t_loc / max(1e-4, dur)))
    return e, offset_y * (1.0 - e)


# ---------------------------------------------------------------------------
# Vector Icon Helpers (Zero Unicode Box Fallbacks!)
# ---------------------------------------------------------------------------
def draw_check_icon(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, bg_col, fg_col=(255, 255, 255, 255), width: int = 4):
    if bg_col is not None:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg_col)
    pts = [
        (cx - int(r * 0.42), cy + int(r * 0.02)),
        (cx - int(r * 0.10), cy + int(r * 0.36)),
        (cx + int(r * 0.46), cy - int(r * 0.32)),
    ]
    d.line(pts, fill=fg_col, width=width, joint="curve")


def draw_arrow_right(d: ImageDraw.ImageDraw, cx: int, cy: int, size: int, col, width: int = 4):
    x0 = cx - size
    x1 = cx + size
    d.line([(x0, cy), (x1, cy)], fill=col, width=width)
    d.line([(x1 - int(size * 0.55), cy - int(size * 0.50)), (x1, cy)], fill=col, width=width)
    d.line([(x1 - int(size * 0.55), cy + int(size * 0.50)), (x1, cy)], fill=col, width=width)


# ---------------------------------------------------------------------------
# 3D Projective Homography (`warp_plane_3d`) + Disney Follow-Through Card Layer
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
    focal: float = 1450.0,
    squash_progress: float = 1.0,
    squash_intensity: float = 0.028,
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
        z = max(250.0, focal + p3[2])
        dst_pts.append((cx + (p3[0] * focal) / z, cy + (p3[1] * focal) / z))
    coeffs = _solve_perspective_coeffs(src_pts, dst_pts)
    return img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BILINEAR)


def _get_cached_shadow(cw: int, ch: int) -> Image.Image:
    key = ("shadow", cw, ch)
    if key not in _BG_CACHE:
        sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([18, 22, cw - 18, ch - 10], radius=38, fill=(0, 0, 0, 118))
        _BG_CACHE[key] = sh
    return _BG_CACHE[key]


def composite_hero_card_3layers(
    canvas: Image.Image,
    card: Image.Image,
    target_x: int,
    target_y: int,
    age: float,
    delay: float = 0.0,
    dur: float = 0.42,
    rx_deg: float = 0.0,
    ry_deg: float = 0.0,
    rz_deg: float = 0.0,
    arc_px: float = 12.0,
):
    local_age = age - delay
    if local_age <= 0.0:
        return
    layers = disney_follow_through_layers(local_age, base_dur=dur)
    shadow_p = layers["shadow"]
    sc = layers["scale"]

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
        squash_intensity=0.028,
    )

    if shadow_p > 0.15:
        cw, ch = card.size
        sh = _get_cached_shadow(cw, ch)
        sh_y_off = int(14 + 10 * shadow_p)
        sh_x_off = int(6 * shadow_p)
        canvas.alpha_composite(sh, (int(round(ax)) + sh_x_off, int(round(ay)) + sh_y_off))

    canvas.alpha_composite(warped, (int(round(ax)), int(round(ay))))


# ---------------------------------------------------------------------------
# Cached Studio Canvases (Dark Obsidian Grid & Editorial Ivory Grid)
# ---------------------------------------------------------------------------
def get_dark_canvas(t: float, age: float = 0.5) -> Image.Image:
    if "dark_base" not in _BG_CACHE:
        bg = Image.new("RGBA", (W, H), (*C_DARK_BG, 255))
        d = ImageDraw.Draw(bg)
        for gx in range(0, W, 72):
            d.line([(gx, 0), (gx, H)], fill=(22, 29, 46, 255), width=1)
        for gy in range(0, H, 72):
            d.line([(0, gy), (W, gy)], fill=(22, 29, 46, 255), width=1)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([60, 180, W - 60, H - 380], fill=(37, 99, 235, 42))
        gd.ellipse([180, 920, W - 180, H - 160], fill=(245, 166, 35, 26))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=95))
        bg = Image.alpha_composite(bg, glow)
        _BG_CACHE["dark_base"] = bg
    im = _BG_CACHE["dark_base"].copy()
    d = ImageDraw.Draw(im)
    _, hero_dy = data_reveal(age, delay=0.0, dur=0.45, offset_y=28.0)
    _, amb_dy = counter_motion_ambient(0.0, hero_dy, ratio=0.28)
    for i in range(26):
        seed = (i + 1) * 137.5
        px = (seed * 29.3 + math.sin(t * 0.8 + i) * 22.0) % W
        py = (seed * 67.1 - t * (20.0 + (i % 5) * 7.0) + amb_dy) % H
        r = 2 + (i % 4)
        col = (*C_CYAN, 110) if i % 2 == 0 else (*C_AMBER, 95)
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
        d.ellipse([px - r, py - r, px + r, py + r], fill=(37, 99, 235, 60))
    draw_bottom_rule_hud(d, t, dark_theme=False)
    return im


def draw_bottom_rule_hud(d: ImageDraw.ImageDraw, t: float, dark_theme: bool = True):
    prog = clamp(t / TOTAL_DURATION)
    bar_y = 1852
    bg_c = (20, 25, 38, 220) if dark_theme else (232, 226, 214, 235)
    fg_c = (195, 205, 222, 235) if dark_theme else (50, 56, 68, 235)
    d.rounded_rectangle([64, bar_y - 18, W - 64, bar_y + 28], radius=22, fill=bg_c)

    tx0, tx1 = 290, W - 230
    d.rounded_rectangle([tx0, bar_y, tx1, bar_y + 10], radius=5, fill=(65, 75, 96, 150))
    fill_w = max(12, int((tx1 - tx0) * prog))
    d.rounded_rectangle([tx0, bar_y, tx0 + fill_w, bar_y + 10], radius=5, fill=(*C_AMBER, 255))

    f_tc = get_font(MONO_MED, 19)
    d.text((88, bar_y - 8), f"DEVIS DESIGNER  {int(t // 60):02d}:{int(t % 60):02d}", font=f_tc, fill=fg_c)

    for bi in range(10):
        bx = W - 205 + bi * 12
        bh = int(6 + 12 * abs(math.sin(t * 7.5 + bi * 0.65)))
        d.rounded_rectangle([bx, bar_y + 5 - bh // 2, bx + 6, bar_y + 5 + bh // 2], radius=2, fill=(*C_CYAN, 240))


def draw_top_header(canvas: Image.Image, age: float, act_num: str, label: str, dark_theme: bool = True):
    a, dy = data_reveal(age, delay=0.02, dur=0.36, offset_y=20.0)
    if a <= 0.02:
        return
    d = ImageDraw.Draw(canvas)
    f_mono = get_font(MONO_MED, 22)
    txt = f"{act_num}   //   {label}"
    bb = d.textbbox((0, 0), txt, font=f_mono)
    tw = bb[2] - bb[0]
    pw = tw + 68
    px = (W - pw) // 2
    py = int(64 + dy)
    bg_c = (18, 23, 36, int(235 * a)) if dark_theme else (255, 255, 255, int(245 * a))
    bd_c = (*C_CYAN, int(225 * a)) if dark_theme else (*C_BLUE, int(220 * a))
    fg_c = (245, 248, 255, int(250 * a)) if dark_theme else (20, 24, 34, int(250 * a))
    d.rounded_rectangle([px, py, px + pw, py + 48], radius=24, fill=bg_c, outline=bd_c, width=2)
    d.ellipse([px + 20, py + 18, px + 32, py + 30], fill=(*C_AMBER, int(255 * a)))
    d.text((px + 44, py + 10), txt, font=f_mono, fill=fg_c)


# ---------------------------------------------------------------------------
# Strictly <= 2 Lines Kinetic Caption Stack (`draw_two_line_caption`)
# ---------------------------------------------------------------------------
def draw_two_line_caption(
    canvas: Image.Image,
    age: float,
    line1: str,
    line2_highlight: str,
    cy: int = 1495,
    dark_theme: bool = True,
    accent=C_AMBER,
):
    """
    Renders at most 2 lines of kinetic subtitles at a time:
      - Line 1: Bold context header (`PlusJakartaSans Bold 46px`)
      - Line 2: ExtraBold highlighted pill (`PlusJakartaSans ExtraBold 58px`) with wipe entrance
    """
    d = ImageDraw.Draw(canvas)
    f_l1 = get_font(JAKARTA_BOLD, 46)
    f_l2 = get_font(JAKARTA_EBOLD, 58)
    fg_main = (255, 255, 255) if dark_theme else C_INK

    a1, dy1 = data_reveal(age, delay=0.0, dur=0.26, offset_y=20.0)
    if line1 and a1 > 0.02:
        bb1 = d.textbbox((0, 0), line1, font=f_l1)
        w1 = bb1[2] - bb1[0]
        x1 = (W - w1) // 2
        y1 = int(cy - 76 + dy1)
        # Subtle shadow for legibility
        if dark_theme:
            d.text((x1 + 2, y1 + 3), line1, font=f_l1, fill=(0, 0, 0, int(180 * a1)))
        d.text((x1, y1), line1, font=f_l1, fill=(*fg_main, int(252 * a1)))

    a2, dy2 = data_reveal(age, delay=0.05, dur=0.28, offset_y=24.0)
    if line2_highlight and a2 > 0.02:
        bb2 = d.textbbox((0, 0), line2_highlight, font=f_l2)
        w2 = bb2[2] - bb2[0]
        h2 = bb2[3] - bb2[1]
        if w2 > W - 110:
            f_l2 = get_font(JAKARTA_EBOLD, 48)
            bb2 = d.textbbox((0, 0), line2_highlight, font=f_l2)
            w2 = bb2[2] - bb2[0]
            h2 = bb2[3] - bb2[1]
        x2 = (W - w2) // 2
        y2 = int(cy + dy2)
        wipe = emil_ease_in_out(clamp((age - 0.04) / 0.26))
        bw = int((w2 + 56) * wipe)
        if bw > 8:
            sh_a = int(115 * clamp((age - 0.08) / 0.24))
            if sh_a > 5:
                d.rounded_rectangle(
                    [x2 - 24, y2 - 4, x2 - 24 + bw, y2 + h2 + 26],
                    radius=20,
                    fill=(0, 0, 0, sh_a),
                )
            d.rounded_rectangle(
                [x2 - 28, y2 - 10, x2 - 28 + bw, y2 + h2 + 20],
                radius=20,
                fill=(*accent, int(250 * a2)),
            )
        txt_c = (14, 17, 24) if accent in (C_AMBER, C_CYAN, C_GREEN) else (255, 255, 255)
        d.text((x2, y2 - bb2[1] + 2), line2_highlight, font=f_l2, fill=(*txt_c, int(255 * a2)))


# ---------------------------------------------------------------------------
# ACT I (00.00s - 08.75s): Dark Obsidian Stage — Official 3D Glass Logo +
# Brand Hero Card & 3 Instant Trust Pillars (20 Exports Offerts / Zéro Installation)
# ---------------------------------------------------------------------------
def render_act1_hook(t: float) -> Image.Image:
    age = t
    canvas = get_dark_canvas(t, age)
    draw_top_header(canvas, age, "01 // APPLICATION WEB", "DEVIS & FACTURES EN LIGNE", dark_theme=True)

    if t < 4.40:
        # Phase 1A (0.00s - 4.40s): Official 3D Glass Logo + Floating Brand Hero Card
        cw, ch = 890, 960
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=42, fill=(16, 21, 34, 248), outline=(*C_CYAN, 230), width=3)

        # Glowing top halo + Official 3D Blue Glass Logo (`230x230`)
        cd.ellipse([cw // 2 - 140, 36, cw // 2 + 140, 316], fill=(37, 99, 235, 55), outline=(*C_CYAN, 160), width=2)
        logo_im = get_logo(220)
        card.alpha_composite(logo_im, ((cw - 220) // 2, 64))

        # Big Brand Headline inside card
        f_title = get_font(JAKARTA_EBOLD, 68)
        t_brand = "DEVIS DESIGNER"
        bb_t = cd.textbbox((0, 0), t_brand, font=f_title)
        cd.text(((cw - (bb_t[2] - bb_t[0])) // 2, 315), t_brand, font=f_title, fill=(255, 255, 255, 255))

        # Subtitle pill
        cd.rounded_rectangle([56, 412, cw - 56, 474], radius=31, fill=(28, 38, 62, 255), outline=(*C_AMBER, 240), width=2)
        f_sub = get_font(MONO_MED, 23)
        s_txt = "VOS DOCUMENTS AUSSI SOIGNÉS QUE VOTRE TRAVAIL"
        bb_s = cd.textbbox((0, 0), s_txt, font=f_sub)
        cd.text(((cw - (bb_s[2] - bb_s[0])) // 2, 428), s_txt, font=f_sub, fill=(*C_AMBER, 255))

        # Mini Stylized A4 Preview Sheet inside the Hero Card (`y=510..895`)
        cd.rounded_rectangle([76, 510, cw - 76, 895], radius=28, fill=(250, 248, 244, 255), outline=(*C_BLUE, 255), width=4)
        cd.rounded_rectangle([76, 510, cw - 76, 608], radius=28, fill=(*C_BLUE, 255))
        cd.text((116, 536), "DEVIS N° DEV-2026-014", font=get_font(JAKARTA_EBOLD, 34), fill=(255, 255, 255, 255))
        cd.rounded_rectangle([cw - 310, 532, cw - 110, 586], radius=16, fill=(*C_GREEN, 255))
        cd.text((cw - 284, 543), "VALIDÉ TTC", font=get_font(JAKARTA_EBOLD, 24), fill=(12, 16, 22, 255))

        # 3 clean mock rows inside the preview sheet
        rows_preview = [
            ("Identité visuelle & Logo", "120 000 F"),
            ("Charte graphique 12 pages", "180 000 F"),
            ("TOTAL TTC (TVA 18% incl.)", "495 600 F CFA"),
        ]
        for r_idx, (r_lbl, r_val) in enumerate(rows_preview):
            ry = 632 + r_idx * 78
            is_tot = r_idx == 2
            row_bg = (232, 240, 255, 255) if is_tot else (238, 235, 228, 255)
            cd.rounded_rectangle([110, ry, cw - 110, ry + 62], radius=14, fill=row_bg)
            cd.text((136, ry + 13), r_lbl, font=get_font(JAKARTA_BOLD if not is_tot else JAKARTA_EBOLD, 28), fill=(*C_INK, 255))
            f_v = get_font(JAKARTA_EBOLD, 30)
            bb_v = cd.textbbox((0, 0), r_val, font=f_v)
            cd.text((cw - 136 - (bb_v[2] - bb_v[0]), ry + 12), r_val, font=f_v, fill=(*C_BLUE, 255) if is_tot else (*C_INK, 255))

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            210,
            age,
            delay=0.02,
            dur=0.44,
            rx_deg=5.5 * math.sin(t * 1.2),
            ry_deg=-5.0 * math.cos(t * 0.95),
            arc_px=14.0,
        )

        draw_two_line_caption(
            canvas,
            age,
            "VOS DEVIS ET FACTURES",
            "AUSSI SOIGNÉS QUE VOTRE TRAVAIL",
            cy=1510,
            dark_theme=True,
            accent=C_AMBER,
        )
    else:
        # Phase 1B (4.40s - 8.75s): 3 Instant Value Pillars Bento Card
        p_age = t - 4.40
        cw, ch = 890, 960
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=42, fill=(16, 21, 34, 248), outline=(*C_AMBER, 235), width=3)

        # Header inside card with mini logo
        logo_sm = get_logo(84)
        card.alpha_composite(logo_sm, (56, 42))
        cd.text((162, 48), "ACCÈS IMMÉDIAT  •  100 % WEB", font=get_font(MONO_MED, 24), fill=(*C_CYAN, 255))
        cd.text((162, 84), "PRÊT EN 10 SECONDES", font=get_font(JAKARTA_EBOLD, 42), fill=(255, 255, 255, 255))

        pillars = [
            (0.04, "20 EXPORTS OFFERTS", "30 jours d'essai gratuit dès l'ouverture", C_GREEN),
            (0.22, "ZÉRO INSTALLATION", "Fonctionne sur PC, mobile & tablette", C_CYAN),
            (0.40, "SANS COMPTE NI CARTE", "Créez et téléchargez votre PDF direct", C_AMBER),
        ]
        for idx, (dly, title_p, sub_p, col) in enumerate(pillars):
            pa, pdy = data_reveal(p_age, delay=dly, dur=0.40, offset_y=28.0)
            if pa <= 0.02:
                continue
            by = int(176 + idx * 246 + pdy)
            cd.rounded_rectangle([48, by, cw - 48, by + 214], radius=30, fill=(24, 31, 48, int(250 * pa)), outline=(*col, int(245 * pa)), width=3)
            draw_check_icon(cd, 124, by + 107, 44, (*col, int(255 * pa)), fg_col=(14, 18, 26, int(255 * pa)), width=6)
            cd.text((196, by + 44), title_p, font=get_font(JAKARTA_EBOLD, 44), fill=(255, 255, 255, int(255 * pa)))
            cd.text((196, by + 118), sub_p, font=get_font(INTER_MED, 30), fill=(195, 205, 222, int(245 * pa)))

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            210,
            p_age,
            delay=0.02,
            dur=0.42,
            rx_deg=4.8 * math.cos(p_age * 1.2),
            ry_deg=5.2 * math.sin(p_age * 1.0),
            arc_px=-14.0,
        )

        draw_two_line_caption(
            canvas,
            p_age,
            "ZÉRO INSTALLATION REQUISE",
            "20 EXPORTS OFFERTS DÈS AUJOURD'HUI",
            cy=1510,
            dark_theme=True,
            accent=C_GREEN,
        )

    return canvas


# ---------------------------------------------------------------------------
# ACT II (08.75s - 17.80s): Editorial Ivory Stage — Real-Time Quote Editor
# (`DEV-2026-014`, Atelier Kpodé -> SARL Sunlè, TVA 18% & 495 600 F CFA Live Counter)
# ---------------------------------------------------------------------------
def render_act2_editor(t: float) -> Image.Image:
    age = t - 8.75
    canvas = get_ivory_canvas(t, age)
    draw_top_header(canvas, age, "02 // ÉDITION EN DIRECT", "CALCUL AUTOMATIQUE HT • TVA • TTC", dark_theme=False)

    cw, ch = 900, 1020
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=38, fill=(255, 255, 255, 255), outline=(210, 204, 192, 255), width=3)

    # Top Royal Blue Banner inside A4 Document Card
    cd.rounded_rectangle([0, 0, cw - 1, 185], radius=38, fill=(*C_BLUE, 255))
    cd.rectangle([0, 140, cw - 1, 185], fill=(*C_BLUE, 255))
    logo_doc = get_logo(104)
    card.alpha_composite(logo_doc, (44, 40))
    cd.text((170, 38), "DEVIS N° DEV-2026-014", font=get_font(JAKARTA_EBOLD, 42), fill=(255, 255, 255, 255))
    cd.text((170, 98), "Atelier Kpodé (Cotonou)   •   Client : SARL Sunlè", font=get_font(INTER_MED, 26), fill=(220, 234, 255, 255))

    # Multi-Currency Active Switcher Bar (`F CFA` | `EUR €` | `USD $`)
    currencies = [("F CFA", True), ("EUR €", False), ("USD $", False)]
    if age > 5.2:
        idx_active = int((age - 5.2) / 1.1) % 3
        currencies = [(lbl, i == idx_active) for i, (lbl, _) in enumerate(currencies)]
    for c_i, (c_lbl, is_act) in enumerate(currencies):
        cx0 = 48 + c_i * 276
        cy0 = 212
        bg_p = (*C_AMBER, 255) if is_act else (240, 237, 230, 255)
        fg_p = (14, 17, 24, 255) if is_act else (95, 102, 115, 255)
        cd.rounded_rectangle([cx0, cy0, cx0 + 252, cy0 + 64], radius=18, fill=bg_p)
        f_c = get_font(JAKARTA_EBOLD, 28)
        bb_c = cd.textbbox((0, 0), c_lbl, font=f_c)
        cd.text((cx0 + (252 - (bb_c[2] - bb_c[0])) // 2, cy0 + 14), c_lbl, font=f_c, fill=fg_p)

    # 4 Real Line Items from `DEV-2026-014` appearing sequentially
    items = [
        (0.15, "01. Création de logo (3 prop.)", "Qté 1", "120 000 F"),
        (0.55, "02. Charte graphique (PDF 12p)", "Qté 1", "180 000 F"),
        (0.95, "03. Impression 500 cartes", "Qté 500", "75 000 F"),
        (1.35, "04. Retouches & sources HD", "Qté 3", "45 000 F"),
    ]
    for idx, (dly, desc, qty, amt) in enumerate(items):
        ia, idy = data_reveal(age, delay=dly, dur=0.38, offset_y=24.0)
        if ia <= 0.02:
            continue
        ry = int(304 + idx * 106 + idy)
        cd.rounded_rectangle([46, ry, cw - 46, ry + 88], radius=18, fill=(247, 245, 240, int(255 * ia)), outline=(224, 219, 210, int(255 * ia)), width=2)
        cd.text((72, ry + 24), desc, font=get_font(JAKARTA_BOLD, 29), fill=(*C_INK, int(255 * ia)))
        cd.rounded_rectangle([545, ry + 20, 665, ry + 68], radius=12, fill=(228, 235, 250, int(255 * ia)))
        cd.text((563, ry + 28), qty, font=get_font(MONO_MED, 24), fill=(*C_BLUE, int(255 * ia)))
        f_amt = get_font(JAKARTA_EBOLD, 32)
        bb_a = cd.textbbox((0, 0), amt, font=f_amt)
        cd.text((cw - 74 - (bb_a[2] - bb_a[0]), ry + 22), amt, font=f_amt, fill=(*C_INK, int(255 * ia)))

    # Bottom Real-Time Totals Footer (`Sous-total HT 420 000 F` + `TVA 18% 75 600 F` -> `495 600 F CFA TTC`)
    prog_cnt = ease_motion(clamp((age - 0.6) / 2.2))
    ht_val = int(round(420000 * prog_cnt))
    tva_val = int(round(75600 * prog_cnt))
    ttc_val = int(round(495600 * prog_cnt))

    cd.rounded_rectangle([46, 742, cw - 46, 976], radius=28, fill=(16, 21, 34, 255), outline=(*C_BLUE, 255), width=3)
    cd.text((76, 768), f"HT : {ht_val:,} F".replace(",", " "), font=get_font(MONO_MED, 25), fill=(195, 205, 225, 255))
    cd.text((455, 768), f"TVA (18 %) : +{tva_val:,} F".replace(",", " "), font=get_font(MONO_MED, 25), fill=(*C_CYAN, 255))

    cd.rounded_rectangle([74, 830, cw - 74, 948], radius=22, fill=(*C_AMBER, 255))
    cd.text((106, 862), "TOTAL TTC", font=get_font(JAKARTA_EBOLD, 38), fill=(14, 17, 24, 255))
    ttc_str = f"{ttc_val:,} F CFA".replace(",", " ")
    f_ttc = get_font(JAKARTA_EBOLD, 52)
    bb_ttc = cd.textbbox((0, 0), ttc_str, font=f_ttc)
    cd.text((cw - 106 - (bb_ttc[2] - bb_ttc[0]), 852), ttc_str, font=f_ttc, fill=(14, 17, 24, 255))

    composite_hero_card_3layers(
        canvas,
        card,
        (W - cw) // 2,
        195,
        age,
        delay=0.02,
        dur=0.44,
        rx_deg=4.5 * math.sin(age * 1.15),
        ry_deg=-4.5 * math.cos(age * 0.95),
        arc_px=12.0,
    )

    if t < 13.10:
        draw_two_line_caption(
            canvas,
            age,
            "CRÉEZ VOTRE DEVIS PRO",
            "EN QUELQUES SECONDES",
            cy=1510,
            dark_theme=False,
            accent=C_BLUE,
        )
    else:
        draw_two_line_caption(
            canvas,
            t - 13.10,
            "TVA & TOTAL CALCULÉS EN DIRECT",
            "FRANC CFA  •  EURO  •  DOLLAR",
            cy=1510,
            dark_theme=False,
            accent=C_AMBER,
        )

    return canvas


# ---------------------------------------------------------------------------
# ACT III (17.80s - 28.30s): Dark Obsidian Stage —
# Phase 3A (17.80s - 23.80s): 12 Pro Templates Live Switcher (Modern, Studio, Purple, Corporate)
# Phase 3B (23.80s - 28.30s): 1-Click Devis -> Facture Conversion + 5 Tracking Statuses
# ---------------------------------------------------------------------------
def render_act3_templates(t: float) -> Image.Image:
    age = t - 17.80
    canvas = get_dark_canvas(t, age)
    draw_top_header(canvas, age, "03 // 12 MODÈLES PRO", "DESIGN & CONVERSION 1-CLIC", dark_theme=True)

    if t < 23.80:
        # Phase 3A: Fanned 12-Template Deck + Morphing Active Template Hero Card
        templates = [
            ("01 // MODERN", "Swiss Contemporain • Bandeau Bleu", C_BLUE, (240, 246, 255)),
            ("02 // STUDIO", "Style SaaS • Cartes Arrondies & Dégradé", C_INDIGO, (243, 240, 255)),
            ("09 // PURPLE", "Éditorial • Cercles & Total Dégradé", C_PURPLE, (248, 242, 255)),
            ("10 // CORPORATE", "Fond Sombre • Accents Orange Vif", C_ORANGE, (24, 28, 38)),
        ]
        tpl_idx = min(3, int(age / 1.48))
        tpl_age = age - tpl_idx * 1.48
        tpl_name, tpl_desc, tpl_col, tpl_paper = templates[tpl_idx]
        is_dark_tpl = tpl_idx == 3

        cw, ch = 890, 990
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=40, fill=(16, 21, 34, 248), outline=(*tpl_col, 240), width=4)

        # Top 4 template selector pills inside card
        short_names = ["MODERN", "STUDIO", "PURPLE", "CORPORATE"]
        for s_i, s_nm in enumerate(short_names):
            sx0 = 44 + s_i * 204
            active = s_i == tpl_idx
            bg_s = (*tpl_col, 255) if active else (28, 35, 52, 255)
            fg_s = (255, 255, 255, 255) if active else (165, 175, 195, 255)
            cd.rounded_rectangle([sx0, 38, sx0 + 190, 104], radius=18, fill=bg_s)
            f_s = get_font(JAKARTA_EBOLD, 24)
            bb_s = cd.textbbox((0, 0), s_nm, font=f_s)
            cd.text((sx0 + (190 - (bb_s[2] - bb_s[0])) // 2, 54), s_nm, font=f_s, fill=fg_s)

        # Active Template Header label
        cd.text((54, 132), tpl_name, font=get_font(JAKARTA_EBOLD, 46), fill=(255, 255, 255, 255))
        cd.text((54, 192), tpl_desc, font=get_font(INTER_MED, 28), fill=(*C_CYAN, 255))

        # Large A4 Template Preview Sheet (`y=252..938`)
        cd.rounded_rectangle([52, 252, cw - 52, 938], radius=30, fill=(*tpl_paper, 255), outline=(*tpl_col, 255), width=4)
        # Distinct header architecture per template!
        if tpl_idx == 0:
            cd.rounded_rectangle([52, 252, cw - 52, 382], radius=30, fill=(*tpl_col, 255))
            cd.text((92, 294), "DEVIS  •  MODÈLE MODERN", font=get_font(JAKARTA_EBOLD, 38), fill=(255, 255, 255, 255))
        elif tpl_idx == 1:
            cd.rounded_rectangle([84, 282, cw - 84, 404], radius=24, fill=(*tpl_col, 255))
            cd.text((120, 320), "STUDIO SAAS  •  DEV-2026-014", font=get_font(JAKARTA_EBOLD, 36), fill=(255, 255, 255, 255))
        elif tpl_idx == 2:
            cd.ellipse([cw - 260, 268, cw - 80, 448], fill=(*tpl_col, 55))
            cd.text((92, 296), "PURPLE ÉDITORIAL", font=get_font(JAKARTA_EBOLD, 42), fill=(*tpl_col, 255))
        else:
            cd.rounded_rectangle([52, 252, cw - 52, 390], radius=30, fill=(*C_ORANGE, 255))
            cd.text((92, 294), "CORPORATE  •  DARK EDITION", font=get_font(JAKARTA_EBOLD, 38), fill=(14, 17, 24, 255))

        fg_doc = (245, 247, 252, 255) if is_dark_tpl else (*C_INK, 255)
        row_fill = (36, 42, 58, 255) if is_dark_tpl else (255, 255, 255, 255)
        for r_i, (r_t, r_p) in enumerate([
            ("Direction artistique & Logo", "120 000 F"),
            ("Charte graphique complète", "180 000 F"),
            ("Supports imprimés & sources", "120 000 F"),
        ]):
            ry = 432 + r_i * 104
            cd.rounded_rectangle([88, ry, cw - 88, ry + 84], radius=16, fill=row_fill, outline=(*tpl_col, 90), width=2)
            cd.text((118, ry + 22), r_t, font=get_font(JAKARTA_BOLD, 29), fill=fg_doc)
            f_rp = get_font(JAKARTA_EBOLD, 30)
            bb_rp = cd.textbbox((0, 0), r_p, font=f_rp)
            cd.text((cw - 118 - (bb_rp[2] - bb_rp[0]), ry + 22), r_p, font=f_rp, fill=(*tpl_col, 255))

        cd.rounded_rectangle([88, 768, cw - 88, 896], radius=22, fill=(*tpl_col, 255))
        cd.text((124, 806), "TOTAL TTC : 495 600 F CFA", font=get_font(JAKARTA_EBOLD, 42), fill=(255, 255, 255, 255))

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            195,
            age,
            delay=0.02,
            dur=0.42,
            rx_deg=5.0 * math.sin(age * 1.3),
            ry_deg=-5.0 * math.cos(age * 1.1),
            arc_px=14.0,
        )

        draw_two_line_caption(
            canvas,
            tpl_age,
            "12 MODÈLES PROFESSIONNELS",
            "CHANGEZ DE DESIGN EN 1 CLIC",
            cy=1510,
            dark_theme=True,
            accent=C_CYAN,
        )
    else:
        # Phase 3B (23.80s - 28.30s): 1-Click Conversion DEVIS -> FACTURE & 5 Statuses
        p_age = t - 23.80
        cw, ch = 890, 980
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=40, fill=(16, 21, 34, 248), outline=(*C_GREEN, 235), width=3)

        cd.text((64, 48), "CONVERSION INSTANTANÉE  •  MÊME FICHE", font=get_font(MONO_MED, 24), fill=(*C_AMBER, 255))
        cd.text((64, 92), "DEVIS VERS FACTURE EN 1 CLIC", font=get_font(JAKARTA_EBOLD, 44), fill=(255, 255, 255, 255))

        # Animated Toggle Switch: [ DEVIS ] ===> [ FACTURE ]
        sw_p = emil_ease_in_out(clamp((p_age - 0.35) / 0.65))
        cd.rounded_rectangle([64, 185, cw - 64, 325], radius=36, fill=(26, 33, 50, 255), outline=(255, 255, 255, 60), width=2)
        knob_x = int(76 + sw_p * (cw - 152 - 370))
        knob_col = C_GREEN if sw_p > 0.5 else C_BLUE
        cd.rounded_rectangle([knob_x, 199, knob_x + 370, 311], radius=28, fill=(*knob_col, 255))
        cd.text((168, 226), "DEVIS", font=get_font(JAKARTA_EBOLD, 42), fill=(255, 255, 255, 255))
        cd.text((535, 226), "FACTURE", font=get_font(JAKARTA_EBOLD, 42), fill=(14, 18, 26, 255) if sw_p > 0.5 else (170, 180, 200, 255))

        # Document Number Morph (`DEV-2026-014` -> `FAC-2026-014`)
        doc_code = "FAC-2026-014  •  FACTURE FINALE" if sw_p > 0.5 else "DEV-2026-014  •  PROPOSITION"
        cd.rounded_rectangle([64, 360, cw - 64, 464], radius=22, fill=(24, 31, 48, 255), outline=(*knob_col, 220), width=2)
        cd.text((102, 390), doc_code, font=get_font(JAKARTA_EBOLD, 36), fill=(255, 255, 255, 255))

        # 5 Tracking Statuses (`Brouillon`, `Envoyé`, `Accepté`, `Refusé`, `Payé`)
        statuses = [
            ("01. BROUILLON", C_INDIGO),
            ("02. ENVOYÉ AU CLIENT", C_CYAN),
            ("03. DEVIS ACCEPTÉ", C_AMBER),
            ("04. FACTURE ÉMISE", C_BLUE),
            ("05. STATUT : PAYÉ TTC", C_GREEN),
        ]
        for s_i, (s_lbl, s_col) in enumerate(statuses):
            sa, sdy = data_reveal(p_age, delay=0.12 + s_i * 0.14, dur=0.36, offset_y=22.0)
            if sa <= 0.02:
                continue
            sy = int(498 + s_i * 88 + sdy)
            is_final = s_i == 4
            bg_st = (*C_GREEN, int(250 * sa)) if is_final else (26, 33, 50, int(245 * sa))
            fg_st = (12, 16, 22, int(255 * sa)) if is_final else (255, 255, 255, int(255 * sa))
            cd.rounded_rectangle([64, sy, cw - 64, sy + 74], radius=18, fill=bg_st, outline=(*s_col, int(235 * sa)), width=2)
            draw_check_icon(cd, 114, sy + 37, 22, (12, 16, 22, int(255 * sa)) if is_final else (*s_col, int(255 * sa)), fg_col=(*C_GREEN, 255) if is_final else (12, 16, 22, 255), width=4)
            cd.text((158, sy + 17), s_lbl, font=get_font(JAKARTA_EBOLD, 30), fill=fg_st)

        composite_hero_card_3layers(
            canvas,
            card,
            (W - cw) // 2,
            195,
            p_age,
            delay=0.02,
            dur=0.42,
            rx_deg=4.5 * math.cos(p_age * 1.2),
            ry_deg=4.5 * math.sin(p_age * 1.0),
            arc_px=-12.0,
        )

        draw_two_line_caption(
            canvas,
            p_age,
            "CONVERTISSEZ VOTRE DEVIS",
            "EN FACTURE INSTANTANÉMENT",
            cy=1510,
            dark_theme=True,
            accent=C_GREEN,
        )

    return canvas


# ---------------------------------------------------------------------------
# ACT IV (28.30s - 36.90s): Editorial Ivory Stage —
# Tactile Digital Signature Pad + Official Stamp Slam + PDF A4 Vector Export
# ---------------------------------------------------------------------------
def render_act4_signature(t: float) -> Image.Image:
    age = t - 28.30
    canvas = get_ivory_canvas(t, age)
    draw_top_header(canvas, age, "04 // SIGNATURE & PDF", "VALIDATION EN LIGNE DIRECTE", dark_theme=False)

    cw, ch = 900, 1010
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=38, fill=(255, 255, 255, 255), outline=(206, 200, 188, 255), width=3)

    # Top Acompte summary strip
    cd.rounded_rectangle([44, 42, cw - 44, 158], radius=24, fill=(16, 21, 34, 255))
    cd.text((80, 62), "BON POUR ACCORD  •  ACOMPTE 30 % À LA SIGNATURE", font=get_font(MONO_MED, 23), fill=(*C_AMBER, 255))
    cd.text((80, 98), "Montant acompte : 148 680 F CFA", font=get_font(JAKARTA_EBOLD, 34), fill=(255, 255, 255, 255))

    # Interactive Signature Pad Box (`y=190..660`)
    cd.rounded_rectangle([44, 190, cw - 44, 665], radius=28, fill=(248, 246, 240, 255), outline=(*C_BLUE, 220), width=3)
    cd.text((82, 218), "SIGNATURE DU CLIENT (AU DOIGT OU À LA SOURIS) :", font=get_font(MONO_MED, 23), fill=(95, 102, 118, 255))
    cd.line([(82, 575), (cw - 82, 575)], fill=(195, 190, 180, 255), width=2)
    cd.text((82, 592), "Signé électroniquement par M. Bidossessi  •  31/08/2026", font=get_font(INTER_MED, 25), fill=(90, 96, 110, 255))

    # Animated Bezier Calligraphic Ink Stroke (`age = 0.25s .. 2.8s`)
    sig_prog = ease_motion(clamp((age - 0.25) / 2.2))
    if sig_prog > 0.02:
        pts_sig = []
        n_pts = max(2, int(90 * sig_prog))
        for i in range(n_pts):
            u = i / 89.0
            sx = 115 + u * 540
            sy = (
                435
                - 95 * math.sin(u * math.pi * 2.5) * math.exp(-u * 0.9)
                + 42 * math.cos(u * math.pi * 6.5)
                - 35 * u
            )
            pts_sig.append((int(sx), int(sy)))
        cd.line(pts_sig, fill=(18, 42, 135, 255), width=8, joint="curve")
        # Glowing pen tip while drawing
        if sig_prog < 0.98:
            px_tip, py_tip = pts_sig[-1]
            cd.ellipse([px_tip - 12, py_tip - 12, px_tip + 12, py_tip + 12], fill=(*C_BLUE, 255))

    # Official Circular Company Stamp Slam at `age >= 2.6s` with `disney_overshoot_ease`!
    if age >= 2.50:
        st_p = disney_overshoot_ease(clamp((age - 2.50) / 0.45))
        st_Layer = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st_Layer)
        sd.ellipse([16, 16, 304, 304], outline=(220, 38, 38, 235), width=7)
        sd.ellipse([32, 32, 288, 288], outline=(220, 38, 38, 190), width=3)
        sd.rounded_rectangle([38, 118, 282, 202], radius=14, fill=(220, 38, 38, 235))
        sd.text((62, 68), "ATELIER KPODÉ", font=get_font(JAKARTA_EBOLD, 24), fill=(220, 38, 38, 240))
        sd.text((54, 140), "LU & APPROUVÉ", font=get_font(JAKARTA_EBOLD, 28), fill=(255, 255, 255, 255))
        sd.text((82, 222), "COTONOU • BÉNIN", font=get_font(MONO_MED, 20), fill=(220, 38, 38, 240))
        rot_st = st_Layer.rotate(14.0, resample=Image.BICUBIC, expand=False)
        sc_st = max(0.2, min(1.35, st_p))
        sw_st = max(20, int(320 * sc_st))
        rot_st = rot_st.resize((sw_st, sw_st), Image.LANCZOS)
        card.alpha_composite(rot_st, (cw - 360 - (sw_st - 320) // 2, 275 - (sw_st - 320) // 2))

    # Bottom 3 Export Badges (`PDF A4 HD`, `SVG VECTORIEL`, `PLEIN ÉCRAN`)
    exports = [
        ("EXPORT PDF A4", "Multi-pages HD", C_BLUE),
        ("SVG VECTORIEL", "Qualité infinie", C_INDIGO),
        ("PLEIN ÉCRAN", "Présentation client", C_GREEN),
    ]
    for e_i, (e_title, e_sub, e_col) in enumerate(exports):
        ea, edy = data_reveal(age, delay=0.50 + e_i * 0.18, dur=0.38, offset_y=24.0)
        if ea <= 0.02:
            continue
        ex0 = 44 + e_i * 276
        ey0 = int(702 + edy)
        cd.rounded_rectangle([ex0, ey0, ex0 + 258, ey0 + 260], radius=26, fill=(*e_col, int(250 * ea)))
        draw_check_icon(cd, ex0 + 129, ey0 + 74, 34, (255, 255, 255, int(250 * ea)), fg_col=(*e_col, 255), width=5)
        f_et = get_font(JAKARTA_EBOLD, 27)
        bb_et = cd.textbbox((0, 0), e_title, font=f_et)
        cd.text((ex0 + (258 - (bb_et[2] - bb_et[0])) // 2, ey0 + 136), e_title, font=f_et, fill=(255, 255, 255, int(255 * ea)))
        f_es = get_font(INTER_MED, 22)
        bb_es = cd.textbbox((0, 0), e_sub, font=f_es)
        cd.text((ex0 + (258 - (bb_es[2] - bb_es[0])) // 2, ey0 + 184), e_sub, font=f_es, fill=(235, 242, 255, int(245 * ea)))

    composite_hero_card_3layers(
        canvas,
        card,
        (W - cw) // 2,
        195,
        age,
        delay=0.02,
        dur=0.44,
        rx_deg=4.5 * math.sin(age * 1.1),
        ry_deg=-4.5 * math.cos(age * 0.9),
        arc_px=12.0,
    )

    if t < 32.50:
        draw_two_line_caption(
            canvas,
            age,
            "SIGNATURE DIRECTE AU DOIGT",
            "OU À LA SOURIS SUR L'APERÇU",
            cy=1510,
            dark_theme=False,
            accent=C_BLUE,
        )
    else:
        draw_two_line_caption(
            canvas,
            t - 32.50,
            "CACHET OFFICIEL INCLUS",
            "EXPORT PDF A4 HAUTE DÉFINITION",
            cy=1510,
            dark_theme=False,
            accent=C_GREEN,
        )

    return canvas


# ---------------------------------------------------------------------------
# ACT V (36.90s - 47.40s): Dark Obsidian Stage —
# Pricing (2 000 F / mois | 15 000 F / an) & Chariow Mobile Money Instant Activation
# ---------------------------------------------------------------------------
def render_act5_pricing(t: float) -> Image.Image:
    age = t - 36.90
    canvas = get_dark_canvas(t, age)
    draw_top_header(canvas, age, "05 // TARIFS & MOMO", "ILLIMITÉ • ACTIVATION AUTO", dark_theme=True)

    cw, ch = 900, 1010
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=40, fill=(16, 21, 34, 248), outline=(*C_AMBER, 235), width=3)

    # Top 2 Pricing Tier Cards (`2 000 F / MOIS` vs `15 000 F / AN`)
    # Left Card: 1 Month
    cd.rounded_rectangle([42, 46, 432, 485], radius=30, fill=(24, 31, 48, 255), outline=(*C_CYAN, 220), width=3)
    cd.text((74, 78), "PASS 1 MOIS", font=get_font(MONO_MED, 25), fill=(*C_CYAN, 255))
    cd.text((74, 134), "2 000 F", font=get_font(JAKARTA_EBOLD, 68), fill=(255, 255, 255, 255))
    cd.text((74, 224), "F CFA  /  30 JOURS", font=get_font(JAKARTA_BOLD, 26), fill=(185, 195, 215, 255))
    cd.rounded_rectangle([74, 292, 400, 358], radius=16, fill=(32, 42, 64, 255))
    cd.text((98, 308), "Exports PDF illimités", font=get_font(INTER_MED, 26), fill=(255, 255, 255, 255))
    cd.rounded_rectangle([74, 376, 400, 442], radius=16, fill=(32, 42, 64, 255))
    cd.text((98, 392), "Les 12 modèles inclus", font=get_font(INTER_MED, 26), fill=(255, 255, 255, 255))

    # Right Featured Card: 1 Year (`15 000 F CFA` - `LE PLUS AVANTAGEUX`)
    cd.rounded_rectangle([462, 46, cw - 42, 485], radius=30, fill=(32, 28, 20, 255), outline=(*C_AMBER, 255), width=4)
    cd.rounded_rectangle([490, 68, cw - 70, 122], radius=16, fill=(*C_AMBER, 255))
    cd.text((514, 80), "LE PLUS AVANTAGEUX", font=get_font(JAKARTA_EBOLD, 24), fill=(14, 17, 24, 255))
    cd.text((494, 142), "15 000 F", font=get_font(JAKARTA_EBOLD, 68), fill=(*C_AMBER, 255))
    cd.text((494, 232), "SOIT 1 250 F / MOIS", font=get_font(JAKARTA_EBOLD, 26), fill=(255, 255, 255, 255))
    cd.rounded_rectangle([494, 292, cw - 70, 358], radius=16, fill=(*C_GREEN, 255))
    cd.text((520, 308), "Économisez 9 000 F / an", font=get_font(JAKARTA_EBOLD, 25), fill=(12, 16, 22, 255))
    cd.rounded_rectangle([494, 376, cw - 70, 442], radius=16, fill=(44, 38, 28, 255))
    cd.text((520, 392), "365 jours 100 % illimités", font=get_font(INTER_MED, 25), fill=(255, 255, 255, 255))

    # Bottom Chariow Mobile Money Instant Payment Dock (`y=520..965`)
    cd.rounded_rectangle([42, 520, cw - 42, 968], radius=32, fill=(22, 28, 44, 255), outline=(255, 255, 255, 65), width=2)
    cd.text((78, 548), "PAIEMENT MOBILE INTÉGRÉ VIA CHARIOW", font=get_font(MONO_MED, 24), fill=(*C_CYAN, 255))
    cd.text((78, 588), "ACTIVATION INSTANTANÉE SANS CODE", font=get_font(JAKARTA_EBOLD, 36), fill=(255, 255, 255, 255))

    operators = [
        (0.35, "MTN MoMo", "Paiement Mobile", (255, 204, 0), (14, 17, 24)),
        (0.55, "Orange Money", "Validation directe", (255, 102, 0), (255, 255, 255)),
        (0.75, "Wave", "Transfert instantané", (29, 200, 255), (14, 17, 24)),
        (0.95, "Moov Money", "Activation auto", (0, 102, 204), (255, 255, 255)),
    ]
    for op_i, (dly, op_name, op_sub, op_bg, op_fg) in enumerate(operators):
        oa, ody = data_reveal(age, delay=dly, dur=0.38, offset_y=22.0)
        if oa <= 0.02:
            continue
        r, c = divmod(op_i, 2)
        ox = 72 + c * 388
        oy = int(662 + r * 140 + ody)
        cd.rounded_rectangle([ox, oy, ox + 368, oy + 120], radius=24, fill=(*op_bg, int(250 * oa)))
        draw_check_icon(cd, ox + 56, oy + 60, 28, (*op_fg, int(245 * oa)), fg_col=(*op_bg, 255), width=5)
        cd.text((ox + 104, oy + 22), op_name, font=get_font(JAKARTA_EBOLD, 32), fill=(*op_fg, int(255 * oa)))
        cd.text((ox + 104, oy + 68), op_sub, font=get_font(INTER_MED, 23), fill=(*op_fg, int(235 * oa)))

    composite_hero_card_3layers(
        canvas,
        card,
        (W - cw) // 2,
        195,
        age,
        delay=0.02,
        dur=0.44,
        rx_deg=4.5 * math.sin(age * 1.15),
        ry_deg=-4.5 * math.cos(age * 0.95),
        arc_px=12.0,
    )

    if t < 42.10:
        draw_two_line_caption(
            canvas,
            age,
            "ILLIMITÉ DÈS 2 000 F / MOIS",
            "OU 15 000 F CFA PAR AN (-9 000 F)",
            cy=1510,
            dark_theme=True,
            accent=C_AMBER,
        )
    else:
        draw_two_line_caption(
            canvas,
            t - 42.10,
            "PAIEMENT MOBILE INSTANTANÉ",
            "MTN MOMO • ORANGE • WAVE • MOOV",
            cy=1510,
            dark_theme=True,
            accent=C_CYAN,
        )

    return canvas


# ---------------------------------------------------------------------------
# ACT VI (47.40s - 56.45s): Dark Obsidian Finale Stage —
# WhatsApp Referral (`1 AMI = 1 MOIS OFFERT`) + Official Logo CTA Portal
# ---------------------------------------------------------------------------
def render_act6_outro(t: float) -> Image.Image:
    age = t - 47.40
    canvas = get_dark_canvas(t, age)
    draw_top_header(canvas, age, "06 // ESSAI GRATUIT", "20 EXPORTS OFFERTS DÈS MAINTENANT", dark_theme=True)

    # Upper Card: WhatsApp Referral Card (`1 AMI = 1 MOIS OFFERT`)
    rw, rh = 890, 330
    rcard = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rcard)
    rd.rounded_rectangle([0, 0, rw - 1, rh - 1], radius=36, fill=(16, 28, 28, 248), outline=(*C_GREEN, 245), width=3)
    rd.text((58, 38), "PARRAINAGE WHATSAPP  •  LIEN PERSONNEL DDREF", font=get_font(MONO_MED, 23), fill=(*C_GREEN, 255))
    rd.rounded_rectangle([54, 94, rw - 54, 214], radius=24, fill=(*C_GREEN, 255))
    f_ref = get_font(JAKARTA_EBOLD, 46)
    ref_txt = "1 AMI PARRAINÉ = 1 MOIS OFFERT"
    bb_r = rd.textbbox((0, 0), ref_txt, font=f_ref)
    rd.text(((rw - (bb_r[2] - bb_r[0])) // 2, 124), ref_txt, font=f_ref, fill=(12, 16, 22, 255))
    rd.text((135, 242), "Cumulez jusqu'à 12 mois gratuits chaque année", font=get_font(INTER_MED, 28), fill=(235, 245, 240, 255))

    composite_hero_card_3layers(
        canvas,
        rcard,
        (W - rw) // 2,
        185,
        age,
        delay=0.02,
        dur=0.40,
        rx_deg=3.8 * math.sin(age * 1.2),
        ry_deg=-3.8 * math.cos(age * 1.0),
        arc_px=10.0,
    )

    # Lower Card: Final Official Brand & CTA Portal (`y=550..1210`)
    pw, ph = 890, 650
    pcard = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pcard)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=40, fill=(16, 21, 34, 252), outline=(*C_AMBER, 255), width=4)

    # Official 3D Blue Glass Logo + Brand Title
    logo_cta = get_logo(156)
    pcard.alpha_composite(logo_cta, ((pw - 156) // 2, 36))

    f_b = get_font(JAKARTA_EBOLD, 58)
    b_txt = "DEVIS DESIGNER"
    bb_b = pd.textbbox((0, 0), b_txt, font=f_b)
    pd.text(((pw - (bb_b[2] - bb_b[0])) // 2, 206), b_txt, font=f_b, fill=(255, 255, 255, 255))

    sub_b = "20 EXPORTS OFFERTS  •  SANS COMPTE NI CARTE"
    f_sb = get_font(MONO_MED, 24)
    bb_sb = pd.textbbox((0, 0), sub_b, font=f_sb)
    pd.text(((pw - (bb_sb[2] - bb_sb[0])) // 2, 286), sub_b, font=f_sb, fill=(*C_CYAN, 255))

    # Glowing Amber-Gold Primary CTA Button
    pd.rounded_rectangle([54, 352, pw - 54, 488], radius=30, fill=(*C_AMBER, 255))
    f_btn = get_font(JAKARTA_EBOLD, 36)
    btn_txt = "ESSAYEZ MAINTENANT GRATUITEMENT"
    bb_btn = pd.textbbox((0, 0), btn_txt, font=f_btn)
    pd.text(((pw - (bb_btn[2] - bb_btn[0])) // 2, 398), btn_txt, font=f_btn, fill=(14, 17, 24, 255))

    # Crisp Web App URL Bar at bottom of portal
    pd.rounded_rectangle([74, 520, pw - 74, 608], radius=22, fill=(26, 34, 54, 255), outline=(*C_CYAN, 220), width=2)
    f_url = get_font(JAKARTA_EBOLD, 31)
    url_txt = "devis-designer-app.jerode.workers.dev"
    bb_u = pd.textbbox((0, 0), url_txt, font=f_url)
    pd.text(((pw - (bb_u[2] - bb_u[0])) // 2, 544), url_txt, font=f_url, fill=(255, 255, 255, 255))

    composite_hero_card_3layers(
        canvas,
        pcard,
        (W - pw) // 2,
        548,
        age,
        delay=0.18,
        dur=0.44,
        rx_deg=4.5 * math.cos(age * 1.15),
        ry_deg=4.5 * math.sin(age * 0.95),
        arc_px=-12.0,
    )

    if t < 51.40:
        draw_two_line_caption(
            canvas,
            age,
            "PARRAINEZ UN AMI SUR WHATSAPP",
            "GAGNEZ 1 MOIS GRATUIT",
            cy=1510,
            dark_theme=True,
            accent=C_GREEN,
        )
    else:
        draw_two_line_caption(
            canvas,
            t - 51.40,
            "ESSAYEZ DEVIS DESIGNER",
            "SANS COMPTE NI CARTE BANCAIRE",
            cy=1510,
            dark_theme=True,
            accent=C_AMBER,
        )

    return canvas


# ---------------------------------------------------------------------------
# Master Frame Dispatcher + Velocity-Matched Seam Transitions
# ---------------------------------------------------------------------------
def _render_scene(t: float) -> Image.Image:
    if t < 8.75:
        return render_act1_hook(t)
    if t < 17.80:
        return render_act2_editor(t)
    if t < 28.30:
        return render_act3_templates(t)
    if t < 36.90:
        return render_act4_signature(t)
    if t < 47.40:
        return render_act5_pricing(t)
    return render_act6_outro(t)


SEAMS = [
    (4.40, 0.22, "cut_the_curve"),
    (8.75, 0.24, "zoom_through"),
    (17.80, 0.24, "cut_the_curve"),
    (23.80, 0.22, "zoom_through"),
    (28.30, 0.24, "rack_focus"),
    (36.90, 0.24, "zoom_through"),
    (47.40, 0.25, "cut_the_curve"),
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
# Master Audio Mixer (French Voiceover `voice-02` + Cinema Pad + UI SFX)
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
            vo_l[start_s:end_s] += arr[:length, 0] * 1.15
            vo_r[start_s:end_s] += arr[:length, 1] * 1.15

    # Warm harmonic ambient synth bed + subtle 120 BPM pulse (-22 dB under voice)
    beat_env = 0.5 + 0.5 * np.sin(2 * np.pi * 2.0 * t) ** 4
    pad_l = (0.022 * np.sin(2 * np.pi * 65.41 * t) + 0.014 * np.sin(2 * np.pi * 130.81 * t + 0.3)) * (0.85 + 0.15 * beat_env)
    pad_r = (0.022 * np.sin(2 * np.pi * 65.41 * t) + 0.014 * np.sin(2 * np.pi * 196.00 * t - 0.3)) * (0.85 + 0.15 * beat_env)

    sfx_l = np.zeros_like(t)
    sfx_r = np.zeros_like(t)
    rng = np.random.default_rng(88)

    # Seam transition whooshes
    for t_seam, _, _ in SEAMS:
        i0 = int(t_seam * sr)
        dur_s = int(0.28 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.6
            noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32)
            sweep = np.sin(2 * np.pi * (110.0 + 280.0 * lt) * lt * 0.28)
            w_sig = (0.046 * sweep + 0.015 * noise) * env
            sfx_l[i0:i1] += w_sig
            sfx_r[i0:i1] += w_sig

    # Synchronized UI Micro-Pop, Stamp Slam & Chime Transients
    pop_times = [
        0.15, 4.45, 4.65, 4.85,
        8.90, 9.30, 9.70, 10.10, 13.15,
        17.95, 19.30, 20.75, 22.25, 24.20,
        28.55, 30.85, 32.55,
        37.10, 37.35, 37.55, 37.75, 42.15,
        47.55, 47.75, 51.45,
    ]
    for pt in pop_times:
        i0 = int(pt * sr)
        dur_p = int(0.09 * sr)
        i1 = min(total_samples, i0 + dur_p)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-26.0 * lt)
            freq = 660.0 if int(pt * 10) % 2 == 0 else 880.0
            chime = 0.034 * np.sin(2 * np.pi * freq * lt * 0.09) * env
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
    parser.add_argument("--preview", type=str, default="", help="Save a 12-frame preview contact sheet")
    args = parser.parse_args()

    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        sample_times = [
            1.8, 6.2, 10.8, 15.2,
            18.8, 22.8, 26.2, 29.8,
            34.0, 39.5, 44.5, 53.0,
        ]
        cols, rows = 4, 3
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
        "19",
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
