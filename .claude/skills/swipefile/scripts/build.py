#!/usr/bin/env python3
"""
Rewrite pass for the mirror — turns crawled HTML into a servable local site.

Reads _raw/*.html plus crawl-manifest.json, mirrors every asset the pages
reference (following text assets to a fixed point), then rewrites each page so
that:
  - assets point at the shared local cdn/ directory
  - links to pages we mirrored point at their local slug (navigation works)
  - links to anything we did not mirror go inert (#inert, never bare #)
  - forms go inert
  - integrity/crossorigin are stripped, because rewriting a file's bytes voids
    its SRI hash and the browser then drops the whole resource silently

Every rule here was paid for by a measured failure; see library/INDEX.md
"Cross-site patterns observed" for the evidence behind each.

Run after crawl.py:  python3 build.py
Then serve with:     python3 serve.py --directory site
"""
import argparse, hashlib, json, os, re, glob, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit, urlunsplit, quote
from urllib.request import Request, urlopen

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/150.0 Safari/537.36")

# A CDN answering `vary: Accept` hands a bare fetch different bytes than it
# hands the browser — framerusercontent serves AVIF to Chrome and PNG to
# `Accept: */*`, so a mirror fetched without this is a different image set.
ACCEPT = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'

# Truncate a captured URL at its first valid extension. Stripping trailing
# punctuation is necessary but not sufficient: a url() inside a CSS custom
# property in an inline <style> is followed by `);--next-prop:…`, and `;`/`:`
# are not stop characters, so the match runs into the next declaration.
ASSET_EXT = (r'woff2?|ttf|otf|eot|png|jpe?g|gif|webp|avif|svg|ico|bmp|'
             r'mp4|webm|mov|m4v|ogg|mp3|wav|'
             r'css|js|mjs|json|framercms|txt|xml|wasm|map|'
             r'glb|gltf|hdr|exr|ktx2|basis|bin')
URL_ANY = re.compile(r'https?://[^\s"\'<>\\`]+', re.I)
EXT_AT = re.compile(rf'\.(?:{ASSET_EXT})(?=[?#]|$|[^A-Za-z0-9])', re.I)
QUERY_STOP = re.compile(r'[\s"\'<>\\`)]')

# Text assets get re-scanned for the URLs they build at runtime.
TEXT_EXT = re.compile(r'\.(?:css|js|mjs|json|framercms|map|txt|xml)$', re.I)
# Relative specifiers, captured with their delimiters so the same patterns can
# both harvest (group 3) and rewrite. Bundler chunks reference each other as
# import('./X.mjs'), which a host-based scan cannot see.
REL_SPEC = re.compile(r"""((?:import\s*\(|from\s+|new\s+URL\s*\()\s*)(['"`])([^'"`]+)(\2)""")
CSS_URL = re.compile(r"""(url\(\s*)(['"]?)([^'")]+)(\2)""")
ATTR_URL = re.compile(r"""((?:src|href|poster|data-src)\s*=\s*)(["'])([^"']+)(\2)""", re.I)
# srcset is a LIST of "url descriptor" candidates, comma-separated — not a single
# URL like the other attributes above, so it needs its own rewrite pass. Missing
# this rewrites the fallback <img src> only; every <source srcset> a <picture>
# actually selects keeps pointing at the origin. A <picture> does NOT fall back
# to <img> when its chosen <source> 404s — only when no <source> matches at all —
# so the visible symptom is not a broken-image icon, it is a blank box exactly
# where a real photo belongs, on img/source pairs everywhere responsive art
# direction is used.
SRCSET_ATTR = re.compile(r'\bsrcset\s*=\s*(["\'])([^"\']+)\1', re.I)
# Google Tag Manager's own published async-loader snippet, byte-for-byte the
# same shape on the large majority of GTM-instrumented sites: a bootstrap
# builds its beacon URL by STRING CONCATENATION at runtime
# (`'https://…/wisetag?id='+i+dl`), so it is invisible to every URL-attribute
# and url()-based rewrite pass above — measured live: a mirror with 0 origin
# refs by every static and asset-level check still fired a real request
# against the target's own production analytics on load. Matched by its two
# structural fingerprints (`event:'gtm.js'`, `insertBefore(j,f)`) rather than
# by container ID, so it generalises to any site's GTM install, and bounded to
# one `<script>...</script>` so it cannot eat an unrelated adjacent tag.
GTM_INLINE = re.compile(
    r'<script(?:(?!</script>)[^>])*>'
    r'(?:(?!</script>).)*?event:\s*[\'"]gtm\.js[\'"]'
    r'(?:(?!</script>).)*?insertBefore\(j\s*,\s*f\)'
    r'(?:(?!</script>).)*?</script>', re.S)
# The no-JS fallback for the same tag: a live off-origin reference sitting in
# ordinary renderable markup, invisible to a JS-driven off-origin-request
# measurement (a <noscript> subtree never executes with JS enabled) but real
# for a screen reader or JS-disabled visit, and still "a live reference to the
# reference's origin" by the report's own definition either way.
GTM_NOSCRIPT = re.compile(
    r'<noscript>\s*<iframe[^>]*\bgtm-iframe\b[^>]*></iframe>\s*</noscript>', re.I)
# Same class as GTM_INLINE, one config value rather than a whole script: a
# bundled analytics SDK (Mixpanel) reads its token from an embedded runtime
# config blob and fires its OWN beacon request at load, invisible to every
# markup-level rewrite. Scoped to the key inside the `"mixpanel":{...}` object
# specifically — a bare `"token":"..."` pattern would also hit unrelated
# tokens (OAuth, CSRF, other vendors' own "token" keys) sitting elsewhere in
# the same config blob.
MIXPANEL_TOKEN = re.compile(r'("mixpanel":\{[^}]*?"token":")[a-f0-9]{16,64}(")')
# Blanking the token above stops the beacon but not the SDK: Mixpanel's own
# init sequence hits a remote "decide"/config endpoint that cannot exist on a
# static mirror, and — measured live on wise.com — the SDK's OWN code then
# dereferences a property off the config that request was supposed to fill in
# (`.opt_out_tracking_persistence_type`, read inside the SDK's own minified
# source, confirmed by grep), throwing with no error boundary catching it.
# Next.js treats the failed render as a cancelled route and falls back to its
# own 404 page — the whole homepage replaced by "we lost this page", not a
# blank frame this time, but the same root cause as a missing chunk: live
# code depending on a live backend the mirror cannot provide. A neutered
# token cannot fix code that runs regardless of whether the token is real;
# only NOT running it can, the same full-removal treatment GTM's own
# bootstrap already gets above. Matched on the vendor's own filename, which
# is stable across however the site loads it (a literal <script src>, or —
# as on wise.com's own homepage — a runtime string built from a CDN host
# plus a path fragment, invisible to any markup rewrite).
LIVE_ANALYTICS_SDK = re.compile(r'/mixpanel[-\w.]*\.min\.js(?:[?#]|$)', re.I)
ANALYTICS_STUB = (
    b"// swipefile: live analytics SDK stubbed out of this mirror. Its real\n"
    b"// init depends on a remote endpoint no static mirror can serve; letting\n"
    b"// it run crashes deep inside the SDK's own code when that dependency\n"
    b"// never resolves, which is worse than the tracking simply not firing.\n"
    b"(function(){function noop(){return stub}"
    b"var stub=new Proxy(noop,{get:function(){return noop},apply:function(){return stub}});"
    b"if(typeof window!=='undefined'){window.mixpanel=stub}"
    b"if(typeof module!=='undefined'&&module.exports){module.exports=stub}})();\n"
)
# The above stub handles mixpanel-js loaded as a SEPARATE file — but the same
# library is routinely webpack-bundled straight into a site's own app chunk
# instead (confirmed live on wise.com: byte-identical across 7 zone bundles,
# unmodified vendor code, not Wise-authored glue), where no filename exists to
# intercept. That copy's own `get_config` accessor —
#   MixpanelLib.prototype.get_config=function(prop_name){return this.config[prop_name]}
# — throws the instant ANY tracking call (track, track_pageview, a group
# helper, …) reaches an instance whose async init hasn't set `this.config`
# yet, which mixpanel-js's own snippet-queue pattern makes easy to hit
# (queued calls fire once the real script loads, whether or not init actually
# completes) and a consent-gated init callback that a static mirror's missing
# CMP can never fire makes near-certain. Confirmed the resulting exception is
# caught INSIDE React's commit-phase error boundary, never reaching
# window.onerror/unhandledrejection — RESILIENCE_SHIM above cannot help here,
# and Next.js reacts by cancelling the in-flight render ("Cancel rendering
# route", E503) and mounting its own error fallback in its place, replacing
# real page content with an error screen. `(this.config||{})[prop_name]` is
# the accessor's own upstream fix shape: identical result whenever config IS
# set, `undefined` instead of a throw when it isn't — the same tolerance the
# library will have once its own init finishes, just applied one line early.
MIXPANEL_GET_CONFIG = re.compile(
    r"""\.get_config=function\((\w+)\)\{return\s+this(?:\.config|\[['"]config['"]\])\[\1\]\}""")


def _harden_get_config(m):
    p = m.group(1)
    return f'.get_config=function({p}){{return(this.config||{{}})[{p}]}}'
# Next.js references its own chunk files two ways this file's other patterns
# cannot see, both keyed to "static/chunks/..." — a path relative to the site's
# _next/ root (Next's publicPath/assetPrefix), NOT to whichever file happens to
# be doing the referencing, so a plain urljoin(base, rel) is wrong whenever the
# referencing file sits at a different depth than the chunk itself:
#   1. An async chunk's filename, assembled at runtime from a chunk-id -> hash
#      map compiled into the entry bundle (webpack-*.js / main-*.js) — a long
#      ternary chain, one term per chunk: 85566===e?"static/chunks/"+e+"-c4b4…".
#   2. A route's chunk LIST inside _buildManifest.js — plain quoted strings in
#      an array literal, e.g. "static/chunks/pages/_error-ac146db….js", never
#      inside an import()/from/new URL() call REL_SPEC would catch, and this
#      file sits one directory deeper (_next/static/<buildId>/) than the
#      webpack bundle does, so this and case 1 are NOT the same directory.
# Measured live on wise.com: BOTH gaps stacked on the same homepage — a
# pricing-widget chunk (case 1) and then Next's own error-boundary chunk
# (case 2, needed only once something else already failed) were each missing
# in turn, and each failed dynamic import unmounted the ENTIRE hydrated React
# tree, whiting out a page whose SSR HTML was otherwise fine underneath.
# next_asset_url() anchors on the '_next/' segment itself rather than walking
# a fixed number of '..' — the one thing guaranteed stable across both cases
# and across Next.js layouts, since every chunk path Next emits is relative to
# that root regardless of how deep the file naming it happens to live.
WEBPACK_CHUNK_MAP = re.compile(
    r'(\d+)===(\w+)\?"static/chunks/"\+\2\+"-([0-9a-f]{6,})\.js"')
STATIC_CHUNK_LITERAL = re.compile(r'"(static/chunks/[\w./-]+\.js)"')
REL_PATTERNS = (REL_SPEC, CSS_URL, ATTR_URL)


def next_asset_url(base, rel):
    """rel (e.g. 'static/chunks/x.js') resolved against base's own '_next/'
    root, wherever that root lives — see the block comment above."""
    idx = base.find('_next/')
    if idx == -1:
        return None
    return base[:idx] + '_next/' + rel
SKIP_SCHEMES = ('data:', 'blob:', '#', 'mailto:', 'tel:', 'javascript:', 'http://', 'https://', '//')
IMPORTMAP_RE = re.compile(r'<script[^>]*type=["\']importmap["\'][^>]*>(.*?)</script>', re.S | re.I)
# A mirror always ships SOME live dependency a bundle assumes will succeed —
# an analytics SDK's init call, a feature-flag fetch, a personalization
# service — and a framework whose error handling treats an uncaught client
# exception as fatal (React/Next unmounting the whole hydrated tree, or
# routing to a not-found fallback, both measured live on wise.com from two
# UNRELATED live dependencies in the same session) turns that one dependency
# into a page that never renders at all. This can't fix the dependency — a
# static mirror cannot make a live SDK's init succeed — but it can stop one
# uncaught exception from taking the whole page down with it, which is the
# actual, generalizable failure mode across all of them. Must run before any
# other script on the page, so it is injected as the very first thing in
# <head>, ahead of the framework/vendor bundles it is defending against.
RESILIENCE_SHIM = (
    '<script>(function(){'
    "window.addEventListener('error',function(e){e.stopImmediatePropagation();"
    'return true;},true);'
    "window.addEventListener('unhandledrejection',function(e){e.preventDefault();"
    'e.stopImmediatePropagation();},true);'
    '})();</script>\n'
)


def parse_importmap(html):
    """The page's own <script type="importmap"> imports table, or {} if absent.

    A bare or prefixed specifier ('three', 'three/addons/x.js') is legal only
    through this map. Resolving it with urljoin() against the page's own URL —
    correct for every other relative specifier — instead treats a jsdelivr-
    hosted Three.js addon as a path on the site being mirrored, and the import
    404s the instant the mirror runs standalone with no live origin behind it.
    Seen on ciaoenergy.com: 14 loader/postprocessing imports missed this way,
    breaking the WebGL hero entirely with no console hint beyond a blank canvas.
    """
    m = IMPORTMAP_RE.search(html)
    if not m:
        return {}
    try:
        return json.loads(m.group(1)).get('imports', {})
    except (json.JSONDecodeError, AttributeError):
        return {}


def safe_urljoin(base, spec):
    """urljoin, but a spec pulled out of minified JS by regex is not guaranteed
    to be a URL. A template-literal interpolation like `//${n.value}/x.js`
    matches REL_SPEC's quote-delimited capture (backtick is a legal quote there
    for real dynamic imports), and urljoin's bracket-host parser raises
    ValueError on the stray `${`. One bad match crashing the whole mirror after
    minutes of fetching is worse than silently dropping that one non-URL.
    """
    try:
        return urljoin(base, spec)
    except ValueError:
        return None


def resolve_spec(spec, base, importmap):
    """A specifier's real URL: import map first, else relative to base.

    Exact match, then the longest prefix key ending in '/', per the import-map
    spec's own resolution algorithm — 'three/addons/' must win over a shorter
    prefix if the map ever has both.
    """
    if importmap:
        if spec in importmap:
            return importmap[spec]
        for prefix in sorted((p for p in importmap if p.endswith('/')),
                              key=len, reverse=True):
            if spec.startswith(prefix):
                return importmap[prefix] + spec[len(prefix):]
    return safe_urljoin(base, spec)


def truncate_at_extension(url):
    """Cut a greedily-captured URL at its first valid extension, keeping the query.

    Returns None when nothing that looks like an asset is in it, or when `url`
    is already None from a spec that failed to resolve (see safe_urljoin).
    """
    if url is None:
        return None
    m = EXT_AT.search(url)
    if not m:
        return None
    end = m.end()
    if end < len(url) and url[end] == '?':
        stop = QUERY_STOP.search(url, end)
        end = stop.start() if stop else len(url)
    return url[:end]


def local_name(url, claimed=None):
    """Local filename for an asset URL, unique across the whole mirror.

    Query strings are part of the identity, not noise: srcset candidates like
    `?scale-down-to=512` and `?width=1024` are different images sharing one
    path, so collapsing them collapses every candidate onto one file. Distinct
    query -> distinct file.

    Basenames are not unique either — `/images/hero.png` and `/blog/hero.png`
    are different images with the same name, and one silently overwriting the
    other is a wrong-image bug no screenshot catches. So the plain basename is
    used only while it is unclaimed; the second URL wanting it gets the
    disambiguated form. `claimed` maps name -> url and is updated in place.
    """
    split = urlsplit(url)
    name = os.path.basename(split.path) or 'index'
    stem, ext = os.path.splitext(name)
    tag = hashlib.sha1(url.encode()).hexdigest()[:8]
    if split.query:
        name = f'{stem}__{tag}{ext}'
    if claimed is None:
        return name
    if claimed.get(name, url) != url:
        name = f'{stem}__{tag}{ext}'
    claimed.setdefault(name, url)
    return name


def harvest(text, base, importmap=None):
    """Every asset URL in a blob, absolute and relative, resolved against base."""
    importmap = importmap or {}
    found = set()
    for raw in URL_ANY.findall(text.replace('&amp;', '&')):
        u = truncate_at_extension(raw)
        if u:
            found.add(u)
    for pat in REL_PATTERNS:
        for m in pat.finditer(text):
            rel = m.group(3).strip().replace('&amp;', '&')
            if not rel or rel.startswith(SKIP_SCHEMES[:6]):
                continue
            u = resolve_spec(rel, base, importmap)
            if not u or "${i.value}" in u:
                continue
            u = truncate_at_extension(u)
            if u:
                found.add(u)
    # Both quote styles, matching SRCSET_ATTR above. Double-quote-only here meant
    # a single-quoted srcset was never FETCHED, so the rewriter had nothing to
    # point at and the origin URL survived — the blank-box failure again, with a
    # build log reading `failed: 0`.
    for s in re.findall(r'srcset\s*=\s*(?:"([^"]+)"|\'([^\']+)\')', text, re.I):
        s = s[0] or s[1]
        for cand in s.split(','):
            cand = cand.strip().split()[0] if cand.strip() else ''
            if cand:
                u = truncate_at_extension(safe_urljoin(base, cand.replace('&amp;', '&')))
                if u:
                    found.add(u)
    for chunk_id, _var, chunk_hash in WEBPACK_CHUNK_MAP.findall(text):
        u = next_asset_url(base, f'static/chunks/{chunk_id}-{chunk_hash}.js')
        if u:
            found.add(u)
    for rel in STATIC_CHUNK_LITERAL.findall(text):
        u = next_asset_url(base, rel)
        if u:
            found.add(u)
    return found


def cms_siblings(urls):
    """CMS collections ship as -chunk-/-indexes- pairs and only one name is a
    literal — the sibling is built by runtime substitution, so a scan finds one
    and the loader 404s on the other, rendering the collection empty with no
    error. A derived name that 404s upstream is expected and harmless."""
    out = set()
    for u in urls:
        if '-chunk-' in u:
            out.add(u.replace('-chunk-', '-indexes-'))
        elif '-indexes-' in u:
            out.add(u.replace('-indexes-', '-chunk-'))
    return out - set(urls)


def fetch_safe(url):
    """A URL as it should be REQUESTED, distinct from the URL used as the
    dict key everywhere else in this file.

    A raw space or other unencoded byte in the path — seen live on a CMS that
    names uploads after their alt text, `United States.svg` — makes urlopen
    raise InvalidURL before a single byte is sent, dropping the asset outright.
    Only the path/query get quoted; the original string stays the key used to
    match and rewrite the same URL as it literally appears in the page markup.
    """
    u = urlsplit(url)
    return urlunsplit((u.scheme, u.netloc, quote(u.path, safe="/%"),
                       quote(u.query, safe="=&%"), u.fragment))


def grab(url, name, outdir):
    """Fetch one asset. An HTML error page written to hero.png is an integrity
    problem, not an asset — reject it here rather than discover it in the diff."""
    dest = os.path.join(outdir, name)
    if LIVE_ANALYTICS_SDK.search(urlsplit(url).path):
        with open(dest, 'wb') as f:
            f.write(ANALYTICS_STUB)
        return url, name, None
    try:
        req = Request(fetch_safe(url), headers={'User-Agent': UA, 'Accept': ACCEPT})
        with urlopen(req, timeout=45) as r:
            if r.status != 200:
                return url, None, f'HTTP {r.status}'
            data = r.read()
            ctype = r.headers.get('Content-Type', '')
    except Exception as e:
        return url, None, type(e).__name__
    if not data:
        return url, None, 'empty body'
    head = data[:64].lstrip().lower()
    if not TEXT_EXT.search(urlsplit(url).path) and (
            head.startswith(b'<!doctype') or head.startswith(b'<html')):
        return url, None, 'HTML body for a binary asset (404 page)'
    if 'text/html' in ctype and not urlsplit(url).path.lower().endswith(
            ('.html', '.htm')):
        return url, None, f'content-type {ctype.split(";")[0]} contradicts extension'
    with open(dest, 'wb') as f:
        f.write(data)
    return url, name, None


def link_dir(rel_target, link):
    """Make `link` resolve to `rel_target` (relative to link's parent dir).

    Plain os.symlink is what every other OS wants, but on Windows it raises
    WinError 1314 unless the user has Developer Mode or admin — which is most
    users. Fall back to a junction (needs no privilege, but only takes an
    absolute path) and finally to a real copy, so a study mirror never fails
    to build just because cdn/ couldn't be linked in.
    """
    if os.path.lexists(link):
        return
    try:
        os.symlink(rel_target, link, target_is_directory=True)
        return
    except OSError:
        pass
    abs_target = os.path.abspath(os.path.join(os.path.dirname(link) or '.', rel_target))
    if os.name == 'nt':
        try:
            # mklink's own success message is emitted in the console's active
            # code page, which does not always round-trip through the decoder
            # subprocess picks for text mode — observed as a crash decoding a
            # message never actually needed. Discard stdio; only the exit
            # code (via check=True) determines whether the junction was made.
            subprocess.run(['cmd', '/c', 'mklink', '/J', link, abs_target],
                            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except (OSError, subprocess.CalledProcessError):
            pass
    shutil.copytree(abs_target, link)


def classify_failure(why):
    """Which bucket a fetch failure belongs in.

    A 404 on the reference's own origin is the reference's defect, not the
    mirror's, and references/report.md keeps the two apart so the integrity gate
    is not tripped by a link that was already broken upstream.
    """
    if why.startswith('HTTP '):
        return 'origin_404s'
    if why.startswith('content-type'):
        return 'content_type_mismatches'
    if why.startswith('HTML body') or why == 'empty body':
        return 'integrity_problems'
    return 'network_failures'


def main():
    ap = argparse.ArgumentParser(description='Mirror assets and rewrite crawled pages.')
    ap.add_argument('--origin', default=None,
                    help='site origin; defaults to the manifest, then the first page URL')
    ap.add_argument('--out', default='site', help='directory to write pages into')
    ap.add_argument('--cdn', default='cdn', help='shared asset directory')
    ap.add_argument('--max-rounds', type=int, default=6,
                    help='asset discovery rounds; text assets reference more assets')
    a = ap.parse_args()

    if not os.path.exists('crawl-manifest.json'):
        raise SystemExit(
            'no crawl-manifest.json in this directory.\n'
            'build.py rewrites what crawl.py fetched, so run it from the same place:\n'
            '  python3 crawl.py <url> && python3 build.py')
    man = json.load(open('crawl-manifest.json'))
    pages = man['pages']
    urlmap = {k.rstrip('/'): v for k, v in man['urlmap'].items()}
    origin = a.origin or man.get('origin')
    if not origin and pages:
        s = urlsplit(pages[0]['url'])
        origin = f'{s.scheme}://{s.netloc}'
    if not origin:
        raise SystemExit('no origin: pass --origin')

    missing = [p['slug'] for p in pages if not os.path.exists(f"_raw/{p['slug']}")]
    if missing:
        raise SystemExit(f'crawl-manifest.json lists {len(pages)} pages but _raw/ is '
                         f'missing {len(missing)} of them ({", ".join(missing[:4])}). '
                         f'Re-run crawl.py — a partial _raw/ builds a partial site.')
    raw = {p['slug']: open(f"_raw/{p['slug']}", encoding='utf-8', errors='replace').read()
           for p in pages}
    page_url = {p['slug']: p['url'] for p in pages}

    # ---------- 1. discover assets, following text assets to a fixed point ----------
    os.makedirs(a.cdn, exist_ok=True)
    resolved, failed = {}, {}
    names, claimed = {}, {}      # url -> local name, and name -> first url to claim it
    frontier = set()
    importmaps = {}
    for slug, html in raw.items():
        importmaps[slug] = parse_importmap(html)
        frontier |= harvest(html, page_url[slug], importmaps[slug])
    frontier |= cms_siblings(frontier)

    for rnd in range(a.max_rounds):
        todo = sorted(u for u in frontier if u not in resolved and u not in failed)
        if not todo:
            break
        print(f'round {rnd + 1}: fetching {len(todo)} assets')
        # Names are assigned single-threaded and in sorted order so the mapping
        # is deterministic across runs, then handed to the workers.
        for u in todo:
            names[u] = local_name(u, claimed)
        with ThreadPoolExecutor(max_workers=12) as ex:
            for url, name, err in ex.map(lambda u: grab(u, names[u], a.cdn), todo):
                if name:
                    resolved[url] = name
                else:
                    failed[url] = err
        # text assets build URLs no markup scan can see — re-scan them
        nxt = set()
        for url, name in resolved.items():
            if not TEXT_EXT.search(urlsplit(url).path):
                continue
            path = os.path.join(a.cdn, name)
            try:
                body = open(path, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            nxt |= harvest(body, url)
        nxt |= cms_siblings(nxt)
        frontier |= nxt

    print(f'assets mirrored: {len(resolved)}   failed: {len(failed)}')
    if failed:
        for url, why in sorted(failed.items())[:15]:
            print(f'  MISS  {why:<48} {url}')
        if len(failed) > 15:
            print(f'  ... {len(failed) - 15} more')

    # Assets that failed to mirror still get pointed at a local path. Leaving
    # them absolute would keep the mirror phoning home and break the "0 origin
    # refs" gate; pointed local they 404 in the network log, which is the
    # documented way these get found in the first place.
    table = {**resolved, **{u: names[u] for u in failed}}
    # longest first so one URL is never rewritten through another's prefix
    order = sorted(table, key=len, reverse=True)

    # Every change made to the reference's own markup, counted by class as it
    # happens. The report's integrity gate asks for 0 *unexplained* changes,
    # which is only answerable if the explained ones were tallied at the time.
    changes = {'url-relocalisation': 0, 'sri-strip': 0, 'href-inert': 0,
               'href-wired': 0, 'form-inert': 0, 'stamp': 0, 'tracker-strip': 0,
               'sdk-hardened': 0}

    def rewrite_urls(text, prefix, count=False):
        """Absolute asset URLs -> local path."""
        for url in order:
            if url in text:
                if count:
                    changes['url-relocalisation'] += text.count(url)
                text = text.replace(url, f'{prefix}{table[url]}')
            amp = url.replace('&', '&amp;')
            if amp != url and amp in text:
                if count:
                    changes['url-relocalisation'] += text.count(amp)
                text = text.replace(amp, f'{prefix}{table[url]}')
        return text

    def rewrite_relative(text, base, prefix, count=False, importmap=None):
        """Relative specifiers -> the same local path, resolved against base."""
        importmap = importmap or {}
        def one(m):
            spec = m.group(3).strip()
            if not spec or spec.startswith(SKIP_SCHEMES):
                return m.group(0)
            u = truncate_at_extension(resolve_spec(spec.replace('&amp;', '&'), base, importmap))
            if u and u in table:
                if count:
                    changes['url-relocalisation'] += 1
                return f'{m.group(1)}{m.group(2)}{prefix}{table[u]}{m.group(4)}'
            return m.group(0)
        for pat in REL_PATTERNS:
            text = pat.sub(one, text)

        def srcset_one(m):
            quote, body = m.group(1), m.group(2)
            rewritten = []
            changed = False
            for cand in body.split(','):
                stripped = cand.strip()
                if not stripped:
                    continue
                parts = stripped.split(None, 1)
                spec, descriptor = parts[0], (parts[1] if len(parts) > 1 else '')
                if not spec.startswith(SKIP_SCHEMES):
                    u = truncate_at_extension(safe_urljoin(base, spec.replace('&amp;', '&')))
                    if u and u in table:
                        spec = f'{prefix}{table[u]}'
                        changed = True
                        if count:
                            changes['url-relocalisation'] += 1
                rewritten.append(f'{spec} {descriptor}'.strip())
            if not changed:
                return m.group(0)
            return f'srcset={quote}{", ".join(rewritten)}{quote}'

        return SRCSET_ATTR.sub(srcset_one, text)

    # ---------- 2. rewrite the mirrored text assets ----------
    # Inside module bodies the same string is resolved against the *module* as an
    # import specifier and against the *document* when it becomes a DOM src at
    # runtime. './x' is correct for one and 404s for the other; '/cdn/x' is
    # correct for both.
    for url, name in resolved.items():
        if not TEXT_EXT.search(urlsplit(url).path):
            continue
        path = os.path.join(a.cdn, name)
        try:
            body = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        # A `new URL(rel, base)` base must stay absolute — relativising it throws
        # TypeError, and one uncaught error in a framework bundle takes the whole
        # render down: images and boxes paint while ALL text disappears.
        body = re.sub(r"""(new\s+URL\s*\(\s*[^,]+,\s*)(['"`])https?://[^'"`]+\2""",
                      r'\1location.origin', body)
        body = rewrite_urls(body, f'/{a.cdn}/')
        body = rewrite_relative(body, url, f'/{a.cdn}/')
        body, n8 = MIXPANEL_GET_CONFIG.subn(_harden_get_config, body)
        changes['sdk-hardened'] += n8
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)

    # ---------- 3. rewrite every page ----------
    inert = mapped = 0
    wired_slugs = set()

    def relink(m):
        nonlocal inert, mapped
        pre, href, post = m.group(1), m.group(2), m.group(3)
        if href.startswith('#') or href.startswith(f'{a.cdn}/'):
            return m.group(0)
        joined = safe_urljoin(origin + '/', href)
        slug = urlmap.get(joined.split('#')[0].rstrip('/')) if joined else None
        if slug:
            mapped += 1
            wired_slugs.add(slug)
            return f'{pre}{slug}{post}'
        inert += 1
        # Never bare '#': an anchor component that runs
        # document.querySelector(href) raises SyntaxError on '#', and that throw
        # has stopped a whole component tree rendering. Any valid-but-unmatched
        # selector is equally dead as a link target.
        return f'{pre}#inert{post}'

    os.makedirs(a.out, exist_ok=True)
    host = urlsplit(origin).netloc
    bare_hash = 0
    for slug, html in raw.items():
        # Root-absolute (/cdn/x), not document-relative (cdn/x): this text also
        # contains inline <script type="module"> bodies, and an ES module
        # specifier that isn't "/", "./", "../"-prefixed (or import-mapped) is a
        # hard TypeError that kills the *entire* module before a single line of
        # it runs — Three.js, Lenis, and every canvas along with it. A plain
        # DOM src/href/url() tolerates either form; only /cdn/ works for both,
        # exactly as the asset-level rewrite pass below already does it.
        h = rewrite_urls(html, f'/{a.cdn}/', count=True)
        h = rewrite_relative(h, page_url[slug], f'/{a.cdn}/', count=True,
                              importmap=importmaps[slug])
        # SRI: rewriting a file's bytes means its hash no longer matches, and the
        # browser drops the entire resource with no console error. Symptom is a
        # page rendering in Times with document.fonts.size === 0.
        h, n1 = re.subn(r'\s+(integrity|crossorigin)=(["\'])[^"\']*\2', '', h)
        h, n2 = re.subn(r'\s+(integrity|crossorigin)(?=[\s>])', '', h)
        changes['sri-strip'] += n1 + n2
        # A live off-origin request beat every URL-attribute rewrite above,
        # because it is built by string concatenation at runtime, not present
        # as a literal URL anywhere in the markup a regex can match.
        h, n5 = GTM_INLINE.subn(
            '<!-- tracker-strip: inline Google Tag Manager bootstrap removed '
            '(built its beacon URL by string concatenation, invisible to '
            'attribute-level rewriting) -->', h)
        h, n6 = GTM_NOSCRIPT.subn(
            '<!-- tracker-strip: GTM no-JS iframe fallback removed -->', h)
        h, n7 = MIXPANEL_TOKEN.subn(r'\1\2', h)
        changes['tracker-strip'] += n5 + n6 + n7
        h = re.sub(r'(<a\b[^>]*?href=")([^"]*)(")', relink, h)
        h, n3 = re.subn(r'(<form\b[^>]*?action=")[^"]*(")', r'\1#inert\2', h)
        changes['form-inert'] += n3
        h, n4 = re.subn(r'<head>',
                        f'<head>\n<!-- LOCAL STUDY MIRROR of {host}. Internal links point at\n'
                        '     mirrored pages; everything else is inert. Do not publish. -->\n'
                        + RESILIENCE_SHIM,
                        h, count=1)
        changes['stamp'] += n4
        bare_hash += len(re.findall(r'href="#"', h))
        with open(os.path.join(a.out, slug), 'w', encoding='utf-8') as f:
            f.write(h)
    changes['href-wired'], changes['href-inert'] = mapped, inert

    # Pages are served with --directory site, so cdn/ has to resolve from inside
    # it — both as the relative 'cdn/x' in markup and the root-absolute '/cdn/x'
    # in module bodies. Without this every asset 404s and the mirror looks broken
    # in a way the build log does not show.
    link = os.path.join(a.out, a.cdn)
    link_dir(os.path.relpath(a.cdn, a.out), link)

    # ---------- 4. the build's own evidence ----------
    # report.py consumes this. Counted here rather than reconstructed later,
    # because a number recovered by re-reading the output is a guess about what
    # the build did, not a record of it.
    buckets = {'origin_404s': [], 'content_type_mismatches': [],
               'integrity_problems': [], 'network_failures': []}
    for url, why in sorted(failed.items()):
        buckets[classify_failure(why)].append({'url': url, 'why': why})
    total_bytes = 0
    for name in resolved.values():
        try:
            total_bytes += os.path.getsize(os.path.join(a.cdn, name))
        except OSError:
            pass
    manifest = {
        'origin': origin, 'out': a.out, 'cdn': a.cdn,
        'pages': [{'slug': s, 'url': page_url[s]} for s in sorted(raw)],
        'assets': {
            'mirrored': len(resolved),
            'bytes': total_bytes,
            'problems': len(buckets['integrity_problems']) + len(buckets['network_failures']),
            'origin_404s': buckets['origin_404s'],
            'content_type_mismatches': len(buckets['content_type_mismatches']),
            'failures': {k: v for k, v in buckets.items() if k != 'origin_404s'},
            'analytics_sdk_stubbed': sum(
                1 for u in resolved if LIVE_ANALYTICS_SDK.search(urlsplit(u).path)),
        },
        'links': {'wired': mapped, 'inert': inert,
                  'missing_targets': sorted(wired_slugs - set(raw)),
                  'bare_hash_hrefs': bare_hash},
        'markup_changes': changes,
    }
    # missing_targets is a count in the report schema; the list is kept beside it
    # because "which one" is the only form of that number anybody can act on.
    manifest['links'] = {**manifest['links'],
                         'missing_target_slugs': manifest['links']['missing_targets'],
                         'missing_targets': len(manifest['links']['missing_targets'])}
    with open('build-manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1)

    print(f'pages written: {len(raw)}   internal links wired: {mapped}   made inert: {inert}')
    print(f'cdn files: {len(resolved)}   served from {a.out}/{a.cdn} -> ../{a.cdn}')
    print(f'build-manifest.json written: {total_bytes} bytes of assets, '
          f"{sum(changes.values())} classified markup changes, "
          f"{manifest['links']['missing_targets']} missing link targets")
    if failed:
        print(f'NOTE: {len(failed)} assets did not mirror — listed above. Load the built '
              f'site and read the network log before concluding a region failed.')


if __name__ == '__main__':
    main()
