#!/usr/bin/env python3
"""
Master 9:16 Video Compositor for:
  `From Klickpin.com- 69 Trending Nature Escape Ideas for 2026-pin-id-1031535489667210887.mp4`
  (Andrew Crosse — Engel & Völkers Real Estate Masterclass, 24.57s, 1080x1920, 30.00 fps)

Applies:
  1. `MOTION-DESIGN.md` (`--motion-ease-out: cubic-bezier(0.2, 0.8, 0.2, 1.0)`,
     `[data-reveal]` `translateY(14px -> 0)`, 60ms stagger, 180ms/300ms/480ms/720ms
     rhythm benchmarks, visual hierarchy, readability, continuity, restraint).
  2. `.claude/skills/motion-code-harvester/scripts/motion_engine.py`:
     - `waterfall_word_state` (`0.84^i` decaying stagger + weight-based Y offset)
     - `nudge_curve_3phase` (10%/65%/25% distance over 20%/18%/62% duration)
     - `swipe_clip_reveal` (`power4.inOut` expanding bar/pill wipe)
     - `zoom_through_seam`, `cut_the_curve_seam`, `rack_focus_blur_cut`
  3. 3D & B-Roll Skills (`.claude/skills/`):
     - `threejs-camera-controls-and-rigs`: 3x3 projective homography (`warp_plane_3d`)
     - `video-shotcraft`: 3D world-space depth-of-field particles & volumetric light cones
     - `broll-media-fetcher`: Z-space speaker foreground segmentation + architectural triptych
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

PROJECT_DIR = "/home/user/COOL-backup/engel-volkers-masterclass"
RAW_VIDEO = "/home/user/COOL-backup/From Klickpin.com- 69 Trending Nature Escape Ideas for 2026-pin-id-1031535489667210887.mp4"
AUDIO_DIR = f"{PROJECT_DIR}/assets/audio"
FILM_DIR = f"{PROJECT_DIR}/film"
MIXED_WAV = f"{AUDIO_DIR}/master_audio_mix.wav"
OUT_MP4 = f"{FILM_DIR}/engel-volkers-masterclass-9x16.mp4"

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
PLAYFAIR_BOLD = f"{FONT_BASE}/playfair-display/700Bold/PlayfairDisplay_700Bold.ttf"
PLAYFAIR_ITALIC = f"{FONT_BASE}/playfair-display/700Bold_Italic/PlayfairDisplay_700Bold_Italic.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"

# Brand & Motion Design Palette
C_EV_RED = (214, 31, 38)       # Engel & Völkers signature crimson (#D61F26)
C_GOLD = (255, 226, 44)        # Signature glowing yellow-gold (#FFE22C)
C_AMBER = (245, 168, 40)       # Warm architectural amber
C_EMERALD = (34, 197, 94)      # Verified green accent
C_CREAM = (246, 239, 226)      # Warm architectural cream
C_DARK = (14, 14, 18)          # Matte obsidian

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


def swipe_bar_progress(age: float, duration: float = 0.36) -> float:
    return expo_in_out(clamp(age / max(1e-4, duration)))


def data_reveal_state(age: float, delay: float = 0.0, dur: float = 0.48, offset_y: float = 28.0):
    """Implements `[data-reveal]` from MOTION-DESIGN.md (`translateY(14px -> 0)` + `cubic-bezier(0.2,0.8,0.2,1)`)."""
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
# Procedural Architectural B-Roll & Halftone Assets
# ---------------------------------------------------------------------------
_ASSETS = {}


def get_assets():
    if _ASSETS:
        return _ASSETS

    # 1. Warm Golden & Crimson Halftone Dot Matrix (behind speaker shoulders)
    halftone = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halftone)
    spacing = 24
    for gy in range(260, 1120, spacing):
        for gx in range(36, W - 36, spacing):
            dist_l = math.hypot((gx - 180) / 230.0, (gy - 660) / 310.0)
            dist_r = math.hypot((gx - 900) / 230.0, (gy - 660) / 310.0)
            strength = max(clamp(1.0 - dist_l), clamp(1.0 - dist_r))
            if strength > 0.08:
                r = max(2, int(round(10.0 * (strength ** 0.85))))
                alpha = int(clamp(strength * 225, 0, 225))
                col = C_GOLD if (gx + gy) % 48 != 0 else C_EV_RED
                hd.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(*col, alpha))
    _ASSETS["halftone"] = halftone

    # 2. Three Architectural Real-Estate Stages for the 4-Slice Accordion (Scene 4B: 10.60s-12.50s)
    # Stage 1: Monochrome Brutalist Luxury Residence
    s1 = Image.new("RGBA", (W, H), (22, 24, 28, 255))
    d1 = ImageDraw.Draw(s1)
    for y in range(0, H, 4):
        v = int(20 + 38 * (1.0 - y / H))
        d1.line([(0, y), (W, y)], fill=(v, v + 2, v + 5, 255), width=4)
    # Cantilevered concrete slabs & floor-to-ceiling glass
    for lvl, y0 in enumerate((340, 680, 1020, 1360)):
        d1.rectangle([90, y0, 990, y0 + 54], fill=(168, 172, 178, 255), outline=(230, 234, 240, 255), width=3)
        d1.rectangle([140, y0 + 54, 940, y0 + 290], fill=(38, 44, 52, 235), outline=(120, 128, 138, 255), width=2)
        for mx in range(220, 900, 110):
            d1.line([(mx, y0 + 54), (mx, y0 + 290)], fill=(140, 146, 154, 200), width=3)
    _ASSETS["arch_stage1"] = s1

    # Stage 2: Architectural CAD Blueprint & Elevation Drawing
    s2 = Image.new("RGBA", (W, H), (242, 236, 224, 255))
    d2 = ImageDraw.Draw(s2)
    for gx in range(0, W, 60):
        d2.line([(gx, 0), (gx, H)], fill=(214, 206, 192, 255), width=1)
    for gy in range(0, H, 60):
        d2.line([(0, gy), (W, gy)], fill=(214, 206, 192, 255), width=1)
    for lvl, y0 in enumerate((340, 680, 1020, 1360)):
        d2.rectangle([90, y0, 990, y0 + 54], outline=(35, 40, 50, 255), width=4)
        d2.rectangle([140, y0 + 54, 940, y0 + 290], outline=(214, 31, 38, 220), width=3)
        d2.line([(90, y0), (990, y0 + 290)], fill=(35, 40, 50, 90), width=2)
        for mx in range(220, 900, 110):
            d2.line([(mx, y0 + 54), (mx, y0 + 290)], fill=(35, 40, 50, 190), width=2)
    _ASSETS["arch_stage2"] = s2

    # Stage 3: Warm Twilight Illuminated Luxury Villa Atrium
    s3 = Image.new("RGBA", (W, H), (16, 20, 32, 255))
    d3 = ImageDraw.Draw(s3)
    for y in range(0, H, 4):
        r = int(18 + 26 * (1.0 - y / H))
        g = int(24 + 34 * (1.0 - y / H))
        b = int(42 + 64 * (1.0 - y / H))
        d3.line([(0, y), (W, y)], fill=(r, g, b, 255), width=4)
    for lvl, y0 in enumerate((340, 680, 1020, 1360)):
        d3.rectangle([90, y0, 990, y0 + 54], fill=(52, 46, 42, 255), outline=(255, 215, 120, 220), width=3)
        # Warm golden interior glow
        d3.rectangle([140, y0 + 54, 940, y0 + 290], fill=(235, 168, 64, 215), outline=(255, 228, 130, 255), width=3)
        for mx in range(220, 900, 110):
            d3.line([(mx, y0 + 54), (mx, y0 + 290)], fill=(45, 38, 32, 240), width=5)
    s3_glow = s3.filter(ImageFilter.GaussianBlur(radius=18))
    s3 = Image.blend(s3, s3_glow, 0.28)
    _ASSETS["arch_stage3"] = s3

    return _ASSETS


# ---------------------------------------------------------------------------
# Speaker Foreground Segmentation Masks (for true Z-Space Behind-Speaker Text)
# ---------------------------------------------------------------------------
def get_wide_speaker_mask(raw_rgb: np.ndarray) -> Image.Image:
    """
    Segments Andrew and his cognac leather armchair from the sunlit cream plaster wall
    in Shot 2 (4.00s-5.85s) and Shot 4 (7.22s-16.12s).
    In the wide shot, Andrew's hair top is at y=665 (x=580..830) and the armchair back starts at y=920.
    """
    arr = raw_rgb.astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    rb_diff = np.abs(r - b)
    is_wall = (luma > 158.0) & (rb_diff < 36.0)
    fg = (~is_wall).astype(np.uint8) * 255

    yy, xx = np.mgrid[0:H, 0:W]
    in_subject_zone = (xx >= 180) & (xx <= 1060) & (yy >= 650)
    head_core = (((xx - 705.0) / 110.0) ** 2 + ((yy - 825.0) / 145.0) ** 2) <= 1.0
    chair_torso_core = (xx >= 250) & (xx <= 990) & (yy >= 960)
    mask_np = np.where(((fg > 128) & in_subject_zone) | head_core | chair_torso_core, 255, 0).astype(np.uint8)
    return Image.fromarray(mask_np, mode="L").filter(ImageFilter.GaussianBlur(radius=4))


def get_closeup_speaker_mask() -> Image.Image:
    if "closeup_mask" in _ASSETS:
        return _ASSETS["closeup_mask"]
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    # Close-up head & shoulders in Shot 1 (0.00-4.00s) and Shot 3 (5.85-7.22s)
    d.ellipse([210, 60, 890, 1220], fill=255)
    d.rounded_rectangle([40, 960, 1040, 1920], radius=180, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(radius=20))
    _ASSETS["closeup_mask"] = m
    return m


# ---------------------------------------------------------------------------
# Color Grading & 3D Depth-of-Field Particles
# ---------------------------------------------------------------------------
def grade_camera_frame(raw_rgb: np.ndarray, t: float, zoom: float = 1.0, dark_vignette: float = 0.52) -> Image.Image:
    f = raw_rgb.astype(np.float32)
    # Cinema contrast + subtle warm architectural highlight
    f = (f - 128.0) * 1.08 + 126.0
    f[:, :, 0] *= 1.03
    f[:, :, 1] *= 1.01
    f[:, :, 2] *= 0.96
    graded = np.clip(f, 0, 255).astype(np.uint8)
    im = Image.fromarray(graded).convert("RGBA")

    # Continuous subtle breathing zoom (`video-talkcraft`: no static frame)
    z = zoom + 0.018 * math.sin(t * 0.85)
    if abs(z - 1.0) > 0.002:
        nw, nh = int(round(W * z)), int(round(H * z))
        im_z = im.resize((nw, nh), Image.BILINEAR)
        x0 = (nw - W) // 2
        y0 = int((nh - H) * 0.36)
        im = im_z.crop((x0, y0, x0 + W, y0 + H))

    if dark_vignette > 0.01:
        yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
        vig = np.clip((yy - 0.50) / 0.50, 0.0, 1.0) * dark_vignette
        arr = np.array(im, dtype=np.float32)
        arr[:, :, :3] *= (1.0 - vig[:, :, None])
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return im


def draw_dof_particles(canvas: Image.Image, t: float, count: int = 38, warm: bool = True):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(count):
        seed = (i + 1) * 137.508
        bx = (seed * 31.7) % W
        by = (seed * 73.1) % H
        z_depth = (i % 7) / 6.0  # 0 = far, 1 = near
        speed_y = 18.0 + 36.0 * z_depth
        px = (bx + math.sin(t * 0.9 + i) * (16.0 + 20.0 * z_depth)) % W
        py = (by - t * speed_y) % H
        r = int(2 + 4.5 * z_depth)
        alpha = int(35 + 95 * (1.0 - abs(z_depth - 0.55)))
        col = (255, 224, 110, alpha) if (warm and i % 3 != 0) else (255, 255, 255, alpha)
        d.ellipse([px - r, py - r, px + r, py + r], fill=col)
    canvas.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# Reusable UI & Kinetic Typography Components
# ---------------------------------------------------------------------------
def draw_top_editorial_pill(canvas: Image.Image, age: float, left_tag: str, right_tag: str, dark_theme: bool = True):
    a, dy = data_reveal_state(age, delay=0.04, dur=0.42, offset_y=22.0)
    if a <= 0.02:
        return
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    f_mono = get_font(MONO_MED, 23)
    text = f"{left_tag}   //   {right_tag}"
    bb = d.textbbox((0, 0), text, font=f_mono)
    tw = bb[2] - bb[0]
    pw = tw + 68
    ph = 50
    px = (W - pw) // 2
    py = int(76 + dy)

    bg_col = (18, 18, 24, int(215 * a)) if dark_theme else (255, 255, 255, int(230 * a))
    border_col = (255, 226, 44, int(190 * a)) if dark_theme else (214, 31, 38, int(210 * a))
    txt_col = (245, 245, 250, int(245 * a)) if dark_theme else (24, 24, 30, int(245 * a))

    d.rounded_rectangle([px, py, px + pw, py + ph], radius=25, fill=bg_col, outline=border_col, width=2)
    # Pulsing crimson status dot
    dot_r = 6
    d.ellipse([px + 22 - dot_r, py + ph // 2 - dot_r, px + 22 + dot_r, py + ph // 2 + dot_r], fill=(*C_EV_RED, int(255 * a)))
    d.text((px + 42, py + 11), text, font=f_mono, fill=txt_col)
    canvas.alpha_composite(overlay)


def draw_3tier_kinetic_lockup(
    canvas: Image.Image,
    age: float,
    lead_text: str = "",
    hero_text: str = "",
    script_text: str = "",
    cy: int = 1420,
    hero_color=C_GOLD,
    crimson_bar: bool = False,
    echo_trail: bool = True,
):
    """
    Renders the signature 3-tier luxury kinetic typography lockup:
      - Lead-in white sans (`waterfall_word_state` weight='normal')
      - Hero word (`Plus Jakarta Sans ExtraBold` 102px) either in glowing gold with
        vertical echo repeats OR inside a wiping Engel & Völkers Crimson bar (`swipe_clip_reveal`)
      - Sweeping white Calligraphic Script (`Great Vibes` 114px) with `nudge_curve_3phase`
    """
    a_lead, dy_lead, _ = waterfall_word_state(age, word_index=0, weight="normal")
    hero_idx = 1 if lead_text else 0
    a_hero, dy_hero, _ = waterfall_word_state(age, word_index=hero_idx, weight="anchor")
    hero_age = max(0.0, age - (0.06 if lead_text else 0.0))

    nudge_dy = 0.0
    if script_text:
        nudge_age = max(0.0, hero_age - 0.10)
        nudge_dy = -16.0 * nudge_curve_3phase(nudge_age / 0.42)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    f_lead = get_font(INTER_MED, 48)
    f_hero = get_font(JAKARTA_EBOLD, 102)
    f_script = get_font(GREAT_VIBES, 118)

    # Soft dark backdrop glow for 100% legibility
    bg_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(bg_glow)
    gd.ellipse([120, cy - 130, W - 120, cy + 250], fill=(0, 0, 0, int(135 * clamp(age / 0.25))))
    bg_glow = bg_glow.filter(ImageFilter.GaussianBlur(radius=42))
    canvas.alpha_composite(bg_glow)

    # 1. Lead-in white text
    if lead_text and a_lead > 0.02:
        bb_l = od.textbbox((0, 0), lead_text, font=f_lead)
        lw = bb_l[2] - bb_l[0]
        lx = (W - lw) // 2
        ly = int(cy - 76 + dy_lead + nudge_dy)
        alpha_l = int(clamp(a_lead) * 255)
        od.text((lx + 3, ly + 4), lead_text, font=f_lead, fill=(0, 0, 0, int(alpha_l * 0.75)))
        od.text((lx, ly), lead_text, font=f_lead, fill=(255, 255, 255, alpha_l))

    # 2. Hero word
    if hero_text and a_hero > 0.02:
        bb_h = od.textbbox((0, 0), hero_text, font=f_hero)
        hw = bb_h[2] - bb_h[0]
        hh = bb_h[3] - bb_h[1]
        hx = (W - hw) // 2
        hy = int(cy + dy_hero + nudge_dy)
        alpha_h = int(clamp(a_hero) * 255)

        if crimson_bar:
            # Wiping Engel & Völkers Crimson bar (`swipe-reveal` expo_in_out)
            wipe_w = swipe_bar_progress(hero_age, duration=0.34)
            pad_x, pad_y = 28, 16
            bx0 = hx - pad_x
            by0 = hy - pad_y
            full_bw = hw + pad_x * 2
            bx1 = bx0 + int(round(full_bw * wipe_w))
            by1 = hy + hh + pad_y
            if bx1 > bx0 + 4:
                od.rounded_rectangle([bx0 + 4, by0 + 6, bx1 + 4, by1 + 6], radius=14, fill=(0, 0, 0, int(170 * a_hero)))
                od.rounded_rectangle([bx0, by0, bx1, by1], radius=14, fill=(*C_EV_RED, alpha_h), outline=(*C_GOLD, int(220 * a_hero)), width=3)
            od.text((hx + 3, hy - bb_h[1] + 4), hero_text, font=f_hero, fill=(0, 0, 0, int(alpha_h * 0.65)))
            od.text((hx, hy - bb_h[1]), hero_text, font=f_hero, fill=(255, 255, 255, alpha_h))
        else:
            # Vertical echo ghost trail during entry
            if echo_trail and hero_age < 0.55:
                echo_fade = clamp(1.0 - hero_age / 0.55)
                for idx in range(1, 5):
                    ey = hy - idx * 36 * echo_fade
                    ea = int(echo_fade * (135 - idx * 26))
                    if ea > 8:
                        od.text((hx, int(ey) - bb_h[1]), hero_text, font=f_hero, fill=(*hero_color, ea))
            # Optical bloom behind hero word
            bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(bloom)
            bd.text((hx, hy - bb_h[1]), hero_text, font=f_hero, fill=(*hero_color, int(alpha_h * 0.55)))
            bloom = bloom.filter(ImageFilter.GaussianBlur(radius=16))
            overlay = Image.alpha_composite(overlay, bloom)
            od = ImageDraw.Draw(overlay)
            od.text((hx + 4, hy - bb_h[1] + 5), hero_text, font=f_hero, fill=(0, 0, 0, int(alpha_h * 0.82)))
            od.text((hx, hy - bb_h[1]), hero_text, font=f_hero, fill=(*hero_color, alpha_h))

    # 3. Calligraphic Script overlay across baseline
    if script_text:
        a_scr, dy_scr, _ = waterfall_word_state(age, word_index=hero_idx + 1, weight="light")
        if a_scr > 0.02:
            bb_s = od.textbbox((0, 0), script_text, font=f_script)
            sw = bb_s[2] - bb_s[0]
            sx = (W - sw) // 2 + 18
            sy = int(cy + 88 + dy_scr * 0.55)
            alpha_s = int(clamp(a_scr) * 255)
            od.text((sx + 3, sy - bb_s[1] + 4), script_text, font=f_script, fill=(0, 0, 0, int(alpha_s * 0.80)))
            od.text((sx, sy - bb_s[1]), script_text, font=f_script, fill=(255, 255, 255, alpha_s))

    canvas.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# SCENE 1 (0.00s - 4.00s): Close-Up Hook + Golden Halftone + 3-Tier Lockups
# "I remember my father coming up to me and he just put his hand on my shoulder and he says..."
# ---------------------------------------------------------------------------
def render_scene1_hook(raw_rgb: np.ndarray, t: float) -> Image.Image:
    base = grade_camera_frame(raw_rgb, t, zoom=1.02, dark_vignette=0.58)
    assets = get_assets()

    # Golden & Crimson Halftone Dot Matrix behind Andrew's shoulders
    ht_alpha = clamp(t / 0.45) * (0.78 + 0.18 * math.sin(t * 2.8))
    if ht_alpha > 0.04:
        ht = assets["halftone"].copy()
        a_ch = ht.split()[3].point(lambda p: int(p * ht_alpha))
        ht.putalpha(a_ch)
        with_ht = Image.alpha_composite(base, ht)
        fg_mask = get_closeup_speaker_mask()
        base = Image.composite(base, with_ht, fg_mask)

    draw_dof_particles(base, t, count=34, warm=True)
    draw_top_editorial_pill(base, t, "ENGEL & VÖLKERS", "MASTERCLASS STORY", dark_theme=True)

    if t < 1.72:
        draw_3tier_kinetic_lockup(
            base,
            age=max(0.0, t - 0.05),
            lead_text="I remember my",
            hero_text="FATHER",
            script_text="coming up to me",
            cy=1380,
            hero_color=C_GOLD,
            crimson_bar=False,
            echo_trail=True,
        )
    else:
        draw_3tier_kinetic_lockup(
            base,
            age=t - 1.72,
            lead_text="put his hand on my",
            hero_text="SHOULDER",
            script_text="and he says...",
            cy=1380,
            hero_color=C_GOLD,
            crimson_bar=True,
            echo_trail=False,
        )
    return base


# ---------------------------------------------------------------------------
# SCENE 2 (4.00s - 5.85s): Wide Armchair + Giant Behind-The-Speaker 3D Title
# "...'Get over it.'"
# ---------------------------------------------------------------------------
def render_scene2_get_over_it(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 4.00
    fg_camera = grade_camera_frame(raw_rgb, t, zoom=1.0, dark_vignette=0.42)
    bg_wall = fg_camera.copy()

    # 1. Giant 3D Behind-The-Speaker Architectural Typography in the sunlit wall space (y=150..620)
    wall_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wall_layer)

    a_badge, dy_badge = data_reveal_state(age, delay=0.04, dur=0.38, offset_y=24.0)
    if a_badge > 0.02:
        f_mono = get_font(MONO_MED, 24)
        lbl = "PATERNAL WISDOM  •  LESSON 01"
        bb = wd.textbbox((0, 0), lbl, font=f_mono)
        bw = bb[2] - bb[0] + 48
        bx = (W - bw) // 2
        by = int(140 + dy_badge)
        wd.rounded_rectangle([bx, by, bx + bw, by + 46], radius=23, fill=(*C_EV_RED, int(245 * a_badge)))
        wd.text((bx + 24, by + 10), lbl, font=f_mono, fill=(255, 255, 255, int(255 * a_badge)))

    # Giant extruded "GET OVER IT." rising from behind Andrew's head & hair (y=490..730)
    a_big, dy_big = data_reveal_state(age, delay=0.08, dur=0.48, offset_y=55.0)
    if a_big > 0.02:
        f_giant = get_font(BEBAS_REG, 236)
        txt = "GET OVER IT."
        bb = wd.textbbox((0, 0), txt, font=f_giant)
        tw = bb[2] - bb[0]
        tx = (W - tw) // 2
        ty = int(495 + dy_big)
        # Crimson underline bar above the behind-speaker title
        wipe_w = swipe_bar_progress(max(0.0, age - 0.14), duration=0.40)
        bar_w = int(tw * wipe_w)
        if bar_w > 6:
            wd.rectangle([tx, ty - 26, tx + bar_w, ty - 12], fill=(*C_EV_RED, int(245 * a_big)))
        # 3D architectural drop-extrusion on the plaster wall
        for depth in range(12, 0, -2):
            wd.text((tx + depth, ty - bb[1] + depth), txt, font=f_giant, fill=(35, 28, 24, int(55 * a_big)))
        wd.text((tx, ty - bb[1]), txt, font=f_giant, fill=(22, 20, 24, int(245 * a_big)))

    bg_with_title = Image.alpha_composite(bg_wall, wall_layer)
    # Composite Andrew's head and armchair IN FRONT of the giant wall typography!
    speaker_mask = get_wide_speaker_mask(raw_rgb)
    scene = Image.composite(fg_camera, bg_with_title, speaker_mask)

    # 2. Lower-Third 3D Perspective Glass Quote Card (y=1380..1720)
    a_card, dy_card = data_reveal_state(age, delay=0.14, dur=0.46, offset_y=36.0)
    if a_card > 0.02:
        cw, ch = 920, 230
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=30, fill=(16, 16, 22, int(230 * a_card)), outline=(255, 226, 44, int(210 * a_card)), width=3)
        cd.rounded_rectangle([24, 24, 36, ch - 24], radius=6, fill=(*C_EV_RED, int(255 * a_card)))

        f_sub = get_font(MONO_MED, 23)
        f_quote = get_font(JAKARTA_EBOLD, 68)
        cd.text((58, 30), "HIS FATHER'S ADVICE // DIRECT & UNFILTERED", font=f_sub, fill=(200, 205, 215, int(235 * a_card)))
        cd.text((58, 82), "“Get over it.”", font=f_quote, fill=(*C_GOLD, int(255 * a_card)))

        # Animated acoustic waveform bars on the right of the card
        for bi in range(12):
            bx = 640 + bi * 20
            amp = 0.25 + 0.75 * abs(math.sin(t * 7.5 + bi * 0.55)) * clamp(1.2 - max(0.0, age - 1.15))
            bh = int(16 + 74 * amp)
            by0 = 118 - bh // 2
            col = C_GOLD if bi % 2 == 0 else C_EV_RED
            cd.rounded_rectangle([bx, by0, bx + 11, by0 + bh], radius=5, fill=(*col, int(240 * a_card)))

        tilt_x = 5.5 * math.sin(age * 1.8)
        tilt_y = -4.5 * math.cos(age * 1.4)
        warped = warp_plane_3d(card, rx_deg=tilt_x, ry_deg=tilt_y, rz_deg=0.0, scale=0.96)
        scene.alpha_composite(warped, ((W - cw) // 2, int(1460 + dy_card)))

    return scene


# ---------------------------------------------------------------------------
# SCENE 3 (5.85s - 7.22s): Tight Close-Up Punch-In + Vertical Echo Stack ("WHAT?!")
# "And I said, 'What?'"
# ---------------------------------------------------------------------------
def render_scene3_what(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 5.85
    base = grade_camera_frame(raw_rgb, t, zoom=1.05, dark_vignette=0.60)

    # Radial concentric shockwave rings behind speaker shoulders
    rings = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    for ri in range(4):
        prog = ((age * 1.45 + ri * 0.25) % 1.0)
        rad = int(140 + prog * 540)
        ra = int((1.0 - prog) * 145)
        col = C_GOLD if ri % 2 == 0 else C_EV_RED
        rd.ellipse([W // 2 - rad, 560 - rad, W // 2 + rad, 560 + rad], outline=(*col, ra), width=4)
    with_rings = Image.alpha_composite(base, rings)
    base = Image.composite(base, with_rings, get_closeup_speaker_mask())

    draw_top_editorial_pill(base, age, "REACTION BEAT", "PERSPECTIVE SHIFT", dark_theme=True)

    # Lead-in + Explosive Vertical Echo Repeat Stack on "WHAT?!"
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    f_lead = get_font(INTER_BOLD, 52)
    f_what = get_font(BEBAS_REG, 196)

    what_age = max(0.0, t - 6.32)
    if what_age > 0.0:
        p_w = ease_motion(clamp(what_age / 0.32))
        txt_w = "“WHAT?!”"
        bb_w = od.textbbox((0, 0), txt_w, font=f_what)
        ww = bb_w[2] - bb_w[0]
        wh = bb_w[3] - bb_w[1]
        wx = (W - ww) // 2
        wy = int(1355 + (1.0 - p_w) * 32)

        # Vertical echo stack above & below
        for idx in range(1, 4):
            spread = idx * int(42 * p_w)
            ea = int((1.0 - idx * 0.24) * 135 * (1.0 - 0.35 * clamp(what_age / 0.8)))
            od.text((wx, wy - spread - bb_w[1]), txt_w, font=f_what, fill=(*C_GOLD, ea))
            od.text((wx, wy + spread - bb_w[1]), txt_w, font=f_what, fill=(*C_EV_RED, ea))

        # Main hero "WHAT?!"
        od.rounded_rectangle([wx - 28, wy - 14, wx + ww + 28, wy + wh + 18], radius=18, fill=(*C_EV_RED, int(245 * p_w)), outline=(*C_GOLD, int(255 * p_w)), width=4)
        od.text((wx + 4, wy - bb_w[1] + 5), txt_w, font=f_what, fill=(0, 0, 0, int(210 * p_w)))
        od.text((wx, wy - bb_w[1]), txt_w, font=f_what, fill=(*C_GOLD, int(255 * p_w)))

    a_lead, dy_lead, _ = waterfall_word_state(age, word_index=0, weight="normal")
    if a_lead > 0.02:
        txt_l = "And I said,"
        bb_l = od.textbbox((0, 0), txt_l, font=f_lead)
        lx = (W - (bb_l[2] - bb_l[0])) // 2
        ly = int(1135 + dy_lead)
        od.rounded_rectangle([lx - 24, ly - 10, lx + (bb_l[2] - bb_l[0]) + 24, ly + 66], radius=16, fill=(14, 14, 18, int(240 * a_lead)), outline=(255, 255, 255, int(90 * a_lead)), width=2)
        od.text((lx, ly), txt_l, font=f_lead, fill=(255, 255, 255, int(255 * a_lead)))

    base.alpha_composite(overlay)
    return base


# ---------------------------------------------------------------------------
# SCENE 4A (7.22s - 10.60s): Wide Armchair + 3D Accountability Checklist Card
# "He says, 'Get over it. Did you do your job, right?' He's like, 'You did your job.'"
# ---------------------------------------------------------------------------
def render_scene4a_checklist(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 7.22
    scene = grade_camera_frame(raw_rgb, t, zoom=1.0, dark_vignette=0.45)

    # 1. Upper 3D Perspective Bento Checklist Card in the open sunlit wall space (y=85..495)
    cw, ch = 940, 390
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    a_c, dy_c = data_reveal_state(age, delay=0.02, dur=0.42, offset_y=28.0)

    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=32, fill=(18, 18, 24, int(232 * a_c)), outline=(255, 255, 255, int(65 * a_c)), width=2)
    # Header bar
    cd.rounded_rectangle([0, 0, cw - 1, 66], radius=32, fill=(30, 30, 38, int(240 * a_c)))
    cd.rectangle([0, 34, cw - 1, 66], fill=(30, 30, 38, int(240 * a_c)))
    cd.ellipse([28, 22, 48, 42], fill=(*C_EV_RED, int(255 * a_c)))
    cd.ellipse([58, 22, 78, 42], fill=(*C_GOLD, int(255 * a_c)))
    cd.ellipse([88, 22, 108, 42], fill=(*C_EMERALD, int(255 * a_c)))
    f_hdr = get_font(MONO_MED, 23)
    cd.text((132, 19), "THE ACCOUNTABILITY AUDIT  //  REAL ESTATE LEADERSHIP", font=f_hdr, fill=(225, 228, 235, int(245 * a_c)))

    rows = [
        (0.05, "01", "“GET OVER IT.”", "DETACH EMOTION", C_EV_RED),
        (0.68, "02", "“DID YOU DO YOUR JOB?”", "AUDIT THE PROCESS", C_GOLD),
        (1.68, "03", "“YOU DID YOUR JOB.”", "VERIFIED EXECUTION ✓", C_EMERALD),
    ]
    f_row = get_font(JAKARTA_BOLD, 34)
    f_tag = get_font(MONO_MED, 21)

    for idx, (r_delay, num_str, title_str, badge_str, col) in enumerate(rows):
        ra, rdy = data_reveal_state(age, delay=r_delay, dur=0.36, offset_y=18.0)
        if ra <= 0.02:
            continue
        ry = int(84 + idx * 96 + rdy)
        active = (idx == 0 and t < 7.90) or (idx == 1 and 7.90 <= t < 8.90) or (idx == 2 and t >= 8.90)
        bg_r = (36, 38, 48, int(235 * ra)) if active else (24, 25, 32, int(185 * ra))
        outline_r = (*col, int(235 * ra)) if active else (255, 255, 255, int(45 * ra))
        cd.rounded_rectangle([24, ry, cw - 24, ry + 80], radius=18, fill=bg_r, outline=outline_r, width=2 if active else 1)

        # Number badge
        cd.rounded_rectangle([40, ry + 16, 102, ry + 64], radius=12, fill=(*col, int(240 * ra)))
        num_fg = (15, 15, 18, int(255 * ra)) if col == C_GOLD else (255, 255, 255, int(255 * ra))
        cd.text((54, ry + 21), num_str, font=f_row, fill=num_fg)

        cd.text((124, ry + 20), title_str, font=f_row, fill=(255, 255, 255, int(250 * ra)))

        bb_b = cd.textbbox((0, 0), badge_str, font=f_tag)
        bw = bb_b[2] - bb_b[0] + 28
        cd.rounded_rectangle([cw - 44 - bw, ry + 20, cw - 44, ry + 60], radius=10, fill=(*col, int(45 * ra)), outline=(*col, int(190 * ra)), width=1)
        cd.text((cw - 44 - bw + 14, ry + 27), badge_str, font=f_tag, fill=(*col, int(250 * ra)))

    warped_card = warp_plane_3d(card, rx_deg=4.0 * math.sin(age * 1.4), ry_deg=-3.5 * math.cos(age * 1.1), scale=0.96)
    card_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card_layer.alpha_composite(warped_card, ((W - cw) // 2, int(82 + dy_c)))

    # Place the card slightly behind the very top of Andrew's hair so he sits in front in Z-space
    with_card = Image.alpha_composite(scene, card_layer)
    scene = Image.composite(scene, with_card, get_wide_speaker_mask(raw_rgb))

    # 2. Lower-third synchronized kinetic typography (y=1420)
    if t < 8.90:
        draw_3tier_kinetic_lockup(
            scene,
            age=max(0.0, t - 7.85),
            lead_text="Did you do",
            hero_text="YOUR JOB",
            script_text="right?",
            cy=1420,
            hero_color=C_GOLD,
            crimson_bar=False,
            echo_trail=True,
        )
    else:
        draw_3tier_kinetic_lockup(
            scene,
            age=t - 8.90,
            lead_text="He's like, you did",
            hero_text="YOUR JOB.",
            script_text="standard met",
            cy=1420,
            hero_color=C_GOLD,
            crimson_bar=True,
            echo_trail=False,
        )
    return scene


# ---------------------------------------------------------------------------
# SCENE 4B (10.60s - 12.50s): 4-Slice Vertical Accordion Architectural Evolution
# "You did a very good job."
# ---------------------------------------------------------------------------
def render_scene4b_accordion(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 10.60
    assets = get_assets()
    s1 = assets["arch_stage1"]
    s2 = assets["arch_stage2"]
    s3 = assets["arch_stage3"]

    # Evolve through the 3 architectural stages across 10.60s..12.50s
    if age < 0.60:
        bg_cur = s1
    elif age < 1.20:
        p_m = ease_motion((age - 0.60) / 0.45)
        bg_cur = Image.blend(s1, s2, p_m)
    else:
        p_m = ease_motion((age - 1.20) / 0.45)
        bg_cur = Image.blend(s2, s3, p_m)

    # 4-Slice Vertical Accordion Entrance (`MOTION-DESIGN.md`: 60ms stagger + `cubic-bezier(0.2,0.8,0.2,1)`)
    canvas = grade_camera_frame(raw_rgb, t, zoom=1.04, dark_vignette=0.55)
    col_w = W // 4
    for c in range(4):
        c_age = max(0.0, age - c * 0.06)
        p_col = ease_motion(clamp(c_age / 0.46))
        if p_col <= 0.01:
            continue
        x0 = c * col_w
        slice_im = bg_cur.crop((x0, 0, x0 + col_w, H))
        y_off = int((1.0 - p_col) * H * (1 if c % 2 == 0 else -1))
        canvas.alpha_composite(slice_im, (x0, y_off))
        # Subtle vertical divider line
        if c > 0:
            d_div = ImageDraw.Draw(canvas)
            d_div.line([(x0, 0), (x0, H)], fill=(255, 226, 44, int(115 * p_col)), width=2)

    # Dark radial readability veil
    veil = Image.new("RGBA", (W, H), (8, 10, 16, 130))
    canvas = Image.alpha_composite(canvas, veil)

    # Full-height 9x Vertical Yellow-Gold Echo Repeat Stack ("VERY GOOD JOB")
    echo_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(echo_layer)
    f_stack = get_font(BEBAS_REG, 178)
    word = "VERY GOOD JOB"
    bb = ed.textbbox((0, 0), word, font=f_stack)
    ww = bb[2] - bb[0]
    wx = (W - ww) // 2
    p_stack = ease_motion(clamp((age - 0.12) / 0.48))

    for i in range(9):
        ry = int(130 + i * 190 + (1.0 - p_stack) * 60)
        is_center = (i == 4)
        if is_center:
            ed.rounded_rectangle([wx - 28, ry - 10, wx + ww + 28, ry + (bb[3] - bb[1]) + 18], radius=16, fill=(*C_EV_RED, int(245 * p_stack)), outline=(*C_GOLD, int(255 * p_stack)), width=4)
            ed.text((wx, ry - bb[1]), word, font=f_stack, fill=(255, 255, 255, int(255 * p_stack)))
        else:
            dist = abs(i - 4)
            alpha = int(clamp((1.0 - dist * 0.20) * 165 * p_stack, 18, 165))
            ed.text((wx, ry - bb[1]), word, font=f_stack, fill=(*C_GOLD, alpha))

    canvas.alpha_composite(echo_layer)

    # Floating 3D Picture-in-Picture Rounded Window of Andrew in upper-right corner
    a_pip, dy_pip = data_reveal_state(age, delay=0.10, dur=0.42, offset_y=26.0)
    if a_pip > 0.02:
        pw, ph = 320, 400
        cam_crop = grade_camera_frame(raw_rgb, t, zoom=1.0, dark_vignette=0.15).crop((380, 580, 980, 1330)).resize((pw, ph), Image.BILINEAR)
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=28, fill=255)
        pip_card = Image.new("RGBA", (pw + 12, ph + 12), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pip_card)
        pd.rounded_rectangle([0, 0, pw + 11, ph + 11], radius=32, fill=(18, 18, 24, 240), outline=(*C_GOLD, 235), width=4)
        pip_card.paste(cam_crop, (6, 6), mask)
        canvas.alpha_composite(pip_card, (W - pw - 64, int(110 + dy_pip)))

    draw_top_editorial_pill(canvas, age, "CRAFT & EXCELLENCE", "ARCHITECTURAL STANDARD", dark_theme=True)
    return canvas


# ---------------------------------------------------------------------------
# SCENE 4C (12.50s - 16.12s): Dark Split-Card Window + 3D Winding Staircase
# "Just because the outcome wasn't what you expected, you did a very good job."
# ---------------------------------------------------------------------------
def render_scene4c_split_staircase(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 12.50
    canvas = Image.new("RGBA", (W, H), (*C_DARK, 255))
    cd = ImageDraw.Draw(canvas)

    # Subtle architectural grid in the lower dark stage
    for gx in range(60, W, 90):
        cd.line([(gx, 840), (gx, H)], fill=(255, 255, 255, 14), width=1)
    for gy in range(860, H, 90):
        cd.line([(0, gy), (W, gy)], fill=(255, 255, 255, 14), width=1)

    draw_dof_particles(canvas, t, count=28, warm=True)
    draw_top_editorial_pill(canvas, age, "PROCESS > OUTCOME", "ENGEL & VÖLKERS PHILOSOPHY", dark_theme=True)

    # 1. Upper Rounded Speaker Window (780x680 at y=150..830)
    win_w, win_h = 820, 680
    win_x, win_y = (W - win_w) // 2, 152
    a_win, dy_win = data_reveal_state(age, delay=0.0, dur=0.44, offset_y=28.0)
    wy = int(win_y + dy_win)

    cam_im = grade_camera_frame(raw_rgb, t, zoom=1.03, dark_vignette=0.25)
    # Crop centered on Andrew in the armchair (y=580..1260)
    cam_crop = cam_im.crop((200, 580, 1020, 1260)).resize((win_w, win_h), Image.BILINEAR)
    win_mask = Image.new("L", (win_w, win_h), 0)
    ImageDraw.Draw(win_mask).rounded_rectangle([0, 0, win_w - 1, win_h - 1], radius=44, fill=255)

    win_frame = Image.new("RGBA", (win_w + 12, win_h + 12), (0, 0, 0, 0))
    wfd = ImageDraw.Draw(win_frame)
    wfd.rounded_rectangle([0, 0, win_w + 11, win_h + 11], radius=48, fill=(24, 24, 32, 255), outline=(255, 226, 44, 210), width=3)
    win_frame.paste(cam_crop, (6, 6), win_mask)
    canvas.alpha_composite(win_frame, (win_x - 6, wy - 6))

    # Window corner HUD tag
    f_hud = get_font(MONO_MED, 21)
    cd.rounded_rectangle([win_x + 24, wy + win_h - 62, win_x + 390, wy + win_h - 20], radius=12, fill=(14, 14, 18, 215), outline=(*C_EV_RED, 220), width=2)
    cd.text((win_x + 42, wy + win_h - 54), "LIVE // ANDREW CROSSE", font=f_hud, fill=(255, 255, 255, 245))

    # 2. Lower Stage (y=860..1860): 3D Winding Architectural Staircase + Outcome vs Process Lockup
    stage = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stage)

    stair_p = ease_motion(clamp(age / 1.85))
    num_steps = 20
    visible_steps = max(2, int(round(num_steps * clamp(age / 1.45))))

    # Draw 3D S-Curved Architectural Staircase from bottom-left (y=1760) to upper-right (y=1020)
    pts_center = []
    for s in range(visible_steps):
        u = s / float(num_steps - 1)
        sx = int(200 + u * 660 + 95 * math.sin(u * math.pi * 2.0))
        sy = int(1750 - u * 700)
        pts_center.append((sx, sy))
        step_w = int(115 - u * 24)
        step_h = 18
        step_d = 14
        is_lit = (u <= stair_p + 0.06)
        top_col = (*C_GOLD, 250) if is_lit else (225, 228, 236, 215)
        front_col = (195, 148, 24, 250) if is_lit else (140, 145, 155, 215)
        side_col = (135, 96, 14, 250) if is_lit else (90, 95, 105, 215)

        # Extruded 3D step block
        sd.polygon([(sx - step_w, sy), (sx + step_w, sy), (sx + step_w + step_d, sy - step_d), (sx - step_w + step_d, sy - step_d)], fill=top_col)
        sd.rectangle([sx - step_w, sy, sx + step_w, sy + step_h], fill=front_col)
        sd.polygon([(sx + step_w, sy), (sx + step_w + step_d, sy - step_d), (sx + step_w + step_d, sy - step_d + step_h), (sx + step_w, sy + step_h)], fill=side_col)

    # Climbing golden energy sphere along the steps
    if pts_center:
        orb_idx = min(len(pts_center) - 1, int(round(stair_p * (num_steps - 1))))
        ox, oy = pts_center[orb_idx]
        oy -= 26
        for gr in range(36, 8, -7):
            sd.ellipse([ox - gr, oy - gr, ox + gr, oy + gr], fill=(*C_GOLD, int(55 * (1.0 - gr / 40.0))))
        sd.ellipse([ox - 13, oy - 13, ox + 13, oy + 13], fill=(255, 255, 255, 255), outline=(*C_GOLD, 255), width=4)

    # Bottom label: "[01] DISCIPLINED EFFORT"
    f_lbl = get_font(MONO_MED, 23)
    f_big = get_font(JAKARTA_EBOLD, 52)
    sd.rounded_rectangle([54, 1730, 420, 1796], radius=16, fill=(24, 26, 34, 240), outline=(255, 255, 255, 90), width=2)
    sd.text((76, 1748), "01 • YOUR EFFORT & CRAFT", font=f_lbl, fill=(235, 238, 245, 250))

    # Mid diverging vector badge (13.10s+): "OUTCOME ≠ EXPECTED"
    if t >= 13.00:
        a_out, dy_out = data_reveal_state(t - 13.00, delay=0.0, dur=0.38, offset_y=22.0)
        by = int(1240 + dy_out)
        sd.rounded_rectangle([52, by, 540, by + 134], radius=22, fill=(32, 18, 22, int(240 * a_out)), outline=(*C_EV_RED, int(245 * a_out)), width=3)
        sd.text((78, by + 18), "UNEXPECTED OUTCOME", font=f_lbl, fill=(*C_EV_RED, int(255 * a_out)))
        sd.text((78, by + 54), "Outcome ≠ Expected", font=get_font(JAKARTA_BOLD, 42), fill=(255, 255, 255, int(255 * a_out)))

    # Top summit badge (14.85s+): "VERY GOOD JOB"
    if t >= 14.85:
        a_top, dy_top = data_reveal_state(t - 14.85, delay=0.0, dur=0.40, offset_y=24.0)
        ty = int(910 + dy_top)
        sd.rounded_rectangle([430, ty, 1028, ty + 150], radius=24, fill=(22, 28, 24, int(245 * a_top)), outline=(*C_GOLD, int(255 * a_top)), width=3)
        sd.text((458, ty + 18), "VERIFIED PERFORMANCE ✓", font=f_lbl, fill=(*C_EMERALD, int(255 * a_top)))
        sd.text((458, ty + 56), "“A VERY GOOD JOB.”", font=f_big, fill=(*C_GOLD, int(255 * a_top)))

    canvas.alpha_composite(stage)
    return canvas


# ---------------------------------------------------------------------------
# SCENE 5 (16.12s - 22.48s): Moody Monochrome Studio + Volumetric Cones
# + 3D Editorial Identity Card + 3D Masterclass Pillar Cards
# "My name's Andrew Crosse. And today's Masterclass, we're going to teach you
#  how to be a mentor in real estate and how to build communities."
# ---------------------------------------------------------------------------
def render_scene5_masterclass(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 16.12
    base = grade_camera_frame(raw_rgb, t, zoom=1.02, dark_vignette=0.48)

    # 1. Twin Volumetric Spotlight Cones descending from y=0 (`reference9` atmospheric light)
    cones = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cones)
    sway = 35.0 * math.sin(age * 0.9)
    cd.polygon([(220, 0), (360, 0), (740 + sway, H), (-80 + sway, H)], fill=(255, 215, 110, 26))
    cd.polygon([(720, 0), (860, 0), (1160 - sway, H), (340 - sway, H)], fill=(214, 31, 38, 22))
    cones = cones.filter(ImageFilter.GaussianBlur(radius=28))
    base = Image.alpha_composite(base, cones)

    # 2. Giant Vertical Stacked Display Letters ("M-E-N-T-O-R") along left edge
    vert_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vert_layer)
    f_vert = get_font(BEBAS_REG, 168)
    for idx, ch_str in enumerate("MENTOR"):
        la, ldy = data_reveal_state(age, delay=0.10 + idx * 0.06, dur=0.44, offset_y=28.0)
        if la <= 0.02:
            continue
        ly = int(520 + idx * 165 + ldy)
        col = C_GOLD if idx % 2 == 0 else C_EV_RED
        vd.text((34, ly), ch_str, font=f_vert, fill=(*col, int(90 * la)))
    base.alpha_composite(vert_layer)

    draw_dof_particles(base, t, count=36, warm=True)

    # 3. Upper Studio Space (y=90..540):
    #    Phase 5A (16.12s - 18.90s): 3D Editorial Speaker Identity Card ("ANDREW CROSSE")
    #    Phase 5B (18.90s - 22.48s): Two 3D Extruded Masterclass Pillar Cards
    if t < 18.90:
        a_id, dy_id = data_reveal_state(age, delay=0.05, dur=0.46, offset_y=32.0)
        cw, ch = 920, 360
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=32, fill=(246, 242, 234, int(242 * a_id)), outline=(*C_EV_RED, int(245 * a_id)), width=4)
        # Left crimson architectural monolith stripe
        d.rounded_rectangle([24, 24, 52, ch - 24], radius=12, fill=(*C_EV_RED, int(255 * a_id)))

        f_tag = get_font(MONO_MED, 24)
        f_name = get_font(JAKARTA_EBOLD, 76)
        f_role = get_font(INTER_BOLD, 32)
        d.text((84, 34), "ENGEL & VÖLKERS  //  FEATURED INSTRUCTOR", font=f_tag, fill=(*C_EV_RED, int(255 * a_id)))
        d.text((84, 82), "ANDREW CROSSE", font=f_name, fill=(18, 18, 24, int(255 * a_id)))
        d.text((84, 184), "Real Estate Advisor & Community Builder", font=f_role, fill=(75, 78, 88, int(245 * a_id)))

        # Animated "TODAY'S MASTERCLASS" pill (lights up at 17.80s)
        mc_p = ease_motion(clamp((t - 17.65) / 0.36))
        pill_bg = C_EV_RED if mc_p > 0.1 else (32, 34, 42)
        d.rounded_rectangle([84, 252, 620, 322], radius=18, fill=(*pill_bg, int(245 * a_id)))
        d.text((112, 270), "★  TODAY'S REAL ESTATE MASTERCLASS", font=f_tag, fill=(255, 255, 255, int(255 * a_id)))

        warped = warp_plane_3d(card, rx_deg=4.5 * math.sin(age * 1.5), ry_deg=-4.0 * math.cos(age * 1.2), scale=0.96)
        base.alpha_composite(warped, ((W - cw) // 2, int(118 + dy_id)))

        if t < 17.85:
            draw_3tier_kinetic_lockup(
                base,
                age=max(0.0, t - 16.50),
                lead_text="My name is",
                hero_text="ANDREW CROSSE",
                script_text="Engel & Völkers",
                cy=1440,
                hero_color=C_GOLD,
                crimson_bar=False,
                echo_trail=True,
            )
        else:
            draw_3tier_kinetic_lockup(
                base,
                age=t - 17.85,
                lead_text="And in today's",
                hero_text="MASTERCLASS",
                script_text="leadership series",
                cy=1440,
                hero_color=C_GOLD,
                crimson_bar=True,
                echo_trail=False,
            )
    else:
        p_age = t - 18.90
        draw_top_editorial_pill(base, p_age, "MASTERCLASS CURRICULUM", "TWO CORE PILLARS", dark_theme=True)

        # Two 3D Pillar Cards in the upper space (y=150..540)
        pillars = [
            (0.05, "PILLAR 01", "BE A MENTOR", "IN REAL ESTATE", C_GOLD),
            (1.95, "PILLAR 02", "HOW TO BUILD", "COMMUNITIES", C_EV_RED),
        ]
        for idx, (delay, tag_s, line1, line2, accent) in enumerate(pillars):
            pa, pdy = data_reveal_state(p_age, delay=delay, dur=0.44, offset_y=30.0)
            if pa <= 0.02:
                continue
            cw, ch = 445, 340
            card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            d = ImageDraw.Draw(card)
            d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=28, fill=(20, 22, 30, int(238 * pa)), outline=(*accent, int(245 * pa)), width=3)
            d.rounded_rectangle([24, 24, 195, 68], radius=12, fill=(*accent, int(245 * pa)))
            fg_t = (16, 16, 20, int(255 * pa)) if accent == C_GOLD else (255, 255, 255, int(255 * pa))
            d.text((42, 32), tag_s, font=get_font(MONO_MED, 22), fill=fg_t)

            d.text((28, 96), line1, font=get_font(JAKARTA_EBOLD, 44), fill=(255, 255, 255, int(255 * pa)))
            d.text((28, 152), line2, font=get_font(JAKARTA_EBOLD, 44), fill=(*accent, int(255 * pa)))

            # Architectural wireframe icon inside card bottom
            if idx == 0:
                # Isometric luxury roof/house wireframe
                d.polygon([(70, 295), (140, 235), (210, 295)], outline=(*accent, int(230 * pa)), width=3)
                d.rectangle([92, 295, 188, 318], outline=(255, 255, 255, int(200 * pa)), width=2)
            else:
                # Interconnected community network nodes
                nodes = [(80, 285), (150, 245), (220, 285), (290, 250)]
                for n1, n2 in zip(nodes[:-1], nodes[1:]):
                    d.line([n1, n2], fill=(*C_GOLD, int(220 * pa)), width=3)
                for nx, ny in nodes:
                    d.ellipse([nx - 9, ny - 9, nx + 9, ny + 9], fill=(*accent, int(255 * pa)), outline=(255, 255, 255, int(240 * pa)), width=2)

            warped = warp_plane_3d(card, rx_deg=4.0, ry_deg=-5.0 if idx == 0 else 5.0, scale=0.96)
            px = 68 if idx == 0 else (W - cw - 68)
            base.alpha_composite(warped, (px, int(162 + pdy)))

        if t < 21.15:
            draw_3tier_kinetic_lockup(
                base,
                age=max(0.0, t - 19.10),
                lead_text="teach you how to be a",
                hero_text="MENTOR",
                script_text="in real estate",
                cy=1440,
                hero_color=C_GOLD,
                crimson_bar=False,
                echo_trail=True,
            )
        else:
            draw_3tier_kinetic_lockup(
                base,
                age=t - 21.15,
                lead_text="and how to build",
                hero_text="COMMUNITIES.",
                script_text="lasting impact",
                cy=1440,
                hero_color=C_GOLD,
                crimson_bar=True,
                echo_trail=False,
            )

    return base


# ---------------------------------------------------------------------------
# SCENE 6 (22.48s - 24.57s): Engel & Völkers Real Estate Masterclass End Card
# Preserves the iconic white E&V title lockup (y=580..980) & grey armchair (y=1350..1920)
# ---------------------------------------------------------------------------
def render_scene6_outro(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 22.48
    # Keep the crisp white background, original E&V logo, and armchair 100% clean
    im = Image.fromarray(raw_rgb).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Subtle architectural drafting lines in the upper white space (y=0..460)
    a_grid = clamp(age / 0.55)
    for gx in range(120, W, 140):
        od.line([(gx, 0), (gx, 460)], fill=(210, 205, 198, int(85 * a_grid)), width=1)
    for gy in range(90, 460, 90):
        od.line([(80, gy), (W - 80, gy)], fill=(210, 205, 198, int(85 * a_grid)), width=1)

    # Top editorial pill (y=96)
    draw_top_editorial_pill(im, age, "ENGEL & VÖLKERS", "LEADERSHIP & MENTORSHIP", dark_theme=False)

    # Animated Crimson + Gold accent bar wiping under "REAL ESTATE MASTERCLASS" (y=1015)
    wipe = swipe_bar_progress(max(0.0, age - 0.18), duration=0.52)
    bar_full = 460
    bw = int(bar_full * wipe)
    if bw > 4:
        bx = (W - bar_full) // 2
        od.rounded_rectangle([bx, 1018, bx + bw, 1030], radius=6, fill=(*C_EV_RED, 245))

    # Subtitle pill below the bar (y=1058)
    a_sub, dy_sub = data_reveal_state(age, delay=0.28, dur=0.46, offset_y=20.0)
    if a_sub > 0.02:
        f_sub = get_font(MONO_MED, 24)
        txt = "ANDREW CROSSE  •  MENTORSHIP & COMMUNITY"
        bb = od.textbbox((0, 0), txt, font=f_sub)
        tw = bb[2] - bb[0]
        px = (W - tw) // 2 - 24
        py = int(1062 + dy_sub)
        od.rounded_rectangle([px, py, px + tw + 48, py + 48], radius=24, fill=(24, 24, 30, int(235 * a_sub)))
        od.text((px + 24, py + 11), txt, font=f_sub, fill=(*C_GOLD, int(255 * a_sub)))

    im.alpha_composite(overlay)
    return im


# ---------------------------------------------------------------------------
# Master Frame Dispatcher + Harvested Seam Transitions (`motion_engine.py`)
# ---------------------------------------------------------------------------
def _render_raw_scene(raw_rgb: np.ndarray, t: float) -> Image.Image:
    if t < 4.00:
        return render_scene1_hook(raw_rgb, t)
    if t < 5.85:
        return render_scene2_get_over_it(raw_rgb, t)
    if t < 7.22:
        return render_scene3_what(raw_rgb, t)
    if t < 10.60:
        return render_scene4a_checklist(raw_rgb, t)
    if t < 12.50:
        return render_scene4b_accordion(raw_rgb, t)
    if t < 16.12:
        return render_scene4c_split_staircase(raw_rgb, t)
    if t < 22.48:
        return render_scene5_masterclass(raw_rgb, t)
    return render_scene6_outro(raw_rgb, t)


SEAMS = [
    (4.00, 0.24, "cut_the_curve"),
    (5.85, 0.22, "zoom_through"),
    (7.22, 0.24, "rack_focus"),
    (12.50, 0.26, "cut_the_curve"),
    (16.12, 0.28, "rack_focus"),
    (22.48, 0.28, "zoom_through"),
]


def render_frame(raw_rgb: np.ndarray, prev_raw_rgb: np.ndarray, t: float) -> np.ndarray:
    for t_seam, half_w, mode in SEAMS:
        if abs(t - t_seam) <= half_w:
            p = clamp((t - (t_seam - half_w)) / (2.0 * half_w))
            # Use prev_raw_rgb before the camera cut and raw_rgb after the cut
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
# Procedural Cinema SFX & Warm Ambient Bed Mixer (mixed with original speech)
# ---------------------------------------------------------------------------
def build_master_audio_mix(ffmpeg_exe: str, duration: float):
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

    # Subtle warm cinema pad (D minor 9th: D2=73.42Hz, A2=110Hz, F3=174.61Hz, E4=329.63Hz)
    # kept very gentle (-24 dB) so Andrew's voice is 100% crystal clear
    pad_l = (
        0.018 * np.sin(2 * np.pi * 73.42 * t)
        + 0.012 * np.sin(2 * np.pi * 110.00 * t + 0.3)
        + 0.008 * np.sin(2 * np.pi * 174.61 * t + 0.7)
    )
    pad_r = (
        0.018 * np.sin(2 * np.pi * 73.42 * t)
        + 0.012 * np.sin(2 * np.pi * 110.00 * t - 0.3)
        + 0.008 * np.sin(2 * np.pi * 329.63 * t + 0.4)
    )

    sfx_l = np.zeros_like(t)
    sfx_r = np.zeros_like(t)

    # Cinema whooshes & sub-bass hits on key cuts and hero reveals
    cues = [
        (0.10, "hit"),
        (2.15, "whoosh"),
        (4.00, "whoosh"),
        (5.85, "hit"),
        (6.38, "hit"),
        (7.22, "whoosh"),
        (8.90, "click"),
        (10.60, "whoosh"),
        (12.50, "whoosh"),
        (14.85, "hit"),
        (16.12, "whoosh"),
        (17.85, "hit"),
        (19.10, "click"),
        (21.15, "hit"),
        (22.48, "whoosh"),
    ]
    rng = np.random.default_rng(42)
    for cue_t, kind in cues:
        i0 = int(cue_t * sr)
        if i0 >= total_samples:
            continue
        if kind == "whoosh":
            dur_s = int(0.32 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.6
            noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32)
            sweep = np.sin(2 * np.pi * (95.0 + 240.0 * lt) * lt * 0.32)
            w_sig = (0.045 * sweep + 0.018 * noise) * env
            sfx_l[i0:i1] += w_sig * (1.0 - 0.3 * lt)
            sfx_r[i0:i1] += w_sig * (0.7 + 0.3 * lt)
        elif kind == "hit":
            dur_s = int(0.38 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-lt * 8.5)
            sub = 0.075 * np.sin(2 * np.pi * (88.0 * np.exp(-lt * 2.4)) * lt * 0.38) * env
            sfx_l[i0:i1] += sub
            sfx_r[i0:i1] += sub
        elif kind == "click":
            dur_s = int(0.045 * sr)
            i1 = min(total_samples, i0 + dur_s)
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.exp(-lt * 24.0)
            clk = 0.05 * np.sin(2 * np.pi * 1250.0 * lt * 0.045) * env
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
    duration = total_frames / FPS

    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        sample_times = [
            0.85, 2.55, 4.35, 5.20,
            6.55, 7.60, 8.45, 9.60,
            11.40, 12.90, 13.90, 15.35,
            17.20, 18.35, 20.10, 23.60,
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
            td.text((14, 13), f"t={st:05.2f}s", fill=(255, 226, 44))
            sheet.paste(thumb, ((idx % cols) * tw, (idx // cols) * th))
        sheet.save(args.preview, quality=92)
        print(f"Saved preview contact sheet to {args.preview}")
        return

    os.makedirs(FILM_DIR, exist_ok=True)
    build_master_audio_mix(ffmpeg_exe, duration)

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
        # Keep a 2-frame delayed reference for seam transitions across camera cuts
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
