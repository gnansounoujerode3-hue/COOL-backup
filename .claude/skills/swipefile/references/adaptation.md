# Adapt mode

For when the user wants a reference's *feel* applied to their own content. This
is most "build me a landing page like X" requests.

Read this after capture, before building. If the `frontend-design` skill is
available, read that too; it goes deeper on making original visual choices, and
this file is the bridge between an extraction and that kind of judgment.

## The two-URL form: re-skin my site with their system

"Here is my site (mysite.com); replicate reference.com and apply its design,
animations, and structure to mine" is Adapt with the content supplied **as a
URL instead of a brief**. It is the skill's most complete workflow and needs no
separate skill:

1. **Capture the reference** exactly as in Match: full extraction, and write
   its library entry. The system side of the work is identical.
2. **Capture the user's own site too**, but for *content*: crawl it for the
   real copy, page inventory, imagery list, brand colours, logo, and existing
   information architecture. This is the user's own property; it is the one
   case where copy and assets are collected for reuse rather than study.
3. **Map content to system.** Match the user's pages onto the reference's
   template taxonomy (their about page → the reference's about spine). Where
   the user has content the reference has no template for, extend the system's
   rules rather than importing a foreign pattern. Where the reference has a
   template the user has no content for, skip it. Do not pad.
4. **Build per the translation table below**: the reference's ratios, rhythm,
   and motion character; the user's copy, brand colours, imagery, and voice.
   The user's brand values win every conflict: their logo is not restyled to
   the reference's palette.
5. **Verify both ways**: the Step 4 feel-check against the reference (yes to
   same feel, no to mistakable-for-it), plus a content audit against the user's
   site: every page of theirs accounted for, no reference copy left anywhere.

The library compounds this: after enough captures, step 1 can start from an
existing entry, and the user's re-skin inherits every gotcha already recorded.

## Digest the reference completely first. This is not optional.

**Adapt and Transfer both require the full Step 1 capture of the reference,
section by section, before any code is written.** Not the gist. Not a
recollection. Not the library entry.

This is the single most common way both jobs fail, and it fails the same way
every time: the build is composed from a *summary* of the reference instead of
measurements of it, so it inherits the reference's vocabulary words and none of
its character. The user's reaction is "this looks sloppy" or "it doesn't feel
like the reference" and they are right, and no amount of tuning colour and
spacing afterwards recovers it, because the missing thing was never a token.

**A library entry is an index, not a substitute for capture.** Entries are
deliberately short: a signature curve, a ratio, the gotchas. That is enough to
*route* a job and nowhere near enough to *build* one. If the reference is already
in the library, the entry tells you where to look and what bit you last time;
you still open the reference (or its mirror, if you kept one) and measure. When a
mirror exists on disk, read it; it is ground truth sitting right there, and
building from memory while a byte-accurate copy is one directory away is
indefensible.

What "completely" means, concretely, before writing code:

1. **Every section**, in document order, with its real geometry (heights,
   column counts, gaps, padding, radii, content measures) in px.
2. **Every animation on the page**, not just the ones you noticed. For each:
   trigger, properties, from/to values, duration, easing, stagger, and for
   anything scroll-linked the start and end offsets. Sample the same elements at
   several scroll positions and diff the computed transforms: progressive change
   means scrubbed, a single snap means in-view-once. Rebuilding a scrubbed
   animation as a triggered one is the classic tell, and the two feel nothing
   alike.
3. **The full type census**: every size/weight/family/line-height/tracking with
   its frequency, and which role each plays.
4. **Interaction states** (hover, focus-visible, active): measured, not assumed.
5. **The alpha ramp**: the exact rgba levels used for secondary text, borders
   and raised surfaces. These carry more of a dark UI's quality than the hues do.
6. **The structural moves**: pins, sticky stacks, horizontal drifts, masked
   reveals, marquee speeds. Name the mechanism for each.

On a long page this is a lot of extraction, and it parallelises well: one pass
per section, then merge into a single spec. Do that rather than skipping it.

**Finish by naming the three things that carry the page's character**: the
motions or structural moves whose absence would make the rebuild feel wrong.
Then check your build has all three. If you cannot name them, you have not
digested the reference yet.

## The move: transfer the measurements, re-derive only what the brand owns

A design system is mostly ratios and relationships, and those transfer. But
"relationships transfer" is routinely over-read as licence to abstract
everything into proportions and re-derive the rest by taste. It is not.

The line is narrow and it is about **ownership**, not about abstraction:

- **Owned by the reference's brand**: typefaces, hex values, logo, photography,
  copy, the signature element. These get substituted or re-derived, always.
- **Everything else transfers as measured numbers.** Geometry, type ratios *and
  their actual sizes*, line-heights, tracking, alpha levels, radii, gaps,
  durations, easings, travel distances, stagger intervals, scroll offsets. A
  90px display at line-height 1.2 and tracking -0.02em is not "a large heading";
  it is a measurement, and it transfers verbatim.

| Extracted | In Adapt / Transfer |
|---|---|
| Type scale ratio **and its measured sizes** | Keep both: the ratio alone loses the character |
| Line-height, letter-spacing, font-weight per role | Keep: measured values, not approximations |
| The specific typefaces | Substitute (brand-owned) |
| Contrast structure, accent frequency, neutral count | Keep |
| The **alpha ramp** (e.g. secondary text at .6) | Keep: measured |
| The specific hex values | Re-derive for the new brand |
| Spacing rhythm, base unit, section padding | Keep |
| Grid, column counts, content measure, radii | Keep as measured px |
| Section order and page structure | Keep if the content has the same shape; otherwise it's cargo cult |
| Motion: duration, easing, travel, stagger, scroll offsets | Keep: **verbatim numbers**, this is most of "the feel" |
| Motion *character* (scrub vs trigger, pin, loop) | Keep, and keep the mechanism, not a lookalike |
| The signature element | Replace with one of your own, but match its *weight* in the composition |
| Copy and imagery | The user's own (two-URL form) or newly written |
| Newly written copy | Ours, therefore checked: `humanizer` loaded *before* writing it, `scripts/copy-gate.py` clean before showing it. Never the reference's words. See `references/copy.md` |

The frequency counts in the extraction are the useful signal for what is
structural. A colour used 40 times is structural; one used twice is decoration. A
type size used across every section is a scale step; one used once is a one-off.
Rebuild the structural layer faithfully, with its numbers, and let the long
tail go.

### Scope discipline: is this Adapt or Transfer?

Getting this wrong produces exactly the "too abstract" failure. If the user names
a specific element ("the hero of X", "X's card hover", "that scroll thing on
X"), it is **Transfer**, and the bar is near-exact: same structure, same measured
geometry, same motion, only the brand layer swapped. Do not generalise it into a
system. If they point at a whole site and their own content, it is **Adapt**, and
the system-level translation above applies, but still built from the full
measured capture, not from a summary.

## Ground it in the new subject

Before touching code, name the subject, the audience, and the single job the
page has to do. If the user hasn't specified, pick and say what you picked.

Distinctive choices come from the subject's own world: its materials,
vocabulary, artifacts, conventions. A reference gives you proportion and pacing;
the subject gives you the specifics that make the result belong to this project
and not the last one.

## Don't collapse into the AI defaults

Adapt mode's failure mode is drifting off the reference and landing on the
house style instead. Right now AI-generated design clusters hard around three
looks:

1. Warm cream background near `#F4F1EA`, high-contrast serif display, terracotta
   accent near `#D97757`. That accent is Claude's own interaction color, so on a
   user's brief it reads as a tell.
2. Near-black background with a single acid-green or vermilion accent.
3. Broadsheet layout: hairline rules, zero border-radius, dense columns.

All three are legitimate for some briefs. When the brief or the reference
specifies one, follow it. When an axis is left free, don't spend that freedom on
a default. If your palette drifted toward cream-and-terracotta and the reference
wasn't cream-and-terracotta, you stopped adapting and started defaulting.

Cheap check: draft the plan, then imagine a totally different brief in the same
category. If you'd have arrived somewhere similar, the plan isn't specific to
this one yet.

## Pick a new signature

Most memorable pages have one element they're remembered by. The reference has
one. Identify it, because it's carrying more of the impression than anything
else. Then build a different one for this project.

Spend boldness in one place. Let the signature be the loud thing and keep
everything around it quiet and disciplined. Maximal directions need elaborate
execution; minimal ones need precision in spacing and type. Either way the
discipline is what reads as intentional.

## Copy is design material

Placeholder copy makes a design feel as templated as the layout does. If the
user didn't supply text, write real copy for their actual subject.

Name things by what people recognize and control, not by how the system works.
Active voice by default; a button says exactly what happens when it's pressed,
and keeps that name through the whole flow. Empty and error states are direction,
not mood: say what happened and what to do next. Specific beats clever.

## Before you show it

**First, the motion gate: it fails silently and a screenshot cannot see it.**
The ownership table above says to keep duration, easing, travel, stagger and
scroll offsets as *verbatim numbers*, which means you must actually hold them.
Working from a library entry you often do not: an entry marked
`Motion fidelity: signature-only` has ranked curves and a character sentence and
no per-animation values at all. Before showing anything, name every animation
the reference runs and point at where each one's numbers came from: the entry's
spec table, a fresh capture, or nowhere. "Nowhere" is not a build that ships
quietly; it is either a re-capture (Step 1 + Step 2, motion only) or a stated
omission. A page whose type, colour and layout are right and whose motion is
absent reads as finished in every still and wrong the moment it loads, which is
why this check comes before the feel test rather than inside it.

**Then the content gate, because an Adapt ships a real page.** Run
`python3 copy-gate.py index.html` and clear it: no AI-writing tells in copy you
wrote, one `<h1>`, a title and meta description, `lang` and `alt` present, and
JSON-LD structured data actually on the page. Structured data was absent on both
builds measured before this gate existed, and it is what a generative engine
leans on to cite the page at all; a page nothing can quote is a page nobody
finds, however well it diffs. Never declare a schema the content does not back
up. `references/copy.md` has the full check list and the GEO floor; `humanizer`
holds the prose rewrites and gets loaded before the copy is written, not after.

Then look at the build next to the reference and ask two questions in this order:

1. Does it carry the same feel: pacing, proportion, weight, motion character?
2. Would anyone mistake it for the reference?

You want yes, then no. Yes-then-yes means you built a Match. No-then-no means
you lost the thread and should go back to the extraction.

Then remove one thing. There is almost always one decoration that isn't earning
its place, and cutting it is what separates a design that looks considered from
one that looks generated.
