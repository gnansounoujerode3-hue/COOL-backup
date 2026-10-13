#!/usr/bin/env python3
"""End-to-end test of swipefile scripts/build.py against a synthetic origin."""
import re
import json, os, shutil, socket, subprocess, sys, tempfile, threading, time
import pathlib as _pl
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs, unquote

BUILD = os.path.join(SCRIPTS, 'build.py')
SERVE = os.path.join(SCRIPTS, 'serve.py')

# ---------------- synthetic origin ----------------
class Origin(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        # A real origin decodes the request line's percent-encoding before
        # routing to a file — matching the raw path here would silently 404
        # every request build.py correctly encoded via fetch_safe().
        u = urlsplit(unquote(self.path)); q = parse_qs(u.query)
        accept = self.headers.get('Accept', '')

        def send(body, ctype='application/octet-stream', status=200, vary=False):
            self.send_response(status)
            self.send_header('Content-Type', ctype)
            if vary: self.send_header('Vary', 'Accept')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers(); self.wfile.write(body)

        if u.path == '/hero.png':
            # vary: Accept — AVIF bytes to a browser-ish Accept, PNG otherwise
            fmt = b'AVIF' if 'image/avif' in accept else b'PNG-'
            w = (q.get('width') or ['0'])[0]
            return send(fmt + f'-w{w}'.encode(), 'image/avif' if b'AVIF' in fmt else 'image/png', vary=True)
        if u.path == '/app.mjs':
            return send((f"import('./chunk.mjs');\n"
                         f"const b = new URL('rel/x', '{ORIGIN}/base/');\n").encode(),
                        'text/javascript')
        if u.path == '/chunk.mjs':
            # A template-literal interpolation sitting right next to a real
            # import — the shape that crashed build.py on a live minified
            # bundle: `${n.value}` matches REL_SPEC's backtick-quoted capture
            # (a legal quote character for real dynamic imports) but is not a
            # URL, and urljoin's bracket-host parser raised ValueError on it,
            # taking the whole mirror down mid-crawl.
            return send((f"import(`//${{n.value}}/x.js`);\n"
                        f"const img = '{ORIGIN}/deep.png';\n").encode(), 'text/javascript')
        if u.path == '/deep.png':
            return send(b'DEEPPNG', 'image/png')
        if u.path == '/_next/static/chunks/webpack-abc123.js':
            # Next's webpack chunk map: a ternary chain, one term per async
            # chunk, giving chunk-id -> hash with no static URL anywhere for
            # a markup/import scan to find. The referenced chunk lives at the
            # site's _next/ root + the literal path, NOT at any fixed offset
            # from this file — same directory here, but a DIFFERENT directory
            # for the buildManifest case just below, which is the point.
            return send(b'99887===e?"static/chunks/"+e+"-deadbeef01.js":0', 'text/javascript')
        if u.path == '/_next/static/chunks/99887-deadbeef01.js':
            return send(b'export const y=3;\n', 'text/javascript')
        if u.path == '/_next/static/BUILDID123/_buildManifest.js':
            # Next's pages-router route->chunks map: plain quoted strings in
            # an array literal, never inside import()/from/new URL() — and
            # this file sits ONE DIRECTORY DEEPER than static/chunks/ itself,
            # so a same-directory join (correct for webpack.js above) resolves
            # to the wrong URL here; only anchoring on '_next/' gets both right.
            return send(b'self.__BUILD_MANIFEST={"/_error":'
                        b'["static/chunks/pages/_error-abc999.js"]}', 'text/javascript')
        if u.path == '/_next/static/chunks/pages/_error-abc999.js':
            return send(b'export const z=4;\n', 'text/javascript')
        if u.path == '/vendor/zone-bundle.js':
            # Mixpanel-js bundled INLINE into a site's own app chunk (not
            # loaded as a separate file) — confirmed live on wise.com,
            # byte-identical stock library code across 7 zone bundles. Its
            # own get_config accessor throws when a tracking call reaches an
            # instance before async init sets `this.config`, which crashed
            # the whole page: React's commit-phase boundary catches it (never
            # reaching window.onerror, so RESILIENCE_SHIM cannot help), and
            # Next.js cancels the render and mounts its error fallback in
            # place of real content. Two minified variable-naming shapes,
            # both seen on the real site, must both be hardened.
            return send(
                b"cZ.prototype.get_config=function(e){return this.config[e]};"
                b"MixpanelLib.prototype.get_config=function(prop_name){"
                b"return this.config[prop_name]};"
                b"export const untouched=function(x){return this.other[x]};",
                'text/javascript')
        if u.path == '/libs/mixpanel-2-latest.min.js':
            # The real SDK: a live init sequence a static mirror can never
            # satisfy. Fetching this for real (and this handler answering it)
            # would defeat the point of the test — the fix must intercept the
            # request before it happens, per LIVE_ANALYTICS_SDK in build.py.
            return send(b'REAL MIXPANEL SDK -- MUST NEVER SHIP IN A MIRROR',
                        'text/javascript')
        if u.path == '/data-chunk-abc.json':
            return send(b'{"chunk":1}', 'application/json')
        if u.path == '/data-indexes-abc.json':
            return send(b'{"indexes":1}', 'application/json')
        if u.path == '/broken.png':
            # 200 with an HTML error body — the classic silent integrity failure
            return send(b'<!doctype html><html><body>404</body></html>', 'text/html')
        if u.path == '/theme.css':
            return send(b'@font-face{src:url(fonts/face.woff2)}', 'text/css')
        if u.path == '/fonts/face.woff2':
            return send(b'WOFF2BYTES', 'font/woff2')
        if u.path == '/v/home/images/photo_small.png':
            return send(b'PHOTOSMALL', 'image/png')
        if u.path == '/v/home/images/photo_small_2x.png':
            return send(b'PHOTOSMALL2X', 'image/png')
        if u.path == '/v/home/images/photo_large.jpg':
            return send(b'PHOTOLARGE', 'image/jpeg')
        if u.path == '/v/home/images/single.png':
            return send(b'SINGLEQUOTED', 'image/png')
        if u.path == '/v/home/images/single_2x.png':
            return send(b'SINGLEQUOTED2X', 'image/png')
        # A CMS that names uploads after their alt text ships a raw space in
        # the URL. urlopen raised InvalidURL on this before any request went
        # out, dropping the asset with no retry possible.
        if u.path == '/imaginary-v2/images/abc-United States.svg':
            return send(b'<svg/>', 'image/svg+xml')
        self.send_error(404)

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

PORT = free_port()
ORIGIN = f'http://127.0.0.1:{PORT}'
srv = ThreadingHTTPServer(('127.0.0.1', PORT), Origin)
threading.Thread(target=srv.serve_forever, daemon=True).start()

# ---------------- fixture crawl output ----------------
work = tempfile.mkdtemp(prefix='build-test-')
os.makedirs(f'{work}/_raw')
PAGE = f'''<!doctype html><html><head>
<link rel="stylesheet" href="{ORIGIN}/theme.css" integrity="sha384-DEADBEEF" crossorigin="anonymous">
<script src="{ORIGIN}/app.mjs" type="module" integrity="sha384-CAFE"></script>
<script src="{ORIGIN}/_next/static/chunks/webpack-abc123.js"></script>
<script src="{ORIGIN}/_next/static/BUILDID123/_buildManifest.js"></script>
<script src="{ORIGIN}/libs/mixpanel-2-latest.min.js"></script>
<script src="{ORIGIN}/vendor/zone-bundle.js"></script>
<style>:root{{--bg:url({ORIGIN}/hero.png?width=1024);--next-prop:red}}</style>
</head><body>
<img src="{ORIGIN}/hero.png?width=512" srcset="{ORIGIN}/hero.png?width=512 512w, {ORIGIN}/hero.png?width=1024 1024w">
<img src="{ORIGIN}/broken.png">
<picture>
  <source srcset="/v/home/images/photo_small.png, /v/home/images/photo_small_2x.png 2x" media="(max-width:734px)">
  <img src="/v/home/images/photo_large.jpg" alt="students">
</picture>
<picture>
  <source srcset='/v/home/images/single.png, /v/home/images/single_2x.png 2x' media="(max-width:500px)">
  <img src="/v/home/images/photo_large.jpg" alt="single-quoted">
</picture>
<img src="{ORIGIN}/imaginary-v2/images/abc-United States.svg" alt="unencoded space">
<script type="text/javascript">window.dataLayer = window.dataLayer || [];
(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://sst.example.com/wisetag?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','GTM-TEST123');</script>
<noscript><iframe title="gtm-iframe" src="https://sst.example.com/ns.html?id=GTM-TEST123" height="0" width="0" style="display:none"></iframe></noscript>
<script id="__NEXT_DATA__" type="application/json">{{"runtimeConfig":{{"mixpanel":{{"record_sessions_percent":1,"token":"e605c449bdf99389fa3ba674d4f5d919"}},"APP_TOKEN":"dad99d7d8e52c2c8aaf9fda788d8acdc"}}}}</script>
<a href="/about">About</a>
<a href="https://elsewhere.example/x">Off-site</a>
<form action="/subscribe"></form>
<script>fetch("{ORIGIN}/data-chunk-abc.json")</script>
</body></html>'''
open(f'{work}/_raw/index.html', 'w').write(PAGE)
open(f'{work}/_raw/about.html', 'w').write('<!doctype html><html><head></head><body>about</body></html>')
json.dump({
    'origin': ORIGIN,
    'pages': [{'url': f'{ORIGIN}/', 'slug': 'index.html', 'depth': 0},
              {'url': f'{ORIGIN}/about', 'slug': 'about.html', 'depth': 1}],
    'urlmap': {f'{ORIGIN}': 'index.html', f'{ORIGIN}/about': 'about.html'},
    'skipped': {},
}, open(f'{work}/crawl-manifest.json', 'w'))

r = subprocess.run([sys.executable, BUILD], cwd=work, capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr); sys.exit('build.py failed')

PASS, FAIL = [], []
def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}{"  — " + detail if detail and not cond else ""}')

def is_link_like(path):
    """True for a real symlink or, on Windows, the junction build.py's
    link_dir() falls back to when the process lacks symlink privilege
    (the common case without Developer Mode/admin). os.path.islink() alone
    misses junctions — they're a different reparse-point type — so a strict
    islink check here would fail on exactly the environment this fallback
    exists for."""
    if os.path.islink(path):
        return True
    if os.name == 'nt':
        import stat as _stat
        try:
            attrs = os.stat(path, follow_symlinks=False).st_file_attributes
            return bool(attrs & _stat.FILE_ATTRIBUTE_REPARSE_POINT)
        except (OSError, AttributeError):
            return False
    return False

cdn = os.listdir(f'{work}/cdn')
page = open(f'{work}/site/index.html').read()

check('site/cdn is linked, not copied', is_link_like(f'{work}/site/cdn'))
check('site/cdn resolves to the asset dir',
      os.path.isdir(os.path.realpath(f'{work}/site/cdn')))

hero = [f for f in cdn if f.startswith('hero')]
check('query strings kept as distinct assets (2 hero files)', len(hero) == 2, str(hero))
check('hero fetched with browser Accept (AVIF, not PNG)',
      any(open(f'{work}/cdn/{f}', "rb").read().startswith(b'AVIF') for f in hero),
      str([open(f'{work}/cdn/{f}','rb').read() for f in hero]))

check('integrity= stripped from markup', 'integrity=' not in page)
check('crossorigin= stripped from markup', 'crossorigin=' not in page)
check('unmirrored link is #inert, never bare #', 'href="#inert"' in page)
check('no bare href="#" remains', 'href="#"' not in page)
check('form action neutralised to #inert', 'action="#inert"' in page)
check('internal link wired to local slug', 'href="about.html"' in page)
check('no absolute origin refs left in the page', ORIGIN not in page)
check('do-not-publish stamp carries the real host',
      '127.0.0.1' in page and 'framer.com' not in page)

# root-relative <source srcset> — the Apple.com bug: harvested for fetching but
# never rewritten, so a <picture> whose <source> matches renders a blank box
# (browsers do not fall back to <img> when a matching <source> just 404s).
check('root-relative srcset assets were fetched',
      any(f.startswith('photo_small') for f in cdn), str(cdn))
check('<source srcset> rewritten off the origin path',
      '/v/home/images/' not in page, page[page.find('<source'):page.find('<source')+200])
check('srcset descriptor (2x) preserved after rewrite',
      re.search(r'srcset="[^"]*cdn/photo_small_2x[^"]*2x', page) is not None, page)
# Root-absolute by design. build.py rewrites to `/<cdn>/` so a page at any crawl
# depth resolves through the served site root — that was the fix for the
# `/../site/cdn/` bug that 404'd every asset on a real build. This assertion
# pinned the old relative form and went stale behind it. What matters is that
# the <picture> fallback points at the local asset instead of the origin path,
# because an unrewritten fallback is what a blank <picture> box is made of.
check('fallback <img src> for the picture also rewritten',
      re.search(r'<img src="/?cdn/photo_large\.jpg"', page) is not None, page)

# The harvester was double-quote-only while SRCSET_ATTR accepted both, so a
# single-quoted srcset was never FETCHED — the rewriter then had nothing local to
# point at and the origin URL survived, with the build log reading `failed: 0`.
check('single-quoted srcset candidates are fetched',
      any(f.startswith('single') for f in cdn), str(cdn))
check('single-quoted srcset is rewritten off the origin',
      '/v/home/images/single.png' not in page and 'cdn/single' in page,
      page[page.find('single'):page.find('single') + 200])
check('its 2x descriptor survives the rewrite',
      re.search(r"srcset=['\"][^'\"]*cdn/single_2x[^'\"]*2x", page) is not None, page)

check('css url() truncated at extension, not swallowed by --next-prop',
      any(f.startswith('theme') for f in cdn) and '--next-prop:red' in page)
check('relative url() inside the stylesheet followed (face.woff2)',
      any(f.startswith('face') for f in cdn), str(cdn))

mjs = [f for f in cdn if f.startswith('app')]
body = open(f'{work}/cdn/{mjs[0]}').read() if mjs else ''
check('module body rewritten root-absolute (/cdn/…)', '/cdn/' in body, body)
check('new URL() base kept absolute via location.origin',
      'location.origin' in body and 'ORIGIN/base' not in body, body)
check('relative dynamic import followed to chunk.mjs',
      any(f.startswith('chunk') for f in cdn), str(cdn))
check('fixed-point: asset referenced only inside chunk.mjs was mirrored',
      any(f.startswith('deep') for f in cdn), str(cdn))
# The check above already proves it implicitly (build.py would have crashed
# and this whole test file would have aborted at the subprocess.run() call
# above before reaching here), but name the regression explicitly: a
# template-literal interpolation sitting right next to that real import must
# not take the harvest pass down with it.
check('a malformed template-literal spec next to a real import does not '
      'crash the build — the build ran to completion at all', True)
check('a webpack chunk named only inside a runtime chunk-id map was mirrored',
      any(f.startswith('99887-deadbeef01') for f in cdn), str(cdn))
check('a chunk named only inside _buildManifest.js, one directory deeper '
      'than the chunk itself, still resolves to the right URL',
      any(f.startswith('_error-abc999') for f in cdn), str(cdn))

mp = [f for f in cdn if f.startswith('mixpanel-2-latest')]
check('the resilience shim is the first thing in <head>, before any '
      'framework/vendor bundle it defends against',
      re.search(r'<head>\s*<!--.*?-->\s*<script>', page, re.S) is not None, page[:400])
check('the shim suppresses uncaught errors so one live-dependency crash '
      "can't unmount the whole hydrated page",
      "addEventListener('error'" in page and 'stopImmediatePropagation' in page, page[:400])
check('the shim also suppresses unhandled promise rejections',
      "addEventListener('unhandledrejection'" in page, page[:400])

check('the mixpanel SDK is mirrored as a real cdn/ file, not left off-origin',
      bool(mp), str(cdn))
mp_body = open(f'{work}/cdn/{mp[0]}', 'rb').read() if mp else b''
check("the SDK's real code is stubbed out, never shipped in the mirror",
      b'REAL MIXPANEL SDK' not in mp_body, mp_body[:80])
check('the stub still defines window.mixpanel so app code calling it does '
      'not throw on undefined', b'window.mixpanel' in mp_body, mp_body)

vendor = [f for f in cdn if f.startswith('zone-bundle')]
vendor_body = open(f'{work}/cdn/{vendor[0]}').read() if vendor else ''
check('a bundled (not stubbed-out-able) get_config accessor is hardened '
      "against this.config being undefined, minified param name 'e'",
      'cZ.prototype.get_config=function(e){return(this.config||{})[e]}'
      in vendor_body, vendor_body)
check('...and the differently-named param shape, unminified-ish',
      'MixpanelLib.prototype.get_config=function(prop_name)'
      '{return(this.config||{})[prop_name]}' in vendor_body, vendor_body)
check('an unrelated same-shaped accessor on a DIFFERENT property is left '
      'alone — the patch matches get_config specifically, not any accessor',
      'return this.other[x]' in vendor_body, vendor_body)
check('CMS -chunk-/-indexes- sibling derived',
      any('indexes' in f for f in cdn), str(cdn))
check('HTML body served as .png was rejected, not written',
      not any(f.startswith('broken') for f in cdn), str(cdn))
check('a URL with a raw unencoded space is fetched, not dropped',
      any(f.startswith('abc-United') for f in cdn), str(cdn))

# A tag manager builds its beacon URL by string concatenation at RUNTIME, so it
# is a literal URL nowhere in the markup — invisible to every attribute/url()
# rewrite above, and the one live off-origin request that survived a mirror
# with 0 static origin refs and 0 asset failures.
check('inline GTM bootstrap script is stripped, not left live',
      'GTM-TEST123' not in page and 'sst.example.com' not in page, page)
check('the no-JS iframe fallback for the same tag is also stripped',
      'gtm-iframe' not in page, page)
check('a bundled analytics SDK token is neutered so it cannot beacon out',
      'e605c449bdf99389fa3ba674d4f5d919' not in page, page)
check('an unrelated token in the same JSON blob is left alone',
      'dad99d7d8e52c2c8aaf9fda788d8acdc' in page, page)
mixpanel_obj = re.search(r'"mixpanel":\{[^}]*\}', page)
check('the JSON blob is still syntactically valid after the strip',
      mixpanel_obj and json.loads('{' + mixpanel_obj.group(0) + '}'), page)
check('an unrelated tag immediately after the GTM script is untouched',
      'href="about.html"' in page, page)

# ---------------- a bare invocation in the wrong directory ----------------
# build.py's docstring documents `python3 build.py` with no arguments, so a
# zero-argument run looks supported; it used to raise FileNotFoundError with a
# full stack trace. Every sibling entry point exits cleanly with guidance.
bare = tempfile.mkdtemp(prefix='build-bare-')
rb = subprocess.run([sys.executable, BUILD], cwd=bare, capture_output=True, text=True)
check('a bare run with no crawl-manifest.json does not traceback',
      'Traceback' not in rb.stderr, rb.stderr[-300:])
check('it names the file it wanted and the command that produces it',
      'crawl-manifest.json' in rb.stderr and 'crawl.py' in rb.stderr, rb.stderr[-300:])
shutil.rmtree(bare, ignore_errors=True)

# ---------------- the build's own evidence, for report.py ----------------
# Counted during the rewrite rather than reconstructed afterwards: a number
# recovered by re-reading the output is a guess about what the build did.
man = json.load(open(f'{work}/build-manifest.json'))
check('build-manifest.json written', bool(man))
check('every integrity/crossorigin attribute counted as an sri-strip',
      man['markup_changes']['sri-strip'] == 3, man['markup_changes'])
check('wired and inert links counted separately',
      man['links']['wired'] == 1 and man['links']['inert'] == 1, man['links'])
check('form neutering counted', man['markup_changes']['form-inert'] == 1)
check('the do-not-publish stamp counted once per page',
      man['markup_changes']['stamp'] == 2, man['markup_changes'])
check('url relocalisation counted', man['markup_changes']['url-relocalisation'] > 0)
check('the tracker strip (GTM script + noscript iframe + SDK token) is '
      'classified, not silent',
      man['markup_changes']['tracker-strip'] == 3, man['markup_changes'])
check('both bundled get_config accessor shapes counted as hardened, not silent',
      man['markup_changes']['sdk-hardened'] == 2, man['markup_changes'])
check('0 missing link targets on a mirror whose links all resolve',
      man['links']['missing_targets'] == 0, man['links'])
check('0 bare # hrefs recorded', man['links']['bare_hash_hrefs'] == 0)
check('asset count and bytes recorded',
      man['assets']['mirrored'] == len(cdn) and man['assets']['bytes'] > 0,
      (man['assets']['mirrored'], len(cdn), man['assets']['bytes']))
check('an HTML body served as .png is an integrity problem, not an origin 404',
      man['assets']['problems'] >= 1 and not man['assets']['origin_404s'],
      man['assets'])

# The contract between the two scripts, checked against a real build rather than
# a fixture — test_report.py hand-writes this manifest, so both suites could stay
# green while the shape they agree on drifts apart.
subprocess.run([sys.executable, os.path.join(SCRIPTS, 'report.py'), '--init'],
               cwd=work, capture_output=True, text=True)
rr = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'report.py'),
                     '--site', 'example.com', '--crawl', 'crawl-manifest.json',
                     '--build', 'build-manifest.json', '--measured', 'measurements.json'],
                    cwd=work, capture_output=True, text=True)
links_line = next((l for l in rr.stdout.splitlines() if 'links:' in l), '')
assets_line = next((l for l in rr.stdout.splitlines() if 'content-type' in l), '')
check('report.py consumes the manifest build.py actually writes',
      links_line.strip().startswith('ok'), rr.stdout + rr.stderr)
check('link counts reach the report as measured values, not "not measured"',
      '0 missing, 0 bare #' in links_line, links_line)
check("the build's own content-type tally reaches the report",
      'not measured — no build manifest' not in assets_line, assets_line)

# ---------------- the mirror actually serves ----------------
sp = free_port()
p = subprocess.Popen([sys.executable, SERVE, '--directory', 'site', '--port', str(sp)],
                     cwd=work, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    import urllib.request, urllib.error
    end = time.time() + 10
    while time.time() < end:
        try: socket.create_connection(('127.0.0.1', sp), 0.2).close(); break
        except OSError: time.sleep(0.05)
    ok = True
    for f in hero + [x for x in cdn if x.startswith('app')]:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{sp}/cdn/{f}', timeout=5) as r:
                ok &= r.status == 200
        except Exception as e:
            ok = False; print('   asset 404:', f, e)
    check('every asset resolves through the served site root', ok)
finally:
    p.terminate(); p.wait(timeout=5)

srv.shutdown()
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
shutil.rmtree(work, ignore_errors=True)
if FAIL: print('FAILED:', ', '.join(FAIL)); sys.exit(1)
