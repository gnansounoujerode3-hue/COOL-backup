# fusionai.framer.website

**Callable as: Fluence** (aliases: fusionai.framer.website, Fusion AI)

AI-workflow-automation SaaS marketing template (dark theme). Captured
2026-08-10 @ 1280x720 (this pass's browser-pane viewport was unreliable,
see gotcha 5, so treat this figure as nominal, not measured). Stack: Framer (SSR + React 19 hydration,
bundled Motion library, rolldown runtime chunks, client-side CMS collection
for the blog). **Mirror path**, scripted (`crawl.py` + `build.py`), 17/17
pages, rebrand target ("Systo Fusion").

## Type: flat black, one workhorse sans

UI text runs on a single sans family (General Sans-class); no serif/display
face observed distinct from the body face on this pass. Unlike every prior
Framer capture in this library, no second display font was found in a quick
scan. Re-verify with a full census before relying on this.

## Layout

Standard Framer triad confirmed a **sixth+** time:
**0–809.98 / 810–1199.98 / 1200+**, full SSR variant per breakpoint gated by
`hidden-<hash>` classes (pure CSS `@media(min-width:…)`, no JS toggle).

Multi-page site: home, about-us, pricing, integrations, blog (listing + 7
posts), contact, waitlist, changelog, privacy-policy, terms-conditions: 17
total, matches sitemap exactly (0 listed-but-uncrawled, 0 crawled-but-unlisted).

## Colour

Black background (`rgb(0,0,0)`), white text, one coral/orange accent on CTAs
and tags. Not separately tallied this pass: rebrand target, not a pure Match.

## Motion

**Motion fidelity: none**, not captured this pass (prioritized rebrand +
runtime-correctness work, per this library's standing convention for a
rebrand target). Framer's own `data-framer-appear-animation="no-preference"`
runtime already respects `prefers-reduced-motion` without any extra work.

## Template taxonomy

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Marketing page | 9 (home/about/pricing/integrations/contact/waitlist/changelog/privacy/terms) | Nav, footer | Section composition |
| Blog listing | 1 | Filter/grid chrome | Card count (7) |
| Blog post | 7 | Nav, footer, "Related blogs" band | Title, tag, date, body |

## Gotchas hit while rebuilding

Framer's badge/promo-widget removal and click-hijack fix from the
**framer.media (Homy)** entry all reproduced identically here. See that
entry for the base recipe. New findings specific to this capture:

1. **Removing `#__framer-badge-container` from the static mirror crashes the
   page with an uncaught, non-recoverable error: a step beyond Homy's
   "hides the container" finding.** The badge widget mounts via its own
   *separate* `ReactDOM.createRoot()` call, scheduled async (idle callback),
   independent of the main hydration tree. `createRoot(null)` throws
   synchronously the instant that container element has already been
   deleted from the DOM by the time the badge-mount code runs (which it
   reliably is, whether removed statically in the HTML or removed
   synchronously by an early corrector script). **Fix: never remove the
   badge container node. Hide it with `display:none!important` instead**
   (via a live corrector, `el.style.setProperty('display','none','important')`)
   so `getElementById` always resolves to a valid element and `createRoot`
   never sees null. Isolated by diffing against an unmodified control mirror
   that never threw. The same rebrand build with the container merely
   *hidden* rather than removed produced 0 uncaught errors.
2. **Removing a normal (non-portal) component from the static mirror, the
   "Get Template" promo card, also reverts on hydration, same as Homy's
   text-node finding, but for a whole subtree.** React's hydration mismatch
   repair re-inserts whatever the client bundle expects when the server DOM
   doesn't match, which for a *removed* node means it comes back. Homy's
   finding was scoped to text; this generalises it to entire missing
   components. Fix: same as text. Leave the static markup untouched, kill
   it live via a MutationObserver-driven corrector (`el.remove()` is safe
   *after* mount; only *before*-mount removal fights hydration).
3. **A page-level `[data-framer-name="Icon"]` component whose props resolve
   to a Phosphor-icon name lazy-loads the icon's code **from framer.com**
   at runtime, unconditionally, via a URL built from a bare literal
   (`Wn = 'https://framer.com/m/phosphor-icons/'`) inside `script_main`'s
   own source, not discoverable by any static asset scan, and present on
   the reference's *own* production hosting too (this is not a mirroring
   defect). Fires once per icon instance on the page (4 footer social
   icons here). Fix: intercept at the server layer. Any request whose path
   contains `phosphor-icons` or `framer.com` gets a tiny no-op ES module
   (`export default function Icon(){return null}`) instead of a real
   fetch. Icon renders empty (matches the mirror's un-hydrated state
   anyway); zero external requests, zero console 404s.
4. **A CMS Collection's data pair (`<id>-chunk-default-0.framercms` /
   `<id>-indexes-default-0.framercms`) 404s at the plain literal path the
   runtime requests, confirmed 404 even against the reference's own
   production origin, not just our mirror.** Framer treats a failed
   Collection fetch as genuinely fatal: `Id`→`evalQuery`→`lookupItems`
   throws all the way up and tears the *entire page's* rendered tree down
   to a near-empty shell (same "fatal on CMS failure" family as the
   `?range=` gotcha already in this library, different trigger). This hit
   both the blog *listing* (renders its 7 post cards from this collection
   client-side, even though the same cards are also fully present in the
   static SSR HTML) and every blog *post* page (looks up its own record by
   slug for a "Related blogs" cross-reference). A real, if short, copy of
   both files was incidentally captured by the crawl under a **query-string
   hash-suffixed filename** (`build.py`'s own `stem__<8hex>.ext` collision
   handling). Copying that to the plain filename the runtime actually
   requests fixed the blog *listing* outright. The blog *post* pages'
   `range: {from,to}` spans still occasionally exceed that captured file's
   true length (`Reading out of bounds`); the captured copy is real but
   incomplete, likely because whatever incidental request produced it
   didn't span the whole document. **Full fix required patching the
   minified reader chain to fail soft at every layer** rather than trying
   to reconstruct the exact byte-complete binary CMS format:
   `loadModel()` wrapped in try/catch → `{entries:[]}`; the low-level byte
   reader's `readJson()` wrapped to return `null` on a `JSON.parse` failure
   instead of throwing; the page component's own per-field accessor
   (`d=e=>{if(!le)throw…}`) changed to return `undefined` instead of
   throwing "No data matches path variables". None of these change
   behaviour on a healthy data path; they only stop a crash on this one.
5. **Fixing gotcha 4 exposed a second, independent effect: once hydration's
   Collection re-query resolves (even to nothing, via the fail-soft path
   above), Framer discards the perfectly good SSR article body and
   re-renders the blog-post page's content block from the (now-empty)
   client data (a content-completeness regression, not a crash).** This is
   the "hydration reverts static content" family (gotcha 2/Homy's finding)
   at its most severe: not text, not one component, but the page's entire
   primary content. No amount of failing the query "more gracefully" fixes
   this, because the client render *succeeding* with empty data is exactly
   what causes it. **Fix: a content-regression guard**. Snapshot
   `#main.innerHTML` at the very top of an early inline script (before the
   async hydration bundle has had time to run), then on a timer well past
   hydration settling (1.2s and 3s after load), compare `#main.innerText`
   length against the snapshot; if it collapsed to under ~40% of the
   original, restore the saved HTML and re-run the text-rebrand corrector
   over the restored subtree. A **first attempt at this same idea using
   the whole `#main` element was too blunt**: because it was taken as one
   HTML blob, restoring it also reverted the SSR breakpoint-variant
   visibility state if hydration had touched anything nearby, and briefly
   looked like a "duplicate nav" regression: false alarm, traced to this
   test browser pane reporting `window.innerWidth === 0` (see this
   library's standing "pane is not a measurement instrument" caution:
   `getComputedStyle().display` on an element only reflects *its own*
   declared CSS value, not whether a `display:none` ancestor is actually
   hiding it; check `offsetParent === null` or a real bounding rect
   instead). The restore itself does not corrupt the breakpoint-gating
   classes; it merely reproduced a measurement artifact this library
   already knew about, confirmed by finding `offsetParent === null` on the
   variant that should be hidden.
6. **A background server process on Windows can keep answering requests
   on a port long after the "new" server process starts on the same
   port, silently.** Windows' permissive `SO_REUSEADDR` behaviour (unlike
   Linux) allows two processes to bind the *same* address:port
   simultaneously with no bind error, and request routing between them is
   unpredictable. Cost real debugging time twice in this session: once
   diagnosed as "my fix didn't work" when it had, and once as a phantom
   file-edit staleness ("edited a file, server still returns old bytes")
   before realizing an old `serve.py` process was still alive answering
   some fraction of requests. **Always verify by PID + `Get-NetTCPConnection
   -LocalPort N -State Listen`, not just "did my start command succeed."**
   Also: browser HTTP caching without `Cache-Control` on the stock static
   handler let a genuinely-fixed `.mjs` file appear stale in-browser even
   after the *correct* single server process was serving fresh bytes.
   Send `Cache-Control: no-store` unconditionally on every response while a
   mirror is under active iteration.
7. Also present, both mundane and already covered by this library's
   existing entries: 3 assets genuinely 404 upstream (the CMS chunk/index
   pair above, plus one `${Wn}${_}.js` runtime-templated literal a static
   scan can never resolve: expected, matches the "runtime-built asset
   paths are invisible to static analysis" cross-site pattern); Framer's
   client router still hijacks a correctly-rewritten `<a href>` post-hydration
   (Homy gotcha 7), but here the *rewritten* href itself gets reset back to
   the pretty-URL form by Framer's own router, not just re-intercepted, so
   the click-hijack fix's target must be resolved against a server-side
   pretty-URL fallback (flatten `/a/b` → `a__b.html`, same rule
   `crawl.py`'s own urlmap already uses) rather than assuming the rewritten
   `.html` href survives to click time.

## Verification achieved

Full 17-page mirror served locally. 0 console errors on every page (verified
in a fresh browser tab per page, not accumulated across navigations; this
tool's console log persists across same-tab navigations and produces false
positives if not reset). 0 external requests on every page checked
(`performance.getEntriesByType('resource')` swept for non-origin, non-`data:`
entries). Text/brand-swap verified against the live DOM post-hydration, not
just served HTML (0 residual "Fluence"/"Fusion AI" outside the corrector
script's own pattern list, confirmed by regex sweep with that block
excluded). Click-through navigation confirmed via a real dispatched click
event (not just href inspection) landing on the correct page with a fresh,
correct `document.title`. Blog-post article content confirmed present and
non-empty post-restore (~3.5k chars innerText per post, consistent across
all 7). No pixel-diff run against the reference this pass (rebrand target,
prioritized runtime-correctness debugging over a Step 4 diff). Motion
fidelity above is `none` for the same reason. A hand-built Three.js layer
(rotating wireframe node-network) added to the homepage hero only, per
user request; not present on any other page, and not visually confirmed at
a real viewport size in this session (only via `WebGLRenderingContext`
presence + 0 console errors). This browser pane reported
`window.innerWidth === 0` throughout the session, a known measurement
limitation this library already flags; recommend a real-browser screenshot
check before considering the hero visual done.
