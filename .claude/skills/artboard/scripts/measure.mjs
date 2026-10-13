#!/usr/bin/env node
/**
 * artboard/measure — read hard facts off a static creative before touching it.
 *
 * Everything this prints is measured from pixels. Nothing is estimated. The whole
 * point of the skill is that a re-layout built on guessed angles and guessed
 * colours produces tilted type and visible patches, and neither shows up until
 * the asset is already in a feed.
 *
 * Usage:
 *   node measure.mjs <image> [--tilt x1,x2,y0,y1[;...]] [--color x,y[;x,y...]]
 *
 *   --tilt   One or more bands to scan for a near-horizontal light edge (a card
 *            shell, a panel, a bar). Each band is `xLeft,xRight,yFrom,yTo`.
 *            Prints the slope in degrees; counter-rotate by the negative.
 *   --color  One or more points to sample. Prints each and their average, which
 *            is what a rebuilt surface should be filled with.
 *
 *   --bbox   Tolerance in levels. Finds the subject's extent against a fitted
 *            background plane, for reframing a SUBJECT creative (packshot,
 *            portrait) rather than re-laying out a LAYOUT creative.
 *
 * With no flags it prints dimensions, aspect ratio and the nearest standard
 * delivery ratios, which is the minimum you need before planning a re-layout.
 *
 * KNOWN LIMIT of --bbox: it models the background as a *plane*, which handles a
 * lit seamless sweep (measured on a real packshot: a 37-level corner-to-corner
 * ramp, correctly fitted). It does NOT handle a radial vignette, where residuals
 * at the frame edges stay above tolerance and the box over-reports toward the
 * full frame. Sweep the tolerance and sanity-check the result by eye; if the
 * reported box is ~100% of the frame on an obviously centred subject, the
 * background is vignetted and the number is wrong. Edge-energy segmentation
 * would fix this properly and is not implemented.
 */
import sharp from 'sharp'
import { readFileSync } from 'node:fs'

const args = process.argv.slice(2)
const file = args[0]
if (!file) {
  console.error('usage: measure.mjs <image> [--tilt x1,x2,y0,y1] [--color x,y]')
  process.exit(1)
}
const flag = (name) => {
  const i = args.indexOf(name)
  return i === -1 ? null : args[i + 1]
}

const RATIOS = [
  ['16:9', 16 / 9], ['1.91:1', 1.91], ['4:3', 4 / 3], ['1:1', 1],
  ['4:5', 0.8], ['3:4', 0.75], ['9:16', 9 / 16],
]

const meta = await sharp(file).metadata()
const ar = meta.width / meta.height
const nearest = RATIOS.map(([n, v]) => [n, v, Math.abs(v - ar) / ar]).sort((a, b) => a[2] - b[2])[0]
console.log(`file    ${file}`)
console.log(`size    ${meta.width}x${meta.height}  (${(readFileSync(file).length / 1048576).toFixed(2)} MB)`)
console.log(`aspect  ${ar.toFixed(4)}  nearest standard: ${nearest[0]}${nearest[2] < 0.01 ? '' : `  (off by ${(nearest[2] * 100).toFixed(1)}%)`}`)

/* ---- tilt -----------------------------------------------------------------
 * Panels in AI-generated and 3D-rendered creatives are almost never axis
 * aligned. Lifting one flat and dropping it into a new layout leaves type that
 * visibly slopes. Scanning for the panel's own top edge at two x positions gives
 * the real angle, and the fix is a rotation by exactly its negative.
 * ------------------------------------------------------------------------- */
const tiltSpec = flag('--tilt')
if (tiltSpec) {
  const { data, info } = await sharp(file).greyscale().raw().toBuffer({ resolveWithObject: true })
  const at = (x, y) => data[y * info.width + x]
  // First y where brightness jumps to a light surface and stays there. The
  // 3px confirmation rejects single-pixel speckle and JPEG ringing.
  const edge = (x, from, to, thr) => {
    for (let y = from; y < to; y++) if (at(x, y) > thr && at(x, y + 3) > thr) return y
    return null
  }
  console.log('\ntilt')
  for (const band of tiltSpec.split(';')) {
    const [x1, x2, y0, y1] = band.split(',').map(Number)
    let found = null
    // Sweep the threshold: one fixed value does not survive both a white card on
    // cream and a pale panel on white.
    for (const thr of [246, 238, 228, 215, 200]) {
      const ya = edge(x1, y0, y1, thr), yb = edge(x2, y0, y1, thr)
      if (ya != null && yb != null) { found = { ya, yb, thr }; break }
    }
    if (!found) { console.log(`  ${band}  no edge found in band`); continue }
    const deg = Math.atan2(found.yb - found.ya, x2 - x1) * 180 / Math.PI
    console.log(`  x${x1}->${x2}  y ${found.ya}->${found.yb}  (thr ${found.thr})  slope ${deg.toFixed(2)}deg  counter-rotate ${(-deg).toFixed(2)}`)
  }
}

/* ---- subject bbox ---------------------------------------------------------
 * Layout creatives are re-laid out. SUBJECT creatives - a packshot, a portrait,
 * one object on seamless - have nothing to re-lay out, and the honest move is a
 * reframe. But a reframe needs to know where the subject actually is, or a tall
 * crop shaves the top off a product and nobody notices until it is live.
 *
 * Finds the extent of everything that differs from the corner background by more
 * than `tol`, then reports the safe crop margins around it.
 * ------------------------------------------------------------------------- */
const bboxTol = flag('--bbox')
if (bboxTol !== null) {
  const tol = Number(bboxTol) || 12
  const { data, info } = await sharp(file).greyscale().raw().toBuffer({ resolveWithObject: true })
  const { width: w, height: h } = info
  const at = (x, y) => data[y * w + x]
  /* Studio backgrounds are almost never flat: a seamless sweep is lit, so it
     ramps. Comparing against one corner value flags the whole ramp as subject
     and returns the entire frame. (Measured on a real packshot: corners ran
     #cbbeb4 to #f0e6df, a ~40-level gradient.)
     So fit the background as a plane v = a + bx + cy from the border ring, and
     measure deviation from the fit rather than from a constant. */
  const ring = []
  const inset = Math.max(2, Math.round(Math.min(w, h) * 0.01))
  for (let x = inset; x < w - inset; x += Math.max(1, Math.round(w / 120))) {
    ring.push([x, inset, at(x, inset)], [x, h - 1 - inset, at(x, h - 1 - inset)])
  }
  for (let y = inset; y < h - inset; y += Math.max(1, Math.round(h / 120))) {
    ring.push([inset, y, at(inset, y)], [w - 1 - inset, y, at(w - 1 - inset, y)])
  }
  // Least squares on the 3x3 normal equations, solved by Cramer's rule.
  let S1 = 0, Sx = 0, Sy = 0, Sxx = 0, Sxy = 0, Syy = 0, Sv = 0, Sxv = 0, Syv = 0
  for (const [x, y, v] of ring) {
    S1++; Sx += x; Sy += y; Sxx += x * x; Sxy += x * y; Syy += y * y
    Sv += v; Sxv += x * v; Syv += y * v
  }
  const det3 = (m) =>
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
    m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
    m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
  const M = [[S1, Sx, Sy], [Sx, Sxx, Sxy], [Sy, Sxy, Syy]]
  const D = det3(M)
  const sub = (i) => det3(M.map((row, r) => row.map((val, c) => (c === i ? [Sv, Sxv, Syv][r] : val))))
  const [a, bx, cy] = Math.abs(D) < 1e-6 ? [Sv / S1, 0, 0] : [sub(0) / D, sub(1) / D, sub(2) / D]
  const base = (x, y) => a + bx * x + cy * y
  const ramp = Math.abs(bx) * w + Math.abs(cy) * h
  let minX = w, minY = h, maxX = 0, maxY = 0
  const step = Math.max(1, Math.round(Math.min(w, h) / 900))  // subsample big files
  for (let y = 0; y < h; y += step) {
    for (let x = 0; x < w; x += step) {
      if (Math.abs(at(x, y) - base(x, y)) > tol) {
        if (x < minX) minX = x; if (x > maxX) maxX = x
        if (y < minY) minY = y; if (y > maxY) maxY = y
      }
    }
  }
  console.log('\nsubject bbox')
  if (maxX <= minX) { console.log(`  nothing exceeds tol ${tol} against the fitted background`) }
  else {
    console.log(`  background fit  ${a.toFixed(1)} + ${bx.toFixed(4)}x + ${cy.toFixed(4)}y   (ramps ${ramp.toFixed(0)} levels corner to corner)`)
    console.log(`  tol        ${tol}`)
    console.log(`  box        ${minX},${minY} ${maxX - minX}x${maxY - minY}`)
    console.log(`  margins    left ${minX}  right ${w - maxX}  top ${minY}  bottom ${h - maxY}`)
    console.log(`  centre     ${Math.round((minX + maxX) / 2)},${Math.round((minY + maxY) / 2)}  (frame centre ${Math.round(w / 2)},${Math.round(h / 2)})`)
    const sw = maxX - minX, sh = maxY - minY
    console.log(`  subject fills ${((sw / w) * 100).toFixed(0)}% wide, ${((sh / h) * 100).toFixed(0)}% tall`)
    console.log(`  tightest safe crop around subject: ${sw}x${sh} -> ratios ${(sw / sh).toFixed(3)} and wider`)
  }
}

/* ---- colour ---------------------------------------------------------------
 * A rebuilt surface has to be filled with the colour the original actually used,
 * not a plausible one. Being two or three values off reads as a faint patch
 * exactly where a lifted element sits.
 * ------------------------------------------------------------------------- */
const colorSpec = flag('--color')
if (colorSpec) {
  const raw = await sharp(file).raw().toBuffer({ resolveWithObject: true })
  const px = (x, y) => {
    const i = (y * raw.info.width + x) * raw.info.channels
    return [raw.data[i], raw.data[i + 1], raw.data[i + 2]]
  }
  const hex = (c) => '#' + c.map(v => Math.round(v).toString(16).padStart(2, '0')).join('')
  const pts = colorSpec.split(';').map(s => s.split(',').map(Number))
  console.log('\ncolour')
  const all = pts.map(([x, y]) => { const c = px(x, y); console.log(`  ${x},${y}  ${hex(c)}`); return c })
  const mean = all.reduce((a, c) => [a[0] + c[0], a[1] + c[1], a[2] + c[2]], [0, 0, 0]).map(v => v / all.length)
  console.log(`  average  ${hex(mean)}   <- fill rebuilt surfaces with this`)
}
