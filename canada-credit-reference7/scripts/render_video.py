#!/usr/bin/env python3
"""
Master 1080x1920 (9:16, 30fps) Ultra-Professional Renderer for:
Raw Video: `imports/AQNIjRAr6B_rpxG_wzm3pn0pqMSSszClolTOsw76yoX7UOh-zXRCqq06eAMqeJpIodAvFY71EYRLXsxIrLyfOJk4v976706AUNDQXx4.mp4`
Inspired directly by `reference 7.mp4` and built on the proven 3D compositing engine
of `felix-gray-reference7/scripts/render_video.py`.
"""
import json
import math
import os
import subprocess
import sys
import time
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, lfilter

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
W, H = 1080, 1920
FPS = 30.0
SPEED_FACTOR = 1.07
BPM = 120.0
BEAT_SEC = 60.0 / BPM  # 0.50s per beat

REPO_ROOT = "/home/user/COOL-backup"
RAW_MP4 = f"{REPO_ROOT}/imports/AQNIjRAr6B_rpxG_wzm3pn0pqMSSszClolTOsw76yoX7UOh-zXRCqq06eAMqeJpIodAvFY71EYRLXsxIrLyfOJk4v976706AUNDQXx4.mp4"
SPEED_MP4 = "/tmp/ref7_inspect/raw_107x.mp4"
WORDS_JSON = "/tmp/ref7_inspect/words_107x.json"
MIXED_WAV = "/tmp/ref7_inspect/studio_mixed_v2.wav"

OUT_DIR = f"{REPO_ROOT}/canada-credit-reference7/film"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_MP4 = os.path.join(OUT_DIR, "canada-credit-reference7-9x16.mp4")

FONT_ROOT = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
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
C_BLUE = (37, 88, 255)          # #2558FF signature electric cobalt
C_BLUE_BRIGHT = (78, 138, 255)  # #4E8AFF neon script cobalt
C_CRIMSON = (255, 36, 66)       # #FF2442 signature crimson script
C_EMERALD = (24, 218, 142)      # #18DA8E approval highlight

_FONT_CACHE = {}


def get_font(path, size):
    key = (path, int(size))
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, int(size))
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


# ---------------------------------------------------------------------------
# Easing & Compositing Helpers
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
    Creates the `reference 7.mp4` studio atmosphere over talking-head frames:
    - Subtle dark vignette at the very top ceiling edge (`y = 0..320`) to tone down fluorescent lights
    - Keeps the speaker's face (`y = 320..1080`) 100% crystal-clear and natural!
    - Smooth dark lower-chest gradient (`y = 1100..1920`) over the hoodie so typography & 3D orbs pop
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    top_vig = np.clip((H * 0.22 - yy) / (H * 0.22), 0, 1) ** 1.6 * 0.38
    d_chest = np.exp(-((yy - H * 0.72) / 310.0) ** 2) * np.exp(-((xx - W * 0.50) / 560.0) ** 2)
    bottom_dark = np.clip((yy - H * 0.56) / (H * 0.44), 0, 1) ** 1.35 * 0.62
    edge_vig = np.clip(((xx - W * 0.5) / (W * 0.54)) ** 2 + ((yy - H * 0.5) / (H * 0.54)) ** 2 - 0.42, 0, 1) * 0.28

    dark_alpha = np.clip(top_vig + d_chest * 0.32 + bottom_dark + edge_vig, 0, 0.74)

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[:, :, 0] = 3
    rgba[:, :, 1] = 6
    rgba[:, :, 2] = 16
    rgba[:, :, 3] = np.clip(dark_alpha * 255, 0, 255).astype(np.uint8)
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
    d_tr = np.sqrt(((xx - W * 0.78) / 620.0) ** 2 + ((yy - H * 0.28) / 680.0) ** 2)
    glow_tr = np.exp(-(d_tr ** 1.6) * 0.95)
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
    Renders a single chest-level word in `Montserrat ExtraBold` (72px) with zero black outline,
    soft Gaussian drop shadow, and localized radial electric-blue or crimson light bloom on
    the leading letters (matching `inquiry` and `inconsistent` in `reference 7.mp4`).
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

    # 1. Soft dark drop shadow for instant chest contrast (no black stroke outline!)
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
        gx = pad_x + min(tw * 0.26, 75.0)
        gy = pad_y + th * 0.52
        yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
        dist = np.sqrt(((xx - gx) / 68.0) ** 2 + ((yy - gy) / 48.0) ** 2)

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
# Stacked Asymmetric Lockups (Strictly <= 2 Lines on A-Roll, Chest Level)
# ---------------------------------------------------------------------------
def render_text_layer(text, font_path, size, color, glow_color=None, glow_radius=16):
    font = get_font(font_path, size)
    dummy = Image.new("RGBA", (10, 10))
    d0 = ImageDraw.Draw(dummy)
    bbox = d0.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 55
    cw, ch = tw + pad * 2, th + pad * 2
    tx, ty = pad - bbox[0], pad - bbox[1]

    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

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
# 3D Glowing Circular Chest Badges (`reference 7.mp4` t=12.3s, 19.2s, 21.0s)
# ---------------------------------------------------------------------------
_BADGE_CACHE = {}


def draw_icon_vector(draw, icon_type, cx, cy, r):
    """Draws crisp white vector iconography inside a 3D circular orb."""
    w_white = (255, 255, 255, 255)
    navy_cut = (12, 36, 118, 255)
    crimson_cut = (95, 12, 28, 255)
    s = r / 105.0

    if icon_type == "card":
        # Sleek angled credit card with chip & stripe
        draw.rounded_rectangle(
            [cx - 46 * s, cy - 30 * s, cx + 46 * s, cy + 30 * s],
            radius=int(9 * s),
            fill=w_white,
        )
        draw.rectangle(
            [cx - 46 * s, cy - 16 * s, cx + 46 * s, cy - 4 * s],
            fill=navy_cut,
        )
        draw.rounded_rectangle(
            [cx - 34 * s, cy + 4 * s, cx - 14 * s, cy + 19 * s],
            radius=int(3 * s),
            fill=navy_cut,
        )
        draw.line(
            [(cx + 6 * s, cy + 14 * s), (cx + 34 * s, cy + 14 * s)],
            fill=navy_cut,
            width=max(2, int(5 * s)),
        )

    elif icon_type == "bank":
        # Classical bank pediment + columns + base
        pediment = [
            (cx, cy - 42 * s),
            (cx - 46 * s, cy - 14 * s),
            (cx + 46 * s, cy - 14 * s),
        ]
        draw.polygon(pediment, fill=w_white)
        draw.rectangle([cx - 42 * s, cy - 12 * s, cx + 42 * s, cy - 6 * s], fill=w_white)
        for bx in (-28, -9, 9, 28):
            draw.rounded_rectangle(
                [cx + (bx - 5) * s, cy - 4 * s, cx + (bx + 5) * s, cy + 26 * s],
                radius=int(2 * s),
                fill=w_white,
            )
        draw.rounded_rectangle(
            [cx - 46 * s, cy + 26 * s, cx + 46 * s, cy + 38 * s],
            radius=int(3 * s),
            fill=w_white,
        )

    elif icon_type == "handshake":
        # Exact clasped handshake from reference 7.mp4 (t=12.30s & t=20.60s)
        cuff_l = [
            (cx - 56 * s, cy - 8 * s),
            (cx - 38 * s, cy - 28 * s),
            (cx - 22 * s, cy - 12 * s),
            (cx - 40 * s, cy + 10 * s),
        ]
        cuff_r = [
            (cx + 56 * s, cy - 8 * s),
            (cx + 38 * s, cy - 28 * s),
            (cx + 22 * s, cy - 12 * s),
            (cx + 40 * s, cy + 10 * s),
        ]
        draw.polygon(cuff_l, fill=w_white)
        draw.polygon(cuff_r, fill=w_white)
        palm = [
            (cx - 32 * s, cy - 8 * s),
            (cx - 6 * s, cy - 24 * s),
            (cx + 32 * s, cy - 8 * s),
            (cx + 26 * s, cy + 18 * s),
            (cx + 2 * s, cy + 30 * s),
            (cx - 26 * s, cy + 18 * s),
        ]
        draw.polygon(palm, fill=w_white)
        for i in range(-1, 3):
            fx = cx + i * 9 * s
            fy = cy + 12 * s + abs(i) * 2 * s
            draw.line(
                [(fx - 6 * s, fy + 10 * s), (fx + 5 * s, fy - 4 * s)],
                fill=navy_cut,
                width=max(2, int(4 * s)),
            )
        draw.line(
            [(cx - 14 * s, cy - 6 * s), (cx + 4 * s, cy - 18 * s), (cx + 18 * s, cy - 4 * s)],
            fill=navy_cut,
            width=max(2, int(4.5 * s)),
        )

    elif icon_type == "coin":
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

    elif icon_type == "house_slash":
        # Minimalist house + crimson slash (for "pas de maison")
        roof = [(cx, cy - 40 * s), (cx - 44 * s, cy - 6 * s), (cx + 44 * s, cy - 6 * s)]
        draw.polygon(roof, fill=w_white)
        draw.rounded_rectangle([cx - 32 * s, cy - 8 * s, cx + 32 * s, cy + 36 * s], radius=int(5 * s), fill=w_white)
        draw.rounded_rectangle([cx - 10 * s, cy + 10 * s, cx + 10 * s, cy + 36 * s], radius=int(3 * s), fill=crimson_cut)
        draw.line([(cx - 44 * s, cy + 38 * s), (cx + 44 * s, cy - 38 * s)], fill=(255, 48, 76, 255), width=max(4, int(7 * s)))

    elif icon_type == "car_slash":
        # Minimalist car silhouette + crimson slash (for "pas de voiture")
        cabin = [(cx - 24 * s, cy - 22 * s), (cx + 20 * s, cy - 22 * s), (cx + 34 * s, cy - 2 * s), (cx - 34 * s, cy - 2 * s)]
        draw.polygon(cabin, fill=w_white)
        draw.rounded_rectangle([cx - 46 * s, cy - 4 * s, cx + 46 * s, cy + 20 * s], radius=int(8 * s), fill=w_white)
        draw.ellipse([cx - 34 * s, cy + 10 * s, cx - 14 * s, cy + 30 * s], fill=w_white, outline=crimson_cut, width=max(2, int(3 * s)))
        draw.ellipse([cx + 14 * s, cy + 10 * s, cx + 34 * s, cy + 30 * s], fill=w_white, outline=crimson_cut, width=max(2, int(3 * s)))
        draw.line([(cx - 44 * s, cy + 38 * s), (cx + 44 * s, cy - 38 * s)], fill=(255, 48, 76, 255), width=max(4, int(7 * s)))


def get_3d_badge_img(icon_type, radius=105, tint="blue"):
    """Pre-renders a 3D glowing circular badge matching `reference 7.mp4` (`t=12.30s`, `19.20s`, `21.00s`)."""
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

    outer_glow = np.exp(-np.maximum(0.0, norm_r - 0.85) * 3.4) * (norm_r > 0.85)
    edge_aa = np.clip((1.015 - norm_r) / 0.03, 0.0, 1.0)
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

    rim_col = (255, 92, 118, 235) if tint == "crimson" else (82, 148, 255, 240)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=rim_col,
        width=max(3, int(radius * 0.032)),
    )
    inner_col = (255, 160, 180, 90) if tint == "crimson" else (140, 195, 255, 95)
    r_in_ring = int(radius * 0.93)
    draw.ellipse(
        [cx - r_in_ring, cy - r_in_ring, cx + r_in_ring, cy + r_in_ring],
        outline=inner_col,
        width=max(1, int(radius * 0.015)),
    )

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
# Cutaway #1 (`7.80s - 11.95s`): 3D Dark MacBook Pro (`BanqueCanada` Credit UI)
# Directly modeled on `t=5.20s` & `t=7.00s` of `reference 7.mp4`
# ---------------------------------------------------------------------------
LAPTOP_CARDS = [
    {
        "appear": 7.95,
        "name": "Banque TD",
        "age": "1m",
        "msg1": "Nouveau dossier — Solde compte : 0,00 $.",
        "msg2": "Carte de crédit 3 000 $ CAD débloquée.",
        "badge": "3 000 $ CAD",
        "skeleton": False,
    },
    {
        "appear": 8.65,
        "name": "RBC Royal Bank",
        "age": "2m",
        "msg1": "Demande approuvée sans apport initial.",
        "msg2": "Plafond actif : 3 000 $ CAD immédiat.",
        "badge": "APPROUVÉ",
        "skeleton": False,
    },
    {
        "appear": 9.35,
        "name": "Scotiabank",
        "age": "5m",
        "msg1": "Ouverture nouveau résident validée.",
        "msg2": "Minimum garanti : 2 500 $ CAD de crédit.",
        "badge": "2 500 $ MIN",
        "skeleton": False,
    },
    {
        "appear": 10.05,
        "name": "BMO Canada",
        "age": "8m",
        "msg1": "Carte Platinum émise avec 0 $ sur compte.",
        "msg2": "Éligible au doublement de limite (×2).",
        "badge": "ACTIF",
        "skeleton": False,
    },
    {
        "appear": 10.75,
        "name": "CIBC Direct",
        "age": "12m",
        "msg1": "",
        "msg2": "",
        "badge": "",
        "skeleton": True,
    },
]


def render_laptop_cutaway(t, midnight_bg):
    dur = 11.95 - 7.80
    u = clamp((t - 7.80) / dur)
    e_u = ease_out_cubic(u)

    canvas = Image.fromarray(midnight_bg.copy()).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    cam_x = int(40 - e_u * 65)
    cam_y = int(45 - e_u * 55)

    lx0, ly0 = 165 + cam_x, 220 + cam_y
    lx1, ly1 = 1260 + cam_x, 1525 + cam_y

    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse([lx0 - 110, ly0 - 90, lx0 + 520, ly0 + 480], fill=(24, 72, 235, 78))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=65))
    canvas = Image.alpha_composite(canvas, glow_layer)
    draw = ImageDraw.Draw(canvas)

    # Lid body & metallic bezel
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=38, fill=(10, 12, 16, 255), outline=(44, 50, 66, 255), width=3)
    sx0, sy0 = lx0 + 28, ly0 + 34
    sx1, sy1 = lx1 - 28, ly1 - 36
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=18, fill=(11, 13, 18, 255))

    # Top header inside screen: "CréditBox" (exact match to "Chat Box" in reference 7.mp4)
    f_light = get_font(F_MONT_LIGHT, 50)
    f_bold = get_font(F_MONT_BOLD, 50)
    hx, hy = sx0 + 48, sy0 + 42
    draw.text((hx, hy), "Crédit", font=f_light, fill=(225, 230, 242, 255))
    w_part1 = draw.textbbox((0, 0), "Crédit", font=f_light)[2]
    draw.text((hx + w_part1 + 6, hy), "Canada", font=f_bold, fill=(255, 255, 255, 255))
    w_part2 = draw.textbbox((0, 0), "Canada", font=f_bold)[2]

    # Status pill next to header
    px0 = hx + w_part1 + w_part2 + 28
    py0 = hy + 10
    draw.rounded_rectangle([px0, py0, px0 + 246, py0 + 42], radius=21, fill=(14, 38, 30, 240), outline=(24, 218, 142, 220), width=2)
    f_pill = get_font(F_INTER_BOLD, 19)
    draw.text((px0 + 22, py0 + 9), "3 000 $ APPROUVÉ", font=f_pill, fill=(24, 218, 142, 255))

    # Right-hand detail pane (matching right column in t=5.2s & t=7.0s of reference 7.mp4)
    rx0 = sx0 + 625
    ry0 = sy0 + 125
    rx1 = sx1 - 36
    ry1 = sy1 - 115
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=22, fill=(22, 25, 34, 255), outline=(42, 48, 64, 255), width=2)

    f_stat_big = get_font(F_MONT_BLACK, 54)
    f_stat_sub = get_font(F_INTER_MED, 21)
    amt_str = "3 000 $" if t < 10.6 else "2 500 $"
    draw.text((rx0 + 36, ry0 + 44), amt_str, font=f_stat_big, fill=(37, 88, 255, 255))
    draw.text((rx0 + 36, ry0 + 118), "Carte de crédit allouée", font=f_stat_sub, fill=(190, 198, 214, 255))
    draw.text((rx0 + 36, ry0 + 148), "avec 0 $ sur le compte", font=f_stat_sub, fill=(24, 218, 142, 255))

    # Bottom right message input bar with blue circular icon (exact match to t=5.2s & t=7.0s)
    ib_y0 = ry1 + 20
    ib_y1 = sy1 - 24
    draw.rounded_rectangle([rx0, ib_y0, rx1, ib_y1], radius=20, fill=(22, 25, 34, 255), outline=(42, 48, 64, 255), width=2)
    draw.rounded_rectangle([rx0 + 16, ib_y0 + 14, rx0 + 60, ib_y0 + 58], radius=12, fill=(45, 92, 255, 255))
    draw.ellipse([rx0 + 27, ib_y0 + 25, rx0 + 49, ib_y0 + 47], outline=(255, 255, 255, 255), width=3)
    draw.text((rx0 + 76, ib_y0 + 24), "Demander une carte...", font=get_font(F_INTER_REG, 21), fill=(130, 138, 158, 255))

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

        avx, avy, avr = cx0 + 54, cy0 + card_h // 2, 33
        if card["skeleton"]:
            cd.ellipse([avx - avr, avy - avr, avx + avr, avy + avr], fill=(60, 66, 82, alpha_c))
        else:
            cd.ellipse([avx - avr, avy - avr, avx + avr, avy + avr], fill=(232, 236, 245, alpha_c))
            cd.ellipse([avx - 11, avy - 18, avx + 11, avy + 4], fill=(52, 58, 74, alpha_c))
            cd.pieslice([avx - 22, avy + 6, avx + 22, avy + 38], 180, 360, fill=(52, 58, 74, alpha_c))

        tx = cx0 + 106
        ty = cy0 + 24
        cd.text((tx, ty), card["name"], font=f_name, fill=(255, 255, 255, alpha_c))
        nw = cd.textbbox((0, 0), card["name"], font=f_name)[2]
        cd.text((tx + nw + 10, ty + 1), f"•  {card['age']}", font=f_age, fill=(150, 160, 182, alpha_c))

        if card["skeleton"]:
            cd.rounded_rectangle([tx, ty + 38, tx + 210, ty + 54], radius=7, fill=(58, 64, 80, alpha_c))
        else:
            bx1 = cx1 - 22
            bx0 = bx1 - 128
            by0 = cy0 + 22
            cd.rounded_rectangle([bx0, by0, bx1, by0 + 28], radius=14, fill=(14, 42, 32, alpha_c), outline=(24, 218, 142, alpha_c), width=1)
            bb = cd.textbbox((0, 0), card["badge"], font=f_b)
            cd.text((bx0 + (128 - (bb[2] - bb[0])) / 2, by0 + 5), card["badge"], font=f_b, fill=(24, 218, 142, alpha_c))

            char_progress = int(clamp((dt - 0.05) / 0.48) * (len(card["msg1"]) + len(card["msg2"])))
            m1 = card["msg1"][: min(len(card["msg1"]), char_progress)]
            m2 = card["msg2"][: max(0, char_progress - len(card["msg1"]))]
            cd.text((tx, ty + 36), m1, font=f_msg, fill=(215, 222, 235, alpha_c))
            if m2:
                cd.text((tx, ty + 64), m2, font=f_msg, fill=(182, 190, 208, alpha_c))

        canvas = Image.alpha_composite(canvas, c_layer)

    draw = ImageDraw.Draw(canvas)

    # 3D Laptop Base / Keyboard Deck in perspective below the screen
    ky0 = ly1 - 4
    ky1 = ky0 + 245
    deck_pts = [(lx0 - 10, ky0), (lx1 + 10, ky0), (lx1 + 135, ky1), (lx0 - 135, ky1)]
    draw.polygon(deck_pts, fill=(38, 43, 54, 255))
    draw.polygon([(lx0 + 40, ky0), (lx1 - 40, ky0), (lx1 - 30, ky0 + 18), (lx0 + 30, ky0 + 18)], fill=(14, 16, 22, 255))
    kw_pts = [(lx0 + 30, ky0 + 28), (lx1 - 30, ky0 + 28), (lx1 + 45, ky0 + 168), (lx0 - 45, ky0 + 168)]
    draw.polygon(kw_pts, fill=(12, 14, 19, 255), outline=(58, 64, 78, 255))

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

    tp_pts = [(lx0 + 310, ky0 + 178), (lx0 + 680, ky0 + 178), (lx0 + 710, ky1 - 8), (lx0 + 280, ky1 - 8)]
    draw.polygon(tp_pts, fill=(30, 35, 45, 255), outline=(56, 62, 76, 255))

    zoom = 0.95 + 0.09 * e_u
    cw = int(W / zoom)
    ch = int(H / zoom)
    x_crop = (W - cw) // 2
    y_crop = (H - ch) // 2
    cropped = canvas.crop((x_crop, y_crop, x_crop + cw, y_crop + ch)).resize((W, H), Image.Resampling.BILINEAR)
    return np.asarray(cropped.convert("RGB"))


# ---------------------------------------------------------------------------
# Cutaways #2 & #3: 3D Badge Shatter -> Crimson Vignette (`reference 7.mp4` t=12.2s -> 14.8s)
# ---------------------------------------------------------------------------
def generate_shatter_shards(radius=198, n_rings=5, seed=77):
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
            pts = []
            for rr, aa in [(r0, a0), (r1, a0), (r1, a1), (r0, a1)]:
                jit_r = rr + rng.uniform(-5, 5) if rr > 0 else 0
                jit_a = aa + rng.uniform(-0.04, 0.04)
                px = math.cos(jit_a) * jit_r - cx
                py = math.sin(jit_a) * jit_r - cy
                pts.append((px, py))

            speed = rng.uniform(220.0, 680.0) * (0.45 + 0.75 * (rm / radius))
            v_ang = am + rng.uniform(-0.32, 0.32)
            vx = math.cos(v_ang) * speed
            vy = math.sin(v_ang) * speed - rng.uniform(40.0, 180.0)
            omega_z = rng.uniform(-6.5, 6.5)
            omega_x = rng.uniform(3.5, 9.5)
            phase_x = rng.uniform(0, math.pi * 2)
            is_white = rng.random() < 0.58
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

    if pre_lockup is not None and t < t_crimson:
        draw_stacked_lockup(frame, t, pre_lockup, anchor_x=210, anchor_y=640, align="left", t_end=t_crimson)

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
            od.polygon(poly_back, fill=(24, 68, 195, a_val))
            if sh["is_white"]:
                lum = int(215 + 40 * abs(tilt_x))
                od.polygon(poly_front, fill=(lum, lum, min(255, lum + 10), a_val))
            else:
                od.polygon(poly_front, fill=(48, 112, 255, a_val))

        alpha_composite_roi(frame, overlay, 0, 0)

    if t >= t_crimson - 0.05:
        draw_stacked_lockup(frame, t, crimson_lines, anchor_x=215, anchor_y=820, align="left", t_end=t_end)

    return frame


# ---------------------------------------------------------------------------
# Multi-Scale Camera Framing & Ken Burns Schedule for Talking-Head Shots
# ---------------------------------------------------------------------------
def get_camera_crop(frame_rgb, t):
    """
    Reframes the speaker so his eyes sit at the Rule-of-Thirds upper line (cropping out
    the empty fluorescent ceiling) and applies multi-scale camera cuts + Ken Burns drift.
    """
    if t < 3.44:
        u = t / 3.44
        zoom = 1.16 + 0.04 * u
        cx, cy = 0.50, 0.62
    elif t < 7.80:
        u = (t - 3.44) / (7.80 - 3.44)
        zoom = 1.24 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.63
    elif t < 15.80:
        u = (t - 11.95) / (15.80 - 11.95)
        zoom = 1.15 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.61
    elif t < 21.16:
        u = (t - 15.80) / (21.16 - 15.80)
        zoom = 1.26 - 0.03 * clamp(u)
        cx, cy = 0.50, 0.63
    elif t < 26.60:
        u = (t - 21.16) / (26.60 - 21.16)
        zoom = 1.17 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.62
    elif t < 33.80:
        u = (t - 26.60) / (33.80 - 26.60)
        zoom = 1.25 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.63
    elif t < 41.40:
        u = (t - 37.80) / (41.40 - 37.80)
        zoom = 1.15 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.61
    elif t < 44.80:
        u = (t - 41.40) / (44.80 - 41.40)
        zoom = 1.26 + 0.02 * clamp(u)
        cx, cy = 0.50, 0.63
    elif t < 55.40:
        u = (t - 49.00) / (55.40 - 49.00)
        zoom = 1.17 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.62
    elif t < 62.20:
        u = (t - 55.40) / (62.20 - 55.40)
        zoom = 1.24 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.63
    else:
        u = (t - 62.20) / (64.02 - 62.20)
        zoom = 1.18 - 0.04 * clamp(u)
        cx, cy = 0.50, 0.61

    sh, sw, _ = frame_rgb.shape
    cw = sw / zoom
    ch = sh / zoom
    x0 = int(clamp(cx * sw - cw / 2, 0, sw - cw))
    y0 = int(clamp(cy * sh - ch / 2, 0, sh - ch))
    crop = frame_rgb[y0 : y0 + int(ch), x0 : x0 + int(cw)]
    resized = cv2.resize(crop, (W, H), interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(resized, (0, 0), 1.4)
    sharp = cv2.addWeighted(resized, 1.14, blur, -0.14, 0)
    return sharp


# ---------------------------------------------------------------------------
# Master 2-Line Chest Lockups on Talking-Head Segments (Strictly <= 2 Lines!)
# Placed at y=1265 over the dark hoodie, completely below chin & microphone!
# ---------------------------------------------------------------------------
TALKING_LOCKUPS = [
    # 1. Opening Hook (0.00 - 1.48s): "Le plus fou / au Canada ?"
    {
        "t_start": 0.00,
        "t_end": 1.48,
        "anchor_x": 185,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (0.00, "Le plus fou", F_MONT_BLACK, 82, C_WHITE, None, 0, 0),
            (0.45, "au Canada ?", F_DAFOE, 118, C_BLUE_BRIGHT, C_BLUE, 14, 68),
        ],
    },
    # 2. Credit Card Request (5.60 - 7.80s): "Une carte / de crédit"
    {
        "t_start": 5.60,
        "t_end": 7.80,
        "anchor_x": 195,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (5.60, "Une carte", F_MONT_BLACK, 86, C_WHITE, None, 0, 0),
            (6.15, "de crédit", F_DAFOE, 120, C_BLUE_BRIGHT, C_BLUE, 16, 68),
        ],
    },
    # 3. Multiply 2,500$ (15.80 - 18.48s): "Les 2 500 $ / tu multiplies"
    {
        "t_start": 15.80,
        "t_end": 18.48,
        "anchor_x": 180,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (15.85, "Les 2 500 $", F_MONT_BLACK, 84, C_WHITE, None, 0, 0),
            (16.65, "tu multiplies", F_DAFOE, 116, C_BLUE_BRIGHT, C_BLUE, 14, 68),
        ],
    },
    # 4. Doubled in First Days (21.16 - 23.48s): "Carte 2 500 $ / je l'ai doublée"
    {
        "t_start": 21.16,
        "t_end": 23.48,
        "anchor_x": 175,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (21.18, "Carte 2 500 $", F_MONT_BLACK, 82, C_SILVER, None, 0, 0),
            (22.05, "je l'ai doublée", F_DAFOE, 116, C_BLUE_BRIGHT, C_BLUE, 14, 68),
        ],
    },
    # 5. Cour des Grands (31.00 - 33.80s): "La cour / des grands"
    {
        "t_start": 31.00,
        "t_end": 33.80,
        "anchor_x": 195,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (31.05, "La cour", F_MONT_BLACK, 88, C_WHITE, None, 0, 0),
            (31.85, "des grands", F_DAFOE, 120, C_BLUE_BRIGHT, C_BLUE, 18, 68),
        ],
    },
    # 6. Mindset Shift (39.80 - 42.40s): "T'as rien / mais t'as tout"
    {
        "t_start": 39.80,
        "t_end": 42.40,
        "anchor_x": 190,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (39.85, "T'as rien,", F_MONT_BLACK, 84, C_SILVER, None, 0, 0),
            (41.40, "mais t'as tout", F_DAFOE, 118, C_BLUE_BRIGHT, C_BLUE, 14, 68),
        ],
    },
    # 7. Manage Properly (55.40 - 56.40s): "Gère-le / correctement"
    {
        "t_start": 55.40,
        "t_end": 56.40,
        "anchor_x": 185,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (55.42, "Gère-le", F_MONT_BLACK, 84, C_WHITE, None, 0, 0),
            (55.72, "correctement", F_DAFOE, 114, C_BLUE_BRIGHT, C_BLUE, 12, 68),
        ],
    },
    # 8. Final Signature CTA Lockup (62.20 - 64.02s): "La famille / 'Abonnez-vous'"
    {
        "t_start": 62.20,
        "t_end": 64.02,
        "anchor_x": 540,
        "anchor_y": 1265,
        "align": "center",
        "lines": [
            (62.24, "La famille", F_DAFOE, 96, C_WHITE, None, 0, 0),
            (62.75, "'Abonnez-vous'", F_MONT_BLACK_IT, 82, C_BLUE_BRIGHT, C_BLUE, 0, 78),
        ],
    },
]

# Cutaway #2 Crimson Reveal (35.40 - 37.80s): "Repartir de zéro / même avec rien" (<= 2 lines)
CRIMSON_LINES_CUT2 = [
    (35.45, "Repartir de zéro", F_MONT_BLACK, 82, C_WHITE, None, 0, 0),
    (36.35, "même avec rien", F_DAFOE, 118, C_CRIMSON, C_CRIMSON, 12, 74),
]

# Cutaway #3 Pre-Lockup (44.80 - 46.50s) & Crimson Lockup (46.50 - 49.00s) (<= 2 lines)
PRE_LINES_CUT3 = [
    (44.85, "S'enrichir", F_MONT_BLACK, 86, C_WHITE, None, 0, 0),
    (45.40, "grâce aux dettes", F_DAFOE, 112, C_BLUE_BRIGHT, C_BLUE, 12, 72),
]

CRIMSON_LINES_CUT3 = [
    (46.55, "En France :", F_MONT_BLACK, 84, C_WHITE, None, 0, 0),
    (47.10, "le découvert !", F_DAFOE, 120, C_CRIMSON, C_CRIMSON, 12, 74),
]

BLUE_GLOW_WORDS = {
    "canada", "banque", "crédit", "3000$", "2500$", "argent",
    "carte", "intelligent", "multiplies", "premiers", "doublée",
    "5000$", "gères", "augmentent", "risque", "grands",
    "opportunité", "zéro", "mentalité", "système", "dette",
    "s'enrichissent", "dettes", "crédit",
}
CRIMSON_GLOW_WORDS = {"rond", "rien", "découvert", "baisse", "maison", "voiture", "ruiné"}


# ---------------------------------------------------------------------------
# Studio Audio Engine: Broadcast Voice EQ + Subtle Dark-Pulse Bed + Studio SFX
# ---------------------------------------------------------------------------
SR = 44100


def butter_bandpass(lowcut, highcut, fs, order=3):
    nyq = 0.5 * fs
    low = max(0.001, min(0.99, lowcut / nyq))
    high = max(low + 0.001, min(0.999, highcut / nyq))
    b, a = butter(order, [low, high], btype="band")
    return b, a


def make_whoosh(duration=0.38, low_f=140, high_f=1800, vol=0.10):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(n)
    b, a = butter_bandpass(low_f, high_f, SR, order=2)
    filtered = lfilter(b, a, noise)
    env = np.clip(np.sin(np.pi * (t / duration)), 0.0, 1.0) ** 2.2
    freq = np.linspace(low_f * 1.4, low_f * 0.5, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * env * 0.45
    sig = (filtered / (np.max(np.abs(filtered)) + 1e-6) * 0.55 + sub) * env * vol
    return np.column_stack([sig * 0.95, sig * 1.05])


def make_ui_pop(duration=0.09, f0=520, f1=980, vol=0.08):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = np.exp(-t * 42.0) * (1.0 - np.exp(-t * 400.0))
    sig = (np.sin(phase) + 0.3 * np.sin(2 * phase)) * env * vol
    return np.column_stack([sig, sig])


def make_shatter(duration=0.85, vol=0.13):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(107)
    sub_freq = 110.0 * np.exp(-t * 9.5) + 36.0
    sub_phase = 2 * np.pi * np.cumsum(sub_freq) / SR
    sub = np.sin(sub_phase) * np.exp(-t * 6.5) * 0.55

    shards = np.zeros(n)
    shard_times = [0.00, 0.015, 0.032, 0.055, 0.08, 0.11, 0.145, 0.19, 0.24, 0.31, 0.39]
    shard_freqs = [2400, 3100, 1950, 3800, 2750, 4200, 2200, 3450, 2900, 3600, 2500]
    for st, sf in zip(shard_times, shard_freqs):
        idx = int(st * SR)
        rem = n - idx
        if rem <= 0:
            continue
        ts = np.linspace(0, rem / SR, rem, endpoint=False)
        ping = (np.sin(2 * np.pi * sf * ts) + 0.45 * np.sin(2 * np.pi * (sf * 1.414) * ts)) * np.exp(-ts * 28.0)
        shards[idx:] += ping * 0.18

    burst = rng.standard_normal(n)
    b, a = butter_bandpass(1200, 7500, SR, order=2)
    burst_f = lfilter(b, a, burst)
    burst_env = np.exp(-t * 14.0) * (1.0 - np.exp(-t * 250.0))
    burst_sig = burst_f / (np.max(np.abs(burst_f)) + 1e-6) * burst_env * 0.35

    sig_l = (sub + shards * 1.08 + burst_sig * 0.92) * vol
    sig_r = (sub + shards * 0.92 + burst_sig * 1.08) * vol
    return np.column_stack([sig_l, sig_r])


def make_soft_riser(duration=1.2, vol=0.065):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = 110.0 + 110.0 * ((t / duration) ** 2)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = (t / duration) ** 2 * np.clip(np.sin(np.pi * (t / duration)), 0.0, 1.0)
    sig = (np.sin(phase) + 0.4 * np.sin(1.5 * phase)) * env * vol
    return np.column_stack([sig * 0.95, sig * 1.05])


def add_at(mix, clip, t_sec):
    idx = int(t_sec * SR)
    if idx < 0 or idx >= len(mix):
        return
    end = min(len(mix), idx + len(clip))
    mix[idx:end] += clip[: end - idx]


def build_studio_audio():
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    clean_vox_wav = "/tmp/ref7_inspect/clean_vox_afftdn.wav"
    # Use FFmpeg's broadcast FFT spectral denoiser (afftdn) + studio EQ + gentle optical-style compressor
    subprocess.run(
        [
            ff, "-y", "-v", "error", "-i", SPEED_MP4, "-vn",
            "-af", "highpass=f=85,afftdn=nf=-24,equalizer=f=180:width_type=o:width=1.2:g=1.5,equalizer=f=3400:width_type=o:width=1.4:g=2.0,acompressor=threshold=-18dB:ratio=2.0:attack=15:release=200:makeup=2dB",
            "-ac", "2", "-ar", str(SR), clean_vox_wav,
        ],
        check=True,
    )
    _, data = wavfile.read(clean_vox_wav)
    voice = data.astype(np.float32) / 32768.0
    if voice.ndim == 1:
        voice = np.column_stack([voice, voice])

    n_total = len(voice)
    t_arr = np.arange(n_total, dtype=np.float32) / SR

    # Warm, deep-filtered 120 BPM dark-ambient sub-bass & soft studio pulse (-20 dB under voice)
    beat_phase = (t_arr % BEAT_SEC) / BEAT_SEC
    sub_f = 55.0 + 48.0 * np.exp(-beat_phase * 24.0)
    sub_kick = np.sin(2 * np.pi * sub_f * (t_arr % BEAT_SEC)) * np.exp(-beat_phase * 7.5) * 0.042

    # Warm low-passed minor chord pad (Am -> Fmaj7 -> C -> G, filtered below 380 Hz so it never clashes with speech)
    bar_idx = ((t_arr / (BEAT_SEC * 4.0)).astype(np.int32)) % 4
    roots = np.choose(bar_idx, [110.0, 87.31, 130.81, 98.00])
    thirds = np.choose(bar_idx, [130.81, 110.0, 164.81, 123.47])
    fifths = np.choose(bar_idx, [164.81, 130.81, 196.00, 146.83])
    pump = 0.35 + 0.65 * (1.0 - np.exp(-beat_phase * 5.5))
    pad_l = (0.45 * np.sin(2 * np.pi * roots * t_arr) + 0.30 * np.sin(2 * np.pi * thirds * t_arr) + 0.25 * np.sin(2 * np.pi * fifths * t_arr)) * pump * 0.026
    pad_r = (0.45 * np.sin(2 * np.pi * roots * t_arr) + 0.30 * np.sin(2 * np.pi * thirds * t_arr + 0.3) + 0.25 * np.sin(2 * np.pi * fifths * t_arr - 0.3)) * pump * 0.026

    mix = voice.copy()
    mix[:, 0] += sub_kick + pad_l
    mix[:, 1] += sub_kick + pad_r

    # Studio SFX synced to every cutaway, 3D badge pop, and shatter
    whoosh_in = make_whoosh(0.36, 150, 1900, vol=0.095)
    whoosh_out = make_whoosh(0.32, 180, 1500, vol=0.080)
    for t_in in [0.02, 5.58, 7.75, 15.78, 21.14, 30.98, 33.75, 39.78, 44.75, 55.38, 62.18]:
        add_at(mix, whoosh_in, t_in)
    for t_out in [11.88, 37.72, 48.92]:
        add_at(mix, whoosh_out, t_out)

    # Laptop UI Card Pops (7.80 - 11.95s)
    for i, t_card in enumerate([7.95, 8.65, 9.35, 10.05]):
        add_at(mix, make_ui_pop(0.085, 480 + i * 45, 920 + i * 55, vol=0.075), t_card)

    # 3D Circular Chest Badge Pops
    badge_times = [3.48, 4.50, 12.10, 13.50, 23.60, 26.50, 51.05, 53.00, 59.10, 60.15]
    for i, tb in enumerate(badge_times):
        add_at(mix, make_ui_pop(0.095, 420 + (i % 2) * 110, 860 + (i % 2) * 140, vol=0.080), tb)

    # 3D Circle Shatter in Cutaway #2 (34.75s) & Cutaway #3 (46.50s)
    add_at(mix, make_shatter(0.88, vol=0.125), 34.74)
    add_at(mix, make_whoosh(0.42, 110, 1200, vol=0.09), 35.42)
    add_at(mix, make_shatter(0.75, vol=0.105), 46.48)
    add_at(mix, make_soft_riser(1.1, vol=0.065), 62.00)

    peak = np.max(np.abs(mix))
    if peak > 0.96:
        mix = mix * (0.96 / peak)

    out_pcm = np.clip(mix * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(MIXED_WAV, SR, out_pcm)
    return MIXED_WAV


# ---------------------------------------------------------------------------
# Master Frame Router (Cutaways vs. Talking Head + 3D Chest Badges)
# ---------------------------------------------------------------------------
def compose_frame_rgb(raw_rgb, t, words, grade_overlay, midnight_bg, crimson_bg):
    # Cutaway #1 (7.80 - 11.95s): 3D Dark MacBook Pro (`Crédit Canada` 3,000$ / 2,500$ UI)
    if 7.80 <= t < 11.95:
        return render_laptop_cutaway(t, midnight_bg)

    # Cutaway #2 (33.80 - 37.80s): 3D Handshake Badge Shatter -> Crimson Vignette ("Repartir de zéro / même avec rien")
    if 33.80 <= t < 37.80:
        return render_shatter_and_crimson_cutaway(
            t=t,
            t_start=33.80,
            t_shatter=34.75,
            t_crimson=35.45,
            t_end=37.80,
            icon_type="handshake",
            crimson_lines=CRIMSON_LINES_CUT2,
            midnight_bg=midnight_bg,
            crimson_bg=crimson_bg,
            pre_lockup=None,
        )

    # Cutaway #3 (44.80 - 49.00s): "S'enrichir grâce aux dettes" + 3D $ Badge Shatter -> Crimson "En France : le découvert !"
    if 44.80 <= t < 49.00:
        return render_shatter_and_crimson_cutaway(
            t=t,
            t_start=44.80,
            t_shatter=46.15,
            t_crimson=46.50,
            t_end=49.00,
            icon_type="coin",
            crimson_lines=CRIMSON_LINES_CUT3,
            midnight_bg=midnight_bg,
            crimson_bg=crimson_bg,
            pre_lockup=PRE_LINES_CUT3,
        )

    # Talking Head with Multi-Scale Camera Framing + Clean Lower-Chest Vignette Grade
    frame = get_camera_crop(raw_rgb, t)
    a = grade_overlay[:, :, 3:4].astype(np.float32) * (1.0 / 255.0)
    frame = np.clip(
        frame.astype(np.float32) * (1.0 - a) + grade_overlay[:, :, :3].astype(np.float32) * a,
        0,
        255,
    ).astype(np.uint8)

    # 1. Check if inside a 2-tier overlapping chest lockup
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

    # 2. Otherwise, draw single-word kinetic chest caption with partial inner blue/crimson glow
    if not drew_lockup:
        active_w = None
        for w_item in words:
            ws, we = w_item["timestamp"]
            if ws <= t <= we + 0.06:
                active_w = w_item
                break
        if active_w is not None:
            w_txt = active_w["text"]
            ws, _ = active_w["timestamp"]
            dt_w = t - ws
            p_w = ease_out_back(clamp(dt_w / 0.14), s=1.3)
            clean_tok = w_txt.lower().strip("?!.,")
            g_style = (
                "crimson_lead"
                if clean_tok in CRIMSON_GLOW_WORDS
                else ("blue_lead" if clean_tok in BLUE_GLOW_WORDS else "none")
            )
            w_im = get_word_caption_img(w_txt, glow_Style=g_style)
            wy = int(1310 + (1.0 - p_w) * 14 - w_im.height / 2)
            wx = int(W / 2 - w_im.width / 2)
            alpha_composite_roi(frame, w_im, wx, wy)

    # 3. Dual 3D Glowing Circular Chest Badges below the words (`reference 7.mp4` t=19.2s & t=21.0s)
    # Sequence A (3.44 - 5.58s): "Tu vas à la banque..." -> Bank Orb + Credit Card Orb
    if 3.44 <= t < 5.58:
        if t < 4.50:
            place_badge(frame, "bank", cx=540, cy=1505, radius=105, t=t, t_appear=3.48, t_end=5.56)
        else:
            slide_p = ease_out_cubic(clamp((t - 4.50) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "bank", cx=lx, cy=1505, radius=105, t=t, t_appear=3.48, t_end=5.56)
            place_badge(frame, "card", cx=678, cy=1505, radius=105, t=t, t_appear=4.50, t_end=5.56)

    # Sequence B (12.00 - 15.75s): "Minimum 2 500 $ dans une carte..." -> Coin ($) Orb + Card Orb
    if 12.00 <= t < 15.75:
        if t < 13.50:
            place_badge(frame, "coin", cx=540, cy=1505, radius=105, t=t, t_appear=12.10, t_end=15.72)
        else:
            slide_p = ease_out_cubic(clamp((t - 13.50) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "coin", cx=lx, cy=1505, radius=105, t=t, t_appear=12.10, t_end=15.72)
            place_badge(frame, "card", cx=678, cy=1505, radius=105, t=t, t_appear=13.50, t_end=15.72)

    # Sequence C (23.50 - 29.35s): "Mon crédit est passé de 2 500 $ à 5 000 $... plus ils l'augmentent" -> Card Orb + Handshake Orb
    if 23.50 <= t < 29.35:
        if t < 26.50:
            place_badge(frame, "card", cx=540, cy=1505, radius=105, t=t, t_appear=23.60, t_end=29.32)
        else:
            slide_p = ease_out_cubic(clamp((t - 26.50) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "card", cx=lx, cy=1505, radius=105, t=t, t_appear=23.60, t_end=29.32)
            place_badge(frame, "handshake", cx=678, cy=1505, radius=105, t=t, t_appear=26.50, t_end=29.32)

    # Sequence D (51.00 - 55.35s): "va à la banque, demande une carte... ils vont te donner un crédit" -> Bank Orb + Handshake Orb
    if 51.00 <= t < 55.35:
        if t < 53.00:
            place_badge(frame, "bank", cx=540, cy=1505, radius=105, t=t, t_appear=51.05, t_end=55.32)
        else:
            slide_p = ease_out_cubic(clamp((t - 53.00) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "bank", cx=lx, cy=1505, radius=105, t=t, t_appear=51.05, t_end=55.32)
            place_badge(frame, "handshake", cx=678, cy=1505, radius=105, t=t, t_appear=53.00, t_end=55.32)

    # Sequence E (59.05 - 62.15s): "pas de maison, pas de voiture, t'as tout ruiné" -> Crimson House-Slash Orb + Crimson Car-Slash Orb
    if 59.05 <= t < 62.15:
        if t < 60.15:
            place_badge(frame, "house_slash", cx=540, cy=1505, radius=105, t=t, t_appear=59.10, t_end=62.12, tint="crimson")
        else:
            slide_p = ease_out_cubic(clamp((t - 60.15) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "house_slash", cx=lx, cy=1505, radius=105, t=t, t_appear=59.10, t_end=62.12, tint="crimson")
            place_badge(frame, "car_slash", cx=678, cy=1505, radius=105, t=t, t_appear=60.15, t_end=62.12, tint="crimson")

    return frame


def generate_preview(preview_path: str):
    words = json.load(open(WORDS_JSON))
    grade_overlay = build_talking_head_grade_overlay()
    midnight_bg = build_midnight_blue_bg()
    crimson_bg = build_crimson_vignette_bg()

    cap = cv2.VideoCapture(SPEED_MP4)
    sample_times = [0.9, 3.8, 4.9, 6.5, 9.2, 11.0, 14.2, 17.2, 22.4, 27.5, 32.2, 35.1, 36.8, 45.6, 47.6, 60.8]
    thumbs = []
    for ts in sample_times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ts * FPS)))
        ok, bgr = cap.read()
        if not ok:
            continue
        raw_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        frame_rgb = compose_frame_rgb(raw_rgb, ts, words, grade_overlay, midnight_bg, crimson_bg)
        frame_bgr = frame_rgb[:, :, ::-1].copy()
        th = cv2.resize(frame_bgr, (270, 480), interpolation=cv2.INTER_AREA)
        cv2.putText(th, f"{ts:4.1f}s", (14, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2, cv2.LINE_AA)
        thumbs.append(th)
    cap.release()

    rows = [np.hstack(thumbs[i : i + 4]) for i in range(0, 16, 4)]
    grid = np.vstack(rows)
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    cv2.imwrite(preview_path, grid, [int(cv2.IMWRITE_JPEG_QUALITY), 94])
    print(f"Saved 16-frame preview sheet to {preview_path}")


def main():
    t0 = time.time()
    words = json.load(open(WORDS_JSON))
    print(f"Loaded {len(words)} timestamped words.")

    build_studio_audio()
    grade_overlay = build_talking_head_grade_overlay()
    midnight_bg = build_midnight_blue_bg()
    crimson_bg = build_crimson_vignette_bg()

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    dec_cmd = [
        ff, "-v", "error", "-i", SPEED_MP4,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    dec_proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, bufsize=720 * 1280 * 3 * 4)

    enc_cmd = [
        ff, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", "30", "-i", "-",
        "-i", MIXED_WAV,
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-maxrate", "3400k", "-bufsize", "6800k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
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
        frame = compose_frame_rgb(raw_rgb, t, words, grade_overlay, midnight_bg, crimson_bg)
        enc_proc.stdin.write(frame.tobytes())
        frame_idx += 1
        if frame_idx % 300 == 0:
            el = time.time() - t0
            print(f"  Rendered {frame_idx}/1921 frames ({frame_idx/el:.1f} fps)...")

    dec_proc.stdout.close()
    dec_proc.wait()
    enc_proc.stdin.close()
    enc_proc.wait()

    el = time.time() - t0
    sz_mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"Done! Rendered {frame_idx} frames in {el:.1f}s -> {OUT_MP4} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        generate_preview(sys.argv[2])
    else:
        main()
