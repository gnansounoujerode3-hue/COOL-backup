# The mirror path: Match mode for server-rendered sites

When the site is server-rendered, do not rebuild it by hand. Mirror it: their
markup, their stylesheets in their cascade order, their assets, rewritten to
local paths by script. A hand rebuild of a server-rendered page is re-deriving
files you can fetch. Every transcription step loses fidelity (grid spans read
as 6/12 when they are 7/13, a token guessed at 5.06em when it is 6em). The
mirror has no transcription steps, which is why it measures 99%+ where careful
hand rebuilds plateau near 94%.

## 1. Decide which path applies

`curl` the page and grep it for strings you can see on screen. Do not assume from
the stack. Framer-built sites look client-rendered and pre-render their markup
in full.

- Key strings and section markup present in the raw HTML → **mirror path** (this
  file). This includes sites whose CSS is inlined in `<style>` rather than
  linked, and whose assets sit on a separate CDN.
- Raw HTML is genuinely a shell and content mounts at runtime → **rebuild path**
  (SKILL.md steps 2–4), serializing the *rendered* DOM as your markup source.

## 1b. Static or scripted mirror

Default to stripping scripts: a static mirror is inert, offline, and
deterministic. But stripping freezes any region whose **state** is JS-driven:
product demos, animated walkthroughs, tabbed/cycling panels. The page still
renders; that region just sits at its initial state and scores far below the
rest.

Diagnose before you conclude the mirror failed:

1. Screenshot the **reference against itself** on two independent loads. If a
   region is not self-consistent, it is animated or stateful.
2. Compare that self-similarity to your mirror's score for the same region.
   Mirror far below reference-vs-itself → the region needed the scripts.

Then produce a **scripted variant**: mirror the JS modules alongside the other
assets, rewrite their urls per step 2, and keep the `<script>` tags. Still
neutralize every `<a href>` and `<form action>`: to `#inert`, never bare `#`.

Measured on framer.com's product-demo panel:

| | scripts stripped | scripts mirrored |
|---|---|---|
| editor panel | 84.12% | **99.55%** |
| viewport | 90.88% | **99.74%** |

Reference-vs-itself on that panel was 99.13%, so the scripted mirror is as
faithful as the page is to itself; that is the ceiling, and chasing past it
measures animation phase, not fidelity.

The tradeoff is real and worth stating in the notes: a scripted mirror executes
the site's own JS locally and may still reach out to their origin, so it is not
a fully offline artifact. Prefer static; escalate to scripted only for the
regions that demand it.

## 2. Mirror procedure

All steps are scripts. Text content is data travelling page → file; it never
needs retyping, and retyping it is how errors enter.

```bash
UA="Mozilla/5.0 ... Chrome/150.0"           # some CDNs 403 curl's default UA
ACCEPT='image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
curl -sL -A "$UA" "$SITE/" -o ref.html

# every stylesheet the page loads, in order
grep -oE 'href="/assets/css/[^"]+' ref.html | sed 's|href="||' > css-list.txt
```

Send the `Accept` header too, not just the UA. A CDN answering `vary: Accept`
hands your mirror different bytes than it hands the browser:
framerusercontent.com serves AVIF to Chrome's `image/avif,image/webp,…` and PNG
to `Accept: */*`, which is what a bare fetch sends by default. Both are 200, so
nothing in any log says anything happened; you have simply mirrored a different
image set. Verify before trusting it: `curl -sI '<asset>' -H 'Accept: */*'`
against `curl -sI '<asset>' -H "Accept: $ACCEPT"` and compare `content-type`.
Local names keep the original extension, so after an Accept-correct fetch a file
called `.png` holds AVIF bytes and the served `Content-Type` has to come from
the leading bytes rather than the name.

Then, in a script (not by hand):

1. **Rewrite CSS asset urls**: every `url(...)` → the local asset name,
   root-absolute (`url(/cdn/...)`) like the module bodies below, so the same
   sheet resolves from any page depth, and collect every referenced url while
   doing it.
2. **Mirror every referenced asset**: fonts, icons, images from the CSS pass,
   plus everything the HTML references via `src`, `srcset`, `poster`. A response
   counts as mirrored only if it is 200, the body is non-empty, a binary asset's
   first bytes are not `<!doctype`/`<html`, and the content-type does not
   contradict the extension. A soft 404 is HTTP 200 with an error page in the
   body; written to `hero.png` it is an integrity problem that resurfaces two
   steps later as a region that looks like it failed to render. Keep every
   rejection as `(url, reason)`. That list is the report's Assets row and the
   first thing to read when a region scores short.

   **Keep the query.** A distinct query is a distinct asset: srcset candidates
   like `?scale-down-to=512&width=1024` and `?width=1024` are one path and
   different images, so stripping the query collapses every candidate onto the
   full-size original. All of them still return 200 and a screenshot cannot see
   it. Strip only params you have confirmed are cache-busters (`?v=`, `?t=`);
   every other distinct (path, query) gets its own local file, which `build.py`
   names `stem__<8hex>.ext`.

   **Derive the CMS siblings.** Collections ship as `-chunk-`/`-indexes-` pairs
   and only one name is a literal in the bundle. The other is built by runtime
   substitution, so a scan finds one, the loader 404s on the other, and the
   collection renders empty with no error. Substitute the name both ways and
   fetch both. A derived name that 404s upstream is expected and harmless.

   **Follow the text assets to a fixed point.** Re-scan every mirrored text
   asset (css, js, mjs, json, CMS data) for the URLs it references, and resolve
   relative dynamic imports against *that module's own* URL, not the page's.
   Bundler chunks reference each other as `import('./X.mjs')`, which a
   host-anchored scan over markup cannot see. Add what is new and repeat until
   the set stops growing (`build.py --max-rounds`, default 6). Skip it and the
   srcs those modules build at runtime keep pointing at the origin: on one site
   that left 157 broken references visible only at 390px and 768px while desktop
   measured at its ceiling, which is why step 4 is run at every breakpoint.

   **Rewrite the module bodies root-absolute** (`/cdn/x`) where markup gets the
   relative form (`cdn/x`). Inside a module the same string is resolved against
   the module as an import specifier and against the document when it becomes a
   DOM `src` at runtime; `./x` is correct for one and 404s for the other.
   Never relativise a URL used as the second argument of `new URL(rel, base)`:
   a base must stay absolute or the constructor throws TypeError, and one
   uncaught error in a framework bundle takes the whole render down. The symptom
   does not point at the cause: images and boxes paint normally while **all text
   disappears** and counters freeze. Where the base sits in a template literal,
   substitute `location.origin` so it stays absolute with no hardcoded port.

3. **Build the local page from ref.html**:
   - strip every `<script>` block: the mirror must be fully static
   - strip `integrity=` and `crossorigin=` from every `<link>` and `<script>`.
     Rewriting a sheet's `url()`s changes its bytes, the SRI hash stops matching,
     and the browser drops the entire sheet with **no console error**; the page
     renders in Times and `document.fonts.size === 0`, which reads as a font
     problem and is not one
   - point every asset url at its local name, keeping any query that is not a
     confirmed cache-buster (step 2), then relativize paths
   - neutralize all `<a href>` except `#anchors` and local assets → `#inert`,
     never bare `#`: an anchor component that runs
     `document.querySelector(href)` raises SyntaxError on `'#'`, and that throw
     has taken a whole component tree down with it
   - neutralize every `<form action>` → `#inert`
   - stamp a comment at the top: local study mirror, links inert, do not publish
4. **Sweep for origin references, then measure.** Zero absolute references to
   the reference's domain may remain. `grep -R` over the built tree is the cheap
   pre-check and it is necessary: attribute-driven rewriting (`src`, `href`,
   `srcset`) misses inline `<style>` blocks (where `@font-face` usually lives)
   plus JSON-LD, `og:` meta, and preloads. Cross-origin fonts are CORS-blocked
   and fall back **silently**, so this single missed class of URL quietly changes
   every text width on the page. Mirror what the sweep finds.

   Grep is not the authority. It does not follow symlinks, so a grep of the page
   directory never descends into `site/cdn -> ../cdn` where every mirrored module
   lives, and it cannot see a URL a bundle assembles at runtime from parts. A
   clean `0` has coexisted with a mirror loading an iframe from the reference's
   origin on every page. Serve the build and read the network log:

   ```js
   performance.getEntriesByType('resource')
     .filter(e => !e.name.startsWith(location.origin))   // must be empty
   ```

   Read the local 404s in that same log too. Assets that failed to mirror are
   pointed at local paths on purpose, so a miss surfaces here as a 404 you can
   name instead of as an origin reference you never see. Run this on **every**
   variant you build and at **every** breakpoint: a scripted variant rebuilt
   from raw HTML does not inherit the static variant's fixes, and the components
   that build srcs at runtime are usually the mobile ones. Only then verify fonts
   per the gate in SKILL.md (`document.fonts.check` + canvas width A/B).
5. **Serve over HTTP with `scripts/serve.py`**: `file://` breaks path
   resolution and renders as a static snapshot in some panes. Use `serve.py`,
   not `python3 -m http.server`: the stock server ignores query strings, and
   Framer's CMS loader slices data chunks with `?range=a-b` (and multi-range
   `?range=a-b,c-d`, comma percent-encoded) then validates the response length.
   Getting the whole file back raises `Unexpected response length`, which Framer
   treats as fatal and tears the rendered tree down to an empty shell. It races
   the render, so it looks intermittent; a headless capture can pass while the
   interactive page collapses. One page measured **9.76% against a 99.93%
   ceiling** from this alone while its 20 siblings sat at 99.7%+. `serve.py`
   also pins the MIME types that block ES modules when guessed wrong. It is a
   drop-in replacement, so use it for every mirror: one that never issues a
   range request is unaffected.

   Serve the variant directory, not the run root. `build.py` symlinks
   `site/cdn -> ../cdn` so both forms resolve from inside it: the relative
   `cdn/x` in markup and the root-absolute `/cdn/x` in module bodies.

   ```bash
   python3 serve.py --directory site --port 8791
   ```

## 3. Verify

Region-split pixel diff per `verify.md`. Expect ≥99% overall. Residuals that are
normal and not worth chasing: server-printed live numbers (visitor counters
differ per load), animation-frame timing, glyph antialiasing noise.

If a region is materially below the rest, something failed to mirror. Read the
build's rejection list and the network log before theorising: assets that
returned HTML 404 bodies, absolute urls the rewrite missed, or content the page
mounts with JS (that region needs the rebuild path grafted in). A page that
paints its images and boxes but shows **no text at all** is not a mirroring gap;
it is an uncaught throw in a module, and the `new URL` bases are the first
suspect.

## 4. What the mirror is for, and the line

The text layer arrives verbatim because the mirror copies files. That is the
point: a pixel-true scaffold whose copy, imagery and branding the user then
replaces with their own. The standing rule from SKILL.md applies with no
exceptions here: **local study artifact only.** Links inert, scripts stripped,
do-not-publish stamped in the file. Published as-is it would be an infringing
copy of a real organisation's site; with the user's own content poured in, it
is their site on a proven structure.
