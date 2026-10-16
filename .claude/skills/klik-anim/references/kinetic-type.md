# Kinetic type — the reveal taxonomy (render-verified)

Load this when setting type in motion. Type is choreography: every law
already binds it — reading holds (A12), staggers (A3), exits (A1), the
ledger (A14), boundaries (A15), golden scale/leading (A10), only the
user's words (A8). This file is the device kit, each class verified in a
labeled demo against a real track.

## The reveal classes

| Class | Mechanics (verified numbers) | Reads as | Watch out |
|---|---|---|---|
| **Masked slide-up** (per word) | word rises through an `overflow:hidden` span, 108% travel, ~11f EASE_OUT, one word per beat; variation: descend from above | THE premium classic — editorial, Apple-adjacent | the mask must hug the line (pad ~0.08em) or descenders clip; last/emphasis word takes the glow |
| **Letter cascade** | per-letter rise 42px + fade, **1.5f stagger ±1f jitter** (A3/A4), ~9f each; variation: reverse direction | crafted, boutique | total = chars × 1.5f — budget against the reading hold; NEVER on long lines (>25 chars ≈ blur of motion) |
| **Emphasis slam** | ONE word, `heavy` spring (d16 k80 m1.6), squash on land + 2–4f shake echo, fired on a **bar-aligned kick** (A16) | the hit — stat/verdict moments | one per scene max (A3 rank-1); hero-scale overshoot territory (A1) |
| **Word swap** | sequential replace inside a SHARED mask: outgoing exits up as incoming rises — **the A15 continuation**; never a bare crossfade | list rhythm — "X · Y · Z" | give each word its A12 hold; the swap movement itself doesn't count as legible time |
| **Typewriter** | variable accelerating rhythm (start ~3.2f/char → ~1.4f, ±0.8f seeded jitter) + blinking caret (8f cycle) | device/terminal voice (A4) | the hold counts from typing START (A12 — viewers read along with the caret); scope it — it's a scene device, not a system |

Banned as primary reveals: bare opacity fade-in (A3's cheap-fade law applied
to type), per-letter opacity twinkle (dated), anything that moves crisp
focal text while it's being read (A5).

## Binding laws, applied to type

- **Hold math first** (A12): the floor `max(0.70s, 0.25s + chars ÷ 17)` per
  line — and the comprehension target `0.3s × words + 1.5s` for standalone/
  hero lines read cold — reveal and exit excluded. The reveal budget is
  what's LEFT of the phrase after the hold — if a cascade doesn't fit,
  shorten the cascade, never the hold.
- **Legibility thresholds while moving** (A12): `v_crit = h × fps ÷ k`
  (k ≈ 1.5–2.0) for text read in flight; entrances may exceed it only if
  the following hold carries the full reading time. Rotation ±15° max while
  being read (±45° = display-only territory); ≥24px rendered height for
  animated body text. **Past ±15° the hold pays A12's rotation tax
  `× (1 + |θ| ÷ 90)`** — ×1.33 at 30°, ×1.50 at 45° — charged on θ *as
  delivered to the reader*, so budget it before choosing the reveal class.
- **Emphasis words** (the SSOT's bolds): land them on strong beats, give
  them the glow/scale/color — and let the vocal LEVEL drive the aura when
  building to music (A16: the copy is the vocal's visual).
- **Exits**: 60–70% of entry duration, EASE_IN, usually upward — and every
  line boundary continues (A15): the next line enters from the departing
  line's origin or through the same mask.
- **Ledger** (A14): reveal class + direction + stagger rate is a device
  signature. Same class twice = vary an axis (direction, rhythm, color
  role) — the demo shows every class twice, varied.
- **Scale**: steps on the golden ratio (A10); display leading 0.95–1.1;
  one glow per frame (the boss).

## THE INERTIA LAW — real physics, three phases (F = ma throughout)

A letterform moved by its base is a mass with an anchored baseline. Newton
gives it exactly three behaviors, and the animation must produce all three
— nothing else reads as real (two failed models are recorded below):

**1 · LAUNCH — drag.** The base accelerates first; the mass above lags →
brief lean BACKWARD (opposite to travel), ∝ acceleration, ramping in over
the accel phase and decaying (~2.5f) once acceleration ends. Vertical
launches compress (up) / stretch (down). This is A2.5's drag, derived.

**2 · CRUISE — upright.** Constant velocity = no net force = NO
deformation. **The motion profile must be a trapezoid** (ramp → cruise →
hard stop): an eased arrival spends the momentum before the stop and
leaves nothing to whip — profile and reaction must agree or the physics is
fake regardless of the curve quality.

**3 · ARREST — the velocity-seeded ring-down.** The base stops dead; the
mass continues at v; linear momentum becomes angular momentum about the
baseline. **The angle does not jump — it starts at ZERO with maximal
angular velocity**, rises to its peak a quarter-period later, and rings
down through 2–3 visible rocks:

```ts
// θ(t) = A·e^(−t/τ)·sin(ω_d·t)   — ω_d ≈ 0.55 rad/f (period ~11f), τ ≈ 7f
// PEAK ∝ ARRIVAL SPEED: peakSkew = min(24°, 2.3·√v) · peakStretch = min(0.24, 0.021·√v)
// launch drag: dragPeak = min(8°, 1.1·√v), ramps in over accel, decays e^(−t/2.5)
// skew = ux·(drag − peakSk·ring) · scaleY = 1 − uy·peakSt·ring + uy·(launch term)
```

Speed-scaled peaks mean every dart whips differently — variance for free
(A14). Failed models, kept as warnings: **displacement-seeded** ("jump to
max angle, spring back" — the angle has no reason to be at max at t=0) and
**lean-while-moving** ("sprinter lean" — models an accelerating body, not
a cruising one). Velocity-seeding is the fix for both.

## The preset library (self-labeling glossary, all render-verified)

| Preset | Mechanics | Signature |
|---|---|---|
| **inertia** | LETTER BY LETTER, multi-directional: each letter darts in along its own LANE and shows the full three-phase law at ITS arrival (per-letter speed → per-letter ring); **lanes are collision-free by construction** — middle letters travel vertically (a column is exclusive), horizontal entries only at the word's ENDS where nothing is parked in the path — **horizontal → skewX rock · vertical → scaleY stretch/squash settle**, all `transformOrigin` baseline | momentum you can see, letter by letter |
| **gravity** | full deterministic physics sim (precomputed at module load, seeded → A0 holds): letters as heavy bodies + raining balls, circle-circle impulse collisions, letters knocked + spun but spring-restored to home/upright — the word survives readable | a physics playground — letters as objects among objects |
| **fade** | pure staggered opacity (2.5f stagger, 12f ease) — NO movement | the humblest entrance; motion disappears |
| **typing** | accelerating 3→1.4f/char + block caret | terminal voice (scoped device) |
| **trace** | stroked outline draws per letter (dashoffset, ~16f) then fill blooms | skeletal → solid; "written" territory |
| **painted** | CURSIVE STROKE-CONSTRUCTION: **no font, no mask** — each letter IS its ductus, connected so the pen never lifts inside the word, ribbon-rendered with the pressure model (thick downstrokes, thin connectors), i dotted and t crossed at the end; see the painted system below | real writing, weight and all |
| **morph (TRUE)** | vector letterforms reshape point-by-point into geometry and back — see the morph system below | fluid typography — the letter IS the shape |
| **flip** | per-letter card flips rotateX between words, 2.5f stagger | mechanical swap (kept as its own device) |
| **arc** | the rail DRAWS FIRST (dashed, ~14f), the word rides it with tangent rotation, the rail fades — signaling law applied: a path move is illegible until the path is visible | path motion that explains itself |

**A face per voice.** Presets carry their own typographic voice — pick the
family that IS the motion: Impact-class for inertia slams · geometric sans
for physics · high-contrast serif (Didot class) for fades · monospace for
typing · the extracted vector face for true morph · painted has NO font —
its ductus skeletons are its face. One scoped face per device (A14 / the
C2 brand allowance governs what's permitted per project).

**Face weight is mass.** Heavier letterforms move with more inertia —
slower acceleration, heavier springs, more follow-through; light faces are
nimble — snap/smooth springs, quicker settles. Pair the face's weight to
the spring preset (Impact → `heavy`, a light Didot → `snap`) and the
physics comes free (A2.1). A hairline face on a heavy slam, or Impact
fluttering in on a feather ease, is a face/motion contradiction — same
family as A17's meaning contradictions.

## Exits in the device's voice (render-verified set)

A preset's exit is the same device run BACKWARDS or ONE STEP TOO FAR —
never a transform on the scene container (A15's element-exit law). The
verified vocabulary:

- **inertia** — each letter launches back out its arrival lane: pure
  acceleration, so only the growing launch lean shows (it never arrives,
  so it never rings).
- **gravity** — the floor gives way; the container is the physics world,
  the one case where moving it IS moving the elements (½gt², slight
  tumble).
- **fade** — staggered letter fade-out in reverse reading order (legal:
  an element's own decay, not a crossfade between unrelated things).
- **typing** — BACKSPACE at accelerating key-repeat, caret alive to the
  end. (A CRT-collapse wrapper was the rejected first cut.)
- **trace** — strokes retract in reverse stagger while the fill drains.
- **painted** — the brush RETRACES its own ribbons in reverse writing
  order, head riding the retreating tip. Failed model: "painting it out"
  in ground color — over any gradient ground the cover stroke reads as a
  floating flat bar; cover-strokes only work on flat grounds.
- **morph** — letters morph out to their shapes once more and each shape
  collapses to zero where it stands (fixed-point scale: translate by
  `(1 − s) · center` so it shrinks about its own centre — A15's
  convergence).
- **flip** — one flip too many, per letter, to edge-on (90°) and gone —
  with the swap cycle FROZEN at its last rest pose first (a cycling
  device exits from rest).

Timing: exits run ~60–70% of entries (A1), staggered per element, and
OVERRUN the cut a few frames painted on top of the successor (A15).

**Continuity law for composed motions (render-found on inertia v1):** when a
travel phase hands off to a settle spring, the driven value must be EQUAL on
both sides of the handoff — v1 leaned ∝ velocity (≈0 by arrival) then the
spring re-kicked from full lean = a one-frame jitter. v2: lean into the run
(~5f), HOLD while travelling, spring-rock from the held value. Same family
as klik-cam's global-frame continuity trap.

## Motion semantics — the alignment table (A17 applied to type)

Motion is a semantic channel; pick the strategy that says what the words
say. Contradiction weakens the line even when the move is beautiful
(the canonical pair: "BREAKING THROUGH" — staccato letter-snaps at 3f
intervals with ±5° jitter, then the second word driving through with a
hard overshoot = visceral; the same phrase on a gentle fade = self-refuting).

| Semantic quality | Motion strategy | Timing pattern | Typical use |
|---|---|---|---|
| **Urgency** | fast, direct paths | short (<0.5s) | alerts, breaking moments |
| **Authority** | slow, centered motion | long holds (>3s) | brand statements, titles |
| **Playfulness** | bouncy, overshoot | elastic easing (`bounce`) | casual, character |
| **Precision** | grid-aligned, constant velocity | quantized, dead stops | specs, data, terminals |
| **Chaos** | erratic, multi-axis | seeded-irregular timing (A0) | disruption, glitch |
| **Elegance** | smooth curves, soft fades | `EASE` 1–2s | luxury, formal |

Directional/velocity/rhythm/transformation semantics are the law itself
(A17). Chaos rows still render deterministically — "random" timing is
seeded, always.

## THE PRECISION DEVICE (scoped linearity — A1's one exception)

The physics: a *driven* system (stepper motor, print head, CNC) is
velocity-controlled — it moves at constant speed and **stops dead**; the
controller absorbs the momentum. A *free* mass rings down (the inertia
law). Both are real; what's fake is mixing them. The device's grammar is
all-or-nothing:

- Constant-velocity moves and **hard stops with ZERO settle/overshoot** —
  a linear move that bounces is incoherent (nothing is left to bounce);
  an eased move that dead-stops reads as a glitch. Profile and reaction
  agree — the inertia law's rule, resolved to the opposite pole.
- Distances and durations **quantized**: whole beats/frames, snap-to-grid
  positions. Machine timing sits naturally on the bar grid (A16/B1).
- **Semantic gate:** only when the subject IS mechanical/technical/data —
  never emotive copy, never a default keyframe accident.
- **Scope:** one context per piece (A14), technical/monospace voice,
  ledger-recorded, never in the same shot as inertia devices.
- `lint-motion.mjs` flags the linear easing — waive it by name:
  `// klik-lint-disable-next-line — PRECISION device (A1/A17)`.

## THE PAINTED SYSTEM (stroke construction — render-verified)

Painting is CONSTRUCTION, not revelation. If the letterform exists before
the brush touches it and paint merely uncovers it, it is not painting —
two failed models are recorded below. The real system (cursive + pressure):

1. **Break each letter into its ductus** — the ordered stroke skeleton a
   writer actually uses. For script: one continuous body stroke per letter
   (entry upstroke from the baseline → body → baseline exit), letters
   CONNECTED exit-to-entry so the pen never lifts inside the word; the
   **deferred strokes (i-dot, t-cross) draw AFTER the word completes** —
   real writing order. Hand-author each stroke as a few-point skeleton in
   a per-letter box (baseline y=100, x-height ~52, ascender ~30, descender
   ~135); per-letter advance widths, never monospace; slant is a shear on
   the points (`x += (baseline − y) × tan(slant)`), not a CSS transform.
2. **Catmull-Rom the skeletons** into dense polylines — the hand-authored
   points stay few, the pen path curves like a real stroke, and all
   arc-length math works on the result.
3. **Line weight is the pressure model — never constant.** A uniform
   stroke width is the flat-weight tell. Render each stroke as a **ribbon**
   (offset the path ±width/2 along its normal, fill the polygon): width
   per point = `wMin + (wMax − wMin) × downwardComponent` — **downstrokes
   thick (pressure), upstrokes and connectors thin** (the broad-nib/
   pointed-pen law), tapered over the first/last ~30px of arc (touchdown
   and lift). Retraces (p, n) redraw thin over their thick downstroke,
   exactly as ink does.
4. **The brush draws at constant px/f speed** — ribbon cut at the live
   tip, round start cap, bristle turbulence (`feTurbulence` +
   displacement) for edge, a **brush-head ellipse riding the tip rotated
   to the tangent**. SPEED sized so word + diacritics complete with the
   A12 hold still left in the window — hold math first, as always.
5. **Mid-frames must be real partial letterforms** — a cursive `n` is a
   single leg before its arch; the `i` sits undotted until the word is
   done. That is the proof it's construction; a reveal never produces
   those states.

Failed models, kept as warnings: **outline dash-trace** (reads as
graffiti/neon tube, user-rejected), **clipPath-stencil zigzag fill** (a
masked reveal wearing paint texture, user-rejected — the letter
pre-exists), and **constant-width polyline strokes** (block letterforms
with butted caps: every junction shows a seam cut and the weight is dead
flat, user-rejected — ribbons + pressure are the fix).

## THE TRUE MORPH SYSTEM (fluid typography — render-verified v1)

"Morph" means RESHAPING the letterforms, not swapping them. Pipeline:

1. **Remake the font in vector at build time** — `opentype.js` loads the
   TTF, glyph outlines flatten to polylines (14 samples/curve).
2. **Canonicalize** every contour: resample to a fixed N (96) points by
   arc length · force clockwise winding · rotate the index so point 0 is
   the topmost — this stops morphs twisting.
3. **Targets are rings in the same canonical form** (N points, clockwise
   from top): circle/tri/square/star — or another glyph's contours.
4. **Morph = lerp the point sets** (easeInOut ~14f), render as
   `<path fill-rule="evenodd">`.
5. **Holes** (O/R/P counters): pair the inner contour with a sub-pixel
   degenerate ring (r ≈ 0.01) at the target's centre — the counter
   collapses on the way out and re-emerges on the way back. (r = 1 leaves
   a visible dot — render-found.)

Known v1 limit: arc-length correspondence can pinch mid-morph on
donut-like glyphs (O briefly waists). v2 upgrade when needed: angular
resampling around the centroid, or match by normalized angle.

## Study — the canon (Hackernoon guide taxonomy)

The guide's examples are external embeds (Dribbble/Tumblr; Gfycat is dead)
so they couldn't be frame-extracted — this study is from its taxonomy and
the named artists' documented signatures, to be refined against real refs
via the method's reference-analysis pass. **A separate seven-title canon
HAS been frame-verified** (Honda, MK12 ×2, Picturemill, BUCK, Oxfam,
Ginetta) — see the study table in `references/layout.md`; where the two
disagree, the frame-verified numbers win:

- **Fluid typography / morphing** (TAPE, Al Boardman) — the prize: letters
  as living vector material. Boardman-style state transitions keep VOLUME
  roughly constant mid-morph and land on grid-crisp end states — morph
  wants soft middles, decisive ends (our easeIO does this).
- **Create/destroy** (David Stanfield) — words aggregate from shapes /
  dissolve into them: our morph system run one-directional, with staggered
  particles. Hero device (A14). **Frame-verified variant (Ginetta "We
  simplify"):** aggregate from *letter-parts* rather than shapes — stems,
  bowls and dots scattered at deconstructed positions, converging into the
  word, each fragment carrying its own colour that resolves to mono on
  arrival. The colour convergence is what makes the assembly read as order
  emerging from chaos; without it the fragments read as debris. A worked
  example of A17 — the reveal enacts the word.
- **Inventive metaphor** — serifs become feet, counters become eyes:
  per-glyph character rigs; pairs with the expression-rig pattern.
- **Arc/path motion** (dudenas) — baselines are paths, not rails.
- **Signaling motion** — the small move that cues the big one (=klik-cam's
  motivation law, element side).

## Imported laws (kinetic-typography canon)

- **Maintain linearity** — reading order survives the animation; letters may
  arrive playfully but never out of reading sequence for running copy (A12's
  gaze law applied to reveals; display single words may break it for effect).
- **Maintain relativity** — typographic elements move relative to EACH
  OTHER; a line is a system, not independent sprites (A3's phrase law).
- **Signaling motion** — a subtle pre-move can cue a larger one (pairs with
  klik-cam's motivation law: the signal is what the camera reacts to).
- **Fluid/create-destroy territory** (type ⇄ shapes, aggregation builds) —
  powerful, expensive; treat as hero devices, one per piece (A14).

Sources: Hackernoon "Kinetic Typography Quickstart" taxonomy + principles;
Material Design type anatomy (baseline/x-height as physical structure).
Springs/curves come from `references/motion-library.md`.
