#!/usr/bin/env python3
"""Design gate: does it fail the right things, and refuse to pass the unmeasured?

The gate replaces a 60-box self-attested checklist, so the cases that matter are
the ones a checklist gets wrong: a check that reads `ok` while its own detail
line describes a violation, a heuristic that fires on a legitimate build until
the reader stops trusting the gate, and an input nobody supplied being folded
into a pass.

The logic arm runs on synthetic probe payloads and needs no browser. The
end-to-end arm serves a fixture page with known, deliberate defects and asserts
the real probe finds them in a real Chrome; it skips cleanly without one.
"""
import http.server, importlib.util, json, os, pathlib as _pl, shutil, socket
import subprocess, sys, tempfile, threading

SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
GATE = os.path.join(SCRIPTS, 'design-gate.py')

spec = importlib.util.spec_from_file_location('design_gate', GATE)
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)

PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:400] if detail and not cond else ""}')


# Six distinct opening fingerprints so the default 6-section page (below) is
# clean on the section-opening-monotony check too — a "disciplined page"
# fixture that quietly repeated its own shape would be the wrong baseline.
_OPEN_SHAPES = [
    ['div:s:n:u', 'h2:xl:b', 'p:m:n'],
    ['h3:l:b', 'p:m:n', 'ul:m:n'],
    ['img:m:n', 'h2:l:b'],
    ['blockquote:l:n', 'p:m:n'],
    ['div:m:n', 'div:m:n', 'div:m:n'],
    ['h2:xl:b', 'div:m:n', 'p:m:n', 'div:s:n'],
]


def section(i, lum=1.0, split=False):
    return {'index': i, 'tag': 'section', 'id': None,
            'rect': {'top': i * 800, 'left': 0, 'width': 1440, 'height': 800},
            'bgHex': '#ffffff', 'bgLuminance': lum, 'bgImage': False, 'media': 1,
            'childCount': 2, 'gridColumns': 2, 'splitImageText': split,
            'openShape': _OPEN_SHAPES[i % len(_OPEN_SHAPES)]}


def shot(**over):
    """A clean page. Every case below is this with one thing broken."""
    base = {
        'url': 'http://127.0.0.1:9/', 'viewport': {'w': 1440, 'h': 900},
        'scrollHeight': 5000,
        'sections': [section(i) for i in range(6)],
        'hero': {'height': 800, 'viewportHeight': 900, 'paddingTop': 40,
                 'textElements': 4, 'headline': 'A real headline', 'headlineLines': 2,
                 'ctas': 1, 'firstCtaTop': 400, 'realMedia': 1, 'backgroundPhotos': 0,
                 'gradientOnly': False, 'lastCtaBottom': 440, 'textBelowCtas': 0,
                 'textBelowCtaSamples': []},
        'nav': {'height': 72, 'items': 6, 'rows': 1, 'labels': []},
        'buttons': [{'label': 'Get started', 'tag': 'a', 'inNav': False, 'size': 16,
                     'lines': 1, 'words': 2, 'fg': '#ffffff', 'bg': '#111111',
                     'overImage': False, 'contrast': 18.9, 'required': 4.5,
                     'top': 400, 'width': 180}],
        'forms': [],
        'eyebrows': {'count': 2, 'samples': []},
        'text': {'emDashes': 0, 'emDashSamples': [], 'body': 'Real copy.', 'nodes': 40},
        'census': {'colors': [], 'accents': [{'hue': 0, 'uses': 20, 'samples':
                                              [{'hex': '#ff532e', 'uses': 20}]}],
                   'radii': [{'radius': '12', 'uses': 40}],
                   'families': [{'family': 'Geist', 'uses': 90, 'loaded': True}]},
        'media': {'images': 6, 'canvases': 0},
        'motion': {'reducedMotionRules': 1, 'stylesheetsUnreadable': 0,
                   'infiniteAnimations': 1, 'marquees': 1},
    }
    base.update(over)
    return base


def ev(shots=None, src=None, mode='adapt', brief='', strict_hero=False):
    return dg.evaluate(shots or {1440: shot()}, src, mode, brief, strict_hero)


def status(c, needle):
    for r in c.rows:
        if needle in r['check']:
            return r['status']
    return None


def detail(c, needle):
    for r in c.rows:
        if needle in r['check']:
            return r['detail']
    return None


# ---- the clean baseline must actually be clean, or every case below is noise
c = ev(src=[])
check('a disciplined page produces no failures', not c.by('FAIL'),
      [r['check'] for r in c.by('FAIL')])

# ---- a passing check never carries a violation in its detail line
# The first version of this gate printed `ok — no prefers-reduced-motion rule
# anywhere in the page CSS`. A row that says ok and reads as a failure is worse
# than no row: it is the checklist failure mode reproduced inside the fix for it.
c = ev(src=[])
contradictions = [r for r in c.rows if r['status'] == 'pass'
                  and any(w in r['detail'].lower() for w in ('no ', 'missing', 'wraps'))
                  and 'n/a' not in r['detail'].lower()]
check('no passing check contradicts itself in its own detail',
      not contradictions, contradictions)

# ---- copy rules are ours, not the reference's
DASHED = shot(text={'emDashes': 3, 'emDashSamples': ['a — b'], 'body': 'a — b', 'nodes': 4})
check('em-dashes fail an authored page', status(ev({1440: DASHED}, src=[]),
                                                'em-dashes') == 'FAIL')
check('em-dashes do not fail a Match — captured copy is verbatim by design',
      status(ev({1440: DASHED}, src=[], mode='match'), 'em-dashes') == 'pass')

TELL = shot(text={'emDashes': 0, 'emDashSamples': [],
                  'body': 'Scroll to explore\nOur work\nJane Doe, Acme Inc', 'nodes': 4})
c = ev({1440: TELL}, src=[])
check('rendered-text tells are caught', status(c, 'banned filler') == 'FAIL',
      detail(c, 'banned filler'))
check('and each one is named, not counted', 'scroll cue' in detail(c, 'banned filler')
      and 'placeholder person' in detail(c, 'banned filler'), detail(c, 'banned filler'))

# ---- the eyebrow budget is arithmetic, not taste
check('eyebrows within ceil(sections/3) pass',
      status(ev({1440: shot(eyebrows={'count': 2, 'samples': []})}, src=[]), 'eyebrow') == 'pass')
check('one eyebrow over budget fails',
      status(ev({1440: shot(eyebrows={'count': 3, 'samples': []})}, src=[]), 'eyebrow') == 'FAIL')

# ---- contrast: measured is a failure, unmeasurable is a warning
LOW = shot(buttons=[dict(shot()['buttons'][0], fg='#cccccc', bg='#ffffff', contrast=1.6)])
check('a CTA below WCAG AA fails', status(ev({1440: LOW}, src=[]), 'every CTA clears') == 'FAIL')
OVER = shot(buttons=[dict(shot()['buttons'][0], overImage=True, contrast=1.1)])
c = ev({1440: OVER}, src=[])
check('a CTA over imagery warns rather than failing — the ratio is not computable',
      status(c, 'every CTA clears') == 'pass' and status(c, 'CTAs over imagery') == 'WARN',
      [r for r in c.rows if 'CTA' in r['check']])
LARGE = shot(buttons=[dict(shot()['buttons'][0], size=28, contrast=3.4, required=3)])
check('large text is held to 3:1, not 4.5:1',
      status(ev({1440: LARGE}, src=[]), 'every CTA clears') == 'pass')
WRAP = shot(buttons=[dict(shot()['buttons'][0], label='VIEW SELECTED WORK', lines=2, words=3)])
check('a wrapped CTA label fails at desktop',
      status(ev({1440: WRAP}, src=[]), 'CTA label wraps') == 'FAIL')

# ---- nav: a cap with a tolerance, because 80.2px is not a two-line nav
check('a nav 0.2px over the cap passes',
      status(ev({1440: shot(nav={'height': 80.203, 'items': 6, 'rows': 1, 'labels': []})},
                src=[]), 'navigation height') == 'pass')
check('a nav genuinely over the cap fails',
      status(ev({1440: shot(nav={'height': 112, 'items': 6, 'rows': 1, 'labels': []})},
                src=[]), 'navigation height') == 'FAIL')
check('a two-line nav fails',
      status(ev({1440: shot(nav={'height': 72, 'items': 9, 'rows': 2, 'labels': []})},
                src=[]), 'one line') == 'FAIL')
check('no nav found is unverified, not a silent exemption',
      status(ev({1440: shot(nav=None)}, src=[]), 'navigation') == 'UNVERIFIED')

# ---- theme lock: one deliberate switch is allowed, oscillation is not
ONE = [section(0, 0.02), section(1, 0.02), section(2, 0.96), section(3, 0.96)]
TWO = [section(0, 0.02), section(1, 0.96), section(2, 0.02), section(3, 0.96)]
check('a single deliberate theme switch warns, it does not fail',
      status(ev({1440: shot(sections=ONE)}, src=[]), 'theme lock') == 'WARN')
check('oscillating light and dark sections fail',
      status(ev({1440: shot(sections=TWO)}, src=[]), 'theme lock') == 'FAIL')
ALL_IMG = [dict(section(i), bgImage=True) for i in range(4)]
check('sections on photography are unverified, not failed on the div behind them',
      status(ev({1440: shot(sections=ALL_IMG)}, src=[]), 'theme lock') == 'UNVERIFIED')

# ---- flat-fill census: most sections being one flat colour is a tell, not a fail
FLAT = [dict(section(i), media=0) for i in range(6)]
c = ev({1440: shot(sections=FLAT)}, src=[])
check('mostly flat solid-colour sections warn, they do not fail',
      status(c, 'flat-fill census') == 'WARN', detail(c, 'flat-fill census'))
check('and the census names the count', '6/6' in detail(c, 'flat-fill census'),
      detail(c, 'flat-fill census'))
VARIED_FILL = [dict(section(0), media=0), dict(section(1), media=0),
               section(2), section(3), section(4), section(5)]
check('a page where only a couple sections are flat does not warn',
      status(ev({1440: shot(sections=VARIED_FILL)}, src=[]), 'flat-fill census') == 'pass')
check('zero sections resolved is unverified, not a silent pass',
      status(ev({1440: shot(sections=[])}, src=[]), 'flat-fill census') == 'UNVERIFIED')

# ---- section-opening monotony: heuristic, read and judged, not a verdict
SAME_OPEN = [dict(section(i), openShape=['div:s:n:u', 'h2:xl:b', 'p:m:n']) for i in range(6)]
c = ev({1440: shot(sections=SAME_OPEN)}, src=[])
check('six sections opening with the identical structure warn',
      status(c, 'section-opening monotony') == 'WARN', detail(c, 'section-opening monotony'))
check('and the census names the repeated shape',
      'h2:xl:b' in detail(c, 'section-opening monotony'), detail(c, 'section-opening monotony'))
check("a page whose sections open differently doesn't warn",
      status(ev(src=[]), 'section-opening monotony') == 'pass')
NO_SHAPES = [dict(section(i), openShape=[]) for i in range(4)]
check('no resolvable opening fingerprints is unverified, not a silent pass',
      status(ev({1440: shot(sections=NO_SHAPES)}, src=[]), 'section-opening monotony')
      == 'UNVERIFIED')

# ---- consistency locks
TWO_ACCENTS = shot(census=dict(shot()['census'], accents=[
    {'hue': 0, 'uses': 20, 'samples': [{'hex': '#ff532e', 'uses': 20}]},
    {'hue': 210, 'uses': 9, 'samples': [{'hex': '#3e5480', 'uses': 9}]}]))
check('two structural accent families fail',
      status(ev({1440: TWO_ACCENTS}, src=[]), 'accent') == 'FAIL')
ONE_STRAY = shot(census=dict(shot()['census'], accents=[
    {'hue': 0, 'uses': 20, 'samples': [{'hex': '#ff532e', 'uses': 20}]},
    {'hue': 210, 'uses': 1, 'samples': [{'hex': '#3e5480', 'uses': 1}]}]))
check('a hue used once is decoration, not a second accent',
      status(ev({1440: ONE_STRAY}, src=[]), 'accent') == 'pass')
FOUR_RADII = shot(census=dict(shot()['census'], radii=[
    {'radius': r, 'uses': 6} for r in ('pill', '12', '8', '4')]))
check('a fourth radius value fails the shape lock',
      status(ev({1440: FOUR_RADII}, src=[]), 'radius scale') == 'FAIL')

# ---- fonts: painted, not merely declared
DECLARED = shot(census=dict(shot()['census'], families=[
    {'family': 'Fraunces', 'uses': 30, 'loaded': False},
    {'family': 'Geist', 'uses': 90, 'loaded': True}]))
check('a banned serif that is declared but never painted does not fail',
      status(ev({1440: DECLARED}, src=[]), 'display serif') == 'pass')
PAINTED = shot(census=dict(shot()['census'], families=[
    {'family': 'Fraunces', 'uses': 30, 'loaded': True}]))
check('a banned serif that is actually painted fails',
      status(ev({1440: PAINTED}, src=[]), 'display serif') == 'FAIL')

# ---- fonts: declared but never rendering (silent system fallback)
check('a font declared with real weight that never loaded fails',
      status(ev({1440: DECLARED}, src=[]), 'no silent system fallback') == 'FAIL')
NAMES_SYSTEM_UI = shot(census=dict(shot()['census'], families=[
    {'family': 'system-ui', 'uses': 90, 'loaded': False}]))
check('a native OS face is exempt — it never goes through @font-face',
      status(ev({1440: NAMES_SYSTEM_UI}, src=[]), 'no silent system fallback') == 'pass')
STRAY_UNLOADED = shot(census=dict(shot()['census'], families=[
    {'family': 'Geist', 'uses': 90, 'loaded': True},
    {'family': 'SomeIcon', 'uses': 1, 'loaded': False}]))
check('an unloaded family used once is noise, not a fallback worth failing on',
      status(ev({1440: STRAY_UNLOADED}, src=[]), 'no silent system fallback') == 'pass')

# ---- the premium-consumer palette is brief-scoped, not universal
BEIGE = shot(sections=[dict(section(i), bgHex='#f5f1ea') for i in range(4)])
check('the beige+brass palette warns on an unstated brief',
      status(ev({1440: BEIGE}, src=[]), 'beige+brass') == 'WARN')
check('and fails when the brief is premium-consumer',
      status(ev({1440: BEIGE}, src=[], brief='premium-consumer'), 'beige+brass') == 'FAIL')

# ---- motion
check('two marquees fail',
      status(ev({1440: shot(motion=dict(shot()['motion'], marquees=2))}, src=[]),
             'marquee') == 'FAIL')
NO_RM = shot(motion={'reducedMotionRules': 0, 'stylesheetsUnreadable': 0,
                     'infiniteAnimations': 3, 'marquees': 0})
check('a page with motion and no reduced-motion rule fails',
      status(ev({1440: NO_RM}, src=[]), 'reduced-motion') == 'FAIL')
BLIND = shot(motion={'reducedMotionRules': 0, 'stylesheetsUnreadable': 4,
                     'infiniteAnimations': 3, 'marquees': 0})
check('unreadable cross-origin stylesheets make it unverified, never a failure',
      status(ev({1440: BLIND}, src=[]), 'reduced-motion') == 'UNVERIFIED')

# ---- unmeasured is never a pass
c = ev(src=None)
check('no --src leaves the source rules UNVERIFIED, not passed',
      status(c, 'source rules') == 'UNVERIFIED', [r for r in c.rows if 'source' in r['check']])
check('and an unverified check is not counted as a failure', not c.by('FAIL'),
      [r['check'] for r in c.by('FAIL')])
c = ev(src=[{'file': 'a.tsx', 'line': 12, 'tier': 'FAIL', 'message': 'h-screen used'}])
check('a source-level violation fails', status(c, 'h-screen') == 'FAIL')
check('and names the file and line', 'a.tsx:12' in detail(c, 'h-screen'), detail(c, 'h-screen'))
c = ev(src=[{'file': 'b.tsx', 'line': 3, 'tier': 'WARN', 'message': 'lucide-react'}])
check('a discouraged import warns rather than failing',
      status(c, 'icon/animation imports') == 'WARN' and not c.by('FAIL'))

# ---- hero
check('a hero CTA below the fold fails',
      status(ev({1440: shot(hero=dict(shot()['hero'], firstCtaTop=1200))}, src=[]),
             'hero CTA visible') == 'FAIL')
check('a hero with no real visual warns by default',
      status(ev({1440: shot(hero=dict(shot()['hero'], realMedia=0, backgroundPhotos=0))},
                src=[]), 'real visual') == 'WARN')
check('and fails under --strict-hero-visual',
      status(ev({1440: shot(hero=dict(shot()['hero'], realMedia=0, backgroundPhotos=0))},
                src=[], strict_hero=True), 'real visual') == 'FAIL')
check('text below the hero CTAs is reported',
      status(ev({1440: shot(hero=dict(shot()['hero'], textBelowCtas=2,
                                      textBelowCtaSamples=['Used by teams at']))},
                src=[]), 'below the hero CTAs') == 'WARN')

# ---- the split-layout cap counts consecutive runs, not totals
SPREAD = [section(0, split=True), section(1), section(2, split=True), section(3),
          section(4, split=True)]
RUN3 = [section(0, split=True), section(1, split=True), section(2, split=True), section(3)]
check('non-consecutive image+text splits pass',
      status(ev({1440: shot(sections=SPREAD)}, src=[]), 'consecutive image+text') == 'pass')
check('three in a row fail',
      status(ev({1440: shot(sections=RUN3)}, src=[]), 'consecutive image+text') == 'FAIL')

# ---- every viewport counts, not just the desktop one
MOBILE_ONLY = {1440: shot(),
               390: shot(buttons=[dict(shot()['buttons'][0], contrast=1.9)])}
check('a contrast failure at 390px fails the run even when 1440px is clean',
      status(ev(MOBILE_ONLY, src=[]), 'every CTA clears') == 'FAIL')


# ---- end-to-end: the real probe in a real browser, on a page built to fail
def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


FIXTURE = """<!doctype html><html><head><meta charset="utf-8"><style>
  body { margin:0; font-family: system-ui; background:#fff; color:#111; }
  .navbar { height:120px; display:flex; flex-wrap:wrap; width:300px; }
  .navbar a { display:block; width:200px; padding:8px; }
  section { min-height:400px; padding:24px; }
  .cta { display:inline-block; padding:14px 28px; background:#ffffff;
         color:#f0f0f0; border:1px solid #eee; }
</style></head><body>
<div class="navbar"><a href="#">One</a><a href="#">Two</a><a href="#">Three</a></div>
<section><h1 style="font-size:48px">A hero headline</h1>
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
       width="400" height="300" alt="">
  <p>Body copy with an em dash — right here.</p>
  <a class="cta" href="#">Get started</a></section>
<section><h2>Second</h2><p>More copy.</p></section>
</body></html>"""


def e2e():
    try:
        import websockets  # noqa: F401
    except ImportError:
        print('SKIP  design e2e — `websockets` not installed')
        return
    spec2 = importlib.util.spec_from_file_location('cdp_run', os.path.join(SCRIPTS, 'cdp-run.py'))
    cdp = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(cdp)
    chrome = next((p for p in cdp.CHROME_CANDIDATES if p and os.path.exists(p)), None)
    if not chrome:
        print('SKIP  design e2e — no Chrome found')
        return

    work = tempfile.mkdtemp()
    with open(os.path.join(work, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(FIXTURE)
    port = free_port()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=work, **kw)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        r = subprocess.run([sys.executable, GATE, f'http://127.0.0.1:{port}/',
                            '--width', '1440', '--json', '--settle', '1'],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', env=env, timeout=180)
        data = json.loads(r.stdout) if r.stdout.strip().startswith('{') else None
        check('the real probe returns a result', data is not None, (r.stderr or '')[-400:])
        if not data:
            return
        joined = ' | '.join(data['failures'])
        check('a fixture built to fail exits non-zero', r.returncode != 0, r.returncode)
        check('the em-dash in the fixture copy is found', 'em-dashes' in joined, joined)
        check('the two-line nav is found', 'one line' in joined or 'navigation' in joined, joined)
        check('the 1.1:1 CTA is found', 'WCAG' in joined, joined)
        check('and the failures carry measured values, not adjectives',
              any(':1' in f or 'px' in f for f in data['failures']), data['failures'])
    finally:
        srv.shutdown()
        shutil.rmtree(work, ignore_errors=True)


e2e()

print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
