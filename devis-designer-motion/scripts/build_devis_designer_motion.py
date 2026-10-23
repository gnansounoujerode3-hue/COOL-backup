#!/usr/bin/env python3
"""
Master 9:16 Motion-Design Video Compositor (`devis-designer-motion` v3)
Directly inspired by and built from `imports/devis-designer-pub-16x9.mp4` (46.40s, 30fps, 1392 frames)
for `https://devis-designer-app.jerode.workers.dev/` (Devis Designer).

Visual & Narrative Architecture (8 Scenes, 46.40s @ 30fps):
  - Deep Midnight Grid Stage (`#050916`) + 3 Luminous Floating 3D Spheres
    (Royal Blue `#1E64F0`, Teal-Emerald `#0D9488`, Violet-Purple `#7C3AED`)
  - Scene 1 (00.00s - 05.00s): "LE MÊME TRAVAIL. LE MÊME PRIX. / Votre devis parle avant vous."
                               + Animated 3D A4 Comparison (`SANS RÉPONSE` vs `SIGNÉ LE JOUR MÊME`)
  - Scene 2 (05.00s - 09.00s): Brand Reveal (`Devis Designer` + 3D Glass Icon + 4 Glass Feature Pills)
  - Scene 3 (09.00s - 16.00s): "Vous tapez. Le devis se met en page." + Real 3D Smartphone Live Typing
                               + Floating Dark Glass Counter Card (`495 600 F` -> `595 900 F`)
  - Scene 4 (16.00s - 24.40s): "12 modèles. Un seul contenu." (3D Depth-of-Field Template Carousel)
                               + Full-Screen 3D Tilted 12-Template Masonry Wall (`12 mises en page incluses`)
  - Scene 5 (24.40s - 29.20s): "Votre couleur. Votre police. Votre devise." + 3x3 Color Swatch Grid
                               + Live Color-Morphing 3D A4 Devis + Glass Currency Card (`CFA / € / $`)
  - Scene 6 (29.20s - 35.40s): "Faites signer. Exportez. Envoyez." + Dual 3D Smartphones
                               (Live Signature Pad + Export Modal) + Glass PDF Card & 3 Export Pills
  - Scene 7 (35.40s - 40.20s): "Accepté ? Un clic : c'est une facture." + 4 Status Pills
                               + Glass `FAC-2026-008` Card + 3D Smartphone Facture Switch
  - Scene 8 (40.20s - 46.40s): "Ouvrez. Remplissez. Envoyez." + White URL Pill
                               (`devis-designer-app.jerode.workers.dev`) + Royal Blue CTA Button
"""

import argparse
import math
import os
import subprocess
import wave
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30.0
TOTAL_FRAMES = 1392
TOTAL_DURATION = TOTAL_FRAMES / FPS  # 46.40s

PROJECT_DIR = "/home/user/COOL-backup/devis-designer-motion"
ASSETS_DIR = f"{PROJECT_DIR}/assets"
AUDIO_DIR = f"{ASSETS_DIR}/audio"
FILM_DIR = f"{PROJECT_DIR}/film"
LOGO_PATH = f"{ASSETS_DIR}/logo.png"
REF_VIDEO = "/home/user/COOL-backup/imports/devis-designer-pub-16x9.mp4"
MIXED_WAV = f"{AUDIO_DIR}/master_v3_mix.wav"
OUT_MP4 = f"{FILM_DIR}/devis-designer-motion-design-9x16.mp4"

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/500Medium/Inter_500Medium.ttf"
INTER_SEMI = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_MED = f"{FONT_BASE}/plus-jakarta-sans/500Medium/PlusJakartaSans_500Medium.ttf"
JAKARTA_SEMI = f"{FONT_BASE}/plus-jakarta-sans/600SemiBold/PlusJakartaSans_600SemiBold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"

_FONT_CACHE = {}
_ASSET_CACHE = {}


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
    key = ("logo", size)
    if key not in _ASSET_CACHE:
        im = Image.open(LOGO_PATH).convert("RGBA")
        _ASSET_CACHE[key] = im.resize((size, size), Image.LANCZOS)
    return _ASSET_CACHE[key]


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def reveal(age: float, delay: float = 0.0, dur: float = 0.45, dy_px: float = 26.0):
    p = clamp((age - delay) / max(1e-4, dur))
    e = ease_out_cubic(p)
    return e, dy_px * (1.0 - e)


# ---------------------------------------------------------------------------
# Cached 3D Luminous Sphere Stage (Matching `devis-designer-pub-16x9.mp4`)
# ---------------------------------------------------------------------------
def _init_stage_layers():
    if "grid_bg" in _ASSET_CACHE:
        return
    # 1. Deep Midnight Grid Base (`#050916` + 60px subtle grid)
    bg = Image.new("RGBA", (W, H), (5, 9, 22, 255))
    d = ImageDraw.Draw(bg)
    for gx in range(0, W, 64):
        d.line([(gx, 0), (gx, H)], fill=(11, 18, 38, 255), width=1)
    for gy in range(0, H, 64):
        d.line([(0, gy), (W, gy)], fill=(11, 18, 38, 255), width=1)
    _ASSET_CACHE["grid_bg"] = bg

    # 2. Big Crisp 3D Royal Blue Sphere (`860x860`) with internal radial lighting
    sw = 860
    yy, xx = np.mgrid[0:sw, 0:sw].astype(np.float32)
    cx, cy, r = sw * 0.5, sw * 0.5, 395.0
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    # Off-center 3D specular highlight inside the sphere
    hdist = np.sqrt((xx - (cx - 45.0)) ** 2 + (yy - (cy + 35.0)) ** 2) / r
    h_norm = np.clip(1.0 - hdist, 0.0, 1.0)
    rim = np.clip(1.0 - (dist / r) ** 2.2, 0.0, 1.0)
    b_ch = np.clip(65.0 + 185.0 * (h_norm ** 1.25) * rim + 40.0 * rim, 0, 255)
    g_ch = np.clip(18.0 + 95.0 * (h_norm ** 1.55) * rim, 0, 255)
    r_ch = np.clip(4.0 + 24.0 * (h_norm ** 2.0) * rim, 0, 255)
    alpha = np.clip((r + 1.5 - dist) * 120.0, 0.0, 242.0)
    blue_orb = np.dstack([r_ch, g_ch, b_ch, alpha]).astype(np.uint8)
    _ASSET_CACHE["blue_orb"] = Image.fromarray(blue_orb)

    # 3. Soft Teal-Emerald Glow Sphere (`680x680`)
    tw = 680
    yy, xx = np.mgrid[0:tw, 0:tw].astype(np.float32)
    d_t = np.sqrt((xx - tw * 0.5) ** 2 + (yy - tw * 0.5) ** 2) / (tw * 0.46)
    g_t = np.clip(1.0 - d_t, 0.0, 1.0) ** 2.1
    teal_rgba = np.zeros((tw, tw, 4), dtype=np.uint8)
    teal_rgba[..., 0] = 16
    teal_rgba[..., 1] = 195
    teal_rgba[..., 2] = 165
    teal_rgba[..., 3] = (g_t * 155.0).astype(np.uint8)
    _ASSET_CACHE["teal_orb"] = Image.fromarray(teal_rgba)

    # 4. Vibrant Violet-Purple 3D Glow Sphere (`760x760`)
    pw = 760
    yy, xx = np.mgrid[0:pw, 0:pw].astype(np.float32)
    d_p = np.sqrt((xx - pw * 0.5) ** 2 + (yy - pw * 0.5) ** 2) / (pw * 0.46)
    g_p = np.clip(1.0 - d_p, 0.0, 1.0) ** 2.0
    purp_rgba = np.zeros((pw, pw, 4), dtype=np.uint8)
    purp_rgba[..., 0] = 138
    purp_rgba[..., 1] = 58
    purp_rgba[..., 2] = 242
    purp_rgba[..., 3] = (g_p * 175.0).astype(np.uint8)
    _ASSET_CACHE["purp_orb"] = Image.fromarray(purp_rgba)


def get_sphere_stage(t: float, show_watermark: bool = True, sphere_layout: str = "default") -> Image.Image:
    _init_stage_layers()
    canvas = _ASSET_CACHE["grid_bg"].copy()

    dx = int(22.0 * math.sin(t * 0.55))
    dy = int(18.0 * math.cos(t * 0.45))

    if sphere_layout == "center":
        bx, by = (W - 860) // 2 + dx, 420 + dy
        tx, ty = (W - 680) // 2 + 40 - dx, 760 - dy
        px, py = W - 520 + dy, 1020 + dx
    elif sphere_layout == "upper_left":
        bx, by = -180 + dx, 120 + dy
        tx, ty = 60 - dx, 480 - dy
        px, py = 360 + dy, 1080 + dx
    else:
        bx, by = -110 + dx, 360 + dy
        tx, ty = 80 - dx, 720 - dy
        px, py = 380 + dy, 1060 + dx

    canvas.alpha_composite(_ASSET_CACHE["blue_orb"], (bx, by))
    canvas.alpha_composite(_ASSET_CACHE["teal_orb"], (tx, ty))
    canvas.alpha_composite(_ASSET_CACHE["purp_orb"], (px, py))

    d = ImageDraw.Draw(canvas)
    if show_watermark:
        logo_w = get_logo(46)
        canvas.alpha_composite(logo_w, (52, 58))
        d.text((112, 64), "Devis Designer", font=get_font(JAKARTA_SEMI, 27), fill=(210, 220, 240, 195))

    # Bottom Royal-Blue Progress Bar (`y = 1912..1920`)
    prog = clamp(t / TOTAL_DURATION)
    bar_w = max(8, int(W * prog))
    d.rectangle([0, H - 8, bar_w, H], fill=(37, 99, 235, 255))
    return canvas


# ---------------------------------------------------------------------------
# Clean Extraction of 3D Animated Objects from `devis-designer-pub-16x9.mp4`
# ---------------------------------------------------------------------------
def _hull_from_binary(m: np.ndarray, min_area: int = 3500) -> np.ndarray:
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k_open)
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 65))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_close)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(m)
    out = np.zeros_like(m)
    for lbl in range(1, num_labels):
        if stats[lbl, cv2.CC_STAT_AREA] >= min_area:
            comp = (labels == lbl).astype(np.uint8) * 255
            cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts:
                hull = cv2.convexHull(c)
                cv2.drawContours(out, [hull], -1, 255, -1)
    return out


def extract_single_3d_object(
    rgb_1080p: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    dilate_px: int = 12,
    include_header: bool = False,
) -> Image.Image:
    roi = rgb_1080p[y0:y1, x0:x1]
    white = (roi.min(axis=2) > 122).astype(np.uint8) * 255
    if include_header:
        ys, xs = np.where(white > 0)
        if len(xs) > 80:
            xmin, xmax = np.percentile(xs, 1), np.percentile(xs, 99)
            hdr = (
                (roi.max(axis=2) > 160)
                & (np.arange(roi.shape[1])[None, :] >= xmin - 14)
                & (np.arange(roi.shape[1])[None, :] <= xmax + 14)
            ).astype(np.uint8) * 255
            white = cv2.bitwise_or(white, hdr)
    mask = _hull_from_binary(white)
    if dilate_px > 0:
        k_dil = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1))
        mask = cv2.dilate(mask, k_dil)
    mask = cv2.GaussianBlur(mask, (7, 7), 1.6)
    return Image.fromarray(np.dstack([roi, mask]))


def extract_dual_3d_objects(
    rgb_1080p: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    split_top_x: float,
    split_bot_x: float,
    dilate_left: int = 6,
    dilate_right: int = 8,
    right_header: bool = False,
) -> Image.Image:
    roi = rgb_1080p[y0:y1, x0:x1]
    rh, rw = roi.shape[:2]
    white = (roi.min(axis=2) > 122).astype(np.uint8) * 255
    yy, xx = np.mgrid[0:rh, 0:rw]
    split_line = split_top_x + (yy / float(max(1, rh))) * (split_bot_x - split_top_x)

    m_left = np.where(xx < split_line, white, 0).astype(np.uint8)
    m_right = np.where(xx >= split_line - 6, white, 0).astype(np.uint8)

    if right_header:
        ys, xs = np.where(m_right > 0)
        if len(xs) > 80:
            xmin, xmax = np.percentile(xs, 1), np.percentile(xs, 99)
            hdr = (
                (roi.max(axis=2) > 160)
                & (xx >= np.maximum(split_line - 4, xmin - 14))
                & (xx <= xmax + 14)
            ).astype(np.uint8) * 255
            m_right = cv2.bitwise_or(m_right, hdr)

    h_left = _hull_from_binary(m_left, min_area=2500)
    h_right = _hull_from_binary(m_right, min_area=2500)

    if dilate_left > 0 and h_left.max() > 0:
        kl = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_left * 2 + 1, dilate_left * 2 + 1))
        h_left = cv2.dilate(h_left, kl)
    if dilate_right > 0 and h_right.max() > 0:
        kr = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_right * 2 + 1, dilate_right * 2 + 1))
        h_right = cv2.dilate(h_right, kr)

    mask = cv2.bitwise_or(h_left, h_right)
    mask = cv2.GaussianBlur(mask, (7, 7), 1.6)
    return Image.fromarray(np.dstack([roi, mask]))


def composite_with_drop_shadow(canvas: Image.Image, obj_rgba: Image.Image, x: int, y: int, shadow_alpha: int = 120):
    if obj_rgba.size[0] <= 0 or obj_rgba.size[1] <= 0:
        return
    alpha = np.array(obj_rgba.split()[3], dtype=np.float32)
    if alpha.max() < 5:
        return
    # Fast downscaled OpenCV shadow blur
    ow, oh = obj_rgba.size
    small_a = cv2.resize(alpha, (max(16, ow // 4), max(16, oh // 4)), interpolation=cv2.INTER_AREA)
    small_a = cv2.GaussianBlur(small_a, (21, 21), 6.0)
    sh_a = cv2.resize(small_a, (ow, oh), interpolation=cv2.INTER_LINEAR)
    sh_a = np.clip(sh_a * (shadow_alpha / 255.0), 0, 255).astype(np.uint8)
    sh_rgba = np.zeros((oh, ow, 4), dtype=np.uint8)
    sh_rgba[..., 3] = sh_a
    canvas.alpha_composite(Image.fromarray(sh_rgba), (x + 10, y + 18))
    canvas.alpha_composite(obj_rgba, (x, y))


# ---------------------------------------------------------------------------
# UI Pill & Glass Card Helpers (Exact `devis-designer-pub-16x9.mp4` Style)
# ---------------------------------------------------------------------------
def draw_glass_pill(
    canvas: Image.Image,
    x: int,
    y: int,
    text: str,
    dot_color=(59, 130, 246),
    alpha: float = 1.0,
    active: bool = False,
    font_size: int = 27,
) -> int:
    if alpha <= 0.02:
        return 0
    f = get_font(JAKARTA_MED if not active else JAKARTA_SEMI, font_size)
    tmp_d = ImageDraw.Draw(canvas)
    bb = tmp_d.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    pw = tw + 74
    ph = int(font_size * 2.25)

    layer = Image.new("RGBA", (pw + 8, ph + 8), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    bg_c = (30, 58, 138, int(135 * alpha)) if active else (255, 255, 255, int(18 * alpha))
    bd_c = (*dot_color, int(210 * alpha)) if active else (255, 255, 255, int(42 * alpha))
    ld.rounded_rectangle([2, 2, pw + 2, ph + 2], radius=ph // 2, fill=bg_c, outline=bd_c, width=2)
    cy_dot = 2 + ph // 2
    ld.ellipse([24, cy_dot - 6, 36, cy_dot + 6], fill=(*dot_color, int(255 * alpha)))
    ld.text((50, (ph - (bb[3] - bb[1])) // 2 - bb[1] + 2), text, font=f, fill=(242, 246, 255, int(250 * alpha)))
    canvas.alpha_composite(layer, (x, y))
    return pw


def draw_eyebrow_and_headline(
    canvas: Image.Image,
    age: float,
    eyebrow: str,
    lines: list,
    subtitle_lines: list = None,
    x: int = 64,
    y: int = 168,
    title_size: int = 70,
    eyebrow_delay: float = 0.05,
    title_delay: float = 0.18,
    sub_delay: float = 0.36,
):
    d = ImageDraw.Draw(canvas)
    # Eyebrow (`#60A5FA` spaced uppercase)
    ea, edy = reveal(age, delay=eyebrow_delay, dur=0.42, dy_px=18.0)
    if eyebrow and ea > 0.02:
        f_eye = get_font(JAKARTA_SEMI, 23)
        spaced = " ".join(list(eyebrow)) if "  " not in eyebrow else eyebrow
        d.text((x, int(y + edy)), spaced, font=f_eye, fill=(96, 165, 250, int(245 * ea)))

    # Main Headline (`PlusJakartaSans ExtraBold`, pure white)
    f_title = get_font(JAKARTA_EBOLD, title_size)
    cur_y = y + 52
    for idx, ln in enumerate(lines):
        ta, tdy = reveal(age, delay=title_delay + idx * 0.08, dur=0.45, dy_px=24.0)
        if ta > 0.02:
            d.text((x, int(cur_y + tdy)), ln, font=f_title, fill=(255, 255, 255, int(255 * ta)))
        cur_y += int(title_size * 1.16)

    # Optional Subtitle (`#94A3B8`)
    if subtitle_lines:
        cur_y += 18
        f_sub = get_font(INTER_REG, 32)
        for idx, sln in enumerate(subtitle_lines):
            sa, sdy = reveal(age, delay=sub_delay + idx * 0.06, dur=0.45, dy_px=20.0)
            if sa > 0.02:
                d.text((x, int(cur_y + sdy)), sln, font=f_sub, fill=(148, 163, 184, int(245 * sa)))
            cur_y += 44


# ---------------------------------------------------------------------------
# SCENE 1 (0.00s - 5.00s): "Votre devis parle avant vous."
# ---------------------------------------------------------------------------
def render_scene1(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t
    canvas = get_sphere_stage(t, show_watermark=False, sphere_layout="default")

    draw_eyebrow_and_headline(
        canvas,
        age,
        eyebrow="LE MÊME TRAVAIL. LE MÊME PRIX.",
        lines=["Votre devis parle", "avant vous."],
        subtitle_lines=[
            "Ce n'est pas le prix qui change. C'est ce que",
            "votre client voit en premier.",
        ],
        x=68,
        y=190,
        title_size=76,
        eyebrow_delay=0.85,
        title_delay=2.65,
        sub_delay=3.20,
    )

    # Extract the animated 3D comparison documents from `rgb_1080p` (`x=845..1850, y=60..810`)
    docs_rgba = extract_dual_3d_objects(
        rgb_1080p,
        845,
        60,
        1850,
        810,
        split_top_x=455.0,
        split_bot_x=435.0,
        dilate_left=3,
        dilate_right=4,
        right_header=True,
    )
    docs_scaled = docs_rgba.resize((980, 732), Image.LANCZOS)
    composite_with_drop_shadow(canvas, docs_scaled, 50, 775, shadow_alpha=135)
    return canvas


# ---------------------------------------------------------------------------
# SCENE 2 (5.00s - 9.00s): Brand Reveal ("Devis Designer")
# ---------------------------------------------------------------------------
def render_scene2(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 5.00
    canvas = get_sphere_stage(t, show_watermark=False, sphere_layout="center")
    d = ImageDraw.Draw(canvas)

    # Expanding concentric halo rings around the 3D Glass Icon
    la, ldy = reveal(age, delay=0.05, dur=0.48, dy_px=24.0)
    icx, icy = W // 2, int(565 + ldy)
    for ring_i in range(3):
        rp = ((age * 0.75 + ring_i * 0.33) % 1.0)
        rr = int(95 + rp * 115)
        ra = int((1.0 - rp) * 75 * la)
        if ra > 4:
            d.ellipse([icx - rr, icy - rr, icx + rr, icy + rr], outline=(96, 165, 250, ra), width=2)

    logo_im = get_logo(176)
    canvas.alpha_composite(logo_im, (icx - 88, icy - 88))

    # Centered "Devis Designer" Headline
    ta, tdy = reveal(age, delay=0.22, dur=0.48, dy_px=26.0)
    if ta > 0.02:
        f_brand = get_font(JAKARTA_EBOLD, 84)
        txt_b = "Devis Designer"
        bb_b = d.textbbox((0, 0), txt_b, font=f_brand)
        d.text(((W - (bb_b[2] - bb_b[0])) // 2, int(715 + tdy)), txt_b, font=f_brand, fill=(255, 255, 255, int(255 * ta)))

    # Centered Subtitle
    sa, sdy = reveal(age, delay=0.55, dur=0.48, dy_px=22.0)
    if sa > 0.02:
        f_sub = get_font(INTER_REG, 33)
        for s_i, s_ln in enumerate([
            "Vos devis et vos factures, aussi soignés",
            "que votre travail.",
        ]):
            bb_s = d.textbbox((0, 0), s_ln, font=f_sub)
            d.text(((W - (bb_s[2] - bb_s[0])) // 2, int(848 + s_i * 46 + sdy)), s_ln, font=f_sub, fill=(165, 180, 204, int(245 * sa)))

    # 4 Glass Feature Pills in a balanced 2x2 grid
    pills = [
        ("12 modèles inclus", (59, 130, 246), 1.05),
        ("PDF A4 · SVG", (56, 189, 248), 1.18),
        ("Signature en ligne", (20, 184, 166), 1.31),
        ("Sans inscription", (139, 92, 246), 1.44),
    ]
    positions = [(115, 1020), (545, 1020), (115, 1110), (545, 1110)]
    for (p_txt, p_col, p_dly), (px, py) in zip(pills, positions):
        pa, pdy = reveal(age, delay=p_dly, dur=0.42, dy_px=18.0)
        draw_glass_pill(canvas, px, int(py + pdy), p_txt, dot_color=p_col, alpha=pa, font_size=28)

    return canvas


# ---------------------------------------------------------------------------
# SCENE 3 (9.00s - 16.00s): "Vous tapez. Le devis se met en page."
# ---------------------------------------------------------------------------
def render_scene3(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 9.00
    canvas = get_sphere_stage(t, show_watermark=True, sphere_layout="upper_left")

    step_lbl = "ÉTAPE 1 · VOTRE ENTREPRISE" if t < 12.15 else "ÉTAPE 2 · VOS PRESTATIONS"
    draw_eyebrow_and_headline(
        canvas,
        age,
        eyebrow=step_lbl,
        lines=["Vous tapez.", "Le devis se met en page."],
        x=64,
        y=158,
        title_size=68,
        eyebrow_delay=0.10,
        title_delay=0.22,
    )

    # Extract the animated 3D Smartphone from `rgb_1080p` (`x=205..830, y=96..1072`)
    phone_rgba = extract_single_3d_object(rgb_1080p, 205, 96, 830, 1072, dilate_px=14, include_header=False)
    phone_scaled = phone_rgba.resize((675, 1054), Image.LANCZOS)
    composite_with_drop_shadow(canvas, phone_scaled, 28, 490, shadow_alpha=145)

    # Floating Dark Glass Counter Card on Right (`TOTAL TTC : 495 600 F -> 595 900 F`)
    ca, cdy = reveal(age, delay=1.45, dur=0.48, dy_px=28.0)
    if ca > 0.02:
        cw, ch = 545, 365
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=30, fill=(10, 15, 28, int(238 * ca)), outline=(255, 255, 255, int(38 * ca)), width=2)
        cd.text((42, 36), "T O T A L   T T C", font=get_font(JAKARTA_SEMI, 22), fill=(148, 163, 184, int(245 * ca)))

        # Synchronized live counter (`495 600 F` -> `595 900 F` during `t = 12.60s..14.15s`)
        if t < 12.60:
            val_num = 495600
            val_col = (255, 255, 255, int(255 * ca))
        elif t < 14.15:
            p_cnt = ease_in_out_cubic((t - 12.60) / 1.55)
            val_num = int(round(495600 + (595900 - 495600) * p_cnt))
            val_col = (59, 130, 246, int(255 * ca))
        else:
            val_num = 595900
            val_col = (255, 255, 255, int(255 * ca))

        val_str = f"{val_num:,} F".replace(",", " ")
        cd.text((42, 82), val_str, font=get_font(JAKARTA_EBOLD, 72), fill=val_col)
        cd.text((42, 186), "TVA 18% incluse", font=get_font(INTER_REG, 28), fill=(148, 163, 184, int(240 * ca)))
        cd.line([(42, 252), (cw - 42, 252)], fill=(255, 255, 255, int(28 * ca)), width=1)
        cd.text((42, 280), "Calculé pendant que vous tapez.", font=get_font(INTER_MED, 27), fill=(226, 232, 240, int(248 * ca)))

        composite_with_drop_shadow(canvas, card, 488, int(1085 + cdy), shadow_alpha=int(135 * ca))

    return canvas


# ---------------------------------------------------------------------------
# SCENE 4 (16.00s - 24.40s): "12 modèles. Un seul contenu." + 12-Template Wall
# ---------------------------------------------------------------------------
def render_scene4(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 16.00
    if t < 22.40:
        # Part 4A (16.00s - 22.40s): 3D Depth-of-Field Template Carousel
        canvas = get_sphere_stage(t, show_watermark=True, sphere_layout="upper_left")
        d = ImageDraw.Draw(canvas)

        ea, edy = reveal(age, delay=0.05, dur=0.42, dy_px=18.0)
        f_eye = get_font(JAKARTA_SEMI, 23)
        eye_txt = "L E S   1 2   M O D È L E S   S O N T   I N C L U S"
        bb_e = d.textbbox((0, 0), eye_txt, font=f_eye)
        d.text(((W - (bb_e[2] - bb_e[0])) // 2, int(175 + edy)), eye_txt, font=f_eye, fill=(96, 165, 250, int(245 * ea)))

        ta, tdy = reveal(age, delay=0.16, dur=0.45, dy_px=22.0)
        f_title = get_font(JAKARTA_EBOLD, 64)
        t_txt = "12 modèles. Un seul contenu."
        bb_t = d.textbbox((0, 0), t_txt, font=f_title)
        d.text(((W - (bb_t[2] - bb_t[0])) // 2, int(230 + tdy)), t_txt, font=f_title, fill=(255, 255, 255, int(255 * ta)))

        # Extract the center A4 template + 2 blurred side templates cleanly (`y=198..905`)
        roi = rgb_1080p[198:905, 160:1760]
        rh, rw = roi.shape[:2]
        # Center crisp A4 sheet mask (`x in [500..1100]` of roi)
        center_roi = roi[:, 500:1100]
        c_white = (center_roi.min(axis=2) > 125).astype(np.uint8) * 255
        k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        c_white = cv2.morphologyEx(c_white, cv2.MORPH_OPEN, k_open)
        ys_c, xs_c = np.where(c_white > 0)
        c_hull = np.zeros(center_roi.shape[:2], dtype=np.uint8)
        if len(xs_c) > 100:
            pts_c = np.column_stack([xs_c, ys_c]).astype(np.float32)
            (cx_c, _), (w_c, h_c), ang_c = cv2.minAreaRect(pts_c)
            if w_c > h_c:
                w_c, h_c = h_c, w_c
                ang_c += 90.0
            full_h = max(h_c, min(center_roi.shape[0] - 8.0, w_c * 1.38))
            box_c = cv2.boxPoints(((cx_c, center_roi.shape[0] * 0.495), (w_c + 8.0, full_h), ang_c))
            cv2.drawContours(c_hull, [np.int32(box_c)], 0, 255, -1)
            # Round the 4 corners of the A4 sheet via erode + elliptical dilate
            k_rnd = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
            c_hull = cv2.erode(c_hull, k_rnd)
            c_hull = cv2.dilate(c_hull, k_rnd)
            c_hull = cv2.GaussianBlur(c_hull, (7, 7), 1.5)
        center_im = Image.fromarray(np.dstack([center_roi, c_hull])).resize((740, 875), Image.LANCZOS)

        # Left & Right blurred side cards for depth-of-field
        left_roi = roi[60:640, 0:420]
        l_mask = np.clip((left_roi.max(axis=2).astype(np.float32) - 45.0) * 2.2, 0, 210).astype(np.uint8)
        l_mask = cv2.GaussianBlur(l_mask, (21, 21), 6.0)
        left_im = Image.fromarray(np.dstack([left_roi, l_mask])).resize((360, 560), Image.LANCZOS)

        right_roi = roi[60:640, 1180:1600]
        r_mask = np.clip((right_roi.max(axis=2).astype(np.float32) - 45.0) * 2.2, 0, 210).astype(np.uint8)
        r_mask = cv2.GaussianBlur(r_mask, (21, 21), 6.0)
        right_im = Image.fromarray(np.dstack([right_roi, r_mask])).resize((360, 560), Image.LANCZOS)

        canvas.alpha_composite(left_im, (-85, 585))
        canvas.alpha_composite(right_im, (W - 275, 585))
        composite_with_drop_shadow(canvas, center_im, (W - 740) // 2, 435, shadow_alpha=150)

        # Dynamic Template Caption at bottom (`y = 1435`)
        if t < 17.85:
            tpl_lbl = "Studio · Cards arrondies, style SaaS"
        elif t < 19.35:
            tpl_lbl = "Creative · Formes géométriques"
        elif t < 20.90:
            tpl_lbl = "Minimalist · Serif élégant"
        else:
            tpl_lbl = "Modern Orange · Noir / orange"
        f_cap = get_font(JAKARTA_SEMI, 38)
        bb_c = d.textbbox((0, 0), tpl_lbl, font=f_cap)
        d.text(((W - (bb_c[2] - bb_c[0])) // 2, 1410), tpl_lbl, font=f_cap, fill=(242, 246, 255, 250))
        return canvas

    # Part 4B (22.40s - 24.40s): Full-Screen 3D Tilted 12-Template Masonry Wall
    w_age = t - 22.40
    # Assemble 100% text-free masonry tiles from left (`x=0..650`) and right (`x=1270..1920`) + top/bottom of `rgb_1080p`
    tile_top = Image.fromarray(rgb_1080p[0:335, 360:1560]).resize((W, 480), Image.LANCZOS)
    tile_mid_l = Image.fromarray(rgb_1080p[80:1000, 0:640]).resize((W // 2, 960), Image.LANCZOS)
    tile_mid_r = Image.fromarray(rgb_1080p[80:1000, 1280:1920]).resize((W // 2, 960), Image.LANCZOS)
    tile_bot = Image.fromarray(rgb_1080p[735:1070, 360:1560]).resize((W, 480), Image.LANCZOS)
    wall = Image.new("RGBA", (W, H), (8, 10, 18, 255))
    wall.paste(tile_top, (0, 0))
    wall.paste(tile_mid_l, (0, 480))
    wall.paste(tile_mid_r, (W // 2, 480))
    wall.paste(tile_bot, (0, 1440))

    # Radial dark vignette in the center so "12 / mises en page incluses" pops
    if "wall_vignette" not in _ASSET_CACHE:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dist = np.sqrt(((xx - W * 0.5) / 480.0) ** 2 + ((yy - H * 0.5) / 520.0) ** 2)
        vig_a = np.clip(1.0 - dist * 0.65, 0.25, 0.88)
        vig = np.zeros((H, W, 4), dtype=np.uint8)
        vig[..., 0] = 6
        vig[..., 1] = 9
        vig[..., 2] = 18
        vig[..., 3] = (vig_a * 255.0).astype(np.uint8)
        _ASSET_CACHE["wall_vignette"] = Image.fromarray(vig)
    wall = Image.alpha_composite(wall, _ASSET_CACHE["wall_vignette"])

    d = ImageDraw.Draw(wall)
    na, ndy = reveal(w_age, delay=0.04, dur=0.38, dy_px=24.0)
    f_12 = get_font(JAKARTA_EBOLD, 190)
    bb_12 = d.textbbox((0, 0), "12", font=f_12)
    d.text(((W - (bb_12[2] - bb_12[0])) // 2, int(680 + ndy)), "12", font=f_12, fill=(255, 255, 255, int(255 * na)))

    f_m = get_font(JAKARTA_BOLD, 62)
    m_txt = "mises en page incluses"
    bb_m = d.textbbox((0, 0), m_txt, font=f_m)
    d.text(((W - (bb_m[2] - bb_m[0])) // 2, int(920 + ndy)), m_txt, font=f_m, fill=(255, 255, 255, int(255 * na)))

    f_s = get_font(INTER_REG, 34)
    s_txt = "Comparez-les sur votre propre contenu."
    bb_s = d.textbbox((0, 0), s_txt, font=f_s)
    d.text(((W - (bb_s[2] - bb_s[0])) // 2, int(1015 + ndy)), s_txt, font=f_s, fill=(203, 213, 225, int(245 * na)))

    prog = clamp(t / TOTAL_DURATION)
    d.rectangle([0, H - 8, max(8, int(W * prog)), H], fill=(37, 99, 235, 255))
    return wall


# ---------------------------------------------------------------------------
# SCENE 5 (24.40s - 29.20s): "Votre couleur. Votre police. Votre devise."
# ---------------------------------------------------------------------------
def render_scene5(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 24.40
    canvas = get_sphere_stage(t, show_watermark=True, sphere_layout="upper_left")
    d = ImageDraw.Draw(canvas)

    draw_eyebrow_and_headline(
        canvas,
        age,
        eyebrow="VOTRE IDENTITÉ",
        lines=["Votre couleur.", "Votre police. Votre devise."],
        x=64,
        y=158,
        title_size=68,
        eyebrow_delay=0.06,
        title_delay=0.16,
    )

    # Extract the live color-morphing 3D A4 Devis sheet (`x=1150..1820, y=105..895`)
    devis_rgba = extract_single_3d_object(rgb_1080p, 1150, 105, 1820, 895, dilate_px=5, include_header=True)
    devis_scaled = devis_rgba.resize((680, 802), Image.LANCZOS)
    composite_with_drop_shadow(canvas, devis_scaled, 372, 495, shadow_alpha=145)

    # 3x3 Color Swatch Grid on Left (`x=64, y=580`)
    swatches = [
        (29, 99, 242),    # 0: Royal Blue
        (24, 24, 27),     # 1: Carbon Black
        (239, 68, 68),    # 2: Crimson Red
        (16, 158, 96),    # 3: Emerald Green
        (139, 92, 246),   # 4: Violet
        (234, 88, 12),    # 5: Orange
        (219, 39, 119),   # 6: Rose Pink
        (13, 148, 136),   # 7: Teal
        (67, 56, 202),    # 8: Indigo
    ]
    if t < 25.55:
        active_sw = 0
    elif t < 26.85:
        active_sw = 3
    elif t < 28.10:
        active_sw = 6
    else:
        active_sw = 4

    sa, sdy = reveal(age, delay=0.35, dur=0.45, dy_px=22.0)
    if sa > 0.02:
        for idx, col in enumerate(swatches):
            r, c = divmod(idx, 3)
            sx = 64 + c * 96
            sy = int(605 + r * 96 + sdy)
            if idx == active_sw:
                d.rounded_rectangle([sx - 5, sy - 5, sx + 85, sy + 85], radius=24, fill=(*col, int(255 * sa)), outline=(226, 232, 240, int(255 * sa)), width=4)
            else:
                d.rounded_rectangle([sx, sy, sx + 80, sy + 80], radius=20, fill=(*col, int(245 * sa)))

    # Bottom Glass Currency Card (`DEVISE : 495 600 F / 755,80 € / 826,00 $`) + `Police au choix`
    ca, cdy = reveal(age, delay=0.55, dur=0.45, dy_px=24.0)
    if ca > 0.02:
        if t < 26.75:
            cur_val, cur_name = "495 600 F", "Franc CFA"
        elif t < 28.20:
            cur_val, cur_name = "755,80 €", "Euro"
        else:
            cur_val, cur_name = "826,00 $", "Dollar US"

        cw, ch = 460, 245
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=28, fill=(10, 15, 28, int(238 * ca)), outline=(255, 255, 255, int(38 * ca)), width=2)
        cd.text((38, 32), "D E V I S E", font=get_font(JAKARTA_SEMI, 21), fill=(148, 163, 184, int(245 * ca)))
        cd.text((38, 76), cur_val, font=get_font(JAKARTA_EBOLD, 64), fill=(255, 255, 255, int(255 * ca)))
        cd.text((38, 168), cur_name, font=get_font(INTER_REG, 29), fill=(148, 163, 184, int(245 * ca)))
        composite_with_drop_shadow(canvas, card, 64, int(1340 + cdy), shadow_alpha=int(130 * ca))

        draw_glass_pill(canvas, 64, int(1615 + cdy), "Police au choix", dot_color=(59, 130, 246), alpha=ca, font_size=28)

    return canvas


# ---------------------------------------------------------------------------
# SCENE 6 (29.20s - 35.40s): "Faites signer. Exportez. Envoyez."
# ---------------------------------------------------------------------------
def render_scene6(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 29.20
    canvas = get_sphere_stage(t, show_watermark=True, sphere_layout="upper_left")

    eye_lbl = "SIGNATURE EN LIGNE" if t < 32.35 else "EXPORT"
    draw_eyebrow_and_headline(
        canvas,
        age,
        eyebrow=eye_lbl,
        lines=["Faites signer. Exportez.", "Envoyez."],
        x=64,
        y=158,
        title_size=66,
        eyebrow_delay=0.06,
        title_delay=0.16,
    )

    # Extract the 1 or 2 animated 3D Smartphones (`x=150..980, y=145..1072`)
    if t < 32.15:
        # In Scene 6A, the phone has a dimmed top/bottom backdrop around the white signature modal.
        # Find the horizontal span of the white signature modal and construct a clean rounded phone mask!
        roi = rgb_1080p[150:1060, 220:870]
        white = (roi.min(axis=2) > 140).astype(np.uint8) * 255
        ys, xs = np.where(white > 0)
        p_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
        if len(xs) > 100:
            # Fit minimum area rotated rectangle to the white modal, then expand vertically to full phone height
            pts = np.column_stack([xs, ys]).astype(np.float32)
            (cx_m, cy_m), (w_m, h_m), ang_m = cv2.minAreaRect(pts)
            if w_m > h_m:
                w_m, h_m = h_m, w_m
                ang_m += 90.0
            box = cv2.boxPoints(((cx_m, roi.shape[0] * 0.49), (w_m + 24, roi.shape[0] * 0.90), ang_m))
            cv2.drawContours(p_mask, [np.int32(box)], 0, 255, -1)
            k_rnd = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (55, 55))
            p_mask = cv2.erode(p_mask, k_rnd)
            p_mask = cv2.dilate(p_mask, k_rnd)
            p_mask = cv2.GaussianBlur(p_mask, (9, 9), 2.0)
        phones_rgba = Image.fromarray(np.dstack([roi, p_mask]))
        phones_scaled = phones_rgba.resize((660, 925), Image.LANCZOS)
        composite_with_drop_shadow(canvas, phones_scaled, (W - 660) // 2, 445, shadow_alpha=145)
    else:
        # Dual phones: left phone (signature modal) + right phone (export modal)
        roi = rgb_1080p[145:1072, 150:980]
        rh, rw = roi.shape[:2]
        white = (roi.min(axis=2) > 135).astype(np.uint8) * 255
        # Left phone mask from its white modal (`x < 395`)
        w_left = white.copy()
        w_left[:, 395:] = 0
        ys_l, xs_l = np.where(w_left > 0)
        m_left = np.zeros((rh, rw), dtype=np.uint8)
        if len(xs_l) > 100:
            pts_l = np.column_stack([xs_l, ys_l]).astype(np.float32)
            (cx_l, _), (w_l, h_l), ang_l = cv2.minAreaRect(pts_l)
            if w_l > h_l:
                w_l, h_l = h_l, w_l
                ang_l += 90.0
            box_l = cv2.boxPoints(((cx_l, rh * 0.48), (w_l + 24, rh * 0.88), ang_l))
            cv2.drawContours(m_left, [np.int32(box_l)], 0, 255, -1)
            k_rnd = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (55, 55))
            m_left = cv2.erode(m_left, k_rnd)
            m_left = cv2.dilate(m_left, k_rnd)
        # Right phone mask (`x >= 385`)
        w_right = white.copy()
        w_right[:, :385] = 0
        m_right = _hull_from_binary(w_right, min_area=3000)
        kr = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29))
        m_right = cv2.dilate(m_right, kr)
        mask = cv2.bitwise_or(m_left, m_right)
        mask = cv2.GaussianBlur(mask, (9, 9), 2.0)
        phones_rgba = Image.fromarray(np.dstack([roi, mask]))
        phones_scaled = phones_rgba.resize((840, 938), Image.LANCZOS)
        composite_with_drop_shadow(canvas, phones_scaled, (W - 840) // 2, 440, shadow_alpha=145)

        # Bottom Glass PDF Card + 3 Export Pills (`t >= 32.35s`)
        ea, edy = reveal(t - 32.35, delay=0.05, dur=0.42, dy_px=22.0)
        if ea > 0.02:
            cw, ch = 640, 138
            card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card)
            cd.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=26, fill=(14, 19, 34, int(242 * ea)), outline=(255, 255, 255, int(42 * ea)), width=2)
            cd.rounded_rectangle([28, 28, 110, 110], radius=18, fill=(225, 45, 57, int(255 * ea)))
            cd.text((42, 50), "PDF", font=get_font(JAKARTA_EBOLD, 27), fill=(255, 255, 255, int(255 * ea)))
            cd.text((138, 30), "Devis-2026-014", font=get_font(JAKARTA_BOLD, 34), fill=(255, 255, 255, int(255 * ea)))
            cd.text((138, 76), "A4 · prêt à envoyer", font=get_font(INTER_REG, 26), fill=(148, 163, 184, int(245 * ea)))
            composite_with_drop_shadow(canvas, card, 64, int(1415 + edy), shadow_alpha=int(130 * ea))

            p1, dy1 = reveal(t - 32.35, delay=0.25, dur=0.38, dy_px=16.0)
            p2, dy2 = reveal(t - 32.35, delay=0.38, dur=0.38, dy_px=16.0)
            p3, dy3 = reveal(t - 32.35, delay=0.51, dur=0.38, dy_px=16.0)
            draw_glass_pill(canvas, 64, int(1585 + dy1), "PDF A4 multi-pages", dot_color=(59, 130, 246), alpha=p1, font_size=26)
            draw_glass_pill(canvas, 485, int(1585 + dy2), "SVG vectoriel", dot_color=(59, 130, 246), alpha=p2, font_size=26)
            draw_glass_pill(canvas, 64, int(1668 + dy3), "Lien de signature client", dot_color=(59, 130, 246), alpha=p3, font_size=26)

    return canvas


# ---------------------------------------------------------------------------
# SCENE 7 (35.40s - 40.20s): "Accepté ? Un clic : c'est une facture."
# ---------------------------------------------------------------------------
def render_scene7(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 35.40
    canvas = get_sphere_stage(t, show_watermark=True, sphere_layout="upper_left")

    draw_eyebrow_and_headline(
        canvas,
        age,
        eyebrow="DU DEVIS AU PAIEMENT",
        lines=["Accepté ? Un clic :", "c'est une facture."],
        x=64,
        y=158,
        title_size=68,
        eyebrow_delay=0.06,
        title_delay=0.16,
    )

    # 4 Status Pills row (`Brouillon`, `Envoyé`, `Accepté`, `Payé`)
    statuses = [
        ("Brouillon", (148, 163, 184), False, 0.35),
        ("Envoyé", (59, 130, 246), False, 0.48),
        ("Accepté", (16, 185, 129), False, 0.61),
        ("Payé", (139, 92, 246), t >= 37.0, 0.74),
    ]
    cur_x = 56
    for s_txt, s_col, is_act, s_dly in statuses:
        sa, sdy = reveal(age, delay=s_dly, dur=0.38, dy_px=16.0)
        w_p = draw_glass_pill(canvas, cur_x, int(468 + sdy), s_txt, dot_color=s_col, alpha=sa, active=is_act, font_size=25)
        cur_x += w_p + 16

    # Extract the animated 3D Smartphone on Right (`x=1180..1710, y=95..960`)
    phone_rgba = extract_single_3d_object(rgb_1080p, 1180, 95, 1710, 960, dilate_px=14, include_header=False)
    phone_scaled = phone_rgba.resize((610, 995), Image.LANCZOS)
    composite_with_drop_shadow(canvas, phone_scaled, 435, 580, shadow_alpha=145)

    # Floating Dark Glass Facture Card on Left (`FAC-2026-008`)
    fa, fdy = reveal(age, delay=1.25, dur=0.45, dy_px=24.0)
    if fa > 0.02:
        cw, ch = 520, 285
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=28, fill=(10, 15, 28, int(242 * fa)), outline=(255, 255, 255, int(40 * fa)), width=2)
        cd.text((38, 34), "F A C T U R E", font=get_font(JAKARTA_SEMI, 21), fill=(148, 163, 184, int(245 * fa)))
        cd.text((38, 78), "FAC-2026-008", font=get_font(JAKARTA_EBOLD, 52), fill=(255, 255, 255, int(255 * fa)))
        cd.text((38, 164), "Numérotation automatique, TVA", font=get_font(INTER_REG, 25), fill=(148, 163, 184, int(245 * fa)))
        cd.text((38, 202), "reprise, même mise en page.", font=get_font(INTER_REG, 25), fill=(148, 163, 184, int(245 * fa)))
        composite_with_drop_shadow(canvas, card, 48, int(1065 + fdy), shadow_alpha=int(135 * fa))

    return canvas


# ---------------------------------------------------------------------------
# SCENE 8 (40.20s - 46.40s): "Ouvrez. Remplissez. Envoyez." (Final CTA)
# ---------------------------------------------------------------------------
def render_scene8(t: float, rgb_1080p: np.ndarray) -> Image.Image:
    age = t - 40.20
    canvas = get_sphere_stage(t, show_watermark=False, sphere_layout="center")
    d = ImageDraw.Draw(canvas)

    # 1. Official 3D Blue Glass Icon
    la, ldy = reveal(age, delay=0.05, dur=0.45, dy_px=22.0)
    logo_im = get_logo(168)
    canvas.alpha_composite(logo_im, ((W - 168) // 2, int(335 + ldy)))

    # 2. Headline: "Ouvrez. Remplissez. / Envoyez."
    f_h = get_font(JAKARTA_EBOLD, 72)
    for idx, ln in enumerate(["Ouvrez. Remplissez.", "Envoyez."]):
        ta, tdy = reveal(age, delay=0.22 + idx * 0.08, dur=0.45, dy_px=24.0)
        if ta > 0.02:
            bb = d.textbbox((0, 0), ln, font=f_h)
            d.text(((W - (bb[2] - bb[0])) // 2, int(555 + idx * 84 + tdy)), ln, font=f_h, fill=(255, 255, 255, int(255 * ta)))

    # 3. Subtitle
    sa, sdy = reveal(age, delay=0.48, dur=0.45, dy_px=20.0)
    if sa > 0.02:
        f_sub = get_font(INTER_REG, 32)
        for s_i, sln in enumerate([
            "20 exports offerts. 12 modèles. Aucune inscription,",
            "aucune carte bancaire.",
        ]):
            bb_s = d.textbbox((0, 0), sln, font=f_sub)
            d.text(((W - (bb_s[2] - bb_s[0])) // 2, int(765 + s_i * 44 + sdy)), sln, font=f_sub, fill=(148, 163, 184, int(245 * sa)))

    # 4. Bright White URL Pill (`• devis-designer-app.jerode.workers.dev`)
    ua, udy = reveal(age, delay=0.72, dur=0.45, dy_px=22.0)
    if ua > 0.02:
        pw, ph = 780, 96
        px, py = (W - pw) // 2, int(925 + udy)
        d.rounded_rectangle([px, py, px + pw, py + ph], radius=48, fill=(255, 255, 255, int(255 * ua)))
        d.ellipse([px + 44, py + 40, px + 60, py + 56], fill=(29, 99, 242, int(255 * ua)))
        f_u = get_font(JAKARTA_BOLD, 33)
        u_txt = "devis-designer-app.jerode.workers.dev"
        bb_u = d.textbbox((0, 0), u_txt, font=f_u)
        d.text((px + 82, py + (ph - (bb_u[3] - bb_u[1])) // 2 - bb_u[1]), u_txt, font=f_u, fill=(15, 23, 42, int(255 * ua)))

    # 5. Glowing Royal-Blue CTA Button (`Ouvrez l'application, c'est tout`)
    ba, bdy = reveal(age, delay=1.05, dur=0.45, dy_px=22.0)
    if ba > 0.02:
        bw, bh = 660, 104
        bx, by = (W - bw) // 2, int(1055 + bdy)
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=52, fill=(29, 99, 242, int(255 * ba)))
        f_b = get_font(JAKARTA_BOLD, 34)
        b_txt = "Ouvrez l'application, c'est tout"
        bb_b = d.textbbox((0, 0), b_txt, font=f_b)
        d.text((bx + (bw - (bb_b[2] - bb_b[0])) // 2, by + (bh - (bb_b[3] - bb_b[1])) // 2 - bb_b[1]), b_txt, font=f_b, fill=(255, 255, 255, int(255 * ba)))

    # 6. Bottom 3 Trust Checkmarks (Vector check circles, zero Unicode fallback!)
    checks = [
        ("Vos documents restent chez vous", 1.35),
        ("Pas de compte, pas de carte", 1.48),
        ("20 exports offerts", 1.61),
    ]
    f_chk = get_font(INTER_MED, 28)
    for c_i, (c_txt, c_dly) in enumerate(checks):
        ca, cdy = reveal(age, delay=c_dly, dur=0.40, dy_px=16.0)
        if ca <= 0.02:
            continue
        bb_c = d.textbbox((0, 0), c_txt, font=f_chk)
        tot_w = 48 + (bb_c[2] - bb_c[0])
        cx0 = (W - tot_w) // 2
        cy0 = int(1245 + c_i * 64 + cdy)
        # Circle + vector check
        d.ellipse([cx0, cy0, cx0 + 34, cy0 + 34], outline=(59, 130, 246, int(230 * ca)), width=2)
        d.line([(cx0 + 9, cy0 + 17), (cx0 + 15, cy0 + 23), (cx0 + 25, cy0 + 11)], fill=(96, 165, 250, int(255 * ca)), width=3)
        d.text((cx0 + 48, cy0 - 2), c_txt, font=f_chk, fill=(203, 213, 225, int(245 * ca)))

    return canvas


# ---------------------------------------------------------------------------
# Master Frame Dispatcher (With Smooth Cross-Fade Transitions at Exact Seams)
# ---------------------------------------------------------------------------
def render_frame_from_ref(fi: int, rgb_1080p: np.ndarray) -> np.ndarray:
    t = fi / FPS
    if t < 5.00:
        im = render_scene1(t, rgb_1080p)
    elif t < 9.00:
        im = render_scene2(t, rgb_1080p)
    elif t < 16.00:
        im = render_scene3(t, rgb_1080p)
    elif t < 24.40:
        im = render_scene4(t, rgb_1080p)
    elif t < 29.20:
        im = render_scene5(t, rgb_1080p)
    elif t < 35.40:
        im = render_scene6(t, rgb_1080p)
    elif t < 40.20:
        im = render_scene7(t, rgb_1080p)
    else:
        im = render_scene8(t, rgb_1080p)
    return np.array(im.convert("RGB"), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Master Audio Builder (Original `devis-designer-pub-16x9.mp4` Soundtrack &
# UI SFX + Synchronized French Voiceover `voice-02`)
# ---------------------------------------------------------------------------
def build_master_audio(ffmpeg_exe: str):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    ref_wav = "/tmp/ref_pub/ref_audio.wav"
    if not os.path.exists(ref_wav):
        subprocess.run(
            [ffmpeg_exe, "-y", "-i", REF_VIDEO, "-vn", "-ar", "48000", "-ac", "2", "-sample_fmt", "s16", ref_wav],
            check=True,
            stderr=subprocess.DEVNULL,
        )

    with wave.open(ref_wav, "rb") as wf:
        sr = wf.getframerate()
        raw_ref = wf.readframes(wf.getnframes())
    ref_arr = np.frombuffer(raw_ref, dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0
    total_samples = int(round(TOTAL_DURATION * sr))
    if ref_arr.shape[0] < total_samples:
        pad = np.zeros((total_samples - ref_arr.shape[0], 2), dtype=np.float32)
        ref_arr = np.vstack([ref_arr, pad])
    else:
        ref_arr = ref_arr[:total_samples]

    vo_arr = np.zeros_like(ref_arr)
    vo_env = np.zeros(total_samples, dtype=np.float32)

    windows = [
        ("v3-s1", 0.25, 4.80),
        ("v3-s2", 5.10, 8.90),
        ("v3-s3", 9.15, 15.75),
        ("v3-s4", 16.20, 24.10),
        ("v3-s5", 24.50, 29.05),
        ("v3-s6", 29.35, 35.20),
        ("v3-s7", 35.50, 40.05),
        ("v3-s8", 40.35, 46.20),
    ]
    for name, t0, t1 in windows:
        mp3 = f"{AUDIO_DIR}/{name}.mp3"
        if not os.path.exists(mp3):
            continue
        wav_raw = f"/tmp/ref_pub/{name}_raw.wav"
        subprocess.run([ffmpeg_exe, "-y", "-i", mp3, "-ar", "48000", "-ac", "2", wav_raw], check=True, stderr=subprocess.DEVNULL)
        with wave.open(wav_raw, "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        max_dur = t1 - t0
        tempo = max(1.08, min(1.28, (dur + 0.10) / max_dur))
        wav_out = f"/tmp/ref_pub/{name}.wav"
        subprocess.run(
            [ffmpeg_exe, "-y", "-i", mp3, "-filter:a", f"atempo={tempo:.3f}", "-ar", "48000", "-ac", "2", "-sample_fmt", "s16", wav_out],
            check=True,
            stderr=subprocess.DEVNULL,
        )
        with wave.open(wav_out, "rb") as wf:
            seg_raw = wf.readframes(wf.getnframes())
        seg = np.frombuffer(seg_raw, dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0
        s0 = int(round(t0 * sr))
        s1 = min(total_samples, s0 + seg.shape[0])
        if s1 > s0:
            vo_arr[s0:s1] += seg[: s1 - s0] * 1.15
            vo_env[s0:s1] = 1.0

    # Smooth ducking envelope on original soundtrack & SFX (keep UI SFX audible at 0.42 during speech, 0.85 between phrases)
    kernel_len = int(0.18 * sr)
    kernel = np.ones(kernel_len, dtype=np.float32) / kernel_len
    smooth_env = np.convolve(vo_env, kernel, mode="same")
    duck_gain = (0.82 - 0.42 * smooth_env)[:, None]

    mix = np.clip(ref_arr * duck_gain + vo_arr, -0.98, 0.98)
    mix_int16 = (mix * 32767.0).astype(np.int16)
    with wave.open(MIXED_WAV, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(mix_int16.tobytes())


# ---------------------------------------------------------------------------
# Main Preview & Full Video Renderer
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=str, default="", help="Save a 12-frame preview contact sheet")
    args = parser.parse_args()

    cap = cv2.VideoCapture(REF_VIDEO)
    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        sample_times = [
            4.35, 7.25, 11.60, 14.50,
            18.85, 21.75, 23.20, 27.55,
            31.90, 34.80, 37.70, 44.95,
        ]
        cols, rows = 4, 3
        tw, th = 270, 480
        sheet = Image.new("RGB", (cols * tw, rows * th), (10, 12, 18))
        for idx, st in enumerate(sample_times):
            fi = min(TOTAL_FRAMES - 1, int(round(st * FPS)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, bgr = cap.read()
            rgb_1080p = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            out_rgb = render_frame_from_ref(fi, rgb_1080p)
            thumb = Image.fromarray(out_rgb).resize((tw, th), Image.LANCZOS)
            td = ImageDraw.Draw(thumb)
            td.rectangle([8, 8, 120, 36], fill=(0, 0, 0))
            td.text((14, 12), f"t={st:05.2f}s", fill=(96, 165, 250))
            sheet.paste(thumb, ((idx % cols) * tw, (idx // cols) * th))
        cap.release()
        sheet.save(args.preview, quality=92)
        print(f"Saved preview contact sheet to {args.preview}")
        return

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(FILM_DIR, exist_ok=True)
    build_master_audio(ffmpeg_exe)

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

    for fi in range(TOTAL_FRAMES):
        ok, bgr = cap.read()
        if not ok:
            break
        rgb_1080p = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        out_rgb = render_frame_from_ref(fi, rgb_1080p)
        proc_out.stdin.write(out_rgb.tobytes())
        if (fi + 1) % 240 == 0 or fi == TOTAL_FRAMES - 1:
            print(f"Rendered {fi + 1}/{TOTAL_FRAMES} frames ({(fi + 1) / TOTAL_FRAMES * 100:.1f}%)", flush=True)

    cap.release()
    proc_out.stdin.close()
    ret = proc_out.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")
    print(f"Successfully rendered {OUT_MP4}")


if __name__ == "__main__":
    main()
