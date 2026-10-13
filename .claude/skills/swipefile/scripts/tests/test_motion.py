#!/usr/bin/env python3
"""Motion extraction: does it recover values we planted in a page?

Every assertion below is a number written into the fixture CSS. If the extractor
comes back with something else, the library will be written with something else,
and a rebuild will animate wrong — silently, because a screenshot cannot show it.

Skips cleanly when Chrome or `websockets` is unavailable; this is the one suite
that needs a real browser, because the failures it guards against only happen in
one (a finished transition leaves getAnimations(); load-time animations fire
before a post-load hook exists).
"""
import os, pathlib as _pl, json, shutil, socket, subprocess, sys, tempfile, time
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)

CDP = os.path.join(SCRIPTS, 'cdp-run.py')
SERVE = os.path.join(SCRIPTS, 'serve.py')
EXTRACT = os.path.join(SCRIPTS, 'motion-extract.js')

try:
    import websockets  # noqa: F401
except ImportError:
    print('SKIP  motion — `websockets` not installed (pip install websockets)')
    sys.exit(0)
if not any(os.path.exists(p) for p in (
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium')) and not (
        shutil.which('google-chrome') or shutil.which('chromium')):
    print('SKIP  motion — no Chrome found')
    sys.exit(0)

# Planted values. These are the answers.
DURATION, EASING, STAGGER, TRAVEL = 700, 'cubic-bezier(0.16, 1, 0.3, 1)', 60, '24px'
FIXTURE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0}section{height:1400px;padding:40px}
.card{opacity:0;transform:translateY(24px);
      transition:opacity 700ms cubic-bezier(0.16, 1, 0.3, 1),
                 transform 700ms cubic-bezier(0.16, 1, 0.3, 1)}
.card.visible{opacity:1;transform:translateY(0)}
.card:nth-child(1){transition-delay:0ms}
.card:nth-child(2){transition-delay:60ms}
.card:nth-child(3){transition-delay:120ms}
.card:nth-child(4){transition-delay:180ms}
.card:nth-child(5){transition-delay:240ms}
/* zero-duration transitions are not animations and must not reach the output */
.noise{transition:color 0ms linear}
@keyframes pulse{0%{opacity:1}50%{opacity:.5}100%{opacity:1}}
.spinner{width:24px;height:24px;animation:pulse 1200ms ease-in-out infinite}
/* fires on LOAD, before any post-load hook could exist */
@keyframes heroIn{from{opacity:0}to{opacity:1}}
.hero{animation:heroIn 900ms cubic-bezier(0.16, 1, 0.3, 1) both}
</style></head><body>
<section><h1 class="hero">Hero</h1><div class="spinner"></div><p class="noise">x</p></section>
<section id="grid"><div class="card">A</div><div class="card">B</div><div class="card">C</div>
<div class="card">D</div><div class="card">E</div></section>
<section><h2>Bottom</h2></section>
<script>
document.querySelectorAll('.noise').forEach(n=>requestAnimationFrame(()=>n.style.color='#123'));
document.querySelectorAll('.card').forEach(c=>new IntersectionObserver(es=>es.forEach(e=>{
  if(e.isIntersecting)e.target.classList.add('visible')}),
  {threshold:0.01,rootMargin:'0px 0px -15% 0px'}).observe(c));
</script></body></html>"""


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


root = tempfile.mkdtemp(prefix='motion-test-')
open(os.path.join(root, 'f.html'), 'w').write(FIXTURE)
port = free_port()
srv = subprocess.Popen([sys.executable, SERVE, '--directory', root, '--port', str(port)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}{"  — " + str(detail) if detail and not cond else ""}')


try:
    end = time.time() + 10
    while time.time() < end:
        try: socket.create_connection(('127.0.0.1', port), 0.2).close(); break
        except OSError: time.sleep(0.05)

    r = subprocess.run([sys.executable, CDP, f'http://127.0.0.1:{port}/f.html',
                        EXTRACT, '--pre', EXTRACT, '--width', '1280', '--height', '900',
                        '--settle', '2'], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(r.stderr[-900:]); sys.exit('cdp-run failed')
    d = json.loads(r.stdout)
    A = d['animations']

    check('found the planted animations at all', d['animationsSeen'] >= 11, d['animationsSeen'])
    check('zero-duration transitions filtered out',
          all(a['duration'] for a in A if a['kind'] == 'CSSTransition'),
          [a for a in A if a['kind'] == 'CSSTransition' and not a['duration']])
    check('the filter is reported, not silent', 'zeroDurationDropped' in d)

    cards = [a for a in A if a.get('text') in list('ABCDE')]
    check('all five cards captured', len({a['text'] for a in cards}) == 5,
          sorted({a['text'] for a in cards}))
    check('duration recovered exactly', all(a['duration'] == DURATION for a in cards),
          sorted({a['duration'] for a in cards}))
    check('easing recovered intact, not comma-split',
          all(a['easing'] == EASING for a in cards), sorted({a['easing'] for a in cards}))

    opac = [a for a in cards if a['property'] == 'opacity']
    trans = [a for a in cards if a['property'] == 'transform']
    check('opacity endpoints are opacity',
          all(a['values']['from'].get('opacity') == '0'
              and a['values']['to'].get('opacity') == '1' for a in opac),
          [a['values'] for a in opac[:2]])
    check('transform endpoints are transform, not opacity',
          all(TRAVEL in str(a['values']['from'].get('transform')) for a in trans),
          [a['values'] for a in trans[:2]])

    ladder = next((l for l in d['ladders'] if l['stagger'] == [STAGGER]), None)
    check(f'{STAGGER}ms stagger ladder derived', ladder is not None,
          [l['stagger'] for l in d['ladders']])
    check('delay ladder is the planted one',
          ladder and ladder['delays'] == [0, 60, 120, 180, 240], ladder and ladder['delays'])

    trig = [a['triggerViewportPct'] for a in cards if a['triggerViewportPct'] is not None]
    check('trigger captured as a viewport %, in the lower half',
          trig and all(30 < t < 100 for t in trig), trig[:6])

    hero = [a for a in A if a['name'] == 'heroIn']
    check('LOAD-time animation caught (needs --pre injection)', len(hero) >= 1,
          'no heroIn — hooks installed too late')
    # A native CSS @keyframes animation is visible to BOTH the animationstart
    # event listener and the WAAPI getAnimations() poll. CSSTransition was
    # already excluded from the poll as "covered by events"; CSSAnimation was
    # not, so every @keyframes animation was recorded twice under two
    # differently-typed dedup keys (a string vs. the animation object) — once
    # correctly, once with a silently wrong 'linear' easing from the raw
    # KeyframeEffect option, which is unrelated to the real CSS curve for a
    # browser-parsed @keyframes rule. Measured live on wise.com: this doubled
    # the counted weight of every real curve and manufactured phantom
    # 'linear' entries in the signature-curve tally.
    check('a @keyframes animation is recorded exactly once, not once per '
          'capture path', len(hero) == 1, hero)
    check('load animation carries its real duration',
          all(a['duration'] == 900 for a in hero), [a['duration'] for a in hero])
    # heroIn is a @keyframes animation, reported via the animationstart event
    # path — a SEPARATE code path from the CSS-transition cards above, and one
    # that independently re-broke the exact bug splitTop() exists to prevent:
    # naive split(',')[0] tore this same 4-parameter curve at its first
    # internal comma, reporting 'cubic-bezier(0.16' on a real capture and
    # shipping a truncated, invalid signature curve. Nothing above this line
    # asserts hero's easing at all, which is how it shipped unnoticed.
    check('load animation easing recovered intact, not comma-split at an '
          'internal cubic-bezier parameter',
          all(a['easing'] == EASING for a in hero), [a['easing'] for a in hero])

    loop = [a for a in A if a['name'] == 'pulse']
    check('infinite loop captured and marked infinite',
          loop and str(loop[0]['iterations']) == 'infinite', loop and loop[0].get('iterations'))
    check('reduced-motion state reported', 'mediaQueryPresent' in d['reducedMotion'])
finally:
    srv.terminate(); srv.wait(timeout=5)
    shutil.rmtree(root, ignore_errors=True)

print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL)); sys.exit(1)
