# Taste: the design loop for work we author

Match has a target to diff against, so Step 4 can measure it: same boxes, same
pixels, same motion. **Adapt, Brand, and any original build have no such
target.** Nothing in the fidelity report applies, and historically that meant
the build shipped on an adjective ("looks good"), which is precisely the
handover the report exists to replace.

This file is the loop for those builds. It has two halves, and the split is the
whole point: what can be measured is measured, and what cannot is sent to
someone who did not write the page.

---

**Which taste skill?** `design-taste-frontend` is the hub, and `design-stack`
decides what else loads beside it. That matters here because several installed
packs claim the same job and two of them contradict the hub outright. A build
that loads `gpt-taste` alongside it is built to two motion doctrines. Route
first, then apply the precedence below.

## 1. Where the taste rules and the measured reference meet

An Adapt build carries a reference's *system*. It does not carry everything:
the reference does not dictate the copy, the CTA labels, the form states, the
sections it does not have. **Every gap gets filled with a default, and the
defaults are the problem.** A build can carry a reference's proportions
faithfully and still ship Fraunces, an AI-purple gradient and three equal
feature cards in the space between them.

So a taste skill governs the gaps. Precedence, in order:

1. **A measured value from the reference wins** wherever the reference has one.
   A captured `cubic-bezier(.22,1,.36,1)` @ .3s is not replaced by a house
   default spring, and an `8.3333vw`-against-1440 type scale is not replaced by
   `text-4xl md:text-6xl`. The measurement is the reason the capture happened.
2. **The taste rule wins wherever the reference is silent.** Type pairings,
   icon family, empty and error states, section rhythm the reference had no
   equivalent of, copy register: all house rules.
3. **A named technique recipe wins over inventing one from scratch**:
   `mengto-skills` (below) is the fallback for a mechanism the reference didn't
   have and the taste hub doesn't cover as a house rule either. It is a real
   step of the ladder, ranked below a measurement because it ships defaults,
   not evidence; a captured curve from an actual site still overrides it.
4. **The taste skill's hard bans win always, over the reference itself.** WCAG
   contrast on every CTA and form control, `prefers-reduced-motion`, a hero that
   fits its viewport, a nav on one line. Reference sites break these constantly.
   An Adapt build is the user's own site, shipped publicly under their name; a
   Match is a local study that is never published. That difference is what makes
   the bans non-negotiable here and inapplicable there.

### A named technique library for step 3: `mengto-skills`

`E:\New Claude\skills\mengto-skills\agent-skills\web-design\` (MIT-licensed,
© Meng To; carry the notice if this build or a distributable ever ships any
of its actual file content, per the license) is ~85 narrow, named skills:
tested techniques (`scroll-scrubbed-word-reveal`, `marquee-loop`,
`progressive-blur`, `css-alpha-masking`) and named aesthetic presets
(`dark-glass-clean-layout`, `tech-green-dark-mode-modern`). Read the specific
`SKILL.md` that names the mechanism you need, the same way this skill reads
its own `references/*.md`. It's a file, not a magic invocation.

**What it's for and what it isn't.** This is a recipe library, the opposite
discipline from the rest of swipefile: its defaults (e.g. hidden opacity
0.12–0.3, blur 4–10px, a 120–220%-of-viewport reveal span) are good,
production-hardened numbers meant to apply broadly, not a measurement from a
real site. Use it exactly where step 3 says: a build has no reference for
this mechanism at all. The moment a reference *does* cover it, its measured
number wins per step 1; a recipe never overrides a capture, only fills the
space one hasn't reached yet.

Two house rules worth importing directly from its
`build-awwwards-quality-sites` orchestrator skill, now standing rules here
too:

- **Every scroll/motion technique needs a stated teardown**, not just a
  forward behavior: kill `ScrollTrigger`/observers, remove listeners, restore
  any DOM a text-split reveal touched, dispose Three.js resources. Motion
  specs in this skill have historically detailed the entrance and skipped
  this; treat an undocumented teardown as an unfinished spec, same tier as an
  undocumented `prefers-reduced-motion` gap.
- **No logo-wall theater and no invented partnerships stated as fact.** A
  fictional company name in a partners row or marquee (per
  `references/adaptation.md`'s content rules) must read as clearly
  demonstrative (a labeled demo, a "such as" framing, or house-styled
  wordmarks that don't mimic a real institution's actual mark), never
  presented with the same confidence as a real, disclosed integration.

**Match takes none of this.** Match copy is captured verbatim and rewriting it
to satisfy a house rule breaks the Step 4 diff outright. `design-gate.py --mode
match` exempts the copy checks for that reason and says so in its own output.

## 1a. Picking a font the build can actually keep

The taste hub's pairing pool (Geist, Satoshi, Cabinet Grotesk, GT America, Söhne
Breit, PP Neue Montreal, and the rotation of justified serifs) names *what looks
right*. It says nothing about *what this tool can actually fetch*, and picking
a family with no path to a real font file does not produce the wrong font, it
produces no font: the page falls back to system sans-serif, silently, because
CSS degrades instead of erroring. `design-gate.py` now fails a build on this
directly ("every declared font actually renders"). That check is the backstop,
not the plan. Resolve the font *before* it can fire:

1. **Google Fonts' catalog, self-hosted.** SIL Open Font License, always
   downloadable, no license question. Next.js: `next/font/google` fetches and
   self-hosts at build time automatically; this is not the same thing as a
   `<link>` to Google's CDN in production, which the taste hub bans for good
   reason (a live cross-origin request on every pageview, and the GDPR exposure
   that comes with it). Anything else: fetch the `.woff2` once into the repo and
   declare it with a local `@font-face` (same result, same rule, one extra step).
   Google Fonts today covers most of the pairing pool's *character* even where
   it doesn't have the exact name (a geometric grotesk in the Geist/Outfit
   register, an editorial serif in the Reckless/Canela register). Reach for the
   equivalent rather than defaulting to Inter because the first pick wasn't there.
2. **Fontshare**, for the handful of named picks Google Fonts doesn't carry:
   Satoshi, Cabinet Grotesk, General Sans, Switzer. Also free, also
   self-hostable, same fetch-and-declare step as above.
3. **A commercial family** (GT America, Söhne, PP Neue Montreal, Migra, Domaine
   Display, and most of the justified-serif rotation) only when the user hands
   over the actual licensed font files. Never fetch one from an unlicensed CDN
   and never guess at a `@font-face` `src` for a paid family. There is no
   legitimate URL for that request, and the build will either 404 (caught now)
   or, worse, pull from a piracy mirror.

A named reference changes nothing here for the *choice* of font (a measured
`font-family` from a capture still wins by the precedence above), but the
reference's font is subject to the same three tiers if it needs re-sourcing
for the rebuild rather than reading straight off its stylesheet.

## 2. Dials from measurement, not from vibes

A taste skill sets dials (variance / motion / density) from the brief. When the
brief names a reference (a URL, or an entry by name from `library/INDEX.md`),
those dials have measured values available and should not be guessed:

| Dial | Read it off |
|---|---|
| `MOTION_INTENSITY` | the entry's motion signature: animation count, duration ladder, travel distance. A page whose reveals travel 5px over .3s is not a 9. |
| `VISUAL_DENSITY` | measured section padding and content-per-viewport from the capture. |
| `DESIGN_VARIANCE` | the layout-family census across sections: how many distinct structures the reference actually uses. |

A named reference resolves through the library with no capture at all, subject
to the `Motion fidelity:` rule in SKILL.md: **below `spec` the entry cannot
carry motion**, so either re-capture it (Step 1 + Step 2, motion only) or say in
one line, up front, that the build ships without it.

The failure this replaces: a design read that says *"leaning toward a
Linear-style minimalist language"* and then builds from a recollection of
Linear. That is the same failure Step 1 exists to prevent, arriving through the
brief instead of through a URL.

## 3. The loop

```
build  →  design-gate.py  →  fix FAILs  →  re-gate  →  fresh-eyes critique  →  fix  →  report
```

Two rounds usually converges. Stop when the gate is clean and the critique has
nothing structural left, not when the page looks fine to you, which is the
judgement the next section exists to route around.

### Gate A: mechanical

```bash
python3 design-gate.py http://127.0.0.1:8791/ --mode adapt --src ../src --out design.json
```

It drives the same headless-Chrome instrument as every other measurement here
(`cdp-run.py`), at 1440 and 390 by default, and returns pass / FAIL / WARN /
UNVERIFIED per check. It measures what a self-review reliably gets wrong:
composited background colours behind translucent surfaces, real contrast ratios,
button labels that wrap, the eyebrow census against its own budget, painted vs
merely-declared font families, the light/dark sequence across sections, the
radius and accent censuses, and the source-level rules the rendered page cannot
show (`h-screen`, scroll listeners, icon family).

Three properties it inherits from the gates already in this folder:

- **UNVERIFIED is never a pass.** No `--src` supplied means the source rules
  were not checked, and the row says so rather than going quiet.
- **Warnings do not block.** Checks whose measurement is a heuristic (the hero
  visual, duplicate CTA intent, a single deliberate theme switch) report and
  let you decide. Say what you decided. A gate that fires on a legitimate build
  is a gate that gets ignored, and then the failures go unread too.
- **A passing row never carries a violation in its detail.** Enforced by a test,
  because the first version of this gate printed `ok — no prefers-reduced-motion
  rule anywhere in the page CSS`.

Feed the JSON into the report so the design gate sits beside the fidelity ones:

```bash
python3 report.py --site mysite.com --mode adapt --path rebuild \
    --design design.json --motion motion.json --copy copy.json --measured measurements.json
```

### Gate B: fresh eyes

**The half the gate cannot see, and must not pretend to.** Nothing mechanical
can tell you whether the copy reads like an LLM trying to sound thoughtful,
whether each animation is motivated, whether the composition is derivative, or
whether the whole thing reads as templated. Those are the failures that actually
make a page feel like AI output.

They are also the failures the author is worst placed to catch. Self-grading in
the same context is the weakest form of review: the model defends what it just
wrote, and every rule it followed feels like evidence that the result is good.

So this half goes to a **subagent that never watched the build happen**. Give it
only:

- the rendered screenshots at 1440 and 390,
- the rendered text (`design.json` carries it, or take it from the page),
- the brief in one line: **for a build with a `BRIEF.md`, this is the field 0
  thesis specifically** (`design-intake`'s ownable-idea sentence), not a
  generic one-line summary of the site. A generic brief lets a critique
  agree the page executes competently and stop there; the thesis is what
  lets it check whether the page has an idea at all.
- and nothing else: no reasoning, no rationale, no "here's why I chose this".

Ask for a scored critique against the taste skill's judgement rules (visual
hierarchy, copy quality, motion motivation, whether it looks templated, what a
skeptical designer would say first), **and, when a thesis was supplied, one
more question asked directly: does every section on the page serve that
thesis, and name any that don't.** Three rounds of this critique on the same
build once found "reads as templated" three separate times, each in a
different place, because nothing was checking the actual cause: the
mechanical gate can't see it (a generic section built well still passes every
contrast/copy/font check) and a critique with no thesis to check against can
only re-describe the symptom, not name it. The `critique` skill covers the
first half of this if it is installed; without it, the prompt is the ask
above plus "name the three things you would change first, in priority order."

The rationale-withholding matters. Supplying the reasoning is how you get a
reviewer that agrees with the reasoning instead of looking at the page.

**Required step, not optional: before acting on or reporting any specific,
surprising finding from the critique, check it against a control.** This
session had two confirmed cases of a fresh-eyes critique making a wrong or
overstated visual claim: calling a colour-fringing artifact present
identically in an untouched file's screenshot a "baked-in chromatic-aberration
glitch" on the file that had actually just been edited (the capture-instrument
bullet below has the full case), and describing a section that had been fully
rebuilt with no cards at all as "still reads as a generic three-card bento."
Both were caught the same way: by checking the specific claim against a
control (an unrelated screenshot from the same round, or the component's
actual source) rather than accepting or dismissing it on faith. The critique
is valuable precisely because it never watched the build happen; that same
distance means it has no memory of what changed and no way to tell stale from
current. Treat a specific, surprising claim as a hypothesis to check, not a
verdict to relay.

## 4. What neither gate covers

Say these out loud rather than letting the pass imply them:

- **Whether the design is right for the brief.** Both gates check execution. A
  beautifully executed page for the wrong audience passes everything here.
- **Content truth.** Fake-precise numbers, invented claims, wrong product facts.
  `copy-gate.py` catches AI-writing tells and the SEO floor; neither gate knows
  what is true.
- **Real-device rendering.** Two viewports in headless Chrome is not a device
  matrix. This library has twice measured a browser pane disagreeing with CDP
  about the same page; the instrument is not the last word on what a person
  sees.
- **The Browser pane cannot verify WebGL/canvas rendering in this
  environment: hard rule, not a preference.** Confirmed independently more
  than four times this session, across different agents plus the operator
  directly: the Browser pane's tab never composites a frame here.
  `document.hidden` stays `true` permanently, `requestAnimationFrame` never
  fires (confirmed by counting callbacks over several seconds: zero), and
  `computer{action:"screenshot"}` against a page with a WebGL canvas returns
  "the Browser pane is not displayed, so the page is not compositing frames."
  `capture.py`, real headless Playwright, captured this exact kind of
  content (a live WaterScene shader, hover-adjacent card treatments)
  repeatedly and correctly in the same session. So: for any WebGL/canvas
  claim, use `capture.py` and actually open or zoom into the resulting PNG.
  Do not attempt or trust a Browser-pane check for it, and do not write
  "confirmed the ripple works" because a ref-chain didn't throw. A round this
  session did exactly that; not throwing is not the same claim as having seen
  a rendered frame.
- **`capture.py`'s own screenshots can lie about text rendering.** Confirmed
  case: light text on a dark background shows a red/cyan fringe at glyph edges
  in `capture.py`'s PNG output, present identically on untouched files across
  two separate capture runs, so it is subpixel color-fringing from this
  Chromium build's text rasterization at screenshot scale, not a CSS effect on
  the page. A fresh-eyes critique flagged it as a baked-in "chromatic
  aberration glitch" on one headline and was wrong; the same fringe was
  sitting on a plain checklist line in an untouched file one screenshot
  earlier. Before spending a build round "fixing" a color-fringe finding,
  zoom into the cited crop on a file the current round did not touch; if the
  fringe is there too, it is the capture instrument, not the build.
- **"Verified" needs to say which kind it means.** This file already tags
  motion fidelity `spec` / `partial` / `signature-only` / `none` so a build
  knows exactly what it inherited from a reference; visual claims need the
  same discipline, because this session "verified" silently meant two
  different things and both shipped as "done." Tag it: **visually
  confirmed**: an actual screenshot or rendered frame was looked at, and the
  report says what was seen in it; **structurally verified only**: `tsc`
  passed, `getComputedStyle` returned the expected value, or nothing threw,
  with no rendered pixel involved. A hard CSS seam and low-contrast text both
  shipped as "done" more than once this session on reports that meant only
  the second and wrote the first. Use the tags for any claim about how
  something looks, not only whether it compiles.
- **Anything at a viewport you did not pass.** The gate measures where it is
  pointed. `--width` is repeatable.

And the standing rule from SKILL.md applies to the number this loop produces:
**say "reported", not "verified", while any check is UNVERIFIED.**
