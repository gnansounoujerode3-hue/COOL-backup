import sharp from 'sharp'

/* Systo poster, papier-mache / torn-paper style. Authored, not assembled:
 * nothing here is lifted, every element is built.
 *
 * The mark is already papercraft geometry - three stacked bars and a beacon dot -
 * so the poster tears it out of pulp at hero scale.
 *
 * What separates papier-mache from flat vector, and the two things that took
 * three passes to get right:
 *
 *  - PULP must modulate the fill in pixel space. Overlay-blending a blurred noise
 *    layer does almost nothing: heavy blur collapses uniform noise to near-flat
 *    grey, and overlay against mid-grey is close to a no-op. Normalise each noise
 *    scale to unit standard deviation, then multiply the base colour by it.
 *  - THE FRINGE must share the colour path's own noise. A torn edge shows the
 *    pale core of the card, so the core layer has to be the same contour grown
 *    outward by a varying amount. Give it independent noise and it sinks inside
 *    the colour layer in places and the fringe disappears.
 *
 * Plus: two shadows (a tight contact one and a wide soft one, both warm brown -
 * paper never casts a black shadow on paper), and the sheet's tooth laid over
 * EVERYTHING at the end, type included, so the frame reads as one surface.
 */
const OUT = process.env.OUTDIR ? process.env.OUTDIR + '/poster.png' : 'poster.png'
const W = 1080, H = 1920, N = W * H
const M = 104

const SHEET = [237, 220, 196], CORE = [244, 234, 214], NOTCH = [234, 217, 191]
const INKHEX = '#251D14'
const EMBER = [255, 140, 78], FLARE = [253, 88, 54], DEEP = [216, 68, 36], HONEY = [255, 190, 60]
const hex = c => '#' + c.map(v => v.toString(16).padStart(2, '0')).join('')

/* ---- deterministic noise ------------------------------------------------ */
function mulberry32(a) {
  return () => {
    a |= 0; a = a + 0x6D2B79F5 | 0
    let t = Math.imul(a ^ a >>> 15, 1 | a)
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t
    return ((t ^ t >>> 14) >>> 0) / 4294967296
  }
}

/* Smooth 1D value noise. Cosine interpolation between control points keeps a tear
 * organic; per-vertex random gives spiky static instead. */
function wobble(n, feature, seed) {
  const r = mulberry32(seed)
  const ctrl = Math.ceil(n / feature) + 2
  const k = Array.from({ length: ctrl }, () => r() * 2 - 1)
  return Array.from({ length: n }, (_, i) => {
    const t = i / feature, i0 = Math.floor(t), f = t - i0
    const s = (1 - Math.cos(f * Math.PI)) / 2
    return k[i0 % ctrl] * (1 - s) + k[(i0 + 1) % ctrl] * s
  })
}

/* 2D value noise: a lattice of random values, smoothstep-bilinear interpolated.
 *
 * Written by hand rather than by upscaling a small image through sharp. libvips'
 * upscale interpolator leaves a period-3 residue in the result at every cell size
 * tried, and normalising to unit sd amplifies it into a visible scanline across
 * every filled shape (lag-1 row diff 12.9 against lag-3 of 0.9 - a dead giveaway,
 * since a clean field has no lag that stands out). Blurring full-res white noise
 * has the same problem for the same reason. Interpolating the lattice directly
 * has no periodic structure to leak. */
function field(cell, seed) {
  const w = Math.ceil(W / cell) + 3, h = Math.ceil(H / cell) + 3
  const r = mulberry32(seed), g = new Float32Array(w * h)
  for (let i = 0; i < w * h; i++) g[i] = r() * 2 - 1
  const f = new Float32Array(N)
  for (let y = 0; y < H; y++) {
    const fy = y / cell, y0 = Math.floor(fy), ty = fy - y0
    const sy = ty * ty * (3 - 2 * ty), r0 = y0 * w, r1 = r0 + w
    for (let x = 0; x < W; x++) {
      const fx = x / cell, x0 = Math.floor(fx), tx = fx - x0
      const sx = tx * tx * (3 - 2 * tx)
      const a = g[r0 + x0], b = g[r0 + x0 + 1], c = g[r1 + x0], d = g[r1 + x0 + 1]
      f[y * W + x] = (a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy
    }
  }
  let m = 0; for (let i = 0; i < N; i++) m += f[i]; m /= N
  let v = 0; for (let i = 0; i < N; i++) { const d = f[i] - m; v += d * d } v = Math.sqrt(v / N)
  for (let i = 0; i < N; i++) f[i] = (f[i] - m) / (v || 1)
  return f
}

/* Per-pixel grain, for texture too fine to want interpolation at all. */
function grain(seed) {
  const r = mulberry32(seed), f = new Float32Array(N)
  for (let i = 0; i < N; i++) f[i] = (r() - 0.5) * 3.464   // unit sd
  return f
}
/* Two octaves per scale. A single octave of value noise reads as distinct blobs -
 * mouldy rather than fibrous - because it has one feature size and nothing else. */
function fractal(octaves, seed) {
  const out = new Float32Array(N)
  octaves.forEach(([cell, w], k) => {
    const f = field(cell, seed + k * 101)
    for (let i = 0; i < N; i++) out[i] += f[i] * w
  })
  let m = 0; for (let i = 0; i < N; i++) m += out[i]; m /= N
  let v = 0; for (let i = 0; i < N; i++) { const d = out[i] - m; v += d * d } v = Math.sqrt(v / N)
  for (let i = 0; i < N; i++) out[i] = (out[i] - m) / (v || 1)
  return out
}
const lump = fractal([[34, 1], [15, 0.55]], 7)     // coarse pulp mass
const mottle = fractal([[7, 1], [3.2, 0.5]], 19)   // mid-scale pulp
const fibre = grain(23)                            // paper fibre

/* Vertical falloff, so a form reads as rounded mass rather than a flat cut-out. */
const shade = new Float32Array(H)
for (let y = 0; y < H; y++) { const t = y / H; shade[y] = 1.035 - 0.09 * t * t }

/* Colour x pulp, as raw RGB. Multiplicative, so the hue survives. */
function pulpFill(base, kL = 0.072, kM = 0.038, kF = 0.020) {
  const out = Buffer.alloc(N * 3)
  for (let y = 0, i = 0; y < H; y++) {
    const sv = shade[y]
    for (let x = 0; x < W; x++, i++) {
      const g = sv * (1 + kL * lump[i] + kM * mottle[i] + kF * fibre[i])
      out[i * 3] = Math.min(255, Math.max(0, base[0] * g))
      out[i * 3 + 1] = Math.min(255, Math.max(0, base[1] * g))
      out[i * 3 + 2] = Math.min(255, Math.max(0, base[2] * g))
    }
  }
  return out
}

const wrap = inner => `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${inner}</svg>`
const alphaOf = svg => sharp(Buffer.from(svg)).extractChannel(3).raw().toBuffer()
const grey1 = b => sharp(b, { raw: { width: W, height: H, channels: 1 } })
const cutTo = (rgb, mask) => sharp(rgb, { raw: { width: W, height: H, channels: 3 } })
  .joinChannel(mask, { raw: { width: W, height: H, channels: 1 } }).png().toBuffer()

/* ---- torn contours ------------------------------------------------------ */
/* Returns the colour contour and its core, sharing one noise field so the core is
 * always outside by a varying margin - that varying margin IS the torn fringe. */
function tornPair(x, y, w, h, { amp = 6.5, grow = 7, seed = 1, n = 520 } = {}) {
  const r = h / 2, cx0 = x + r, cx1 = x + w - r, cy = y + r, span = w - h
  const mass = wobble(n, 58, seed + 5), lo = wobble(n, 17, seed), hi = wobble(n, 5, seed + 977)
  const gv = wobble(n, 26, seed + 313), nick = wobble(n, 9, seed + 71)
  const A = [], B = []
  for (let i = 0; i < n; i++) {
    const u = (i / n) * (2 * span + 2 * Math.PI * r)   // arclength around the form
    let px, py, nx, ny
    if (u < span) { px = cx0 + u; py = y; nx = 0; ny = -1 }
    else if (u < span + Math.PI * r) {
      const a = (u - span) / r - Math.PI / 2
      nx = Math.cos(a); ny = Math.sin(a); px = cx1 + nx * r; py = cy + ny * r
    } else if (u < 2 * span + Math.PI * r) {
      px = cx1 - (u - span - Math.PI * r); py = y + h; nx = 0; ny = 1
    } else {
      const a = (u - 2 * span - Math.PI * r) / r + Math.PI / 2
      nx = Math.cos(a); ny = Math.sin(a); px = cx0 + nx * r; py = cy + ny * r
    }
    const d = mass[i] * amp * 0.9 + lo[i] * amp * 0.55 + hi[i] * amp * 0.22
    const fr = grow * (0.16 + 0.84 * (gv[i] * 0.5 + 0.5)) + nick[i] * 1.4 + 1.2
    A.push([(px + nx * d).toFixed(1), (py + ny * d).toFixed(1)])
    B.push([(px + nx * (d + fr)).toFixed(1), (py + ny * (d + fr)).toFixed(1)])
  }
  const path = p => 'M' + p.map(q => q.join(' ')).join('L') + 'Z'
  return { color: path(A), core: path(B) }
}

function tornRing(cx, cy, rad, { amp = 4.5, grow = 7, seed = 1, n = 320 } = {}) {
  const lo = wobble(n, 15, seed), hi = wobble(n, 4, seed + 31), gv = wobble(n, 21, seed + 77)
  const A = [], B = []
  for (let i = 0; i < n; i++) {
    const a = (i / n) * 2 * Math.PI, ca = Math.cos(a), sa = Math.sin(a)
    const d = rad + lo[i] * amp * 0.75 + hi[i] * amp * 0.3
    const fr = grow * (0.16 + 0.84 * (gv[i] * 0.5 + 0.5)) + 1
    A.push([(cx + ca * d).toFixed(1), (cy + sa * d).toFixed(1)])
    B.push([(cx + ca * (d + fr)).toFixed(1), (cy + sa * (d + fr)).toFixed(1)])
  }
  const path = p => 'M' + p.map(q => q.join(' ')).join('L') + 'Z'
  return { color: path(A), core: path(B) }
}

/* ---- assembly ----------------------------------------------------------- */
async function shadows(d, rot, about) {
  const g = off => wrap(`<g transform="rotate(${rot} ${about[0]} ${about[1]}) translate(${off[0]} ${off[1]})"><path d="${d}" fill="#000"/></g>`)
  const tint = async (svg, blur, o) => sharp({ create: { width: W, height: H, channels: 3, background: '#5E3214' } })
    .joinChannel(await sharp(Buffer.from(svg)).extractChannel(3).blur(blur).linear(o, 0).raw().toBuffer(),
      { raw: { width: W, height: H, channels: 1 } }).png().toBuffer()
  return [await tint(g([14, 30]), 26, 0.42), await tint(g([4, 9]), 6, 0.50)]
}

async function layers({ color, core }, rot, about, base) {
  const T = d => wrap(`<g transform="rotate(${rot} ${about[0]} ${about[1]})"><path d="${d}" fill="#000"/></g>`)
  const [wide, tight] = await shadows(core, rot, about)
  return [
    { input: wide }, { input: tight },
    { input: await cutTo(pulpFill(CORE, 0.040, 0.026, 0.020), await alphaOf(T(core))) },
    { input: await cutTo(pulpFill(base), await alphaOf(T(color))) },
  ]
}

/* A counter-notch is a HOLE, not a disc. It shows the sheet through the bar and
 * takes an inner shadow from the wall nearest the light; giving it a drop shadow
 * of its own made it read as a cotton ball stuck on top. */
async function hole(cx, cy, rad, seed) {
  const { color } = tornRing(cx, cy, rad, { seed, grow: 0 })
  const mask = await alphaOf(wrap(`<path d="${color}" fill="#000"/>`))
  const lip = await sharp(Buffer.from(wrap(`<g transform="translate(7 11)"><path d="${color}" fill="#000"/></g>`)))
    .extractChannel(3).blur(9).raw().toBuffer()
  const inner = Buffer.alloc(N), recess = Buffer.alloc(N * 3)
  for (let i = 0; i < N; i++) inner[i] = Math.max(0, mask[i] - lip[i]) * 0.5
  for (let i = 0; i < N * 3; i++) recess[i] = sheetBuf[i] * 0.955
  return [
    { input: await cutTo(recess, mask) },
    {
      input: await sharp({ create: { width: W, height: H, channels: 3, background: '#4A2610' } })
        .joinChannel(inner, { raw: { width: W, height: H, channels: 1 } }).png().toBuffer()
    },
  ]
}

const bar = (x, y, w, h, base, rot, seed) =>
  layers(tornPair(x, y, w, h, { seed }), rot, [x + w / 2, y + h / 2], base)
const dot = (cx, cy, rad, base, seed) =>
  layers(tornRing(cx, cy, rad, { seed }), 0, [cx, cy], base)

/* ---- the sheet ---------------------------------------------------------- */
const tooth = grain(41)
const sheetBuf = Buffer.alloc(N * 3)
for (let y = 0, i = 0; y < H; y++) {
  for (let x = 0; x < W; x++, i++) {
    // tooth, plus a soft vignette so the sheet reads as a lit object
    const dx = (x - W / 2) / (W / 2), dy = (y - H * 0.44) / (H * 0.56)
    const vig = 1 - 0.12 * Math.min(1, (dx * dx + dy * dy) ** 1.4)
    const g = vig * (1 + 0.016 * tooth[i] + 0.010 * fibre[i] + 0.014 * lump[i])
    for (let c = 0; c < 3; c++) sheetBuf[i * 3 + c] = Math.min(255, Math.max(0, SHEET[c] * g))
  }
}

/* ---- type: one left edge, ink printed on the sheet ---------------------- */
const type = Buffer.from(wrap(`
  <text x="${M}" y="228" font-family="Consolas, 'Courier New', monospace" font-size="25"
        letter-spacing="6.5" fill="${hex(FLARE)}">ARTIFICIAL INTELLIGENCE OPERATORS</text>
  <rect x="${M}" y="260" width="78" height="3" fill="${hex(FLARE)}"/>

  <g font-family="Arial Black, Arial, sans-serif" font-size="112" letter-spacing="-4" fill="${INKHEX}">
    <text x="${M}" y="420">Operators for</text>
    <text x="${M}" y="536">the AI you own.</text>
  </g>

  <text x="${M}" y="1466" font-family="Georgia, 'Times New Roman', serif" font-style="italic"
        font-size="40" fill="#6A5540">We run it. You keep it.</text>

  <g font-family="Segoe UI, Arial, sans-serif" font-size="28" fill="#7C6650">
    <text x="${M}" y="1538">Your tools, your accounts, your logins.</text>
    <text x="${M}" y="1580">A named operator drives them every day.</text>
  </g>

  <rect x="${M}" y="1716" width="${W - M * 2}" height="2" fill="${INKHEX}" fill-opacity="0.16"/>
  <text x="${W - M}" y="1786" text-anchor="end" font-family="Consolas, 'Courier New', monospace"
        font-size="26" letter-spacing="3" fill="${hex(DEEP)}">systo-ai.com/book</text>`))

const lockup = await sharp(process.env.BRAND_LOCKUP || 'brand/svg/systo-lockup-light.svg', { density: 400 })
  .resize({ width: 208 }).png().toBuffer()

// The sheet's tooth over everything, art and type alike.
const toothTop = Buffer.alloc(N * 4)
for (let i = 0; i < N; i++) {
  const v = Math.min(255, Math.max(0, 128 + tooth[i] * 28))
  toothTop[i * 4] = v; toothTop[i * 4 + 1] = v; toothTop[i * 4 + 2] = v; toothTop[i * 4 + 3] = 30
}

await sharp(sheetBuf, { raw: { width: W, height: H, channels: 3 } })
  .composite([
    ...await bar(150, 742, 700, 156, EMBER, -2.6, 11),
    ...await hole(266, 822, 44, 300),                       // counter-notch
    ...await bar(232, 928, 716, 156, FLARE, 1.6, 61),
    ...await bar(168, 1114, 690, 156, DEEP, -1.1, 131),
    ...await dot(792, 1190, 52, HONEY, 400),                // beacon
    { input: type },
    { input: lockup, left: M, top: 1742 },
    { input: toothTop, raw: { width: W, height: H, channels: 4 }, blend: 'overlay' },
  ])
  .png().toFile(OUT)
console.log('paper poster ->', await sharp(OUT).metadata().then(m => `${m.width}x${m.height}`))
