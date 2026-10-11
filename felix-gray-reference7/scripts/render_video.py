#!/usr/bin/env python3
"""
Master 1080x1920 (9:16) Video Renderer for `videobrut 7.mp4`
Inspired by `reference 7.mp4`.
"""
import json
import math
import os
import subprocess
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
W, H = 1080, 1920
FPS_NUM, FPS_DEN = 24000, 1001
FPS = FPS_NUM / FPS_DEN  # ~23.976 fps

RAW_VIDEO = "/home/user/COOL-backup/videobrut 7.mp4"
MIXED_WAV = "/home/user/.cache/sfx_ref7/mixed_audio.wav"
WORDS_JSON = "/home/user/.cache/whisper/brut7_master_words.json"
OUT_DIR = "/home/user/COOL-backup/felix-gray-reference7/film"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_MP4 = os.path.join(OUT_DIR, "felix-gray-reference7-9x16.mp4")

FONT_ROOT = "/home/user/.cache/fonts/node_modules/@expo-google-fonts"
F_MONT_LIGHT = f"{FONT_ROOT}/montserrat/300Light/Montserrat_300Light.ttf"
F_MONT_REG = f"{FONT_ROOT}/montserrat/400Regular/Montserrat_400Regular.ttf"
F_MONT_MED = f"{FONT_ROOT}/montserrat/500Medium/Montserrat_500Medium.ttf"
F_MONT_SEMI = f"{FONT_ROOT}/montserrat/600SemiBold/Montserrat_600SemiBold.ttf"
F_MONT_BOLD = f"{FONT_ROOT}/montserrat/700Bold/Montserrat_700Bold.ttf"
F_MONT_EBOLD = f"{FONT_ROOT}/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf"
F_MONT_BLACK = f"{FONT_ROOT}/montserrat/900Black/Montserrat_900Black.ttf"
F_MONT_BLACK_IT = f"{FONT_ROOT}/montserrat/900Black_Italic/Montserrat_900Black_Italic.ttf"
F_DAFOE = f"{FONT_ROOT}/mr-dafoe/400Regular/MrDafoe_400Regular.ttf"
F_INTER_REG = f"{FONT_ROOT}/inter/400Regular/Inter_400Regular.ttf"
F_INTER_MED = f"{FONT_ROOT}/inter/500Medium/Inter_500Medium.ttf"
F_INTER_BOLD = f"{FONT_ROOT}/inter/700Bold/Inter_700Bold.ttf"

# Color Palette (from `reference 7.mp4`)
C_WHITE = (255, 255, 255)
C_SILVER = (202, 210, 226)
C_BLUE = (37, 88, 255)       # #2558FF signature electric cobalt
C_BLUE_BRIGHT = (78, 138, 255)
C_CRIMSON = (255, 36, 66)    # #FF2442 signature crimson script

_FONT_CACHE = {}


def get_font(path, size):
    key = (path, int(size))
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, int(size))
    return _FONT_CACHE[key]


# ---------------------------------------------------------------------------
# Easing & Math Helpers
# ---------------------------------------------------------------------------
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out_cubic(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t, s=1.45):
    t = clamp(t)
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def ease_in_out_cubic(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def alpha_composite_roi(dst_rgb, src_rgba, x0=0, y0=0):
    """Fast ROI alpha compositing of an RGBA PIL image onto a HxWx3 uint8 numpy frame."""
    sw, sh = src_rgba.size
    x1, y1 = x0 + sw, y0 + sh
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x1), min(H, y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    arr = np.asarray(src_rgba)[cy0 - y0 : cy1 - y0, cx0 - x0 : cx1 - x0]
    a = arr[:, :, 3:4].astype(np.float32) * (1.0 / 255.0)
    if np.max(a) <= 0.001:
        return
    roi = dst_rgb[cy0:cy1, cx0:cx1].astype(np.float32)
    fg = arr[:, :, :3].astype(np.float32)
    dst_rgb[cy0:cy1, cx0:cx1] = np.clip(roi * (1.0 - a) + fg * a, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Pre-rendered Studio Backgrounds & Vignettes
# ---------------------------------------------------------------------------
def build_talking_head_grade_overlay():
    """
    Creates the `reference 7.mp4` lighting atmosphere over talking-head frames:
    - Subtle royal-blue studio ambient glow near upper background (`y=320..760`)
    - Smooth dark chest-level gradient (`y=920..1580`) so chest typography pops
    - Subtle cinematic edge vignette
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # Top-center royal blue ambient studio light (subtle)
    d_top = np.sqrt(((xx - W * 0.50) / 480.0) ** 2 + ((yy - H * 0.23) / 360.0) ** 2)
    blue_glow = np.clip(1.0 - d_top, 0, 1) ** 2.2 * 0.18

    # Chest & lower torso dark vignette for crisp text contrast
    d_chest = np.exp(-((yy - H * 0.64) / 340.0) ** 2) * np.exp(-((xx - W * 0.50) / 560.0) ** 2)
    bottom_dark = np.clip((yy - H * 0.48) / (H * 0.52), 0, 1) ** 1.4 * 0.46
    edge_vig = np.clip(((xx - W * 0.5) / (W * 0.52)) ** 2 + ((yy - H * 0.5) / (H * 0.52)) ** 2 - 0.35, 0, 1) * 0.32

    dark_alpha = np.clip(d_chest * 0.34 + bottom_dark + edge_vig, 0, 0.68)

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    total_a = np.clip(dark_alpha + blue_glow, 0.001, 0.72)
    w_blue = blue_glow / total_a
    rgba[:, :, 0] = np.clip(w_blue * 22 + (1 - w_blue) * 2, 0, 255).astype(np.uint8)
    rgba[:, :, 1] = np.clip(w_blue * 68 + (1 - w_blue) * 5, 0, 255).astype(np.uint8)
    rgba[:, :, 2] = np.clip(w_blue * 210 + (1 - w_blue) * 16, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(total_a * 255, 0, 255).astype(np.uint8)
    return rgba


def build_midnight_blue_bg():
    """Full-screen deep midnight-blue studio canvas (`#020512` + cobalt radial glow)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.sqrt(((xx - W * 0.50) / 520.0) ** 2 + ((yy - H * 0.48) / 560.0) ** 2)
    glow = np.exp(-(dist ** 1.75) * 1.15)
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    rgb[:, :, 0] = np.clip(2 + glow * 16, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(5 + glow * 44, 0, 255).astype(np.uint8)
    rgb[:, :, 2] = np.clip(18 + glow * 138, 0, 255).astype(np.uint8)
    return rgb


def build_crimson_vignette_bg():
    """
    Full-screen dark crimson-red radial vignette matching `t=14.80s` of `reference 7.mp4`:
    Deep near-black center-left (`#080103`) with rich dark crimson glow (`#580615`) at top-right & edges.
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Primary crimson light pool in upper-right / outer ring
    d_tr = np.sqrt(((xx - W * 0.78) / 620.0) ** 2 + ((yy - H * 0.28) / 680.0) ** 2)
    glow_tr = np.exp(-(d_tr ** 1.6) * 0.95)
    # Secondary soft crimson edge glow at bottom-left
    d_bl = np.sqrt(((xx - W * 0.22) / 640.0) ** 2 + ((yy - H * 0.78) / 680.0) ** 2)
    glow_bl = np.exp(-(d_bl ** 1.7) * 1.25) * 0.55

    glow = np.clip(glow_tr + glow_bl, 0, 1.0)
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    rgb[:, :, 0] = np.clip(8 + glow * 88, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(1 + glow * 5, 0, 255).astype(np.uint8)
    rgb[:, :, 2] = np.clip(3 + glow * 18, 0, 255).astype(np.uint8)
    return rgb


# ---------------------------------------------------------------------------
# Signature Single-Word Kinetic Chest Captions (with Partial Inner Blue Glow)
# ---------------------------------------------------------------------------
_WORD_IMG_CACHE = {}


def get_word_caption_img(word_text, glow_Style="none"):
    """
    Renders a single chest-level word in `Montserrat ExtraBold` (72px).
    If `glow_Style == 'blue_lead'` (like `inquiry` at t=3.10s and `inconsistent` at t=8.30s
    in `reference 7.mp4`), applies a localized radial electric-blue light bloom + cyan-blue
    gradient tint across the leading letters while keeping the rest of the word crisp white!
    If `glow_Style == 'crimson_lead'`, uses a localized crimson-red glow.
    """
    key = (word_text, glow_Style)
    if key in _WORD_IMG_CACHE:
        return _WORD_IMG_CACHE[key]

    font = get_font(F_MONT_EBOLD, 72)
    dummy = Image.new("RGBA", (10, 10))
    d0 = ImageDraw.Draw(dummy)
    bbox = d0.textbbox((0, 0), word_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x, pad_y = 90, 75
    cw, ch = tw + pad_x * 2, th + pad_y * 2
    tx, ty = pad_x - bbox[0], pad_y - bbox[1]

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    # 1. Soft dark drop shadow for instant chest contrast
    shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    ds.text((tx, ty + 5), word_text, font=font, fill=(0, 0, 0, 195))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=9))
    canvas = Image.alpha_composite(canvas, shadow)

    # 2. Base text mask
    mask_im = Image.new("L", (cw, ch), 0)
    dm = ImageDraw.Draw(mask_im)
    dm.text((tx, ty), word_text, font=font, fill=255)
    mask_np = np.asarray(mask_im).astype(np.float32) / 255.0

    if glow_Style in ("blue_lead", "crimson_lead"):
        # Center the radial glow on the first ~28% of the word width (like 'in' of 'inquiry'/'inconsistent')
        gx = pad_x + min(tw * 0.26, 75.0)
        gy = pad_y + th * 0.52
        yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
        dist = np.sqrt(((xx - gx) / 68.0) ** 2 + ((yy - gy) / 48.0) ** 2)

        # Ambient radial glow behind those leading letters
        amb = np.exp(-(dist ** 1.65) * 1.1)
        amb_rgba = np.zeros((ch, cw, 4), dtype=np.uint8)
        if glow_Style == "blue_lead":
            amb_rgba[:, :, 0] = 30
            amb_rgba[:, :, 1] = 95
            amb_rgba[:, :, 2] = 255
        else:
            amb_rgba[:, :, 0] = 255
            amb_rgba[:, :, 1] = 36
            amb_rgba[:, :, 2] = 68
        amb_rgba[:, :, 3] = np.clip(amb * 155.0, 0, 255).astype(np.uint8)
        canvas = Image.alpha_composite(canvas, Image.fromarray(amb_rgba))

        # Letter fill gradient: vibrant electric blue/cyan at the glow core -> pure white
        tint = np.exp(-(dist ** 1.55) * 0.85)
        fg = np.zeros((ch, cw, 4), dtype=np.uint8)
        if glow_Style == "blue_lead":
            fg[:, :, 0] = np.clip(255 - tint * 205, 0, 255).astype(np.uint8)
            fg[:, :, 1] = np.clip(255 - tint * 115, 0, 255).astype(np.uint8)
            fg[:, :, 2] = 255
        else:
            fg[:, :, 0] = 255
            fg[:, :, 1] = np.clip(255 - tint * 195, 0, 255).astype(np.uint8)
            fg[:, :, 2] = np.clip(255 - tint * 170, 0, 255).astype(np.uint8)
        fg[:, :, 3] = np.clip(mask_np * 255.0, 0, 255).astype(np.uint8)
        canvas = Image.alpha_composite(canvas, Image.fromarray(fg))
    else:
        fg = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        df = ImageDraw.Draw(fg)
        df.text((tx, ty), word_text, font=font, fill=(255, 255, 255, 255))
        canvas = Image.alpha_composite(canvas, fg)

    _WORD_IMG_CACHE[key] = canvas
    return canvas


# ---------------------------------------------------------------------------
# 3-Tier & 4-Tier Asymmetric Stacked Lockups (Chest & Full-Screen)
# ---------------------------------------------------------------------------
def render_text_layer(text, font_path, size, color, glow_color=None, glow_radius=16):
    """Renders a single line of text with drop shadow and optional neon bloom."""
    font = get_font(font_path, size)
    dummy = Image.new("RGBA", (10, 10))
    d0 = ImageDraw.Draw(dummy)
    bbox = d0.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 55
    cw, ch = tw + pad * 2, th + pad * 2
    tx, ty = pad - bbox[0], pad - bbox[1]

    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    # Drop shadow
    sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((tx, ty + 5), text, font=font, fill=(0, 0, 0, 185))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=8))
    out = Image.alpha_composite(out, sh)

    if glow_color is not None:
        g1 = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(g1).text((tx, ty), text, font=font, fill=(*glow_color, 190))
        g1 = g1.filter(ImageFilter.GaussianBlur(radius=glow_radius))
        out = Image.alpha_composite(out, g1)

        g2 = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(g2).text((tx, ty), text, font=font, fill=(*glow_color, 150))
        g2 = g2.filter(ImageFilter.GaussianBlur(radius=max(4, glow_radius // 3)))
        out = Image.alpha_composite(out, g2)

    fg = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(fg).text((tx, ty), text, font=font, fill=(*color, 255))
    out = Image.alpha_composite(out, fg)
    return out, tw, th, pad


_LOCKUP_LINE_CACHE = {}


def get_cached_line(text, font_path, size, color, glow_color=None, glow_radius=16):
    key = (text, font_path, int(size), color, glow_color, glow_radius)
    if key not in _LOCKUP_LINE_CACHE:
        _LOCKUP_LINE_CACHE[key] = render_text_layer(text, font_path, size, color, glow_color, glow_radius)
    return _LOCKUP_LINE_CACHE[key]


def draw_stacked_lockup(frame_rgb, t, lines_spec, anchor_x, anchor_y, align="left", t_end=None):
    """
    Draws a multi-tier stacked lockup where each line in `lines_spec` has:
      (appear_t, text, font_path, size, color, glow_color, dx_offset, dy_offset)
    Supports smooth spring entrance per line and smooth fade-out near `t_end`.
    """
    fade_out = 1.0
    if t_end is not None and t > t_end - 0.16:
        fade_out = clamp((t_end - t) / 0.16)
    if fade_out <= 0.01:
        return

    for appear_t, text, font_path, size, color, glow_color, dx, dy in lines_spec:
        if t < appear_t:
            continue
        dt = t - appear_t
        p = ease_out_back(clamp(dt / 0.24), s=1.35)
        alpha_p = ease_out_cubic(clamp(dt / 0.16)) * fade_out

        im, tw, th, pad = get_cached_line(text, font_path, size, color, glow_color)
        slide_y = int((1.0 - p) * 22.0)

        if align == "center":
            x0 = int(anchor_x + dx - tw / 2 - pad)
        else:
            x0 = int(anchor_x + dx - pad)
        y0 = int(anchor_y + dy + slide_y - pad)

        if alpha_p < 0.99:
            arr = np.asarray(im).copy()
            arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * alpha_p).astype(np.uint8)
            im_use = Image.fromarray(arr)
        else:
            im_use = im

        alpha_composite_roi(frame_rgb, im_use, x0, y0)


# ---------------------------------------------------------------------------
# 3D Glowing Circular Blue Badges (Matching `t=12.30s`, `18.80s`, `20.60s`)
# ---------------------------------------------------------------------------
_BADGE_CACHE = {}


def draw_icon_vector(draw, icon_type, cx, cy, r):
    """Draws crisp white vector iconography inside a 3D circular orb."""
    w_white = (255, 255, 255, 255)
    s = r / 105.0  # normalized scale factor

    if icon_type == "megaphone":
        # Tilted megaphone horn + handle + sound waves (matches t=18.80s & t=20.60s)
        # Horn body polygon
        pts_horn = [
            (cx - 32 * s, cy + 2 * s),
            (cx + 18 * s, cy - 30 * s),
            (cx + 26 * s, cy + 16 * s),
            (cx - 26 * s, cy + 16 * s),
        ]
        draw.polygon(pts_horn, fill=w_white)
        # Rear cap
        draw.rounded_rectangle(
            [cx - 44 * s, cy - 2 * s, cx - 28 * s, cy + 20 * s],
            radius=int(5 * s),
            fill=w_white,
        )
        # Handle
        pts_handle = [
            (cx - 24 * s, cy + 16 * s),
            (cx - 12 * s, cy + 16 * s),
            (cx - 6 * s, cy + 36 * s),
            (cx - 18 * s, cy + 38 * s),
        ]
        draw.polygon(pts_handle, fill=w_white)
        # Front bell rim
        draw.line(
            [(cx + 21 * s, cy - 34 * s), (cx + 30 * s, cy + 20 * s)],
            fill=(12, 34, 110, 255),
            width=max(2, int(4 * s)),
        )
        draw.line(
            [(cx + 25 * s, cy - 33 * s), (cx + 34 * s, cy + 19 * s)],
            fill=w_white,
            width=max(3, int(6 * s)),
        )
        # Sound wave ticks
        for ang, d1, d2 in [(-24, 34, 46), (-4, 36, 50), (16, 34, 46)]:
            rad = math.radians(ang)
            x1 = cx + 24 * s + math.cos(rad) * d1 * s
            y1 = cy - 6 * s + math.sin(rad) * d1 * s
            x2 = cx + 24 * s + math.cos(rad) * d2 * s
            y2 = cy - 6 * s + math.sin(rad) * d2 * s
            draw.line([(x1, y1), (x2, y2)], fill=w_white, width=max(3, int(5 * s)))

    elif icon_type == "handshake":
        # Clasped handshake with cuffs & fingers (matches t=12.30s & t=20.60s)
        navy_cut = (12, 36, 118, 255)
        # Left cuff (angled down-right)
        cuff_l = [
            (cx - 56 * s, cy - 8 * s),
            (cx - 38 * s, cy - 28 * s),
            (cx - 22 * s, cy - 12 * s),
            (cx - 40 * s, cy + 10 * s),
        ]
        draw.polygon(cuff_l, fill=w_white)
        # Right cuff (angled down-left)
        cuff_r = [
            (cx + 56 * s, cy - 8 * s),
            (cx + 38 * s, cy - 28 * s),
            (cx + 22 * s, cy - 12 * s),
            (cx + 40 * s, cy + 10 * s),
        ]
        draw.polygon(cuff_r, fill=w_white)
        # Central clasped palms
        palm = [
            (cx - 32 * s, cy - 8 * s),
            (cx - 6 * s, cy - 24 * s),
            (cx + 32 * s, cy - 8 * s),
            (cx + 26 * s, cy + 18 * s),
            (cx + 2 * s, cy + 30 * s),
            (cx - 26 * s, cy + 18 * s),
        ]
        draw.polygon(palm, fill=w_white)
        # Interlocking finger separator lines in navy
        for i in range(-1, 3):
            fx = cx + i * 9 * s
            fy = cy + 12 * s + abs(i) * 2 * s
            draw.line(
                [(fx - 6 * s, fy + 10 * s), (fx + 5 * s, fy - 4 * s)],
                fill=navy_cut,
                width=max(2, int(4 * s)),
            )
        # Top thumb fold line in navy
        draw.line(
            [(cx - 14 * s, cy - 6 * s), (cx + 4 * s, cy - 18 * s), (cx + 18 * s, cy - 4 * s)],
            fill=navy_cut,
            width=max(2, int(4.5 * s)),
        )

    elif icon_type == "flame":
        # Stylized sacrifice/dedication flame + core
        pts_outer = [
            (cx, cy - 46 * s),
            (cx + 24 * s, cy - 14 * s),
            (cx + 34 * s, cy + 12 * s),
            (cx + 20 * s, cy + 38 * s),
            (cx, cy + 44 * s),
            (cx - 20 * s, cy + 38 * s),
            (cx - 34 * s, cy + 12 * s),
            (cx - 22 * s, cy - 16 * s),
        ]
        draw.polygon(pts_outer, fill=w_white)
        pts_inner = [
            (cx, cy - 12 * s),
            (cx + 12 * s, cy + 8 * s),
            (cx + 8 * s, cy + 28 * s),
            (cx, cy + 32 * s),
            (cx - 8 * s, cy + 28 * s),
            (cx - 12 * s, cy + 8 * s),
        ]
        draw.polygon(pts_inner, fill=(18, 56, 175, 255))

    elif icon_type == "key":
        # Ownership key icon (angled at -35 deg)
        draw.ellipse(
            [cx - 42 * s, cy - 36 * s, cx - 2 * s, cy + 4 * s],
            fill=w_white,
        )
        draw.ellipse(
            [cx - 30 * s, cy - 24 * s, cx - 14 * s, cy - 8 * s],
            fill=(14, 42, 136, 255),
        )
        # Key shaft + teeth
        shaft = [
            (cx - 6 * s, cy - 12 * s),
            (cx + 40 * s, cy + 24 * s),
            (cx + 32 * s, cy + 34 * s),
            (cx - 14 * s, cy - 2 * s),
        ]
        draw.polygon(shaft, fill=w_white)
        tooth1 = [
            (cx + 16 * s, cy + 18 * s),
            (cx + 24 * s, cy + 24 * s),
            (cx + 14 * s, cy + 36 * s),
            (cx + 6 * s, cy + 30 * s),
        ]
        tooth2 = [
            (cx + 28 * s, cy + 28 * s),
            (cx + 36 * s, cy + 34 * s),
            (cx + 26 * s, cy + 46 * s),
            (cx + 18 * s, cy + 40 * s),
        ]
        draw.polygon(tooth1, fill=w_white)
        draw.polygon(tooth2, fill=w_white)

    elif icon_type in ("store_a", "store_b"):
        # Storefront awning + base + A/B label
        draw.rounded_rectangle(
            [cx - 36 * s, cy - 8 * s, cx + 36 * s, cy + 36 * s],
            radius=int(6 * s),
            fill=w_white,
        )
        awning = [
            (cx - 44 * s, cy - 8 * s),
            (cx - 30 * s, cy - 32 * s),
            (cx + 30 * s, cy - 32 * s),
            (cx + 44 * s, cy - 8 * s),
        ]
        draw.polygon(awning, fill=w_white)
        draw.line(
            [(cx - 44 * s, cy - 8 * s), (cx + 44 * s, cy - 8 * s)],
            fill=(14, 38, 120, 255),
            width=max(2, int(4 * s)),
        )
        f_lbl = get_font(F_MONT_BLACK, int(34 * s))
        lbl = "A" if icon_type == "store_a" else "B"
        col = (210, 28, 56, 255) if icon_type == "store_a" else (22, 68, 210, 255)
        bb = draw.textbbox((0, 0), lbl, font=f_lbl)
        draw.text(
            (cx - (bb[2] - bb[0]) / 2 - bb[0], cy + 12 * s - (bb[3] - bb[1]) / 2 - bb[1]),
            lbl,
            font=f_lbl,
            fill=col,
        )
        if icon_type == "store_a":
            # Diagonal slash indicating closed
            draw.line(
                [(cx - 44 * s, cy + 38 * s), (cx + 44 * s, cy - 38 * s)],
                fill=(255, 48, 76, 255),
                width=max(4, int(7 * s)),
            )

    elif icon_type == "coin":
        # Bold $ symbol inside inner ring
        draw.ellipse(
            [cx - 44 * s, cy - 44 * s, cx + 44 * s, cy + 44 * s],
            outline=w_white,
            width=max(3, int(6 * s)),
        )
        f_dlr = get_font(F_MONT_BLACK, int(56 * s))
        bb = draw.textbbox((0, 0), "$", font=f_dlr)
        draw.text(
            (cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
            "$",
            font=f_dlr,
            fill=w_white,
        )


def get_3d_badge_img(icon_type, radius=105, tint="blue"):
    """
    Pre-renders a 3D glowing circular badge matching `reference 7.mp4` (`t=12.30s`, `18.80s`, `20.60s`).
    """
    key = (icon_type, int(radius), tint)
    if key in _BADGE_CACHE:
        return _BADGE_CACHE[key]

    pad = int(radius * 0.65)
    sz = (radius + pad) * 2
    cx = cy = radius + pad

    yy, xx = np.mgrid[0:sz, 0:sz].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    dist = np.sqrt(dx * dx + dy * dy)
    norm_r = dist / float(radius)

    rgba = np.zeros((sz, sz, 4), dtype=np.uint8)

    # 1. Soft outer neon aura
    outer_glow = np.exp(-np.maximum(0.0, norm_r - 0.85) * 3.4) * (norm_r > 0.85)
    # 2. Interior 3D sphere/disc gradient (deep navy center -> vibrant electric cobalt rim)
    inside = norm_r <= 1.0
    edge_aa = np.clip((1.015 - norm_r) / 0.03, 0.0, 1.0)

    # Off-center highlight towards top-left and bottom-right inner rim
    rim_factor = np.clip(norm_r ** 2.2, 0.0, 1.0)
    top_spec = np.exp(-(((dx + radius * 0.28) / (radius * 0.55)) ** 2 + ((dy + radius * 0.32) / (radius * 0.45)) ** 2))

    if tint == "crimson":
        r_in = 22 + rim_factor * 165 + top_spec * 45
        g_in = 4 + rim_factor * 18 + top_spec * 20
        b_in = 14 + rim_factor * 42 + top_spec * 30
        gr, gg, gb = 255, 38, 72
    else:
        r_in = 5 + rim_factor * 26 + top_spec * 32
        g_in = 16 + rim_factor * 68 + top_spec * 65
        b_in = 58 + rim_factor * 172 + top_spec * 48
        gr, gg, gb = 38, 102, 255

    # Combine outer glow + inside disc
    alpha_in = edge_aa
    alpha_out = np.clip(outer_glow * 0.62, 0.0, 1.0)
    tot_a = np.clip(alpha_in + alpha_out * (1.0 - alpha_in), 0.0, 1.0)

    w_in = np.where(tot_a > 1e-4, alpha_in / np.maximum(tot_a, 1e-4), 0.0)
    rgba[:, :, 0] = np.clip(w_in * r_in + (1.0 - w_in) * gr, 0, 255).astype(np.uint8)
    rgba[:, :, 1] = np.clip(w_in * g_in + (1.0 - w_in) * gg, 0, 255).astype(np.uint8)
    rgba[:, :, 2] = np.clip(w_in * b_in + (1.0 - w_in) * gb, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(tot_a * 255.0, 0, 255).astype(np.uint8)

    im = Image.fromarray(rgba)
    draw = ImageDraw.Draw(im)

    # Crisp specular 3px border ring
    rim_col = (255, 92, 118, 235) if tint == "crimson" else (82, 148, 255, 240)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=rim_col,
        width=max(3, int(radius * 0.032)),
    )
    # Subtle inner glass ring
    inner_col = (255, 160, 180, 90) if tint == "crimson" else (140, 195, 255, 95)
    r_in_ring = int(radius * 0.93)
    draw.ellipse(
        [cx - r_in_ring, cy - r_in_ring, cx + r_in_ring, cy + r_in_ring],
        outline=inner_col,
        width=max(1, int(radius * 0.015)),
    )

    # Draw crisp white vector icon on a separate layer with slight drop shadow
    ic_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    ic_draw = ImageDraw.Draw(ic_layer)
    draw_icon_vector(ic_draw, icon_type, cx, cy, radius)

    ic_shadow = ic_layer.filter(ImageFilter.GaussianBlur(radius=max(3, int(radius * 0.04))))
    sh_arr = np.asarray(ic_shadow).copy()
    sh_arr[:, :, 0] = 4
    sh_arr[:, :, 1] = 12
    sh_arr[:, :, 2] = 42
    sh_arr[:, :, 3] = (sh_arr[:, :, 3].astype(np.float32) * 0.65).astype(np.uint8)
    im = Image.alpha_composite(im, Image.fromarray(sh_arr))
    im = Image.alpha_composite(im, ic_layer)

    _BADGE_CACHE[key] = im
    return im


def place_badge(frame_rgb, icon_type, cx, cy, radius, t, t_appear, t_end, tint="blue"):
    if t < t_appear or t > t_end:
        return
    p_in = ease_out_back(clamp((t - t_appear) / 0.26), s=1.5)
    p_out = clamp((t_end - t) / 0.18) if t > t_end - 0.18 else 1.0
    scale = max(0.05, p_in * (0.85 + 0.15 * p_out))
    # Gentle floating bob
    bob_y = math.sin((t - t_appear) * 3.2) * 5.0

    base_im = get_3d_badge_img(icon_type, radius=radius, tint=tint)
    if abs(scale - 1.0) > 0.015:
        nw = max(4, int(base_im.width * scale))
        nh = max(4, int(base_im.height * scale))
        im = base_im.resize((nw, nh), Image.Resampling.BILINEAR)
    else:
        im = base_im

    if p_out < 0.99:
        arr = np.asarray(im).copy()
        arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * p_out).astype(np.uint8)
        im = Image.fromarray(arr)

    x0 = int(cx - im.width / 2)
    y0 = int(cy + bob_y - im.height / 2)
    alpha_composite_roi(frame_rgb, im, x0, y0)


# ---------------------------------------------------------------------------
# Cutaway #1 (`4.80s - 8.36s`): 3D Dark Laptop with `BizBuySell` Window
# (Directly inspired by `t=5.00s` & `t=6.80s` `Chat Box` Laptop in `reference 7.mp4`)
# ---------------------------------------------------------------------------
LAPTOP_CARDS = [
    {
        "appear": 4.95,
        "name": "Sarah T.",
        "age": "11m",
        "msg1": "Listed at $680K — 80% of listings here",
        "msg2": "never sell. Still waiting on a buyer.",
        "badge": "DID NOT SELL",
        "skeleton": False,
    },
    {
        "appear": 5.58,
        "name": "Mark J.",
        "age": "1y",
        "msg1": "Any update on offers? Haven't",
        "msg2": "heard back from a single buyer yet.",
        "badge": "DID NOT SELL",
        "skeleton": False,
    },
    {
        "appear": 6.20,
        "name": "Daniel R.",
        "age": "14m",
        "msg1": "I listed the business 14 months ago.",
        "msg2": "Zero qualified buyers — forced to close.",
        "badge": "CLOSING",
        "skeleton": False,
    },
    {
        "appear": 6.82,
        "name": "Priya K.",
        "age": "18m",
        "msg1": "80% listed did not sell. Preparing",
        "msg2": "to shut down operations next month.",
        "badge": "UNSOLD",
        "skeleton": False,
    },
    {
        "appear": 7.35,
        "name": "Ahmed S.",
        "age": "2y",
        "msg1": "",
        "msg2": "",
        "badge": "",
        "skeleton": True,
    },
]


def render_laptop_cutaway(t, midnight_bg):
    """
    Renders the 3D dark MacBook Pro cutaway (`4.80s - 8.36s`) matching `t=5.00s` & `t=6.80s`
    of `reference 7.mp4`:
    - Smooth camera push-in (`scale 0.90 -> 1.07`) and gentle left-to-right drift
    - Dark matte aluminum bezel + perspective keyboard deck & trackpad at bottom
    - `BizBuySell` header (`BizBuy` Light + `Sell` Bold) + `80% UNSOLD` pill
    - Stacking glassmorphic listing cards with circular user avatars, timestamps, and live typing
    - Right-hand detail pane with `80%` ring visual and bottom blue send-icon bar (`[o] Type message...`)
    """
    dur = 8.36 - 4.80
    u = clamp((t - 4.80) / dur)
    e_u = ease_out_cubic(u)

    # Render onto a slightly larger virtual canvas then crop/zoom for smooth 3D camera push-in
    canvas = Image.fromarray(midnight_bg.copy()).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Camera pan & zoom parameters matching t=5.00s -> t=6.80s in reference 7.mp4
    cam_x = int(40 - e_u * 65)
    cam_y = int(45 - e_u * 55)

    # Outer laptop lid (dark matte charcoal with subtle specular edge)
    lx0, ly0 = 165 + cam_x, 220 + cam_y
    lx1, ly1 = 1260 + cam_x, 1525 + cam_y

    # Soft blue backlight behind top-left of laptop lid
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse([lx0 - 110, ly0 - 90, lx0 + 520, ly0 + 480], fill=(24, 72, 235, 78))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=65))
    canvas = Image.alpha_composite(canvas, glow_layer)
    draw = ImageDraw.Draw(canvas)

    # Lid body & metallic bezel
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=38, fill=(10, 12, 16, 255), outline=(44, 50, 66, 255), width=3)
    # Inner screen glass area
    sx0, sy0 = lx0 + 28, ly0 + 34
    sx1, sy1 = lx1 - 28, ly1 - 36
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=18, fill=(11, 13, 18, 255))

    # Top header inside screen: "BizBuySell" (styled just like "Chat Box" in reference 7.mp4)
    f_light = get_font(F_MONT_LIGHT, 50)
    f_bold = get_font(F_MONT_BOLD, 50)
    hx, hy = sx0 + 48, sy0 + 42
    draw.text((hx, hy), "BizBuy", font=f_light, fill=(225, 230, 242, 255))
    w_part1 = draw.textbbox((0, 0), "BizBuy", font=f_light)[2]
    draw.text((hx + w_part1 + 2, hy), "Sell", font=f_bold, fill=(255, 255, 255, 255))
    w_part2 = draw.textbbox((0, 0), "Sell", font=f_bold)[2]

    # "80% DID NOT SELL" alert pill next to header
    px0 = hx + w_part1 + w_part2 + 28
    py0 = hy + 10
    draw.rounded_rectangle([px0, py0, px0 + 246, py0 + 42], radius=21, fill=(42, 14, 24, 240), outline=(255, 48, 78, 220), width=2)
    f_pill = get_font(F_INTER_BOLD, 20)
    draw.text((px0 + 20, py0 + 9), "80% DID NOT SELL", font=f_pill, fill=(255, 78, 104, 255))

    # Right-hand detail pane (matching the right column in t=5.00s & t=6.80s of reference 7.mp4)
    rx0 = sx0 + 625
    ry0 = sy0 + 125
    rx1 = sx1 - 36
    ry1 = sy1 - 115
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=22, fill=(22, 25, 34, 255), outline=(42, 48, 64, 255), width=2)

    # Inside right pane: 80% Unsold Study visual
    f_stat_big = get_font(F_MONT_BLACK, 64)
    f_stat_sub = get_font(F_INTER_MED, 21)
    draw.text((rx0 + 42, ry0 + 44), "80%", font=f_stat_big, fill=(37, 88, 255, 255))
    draw.text((rx0 + 42, ry0 + 122), "of listed businesses", font=f_stat_sub, fill=(190, 198, 214, 255))
    draw.text((rx0 + 42, ry0 + 150), "did not sell", font=f_stat_sub, fill=(255, 64, 92, 255))

    # Bottom right message input bar with blue circular icon (exact match to t=5.00s & t=6.80s)
    ib_y0 = ry1 + 20
    ib_y1 = sy1 - 24
    draw.rounded_rectangle([rx0, ib_y0, rx1, ib_y1], radius=20, fill=(22, 25, 34, 255), outline=(42, 48, 64, 255), width=2)
    # Blue icon button
    draw.rounded_rectangle([rx0 + 16, ib_y0 + 14, rx0 + 60, ib_y0 + 58], radius=12, fill=(45, 92, 255, 255))
    draw.ellipse([rx0 + 27, ib_y0 + 25, rx0 + 49, ib_y0 + 47], outline=(255, 255, 255, 255), width=3)
    draw.text((rx0 + 76, ib_y0 + 24), "Type message...", font=get_font(F_INTER_REG, 21), fill=(130, 138, 158, 255))

    # Left column: Stacking glassmorphic notification cards
    f_name = get_font(F_INTER_BOLD, 21)
    f_age = get_font(F_INTER_REG, 19)
    f_msg = get_font(F_INTER_REG, 19)
    f_b = get_font(F_INTER_BOLD, 15)

    cx0 = sx0 + 48
    cx1 = sx0 + 598
    cy_base = sy0 + 125
    card_h = 148
    card_gap = 20

    for idx, card in enumerate(LAPTOP_CARDS):
        if t < card["appear"]:
            continue
        dt = t - card["appear"]
        p_in = ease_out_back(clamp(dt / 0.28), s=1.25)
        alpha_c = int(clamp(dt / 0.18) * (150 if card["skeleton"] else 255))

        cy0 = cy_base + idx * (card_h + card_gap) + int((1.0 - p_in) * 28)
        cy1 = cy0 + card_h

        c_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(c_layer)

        bg_col = (22, 25, 34, alpha_c) if card["skeleton"] else (28, 32, 43, alpha_c)
        bd_col = (44, 50, 66, alpha_c) if card["skeleton"] else (62, 70, 92, alpha_c)
        cd.rounded_rectangle([cx0, cy0, cx1, cy1], radius=20, fill=bg_col, outline=bd_col, width=2)

        # Circular avatar on left (matching the white/grey circular portrait avatars in t=6.80s)
        avx, avy, avr = cx0 + 54, cy0 + card_h // 2, 33
        if card["skeleton"]:
            cd.ellipse([avx - avr, avy - avr, avx + avr, avy + avr], fill=(60, 66, 82, alpha_c))
        else:
            cd.ellipse([avx - avr, avy - avr, avx + avr, avy + avr], fill=(232, 236, 245, alpha_c))
            # Head & shoulders silhouette inside avatar
            cd.ellipse([avx - 11, avy - 18, avx + 11, avy + 4], fill=(52, 58, 74, alpha_c))
            cd.pieslice([avx - 22, avy + 6, avx + 22, avy + 38], 180, 360, fill=(52, 58, 74, alpha_c))

        # Name + dot + timestamp
        tx = cx0 + 106
        ty = cy0 + 24
        cd.text((tx, ty), card["name"], font=f_name, fill=(255, 255, 255, alpha_c))
        nw = cd.textbbox((0, 0), card["name"], font=f_name)[2]
        cd.text((tx + nw + 10, ty + 1), f"•  {card['age']}", font=f_age, fill=(150, 160, 182, alpha_c))

        if card["skeleton"]:
            # Skeleton placeholder bars (just like Ahmed S. at bottom of t=6.80s!)
            cd.rounded_rectangle([tx, ty + 38, tx + 210, ty + 54], radius=7, fill=(58, 64, 80, alpha_c))
        else:
            # Badge on top-right of card
            bx1 = cx1 - 22
            bx0 = bx1 - 128
            by0 = cy0 + 22
            cd.rounded_rectangle([bx0, by0, bx1, by0 + 28], radius=14, fill=(52, 16, 26, alpha_c), outline=(255, 58, 88, alpha_c), width=1)
            bb = cd.textbbox((0, 0), card["badge"], font=f_b)
            cd.text((bx0 + (128 - (bb[2] - bb[0])) / 2, by0 + 5), card["badge"], font=f_b, fill=(255, 92, 118, alpha_c))

            # Typewriter message lines
            char_progress = int(clamp((dt - 0.05) / 0.48) * (len(card["msg1"]) + len(card["msg2"])))
            m1 = card["msg1"][: min(len(card["msg1"]), char_progress)]
            m2 = card["msg2"][: max(0, char_progress - len(card["msg1"]))]
            cd.text((tx, ty + 36), m1, font=f_msg, fill=(215, 222, 235, alpha_c))
            if m2:
                cd.text((tx, ty + 64), m2, font=f_msg, fill=(182, 190, 208, alpha_c))

        canvas = Image.alpha_composite(canvas, c_layer)

    draw = ImageDraw.Draw(canvas)

    # 3D Laptop Base / Keyboard Deck in perspective below the screen (matching t=5.00s & t=6.80s)
    ky0 = ly1 - 4
    ky1 = ky0 + 245
    deck_pts = [
        (lx0 - 10, ky0),
        (lx1 + 10, ky0),
        (lx1 + 135, ky1),
        (lx0 - 135, ky1),
    ]
    draw.polygon(deck_pts, fill=(38, 43, 54, 255))
    # Top hinge groove
    draw.polygon(
        [(lx0 + 40, ky0), (lx1 - 40, ky0), (lx1 - 30, ky0 + 18), (lx0 + 30, ky0 + 18)],
        fill=(14, 16, 22, 255),
    )
    # Perspective keyboard well
    kw_pts = [
        (lx0 + 30, ky0 + 28),
        (lx1 - 30, ky0 + 28),
        (lx1 + 45, ky0 + 168),
        (lx0 - 45, ky0 + 168),
    ]
    draw.polygon(kw_pts, fill=(12, 14, 19, 255), outline=(58, 64, 78, 255))

    # Draw rows of 3D perspective keys
    for r_idx in range(5):
        fr0 = r_idx / 5.0
        fr1 = (r_idx + 0.78) / 5.0
        ry_a = (ky0 + 34) + fr0 * 128
        ry_b = (ky0 + 34) + fr1 * 128
        xl_a = (lx0 + 38) - fr0 * 68
        xr_a = (lx1 - 38) + fr0 * 68
        xl_b = (lx0 + 38) - fr1 * 68
        xr_b = (lx1 - 38) + fr1 * 68
        n_keys = 12
        for k_idx in range(n_keys):
            u0 = (k_idx + 0.08) / n_keys
            u1 = (k_idx + 0.88) / n_keys
            k_pts = [
                (xl_a + u0 * (xr_a - xl_a), ry_a),
                (xl_a + u1 * (xr_a - xl_a), ry_a),
                (xl_b + u1 * (xr_b - xl_b), ry_b),
                (xl_b + u0 * (xr_b - xl_b), ry_b),
            ]
            draw.polygon(k_pts, fill=(24, 28, 36, 255), outline=(48, 54, 68, 200))

    # Trackpad at bottom center of deck
    tp_pts = [
        (lx0 + 310, ky0 + 178),
        (lx0 + 680, ky0 + 178),
        (lx0 + 710, ky1 - 8),
        (lx0 + 280, ky1 - 8),
    ]
    draw.polygon(tp_pts, fill=(30, 35, 45, 255), outline=(56, 62, 76, 255))

    # Subtle camera zoom from 0.94 to 1.05
    zoom = 0.95 + 0.09 * e_u
    cw = int(W / zoom)
    ch = int(H / zoom)
    x_crop = (W - cw) // 2
    y_crop = (H - ch) // 2
    cropped = canvas.crop((x_crop, y_crop, x_crop + cw, y_crop + ch)).resize((W, H), Image.Resampling.BILINEAR)
    return np.asarray(cropped.convert("RGB"))


# ---------------------------------------------------------------------------
# Cutaway #2 (`28.28s - 33.48s`): 3D Blue Circle Handshake Shatter -> Crimson Vignette
# (Directly inspired by `t=12.30s`, `t=13.10s`, `t=14.80s` in `reference 7.mp4`)
# ---------------------------------------------------------------------------
def generate_shatter_shards(radius=198, n_rings=5, seed=77):
    """Generates ~125 3D faceted polygonal shards from a circular badge."""
    rng = np.random.default_rng(seed)
    shards = []
    ring_radii = np.linspace(0, radius, n_rings + 1)
    for r_i in range(n_rings):
        r0, r1 = ring_radii[r_i], ring_radii[r_i + 1]
        n_sec = 10 + r_i * 7
        angles = np.linspace(0, 2 * math.pi, n_sec + 1) + rng.uniform(-0.08, 0.08, n_sec + 1)
        angles[-1] = angles[0] + 2 * math.pi
        for s_i in range(n_sec):
            a0, a1 = angles[s_i], angles[s_i + 1]
            am = 0.5 * (a0 + a1)
            rm = 0.5 * (r0 + r1)
            cx = math.cos(am) * rm
            cy = math.sin(am) * rm
            # Local polygon vertices relative to shard center
            pts = []
            for rr, aa in [(r0, a0), (r1, a0), (r1, a1), (r0, a1)]:
                jit_r = rr + rng.uniform(-5, 5) if rr > 0 else 0
                jit_a = aa + rng.uniform(-0.04, 0.04)
                px = math.cos(jit_a) * jit_r - cx
                py = math.sin(jit_a) * jit_r - cy
                pts.append((px, py))

            # Radial outward velocity + gravity + 3D tumble speeds
            speed = rng.uniform(220.0, 680.0) * (0.45 + 0.75 * (rm / radius))
            v_ang = am + rng.uniform(-0.32, 0.32)
            vx = math.cos(v_ang) * speed
            vy = math.sin(v_ang) * speed - rng.uniform(40.0, 180.0)
            omega_z = rng.uniform(-6.5, 6.5)
            omega_x = rng.uniform(3.5, 9.5)
            phase_x = rng.uniform(0, math.pi * 2)
            is_white = rng.random() < 0.58  # Mix of bright white/silver & cobalt shards like t=13.10s
            shards.append({
                "cx": cx,
                "cy": cy,
                "pts": pts,
                "vx": vx,
                "vy": vy,
                "omega_z": omega_z,
                "omega_x": omega_x,
                "phase_x": phase_x,
                "is_white": is_white,
            })
    return shards


SHARDS_DATA = generate_shatter_shards(radius=198)


def render_shatter_and_crimson_cutaway(
    t,
    t_start,
    t_shatter,
    t_crimson,
    t_end,
    icon_type,
    crimson_lines,
    midnight_bg,
    crimson_bg,
    pre_lockup=None,
):
    """
    Renders the 3-phase sequence from `reference 7.mp4` (`12.00s - 15.50s`):
    - Phase A (`t_start .. t_shatter`): 3D Glowing Blue Circular Badge scales in & cracks
    - Phase B (`t_shatter .. t_crimson + 0.35`): Explosive 3D faceted polygon shatter (125 white & blue 3D shards)
    - Phase C (`t_crimson .. t_end`): Deep crimson-red radial vignette + 4-line stacked reveal
    """
    # Background cross-fade from midnight_bg to crimson_bg around `t_crimson`
    w_crim = clamp((t - (t_crimson - 0.18)) / 0.42)
    if w_crim <= 0.001:
        frame = midnight_bg.copy()
    elif w_crim >= 0.999:
        frame = crimson_bg.copy()
    else:
        frame = np.clip(
            midnight_bg.astype(np.float32) * (1.0 - w_crim) + crimson_bg.astype(np.float32) * w_crim,
            0,
            255,
        ).astype(np.uint8)

    cx, cy = W // 2, H // 2 if pre_lockup is None else int(H * 0.62)

    # Optional pre-lockup above badge (used in Cutaway #3 at 44.12-45.95s)
    if pre_lockup is not None and t < t_crimson:
        draw_stacked_lockup(frame, t, pre_lockup, anchor_x=230, anchor_y=640, align="left", t_end=t_crimson)

    # Phase A: Intact 3D Blue Circular Badge (`t_start .. t_shatter`)
    if t < t_shatter:
        dt = t - t_start
        p_in = ease_out_back(clamp(dt / 0.32), s=1.35)
        rad = 198 if pre_lockup is None else 145
        badge_im = get_3d_badge_img(icon_type, radius=rad, tint="blue")
        sc = max(0.1, p_in)
        if abs(sc - 1.0) > 0.015:
            nw, nh = int(badge_im.width * sc), int(badge_im.height * sc)
            b_use = badge_im.resize((nw, nh), Image.Resampling.BILINEAR)
        else:
            b_use = badge_im

        # Draw fracture crack lines in final 0.18s before shatter
        if t > t_shatter - 0.18:
            b_use = b_use.copy()
            bd = ImageDraw.Draw(b_use)
            bcx, bcy = b_use.width // 2, b_use.height // 2
            crack_p = clamp((t - (t_shatter - 0.18)) / 0.18)
            for ang in [18, 72, 134, 195, 252, 310]:
                r_len = rad * 0.95 * crack_p
                rad_a = math.radians(ang)
                mx = bcx + math.cos(rad_a + 0.12) * (r_len * 0.5)
                my = bcy + math.sin(rad_a + 0.12) * (r_len * 0.5)
                ex = bcx + math.cos(rad_a) * r_len
                ey = bcy + math.sin(rad_a) * r_len
                bd.line([(bcx, bcy), (mx, my), (ex, ey)], fill=(210, 235, 255, 255), width=4)

        alpha_composite_roi(frame, b_use, int(cx - b_use.width / 2), int(cy - b_use.height / 2))

    # Phase B: 3D Polygon Shatter (`t_shatter .. t_crimson + 0.38`)
    elif t < t_crimson + 0.38:
        st = t - t_shatter
        shatter_dur = (t_crimson + 0.38) - t_shatter
        fade_s = clamp(1.0 - (st / shatter_dur) ** 1.65)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        grav = 540.0
        for sh in SHARDS_DATA:
            sx = cx + sh["cx"] + sh["vx"] * st
            sy = cy + sh["cy"] + sh["vy"] * st + 0.5 * grav * (st ** 2)
            rot_z = sh["omega_z"] * st
            tilt_x = math.cos(sh["phase_x"] + sh["omega_x"] * st)
            cz, sz_r = math.cos(rot_z), math.sin(rot_z)

            poly_front = []
            poly_back = []
            thickness = 9.0
            for px, py in sh["pts"]:
                rx = px * cz - py * sz_r
                ry = (px * sz_r + py * cz) * tilt_x
                poly_front.append((sx + rx, sy + ry))
                poly_back.append((sx + rx + thickness * 0.6, sy + ry + thickness))

            a_val = int(255 * fade_s)
            if a_val <= 4:
                continue
            # 3D extruded side/back in deep cobalt blue
            od.polygon(poly_back, fill=(24, 68, 195, a_val))
            # Front faceted face in bright white/silver or electric blue (matching t=13.10s!)
            if sh["is_white"]:
                lum = int(215 + 40 * abs(tilt_x))
                od.polygon(poly_front, fill=(lum, lum, min(255, lum + 10), a_val))
            else:
                od.polygon(poly_front, fill=(48, 112, 255, a_val))

        alpha_composite_roi(frame, overlay, 0, 0)

    # Phase C: 4-Line Stacked Crimson Reveal (`t >= t_crimson`)
    if t >= t_crimson - 0.05:
        draw_stacked_lockup(frame, t, crimson_lines, anchor_x=235, anchor_y=800, align="left", t_end=t_end)

    return frame


# ---------------------------------------------------------------------------
# Camera Framing & Ken Burns Schedule for Talking-Head Shots
# ---------------------------------------------------------------------------
def get_camera_crop(frame_rgb, t):
    """
    Applies multi-scale framing switches synchronized to the raw jump cuts in `videobrut 7.mp4`
    (`8.30s`, `11.59s`, `14.64s`, `19.95s`, `23.57s`, `33.48s`, `38.46s`, `41.75s`, `48.05s`)
    plus subtle Ken Burns drift, mirroring the multi-camera cuts of `reference 7.mp4`.
    """
    if t < 4.80:
        u = t / 4.80
        zoom = 1.00 + 0.03 * u
        cx, cy = 0.50, 0.48
    elif t < 11.58:
        # Jump cut at 8.30s -> Medium 1.15x
        u = (t - 8.36) / (11.58 - 8.36)
        zoom = 1.15 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.44
    elif t < 14.64:
        # Jump cut at 11.59s -> Wide 1.02x
        u = (t - 11.58) / (14.64 - 11.58)
        zoom = 1.02 + 0.025 * clamp(u)
        cx, cy = 0.50, 0.48
    elif t < 19.95:
        # Clause cut at 14.64s -> Close-Up 1.20x
        u = (t - 14.64) / (19.95 - 14.64)
        zoom = 1.20 - 0.02 * clamp(u)
        cx, cy = 0.50, 0.43
    elif t < 23.57:
        # Clause cut at 19.95s -> Medium 1.10x
        u = (t - 19.95) / (23.57 - 19.95)
        zoom = 1.10 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.46
    elif t < 28.28:
        # Jump cut at 23.57s -> Tighter side-biased framing 1.18x
        u = (t - 23.57) / (28.28 - 23.57)
        zoom = 1.18 + 0.025 * clamp(u)
        cx, cy = 0.48, 0.43
    elif t < 38.46:
        # Return from Cutaway #2 at 33.48s -> Medium 1.15x
        u = (t - 33.48) / (38.46 - 33.48)
        zoom = 1.15 - 0.02 * clamp(u)
        cx, cy = 0.50, 0.44
    elif t < 41.75:
        # Jump cut at 38.46s -> Wide 1.01x
        u = (t - 38.46) / (41.75 - 38.46)
        zoom = 1.01 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.48
    elif t < 44.12:
        # Jump cut at 41.75s -> Close-Up 1.19x
        u = (t - 41.75) / (44.12 - 41.75)
        zoom = 1.19 + 0.02 * clamp(u)
        cx, cy = 0.50, 0.43
    elif t < 53.85:
        # Return from Cutaway #3 at 48.05s -> Medium 1.13x
        u = (t - 48.05) / (53.85 - 48.05)
        zoom = 1.13 + 0.02 * clamp(u)
        cx, cy = 0.50, 0.45
    else:
        # Final CTA lockup (53.85s - 56.89s) -> Clean Wide-Medium pull-back
        u = (t - 53.85) / (56.89 - 53.85)
        zoom = 1.06 - 0.04 * clamp(u)
        cx, cy = 0.50, 0.47

    sh, sw, _ = frame_rgb.shape
    cw = sw / zoom
    ch = sh / zoom
    x0 = int(clamp(cx * sw - cw / 2, 0, sw - cw))
    y0 = int(clamp(cy * sh - ch / 2, 0, sh - ch))
    crop = frame_rgb[y0 : y0 + int(ch), x0 : x0 + int(cw)]
    return np.asarray(Image.fromarray(crop).resize((W, H), Image.Resampling.BILINEAR))


# ---------------------------------------------------------------------------
# Master Overlay & Lockup Definitions Across All 9 Beats
# ---------------------------------------------------------------------------
# Multi-tier lockups on talking-head segments:
TALKING_LOCKUPS = [
    # 1. Opening Hook (0.00 - 2.04s): "BizBuySell / has done / studies" (matches t=0.60s in reference 7.mp4)
    {
        "t_start": 0.00,
        "t_end": 2.04,
        "anchor_x": 165,
        "anchor_y": 1030,
        "align": "left",
        "lines": [
            (0.00, "BizBuySell", F_MONT_BOLD, 56, C_WHITE, None, 0, 0),
            (0.90, "has done", F_MONT_BLACK, 88, C_SILVER, None, 0, 56),
            (1.48, "studies", F_DAFOE, 118, C_BLUE_BRIGHT, C_BLUE, 12, 122),
        ],
    },
    # 2. Beat 4A (12.94 - 14.58s): "how to / buy / businesses" (matches t=1.80s in reference 7.mp4)
    {
        "t_start": 12.94,
        "t_end": 14.58,
        "anchor_x": 195,
        "anchor_y": 1020,
        "align": "left",
        "lines": [
            (12.94, "how to", F_MONT_BOLD, 46, C_WHITE, None, 32, 0),
            (13.50, "buy", F_MONT_BLACK, 92, C_WHITE, None, 0, 44),
            (13.86, "businesses", F_DAFOE, 114, C_BLUE_BRIGHT, C_BLUE, 8, 116),
        ],
    },
    # 3. Beat 5A (19.96 - 22.08s): "a lot of businesses / are going to / close"
    {
        "t_start": 19.96,
        "t_end": 22.08,
        "anchor_x": 180,
        "anchor_y": 1025,
        "align": "left",
        "lines": [
            (19.96, "a lot of businesses", F_MONT_BOLD, 44, C_WHITE, None, 0, 0),
            (20.62, "are going to", F_MONT_BLACK, 78, C_SILVER, None, 0, 48),
            (21.14, "close", F_DAFOE, 122, C_CRIMSON, C_CRIMSON, 18, 108),
        ],
    },
    # 4. Beat 7A (33.50 - 36.46s): "Buying businesses / Builds A Real / Asset" (matches t=16.60s "We built the / Revenue / Rhythm")
    {
        "t_start": 33.50,
        "t_end": 36.46,
        "anchor_x": 175,
        "anchor_y": 1030,
        "align": "left",
        "lines": [
            (33.50, "Buying businesses", F_MONT_BOLD, 42, C_WHITE, None, 0, 0),
            (34.84, "Builds A Real", F_MONT_BLACK, 80, C_WHITE, None, 0, 46),
            (35.80, "Asset", F_DAFOE, 122, C_BLUE_BRIGHT, C_BLUE, 18, 106),
        ],
    },
    # 5. Beat 8A (43.36 - 44.12s): "to make / money"
    {
        "t_start": 43.36,
        "t_end": 44.12,
        "anchor_x": 540,
        "anchor_y": 1045,
        "align": "center",
        "lines": [
            (43.36, "to make", F_MONT_BLACK, 82, C_WHITE, None, 0, 0),
            (43.62, "money", F_DAFOE, 118, C_BLUE_BRIGHT, C_BLUE, 0, 62),
        ],
    },
    # 6. Beat 9A (49.50 - 51.82s): "the right / Intentions / buy them" (matches t=24.40s "Revenue Leak / Detection / session")
    {
        "t_start": 49.50,
        "t_end": 51.82,
        "anchor_x": 180,
        "anchor_y": 1025,
        "align": "left",
        "lines": [
            (49.50, "the right", F_MONT_BOLD, 44, C_WHITE, None, 0, 0),
            (49.90, "Intentions", F_MONT_BLACK, 82, C_WHITE, None, 0, 46),
            (50.78, "buy them", F_DAFOE, 114, C_BLUE_BRIGHT, C_BLUE, 14, 110),
        ],
    },
    # 7. Final Signature CTA Lockup (53.88 - 56.89s): "Improve / 'The Lives' / of all of these people"
    # (Directly mirrors t=27.20s "Comment / 'Rhythm' / or DM me" in reference 7.mp4!)
    {
        "t_start": 53.88,
        "t_end": 56.89,
        "anchor_x": 540,
        "anchor_y": 1025,
        "align": "center",
        "lines": [
            (53.92, "Improve", F_DAFOE, 92, C_WHITE, None, 0, 0),
            (54.55, "'The Lives'", F_MONT_BLACK_IT, 88, C_BLUE_BRIGHT, C_BLUE, 0, 74),
            (55.12, "of all of these people", F_MONT_BOLD, 44, C_WHITE, None, 0, 168),
        ],
    },
]

# Crimson Cutaway #2 Lockup (30.25 - 33.48s): "You have so much / tension / in the / transition"
CRIMSON_LINES_CUT2 = [
    (30.28, "You have so much", F_MONT_BOLD, 42, C_WHITE, None, 0, 0),
    (31.15, "tension", F_MONT_BLACK, 90, C_WHITE, None, 0, 46),
    (31.78, "in the", F_MONT_BLACK, 86, C_WHITE, None, 0, 124),
    (32.32, "transition", F_DAFOE, 118, C_CRIMSON, C_CRIMSON, 10, 188),
]

# Cutaway #3 Pre-Lockup (44.12 - 45.95s) & Crimson Lockup (45.95 - 48.05s)
PRE_LINES_CUT3 = [
    (44.16, "Motivated", F_MONT_BOLD, 46, C_WHITE, None, 0, 0),
    (44.66, "Only By", F_MONT_BLACK, 88, C_WHITE, None, 0, 48),
    (45.24, "Money", F_DAFOE, 118, C_BLUE_BRIGHT, C_BLUE, 12, 116),
]

CRIMSON_LINES_CUT3 = [
    (45.96, "tend to", F_MONT_BOLD, 44, C_WHITE, None, 0, 0),
    (46.24, "not care", F_MONT_BLACK, 90, C_WHITE, None, 0, 46),
    (47.05, "about the", F_MONT_BLACK, 84, C_WHITE, None, 0, 124),
    (47.48, "people", F_DAFOE, 122, C_CRIMSON, C_CRIMSON, 12, 186),
]

# Words that get the signature partial inner blue glow (or crimson glow) in single-word chest captions
BLUE_GLOW_WORDS = {
    "many", "sold,", "large", "businesses", "businesses,", "learn",
    "sacrifice", "skills", "own", "shift,", "starts", "serve",
    "customers,", "important", "impact", "community.", "hoping", "improve",
}
CRIMSON_GLOW_WORDS = {"closing.", "closes,", "close."}


def is_in_cutaway_or_lockup(t):
    if 4.80 <= t < 8.36:
        return True
    if 28.28 <= t < 33.48:
        return True
    if 44.12 <= t < 48.05:
        return True
    for lk in TALKING_LOCKUPS:
        if lk["t_start"] <= t < lk["t_end"]:
            return True
    return False


def main():
    t0 = time.time()
    words = json.load(open(WORDS_JSON))
    print(f"Loaded {len(words)} master timestamped words.")

    grade_overlay = build_talking_head_grade_overlay()
    midnight_bg = build_midnight_blue_bg()
    crimson_bg = build_crimson_vignette_bg()

    # Decode raw video frames (720x1280 @ 23.976fps)
    dec_cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        RAW_VIDEO,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    dec_proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, bufsize=720 * 1280 * 3 * 4)

    # Encode output 1080x1920 H.264 + mixed stereo AAC audio
    enc_cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        f"{FPS_NUM}/{FPS_DEN}",
        "-i",
        "-",
        "-i",
        MIXED_WAV,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
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
    enc_proc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, bufsize=W * H * 3 * 2)

    raw_frame_bytes = 720 * 1280 * 3
    frame_idx = 0

    while True:
        buf = dec_proc.stdout.read(raw_frame_bytes)
        if len(buf) < raw_frame_bytes:
            break
        t = frame_idx / FPS
        raw_rgb = np.frombuffer(buf, dtype=np.uint8).reshape((1280, 720, 3))

        # -------------------------------------------------------------------
        # Route by Scene: Full-Screen Cutaways vs. Graded Talking Head
        # -------------------------------------------------------------------
        if 4.80 <= t < 8.36:
            # Cutaway #1: 3D Dark Laptop with BizBuySell Marketplace UI
            frame = render_laptop_cutaway(t, midnight_bg)

        elif 28.28 <= t < 33.48:
            # Cutaway #2: 3D Blue Handshake Badge Shatter -> Crimson Vignette + Stacked Red Script
            frame = render_shatter_and_crimson_cutaway(
                t=t,
                t_start=28.28,
                t_shatter=29.25,
                t_crimson=30.25,
                t_end=33.48,
                icon_type="handshake",
                crimson_lines=CRIMSON_LINES_CUT2,
                midnight_bg=midnight_bg,
                crimson_bg=crimson_bg,
                pre_lockup=None,
            )

        elif 44.12 <= t < 48.05:
            # Cutaway #3: Midnight Blue "Motivated Only By Money" + Coin Badge Shatter -> Crimson "tend to not care about the people"
            frame = render_shatter_and_crimson_cutaway(
                t=t,
                t_start=44.12,
                t_shatter=45.62,
                t_crimson=45.95,
                t_end=48.05,
                icon_type="coin",
                crimson_lines=CRIMSON_LINES_CUT3,
                midnight_bg=midnight_bg,
                crimson_bg=crimson_bg,
                pre_lockup=PRE_LINES_CUT3,
            )

        else:
            # Talking Head with Multi-Scale Camera Framing + Studio Blue/Dark Vignette Grade
            frame = get_camera_crop(raw_rgb, t)
            # Apply studio grade overlay
            a = grade_overlay[:, :, 3:4].astype(np.float32) * (1.0 / 255.0)
            frame = np.clip(
                frame.astype(np.float32) * (1.0 - a) + grade_overlay[:, :, :3].astype(np.float32) * a,
                0,
                255,
            ).astype(np.uint8)

            # 1. Check if inside a 3-tier chest lockup
            drew_lockup = False
            for lk in TALKING_LOCKUPS:
                if lk["t_start"] <= t < lk["t_end"]:
                    draw_stacked_lockup(
                        frame,
                        t,
                        lk["lines"],
                        anchor_x=lk["anchor_x"],
                        anchor_y=lk["anchor_y"],
                        align=lk["align"],
                        t_end=lk["t_end"],
                    )
                    drew_lockup = True
                    break

            # 2. Otherwise, draw single-word kinetic chest caption with partial inner blue glow
            if not drew_lockup:
                active_w = None
                for w_item in words:
                    ws, we = w_item["timestamp"]
                    if ws <= t <= we + 0.08:
                        active_w = w_item
                        break
                if active_w is not None:
                    w_txt = active_w["text"]
                    ws, we = active_w["timestamp"]
                    dt_w = t - ws
                    p_w = ease_out_back(clamp(dt_w / 0.14), s=1.3)
                    g_style = (
                        "crimson_lead"
                        if w_txt.lower() in CRIMSON_GLOW_WORDS
                        else ("blue_lead" if w_txt.lower() in BLUE_GLOW_WORDS else "none")
                    )
                    w_im = get_word_caption_img(w_txt, glow_Style=g_style)
                    wy = int(1105 + (1.0 - p_w) * 14 - w_im.height / 2)
                    wx = int(W / 2 - w_im.width / 2)
                    alpha_composite_roi(frame, w_im, wx, wy)

            # 3. Dual 3D Glowing Circular Chest Badges below the words (matching t=18.80s & t=20.60s in reference 7.mp4)
            # Sequence A (16.54 - 19.90s): Sacrifice (Flame) + Skills to Own (Key)
            if 16.50 <= t < 19.92:
                if t < 17.90:
                    # Single centered badge first (just like t=18.80s in reference 7.mp4!)
                    place_badge(frame, "flame", cx=540, cy=1310, radius=105, t=t, t_appear=16.54, t_end=19.90)
                else:
                    # Smoothly slide left badge to x=402 and pop in right badge at x=678 (just like t=20.60s!)
                    slide_p = ease_out_cubic(clamp((t - 17.90) / 0.28))
                    lx = int(540 - slide_p * 138)
                    place_badge(frame, "flame", cx=lx, cy=1310, radius=105, t=t, t_appear=16.54, t_end=19.90)
                    place_badge(frame, "key", cx=678, cy=1310, radius=105, t=t, t_appear=17.90, t_end=19.90)

            # Sequence B (23.96 - 28.24s): Business A Closes -> Business B Serves Customers
            if 23.92 <= t < 28.25:
                if t < 25.50:
                    place_badge(frame, "store_a", cx=540, cy=1310, radius=105, t=t, t_appear=23.96, t_end=28.24, tint="crimson")
                else:
                    slide_p = ease_out_cubic(clamp((t - 25.50) / 0.28))
                    lx = int(540 - slide_p * 138)
                    place_badge(frame, "store_a", cx=lx, cy=1310, radius=105, t=t, t_appear=23.96, t_end=28.24, tint="crimson")
                    place_badge(frame, "store_b", cx=678, cy=1310, radius=105, t=t, t_appear=25.50, t_end=28.24, tint="blue")

            # Sequence C (38.88 - 40.90s): Impact in the Community -> Exact Megaphone + Handshake pair from reference 7.mp4!
            if 38.88 <= t < 40.90:
                if t < 39.88:
                    place_badge(frame, "megaphone", cx=540, cy=1310, radius=105, t=t, t_appear=38.90, t_end=40.88)
                else:
                    slide_p = ease_out_cubic(clamp((t - 39.88) / 0.26))
                    lx = int(540 - slide_p * 138)
                    place_badge(frame, "megaphone", cx=lx, cy=1310, radius=105, t=t, t_appear=38.90, t_end=40.88)
                    place_badge(frame, "handshake", cx=678, cy=1310, radius=105, t=t, t_appear=39.88, t_end=40.88)

            # Sequence D (51.84 - 53.85s): "and improve them" -> Storefront B + Handshake badges
            if 51.84 <= t < 53.85:
                if t < 52.65:
                    place_badge(frame, "store_b", cx=540, cy=1310, radius=105, t=t, t_appear=51.86, t_end=53.84)
                else:
                    slide_p = ease_out_cubic(clamp((t - 52.65) / 0.26))
                    lx = int(540 - slide_p * 138)
                    place_badge(frame, "store_b", cx=lx, cy=1310, radius=105, t=t, t_appear=51.86, t_end=53.84)
                    place_badge(frame, "handshake", cx=678, cy=1310, radius=105, t=t, t_appear=52.65, t_end=53.84)

        enc_proc.stdin.write(frame.tobytes())
        frame_idx += 1
        if frame_idx % 200 == 0:
            el = time.time() - t0
            print(f"  Rendered {frame_idx}/1364 frames ({frame_idx/el:.1f} fps)...")

    dec_proc.stdout.close()
    dec_proc.wait()
    enc_proc.stdin.close()
    enc_proc.wait()

    el = time.time() - t0
    sz_mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"Done! Rendered {frame_idx} frames in {el:.1f}s -> {OUT_MP4} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    main()
