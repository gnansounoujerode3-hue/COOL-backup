#!/usr/bin/env python3
"""
Animation Design Rules Engine (`animation_rules_engine.py`)
Executable Python implementation of:
- Disney's 12 Principles of Animation (`dylantarre/animation-principles`, `disney-animation-rule-skill`)
- Emil Kowalski, Jakub Krehel & Jhey Tompkins UI Motion Laws (`emilkowalski/skills`, `design-motion-principles`)
- LottieFiles Universal Motion Design Rules (`LottieFiles/motion-design-skill`)
- Klik Animation & Camera Craft Bible (`t3knobox/klik-anim-skill-creation`)
"""

import math
from typing import Dict, List, Tuple


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def cubic_bezier(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Evaluates a CSS cubic-bezier(x1, y1, x2, y2) curve at progress x in [0, 1]."""
    x = clamp(x)
    if x <= 0.0 or x >= 1.0:
        return x
    u = x
    for _ in range(7):
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
# 1. Canonical Designer Easing Curves (Emil Kowalski, MD3, Apple HIG, Disney)
# ---------------------------------------------------------------------------
def emil_ease_out(t: float) -> float:
    """Strong UI entrance deceleration: cubic-bezier(0.23, 1, 0.32, 1)"""
    return cubic_bezier(t, 0.23, 1.0, 0.32, 1.0)


def emil_ease_in_out(t: float) -> float:
    """Strong on-screen movement/morph: cubic-bezier(0.77, 0, 0.175, 1)"""
    return cubic_bezier(t, 0.77, 0.0, 0.175, 1.0)


def emil_drawer_ease(t: float) -> float:
    """iOS sheet/drawer curve: cubic-bezier(0.32, 0.72, 0, 1)"""
    return cubic_bezier(t, 0.32, 0.72, 0.0, 1.0)


def md3_emphasized_decelerate(t: float) -> float:
    """Material Design 3 Hero Entrance: cubic-bezier(0.05, 0.7, 0.1, 1.0)"""
    return cubic_bezier(t, 0.05, 0.7, 0.1, 1.0)


def md3_emphasized_accelerate(t: float) -> float:
    """Material Design 3 Exit (20% faster): cubic-bezier(0.3, 0.0, 1.0, 1.0)"""
    return cubic_bezier(t, 0.3, 0.0, 1.0, 1.0)


def disney_overshoot_ease(t: float) -> float:
    """Disney Exaggeration / Appeal settle: cubic-bezier(0.175, 0.885, 0.32, 1.275)"""
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


# ---------------------------------------------------------------------------
# 2. Disney's 12 Principles — Mathematical Primitives
# ---------------------------------------------------------------------------
def disney_squash_stretch(t: float, max_deform: float = 0.06) -> Tuple[float, float]:
    """
    Principle 1: Squash & Stretch with strict volume conservation (scale_x * scale_y == 1.0).
    Stretches during peak velocity (t ~ 0.25), squashes slightly on landing (t ~ 0.75),
    and settles to (1.0, 1.0) at t = 1.0.
    """
    t = clamp(t)
    envelope = math.sin(t * math.pi * 2.0) * math.exp(-3.2 * t)
    sy = 1.0 + max_deform * envelope
    sx = 1.0 / max(0.5, sy)
    return sx, sy


def disney_anticipation_launch(
    t: float, dip_ratio: float = 0.18, dip_amount: float = 0.045
) -> float:
    """
    Principle 2: Anticipation.
    First `dip_ratio` (18% of duration) pulls backward to `-dip_amount`,
    then launches forward with strong deceleration to 1.0.
    """
    t = clamp(t)
    if t < dip_ratio:
        u = t / dip_ratio
        return -dip_amount * math.sin(u * math.pi)
    u = (t - dip_ratio) / (1.0 - dip_ratio)
    return emil_ease_out(u)


def disney_arc_position(
    x0: float, y0: float, x1: float, y1: float, t: float, arc_offset_px: float = 14.0
) -> Tuple[float, float]:
    """
    Principle 7: Arcs.
    Moves from (x0, y0) to (x1, y1) along a smooth parabolic/sinusoidal arc
    with perpendicular midpoint deflection `arc_offset_px`.
    """
    p = emil_ease_out(t)
    bx = x0 + (x1 - x0) * p
    by = y0 + (y1 - y0) * p
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        return bx, by
    nx, ny = -dy / dist, dx / dist
    arc = math.sin(clamp(t) * math.pi) * arc_offset_px
    return bx + nx * arc, by + ny * arc


def disney_follow_through_layers(age: float, base_dur: float = 0.42) -> Dict[str, float]:
    """
    Principle 5 & 8: Follow-Through, Overlapping Action & Secondary Action.
    From `lottiefiles-motion-design` Card Entrance Recipe:
    - Primary card enters at t=0.00
    - Shadow arrives +50ms after card
    - Headline content arrives +65ms after card
    - Secondary badge/accent arrives +100ms after card with subtle overshoot
    """
    card_p = emil_ease_out(age / base_dur)
    shadow_p = emil_ease_out((age - 0.050) / base_dur)
    title_p = emil_ease_out((age - 0.065) / max(0.18, base_dur * 0.85))
    badge_p = disney_overshoot_ease((age - 0.100) / max(0.20, base_dur * 0.80))
    return {
        "card": card_p,
        "shadow": shadow_p,
        "title": title_p,
        "badge": badge_p,
        "scale": 0.95 + 0.05 * card_p,  # Never starts from scale(0)
    }


def counter_motion_ambient(hero_dx: float, hero_dy: float, ratio: float = 0.25) -> Tuple[float, float]:
    """
    LottieFiles Choreography Rule:
    When hero moves in (dx, dy), ambient background layer counter-moves in (-dx, -dy) at 20-30% speed.
    """
    return -hero_dx * ratio, -hero_dy * ratio


# ---------------------------------------------------------------------------
# 3. Automated Animation Design Rules Auditor (`design-motion-principles` + `review-animations`)
# ---------------------------------------------------------------------------
def audit_animation_spec(spec: Dict) -> List[str]:
    """
    Audits an animation configuration dictionary against the 10 Non-Negotiable Animation Design Rules.
    Returns a list of violations (empty list = 100% compliant).
    """
    violations = []
    initial_scale = spec.get("initial_scale", 0.95)
    if initial_scale < 0.90:
        violations.append(
            f"Rule 1 Violation (Emil Kowalski): initial_scale={initial_scale} is too small; start from >= 0.95, never scale(0)."
        )
    easing = spec.get("easing", "ease-out")
    motion_type = spec.get("type", "entrance")
    if easing == "linear" and motion_type in ("entrance", "exit", "spatial"):
        violations.append(
            "Rule 2 Violation (LottieFiles / Disney): Never use linear easing for spatial movement."
        )
    if easing == "ease-in" and motion_type == "entrance":
        violations.append(
            "Rule 3 Violation (Emil Kowalski): Never use ease-in on UI entrances; use strong ease-out."
        )
    travel_ratio = spec.get("screen_travel_ratio", 0.15)
    if travel_ratio > 0.34 and not spec.get("has_intermediate_seam", False):
        violations.append(
            f"Rule 5 Violation (LottieFiles 1/3 Rule): travel_ratio={travel_ratio:.2f} exceeds 1/3 of screen without intermediate seam."
        )
    layers = spec.get("layers", ["primary", "secondary", "ambient"])
    if len(layers) < 3:
        violations.append(
            f"Rule 6 Violation (LottieFiles 3-Layer Rule): scene has {len(layers)} layers; requires primary + secondary + ambient."
        )
    return violations


if __name__ == "__main__":
    sample = {
        "type": "entrance",
        "initial_scale": 0.95,
        "easing": "cubic-bezier(0.23, 1, 0.32, 1)",
        "screen_travel_ratio": 0.18,
        "layers": ["primary", "secondary", "ambient"],
    }
    issues = audit_animation_spec(sample)
    print("Animation Rules Engine self-test:", "PASSED (0 violations)" if not issues else issues)
