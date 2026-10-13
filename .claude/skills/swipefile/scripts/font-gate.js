/*
 * The font gate. Run it on the REFERENCE and on the MIRROR at the same
 * viewport, then compare the two results — the gate is that they AGREE, not
 * that either one returns true in the absolute.
 *
 * Why a two-sided comparison: a reference routinely returns
 * document.fonts.check() === false for families it declares in fallback stacks
 * but never actually uses on that page (measured: Inter and Fragment Mono both
 * false on onefin's own homepage, 67 faces loaded). An absolute pass condition
 * therefore fails on a perfect mirror.
 *
 * Fonts fail silently and three detectors are each individually blind:
 *   - computed fontFamily echoes the REQUESTED family while a fallback paints,
 *     so reading styles proves nothing;
 *   - document.fonts.check() returned TRUE throughout the SRI failure, where a
 *     stylesheet was dropped whole and the page rendered in Times — and it is
 *     weaker still: measured in scripts/tests/test_font.py, check() returns TRUE
 *     for a family never declared anywhere, because the spec asks whether the
 *     text can be rendered and a fallback always can. It cannot detect an absent
 *     face at all;
 *   - the canvas width A/B reports differs:false for metric-compatible
 *     fallbacks — Framer registers "<Family> Placeholder" faces by design.
 * So: run all three, and probe the DISPLAY face, not just the UI sans, where a
 * metric-compatible substitution actually shows up.
 *
 * Usage — DevTools: paste, result is copied to the clipboard.
 *         Automation: evaluate this file, read the return value or
 *         window.__fontGate.
 *         Custom list: window.__fontGateSpecs = [{family:'Satoshi', weight:500,
 *         size:16}, ...] before running, else the page's own census is used.
 */
(() => {
  const SAMPLE = 'Handgloves 0123456789 — the quick brown fox';
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  const width = (family, weight, size) => {
    ctx.font = `${weight} ${size}px ${family}`;
    return ctx.measureText(SAMPLE).width;
  };

  // Census the page's rendered text so the gate covers what actually paints,
  // not what the stylesheet declares. Sorted by frequency: the top entries are
  // the type system, and a family that never renders is not worth gating on.
  const census = () => {
    const tally = new Map();
    for (const el of document.querySelectorAll('*')) {
      if (!el.childNodes.length) continue;
      let text = '';
      for (const n of el.childNodes) if (n.nodeType === 3) text += n.textContent.trim();
      if (!text) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const box = el.getBoundingClientRect();
      if (!box.width || !box.height) continue;   // detached / 0x0 nodes lie
      const family = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
      const size = Math.round(parseFloat(cs.fontSize));
      const key = `${family}|${cs.fontWeight}|${size}`;
      tally.set(key, (tally.get(key) || 0) + 1);
    }
    return [...tally.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([key, count]) => {
        const [family, weight, size] = key.split('|');
        return { family, weight: Number(weight), size: Number(size), count };
      });
  };

  const seen = census();
  const specs = window.__fontGateSpecs || (() => {
    // Everything the page renders, deduped per family+weight, keeping the
    // LARGEST size seen for each — the display cut is where a metric-compatible
    // substitution is visible and the UI sans is where it hides.
    const best = new Map();
    for (const s of seen) {
      const k = `${s.family}|${s.weight}`;
      if (!best.has(k) || best.get(k).size < s.size) best.set(k, s);
    }
    return [...best.values()];
  })();

  const families = specs.map(({ family, weight, size, count }) => {
    const requested = width(`"${family}", sans-serif`, weight, size);
    const fallback = width('sans-serif', weight, size);
    const serifCtrl = width('serif', weight, size);
    return {
      family,
      weight,
      size,
      renderedCount: count ?? null,
      check: document.fonts.check(`${weight} ${size}px "${family}"`),
      requestedWidth: Math.round(requested * 100) / 100,
      fallbackWidth: Math.round(fallback * 100) / 100,
      // Identical to BOTH generic stacks is the strong signal that nothing
      // special is painting. Identical to sans-serif alone can still be a
      // metric-compatible face doing its job.
      differs: Math.abs(requested - fallback) > 0.5,
      differsFromSerif: Math.abs(requested - serifCtrl) > 0.5,
    };
  });

  const loaded = [...document.fonts].map((f) => `${f.family} ${f.weight} ${f.status}`);
  const out = {
    url: location.href,
    viewport: { w: innerWidth, h: innerHeight, dpr: devicePixelRatio },
    faces: document.fonts.size,
    fontsReady: document.fonts.status,
    // A stylesheet dropped for a stale SRI hash takes every face with it, and
    // reports no console error. Zero faces on a page that declares any is that.
    zeroFaces: document.fonts.size === 0,
    placeholderFaces: loaded.filter((f) => /placeholder/i.test(f)),
    families,
    loaded,
    census: seen.slice(0, 25),
  };

  out.summary = {
    familiesProbed: families.length,
    checkFalse: families.filter((f) => !f.check).map((f) => f.family),
    identicalToFallback: families.filter((f) => !f.differs).map((f) => f.family),
  };
  out.compare = 'Run on both sides. PASS = faces equal, per-family check() equal, '
    + 'and requestedWidth equal within 0.5px. An absolute true is NOT the gate.';

  window.__fontGate = out;
  const json = JSON.stringify(out, null, 2);
  if (typeof copy === 'function') {
    copy(json);
    console.log('Font gate copied to clipboard —', json.length, 'chars.');
  } else {
    console.log(json);
  }
  return out;
})();
