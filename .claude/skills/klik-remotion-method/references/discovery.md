# Stage 1 — Discovery

Goal: one approved `<project>_animation_SSOT.md` a context-blind agent could
build from. The template (`templates/SSOT.template.md`) defines the sections
and carries inline guidance — this file is how to *run the interview*.

## Setup (before question 1)

1. Create the planning folder (user-assigned, else `klik/`), copy in the SSOT
   template named `<project>_animation_SSOT.md`, create `PROGRESS.md` from its
   template. Say you did.
2. Warn now: 30s+ videos WILL hit session limits a few times; artifacts on
   disk make resume lossless.
3. If the user's opening prompt already answered things, fill those sections
   first, mark them ✅ only if nothing needs confirming, then start at the
   first ⬜.

## Conduct

- **The sequence is law.** Ask in SSOT order 1→8. Early answers get recorded
  in their section; then return to where you left off and say so ("Logged your
  track for §7 — back to the brand guide").
- **One section per message batch.** All of a section's questions in one go,
  never one-question messages, never two sections at once.
- **Ask before generating — every section.** "Do you have X?" precedes making
  X, for every artifact class: script, refs, brand kit, assets, music, board.
- **Recommend, then defer.** Where you can infer (platform → format/length),
  present the inference as a recommendation and ALWAYS let the user overrule.
  Record who decided.
- **Confirm the fork early.** Item 1's dialogue-vs-pure-MG answer changes the
  questions in 6 and 7 — get it locked before moving past 1.
- Mark a section ✅ only when filled AND user-confirmed. Guesses stay
  `(inferred)` and go to Open Questions.

## Per-section notes (persona · the judgment the template can't carry)

**1 · Objective & spec — Producer.** Platform drives the recommendation
(IG/TikTok/FB → vertical, 20–30s cap · YouTube/web → landscape, longer), but
the user chooses. Convert duration to frames the moment fps is known. Vertical
platform → fill safe zones; don't skip the row with "n/a" unless the user
says so.

**2–3 · Style & mood — Producer.** Elicit, never propose. Push adjectives
toward named references ("premium like what — Apple keynote? Linear launch?").
Collect anti-references too; they constrain better than positives. **Every
supplied reference gets the extraction pass** — load
`references/reference-analysis.md`: analyze it into dial/motif terms, then
confirm takeaways per item before they enter the SSOT table. If the user
has no view at all, note it — the storyboard stage will render candidate
directions to react to (cheaper to pick from pixels than describe a vibe).

**4 · Brand guide — Producer.** Get hex codes, not color names. The deviation
allowances (font AND color) are the questions users never volunteer — ask
explicitly, they define your creative room. Logo: every variant they have, SVG
preferred; record the guide's forbidden treatments while you're there.

**5 · Assets — Asset Wrangler.** For software showcases this is the critical
section: live site to pull HTML from? Figma to export SVGs? Screenshots?
**View every asset before logging it** (klik-anim §A9) — resolution tier, and
clean of burned-in captions/watermarks/third-party logos. Anything needed but
absent: the fallback is HTML/CSS built with real frontend-design craft (ports
~1:1 into Remotion) — generative images only for texture, never for anything
that must re-render exactly. If the user has no asset direction, check the
ref library's asset-design entries first — decomposed recipes from their own
references seed the fallback designs (`references/reference-analysis.md`).

**6 · Copy — Copy Editor.** Recommend the user writes their own copy — say
why (their voice, their claims to stand behind). If AI-drafts, they approve
every word before it enters the SSOT; once in, §A8 makes it the only text
that can appear on screen.
- *Dialogue:* ask for the stitched a-roll; **offer auto-transcription**
  (`remotion-captions` skill) rather than asking them to hand-transcribe. No
  recording yet → take the script, mark timing provisional.
- *No dialogue:* explain the line-spacing convention once (single break =
  sequential in-scene, blank line = new scene with gap), parse their script,
  and **echo the numbered scene table back for confirmation** — pasted text is
  full of accidental breaks. Then ask which words carry emphasis; bold them
  inline, nowhere else.
- **Feasibility — run it NOW, before the gate.** Per line compute
  `max(0.70s, 0.25s + chars ÷ 17)` (klik-anim §A12) and sum against the §1
  duration. A script that needs 667f of hold against a 600f spec is knowable
  today; discovered after the build it costs full re-times. Over budget →
  cut lines or extend duration, with the user, here. Record the sum in §6.

**7 · Music — Music Supervisor.** First the timing role (set by the fork):
no dialogue → the track IS the timing authority; dialogue → background mood
only, animation follows speech. Then sourcing: who supplies it, licensed for
this use? (Real blocker for client work — flag, don't police.) Track in hand →
run `scripts/analyze-audio.py`: it emits the grid (BPM/downbeat) **and the
MUSIC MAP** — sections with energy tier, bass/mid/high lead, attack/sustain
character, and per-source rhythm patterns. **Stem mode** (`--stems auto`, the
default) uses demucs if installed to split vocals/drums/bass/guitar/piano
first — kick/snare/hats then come from the isolated drums, and vocals/guitar
stop reading as percussion. If demucs is missing the script degrades to
3-band mode and says so — mention `pip install demucs` to the user when the
piece leans on per-instrument sync. Paste both layers into §7. Sanity-check the
grid against hand-counted beats AND the map by ear (is the detected top-tier
section actually the drop? is the bar phase right — patterns can sit rotated
when the intro has no accent?). The map is what klik-anim §A16 and klik-cam
CAM-5 build motion character from — a wrong map ships wrong-feeling motion
everywhere. No track → internal pulse grid, and say plainly that landing the
track later means a re-time pass.

**8 · Dials & composition model — DP.** Two values, global-first (klik-cam C0
camera, klik-anim C0.5 pacing) — plus the **composition model** for any
copy-led passage (klik-anim `references/layout.md`: fixed anchor · accretion
artboard · growing line · world-space · annotation layer). The model is a
spec decision of the same kind as a dial, and it must be set here because it
changes the arithmetic downstream — accretion budgets holds in the reading
pocket and excludes demoted copy, world-space needs a 3D plate, annotation
needs something in frame worth annotating. Default is fixed anchor; anything
else is a deliberate, recorded choice.
Tie each recommendation to the mood answer from §3 ("premium calm → camera 2,
pacing 2"), let the user set the numbers. Local overrides exist but are not
part of discovery — note the mechanism, don't collect them yet.
Then the **energy arc** (klik-anim §A18) — the ONE intensity shape for the
whole piece. Music-driven: the §7 tier row IS the arc; confirm it reads as
the piece's dramaturgy (does the copy's climax sit on the musical peak?).
No music: offer the shapes (ramp · wave · cold open · plateau-drop), tie
the recommendation to §1's objective and §6's script structure, sketch it
per section in §8. This row is what QA later measures the render against
(`scripts/measure-motion.py`) — an unrecorded arc is unmeasurable.

## Gate — text

Present the filled SSOT compactly: the decisions, not the file. Surface every
`(inferred)` and open question in the same message. User approval flips
`Status: DRAFT → APPROVED` (you edit the line). Log the gate in PROGRESS.md.
Then → `references/storyboard.md`.

Right-size check: if this turned out to be a single-scene ask, say the method
is overkill and offer to work under klik-anim (+ klik-cam) alone.
