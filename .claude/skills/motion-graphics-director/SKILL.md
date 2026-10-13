---
name: motion-graphics-director
description: The process layer for any motion graphics / video build - runs BEFORE tool-specific skills (hyperframes, remotion, hyperframes-blender-davinci) and decides how much of the real production pipeline a given piece actually needs. Use at the START of any "make a video" request, before writing a single line of composition code. Encodes the industry-standard stage model (brief -> concept -> storyboard -> style frame -> animatic -> production -> review -> delivery), adapted to agent speed, and the specific failure this exists to prevent: building full-detail, fully-polished code straight from a one-line brief, discovering the direction was wrong only after a full render, and having to redo it from scratch.
---

# Motion graphics director - the process, not the technique

`motion-design-skill` governs how to animate one element. `hyperframes-animation`'s
blueprints govern what a proven shot looks like. Neither governs the *order of
operations* for a whole project - and skipping that order is what produced a build
that passed every technical check and still needed a from-scratch rebuild once a human
actually looked at it (`hyperframes-systo-stats`, first attempt: four visually identical
scenes, a decorative field with no reason to be there, zero variation in weight or
pacing - "kinda bad," correctly).

This skill is that missing order of operations.

## The real industry shape, and where it lives already

Researched from two independent sources - a working agency's documented process and a
motion design educator's project guide - and they converge on the same stages:

**brief → concept/treatment → storyboard → style frames → animatic → production →
sound → review → delivery**, with three approval gates: after the treatment, after the
storyboard ("the last stage where significant changes don't create major delays" - the
single most valuable, cheapest-to-run gate), and at final delivery.

**HyperFrames' own vendored workflows already implement most of this**, `Step 0 brief
→ Step 2 design system (frame.md) → Step 3 storyboard + review gate → Step 4 visual
design → Step 5 build → Step 6 finalize + review pause` is the same shape as the
research above, stage for stage. Every HyperFrames build this session bypassed Steps
2-4 in favor of direct authoring, for real reasons (reusing already-verified brand
tokens, avoiding sub-agent drift across a continuing series) - but that was a
**judgment call that should have been stated and substituted with something**, not a
silent default that skipped the gates with nothing standing in for them. This skill is
what should have stood in.

## The five gates, adapted to agent speed

Real studios take days between these because a human has to look and respond. An agent
doesn't need days - it needs to actually **stop and do the gate's job**, not skip it
because nothing is externally forcing a pause. Each gate below is minutes of work, not
days, but it is real work, done *before* the next stage, not folded into it.

### Gate 1 - Concept statement (replaces "treatment")

One paragraph, written before any code: what is the ONE dominant idea, what should the
viewer feel, what carries the argument. Per `motion-design-skill`'s Three Pillars -
Emotional Intent, Visual Narrative, Motion Craft - answer these explicitly, in words,
before answering them in pixels. If the brief doesn't obviously imply one idea, name 2-3
candidate directions and pick one with a stated reason - don't build the first idea that
comes to mind and call it the concept.

### Gate 2 - Shot list (replaces "storyboard")

Plain text, one line per beat: what's on screen, what moves, roughly how long, what
carries the eye to the next beat. Not a drawing - a sentence per scene is enough. This
is the cheapest possible check and the one most worth never skipping: **read the shot
list back and ask "does every beat need to look different from its neighbors, and does
it?"** The stat-video failure was visible in a shot list before a single line of CSS -
"5 scenes, identical layout, identical motion trick, identical color, no camera, no
transition" reads as a warning even as a sentence.

### Gate 3 - Style-frame check (replaces "style frames")

Before animating anything, render ONE static frame - the busiest beat, or frame 0 - and
look at it as a still image, not mid-motion. Layout, type scale, color, what's
physically present in the shot. Catch a wrong static composition before spending effort
animating it. (`npx hyperframes snapshot --at <one timestamp>` or a Remotion `still` -
already available, just needs to run *before* the timeline is built, not only after.)

### Gate 4 - Rough timing pass (replaces "animatic")

Build the *structure* first - beats, cuts, rough durations - with no polish: no glow
blooms, no fine-tuned easing, no color-safe corrections yet. Confirm the pacing and
rhythm read right at this rough stage. Only then add the detail work. Building full
polish in the same pass as the structure means a wrong structure throws away finished
polish work along with it - which is exactly what the from-scratch rebuild cost.

### Gate 5 - Self-critique before declaring done (replaces "final review")

Before running the tool-level checks (`hyperframes-render-discipline`'s duration/
contrast/hard-kill items - a different, later gate), ask of the whole piece:

- Does every element on screen earn its place, or is something there because it was
  available rather than because this shot needs it? (the exact question that produced
  the field-removal correction)
- Does visual weight match actual significance - is the most important beat the most
  prominent, or is everything given identical treatment?
- Are transitions between beats designed, or are they accidental hard cuts?
- Is there one dominant motif, or is the piece doing several unrelated things at once?

Answer these honestly against the actual build, not against what was intended. If any
answer is uncomfortable, that is the gate working.

## When to run the full formal pipeline instead

This skill's five gates are the fast, always-worth-it minimum. Some pieces genuinely
need HyperFrames' full Step 0-6 pipeline instead - longer narrative pieces (60-90s+),
anything with real narration requiring script-to-voiceover sync, or a first piece for a
new brand with no already-verified tokens to reuse. Use the full pipeline there; use
these five gates for everything else, including fast iterative work on an established
series. State which one is being used and why - the choice itself is Gate 1's job.

## Where this hands off

Once Gates 1-2 produce a concept and shot list: pick the tool (`/hyperframes`,
`/remotion-create`, or the full formal HyperFrames pipeline per the section above).
Gates 3-4 run during that tool's own build loop. Gate 5 runs before
`hyperframes-render-discipline`'s technical checks and before delivery.

Related: [[hyperframes-render-discipline]] (technical verification, after this skill's
Gate 5) · motion-design-skill/director (single-element motion decisions, a different
layer entirely from project-level process).
