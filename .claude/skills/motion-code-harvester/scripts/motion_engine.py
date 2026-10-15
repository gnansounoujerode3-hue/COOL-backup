#!/usr/bin/env python3
"""
Motion Code Harvester — Production Animation Engine (`motion_engine.py`)
Translates GSAP (`cut-the-curve`, `seam-craft`), `embedded-captions` (`motion-vocabulary`),
and Emil Kowalski (`emil-design-eng` / `animations.dev`) animation code into
frame-accurate Python/PIL/NumPy video compositing primitives.
"""

import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# 1. Canonical GSAP & CSS Easing Curves
# ---------------------------------------------------------------------------
def power2_in(t: float) -> float:
    t = clamp(t)
    return t * t


def power2_out(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 2


def power3_in(t: float) -> float:
    t = clamp(t)
    return t ** 3


def power3_out(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def power4_in(t: float) -> float:
    t = clamp(t)
    return t ** 4


def power4_out(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 4


def expo_out(t: float) -> float:
    t = clamp(t)
    return 1.0 if t >= 1.0 else 1.0 - (2.0 ** (-10.0 * t))


def expo_in_out(t: float) -> float:
    """
    Matches `cubic-bezier(0.77, 0, 0.175, 1)` used in `swipe-reveal` (`motion-vocabulary.md`).
    """
    t = clamp(t)
    if t <= 0.0 or t >= 1.0:
        return t
    if t < 0.5:
        return 0.5 * (2.0 ** (20.0 * t - 10.0))
    return 1.0 - 0.5 * (2.0 ** (-20.0 * t + 10.0))


def cubic_bezier(x: float, x1: float = 0.2, y1: float = 0.8, x2: float = 0.2, y2: float = 1.0) -> float:
    x = clamp(x)
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
        u = clamp(u - bx / dbx)
    return 3.0 * ((1.0 - u) ** 2) * u * y1 + 3.0 * (1.0 - u) * (u ** 2) * y2 + (u ** 3)


# ---------------------------------------------------------------------------
# 2. The 3-Phase Nudge Curve (`cut-the-curve` §7: 10% / 65% / 25% distance
#    over 20% / 18% / 62% time -> power3.in -> linear burst -> power4.out)
# ---------------------------------------------------------------------------
def nudge_curve_3phase(t: float) -> float:
    """
    Slow-fast-slow group repositioning curve from `.claude/skills/cut-the-curve/SKILL.md` §7:
    - Phase 1 (0.00 -> 0.20 time): `power3.in` covers 10% of distance
    - Phase 2 (0.20 -> 0.38 time): `linear` burst covers 65% of distance (10% -> 75%)
    - Phase 3 (0.38 -> 1.00 time): `power4.out` decaying creep covers final 25% (75% -> 100%)
    """
    t = clamp(t)
    if t <= 0.20:
        return 0.10 * power3_in(t / 0.20)
    if t <= 0.38:
        return 0.10 + 0.65 * ((t - 0.20) / 0.18)
    return 0.75 + 0.25 * power4_out((t - 0.38) / 0.62)


# ---------------------------------------------------------------------------
# 3. Waterfall Entry (`cut-the-curve` §6: shrinking gap * 0.84^i + weight offset)
# ---------------------------------------------------------------------------
def waterfall_word_state(
    age: float,
    word_index: int = 0,
    weight: str = "normal",
    base_gap: float = 0.055,
    decay: float = 0.84,
):
    """
    Computes `(opacity, dy_px, scale)` for a word in a Waterfall Entry cascade:
    - Gaps shrink by `decay` (`0.84`) per word so the cascade accelerates.
    - Anchor/heavy words travel 72px over 0.22s (`expo_out`), normal words 46px over 0.16s,
      light words 32px over 0.13s.
    - Never starts from `scale(0)` (`emil-design-eng`: starts at `scale=0.95`).
    """
    start_t = 0.0
    gap = base_gap
    for _ in range(word_index):
        start_t += gap
        gap *= decay

    local_age = age - start_t
    if local_age < 0.0:
        return 0.0, 72.0, 0.95

    if weight == "anchor":
        dur, max_dy = 0.24, 72.0
    elif weight == "light":
        dur, max_dy = 0.13, 32.0
    else:
        dur, max_dy = 0.17, 46.0

    p = expo_out(local_age / dur)
    # Binary-fast ignition (`cut-the-curve` §6: opacity snaps 0->1 over first 2 frames)
    op = clamp(local_age / 0.065)
    dy = (1.0 - p) * max_dy
    sc = 0.95 + 0.05 * p
    return op, dy, sc


# ---------------------------------------------------------------------------
# 4. Swipe Clip-Path Reveal (`embedded-captions` §4: expo.inOut inset wipe)
# ---------------------------------------------------------------------------
def swipe_clip_reveal(layer: Image.Image, progress: float, direction: str = "left_to_right") -> Image.Image:
    """
    Applies `clip-path: inset(0 100% 0 0 -> 0 0 0 0)` with `expo_in_out` easing
    (`cubic-bezier(0.77, 0, 0.175, 1)`).
    """
    p = expo_in_out(progress)
    if p <= 0.001:
        return Image.new("RGBA", layer.size, (0, 0, 0, 0))
    if p >= 0.999:
        return layer

    w, h = layer.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    if direction == "left_to_right":
        x_end = int(round(w * p))
        d.rectangle([0, 0, x_end, h], fill=255)
    elif direction == "bottom_to_top":
        y_start = int(round(h * (1.0 - p)))
        d.rectangle([0, y_start, w, h], fill=255)
    else:
        y_end = int(round(h * p))
        d.rectangle([0, 0, w, y_end], fill=255)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(layer, (0, 0), mask)
    return out


# ---------------------------------------------------------------------------
# 5. Velocity-Matched Scene Seams (`cut-the-curve` §1, §2, §3, §5)
# ---------------------------------------------------------------------------
def _scale_and_blur(im: Image.Image, scale: float, blur_px: float, dx: int = 0, dy: int = 0) -> Image.Image:
    w, h = im.size
    out = Image.new("RGBA", (w, h), (10, 10, 12, 255))
    nw = max(16, int(round(w * scale)))
    nh = max(16, int(round(h * scale)))
    scaled = im.resize((nw, nh), Image.BILINEAR)

    if nw >= w and nh >= h:
        x0 = (nw - w) // 2 - dx
        y0 = (nh - h) // 2 - dy
        x0 = max(0, min(nw - w, x0))
        y0 = max(0, min(nh - h, y0))
        cropped = scaled.crop((x0, y0, x0 + w, y0 + h))
        out = cropped.convert("RGBA")
    else:
        px = (w - nw) // 2 + dx
        py = (h - nh) // 2 + dy
        out.paste(scaled, (px, py))

    if blur_px >= 0.8:
        out = out.filter(ImageFilter.GaussianBlur(radius=min(18.0, blur_px)))
    return out


def zoom_through_seam(img_old: Image.Image, img_new: Image.Image, progress: float, inverse: bool = False) -> Image.Image:
    """
    Implements `Zoom-Through` (forward push: 1.0 -> 1.22, cut at peak blur, 0.78 -> 1.0)
    and `Inverse Zoom-Through` (backward pull: 1.0 -> 0.82, cut at peak blur, 1.24 -> 1.0)
    from `.claude/skills/cut-the-curve/examples/gsap-implementation.md`.
    30% exit (`power3.in`) / 70% entry (`expo.out`), matching velocity and blur at the cut.
    """
    p = clamp(progress)
    cut_p = 0.30
    peak_blur = 14.0

    if p < cut_p:
        u = p / cut_p
        e = power3_in(u)
        sc = (1.0 - 0.18 * e) if inverse else (1.0 + 0.22 * e)
        bl = peak_blur * e
        return _scale_and_blur(img_old, sc, bl)
    else:
        u = (p - cut_p) / (1.0 - cut_p)
        e = expo_out(u)
        sc = (1.24 - 0.24 * e) if inverse else (0.78 + 0.22 * e)
        bl = peak_blur * (1.0 - e)
        return _scale_and_blur(img_new, sc, bl)


def cut_the_curve_seam(
    img_old: Image.Image,
    img_new: Image.Image,
    progress: float,
    direction: str = "left",
) -> Image.Image:
    """
    Implements `Cut the Curve` (`cut-the-curve` §3):
    Partial travel (~12% of frame = 130px horizontal / 220px vertical) with mirrored
    `power4.in` exit and `power4.out` entry so velocity matches at `p = 0.45`.
    """
    p = clamp(progress)
    w, h = img_old.size
    travel_x = int(round(w * 0.12))
    travel_y = int(round(h * 0.12))
    cut_p = 0.45

    if p < cut_p:
        u = p / cut_p
        e = power4_in(u)
        dx, dy = 0, 0
        if direction == "left":
            dx = -int(round(travel_x * e))
        elif direction == "right":
            dx = int(round(travel_x * e))
        elif direction == "up":
            dy = -int(round(travel_y * e))
        else:
            dy = int(round(travel_y * e))
        return _scale_and_blur(img_old, 1.04, 9.0 * e, dx=dx, dy=dy)
    else:
        u = (p - cut_p) / (1.0 - cut_p)
        e = power4_out(u)
        rem = 1.0 - e
        dx, dy = 0, 0
        if direction == "left":
            dx = int(round(travel_x * rem))
        elif direction == "right":
            dx = -int(round(travel_x * rem))
        elif direction == "up":
            dy = int(round(travel_y * rem))
        else:
            dy = -int(round(travel_y * rem))
        return _scale_and_blur(img_new, 1.04, 9.0 * rem, dx=dx, dy=dy)


def rack_focus_blur_cut(img_old: Image.Image, img_new: Image.Image, progress: float) -> Image.Image:
    """
    Implements `Rack-Focus Blur-Cut` (`cut-the-curve` §5):
    Optical DSLR focus-pull (`scale 1.0 -> 1.06 -> 1.0`, peak `13px` defocus blur at `p=0.45`,
    `power2.in` / `power2.out`).
    """
    p = clamp(progress)
    cut_p = 0.45
    if p < cut_p:
        e = power2_in(p / cut_p)
        return _scale_and_blur(img_old, 1.0 + 0.06 * e, 13.0 * e)
    else:
        e = power2_out((p - cut_p) / (1.0 - cut_p))
        rem = 1.0 - e
        return _scale_and_blur(img_new, 1.0 + 0.06 * rem, 13.0 * rem)
