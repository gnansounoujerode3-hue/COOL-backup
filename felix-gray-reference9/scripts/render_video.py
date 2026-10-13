#!/usr/bin/env python3
"""
Renders `felix-gray-reference9-9x16.mp4` (1080x1920, 30.00 fps, 54.85s) from
`video brut 9.mp4`, combining every visual and motion signature of `reference9.mp4`
with the exact motion-design methodology of `MOTION-DESIGN.md`:

  - Master Easing Curve: `--motion-ease-out: cubic-bezier(0.2, 0.8, 0.2, 1.0)`
    (no aggressive overshoot bounces; smooth acceleration/deceleration).
  - Directional `[data-reveal]` Entrances: `opacity: 0 -> 1` paired with
    `transform: translateY(14px) -> translateY(0)` (28px at 1080p) over
    `--motion-enter: 480ms`, with secondary elements staggered by `60ms` (40–80ms).
  - Rhythm Benchmarks from `MOTION-DESIGN.md`:
      * Active/press feedback (`scale(0.98)`): 140ms (100–180ms)
      * Hover/focus control state (`translateY(-2px)`, `:focus-visible` outline): 180ms (150–220ms)
      * State transition / small reveal: 300ms (220–400ms)
      * Primary section entrance: 480ms (400–650ms)
      * Narrative camera pan / GSAP DrawSVG contour trace: 680–750ms (500–900ms)
  - Exact Frame-by-Frame Transitions from `reference9.mp4`:
      * Progressive SVG contour drawing (`draw_progressive_polyline`)
      * 3D connecting plugs approaching the twin spotlight cores (`8.30–10.75s`)
      * Diagonal neon blue/crimson light-ribbon wipe (`17.30–17.66s`, `35.30–35.66s`)
      * Live cursor-driven text selection (`|early awareness|`, `|technical skills|`)
      * Two-state wireframe card transition with Border Beam (`what the -> the construction PROCESS`)
      * Staggered directional reveal (`ARCHI -> ARCHITECT`) + blazing diagonal golden-red
        light beam transition (`30.08–30.35s`, matching `t=17.85s` in `reference9.mp4`).
"""
import argparse
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30.0
DURATION = 54.85
TOTAL_FRAMES = int(round(DURATION * FPS))

# Rhythm benchmarks from MOTION-DESIGN.md
MOTION_FAST = 0.180      # 180ms (hover/focus/active feedback: 100–220ms)
MOTION_STATE = 0.300     # 300ms (state transition or small reveal: 220–400ms)
MOTION_ENTER = 0.480     # 480ms (--motion-enter primary reveal: 400–650ms)
MOTION_SEQUENCE = 0.720  # 720ms (narrative camera pan / SVG trace: 500–900ms)
MOTION_STAGGER = 0.060   # 60ms  (secondary element cascade stagger: 40–80ms)
REVEAL_OFFSET_Y = 28     # 14px CSS -> 28px at 1080x1920 retina scale

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
MONTSERRAT_BLACK_IT = f"{FONT_BASE}/montserrat/900Black_Italic/Montserrat_900Black_Italic.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"

_FONT_CACHE = {}


def get_font(path: str, size: int):
    sz = max(12, int(round(size)))
    key = (path, sz)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, sz)
    return _FONT_CACHE[key]


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def cubic_bezier_cool(x: float, x1=0.2, y1=0.8, x2=0.2, y2=1.0) -> float:
    """
    Exact solver for `--motion-ease-out: cubic-bezier(.2, .8, .2, 1)` from MOTION-DESIGN.md.
    Smooth, fast initial response with a gentle, zero-overshoot deceleration.
    """
    x = clamp(x, 0.0, 1.0)
    if x <= 0.0 or x >= 1.0:
        return x
    u = x
    for _ in range(6):
        bx = 3.0 * ((1.0 - u) ** 2) * u * x1 + 3.0 * (1.0 - u) * (u ** 2) * x2 + (u ** 3) - x
        dbx = (
            3.0 * ((1.0 - u) ** 2) * x1
            + 6.0 * (1.0 - u) * u * (x2 - x1)
            + 3.0 * (u ** 2) * (1.0 - x2)
        )
        if abs(dbx) < 1e-6:
            break
        u = clamp(u - bx / dbx, 0.0, 1.0)
    return 3.0 * ((1.0 - u) ** 2) * u * y1 + 3.0 * (1.0 - u) * (u ** 2) * y2 + (u ** 3)


def data_reveal(age: float, duration: float = MOTION_ENTER, offset_y: float = REVEAL_OFFSET_Y):
    """
    Implements `[data-reveal]` from MOTION-DESIGN.md:
      opacity: 0 -> 1
      transform: translateY(14px) -> translateY(0)
      transition: var(--motion-enter) var(--motion-ease-out)
    Returns (alpha_0_to_1, dy_pixels).
    """
    p = cubic_bezier_cool(age / max(0.001, duration))
    return p, (1.0 - p) * offset_y


def draw_progressive_polyline(
    draw: ImageDraw.ImageDraw,
    pts: list,
    progress: float,
    fill: tuple,
    width: int = 4,
):
    """
    GSAP DrawSVG-style progressive vector path drawing along a polyline.
    """
    p = cubic_bezier_cool(progress)
    if p <= 0.001 or len(pts) < 2:
        return
    seg_lens = []
    total_len = 0.0
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        d = math.hypot(dx, dy)
        seg_lens.append(d)
        total_len += d
    if total_len <= 1e-3:
        return

    target_len = total_len * p
    out_pts = [pts[0]]
    acc = 0.0
    for i, slen in enumerate(seg_lens):
        if acc + slen <= target_len:
            out_pts.append(pts[i + 1])
            acc += slen
        else:
            rem = target_len - acc
            frac = clamp(rem / max(1e-4, slen))
            nx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * frac
            ny = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * frac
            out_pts.append((nx, ny))
            break
    if len(out_pts) >= 2:
        draw.line(out_pts, fill=fill, width=width, joint="curve")


# ---------------------------------------------------------------------------
# Color Grade & Anamorphic Light Leaks on Talking Head
# ---------------------------------------------------------------------------
def grade_talking_head(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    f = frame_rgb.astype(np.float32) / 255.0
    f = np.clip((f - 0.5) * 1.08 + 0.50, 0.0, 1.0)
    f[:, :, 0] = np.clip(f[:, :, 0] * 1.02, 0.0, 1.0)
    f[:, :, 2] = np.clip(f[:, :, 2] * 0.98, 0.0, 1.0)
    return np.clip(f * 255.0, 0, 255).astype(np.uint8)


_LIGHT_LEAK_BLUE = None
_LIGHT_LEAK_RED = None


def get_light_leaks():
    global _LIGHT_LEAK_BLUE, _LIGHT_LEAK_RED
    if _LIGHT_LEAK_BLUE is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        wx = np.exp(-((xx / W) ** 2) / (2 * 0.22 ** 2))
        wy = np.exp(-(((yy / H) - 0.45) ** 2) / (2 * 0.48 ** 2))
        w_blue = (wx * wy)[:, :, None]
        blue_col = np.array([36.0, 92.0, 255.0], dtype=np.float32)[None, None, :]
        _LIGHT_LEAK_BLUE = w_blue * blue_col

        wx_r = np.exp(-((xx / W) ** 2) / (2 * 0.30 ** 2))
        wy_r = np.exp(-(((yy / H) - 0.50) ** 2) / (2 * 0.50 ** 2))
        w_red = (wx_r * wy_r)[:, :, None]
        red_col = np.array([235.0, 48.0, 38.0], dtype=np.float32)[None, None, :]
        _LIGHT_LEAK_RED = w_red * red_col
    return _LIGHT_LEAK_BLUE, _LIGHT_LEAK_RED


def apply_light_leak(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    blue_leak, red_leak = get_light_leaks()
    out = frame_rgb.astype(np.float32)

    blue_windows = [
        (5.65, 6.45, 0.85),
        (20.55, 21.45, 0.90),
        (30.35, 31.30, 0.78),
        (43.40, 44.35, 0.88),
    ]
    for t0, t1, peak in blue_windows:
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            env = math.sin(math.pi * p) ** 1.3 * peak
            out = np.clip(out + blue_leak * env, 0, 255)

    red_windows = [
        (14.10, 14.65, 0.82),
        (38.45, 39.15, 0.85),
    ]
    for t0, t1, peak in red_windows:
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            env = math.sin(math.pi * p) ** 1.4 * peak
            out = np.clip(out + red_leak * env, 0, 255)

    return out.astype(np.uint8)


# ---------------------------------------------------------------------------
# Technical Viewfinder / Film-HUD Overlay
# ---------------------------------------------------------------------------
_HUD_DARK_CACHE = None
_HUD_LIGHT_CACHE = None


def get_hud_overlay(mode: str = "dark") -> Image.Image:
    global _HUD_DARK_CACHE, _HUD_LIGHT_CACHE
    if mode == "dark" and _HUD_DARK_CACHE is not None:
        return _HUD_DARK_CACHE
    if mode == "light" and _HUD_LIGHT_CACHE is not None:
        return _HUD_LIGHT_CACHE

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    col_main = (225, 232, 245, 175) if mode == "dark" else (35, 38, 44, 185)
    col_dim = (225, 232, 245, 90) if mode == "dark" else (35, 38, 44, 95)
    f_mono = get_font(MONO_MED, 18)

    d.line([(52, 80), (52, 920)], fill=col_dim, width=2)
    d.line([(52, 1340), (52, 1840)], fill=col_dim, width=2)
    d.line([(1028, 80), (1028, 390)], fill=col_dim, width=2)
    d.line([(1028, 600), (1028, 960)], fill=col_dim, width=2)
    d.line([(1028, 1240), (1028, 1840)], fill=col_dim, width=2)

    lbl_tl = Image.new("RGBA", (140, 40), (0, 0, 0, 0))
    dtl = ImageDraw.Draw(lbl_tl)
    dtl.text((0, 6), "45  +  G", font=f_mono, fill=col_main)
    lbl_tl_rot = lbl_tl.rotate(-90, expand=True)
    img.alpha_composite(lbl_tl_rot, (28, 96))

    for i in range(11):
        yy = 415 + i * 14
        d.line([(1020, yy + 6), (1036, yy - 6)], fill=col_main, width=2)

    lbl_r = Image.new("RGBA", (220, 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lbl_r)
    dr.text((0, 6), "456 JK  /  789 0", font=f_mono, fill=col_main)
    lbl_r_rot = lbl_r.rotate(-90, expand=True)
    img.alpha_composite(lbl_r_rot, (1006, 995))

    for i in range(13):
        yy = 980 + i * 22
        w_tick = 12 if i % 3 == 0 else 6
        d.line([(46, yy), (46 + w_tick, yy)], fill=col_main, width=2)

    for cx, cy in [(86, 52), (994, 52), (86, 1868), (994, 1868)]:
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=col_main)

    if mode == "dark":
        _HUD_DARK_CACHE = img
    else:
        _HUD_LIGHT_CACHE = img
    return img


# ---------------------------------------------------------------------------
# Beat 1 (0.00s - 5.65s): 3D Z-Space Dark Blueprint & Node Canvas
# (Follows MOTION-DESIGN.md: 1 unified camera motion per state + `[data-reveal]`
# `translateY(28px) -> 0` with `cubic-bezier(0.2, 0.8, 0.2, 1.0)` + DrawSVG curve)
# ---------------------------------------------------------------------------
def render_zspace_opening(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (3, 4, 8, 255))
    d = ImageDraw.Draw(img)

    # Smooth narrative camera Z-progression (MOTION_SEQUENCE = 720ms per step)
    cam_z = (
        cubic_bezier_cool((t - 0.54) / MOTION_SEQUENCE) * 1.0
        + cubic_bezier_cool((t - 1.58) / MOTION_SEQUENCE) * 1.0
        + cubic_bezier_cool((t - 3.65) / MOTION_SEQUENCE) * 1.0
    )

    # 1. Background technical blueprint grid on the right half
    grid_shift_x = int(-cam_z * 26)
    grid_shift_y = int(cam_z * 20)
    grid_col = (24, 38, 66, 95)
    for gx in range(520 + grid_shift_x, W + 120, 72):
        d.line([(gx, 180), (gx, 1740)], fill=grid_col, width=1)
    for gy in range(260 + grid_shift_y, 1680, 72):
        d.line([(480, gy), (W, gy)], fill=grid_col, width=1)
    for gx in range(592 + grid_shift_x, W, 144):
        for gy in range(332 + grid_shift_y, 1600, 144):
            d.line([(gx - 6, gy), (gx + 6, gy)], fill=(48, 76, 130, 140), width=2)
            d.line([(gx, gy - 6), (gx, gy + 6)], fill=(48, 76, 130, 140), width=2)

    # 2. Progressive GSAP DrawSVG golden-ochre contour curve (starts drawing at t=1.60s over 800ms,
    #    matching t=1.65s -> 2.50s -> 3.10s in ref9_motion_strip.jpg)
    if t >= 1.60:
        pts = []
        for idx in range(60):
            u = idx / 59.0
            py = int(80 + u * 1760)
            px = int(650 + 230 * math.sin(u * 3.6 - cam_z * 0.42) + 80 * math.cos(u * 7.2))
            pts.append((px, py))
        draw_progressive_polyline(
            d,
            pts,
            progress=(t - 1.60) / 0.82,
            fill=(172, 128, 56, 205),
            width=5,
        )

    # 3. Floating dark-glass notification pills with royal-blue icon circles & Magic UI shimmer
    pills = [
        (0.10, 150, 1020, 0.2, "Site Blueprint CAD"),
        (1.05, 760, 1280, 1.0, "Hey, I'm an architect..."),
        (1.85, 680, 620, 1.8, "Structural Studio"),
        (2.70, 260, 880, 2.3, "Technical College"),
    ]
    for t_app, bx, by, bz, label in pills:
        if t < t_app:
            continue
        age = t - t_app
        alpha_p, dy_rev = data_reveal(age, duration=MOTION_STATE, offset_y=20)
        rel_z = max(0.0, cam_z - bz * 0.55)
        scale = clamp(1.0 / (1.0 + rel_z * 0.42), 0.36, 1.0)
        alpha = int(alpha_p * clamp(1.0 - rel_z * 0.28, 0.25, 0.92) * 255)

        pw, ph = int(340 * scale), int(76 * scale)
        px = int(bx + (W * 0.52 - bx) * (1.0 - 1.0 / (1.0 + rel_z * 0.35)))
        py = int(by + dy_rev + (H * 0.46 - by) * (1.0 - 1.0 / (1.0 + rel_z * 0.35)))

        pill_layer = Image.new("RGBA", (pw + 20, ph + 20), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_layer)
        pd.rounded_rectangle(
            [6, 6, pw + 6, ph + 6],
            radius=ph // 2,
            fill=(14, 20, 34, int(alpha * 0.86)),
            outline=(52, 88, 165, int(alpha * 0.75)),
            width=max(1, int(2 * scale)),
        )
        # Subtle Magic UI shimmer reflection sweeping across the pill on arrival (0.15s..0.55s)
        if 0.10 <= age <= 0.58:
            sh_p = cubic_bezier_cool((age - 0.10) / 0.48)
            sx = int(12 + sh_p * (pw - 24))
            pd.line(
                [(sx, 8), (sx + int(28 * scale), 8)],
                fill=(150, 200, 255, int(alpha * (1.0 - sh_p))),
                width=max(2, int(3 * scale)),
            )

        r_cir = int(ph * 0.38)
        cx_c, cy_c = 6 + int(ph * 0.52), 6 + ph // 2
        pd.ellipse(
            [cx_c - r_cir, cy_c - r_cir, cx_c + r_cir, cy_c + r_cir],
            fill=(36, 98, 255, alpha),
        )
        s_tri = max(3, int(7 * scale))
        pd.polygon(
            [(cx_c - s_tri, cy_c - s_tri // 2), (cx_c + s_tri, cy_c - s_tri), (cx_c, cy_c + s_tri)],
            fill=(255, 255, 255, alpha),
        )
        f_pill = get_font(INTER_MED, max(12, int(24 * scale)))
        pd.text(
            (cx_c + r_cir + int(14 * scale), cy_c - int(13 * scale)),
            label,
            font=f_pill,
            fill=(188, 206, 238, int(alpha * 0.92)),
        )
        if rel_z > 0.6:
            pill_layer = pill_layer.filter(ImageFilter.GaussianBlur(radius=min(3.5, rel_z * 1.4)))
        img.alpha_composite(pill_layer, (px - pw // 2, py - ph // 2))

    # 4. 3D Z-Space Kinetic Phrases using `[data-reveal]` (translateY(28px) -> 0 + 60ms line stagger)
    phrases = [
        (0.04, 0.0, 360, 920, 290, 780, [("i got into", 68, INTER_MED)], "left"),
        (0.54, 1.0, 410, 720, 560, 580, [("architecture.", 84, INTER_BOLD)], "center"),
        (
            1.58,
            2.0,
            340,
            1160,
            280,
            1260,
            [("construction", 82, INTER_BOLD), ("my dad taught", 48, INTER_REG)],
            "left",
        ),
        (
            3.65,
            3.0,
            510,
            900,
            540,
            860,
            [("at a local", 48, INTER_REG), ("technical", 92, INTER_BOLD), ("college.", 54, INTER_MED)],
            "center",
        ),
    ]

    for t_in, z_idx, tx, ty, vx, vy, lines, align in phrases:
        if t < t_in:
            continue
        age = t - t_in
        depth_behind = max(0.0, cam_z - z_idx)
        scale = 1.0 / (1.0 + depth_behind * 0.62)
        depth_fade = clamp(1.0 - depth_behind * 0.36, 0.20, 1.0)

        z_pull = 1.0 - 1.0 / (1.0 + depth_behind * 0.55)
        cx = int(tx + (vx - tx) * z_pull)
        cy = int(ty + (vy - ty) * z_pull)

        layer = Image.new("RGBA", (820, 380), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cur_y = 40
        for l_idx, (txt, base_sz, f_path) in enumerate(lines):
            # 60ms stagger per secondary line (MOTION-DESIGN.md: 40–80ms)
            line_age = max(0.0, age - l_idx * MOTION_STAGGER)
            rev_a, rev_dy = data_reveal(line_age, duration=MOTION_ENTER, offset_y=26 * scale)
            line_alpha = int(rev_a * depth_fade * 255)
            if line_alpha <= 2:
                cur_y += int(base_sz * scale * 1.04)
                continue
            sz = max(14, int(base_sz * scale))
            fnt = get_font(f_path, sz)
            bbox = ld.textbbox((0, 0), txt, font=fnt)
            tw = bbox[2] - bbox[0]
            lx = (820 - tw) // 2 if align == "center" else 90
            ld.text((lx, int(cur_y + rev_dy)), txt, font=fnt, fill=(248, 244, 232, line_alpha))
            cur_y += int(sz * 1.04)

        if depth_behind < 0.35:
            glow = layer.filter(ImageFilter.GaussianBlur(radius=8))
            img.alpha_composite(glow, (cx - 410, cy - 140))
        elif depth_behind > 0.65:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=min(3.0, depth_behind * 1.2)))

        img.alpha_composite(layer, (cx - 410, cy - 140))

    # 5. Cobalt-blue CRT / blueprint scanline flash at 5.25s - 5.65s
    if 5.25 <= t <= 5.65:
        p = (t - 5.25) / 0.40
        flash_a = int(math.sin(math.pi * p) * 215)
        crt = Image.new("RGBA", (W, H), (10, 26, 118, flash_a))
        cd = ImageDraw.Draw(crt)
        for sy in range(0, H, 10):
            cd.line([(0, sy), (W, sy)], fill=(28, 72, 235, int(flash_a * 0.75)), width=3)
        img = Image.alpha_composite(img, crt)

    return img


# ---------------------------------------------------------------------------
# Beat 2B (8.30s - 10.75s): Dark HUD Viewfinder Spotlight + 3D Connecting Plugs
# (Exact replica of t=4.60s - 6.10s in ref9_motion_strip.jpg + MOTION-DESIGN.md)
# ---------------------------------------------------------------------------
def render_dark_spotlight_hud(t: float) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r_ch = np.clip(6.0 + 18.0 * np.exp(-(((yy - 940) / 380) ** 2)), 0, 255)
    g_ch = np.clip(14.0 + 36.0 * np.exp(-(((yy - 940) / 420) ** 2)), 0, 255)
    b_ch = np.clip(22.0 + 48.0 * np.exp(-(((yy - 940) / 460) ** 2)), 0, 255)

    # Twin warm amber spotlight cores at center (matching t=4.60s..6.10s)
    age = t - 8.30
    sep = 45.0 + 32.0 * cubic_bezier_cool(max(0.0, (t - 9.40) / 0.85))
    for lx in (540.0 - sep, 540.0 + sep):
        d2 = ((xx - lx) / 36.0) ** 2 + ((yy - 920.0) / 26.0) ** 2
        glow = np.exp(-d2 * 0.5)
        halo = np.exp(-(((xx - lx) / 160.0) ** 2 + ((yy - 920.0) / 95.0) ** 2) * 0.5)
        r_ch += glow * 245.0 + halo * 85.0
        g_ch += glow * 195.0 + halo * 58.0
        b_ch += glow * 130.0 + halo * 28.0

    refl = np.exp(-(((yy - 1320.0) / 22.0) ** 2)) * np.exp(-(((xx - 540.0) / 340.0) ** 2))
    r_ch += refl * 35.0
    g_ch += refl * 65.0
    b_ch += refl * 95.0

    arr = np.stack([np.clip(r_ch, 0, 255), np.clip(g_ch, 0, 255), np.clip(b_ch, 0, 255)], axis=-1).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGBA")
    d = ImageDraw.Draw(img)

    # 3D cylindrical cables & plugs extending from left/right edges to the twin lights (matching t=6.10s)
    plug_p = cubic_bezier_cool(max(0.0, (t - 8.50) / 0.80))
    lx_end = int(540 - sep - 18)
    rx_end = int(540 + sep + 18)
    # Left cable & plug body
    d.line([(0, 965), (int(lx_end * plug_p), 924)], fill=(46, 58, 72, 220), width=16)
    d.line([(0, 961), (int(lx_end * plug_p), 920)], fill=(95, 118, 142, 180), width=4)
    # Right cable & plug body
    rx_start = int(W - (W - rx_end) * plug_p)
    d.line([(W, 975), (rx_start, 924)], fill=(46, 58, 72, 220), width=16)
    d.line([(W, 971), (rx_start, 920)], fill=(95, 118, 142, 180), width=4)

    img.alpha_composite(get_hud_overlay("dark"))

    # Top-left caption "from day one" rising smoothly (matching "in 2025" at t=4.60s->5.60s)
    if t >= 8.35:
        a1, dy1 = data_reveal(t - 8.35, duration=MOTION_ENTER, offset_y=32)
        drift_up = cubic_bezier_cool((t - 8.35) / 2.2) * 48.0
        f_top = get_font(INTER_REG, 64)
        d.text((225, int(545 + dy1 - drift_up)), "from day one", font=f_top, fill=(220, 232, 242, int(a1 * 240)))

    # Lower spatial words with 60ms-style sequential `[data-reveal]`
    if t >= 8.95:
        a2, dy2 = data_reveal(t - 8.95, duration=MOTION_STATE, offset_y=24)
        f_w1 = get_font(INTER_MED, 74)
        d.text((545, int(1065 + dy2)), "dragged", font=f_w1, fill=(248, 244, 232, int(a2 * 255)))

    if t >= 9.30:
        a3, dy3 = data_reveal(t - 9.30, duration=MOTION_STATE, offset_y=24)
        f_w2 = get_font(INTER_REG, 66)
        d.text((310, int(1145 + dy3)), "onto", font=f_w2, fill=(232, 228, 218, int(a3 * 240)))

    if t >= 9.68:
        a4, dy4 = data_reveal(t - 9.68, duration=MOTION_ENTER, offset_y=28)
        f_w3 = get_font(INTER_BOLD, 78)
        d.text((310, int(1225 + dy4)), "building sites.", font=f_w3, fill=(252, 248, 238, int(a4 * 255)))

    return img


# ---------------------------------------------------------------------------
# Beat 3A (10.75s - 14.10s): Cream Drafting-Paper + Progressive SVG Contours +
# Black Portal & 3 Interactive Sky-Blue UI Pills (hover/active/focus-visible)
# ---------------------------------------------------------------------------
def render_cream_portal_pills(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, 390, 68], fill=(10, 10, 12, 255))

    age = t - 10.75

    # Progressive GSAP DrawSVG contour lines (MOTION_SEQUENCE = 720ms)
    gold_pts = [(0, 420), (145, 510), (95, 760), (210, 1180), (0, 1480)]
    draw_progressive_polyline(d, gold_pts, age / MOTION_SEQUENCE, fill=(217, 164, 65, 220), width=4)

    red_tl = [(265, 68), (235, 195), (165, 290), (138, 430), (65, 545), (48, 720), (0, 795)]
    draw_progressive_polyline(d, red_tl, age / MOTION_SEQUENCE, fill=(216, 67, 46, 255), width=20)

    red_br = [(1080, 1320), (960, 1490), (885, 1560), (745, 1690), (540, 1850), (465, 1920)]
    draw_progressive_polyline(d, red_br, (age - 0.12) / MOTION_SEQUENCE, fill=(216, 67, 46, 255), width=32)

    img.alpha_composite(get_hud_overlay("light"))

    # Central deep-black circular portal with smooth cubic-bezier entrance (zero bounce)
    p_portal = cubic_bezier_cool(age / MOTION_ENTER)
    r_p = int(282 * (0.86 + 0.14 * p_portal))
    cx, cy = 540, 1020
    d.ellipse([cx - r_p, cy - r_p, cx + r_p, cy + r_p], fill=(6, 10, 16, int(255 * p_portal)))
    d.ellipse(
        [cx - r_p + 6, cy - r_p + 6, cx + r_p - 6, cy + r_p - 6],
        outline=(28, 56, 88, int(135 * p_portal)),
        width=4,
    )

    # 3 stacked sky-blue rounded pills (#4294FF) following MOTION-DESIGN.md `.button` rules:
    #   - `[data-reveal]` entrance: opacity 0->1 + translateY(26px)->0 over 320ms (`cubic_bezier_cool`)
    #   - `:hover` state: translateY(-4px) over 180ms (`MOTION_FAST`)
    #   - `:active` press state: scale(0.98) over 140ms
    #   - `:focus-visible` outline on final pill + Magic UI shimmer sweep
    pills_spec = [
        (11.00, -118, 390, 74, "When I was young", 34),
        (12.15, -24, 420, 78, "Kicking my heels...", 36),
        (13.00, 92, 600, 134, "During summer\nholidays!", 48),
    ]
    for idx, (t_in, y_off, pw, ph, txt, fsz) in enumerate(pills_spec):
        if t < t_in:
            continue
        p_age = t - t_in
        rev_a, rev_dy = data_reveal(p_age, duration=MOTION_STATE, offset_y=26)

        # Interactive `.button:active` (100-180ms press) -> `.button:hover` (-4px lift)
        press_scale = 1.0
        hover_dy = 0.0
        if 0.24 <= p_age <= 0.40:
            # 160ms active press pulse (`transform: scale(.98)`)
            press_w = math.sin(math.pi * (p_age - 0.24) / 0.16)
            press_scale = 1.0 - 0.025 * press_w
        elif p_age > 0.40:
            hover_dy = -4.0 * cubic_bezier_cool((p_age - 0.40) / MOTION_FAST)

        cw, ch = int(pw * press_scale), int(ph * press_scale)
        pill_img = Image.new("RGBA", (cw + 48, ch + 48), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_img)

        alpha_i = int(rev_a * 255)
        # Soft drop shadow
        pd.rounded_rectangle(
            [24, 30, 24 + cw, 30 + ch],
            radius=min(38, ch // 2),
            fill=(0, 0, 0, int(rev_a * 140)),
        )
        # Sky-blue pill body (#4294FF)
        pd.rounded_rectangle(
            [22, 22, 22 + cw, 22 + ch],
            radius=min(38, ch // 2),
            fill=(66, 148, 255, alpha_i),
            outline=(155, 206, 255, int(rev_a * 235)),
            width=2,
        )
        # `:focus-visible` ring on the active/featured 3rd pill (MOTION-DESIGN.md)
        if idx == 2 and p_age >= 0.28:
            foc_a = int(cubic_bezier_cool((p_age - 0.28) / MOTION_FAST) * 210)
            pd.rounded_rectangle(
                [16, 16, 28 + cw, 28 + ch],
                radius=min(44, ch // 2 + 6),
                outline=(255, 255, 255, foc_a),
                width=3,
            )

        # Magic UI shimmer reflection sweeping across the pill (360ms)
        if 0.18 <= p_age <= 0.56:
            sh_p = cubic_bezier_cool((p_age - 0.18) / 0.38)
            sx = int(30 + sh_p * (cw - 60))
            pd.line(
                [(sx, 24), (sx + 48, 24)],
                fill=(255, 255, 255, int(alpha_i * (1.0 - sh_p) * 0.9)),
                width=3,
            )

        f_p = get_font(INTER_MED, int(fsz * press_scale))
        lines = txt.split("\n")
        total_h = len(lines) * int(fsz * press_scale * 1.12)
        cur_y = 22 + (ch - total_h) // 2 - 4
        for line in lines:
            bb = pd.textbbox((0, 0), line, font=f_p)
            tw = bb[2] - bb[0]
            tx = 22 + (cw - tw) // 2
            pd.text((tx, cur_y), line, font=f_p, fill=(255, 255, 255, alpha_i))
            cur_y += int(fsz * press_scale * 1.12)

        pill_rot = pill_img.rotate(2.2 if idx % 2 == 0 else -1.8, resample=Image.BICUBIC, expand=True)
        px = cx - pill_rot.width // 2 + (-22 if idx == 0 else (28 if idx == 1 else -8))
        py = int(cy + y_off + rev_dy + hover_dy - pill_rot.height // 2)
        img.alpha_composite(pill_rot, (px, py))

    return img


# ---------------------------------------------------------------------------
# Beat 4 (17.30s - 20.55s) & Beat 6B (35.30s - 38.45s):
# Diagonal Neon Blue/Crimson Light-Ribbon Wipe -> Live Cursor-Driven Text Selection
# -> Two-State Wireframe Card with Border Beam & Progressive Red SVG Contour
# (Exact replica of t=8.20s - 10.85s in ref9_motion_strip.jpg + MOTION-DESIGN.md)
# ---------------------------------------------------------------------------
def draw_wireframe_cursor(canvas: Image.Image, cx: int, cy: int, angle_deg: float, scale: float = 1.0):
    size = int(110 * scale)
    c_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(c_img)
    pts = [(24, 16), (24, 82), (42, 66), (56, 94), (68, 88), (54, 60), (78, 58)]
    pts_scaled = [(int(x * scale), int(y * scale)) for x, y in pts]
    cd.polygon(pts_scaled, fill=(12, 16, 22, 185), outline=(238, 242, 250, 240), width=3)
    rot = c_img.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(rot, (cx - rot.width // 2, cy - rot.height // 2))


def render_dark_selection_and_stamp(
    t: float,
    t_start: float,
    t_mid: float,
    t_end: float,
    sel_top_text: str,
    sel_bot_text: str,
    state1_top: str,
    state1_bot: str,
    stamp_top_text: str,
    stamp_blue_word: str,
) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r_ch = np.full((H, W), 5.0, dtype=np.float32)
    g_ch = np.full((H, W), 7.0, dtype=np.float32)
    b_ch = np.full((H, W), 12.0, dtype=np.float32)

    # Warm tungsten horizontal lens flare at upper-right (matching t=8.55s & t=10.85s)
    flare_core = np.exp(-(((xx - 980.0) / 140.0) ** 2 + ((yy - 560.0) / 38.0) ** 2) * 0.5)
    flare_streak = np.exp(-(((yy - 560.0) / 14.0) ** 2)) * np.exp(-(((xx - 720.0) / 480.0) ** 2))
    flare_left = np.exp(-(((xx - 160.0) / 220.0) ** 2 + ((yy - 650.0) / 120.0) ** 2) * 0.5)
    r_ch += flare_core * 250.0 + flare_streak * 185.0 + flare_left * 75.0
    g_ch += flare_core * 175.0 + flare_streak * 95.0 + flare_left * 32.0
    b_ch += flare_core * 95.0 + flare_streak * 35.0 + flare_left * 18.0

    c_glow = np.exp(-(((xx - 540.0) / 260.0) ** 2 + ((yy - 950.0) / 190.0) ** 2) * 0.5)
    r_ch += c_glow * 36.0
    g_ch += c_glow * 42.0
    b_ch += c_glow * 58.0

    # Diagonal Neon Blue/Crimson Light-Ribbon Wipe during first 380ms (exact match to t=8.20s in ref9_motion_strip.jpg!)
    age_total = t - t_start
    if age_total <= 0.38:
        w_p = cubic_bezier_cool(age_total / 0.38)
        env = math.sin(math.pi * w_p)
        # Diagonal coordinate u = (xx * 0.65 + yy * 0.76)
        diag_d = (xx * 0.65 + (yy - (760.0 + w_p * 520.0)) * 0.76)
        blue_band = np.exp(-((diag_d / 145.0) ** 2)) * env
        red_edge = np.exp(-(((diag_d - 140.0) / 55.0) ** 2)) * env
        r_ch += blue_band * 55.0 + red_edge * 245.0
        g_ch += blue_band * 165.0 + red_edge * 48.0
        b_ch += blue_band * 255.0 + red_edge * 95.0

    arr = np.stack([np.clip(r_ch, 0, 255), np.clip(g_ch, 0, 255), np.clip(b_ch, 0, 255)], axis=-1).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGBA")
    d = ImageDraw.Draw(img)

    img.alpha_composite(get_hud_overlay("dark"))

    if t < t_mid:
        # ---------------- PHASE A: Live Cursor-Driven Text Selection (`MOTION_ENTER = 480ms`) ----------------
        age = t - t_start
        sel_p = cubic_bezier_cool(age / MOTION_ENTER)

        f_top = get_font(INTER_REG, 68)
        f_bot = get_font(INTER_BOLD, 86)

        bb_top = d.textbbox((0, 0), sel_top_text, font=f_top)
        tw_top, th_top = bb_top[2] - bb_top[0], bb_top[3] - bb_top[1]
        tx_top = (W - tw_top) // 2
        ty_top = 845

        cur_w = int((tw_top + 28) * sel_p)
        bx0 = tx_top - 14
        by0 = ty_top - 4
        bx1 = bx0 + cur_w
        by1 = ty_top + th_top + 18

        # Translucent blue UI selection box + left & right handle pins
        d.rectangle([bx0, by0, bx1, by1], fill=(42, 118, 255, 112))
        d.line([(bx0, by0), (bx0, by1)], fill=(66, 148, 255, 255), width=4)
        d.ellipse([bx0 - 8, by0 - 14, bx0 + 8, by0 + 2], fill=(66, 148, 255, 255))
        d.line([(bx1, by0), (bx1, by1)], fill=(66, 148, 255, 255), width=4)
        d.ellipse([bx1 - 8, by1 - 2, bx1 + 8, by1 + 14], fill=(66, 148, 255, 255))

        # Top text (progressively brightens as the selection sweeps across it, like t=8.20s -> 8.55s)
        d.text((tx_top, ty_top), sel_top_text, font=f_top, fill=(246, 244, 236, 255))

        # Secondary line enters after 80ms stagger via `[data-reveal]` (translateY(28px) -> 0)
        if age >= 0.08:
            bot_a, bot_dy = data_reveal(age - 0.08, duration=MOTION_ENTER, offset_y=28)
            bb_bot = d.textbbox((0, 0), sel_bot_text, font=f_bot)
            tw_bot = bb_bot[2] - bb_bot[0]
            tx_bot = (W - tw_bot) // 2
            d.text((tx_bot, int(930 + bot_dy)), sel_bot_text, font=f_bot, fill=(252, 250, 242, int(bot_a * 255)))

        # Wireframe cursors: lower cursor tracks the selection drag and then settles downward
        if age <= MOTION_ENTER:
            cur_x = int(bx1 + 18)
            cur_y = int(by1 + 68 + age * 180)
        else:
            post = cubic_bezier_cool((age - MOTION_ENTER) / 0.65)
            cur_x = int((bx1 + 18) * (1.0 - post) + 410 * post)
            cur_y = int((by1 + 155) * (1.0 - post) + 1435 * post)
        draw_wireframe_cursor(img, cur_x, cur_y, angle_deg=-24, scale=1.05)
        draw_wireframe_cursor(
            img,
            int(895 - cubic_bezier_cool(age / 0.9) * 35),
            int(420 + cubic_bezier_cool(age / 0.9) * 45),
            angle_deg=155,
            scale=0.95,
        )
    else:
        # ---------------- PHASE B: Wireframe Card + Progressive SVG Contour + Two-State Reveal ----------------
        # (Matches t=9.60s -> 10.20s `are sending` -> 10.85s `the same MESSAGE` in ref9_motion_strip.jpg!)
        age = t - t_mid

        ochre_pts = [(690, 0), (540, 140), (200, 340), (195, 580), (490, 620), (750, 560)]
        draw_progressive_polyline(d, ochre_pts, age / 0.62, fill=(185, 138, 68, 180), width=6)

        red_pts = [
            (840, 490),
            (895, 535),
            (865, 860),
            (880, 1080),
            (710, 1480),
            (485, 1610),
            (180, 1690),
            (0, 1720),
        ]
        draw_progressive_polyline(d, red_pts, age / 0.68, fill=(192, 56, 40, 230), width=22)

        # Technical wireframe grid box around center lockup
        card_a, card_dy = data_reveal(age, duration=MOTION_STATE, offset_y=20)
        gx0, gy0, gx1, gy1 = 220, int(680 + card_dy), 790, int(1290 + card_dy)
        grid_alpha = int(card_a * 140)
        for xx_l in (gx0, gx0 + 95, gx1 - 95, gx1):
            d.line([(xx_l, gy0 - 40), (xx_l, gy1 + 40)], fill=(58, 76, 104, grid_alpha), width=2)
        for yy_l in (gy0, gy0 + 110, gy1 - 110, gy1):
            d.line([(gx0 - 40, yy_l), (gx1 + 40, yy_l)], fill=(58, 76, 104, grid_alpha), width=2)
        d.rectangle([gx0, gy0, gx1, gy1], outline=(82, 108, 148, int(card_a * 185)), width=2)
        d.rectangle([gx0 + 12, gy0 + 12, gx0 + 34, gy0 + 34], outline=(160, 180, 210, int(card_a * 185)), width=2)

        # Aceternity UI / Magic UI Border Beam traveling along the card perimeter
        beam_p = cubic_bezier_cool((age % 1.15) / 1.15)
        bx_beam = int(gx0 + (gx1 - gx0) * beam_p)
        d.line([(bx_beam, gy0), (min(gx1, bx_beam + 90), gy0)], fill=(88, 168, 255, 235), width=4)

        # State 1 (0.00 .. 0.42s): Preliminary dim phrase (like `are / sending` at t=10.20s)
        if age < 0.42:
            s1_a, s1_dy = data_reveal(age, duration=0.26, offset_y=22)
            f_s1 = get_font(INTER_REG, 56)
            bb1 = d.textbbox((0, 0), state1_top, font=f_s1)
            d.text((385, int(815 + s1_dy)), state1_top, font=f_s1, fill=(220, 226, 235, int(s1_a * 230)))
            f_s2 = get_font(INTER_MED, 62)
            d.text((385, int(880 + s1_dy)), state1_bot, font=f_s2, fill=(120, 134, 156, int(s1_a * 185)))
        else:
            # State 2 (0.42s .. end): Smooth state transition (`MOTION_STATE = 300ms`) into
            # `stamp_top_text` + bold italic electric-blue `stamp_blue_word` (`PROCESS` / `CREATIVE`)
            s2_age = age - 0.42
            top_a, top_dy = data_reveal(s2_age, duration=MOTION_STATE, offset_y=22)
            f_top = get_font(INTER_REG, 58)
            bb_t = d.textbbox((0, 0), stamp_top_text, font=f_top)
            tw_t = bb_t[2] - bb_t[0]
            d.text(((W - tw_t) // 2, int(790 + top_dy)), stamp_top_text, font=f_top, fill=(246, 244, 236, int(top_a * 255)))

            # 60ms stagger on the primary electric-blue keyword (`MOTION_STAGGER = 60ms`)
            blue_age = max(0.0, s2_age - MOTION_STAGGER)
            blue_a, blue_dy = data_reveal(blue_age, duration=MOTION_ENTER, offset_y=28)
            f_blue = get_font(MONTSERRAT_BLACK_IT, 94)
            bb_b = d.textbbox((0, 0), stamp_blue_word, font=f_blue)
            tw_b = bb_b[2] - bb_b[0]
            bx = (W - tw_b) // 2
            by = int(865 + blue_dy)

            glow_l = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_l)
            gd.text((bx, 40), stamp_blue_word, font=f_blue, fill=(42, 124, 255, int(blue_a * 135)))
            glow_l = glow_l.filter(ImageFilter.GaussianBlur(radius=12))
            img.alpha_composite(glow_l, (0, by - 40))

            d.text((bx, by), stamp_blue_word, font=f_blue, fill=(58, 142, 255, int(blue_a * 255)))

    return img


# ---------------------------------------------------------------------------
# Beat 5B (26.85s - 30.35s): Cream Drafting-Paper #2 + Progressive Gold/Red SVG
# Contours + Staggered Directional Reveal + Diagonal Golden-Red Light Beam Transition
# (Exact replica of t=16.95s -> 17.25s -> 17.55s -> 17.85s in ref9_motion_strip.jpg!)
# ---------------------------------------------------------------------------
def render_cream_architect_stamp(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, 390, 68], fill=(10, 10, 12, 255))

    age = t - 26.85

    # 1. Golden-ochre contour draws in first (0.00s .. 0.55s, matching t=16.95s)
    gold_pts = [
        (360, 68),
        (590, 440),
        (780, 520),
        (960, 640),
        (930, 880),
        (780, 1040),
        (510, 1110),
        (110, 1090),
        (0, 1075),
    ]
    draw_progressive_polyline(d, gold_pts, age / 0.55, fill=(216, 162, 62, 235), width=5)

    # 2. Terracotta-red bottom contour draws in starting at age=0.28s (matching t=17.25s)
    red_pts = [
        (240, 1920),
        (295, 1620),
        (485, 1460),
        (635, 1340),
        (735, 1210),
        (920, 1360),
        (1080, 1465),
    ]
    draw_progressive_polyline(d, red_pts, (age - 0.25) / 0.60, fill=(212, 64, 44, 255), width=28)

    # 3. Dark charcoal 3D silhouettes enter smoothly from corners starting at age=0.32s
    if age >= 0.30:
        sil_p = cubic_bezier_cool((age - 0.30) / MOTION_SEQUENCE)
        sil_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sil_layer)
        # Upper-left silhouette polygon
        ul_x = int(-180 * (1.0 - sil_p))
        sd.polygon(
            [(0, 68), (245 + ul_x, 68), (155 + ul_x, 340), (0, 490)],
            fill=(32, 38, 36, int(235 * sil_p)),
        )
        # Right-middle silhouette polygon
        rm_x = int(160 * (1.0 - sil_p))
        sd.polygon(
            [(1080, 660), (875 + rm_x, 830), (955 + rm_x, 1070), (1080, 1130)],
            fill=(32, 38, 36, int(230 * sil_p)),
        )
        # Lower-left silhouette polygon
        ll_y = int(220 * (1.0 - sil_p))
        sd.polygon(
            [(0, 1310 + ll_y), (225, 1450 + ll_y), (295, 1680 + ll_y), (145, 1920), (0, 1920)],
            fill=(32, 38, 36, int(235 * sil_p)),
        )
        sil_layer = sil_layer.filter(ImageFilter.GaussianBlur(radius=4))
        img.alpha_composite(sil_layer)

    img.alpha_composite(get_hud_overlay("light"))

    # 4. Center Typography Lockup with `[data-reveal]` + 2-part staggered word reveal
    #    (matching `you're just` at t=16.95s -> `ONE` at t=17.25s -> `ONE MORE` at t=17.55s!)
    if t < 28.70:
        top_a, top_dy = data_reveal(age, duration=MOTION_STATE, offset_y=24)
        f_top = get_font(INTER_REG, 56)
        txt_top = "the term"
        bb_t = d.textbbox((0, 0), txt_top, font=f_top)
        d.text(
            ((W - (bb_t[2] - bb_t[0])) // 2 + 18, int(918 + top_dy)),
            txt_top,
            font=f_top,
            fill=(28, 30, 34, int(top_a * 255)),
        )

        if age >= 0.26:
            f_blue = get_font(MONTSERRAT_BLACK_IT, 92)
            full_word = "ARCHITECT"
            bb_full = d.textbbox((0, 0), full_word, font=f_blue)
            full_w = bb_full[2] - bb_full[0]
            start_x = (W - full_w) // 2

            # Part 1 ("ARCHI") reveals at age=0.26s; Part 2 ("TECT") reveals with 80ms stagger
            p1_a, p1_dy = data_reveal(age - 0.26, duration=MOTION_STATE, offset_y=26)
            d.text((start_x, int(985 + p1_dy)), "ARCHI", font=f_blue, fill=(58, 142, 255, int(p1_a * 255)))

            if age >= 0.34:
                bb_p1 = d.textbbox((0, 0), "ARCHI", font=f_blue)
                w_p1 = bb_p1[2] - bb_p1[0]
                p2_a, p2_dy = data_reveal(age - 0.34, duration=MOTION_STATE, offset_y=26)
                d.text(
                    (start_x + w_p1 - 4, int(985 + p2_dy)),
                    "TECT",
                    font=f_blue,
                    fill=(58, 142, 255, int(p2_a * 255)),
                )
    else:
        s2_age = t - 28.70
        top_a, top_dy = data_reveal(s2_age, duration=MOTION_STATE, offset_y=24)
        f_top = get_font(INTER_REG, 54)
        txt_top = "without knowing"
        bb_t = d.textbbox((0, 0), txt_top, font=f_top)
        d.text(
            ((W - (bb_t[2] - bb_t[0])) // 2, int(915 + top_dy)),
            txt_top,
            font=f_top,
            fill=(28, 30, 34, int(top_a * 255)),
        )

        blue_a, blue_dy = data_reveal(max(0.0, s2_age - MOTION_STAGGER), duration=MOTION_ENTER, offset_y=28)
        f_blue = get_font(MONTSERRAT_BLACK_IT, 86)
        word = "WHAT IT MEANT"
        bb_b = d.textbbox((0, 0), word, font=f_blue)
        d.text(
            ((W - (bb_b[2] - bb_b[0])) // 2, int(985 + blue_dy)),
            word,
            font=f_blue,
            fill=(58, 142, 255, int(blue_a * 255)),
        )

    # 5. Blazing Diagonal Golden-White/Crimson Light-Beam Transition at 30.05s - 30.35s
    #    (Exact replica of t=17.85s in ref9_motion_strip.jpg!)
    if t >= 30.05:
        bp = cubic_bezier_cool((t - 30.05) / 0.30)
        beam_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam_layer)
        bx_top = int(220 + bp * 260)
        bx_bot = int(-60 + bp * 260)
        # Outer warm crimson-orange glow
        bd.line([(bx_top, -40), (bx_bot, H + 40)], fill=(235, 78, 32, 225), width=140)
        # Inner bright golden-white core
        bd.line([(bx_top, -40), (bx_bot, H + 40)], fill=(255, 248, 220, 255), width=58)
        beam_layer = beam_layer.filter(ImageFilter.GaussianBlur(radius=14))
        img.alpha_composite(beam_layer)

    return img


# ---------------------------------------------------------------------------
# Talking-Head Lower-Case Minimalist Tight-Tracked Chest Subtitles
# with `[data-reveal]` block entrance & progressive word opacity
# ---------------------------------------------------------------------------
TALKING_SUBTITLES = [
    # Beat 2 (5.65 - 8.30s)
    (5.70, 6.95, [[("so", 5.70), ("i'd", 5.82), ("always", 5.95), ("been", 6.20), ("aware", 6.40)]]),
    (6.95, 8.30, [[("of", 6.98), ("the", 7.12), ("construction", 7.30)], [("sector.", 7.75)]]),
    # Beat 3B (14.10 - 17.30s)
    (14.12, 15.35, [[("he", 14.15), ("used", 14.28), ("to", 14.42), ("take", 14.55), ("me", 14.70)], [("onto", 14.85), ("sites", 15.02)]]),
    (15.35, 17.28, [[("and", 15.40), ("i", 15.55), ("used", 15.70), ("to", 15.88), ("be", 16.02)], [("like", 16.22), ("a", 16.42), ("helper.", 16.58)]]),
    # Beat 5A (20.55 - 26.85s)
    (20.58, 22.15, [[("i", 20.60), ("was", 20.75), ("quite", 20.92), ("artistic", 21.10)], [("at", 21.42), ("school,", 21.58)]]),
    (22.15, 23.95, [[("and", 22.18), ("i", 22.32), ("obviously", 22.48)], [("wanted", 22.85), ("to", 23.18), ("try", 23.40)]]),
    (23.95, 25.65, [[("and", 24.00), ("use", 24.30), ("those", 24.65)], [("skills.", 24.95)]]),
    (25.65, 26.85, [[("happened", 25.72), ("upon", 26.15)]]),
    # Beat 6A (30.35 - 35.30s)
    (30.38, 32.05, [[("and", 30.40), ("the", 30.55), ("more", 30.72), ("i", 30.92)], [("investigated", 31.25)]]),
    (32.05, 33.30, [[("and", 32.08), ("looked", 32.22), ("into", 32.48), ("it,", 32.72)]]),
    (33.30, 35.28, [[("it", 33.32), ("became", 33.52), ("very", 33.85)], [("appealing", 34.18), ("to", 34.62), ("me.", 34.80)]]),
    # Beat 6C (38.45 - 43.40s)
    (38.48, 40.35, [[("and", 38.55), ("having", 39.10), ("a", 39.65)]]),
    (40.35, 42.15, [[("management", 40.45), ("role", 41.15)], [("as", 41.55), ("well,", 41.75)]]),
    (42.15, 43.38, [[("and", 42.18), ("driving", 42.38)], [("the", 42.75), ("process", 42.95)]]),
    # Beat 7A (43.40 - 48.95s)
    (43.42, 45.45, [[("really", 43.65), ("appealed", 44.25)], [("to", 44.85), ("me", 45.10)]]),
    (45.45, 47.08, [[("from", 45.50), ("a", 45.80), ("very", 46.00)], [("early", 46.35), ("age.", 46.65)]]),
    (47.08, 48.92, [[("so", 47.12), ("i", 47.35), ("think", 47.52)], [("i", 47.78), ("even", 47.95), ("said", 48.20)]]),
]


def render_talking_subtitle(canvas: Image.Image, t: float):
    for t0, t1, lines in TALKING_SUBTITLES:
        if t0 <= t < t1:
            fnt = get_font(INTER_MED, 62)
            line_h = 68
            block_y = 1095 if len(lines) == 1 else 1065

            # Subtle `[data-reveal]` block entrance (220ms cubic-bezier)
            blk_a, blk_dy = data_reveal(t - t0, duration=0.22, offset_y=14)

            line_widths = []
            d = ImageDraw.Draw(canvas)
            for line in lines:
                full_str = " ".join(w for w, _ in line)
                bb = d.textbbox((0, 0), full_str, font=fnt)
                line_widths.append(bb[2] - bb[0])
            max_w = max(line_widths)
            start_x = (W - max_w) // 2

            for l_idx, line in enumerate(lines):
                cur_x = start_x if len(lines) > 1 else (W - line_widths[l_idx]) // 2
                cur_y = int(block_y + l_idx * line_h + blk_dy)
                for w_str, t_act in line:
                    active_p = cubic_bezier_cool((t - t_act) / MOTION_FAST)
                    alpha = int((72 + 183 * active_p) * blk_a)
                    d.text((cur_x + 2, cur_y + 3), w_str, font=fnt, fill=(0, 0, 0, int(alpha * 0.72)))
                    d.text((cur_x, cur_y), w_str, font=fnt, fill=(250, 248, 242, alpha))
                    bb_w = d.textbbox((0, 0), w_str + " ", font=fnt)
                    cur_x += (bb_w[2] - bb_w[0]) - 3
            break


# ---------------------------------------------------------------------------
# Beat 7B (48.95s - 51.80s): Pull-Back Window-in-Black Frame + Giant Metallic
# Ice-Blue Chrome Lockup (Follows MOTION-DESIGN.md: smooth 580ms cubic-bezier
# scale-down + `[data-reveal]` translateY(28px) -> 0 on the metallic headline)
# ---------------------------------------------------------------------------
def render_metallic_chrome_text(text: str, font_size: int = 225, alpha_scale: float = 1.0) -> Image.Image:
    fnt = get_font(BEBAS_REG, font_size)
    tmp = Image.new("RGBA", (W, 340), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bb = td.textbbox((0, 0), text, font=fnt)
    tw = bb[2] - bb[0]
    tx = (W - tw) // 2
    ty = 40 - bb[1]

    mask = Image.new("L", (W, 340), 0)
    md = ImageDraw.Draw(mask)
    md.text((tx, ty), text, font=fnt, fill=int(255 * clamp(alpha_scale)))

    yy = np.linspace(0.0, 1.0, 340, dtype=np.float32)[:, None]
    r = np.where(yy < 0.48, 128 + (255 - 128) * (yy / 0.48), 255 - (255 - 98) * ((yy - 0.48) / 0.52))
    g = np.where(yy < 0.48, 178 + (255 - 178) * (yy / 0.48), 255 - (255 - 152) * ((yy - 0.48) / 0.52))
    b = np.where(yy < 0.48, 238 + (255 - 238) * (yy / 0.48), 255 - (255 - 218) * ((yy - 0.48) / 0.52))

    grad = np.zeros((340, W, 4), dtype=np.uint8)
    grad[:, :, 0] = np.clip(r, 0, 255).astype(np.uint8)
    grad[:, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
    grad[:, :, 2] = np.clip(b, 0, 255).astype(np.uint8)
    grad[:, :, 3] = np.array(mask)

    chrome_img = Image.fromarray(grad, mode="RGBA")
    glow = chrome_img.filter(ImageFilter.GaussianBlur(radius=10))
    out = Image.new("RGBA", (W, 340), (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(chrome_img)
    return out


def render_pullback_window_finale(raw_rgb: np.ndarray, t: float) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    # Smooth 580ms section entrance (`cubic_bezier_cool`, zero bounce)
    p_zoom = cubic_bezier_cool((t - 48.95) / 0.58)
    scale = 1.0 - 0.44 * p_zoom  # 1.00 -> 0.56

    nw, nh = int(W * scale), int(H * scale)
    graded = grade_talking_head(raw_rgb, t)
    sub_im = Image.fromarray(graded).resize((nw, nh), Image.BILINEAR).convert("RGBA")

    vx = (W - nw) // 2
    vy = int((H - nh) * 0.44)
    canvas.alpha_composite(sub_im, (vx, vy))

    d = ImageDraw.Draw(canvas)

    if t < 50.52:
        lbl = "when i was about"
        chrome_word = '"AGE 14"'
        lbl_a, lbl_dy = data_reveal(t - 49.05, duration=MOTION_STATE, offset_y=20)
        ch_a, ch_dy = data_reveal(t - 49.15, duration=MOTION_ENTER, offset_y=28)
        f_sz = 235
    else:
        lbl = "i wanted to be an"
        chrome_word = '"ARCHITECT"'
        lbl_a, lbl_dy = data_reveal(t - 50.52, duration=MOTION_STATE, offset_y=20)
        ch_a, ch_dy = data_reveal(t - 50.58, duration=MOTION_ENTER, offset_y=28)
        f_sz = 195

    if lbl_a > 0.02:
        f_lbl = get_font(INTER_MED, 50)
        bb_l = d.textbbox((0, 0), lbl, font=f_lbl)
        lw = bb_l[2] - bb_l[0]
        ly = int(1045 + lbl_dy)
        d.text(((W - lw) // 2 + 2, ly + 2), lbl, font=f_lbl, fill=(0, 0, 0, int(lbl_a * 200)))
        d.text(((W - lw) // 2, ly), lbl, font=f_lbl, fill=(250, 248, 242, int(lbl_a * 255)))

    if ch_a > 0.02:
        chrome_layer = render_metallic_chrome_text(chrome_word, font_size=f_sz, alpha_scale=ch_a)
        canvas.alpha_composite(chrome_layer, (0, int(1085 + ch_dy)))

    return canvas


# ---------------------------------------------------------------------------
# Master Frame Compositor
# ---------------------------------------------------------------------------
def render_frame(raw_rgb: np.ndarray, t: float) -> np.ndarray:
    if t < 5.65:
        out = render_zspace_opening(t)
        return np.array(out.convert("RGB"))

    if 8.30 <= t < 10.75:
        out = render_dark_spotlight_hud(t)
        return np.array(out.convert("RGB"))

    if 10.75 <= t < 14.10:
        out = render_cream_portal_pills(t)
        return np.array(out.convert("RGB"))

    if 17.30 <= t < 20.55:
        out = render_dark_selection_and_stamp(
            t,
            t_start=17.30,
            t_mid=18.85,
            t_end=20.55,
            sel_top_text="early awareness",
            sel_bot_text="of building",
            state1_top="what the",
            state1_bot="building",
            stamp_top_text="the construction",
            stamp_blue_word="PROCESS",
        )
        return np.array(out.convert("RGB"))

    if 26.85 <= t < 30.35:
        out = render_cream_architect_stamp(t)
        return np.array(out.convert("RGB"))

    if 35.30 <= t < 38.45:
        out = render_dark_selection_and_stamp(
            t,
            t_start=35.30,
            t_mid=36.85,
            t_end=38.45,
            sel_top_text="technical skills",
            sel_bot_text="in design",
            state1_top="having both",
            state1_bot="sides",
            stamp_top_text="plus the",
            stamp_blue_word="CREATIVE",
        )
        return np.array(out.convert("RGB"))

    if 48.95 <= t < 51.80:
        out = render_pullback_window_finale(raw_rgb, t)
        return np.array(out.convert("RGB"))

    if t >= 51.80:
        graded = grade_talking_head(raw_rgb, t)
        canvas = Image.fromarray(graded).convert("RGBA")
        canvas.alpha_composite(get_hud_overlay("dark"))
        return np.array(canvas.convert("RGB"))

    graded = grade_talking_head(raw_rgb, t)
    leaked = apply_light_leak(graded, t)
    canvas = Image.fromarray(leaked).convert("RGBA")
    render_talking_subtitle(canvas, t)
    return np.array(canvas.convert("RGB"))


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def build_preview_grid(raw_video_path: str, out_jpg_path: str):
    preview_times = [
        0.35, 1.85, 2.55, 4.45,
        8.60, 9.85,
        11.20, 12.40, 13.45,
        17.48, 18.15, 19.05, 19.85,
        27.00, 27.30, 27.85, 29.35, 30.20,
        35.48, 36.15, 37.75,
        49.80, 51.15, 53.20,
    ]
    thumbs = []
    for t in preview_times:
        raw_cmd = [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{t:.3f}",
            "-i",
            raw_video_path,
            "-frames:v",
            "1",
            "-vf",
            f"scale={W}:{H}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ]
        raw_bytes = subprocess.check_output(raw_cmd)
        raw_rgb = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((H, W, 3))
        comp_rgb = render_frame(raw_rgb, t)
        im = Image.fromarray(comp_rgb).resize((270, 480), Image.BILINEAR)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 115, 30], fill=(0, 0, 0))
        d.text((8, 7), f"t={t:.2f}s", fill=(0, 255, 200))
        thumbs.append(im)

    cols = 6
    rows = int(math.ceil(len(thumbs) / cols))
    grid = Image.new("RGB", (cols * 270, rows * 480), (12, 12, 12))
    for i, im in enumerate(thumbs):
        r, c = divmod(i, cols)
        grid.paste(im, (c * 270, r * 480))
    os.makedirs(os.path.dirname(out_jpg_path), exist_ok=True)
    grid.save(out_jpg_path, quality=92)
    print(f"Saved preview contact sheet to {out_jpg_path}")


def render_full_video(raw_video_path: str, audio_wav_path: str, out_mp4_path: str):
    os.makedirs(os.path.dirname(out_mp4_path), exist_ok=True)
    dec_cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        raw_video_path,
        "-vf",
        f"scale={W}:{H}",
        "-r",
        str(FPS),
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    enc_cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-i",
        audio_wav_path,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
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
        out_mp4_path,
    ]
    dec_proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE)
    enc_proc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)

    frame_bytes = W * H * 3
    last_rgb = np.zeros((H, W, 3), dtype=np.uint8)
    for f_idx in range(TOTAL_FRAMES):
        buf = dec_proc.stdout.read(frame_bytes)
        if len(buf) == frame_bytes:
            last_rgb = np.frombuffer(buf, dtype=np.uint8).reshape((H, W, 3))
        t = f_idx / FPS
        out_rgb = render_frame(last_rgb, t)
        enc_proc.stdin.write(out_rgb.tobytes())
        if f_idx % 240 == 0 or f_idx == TOTAL_FRAMES - 1:
            print(f"Rendered frame {f_idx + 1}/{TOTAL_FRAMES} ({t:.2f}s / {DURATION:.2f}s)")
            sys.stdout.flush()

    dec_proc.stdout.close()
    enc_proc.stdin.close()
    dec_proc.wait()
    enc_proc.wait()
    if enc_proc.returncode != 0:
        raise RuntimeError(f"FFmpeg encode failed with code {enc_proc.returncode}")
    print(f"Successfully rendered {out_mp4_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="/home/user/COOL-backup/video brut 9.mp4")
    parser.add_argument("--audio", default="/tmp/work_cache/felix_ref9_audio.wav")
    parser.add_argument(
        "--out",
        default="/home/user/COOL-backup/felix-gray-reference9/film/felix-gray-reference9-9x16.mp4",
    )
    parser.add_argument("--preview", default="")
    args = parser.parse_args()

    if args.preview:
        build_preview_grid(args.raw, args.preview)
    else:
        render_full_video(args.raw, args.audio, args.out)
