# Design library: index

One line per site captured. Newest last. Read this before a capture; append to it
after. Full entries live beside this file as `<domain>.md`.

**Every entry is callable by name.** "Build my site, reference: <a name from the
*Call it* column below>"
resolves through the *Call it* column below (match case-insensitively against
the name, the domain, or any alias in the entry), then runs Adapt from the
entry's measured system (see "Design from a named reference" in SKILL.md).

**What belongs here:** design *system* facts: palettes, type scales, spacing,
easing curves, breakpoints, layout mechanics, structural patterns, and the
gotchas hit while rebuilding. Measurements and patterns, which are the shared
vocabulary of web design.

**What does not:** body copy, imagery, logos, or any asset. Those stay in the
local mirror for the job that needed them. The library is knowledge, not content.

| Call it | Site | Captured | Path | Motion fidelity · signature | Notable |
|---|---|---|---|---|---|
| **YouTube** | [youtube.com](youtube.com.md) | 2026-07-29 | rebuild | **partial** · `cubic-bezier(.05,0,0,1)` @ .1–.3s | Tonal white-alpha surface system; grid column count is a JS-set CSS var, not a media query |
| **Phenomenon** | [phenomenonstudio.com](phenomenonstudio.com.md) | 2026-07-30 | mirror (scripted) | **spec** · `cubic-bezier(.22,1,.36,1)` @ .3s | Sticky-stacking section choreography; `.isview`+`.visible` scroll-reveal gate |
| **Lando Norris** | [landonorris.com](landonorris.com.md) | 2026-07-30, +2026-08-17 socials-deck source-read | mirror (scripted) | **signature-only** page-wide · `cubic-bezier(.65,.05,0,1)` @ .75s; **`spec` for the socials fanned deck** (entrance `power2.out` .8s stagger .5 from-end → `elastic.out(1,0.75)` 1.2s stagger .2 from-centre, overlap −0.4s; hover 0.5s elastic, 50ms leave debounce) | Whole rem scale is one `calc()` pinned to a 1728 design width; WebGL hero randomises its livery per load; Webflow SRI silently voids the mirror. **2026-08-17 correction: the 2026-07-31 deck addendum's "no transition, no animation, no hover state" was WRONG**: read from a settled end-state. The deck has a scroll entrance and a rich hover where the hovered card keeps its own x and fan angle (lifts 2.5rem, ×1.08) and *shoves neighbours outward* by `8·p·c` rem; it never snaps to centre. Also corrects "no GSAP": `window.gsapVersions` = 3.13.0 and `themeScrollTriggers` exist even though `window.gsap` is undefined. Geometry is **rem against the fluid root**, not the px this entry first recorded |
| **CreateStudio** | [createstudio.framer.media](createstudio.framer.media.md) | 2026-07-30 | mirror (scripted) | **spec** · none in CSS: all motion is JS (Motion lib) | Framer: SSR'd but script-*dependent* (73% static vs 98.5% scripted); `new URL()` bases must stay absolute or all text vanishes; one `#ff6041` accent over a full greyscale ramp |
| **OSA** | [osa.framer.website](osa.framer.website.md) | 2026-07-30 | mirror (scripted) | **partial** · none in CSS: all motion is JS (Motion lib) | Second Framer capture: reusing the hardened build hit 99.37% vs a 99.46% ceiling first try. Satoshi 500 carries the whole UI, Instrument Serif only at 46–54px display. CMS `-chunk-`/`-indexes-` pairs |
| **Phillia** | [philllia.com](philllia.com.md) | 2026-07-30 | capture only (Adapt) | **signature-only** · `cubic-bezier(.22,1,.36,1)` / `(.16,1,.3,1)` @ .42s | Four named curves for four *jobs* + stagger/travel ladders, the most complete motion-token set in the library. Next.js with **no JS animation library at all**. Two palettes in one stylesheet |
| **Systo** | [systo-ai.com](systo-ai.com.md) | 2026-07-30, +2026-08-18 contrast correction | rendered-DOM (Adapt content source) | **partial** · word-reveal hero + count-ups | Kyle's own site; first library-composed redesign target (6 donors). SPA shell undercounts content ~8×. Extract from rendered DOM. Serif-display-only discipline confirmed a 4th time. **2026-08-18: accent `#ff532e` on cream measures 2.96:1, fails the BRAND.md's own AA claim**: text-safe fix `#fa5029` (3.10:1) verified building two HyperFrames videos from this brand; not yet applied to the live site |
| **FintechX** | [fintechx-wbs.framer.website](fintechx-wbs.framer.website.md) | 2026-07-30 | capture only (Adapt donor) | **partial** · baked-spring fade-up: `translateY(20/10px)`+opacity @ 400/600/1000ms, ~100ms ladder | Fourth Framer capture, and it **settles the onefin easing question**: `cubic-bezier(.44,0,.56,1) @ .4s` and the `linear(0, 0.024, 0.0823, …)` spring appear byte-identical on both unrelated templates. Framer/Motion defaults, not authorship. Reusable bento (3×380/gap 30, 393+393+374-span vs 528+239) and a dashboard-showcase frame whose UI bleeds off the bottom edge. Band names are generic, so identify by geometry |
| **OneFin** | [onefin.framer.website](onefin.framer.website.md) | 2026-07-30 | mirror (scripted) + 1440 runtime addendum + About-section spec | **partial** page-wide; **spec** for the About/statement section (scrub profile, pointer-parallax coefficients, per-character reveal) · `cubic-bezier(.44,0,.56,1)` @ .4s + springs; **per-character `blur(10px)→0` @400ms, 50ms/char uncapped** | Third Framer capture, and the one that broke three priors: Framer **does** ship CSS easing (45 uses, same curve as its appear tween); breakpoint edges are integer *and* `.98`. Found the `vary: Accept` AVIF/PNG trap. 25/25 pages all at ceiling, geometry 100.00% exact at 0px |
| **Apple** | [apple.com](apple.com.md) | 2026-08-03, +2026-08-11 addendum | mirror (static), scoped 30/846 · + 3-surface Liquid Glass capture (Adapt) | **partial** · `ease-in-out` @ 1000ms (fades) + `cubic-bezier(.4,…)` @ 320ms (UI); only 1/43 scroll-triggered. Addendum adds a buildable reveal spec: 800ms `cubic-bezier(.4,0,.25,1)`, `opacity 0→1` + `translateY(20%)→0`, IntersectionObserver, fires at ~97–101% viewport height, no stagger | Hand-built, no framework fingerprint; SF Pro Display/Text, no fluid rem driver. Found and fixed a real engine bug: `srcset` was fetched but never rewritten, leaving real photos blank (`<picture>` doesn't fall back to `<img>` on a 404'd `<source>`). Real JSON-LD present (rare in this library). **2026-08-11 addendum, read before any "Liquid Glass" job: Apple's web properties are NOT rendered in Liquid Glass** (zero lensing/refraction/specular/inset-highlight in their CSS), so measure the web chrome and take the material from Apple's docs. Real web glass recipe is small: `saturate(180%) blur(20px)` over 70–80% alpha, one 1px `rgba(29,29,31,.2)` `::after` hairline, no border/inset/shadow, `@supports` + alpha-to-0.9 fallback + `-noblur` hatch. Documented rules that change a build: glass is the **functional layer only** (Apple prohibits it in the content layer → two surface systems, not one), regular vs clear, 35% dim for clear over bright, no inherent colour, larger elements more opaque. Also: browser-level CDP endpoint has no Page/Runtime domains; Sheets coerces `N/M` cells into dates in xlsx while CSV keeps the text |
| **MEXC** | [mexc.co](mexc.co.md) | 2026-08-08 | mirror (static), scoped 4/1700+ | **none** · not captured this pass | Live crypto exchange: scripts deliberately stripped for safety (real trading/account app), so live price/fee/chart widgets render blank by design. Pure-black theme, `#1463FF` accent, pill buttons. Found: Git-Bash `MSYS_NO_PATHCONV` silently corrupts `crawl.py --exclude` regexes starting `^/`; `should_follow()` filters pre-redirect hrefs so an excluded link can still land via a redirect; raw SSR shell inconsistently ships `data-theme="light"` on 3/4 routes while the live hydrated site always renders dark |
| **Wise.com** | [wise.com](wise.com.md) | 2026-08-08 | mirror, scoped 142/174 | **partial** · `cubic-bezier(.34,1,.64,1)` @ 1500/1600ms; 50/100ms stagger | Next.js, geo-personalized homepage (no redirect; verify locale before trusting a capture). Found and fixed seven real engine bugs across build.py/serve.py/motion-extract.js: a JS template-literal interpolation crashed the URL resolver; a raw space in a CDN filename raised InvalidURL; an inline GTM/Mixpanel bootstrap survived every markup rewrite and still beaconed production analytics; runtime-constructed webpack chunk URLs 404'd (serve.py cdn/ fallback) and two DISCOVERY gaps meant some chunks were never mirrored at all (a webpack chunk-id ternary map, and _buildManifest.js's route→chunk arrays); a vendor SDK bundled INLINE (not as a separate file) crashed React's commit-phase error boundary on every page, which a global window-error shim could NOT catch: fixed by hardening the SDK's own unguarded `get_config` accessor text. Also fixed motion-extract.js: a naive comma-split truncated 4-param cubic-beziers, and CSSAnimation was double-recorded against CSSTransition's own "covered by events" exclusion, manufacturing phantom `linear` curves. One real-time pricing-comparison widget is 100% client-fetched with no SSR fallback: architecturally uncapturable, drives every reported delta (68.66% text, 1 vs 28 animations) |
| **Homy** | [framer.media](framer.media.md) | 2026-08-10, +2026-08-17 motion/type/colour re-capture @ 1424×805 | mirror (scripted), 21/21 pages, rebrand target ("Systo Estate") | **spec** · `ease-out` @ **400ms** (87 of 88 firings, the site's entire CSS curve vocabulary); entrance is a Framer appear **spring 320/60/1, overdamped (ζ 1.677), delays 0/0.2/0.2/0.3s**; signature is a **per-word statement reveal** (43 spans = 22 words + 21 separators, `blur(10px)→0` + `color transparent→rgb(8,11,15)`, both 400ms, **zero delay: the ladder is scroll position**) inside a sticky band; plus one 36857ms `linear` infinite ticker | Real-estate template, fully achromatic palette (no accent color at all), Switzer + display-only Special Gothic (exactly 1 element). Fifth Framer capture, third+ confirming the 0–809.98/810–1199.98/1200+ breakpoint triad, and the 2026-08-17 pass confirms it **from the runtime `framer/appear` payload's own hash→media-query map**, so a Framer site's breakpoints are readable out of one inline script without touching CSS. Type system: line-height is a function of size (1.6 → 1.4 → 1.2 → 1.0 → 0.9 → 0.8 as px climbs) and negative tracking scales in em (−0.02em @48 → −0.04em @54 → −0.0427em @120), second entry after polestar confirming the em rule. Body colour is `rgb(75,91,99)` (767 elements), not black. Structure is `position: sticky` used three ways (hero pin, three 805px featured cards that stack, a 2500px masked reveal) and **all three produce zero animation rows**. **Read the Adapt warning before ordering this by name: `design-gate.py --mode adapt` returns NOT DONE, 7 failing** (nav 84px/2 rows, 14 distinct radii, eyebrow budget, wrapping CTA labels, and no `prefers-reduced-motion` anywhere; the reference ships none, so an Adapt must author it). Two instrument findings: a mirror's unstyled links put `rgb(0,0,238)` third in the colour census (242 hits, ahead of the real ink) and made the gate report a CTA contrast failure that does not exist on the reference; and `motion-extract.js`'s `triggerOffsets` field drops the 0% bucket (`tally()` treats `0` as falsy), hiding the largest of five. Reconcile it against `animations[].triggerViewportPct`, and distrust any histogram that doesn't sum to `scrollTriggered`. Two hydration findings beyond prior entries: Framer's bundle reverts edited **static text nodes** (title/meta/body copy) post-mount from its own baked page-config, not just hidden components: needs a live MutationObserver corrector scoped to mutation records only (a naive full-document re-walk inside the callback pegged the main thread against this page's live counters and hung page load); and anything inserted *inside* `#main` gets hydration-wiped (React #418), including a plain `<canvas>`. Build new content as a sibling outside `#main` and self-position via `getBoundingClientRect()`. Also: Lenis-owned scroll effects don't respond to synthetic `scrollTo()`, only real wheel events; and a WebGL layer can be provably rendering (`renderer.info`, same-task `readPixels`) while absent from a headless `page.screenshot()`, a second confirmed case of the browser-pane measurement-instrument problem, this time in headless Playwright itself |
| **Fluence** | [fusionai.framer.website](fusionai.framer.website.md) | 2026-08-10 | mirror (scripted), 17/17 pages, rebrand target ("Systo Fusion") | **none** · not captured this pass | AI-workflow SaaS template, black/coral dark theme. Sixth Framer capture. Generalises Homy's hydration findings from *text* to *whole components*: removing the "Made in Framer" badge container from static markup crashes the page outright (it mounts via a separate `createRoot()` call that throws on a null container; hide with `display:none`, never remove the node); removing a promo-card component reverts on hydration same as text does. A CMS Collection chunk/index pair 404s even on the reference's own production origin: Framer treats that as fatal and collapses the whole page, not just the collection; fixed by making the minified reader chain fail soft at every layer (`loadModel`/`readJson`/per-field accessor), then discovered fixing the crash exposes a second effect: hydration still discards good SSR article content in favour of the now-successfully-empty client render, needing a snapshot-and-restore content-regression guard on `#main`. Also: Phosphor-icon components lazy-fetch from `framer.com` unconditionally (present on production too, not a mirroring artifact): stub server-side; and confirmed Windows' permissive `SO_REUSEADDR` lets two server processes silently share a port, producing phantom "my fix didn't work" debugging sessions. Verify by PID, not by whether the start command succeeded |
| **Agentwise** | [agentwise.framer.website](agentwise.framer.website.md) | 2026-08-10 | mirror (scripted), 21/21 pages, rebrand target | **partial** · `cubic-bezier(.65,0,.35,1)` @ .9s/.6s, 80ms ladder, appear delay .4s | Real-estate-agent template, Inter/Inter Display only (no serif, breaks that pattern). Sixth Framer capture. `build.py`'s `/../site/cdn/` bug still isn't fixed in the script itself, only worked around per-build. Always run it bare with no `--out`/`--cdn` flags. New, more severe finding: **Git-Bash `ln -s` on a directory silently fails to produce a link Windows-native processes can see**, so edits to the true target never reach what the file server actually serves: produces React hydration errors indistinguishable from a live framework bug; fix is `cp -r` a real copy, never trust the symlink for anything Chrome/Python reads. Also: `.framercms` is confirmed length-prefixed binary (a type byte + 4-byte length before each string): same-length substitutions are safe in place, different-length ones are not without patching offsets; a bare-word CMS text search for a first name false-positived 11× on "Mark**et**"; and a `searchIndex-*.json` sitewide full-text asset carries its own copy of every page's text, invisible to a `*.html`/`*.mjs`/`*.css`-only rebrand glob. One confirmed-benign, unfixable class: a decrypt/scramble hero-heading animation frozen mid-reveal by the crawl produces a real but self-healing hydration mismatch with zero visible defect |
| **Salix** | [salix.framer.website](salix.framer.website.md) | 2026-08-10 | mirror (scripted), 51/51 pages, rebrand target ("Systolix") | **none** · not captured this pass | SaaS/CRM template, 7th Framer capture. **Breaks the previously-universal 809.98/810 breakpoint**: this site uses 767.98/768 instead, proving the low breakpoint is per-template, not a platform constant. Fully reverse-engineered the `.framercms` binary format (string field = tag `0x0C`+4-byte-BE-length+content; paired `-indexes-` offset table = tag `0x0C` id + tag `0x0B`+11-byte-BE-offset+4-byte-BE-length, items contiguous), but a length-changing edit made per that model still corrupted 2/8 case-study pages **silently, with zero console error** (content truncated to 1/4 length) despite a self-consistent, verified-contiguous offset table; safe fix was reverting to the pristine fetch and correcting the *rendered* text instead. Root cause of the wrong CMS URLs in the first place: the crawler's static asset scan found two plausible-but-wrong CDN prefixes (`/modules/…`, `/sites/…`, both 403) while the live runtime actually requests a third (`/cms/<hash1>/<hash2>/…`) assembled at runtime. Extends "runtime-built asset paths are invisible to static analysis" from relative import specifiers to CDN host paths. New DOM-rebrand finding: a per-character kinetic-reveal heading (one `<span>` per letter, no per-character stagger data) makes `document.body.innerText` contain a brand word that **no individual text node does**: a text-node-level MutationObserver guard (the pattern that worked on every prior Framer rebrand here) silently does nothing; fix by collapsing the smallest containing *element* once settled. Also: hero "product screenshot" images ship as ~5 responsive srcset variants per logical asset, each independently served and each needing its own proportional patch: fixing only the variant your test viewport happens to load leaves the rest wrong. |
| **Hanzo** | [hanzo.framer.website](hanzo.framer.website.md) | 2026-08-10 | mirror (scripted), 7/7 pages, rebrand target ("Syszo") | **none** · not captured this pass | Single-designer portfolio template, flat Inter/Inter Display + a rare `Fragment Mono` label accent. Seventh Framer capture, fourth+ reconfirming the 809.98/1199.98/1200 breakpoint triad. Major new finding: **a subtree-wide `MutationObserver`-based hydration guard (the Homy/Fluence pattern) can hang real headless Chrome outright** on a page whose headings wrap every character in its own reveal `<span>`: querying the DOM from inside the observer callback per mutation compounds into an unrecoverable main-thread stall (reproduced via a 4-way bisect: pristine loads fine, rebrand.py-only loads fine and already carries correct `document.title`, adding the observer hangs `Runtime.evaluate` past 120s every time). Fix: hide Framer's badge/CTA with a plain CSS `!important` rule instead of JS (zero runtime cost, nothing for hydration to revert), and make title/meta correction a one-shot post-load check, never a standing observer. Also confirmed directly from this build's own bundle: the "Made in Framer" badge mounts via a separate React root (`getElementById` + a bare `createRoot`-style call), so removing the node, not just hiding it, throws on any page where the container is missing |
| **Retirement Architects** | [retirementarchitects.com](retirementarchitects.com.md) | 2026-08-13 | capture only (Adapt content source) | **none** · not captured (Divi; motion is trivial) | WordPress 6.9.7 + Divi 4.27.6 redesign target. Measured what a dated Divi build actually costs: a ~3000px hero that is one stock photo of a glass office block with a 70px headline in its corner, **12,943px total page height** (the rebuild carries the same content in 6,757px), a ~600px empty white gap mid-page, four font families with no division of labour (Montserrat/Lato/Oswald + Divi's ETMODULES icon font, which leaks a stray "3" glyph into three buttons), and 18px/36px body. Yoast sitemap overstates the site ~8x (187 of 241 URLs are blog posts). Four legally-required disclosures site-wide, set at ~8px grey. `/dipl-team-member/karlan-tucker/` 404s but still renders a styled page, so a captured 404 looks like a real small page |
| **Resend** | [resend.com](resend.com.md) | undated | motion-only audit (not produced by this engine) | **partial** · `ease-out` @ .3s (45% of durations) | Motion census only: ranked curves, duration frequencies, two scroll offsets (hero 20% / cards 35% viewport) and hover `scale(1.05)`. No type, colour, spacing or layout captured, so it is a motion donor and cannot carry a build alone. Originally filed as `spec`; downgraded to `partial` because it has no per-animation mapping; a `spec` claim over a census is exactly what `library-lint.py` exists to catch, and `motion-spec.py` would otherwise have handed a build a motion spec with no target, trigger or from/to in it |
| **Polestar** | [polestar.com](polestar.com.md) | 2026-08-16 | capture only (Adapt donor) | **partial** · `cubic-bezier(0.65,0,0,1)` @ .15s (52 uses); only 8 animations page-wide, 1 scroll-triggered | The most disciplined type system in the library: **one family, weight 400, 762/763 sampled elements**, with hierarchy carried entirely by size, line-height and tracking. Display line-height is exactly **1.0** (110/110 and 30/30), body 1.125. Negative tracking scales in em (−0.045 @110px → −0.008 @12px), so copy the ratio not the px. Ink is `rgb(16,24,32)` (blue-shifted near-black, the same refusal of `#000` phenomenon makes at `rgb(8,13,16)`) against a warm `rgb(236,236,231)` off-white. **No brand accent anywhere in the UI**; the photography carries all the colour. Salesforce Embedded Service chat is bundled, so filter `lwc-*`/`embeddedService*` from every census or the palette reads twice its real size |
| **Rivian** | [rivian.com](rivian.com.md) | 2026-08-16 | motion-only capture | **partial** · Tailwind defaults (`cubic-bezier(.4,0,.6,1)` @2000ms `animate-pulse`); **0 scroll-triggered on a 16,443px page** | Motion only: no type, colour, spacing or layout captured, so it cannot carry a build. Exists to corroborate the automotive-OEM motion pattern below. Captured easings are Tailwind utilities, not authorship |
| **Antidote** | [antidote.email](antidote.email.md) | 2026-08-17 | capture only (Transfer, 2 sections) | **none** · not swept for hover/entrance | Two components only: a "portfolio wall" (Webflow class names imply a marquee; measured static, `transform` identical across two reads 1.2s apart, `position:static`) of 400×902px tall cards, 8px radius, hard **zero-blur offset shadow** `-6px 6px 0 0`; and a testimonial "collage" that is really just `flex-wrap` + `justify-content:center` on variably-sized screenshots (16px radius, soft 5px-blur shadow); the scattered look is emergent, not absolute-positioned or rotated. Deliberate two-shadow-language page: hard sticker shadow = curated work, soft shadow = candid screenshot |
| **Nova** | [novaapptemplate.framer.website](novaapptemplate.framer.website.md) | 2026-08-18 | capture only (Audit) | **partial** · baked spring `linear(…, 330 stops)` @ 3300ms (per-line hero reveal, 100ms/line) + `linear` @ 57333ms marquees; only 2/14 scroll steps yielded new motion | Budgeting-app template, tenth Framer capture: first in the library where **one sans (General Sans, weights 400/500 only) carries the whole scale including the 48px hero**, breaking the "separate display face" pattern held 4/4 through fintechx; DM Mono reserved for an eyebrow/label accent only. Tracking is an exact 3-step em ladder (−0.03/−0.02/−0.01em by tier). `mediaConditions` carries integer *and* `.98` breakpoint edges simultaneously (not a same-day field-note's oversimplified `.98`-only read). `sampled.typeScale`'s dominant 1070-count tier is styled elements, not a copy census. Cross-check against `font-gate.json`'s canvas-proven render census. Hero paragraph reveal is bucketed `scrollTriggered` at 1312px but is almost certainly a load-time reveal caught late by the capture's first snapshot |
| **Sylva** | [mengto.github.io/sylva](sylva.md) | 2026-08-19 | capture only (Audit) | **spec** · named `--ease-out` `cubic-bezier(.16,1,.3,1)` @ 900–1450ms (17/28 firings) + `--ease` `cubic-bezier(.22,.61,.36,1)` (6/28); 0/28 scroll-triggered: single fixed-viewport hero, nothing below the fold | Hand-built (plain static HTML + hand-written vanilla JS + three.js r149, no framework fingerprint at all), by product designer Meng To. Confirmed single-screen at 3 independent viewports (`scrollHeight === innerHeight` exactly). One variable font (Lexend) carries the whole scale. **Zero saturated hue anywhere in the 16-swatch palette**: achromatic dark-moss + cream only, a harder version of polestar's no-accent finding. Whole layout runs on one fluid design-unit (`--u`), declared as 3 discrete per-tier `calc()` forms (fixed above 1900px, `÷1600` 900–1900, `÷760` below 900) rather than landonorris's single continuous root-font-size clamp: same idea, different mechanism. `--ease-out` is byte-identical to philllia's named `--ease-out-expo` and close kin to phenomenonstudio's 84-firing signature curve, despite three unrelated stacks (WordPress, Next.js/no-lib, hand-rolled vanilla). Both CTAs are sandboxed no-origin iframes with hover faked by geometric band-testing against the frame's own rect, since the parent receives no cross-frame pointer events at all |
| **Essentia** | [essentia.framer.media](essentia.framer.media.md) | 2026-08-20 | mirror (scripted), 13/13 pages | **spec** · `cubic-bezier(0.16, 1, 0.3, 1)` @ 600–1000ms + springs; 50ms stagger | Luxury single-product e-commerce template ("The Luxury of Less"). Two-column hero with sticky buy box, interactive subscription toggle, accordion FAQs, clean journal CMS. 99.86% visual fidelity, 100% offline navigable |
| **ThreeUI** | [threeui.com](threeui.md) | 2026-08-21 | source survey (not a Match/Adapt target) | **none** · a component donor catalog, not a measured site; read the specific component's own source instead of ordering motion from this entry | **Not a normal entry: a redistributable component source, not a study.** 220-component MIT-licensed (Community tier) React+Three.js+TypeScript catalog, `npm install @designcodeio/threeui`, built explicitly "for agents." Real buttons/backgrounds/data-fields/brand marks, not tokens to re-derive. Structural finds: a `window.__seek(v)` explicit-clock scrubbing hook (the same seek-safe discipline HyperFrames' `THREEJS-PATTERN.md` needed, confirmed independently in unrelated production code); iframe+`postMessage` isolation so a WebGL effect never touches the host page's own framework/bundle; a second confirmation of Sylva's `--u` fluid-reference-unit pattern (here `--h`/516). First place to check before hand-building a WebGL effect from scratch |

**Motion fidelity gates the named-reference path.** Only `spec` lets a build take
its motion from the entry; `partial` saves most of a capture but not the mapping;
`signature-only` and `none` mean the motion must be re-captured or the build
ships without it and says so. **Phenomenon** and **CreateStudio** are `spec` as of 2026-07-31,
and **Homy** joined them 2026-08-17: all three re-measured with
`scripts/motion-extract.js` through `cdp-run.py --pre`, so all three can be
ordered by name and will animate. The rest still need a motion-only
re-capture before their motion can be built from; it is one cheap pass each.

**A `spec` entry is not a promise that the reference is good.** Homy is the
first entry to carry both a complete motion spec and a failing house gate
(`design-gate.py --mode adapt`: NOT DONE, 7 checks). Fidelity answers "can I
rebuild this?"; it says nothing about "should I ship this as-is?" Read the
entry's own Adapt warning before treating a named reference as a target.

- **`scroll-behavior: smooth` silently defeats a programmatic scroll loop**, and
  the failure looks exactly like a broken reveal gate. A verification harness
  that walks the page with `scrollTo(0, y)` in a tight loop never catches up
  when the page has smooth scrolling on, so the lower half of the document is
  never scrolled into view, never revealed, and screenshots back as blank
  sections with their height reserved. Measured on the systo-plumbing build:
  6 of 13 reveal gates fired, the rest reported `opacity: 0`, and the site was
  correct the whole time. Always pass `behavior: "instant"` in a harness, and
  read a page of blank-but-spaced sections as a scrolling problem before
  touching the gate.
- **A nav that measures as two rows may not be wrapping at all.** Row counting
  buckets item `top` values, so a pill whose brand, links, phone number and
  button each centre at a different height reports two rows while rendering
  perfectly on one. Same trap one level down: a control given an explicit
  `height` without a matching `line-height` measures as a wrapped label,
  because rendered lines are computed as `contentHeight / lineHeight`. Give
  every item in a nav one shared row height, and give any height-forced button
  a `line-height` equal to that height.
- **Automotive OEM homepages are motion-light in CSS; the budget goes to video.**
  Measured on two unrelated manufacturers in one pass: polestar.com fired **8**
  animations page-wide with **1** scroll-triggered over 5,832px, and rivian.com
  fired **13** with **0** scroll-triggered over 16,443px; and on both, most of
  what fired was skeleton loaders and a cookie banner. Against phenomenonstudio's
  626 and createstudio's 1427 that is a different discipline, not a quieter
  version of the same one. Consequence for any build in this genre: **the
  category gives you the visual language and cannot give you the motion system.**
  Take motion from a `spec`-grade entry and say so, rather than assuming a car
  brand's own site will supply it. Do not read a near-empty motion capture of an
  OEM page as a failed capture.
- **The premium-automotive curve is `cubic-bezier(0.65, ~0, 0, 1)`**: hard out,
  very long settle. Two independent confirmations: polestar.com ships
  `cubic-bezier(0.65,0,0,1)` on its opacity transition (52 uses) and
  landonorris.com ships `cubic-bezier(0.65,0.05,0,1)` as `--cubic-default` at
  750ms (7 of 12 live animations). Different agencies, different stacks, the same
  curve to two decimal places. Treat it as the genre's signature the way
  `(.22,1,.36,1)` is phenomenon's.
- **Refusing pure black is a genre marker, not a one-off.** phenomenonstudio ink
  is `rgb(8,13,16)`, polestar's is `rgb(16,24,32)`: both near-black with a blue
  cast, both paired with a warm off-white rather than `#fff` (`rgb(236,236,231)`
  on polestar). Three sites in the library now avoid a true neutral anywhere in
  the ramp (landonorris green-shifts every grey). Starting a premium build from
  `#000`/`#fff` is the cheapest possible tell.
- **A design system can ship two palettes at once.** philllia.com carries a warm
  editorial set (`--background`/`--primary`/`--accent`) *and* a separate cooler
  `--sig-*` set with its own display scale, both live in one stylesheet. Tally
  token prefixes before assuming one system, or you will average two languages
  into a muddle that matches neither.
- **Name curves by job, not by signature.** The richest motion token set measured
  so far uses four curves for four purposes (reveal, soft settle, hover, swap)
  plus a stagger ladder (40/80/140ms) and a travel ladder (12/24/48px), so
  "reveal this grid looser" is a token swap rather than a hand-tuned delay. This
  is the architecture to copy; values are cheap to re-derive. Seen on philllia.
- **A serif display face earns its keep only at display size.** Two independent
  confirmations: osa (Instrument Serif at 46–54px only) and philllia (Fraunces
  at 20–48px, weight 400 only), each with a geometric sans carrying the entire
  interface. If a rebuild's serif is showing up at 15px body copy, it has drifted.
- **An IntersectionObserver only reports transitions it witnesses**, so any
  reveal gate needs a self-healing sweep on load/scroll/resize that reveals
  anything already at or above the trigger line. Without it, landing on an
  anchor, restoring a scroll position, or jumping to the page bottom strands
  every skipped section at `opacity: 0` permanently. Measured on a fresh build:
  a bottom jump revealed 1 of 11 sections and left 30 items invisible. The guard
  must test `rect.top < line` **only**; adding `rect.bottom > 0` re-breaks the
  jump case by excluding anything already scrolled past. Same guard belongs on
  count-ups and any progress element, and under reduced motion they must resolve
  to their final value up front rather than waiting for a view that never comes.
- **`.parent > .child` is the wrong combinator for a reveal gate.** Items are
  routinely nested a level deeper than the gate element (inside a `.prose` or
  `.section-head` wrapper), so a direct-child selector silently skips them;
  they get neither the hidden state nor the transition and just render static,
  which looks like "the animation didn't run" rather than a selector bug.
- **The in-app browser pane does not run `requestAnimationFrame`, so NO
  JS-driven animation can be observed there, and every reading taken while
  that is true is wrong, not merely incomplete.** Measured directly: an rAF
  sampling loop produced exactly **1 sample in 3.5 seconds**, and
  `el.getAnimations()` was empty on an element with a live framer-motion tween.
  Because GSAP, framer-motion, Motion and Lenis are all rAF-driven, a captured
  page sits frozen at whatever its pre-animation state is. This is what makes
  the failure so expensive: a fanned deck read back with **all seven cards at
  an identical rect and an identical transform**, which looks exactly like "the
  component is a static stack" rather than "the animation never ticked", and
  that misreading went into a library entry as fact. The tell is that
  `computer{action:"screenshot"}` on the same tab errors with *"the Browser
  pane is not displayed, so the page is not compositing frames"*. Treat that
  error as invalidating every JS-layout and motion reading from that tab, not
  just the screenshot. Verify motion through CDP or Playwright instead; a
  headless run of the identical page produced a clean per-frame trace.
- **The in-app browser pane's IntersectionObserver does not fire.** A fresh
  observer at threshold 0.05, on an element demonstrably on screen, with working
  scroll, never fired, while the identical page in headless CDP revealed 11/11
  sections. Combined with the pane rendering a working page fully black on an
  earlier capture: use the pane for interaction only, and verify all
  scroll-driven behaviour through CDP.
- **The same "pane not compositing" failure breaks JS-computed carousel/fan
  transforms, not just IntersectionObserver.** Re-querying landonorris.com's
  "What's up on socials" deck through a non-displayed pane returned all 7
  cards at the identical rect and identical `matrix(1,0,0,1,0,118.519)`;
  z-index varied (1/2/3/10/3/2/1, correctly showing which slide is meant to be
  "front") but the per-card rotate/scale/tx spread never got computed, because
  whatever layout pass assigns it never ran without real paint. `computer
  {action:"screenshot"}` on the same tab errored "the Browser pane is not
  displayed, so the page is not compositing frames": that error is the
  tell, and it means ANY reading taken while it's true (not just visual ones)
  is suspect for JS-driven layout. The original capture of this exact
  component (the measured FAN_CURVE in landonorris.com.md) returned real
  differentiated values, so it was not taken under this condition. Trust a
  capture that shows per-item variation over a re-check that returns uniform
  values, and re-verify only once `computer{screenshot}` succeeds.

- **Removing a component from the static mirror, not just editing its text, can crash the page outright rather than merely reverting on hydration.** Homy established that Framer's hydration reverts edited *text nodes*. Fluence sharpened it: a component that mounts via its own separate `ReactDOM.createRoot()` call (a "badge"/widget pattern, not part of the main hydration tree) throws synchronously the instant `getElementById` returns null for its expected container; `createRoot(null)` is a hard crash, not a soft revert. Never delete a node a *separate* root might target; hide it with `display:none` live instead, after mount. A component that *is* part of the main tree (e.g. a promo card) just reverts like text does: same fix (a live corrector), different failure mode if you get the removal-timing wrong.
- **A Windows server process is not gone just because your start command succeeded and a later one bound the same port.** `SO_REUSEADDR` on Windows allows two processes to bind one address:port simultaneously with no error, and request routing between them is unpredictable, silently serving stale bytes from the old process while every symptom points at "my fix didn't work." Verify the actual owner with `Get-NetTCPConnection -LocalPort N -State Listen` (or equivalent), not by whether your launch command exited 0. Seen twice in one session on Fluence.
- **The in-app browser pane can report `window.innerWidth === 0`, making every `min-width` media query behave unpredictably and `getComputedStyle().display` on an element read as its own declared value regardless of whether a `display:none` ancestor is actually hiding it.** Both read as real layout bugs until checked with `offsetParent === null` or a real bounding rect. Extends this library's standing "pane is not a measurement instrument" caution from IntersectionObserver/screenshot failures to viewport dimensions themselves. Seen on Fluence.

- **A component built to be embeddable/scrubbable avoids a free-running
  `requestAnimationFrame` loop in favour of an explicit, externally-settable
  clock.** ThreeUI's shader components expose `window.__seek(v)` and render
  exactly the requested frame rather than ticking their own internal timer,
  the same reasoning this project's own HyperFrames video work landed on
  independently (a paused timeline seeking to an arbitrary timestamp needs the
  WebGL layer keyed off that same seek, or an exported frame shows the wrong
  state). Worth checking for on any future "premium interactive 3D component"
  donor: if it only animates via its own rAF tick with no way to set the clock
  externally, it cannot be dropped into a scrubbed/exported timeline without
  modification. Ask before assuming a found component is drop-in reusable
  there.

## Cross-site patterns observed

Accumulating notes: the point of keeping the library. Update as N grows.

- **Never write "no animation / no hover state" into an entry from geometry
  alone.** A settled end-state and a genuinely static layout are pixel-identical
  and rect-identical; nothing in a DOM measurement distinguishes them. The
  landonorris socials deck was recorded as "a static fan, no transition, no
  animation, no hover state" and is in fact one of the most motion-rich
  components in the library (scroll entrance + a per-card hover that redistributes
  the whole fan). That wrong line then propagated into a real build and had to be
  undone twice. An absence-of-motion claim needs *positive* evidence: a tween
  list from the runtime, or the component's own source out of the bundle. If you
  have neither, the honest fidelity is `none` ("not swept"), never a claim that
  there is nothing there. Same asymmetry as "a clean network log does not mean
  the right assets loaded": absence of observation is not observation of absence.
- **Hover on an overlapping deck is a *distribution*, not a selection.** Both
  instincts a rebuild reaches for (snap the hovered card to centre, or
  hit-test the nearest card centre) are wrong and both flicker. What the
  reference actually does is keep every card's own position and angle, lift the
  hovered one in place, and push its neighbours outward by an amount that decays
  with distance, using plain per-card `mouseenter`/`mouseleave` with an
  `overwrite:"auto"` tween and a ~50ms leave debounce. Overlapping hit regions
  stop mattering because the *response is continuous in distance*: whichever
  card wins the hit-test, the resulting arrangement is nearly the same, so a
  mis-hit is invisible rather than a jump. Reach for this before building any
  hysteresis/settle-time machinery to stabilise a fan hover.

- **Resizing the viewport to the document height, the standard full-page
  screenshot trick, re-lays-out every `100vh` / `min-height:100dvh` section, so
  each one becomes a full *page* tall and the shot explodes.** Measured twice in
  one session: a Framer template went 16,740px -> 111,780px, and a Divi page
  7,907px -> 12,943px. Nothing errors; you just get a hugely tall image whose
  proportions no longer match what a visitor sees, and any geometry read off it
  is wrong. Capture **viewport-sized tiles at fixed scroll positions** instead
  (scroll once to prime lazy content and fire reveals, return to top, then shoot
  at y = 0, h, 2h…). Keep the full-height trick only for pages with no viewport
  units in their section heights, and check before assuming that.

- **Move the mouse before calling anything static.** Three independent probes
  on onefin's About tiles (a 19-point scroll sweep, an entry-opacity trace and
  a pre-load WAAPI capture) all reported "no motion", and all three were wrong:
  the tiles carry Framer's `data-parallaxfloating` and track the POINTER
  (≈ −0.035×dx, −0.055×dy from viewport centre, ±22/±19px, ~600ms settle).
  Scroll, entry and WAAPI instrumentation share a blind spot, and it covers the
  most visible motion on that section. Grep for `data-parallaxfloating` and run
  a pointer pass as part of Step 1's interaction states, not as an afterthought.

- **Scroll-reveal is almost always a two-class gate**: a base class sets
  `opacity:0`, JS adds a second class for the end state. Find both class names and
  you can render the end state statically without running their JS. Seen on
  phenomenonstudio (`.isview` → `.visible`).
- **Column counts are increasingly JS-computed, not media queries.** Grep the CSS
  for the variable before assuming a breakpoint ladder exists. Seen on youtube.
- **A site's "signature" easing is the one with the highest use count**, and it is
  usually custom, not a Material/standard curve. Tally `cubic-bezier(...)` by
  frequency across the whole stylesheet rather than reading one component.
- **An `{≈.16-.22, ~1, ≈.3-.36, 1}` ease-out family recurs across three
  completely unrelated stacks, and it is NOT explained by shared tooling.**
  Unlike the Framer/Motion default below (a library default, expected to
  repeat on every site built with that library), this curve shape shows up on
  a WordPress theme, a Next.js site with no JS animation library at all, and
  a hand-written vanilla-JS/three.js site with no framework whatsoever:
  phenomenonstudio's 84-firing signature `cubic-bezier(.22,1,.36,1)`;
  philllia's two top-ranked stylesheet curves, both named tokens,
  `--ease-out-expo: cubic-bezier(.16,1,.3,1)` and
  `--ease-out-soft: cubic-bezier(.22,1,.36,1)` (four uses each); and sylva's
  two named tokens, `--ease-out: cubic-bezier(.16,1,.3,1)` (17 of 28
  animation firings, the page's signature) and `--ease: cubic-bezier(.22,.61,
  .36,1)` (6 of 28; same x-anchors as the others, a softer y1). sylva's
  `--ease-out` is byte-identical to philllia's `--ease-out-expo`. Both
  `.16,1,.3,1` and `.22,1,.36,1` are the named "easeOutExpo"/"easeOutQuint"
  entries on easings.net; read as three independent designers/toolchains
  drawing from the same public easing-curve vocabulary, not as one library's
  default leaking across sites (contrast with the Framer note below, where
  the shared curve genuinely is a library default).
- **Some sites ship literally zero saturated accent colour anywhere in the
  UI**, and put all colour into imagery/context instead. Two confirmations:
  polestar (product photography carries all the colour; two saturated hues
  that do exist are status-only, buried in a bundled chat widget, not design)
  and sylva (all 16 distinct measured swatches are near-black moss-green,
  cream, or a pure black/white endpoint; no exceptions at all, colour comes
  entirely from the WebGL scene and two photographic card thumbnails). Before
  assuming a build needs a brand hue in its UI chrome, check whether the
  imagery is doing that job instead.
- **Dark UIs increasingly layer white at low alpha** rather than using opaque
  greys, so interactive surfaces composite over any background. Seen on youtube
  (8/10/20% white), onefin and osa (a 5-step 5/20/40/60/80% ramp), and sylva
  (an 8-step ramp: .04/.055/.075/.18/.34/.44/.5/.62, the finest-grained
  confirmation yet, and the first where the "dark" surface is a WebGL canvas
  render rather than a DOM `background-color`, so the ramp only shows up by
  reading the page's `--ink*` custom properties, not by sampling `background`
  on real elements).
- **`@font-face` frequently lives in an inline `<style>` block**, not the linked
  stylesheets: attribute-level URL rewriting misses it, cross-origin fonts are
  CORS-blocked, and the fallback is silent. Computed `fontFamily` echoes the
  request, so it cannot detect this; only `document.fonts.check()` + a canvas
  width A/B can. Seen on phenomenonstudio.
- **WordPress sitemaps overstate the site ~7×.** 585 URLs → 368 blog machinery
  (articles/FAQ/tags), 114 portfolio, ~40 actual nav surface. Histogram by first
  path segment before crawling; the design surface is the small slice.
- **Subresource Integrity silently voids a mirror.** A linked stylesheet carrying
  `integrity="sha384-…"` stops loading the instant you rewrite its `url()`s,
  because the bytes no longer hash to the recorded value, and the browser drops
  the *entire* sheet with no console error. Symptom is a page rendering in Times
  with `document.fonts.size === 0`. Strip `integrity` and `crossorigin` from every
  `<link>`/`<script>` in any mirror. Seen on landonorris (Webflow); assume every
  Webflow and every CDN-hosted stylesheet ships it. This also sharpens the
  font-face pattern below: `document.fonts.check()` returned **true** throughout,
  so only the canvas width A/B detected it.
- **A fluid design-unit beats a breakpoint ladder, and the mechanism has now
  been seen two ways.** landonorris drives its whole scale from one
  `calc(clamp(min,100vw,max) / <design-width> * 16)` root-font-size formula,
  making `rem` the vehicle and the curve continuous across its whole clamped
  range (verified: 11.8519px at 1280 = 1280/1728×16). sylva reaches the same
  goal (one design-width-pinned constant driving every measurement, no
  breakpoint-by-breakpoint hand-tuned pixels) with a *different* vehicle: a
  plain custom property (`--u: calc(100vw / 1600)`) multiplied directly into
  `calc()` expressions with no `rem`/root-font-size involved at all, declared
  as **three discrete per-tier forms** (a fixed value above 1900px, one
  formula 900–1900px, a different reference-width formula below 900px) rather
  than landonorris's single continuous clamp. Second confirmation generalises
  the pattern from "a rem driver" to "a single fluid constant, continuous or
  discretely tiered, always pinned to an explicit design width." Grep for
  `--design-width`/`--fluid-font` (rem form) or a repeated custom-property
  name declared under multiple `@media` blocks (discrete form) before
  assuming breakpoints drive the scale by hand.
- **Runtime-built asset paths are invisible to static analysis.** Bundles
  increasingly construct texture/model URLs from a descriptor at load time, so no
  literal string exists to grep. Build the mirror, load it in a real browser, and
  read the network log for 404s; that pass found 13 assets the source scan
  missed on landonorris. Do this before concluding a region "failed to mirror".
- **Sites randomise a visual variant per page load**, which caps the achievable
  diff and is not a defect in your build. Detect it by loading the reference N
  times and reading the relevant runtime state, not by staring at screenshots.
  Where the runtime exposes a writable params object, pin it identically on both
  sides before capturing. Seen on landonorris (helmet livery, 5 variants).
- **Interrogate the runtime before grepping the bundle.** A globals-exposed
  control object (`window.landoGL`) answered asset paths, scene parameters and
  colour values in one `evaluate` call that minified-source grep could not.
  Check `Object.keys(window)` for a project-named global first.
- **A CDN that answers `vary: Accept` hands your mirror different bytes than it
  hands the browser.** framerusercontent.com serves **AVIF** to Chrome's
  `image/avif,image/webp,…` and **PNG** to `Accept: */*`, which is what every
  mirroring fetch sends by default. The mirror then renders lossless PNG where
  the reference renders lossy AVIF. This is invisible to every structural check:
  geometry, text, fonts, decode sizes and node counts all verify perfectly. Its
  only signature is a pixel diff showing a uniform 1–2 level delta across ~90%
  of *background* pixels with **text untouched**; nothing is misplaced, so
  there is nothing to inspect. Send the browser's Accept header, keep the
  original filenames so references stay valid, and set `Content-Type` from magic
  bytes in the server. Seen on onefin (128 of 160 rasters were actually AVIF).
- **Never drop the query string from a CDN asset URL until you know what it
  does.** The recipe's "strip `?v=` cache-busters" is right for cache-busters and
  catastrophic for a CDN that *resizes from the query*: srcset candidates like
  `?scale-down-to=512&width=1024` and `?width=1024` are different images sharing
  one path, so stripping collapses every candidate onto the full-size original
  and the browser downscales a far larger source. Fetch each distinct
  `(path, query)` as its own file. Detect it in one cheap pass: compare
  `naturalWidth`/`naturalHeight` for every image across both sides; no pixel
  diff needed. Seen on onefin (186 variants in markup, 157 more in modules).
- **A clean network log does not mean the right assets loaded.** The two traps
  above both fail *silently with HTTP 200*: wrong format, wrong resolution,
  nothing to 404 on. Asset verification therefore needs a positive check
  (decode sizes match, content-type matches) rather than an absence of errors.
- **`grep -r` does not follow symlinks, so the origin sweep can lie.** build.py
  symlinks `cdn/` into each variant directory, so a recursive grep over the page
  dirs covers markup only and reports a clean 0 while mirrored bundles still
  reference, or assemble, live URLs. Sweep the asset directory explicitly, and
  treat `performance.getEntriesByType('resource')` filtered to non-origin
  entries as the authority: a grep cannot find a URL a bundle builds at runtime.
  Seen on onefin, where a mirror reporting "0 origin refs" was loading an iframe
  from framer.com on every page.
- **Strip a framework's editor/analytics bootstrap at the module level, not just
  the tag level.** Removing `<script src="…/edit/init.mjs">` does nothing when a
  bundle contains `await import('https://framer.com/edit/init.mjs')`. Because it
  is awaited at module top level and its result is consumed
  (`{default: createEditorBar()}`), deleting the import rejects the module and
  takes the surrounding lazy factory with it. Point it at a local stub whose
  export returns a component rendering `null`. Seen on onefin.
- **When an animated region caps a diff, measure one side against itself at two
  different waits.** Capturing the mirror at 12s vs 13s reproduced the exact
  reference-vs-mirror score on a scrolling marquee band (98.07% vs 98.02%),
  while two mirror captures at the same wait scored 99.84% against the
  reference's own 99.79% ceiling. Two screenshots separate animation phase from
  replication error, and turn "probably just the animation" into a measurement.
  Seen on onefin; supersedes eyeballing a diff map for motion residuals.
- **Framer is now characterised, but two of the "constants" were only priors.**
  Across three captures, these hold: breakpoints are always
  `0–809 / 810–1199 / 1200+`; root font-size is a flat 16px with no fluid driver;
  colour tokens are UUID-named so the values are the system and the names carry
  nothing; `@font-face` is in inline `<style>`; and the *bulk* of motion runs
  through the bundled Motion library as `type="framer/appear"` payloads.
  **Two claims made from the first two captures did not survive the third**
  (onefin), and both were generalisations from N=2:
  *"zero CSS easing"*: onefin ships `cubic-bezier(.44,0,.56,1)` 45 times, and it
  is the same curve as its one appear-tween's ease, so a Framer site can have a
  real CSS motion signature. Always tally rather than assume.
  *"`.98` fractional edges"*: onefin emits integer edges (`max-width:809px`,
  `max-width:1199px`) 145 times each *alongside* the `.98` forms (50). A missing
  `.98` is not evidence a site is not Framer.
  Read this as the standing caution: a two-site pattern is a hypothesis, and the
  entry that breaks it is worth more than the two that built it. Framer also
  registers metric-compatible "… Placeholder" faces, which are not a mirroring
  artifact but *will* make a naive font A/B report `differs: false` for a family
  that is genuinely loaded. Probe the display face, where the gap is obvious.
  Reusing the hardened Framer build on a second site scored 99.37% against a
  99.46% ceiling on the first attempt, versus a multi-round debug on the first.
- **Serve mirrors with a server that honours `?range=a-b` AND `?range=a-b,c-d`.**
  Framer's CMS loader slices data chunks with a *query parameter*, not the HTTP
  `Range` header, and validates the response length. Python's `http.server`
  ignores it and returns the whole file, so the loader throws `Unexpected
  response length`, which Framer treats as fatal and tears the rendered tree down
  to an empty shell. It races the rest of the render, so it looks intermittent:
  headless captures can pass while the interactive page collapses. Critically the
  loader also issues **multi-range** requests (`?range=12650-18880,25241-31599`,
  comma encoded as `%2C`) and expects the concatenation of every slice; a handler
  that honours only the first pair fails exactly the same way, and only on the
  pages whose collections are big enough to be split. One page measured **9.76%**
  against a 99.93% ceiling from this alone while its 20 siblings sat at 99.7%+.
  Ship a `serve.py` that handles both forms with any Framer mirror.
- **Never neutralise links to `href="#"` on a Framer site; use `#inert`.**
  Framer's anchor component calls `document.querySelector(href)`, and
  `querySelector('#')` raises `SyntaxError: '#' is not a valid selector`. On at
  least one page that throw stopped the component tree rendering entirely. Any
  valid-but-unmatched selector works and is equally dead as a link target. This
  is a self-inflicted wound from the standard mirroring recipe, so it is worth
  checking on every framework that treats `href` as a selector.
- **One bad page hides behind a good mean.** A 21-page run averaged well while a
  single page sat at 9.76%. Always print the per-page table and flag outliers
  against each page's own ceiling; never report only an aggregate.
- **CMS collections come in `-chunk-`/`-indexes-` pairs and only one name is a
  literal.** The sibling is built by runtime substitution, so a scan finds one and
  the loader 404s on the other, rendering the collection empty with no error.
  Derive the sibling from every chunk found; a derived name that 404s upstream is
  expected and harmless.
- **A sitemap can list pages no crawl reaches, and a crawler can silently drop
  real ones.** Paginated indexes hide entries from link-following, and the
  bundled `AUTH_PAT` treats `/projects/` as an account area: correct for app
  dashboards, wrong for a portfolio, and it dropped 5 case studies as
  "auth-gated". Always set-difference the crawl against `/sitemap.xml` and read
  the skip reasons before trusting a page count.
- **Server-rendered does NOT mean script-independent.** The `curl`-and-grep test
  in mirror.md tells you the *markup* is there; it cannot tell you the markup is
  *visible*. Framer server-renders everything and then hides most of it, revealing
  it from its own runtime; scripts stripped measured 73.4% against 98.5% scripted
  on the same page. Always shoot the static variant once before assuming it is the
  safe default; the gap, not the stack, decides.
- **Never rewrite a URL that is used as a `new URL(rel, base)` base.** A base must
  be absolute, so relativising it throws `TypeError: Failed to construct 'URL'`,
  and one uncaught error in a framework bundle takes down the whole render. The
  failure mode is badly misleading: images and layout boxes paint normally while
  **all text disappears** and every counter/clock freezes at its initial value;
  it reads like a font or CSS fault and is neither. When the base sits in a
  template literal, inject `${location.origin}` to keep it absolute with no
  hardcoded port. Seen on createstudio (Framer CMS chunks).
- **Inside module bodies, rewrite to root-absolute (`/cdn/x`), never `./x`.** The
  same URL string is resolved against the *module* when it is an import specifier
  and against the *document* when it becomes a DOM `src` at runtime. `./` is
  correct for one and 404s at the site root for the other; `/cdn/` is correct for
  both.
- **Follow relative dynamic imports, not just absolute CDN urls.** Bundler chunks
  reference each other as `import('./X.mjs')`, which a host-based scan cannot see.
  Resolve relative specifiers against each module's own origin URL and iterate to
  a fixed point.
- **Truncate a captured URL at its first valid extension**, rather than stripping
  trailing punctuation. The stop-character rule in crawl.md is necessary but not
  sufficient: asset urls inside CSS custom properties in inline `<style>` blocks
  are followed by `);--next-prop:…`, and `;`/`:`/`-` are not stop characters, so
  the match runs into the next declaration and no amount of trailing-strip
  recovers it. Seen on createstudio.
- **A doubled DOM node count means hydration did not complete**, not that the
  mirror is broken. Framer emits every breakpoint variant server-side and switches
  them with `display:contents`/`none`, so the un-hydrated tree is ~2× the hydrated
  one (13,228 vs 7,042). Compare node counts across reference and mirror early;
  it is a fast, cheap hydration check.
- **Framework globals often come from the analytics script you correctly removed.**
  `__framer_events` and friends are set by `events.framer.com`, not by the app
  bundle, so their absence on a mirror proves nothing about whether the runtime
  booted. Check for loaded module count or rendered output instead. Corollary:
  neutralise tracker scripts by deleting the tag, not by pointing `src` at
  `about:blank`; that raises `ERR_UNKNOWN_URL_SCHEME` and pollutes the console
  you are trying to read.
- **The in-app browser pane is not a measurement instrument.** It rendered a fully
  black frame for a page that headless CDP captured correctly at 64% non-black
  pixels. Screenshot through CDP for anything you intend to reason about; use the
  pane only for interaction.
- **A production bundle's licence comments lie about its stack.** landonorris's
  bundle name-drops gsap.com and rive.app, but `window.gsap` and
  `window.ScrollTrigger` are undefined; the motion is CSS transitions plus a
  hand-rolled renderer. Confirm libraries by probing globals, not by grepping
  strings. Related: dat.GUI shipped hidden in production and inflated the
  hover-rule tally 3×; filter debug-tool selectors out of any state census.
- **"Runtime-built asset paths are invisible to static analysis" extends to CDN
  *host* paths, not just relative import specifiers.** salix's crawler found two
  plausible-looking `.framercms` URL prefixes in the bundle (`/modules/…`,
  `/sites/<siteId>/…`) and both 403'd; the live runtime actually requests a
  third, `/cms/<hash1>/<hash2>/…`, assembled from data with no literal joinable
  string anywhere in the bundle. Only a live network-log read (a few real pages,
  one per CMS collection) finds it. Re-fetch the complete, unranged file under
  the correct **bare** local filename the rewritten markup/JS reference; the
  hash-suffixed name build.py assigns from a wrong-prefix fetch can succeed
  (200 OK) while silently holding different/incomplete data.
- **A breakpoint "constant" is per-template, not a platform constant; it can
  flip entirely.** Six Framer captures running back to 2026-07-30 all shared
  809.98/810 as the low breakpoint; salix (the seventh) uses 767.98/768
  instead. Tally the actual `@media` values on every new capture; never assume
  the low edge without checking, the same standing caution as the onefin
  `.98`-vs-integer break.
- **A verified-self-consistent offset/length table is not proof a binary CMS
  edit is safe.** salix fully reverse-engineered `.framercms`'s string
  (tag+4-byte-BE-length+content) and indexes (contiguous per-item
  offset+length) framing well enough to patch a length-changing text edit and
  confirm the recomputed offset chain was perfectly contiguous end-to-end, and
  it still silently truncated 2 of 8 CMS items to a quarter of their real
  content, with zero console error, discovered only by comparing rendered
  character counts against the live reference. There is at least one more
  structural piece this model doesn't capture. Same-length substitutions
  remain safe (confirmed on agentwise); treat any length-changing edit to this
  format as unverified until proven against live rendered content, not just a
  self-consistent offset table, and prefer fixing the *rendered* text at the
  DOM layer over a binary patch when the edit changes length.
- **A per-character kinetic-reveal heading can make `body.innerText` contain a
  word that literally no text node does**, defeating the text-node-level
  MutationObserver guard that has worked on every other Framer rebrand in this
  library (homy, agentwise, fusionai). Each letter lives in its own
  `<span>` with no per-character stagger data in the DOM (the reveal is
  driven by JS/DOM order, not inline style), so a substring check against any
  individual `node.nodeValue` never matches even though the browser's own
  `innerText` computation concatenates the adjacent single-letter nodes and
  does contain the word. Fix at the *element* level instead: walk up to the
  smallest container whose own `innerText` contains the needle (confirming no
  child independently satisfies it first), then collapse that container's
  `textContent` once the reveal has settled. Seen on salix's case-study
  headings.
- **Enumerate every responsive srcset sibling of a "hero screenshot" image, not
  just the one your test viewport loads.** Framer serves up to 5 independently
  hashed size variants per logical image (`<id>__<hash8>.png`, ~512px up to
  native), and each is a separate file on disk needing its own fix: patching
  only the variant `document.elementFromPoint(...).src` resolves to at your
  current viewport leaves every other breakpoint's variant showing the old
  content. A straight proportional scale (crop box × replacement size ×
  `variant_width / reference_width`) against one manually calibrated reference
  variant carries cleanly to the rest. Seen on salix: 5 distinct base images,
  21 files once every variant was counted, only 1 of the 5 visible on the
  first screenshot taken.
