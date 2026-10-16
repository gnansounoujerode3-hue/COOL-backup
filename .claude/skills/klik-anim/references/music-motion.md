# Music → motion recipes — implementing §A16

Load this when building anything that moves to music. It turns the method's
analyzer output (`analyze-audio.py --json`: the music map + `events` +
`levels`) into element motion. **Every recipe here was render-verified against
a real song in an isolated POC** — kick impacts, snare echoes, hat shimmer,
vocal glow, bass mass, and a tier-driven section shift, checked in frames.

Camera-side mappings live in `klik-cam` CAM-5 — do not mix the layers.

## The data

```jsonc
// analyze-audio.py --json out.json  (stem mode via demucs when installed)
{
  "frames_per_beat": 14.52, "first_downbeat_frame": 33,
  "energy_tier_per_bar": "111222155543…",        // tier 1–5 per bar
  "music_map": [ { "bars": [4,12], "start_frame": 265, "tier": 1.8,
                   "lead": "bass", "attack": "sharp (~23ms)", … } ],
  "events": { "kick": [267,272,…], "snare": […], "hats": […],
              "vocals": […], "bass": […], "guitar": […], "piano": […] },
  "levels": { "kick": [0.01,…], "vocals": […], … }  // per-frame, 0–1
}
```
Import it into `src/` (`resolveJsonModule: true`) — it's data, deterministic,
pure function of frame (A0). Band mode gives `low/mid/high` keys instead;
same recipes, coarser sources.

## Core helpers (verified — copy into `src/music.ts`)

```ts
/** Latest event ≤ frame → exp-decay intensity 1→0. Attack is INSTANT —
 *  a transient's rise is under one frame (A16); the decay is the settle.
 *  decay 3–4 ≈ tight percussive · 8–10 ≈ ringing/heavy. */
export const hitPulse = (events: number[], frame: number, decay = 3.5, window = 18) => {
  let lo = 0, hi = events.length - 1, best = -1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (events[m] <= frame) { best = events[m]; lo = m + 1; } else hi = m - 1;
  }
  if (best < 0 || frame - best > window) return 0;
  return Math.exp(-(frame - best) / decay);
};

/** Smoothed level follower — sustain-shaped amplitude. ±4f ≈ 130ms box
 *  average: musical, not jittery. Hits ride EVENTS; glow/mass ride LEVELS. */
export const levelAt = (levels: number[], frame: number, smooth = 4) => {
  let s = 0, k = 0;
  for (let f = frame - smooth; f <= frame + smooth; f++)
    if (f >= 0 && f < levels.length) { s += levels[f]; k++; }
  return k ? s / k : 0;
};

/** Energy tier (1–5) of the bar under this frame. */
export const tierAt = (frame: number) => { /* bar = (frame−DOWN0)/(FPB·4) → TIERS[bar] */ };

/** Every nth event — "mapped, not literal" (A16/A4): sample the hats. */
export const everyNth = (ev: number[], n: number, off = 0) => ev.filter((_, i) => i % n === off);

/** THE INTEGRAL LAW (render-found): any rotation/travel whose SPEED rides
 *  a music signal must drive its position from the ACCUMULATED rate —
 *  `pos = frame × rate(frame)` JUMPS whenever the rate moves, by
 *  frame × Δrate: measured 733° in ONE frame at f≈3000 on a track whose
 *  tiers alternate bar-to-bar ("the oval jitters"); the integral's worst
 *  step was 1.15° — its top speed, smooth by construction. Same
 *  continuity family as the handoff/glide laws. Precompute at module
 *  scope (A0-pure, like a physics sim): */
export const rateIntegral = (base: number, gain: number): number[] => {
  const n = ((LEVELS.full ?? LEVELS.low ?? []).length || 4000) + 90;
  const out: number[] = new Array(n);
  let a = 0;
  for (let f = 0; f < n; f++) { a += base + gain * heatAt(f); out[f] = a; }
  return out;   // usage: const ORBIT = rateIntegral(0.25, 0.9)  →
};              //        rotate(ORBIT[clamp(frame)]) — never frame × rate
```

## The mappings (each render-verified)

| Source | Drives | Recipe |
|---|---|---|
| **kick** | THE primary hit | squash-pop `scale(1+0.05p, 1+0.10p)` (A2.1) + seeded screen-shake ±3px·p + shadow/ground pulse. `decay 4` — heavy things settle slower (A16 weight). One rank-1 mover at a time (A10). |
| **snare** | secondary echo | accent elements (side bars, underline flicks) driven by `hitPulse(snare, frame - 3)` — the **3f lag** makes it an A3 echo, not a competitor. Amplitude ≤ ~60% of the kick's. |
| **hats** | micro life | `everyNth(hats, 2)` → shimmer field, per-element phase offset (`frame - (i % 4)`), amplitude tiny (opacity/scale ticks). Never every hat — that's mickey-mousing. |
| **vocals** | the focal's aura | `levelAt(vocals)` → glow radius/intensity on the copy (the focal element, A10). Vocal *onsets* can cue word-emphasis in kinetic type. |
| **bass** | mass & ground | `levelAt(bass, 6)` (slower smooth — bass is slow) → background blob scale, vignette depth, drift amplitude. Weight, not flashes. |
| **guitar/piano** | melodic accents | mid-amplitude accent events where the arrangement leads with them (check the map's per-section patterns — don't invent hits the section doesn't have). |
| **tier** | density + local pacing | element count, idle-life amplitude, palette heat all step with `tierAt(frame)`; tier ≥ 4 unlocks the piece's hero devices (A14: never spent on verses). |
| **section boundary** | scene character | `music_map[i].start_frame` is where palettes/density/devices switch — boundaries continue per A15; the switch rides a transition, never a hard swap mid-hold. |

## Discipline (what keeps this from being a visualizer)

- **Match each parameter to its signal's TIME-SCALE.** Transient pulses →
  frame-scale (hits, squash). Levels → word/beat-scale (glow, mass). Bar
  tiers → density and speed. **Temperature/palette → SECTION-scale only**:
  average the tier over ±2 bars before mapping to hue — a color that
  flickers with bar-to-bar tier changes reads as noise, not heat
  (render-found on a track whose tiers alternate every bar). Drastic
  palette maps (blue → violet → red → gold across the tier range — the
  cool→hot path that never passes green) want the SLOW signal; give the
  fast signals to geometry.

- **Reactive motion is garnish, not choreography.** The scene's designed
  moves (entrances, travels, reveals) stay authored on the beat grid (B1);
  events drive *impacts and life*, levels drive *amplitudes*. If removing the
  music data would leave nothing moving, the scene was never designed (A6/A12
  still bind).
- **Amplitude subordination (A10):** reactive accents never outrank the focal
  move. A hat shimmer that pulls the eye off the copy is a defect.
- **Swells have no events** — sections marked "no transients: swell/pad
  territory" are ramp territory: long `EASE_IN` pushes and blooms driven by
  `levelAt`, no pulses (A16 attack law).
- **Verify with both checks (A9):** stills at event frames prove the hits
  land; the arithmetic (event frame vs visual peak ≤ 1f apart) proves sync a
  still can't show. Watch one section boundary with audio before shipping.
