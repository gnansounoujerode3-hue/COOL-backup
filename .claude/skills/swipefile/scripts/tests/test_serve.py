#!/usr/bin/env python3
"""Empirical test of swipefile scripts/serve.py against the documented failure."""
import os, socket, subprocess, sys, tempfile, time, urllib.request, urllib.error

import os, pathlib as _pl
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)

SERVE = os.path.join(SCRIPTS, 'serve.py')
root = tempfile.mkdtemp(prefix='mirror-')

# deterministic 1000-byte payload; byte i == i % 256
PAYLOAD = bytes(i % 256 for i in range(1000))
open(os.path.join(root, 'chunk.json'), 'wb').write(PAYLOAD)
open(os.path.join(root, 'index.html'), 'w').write('<h1>mirror</h1>')
open(os.path.join(root, 'app.mjs'), 'w').write('export const x=1;\n')
# AVIF bytes in a file still named .png — what an Accept-correct fetch produces
open(os.path.join(root, 'hero.png'), 'wb').write(
    b'\x00\x00\x00\x20ftypavif' + b'\x00' * 32)
open(os.path.join(root, 'real.png'), 'wb').write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 32)
open(os.path.join(root, 'face.woff2'), 'wb').write(b'wOF2' + b'\x00' * 32)
# a Next.js-style async chunk: build.py mirrors it flat into cdn/, but the
# page's own webpack runtime requests it at the ORIGINAL absolute site path
os.makedirs(os.path.join(root, 'cdn'), exist_ok=True)
# Binary mode on purpose. Text mode translates the trailing \n to \r\n on
# Windows, so the file lands 19 bytes and the byte-for-byte assertion below
# fails on a fallback that worked perfectly — status 200, right file, wrong
# length. A served asset is bytes; the fixture has to be written as bytes.
open(os.path.join(root, 'cdn', '9627638a-fake.js'), 'wb').write(b'export const x=2;\n')

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def wait(port, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close(); return True
        except OSError:
            time.sleep(0.05)
    return False

def get(port, path, method='GET'):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', method=method)
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, r.headers, r.read()   # HTTPMessage: case-insensitive lookup

PASS, FAIL = [], []
def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}{"  — " + detail if detail and not cond else ""}')

# ---------- 1. the server under test ----------
port = free_port()
proc = subprocess.Popen([sys.executable, SERVE, '--directory', root, '--port', str(port)],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
try:
    assert wait(port), 'serve.py did not start'

    st, h, b = get(port, '/chunk.json')
    check('plain GET returns whole file', b == PAYLOAD and st == 200, f'{len(b)} bytes')

    st, h, b = get(port, '/chunk.json?range=10-19')
    check('single range is inclusive, 10 bytes', b == PAYLOAD[10:20], f'got {len(b)}')
    check('single range Content-Length matches body', h.get('Content-Length') == str(len(b)))

    st, h, b = get(port, '/chunk.json?range=10-19,30-34')
    check('multi-range concatenates both slices',
          b == PAYLOAD[10:20] + PAYLOAD[30:35], f'got {len(b)}, want 15')

    st, h, b = get(port, '/chunk.json?range=10-19%2C30-34')
    check('multi-range works percent-encoded (%2C)',
          b == PAYLOAD[10:20] + PAYLOAD[30:35], f'got {len(b)}')

    st, h, b = get(port, '/chunk.json?range=100-199,300-399,500-599')
    check('three ranges concatenate in order',
          b == PAYLOAD[100:200] + PAYLOAD[300:400] + PAYLOAD[500:600], f'got {len(b)}')

    st, h, b = get(port, '/chunk.json?range=30-34,10-19')
    check('ranges returned in requested order, not sorted',
          b == PAYLOAD[30:35] + PAYLOAD[10:20])

    st, h, b = get(port, '/chunk.json?range=995-2000')
    check('range clamps at EOF', b == PAYLOAD[995:1000], f'got {len(b)}, want 5')

    st, h, b = get(port, '/chunk.json?range=5000-6000')
    check('range past EOF is empty, not an error', st == 200 and b == b'')

    st, h, b = get(port, '/chunk.json?range=0-0')
    check('single-byte range', b == PAYLOAD[0:1])

    st, h, b = get(port, '/chunk.json?range=abc')
    check('malformed range falls through to whole file', b == PAYLOAD)

    st, h, b = get(port, '/chunk.json?range=50-10')
    check('reversed range falls through, no crash', b == PAYLOAD)

    st, h, b = get(port, '/chunk.json?v=12345')
    check('unrelated query string still serves whole file', b == PAYLOAD)

    st, h, b = get(port, '/chunk.json?range=10-19', method='HEAD')
    check('HEAD with range: correct length, empty body',
          h.get('Content-Length') == '10' and b == b'')

    st, h, b = get(port, '/app.mjs')
    check('.mjs served as text/javascript (ES module MIME check)',
          'javascript' in h.get('Content-Type', ''), h.get('Content-Type'))

    st, h, b = get(port, '/')
    check('directory index still works', b'mirror' in b)

    st, h, b = get(port, '/hero.png')
    check('AVIF bytes in a .png are served as image/avif (magic bytes win)',
          h.get('Content-Type') == 'image/avif', h.get('Content-Type'))
    st, h, b = get(port, '/real.png')
    check('a genuine .png is still image/png', h.get('Content-Type') == 'image/png',
          h.get('Content-Type'))
    st, h, b = get(port, '/face.woff2')
    check('woff2 magic bytes typed correctly', h.get('Content-Type') == 'font/woff2',
          h.get('Content-Type'))
    st, h, b = get(port, '/index.html')
    check('text types are never second-guessed from bytes',
          'text/html' in h.get('Content-Type', ''), h.get('Content-Type'))

    try:
        get(port, '/nope.json?range=0-9'); check('404 for missing file with range', False)
    except urllib.error.HTTPError as e:
        check('404 for missing file with range', e.code == 404)

    st, h, b = get(port, '/static-assets/app/_next/static/chunks/9627638a-fake.js')
    check('runtime-constructed asset URL recovered via cdn/ basename fallback',
          st == 200 and b == b'export const x=2;\n', f'status {st}, {len(b)} bytes')
    check('recovered chunk still gets its real content type',
          'javascript' in h.get('Content-Type', ''), h.get('Content-Type'))

    try:
        get(port, '/static-assets/app/_next/static/chunks/does-not-exist.js')
        check('a truly missing asset still 404s, no false-positive fallback', False)
    except urllib.error.HTTPError as e:
        check('a truly missing asset still 404s, no false-positive fallback', e.code == 404)

    st, h, b = get(port, '/chunk.json?range=10-19')
    check('no-store set so re-diffs cannot read stale bytes',
          'no-store' in h.get('Cache-Control', ''))
finally:
    proc.terminate(); proc.wait(timeout=5)

# ---------- 2. reproduce the bug on stock http.server ----------
port2 = free_port()
p2 = subprocess.Popen([sys.executable, '-m', 'http.server', str(port2), '--directory', root],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    assert wait(port2)
    st, h, b = get(port2, '/chunk.json?range=10-19')
    check('CONTROL: stock http.server returns whole file for ?range= (the bug)',
          len(b) == 1000, f'returned {len(b)} bytes for a 10-byte request')
finally:
    p2.terminate(); p2.wait(timeout=5)

print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL)); sys.exit(1)
