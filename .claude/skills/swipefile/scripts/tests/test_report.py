#!/usr/bin/env python3
"""Replication report: does it refuse to call an unmeasured build done?

The report existed as prose for the whole life of the Match path, and prose is
what this skill has already measured as not holding. So the cases that matter
here are not the happy path — they are the three ways a hand-written report
lies: a metric quietly omitted, a gate asserted over a number nobody read, and
a similarity score computed against placeholder content.
"""
import json, os, pathlib as _pl, shutil, subprocess, sys, tempfile
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
REPORT = os.path.join(SCRIPTS, 'report.py')

# Both sides agree: same face count, same check() per face, widths within 1px,
# and the reference's A/B gap reproduced on the mirror.
FONTS_AGREE = {
    'reference': {'faces': 67,
                  'checks': [{'family': 'Satoshi', 'weight': '700', 'ok': True},
                             {'family': 'Inter', 'weight': '400', 'ok': False}],
                  'widths': [{'family': 'Satoshi', 'real': 1183.3, 'fallback': 1208.3}]},
    'mirror': {'faces': 67,
               'checks': [{'family': 'Satoshi', 'weight': '700', 'ok': True},
                          {'family': 'Inter', 'weight': '400', 'ok': False}],
               'widths': [{'family': 'Satoshi', 'real': 1183.9, 'fallback': 1208.1}]},
}

BASE = {
    'fidelity': {
        'text_pct': 100, 'text_chars': 48210,
        'geometry': {'boxes': 120, 'exact': 120, 'worst_delta_px': 0},
        'pixel': [{'breakpoint': 1440, 'similarity_pct': 99.2, 'self_ceiling_pct': 99.4}],
        'pixel_by_page': [],
        'fonts': FONTS_AGREE,
    },
    'integrity': {'origin_refs_remaining': 0, 'off_origin_requests': 0,
                  'markup_changes_unexplained': 0, 'decode_size_mismatches': 0},
    'runtime': {'failed_requests': 0, 'live_surfaces': {}},
    'motion': {'mechanism': 'two-class reveal gate'},
    'placeholder_content': False,
    'honesty': {'excluded': [], 'unresolved': ['none']},
}

BUILD_MANIFEST = {
    'origin': 'https://example.com', 'out': 'site', 'cdn': 'cdn',
    'pages': [{'slug': 'index.html', 'url': 'https://example.com/'}],
    'assets': {'mirrored': 412, 'bytes': 18_400_000, 'problems': 0,
               'origin_404s': [{'url': 'https://example.com/gone.png', 'why': 'HTTP 404'}],
               'content_type_mismatches': 0, 'failures': {}},
    'links': {'wired': 88, 'inert': 12, 'missing_targets': 0, 'missing_target_slugs': [],
              'bare_hash_hrefs': 0},
    'markup_changes': {'url-relocalisation': 1186, 'sri-strip': 2, 'href-inert': 12,
                       'href-wired': 88, 'form-inert': 1, 'stamp': 1},
}

CRAWL_MANIFEST = {'origin': 'https://example.com',
                  'pages': [{'url': 'https://example.com/', 'slug': 'index.html'}],
                  'skipped': {'https://example.com/blog/1': 'excluded by pattern'},
                  'urlmap': {}, 'sitemap_only': ['https://example.com/blog/1'],
                  'crawl_only': []}

root = tempfile.mkdtemp(prefix='report-test-')
PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:400] if detail and not cond else ""}')


def setpath(obj, path, value):
    """Copy of obj with a dotted path replaced. Never mutates the fixture."""
    out = json.loads(json.dumps(obj))
    cur = out
    parts = path.split('.')
    for p in parts[:-1]:
        cur = cur[p]
    cur[parts[-1]] = value
    return out


def run(measured=None, *args, files=None):
    """Run report.py in a fresh directory. Returns (code, output, report_json)."""
    work = tempfile.mkdtemp(dir=root)
    argv = [sys.executable, REPORT, '--site', 'example.com', '--date', '2026-08-06']
    if measured is not None:
        json.dump(measured, open(os.path.join(work, 'measurements.json'), 'w'))
        argv += ['--measured', 'measurements.json']
    for flag, payload in (files or {}).items():
        name = f'{flag}.json'
        json.dump(payload, open(os.path.join(work, name), 'w'))
        argv += [f'--{flag}', name]
    r = subprocess.run(argv + list(args), cwd=work, capture_output=True, text=True)
    out = r.stdout + r.stderr
    data = None
    p = os.path.join(work, 'report.json')
    if os.path.exists(p):
        data = json.load(open(p))
    return r.returncode, out, data


def status_of(data, needle):
    for g in (data or {}).get('gates', {}).get('detail', []):
        if needle in g['gate']:
            return g['status']
    return None


# ---- omission is a failure, and the refusal is actionable
code, out, data = run(None)
check('refuses to report with no measurements at all', code == 2, out[-300:])
check('names the missing keys', 'fidelity.text_pct' in out and 'placeholder_content' in out, out)
check('prints how to obtain a missing metric', 'font-gate.js' in out, out)
check('points at --init', '--init' in out, out[-300:])

code, out, data = run(setpath(BASE, 'placeholder_content', None) and
                      {k: v for k, v in BASE.items() if k != 'placeholder_content'})
check('a single omitted key still refuses', code == 2, out[-200:])
check('the refusal names only what is missing',
      'placeholder_content' in out and 'fidelity.text_pct' not in out, out)

# ---- the happy path
code, out, data = run(BASE, files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                                   'copy': {'pass': True, 'failures': []},
                                   'motion': {'pass': True, 'failures': [], 'coverage': 0.98}})
check('a fully measured clean build passes', code == 0, out[-600:])
check('report.json written', data is not None)
check('REPORT.md written', 'REPORT.md' in out, out[-200:])
check('every gate passes on the clean build',
      data and data['gates']['passed'] and not data['gates']['failing'],
      data and data['gates']['failing'])
check('build manifest feeds the assets block',
      data and data['integrity']['assets']['mirrored'] == 412
      and data['integrity']['assets']['bytes'] == 18_400_000)
check("origin 404s recorded separately from our own defects",
      data and len(data['integrity']['assets']['origin_404s']) == 1
      and data['integrity']['assets']['problems'] == 0)
check('crawl manifest feeds the scope block',
      data and data['scope']['built'] == 1 and data['scope']['sitemap_only'])
check('markup changes classified from the build manifest',
      data and data['integrity']['markup_changes']['classified'] == 1290,
      data and data['integrity']['markup_changes'])

# ---- scope.built must count real files, not the crawler's raw queue.
# crawl.py records one manifest entry per URL it fetched; a query-string
# variant of an already-captured page (?region=PH vs ?region=SG on the same
# fee-history page) is a distinct manifest entry there, but build.py's
# slug-based dedup collapses it to the same file. Measured live on a 174-page
# crawl: 32 of those were never distinct files, and scope.built read 174.
dedup_crawl = {**CRAWL_MANIFEST,
              'pages': [{'url': 'https://example.com/', 'slug': 'index.html'},
                        {'url': 'https://example.com/?ref=a', 'slug': 'index.html'},
                        {'url': 'https://example.com/?ref=b', 'slug': 'index.html'},
                        {'url': 'https://example.com/about', 'slug': 'about.html'}]}
dedup_build = {**BUILD_MANIFEST,
              'pages': [{'slug': 'index.html', 'url': 'https://example.com/'},
                        {'slug': 'about.html', 'url': 'https://example.com/about'}]}
code, out, data = run(BASE, files={'build': dedup_build, 'crawl': dedup_crawl,
                                   'copy': {'pass': True}, 'motion': {'pass': True}})
check("scope.built counts unique files build.py wrote, not the crawler's raw "
      'queue (4 manifest entries, 2 real files)',
      data and data['scope']['built'] == 2, data and data['scope'])

# ---- unmeasured is reported, never passed — and does not block by default
UNMEASURED = setpath(BASE, 'integrity.origin_refs_remaining',
                     'not measured — no browser available')
GATE_INPUTS = {'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
               'copy': {'pass': True}, 'motion': {'pass': True},
               'design': {'pass': True}}
code, out, data = run(UNMEASURED, files=GATE_INPUTS)
check('an unmeasured gated metric does not block by default', code == 0, out[-400:])
check('and is reported UNVERIFIED, not passed',
      status_of(data, 'origin refs remaining') == 'UNVERIFIED', status_of(data, 'origin refs'))
check('the headline refuses to read as a clean pass',
      'UNVERIFIED' in out and 'PASS, 1 UNVERIFIED' in out, out[-400:])
check('the unverified gates are listed in report.json, not merged into failing',
      data and data['gates']['unverified'] == ['origin refs remaining = 0']
      and not data['gates']['failing'], data and data['gates'])
check('the reader is told not to call this verified',
      'do not describe this build as verified' in out, out[-400:])
check('and is pointed at --strict', '--strict' in out, out[-300:])

code, out, data = run(UNMEASURED, '--strict', files=GATE_INPUTS)
check('--strict makes an unverified gate blocking', code != 0, out[-300:])
check('--strict does not print PASS while exiting non-zero',
      'REPLICATION GATE: NOT DONE' in out and 'GATE: PASS' not in out, out[-300:])
check('--strict is recorded in report.json', data and data['gates']['strict'] is True)
check('--strict does not invent a failure — it is still UNVERIFIED, not FAIL',
      data and not data['gates']['failing']
      and status_of(data, 'origin refs remaining') == 'UNVERIFIED', data and data['gates'])

code, out, data = run(BASE)          # no --copy, --motion or --design supplied
check('an absent sub-gate is unverified, not assumed clean',
      status_of(data, 'motion gate') == 'UNVERIFIED'
      and status_of(data, 'content gate') == 'UNVERIFIED'
      and status_of(data, 'design gate') == 'UNVERIFIED',
      data and data['gates']['failing'])
check('a REPORT.md with unverified gates says so in its headline',
      data and data['gates']['unverified'], data and data['gates'])

# ---- placeholder content voids the score outright
code, out, data = run(setpath(BASE, 'placeholder_content', True),
                      files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                             'copy': {'pass': True}, 'motion': {'pass': True}})
check('a similarity score over placeholder content fails outright',
      status_of(data, 'placeholder content') == 'FAIL', status_of(data, 'placeholder'))
check('placeholder content blocks the whole report', code != 0)

# ---- the font gate is two-sided, and both-false is a pass
both_false = json.loads(json.dumps(FONTS_AGREE))
for side in ('reference', 'mirror'):
    both_false[side]['checks'] = [{'family': 'Inter', 'weight': '400', 'ok': False}]
    both_false[side]['widths'] = []
code, out, data = run(setpath(BASE, 'fidelity.fonts', both_false),
                      files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                             'copy': {'pass': True}, 'motion': {'pass': True}})
check('check()=false on BOTH sides is declared-but-unused: a pass',
      status_of(data, 'font gate') == 'pass', data and data['fidelity']['fonts'])

disagree = setpath(FONTS_AGREE, 'mirror.checks',
                   [{'family': 'Satoshi', 'weight': '700', 'ok': False},
                    {'family': 'Inter', 'weight': '400', 'ok': False}])
code, out, data = run(setpath(BASE, 'fidelity.fonts', disagree),
                      files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                             'copy': {'pass': True}, 'motion': {'pass': True}})
check('a check() that differs between the two sides fails',
      status_of(data, 'font gate') == 'FAIL')
check('the disagreement is named, not just counted',
      data and any('Satoshi' in d for d in data['fidelity']['fonts']['disagreements']),
      data and data['fidelity']['fonts']['disagreements'])

# The silent fallback: the reference paints a real face (25px A/B gap), the
# mirror's widths are identical to its fallback. check() and computed
# fontFamily both report success here; only the A/B arm catches it.
fallback = setpath(FONTS_AGREE, 'mirror.widths',
                   [{'family': 'Satoshi', 'real': 1208.3, 'fallback': 1208.3}])
code, out, data = run(setpath(BASE, 'fidelity.fonts', fallback),
                      files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                             'copy': {'pass': True}, 'motion': {'pass': True}})
check('a silent fallback on the mirror fails the font gate',
      status_of(data, 'font gate') == 'FAIL')
check('and is named as a silent fallback',
      data and any('silent fallback' in d for d in data['fidelity']['fonts']['disagreements']),
      data and data['fidelity']['fonts']['disagreements'])

# Two empty sides agree trivially. That is a probe that never ran, and the
# --init skeleton is exactly this shape — it must not hand back a passing gate.
empty = {'reference': {'faces': 0, 'checks': [], 'widths': []},
         'mirror': {'faces': 0, 'checks': [], 'widths': []}}
code, out, data = run(setpath(BASE, 'fidelity.fonts', empty),
                      files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                             'copy': {'pass': True}, 'motion': {'pass': True}})
check('two empty font sides do not agree their way to a pass',
      status_of(data, 'font gate') == 'UNVERIFIED', status_of(data, 'font gate'))
check('and the refusal names the probe to run',
      data and any('font-gate.js' in d for d in data['fidelity']['fonts']['disagreements']),
      data and data['fidelity']['fonts']['disagreements'])

code, out, data = run(setpath(BASE, 'fidelity.fonts', 'not measured — no Chrome on this box'),
                      files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                             'copy': {'pass': True}, 'motion': {'pass': True}})
check('an unmeasured font gate is unverified, not passed',
      status_of(data, 'font gate') == 'UNVERIFIED')

# ---- the ceiling gate, which is what stops "99% is basically done"
near = setpath(BASE, 'fidelity.pixel',
               [{'breakpoint': 1440, 'similarity_pct': 99.1, 'self_ceiling_pct': 99.4}])
code, out, data = run(near, files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                                   'copy': {'pass': True}, 'motion': {'pass': True}})
check('0.3 below its own ceiling passes', status_of(data, 'own ceiling') == 'pass')

far = setpath(BASE, 'fidelity.pixel',
              [{'breakpoint': 1440, 'similarity_pct': 98.7, 'self_ceiling_pct': 99.4}])
code, out, data = run(far, files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                                  'copy': {'pass': True}, 'motion': {'pass': True}})
check('0.7 below its own ceiling fails', status_of(data, 'own ceiling') == 'FAIL')
check('a high score under its ceiling still blocks the report', code != 0)

# "Nothing is below its ceiling" is trivially true of an empty list. Vacuous
# truth is the quietest false pass there is.
for empty_pixel, label in (([], 'an empty pixel list'),
                           ([{'breakpoint': 1440, 'similarity_pct': 'not measured — ',
                              'self_ceiling_pct': None}], 'rows carrying no number')):
    code, out, data = run(setpath(BASE, 'fidelity.pixel', empty_pixel),
                          files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                                 'copy': {'pass': True}, 'motion': {'pass': True}})
    check(f'{label} does not pass the ceiling gate vacuously',
          status_of(data, 'own ceiling') == 'UNVERIFIED', status_of(data, 'own ceiling'))
    check(f'{label} does not pass the floor gate vacuously',
          status_of(data, 'floor') == 'UNVERIFIED', status_of(data, 'floor'))

low = setpath(BASE, 'fidelity.pixel',
              [{'breakpoint': 1440, 'similarity_pct': 92.0, 'self_ceiling_pct': None}])
code, out, data = run(low, files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                                  'copy': {'pass': True}, 'motion': {'pass': True}})
check('below the 95% floor fails even with no ceiling measured',
      status_of(data, 'floor') == 'FAIL')

# ---- scope: a sitemap URL neither built nor explained
unlisted = json.loads(json.dumps(CRAWL_MANIFEST))
unlisted['sitemap_only'] = ['https://example.com/blog/1', 'https://example.com/orphan']
code, out, data = run(BASE, files={'build': BUILD_MANIFEST, 'crawl': unlisted,
                                   'copy': {'pass': True}, 'motion': {'pass': True}})
check('a sitemap URL neither built nor given a reason fails',
      status_of(data, 'sitemap URL') == 'FAIL', data and data['scope'])
check('the explained one is not counted against it',
      data and data['scope']['unlisted'] == ['https://example.com/orphan'],
      data and data['scope']['unlisted'])

# ---- sub-gate failures propagate
code, out, data = run(BASE, files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
                                   'copy': {'pass': True},
                                   'motion': {'pass': False,
                                              'failures': ['NO prefers-reduced-motion']}})
check('a failing motion gate fails the report', status_of(data, 'motion gate') == 'FAIL')
check('and its reason is carried into the report',
      data and 'NO prefers-reduced-motion' in data['motion']['failures'][0])

# The design gate is the taste pre-flight's mechanical half. A failing one has
# to block for the same reason the motion gate does: a still screenshot cannot
# see a 2.1:1 CTA or a two-line nav, so a pixel score of 99% reads as done over
# a page that fails its own house rules.
code, out, data = run(BASE, files={
    'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST,
    'copy': {'pass': True}, 'motion': {'pass': True},
    'design': {'pass': False, 'failures': ['every CTA clears WCAG AA: "Buy" 2.1:1'],
               'warnings': ['no duplicate CTA intent: contact']}})
check('a failing design gate fails the report', status_of(data, 'design gate') == 'FAIL')
check('and the report exits non-zero on it', code != 0, out[-300:])
check('the design failure is carried, not summarised away',
      data and '2.1:1' in data['design']['failures'][0], data and data['design'])
check('design warnings are kept apart from design failures',
      data and data['design']['warnings'] and not data['gates']['unverified'][:1] == ['design'],
      data and data['design'])

# ---- link integrity comes from the build, not from a promise
broken = setpath(BUILD_MANIFEST, 'links',
                 {'wired': 88, 'inert': 12, 'missing_targets': 3,
                  'missing_target_slugs': ['a.html'], 'bare_hash_hrefs': 0})
code, out, data = run(BASE, files={'build': broken, 'crawl': CRAWL_MANIFEST,
                                   'copy': {'pass': True}, 'motion': {'pass': True}})
check('missing link targets from the build manifest fail the gate',
      status_of(data, 'links:') == 'FAIL')

bare = setpath(BUILD_MANIFEST, 'links',
               {'wired': 88, 'inert': 12, 'missing_targets': 0,
                'missing_target_slugs': [], 'bare_hash_hrefs': 4})
code, out, data = run(BASE, files={'build': bare, 'crawl': CRAWL_MANIFEST,
                                   'copy': {'pass': True}, 'motion': {'pass': True}})
check('a surviving bare # href fails the gate', status_of(data, 'links:') == 'FAIL')

# ---- --init produces a skeleton that satisfies the schema but passes nothing
work = tempfile.mkdtemp(dir=root)
r = subprocess.run([sys.executable, REPORT, '--init'], cwd=work, capture_output=True, text=True)
skel = os.path.join(work, 'measurements.json')
check('--init writes measurements.json', os.path.exists(skel), r.stdout + r.stderr)
if os.path.exists(skel):
    code, out, data = run(json.load(open(skel)),
                          files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST})
    check('the skeleton satisfies the omission check (every key present)', code != 2, out[-300:])
    check('a blank skeleton invents no failure — nothing measured means nothing failed',
          data and not data['gates']['failing'], data and data['gates']['failing'])
    check('but it claims no pass either: the unfilled metrics are UNVERIFIED',
          data and len(data['gates']['unverified']) >= 8, data and data['gates']['unverified'])
    check('a blank skeleton does not block by default (report first, verify after)',
          code == 0, out[-300:])
    code, out, data = run(json.load(open(skel)), '--strict',
                          files={'build': BUILD_MANIFEST, 'crawl': CRAWL_MANIFEST})
    check('--strict blocks the blank skeleton', code != 0)

# ---- placeholder content, via the shape report.md actually mandates
# report.md requires pixel_by_page "for any multi-page mirror", so a veto that
# reads only fidelity.pixel is blind to every multi-page build.
by_page = setpath(setpath(BASE, 'placeholder_content', True), 'fidelity.pixel', [])
by_page = setpath(by_page, 'fidelity.pixel_by_page',
                  [{'slug': '/', 'breakpoint': 1440, 'similarity_pct': 99.4,
                    'self_ceiling_pct': 99.6}])
code, out, data = run(by_page, files=GATE_INPUTS)
check('a placeholder score hiding in pixel_by_page still fails the veto',
      status_of(data, 'placeholder content') == 'FAIL', status_of(data, 'placeholder'))
check('and it blocks even without --strict', code != 0, out[-300:])
code, out, data = run(setpath(BASE, 'placeholder_content', False), files=GATE_INPUTS)
check('a passing placeholder gate does not read as a violation',
      'computed over placeholder content' not in
      next(g['detail'] for g in data['gates']['detail'] if 'placeholder' in g['gate']),
      next(g['detail'] for g in data['gates']['detail'] if 'placeholder' in g['gate']))

# NaN is a float that compares False against every threshold, so it clears both
# pixel gates and then makes report.json unparseable on the way out.
nan = setpath(BASE, 'fidelity.pixel',
              [{'breakpoint': 1440, 'similarity_pct': float('nan'), 'self_ceiling_pct': 99.4}])
code, out, data = run(nan, files=GATE_INPUTS)
check('NaN is not accepted as a similarity score',
      status_of(data, 'floor') == 'UNVERIFIED', status_of(data, 'floor'))

# ---- the count gates must actually fail on a non-zero count
for path, needle, bad in (('integrity.origin_refs_remaining', 'origin refs', 517),
                          ('integrity.off_origin_requests', 'off-origin', 42),
                          ('runtime.failed_requests', 'failed requests', 23),
                          ('integrity.markup_changes_unexplained', 'unexplained markup', 36),
                          ('integrity.decode_size_mismatches', 'decode-size', 9)):
    code, out, data = run(setpath(BASE, path, bad), files=GATE_INPUTS)
    check(f'a non-zero {needle} count fails', status_of(data, needle) == 'FAIL',
          status_of(data, needle))

# ---- the three rows report.md gates that the code used to ignore
code, out, data = run(setpath(BASE, 'fidelity.text_pct', 41.2), files=GATE_INPUTS)
check('a mirror-path Match with a 41% text layer fails',
      status_of(data, 'text layer') == 'FAIL', status_of(data, 'text layer'))
code, out, data = run(setpath(BASE, 'fidelity.text_pct', 41.2), '--path', 'rebuild',
                      files=GATE_INPUTS)
check('the text gate is n/a off the mirror path, not a silent pass claim',
      status_of(data, 'text layer') == 'pass'
      and 'n/a' in next(g['detail'] for g in data['gates']['detail'] if 'text layer' in g['gate']))

drift = setpath(setpath(BASE, 'fidelity.geometry',
                        {'boxes': 120, 'exact': 3, 'worst_delta_px': 847}),
                'honesty.unresolved', [])
code, out, data = run(drift, files=GATE_INPUTS)
check('an unexplained geometry delta fails', status_of(data, 'geometry') == 'FAIL',
      status_of(data, 'geometry'))
code, out, data = run(setpath(drift, 'honesty.unresolved', ['hero randomises per load']),
                      files=GATE_INPUTS)
check('the same delta passes once the unresolved row explains it',
      status_of(data, 'geometry') == 'pass', status_of(data, 'geometry'))
geo_detail = next(g['detail'] for g in data['gates']['detail'] if 'geometry' in g['gate'])
check('a PASSING geometry gate does not claim the unresolved row is empty '
      '(it is the reason the gate passed)',
      'is empty' not in geo_detail and 'explained in honesty.unresolved' in geo_detail,
      geo_detail)

probs = setpath(BUILD_MANIFEST, 'assets',
                {**BUILD_MANIFEST['assets'], 'problems': 5})
code, out, data = run(BASE, files={**GATE_INPUTS, 'build': probs})
check('asset integrity problems fail the gate',
      status_of(data, 'asset integrity') == 'FAIL', status_of(data, 'asset integrity'))

# ---- the font gate's three arms, each independently
faces = setpath(FONTS_AGREE, 'mirror.faces', 12)
code, out, data = run(setpath(BASE, 'fidelity.fonts', faces), files=GATE_INPUTS)
check('unequal document.fonts.size fails the font gate',
      status_of(data, 'font gate') == 'FAIL', data and data['fidelity']['fonts'])
one_sided = setpath(FONTS_AGREE, 'mirror.checks',
                    [{'family': 'Satoshi', 'weight': '700', 'ok': True}])
code, out, data = run(setpath(BASE, 'fidelity.fonts', one_sided), files=GATE_INPUTS)
check('a face checked on only one side fails the font gate',
      status_of(data, 'font gate') == 'FAIL', data and data['fidelity']['fonts'])
wide = setpath(FONTS_AGREE, 'mirror.widths',
               [{'family': 'Satoshi', 'real': 1195.0, 'fallback': 1208.3}])
code, out, data = run(setpath(BASE, 'fidelity.fonts', wide), files=GATE_INPUTS)
check('a canvas width past tolerance fails the font gate',
      status_of(data, 'font gate') == 'FAIL', data and data['fidelity']['fonts'])

# ---- a pipe in a free-text reason must not shred the markdown table
work = tempfile.mkdtemp(dir=root)
piped = setpath(BASE, 'integrity.off_origin_requests',
                'not measured — fonts | analytics still proxied')
json.dump(piped, open(os.path.join(work, 'm.json'), 'w'))
subprocess.run([sys.executable, REPORT, '--site', 'x', '--measured', 'm.json',
                '--single-page'], cwd=work, capture_output=True, text=True)
gate_row = next(l for l in open(os.path.join(work, 'REPORT.md')) if 'off-origin' in l)
check('a pipe inside a gate detail does not add a cell to the table',
      gate_row.count('|') == 4, gate_row)

# ---- the report leads with the verdict rather than burying it
work = tempfile.mkdtemp(dir=root)
json.dump(BASE, open(os.path.join(work, 'm.json'), 'w'))
json.dump(BUILD_MANIFEST, open(os.path.join(work, 'b.json'), 'w'))
json.dump({'pass': True}, open(os.path.join(work, 'c.json'), 'w'))
json.dump({'pass': True}, open(os.path.join(work, 'mo.json'), 'w'))
subprocess.run([sys.executable, REPORT, '--site', 'example.com', '--measured', 'm.json',
                '--build', 'b.json', '--copy', 'c.json', '--motion', 'mo.json',
                '--single-page'], cwd=work, capture_output=True, text=True)
md = open(os.path.join(work, 'REPORT.md')).read()
check('REPORT.md states the verdict in its first lines', 'PASS' in md.split('\n')[2], md[:200])
check('--single-page is a declared scope, not a silent default',
      '1 built' in md, md[:600])

shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
