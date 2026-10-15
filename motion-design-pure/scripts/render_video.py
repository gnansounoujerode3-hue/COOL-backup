#!/usr/bin/env python3
"""
100% Pure Motion Design Film (`1080x1920`, `30.00 fps`, `36.00s`)
`motion-design-pure/film/motion-design-pure-9x16.mp4`

Zero camera footage, zero static photos — 100% generative 3D/2.5D geometric
motion graphics, procedural 3D polyhedra, kinetic Swiss/Bauhaus typography,
interactive `cubic-bezier(0.2, 0.8, 0.2, 1.0)` physics simulations, 3D winding
architectural staircases, volumetric light cones, and velocity-matched transitions
(`zoom_through_seam`, `inverse_zoom_seam`, `cut_the_curve_seam`, `rack_focus_blur_cut`,
`waterfall_word_state`, `nudge_curve_3phase`, `swipe_clip_reveal`).
"""

import argparse
import math
import os
import subprocess
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
from motion_engine import (
    clamp,
    cubic_bezier,
    expo_in_out,
    expo_out,
    power2_in,
    power2_out,
    power3_in,
    power3_out,
    power4_in,
    power4_out,
    nudge_curve_3phase,
    waterfall_word_state,
    swipe_clip_reveal,
    zoom_through_seam,
    cut_the_curve_seam,
    rack_focus_blur_cut,
)

W, H = 1080, 1920
FPS = 30.0
DURATION = 36.00
TOTAL_FRAMES = int(round(DURATION * FPS))

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
MONTSERRAT_BLACK_IT = f"{FONT_BASE}/montserrat/900Black_Italic/Montserrat_900Black_Italic.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"

_FONT_CACHE = {}


def get_font(path: str, size: int):
    sz = max(12, int(round(size)))
    key = (path, sz)
    if key not in _FONT_CACHE:
        if not os.path.exists(path):
            path = INTER_BOLD
        _FONT_CACHE[key] = ImageFont.truetype(path, sz)
    return _FONT_CACHE[key]


# ---------------------------------------------------------------------------
# True 3D Perspective Homography (`warp_plane_3d`) & 3D Mesh Projection
# ---------------------------------------------------------------------------
def _find_perspective_coeffs(src_pts, dst_pts):
    matrix = []
    rhs = []
    for (x_src, y_src), (x_dst, y_dst) in zip(src_pts, dst_pts):
        matrix.append([x_dst, y_dst, 1, 0, 0, 0, -x_src * x_dst, -x_src * y_dst])
        matrix.append([0, 0, 0, x_dst, y_dst, 1, -y_src * x_dst, -y_src * y_dst])
        rhs.append(x_src)
        rhs.append(y_src)
    A = np.array(matrix, dtype=np.float64)
    B = np.array(rhs, dtype=np.float64)
    return np.linalg.solve(A, B).tolist()


def warp_plane_3d(
    img: Image.Image,
    rx_deg: float = 0.0,
    ry_deg: float = 0.0,
    rz_deg: float = 0.0,
    scale: float = 1.0,
    focal: float = 2200.0,
) -> Image.Image:
    if abs(rx_deg) < 0.05 and abs(ry_deg) < 0.05 and abs(rz_deg) < 0.05 and abs(scale - 1.0) < 0.002:
        return img
    w, h = img.size
    cx, cy = w * 0.5, h * 0.5
    rx, ry, rz = math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)
    cx_r, sx_r = math.cos(rx), math.sin(rx)
    cy_r, sy_r = math.cos(ry), math.sin(ry)
    cz_r, sz_r = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx_r, -sx_r], [0, sx_r, cx_r]])
    Ry = np.array([[cy_r, 0, sy_r], [0, 1, 0], [-sy_r, 0, cy_r]])
    Rz = np.array([[cz_r, -sz_r, 0], [sz_r, cz_r, 0], [0, 0, 1]])
    R = Rz @ Ry @ Rx
    corners = [(-cx, -cy, 0.0), (w - cx, -cy, 0.0), (w - cx, h - cy, 0.0), (-cx, h - cy, 0.0)]
    src_pts = [(0.0, 0.0), (float(w), 0.0), (float(w), float(h)), (0.0, float(h))]
    dst_pts = []
    for x, y, z in corners:
        vec = R @ np.array([x * scale, y * scale, z * scale])
        denom = max(200.0, focal + vec[2])
        px = cx + vec[0] * (focal / denom)
        py = cy + vec[1] * (focal / denom)
        dst_pts.append((float(px), float(py)))
    coeffs = _find_perspective_coeffs(src_pts, dst_pts)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BILINEAR)


def rot3d_matrix(rx_deg: float, ry_deg: float, rz_deg: float) -> np.ndarray:
    rx, ry, rz = math.radians(rx_deg), math.radians(ry_deg), math.radians(rz_deg)
    cx_r, sx_r = math.cos(rx), math.sin(rx)
    cy_r, sy_r = math.cos(ry), math.sin(ry)
    cz_r, sz_r = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx_r, -sx_r], [0, sx_r, cx_r]])
    Ry = np.array([[cy_r, 0, sy_r], [0, 1, 0], [-sy_r, 0, cy_r]])
    Rz = np.array([[cz_r, -sz_r, 0], [sz_r, cz_r, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


# Golden-ratio Icosahedron vertices & edges for 3D procedural crystal rendering
_PHI = (1.0 + math.sqrt(5.0)) / 2.0
_ICO_VERTS = np.array([
    [-1,  _PHI, 0], [ 1,  _PHI, 0], [-1, -_PHI, 0], [ 1, -_PHI, 0],
    [ 0, -1,  _PHI], [ 0,  1,  _PHI], [ 0, -1, -_PHI], [ 0,  1, -_PHI],
    [ _PHI, 0, -1], [ _PHI, 0,  1], [-_PHI, 0, -1], [-_PHI, 0,  1],
], dtype=np.float64)
_ICO_VERTS /= np.linalg.norm(_ICO_VERTS[0])

_ICO_FACES = [
    (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
    (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
    (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
    (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
]

_PARTICLES_90 = None


def get_particles_90():
    global _PARTICLES_90
    if _PARTICLES_90 is None:
        rng = np.random.default_rng(108)
        _PARTICLES_90 = [
            (
                float(rng.uniform(-640, 640)),
                float(rng.uniform(-1020, 1020)),
                float(rng.uniform(80, 1450)),
                int(rng.integers(3, 8)),
                int(rng.integers(0, 3)),
            )
            for _ in range(90)
        ]
    return _PARTICLES_90


def draw_3d_icosahedron(
    canvas: Image.Image,
    cx: int,
    cy: int,
    radius: float,
    rx_deg: float,
    ry_deg: float,
    rz_deg: float,
    focal: float = 1600.0,
    wire_color=(255, 222, 48, 240),
):
    R = rot3d_matrix(rx_deg, ry_deg, rz_deg)
    verts_3d = (_ICO_VERTS * radius) @ R.T
    proj_2d = []
    for vx, vy, vz in verts_3d:
        s = focal / max(200.0, focal + vz)
        proj_2d.append((cx + vx * s, cy + vy * s, vz))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Sort faces back-to-front (Painter's algorithm) with PBR-like directional shading
    light_dir = np.array([0.45, -0.65, -0.60])
    light_dir /= np.linalg.norm(light_dir)

    face_list = []
    for i0, i1, i2 in _ICO_FACES:
        v0, v1, v2 = verts_3d[i0], verts_3d[i1], verts_3d[i2]
        avg_z = (v0[2] + v1[2] + v2[2]) / 3.0
        normal = np.cross(v1 - v0, v2 - v0)
        norm_len = np.linalg.norm(normal)
        if norm_len > 1e-6:
            normal /= norm_len
        ndotl = max(0.0, float(np.dot(normal, light_dir)))
        face_list.append((avg_z, i0, i1, i2, ndotl))

    face_list.sort(key=lambda x: x[0], reverse=True)

    # Glowing inner core
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r_core = int(radius * 0.55)
    gd.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=(58, 148, 255, 130))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=36))
    canvas.alpha_composite(glow)

    for avg_z, i0, i1, i2, ndotl in face_list:
        p0 = (proj_2d[i0][0], proj_2d[i0][1])
        p1 = (proj_2d[i1][0], proj_2d[i1][1])
        p2 = (proj_2d[i2][0], proj_2d[i2][1])
        r_c = int(18 + 85 * ndotl)
        g_c = int(32 + 135 * ndotl)
        b_c = int(68 + 175 * ndotl)
        alpha_f = 135 if avg_z < 0 else 75
        d.polygon([p0, p1, p2], fill=(r_c, g_c, b_c, alpha_f), outline=wire_color, width=3)

    # Vertex nodes
    for px, py, pz in proj_2d:
        r_v = 6 if pz < 0 else 4
        col_v = (255, 255, 255, 255) if pz < 0 else (110, 175, 255, 180)
        d.ellipse([px - r_v, py - r_v, px + r_v, py + r_v], fill=col_v)

    canvas.alpha_composite(layer)


# ---------------------------------------------------------------------------
# Shared Pure Motion Typography & HUD Chrome
# ---------------------------------------------------------------------------
def draw_hud_frame(canvas: Image.Image, act_num: str, act_title: str, t: float, dark: bool = True):
    d = ImageDraw.Draw(canvas)
    col_line = (72, 108, 165, 135) if dark else (38, 36, 32, 135)
    col_txt = (210, 224, 248, 225) if dark else (28, 26, 24, 225)
    accent = (255, 218, 44, 255) if dark else (212, 64, 44, 255)

    # Outer precision registration ticks
    d.rectangle([42, 42, W - 42, H - 42], outline=col_line, width=1)
    for cx, cy in [(42, 42), (W - 42, 42), (42, H - 42), (W - 42, H - 42)]:
        d.line([(cx - 16, cy), (cx + 16, cy)], fill=accent, width=3)
        d.line([(cx, cy - 16), (cx, cy + 16)], fill=accent, width=3)

    f_mono = get_font(MONO_MED, 22)
    f_bold = get_font(JAKARTA_BOLD, 30)
    d.rounded_rectangle([72, 72, 232, 118], radius=22, fill=accent)
    d.text((96, 81), f"ACTE {act_num}", font=f_mono, fill=(12, 14, 18, 255) if dark else (255, 255, 255, 255))
    d.text((254, 77), act_title, font=f_bold, fill=col_txt)

    # Live frame & timecode counter on top-right
    tc_str = f"TC 00:{int(t):02d}:{int((t % 1.0) * 30):02d} // 30FPS"
    bb = d.textbbox((0, 0), tc_str, font=f_mono)
    d.text((W - 72 - (bb[2] - bb[0]), 82), tc_str, font=f_mono, fill=col_txt)


def draw_motion_lockup(
    canvas: Image.Image,
    age: float,
    lead_text: str,
    hero_text: str,
    script_text: str = "",
    cy: int = 1480,
    hero_color=(255, 226, 44),
    dark_bg: bool = True,
):
    a_lead, dy_lead, _ = waterfall_word_state(age, word_index=0, weight="normal")
    a_hero, dy_hero, _ = waterfall_word_state(age, word_index=1, weight="anchor")
    hero_age = max(0.0, age - 0.055)
    nudge_dy = -16.0 * nudge_curve_3phase(max(0.0, hero_age - 0.10) / 0.42) if script_text else 0.0

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    f_lead = get_font(INTER_MED, 48)
    f_hero = get_font(JAKARTA_BOLD, 102)
    f_script = get_font(GREAT_VIBES, 126)

    lead_col = (244, 246, 252) if dark_bg else (22, 24, 30)

    if lead_text and a_lead > 0.02:
        bb_l = od.textbbox((0, 0), lead_text, font=f_lead)
        lw = bb_l[2] - bb_l[0]
        lx, ly = (W - lw) // 2, int(cy - 68 + dy_lead + nudge_dy)
        if dark_bg:
            od.text((lx + 2, ly + 4), lead_text, font=f_lead, fill=(0, 0, 0, int(190 * a_lead)))
        od.text((lx, ly), lead_text, font=f_lead, fill=(lead_col[0], lead_col[1], lead_col[2], int(255 * a_lead)))

    if hero_text and a_hero > 0.02:
        bb_h = od.textbbox((0, 0), hero_text, font=f_hero)
        hw = bb_h[2] - bb_h[0]
        hx, hy = (W - hw) // 2, int(cy - 8 + dy_hero + nudge_dy)

        if 0.01 < hero_age < 0.58:
            ep = 1.0 - power4_out(hero_age / 0.58)
            for mult, asc in [(1, 0.44), (2, 0.24)]:
                off = int(round(mult * 74 * ep))
                ea = int(255 * asc * ep)
                od.text((hx, hy - off), hero_text, font=f_hero, fill=(hero_color[0], hero_color[1], hero_color[2], ea))
                od.text((hx, hy + off), hero_text, font=f_hero, fill=(hero_color[0], hero_color[1], hero_color[2], ea))

        glow = Image.new("RGBA", (W, 250), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.text((hx, 65), hero_text, font=f_hero, fill=(hero_color[0], hero_color[1], hero_color[2], int(175 * a_hero)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=20))
        overlay.alpha_composite(glow, (0, hy - 65))

        od.text((hx + 3, hy + 5), hero_text, font=f_hero, fill=(0, 0, 0, int(195 * a_hero)))
        od.text((hx, hy), hero_text, font=f_hero, fill=(hero_color[0], hero_color[1], hero_color[2], int(255 * a_hero)))

    if script_text:
        sc_age = max(0.0, hero_age - 0.12)
        if sc_age > 0.01:
            sc_layer = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
            scd = ImageDraw.Draw(sc_layer)
            bb_sc = scd.textbbox((0, 0), script_text, font=f_script)
            sc_w = bb_sc[2] - bb_sc[0]
            sc_x = (W - sc_w) // 2 + 12
            sc_col = (255, 255, 255, 255) if dark_bg else (212, 64, 44, 255)
            scd.text((sc_x + 3, 44), script_text, font=f_script, fill=(0, 0, 0, 185))
            scd.text((sc_x, 40), script_text, font=f_script, fill=sc_col)
            sc_wiped = swipe_clip_reveal(sc_layer, sc_age / 0.42, direction="left_to_right")
            overlay.alpha_composite(sc_wiped, (0, int(cy + 62)))

    canvas.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# Act I (0.00s - 6.00s): L'Émergence — 3D Z-Space Icosahedron Crystal & Splines
# ---------------------------------------------------------------------------
def render_act1_emergence(t: float) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (5, 7, 13, 255))

    # 3D perspective coordinate grid
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for gx in range(90, W, 90):
        gd.line([(gx, 0), (gx, H)], fill=(28, 52, 96, 110), width=1)
    for gy in range(90, H, 90):
        gd.line([(0, gy), (W, gy)], fill=(28, 52, 96, 110), width=1)
    tilted_grid = warp_plane_3d(grid, rx_deg=12.0, ry_deg=-16.0 + t * 2.5, rz_deg=-2.0, focal=2200.0)
    canvas.alpha_composite(tilted_grid)

    # 90 3D DoF particles flying through Z-space
    d = ImageDraw.Draw(canvas)
    focal = 1750.0
    cam_z = t * 210.0
    palette = [(255, 218, 44), (68, 162, 255), (242, 245, 255)]
    for px, py, pz, rad, c_idx in get_particles_90():
        rel_z = (pz - cam_z) % 1450.0 + 90.0
        proj = focal / (focal + rel_z)
        sx = int(W * 0.5 + px * proj)
        sy = int(H * 0.44 + py * proj)
        if 0 <= sx < W and 0 <= sy < H:
            a = int(clamp(1.15 - rel_z / 1350.0, 0.2, 0.9) * 195)
            r = max(1, int(rad * proj))
            c = palette[c_idx]
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(c[0], c[1], c[2], a))

    # Golden & Cyan Bezier Vector Splines + 4 Floating Rhythm Nodes
    nodes = [
        (195, 420, "0.18s • MICRO", (68, 168, 255)),
        (865, 495, "0.30s • ÉTAT", (255, 218, 44)),
        (210, 1085, "0.48s • REVEAL", (92, 238, 162)),
        (855, 1145, "0.72s • SÉQUENCE", (255, 118, 92)),
    ]
    d.line([(195, 420), (540, 740), (865, 495)], fill=(68, 168, 255, 150), width=3)
    d.line([(210, 1085), (540, 740), (855, 1145)], fill=(255, 218, 44, 150), width=3)

    # 3D Rotating Faceted Icosahedron Crystal at (540, 740)
    scale_in = expo_out(t / 0.65)
    draw_3d_icosahedron(
        canvas,
        cx=540,
        cy=740,
        radius=245.0 * (0.65 + 0.35 * scale_in),
        rx_deg=t * 28.0,
        ry_deg=t * 42.0,
        rz_deg=t * 16.0,
    )

    f_node = get_font(MONO_MED, 21)
    for idx, (nx, ny, n_lbl, ncol) in enumerate(nodes):
        np_in = expo_out((t - 0.25 - idx * 0.14) / 0.45)
        if np_in > 0.02:
            ny_cur = int(ny + 28 * (1.0 - np_in) + 8 * math.sin(t * 2.4 + idx))
            a_n = int(245 * np_in)
            d.rounded_rectangle([nx - 125, ny_cur - 28, nx + 125, ny_cur + 28], radius=24, fill=(14, 20, 32, a_n), outline=(ncol[0], ncol[1], ncol[2], a_n), width=2)
            d.ellipse([nx - 108, ny_cur - 7, nx - 94, ny_cur + 7], fill=(ncol[0], ncol[1], ncol[2], a_n))
            d.text((nx - 82, ny_cur - 13), n_lbl, font=f_node, fill=(242, 246, 255, a_n))

    draw_hud_frame(canvas, "01", "GÉOMÉTRIE 3D & Z-SPACE", t, dark=True)

    if t < 3.00:
        draw_motion_lockup(canvas, t - 0.15, "architecture spatiale et", "Motion 3D", "pure géométrie", cy=1475)
    else:
        draw_motion_lockup(canvas, t - 3.00, "chaque pixel obéit à", "La Physique", "du mouvement", cy=1475)

    return canvas


# ---------------------------------------------------------------------------
# Act II (6.00s - 12.00s): La Courbe Maîtresse — Swiss Grid & Cubic-Bezier Lab
# ---------------------------------------------------------------------------
def render_act2_bezier_lab(t: float) -> Image.Image:
    age = t - 6.00
    canvas = Image.new("RGBA", (W, H), (8, 12, 22, 255))
    d = ImageDraw.Draw(canvas)

    # 4-Column Vertical Accordion Swiss Grid Background
    col_colors = [(12, 18, 32), (16, 24, 42), (12, 18, 32), (16, 24, 42)]
    sw = W // 4
    for i in range(4):
        lp = expo_out((age - i * 0.065) / 0.48)
        y_end = int(H * lp)
        c = col_colors[i]
        d.rectangle([i * sw, 0, (i + 1) * sw, y_end], fill=(c[0], c[1], c[2], 255))
        if i > 0:
            d.line([(i * sw, 0), (i * sw, H)], fill=(58, 88, 142, 95), width=2)

    draw_hud_frame(canvas, "02", "COURBE MAÎTRESSE CUBIC-BEZIER", t, dark=True)

    # 3D-Tilted Interactive Bezier Laboratory Card (y=190..940)
    lab = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lab)
    bx0, by0, bx1, by1 = 76, 195, 1004, 935
    ld.rounded_rectangle([bx0, by0, bx1, by1], radius=26, fill=(10, 15, 26, 242), outline=(255, 218, 44, 225), width=3)

    f_mono = get_font(MONO_MED, 24)
    f_bold = get_font(JAKARTA_BOLD, 32)
    ld.text((bx0 + 36, by0 + 26), "--motion-ease-out : cubic-bezier(0.2, 0.8, 0.2, 1.0)", font=f_mono, fill=(255, 224, 58, 255))

    # Plot coordinates
    px0, py0, pw, ph = 175, 845, 730, 520
    for k in range(5):
        yy = py0 - int(ph * k / 4)
        xx = px0 + int(pw * k / 4)
        ld.line([(px0, yy), (px0 + pw, yy)], fill=(38, 56, 88, 170), width=1)
        ld.line([(xx, py0 - ph), (xx, py0)], fill=(38, 56, 88, 170), width=1)

    # Control handles P0(0,0) -> P1(0.2, 0.8) and P3(1,1) -> P2(0.2, 1.0)
    p0 = (px0, py0)
    p1 = (px0 + int(0.2 * pw), py0 - int(0.8 * ph))
    p2 = (px0 + int(0.2 * pw), py0 - int(1.0 * ph))
    p3 = (px0 + pw, py0 - ph)
    ld.line([p0, p1], fill=(255, 105, 92, 220), width=3)
    ld.line([p3, p2], fill=(68, 175, 255, 220), width=3)
    ld.ellipse([p1[0] - 10, p1[1] - 10, p1[0] + 10, p1[1] + 10], fill=(255, 105, 92, 255))
    ld.ellipse([p2[0] - 10, p2[1] - 10, p2[0] + 10, p2[1] + 10], fill=(68, 175, 255, 255))
    ld.text((p1[0] + 18, p1[1] - 14), "P1(0.2, 0.8) • départ franc", font=f_mono, fill=(255, 145, 132, 255))
    ld.text((p2[0] + 18, p2[1] - 14), "P2(0.2, 1.0) • arrivée amortie", font=f_mono, fill=(132, 205, 255, 255))

    # Linear comparison diagonal vs Master Cubic-Bezier curve
    ld.line([p0, p3], fill=(95, 112, 142, 140), width=3)
    pts = []
    for i in range(81):
        u = i / 80.0
        v = cubic_bezier(u, 0.2, 0.8, 0.2, 1.0)
        pts.append((px0 + int(u * pw), py0 - int(v * ph)))
    ld.line(pts, fill=(255, 222, 44, 255), width=8)

    # Live racing spheres comparing Linear vs Ease-In vs Master Cubic-Bezier (y=985..1310)
    u_race = (age * 0.65) % 1.0
    v_bez = cubic_bezier(u_race, 0.2, 0.8, 0.2, 1.0)
    v_lin = u_race
    v_nudge = nudge_curve_3phase(u_race)

    cx_dot = px0 + int(u_race * pw)
    cy_dot = py0 - int(v_bez * ph)
    ld.ellipse([cx_dot - 15, cy_dot - 15, cx_dot + 15, cy_dot + 15], fill=(255, 255, 255, 255), outline=(255, 218, 44, 255), width=4)

    tracks = [
        ("CUBIC-BEZIER(.2,.8,.2,1)", v_bez, (255, 222, 44)),
        ("NUDGE CURVE 10/65/25", v_nudge, (72, 182, 255)),
        ("LINEAR (SANS ÂME)", v_lin, (118, 132, 158)),
    ]
    for idx, (t_name, val, tcol) in enumerate(tracks):
        ty = 1005 + idx * 105
        ld.rounded_rectangle([76, ty, 1004, ty + 78], radius=20, fill=(14, 20, 34, 235), outline=(48, 68, 104, 190), width=2)
        ld.text((102, ty + 24), t_name, font=f_mono, fill=(210, 222, 242, 240))
        rx_start, rx_end = 485, 955
        bx_cur = int(rx_start + (rx_end - rx_start) * val)
        ld.line([(rx_start, ty + 39), (rx_end, ty + 39)], fill=(45, 62, 92, 200), width=4)
        ld.ellipse([bx_cur - 22, ty + 17, bx_cur + 22, ty + 61], fill=(tcol[0], tcol[1], tcol[2], 255))

    warped_lab = warp_plane_3d(lab, rx_deg=3.5, ry_deg=-6.5 + 3.0 * math.sin(age * 0.7), focal=2400.0)
    canvas.alpha_composite(warped_lab)

    # Climax Vertical Yellow-Gold Echo Repeat Stack in the last 1.4s of Act II
    if age >= 4.60:
        c_age = age - 4.60
        cp = expo_out(c_age / 0.48)
        f_big = get_font(JAKARTA_BOLD, 112)
        word = "VÉLOCITÉ"
        bb = d.textbbox((0, 0), word, font=f_big)
        cw = bb[2] - bb[0]
        cx = (W - cw) // 2
        cy_mid = 1520
        for k in range(-3, 4):
            if k == 0:
                continue
            ey = int(cy_mid + k * 112 * cp)
            ea = int(195 * (1.0 - abs(k) * 0.22) * cp)
            d.text((cx, ey), word, font=f_big, fill=(255, 222, 40, ea))
        d.text((cx + 3, cy_mid + 5), word, font=f_big, fill=(0, 0, 0, 220))
        d.text((cx, cy_mid), word, font=f_big, fill=(255, 255, 255, 255))
    else:
        draw_motion_lockup(canvas, age - 0.15, "départ franc et arrivée amortie", "Cubic Bezier", "zéro rebond parasite", cy=1490)

    return canvas


# ---------------------------------------------------------------------------
# Act III (12.00s - 18.00s): L'Architecture de la Lumière — Cream Bauhaus Portal
# ---------------------------------------------------------------------------
def render_act3_bauhaus_portal(t: float) -> Image.Image:
    age = t - 12.00
    # Warm Cream Drafting-Paper Canvas (#F6EFE0)
    canvas = Image.new("RGBA", (W, H), (246, 239, 224, 255))
    d = ImageDraw.Draw(canvas)

    # Architectural fold splines in gold & vermilion
    gold_pts = [(120, 140), (880, 260), (960, 740), (740, 1280), (140, 1360)]
    red_pts = [(0, 1180), (340, 1020), (740, 1190), (1080, 960)]
    d.line(gold_pts, fill=(214, 160, 58, 225), width=5)
    d.line(red_pts, fill=(212, 64, 44, 245), width=24)

    # Extruded 3D Isometric Architectural Monoliths with Contact Shadows
    m_p = expo_out(age / 0.65)
    ul_x = int(-160 * (1.0 - m_p))
    d.polygon([(42, 160), (290 + ul_x, 160), (195 + ul_x, 450), (42, 580)], fill=(20, 18, 14, 75))
    d.polygon([(42, 145), (275 + ul_x, 145), (180 + ul_x, 435), (42, 565)], fill=(28, 34, 38, 245))

    rm_x = int(160 * (1.0 - m_p))
    d.polygon([(1038, 480), (810 + rm_x, 660), (810 + rm_x, 960), (1038, 810)], fill=(20, 18, 14, 75))
    d.polygon([(1038, 465), (795 + rm_x, 645), (795 + rm_x, 945), (1038, 795)], fill=(28, 34, 38, 245))

    # Center 3D Dark Circular Portal with Orbiting Glassmorphic Pills (cx=540, cy=740)
    portal_r = int(round(335 * expo_out((age - 0.10) / 0.55)))
    cx, cy = 540, 740
    if portal_r > 20:
        d.ellipse([cx - portal_r + 12, cy - portal_r + 18, cx + portal_r + 12, cy + portal_r + 18], fill=(20, 18, 14, 95))
        d.ellipse([cx - portal_r, cy - portal_r, cx + portal_r, cy + portal_r], fill=(10, 13, 20, 255), outline=(68, 152, 255, 235), width=6)

        # Concentric rotating radar rings inside the dark portal
        for r_ring in (portal_r - 36, portal_r - 95, portal_r - 165):
            if r_ring > 20:
                d.ellipse([cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring], outline=(42, 68, 112, 140), width=2)

        # 3 Staggered 3D Pills inside the portal
        pills = [
            (0.35, "01 • HIÉRARCHIE VISUELLE", -95, (48, 132, 252)),
            (0.55, "02 • CONTRASTE CHROMATIQUE", 0, (255, 214, 42)),
            (0.75, "03 • FLUIDITÉ & MÉMOIRE", 95, (232, 84, 52)),
        ]
        f_pill = get_font(JAKARTA_BOLD, 30)
        for p_delay, p_txt, y_off, p_col in pills:
            if age > p_delay:
                pp = expo_out((age - p_delay) / 0.42)
                py = int(cy + y_off + 32 * (1.0 - pp))
                pw_half = 248
                txt_col = (12, 14, 18, int(255 * pp)) if p_col[0] > 200 and p_col[1] > 180 else (255, 255, 255, int(255 * pp))
                d.rounded_rectangle(
                    [cx - pw_half, py - 34, cx + pw_half, py + 34],
                    radius=34,
                    fill=(p_col[0], p_col[1], p_col[2], int(248 * pp)),
                )
                bb = d.textbbox((0, 0), p_txt, font=f_pill)
                d.text((cx - (bb[2] - bb[0]) // 2, py - 19), p_txt, font=f_pill, fill=txt_col)

    # Glowing Golden-Red Laser Light Beam sweeping diagonally across the canvas
    if age > 1.20:
        beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam)
        bx_top = int(220 + 640 * math.sin((age - 1.20) * 0.95))
        bx_bot = bx_top - 260
        bd.line([(bx_top, 42), (bx_bot, H - 42)], fill=(235, 78, 42, 215), width=36)
        bd.line([(bx_top, 42), (bx_bot, H - 42)], fill=(255, 242, 200, 255), width=12)
        beam = beam.filter(ImageFilter.GaussianBlur(radius=6))
        canvas.alpha_composite(beam)

    draw_hud_frame(canvas, "03", "COMPOSITION BAUHAUS & PORTAIL 3D", t, dark=False)
    draw_motion_lockup(canvas, age - 0.20, "guider l'œil par le contraste", "Architecture", "de la lumière", cy=1485, hero_color=(24, 26, 34), dark_bg=False)
    return canvas


# ---------------------------------------------------------------------------
# Act IV (18.00s - 24.00s): La Continuité Vectorielle — 3D Staircase & Volumetric Cones
# ---------------------------------------------------------------------------
def render_act4_staircase_hud(t: float) -> Image.Image:
    age = t - 18.00
    canvas = Image.new("RGBA", (W, H), (7, 9, 15, 255))

    # Twin Volumetric Spotlight Cones from top lamps
    cones = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cones)
    cd.polygon([(310, 150), (70, 1380), (550, 1380)], fill=(255, 192, 78, 62))
    cd.polygon([(770, 150), (530, 1380), (1010, 1380)], fill=(64, 158, 255, 62))
    cones = cones.filter(ImageFilter.GaussianBlur(radius=34))
    canvas.alpha_composite(cones)

    draw_hud_frame(canvas, "04", "CONTINUITÉ VECTORIELLE & ESCALIER 3D", t, dark=True)

    # 3D Winding Architectural Staircase spiraling from bottom-left (y=1720) to top portal (y=460)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n_steps = 26
    build_p = expo_out(age / 0.85)
    vis_steps = int(round(n_steps * build_p))

    pts = []
    for i in range(n_steps):
        u = i / float(n_steps - 1)
        cx = 240 + 520 * u + 220 * math.sin(u * math.pi * 2.0 - 0.3)
        cy = 1360 - 880 * (u ** 0.92)
        ws = int(round(145 * (1.0 - 0.35 * u)))
        pts.append((cx, cy, ws, u))

    # Glowing trail under steps
    for i in range(vis_steps):
        cx, cy, ws, u = pts[i]
        x0, x1, y0 = int(cx - ws), int(cx + ws), int(cy)
        # Highlight active step as the golden energy orb climbs
        orb_idx = int(((age * 0.45) % 1.0) * (n_steps - 1))
        is_lit = abs(i - orb_idx) <= 2
        tread_col = (255, 224, 58, 255) if is_lit else (232, 236, 245, 255)
        riser_col = (128, 98, 24, 245) if is_lit else (54, 60, 72, 245)
        d.rectangle([x0, y0, x1, y0 + 36], fill=riser_col, outline=(115, 122, 136, 255), width=1)
        d.polygon([(x0, y0), (x1, y0), (x1 + 12, y0 - 18), (x0 + 12, y0 - 18)], fill=tread_col, outline=(160, 168, 182, 255))

    # Climbing Golden Energy Sphere on the staircase
    if vis_steps > 2:
        orb_u = (age * 0.45) % 1.0
        orb_i = min(vis_steps - 1, int(orb_u * (n_steps - 1)))
        ox, oy, _, _ = pts[orb_i]
        oy -= 42
        glow_o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        god = ImageDraw.Draw(glow_o)
        god.ellipse([ox - 46, oy - 46, ox + 46, oy + 46], fill=(255, 212, 38, 185))
        glow_o = glow_o.filter(ImageFilter.GaussianBlur(radius=18))
        layer.alpha_composite(glow_o)
        d.ellipse([ox - 18, oy - 18, ox + 18, oy + 18], fill=(255, 255, 255, 255), outline=(255, 218, 44, 255), width=4)

    # 4 Floating Seam Callout Badges along the staircase
    badges = [
        (0.30, 245, 1180, "01 • ZOOM-THROUGH (Z+)", (68, 168, 255)),
        (0.55, 815, 960, "02 • INVERSE ZOOM (Z-)", (255, 218, 44)),
        (0.80, 260, 720, "03 • CUT THE CURVE (±12%)", (92, 238, 162)),
        (1.05, 795, 490, "04 • RACK-FOCUS (13PX)", (255, 118, 92)),
    ]
    f_b = get_font(MONO_MED, 21)
    for b_delay, bx, by, b_txt, bcol in badges:
        if age > b_delay:
            bp = expo_out((age - b_delay) / 0.42)
            by_c = int(by + 24 * (1.0 - bp))
            a_b = int(245 * bp)
            d.rounded_rectangle([bx - 165, by_c - 28, bx + 165, by_c + 28], radius=22, fill=(14, 20, 32, a_b), outline=(bcol[0], bcol[1], bcol[2], a_b), width=2)
            d.text((bx - 142, by_c - 13), b_txt, font=f_b, fill=(245, 248, 255, a_b))

    canvas.alpha_composite(layer)
    draw_motion_lockup(canvas, age - 0.20, "couper au pic de vitesse", "Cut the Curve", "continuité parfaite", cy=1510)
    return canvas


# ---------------------------------------------------------------------------
# Act V (24.00s - 30.00s): Typographie Cinétique Monumentale & Bento 3D
# ---------------------------------------------------------------------------
def render_act5_kinetic_bento(t: float) -> Image.Image:
    age = t - 24.00
    canvas = Image.new("RGBA", (W, H), (9, 12, 20, 255))
    d = ImageDraw.Draw(canvas)

    # Giant Vertical Stacked Display Typography "M-O-T-I-O-N" along left edge (x=28..310)
    word = "MOTION"
    step_h = (H - 160) // len(word)
    f_vert = get_font(JAKARTA_BOLD, 248)
    for idx, ch_str in enumerate(word):
        cp = expo_out((age - idx * 0.055) / 0.44)
        if cp <= 0.01:
            continue
        lx = int(32 - 210 * (1.0 - cp))
        ly = 65 + idx * step_h - 24
        col = (34, 152, 236, int(248 * cp)) if idx < 3 else (232, 96, 36, int(248 * cp))
        d.text((lx + 5, ly + 7), ch_str, font=f_vert, fill=(0, 0, 0, int(175 * cp)))
        d.text((lx, ly), ch_str, font=f_vert, fill=col)

    draw_hud_frame(canvas, "05", "TYPOGRAPHIE CINÉTIQUE & BENTO 3D", t, dark=True)

    # Right-side 3D Perspective Bento Motion Widgets (x=330..1010, y=195..1310)
    bento = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bento)
    f_mono = get_font(MONO_MED, 22)
    f_val = get_font(JAKARTA_BOLD, 56)

    # Widget 1: Radial Velocity Ring & Waterfall Decay Gauge (y=210..560)
    bd.rounded_rectangle([340, 210, 1004, 555], radius=24, fill=(15, 22, 36, 240), outline=(68, 158, 255, 220), width=3)
    bd.text((374, 236), "WATERFALL DECAY // GAP × 0.84^i", font=f_mono, fill=(138, 198, 255, 245))
    # Radial gauge
    rcx, rcy, rr = 495, 410, 92
    bd.ellipse([rcx - rr, rcy - rr, rcx + rr, rcy + rr], outline=(42, 64, 98, 200), width=14)
    ang_end = int(-90 + 360 * clamp((age * 0.55) % 1.0))
    bd.arc([rcx - rr, rcy - rr, rcx + rr, rcy + rr], start=-90, end=ang_end, fill=(255, 218, 44, 255), width=14)
    pct_val = int(((age * 0.55) % 1.0) * 100)
    bd.text((rcx - 48, rcy - 32), f"{pct_val:02d}%", font=f_val, fill=(255, 255, 255, 255))

    # Cascading bars showing 0.84 decay
    for k in range(6):
        bar_h = int(165 * (0.84 ** k) * expo_out((age - 0.2 - k * 0.08) / 0.4))
        bx = 650 + k * 52
        bd.rounded_rectangle([bx, 505 - bar_h, bx + 34, 505], radius=6, fill=(68, 168, 255, 240))

    # Widget 2: Harmonic Spring Oscillator & Phase Wave (y=590..935)
    bd.rounded_rectangle([340, 590, 1004, 935], radius=24, fill=(15, 22, 36, 240), outline=(255, 218, 44, 220), width=3)
    bd.text((374, 616), "OSCILLATEUR HARMONIQUE // ZETA = 0.74", font=f_mono, fill=(255, 224, 68, 245))
    wave_pts = []
    for i in range(120):
        u = i / 119.0
        wx = 374 + int(u * 596)
        damped = math.exp(-3.2 * u) * math.cos(16.0 * u - age * 6.0)
        wy = 785 - int(95 * damped)
        wave_pts.append((wx, wy))
    bd.line([(374, 785), (970, 785)], fill=(52, 74, 112, 160), width=2)
    bd.line(wave_pts, fill=(92, 238, 162, 255), width=6)

    # Widget 3: 3D Extruded Chrome / Gold Kinetic Counter (y=970..1295)
    bd.rounded_rectangle([340, 970, 1004, 1295], radius=24, fill=(15, 22, 36, 240), outline=(232, 96, 36, 220), width=3)
    bd.text((374, 996), "CADENCE DE RENDU // FRAME-ACCURATE", font=f_mono, fill=(255, 152, 108, 245))
    f_huge = get_font(MONTSERRAT_BLACK_IT, 96)
    bd.text((378, 1075), "1080×1920", font=f_huge, fill=(255, 255, 255, 255))
    bd.text((382, 1195), "60 / 30 FPS • HDR BLOOM", font=f_mono, fill=(255, 218, 44, 255))

    warped_bento = warp_plane_3d(bento, rx_deg=3.5, ry_deg=-9.5 + 3.0 * math.sin(age * 0.7), focal=2300.0)
    canvas.alpha_composite(warped_bento)

    draw_motion_lockup(canvas, age - 0.15, "typographie monumentale et", "Précision", "image par image", cy=1495)
    return canvas


# ---------------------------------------------------------------------------
# Act VI (30.00s - 36.00s): Apothéose Géométrique — 3D Tunnel & Finale Signature
# ---------------------------------------------------------------------------
def render_act6_apotheosis(t: float) -> Image.Image:
    age = t - 30.00
    canvas = Image.new("RGBA", (W, H), (5, 7, 13, 255))
    d = ImageDraw.Draw(canvas)

    # 16 Concentric 3D Perspective Wireframe Tunnel Frames flying toward viewer
    cx, cy = W // 2, 760
    n_rings = 16
    for i in range(n_rings):
        depth = ((i / float(n_rings)) - (age * 0.28)) % 1.0
        if depth <= 0.02:
            continue
        proj = 0.08 + 1.35 * ((1.0 - depth) ** 2.2)
        rw = int(420 * proj)
        rh = int(640 * proj)
        alpha = int(clamp((1.0 - depth) * depth * 4.2, 0.0, 1.0) * 215)
        col = (255, 218, 44, alpha) if i % 2 == 0 else (68, 162, 255, alpha)
        d.rounded_rectangle([cx - rw, cy - rh, cx + rw, cy + rh], radius=max(8, int(36 * proj)), outline=col, width=3)

    # Central 3D Rotating Icosahedron Crystal at peak velocity
    draw_3d_icosahedron(
        canvas,
        cx=cx,
        cy=cy,
        radius=235.0,
        rx_deg=age * 45.0,
        ry_deg=age * 62.0,
        rz_deg=age * 28.0,
    )

    draw_hud_frame(canvas, "06", "APOTHÉOSE MOTION DESIGN", t, dark=True)
    draw_motion_lockup(canvas, age - 0.15, "l'alliance du code et du", "Pure Motion", "Architecture & Rythme", cy=1470)
    return canvas


# ---------------------------------------------------------------------------
# Master Frame Dispatcher + Velocity-Matched Seams (`motion_engine.py`)
# ---------------------------------------------------------------------------
def _render_act_at(t: float) -> Image.Image:
    if t < 6.00:
        return render_act1_emergence(t)
    if t < 12.00:
        return render_act2_bezier_lab(t)
    if t < 18.00:
        return render_act3_bauhaus_portal(t)
    if t < 24.00:
        return render_act4_staircase_hud(t)
    if t < 30.00:
        return render_act5_kinetic_bento(t)
    return render_act6_apotheosis(t)


SEAMS = [
    (6.00, 0.36, "zoom_in"),
    (12.00, 0.36, "cut_left"),
    (18.00, 0.36, "rack_focus"),
    (24.00, 0.36, "inverse_zoom"),
    (30.00, 0.36, "zoom_in"),
]


def render_frame(t: float) -> np.ndarray:
    for cut_t, width_s, kind in SEAMS:
        t0, t1 = cut_t - width_s * 0.40, cut_t + width_s * 0.60
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            old_im = _render_act_at(cut_t - 0.04)
            new_im = _render_act_at(max(cut_t + 0.02, t))
            if kind == "zoom_in":
                out = zoom_through_seam(old_im, new_im, p, inverse=False)
            elif kind == "inverse_zoom":
                out = zoom_through_seam(old_im, new_im, p, inverse=True)
            elif kind == "cut_left":
                out = cut_the_curve_seam(old_im, new_im, p, direction="left")
            else:
                out = rack_focus_blur_cut(old_im, new_im, p)
            return np.array(out.convert("RGB"))

    out = _render_act_at(t)
    return np.array(out.convert("RGB"))


# ---------------------------------------------------------------------------
# Procedural Electronic & Cinematic Motion-Design Soundtrack Generator
# ---------------------------------------------------------------------------
def generate_motion_soundtrack(out_wav_path: str):
    os.makedirs(os.path.dirname(out_wav_path), exist_ok=True)
    sr = 48000
    n_samples = int(DURATION * sr)
    t = np.arange(n_samples, dtype=np.float32) / sr

    # 1. Warm stereo lush synth pad (D minor 9 -> Bb maj7 -> G minor 9 -> A7sus4 progression every 6s)
    chords = [
        (146.83, 174.61, 220.00, 261.63, 329.63),  # Act I: Dm9
        (116.54, 174.61, 220.00, 293.66, 349.23),  # Act II: Bbmaj9
        (130.81, 196.00, 246.94, 293.66, 392.00),  # Act III: Cmaj9 / G
        (98.00,  146.83, 174.61, 220.00, 293.66),  # Act IV: Gm9
        (110.00, 164.81, 196.00, 261.63, 329.63),  # Act V: Am7
        (146.83, 220.00, 293.66, 349.23, 440.00),  # Act VI: Dm (Apex)
    ]

    pad_l = np.zeros(n_samples, dtype=np.float32)
    pad_r = np.zeros(n_samples, dtype=np.float32)

    for act_i, freqs in enumerate(chords):
        t0, t1 = act_i * 6.0, (act_i + 1) * 6.0
        mask = (t >= max(0.0, t0 - 0.4)) & (t < min(DURATION, t1 + 0.4))
        tm = t[mask]
        # Crossfade envelope
        env = np.ones_like(tm)
        env = np.minimum(env, np.clip((tm - (t0 - 0.4)) / 0.6, 0.0, 1.0))
        env = np.minimum(env, np.clip(((t1 + 0.4) - tm) / 0.6, 0.0, 1.0))
        for k, f_hz in enumerate(freqs):
            detune = 1.0 + (k - 2) * 0.0015
            pad_l[mask] += (0.045 / len(freqs)) * env * np.sin(2 * np.pi * f_hz * tm + k * 0.4)
            pad_r[mask] += (0.045 / len(freqs)) * env * np.sin(2 * np.pi * f_hz * detune * tm - k * 0.4)

    # 2. Rhythmic 120 BPM (0.5s beat / 0.25s 8th-note) crystalline plucks & sub-bass pulse
    arp_notes = [293.66, 349.23, 440.00, 523.25, 659.25, 523.25, 440.00, 349.23]
    step_s = 0.25
    n_steps = int(DURATION / step_s)
    pluck_l = np.zeros(n_samples, dtype=np.float32)
    pluck_r = np.zeros(n_samples, dtype=np.float32)

    for s_idx in range(n_steps):
        ts = s_idx * step_s
        i0 = int(ts * sr)
        i1 = min(n_samples, i0 + int(0.24 * sr))
        if i0 >= n_samples:
            break
        dt = (np.arange(i1 - i0, dtype=np.float32)) / sr
        f_note = arp_notes[s_idx % len(arp_notes)]
        env_p = np.exp(-dt * 16.0) * (1.0 - np.exp(-dt * 220.0))
        sig = 0.065 * env_p * (np.sin(2 * np.pi * f_note * dt) + 0.35 * np.sin(2 * np.pi * f_note * 2.0 * dt))
        pan = 0.65 if s_idx % 2 == 0 else 0.35
        pluck_l[i0:i1] += sig * pan
        pluck_r[i0:i1] += sig * (1.0 - pan)

        # Deep sub-bass pulse every 1.0s (4 steps)
        if s_idx % 4 == 0:
            ib1 = min(n_samples, i0 + int(0.45 * sr))
            dtb = (np.arange(ib1 - i0, dtype=np.float32)) / sr
            env_b = np.exp(-dtb * 7.5)
            f_drop = 73.42 + 45.0 * np.exp(-dtb * 28.0)
            sub = 0.14 * env_b * np.sin(2 * np.pi * f_drop * dtb)
            pluck_l[i0:ib1] += sub
            pluck_r[i0:ib1] += sub

    # 3. Cinematic seam whoosh + impact at every 6.0s Act transition
    sfx = np.zeros(n_samples, dtype=np.float32)
    for cut_t in (0.15, 6.00, 12.00, 18.00, 24.00, 30.00):
        mask = (t >= max(0.0, cut_t - 0.22)) & (t <= min(DURATION, cut_t + 0.38))
        dt = t[mask] - cut_t
        env_w = np.exp(-((dt - 0.02) / 0.11) ** 2)
        freq_w = 130.0 - 70.0 * ((dt + 0.22) / 0.60)
        sfx[mask] += 0.16 * env_w * np.sin(2 * np.pi * freq_w * (dt + 0.22))

    # Master fade-in & fade-out
    fade = np.ones(n_samples, dtype=np.float32)
    fi = int(0.45 * sr)
    fo = int(1.10 * sr)
    fade[:fi] = np.linspace(0.0, 1.0, fi)
    fade[-fo:] = np.linspace(1.0, 0.0, fo)

    mix_l = np.clip((pad_l + pluck_l + sfx) * fade, -0.95, 0.95)
    mix_r = np.clip((pad_r + pluck_r + sfx) * fade, -0.95, 0.95)
    pcm16 = (np.stack([mix_l, mix_r], axis=-1) * 32767.0).astype(np.int16)

    with wave.open(out_wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())
    print(f"Generated procedural motion soundtrack: {out_wav_path}")


# ---------------------------------------------------------------------------
# Preview Contact Sheet & Full MP4 Encoder
# ---------------------------------------------------------------------------
def build_preview_grid(out_jpg_path: str):
    preview_times = [
        0.80, 2.20, 4.50, 6.00,
        7.20, 9.20, 11.20, 12.00,
        13.20, 15.20, 17.00, 18.00,
        19.20, 21.20, 23.00, 24.00,
        25.20, 27.20, 29.00, 30.00,
        31.20, 32.80, 34.20, 35.40,
    ]
    thumbs = []
    for t in preview_times:
        comp_rgb = render_frame(t)
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


def render_full_video(audio_wav_path: str, out_mp4_path: str):
    if not os.path.exists(audio_wav_path):
        generate_motion_soundtrack(audio_wav_path)
    os.makedirs(os.path.dirname(out_mp4_path), exist_ok=True)
    enc_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-", "-i", audio_wav_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        out_mp4_path
    ]
    enc_proc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)
    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        out_rgb = render_frame(t)
        enc_proc.stdin.write(out_rgb.tobytes())
        if f_idx % 180 == 0 or f_idx == TOTAL_FRAMES - 1:
            print(f"Rendered frame {f_idx + 1}/{TOTAL_FRAMES} ({t:.2f}s / {DURATION:.2f}s)")
            sys.stdout.flush()

    enc_proc.stdin.close()
    enc_proc.wait()
    if enc_proc.returncode != 0:
        raise RuntimeError(f"FFmpeg encode failed with code {enc_proc.returncode}")
    print(f"Successfully rendered {out_mp4_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="/home/user/COOL-backup/motion-design-pure/assets/audio/motion_soundtrack.wav")
    parser.add_argument(
        "--out",
        default="/home/user/COOL-backup/motion-design-pure/film/motion-design-pure-9x16.mp4",
    )
    parser.add_argument("--preview", default="")
    args = parser.parse_args()

    if args.preview:
        build_preview_grid(args.preview)
    else:
        generate_motion_soundtrack(args.audio)
        render_full_video(args.audio, args.out)
