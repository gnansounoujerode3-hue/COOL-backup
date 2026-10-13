# hanzo.framer.website

**Callable as: Hanzo** (aliases: hanzo.framer.website, the "Design Craftsman" Framer portfolio template)

Free single-designer portfolio template (Framer), published by stfn.co (Nick
Step): hero, featured-work grid, testimonial, experience list, contact, plus a
CMS-backed case-study collection (6 work items). Captured 2026-08-10 @
1440x900 (default `crawl.py`/`build.py` viewport). Stack: Framer (React + the
bundled Motion library), CMS Collection for the work items, Lenis smooth
scroll. **Mirror path** (full scripted mirror + full sitewide rebrand to
"Syszo"), plus one hand-built Three.js hero decoration.

## Type: flat Inter system with a display-only serif accent

No fluid rem driver, same as every prior Framer capture in this library.
Two-family system carries the whole UI: **Inter** (132 declarations, body/UI)
and **Inter Display** (136 declarations, headings), both self-hosted with
Framer's metric-compatible `"X Placeholder"` fallback pair. Two accent faces
at low use count: **Instrument Serif** (4 uses; matches this library's
"serif earns its keep only at display size" pattern, seen previously on osa
and philllia) and **Fragment Mono** (3 uses, a monospace accent for small
tag/label text; new to this library, not seen on the six prior Framer
captures).

## Layout

Breakpoint edges: `809px`/`809.98px` (19+2), `810px` paired with `1023px`,
`1199px`, `1439px`/`1439.98px`, and `1440px`/`1440px+`. This is the
**fourth-plus** confirmation in this library of the `0–809.98 / 810–1199.98 /
1200+` triad as a Framer-wide constant, with this template's own extra
810/1023 and 810/1439 steps layered on top for wide-desktop tuning: matches
the pattern already noted on agentwise (own extra steps on top of a fixed
low pair).

## Colour

Colour custom properties are UUID-named (`--token-<uuid>`), values are the
system, consistent with every prior Framer capture. Palette is a plain
white/near-white ground with pure black (`rgb(0,0,0)`) text and UI, no accent
colour at all beyond the token-driven light/dark toggle on components (badge
pills, cards). Leans on client-logo and case-study imagery rather than a
brand-colour system, similar to agentwise.

## Motion

**Motion fidelity: none**. Not captured this pass (scope was Match + full-
site rebrand, not a dedicated `motion-extract.js` pass). Visually: a
per-character blur/translateY entrance reveal on hero and section headings
(`opacity:0.001; filter:blur(4px); transform:translateY(10px)` per `<span>`
character, settling on load/scroll), Lenis-driven smooth scroll, and simple
opacity/translate card reveals on the featured-work grid.

## Template taxonomy (multi-page crawl)

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Home | 1 | hero, featured-work grid, testimonial, experience list, contact | - |
| Work / case study (CMS collection) | 6 (Strida, Bravo, Nitro, Fargo, Taro, Haze) | title, intro paragraph, CTA row, device-mockup gallery | project name, copy, mockup imagery |

7/7 sitemap pages mirrored (home + 6 CMS work items; the site's own `/404`
correctly excluded: 404s on the live reference too, matching this library's
standing convention).

## Gotchas hit while rebuilding

1. **A live hydration guard that hides Framer's own chrome (badge/CTA) and
   corrects title/meta from inside a subtree-wide `MutationObserver` can hang
   real headless Chrome outright on a page with dense per-character
   kinetic-reveal text**: reproduced deterministically via a 4-way bisect
   (pristine mirror loads fine; a `rebrand.py`-only build loads fine and
   already carries a correctly-rebranded `document.title`, confirming the
   bundle-level text fix alone is sufficient here; adding a Homy-style
   observer-based guard hangs `Runtime.evaluate` past 120s on every attempt,
   even for a script as trivial as `document.title`). Root cause: this
   template's hero/testimonials wrap **every character** of several headings
   in its own `<span>` for a blur/translate reveal, so a single hydration
   pass fires a very large number of `childList` mutations; running
   `document.querySelectorAll()` plus a fresh `TreeWalker` from inside the
   observer callback for *each* of those mutations compounds into a
   main-thread stall the headless renderer never recovers from. Homy's page
   (where this observer pattern originated) didn't hit this because it
   lacked that reveal density and its guard never queried the DOM from the
   callback. **Fix:** don't use a `MutationObserver` for this at all. Hide
   Framer's badge/CTA with a plain CSS `!important` rule (a stylesheet rule
   beats an element's inline style with zero runtime cost and nothing for
   hydration to "revert," since the DOM tree itself is never touched);
   correct `document.title`/`meta[content]` with a one-shot check on
   `load`/`DOMContentLoaded`/a short `setTimeout`, not a standing observer.
   `rebrand.py` already rewrites the same strings inside the JS bundle
   (`cdn/*.mjs`), so the one-shot check is a safety net for a hydration race,
   not the primary fix. **Detect this class of bug fast:** bisect with the
   simplest possible probe script (`document.title`, no `--pre`) against
   (a) the live reference, (b) the pristine unmodified mirror, (c) each
   patch applied independently. The live reference and pristine mirror both
   returning instantly is what proves the hang is build-specific, not
   template-inherent.
2. **The "Made in Framer" badge confirmed, directly in this build's own
   `script_main.*.mjs`, to mount via a separate React root**:
   `E(document.getElementById('__framer-badge-container'), h(_, {}, ...))`
   called after the main hydration pass. Generalises the fusionai/agentwise
   finding with a direct source read rather than inference. If the
   container element is missing, `getElementById` returns `null` and the
   render call throws. Never remove the node; hide only.
3. **`build.py`'s off-origin neutralisation already does most of the
   "repoint transactional endpoints" work for you.** This template embeds
   the real designer's own promotional links (a Lemon Squeezy "buy the pro
   template" link, Instagram/X profile links, a second `hello@stfn.co`
   contact) alongside the portfolio's own fictional contact
   (`joris@hanzo.com`). All off-origin/non-`http(s)` hrefs were already
   rewritten to `href="#inert"` by the standard build pass before any
   rebrand script ran; only the *portfolio's own* visible email text needed
   a rebrand-pass substitution. Check what `build.py` already neutralised
   (`grep -c '#inert' site/*.html`) before writing bespoke link-repointing
   logic.
4. **A visible "+N" style count badge next to an avatar-stack ("Trusted by
   Leaders") is easy to mistake for a leftover chat-widget or notification
   overlay in a screenshot**: worth a two-second DOM check
   (`document.elementFromPoint` or a text-content search) before treating an
   unexplained small numeric badge as a bug; this one was real, intentional
   template content.
5. Two asset 404s are expected and harmless, confirmed by 0 console errors
   across all 7 pages post-rebuild: the bare, hash-less CMS
   `<id>-chunk-default-0.framercms`/`<id>-indexes-default-0.framercms` pair
   (same already-documented pattern from agentwise/onefin/createstudio; the
   runtime also requests a *hashed* form that mirrors correctly and a
   compiled fallback covers the rest), and two unresolved
   `${Ne}${g}.js`/`${ci}${g}.js` template-literal artifacts left over from
   `build.py`'s static asset-reference scan (it can't evaluate a runtime
   JS template literal, so it treats the literal `${...}` text as a literal
   URL segment and 404s trying to fetch it: cosmetic in the build log only,
   confirmed to not affect page function).

## Verification achieved

7/7 sitemap pages mirrored and served, 0 console errors on every page
(checked via real headless Chrome over CDP: `scripts/cdp-run.py` with a
two-phase error-capture probe, not the in-app browser pane, which could not
composite frames in the session this build ran in and timed out on every
screenshot/DOM-read call). Text rebrand verified by exhaustive case-
insensitive scan across every text-bearing extension actually present in
`cdn/` (`css`, `framercms`, `js`, `json`, `mjs`) plus `site/*.html`: the only
surviving "hanzo" occurrences are the guard script's own fix-up code (which
necessarily contains the word it matches/replaces) and non-visible plumbing
(`canonical`/`og:url`/`siteCanonicalURL`, a source-crediting HTML comment),
left intentionally per this library's standing convention. One incidental
real-copy mention of "Framer" survives by design (the portfolio owner's own
sentence recommending "trusted no-code or Webflow/Framer developers"). Match
mode preserves real captured copy verbatim; this is content, not platform
branding. Not diffed against the reference (rebrand target, not a fidelity
study): no similarity score applies, matching the ciaoenergy/homy/
agentwise/fusionai rebrand-build convention. Do not publish: template
photography/copy, local rebrand study only.
