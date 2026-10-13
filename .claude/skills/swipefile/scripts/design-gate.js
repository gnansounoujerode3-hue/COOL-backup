/*
 * The design gate's probe — the measurement half of the taste Pre-Flight.
 *
 * The taste skill's pre-flight is ~60 checkboxes an agent ticks about its own
 * output, in prose, with no instrument. This folder has already measured what
 * that produces: Step 2's motion spec was a written rule an agent skipped three
 * times in one session and stopped skipping only when motion-spec.py began
 * refusing. Prose is what gets quoted back correctly while being skipped.
 *
 * So this file measures. It reads a SERVED, RENDERED page and returns a census
 * — it decides nothing. All pass/fail logic lives in design-gate.py, so the
 * thresholds are reviewable in one place and this side stays a witness.
 *
 * Every number here is one a still screenshot cannot carry and a model looking
 * at its own source cannot honestly self-report: composited background colours,
 * real contrast ratios, wrapped button labels, the eyebrow census, painted font
 * families, the section-background sequence.
 *
 *   python3 cdp-run.py http://127.0.0.1:8791/ design-gate.js --out design-1440.json
 *   python3 cdp-run.py http://127.0.0.1:8791/ design-gate.js --width 390 --out design-390.json
 *
 * Run it through cdp-run.py, not an in-app browser pane: this library has twice
 * measured a pane reporting innerWidth === 0 or a fully black frame on a page
 * that headless CDP read correctly.
 */
(() => {
  const V = { w: window.innerWidth, h: window.innerHeight };
  const clamp = (n) => Math.round(n * 1000) / 1000;

  /* ---------- colour ---------- */

  const parseColor = (str) => {
    if (!str) return null;
    const m = String(str).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    if (p.length < 3 || p.some((n) => Number.isNaN(n))) return null;
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };

  const over = (fg, bg) => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a),
    a: 1,
  });

  const lum = (c) => {
    const f = (v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };

  const contrast = (a, b) => {
    const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };

  const hsl = (c) => {
    const r = c.r / 255, g = c.g / 255, b = c.b / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    let h = 0;
    if (d) {
      if (max === r) h = ((g - b) / d) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h *= 60;
      if (h < 0) h += 360;
    }
    const l = (max + min) / 2;
    const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    return { h, s, l };
  };

  const hex = (c) => '#' + [c.r, c.g, c.b]
    .map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

  /* Composite an element's background against its ancestors until it is opaque.
   * Reading backgroundColor alone is the single most common way a contrast
   * check lies: a translucent card over a dark page reports rgba(255,255,255,.06)
   * and every ratio computed against it is fiction. `imageBehind` is reported
   * rather than resolved — text over a photograph needs a scrim, and guessing a
   * ratio off one pixel of a gradient is worse than saying "not measurable". */
  const effectiveBg = (el) => {
    let acc = null, imageBehind = false, node = el;
    while (node && node !== document.documentElement.parentNode) {
      const cs = getComputedStyle(node);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') imageBehind = true;
      const c = parseColor(cs.backgroundColor);
      if (c && c.a > 0) {
        acc = acc === null ? c : over(acc, c);
        if (acc.a >= 0.999) return { color: acc, imageBehind };
      }
      node = node.parentElement;
    }
    const page = parseColor(getComputedStyle(document.body).backgroundColor);
    const base = page && page.a >= 0.999 ? page : { r: 255, g: 255, b: 255, a: 1 };
    return { color: acc ? over(acc, base) : base, imageBehind };
  };

  /* ---------- traversal ---------- */

  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    if (parseFloat(cs.opacity) < 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  const all = [...document.body.querySelectorAll('*')]
    .filter((el) => !/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|BR|META|LINK)$/.test(el.tagName))
    .filter(visible);

  const ownText = (el) => [...el.childNodes]
    .filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' ')
    .replace(/\s+/g, ' ').trim();

  const docRect = (el) => {
    const r = el.getBoundingClientRect();
    return { top: r.top + window.scrollY, left: r.left, width: r.width, height: r.height };
  };

  /* ---------- navigation ---------- */

  /* Tag-based detection alone finds nothing on a Webflow/Framer/div-only build,
   * and a missing nav then silently exempts the page from two gates. So: the
   * topmost visible element that looks like site chrome by tag, role, or class
   * and actually carries links. */
  const navEl = [...document.querySelectorAll(
    'header, nav, [role="navigation"], [class*="navbar" i], [class*="nav-bar" i], '
    + '[class*="site-header" i], [id*="navbar" i], [id*="header" i]')]
    .filter(visible)
    .filter((el) => el.querySelectorAll('a, button').length >= 2)
    .filter((el) => el.getBoundingClientRect().top + window.scrollY < 240)
    .sort((a, b) => docRect(a).top - docRect(b).top
      || b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0] || null;

  /* ---------- sections ---------- */

  /* A "section" is a full-bleed band of the page, however it is marked up.
   * Tag-based detection misses div-only builds; this takes the widest run of
   * children under the main content root. Chrome and footer are excluded — the
   * eyebrow budget and the theme sequence are about content bands. */
  const root = document.querySelector('main') || document.body;
  const sectionEls = [...root.children].filter((el) => {
    if (!visible(el)) return false;
    if (/^(HEADER|NAV|FOOTER)$/.test(el.tagName)) return false;
    if (navEl && (el === navEl || navEl.contains(el))) return false;
    const r = el.getBoundingClientRect();
    return r.height >= 160 && r.width >= V.w * 0.6;
  });
  const sections = sectionEls.map((el, i) => {
    const bg = effectiveBg(el);
    const imgs = el.querySelectorAll('img, picture, video, canvas, svg[width], [style*="background-image"]');
    const kids = [...el.children].filter(visible);
    // Two visually side-by-side children, one carrying the image and one the
    // text, is the zigzag pattern the taste skill caps at two in a row.
    const grid = getComputedStyle(el).gridTemplateColumns;
    const cols = grid && grid !== 'none' ? grid.split(/\s+/).filter(Boolean).length : 0;
    const sideBySide = kids.length === 2
      && Math.abs(kids[0].getBoundingClientRect().top - kids[1].getBoundingClientRect().top) < 80
      && kids[0].getBoundingClientRect().width < el.getBoundingClientRect().width * 0.75;
    const hasImg = (n) => n.querySelector('img, picture, video, canvas')
      || getComputedStyle(n).backgroundImage !== 'none';
    // Section-opening fingerprint: tag, rough type size, weight, and the same
    // uppercase-tracking test eyebrowCount uses below, read per child instead
    // of per page. Two sections producing the same string opened with the
    // same shape — whether that is a deliberate rhythm or the templated
    // eyebrow/heading/subhead/content stack is a call for design-gate.py's
    // consumer, not this probe.
    const openShape = kids.slice(0, 4).map((k) => {
      const kcs = getComputedStyle(k);
      const sz = parseFloat(kcs.fontSize) || 0;
      const bucket = sz >= 40 ? 'xl' : sz >= 24 ? 'l' : sz >= 17 ? 'm' : 's';
      const kt = ownText(k) || (k.innerText || '').trim();
      const upper = kcs.textTransform === 'uppercase'
        || (!!kt && kt === kt.toUpperCase() && /[A-Z]{2}/.test(kt));
      return `${k.tagName.toLowerCase()}:${bucket}:${parseInt(kcs.fontWeight, 10) >= 600 ? 'b' : 'n'}`
        + (upper ? ':u' : '');
    });
    return {
      index: i,
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      rect: docRect(el),
      bgHex: hex(bg.color),
      bgLuminance: clamp(lum(bg.color)),
      bgImage: bg.imageBehind,
      media: imgs.length,
      childCount: kids.length,
      gridColumns: cols,
      splitImageText: !!(sideBySide && (hasImg(kids[0]) !== hasImg(kids[1]))),
      openShape,
    };
  });

  /* ---------- text census ---------- */

  const EYEBROW_MAX_PX = 16;
  const textNodes = [];
  let eyebrowCount = 0;
  const eyebrows = [];

  for (const el of all) {
    const t = ownText(el);
    if (!t) continue;
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize) || 0;
    const track = cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing) || 0;
    const upper = cs.textTransform === 'uppercase' || (t === t.toUpperCase() && /[A-Z]{2}/.test(t));
    const rec = {
      text: t.slice(0, 160),
      tag: el.tagName.toLowerCase(),
      size: clamp(size),
      weight: cs.fontWeight,
      family: (cs.fontFamily || '').split(',')[0].replace(/["']/g, '').trim(),
      upper,
      trackingEm: size ? clamp(track / size) : 0,
      top: clamp(docRect(el).top),
    };
    textNodes.push(rec);

    // Eyebrow: the small uppercase wide-tracked label sitting above a heading.
    // Both conditions matter — an uppercase button label is not an eyebrow, and
    // a tracked lowercase caption is not either. The "above a heading" arm is
    // what separates a section label from a stat unit or a nav item.
    if (upper && size <= EYEBROW_MAX_PX && track / (size || 1) >= 0.06 && t.length <= 48) {
      const host = el.closest('section, article, div');
      const heading = host && [...host.querySelectorAll('h1,h2,h3,*')]
        .find((h) => visible(h) && parseFloat(getComputedStyle(h).fontSize) >= 26
          && docRect(h).top > rec.top && docRect(h).top - rec.top < 220);
      if (heading || /^(h[1-6]|p|span|div|small|label)$/.test(rec.tag) && /^[A-Z0-9 .·/–-]+$/.test(t)) {
        if (heading) { eyebrowCount += 1; eyebrows.push(rec); }
      }
    }
  }

  const pageText = (document.body.innerText || '').replace(/ /g, ' ');

  /* ---------- buttons and CTAs ---------- */

  const buttonish = all.filter((el) => {
    if (/^(BUTTON|INPUT)$/.test(el.tagName)) return el.type !== 'hidden';
    if (el.tagName !== 'A') return false;
    const cs = getComputedStyle(el);
    const pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
    const hasFill = (parseColor(cs.backgroundColor) || { a: 0 }).a > 0.05;
    const hasBorder = parseFloat(cs.borderTopWidth) > 0;
    return pad >= 16 && (hasFill || hasBorder);
  });

  const buttons = buttonish.map((el) => {
    const cs = getComputedStyle(el);
    const bg = effectiveBg(el);
    const fgRaw = parseColor(cs.color) || { r: 0, g: 0, b: 0, a: 1 };
    const fg = fgRaw.a >= 0.999 ? fgRaw : over(fgRaw, bg.color);
    const size = parseFloat(cs.fontSize) || 16;
    const lh = cs.lineHeight === 'normal' ? size * 1.2 : parseFloat(cs.lineHeight) || size * 1.2;
    const r = el.getBoundingClientRect();
    const inner = r.height - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)
      - parseFloat(cs.borderTopWidth) - parseFloat(cs.borderBottomWidth);
    const label = (el.innerText || el.value || '').replace(/\s+/g, ' ').trim();
    const large = size >= 24 || (size >= 18.66 && parseInt(cs.fontWeight, 10) >= 700);
    return {
      label: label.slice(0, 80),
      tag: el.tagName.toLowerCase(),
      // Site chrome sits inside the hero's y-range on almost every page, so a
      // nav button would otherwise satisfy "the hero CTA is above the fold"
      // for a hero whose real CTA is 900px down.
      inNav: !!(navEl && navEl.contains(el)),
      size: clamp(size),
      lines: lh > 0 ? Math.max(1, Math.round(inner / lh)) : 1,
      words: label.split(/\s+/).filter(Boolean).length,
      fg: hex(fg),
      bg: hex(bg.color),
      overImage: bg.imageBehind,
      contrast: clamp(contrast(fg, bg.color)),
      required: large ? 3 : 4.5,
      top: clamp(docRect(el).top),
      width: clamp(r.width),
    };
  }).filter((b) => b.label);

  /* ---------- form controls ---------- */

  const controls = all.filter((el) => /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)
    && el.type !== 'hidden' && el.type !== 'submit' && el.type !== 'button');

  const forms = controls.map((el) => {
    const cs = getComputedStyle(el);
    const bg = effectiveBg(el);
    const fgRaw = parseColor(cs.color) || { r: 0, g: 0, b: 0, a: 1 };
    const fg = fgRaw.a >= 0.999 ? fgRaw : over(fgRaw, bg.color);
    let ph = null;
    try {
      const pc = parseColor(getComputedStyle(el, '::placeholder').color);
      if (pc) ph = clamp(contrast(pc.a >= 0.999 ? pc : over(pc, bg.color), bg.color));
    } catch (e) { /* ::placeholder unreadable on this engine — reported as null */ }
    return {
      name: el.name || el.id || el.type || el.tagName.toLowerCase(),
      type: el.type || el.tagName.toLowerCase(),
      fg: hex(fg),
      bg: hex(bg.color),
      overImage: bg.imageBehind,
      contrast: clamp(contrast(fg, bg.color)),
      placeholderContrast: ph,
      hasPlaceholder: !!el.placeholder,
      labelled: !!(el.labels && el.labels.length) || !!el.getAttribute('aria-label'),
      placeholderOnlyLabel: !!el.placeholder && !(el.labels && el.labels.length)
        && !el.getAttribute('aria-label'),
    };
  });

  let nav = null;
  if (navEl) {
    const r = navEl.getBoundingClientRect();
    const items = [...navEl.querySelectorAll('a, button')].filter(visible);
    const tops = [...new Set(items.map((i) => Math.round(i.getBoundingClientRect().top / 8) * 8))];
    nav = {
      height: clamp(r.height),
      items: items.length,
      rows: tops.length,
      // A hamburger legitimately collapses to one row; rows counts rendered
      // lines of whatever is actually on screen at this viewport.
      labels: items.map((i) => (i.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean),
    };
  }

  /* ---------- colour, radius and font census ---------- */

  const colorCount = {}, radiusCount = {}, familyCount = {};
  for (const el of all) {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (r.width * r.height >= 400) {
      const rad = parseFloat(cs.borderTopLeftRadius) || 0;
      // A pill/circle is a shape decision, not a scale value: normalise anything
      // at or past half the short edge so `9999px` and `50%` collapse together.
      const key = rad >= Math.min(r.width, r.height) / 2 - 0.5 ? 'pill'
        : String(Math.round(rad));
      if (rad > 0 || key === 'pill') radiusCount[key] = (radiusCount[key] || 0) + 1;
      const bg = parseColor(cs.backgroundColor);
      if (bg && bg.a > 0.2) {
        const k = hex(bg.a >= 0.999 ? bg : over(bg, effectiveBg(el.parentElement || document.body).color));
        colorCount[k] = (colorCount[k] || 0) + 1;
      }
    }
    if (ownText(el)) {
      const c = parseColor(cs.color);
      if (c && c.a > 0.5) { const k = hex(c); colorCount[k] = (colorCount[k] || 0) + 1; }
      const fam = (cs.fontFamily || '').split(',')[0].replace(/["']/g, '').trim();
      if (fam) familyCount[fam] = (familyCount[fam] || 0) + 1;
    }
  }

  // Accent families: chromatic hues used structurally. Neutrals — the greys and
  // tinted papers a page is mostly made of — are excluded by CHROMA, not by
  // HSL saturation: a warm cream like #f7e7d3 reports s≈0.69 because saturation
  // is normalised against lightness, and filtering on it books the page
  // background as a second accent. Raw max-min channel spread does not lie that
  // way. A hue seen once or twice is decoration; the library weights colour by
  // use count for the same reason motion-diff weights durations by use count.
  const CHROMA_MIN = 40;
  const accentBuckets = {};
  for (const [k, n] of Object.entries(colorCount)) {
    const c = parseColor(`rgb(${parseInt(k.slice(1, 3), 16)},${parseInt(k.slice(3, 5), 16)},${parseInt(k.slice(5, 7), 16)})`);
    const { h, l } = hsl(c);
    const chroma = Math.max(c.r, c.g, c.b) - Math.min(c.r, c.g, c.b);
    if (chroma < CHROMA_MIN || l < 0.12 || l > 0.9) continue;
    const bucket = Math.round(h / 30) * 30 % 360;
    accentBuckets[bucket] = accentBuckets[bucket] || { hue: bucket, uses: 0, samples: [] };
    accentBuckets[bucket].uses += n;
    if (accentBuckets[bucket].samples.length < 4) accentBuckets[bucket].samples.push({ hex: k, uses: n });
  }

  // status, not presence: a @font-face that 404s is still IN document.fonts
  // (browsers register the rule on parse, before the fetch resolves), so
  // presence alone reads a failed fetch as a successful one.
  const loadedFaces = new Set();
  try {
    document.fonts.forEach((f) => { if (f.status === 'loaded') loadedFaces.add(f.family.replace(/["']/g, '')); });
  } catch (e) { /* older engine */ }

  /* ---------- motion ---------- */

  let reducedMotionRules = 0, stylesheetsUnreadable = 0;
  for (const sheet of document.styleSheets) {
    try {
      const walk = (rules) => {
        for (const rule of rules) {
          if (rule.media && /prefers-reduced-motion/.test(rule.conditionText || rule.media.mediaText || '')) {
            reducedMotionRules += 1;
          }
          if (rule.cssRules) walk(rule.cssRules);
        }
      };
      walk(sheet.cssRules);
    } catch (e) { stylesheetsUnreadable += 1; }
  }

  let infinite = 0, marquees = 0;
  try {
    for (const anim of document.getAnimations()) {
      const timing = anim.effect && anim.effect.getTiming ? anim.effect.getTiming() : {};
      if (timing.iterations !== Infinity) continue;
      infinite += 1;
      const frames = anim.effect.getKeyframes ? anim.effect.getKeyframes() : [];
      const movesX = frames.some((f) => /translate(3d|X)?\((-?[\d.]+)(px|%|em|rem)/.test(f.transform || ''));
      const el = anim.effect.target;
      const wide = el && el.scrollWidth > el.clientWidth * 1.2;
      if (movesX && wide) marquees += 1;
    }
  } catch (e) { /* getAnimations unsupported — reported via infinite === 0 */ }

  /* ---------- hero ---------- */

  const heroEl = sectionEls[0] || null;
  let hero = null;
  if (heroEl) {
    const r = docRect(heroEl);
    const cs = getComputedStyle(heroEl);
    const inHero = (el) => {
      const t = docRect(el).top;
      return t >= r.top - 1 && t < r.top + r.height;
    };
    const heroText = all.filter((el) => inHero(el) && ownText(el)
      && el.children.length === 0);
    const heroButtons = buttons.filter((b) => !b.inNav
      && b.top >= r.top - 1 && b.top < r.top + r.height);

    /* Reveal-gated media is still a real visual. `visible()` requires opacity,
     * and a hero image sitting at opacity 0 until its IntersectionObserver
     * fires would otherwise report the hero as having no imagery at all — the
     * exact false FAIL that teaches an agent to stop reading this gate. Laid
     * out with real area is the test; painted-this-instant is not. */
    const laidOut = (el) => {
      const b = el.getBoundingClientRect();
      return getComputedStyle(el).display !== 'none' && b.width * b.height >= 400;
    };
    /* Overlap, not descent. A WebGL page hangs one <canvas> off <main> and
     * paints every section through it, so a `heroEl.querySelectorAll` reports
     * a hero with no visual on a page that is nothing but visual. The question
     * is whether something real is rendered in the hero's band. */
    const overlapsHero = (el) => {
      const b = docRect(el);
      return b.top < r.top + r.height && b.top + b.height > r.top;
    };
    const media = [...document.querySelectorAll('img, picture, video, canvas')]
      .filter((el) => laidOut(el) && overlapsHero(el));
    const bgImages = [...document.body.querySelectorAll('*')]
      .filter((el) => laidOut(el) && overlapsHero(el)
        && getComputedStyle(el).backgroundImage !== 'none'
        && !/^\s*(linear|radial|conic)-gradient/.test(getComputedStyle(el).backgroundImage));
    /* Headline detection cannot use the leaf-text filter: a kinetic-reveal
     * heading wraps every word — sometimes every character — in its own span,
     * so the element carrying the headline has children and no own text. Take
     * the largest-type element that renders text, leaf or not. */
    const headline = [...heroEl.querySelectorAll('h1, h2, h3, p, span, div')]
      .filter((el) => visible(el) && (el.innerText || '').trim()
        && parseFloat(getComputedStyle(el).fontSize) >= 28
        // Its own parent would score identically and wrap more than the
        // headline, so prefer the innermost element with the same text.
        && ![...el.children].some((k) => visible(k)
          && (k.innerText || '').trim() === (el.innerText || '').trim()))
      .sort((a, b) => parseFloat(getComputedStyle(b).fontSize)
        - parseFloat(getComputedStyle(a).fontSize) || docRect(a).top - docRect(b).top)[0];
    let headlineLines = null;
    if (headline) {
      const hcs = getComputedStyle(headline);
      const hsz = parseFloat(hcs.fontSize);
      const hlh = hcs.lineHeight === 'normal' ? hsz * 1.2 : parseFloat(hcs.lineHeight) || hsz * 1.2;
      headlineLines = Math.max(1, Math.round(headline.getBoundingClientRect().height / hlh));
    }
    /* The hero-stack rule bans specific things rather than a raw element count:
     * the tiny tagline under the CTAs, the trust micro-strip, the pricing
     * teaser. All of them share one measurable signature — text below the last
     * CTA, still inside the hero. Counting every text leaf instead reports 31
     * on a perfectly disciplined hero and means nothing. */
    const ctaEls = buttonish.filter((el) => !(navEl && navEl.contains(el)) && inHero(el));
    const lastCtaBottom = ctaEls.length
      ? Math.max(...ctaEls.map((el) => docRect(el).top + el.getBoundingClientRect().height))
      : null;
    const belowCtas = lastCtaBottom === null ? [] : heroText.filter((el) => {
      if (ctaEls.some((b) => b.contains(el))) return false;
      return docRect(el).top >= lastCtaBottom - 2;
    });

    hero = {
      height: clamp(r.height),
      viewportHeight: V.h,
      paddingTop: clamp(parseFloat(cs.paddingTop) || 0),
      textElements: heroText.length,
      lastCtaBottom: lastCtaBottom === null ? null : clamp(lastCtaBottom),
      textBelowCtas: belowCtas.length,
      textBelowCtaSamples: belowCtas.slice(0, 5).map((el) => ownText(el).slice(0, 60)),
      headline: headline ? (headline.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) : null,
      headlineLines,
      ctas: heroButtons.length,
      firstCtaTop: heroButtons.length ? Math.min(...heroButtons.map((b) => b.top)) : null,
      realMedia: media.length,
      backgroundPhotos: bgImages.length,
      // A gradient is not a hero visual — the taste skill calls text + gradient
      // blob a placeholder, so gradients are excluded from the count above.
      gradientOnly: media.length === 0 && bgImages.length === 0
        && /gradient/.test(cs.backgroundImage || ''),
    };
  }

  return {
    url: location.href,
    viewport: V,
    scrollHeight: document.documentElement.scrollHeight,
    sections,
    hero,
    nav,
    buttons,
    forms,
    eyebrows: { count: eyebrowCount, samples: eyebrows.slice(0, 12) },
    text: {
      emDashes: (pageText.match(/—/g) || []).length,
      emDashSamples: (pageText.match(/[^\n]{0,40}—[^\n]{0,40}/g) || []).slice(0, 6),
      body: pageText.slice(0, 200000),
      nodes: textNodes.length,
    },
    census: {
      colors: Object.entries(colorCount).sort((a, b) => b[1] - a[1]).slice(0, 40)
        .map(([k, n]) => ({ hex: k, uses: n })),
      accents: Object.values(accentBuckets).sort((a, b) => b.uses - a.uses),
      radii: Object.entries(radiusCount).sort((a, b) => b[1] - a[1])
        .map(([k, n]) => ({ radius: k, uses: n })),
      families: Object.entries(familyCount).sort((a, b) => b[1] - a[1])
        .map(([k, n]) => ({ family: k, uses: n, loaded: loadedFaces.has(k) })),
    },
    media: {
      images: document.querySelectorAll('img, picture, video').length,
      canvases: document.querySelectorAll('canvas').length,
    },
    motion: {
      reducedMotionRules,
      stylesheetsUnreadable,
      infiniteAnimations: infinite,
      marquees,
    },
  };
})();
