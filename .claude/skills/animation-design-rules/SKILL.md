---
name: animation-design-rules
description: Master rulebook and executable Python/JS engine unifying Disney's 12 Principles of Animation (dylantarre/animation-principles, vibe-motion/disney-animation-rule-skill), Emil Kowalski / Jakub Krehel / Jhey Tompkins UI Animation Laws (emilkowalski/skills, kylezantos/design-motion-principles, vercel-labs/web-animation-design, mblode/ui-animation), LottieFiles Universal Motion Design Rules (LottieFiles/motion-design-skill), and Klik Animation & Camera Craft Bible (t3knobox/klik-anim-skill-creation).
---

# Animation Design Rules — Master Skill & Rulebook

This skill consolidates the **Animation Design Rules** installed in `.claude/skills/` (502 skills total) into a single actionable specification and executable Python engine (`.claude/skills/animation-design-rules/scripts/animation_rules_engine.py`).

---

## 1. The 10 Non-Negotiable Animation Design Laws (Hard Rules)

| # | Rule Name | Source Skill(s) | Exact Mathematical / Code Rule |
|---|---|---|---|
| **1** | **Never `scale(0)` on Entrance** | `emil-design-eng`, `animate`, `web-animation-design` | Always enter from `scale(0.95)` + `opacity: 0` (or `scale(0.92)` for hero cards). Objects in the real world never materialize from zero volume. |
| **2** | **Never Linear for Spatial Motion** | `lottiefiles-motion-design`, `web-motion-design`, `klik-anim` | `linear` is strictly reserved for constant loops (spinners, marquees, progress bars, timecode). All spatial motion must use directional cubic-bezier or physical springs. |
| **3** | **Directional Easing Hierarchy** | `animate`, `lottiefiles-motion-design`, `ui-animation` | **Entrances**: strong decelerate (`cubic-bezier(0.23, 1, 0.32, 1)` or `MD3 Emphasized (0.05, 0.7, 0.1, 1)`). **On-screen morph/move**: `cubic-bezier(0.77, 0, 0.175, 1)`. **Exits**: `20%` faster than entrance (`cubic-bezier(0.3, 0, 1, 1)`). |
| **4** | **Paired Elements Synchronization** | `web-animation-design`, `design-motion-principles` | Elements that move as a unit (card + backdrop, modal + overlay, badge + container) **must** share the exact same `duration` and `easing` curve. |
| **5** | **The 1/3 Distance & Concurrency Rule** | `lottiefiles-motion-design` | (a) No element travels `> 1/3` of the viewport without an intermediate keyframe or velocity-matched cut (`cut-the-curve`). (b) With `3+` elements, at most `1/3` are in peak rapid motion simultaneously. |
| **6** | **Always 3 Motion Layers** | `lottiefiles-motion-design`, `klik-anim`, `MOTION-DESIGN.md` | Every scene must layer: **(1) Primary Hero** (foreground card/subject), **(2) Secondary Follow-Through** (badges, shadows, data counters lagging by `50–90ms`), and **(3) Ambient Depth** (parallax grid/particles at `20–30%` counter-motion speed). |
| **7** | **Disney Follow-Through & Overlapping Action** | `follow-through-overlapping`, `disney-animation-rule-skill` | Child elements never land on the exact same frame as their parent container: shadow arrives `+50ms` after card; inner headline `+60ms`; subtitle/badge `+100ms`. |
| **8** | **Disney Anticipation & Squash/Stretch** | `anticipation-mastery`, `squash-stretch-mastery` | Before a high-energy launch or exit, apply a `60–90ms` (`2–3 frame`) anticipation dip (`-4px` or `scale=0.97`). Preserve volume during elastic deformation (`scale_x * scale_y == 1.0`, max `±6%` for UI cards). |
| **9** | **Arc Trajectory Over Straight Lines** | `arc-mastery`, `lottiefiles-motion-design` | Diagonal or multi-axis entrances add a natural parabolic/sinusoidal arc (`8–16px` perpendicular offset at `t=0.5`) rather than sterile linear interpolation. |
| **10** | **Timing Bands & Stagger Budget** | `universal-timing`, `animate`, `klik-anim` | Micro-interactions: `100–200ms`. Standard UI transitions: `180–300ms`. Choreographed cards/scenes: `400–700ms`. Multi-item stagger: `30–80ms` per item (total stagger cap `<= 500ms`, accelerating by `0.84^i`). |

---

## 2. Canonical Easing & Spring Lookup Table

```css
/* Emil Kowalski / Design Engineering Curves */
--ease-out-strong:     cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out-strong:  cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer-ios:     cubic-bezier(0.32, 0.72, 0, 1);

/* LottieFiles / Material Design 3 / Apple HIG Curves */
--md3-standard:        cubic-bezier(0.2, 0, 0, 1);
--md3-emphasized-dec:  cubic-bezier(0.05, 0.7, 0.1, 1);
--md3-emphasized-acc:  cubic-bezier(0.3, 0, 1, 1);
--apple-hig-default:   cubic-bezier(0.25, 0.1, 0.25, 1);
--disney-overshoot:    cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

---

## 3. Connected Skill Families in `.claude/skills/`

- **Disney's 12 Principles (145 skills)**: `disney-animation-rule-skill`, `squash-stretch-mastery`, `anticipation-mastery`, `staging-mastery`, `straight-ahead-pose-mastery`, `follow-through-overlapping`, `slow-in-out-mastery`, `arc-mastery`, `secondary-action-mastery`, `timing-principle-mastery`, `exaggeration-mastery`, `solid-drawing-mastery`, `appeal-mastery`, plus all 12 domain/persona/timing/emotion categories from `dylantarre/animation-principles`.
- **UI & Web Animation Rules (18 skills)**: `animate`, `emil-design-eng`, `design-motion-principles` (Emil Kowalski, Jakub Krehel, Jhey Tompkins), `web-animation-design`, `ui-animation`, `animation-performance`, `animation-vocabulary`, `find-animation-opportunities`, `improve-animations`, `review-animations`, `impeccable`, `detail-design`, `optimize-web-animations`.
- **Motion Director & Choreography Rules (15 skills)**: `lottiefiles-motion-design`, `motion-design`, `klik-anim`, `klik-cam`, `klik-remotion-method`, `cut-the-curve`, `seam-craft`, `embedded-captions`, `hyperframes-motion-director`, `hyperframes-motion-reel`, `remotion-motion-graphics`, `anything2explainer`.
- **GSAP & 3D WebGL Motion Systems (65+ skills)**: `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`, `gsap-performance`, `cinematic-gsap-lenis-motion-system`, `cinematic-scroll-storytelling`, `animation-systems`, `animation-on-scroll`, `staggered-word-reveal`, `scroll-scrubbed-visual-sequence`, `3d-cloth-material` .. `3d-wood-material`.

---

## 4. Executable Python Engine

Import `.claude/skills/animation-design-rules/scripts/animation_rules_engine.py` in any Python video compositor (`render_video.py`) to apply:
- `emil_ease_out(t)`, `emil_ease_in_out(t)`, `emil_drawer_ease(t)`, `md3_emphasized_decelerate(t)`, `disney_overshoot_ease(t)`
- `disney_squash_stretch(t, intensity=0.06)` → volume-preserving `(scale_x, scale_y)`
- `disney_anticipation_launch(t, dip_ratio=0.18, dip_amount=0.04)` → anticipation wind-up before launch
- `disney_arc_position(x0, y0, x1, y1, t, arc_Offset=14.0)` → curved trajectory `(x, y)`
- `disney_follow_through_layers(age, base_dur=0.42)` → synchronized `(card_p, shadow_p, title_p, badge_p)`
- `audit_animation_spec(spec)` → validates durations, easings, `scale >= 0.95`, and 1/3 rules.
