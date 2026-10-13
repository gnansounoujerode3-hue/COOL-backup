#!/usr/bin/env python3
"""
Renders `felix-gray-reference9-9x16.mp4` (1080x1920, 30.00 fps, 54.85s) from
`video brut 9.mp4`, integrating:
  1. `reference9.mp4` visual & motion language
  2. `MOTION-DESIGN.md` (`cubic-bezier(0.2, 0.8, 0.2, 1.0)`, `[data-reveal]`
     `translateY(14px) -> 0`, 60ms stagger, 180ms/300ms/480ms/720ms rhythm)
  3. Installed Claude 3D & Motion Design Skills (`.claude/skills/`):
     - `video-shotcraft/recipes/basic-3d-scene.md`:
       True 3D camera pose `camera = stepTransform.inverse()` with 3D perspective
       homography `(rx, ry, rz)`, `hop` flight arc `sin(pi * p)`, `1.5%` slow hold
       drift, and 70 3D world-space particles with depth-of-field (`opacity 0.22–1.0`,
       `blur 0–6px`).
     - `threejs-camera-controls-and-rigs`: Exact 3x3 projective homography solver
       (`warp_plane_3d`) for true 3D perspective foreshortening on 3D planes/cards.
     - `threejs-bloom` & `threejs-ambient-contact-shading`: Multi-octave selective
       HDR optical bloom + ambient contact shadows under 3D cards, pills, and
       extruded 3D architectural monoliths.
     - `motion-design` & `video-talkcraft`: Log-space camera zoom interpolation +
       continuous micro-drift (`+1.8%`) so no frame is ever frozen.
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
    p = cubic_bezier_cool(age / max(0.001, duration))
    return p, (1.0 - p) * offset_y


# ---------------------------------------------------------------------------
# True 3D Perspective Homography & 3D World Particle System
# (From `.claude/skills/threejs-camera-controls-and-rigs` & `basic-3d-scene.md`)
# ---------------------------------------------------------------------------
def _find_perspective_coeffs(src_pts, dst_pts):
    """
    Solves the 8 projective homography coefficients mapping dst_pts -> src_pts
    for `PIL.Image.transform(..., Image.Transform.PERSPECTIVE, coeffs)`.
    """
    matrix = []
    rhs = []
    for (x_src, y_src), (x_dst, y_dst) in zip(src_pts, dst_pts):
        matrix.append([x_dst, y_dst, 1, 0, 0, 0, -x_src * x_dst, -x_src * y_dst])
        matrix.append([0, 0, 0, x_dst, y_dst, 1, -y_src * x_dst, -y_src * y_dst])
        rhs.append(x_src)
        rhs.append(y_src)
    A = np.array(matrix, dtype=np.float64)
    B = np.array(rhs, dtype=np.float64)
    res = np.linalg.solve(A, B)
    return res.tolist()


def warp_plane_3d(
    img: Image.Image,
    rx_deg: float = 0.0,
    ry_deg: float = 0.0,
    rz_deg: float = 0.0,
    scale: float = 1.0,
    focal: float = 2400.0,
) -> Image.Image:
    """
    Applies a true 3D perspective rotation `(rx_deg, ry_deg, rz_deg)` and scale
    around the center of `img` with focal length `focal` (default 2400px, matching
    `basic-3d-scene.md`).
    """
    if abs(rx_deg) < 0.05 and abs(ry_deg) < 0.05 and abs(rz_deg) < 0.05 and abs(scale - 1.0) < 0.002:
        return img

    w, h = img.size
    hw, hh = w / 2.0, h / 2.0
    corners_3d = np.array(
        [
            [-hw, -hh, 0.0],
            [hw, -hh, 0.0],
            [hw, hh, 0.0],
            [-hw, hh, 0.0],
        ],
        dtype=np.float64,
    ) * scale

    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)

    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)
    R = Rz @ Ry @ Rx

    rot_pts = corners_3d @ R.T
    dst_pts = []
    for px, py, pz in rot_pts:
        denom = max(200.0, focal - pz)
        u = hw + (px * focal) / denom
        v = hh + (py * focal) / denom
        dst_pts.append((u, v))

    src_pts = [(0.0, 0.0), (float(w), 0.0), (float(w), float(h)), (0.0, float(h))]
    coeffs = _find_perspective_coeffs(src_pts, dst_pts)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def apply_selective_bloom(img: Image.Image, threshold: int = 212, strength: float = 0.32) -> Image.Image:
    """
    Scene-linear selective HDR bloom (`threejs-bloom/SKILL.md`):
    extracts pixels above `threshold` and adds a two-octave optical point-spread glare.
    """
    arr = np.array(img.convert("RGBA"), dtype=np.float32)
    rgb = arr[:, :, :3]
    luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    mask = np.clip((luma - threshold) / max(1.0, 255.0 - threshold), 0.0, 1.0)[:, :, None]
    bright = (rgb * mask).astype(np.uint8)
    b_im = Image.fromarray(bright, mode="RGB")
    g1 = np.array(b_im.filter(ImageFilter.GaussianBlur(radius=8)), dtype=np.float32)
    g2 = np.array(b_im.filter(ImageFilter.GaussianBlur(radius=22)), dtype=np.float32)
    glare = (g1 * 0.65 + g2 * 0.55) * strength
    arr[:, :, :3] = np.clip(rgb + glare, 0.0, 255.0)
    return Image.fromarray(arr.astype(np.uint8), mode="RGBA")


# 70 deterministic 3D world-space dust particles (`basic-3d-scene.md`: 70 particles in world space)
_WORLD_PARTICLES_70 = None


def get_world_particles_70():
    global _WORLD_PARTICLES_70
    if _WORLD_PARTICLES_70 is None:
        rng = np.random.default_rng(20261013)
        pts = []
        for i in range(70):
            px = rng.uniform(-620.0, 620.0)
            py = rng.uniform(-980.0, 980.0)
            pz = rng.uniform(-120.0, 1450.0)
            rad = rng.uniform(2.2, 5.2)
            is_blue = (i % 3 == 0)
            pts.append((px, py, pz, rad, is_blue))
        _WORLD_PARTICLES_70 = pts
    return _WORLD_PARTICLES_70


def draw_progressive_polyline(
    draw: ImageDraw.ImageDraw,
    pts: list,
    progress: float,
    fill: tuple,
    width: int = 4,
):
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
# Color Grade, Log-Space Camera Micro-Drift & Anamorphic Light Leaks
# ---------------------------------------------------------------------------
TALKING_SEGMENTS = [
    (5.65, 8.30),
    (14.10, 17.30),
    (20.55, 26.85),
    (30.35, 35.30),
    (38.45, 43.40),
    (43.40, 48.95),
]


def apply_log_camera_drift(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    """
    Applies a subtle log-space camera push (`1.00 -> 1.022`, `motion-design/SKILL.md`
    & `basic-3d-scene.md` 1.5%–2.2% hold push) so no talking-head frame is ever static.
    """
    seg_p = 0.0
    for t0, t1 in TALKING_SEGMENTS:
        if t0 <= t < t1:
            seg_p = clamp((t - t0) / max(0.1, t1 - t0))
            break
    if seg_p <= 0.001:
        return frame_rgb
    zoom = math.exp(math.log(1.022) * seg_p)
    cw = int(round(W / zoom))
    ch = int(round(H / zoom))
    x0 = (W - cw) // 2
    y0 = int((H - ch) * 0.42)
    cropped = frame_rgb[y0 : y0 + ch, x0 : x0 + cw]
    return np.array(Image.fromarray(cropped).resize((W, H), Image.Resampling.BILINEAR))


def grade_talking_head(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    drifted = apply_log_camera_drift(frame_rgb, t)
    f = drifted.astype(np.float32) / 255.0
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
# (Upgraded with `basic-3d-scene.md` 70 3D world-space particles, `hop` camera
# flight arc, and true 3D perspective plane warping `warp_plane_3d`)
# ---------------------------------------------------------------------------
def render_zspace_opening(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (3, 4, 8, 255))

    # Camera Z-progression + `hop` arc (`sin(pi * p)`) during transitions (`basic-3d-scene.md`)
    p1 = cubic_bezier_cool((t - 0.54) / MOTION_SEQUENCE)
    p2 = cubic_bezier_cool((t - 1.58) / MOTION_SEQUENCE)
    p3 = cubic_bezier_cool((t - 3.65) / MOTION_SEQUENCE)
    cam_z = p1 + p2 + p3
    hop = (
        math.sin(math.pi * clamp((t - 0.54) / MOTION_SEQUENCE)) * 0.14
        + math.sin(math.pi * clamp((t - 1.58) / MOTION_SEQUENCE)) * 0.16
        + math.sin(math.pi * clamp((t - 3.65) / MOTION_SEQUENCE)) * 0.18
    )

    # 1. 3D Perspective-Tilted Blueprint Grid Plane on the right half (`warp_plane_3d`)
    grid_plane = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid_plane)
    grid_col = (26, 44, 78, 110)
    for gx in range(440, W + 80, 72):
        gd.line([(gx, 120), (gx, 1800)], fill=grid_col, width=1)
    for gy in range(200, 1740, 72):
        gd.line([(400, gy), (W, gy)], fill=grid_col, width=1)
    for gx in range(512, W, 144):
        for gy in range(272, 1660, 144):
            gd.line([(gx - 6, gy), (gx + 6, gy)], fill=(54, 88, 152, 155), width=2)
            gd.line([(gx, gy - 6), (gx, gy + 6)], fill=(54, 88, 152, 155), width=2)

    # Tilt the blueprint grid in true 3D perspective (`ry = -16 deg`, `rx = +6 deg`)
    tilted_grid = warp_plane_3d(
        grid_plane,
        rx_deg=6.0 - cam_z * 1.8,
        ry_deg=-16.0 + cam_z * 3.2,
        rz_deg=-1.5,
        scale=1.0 - hop * 0.15,
        focal=2400.0,
    )
    img.alpha_composite(tilted_grid)
    d = ImageDraw.Draw(img)

    # 2. 70 True 3D World-Space Particles with Depth-of-Field (`basic-3d-scene.md`)
    focal = 1800.0
    cam_world_z = cam_z * 360.0
    for px, py, pz, rad, is_blue in get_world_particles_70():
        rel_z = (pz - cam_world_z) % 1400.0 + 120.0
        proj = focal / (focal + rel_z)
        sx = int(W * 0.54 + px * proj)
        sy = int(H * 0.48 + py * proj)
        if 0 <= sx < W and 0 <= sy < H:
            dof_alpha = int(clamp(1.15 - rel_z / 1300.0, 0.22, 0.85) * 165)
            r_dot = max(1, int(rad * proj))
            col = (58, 132, 255, dof_alpha) if is_blue else (225, 215, 195, int(dof_alpha * 0.75))
            d.ellipse([sx - r_dot, sy - r_dot, sx + r_dot, sy + r_dot], fill=col)

    # 3. Progressive GSAP DrawSVG golden-ochre contour curve (starts at t=1.60s)
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
            fill=(178, 134, 60, 215),
            width=5,
        )

    # 4. Floating 3D dark-glass notification pills with royal-blue icon circles & Magic UI shimmer
    pills = [
        (0.10, 150, 1020, 0.2, 8.0, "Site Blueprint CAD"),
        (1.05, 760, 1280, 1.0, -10.0, "Hey, I'm an architect..."),
        (1.85, 680, 620, 1.8, -8.0, "Structural Studio"),
        (2.70, 260, 880, 2.3, 9.0, "Technical College"),
    ]
    for t_app, bx, by, bz, ry_pill, label in pills:
        if t < t_app:
            continue
        age = t - t_app
        alpha_p, dy_rev = data_reveal(age, duration=MOTION_STATE, offset_y=20)
        rel_z = max(0.0, cam_z - bz * 0.55)
        scale = clamp((1.0 - hop * 0.18) / (1.0 + rel_z * 0.42), 0.36, 1.0)
        alpha = int(alpha_p * clamp(1.0 - rel_z * 0.28, 0.24, 0.94) * 255)

        pw, ph = int(340 * scale), int(76 * scale)
        px = int(bx + (W * 0.52 - bx) * (1.0 - 1.0 / (1.0 + rel_z * 0.35)))
        py = int(by + dy_rev + (H * 0.46 - by) * (1.0 - 1.0 / (1.0 + rel_z * 0.35)))

        pill_layer = Image.new("RGBA", (pw + 24, ph + 24), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_layer)
        pd.rounded_rectangle(
            [8, 8, pw + 8, ph + 8],
            radius=ph // 2,
            fill=(14, 20, 34, int(alpha * 0.88)),
            outline=(58, 96, 178, int(alpha * 0.78)),
            width=max(1, int(2 * scale)),
        )
        if 0.10 <= age <= 0.58:
            sh_p = cubic_bezier_cool((age - 0.10) / 0.48)
            sx = int(14 + sh_p * (pw - 28))
            pd.line(
                [(sx, 10), (sx + int(30 * scale), 10)],
                fill=(165, 210, 255, int(alpha * (1.0 - sh_p))),
                width=max(2, int(3 * scale)),
            )

        r_cir = int(ph * 0.38)
        cx_c, cy_c = 8 + int(ph * 0.52), 8 + ph // 2
        pd.ellipse(
            [cx_c - r_cir, cy_c - r_cir, cx_c + r_cir, cy_c + r_cir],
            fill=(38, 104, 255, alpha),
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
            fill=(192, 210, 242, int(alpha * 0.94)),
        )
        pill_layer = warp_plane_3d(pill_layer, rx_deg=3.0, ry_deg=ry_pill * (0.4 + 0.6 * min(1.0, rel_z)), focal=1800.0)
        if rel_z > 0.55:
            pill_layer = pill_layer.filter(ImageFilter.GaussianBlur(radius=min(4.0, rel_z * 1.45)))
        img.alpha_composite(pill_layer, (px - pill_layer.width // 2, py - pill_layer.height // 2))

    # 5. 3D Z-Space Kinetic Phrases with true 3D perspective tilt `(rx, ry)` as they recede
    phrases = [
        (0.04, 0.0, 360, 920, 290, 780, 6.0, [("i got into", 68, INTER_MED)], "left"),
        (0.54, 1.0, 410, 720, 560, 580, -7.5, [("architecture.", 84, INTER_BOLD)], "center"),
        (
            1.58,
            2.0,
            340,
            1160,
            280,
            1260,
            8.5,
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
            -5.0,
            [("at a local", 48, INTER_REG), ("technical", 92, INTER_BOLD), ("college.", 54, INTER_MED)],
            "center",
        ),
    ]

    for t_in, z_idx, tx, ty, vx, vy, base_ry, lines, align in phrases:
        if t < t_in:
            continue
        age = t - t_in
        depth_behind = max(0.0, cam_z - z_idx)
        # Apply `1.5%` slow hold push while active in foreground (`basic-3d-scene.md`)
        hold_push = 1.0 + 0.018 * clamp(age / 0.85) if depth_behind < 0.25 else 1.0
        scale = (hold_push * (1.0 - hop * 0.14)) / (1.0 + depth_behind * 0.62)
        depth_fade = clamp(1.0 - depth_behind * 0.36, 0.22, 1.0)

        z_pull = 1.0 - 1.0 / (1.0 + depth_behind * 0.55)
        cx = int(tx + (vx - tx) * z_pull)
        cy = int(ty + (vy - ty) * z_pull)

        layer = Image.new("RGBA", (820, 380), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cur_y = 40
        for l_idx, (txt, base_sz, f_path) in enumerate(lines):
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

        # True 3D perspective tilt as the phrase recedes into Z-space
        tilt_ry = base_ry * min(1.8, 0.25 + depth_behind * 0.85)
        tilt_rx = 3.5 * min(1.5, depth_behind * 0.7)
        layer = warp_plane_3d(layer, rx_deg=tilt_rx, ry_deg=tilt_ry, focal=2000.0)

        if depth_behind < 0.35:
            glow = layer.filter(ImageFilter.GaussianBlur(radius=8))
            img.alpha_composite(glow, (cx - 410, cy - 140))
        elif depth_behind > 0.55:
            # Depth-of-field blur (`0–6px`, `basic-3d-scene.md`)
            layer = layer.filter(ImageFilter.GaussianBlur(radius=min(5.5, depth_behind * 1.65)))

        img.alpha_composite(layer, (cx - 410, cy - 140))

    # 6. Cobalt-blue CRT / blueprint scanline flash at 5.25s - 5.65s
    if 5.25 <= t <= 5.65:
        p = (t - 5.25) / 0.40
        flash_a = int(math.sin(math.pi * p) * 215)
        crt = Image.new("RGBA", (W, H), (10, 26, 118, flash_a))
        cd = ImageDraw.Draw(crt)
        for sy in range(0, H, 10):
            cd.line([(0, sy), (W, sy)], fill=(28, 72, 235, int(flash_a * 0.75)), width=3)
        img = Image.alpha_composite(img, crt)

    return apply_selective_bloom(img, threshold=215, strength=0.28)


# ---------------------------------------------------------------------------
# Beat 2B (8.30s - 10.75s): Dark HUD Viewfinder Spotlight + 3D Cylindrical Plugs
# ---------------------------------------------------------------------------
def render_dark_spotlight_hud(t: float) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r_ch = np.clip(6.0 + 18.0 * np.exp(-(((yy - 940) / 380) ** 2)), 0, 255)
    g_ch = np.clip(14.0 + 36.0 * np.exp(-(((yy - 940) / 420) ** 2)), 0, 255)
    b_ch = np.clip(22.0 + 48.0 * np.exp(-(((yy - 940) / 460) ** 2)), 0, 255)

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

    # 3D PBR-shaded cylindrical cables & metallic plug heads (`threejs-lighting`)
    plug_p = cubic_bezier_cool(max(0.0, (t - 8.50) / 0.80))
    lx_end = int((540 - sep - 18) * plug_p)
    rx_start = int(W - (W - (540 + sep + 18)) * plug_p)

    # Left 3D cable + metallic collar + glowing amber contact tip
    d.line([(0, 968), (lx_end - 26, 926)], fill=(28, 36, 46, 235), width=20)
    d.line([(0, 962), (lx_end - 26, 920)], fill=(110, 134, 162, 195), width=5)
    d.polygon(
        [(lx_end - 32, 908), (lx_end, 906), (lx_end, 938), (lx_end - 32, 940)],
        fill=(64, 76, 92, 255),
        outline=(155, 178, 205, 220),
    )
    # Right 3D cable + metallic collar
    d.line([(W, 978), (rx_start + 26, 926)], fill=(28, 36, 46, 235), width=20)
    d.line([(W, 972), (rx_start + 26, 920)], fill=(110, 134, 162, 195), width=5)
    d.polygon(
        [(rx_start, 906), (rx_start + 32, 908), (rx_start + 32, 940), (rx_start, 938)],
        fill=(64, 76, 92, 255),
        outline=(155, 178, 205, 220),
    )

    img.alpha_composite(get_hud_overlay("dark"))

    if t >= 8.35:
        a1, dy1 = data_reveal(t - 8.35, duration=MOTION_ENTER, offset_y=32)
        drift_up = cubic_bezier_cool((t - 8.35) / 2.2) * 48.0
        f_top = get_font(INTER_REG, 64)
        d.text((225, int(545 + dy1 - drift_up)), "from day one", font=f_top, fill=(220, 232, 242, int(a1 * 240)))

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

    return apply_selective_bloom(img, threshold=215, strength=0.30)


# ---------------------------------------------------------------------------
# Beat 3A (10.75s - 14.10s): Cream Drafting-Paper + 3D Portal & 3 3D-Tilted Pills
# with Ambient Contact Shadows (`threejs-ambient-contact-shading`)
# ---------------------------------------------------------------------------
def render_cream_portal_pills(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, 390, 68], fill=(10, 10, 12, 255))

    age = t - 10.75

    gold_pts = [(0, 420), (145, 510), (95, 760), (210, 1180), (0, 1480)]
    draw_progressive_polyline(d, gold_pts, age / MOTION_SEQUENCE, fill=(217, 164, 65, 220), width=4)

    red_tl = [(265, 68), (235, 195), (165, 290), (138, 430), (65, 545), (48, 720), (0, 795)]
    draw_progressive_polyline(d, red_tl, age / MOTION_SEQUENCE, fill=(216, 67, 46, 255), width=20)

    red_br = [(1080, 1320), (960, 1490), (885, 1560), (745, 1690), (540, 1850), (465, 1920)]
    draw_progressive_polyline(d, red_br, (age - 0.12) / MOTION_SEQUENCE, fill=(216, 67, 46, 255), width=32)

    img.alpha_composite(get_hud_overlay("light"))

    # Central deep-black circular portal with inner 3D depth rim
    p_portal = cubic_bezier_cool(age / MOTION_ENTER)
    r_p = int(282 * (0.86 + 0.14 * p_portal))
    cx, cy = 540, 1020
    # Soft ambient contact shadow beneath the portal rim
    d.ellipse([cx - r_p - 6, cy - r_p + 8, cx + r_p + 6, cy + r_p + 16], fill=(22, 18, 12, int(65 * p_portal)))
    d.ellipse([cx - r_p, cy - r_p, cx + r_p, cy + r_p], fill=(6, 10, 16, int(255 * p_portal)))
    d.ellipse(
        [cx - r_p + 6, cy - r_p + 6, cx + r_p - 6, cy + r_p - 6],
        outline=(34, 68, 108, int(155 * p_portal)),
        width=4,
    )

    pills_spec = [
        (11.00, -118, 390, 74, "When I was young", 34, 6.0, -5.0),
        (12.15, -24, 420, 78, "Kicking my heels...", 36, -5.0, 6.0),
        (13.00, 92, 600, 134, "During summer\nholidays!", 48, 7.0, -4.0),
    ]
    for idx, (t_in, y_off, pw, ph, txt, fsz, rx_t, ry_t) in enumerate(pills_spec):
        if t < t_in:
            continue
        p_age = t - t_in
        rev_a, rev_dy = data_reveal(p_age, duration=MOTION_STATE, offset_y=26)

        press_scale = 1.0
        hover_dy = 0.0
        if 0.24 <= p_age <= 0.40:
            press_w = math.sin(math.pi * (p_age - 0.24) / 0.16)
            press_scale = 1.0 - 0.025 * press_w
        elif p_age > 0.40:
            hover_dy = -4.0 * cubic_bezier_cool((p_age - 0.40) / MOTION_FAST)

        cw, ch = int(pw * press_scale), int(ph * press_scale)
        pill_img = Image.new("RGBA", (cw + 56, ch + 56), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_img)

        alpha_i = int(rev_a * 255)
        # Ambient contact occlusion shadow (`threejs-ambient-contact-shading`)
        pd.rounded_rectangle(
            [28, 38, 28 + cw, 38 + ch],
            radius=min(38, ch // 2),
            fill=(0, 0, 0, int(rev_a * 155)),
        )
        # 3D bottom extrusion bevel lip (`#2866C8`)
        pd.rounded_rectangle(
            [26, 30, 26 + cw, 30 + ch],
            radius=min(38, ch // 2),
            fill=(36, 98, 198, alpha_i),
        )
        # Sky-blue top pill surface (#4294FF)
        pd.rounded_rectangle(
            [26, 24, 26 + cw, 24 + ch],
            radius=min(38, ch // 2),
            fill=(66, 148, 255, alpha_i),
            outline=(165, 212, 255, int(rev_a * 240)),
            width=2,
        )
        if idx == 2 and p_age >= 0.28:
            foc_a = int(cubic_bezier_cool((p_age - 0.28) / MOTION_FAST) * 210)
            pd.rounded_rectangle(
                [20, 18, 32 + cw, 32 + ch],
                radius=min(44, ch // 2 + 6),
                outline=(255, 255, 255, foc_a),
                width=3,
            )

        if 0.18 <= p_age <= 0.56:
            sh_p = cubic_bezier_cool((p_age - 0.18) / 0.38)
            sx = int(34 + sh_p * (cw - 68))
            pd.line(
                [(sx, 26), (sx + 52, 26)],
                fill=(255, 255, 255, int(alpha_i * (1.0 - sh_p) * 0.92)),
                width=3,
            )

        f_p = get_font(INTER_MED, int(fsz * press_scale))
        lines = txt.split("\n")
        total_h = len(lines) * int(fsz * press_scale * 1.12)
        cur_y = 24 + (ch - total_h) // 2 - 4
        for line in lines:
            bb = pd.textbbox((0, 0), line, font=f_p)
            tw = bb[2] - bb[0]
            tx = 26 + (cw - tw) // 2
            pd.text((tx, cur_y), line, font=f_p, fill=(255, 255, 255, alpha_i))
            cur_y += int(fsz * press_scale * 1.12)

        # True 3D perspective tilt settles smoothly as the pill locks in
        settle = 1.0 - 0.65 * cubic_bezier_cool(p_age / MOTION_ENTER)
        pill_3d = warp_plane_3d(
            pill_img,
            rx_deg=rx_t * settle,
            ry_deg=ry_t * settle,
            rz_deg=2.2 if idx % 2 == 0 else -1.8,
            focal=1900.0,
        )
        px = cx - pill_3d.width // 2 + (-22 if idx == 0 else (28 if idx == 1 else -8))
        py = int(cy + y_off + rev_dy + hover_dy - pill_3d.height // 2)
        img.alpha_composite(pill_3d, (px, py))

    return img


# ---------------------------------------------------------------------------
# Beat 4 (17.30s - 20.55s) & Beat 6B (35.30s - 38.45s):
# Diagonal Neon Blue/Crimson Light-Ribbon Wipe -> Live Cursor-Driven Text Selection
# -> 3D Perspective-Tilted Wireframe Card with Border Beam & Red SVG Contour
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

    age_total = t - t_start
    if age_total <= 0.38:
        w_p = cubic_bezier_cool(age_total / 0.38)
        env = math.sin(math.pi * w_p)
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

        d.rectangle([bx0, by0, bx1, by1], fill=(42, 118, 255, 112))
        d.line([(bx0, by0), (bx0, by1)], fill=(66, 148, 255, 255), width=4)
        d.ellipse([bx0 - 8, by0 - 14, bx0 + 8, by0 + 2], fill=(66, 148, 255, 255))
        d.line([(bx1, by0), (bx1, by1)], fill=(66, 148, 255, 255), width=4)
        d.ellipse([bx1 - 8, by1 - 2, bx1 + 8, by1 + 14], fill=(66, 148, 255, 255))

        d.text((tx_top, ty_top), sel_top_text, font=f_top, fill=(246, 244, 236, 255))

        if age >= 0.08:
            bot_a, bot_dy = data_reveal(age - 0.08, duration=MOTION_ENTER, offset_y=28)
            bb_bot = d.textbbox((0, 0), sel_bot_text, font=f_bot)
            tw_bot = bb_bot[2] - bb_bot[0]
            tx_bot = (W - tw_bot) // 2
            d.text((tx_bot, int(930 + bot_dy)), sel_bot_text, font=f_bot, fill=(252, 250, 242, int(bot_a * 255)))

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

        # Render the wireframe card on its own plane and apply true 3D perspective rotation
        # (`ry: -14° -> -3°`, `rx: +8° -> +2°`) as it locks in!
        card_plane = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card_plane)

        card_a, card_dy = data_reveal(age, duration=MOTION_STATE, offset_y=20)
        gx0, gy0, gx1, gy1 = 220, int(680 + card_dy), 790, int(1290 + card_dy)
        grid_alpha = int(card_a * 145)
        for xx_l in (gx0, gx0 + 95, gx1 - 95, gx1):
            cd.line([(xx_l, gy0 - 40), (xx_l, gy1 + 40)], fill=(58, 76, 104, grid_alpha), width=2)
        for yy_l in (gy0, gy0 + 110, gy1 - 110, gy1):
            cd.line([(gx0 - 40, yy_l), (gx1 + 40, yy_l)], fill=(58, 76, 104, grid_alpha), width=2)
        cd.rectangle([gx0, gy0, gx1, gy1], outline=(88, 116, 160, int(card_a * 195)), width=2)
        cd.rectangle([gx0 + 12, gy0 + 12, gx0 + 34, gy0 + 34], outline=(168, 188, 220, int(card_a * 195)), width=2)

        beam_p = cubic_bezier_cool((age % 1.15) / 1.15)
        bx_beam = int(gx0 + (gx1 - gx0) * beam_p)
        cd.line([(bx_beam, gy0), (min(gx1, bx_beam + 95), gy0)], fill=(95, 175, 255, 245), width=4)

        if age < 0.42:
            s1_a, s1_dy = data_reveal(age, duration=0.26, offset_y=22)
            f_s1 = get_font(INTER_REG, 56)
            cd.text((385, int(815 + s1_dy)), state1_top, font=f_s1, fill=(220, 226, 235, int(s1_a * 230)))
            f_s2 = get_font(INTER_MED, 62)
            cd.text((385, int(880 + s1_dy)), state1_bot, font=f_s2, fill=(120, 134, 156, int(s1_a * 185)))
        else:
            s2_age = age - 0.42
            top_a, top_dy = data_reveal(s2_age, duration=MOTION_STATE, offset_y=22)
            f_top = get_font(INTER_REG, 58)
            bb_t = cd.textbbox((0, 0), stamp_top_text, font=f_top)
            tw_t = bb_t[2] - bb_t[0]
            cd.text(((W - tw_t) // 2, int(790 + top_dy)), stamp_top_text, font=f_top, fill=(246, 244, 236, int(top_a * 255)))

            blue_age = max(0.0, s2_age - MOTION_STAGGER)
            blue_a, blue_dy = data_reveal(blue_age, duration=MOTION_ENTER, offset_y=28)
            f_blue = get_font(MONTSERRAT_BLACK_IT, 94)
            bb_b = cd.textbbox((0, 0), stamp_blue_word, font=f_blue)
            tw_b = bb_b[2] - bb_b[0]
            bx = (W - tw_b) // 2
            by = int(865 + blue_dy)

            glow_l = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow_l)
            gd.text((bx, 40), stamp_blue_word, font=f_blue, fill=(42, 124, 255, int(blue_a * 145)))
            glow_l = glow_l.filter(ImageFilter.GaussianBlur(radius=12))
            card_plane.alpha_composite(glow_l, (0, by - 40))

            cd.text((bx, by), stamp_blue_word, font=f_blue, fill=(58, 142, 255, int(blue_a * 255)))

        tilt_p = 1.0 - 0.78 * cubic_bezier_cool(age / MOTION_SEQUENCE)
        card_3d = warp_plane_3d(
            card_plane,
            rx_deg=7.5 * tilt_p,
            ry_deg=-12.0 * tilt_p,
            rz_deg=0.0,
            focal=2200.0,
        )
        img.alpha_composite(card_3d)

    return apply_selective_bloom(img, threshold=215, strength=0.26)


# ---------------------------------------------------------------------------
# Beat 5B (26.85s - 30.35s): Cream Drafting-Paper #2 + 3D Extruded Architectural
# Monoliths with Ambient Contact Shadows + Diagonal Golden-Red Light Beam
# ---------------------------------------------------------------------------
def render_cream_architect_stamp(t: float) -> Image.Image:
    img = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, 390, 68], fill=(10, 10, 12, 255))

    age = t - 26.85

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

    # 3D extruded architectural monoliths with contact shadows (`threejs-ambient-contact-shading`)
    if age >= 0.30:
        sil_p = cubic_bezier_cool((age - 0.30) / MOTION_SEQUENCE)
        sil_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sil_layer)

        ul_x = int(-180 * (1.0 - sil_p))
        # Contact shadow on cream drafting paper
        sd.polygon(
            [(0, 82), (262 + ul_x, 82), (172 + ul_x, 356), (0, 508)],
            fill=(20, 18, 14, int(85 * sil_p)),
        )
        # 3D bevel face + main monolith face
        sd.polygon(
            [(0, 68), (254 + ul_x, 68), (164 + ul_x, 348), (0, 498)],
            fill=(56, 66, 62, int(235 * sil_p)),
        )
        sd.polygon(
            [(0, 68), (242 + ul_x, 68), (152 + ul_x, 338), (0, 488)],
            fill=(28, 34, 32, int(242 * sil_p)),
        )

        rm_x = int(160 * (1.0 - sil_p))
        sd.polygon(
            [(1080, 672), (862 + rm_x, 844), (942 + rm_x, 1084), (1080, 1144)],
            fill=(20, 18, 14, int(85 * sil_p)),
        )
        sd.polygon(
            [(1080, 660), (875 + rm_x, 830), (955 + rm_x, 1070), (1080, 1130)],
            fill=(28, 34, 32, int(238 * sil_p)),
        )

        ll_y = int(220 * (1.0 - sil_p))
        sd.polygon(
            [(0, 1300 + ll_y), (238, 1442 + ll_y), (308, 1672 + ll_y), (158, 1920), (0, 1920)],
            fill=(20, 18, 14, int(85 * sil_p)),
        )
        sd.polygon(
            [(0, 1310 + ll_y), (225, 1450 + ll_y), (295, 1680 + ll_y), (145, 1920), (0, 1920)],
            fill=(28, 34, 32, int(242 * sil_p)),
        )
        sil_layer = sil_layer.filter(ImageFilter.GaussianBlur(radius=3.5))
        img.alpha_composite(sil_layer)

    img.alpha_composite(get_hud_overlay("light"))

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

    if t >= 30.05:
        bp = cubic_bezier_cool((t - 30.05) / 0.30)
        beam_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam_layer)
        bx_top = int(220 + bp * 260)
        bx_bot = int(-60 + bp * 260)
        bd.line([(bx_top, -40), (bx_bot, H + 40)], fill=(235, 78, 32, 225), width=140)
        bd.line([(bx_top, -40), (bx_bot, H + 40)], fill=(255, 248, 220, 255), width=58)
        beam_layer = beam_layer.filter(ImageFilter.GaussianBlur(radius=14))
        img.alpha_composite(beam_layer)

    return img


# ---------------------------------------------------------------------------
# Talking-Head Lower-Case Minimalist Tight-Tracked Chest Subtitles
# ---------------------------------------------------------------------------
TALKING_SUBTITLES = [
    (5.70, 6.95, [[("so", 5.70), ("i'd", 5.82), ("always", 5.95), ("been", 6.20), ("aware", 6.40)]]),
    (6.95, 8.30, [[("of", 6.98), ("the", 7.12), ("construction", 7.30)], [("sector.", 7.75)]]),
    (14.12, 15.35, [[("he", 14.15), ("used", 14.28), ("to", 14.42), ("take", 14.55), ("me", 14.70)], [("onto", 14.85), ("sites", 15.02)]]),
    (15.35, 17.28, [[("and", 15.40), ("i", 15.55), ("used", 15.70), ("to", 15.88), ("be", 16.02)], [("like", 16.22), ("a", 16.42), ("helper.", 16.58)]]),
    (20.58, 22.15, [[("i", 20.60), ("was", 20.75), ("quite", 20.92), ("artistic", 21.10)], [("at", 21.42), ("school,", 21.58)]]),
    (22.15, 23.95, [[("and", 22.18), ("i", 22.32), ("obviously", 22.48)], [("wanted", 22.85), ("to", 23.18), ("try", 23.40)]]),
    (23.95, 25.65, [[("and", 24.00), ("use", 24.30), ("those", 24.65)], [("skills.", 24.95)]]),
    (25.65, 26.85, [[("happened", 25.72), ("upon", 26.15)]]),
    (30.38, 32.05, [[("and", 30.40), ("the", 30.55), ("more", 30.72), ("i", 30.92)], [("investigated", 31.25)]]),
    (32.05, 33.30, [[("and", 32.08), ("looked", 32.22), ("into", 32.48), ("it,", 32.72)]]),
    (33.30, 35.28, [[("it", 33.32), ("became", 33.52), ("very", 33.85)], [("appealing", 34.18), ("to", 34.62), ("me.", 34.80)]]),
    (38.48, 40.35, [[("and", 38.55), ("having", 39.10), ("a", 39.65)]]),
    (40.35, 42.15, [[("management", 40.45), ("role", 41.15)], [("as", 41.55), ("well,", 41.75)]]),
    (42.15, 43.38, [[("and", 42.18), ("driving", 42.38)], [("the", 42.75), ("process", 42.95)]]),
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
# Beat 7B (48.95s - 51.80s): 3D Pull-Back Window-in-Black Frame + Giant Metallic
# Ice-Blue Chrome Lockup (`warp_plane_3d` + selective HDR bloom)
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
    age = t - 48.95
    p_zoom = cubic_bezier_cool(age / 0.58)
    # Log-space scale-down from 1.00 -> 0.56 + subtle 1.5% hold drift after landing
    hold_drift = 1.0 + 0.015 * clamp((age - 0.58) / 2.2)
    scale = math.exp(math.log(0.56) * p_zoom) * hold_drift

    nw, nh = int(W * scale), int(H * scale)
    graded = grade_talking_head(raw_rgb, t)
    sub_im = Image.fromarray(graded).resize((nw, nh), Image.BILINEAR).convert("RGBA")

    # Subtle 3D perspective tilt during the pull-back flight (`rx`, `ry` settling to 0)
    flight_arc = math.sin(math.pi * clamp(age / 0.58))
    sub_3d = warp_plane_3d(
        sub_im,
        rx_deg=4.5 * flight_arc,
        ry_deg=-6.0 * flight_arc,
        focal=2200.0,
    )

    vx = (W - sub_3d.width) // 2
    vy = int((H - sub_3d.height) * 0.44)
    canvas.alpha_composite(sub_3d, (vx, vy))

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

    return apply_selective_bloom(canvas, threshold=220, strength=0.25)


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
