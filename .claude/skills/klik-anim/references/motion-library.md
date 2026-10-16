# The motion library — canonical springs & curves (measured)

The A1 law says "define curves once in `src/motion.ts`, never inline" and
names the presets — this file IS those presets, with values **measured from
the real `spring()` implementation** (overshoot % and settle time read off
rendered plots, not guessed). Copy the code block as the project's
`motion.ts`; pick by the move-class tables; vary per the A14 ledger.

## Springs (physics moments: land, pop, gather, arrival)

| Preset | config | Measured | Feels like | Use for |
|---|---|---|---|---|
| **snap** | d13 · k180 · m0.6 | **8.1% overshoot · settled 400ms (f12@30)** | a finger-flick | UI presses, micro-accents, kick hits on small elements |
| **bounce** | d9 · k150 · m0.8 | **23.8% overshoot · settled 833ms (f25)** | a dropped ball, two visible bounces | playful lands, mascots, hero/stat moments that may exaggerate (A2.10) |
| **smooth** | d26 · k120 · m1.0 | **0% overshoot · settled 633ms (f19)** | a door with a damper | elegant arrivals, panels, anything near body text |
| **heavy** | d16 · k80 · m1.6 | **4.3% overshoot · settled 933ms (f28)** | mass arriving | big cards, bass-led moments (A16 weight), full-frame objects |

Rules: overshoot budget follows A1 (2–4% UI · more only on heroes — so
`snap` is already at the UI ceiling and `bounce` is hero-only). Heavier =
slower settle; if a heavy element must settle fast, it isn't heavy — change
the element, not the physics. Springs drive HITS; beziers drive TRAVEL.

## Easing curves (travel)

| Name | cubic-bezier | Character | Use for |
|---|---|---|---|
| **EASE** | (0.83, 0, 0.17, 1) | the house thin-peak | most travel — the default |
| **EASE_OUT** | (0.16, 1, 0.30, 1) | instant burst, long settle | entrances |
| **EASE_IN** | (0.70, 0, 0.84, 0) | building acceleration | anticipation wind-ups & exits ONLY |
| **WHIP** | (0.90, 0, 0.10, 1) | near-vertical peak | slams, transitions, C0.5-dial-5 moves — pair with smear frames (A5) |
| **GLIDE** | (0.40, 0, 0.20, 1) | gentle, materials-style | dense UI walkthroughs, moves near reading text |

## Canonical `src/motion.ts`

```ts
import { Easing, spring } from "remotion";

// travel curves — never redefine inline (A1)
export const EASE      = Easing.bezier(0.83, 0, 0.17, 1);
export const EASE_OUT  = Easing.bezier(0.16, 1, 0.30, 1);
export const EASE_IN   = Easing.bezier(0.70, 0, 0.84, 0);
export const WHIP      = Easing.bezier(0.90, 0, 0.10, 1);
export const GLIDE     = Easing.bezier(0.40, 0, 0.20, 1);

// spring presets — physics moments (measured: see motion-library.md)
export const SPRING = {
  snap:   { damping: 13, stiffness: 180, mass: 0.6 },
  bounce: { damping: 9,  stiffness: 150, mass: 0.8 },
  smooth: { damping: 26, stiffness: 120, mass: 1.0 },
  heavy:  { damping: 16, stiffness: 80,  mass: 1.6 },
} as const;
export const hit = (frame: number, from: number, fps: number,
  preset: keyof typeof SPRING = "snap") =>
  spring({ frame: frame - from, fps, config: SPRING[preset] });

// beat grid (B1) — fill from the music map / analyzer
export const FPS = 30;
export const BPM = 0;                // ← project value
export const FIRST_BEAT = 0;         // ← project value
export const FRAMES_PER_BEAT = BPM ? (60 / BPM) * FPS : 0;
export const beat = (n: number) => Math.round(FIRST_BEAT + n * FRAMES_PER_BEAT);
export const bar  = (n: number) => beat(n * 4);
```

**A14 note:** the ledger tracks spring/curve choices as device parameters —
two elements may share `snap`; they may not share `snap` at identical
amplitude, delay, AND duration. Vary at least one.
