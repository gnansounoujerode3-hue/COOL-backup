#!/usr/bin/env python3
"""
Run a capture script against a live page in real headless Chrome, over CDP.

This is the browser tier that always works. The alternatives each fail in a way
that is silent rather than loud:

  - `chrome --headless --virtual-time-budget ... --dump-dom` scrolls fine but
    never fires IntersectionObserver, so every scroll-triggered reveal reports
    as "no motion on this page". Measured: 0 animations on a fixture with 10.
  - An in-app browser pane can report `innerHeight === 0` while looking open, in
    which case nothing can intersect and the same empty result comes back. It
    has also rendered a working page as a fully black frame.

Both produce empty captures that read as findings. CDP against real headless
Chrome is the instrument; use it for anything whose number you intend to keep.

  python3 cdp-run.py https://example.com motion-extract.js
  python3 cdp-run.py https://example.com font-gate.js --width 390 --height 844

Needs the `websockets` package (stdlib has no WebSocket client) and Chrome.
Prints the script's return value as JSON on stdout; diagnostics go to stderr.
"""
import argparse, asyncio, json, os, shutil, socket, subprocess, sys, tempfile, time
import urllib.request

CHROME_CANDIDATES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    shutil.which('google-chrome') or '',
    shutil.which('chromium') or '',
    shutil.which('chrome') or '',
    # Windows installs Chrome outside PATH, so `which` finds nothing and the
    # instrument reports "no Chrome found" on a machine that has it. Every
    # script in this folder that measures anything routes through here.
    os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
    os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
    os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
    os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
]


def find_chrome(explicit=None):
    for p in ([explicit] if explicit else []) + CHROME_CANDIDATES:
        if p and os.path.exists(p):
            return p
    sys.exit('no Chrome found — pass --chrome /path/to/chrome')


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_for_devtools(port, timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=1) as r:
                return json.load(r)
        except Exception:
            time.sleep(0.15)
    return None


async def drive(ws_url, url, expression, settle, nav_timeout, pre_expression=None):
    import websockets
    try:
        connect = websockets.asyncio.client.connect          # websockets >= 12
    except AttributeError:
        connect = websockets.connect                          # older
    msg_id = 0

    async with connect(ws_url, max_size=64 * 1024 * 1024, open_timeout=20) as ws:
        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
            while True:
                data = json.loads(await ws.recv())
                if data.get('id') == msg_id:
                    return data

        async def wait_event(name, timeout):
            end = time.time() + timeout
            while time.time() < end:
                try:
                    data = json.loads(await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - time.time())))
                except asyncio.TimeoutError:
                    return False
                if data.get('method') == name:
                    return True
            return False

        await send('Page.enable')
        await send('Runtime.enable')
        if pre_expression:
            # Runs before any of the page's own script on every new document, so
            # hooks are in place for load-time animations. Without this, hero and
            # entrance motion has already fired and been discarded by the time a
            # post-load evaluate runs, and the page reports as having none.
            await send('Page.addScriptToEvaluateOnNewDocument', {'source': pre_expression})
        await send('Page.navigate', {'url': url})
        if not await wait_event('Page.loadEventFired', nav_timeout):
            print(f'warning: no load event within {nav_timeout}s — evaluating anyway',
                  file=sys.stderr)
        await asyncio.sleep(settle)

        res = await send('Runtime.evaluate', {
            'expression': expression,
            'awaitPromise': True,
            'returnByValue': True,
            'timeout': 120000,
        })
        result = res.get('result', {})
        if 'exceptionDetails' in result:
            print(json.dumps(result['exceptionDetails'], indent=1), file=sys.stderr)
            sys.exit('script threw in the page')
        return result.get('result', {}).get('value')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('url')
    ap.add_argument('script', help='path to a .js file; its return value is printed')
    ap.add_argument('--pre', default=None, metavar='FILE',
                    help='JS injected at document-start, before the page\'s own scripts. '
                         'Use the same file as `script` for two-phase captures like '
                         'motion-extract.js, which installs hooks early then reports late.')
    ap.add_argument('--width', type=int, default=1440)
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--settle', type=float, default=2.5, help='seconds after load before evaluating')
    ap.add_argument('--nav-timeout', type=float, default=45)
    ap.add_argument('--chrome', default=None)
    ap.add_argument('--out', default=None, help='write JSON here instead of stdout')
    a = ap.parse_args()

    expression = open(a.script, encoding='utf-8').read()
    pre_expression = open(a.pre, encoding='utf-8').read() if a.pre else None
    chrome, port = find_chrome(a.chrome), free_port()
    profile = tempfile.mkdtemp(prefix='cdp-profile-')
    proc = subprocess.Popen([
        chrome, '--headless=new', f'--remote-debugging-port={port}',
        f'--user-data-dir={profile}', f'--window-size={a.width},{a.height}',
        '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
        '--force-device-scale-factor=1', '--disable-features=Translate',
        'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_for_devtools(port):
            sys.exit('Chrome did not expose the DevTools endpoint')
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as r:
            targets = json.load(r)
        page = next((t for t in targets if t.get('type') == 'page'), None)
        if not page:
            sys.exit('no page target')
        value = asyncio.run(drive(page['webSocketDebuggerUrl'], a.url, expression,
                                  a.settle, a.nav_timeout, pre_expression))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(profile, ignore_errors=True)

    text = json.dumps(value, indent=1, ensure_ascii=False)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(text)
        print(f'wrote {a.out} ({len(text)} chars)', file=sys.stderr)
    else:
        print(text)


if __name__ == '__main__':
    main()
