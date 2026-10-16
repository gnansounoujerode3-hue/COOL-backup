# Layout & positioning — the composition models (frame-verified)

Load this when deciding **where copy lives and how the frame relates to it
across a sequence** — the axis above the reveal device. `kinetic-type.md`
answers *how a word appears*; this file answers *where it sits, what else is
on screen with it, and what the frame does while it's read*. Camera grammar
stays klik-cam's (C0, CAM-1..6); this file only says which model the camera
is serving.

**Pick ONE model per passage and record it in the spec** — like a dial value,
never a silent drift. Mixing models inside one passage is the failure mode:
copy that half-accumulates and half-replaces reads as a broken system.

Provenance is labelled throughout: **[measured]** = extracted from the
reference frames · **[observed]** = read off frames, not counted ·
**[proposed]** = ours, to be render-verified.

## The five models

| Model | Copy lives | The frame | Canon ref | Reach for it |
|---|---|---|---|---|
| **Fixed anchor** | one slot, all copy cycles through it | locked | Honda "Keep Up" | manifestos over a live plate; maximum negative space |
| **Accretion artboard** | a persistent 2D canvas; copy accumulates, nothing exits | travels across the canvas | MK12 "Brazil Inspired", Oxfam Ebola | dense energy, editorial montage, sequences that must feel authored as one artefact |
| **Growing line** | one line, anchored at its start, extending | locked | Childline "First Step" | long-form narration, quiet emotional copy |
| **World-space type** | a static object in the 3D scene | reveals it by parallax | Picturemill "Panic Room" | type as architecture; live-action integration |
| **Annotation layer** | hairline overlay tracked to the plate | follows the plate | MK12 "Stranger Than Fiction" | measuring/annotating a world rather than stating over it |

Only **Fixed anchor** matches the default enter → hold → exit assumption the
rest of this skill is written against. The other four need the resolutions
below, or the laws read as violated when they are not.

---

## 1 · FIXED ANCHOR

One slot. Every word cycles through it; nothing else on screen moves.
The entire craft is hold timing — there is no reveal to hide behind.

- **The anchor is a feature of the PLATE, not the frame centre.** Honda sets
  the word's baseline exactly on the horizon at ~48.5% frame height, dead
  centre horizontally — not the geometric 50% **[measured]**. Type anchored
  to a real line in the footage sits *in* the shot; type at frame centre sits
  *on* it. Find the plate's line (horizon, table edge, architectural rule)
  and set the baseline there.
- **Scale is small and constant.** Cap height ~10% of the active image
  height **[measured]**; the count-in and the logo are the only scale
  changes. Emphasis is weight and colour, not size.
- **Everything else is the plate.** Product/subject enters the plate itself
  and shares the anchor line — never a second graphic layer competing.

Reading holds are A12's, unchanged — unless the passage is a declared
**SPEED-READ device** (A12's licensed exception), whose measured grammar is:

| | Value | |
|---|---|---|
| Base rate | **4f/word @25fps** (0.13–0.16s) | [measured] |
| Sentence-end hold | **12–18f**, 3–4.5× base | [measured] |
| Ratchet across the piece | 5f → 4f → 3f, bursting to 2f | [measured] |
| Overall | ~5.9 words/sec | [measured] |

**The long hold is the punctuation** — it is literally the full stop, and it
is the only reason the passage stays parseable. A speed-read passage with an
even rate is unreadable noise, not a device. Honda: 204 word events over
34.9s of manifesto.

---

## 2 · ACCRETION ARTBOARD — and the reading pocket

Copy is **never replaced**. It accumulates on one persistent 2D canvas, and
the camera travels across that canvas. Old copy exits by leaving frame under
camera motion — never by animating out.

### The reading pocket (resolves A12 × CAM-6)

The naive read is that accretion violates A12 ("the eye reads at rest") and
CAM-6 ("gaze-anchored, margin-capped — the focal centroid never leaves the
inner ~8%"). It does not, because **in accretion the reading frame is not the
video frame.**

- Define a **reading pocket**: a fixed region in *screen* space where the
  active run is always delivered — comfortable scale, near-horizontal angle.
- The camera moves so **the pocket stays put while the canvas travels
  beneath it.**
- A12 holds: the eye *is* at rest — in the pocket. Reading time is budgeted
  for the run while it occupies the pocket, and the pocket's contents are
  what `v_crit` is measured against — not the canvas.
- CAM-6 holds: the margin cap is measured against **the pocket**, not the
  canvas centroid. The boss never leaves the pocket; the canvas does.

If a run is read while crossing the frame rather than while parked in the
pocket, that is the ordinary A12 violation and the ordinary fix applies.
The pocket is a coordinate change, not a licence.

### The armature

- **A new phrase gets a new baseline at a new angle, anchored to the previous
  run's terminus** — the hinge. Baselines run 30–45° off horizontal
  **[observed]**; letters build *along* the baseline rather than the word
  popping in whole.
- **The camera counter-rotates** so the active baseline reads near-horizontal
  in the pocket while older runs skew away. This is what buys the ±45°
  display allowance in A12 — the copy is rotated *in canvas space*, not in
  reading space. **This is also what makes accretion affordable:** A12's
  rotation dwell tax `× (1 + |θ| ÷ 90)` charges θ **as delivered**, so a run
  authored at 45° on the canvas but presented at ~5° in the pocket pays ~6%,
  not 50%. A pocket that delivers copy still tilted pays the full tax — and
  at accretion's ~0.87s composition cycle there is no room for it. Counter-
  rotation is a timing requirement, not a stylistic flourish.
- **Adjacent runs at different angles must differ in colour role.** Brazil
  alternates its two inks between neighbouring runs precisely because
  geometry alone leaves the reading order ambiguous where two baselines meet
  **[observed]**. Two adjacent runs in the same ink at different angles is
  the ambiguity bug.
- **Scale ratio is extreme** — hero:caption ≈ 10–20:1 **[observed]**. The
  caption tier is *texture, not information* (see the ladder below).
- **A fixed corner mark** (both MK12 pieces hold one bottom-right for the
  full runtime **[observed]**) establishes a stable UI plane above the
  moving canvas. Cheap, and it is what stops a constantly-moving canvas
  reading as unmoored.

### The demotion ladder (resolves A10)

In accretion the boss is **the newest run**. A10's one-boss law is satisfied
by demotion, not by exit — and the demotion is mechanical, not art-directed:

1. On the next run's arrival, every existing run steps **down one tier**:
   hero → secondary → caption/texture.
2. Each step is **scale ÷ φ** (A10's golden steps, 1.618 default).
3. A completed block may additionally **rotate to the margin** — Oxfam turns
   its finished stack 90° and parks it at the left edge, holding it as
   context **[observed]**.
4. **Caption tier is texture: it is NOT budgeted for reading time.** This is
   load-bearing beyond A10 — without it, accretion blows A12's Σ-holds
   feasibility sum on the third run. Anything that must be *read* has to be
   at hero or secondary tier while it is read.

### How A15 resolves

Accretion has no departing line, so "boundaries continue, never reset" is
satisfied **trivially** — continuity is total because nothing resets, and
A15's element-exit clause is moot where there are no exits. The boundary
that does need continuing is the **hinge**: each new run's baseline anchors
to the previous run's terminus. That is A15's principle in layout terms.
Likewise A15's "incoming attractor within ~2f of every cut" applies at
passage boundaries only — inside an accretion passage there are no cuts.

### Rhythm

Brazil runs **~175 settle/move cycles in 152s — a new composition roughly
every 0.87s** **[measured]**; settled runs median 3f, moving runs median 6f
**[measured]**. It is almost never at rest: the "holds" are micro-settles,
and only hero compositions rest (max ~1.2s). Budget accretion as a high-C0.5
device — at pacing 1–2 the model reads as sludge.

---

## 3 · GROWING LINE

One line, anchored at its start, extending as the sentence completes.
Position stable; content grows. Childline carries a four-minute film on it.

- Left-anchored (or start-anchored for RTL), vertically centred, in a large
  empty field. The anchor **does not** re-centre as the line grows — optical
  re-centring on every word is the tell that kills it **[observed]**.
- The A12 hold counts from the point the line is **complete**, not from the
  first fragment — the viewer reads the finished sentence.
- **Emotional register drives type register** (A17, layout side): quiet copy
  sits small, low-contrast, in maximum negative space; emotional peaks
  switch to large display type. Two registers, switched on story beats, not
  on a timer **[observed]**.
- Ground-colour flip (Childline alternates a cream and a near-black
  aubergine **[observed]**) is the scene-change device — the model needs no
  camera at all.

---

## 4 · WORLD-SPACE TYPE

Type is a static object standing in the 3D scene at architectural scale.
**The reveal IS the parallax** — nothing animates. Camera grammar is
klik-cam's; what this file owns is the integration checklist:

- **Occlusion is the tell that sells it.** Scene geometry must pass *in front
  of* the type — Panic Room runs buildings across the letterforms
  **[observed]**. Type that never occludes reads as an overlay no matter how
  good the track is.
- **Grade-match, never pure white.** The type takes the plate's white point
  (a dirty, desaturated white against that sky) **[observed]**.
- **Atmospheric haze with distance** — far type sits back in the same fog
  curve as the far buildings.
- **DOF applies to type** — far names soften. Type exempt from the lens is
  type that isn't in the world (A5).

---

## 5 · ANNOTATION LAYER

A hairline vector overlay tracked to the plate that **measures and annotates**
the world rather than stating over it. Distinct from every other model: it is
not the message, it is a data layer about the message.

- **1px hairlines, light, low opacity** — it must never compete with the
  plate **[observed]**.
- **It counts and measures things that are actually there**: paving slabs
  numbered under a walking figure, the eight steps of a tie knot, arithmetic
  floating beside the character doing it **[observed]**. Annotation that
  annotates nothing is decoration.
- **Rectangles crop the plate into inset panel grids** — the overlay
  supplies a composition grid on top of the footage.
- Perspective-matched to surfaces; numbers pin to objects and track them.
- A fixed corner mark again holds the UI plane.

Expensive to author. Treat as a hero device (A14) — one piece, one system.

---

## Study — the canon (frame-verified 2026-08-06)

Seven references pulled and studied frame-by-frame; measurements above come
from these. This supersedes the inference-only study note in
`kinetic-type.md` for these titles.

| Piece | Model | What it proves |
|---|---|---|
| Honda "Keep Up" (W+K / ManvsMachine) | Fixed anchor | speed-read timing grammar; plate-feature anchoring |
| MK12 "Brazil Inspired" | Accretion | the armature, the hinge, colour disambiguation, the ~0.87s composition cycle |
| Oxfam Ebola (Fred & Eric) | Accretion | the demotion ladder — 90° rotate-to-margin |
| Childline "First Step" (BUCK / YCN) | Growing line | register switching; ground-flip as scene change |
| Picturemill "Panic Room" | World-space | occlusion, grade-match, haze, DOF |
| MK12 "Stranger Than Fiction" | Annotation | the hairline data layer |
| Ginetta "We simplify" | — | fragments→word assembly with per-fragment colour converging to mono; a worked example of A17 (the reveal enacts the word) |

Vimeo blocks automated extraction — YouTube mirrors and direct MP4s were
used, consistent with the method's "local files primary" note.
