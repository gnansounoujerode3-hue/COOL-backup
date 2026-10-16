# The camera-move vocabulary — named moves, 2.5D implementations

The classic move names, each with: what it physically is, what it says, and
the EXACT implementation in this skill's rig convention (one perspective
wrapper → one transform on the space → planes at `translateZ`). Camera pose
convention: `transform: translate3d(−x, −y, z) rotateZ(−rz) rotateY(ry)
rotateX(rx)` on the space; `scale(s)` on the OUTER wrapper is the zoom axis
(post-projection = FOV change).

**The two distinctions that only exist once you have depth planes:**
- **Pan/tilt (rotation) vs truck/pedestal (translation):** rotation produces
  NO parallax; translation separates the planes. In 2.5D, big "pans across a
  scene" are almost always trucks.
- **Zoom (outer scale) vs dolly (camera z):** zoom magnifies everything
  equally; a dolly changes the *relationships* — near planes grow faster.
  This difference is the whole reason to build in 2.5D.

| Move | Physical | Says | 2.5D implementation | Watch out |
|---|---|---|---|---|
| **Truck** | camera slides left/right | follow travel, scan a scene, scene-to-scene transit | animate `x`; planes parallax automatically | the workhorse — preset A's glides are trucks |
| **Pedestal** | camera rises/falls, axis level | change of level, hands→faces reveals | animate `y` | pairs with truck for L-shaped reveals |
| **Dolly in/out** | camera moves toward/away | entering the world / leaving it; depth context | animate `z` (+ = in); planes separate | never a bare `scale()` — that's zoom, and the anti-AI-camera rule wants dollies paired with a lateral or roll component |
| **Zoom in/out** | focal length change | attention squeeze without spatial change | animate outer-wrapper `scale` 1→~1.2 | flat feel is the POINT of zoom; use when you *don't* want parallax (archival/CCTV/broadcast flavors) |
| **Dolly-zoom** (Vertigo) | dolly one way, zoom the other | unease, realization, world-shift | `z: 0→c` while outer scale compensates `s = (P − c)/P` (P = perspective, 1100): focal plane holds size, background crawls | the strongest move in the kit — one per piece, on the biggest narrative turn, tier-5 territory |
| **Pan** | camera rotates on Y | glance left/right, tension between two subjects | animate `ry`, SMALL (≤ ~6°) | flat planes go edge-on at big angles and the illusion dies; big scans = truck instead |
| **Tilt** | camera rotates on X | reveal up/down (knife → face) | animate `rx`, SMALL (≤ ~5°) | perspective distorts type — never tilt across crisp focal copy (A5 screen-flat plane) |
| **Roll** | camera rotates on Z | disorientation, energy accents | animate `rz` | already rationed by the grammar: ±0.9° poses, hit accents |
| **Crane / jib** | camera arcs up + tilts down (or reverse) | scale, arrival, finale | path: `y` down→up eased WITH compensating `rx` so the focal stays framed | the classic closer; pair with a section seam |
| **Whip (pan/truck)** | violently fast lateral | hard transition, chaos accent | truck at minimum T (~10–14f) + velocity smear per plane; landing sharp; can hide a cut at peak smear | this is a TRANSITION, not a shot; A14 ledger — twice max |
| **Handheld** | operator's body noise | authenticity, urgency, doc energy | **preset B (Reactive Shake)**, scoped | field-judged: never the standing behavior |
| **Steadicam / follow** | smoothed pursuit of a subject | intimacy with a moving subject | **preset C (Element-Follow)** — camera home tracks the focal with inertia | roadmap; needs travelling focals |
| **Rack focus** | focus shifts between depths | redirect attention without moving | animate `focusZ`: crossfade per-plane DOF blurs (far crisp→soft while near soft→crisp) over 12–20f | the "camera move" of attention; obeys CAM-2 — it must LAND on the narrative target |
| **Signature / custom** | the rope-swing | style identity | a named pose-path defined once in the style bible, reused as the piece's motif | CAM-1: vary its parameters between uses |

## Composing them

- Real moves are **pairs**: truck+pan (scan with a look), dolly+roll (the
  anti-AI pairing), pedestal+tilt (crane), truck+zoom (push-slide). Single-
  axis moves read mechanical — same law as element arcs (A2.7).
- **Dial gates the vocabulary:** 1 → cuts only · 2 → zoom/rack focus only
  (no spatial motion) · 3 → truck/pedestal/dolly as motivated phrases ·
  4 → full kit incl. crane paths · 5 → continuous pose-graph composition.
- **Music map places them:** glides/trucks land on section seams (preset A);
  dolly-zoom and crane belong to the piece's ONE biggest moment; whips are
  hot-section transitions; rack focus rides vocal/narrative handoffs.
- Every move remains a phrase (CAM-4): wind-up, travel, settle-into-breath —
  and the A14 ledger applies to moves exactly as to element devices.

*All implementations verified in the CamMoves glossary demo (fx-poc) —
rendered, viewed, each move labeled.*
