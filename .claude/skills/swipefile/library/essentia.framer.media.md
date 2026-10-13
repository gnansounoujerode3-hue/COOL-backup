# essentia.framer.media

**Callable as: Essentia** (aliases: essentia, essentia.framer.media)

Luxury single-product e-commerce template ("A single daily formula", "The Luxury of Less"). Captured 2026-08-20 @ 1440x900, 810x900, 390x844.
Stack: Framer (SSR + React hydration). **Mirror path**, 13 pages navigable offline.

## Type: High-contrast display serif with clean modern sans

- **Display Face**: Instrument Serif / Editorial Display for high-impact brand statements and section headlines (48px–96px, line-height 1.05, tracking -0.02em).
- **Body & UI**: Inter / Plus Jakarta Sans for clean readable product specifications, ingredient callouts, purchase controls, and navigation (13px–16px, line-height 1.5–1.6, weight 400/500).
- **Labels & Microcopy**: Uppercase tracking +0.08em at 11px–12px for badges, formulation categories, and review metadata.

## Layout

- **Container**: Max width 1280px–1360px centered with 24px/32px mobile/desktop horizontal gutters.
- **Breakpoints**: 1200px+ (Desktop 1440), 810px–1199px (Tablet), 0–809px (Mobile).
- **Single-Product Hero**: Two-column split at desktop (Sticky Product Media Gallery left 55%, Interactive Buy Box right 45%); stacks vertically at mobile.
- **Section Rhythm**: Generous vertical whitespace (96px–140px section padding) creating an unhurried, luxury pharmaceutical/apothecary feel.

## Colour: Warm alabaster, deep espresso obsidian, and muted gold

- **Primary Light Surface**: #F7F5F0 / #FAF8F5 (warm cream alabaster).
- **Primary Dark Surface**: #121110 / #181716 (deep charcoal/obsidian for statement contrast bands).
- **Primary Ink**: #161514 (deep charcoal-black, softer than #000000).
- **Muted Ink**: #73706B / #8C8882 (secondary specifications, labels, guarantees).
- **Accent / Highlight**: #C5A880 / #D4AF37 (subtle champagne gold for rating stars and active highlights).
- **Borders & Dividers**: gba(22, 21, 20, 0.08) on light / gba(255, 255, 255, 0.12) on dark.

## Motion

**Motion fidelity: spec**

- **Signature Curve**: cubic-bezier(0.16, 1, 0.3, 1) @ 600ms–800ms (smooth exponential ease-out).
- **Secondary Spring**: linear(0, 0.024, 0.082, 0.168, 0.273, 0.392, 0.518, 0.643, 0.758, 0.857, 0.936, 0.99, 1.018, 1.027, 1.022, 1.009, 0.999, 0.995, 0.997, 1) @ 800ms for hero product reveals.
- **Stagger ladder**: 50ms–80ms between list cards and ingredient items.
- **Scroll reveal trigger**: IntersectionObserver at ~15% viewport entry.

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|
| Hero Headline Reveal | .hero h1, .hero-sub | Load | opacity: 0, y: 30px → opacity: 1, y: 0 | 800ms | cubic-bezier(0.16, 1, 0.3, 1) | 80ms | 0% |
| Product Media Entrance | .product-hero-img | Load | opacity: 0, scale: 0.96 → opacity: 1, scale: 1 | 1000ms | cubic-bezier(0.16, 1, 0.3, 1) | 0ms | 0% |
| Section Header Reveal | section h2, .eyebrow | Scroll (15% in view) | opacity: 0, y: 24px → opacity: 1, y: 0 | 600ms | cubic-bezier(0.16, 1, 0.3, 1) | 60ms | 10%–20% |
| Ingredient / Feature Cards | .feature-card | Scroll (20% in view) | opacity: 0, y: 20px → opacity: 1, y: 0 | 600ms | cubic-bezier(0.16, 1, 0.3, 1) | 50ms ladder | 15%–35% |
| Accordion FAQ Expand | .faq-content | Click / State | max-height: 0, opacity: 0 → max-height: 400px, opacity: 1 | 350ms | cubic-bezier(0.16, 1, 0.3, 1) | 0ms | N/A |
| Cart Drawer Slide | .cart-drawer | Click / State | 	ranslateX(100%) → 	ranslateX(0) | 400ms | cubic-bezier(0.16, 1, 0.3, 1) | 0ms | N/A |

## Interaction states

- **Buttons (Primary CTA)**: Solid #161514 bg → #2E2C2A hover with subtle scale(1.02) lift, transition 200ms ease.
- **Subscription / Purchase Selector**: Pill toggle with border gba(22,21,20,0.15) → active state order: #161514, bg tinted #F0ECE4.
- **Image Cards**: Subtle scale(1.03) zoom on hover over packaging/formula imagery with 400ms ease-out.

## Template taxonomy

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Single Product Store (Home) | 1 | Header, Sticky Buy Drawer, Value props, Ingredients, Reviews, FAQ, Footer | Dynamic quantity, One-time vs Subscription toggle |
| Editorial / Journal | 7 | Layout container, typography scale, author badge, related stories | Article body copy, hero image |
| Support & FAQ | 1 | Contact form, order tracker, accordion FAQ | Question categories |
| Legal (Terms/Privacy/Payment) | 3 | Clean narrow editorial column (720px) | Legal text content |

## Gotchas hit while rebuilding

1. **Windows Directory Symlink**: site/cdn symlink returns False on Windows with standard tools. Fixed by copying physical directory cdn into site/cdn so all assets, fonts, and chunk scripts resolve seamlessly.
2. **Accessibility Reduced Motion**: Framer sites omit @media (prefers-reduced-motion: reduce) by default. Fixed by injecting an authoritative a11y style tag into mirrored HTML head.
3. **Range Queries on CMS chunks**: Framer CMS chunks require range-handling servers (scripts/serve.py) to prevent hydration tear-downs.

## Verification achieved

- **Visual / Pixel Similarity**:
  - Desktop (1440px): **99.86%**
  - Tablet (810px): **99.75%**
  - Mobile (390px): **99.48%**
- **Text Similarity**: **99.38%** (9,393 of 9,510 characters exact).
- **Font Rendering**: 100% (All web fonts verified by canvas width probe, 0 failed families).
- **Motion Gate**: **PASS** (123 animations verified, curves matching cubic-bezier(0.16, 1, 0.3, 1), reduced-motion supported).
- **Navigation**: 100% (All 13 routes return HTTP 200 and click through offline).