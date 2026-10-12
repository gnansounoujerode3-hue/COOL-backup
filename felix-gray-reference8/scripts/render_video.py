#!/usr/bin/env python3
"""
Master 1080x1920 (9:16, 30.00 fps) Video Renderer for `Video brut 8.mp4`
Inspired by `reference 8.mp4` (Luxury Minimalist / Iman Gadzhi Editing Style).
"""
import json
import math
import os
import subprocess
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
W, H = 1080, 1920
FPS = 30.0

RAW_VIDEO = "/home/user/COOL-backup/Video brut 8.mp4"
MIXED_WAV = "/tmp/work_cache/sfx_ref8/mixed_audio.wav"
WORDS_JSON = "/tmp/work_cache/whisper/brut8_master_words.json"
SPEAKER_CUTOUT_PNG = "/tmp/work_cache/inspect/speaker_bw_cutout.png"

OUT_DIR = "/home/user/COOL-backup/felix-gray-reference8/film"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_MP4 = os.path.join(OUT_DIR, "felix-gray-reference8-9x16.mp4")

FONT_ROOT = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
F_PJS_REG = f"{FONT_ROOT}/plus-jakarta-sans/400Regular/PlusJakartaSans_400Regular.ttf"
F_PJS_MED = f"{FONT_ROOT}/plus-jakarta-sans/500Medium/PlusJakartaSans_500Medium.ttf"
F_PJS_SEMI = f"{FONT_ROOT}/plus-jakarta-sans/600SemiBold/PlusJakartaSans_600SemiBold.ttf"
F_PJS_BOLD = f"{FONT_ROOT}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
F_PJS_EBOLD = f"{FONT_ROOT}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
F_INTER_LIGHT = f"{FONT_ROOT}/inter/300Light/Inter_300Light.ttf"
F_INTER_REG = f"{FONT_ROOT}/inter/400Regular/Inter_400Regular.ttf"
F_INTER_SEMI = f"{FONT_ROOT}/inter/600SemiBold/Inter_600SemiBold.ttf"
F_INTER_BOLD = f"{FONT_ROOT}/inter/700Bold/Inter_700Bold.ttf"
F_INTER_EBOLD = f"{FONT_ROOT}/inter/800ExtraBold/Inter_800ExtraBold.ttf"
F_INTER_BLACK = f"{FONT_ROOT}/inter/900Black/Inter_900Black.ttf"
F_BEBAS = f"{FONT_ROOT}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"

# Color Palette from `reference 8.mp4`
C_WHITE = (255, 255, 255)
C_LIME = (110, 204, 38)        # #6ECC26 signature chartreuse/lime highlight bar
C_BURGUNDY = (112, 10, 14)     # #700A0E deep burgundy poster accent
C_WARM_GREY = (184, 171, 160)  # #B8ABA0 luxury orbital subtext

_FONT_CACHE = {}


def get_font(path, size):
    key = (path, int(size))
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, int(size))
    return _FONT_CACHE[key]


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out_cubic(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t, s=1.35):
    t = clamp(t)
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


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
# Pre-rendered Studio Vignette & Luxury Backgrounds
# ---------------------------------------------------------------------------
def build_talking_head_luxury_overlay():
    """
    Matches `reference 8.mp4` warm studio talking-head atmosphere:
    - Subtle warm amber glow in upper background (`y=18%..48%`)
    - Deep espresso-black top vignette (`y=0..18%`) & bottom chest/lower vignette (`y=52%..100%`)
      so chest-level white + lime-green typography pops with razor-sharp contrast.
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top_dark = np.clip((H * 0.17 - yy) / (H * 0.17), 0, 1) ** 1.5 * 0.55
    bot_dark = np.clip((yy - H * 0.48) / (H * 0.52), 0, 1) ** 1.35 * 0.64
    edge_vig = np.clip(((xx - W * 0.5) / (W * 0.52)) ** 2 + ((yy - H * 0.5) / (H * 0.52)) ** 2 - 0.32, 0, 1) * 0.35

    # Warm amber studio highlight near upper wood/slats
    d_warm = np.sqrt(((xx - W * 0.48) / 520.0) ** 2 + ((yy - H * 0.28) / 380.0) ** 2)
    warm_glow = np.clip(1.0 - d_warm, 0, 1) ** 2.0 * 0.10

    dark_a = np.clip(top_dark + bot_dark + edge_vig, 0, 0.76)
    tot_a = np.clip(dark_a + warm_glow, 0.001, 0.78)
    w_warm = warm_glow / tot_a

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[:, :, 0] = np.clip(w_warm * 145 + (1 - w_warm) * 7, 0, 255).astype(np.uint8)
    rgba[:, :, 1] = np.clip(w_warm * 82 + (1 - w_warm) * 4, 0, 255).astype(np.uint8)
    rgba[:, :, 2] = np.clip(w_warm * 24 + (1 - w_warm) * 3, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(tot_a * 255.0, 0, 255).astype(np.uint8)
    return rgba


def build_offwhite_poster_bg():
    """Alabaster `#F2F2F2` paper canvas with subtle radial edge vignette for Cutaway Type B."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = np.clip(((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * 0.5) / (H * 0.62)) ** 2, 0, 1)
    val = np.clip(245 - vig * 24, 212, 246).astype(np.uint8)
    return np.stack([val, val, val], axis=-1)


def build_dark_espresso_bg():
    """Deep luxury espresso-burgundy/obsidian canvas (`#0D0504` to `#221008`) for Cutaway Type C."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d_tl = np.sqrt(((xx - 120.0) / 680.0) ** 2 + ((yy - 260.0) / 680.0) ** 2)
    d_br = np.sqrt(((xx - 960.0) / 680.0) ** 2 + ((yy - 1680.0) / 680.0) ** 2)
    glow = np.clip(np.exp(-d_tl * 1.35) * 0.65 + np.exp(-d_br * 1.35) * 0.65, 0, 1)
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    rgb[:, :, 0] = np.clip(12 + glow * 44, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(4 + glow * 24, 0, 255).astype(np.uint8)
    rgb[:, :, 2] = np.clip(3 + glow * 10, 0, 255).astype(np.uint8)
    return rgb


# ---------------------------------------------------------------------------
# Signature Element #1: 3-Line Chest Lockup with Wiping Lime-Green Bar (`#6ECC26`)
# & Partial-Letter Lime-Green Pill (`[Ad]mire` -> `[Co]nfuse`)
# ---------------------------------------------------------------------------
def draw_3line_lime_lockup(
    frame_rgb,
    t,
    t_start,
    t_end,
    top_text,
    t_top,
    mid_text,
    t_mid,
    bot_text,
    t_bot,
    center_y=1085,
):
    """
    Renders the exact `reference 8.mp4` (`t=1.50s`, `2.20s`, `3.80s`, `13.70s`) 3-line chest lockup:
    - `mid_text`: Bold white (`Plus Jakarta Sans ExtraBold`, 70px) centered at `x=540, y=center_y`
      over a wiping `#6ECC26` chartreuse/lime-green horizontal bar.
    - `top_text`: Clean white (`Plus Jakarta Sans SemiBold`, 38px) left-aligned with `mid_text` just above the bar.
    - `bot_text`: Clean white (`Plus Jakarta Sans SemiBold`, 38px) right-aligned with `mid_text` just below the bar.
    """
    if t < t_start or t > t_end:
        return
    fade_out = clamp((t_end - t) / 0.16) if t > t_end - 0.16 else 1.0
    if fade_out <= 0.01:
        return

    f_top = get_font(F_PJS_SEMI, 38)
    f_mid = get_font(F_PJS_EBOLD, 72)
    f_bot = get_font(F_PJS_SEMI, 38)

    cw, ch = 960, 320
    overlay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Measure mid_text to anchor the entire geometric lockup
    bb_mid = draw.textbbox((0, 0), mid_text, font=f_mid)
    mw = bb_mid[2] - bb_mid[0]
    mh = bb_mid[3] - bb_mid[1]
    mx = (cw - mw) // 2
    my = 105

    # 1. Wiping Lime-Green Bar behind mid_text
    if t >= t_mid:
        p_wipe = ease_out_cubic(clamp((t - t_mid) / 0.24))
        bar_pad_x = 14
        bar_x0 = mx - bar_pad_x
        bar_full_w = mw + bar_pad_x * 2
        bar_x1 = bar_x0 + int(bar_full_w * p_wipe)
        bar_y0 = my + 8
        bar_y1 = my + mh + 16
        if bar_x1 > bar_x0 + 2:
            draw.rectangle(
                [bar_x0, bar_y0, bar_x1, bar_y1],
                fill=(*C_LIME, int(255 * fade_out)),
            )

        # Mid text with crisp drop shadow
        p_mid_a = clamp((t - t_mid) / 0.14) * fade_out
        sh_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(sh_layer).text(
            (mx - bb_mid[0], my - bb_mid[1] + 4),
            mid_text,
            font=f_mid,
            fill=(0, 0, 0, int(185 * p_mid_a)),
        )
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(radius=6))
        overlay = Image.alpha_composite(overlay, sh_layer)
        draw = ImageDraw.Draw(overlay)
        draw.text(
            (mx - bb_mid[0], my - bb_mid[1]),
            mid_text,
            font=f_mid,
            fill=(255, 255, 255, int(255 * p_mid_a)),
        )

    # 2. Top-left line (`top_text`)
    if top_text and t >= t_top:
        p_top = ease_out_cubic(clamp((t - t_top) / 0.18)) * fade_out
        bb_top = draw.textbbox((0, 0), top_text, font=f_top)
        tx = mx - 4
        ty = my - (bb_top[3] - bb_top[1]) - 10 + int((1.0 - p_top) * 10)
        sh_t = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(sh_t).text(
            (tx - bb_top[0], ty - bb_top[1] + 3),
            top_text,
            font=f_top,
            fill=(0, 0, 0, int(190 * p_top)),
        )
        sh_t = sh_t.filter(ImageFilter.GaussianBlur(radius=5))
        overlay = Image.alpha_composite(overlay, sh_t)
        draw = ImageDraw.Draw(overlay)
        draw.text(
            (tx - bb_top[0], ty - bb_top[1]),
            top_text,
            font=f_top,
            fill=(255, 255, 255, int(255 * p_top)),
        )

    # 3. Bottom-right line (`bot_text`)
    if bot_text and t >= t_bot:
        p_bot = ease_out_cubic(clamp((t - t_bot) / 0.20)) * fade_out
        bb_bot = draw.textbbox((0, 0), bot_text, font=f_bot)
        bw_txt = bb_bot[2] - bb_bot[0]
        bx = mx + mw - bw_txt + 4
        by = my + mh + 22 + int((1.0 - p_bot) * 10)
        sh_b = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(sh_b).text(
            (bx - bb_bot[0], by - bb_bot[1] + 3),
            bot_text,
            font=f_bot,
            fill=(0, 0, 0, int(190 * p_bot)),
        )
        sh_b = sh_b.filter(ImageFilter.GaussianBlur(radius=5))
        overlay = Image.alpha_composite(overlay, sh_b)
        draw = ImageDraw.Draw(overlay)
        draw.text(
            (bx - bb_bot[0], by - bb_bot[1]),
            bot_text,
            font=f_bot,
            fill=(255, 255, 255, int(255 * p_bot)),
        )

    alpha_composite_roi(frame_rgb, overlay, (W - cw) // 2, center_y - 140)


def draw_partial_lime_word(frame_rgb, t, t_start, t_end, prefix, hi_chars, suffix, center_y=1085):
    """
    Renders the `[Ad]mire` (`t=2.80s` in `reference 8.mp4`) partial-letter lime-green highlight pill:
    e.g. `prefix=""`, `hi_chars="Co"`, `suffix="nfuse"` or `prefix="Not "`, `hi_chars="Lo"`, `suffix="uder"`.
    """
    if t < t_start or t > t_end:
        return
    p_in = ease_out_back(clamp((t - t_start) / 0.20), s=1.25)
    fade_out = clamp((t_end - t) / 0.14) if t > t_end - 0.14 else 1.0
    alpha_f = clamp((t - t_start) / 0.14) * fade_out
    if alpha_f <= 0.01:
        return

    font = get_font(F_PJS_BOLD, 72)
    full_text = prefix + hi_chars + suffix
    cw, ch = 900, 200
    overlay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bb_full = draw.textbbox((0, 0), full_text, font=font)
    fw = bb_full[2] - bb_full[0]
    fh = bb_full[3] - bb_full[1]
    x0 = (cw - fw) // 2
    y0 = (ch - fh) // 2 + int((1.0 - p_in) * 14)

    w_pre = draw.textbbox((0, 0), prefix, font=font)[2] if prefix else 0
    w_pre_hi = draw.textbbox((0, 0), prefix + hi_chars, font=font)[2]

    # Lime-green pill behind `hi_chars`
    wipe_p = ease_out_cubic(clamp((t - t_start) / 0.18))
    px0 = x0 + w_pre - 6
    px1 = px0 + int((w_pre_hi - w_pre + 12) * wipe_p)
    py0 = y0 + 6
    py1 = y0 + fh + 14
    if px1 > px0 + 2:
        draw.rounded_rectangle(
            [px0, py0, px1, py1],
            radius=6,
            fill=(*C_LIME, int(255 * alpha_f)),
        )

    # Drop shadow + white text
    sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(
        (x0 - bb_full[0], y0 - bb_full[1] + 4),
        full_text,
        font=font,
        fill=(0, 0, 0, int(190 * alpha_f)),
    )
    sh = sh.filter(ImageFilter.GaussianBlur(radius=6))
    overlay = Image.alpha_composite(overlay, sh)
    draw = ImageDraw.Draw(overlay)
    draw.text(
        (x0 - bb_full[0], y0 - bb_full[1]),
        full_text,
        font=font,
        fill=(255, 255, 255, int(255 * alpha_f)),
    )

    alpha_composite_roi(frame_rgb, overlay, (W - cw) // 2, center_y - ch // 2)


# ---------------------------------------------------------------------------
# Signature Element #2: Diagonal 3D Yellow Icon-Bridge Lockups
# (`The [3D Key] Secrets` at t=11.70s & `The [3D Brain] Execution` at t=21.80s)
# ---------------------------------------------------------------------------
_ICON_3D_CACHE = {}


def get_3d_key_img():
    """
    Pre-renders a large stylized 3D extruded golden-yellow key matching `t=11.70s` of `reference 8.mp4`.
    """
    if "key_3d" in _ICON_3D_CACHE:
        return _ICON_3D_CACHE["key_3d"]

    cw, ch = 440, 240
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    # Draw from bottom 3D extrusion layer up to bright yellow top face
    for depth_i in range(16, -1, -1):
        layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ox = int(depth_i * 0.5)
        oy = int(depth_i * 1.35)
        if depth_i == 0:
            col = (255, 236, 38, 255)   # Bright golden yellow face
        elif depth_i < 5:
            col = (230, 182, 12, 255)
        else:
            col = (182, 132, 4, 255)    # Deep golden-amber 3D extrusion

        # Bow (circular ring on left)
        bx, by, br = 128 + ox, 110 + oy, 64
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=col)
        # Shaft extending right
        d.rounded_rectangle([bx + 36, by - 20, bx + 235, by + 16], radius=10, fill=col)
        # Key teeth hanging down on the right
        d.rounded_rectangle([bx + 150, by + 10, bx + 182, by + 56], radius=6, fill=col)
        d.rounded_rectangle([bx + 196, by + 10, bx + 228, by + 46], radius=6, fill=col)
        # Cutout hole inside key bow
        hole_col = (150, 108, 4, 255) if depth_i < 6 else (0, 0, 0, 0)
        if depth_i == 0:
            # Punch transparent hole through the key bow
            pass
        im = Image.alpha_composite(im, layer)

    # Punch out the inner bow hole cleanly with 3D inner rim
    arr = np.asarray(im).copy()
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    hole_dist = np.sqrt((xx - 122.0) ** 2 + (yy - 110.0) ** 2)
    inner_rim = (hole_dist >= 22.0) & (hole_dist <= 30.0)
    arr[inner_rim, 0] = 175
    arr[inner_rim, 1] = 126
    arr[inner_rim, 2] = 6
    hole_clear = hole_dist < 22.0
    arr[hole_clear, 3] = 0
    im = Image.fromarray(arr)

    # Add warm golden outer glow + drop shadow
    glow = im.filter(ImageFilter.GaussianBlur(radius=18))
    g_arr = np.asarray(glow).copy()
    g_arr[:, :, 0] = 255
    g_arr[:, :, 1] = 215
    g_arr[:, :, 2] = 30
    g_arr[:, :, 3] = (g_arr[:, :, 3].astype(np.float32) * 0.55).astype(np.uint8)
    out = Image.alpha_composite(Image.fromarray(g_arr), im)

    _ICON_3D_CACHE["key_3d"] = out
    return out


def get_3d_brain_img():
    """
    Pre-renders the stylized 3D yellow-lime cel-shaded brain illustration matching `t=21.80s` of `reference 8.mp4`.
    """
    if "brain_3d" in _ICON_3D_CACHE:
        return _ICON_3D_CACHE["brain_3d"]

    cw, ch = 380, 290
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    lobes = [
        (135, 130, 56),
        (168, 96, 54),
        (216, 94, 56),
        (250, 126, 54),
        (242, 166, 50),
        (196, 174, 52),
        (148, 166, 48),
    ]

    # 1. 3D Extrusion layers (olive-gold depth)
    for depth_i in range(14, -1, -1):
        layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ox = int(depth_i * 0.45)
        oy = int(depth_i * 1.25)
        col = (232, 255, 68, 255) if depth_i == 0 else ((154, 182, 18, 255) if depth_i < 6 else (102, 122, 8, 255))
        for lx, ly, lr in lobes:
            d.ellipse([lx - lr + ox, ly - lr + oy, lx + lr + ox, ly + lr + oy], fill=col)
        im = Image.alpha_composite(im, layer)

    # 2. Bold dark cel-shaded gyri / sulci contour lines across the brain face (exact match to t=21.80s!)
    d = ImageDraw.Draw(im)
    sulci_col = (28, 32, 10, 255)
    # Outer lobe accent arcs
    for lx, ly, lr in lobes:
        d.arc([lx - lr, ly - lr, lx + lr, ly + lr], start=195, end=340, fill=sulci_col, width=5)
    # Internal brain fold squiggles
    folds = [
        [(122, 128), (154, 118), (176, 136), (162, 156)],
        [(168, 86), (192, 112), (218, 102), (232, 124)],
        [(192, 138), (218, 132), (238, 148), (222, 168)],
        [(142, 156), (174, 152), (195, 168)],
        [(214, 78), (206, 106), (182, 122)],
    ]
    for pts in folds:
        d.line(pts, fill=sulci_col, width=6, joint="curve")

    # 3. Warm yellow-lime outer aura
    glow = im.filter(ImageFilter.GaussianBlur(radius=18))
    g_arr = np.asarray(glow).copy()
    g_arr[:, :, 0] = 225
    g_arr[:, :, 1] = 255
    g_arr[:, :, 2] = 65
    g_arr[:, :, 3] = (g_arr[:, :, 3].astype(np.float32) * 0.50).astype(np.uint8)
    out = Image.alpha_composite(Image.fromarray(g_arr), im)

    _ICON_3D_CACHE["brain_3d"] = out
    return out


def draw_diagonal_icon_bridge(
    frame_rgb,
    t,
    t_start,
    t_end,
    top_left_word,
    t_tl,
    icon_kind,
    t_icon,
    bot_right_word,
    t_br,
    center_y=1100,
):
    """
    Renders the diagonal `The [3D Key] Secrets` (`t=11.70s`) and `The [3D Brain] Execution` (`t=21.80s`)
    chest lockup from `reference 8.mp4`:
    - `top_left_word` at upper-left of icon
    - 3D yellow icon (`key_3d` or `brain_3d`) in center with 3D perspective turn/float
    - `bot_right_word` overlapping the lower-right of icon
    """
    if t < t_start or t > t_end:
        return
    fade_out = clamp((t_end - t) / 0.16) if t > t_end - 0.16 else 1.0
    if fade_out <= 0.01:
        return

    font = get_font(F_PJS_BOLD, 64)

    # 1. Top-Left Word (`The` / `Small` / `Private` / `One`)
    if t >= t_tl:
        dt_tl = t - t_tl
        p_tl = ease_out_back(clamp(dt_tl / 0.22), s=1.3)
        a_tl = clamp(dt_tl / 0.15) * fade_out
        cw, ch = 520, 150
        tl_im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d_tl = ImageDraw.Draw(tl_im)
        bb = d_tl.textbbox((0, 0), top_left_word, font=font)
        tw = bb[2] - bb[0]
        tx = cw - tw - 30
        ty = 35 + int((1.0 - p_tl) * 16)
        sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((tx - bb[0], ty - bb[1] + 4), top_left_word, font=font, fill=(0, 0, 0, int(195 * a_tl)))
        sh = sh.filter(ImageFilter.GaussianBlur(radius=6))
        tl_im = Image.alpha_composite(tl_im, sh)
        ImageDraw.Draw(tl_im).text((tx - bb[0], ty - bb[1]), top_left_word, font=font, fill=(255, 255, 255, int(255 * a_tl)))
        alpha_composite_roi(frame_rgb, tl_im, 50, center_y - 175)

    # 2. Center 3D Icon (`key_3d` or `brain_3d`) with 3D turn & float
    if t >= t_icon:
        dt_ic = t - t_icon
        p_ic = ease_out_back(clamp(dt_ic / 0.28), s=1.45)
        base_ic = get_3d_key_img() if icon_kind == "key_3d" else get_3d_brain_img()
        # Simulate 3D Y-axis turn via horizontal cosine scale + slight Z-tilt (just like the rotating 3D key at 10.9-12.2s!)
        turn_x = 0.88 + 0.12 * math.cos(dt_ic * 2.6)
        nw = max(8, int(base_ic.width * p_ic * turn_x))
        nh = max(8, int(base_ic.height * p_ic))
        ic_use = base_ic.resize((nw, nh), Image.Resampling.BILINEAR)
        rot_deg = math.sin(dt_ic * 2.2) * 4.5
        ic_use = ic_use.rotate(rot_deg, resample=Image.Resampling.BILINEAR, expand=True)
        if fade_out < 0.99:
            arr = np.asarray(ic_use).copy()
            arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * fade_out).astype(np.uint8)
            ic_use = Image.fromarray(arr)
        alpha_composite_roi(frame_rgb, ic_use, int(525 - ic_use.width / 2), int(center_y - ic_use.height / 2 + 8))

    # 3. Bottom-Right Word (`Secrets` / `Execution` -> `Promises` / `Repetition` / `System`)
    if t >= t_br:
        dt_br = t - t_br
        p_br = ease_out_back(clamp(dt_br / 0.22), s=1.3)
        a_br = clamp(dt_br / 0.15) * fade_out
        cw, ch = 580, 150
        br_im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d_br = ImageDraw.Draw(br_im)
        bb = d_br.textbbox((0, 0), bot_right_word, font=font)
        tx = 25
        ty = 30 + int((1.0 - p_br) * 16)
        sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((tx - bb[0], ty - bb[1] + 5), bot_right_word, font=font, fill=(0, 0, 0, int(210 * a_br)))
        sh = sh.filter(ImageFilter.GaussianBlur(radius=7))
        br_im = Image.alpha_composite(br_im, sh)
        ImageDraw.Draw(br_im).text((tx - bb[0], ty - bb[1]), bot_right_word, font=font, fill=(255, 255, 255, int(255 * a_br)))
        alpha_composite_roi(frame_rgb, br_im, 475, center_y + 18)


# ---------------------------------------------------------------------------
# Cutaway Type A: Stark White (`#FAFAFA`) Minimalist Kinetic Screen
# (`So / which one is it?` at t=4.60s-6.10s in `reference 8.mp4`)
# ---------------------------------------------------------------------------
def render_stark_white_cutaway(t, t_start, t_end, big_word, sub_words_spec):
    """
    Renders the pure stark white (`#FAFAFA`) minimalist screen from `reference 8.mp4`:
    - Giant condensed black display word (`big_word`, e.g., `Not`, `Hype`, `STABLE`) in the center
      with the signature bottom 30% smooth vertical white fade!
    - Directly below `big_word`, small clean black sans words (`sub_words_spec`) reveal word-by-word
      with a soft unblur entrance!
    """
    frame = np.full((H, W, 3), 250, dtype=np.uint8)
    dt = t - t_start
    p_in = ease_out_cubic(clamp(dt / 0.26))

    # 1. Giant condensed black display word with bottom 30% vertical gradient fade
    f_big = get_font(F_BEBAS, 255)
    cw, ch = 900, 340
    big_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    db = ImageDraw.Draw(big_layer)
    bb = db.textbbox((0, 0), big_word, font=f_big)
    bw = bb[2] - bb[0]
    bh = bb[3] - bb[1]
    bx = (cw - bw) // 2 - bb[0]
    by = (ch - bh) // 2 - bb[1] + int((1.0 - p_in) * 24)
    db.text((bx, by), big_word, font=f_big, fill=(10, 10, 10, 255))

    # Apply the signature vertical bottom fade mask (matching `So` at t=5.10s & 5.90s!)
    arr = np.asarray(big_layer).copy()
    y_top_glyph = (ch - bh) // 2
    y_bot_glyph = y_top_glyph + bh
    yy = np.arange(ch, dtype=np.float32)[:, None]
    fade_start = y_top_glyph + bh * 0.62
    fade_mask = np.clip((y_bot_glyph - yy) / max(1.0, (y_bot_glyph - fade_start)), 0.0, 1.0) ** 1.35
    arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * fade_mask * p_in).astype(np.uint8)
    big_im = Image.fromarray(arr)
    if dt < 0.14:
        big_im = big_im.filter(ImageFilter.GaussianBlur(radius=(1.0 - dt / 0.14) * 8.0))

    alpha_composite_roi(frame, big_im, (W - cw) // 2, H // 2 - 220)

    # 2. Word-by-word black sans subtitle directly underneath `big_word`
    f_sub = get_font(F_PJS_MED, 42)
    full_sub = " ".join(w for _, w in sub_words_spec)
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tot_w = dummy.textbbox((0, 0), full_sub, font=f_sub)[2]
    cur_x = (W - tot_w) // 2
    sub_y = H // 2 + 32

    sub_layer = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sub_layer)
    space_w = dummy.textbbox((0, 0), " ", font=f_sub)[2]

    for w_appear, w_str in sub_words_spec:
        ww = dummy.textbbox((0, 0), w_str, font=f_sub)[2]
        if t >= w_appear:
            w_dt = t - w_appear
            w_a = int(clamp(w_dt / 0.18) * 255)
            w_dy = int((1.0 - ease_out_cubic(clamp(w_dt / 0.18))) * 10)
            ds.text((cur_x, 25 + w_dy), w_str, font=f_sub, fill=(18, 18, 18, w_a))
        cur_x += ww + space_w

    alpha_composite_roi(frame, sub_layer, 0, sub_y)
    return frame


# ---------------------------------------------------------------------------
# Cutaway Type B: Off-White (`#F2F2F2`) Editorial Poster with Deep Burgundy Circles
# & High-Contrast B&W Speaker Cutout (`t=6.40s - 10.50s` in `reference 8.mp4`)
# ---------------------------------------------------------------------------
def render_burgundy_poster_cutaway(t, t_start, t_end, poster_bg, speaker_cutout):
    """
    Renders the Off-White Editorial Poster (`23.96s - 29.35s`) matching `t=6.40s - 10.50s`
    (`Iman Gadzhi / Long-Form Editing Style`) in `reference 8.mp4`:
    - Deep Burgundy (`#6E090D`) bold header `Settled Confidence` + black subtitle `Quiet • Boring • Repeatable`
    - 4 Deep Burgundy (`#700A0E`) 3D-shaded circles scaling & floating in background
    - Surgical Black & White cutout portrait of the speaker rising smoothly in foreground
    """
    dt = t - t_start
    dur = t_end - t_start
    u = clamp(dt / dur)
    p_enter = ease_out_cubic(clamp(dt / 0.48))

    canvas = Image.fromarray(poster_bg.copy()).convert("RGBA")

    # 1. Top Centered Header (`Settled Confidence` + `Quiet  •  Boring  •  Repeatable`)
    hdr_layer = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hdr_layer)
    f_title = get_font(F_PJS_EBOLD, 66)
    f_sub = get_font(F_PJS_REG, 36)

    title_str = "Settled Confidence"
    bb_t = hd.textbbox((0, 0), title_str, font=f_title)
    tw = bb_t[2] - bb_t[0]
    tx = (W - tw) // 2 - bb_t[0]
    ty = 110 + int((1.0 - p_enter) * -24)

    # Subtle drop shadow on burgundy title
    sh_t = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    ImageDraw.Draw(sh_t).text((tx, ty + 4), title_str, font=f_title, fill=(0, 0, 0, int(55 * p_enter)))
    sh_t = sh_t.filter(ImageFilter.GaussianBlur(radius=6))
    hdr_layer = Image.alpha_composite(hdr_layer, sh_t)
    hd = ImageDraw.Draw(hdr_layer)
    hd.text((tx, ty), title_str, font=f_title, fill=(*C_BURGUNDY, int(255 * p_enter)))

    # Subtitle builds progressively as he says "It's quiet (25.90), it's boring (27.14), it's repeatable (28.38)"
    if t < 25.85:
        sub_str = "Is Different From Hype"
    elif t < 27.05:
        sub_str = "It's Quiet"
    elif t < 28.25:
        sub_str = "It's Quiet  •  It's Boring"
    else:
        sub_str = "It's Quiet  •  It's Boring  •  It's Repeatable"

    bb_s = hd.textbbox((0, 0), sub_str, font=f_sub)
    sw = bb_s[2] - bb_s[0]
    sx = (W - sw) // 2 - bb_s[0]
    sy = 192
    hd.text((sx, sy), sub_str, font=f_sub, fill=(24, 24, 24, int(255 * p_enter)))
    canvas.alpha_composite(hdr_layer, (0, 0))

    # 2. Deep Burgundy Circles with Soft Drop Shadows (scaling & drifting smoothly)
    c_main_r = int(385 * (0.78 + 0.22 * p_enter) + u * 18)
    circles = [
        (540, int(1090 - p_enter * 25), c_main_r),
        (int(1045 - u * 25), int(640 + u * 30), int(205 * p_enter)),
        (int(1020 - u * 18), int(1120 - u * 25), int(145 * p_enter)),
        (int(92 + u * 16), int(1490 - u * 22), int(88 * p_enter)),
    ]
    for cx, cy, r in circles:
        if r <= 4:
            continue
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([cx - r - 8, cy - r + 14, cx + r - 8, cy + r + 14], fill=(0, 0, 0, 82))
        sh = sh.filter(ImageFilter.GaussianBlur(radius=16))
        canvas = Image.alpha_composite(canvas, sh)
        fg_c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(fg_c).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*C_BURGUNDY, 255))
        canvas = Image.alpha_composite(canvas, fg_c)

    # 3. Foreground High-Contrast B&W Speaker Cutout (rising + unblurring like t=6.40s -> 6.85s!)
    zoom_s = 0.98 + 0.05 * u
    nw = int(speaker_cutout.width * zoom_s)
    nh = int(speaker_cutout.height * zoom_s)
    sp_im = speaker_cutout.resize((nw, nh), Image.Resampling.BILINEAR)
    if dt < 0.35:
        blur_r = (1.0 - dt / 0.35) * 9.0
        sp_im = sp_im.filter(ImageFilter.GaussianBlur(radius=blur_r))

    sp_x = (W - nw) // 2
    sp_y = int(H - nh + (1.0 - p_enter) * 110)
    canvas.alpha_composite(sp_im, (sp_x, sp_y))

    return np.asarray(canvas.convert("RGB"))


# ---------------------------------------------------------------------------
# Cutaway Type C: Dark Luxury Espresso-Gold Orbital Arcs & Glowing Nodes
# (`Luxurious and Minimalistic / Animations incorporated in / the video` at t=14.50s-19.65s)
# ---------------------------------------------------------------------------
def render_luxury_orbital_cutaway(t, t_start, t_end, headline, sub1, sub2, espresso_bg):
    """
    Renders the Dark Luxury Espresso-Gold Orbital Arcs cutaway from `reference 8.mp4` (`14.50s - 19.65s`):
    - Translucent golden-bronze circular domes at top-left & bottom-right with `#A87E34` 2.5px rims
    - Bright glowing warm-gold light nodes (`#FFF6D6` core + `#E6A832` bloom) riding along the rims
    - Left-aligned Bold White headline + Warm Grey 2-line subtitle in the center
    """
    dt = t - t_start
    dur = t_end - t_start
    u = clamp(dt / dur)
    p_in = ease_out_cubic(clamp(dt / 0.35))

    canvas = Image.fromarray(espresso_bg.copy()).convert("RGBA")

    # Top-left dome & Bottom-right dome parameters
    tl_cx, tl_cy, tl_r = int(95 + u * 25), int(235 + u * 20), 430
    br_cx, br_cy, br_r = int(985 - u * 25), int(1710 - u * 20), 440

    dome_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dome_layer)

    for cx, cy, r in [(tl_cx, tl_cy, tl_r), (br_cx, br_cy, br_r)]:
        dd.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(76, 48, 14, 108),
            outline=(168, 126, 52, 215),
            width=3,
        )

    canvas = Image.alpha_composite(canvas, dome_layer)

    # Glowing Golden-White Nodes orbiting along each rim
    # Top-left node travels from angle 35 deg to 82 deg
    ang_tl = math.radians(32.0 + u * 52.0)
    nx1 = tl_cx + math.cos(ang_tl) * tl_r
    ny1 = tl_cy + math.sin(ang_tl) * tl_r

    # Bottom-right node travels from angle 212 deg to 264 deg
    ang_br = math.radians(212.0 + u * 52.0)
    nx2 = br_cx + math.cos(ang_br) * br_r
    ny2 = br_cy + math.sin(ang_br) * br_r

    node_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(node_layer)
    for nx, ny in [(nx1, ny1), (nx2, ny2)]:
        # Outer warm golden bloom
        nd.ellipse([nx - 42, ny - 42, nx + 42, ny + 42], fill=(230, 168, 48, 95))
        nd.ellipse([nx - 22, ny - 22, nx + 22, ny + 22], fill=(255, 210, 95, 165))
    node_layer = node_layer.filter(ImageFilter.GaussianBlur(radius=14))
    nd_sharp = ImageDraw.Draw(node_layer)
    for nx, ny in [(nx1, ny1), (nx2, ny2)]:
        nd_sharp.ellipse([nx - 9, ny - 9, nx + 9, ny + 9], fill=(255, 248, 220, 255))

    canvas = Image.alpha_composite(canvas, node_layer)

    # Center Left-Aligned Luxury Minimalist Typography (matching t=16.50s in reference 8.mp4)
    txt_layer = Image.new("RGBA", (W, 320), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    f_h = get_font(F_PJS_BOLD, 44)
    f_s = get_font(F_INTER_LIGHT, 34)

    tx = 145 + int((1.0 - p_in) * 28)
    alpha_t = int(clamp(dt / 0.24) * 255)
    td.text((tx, 40), headline, font=f_h, fill=(255, 255, 255, alpha_t))

    alpha_s = int(clamp((dt - 0.10) / 0.26) * 255)
    if alpha_s > 0:
        td.text((tx, 102), sub1, font=f_s, fill=(*C_WARM_GREY, alpha_s))
        td.text((tx, 146), sub2, font=f_s, fill=(*C_WARM_GREY, alpha_s))

    if dt < 0.22:
        txt_layer = txt_layer.filter(ImageFilter.GaussianBlur(radius=(1.0 - dt / 0.22) * 6.0))

    canvas.alpha_composite(txt_layer, (0, 860))
    return np.asarray(canvas.convert("RGB"))


# ---------------------------------------------------------------------------
# Camera Framing & Ken Burns Schedule for Talking-Head Shots
# ---------------------------------------------------------------------------
def get_camera_crop(frame_rgb, t):
    """
    Alternates between Wide (`1.00x`), Medium (`1.14x`), and Close-Up (`1.20x`) framing
    with smooth Ken Burns drift across talking-head segments.
    """
    if t < 4.26:
        u = t / 4.26
        zoom = 1.00 + 0.03 * u
        cx, cy = 0.50, 0.47
    elif t < 7.90:
        u = (t - 4.26) / (7.90 - 4.26)
        zoom = 1.14 + 0.025 * clamp(u)
        cx, cy = 0.50, 0.44
    elif t < 12.08:
        u = (t - 7.90) / (12.08 - 7.90)
        zoom = 1.20 - 0.02 * clamp(u)
        cx, cy = 0.50, 0.43
    elif t < 19.22:
        u = (t - 15.78) / (19.22 - 15.78)
        zoom = 1.12 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.45
    elif t < 32.65:
        u = (t - 29.35) / (32.65 - 29.35)
        zoom = 1.02 + 0.025 * clamp(u)
        cx, cy = 0.50, 0.47
    elif t < 35.15:
        u = (t - 32.65) / (35.15 - 32.65)
        zoom = 1.15 + 0.02 * clamp(u)
        cx, cy = 0.50, 0.44
    elif t < 38.80:
        u = (t - 35.15) / (38.80 - 35.15)
        zoom = 1.21 - 0.02 * clamp(u)
        cx, cy = 0.50, 0.43
    elif t < 43.10:
        u = (t - 38.80) / (43.10 - 38.80)
        zoom = 1.04 + 0.03 * clamp(u)
        cx, cy = 0.50, 0.46
    elif t < 45.84:
        u = (t - 43.10) / (45.84 - 43.10)
        zoom = 1.16 + 0.02 * clamp(u)
        cx, cy = 0.50, 0.44
    elif t < 49.75:
        u = (t - 45.84) / (49.75 - 45.84)
        zoom = 1.10 + 0.025 * clamp(u)
        cx, cy = 0.50, 0.45
    elif t < 58.30:
        u = (t - 53.85) / (58.30 - 53.85)
        zoom = 1.15 - 0.02 * clamp(u)
        cx, cy = 0.50, 0.44
    elif t < 60.12:
        u = (t - 58.30) / (60.12 - 58.30)
        zoom = 1.22 - 0.01 * clamp(u)
        cx, cy = 0.50, 0.43
    elif t < 67.80:
        u = (t - 64.95) / (67.80 - 64.95)
        zoom = 1.13 + 0.02 * clamp(u)
        cx, cy = 0.50, 0.45
    else:
        u = (t - 67.80) / (70.70 - 67.80)
        zoom = 1.06 - 0.04 * clamp(u)
        cx, cy = 0.50, 0.46

    sh, sw, _ = frame_rgb.shape
    cw = sw / zoom
    ch = sh / zoom
    x0 = int(clamp(cx * sw - cw / 2, 0, sw - cw))
    y0 = int(clamp(cy * sh - ch / 2, 0, sh - ch))
    crop = frame_rgb[y0 : y0 + int(ch), x0 : x0 + int(cw)]
    return np.asarray(Image.fromarray(crop).resize((W, H), Image.Resampling.BILINEAR))


# ---------------------------------------------------------------------------
# Frame Compositor (Used for both Preview Verification & Full Video Render)
# ---------------------------------------------------------------------------
class LuxuryVideoCompositor:
    def __init__(self):
        self.words = json.load(open(WORDS_JSON))
        self.luxury_overlay = build_talking_head_luxury_overlay()
        self.poster_bg = build_offwhite_poster_bg()
        self.espresso_bg = build_dark_espresso_bg()
        self.speaker_cutout = Image.open(SPEAKER_CUTOUT_PNG).convert("RGBA")

    def render_frame(self, raw_rgb, t):
        # 1. Cutaway #1 (12.08 - 15.78s): Stark White Minimalist Kinetic Screen
        if 12.08 <= t < 13.86:
            return render_stark_white_cutaway(
                t,
                12.08,
                13.86,
                "Not",
                [(12.10, "that's"), (12.40, "not"), (12.55, "confidence.")],
            )
        if 13.86 <= t < 15.78:
            return render_stark_white_cutaway(
                t,
                13.86,
                15.78,
                "Hype",
                [(13.88, "my"), (13.98, "friend,"), (14.10, "that's"), (14.28, "intensity.")],
            )

        # 2. Cutaway #2 (19.22 - 23.96s): Dark Luxury Espresso-Gold Orbital Arcs & Nodes
        if 19.22 <= t < 21.36:
            return render_luxury_orbital_cutaway(
                t,
                19.22,
                21.36,
                "Spikes When Things Go Well",
                "Driven by temporary emotion",
                "instead of real discipline",
                self.espresso_bg,
            )
        if 21.36 <= t < 23.96:
            return render_luxury_orbital_cutaway(
                t,
                21.36,
                23.96,
                "Disappears Under Pressure",
                "When things get hard and",
                "pressure finally shows up",
                self.espresso_bg,
            )

        # 3. Cutaway #3 (23.96 - 29.35s): Off-White Editorial Poster + Burgundy Circles + B&W Speaker Cutout
        if 23.96 <= t < 29.35:
            return render_burgundy_poster_cutaway(
                t,
                23.96,
                29.35,
                self.poster_bg,
                self.speaker_cutout,
            )

        # 4. Cutaway #4 (49.75 - 53.85s): Dark Luxury Espresso-Gold Orbital Arcs (bridges 49.27s jump cut)
        if 49.75 <= t < 53.85:
            return render_luxury_orbital_cutaway(
                t,
                49.75,
                53.85,
                "Tired of Rebuilding Confidence",
                "Starting over every few months",
                "without a repeatable system",
                self.espresso_bg,
            )

        # 5. Cutaway #5 (60.12 - 64.95s): Stark White Minimalist Kinetic Screen ("STABLE")
        if 60.12 <= t < 64.95:
            return render_stark_white_cutaway(
                t,
                60.12,
                64.95,
                "STABLE",
                [
                    (61.25, "Drop"),
                    (62.00, '"STABLE"'),
                    (62.85, "in"),
                    (63.85, "the"),
                    (64.04, "comments"),
                ],
            )

        # -------------------------------------------------------------------
        # Talking-Head Segments with Warm Luxury Studio Grade + Chest Graphics
        # -------------------------------------------------------------------
        frame = get_camera_crop(raw_rgb, t)
        a = self.luxury_overlay[:, :, 3:4].astype(np.float32) * (1.0 / 255.0)
        frame = np.clip(
            frame.astype(np.float32) * (1.0 - a) + self.luxury_overlay[:, :, :3].astype(np.float32) * a,
            0,
            255,
        ).astype(np.uint8)

        # Beat 1A (0.35 - 2.88s): "Confidence, my friend / [Isn't Loud] / at all"
        draw_3line_lime_lockup(
            frame, t, 0.35, 2.88,
            "Confidence, my friend", 0.40,
            "Isn't Loud", 1.58,
            "never was", 2.15,
        )
        # Beat 1B (2.88 - 4.26s): "Real confidence / [It's Consistent] / every day"
        draw_3line_lime_lockup(
            frame, t, 2.88, 4.26,
            "Real confidence", 2.90,
            "It's Consistent", 3.06,
            "every single day", 3.55,
        )

        # Beat 2A (4.26 - 5.38s): Partial-letter lime pill "[Co]nfuse" (matches "[Ad]mire" at t=2.80s!)
        draw_partial_lime_word(frame, t, 4.26, 5.38, "", "Co", "nfuse")

        # Beat 2B (5.38 - 7.90s): "Confidence / [With Volume] / on the outside"
        draw_3line_lime_lockup(
            frame, t, 5.38, 7.90,
            "Confidence", 5.38,
            "With Volume", 5.96,
            "on the outside", 6.92,
        )

        # Beat 3 (7.90 - 12.08s): "[Ch]est out" -> "[Bi]g talk" -> "Big goals / [Big Energy] / all for show"
        draw_partial_lime_word(frame, t, 7.90, 8.92, "", "Ch", "est out")
        draw_partial_lime_word(frame, t, 8.92, 9.80, "", "Bi", "g talk")
        draw_3line_lime_lockup(
            frame, t, 9.80, 12.08,
            "Big goals", 9.80,
            "Big Energy", 10.58,
            "all for show", 11.15,
        )

        # Beat 5A (15.78 - 19.22s): "Fake confidence / [Is Emotional] / and fragile"
        draw_3line_lime_lockup(
            frame, t, 15.78, 19.22,
            "Fake confidence", 15.88,
            "Is Emotional", 17.16,
            "and fragile", 18.12,
        )

        # Beat 7A (29.35 - 32.65s): "It looks like / [Showing Up] / when you said you would"
        draw_3line_lime_lockup(
            frame, t, 29.35, 32.65,
            "It looks like", 29.48,
            "Showing Up", 30.06,
            "when you said you would", 31.18,
        )

        # Beat 7B (32.65 - 35.15s): Diagonal 3D Golden Key Bridge Lockup ("Small [3D Key] Promises")
        draw_diagonal_icon_bridge(
            frame, t, 32.65, 35.15,
            "Small", 32.78,
            "key_3d", 32.94,
            "Promises", 33.30,
        )

        # Beat 7C (35.15 - 38.80s): "Staying / [Steady] / when you don't feel like it"
        draw_3line_lime_lockup(
            frame, t, 35.15, 38.80,
            "Staying", 35.18,
            "Steady", 35.50,
            "when you don't feel like it", 36.66,
        )

        # Beat 8A (38.80 - 41.10s): Partial-letter lime pill "Not [Lo]uder"
        draw_partial_lime_word(frame, t, 38.85, 41.10, "Not ", "Lo", "uder")

        # Beat 8B (41.10 - 43.10s): "You need to be / [Consistent] / every single day"
        draw_3line_lime_lockup(
            frame, t, 41.10, 43.10,
            "You need to be", 41.20,
            "Consistent", 41.80,
            "every single day", 42.30,
        )

        # Beat 8C (43.10 - 45.84s): "Never built in / [Hype Moments] / or quick highs"
        draw_3line_lime_lockup(
            frame, t, 43.10, 45.84,
            "Never built in", 43.26,
            "Hype Moments", 45.10,
            "or quick highs", 45.45,
        )

        # Beat 8D (45.84 - 49.75s): Diagonal 3D Yellow Brain Bridge Lockup ("Private [3D Brain] Repetition")
        draw_diagonal_icon_bridge(
            frame, t, 45.84, 49.75,
            "Private", 46.15,
            "brain_3d", 46.50,
            "Repetition", 48.10,
        )

        # Beat 9B (53.85 - 58.30s): "Live Webinar • 8:30 / [March 14th] / breaking this down deep"
        draw_3line_lime_lockup(
            frame, t, 53.85, 58.30,
            "Live Webinar  •  8:30", 53.95,
            "March 14th", 55.16,
            "breaking this down deep", 56.68,
        )

        # Beat 9C (58.30 - 60.12s): Diagonal 3D Golden Key Bridge Lockup ("Fix The [3D Key] System")
        draw_diagonal_icon_bridge(
            frame, t, 58.30, 60.12,
            "Fix The", 58.45,
            "key_3d", 58.88,
            "System", 59.55,
        )

        # Beat 10B (64.95 - 67.80s): "Stop chasing / [The Hype] / starting today"
        draw_3line_lime_lockup(
            frame, t, 64.95, 67.80,
            "Stop chasing", 65.10,
            "The Hype", 65.84,
            "starting today", 66.40,
        )

        # Beat 10C (67.80 - 70.70s): Final Signature Diagonal 3D Yellow Brain Lockup ("One [3D Brain] System")
        draw_diagonal_icon_bridge(
            frame, t, 67.80, 70.70,
            "One", 68.10,
            "brain_3d", 68.48,
            "System", 69.30,
        )

        return frame


def render_preview_grid():
    """Renders a 14-frame verification grid in ~3 seconds to inspect every key visual beat."""
    comp = LuxuryVideoCompositor()
    sample_times = [
        2.3,   # Beat 1: "Confidence, my friend / [Isn't Loud] / never was"
        4.8,   # Beat 2A: "[Co]nfuse" partial lime-green pill
        7.2,   # Beat 2B: "Confidence / [With Volume] / on the outside"
        13.1,  # Beat 4A: Cutaway Type A Stark White "Not / that's not confidence."
        15.1,  # Beat 4B: Cutaway Type A Stark White "Hype / my friend, that's intensity."
        20.5,  # Beat 5B: Cutaway Type C Dark Luxury Espresso-Gold Orbital Arcs & Nodes
        24.2,  # Beat 6: Cutaway Type B Burgundy Poster entrance (blur -> sharp)
        28.6,  # Beat 6: Cutaway Type B Burgundy Poster full ("Settled Confidence / It's Quiet • It's Boring • It's Repeatable")
        31.8,  # Beat 7A: "It looks like / [Showing Up] / when you said you would"
        34.1,  # Beat 7B: Diagonal 3D Golden Key ("Small [3D Key] Promises")
        48.6,  # Beat 8D: Diagonal 3D Yellow Brain ("Private [3D Brain] Repetition")
        56.9,  # Beat 9B: "Live Webinar • 8:30 / [March 14th] / breaking this down deep"
        64.3,  # Beat 10A: Stark White "STABLE / Drop 'STABLE' in the comments"
        69.8,  # Beat 10C: Final Diagonal 3D Yellow Brain ("One [3D Brain] System")
    ]
    thumbs = []
    for ts in sample_times:
        raw_bytes = subprocess.check_output([
            "ffmpeg", "-v", "error", "-ss", str(ts),
            "-i", RAW_VIDEO, "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
        ])
        raw_rgb = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((1280, 720, 3))
        out_rgb = comp.render_frame(raw_rgb, ts)
        im = Image.fromarray(out_rgb).resize((360, 640), Image.Resampling.BILINEAR)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 140, 36], fill=(0, 0, 0))
        d.text((8, 8), f"t = {ts:.2f}s", fill=(110, 255, 80))
        thumbs.append(im)

    sheet = Image.new("RGB", (360 * 7, 640 * 2))
    for i, im in enumerate(thumbs):
        r, c = divmod(i, 7)
        sheet.paste(im, (c * 360, r * 640))
    out_grid = "/tmp/work_cache/inspect/out8_preview_grid.jpg"
    sheet.save(out_grid, quality=92)
    print(f"Saved preview verification grid to {out_grid}")


def render_full_video():
    t0 = time.time()
    comp = LuxuryVideoCompositor()

    dec_cmd = [
        "ffmpeg", "-v", "error", "-i", RAW_VIDEO,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    dec_proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, bufsize=720 * 1280 * 3 * 4)

    enc_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30",
        "-i", "-", "-i", MIXED_WAV,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
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
        frame = comp.render_frame(raw_rgb, t)
        enc_proc.stdin.write(frame.tobytes())
        frame_idx += 1
        if frame_idx % 300 == 0:
            el = time.time() - t0
            print(f"  Rendered {frame_idx}/2121 frames ({frame_idx/el:.1f} fps)...")

    dec_proc.stdout.close()
    dec_proc.wait()
    enc_proc.stdin.close()
    enc_proc.wait()

    el = time.time() - t0
    sz_mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"Done! Rendered {frame_idx} frames in {el:.1f}s -> {OUT_MP4} ({sz_mb:.2f} MB)")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        render_preview_grid()
    else:
        render_full_video()
