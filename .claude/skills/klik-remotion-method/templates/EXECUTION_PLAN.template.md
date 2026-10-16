# <project_name> — Execution Plan

Status: DRAFT
<!-- The build contract. Written from the approved SSOT + storyboard; approved
     once, then FROZEN — the build executes this, it does not reinterpret it.
     If the build discovers this plan is wrong, STOP, amend with the user, then
     continue. Amendments are dated entries at the bottom, never silent edits. -->

## For the build agent (read first)

You are expected to start with **no context beyond the artifacts**. Read, in
order: `<project>_animation_SSOT.md` → `<project>_storyboard.html` (and
`boards/` stills) → this plan. Then obey:

1. **klik-anim governs every frame; klik-cam governs the camera.** Craft laws
   Part A — incl. §A8 (only the SSOT's words on screen), §A9 (render → look →
   list defects → fix before showing anything), §A12 (per-line reading holds),
   §A14 (device ledger — no unvaried repeats), §A15 (boundaries continue).
   Dials: camera C0 = <N> (klik-cam), pacing C0.5 = <N> (klik-anim) (from
   SSOT §8, overrides listed there).
2. **Verbatim rule.** Copy, scene descriptions and transition specs below are
   carried over from the approved artifacts word-for-word. Do not improve,
   reinterpret, or add. Ambiguity → ask, don't invent.
3. **Recommend the user runs this phase on Opus** (planning happened on
   Fable 5). Estimated build spend: **~<N>k–<N>k tokens, NOT INCLUDING
   ITERATIONS** <!-- sum the per-scene classes: simple type scene ~15–25k ·
   component/asset scene ~25–45k · heavy composite scene ~45–80k, + ~30k
   setup/shared. State the total as a band, never a promise. -->
   For 30s+ videos the user WILL hit session limits — artifacts on disk make
   resume lossless (check PROGRESS.md on every restart).

## 1 · Setup (skip what already exists)

- [ ] Scaffold: `npx create-video@latest --yes --blank --no-tailwind <name>`
      (use the `remotion-create` skill) — or confirm existing project.
- [ ] Pin every `@remotion/*` package and `remotion` to the exact same version
      (upgrade together via `npx remotion upgrade`). Needed:
      <!-- e.g. @remotion/google-fonts, @remotion/motion-blur, @remotion/noise -->
- [ ] Lay down the standard file layout: `theme.ts` (tokens, verbatim from
      SSOT) · `fonts.ts` (loaded families) · `motion.ts` (EASE set, springs,
      beat grid) · `ui/Stage.tsx` (1920×1080 design space scaled to comp
      size — design in base space, never raw 4K px) · `transitions/<Motif>.tsx`
      · `remotion.config.ts`.
- [ ] `npm run dev` → tell the user Remotion Studio is at the printed URL —
      they can watch every scene live while you build.
- [ ] `npm run lint` passes on the empty scaffold before any scene work.

## 2 · Foundations (verbatim from SSOT)

- **`theme.ts`:** <!-- paste the full token block from SSOT §4 — hex-exact -->
- **`fonts.ts`:** <!-- families/weights from SSOT §4; self-hosted files via staticFile -->
- **`motion.ts`:** EASE set per klik-anim A1; duration constants biased per
  pacing dial C0.5 = <N>; beat grid from SSOT §7: <!-- BPM · firstBeatFrame · beat()/bar() constants, or internal pulse -->
- **Timing contract — before any scene:** `timeline.ts` + `copyTiming.ts`
  mirror: every line's legible window from klik-anim §A12 (SSOT §6 lines ×
  the reading law), device assignment per scene (§A14 ledger), **each scene's
  motion character from the music map** (SSOT §7: tier → density/pacing,
  attack → curve steepness, lead → weight — klik-anim §A16; camera per
  klik-cam CAM-5), and a lint check that FAILS on any violated window.
  Scenes satisfy the contract; cue timing never lives only in scene code.
- **Shared components:** <!-- from storyboard: the transition motif + anything used by ≥2 scenes. Build these FIRST. -->
- **Assets:** copy verified files (SSOT §5 log — only rows marked Clean ✅)
  into `public/`. An asset not in the log does not enter the project.

## 3 · Scene build table

<!-- One row per storyboard card, in timeline order. Copy/visual/transition
     columns are VERBATIM from the approved artifacts. Done = klik-anim A-laws
     hold, lint passes, cheap render viewed (§A9), matches the card.
     Components column doubles as the §A14 device ledger — no reveal or
     transition appears in two rows unvaried. -->
| # | Frames | Copy (exact) | Visual (from card) | Transition out (exact) | Components | Status |
|---|---|---|---|---|---|---|
| 1 | 0–<n> | | | | | ⬜ |
| 2 | | | | | | ⬜ |

## 4 · Build order & gates

1. **Foundations + shared components** (§2). Lint gate.
2. **PROOF GATE — hard stop.** Build scene <N> <!-- the most style-defining
   scene, agreed at plan approval --> + one signature transition. Render at
   `--scale=0.5`, run the §A9 look-pass, then show the user. **Do not build
   further scenes until they approve.** A miss here costs one scene; the same
   miss after mass production costs the build.
3. **Remaining scenes**, timeline order, one row at a time. Per scene: build →
   lint → cheap render of its frame range → §A9 look-pass → mark row ✅ in §3
   → log in PROGRESS.md. Show the user at natural checkpoints
   <!-- e.g. every 3 scenes, or per act — set at plan approval -->.
4. **Missing asset mid-build:** placeholder-then-swap (same component boundary
   and dimensions as the real asset), logged in TODO.md with the exact
   required format. Never stall the timeline.

## 5 · QA handoff (fresh context — never the build agent)

QA runs in a **clean window** that did not author the code: it reads the SSOT,
the storyboard, this plan, and the rendered output — then judges.

- [ ] Full-timeline watch-down at `--scale=0.5` (flow, tempo sameness, focal
      fights, drift).
- [ ] Arithmetic pass: recompute every line's legible window (§A12) from the
      ACTUAL frame numbers; audit the §A14 device ledger and every §A15
      boundary. A watch-down cannot catch durations — both checks, always.
- [ ] klik-anim Part D pre-flight — every item, incl. 16 (copy traces to SSOT
      §6), 17 (assets verified clean), 18 (the §A9 look-pass happened and its
      defect list is empty), 27–29 (holds, ledger, boundaries) — plus
      klik-cam's CAM checklist when the camera dial > 1.
- [ ] Board match: each scene against its approved card — layout, type scale,
      palette. Deviations are defects unless an amendment covers them.
- [ ] Full-res render per SSOT §1 hard numbers. Deliver with the pre-flight
      result + open TODO list.
- **Change requests re-enter by scope:** copy → SSOT §6 then that scene ·
  style → SSOT/style tokens first, then code · single scene → §3 row ·
  timing → storyboard, then plan. Artifacts stay truthful; never patch code
  against what the documents say.

## Amendments
<!-- date — what changed — why — user-approved -->
