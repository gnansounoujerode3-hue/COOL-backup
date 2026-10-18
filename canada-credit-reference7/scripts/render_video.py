#!/usr/bin/env python3
"""
Master 9:16 (1080x1920, 30fps) Video Editor for:
Raw Video: `imports/AQNIjRAr6B_rpxG_wzm3pn0pqMSSszClolTOsw76yoX7UOh-zXRCqq06eAMqeJpIodAvFY71EYRLXsxIrLyfOJk4v976706AUNDQXx4.mp4`
Reference: `reference 7.mp4`

Implements all user instructions:
1. Isolated, noise-free, broadcast-equalized voice slightly accelerated (x1.07) to dynamize pacing (68.50s -> 64.02s).
2. Motivating, trending 120 BPM dynamic background beat (0.50s per beat, 2.00s per bar) with sidechain ducking.
3. Subtle, punchy SFX (`whoosh`, `pop`, `click`, `ding`) synced to transitions, text reveals, and zooms.
4. Progressive Ken Burns zooms + fast transitions (`whip pan`, `RGB glitch`, `zoom-in`).
5. Beat-locked B-Rolls & B-Roll Overlays snapped to the 120 BPM musical grid (0.50s / 1.00s intervals).
6. Custom animations directly illustrating what the speaker says (3,000$ Credit Card approval with 0$, multiplying 2,500$ -> 5,000$, Cour des Grands, Repartir de Zéro, Canada Système de Dette vs France Découvert, Credit Score crash: Pas de Maison / Pas de Voiture) in the exact visual language of `reference 7.mp4` (Electric Cobalt Blue `#2558FF`, Crimson `#FF2442`, 3D UI Cards, Dual Neon Circular Badges, Shattering Emblem, and Montserrat + Mr Dafoe script typography, max 2 lines).
"""

import json
import math
import os
import subprocess
import sys
import wave
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from scipy import signal

REPO_ROOT = "/home/user/COOL-backup"
sys.path.insert(0, f"{REPO_ROOT}/.claude/skills/motion-code-harvester/scripts")
sys.path.insert(0, f"{REPO_ROOT}/.claude/skills/animation-design-rules/scripts")

from motion_engine import (
    clamp,
    zoom_through_seam,
    cut_the_curve_seam,
)
from animation_rules_engine import (
    emil_ease_out,
    emil_ease_in_out,
    disney_overshoot_ease,
    disney_follow_through_layers,
)

RAW_MP4 = f"{REPO_ROOT}/imports/AQNIjRAr6B_rpxG_wzm3pn0pqMSSszClolTOsw76yoX7UOh-zXRCqq06eAMqeJpIodAvFY71EYRLXsxIrLyfOJk4v976706AUNDQXx4.mp4"
SPEED_MP4 = "/tmp/ref7_inspect/raw_107x.mp4"
PROJECT_DIR = f"{REPO_ROOT}/canada-credit-reference7"
FILM_DIR = f"{PROJECT_DIR}/film"
OUT_MP4 = f"{FILM_DIR}/canada-credit-reference7-9x16.mp4"

BROLL_SKYLINE = f"{REPO_ROOT}/felix-gray-reference10/assets/broll/broll_shard_skyline.mp4"
BROLL_ATRIUM = f"{REPO_ROOT}/felix-gray-reference10/assets/broll/broll_timber_atrium.mp4"
BROLL_TWILIGHT = f"{REPO_ROOT}/felix-gray-reference10/assets/broll/broll_stage3_twilight_atrium.mp4"

W, H = 1080, 1920
FPS = 30.0
SPEED_FACTOR = 1.07
BPM = 120.0
BEAT_SEC = 60.0 / BPM  # 0.50s exact per beat

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
F_MONT_REG = f"{FONT_BASE}/montserrat/400Regular/Montserrat_400Regular.ttf"
F_MONT_SEMI = f"{FONT_BASE}/montserrat/600SemiBold/Montserrat_600SemiBold.ttf"
F_MONT_BOLD = f"{FONT_BASE}/montserrat/700Bold/Montserrat_700Bold.ttf"
F_MONT_EBOLD = f"{FONT_BASE}/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf"
F_MONT_BLACK = f"{FONT_BASE}/montserrat/900Black/Montserrat_900Black.ttf"
F_DAFOE = f"{FONT_BASE}/mr-dafoe/400Regular/MrDafoe_400Regular.ttf"
F_MONO = f"{FONT_BASE}/dm-mono/500Medium/DMMono_500Medium.ttf"

# `reference 7.mp4` Color Palette (RGB)
C_COBALT = (37, 88, 255)        # #2558FF Electric Cobalt Blue from reference 7.mp4
C_COBALT_LIGHT = (88, 148, 255) # #5894FF Neon Blue Glow
C_COBALT_DEEP = (14, 34, 115)   # #0E2273 Deep Royal Blue
C_CRIMSON = (255, 36, 66)       # #FF2442 Signature Crimson Red from reference 7.mp4 (t=15.3s)
C_EMERALD = (16, 215, 138)      # #10D78A Bank Approval Green
C_GOLD = (250, 188, 42)         # #FABC2A Gold Card Chip / Crown
C_SILVER = (198, 208, 228)      # #C6D0E4 Muted Silver-Blue Subtitle Ink
C_DARK_BG = (6, 9, 18)          # #060912 Obsidian Studio Background

_FONT_CACHE = {}
_STATIC_CACHE = {}
_BROLL_CACHE = {}


def get_font(path: str, size: int):
    size = max(12, int(round(size)))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def fit_font(path: str, text: str, target_size: int, max_w: int = 940):
    sz = target_size
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    while sz > 28:
        f = get_font(path, sz)
        if d.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        sz -= 3
    return get_font(path, sz)


# ---------------------------------------------------------------------------
# Curated French Subtitles (Strictly <= 2 Lines, locked to 1.07x timeline)
# Every segment has `style` ('blue_script', 'bold_impact', 'crimson_script')
# matching `reference 7.mp4` chest-level dual-font typography!
# ---------------------------------------------------------------------------
SEGMENTS = [
    (0.00, 1.50, "C'est quoi le plus fou", "au Canada ?", "blue_script"),
    (1.50, 3.50, "T'arrives là-bas,", "t'as pas un rond.", "bold_impact"),
    (3.50, 5.50, "Tu vas à la banque,", "n'importe laquelle,", "blue_script"),
    (5.50, 7.80, "tu demandes une", "carte de crédit,", "bold_impact"),
    (7.80, 10.80, "ils te passent direct", "3 000 $ !", "blue_script"),
    (10.80, 14.80, "Minimum 2 500 $", "sans aucun argent.", "bold_impact"),
    (14.80, 16.00, "Ils te passent", "la carte.", "blue_script"),
    (16.00, 18.50, "Si t'es intelligent,", "tu les multiplies !", "blue_script"),
    (18.50, 21.16, "Dès mes premiers jours", "au Canada,", "bold_impact"),
    (21.16, 23.50, "j'ai eu 2 500 $,", "je l'ai doublée !", "blue_script"),
    (23.50, 26.60, "Mon crédit est passé", "de 2 500 à 5 000 $,", "bold_impact"),
    (26.60, 29.40, "et plus tu gères bien,", "plus ils augmentent.", "blue_script"),
    (29.40, 31.00, "De l'argent qui", "t'appartient pas,", "bold_impact"),
    (31.00, 34.00, "et tu rentres dans", "la cour des grands !", "blue_script"),
    (34.00, 36.60, "Le Canada te permet", "de repartir de zéro,", "crimson_script"),
    (36.60, 37.80, "même avec", "rien du tout.", "crimson_script"),
    (37.80, 39.80, "Il y a une vraie", "différence de mentalité :", "bold_impact"),
    (39.80, 41.40, "Là-bas t'as rien,", "", "bold_impact"),
    (41.40, 42.50, "mais t'as", "tout !", "blue_script"),
    (42.50, 44.80, "Ils ont un vrai", "système de dette,", "bold_impact"),
    (44.80, 46.50, "ils s'enrichissent", "grâce aux dettes,", "blue_script"),
    (46.50, 49.00, "alors qu'en France,", "c'est le découvert !", "crimson_script"),
    (49.00, 51.00, "Quand tu viens au Canada", "sans argent,", "bold_impact"),
    (51.00, 53.20, "va à la banque,", "demande ta carte,", "blue_script"),
    (53.20, 55.40, "ils te donnent un crédit", "et c'est toi qui gères.", "bold_impact"),
    (55.40, 56.50, "Mais gère-le", "correctement !", "blue_script"),
    (56.50, 59.20, "Car si tu gères mal", "et ton crédit baisse :", "crimson_script"),
    (59.20, 62.20, "pas de maison, pas d'auto,", "t'as tout ruiné.", "crimson_script"),
    (62.20, 64.02, "Voilà la famille,", "abonnez-vous !", "blue_script"),
]

# ---------------------------------------------------------------------------
# Beat-Locked Full-Screen B-Roll & Motion Cutaways (Snapped to 120 BPM = 0.50s grid)
# ---------------------------------------------------------------------------
# (t_start, t_end, cutaway_id, transition_in, transition_out)
CUTAWAY_WINDOWS = [
    (8.00, 12.00, 1, "zoom_in", "whip_pan"),      # Beats 16..24: 3D Laptop/Bank Card Approval 3,000$ (`reference 7.mp4` t=5.4s style)
    (21.50, 26.50, 2, "whip_pan", "glitch"),      # Beats 43..53: Skyline B-Roll + 2,500$ -> 5,000$ Doubling Chart
    (34.00, 38.00, 3, "zoom_in", "whip_pan"),     # Beats 68..76: Crimson Glow 'REPARTIR DE ZÉRO / même avec rien' (`reference 7.mp4` t=15.3s style)
    (42.50, 49.00, 4, "glitch", "zoom_in"),       # Beats 85..98: Canada Système de Dette (B-Roll) vs France Découvert (Shattering Emblem t=12.9s)
    (56.50, 62.00, 5, "whip_pan", "glitch"),      # Beats 113..124: Credit Score Plunge + Shattering House & Car Icons (`reference 7.mp4` t=12.9s)
]

# Beat-Locked B-Roll Overlays on A-Roll (Snapped to 120 BPM = 0.50s grid)
# Matches `reference 7.mp4` `t=20.3s` Dual Glowing Neon Circular Badges & Floating 3D Cards!
BROLL_OVERLAY_WINDOWS = [
    (3.50, 7.50, "bank_card_request"),   # Beats 7..15: Floating 3D Bank & Credit Card Request Overlay
    (16.00, 18.50, "multiply_badges"),   # Beats 32..37: Dual Neon Circular Badges (`2 500 $` -> `x2 MULTIPLIER`)
    (31.00, 34.00, "cour_des_grands"),   # Beats 62..68: Dual Neon Circular Badges (`RISQUE BANQUE` -> `COUR DES GRANDS`)
    (39.80, 42.50, "rien_mais_tout"),    # Beats 80..85: Dual Contrast Badges (`0 $ EN POCHE` -> `100% OPPORTUNITÉ`)
    (51.00, 56.00, "three_steps_plan"),  # Beats 102..112: Beat-Synced 3-Step Action Pills (`1. BANQUE`, `2. CARTE`, `3. GÉRER`)
]

# Fast Punch-Zoom Windows on A-Roll
PUNCH_ZOOM_WINDOWS = [
    (0.00, 1.50, 1.12),
    (5.50, 7.80, 1.13),
    (15.80, 18.50, 1.14),
    (31.00, 34.00, 1.13),
    (39.80, 42.50, 1.15),
    (55.00, 56.50, 1.14),
    (62.20, 64.02, 1.12),
]


def ensure_speed_video():
    if os.path.exists(SPEED_MP4) and os.path.getsize(SPEED_MP4) > 1000000:
        return
    os.makedirs(os.path.dirname(SPEED_MP4), exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ff, "-y", "-i", RAW_MP4,
            "-filter_complex", f"[0:v]setpts=PTS/{SPEED_FACTOR},fps=30[v];[0:a]atempo={SPEED_FACTOR}[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16",
            "-c:a", "aac", "-b:a", "192k",
            SPEED_MP4,
        ],
        check=True,
        capture_output=True,
    )


def get_graded_broll_frame(path: str, local_t: float, tint: str = "cobalt") -> Image.Image:
    """Loads and grades real HD B-Roll video clips in `reference 7.mp4` Cobalt-Noir or Crimson-Noir LUT with a tiny RAM footprint."""
    key = (path, tint)
    if key not in _BROLL_CACHE:
        frames = []
        if os.path.exists(path):
            cap = cv2.VideoCapture(path)
            step = 0
            while len(frames) < 40:
                ok, f = cap.read()
                if not ok:
                    break
                step += 1
                if step % 2 != 0:
                    continue
                fh, fw = f.shape[:2]
                tw = int(round(fh * (W / H)))
                if tw <= fw:
                    x0 = (fw - tw) // 2
                    f = f[:, x0 : x0 + tw]
                # Store at 360x640 RGB (~690 KB/frame) and upscale on demand to save 3.6 GB RAM
                f_res = cv2.resize(f, (360, 640), interpolation=cv2.INTER_AREA)
                rgb = cv2.cvtColor(f_res, cv2.COLOR_BGR2RGB).astype(np.float32) * 0.38
                if tint == "cobalt":
                    rgb[:, :, 0] = np.clip(rgb[:, :, 0] * 0.65 + 6.0, 0, 255)
                    rgb[:, :, 1] = np.clip(rgb[:, :, 1] * 0.88 + 14.0, 0, 255)
                    rgb[:, :, 2] = np.clip(rgb[:, :, 2] * 1.45 + 36.0, 0, 255)
                else:
                    rgb[:, :, 0] = np.clip(rgb[:, :, 0] * 1.45 + 34.0, 0, 255)
                    rgb[:, :, 1] = np.clip(rgb[:, :, 1] * 0.65 + 8.0, 0, 255)
                    rgb[:, :, 2] = np.clip(rgb[:, :, 2] * 0.80 + 14.0, 0, 255)
                frames.append(rgb.astype(np.uint8))
            cap.release()
        _BROLL_CACHE[key] = frames

    frames = _BROLL_CACHE[key]
    if not frames:
        return Image.new("RGBA", (W, H), (*C_DARK_BG, 255))
    idx = int(local_t * 15.0) % len(frames)
    up = cv2.resize(frames[idx], (W, H), interpolation=cv2.INTER_LINEAR)
    return Image.fromarray(up, mode="RGB").convert("RGBA")


# ---------------------------------------------------------------------------
# 1. `reference 7.mp4` A-Roll Lighting Grade & Progressive Ken Burns Camera
# ---------------------------------------------------------------------------
def get_ref7_grade_overlay() -> Image.Image:
    if "ref7_grade" in _STATIC_CACHE:
        return _STATIC_CACHE["ref7_grade"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Top-center Cobalt-Blue studio ambient glow (`reference 7.mp4` signature)
    d_top = np.sqrt(((xx - W * 0.50) / 520.0) ** 2 + ((yy - H * 0.20) / 340.0) ** 2)
    blue_glow = (np.clip(1.0 - d_top, 0.0, 1.0) ** 2.2) * 0.22

    # Smooth dark gradient on lower third (`y=1120..1920`) so chest-level subtitles pop cleanly
    bottom_dark = (np.clip((yy - H * 0.56) / (H * 0.44), 0.0, 1.0) ** 1.35) * 0.68
    edge_vig = np.clip(((xx - W * 0.5) / (W * 0.52)) ** 2 + ((yy - H * 0.5) / (H * 0.52)) ** 2 - 0.38, 0.0, 1.0) * 0.28

    dark_a = np.clip(bottom_dark + edge_vig, 0.0, 0.76)
    total_a = np.clip(dark_a + blue_glow, 0.001, 0.80)
    w_blue = blue_glow / total_a

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[:, :, 0] = np.clip(w_blue * 28.0 + (1.0 - w_blue) * 4.0, 0, 255).astype(np.uint8)
    rgba[:, :, 1] = np.clip(w_blue * 78.0 + (1.0 - w_blue) * 7.0, 0, 255).astype(np.uint8)
    rgba[:, :, 2] = np.clip(w_blue * 245.0 + (1.0 - w_blue) * 18.0, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(total_a * 255.0, 0, 255).astype(np.uint8)

    im = Image.fromarray(rgba, mode="RGBA")
    _STATIC_CACHE["ref7_grade"] = im
    return im


def prepare_aroll_frame(bgr: np.ndarray, t: float) -> Image.Image:
    """
    Upscales 720x1280 A-Roll to 1080x1920 with:
    - Progressive Ken Burns zoom (`1.01x -> 1.09x`) + fast punch-zooms on key beats
    - Subtle beat-synced micro-pulse on 120 BPM kicks
    - `reference 7.mp4` Cobalt-Blue studio glow & dark lower-chest vignette
    """
    # Progressive Ken Burns drift + fast punch-zoom windows
    kb_cycle = (t % 8.0) / 8.0
    kb_zoom = 1.015 + 0.065 * (kb_cycle if kb_cycle < 0.5 else (1.0 - kb_cycle)) * 2.0

    for z_start, z_end, z_val in PUNCH_ZOOM_WINDOWS:
        if z_start <= t <= z_end:
            p_in = emil_ease_out(clamp((t - z_start) / 0.22))
            p_out = emil_ease_out(clamp((z_end - t) / 0.25)) if (z_end - t) < 0.25 else 1.0
            kb_zoom = max(kb_zoom, 1.0 + (z_val - 1.0) * min(p_in, p_out))
            break

    # Subtle 120 BPM beat pulse (+0.6% on kick)
    beat_phase = (t % BEAT_SEC) / BEAT_SEC
    beat_pulse = 0.006 * math.exp(-beat_phase * 9.0)
    zoom = kb_zoom + beat_pulse

    fh, fw = bgr.shape[:2]
    ch = int(round(fh / zoom))
    cw = int(round(fw / zoom))
    x0 = (fw - cw) // 2
    y0 = int(round((fh - ch) * 0.42))
    cropped = bgr[y0 : y0 + ch, x0 : x0 + cw]
    resized = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_CUBIC)

    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb)
    im = ImageEnhance.Contrast(im).enhance(1.10)
    im = ImageEnhance.Color(im).enhance(1.06)
    im = im.convert("RGBA")
    im = Image.alpha_composite(im, get_ref7_grade_overlay())
    return im


# ---------------------------------------------------------------------------
# 2. `reference 7.mp4` Chest-Level Dual-Font Subtitles (Strictly <= 2 Lines)
# ---------------------------------------------------------------------------
def draw_glow_text(canvas: Image.Image, text: str, cx: int, cy: int, font, fill_rgb: tuple, glow_rgb: tuple = None, alpha: float = 1.0):
    if alpha <= 0.02 or not text:
        return
    d = ImageDraw.Draw(canvas)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = cx - tw // 2
    ty = cy - th // 2 - bb[1]

    if glow_rgb is not None:
        g_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g_im)
        gd.text((tx, ty), text, font=font, fill=(*glow_rgb, int(185 * alpha)), stroke_width=6, stroke_fill=(*glow_rgb, int(145 * alpha)))
        g_im = g_im.filter(ImageFilter.GaussianBlur(radius=14))
        canvas.alpha_composite(g_im)
        d = ImageDraw.Draw(canvas)

    # Crisp dark drop-shadow + stroke
    d.text((tx + 3, ty + 5), text, font=font, fill=(0, 0, 0, int(195 * alpha)), stroke_width=6, stroke_fill=(0, 0, 0, int(195 * alpha)))
    d.text((tx, ty), text, font=font, fill=(*fill_rgb, int(255 * alpha)), stroke_width=3, stroke_fill=(8, 12, 24, int(230 * alpha)))


def overlay_ref7_subtitles(canvas: Image.Image, t: float, in_cutaway: bool = False):
    """
    Renders strict <= 2-line French subtitles in the exact `reference 7.mp4` style:
    - Line 1: Clean Montserrat SemiBold / ExtraBold
    - Line 2: Either glowing Electric Cobalt-Blue / Crimson-Red script (`Mr Dafoe`) OR huge `Montserrat Black` with neon glow!
    """
    for t0, t1, l1, l2, style in SEGMENTS:
        if t0 <= t < t1:
            age = t - t0
            rem = t1 - t
            p_in = emil_ease_out(clamp(age / 0.16))
            p_out = clamp(rem / 0.10) if rem < 0.10 else 1.0
            alpha = min(p_in, p_out)
            dy = int(round(20.0 * (1.0 - p_in)))

            base_y = 1525 if in_cutaway else 1445
            if not l2:
                f1 = fit_font(F_MONT_BLACK, l1, 68, max_w=940)
                draw_glow_text(canvas, l1, W // 2, base_y + dy, f1, (255, 255, 255), glow_rgb=C_COBALT, alpha=alpha)
                return

            if style == "blue_script":
                # Matches `t=17.8s` ("We built the / Revenue / Rhythm") & `t=27.7s` ("Comment / 'Rhythm'"):
                f1 = fit_font(F_MONT_BOLD, l1, 46, max_w=920)
                draw_glow_text(canvas, l1, W // 2, base_y - 45 + dy, f1, C_SILVER, alpha=alpha)
                has_digits = any(ch.isdigit() for ch in l2)
                if len(l2) <= 20 and not has_digits:
                    f2 = fit_font(F_DAFOE, l2, 86, max_w=940)
                    draw_glow_text(canvas, l2, W // 2, base_y + 42 + dy, f2, C_COBALT_LIGHT, glow_rgb=C_COBALT, alpha=alpha)
                else:
                    f2 = fit_font(F_MONT_BLACK, l2, 64, max_w=940)
                    draw_glow_text(canvas, l2, W // 2, base_y + 38 + dy, f2, C_COBALT_LIGHT, glow_rgb=C_COBALT, alpha=alpha)

            elif style == "crimson_script":
                # Matches `t=15.3s` ("most agencies / can't help" in glowing Crimson Red)
                f1 = fit_font(F_MONT_BOLD, l1, 46, max_w=920)
                draw_glow_text(canvas, l1, W // 2, base_y - 45 + dy, f1, (255, 255, 255), alpha=alpha)
                f2 = fit_font(F_MONT_BLACK, l2, 60, max_w=940)
                draw_glow_text(canvas, l2, W // 2, base_y + 38 + dy, f2, C_CRIMSON, glow_rgb=C_CRIMSON, alpha=alpha)

            else:
                # 'bold_impact': Matches `t=0.5s` & `t=3.0s` (Clean Silver + Huge White Montserrat Black)
                f1 = fit_font(F_MONT_SEMI, l1, 44, max_w=920)
                f2 = fit_font(F_MONT_BLACK, l2, 62, max_w=940)
                draw_glow_text(canvas, l1, W // 2, base_y - 45 + dy, f1, C_SILVER, alpha=alpha)
                draw_glow_text(canvas, l2, W // 2, base_y + 38 + dy, f2, (255, 255, 255), glow_rgb=C_COBALT, alpha=alpha)
            return


# ---------------------------------------------------------------------------
# 3. Beat-Locked B-Roll Overlays on A-Roll (`reference 7.mp4` `t=20.3s` style)
# ---------------------------------------------------------------------------
def draw_neon_circle_badge(canvas: Image.Image, cx: int, cy: int, radius: int, icon_type: str, label: str, sub: str, p: float, color: tuple = C_COBALT):
    """Renders the signature glowing Cobalt-Blue circular neon icon badge from `t=20.3s` of `reference 7.mp4`."""
    if p <= 0.02:
        return
    r = int(round(radius * p))
    if r < 12:
        return

    # Outer neon bloom
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=(*color, int(115 * p)), outline=(*color, int(220 * p)), width=6)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=16))
    canvas.alpha_composite(glow)

    d = ImageDraw.Draw(canvas)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 18, 42, int(238 * p)), outline=(*color, int(255 * p)), width=4)
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], outline=(255, 255, 255, int(70 * p)), width=2)

    # Vector Icon inside circle
    if icon_type == "card":
        d.rounded_rectangle([cx - 46, cy - 30, cx + 46, cy + 28], radius=10, fill=(*color, int(255 * p)), outline=(255, 255, 255, int(255 * p)), width=3)
        d.rectangle([cx - 46, cy - 14, cx + 46, cy - 2], fill=(255, 255, 255, int(230 * p)))
        d.rounded_rectangle([cx - 32, cy + 6, cx - 12, cy + 20], radius=3, fill=(*C_GOLD, int(255 * p)))
    elif icon_type == "multiply":
        f_x = get_font(F_MONT_BLACK, 52)
        bb = d.textbbox((0, 0), "×2", font=f_x)
        d.text((cx - (bb[2] - bb[0]) // 2, cy - (bb[3] - bb[1]) // 2 - bb[1]), "×2", font=f_x, fill=(*C_EMERALD, int(255 * p)))
    elif icon_type == "bank":
        # Classical bank columns + roof triangle
        d.polygon([(cx, cy - 38), (cx - 46, cy - 12), (cx + 46, cy - 12)], fill=(255, 255, 255, int(255 * p)))
        for bx in (-30, -10, 10, 30):
            d.rectangle([cx + bx - 5, cy - 10, cx + bx + 5, cy + 22], fill=(*C_COBALT_LIGHT, int(255 * p)))
        d.rectangle([cx - 48, cy + 22, cx + 48, cy + 32], fill=(255, 255, 255, int(255 * p)))
    elif icon_type == "crown":
        pts = [(cx - 40, cy + 22), (cx - 44, cy - 18), (cx - 18, cy + 2), (cx, cy - 28), (cx + 18, cy + 2), (cx + 44, cy - 18), (cx + 40, cy + 22)]
        d.polygon(pts, fill=(*C_GOLD, int(255 * p)), outline=(255, 255, 255, int(255 * p)))

    # Label pill below circle
    f_lbl = get_font(F_MONT_BLACK, 26)
    f_sub = get_font(F_MONO, 18)
    w_l = d.textbbox((0, 0), label, font=f_lbl)[2]
    w_s = d.textbbox((0, 0), sub, font=f_sub)[2]
    pw = max(w_l, w_s) + 40
    py0 = cy + r + 14
    d.rounded_rectangle([cx - pw // 2, py0, cx + pw // 2, py0 + 68], radius=16, fill=(8, 14, 30, int(235 * p)), outline=(*color, int(220 * p)), width=2)
    d.text((cx - w_l // 2, py0 + 8), label, font=f_lbl, fill=(255, 255, 255, int(255 * p)))
    d.text((cx - w_s // 2, py0 + 38), sub, font=f_sub, fill=(*C_COBALT_LIGHT, int(255 * p)))


def overlay_beat_broll_widgets(canvas: Image.Image, t: float):
    """Places beat-synced B-Roll overlays on the 120 BPM musical grid (`0.50s` beats)."""
    for w0, w1, otype in BROLL_OVERLAY_WINDOWS:
        if w0 <= t < w1:
            age = t - w0
            rem = w1 - t
            p_out = clamp(rem / 0.22) if rem < 0.22 else 1.0

            if otype == "bank_card_request":
                # Beat 7 (3.50s): Bank badge on left; Beat 11 (5.50s): Credit Card badge on right
                p1 = disney_overshoot_ease(clamp(age / 0.35)) * p_out
                draw_neon_circle_badge(canvas, 220, 230, 82, "bank", "BANQUE", "N'IMPORTE LAQUELLE", p1, C_COBALT)
                if t >= 5.50:
                    p2 = disney_overshoot_ease(clamp((t - 5.50) / 0.35)) * p_out
                    draw_neon_circle_badge(canvas, 860, 230, 82, "card", "CARTE CRÉDIT", "DEMANDE DIRECTE", p2, C_EMERALD)

            elif otype == "multiply_badges":
                # Matches `t=20.3s` of `reference 7.mp4`: Dual Neon Circular Badges popping on Beat 32 (16.0s) & Beat 33 (16.5s)
                p1 = disney_overshoot_ease(clamp(age / 0.35)) * p_out
                p2 = disney_overshoot_ease(clamp((age - 0.50) / 0.35)) * p_out
                draw_neon_circle_badge(canvas, 240, 235, 86, "card", "2 500 $", "CAPITAL DÉPART", p1, C_COBALT)
                draw_neon_circle_badge(canvas, 840, 235, 86, "multiply", "MULTIPLIE", "EFFET LEVIER", p2, C_EMERALD)

            elif otype == "cour_des_grands":
                # Beat 62 (31.0s) & Beat 63 (31.5s)
                p1 = disney_overshoot_ease(clamp(age / 0.35)) * p_out
                p2 = disney_overshoot_ease(clamp((age - 0.50) / 0.35)) * p_out
                draw_neon_circle_badge(canvas, 235, 235, 84, "bank", "RISQUE BANQUE", "CONFIANCE ↑", p1, C_COBALT)
                draw_neon_circle_badge(canvas, 845, 235, 84, "crown", "COUR DES GRANDS", "NIVEAU SUPÉRIEUR", p2, C_GOLD)

            elif otype == "rien_mais_tout":
                # Beat 80 (40.0s): "Là-bas t'as rien" -> Beat 83 (41.5s): "Mais t'as tout !"
                p1 = disney_overshoot_ease(clamp(age / 0.32)) * p_out
                draw_neon_circle_badge(canvas, 230, 235, 82, "card", "0 $ EN POCHE", "AU DÉPART", p1, C_CRIMSON)
                if t >= 41.40:
                    p2 = disney_overshoot_ease(clamp((t - 41.40) / 0.32)) * p_out
                    draw_neon_circle_badge(canvas, 850, 235, 82, "crown", "MAIS T'AS TOUT", "OPPORTUNITÉ 100%", p2, C_EMERALD)

            elif otype == "three_steps_plan":
                # Beat-synced 3-step pills at top of frame: 51.0s (Beat 102), 52.0s (Beat 104), 53.5s (Beat 107)
                steps = [
                    (0.00, "01", "VA À LA BANQUE", C_COBALT),
                    (1.00, "02", "DEMANDE UNE CARTE DE CRÉDIT", C_COBALT_LIGHT),
                    (2.50, "03", "GÈRE TON CRÉDIT CORRECTEMENT", C_EMERALD),
                ]
                d = ImageDraw.Draw(canvas)
                for idx_s, (delay_s, num_s, txt_s, col_s) in enumerate(steps):
                    ps = emil_ease_out(clamp((age - delay_s) / 0.28)) * p_out
                    if ps <= 0.02:
                        continue
                    py = int(105 + idx_s * 86 + 20 * (1.0 - ps))
                    d.rounded_rectangle([90, py, W - 90, py + 72], radius=20, fill=(8, 14, 30, int(235 * ps)), outline=(*col_s, int(245 * ps)), width=3)
                    d.rounded_rectangle([110, py + 14, 178, py + 58], radius=12, fill=(*col_s, int(255 * ps)))
                    d.text((126, py + 21), num_s, font=get_font(F_MONO, 24), fill=(255, 255, 255, int(255 * ps)))
                    d.text((202, py + 19), txt_s, font=get_font(F_MONT_EBOLD, 27), fill=(255, 255, 255, int(255 * ps)))
            return


# ---------------------------------------------------------------------------
# 4. Full-Screen Beat-Locked B-Roll & Motion Cutaways (`reference 7.mp4` style)
# ---------------------------------------------------------------------------
def render_cutaway_scene(t: float, cid: int) -> Image.Image:
    if cid == 1:
        # Cutaway 1 (8.00s - 12.00s, Beats 16..24):
        # Matches `t=5.4s` of `reference 7.mp4` (Dark 3D Laptop / UI Screen) + Real Graded B-Roll background:
        # Shows a 3D Canadian Bank Credit Card Approval UI (`3 000 $ APPROUVÉ` while `SOLDE : 0 $`)!
        age = t - 8.00
        canvas = get_graded_broll_frame(BROLL_TWILIGHT, age, tint="cobalt")
        d = ImageDraw.Draw(canvas)

        # Top Cobalt ambient glow
        p = emil_ease_out(clamp(age / 0.35))
        uy = int(210 + 35 * (1.0 - p))

        # 3D Glassmorphic Bank Terminal Window (`reference 7.mp4` t=5.4s style)
        d.rounded_rectangle([70, uy, W - 70, uy + 980], radius=38, fill=(8, 13, 28, int(242 * p)), outline=(*C_COBALT, int(235 * p)), width=3)
        # Window traffic lights + header bar
        d.ellipse([115, uy + 36, 135, uy + 56], fill=(255, 95, 86, int(255 * p)))
        d.ellipse([150, uy + 36, 170, uy + 56], fill=(255, 189, 46, int(255 * p)))
        d.ellipse([185, uy + 36, 205, uy + 56], fill=(39, 201, 63, int(255 * p)))
        d.text((235, uy + 31), "BANQUE DU CANADA • DOSSIER CRÉDIT", font=get_font(F_MONO, 22), fill=(*C_SILVER, int(230 * p)))

        # Row 1: Solde Compte Courant = 0 $ (pops on Beat 16 = 8.0s)
        d.rounded_rectangle([120, uy + 110, W - 120, uy + 235], radius=24, fill=(16, 24, 48, int(255 * p)), outline=(*C_CRIMSON, int(210 * p)), width=2)
        d.text((160, uy + 132), "ARGENT SUR LE COMPTE", font=get_font(F_MONO, 21), fill=(*C_SILVER, int(240 * p)))
        d.text((160, uy + 168), "0,00 $ CAD (PAS UN ROND)", font=get_font(F_MONT_BLACK, 36), fill=(*C_CRIMSON, int(255 * p)))

        # Row 2: 3D Glossy Canadian Credit Card (pops on Beat 17 = 8.5s)
        p_card = disney_overshoot_ease(clamp((age - 0.35) / 0.42))
        if p_card > 0.02:
            cy_c = int(uy + 280 + 30 * (1.0 - p_card))
            # Card glow
            d.rounded_rectangle([135, cy_c, W - 135, cy_c + 430], radius=34, fill=(*C_COBALT, int(255 * p_card)), outline=(255, 255, 255, int(220 * p_card)), width=3)
            d.rounded_rectangle([135, cy_c + 215, W - 135, cy_c + 430], radius=34, fill=(*C_COBALT_DEEP, int(210 * p_card)))
            # Gold EMV Chip
            d.rounded_rectangle([195, cy_c + 65, 295, cy_c + 140], radius=14, fill=(*C_GOLD, int(255 * p_card)), outline=(255, 255, 255, int(190 * p_card)), width=2)
            d.text((W - 430, cy_c + 65), " PLATINUM CREDIT", font=get_font(F_MONO, 24), fill=(255, 255, 255, int(230 * p_card)))

            # Animated Credit Limit Counter (2 500 $ -> 3 000 $)
            val = 3000 if age < 2.8 else 2500
            lbl_top = "LIMITE DE CRÉDIT ALLOUÉE" if age < 2.8 else "MINIMUM GARANTI DÉBUTANT"
            d.text((195, cy_c + 175), lbl_top, font=get_font(F_MONO, 22), fill=(*C_SILVER, int(255 * p_card)))
            d.text((195, cy_c + 215), f"{val:,} $ CAD".replace(",", " "), font=get_font(F_MONT_BLACK, 88), fill=(255, 255, 255, int(255 * p_card)))
            d.text((195, cy_c + 345), "4519  ••••  ••••  2026", font=get_font(F_MONO, 28), fill=(*C_SILVER, int(245 * p_card)))

        # Row 3: Green Approval Stamp on Beat 19 (9.5s)
        p_ok = disney_overshoot_ease(clamp((age - 1.0) / 0.35))
        if p_ok > 0.02:
            by = uy + 760
            d.rounded_rectangle([160, by, W - 160, by + 135], radius=26, fill=(10, 42, 32, int(245 * p_ok)), outline=(*C_EMERALD, int(255 * p_ok)), width=3)
            d.text((205, by + 26), "STATUT : CARTE APPROUVÉE", font=get_font(F_MONT_BLACK, 35), fill=(*C_EMERALD, int(255 * p_ok)))
            # Custom vector checkmark badge
            ck_x, ck_y = W - 225, by + 48
            d.ellipse([ck_x - 24, ck_y - 24, ck_x + 24, ck_y + 24], fill=(*C_EMERALD, int(255 * p_ok)))
            d.line([(ck_x - 11, ck_y), (ck_x - 3, ck_y + 9), (ck_x + 12, ck_y - 8)], fill=(8, 28, 20, int(255 * p_ok)), width=5)
            d.text((205, by + 78), "AUCUN HISTORIQUE REQUIS AU DÉPART", font=get_font(F_MONO, 22), fill=(255, 255, 255, int(240 * p_ok)))

        return canvas

    elif cid == 2:
        # Cutaway 2 (21.50s - 26.50s, Beats 43..53):
        # Graded Skyline B-Roll + Animated Credit Limit Doubling Chart (2 500 $ -> 5 000 $ -> 10 000 $+)
        age = t - 21.50
        canvas = get_graded_broll_frame(BROLL_SKYLINE, age, tint="cobalt")
        d = ImageDraw.Draw(canvas)

        p = emil_ease_out(clamp(age / 0.35))
        uy = int(200 + 30 * (1.0 - p))
        d.rounded_rectangle([70, uy, W - 70, uy + 980], radius=38, fill=(8, 13, 28, int(238 * p)), outline=(*C_COBALT, int(235 * p)), width=3)

        f_hdr = get_font(F_MONT_BLACK, 44)
        h_txt = "EFFET MULTIPLICATEUR"
        wh = d.textbbox((0, 0), h_txt, font=f_hdr)[2]
        d.text(((W - wh) // 2, uy + 52), h_txt, font=f_hdr, fill=(255, 255, 255, int(255 * p)))

        f_scr = get_font(F_DAFOE, 68)
        s_txt = "Doubler son crédit"
        ws = d.textbbox((0, 0), s_txt, font=f_scr)[2]
        d.text(((W - ws) // 2, uy + 108), s_txt, font=f_scr, fill=(*C_COBALT_LIGHT, int(255 * p)))

        # 3 Beat-Locked Escalating Credit Bars (Beat 44=22.0s, Beat 47=23.5s, Beat 50=25.0s)
        bars = [
            (0.15, "JOUR 1 • DÉPART", "2 500 $", 0.38, C_COBALT),
            (1.50, "ÉTAPE 2 • DOUBLÉ (×2)", "5 000 $", 0.68, C_COBALT_LIGHT),
            (3.00, "ÉTAPE 3 • BONNE GESTION", "10 000 $ +", 1.00, C_EMERALD),
        ]
        for idx_b, (delay_b, lbl_b, val_b, frac_b, col_b) in enumerate(bars):
            pb = emil_ease_out(clamp((age - delay_b) / 0.45))
            if pb <= 0.02:
                continue
            by = uy + 245 + idx_b * 225
            d.rounded_rectangle([125, by, W - 125, by + 185], radius=26, fill=(14, 22, 46, int(245 * pb)), outline=(*col_b, int(235 * pb)), width=3)
            d.text((165, by + 26), lbl_b, font=get_font(F_MONO, 23), fill=(*C_SILVER, int(255 * pb)))
            d.text((165, by + 64), val_b, font=get_font(F_MONT_BLACK, 52), fill=(255, 255, 255, int(255 * pb)))
            bar_max_w = W - 330
            cur_w = max(24, int(round(bar_max_w * frac_b * pb)))
            d.rounded_rectangle([165, by + 136, 165 + bar_max_w, by + 162], radius=13, fill=(28, 38, 68, int(255 * pb)))
            d.rounded_rectangle([165, by + 136, 165 + cur_w, by + 162], radius=13, fill=(*col_b, int(255 * pb)))

        return canvas

    elif cid == 3:
        # Cutaway 3 (34.00s - 38.00s, Beats 68..76):
        # Exact match to `t=15.3s` of `reference 7.mp4` ("and where / most agencies / can't help" on Crimson-Red glow background)!
        age = t - 34.00
        canvas = Image.new("RGBA", (W, H), (*C_DARK_BG, 255))
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        # Left & top-left intense Crimson-Red radial glow (`reference 7.mp4` t=15.3s signature)
        d_red = np.sqrt(((xx - W * 0.22) / 560.0) ** 2 + ((yy - H * 0.36) / 620.0) ** 2)
        red_glow = (np.clip(1.0 - d_red, 0.0, 1.0) ** 1.8) * 0.62
        arr = np.array(canvas, dtype=np.float32)
        arr[:, :, 0] = np.clip(arr[:, :, 0] + red_glow * 235.0, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] + red_glow * 22.0, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] + red_glow * 48.0, 0, 255)
        canvas = Image.fromarray(arr.astype(np.uint8), mode="RGBA")

        p1 = emil_ease_out(clamp(age / 0.32))
        p2 = emil_ease_out(clamp((age - 0.18) / 0.36))
        p3 = emil_ease_out(clamp((age - 0.45) / 0.42))

        d = ImageDraw.Draw(canvas)
        f_sm = get_font(F_MONT_BOLD, 44)
        f_big = get_font(F_MONT_BLACK, 102)
        f_scr = get_font(F_DAFOE, 112)

        d.text((155, int(680 + 20 * (1.0 - p1))), "L'opportunité de", font=f_sm, fill=(255, 255, 255, int(245 * p1)))
        d.text((150, int(740 + 24 * (1.0 - p2))), "REPARTIR", font=f_big, fill=(255, 255, 255, int(255 * p2)))
        d.text((150, int(848 + 24 * (1.0 - p2))), "DE ZÉRO", font=f_big, fill=(255, 255, 255, int(255 * p2)))

        # Glowing Crimson Script "même avec rien" (`t=15.3s` "can't help" style)
        draw_glow_text(canvas, "même avec rien", W // 2, int(1025 + 24 * (1.0 - p3)), f_scr, C_CRIMSON, glow_rgb=C_CRIMSON, alpha=p3)
        return canvas

    elif cid == 4:
        # Cutaway 4 (42.50s - 49.00s, Beats 85..98):
        # Phase A (42.50s - 46.50s): Canada = Système de Dette (S'enrichir grâce aux dettes)
        # Phase B (46.50s - 49.00s): France = Le Découvert (Shattering 3D Emblem matching `t=12.9s` of `reference 7.mp4`!)
        if t < 46.50:
            age = t - 42.50
            canvas = get_graded_broll_frame(BROLL_ATRIUM, age, tint="cobalt")
            p = emil_ease_out(clamp(age / 0.35))
            d = ImageDraw.Draw(canvas)
            cy = int(380 + 30 * (1.0 - p))
            d.rounded_rectangle([80, cy, W - 80, cy + 680], radius=38, fill=(8, 15, 34, int(242 * p)), outline=(*C_EMERALD, int(245 * p)), width=4)
            d.rounded_rectangle([135, cy + 50, 520, cy + 108], radius=18, fill=(*C_EMERALD, int(255 * p)))
            d.text((162, cy + 64), "MODÈLE NORD-AMÉRICAIN", font=get_font(F_MONO, 23), fill=(6, 18, 14, int(255 * p)))
            d.text((135, cy + 145), "SYSTÈME DE DETTE", font=get_font(F_MONT_BLACK, 64), fill=(255, 255, 255, int(255 * p)))
            d.text((135, cy + 235), "S'enrichir grâce au crédit", font=get_font(F_DAFOE, 72), fill=(*C_COBALT_LIGHT, int(255 * p)))

            # Rising wealth graph inside card
            pts = [(145, cy + 560), (320, cy + 490), (520, cy + 510), (720, cy + 400), (915, cy + 320)]
            d.line(pts, fill=(*C_EMERALD, int(255 * p)), width=10)
            for px, py in pts:
                d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=(255, 255, 255, int(255 * p)), outline=(*C_EMERALD, int(255 * p)), width=4)
            return canvas

        # Phase B (46.50s - 49.00s): Shattering 3D Emblem (`reference 7.mp4` t=12.9s style) for "EN FRANCE : LE DÉCOUVERT"
        age = t - 46.50
        canvas = Image.new("RGBA", (W, H), (*C_DARK_BG, 255))
        p = emil_ease_out(clamp(age / 0.35))
        shatter = emil_ease_out(clamp((age - 0.15) / 0.65))

        # Radial Cobalt/Crimson glow behind shattering sphere
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([W // 2 - 260, 460, W // 2 + 260, 980], fill=(*C_CRIMSON, int(115 * p)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=45))
        canvas.alpha_composite(glow)

        d = ImageDraw.Draw(canvas)
        cx, cy = W // 2, 720
        d.ellipse([cx - 195, cy - 195, cx + 195, cy + 195], fill=(16, 22, 44, int(245 * p)), outline=(*C_CRIMSON, int(245 * p)), width=5)

        # Center broken overdraft gauge (`-450 €`) + lightning crack inside the sphere
        f_ov = get_font(F_MONT_BLACK, 64)
        ov_txt = "- 450 €"
        w_ov = d.textbbox((0, 0), ov_txt, font=f_ov)[2]
        d.text((cx - w_ov // 2, cy - 42), ov_txt, font=f_ov, fill=(*C_CRIMSON, int(255 * p)))
        f_fr = get_font(F_MONO, 22)
        fr_txt = "SOLDE NÉGATIF"
        w_fr = d.textbbox((0, 0), fr_txt, font=f_fr)[2]
        d.text((cx - w_fr // 2, cy + 38), fr_txt, font=f_fr, fill=(255, 255, 255, int(235 * p)))

        # Shattering polygon shards radiating outward (`reference 7.mp4` t=12.9s effect!)
        rng = np.random.default_rng(129)
        for i in range(18):
            ang = (i / 18.0) * 2.0 * math.pi
            dist = 135.0 + shatter * (65.0 + rng.uniform(0, 55))
            sx = cx + math.cos(ang) * dist
            sy = cy + math.sin(ang) * dist
            s_rad = 22.0 * (1.0 - 0.25 * shatter)
            poly = [
                (sx + math.cos(ang + 0.2) * s_rad, sy + math.sin(ang + 0.2) * s_rad),
                (sx + math.cos(ang + 2.1) * s_rad, sy + math.sin(ang + 2.1) * s_rad),
                (sx + math.cos(ang + 4.2) * s_rad, sy + math.sin(ang + 4.2) * s_rad),
            ]
            d.polygon(poly, fill=(255, 255, 255, int(235 * p)), outline=(*C_CRIMSON, int(255 * p)))

        f_ban = get_font(F_MONT_BLACK, 56)
        txt_b = "LE DÉCOUVERT"
        wb = d.textbbox((0, 0), txt_b, font=f_ban)[2]
        d.text(((W - wb) // 2, 1005), txt_b, font=f_ban, fill=(*C_CRIMSON, int(255 * p)))
        f_s = get_font(F_MONO, 26)
        ts = "AGIOS • BLOCAGE • PÉNALITÉS"
        ws = d.textbbox((0, 0), ts, font=f_s)[2]
        d.text(((W - ws) // 2, 1085), ts, font=f_s, fill=(*C_SILVER, int(245 * p)))
        return canvas

    # cid == 5 (56.50s - 62.00s, Beats 113..124):
    # Credit Score Plunge + 3 Beat-Locked Crossed-Out Icons (`PAS DE MAISON`, `PAS DE VOITURE`, `TOUT RUINÉ`)
    age = t - 56.50
    canvas = get_graded_broll_frame(BROLL_TWILIGHT, age, tint="crimson")
    d = ImageDraw.Draw(canvas)
    p = emil_ease_out(clamp(age / 0.35))

    # Top Credit Score Plunge Card (780 -> 410)
    score_val = int(round(780 - 370 * emil_ease_in_out(clamp(age / 1.8))))
    d.rounded_rectangle([80, 175, W - 80, 445], radius=34, fill=(14, 10, 22, int(242 * p)), outline=(*C_CRIMSON, int(245 * p)), width=4)
    d.text((135, 215), "MAUVAISE GESTION • SCORE EN CHUTE", font=get_font(F_MONO, 23), fill=(*C_CRIMSON, int(255 * p)))
    d.text((135, 265), f"SCORE : {score_val}", font=get_font(F_MONT_BLACK, 82), fill=(255, 255, 255, int(255 * p)))

    # 3 Beat-Locked Consequence Cards popping on the 120 BPM beat
    items = [
        (1.50, "❌  PAS DE MAISON", "Refus immédiat de prêt immobilier"),
        (2.50, "❌  PAS DE VOITURE", "Aucun financement ni leasing possible"),
        (3.50, "⚠️  DOSSIER BLOQUÉ", "Ton historique de crédit est ruiné"),
    ]
    for idx_i, (delay_i, title_i, sub_i) in enumerate(items):
        pi = disney_overshoot_ease(clamp((age - delay_i) / 0.36))
        if pi <= 0.02:
            continue
        iy = int(500 + idx_i * 235 + 25 * (1.0 - pi))
        d.rounded_rectangle([80, iy, W - 80, iy + 195], radius=28, fill=(18, 12, 26, int(244 * pi)), outline=(*C_CRIMSON, int(245 * pi)), width=3)
        # Draw vector red X badge on left
        bx, by = 165, iy + 97
        d.ellipse([bx - 42, by - 42, bx + 42, by + 42], fill=(*C_CRIMSON, int(255 * pi)))
        d.line([(bx - 18, by - 18), (bx + 18, by + 18)], fill=(255, 255, 255, int(255 * pi)), width=7)
        d.line([(bx - 18, by + 18), (bx + 18, by - 18)], fill=(255, 255, 255, int(255 * pi)), width=7)
        clean_title = title_i.split("  ")[-1]
        d.text((235, iy + 42), clean_title, font=get_font(F_MONT_BLACK, 44), fill=(255, 255, 255, int(255 * pi)))
        d.text((235, iy + 112), sub_i, font=get_font(F_MONT_SEMI, 26), fill=(*C_SILVER, int(245 * pi)))

    return canvas


# ---------------------------------------------------------------------------
# 5. Fast Transitions (`whip pan`, `RGB glitch`, `zoom-in`)
# ---------------------------------------------------------------------------
def apply_glitch_seam(im_a: Image.Image, im_b: Image.Image, p: float) -> Image.Image:
    """Fast RGB Chromatic Aberration + Horizontal Slice Glitch transition."""
    base = im_a if p < 0.5 else im_b
    arr = np.array(base.convert("RGB"), dtype=np.uint8)
    intensity = math.sin(p * math.pi)
    shift_x = int(round(28 * intensity))
    out = arr.copy()
    if shift_x > 0:
        out[:, shift_x:, 0] = arr[:, :-shift_x, 0]   # Red channel right
        out[:, :-shift_x, 2] = arr[:, shift_x:, 2]   # Blue channel left
    # Horizontal glitch slices
    rng = np.random.default_rng(int(p * 100) + 7)
    for _ in range(6):
        y0 = int(rng.integers(100, H - 220))
        sh = int(rng.integers(25, 95))
        dx = int(rng.integers(-65, 65) * intensity)
        out[y0 : y0 + sh] = np.roll(out[y0 : y0 + sh], dx, axis=1)
    return Image.fromarray(out, mode="RGB").convert("RGBA")


def render_base_state(bgr: np.ndarray, t: float) -> Image.Image:
    for c0, c1, cid, _, _ in CUTAWAY_WINDOWS:
        if c0 <= t < c1:
            im = render_cutaway_scene(t, cid)
            overlay_ref7_subtitles(im, t, in_cutaway=True)
            return im

    im = prepare_aroll_frame(bgr, t)
    overlay_beat_broll_widgets(im, t)
    overlay_ref7_subtitles(im, t, in_cutaway=False)
    return im


def compose_frame(bgr: np.ndarray, t: float) -> np.ndarray:
    half_w = 0.16
    for c0, c1, _cid, tr_in, tr_out in CUTAWAY_WINDOWS:
        for t_seam, tr_mode in ((c0, tr_in), (c1, tr_out)):
            if abs(t - t_seam) <= half_w:
                p = clamp((t - (t_seam - half_w)) / (2.0 * half_w))
                im_a = render_base_state(bgr, t_seam - half_w - 0.02)
                im_b = render_base_state(bgr, t_seam + half_w + 0.02)
                if tr_mode == "zoom_in":
                    out = zoom_through_seam(im_a, im_b, p, inverse=False)
                elif tr_mode == "whip_pan":
                    out = cut_the_curve_seam(im_a, im_b, p, direction="left")
                else:
                    out = apply_glitch_seam(im_a, im_b, p)
                rgb = np.array(out.convert("RGB"), dtype=np.uint8)
                return rgb[:, :, ::-1].copy()

    out = render_base_state(bgr, t)
    rgb = np.array(out.convert("RGB"), dtype=np.uint8)
    return rgb[:, :, ::-1].copy()


# ---------------------------------------------------------------------------
# 6. Audio Engine: Isolated 1.07x Voice + 120 BPM Motivating Beat + SFX (`whoosh`, `pop`, `click`, `ding`)
# ---------------------------------------------------------------------------
def build_master_audio() -> str:
    ensure_speed_video()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw_wav = "/tmp/ref7_inspect/voice_107x.wav"
    mixed_wav = "/tmp/ref7_inspect/master_mix_ref7.wav"

    subprocess.run([ff, "-y", "-i", SPEED_MP4, "-vn", "-ar", "44100", "-ac", "2", raw_wav], check=True, capture_output=True)
    with wave.open(raw_wav, "rb") as wf:
        sr = wf.getframerate()
        n_f = wf.getnframes()
        vo = np.frombuffer(wf.readframes(n_f), dtype=np.int16).astype(np.float32).reshape((-1, 2)) / 32768.0

    total_samples = vo.shape[0]
    t = np.arange(total_samples, dtype=np.float32) / float(sr)

    # --- A. Voice Isolation & Studio Clarity EQ ---
    # 1. High-pass at 95 Hz + Low-pass at 11.5 kHz to remove room rumble & hiss
    sos_hp = signal.butter(3, 95.0 / (sr * 0.5), btype="highpass", output="sos")
    sos_lp = signal.butter(3, 11500.0 / (sr * 0.5), btype="lowpass", output="sos")
    vo_clean = signal.sosfilt(sos_lp, signal.sosfilt(sos_hp, vo, axis=0), axis=0).astype(np.float32)

    # 2. 3-Band Broadcast Vocal EQ (Warmth 170 Hz + Articulation Presence 3.2 kHz + Air 7.8 kHz)
    sos_warm = signal.butter(2, [120.0 / (sr * 0.5), 230.0 / (sr * 0.5)], btype="bandpass", output="sos")
    sos_pres = signal.butter(2, [2400.0 / (sr * 0.5), 4600.0 / (sr * 0.5)], btype="bandpass", output="sos")
    sos_air = signal.butter(2, 7200.0 / (sr * 0.5), btype="highpass", output="sos")
    vo_eq = (
        vo_clean
        + 0.20 * signal.sosfilt(sos_warm, vo_clean, axis=0)
        + 0.36 * signal.sosfilt(sos_pres, vo_clean, axis=0)
        + 0.18 * signal.sosfilt(sos_air, vo_clean, axis=0)
    ).astype(np.float32)

    # 3. Smooth downward noise gate to suppress background room noise between words
    mono_abs = np.abs(vo_eq[:, 0])
    win_g = int(0.03 * sr)
    vox_env = np.convolve(mono_abs, np.ones(win_g, dtype=np.float32) / win_g, mode="same")
    gate = np.clip((vox_env - 0.008) / 0.018, 0.15, 1.0)[:, None]
    vo_master = np.tanh(vo_eq * gate * 1.38) * 0.88

    # --- B. Motivating 120 BPM Trending Beat (`0.50s` per beat, `2.00s` per bar) ---
    bar_sec = BEAT_SEC * 4.0  # 2.00s exact
    chords = [
        (110.00, 220.00, 261.63, 329.63, 440.00),  # Am
        (87.31, 174.61, 220.00, 261.63, 349.23),   # Fmaj7
        (130.81, 261.63, 329.63, 392.00, 523.25),  # C
        (98.00, 196.00, 246.94, 293.66, 392.00),   # G
    ]
    bgm_l = np.zeros(total_samples, dtype=np.float32)
    bgm_r = np.zeros(total_samples, dtype=np.float32)
    bar_len = int(round(bar_sec * sr))
    n_bars = (total_samples + bar_len - 1) // bar_len
    rng = np.random.default_rng(2026)

    for b_idx in range(n_bars):
        i0 = b_idx * bar_len
        i1 = min(total_samples, i0 + bar_len)
        if i1 <= i0:
            continue
        bt = np.arange(i1 - i0, dtype=np.float32) / float(sr)
        fb, f1, f2, f3, f4 = chords[b_idx % 4]

        # Driving 120 BPM Kick + Sub-Bass on every 0.50s beat
        beat_pos = (bt % BEAT_SEC) / BEAT_SEC
        kick_f = 54.0 + 110.0 * np.exp(-beat_pos * 22.0)
        kick = np.sin(2 * np.pi * kick_f * (bt % BEAT_SEC)) * np.exp(-beat_pos * 6.8) * 0.45

        # Crisp Clap/Snare on Beats 2 & 4 (0.50s and 1.50s)
        beat_idx = np.clip((bt / BEAT_SEC).astype(np.int32), 0, 3)
        is_snare = (beat_idx == 1) | (beat_idx == 3)
        snare_noise = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32)
        snare = np.where(is_snare, (snare_noise * 0.55 + np.sin(2 * np.pi * 220.0 * (bt % BEAT_SEC)) * 0.45) * np.exp(-beat_pos * 18.0), 0.0) * 0.28

        # 16th-note (0.125s) driving Hi-Hat + Motivating Synth Pluck Arpeggio
        sixteenth = BEAT_SEC * 0.25
        s_pos = (bt % sixteenth) / sixteenth
        hat = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32) * np.exp(-s_pos * 22.0) * 0.06

        eighth = BEAT_SEC * 0.50
        e_pos = (bt % eighth) / eighth
        arp_notes = [f1, f2, f3, f4, f3, f2, f4, f3]
        n_idx = np.clip((bt / eighth).astype(np.int32), 0, 7)
        af = np.choose(n_idx, arp_notes)
        arp_env = np.exp(-e_pos * 4.5) * (1.0 - 0.35 * np.exp(-beat_pos * 12.0))  # Sidechain pump on kick
        arp_l = (0.65 * np.sin(2 * np.pi * af * bt) + 0.35 * np.sin(2 * np.pi * (af * 2.0) * bt)) * arp_env * 0.46
        arp_r = (0.65 * np.sin(2 * np.pi * af * bt + 0.25) + 0.35 * np.sin(2 * np.pi * (af * 2.0) * bt)) * arp_env * 0.46

        # Warm stereo motivating pad
        pad_pump = 0.35 + 0.65 * (1.0 - np.exp(-beat_pos * 5.0))
        pad_l = (0.4 * np.sin(2 * np.pi * fb * bt) + 0.35 * np.sin(2 * np.pi * f2 * bt) + 0.25 * np.sin(2 * np.pi * f3 * bt)) * pad_pump * 0.35
        pad_r = (0.4 * np.sin(2 * np.pi * fb * bt) + 0.35 * np.sin(2 * np.pi * f3 * bt) + 0.25 * np.sin(2 * np.pi * f4 * bt)) * pad_pump * 0.35

        bgm_l[i0:i1] = kick + snare + hat + arp_l + pad_l
        bgm_r[i0:i1] = kick + snare + hat + arp_r + pad_r

    # Carve 2.5 - 4.2 kHz vocal clarity pocket
    sos_pocket = signal.butter(2, [2500.0 / (sr * 0.5), 4200.0 / (sr * 0.5)], btype="bandstop", output="sos")
    bgm_l = signal.sosfilt(sos_pocket, bgm_l).astype(np.float32)
    bgm_r = signal.sosfilt(sos_pocket, bgm_r).astype(np.float32)

    bgm_rms = float(np.sqrt(np.mean(0.5 * (bgm_l ** 2 + bgm_r ** 2))) + 1e-6)
    bgm_l /= bgm_rms
    bgm_r /= bgm_rms

    win_d = int(0.22 * sr)
    smooth_vox = np.convolve(mono_abs, np.ones(win_d, dtype=np.float32) / win_d, mode="same")
    duck_gain = np.clip(0.115 - 0.34 * smooth_vox, 0.072, 0.115)
    bgm_l *= duck_gain
    bgm_r *= duck_gain

    # --- C. Synchronized SFX: `whoosh`, `pop`, `click`, `ding` ---
    sfx_l = np.zeros(total_samples, dtype=np.float32)
    sfx_r = np.zeros(total_samples, dtype=np.float32)

    def add_whoosh(ts: float):
        i0 = int(ts * sr)
        dur = int(0.24 * sr)
        i1 = min(total_samples, i0 + dur)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            env = np.clip(np.sin(np.pi * lt), 0.0, 1.0) ** 1.4
            sub = np.sin(2 * np.pi * (120.0 - 65.0 * lt) * lt * 0.24) * np.exp(-lt * 3.5)
            air = rng.normal(0.0, 1.0, i1 - i0).astype(np.float32) * env
            sfx_l[i0:i1] += 0.065 * sub + 0.024 * air
            sfx_r[i0:i1] += 0.065 * sub + 0.024 * air

    def add_pop(ts: float):
        i0 = int(ts * sr)
        dur = int(0.12 * sr)
        i1 = min(total_samples, i0 + dur)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            w = np.sin(2 * np.pi * (310.0 + 440.0 * (lt ** 0.65)) * lt * 0.12) * np.exp(-lt * 5.5)
            sfx_l[i0:i1] += 0.075 * w
            sfx_r[i0:i1] += 0.075 * w

    def add_click(ts: float):
        i0 = int(ts * sr)
        dur = int(0.035 * sr)
        i1 = min(total_samples, i0 + dur)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            c = np.sin(2 * np.pi * 1650.0 * lt * 0.035) * np.exp(-lt * 16.0)
            sfx_l[i0:i1] += 0.045 * c
            sfx_r[i0:i1] += 0.045 * c

    def add_ding(ts: float):
        i0 = int(ts * sr)
        dur = int(0.38 * sr)
        i1 = min(total_samples, i0 + dur)
        if i1 > i0:
            lt = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
            d_wave = (0.65 * np.sin(2 * np.pi * 1567.98 * lt * 0.38) + 0.35 * np.sin(2 * np.pi * 2349.32 * lt * 0.38)) * np.exp(-lt * 5.2)
            sfx_l[i0:i1] += 0.065 * d_wave
            sfx_r[i0:i1] += 0.065 * d_wave

    # Trigger Whooshes on all cutaway transitions & punch zooms
    for c0, c1, _, _, _ in CUTAWAY_WINDOWS:
        add_whoosh(c0)
        add_whoosh(c1)
    for z0, _, _ in PUNCH_ZOOM_WINDOWS:
        add_whoosh(z0)

    # Trigger Pops on all B-Roll Overlays & step cards
    for pop_t in [3.50, 5.50, 8.35, 16.00, 16.50, 22.00, 23.50, 31.00, 31.50, 39.80, 41.40, 51.00, 52.00, 53.50, 58.00, 59.00, 60.00]:
        add_pop(pop_t)

    # Trigger Dings on money & approval highlights
    for ding_t in [7.80, 9.00, 10.80, 21.50, 25.00, 34.00, 41.40, 44.80]:
        add_ding(ding_t)

    # Trigger subtle Clicks on subtitle changes
    for seg_t0, _, _, _, _ in SEGMENTS[::2]:
        add_click(seg_t0)

    mix_l = np.clip(vo_master[:, 0] + bgm_l + sfx_l, -0.98, 0.98)
    mix_r = np.clip(vo_master[:, 1] + bgm_r + sfx_r, -0.98, 0.98)
    out_i16 = (np.stack([mix_l, mix_r], axis=-1) * 32767.0).astype(np.int16)

    with wave.open(mixed_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out_i16.tobytes())
    return mixed_wav


def generate_preview(preview_path: str):
    ensure_speed_video()
    cap = cv2.VideoCapture(SPEED_MP4)
    sample_times = [0.8, 4.2, 6.2, 9.2, 11.2, 16.8, 22.8, 25.4, 32.2, 35.5, 41.8, 44.2, 47.6, 54.0, 59.5, 62.8]
    thumbs = []
    for ts in sample_times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ts * FPS)))
        ok, bgr = cap.read()
        if not ok:
            continue
        frame = compose_frame(bgr, ts)
        th = cv2.resize(frame, (270, 480), interpolation=cv2.INTER_AREA)
        cv2.rectangle(th, (8, 8), (155, 42), (10, 14, 28), -1)
        cv2.putText(th, f"t={ts:4.1f}s", (16, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 190, 80), 2, cv2.LINE_AA)
        thumbs.append(th)
    cap.release()

    rows = [np.hstack(thumbs[i : i + 4]) for i in range(0, 16, 4)]
    grid = np.vstack(rows)
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)
    cv2.imwrite(preview_path, grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"Saved 16-frame preview sheet to {preview_path}")


def render_full_video():
    os.makedirs(FILM_DIR, exist_ok=True)
    ensure_speed_video()
    mixed_wav = build_master_audio()

    cap = cv2.VideoCapture(SPEED_MP4)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ff = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ff, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "bgr24",
        "-r", f"{FPS:.2f}",
        "-i", "-",
        "-i", mixed_wav,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-maxrate", "3200k",
        "-bufsize", "6400k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        OUT_MP4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for f_idx in range(total_frames):
        ok, bgr = cap.read()
        if not ok:
            break
        t = f_idx / FPS
        frame = compose_frame(bgr, t)
        proc.stdin.write(frame.tobytes())
        if (f_idx + 1) % 300 == 0 or (f_idx + 1) == total_frames:
            print(f"Rendered {f_idx + 1}/{total_frames} frames ({(f_idx + 1) * 100.0 / total_frames:.1f}%)")

    proc.stdin.close()
    proc.wait()
    cap.release()
    mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"Successfully rendered {OUT_MP4} ({mb:.2f} MB)")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        generate_preview(sys.argv[2])
    else:
        render_full_video()
