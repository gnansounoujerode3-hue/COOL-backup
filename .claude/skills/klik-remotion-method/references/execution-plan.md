# Stage 3 — Execution plan (persona: Tech Director)

Goal: an approved, then **frozen**, `<project>_execution_plan.md`. The
template (`templates/EXECUTION_PLAN.template.md`) defines the document; this
file is how to produce it. This stage is synthesis, not dialogue — run it in a
fresh context if practical, inheriting only the artifacts (SSOT, storyboard,
ref library, PROGRESS).

## Process

1. **Inputs must be APPROVED.** SSOT and storyboard both — a plan built on a
   DRAFT artifact is a plan built on sand; go finish the earlier gate instead.
2. **Fill the template verbatim.** Scene table from the board's `data-*`
   attributes + SSOT §6 copy (word-for-word, emphasis bold intact); transition
   specs exactly as their cards state them, with library IDs where cited;
   tokens from SSOT §4; beat grid from §7; dials + overrides from §8. The
   plan quotes the artifacts — it never paraphrases them.
3. **The context-blind test.** Before presenting: could an agent with zero
   chat history build this video from the plan + SSOT + board + craft skills alone?
   Anything that fails that test gets written in — never rely on what "we
   discussed".
4. **Propose the proof scene** — the most style-defining scene plus the
   signature transition, not the easiest one. The user confirms it at the
   gate, along with the checkpoint cadence (every N scenes / per act).
5. **Estimate tokens honestly.** Classify each scene — simple type scene
   ~15–25k · component/asset scene ~25–45k · heavy composite ~45–80k — sum,
   add ~30k setup/shared, present as a band, and say **"not including
   iterations"** in exactly those words.

## Gate — text, then frozen

Present compactly: build order, proof scene, checkpoint cadence, token band,
what happens next. Approval flips `Status: DRAFT → APPROVED` and the plan is
now **frozen** — build-time discoveries become dated amendments with the user,
never silent edits.

At approval, tell the user: **switch to Opus for the build** (planning ran on
Fable 5); quote the token band again; remind them 30s+ builds will likely hit
a session limit and that resume is lossless via the artifacts. Log the gate in
PROGRESS.md. Then → `references/build-qa.md`.

## Judgment

- Cite skill law numbers (§A.., C0, CAM-..); never restate mechanics (the builder loads the
  skills themselves).
- Assets: only SSOT §5 rows marked Clean ✅ may appear in the plan. A scene
  needing an unlogged asset → back to the user, or placeholder-then-swap
  written into the plan explicitly (exact required format in TODO.md).
- Missing information discovered here (a transition card left vague, a scene
  with no frame range) is a storyboard defect — fix it there first, don't
  compensate in the plan.
