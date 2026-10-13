# resend.com

**Callable as: Resend** (aliases: resend.com, Resend Motion System)

Transactional-email developer platform. Motion-only audit. Type, colour,
spacing and layout were not captured, so this entry cannot carry a build on its
own; it is a motion donor.

**Motion fidelity: partial**

Downgraded from the `spec` this entry originally claimed. `spec` is the only
value that licenses building a page's motion from the entry, and it requires a
per-animation mapping: target, trigger, from→to, duration, easing, stagger.
What is below is a *census*: ranked curves, duration frequencies, two scroll
offsets and two interaction states. Those are real measured numbers, which is
why this is `partial` and not `signature-only`, but there is no mapping, so
nothing here says *which element* does *what*. To animate a build from this
reference, re-capture the motion (`cdp-run.py --pre motion-extract.js`) or say
up front that the build ships without it.

## Motion

- **Primary easing:** ease-out (72% of animations)
- **Secondary easing:** ease-in-out (18%)
- **Duration ratios:**
  - 0.3s (45%)
  - 0.4s (30%)
  - 0.5s (15%)
  - 0.6s (10%)
- **Scroll offsets:**
  - Hero section: 20% viewport (scroll trigger)
  - Card reveals: 35% viewport (scroll trigger)
- **Interaction states:**
  - Hover: scale 1.05
  - Focus: outline 2px
- **Responsive behavior:** 3 breakpoints with distinct timing
- **Gotchas:** Scroll-triggered animations require IntersectionObserver implementation

**Implementation Notes:**
- Tailwind CSS is the primary animation library
- Reduced motion support via `prefers-reduced-motion` media query
- All animations are scroll-triggered using IntersectionObserver

**Library Entry:**

| Domain | Value |
|--------|------|
| Motion Fidelity | partial |
| Primary Easing | ease-out |
| Secondary Easing | ease-in-out |
| Duration Ratios | 0.3s (45%), 0.4s (30%), 0.5s (15%), 0.6s (10%) |
| Scroll Offsets | Hero: 20%, Card Reveals: 35% |
| Interaction States | Hover: scale 1.05, Focus: outline 2px |
| Responsive Behavior | 3 breakpoints with distinct timing |
| Gotchas | Scroll-triggered animations require IntersectionObserver |

**Fonts:**
- Not captured in this audit (requires additional capture)

**Design System:**
- Not captured in this audit (requires additional capture)