/*
 * Paste into the DevTools console on the reference page, then send Claude the output.
 *
 * Scroll the page top to bottom BEFORE running this. Scroll-triggered animations
 * don't exist in getAnimations() until they've fired at least once, and lazy
 * sections aren't in the DOM, so a fresh-load run silently misses most of both.
 *
 * In DevTools the result is copied to the clipboard. Elsewhere it's logged, and
 * parked on window.__designCapture for browser automation to read back.
 */
(() => {
  const MEDIA_RULE = 4;
  const FONT_FACE_RULE = 5;
  const KEYFRAMES_RULE = 7;
  const out = { url: location.href, viewport: { w: innerWidth, h: innerHeight } };

  // --- Collect rules, recursing into @media / @supports / @layer. Only walking
  // --- the top level (the obvious approach) misses every responsive override
  // --- and any keyframes declared inside a conditional block.
  const rules = [];
  let blocked = 0;
  const walk = (list) => {
    for (const r of list) {
      rules.push(r);
      // Don't descend into @keyframes — its children are the individual steps,
      // already captured via the parent's cssText.
      if (r.cssRules && r.type !== KEYFRAMES_RULE) walk(r.cssRules);
    }
  };
  for (const sheet of document.styleSheets) {
    try {
      walk(sheet.cssRules);
    } catch {
      blocked++; // cross-origin sheets throw on access
    }
  }
  out.blockedStylesheets = blocked;
  out.blockedNote = blocked
    ? `${blocked} cross-origin stylesheet(s) unreadable — CDN-hosted CSS is missing here.`
    : null;

  const clip = (s, n) => (s && s.length > n ? s.slice(0, n) + ' …' : s);

  // --- Custom properties declared on :root / html
  out.customProperties = rules
    .filter((r) => r.selectorText === ':root' || r.selectorText === 'html')
    .flatMap((r) => [...r.style].filter((p) => p.startsWith('--'))
      .map((p) => `${p}: ${r.style.getPropertyValue(p).trim()}`));

  // --- Breakpoints actually in use. Tells you which widths to re-capture at
  // --- instead of guessing the usual 768/1024.
  out.mediaConditions = [...new Set(rules
    .filter((r) => r.type === MEDIA_RULE)
    .map((r) => r.conditionText || (r.media && r.media.mediaText))
    .filter(Boolean))];

  // --- Loaded typefaces — what tells you whether a substitution is needed.
  out.fontFaces = rules
    .filter((r) => r.type === FONT_FACE_RULE)
    .slice(0, 30)
    .map((r) => ({
      family: r.style.getPropertyValue('font-family'),
      weight: r.style.getPropertyValue('font-weight'),
      style: r.style.getPropertyValue('font-style'),
      src: clip(r.style.getPropertyValue('src'), 120),
    }));

  // --- Interaction states. Easy to forget, very visible when missing.
  out.interactionRules = rules
    .filter((r) => r.selectorText && /:hover|:focus-visible|:focus\b|:active/.test(r.selectorText))
    .slice(0, 40)
    .map((r) => clip(r.cssText, 260));

  // --- @keyframes, full text
  out.keyframes = rules
    .filter((r) => r.type === KEYFRAMES_RULE)
    .map((r) => clip(r.cssText, 600));

  // --- Scroll-driven CSS (used instead of a JS library on newer sites)
  // Leaf style rules only — recursion means a matching @supports block would
  // otherwise be reported alongside each of its children.
  out.scrollDrivenCSS = rules
    .filter((r) => r.style && r.cssText &&
      /animation-timeline|view-timeline|scroll-timeline|animation-range/.test(r.cssText))
    .slice(0, 20)
    .map((r) => clip(r.cssText, 300));

  // --- Computed styles sampled off real elements. Resolves cascade, media
  // --- queries and fallbacks — far more reliable than reading source CSS.
  // --- Counts matter as much as values: frequent ones are the system.
  const tally = (map, n = 12) => [...map.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([value, count]) => `${value}  (${count})`);

  const maps = {
    fontFamilies: new Map(), typeScale: new Map(), textColors: new Map(),
    backgrounds: new Map(), borderRadii: new Map(), shadows: new Map(),
    transitions: new Map(), verticalSpacing: new Map(), gaps: new Map(),
    borders: new Map(),
  };
  const skip = new Set(['none', 'normal', 'auto', '0px', 'rgba(0, 0, 0, 0)', '']);
  const isZero = (v) => !v || parseFloat(v) === 0;
  const bump = (map, key) => {
    if (!key || skip.has(key)) return;
    map.set(key, (map.get(key) || 0) + 1);
  };

  // documentElement and body are included deliberately — querySelectorAll('*')
  // skips them, and the page background usually lives on one of the two.
  const els = [
    document.documentElement,
    document.body,
    ...document.body.querySelectorAll('*'),
  ].slice(0, 4000);

  for (const el of els) {
    if (!el.getClientRects().length) continue; // skip hidden elements
    const cs = getComputedStyle(el);
    bump(maps.fontFamilies, cs.fontFamily);
    bump(maps.typeScale, `${cs.fontSize} / ${cs.fontWeight} / lh ${cs.lineHeight} / ls ${cs.letterSpacing}`);
    bump(maps.textColors, cs.color);
    bump(maps.backgrounds, cs.backgroundColor);
    bump(maps.borderRadii, cs.borderRadius);
    bump(maps.shadows, cs.boxShadow);
    bump(maps.transitions, cs.transition);
    // Most elements have no padding and no border. Counting those swamps the
    // tally with values that tell you nothing about the spacing rhythm.
    if (!(isZero(cs.paddingTop) && isZero(cs.paddingBottom))) {
      bump(maps.verticalSpacing, `pad ${cs.paddingTop} / ${cs.paddingBottom}`);
    }
    bump(maps.gaps, cs.gap);
    if (!isZero(cs.borderTopWidth) && cs.borderTopStyle !== 'none' && cs.borderTopStyle !== 'hidden') {
      bump(maps.borders, `${cs.borderTopStyle} ${cs.borderTopWidth} ${cs.borderTopColor}`);
    }
  }

  out.sampled = Object.fromEntries(
    Object.entries(maps).map(([k, m]) => [k, tally(m)])
  );
  out.sampledElementCount = els.length;

  // --- Live animations with real timing. Only populated for animations that
  // --- have already run — hence the "scroll first" note above.
  out.liveAnimations = (document.getAnimations?.() || []).slice(0, 60).map((a) => {
    const t = (a.effect && a.effect.getTiming && a.effect.getTiming()) || {};
    const el = a.effect && a.effect.target;
    let selector = null;
    if (el && el.tagName) {
      const cls = typeof el.className === 'string' && el.className.trim()
        ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.')
        : '';
      selector = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + cls;
    }
    return {
      name: a.animationName || a.transitionProperty || a.constructor.name,
      selector,
      duration: t.duration,
      delay: t.delay,
      easing: t.easing,
      iterations: t.iterations,
      fill: t.fill,
      playState: a.playState,
    };
  });
  out.liveAnimationNote = out.liveAnimations.length === 0 && out.keyframes.length > 0
    ? 'No live animations but keyframes exist — the page probably was not scrolled before running this.'
    : null;

  // --- Which motion library is in play. Changes what you reach for on rebuild.
  out.libraries = Object.entries({
    gsap: !!window.gsap,
    scrollTrigger: !!(window.ScrollTrigger || (window.gsap && window.gsap.ScrollTrigger)),
    lenis: !!(window.Lenis || window.lenis),
    locomotive: !!window.LocomotiveScroll,
    three: !!window.THREE,
    lottie: !!(window.lottie || window.bodymovin),
    framerMotion: !!document.querySelector('[data-framer-name], [data-projection-id]'),
    aos: !!window.AOS || !!document.querySelector('[data-aos]'),
    swiper: !!window.Swiper,
    barba: !!window.barba,
    tailwind: !!document.querySelector('[class*="text-"][class*="bg-"], [class*="flex"][class*="gap-"]'),
  }).filter(([, present]) => present).map(([name]) => name);

  // Parked on a global so browser automation can read it back without depending
  // on the evaluated expression's return value.
  window.__designCapture = out;

  const json = JSON.stringify(out, null, 2);
  if (typeof copy === 'function') {
    copy(json);
    console.log('Copied to clipboard —', json.length, 'chars. Paste it to Claude.');
  } else {
    console.log(json);
  }
  return out;
})();
