# Stage 2 — Visual storyboard (persona: Storyboard Artist)

Goal: an approved `<project>_storyboard.html` where the user approved **real
rendered stills** — pixels, not prose. The template
(`templates/storyboard.template.html`) carries the file mechanics in its
header comment; this file is how to run the stage.

## Setup

- Copy the template → `klik/<project>_storyboard.html`; stills and previews go
  in `klik/boards/`.
- **Scaffold the Remotion project NOW, in the background**, if none exists
  (`remotion-create` skill). Drafting continues while it installs — the
  approval pass needs the real project, and the install takes minutes you
  shouldn't spend blocking.

## Process

**1 · Cards from the SSOT.** One scene card per SSOT §6 row — including
visual-only scenes — one transition card in every gap. Copy verbatim, emphasis
bold preserved. If a scene isn't in the SSOT, it doesn't get a card; if the
board needs a scene the SSOT lacks, amend the SSOT first (with the user).
**Time the cards against the music map** (SSOT §7): scene boundaries want to
land on section boundaries, the biggest scene on the highest-tier section —
and each card notes its section's character (tier · lead · attack), which the
plan later turns into motion directives (klik-anim §A16 / klik-cam CAM-5).

**2 · Draft pass — HTML mockups, cheap iteration.** Build each card's visual
as an HTML/CSS mockup with real frontend craft, using the SSOT brand tokens.
Iterate here — this is the cheapest medium the look will ever be in. Ask for
the user's reference screenshots per card (refs strip).
*If discovery logged "no style direction":* open by mocking scene 1 in 2–3
candidate directions and let the user pick — reacting to pixels beats
describing a vibe. The pick gets one confirming sentence in the SSOT (§2).

**3 · Transitions — elicit every gap.** For each boundary ask how it should
move: motif, duration (frames), speed/curve (against pacing dial C0.5),
camera involvement (against C0). **Check the reference library first** — if
`<project>_ref_library.md` holds matching transition/camera-move entries,
offer them by ID as candidates before inventing new ones. Offer real rendered
previews **only after saying they cost extra tokens**; default is the text
spec on the card. Record the agreed spec verbatim (with any L-ID) — the
execution plan carries it word-for-word.

**4 · Approval pass — real stills.** When drafts are stable: pose each card as
a real component in the project (these comps ARE the build's starting point),
render `npx remotion still` per card into `boards/`, run the §A9 loop on every
still — look, list defects, fix, re-render — then swap the stills into the
html, replacing the mockups.

**5 · Gate — PIXELS.** The user reviews the board with real stills and every
transition card filled. Approval flips the board's status; log it in
PROGRESS.md. Then → `references/execution-plan.md`.

## Judgment

- **One focal idea per card** (density per SSOT). A card that needs two focal
  elements is usually two scenes — split it and flag the SSOT amendment.
- **Iterate in the cheapest medium that can settle the question.** Layout and
  type questions die in HTML; only stable cards earn a still; only approved
  boards earn motion.
- **Right-size the board.** A 15s piece may be 3–4 cards; don't pad. Long
  pieces: board in acts, gate per act if the user prefers.
- **Refs are references.** A user screenshot on a card steers the mockup; it
  is never composited into the deliverable (Remotion output only). Card refs
  get the lighter per-card pass in `references/reference-analysis.md` — a card
  ref never silently changes the global SSOT profile.
- Camera/pacing overrides surfacing here ("this one slower") are recorded in
  SSOT §8 Local overrides — never left as verbal agreements.
