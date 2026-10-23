#!/usr/bin/env python3
"""
100% Pure 3D SaaS Product Launch Motion Design Video for:
https://devis-designer-app.jerode.workers.dev/ ("Devis Designer")

Output:
- `devis-designer-motion/film/devis-designer-motion-design-9x16.mp4` (1080x1920 @ 30fps, 52.0s)

Applies the 10 Animation Design Laws:
1. Anticipation & Overshoot (`ease_out_back`, spring settle)
2. Staggered Choreography (cascade delays on line items, templates, pricing cards)
3. Real 3D Perspective Projection (`cv2.getPerspectiveTransform` + `cv2.warpPerspective` + specular sheen)
4. Micro-Interactions (animated cursor, click ripples, live WYSIWYG focus ring, Bézier signature draw)
5. Kinetic Typography & Rolling Number Counters (`0 F -> 495 600 F CFA`)
6. Zero Repeated Scene / 8 Bespoke Scenes
7. 100% Custom Vector Icons (zero Unicode emoji `[]` boxes)
8. Beat-Synced 124 BPM SaaS Launch Soundtrack + Frame-Accurate UI Foley SFX
"""

import math
import os
import subprocess
import time
import wave
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import imageio_ffmpeg

W, H = 1080, 1920
FPS = 30
DURATION = 52.0
TOTAL_FRAMES = int(DURATION * FPS)  # 1560 frames

REPO_ROOT = "/home/user/COOL-backup"
OUT_DIR = os.path.join(REPO_ROOT, "devis-designer-motion/film")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs("/tmp/dd_inspect", exist_ok=True)
OUT_MP4 = os.path.join(OUT_DIR, "devis-designer-motion-design-9x16.mp4")

FONT_DIR = "/tmp/work_cache/fonts/node_modules"
F_BLACK = f"{FONT_DIR}/@expo-google-fonts/montserrat/900Black/Montserrat_900Black.ttf"
F_EXTRABOLD = f"{FONT_DIR}/@expo-google-fonts/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf"
F_BOLD = f"{FONT_DIR}/@expo-google-fonts/montserrat/700Bold/Montserrat_700Bold.ttf"
F_SEMIBOLD = f"{FONT_DIR}/@expo-google-fonts/inter/600SemiBold/Inter_600SemiBold.ttf"
F_REGULAR = f"{FONT_DIR}/@expo-google-fonts/inter/400Regular/Inter_400Regular.ttf"
F_MONO = f"{FONT_DIR}/@expo-google-fonts/dm-mono/500Medium/DMMono_500Medium.ttf"
F_SCRIPT = f"{FONT_DIR}/@expo-google-fonts/mr-dafoe/400Regular/MrDafoe_400Regular.ttf"

_FONT_CACHE = {}


def get_font(path: str, size: int):
    k = (path, int(size))
    if k not in _FONT_CACHE:
        _FONT_CACHE[k] = ImageFont.truetype(path, int(size))
    return _FONT_CACHE[k]


def fit_font(path: str, text: str, max_size: int, max_w: int, min_size: int = 18):
    sz = max_size
    dummy = Image.new("RGBA", (8, 8))
    d = ImageDraw.Draw(dummy)
    while sz >= min_size:
        f = get_font(path, sz)
        if d.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        sz -= 2
    return get_font(path, min_size)


# ==============================================================================
# EASING & MATH HELPERS
# ==============================================================================
def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(v)))


def prog(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease_out_cubic(t):
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1.0 - ((-2 * t + 2) ** 3) / 2.0


def ease_out_back(t, s=1.45):
    t = clamp(t)
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def ease_out_expo(t):
    t = clamp(t)
    return 1.0 if t >= 1.0 else 1.0 - 2.0 ** (-10.0 * t)


def fmt_fcfa(val: int) -> str:
    s = f"{int(round(val)):,}".replace(",", " ")
    return f"{s} F"


# ==============================================================================
# VECTOR ICONS & UI PRIMITIVES (Zero Unicode Emoji `[]` Boxes!)
# ==============================================================================
def draw_check_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, bg_col, fg_col=(255, 255, 255, 255)):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg_col)
    pts = [
        (cx - int(r * 0.42), cy + int(r * 0.02)),
        (cx - int(r * 0.10), cy + int(r * 0.36)),
        (cx + int(r * 0.46), cy - int(r * 0.32)),
    ]
    draw.line(pts, fill=fg_col, width=max(3, r // 4), joint="curve")


def draw_cross_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, bg_col, fg_col=(255, 255, 255, 255)):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg_col)
    d = int(r * 0.38)
    w = max(3, r // 4)
    draw.line([(cx - d, cy - d), (cx + d, cy + d)], fill=fg_col, width=w)
    draw.line([(cx - d, cy + d), (cx + d, cy - d)], fill=fg_col, width=w)


def draw_doc_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color):
    w = int(size * 0.72)
    h = int(size * 0.92)
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = x0 + w, y0 + h
    draw.rounded_rectangle((x0, y0, x1, y1), radius=max(4, size // 8), outline=color, width=3, fill=(color[0], color[1], color[2], 35))
    for i in range(3):
        ly = y0 + int(h * (0.32 + i * 0.20))
        draw.line([(x0 + int(w * 0.22), ly), (x1 - int(w * 0.22), ly)], fill=color, width=3)


def draw_cursor(canvas: Image.Image, x: float, y: float, clicked: float = 0.0):
    """Draws a crisp macOS/SaaS vector pointer cursor with optional click ripple."""
    ix, iy = int(x), int(y)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    if clicked > 0.01:
        rp = clamp(clicked)
        rad = int(16 + 46 * ease_out_cubic(rp))
        alpha = int(190 * (1.0 - rp))
        if alpha > 5:
            d.ellipse((ix - rad, iy - rad, ix + rad, iy + rad), outline=(56, 189, 248, alpha), width=4)
    scale = 1.0 - 0.14 * math.sin(clamp(clicked) * math.pi)
    pts = [
        (ix, iy),
        (ix, iy + int(38 * scale)),
        (ix + int(10 * scale), iy + int(29 * scale)),
        (ix + int(18 * scale), iy + int(44 * scale)),
        (ix + int(24 * scale), iy + int(41 * scale)),
        (ix + int(16 * scale), iy + int(26 * scale)),
        (ix + int(28 * scale), iy + int(26 * scale)),
    ]
    # Drop shadow
    pts_sh = [(px + 3, py + 4) for px, py in pts]
    d.polygon(pts_sh, fill=(0, 0, 0, 140))
    d.polygon(pts, fill=(255, 255, 255, 255), outline=(15, 23, 42, 255))
    canvas.alpha_composite(overlay)


# ==============================================================================
# 3D PERSPECTIVE WARP ENGINE
# ==============================================================================
def warp_card_3d(
    card_rgba: Image.Image,
    cx: float,
    cy: float,
    scale: float = 1.0,
    yaw_deg: float = 0.0,
    pitch_deg: float = 0.0,
    roll_deg: float = 0.0,
    sheen_pos: float = -1.0,
    shadow_alpha: int = 135,
) -> Image.Image:
    """
    Fast 3D perspective projection (yaw, pitch, roll) with feathered multi-layer
    drop shadow and diagonal specular glass reflection (~12x faster).
    """
    cw, ch = card_rgba.size
    if 0.0 <= sheen_pos <= 1.0:
        sheen_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sheen_layer)
        sx = int(-cw * 0.35 + (cw * 1.7) * sheen_pos)
        band_w = int(cw * 0.18)
        skew = int(ch * 0.32)
        for pad, al in [(32, 18), (14, 30), (0, 46)]:
            poly = [
                (sx - pad, 0),
                (sx + band_w + pad, 0),
                (sx + band_w + pad - skew, ch),
                (sx - pad - skew, ch),
            ]
            sd.polygon(poly, fill=(56, 189, 248, al))
        # Preserve card alpha mask so transparent corners stay transparent
        work = Image.alpha_composite(card_rgba, sheen_layer)
        work.putalpha(card_rgba.getchannel("A"))
    else:
        work = card_rgba

    hw, hh = (cw * scale) / 2.0, (ch * scale) / 2.0
    corners_3d = np.array([
        [-hw, -hh, 0.0],
        [hw, -hh, 0.0],
        [hw, hh, 0.0],
        [-hw, hh, 0.0],
    ], dtype=np.float32)

    yr = math.radians(yaw_deg)
    pr = math.radians(pitch_deg)
    rr = math.radians(roll_deg)

    ry = np.array([
        [math.cos(yr), 0.0, math.sin(yr)],
        [0.0, 1.0, 0.0],
        [-math.sin(yr), 0.0, math.cos(yr)],
    ], dtype=np.float32)
    rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, math.cos(pr), -math.sin(pr)],
        [0.0, math.sin(pr), math.cos(pr)],
    ], dtype=np.float32)
    rz = np.array([
        [math.cos(rr), -math.sin(rr), 0.0],
        [math.sin(rr), math.cos(rr), 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

    rot = rz @ rx @ ry
    focal = 1850.0
    dst_pts = []
    for pt in corners_3d:
        r_pt = rot @ pt
        z_eff = max(300.0, focal + r_pt[2])
        px = cx + (r_pt[0] * focal) / z_eff
        py = cy + (r_pt[1] * focal) / z_eff
        dst_pts.append([px, py])
    dst_pts = np.array(dst_pts, dtype=np.float32)

    src_pts = np.array([
        [0.0, 0.0],
        [float(cw), 0.0],
        [float(cw), float(ch)],
        [0.0, float(ch)],
    ], dtype=np.float32)

    out_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    if shadow_alpha > 0:
        sd = ImageDraw.Draw(out_layer, "RGBA")
        ox = 14.0 - yaw_deg * 0.55
        oy = 26.0 + pitch_deg * 0.45
        for exp_px, mult in [(22.0, 0.22), (11.0, 0.35), (3.0, 0.50)]:
            sh_pts = []
            for p in dst_pts:
                dx_c = 1.0 if p[0] >= cx else -1.0
                dy_c = 1.0 if p[1] >= cy else -1.0
                sh_pts.append((float(p[0] + ox + dx_c * exp_px), float(p[1] + oy + dy_c * exp_px)))
            sd.polygon(sh_pts, fill=(2, 6, 18, int(shadow_alpha * mult)))

    mat = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(
        np.array(work, dtype=np.uint8),
        mat,
        (W, H),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    out_layer.alpha_composite(Image.fromarray(warped, mode="RGBA"))
    return out_layer


# ==============================================================================
# AUTHENTIC DEVIS DESIGNER A4 DOCUMENT GENERATOR (`DEV-2026-014`)
# ==============================================================================
DEVIS_LINES = [
    ("Création de logo — 3 propositions", "1", "120 000 F", 120000),
    ("Charte graphique (PDF, 12 pages)", "1", "180 000 F", 180000),
    ("Impression 500 cartes de visite", "500", "150 F", 75000),
    ("Retouches et fichiers sources", "3", "15 000 F", 45000),
]


def render_a4_devis_card(
    template_style: str = "Modern",
    accent_rgb=(37, 99, 235),
    visible_lines: float = 4.0,
    total_progress: float = 1.0,
    sig_progress: float = 0.0,
    is_facture: bool = False,
    status_label: str = "BROUILLON",
    highlight_edit: float = 0.0,
    currency: str = "F CFA",
) -> Image.Image:
    """
    Renders a crisp A4 Devis/Facture document (760x1040 RGBA) matching
    https://devis-designer-app.jerode.workers.dev/ (`Atelier Kpodé` -> `SARL Sunlè`).
    """
    cw, ch = 760, 1040
    dark_mode = template_style in ("Corporate", "Adapted")
    bg_col = (18, 22, 34, 255) if dark_mode else (255, 255, 255, 255)
    txt_main = (248, 250, 252, 255) if dark_mode else (15, 23, 42, 255)
    txt_muted = (148, 163, 184, 255) if dark_mode else (100, 116, 139, 255)
    row_alt = (28, 34, 50, 255) if dark_mode else (248, 250, 252, 255)
    border_col = (51, 65, 85, 255) if dark_mode else (226, 232, 240, 255)

    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=24, fill=bg_col, outline=border_col, width=3)

    ar, ag, ab = accent_rgb
    doc_type = "FACTURE" if is_facture else "DEVIS"
    doc_num = "FAC-2026-014" if is_facture else "DEV-2026-014"

    # Top header banner depending on template style
    if template_style in ("Modern", "Studio", "Corporate", "Purple", "Clean Gradient"):
        d.rounded_rectangle((0, 0, cw - 1, 148), radius=24, fill=(ar, ag, ab, 255))
        d.rectangle((0, 110, cw - 1, 148), fill=(ar, ag, ab, 255))
        d.text((40, 28), doc_type, font=get_font(F_BLACK, 40), fill=(255, 255, 255, 255))
        d.text((40, 78), f"PROPOSITION COMMERCIALE · {doc_num}", font=get_font(F_BOLD, 16), fill=(255, 255, 255, 225))
        d.text((40, 106), "Émis le 31/08/2026 · Valide jusqu'au 30/09/2026", font=get_font(F_REGULAR, 14), fill=(255, 255, 255, 200))
    else:
        # Minimal / Fresh / Signature top bar
        d.rounded_rectangle((0, 0, cw - 1, 16), radius=8, fill=(ar, ag, ab, 255))
        d.text((40, 34), doc_type, font=get_font(F_BLACK, 42), fill=(ar, ag, ab, 255))
        d.text((40, 86), f"N° {doc_num} · Émis le 31/08/2026", font=get_font(F_BOLD, 16), fill=txt_main)
        d.text((40, 112), "Valide jusqu'au 30/09/2026", font=get_font(F_REGULAR, 14), fill=txt_muted)

    # Status pill in top-right
    status_colors = {
        "BROUILLON": (100, 116, 139),
        "ENVOYÉ": (59, 130, 246),
        "ACCEPTÉ": (139, 92, 246),
        "PAYÉ ✓": (16, 185, 129),
    }
    sc = status_colors.get(status_label, (16, 185, 129))
    d.rounded_rectangle((cw - 210, 34, cw - 36, 78), radius=22, fill=(255, 255, 255, 245))
    d.rounded_rectangle((cw - 210, 34, cw - 36, 78), radius=22, outline=(*sc, 255), width=3)
    f_st = get_font(F_EXTRABOLD, 16)
    st_txt = status_label.replace(" ✓", "")
    bb_s = d.textbbox((0, 0), st_txt, font=f_st)
    d.text((cw - 123 - (bb_s[2] - bb_s[0]) // 2, 46), st_txt, font=f_st, fill=(*sc, 255))

    # Template badge pill
    d.rounded_rectangle((cw - 210, 88, cw - 36, 122), radius=14, fill=(0, 0, 0, 65))
    d.text((cw - 194, 96), f"Modèle : {template_style}", font=get_font(F_SEMIBOLD, 14), fill=(255, 255, 255, 235))

    # Emetteur & Client boxes (y=168..310)
    d.rounded_rectangle((36, 168, 366, 312), radius=14, fill=row_alt, outline=border_col, width=2)
    d.text((54, 180), "DE (ÉMETTEUR)", font=get_font(F_BOLD, 13), fill=(ar, ag, ab, 255))
    d.text((54, 202), "Atelier Kpodé", font=get_font(F_EXTRABOLD, 21), fill=txt_main)
    d.text((54, 230), "Design graphique & impression", font=get_font(F_SEMIBOLD, 14), fill=txt_muted)
    d.text((54, 252), "contact@atelier-kpode.bj", font=get_font(F_REGULAR, 13), fill=txt_muted)
    d.text((54, 272), "+229 01 00 00 00 00 · Cotonou, Bénin", font=get_font(F_REGULAR, 13), fill=txt_muted)

    d.rounded_rectangle((394, 168, cw - 36, 312), radius=14, fill=row_alt, outline=border_col, width=2)
    d.text((412, 180), "POUR (CLIENT)", font=get_font(F_BOLD, 13), fill=(ar, ag, ab, 255))
    d.text((412, 202), "M. Bidossessi — SARL Sunlè", font=get_font(F_EXTRABOLD, 20), fill=txt_main)
    d.text((412, 230), "commandes@sunle.bj", font=get_font(F_SEMIBOLD, 14), fill=txt_muted)
    d.text((412, 252), "Porto-Novo, Bénin", font=get_font(F_REGULAR, 13), fill=txt_muted)
    d.text((412, 274), "Objet : Prestations de design", font=get_font(F_SEMIBOLD, 13), fill=(ar, ag, ab, 255))

    # Table Header (y=332..376)
    d.rounded_rectangle((36, 332, cw - 36, 376), radius=10, fill=(ar, ag, ab, 32 if dark_mode else 24))
    f_th = get_font(F_EXTRABOLD, 14)
    th_col = (ar, ag, ab, 255)
    d.text((54, 345), "DÉSIGNATION", font=f_th, fill=th_col)
    d.text((440, 345), "QTÉ", font=f_th, fill=th_col)
    d.text((515, 345), "P.U. HT", font=f_th, fill=th_col)
    d.text((628, 345), "MONTANT", font=f_th, fill=th_col)

    # Table Rows (y=384..608)
    row_h = 54
    for idx, (desc, qte, pu, total_val) in enumerate(DEVIS_LINES):
        line_alpha = clamp(visible_lines - idx)
        if line_alpha <= 0.01:
            continue
        ry = 384 + idx * (row_h + 6)
        slide_x = int((1.0 - ease_out_cubic(line_alpha)) * 40)
        a_int = int(255 * line_alpha)

        if idx % 2 == 1:
            d.rounded_rectangle((36 + slide_x, ry, cw - 36 + slide_x, ry + row_h), radius=8, fill=row_alt)

        # Highlight row 0 when demonstrating Direct Live Editing (Scene 4)
        if idx == 0 and highlight_edit > 0.01:
            ha = int(230 * highlight_edit)
            d.rounded_rectangle(
                (34, ry - 2, cw - 34, ry + row_h + 2),
                radius=10,
                outline=(56, 189, 248, ha),
                width=3,
                fill=(56, 189, 248, int(28 * highlight_edit)),
            )

        d.text((54 + slide_x, ry + 16), desc, font=get_font(F_SEMIBOLD, 16), fill=(txt_main[0], txt_main[1], txt_main[2], a_int))
        d.text((445 + slide_x, ry + 16), qte, font=get_font(F_MONO, 15), fill=(txt_muted[0], txt_muted[1], txt_muted[2], a_int))
        d.text((512 + slide_x, ry + 16), pu, font=get_font(F_MONO, 15), fill=(txt_muted[0], txt_muted[1], txt_muted[2], a_int))
        d.text((624 + slide_x, ry + 16), fmt_fcfa(total_val), font=get_font(F_BOLD, 16), fill=(txt_main[0], txt_main[1], txt_main[2], a_int))

    # Totals Box (y=638..788)
    tp = clamp(total_progress)
    sub_ht = int(round(420000 * tp))
    tva_val = int(round(75600 * tp))
    ttc_val = int(round(495600 * tp))

    d.rounded_rectangle((380, 638, cw - 36, 792), radius=16, fill=row_alt, outline=border_col, width=2)
    d.text((404, 654), "Sous-total HT", font=get_font(F_SEMIBOLD, 15), fill=txt_muted)
    d.text((590, 654), fmt_fcfa(sub_ht), font=get_font(F_MONO, 16), fill=txt_main)

    d.text((404, 686), "TVA (18%)", font=get_font(F_SEMIBOLD, 15), fill=txt_muted)
    d.text((590, 686), fmt_fcfa(tva_val), font=get_font(F_MONO, 16), fill=txt_main)

    # Grand Total Pill
    d.rounded_rectangle((394, 722, cw - 50, 778), radius=12, fill=(ar, ag, ab, 255))
    d.text((412, 738), "TOTAL TTC", font=get_font(F_EXTRABOLD, 17), fill=(255, 255, 255, 255))

    if currency == "EUR €":
        ttc_str = "755,50 €"
    elif currency == "USD $":
        ttc_str = "826.00 $"
    else:
        ttc_str = f"{fmt_fcfa(ttc_val)} CFA"
    f_ttc = fit_font(F_BLACK, ttc_str, 22, 185)
    d.text((535, 736), ttc_str, font=f_ttc, fill=(255, 255, 255, 255))

    # Conditions Box on the left (y=638..792)
    d.rounded_rectangle((36, 638, 362, 792), radius=14, fill=row_alt, outline=border_col, width=2)
    d.text((54, 654), "CONDITIONS DE RÈGLEMENT", font=get_font(F_BOLD, 13), fill=(ar, ag, ab, 255))
    d.text((54, 682), "• Acompte de 30% à la signature", font=get_font(F_REGULAR, 14), fill=txt_muted)
    d.text((54, 706), "  du devis (148 680 F CFA).", font=get_font(F_SEMIBOLD, 14), fill=txt_main)
    d.text((54, 734), "• Solde à la livraison finale.", font=get_font(F_REGULAR, 14), fill=txt_muted)
    d.text((54, 758), "• Paiement Mobile Money / Virement.", font=get_font(F_REGULAR, 13), fill=txt_muted)

    # Signatures Area (y=812..982)
    d.rounded_rectangle((36, 812, 362, 976), radius=14, fill=row_alt, outline=border_col, width=2)
    d.text((54, 826), "LE PRESTATAIRE — Atelier Kpodé", font=get_font(F_BOLD, 13), fill=txt_muted)
    d.text((68, 862), "Atelier Kpodé", font=get_font(F_SCRIPT, 38), fill=(ar, ag, ab, 220))
    d.text((54, 938), "Cachet & Signature certifiés", font=get_font(F_REGULAR, 12), fill=txt_muted)

    d.rounded_rectangle((380, 812, cw - 36, 976), radius=14, fill=row_alt, outline=(*accent_rgb, 255) if sig_progress > 0 else border_col, width=3 if sig_progress > 0 else 2)
    d.text((400, 826), "LE CLIENT — M. Bidossessi (SARL Sunlè)", font=get_font(F_BOLD, 13), fill=txt_muted)

    if sig_progress > 0.01:
        sp = clamp(sig_progress)
        # Animated handwritten Bézier path for client signature
        sig_pts = [
            (416, 912), (434, 868), (448, 916), (470, 874),
            (494, 908), (522, 866), (546, 904), (578, 882),
            (612, 898), (648, 870), (678, 892),
        ]
        n_seg = max(2, int(len(sig_pts) * sp))
        d.line(sig_pts[:n_seg], fill=(16, 185, 129, 255), width=5, joint="curve")
        if sp > 0.65:
            d.rounded_rectangle((400, 934, 690, 964), radius=8, fill=(16, 185, 129, 32))
            d.text((412, 940), "Signé en ligne le 31/08/2026 · Certifié PDF", font=get_font(F_BOLD, 13), fill=(16, 185, 129, 255))
    else:
        d.text((400, 890), "Signez ici avec le doigt ou la souris...", font=get_font(F_REGULAR, 14), fill=txt_muted)

    # Footer
    d.text((210, 998), "Atelier Kpodé · contact@atelier-kpode.bj · Page 1 / 1", font=get_font(F_REGULAR, 13), fill=txt_muted)
    return card


# Pre-cache static base background gradients & grid for speed
def build_base_background() -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W * 0.5) / W
    ny = (yy - H * 0.35) / H
    dist = np.sqrt(nx * nx + ny * ny)
    r = np.clip(18.0 - dist * 16.0, 6.0, 24.0)
    g = np.clip(22.0 - dist * 18.0, 8.0, 28.0)
    b = np.clip(44.0 - dist * 26.0, 16.0, 52.0)
    rgb = np.stack([r, g, b], axis=-1).astype(np.uint8)
    pil_bg = Image.fromarray(rgb, mode="RGB").convert("RGBA")
    d = ImageDraw.Draw(pil_bg)
    # Subtle perspective tech grid
    for gx in range(0, W, 90):
        d.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 7), width=1)
    for gy in range(0, H, 90):
        d.line([(0, gy), (W, gy)], fill=(255, 255, 255, 7), width=1)
    return np.array(pil_bg, dtype=np.uint8)


BASE_BG_RGBA = build_base_background()
_CARD_CACHE = {}


def get_cached_devis_card(style: str, accent_rgb):
    k = (style, accent_rgb)
    if k not in _CARD_CACHE:
        _CARD_CACHE[k] = render_a4_devis_card(
            template_style=style,
            accent_rgb=accent_rgb,
            visible_lines=4.0,
            total_progress=1.0,
            sig_progress=0.0,
            is_facture=False,
            status_label="ENVOYÉ",
        )
    return _CARD_CACHE[k]


def draw_top_brand_bar(canvas: Image.Image, step_badge: str, accent=(56, 189, 248)):
    d = ImageDraw.Draw(canvas)
    # Glass top pill
    d.rounded_rectangle((48, 58, W - 48, 134), radius=38, fill=(15, 23, 42, 215), outline=(255, 255, 255, 38), width=2)
    # Brand dot + name
    d.ellipse((76, 80, 108, 112), fill=(*accent, 255))
    draw_doc_icon(d, 92, 96, 22, (255, 255, 255, 255))
    d.text((124, 78), "DEVIS DESIGNER", font=get_font(F_BLACK, 24), fill=(255, 255, 255, 255))
    d.text((352, 83), "· devis-designer-app.jerode.workers.dev", font=get_font(F_MONO, 16), fill=(148, 163, 184, 255))

    # Right step pill
    f_b = get_font(F_BOLD, 16)
    bb = d.textbbox((0, 0), step_badge, font=f_b)
    bw = bb[2] - bb[0] + 36
    d.rounded_rectangle((W - 68 - bw, 72, W - 68, 120), radius=24, fill=(*accent, 42), outline=(*accent, 220), width=2)
    d.text((W - 68 - bw + 18, 84), step_badge, font=f_b, fill=(255, 255, 255, 255))


# ==============================================================================
# SCENE RENDERERS (8 Unique Motion Design Scenes, 0.0s -> 52.0s)
# ==============================================================================
def render_scene_1_hook(canvas: Image.Image, t: float):
    """Scene 1 (0.0s - 6.2s): Shatter messy Word/Excel -> Reveal Devis Designer 3D Hero."""
    d = ImageDraw.Draw(canvas)
    draw_top_brand_bar(canvas, "100 % WEB · 0 INSTALLATION", (56, 189, 248))

    if t < 2.1:
        # Phase 1A: Frustrating messy Word/Excel spreadsheets getting crossed out & shattering
        p_in = ease_out_back(prog(t, 0.0, 0.55))
        shatter = ease_in_out_cubic(prog(t, 1.35, 2.05))

        d.text((84, int(190 - 30 * (1 - p_in))), "ENCORE EN TRAIN DE BRICOLER", font=get_font(F_EXTRABOLD, 42), fill=(248, 113, 113, int(255 * (1 - shatter))))
        d.text((84, int(248 - 30 * (1 - p_in))), "VOS DEVIS SUR WORD OU EXCEL ?", font=get_font(F_BLACK, 48), fill=(255, 255, 255, int(255 * (1 - shatter))))

        bad_cards = [
            ("Tableau_Bricolé_v4_FINAL.xlsx", "Formule #VALEUR! · Mise en page cassée", -12, 480),
            ("Devis_Word_Décalé.docx", "Marges tordues · Aucun suivi client", 9, 820),
            ("Calculatrice_TVA_Manuelle", "Erreurs de calcul · Pas de signature", -6, 1160),
        ]
        for idx, (title, sub, ang, base_y) in enumerate(bad_cards):
            cp = ease_out_back(prog(t, 0.12 * idx, 0.55 + 0.12 * idx))
            dx = int((idx - 1) * 260 * shatter)
            dy = int(base_y + 180 * shatter)
            alpha = int(240 * cp * (1.0 - shatter))
            if alpha <= 10:
                continue
            box = Image.new("RGBA", (860, 250), (0, 0, 0, 0))
            bd = ImageDraw.Draw(box)
            bd.rounded_rectangle((0, 0, 859, 249), radius=24, fill=(38, 18, 28, alpha), outline=(239, 68, 68, alpha), width=4)
            draw_cross_icon(bd, 82, 125, 42, (239, 68, 68, alpha))
            bd.text((150, 72), title, font=get_font(F_EXTRABOLD, 30), fill=(255, 255, 255, alpha))
            bd.text((150, 128), sub, font=get_font(F_SEMIBOLD, 24), fill=(252, 165, 165, alpha))
            warped = warp_card_3d(box, W * 0.5 + dx, dy, scale=cp, yaw_deg=ang + 25 * shatter, pitch_deg=8 * shatter, shadow_alpha=alpha // 2)
            canvas.alpha_composite(warped)
        return

    # Phase 1B (2.1s - 6.2s): Hero Reveal of Devis Designer
    lt = t - 2.1
    p_hero = ease_out_back(prog(lt, 0.0, 0.75))

    # Headline
    d.text((72, 178), "VOS DEVIS & FACTURES", font=get_font(F_BLACK, 58), fill=(255, 255, 255, 255))
    d.text((72, 250), "AUSSI SOIGNÉS QUE VOTRE TRAVAIL.", font=get_font(F_EXTRABOLD, 42), fill=(56, 189, 248, 255))

    # 3D Floating Hero Document
    doc_img = get_cached_devis_card("Modern", (37, 99, 235))
    yaw = -14.0 * math.cos(lt * 1.3)
    pitch = 8.0 * math.sin(lt * 1.1)
    sheen = prog(lt, 0.4, 2.8)
    warped_doc = warp_card_3d(doc_img, W * 0.5, 980, scale=0.92 * p_hero, yaw_deg=yaw, pitch_deg=pitch, sheen_pos=sheen)
    canvas.alpha_composite(warped_doc)

    # Floating KPI Badges around the 3D document
    badges = [
        (0.25, 76, 1560, "20 EXPORTS OFFERTS", "0 F · Sans carte bancaire", (16, 185, 129)),
        (0.45, 556, 1560, "12 MODÈLES INCLUS", "Devis & Factures A4 / SVG", (59, 130, 246)),
        (0.65, 76, 1720, "3 DEVISES INTÉGRÉES", "Franc CFA · Euro € · Dollar $", (245, 158, 11)),
        (0.85, 556, 1720, "ZÉRO COMPTE REQUIS", "S'ouvre direct dans le navigateur", (168, 85, 247)),
    ]
    d = ImageDraw.Draw(canvas)
    for delay, bx, by, b_title, b_sub, b_col in badges:
        bp = ease_out_back(prog(lt, delay, delay + 0.55))
        if bp <= 0.01:
            continue
        yy = int(by + (1.0 - bp) * 60)
        d.rounded_rectangle((bx, yy, bx + 448, yy + 132), radius=22, fill=(15, 23, 42, 235), outline=(*b_col, 255), width=3)
        draw_check_icon(d, bx + 48, yy + 66, 24, (*b_col, 255))
        d.text((bx + 90, yy + 30), b_title, font=get_font(F_EXTRABOLD, 22), fill=(255, 255, 255, 255))
        d.text((bx + 90, yy + 68), b_sub, font=get_font(F_SEMIBOLD, 18), fill=(203, 213, 225, 255))


def render_scene_2_live_builder(canvas: Image.Image, t: float):
    """Scene 2 (6.2s - 13.2s): Step 1 & 2 — Live Line Items + Rolling Total 495 600 F CFA."""
    lt = t - 6.2
    draw_top_brand_bar(canvas, "ÉTAPES 1 & 2 · CALCUL EN DIRECT", (16, 185, 129))
    d = ImageDraw.Draw(canvas)

    d.text((68, 170), "AJOUTEZ VOS LIGNES :", font=get_font(F_EXTRABOLD, 40), fill=(16, 185, 129, 255))
    d.text((68, 224), "TVA, ACOMPTE & TOTAL CALCULÉS EN DIRECT", font=get_font(F_BLACK, 36), fill=(255, 255, 255, 255))

    # Staggered line items reveal (0.3s -> 3.4s)
    vis_lines = clamp(lt / 0.78, 0.0, 4.0)
    tot_prog = ease_out_cubic(prog(lt, 0.4, 3.8))

    # Currency toggle cycling at lt > 4.6s
    if lt < 4.6:
        curr = "F CFA"
    elif lt < 5.6:
        curr = "EUR €"
    elif lt < 6.3:
        curr = "USD $"
    else:
        curr = "F CFA"

    doc_card = render_a4_devis_card(
        template_style="Modern",
        accent_rgb=(16, 185, 129),
        visible_lines=vis_lines,
        total_progress=tot_prog,
        currency=curr,
    )
    warped = warp_card_3d(
        doc_card,
        W * 0.5,
        890,
        scale=0.94,
        yaw_deg=8.0 * math.sin(lt * 0.9),
        pitch_deg=-4.0 * math.cos(lt * 0.8),
        sheen_pos=prog(lt, 3.2, 5.5),
    )
    canvas.alpha_composite(warped)

    # Bottom Live Total Callout Bar + Currency Switcher (y=1470..1820)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((56, 1465, W - 56, 1665), radius=26, fill=(15, 23, 42, 240), outline=(16, 185, 129, 255), width=3)
    d.text((92, 1492), "TOTAL TTC CALCULÉ AUTOMATIQUEMENT", font=get_font(F_BOLD, 20), fill=(148, 163, 184, 255))

    val_num = int(round(495600 * tot_prog))
    big_str = "755,50 €" if curr == "EUR €" else ("826.00 $" if curr == "USD $" else f"{fmt_fcfa(val_num)} CFA")
    d.text((92, 1532), big_str, font=get_font(F_BLACK, 64), fill=(52, 211, 153, 255))
    d.text((92, 1614), "Sous-total HT : 420 000 F  ·  TVA (18%) : 75 600 F  ·  Acompte 30% : 148 680 F", font=get_font(F_SEMIBOLD, 19), fill=(226, 232, 240, 255))

    # 3 Currency Pills
    currencies = ["F CFA", "EUR €", "USD $"]
    for idx, c_label in enumerate(currencies):
        cx0 = 68 + idx * 322
        active = (c_label == curr)
        bg = (16, 185, 129, 255) if active else (30, 41, 59, 220)
        d.rounded_rectangle((cx0, 1700, cx0 + 300, 1784), radius=20, fill=bg, outline=(255, 255, 255, 90 if active else 30), width=2)
        d.text((cx0 + 78, 1724), c_label, font=get_font(F_EXTRABOLD, 28), fill=(255, 255, 255, 255))


def render_scene_3_templates_carousel(canvas: Image.Image, t: float):
    """Scene 3 (13.2s - 20.2s): Step 3 — 12 Templates 3D Carousel + Live Theme Color Picker."""
    lt = t - 13.2
    draw_top_brand_bar(canvas, "ÉTAPE 3 · 12 MODÈLES INCLUS", (139, 92, 246))
    d = ImageDraw.Draw(canvas)

    d.text((68, 170), "12 MISES EN PAGE PRO INCLUSES", font=get_font(F_BLACK, 46), fill=(255, 255, 255, 255))
    d.text((68, 232), "Changez de modèle, de couleur et de police en 1 clic", font=get_font(F_SEMIBOLD, 26), fill=(196, 181, 253, 255))

    templates = [
        ("Modern", "Swiss contemporain", (37, 99, 235)),
        ("Studio", "Cards arrondies SaaS", (139, 92, 246)),
        ("Corporate", "Mode sombre & Or", (245, 158, 11)),
        ("Minimal", "Ultra-épuré A4", (16, 185, 129)),
        ("Signature", "Éditorial & Cachet", (236, 72, 153)),
        ("Clean Gradient", "Bulles dégradées", (6, 182, 212)),
    ]

    # Smooth continuous carousel index (0 -> 5)
    scroll = (lt / 6.8) * 4.8
    active_idx = int(round(clamp(scroll, 0, len(templates) - 1)))

    # Draw side cards first, center card last
    order = sorted(range(len(templates)), key=lambda i: -abs(i - scroll))
    for i in order:
        diff = i - scroll
        if abs(diff) > 2.2:
            continue
        style_name, style_desc, acc_col = templates[i]
        card_img = get_cached_devis_card(style_name, acc_col)
        cx = W * 0.5 + diff * 360.0
        cy = 910.0 + abs(diff) * 55.0
        sc = max(0.55, 0.90 - abs(diff) * 0.20)
        yaw = clamp(diff * -26.0, -45.0, 45.0)
        sheen = (lt * 0.9) % 1.0 if i == active_idx else -1.0
        warped = warp_card_3d(card_img, cx, cy, scale=sc, yaw_deg=yaw, pitch_deg=4.0, sheen_pos=sheen)
        canvas.alpha_composite(warped)

    # Bottom 12-Template Pill Grid + Active Theme Swatches (y=1470..1830)
    d = ImageDraw.Draw(canvas)
    all_12 = [
        "1. Modern", "2. Studio", "3. Minimal", "4. Fresh",
        "5. Creative", "6. Signature", "7. Adapted", "8. Minimalist",
        "9. Purple", "10. Corporate", "11. Modern Orange", "12. Clean Gradient",
    ]
    active_name = templates[active_idx][0]
    active_col = templates[active_idx][2]

    d.rounded_rectangle((48, 1465, W - 48, 1825), radius=26, fill=(15, 23, 42, 240), outline=(*active_col, 255), width=3)
    d.text((82, 1490), f"MODÈLE ACTIF : {active_name.upper()} — {templates[active_idx][1]}", font=get_font(F_EXTRABOLD, 24), fill=(255, 255, 255, 255))

    for idx, t_name in enumerate(all_12):
        col_i = idx % 3
        row_i = idx // 3
        px = 78 + col_i * 312
        py = 1545 + row_i * 64
        is_hi = (active_name in t_name)
        fill_c = (*active_col, 255) if is_hi else (30, 41, 59, 210)
        d.rounded_rectangle((px, py, px + 294, py + 50), radius=12, fill=fill_c, outline=(255, 255, 255, 120 if is_hi else 28), width=2)
        d.text((px + 18, py + 13), t_name, font=get_font(F_BOLD, 17), fill=(255, 255, 255, 255))


def render_scene_4_direct_edit(canvas: Image.Image, t: float):
    """Scene 4 (20.2s - 26.5s): Direct On-Document WYSIWYG Editing + Local Auto-Save."""
    lt = t - 20.2
    draw_top_brand_bar(canvas, "ÉDITION DIRECTE SUR L'APERÇU", (56, 189, 248))
    d = ImageDraw.Draw(canvas)

    d.text((68, 170), "ÉDITION DIRECTE SUR LE DEVIS", font=get_font(F_BLACK, 46), fill=(255, 255, 255, 255))
    d.text((68, 232), "Touchez n'importe quel texte de l'aperçu pour le modifier", font=get_font(F_SEMIBOLD, 25), fill=(56, 189, 248, 255))

    hi = ease_out_cubic(prog(lt, 0.8, 1.5))
    doc_card = render_a4_devis_card(
        template_style="Studio",
        accent_rgb=(59, 130, 246),
        visible_lines=4.0,
        total_progress=1.0,
        highlight_edit=hi,
    )
    warped = warp_card_3d(doc_card, W * 0.5, 885, scale=0.95, yaw_deg=-5.0 + 3.0 * math.sin(lt), pitch_deg=3.0)
    canvas.alpha_composite(warped)

    # Magnified WYSIWYG Callout Pop-up Card (y=1340..1780)
    pop_p = ease_out_back(prog(lt, 1.1, 1.8))
    if pop_p > 0.01:
        box = Image.new("RGBA", (960, 410), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((0, 0, 959, 409), radius=28, fill=(15, 23, 42, 248), outline=(56, 189, 248, 255), width=4)
        bd.rounded_rectangle((28, 26, 360, 72), radius=14, fill=(56, 189, 248, 45))
        bd.text((46, 36), "MODE ÉDITION DIRECTE ACTIF", font=get_font(F_EXTRABOLD, 18), fill=(56, 189, 248, 255))

        # Simulated typing text inside the magnified field
        bd.rounded_rectangle((28, 92, 932, 198), radius=16, fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=3)
        full_txt = "Création de logo — 3 propositions + Pack Réseaux Sociaux"
        n_chars = int(34 + 22 * clamp((lt - 1.6) / 2.2))
        shown_txt = full_txt[:n_chars] + ("|" if int(lt * 4) % 2 == 0 else "")
        bd.text((52, 126), shown_txt, font=get_font(F_BOLD, 25), fill=(255, 255, 255, 255))

        # Auto-save & Carnet de lignes badges
        draw_check_icon(bd, 64, 258, 24, (16, 185, 129, 255))
        bd.text((106, 242), "Sauvegarde automatique dans le navigateur (toutes les 2s)", font=get_font(F_BOLD, 22), fill=(255, 255, 255, 255))

        draw_check_icon(bd, 64, 332, 24, (59, 130, 246, 255))
        bd.text((106, 316), "Carnet client & tarifs mémorisés + Export/Import JSON", font=get_font(F_BOLD, 22), fill=(203, 213, 225, 255))

        w_pop = warp_card_3d(box, W * 0.5, 1580, scale=pop_p, yaw_deg=0.0, pitch_deg=0.0)
        canvas.alpha_composite(w_pop)

    # Animated pointer cursor moving to line 1 and clicking
    cx = 820 - 380 * ease_in_out_cubic(prog(lt, 0.2, 1.0))
    cy = 1100 - 380 * ease_in_out_cubic(prog(lt, 0.2, 1.0))
    click_p = prog(lt, 0.95, 1.45) if 0.95 <= lt <= 1.45 else 0.0
    draw_cursor(canvas, cx, cy, clicked=click_p)


def render_scene_5_signature_and_invoice(canvas: Image.Image, t: float):
    """Scene 5 (26.5s - 33.5s): Online Handwritten Signature + 1-Click Devis -> Facture Conversion."""
    lt = t - 26.5
    is_fac = (lt >= 3.6)
    accent = (16, 185, 129) if is_fac else (245, 158, 11)
    draw_top_brand_bar(canvas, "ÉTAPE 4 · SIGNATURE & FACTURATION", accent)
    d = ImageDraw.Draw(canvas)

    if not is_fac:
        d.text((68, 170), "SIGNATURE EN LIGNE AU DOIGT", font=get_font(F_BLACK, 46), fill=(255, 255, 255, 255))
        d.text((68, 232), "Le client signe directement sur le devis · Date inscrite sur le PDF", font=get_font(F_SEMIBOLD, 23), fill=(251, 191, 36, 255))
    else:
        d.text((68, 170), "CONVERTI EN FACTURE EN 1 CLIC !", font=get_font(F_BLACK, 46), fill=(52, 211, 153, 255))
        d.text((68, 232), "Numérotation automatique FAC-2026-014 & suivi des 5 statuts", font=get_font(F_SEMIBOLD, 23), fill=(255, 255, 255, 255))

    sig_p = clamp((lt - 0.4) / 2.2)
    status_str = "PAYÉ ✓" if is_fac else ("ACCEPTÉ" if sig_p >= 0.95 else "ENVOYÉ")

    doc_card = render_a4_devis_card(
        template_style="Modern",
        accent_rgb=accent,
        visible_lines=4.0,
        total_progress=1.0,
        sig_progress=sig_p,
        is_facture=is_fac,
        status_label=status_str,
    )

    # Flip spin when converting Devis -> Facture at lt = 3.4..4.0s
    flip_p = prog(lt, 3.3, 3.9)
    yaw_spin = math.sin(flip_p * math.pi) * 28.0
    warped = warp_card_3d(doc_card, W * 0.5, 865, scale=0.93, yaw_deg=yaw_spin, pitch_deg=-3.0, sheen_pos=prog(lt, 3.6, 5.2))
    canvas.alpha_composite(warped)

    # 5-Status Pipeline Tracker at Bottom (y=1445..1810)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((48, 1450, W - 48, 1810), radius=26, fill=(15, 23, 42, 245), outline=(*accent, 255), width=3)
    d.text((80, 1478), "SUIVI COMPLET DU DOCUMENT (5 STATUTS INTÉGRÉS)", font=get_font(F_EXTRABOLD, 21), fill=(255, 255, 255, 255))

    statuses = [
        ("1. Brouillon", 0.0, (100, 116, 139)),
        ("2. Envoyé", 0.5, (59, 130, 246)),
        ("3. Accepté", 2.2, (139, 92, 246)),
        ("4. Facturé", 3.6, (245, 158, 11)),
        ("5. Payé ✓", 4.4, (16, 185, 129)),
    ]
    for idx, (st_name, trig_t, st_col) in enumerate(statuses):
        active = (lt >= trig_t)
        col_i = idx % 3
        row_i = idx // 3
        px = 78 + col_i * 312
        py = 1540 + row_i * 112
        bg_c = (*st_col, 255) if active else (30, 41, 59, 200)
        d.rounded_rectangle((px, py, px + 292, py + 88), radius=18, fill=bg_c, outline=(255, 255, 255, 140 if active else 30), width=2)
        draw_check_icon(d, px + 42, py + 44, 20, (255, 255, 255, 45) if active else (51, 65, 85, 200))
        d.text((px + 76, py + 28), st_name.replace(" ✓", ""), font=get_font(F_EXTRABOLD, 22), fill=(255, 255, 255, 255))


def render_scene_6_exports(canvas: Image.Image, t: float):
    """Scene 6 (33.5s - 39.8s): Triple Export Engine — PDF A4 Multi-pages, SVG Vectoriel, Présentation Plein Écran."""
    lt = t - 33.5
    draw_top_brand_bar(canvas, "EXPORT PDF A4 · SVG · PRÉSENTATION", (236, 72, 153))
    d = ImageDraw.Draw(canvas)

    d.text((68, 175), "3 FORMATS D'EXPORT PRO", font=get_font(F_BLACK, 52), fill=(255, 255, 255, 255))
    d.text((68, 244), "Prêt à être envoyé sur WhatsApp, imprimé ou présenté en plein écran", font=get_font(F_SEMIBOLD, 23), fill=(244, 114, 182, 255))

    export_cards = [
        (
            0.15,
            520,
            "EXPORT PDF A4 MULTI-PAGES",
            "Pagination automatique, prêt à envoyer sur WhatsApp ou par email avec signature et cachet intégrés.",
            "DEV-2026-014.pdf · Haute Définition",
            (239, 68, 68),
        ),
        (
            0.45,
            980,
            "EXPORT SVG VECTORIEL PUR",
            "Qualité vectorielle infinie sans aucune perte : idéal à confier à votre imprimeur ou graphiste.",
            "DEV-2026-014.svg · Courbes Vectorielles",
            (59, 130, 246),
        ),
        (
            0.75,
            1440,
            "PRÉSENTATION PLEIN ÉCRAN",
            "Affichez le devis en grand chez le client sur téléphone, tablette ou PC et faites-le signer sur place.",
            "Mode Showroom Client · 100 % Mobile & PC",
            (16, 185, 129),
        ),
    ]

    for idx, (delay, cy, title, desc, pill_txt, col) in enumerate(export_cards):
        cp = ease_out_back(prog(lt, delay, delay + 0.65))
        if cp <= 0.01:
            continue
        card = Image.new("RGBA", (940, 390), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 939, 389), radius=28, fill=(15, 23, 42, 245), outline=(*col, 255), width=4)
        cd.rounded_rectangle((32, 34, 152, 154), radius=26, fill=(*col, 45), outline=(*col, 255), width=3)
        draw_doc_icon(cd, 92, 94, 68, (*col, 255))

        cd.text((184, 38), title, font=get_font(F_BLACK, 32), fill=(255, 255, 255, 255))
        # Wrap description into 2 clean lines
        words = desc.split(" ")
        mid = len(words) // 2
        l1 = " ".join(words[:mid])
        l2 = " ".join(words[mid:])
        cd.text((184, 96), l1, font=get_font(F_SEMIBOLD, 22), fill=(203, 213, 225, 255))
        cd.text((184, 130), l2, font=get_font(F_SEMIBOLD, 22), fill=(203, 213, 225, 255))

        cd.rounded_rectangle((184, 188, 760, 246), radius=14, fill=(*col, 38), outline=(*col, 190), width=2)
        cd.text((210, 204), pill_txt, font=get_font(F_MONO, 20), fill=(255, 255, 255, 255))

        draw_check_icon(cd, 212, 314, 22, (*col, 255))
        cd.text((250, 298), "Généré instantanément dans votre navigateur", font=get_font(F_BOLD, 21), fill=(255, 255, 255, 255))

        yaw = (idx - 1) * 5.0 * math.cos(lt * 1.2)
        warped = warp_card_3d(card, W * 0.5, cy, scale=cp, yaw_deg=yaw, pitch_deg=3.0, sheen_pos=prog(lt, delay + 0.5, delay + 2.2))
        canvas.alpha_composite(warped)


def render_scene_7_pricing_and_momo(canvas: Image.Image, t: float):
    """Scene 7 (39.8s - 46.2s): Pricing Bento + Chariow Mobile Money Auto-Activation + Referral."""
    lt = t - 39.8
    draw_top_brand_bar(canvas, "TARIFS & MOBILE MONEY AUTO", (245, 158, 11))
    d = ImageDraw.Draw(canvas)

    d.text((64, 168), "COMMENCEZ GRATUITEMENT.", font=get_font(F_BLACK, 48), fill=(255, 255, 255, 255))
    d.text((64, 230), "Activation automatique via Mobile Money · Sans prélèvement forcé", font=get_font(F_SEMIBOLD, 23), fill=(251, 191, 36, 255))

    plans = [
        (0.10, 64, 310, "DÉCOUVERTE", "0 F CFA", "20 exports offerts / 30j", "Tous les 12 modèles inclus", (16, 185, 129)),
        (0.28, 556, 310, "ABONNEMENT 1 MOIS", "2 000 F CFA", "Exports & signatures illimités", "Activation immédiate sans code", (59, 130, 246)),
        (0.46, 64, 670, "ABONNEMENT 1 AN ★", "15 000 F CFA", "Soit 1 250 F/mois (-9 000 F)", "12 mois d'exports illimités", (245, 158, 11)),
        (0.64, 556, 670, "DESIGN SUR MESURE", "5 000 F CFA", "Créé à vos couleurs uniques", "+ 1 mois illimité inclus", (236, 72, 153)),
    ]

    for delay, px, py, p_title, p_price, p_l1, p_l2, p_col in plans:
        cp = ease_out_back(prog(lt, delay, delay + 0.55))
        if cp <= 0.01:
            continue
        yy = int(py + (1.0 - cp) * 70)
        d.rounded_rectangle((px, yy, px + 460, yy + 325), radius=26, fill=(15, 23, 42, 245), outline=(*p_col, 255), width=4)
        d.rounded_rectangle((px + 24, yy + 24, px + 436, yy + 74), radius=14, fill=(*p_col, 42))
        d.text((px + 42, yy + 36), p_title.replace(" ★", ""), font=get_font(F_EXTRABOLD, 20), fill=(*p_col, 255))
        d.text((px + 28, yy + 96), p_price, font=get_font(F_BLACK, 48), fill=(255, 255, 255, 255))
        draw_check_icon(d, px + 46, yy + 198, 18, (*p_col, 255))
        d.text((px + 78, yy + 184), p_l1, font=get_font(F_BOLD, 19), fill=(241, 245, 249, 255))
        draw_check_icon(d, px + 46, yy + 254, 18, (*p_col, 255))
        d.text((px + 78, yy + 240), p_l2, font=get_font(F_SEMIBOLD, 18), fill=(148, 163, 184, 255))

    # Chariow Mobile Money Banner (y=1040..1380)
    mp = ease_out_back(prog(lt, 0.85, 1.45))
    if mp > 0.01:
        yy = int(1040 + (1.0 - mp) * 60)
        d.rounded_rectangle((64, yy, W - 64, yy + 320), radius=28, fill=(15, 23, 42, 248), outline=(56, 189, 248, 255), width=3)
        d.text((98, yy + 28), "PAIEMENT MOBILE MONEY EN LIGNE (CAISSE CHARIOW)", font=get_font(F_EXTRABOLD, 23), fill=(56, 189, 248, 255))
        d.text((98, yy + 68), "L'offre s'active toute seule dès le paiement confirmé — aucun code à copier !", font=get_font(F_SEMIBOLD, 19), fill=(226, 232, 240, 255))

        momo_ops = [
            ("MTN MoMo", (250, 204, 21), (15, 23, 42)),
            ("Orange Money", (249, 115, 22), (255, 255, 255)),
            ("Wave", (56, 189, 248), (15, 23, 42)),
            ("Moov Money", (37, 99, 235), (255, 255, 255)),
        ]
        for idx, (op_name, bg_c, fg_c) in enumerate(momo_ops):
            ox = 96 + idx * 224
            oy = yy + 130
            d.rounded_rectangle((ox, oy, ox + 206, oy + 78), radius=18, fill=(*bg_c, 255))
            d.text((ox + 22, oy + 24), op_name, font=get_font(F_EXTRABOLD, 21), fill=(*fg_c, 255))

        d.text((98, yy + 240), "Bouton « PRO » dans l'application > Choisissez l'offre > « Payer » > Activé !", font=get_font(F_BOLD, 19), fill=(52, 211, 153, 255))

    # Referral Card (y=1400..1780)
    rp = ease_out_back(prog(lt, 1.35, 1.95))
    if rp > 0.01:
        yy = int(1400 + (1.0 - rp) * 60)
        d.rounded_rectangle((64, yy, W - 64, yy + 360), radius=28, fill=(24, 18, 42, 248), outline=(168, 85, 247, 255), width=3)
        d.text((98, yy + 32), "PROGRAMME PARRAINAGE : 1 AMI = 1 MOIS OFFERT", font=get_font(F_BLACK, 26), fill=(216, 180, 254, 255))
        steps_ref = [
            "1. Partagez votre lien personnel (DDREF-...) sur WhatsApp",
            "2. Votre filleul crée ses devis et fait son 1er export gratuit",
            "3. Vous recevez automatiquement 1 mois d'abonnement offert !",
        ]
        for s_i, s_txt in enumerate(steps_ref):
            sy = yy + 104 + s_i * 74
            draw_check_icon(d, 118, sy + 18, 20, (168, 85, 247, 255))
            d.text((156, sy + 2), s_txt, font=get_font(F_BOLD, 21), fill=(255, 255, 255, 255))


def render_scene_8_finale_cta(canvas: Image.Image, t: float):
    """Scene 8 (46.2s - 52.0s): Grand Finale CTA — devis-designer-app.jerode.workers.dev."""
    lt = t - 46.2
    draw_top_brand_bar(canvas, "ESSAYEZ GRATUITEMENT · 20 EXPORTS", (16, 185, 129))
    d = ImageDraw.Draw(canvas)

    p_in = ease_out_back(prog(lt, 0.0, 0.7))
    d.text((64, 172), "VOTRE PROCHAIN DEVIS", font=get_font(F_BLACK, 54), fill=(255, 255, 255, 255))
    d.text((64, 240), "PEUT ÊTRE LE PLUS BEAU DE LA VILLE.", font=get_font(F_EXTRABOLD, 38), fill=(52, 211, 153, 255))

    # Dual 3D Hero Cards (Studio + Modern)
    c_left = get_cached_devis_card("Studio", (139, 92, 246))
    c_right = render_a4_devis_card(
        template_style="Modern",
        accent_rgb=(16, 185, 129),
        visible_lines=4.0,
        total_progress=1.0,
        sig_progress=1.0,
        is_facture=True,
        status_label="PAYÉ",
    )

    w_left = warp_card_3d(c_left, 330, 830, scale=0.68 * p_in, yaw_deg=18.0, pitch_deg=4.0)
    w_right = warp_card_3d(c_right, 650, 860, scale=0.76 * p_in, yaw_deg=-12.0, pitch_deg=3.0, sheen_pos=(lt * 0.6) % 1.0)
    canvas.alpha_composite(w_left)
    canvas.alpha_composite(w_right)

    # Giant CTA Box at bottom (y=1330..1830)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((48, 1335, W - 48, 1830), radius=32, fill=(15, 23, 42, 248), outline=(52, 211, 153, 255), width=4)

    d.text((88, 1372), "20 EXPORTS OFFERTS · 12 MODÈLES · SANS INSCRIPTION", font=get_font(F_EXTRABOLD, 23), fill=(52, 211, 153, 255))

    # Glowing URL Bar
    d.rounded_rectangle((84, 1432, W - 84, 1542), radius=22, fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=3)
    d.text((118, 1466), "https://devis-designer-app.jerode.workers.dev/", font=get_font(F_MONO, 27), fill=(255, 255, 255, 255))

    # Pulsing CTA Button
    pulse = 1.0 + 0.025 * math.sin(lt * 6.0)
    bw = int(880 * pulse)
    bx0 = (W - bw) // 2
    d.rounded_rectangle((bx0, 1575, bx0 + bw, 1695), radius=28, fill=(16, 185, 129, 255))
    d.text((bx0 + 135, 1614), "OUVRIR L'APPLICATION MAINTENANT", font=get_font(F_BLACK, 29), fill=(255, 255, 255, 255))

    d.text((155, 1735), "Support WhatsApp direct : +229 01 91 94 35 18 · Cotonou, Bénin", font=get_font(F_SEMIBOLD, 21), fill=(148, 163, 184, 255))


# ==============================================================================
# PROCEDURAL 124 BPM SAAS LAUNCH SOUNDTRACK + UI FOLEY SFX
# ==============================================================================
def build_soundtrack_wav(wav_path: str):
    sr = 44100
    n_samples = int(DURATION * sr)
    t = np.arange(n_samples, dtype=np.float32) / sr

    bpm = 124.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4.0

    # Warm inspiring SaaS chord progression: Fmaj7 -> G6 -> Em7 -> Am7
    chords = [
        [174.61, 220.00, 261.63, 329.63],  # Fmaj7
        [196.00, 246.94, 293.66, 329.63],  # G6
        [164.81, 196.00, 246.94, 293.66],  # Em7
        [220.00, 261.63, 329.63, 392.00],  # Am7
    ]

    bar_idx = (t / bar_dur).astype(np.int32) % 4
    pad_l = np.zeros(n_samples, dtype=np.float32)
    pad_r = np.zeros(n_samples, dtype=np.float32)

    for c_i, freqs in enumerate(chords):
        mask = (bar_idx == c_i).astype(np.float32)
        for f_i, f_hz in enumerate(freqs):
            detune = 1.002 if f_i % 2 == 0 else 0.998
            pad_l += mask * 0.045 * np.sin(2.0 * np.pi * f_hz * t)
            pad_r += mask * 0.045 * np.sin(2.0 * np.pi * (f_hz * detune) * t + 0.4)

    # Sub-bass on quarter beats
    beat_phase = (t % beat_dur) / beat_dur
    kick_env = np.exp(-beat_phase * 9.5)
    kick_freq = 54.0 + 75.0 * np.exp(-beat_phase * 28.0)
    kick = 0.22 * kick_env * np.sin(2.0 * np.pi * kick_freq * t)

    # Pluck arpeggio on 16th notes
    step_dur = beat_dur / 4.0
    step_idx = (t / step_dur).astype(np.int32)
    step_phase = (t % step_dur) / step_dur
    arp_notes = np.array([261.63, 329.63, 392.00, 523.25, 659.25, 523.25, 392.00, 329.63], dtype=np.float32)
    arp_freq = arp_notes[step_idx % len(arp_notes)]
    arp_env = np.exp(-step_phase * 11.0)
    arp = 0.065 * arp_env * np.sin(2.0 * np.pi * arp_freq * t)

    # Crisp hi-hat on off-beats
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(n_samples).astype(np.float32)
    hat_phase = ((t + beat_dur * 0.5) % beat_dur) / beat_dur
    hat_env = np.exp(-hat_phase * 35.0)
    hat = 0.03 * hat_env * noise

    mix_l = pad_l + kick + arp * 1.1 + hat
    mix_r = pad_r + kick + arp * 0.9 + hat

    # Helper to inject UI SFX at exact timestamps
    def add_whoosh(t0, dur=0.38, vol=0.22):
        i0 = int(t0 * sr)
        i1 = min(n_samples, i0 + int(dur * sr))
        if i1 <= i0:
            return
        lt_s = np.linspace(0.0, 1.0, i1 - i0, dtype=np.float32)
        env = np.sin(lt_s * np.pi)
        sw = env * vol * np.sin(2.0 * np.pi * (180.0 + 520.0 * lt_s) * lt_s)
        mix_l[i0:i1] += sw
        mix_r[i0:i1] += sw * 0.9

    def add_chime(t0, freq=880.0, dur=0.45, vol=0.20):
        i0 = int(t0 * sr)
        i1 = min(n_samples, i0 + int(dur * sr))
        if i1 <= i0:
            return
        lt_s = np.arange(i1 - i0, dtype=np.float32) / sr
        env = np.exp(-lt_s * 8.5)
        sig = vol * env * (np.sin(2.0 * np.pi * freq * lt_s) + 0.5 * np.sin(2.0 * np.pi * (freq * 1.5) * lt_s))
        mix_l[i0:i1] += sig
        mix_r[i0:i1] += sig

    def add_click(t0, vol=0.24):
        i0 = int(t0 * sr)
        i1 = min(n_samples, i0 + int(0.04 * sr))
        if i1 <= i0:
            return
        lt_s = np.arange(i1 - i0, dtype=np.float32) / sr
        sig = vol * np.exp(-lt_s * 120.0) * np.sin(2.0 * np.pi * 1450.0 * lt_s)
        mix_l[i0:i1] += sig
        mix_r[i0:i1] += sig

    # Scene transitions & UI events SFX
    for wt in [0.05, 2.1, 6.2, 13.2, 20.2, 26.5, 33.5, 39.8, 46.2]:
        add_whoosh(wt, 0.42, 0.22)

    for ct in [2.35, 6.8, 7.6, 8.4, 9.2, 14.5, 16.0, 17.5, 21.2, 27.0, 30.1, 34.0, 35.2, 36.4, 40.5, 41.8, 47.0]:
        add_click(ct, 0.22)

    for dt in [2.2, 9.8, 22.0, 29.0, 30.3, 37.0, 42.5, 44.0, 46.5, 49.0]:
        add_chime(dt, 1046.5, 0.48, 0.18)

    # Fade in / fade out
    fade_in = np.clip(t / 0.8, 0.0, 1.0)
    fade_out = np.clip((DURATION - t) / 1.4, 0.0, 1.0)
    master = fade_in * fade_out

    stereo = np.stack([mix_l * master, mix_r * master], axis=-1)
    peak = np.max(np.abs(stereo)) + 1e-6
    stereo = np.clip((stereo / peak) * 0.88 * 32767.0, -32767, 32767).astype(np.int16)

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())


# ==============================================================================
# MAIN RENDER PIPELINE
# ==============================================================================
def render_frame(f_idx: int) -> np.ndarray:
    t = f_idx / float(FPS)
    canvas = Image.fromarray(BASE_BG_RGBA.copy(), mode="RGBA")

    if t < 6.2:
        render_scene_1_hook(canvas, t)
    elif t < 13.2:
        render_scene_2_live_builder(canvas, t)
    elif t < 20.2:
        render_scene_3_templates_carousel(canvas, t)
    elif t < 26.5:
        render_scene_4_direct_edit(canvas, t)
    elif t < 33.5:
        render_scene_5_signature_and_invoice(canvas, t)
    elif t < 39.8:
        render_scene_6_exports(canvas, t)
    elif t < 46.2:
        render_scene_7_pricing_and_momo(canvas, t)
    else:
        render_scene_8_finale_cta(canvas, t)

    # Smooth scene transition flash at boundaries
    boundaries = [2.1, 6.2, 13.2, 20.2, 26.5, 33.5, 39.8, 46.2]
    for bt in boundaries:
        dist = abs(t - bt)
        if dist < 0.18:
            fl = int(95 * (1.0 - dist / 0.18))
            overlay = Image.new("RGBA", (W, H), (56, 189, 248, fl))
            canvas.alpha_composite(overlay)

    # Bottom progress bar
    d = ImageDraw.Draw(canvas)
    pw = int(W * (t / DURATION))
    d.rectangle((0, H - 10, W, H), fill=(15, 23, 42, 200))
    d.rectangle((0, H - 10, pw, H), fill=(52, 211, 153, 255))

    return np.array(canvas.convert("RGB"), dtype=np.uint8)


def main():
    t0 = time.time()
    wav_path = "/tmp/dd_inspect/devis_designer_audio.wav"
    print("Generating 124 BPM SaaS soundtrack & UI foley SFX...", flush=True)
    build_soundtrack_wav(wav_path)

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ff, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-maxrate", "3500k", "-bufsize", "7000k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        OUT_MP4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, bufsize=W * H * 3 * 2)

    for f_idx in range(TOTAL_FRAMES):
        rgb = render_frame(f_idx)
        proc.stdin.write(rgb.tobytes())
        if (f_idx + 1) % 300 == 0 or f_idx + 1 == TOTAL_FRAMES:
            print(f"  Rendered {f_idx + 1}/{TOTAL_FRAMES} frames ({time.time() - t0:.1f}s)", flush=True)

    proc.stdin.close()
    proc.wait()
    mb = os.path.getsize(OUT_MP4) / (1024 * 1024)
    print(f"Done! {OUT_MP4} ({DURATION:.1f}s, {mb:.2f} MB) in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
