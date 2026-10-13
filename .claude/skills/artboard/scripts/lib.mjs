/**
 * artboard/lib — the primitives a recut is built from.
 *
 * Deliberately NOT a layout DSL. Every creative is laid out differently, and a
 * general-purpose JSON schema for "where things go" collapses on the second real
 * job. What generalises is the handful of operations that are genuinely hard to
 * get right, and which look fine in a thumbnail while being wrong in the feed:
 *
 *   lift()    pull an element out of a source that is tilted, and land it flat
 *   feather() dissolve a lifted rectangle so it leaves no patch
 *   fadeEdges() bleed a photograph into the page instead of ending on a seam
 *   bg()      a warm/neutral gradient field with an optional glow
 *   place()   compose, with the maths that stops sharp throwing on overflow
 *
 * The layout itself is written per job, in plain code, next to these. See
 * examples/ for a complete one.
 */
import sharp from 'sharp'

/** Crop a box `[left, top, width, height]` out of the source. */
export const cut = (src, [left, top, width, height]) =>
  sharp(src).extract({ left, top, width, height }).png().toBuffer()

/**
 * Soft-edged alpha, so a lifted rectangle dissolves into whatever it lands on.
 *
 * Every element cut from a finished creative carries a rectangle of that
 * creative's background. Against a new field, that rectangle shows as a faint
 * patch, and if the element was also rotated the patch tilts with it, which
 * reads unmistakably as a paste-up. Feathering costs `r` pixels of margin and
 * removes the tell entirely.
 *
 * Keep `r` well inside the padding you cropped with, or it will eat the content.
 */
export async function feather(buf, r = 12) {
  const { width, height } = await sharp(buf).metadata()
  const inner = `<rect x="${r}" y="${r}" width="${Math.max(1, width - 2 * r)}" height="${Math.max(1, height - 2 * r)}" rx="${r}" fill="#fff"/>`
  const mask = await sharp(Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">${inner}</svg>`
  )).blur(r / 1.8).png().toBuffer()
  return sharp(buf).ensureAlpha().composite([{ input: mask, blend: 'dest-in' }]).png().toBuffer()
}

/**
 * Lift an element out of the source: crop, de-tilt, scale, feather.
 *
 * `tilt` is the measured slope in degrees from `measure.mjs --tilt`. The element
 * is rotated by its negative, then trimmed, because rotation pads the canvas with
 * transparency and the piece must be placed by its real bounds.
 *
 * Pass tilt 0 for anything genuinely axis-aligned. Do not guess a value: an
 * unnecessary rotation resamples type for nothing.
 */
export async function lift(src, box, { tilt = 0, width = null, feather: r = 12 } = {}) {
  let buf = await cut(src, box)
  if (Math.abs(tilt) > 0.05) {
    buf = await sharp(buf).rotate(-tilt, { background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer()
    buf = await sharp(buf).trim({ threshold: 1 }).png().toBuffer()
  }
  if (width) buf = await sharp(buf).resize({ width }).png().toBuffer()
  return r > 0 ? feather(buf, r) : buf
}

/**
 * Fade a photograph's top and/or bottom to transparent.
 *
 * A photographic element that stops on a straight horizontal line announces that
 * it was cropped from something else. Bleeding it into the page is what makes a
 * re-layout read as designed rather than assembled.
 */
export async function fadeEdges(buf, { top = 0, bottom = 0.26 } = {}) {
  const { width, height } = await sharp(buf).metadata()
  const stops = [
    `<stop offset="0" stop-color="#fff" stop-opacity="${top > 0 ? 0 : 1}"/>`,
    top > 0 ? `<stop offset="${top}" stop-color="#fff" stop-opacity="1"/>` : '',
    `<stop offset="${1 - bottom}" stop-color="#fff" stop-opacity="1"/>`,
    `<stop offset="1" stop-color="#fff" stop-opacity="${bottom > 0 ? 0 : 1}"/>`,
  ].join('')
  const mask = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <defs><linearGradient id="f" x1="0" y1="0" x2="0" y2="1">${stops}</linearGradient></defs>
    <rect width="${width}" height="${height}" fill="url(#f)"/></svg>`)
  return sharp(buf).composite([{ input: mask, blend: 'dest-in' }]).png().toBuffer()
}

/** A gradient field, optionally with a soft radial glow. Colours come from measure. */
export function bg(w, h, { stops, glow = null } = {}) {
  const gs = stops.map(([o, c]) => `<stop offset="${o}" stop-color="${c}"/>`).join('')
  const g = glow
    ? `<radialGradient id="glow" cx="${glow.cx}" cy="${glow.cy}" r="${glow.r}">
         <stop offset="0" stop-color="${glow.color}"/><stop offset="1" stop-color="${glow.fade}"/>
       </radialGradient>`
    : ''
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><defs>
    <linearGradient id="g" x1="0" y1="0" x2="0.3" y2="1">${gs}</linearGradient>${g}</defs>
    <rect width="${w}" height="${h}" fill="url(#g)"/>
    ${glow ? `<rect width="${w}" height="${h}" fill="url(#glow)"/>` : ''}</svg>`)
}

/** A rounded surface filled with a measured colour. */
export const surface = (w, h, fill, radius = 32) => Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
     <rect width="${w}" height="${h}" rx="${radius}" fill="${fill}"/></svg>`)

export const heightOf = async (buf) => (await sharp(buf).metadata()).height
export const widthOf = async (buf) => (await sharp(buf).metadata()).width

/**
 * Compose layers onto a canvas.
 *
 * sharp throws if any composite input extends past the canvas, which on a recut
 * usually means an element grew during de-tilt. Failing loudly with the offending
 * layer named beats a cryptic libvips error.
 */
export async function place(canvas, layers, out, { w, h }) {
  for (const l of layers) {
    const m = await sharp(l.input).metadata()
    if (l.left + m.width > w || l.top + m.height > h || l.left < 0 || l.top < 0) {
      throw new Error(
        `layer "${l.name ?? 'unnamed'}" (${m.width}x${m.height} at ${l.left},${l.top}) ` +
        `does not fit the ${w}x${h} canvas`)
    }
  }
  await sharp(canvas).composite(layers.map(({ name, ...l }) => l)).png().toFile(out)
  const m = await sharp(out).metadata()
  return { width: m.width, height: m.height }
}
