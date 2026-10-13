# agentwise.framer.website

**Callable as: Agentwise** (aliases: agentwise.framer.website, the real-estate-agent Framer template)

Real-estate-agent marketing template (Framer): single-agent personal brand site
(home, about, listings, blog/articles, contact, legal). Captured 2026-08-10 @
1440x900. Stack: Framer (React + the bundled Motion library), CMS-backed
blog/property/legal collections. **Mirror path** (full scripted mirror + full
sitewide rebrand to "Systowise" / agent "Systo Denim").

## Type: flat 16px root, two-family Inter system, no serif

No fluid rem driver: root font-size is a flat `16px` throughout (confirmed via
`getComputedStyle`), matching every other Framer capture in this library. Two
families only, both self-hosted with Framer's metric-compatible `"X Placeholder"`
fallback pair: **Inter** (314 declarations: UI/body) and **Inter Display** (290
declarations: headings). No third serif/display face on this template, which
breaks the "serif earns its keep at display size" pattern seen on osa/philllia.
Not every Framer site carries one.

## Layout

Breakpoint edges found in the stylesheet, by frequency: `809px` (45), `1439px`
(40), `1919px` (37), `1900px` (19), `1199px` (7), plus a `809.98px` fractional
form (2) confirming the `.98` convention still coexists with integer edges on
this site too. The 809/1199 pair is the primary two-step ladder this library has
now seen on every Framer capture; 1439/1919/1900 are this template's *own* extra
wide-desktop steps layered on top. Breakpoint count is not fixed sitewide, only
the low pair is a constant.

## Colour

Colour custom properties are UUID-named (`--token-<uuid>`, e.g.
`--token-5b89944e-d417-4e57-bfaa-d006e07ad499` → `rgb(255,255,255)`). The values
are the system, the names carry nothing, consistent with every prior Framer
capture. Palette is a dark hero (near-black `rgb(9,14,14)`–`rgb(14,33,32)`
gradient stops) over an otherwise light/white body. No single accent colour
dominates; this template leans on photography (agent portrait, property photos)
rather than a brand-colour system.

## Motion

**Motion fidelity: partial**

Signature easing by use count: **`cubic-bezier(0.65, 0, 0.35, 1)` @ 0.9s** (32
uses) is the dominant curve, new to this library (prior Framer captures
converged on `cubic-bezier(.44,0,.56,1)`), so "Framer's default easing" is now
confirmed to vary *by template*, not by platform. A secondary `0.6s` duration on
the same curve family covers smaller UI transitions (8 uses). Bulk of the
motion still runs through the bundled Motion library as `type="framer/appear"`
payloads (unmeasured per-animation here, hence `signature-only`, not `spec`).

**The one mechanism worth recording precisely: a per-character blur/offset
entrance reveal on `<h1>` headings**, one `<span>` per character, each starting
at `opacity:0.001; filter:blur(10px); transform:translateY(10px)` and animating
to settled. This is on every page's H1 (article titles, property names, the
homepage agent-name heading), **and it is also the site's decrypt/scramble
variant**: the homepage's two-line agent-name heading (first name / last name
on separate lines) additionally cycles through randomised placeholder glyphs
before locking each character, via a `children:` template-literal prop compiled
directly into the JS bundle (not present in the SSR HTML at all for the
first-name line; present but frozen mid-reveal for the second line; see
gotcha 4).


### Addendum 2026-08-13: measured with `motion-extract.js --pre`

Re-measured during the Retirement Architects rebuild (which adapts this system),
so the entry is no longer signature-only. 13 animations at 1440x900, 8
CSSTransition + 5 Animation, 5 scroll-triggered.

- **Durations by count: 900ms x6, 600ms x6, 700ms x1.** Confirms the 0.9/0.6
  pair recorded above as the template's two real steps.
- **Easing: `cubic-bezier(0.65, 0, 0.35, 1)` x8**, plus 5 baked springs
  (`linear(...)` with 60-70 stops) from the bundled Motion library.
- **Stagger ladder: 80ms**, a 6-element group with delays
  `[0, 80, 160, 240, 320, 400]`, all 900ms on the signature curve, animating
  `height` to `0%` (a mask wipe, not a fade).
- **Framer appear payload:** `initial { opacity: 0.001, scale: 1, x: 0, y: 0 }`,
  spring `{ damping: 50, delay: 0.4 }`. The `0.001` matches the per-character
  heading reveal recorded above, and **0.4s is the real hero delay**: worth
  copying, because a shorter one makes the decrypt feel rushed.

Still `partial` rather than `spec`: there is no per-animation target->from/to
mapping for the bulk of the appear payloads, only the group above.

## Interaction states

Not separately captured this pass (scope was Match + full-site rebrand, not a
component-level interaction audit).

## Template taxonomy (multi-page crawl)

| Template | Instances | Fixed | Varies |
|---|---|---|---|
| Home | 1 | hero, stats, featured properties, insights, footer | - |
| About | 1 | agent bio, team photos | - |
| Article listing | 1 | grid of blog cards | - |
| Article detail | 7 | H1 title, body rich-text, sidebar | headline, body copy, cover image |
| Property listing | 1 | grid of property cards | - |
| Property detail | 5 (+1 "schedule a showing" variant reusing the same template) | gallery, specs (beds/baths/sqft/price), CTA | address, price, photos, specs |
| Contact | 1 | form (inert), hours, map area | - |
| Legal | 2 (privacy, terms) | rich-text body | copy only |

21/21 sitemap pages mirrored (the 22nd sitemap entry, `/404`, is the error page
and correctly excluded; it 404s on the live reference too).

## Gotchas hit while rebuilding

1. **`build.py`'s documented `/../site/cdn/` root-absolute bug is not fixed in
   the script, only worked around per-build.** Passing `--cdn` as anything
   other than the bare leaf name (`cdn`) (e.g. `../site/cdn`, matching the
   `--out` value) makes the tool literally interpolate that string into
   `f'/{a.cdn}/'` for every rewritten URL, producing `/../site/cdn/x`, which
   browsers clamp to `/site/cdn/x` (one directory too deep, universal 404).
   **Fix:** always run `build.py` bare (`python3 build.py`, no `--out`/`--cdn`
   flags) from inside `crawl-out/`, which uses the correct defaults
   (`--out site --cdn cdn`) and produces a working `site/cdn -> ../cdn` link;
   move both `site/` and `cdn/` up to the mirror root together afterward if
   the convention calls for them as root-level siblings, never independently.

2. **Git-Bash `ln -s` for a directory on Windows does not create a link
   Windows-native processes (Python, Chrome) can see**, even though
   `readlink`/`ls -la` *from Git-Bash itself* report it as a working symlink
   immediately after creation. `os.path.islink()` (native Python) returns
   `False` on the same path. The practical failure mode is silent and
   severe: edits made to the real target directory (`cdn/`) never reach the
   directory the static file server actually reads from (`site/cdn/`, which
   MSYS silently degrades into an independent, diverging physical copy).
   Every subsequent edit appears to work (no error, on-disk source-of-truth
   is correct) while the served site keeps the pre-edit bytes indefinitely.
   This produced real symptoms indistinguishable from a live framework bug
   (React hydration mismatches: minified error #418/#425, "recoverable",
   component stack pointing at the stale element) that a naive read would
   blame on the site rather than the mirroring step. **Detect:** compare
   `os.path.getsize()` (or a content hash) between the two paths after any
   edit to a directory reached through a Git-Bash-created symlink; they
   should be identical and frequently are not. **Fix:** don't trust the
   symlink on Windows for anything Chrome/Python must read; `rm -rf` the
   linked path and `cp -r` a real, independent copy instead, and repeat the
   copy after every edit to the source (or edit both copies directly).

3. **CMS collection-name "chunk"/"indexes" pairs live in TWO places, not
   one, and only the version with a mirrored-asset hash suffix
   (`<id>-chunk-default-0__<hash>.framercms`) is a real, fetchable file**,
   confirmed already in this library for onefin/createstudio, but this
   capture adds: the runtime *also* requests the bare, hash-less form
   (`<id>-indexes-default-0.framercms?range=…`) directly, which 404s both
   locally and against the live upstream CDN (verified with a live `curl`);
   i.e. it is not a mirroring gap at all, it 404s on the reference too, and
   a component that depends on it still renders correctly from a compiled
   fallback. Confirms the "expected and harmless" classification generalizes
   rather than being onefin-specific.

4. **A crawler captures an entrance/decrypt text-reveal animation at
   whatever frame it happens to be on, and that frame gets frozen into the
   static mirror forever**. This build's hero last-name heading was
   captured mid-scramble (`data-framer-name="DEhdysNIM"` for what settles to
   "DENIM": first/last two and last three characters already resolved,
   middle four still showing randomised placeholder glyphs). The frozen,
   *unsettled* SSR text does not match what the client's own first paint
   produces (a *different* random placeholder sequence, since the effect
   re-randomises on every mount): a **genuine, unavoidable-by-content-edit
   React hydration mismatch** (`#425`, "text content does not match"),
   confined to whichever page(s) carry that heading. It self-heals (React's
   own recovery patches the DOM, the settled text is provably correct half
   a second later, verified) and produces no visible or functional defect,
   only a console warning. Unlike gotcha 2, this one is NOT fixable by
   editing static content: the non-determinism is inside the compiled
   animation library itself, and a static single-snapshot mirror cannot
   reproduce a live server's ability to resync its random seed with the
   client on every fresh request. Report it; do not chase it.

5. **A "search index" CMS-adjacent asset (`searchIndex-<hash>.json`) carries
   its own full-text copy of every page**, separate from both the per-page
   SSR HTML and the CMS `.framercms` files. A sitewide rebrand that only
   walks `*.html`/`*.mjs`/`*.css` misses it silently (it has no code-like
   extension to catch a broad glob, and grep's line-count `-c` badly
   undersold it: reported as "1" match per file because the whole file is
   one line, when the real count was 99 occurrences per file). Grep every
   text-bearing extension actually present in `cdn/`, not an assumed set:
   `ls cdn/ | sed 's/.*\.//' | sort -u` before deciding what a rebrand
   script's glob should cover.

6. **The `.framercms` CMS format is length-prefixed binary, not plain
   text**, confirmed by reading raw bytes around a string field: a type tag
   byte followed by a 4-byte little-endian length, then exactly that many
   bytes of content (`\x0c\x00\x00\x00\x0eMarket Reports` → tag `0x0c`,
   length `14`, and `"Market Reports"` is 14 bytes). A same-length
   substitution (`Agentwise`→`Systowise`, both 9 bytes; `agentwise.com`→
   `systowise.com`, both 13) is safe in place. A **different**-length
   substitution is not safe without also patching every length prefix and
   any offset table in the paired `-indexes-` file (this is exactly the
   mechanism behind the already-documented `?range=` byte-slicing gotcha).
   Verify the byte delta is zero before writing, never assume text-editor
   semantics apply to a `.framercms` file.

7. **A raw substring search for a first name across binary CMS payloads
   produces false positives from ordinary words that happen to start with
   it**. This template's blog content legitimately discusses "the **Mark**et"
   many times ("Market Reports", "Local Market Update", "A Market That
   Rewards Preparation"); a byte-level `b'Mark'` search matched 11 times
   across two collection files with **zero** of them being the agent's name.
   Confirmed by reading the surrounding bytes (the length-prefixed field
   read as `"Market Reports"`, `"Local Market Update: Trends…"`, etc.) before
   writing anything. The equivalent risk does not exist for the full
   `"Mark Denim"` phrase (space-plus-surname is not a substring of any real
   word on the site), which is why the HTML/JS-level rebrand used the full
   phrase throughout and never touched a bare `"Mark"` outside one confirmed,
   inspected, backtick-bounded template-literal (`` `MARK` ``, the kinetic
   heading's compiled prop, the only ALL-CAPS occurrence anywhere in the
   mirror, verified by an exhaustive scan before treating it as safe).

## Verification achieved

21/21 sitemap pages mirrored and served (the 22nd sitemap entry is the site's
own `/404` page, correctly excluded: confirmed 404 on the live reference).
Zero unexpected console errors across all 21 pages after the rebrand pass; the
only recurring console noise is the already-classified harmless CMS
chunk/indexes 404 (gotcha 3) and the unfixable decrypt-animation hydration
warning on the pages carrying the scrambled hero heading (gotcha 4), both
confirmed benign by cross-checking the live reference and by settled-state
re-checks. Text rebrand verified by exhaustive byte-level scan (not just a
line-count grep; see gotcha 5) across every file in the mirror (`site/*.html`,
`cdn/*.mjs`, `cdn/*.css`, `cdn/*.framercms`, `cdn/searchIndex-*.json`): zero
residual "Agentwise"/"Mark Denim" in any visible-text or CMS-payload location;
the only surviving lowercase `agentwise.framer.website` strings are the
non-visible `canonical`/`og:url` plumbing, left intentionally per this
library's established convention (never rendered to a user). Not diffed
against the reference (rebrand target, not a fidelity study): no similarity
score applies, matching the ciaoenergy/homy rebrand-build convention.
