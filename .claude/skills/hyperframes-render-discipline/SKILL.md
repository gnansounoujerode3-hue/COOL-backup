---
name: hyperframes-render-discipline
description: Six verification habits for render and capture work - five carried over from building the same piece in Remotion right after HyperFrames, plus a frame-capture discipline harvested from a puppeteer QA harness. Each maps to a real bug that shipped (or nearly shipped) without it. Use BEFORE finalizing render timing in a HyperFrames composition (duration source of truth), AFTER any render (duration verification), whenever a GSAP exit tween is added (hard-kill pairing), whenever a background element changes near existing text (contrast re-check), whenever a visual bug survives two blind fixes (stop guessing, dump ground truth), and whenever screenshotting a canvas or WebGL scene (capture through a sink, assert the frame isn't blank).
---

# HyperFrames render discipline, learned by contrast with Remotion

Built the same 5-beat stat video twice in one session - once in HyperFrames (twice,
actually, after a director rebuild), once in Remotion. Neither framework is "better";
but Remotion's tooling made certain checks unavoidable that HyperFrames' workflow makes
optional, and every one of those checks maps to a bug that actually happened. This is
what to keep doing in HyperFrames now that the contrast made it visible.

## 1. Verify actual rendered duration with `ffprobe`, not just the CLI summary

Remotion's render overshot into ~2s of blank frames because `TransitionSeries`
subtracts transition time from the total rather than adding it, caught in under a
minute because `ffprobe -show_entries format=duration` gave an exact number to compare
against intent, immediately after render.

**HyperFrames renders never got this check this session.** All three (`systo-intro`,
`systo-explainer`, `systo-stats`) were accepted on the CLI's own printed "X.Xs video"
line alone. That line is almost certainly correct, `data-duration` is authoritative,
but "almost certainly" is exactly the gap `ffprobe` closes for free:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 renders/*.mp4
```

Run it after every render. Compare against the intended duration, not against what the
render command printed.

## 2. One source of truth for duration, never a hand-synced pair

The Remotion overshoot's root cause was a *guessed* composition duration living apart
from the *computed* sequence total, two numbers that could drift, and did.

Every HyperFrames composition this session had the exact same shape of risk: root
`data-duration="15"` typed by hand, GSAP beat times typed by hand elsewhere in the same
file, kept in sync only by the author remembering to update both. Nothing enforces
they match. Where a project's beat lengths are more than trivial, compute the root
`data-duration` from the same array of per-beat seconds that seeds the GSAP timeline
positions, rather than writing the total as its own literal.

## 3. Pair every GSAP exit tween with its hard-kill on creation, not after `check` complains

`@remotion/transitions`' `TransitionSeries` handles the "did the exit actually finish
before the boundary" problem structurally, there's no way to forget it. HyperFrames'
raw GSAP model has no such guarantee, and `gsap_exit_missing_hard_kill` fired on both
`hyperframes-systo-explainer` and `hyperframes-systo-stats` this session, same lint
error, two different projects, because the fix was applied per-tween after the fact
instead of built into the helper.

Write exit helpers that can't produce the bug:

```js
function exitBlur(sel, endAt, dur) {
  tl.to(sel, { opacity: 0, scale: 1.14, filter: "blur(9px)", duration: dur, ease: "power2.in" }, endAt - dur);
  tl.set(sel, { opacity: 0 }, endAt); // hard kill, always - not added after lint complains
}
```

Any project's shared exit/enter helpers should default to this shape from the start.

## 4. Re-verify contrast against the actual composited background, not the flat pairing

The AA-safe accent color (`#FA5029`, later `#D63816`) broke contrast twice in
`hyperframes-systo-stats` alone, once when a glow bloom sat behind it, once when a
5%-alpha ambient wash was added, because each fix was verified against a flat Paper
background, not against what the text would actually render on top of once every other
layer in the shot was present. The Blender/Remotion color pipeline taught the same
lesson from a different angle: a color choice is only verified once it's been checked
in the exact rendering context it will actually appear in, not the isolated case that's
easiest to compute.

**Rule:** any time a new background element is added near existing text (a glow, a
wash, a gradient, anything with opacity < 1 over the text's backdrop), re-run
`npx hyperframes check`'s contrast pass before assuming an already-verified color still
holds. It usually doesn't, by exactly the margin that was spent proving it worked the
first time.

## 5. When a visual bug survives two blind fixes, stop guessing and dump ground truth

Three attempted fixes to a Blender notch-alignment bug, bevel width, then Z-height,
then a third look, all guessed from reading an isometric render. None worked, because
none were the actual bug (a `size=1` cube scaled by `size_x/2`, silently halving every
object). What actually found it: a five-line script printing each object's real
world-space bounding box. Ground truth in five lines beat three rounds of eyeballing.

The same applies inside a HyperFrames composition: if a `snapshot --at` contact sheet
doesn't resolve a positioning or timing bug on the second look, stop iterating on CSS
values from the render alone. Use `npx hyperframes docs troubleshooting`, or open
`npx hyperframes preview` and read computed values directly (`getBoundingClientRect()`,
computed style) via the browser, rather than a third guess informed only by a picture.

## 6. Capture frames through a sink to disk, never through the agent's context

Harvested from `bilawalsidhu/gods-eye-view`, whose `scripts/shot-sink.mjs` carries the
rationale in its own header: *"Keeps large image payloads OUT of the agent's context,
browser → sink → disk."* A ~40-script puppeteer QA harness written for exactly this
workflow, and the sink is the load-bearing piece.

The pattern is a 40-line HTTP server that accepts a `data:image/...` POST and writes the
file. The browser grabs the real GPU canvas, POSTs it, and the agent only ever reads the
one-line path and size that come back.

```js
// The page POSTs to the sink; the agent never holds the pixels.
await fetch(`http://localhost:4399/save?name=${shot}`, { method: 'POST', body: canvas.toDataURL() })
```

Three mechanics that decide whether the frame is real:

- **`preserveDrawingBuffer: true`** in the renderer/context options, or `toDataURL()`
  returns an already-cleared buffer.
- **Force one explicit render immediately before reading**, so you capture the current
  frame rather than a stale one. On a governed/on-demand loop (§ the idle governor in
  [[threejs-scroll-sites]]) nothing is drawing while you sit there, so this is mandatory,
  not defensive.
- **Grab the renderer's own canvas**, never `document.querySelector('canvas')`. Cost me a
  full debugging round today: a page had seven canvases and the selector returned a
  300×150 default-sized one while the real target was 1600×900.

**Assert the frame isn't blank, and do it on pixels, not on file size.** File size is
the obvious check and it does not work. Measured on a 1200x675 WebGL canvas: a fully
transparent capture was **18.1 KB**, so a "under 15 KB means blank" rule passed it as
real content. Count distinct pixel values instead. Downsample into a scratch 2D context
and put the result in a Set:

```js
const s = document.createElement('canvas'); s.width = 64; s.height = 36;
const x = s.getContext('2d'); x.drawImage(canvas, 0, 0, 64, 36);
const d = x.getImageData(0, 0, 64, 36).data, seen = new Set();
for (let i = 0; i < d.length; i += 4) seen.add(`${d[i]},${d[i+1]},${d[i+2]},${d[i+3]}`);
// seen.size === 1 means every sampled pixel is identical, i.e. nothing rendered
```

Same canvas, same run: blank frame `1` distinct colour, real frame `161`. The pixel test
separated them; size did not.

**The count and the `toDataURL` must run in the same synchronous block as the draw.**
Without `preserveDrawingBuffer` the buffer clears after each composite, so a pixel test
in a second `page.evaluate()` reads an already-cleared canvas and reports *every* capture
as blank, including the good one. That mistake looks exactly like a real bug and wasted a
round here before the numbers made it obvious.

This is the same root cause as the note that the Browser pane is not a measurement
instrument: a hidden pane composites no frames. The sink pattern sidesteps it entirely,
puppeteer with a real GPU context, pixels straight to disk, context untouched.

## Where this doesn't transfer

Not everything about Remotion's tooling is portable, most of it is a consequence of
being a different framework, not a better practice:

- React/hooks vs. GSAP-timeline authoring is an architecture choice, not a bug either
  side has. Nothing here suggests HyperFrames should adopt React.
- `TransitionSeries`' declarative scene-to-scene transitions are cleaner than hand-built
  GSAP enter/exit pairs, but that's Remotion's framework design, not something to import
  as code, §3 above is the closest honest transfer (write helpers that can't omit the
  hard-kill, rather than trying to replicate `TransitionSeries` itself).
- TypeScript's `tsc --noEmit` catching an unused-import error in seconds has no
  HyperFrames equivalent because there's no compiler in a vanilla-JS composition file -
  `npx hyperframes lint` is the nearest fast-feedback check and already gets used.

Related: [[hyperframes-design-memory]], the swipefile bridge (design tokens, not
engineering process). This skill is about render/verification discipline; that one is
about brand-fact provenance. Different concerns, don't merge them.
