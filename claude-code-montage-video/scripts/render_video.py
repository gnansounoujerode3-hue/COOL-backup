#!/usr/bin/env python3
"""
Master 9:16 Video Compositor (`1080x1920`, `30.00 fps`, `69.03s`)
"Comment utiliser Claude Code pour faire du Montage Vidéo 3D & Motion Design"

Combines:
- Synchronized 6-chapter French voiceover (`claude-code-montage-video/assets/audio/master_voiceover_mix.wav`)
- `.claude/skills/motion-code-harvester/scripts/motion_engine.py` (`zoom_through_seam`,
  `cut_the_curve_seam`, `rack_focus_blur_cut`, `waterfall_word_state`, `nudge_curve_3phase`,
  `swipe_clip_reveal`)
- True 3D perspective projective homography (`warp_plane_3d`)
- Live B-roll video clips & architectural plates from `felix-gray-reference9` & `felix-gray-reference10`
"""

import argparse
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
from motion_engine import (
    clamp,
    cubic_bezier,
    expo_out,
    power3_in,
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
DURATION = 69.03
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
# True 3D Perspective Homography (`warp_plane_3d`)
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


# ---------------------------------------------------------------------------
# Pre-load B-Roll Clips, Rendered Edits & High-Res Architectural Plates
# ---------------------------------------------------------------------------
_CACHE = None


def get_cache():
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    _CACHE = {}
    img_dir = "/home/user/COOL-backup/felix-gray-reference10/assets/images"
    broll_dir = "/home/user/COOL-backup/felix-gray-reference10/assets/broll"

    def load_fit(name, target_w=W, target_h=H, grayscale=False):
        p = f"{img_dir}/{name}"
        im = Image.open(p).convert("RGB")
        if grayscale:
            im = im.convert("L").convert("RGB")
            im = ImageEnhance.Contrast(im).enhance(1.18)
        iw, ih = im.size
        sc = max(target_w / iw, target_h / ih)
        nw, nh = int(round(iw * sc)), int(round(ih * sc))
        im = im.resize((nw, nh), Image.BICUBIC)
        x0, y0 = (nw - target_w) // 2, (nh - target_h) // 2
        return im.crop((x0, y0, x0 + target_w, y0 + target_h)).convert("RGBA")

    _CACHE["stage1"] = load_fit("stage1_monochrome_concrete.jpg", int(W * 1.08), int(H * 1.08), grayscale=True)
    _CACHE["stage2"] = load_fit("stage2_blueprint_sketch.jpg", int(W * 1.08), int(H * 1.08))
    _CACHE["stage3"] = load_fit("stage3_twilight_atrium.jpg", int(W * 1.08), int(H * 1.08))
    _CACHE["shard"] = load_fit("shard_skyline.jpg", int(W * 1.12), int(H * 1.12))
    _CACHE["model_card"] = Image.open(f"{img_dir}/arch_3d_model.jpg").convert("RGBA").resize((420, 248), Image.BICUBIC)

    def load_mp4_frames(mp4_path, cw, ch, max_frames=90, start_s=0.0):
        cmd = [
            "ffmpeg", "-v", "error", "-ss", f"{start_s:.2f}", "-i", mp4_path,
            "-frames:v", str(max_frames), "-vf", f"scale={cw}:{ch}",
            "-r", "30", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
        ]
        raw = subprocess.check_output(cmd)
        n = len(raw) // (cw * ch * 3)
        arr = np.frombuffer(raw[: n * cw * ch * 3], dtype=np.uint8).reshape((n, ch, cw, 3))
        return [Image.fromarray(arr[i]).convert("RGBA") for i in range(n)]

    _CACHE["broll_cad"] = load_mp4_frames(f"{broll_dir}/broll_blueprint_cad.mp4", 420, 236, max_frames=90)
    _CACHE["broll_site"] = load_mp4_frames(f"{broll_dir}/broll_construction_site.mp4", 420, 236, max_frames=90)
    _CACHE["ref9_clip"] = load_mp4_frames(
        "/home/user/COOL-backup/felix-gray-reference9/film/felix-gray-reference9-9x16.mp4",
        380, 675, max_frames=90, start_s=1.2
    )
    _CACHE["ref10_clip"] = load_mp4_frames(
        "/home/user/COOL-backup/felix-gray-reference10/film/felix-gray-reference10-9x16.mp4",
        380, 675, max_frames=90, start_s=4.2
    )
    _CACHE["ref10_head"] = load_mp4_frames(
        "/home/user/COOL-backup/felix-gray-reference10/film/felix-gray-reference10-9x16.mp4",
        720, 660, max_frames=90, start_s=0.8
    )

    # 70 3D particles
    rng = np.random.default_rng(42)
    pts = []
    for _ in range(70):
        pts.append((
            float(rng.uniform(-620, 620)),
            float(rng.uniform(-980, 980)),
            float(rng.uniform(80, 1400)),
            int(rng.integers(3, 8)),
            bool(rng.random() < 0.45),
        ))
    _CACHE["particles"] = pts
    return _CACHE


# ---------------------------------------------------------------------------
# Shared Kinetic Lock-up & Step Header Badge
# ---------------------------------------------------------------------------
def draw_step_badge(canvas: Image.Image, step_label: str, title: str, age: float, dark: bool = True):
    p = expo_out(age / 0.40)
    dy = int(round(24 * (1.0 - p)))
    alpha = int(255 * clamp(age / 0.18))

    layer = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f_badge = get_font(MONO_MED, 24)
    f_title = get_font(JAKARTA_BOLD, 38)

    # Pill badge
    pill_bg = (255, 218, 38, alpha) if dark else (18, 22, 30, alpha)
    pill_fg = (14, 16, 22, alpha) if dark else (255, 222, 44, alpha)
    d.rounded_rectangle([64, 58 + dy, 310, 108 + dy], radius=24, fill=pill_bg)
    d.text((88, 68 + dy), step_label, font=f_badge, fill=pill_fg)

    title_col = (246, 248, 252, alpha) if dark else (18, 20, 26, alpha)
    d.text((332, 62 + dy), title, font=f_title, fill=title_col)
    canvas.alpha_composite(layer, (0, 0))


def draw_kinetic_lockup(
    canvas: Image.Image,
    age: float,
    lead_text: str,
    hero_text: str,
    script_text: str = "",
    cy: int = 1480,
    hero_color=(255, 226, 44),
):
    a_lead, dy_lead, _ = waterfall_word_state(age, word_index=0, weight="normal")
    a_hero, dy_hero, _ = waterfall_word_state(age, word_index=1, weight="anchor")
    hero_age = max(0.0, age - 0.055)
    nudge_dy = -14.0 * nudge_curve_3phase(max(0.0, hero_age - 0.10) / 0.42) if script_text else 0.0

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    f_lead = get_font(INTER_MED, 46)
    f_hero = get_font(JAKARTA_BOLD, 92)
    f_script = get_font(GREAT_VIBES, 118)

    if lead_text and a_lead > 0.02:
        bb_l = od.textbbox((0, 0), lead_text, font=f_lead)
        lw = bb_l[2] - bb_l[0]
        lx, ly = (W - lw) // 2, int(cy - 64 + dy_lead + nudge_dy)
        od.text((lx + 2, ly + 4), lead_text, font=f_lead, fill=(0, 0, 0, int(195 * a_lead)))
        od.text((lx, ly), lead_text, font=f_lead, fill=(248, 248, 252, int(255 * a_lead)))

    if hero_text and a_hero > 0.02:
        bb_h = od.textbbox((0, 0), hero_text, font=f_hero)
        hw = bb_h[2] - bb_h[0]
        hx, hy = (W - hw) // 2, int(cy - 8 + dy_hero + nudge_dy)

        if 0.01 < hero_age < 0.55:
            ep = 1.0 - power4_out(hero_age / 0.55)
            for mult, asc in [(1, 0.42), (2, 0.22)]:
                off = int(round(mult * 68 * ep))
                ea = int(255 * asc * ep)
                od.text((hx, hy - off), hero_text, font=f_hero, fill=(255, 220, 40, ea))
                od.text((hx, hy + off), hero_text, font=f_hero, fill=(255, 220, 40, ea))

        glow = Image.new("RGBA", (W, 250), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.text((hx, 65), hero_text, font=f_hero, fill=(255, 200, 15, int(195 * a_hero)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=20))
        overlay.alpha_composite(glow, (0, hy - 65))

        od.text((hx + 3, hy + 5), hero_text, font=f_hero, fill=(0, 0, 0, int(205 * a_hero)))
        od.text((hx, hy), hero_text, font=f_hero, fill=(hero_color[0], hero_color[1], hero_color[2], int(255 * a_hero)))

    if script_text:
        sc_age = max(0.0, hero_age - 0.12)
        if sc_age > 0.01:
            sc_layer = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
            scd = ImageDraw.Draw(sc_layer)
            bb_sc = scd.textbbox((0, 0), script_text, font=f_script)
            sc_w = bb_sc[2] - bb_sc[0]
            sc_x = (W - sc_w) // 2 + 10
            scd.text((sc_x + 3, 44), script_text, font=f_script, fill=(0, 0, 0, 225))
            scd.text((sc_x, 40), script_text, font=f_script, fill=(255, 255, 255, 255))
            sc_wiped = swipe_clip_reveal(sc_layer, sc_age / 0.42, direction="left_to_right")
            overlay.alpha_composite(sc_wiped, (0, int(cy + 58)))

    canvas.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# Scene 1 (0.00s - 8.45s): Hook — 3D Z-Space Claude Code Terminal & Live Preview
# ---------------------------------------------------------------------------
def render_scene1_hook(t: float) -> Image.Image:
    cache = get_cache()
    canvas = Image.new("RGBA", (W, H), (6, 8, 14, 255))

    # 3D perspective blueprint grid
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for gx in range(80, W, 80):
        gd.line([(gx, 0), (gx, H)], fill=(32, 56, 98, 95), width=1)
    for gy in range(80, H, 80):
        gd.line([(0, gy), (W, gy)], fill=(32, 56, 98, 95), width=1)
    tilted_grid = warp_plane_3d(grid, rx_deg=8.0, ry_deg=-14.0 + t * 1.2, focal=2200.0)
    canvas.alpha_composite(tilted_grid)

    # 70 3D DoF particles
    d = ImageDraw.Draw(canvas)
    focal = 1800.0
    cam_z = t * 140.0
    for px, py, pz, rad, is_gold in cache["particles"]:
        rel_z = (pz - cam_z) % 1400.0 + 120.0
        proj = focal / (focal + rel_z)
        sx = int(W * 0.5 + px * proj)
        sy = int(H * 0.48 + py * proj)
        if 0 <= sx < W and 0 <= sy < H:
            a = int(clamp(1.15 - rel_z / 1300.0, 0.2, 0.85) * 180)
            r = max(1, int(rad * proj))
            col = (255, 216, 44, a) if is_gold else (70, 155, 255, a)
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=col)

    draw_step_badge(canvas, "CLAUDE CODE", "MONTAGE VIDÉO 3D & MOTION", t, dark=True)

    # 3D Frosted-Glass Claude Code Terminal Window (x=70..1010, y=220..790)
    term_plane = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(term_plane)
    tx0, ty0, tx1, ty1 = 76, 225, 1004, 775
    td.rounded_rectangle([tx0, ty0, tx1, ty1], radius=24, fill=(14, 18, 28, 240), outline=(88, 156, 255, 220), width=3)
    # macOS traffic lights + header
    for idx, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx_dot = tx0 + 36 + idx * 28
        td.ellipse([cx_dot - 8, ty0 + 22, cx_dot + 8, ty0 + 38], fill=col)
    f_mono = get_font(MONO_MED, 24)
    f_mono_lg = get_font(MONO_MED, 28)
    td.text((tx0 + 145, ty0 + 16), "claude-code — /home/user/COOL-backup", font=f_mono, fill=(165, 182, 210, 235))
    td.line([(tx0, ty0 + 58), (tx1, ty0 + 58)], fill=(54, 78, 120, 180), width=2)

    cmd_str = '$ claude "Monte ma vidéo brute en 9:16 3D"'
    typed_n = min(len(cmd_str), max(1, int((t - 0.15) * 26)))
    td.text((tx0 + 34, ty0 + 86), cmd_str[:typed_n], font=f_mono_lg, fill=(255, 224, 52, 255))

    lines = [
        (1.10, "[✓] 206 Skills chargés (.claude/skills/)", (92, 238, 152)),
        (2.10, "[✓] Whisper JSON + MOTION-DESIGN.md (cubic-bezier)", (115, 195, 255)),
        (3.20, "[✓] B-Roll 4K & Images téléchargés (broll-media-fetcher)", (255, 198, 92)),
        (4.30, "[✓] Cut-the-Curve + Homographie 3D + Bloom HDR actifs", (238, 145, 255)),
    ]
    for idx, (t_appear, txt, col) in enumerate(lines):
        if t >= t_appear:
            lp = expo_out((t - t_appear) / 0.35)
            ly = int(ty0 + 165 + idx * 66 + 18 * (1.0 - lp))
            td.text((tx0 + 38, ly), txt, font=f_mono, fill=(col[0], col[1], col[2], int(255 * lp)))

    # Floating 3D Live Video Preview Card on the middle-right (y=720..1360)
    ref10_frames = cache["ref10_clip"]
    f_im = ref10_frames[int(t * FPS) % len(ref10_frames)]
    td.rounded_rectangle([340, 740, 740, 1365], radius=22, fill=(10, 12, 18, 245), outline=(255, 218, 44, 235), width=3)
    term_plane.alpha_composite(f_im.resize((380, 605), Image.BILINEAR), (350, 750))

    warped_term = warp_plane_3d(
        term_plane,
        rx_deg=4.5 - 2.0 * math.sin(t * 0.7),
        ry_deg=-7.5 + 3.0 * math.cos(t * 0.6),
        focal=2300.0,
    )
    canvas.alpha_composite(warped_term)

    if t < 4.20:
        draw_kinetic_lockup(canvas, t - 0.20, "transformer une vidéo brute avec", "Claude Code", "automatiquement", cy=1520)
    else:
        draw_kinetic_lockup(canvas, t - 4.20, "en un montage", "Trois D", "spectaculaire", cy=1520)

    return canvas


# ---------------------------------------------------------------------------
# Scene 2 (8.45s - 23.03s): Étape 1 — 206 Skills 3D, Three.js, Remotion & Motion
# ---------------------------------------------------------------------------
def render_scene2_skills(t: float) -> Image.Image:
    cache = get_cache()
    age = t - 8.45
    dur = 23.03 - 8.45

    # 4-Slice Vertical Accordion Architectural Evolution background
    im1 = cache["stage1"].crop((0, 0, W, H))
    im2 = cache["stage2"].crop((0, 0, W, H))
    im3 = cache["stage3"].crop((0, 0, W, H))

    def slice_blend(a_im, b_im, prog):
        out = a_im.copy()
        sw = W // 4
        for i in range(4):
            lp = expo_out((prog - i * 0.10) / 0.70)
            if lp <= 0.001:
                continue
            x0, x1 = i * sw, W if i == 3 else (i + 1) * sw
            col = b_im.crop((x0, 0, x1, H))
            dy = int(round((1.0 - lp) * H * (1 if i % 2 == 0 else -1)))
            out.alpha_composite(col, (x0, dy))
        return out

    canvas = im1.copy()
    if age > 2.2:
        canvas = slice_blend(canvas, im2, (age - 2.2) / 1.1)
    if age > 6.2:
        canvas = slice_blend(canvas, im3, (age - 6.2) / 1.1)

    # Dark translucent cinema scrim for card contrast
    scrim = Image.new("RGBA", (W, H), (8, 10, 16, 145))
    canvas.alpha_composite(scrim)

    draw_step_badge(canvas, "ÉTAPE 01", "INSTALLER .claude/skills/", age, dark=True)

    # 5 3D Perspective Skill Cards cascading in
    skill_cards = [
        (0.4, "threejs-skills & shaders", "WebGL / PBR / HDR Bloom / Homographie 3D", (58, 152, 255)),
        (2.0, "remotion-best-practices", "Rendu 3D frame-accurate @remotion/three", (92, 232, 162)),
        (3.8, "broll-media-fetcher", "Téléchargement auto Images & Vidéos B-Roll", (255, 194, 52)),
        (5.6, "cut-the-curve & seam-craft", "Transitions GSAP Zoom-Through & Waterfall", (245, 118, 255)),
        (7.4, "embedded-captions", "Typographie Vogue-cover derrière l'orateur", (255, 112, 82)),
    ]

    plane = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plane)
    f_c_title = get_font(JAKARTA_BOLD, 34)
    f_c_sub = get_font(INTER_REG, 26)
    f_c_tag = get_font(MONO_MED, 22)

    for idx, (t_in, s_name, s_desc, col) in enumerate(skill_cards):
        if age >= t_in:
            cp = expo_out((age - t_in) / 0.48)
            cy = int(245 + idx * 195 + 45 * (1.0 - cp))
            cx0, cx1 = 84, 996
            a = int(242 * cp)
            pd.rounded_rectangle([cx0, cy, cx1, cy + 162], radius=20, fill=(14, 18, 28, a), outline=(col[0], col[1], col[2], a), width=3)
            pd.rounded_rectangle([cx0 + 24, cy + 24, cx0 + 135, cy + 62], radius=10, fill=(col[0], col[1], col[2], a))
            pd.text((cx0 + 38, cy + 29), f"SKILL 0{idx+1}", font=f_c_tag, fill=(12, 14, 20, a))
            pd.text((cx0 + 158, cy + 22), s_name, font=f_c_title, fill=(250, 252, 255, a))
            pd.text((cx0 + 28, cy + 88), s_desc, font=f_c_sub, fill=(195, 206, 225, a))

    warped_cards = warp_plane_3d(plane, rx_deg=3.5, ry_deg=-8.0 + 3.0 * math.sin(age * 0.5), focal=2400.0)
    canvas.alpha_composite(warped_cards)

    # Climax Vertical Yellow-Gold Echo Repeat Stack in the last 3.2s of Scene 2
    if age >= dur - 3.2:
        c_age = age - (dur - 3.2)
        cp = expo_out(c_age / 0.55)
        f_big = get_font(JAKARTA_BOLD, 108)
        word = "206 SKILLS"
        d = ImageDraw.Draw(canvas)
        bb = d.textbbox((0, 0), word, font=f_big)
        cw = bb[2] - bb[0]
        cx = (W - cw) // 2
        cy_mid = 1480
        for k in range(-3, 4):
            if k == 0:
                continue
            ey = int(cy_mid + k * 115 * cp)
            ea = int(190 * (1.0 - abs(k) * 0.22) * cp)
            d.text((cx, ey), word, font=f_big, fill=(255, 220, 38, ea))
        d.text((cx + 3, cy_mid + 5), word, font=f_big, fill=(0, 0, 0, 220))
        d.text((cx, cy_mid), word, font=f_big, fill=(255, 255, 255, 255))
    else:
        draw_kinetic_lockup(canvas, age - 0.3, "installez vos skills dans", ".claude/skills", "206 moteurs 3D", cy=1490)

    return canvas


# ---------------------------------------------------------------------------
# Scene 3 (23.03s - 34.93s): Étape 2 — Analyse Whisper & Courbes MOTION-DESIGN.md
# ---------------------------------------------------------------------------
def render_scene3_analyse(t: float) -> Image.Image:
    age = t - 23.03
    canvas = Image.new("RGBA", (W, H), (8, 11, 18, 255))

    # Dual warm amber volumetric spotlights from top
    spot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spot)
    sd.polygon([(280, 140), (60, 1280), (520, 1280)], fill=(255, 186, 82, 52))
    sd.polygon([(800, 140), (560, 1280), (1020, 1280)], fill=(72, 162, 255, 52))
    spot = spot.filter(ImageFilter.GaussianBlur(radius=32))
    canvas.alpha_composite(spot)

    draw_step_badge(canvas, "ÉTAPE 02", "WHISPER JSON + MOTION-DESIGN.md", age, dark=True)

    d = ImageDraw.Draw(canvas)
    f_mono = get_font(MONO_MED, 24)
    f_bold = get_font(JAKARTA_BOLD, 34)

    # 1. Audio Waveform & Word-Level Timestamp Analyzer Box (y=210..640)
    bx0, by0, bx1, by1 = 76, 210, 1004, 630
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=22, fill=(14, 20, 32, 235), outline=(78, 148, 255, 210), width=2)
    d.text((bx0 + 32, by0 + 22), "ANALYSE AUDIO WHISPER (TIMESTAMPS AU 1/100s)", font=f_mono, fill=(135, 195, 255, 240))

    # Animated bars
    n_bars = 44
    for i in range(n_bars):
        bx = bx0 + 44 + i * 19
        h_bar = int(32 + 95 * abs(math.sin(i * 0.42 + age * 5.2)) * (0.4 + 0.6 * abs(math.cos(i * 0.18 - age * 2.1))))
        active_bar = (i / n_bars) <= ((age * 0.22) % 1.0)
        col = (255, 218, 44, 245) if active_bar else (68, 118, 188, 175)
        d.rounded_rectangle([bx, 415 - h_bar, bx + 11, 415 + h_bar], radius=4, fill=col)

    pills = [
        ("00.18s • micro", 110),
        ("00.30s • état", 335),
        ("00.48s • reveal", 555),
        ("00.72s • séquence", 785),
    ]
    for idx, (ptxt, px) in enumerate(pills):
        pp = expo_out((age - idx * 0.35) / 0.4)
        if pp > 0.02:
            d.rounded_rectangle([px, 535, px + 205, 592], radius=18, fill=(24, 34, 54, int(245 * pp)), outline=(255, 218, 44, int(225 * pp)), width=2)
            d.text((px + 18, 550), ptxt, font=f_mono, fill=(255, 232, 110, int(255 * pp)))

    # 2. Live Cubic-Bezier(0.2, 0.8, 0.2, 1.0) Interactive Graph (y=680..1290)
    gx0, gy0, gx1, gy1 = 76, 680, 1004, 1290
    d.rounded_rectangle([gx0, gy0, gx1, gy1], radius=22, fill=(14, 20, 32, 235), outline=(255, 212, 48, 210), width=2)
    d.text((gx0 + 32, gy0 + 22), "COURBE MAÎTRESSE : cubic-bezier(0.2, 0.8, 0.2, 1.0)", font=f_mono, fill=(255, 222, 68, 245))

    plot_x0, plot_y0, plot_w, plot_h = 160, 1210, 760, 420
    # Grid lines
    for k in range(5):
        yy = plot_y0 - int(plot_h * k / 4)
        d.line([(plot_x0, yy), (plot_x0 + plot_w, yy)], fill=(42, 58, 86, 160), width=1)
    # Bezier curve points
    pts = []
    prog_curve = clamp((age - 0.5) / 1.8)
    n_pts = max(2, int(80 * prog_curve))
    for i in range(n_pts + 1):
        u = (i / 80.0)
        v = cubic_bezier(u, 0.2, 0.8, 0.2, 1.0)
        pts.append((plot_x0 + int(u * plot_w), plot_y0 - int(v * plot_h)))
    if len(pts) >= 2:
        d.line(pts, fill=(255, 218, 44, 255), width=7)
        # Moving tracer dot
        u_cur = (age * 0.55) % 1.0
        v_cur = cubic_bezier(u_cur, 0.2, 0.8, 0.2, 1.0)
        cx_dot = plot_x0 + int(u_cur * plot_w)
        cy_dot = plot_y0 - int(v_cur * plot_h)
        d.ellipse([cx_dot - 14, cy_dot - 14, cx_dot + 14, cy_dot + 14], fill=(255, 255, 255, 255), outline=(255, 218, 44, 255), width=4)

    draw_kinetic_lockup(canvas, age - 0.3, "transcrit chaque mot et applique", "Motion Design", "au centième de seconde", cy=1490)
    return canvas


# ---------------------------------------------------------------------------
# Scene 4 (34.93s - 45.60s): Étape 3 — Téléchargement B-Roll & Découpes Papier
# ---------------------------------------------------------------------------
def render_scene4_broll(t: float) -> Image.Image:
    cache = get_cache()
    age = t - 34.93

    # Tactile Cream Drafting-Paper Canvas (#F7F0D8) matching reference9 & paper-cut-motion
    canvas = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(canvas)

    # Architectural drafting lines in gold & crimson
    d.line([(60, 180), (980, 180), (980, 1340), (120, 1340)], fill=(216, 162, 62, 220), width=4)
    d.line([(0, 1280), (420, 1140), (780, 1260), (1080, 1120)], fill=(212, 64, 44, 245), width=18)

    draw_step_badge(canvas, "ÉTAPE 03", "TÉLÉCHARGEMENT IMAGES & B-ROLL", age, dark=False)

    # 3 3D Media Cards (2 Frosted-Glass Live Video B-Roll Cards + 1 Paper-Cut Photo Evidence Card)
    plane = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plane)
    f_lbl = get_font(MONO_MED, 18)

    # Card 1: CAD Blueprint B-Roll Video (top-left)
    if age > 0.25:
        p1 = expo_out((age - 0.25) / 0.48)
        f_cad = cache["broll_cad"][int(age * FPS) % len(cache["broll_cad"])]
        x0, y0 = 76, int(235 + 45 * (1.0 - p1))
        pd.rounded_rectangle([x0, y0, x0 + 440, y0 + 286], radius=16, fill=(14, 18, 26, 245), outline=(68, 152, 255, 235), width=3)
        plane.alpha_composite(f_cad, (x0 + 10, y0 + 40))
        pd.ellipse([x0 + 18, y0 + 13, x0 + 30, y0 + 25], fill=(255, 72, 64, 255))
        pd.text((x0 + 40, y0 + 9), "B-ROLL MP4 // CAD PLAN", font=f_lbl, fill=(235, 242, 255, 255))

    # Card 2: Construction Site B-Roll Video (top-right)
    if age > 0.85:
        p2 = expo_out((age - 0.85) / 0.48)
        f_site = cache["broll_site"][int(age * FPS) % len(cache["broll_site"])]
        x0, y0 = 564, int(345 + 45 * (1.0 - p2))
        pd.rounded_rectangle([x0, y0, x0 + 440, y0 + 286], radius=16, fill=(14, 18, 26, 245), outline=(255, 198, 58, 235), width=3)
        plane.alpha_composite(f_site, (x0 + 10, y0 + 40))
        pd.ellipse([x0 + 18, y0 + 13, x0 + 30, y0 + 25], fill=(255, 72, 64, 255))
        pd.text((x0 + 40, y0 + 9), "B-ROLL MP4 // CHANTIER", font=f_lbl, fill=(235, 242, 255, 255))

    # Card 3: Paper-Cut 3D Architectural Scale Model Photo Card with Masking Tape (center-bottom)
    if age > 1.55:
        p3 = expo_out((age - 1.55) / 0.52)
        im_mod = cache["model_card"]
        x0, y0 = 280, int(710 + 50 * (1.0 - p3))
        # Contact shadow
        pd.rounded_rectangle([x0 + 12, y0 + 16, x0 + 452, y0 + 314], radius=12, fill=(20, 18, 14, 95))
        pd.rounded_rectangle([x0, y0, x0 + 440, y0 + 298], radius=10, fill=(254, 250, 242, 255), outline=(32, 30, 26, 240), width=3)
        plane.alpha_composite(im_mod, (x0 + 10, y0 + 40))
        # Masking tape strips at corners
        pd.polygon([(x0 - 16, y0 + 18), (x0 + 48, y0 - 10), (x0 + 54, y0 + 8), (x0 - 10, y0 + 36)], fill=(232, 212, 162, 235))
        pd.polygon([(x0 + 392, y0 - 10), (x0 + 456, y0 + 18), (x0 + 450, y0 + 36), (x0 + 386, y0 + 8)], fill=(232, 212, 162, 235))
        pd.text((x0 + 18, y0 + 10), "IMAGE SEARCH // PAPER-CUT 3D", font=f_lbl, fill=(28, 28, 30, 255))

    warped = warp_plane_3d(plane, rx_deg=4.5, ry_deg=-7.0 + 3.0 * math.sin(age * 0.6), focal=2300.0)
    canvas.alpha_composite(warped)

    # Dark bottom banner for glowing caption contrast on cream background
    d.rounded_rectangle([54, 1360, 1026, 1765], radius=28, fill=(14, 16, 22, 242))
    draw_kinetic_lockup(canvas, age - 0.3, "télécharge images et courtes vidéos", "B-Roll 4K", "en cartes 3D", cy=1515)
    return canvas


# ---------------------------------------------------------------------------
# Scene 5 (45.60s - 57.38s): Étape 4 — Motion Engine (Cut-the-Curve & Escalier 3D)
# ---------------------------------------------------------------------------
def render_scene5_transitions(t: float) -> Image.Image:
    cache = get_cache()
    age = t - 45.60
    canvas = Image.new("RGBA", (W, H), (12, 13, 17, 255))

    draw_step_badge(canvas, "ÉTAPE 04", "MOTEUR MOTION ENGINE & SEAMS", age, dark=True)

    # Upper Rounded Square Window playing the live edited speaker with Golden Halftone & Subject-Occluded Watermark
    head_frames = cache["ref10_head"]
    h_im = head_frames[int(age * FPS) % len(head_frames)]
    win_w, win_h = 720, 620
    win_x, win_y = (W - win_w) // 2, 165
    mask = Image.new("L", (win_w, win_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, win_w - 1, win_h - 1], radius=44, fill=255)
    win_card = Image.new("RGBA", (win_w, win_h), (0, 0, 0, 0))
    win_card.paste(h_im.resize((win_w, win_h), Image.BILINEAR), (0, 0), mask)
    canvas.alpha_composite(win_card, (win_x, win_y))

    # Below window: 3D Winding White Architectural Staircase (matching reference 10.mp4)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n_steps = 22
    build_p = expo_out(age / 0.85)
    vis_steps = int(round(n_steps * build_p))
    pts = []
    for i in range(n_steps):
        u = i / float(n_steps - 1)
        cx = 230 + 480 * u + 195 * math.sin(u * math.pi * 1.85 - 0.35)
        cy = 1740 - 845 * (u ** 0.92)
        ws = int(round(135 * (1.0 - 0.32 * u)))
        pts.append((cx, cy, ws))

    for i in range(vis_steps):
        cx, cy, ws = pts[i]
        x0, x1, y0 = int(cx - ws), int(cx + ws), int(cy)
        d.rectangle([x0, y0, x1, y0 + 38], fill=(58, 62, 70, 245), outline=(115, 120, 130, 255), width=1)
        d.polygon([(x0, y0), (x1, y0), (x1 + 10, y0 - 18), (x0 + 10, y0 - 18)], fill=(235, 238, 245, 255), outline=(150, 155, 165, 255))

    if build_p > 0.2:
        fx, fy = int(pts[1][0] - 42), int(pts[1][1] - 12)
        d.ellipse([fx - 12, fy - 128, fx + 12, fy - 104], fill=(230, 234, 242, 255))
        d.polygon([(fx - 18, fy - 100), (fx + 18, fy - 100), (fx + 22, fy - 44), (fx - 22, fy - 44)], fill=(170, 175, 185, 255))
        d.line([(fx - 8, fy - 44), (fx - 14, fy)], fill=(215, 220, 228, 255), width=8)
        d.line([(fx + 8, fy - 44), (fx + 16, fy - 12)], fill=(215, 220, 228, 255), width=8)
        f_bot = get_font(INTER_MED, 40)
        d.text((fx - 55, fy - 220), "vidéo brute", font=f_bot, fill=(210, 215, 225, 255))

    canvas.alpha_composite(layer)

    draw_kinetic_lockup(canvas, age - 0.3, "transitions à vélocité continue", "Cut the Curve", "Zoom Through", cy=875)
    return canvas


# ---------------------------------------------------------------------------
# Scene 6 (57.38s - 69.03s): Étape 5 — Export Master 9:16 (1080x1920 30fps)
# ---------------------------------------------------------------------------
def render_scene6_outro(t: float) -> Image.Image:
    cache = get_cache()
    age = t - 57.38

    bg = cache["shard"].crop((0, 0, W, H)).copy()
    scrim = Image.new("RGBA", (W, H), (8, 12, 20, 165))
    bg.alpha_composite(scrim)

    # Giant Vertical Stacked Letters "C-L-A-U-D-E" on the left edge (matching L-O-N-D-O-N in ref10)
    word = "CLAUDE"
    step_h = (H - 120) // len(word)
    f_vert = get_font(JAKARTA_BOLD, 255)
    td = ImageDraw.Draw(bg)
    for idx, ch_str in enumerate(word):
        cp = expo_out((age - idx * 0.06) / 0.45)
        if cp <= 0.01:
            continue
        lx = int(24 - 210 * (1.0 - cp))
        ly = 40 + idx * step_h - 30
        col = (34, 152, 236, int(248 * cp)) if idx < 3 else (232, 96, 36, int(248 * cp))
        td.text((lx + 5, ly + 7), ch_str, font=f_vert, fill=(0, 0, 0, int(165 * cp)))
        td.text((lx, ly), ch_str, font=f_vert, fill=col)

    draw_step_badge(bg, "ÉTAPE 05", "EXPORT MASTER 9:16 (1080x1920)", age, dark=True)

    # Two 3D Tilted Smartphone Showcase Frames playing our finished edits (ref9 & ref10)
    f9 = cache["ref9_clip"][int(age * FPS) % len(cache["ref9_clip"])]
    f10 = cache["ref10_clip"][int(age * FPS) % len(cache["ref10_clip"])]

    phones = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(phones)
    f_tag = get_font(MONO_MED, 20)

    # Left phone (felix-gray-reference9)
    pd.rounded_rectangle([245, 255, 625, 965], radius=32, fill=(12, 14, 20, 250), outline=(88, 165, 255, 240), width=4)
    phones.alpha_composite(f9.resize((360, 640), Image.BILINEAR), (255, 305))
    pd.text((285, 268), "MONTAGE 3D // REF 09", font=f_tag, fill=(155, 205, 255, 255))

    # Right phone (felix-gray-reference10)
    pd.rounded_rectangle([655, 345, 1035, 1055], radius=32, fill=(12, 14, 20, 250), outline=(255, 218, 44, 240), width=4)
    phones.alpha_composite(f10.resize((360, 640), Image.BILINEAR), (665, 395))
    pd.text((695, 358), "OUR WORK // REF 10", font=f_tag, fill=(255, 226, 68, 255))

    warped_phones = warp_plane_3d(phones, rx_deg=4.0, ry_deg=-9.5 + 3.0 * math.sin(age * 0.6), focal=2300.0)
    bg.alpha_composite(warped_phones)

    draw_kinetic_lockup(bg, age - 0.25, "exportez en haute définition pour", "Reels & Shorts", "1080x1920 30fps", cy=1460)
    return bg


# ---------------------------------------------------------------------------
# Master Scene Dispatcher + Velocity-Matched Seams (`motion_engine.py`)
# ---------------------------------------------------------------------------
def _render_scene_at(t: float) -> Image.Image:
    if t < 8.45:
        return render_scene1_hook(t)
    if t < 23.03:
        return render_scene2_skills(t)
    if t < 34.93:
        return render_scene3_analyse(t)
    if t < 45.60:
        return render_scene4_broll(t)
    if t < 57.38:
        return render_scene5_transitions(t)
    return render_scene6_outro(t)


SEAMS = [
    (8.45, 0.36, "zoom_in"),
    (23.03, 0.36, "inverse_zoom"),
    (34.93, 0.34, "cut_left"),
    (45.60, 0.34, "rack_focus"),
    (57.38, 0.36, "zoom_in"),
]


def render_frame(t: float) -> np.ndarray:
    for cut_t, width_s, kind in SEAMS:
        t0, t1 = cut_t - width_s * 0.40, cut_t + width_s * 0.60
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            old_im = _render_scene_at(cut_t - 0.04)
            new_im = _render_scene_at(max(cut_t + 0.02, t))
            if kind == "zoom_in":
                out = zoom_through_seam(old_im, new_im, p, inverse=False)
            elif kind == "inverse_zoom":
                out = zoom_through_seam(old_im, new_im, p, inverse=True)
            elif kind == "cut_left":
                out = cut_the_curve_seam(old_im, new_im, p, direction="left")
            else:
                out = rack_focus_blur_cut(old_im, new_im, p)
            return np.array(out.convert("RGB"))

    out = _render_scene_at(t)
    return np.array(out.convert("RGB"))


def build_preview_grid(out_jpg_path: str):
    preview_times = [
        1.20, 3.50, 6.20, 8.45,
        10.50, 14.50, 18.20, 21.50,
        24.80, 28.50, 32.50, 34.93,
        37.20, 40.50, 43.80, 45.60,
        48.20, 52.00, 55.50, 57.38,
        59.50, 62.50, 65.50, 67.80,
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
        if f_idx % 240 == 0 or f_idx == TOTAL_FRAMES - 1:
            print(f"Rendered frame {f_idx + 1}/{TOTAL_FRAMES} ({t:.2f}s / {DURATION:.2f}s)")
            sys.stdout.flush()

    enc_proc.stdin.close()
    enc_proc.wait()
    if enc_proc.returncode != 0:
        raise RuntimeError(f"FFmpeg encode failed with code {enc_proc.returncode}")
    print(f"Successfully rendered {out_mp4_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="/home/user/COOL-backup/claude-code-montage-video/assets/audio/master_voiceover_mix.wav")
    parser.add_argument(
        "--out",
        default="/home/user/COOL-backup/claude-code-montage-video/film/comment-utiliser-claude-code-montage-video-9x16.mp4",
    )
    parser.add_argument("--preview", default="")
    args = parser.parse_args()

    if args.preview:
        build_preview_grid(args.preview)
    else:
        render_full_video(args.audio, args.out)
