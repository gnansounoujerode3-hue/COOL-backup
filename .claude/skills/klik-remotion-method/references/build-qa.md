# Stages 4–5 — Build & QA

Two personas, two contexts, on purpose: the **Animator** builds; **QA judges
in a fresh context that did not author the code** — an author reviewing its
own work rubber-stamps.

## Stage 4 — Build (persona: Animator, on Opus)

You inherit ONLY: the execution plan + SSOT + storyboard/boards + ref library
+ klik-anim (+ klik-cam if the camera dial > 1) + PROGRESS.md. Read them in
that order. The plan's §4 build order is the law of this stage:

1. **Setup + foundations** per plan §1–2 (scaffold if needed, pinned
   versions, the plan's §1 file layout, tokens verbatim). `npm run dev` and tell the
   user Studio's URL — they can watch scenes land live. Lint gates every step.
   **The timing contract comes first:** before any scene, write `timeline.ts`
   (+ a `copyTiming.ts` mirror) with every line's legible window computed from
   klik-anim §A12's reading law, device assignments per scene (§A14 ledger),
   and a lint check that FAILS on any violated window. Scenes are then written
   to satisfy the contract — cue-level timing never lives only in scene code.
2. **PROOF GATE — hard stop.** The agreed proof scene + signature transition,
   rendered `--scale=0.5`, §A9 look-pass (render → look → list defects → fix →
   re-render until the list is empty), then show the user. **Nothing else gets
   built until they approve.** Style misses here are cheap; after mass
   production they cost the build.
3. **Scene by scene** in plan order. Per scene: build → lint → cheap render of
   its range → §A9 look-pass → check against its board card (layout, type
   scale, palette — deviations are defects) → mark the plan row ✅ → log in
   PROGRESS.md. Show the user at the agreed checkpoint cadence.
4. **Friction rules:** missing asset → placeholder-then-swap (same component
   boundary and dimensions, so the real asset drops in cleanly), logged in
   TODO.md with the exact required format — never stall. Plan wrong or vague →
   STOP, amend with the user (dated), continue. Copy is SSOT §6 verbatim
   (§A8) — a word the script lacks does not appear, however good it looks.
   Library-cited transitions (L-IDs) reproduce the catalogued mechanics, not
   your memory of them.
5. **Edits must land.** Every scripted string-replace carries a post-condition
   check scoped to the exact target — `replace` no-ops silently on a miss and
   stale code ships while PROGRESS says fixed (a real shipped failure).
6. **Rebuilds are visibly new.** "Make a new version" = a NEW composition ID,
   registered beside the old (V1/V2) until the user culls one — never an
   in-place rewrite under the same ID, and never delete a superseded sequence
   that isn't in git. Renders are not source.

## Stage 5 — QA (persona: QA, fresh context)

Open a clean window/session. Inputs: SSOT, storyboard, execution plan, ref
library, klik-anim + klik-cam, and the rendered output. You judge; you don't
rebuild.

1. **Full-timeline watch-down** at `--scale=0.5` — flow defects no per-scene
   check catches: tempo sameness, transition monotony, focal fights at
   boundaries, drift.
2. **Arithmetic pass — a watch-down cannot catch durations.** Recompute every
   line's legible window against klik-anim §A12's reading law from the actual
   frame numbers; audit the §A14 device ledger (no unvaried repeats) and every
   §A15 boundary (no exit → gap → entrance). Both checks always: only looking
   catches smudges and strobes; only arithmetic catches a 7-frame hold.
   **Then measure the arc:** run `scripts/measure-motion.py render.mp4
   [--map <music-map.json>]` — it frame-diffs the render into the piece's
   ACTUAL energy curve and reports event/rest contrast, the floor-relative
   rest ratio vs §A6's 40–60% band, and (with the map) per-bar correlation
   against SSOT §8's recorded arc with per-tier means. Non-monotonic tier
   means or a flat curve on a designed piece = the render is not following
   its arc (§A18) — a defect with a frame-number address, not a vibe.
3. **klik-anim Part D pre-flight — every item**, including 16 (every on-screen
   word traces to SSOT §6), 17 (every asset was viewed and logged clean), 18
   (the §A9 look-pass ran and its defect list is empty), 27–29 (reading holds,
   device ledger, boundary continuity). **Plus klik-cam's CAM checklist** when
   the camera dial > 1.
4. **Board match** — each scene against its approved card. Divergence is a
   defect unless a dated amendment covers it.
5. **Dial audit** — camera C0 (klik-cam) and pacing C0.5 (klik-anim) as set in
   SSOT §8, local overrides only where recorded.
6. **The distraction test.** After the watch-down, write the copy from
   memory before re-reading the SSOT. If you remember the animation but not
   the words, motion is too dominant — klik-anim's restraint law failed even
   if every mechanical check passes. Judge per scene, not just overall.
7. **Speed & robustness probes** (cheap, run on the half-res render):
   re-watch at 0.75× and 0.5× playback — pacing defects (rushed holds,
   dead spots, tempo sameness) surface at reduced speed that real-time
   watching hides. If the deliverable targets a platform honoring
   `prefers-reduced-motion`, confirm with the user what the fallback is
   (static poster / fades-only variant) — an unanswered accessibility
   question is an open TODO, not a silent skip.
8. **Deliverable render** at full res per SSOT §1 hard numbers (correct
   resolution/fps/codec/handoff — mp4 vs chroma slice vs ProRes alpha).
9. **Close out:** deliver render + pre-flight + arithmetic results + open TODO
   list. Nothing silently dropped. A run is correct only if: every legible
   window passes by computation · feasibility was computed at discovery · the
   device ledger shows no unvaried repeats · every boundary continues ·
   scripted edits carried post-condition checks · artifacts were reconciled on
   resume · superseded sequences stayed visible until the user culled them.
   Mark PROGRESS.md `DELIVERED` when the user accepts.

## Change requests (any time after delivery or mid-build)

Re-enter by scope, artifacts first, code second — they must stay truthful:
copy → SSOT §6, then the scene · style → SSOT/tokens, then code · one scene →
its plan row · timing/structure → storyboard, then plan. Check PROGRESS.md
before starting any new feature; log it after.
