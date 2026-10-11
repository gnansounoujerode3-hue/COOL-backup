#!/usr/bin/env python3
"""High-precision 2D/3D motion graphics engine inspired by REFERENCE 6.mp4."""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from plan import (
    W, H, BG_DARK, BLUE_ELECTRIC, BLUE_GLOW, BLUE_ICE,
    RED_CRIMSON, RED_GLOW, WHITE, DIM_WORD,
)

FONT_DIR = "/home/user/.cache/fonts/node_modules/@expo-google-fonts"
FONT_PATHS = {
    "m600": f"{FONT_DIR}/montserrat/600SemiBold/Montserrat_600SemiBold.ttf",
    "m700": f"{FONT_DIR}/montserrat/700Bold/Montserrat_700Bold.ttf",
    "m800": f"{FONT_DIR}/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf",
    "m900": f"{FONT_DIR}/montserrat/900Black/Montserrat_900Black.ttf",
    "script": f"{FONT_DIR}/mr-dafoe/400Regular/MrDafoe_400Regular.ttf",
    "i400": f"{FONT_DIR}/inter/400Regular/Inter_400Regular.ttf",
    "i500": f"{FONT_DIR}/inter/500Medium/Inter_500Medium.ttf",
    "i600": f"{FONT_DIR}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "i700": f"{FONT_DIR}/inter/700Bold/Inter_700Bold.ttf",
}

_font_cache = {}
_asset_cache = {}


def get_font(key, size):
    k = (key, int(size))
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONT_PATHS[key], int(size))
    return _font_cache[k]


def ease_out_cubic(x):
    x = max(0.0, min(1.0, x))
    return 1.0 - (1.0 - x) ** 3


def ease_out_back(x, s=1.70158):
    x = max(0.0, min(1.0, x))
    x -= 1.0
    return x * x * ((s + 1.0) * x + s) + 1.0


def ease_in_out_cubic(x):
    x = max(0.0, min(1.0, x))
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# ---------------------------------------------------------------------------
# 1. STUDIO ELECTRIC-BLUE AMBIENT OVERLAY & CHEST SCRIM (FOR LIVE FOOTAGE)
# ---------------------------------------------------------------------------
def get_studio_scrim():
    """Creates the REFERENCE 6 dark-blue studio atmosphere + chest vignette below chin (y > 900).
    Keeps the speaker's face (y = 250..880) bright, clear, and unobstructed!
    """
    if "studio_scrim" in _asset_cache:
        return _asset_cache["studio_scrim"]

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # Top-right & top-left electric cobalt studio rim glow (avoids center face area)
    d_tr = np.sqrt(((xx - W * 0.88) / 440.0) ** 2 + ((yy - H * 0.18) / 480.0) ** 2)
    glow_tr = np.clip(1.0 - d_tr, 0.0, 1.0) ** 2.2

    d_tl = np.sqrt(((xx - W * 0.10) / 400.0) ** 2 + ((yy - H * 0.22) / 460.0) ** 2)
    glow_tl = np.clip(1.0 - d_tl, 0.0, 1.0) ** 2.4

    # Chest-to-bottom dark midnight scrim starting smoothly BELOW the chin (y > 880)
    chest_ramp = np.clip((yy - 840.0) / 340.0, 0.0, 1.0)
    chest_smooth = chest_ramp * chest_ramp * (3.0 - 2.0 * chest_ramp)
    bottom_deep = np.clip((yy - 1150.0) / 650.0, 0.0, 1.0) ** 1.2

    # Protect the face region (cx=540, cy=560, rx=310, ry=340) so skin stays bright and crisp
    face_dist = ((xx - 540.0) / 320.0) ** 2 + ((yy - 540.0) / 350.0) ** 2
    face_keep_clear = np.clip((face_dist - 0.55) / 0.65, 0.0, 1.0)

    dark_alpha = (0.76 * chest_smooth + 0.16 * bottom_deep + 0.22 * (glow_tr + glow_tl)) * face_keep_clear
    dark_alpha = np.clip(dark_alpha, 0.0, 0.88)

    blue_glow_chest = np.exp(-((xx - 540.0) / 460.0) ** 2 - ((yy - 1180.0) / 320.0) ** 2)
    blue_mix = np.clip(0.45 * glow_tr + 0.32 * glow_tl + 0.22 * blue_glow_chest, 0.0, 1.0)

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(3 + 26 * blue_mix, 0, 255).astype(np.uint8)
    rgba[..., 1] = np.clip(7 + 62 * blue_mix, 0, 255).astype(np.uint8)
    rgba[..., 2] = np.clip(22 + 198 * blue_mix, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(dark_alpha * 255, 0, 255).astype(np.uint8)

    im = Image.fromarray(rgba, "RGBA")
    _asset_cache["studio_scrim"] = im
    return im


# ---------------------------------------------------------------------------
# 2. TEXT HELPERS: GLOWING SCRIPT, PARTIAL INNER BLUE GLOW SANS, STACKED LOCKUPS
# ---------------------------------------------------------------------------
def render_text_layer(text, font_key, size, color=WHITE, glow_color=None, glow_radius=18, shadow=True):
    """Renders a crisp RGBA text sprite (cached) with optional neon glow and drop shadow."""
    cache_key = ("txt", text, font_key, int(size), color, glow_color, glow_radius, shadow)
    if cache_key in _asset_cache:
        return _asset_cache[cache_key]

    f = get_font(font_key, size)
    dummy = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bbox = dummy.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = max(48, glow_radius * 3 + 20)

    w_im, h_im = tw + 2 * pad, th + 2 * pad
    ox, oy = pad - bbox[0], pad - bbox[1]

    out = Image.new("RGBA", (w_im, h_im), (0, 0, 0, 0))

    if shadow:
        sh = Image.new("RGBA", (w_im, h_im), (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh)
        d_sh.text((ox, oy + 8), text, font=f, fill=(2, 4, 14, 220))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        out = Image.alpha_composite(out, sh)

    if glow_color is not None:
        gl = Image.new("RGBA", (w_im, h_im), (0, 0, 0, 0))
        d_gl = ImageDraw.Draw(gl)
        d_gl.text((ox, oy), text, font=f, fill=glow_color + (225,))
        gl1 = gl.filter(ImageFilter.GaussianBlur(glow_radius))
        gl2 = gl.filter(ImageFilter.GaussianBlur(max(4, glow_radius // 3)))
        out = Image.alpha_composite(out, gl1)
        out = Image.alpha_composite(out, gl2)

    fg = Image.new("RGBA", (w_im, h_im), (0, 0, 0, 0))
    d_fg = ImageDraw.Draw(fg)
    d_fg.text((ox, oy), text, font=f, fill=color + (255,))
    out = Image.alpha_composite(out, fg)

    info = {"img": out, "tw": tw, "th": th, "pad": pad}
    _asset_cache[cache_key] = info
    return info


def render_partial_blue_word(text, font_key, size, glow_frac=0.42):
    """Renders white extra-bold word with REFERENCE 6's inner electric-blue gradient tint on left/right letters."""
    cache_key = ("pblue", text, font_key, int(size), round(glow_frac, 2))
    if cache_key in _asset_cache:
        return _asset_cache[cache_key]

    f = get_font(font_key, size)
    dummy = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bbox = dummy.textbbox((0, 0), text, font=f)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    pad = 44
    w_im, h_im = tw + 2 * pad, th + 2 * pad
    ox, oy = pad - bbox[0], pad - bbox[1]

    out = Image.new("RGBA", (w_im, h_im), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w_im, h_im), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((ox, oy + 8), text, font=f, fill=(2, 5, 18, 220))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(10)))

    mask_im = Image.new("L", (w_im, h_im), 0)
    ImageDraw.Draw(mask_im).text((ox, oy), text, font=f, fill=255)
    mask_np = np.asarray(mask_im, dtype=np.float32) / 255.0

    xx = np.arange(w_im, dtype=np.float32)[None, :]
    rel_x = (xx - pad) / float(tw)
    if glow_frac >= 0:
        t_curve = np.clip((rel_x - glow_frac) / 0.28, 0.0, 1.0)
    else:
        t_curve = np.clip((abs(glow_frac) - rel_x) / 0.28, 0.0, 1.0)

    rgb = np.zeros((h_im, w_im, 4), dtype=np.uint8)
    c_blue = np.array([68, 128, 255], dtype=np.float32)
    c_white = np.array([255, 255, 255], dtype=np.float32)
    for k in range(3):
        rgb[..., k] = (c_blue[k] * (1.0 - t_curve) + c_white[k] * t_curve).astype(np.uint8)
    rgb[..., 3] = (mask_np * 255).astype(np.uint8)

    word_im = Image.fromarray(rgb, "RGBA")
    out = Image.alpha_composite(out, word_im)
    info = {"img": out, "tw": tw, "th": th, "pad": pad}
    _asset_cache[cache_key] = info
    return info


def paste_sprite(canvas, info, cx, cy, align="center", alpha=1.0, scale=1.0, wipe_x=1.0, dy=0):
    """Pastes a rendered text sprite onto RGBA canvas with animation parameters."""
    if alpha <= 0.01 or wipe_x <= 0.01:
        return
    im = info["img"]
    tw, th, pad = info["tw"], info["th"], info["pad"]

    if wipe_x < 0.999:
        crop_w = int(pad + tw * ease_out_cubic(wipe_x) + pad * 0.4)
        crop_w = max(1, min(im.width, crop_w))
        im_cropped = Image.new("RGBA", im.size, (0, 0, 0, 0))
        part = im.crop((0, 0, crop_w, im.height))
        im_cropped.paste(part, (0, 0))
        im = im_cropped

    if abs(scale - 1.0) > 0.005:
        nw = max(1, int(im.width * scale))
        nh = max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.BICUBIC)
        pad_s = pad * scale
        tw_s = tw * scale
        th_s = th * scale
    else:
        pad_s, tw_s, th_s = pad, tw, th

    if alpha < 0.999:
        im = im.copy()
        a_ch = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a_ch)

    if align == "center":
        x = int(round(cx - tw_s / 2 - pad_s))
    elif align == "left":
        x = int(round(cx - pad_s))
    elif align == "right":
        x = int(round(cx - tw_s - pad_s))
    else:
        x = int(round(cx - tw_s / 2 - pad_s))

    y = int(round(cy - th_s / 2 - pad_s + dy))
    canvas.alpha_composite(im, (x, y))


# ---------------------------------------------------------------------------
# 3. 3D GLASSMORPHIC SQUIRCLE BADGE + COUNTER PILL + POLYGON SHATTER MESH
# ---------------------------------------------------------------------------
def build_squircle_base():
    """Builds the 3D dark matte squircle badge with glowing blue inner orb (like REFERENCE 6 t=0.75s)."""
    if "squircle_base" in _asset_cache:
        return _asset_cache["squircle_base"]

    S = 260
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    cx, cy = S / 2.0, S / 2.0

    hw, hh, rad = 104.0, 104.0, 54.0
    qx = np.maximum(np.abs(xx - cx) - (hw - rad), 0.0)
    qy = np.maximum(np.abs(yy - cy) - (hh - rad), 0.0)
    dist_sq = np.sqrt(qx * qx + qy * qy) - rad
    alpha_sq = np.clip(1.0 - dist_sq / 1.5, 0.0, 1.0)

    nx = (xx - cx) / hw
    ny = (yy - cy) / hh
    bevel = np.clip(1.0 - np.abs(dist_sq + 4.0) / 4.5, 0.0, 1.0)
    rim_light = bevel * np.clip(-0.6 * nx - 0.7 * ny + 0.5, 0.0, 1.0)
    surf_grad = np.clip(0.5 - 0.35 * ny - 0.2 * nx, 0.0, 1.0)

    r_ch = 18 + 22 * surf_grad + 75 * rim_light
    g_ch = 20 + 25 * surf_grad + 85 * rim_light
    b_ch = 28 + 35 * surf_grad + 120 * rim_light

    orb_r = 68.0
    dx_o = xx - cx
    dy_o = yy - (cy + 2.0)
    d_orb = np.sqrt((dx_o / 1.06) ** 2 + (dy_o / 0.96) ** 2)

    tail_d = np.sqrt(((xx - (cx - 46.0)) / 24.0) ** 2 + ((yy - (cy + 46.0)) / 18.0) ** 2)
    in_orb = np.clip(1.0 - (np.minimum(d_orb / orb_r, tail_d) - 1.0) * 35.0, 0.0, 1.0)

    lz_x = (dx_o / orb_r) + 0.28
    lz_y = (dy_o / orb_r) + 0.34
    spec = np.exp(-(lz_x * lz_x + lz_y * lz_y) * 2.4)
    edge_dark = np.clip(d_orb / orb_r, 0.0, 1.0) ** 1.8

    orb_R = 16 + 72 * spec - 10 * edge_dark
    orb_G = 52 + 115 * spec - 28 * edge_dark
    orb_B = 245 + 10 * spec - 65 * edge_dark

    r_ch = r_ch * (1.0 - in_orb) + orb_R * in_orb
    g_ch = g_ch * (1.0 - in_orb) + orb_G * in_orb
    b_ch = b_ch * (1.0 - in_orb) + orb_B * in_orb

    rgba = np.zeros((S, S, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(r_ch, 0, 255).astype(np.uint8)
    rgba[..., 1] = np.clip(g_ch, 0, 255).astype(np.uint8)
    rgba[..., 2] = np.clip(b_ch, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha_sq * 255, 0, 255).astype(np.uint8)

    im = Image.fromarray(rgba, "RGBA")
    _asset_cache["squircle_base"] = im
    return im


def render_squircle_with_pill(pill_text="99+"):
    """Returns RGBA image of the 3D squircle badge + white top-right notification pill."""
    key = ("sq_pill", pill_text)
    if key in _asset_cache:
        return _asset_cache[key]

    base = build_squircle_base().copy()
    S = base.width

    pad = 36
    out = Image.new("RGBA", (S + 2 * pad, S + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        (pad + 26, pad + 36, pad + S - 26, pad + S - 16),
        radius=54, fill=(0, 3, 15, 200)
    )
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(18)))
    out.alpha_composite(base, (pad, pad))

    d = ImageDraw.Draw(out)
    bx, by = pad + S - 52, pad + 48
    rx, ry = 31, 25
    d.rounded_rectangle((bx - rx, by - ry, bx + rx, by + ry), radius=25, fill=(255, 255, 255, 255))
    f_pill = get_font("m800", 22)
    d.text((bx, by), pill_text, font=f_pill, fill=(12, 16, 28, 255), anchor="mm")

    _asset_cache[key] = out
    return out


def build_shatter_shards():
    """Pre-computes 64 Voronoi polygon shards of the 3D squircle badge for the shatter explosion."""
    if "shatter_shards" in _asset_cache:
        return _asset_cache["shatter_shards"]

    sq = render_squircle_with_pill("99+").crop((36, 36, 36 + 260, 36 + 260))
    S = 260
    sq_np = np.asarray(sq)

    rng = np.random.default_rng(42)
    pts = []
    for r_ring, n_pts in [(16, 7), (42, 14), (72, 20), (100, 23)]:
        for k in range(n_pts):
            ang = 2 * math.pi * k / n_pts + rng.uniform(-0.16, 0.16)
            rr = r_ring + rng.uniform(-7, 7)
            pts.append((S / 2 + rr * math.cos(ang), S / 2 + rr * math.sin(ang)))
    pts = np.array(pts, dtype=np.float32)

    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dists = (xx[..., None] - pts[:, 0]) ** 2 + (yy[..., None] - pts[:, 1]) ** 2
    labels = np.argmin(dists, axis=-1)

    sorted_d = np.sort(dists, axis=-1)
    crack = (np.sqrt(sorted_d[..., 1]) - np.sqrt(sorted_d[..., 0])) > 1.2

    shards = []
    for idx in range(len(pts)):
        mask = (labels == idx) & crack & (sq_np[..., 3] > 20)
        if not np.any(mask):
            continue
        ys, xs = np.where(mask)
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1

        patch = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
        sub_mask = mask[y0:y1, x0:x1]
        patch[sub_mask] = sq_np[y0:y1, x0:x1][sub_mask]

        # 3D facet shading per shard
        is_blue = patch[sub_mask, 2].mean() > 110
        if is_blue and rng.random() < 0.42:
            patch[sub_mask, 0] = np.clip(patch[sub_mask, 0] * 0.65 + 30, 0, 255)
            patch[sub_mask, 1] = np.clip(patch[sub_mask, 1] * 0.78 + 60, 0, 255)
            patch[sub_mask, 2] = 255

        cx_s, cy_s = float(pts[idx, 0] - S / 2), float(pts[idx, 1] - S / 2)
        dist_center = max(8.0, math.hypot(cx_s, cy_s))
        nx, ny = cx_s / dist_center, cy_s / dist_center

        shards.append({
            "img": Image.fromarray(patch, "RGBA"),
            "ox": x0 - S / 2,
            "oy": y0 - S / 2,
            "nx": nx,
            "ny": ny,
            "dist": dist_center,
            "vx": nx * rng.uniform(220, 520) + rng.uniform(-80, 80),
            "vy": ny * rng.uniform(110, 280) - rng.uniform(60, 190),
            "rot_speed": rng.uniform(-420, 420),
            "gravity": rng.uniform(1050, 1650),
        })

    _asset_cache["shatter_shards"] = shards
    return shards


def draw_squircle_or_shatter(canvas, cx, cy, t, mode="intact", pill_text="99+", t_shatter=21.74):
    """Draws either the floating 3D squircle badge or its 3D Voronoi shatter animation."""
    if mode == "intact":
        im = render_squircle_with_pill(pill_text)
        bob_y = int(round(6.0 * math.sin(t * 4.2)))
        canvas.alpha_composite(im, (int(cx - im.width // 2), int(cy - im.height // 2 + bob_y)))
        return

    dt = t - t_shatter
    if dt < 0:
        im = render_squircle_with_pill(pill_text)
        canvas.alpha_composite(im, (int(cx - im.width // 2), int(cy - im.height // 2)))
        return
    if dt > 1.50:
        return

    shards = build_shatter_shards()
    for sh in shards:
        if dt < 0.20:
            p = ease_out_cubic(dt / 0.20)
            dx = sh["nx"] * (22.0 + 0.36 * sh["dist"]) * p
            dy = sh["ny"] * (22.0 + 0.36 * sh["dist"]) * p
            ang = sh["rot_speed"] * 0.07 * p
            alpha = 1.0
        else:
            t_fall = dt - 0.20
            dx0 = sh["nx"] * (22.0 + 0.36 * sh["dist"])
            dy0 = sh["ny"] * (22.0 + 0.36 * sh["dist"])
            dx = dx0 + sh["vx"] * t_fall
            dy = dy0 + sh["vy"] * t_fall + 0.5 * sh["gravity"] * (t_fall ** 2)
            ang = sh["rot_speed"] * (0.07 + t_fall)
            alpha = max(0.0, min(1.0, (1.46 - dt) / 0.38))

        if alpha <= 0.02:
            continue
        im_s = sh["img"].rotate(ang, resample=Image.BICUBIC, expand=True)
        if alpha < 0.99:
            im_s = im_s.copy()
            im_s.putalpha(im_s.getchannel("A").point(lambda v: int(v * alpha)))

        px = int(round(cx + sh["ox"] + dx))
        py = int(round(cy + sh["oy"] + dy))
        if -120 < px < W + 120 and -120 < py < H + 120:
            canvas.alpha_composite(im_s, (px, py))


# ---------------------------------------------------------------------------
# 4. CUTAWAY #1 (12.10 - 16.45s): DARK TABLET + UI NOTIFICATION CARD PUSH-IN
# ---------------------------------------------------------------------------
def build_ui_card_plate(time_label):
    """Builds the high-res 1600x2400 dark tablet + notification card (like REFERENCE 6 t=4.25-7.50s)."""
    key = ("ui_plate", time_label)
    if key in _asset_cache:
        return _asset_cache[key]

    CW, CH = 1600, 2400
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)

    d_top = np.sqrt(((xx - CW * 0.52) / 680.0) ** 2 + ((yy - 180.0) / 420.0) ** 2)
    top_glow = np.clip(1.0 - d_top, 0.0, 1.0) ** 2.2

    rgb = np.zeros((CH, CW, 3), dtype=np.uint8)
    rgb[..., 0] = np.clip(4 + 14 * top_glow, 0, 255).astype(np.uint8)
    rgb[..., 1] = np.clip(6 + 32 * top_glow, 0, 255).astype(np.uint8)
    rgb[..., 2] = np.clip(14 + 98 * top_glow, 0, 255).astype(np.uint8)

    for gx in range(0, CW, 80):
        rgb[:560, gx:gx+1, :] = np.clip(rgb[:560, gx:gx+1, :] + 7, 0, 255)
    for gy in range(0, 560, 80):
        rgb[gy:gy+1, :, :] = np.clip(rgb[gy:gy+1, :, :] + 7, 0, 255)

    plate = Image.fromarray(rgb, "RGB").convert("RGBA")
    d = ImageDraw.Draw(plate)

    # Tablet screen bezel starting at y=520 (exact match to REFERENCE 6 t=5.25s & t=7.00s)
    d.line((0, 520, CW, 520), fill=(42, 48, 68, 255), width=3)
    d.rectangle((0, 523, CW, CH), fill=(7, 9, 15, 255))

    # Webcam lens dot centered at (CW*0.50, 575)
    cam_x, cam_y = int(CW * 0.50), 575
    d.ellipse((cam_x - 16, cam_y - 16, cam_x + 16, cam_y + 16), fill=(34, 42, 60, 255))
    d.ellipse((cam_x - 7, cam_y - 7, cam_x + 7, cam_y + 7), fill=(85, 115, 165, 255))

    # Notification Card: width=960 (cx0=320, cx1=1280) so at 1.0x zoom (1080px crop) there is 60px margin on each side!
    cx0, cy0 = 320, 745
    cx1, cy1 = 1280, 925
    card_ov = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    dc = ImageDraw.Draw(card_ov)
    dc.rounded_rectangle((cx0, cy0, cx1, cy1), radius=28, fill=(46, 49, 58, 240), outline=(80, 86, 102, 185), width=2)

    # Avatar circle on left
    av_x, av_y, av_r = cx0 + 70, (cy0 + cy1) // 2, 46
    dc.ellipse((av_x - av_r, av_y - av_r, av_x + av_r, av_y + av_r), fill=(230, 234, 242, 255))
    dc.ellipse((av_x - 15, av_y - 23, av_x + 15, av_y + 7), fill=(155, 162, 176, 255))
    dc.pieslice((av_x - 32, av_y + 9, av_x + 32, av_y + 58), 180, 360, fill=(155, 162, 176, 255))

    # Header: "AJ (Mentor) • 1m / Day 1"
    tx = cx0 + 140
    f_name = get_font("i700", 25)
    f_time = get_font("i500", 22)
    f_body = get_font("i400", 22)
    dc.text((tx, cy0 + 34), "AJ (Mentor)", font=f_name, fill=(255, 255, 255, 255))
    name_w = dc.textlength("AJ (Mentor)", font=f_name)
    dc.text((tx + name_w + 12, cy0 + 37), f"• {time_label}", font=f_time, fill=(175, 182, 198, 255))

    # Body text (2 lines)
    dc.text((tx, cy0 + 76), "Through all the ups and downs — always here", font=f_body, fill=(235, 238, 245, 255))
    dc.text((tx, cy0 + 108), "whenever you need real advice.", font=f_body, fill=(235, 238, 245, 255))

    # Right Pill Button ("Real Advice" in glowing electric blue, matching "Waiting for Reply")
    px0, py0 = cx1 - 245, (cy0 + cy1) // 2 - 31
    px1, py1 = cx1 - 28, (cy0 + cy1) // 2 + 31
    p_glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ImageDraw.Draw(p_glow).rounded_rectangle((px0 - 6, py0 - 6, px1 + 6, py1 + 6), radius=34, fill=(58, 102, 255, 145))
    card_ov = Image.alpha_composite(card_ov, p_glow.filter(ImageFilter.GaussianBlur(14)))
    dc = ImageDraw.Draw(card_ov)
    dc.rounded_rectangle((px0, py0, px1, py1), radius=31, fill=(76, 116, 255, 255), outline=(135, 168, 255, 220), width=2)
    f_btn = get_font("i600", 22)
    dc.text(((px0 + px1) // 2, (py0 + py1) // 2), "Real Advice", font=f_btn, fill=(255, 255, 255, 255), anchor="mm")

    plate = Image.alpha_composite(plate, card_ov)
    _asset_cache[key] = plate
    return plate


def render_cutaway_ui_card(t, t0=12.10, t1=16.45):
    """Renders Cutaway #1 at timestamp t with initial wide hold then smooth camera push-in."""
    p = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    if p < 0.25:
        t_lbl = "1m"
    elif p < 0.50:
        t_lbl = "6m"
    elif p < 0.75:
        t_lbl = "3y"
    else:
        t_lbl = "Day 1"

    plate = build_ui_card_plate(t_lbl)
    CW, CH = plate.size

    # Hold wide for first 0.9s so entire card + 'Real Advice' pill is 100% framed (like t=5.25s in REFERENCE 6),
    # then smoothly push in onto left half of card (like t=7.00s in REFERENCE 6)
    p_move = max(0.0, min(1.0, (t - (t0 + 0.85)) / (t1 - t0 - 0.85)))
    pz = ease_in_out_cubic(p_move)
    zoom = 1.00 + 0.64 * pz
    crop_w = W / zoom
    crop_h = H / zoom

    cx = 800.0 - 185.0 * pz
    cy = 910.0 - 65.0 * pz

    x0 = max(0.0, min(CW - crop_w, cx - crop_w / 2.0))
    y0 = max(0.0, min(CH - crop_h, cy - crop_h / 2.0))

    cropped = plate.crop((int(round(x0)), int(round(y0)), int(round(x0 + crop_w)), int(round(y0 + crop_h))))
    return cropped.resize((W, H), Image.BICUBIC)


# ---------------------------------------------------------------------------
# 5. CUTAWAY #2 (25.15 - 30.05s): CENTRAL ORB + RIPPLES + DASHED ORBIT + 3 NODES
# ---------------------------------------------------------------------------
def get_3d_blue_sphere(radius, style="central"):
    """Generates a 3D shaded royal/electric blue circle orb like REFERENCE 6 t=11.50s-16.50s."""
    key = ("sphere3d", int(radius), style)
    if key in _asset_cache:
        return _asset_cache[key]

    D = int(radius * 2 + 16)
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    cx = cy = D / 2.0
    dx, dy = (xx - cx) / radius, (yy - cy) / radius
    r = np.sqrt(dx * dx + dy * dy)
    alpha = np.clip((1.0 - r) * radius * 0.75, 0.0, 1.0)

    if style == "central":
        light = np.clip(0.56 - 0.48 * dx - 0.52 * dy, 0.0, 1.0) ** 1.25
        rim = np.clip(1.0 - np.abs(r - 0.96) * 18.0, 0.0, 1.0) * np.clip(-0.5 * dx - 0.5 * dy + 0.4, 0.0, 1.0)
        R = 6 + 38 * light + 55 * rim
        G = 18 + 86 * light + 90 * rim
        B = 72 + 178 * light + 60 * rim
    elif style == "ring":
        # 3D shaded concentric ripple ring (brighter top-left, deep blue bottom-right like REFERENCE 6 t=11.50s)
        light = np.clip(0.52 - 0.38 * dx - 0.42 * dy, 0.0, 1.0)
        R = 4 + 22 * light
        G = 14 + 48 * light
        B = 78 + 145 * light
    else:
        light = np.clip(0.62 - 0.50 * dx - 0.50 * dy, 0.0, 1.0) ** 1.15
        R = 18 + 78 * light
        G = 46 + 115 * light
        B = 140 + 115 * light

    rgba = np.zeros((D, D, 4), dtype=np.uint8)
    rgba[..., 0] = np.clip(R, 0, 255).astype(np.uint8)
    rgba[..., 1] = np.clip(G, 0, 255).astype(np.uint8)
    rgba[..., 2] = np.clip(B, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)

    im = Image.fromarray(rgba, "RGBA")
    _asset_cache[key] = im
    return im


def draw_fg_center_logo(canvas, cx, cy, scale=1.0):
    """Draws the crisp white stylized Felix Gray eyeglasses + 'FG' mark inside the central orb."""
    S = int(220 * scale)
    if S < 16:
        return
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    lw = max(3, int(9 * scale))
    d.rounded_rectangle((int(S * 0.14), int(S * 0.24), int(S * 0.45), int(S * 0.50)), radius=int(12 * scale), outline=(255, 255, 255, 255), width=lw)
    d.rounded_rectangle((int(S * 0.55), int(S * 0.24), int(S * 0.86), int(S * 0.50)), radius=int(12 * scale), outline=(255, 255, 255, 255), width=lw)
    d.arc((int(S * 0.42), int(S * 0.28), int(S * 0.58), int(S * 0.44)), 190, 350, fill=(255, 255, 255, 255), width=lw)
    d.line((int(S * 0.08), int(S * 0.30), int(S * 0.15), int(S * 0.30)), fill=(255, 255, 255, 255), width=lw)
    d.line((int(S * 0.85), int(S * 0.30), int(S * 0.92), int(S * 0.30)), fill=(255, 255, 255, 255), width=lw)

    f_fg = get_font("m900", max(12, int(52 * scale)))
    d.text((S // 2, int(S * 0.72)), "FG", font=f_fg, fill=(235, 242, 255, 255), anchor="mm")

    canvas.alpha_composite(im, (int(cx - S // 2), int(cy - S // 2)))


def draw_node_icon(canvas, cx, cy, kind, scale=1.0):
    """Draws the white icon inside each of the 3 orbital nodes (book/reading, badge/planning, laptop)."""
    S = int(96 * scale)
    if S < 12:
        return
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (255, 255, 255, 255)
    blue_in = (42, 85, 210, 255)
    lw = max(2, int(4 * scale))

    if kind == "reading":
        d.rounded_rectangle((int(S * 0.18), int(S * 0.24), int(S * 0.82), int(S * 0.74)), radius=int(12 * scale), fill=c)
        d.line((S // 2, int(S * 0.28), S // 2, int(S * 0.70)), fill=blue_in, width=lw)
        for ry in (0.38, 0.50, 0.62):
            d.line((int(S * 0.26), int(S * ry), int(S * 0.44), int(S * ry)), fill=blue_in, width=lw)
            d.line((int(S * 0.56), int(S * ry), int(S * 0.74), int(S * ry)), fill=blue_in, width=lw)
    elif kind == "planning":
        r_out = S * 0.28
        pts = []
        for k in range(16):
            ang = 2 * math.pi * k / 16
            rr = r_out if k % 2 == 0 else r_out * 0.84
            pts.append((S / 2 + rr * math.cos(ang), S * 0.44 + rr * math.sin(ang)))
        d.polygon(pts, fill=c)
        d.polygon([(S * 0.36, S * 0.66), (S * 0.46, S * 0.66), (S * 0.42, S * 0.84), (S * 0.32, S * 0.78)], fill=c)
        d.polygon([(S * 0.54, S * 0.66), (S * 0.64, S * 0.66), (S * 0.68, S * 0.78), (S * 0.58, S * 0.84)], fill=c)
        d.ellipse((S * 0.34, S * 0.28, S * 0.66, S * 0.60), outline=blue_in, width=lw)
        d.line([(S * 0.41, S * 0.44), (S * 0.48, S * 0.51), (S * 0.60, S * 0.37)], fill=blue_in, width=lw)
    elif kind == "laptop":
        d.rounded_rectangle((int(S * 0.22), int(S * 0.26), int(S * 0.78), int(S * 0.64)), radius=int(6 * scale), fill=c)
        d.rounded_rectangle((int(S * 0.28), int(S * 0.32), int(S * 0.72), int(S * 0.58)), radius=int(3 * scale), fill=blue_in)
        d.polygon([(int(S * 0.14), int(S * 0.68)), (int(S * 0.86), int(S * 0.68)), (int(S * 0.80), int(S * 0.76)), (int(S * 0.20), int(S * 0.76))], fill=c)

    canvas.alpha_composite(im, (int(cx - S // 2), int(cy - S // 2)))


def render_cutaway_orbital(t, t0=25.15, t1=30.05):
    """Renders Cutaway #2 (Central FG Orb + Concentric Ripples + Dashed Orbit + 3 Pop-In Feature Nodes)."""
    if "orbital_bg" not in _asset_cache:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d_c = np.sqrt(((xx - W * 0.5) / 520.0) ** 2 + ((yy - H * 0.48) / 560.0) ** 2)
        glow = np.clip(1.0 - d_c, 0.0, 1.0) ** 2.0
        rgb = np.zeros((H, W, 3), dtype=np.uint8)
        rgb[..., 0] = np.clip(2 + 12 * glow, 0, 255).astype(np.uint8)
        rgb[..., 1] = np.clip(5 + 28 * glow, 0, 255).astype(np.uint8)
        rgb[..., 2] = np.clip(16 + 115 * glow, 0, 255).astype(np.uint8)
        _asset_cache["orbital_bg"] = Image.fromarray(rgb, "RGB").convert("RGBA")

    canvas = _asset_cache["orbital_bg"].copy()
    cx, cy = W // 2, int(H * 0.48)

    t_orbit_start = 26.85

    if t < t_orbit_start:
        orb_scale = ease_out_back(min(1.0, (t - t0) / 0.48), 1.35)
        pulse = 1.0 + 0.035 * math.sin((t - t0) * 6.5)

        # 3 large concentric 3D-shaded blue discs (matching REFERENCE 6 t=11.50s)
        for r_base, a_max, delay in [(520, 0.52, 0.20), (385, 0.68, 0.11), (268, 0.82, 0.03)]:
            rp = ease_out_cubic(max(0.0, min(1.0, (t - t0 - delay) / 0.52)))
            fade_end = max(0.0, min(1.0, (t_orbit_start - t) / 0.26))
            rr = int(r_base * rp * pulse)
            al = a_max * rp * fade_end
            if rr > 20 and al > 0.02:
                disc = get_3d_blue_sphere(rr, "ring").copy()
                disc.putalpha(disc.getchannel("A").point(lambda v: int(v * al)))
                canvas.alpha_composite(disc, (cx - disc.width // 2, cy - disc.height // 2))

        r_orb = int(172 * max(0.08, orb_scale))
        sph = get_3d_blue_sphere(r_orb, "central")
        canvas.alpha_composite(sph, (cx - sph.width // 2, cy - sph.height // 2))
        draw_fg_center_logo(canvas, cx, cy, scale=max(0.08, orb_scale * 1.05))
    else:
        p_orb = min(1.0, (t - t_orbit_start) / 0.40)
        r_orbit = 316
        d = ImageDraw.Draw(canvas)

        n_dashes = 58
        max_dash = int(n_dashes * ease_out_cubic(p_orb))
        rot_offset = (t - t_orbit_start) * 4.5
        bbox_orb = (cx - r_orbit, cy - r_orbit, cx + r_orbit, cy + r_orbit)
        for k in range(max_dash):
            a0 = k * (360.0 / n_dashes) - 90.0 + rot_offset * 0.4
            a1 = a0 + (360.0 / n_dashes) * 0.52
            d.arc(bbox_orb, a0, a1, fill=(215, 228, 255, 215), width=3)

        r_orb = 148
        sph = get_3d_blue_sphere(r_orb, "central")
        canvas.alpha_composite(sph, (cx - sph.width // 2, cy - sph.height // 2))
        draw_fg_center_logo(canvas, cx, cy, scale=148.0 / 162.0)

        nodes = [
            (27.08, -86.0, "reading", "READING"),
            (28.22, 32.0, "planning", "PLANNING"),
            (29.18, 148.0, "laptop", "LAPTOP"),
        ]
        for t_node, base_deg, kind, label in nodes:
            if t < t_node:
                continue
            pn = min(1.0, (t - t_node) / 0.34)
            sc = ease_out_back(pn, 1.8)
            deg = base_deg + (t - t_node) * 3.2
            rad = math.radians(deg)
            nx = int(round(cx + r_orbit * math.cos(rad)))
            ny = int(round(cy + r_orbit * math.sin(rad)))

            r_n = max(8, int(76 * sc))
            node_sph = get_3d_blue_sphere(r_n, "node")
            canvas.alpha_composite(node_sph, (nx - node_sph.width // 2, ny - node_sph.height // 2))
            draw_node_icon(canvas, nx, ny, kind, scale=sc)

            lbl_sp = render_text_layer(label, "m800", 24, (210, 225, 255))
            ly_off = -112 if base_deg < 0 else 112
            paste_sprite(canvas, lbl_sp, nx, ny + ly_off, "center", alpha=min(1.0, pn * 1.4), scale=sc)

    return canvas


# ---------------------------------------------------------------------------
# 6. CUTAWAY #3 (42.25 - 46.63s): GIANT FAINT '?' + WORD-BY-WORD REVEAL
# ---------------------------------------------------------------------------
def get_question_bg():
    """Builds the deep navy background with the giant translucent 3D '?' watermark (like REFERENCE 6 t=23.25s)."""
    if "question_bg" in _asset_cache:
        return _asset_cache["question_bg"]

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d_c = np.sqrt(((xx - W * 0.5) / 520.0) ** 2 + ((yy - H * 0.5) / 620.0) ** 2)
    glow = np.clip(1.0 - d_c, 0.0, 1.0) ** 1.8

    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    rgb[..., 0] = np.clip(2 + 10 * glow, 0, 255).astype(np.uint8)
    rgb[..., 1] = np.clip(5 + 22 * glow, 0, 255).astype(np.uint8)
    rgb[..., 2] = np.clip(15 + 88 * glow, 0, 255).astype(np.uint8)
    bg = Image.fromarray(rgb, "RGB").convert("RGBA")

    q_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dq = ImageDraw.Draw(q_layer)
    f_q = get_font("m800", 980)
    dq.text((W // 2, H // 2 - 20), "?", font=f_q, fill=(18, 44, 130, 95), anchor="mm")
    q_layer = q_layer.filter(ImageFilter.GaussianBlur(2))
    bg = Image.alpha_composite(bg, q_layer)

    _asset_cache["question_bg"] = bg
    return bg


def render_cutaway_question(t):
    """Renders Cutaway #3 with word-by-word illumination from dim blue-gray to bright white."""
    canvas = get_question_bg().copy()
    d = ImageDraw.Draw(canvas)
    f_w = get_font("m800", 50)

    lines = [
        [("Looking", 42.60), ("for", 42.82), ("something", 43.00), ("small", 43.24)],
        [("to", 43.80), ("show", 44.10), ("your", 44.26), ("appreciation", 44.40)],
        [("for", 44.82), ("someone", 45.20), ("who", 45.44), ("impacted", 45.68), ("your", 46.00), ("life?", 46.26)],
    ]

    space_w = d.textlength(" ", font=f_w)
    y_start = H // 2 - 74

    for li, line in enumerate(lines):
        widths = [d.textlength(w_txt, font=f_w) for w_txt, _ in line]
        total_w = sum(widths) + space_w * (len(line) - 1)
        x = (W - total_w) / 2.0
        y = y_start + li * 74

        for (w_txt, t_on), ww in zip(line, widths):
            p = max(0.0, min(1.0, (t - t_on) / 0.18))
            col = tuple(int(DIM_WORD[k] + (WHITE[k] - DIM_WORD[k]) * p) for k in range(3)) + (255,)
            if p > 0.05:
                d.text((x, y + 4), w_txt, font=f_w, fill=(2, 5, 18, int(170 * p)))
            d.text((x, y), w_txt, font=f_w, fill=col)
            x += ww + space_w

    return canvas


# ---------------------------------------------------------------------------
# 7. CHEST-LEVEL KINETIC TYPOGRAPHY ORCHESTRATOR (BEATS ON LIVE FOOTAGE)
# ---------------------------------------------------------------------------
def draw_chest_graphics(canvas, t):
    """Draws the studio scrim + chest-level kinetic typography & 3D squircle badge on live footage.
    Vertical anchor sits cleanly on the speaker's chest (y = 1040..1510), keeping the face 100% clear!
    """
    canvas.alpha_composite(get_studio_scrim())

    # ---- BEAT 1A (0.00 - 2.82s): "I'm doing teacher / appreciation / different" + 3D squircle badge ----
    if 0.00 <= t < 2.82:
        fade_out = min(1.0, (2.82 - t) / 0.18)
        x_left = 155
        if t >= 0.00:
            p = ease_out_cubic(min(1.0, t / 0.22))
            s1 = render_text_layer("I'm doing teacher", "m700", 50, WHITE)
            paste_sprite(canvas, s1, x_left, 1035, "left", alpha=p * fade_out, dy=int(18 * (1 - p)))
        if t >= 0.65:
            p = ease_out_back(min(1.0, (t - 0.65) / 0.26), 1.4)
            s2 = render_text_layer("appreciation", "m800", 104, WHITE)
            paste_sprite(canvas, s2, x_left, 1122, "left", alpha=min(1.0, (t - 0.65) / 0.15) * fade_out, scale=0.88 + 0.12 * p)
        if t >= 1.45:
            pw = min(1.0, (t - 1.45) / 0.42)
            s3 = render_text_layer("different", "script", 138, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=20)
            paste_sprite(canvas, s3, x_left + 45, 1225, "left", alpha=fade_out, wipe_x=pw)

        pill = "1+" if t < 0.70 else ("10+" if t < 1.50 else "25+")
        draw_squircle_or_shatter(canvas, W // 2, 1495, t, mode="intact", pill_text=pill)

    # ---- BEAT 1B (2.82 - 4.92s): "show love to / my mentor / AJ" + 3D squircle badge (99+) ----
    elif 2.82 <= t < 4.92:
        fade_out = min(1.0, (4.92 - t) / 0.18)
        x_left = 175
        if t >= 2.85:
            p = ease_out_cubic(min(1.0, (t - 2.85) / 0.24))
            s1 = render_text_layer("show love to", "m700", 50, WHITE)
            paste_sprite(canvas, s1, x_left, 1035, "left", alpha=p * fade_out, dy=int(18 * (1 - p)))
        if t >= 3.68:
            p = ease_out_back(min(1.0, (t - 3.68) / 0.26), 1.4)
            s2 = render_text_layer("my mentor", "m800", 112, WHITE)
            paste_sprite(canvas, s2, x_left, 1125, "left", alpha=min(1.0, (t - 3.68) / 0.15) * fade_out, scale=0.88 + 0.12 * p)
        if t >= 4.30:
            pw = min(1.0, (t - 4.30) / 0.35)
            s3 = render_text_layer("AJ", "script", 146, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=22)
            paste_sprite(canvas, s3, x_left + 160, 1235, "left", alpha=fade_out, wipe_x=pw)

        pill = "50+" if t < 3.90 else "99+"
        draw_squircle_or_shatter(canvas, W // 2, 1495, t, mode="intact", pill_text=pill)

    # ---- BEAT 2A (4.92 - 6.80s): Word-by-word centered chest beats ("He's been / one of those / people / truly shaped") ----
    elif 4.92 <= t < 6.80:
        beats = [
            (4.92, 5.46, "He's been", False),
            (5.46, 5.96, "one of those", False),
            (5.96, 6.38, "people", False),
            (6.38, 6.80, "truly shaped", True),
        ]
        for b0, b1, txt, is_blue in beats:
            if b0 <= t < b1:
                p = ease_out_back(min(1.0, (t - b0) / 0.18), 1.4)
                sp = render_partial_blue_word(txt, "m800", 90, 0.45) if is_blue else render_text_layer(txt, "m800", 90, WHITE)
                paste_sprite(canvas, sp, W // 2, 1185, "center", alpha=1.0, scale=0.90 + 0.10 * p)

    # ---- BEAT 2B (6.80 - 9.05s): Stacked 3-line Pyramid ("how I think / how I move / how I approach") ----
    elif 6.80 <= t < 9.05:
        fade_out = min(1.0, (9.05 - t) / 0.16)
        if t >= 6.80:
            p = ease_out_cubic(min(1.0, (t - 6.80) / 0.22))
            s1 = render_text_layer("how I think", "m700", 60, WHITE)
            paste_sprite(canvas, s1, W // 2, 1085, "center", alpha=p * fade_out, dy=int(16 * (1 - p)))
        if t >= 7.72:
            p = ease_out_cubic(min(1.0, (t - 7.72) / 0.22))
            s2 = render_text_layer("how I move", "m800", 82, WHITE)
            paste_sprite(canvas, s2, W // 2, 1180, "center", alpha=p * fade_out, dy=int(16 * (1 - p)))
        if t >= 8.58:
            p = ease_out_back(min(1.0, (t - 8.58) / 0.24), 1.4)
            s3 = render_partial_blue_word("how I approach", "m900", 92, -0.58)
            paste_sprite(canvas, s3, W // 2, 1290, "center", alpha=fade_out, scale=0.90 + 0.10 * p)

    # ---- BEAT 2C (9.05 - 10.75s): "how I approach / everything / that I'm building" (like 'it is / everything' t=20.75s) ----
    elif 9.05 <= t < 10.75:
        fade_out = min(1.0, (10.75 - t) / 0.18)
        x_left = 155
        s1 = render_text_layer("how I approach", "m700", 54, WHITE)
        paste_sprite(canvas, s1, x_left, 1085, "left", alpha=fade_out)
        if t >= 9.32:
            pw = min(1.0, (t - 9.32) / 0.42)
            s2 = render_text_layer("everything", "script", 148, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=22)
            paste_sprite(canvas, s2, x_left + 10, 1190, "left", alpha=fade_out, wipe_x=pw)
        if t >= 9.96:
            p3 = ease_out_cubic(min(1.0, (t - 9.96) / 0.22))
            s3 = render_text_layer("that I'm building", "m700", 44, (195, 215, 255))
            paste_sprite(canvas, s3, W // 2, 1320, "center", alpha=p3 * fade_out, dy=int(14 * (1 - p3)))

    # ---- BEAT 3A (10.75 - 12.10s): "Through a lot of my / ups & / downs" (red script accent) ----
    elif 10.75 <= t < 12.10:
        fade_out = min(1.0, (12.10 - t) / 0.15)
        x_left = 195
        p1 = ease_out_cubic(min(1.0, (t - 10.75) / 0.20))
        s1 = render_text_layer("Through a lot of my", "m700", 46, WHITE)
        paste_sprite(canvas, s1, x_left, 1060, "left", alpha=p1 * fade_out)
        if t >= 11.24:
            p2 = ease_out_back(min(1.0, (t - 11.24) / 0.22), 1.4)
            s2 = render_text_layer("ups &", "m800", 112, WHITE)
            paste_sprite(canvas, s2, x_left, 1150, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)
        if t >= 11.52:
            pw = min(1.0, (t - 11.52) / 0.34)
            s3 = render_text_layer("downs", "script", 138, RED_CRIMSON, glow_color=RED_GLOW, glow_radius=20)
            paste_sprite(canvas, s3, x_left + 90, 1250, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 3B (16.45 - 19.15s): "wanted to get him something / truly / purposeful" ----
    elif 16.45 <= t < 19.15:
        fade_out = min(1.0, (19.15 - t) / 0.18)
        x_left = 165
        p1 = ease_out_cubic(min(1.0, (t - 16.45) / 0.25))
        s1 = render_text_layer("wanted to get him something", "m700", 44, WHITE)
        paste_sprite(canvas, s1, x_left, 1060, "left", alpha=p1 * fade_out, dy=int(16 * (1 - p1)))
        if t >= 17.70:
            p2 = ease_out_back(min(1.0, (t - 17.70) / 0.24), 1.4)
            s2 = render_text_layer("truly", "m800", 118, WHITE)
            paste_sprite(canvas, s2, x_left, 1152, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)
        if t >= 18.22:
            pw = min(1.0, (t - 18.22) / 0.45)
            s3 = render_text_layer("purposeful", "script", 136, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=22)
            paste_sprite(canvas, s3, x_left + 40, 1258, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 4A (19.15 - 23.15s): Negative Red-Script Lockup ("not / random") + 3D SQUIRCLE SHATTER ----
    elif 19.15 <= t < 23.15:
        if t < 21.74:
            x_left = 160
            p1 = ease_out_cubic(min(1.0, (t - 19.15) / 0.25))
            s1 = render_text_layer("When getting him a gift", "m700", 46, WHITE)
            paste_sprite(canvas, s1, x_left, 1025, "left", alpha=p1)
            if t >= 20.75:
                p2 = ease_out_back(min(1.0, (t - 20.75) / 0.24), 1.4)
                s2 = render_text_layer("not", "m800", 122, WHITE)
                paste_sprite(canvas, s2, x_left, 1115, "left", alpha=1.0, scale=0.88 + 0.12 * p2)
            if t >= 21.38:
                pw = min(1.0, (t - 21.38) / 0.32)
                s3 = render_text_layer("random", "script", 138, RED_CRIMSON, glow_color=RED_GLOW, glow_radius=20)
                paste_sprite(canvas, s3, x_left + 20, 1215, "left", alpha=1.0, wipe_x=pw)

            draw_squircle_or_shatter(canvas, W // 2, 1495, t, mode="intact", pill_text="99+")
        else:
            # 21.74 - 23.15s: Squircle shatters into 3D blue/dark shards + centered word beats (like t=2.75-3.50s in REFERENCE 6)
            word_txt = "anything" if t < 21.90 else ("random" if t < 22.45 else "I wanted")
            is_b = (word_txt == "random")
            sp = render_partial_blue_word(word_txt, "m800", 98, 0.45) if is_b else render_text_layer(word_txt, "m800", 98, WHITE)
            paste_sprite(canvas, sp, W // 2, 1145, "center", alpha=min(1.0, (23.15 - t) / 0.18))
            draw_squircle_or_shatter(canvas, W // 2, 1480, t, mode="shatter", t_shatter=21.74)

    # ---- BEAT 4B (23.15 - 25.15s): "made sense for his / everyday / life" ----
    elif 23.15 <= t < 25.15:
        fade_out = min(1.0, (25.15 - t) / 0.16)
        x_left = 165
        p1 = ease_out_cubic(min(1.0, (t - 23.15) / 0.22))
        s1 = render_text_layer("made sense for his", "m700", 50, WHITE)
        paste_sprite(canvas, s1, x_left, 1060, "left", alpha=p1 * fade_out)
        if t >= 24.22:
            p2 = ease_out_back(min(1.0, (t - 24.22) / 0.24), 1.4)
            s2 = render_partial_blue_word("everyday", "m800", 106, 0.42)
            paste_sprite(canvas, s2, x_left, 1150, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)
        if t >= 24.58:
            pw = min(1.0, (t - 24.58) / 0.34)
            s3 = render_text_layer("life", "script", 142, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=22)
            paste_sprite(canvas, s3, x_left + 140, 1255, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 5B (30.05 - 32.03s): "something like this / just felt / right" ----
    elif 30.05 <= t < 32.03:
        fade_out = min(1.0, (32.03 - t) / 0.16)
        x_left = 165
        p1 = ease_out_cubic(min(1.0, (t - 30.05) / 0.22))
        s1 = render_text_layer("something like this", "m700", 48, WHITE)
        paste_sprite(canvas, s1, x_left, 1060, "left", alpha=p1 * fade_out)
        if t >= 30.95:
            p2 = ease_out_back(min(1.0, (t - 30.95) / 0.24), 1.4)
            s2 = render_text_layer("just felt", "m800", 108, WHITE)
            paste_sprite(canvas, s2, x_left, 1150, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)
        if t >= 31.42:
            pw = min(1.0, (t - 31.42) / 0.35)
            s3 = render_text_layer("right", "script", 142, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=22)
            paste_sprite(canvas, s3, x_left + 120, 1255, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 6A (32.03 - 33.25s): Stacked 3-Line Pyramid ("And the / best / part") ----
    elif 32.03 <= t < 33.25:
        fade_out = min(1.0, (33.25 - t) / 0.14)
        s1 = render_text_layer("And the", "m700", 52, WHITE)
        paste_sprite(canvas, s1, W // 2, 1095, "center", alpha=fade_out)
        if t >= 32.25:
            s2 = render_text_layer("best", "m800", 78, WHITE)
            paste_sprite(canvas, s2, W // 2, 1175, "center", alpha=fade_out)
        if t >= 32.42:
            p3 = ease_out_back(min(1.0, (t - 32.42) / 0.20), 1.4)
            s3 = render_text_layer("part", "m900", 108, WHITE)
            paste_sprite(canvas, s3, W // 2, 1270, "center", alpha=fade_out, scale=0.88 + 0.12 * p3)

    # ---- BEAT 6B (33.25 - 35.15s): "they have / clear lenses / everyday use" ----
    elif 33.25 <= t < 35.15:
        fade_out = min(1.0, (35.15 - t) / 0.16)
        x_left = 155
        s1 = render_text_layer("they have", "m700", 48, WHITE)
        paste_sprite(canvas, s1, x_left, 1060, "left", alpha=fade_out)
        if t >= 33.30:
            p2 = ease_out_back(min(1.0, (t - 33.30) / 0.24), 1.4)
            s2 = render_partial_blue_word("clear lenses", "m800", 102, 0.42)
            paste_sprite(canvas, s2, x_left, 1147, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)
        if t >= 34.10:
            pw = min(1.0, (t - 34.10) / 0.42)
            s3 = render_text_layer("everyday use", "script", 128, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=20)
            paste_sprite(canvas, s3, x_left + 30, 1250, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 6C (35.15 - 37.79s): "blue light / filtering / on screens a lot" ----
    elif 35.15 <= t < 37.79:
        fade_out = min(1.0, (37.79 - t) / 0.16)
        x_left = 155
        s1 = render_text_layer("and blue light", "m700", 50, WHITE)
        paste_sprite(canvas, s1, x_left, 1060, "left", alpha=fade_out)
        if t >= 35.60:
            p2 = ease_out_back(min(1.0, (t - 35.60) / 0.24), 1.4)
            s2 = render_text_layer("filtering", "m800", 110, WHITE)
            paste_sprite(canvas, s2, x_left, 1150, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)
        if t >= 36.68:
            pw = min(1.0, (t - 36.68) / 0.45)
            s3 = render_text_layer("on screens a lot", "script", 122, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=20)
            paste_sprite(canvas, s3, x_left + 20, 1255, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 7A (37.79 - 40.15s): "It feels good / showing / appreciation" ----
    elif 37.79 <= t < 40.15:
        fade_out = min(1.0, (40.15 - t) / 0.16)
        if t < 38.95:
            p = ease_out_back(min(1.0, (t - 37.79) / 0.22), 1.4)
            sp = render_partial_blue_word("It feels good", "m800", 88, -0.45)
            paste_sprite(canvas, sp, W // 2, 1180, "center", alpha=1.0, scale=0.90 + 0.10 * p)
        else:
            x_left = 155
            s1 = render_text_layer("to show my", "m700", 50, WHITE)
            paste_sprite(canvas, s1, x_left, 1100, "left", alpha=fade_out)
            if t >= 39.38:
                p2 = ease_out_back(min(1.0, (t - 39.38) / 0.24), 1.4)
                s2 = render_partial_blue_word("appreciation", "m800", 98, 0.45)
                paste_sprite(canvas, s2, x_left, 1190, "left", alpha=fade_out, scale=0.88 + 0.12 * p2)

    # ---- BEAT 7B (40.15 - 42.25s): "something he'll use / every day" (exact match to 'it is / everything' t=20.75s) ----
    elif 40.15 <= t < 42.25:
        fade_out = min(1.0, (42.25 - t) / 0.16)
        x_left = 165
        p1 = ease_out_cubic(min(1.0, (t - 40.15) / 0.24))
        s1 = render_text_layer("something he'll use", "m700", 52, WHITE)
        paste_sprite(canvas, s1, x_left, 1105, "left", alpha=p1 * fade_out)
        if t >= 41.35:
            pw = min(1.0, (t - 41.35) / 0.42)
            s2 = render_text_layer("every day", "script", 146, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=22)
            paste_sprite(canvas, s2, x_left + 15, 1210, "left", alpha=fade_out, wipe_x=pw)

    # ---- BEAT 9 (46.63 - 48.80s): FINAL 3-LINE CTA LOCKUP (exact match to 'Dm me / Rhythm / and I'll check your pipeline') ----
    elif t >= 46.63:
        pw1 = min(1.0, (t - 46.66) / 0.30)
        s1 = render_text_layer("Go to", "script", 96, WHITE, glow_color=BLUE_GLOW, glow_radius=12)
        paste_sprite(canvas, s1, W // 2, 1085, "center", alpha=1.0, wipe_x=pw1)

        if t >= 46.92:
            p2 = ease_out_back(min(1.0, (t - 46.92) / 0.26), 1.45)
            s2 = render_text_layer("‘FelixGray.com’", "m800", 98, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=24)
            paste_sprite(canvas, s2, W // 2, 1180, "center", alpha=1.0, scale=0.86 + 0.14 * p2)

        if t >= 47.82:
            d = ImageDraw.Draw(canvas)
            f_sub = get_font("m700", 44)
            w1 = "and "
            w2 = "shop now"
            tw1 = d.textlength(w1, font=f_sub)
            tw2 = d.textlength(w2, font=f_sub)
            x0 = (W - (tw1 + tw2)) / 2.0
            y0 = 1262
            d.text((x0, y0 + 4), w1, font=f_sub, fill=(2, 5, 18, 200))
            d.text((x0, y0), w1, font=f_sub, fill=(255, 255, 255, 255))
            if t >= 48.12:
                d.text((x0 + tw1, y0 + 4), w2, font=f_sub, fill=(2, 5, 18, 200))
                d.text((x0 + tw1, y0), w2, font=f_sub, fill=BLUE_ELECTRIC + (255,))
