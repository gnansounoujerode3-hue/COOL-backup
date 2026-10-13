#!/usr/bin/env python3
"""
Multi-page mirror crawler.

Seeds from a start URL, follows same-origin links breadth-first, mirrors each
page plus its assets, and rewrites internal links so the copy is navigable
offline. Stops at the boundaries that actually matter: robots.txt rules, auth
walls, bulk user-generated sections, and hard page/depth caps.

Pages are written flat as <slug>.html so every page can reference shared assets
at cdn/ with no relative-depth arithmetic.

Usage:
  python3 crawl.py https://www.framer.com/ --max-pages 30 --max-depth 2
"""
import argparse, os, re, sys, time, json
from collections import deque
from urllib.parse import urljoin, urlparse, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/150.0 Safari/537.36")

# Pages behind a login are not mirrorable and not ours to mirror. Detected two
# ways: by path, and by what the server does (401/403, or a redirect to a
# login-ish URL).
#
# `projects/` is deliberately NOT here. It reads as an account area on an app
# dashboard and as the portfolio on a studio site, and the path guess dropped 5
# real case studies as "auth-gated" on a measured run. The behavioural
# detectors below (401/403, login redirect) catch the real thing without
# guessing, so let them.
AUTH_PAT = re.compile(
    r'/(login|signin|sign-in|signup|sign-up|register|account|dashboard|'
    r'settings|billing|checkout|logout|auth|oauth|admin)\b', re.I)

# Bulk user-generated or reference sections: thousands of pages, not the design
# surface anyone means by "the site". Skipped by default; --include re-admits a
# section, --exclude adds one, both repeatable and matched against the path.
BULK_PAT = re.compile(r'^/(community|dictionary|help|docs|developers|marketplace|'
                      r'blog|news|tag|tags|category|categories|author|authors|'
                      r'glossary|forum|support|kb)(/|$)', re.I)

# robots.txt Disallow rules for this run, filled at startup.
ROBOTS = []

BINARY_EXT = re.compile(r'\.(zip|dmg|exe|pkg|pdf|mp4|webm|mov|woff2?|ttf|otf|'
                        r'png|jpe?g|gif|svg|webp|avif|ico|mjs|js|css|json|xml)$', re.I)


def fetch(url, timeout=45):
    req = Request(url, headers={'User-Agent': UA})
    with urlopen(req, timeout=timeout) as r:
        return r.read(), r.geturl(), r.status, r.headers.get('Content-Type', '')


def load_robots(origin):
    """Only the Disallow lines for User-Agent: * — enough for a polite crawl."""
    try:
        body, _, _, _ = fetch(urljoin(origin, '/robots.txt'))
    except Exception:
        return []
    rules, applies = [], False
    for line in body.decode('utf-8', 'replace').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        k, _, v = line.partition(':')
        k, v = k.strip().lower(), v.strip()
        if k == 'user-agent':
            applies = (v == '*')
        elif k == 'disallow' and applies and v:
            rules.append(v)
    return rules


def robots_blocked(path_q):
    for rule in ROBOTS:
        # Only wildcard semantics real sites rely on: * anywhere, prefix match.
        pat = re.escape(rule).replace(r'\*', '.*')
        if re.match(pat, path_q):
            return True
    return False


def slug_for(url, origin):
    """/solutions/designers -> solutions__designers.html ; root -> index.html"""
    p = urlsplit(url).path.strip('/')
    if not p:
        return 'index.html'
    s = re.sub(r'[^a-zA-Z0-9._-]+', '-', p.replace('/', '__')).strip('-')
    return (s[:120] or 'page') + '.html'


def load_sitemap(origin, url=None):
    """Sitemap URLs, for set-differencing against what the crawl actually reached.

    Link-following is not complete: paginated indexes and JS-built listings hide
    entries from it, so a page count alone is not evidence of coverage.
    """
    out = set()
    try:
        body, _, _, _ = fetch(url or urljoin(origin, '/sitemap.xml'))
    except Exception:
        return out
    text = body.decode('utf-8', 'replace')
    for loc in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', text):
        if loc.endswith('.xml'):          # sitemap index — one level down
            try:
                sub, _, _, _ = fetch(loc)
                out |= {m for m in re.findall(
                    r'<loc>\s*([^<\s]+)\s*</loc>', sub.decode('utf-8', 'replace'))
                    if not m.endswith('.xml')}
            except Exception:
                continue
        else:
            out.add(loc)
    return out


def should_follow(url, origin, include_pats, exclude_pats):
    u = urlsplit(url)
    if u.scheme not in ('http', 'https'):
        return False, 'scheme'
    if f'{u.scheme}://{u.netloc}' != origin:
        return False, 'offsite'
    if BINARY_EXT.search(u.path):
        return False, 'binary'
    if AUTH_PAT.search(u.path):
        return False, 'auth-gated'
    if any(p.search(u.path) for p in include_pats):
        pass                              # explicitly re-admitted
    elif any(p.search(u.path) for p in exclude_pats) or BULK_PAT.search(u.path):
        return False, 'bulk-section'
    pq = u.path + (('?' + u.query) if u.query else '')
    if robots_blocked(pq):
        return False, 'robots'
    return True, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('start')
    ap.add_argument('--out', default='.')
    ap.add_argument('--max-pages', type=int, default=30)
    ap.add_argument('--max-depth', type=int, default=2)
    ap.add_argument('--delay', type=float, default=0.4, help='politeness delay, seconds')
    ap.add_argument('--include-bulk', action='store_true',
                    help='re-admit every default bulk section')
    ap.add_argument('--include', action='append', default=[], metavar='PATTERN',
                    help='re-admit paths matching this regex (repeatable)')
    ap.add_argument('--exclude', action='append', default=[], metavar='PATTERN',
                    help='skip paths matching this regex (repeatable)')
    ap.add_argument('--sitemap', default=None,
                    help='sitemap URL for the coverage set-difference '
                         '(default <origin>/sitemap.xml; --sitemap "" to skip)')
    a = ap.parse_args()

    include_pats = [re.compile(p, re.I) for p in a.include]
    exclude_pats = [re.compile(p, re.I) for p in a.exclude]
    if a.include_bulk:
        include_pats.append(re.compile(r'.', re.I))

    origin = '{0.scheme}://{0.netloc}'.format(urlsplit(a.start))
    global ROBOTS
    ROBOTS = load_robots(origin)
    print(f'robots: {len(ROBOTS)} disallow rules')

    sitemap = set() if a.sitemap == '' else load_sitemap(origin, a.sitemap or None)
    if sitemap:
        print(f'sitemap: {len(sitemap)} URLs')

    os.makedirs(a.out, exist_ok=True)
    seen, queued = {}, set()
    skipped = {}
    q = deque([(a.start, 0)])
    queued.add(a.start.rstrip('/'))
    pages = []

    # Seed from the sitemap too: link-following alone misses anything behind a
    # paginated index, and those are real pages, not bulk.
    for loc in sorted(sitemap):
        key = loc.rstrip('/')
        if key in queued:
            continue
        ok, why = should_follow(loc, origin, include_pats, exclude_pats)
        if not ok:
            skipped.setdefault(loc, f'{why} (sitemap)')
            continue
        queued.add(key)
        q.append((loc, 1))

    while q and len(pages) < a.max_pages:
        url, depth = q.popleft()
        try:
            body, final, status, ctype = fetch(url)
        except HTTPError as e:
            # 401/403 is the server telling us this needs an account.
            skipped[url] = f'HTTP {e.code}' + (' (auth)' if e.code in (401, 403) else '')
            continue
        except (URLError, Exception) as e:
            skipped[url] = f'error {type(e).__name__}'
            continue

        if 'text/html' not in ctype:
            skipped[url] = f'not html ({ctype.split(";")[0]})'
            continue
        # a redirect into a login page is an auth wall by another name
        if AUTH_PAT.search(urlsplit(final).path):
            skipped[url] = 'redirected to auth'
            continue

        html = body.decode('utf-8', 'replace')
        slug = slug_for(final, origin)
        seen[final.rstrip('/')] = slug
        seen[url.rstrip('/')] = slug
        pages.append({'url': final, 'slug': slug, 'depth': depth, 'html': html})
        print(f'  [{len(pages):>3}] d{depth} {slug:<44} {len(html)//1024:>5}KB  {final}')

        if depth < a.max_depth:
            for m in re.finditer(r'<a\b[^>]*?href="([^"#][^"]*)"', html):
                nxt = urljoin(final, m.group(1)).split('#')[0]
                key = nxt.rstrip('/')
                if key in queued:
                    continue
                ok, why = should_follow(nxt, origin, include_pats, exclude_pats)
                if not ok:
                    skipped.setdefault(nxt, why)
                    continue
                queued.add(key)
                q.append((nxt, depth + 1))
        time.sleep(a.delay)

    # Two silent loss channels, both recorded rather than left to be inferred
    # from a page count: the cap, and anything the sitemap lists that we never
    # reached. A crawler can drop real pages and still look like it finished.
    for url, _ in q:
        skipped.setdefault(url, 'max-pages cap')
    reached = {u.rstrip('/') for u in seen}
    sitemap_only = sorted(u for u in sitemap if u.rstrip('/') not in reached)
    crawl_only = sorted(p['url'] for p in pages
                        if sitemap and p['url'].rstrip('/') not in
                        {s.rstrip('/') for s in sitemap})

    json.dump({'origin': origin,
               'pages': [{k: v for k, v in p.items() if k != 'html'} for p in pages],
               'skipped': skipped, 'urlmap': seen,
               'sitemap_only': sitemap_only, 'crawl_only': crawl_only},
              open(os.path.join(a.out, 'crawl-manifest.json'), 'w', encoding='utf-8'), indent=1)

    # write raw html for the rewrite pass. encoding='utf-8' is not optional here:
    # this is a live page's actual bytes, and the crawl exists to run against
    # real sites — the moment one uses a curly quote, an accented letter, or an
    # arrow, a bare open(..., 'w') on Windows falls back to cp1252 and throws.
    os.makedirs(os.path.join(a.out, '_raw'), exist_ok=True)
    for p in pages:
        open(os.path.join(a.out, '_raw', p['slug']), 'w', encoding='utf-8').write(p['html'])

    reasons = {}
    for why in skipped.values():
        reasons[why] = reasons.get(why, 0) + 1
    print(f'\nmirrored {len(pages)} pages')
    print('skipped by reason:')
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f'  {v:5}  {k}')
    if sitemap:
        print(f'\ncoverage vs sitemap: {len(sitemap_only)} listed but not crawled, '
              f'{len(crawl_only)} crawled but not listed')
        for u in sitemap_only[:10]:
            print(f'  MISSED  {u}  ({skipped.get(u, "never queued")})')
        if len(sitemap_only) > 10:
            print(f'  ... {len(sitemap_only) - 10} more')
        print('Read the skip reasons before trusting this page count.')


if __name__ == '__main__':
    main()
