#!/usr/bin/env python3
"""End-to-end test of swipefile scripts/crawl.py against a synthetic site."""
import json, os, shutil, socket, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import os, pathlib as _pl
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)

CRAWL = os.path.join(SCRIPTS, 'crawl.py')

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

PORT = free_port(); ORIGIN = f'http://127.0.0.1:{PORT}'

# / links to /about and /projects/case-one (portfolio, NOT an auth wall)
# /articles is a paginated index: page 2 holds /articles/hidden, unreachable by
# link-following from page 1 — only the sitemap knows about it.
PAGES = {
    '/': '<a href="/about">a</a><a href="/projects/case-one">p</a>'
         '<a href="/articles">idx</a><a href="/dashboard">acct</a>'
         '<a href="/portal/secret">portal</a>',
    '/about': 'about',
    '/projects/case-one': 'case study one',
    '/articles': '<a href="/articles/visible">v</a>',   # page 2 not linked
    '/articles/visible': 'visible article',
    '/articles/hidden': 'hidden article',
}
SITEMAP = ('<?xml version="1.0"?><urlset>' + ''.join(
    f'<loc>{ORIGIN}{p}</loc>' for p in
    ['/', '/about', '/projects/case-one', '/articles/visible', '/articles/hidden',
     '/never-reachable']) + '</urlset>')

class Site(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = urlsplit(self.path).path
        if p == '/robots.txt':
            return self.reply(b'User-agent: *\nDisallow: /private\n', 'text/plain')
        if p == '/sitemap.xml':
            return self.reply(SITEMAP.encode(), 'application/xml')
        if p in ('/dashboard', '/portal/secret'):
            self.send_error(403); return
        if p == '/never-reachable':
            self.send_error(404); return
        body = PAGES.get(p.rstrip('/') or '/')
        if body is None:
            self.send_error(404); return
        self.reply(f'<!doctype html><html><body>{body}</body></html>'.encode(), 'text/html')
    def reply(self, body, ctype):
        self.send_response(200); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.end_headers()
        self.wfile.write(body)

srv = ThreadingHTTPServer(('127.0.0.1', PORT), Site)
threading.Thread(target=srv.serve_forever, daemon=True).start()

work = tempfile.mkdtemp(prefix='crawl-test-')
r = subprocess.run([sys.executable, CRAWL, ORIGIN + '/', '--out', work,
                    '--max-pages', '20', '--max-depth', '2', '--delay', '0'],
                   capture_output=True, text=True)
print(r.stdout[-1800:])
if r.returncode != 0:
    print(r.stderr); sys.exit('crawl.py failed')

man = json.load(open(f'{work}/crawl-manifest.json'))
slugs = {p['slug'] for p in man['pages']}
paths = {urlsplit(p['url']).path.rstrip('/') or '/' for p in man['pages']}

PASS, FAIL = [], []
def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}{"  — " + detail if detail and not cond else ""}')

check('manifest records the origin (build.py needs it)', man.get('origin') == ORIGIN)
check('/projects/ portfolio page crawled, not dropped as auth-gated',
      '/projects/case-one' in paths, str(sorted(paths)))
check('known auth path skipped without even requesting it',
      man['skipped'].get(ORIGIN + '/dashboard') == 'auth-gated', str(man['skipped']))
check('403 on a path NOT in AUTH_PAT still caught behaviourally',
      '403' in man['skipped'].get(ORIGIN + '/portal/secret', ''), str(man['skipped']))
check('sitemap-only page behind a paginated index was reached',
      '/articles/hidden' in paths, str(sorted(paths)))
check('sitemap set-difference recorded', 'sitemap_only' in man)
check('a sitemap URL that 404s is reported, not silently lost',
      any('never-reachable' in u for u in man['sitemap_only']), str(man['sitemap_only']))
check('coverage lines printed for the human', 'coverage vs sitemap' in r.stdout)
check('skip reasons printed', 'skipped by reason' in r.stdout)

# --exclude / --include are per-section, not all-or-nothing
r2 = subprocess.run([sys.executable, CRAWL, ORIGIN + '/', '--out', work + '2',
                     '--max-pages', '20', '--max-depth', '2', '--delay', '0',
                     '--exclude', r'^/projects', '--sitemap', ''],
                    capture_output=True, text=True)
man2 = json.load(open(f'{work}2/crawl-manifest.json'))
paths2 = {urlsplit(p['url']).path.rstrip('/') or '/' for p in man2['pages']}
check('--exclude PATTERN drops just that section',
      '/projects/case-one' not in paths2 and '/about' in paths2, str(sorted(paths2)))

r3 = subprocess.run([sys.executable, CRAWL, ORIGIN + '/', '--out', work + '3',
                     '--max-pages', '2', '--max-depth', '2', '--delay', '0',
                     '--sitemap', ''], capture_output=True, text=True)
man3 = json.load(open(f'{work}3/crawl-manifest.json'))
check('pages dropped by the --max-pages cap are recorded as a skip reason',
      any('max-pages cap' in v for v in man3['skipped'].values()),
      str(man3['skipped']))

srv.shutdown()
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
for d in (work, work + '2', work + '3'): shutil.rmtree(d, ignore_errors=True)
if FAIL: print('FAILED:', ', '.join(FAIL)); sys.exit(1)
