# Verify: turn the diff into a number

Eyeballing two screenshots converges slowly and stops early. Two measurements
converge fast and tell you when to stop: **box geometry** for structure, and a
**pixel diff** for everything else.

Target for Match: ≥95% similarity and ≥90% of pixels within 16/255, scored per
region against that region's own ceiling, never as one blended number for the
page. Below that, something structural is still wrong; find it with geometry,
not by squinting.

## 0. Instrument: every number comes from headless CDP

The in-app browser pane is not a measurement instrument. Two measured failures:

- It rendered a working page as a **fully black frame**. Headless CDP captured
  the identical page correctly, at **64% non-black pixels**.
- A fresh `IntersectionObserver` at `threshold: 0.05`, on an element
  demonstrably on screen with working scroll, **never fired at all** (while the
  identical page in headless CDP revealed **11/11 sections**).

Both failures are silent: no error, no warning, a plausible-looking result.

So every number that enters the report (geometry probe, pixel capture, font and
asset probes, and all reveal/scroll-driven behaviour) is read through
`chrome-devtools-mcp`, Playwright, or the `--headless=new` CLI in §2. Use the
pane for **interaction only**: clicking, dismissing a consent banner, driving a
menu. Anything you read off the pane is a hypothesis; re-measure it through CDP
before it becomes a number.

## 1. Geometry first: cheapest and most diagnostic

Read the same boxes off both pages at the *same viewport* and diff the numbers.
This localises a fault in one pass, where a pixel diff only tells you a region
is wrong.

```js
// run on each page, same viewport, then compare the two tables
(() => {
  const b = s => { const e=document.querySelector(s); if(!e) return 'missing';
    const r=e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}`; };
  return ['section.hero','.grid','.card','h1','.btn']   // your real selectors
    .reduce((o,s)=>(o[s]=b(s),o), {docHeight: document.body.scrollHeight,
                                   nodes: document.querySelectorAll('*').length});
})()
```

**Read `nodes` before anything else**: it is the cheapest check in this file and
it disqualifies every measurement under it. A mirror at roughly **2× the
reference's node count means hydration did not complete**, not that the mirror is
broken: Framer emits every breakpoint variant server-side and switches them with
`display: contents` / `display: none`, so the un-hydrated tree still carries all
of them. Measured on one site: **13,228 nodes un-hydrated vs 7,042 hydrated**.
Fix the runtime before chasing a single box delta.

Then chase every non-zero height delta to its source before rendering anything.
A 12px card delta is a real bug; it will not "average out" in the pixel score.

## 2. Pixel diff: headless, identical conditions

Both captures must use the same browser build, viewport, and device scale, or
you are measuring your capture setup instead of your build.

Serve the mirror with `scripts/serve.py`, not `python3 -m http.server`. See
`mirror.md` step 5. A headless capture can pass on the stock server while the
interactive page collapses, so a clean score here proves nothing if the mirror
was served wrong.

```bash
python3 serve.py --directory site --port 8791 &

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
shoot () {   # url out [wait_ms]
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=1 --window-size=1280,900 \
    --virtual-time-budget="${3:-12000}" --screenshot="$2" "$1"
}
shoot "https://reference.example" ref.png
shoot "https://reference.example" ref2.png    # second independent load — the ceiling
shoot "http://localhost:8791/"    clone.png
```

**Long pages: shoot bands at their own scroll offsets, not one `fullPage`.**
Fire-once reveals gated at ~84% of the viewport never trigger in a full-page
capture, so everything below the first fold lands at `opacity: 0.001`, measured
on a 22,789px page. Scroll to each band, settle longer than the longest stagger
on the page (that site's longest character stagger ran 2.65s; **3.2s** was
enough), then capture. Score band by band.

### Score per region, against that region's own ceiling

A single blended number hides a broken region. Never emit one.

```python
from PIL import Image, ImageChops

# Regions are horizontal bands: fixed strips, or the §1 section boxes read off
# the reference. Crop consent/cookie UI off BOTH sides by excluding its band.
BANDS = [('hero', 0, 756), ('marquee', 756, 1180), ('features', 1180, 2040)]
W = 1280

def band(a, b, top, bot):
    r = Image.open(a).convert('RGB').crop((0, top, W, bot))
    c = Image.open(b).convert('RGB').crop((0, top, W, bot))
    d = ImageChops.difference(r, c)
    px = list(d.getdata()); n = len(px)
    mean = sum(sum(p) for p in px) / (n * 3)
    return (100 - mean/255*100,
            sum(1 for p in px if max(p) <= 16) / n * 100,
            max(max(p) for p in px), d)

for name, top, bot in BANDS:
    sim, w16, mx, d = band('ref.png', 'clone.png', top, bot)
    ceil, _, _, _   = band('ref.png', 'ref2.png',  top, bot)   # this band's own ceiling
    flag = '  <-- WORST' if ceil - sim > 0.5 else ''
    print(f"{name:12} {sim:6.2f}%  ceiling {ceil:6.2f}%  gap {ceil-sim:+.2f}"
          f"  within16 {w16:6.2f}%  maxdelta {mx:3}{flag}")
    d.convert('L').point(lambda v: min(255, v*4)).save(f'diffmap-{name}.png')   # 4x amplified
```

Print the whole table and flag the worst band. On one mirror the marquee band
scored **98.02%** while every band outside it was pixel-identical: **99.96% and
100.00% against 100.00% ceilings**. A page mean would have reported one number
and hidden both facts.

Sanity-check the result before trusting it: confirm `ref.png` and `clone.png`
have different hashes. Identical files mean both shots hit the same URL, and
100% is then meaningless.

Then **look at the `diffmap-*.png`**. Black is agreement. What they show you:

- Ghosted/doubled text → a vertical offset above it. Fix the offset, not the
  text, **unless the band holds a marquee, ticker, or loop**, where this is the
  signature of animation phase. Run the two-wait test below before touching layout.
- A crisp edge outline → a size or border delta on that box.
- A whole band uniformly speckled while its neighbours are black → motion phase.
  Two-wait test.
- Faint noise over photos → decode variance **or the wrong image variant**. Do
  not dismiss it; settle it positively in §3.

### Ceilings: what a region cannot beat

A band below 100% is not automatically a defect. Establish the ceiling per band
first, from `ref.png` vs `ref2.png`, and score against that number rather than
against 100%. Four causes put a ceiling below 100%: animation, a live counter,
lazy-load timing, and a randomised per-load variant.

**Randomised per-load variants.** Some sites pick a visual variant at random on
each load, so the reference is not self-consistent with itself. Two screenshots
cannot detect this: with 5 variants, two loads collide 20% of the time and
report a false 100% ceiling. Instead, load the reference **3-5 times and read the
runtime state**: `Object.keys(window)` for a project-named global first. Where
the runtime exposes a **writable params object, pin it identically on both sides
before capturing**. One site exposes `VARIANT`, `IS_WIREFRAME_ANIMATING` and
`SHOW_HELMET_PERMANENTLY`, and its helmet livery has 5 variants. Whether you
pinned it or measured around it, say which in the report's Unresolved row.

**Motion residual: the two-wait test.** When a band sits below its ceiling and
contains continuous motion, capture **one side against itself at two different
waits** and diff those:

```bash
shoot "http://localhost:8791/" a.png 12000
shoot "http://localhost:8791/" b.png 13000
# then: band('a.png','b.png', top, bot)  for that band only
```

If that score reproduces the cross-side score, the residual is phase, and that
residual **is** the ceiling for that band. Measured on the marquee above: **98.02%**
reference-vs-mirror, **98.07%** same side at 12s vs 13s, **99.84%** same side at
the same wait. Record it in the report's Unresolved row as measured phase, not
as a defect.

A band far below its ceiling is a real defect *unless the two-wait test
reproduces it*. A band matching its ceiling is finished. Chasing a band past its
ceiling measures animation phase, not fidelity.

## 3. Assets: verify positively, not by absence of errors

A clean network log does not mean the right assets loaded. Both known traps
answer **HTTP 200** and leave no error anywhere:

- **`vary: Accept`**: `framerusercontent.com` serves AVIF to Chrome's
  `image/avif,image/webp,…` and PNG to `Accept: */*`, which is what a default
  mirroring fetch sends. Same URL, different bytes, no failure.
- **Query strings**: `?scale-down-to=512&width=1024` and `?width=1024` are
  different images sharing one path. Strip the query and every srcset candidate
  collapses onto the full-size original, silently.

Neither shows up in §2: the residual is 1-2/255, well inside the ≥90%-within-16
target, and it reads as the "faint noise over photos" the diffmap list used to
tell you to ignore.

So check positively. The same probe on both sides, exact match required:

```js
// reference and mirror, same viewport, after a full scroll pass
[...document.images]
  .map(i => [i.currentSrc.split('/').pop(), i.naturalWidth, i.naturalHeight])
  .sort()
```

A `naturalWidth`/`naturalHeight` mismatch is a wrong variant, the query-string
trap. It is cheaper than a pixel diff and catches this exactly.

Then confirm the format, per asset:

```bash
ACC='image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
curl -sI "$ASSET_URL" -H "Accept: $ACC" | grep -i '^content-type'   # what Chrome is served
curl -sI "$ASSET_URL" -H 'Accept: */*'  | grep -i '^content-type'   # what a naive fetch took
```

Two different content-types means the CDN varies on Accept and your mirror
holds the wrong bytes. Compare the mirror's served `content-type` against the
reference's Chrome-Accept one for every image. Content-type mismatches and
decode-size mismatches both gate at 0.

## 4. Deltas that keep recurring

Check these first; between them they account for most of the gap.

| Symptom | Cause |
|---|---|
| Mirror has ~2× the reference's node count | Hydration never completed (§1, not a geometry bug) |
| Everything below a block is offset | Unreset UA margin: `<p>`/`<h*>` `margin-bottom` is the usual one |
| Sibling cards differ in height from the reference | Reference grid/flex lets them **stretch**; you set `align-items: start` |
| A list is taller by ~2× its padding | You modelled the rule as `.x + .x`; the reference uses `.x` plus `:first-child`/`:last-child` overrides |
| One button taller than its neighbour | Flex `align-items: stretch` inflating it to match a bordered sibling |
| One band 1-2 points down, neighbours at ceiling | Motion phase: two-wait test, §2 |
| Right size, wrong feel | Easing or gradient *type* guessed: a linear gradient read as radial, or a token name assumed |

## 5. Stop condition

Stop when the numbers stop moving, not when the page looks fine. Two or three
rounds is normal. A band sitting at its own ceiling is done even at 98%; a band
below its ceiling is not done even when the page mean looks healthy. If a delta
survives two rounds and the two-wait test does not reproduce it, it is being
caused by a rule you have not read yet. Go back and read the reference's actual
CSS for that selector rather than adjusting values by feel.


## 6. Fonts: the gate that is two-sided

A Match with an unverified font is not done: the wrong face changes every wrap
and box height on the page. Run `scripts/font-gate.js` on the **reference and
the mirror**, same viewport, and require the two sides to **agree**: equal
`document.fonts.size`, the same `check()` per family/weight, canvas widths
within ~1px. A family `false` on *both* sides is declared in a fallback stack
and never painted on that page: a pass, not a defect. onefin measured 67 faces
on both sides with `Inter` and `Fragment Mono` false on the reference itself;
demand an absolute `true` there and a byte-accurate mirror fails its own gate.

### The four traps, each observed in practice

1. `@font-face` rules often live in an **inline `<style>` block**, not the
   linked CSS. A rewriter that only processes stylesheets and `src=`
   attributes leaves those URLs pointing at the origin. Sweep *every* origin URL
   in the final document, inline styles included.
2. Cross-origin font loads are **CORS-blocked**. A local page requesting fonts
   from the reference's origin gets a silent fallback, not an error dialog.
3. **Computed `fontFamily` lies.** It echoes the *requested* family even while a
   fallback renders, so "the styles say Bricolage" proves nothing.
4. **SRI voids a rewritten stylesheet.** A `<link>` carrying
   `integrity="sha384-…"` stops loading the moment you rewrite its `url()`s:
   the bytes no longer hash, so the browser drops the **entire** sheet with no
   console error. The symptom is a page rendering in Times with
   `document.fonts.size === 0`. `scripts/build.py` strips `integrity` and
   `crossorigin` automatically, but the strip is not the check: through that
   whole failure `document.fonts.check()` kept returning **true**.

### Why the canvas A/B is not optional

`check()` is weaker than it looks. Measured in `scripts/tests/test_font.py`, it
returns **true for a family that was never declared anywhere**: the spec asks
whether the text can be rendered, and a fallback always can. So `check()` cannot
detect an absent face in any case, not merely the SRI one.

The A/B arm is measured rather than inferred: one real headline string in the
requested face against a forced `sans-serif`, on an offscreen canvas.
phenomenonstudio's probe read 1183.3px vs 1208.3px; a gap that size is the real
face painting. Identical widths on the mirror where the reference shows a gap
mean the fallback is rendering, whatever the styles claim.

**Probe the display face, not the UI sans.** Framer, and anything else shipping
metric-compatible fallbacks, registers `<Family> Placeholder` faces (Satoshi
Placeholder, Inter Placeholder, Figtree Placeholder) matched to the real font's
metrics *by design*, so an A/B against the page's own computed stack returns
identical widths on a page where the font is genuinely loaded. Take the largest,
most distinctive family in the type census as the probe target, and force
`sans-serif` on the control arm rather than dropping the first family off the
stack.

## Scrolling a page in a harness: always `behavior: "instant"`

Any script that walks a page to fire reveal gates, load lazy images or settle
scroll-linked state must scroll instantly:

```js
scrollTo({ top: y, behavior: "instant" });
```

A plain `scrollTo(0, y)` loop against a page with `html { scroll-behavior:
smooth }` animates every step, never catches up, and stops somewhere in the
middle of the document. Everything below that point is never revealed, so the
capture comes back with correctly-spaced but empty sections and the obvious
reading is that the reveal gate is broken. Measured once at full cost: 6 of 13
gates fired, the remaining 7 reported `opacity: 0`, and the page was correct in
a real browser throughout.

Read blank-but-height-reserved sections as a scrolling failure first, and the
gate second.
