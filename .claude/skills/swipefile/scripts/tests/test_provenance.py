#!/usr/bin/env python3
"""Provenance gate: does it catch fiction without crying wolf on formatting?

The measured failure this suite pins: a local model handed a capture JSON
produced a structurally perfect entry that invented a capture date and dropped
every hex and curve — and library-lint passed it, because that gate protects
the resolver, not the truth. Every fabrication case here is that failure in
one of its shapes; every normalisation case is the false positive that would
get this gate ignored in an unattended retry loop.
"""
import json, os, pathlib as _pl, shutil, subprocess, sys, tempfile
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
GATE = os.path.join(SCRIPTS, 'provenance.py')

CAPTURE = {
    'viewport': '1440x900', 'captured': '2026-08-07', 'path': 'mirror',
    'type': {'families': ['Satoshi 500', 'Instrument Serif 400'],
             'scale': 'clamp() pinned to 1440', 'steps_px': [14, 16, 20, 28, 46]},
    'colour': {'hex': ['#0e0e0e', '#f5f3ef', '#ff6041'], 'system': 'greyscale + accent'},
    'motion': {'easings': [['cubic-bezier(.22,1,.36,1)', 41]],
               'durations_ms': [[300, 38]], 'travel_px': 8, 'stagger_ms': 80,
               'reduced_motion': 'absent'},
    'breakpoints': [810, 1200],
}

CLEAN = """# meridian.test

**Callable as: Meridian** (aliases: meridian)

A coffee site. Captured 2026-08-07 @ 1440x900.

## Type

Satoshi 500 carries the UI, Instrument Serif 400 the display. Scale is clamp()
pinned to 1440: steps 14/16/20/28/46px.

## Colour

#0e0e0e ink on #f5f3ef paper, #ff6041 the single accent. Greyscale + accent.

## Motion

**Motion fidelity: partial**

Signature `cubic-bezier(.22,1,.36,1)` (41 uses) @ 300ms. Travel 8px, stagger
80ms. Breakpoints 810 and 1200. reduced_motion: absent.
"""

root = tempfile.mkdtemp(prefix='provenance-test-')
PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:300] if detail and not cond else ""}')


def run(entry_text, capture=CAPTURE, *args):
    d = tempfile.mkdtemp(dir=root)
    e = os.path.join(d, 'entry.md')
    c = os.path.join(d, 'capture.json')
    open(e, 'w', encoding='utf-8').write(entry_text)
    json.dump(capture, open(c, 'w'))
    r = subprocess.run([sys.executable, GATE, e, c, '--json', *args],
                       capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except Exception:
        data = None
    return r.returncode, r.stdout + r.stderr, data


def fails_of(d):
    return ' || '.join((d or {}).get('failures', []))


# ---- the measured failure, in its exact shape
code, out, data = run(CLEAN)
check('a faithful entry passes', code == 0, fails_of(data))
check('a faithful entry raises no warnings', data and not data['warnings'],
      data and data['warnings'])

fabricated_date = CLEAN.replace('Captured 2026-08-07', 'Captured 2023-11-15')
code, out, data = run(fabricated_date)
check('an invented capture date fails', code != 0)
check('and the date is named as fabricated', '2023-11-15' in fails_of(data), fails_of(data))

dropped = """# meridian.test

**Callable as: Meridian** (aliases: meridian)

Captured 2026-08-07 @ 1440x900.

## Motion

**Motion fidelity: partial**

Smooth entrance animations with elegant easing throughout.
"""
code, out, data = run(dropped)
check('an entry that drops the palette fails', 'DROPPED PALETTE' in fails_of(data),
      fails_of(data))
check('and names every missing colour',
      all(h in fails_of(data) for h in ('#0e0e0e', '#f5f3ef', '#ff6041')), fails_of(data))
check('an entry that drops the signature curve fails',
      'DROPPED CURVES' in fails_of(data), fails_of(data))

# ---- fabricated values by class
code, out, data = run(CLEAN.replace('Travel 8px', 'Travel 8px with 999px sections'))
check('a fabricated px value fails', '999px' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN.replace('#ff6041 the single accent',
                                    '#ff6041 the single accent beside #00ff00'))
check('a fabricated hex fails', '#00ff00' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN + '\nAlso `cubic-bezier(.99,.1,.2,.3)` on hover.\n')
check('a fabricated bezier fails', 'cubic-bezier(0.99' in fails_of(data), fails_of(data))

# ---- normalisation: the false positives that would get the gate ignored
code, out, data = run(CLEAN.replace('@ 300ms', '@ .3s'))
check('.3s equals the measured 300ms', code == 0, fails_of(data))
code, out, data = run(CLEAN.replace('@ 300ms', '@ 0.3s'))
check('0.3s equals the measured 300ms', code == 0, fails_of(data))
code, out, data = run(CLEAN.replace('cubic-bezier(.22,1,.36,1)',
                                    'cubic-bezier(0.22, 1, 0.36, 1)'))
check('bezier formatting variants are the same curve', code == 0, fails_of(data))
code, out, data = run(CLEAN.replace('#ff6041', '#FF6041'))
check('hex case is not a fabrication', code == 0, fails_of(data))
code, out, data = run(CLEAN + '\nThe scale has 5 steps.\n')
check('"5 steps" over a 5-item list is a derived count, not a fabrication',
      code == 0, fails_of(data))
code, out, data = run(CLEAN + '\nTwo palettes share 2 roles across 3 surfaces.\n')
check('small unitless prose counts are ignored', code == 0, fails_of(data))
code, out, data = run(CLEAN + '\n## Gotchas hit while rebuilding\n\n6. A numbered gotcha.\n'
                              '7. Another one.\n')
check('numbered-list markers are not treated as measurements', code == 0, fails_of(data))
code, out, data = run(CLEAN + '\nThe viewport spans 900 of height.\n')
check('a bare number embedded in a capture string (1440x900) is measured', code == 0,
      fails_of(data))
code, out, data = run(CLEAN + '\nThe hero is 900px tall.\n')
check('but claiming a UNIT the capture never measured for it fails — roles matter',
      '900px' in fails_of(data), fails_of(data))

# ---- the collision channels adversarial review drove fiction through.
# Weights, use counts, and list lengths are all in the capture as NUMBERS; the
# question is whether they can masquerade as durations and travel.
code, out, data = run(CLEAN + '\nEntrance delay 500ms with a 0.4s settle.\n')
check('a fabricated duration cannot pass via the font-weight ladder (500/400)',
      '500ms' in fails_of(data) and '0.4s' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN + '\nCards stagger 38ms apart.\n')
check('a fabricated duration cannot pass via a use count (38)',
      '38ms' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN + '\nAutoplay runs 3s.\n')
check('a fabricated duration cannot pass via a 3-item list length',
      '3s' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN + '\nSections rise 41px on entry.\n')
check('a fabricated travel cannot pass via a use count (41)',
      '41px' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN + '\nAccents lean on rgb(46, 80, 41) tints.\n')
check('a fabricated rgb() colour is a colour, not three lucky numbers',
      code != 0, fails_of(data))

# ---- and the false positives the same review proved on real capture shapes
bp = dict(CAPTURE, breakpoints=[810, 1200, 1920])
code, out, data = run(CLEAN + '\nThe widest breakpoint is 1920.\n', bp)
check('a measured 1920 breakpoint is not mistaken for a year', code == 0, fails_of(data))
neg = dict(CAPTURE, motion=dict(CAPTURE['motion'], from_y_px=-24))
code, out, data = run(CLEAN + '\nCards start at translateY(-24px).\n', neg)
check('a negative measured value is citable', code == 0, fails_of(data))
frac = dict(CAPTURE, motion=dict(CAPTURE['motion'], scroll_start=0.1))
code, out, data = run(CLEAN + '\nThe scrub starts at 10%.\n', frac)
check('a 0-1 fraction is citable as the percentage TEMPLATE mandates', code == 0,
      fails_of(data))
wide = dict(CAPTURE, type=dict(CAPTURE['type'], hero_vw=8.3333))
code, out, data = run(CLEAN + '\nThe hero is 8.33vw.\n', wide)
check('citing a measured float at fewer digits is rounding, not fabrication',
      code == 0, fails_of(data))
big = dict(CAPTURE, stats={'nodes': 14191})
code, out, data = run(CLEAN + '\nThe DOM holds 14,191 nodes.\n', big)
check('a thousands separator does not split one number into two fabrications',
      code == 0, fails_of(data))
code, out, data = run(CLEAN + '\nOne <source> in the hero just 404s.\n')
check('"404s" is a verb, not a 404-second duration', code == 0, fails_of(data))
code, out, data = run(CLEAN + '\n## Gotchas hit while rebuilding\n\n'
                              '1. First thing.\n    6. Nested at four spaces.\n')
check('numbered lists at 4-space indent are still list markers', code == 0,
      fails_of(data))
rgbcap = dict(CAPTURE, colour={'hex': ['#0e0e0e', '#f5f3ef', '#ff6041'],
                               'computed': 'rgb(29,29,31) on nav'})
code, out, data = run(CLEAN.replace('accent. Greyscale', 'accent beside #1d1d1f. Greyscale'),
                      rgbcap)
check('a colour the capture measured as rgb() is citable as hex', code == 0,
      fails_of(data))
code, out, data = run(CLEAN.replace('Captured 2026-08-07', 'Captured 2026-8-7'))
check('a sloppily-formatted but correct date is not a fabrication', code == 0,
      fails_of(data))
code, out, data = run(CLEAN.replace('Captured 2026-08-07', 'Captured January 2026'))
check('a month-name date with the wrong month fails', code != 0, fails_of(data))
code, out, data = run(CLEAN.replace('Captured 2026-08-07', 'Captured August 2026'))
check('a month-name date with the right month passes', code == 0, fails_of(data))
code, out, data = run(CLEAN + '\nAlso cubic-bezier(999, 777) on exit.\n')
check('a garbled bezier still has its numbers checked, not deleted wholesale',
      code != 0 and ('999' in fails_of(data) or '777' in fails_of(data)), fails_of(data))

# ---- --allow, for values the caller stamped rather than measured
no_date = {k: v for k, v in CAPTURE.items() if k != 'captured'}
code, out, data = run(CLEAN, no_date)
check('a date absent from the capture fails without --allow', code != 0, fails_of(data))
code, out, data = run(CLEAN, no_date, '--allow', '2026-08-07')
check('--allow legitimises the stamped date', code == 0, fails_of(data))
code, out, data = run(CLEAN + '\nSee 365daily notes.\n', CAPTURE, '--allow', '365daily.com')
check('--allow legitimises numbers too, not only dates', code == 0, fails_of(data))

# ---- thinness is a warning, never a failure
thin = """# meridian.test

**Callable as: Meridian** (aliases: meridian)

Captured 2026-08-07 @ 1440x900.

## Colour

#0e0e0e, #f5f3ef, #ff6041.

## Motion

**Motion fidelity: partial**

`cubic-bezier(.22,1,.36,1)`.
"""
code, out, data = run(thin)
check('an entry with full essentials but few numbers still passes', code == 0,
      fails_of(data))
check('but its thinness is warned about',
      any('THIN' in w for w in data['warnings']), data and data['warnings'])

# ---- contract
code, out, data = run(CLEAN)
for key in ('fabricated', 'missingHex', 'missingBezier', 'numberCoverage'):
    check(f'--json carries `{key}`', data and key in data)
r = subprocess.run([sys.executable, GATE, 'nope.md', 'nope.json'],
                   capture_output=True, text=True)
check('unreadable inputs exit 2, not 1', r.returncode == 2, r.stderr)

shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
