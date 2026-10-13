#!/usr/bin/env python3
"""Font gate: can it tell a real face from a fallback, in a real browser?

This is the one instrument in the folder that had no test, and the only one
whose failures are invisible by construction — a page in the wrong face renders
perfectly, just wrong, and every cheap detector lies about it: computed
fontFamily echoes the requested family while a fallback paints, and
document.fonts.check() returned TRUE throughout the SRI failure that left a page
in Times. Only the canvas A/B catches that, so the A/B is what is asserted here,
against a real font file served over HTTP rather than a stub.

Skips cleanly without Chrome, `websockets`, or a system TTF to serve — same
contract as the motion suite, and for the same reason: the behaviour under test
only exists in a browser.
"""
import json, os, pathlib as _pl, shutil, socket, subprocess, sys, tempfile, time
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
CDP = os.path.join(SCRIPTS, 'cdp-run.py')
SERVE = os.path.join(SCRIPTS, 'serve.py')
GATE = os.path.join(SCRIPTS, 'font-gate.js')

try:
    import websockets  # noqa: F401
except ImportError:
    print('SKIP  font — `websockets` not installed (pip install websockets)')
    sys.exit(0)
if not any(os.path.exists(p) for p in (
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium')) and not (
        shutil.which('google-chrome') or shutil.which('chromium')):
    print('SKIP  font — no Chrome found')
    sys.exit(0)

# A real face with metrics obviously unlike any sans-serif, so "the requested
# face is painting" is a measurable claim rather than an assumption.
TTF = next((p for p in ('/System/Library/Fonts/Supplemental/Courier New.ttf',
                        '/System/Library/Fonts/Supplemental/Andale Mono.ttf',
                        '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
                        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
            if os.path.exists(p)), None)
if not TTF:
    print('SKIP  font — no system TTF available to serve as a probe face')
    sys.exit(0)

FIXTURE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
@font-face{font-family:'ProbeFace';src:url(probe.ttf) format('truetype')}
/* Framer and friends register metric-compatible "<Family> Placeholder" faces
   BY DESIGN, so an A/B against the page's own stack reads identical on a page
   where the real font is genuinely loaded. The gate has to surface them. */
@font-face{font-family:'Ghost Placeholder';src:url(probe.ttf) format('truetype')}
body{margin:0;font-family:sans-serif}
.display{font-family:'ProbeFace',sans-serif;font-size:64px;font-weight:400}
.small{font-family:'ProbeFace',sans-serif;font-size:14px;font-weight:400}
.ghost{font-family:'NoSuchFaceXYZ',sans-serif;font-size:32px;font-weight:400}
.gone{display:none;font-family:'HiddenFace',sans-serif;font-size:20px}
.zero{position:absolute;width:0;height:0;overflow:hidden;
      font-family:'ZeroFace',sans-serif;font-size:20px}
</style></head><body>
<h1 class="display">Display cut</h1>
<p class="small">one</p><p class="small">two</p><p class="small">three</p>
<p class="ghost">requested but absent</p>
<p class="gone">never painted</p><p class="zero">never painted</p>
</body></html>"""

BARE = ('<!doctype html><html lang="en"><head><meta charset="utf-8"></head>'
        '<body><p style="font-family:sans-serif">no web fonts here</p></body></html>')

OVERRIDE = FIXTURE.replace('</body>', """<script>
window.__fontGateSpecs=[{family:'ProbeFace',weight:400,size:48}];
</script></body>""")


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


root = tempfile.mkdtemp(prefix='font-test-')
# copyfile, not copy2: a system font carries macOS flags that copystat cannot
# reproduce under SIP, and only the bytes matter here.
shutil.copyfile(TTF, os.path.join(root, 'probe.ttf'))
for name, text in (('f.html', FIXTURE), ('bare.html', BARE), ('override.html', OVERRIDE)):
    open(os.path.join(root, name), 'w', encoding='utf-8').write(text)

port = free_port()
srv = subprocess.Popen([sys.executable, SERVE, '--directory', root, '--port', str(port)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:300] if detail and not cond else ""}')


def probe(page):
    r = subprocess.run([sys.executable, CDP, f'http://127.0.0.1:{port}/{page}', GATE,
                        '--width', '1280', '--height', '900', '--settle', '2'],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(r.stderr[-800:])
        raise SystemExit(f'cdp-run failed on {page}')
    return json.loads(r.stdout)


try:
    end = time.time() + 10
    while time.time() < end:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close(); break
        except OSError:
            time.sleep(0.05)

    d = probe('f.html')
    fams = {f['family']: f for f in d['families']}

    # ---- the A/B arm: the only detector that survives a silent fallback
    check('the probe ran and returned families', bool(fams), d.get('summary'))
    probe_face = fams.get('ProbeFace')
    check('a real served face is reported as loaded',
          probe_face and probe_face['check'] is True, probe_face)
    check('a real served face measures WIDER or NARROWER than sans-serif',
          probe_face and probe_face['differs'] is True,
          probe_face and (probe_face['requestedWidth'], probe_face['fallbackWidth']))
    check('the width gap is a real measurement, not a rounding artefact',
          probe_face and abs(probe_face['requestedWidth']
                             - probe_face['fallbackWidth']) > 5,
          probe_face and (probe_face['requestedWidth'], probe_face['fallbackWidth']))

    ghost = fams.get('NoSuchFaceXYZ')
    # Measured here, and it is worse than the docstring claimed: check() returns
    # TRUE for a family that was never declared at all, because the spec asks
    # whether the text can be rendered — and it can, in a fallback. So check()
    # cannot detect an absent face in ANY case, not merely the SRI one. This is
    # the whole reason the canvas A/B exists, asserted rather than assumed.
    check('check() returns true even for a family that does not exist — it cannot '
          'detect an absent face, which is why the A/B arm is not optional',
          ghost and ghost['check'] is True, ghost)
    check('the A/B arm catches what check() missed: IDENTICAL to the fallback',
          ghost and ghost['differs'] is False,
          ghost and (ghost['requestedWidth'], ghost['fallbackWidth']))
    check('the summary lists it under identicalToFallback',
          'NoSuchFaceXYZ' in d['summary']['identicalToFallback'],
          d['summary']['identicalToFallback'])

    # ---- probe the DISPLAY cut, where a metric-compatible swap is visible
    check('the largest size per family+weight is the one probed',
          probe_face and probe_face['size'] == 64, probe_face and probe_face['size'])

    # ---- faces and the SRI signature
    check('declared faces are counted', d['faces'] >= 2, d['faces'])
    check('zeroFaces is false when the page declares faces', d['zeroFaces'] is False)
    check('metric-compatible Placeholder faces are surfaced',
          any('Ghost Placeholder' in f for f in d['placeholderFaces']),
          d['placeholderFaces'])

    # ---- the census counts what paints, and only what paints
    seen = {(c['family'], c['size']): c['count'] for c in d['census']}
    check('census counts rendered text by frequency',
          seen.get(('ProbeFace', 14)) == 3, d['census'][:4])
    check('display:none text is not counted',
          not any(c['family'] == 'HiddenFace' for c in d['census']), d['census'])
    check('zero-box text is not counted',
          not any(c['family'] == 'ZeroFace' for c in d['census']), d['census'])
    check('census is sorted by count, most frequent first',
          [c['count'] for c in d['census']] == sorted((c['count'] for c in d['census']),
                                                      reverse=True),
          [c['count'] for c in d['census']])

    # ---- a page with no web fonts at all
    b = probe('bare.html')
    check('a page with no @font-face reports zero faces', b['faces'] == 0, b['faces'])
    check('and says so explicitly rather than leaving it to be inferred',
          b['zeroFaces'] is True)
    check('it still probes the system stack rather than returning nothing',
          len(b['families']) >= 1, b['families'])

    # ---- the caller can name the faces to probe
    o = probe('override.html')
    check('__fontGateSpecs overrides the page census',
          [f['family'] for f in o['families']] == ['ProbeFace'],
          [f['family'] for f in o['families']])
    check('and the requested size is honoured', o['families'][0]['size'] == 48,
          o['families'][0])

    # ---- the two-sided contract the report gate depends on
    check('the payload states that an absolute true is not the gate',
          'not the gate' in d['compare'].lower(), d['compare'])
    for key in ('faces', 'families', 'census', 'loaded', 'summary', 'viewport'):
        check(f'payload carries `{key}` for the two-sided comparison', key in d)
finally:
    srv.terminate()
    srv.wait(timeout=5)
    shutil.rmtree(root, ignore_errors=True)

print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
