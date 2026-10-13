/*
 * Motion extraction at SPEC depth — the per-animation mapping a rebuild needs.
 *
 * `extract-console.js` already tallies @keyframes, transitions and live timing.
 * That is a signature: it tells you what a site's motion FEELS like. It cannot
 * rebuild one, because it never records which element an animation belongs to,
 * what it moves from and to, or where in the scroll it fires. A library entry
 * written from it says "cubic-bezier(.22,1,.36,1), quick and soft-landing" —
 * true, and un-buildable. This fills exactly that gap.
 *
 * Method, and why it is shaped this way:
 *   - Scroll-triggered animations do not exist in getAnimations() until they
 *     have fired, so this scrolls the page in steps and snapshots after each.
 *   - The step at which an animation FIRST appears, plus its target's position
 *     in the viewport at that moment, is the trigger offset — the thing
 *     "fades in on scroll" leaves out and the thing that decides whether the
 *     page feels responsive or late.
 *   - Framer runs entrance motion from `script[type="framer/appear"]` JSON, not
 *     from CSS. Two Framer captures in this library recorded "read the appear
 *     payloads instead" and then never did, leaving both entries with no motion
 *     at all. They are read here.
 *
 * Usage — DevTools: paste, await it, result copies to the clipboard.
 *         Automation: evaluate and await the returned promise, or read
 *         window.__motionSpec once it resolves.
 */
(() => {
  const STEPS = 14;            // scroll snapshots top to bottom
  const SETTLE = 550;          // ms after each scroll for reveals to fire
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // TWO PHASES, and the split is the whole point.
  //
  // Hero and entrance animations fire during load. Listeners installed after
  // load therefore miss every one of them — and a finished transition is gone
  // from getAnimations(), so nothing recovers them afterwards. A landing page
  // whose hero words stagger in and whose sections reveal on scroll would
  // report only the scroll half, which is exactly the half a user does not
  // notice missing.
  //
  // So: inject this file at document-start (CDP
  // Page.addScriptToEvaluateOnNewDocument, i.e. `cdp-run.py --pre`) and it
  // installs the hooks and returns. Evaluate it again after load and it runs
  // the scroll pass and reports, reusing everything the hooks caught.
  if (window.__motionHooks) return window.__motionRun();

  // Short, readable, reasonably stable path to an element.
  const selectorFor = (el) => {
    if (!el || el.nodeType !== 1) return null;
    const parts = [];
    for (let n = el; n && n.nodeType === 1 && parts.length < 4; n = n.parentElement) {
      let s = n.tagName.toLowerCase();
      if (n.id) { parts.unshift(`${s}#${n.id}`); break; }
      const cls = [...n.classList].filter((c) => !/^(is|has)-|active|visible/.test(c)).slice(0, 2);
      if (cls.length) s += '.' + cls.join('.');
      const sibs = n.parentElement ? [...n.parentElement.children].filter((c) => c.tagName === n.tagName) : [];
      if (sibs.length > 1) s += `:nth-of-type(${sibs.indexOf(n) + 1})`;
      parts.unshift(s);
    }
    return parts.join(' > ');
  };

  // Only the properties that carry a reveal; a keyframe dump of every computed
  // property is noise that hides the two values that matter.
  const INTERESTING = ['opacity', 'transform', 'translate', 'scale', 'rotate',
                       'filter', 'clipPath', 'clip-path', 'width', 'height',
                       'backgroundColor', 'color'];
  const endpoints = (anim) => {
    let frames = [];
    try { frames = anim.effect?.getKeyframes?.() || []; } catch { return null; }
    if (!frames.length) return null;
    const pick = (f) => {
      const o = {};
      for (const k of INTERESTING) if (f[k] !== undefined) o[k] = String(f[k]);
      return o;
    };
    const from = pick(frames[0]);
    const to = pick(frames[frames.length - 1]);
    return {
      from, to,
      steps: frames.length,     // >2 means a baked spring, not a simple tween
      baked: frames.length > 3,
    };
  };

  const seen = new Map();       // animation object or synthetic key -> record
  let order = 0;

  // A finished transition is REMOVED from getAnimations(), so polling after a
  // settle delay silently misses every short one — which is most of them, and
  // is why a page full of 300ms reveals can look like a page with no motion.
  // Events are the reliable channel: they cannot be sampled late.
  const ms = (v) => Math.round(parseFloat(v || 0) * (/(^|\d)s$/.test((v || '').trim()) && !/ms$/.test((v || '').trim()) ? 1000 : 1)) || 0;
  // Split a CSS list on TOP-LEVEL commas only. Splitting naively tears
  // `cubic-bezier(0.16, 1, 0.3, 1)` into four fragments, which then read as
  // four different easings and manufacture phantom duplicate ladders.
  const splitTop = (s) => {
    const out = []; let depth = 0, cur = '';
    for (const ch of (s || '')) {
      if (ch === '(') depth++;
      else if (ch === ')') depth--;
      if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; continue; }
      cur += ch;
    }
    if (cur.trim()) out.push(cur.trim());
    return out.length ? out : [''];
  };
  const perProp = (cs, prop) => {
    const names = splitTop(cs.transitionProperty);
    const durs = splitTop(cs.transitionDuration);
    const dels = splitTop(cs.transitionDelay);
    const eas = splitTop(cs.transitionTimingFunction);
    let i = names.indexOf(prop);
    if (i < 0) i = names.indexOf('all');
    if (i < 0) i = 0;
    const at = (arr) => arr[i % arr.length];
    return { duration: ms(at(durs)), delay: ms(at(dels)), easing: at(eas) };
  };

  const record = (key, rec) => { if (!seen.has(key)) seen.set(key, { order: order++, ...rec }); };
  const where = (t) => {
    const rect = t?.getBoundingClientRect?.();
    return {
      firedAtScrollY: Math.round(scrollY),
      // where the element sat in the viewport when it fired, as a % of viewport
      // height — 85% feels responsive, 50% feels late, and this is the number
      // "fades in on scroll" leaves out
      triggerViewportPct: rect && innerHeight ? Math.round((rect.top / innerHeight) * 100) : null,
    };
  };

  document.addEventListener('transitionrun', (e) => {
    const t = e.target, prop = e.propertyName;
    if (!t.getBoundingClientRect) return;
    const cs = getComputedStyle(t);
    const timing = perProp(cs, prop);
    // Read from/to off the WAAPI object, not off computed style: during a
    // transition getComputedStyle returns the CURRENT animated value, so it
    // reports a meaningless mid-flight number (opacity 0.0723) as the start.
    // The transition's own keyframes carry the real endpoints.
    // Match the transition for THIS property. Falling back to "any transition
    // on the element" reports the first one's endpoints for every property, so
    // a transform row claims it animates opacity.
    const live = (t.getAnimations?.() || []).find((x) => x.transitionProperty === prop);
    record(`${selectorFor(t)}|${prop}|${order}`, {
      name: `transition ${prop}`, kind: 'CSSTransition', property: prop,
      target: selectorFor(t), text: (t.textContent || '').trim().slice(0, 40) || null,
      ...timing,
      values: (live && endpoints(live)) || { from: { [prop]: cs.getPropertyValue(prop) }, to: null },
      ...where(t), _t: t, _prop: prop,
    });
  }, true);

  document.addEventListener('transitionend', (e) => {
    for (const r of seen.values()) {
      if (r._t === e.target && r._prop === e.propertyName && r.values && !r.values.to) {
        r.values.to = { [e.propertyName]: getComputedStyle(e.target).getPropertyValue(e.propertyName) };
      }
    }
  }, true);

  // target+name pairs already recorded via the animationstart EVENT below —
  // consulted by the WAAPI snapshot path further down so a native CSS
  // @keyframes animation is never double-recorded under both its string key
  // here and its animation-object key there.
  const eventCovered = new Set();

  document.addEventListener('animationstart', (e) => {
    const t = e.target;
    if (!t.getBoundingClientRect) return;
    const cs = getComputedStyle(t);
    eventCovered.add(`${selectorFor(t)}|${e.animationName}`);
    record(`${selectorFor(t)}|${e.animationName}|${order}`, {
      name: e.animationName, kind: 'CSSAnimation',
      target: selectorFor(t), text: (t.textContent || '').trim().slice(0, 40) || null,
      duration: ms(cs.animationDuration.split(',')[0]),
      delay: ms(cs.animationDelay.split(',')[0]),
      // Naive split(',')[0] tears a 4-parameter cubic-bezier at its first
      // internal comma — cubic-bezier(0.34, 1.56, 0.64, 1) read back as the
      // truncated, invalid 'cubic-bezier(0.34'. Measured live: this shipped
      // a broken signature-curve value into a real capture. splitTop() is
      // already correct for the CSS-transition path below; this event-driven
      // CSS-animation path independently repeated the same mistake it fixes.
      easing: splitTop(cs.animationTimingFunction)[0],
      iterations: cs.animationIterationCount.split(',')[0],
      values: null, ...where(t),
    });
  }, true);

  // JS-driven Web Animations (Motion, GSAP's WAAPI path) raise no CSS events,
  // so they still need polling — but polled OFTEN, not once per scroll step.
  const snapshot = () => {
    for (const a of (document.getAnimations?.() || [])) {
      if (seen.has(a)) continue;
      if (a.constructor.name === 'CSSTransition') continue;   // covered by events
      const t = a.effect?.target;
      // A native CSS @keyframes animation is ALSO covered by events, the same
      // way CSSTransition is above — but the corresponding skip here was
      // missing, so every @keyframes animation was recorded TWICE, once
      // correctly via the event listener and once here with a silently WRONG
      // easing: `effect.getTiming().easing` reflects the raw KeyframeEffect
      // option, which for a browser-parsed @keyframes rule is 'linear'
      // regardless of the real animation-timing-function — measured live,
      // this planted a phantom 'linear' entry for every real curve, which
      // pollutes exactly the frequency tally the library's signature-curve
      // selection depends on ("the highest-frequency easing curve... the
      // single most reusable thing in the entry").
      if (a.constructor.name === 'CSSAnimation'
          && eventCovered.has(`${selectorFor(t)}|${a.animationName}`)) continue;
      const timing = a.effect?.getComputedTiming?.() || {};
      record(a, {
        name: a.animationName || a.transitionProperty || 'js-animation',
        kind: a.constructor.name,
        target: selectorFor(t), text: (t?.textContent || '').trim().slice(0, 40) || null,
        duration: Math.round(timing.duration) || null,
        delay: Math.round(timing.delay) || 0,
        easing: a.effect?.getTiming?.().easing || null,
        iterations: timing.iterations === Infinity ? 'infinite' : timing.iterations,
        values: endpoints(a), ...where(t),
      });
      seen.set(a, seen.get(a) || [...seen.values()].pop());
    }
  };

  window.__motionHooks = true;
  window.__motionRun = async () => {

  // ---- Framer entrance payloads: JSON in the DOM, no instrumentation needed.
  const appear = [...document.querySelectorAll('script[type="framer/appear"]')]
    .map((s) => { try { return JSON.parse(s.textContent); } catch { return null; } })
    .filter(Boolean);

  // ---- Scroll and snapshot.
  const startY = scrollY;
  const pageHeight = () => document.body.scrollHeight;
  // Poll fast and continuously rather than once per step, so a JS animation
  // that starts and finishes inside one settle window is still caught.
  const poller = setInterval(snapshot, 40);
  window.scrollTo(0, 0);
  await sleep(SETTLE);
  for (let i = 1; i <= STEPS; i++) {
    window.scrollTo(0, Math.round((pageHeight() - innerHeight) * (i / STEPS)));
    await sleep(SETTLE);
  }
  clearInterval(poller);
  window.scrollTo(0, startY);

  // A zero-duration transition is not an animation. Browsers still raise
  // transitionrun for them, and on one real site 1650 of 1724 records were
  // these — burying the 74 that actually carried the site's signature curve.
  const anims = [...seen.values()]
    .filter((r) => r && r.order !== undefined)
    .filter((r) => r.kind !== 'CSSTransition' || (r.duration || 0) > 0);
  const droppedZero = [...seen.values()].filter(
    (r) => r && r.kind === 'CSSTransition' && !(r.duration > 0)).length;
  for (const a of anims) { delete a._t; delete a._prop; }   // drop DOM refs before serialising

  // A baked spring serialises as a `linear()` with 80+ stops — kilobytes of
  // noise per row. Keep the shape, drop the transcript.
  const shorten = (e) => (typeof e === 'string' && e.length > 90 && e.startsWith('linear('))
    ? `linear(baked spring, ${e.split(',').length} stops)` : e;
  for (const a of anims) a.easing = shorten(a.easing);

  // ---- Derive the stagger ladder. A group of animations sharing duration and
  // easing is one choreographed set; the gaps between their delays are the
  // stagger, which is what "staggered 100ms left to right" actually means.
  const groups = {};
  for (const a of anims) {
    const key = `${a.duration}|${a.easing}|${JSON.stringify(a.values?.to || {})}`;
    (groups[key] ||= []).push(a);
  }
  const ladders = Object.entries(groups)
    .filter(([, g]) => g.length > 1)
    .map(([key, g]) => {
      const delays = [...new Set(g.map((x) => x.delay))].sort((a, b) => a - b);
      const gaps = delays.slice(1).map((d, i) => d - delays[i]);
      return {
        count: g.length,
        duration: g[0].duration,
        easing: g[0].easing,
        to: g[0].values?.to,
        delays,
        stagger: gaps.length ? [...new Set(gaps)] : null,
        sample: g.slice(0, 3).map((x) => x.target),
      };
    })
    .sort((a, b) => b.count - a.count);

  // Guard on null/empty, NOT on truthiness. `v &&` silently drops every zero
  // bucket, and for triggerViewportPct 0 is a real, meaningful value: an element
  // already in view when its animation fires. Measured on framer.media 2026-08-17,
  // where 0% was the LARGEST bucket at 24 uses and vanished from the summary
  // entirely, leaving four buckets summing to 63 against a reported
  // scrollTriggered of 87. The discrepancy between those two numbers is the only
  // reason it was caught, so keep both in the output.
  const tally = (arr) => Object.entries(
    arr.reduce((m, v) => ((v !== null && v !== undefined && v !== '') && (m[v] = (m[v] || 0) + 1), m), {}))
    .sort((a, b) => b[1] - a[1]);

  const out = {
    url: location.href,
    viewport: { w: innerWidth, h: innerHeight },
    pageHeight: pageHeight(),
    scrollSteps: STEPS,
    animationsSeen: anims.length,
    zeroDurationDropped: droppedZero,
    byKind: Object.fromEntries(tally(anims.map((a) => a.kind))),
    easingByCount: tally(anims.map((a) => a.easing)),
    durationByCount: tally(anims.map((a) => a.duration)),
    scrollTriggered: anims.filter((a) => a.firedAtScrollY > 0).length,
    triggerOffsets: tally(anims.filter((a) => a.firedAtScrollY > 0)
      .map((a) => a.triggerViewportPct)),
    ladders,
    animations: anims,
    framerAppear: appear.length ? appear : null,
    framerAppearNote: appear.length
      ? `${appear.length} framer/appear payload(s) — Framer entrance motion lives here, not in CSS.`
      : null,
    reducedMotion: {
      mediaQueryPresent: [...document.styleSheets].some((s) => {
        try { return [...s.cssRules].some((r) => /prefers-reduced-motion/.test(r.cssText)); }
        catch { return false; }
      }),
      currentlyReduced: matchMedia('(prefers-reduced-motion: reduce)').matches,
    },
  };

  out.note = anims.length === 0
    ? 'Nothing fired. Either the page has no motion, or it mounts late — re-run after interaction.'
    : `${anims.length} animations, ${out.scrollTriggered} scroll-triggered. `
      + 'Trigger offsets are viewport % at fire time; use them as START in the spec.';

  window.__motionSpec = out;
  const json = JSON.stringify(out, null, 1);
  if (typeof copy === 'function') { copy(json); console.log('Motion spec copied —', json.length, 'chars.'); }
  else console.log(json);
  return out;
  };   // end __motionRun

  // Injected at document-start there is no page to scroll yet: install and wait.
  // Run standalone (paste / plain evaluate) it hooks and immediately runs, which
  // still catches everything scroll-triggered — just not the load-time reveals.
  if (document.readyState === 'loading') return { installed: true };
  return window.__motionRun();
})();
