---
name: swipefile
description: Swipefile. Capture a reference website's design system (layout, tokens, typography, interaction states, animations), verify it by measurement, and remember it in a growing local library. Five jobs. Match (clone a site faithfully, full crawl with working nav), Adapt (apply its system to your own content or re-skin your existing site), Audit (explain what animations/fonts/design a site uses), Transfer (apply one extracted animation or element to a section of your site), Brand (extract a brand kit, or generate one from the library). Use whenever the user wants to copy, clone, match, borrow, or take inspiration from another site's design or motion; asks for a landing page or mockup "like [some site]"; wants to extract CSS, design tokens, easing curves, animations, or a brand kit from a page; shares a URL and asks what makes its design work; wants a site's animations explained or recreated on their own pages; or is iterating on a build to match a visual reference. Also use when a rebuild is close but feels wrong and the user can't say why.
---

# Swipefile

*The swipe file that measures.* Great designers have always kept swipe files of
work worth learning from; this one captures the actual system: verified by
measurement, remembered in a library that compounds with every site it studies.

## First: which job is this?

Two different tasks hide behind the same request, and conflating them is the main
reason results disappoint.

**Match**: rebuild the reference as faithfully as possible. Recreating a page
the user owns, a design-to-code handoff, a rebuild on a new stack. Done when a
side-by-side diff has nothing left to fix.

**Adapt**: extract the reference's *system* (proportions, rhythm, motion
character, structural logic) and apply it to different content and a different
brand. Done when the result feels related to the reference but reads as its own
thing.

**Match is the default. A bare URL means Match.** "Clone this site", "copy this
page", or this skill invoked on a URL with nothing else said is a request for an
exact replication. Build it, don't ask.

Switch to Adapt only on a positive signal: the user supplies their own content,
copy, or brand; or they say inspiration / "in the style of" / "like X but for Y".
If they gave you their own content, it's Adapt. Don't ask. **Two URLs ("apply
reference.com's design to my site mysite.com") is Adapt in its two-URL form**;
see `references/adaptation.md`, which captures both sites (the reference for its
system, the user's for their content) and re-skins. If a request is genuinely
ambiguous *after* those tests, ask once, in one line, then proceed.

Ship a Match for an Adapt request and the user gets something they can't sensibly
use. Ship an Adapt for a Match request and you have wasted their time with a
rough sketch when they asked for the real thing, and that is the far more common
failure, because it is the one that feels safe.

Both modes share Steps 1-4 below. Adapt inserts one extra step before building;
see `references/adaptation.md`.

**Adapt also picks up a second rulebook, and the order between them is fixed.**
The reference does not dictate everything (not the copy, not the CTA labels,
not the states it has no equivalent of), and every gap it leaves gets filled
with a default. A build can carry a reference's proportions faithfully and still
ship the house AI aesthetic in the space between them. So: a **measured**
reference value wins wherever one exists; a taste rule wins wherever the
reference is silent; and the accessibility hard bans (contrast, reduced motion,
a hero that fits, a nav on one line) win over the reference itself, because an
Adapt ships publicly under the user's name and a Match never ships at all.
`references/taste.md` has the full order and the gate that enforces it.

**Adapt and Transfer digest the reference completely before building: same full
Step 1 capture as Match, section by section.** Not the gist and not a
recollection. A library entry is a partial substitute and only a scoped one: it
carries the proportional systems as systems, so those need no re-measuring, but
it carries motion at whatever depth its `Motion fidelity:` line declares. See
"Design from a named reference" for the rule, which governs. Anything the entry
does not hold gets measured, not remembered. If a mirror of the reference
already exists on disk, read it: that is ground truth, and building from memory
beside a byte-accurate copy is indefensible.

This is how both jobs fail, and it fails identically every time: the build gets
composed from a *summary* of the reference, so it inherits the vocabulary and
none of the character. The user says "this looks sloppy" or "it doesn't feel like
the reference", and they are right: the missing thing was never a token, so no
amount of later colour and spacing tuning recovers it.

Digesting completely means, before any code: every section's real geometry in px;
**every animation on the page** with its trigger, from/to values, duration,
easing, stagger and (for anything scroll-linked) its start and end offsets; the
full type census with frequencies; the interaction states; and the exact alpha
ramp. On a long page that is a lot of extraction and it parallelises well: one
pass per section, then merge into one spec. Then name the three things that carry
the page's character and confirm your build has all three. Details and the
ownership line that decides what may be re-derived are in
`references/adaptation.md`.

## Three scoped jobs: Audit, Transfer, Brand

Not every request wants a page built. These jobs reuse the same capture
machinery and are first-class uses of this skill, not degraded clones:

**Audit**: "what animations / fonts / design system does this site use?" The
deliverable *is* the extraction, written twice for two readers:

1. **Plain language**, for a human deciding whether they want it: "cards rise
   5px and settle over .3s with a hard-out curve, staggered 100ms left to
   right; the hero pins while three panels scroll over it." Name the feel, not
   just the mechanism.
2. **The implementable spec** (per `references/motion.md`): trigger, properties,
   duration, easing, stagger, scroll offsets, and the mechanism (with the
   library *confirmed by probing runtime globals*, never by grepping bundle
   comments, which routinely name-drop libraries the site doesn't run).

3. **What it costs at rest**, when the site animates. Measure idle CPU/GPU with
   the tab focused and nothing being touched, and count infinite animations
   (CSS `animation-iteration-count: infinite`, unpaused rAF loops, always-on
   canvases). This is a real audit dimension, not a footnote: one site sat at
   43-74% CPU with no input from ~31 infinite CSS animations, and a Cesium globe
   burned ~60% GPU with a parked camera and zero data layers. A reference whose
   look depends on permanent motion is a reference you are quoting a battery
   cost on, so say so before the client falls in love with it.

Run Step 1 capture + Step 2 motion spec, skip build and diff, and still write
the library entry. An audit feeds the library exactly like a clone does. If
the site is already in the library, the audit is a file read.

**Transfer**: "apply that hero animation to *my* hero section." A scoped
two-URL Adapt, and the bar is **near-exact**: same structure, same measured
geometry, same motion, with only the brand layer swapped. Do not generalise a
named element into a system: "the hero of X" is a request for that hero, not for
X's proportional logic. Capture the specific mechanism from the reference (not the
whole site), then **read the user's target code first** and translate the spec into
their existing stack: their animation library, their tokens, their reduced-
motion handling. Import the measured *values* (curve, duration, travel,
stagger), never a second animation library the repo doesn't already have; one
scroll owner per page stays law. Done means the motion runs live in the user's
page and a reduced-motion pass exists, verified, not assumed. The adaptation
feel-test applies at component scale: same character, their brand.

**Brand**: "pull the brand kit out of this site", and eventually "make me a
new one." Two halves, one available now and one that matures with the library:

**This job and the `brandkit` skill both answer to "brand kit", and they produce
different objects.** This one produces the measured *system* (palette with
usage frequency, type scale and ratio, spacing base unit, radius and shadow
language, motion character, logo treatment rules) as `BRAND-KIT.md` plus CSS
custom properties and JSON. `brandkit` produces the rendered *imagery*:
guideline boards, logo concepts, mockups, decks. When both are wanted, **this
runs first and `brandkit` renders from these tokens**; the other order invents
values the build then has to match. `design-stack` holds the full routing.

*Extraction (now).* From a capture, deliver a brand kit as a document plus
tokens: palette with semantic roles **and usage frequency** (a colour used 40
times is structural; twice is decoration), type system (families, roles, scale
ratio, casing conventions), spacing rhythm and its base unit, radius/shadow
language, motion character, and logo *treatment* rules (clear-space, sizing,
background behaviour), never the logo asset itself. Output: `BRAND-KIT.md` +
design tokens (CSS custom properties and JSON). An extracted kit is a
**reference document**: shipping it verbatim on another brand is the Match/Adapt
line applied to identity, so anything that goes on the user's own work is
re-derived per `references/adaptation.md`.

A kit that ships with copy (a sample page, a voice section, anything written)
is newly written copy and is therefore ours: load `humanizer` **before** writing
it, and clear `scripts/copy-gate.py` before showing it. Same rule for every Adapt
build, which ships a real page with real copy, real SEO and real structured data.
Match copy never goes through either; it is captured verbatim, and rewriting it
breaks the Step 4 diff. `references/copy.md` has the ownership line, the gate's
checks, and the GEO floor.

*Generation (matures with the library).* "Create a brand kit for my espresso
bar" pulls ratios, contrast structures, and motion characters from accumulated
library entries and re-derives every specific for the new subject, selecting
and **citing** which captured systems informed which choice, never averaging
entries into mush. At low N, say so plainly: a library of three carries three
opinions, not a style space. This is the seed of the future generation
companion; it lives here until it outgrows the folder.

Prompts that route here: "what makes this site feel so smooth", "extract the
scroll animations from X", "what easing does X use", "recreate X's hero
animation on my landing page", "make my cards animate like X's", "extract the
brand kit from X", "what are X's brand colours and fonts", "generate a brand
kit for my <subject> from what you've learned".

## Design from a named reference

Every library entry is **callable by name**: "build a website for my brand,
reference: **<the name in the index>**" needs no URL. Resolution:

1. Look the name up in `library/INDEX.md`'s *Call it* column: match
   case-insensitively against the name, the domain, or any alias listed in the
   entry. Found → run **Adapt** with the entry as the extraction: its ratios,
   contrast structure, and mechanisms are the captured system, already measured.
   Re-capture the live site only when the job needs something the entry flags as
   missing, not by reflex.

   **What an entry can and cannot replace.** It replaces measuring for the
   *proportional* systems, because those are stored as systems: type scale,
   layout, colour, spacing, interaction deltas. `8.3333vw against a 1440 design
   width` rebuilds exactly. It replaces measuring for **motion only when the
   entry's `Motion fidelity:` line reads `spec`**; anything below it does not.
   `partial` has real numbers but no per-animation mapping; `signature-only` has
   ranked curves and a character sentence, a *vocabulary* rather than a mapping;
   `none` has nothing. From any of those, no page can be animated: there is no
   target, no trigger, no from/to, no stagger, no scroll offset. Building anyway
   produces the exact failure this skill exists to prevent, and it is invisible
   in a still screenshot: correct type, correct colour, correct layout, and a
   dead page. So below `spec`, either **re-capture the motion** from the live
   site (Step 1 + Step 2, motion only: cheap, one pass) or say in one line, up
   front, that the build ships without it. Never quietly drop it.

   Read the fidelity off `INDEX.md` at Step 0, before planning; it is in the
   motion column, so choosing a donor and knowing whether it can carry motion is
   one lookup, not a file read per candidate.
2. Not found → say what the library *does* hold, reading the names straight off
   `library/INDEX.md`'s *Call it* column rather than from memory, and ask for a
   URL: a fresh capture both serves the job and adds the name for next time.
   On a blank library say that plainly; it is the documented first-run state.
3. Multiple names ("hero like <one entry>, cards like <another>") is a
   legitimate composition: take each named system for the scope it was named
   for, and say in the plan which entry governs which region.

**Select donors by mechanism quality, never by subject relevance.** A
reference's industry, audience, or content has zero bearing on whether its
*mechanisms* fit: an athlete's site can supply the scale system for a B2B
product, a studio's site the reveal feel for a storefront. When composing,
pick each slot's donor by which entry holds the best-measured system for that
job, and never exclude (or prefer) an entry because its subject resembles the
user's. Similarity of subject is not a design argument; quality of mechanism is.

Naming rule: **every new entry gets its callable name at write time**, the
short human name of the brand or site (aliases welcome), recorded in the
entry's header and the index column. An unnamed entry can't be ordered from.

The name is a lookup handle, not an identity to wear: everything in
`references/adaptation.md` still applies; the user gets the reference's
proportions, pacing, and motion character re-derived for their own brand, and
the feel-test's second question ("would anyone mistake it for the reference?")
must still come back **no**.

Prompts that route here: "reference: <name>", "use the <name> design", "make it
like the <name> one you captured", "in the style of <name> from your library".

## The fidelity bar for Match

**100% accurate replication is the target. Not "close", not "the design language",
not "the structure with placeholders in it."**

In Match mode the following are **defects**, not judgment calls, and each one on
its own means the build is not done:

- Placeholder, lorem, invented, or paraphrased text where the reference has real text.
- Substituted fonts, icons, logos, images, or video posters where the real asset
  could have been fetched.
- Coloured rectangles, gradients, or `hsl()` fills standing in for real imagery.
- Invented copy for a section whose real copy you did not capture.
- "Representative" content: three cards where the reference has eleven.

Every one of these changes text wrap, box height, and every position below it, so
the Step 4 diff can never converge. A placeholder does not just look wrong; it
makes the verification step meaningless, which is the whole point of the skill.

Fidelity is the default *because* the constraint sits on publication, not on how
accurate the local artifact is. See "Copying, and where the line is": a local
study rebuild uses the real text, the real fonts, and the real images. Degrading
the build is not a substitute for the publication rule and does not make anything
safer.

**When content genuinely cannot be captured** (an empty logged-out feed, an
auth-gated region, a lazy section that never mounts, an API that returns nothing),
that is a capture failure, and it gets **reported, not filled in**. Say which
region is missing and why, deliver everything that *was* capturable at full
fidelity, and ask whether to proceed. Silently substituting invented content turns
a known gap into an unknown one and quietly converts a Match into an Adapt.

**Match has two paths, and picking wrong caps your fidelity.** `curl` the page
first: if the raw HTML already contains the content (server-rendered), take the
**mirror path**: their markup, stylesheets, and assets fetched and rewritten to
local paths by script; see `references/mirror.md`. Mirrors measure 99%+ because
they have no transcription steps. Hand-rebuild (Steps 2–4) only what cannot be
mirrored: client-rendered pages, or single components lifted into another stack.
Text content is captured programmatically in either path; it is data already in
the DOM. Retyped or placeholder text in Match mode is a defect: it changes every
wrap and height below it, and the diff never converges.

**One page or the whole site? The whole site is the default.** A Match invoked
on a site (a bare domain, a homepage URL) is a request for a *navigable* copy:
clicking a nav item must land on a mirrored local page, not a dead `#`. A
single-page mirror with an inert menu reads as broken to the user even when that
page diffs at 99%. Mirror the crawl surface with `scripts/crawl.py` +
`scripts/build.py`, serve it with `scripts/serve.py` (see
`references/crawl.md`), rewriting internal links between crawled pages to their
local slugs. Single-page is the *exception*: right when
the user pointed at one specific page or component, and say so in the notes.

Scope the crawl from evidence, not appetite: read the sitemap, histogram URLs by
first path segment, and split the site into **design surface** (nav-reachable
marketing pages, service/product pages, the portfolio) and **bulk** (blog
articles, docs, tags, user-generated listings: hundreds of near-identical
templates with no new design information after the first). Crawl the design
surface by default; for bulk sections mirror one exemplar of each template,
quote the counts, and leave the rest as an explicit, one-command extension.
Depth is a storage decision as much as a fidelity one; say what a full crawl
would cost rather than silently skipping it. Auth-gated pages are out of scope,
detected by path and by 401/403-or-login-redirect. Never attempt credentials to
reach one.

## The constraint that shapes the workflow

You cannot see a live page, and fetching a URL returns stripped text: no
computed styles, no keyframes, no interaction states, no motion. Every good
outcome here depends on getting structured evidence out of a real browser first.

So: **consult → capture → spec → build → visually diff → iterate → record.**
Building from a URL and a description produces confident, wrong output. That
failure is what this skill exists to prevent.

## Step 0: Consult the library

`library/INDEX.md` holds the design system of every site captured so far, one
`<domain>.md` per site, plus a running list of cross-site patterns. **Read the
index before capturing.**

**First run / blank library:** the skill ships with the library empty. That is
normal, not broken. If `INDEX.md` is missing or has no entries, create the
scaffold (index header + empty table + empty "Cross-site patterns" section,
shaped per `library/TEMPLATE.md`) and proceed; this capture becomes entry #1.
Do not generalize from nothing: the cross-site patterns section only gains a
line once **two or more** entries support it, each cited by name. A library
earns its authority one measured capture at a time.

With entries present, the read costs one file and pays for itself three ways:

- **Same site again?** The entry has its tokens, breakpoints, motion curves and
  (most valuable) the gotchas that cost time last run. Re-verify rather than
  re-derive; sites change, but the structural notes rarely go stale.
- **Same stack or genre?** Entries record the stack (Polymer, WordPress theme,
  Framer) and which path worked. Knowing a stack is client-rendered before you
  `curl` saves picking the wrong path.
- **Adapt mode?** The library *is* the reference shelf. Pull a motion signature or
  a type ratio from a site already captured instead of guessing at a feel.

**A brief with a "wow"/premium/distinctive ambition changes what this read is
checking for.** Most captures sit in the same CSS/DOM/Framer-template register,
so a donor search run on autopilot quietly inherits whatever register the
library happens to be full of, and defaults to more of the same the moment
ambition asks for something that register cannot deliver. The library already
held the counter-evidence once: Sylva (`library/sylva.md`) is a hand-built
three.js site where the UI itself carries zero saturated hue anywhere in its
16-swatch palette ("the colour comes from the WebGL scene," not any DOM
element), directly relevant to a later "no flat colors, use three.js" request.
Nothing in donor selection surfaced it; the entry only got used once the user
asked outright why swipefile wasn't reaching for three.js at all, on a build
where the entry had been sitting in the library the whole time. So when the
brief's ambition language reads as "wow," premium, or best-in-class (not
merely "nice"), read every entry's *Notable* column, not just its *Motion
fidelity* column, and say out loud whether any of them uses WebGL, canvas, an
SVG filter, or another technique outside the default register before
defaulting to whatever register most captures happen to be in. Surfacing it is
not choosing it (mechanism quality still decides the donor), but a register
nobody named can't be weighed at all.

**ThreeUI (`library/threeui.md`) is the other half of that check, and usually
the first one worth reading.** Where Sylva demonstrates that a bespoke
three.js register can carry a whole page, ThreeUI is a real, MIT-licensed,
`npm install`-able catalog of 220 ready components (buttons, backgrounds,
data-field visuals, brand-mark reveals) built explicitly for agents to pull
into a build: a donor catalog, not a site to study. Before hand-authoring a
CSS/SVG approximation of a "premium" moment, check whether ThreeUI already has
a Community-tier component for the job; it usually beats building one from
scratch, and its source is directly readable rather than something to
reverse-engineer from computed styles.

The cross-site patterns section at the bottom of the index is the compounding
part; it is where "scroll-reveal is usually a two-class gate" and "column counts
are increasingly JS-computed" come from. Those generalisations are what make the
next capture faster.

## Step 0.5: Brief the gaps, on paper

**Fires for Adapt or Brand-generation**: anything that ships as the user's own
site rather than a local study. Match and Transfer skip it: Match's reference
already answers everything, and Transfer's target is the user's own existing
page, which already has everything but the one mechanism being copied in.

Run the `design-intake` skill. It is the standing version of the rule
`references/taste.md` §1 states outright (*"every gap gets filled with a
default, and the defaults are the problem"*), covering not just a missing
reference but every input a reference doesn't supply: brand kit, previous
design, copy ownership, contact info, form destinations, page scope, imagery
source, and (only when there is no reference at all) a style family. It asks
one question at a time, pre-filled from whatever the request already said, and
accepts "your call" as a complete answer wherever a dial is genuinely the
user's to skip. That delegation is then `references/taste.md`'s to resolve,
including font choice, which routes through §1a's sourcing tiers (Google Fonts
self-hosted, then Fontshare, then a user-supplied commercial file) rather than
a pairing-pool name with no path to an actual file behind it.

Its output, `BRIEF.md`, is what Step 1 reads before capturing anything. Do not
proceed on a guess when this step applies. It also doubles as Step 4 Gate B's
"the brief in one line" input, so writing it once here is the only time it gets
written. Under `studio-os`, the same interview fills `docs/project/01-brand.md`
instead of a standalone file. See `design-intake`'s own SKILL.md for that
split and for what it deliberately leaves to Studio OS (budget, deadline,
approval gates) rather than asking twice.

## Step 1: Capture

Pick the strongest path available:

| Situation | Path |
|---|---|
| `chrome-devtools-mcp` connected | Best. Drive the live page directly: `evaluate_script`, `take_screenshot`, `hover`, `resize_page` |
| Claude in Chrome, or another browser MCP | Same approach, whatever the equivalent tools are, but an **in-app browser pane is for interaction only**: one rendered a working page as a fully black frame that headless CDP captured at 64% non-black pixels, and its `IntersectionObserver` never fired on an element demonstrably on screen where CDP revealed 11/11 sections. Re-measure through CDP before any number enters the report |
| **Nothing connected, but Chrome is installed** | `python3 scripts/cdp-run.py <url> <script.js>`: real headless Chrome over CDP, needs only the `websockets` package. This is the **measurement instrument**: prefer it over any pane for numbers you intend to keep. Do NOT substitute `chrome --headless --virtual-time-budget --dump-dom`; it scrolls but never fires `IntersectionObserver`, so every scroll reveal reports as "no motion" (measured as 0 animations on a fixture with 10) |
| Playwright or Puppeteer installed | Run `scripts/capture.py` |
| Chat only, no browser access | Send the user `scripts/extract-console.js` to paste into DevTools |

**Canvas and WebGL heroes are a blind spot in the extraction, by construction.**
None of the CSS-token machinery describes a `<canvas>`: a three.js hero extracts
as a single element with a background colour, so a Match built from that capture
silently drops the thing the reference is actually known for. Two rules:

- `scripts/capture.py` now launches with a real GPU path
  (`--enable-gpu --ignore-gpu-blocklist --enable-unsafe-swiftshader`, plus the
  platform's ANGLE backend). Without those, headless Chromium software-renders
  and a WebGL hero captures as a **black rectangle that looks like a design
  choice**. Verified: with the flags, `get.webgl.org` reports "Your browser
  supports WebGL" during capture.
- Every capture records a **canvas census** (`canvases` in `extraction-W.json`:
  buffer and CSS dimensions per canvas), and any canvas ≥200×200 CSS px prints a
  warning. When it fires, open `full-W.png` and confirm the canvas rendered
  before trusting the capture, then describe the 3D content in prose, because it
  will not be in the tokens.

Motion and fonts have dedicated extractors, and both are two-sided or two-phase
for reasons that bite silently otherwise:

- `scripts/motion-extract.js`: the per-animation spec (target, trigger as a
  viewport %, from→to, duration, easing, stagger ladder). **Run it with
  `cdp-run.py --pre motion-extract.js`**, which injects it before the page's own
  scripts. Hooks installed after load miss every hero and entrance animation,
  because a finished transition is gone from `getAnimations()` and cannot be
  recovered; on one real site that was the difference between 0 animations and
  35. Without this, an entry records the scroll half of a page's motion and none
  of the half a visitor sees first.
- `scripts/font-gate.js`: run on the reference *and* the mirror, and compare.

`references/capture.md` has the exact tool sequence for each path, the install
command for `chrome-devtools-mcp`, and what to ask the user for when you're
working chat-only.

Collect all six artifacts. Anything you don't get is a guess later. Name the
gaps out loud rather than filling them silently:

1. **Markup**: `outerHTML` of the section in question.
2. **Tokens**: custom properties, plus computed values sampled off real
   elements. Sampling beats reading source CSS: it resolves cascade, media
   queries, and fallbacks for you.
3. **Motion**: `@keyframes`, live `getAnimations()` timing, transitions, and
   which library is loaded. That is the *signature*. For anything that will be
   rebuilt or stored in the library, also take the *spec* with
   `motion-extract.js`: which element, what trigger, from→to, and the stagger
   ladder. A tally of curves says what a site feels like; only the mapping can
   be built, and an entry without it produces a page with correct type, correct
   colour and no animation.
4. **Interaction states**: hover, focus-visible, and active. Easy to forget and
   very visible when missing.
5. **Responsive behavior**: the actual breakpoints, and what changes at each.
6. **Screenshots**: full page, plus start and end frames of each notable
   animation, plus one per breakpoint.
7. **The raw stylesheets.** Computed styles resolve values but hide which
   selector produced them, and cannot show a rule that did not apply to the
   element you sampled: `:first-child` overrides, whether spacing is a `gap` or
   per-item padding, the `clamp()` behind a size. `curl` the CSS and read the
   real rules for the selectors you are rebuilding. See `references/capture.md`.
8. **Pseudo-elements.** Check icons, stamps, counters, dividers and dots often
   live in `::before`/`::after`, invisible to element queries, so a text search
   for the visible mark finds nothing and the component silently degrades to
   plain text. Read them with `getComputedStyle(el, '::before')` and pull their
   rules from the source CSS.
9. **Text content, programmatically.** Extract it from the DOM or raw HTML by
   script into the build. Never retype it, never substitute placeholder in
   Match mode. A full-page frequency tally of rendered text styles
   (size/weight/family, sorted by count) is also the fastest check that your
   type scale is right: the top entries are the system.

Scroll the page top to bottom before extracting. Scroll-triggered animations
don't appear in `getAnimations()` until they've fired once, and lazy sections
aren't in the DOM yet.

## Step 2: Write the motion spec before writing code

Under-specified motion is where these builds fall apart. Convert raw extraction
into an explicit spec (trigger, properties, duration, easing, stagger, scroll
offsets) and confirm it before building.

**Get the spec from `scripts/motion-spec.py`. Do not start from prose, and do
not start from your own recollection of the page.**

```bash
python3 motion-spec.py --name <Name>            # library, if the entry is spec-grade
python3 motion-spec.py --url https://ref.com    # otherwise capture one
python3 motion-spec.py --list                   # what is buildable right now
```

It exits non-zero when no spec exists, and prints the command that produces one.
That refusal is the point. This rule existed as prose first and did not hold: an
agent built a section's motion from a `partial` entry plus hand-written probes
**three times in one session**, patching each time the user noticed something
static, and afterwards wrote *"the skill has a purpose-built instrument I haven't
used once."* The rule was quoted back correctly the moment the file was finally
read. Prose does not stop anything; holding the artifact does.

Two habits that produce that outcome, both defects:

- **Motion described in words in your capture notes.** "Drifts", "lifts",
  "floats", "settles", "hover lift" carry no values, so whatever you build from
  them is invented or static. Observed twice in one session: *"I described those
  tiles as 'drifting' in my capture notes but never measured it, then built them
  static."* If a note names a movement, it carries the numbers or it is marked
  unmeasured, never a description standing in for a measurement.
- **Hand-rolled per-element probes.** A selector you write for one component
  finds only what it matches, and reports nothing for everything it misses:
  *"selector caught text spans, not the tiles."* `motion-extract.js` sweeps the
  whole page and records every animation with its target, so a wrong selector
  cannot masquerade as an absence of motion.

`references/motion.md` has the template, the easing reference, library
translation notes, and current browser-support facts for scroll-driven
animations and `linear()`.

## Step 3: Build in this order

**On a build with a `BRIEF.md` (Adapt or Brand-generation, no reference:
`design-intake`'s field 0): check every proposed section against the stated
thesis before writing it, not after.** "This genre of site usually has a
testimonials section / a trust-logo marquee / an AI-chat demo" is not a
reason to add one. It's the exact failure `design-intake`'s field 0 exists
to stop, and it is invisible to every gate below, because a testimonials
section built competently still passes contrast checks, still clears the
copy gate, still measures a clean font census. None of that says whether the
section belongs. A section that doesn't serve the thesis gets reworked until
it does, or cut. This is a standing failure mode, not a hypothetical one. A
build here shipped eleven sections this way, iterated on for hours, and the
fresh-eyes critique named the same root complaint three separate times
before anyone asked why a *build* problem kept surviving *fix* after fix.

Each layer below constrains the next, so order matters.

1. **Tokens as CSS custom properties.** Every color, size, and radius resolves
   through a variable. Values hardcoded across the markup make Step 4 painfully
   slow, and Step 4 is what actually gets you close.
2. **Static layout at the reference's primary breakpoint.** No motion yet.
3. **The other breakpoints.**
4. **Interaction states.**
5. **Motion**, from the spec.
6. **`prefers-reduced-motion`.** Reference sites often skip it. Include it
   anyway: one media query, and vestibular triggers are a real accessibility
   failure.

Watch CSS specificity as you go. Element-based and class-based selectors that
cancel each other out is a common self-inflicted bug, especially with section
padding and margins.

On fonts: for a local Match, fetch the reference's actual font files and serve
them locally; they are already being served to every browser that loads the
page, and the typeface drives every text width on it. Substituting is an **Adapt**
move, or a step you take when the artifact is going to be published; in that case
name the replacement face and why, because a silent swap to a system stack leaves
the user wondering why the result feels off. Never substitute silently in Match.

**Fonts fail silently, so they get their own gate: `scripts/font-gate.js`, run
on the reference AND on the mirror at the same viewport.** The gate is that the
two sides **agree**: equal `document.fonts.size`, the same `check()` per
family/weight, canvas widths within ~1px. It is never that either side returns
true. A family `false` on *both* sides is declared in a fallback stack and
never painted, which is a pass, and demanding an absolute `true` makes a
byte-accurate mirror fail its own gate.

Every cheap detector lies here. Computed `fontFamily` echoes the requested
family while a fallback paints, and `document.fonts.check()` returns **true even
for a family that was never declared** (measured in `tests/test_font.py`). The
canvas width A/B is the only arm that catches a silent fallback, and it has to
probe the *display* face against a forced `sans-serif`, because
metric-compatible `<Family> Placeholder` faces read identical against the page's
own stack.

The four traps that produce a silently wrong face (inline `@font-face`, CORS,
lying computed styles, and SRI voiding a rewritten sheet) are in
`references/verify.md` §6, with the measured numbers. A Match with an unverified
font is not done: the wrong face changes every wrap and box height on the page.

Same rule for images, icons, and logos: fetch them, keep them local, and record
in the build notes what came from the reference. A gradient in place of a real
image is a defect, not a placeholder.

**In Adapt, the reference's images are the one thing you cannot carry over**.
They are the part that belongs to the reference, and the build ships under the
user's name. So an Adapt needs its own imagery, and a page of coloured
rectangles where the reference had photographs loses the thing the measurement
was for. Generate it with `imagegen-frontend-web` (or `-mobile` for app
screens) **before building**, at the section geometry this capture measured, so
the layout is planned around real assets rather than retrofitted to them.

## Step 4: Close the loop with visual diffs

This is what gets the result close, and it's the step most often skipped.

Measure, don't squint. `references/verify.md` has the loop: read the same box
geometry off both pages at the same viewport and chase every non-zero delta to
its cause, then capture both headless under identical conditions and compute a
pixel difference. **For Match the target is 100%, and ≥95% similarity with ≥90% of
pixels within 16/255 is the floor you must clear before showing the user anything,
not the goal.** Keep going while deltas still have findable causes. Read the
amplified diff map: ghosted text means a vertical offset above it, not a text
problem.

A Match that measures 95% because the content is real and one shadow is off is
nearly done. A Match that measures 95% because the layout is right and the text
is invented is not a 95%; it is an unfinished build with a misleading number on
it. Never report a similarity score for a page containing placeholder content.

**The pixel diff cannot see motion, so it gets its own gate.** Screenshots are
static: a build with every animation missing still scores 99%, and the number
reads as "nearly done" about a page that is dead the moment it loads. Capture
both sides with the same instrument and compare them:

```bash
python3 cdp-run.py https://reference.com  motion-extract.js --pre motion-extract.js --out ref.json
python3 cdp-run.py http://127.0.0.1:8791/ motion-extract.js --pre motion-extract.js --out build.json
python3 motion-diff.py ref.json build.json          # --adapt when content differs
```

It fails on a build with no motion, a missing signature curve, absent structural
durations, a missing stagger ladder, and on any build with no
`prefers-reduced-motion` (that last one regardless of what the reference does).
Durations are weighted by use count, the same way the library treats colour: a
duration used 490 times is the system, one used 14 times is decoration and is
reported rather than gated, because a gate that cries wolf gets ignored.

Before writing any UA reset of your own, note that an unreset `<p>`
`margin-bottom` is the single most common source of a whole-page offset.

Two or three rounds usually converges. Stop when the number stops moving, not
when the page looks fine. If a delta survives two rounds, a rule you have not
read yet is causing it. Go back to the source CSS rather than tuning values by
feel. Check each breakpoint, not just the wide one.

Without browser tooling, hand the user both images side by side and ask what's
off.

For Adapt mode, the diff question changes: not "is this the same?" but "does
this carry the same feel with its own identity?" Matching too closely in Adapt
mode is a failure, not a success.

**Which means Adapt, Brand and every original build have no pixel target, so
they get their own gate, and it is not optional.** Everything above measures a
build against a reference. A build with no reference has historically shipped on
an adjective, which is the exact handover the report exists to replace.

```bash
python3 design-gate.py http://127.0.0.1:8791/ --mode adapt --src ../src --out design.json
python3 report.py ... --design design.json      # sits beside the fidelity gates
```

It measures the mechanical half of a taste pre-flight on the served page:
composited contrast on every CTA and form control, wrapped button labels, the
eyebrow census against its own budget, the light/dark section sequence, the
accent and radius censuses, painted-vs-declared font families, and the
source-level rules a rendered page cannot show. Same vocabulary as every gate
here: pass / FAIL / WARN / UNVERIFIED, and unverified is never a pass.

The other half (is the copy LLM-flavoured, is each animation motivated, does
the whole thing read as templated) is not mechanical and must not be faked by
self-review: the author defends what the author just wrote. It goes to a
subagent that never saw the build happen, given the screenshots and the rendered
text and **not** your reasoning. `references/taste.md` has the loop, the
precedence rule for where a measured reference value beats a house rule and
where it does not, and the honest list of what neither gate covers.

**Close every Match with the replication report, and get it from
`scripts/report.py`**, not from the table in `references/report.md`, which is
the specification, not the artifact.

```bash
python3 report.py --init          # skeleton: every metric, blank
python3 report.py --site example.com --mode match --path mirror \
    --crawl crawl-manifest.json --build build-manifest.json \
    --copy copy.json --motion motion.json --measured measurements.json
```

It aggregates what the other instruments emit and refuses three things a
hand-written table does easily: **omitting** a metric (exit 2, naming the
command that produces it), **passing** a gate nobody measured, and **scoring** a
page containing placeholder content. An unmeasured gate reads `UNVERIFIED`: it
does not block, so a mirror can always produce a report, but it is never a pass
and the headline carries the count. `--strict` makes them blocking. **Say
"reported", not "verified", while any gate is unverified**, and put those gates
in the honesty rows. The gate list and the JSON schema are in
`references/report.md`; together they are the definition of done, and the user
should never have to ask "how accurate is this?"

It is a script rather than a paragraph for the reason Step 2 already paid: prose
is what gets quoted back correctly while being skipped.

## Step 5: Record what you learned

A capture that teaches you a site's system and then throws it away is waste. Before
you finish, write `library/<domain>.md` and add a row to `library/INDEX.md`.

Write it for the version of you that arrives at this site in six months with no
memory of today. Concretely:

1. **Tokens as a system, not a dump.** The ratio, not the five numbers. "The scale
   is `vw`-based pinned to a 1440 design width" is worth more than a list of px.
2. **The motion signature.** The highest-frequency easing curve and duration, and
   one line on the *character*: utility interface, long settle, no scroll motion.
   This is the single most reusable thing in the entry.
3. **The structural pattern**, if the site has one: sticky-stacking, a JS-computed
   grid variable, a two-class reveal gate. Name the mechanism.
4. **The gotchas, the highest-value section.** What broke, why, and the fix. Every
   hour lost to a frozen JS region or a deferred renderer should cost that hour
   exactly once.
5. **What you achieved**, honestly: the diff number and what was left unresolved.

Then update the **cross-site patterns** list in the index if this capture confirms
or contradicts one. That list is the actual learning; the per-site entries are
evidence for it.

**Then run the library gate: it is one command and it guards the thing that
silently mis-resolves.**

```bash
python3 library-lint.py
```

It checks what the library's own readers assume: exactly one page-wide `Motion
fidelity:` declaration and that `motion-spec.py`'s regex lands on *that* line
(it takes the first match anywhere in the file, so a component-scoped `spec`
note above the declaration promotes a `partial` entry to buildable), a legal
fidelity value, a mapping table behind every `spec` claim, no callable name
claimed by two entries or shadowing another's, and the INDEX row agreeing with
the entry it links to. Step 0 reads fidelity off `INDEX.md`; `motion-spec.py`
never opens that file. Nothing else compares the two.

**A lesson that stays in the library does not fire.** The index is read once, at
Step 0, as an index, so a rule recorded only there is a rule the procedure will
not follow, and the next run pays for it again. When a capture teaches something
that changes *how the work is done*, land it where it executes in the same pass:
a `references/` step if it is a judgement, a `scripts/` change if it is
mechanical. Then check the reverse direction: that no reference or script still
instructs the behaviour the lesson just disproved. That check is the one that
matters, because a procedure contradicting its own library is worse than one
that is merely silent: it actively steers into the failure the library already
paid to discover. An audit of this skill found 33 such gaps at once, 16 of them
HIGH, and every one had been correctly written down first.

On a multi-page crawl, also record the **template taxonomy**: the distinct page
types seen (service page, case study, landing, listing), what varies between
instances of one template and what is fixed. One line per template is enough.

**Entries may be drafted by a local model, never accepted on its word.**
`scripts/local-entry.py` drives an Ollama model from a capture JSON to a
finished entry, behind two gates: `library-lint.py` (the resolver can read it)
and `scripts/provenance.py` (every number, hex, curve and date traces to the
capture; measured necessity: a local model handed a capture invented the
capture date and dropped every hex and curve while producing perfect
structure). Failures are fed back into the prompt and retried; only an entry
that clears both gates lands, and `--write` re-lints the whole library
afterwards, rolling back byte-for-byte if it fails. A fabricating model costs
retries, never corruption. The gate's scope is the four token classes:
numbers, hexes, curves, dates; prose claims (numbers written as words, named
colours, easing keywords, font or library names) are yours to judge when you
read the entry, and that division is deliberate.

This step is not optional housekeeping; it is why the skill gets better. The
library is what separates the next original build from a templated default: when
asked to *design* rather than replicate, the entries are a shelf of real,
measured systems: how a working studio spaces a section, how tight a real
reveal's travel is (5px, not 40), which curve a site actually ships, instead of
the generic answers that read as AI output. Recall beats taste. Every capture
that skips this step leaves the next build dumber than it had to be.

Write every entry as if it will be read by an agent that has never seen the
site and cannot visit it, because that is the library's future: it travels
with the skill folder to other agents and harnesses (see "Portability and what
ships"). An entry that only makes sense next to its mirror has failed; the
numbers, names, and mechanisms must stand alone.

**Keep the library to design-system facts**: palettes, scales, curves,
breakpoints, layout mechanics, gotchas. No body copy, no imagery, no assets: those
belong to the local mirror for the job that needed them, and are covered by the
rules below. The library is knowledge, and it is meant to outlive every artifact.

## Copying, and where the line is

Layout, spacing, type scale, color relationships, and motion patterns are the
shared vocabulary of web design. Learning from them is ordinary practice.

Logos, photography, illustration, licensed fonts, and body copy are not. Neither
is a wholesale clone presented as original work, or one that could confuse users
about who they're dealing with. Automated extraction should also respect the
site's terms of service and robots.txt.

The line is **publication, not possession**, and it applies per artifact, not
per file type. A local study rebuild that serves the site's own fonts, images and
copy is ordinary developer practice: it is what every browser that loads the page
already did. Refusing the images while transcribing every word of their copy is
not a coherent position: pick one standard and apply it to both. For a local
Match the standard is **fetch everything and record what came from where**.

"Indistinguishable from theirs" is the *goal* of a local Match, not a warning
sign. That is what a 100% replication means and what the Step 4 diff measures.
The question to ask is never "how accurate should this be?" but "where is this
going to end up?" If the answer is a deploy, a public URL, or anything presented
as the user's own product, raise that once; the constraint is on shipping it,
and it is not answered by making the local build worse. Degrading fidelity
protects nobody: it produces an artifact that is equally un-shippable and no
longer verifiable.

What does not change: keep the assets local, note in the build what came from
the reference, repoint live form and application endpoints at something inert so
the copy cannot transact, and do not publish a faithful clone of a real
organisation's page. Say that plainly once, in the notes, rather than quietly
degrading the build.

## Portability and what ships

This skill folder is self-contained and framework-neutral by design: `SKILL.md`
(open Agent Skills format), `references/` (plain markdown), `scripts/` (plain
Python; the browser path uses Playwright), and `library/`. Nothing in the
workflow requires a specific agent harness. Where a step says to drive a live
browser, use whatever browser tool your harness has, and fall back to
`scripts/capture.py` (Playwright) or `scripts/extract-console.js` (paste into
DevTools) when it has none.

**The skill ships with a BLANK library.** The distributable artifact is the
engine: workflow, scripts, references, and the empty `library/` scaffold
(`INDEX.md` header plus `TEMPLATE.md`). Every installation grows its own library
from its own captures, on its own machine:

- Nothing captured ever leaves the machine that captured it, not mirrors, not
  library entries. There is no shared corpus and nothing to redistribute.
- Each user's library becomes their accumulated design education: structured,
  measured, model-readable. It works as-is for retrieval/context with a local
  model, and because every entry follows `library/TEMPLATE.md`, converting it to
  fine-tuning data later is mechanical. Uniform structure is what makes the
  library trainable; a freeform library is just notes.
- **Builds live in the workspace, indexed in `BUILDS.md` at its root**: one
  folder per build (`<reference>-<mirror|clone>`), servable root `site/` for a
  crawl and the folder itself for a single-page rebuild, with its `REPORT.md`
  beside it. Append a row when a build finishes and read the index before
  starting one: an unindexed build is a folder nobody knows to reopen, and a
  mirror already on disk is ground truth that beats rebuilding from memory.
  Never leave a build in a temp directory; those are wiped, and the user asks
  for it back a week later.
- Mirrors remain content and stay out of the library. The library is
  knowledge (measurements, ratios, curves, mechanisms) and contains no site's
  copy, imagery, or assets. Any new artifact the skill produces is one or the
  other.

**Never hand-assemble the distributable; `scripts/package.py` builds it.**

```bash
python3 package.py                     # -> dist/<skill>/ and dist/<skill>.skill
python3 package.py --verify dist/<skill>
```

It stages from an **allowlist**, so an artifact nobody thought of cannot ride
along, then audits the result as if the allowlist were untrusted: no captured
entry, no `INDEX.md` row, no mirror or build artifact, no bytecode; and the
packaged suite has to pass *in place* before an archive is written. Traces of
this machine's corpus that are only names (an example command naming a real
site) are reported as warnings rather than blocking, so genericise them before
sending a bundle to a stranger. The promise above is the user's, not a
convention: a reset that lives in a paragraph is a reset somebody eventually
forgets, and the leak is found by whoever receives it.

## Failure modes worth watching for

- **Easing invented from vibes.** A custom cubic-bezier replaced with
  `ease-in-out` is the most common reason a rebuild feels wrong despite matching
  pixel-for-pixel. Extract the real curve.
- **Pixel values copied instead of the scale behind them.** 14/16/20/28/40 is a
  ratio, not five numbers. In Adapt mode the ratio is the whole point.
- **Scroll offsets ignored.** "Fades in on scroll" is not a spec. Where in the
  viewport does it start, and where does it finish?
- **One breakpoint captured, responsive behavior invented.** Guessed mobile
  layouts are usually wrong in ways that are obvious to the user immediately.
- **Adapt handled as Match.** The user asked for inspiration and got a clone
  they can't ship.
- **Match handled as Adapt, the most common failure of this skill.** Placeholder
  copy, substituted fonts, gradient blocks where images go, or a "representative"
  subset of the content, shipped against a request for a replication. It usually
  arrives dressed as caution. It is not caution: the user asked for a working
  replica and got a sketch, the diff in Step 4 becomes meaningless, and the gap
  gets discovered by the user instead of reported by you. If something could not
  be captured, say so; do not fill it in.
- **Fidelity degraded in place of raising a publication question.** Quietly making
  the build worse instead of saying once, plainly, where the artifact can and
  cannot go. Build it accurately, note the constraint, let the user decide.
