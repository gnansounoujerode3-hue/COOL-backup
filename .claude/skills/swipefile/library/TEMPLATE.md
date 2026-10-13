# Library entry template

Every `<domain>.md` follows this shape. Uniformity is the point: the library is
read by agents (and fed to local models) that have never seen the site and
cannot visit it. Every value is **measured, not estimated**; every claim stands
alone without the mirror. No body copy, no imagery, no assets: knowledge only.

Omit a section only when it truly does not apply, and say why in one line
("No 3D: none present"). An empty heading is better than an invented value.

---

```markdown
# <domain>

**Callable as: <Name>** (aliases: <domain>, <other names people would say>)

<One line: what the site is.> Captured <date> @ <viewport>.
Stack: <framework/CMS/build evidence>. **<Mirror | Rebuild> path**<, variant>.

## Type — <the system in five words>

<The scale as a SYSTEM: ratios, fluid units, root size trick, leading rule,
tracking rule. A table of steps with measured values. Name the loaded families,
their format (variable? axes?), and their roles.>

## Layout

<Container widths/padding, content measure, grid mechanism (formula vs media
queries), the 2-4 breakpoints that actually carry the design, section rhythm.>

## Colour

<Palette with exact values AND the system behind it: alpha layering, semantic
roles, light/dark rhythm. The system matters more than the swatches.>

## Motion

**Motion fidelity: <spec | partial | signature-only | none>**

<Declare what this entry can actually support, conservatively:

- `spec` — every animation carries target, trigger, from→to, duration, easing,
  stagger and scroll offsets. **Only this value licenses building motion from
  the entry without re-capturing.**
- `partial` — real values measured (durations, travel, stagger ladders,
  properties) but no per-animation mapping. Saves most of a re-capture; does not
  replace one.
- `signature-only` — ranked curves and a character sentence. A vocabulary.
- `none` — motion exists on the site but was never measured.

Never promote this line without re-measuring. Under-claiming costs one cheap
capture pass; over-claiming silently ships a page with no animation, and no
still screenshot will show it.>

<**The signature.** Easing curves ranked by USE COUNT across the full stylesheet
— the top one is the signature. Duration inventory by frequency. Then the
character in 1-2 sentences: what moves, what never moves, travel distances,
stagger scheme. Name the mechanism of any scroll choreography (classes,
pinning, clip-paths). Record the `prefers-reduced-motion` handling, or its
absence.>

<**The spec.** One row per animation, in the `references/motion.md` vocabulary.
A curve list is a *vocabulary*; this table is the *mapping*, and only the
mapping can be rebuilt. Omit the table only with `signature-only` above.>

| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |
|---|---|---|---|---|---|---|---|

<Scroll rows: START/END as viewport percentages, and whether it scrubs. "Fades
in on scroll" is not a row. Close with what deliberately does NOT move.>

## Interaction states

<Hover / focus / active / current, as deltas: "bg alpha .1 → .2", "weight
400 → 500". Include the states that DON'T change.>

## Template taxonomy   (multi-page crawls)

| Template | Instances | Fixed | Varies |
|---|---|---|---|

<One row per page type. Close with which single pages capture the full system.>

## Gotchas hit while rebuilding

<Numbered. Each: symptom → root cause → fix → how to verify. This is the
highest-value section; every hour lost should be recorded exactly once.>

## Verification achieved

<The honest numbers: diff %, boxes exact, images loaded, fonts proven by
width-test, what was excluded and what remains unresolved.>
```

---

## Rules

1. **Measured or absent.** No value goes in that was not read off the live page
   or its stylesheets. "Feels like .3s" is not an entry.
2. **Systems over samples.** `8.3333vw against a 1440 design width` beats
   `120px`. The ratio transfers; the pixel does not.
3. **Self-contained.** If a line only makes sense next to the mirror, rewrite it.
4. **Knowledge, never content.** No copy, no image files, no logos, no excerpts
   of text beyond what a measurement requires (a headline's character count is
   knowledge; the headline is content).
5. **Cross-site patterns live in INDEX.md, not here**, and only once two or
   more entries support them, each cited by name.
6. **After writing:** add the one-line row to `INDEX.md` (site, date, path,
   signature motion, notable).
