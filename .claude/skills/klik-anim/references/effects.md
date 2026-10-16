# Effect & finish recipes — the A13 catalogue

Load this when building any treated/textured element. Each recipe: what it
signals, the mechanics, params, cost, and when NOT to use it. **Every recipe
below was render-verified in an isolated POC comp (A9)** — the parameter bands
come from looking at real frames. Adapt names/structure to the project; verify
current API shapes against `remotion-docs` if unsure.

## Laws that govern every effect here

- **Deterministic always (A0).** Every seed derives from an element id or
  Remotion's `random("seed")` — never `Math.random()`. "Animated" noise means
  the seed or params are a function of `useCurrentFrame()`.
- **Define once.** Effects live in `src/effects/` as parameterized components/
  hooks, imported everywhere — the `motion.ts` rule applied to finish.
- **Budgeted like blur (A5).** `feTurbulence` + `feDisplacementMap` cost like
  blur layers: cap ~4–6 concurrently filtered elements at 1080p, fewer at 4K.
  Static-seed filters are cheap (the browser caches the result); per-frame
  re-seeding (grain, boil) is the expensive kind — spend it deliberately.
- **On top of craft, never instead (A13).** Compute proper thin-peak motion
  first; treatments sample, jitter, or texture the *result*. And treated
  frames still pass the squint test (A10) — a busy texture must not steal
  rank-1 attention from the focal element.
- **Stack order matters.** Per element: silhouette → fill/texture → edge
  treatment (cutout/sticker) → shadow → boil/jitter. Fullscreen: grain and
  scanlines go LAST, over everything, so they unify the layers beneath.
- **Render a still of every new effect before using it in scenes (A9).**

## Choosing a stack — style words → treatments

Offer these named stacks in the C2 interview; they are starting points, not
cages. One stack per video — mixing stacks reads as two different pieces.

| Style words | Stack (in order) |
|---|---|
| **clean-flat** (deliberate!) | nothing but crisp vectors + shadow discipline + fine grain 0.03 |
| **grain-only / premium tech** | glow bloom → chromatic aberration at peaks only (A5) → grain 0.04–0.06 |
| **paper / cutout / hand-made** | paper texture fill → cutout edge + hard shadow → boil on heroes → grain |
| **riso / print / zine** | 1–2 ink duotone → halftone pattern → misregistration → heavy grain |
| **boil / hand-drawn** | rough strokes → boil everything → wobble underlines → grain |
| **stop-motion / craft** | cutout + paper → stop-motion sampling (2s) → per-pose jitter → grain |
| **retro broadcast / VHS** | scanlines → aberration 1–2px constant → wave-warp accents → heavy grain |
| **liquid / dreamy** | wave warp on shapes → glow → light leak drift → soft grain |
| **sticker / collage** | die-cut outline → cutout shadow → micro-rotation scatter → grain |

---

## 1. Film grain (fullscreen)

**Signals:** analog warmth; unifies disparate layers; kills the "too clean"
digital look. The single cheapest premium upgrade — near-universal.

```tsx
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.1 }) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 3; // fresh grain every 2f, 3-pose loop
  const fid = `grain-${seed}`;
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <svg width="100%" height="100%">
        <filter id={fid}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2"
            seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
          <feComponentTransfer>
            <feFuncR type="linear" slope="2.6" intercept="-0.8" />
            <feFuncG type="linear" slope="2.6" intercept="-0.8" />
            <feFuncB type="linear" slope="2.6" intercept="-0.8" />
            <feFuncA type="linear" slope="0" intercept="1" />
          </feComponentTransfer>
        </filter>
        <rect width="100%" height="100%" filter={`url(#${fid})`} />
      </svg>
    </AbsoluteFill>
  );
};
```

The three post-turbulence lines are load-bearing (render-verified): raw
turbulence is **RGB confetti** (desaturate it), **mid-gray mush** (the
contrast-boost transfer spreads it), and has a **noisy alpha channel** that
makes the grain vanish (`feFuncA` forces it solid). Without them the layer is
invisible at any sane opacity.

**Params:** opacity 0.05–0.15 (~0.1 sweet spot; lower on dark scenes — it
lifts blacks); re-seed every 2f. Grain reads in the midtones — it is nearly
invisible over white surfaces, which is correct film behavior; don't chase it
with opacity. **Don't:** exceed ~0.15 over dense body text; forget it's a
per-frame filter (one instance per comp, mounted last).

**One-clock rule (render-verified):** in a piece with a boil identity, the
grain reseeds on the SAME held step as every other textural layer (§5) —
grain ticking at its own rate reads as two competing effects. **Poster-grain
variant:** the gradient-field ground (§12) runs this recipe hot (overlay
~0.5) as a designed surface, not a finish. **Cost warning (measured):**
stepped full-frame grain destroys temporal compression — a 33s 1080p piece
jumped ~6× in file size; grain-heavy boil work needs a delivery CRF/bitrate
plan, not the default.

## 2. Line boil / wobble

**Signals:** hand-drawn, alive, Duolingo/King-of-the-Hill energy. The
strongest single "a human made this" cue on flat vectors.

```tsx
// Wrap any element; 3 wobble poses cycling at ~8–10fps.
export const Boil: React.FC<{ children: React.ReactNode; amount?: number; id: string }> =
  ({ children, amount = 2.5, id }) => {
    const frame = useCurrentFrame();
    const pose = Math.floor(frame / 3) % 3; // hold each pose 3f
    return (
      <>
        <svg width="0" height="0"><filter id={`boil-${id}-${pose}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="2"
            seed={pose * 7 + 1} />
          <feDisplacementMap in="SourceGraphic" scale={amount} />
        </filter></svg>
        <div style={{ filter: `url(#boil-${id}-${pose})` }}>{children}</div>
      </>
    );
  };
```

**Params:** `amount` 1.5–4 at 1080-base (higher = rougher); 3f hold = 8fps
boil (2f = frenetic, 4f = lazy). **Don't:** boil small body text (legibility
dies) or more than the budget allows; at dial-1 pacing keep amount low.

**Letterform boil — the type variant (render-verified):** to melt DISPLAY
TYPE into a textured ground, boil it with long single-octave waves so each
held cel is a gentle bend of the whole letterform, not an edge crinkle:
`baseFrequency 0.003 0.0062 · numOctaves 1 · scale ~6.5`, 4 cels
(`seed = base + (floor(f/3) % 4) * 31`) held 3f and SNAPPED — plus a
generous filter region (x −18% w 136% · y −36% h 172%) so ascenders,
descenders, and travel don't clip. Failed model, kept as a warning:
**continuously drifting the field** (feOffset or baseFrequency driven per
frame) — constant sub-pixel edge crawl that reads as jagged jitter, not
life. Never interpolate between cels. Trap (A5): never put this filter on
a container whose children use perspective transforms — it flattens them
(card-flip devices); there, let the shared grain carry the texture.

## 3. Paper cutout

**Signals:** collage, craft, tactile. Three tells make it read: a rough
displaced edge, a HARD shadow (paper sits just above the page), and a
slightly-off resting rotation (A4).

```tsx
export const Cutout: React.FC<{ children: React.ReactNode; id: string }> = ({ children, id }) => {
  const rot = (random(`cut-rot-${id}`) - 0.5) * 2.4; // ±1.2° resting tilt
  return (
    <>
      <svg width="0" height="0"><filter id={`cut-${id}`}>
        <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3"
          seed={Math.floor(random(`cut-seed-${id}`) * 100)} />
        <feDisplacementMap in="SourceGraphic" scale={6} />
      </filter></svg>
      <div style={{
        filter: `url(#cut-${id}) drop-shadow(3px 5px 0px rgba(25,15,5,0.28))`,
        transform: `rotate(${rot}deg)`,
      }}>{children}</div>
    </>
  );
};
```

**Params:** edge `scale` 4–10; shadow offset 2–6px with **0–1px blur** (a soft
blur breaks the illusion — cutouts cast hard shadows). Static seed per
element so the edge is stable; add `Boil` on top only for the full craft look.
**Don't:** cutout tiny elements (edge noise swallows them).

## 4. Wave warp

**Signals:** liquid, flags, dream sequences, "alive" banners.

```tsx
const frame = useCurrentFrame();
const bf = 0.008 + Math.sin(frame / 13) * 0.002; // slow deterministic drift
// <filter id="wave">
//   <feTurbulence type="turbulence" baseFrequency={`${bf} 0.02`} numOctaves="1" seed="7" />
//   <feDisplacementMap in="SourceGraphic" scale={18} xChannelSelector="R" yChannelSelector="G" />
// </filter>
```

**Params:** `scale` 10–30 (displacement px); drive `baseFrequency` or `scale`
through the frame for motion. **Don't:** warp focal body text mid-read (A5's
crisp-focal law) — warp it in/out, hold it readable. And don't DRIFT a warp
on parked type — that's §2's recorded failed model (edge crawl); parked type
wants held boil cels, not a moving field.

## 5. Stop-motion sampling

**Signals:** handcrafted, Laika/Aardman charm. **The law: sample AFTER
easing** — compute full thin-peak motion (A1), then quantize the clock.

```tsx
const frame = useCurrentFrame();
const held = Math.floor(frame / 2) * 2; // "on 2s" → 12fps feel at 24fps
const x = interpolate(held, [10, 26], [0, 420], CLAMP); // eased curve, held clock
// fresh micro-offset per held pose = the hand that repositioned the puppet:
const j = (s: string) => (random(`${s}-${held}`) - 0.5);
const style = { transform: `translate(${x + j("jx") * 1.5}px, ${j("jy") * 1.5}px) rotate(${j("jr") * 0.6}deg)` };
```

**Params:** on 2s (÷2) for the classic feel, 3s (÷3) for lazier charm; jitter
±1–2px / ±0.3–0.6° per pose. Apply per-element or to a whole scene group.
**Don't:** quantize the camera at dials 4–5 (nauseating); mix sampled and
smooth elements in one shot without meaning it.

**The one-clock rule (render-verified):** when a piece commits to a boil,
EVERY textural layer shares one held step — type-warp cels (§2), grain
plates (§1), and ambient color fields (§12) all snap on the same
`floor(f/N)`, with ambient motion computed as smooth curves then SAMPLED
at the held frame. Proof standard: frame-diff within a step must be
pixel-identical (measured 0.0); at the step boundary the whole surface
jumps as one. **Hybrid rates ARE the look:** ground world on 3s (~10fps)
under element motion at full frame rate — quantize the world, never the
focal action, unless the style explicitly puppets everything.

## 6. Riso / halftone print

**Signals:** zine, indie print, screen-print. The tell is **misregistration**
— ink layers 1–3px off — plus visible dot/line pattern and limited inks.

```tsx
// Ink = the artwork silhouette in ONE flat color. Two inks, multiply, offset:
<Art color={theme.color.accent} />
<Art color="#1d3557" style={{
  transform: `translate(${1.5 + random("mis-x") * 1.5}px, ${-1 - random("mis-y")}px)`,
  mixBlendMode: "multiply", opacity: 0.85,
}} />
// Halftone fill: mask the art over an SVG dot pattern
// <pattern id="dots" width="6" height="6" patternUnits="userSpaceOnUse">
//   <circle cx="3" cy="3" r="1.6" /></pattern>
```

**Params:** 1–2 inks max (that's the medium); misregistration static + seeded,
never animated (it's a printing error, not a wobble). Pair with heavy grain.
**Inks must be mid-value and translucent** (render-verified): two dark
saturated inks multiply to near-black sludge — keep the top ink at 0.6–0.8
opacity and prefer lighter ink colors so the overlap stays a colorful third
tone. **Don't:** use more than 2–3 colors — full palette kills the print
story.

## 7. Texture fills

**Signals:** paper, canvas, cardboard — surfaces with a past. Real scans beat
procedural (A13: source > draw): pull 1–2 seamless textures into
`public/textures/`, then blend over flat fills.

```tsx
<div style={{ position: "absolute", inset: 0, backgroundImage: `url(${staticFile("textures/paper.jpg")})`,
  backgroundSize: "1024px", mixBlendMode: "multiply", opacity: 0.35, pointerEvents: "none" }} />
```

**Params:** multiply for shadow-texture on light fills, overlay for both-ways;
opacity 0.2–0.5. Tile at native size — never stretch (A13). **Don't:** apply
one giant texture over everything *instead of* per-surface — it reads as a
screen overlay, not material (fullscreen texture is grain's job).

No scan available? This procedural paper renders correctly (verified):
```xml
<filter id="p">
  <feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="5" seed="11"/>
  <feColorMatrix type="saturate" values="0"/>
  <feComponentTransfer>
    <feFuncR type="linear" slope="0.22" intercept="0.86"/>
    <feFuncG type="linear" slope="0.22" intercept="0.86"/>
    <feFuncB type="linear" slope="0.22" intercept="0.86"/>
    <feFuncA type="linear" slope="0" intercept="1"/>
  </feComponentTransfer>
  <feBlend in2="SourceGraphic" mode="multiply"/>
</filter>
<rect width="1024" height="1024" fill="#f4ead8" filter="url(#p)"/>
```
The explicit `fill` on the filtered rect is **mandatory** — an SVG rect with
no fill is BLACK, and a black source multiplies the whole texture to mud (a
render-found bug, invisible in code).

## 8. Die-cut sticker

**Signals:** playful, chat/social, collage-adjacent.

```tsx
// Fat white border = the same art stacked behind itself with a thick stroke.
<svg viewBox="…">
  <use href="#art" stroke="#fff" strokeWidth={14} strokeLinejoin="round" fill="#fff" />
  <use href="#art" />
</svg>
// + drop-shadow(0 4px 0 rgba(0,0,0,0.18)) + ±1° resting rotation (A4)
```

**Params:** border 8–18px at 1080-base, `strokeLinejoin="round"` mandatory.
**Don't:** outline text letter-by-letter (outline the word's group shape).

## 9. Glow bloom + chromatic aberration

Already law-bounded in A5 (aberration ≤2px, never on crisp focal body text,
bold only at transition peaks). Compact mechanics:

```tsx
// Bloom: a blurred, brightened copy UNDER the crisp original.
<div style={{ filter: "blur(12px) brightness(1.6)", opacity: 0.55 }}>{art}</div>
<div>{art}</div>
// Aberration: two channel-tinted ghosts, offset opposite ways, screen blend.
<Ghost tint="red"  dx={-1.5} /> <Ghost tint="cyan" dx={1.5} />
```

**Don't:** persistent strong aberration outside VHS looks; glow on more than
the focal + one echo (A3).

## 10. Textured reveals (brush / tear masks)

**Signals:** organic entrances — the anti-cheap-fade (A3) for craft looks.
Displace the **mask**, not the artwork: a wipe whose edge is torn paper or a
dry brush stroke.

```tsx
<mask id="tear">
  <rect x={interpolate(t, [0, 1], [-W, 0])} width={W} height={H} fill="#fff"
    filter="url(#cut-edge)" /> {/* same displacement filter as Cutout */}
</mask>
<g mask="url(#tear)">{scene}</g>
```

**Params:** drive `t` with the standard `EASE` (A1); edge roughness = the
cutout filter's `scale`. **Don't:** let the rough edge linger — it's a
transition, the landed frame is clean.

## 11. Inset wipe (the plain reveal primitive)

**Signals:** nothing on its own — it's the untreated base that #10 dresses,
and the cheapest way to satisfy **A15**. `clip-path: inset(top right bottom
left)`: each value eats in from that side. Paint-level, so it costs nothing
and is A7-safe (not a layout property).

Both halves of a boundary run the **same expression in opposite directions**,
which is what makes the origin shared rather than merely adjacent:

```tsx
const close = interpolate(t, [0, 1], [0, 100], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
const open  = interpolate(t, [0, 1], [100, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

<div style={{clipPath: `inset(0 0 ${close}% 0)`}}>{outgoing}</div> {/* collapses to the top edge */}
<div style={{clipPath: `inset(0 0 ${open}% 0)`}}>{incoming}</div>  {/* grows from the same edge */}
```

The second use is an in-place change without a crossfade (A3) — duplicate the
element, clip the copy, sweep the clip across it:

```tsx
<span style={{color: BASE}}>{word}</span>
<span style={{color: ACCENT, position: 'absolute', inset: 0,
              clipPath: `inset(0 ${100 - p}% 0 0)`}}>{word}</span>
```

**Params:** drive `t` with the standard `EASE` (A1); overrun the outgoing a few
frames past the cut and let paint order put it on top (A15). **Don't:** stop
short of a full 0/100 — a wipe that resolves to 28% leaves a smudge behind the
incoming line and reads as stuck, not handed off. And don't let it become every
cut's default: one signature motif (A3), varied per use (A14).

## 12. Flowing gradient-field ground (the poster ground)

**Signals:** editorial poster, print-like, soft color energy under ink
type — the light-ground reference look: large organic color fields, heavy
unifying grain, no glow anywhere.

```tsx
// light base + 5–7 large radial-gradient blobs + hot grain (§1) on top
const BLOBS = [ // color, center, radius, base opacity, phase — spread hues
  { c: "#3e5fb8", x: 620, y: 380, r: 430, o: 0.6, p: 0 }, /* + 5 more */
];
// per blob: 3-stop radial gradient (o → 0.55·o at 62% → 0 at edge);
// drift ±88/66px (periods ~71/83f), radius ±9%, opacity 0.78 ± 0.22 —
// computed smooth, SAMPLED on the boil step (§5 one-clock):
const fq = Math.floor(f / 3) * 3;   // then use fq in every sinusoid
```

**Params:** base near-white with a temperature (`#eae3e5`-class); 5–7
blobs, r 330–470 at 1080-base, base opacity 0.4–0.6; type is INK
(`#262230`-class) with NO glow — the shared grain (§1 hot variant) plus a
letterform boil (§2) is what fuses figure into ground. Blob motion stays
ambient amplitude: it must lose to the focal move instantly (A10).
**Don't:** park crisp focal copy over an accent blob at full strength
(contrast reserve, A10); add glow back "for pop" — this ground replaces
glow as the energy carrier.

## Quick extras (one-liners, same laws apply)

- **Long shadow:** ~24 stacked copies translated (i, i) px in ONE solid darker color at full opacity — flat-design depth. (Verified: stacked low-alpha copies blur into smudge; the color must be solid.)
- **Duotone:** `feColorMatrix` to luminance → map via two-stop gradient (`feComponentTransfer`).
- **Scanlines:** `repeating-linear-gradient(0deg, transparent 0 2px, rgba(0,0,0,.12) 2px 3px)` overlay + 1px constant aberration.
- **Light leak:** big radial-gradient blob, `screen` blend, drifting on a slow sine (frame-driven), opacity ≤0.25.
- **Wobble underline / circle:** hand-drawn accent strokes = rough `path` + `Boil` + draw-on via `strokeDashoffset` with `EASE_OUT`.
