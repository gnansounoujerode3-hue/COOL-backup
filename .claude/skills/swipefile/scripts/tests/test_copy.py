#!/usr/bin/env python3
"""Copy / SEO / GEO gate: does it catch slop without crying wolf?

Both directions matter equally. A gate that misses obvious AI copy is useless; a
gate that fails clean copy gets ignored, and an ignored gate is how a correct
rule got skipped three times in one session. So: a deliberately sloppy fixture
must fail on named categories, and a clean fixture must pass with zero prose
findings.
"""
import os, pathlib as _pl, subprocess, sys, tempfile
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
GATE = os.path.join(SCRIPTS, 'copy-gate.py')

HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>Meridian Coffee Roasters, Portland</title>'
        '<meta name="description" content="Small-batch single-origin coffee roasted in southeast '
        'Portland. Subscriptions from 250 grams and a tasting room open Wednesday to Sunday.">'
        '<link rel="canonical" href="https://example.com/">'
        '<meta property="og:title" content="Meridian"><meta property="og:description" content="x">'
        '<meta property="og:image" content="x.jpg">'
        '<script type="application/ld+json">{"@context":"https://schema.org",'
        '"@type":"LocalBusiness","name":"Meridian","address":"Portland"}</script></head><body>')

CLEAN = HEAD + (
    '<h1>Meridian Coffee Roasters</h1>'
    '<p>We buy single lots and cup every one the Tuesday it lands. Batch 0412 charged at 195C, '
    'first crack at 9:05, dropped at 208C. Subscriptions start at 250 grams. The tasting room is '
    'open Wednesday to Sunday, 7am to 2pm, at 1841 SE Division.</p>'
    '<img src="a.jpg" alt="Roast log for batch 0412"></body></html>')

SLOP = HEAD + (
    '<h1>Elevating Your Coffee Journey</h1>'
    '<p>Meridian stands as a testament to craftsmanship. Our meticulously curated beans are not '
    'just coffee, they are a journey. Experts agree that single-origin represents a turning point, '
    'showcasing the artisanal dedication that defines us. Our bespoke offerings leverage '
    'cutting-edge roasting to unlock a myriad of flavours, underscoring our holistic commitment. '
    'We deliver world-class quality and unparalleled freshness, reflecting a pivotal shift.</p>'
    '<img src="a.jpg" alt="x"></body></html>')

MODERN = HEAD + (
    '<h1>Meridian</h1>'
    "<p>Here's the thing. Coffee is the language of morning. Then we started roasting. "
    'Everything changed. It got better. Much better. The thing is, roasting is not a craft, '
    'but a conversation. Quality becomes a trap when you chase it.</p>'
    '<img src="a.jpg" alt="x"></body></html>')


# 200+ words leaning on one connective phrase. The tic, not the topic.
TIC = HEAD + (
    '<h1>Meridian Coffee Roasters</h1>'
    '<p>We buy single lots rather than blends. We cup on Tuesday rather than Friday, '
    'and we ship on Thursday rather than the following week. The roast log is public '
    'rather than hidden, because a number you can check is worth more than a promise. '
    'Batch 0412 charged at 195C and dropped at 208C, measured rather than estimated. '
    'The tasting room opens Wednesday rather than Monday, and closes at two rather than '
    'five. Subscriptions start at 250 grams rather than a kilo, so a first order is a '
    'trial rather than a commitment. We roast to order rather than to stock, we grind '
    'on request rather than in advance, and we price by weight rather than by bag. '
    'Every lot is named for its farm rather than its region, which is slower to explain '
    'but easier to verify. The cupping scores are posted rather than summarised. '
    'We answer the phone rather than a form, and we deliver by bike rather than by van '
    'wherever the ride is under four miles from the roastery on Division.</p>'
    '<img src="a.jpg" alt="Roast log"></body></html>')

# Same length, repeating its BRAND and PRODUCT names. Legitimate: that is the topic.
TOPIC = HEAD + (
    '<h1>Meridian Coffee Roasters</h1>'
    '<p>Meridian roasts single lots in southeast Portland. The Meridian subscription '
    'ships every two weeks, and the Meridian tasting room is open Wednesday to Sunday. '
    'Our Chelbesa lot is a washed Ethiopian coffee at $22 for 250 grams. The Chelbesa '
    'is floral and bright. Our Huila lot is a Colombian coffee at $19 for 250 grams, '
    'and the Huila is heavier, with cocoa and plum. Add to bag, or add to bag from the '
    'subscription page. Add to bag works the same on every product. Batch 0412 charged '
    'at 195C, hit first crack at 9:05, and dropped at 208C after 11 minutes. Batch 0413 '
    'charged at 197C and dropped at 209C. Every batch is logged, every log is public, '
    'and every bag ships with the roast curve it was roasted on. The roastery is at '
    '1841 SE Division, open from seven in the morning until two in the afternoon, and '
    'the roastery phone is answered by whoever is closest to it.</p>'
    '<img src="a.jpg" alt="Roast log"></body></html>')

NO_SEO = ('<!doctype html><html><head><meta charset="utf-8"></head><body>'
          '<h1>A</h1><h1>B</h1><p>Words here about nothing in particular at all.</p>'
          '<img src="a.jpg"></body></html>')

root = tempfile.mkdtemp(prefix='copy-test-')
def write(name, content):
    p = os.path.join(root, name)
    open(p, 'w', encoding='utf-8').write(content)
    return p

PASS, FAIL = [], []
def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}{"  — " + str(detail) if detail and not cond else ""}')

def run(path, *args):
    r = subprocess.run([sys.executable, GATE, path, *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr

# ---- clean copy must pass cleanly
code, out = run(write('clean.html', CLEAN))
check('clean page passes the gate', code == 0, out[-400:])
check('clean page raises no prose findings',
      not any(l.startswith('  FAIL  ') and l.split()[2].isdigit() for l in out.splitlines()), out)

# ---- slop must fail on named humanizer categories
code, out = run(write('slop.html', SLOP))
check('slop page fails the gate', code != 0)
for cat in ('AI vocabulary', 'promotional language', 'vague attribution',
            'negative parallelism', 'inflated significance', 'superficial -ing'):
    check(f'catches: {cat}', cat in out, out[-500:])
check('routes the fix to the humanizer skill', 'humanizer' in out, out[-300:])

# ---- Match mode must NOT judge captured copy
code, out = run(write('slop2.html', SLOP), '--match')
check('--match skips prose checks (captured copy is not ours to rewrite)',
      'AI vocabulary' not in out, out[-300:])
check('--match says so explicitly', 'Match mode' in out, out[-300:])
check('--match still passes when only prose was wrong', code == 0, out[-300:])

# ---- the tells that actually date a 2026 page (humanizer 31-33)
code, out = run(write('modern.html', MODERN))
check('modern-tell page fails', code != 0)
for cat in ('staccato drama', 'rhetorical opener', 'aphorism formula'):
    check(f'catches: {cat}', cat in out, out[-400:])

# ---- repetition: the writer's crutch, not the page's subject
code, out = run(write('tic.html', TIC))
check('catches a crutch phrase repeated across the page',
      'repetition' in out and 'rather than' in out, out[-500:])
check('repetition only warns, never fails the gate',
      not any(l.startswith('  FAIL') and 'repetition' in l for l in out.splitlines()), out[-400:])

code, out = run(write('topic.html', TOPIC))
check('does NOT fire on a page repeating its brand and products',
      'repetition' not in out, out[-500:])

code, out = run(write('tic2.html', TIC), '--match')
check('--match skips the repetition check too', 'repetition' not in out, out[-300:])

# ---- structural SEO failures
code, out = run(write('noseo.html', NO_SEO))
check('missing title detected', 'no <title>' in out)
check('missing meta description detected', 'no meta description' in out)
check('duplicate h1 detected', '2 <h1>' in out)
check('missing lang detected', 'lang attribute' in out)
check('img without alt detected', 'without alt' in out)
check('missing JSON-LD detected (the GEO gap)', 'no JSON-LD' in out)
check('no-SEO page fails', code != 0)

import shutil; shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL)); sys.exit(1)
