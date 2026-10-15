#!/usr/bin/env python3
"""
Master 9:16 Video Compositor for `video brut 10.mp4` (`felix-gray-reference10`)
Inspired EXCLUSIVELY by the "After" ("our work") edit in `reference 10.mp4`
and governed by `MOTION-DESIGN.md` + `.claude/skills/broll-media-fetcher`.

Visual Grammar of `reference 10.mp4` ("After" / "our work"):
1. Talking-Head Kinetic Typography (`render_talking_head_scene`):
   - Center-chest captions (`y ~ 980..1180`) with clean white lead-in words,
     giant Glowing Yellow-Gold (`#FFE438`) hero words with vertical ghost/echo
     trails on entry, and sweeping white Calligraphic Script overlays (`Great Vibes`)
     across the baseline (`"Peak Architects"`, `"London practice"` style).
   - Warm Golden Halftone Dot Matrix (`#FFD428`) glowing behind the speaker's
     shoulders (between the background and the segmented speaker cutout) on key beats.
2. Full-Screen 4-Slice Vertical Accordion Architectural Evolution (`render_4slice_accordion`):
   - 4 vertical columns (`270px` each) sliding in with staggered `--motion-ease-out`
     (`cubic-bezier(.2, .8, .2, 1)`), evolving through 3 architectural stages:
     (Stage A) Monochrome black-and-white modern concrete architecture ->
     (Stage B) Hand-drawn ink elevation sketch & CAD blueprint ->
     (Stage C) Warm twilight illuminated glass atrium with wireframe lines,
     climaxing with a full-height 11x Vertical Yellow-Gold Echo Repeat Stack
     (`COLLEGE` / `ARCHITECT`) and center word-by-word white captions.
3. Rising Architectural Spire Wipe + Full-Screen Vertical Stacked Typography Postcard
   (`render_vertical_postcard_scene`):
   - A 3D architectural glass spire rises in front of the speaker right before the cut,
     transitioning into a full-screen architectural B-roll scene with giant vertical
     stacked display letters along the left edge (`S-I-T-E-S` / `D-E-S-I-G-N`) in
     sky-blue (`#2296F3`) and burnt-orange (`#E86424`).
4. Dark Split-Card Rounded Window + 3D Winding Staircase & Architectural Tower Cutout
   (`render_dark_split_window_scene`):
   - Matte black canvas (`#0E0E11`) with the speaker framed in an upper rounded
     square window (`760x700`, `radius=48px`).
   - Below the window:
     (Phase A) A 3D S-curved white architectural staircase winding upward from
     a minimalist figure at the bottom step (`"helper"` / `"technical"`) up to a
     glowing yellow-gold hero word (`"awareness"` / `"management"`) at the top.
     (Phase B) A monochrome architectural tower elevation cutout on the bottom-left
     beside a 3-tier white + glowing yellow-gold + sweeping calligraphic script lock-up.
"""

import argparse
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/home/user/COOL-backup/.claude/skills/motion-code-harvester/scripts")
from motion_engine import (
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
DURATION = 54.85
TOTAL_FRAMES = int(round(DURATION * FPS))

# Rhythm benchmarks from MOTION-DESIGN.md
MOTION_FAST = 0.180      # 180ms
MOTION_STATE = 0.300     # 300ms
MOTION_ENTER = 0.480     # 480ms
MOTION_SEQUENCE = 0.720  # 720ms
MOTION_STAGGER = 0.065   # 65ms
REVEAL_OFFSET_Y = 28

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
INTER_REG = f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf"
INTER_MED = f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf"
INTER_BOLD = f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf"
JAKARTA_BOLD = f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf"
MONTSERRAT_BLACK_IT = f"{FONT_BASE}/montserrat/900Black_Italic/Montserrat_900Black_Italic.ttf"
BEBAS_REG = f"{FONT_BASE}/bebas-neue/400Regular/BebasNeue_400Regular.ttf"
MONO_MED = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"
GREAT_VIBES = f"{FONT_BASE}/great-vibes/400Regular/GreatVibes_400Regular.ttf"
PLAYFAIR_IT = f"{FONT_BASE}/playfair-display/700Bold_Italic/PlayfairDisplay_700Bold_Italic.ttf"

_FONT_CACHE = {}


def get_font(path: str, size: int):
    sz = max(12, int(round(size)))
    key = (path, sz)
    if key not in _FONT_CACHE:
        if not os.path.exists(path):
            path = INTER_BOLD
        _FONT_CACHE[key] = ImageFont.truetype(path, sz)
    return _FONT_CACHE[key]


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
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
# Pre-load High-Res Architectural Assets & B-Roll Clips
# ---------------------------------------------------------------------------
_ASSETS = None


def get_assets():
    global _ASSETS
    if _ASSETS is not None:
        return _ASSETS

    _ASSETS = {}
    img_dir = "/home/user/COOL-backup/felix-gray-reference10/assets/images"

    def load_fit(name, target_w=W, target_h=H, grayscale=False):
        p = f"{img_dir}/{name}"
        im = Image.open(p).convert("RGB")
        if grayscale:
            im = im.convert("L").convert("RGB")
            im = ImageEnhance.Contrast(im).enhance(1.18)
        iw, ih = im.size
        scale = max(target_w / iw, target_h / ih)
        nw, nh = int(round(iw * scale)), int(round(ih * scale))
        im = im.resize((nw, nh), Image.BICUBIC)
        x0 = (nw - target_w) // 2
        y0 = (nh - target_h) // 2
        return im.crop((x0, y0, x0 + target_w, y0 + target_h)).convert("RGBA")

    _ASSETS["stage1_concrete"] = load_fit("stage1_monochrome_concrete.jpg", int(W * 1.12), int(H * 1.12), grayscale=True)
    _ASSETS["stage2_sketch"] = load_fit("stage2_blueprint_sketch.jpg", int(W * 1.12), int(H * 1.12))
    _ASSETS["stage3_atrium"] = load_fit("stage3_twilight_atrium.jpg", int(W * 1.12), int(H * 1.12))

    _ASSETS["stage2_mono_atrium"] = load_fit("monochrome_atrium.jpg", int(W * 1.12), int(H * 1.12), grayscale=True)
    _ASSETS["stage2_cad"] = load_fit("blueprint_cad.jpg", int(W * 1.12), int(H * 1.12))
    _ASSETS["stage2_model"] = load_fit("arch_3d_model.jpg", int(W * 1.12), int(H * 1.12))

    _ASSETS["postcard_sites"] = load_fit("construction_site.jpg", int(W * 1.18), int(H * 1.18))
    _ASSETS["postcard_shard"] = load_fit("shard_skyline.jpg", int(W * 1.18), int(H * 1.18))
    _ASSETS["postcard_timber"] = load_fit("timber_atrium.jpg", int(W * 1.18), int(H * 1.18))

    # Build a clean 3D glass spire cutout (like The Shard rising at t=9.60s in ref10)
    spire = Image.new("RGBA", (320, 920), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spire)
    # Left sunlit glass face
    sd.polygon([(160, 10), (48, 910), (168, 910)], fill=(212, 224, 210, 255))
    # Right shadowed glass face
    sd.polygon([(160, 10), (168, 910), (272, 910)], fill=(118, 136, 128, 255))
    # Central specular ridge & horizontal mullion ribs
    sd.line([(160, 10), (168, 910)], fill=(248, 252, 245, 255), width=4)
    for yy in range(90, 900, 38):
        frac = (yy - 10) / 900.0
        lx = int(160 - 112 * frac)
        rx = int(160 + 112 * frac)
        sd.line([(lx, yy), (168, yy - 6)], fill=(165, 180, 168, 210), width=2)
        sd.line([(168, yy - 6), (rx, yy)], fill=(82, 98, 92, 210), width=2)
    _ASSETS["spire_cutout"] = spire

    # Build a detailed monochrome architectural clock-tower / facade elevation cutout
    # (for the bottom-left of the dark split-card scene, matching t=15.60s-16.85s of ref10)
    tower = Image.new("RGBA", (300, 820), (0, 0, 0, 0))
    td = ImageDraw.Draw(tower)
    # Spire roof + pediment
    td.polygon([(140, 10), (50, 210), (230, 210)], fill=(168, 168, 172, 255), outline=(235, 235, 240, 255))
    td.rectangle([38, 210, 242, 820], fill=(142, 142, 146, 255), outline=(225, 225, 230, 255), width=3)
    # Architectural pilasters & cornices
    for yy in (210, 320, 520, 680):
        td.rectangle([28, yy, 252, yy + 14], fill=(195, 195, 200, 255), outline=(90, 90, 95, 255), width=2)
    for xx in range(56, 230, 28):
        td.line([(xx, 224), (xx, 320)], fill=(75, 75, 80, 255), width=5)
        td.line([(xx, 534), (xx, 820)], fill=(75, 75, 80, 255), width=5)
    # Clock dial face (matching Big Ben / clock tower in ref10 t=15.95s)
    td.rectangle([62, 344, 218, 500], fill=(180, 180, 185, 255), outline=(70, 70, 75, 255), width=3)
    td.ellipse([78, 360, 202, 484], fill=(242, 242, 245, 255), outline=(55, 55, 60, 255), width=4)
    td.ellipse([134, 416, 146, 428], fill=(40, 40, 45, 255))
    td.line([(140, 422), (140, 378)], fill=(35, 35, 40, 255), width=5)
    td.line([(140, 422), (174, 438)], fill=(35, 35, 40, 255), width=4)
    _ASSETS["tower_cutout"] = tower

    return _ASSETS


# ---------------------------------------------------------------------------
# Color Grading & Golden Halftone Backdrop Behind Speaker
# ---------------------------------------------------------------------------
_HALFTONE_LAYER = None
_SPEAKER_ELLIPSE_MASK = None


def get_halftone_layer() -> Image.Image:
    global _HALFTONE_LAYER
    if _HALFTONE_LAYER is not None:
        return _HALFTONE_LAYER

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # Golden halftone dot matrix across middle-upper background (y = 340..1080)
    # matching t=3.35s-3.60s of reference 10.mp4!
    spacing = 24
    for gy in range(360, 1080, spacing):
        for gx in range(40, W - 40, spacing):
            # Concentrated behind the left and right shoulders
            dist_l = math.hypot((gx - 210) / 240.0, (gy - 690) / 290.0)
            dist_r = math.hypot((gx - 870) / 240.0, (gy - 690) / 290.0)
            strength = max(clamp(1.0 - dist_l), clamp(1.0 - dist_r))
            if strength > 0.08:
                r = max(2, int(round(10.5 * (strength ** 0.85))))
                alpha = int(clamp(strength * 235, 0, 230))
                d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(255, 212, 38, alpha))
    _HALFTONE_LAYER = layer
    return _HALFTONE_LAYER


def get_speaker_foreground_mask() -> Image.Image:
    """
    Soft anatomical foreground mask for Paul's head and torso so the golden halftone
    dot matrix sits BEHIND his head and shoulders, just like reference 10.mp4!
    """
    global _SPEAKER_ELLIPSE_MASK
    if _SPEAKER_ELLIPSE_MASK is not None:
        return _SPEAKER_ELLIPSE_MASK

    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    # Head + neck
    d.ellipse([365, 230, 715, 760], fill=255)
    # Shoulders + torso
    d.rounded_rectangle([140, 680, 940, 1920], radius=180, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(radius=22))
    _SPEAKER_ELLIPSE_MASK = m
    return _SPEAKER_ELLIPSE_MASK


def grade_talking_head(raw_rgb: np.ndarray, t: float, zoom: float = 1.0) -> Image.Image:
    f = raw_rgb.astype(np.float32)
    # Rich cinema contrast + warm amber tungsten glow matching reference 10.mp4
    f = (f - 128.0) * 1.10 + 125.0
    f[:, :, 0] *= 1.04
    f[:, :, 1] *= 1.01
    f[:, :, 2] *= 0.94
    graded = np.clip(f, 0, 255).astype(np.uint8)
    im = Image.fromarray(graded).convert("RGBA")

    # Subtle breathing camera zoom
    z = zoom + 0.025 * math.sin(t * 0.65)
    if abs(z - 1.0) > 0.002:
        nw, nh = int(round(W * z)), int(round(H * z))
        im_z = im.resize((nw, nh), Image.BILINEAR)
        x0 = (nw - W) // 2
        y0 = int((nh - H) * 0.38)
        im = im_z.crop((x0, y0, x0 + W, y0 + H))

    # Bottom vignette for crisp chest-level caption contrast
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    vig = np.clip((yy - 0.42) / 0.58, 0.0, 1.0) * 0.48
    arr = np.array(im, dtype=np.float32)
    arr[:, :, :3] *= (1.0 - vig[:, :, None])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------------------
# Signature Reference 10 Kinetic Typography Renderer
# (White sans lead-in + Glowing Yellow-Gold Hero Word with Vertical Echo Trail
#  + Sweeping White Calligraphic Script Overlay)
# ---------------------------------------------------------------------------
def draw_ref10_lockup(
    canvas: Image.Image,
    age: float,
    lead_text: str = "",
    hero_text: str = "",
    script_text: str = "",
    sub_text: str = "",
    cy: int = 1045,
    hero_color=(255, 226, 44),
    echo_trail: bool = True,
    align: str = "center",
):
    # Waterfall Entry (`cut-the-curve` §6: shrinking gap * 0.84^i + weight-based Y offset)
    a_lead, dy_lead, _ = waterfall_word_state(age, word_index=0, weight="normal")
    hero_idx = 1 if lead_text else 0
    a_hero, dy_hero, _ = waterfall_word_state(age, word_index=hero_idx, weight="anchor")
    hero_age = max(0.0, age - (0.055 if lead_text else 0.0))

    # 3-Phase Nudge Curve (`cut-the-curve` §7: 10%/65%/25% distance over 20%/18%/62% time)
    # Gently repositions the lead + hero group upward by 16px when script/sub-text arrives!
    nudge_dy = 0.0
    if script_text or sub_text:
        nudge_age = max(0.0, hero_age - 0.10)
        nudge_dy = -16.0 * nudge_curve_3phase(nudge_age / 0.42)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    f_lead = get_font(INTER_MED, 50)
    f_hero = get_font(JAKARTA_BOLD, 104)
    f_script = get_font(GREAT_VIBES, 128)
    f_sub = get_font(INTER_REG, 44)

    # Compute horizontal anchor
    hero_w = 0
    if hero_text:
        bb_h = od.textbbox((0, 0), hero_text, font=f_hero)
        hero_w = bb_h[2] - bb_h[0]

    # 1. Lead-in white text above hero word
    if lead_text and a_lead > 0.02:
        bb_l = od.textbbox((0, 0), lead_text, font=f_lead)
        lw = bb_l[2] - bb_l[0]
        if align == "left_of_hero" and hero_w > 0:
            lx = (W - hero_w) // 2
        else:
            lx = (W - lw) // 2
        ly = int(cy - 68 + dy_lead + nudge_dy)
        od.text((lx + 2, ly + 4), lead_text, font=f_lead, fill=(0, 0, 0, int(185 * a_lead)))
        od.text((lx, ly), lead_text, font=f_lead, fill=(248, 248, 252, int(255 * a_lead)))

    # 2. Hero word (Glowing Yellow-Gold or Crisp White) + Vertical Kinetic Echo Trail
    if hero_text and a_hero > 0.02:
        hx = (W - hero_w) // 2
        hy = int(cy - 10 + dy_hero + nudge_dy)

        # Vertical ghost echo copies during entry (like "Paul", "started", "Peak" in ref10)
        if echo_trail and 0.01 < hero_age < 0.62:
            echo_p = 1.0 - power4_out(hero_age / 0.62)
            for mult, alpha_scale in [(1, 0.44), (2, 0.24)]:
                off = int(round(mult * 76 * echo_p))
                e_alpha = int(255 * alpha_scale * echo_p)
                if e_alpha > 6:
                    od.text((hx, hy - off), hero_text, font=f_hero, fill=(255, 220, 40, e_alpha))
                    od.text((hx, hy + off), hero_text, font=f_hero, fill=(255, 220, 40, e_alpha))

        # Warm Golden Outer Glow Halo
        glow = Image.new("RGBA", (W, 280), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.text((hx, 70), hero_text, font=f_hero, fill=(255, 200, 15, int(195 * a_hero)))
        glow_blur = glow.filter(ImageFilter.GaussianBlur(radius=22))
        overlay.alpha_composite(glow_blur, (0, hy - 70))

        # Dark drop shadow + Main Hero Word
        od.text((hx + 3, hy + 5), hero_text, font=f_hero, fill=(0, 0, 0, int(195 * a_hero)))
        od.text(
            (hx, hy),
            hero_text,
            font=f_hero,
            fill=(hero_color[0], hero_color[1], hero_color[2], int(255 * a_hero)),
        )

    # 3. Sub-text below hero word
    if sub_text:
        a_sub, dy_sub, _ = waterfall_word_state(age, word_index=hero_idx + 1, weight="light")
        if a_sub > 0.02:
            bb_s = od.textbbox((0, 0), sub_text, font=f_sub)
            sw = bb_s[2] - bb_s[0]
            sx = (W - sw) // 2
            sy = int(cy + 98 + dy_sub)
            od.text((sx + 2, sy + 3), sub_text, font=f_sub, fill=(0, 0, 0, int(185 * a_sub)))
            od.text((sx, sy), sub_text, font=f_sub, fill=(242, 242, 246, int(250 * a_sub)))

    # 4. Sweeping White Calligraphic Script Overlay via `swipe_clip_reveal` (`expo.inOut` left-to-right wipe!)
    if script_text:
        sc_age = max(0.0, hero_age - 0.12)
        if sc_age > 0.01:
            sc_layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
            scd = ImageDraw.Draw(sc_layer)
            bb_sc = scd.textbbox((0, 0), script_text, font=f_script)
            sc_w = bb_sc[2] - bb_sc[0]
            sc_x = (W - sc_w) // 2 + 12
            scd.text((sc_x + 3, 45), script_text, font=f_script, fill=(0, 0, 0, 225))
            scd.text((sc_x, 40), script_text, font=f_script, fill=(255, 255, 255, 255))
            sc_wiped = swipe_clip_reveal(sc_layer, sc_age / 0.42, direction="left_to_right")
            overlay.alpha_composite(sc_wiped, (0, int(cy + 38)))

    canvas.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# Talking-Head Scene with Glowing Captions, Golden Halftone & Rising Spire Wipe
# ---------------------------------------------------------------------------
TALKING_BEATS = [
    # Scene 1 (0.00s - 3.65s): "I got into architecture—my dad taught construction"
    (0.05, 0.85, "I got into", "", "", "", False, (255, 226, 44), "center"),
    (0.85, 2.15, "I got into", "Architecture", "", "", False, (255, 226, 44), "left_of_hero"),
    (2.15, 2.75, "my dad", "Taught", "", "", False, (255, 226, 44), "center"),
    (2.75, 3.65, "taught", "Construction", "craft", "", True, (255, 255, 255), "center"),

    # Scene 3A (8.35s - 10.15s): "dragged onto sites" + rising spire wipe at 9.65s-10.15s
    (8.35, 8.95, "dragged", "", "", "", False, (255, 226, 44), "center"),
    (8.95, 10.15, "dragged onto", "Sites", "", "", False, (255, 226, 44), "left_of_hero"),

    # Scene 5 (20.55s - 26.85s): "When I was about age 14, I was thinking about what I wanted to do in terms of career"
    (20.55, 22.10, "when I was about", "Age 14", "", "", False, (255, 226, 44), "left_of_hero"),
    (22.10, 24.45, "thinking about what I", "Wanted", "", "to do", False, (255, 226, 44), "center"),
    (24.45, 26.85, "in terms of", "Career", "path", "", True, (255, 226, 44), "center"),

    # Scene 7A (32.50s - 35.30s): "and I enjoyed drawing and being creative, so I think it was a combination of"
    (32.50, 33.90, "and I enjoyed", "Drawing", "", "", False, (255, 226, 44), "left_of_hero"),
    (33.90, 35.30, "and being", "Creative", "design", "", True, (255, 226, 44), "center"),

    # Scene 9A (46.80s - 51.80s): "something that really appealed to me when I was about age 14 and decided I wanted to be an architect"
    (46.80, 48.95, "when I was about", "Age 14", "", "", False, (255, 226, 44), "left_of_hero"),
    (48.95, 51.80, "decided I wanted to be an", "Architect", "Peak", "", True, (255, 226, 44), "center"),
]


def render_talking_head_scene(raw_rgb: np.ndarray, t: float) -> Image.Image:
    base = grade_talking_head(raw_rgb, t, zoom=1.04)

    # Check active beat
    active = None
    for b in TALKING_BEATS:
        if b[0] <= t < b[1]:
            active = b
            break

    if active is not None:
        t0, t1, lead, hero, script, sub, use_halftone, h_col, align = active
        age = t - t0

        # If golden halftone backdrop is active (like t=3.35s-3.60s in ref10),
        # composite halftone behind the foreground speaker cutout!
        if use_halftone:
            ht_p = expo_out(age / 0.32) * (
                cubic_bezier_cool((t1 - t) / 0.25) if (t1 - t) < 0.25 else 1.0
            )
            if ht_p > 0.02:
                fg_speaker = base.copy()
                ht = get_halftone_layer().copy()
                # Also draw an oversized Subject-Occluded Display Watermark (`embedded-captions` Vogue-cover depth embed)
                if hero:
                    hd = ImageDraw.Draw(ht)
                    f_big = get_font(JAKARTA_BOLD, 215)
                    bb_b = hd.textbbox((0, 0), hero.upper(), font=f_big)
                    bw = bb_b[2] - bb_b[0]
                    bx = (W - bw) // 2
                    by = int(455 - 24 * expo_out(age / 0.45))
                    hd.text((bx, by), hero.upper(), font=f_big, fill=(255, 224, 52, int(92 * ht_p)))
                if ht_p < 0.99:
                    r, g, b_ch, a = ht.split()
                    a = a.point(lambda p: int(p * ht_p))
                    ht = Image.merge("RGBA", (r, g, b_ch, a))
                base.alpha_composite(ht)
                mask = get_speaker_foreground_mask()
                base = Image.composite(fg_speaker, base, mask)

        draw_ref10_lockup(
            base,
            age=age,
            lead_text=lead,
            hero_text=hero,
            script_text=script,
            sub_text=sub,
            cy=1050,
            hero_color=h_col,
            echo_trail=True,
            align=align,
        )

    # Rising 3D Architectural Spire Cutout right before the Vertical Postcard cuts
    # (Exact match to t=9.60s in reference 10.mp4!)
    for spire_start, spire_end in [(9.60, 10.15), (34.75, 35.30)]:
        if spire_start <= t <= spire_end:
            sp_p = cubic_bezier_cool((t - spire_start) / (spire_end - spire_start))
            spire = get_assets()["spire_cutout"]
            sy = int(H - 860 * sp_p)
            sx = (W - spire.width) // 2 + 25
            base.alpha_composite(spire, (sx, sy))

    return base


# ---------------------------------------------------------------------------
# Full-Screen 4-Slice Vertical Accordion Architectural Evolution
# (Exact match to t=3.85s - 8.20s in reference 10.mp4!)
# ---------------------------------------------------------------------------
def composite_4slice_transition(
    prev_img: Image.Image,
    next_img: Image.Image,
    progress: float,
    direction: str = "up_down",
) -> Image.Image:
    """
    Splits `next_img` into 4 vertical columns (`270px` each) and slides each column
    vertically over `prev_img` with staggered `--motion-ease-out` timing.
    """
    out = prev_img.copy()
    slice_w = W // 4
    for i in range(4):
        stagger = i * 0.11
        local_p = cubic_bezier_cool((progress - stagger) / (1.0 - 3 * 0.11))
        if local_p <= 0.001:
            continue
        x0 = i * slice_w
        x1 = W if i == 3 else (i + 1) * slice_w
        col_im = next_img.crop((x0, 0, x1, H))

        if direction == "up":
            dy = int(round((1.0 - local_p) * H))
        elif direction == "down":
            dy = int(round(-(1.0 - local_p) * H))
        else:
            dy = int(round((1.0 - local_p) * H * (1 if i % 2 == 0 else -1)))

        out.alpha_composite(col_im, (x0, dy))

    # Subtle architectural vertical slice seam lines (matching ref10)
    d = ImageDraw.Draw(out)
    for i in range(1, 4):
        xx = i * slice_w
        d.line([(xx, 0), (xx, H)], fill=(255, 255, 255, 55), width=2)
    return out


def crop_ken_burns(src_oversized: Image.Image, p: float, pan_y: float = -0.5) -> Image.Image:
    ow, oh = src_oversized.size
    max_dx = ow - W
    max_dy = oh - H
    x0 = max_dx // 2
    y0 = int(round(max_dy * (0.5 + 0.45 * pan_y * (p - 0.5))))
    y0 = max(0, min(max_dy, y0))
    return src_oversized.crop((x0, y0, x0 + W, y0 + H))


def render_4slice_accordion_scene(
    t: float,
    t_start: float,
    t_end: float,
    stage_keys: tuple,
    word_cues: list,
    climax_word: str,
) -> Image.Image:
    assets = get_assets()
    dur = t_end - t_start
    age = t - t_start
    norm_t = clamp(age / dur)

    # Neutral studio gradient backdrop (visible as the first 4 slices slide in at t=3.85s)
    yy = np.linspace(218, 128, H, dtype=np.uint8)[:, None]
    bg_arr = np.repeat(yy, W, axis=1)
    bg_rgb = np.stack([bg_arr, bg_arr, bg_arr + 4], axis=-1)
    bg_im = Image.fromarray(bg_rgb).convert("RGBA")

    im1 = crop_ken_burns(assets[stage_keys[0]], norm_t, pan_y=-0.6)
    im2 = crop_ken_burns(assets[stage_keys[1]], norm_t, pan_y=0.5)
    im3 = crop_ken_burns(assets[stage_keys[2]], norm_t, pan_y=-0.4)

    # Phase 1 (0.00 - 0.30 of scene): 4 vertical slices of Stage 1 (Monochrome Concrete) slide up
    p1 = clamp(age / 0.85)
    canvas = composite_4slice_transition(bg_im, im1, p1, direction="up")

    # Phase 2 (0.28 - 0.62 of scene): 4 vertical slices of Stage 2 (Blueprint Sketch) slide in
    t_p2 = dur * 0.28
    if age > t_p2:
        p2 = clamp((age - t_p2) / 0.88)
        canvas = composite_4slice_transition(canvas, im2, p2, direction="up_down")

    # Phase 3 (0.58 - 1.00 of scene): 4 vertical slices of Stage 3 (Twilight Glass Atrium) slide in
    t_p3 = dur * 0.56
    if age > t_p3:
        p3 = clamp((age - t_p3) / 0.88)
        canvas = composite_4slice_transition(canvas, im3, p3, direction="down")

    # Center-screen word-by-word white captions (matching "My / route / to / architecture / in / terms / of / why" in ref10)
    d = ImageDraw.Draw(canvas)
    for w_start, w_end, w_txt in word_cues:
        if w_start <= t < w_end:
            w_age = t - w_start
            wa, wdy = data_reveal(w_age, duration=0.20, offset_y=16)
            f_w = get_font(INTER_MED, 58)
            bb = d.textbbox((0, 0), w_txt, font=f_w)
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
            wx = (W - tw) // 2
            wy = int((H - th) // 2 + wdy)
            # Soft dark pill/shadow for readability over architectural details
            sh = Image.new("RGBA", (W, 180), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh)
            sd.text((wx, 50), w_txt, font=f_w, fill=(0, 0, 0, int(210 * wa)))
            sh = sh.filter(ImageFilter.GaussianBlur(radius=14))
            canvas.alpha_composite(sh, (0, wy - 50))
            d.text((wx, wy), w_txt, font=f_w, fill=(255, 255, 255, int(255 * wa)))
            break

    # Phase 4 Climax (last 0.95s of scene): Full-Height Vertical Yellow-Gold Echo Cascade
    # (Exact match to "Peak / Peak / Peak / Peak" at t=7.85s - 8.15s in reference 10.mp4!)
    climax_start = t_end - 0.95
    if t >= climax_start:
        c_age = t - climax_start
        c_p = cubic_bezier_cool(c_age / 0.55)
        f_climax = get_font(JAKARTA_BOLD, 114)
        bb_c = d.textbbox((0, 0), climax_word, font=f_climax)
        cw = bb_c[2] - bb_c[0]
        cx = (W - cw) // 2
        cy_center = H // 2 - 55

        echo_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ed = ImageDraw.Draw(echo_layer)

        # 5 echoes above and 5 echoes below cascading outward
        n_echoes = 6
        step_y = 142
        for k in range(-n_echoes, n_echoes + 1):
            if k == 0:
                continue
            dist_frac = abs(k) / n_echoes
            appear_delay = abs(k) * 0.045
            local_e = cubic_bezier_cool((c_age - appear_delay) / 0.38)
            if local_e <= 0.01:
                continue
            ey = int(cy_center + k * step_y * (0.35 + 0.65 * c_p))
            alpha_e = int(clamp((1.0 - dist_frac * 0.55) * local_e * 235, 0, 230))
            # Yellow-gold echo repeat (matching t=8.10s of reference 10.mp4)
            ed.text((cx + 2, ey + 3), climax_word, font=f_climax, fill=(0, 0, 0, int(alpha_e * 0.55)))
            ed.text((cx, ey), climax_word, font=f_climax, fill=(255, 218, 36, alpha_e))

        # Center Hero Word in Crisp White with Warm Golden Glow Halo
        glow_c = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        gcd = ImageDraw.Draw(glow_c)
        gcd.text((cx, 65), climax_word, font=f_climax, fill=(255, 195, 20, int(220 * c_p)))
        glow_c = glow_c.filter(ImageFilter.GaussianBlur(radius=22))
        echo_layer.alpha_composite(glow_c, (0, cy_center - 65))

        ed.text((cx + 3, cy_center + 5), climax_word, font=f_climax, fill=(0, 0, 0, int(210 * c_p)))
        ed.text((cx, cy_center), climax_word, font=f_climax, fill=(255, 255, 255, int(255 * c_p)))
        canvas.alpha_composite(echo_layer)

    return canvas


# ---------------------------------------------------------------------------
# Full-Screen Vertical Stacked Typography Postcard
# (Exact match to "L-O-N-D-O-N" at t=9.85s - 10.70s in reference 10.mp4!)
# ---------------------------------------------------------------------------
def render_vertical_postcard_scene(
    t: float,
    t_start: float,
    t_end: float,
    bg_key: str,
    vertical_word: str,
    caption_cues: list,
) -> Image.Image:
    assets = get_assets()
    age = t - t_start
    dur = t_end - t_start
    norm_t = clamp(age / max(0.01, dur))

    # Smooth Ken-Burns zoom on the architectural skyline / site B-roll
    src = assets[bg_key]
    ow, oh = src.size
    scale = 1.0 - 0.08 * norm_t
    cw, ch = int(round(W / scale)), int(round(H / scale))
    cw = min(ow, max(W, cw))
    ch = min(oh, max(H, ch))
    x0 = (ow - cw) // 2
    y0 = (oh - ch) // 2
    bg = src.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)

    # Subtle warm daylight grade + left-edge contrast gradient
    arr = np.array(bg, dtype=np.float32)
    xx = np.linspace(0.0, 1.0, W, dtype=np.float32)[None, :]
    left_shade = np.clip(1.0 - xx / 0.42, 0.0, 1.0) * 0.28
    arr[:, :, :3] *= (1.0 - left_shade[:, :, None])
    canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # Giant Vertical Stacked Letters along the Left Edge (x = 18..330, y = 40..1860)
    # Top half letters in Sky Blue (#2094E8), bottom half letters in Burnt Orange (#E66022)
    # matching L-O-N-D-O-N in reference 10.mp4!
    n_chars = len(vertical_word)
    step_h = (H - 120) // max(1, n_chars)
    font_sz = min(295, int(step_h * 1.12))
    f_vert = get_font(JAKARTA_BOLD, font_sz)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)

    split_idx = n_chars // 2
    for idx, ch_str in enumerate(vertical_word):
        c_delay = idx * 0.055
        c_p = cubic_bezier_cool((age - c_delay) / 0.44)
        if c_p <= 0.01:
            continue

        lx = int(28 - 220 * (1.0 - c_p))
        ly = 45 + idx * step_h - int(font_sz * 0.14)

        if idx < split_idx:
            col = (34, 152, 236, int(248 * c_p))
        else:
            col = (232, 96, 36, int(248 * c_p))

        # Crisp drop shadow + bold letter
        td.text((lx + 5, ly + 7), ch_str, font=f_vert, fill=(0, 0, 0, int(155 * c_p)))
        td.text((lx, ly), ch_str, font=f_vert, fill=col)

    canvas.alpha_composite(txt_layer)

    # Optional center-right kinetic caption cues during longer postcard spans
    for c_start, c_end, lead, hero in caption_cues:
        if c_start <= t < c_end:
            draw_ref10_lockup(
                canvas,
                age=t - c_start,
                lead_text=lead,
                hero_text=hero,
                cy=1360,
                hero_color=(255, 226, 44),
                echo_trail=False,
            )
            break

    return canvas


# ---------------------------------------------------------------------------
# Dark Split-Card Rounded Window + 3D Winding Staircase & Tower Cutout
# (Exact match to t=14.10s - 17.05s in reference 10.mp4!)
# ---------------------------------------------------------------------------
def draw_3d_winding_staircase(
    canvas: Image.Image,
    age: float,
    bottom_label: str,
    top_hero_word: str,
    top_sub_text: str,
):
    """
    Renders the 3D winding white architectural staircase from bottom-left (x=210, y=1700)
    spiraling through an S-curve up to the bottom of the speaker's rounded window (y=885),
    with a minimalist architectural figure climbing from `bottom_label` to glowing
    yellow-gold `top_hero_word` (matching "junior" -> "director" at t=14.10s-15.50s of ref10).
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # S-curve centerline points from bottom-left up to top-center-right
    n_steps = 22
    build_p = cubic_bezier_cool(age / 0.68)
    visible_steps = int(round(n_steps * build_p))

    pts = []
    for i in range(n_steps):
        u = i / float(n_steps - 1)
        # S-curve trajectory matching reference 10.mp4
        cx = 230 + 480 * u + 195 * math.sin(u * math.pi * 1.85 - 0.35)
        cy = 1715 - 815 * (u ** 0.92)
        w_step = int(round(135 * (1.0 - 0.32 * u)))
        pts.append((cx, cy, w_step, u))

    # Soft white glow under the staircase
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(min(visible_steps, len(pts) - 1)):
        cx, cy, ws, _ = pts[i]
        nx, ny, nws, _ = pts[i + 1]
        poly = [(cx - ws, cy), (cx + ws, cy), (nx + nws, ny), (nx - nws, ny)]
        gd.polygon(poly, fill=(220, 225, 235, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=24))
    layer.alpha_composite(glow)

    # Draw 3D risers and treads from top to bottom or bottom to top
    for i in range(visible_steps):
        cx, cy, ws, u = pts[i]
        tread_h = 18
        riser_h = 22
        x0, x1 = int(cx - ws), int(cx + ws)
        y0 = int(cy)
        # Dark 3D riser face
        d.rectangle([x0, y0, x1, y0 + tread_h + riser_h], fill=(58, 62, 68, 245), outline=(110, 115, 124, 255), width=1)
        # Bright 3D top tread face
        d.polygon(
            [(x0, y0), (x1, y0), (x1 + 10, y0 - tread_h), (x0 + 10, y0 - tread_h)],
            fill=(232, 235, 242, 255),
            outline=(145, 150, 160, 255),
        )

    # Minimalist architectural person silhouette standing on step 2 (bottom-left)
    if build_p > 0.18:
        fig_a = int(255 * cubic_bezier_cool((age - 0.10) / 0.35))
        fx, fy = int(pts[1][0] - 42), int(pts[1][1] - 12)
        # Head
        d.ellipse([fx - 12, fy - 128, fx + 12, fy - 104], fill=(225, 228, 235, fig_a))
        # Torso + coat silhouette
        d.polygon(
            [(fx - 18, fy - 100), (fx + 18, fy - 100), (fx + 22, fy - 44), (fx - 22, fy - 44)],
            fill=(165, 170, 178, fig_a),
        )
        # Legs climbing
        d.line([(fx - 8, fy - 44), (fx - 14, fy)], fill=(210, 214, 222, fig_a), width=8)
        d.line([(fx + 8, fy - 44), (fx + 16, fy - 12)], fill=(210, 214, 222, fig_a), width=8)

        # Bottom label ("helper" / "technical") right above the figure
        f_bot = get_font(INTER_REG, 44)
        d.text((fx - 38, fy - 245), bottom_label, font=f_bot, fill=(195, 200, 210, fig_a))

    canvas.alpha_composite(layer)

    # Top glowing yellow-gold hero word ("awareness" / "management") right under the speaker window
    if age > 0.32:
        draw_ref10_lockup(
            canvas,
            age=age - 0.32,
            lead_text="",
            hero_text=top_hero_word,
            script_text="",
            sub_text=top_sub_text,
            cy=905,
            hero_color=(255, 226, 44),
            echo_trail=False,
        )


def render_dark_split_window_scene(
    raw_rgb: np.ndarray,
    t: float,
    t_start: float,
    t_mid: float,
    t_end: float,
    stair_bottom_label: str,
    stair_top_hero: str,
    stair_top_sub: str,
    tower_lead: str,
    tower_hero: str,
    tower_script: str,
) -> Image.Image:
    # Deep matte charcoal-black canvas (#0E0E11) matching reference 10.mp4 t=14.10s-17.05s
    canvas = Image.new("RGBA", (W, H), (14, 14, 17, 255))

    # Grade speaker frame and place inside upper rounded square window (760x700 at x=160, y=175)
    graded = grade_talking_head(raw_rgb, t, zoom=1.12)
    win_w, win_h = 760, 700
    win_x, win_y = (W - win_w) // 2, 175

    # Crop centered on Paul's head & upper shoulders
    crop_box = ((W - win_w) // 2, 140, (W + win_w) // 2, 140 + win_h)
    win_im = graded.crop(crop_box)

    # Smooth morph-in from full screen during first 0.28s
    age_total = t - t_start
    morph_p = cubic_bezier_cool(age_total / 0.28)
    cur_w = int(round(W + (win_w - W) * morph_p))
    cur_h = int(round(H + (win_h - H) * morph_p))
    cur_x = (W - cur_w) // 2
    cur_y = int(round(win_y * morph_p))
    cur_rad = int(round(48 * morph_p))

    if (cur_w, cur_h) != (win_w, win_h):
        win_im_scaled = graded.resize((cur_w, cur_h), Image.BILINEAR)
    else:
        win_im_scaled = win_im

    mask = Image.new("L", (cur_w, cur_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, cur_w - 1, cur_h - 1], radius=cur_rad, fill=255)

    win_card = Image.new("RGBA", (cur_w, cur_h), (0, 0, 0, 0))
    win_card.paste(win_im_scaled, (0, 0), mask)
    canvas.alpha_composite(win_card, (cur_x, cur_y))

    if t < t_mid:
        # Phase A: 3D Winding Staircase metaphor below the rounded window
        draw_3d_winding_staircase(
            canvas,
            age=t - t_start,
            bottom_label=stair_bottom_label,
            top_hero_word=stair_top_hero,
            top_sub_text=stair_top_sub,
        )
    else:
        # Phase B: Bottom-Left Monochrome Architectural Tower Cutout + 3-tier Lock-up
        # (Exact match to t=15.60s - 17.05s in reference 10.mp4!)
        p_age = t - t_mid
        tower_p = cubic_bezier_cool(p_age / 0.42)
        tower = get_assets()["tower_cutout"]
        tx = int(-260 * (1.0 - tower_p))
        ty = int(H - tower.height + 140 * (1.0 - tower_p))
        canvas.alpha_composite(tower, (tx, ty))

        draw_ref10_lockup(
            canvas,
            age=p_age,
            lead_text=tower_lead,
            hero_text=tower_hero,
            script_text=tower_script,
            cy=965,
            hero_color=(255, 226, 44),
            echo_trail=False,
        )

    return canvas


# ---------------------------------------------------------------------------
# Finale Scene (51.80s - 54.85s): Real Studio Table B-Roll with 4-Slice Entrance
# & "Peak Architects" Glowing Gold + Calligraphic Script Lock-up
# ---------------------------------------------------------------------------
def render_studio_finale(raw_rgb: np.ndarray, t: float) -> Image.Image:
    age = t - 51.80
    graded = grade_talking_head(raw_rgb, t, zoom=1.0)

    # 4-slice vertical accordion entrance over the first 0.55s
    if age < 0.65:
        dark_bg = Image.new("RGBA", (W, H), (14, 14, 17, 255))
        p = clamp(age / 0.62)
        canvas = composite_4slice_transition(dark_bg, graded, p, direction="up_down")
    else:
        canvas = graded

    draw_ref10_lockup(
        canvas,
        age=max(0.0, age - 0.18),
        lead_text="driving the",
        hero_text="Design",
        script_text="process",
        cy=1380,
        hero_color=(255, 226, 44),
        echo_trail=True,
    )
    return canvas


# ---------------------------------------------------------------------------
# Master Frame Dispatcher (0.00s - 54.85s)
# ---------------------------------------------------------------------------
SCENE2_WORDS = [
    (3.75, 4.45, "at a local"),
    (4.45, 5.35, "technical"),
    (5.35, 6.25, "college"),
    (6.25, 6.95, "and"),
    (6.95, 7.45, "was"),
]

SCENE3B_CAPTIONS = [
    (10.85, 12.25, "when I was", "Young"),
    (12.25, 14.10, "in the summer", "Holidays"),
]

SCENE6_WORDS = [
    (26.95, 27.65, "happened"),
    (27.65, 28.35, "upon"),
    (28.35, 29.15, "the term"),
    (29.15, 30.05, "architect"),
    (30.05, 30.85, "without"),
    (30.85, 31.55, "knowing"),
]

SCENE7B_CAPTIONS = [
    (35.85, 37.15, "technical", "Skills"),
    (37.15, 38.40, "having both", "Sides"),
]


def _render_scene_layer(raw_rgb: np.ndarray, t: float) -> Image.Image:
    # Scene 2 (3.65s - 8.35s): 4-Slice Vertical Accordion Architectural Evolution #1
    if 3.65 <= t < 8.35:
        return render_4slice_accordion_scene(
            t,
            t_start=3.65,
            t_end=8.35,
            stage_keys=("stage1_concrete", "stage2_sketch", "stage3_atrium"),
            word_cues=SCENE2_WORDS,
            climax_word="College",
        )

    # Scene 3B (10.15s - 14.15s): Full-Screen Vertical Stacked Typography Postcard ("S-I-T-E-S")
    if 10.15 <= t < 14.15:
        return render_vertical_postcard_scene(
            t,
            t_start=10.15,
            t_end=14.15,
            bg_key="postcard_shard",
            vertical_word="SITES",
            caption_cues=SCENE3B_CAPTIONS,
        )

    # Scene 4 (14.15s - 20.55s): Dark Split-Card Rounded Window + 3D Winding Staircase & Tower Cutout
    if 14.15 <= t < 20.55:
        return render_dark_split_window_scene(
            raw_rgb,
            t,
            t_start=14.15,
            t_mid=17.35,
            t_end=20.55,
            stair_bottom_label="helper",
            stair_top_hero="awareness",
            stair_top_sub="early building",
            tower_lead="construction",
            tower_hero="Process",
            tower_script="building",
        )

    # Scene 6 (26.85s - 32.50s): 4-Slice Vertical Accordion Architectural Evolution #2
    if 26.85 <= t < 32.50:
        return render_4slice_accordion_scene(
            t,
            t_start=26.85,
            t_end=32.50,
            stage_keys=("stage2_mono_atrium", "stage2_sketch", "stage2_model"),
            word_cues=SCENE6_WORDS,
            climax_word="Architect",
        )

    # Scene 7B (35.30s - 38.45s): Full-Screen Vertical Stacked Typography Postcard ("D-E-S-I-G-N")
    if 35.30 <= t < 38.45:
        return render_vertical_postcard_scene(
            t,
            t_start=35.30,
            t_end=38.45,
            bg_key="postcard_timber",
            vertical_word="DESIGN",
            caption_cues=SCENE7B_CAPTIONS,
        )

    # Scene 8 (38.45s - 46.80s): Dark Split-Card Rounded Window #2 + 3D Winding Staircase & Tower Cutout
    if 38.45 <= t < 46.80:
        return render_dark_split_window_scene(
            raw_rgb,
            t,
            t_start=38.45,
            t_mid=42.65,
            t_end=46.80,
            stair_bottom_label="technical",
            stair_top_hero="management",
            stair_top_sub="role as well",
            tower_lead="driving the",
            tower_hero="Process",
            tower_script="appealed",
        )

    # Scene 9B (51.80s - 54.85s): Studio Finale
    if t >= 51.80:
        return render_studio_finale(raw_rgb, t)

    # Default: Talking Head with Glowing Yellow-Gold Captions, Golden Halftone & Script Overlays
    return render_talking_head_scene(raw_rgb, t)


# Velocity-matched seam windows (`cut-the-curve/SKILL.md` + `examples/gsap-implementation.md`)
SEAM_WINDOWS = [
    (8.35, 0.36, "inverse_zoom"),
    (14.15, 0.34, "cut_left"),
    (20.55, 0.34, "rack_focus"),
    (32.50, 0.36, "inverse_zoom"),
    (38.45, 0.34, "cut_left"),
    (46.80, 0.34, "rack_focus"),
]


def render_frame(raw_rgb: np.ndarray, t: float) -> np.ndarray:
    for cut_t, half_w, seam_kind in SEAM_WINDOWS:
        t0, t1 = cut_t - half_w * 0.40, cut_t + half_w * 0.60
        if t0 <= t <= t1:
            p = (t - t0) / (t1 - t0)
            old_im = _render_scene_layer(raw_rgb, cut_t - 0.04)
            new_im = _render_scene_layer(raw_rgb, max(cut_t + 0.02, t))
            if seam_kind == "inverse_zoom":
                out = zoom_through_seam(old_im, new_im, p, inverse=True)
            elif seam_kind == "cut_left":
                out = cut_the_curve_seam(old_im, new_im, p, direction="left")
            else:
                out = rack_focus_blur_cut(old_im, new_im, p)
            return np.array(out.convert("RGB"))

    out = _render_scene_layer(raw_rgb, t)
    return np.array(out.convert("RGB"))


# ---------------------------------------------------------------------------
# Preview Contact Sheet & Full MP4 Encoder
# ---------------------------------------------------------------------------
def build_preview_grid(raw_video_path: str, out_jpg_path: str):
    preview_times = [
        0.40, 1.35, 2.40, 3.25,
        4.10, 5.20, 6.60, 7.95,
        9.25, 9.95, 10.65, 12.60,
        14.85, 16.20, 18.20, 19.60,
        21.30, 25.40, 27.60, 29.50, 32.00,
        34.30, 35.05, 36.40, 40.20, 44.20,
        50.20, 53.10,
    ]
    thumbs = []
    for t in preview_times:
        raw_cmd = [
            "ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", raw_video_path,
            "-frames:v", "1", "-vf", f"scale={W}:{H}",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
        ]
        raw_bytes = subprocess.check_output(raw_cmd)
        raw_rgb = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((H, W, 3))
        comp_rgb = render_frame(raw_rgb, t)
        im = Image.fromarray(comp_rgb).resize((270, 480), Image.BILINEAR)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 115, 30], fill=(0, 0, 0))
        d.text((8, 7), f"t={t:.2f}s", fill=(0, 255, 200))
        thumbs.append(im)

    cols = 7
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
        "ffmpeg", "-v", "error", "-i", raw_video_path,
        "-vf", f"scale={W}:{H}", "-r", str(FPS),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"
    ]
    enc_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-", "-i", audio_wav_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        out_mp4_path
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
    parser.add_argument("--raw", default="/home/user/COOL-backup/video brut 10.mp4")
    parser.add_argument("--audio", default="/tmp/work_cache/felix_ref10_audio.wav")
    parser.add_argument(
        "--out",
        default="/home/user/COOL-backup/felix-gray-reference10/film/felix-gray-reference10-9x16.mp4",
    )
    parser.add_argument("--preview", default="")
    args = parser.parse_args()

    if args.preview:
        build_preview_grid(args.raw, args.preview)
    else:
        render_full_video(args.raw, args.audio, args.out)
