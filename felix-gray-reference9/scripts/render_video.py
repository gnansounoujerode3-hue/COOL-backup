#!/usr/bin/env python3
"""
Renders `felix-gray-reference9-9x16.mp4` (1080x1920, 30.00 fps, 54.85s) from
`video brut 9.mp4`, faithfully translating every visual signature of `reference9.mp4`:
  1. 3D Z-Space Dark Blueprint & Node Canvas (receding 3D typography, blue icon pills,
     golden contour lines, and cobalt blueprint CRT flash).
  2. Technical Viewfinder HUD Border Overlay (`45 + G`, diagonal hatch ticks `/////////`,
     vertical rotated code `456 JK / 789 0`, registration hairlines).
  3. Dark HUD Viewfinder Spotlight Cutaway (`from day one` / `dragged onto building sites.`).
  4. Cream Architectural Drafting-Paper Cutaways (`#F7F0D8`) with Terracotta (`#D8432E`)
     & Ochre (`#D9A441`) contour lines, Central Black Circular Portal with 3 tilted
     Sky-Blue (`#4294FF`) pills, and sliding dark geometric silhouettes.
  5. Dark Technical Grid + Translucent Blue UI Text-Selection Box (`|o ... o|`) +
     Floating Wireframe Arrow Cursors (`↖`) + Italic Electric-Blue Condensed Stamps.
  6. Talking-Head Lower-Case Tight-Tracked Chest Subtitles with progressive word opacity
     + Royal-Blue & Crimson-Amber vertical anamorphic light leaks.
  7. Pull-Back Floating Video Window on Pitch Black + Giant Metallic Ice-Blue Chrome
     `"14"` / `"ARCHITECT"` Lockup (`48.95–51.80s`), followed by HUD-framed
     `peakarchitects` studio blueprint B-roll (`51.80–54.85s`).
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

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
MONTSERRAT_BLACK_IT = f"{FONT_BASE}/montserrat/900Black_Italic/Montserrat_900Black_Italic.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"

_FONT_CACHE = {}


def get_font(path: str, size: int):
    sz = max(12, int(size))
    key = (path, sz)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, sz)
    return _FONT_CACHE[key]


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out_cubic(x):
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def ease_out_back(x, s=1.45):
    x = clamp(x) - 1.0
    return x * x * ((s + 1.0) * x + s) + 1.0


def ease_in_out_cubic(x):
    x = clamp(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# ---------------------------------------------------------------------------
# Color Grade & Anamorphic Light Leaks on Talking Head
# ---------------------------------------------------------------------------
def grade_talking_head(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    """Crisp editorial contrast grade + subtle vignette matching reference9.mp4."""
    f = frame_rgb.astype(np.float32) / 255.0
    # Slight S-curve contrast & clean neutral-warm skin tones
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
        # Left vertical anamorphic royal-blue glow (like t=18.2s & t=25.3s in reference9.mp4)
        wx = np.exp(-((xx / W) ** 2) / (2 * 0.22 ** 2))
        wy = np.exp(-(((yy / H) - 0.45) ** 2) / (2 * 0.48 ** 2))
        w_blue = (wx * wy)[:, :, None]
        blue_col = np.array([36.0, 92.0, 255.0], dtype=np.float32)[None, None, :]
        _LIGHT_LEAK_BLUE = w_blue * blue_col

        # Warm crimson-amber flash glow (like t=18.1s in reference9.mp4)
        wx_r = np.exp(-((xx / W) ** 2) / (2 * 0.30 ** 2))
        wy_r = np.exp(-(((yy / H) - 0.50) ** 2) / (2 * 0.50 ** 2))
        w_red = (wx_r * wy_r)[:, :, None]
        red_col = np.array([235.0, 48.0, 38.0], dtype=np.float32)[None, None, :]
        _LIGHT_LEAK_RED = w_red * red_col
    return _LIGHT_LEAK_BLUE, _LIGHT_LEAK_RED


def apply_light_leak(frame_rgb: np.ndarray, t: float) -> np.ndarray:
    blue_leak, red_leak = get_light_leaks()
    out = frame_rgb.astype(np.float32)

    # Royal-blue light leak windows (matching t=18.2s, 25.3s in reference9.mp4)
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

    # Crimson-amber flash transitions (matching t=18.0-18.15s in reference9.mp4)
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
# Signature Element #2: Technical Viewfinder / Film-HUD Overlay
# ---------------------------------------------------------------------------
_HUD_DARK_CACHE = None
_HUD_LIGHT_CACHE = None


def get_hud_overlay(mode: str = "dark") -> Image.Image:
    """
    Builds the exact technical viewfinder HUD border from reference9.mp4:
      - Vertical registration hairlines at x=52 and x=1028
      - Top-left '45 + G' micro-marker
      - Top-right diagonal hatch ticks '/////////'
      - Right-edge vertical code '456 JK / 789 0'
      - Left-edge tick marks
    """
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

    # Left & Right vertical registration hairlines
    d.line([(52, 80), (52, 920)], fill=col_dim, width=2)
    d.line([(52, 1340), (52, 1840)], fill=col_dim, width=2)
    d.line([(1028, 80), (1028, 390)], fill=col_dim, width=2)
    d.line([(1028, 600), (1028, 960)], fill=col_dim, width=2)
    d.line([(1028, 1240), (1028, 1840)], fill=col_dim, width=2)

    # Top-left vertical micro-label "45 + G"
    lbl_tl = Image.new("RGBA", (140, 40), (0, 0, 0, 0))
    dtl = ImageDraw.Draw(lbl_tl)
    dtl.text((0, 6), "45  +  G", font=f_mono, fill=col_main)
    lbl_tl_rot = lbl_tl.rotate(-90, expand=True)
    img.alpha_composite(lbl_tl_rot, (28, 96))

    # Top-right diagonal hatch ticks (/////////)
    for i in range(11):
        yy = 415 + i * 14
        d.line([(1020, yy + 6), (1036, yy - 6)], fill=col_main, width=2)

    # Right-edge rotated micro-code "456 JK / 789 0"
    lbl_r = Image.new("RGBA", (220, 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lbl_r)
    dr.text((0, 6), "456 JK  /  789 0", font=f_mono, fill=col_main)
    lbl_r_rot = lbl_r.rotate(-90, expand=True)
    img.alpha_composite(lbl_r_rot, (1006, 995))

    # Left-edge vertical tick ruler (y = 970..1280)
    for i in range(13):
        yy = 980 + i * 22
        w_tick = 12 if i % 3 == 0 else 6
        d.line([(46, yy), (46 + w_tick, yy)], fill=col_main, width=2)

    # Small corner registration dots
    for cx, cy in [(86, 52), (994, 52), (86, 1868), (994, 1868)]:
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=col_main)

    if mode == "dark":
        _HUD_DARK_CACHE = img
    else:
        _HUD_LIGHT_CACHE = img
    return img


# ---------------------------------------------------------------------------
# Signature Element #1: 3D Z-Space Dark Blueprint & Node Canvas (0.00s - 5.65s)
# ---------------------------------------------------------------------------
def render_zspace_opening(t: float) -> Image.Image:
    """
    Reproduces t=0.00s–4.00s of reference9.mp4:
      - Pitch-black canvas (#030408) with subtle technical blueprint grid
      - Sweeping golden-ochre contour curve (#A67B38)
      - Floating dark-glass pills with glowing royal-blue circular icons (#2460FF)
      - 4 sequential kinetic phrases that pop in the foreground and recede into 3D Z-depth
      - Brief cobalt-blue blueprint CRT scanline flash at 5.25s–5.65s
    """
    img = Image.new("RGBA", (W, H), (3, 4, 8, 255))
    d = ImageDraw.Draw(img)

    # Camera Z-progress as phrases accumulate
    cam_z = (
        ease_out_cubic((t - 0.54) / 0.55) * 1.0
        + ease_out_cubic((t - 1.58) / 0.55) * 1.0
        + ease_out_cubic((t - 3.65) / 0.55) * 1.0
    )

    # 1. Background technical blueprint grid on the right half (matching t=1.4s, 2.2s, 3.6s)
    grid_shift_x = int(-cam_z * 28)
    grid_shift_y = int(cam_z * 22)
    grid_col = (24, 38, 66, 95)
    for gx in range(520 + grid_shift_x, W + 120, 72):
        d.line([(gx, 180), (gx, 1740)], fill=grid_col, width=1)
    for gy in range(260 + grid_shift_y, 1680, 72):
        d.line([(480, gy), (W, gy)], fill=grid_col, width=1)
    # Crosshair nodes on the blueprint grid
    for gx in range(592 + grid_shift_x, W, 144):
        for gy in range(332 + grid_shift_y, 1600, 144):
            d.line([(gx - 6, gy), (gx + 6, gy)], fill=(48, 76, 130, 140), width=2)
            d.line([(gx, gy - 6), (gx, gy + 6)], fill=(48, 76, 130, 140), width=2)

    # 2. Sweeping golden-ochre architectural contour curve (matching t=2.2s & t=3.6s)
    if t >= 0.90:
        curve_alpha = int(clamp((t - 0.90) / 0.60) * 195)
        pts = []
        for idx in range(60):
            u = idx / 59.0
            py = int(80 + u * 1760)
            px = int(
                640
                + 240 * math.sin(u * 3.6 - cam_z * 0.45)
                + 85 * math.cos(u * 7.2)
            )
            pts.append((px, py))
        d.line(pts, fill=(168, 124, 54, curve_alpha), width=5)

    # 3. Floating dark-glass notification pills with royal-blue icon circles
    pills = [
        # (t_appear, base_x, base_y, base_z, label, icon_char)
        (0.10, 140, 1020, 0.2, "Site Blueprint CAD", "📐"),
        (1.05, 760, 1280, 1.0, "Hey, I'm an architect...", "✎"),
        (1.85, 680, 620, 1.8, "Structural Studio", "🏛"),
        (2.70, 260, 880, 2.3, "Technical College", "✓"),
    ]
    for t_app, bx, by, bz, label, _ in pills:
        if t < t_app:
            continue
        age = t - t_app
        pop = ease_out_back(age / 0.35)
        rel_z = max(0.0, cam_z - bz * 0.55)
        scale = clamp(pop * (1.0 / (1.0 + rel_z * 0.42)), 0.35, 1.15)
        alpha = int(clamp(age / 0.20) * clamp(1.0 - rel_z * 0.28, 0.25, 0.92) * 255)

        pw, ph = int(340 * scale), int(76 * scale)
        px = int(bx + (W * 0.52 - bx) * (1.0 - 1.0 / (1.0 + rel_z * 0.35)))
        py = int(by + (H * 0.46 - by) * (1.0 - 1.0 / (1.0 + rel_z * 0.35)))

        pill_layer = Image.new("RGBA", (pw + 20, ph + 20), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_layer)
        # Dark glass pill body
        pd.rounded_rectangle(
            [6, 6, pw + 6, ph + 6],
            radius=ph // 2,
            fill=(14, 20, 34, int(alpha * 0.85)),
            outline=(45, 75, 140, int(alpha * 0.7)),
            width=max(1, int(2 * scale)),
        )
        # Glowing royal-blue circle on the left
        r_cir = int(ph * 0.38)
        cx_c, cy_c = 6 + int(ph * 0.52), 6 + ph // 2
        pd.ellipse(
            [cx_c - r_cir, cy_c - r_cir, cx_c + r_cir, cy_c + r_cir],
            fill=(36, 98, 255, alpha),
        )
        # Small white checkmark/triangle inside blue circle
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
            fill=(180, 198, 230, int(alpha * 0.9)),
        )
        if rel_z > 0.6:
            pill_layer = pill_layer.filter(ImageFilter.GaussianBlur(radius=min(3.5, rel_z * 1.4)))
        img.alpha_composite(pill_layer, (px - pw // 2, py - ph // 2))

    # 4. 3D Z-Space Kinetic Phrases (foreground crisp -> recedes into Z-depth as next phrase pops)
    phrases = [
        # (t_in, z_idx, target_x, target_y, vx, vy, lines, align)
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
        pop = ease_out_back(min(1.0, age / 0.28), s=1.25)
        depth_behind = max(0.0, cam_z - z_idx)
        scale = pop * (1.0 / (1.0 + depth_behind * 0.62))
        alpha = int(clamp(age / 0.14) * clamp(1.0 - depth_behind * 0.36, 0.20, 1.0) * 255)

        # Pull receding text smoothly toward its spatial Z-pocket
        z_pull = 1.0 - 1.0 / (1.0 + depth_behind * 0.55)
        cx = int(tx + (vx - tx) * z_pull)
        cy = int(ty + (vy - ty) * z_pull)

        layer = Image.new("RGBA", (820, 360), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cur_y = 40
        for txt, base_sz, f_path in lines:
            sz = max(14, int(base_sz * scale))
            fnt = get_font(f_path, sz)
            bbox = ld.textbbox((0, 0), txt, font=fnt)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            lx = (820 - tw) // 2 if align == "center" else 90
            # Warm ivory-white text (#F8F4E8) matching reference9.mp4
            ld.text((lx, cur_y), txt, font=fnt, fill=(248, 244, 232, alpha))
            cur_y += int(sz * 1.04)

        # Add soft warm halation glow on foreground phrase
        if depth_behind < 0.35:
            glow = layer.filter(ImageFilter.GaussianBlur(radius=8))
            img.alpha_composite(glow, (cx - 410, cy - 140))
        elif depth_behind > 0.65:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=min(3.0, depth_behind * 1.2)))

        img.alpha_composite(layer, (cx - 410, cy - 140))

    # 5. Cobalt-blue CRT / blueprint scanline flash at 5.25s - 5.65s (matching t=3.70s in reference9.mp4)
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
# Cutaway #2 (8.30s - 10.75s): Dark HUD Viewfinder Spotlight Cutaway
# (Directly inspired by t=4.30s - 6.20s "in 2025 / cold outreach is dead")
# ---------------------------------------------------------------------------
def render_dark_spotlight_hud(t: float) -> Image.Image:
    """
    Reproduces t=4.30s–6.20s of reference9.mp4:
      - Atmospheric dark teal-black architectural night canvas
      - Glowing twin warm tungsten spotlight beams in the center (y=940)
      - Technical Viewfinder HUD border ('45 + G', '/////////', '456 JK / 789 0')
      - Top-left 'from day one' + lower spatial reveal 'dragged onto' / 'building sites.'
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Deep atmospheric teal-black background gradient
    r_ch = np.clip(6.0 + 18.0 * np.exp(-(((yy - 940) / 380) ** 2)), 0, 255)
    g_ch = np.clip(14.0 + 36.0 * np.exp(-(((yy - 940) / 420) ** 2)), 0, 255)
    b_ch = np.clip(22.0 + 48.0 * np.exp(-(((yy - 940) / 460) ** 2)), 0, 255)

    # Twin warm amber spotlight cores at center (matching the twin glowing lights at t=5.40s)
    for lx in (495.0, 585.0):
        d2 = ((xx - lx) / 36.0) ** 2 + ((yy - 920.0) / 26.0) ** 2
        glow = np.exp(-d2 * 0.5)
        halo = np.exp(-(((xx - lx) / 160.0) ** 2 + ((yy - 920.0) / 95.0) ** 2) * 0.5)
        r_ch += glow * 245.0 + halo * 85.0
        g_ch += glow * 195.0 + halo * 58.0
        b_ch += glow * 130.0 + halo * 28.0

    # Subtle horizon reflection line at y=1320
    refl = np.exp(-(((yy - 1320.0) / 22.0) ** 2)) * np.exp(-(((xx - 540.0) / 340.0) ** 2))
    r_ch += refl * 35.0
    g_ch += refl * 65.0
    b_ch += refl * 95.0

    arr = np.stack([np.clip(r_ch, 0, 255), np.clip(g_ch, 0, 255), np.clip(b_ch, 0, 255)], axis=-1).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGBA")
    d = ImageDraw.Draw(img)

    # Technical HUD overlay
    img.alpha_composite(get_hud_overlay("dark"))

    # Top-left caption "from day one" (matching "in 2025" at t=5.40s)
    if t >= 8.38:
        a1 = int(clamp((t - 8.38) / 0.25) * 235)
        f_top = get_font(INTER_REG, 64)
        d.text((235, 510), "from day one", font=f_top, fill=(215, 228, 238, a1))

    # Lower spatial words: "dragged" (8.95s) -> "onto" (9.35s) -> "building sites." (9.75s)
    if t >= 8.95:
        a2 = int(clamp((t - 8.95) / 0.22) * 255)
        f_w1 = get_font(INTER_MED, 74)
        d.text((545, 1065), "dragged", font=f_w1, fill=(248, 244, 232, a2))

    if t >= 9.35:
        a3 = int(clamp((t - 9.35) / 0.22) * 240)
        f_w2 = get_font(INTER_REG, 66)
        d.text((310, 1145), "onto", font=f_w2, fill=(232, 228, 218, a3))

    if t >= 9.75:
        a4 = int(clamp((t - 9.75) / 0.24) * 255)
        f_w3 = get_font(INTER_BOLD, 78)
        d.text((310, 1225), "building sites.", font=f_w3, fill=(252, 248, 238, a4))

    return img


# ---------------------------------------------------------------------------
# Signature Element #4: Cream Drafting-Paper Cutaway #1 with Terracotta Contours,
# Central Black Portal & 3 Stacked Sky-Blue Pills (10.75s - 14.10s)
# (Exact replica of t=11.40s - 14.20s in reference9.mp4)
# ---------------------------------------------------------------------------
def render_cream_portal_pills(t: float) -> Image.Image:
    """
    Reproduces t=11.40s–14.20s of reference9.mp4:
      - Warm cream drafting-paper canvas (#F7F0D8)
      - Dark charcoal Technical Viewfinder HUD border
      - Bold terracotta-red (#D8432E) and ochre-gold (#D9A441) angular contour lines
      - Central deep-black circular portal (r=280)
      - 3 tilted (-2.2°) sky-blue (#4294FF) rounded pills popping in sequentially:
          1. 'When I was young' (11.00s)
          2. 'Kicking my heels...' (12.20s)
          3. 'During summer holidays!' (13.05s)
    """
    img = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(img)

    # Subtle top-left dark header bar like reference9.mp4 (t=12.2s, 13.5s)
    d.rectangle([0, 0, 390, 68], fill=(10, 10, 12, 255))

    # Ochre-gold thin contour line (#D9A441)
    gold_pts = [(0, 420), (145, 510), (95, 760), (210, 1180), (0, 1480)]
    d.line(gold_pts, fill=(217, 164, 65, 220), width=4)

    # Terracotta-red bold angular contour lines (#D8432E) at upper-left & lower-right
    red_tl = [(265, 68), (235, 195), (165, 290), (138, 430), (65, 545), (48, 720), (0, 795)]
    d.line(red_tl, fill=(216, 67, 46, 255), width=20, joint="curve")

    red_br = [(1080, 1320), (960, 1490), (885, 1560), (745, 1690), (540, 1850), (465, 1920)]
    d.line(red_br, fill=(216, 67, 46, 255), width=32, joint="curve")

    # Technical HUD overlay in dark charcoal
    img.alpha_composite(get_hud_overlay("light"))

    # Central deep-black circular portal (matching t=12.2s & t=13.5s)
    pop_portal = ease_out_back(min(1.0, (t - 10.75) / 0.32), s=1.15)
    r_p = int(282 * pop_portal)
    cx, cy = 540, 1020
    # Inner teal-blue subtle rim inside black circle
    d.ellipse([cx - r_p, cy - r_p, cx + r_p, cy + r_p], fill=(6, 10, 16, 255))
    d.ellipse(
        [cx - r_p + 6, cy - r_p + 6, cx + r_p - 6, cy + r_p - 6],
        outline=(28, 56, 88, 120),
        width=4,
    )

    # 3 stacked sky-blue rounded pills (#4294FF)
    pills_spec = [
        # (t_in, y_off, w_pill, h_pill, text, font_sz)
        (11.00, -118, 390, 74, "When I was young", 34),
        (12.20, -24, 420, 78, "Kicking my heels...", 36),
        (13.05, 92, 600, 134, "During summer\nholidays!", 48),
    ]
    for idx, (t_in, y_off, pw, ph, txt, fsz) in enumerate(pills_spec):
        if t < t_in:
            continue
        p_age = t - t_in
        s_pill = ease_out_back(min(1.0, p_age / 0.28), s=1.35)
        cw, ch = int(pw * s_pill), int(ph * s_pill)
        if cw < 20 or ch < 20:
            continue

        pill_img = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill_img)
        # Drop shadow
        pd.rounded_rectangle(
            [20, 26, 20 + cw, 26 + ch],
            radius=min(38, ch // 2),
            fill=(0, 0, 0, 135),
        )
        # Sky-blue pill body (#4294FF) with subtle lighter top border
        pd.rounded_rectangle(
            [18, 18, 18 + cw, 18 + ch],
            radius=min(38, ch // 2),
            fill=(66, 148, 255, 255),
            outline=(135, 192, 255, 220),
            width=2,
        )
        f_p = get_font(INTER_MED, max(12, int(fsz * s_pill)))
        lines = txt.split("\n")
        total_h = len(lines) * int(fsz * s_pill * 1.12)
        cur_y = 18 + (ch - total_h) // 2 - int(4 * s_pill)
        for line in lines:
            bb = pd.textbbox((0, 0), line, font=f_p)
            tw = bb[2] - bb[0]
            tx = 18 + (cw - tw) // 2
            pd.text((tx, cur_y), line, font=f_p, fill=(255, 255, 255, 255))
            cur_y += int(fsz * s_pill * 1.12)

        # Tilt by -2.2 degrees just like t=13.50s in reference9.mp4
        pill_rot = pill_img.rotate(2.2 if idx % 2 == 0 else -1.8, resample=Image.BICUBIC, expand=True)
        px = cx - pill_rot.width // 2 + (-22 if idx == 0 else (28 if idx == 1 else -8))
        py = cy + y_off - pill_rot.height // 2
        img.alpha_composite(pill_rot, (px, py))

    return img


# ---------------------------------------------------------------------------
# Signature Element #3: Dark Technical Grid + UI Selection Box + Wireframe Cursors
# & Italic Electric-Blue Condensed Stamp (17.30s - 20.55s and 35.30s - 38.45s)
# (Exact replica of t=8.00s - 11.20s in reference9.mp4)
# ---------------------------------------------------------------------------
def draw_wireframe_cursor(canvas: Image.Image, cx: int, cy: int, angle_deg: float, scale: float = 1.0):
    """Draws the crisp white wireframe arrow cursor from t=8.60s of reference9.mp4."""
    size = int(110 * scale)
    c_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(c_img)
    # Classic pointer polygon centered near top-left
    pts = [
        (24, 16),
        (24, 82),
        (42, 66),
        (56, 94),
        (68, 88),
        (54, 60),
        (78, 58),
    ]
    pts_scaled = [(int(x * scale), int(y * scale)) for x, y in pts]
    cd.polygon(pts_scaled, fill=(12, 16, 22, 180), outline=(238, 242, 250, 235), width=3)
    rot = c_img.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(rot, (cx - rot.width // 2, cy - rot.height // 2))


def render_dark_selection_and_stamp(
    t: float,
    t_start: float,
    t_mid: float,
    t_end: float,
    sel_top_text: str,
    sel_bot_text: str,
    stamp_top_text: str,
    stamp_blue_word: str,
) -> Image.Image:
    """
    Reproduces t=8.00s–11.20s of reference9.mp4:
      - Phase A (t_start .. t_mid): Translucent blue UI text-selection box (`|o ... o|`)
        around `sel_top_text` + bold white `sel_bot_text` underneath + floating wireframe
        arrow cursors + warm tungsten upper-right lens flare.
      - Phase B (t_mid .. t_end): Technical wireframe bounding box + sweeping red/ochre
        contour path + `stamp_top_text` above bold condensed italic electric-blue `stamp_blue_word`.
    """
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r_ch = np.full((H, W), 5.0, dtype=np.float32)
    g_ch = np.full((H, W), 7.0, dtype=np.float32)
    b_ch = np.full((H, W), 12.0, dtype=np.float32)

    # Warm tungsten horizontal lens flare at upper-right (matching t=8.60s & t=10.80s)
    flare_core = np.exp(-(((xx - 980.0) / 140.0) ** 2 + ((yy - 560.0) / 38.0) ** 2) * 0.5)
    flare_streak = np.exp(-(((yy - 560.0) / 14.0) ** 2)) * np.exp(-(((xx - 720.0) / 480.0) ** 2))
    flare_left = np.exp(-(((xx - 160.0) / 220.0) ** 2 + ((yy - 650.0) / 120.0) ** 2) * 0.5)
    r_ch += flare_core * 250.0 + flare_streak * 185.0 + flare_left * 75.0
    g_ch += flare_core * 175.0 + flare_streak * 95.0 + flare_left * 32.0
    b_ch += flare_core * 95.0 + flare_streak * 35.0 + flare_left * 18.0

    # Soft center ambient glow behind typography
    c_glow = np.exp(-(((xx - 540.0) / 260.0) ** 2 + ((yy - 950.0) / 190.0) ** 2) * 0.5)
    r_ch += c_glow * 36.0
    g_ch += c_glow * 42.0
    b_ch += c_glow * 58.0

    arr = np.stack([np.clip(r_ch, 0, 255), np.clip(g_ch, 0, 255), np.clip(b_ch, 0, 255)], axis=-1).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGBA")
    d = ImageDraw.Draw(img)

    # Technical HUD overlay
    img.alpha_composite(get_hud_overlay("dark"))

    if t < t_mid:
        # ---------------- PHASE A: Blue UI Text-Selection Box + Floating Cursors ----------------
        age = t - t_start
        sel_p = ease_out_cubic(min(1.0, age / 0.38))

        f_top = get_font(INTER_REG, 68)
        f_bot = get_font(INTER_BOLD, 86)

        bb_top = d.textbbox((0, 0), sel_top_text, font=f_top)
        tw_top, th_top = bb_top[2] - bb_top[0], bb_top[3] - bb_top[1]
        tx_top = (W - tw_top) // 2
        ty_top = 845

        # Translucent blue UI selection highlight rectangle + left/right handle pins
        cur_w = int((tw_top + 28) * sel_p)
        bx0 = tx_top - 14
        by0 = ty_top - 4
        bx1 = bx0 + cur_w
        by1 = ty_top + th_top + 18

        d.rectangle([bx0, by0, bx1, by1], fill=(42, 118, 255, 108))
        # Left selection handle (vertical bar + top circle pin)
        d.line([(bx0, by0), (bx0, by1)], fill=(66, 148, 255, 255), width=4)
        d.ellipse([bx0 - 8, by0 - 14, bx0 + 8, by0 + 2], fill=(66, 148, 255, 255))
        # Right selection handle (vertical bar + bottom circle pin)
        d.line([(bx1, by0), (bx1, by1)], fill=(66, 148, 255, 255), width=4)
        d.ellipse([bx1 - 8, by1 - 2, bx1 + 8, by1 + 14], fill=(66, 148, 255, 255))

        # Top text & bottom bold text
        d.text((tx_top, ty_top), sel_top_text, font=f_top, fill=(246, 244, 236, 255))

        if age >= 0.16:
            bot_p = ease_out_back(min(1.0, (age - 0.16) / 0.28), s=1.2)
            bb_bot = d.textbbox((0, 0), sel_bot_text, font=f_bot)
            tw_bot = bb_bot[2] - bb_bot[0]
            tx_bot = (W - tw_bot) // 2
            ty_bot = int(930 + (1.0 - bot_p) * 24)
            d.text((tx_bot, ty_bot), sel_bot_text, font=f_bot, fill=(252, 250, 242, int(clamp((age - 0.16) / 0.18) * 255)))

        # Floating white wireframe arrow cursors (matching t=8.60s in reference9.mp4)
        drift = age * 28.0
        draw_wireframe_cursor(img, int(395 + drift * 0.6), int(1465 - drift), angle_deg=-24, scale=1.05)
        draw_wireframe_cursor(img, int(890 - drift * 0.5), int(430 + drift * 0.8), angle_deg=155, scale=0.95)
    else:
        # ---------------- PHASE B: Technical Bounding Box + Red Contour + Italic Blue Stamp ----------------
        age = t - t_mid
        pop = ease_out_back(min(1.0, age / 0.28), s=1.25)

        # Sweeping terracotta-red & ochre contour path (matching t=10.80s in reference9.mp4)
        ochre_pts = [(690, 0), (540, 140), (200, 340), (195, 580), (490, 620), (750, 560)]
        d.line(ochre_pts, fill=(185, 138, 68, 175), width=6, joint="curve")

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
        d.line(red_pts, fill=(192, 56, 40, 225), width=22, joint="curve")

        # Technical wireframe grid box around center lockup
        gx0, gy0, gx1, gy1 = 220, 680, 790, 1290
        for xx_l in (gx0, gx0 + 95, gx1 - 95, gx1):
            d.line([(xx_l, gy0 - 40), (xx_l, gy1 + 40)], fill=(58, 76, 104, 135), width=2)
        for yy_l in (gy0, gy0 + 110, gy1 - 110, gy1):
            d.line([(gx0 - 40, yy_l), (gx1 + 40, yy_l)], fill=(58, 76, 104, 135), width=2)
        d.rectangle([gx0, gy0, gx1, gy1], outline=(82, 108, 148, 180), width=2)

        # Small technical icon in top-left of bounding box
        d.rectangle([gx0 + 12, gy0 + 12, gx0 + 34, gy0 + 34], outline=(160, 180, 210, 180), width=2)

        # Top white phrase + giant italic electric-blue stamp (#3888FF)
        f_top = get_font(INTER_REG, 58)
        bb_t = d.textbbox((0, 0), stamp_top_text, font=f_top)
        tw_t = bb_t[2] - bb_t[0]
        d.text(((W - tw_t) // 2, 790), stamp_top_text, font=f_top, fill=(246, 244, 236, 255))

        f_blue = get_font(MONTSERRAT_BLACK_IT, int(94 * pop))
        bb_b = d.textbbox((0, 0), stamp_blue_word, font=f_blue)
        tw_b = bb_b[2] - bb_b[0]
        bx = (W - tw_b) // 2
        by = 865
        # Soft blue glow behind electric-blue word
        glow_l = Image.new("RGBA", (W, 240), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_l)
        gd.text((bx, 40), stamp_blue_word, font=f_blue, fill=(42, 124, 255, 135))
        glow_l = glow_l.filter(ImageFilter.GaussianBlur(radius=12))
        img.alpha_composite(glow_l, (0, by - 40))

        d.text((bx, by), stamp_blue_word, font=f_blue, fill=(58, 142, 255, 255))

    return img


# ---------------------------------------------------------------------------
# Cutaway #4 (26.85s - 30.35s): Cream Drafting-Paper #2 with Sliding Silhouettes
# & Italic Electric-Blue Stamp (Exact replica of t=16.80s - 17.95s "you're just / ONE MORE")
# ---------------------------------------------------------------------------
def render_cream_architect_stamp(t: float) -> Image.Image:
    """
    Reproduces t=16.80s–17.95s of reference9.mp4:
      - Warm cream drafting-paper canvas (#F7F0D8)
      - Sweeping ochre-gold & terracotta-red contour lines
      - Dark charcoal architectural silhouette shapes sliding across upper-left,
        middle-right, and lower-left corners
      - Center typography: 'the term' / 'ARCHITECT' (italic electric-blue) ->
        'without knowing / what it meant'
    """
    img = Image.new("RGBA", (W, H), (247, 240, 216, 255))
    d = ImageDraw.Draw(img)

    # Top-left black header bar
    d.rectangle([0, 0, 390, 68], fill=(10, 10, 12, 255))

    age = t - 26.85

    # Golden-ochre sweeping contour loop (matching t=17.40s)
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
    d.line(gold_pts, fill=(216, 162, 62, 235), width=5, joint="curve")

    # Bold terracotta-red angular contour line at bottom (matching t=17.40s)
    red_pts = [
        (240, 1920),
        (295, 1620),
        (485, 1460),
        (635, 1340),
        (735, 1210),
        (920, 1360),
        (1080, 1465),
    ]
    d.line(red_pts, fill=(212, 64, 44, 255), width=28, joint="curve")

    # Dark charcoal architectural silhouette blocks sliding across corners (matching t=17.40s)
    slide = int(age * 42)
    sil_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sil_layer)
    # Upper-left silhouette polygon
    sd.polygon(
        [(0, 68), (240 - slide // 2, 68), (160 - slide // 2, 320), (0, 480)],
        fill=(32, 38, 36, 235),
    )
    # Right-middle silhouette polygon
    sd.polygon(
        [(1080, 640 + slide // 3), (880, 820 + slide // 3), (960, 1060 + slide // 3), (1080, 1120 + slide // 3)],
        fill=(32, 38, 36, 230),
    )
    # Lower-left silhouette polygon
    sd.polygon(
        [(0, 1320 - slide // 3), (220, 1460 - slide // 3), (295, 1680 - slide // 3), (140, 1920), (0, 1920)],
        fill=(32, 38, 36, 235),
    )
    sil_layer = sil_layer.filter(ImageFilter.GaussianBlur(radius=4))
    img.alpha_composite(sil_layer)

    # Technical HUD overlay in dark charcoal
    img.alpha_composite(get_hud_overlay("light"))

    # Center typography lockup (matching "you're just / ONE MORE" at t=17.40s)
    if t < 28.75:
        f_top = get_font(INTER_REG, 56)
        txt_top = "the term"
        bb_t = d.textbbox((0, 0), txt_top, font=f_top)
        d.text(((W - (bb_t[2] - bb_t[0])) // 2 + 25, 920), txt_top, font=f_top, fill=(28, 30, 34, 255))

        pop = ease_out_back(min(1.0, (t - 26.92) / 0.26), s=1.3)
        f_blue = get_font(MONTSERRAT_BLACK_IT, max(24, int(92 * pop)))
        word = "ARCHITECT" if t >= 27.25 else "ARCHI"
        bb_b = d.textbbox((0, 0), word, font=f_blue)
        d.text(((W - (bb_b[2] - bb_b[0])) // 2, 985), word, font=f_blue, fill=(58, 142, 255, 255))
    else:
        p2 = ease_out_back(min(1.0, (t - 28.75) / 0.26), s=1.25)
        f_top = get_font(INTER_REG, 54)
        txt_top = "without knowing"
        bb_t = d.textbbox((0, 0), txt_top, font=f_top)
        d.text(((W - (bb_t[2] - bb_t[0])) // 2, 915), txt_top, font=f_top, fill=(28, 30, 34, 255))

        f_blue = get_font(MONTSERRAT_BLACK_IT, max(24, int(86 * p2)))
        word = "WHAT IT MEANT"
        bb_b = d.textbbox((0, 0), word, font=f_blue)
        d.text(((W - (bb_b[2] - bb_b[0])) // 2, 985), word, font=f_blue, fill=(58, 142, 255, 255))

    return img


# ---------------------------------------------------------------------------
# Signature Element #5: Talking-Head Lower-Case Minimalist Tight-Tracked Chest Subtitles
# with Progressive Word Opacity (matching t=7.2s, 15.2s, 18.2s, 21.0s, 25.3s)
# ---------------------------------------------------------------------------
# Format: (t_start, t_end, [ [(word, t_active), ...], [(word, t_active), ...] ])
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
    """
    Renders the exact lower-case tight-tracked chest captions from reference9.mp4
    (e.g. t=18.2s 'what you', t=21.0s 'content on / social media.', t=25.3s 'now, i get it'):
      - Positioned at chest level (y ~ 1110)
      - Words not yet spoken appear at 28% ghost opacity and illuminate to 100% crisp white
        with a soft dark drop shadow as spoken.
    """
    for t0, t1, lines in TALKING_SUBTITLES:
        if t0 <= t < t1:
            fnt = get_font(INTER_MED, 62)
            line_h = 68
            block_y = 1095 if len(lines) == 1 else 1065

            # Measure widest line so multi-line blocks align cleanly at left edge of centered block
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
                cur_y = block_y + l_idx * line_h
                for w_str, t_act in line:
                    active_p = clamp((t - t_act) / 0.10, 0.0, 1.0)
                    alpha = int(72 + 183 * active_p)
                    # Soft dark shadow
                    d.text((cur_x + 2, cur_y + 3), w_str, font=fnt, fill=(0, 0, 0, int(alpha * 0.72)))
                    d.text((cur_x, cur_y), w_str, font=fnt, fill=(250, 248, 242, alpha))
                    bb_w = d.textbbox((0, 0), w_str + " ", font=fnt)
                    cur_x += (bb_w[2] - bb_w[0]) - 3
            break


# ---------------------------------------------------------------------------
# Signature Element #6: Final Pull-Back Window-in-Black Frame + Giant Metallic
# Ice-Blue Chrome Lockup (48.95s - 51.80s, exact match to t=35.80s - 37.86s "2025")
# ---------------------------------------------------------------------------
def render_metallic_chrome_text(text: str, font_size: int = 230) -> Image.Image:
    """
    Renders giant condensed display text with the exact vertical metallic ice-blue-to-white
    chrome gradient & subtle glow from t=36.80s ("2025") of reference9.mp4.
    """
    fnt = get_font(BEBAS_REG, font_size)
    tmp = Image.new("RGBA", (W, 340), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bb = td.textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = (W - tw) // 2
    ty = 40 - bb[1]

    mask = Image.new("L", (W, 340), 0)
    md = ImageDraw.Draw(mask)
    md.text((tx, ty), text, font=fnt, fill=255)

    # Vertical chrome gradient: ice-blue top -> bright white middle -> steel-blue bottom
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
    """
    Reproduces t=35.80s–37.86s of reference9.mp4:
      - Talking-head frame smoothly scales down from 100% -> 56% into a centered
        floating vertical rectangle on a pitch-black (#000000) background.
      - Overlapping the lower portion of the video card:
          * Small lower-case white label ('when i was just' -> 'i wanted to be an')
          * Giant metallic ice-blue-to-white chrome headline ('"AGE 14"' -> '"ARCHITECT"')
    """
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    p_zoom = ease_out_cubic(min(1.0, (t - 48.95) / 0.48))
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
        pop = ease_out_back(min(1.0, max(0.0, (t - 49.20) / 0.30)), s=1.3)
        f_sz = max(40, int(235 * pop))
    else:
        lbl = "i wanted to be an"
        chrome_word = '"ARCHITECT"'
        pop = ease_out_back(min(1.0, (t - 50.52) / 0.30), s=1.3)
        f_sz = max(40, int(195 * pop))

    f_lbl = get_font(INTER_MED, 50)
    bb_l = d.textbbox((0, 0), lbl, font=f_lbl)
    lw = bb_l[2] - bb_l[0]
    ly = 1045
    d.text(((W - lw) // 2 + 2, ly + 2), lbl, font=f_lbl, fill=(0, 0, 0, 200))
    d.text(((W - lw) // 2, ly), lbl, font=f_lbl, fill=(250, 248, 242, 255))

    if (t >= 49.20 and t < 50.52) or t >= 50.52:
        chrome_layer = render_metallic_chrome_text(chrome_word, font_size=f_sz)
        canvas.alpha_composite(chrome_layer, (0, 1085))

    return canvas


# ---------------------------------------------------------------------------
# Master Frame Compositor
# ---------------------------------------------------------------------------
def render_frame(raw_rgb: np.ndarray, t: float) -> np.ndarray:
    # 1. Beat 1 (0.00 - 5.65s): 3D Z-Space Dark Blueprint & Node Canvas
    if t < 5.65:
        out = render_zspace_opening(t)
        return np.array(out.convert("RGB"))

    # 2. Beat 2B (8.30 - 10.75s): Dark HUD Viewfinder Spotlight Cutaway
    if 8.30 <= t < 10.75:
        out = render_dark_spotlight_hud(t)
        return np.array(out.convert("RGB"))

    # 3. Beat 3A (10.75 - 14.10s): Cream Drafting-Paper + Black Portal & 3 Sky-Blue Pills
    if 10.75 <= t < 14.10:
        out = render_cream_portal_pills(t)
        return np.array(out.convert("RGB"))

    # 4. Beat 4 (17.30 - 20.55s): Dark Grid + Blue UI Selection Box + Wireframe Cursors & Italic Blue Stamp
    if 17.30 <= t < 20.55:
        out = render_dark_selection_and_stamp(
            t,
            t_start=17.30,
            t_mid=18.90,
            t_end=20.55,
            sel_top_text="early awareness",
            sel_bot_text="of building",
            stamp_top_text="the construction",
            stamp_blue_word="PROCESS",
        )
        return np.array(out.convert("RGB"))

    # 5. Beat 5B (26.85 - 30.35s): Cream Drafting-Paper #2 + Sliding Silhouettes & Italic Blue Stamp
    if 26.85 <= t < 30.35:
        out = render_cream_architect_stamp(t)
        return np.array(out.convert("RGB"))

    # 6. Beat 6B (35.30 - 38.45s): Dark Grid + Blue UI Selection Box + Italic Blue Stamp ("CREATIVE")
    if 35.30 <= t < 38.45:
        out = render_dark_selection_and_stamp(
            t,
            t_start=35.30,
            t_mid=36.90,
            t_end=38.45,
            sel_top_text="technical skills",
            sel_bot_text="in design",
            stamp_top_text="plus the",
            stamp_blue_word="CREATIVE",
        )
        return np.array(out.convert("RGB"))

    # 7. Beat 7B (48.95 - 51.80s): Pull-Back Window-in-Black Frame + Metallic Chrome '"AGE 14"' / '"ARCHITECT"'
    if 48.95 <= t < 51.80:
        out = render_pullback_window_finale(raw_rgb, t)
        return np.array(out.convert("RGB"))

    # 8. Beat 7C (51.80 - 54.85s): Studio Blueprint Table B-Roll with HUD Viewfinder Border
    if t >= 51.80:
        graded = grade_talking_head(raw_rgb, t)
        canvas = Image.fromarray(graded).convert("RGBA")
        canvas.alpha_composite(get_hud_overlay("dark"))
        return np.array(canvas.convert("RGB"))

    # 9. Default: Talking Head with Anamorphic Light Leaks & Lower-Case Progressive Chest Subtitles
    graded = grade_talking_head(raw_rgb, t)
    leaked = apply_light_leak(graded, t)
    canvas = Image.fromarray(leaked).convert("RGBA")
    render_talking_subtitle(canvas, t)
    return np.array(canvas.convert("RGB"))


# ---------------------------------------------------------------------------
# CLI Entry Point (Preview Contact Sheet & Full 1080x1920 Render)
# ---------------------------------------------------------------------------
def build_preview_grid(raw_video_path: str, out_jpg_path: str):
    preview_times = [
        0.35, 1.25, 2.35, 4.45, 5.45,
        6.10, 7.50, 9.85,
        11.50, 12.60, 13.55,
        16.40, 18.10, 19.65,
        21.60, 27.60, 29.40,
        36.10, 37.60, 41.20,
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
        d.text((8, 7), f"t={t:.2f}s", fill=(255, 255, 0))
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
