#!/usr/bin/env python3
"""
Static server for local mirrors — honours the `?range=` query parameter.

`python3 -m http.server` ignores query strings and returns the whole file.
Framer's CMS loader slices data chunks with `?range=a-b` (and multi-range
`?range=a-b,c-d`, the comma percent-encoded as %2C) and validates the response
length, so the whole file reads as `Unexpected response length` — which Framer
treats as fatal and tears the rendered tree down to an empty shell. It races the
rest of the render, so it presents as intermittent: headless captures can pass
while the interactive page collapses. One page measured 9.76% against a 99.93%
ceiling from this alone while its 20 siblings sat at 99.7%+.

Ranges are inclusive on both ends, like HTTP Range. A multi-range request
returns the concatenation of every slice in the order asked for — honouring
only the first pair fails exactly the same way, and only on the pages whose
collections are big enough to be split.

Everything else is served normally, so this is a drop-in replacement for
`python3 -m http.server` on any mirror. Use it for all of them, not just Framer:
a mirror that never issues a range request is unaffected.

Usage:
  python3 serve.py --directory site --port 8791
"""
import argparse, os, re, sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit, quote

RANGE_RE = re.compile(r'^(\d+)-(\d+)$')

# Older Pythons do not know .mjs or .avif. A module served as
# application/octet-stream is refused by the browser's strict MIME check for ES
# modules, which takes down the render the same way a 404 would.
EXTRA_TYPES = {
    '.mjs': 'text/javascript',
    '.js': 'text/javascript',
    '.avif': 'image/avif',
    '.webp': 'image/webp',
    '.woff2': 'font/woff2',
    '.json': 'application/json',
    '.wasm': 'application/wasm',
}


def parse_ranges(raw):
    """'12650-18880,25241-31599' -> [(12650, 18880), (25241, 31599)].

    Returns None for anything malformed so the caller can fall through to
    serving the file normally — a bad range is not worth a 500.
    """
    spans = []
    for part in raw.split(','):
        m = RANGE_RE.match(part.strip())
        if not m:
            return None
        start, end = int(m.group(1)), int(m.group(2))
        if end < start:
            return None
        spans.append((start, end))
    return spans or None


def sniff(path):
    """Content type from the leading bytes, or None.

    A mirror keeps the reference's original filenames so every reference to them
    stays valid — but the bytes were fetched with the browser's Accept header, so
    a CDN answering `vary: Accept` hands back AVIF for a file still named `.png`
    (measured: 128 of 160 rasters on one site). Typing that response from the
    extension serves AVIF as image/png. The name is the reference; the bytes are
    the truth.
    """
    try:
        with open(path, 'rb') as f:
            head = f.read(16)
    except OSError:
        return None
    if head[:4] == b'\x89PNG':
        return 'image/png'
    if head[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'image/webp'
    if head[4:8] == b'ftyp':
        brand = head[8:12]
        if brand in (b'avif', b'avis'):
            return 'image/avif'
        if brand in (b'heic', b'heix', b'mif1'):
            return 'image/heic'
        return 'video/mp4'
    if head[:4] == b'wOF2':
        return 'font/woff2'
    if head[:4] == b'wOFF':
        return 'font/woff'
    if head[:4] == b'OTTO':
        return 'font/otf'
    if head[:4] == b'\x00\x01\x00\x00':
        return 'font/ttf'
    if head[:4] == b'\x00\x00\x01\x00':
        return 'image/x-icon'
    return None


class RangeQueryHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, **EXTRA_TYPES}
    ranges_served = 0
    mistyped = 0
    cdn_fallbacks = 0

    def guess_type(self, path):
        by_name = super().guess_type(path)
        # Only binary media can be mistyped this way; never second-guess a text
        # type, where a stray leading byte would be a worse guess than the name.
        if by_name.startswith(('text/', 'application/json', 'application/xml')):
            return by_name
        by_bytes = sniff(path)
        if by_bytes and by_bytes != by_name:
            type(self).mistyped += 1
            return by_bytes
        return by_name

    def _wanted(self):
        raw = parse_qs(urlsplit(self.path).query).get('range', [''])[0]
        return parse_ranges(raw) if raw else None

    def _slice(self, path, spans):
        size = os.path.getsize(path)
        out = bytearray()
        with open(path, 'rb') as f:
            for start, end in spans:
                if start >= size:
                    continue            # past EOF contributes nothing, like a slice
                f.seek(start)
                out += f.read(min(end, size - 1) - start + 1)
        return bytes(out)

    def _serve_ranges(self, spans, body):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404, 'File not found')
            return
        try:
            data = self._slice(path, spans)
        except OSError:
            self.send_error(404, 'File not found')
            return

        # 200, not 206: this is a query parameter, not an HTTP Range request,
        # and a 206 without Content-Range is malformed.
        self.send_response(200)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')   # re-diffs must not read stale bytes
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        if body:
            self.wfile.write(data)
        type(self).ranges_served += 1

    def _reroute_missing_asset(self):
        """build.py rewrites markup's own asset references to /cdn/<file>, but a
        site's JS can build ITS OWN asset URLs at runtime from a publicPath baked
        into the bundle at capture time — Next.js's webpack chunk loader is the
        measured case. That request still targets the reference site's original
        absolute path and 404s, even though build.py already mirrored the exact
        same bytes into cdn/ under their original basename. Every mirrored asset
        lives flat in cdn/ regardless of its source path, so one basename lookup
        recovers it — no need to parse the minified bundle that built the URL.
        """
        if not os.path.isfile(self.translate_path(self.path)):
            basename = os.path.basename(urlsplit(self.path).path)
            if basename and os.path.isfile(os.path.join(self.directory, 'cdn', basename)):
                type(self).cdn_fallbacks += 1
                query = urlsplit(self.path).query
                self.path = '/cdn/' + quote(basename) + (f'?{query}' if query else '')

    def do_GET(self):
        self._reroute_missing_asset()
        spans = self._wanted()
        if spans is None:
            return super().do_GET()
        self._serve_ranges(spans, body=True)

    def do_HEAD(self):
        self._reroute_missing_asset()
        spans = self._wanted()
        if spans is None:
            return super().do_HEAD()
        self._serve_ranges(spans, body=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--directory', default='site', help='mirror root to serve (default: site)')
    ap.add_argument('--port', type=int, default=8791)
    ap.add_argument('--bind', default='127.0.0.1', help='loopback by default; a mirror is not for the network')
    a = ap.parse_args()

    if not os.path.isdir(a.directory):
        sys.exit(f'no such directory: {a.directory}')

    handler = partial(RangeQueryHandler, directory=a.directory)
    with ThreadingHTTPServer((a.bind, a.port), handler) as httpd:
        print(f'serving {a.directory} at http://{a.bind}:{a.port}/  (?range= honoured, Ctrl-C to stop)')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f'\nstopped. range requests served: {RangeQueryHandler.ranges_served}'
                  f'   responses retyped from magic bytes: {RangeQueryHandler.mistyped}'
                  f'   runtime asset URLs recovered via cdn/ fallback: {RangeQueryHandler.cdn_fallbacks}')


if __name__ == '__main__':
    main()
