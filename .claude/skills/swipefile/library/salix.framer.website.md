# salix.framer.website

**Callable as: Salix** (aliases: salix.framer.website, Saalix, the SaaS/CRM Framer template)

Multi-layout SaaS/CRM marketing template (Framer): 3 homepage variants, 3
pricing variants, 3 company/about variants, 2 contact variants, a product
page, book-a-demo, career hub + 6 postings, case-study hub + 8 studies,
integration hub + 9 integrations, blog hub + 10 posts, one legal page.
Captured 2026-08-10 @ 1440x900/1440x1000. Stack: Framer (React + bundled
Motion/`rolldown` runtime, CMS-backed blog/case-study/career/integration
collections). **Mirror path** (full scripted crawl + full sitewide rebrand
to "Systolix").

Marketplace listing note: the Framer Marketplace page's own title stylizes
this template as **"Saalix"** (double-a). The live site itself, every page
title, and all body copy consistently say **"Salix"** (single-a). Always
verify the brand string against the *live* site, never the marketplace
listing's display name; they can differ (probably a marketplace slug/dedup
artifact, not a deliberate second spelling).

## Type: Inter workhorse + Geist display, flat 16px root

Two families, both self-hosted with Framer's metric-compatible `" X
Placeholder"` fallback: **Inter** (body/UI, the overwhelming majority of
`font-family` declarations) and **Geist** (secondary/display, seen on
headline-weight text). Root font-size is a flat `16px`: no fluid-rem
driver, consistent with most of this library's Framer captures.

## Layout

**Breakpoints: 767.98/768 and 1199.98/1200px**, a **two-step ladder that
breaks this library's previously-universal 809.98/810 + 1199.98/1200
Framer triad**, seen unbroken across 6 prior captures (youtube isn't
Framer; createstudio/osa/onefin/homy/agentwise/fusionai all used 809/810).
This is now the second data point (after onefin's `.98`-vs-integer finding)
proving a Framer "constant" can vary **by template**, not just by capture
count. Always tally the actual `@media` values per site rather than
assuming the low breakpoint is 809/810. See INDEX.md cross-site patterns.

## Colour

Accent is a **cyan → blue linear gradient**, `#21CCEE` → `#1470EF`, used
consistently on the logo mark, primary buttons' glow, and the homepage's
thin top accent bar. Text: ink `rgb(24, 24, 24)` (headings), secondary
`rgb(70, 72, 77)` (body/muted). Background is white throughout: no dark
sections observed on the pages captured this pass.

## Motion

**Motion fidelity: none**, not separately captured this pass (prioritized
the full-site rebrand + CMS-binary correctness work over a motion-spec
pass). The template does carry a per-character kinetic-reveal effect on
every page's main heading (see gotcha 4): mechanism identified, timing/
easing not measured.

## Template taxonomy (multi-page crawl)

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Home | 3 (`/`, `/home-02`, `/home-03`) | nav, footer, dashboard-mockup hero image | headline, layout arrangement |
| Pricing | 3 | plan cards, toggle | layout only |
| Company/About | 3 | team section | layout only |
| Contact | 2 | form (inert), staff photo strip | layout only |
| Product | 1 | - | - |
| Book a demo | 1 | - | - |
| Career hub + posting | 1 + 6 | listing grid / posting body | role title, description |
| Case-study hub + detail | 1 + 8 | Challenge/Solution/Results/Testimonial sections, 7 images | headline, body copy, metrics |
| Integration hub + detail | 1 + 9 | - | integration name, description |
| Blog hub + post | 1 + 10 | article shell | headline, body copy |
| Legal | 1 (terms-conditions) | rich-text body | copy only |

51/52 sitemap pages mirrored (the 52nd is `/404`, correctly excluded: 404s
on the live reference too).

## Gotchas hit while rebuilding

1. **The crawler picks the *wrong* CDN URL prefix for CMS `.framercms`
   chunk/indexes files, and it looks plausible enough to ship silently.**
   Static asset extraction found candidate URLs under
   `framerusercontent.com/modules/<hash1>/<hash2>/<name>.framercms` and
   `framerusercontent.com/sites/<siteId>/<name>.framercms`. Both 403 on
   direct fetch. The URL the **live runtime actually requests** is a third,
   different shape: `framerusercontent.com/cms/<hash1>/<hash2>/<name>.framercms`
   (confirmed only by loading the live reference in a real browser and
   reading the network log; this generalizes the library's existing
   "runtime-built asset paths are invisible to static analysis" finding to
   *CDN host paths*, not just relative import specifiers). Symptom in the
   mirror: `Made UI non-interactive due to an error... at K.loadModel`
   console errors plus 404s on **the correctly-named local file**, because
   build.py had in fact successfully fetched *some* bytes from the wrong
   prefix and saved them under a `<name>__<hash8>.framercms` filename, while
   the page's own runtime requests the **bare** `<name>.framercms` (no hash
   suffix) that was never populated. Fix: visit one live page per CMS
   collection, read the network log for the real `/cms/.../` URL, fetch the
   **complete, unranged** file (a plain `curl`, no `?range=`, returns the
   whole blob), and save it under the exact bare filename the rewritten
   markup/JS already reference. Do **not** trust the hash-suffixed file
   build.py produced from the wrong prefix; on this site it silently
   contained different/incomplete data even though it downloaded 200 OK.

2. **`.framercms` is a real, fully reverse-engineered binary format on this
   capture, and it is dangerous to hand-edit.** Confirmed structure via
   byte-level analysis of `niNTTNprJ` (the case-study collection):
   - **String field:** `0x0C` + 4-byte **big-endian** length + content bytes.
     (Corrects an earlier library note on agentwise that guessed
     little-endian from an ambiguous example; this capture's evidence,
     `\x00\x00\x00\x0e` = 14, only works as big-endian.)
   - **Paired `-indexes-` file, per CMS item:** `0x0C`+len+`<item-id
     string>`, then `0x0B` + **11-byte** big-endian offset + 4-byte
     big-endian length, giving that item's exact byte range in the
     `-chunk-` file. Items are stored **contiguously**: sorted by offset,
     each item's end exactly equals the next item's start, and the last
     item's end exactly equals the chunk file's total size. This checks out
     byte-for-byte and is a reliable way to verify a parse is correct.
   - **A same-length string substitution here is safe** (matches the
     already-documented agentwise finding), **but a length-changing edit is
     NOT**, even when the offset/length table above is recomputed and
     verified perfectly self-consistent (contiguous chain, right total
     size). A "Salix"(5)→"Systolix"(8) title patch across all 8 case-study
     items, done exactly per this model, produced **real corruption**:
     `Error: Reading out of bounds` (`ensureLength`/`readUint8`/`readUint32`)
     on 6 of 8 detail pages, and, more dangerously, **silent content
     truncation with zero console error** on the other 2 (a 2,300-character
     case-study body collapsed to 611 characters, no testimonial/results
     section, confirmed against the live reference's own 2,406-character
     version of the same page). There is clearly at least one more
     structural element this model doesn't capture (a per-item field count,
     a checksum, or a second offset table) that a length change silently
     invalidates. **Do not hand-patch a length-changing edit into this
     format without solving that piece too**. Verify against actual
     rendered page content (character count, section presence), not just
     "the offset chain is still contiguous," before trusting a patch.
     **Reverting to the pristine, unmodified fetch (per gotcha 1) and fixing
     the *visible* text at the DOM layer instead (gotcha 4) is the safe
     path** for any length-changing CMS rebrand on this format until it's
     fully solved.

3. **Search-index JSON (`searchIndex-*.json`) and CMS binary payloads are
   separate copies of the same brand text and must both be checked.** This
   capture's `.framercms` files legitimately contained the brand name (314+
   occurrences per collection) even though a first-pass `grep` reported
   zero. Git-Bash `grep -a` on Windows can silently fail to match text
   inside NUL-containing binary records; **verify with a raw Python
   byte-level search** (`data.lower().find(b'needle')`), never trust a
   binary grep returning 0 as proof of absence.

4. **A per-character kinetic-reveal heading defeats every text-node-level
   rebrand technique, static or live.** Each letter of "Salix" (and every
   other heading word) is baked as its **own** `<span
   style="...">X</span>`, all sharing byte-identical inline styles (no
   per-character stagger data lives in the DOM; the reveal timing is
   driven entirely by JS/DOM order). Consequences, all confirmed live:
   - A plain string search/replace over the raw HTML (`"Salix" in html`)
     never matches. There is no contiguous "Salix" substring anywhere in
     the markup.
   - `document.body.innerText` **does** contain "Salix" (browsers
     concatenate adjacent text nodes when computing it) even though a
     `TreeWalker` over actual text nodes finds **zero** nodes containing
     more than one character, so a MutationObserver/text-guard that
     inspects individual `node.nodeValue` values (the pattern that worked
     fine on every prior Framer rebrand in this library, e.g. homy/
     agentwise/fusionai) **silently does nothing** here, with no error to
     signal the miss.
   - Fix: walk up to the smallest **element** (not text node) whose
     `element.innerText` contains the needle, confirm none of its children
     independently satisfy the same condition (so you pick the true leaf
     container, not an ancestor), then, once the reveal animation has
     settled, collapse that container to `element.textContent =
     fixedText`. This sacrifices the per-character reveal animation on that
     one heading (replaced by a plain, already-visible text node) in
     exchange for guaranteed-correct branding; a fully general fix that
     *preserves* the animation would need to insert/remove sibling
     `<span>`s to match the new character count, which was not attempted
     here.
   - A static HTML edit to these spans (rewriting the per-character
     sequence to spell the new word, preserving span count/style) **does**
     work for first paint, but gets **reverted the instant the CMS binary
     loads successfully** (gotcha 1's fix and gotcha 2's revert both make
     the CMS load succeed), so a static-only fix is not durable once the
     live data path is working; pair it with the live DOM-guard above, or
     skip the static fix and rely on the guard alone.
   - **Scope the MutationObserver callback to the mutation records
     themselves, never re-walk `document.body` on every callback
     invocation**. This repeats Homy's gotcha 4 finding, and the parallel
     Hanzo capture (same day, this library) hit the failure mode this
     causes precisely on a per-character-span page: headless Chrome hangs
     outright. This build's first guard draft called a full
     `fixContainers(document.body)` from inside the observer callback and
     happened not to hang across all 51 pages in testing, but that's an
     empirical near-miss, not a safe pattern. It was rescoped afterward to
     only inspect `mutation.addedNodes`/`mutation.target` before shipping.
     Treat "full re-walk inside the observer" as unsafe by default on any
     Framer page with kinetic per-character headings, this capture's own
     near-miss notwithstanding.

5. **A raster "product screenshot" hero image ships as several
   independently-served responsive variants, and each carries its own copy
   of the baked brand mark.** Framer requests up to 5 differently-sized
   files sharing one logical asset (`<base36id>__<hash8>.png`, from ~512px
   wide up to native resolution, picked by `srcset`/viewport). Fixing the
   one variant your own browser happened to load at your test viewport
   (found via `document.elementFromPoint` → `<img>.src`) leaves every other
   size variant, served to other breakpoints, still showing the old logo.
   Enumerate every `<base>__*.png` sibling in `cdn/` and patch each one,
   scaling the paint-over box and replacement-logo size proportionally to
   that variant's own width (a straight ratio against one manually
   calibrated reference variant worked cleanly here: same crop coordinates
   scaled by `variant_width / reference_width`). Found 5 distinct base
   mockup images across the home/pricing hero sections this way (only 1 of
   5 was visible on the page I happened to screenshot first), 21 files
   total once every responsive variant was counted.
   - These specific mockup files are also a live instance of this
     library's existing "CDN `vary: Accept` hands the mirror AVIF, not
     PNG" finding: every one of them has a `.png`-looking filename but is
     genuinely AVIF-encoded bytes (confirmed via magic-byte sniffing,
     `ftypavif`). Pillow opens and re-saves them correctly regardless of
     the misleading extension: no format conversion step needed, just
     don't be alarmed when a file-type check disagrees with the name.

6. **"nextVariant should be defined" is a real, pre-existing, benign
   assertion error baked into this template's own compiled bundle, not
   caused by any mirroring or rebrand step.** Confirmed two ways: (a) it
   fires identically on the **live production reference site**, completely
   untouched, and (b) it still fires after fully reverting every one of
   this build's own edits (badge-hiding, text rebrand, everything) back to
   a pristine crawl. Do not chase this one on a future Salix capture.
   Verify against the live reference first, the same way this was settled,
   before spending time on it. (A related false lead during this build:
   both a static CSS `display:none` and a delayed-JS hide were tried on
   `#__framer-badge-container` while this assertion was still being
   investigated, and neither choice affected whether the assertion fired;
   it is unconnected to the badge. Both hiding techniques work fine here;
   the delayed-JS version shipped for consistency with the established
   agentwise/fusionai pattern, not because the static-CSS version was shown
   to be unsafe.)

## Verification achieved

51/51 mirrored pages served with 0 residual case-sensitive "Salix" text
(verified by a scripted Playwright sweep reading live `document.body.innerText`
on every page, not just the served HTML: the method that caught gotcha 4),
0 failed requests, 0 load errors, and console output limited to the one
pre-existing benign assertion (gotcha 6) plus, on the CMS chunk/indexes
404 class, none remaining after gotcha 1's fix. Case-study page content
integrity cross-checked against the live reference's own character counts
after the gotcha-2 binary-patch revert (2,298–2,335 chars, 7 images,
testimonial+results present on all 8, matching the live site). All 21
responsive image variants across the 5 distinct dashboard-mockup assets
confirmed rebranded via a full contact-sheet visual review, not spot-checks.
Not diffed against the reference (rebrand target, not a fidelity study):
matches the ciaoenergy/homy/agentwise/fusionai rebrand-build convention.
