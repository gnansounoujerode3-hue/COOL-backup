# Multi-page mirrors: crawling a whole site

One page is `mirror.md`. A navigable site is this: seed from the homepage and
from the sitemap, follow same-origin links breadth-first, mirror each page and
its assets, then rewrite internal links to local files so the copy clicks
through like the real thing.

`scripts/crawl.py` and `scripts/build.py` implement it. Crawl writes raw HTML
plus a manifest; build mirrors assets and rewrites links; `scripts/serve.py`
serves the result.

```bash
python3 crawl.py https://example.com/ --max-pages 50 --max-depth 2
python3 build.py          # assets + link rewriting -> site/
python3 serve.py --directory site --port 8791
```

The document root is `site/`, not the run root. Pages reference assets as
`cdn/<name>` in markup and root-absolute `/cdn/<name>` inside module bodies, and
`build.py` symlinks `site/cdn -> ../cdn` so both forms resolve from that root.
Serve any other directory and every asset 404s while the build log stays clean.

**On Windows, verify that symlink is real before trusting it for anything
Chrome or Python reads.** Git-Bash's `ln -s` on a directory can report success
(`ls -la`/`readlink` from Git-Bash itself both show a working link) while
`os.path.islink()` (native Python) returns `False` on the same path, meaning
Windows-native processes (the static file server, the browser) never actually
follow it. The failure is silent and severe: `site/cdn` silently degrades into
an independent, un-synced physical copy, so every edit made afterward to the
real `cdn/` (a rebrand pass, an asset fix) never reaches what gets served;
symptoms look exactly like a live framework bug (React hydration mismatches,
stale text that "should" be fixed) rather than a stale-mirror problem. Verify
with `python3 -c "import os; print(os.path.islink('site/cdn'))"` after any
manual directory move/relink (e.g. relocating `site/`+`cdn/` out of
`crawl-out/`); if it prints `False`, `rm -rf site/cdn && cp -r cdn site/cdn`
instead, and re-copy after every subsequent edit to `cdn/`. There is no
symlink to rely on once this happens. Seen on agentwise.framer.website.

Serve with `serve.py`, never `python3 -m http.server`: the stock server ignores
the `?range=` query parameter that Framer's CMS loader uses to slice data
chunks, and the resulting length mismatch collapses the rendered page. See
`mirror.md` step 5.

`crawl-manifest.json` carries the `origin`, the URL→slug `urlmap`, the `skipped`
map with a reason per URL, and the `sitemap_only` / `crawl_only` difference
lists. `build.py` reads the origin from it, so the mirror is not hardcoded to
any one stack.

## Scope is the whole problem

A sitemap is not a work-list. framer.com publishes **25,763 URLs**; 17,774 are
user-submitted marketplace listings and 1,146 are docs and glossary entries. The
marketing surface a person means by "the site" is roughly 200. A WordPress
studio site overstated itself ~7×: 585 URLs, of which 368 were blog machinery
and 114 portfolio entries, against roughly 40 pages of real nav surface.

Read `/sitemap.xml` first and group URLs by first path segment. That histogram
tells you what the site actually is, and which sections are bulk. Quote the
numbers to the user before crawling, and agree the scope: a deep crawl is a
storage decision as much as a fidelity one (52 Framer pages cost 406MB).

The histogram's output is the flag list, not a note to yourself. `--exclude
PATTERN` and `--include PATTERN` are repeatable regexes matched against the
path; pass the agreed sections as flags rather than editing `BULK_PAT` in the
script, because a script edit persists into the next capture of an unrelated
site. `--include-bulk` re-admits everything the defaults skip. The default bulk
list is deliberately wide (`blog`, `news`, `tag(s)`, `category`/`categories`,
`author(s)`, `glossary`, `forum`, `support`, `kb`, `docs`, `help`, `community`,
`marketplace`, `dictionary`, `developers`) because the sections that dominate a
sitemap are almost never the design surface.

## The five boundaries

The crawler stops at the first four and reports counts by reason. The fifth
leaves no trace in that table at all. Expect to hit all five:

1. **robots.txt.** Parse `Disallow` for `User-Agent: *` and honour it, wildcards
   included. Framer disallows `/api-proxy` and seven query-param patterns. Add a
   delay between requests; you are a guest.
2. **Auth walls.** Detect two ways, because path patterns alone miss redirects:
   by path (`/login`, `/signup`, `/account`, `/dashboard`, `/settings`,
   `/billing`, `/checkout`), and by behaviour: HTTP 401/403, or a redirect
   whose final URL is a login page. These pages are somebody's account, not
   design surface. Never attempt credentials to get past one.

   `/projects` is deliberately **not** in the path list. It reads as an account
   area on an app dashboard and as the portfolio on a studio site, and the guess
   dropped 5 real case studies as "auth-gated" on a measured run. The portfolio
   index mirrored fine, so it surfaced as a card grid of dead links rather than
   an obviously missing section. Portfolio paths (`/projects`, `/work`,
   `/case-studies`) get probed, never assumed: 200 with no login redirect means
   crawl it. Behavioural detection still catches a real wall on any path,
   including a 403 on a path no pattern covers.
3. **Bulk sections.** User-generated listings, help centres, API docs,
   glossaries. Thousands of pages, near-identical templates, no design value
   after the first. Excluded by default; opt in per section with `--include`.
4. **Off-site, binaries, non-http schemes.** `mailto:`, downloads, other origins.
5. **Undiscovered pages.** Link-following is not complete, and this boundary
   lands in no skip bucket, so a clean four-way reason table reads as proof of
   completeness while real pages are missing. Paginated indexes hide their tail.
   Three osa URLs (`/waitlist` and two articles) were unreachable because the
   articles index paginates, and JS-built listings hide everything. Links on a
   page already at `--max-depth` are never extracted either. The sitemap is the
   only detector: it seeds the queue at depth 1 *and* gets set-differenced
   against what the crawl reached.

## Coverage: before you quote a page count

`--sitemap URL` defaults to `<origin>/sitemap.xml`; `--sitemap ""` skips it.
The run ends with a coverage block: how many sitemap URLs were listed but never
crawled, the first 10 by name with the reason each was skipped, and the line
"Read the skip reasons before trusting this page count." Do that, in this order:

- Read `crawl-manifest.json`'s `skipped` map by reason. Every URL still queued
  when `--max-pages` hits is recorded as `max-pages cap` instead of vanishing,
  so the totals reconcile instead of quietly disagreeing.
- Re-probe every `auth-gated` entry for 200-without-login-redirect. A path
  pattern is a guess; the response is evidence. This is the check that would
  have caught the 5 dropped case studies.
- Work `sitemap_only`. Seed and crawl whatever is real; account for the rest by
  reason in the report's Excluded row.
- `crawl_only` is usually pagination or a page the sitemap omits (not an error,
  but proof the sitemap is not authoritative either). Neither list alone is the
  page count; the reconciliation is.

## Local paths: go flat

Write every page as a flat `<slug>.html` (`/solutions/designers` →
`solutions__designers.html`). Nested directories force per-page relative-depth
arithmetic for shared assets, and that arithmetic is where mirrors break. Flat
means every page references `cdn/…` identically.

## Link rewriting

Build a map of crawled URL → local slug, then for every `<a href>`:

- points at a page we mirrored → rewrite to its slug (navigation works)
- anything else → `#inert`, **never bare `#`**. Framer's anchor component runs
  `document.querySelector(href)`, and `querySelector('#')` raises SyntaxError,
  which can stop the whole component tree rendering, a self-inflicted wound
  from the standard mirroring recipe. Any valid-but-unmatched selector is
  equally dead as a link target and costs nothing.
- `<form action>` → `#inert`

Report both counts. A healthy Framer run: 7,267 links wired, 12,377 inert.

## Extracting asset URLs: truncate at the extension, keep the query

A naive `https://cdn\.example\.com/[^\s"'),]+` swallows trailing escape and
entity artifacts from the surrounding HTML: `image.jpg\`, `icon.svg&quot;`,
`hero.png<code`. Those 400/403 and look exactly like rate-limiting or dead
assets. On one Framer run this manufactured 362 phantom URLs and hid the 33 real
failures inside them.

A stop-character list is necessary but not sufficient, and that exclusion class
is itself a second bug. `;` and `:` are not stop characters, so a `url()` inside
a CSS custom property in an inline `<style>`, followed by `);--next-prop:…`,
runs straight into the next declaration, and no trailing-strip recovers it.
Meanwhile `)` and spaces are legal filename characters, so excluding them
truncates `Britain-25 (1).webp` to `Britain-25`, which 404s, is never mirrored,
and leaves the absolute reference alive in the rewritten page.

So: capture greedily, then truncate at the **first valid file extension**,
`ASSET_EXT` in `build.py`, published once so the extractor and the fetcher agree:

```
woff2? ttf otf eot | png jpe?g gif webp avif svg ico bmp | mp4 webm mov m4v
ogg mp3 wav | css js mjs json framercms txt xml wasm map | glb gltf hdr exr
ktx2 basis bin
```

`.framercms` is a real extension that appears in no default list. Apply the stop
characters only to whatever follows the extension. A token with no extension
match is not an asset URL; discard it rather than repair it.

**Keep the query string.** Query params are asset identity, not noise:
`?scale-down-to=512&width=1024` and `?width=1024` are different images sharing
one path, so stripping the query collapses every `srcset` candidate onto the
full-size original: HTTP 200 throughout, nothing in the network log, and the
residual shows up only at 390px and 768px. Strip only params you have confirmed
are cache-busters (`?v=`, `?t=`). Every distinct `(path, query)` gets its own
local file.

That scan is **one pass over markup** and does not finish the job. Bundler
chunks reference each other as `import('./X.mjs')`, invisible to a host-anchored
regex, and components assemble image `src`s at runtime inside module bodies.
Re-scan every fetched text asset (css, js, mjs, json, CMS data), resolving
relative specifiers against that module's own URL, and iterate until the set
stops growing. On one site the missing half was 157 broken references that
appeared only at 390px and 768px while desktop measured at its ceiling.

Verify by count: clean list length should be stable across re-runs, and "still
missing" should reach zero.

## Verify

Score **every** crawled page against its own reference-vs-itself ceiling with
the region diff in `verify.md`, and print the full per-page table. Flag any page
sitting more than ~0.5 points under its own ceiling. Never report only an
aggregate.

Spot-checking is how a broken page ships. A 21-page run averaged well while one
page sat at **9.76%** against a **99.93%** ceiling and its twenty siblings sat
at 99.7%+ (invisible to the mean, and invisible on the homepage).

Section coverage is not page coverage either. A Framer 52-page run measured
pricing 100.00%, enterprise 99.99%, a customer story 99.78%, a solutions page
96.92%. That last one is a 3-point outlier that clears a 95% floor and still
wants an explanation before the run is called done.

## The line

Everything in `mirror.md` applies, and scale sharpens it: a multi-page mirror is
a substantial copy of someone's site on local disk. Links inert, forms inert,
do-not-publish stamped in every page. It exists as a structural scaffold to
refill with the user's own content.
