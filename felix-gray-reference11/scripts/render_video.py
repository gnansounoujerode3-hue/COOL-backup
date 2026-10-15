#!/usr/bin/env python3
"""
Master 9:16 Video Compositor for `video brut 11.mp4` (`felix-gray-reference11`)
Inspired directly by `reference 11.mp4` and governed by `MOTION-DESIGN.md`
+ `.claude/skills/motion-code-harvester/scripts/motion_engine.py`.

Signature Visual & Motion Grammar of `reference 11.mp4`:
  1. Two-Tier Chest Typography Lockup:
     - Upper line: Bold ALL-CAPS Pure White Sans-Serif (`Plus Jakarta Sans ExtraBold`)
       entering with directional horizontal motion-blur slide (`t=14.0s`, `t=36.5s` of ref11).
     - Lower overlapping line: Glowing Electric Cyan (`#54F2E8`) Calligraphic Script
       (`Great Vibes`) with multi-octave neon cyan outer bloom (`Instagram`, `new people`,
       `views`, `followers`, `within your niche`, `their followers` style).
  2. 3-Box Cyan-Bordered Rounded Icon Row (`t=2.5s-3.0s` of ref11):
     - Three dark-glass rounded squares (`border: 2.5px solid #54F2E8` + cyan outer glow)
       popping in below the script with a 60ms stagger (`cubic-bezier(0.2, 0.8, 0.2, 1.0)`),
       containing animated cyan vector icons.
  3. Tilted Cyan Numbered Step Badge (`t=3.5s`, `t=17.5s`, `t=35.0s` of ref11):
     - A tilted (`-18 deg`) dark rounded-square badge with a glowing `#54F2E8` border
       and bold cyan number (`1`, `2`, `3`) popping in on the left of the speaker's chest.
  4. 3D Folder Stamp & Rising Laptop Cutout Props (`t=20.5s`, `t=22.0s` of ref11):
     - 3D Manila Dossier Folder with red stamp (`[MINDSET]`) + rising dark-mode Laptop UI
       transitioning into the full-screen dark cyan-grid cutaway.
  5. Full-Screen Dark Teal-Cyan Grid + 3D Tilted Dark-Mode Mobile UI Cutaway
     (`t=5.5s-12.5s` & `t=38.0s-45.0s` of ref11):
     - Deep dark teal-black background (`#050C0E`) with `#0E2830` coordinate grid lines.
     - Dark-mode iOS Settings/Audit screen sliding in with vertical motion blur,
       tilting in 3D perspective (`warp_plane_3d`) with an Electric Cyan highlight bar
       (`#3CE6DC`) and interactive iOS toggle switches flipping ON + typewriter text.
  6. 5-Person White Silhouette Crowd Row (`t=15.5s-17.0s` of ref11) &
     3-Column Social Profile Card Fan -> Hero Profile Card Zoom with Cascading Silhouettes
     (`t=30.0s-34.5s` & `t=45.5s-46.5s` of ref11).
"""

import argparse
import math
import os
import subprocess
import sys
import wave
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
from motion_engine import (
    cubic_bezier,
    expo_in_out,
    expo_out,
    power3_in,
    power4_in,
    power4_out,
    nudge_curve_3phase,
    waterfall_word_state,
    zoom_through_seam,
    cut_the_curve_seam,
    rack_focus_blur_cut,
)

W, H = 1080, 1920
FPS = 30.0

PROJECT_DIR = "/home/user/COOL-backup/felix-gray-reference11"
RAW_VIDEO = "/home/user/COOL-backup/video brut 11.mp4"
AUDIO_DIR = f"{PROJECT_DIR}/assets/audio"
FILM_DIR = f"{PROJECT_DIR}/film"
MIXED_WAV = f"{AUDIO_DIR}/master_audio_mix.wav"
OUT_MP4 = f"{FILM_DIR}/felix-gray-reference11-9x16.mp4"

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
MONTSERRAT_BLACK = f"{FONT_BASE}/montserrat/900Black/Montserrat_900Black.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"

# Exact `reference 11.mp4` Color Palette
C_CYAN = (84, 242, 232)         # #54F2E8 signature electric cyan script & border glow
C_CYAN_DEEP = (32, 188, 182)    # #20BCB6 deep cyan accent
C_BLUE_BTN = (56, 151, 240)     # #3897F0 social follow button blue
C_GRID_BG = (5, 12, 15)         # #050C0F dark teal-black UI cutaway background
C_GRID_LINE = (15, 42, 48)      # #0F2A30 dark cyan coordinate grid line
C_CARD_BG = (18, 22, 26)        # #12161A dark rounded card background
C_WHITE = (255, 255, 255)
C_RED_STAMP = (232, 44, 56)

_FONT_CACHE = {}


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
    return cubic_bezier(clamp(p), 0.2, 0.8, 0.2, 1.0)


def ease_out_back(t: float, s: float = 1.45) -> float:
    t = clamp(t) - 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def data_reveal_state(age: float, delay: float = 0.0, dur: float = 0.46, offset_y: float = 28.0):
    t_local = age - delay
    if t_local <= 0.0:
        return 0.0, offset_y
    p = clamp(t_local / max(1e-4, dur))
    e = ease_motion(p)
    return e, offset_y * (1.0 - e)


# ---------------------------------------------------------------------------
# 3D Projective Homography (`threejs-camera-controls-and-rigs`)
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
) -> Image.Image:
    w, h = img.size
    cx, cy = w * 0.5, h * 0.5
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)

    cx_r, sx_r = math.cos(rx), math.sin(rx)
    cy_r, sy_r = math.cos(ry), math.sin(ry)
    cz_r, sz_r = math.cos(rz), math.sin(rz)

    Rx = np.array([[1, 0, 0], [0, cx_r, -sx_r], [0, sx_r, cx_r]], dtype=np.float64)
    Ry = np.array([[cy_r, 0, sy_r], [0, 1, 0], [-sy_r, 0, cy_r]], dtype=np.float64)
    Rz = np.array([[cz_r, -sz_r, 0], [sz_r, cz_r, 0], [0, 0, 1]], dtype=np.float64)
    R = Rz @ Ry @ Rx

    corners = np.array(
        [[-cx, -cy, 0.0], [cx, -cy, 0.0], [cx, cy, 0.0], [-cx, cy, 0.0]],
        dtype=np.float64,
    ) * max(0.15, scale)

    src_pts = [(0.0, 0.0), (float(w), 0.0), (float(w), float(h)), (0.0, float(h))]
    dst_pts = []
    for pt in corners:
        p3 = R @ pt
        z = max(200.0, focal + p3[2])
        u = cx + (p3[0] * focal) / z
        v = cy + (p3[1] * focal) / z
        dst_pts.append((u, v))

    coeffs = _solve_perspective_coeffs(src_pts, dst_pts)
    return img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)


# ---------------------------------------------------------------------------
# Pre-built Avatars & Dark Cyan Grid Background (`reference 11.mp4`)
# ---------------------------------------------------------------------------
_CACHE = {}


def get_dark_grid_bg() -> Image.Image:
    """Matches `reference 11.mp4` (`t=6.0s-12.5s`, `38.0s-45.0s`) dark teal-cyan grid."""
    if "grid_bg" in _CACHE:
        return _CACHE["grid_bg"].copy()
    bg = Image.new("RGBA", (W, H), (*C_GRID_BG, 255))
    d = ImageDraw.Draw(bg)
    step = 72
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=(*C_GRID_LINE, 255), width=2)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=(*C_GRID_LINE, 255), width=2)
    # Soft radial cyan ambient glow in center
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([140, 320, W - 140, H - 320], fill=(18, 82, 88, 65))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=90))
    bg = Image.alpha_composite(bg, glow)
    _CACHE["grid_bg"] = bg
    return bg.copy()


def extract_andrew_avatar(raw_rgb: np.ndarray, size: int = 120) -> Image.Image:
    """Creates a circular portrait avatar of Andrew for the `reference 11` profile cards."""
    im = Image.fromarray(raw_rgb)
    if "face_avatar" not in _CACHE:
        crop = im.crop((190, 240, 910, 1140)).resize((size, size), Image.LANCZOS)
        _CACHE["face_avatar"] = crop
    av = _CACHE["face_avatar"].resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(av, (0, 0), mask)
    return out


# ---------------------------------------------------------------------------
# Camera Grading with Subtle `reference 11` Cyan-Blue Studio Rim Glow
# ---------------------------------------------------------------------------
def grade_ref11_talking_head(raw_rgb: np.ndarray, t: float, zoom: float = 1.0) -> Image.Image:
    f = raw_rgb.astype(np.float32)
    f = (f - 128.0) * 1.10 + 124.0
    graded = np.clip(f, 0, 255).astype(np.uint8)
    im = Image.fromarray(graded).convert("RGBA")

    # Subtle continuous breathing zoom
    z = zoom + 0.018 * math.sin(t * 0.9)
    if abs(z - 1.0) > 0.002:
        nw, nh = int(round(W * z)), int(round(H * z))
        im_z = im.resize((nw, nh), Image.BILINEAR)
        x0 = (nw - W) // 2
        y0 = int((nh - H) * 0.36)
        im = im_z.crop((x0, y0, x0 + W, y0 + H))

    # Subtle cyan-blue studio rim glow on top-left & top-right + dark chest vignette
    # so the white sans + glowing cyan script at chest level pops like `reference 11.mp4`
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = np.clip((yy - H * 0.42) / (H * 0.58), 0.0, 1.0) ** 1.25 * 0.62
    arr = np.array(im, dtype=np.float32)
    arr[:, :, :3] *= (1.0 - vig[:, :, None])

    # Top-corner cyan studio reflection
    d_tl = np.exp(-(((xx - 120.0) / 380.0) ** 2 + ((yy - 180.0) / 340.0) ** 2)) * 0.16
    d_tr = np.exp(-(((xx - 960.0) / 380.0) ** 2 + ((yy - 180.0) / 340.0) ** 2)) * 0.16
    cyan_rim = (d_tl + d_tr)[:, :, None]
    arr[:, :, 0] = np.clip(arr[:, :, 0] + cyan_rim[:, :, 0] * 30.0, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + cyan_rim[:, :, 0] * 210.0, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] + cyan_rim[:, :, 0] * 235.0, 0, 255)

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------------------
# Signature `reference 11.mp4` Visual Primitives
# ---------------------------------------------------------------------------
def draw_ref11_chest_lockup(
    canvas: Image.Image,
    age: float,
    upper_caps: str,
    lower_script: str = "",
    lower_caps_cyan: str = "",
    cy: int = 1040,
    slide_from_left: bool = True,
):
    """
    Renders the exact `reference 11.mp4` 2-tier chest lockup:
      - Upper line: Bold ALL-CAPS white sans-serif (`NEVER POST ON`, `TO REACH MORE`,
        `OTHER ACCOUNTS`, `YOU'RE STEALING`) with horizontal motion-blur slide entry.
      - Lower line: Overlapping Glowing Electric Cyan (`#54F2E8`) Calligraphic Script
        (`Instagram`, `new people`, `views`, `within your niche`) OR glowing cyan
        ALL-CAPS (`ON A COMPUTER`).
    """
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    f_caps = get_font(JAKARTA_EBOLD, 68)
    f_script = get_font(GREAT_VIBES, 122)
    f_cyan_caps = get_font(JAKARTA_EBOLD, 66)

    # Soft dark chest backdrop for crisp legibility
    bg_dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bg_dark).ellipse([90, cy - 110, W - 90, cy + 250], fill=(0, 0, 0, int(145 * clamp(age / 0.20))))
    bg_dark = bg_dark.filter(ImageFilter.GaussianBlur(radius=38))
    canvas.alpha_composite(bg_dark)

    # 1. Upper ALL-CAPS white line with directional slide (`t=14.0s`, `36.5s` of ref11)
    p_up = ease_motion(clamp(age / 0.34))
    if p_up > 0.02 and upper_caps:
        bb_u = od.textbbox((0, 0), upper_caps, font=f_caps)
        uw = bb_u[2] - bb_u[0]
        dir_sign = -1 if slide_from_left else 1
        ux = (W - uw) // 2 + int(dir_sign * (1.0 - p_up) * 140)
        uy = cy

        # Horizontal motion-blur trail during fast slide-in (age < 0.22s)
        if age < 0.22:
            blur_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(blur_layer)
            for trail_i in range(1, 5):
                tx = ux - dir_sign * trail_i * 18
                bd.text((tx, uy - bb_u[1]), upper_caps, font=f_caps, fill=(255, 255, 255, int(70 * (1.0 - trail_i * 0.2))))
            overlay = Image.alpha_composite(overlay, blur_layer)
            od = ImageDraw.Draw(overlay)

        od.text((ux + 3, uy - bb_u[1] + 4), upper_caps, font=f_caps, fill=(0, 0, 0, int(215 * p_up)))
        od.text((ux, uy - bb_u[1]), upper_caps, font=f_caps, fill=(255, 255, 255, int(255 * p_up)))

    # 2A. Lower overlapping Electric Cyan Script (`#54F2E8` with neon cyan bloom)
    scr_age = max(0.0, age - 0.10)
    if lower_script and scr_age > 0.0:
        p_s = ease_out_back(clamp(scr_age / 0.38), s=1.25)
        a_s = clamp(scr_age / 0.24)
        bb_s = od.textbbox((0, 0), lower_script, font=f_script)
        sw = bb_s[2] - bb_s[0]
        sx = (W - sw) // 2
        sy = int(cy + 42 + (1.0 - p_s) * 24)

        # Multi-octave Electric Cyan outer glow (`reference 11` signature!)
        glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.text((sx, sy - bb_s[1]), lower_script, font=f_script, fill=(*C_CYAN, int(235 * a_s)))
        glow_wide = glow_layer.filter(ImageFilter.GaussianBlur(radius=22))
        glow_tight = glow_layer.filter(ImageFilter.GaussianBlur(radius=7))
        overlay = Image.alpha_composite(overlay, glow_wide)
        overlay = Image.alpha_composite(overlay, glow_tight)
        od = ImageDraw.Draw(overlay)

        od.text((sx + 2, sy - bb_s[1] + 3), lower_script, font=f_script, fill=(0, 25, 28, int(210 * a_s)))
        od.text((sx, sy - bb_s[1]), lower_script, font=f_script, fill=(*C_CYAN, int(255 * a_s)))
        # Subtle bright white-cyan core highlight
        od.text((sx, sy - bb_s[1]), lower_script, font=f_script, fill=(215, 255, 252, int(130 * a_s)))

    # 2B. Lower Electric Cyan ALL-CAPS (`ON A COMPUTER` style at `t=22.0s` of ref11)
    if lower_caps_cyan and scr_age > 0.0:
        p_c = ease_motion(clamp(scr_age / 0.34))
        bb_c = od.textbbox((0, 0), lower_caps_cyan, font=f_cyan_caps)
        cw = bb_c[2] - bb_c[0]
        cx = (W - cw) // 2
        cy_c = int(cy + 74 + (1.0 - p_c) * 22)

        glow_c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow_c).text((cx, cy_c - bb_c[1]), lower_caps_cyan, font=f_cyan_caps, fill=(*C_CYAN, int(210 * p_c)))
        glow_c = glow_c.filter(ImageFilter.GaussianBlur(radius=16))
        overlay = Image.alpha_composite(overlay, glow_c)
        od = ImageDraw.Draw(overlay)
        od.text((cx + 3, cy_c - bb_c[1] + 4), lower_caps_cyan, font=f_cyan_caps, fill=(0, 0, 0, int(215 * p_c)))
        od.text((cx, cy_c - bb_c[1]), lower_caps_cyan, font=f_cyan_caps, fill=(*C_CYAN, int(255 * p_c)))

    canvas.alpha_composite(overlay)


def draw_tilted_step_badge(
    canvas: Image.Image,
    age: float,
    step_num: str,
    cx: int = 215,
    cy: int = 960,
    tilt_deg: float = -18.0,
):
    """
    Renders the exact `reference 11.mp4` (`t=3.5s`, `t=17.5s`, `t=35.0s`) tilted dark
    rounded-square badge with glowing cyan border and bold cyan number (`1`, `2`, `3`).
    """
    if age <= 0.0:
        return
    p = ease_out_back(clamp(age / 0.34), s=1.55)
    a = clamp(age / 0.18)
    size = 156
    badge = Image.new("RGBA", (size + 60, size + 60), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bx0, by0 = 30, 30
    bd.rounded_rectangle([bx0, by0, bx0 + size, by0 + size], radius=34, fill=(14, 22, 26, int(242 * a)), outline=(*C_CYAN, int(255 * a)), width=4)

    # Outer cyan glow
    glow = badge.filter(ImageFilter.GaussianBlur(radius=12))
    badge = Image.alpha_composite(glow, badge)
    bd = ImageDraw.Draw(badge)

    f_num = get_font(JAKARTA_EBOLD, 86)
    bb = bd.textbbox((0, 0), step_num, font=f_num)
    nx = bx0 + (size - (bb[2] - bb[0])) // 2
    ny = by0 + (size - (bb[3] - bb[1])) // 2 - bb[1]
    bd.text((nx, ny), step_num, font=f_num, fill=(*C_CYAN, int(255 * a)))

    rotated = badge.rotate(tilt_deg, resample=Image.BICUBIC, expand=True)
    rw, rh = rotated.size
    sw = max(16, int(round(rw * p)))
    sh = max(16, int(round(rh * p)))
    scaled = rotated.resize((sw, sh), Image.BILINEAR)
    canvas.alpha_composite(scaled, (cx - sw // 2, cy - sh // 2))


def draw_three_cyan_icon_boxes(canvas: Image.Image, age: float, cy: int = 1265, t: float = 0.0):
    """
    Renders the exact `reference 11.mp4` (`t=2.5s-3.0s`) row of 3 dark rounded-square
    boxes with glowing `#54F2E8` borders and spinning cyan gear/compass icons.
    """
    if age <= 0.0:
        return
    box_s = 132
    gap = 42
    total_w = 3 * box_s + 2 * gap
    start_x = (W - total_w) // 2

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(3):
        b_age = age - i * 0.065  # 65ms stagger (`MOTION-DESIGN.md`)
        if b_age <= 0.0:
            continue
        p = ease_out_back(clamp(b_age / 0.34), s=1.4)
        a = clamp(b_age / 0.20)
        bx = start_x + i * (box_s + gap)
        by = int(cy + (1.0 - p) * 34)

        card = Image.new("RGBA", (box_s + 32, box_s + 32), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([16, 16, 16 + box_s, 16 + box_s], radius=28, fill=(14, 22, 26, int(240 * a)), outline=(*C_CYAN, int(255 * a)), width=3)

        # Draw spinning cyan gear icon inside each box (exact match to ref11 t=2.5s-3.0s)
        icx, icy = 16 + box_s // 2, 16 + box_s // 2
        angle_base = t * 2.2 + i * 0.8
        r_outer = 32
        r_inner = 22
        for tooth in range(8):
            ang = angle_base + tooth * (math.pi / 4.0)
            x1 = icx + int(r_inner * math.cos(ang))
            y1 = icy + int(r_inner * math.sin(ang))
            x2 = icx + int((r_outer + 6) * math.cos(ang))
            y2 = icy + int((r_outer + 6) * math.sin(ang))
            cd.line([(x1, y1), (x2, y2)], fill=(*C_CYAN, int(255 * a)), width=7)
        cd.ellipse([icx - r_inner, icy - r_inner, icx + r_inner, icy + r_inner], fill=(14, 22, 26, int(255 * a)), outline=(*C_CYAN, int(255 * a)), width=5)
        cd.ellipse([icx - 9, icy - 9, icx + 9, icy + 9], fill=(*C_CYAN, int(255 * a)))

        glow = card.filter(ImageFilter.GaussianBlur(radius=8))
        card = Image.alpha_composite(glow, card)
        overlay.alpha_composite(card, (bx - 16, by - 16))

    canvas.alpha_composite(overlay)


def draw_user_silhouette_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0, alpha: int = 255):
    """Draws a 3D-shaded white user bust silhouette matching `reference 11.mp4` (`t=15.5s-17.0s`, `33.5s`)."""
    hr = max(4, int(round(22 * scale)))
    bw = max(8, int(round(38 * scale)))
    bh = max(6, int(round(30 * scale)))
    # Soft drop shadow
    draw.ellipse([cx - hr + 2, cy - hr - int(18 * scale) + 3, cx + hr + 2, cy + hr - int(18 * scale) + 3], fill=(0, 0, 0, int(alpha * 0.45)))
    # Shoulders / torso dome
    draw.pieslice([cx - bw, cy + int(6 * scale), cx + bw, cy + int(6 * scale) + bh * 2], 180, 360, fill=(242, 246, 250, alpha))
    # Head sphere
    draw.ellipse([cx - hr, cy - hr - int(18 * scale), cx + hr, cy + hr - int(18 * scale)], fill=(255, 255, 255, alpha))


def draw_five_silhouettes_row(canvas: Image.Image, age: float, cy: int = 1265):
    """Matches `reference 11.mp4` (`t=15.5s-17.0s`) row of 5 white 3D user silhouettes."""
    if age <= 0.0:
        return
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    spacing = 82
    start_x = W // 2 - 2 * spacing
    for i in range(5):
        s_age = age - i * 0.055
        if s_age <= 0.0:
            continue
        p = ease_out_back(clamp(s_age / 0.32), s=1.45)
        a = int(clamp(s_age / 0.18) * 255)
        sx = start_x + i * spacing
        sy = int(cy + (1.0 - p) * 28)
        draw_user_silhouette_icon(od, sx, sy, scale=1.08, alpha=a)
    canvas.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# SCENE 1 (0.00s - 4.00s): Hook + White Sans / Cyan Script + 3 Gear Boxes + Badge "1"
# "I remember my father coming up to me and he just put his hand on my shoulder and he says..."
# ---------------------------------------------------------------------------
def render_scene1_hook(raw_rgb: np.ndarray, t: float) -> Image.Image:
    # Cache Andrew's face from the close-up frame for later profile cards
    if "face_avatar" not in _CACHE and t > 0.4:
        _CACHE["face_avatar"] = Image.fromarray(raw_rgb).crop((190, 240, 910, 1140)).resize((160, 160), Image.LANCZOS)

    base = grade_ref11_talking_head(raw_rgb, t, zoom=1.02)

    if t < 1.65:
        draw_ref11_chest_lockup(
            base,
            age=max(0.0, t - 0.04),
            upper_caps="I REMEMBER MY",
            lower_script="Father coming up",
            cy=1175,
            slide_from_left=True,
        )
        # Floating tilted 3D badge on the right of the script (matching tilted icon in ref11 t=0.5s-2.0s)
        p_ico = ease_out_back(clamp((t - 0.12) / 0.36), s=1.45)
        if p_ico > 0.02:
            ico = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
            idraw = ImageDraw.Draw(ico)
            idraw.rounded_rectangle([18, 18, 122, 122], radius=28, fill=(214, 31, 38, 245), outline=(*C_CYAN, 255), width=4)
            f_ev = get_font(JAKARTA_EBOLD, 44)
            idraw.text((34, 42), "E&V", font=f_ev, fill=(255, 255, 255, 255))
            rot_ico = ico.rotate(-14.0, resample=Image.BICUBIC, expand=True)
            base.alpha_composite(rot_ico, (825, int(1180 + (1.0 - p_ico) * 26)))
    else:
        age_b = t - 1.65
        draw_ref11_chest_lockup(
            base,
            age=age_b,
            upper_caps="HAND ON MY",
            lower_script="Shoulder",
            cy=1155,
            slide_from_left=False,
        )
        # 3 cyan-bordered gear boxes popping in (`t=2.5s-3.0s` of ref11)
        draw_three_cyan_icon_boxes(base, age=max(0.0, t - 2.05), cy=1395, t=t)

        # At t=3.25s ("and he says..."), pop in the tilted cyan `1` badge on the left (`t=3.5s` of ref11)
        if t >= 3.20:
            draw_tilted_step_badge(base, age=t - 3.20, step_num="1", cx=195, cy=1090, tilt_deg=-18.0)

    return base


# ---------------------------------------------------------------------------
# SCENE 2 (4.00s - 5.85s): Wide Armchair + Docked Badge "1" + 3D Secret/Mindset Folder Prop
# "...'Get over it.'"
# ---------------------------------------------------------------------------
def render_scene2_get_over_it(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 4.00
    base = grade_ref11_talking_head(raw_rgb, t, zoom=1.0)

    # Docked tilted badge `1` right above the left edge of the text (`t=4.0s` of ref11!)
    draw_tilted_step_badge(base, age=0.5 + age, step_num="1", cx=235, cy=985, tilt_deg=-16.0)

    draw_ref11_chest_lockup(
        base,
        age=age,
        upper_caps="HE TOLD ME",
        lower_script="Get over it",
        cy=1015,
        slide_from_left=True,
    )

    # 3D Manila Dossier Folder with red "[MINDSET]" stamp below the text (`t=20.5s` of ref11!)
    f_age = max(0.0, age - 0.16)
    if f_age > 0.0:
        p_f = ease_out_back(clamp(f_age / 0.38), s=1.4)
        fw, fh = 260, 200
        folder = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        fd = ImageDraw.Draw(folder)
        # Back tab + white paper sheets + front golden-tan folder cover
        fd.rounded_rectangle([24, 18, 125, 60], radius=10, fill=(215, 168, 78, 255))
        fd.rounded_rectangle([24, 34, fw - 24, fh - 20], radius=14, fill=(215, 168, 78, 255))
        fd.polygon([(34, 46), (fw - 30, 32), (fw - 26, fh - 34), (30, fh - 34)], fill=(248, 248, 252, 255))
        fd.polygon([(20, 62), (fw - 18, 48), (fw - 24, fh - 18), (24, fh - 18)], fill=(238, 192, 98, 255), outline=(255, 224, 140, 255), width=2)
        # Red "[MINDSET]" stamp
        stamp = Image.new("RGBA", (180, 64), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        sd.rounded_rectangle([4, 4, 176, 60], radius=8, outline=(*C_RED_STAMP, 245), width=4)
        sd.text((20, 14), "MINDSET", font=get_font(JAKARTA_EBOLD, 30), fill=(*C_RED_STAMP, 245))
        stamp_rot = stamp.rotate(14.0, resample=Image.BICUBIC, expand=True)
        folder.alpha_composite(stamp_rot, (32, 58))

        fy = int(1225 + (1.0 - p_f) * 36)
        base.alpha_composite(folder, ((W - fw) // 2, fy))

    return base


# ---------------------------------------------------------------------------
# SCENE 3 (5.85s - 7.22s): Close-Up Punch-In + Cyan ALL-CAPS + Rising 3D Laptop UI
# "And I said, 'What?'"
# ---------------------------------------------------------------------------
def render_scene3_what_laptop(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 5.85
    base = grade_ref11_talking_head(raw_rgb, t, zoom=1.04)

    draw_ref11_chest_lockup(
        base,
        age=age,
        upper_caps="And I said,",
        lower_caps_cyan="“WHAT?!”",
        cy=1120,
        slide_from_left=True,
    )

    # Rising 3D Dark-Mode Laptop (`t=22.0s-22.5s` of ref11) that zooms up at the end of Scene 3
    lap_age = max(0.0, age - 0.22)
    if lap_age > 0.0:
        p_l = ease_motion(clamp(lap_age / 0.45))
        # Zoom forward into screen during last 0.25s before 7.22s cut
        zoom_push = 1.0 + 0.55 * power3_in(clamp((t - 6.92) / 0.30))
        lw, lh = int(560 * zoom_push), int(360 * zoom_push)

        lap = Image.new("RGBA", (560, 360), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lap)
        # Laptop lid/screen
        ld.rounded_rectangle([40, 12, 520, 310], radius=18, fill=(14, 18, 22, 255), outline=(120, 130, 140, 255), width=4)
        ld.rectangle([56, 28, 504, 294], fill=(8, 14, 18, 255))
        # Mini UI preview inside laptop screen
        ld.rounded_rectangle([80, 52, 480, 92], radius=8, fill=(20, 32, 38, 255))
        ld.text((98, 60), "Advisor Performance Audit", font=get_font(INTER_BOLD, 22), fill=(*C_CYAN, 255))
        for ry in (112, 162, 212):
            ld.rounded_rectangle([80, ry, 480, ry + 36], radius=6, fill=(18, 24, 30, 255), outline=(40, 65, 72, 200), width=1)
            ld.ellipse([440, ry + 8, 460, ry + 28], fill=(*C_CYAN, 240))
        # Laptop aluminum base + trackpad notch
        ld.polygon([(10, 310), (550, 310), (530, 334), (30, 334)], fill=(165, 172, 180, 255))
        ld.rounded_rectangle([235, 310, 325, 318], radius=4, fill=(110, 116, 124, 255))

        if zoom_push > 1.01:
            lap = lap.resize((lw, lh), Image.BILINEAR)
        ly = int(1340 + (1.0 - p_l) * 90 - (zoom_push - 1.0) * 260)
        base.alpha_composite(lap, ((W - lw) // 2, ly))

    return base


# ---------------------------------------------------------------------------
# SCENE 4 (7.22s - 12.50s): Full-Screen Dark Cyan-Grid + 3D Tilted iOS Dark-Mode UI
# (`reference 11.mp4` `t=5.5s-12.5s` & `t=38.0s-45.0s` style)
# "He says, 'Get over it. Did you do your job, right?' He's like, 'You did your job.
#  You did a very good job.'"
# ---------------------------------------------------------------------------
def render_scene4_dark_grid_ui(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 7.22
    canvas = get_dark_grid_bg()

    # Build the Dark-Mode iOS Settings & Performance Audit Screen (`780x1480`)
    pw, ph = 800, 1480
    phone = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(phone)

    # Phone card body
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=44, fill=(8, 10, 14, 252), outline=(45, 75, 82, 220), width=3)

    # iOS Status bar (`9:41` + signal/wifi/battery)
    f_status = get_font(INTER_BOLD, 26)
    f_hdr = get_font(INTER_BOLD, 32)
    f_sec = get_font(INTER_BOLD, 26)
    f_row = get_font(INTER_MED, 28)
    f_sub = get_font(INTER_REG, 22)

    pd.text((48, 28), "9:41", font=f_status, fill=(255, 255, 255, 255))
    pd.rounded_rectangle([pw - 96, 32, pw - 44, 56], radius=6, outline=(255, 255, 255, 220), width=2)
    pd.rectangle([pw - 92, 36, pw - 56, 52], fill=(255, 255, 255, 255))

    # Navigation header (`<   Advisor Mindset & Audit`)
    pd.text((42, 92), "‹", font=get_font(INTER_REG, 48), fill=(255, 255, 255, 255))
    pd.text((210, 102), "Settings and activity", font=f_hdr, fill=(255, 255, 255, 255))

    # Search / Live Typewriter bar (`t=10.0s-12.5s` of ref11!)
    pd.rounded_rectangle([38, 168, pw - 38, 232], radius=18, fill=(26, 30, 36, 255))
    typed_full = "Standard: Very Good Job ✓"
    if t >= 10.40:
        n_chars = min(len(typed_full), int((t - 10.40) * 18))
        typed_str = typed_full[:n_chars]
        pd.text((64, 184), typed_str, font=f_row, fill=(*C_CYAN, 255))
    else:
        pd.text((64, 184), "Q  Search advisor standards...", font=f_row, fill=(140, 148, 158, 255))

    # Section 1: Meta / Engel & Völkers Advisor Center
    pd.text((42, 262), "Your advisor standard", font=f_sec, fill=(165, 172, 182, 255))
    pd.text((pw - 180, 262), "∞ Engel & Völkers", font=f_sub, fill=(165, 172, 182, 255))

    # Highlighted Cyan Bar on the active row (`t=39.5s-41.0s` of ref11!)
    # Row 1: "Get over it" (7.22s - 7.90s)
    # Row 2: "Did you do your job?" (7.90s - 8.95s)
    # Row 3: "You did your job" (8.95s - 10.60s)
    # Row 4: "You did a very good job" (10.60s - 12.50s)
    items = [
        ("1. “Get over it”", "Release emotional attachment to outcome", 7.22),
        ("2. “Did you do your job?”", "Verify preparation, craft & client service", 7.90),
        ("3. “You did your job.”", "Process executed to professional standard", 8.95),
        ("4. “You did a very good job.”", "Excellence validated independent of result", 10.60),
    ]

    for idx, (title_s, desc_s, trigger_t) in enumerate(items):
        ry = 320 + idx * 210
        is_active = (t >= trigger_t) and (idx == len(items) - 1 or t < items[idx + 1][2])
        is_done = t >= trigger_t

        # Glowing Electric Cyan row highlight bar (exact match to `t=39.5s-41.0s` of ref11!)
        if is_active:
            p_bar = ease_motion(clamp((t - trigger_t) / 0.28))
            bar_w = int((pw - 56) * p_bar)
            pd.rounded_rectangle([28, ry - 10, 28 + bar_w, ry + 158], radius=22, fill=(*C_CYAN, 42), outline=(*C_CYAN, 235), width=3)
        else:
            pd.rounded_rectangle([28, ry - 10, pw - 28, ry + 158], radius=22, fill=(16, 20, 26, 230), outline=(38, 46, 56, 180), width=1)

        txt_col = C_CYAN if is_active else (255, 255, 255)
        pd.text((54, ry + 12), title_s, font=f_hdr, fill=(*txt_col, 255))
        pd.text((54, ry + 62), desc_s, font=f_sub, fill=(175, 182, 192, 245))

        # Interactive iOS Toggle Switch on the right (`t=26.5s` & `t=43.5s` of ref11!)
        sw_p = ease_motion(clamp((t - trigger_t) / 0.32)) if is_done else 0.0
        tx0, ty0, tw_s, th_s = pw - 148, ry + 36, 92, 52
        track_col = (
            int(55 + (56 - 55) * sw_p),
            int(62 + (151 - 62) * sw_p),
            int(72 + (240 - 72) * sw_p),
            255,
        )
        if sw_p > 0.5:
            track_col = (*C_BLUE_BTN, 255)
        pd.rounded_rectangle([tx0, ty0, tx0 + tw_s, ty0 + th_s], radius=26, fill=track_col)
        knob_x = int(tx0 + 6 + sw_p * (tw_s - 40 - 12))
        pd.ellipse([knob_x, ty0 + 6, knob_x + 40, ty0 + 46], fill=(255, 255, 255, 255))

    # Bottom Save draft / Verified Next buttons (`t=39.0s-45.0s` of ref11!)
    pd.rounded_rectangle([42, ph - 135, 385, ph - 55], radius=18, fill=(28, 34, 42, 255))
    pd.text((145, ph - 112), "Audit Log", font=f_row, fill=(255, 255, 255, 255))
    pd.rounded_rectangle([415, ph - 135, pw - 42, ph - 55], radius=18, fill=(*C_BLUE_BTN, 255))
    pd.text((525, ph - 112), "Verified ✓", font=f_row, fill=(255, 255, 255, 255))

    # iOS Home indicator bar
    pd.rounded_rectangle([pw // 2 - 90, ph - 24, pw // 2 + 90, ph - 16], radius=4, fill=(255, 255, 255, 210))

    # 3D Perspective Tilt during the middle of the scene (matching `t=39.5s-41.5s` of ref11!)
    if 7.80 <= t <= 11.20:
        tilt_env = math.sin(clamp((t - 7.80) / 3.40) * math.pi)
        rx = -7.5 * tilt_env
        ry = 11.0 * tilt_env
        rz = -2.5 * tilt_env
        phone = warp_plane_3d(phone, rx_deg=rx, ry_deg=ry, rz_deg=rz, scale=0.96)

    # Vertical motion-blur slide-in over first 0.32s (`t=5.5s` of ref11)
    p_in = ease_motion(clamp(age / 0.34))
    py = int(220 + (1.0 - p_in) * 520)
    if age < 0.25:
        phone = phone.filter(ImageFilter.BoxBlur(radius=int((1.0 - age / 0.25) * 12)))

    canvas.alpha_composite(phone, ((W - pw) // 2, py))
    return canvas


# ---------------------------------------------------------------------------
# SCENE 5 (12.50s - 16.12s): Talking-Head + Tilted Badge "2" + 5 White Silhouettes Row
# "Just because the outcome wasn't what you expected, you did a very good job."
# ---------------------------------------------------------------------------
def render_scene5_outcome_silhouettes(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 12.50
    base = grade_ref11_talking_head(raw_rgb, t, zoom=1.02)

    if t < 14.85:
        # Tilted cyan badge `2` above the left edge (`t=17.5s` of ref11)
        draw_tilted_step_badge(base, age=age, step_num="2", cx=185, cy=900, tilt_deg=-18.0)
        draw_ref11_chest_lockup(
            base,
            age=max(0.0, age - 0.08),
            upper_caps="WHEN THE OUTCOME",
            lower_script="wasn't expected",
            cy=1015,
            slide_from_left=True,
        )
    else:
        age_b = t - 14.85
        draw_ref11_chest_lockup(
            base,
            age=age_b,
            upper_caps="YOU STILL DID A",
            lower_script="very good job",
            cy=985,
            slide_from_left=False,
        )
        # Signature `reference 11` (`t=15.5s-17.0s`) row of 5 glowing white user silhouettes!
        draw_five_silhouettes_row(base, age=max(0.0, age_b - 0.08), cy=1235)

    return base


# ---------------------------------------------------------------------------
# SCENE 6 (16.12s - 22.48s): Talking-Head + Badge "3" + 3-Column Social Profile Card Fan
# -> Hero Profile Card Zoom & Cascading Followers (`t=30.0s-36.0s` of ref11!)
# "My name's Andrew Crosse. And today's Masterclass, we're going to teach you
#  how to be a mentor in real estate and how to build communities."
# ---------------------------------------------------------------------------
def build_social_profile_card(
    raw_rgb: np.ndarray,
    name: str,
    handle: str,
    btn_text: str = "Follow",
    is_following: bool = False,
    card_w: int = 260,
    card_h: int = 330,
    cyan_border: bool = False,
) -> Image.Image:
    """Builds a dark rounded social profile card matching `reference 11.mp4` (`t=30.0s-34.5s`, `46.0s`)."""
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    border_col = (*C_CYAN, 245) if cyan_border else (65, 72, 82, 210)
    cd.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=28, fill=(*C_CARD_BG, 248), outline=border_col, width=3 if cyan_border else 2)

    # Close 'x' in top-right corner (`t=30.5s-33.0s` of ref11)
    f_x = get_font(INTER_REG, int(card_w * 0.09))
    cd.text((card_w - int(card_w * 0.14), int(card_h * 0.04)), "×", font=f_x, fill=(185, 192, 202, 220))

    # Circular avatar
    av_s = int(card_w * 0.42)
    av = extract_andrew_avatar(raw_rgb, size=av_s)
    ax = (card_w - av_s) // 2
    ay = int(card_h * 0.11)
    card.alpha_composite(av, (ax, ay))
    cd.ellipse([ax - 2, ay - 2, ax + av_s + 2, ay + av_s + 2], outline=(*C_CYAN, 230), width=3)

    # Name & handle
    f_n = get_font(INTER_BOLD, max(16, int(card_w * 0.095)))
    f_h = get_font(INTER_REG, max(14, int(card_w * 0.075)))
    bb_n = cd.textbbox((0, 0), name, font=f_n)
    nx = (card_w - (bb_n[2] - bb_n[0])) // 2
    ny = ay + av_s + int(card_h * 0.06)
    cd.text((nx, ny), name, font=f_n, fill=(255, 255, 255, 255))

    bb_h = cd.textbbox((0, 0), handle, font=f_h)
    hx = (card_w - (bb_h[2] - bb_h[0])) // 2
    hy = ny + int(card_h * 0.10)
    cd.text((hx, hy), handle, font=f_h, fill=(165, 172, 182, 240))

    # Follow / Following pill button
    bw = int(card_w * 0.76)
    bh = int(card_h * 0.15)
    bx = (card_w - bw) // 2
    by = card_h - bh - int(card_h * 0.08)
    btn_col = (*C_BLUE_BTN, 255) if not is_following else (42, 168, 224, 255)
    cd.rounded_rectangle([bx, by, bx + bw, by + bh], radius=12, fill=btn_col)
    f_b = get_font(INTER_BOLD, max(15, int(card_w * 0.085)))
    bb_b = cd.textbbox((0, 0), btn_text, font=f_b)
    cd.text((bx + (bw - (bb_b[2] - bb_b[0])) // 2, by + (bh - (bb_b[3] - bb_b[1])) // 2 - bb_b[1]), btn_text, font=f_b, fill=(255, 255, 255, 255))

    return card


def render_scene6_masterclass_profiles(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 16.12
    base = grade_ref11_talking_head(raw_rgb, t, zoom=1.02)

    # Phase 6A (16.12s - 18.85s): "My name's Andrew Crosse. And today's Masterclass,"
    if t < 18.85:
        draw_tilted_step_badge(base, age=age, step_num="3", cx=185, cy=885, tilt_deg=-18.0)
        if t < 17.65:
            draw_ref11_chest_lockup(
                base,
                age=max(0.0, age - 0.10),
                upper_caps="ANDREW CROSSE",
                lower_script="Engel & Völkers",
                cy=990,
                slide_from_left=True,
            )
        else:
            draw_ref11_chest_lockup(
                base,
                age=t - 17.65,
                upper_caps="TODAY'S REAL ESTATE",
                lower_script="Masterclass",
                cy=990,
                slide_from_left=False,
            )
        return base

    # Phase 6B (18.85s - 20.85s): "we're going to teach you how to be a mentor in real estate"
    # Exact `reference 11` (`t=30.0s-31.5s`) 3-Column Social Profile Card Fan!
    if t < 20.85:
        p_age = t - 18.85
        draw_ref11_chest_lockup(
            base,
            age=p_age,
            upper_caps="BE A MENTOR",
            lower_script="in real estate",
            cy=880,
            slide_from_left=True,
        )
        profiles = [
            ("Advisor Team", "real.estate"),
            ("Andrew Crosse", "andrewcrosse"),
            ("E&V Mentors", "engelvolkers"),
        ]
        cw, ch = 268, 340
        gap = 34
        start_x = (W - (3 * cw + 2 * gap)) // 2
        for i, (p_name, p_handle) in enumerate(profiles):
            c_age = p_age - 0.18 - i * 0.08
            if c_age <= 0.0:
                continue
            p_c = ease_out_back(clamp(c_age / 0.34), s=1.35)
            card = build_social_profile_card(raw_rgb, p_name, p_handle, btn_text="Follow", card_w=cw, card_h=ch, cyan_border=(i == 1))
            cx = start_x + i * (cw + gap)
            cy = int(1120 + (1.0 - p_c) * 48)
            base.alpha_composite(card, (cx, cy))
        return base

    # Phase 6C (20.85s - 22.48s): "and how to build communities."
    # Exact `reference 11` (`t=32.0s-34.5s`) Hero Profile Card Zoom + Cascading User Silhouettes!
    z_age = t - 20.85
    draw_ref11_chest_lockup(
        base,
        age=z_age,
        upper_caps="HOW TO BUILD",
        lower_script="communities",
        cy=820,
        slide_from_left=False,
    )
    p_zoom = ease_out_back(clamp(z_age / 0.36), s=1.35)
    cw = int(268 + 112 * p_zoom)
    ch = int(340 + 130 * p_zoom)
    hero_card = build_social_profile_card(
        raw_rgb,
        "Andrew Crosse",
        "andrewcrosse",
        btn_text="Following",
        is_following=True,
        card_w=cw,
        card_h=ch,
        cyan_border=True,
    )
    hx = (W - cw) // 2
    hy = int(1045 - 20 * p_zoom)
    base.alpha_composite(hero_card, (hx, hy))

    # Cascading white 3D user silhouettes below the hero card (`t=33.5s` of ref11!)
    if z_age > 0.25:
        sil_age = z_age - 0.25
        sil_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sil_layer)
        offsets = [(-130, 0.0), (-55, 0.06), (25, 0.12), (115, 0.18), (-85, 0.24), (65, 0.30)]
        for ox, delay in offsets:
            sa = sil_age - delay
            if sa <= 0.0:
                continue
            sp = clamp(sa / 0.75)
            sx = W // 2 + ox
            sy = int(hy + ch - 40 + sp * 280)
            alpha = int(255 * math.sin(sp * math.pi))
            draw_user_silhouette_icon(sd, sx, sy, scale=0.95, alpha=alpha)
        base.alpha_composite(sil_layer)

    return base


# ---------------------------------------------------------------------------
# SCENE 7 (22.48s - 24.57s): `reference 11` Finale Follow-Card Pop + E&V End Card
# (`reference 11.mp4` `t=45.5s-46.5s` combined with the E&V Masterclass end card)
# ---------------------------------------------------------------------------
def render_scene7_outro(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 22.48
    # Keep the original white Engel & Völkers Real Estate Masterclass lockup & armchair
    im = Image.fromarray(raw_rgb).convert("RGBA")

    # Pop in the signature `reference 11` (`t=46.0s`) Cyan-Bordered Profile Follow Card
    # in the upper canvas (`y=95..520`) above the `ENGEL & VÖLKERS` logo (`y=590..960`)!
    p_card = ease_out_back(clamp(age / 0.42), s=1.35)
    cw, ch = 360, 410
    card = build_social_profile_card(
        raw_rgb,
        "Andrew Crosse",
        "Engel & Völkers Masterclass",
        btn_text="Following",
        is_following=True,
        card_w=cw,
        card_h=ch,
        cyan_border=True,
    )
    # Outer cyan glow around the card
    glow = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([16, 16, cw + 24, ch + 24], radius=32, fill=(*C_CYAN, 95))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=14))
    glow.alpha_composite(card, (20, 20))

    if age < 0.22:
        glow = glow.filter(ImageFilter.BoxBlur(radius=int((1.0 - age / 0.22) * 10)))

    cy = int(105 + (1.0 - p_card) * 85)
    im.alpha_composite(glow, ((W - (cw + 40)) // 2, cy))
    return im


# ---------------------------------------------------------------------------
# Master Frame Dispatcher + Velocity-Matched Seam Transitions
# ---------------------------------------------------------------------------
def _render_raw_scene(raw_rgb: np.ndarray, t: float) -> Image.Image:
    if t < 4.00:
        return render_scene1_hook(raw_rgb, t)
    if t < 5.85:
        return render_scene2_get_over_it(raw_rgb, t)
    if t < 7.22:
        return render_scene3_what_laptop(raw_rgb, t)
    if t < 12.50:
        return render_scene4_dark_grid_ui(raw_rgb, t)
    if t < 16.12:
        return render_scene5_outcome_silhouettes(raw_rgb, t)
    if t < 22.48:
        return render_scene6_masterclass_profiles(raw_rgb, t)
    return render_scene7_outro(raw_rgb, t)


SEAMS = [
    (4.00, 0.22, "cut_the_curve"),
    (5.85, 0.22, "zoom_through"),
    (7.22, 0.24, "zoom_through"),
    (12.50, 0.24, "rack_focus"),
    (16.12, 0.24, "cut_the_curve"),
    (22.48, 0.26, "zoom_through"),
]


def render_frame(raw_rgb: np.ndarray, prev_raw_rgb: np.ndarray, t: float) -> np.ndarray:
    for t_seam, half_w, mode in SEAMS:
        if abs(t - t_seam) <= half_w:
            p = clamp((t - (t_seam - half_w)) / (2.0 * half_w))
            rgb_a = prev_raw_rgb if t >= t_seam else raw_rgb
            rgb_b = raw_rgb if t >= t_seam else prev_raw_rgb
            im_a = _render_raw_scene(rgb_a, t_seam - 0.02)
            im_b = _render_raw_scene(rgb_b, t_seam + 0.02)
            if mode == "zoom_through":
                out = zoom_through_seam(im_a, im_b, p, inverse=False)
            elif mode == "cut_the_curve":
                out = cut_the_curve_seam(im_a, im_b, p, direction="left")
            else:
                out = rack_focus_blur_cut(im_a, im_b, p)
            return np.array(out.convert("RGB"), dtype=np.uint8)

    im = _render_raw_scene(raw_rgb, t)
    return np.array(im.convert("RGB"), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Procedural SFX & Audio Mixer (synchronized to `reference 11` pops, clicks & whooshes)
# ---------------------------------------------------------------------------
def build_master_audio_mix(ffmpeg_exe: str):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    orig_wav = f"{AUDIO_DIR}/orig_48k.wav"
    subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i",
            RAW_VIDEO,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            orig_wav,
        ],
        check=True,
        capture_output=True,
    )

    with wave.open(orig_wav, "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    speech = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0
    total_samples = speech.shape[0]
    t = np.arange(total_samples, dtype=np.float32) / float(sr)

    # Subtle modern dark-cyan synth pulse pad (-25 dB)
    pad_l = 0.015 * np.sin(2 * np.pi * 65.41 * t) + 0.010 * np.sin(2 * np.pi * 130.81 * t + 0.4)
    pad_r = 0.015 * np.sin(2 * np.pi * 65.41 * t) + 0.010 * np.sin(2 * np.pi * 196.00 * t - 0.3)

    sfx_l = np.zeros_like(t)
    sfx_r = np.zeros_like(t)

    cues = [
        (0.08, "whoosh"),
        (1.65, "whoosh"),
        (2.05, "click"),
        (2.12, "click"),
        (2.19, "click"),
        (3.20, "pop"),
        (4.00, "whoosh"),
        (4.20, "pop"),
        (5.85, "hit"),
        (6.10, "whoosh"),
        (7.22, "whoosh"),
        (7.90, "click"),
        (8.95, "click"),
        (10.60, "click"),
        (12.50, "whoosh"),
        (14.85, "pop"),
        (16.12, "whoosh"),
        (18.85, "whoosh"),
        (19.05, "click"),
        (19.13, "click"),
        (19.21, "click"),
        (20.85, "hit"),
        (22.48, "whoosh"),
    ]
    rng = np.random.default_rng(11)
    for cue_t, kind in cues:
        i0 = int(cue_t * sr)
        if i0 >= total_samples:
            continue
        if kind == "whoosh":
            dur_s = int(0.28 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.6
            noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32)
            sweep = np.sin(2 * np.pi * (110.0 + 280.0 * lt) * lt * 0.28)
            w_sig = (0.042 * sweep + 0.016 * noise) * env
            sfx_l[i0:i1] += w_sig * (1.0 - 0.3 * lt)
            sfx_r[i0:i1] += w_sig * (0.7 + 0.3 * lt)
        elif kind == "hit":
            dur_s = int(0.34 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-lt * 8.5)
            sub = 0.072 * np.sin(2 * np.pi * (92.0 * np.exp(-lt * 2.2)) * lt * 0.34) * env
            sfx_l[i0:i1] += sub
            sfx_r[i0:i1] += sub
        elif kind == "pop":
            dur_s = int(0.08 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-lt * 16.0)
            pop = 0.055 * np.sin(2 * np.pi * (420.0 + 380.0 * lt) * lt * 0.08) * env
            sfx_l[i0:i1] += pop
            sfx_r[i0:i1] += pop
        elif kind == "click":
            dur_s = int(0.04 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-lt * 26.0)
            clk = 0.048 * np.sin(2 * np.pi * 1450.0 * lt * 0.04) * env
            sfx_l[i0:i1] += clk
            sfx_r[i0:i1] += clk

    mix_l = np.clip(speech[:, 0] * 1.12 + pad_l + sfx_l, -0.98, 0.98)
    mix_r = np.clip(speech[:, 1] * 1.12 + pad_r + sfx_r, -0.98, 0.98)
    stereo_int16 = (np.stack([mix_l, mix_r], axis=-1) * 32767.0).astype(np.int16)

    with wave.open(MIXED_WAV, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo_int16.tobytes())
    os.remove(orig_wav)


# ---------------------------------------------------------------------------
# Main Preview & Full Video Renderer
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=str, default="", help="Save a 16-frame preview contact sheet")
    args = parser.parse_args()

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    frame_size = W * H * 3
    total_frames = 737

    # Pre-cache Andrew's close-up face avatar at t=1.0s
    cmd_av = [
        ffmpeg_exe,
        "-ss",
        "1.0",
        "-i",
        RAW_VIDEO,
        "-frames:v",
        "1",
        "-vf",
        f"scale={W}:{H}:flags=lanczos",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    p_av = subprocess.Popen(cmd_av, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    buf_av = p_av.stdout.read(frame_size)
    p_av.wait()
    if len(buf_av) == frame_size:
        av_rgb = np.frombuffer(buf_av, dtype=np.uint8).reshape((H, W, 3))
        _CACHE["face_avatar"] = Image.fromarray(av_rgb).crop((190, 240, 910, 1140)).resize((160, 160), Image.LANCZOS)

    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        sample_times = [
            0.85, 2.55, 3.55, 4.75,
            6.55, 7.65, 9.40, 11.40,
            13.40, 15.45, 16.90, 18.25,
            19.85, 21.35, 21.95, 23.60,
        ]
        cols, rows = 4, 4
        tw, th = 270, 480
        sheet = Image.new("RGB", (cols * tw, rows * th), (12, 12, 16))
        for idx, st in enumerate(sample_times):
            cmd = [
                ffmpeg_exe,
                "-ss",
                f"{st:.3f}",
                "-i",
                RAW_VIDEO,
                "-frames:v",
                "1",
                "-vf",
                f"scale={W}:{H}:flags=lanczos",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-",
            ]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            buf = p.stdout.read(frame_size)
            p.wait()
            raw_f = np.frombuffer(buf, dtype=np.uint8).reshape((H, W, 3))
            rgb = render_frame(raw_f, raw_f, st)
            thumb = Image.fromarray(rgb).resize((tw, th), Image.LANCZOS)
            td = ImageDraw.Draw(thumb)
            td.rectangle([8, 8, 128, 38], fill=(0, 0, 0))
            td.text((14, 13), f"t={st:05.2f}s", fill=(84, 242, 232))
            sheet.paste(thumb, ((idx % cols) * tw, (idx // cols) * th))
        sheet.save(args.preview, quality=92)
        print(f"Saved preview contact sheet to {args.preview}")
        return

    os.makedirs(FILM_DIR, exist_ok=True)
    build_master_audio_mix(ffmpeg_exe)

    decode_cmd = [
        ffmpeg_exe,
        "-i",
        RAW_VIDEO,
        "-vf",
        f"fps={FPS},scale={W}:{H}:flags=lanczos",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
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
        "faster",
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
    proc_in = subprocess.Popen(decode_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc_out = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE)

    prev_raw_f = None
    fi = 0
    while True:
        buf = proc_in.stdout.read(frame_size)
        if not buf or len(buf) < frame_size:
            break
        raw_f = np.frombuffer(buf, dtype=np.uint8).reshape((H, W, 3))
        if prev_raw_f is None:
            prev_raw_f = raw_f
        t = fi / FPS
        out_rgb = render_frame(raw_f, prev_raw_f, t)
        proc_out.stdin.write(out_rgb.tobytes())
        if fi % 2 == 0:
            prev_raw_f = raw_f
        fi += 1
        if fi % 120 == 0 or fi == total_frames:
            print(f"Rendered {fi}/{total_frames} frames ({fi / total_frames * 100:.1f}%)")

    proc_in.stdout.close()
    proc_in.wait()
    proc_out.stdin.close()
    ret = proc_out.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")
    print(f"Successfully rendered {OUT_MP4} ({fi} frames)")


if __name__ == "__main__":
    main()
