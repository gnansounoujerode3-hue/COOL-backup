/**
 * Worked example: 16:9 capability ad -> 9:16, as a re-layout.
 *
 * Library entry: library/systo-you-own-the-ai.md (fidelity: spec)
 * Every box, tilt and colour below came from `measure.mjs`. Nothing is estimated.
 *
 *   node recut-9x16.mjs <source.png> <out.png>
 *
 * The move: in the source the four capability cards sit in a right-hand column
 * beside the hero. At 9:16 there is no right-hand column, so they stack below it.
 * That is why a crop cannot do this job.
 */
import { lift, fadeEdges, bg, surface, place, heightOf } from '../../scripts/lib.mjs'

const SRC = process.argv[2]
const OUT = process.argv[3] ?? 'systo-9x16.png'
if (!SRC) { console.error('usage: recut-9x16.mjs <source.png> [out.png]'); process.exit(1) }

const W = 1080, H = 1920
const SHELL = '#fef8f2'   // sampled from the real card interior, not a brand token

// Measured tilt per card: the perspective compounds down the stack.
const CARDS = [
  { tilt: 0.00, icon: [1372, 392, 96, 96],  text: [1471, 380, 244, 120], logos: [1686, 386, 252, 120] },
  { tilt: 0.72, icon: [1370, 552, 96, 96],  text: [1471, 542, 234, 124], logos: [1680, 552, 260, 124] },
  { tilt: 2.39, icon: [1362, 716, 96, 96],  text: [1461, 708, 239, 126], logos: [1670, 724, 272, 128] },
  { tilt: 4.53, icon: [1344, 878, 100, 100], text: [1443, 878, 244, 124], logos: [1654, 894, 280, 134] },
]

const layers = []
const add = (name, input, left, top) => layers.push({ name, input, left, top })

const field = bg(W, H, {
  stops: [[0, '#faf3ea'], [0.2, '#f9f2e9'], [0.55, '#f6ebde'], [1, '#eee1d4']],
  glow: { cx: '52%', cy: '60%', r: '52%', color: 'rgba(255,138,60,0.15)', fade: 'rgba(255,138,60,0)' },
})

add('logo', await lift(SRC, [30, 40, 240, 80], { width: 208, feather: 8 }), 58, 60)

// Headline and subline are cut separately and kept clear of x>1340: the first
// capability card overlaps that band and otherwise bleeds a white block in.
const headline = await lift(SRC, [590, 92, 868, 260], { width: 916, feather: 18 })
add('headline', headline, Math.round((W - 916) / 2), 142)
const headEnd = 142 + await heightOf(headline)

const subline = await lift(SRC, [682, 340, 664, 64], { width: 648, feather: 16 })
add('subline', subline, Math.round((W - 648) / 2), headEnd + 6)
const subEnd = headEnd + 6 + await heightOf(subline)

// Hero: cropped tighter than the source framing, because vertical wants the
// operator and the console rather than the empty room beside them. Feathered top
// and bottom so it bleeds into the field instead of ending on a seam.
const hero = await fadeEdges(
  await lift(SRC, [180, 400, 1060, 752], { width: W, feather: 0 }),
  { top: 0.06, bottom: 0.26 })
const heroTop = subEnd + 18
const heroH = await heightOf(hero)
add('hero', hero, 0, heroTop)

// Cards: surfaces rebuilt at the sampled colour, contents lifted and de-tilted.
const X = 48, CW = W - X * 2, CH = 146, GAP = 20
let y = heroTop + heroH - 34
for (const [i, c] of CARDS.entries()) {
  add(`card${i}.surface`, surface(CW, CH, SHELL, 33), X, y)
  add(`card${i}.icon`, await lift(SRC, c.icon, { width: 88, feather: 0 }), X + 32, y + Math.round((CH - 88) / 2))
  const text = await lift(SRC, c.text, { tilt: c.tilt, width: 312, feather: 12 })
  add(`card${i}.text`, text, X + 148, y + Math.round((CH - await heightOf(text)) / 2))
  const logos = await lift(SRC, c.logos, { tilt: c.tilt, width: 302, feather: 12 })
  add(`card${i}.logos`, logos, X + CW - 302 - 26, y + Math.round((CH - await heightOf(logos)) / 2))
  y += CH + GAP
}

console.log(`hero ${heroTop}..${heroTop + heroH} | cards end ${y - GAP} / ${H}`)
console.log('wrote', await place(field, layers, OUT, { w: W, h: H }))
