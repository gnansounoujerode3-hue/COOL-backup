#!/usr/bin/env python3
"""
Master 1080x1920 (9:16, 30fps) Ultra-Professional Renderer for:
Raw Video: `imports/AQNIjRAr6B_rpxG_wzm3pn0pqMSSszClolTOsw76yoX7UOh-zXRCqq06eAMqeJpIodAvFY71EYRLXsxIrLyfOJk4v976706AUNDQXx4.mp4`
Inspired directly by `reference 7.mp4`.

Key guarantees:
1. Cutaway #1 (7.80s - 12.60s): Sleek 3D perspective-tilted Credit Card animation showing
   `3 000 $` (7.80s - 10.65s) and then flipping in 3D to `2 500 $` (10.65s - 12.60s).
2. ZERO repeated animations & ZERO repeated 3D icons across the entire video:
   - Cutaway #1 (7.80s - 12.60s): 3D Perspective Credit Card (`3 000 $` -> `2 500 $`)
   - Cutaway #2 (23.48s - 26.60s): 3D Perspective Credit Growth Chart (`2 500 $` -> `5 000 $`)
   - Cutaway #3 (33.80s - 37.80s): Crimson Studio Vignette + Neon Progress Ring (`Repartir de zéro / même avec rien`)
   - Cutaway #4 (44.80s - 49.00s): 125-Shard 3D Sphere Shatter (`S'enrichir grâce aux dettes` -> `En France : le découvert !`)
   - Chest Orb Seq 1 (3.44s - 5.58s): `bank` + `key`
   - Chest Orb Seq 2 (15.80s - 18.48s): `bulb` + `multiply`
   - Chest Orb Seq 3 (29.40s - 33.75s): `shield` + `crown`
   - Chest Orb Seq 4 (51.00s - 55.35s): `sliders` + `check`
   - Chest Orb Seq 5 (59.05s - 62.15s): `house_slash` + `car_slash`
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
MIXED_WAV = "/tmp/ref7_inspect/studio_mixed_v3.wav"

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
F_MONO = f"{FONT_ROOT}/dm-mono/500Medium/DMMono_500Medium.ttf"

# Color Palette (from `reference 7.mp4`)
C_WHITE = (255, 255, 255)
C_SILVER = (202, 210, 226)
C_BLUE = (37, 88, 255)          # #2558FF signature electric cobalt
C_BLUE_BRIGHT = (78, 138, 255)  # #4E8AFF neon script cobalt
C_CRIMSON = (255, 36, 66)       # #FF2442 signature crimson script
C_EMERALD = (24, 218, 142)      # #18DA8E approval highlight
C_GOLD = (248, 192, 58)         # #F8C03A metallic gold chip

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
    """Full-screen dark crimson-red radial vignette matching `t=14.80s` of `reference 7.mp4`."""
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

    shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    ds.text((tx, ty + 5), word_text, font=font, fill=(0, 0, 0, 195))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=9))
    canvas = Image.alpha_composite(canvas, shadow)

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
# 3D Glowing Circular Chest Badges — 10 Unique Vector Icons (Never Repeated!)
# ---------------------------------------------------------------------------
_BADGE_CACHE = {}


def draw_icon_vector(draw, icon_type, cx, cy, r):
    """Draws 100% distinct, crisp white vector iconography inside a 3D circular orb."""
    w_white = (255, 255, 255, 255)
    navy_cut = (12, 36, 118, 255)
    crimson_cut = (95, 12, 28, 255)
    s = r / 105.0

    if icon_type == "bank":
        pediment = [(cx, cy - 42 * s), (cx - 46 * s, cy - 14 * s), (cx + 46 * s, cy - 14 * s)]
        draw.polygon(pediment, fill=w_white)
        draw.rectangle([cx - 42 * s, cy - 12 * s, cx + 42 * s, cy - 6 * s], fill=w_white)
        for bx in (-28, -9, 9, 28):
            draw.rounded_rectangle([cx + (bx - 5) * s, cy - 4 * s, cx + (bx + 5) * s, cy + 26 * s], radius=int(2 * s), fill=w_white)
        draw.rounded_rectangle([cx - 46 * s, cy + 26 * s, cx + 46 * s, cy + 38 * s], radius=int(3 * s), fill=w_white)

    elif icon_type == "key":
        # Security account key (angled at -35 deg)
        draw.ellipse([cx - 42 * s, cy - 36 * s, cx - 2 * s, cy + 4 * s], fill=w_white)
        draw.ellipse([cx - 30 * s, cy - 24 * s, cx - 14 * s, cy - 8 * s], fill=navy_cut)
        shaft = [(cx - 6 * s, cy - 12 * s), (cx + 40 * s, cy + 24 * s), (cx + 32 * s, cy + 34 * s), (cx - 14 * s, cy - 2 * s)]
        draw.polygon(shaft, fill=w_white)
        tooth1 = [(cx + 16 * s, cy + 18 * s), (cx + 24 * s, cy + 24 * s), (cx + 14 * s, cy + 36 * s), (cx + 6 * s, cy + 30 * s)]
        tooth2 = [(cx + 28 * s, cy + 28 * s), (cx + 36 * s, cy + 34 * s), (cx + 26 * s, cy + 46 * s), (cx + 18 * s, cy + 40 * s)]
        draw.polygon(tooth1, fill=w_white)
        draw.polygon(tooth2, fill=w_white)

    elif icon_type == "bulb":
        # Intelligence lightbulb + rays (for "si t'es intelligent")
        draw.ellipse([cx - 28 * s, cy - 36 * s, cx + 28 * s, cy + 16 * s], fill=w_white)
        draw.rounded_rectangle([cx - 16 * s, cy + 10 * s, cx + 16 * s, cy + 28 * s], radius=int(4 * s), fill=w_white)
        draw.rounded_rectangle([cx - 11 * s, cy + 32 * s, cx + 11 * s, cy + 40 * s], radius=int(4 * s), fill=w_white)
        for ang in (-145, -90, -35, 20, 160):
            ra = math.radians(ang)
            x1 = cx + math.cos(ra) * 35 * s
            y1 = (cy - 10 * s) + math.sin(ra) * 35 * s
            x2 = cx + math.cos(ra) * 47 * s
            y2 = (cy - 10 * s) + math.sin(ra) * 47 * s
            draw.line([(x1, y1), (x2, y2)], fill=w_white, width=max(3, int(5 * s)))

    elif icon_type == "multiply":
        # Bold "×2" inside twin rising rings (for "tu les multiplies")
        draw.arc([cx - 46 * s, cy - 46 * s, cx + 46 * s, cy + 46 * s], start=210, end=30, fill=w_white, width=max(3, int(6 * s)))
        draw.arc([cx - 46 * s, cy - 46 * s, cx + 46 * s, cy + 46 * s], start=30, end=210, fill=w_white, width=max(3, int(6 * s)))
        f_x = get_font(F_MONT_BLACK, int(48 * s))
        bb = draw.textbbox((0, 0), "×2", font=f_x)
        draw.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), "×2", font=f_x, fill=w_white)

    elif icon_type == "shield":
        # Bank risk/trust shield with upward arrow (for "plus la banque prend le risque")
        pts = [
            (cx, cy - 44 * s),
            (cx + 38 * s, cy - 28 * s),
            (cx + 32 * s, cy + 12 * s),
            (cx, cy + 44 * s),
            (cx - 32 * s, cy + 12 * s),
            (cx - 38 * s, cy - 28 * s),
        ]
        draw.polygon(pts, fill=w_white)
        draw.line([(cx, cy + 20 * s), (cx, cy - 18 * s)], fill=navy_cut, width=max(3, int(6 * s)))
        draw.line([(cx - 14 * s, cy - 4 * s), (cx, cy - 18 * s), (cx + 14 * s, cy - 4 * s)], fill=navy_cut, width=max(3, int(6 * s)))

    elif icon_type == "crown":
        # Royal crown (for "la cour des grands")
        pts = [
            (cx - 38 * s, cy + 24 * s),
            (cx - 44 * s, cy - 18 * s),
            (cx - 18 * s, cy + 4 * s),
            (cx, cy - 30 * s),
            (cx + 18 * s, cy + 4 * s),
            (cx + 44 * s, cy - 18 * s),
            (cx + 38 * s, cy + 24 * s),
        ]
        draw.polygon(pts, fill=w_white)
        draw.rounded_rectangle([cx - 38 * s, cy + 28 * s, cx + 38 * s, cy + 36 * s], radius=int(3 * s), fill=w_white)
        for dx_c, dy_c in [(-44, -22), (0, -34), (44, -22)]:
            draw.ellipse([cx + (dx_c - 5) * s, cy + (dy_c - 5) * s, cx + (dx_c + 5) * s, cy + (dy_c + 5) * s], fill=w_white)

    elif icon_type == "sliders":
        # Precision control sliders (for "et le reste c'est toi qui gères")
        for idx_s, (sy_off, kx_off) in enumerate([(-24, -14), (0, 16), (24, -6)]):
            yy_s = cy + sy_off * s
            draw.line([(cx - 40 * s, yy_s), (cx + 40 * s, yy_s)], fill=w_white, width=max(3, int(5 * s)))
            kx = cx + kx_off * s
            draw.ellipse([kx - 10 * s, yy_s - 10 * s, kx + 10 * s, yy_s + 10 * s], fill=w_white)
            draw.ellipse([kx - 4 * s, yy_s - 4 * s, kx + 4 * s, yy_s + 4 * s], fill=navy_cut)

    elif icon_type == "check":
        # Bold circular verification badge (for "Mais gère-le correctement !")
        draw.ellipse([cx - 42 * s, cy - 42 * s, cx + 42 * s, cy + 42 * s], outline=w_white, width=max(3, int(6 * s)))
        draw.line([(cx - 20 * s, cy + 2 * s), (cx - 5 * s, cy + 18 * s), (cx + 22 * s, cy - 14 * s)], fill=w_white, width=max(4, int(8 * s)))

    elif icon_type == "house_slash":
        roof = [(cx, cy - 40 * s), (cx - 44 * s, cy - 6 * s), (cx + 44 * s, cy - 6 * s)]
        draw.polygon(roof, fill=w_white)
        draw.rounded_rectangle([cx - 32 * s, cy - 8 * s, cx + 32 * s, cy + 36 * s], radius=int(5 * s), fill=w_white)
        draw.rounded_rectangle([cx - 10 * s, cy + 10 * s, cx + 10 * s, cy + 36 * s], radius=int(3 * s), fill=crimson_cut)
        draw.line([(cx - 44 * s, cy + 38 * s), (cx + 44 * s, cy - 38 * s)], fill=(255, 48, 76, 255), width=max(4, int(7 * s)))

    elif icon_type == "car_slash":
        cabin = [(cx - 24 * s, cy - 22 * s), (cx + 20 * s, cy - 22 * s), (cx + 34 * s, cy - 2 * s), (cx - 34 * s, cy - 2 * s)]
        draw.polygon(cabin, fill=w_white)
        draw.rounded_rectangle([cx - 46 * s, cy - 4 * s, cx + 46 * s, cy + 20 * s], radius=int(8 * s), fill=w_white)
        draw.ellipse([cx - 34 * s, cy + 10 * s, cx - 14 * s, cy + 30 * s], fill=w_white, outline=crimson_cut, width=max(2, int(3 * s)))
        draw.ellipse([cx + 14 * s, cy + 10 * s, cx + 34 * s, cy + 30 * s], fill=w_white, outline=crimson_cut, width=max(2, int(3 * s)))
        draw.line([(cx - 44 * s, cy + 38 * s), (cx + 44 * s, cy - 38 * s)], fill=(255, 48, 76, 255), width=max(4, int(7 * s)))

    elif icon_type == "euro_overdraft":
        # Central icon for the France Découvert shatter sphere (used only in Cutaway #4)
        draw.ellipse([cx - 44 * s, cy - 44 * s, cx + 44 * s, cy + 44 * s], outline=w_white, width=max(3, int(6 * s)))
        f_eu = get_font(F_MONT_BLACK, int(54 * s))
        bb = draw.textbbox((0, 0), "€", font=f_eu)
        draw.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), "€", font=f_eu, fill=w_white)


def get_3d_badge_img(icon_type, radius=105, tint="blue"):
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
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=rim_col, width=max(3, int(radius * 0.032)))
    inner_col = (255, 160, 180, 90) if tint == "crimson" else (140, 195, 255, 95)
    r_in_ring = int(radius * 0.93)
    draw.ellipse([cx - r_in_ring, cy - r_in_ring, cx + r_in_ring, cy + r_in_ring], outline=inner_col, width=max(1, int(radius * 0.015)))

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
# Cutaway #1 (`7.80s - 12.60s`): 3D Perspective Credit Card (`3 000 $` -> `2 500 $`)
# Replaces the laptop cutaway per user instruction:
# "Remplace cette animation par une carte de crédit avec le montant 3000$ et après 2500$"
# ---------------------------------------------------------------------------
def build_flat_credit_card_rgba(amount_str: str, subtitle_str: str, badge_str: str, badge_col: tuple, sheen_pos: float) -> np.ndarray:
    """
    Renders a photorealistic 920x580 Titanium Cobalt-Noir Credit Card texture with:
    - Brushed dark sapphire-titanium metallic gradient + dynamic diagonal specular sheen
    - Gold EMV smart chip with circuit contacts + contactless NFC waves
    - Embossed card number & glowing `3 000 $` or `2 500 $` credit limit
    """
    cw, ch = 920, 580
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    nx, ny = xx / cw, yy / ch

    # Metallic dark cobalt-titanium gradient + diagonal specular sheen sweep
    diag = nx * 0.72 + ny * 0.68
    sheen = np.exp(-((diag - sheen_pos) / 0.14) ** 2) * 0.55
    corner_glow = np.exp(-(((nx - 0.82) / 0.42) ** 2 + ((ny - 0.22) / 0.42) ** 2)) * 0.65

    r = np.clip(10 + corner_glow * 28 + sheen * 110, 0, 255).astype(np.uint8)
    g = np.clip(20 + corner_glow * 74 + sheen * 145, 0, 255).astype(np.uint8)
    b = np.clip(52 + corner_glow * 185 + sheen * 200, 0, 255).astype(np.uint8)

    card_im = Image.fromarray(np.dstack([r, g, b, np.full((ch, cw), 255, dtype=np.uint8)]), mode="RGBA")

    # Rounded card mask (radius=44)
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=44, fill=255)
    card_im.putalpha(mask)

    d = ImageDraw.Draw(card_im)
    # Specular metallic outer & inner border rings
    d.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=44, outline=(120, 175, 255, 235), width=4)
    d.rounded_rectangle([12, 12, cw - 13, ch - 13], radius=36, outline=(255, 255, 255, 45), width=2)

    # Top-left Bank Logo ("CRÉDIT" Light + "CANADA" Bold)
    f_l = get_font(F_MONT_LIGHT, 34)
    f_b = get_font(F_MONT_BLACK, 34)
    d.text((58, 48), "CRÉDIT", font=f_l, fill=(210, 222, 245, 255))
    w_cr = d.textbbox((0, 0), "CRÉDIT", font=f_l)[2]
    d.text((58 + w_cr + 10, 48), "CANADA", font=f_b, fill=(255, 255, 255, 255))

    # Top-right Status Pill ("LIMITE APPROUVÉE" or "MINIMUM GARANTI")
    pw = 285
    px0, py0 = cw - pw - 54, 44
    d.rounded_rectangle([px0, py0, px0 + pw, py0 + 48], radius=24, fill=(10, 24, 38, 230), outline=(*badge_col, 240), width=2)
    f_p = get_font(F_INTER_BOLD, 19)
    bb_p = d.textbbox((0, 0), badge_str, font=f_p)
    d.text((px0 + (pw - (bb_p[2] - bb_p[0])) / 2, py0 + 12), badge_str, font=f_p, fill=(*badge_col, 255))

    # Realistic Gold EMV Chip (left middle) + Contactless Waves
    cx0, cy0, cx1, cy1 = 62, 138, 174, 224
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16, fill=(242, 192, 68, 255), outline=(255, 232, 155, 255), width=2)
    # Chip circuit lines
    d.line([(cx0 + 36, cy0), (cx0 + 36, cy1)], fill=(165, 120, 28, 220), width=2)
    d.line([(cx1 - 36, cy0), (cx1 - 36, cy1)], fill=(165, 120, 28, 220), width=2)
    d.line([(cx0, cy0 + 28), (cx1, cy0 + 28)], fill=(165, 120, 28, 220), width=2)
    d.line([(cx0, cy1 - 28), (cx1, cy1 - 28)], fill=(165, 120, 28, 220), width=2)
    # Contactless NFC arcs next to chip
    for r_nfc in (16, 28, 40):
        d.arc([200 - r_nfc, 181 - r_nfc, 200 + r_nfc, 181 + r_nfc], start=-42, end=42, fill=(210, 225, 250, 215), width=3)

    # Center Hero Amount ("3 000 $" or "2 500 $") with soft neon bloom
    f_sub = get_font(F_MONO, 22)
    d.text((62, 252), subtitle_str, font=f_sub, fill=(185, 205, 240, 245))

    f_amt = get_font(F_MONT_BLACK, 118)
    glow_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.text((58, 282), amount_str, font=f_amt, fill=(*badge_col, 175))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=18))
    card_im = Image.alpha_composite(card_im, glow_layer)
    d = ImageDraw.Draw(card_im)
    d.text((58, 282), amount_str, font=f_amt, fill=(255, 255, 255, 255))

    # Bottom Card Number & Holder Info
    f_num = get_font(F_MONO, 29)
    d.text((62, 448), "4519   8824   0091   2026", font=f_num, fill=(215, 228, 250, 245))
    f_hol = get_font(F_INTER_MED, 20)
    d.text((62, 504), "NOUVEAU RÉSIDENT • SOLDE COMPTE : 0,00 $", font=f_hol, fill=(155, 178, 215, 235))

    # Bottom-right holographic MasterCard/Visa-style overlapping orbs
    d.ellipse([cw - 155, 468, cw - 95, 528], fill=(37, 88, 255, 215))
    d.ellipse([cw - 118, 468, cw - 58, 528], fill=(24, 218, 142, 205))

    return np.asarray(card_im)


def warp_card_3d(card_rgba: np.ndarray, yaw_deg: float, pitch_deg: float, scale: float, center_x: float, center_y: float) -> Image.Image:
    """Applies a true 3D perspective projection (`cv2.warpPerspective`) to the 920x580 credit card."""
    ch, cw = card_rgba.shape[:2]
    hw, hh = cw / 2.0, ch / 2.0
    pts_3d = np.array([[-hw, -hh, 0.0], [hw, -hh, 0.0], [hw, hh, 0.0], [-hw, hh, 0.0]], dtype=np.float32)

    ry = math.radians(yaw_deg)
    rx = math.radians(pitch_deg)
    cy_r, sy_r = math.cos(ry), math.sin(ry)
    cx_r, sx_r = math.cos(rx), math.sin(rx)

    rot_y = np.array([[cy_r, 0.0, sy_r], [0.0, 1.0, 0.0], [-sy_r, 0.0, cy_r]], dtype=np.float32)
    rot_x = np.array([[1.0, 0.0, 0.0], [0.0, cx_r, -sx_r], [0.0, sx_r, cx_r]], dtype=np.float32)
    r_mat = rot_x @ rot_y

    focal = 1450.0
    dst_pts = []
    for p in pts_3d:
        pr = r_mat @ p
        z = max(250.0, focal + pr[2])
        px = center_x + (pr[0] * focal / z) * scale
        py = center_y + (pr[1] * focal / z) * scale
        dst_pts.append([px, py])

    src_pts = np.array([[0, 0], [cw - 1, 0], [cw - 1, ch - 1], [0, ch - 1]], dtype=np.float32)
    dst_pts = np.array(dst_pts, dtype=np.float32)
    H_mat = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(
        card_rgba, H_mat, (W, H),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    return Image.fromarray(warped, mode="RGBA")


def render_3d_credit_card_cutaway(t: float, midnight_bg: np.ndarray) -> np.ndarray:
    """
    Renders Cutaway #1 (`7.80s - 12.60s`):
    - Phase 1 (`7.80s - 10.65s`): 3D Credit Card with `3 000 $` ("ils te passent une carte de crédit de 3 000 $")
    - Phase 2 (`10.65s - 12.60s`): Smooth 3D perspective flip to `2 500 $` ("Minimum 2 500 $ dans une carte alors que t'as pas d'argent")
    """
    age = t - 7.80
    p_enter = ease_out_back(clamp(age / 0.42), s=1.25)

    # Around t=10.65s .. 11.05s, perform a 180-deg 3D perspective flip from 3,000$ to 2,500$!
    flip_u = clamp((t - 10.60) / 0.42)
    is_phase2 = flip_u >= 0.50

    if not is_phase2:
        amt_str = "3 000 $"
        sub_str = "LIMITE DE CRÉDIT DÉBLOQUÉE"
        bdg_str = "APPROUVÉ • 3 000 $"
        bdg_col = C_EMERALD
        sheen = 0.15 + 0.70 * clamp(age / 2.8)
    else:
        amt_str = "2 500 $"
        sub_str = "MINIMUM GARANTI SANS APPORT"
        bdg_str = "MINIMUM • 2 500 $"
        bdg_col = C_BLUE_BRIGHT
        sheen = 0.20 + 0.65 * clamp((t - 10.80) / 1.8)

    # Smooth floating 3D angles + flip impulse around t=10.60..11.02s
    flip_yaw = math.sin(flip_u * math.pi) * 72.0 * (1.0 if flip_u < 0.5 else -1.0)
    base_yaw = -14.0 + 10.0 * math.sin(age * 1.35) + (1.0 - p_enter) * 35.0
    yaw = clamp(base_yaw + flip_yaw, -76.0, 76.0)
    pitch = 11.0 - 6.0 * math.cos(age * 1.15)
    scale = 1.02 * p_enter

    canvas = Image.fromarray(midnight_bg.copy()).convert("RGBA")

    # Ambient neon glow behind card
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    g_col = C_EMERALD if not is_phase2 else C_BLUE
    gd.ellipse([140, 560, W - 140, 1280], fill=(*g_col, int(85 * p_enter)))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=75))
    canvas = Image.alpha_composite(canvas, glow)

    card_tex = build_flat_credit_card_rgba(amt_str, sub_str, bdg_str, bdg_col, sheen)

    # 3D extruded metallic edge / drop-shadow layer slightly offset in Y/Z
    edge_im = warp_card_3d(card_tex, yaw, pitch, scale, W * 0.50 + 8, H * 0.48 + 16)
    edge_arr = np.asarray(edge_im).copy()
    edge_arr[:, :, :3] = (edge_arr[:, :, :3].astype(np.float32) * 0.22).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(edge_arr))

    # Main 3D warped credit card
    main_im = warp_card_3d(card_tex, yaw, pitch, scale, W * 0.50, H * 0.48)
    canvas = Image.alpha_composite(canvas, main_im)

    frame_rgb = np.asarray(canvas.convert("RGB")).copy()

    # Clean 2-line lockup below the 3D card matching what he says (no digits in Mr Dafoe!)
    if not is_phase2:
        lines = [
            (7.85, "Carte de crédit", F_MONT_BLACK, 78, C_WHITE, None, 0, 0),
            (8.25, "approuvée direct", F_DAFOE, 112, C_BLUE_BRIGHT, C_BLUE, 0, 72),
        ]
        draw_stacked_lockup(frame_rgb, t, lines, anchor_x=540, anchor_y=1340, align="center", t_end=10.65)
    else:
        lines = [
            (10.75, "Minimum 2 500 $", F_MONT_BLACK, 78, C_WHITE, None, 0, 0),
            (11.10, "sans argent", F_DAFOE, 116, C_BLUE_BRIGHT, C_BLUE, 0, 72),
        ]
        draw_stacked_lockup(frame_rgb, t, lines, anchor_x=540, anchor_y=1340, align="center", t_end=12.60)

    return frame_rgb


# ---------------------------------------------------------------------------
# Cutaway #2 (`23.48s - 26.60s`): 3D Perspective Credit Growth (`2 500 $` -> `5 000 $`)
# Unique animation (used ONLY once!) for "Mon crédit est passé de 2 500 à 5 000 $"
# ---------------------------------------------------------------------------
def render_3d_growth_cutaway(t: float, midnight_bg: np.ndarray) -> np.ndarray:
    age = t - 23.48
    p = ease_out_cubic(clamp(age / 0.40))
    prog = ease_in_out_cubic(clamp((age - 0.15) / 1.85))

    # Build a 880x680 glassmorphic growth chart texture and warp it in 3D perspective
    cw, ch = 880, 680
    panel = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle([4, 4, cw - 5, ch - 5], radius=42, fill=(10, 16, 34, 242), outline=(62, 118, 255, 225), width=4)

    # Live ticking counter: 2 500 $ -> 5 000 $
    cur_val = int(round(2500 + 2500 * prog))
    val_str = f"{cur_val:,} $".replace(",", " ")
    d.text((64, 52), "ÉVOLUTION DU PLAFOND DE CRÉDIT", font=get_font(F_MONO, 22), fill=(170, 190, 225, 255))
    d.text((64, 92), val_str, font=get_font(F_MONT_BLACK, 104), fill=(255, 255, 255, 255))

    # "+100% (×2)" Emerald Pill
    if prog > 0.25:
        p_b = clamp((prog - 0.25) / 0.45)
        d.rounded_rectangle([cw - 265, 112, cw - 64, 168], radius=28, fill=(12, 44, 34, int(240 * p_b)), outline=(24, 218, 142, int(255 * p_b)), width=2)
        d.text((cw - 235, 126), "DOUBLÉ ×2", font=get_font(F_INTER_BOLD, 22), fill=(24, 218, 142, int(255 * p_b)))

    # Rising 3D bars + glowing curve from 2 500 $ to 5 000 $
    milestones = [
        (0.0, "DÉPART", "2 500 $", 0.38, C_BLUE),
        (0.45, "DOUBLÉ", "5 000 $", 0.74, C_BLUE_BRIGHT),
        (0.85, "GESTION +", "10 000 $", 1.00, C_EMERALD),
    ]
    curve_pts = []
    for idx_m, (m_delay, m_lbl, m_val, m_h, m_col) in enumerate(milestones):
        mp = ease_out_back(clamp((age - m_delay) / 0.48), s=1.2)
        bx0 = 95 + idx_m * 265
        bx1 = bx0 + 165
        by_bot = 575
        bar_h = int(round(280 * m_h * mp))
        by_top = by_bot - max(18, bar_h)
        d.rounded_rectangle([bx0, by_top, bx1, by_bot], radius=22, fill=(*m_col, int(235 * mp)), outline=(255, 255, 255, int(190 * mp)), width=2)
        d.text((bx0 + 18, by_top - 42), m_val, font=get_font(F_MONT_BLACK, 28), fill=(255, 255, 255, int(255 * mp)))
        d.text((bx0 + 22, by_bot + 16), m_lbl, font=get_font(F_MONO, 20), fill=(180, 198, 230, int(240 * mp)))
        curve_pts.append((bx0 + 82, by_top))

    if len(curve_pts) >= 2:
        d.line(curve_pts, fill=(255, 255, 255, 220), width=6)

    warped_panel = warp_card_3d(np.asarray(panel), yaw_deg=-8.0 + 5.0 * math.sin(age * 1.2), pitch_deg=6.0, scale=0.98 * p, center_x=W * 0.50, center_y=H * 0.45)
    canvas = Image.fromarray(midnight_bg.copy()).convert("RGBA")
    canvas = Image.alpha_composite(canvas, warped_panel)
    frame_rgb = np.asarray(canvas.convert("RGB")).copy()

    lines = [
        (23.55, "De 2 500 $ à 5 000 $", F_MONT_BLACK, 64, C_WHITE, None, 0, 0),
        (24.10, "crédit doublé", F_DAFOE, 114, C_BLUE_BRIGHT, C_BLUE, 0, 72),
    ]
    draw_stacked_lockup(frame_rgb, t, lines, anchor_x=540, anchor_y=1365, align="center", t_end=26.60)
    return frame_rgb


# ---------------------------------------------------------------------------
# Cutaway #3 (`33.80s - 37.80s`): Crimson Studio Vignette ("Repartir de zéro / même avec rien")
# Matches `t=14.80s` of `reference 7.mp4` WITHOUT repeating the shatter animation!
# ---------------------------------------------------------------------------
def render_crimson_zero_cutaway(t: float, crimson_bg: np.ndarray) -> np.ndarray:
    age = t - 33.80
    frame = crimson_bg.copy()

    # Subtle glowing "0 $ -> 100%" opportunity ring above the stacked crimson lockup
    p_ring = ease_out_cubic(clamp(age / 1.4))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    rcx, rcy, rr = W // 2, 620, 135
    od.ellipse([rcx - rr, rcy - rr, rcx + rr, rcy + rr], fill=(24, 6, 12, 210), outline=(90, 22, 38, 180), width=6)
    end_ang = -90 + int(360 * p_ring)
    od.arc([rcx - rr, rcy - rr, rcx + rr, rcy + rr], start=-90, end=end_ang, fill=(255, 42, 74, 255), width=10)
    f_z = get_font(F_MONT_BLACK, 64)
    bb_z = od.textbbox((0, 0), "0 $", font=f_z)
    od.text((rcx - (bb_z[2] - bb_z[0]) / 2, rcy - (bb_z[3] - bb_z[1]) / 2 - bb_z[1]), "0 $", font=f_z, fill=(255, 255, 255, 255))
    alpha_composite_roi(frame, overlay, 0, 0)

    crimson_lines = [
        (33.90, "Repartir de zéro", F_MONT_BLACK, 84, C_WHITE, None, 0, 0),
        (35.10, "même avec rien", F_DAFOE, 120, C_CRIMSON, C_CRIMSON, 12, 76),
    ]
    draw_stacked_lockup(frame, t, crimson_lines, anchor_x=195, anchor_y=920, align="left", t_end=37.80)
    return frame


# ---------------------------------------------------------------------------
# Cutaway #4 (`44.80s - 49.00s`): The Single 125-Shard 3D Sphere Shatter Cutaway
# ("S'enrichir grâce aux dettes" -> Shatters into "En France : le découvert !")
# ---------------------------------------------------------------------------
def generate_shatter_shards(radius=165, n_rings=5, seed=77):
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


SHARDS_DATA = generate_shatter_shards(radius=165)


def render_shatter_decouvert_cutaway(t, midnight_bg, crimson_bg):
    t_start, t_shatter, t_crimson, t_end = 44.80, 46.25, 46.60, 49.00
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

    cx, cy = W // 2, int(H * 0.62)

    pre_lines = [
        (44.85, "S'enrichir", F_MONT_BLACK, 86, C_WHITE, None, 0, 0),
        (45.40, "grâce aux dettes", F_DAFOE, 112, C_BLUE_BRIGHT, C_BLUE, 12, 72),
    ]
    if t < t_crimson:
        draw_stacked_lockup(frame, t, pre_lines, anchor_x=210, anchor_y=640, align="left", t_end=t_crimson)

    if t < t_shatter:
        dt = t - t_start
        p_in = ease_out_back(clamp(dt / 0.32), s=1.35)
        rad = 155
        badge_im = get_3d_badge_img("euro_overdraft", radius=rad, tint="blue")
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
        crimson_lines = [
            (46.62, "En France :", F_MONT_BLACK, 84, C_WHITE, None, 0, 0),
            (47.12, "le découvert !", F_DAFOE, 120, C_CRIMSON, C_CRIMSON, 12, 74),
        ]
        draw_stacked_lockup(frame, t, crimson_lines, anchor_x=215, anchor_y=820, align="left", t_end=t_end)

    return frame


# ---------------------------------------------------------------------------
# Multi-Scale Camera Framing & Ken Burns Schedule for Talking-Head Shots
# ---------------------------------------------------------------------------
def get_camera_crop(frame_rgb, t):
    if t < 3.44:
        u = t / 3.44
        zoom = 1.16 + 0.04 * u
        cx, cy = 0.50, 0.62
    elif t < 7.80:
        u = (t - 3.44) / (7.80 - 3.44)
        zoom = 1.24 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.63
    elif t < 15.80:
        u = (t - 12.60) / (15.80 - 12.60)
        zoom = 1.15 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.61
    elif t < 23.48:
        u = (t - 15.80) / (23.48 - 15.80)
        zoom = 1.25 - 0.03 * clamp(u)
        cx, cy = 0.50, 0.63
    elif t < 33.80:
        u = (t - 26.60) / (33.80 - 26.60)
        zoom = 1.17 + 0.04 * clamp(u)
        cx, cy = 0.50, 0.62
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
# ---------------------------------------------------------------------------
TALKING_LOCKUPS = [
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
    {
        "t_start": 33.80,
        "t_end": 37.80,
        "anchor_x": 185,
        "anchor_y": 1265,
        "align": "left",
        "lines": [
            (33.85, "Repartir de zéro", F_MONT_BLACK, 82, C_WHITE, None, 0, 0),
            (35.20, "même avec rien", F_DAFOE, 118, C_CRIMSON, C_CRIMSON, 14, 68),
        ],
    },
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

BLUE_GLOW_WORDS = {
    "canada", "banque", "crédit", "3000$", "2500$", "argent",
    "carte", "intelligent", "multiplies", "premiers", "doublée",
    "5000$", "gères", "augmentent", "risque", "grands",
    "opportunité", "zéro", "mentalité", "système", "dette",
    "s'enrichissent", "dettes",
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
    if not os.path.exists(clean_vox_wav):
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

    beat_phase = (t_arr % BEAT_SEC) / BEAT_SEC
    sub_f = 55.0 + 48.0 * np.exp(-beat_phase * 24.0)
    sub_kick = np.sin(2 * np.pi * sub_f * (t_arr % BEAT_SEC)) * np.exp(-beat_phase * 7.5) * 0.042

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

    whoosh_in = make_whoosh(0.36, 150, 1900, vol=0.095)
    whoosh_out = make_whoosh(0.32, 180, 1500, vol=0.080)
    for t_in in [0.02, 5.58, 7.75, 10.62, 21.14, 23.44, 33.75, 39.78, 44.75, 55.38, 62.18]:
        add_at(mix, whoosh_in, t_in)
    for t_out in [12.55, 26.55, 37.72, 48.92]:
        add_at(mix, whoosh_out, t_out)

    # 3D Card & Growth Milestone Pops
    for i, t_card in enumerate([7.85, 10.75, 23.55, 24.30]):
        add_at(mix, make_ui_pop(0.09, 500 + i * 50, 940 + i * 55, vol=0.08), t_card)

    # 3D Circular Chest Badge Pops (5 unique pairs)
    badge_times = [3.48, 4.50, 15.85, 16.85, 29.45, 31.20, 51.05, 53.00, 59.10, 60.15]
    for i, tb in enumerate(badge_times):
        add_at(mix, make_ui_pop(0.095, 420 + (i % 2) * 110, 860 + (i % 2) * 140, vol=0.080), tb)

    # Single 3D Circle Shatter in Cutaway #4 (46.25s: "alors qu'en France, c'est le découvert !")
    add_at(mix, make_shatter(0.85, vol=0.125), 46.24)
    add_at(mix, make_soft_riser(1.1, vol=0.065), 62.00)

    peak = np.max(np.abs(mix))
    if peak > 0.96:
        mix = mix * (0.96 / peak)

    out_pcm = np.clip(mix * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(MIXED_WAV, SR, out_pcm)
    return MIXED_WAV


# ---------------------------------------------------------------------------
# Master Frame Router (4 Unique Cutaways + 5 Unique Chest Orb Pairs)
# ---------------------------------------------------------------------------
def compose_frame_rgb(raw_rgb, t, words, grade_overlay, midnight_bg, crimson_bg):
    # Cutaway #1 (7.80 - 12.60s): 3D Perspective Credit Card (`3 000 $` -> flips to `2 500 $`)
    if 7.80 <= t < 12.60:
        return render_3d_credit_card_cutaway(t, midnight_bg)

    # Cutaway #2 (23.48 - 26.60s): 3D Perspective Credit Growth (`2 500 $` -> `5 000 $`)
    if 23.48 <= t < 26.60:
        return render_3d_growth_cutaway(t, midnight_bg)

    # Cutaway #3 (44.80 - 49.00s): 125-Shard 3D Sphere Shatter ("S'enrichir grâce aux dettes" -> "En France : le découvert !")
    if 44.80 <= t < 49.00:
        return render_shatter_decouvert_cutaway(t, midnight_bg, crimson_bg)

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

    # 3. Five 100% Unique Chest Orb Pairs (Zero repeated icons!)
    # Pair 1 (3.44 - 5.58s): "Tu vas à la banque..." -> `bank` + `key`
    if 3.44 <= t < 5.58:
        if t < 4.50:
            place_badge(frame, "bank", cx=540, cy=1505, radius=105, t=t, t_appear=3.48, t_end=5.56)
        else:
            slide_p = ease_out_cubic(clamp((t - 4.50) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "bank", cx=lx, cy=1505, radius=105, t=t, t_appear=3.48, t_end=5.56)
            place_badge(frame, "key", cx=678, cy=1505, radius=105, t=t, t_appear=4.50, t_end=5.56)

    # Pair 2 (15.80 - 18.48s): "Si t'es intelligent, les 2 500 $ tu les multiplies" -> `bulb` + `multiply`
    if 15.80 <= t < 18.48:
        if t < 16.85:
            place_badge(frame, "bulb", cx=540, cy=1505, radius=105, t=t, t_appear=15.85, t_end=18.45)
        else:
            slide_p = ease_out_cubic(clamp((t - 16.85) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "bulb", cx=lx, cy=1505, radius=105, t=t, t_appear=15.85, t_end=18.45)
            place_badge(frame, "multiply", cx=678, cy=1505, radius=105, t=t, t_appear=16.85, t_end=18.45)

    # Pair 3 (29.40 - 33.75s): "plus la banque prend le risque, plus tu rentres dans la cour des grands" -> `shield` + `crown`
    if 29.40 <= t < 33.75:
        if t < 31.20:
            place_badge(frame, "shield", cx=540, cy=1505, radius=105, t=t, t_appear=29.45, t_end=33.72)
        else:
            slide_p = ease_out_cubic(clamp((t - 31.20) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "shield", cx=lx, cy=1505, radius=105, t=t, t_appear=29.45, t_end=33.72)
            place_badge(frame, "crown", cx=678, cy=1505, radius=105, t=t, t_appear=31.20, t_end=33.72)

    # Pair 4 (51.00 - 55.35s): "ils te donnent un crédit et le reste c'est toi qui gères" -> `sliders` + `check`
    if 51.00 <= t < 55.35:
        if t < 53.00:
            place_badge(frame, "sliders", cx=540, cy=1505, radius=105, t=t, t_appear=51.05, t_end=55.32)
        else:
            slide_p = ease_out_cubic(clamp((t - 53.00) / 0.28))
            lx = int(540 - slide_p * 138)
            place_badge(frame, "sliders", cx=lx, cy=1505, radius=105, t=t, t_appear=51.05, t_end=55.32)
            place_badge(frame, "check", cx=678, cy=1505, radius=105, t=t, t_appear=53.00, t_end=55.32)

    # Pair 5 (59.05 - 62.15s): "pas de maison, pas de voiture, t'as tout ruiné" -> `house_slash` + `car_slash`
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
    sample_times = [0.9, 4.9, 9.2, 11.6, 17.5, 22.4, 25.2, 30.2, 32.2, 35.8, 41.8, 45.6, 46.5, 47.6, 54.0, 60.8]
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
