#!/usr/bin/env python3
"""
Master 9:16 Video Compositor (`felix-gray-reference12`)
Edits `videobrut 12.mp4` (27.98s) inspired by `reference (2).mp4`, applying:
  - `MOTION-DESIGN.md` methodology
  - `.claude/skills/animation-design-rules/scripts/animation_rules_engine.py`
    (Disney's 12 Principles, Emil Kowalski UI Motion Laws, LottieFiles 3-Layer Choreography)
  - `.claude/skills/motion-code-harvester/scripts/motion_engine.py`
    (`zoom_through_seam`, `cut_the_curve_seam`, `rack_focus_blur_cut`, `nudge_curve_3phase`)

Visual DNA harvested from `reference (2).mp4`:
  1. Chest-level multi-font editorial typography over dark-studio speaker A-roll:
     - Bold geometric sans (`Plus Jakarta Sans ExtraBold`)
     - Clean light/medium sans (`Inter Regular / SemiBold`)
     - Calligraphic script accent (`Great Vibes`)
     - Crimson Red highlight bars (`#D61C1C`) with deep 45-degree soft drop shadows
     - Hand-drawn Crimson Red brush-stroke underlines & curves
  2. Full-screen Sunlit Window-Gobo White Paper Cutaways (`#F7F6F3`):
     - Soft diagonal window-blind gobo light & shadow beams + fine paper grain
     - Cutaway 1A (3.44s - 4.55s): Half-height Crimson Red bar lockup (`"Let the / heartbreak"`)
     - Cutaway 1B (4.55s - 5.92s): Radial Blueprint Square Grid + 3D Extruded Glossy
       Crimson-to-Obsidian Hero Display (`"let the / BREAK YOU / completely."`, matching `10K` at t=6.4s)
     - Cutaway 2A (10.56s - 13.24s): Horizontal Camera Whip-Pan across two Crimson Red pills
       (`"pretending that / you're fine,"` ===> `"doesn't speed up / the healing."`, matching t=14.2s-15.0s)
     - Cutaway 2B (13.24s - 14.96s): Floating 3D Tactile Card & Golden Magnifying Glass Icon
       above Crimson Red bar (`"buries it / a little deeper."`, matching t=17.6s)
     - Cutaway 3 (22.08s - 25.48s): Calligraphic script + `"of you that comes"` + Crimson Red bar
       `"after breaking"` + `"is finally reborn."` (matching `"rewrite / in a / simple way"` at t=27.6s)
"""

import argparse
import math
import os
import subprocess
import sys
import wave
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/animation-design-rules/scripts")
from motion_engine import (
    clamp,
    cubic_bezier,
    expo_in_out,
    expo_out,
    nudge_curve_3phase,
    zoom_through_seam,
    cut_the_curve_seam,
    rack_focus_blur_cut,
)
from animation_rules_engine import (
    emil_ease_out,
    emil_ease_in_out,
    md3_emphasized_decelerate,
    disney_overshoot_ease,
    disney_squash_stretch,
    disney_anticipation_launch,
    disney_arc_position,
    disney_follow_through_layers,
    counter_motion_ambient,
    audit_animation_spec,
)

W, H = 1080, 1920
FPS = 30.0

REPO_ROOT = "/home/user/COOL-backup"
RAW_VIDEO = f"{REPO_ROOT}/videobrut 12.mp4"
PROJECT_DIR = f"{REPO_ROOT}/felix-gray-reference12"
FILM_DIR = f"{PROJECT_DIR}/film"
ASSETS_DIR = f"{PROJECT_DIR}/assets"
MIXED_WAV = f"{ASSETS_DIR}/master_audio_mix.wav"
OUT_MP4 = f"{FILM_DIR}/felix-gray-reference12-9x16.mp4"

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
JAKARTA_EBOLD = f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"

# Palette harvested from `reference (2).mp4`
C_CRIMSON = (214, 28, 28)       # #D61C1C signature crimson red bar from reference (2).mp4
C_CRIMSON_DARK = (138, 14, 18)  # Deep 3D extrusion bevel red
C_PAPER = (246, 245, 242)       # #F6F5F2 warm sunlit paper cutaway background
C_CHARCOAL = (22, 24, 28)       # Crisp editorial ink on white paper
C_MUTED_INK = (72, 76, 84)      # Secondary charcoal subtitle ink
C_GOLD = (238, 174, 42)         # Golden magnifying glass accent from t=17.6s

_FONT_CACHE = {}
_STATIC_CACHE = {}


def get_font(path: str, size: int):
    size = max(12, int(round(size)))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def reveal_state(age: float, delay: float = 0.0, dur: float = 0.34, dy_px: float = 24.0):
    """
    Applies Emil Kowalski (`emil_ease_out`: cubic-bezier(0.23, 1, 0.32, 1))
    and Rule 1 (`scale >= 0.95` floor).
    """
    loc = age - delay
    if loc <= 0.0:
        return 0.0, dy_px, 0.95
    p = emil_ease_out(clamp(loc / max(1e-4, dur)))
    return p, dy_px * (1.0 - p), 0.95 + 0.05 * p


# ---------------------------------------------------------------------------
# 1. Sunlit Window-Gobo White Paper Cutaway Canvas (`t=5.2s, 14.2s, 17.6s, 27.6s`)
# ---------------------------------------------------------------------------
def get_sunlit_gobo_paper_canvas(t: float, age: float = 0.3, pan_x: float = 0.0) -> Image.Image:
    """
    Reconstructs the exact sunlit white paper canvas with soft diagonal window-blind
    gobo shadows from `reference (2).mp4` (`t=5.2s`, `t=14.2s`, `t=17.6s`, `t=27.6s`),
    plus Rule 6 Ambient Counter-Motion (`counter_motion_ambient`).
    """
    if "gobo_base" not in _STATIC_CACHE:
        base = Image.new("RGBA", (W, H), (*C_PAPER, 255))
        # Diagonal window-blind gobo shadow layer (blurred heavily for optical sunlight softness)
        gobo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gobo)
        # Diagonal shadow bands from top-right / top-left like window blinds in t=14.2s & t=17.6s
        polygons = [
            [(380, -100), (1180, 320), (1180, 620), (180, 120)],
            [(-100, 420), (1180, 1080), (1180, 1420), (-100, 740)],
            [(-100, 1180), (980, 1780), (760, 1980), (-100, 1480)],
        ]
        for poly in polygons:
            gd.polygon(poly, fill=(196, 194, 188, 105))
        gobo = gobo.filter(ImageFilter.GaussianBlur(radius=68))
        base = Image.alpha_composite(base, gobo)

        # Subtle radial vignette + fine paper grain
        rng = np.random.default_rng(42)
        arr = np.array(base, dtype=np.int16)
        grain = rng.integers(-4, 5, size=(H, W, 1), dtype=np.int16)
        arr[:, :, :3] = np.clip(arr[:, :, :3] + grain, 0, 255)
        _STATIC_CACHE["gobo_base"] = Image.fromarray(arr.astype(np.uint8), mode="RGBA")

    im = _STATIC_CACHE["gobo_base"].copy()
    return im


# ---------------------------------------------------------------------------
# 2. Dark-Studio Speaker Frame Enhancer (A-Roll Grade + Chest Vignette)
# ---------------------------------------------------------------------------
def prepare_speaker_frame(bgr_frame: np.ndarray, t: float, beat_age: float) -> Image.Image:
    """
    Upscales `videobrut 12.mp4` (`720x1280`) to `1080x1920` with:
    - Slow breathing camera push-in (`1.00 -> 1.045`)
    - Rich editorial contrast & warm skin-tone color grade matching `reference (2).mp4`
    - Subtle chest-area soft gradient (`y=1020..1920`) so chest-level multi-font typography pops
    """
    rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb)

    # Slow cinematic push-in (`klik-cam`: continuous micro-dolly)
    zoom = 1.015 + 0.028 * math.sin(t * 0.55)
    zw = int(round(W * zoom))
    zh = int(round(H * zoom))
    im = im.resize((zw, zh), Image.BILINEAR)
    x0 = (zw - W) // 2
    y0 = (zh - H) // 2
    im = im.crop((x0, y0, x0 + W, y0 + H))

    # Color grade: crisp contrast + warm studio richness
    im = ImageEnhance.Contrast(im).enhance(1.10)
    im = ImageEnhance.Color(im).enhance(1.08)
    im = im.convert("RGBA")

    # Cached lower-chest gradient vignette (`y=980..1920`) for typography legibility
    if "chest_vignette" not in _STATIC_CACHE:
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig)
        for y in range(960, H, 4):
            u = (y - 960) / float(H - 960)
            alpha = int(155 * (u ** 1.45))
            vd.rectangle([0, y, W, y + 4], fill=(6, 7, 10, alpha))
        _STATIC_CACHE["chest_vignette"] = vig

    im = Image.alpha_composite(im, _STATIC_CACHE["chest_vignette"])
    return im


# ---------------------------------------------------------------------------
# 3. Signature Typography Primitives from `reference (2).mp4`
#    (Crimson Red Bar with 45° Long Soft Shadow + Brush Underline + Script)
# ---------------------------------------------------------------------------
def draw_crimson_bar_word(
    canvas: Image.Image,
    text: str,
    cx: int,
    cy: int,
    age: float,
    delay: float = 0.05,
    font_size: int = 76,
    half_height: bool = False,
    on_white_paper: bool = False,
):
    """
    Renders the signature Crimson Red Highlight Bar (`#D61C1C`) from `reference (2).mp4`
    (`t=5.2s`, `11.4s`, `15.0s`, `17.6s`, `27.6s`, `33.2s`) with:
    - Paired wipe animation (`emil_ease_in_out`: cubic-bezier(0.77, 0, 0.175, 1))
    - Disney Follow-Through 45° soft drop shadow arriving +50ms after bar (`disney_follow_through_layers`)
    - Optional `half_height=True` (`t=5.2s` `"growing &"` where the red bar sits behind the lower 58% of letters)
    """
    layers = disney_follow_through_layers(age - delay, base_dur=0.34)
    card_p = layers["card"]
    shadow_p = layers["shadow"]
    if card_p <= 0.02:
        return

    f_bold = get_font(JAKARTA_EBOLD, font_size)
    tmp_d = ImageDraw.Draw(canvas)
    bb = tmp_d.textbbox((0, 0), text, font=f_bold)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]

    # Arc trajectory entrance (`disney_arc_position`)
    _, dy_off, _ = reveal_state(age, delay=delay, dur=0.34, dy_px=24.0)
    tx = cx - tw // 2
    ty = int(cy - th // 2 + dy_off)

    pad_x = 26
    bx0 = tx - pad_x
    bx1_full = tx + tw + pad_x
    wipe = emil_ease_in_out(clamp((age - delay) / 0.30))
    bx1 = bx0 + int((bx1_full - bx0) * wipe)

    if half_height:
        by0 = ty + int(th * 0.36)
        by1 = ty + th + 14
    else:
        by0 = ty - 10
        by1 = ty + th + 16

    # Layer 2: 45-degree soft drop shadow (+50ms Disney Follow-Through lag)
    if shadow_p > 0.05 and bx1 > bx0 + 8:
        sh_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh_d = ImageDraw.Draw(sh_layer)
        sh_alpha = int((125 if on_white_paper else 160) * shadow_p)
        sh_dx = int(8 * shadow_p)
        sh_dy = int(18 * shadow_p)
        sh_d.rounded_rectangle(
            [bx0 + sh_dx, by0 + sh_dy, bx1 + sh_dx, by1 + sh_dy],
            radius=4,
            fill=(15, 16, 20, sh_alpha),
        )
        if on_white_paper and half_height:
            # Soft dark ambient silhouette behind upper half of white text (exact match to t=5.2s "growing &" & t=27.6s "simple way")
            sh_d.text((tx, ty - bb[1] + 2), text, font=f_bold, fill=(12, 14, 18, int(165 * shadow_p)))
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(radius=11))
        canvas.alpha_composite(sh_layer)

    d = ImageDraw.Draw(canvas)
    if bx1 > bx0 + 4:
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=(*C_CRIMSON, int(255 * card_p)))

    txt_color = (255, 255, 255, int(255 * card_p))
    d.text((tx, ty - bb[1]), text, font=f_bold, fill=txt_color)


def draw_red_brush_underline(
    d: ImageDraw.ImageDraw, cx: int, y: int, width: int, progress: float, alpha: int = 255
):
    """Draws the hand-drawn curved Crimson Red brush stroke from `t=1.2s` & `t=3.8s` of `reference (2).mp4`."""
    p = emil_ease_out(clamp(progress))
    if p <= 0.04:
        return
    x0 = cx - width // 2
    cur_w = int(width * p)
    pts = []
    for i in range(16):
        u = i / 15.0
        px = x0 + int(cur_w * u)
        py = y - int(7.0 * math.sin(u * math.pi))
        pts.append((px, py))
    if len(pts) >= 2:
        d.line(pts, fill=(*C_CRIMSON, alpha), width=6)


def draw_shadowed_text_centered(
    canvas: Image.Image,
    text: str,
    cx: int,
    cy: int,
    font,
    fill_rgb,
    age: float,
    delay: float = 0.0,
    dur: float = 0.32,
    on_white_paper: bool = False,
):
    a, dy, _ = reveal_state(age, delay=delay, dur=dur, dy_px=22.0)
    if a <= 0.02:
        return
    d = ImageDraw.Draw(canvas)
    bb = d.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    tx = cx - tw // 2
    ty = int(cy - th // 2 + dy) - bb[1]
    if not on_white_paper:
        d.text((tx + 3, ty + 5), text, font=font, fill=(0, 0, 0, int(155 * a)))
    d.text((tx, ty), text, font=font, fill=(*fill_rgb, int(255 * a)))


# ---------------------------------------------------------------------------
# 4. Cutaway Scene Renderers (Matching `t=5.2s`, `6.4s`, `14.2s-15.0s`, `17.6s`, `27.6s`)
# ---------------------------------------------------------------------------
def render_cutaway_1_heartbreak(t: float) -> Image.Image:
    """
    Beat 3 (3.44s - 5.92s): "Let the heartbreak break you."
    - Phase A (3.44s - 4.55s): Matches `t=5.2s` ("So as we are / growing &"):
      Sunlit white gobo paper + top-left "Let the" + Half-Height Crimson Red bar "heartbreak"
    - Phase B (4.55s - 5.92s): Matches `t=6.4s` ("cross / 10K / followers mark,"):
      Radial Blueprint Square Grid + 3D Extruded Glossy Crimson Display "BREAK YOU"
    """
    if t < 4.55:
        age = t - 3.44
        canvas = get_sunlit_gobo_paper_canvas(t, age=age)
        # Top-left offset small sans ("So as we are" -> "Let the")
        a1, dy1, _ = reveal_state(age, delay=0.02, dur=0.30, dy_px=20.0)
        d = ImageDraw.Draw(canvas)
        f_sm = get_font(INTER_REG, 44)
        d.text((225, int(845 + dy1)), "Let the", font=f_sm, fill=(*C_CHARCOAL, int(255 * a1)))
        # Half-height Crimson Red Bar word ("growing &" -> "heartbreak")
        draw_crimson_bar_word(
            canvas,
            "heartbreak",
            cx=W // 2,
            cy=965,
            age=age,
            delay=0.08,
            font_size=96,
            half_height=True,
            on_white_paper=True,
        )
        return canvas

    # Phase B (4.55s - 5.92s): Blueprint Square Grid + 3D Extruded Glossy Crimson "BREAK YOU" (`t=6.4s` 10K style!)
    age = t - 4.55
    canvas = get_sunlit_gobo_paper_canvas(t, age=age)
    d = ImageDraw.Draw(canvas)

    # 1. Architectural Blueprint Square Grid around center (`x=190..890, y=650..1250`) with radial fade
    grid_p = emil_ease_out(clamp(age / 0.35))
    gx0, gx1, gy0, gy1 = 180, 900, 660, 1260
    step = 45
    for gx in range(gx0, gx1 + 1, step):
        dist_x = abs(gx - W // 2) / 360.0
        al = int(145 * grid_p * max(0.15, 1.0 - 0.65 * dist_x))
        d.line([(gx, gy0), (gx, gy1)], fill=(195, 192, 186, al), width=2)
    for gy in range(gy0, gy1 + 1, step):
        dist_y = abs(gy - 960) / 300.0
        al = int(145 * grid_p * max(0.15, 1.0 - 0.65 * dist_y))
        d.line([(gx0, gy), (gx1, gy)], fill=(195, 192, 186, al), width=2)

    # 2. 3D Extruded Glossy Crimson-to-Obsidian Hero Text ("10K" -> "BREAK")
    layers = disney_follow_through_layers(age, base_dur=0.38)
    hero_p = layers["card"]
    sh_p = layers["shadow"]
    sx_d, sy_d = disney_squash_stretch(clamp(age / 0.48), max_deform=0.045)
    f_hero = get_font(JAKARTA_EBOLD, int(round(138 * sx_d)))
    hero_txt = "BREAK"
    bb = d.textbbox((0, 0), hero_txt, font=f_hero)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    hx = (W - tw) // 2
    hy = int(935 - th // 2 + 24 * (1.0 - hero_p)) - bb[1]

    # Deep 45-degree soft shadow behind 3D extrusion
    if sh_p > 0.05:
        sh_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh_im)
        sd.text((hx + 16, hy + 24), hero_txt, font=f_hero, fill=(10, 12, 16, int(135 * sh_p)))
        sh_im = sh_im.filter(ImageFilter.GaussianBlur(radius=14))
        canvas.alpha_composite(sh_im)
        d = ImageDraw.Draw(canvas)

    # 3D Bevel Extrusion layers (10 depth steps from dark obsidian-crimson to bright crimson)
    for depth in range(10, 0, -1):
        u_d = depth / 10.0
        r_c = int(45 + 150 * (1.0 - u_d))
        g_c = int(8 + 14 * (1.0 - u_d))
        b_c = int(12 + 14 * (1.0 - u_d))
        d.text((hx + depth, hy + int(depth * 1.2)), hero_txt, font=f_hero, fill=(r_c, g_c, b_c, int(255 * hero_p)))

    # Front glossy crimson face
    d.text((hx, hy), hero_txt, font=f_hero, fill=(*C_CRIMSON, int(255 * hero_p)))

    # Strict 2-line maximum: Line 1 = "BREAK" (3D hero), Line 2 = "you open."
    f_sub = get_font(INTER_REG, 42)
    d.text((hx + tw - 215, hy + bb[3] + 22), "you open.", font=f_sub, fill=(*C_MUTED_INK, int(245 * hero_p)))
    return canvas


def render_cutaway_2_pan_and_icon(t: float) -> Image.Image:
    """
    Beat 6 (10.56s - 14.96s):
    - Phase A (10.56s - 13.24s): Horizontal Camera Whip-Pan across two Crimson Red pills
      matching `t=14.2s -> 15.0s` ("who are / founders, -> content creators")
    - Phase B (13.24s - 14.96s): Floating 3D Tactile Document & Golden Magnifying Glass Icon
      above Crimson Red bar matching `t=17.6s` ("scripting / I was stuck in before.")
    """
    if t < 13.24:
        age = t - 10.56
        # Camera pan progress between t=11.65s and t=12.15s using 3-Phase Nudge Curve (`cut-the-curve` §7)!
        pan_p = nudge_curve_3phase(clamp((t - 11.60) / 0.52))
        cam_x = int(round(pan_p * 920))
        canvas = get_sunlit_gobo_paper_canvas(t, age=age, pan_x=float(cam_x))
        d = ImageDraw.Draw(canvas)

        # Station 1 (centered at x = W//2 - cam_x): "pretending that / you're fine,"
        s1_cx = (W // 2) - cam_x
        if -500 <= s1_cx <= W + 500:
            a1, dy1, _ = reveal_state(age, delay=0.02, dur=0.30, dy_px=20.0)
            f_top = get_font(INTER_REG, 40)
            d.text((s1_cx - 215, int(860 + dy1)), "pretending that", font=f_top, fill=(*C_CHARCOAL, int(255 * a1)))
            draw_crimson_bar_word(
                canvas,
                "you're fine,",
                cx=s1_cx,
                cy=965,
                age=age,
                delay=0.06,
                font_size=74,
                half_height=False,
                on_white_paper=True,
            )

        # Station 2 (centered at x = W//2 + 920 - cam_x): "doesn't speed up / the healing."
        s2_cx = (W // 2) + 920 - cam_x
        if -500 <= s2_cx <= W + 500:
            d = ImageDraw.Draw(canvas)
            f_top = get_font(INTER_REG, 40)
            d.text((s2_cx - 235, 860), "doesn't speed up", font=f_top, fill=(*C_CHARCOAL, 245))
            draw_crimson_bar_word(
                canvas,
                "the healing.",
                cx=s2_cx,
                cy=965,
                age=max(0.15, age - 0.90),
                delay=0.0,
                font_size=74,
                half_height=False,
                on_white_paper=True,
            )
        return canvas

    # Phase B (13.24s - 14.96s): Matches `t=17.6s` (3D Document Card + Golden Magnifying Glass + Red Bar + Subtitle)
    age = t - 13.24
    canvas = get_sunlit_gobo_paper_canvas(t, age=age)
    layers = disney_follow_through_layers(age, base_dur=0.38)
    ic_p = layers["card"]
    sh_p = layers["shadow"]

    # 1. Floating 3D Tactile Stacked Paper Card + Golden Magnifying Glass (`x=540, y=760`)
    ax, ay = disney_arc_position(540.0, 795.0, 540.0, 755.0, ic_p, arc_offset_px=12.0)
    icx, icy = int(round(ax)), int(round(ay))

    if sh_p > 0.05:
        sh_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh_im)
        sd.rounded_rectangle([icx - 78 + 14, icy - 92 + 22, icx + 78 + 14, icy + 92 + 22], radius=18, fill=(15, 16, 20, int(115 * sh_p)))
        sh_im = sh_im.filter(ImageFilter.GaussianBlur(radius=14))
        canvas.alpha_composite(sh_im)

    d = ImageDraw.Draw(canvas)
    # Back tilted sheet
    d.rounded_rectangle([icx - 74, icy - 92, icx + 82, icy + 86], radius=16, fill=(225, 223, 218, int(255 * ic_p)), outline=(200, 198, 192, int(255 * ic_p)), width=2)
    # Front white tactile sheet
    d.rounded_rectangle([icx - 82, icy - 84, icx + 74, icy + 94], radius=16, fill=(252, 251, 249, int(255 * ic_p)), outline=(212, 210, 205, int(255 * ic_p)), width=2)
    # Engraved lines on document sheet
    for li in range(4):
        ly = icy - 48 + li * 28
        d.rounded_rectangle([icx - 54, ly, icx + 44, ly + 10], radius=5, fill=(130, 134, 142, int(220 * ic_p)))

    # 3D Golden Magnifying Glass overlapping the sheet (exact match to `t=17.6s` of `reference (2).mp4`!)
    mg_x, mg_y = icx - 10, icy + 4
    # Handle
    d.line([(mg_x - 28, mg_y + 28), (mg_x - 62, mg_y + 72)], fill=(198, 132, 18, int(255 * ic_p)), width=18)
    d.line([(mg_x - 28, mg_y + 28), (mg_x - 62, mg_y + 72)], fill=(*C_GOLD, int(255 * ic_p)), width=12)
    # Rim
    d.ellipse([mg_x - 48, mg_y - 48, mg_x + 48, mg_y + 48], fill=(255, 244, 210, int(140 * ic_p)), outline=(198, 132, 18, int(255 * ic_p)), width=16)
    d.ellipse([mg_x - 44, mg_y - 44, mg_x + 44, mg_y + 44], outline=(*C_GOLD, int(255 * ic_p)), width=10)

    # 2. Line 1 (Crimson Red Bar): "It just buries it" (`y=980`)
    draw_crimson_bar_word(
        canvas,
        "It just buries it",
        cx=W // 2,
        cy=980,
        age=age,
        delay=0.06,
        font_size=70,
        half_height=False,
        on_white_paper=True,
    )

    # 3. Line 2 (Clean charcoal subtitle below red bar): "a little deeper." (Strict 2-line max)
    draw_shadowed_text_centered(
        canvas,
        "a little deeper.",
        cx=W // 2,
        cy=1075,
        font=get_font(INTER_REG, 44),
        fill_rgb=C_CHARCOAL,
        age=age,
        delay=0.12,
        on_white_paper=True,
    )
    return canvas


def render_cutaway_3_after_breaking(t: float) -> Image.Image:
    """
    Beat 9 (22.08s - 25.48s): "Because the version of you that comes after breaking..."
    Split into two 2-line sub-beats so there are NEVER more than 2 lines of subtitle at once:
    - Phase A (22.08s - 23.75s):
      Line 1 (Script `Great Vibes`): "the version of you"
      Line 2 (Sans `Inter Regular`): "that comes"
    - Phase B (23.75s - 25.48s):
      Line 1 (Sans `Inter Regular`): "right after"
      Line 2 (Half-Height Crimson Red Bar): "breaking"
    """
    if t < 23.75:
        age = t - 22.08
        canvas = get_sunlit_gobo_paper_canvas(t, age=age)
        draw_shadowed_text_centered(
            canvas,
            "the version of you",
            cx=W // 2,
            cy=885,
            font=get_font(GREAT_VIBES, 94),
            fill_rgb=C_CHARCOAL,
            age=age,
            delay=0.02,
            on_white_paper=True,
        )
        draw_shadowed_text_centered(
            canvas,
            "that comes",
            cx=W // 2,
            cy=985,
            font=get_font(INTER_REG, 46),
            fill_rgb=C_CHARCOAL,
            age=age,
            delay=0.08,
            on_white_paper=True,
        )
        return canvas

    age = t - 23.75
    canvas = get_sunlit_gobo_paper_canvas(t, age=age)
    draw_shadowed_text_centered(
        canvas,
        "right after",
        cx=W // 2,
        cy=865,
        font=get_font(INTER_REG, 44),
        fill_rgb=C_CHARCOAL,
        age=age,
        delay=0.02,
        on_white_paper=True,
    )
    draw_crimson_bar_word(
        canvas,
        "breaking",
        cx=W // 2,
        cy=970,
        age=age,
        delay=0.07,
        font_size=88,
        half_height=True,
        on_white_paper=True,
    )
    return canvas


# ---------------------------------------------------------------------------
# 5. Chest-Level Multi-Font Overlays on Dark-Studio Speaker A-Roll (MAX 2 LINES)
# ---------------------------------------------------------------------------
def overlay_speaker_typography(canvas: Image.Image, t: float):
    d = ImageDraw.Draw(canvas)

    if t < 0.72:
        # Beat 1A (0.00s - 0.72s): 2 lines max ("Sometimes you need" / "to get over")
        age = t
        draw_shadowed_text_centered(
            canvas, "Sometimes you need", W // 2, 1235, get_font(JAKARTA_EBOLD, 64), (255, 255, 255), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "to get over", W // 2, 1325, get_font(INTER_REG, 46), (240, 242, 246), age, delay=0.07
        )
        draw_red_brush_underline(d, W // 2, 1368, 230, (age - 0.10) / 0.25)

    elif t < 1.44:
        # Beat 1B (0.72s - 1.44s): 2 lines max ("to get over" / "your ex.")
        age = t - 0.72
        draw_shadowed_text_centered(
            canvas, "to get over", W // 2, 1235, get_font(INTER_REG, 46), (240, 242, 246), age, delay=0.0
        )
        draw_shadowed_text_centered(
            canvas, "your ex.", W // 2, 1345, get_font(GREAT_VIBES, 108), (255, 255, 255), age, delay=0.03
        )

    elif t < 2.44:
        # Beat 2A (1.44s - 2.44s): 2 lines max ("So let me tell you" / "the best way")
        age = t - 1.44
        draw_shadowed_text_centered(
            canvas, "So let me tell you", W // 2 + 65, 1225, get_font(INTER_REG, 44), (235, 238, 245), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "the best way", W // 2 - 20, 1315, get_font(JAKARTA_EBOLD, 76), (255, 255, 255), age, delay=0.07
        )
        draw_red_brush_underline(d, W // 2 + 55, 1385, 240, (age - 0.10) / 0.26)

    elif t < 3.44:
        # Beat 2B (2.44s - 3.44s): 2 lines max ("the best way" / "to do it.")
        age = t - 2.44
        draw_shadowed_text_centered(
            canvas, "the best way", W // 2 - 20, 1230, get_font(JAKARTA_EBOLD, 74), (255, 255, 255), age, delay=0.0
        )
        draw_shadowed_text_centered(
            canvas, "to do it.", W // 2 + 55, 1345, get_font(GREAT_VIBES, 100), (255, 255, 255), age, delay=0.03
        )

    elif 5.92 <= t < 6.76:
        # Beat 4A (5.92s - 6.76s): 1 line ("Feel it.")
        age = t - 5.92
        draw_crimson_bar_word(canvas, "Feel it.", cx=W // 2, cy=1290, age=age, delay=0.02, font_size=84)

    elif 6.76 <= t < 7.60:
        # Beat 4B-1 (6.76s - 7.60s): 2 lines max ("Let it knock" / "the wind")
        age = t - 6.76
        draw_shadowed_text_centered(
            canvas, "Let it knock", W // 2, 1220, get_font(INTER_REG, 46), (240, 242, 248), age, delay=0.02
        )
        draw_crimson_bar_word(canvas, "the wind", cx=W // 2, cy=1320, age=age, delay=0.06, font_size=78)

    elif 7.60 <= t < 8.44:
        # Beat 4B-2 (7.60s - 8.44s): 2 lines max ("the wind" / "out of you.")
        age = t - 7.60
        draw_crimson_bar_word(canvas, "the wind", cx=W // 2, cy=1235, age=age + 0.35, delay=0.0, font_size=76)
        draw_shadowed_text_centered(
            canvas, "out of you.", W // 2, 1350, get_font(GREAT_VIBES, 100), (255, 255, 255), age, delay=0.03
        )

    elif 8.44 <= t < 9.45:
        # Beat 5A (8.44s - 9.45s): 2 lines max ("Let it hurt in the" / "places")
        age = t - 8.44
        draw_shadowed_text_centered(
            canvas, "Let it hurt in the", W // 2, 1225, get_font(INTER_REG, 44), (240, 242, 248), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "places", W // 2, 1315, get_font(JAKARTA_EBOLD, 80), (255, 255, 255), age, delay=0.06
        )
        draw_red_brush_underline(d, W // 2, 1372, 240, (age - 0.09) / 0.25)

    elif 9.45 <= t < 10.56:
        # Beat 5B (9.45s - 10.56s): 2 lines max ("that you've been" / "avoiding.")
        age = t - 9.45
        draw_shadowed_text_centered(
            canvas, "that you've been", W // 2, 1225, get_font(INTER_REG, 44), (240, 242, 248), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "avoiding.", W // 2, 1335, get_font(GREAT_VIBES, 98), (255, 255, 255), age, delay=0.05
        )

    elif 14.96 <= t < 16.92:
        # Beat 7 (14.96s - 16.92s): 2 lines ("And the only way is" / "to go through it.")
        age = t - 14.96
        draw_shadowed_text_centered(
            canvas, "And the only way is", W // 2, 1225, get_font(INTER_REG, 44), (240, 242, 248), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "to go through it.", W // 2, 1315, get_font(JAKARTA_EBOLD, 72), (255, 255, 255), age, delay=0.07
        )
        draw_red_brush_underline(d, W // 2, 1372, 360, (age - 0.10) / 0.30)

    elif 16.92 <= t < 18.25:
        # Beat 8A-1 (16.92s - 18.25s): 2 lines max ("So cry and" / "let it grieve")
        age = t - 16.92
        draw_shadowed_text_centered(
            canvas, "So cry and", W // 2, 1220, get_font(INTER_REG, 46), (240, 242, 248), age, delay=0.02
        )
        draw_crimson_bar_word(canvas, "let it grieve", cx=W // 2, cy=1320, age=age, delay=0.06, font_size=76)

    elif 18.25 <= t < 19.68:
        # Beat 8A-2 (18.25s - 19.68s): 2 lines max ("like you thought" / "it wouldn't.")
        age = t - 18.25
        draw_shadowed_text_centered(
            canvas, "like you thought", W // 2, 1225, get_font(INTER_REG, 44), (240, 242, 248), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "it wouldn't.", W // 2, 1335, get_font(GREAT_VIBES, 98), (255, 255, 255), age, delay=0.05
        )

    elif 19.68 <= t < 20.88:
        # Beat 8B-1 (19.68s - 20.88s): 2 lines max ("And let it" / "ruin a night")
        age = t - 19.68
        draw_shadowed_text_centered(
            canvas, "And let it", W // 2, 1225, get_font(INTER_REG, 46), (240, 242, 248), age, delay=0.02
        )
        draw_shadowed_text_centered(
            canvas, "ruin a night", W // 2, 1315, get_font(JAKARTA_EBOLD, 76), (255, 255, 255), age, delay=0.06
        )
        draw_red_brush_underline(d, W // 2, 1372, 280, (age - 0.09) / 0.26)

    elif 20.88 <= t < 22.08:
        # Beat 8B-2 (20.88s - 22.08s): 2 lines max ("ruin a night" / "if it has to.")
        age = t - 20.88
        draw_shadowed_text_centered(
            canvas, "ruin a night", W // 2, 1230, get_font(JAKARTA_EBOLD, 74), (255, 255, 255), age, delay=0.0
        )
        draw_shadowed_text_centered(
            canvas, "if it has to.", W // 2, 1345, get_font(GREAT_VIBES, 96), (255, 255, 255), age, delay=0.03
        )

    elif t >= 25.48:
        # Beat 10 (25.48s - 27.98s): 2 lines max ("is the one that finally" / "knows peace.")
        age = t - 25.48
        draw_shadowed_text_centered(
            canvas, "is the one that finally", W // 2, 1225, get_font(INTER_REG, 44), (240, 242, 248), age, delay=0.02
        )
        draw_crimson_bar_word(canvas, "knows peace.", cx=W // 2, cy=1325, age=age, delay=0.06, font_size=80)


# ---------------------------------------------------------------------------
# 6. Master Frame Compositor & Seam Transitions (`cut-the-curve`)
# ---------------------------------------------------------------------------
SEAMS = [
    (3.44, 0.18, "zoom_through"),
    (5.92, 0.18, "rack_focus"),
    (10.56, 0.18, "cut_the_curve"),
    (14.96, 0.18, "zoom_through"),
    (22.08, 0.18, "cut_the_curve"),
    (25.48, 0.18, "rack_focus"),
]


def is_cutaway_time(t: float) -> bool:
    return (3.44 <= t < 5.92) or (10.56 <= t < 14.96) or (22.08 <= t < 25.48)


def render_cutaway_for_time(t: float) -> Image.Image:
    if 3.44 <= t < 5.92:
        return render_cutaway_1_heartbreak(t)
    if 10.56 <= t < 14.96:
        return render_cutaway_2_pan_and_icon(t)
    return render_cutaway_3_after_breaking(t)


def compose_frame(bgr_frame: np.ndarray, t: float) -> np.ndarray:
    # Check if we are on a velocity-matched seam between A-roll and White Paper Cutaway
    for t_seam, half_w, mode in SEAMS:
        if abs(t - t_seam) <= half_w:
            p = clamp((t - (t_seam - half_w)) / (2.0 * half_w))
            t_before = t_seam - 0.04
            t_after = t_seam + 0.04
            if is_cutaway_time(t_before):
                im_a = render_cutaway_for_time(t_before)
            else:
                im_a = prepare_speaker_frame(bgr_frame, t_before, 0.5)
                overlay_speaker_typography(im_a, t_before)
            if is_cutaway_time(t_after):
                im_b = render_cutaway_for_time(t_after)
            else:
                im_b = prepare_speaker_frame(bgr_frame, t_after, 0.1)
                overlay_speaker_typography(im_b, t_after)

            if mode == "zoom_through":
                out = zoom_through_seam(im_a, im_b, p, inverse=False)
            elif mode == "cut_the_curve":
                out = cut_the_curve_seam(im_a, im_b, p, direction="left")
            else:
                out = rack_focus_blur_cut(im_a, im_b, p)
            return np.array(out.convert("RGB"), dtype=np.uint8)

    if is_cutaway_time(t):
        out = render_cutaway_for_time(t)
        return np.array(out.convert("RGB"), dtype=np.uint8)

    canvas = prepare_speaker_frame(bgr_frame, t, 0.5)
    overlay_speaker_typography(canvas, t)
    return np.array(canvas.convert("RGB"), dtype=np.uint8)


# ---------------------------------------------------------------------------
# 7. Audio Mastering (Original Voice + Subtle Paper-Whoosh & Sub-Bass Seams)
# ---------------------------------------------------------------------------
def build_master_audio(ffmpeg_exe: str, total_dur: float):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    raw_wav = f"{ASSETS_DIR}/raw_voice.wav"
    subprocess.run(
        [ffmpeg_exe, "-y", "-i", RAW_VIDEO, "-vn", "-ar", "48000", "-ac", "2", raw_wav],
        check=True,
        capture_output=True,
    )
    with wave.open(raw_wav, "rb") as wf:
        sr = wf.getframerate()
        n_f = wf.getnframes()
        raw_bytes = wf.readframes(n_f)

    vo = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0
    total_samples = vo.shape[0]
    t = np.arange(total_samples, dtype=np.float32) / float(sr)

    # Warm intimate ambient pad (-28 dB)
    pad_l = 0.012 * np.sin(2 * np.pi * 110.0 * t) + 0.008 * np.sin(2 * np.pi * 164.81 * t)
    pad_r = 0.012 * np.sin(2 * np.pi * 110.0 * t) + 0.008 * np.sin(2 * np.pi * 220.0 * t)

    sfx = np.zeros_like(t)
    rng = np.random.default_rng(12)

    # Paper-whoosh & gentle sub-thump on cutaway transitions (`reference (2).mp4` style)
    transition_times = [3.44, 4.55, 5.92, 10.56, 11.75, 13.24, 14.96, 22.08, 25.48]
    for ts in transition_times:
        i0 = int(ts * sr)
        dur_s = int(0.22 * sr)
        i1 = min(total_samples, i0 + dur_s)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.maximum(0.0, np.sin(np.pi * lt)) ** 1.5
            noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32)
            sub = np.sin(2 * np.pi * (95.0 + 140.0 * lt) * lt * 0.22)
            sfx[i0:i1] += (0.035 * sub + 0.014 * noise) * env

    mix_l = np.clip(vo[:, 0] * 1.15 + pad_l + sfx, -0.98, 0.98)
    mix_r = np.clip(vo[:, 1] * 1.15 + pad_r + sfx, -0.98, 0.98)
    out_i16 = (np.stack([mix_l, mix_r], axis=-1) * 32767.0).astype(np.int16)

    with wave.open(MIXED_WAV, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out_i16.tobytes())
    os.remove(raw_wav)


# ---------------------------------------------------------------------------
# 8. CLI Entrypoint (`--preview` Contact Sheet or Full MP4 Render)
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=str, default="", help="Save a 16-frame preview contact sheet")
    args = parser.parse_args()

    # Audit against the 10 Animation Design Rules
    violations = audit_animation_spec(
        {
            "type": "entrance",
            "initial_scale": 0.95,
            "easing": "cubic-bezier(0.23, 1, 0.32, 1)",
            "screen_travel_ratio": 0.16,
            "layers": ["primary", "secondary", "ambient"],
        }
    )
    if violations:
        raise RuntimeError(f"Animation Design Rules audit failed: {violations}")

    if args.preview:
        os.makedirs(os.path.dirname(args.preview), exist_ok=True)
        cap = cv2.VideoCapture(RAW_VIDEO)
        sample_times = [
            0.8, 2.3, 3.9, 5.1,
            6.3, 7.5, 9.4, 11.2,
            12.5, 14.1, 15.8, 18.2,
            20.6, 23.2, 24.4, 26.6,
        ]
        cols, rows = 4, 4
        tw, th = 270, 480
        sheet = Image.new("RGB", (cols * tw, rows * th), (14, 14, 18))
        for idx, st in enumerate(sample_times):
            cap.set(cv2.CAP_PROP_POS_MSEC, st * 1000.0)
            ok, bgr = cap.read()
            if not ok:
                bgr = np.zeros((1280, 720, 3), dtype=np.uint8)
            rgb = compose_frame(bgr, st)
            thumb = Image.fromarray(rgb).resize((tw, th), Image.LANCZOS)
            td = ImageDraw.Draw(thumb)
            td.rectangle([8, 8, 128, 36], fill=(0, 0, 0))
            td.text((14, 12), f"t={st:05.2f}s", fill=(255, 210, 60))
            sheet.paste(thumb, ((idx % cols) * tw, (idx // cols) * th))
        cap.release()
        sheet.save(args.preview, quality=92)
        print(f"Saved preview contact sheet to {args.preview}")
        return

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(FILM_DIR, exist_ok=True)

    cap = cv2.VideoCapture(RAW_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_dur = total_frames / fps

    build_master_audio(ffmpeg_exe, total_dur)

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
        f"{fps}",
        "-i",
        "-",
        "-i",
        MIXED_WAV,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "19",
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
    proc = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    fi = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        t = fi / fps
        rgb = compose_frame(bgr, t)
        proc.stdin.write(rgb.tobytes())
        fi += 1
        if fi % 150 == 0 or fi == total_frames:
            print(f"Rendered {fi}/{total_frames} frames ({fi / max(1, total_frames) * 100:.1f}%)", flush=True)
    cap.release()
    proc.stdin.close()
    ret = proc.wait()
    if os.path.exists(MIXED_WAV):
        os.remove(MIXED_WAV)
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")
    print(f"Successfully rendered {OUT_MP4}")


if __name__ == "__main__":
    main()
