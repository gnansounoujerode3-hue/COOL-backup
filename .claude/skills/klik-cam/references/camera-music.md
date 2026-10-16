# Camera ← music recipes — implementing CAM-5 / CAM-6

## The preset family (field-judged)

| Preset | What | When |
|---|---|---|
| **A · HOLD & GLIDE — the DEFAULT** | Camera holds on each scene (Anchored-level breathing only, ≤0.5% creep + gentle level swell on depth), then ONE composed zoom/slide glide per musical seam, **starting T frames early so it lands on the incoming downbeat**. Scenes sit side by side in world space — the camera travel IS the scene change. T scales with the incoming tier (~24f hot, ~50f calm); per-section poses are quantized (3 zoom levels × 3 heights × 3 rolls) so consecutive framings differ readably. | Motion graphics, default for dials 2–4. Field verdict: continuous reactive drift "reads as camera shake, not MG" — holds + composed transitions read as design. |
| **B · REACTIVE SHAKE — opt-in** | The sidechained continuous rig (per-section drift signatures, bar-kick hits, duck envelope — the full CAM-6 sidechain math below). | Handheld/hype energy: performance montages, dial-5 sizzle, single hero sections. Never the standing behavior — scope it to a section and record the choice. |
| **C · ELEMENT-FOLLOW** | Camera pursues the focal's **phrase-level path**, never its per-frame motion — hops/bounces play inside a stable frame. Verified mechanics below. | Travelling focals: journey pieces, cursor tours, anything the eye must stay with. |

Named single moves (truck/dolly/dolly-zoom/whip/rack focus…) live in
`references/camera-moves.md` — preset A composes its glides from that
vocabulary.

**Continuity trap (render-found):** every always-on layer of the pose —
breathing, drift, swell — must be keyed to the **global frame**, never to
the section index. A section-keyed phase (`sin(f/95 + section·1.7)`)
teleports its offset the frame the index increments: a one-frame pop at
every glide landing. Verify seams numerically: frame-difference the render
across each boundary — the landing frame's diff must be in line with its
neighbors. / CAM-6

Load this when a piece's camera should follow the music. It turns the
method's analyzer output (music map + `events` + `levels`) into camera
movement. **Every recipe was render-verified in a 2.5D POC against a real
track.** Two presets, field-judged:

## PRESET A — HOLD & GLIDE (the default for motion graphics)

The camera **holds** on each section's pose — Anchored-level breathing only
(≤0.5% creep) — then executes ONE composed zoom/slide transition per musical
seam. Field verdict drove this: continuous reactive drift "reads as camera
shake, not motion graphics."

- **Scenes live side by side in world space** (one slot per music-map
  section, e.g. 2400px apart); the camera travel IS the scene change.
- **Arrive on the seam:** the glide STARTS `T` frames before the next
  section's boundary and LANDS exactly on its downbeat — the move belongs to
  the music. `T = clamp(56 − 6·tier_incoming, 24, 50)`: hot section ⇒ snappy
  arrival, calm ⇒ long glide. Monotone ease-in-out — no overshoot (C0 rule).
- **Poses are quantized per section** (zoom level ∈ {0, 80, 150} · y ∈
  {−45, 0, 45} · roll ∈ {−0.9°, 0, 0.9°}, seeded) so each transition reads as
  a deliberate zoom-in / zoom-out / rise / drop — CAM-1 variation without
  wander.
- **Holds carry only breathing + a gentle level swell on depth** — during
  element phrases the camera is still by construction (CAM-6 satisfied
  structurally: it moves BETWEEN element phrases, at the seams).

## PRESET B — REACTIVE SHAKE (opt-in accent flavor, never the default)

The sidechained continuous rig below (drift + bar-kick hits). Field-judged
too twitchy as a standing behavior — **use it scoped**: a hype section, a
performance montage, a deliberate handheld-energy moment. The user opts in;
record the scope in the spec.

## ROADMAP — ELEMENT-FOLLOW (next)

The third preset: the camera framing driven by ELEMENT positions (follow a
travelling focal with inertia, reframe on staging changes, gaze-anchored
homes per A12) with music as the timing layer. Deliberately deferred.

---

# Preset B mechanics (the original CAM-5 rig)

Element-side mappings live in `klik-anim references/music-motion.md` —
the camera takes the music's **big body** (bars, sections, drops); elements
take the syncopation and the surface detail. Do not mix the layers.

## The rig shape (CAM-3 compliant)

```
outer AbsoluteFill        perspective: 1100        ← NO filters, ever
└─ THE SPACE  div         preserve-3d; the camera is EXACTLY ONE transform here:
   │                      translate3d(−x,−y,z) rotateZ(−rz) rotateY(ry)
   ├─ far plane   div     translateZ(−380) · DOF blur 2px   (parked, soft)
   ├─ mid plane   div     translateZ(0)    · crisp          (FOCAL — CAM-2)
   └─ near plane  div     translateZ(240)  · DOF blur 1px   (biggest parallax)
```

Lateral camera translate + perspective produces true parallax (near planes
shift more on screen); pair it with a small `rotateY` (`ry = x * 0.008`) so
no move is ever a pure truck (anti-AI-camera).

## The verified mappings

| Music | Camera | Recipe |
|---|---|---|
| **Section** (map rows) | drift **signature** (CAM-1) | Per-section seeded signature: axis mix, period 110–240f, roll weight, magnitude — all differ at every musical seam. **Crossfade signatures over ~36f with smoothstep** after each boundary: the character changes at the seam, the camera never teleports. |
| **Energy tier** | activity within the dial | `tierScale = [.22, .32, .55, .85, 1.15][tier]` multiplies drift magnitude. Tier 1–2 = the dial's floor (breath only); tier 5 = its ceiling. The breakdown *exhale* is as expressive as the drop hit. |
| **Bar-aligned kicks** | the camera HIT | Filter kick events to within ±2f of a bar line (`(e − DOWN0) mod (FPB·4)`) — the POC track kept 42 of 279 kicks. Hit = `hitPulse(barKicks, f, 5)` driving `z += 34·p`, `rz += 0.55·p`, `x += 7·p` — push + paired roll + lateral, exp decay into drift (CAM-4: never a dead stop). **Never hit on every kick** — syncopation is element territory. |
| **Swells / level** | the slow push | `z += 130 · (0.6·levelAt(bass, 8) + 0.4·levelAt(full, 8))` — ramps by nature of the smoothed level; no pulse. |
| **Camera speed** | shutter smear | `camSpeed(f) = |Δpose|` between f and f−1; `smear = clamp((speed − 3) · 0.35, 0, 4.5)` px added to **each plane's own blur**. Non-zero only 2–4f around a hit; the landing is sharp by decay. |

## DISCOVERED TRAP — sample-stacking motion blur flattens 3D

`@remotion/motion-blur`'s `CameraMotionBlur` composites fractional-**opacity**
samples. Opacity is a CSS *grouping property*: it forces `transform-style:
flat`, so a `preserve-3d` camera space inside it **collapses — mid/near
planes vanish** (render-verified failure; the far plane's leftovers made it
look like a partial render). This is CAM-3's ancestor-filter law in another
costume: **no filter, no opacity < 1, no grouping property on the space or
any ancestor of it.**

- DOM 3D rig → implement the smear as the per-plane velocity blur above.
- `CameraMotionBlur` remains correct for **flat scenes** (camera faked in 2D
  transforms without preserve-3d) — that's its domain, not this one's.

## Core code (verified — `src/music-cam.ts`)

```ts
export const barKicks = kicks.filter((e) => {
  const pos = ((e - DOWN0) % BAR + BAR) % BAR;
  return pos <= 2 || pos >= BAR - 2;                 // the big body only
});

const signature = (i: number) => ({                   // CAM-1, per section
  ax: random(`sig-ax-${i}`) * 2 - 1,
  ay: (random(`sig-ay-${i}`) * 2 - 1) * 0.55,
  rz: (random(`sig-rz-${i}`) * 2 - 1) * 0.9,
  period: 110 + random(`sig-p-${i}`) * 130,
  phase: random(`sig-ph-${i}`) * Math.PI * 2,
  mag: 34 + random(`sig-m-${i}`) * 46,
});

// camPose(frame): section drift (crossfaded 36f at seams, smoothstep)
//   + swell push from smoothed levels + bar-kick hit (z/rz/x paired, decay 5)
//   + ry = x * 0.008  — full implementation in the POC, structure above.
```

## Preset C — ELEMENT-FOLLOW (render-verified)

CAM-6 doctrine applied to pursuit. Three mechanisms, all pure functions of
frame:

- **The landing track.** The follow target is where the focal will LAND, not
  where it is: the moment a hop/phrase starts, the target jumps to its end
  point. The element's arcs, squash, and bounces play out INSIDE a stable
  frame — the camera tracks phrases, the element keeps the syncopation.
- **Lookahead lead room.** Sample the landing track ~14f into the future
  (deterministic — the future is data) to counter the inertia lag: the
  subject then rides slightly *behind* center with clear space ahead — real
  follow grammar. Without it the camera *chases* (subject ahead of center —
  a render-found defect, fixed and re-verified).
- **Inertia.** Camera x = trailing exponential average of the target
  (`Σ target(f−k)·e^(−k/10)`, k ≤ 36) — steadicam glide, natural lag on
  direction changes, settle-into-breath. Breathing/swell layers key to the
  GLOBAL frame (continuity law).

**Boss handoff (A12 eye-trace made physical):** when the focal changes, the
target blends to the new boss over ~30f with smoothstep, keyed to the
musical seam — never a snap. And the outgoing boss must actually YIELD:
render-found, the traveller kept advancing on sparse breakdown kicks and
wandered past its replacement mid-handoff — a resting boss's residual event
stream is texture, not travel; freeze its phrase motion for the handoff
span.

**THE GOVERNOR — the jarring threshold.** Too much camera movement
back-to-back is jarring regardless of what demands it. Two caps, both
render-found and numerically verified:

- **Element phrases complete.** An event may only start a travel phrase if
  the previous phrase has landed (greedy min-gap = phrase duration + a
  ground beat). Without it, dense syncopation (kicks 2–5f apart vs a 12f
  hop) snaps the base position forward — the subject **teleports**. Events
  beyond phrase capacity are texture, not travel.
- **Sustained camera speed cap** (~13px/f at 1080p): a forward pass clamps
  the follow target's per-frame advance, so demand bursts become a steady
  glide toward the *trend* instead of surge-after-surge — the operator
  going steady-and-wide when the subject gets frantic. Verify numerically:
  max per-frame camera delta ≤ cap across the piece; the focal's max delta
  ≤ its own phrase cruise speed.

Music layer on top: tier can scale follow tightness; depth-only co-fire on
bar-kicks stays tiny — the travelling element owns its own impacts — and is
**gated OFF entirely while the boss is not the traveller** (render-found: a
bar-aligned kick during the handoff pushed the camera while it contemplated
a resting boss — jitter on a moment that must be still).

**Per-segment physics (element side, feeds the follow):** when travel
energy evolves with the piece, keep **gravity constant** and derive
airtime from bounce — `T = √(8h/g)`; height and stride scale with the
section tier, impact squash/ripple scale with height (A16 weight). Size
the governor cap just above the fastest segment's cruise speed
(`max(stride/T)`) so steady travel passes while bursts still cap.

## CAM-6 layer — the sidechain (v2, render-verified A/B)

v1 of this rig moved the camera off the music alone and walked the subject
off-center during busy element phrases. v2 subordinates it (the DEFAULT;
user-overridable as a recorded spec decision):

```ts
// authored element motion — the SAME music data, used a second time:
elementMotion(f) = min(1, kickPulse + 0.5·snarePulse + 0.2·hatPulse
                        + |Δ bass level|·8 + |Δ vocal level|·5)

// sidechain envelope — fast attack (current value counts fully),
// slow release (~24–30f perceptible tail):
duckEnv(f) = max over k∈0..30 of elementMotion(f − k) · exp(−k / 12)

// the camera's claim on the residual:
DIAL_GAIN = [—, 0, 0.18, 0.5, 1.0, 1.5]        // C0 dial = claim multiplier
gXY = tierScale(tier) · DIAL_GAIN[dial] · (1 − 0.85·duck)   // frame plane
gZR = tierScale(tier) · DIAL_GAIN[dial] · (1 − 0.45·duck)   // depth/roll
// → complementary axes: elements own the frame plane, camera's residual
//   lives in depth. Margin cap AFTER gains: |x| ≤ 55px, |y| ≤ 40px (A11
//   inner pocket at 1080p). Accent co-fire (bar-kicks, tier ≥ 4) is EXEMPT
//   from the duck, scaled by the dial, and rides z/rz with only ~4px x.
```

Verified A/B on the same track and frames: busy tier-5 frame — v1 subject
displaced right + tilted, v2 dead-center with camera parked; bar-kick frame —
v2 keeps the push + smear co-fire with composition held. The music is still
audible in the camera — it just speaks in the gaps the elements leave.

## Judging it (CAM checklist hooks)

- Two stills in different sections show different drift orientations (CAM-1).
- A breakdown still is crisp and near-home; a hit still is displaced AND
  smeared; 3 frames later it is sharp again (checklist 3–4).
- The focal plane stays crisp through every drift (CAM-2) — whole-frame smear
  is allowed only at the 2–4 frame velocity peak.
- Scrub any section seam: the signature changes, the camera never jumps.
- **CAM-6:** pick the busiest element frame — the focal centroid sits inside
  the inner margin and the camera is near-parked; pick a designed hold — the
  camera carries the life. If both fail, the sidechain isn't wired.
