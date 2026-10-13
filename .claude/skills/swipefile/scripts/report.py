#!/usr/bin/env python3
"""
The replication report — the definition of done, as an instrument.

`references/report.md` has specified this report for as long as the skill has
had a Match path: seventeen rows, a stable JSON schema, and gates that
decide whether a build is finished. All of it was prose. Prose is the thing
this skill has already measured as not holding: Step 2's motion spec was a
written rule an agent skipped three times in one session, and it stopped being
skipped only when `motion-spec.py` began refusing to return a spec that did not
exist. This is that move applied to Step 4.

It measures nothing itself. It aggregates what the other instruments already
emit, demands the numbers only a browser pass can produce, and refuses to call
a build done on a metric nobody read.

  python3 report.py --init                        # skeleton to fill in
  python3 report.py --site example.com --mode match --path mirror \\
      --crawl crawl-manifest.json --build build-manifest.json \\
      --copy copy.json --motion motion.json --measured measurements.json

Three rules it enforces that a hand-written table routinely bends:

  Omission is a failure.  Every required metric is present or explicitly
                          `not measured — <why>`. A missing key exits non-zero
                          naming the command that produces it.
  Unmeasured is not pass. A gate whose input was never measured is UNVERIFIED.
                          It does not block — an automated mirror should be able
                          to produce a report — but it never reads as cleared,
                          and the headline carries the count. `--strict` makes
                          them blocking, which is what asserting a fully
                          verified Match requires.
  Placeholders void it.   A similarity score over placeholder content is
                          forbidden outright, not footnoted.

Writes REPORT.md and report.json. Exits non-zero on a failing gate, and on an
unverified one only under --strict.
"""
import argparse, json, math, os, sys

MISSING = object()
TOL_PX = 1.0            # font canvas A/B agreement, per references/report.md
CEILING_SLACK = 0.5     # points a page may sit below its own self-diff ceiling
PIXEL_FLOOR = 95.0      # the floor to clear before showing the user anything

# Metrics no script in this folder can produce. Each carries the command or
# procedure that produces it, so a refusal is actionable rather than annoying.
REQUIRED = [
    ('fidelity.text_pct', 'diff the reference DOM text against the built page'),
    ('fidelity.text_chars', 'total characters compared for text_pct'),
    ('fidelity.geometry', 'references/verify.md — same boxes, both sides, one viewport'),
    ('fidelity.pixel', 'headless capture of both sides under identical conditions'),
    ('fidelity.fonts', 'scripts/font-gate.js on the reference AND the mirror'),
    ('integrity.origin_refs_remaining', "grep the built pages for the reference's origin"),
    ('integrity.off_origin_requests',
     "performance.getEntriesByType('resource') on served pages, every breakpoint"),
    ('integrity.markup_changes_unexplained',
     'diff built markup against _raw/ and classify every change'),
    ('integrity.decode_size_mismatches',
     'naturalWidth/naturalHeight per image against the reference'),
    ('runtime.failed_requests', 'network log on load of the built pages'),
    ('placeholder_content',
     'true/false — does any built page carry placeholder or invented content'),
    ('honesty.excluded', 'what was left out, with reason and the command to extend'),
    ('honesty.unresolved', 'deltas whose cause was not found — "none" is a finding'),
]


def dig(obj, path):
    """Value at a dotted path, or MISSING. Never raises on a wrong-shaped input."""
    cur = obj
    for part in path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


def unmeasured(v):
    return isinstance(v, str) and v.strip().lower().startswith('not measured')


def load(path, what):
    if not path:
        return None
    if not os.path.exists(path):
        raise SystemExit(f'{what}: no such file: {path}')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def font_gate(fonts):
    """Two-sided comparison, per references/report.md.

    `false` on both sides is declared-but-never-painted: a pass. Demanding an
    absolute `true` fails byte-accurate mirrors — onefin measured 67 faces on
    both sides with Inter and Fragment Mono false on the reference itself. What
    must hold is that the two sides AGREE.
    """
    if unmeasured(fonts) or not isinstance(fonts, dict):
        return 'unverified', ['font gate not measured']
    ref, mir = fonts.get('reference'), fonts.get('mirror')
    if not isinstance(ref, dict) or not isinstance(mir, dict):
        return 'unverified', ['font gate needs both sides: reference and mirror']
    # Two empty sides agree trivially, and "agreement" over no evidence is the
    # shape of a probe that never ran. A page genuinely on a system stack still
    # produces checks — the census names the families and check() returns false
    # on both sides, which is the declared-but-unpainted pass below.
    if not any(side.get('checks') or side.get('widths') for side in (ref, mir)):
        return 'unverified', ['font gate has no evidence on either side — '
                              'run scripts/font-gate.js on the reference and the mirror']

    bad = []
    if ref.get('faces') != mir.get('faces'):
        bad.append(f"document.fonts.size {ref.get('faces')} vs {mir.get('faces')}")

    def checks(side):
        return {(c.get('family'), str(c.get('weight'))): c.get('ok')
                for c in side.get('checks', [])}

    rc, mc = checks(ref), checks(mir)
    for key in sorted(set(rc) | set(mc), key=lambda k: (str(k[0]), str(k[1]))):
        if key not in rc or key not in mc:
            bad.append(f'{key[0]} {key[1]}: check() run on only one side')
        elif rc[key] != mc[key]:
            bad.append(f'{key[0]} {key[1]}: check() {rc[key]} vs {mc[key]}')

    def widths(side):
        return {w.get('family'): w for w in side.get('widths', [])}

    rw, mw = widths(ref), widths(mir)
    for fam in sorted(set(rw) & set(mw), key=str):
        real_delta = abs(float(rw[fam].get('real', 0)) - float(mw[fam].get('real', 0)))
        if real_delta > TOL_PX:
            bad.append(f'{fam}: canvas width differs by {real_delta:.1f}px '
                       f'(tolerance {TOL_PX}px)')
        # The A/B arm. A gap on the reference and none on the mirror is the
        # silent-fallback signature — computed fontFamily and check() both lie
        # about it, and only this catches it.
        rgap = abs(float(rw[fam].get('real', 0)) - float(rw[fam].get('fallback', 0)))
        mgap = abs(float(mw[fam].get('real', 0)) - float(mw[fam].get('fallback', 0)))
        if rgap > TOL_PX >= mgap:
            bad.append(f'{fam}: reference paints the real face (A/B gap {rgap:.1f}px), '
                       f'mirror does not ({mgap:.1f}px) — silent fallback')
    return ('pass' if not bad else 'fail'), bad


def scope_block(crawl, build, measured, single_page):
    """Built / excluded / sitemap set-difference, from the crawler's own manifest.

    'built' means pages actually WRITTEN TO DISK, which is build.py's page
    list, not crawl.py's raw queue — a query-string variant of an already-
    captured URL (?region=PH vs ?region=SG on the same fee-history page) is
    one real page, but crawl.py records it as a separate manifest entry before
    build.py's slug-based dedup collapses it. Measured live: 174 crawl entries
    collapsed to 142 real files, and the report's own scope line claimed 174
    built when 32 of those were never distinct files at all.
    """
    if crawl:
        skipped = crawl.get('skipped') or {}
        reasons = {}
        for why in skipped.values():
            reasons[why] = reasons.get(why, 0) + 1
        sitemap_only = list(crawl.get('sitemap_only') or [])
        built = len(build.get('pages') or []) if build else len(crawl.get('pages') or [])
        return {'built': built,
                'sitemap_total': built + len(sitemap_only),
                'sitemap_only': sitemap_only,
                'crawl_only': list(crawl.get('crawl_only') or []),
                'unlisted': [u for u in sitemap_only if u not in skipped],
                'excluded': [{'section': why, 'count': n, 'reason': why}
                             for why, n in sorted(reasons.items(), key=lambda kv: -kv[1])]}
    if single_page:
        return {'built': 1, 'sitemap_total': 1, 'sitemap_only': [], 'crawl_only': [],
                'unlisted': [], 'excluded': []}
    supplied = dig(measured, 'scope')
    if supplied is not MISSING:
        return supplied
    return {'built': 'not measured — no crawl manifest supplied',
            'sitemap_total': 'not measured — no crawl manifest supplied',
            'sitemap_only': [], 'crawl_only': [], 'unlisted': [], 'excluded': []}


def assemble(a, crawl, build, copy, motion, design, measured):
    # MISSING is a sentinel for gate logic and must never reach the report
    # itself — an unserializable object here truncates report.json halfway
    # through, which is a worse failure than the missing number it stood for.
    def block(obj, path):
        v = dig(obj or {}, path)
        return v if isinstance(v, dict) else {}

    assets, links = block(build, 'assets'), block(build, 'links')
    changes = block(build, 'markup_changes')
    fonts_raw = dig(measured, 'fidelity.fonts')
    fonts = fonts_raw if isinstance(fonts_raw, dict) else {}
    gate, disagreements = font_gate(fonts_raw)

    def m(path, default=None):
        v = dig(measured, path)
        return default if v is MISSING else v

    classified = sum(v for v in changes.values() if isinstance(v, int)) \
        if changes else 'not measured — no build manifest supplied'
    no_build = 'not measured — no build manifest supplied'
    return {
        'site': a.site, 'date': a.date, 'mode': a.mode, 'path': a.path,
        'scope': scope_block(crawl, build, measured, a.single_page),
        'fidelity': {
            'text_pct': m('fidelity.text_pct'),
            'text_chars': m('fidelity.text_chars'),
            'geometry': m('fidelity.geometry'),
            'pixel': m('fidelity.pixel'),
            'pixel_by_page': m('fidelity.pixel_by_page', []),
            'fonts': {'gate': gate, 'disagreements': disagreements,
                      'reference': fonts.get('reference'), 'mirror': fonts.get('mirror')},
        },
        'integrity': {
            'assets': {
                'mirrored': assets.get('mirrored', no_build),
                'bytes': assets.get('bytes', no_build),
                'problems': assets.get('problems', no_build),
                'origin_404s': assets.get('origin_404s', []),
                'content_type_mismatches': assets.get('content_type_mismatches', no_build),
                'decode_size_mismatches': m('integrity.decode_size_mismatches'),
            },
            'origin_refs_remaining': m('integrity.origin_refs_remaining'),
            'off_origin_requests': m('integrity.off_origin_requests'),
            'links': {
                'wired': links.get('wired', no_build),
                'inert': links.get('inert', no_build),
                'missing_targets': links.get('missing_targets', no_build),
                'bare_hash_hrefs': links.get('bare_hash_hrefs', no_build),
            },
            'markup_changes': {
                'total': (classified + m('integrity.markup_changes_unexplained')
                          if isinstance(classified, int)
                          and isinstance(m('integrity.markup_changes_unexplained'), int)
                          else classified),
                'classified': classified,
                'unexplained': m('integrity.markup_changes_unexplained'),
                'classes': changes,
            },
        },
        'runtime': {'failed_requests': m('runtime.failed_requests'),
                    'live_surfaces': m('runtime.live_surfaces', {})},
        'motion': {'gate': 'pass' if (motion or {}).get('pass') else
                           ('fail' if motion else 'unverified'),
                   'failures': (motion or {}).get('failures', []),
                   'warnings': (motion or {}).get('warnings', []),
                   'coverage': (motion or {}).get('coverage'),
                   'mechanism': m('motion.mechanism', '')},
        'content': {'gate': 'pass' if (copy or {}).get('pass') else
                            ('fail' if copy else 'unverified'),
                    'failures': (copy or {}).get('failures', []),
                    'warnings': (copy or {}).get('warnings', [])},
        # The taste pre-flight's mechanical half. Its own judgement half is not
        # in here and must not be inferred from it — see references/taste.md.
        'design': {'gate': 'pass' if (design or {}).get('pass') else
                           ('fail' if design else 'unverified'),
                   'failures': (design or {}).get('failures', []),
                   'warnings': (design or {}).get('warnings', []),
                   'unverified_checks': (design or {}).get('unverified', []),
                   'coverage': (design or {}).get('coverage')},
        'placeholder_content': m('placeholder_content'),
        'honesty': {'excluded': m('honesty.excluded'), 'unresolved': m('honesty.unresolved')},
    }


def gates(r):
    """The nine gates of references/report.md, plus the two sub-gates.

    Every one returns pass / FAIL / UNVERIFIED. FAIL means measured and wrong;
    UNVERIFIED means nobody looked. Only FAIL blocks by default (--strict blocks
    both), but UNVERIFIED is never folded into pass — the two are different
    claims about the build and the report has to keep them apart.
    """
    out = []

    def gate(name, value, ok, detail=''):
        if unmeasured(value) or value is MISSING:
            out.append({'gate': name, 'status': 'UNVERIFIED',
                        'detail': value if isinstance(value, str) else 'not measured'})
        else:
            out.append({'gate': name, 'status': 'pass' if ok else 'FAIL', 'detail': detail})

    origin_refs = dig(r, 'integrity.origin_refs_remaining')
    gate('origin refs remaining = 0', origin_refs, origin_refs == 0, f'{origin_refs} remaining')
    off = dig(r, 'integrity.off_origin_requests')
    gate('off-origin requests = 0', off, off == 0, f'{off} measured at runtime')
    failed = dig(r, 'runtime.failed_requests')
    gate('failed requests on load = 0', failed, failed == 0, f'{failed} failed')

    missing = dig(r, 'integrity.links.missing_targets')
    bare = dig(r, 'integrity.links.bare_hash_hrefs')
    if unmeasured(missing) or unmeasured(bare):
        gate('links: 0 missing targets, 0 bare # hrefs', 'not measured', False)
    else:
        gate('links: 0 missing targets, 0 bare # hrefs', missing,
             missing == 0 and bare == 0, f'{missing} missing, {bare} bare #')

    unexp = dig(r, 'integrity.markup_changes.unexplained')
    gate('unexplained markup changes = 0', unexp, unexp == 0, f'{unexp} unexplained')

    fg = dig(r, 'fidelity.fonts.gate')
    out.append({'gate': 'font gate: the two sides agree',
                'status': {'pass': 'pass', 'fail': 'FAIL'}.get(fg, 'UNVERIFIED'),
                'detail': '; '.join(dig(r, 'fidelity.fonts.disagreements') or [])})

    ct = dig(r, 'integrity.assets.content_type_mismatches')
    ds = dig(r, 'integrity.assets.decode_size_mismatches')
    if unmeasured(ct) or unmeasured(ds):
        gate('assets: 0 content-type, 0 decode-size mismatches', 'not measured', False)
    else:
        gate('assets: 0 content-type, 0 decode-size mismatches', ct,
             ct == 0 and ds == 0, f'{ct} content-type, {ds} decode-size')

    unlisted = dig(r, 'scope.unlisted')
    built = dig(r, 'scope.built')
    if unmeasured(built) or unlisted is MISSING:
        gate('every sitemap URL built or listed with a reason', 'not measured', False)
    else:
        gate('every sitemap URL built or listed with a reason', built, not unlisted,
             f'{len(unlisted)} sitemap URLs neither built nor explained')

    # Both pixel tables count. report.md mandates `pixel_by_page` for any
    # multi-page mirror, so reading only `pixel` leaves the shape the spec asks
    # for outside every pixel gate — including the placeholder veto, which a
    # 99.4% multi-page score then walked straight through.
    def is_score(v):
        # NaN is a float that compares False against everything, so it clears
        # both thresholds and then makes report.json unparseable on the way out.
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

    pixel, by_page = dig(r, 'fidelity.pixel'), dig(r, 'fidelity.pixel_by_page')
    rows = [p for p in (pixel if isinstance(pixel, list) else [])
            + (by_page if isinstance(by_page, list) else []) if isinstance(p, dict)]
    scored = [p for p in rows if is_score(p.get('similarity_pct'))]

    # Placeholder content voids the pixel number outright — it is not a
    # deduction, it is a forbidden measurement.
    placeholder = dig(r, 'placeholder_content')
    if unmeasured(placeholder) or placeholder is MISSING:
        gate('no similarity score over placeholder content', 'not measured', False)
    else:
        violated = bool(placeholder) and bool(scored)
        gate('no similarity score over placeholder content', placeholder, not violated,
             f'{len(scored)} similarity score(s) computed over placeholder content'
             if violated else 'no placeholder content declared')

    if not scored:
        # An empty list, or rows carrying no usable number, satisfies "nothing is
        # below its ceiling" vacuously. Nothing measured is unverified.
        gate('every page within 0.5 points of its own ceiling', 'not measured', False)
        gate(f'pixel similarity >= {PIXEL_FLOOR}% floor', 'not measured', False)
    else:
        below, under_floor = [], []
        for p in scored:
            sim, ceil = p['similarity_pct'], p.get('self_ceiling_pct')
            if is_score(ceil) and sim < ceil - CEILING_SLACK:
                below.append(f"{p.get('slug') or p.get('breakpoint')}: {sim} vs ceiling {ceil}")
            if sim < PIXEL_FLOOR:
                under_floor.append(f"{p.get('slug') or p.get('breakpoint')}: {sim}%")
        gate('every page within 0.5 points of its own ceiling', pixel, not below,
             '; '.join(below))
        gate(f'pixel similarity >= {PIXEL_FLOOR}% floor', pixel, not under_floor,
             '; '.join(under_floor))

    # references/report.md assigns each of these a Gate in its table. Without
    # them the report prints "every gate cleared" over a 41% text layer.
    text_pct = dig(r, 'fidelity.text_pct')
    if not (r['mode'] == 'match' and str(r['path']).startswith('mirror')):
        out.append({'gate': 'text layer 100% (mirror-path Match)', 'status': 'pass',
                    'detail': f"n/a — mode {r['mode']}, path {r['path']}"})
    else:
        gate('text layer 100% (mirror-path Match)', text_pct, text_pct == 100,
             f'{text_pct}% of characters identical to the reference')

    geo, unresolved = dig(r, 'fidelity.geometry'), dig(r, 'honesty.unresolved')
    if unmeasured(geo) or not isinstance(geo, dict):
        gate('geometry: worst delta zero or explained', 'not measured', False)
    else:
        worst = geo.get('worst_delta_px')
        explained = bool(unresolved) and not unmeasured(unresolved)
        if worst == 0:
            detail = 'worst delta 0px'
        elif explained:
            detail = (f'worst delta {worst}px, explained in honesty.unresolved '
                      f'({len(unresolved)} entr{"y" if len(unresolved) == 1 else "ies"})')
        else:
            detail = (f'worst delta {worst}px and honesty.unresolved is empty — '
                      f'a delta with no stated cause is not an explained one')
        gate('geometry: worst delta zero or explained', worst, worst == 0 or explained, detail)

    problems = dig(r, 'integrity.assets.problems')
    gate('asset integrity problems = 0', problems, problems == 0, f'{problems} problems')

    for name, key in (('motion gate: 0 failures', 'motion'),
                      ('content gate: 0 failures', 'content'),
                      ('design gate: 0 failures', 'design')):
        status = dig(r, f'{key}.gate')
        out.append({'gate': name,
                    'status': {'pass': 'pass', 'fail': 'FAIL'}.get(status, 'UNVERIFIED'),
                    'detail': '; '.join(dig(r, f'{key}.failures') or [])})
    return out


def verdict(g, strict=False):
    """Failing, unverified, and the headline they add up to.

    An unverified gate does not block, but it must never read as a cleared one:
    a report that says PASS over metrics nobody measured is the exact adjective-
    trusting handover the report exists to replace.
    """
    failed = [x for x in g if x['status'] == 'FAIL']
    unverified = [x for x in g if x['status'] == 'UNVERIFIED']
    if failed:
        head = (f'**NOT DONE — {len(failed)} gate(s) failing'
                + (f', {len(unverified)} unverified' if unverified else '') + '.**')
    elif unverified and strict:
        head = (f'**NOT DONE — {len(unverified)} gate(s) UNVERIFIED, and --strict '
                f'makes unverified blocking.** Measure them, or drop --strict and '
                f'ship a report that names what it could not check.')
    elif unverified:
        head = (f'**PASS on {len(g) - len(unverified)} gates — {len(unverified)} UNVERIFIED.** '
                'Every gate that was measured cleared. The unverified ones were not '
                'measured, so this is not a fully verified replication.')
    else:
        head = '**PASS — every gate cleared, every gate measured.**'
    return failed, unverified, head


def render(r, g, strict=False):
    failed, unverified, head = verdict(g, strict)
    bad = [x for x in g if x['status'] != 'pass']
    lines = [f"# Replication report — {r['site']}", '', head, '']
    if bad:
        lines += ['| Gate | Status | Detail |', '|---|---|---|']
        lines += [f"| {x['gate']} | {x['status']} | "
                  f"{str(x['detail'] or '').replace('|', '/')} |" for x in bad]
        lines.append('')
    lines += [f"Mode `{r['mode']}` · path `{r['path']}` · {r['date']}", '',
              '| Group | Check | Reported |', '|---|---|---|']
    f, i = r['fidelity'], r['integrity']
    rows = [
        ('Scope', 'Pages built', f"{r['scope']['built']} built, "
                                 f"{len(r['scope']['sitemap_only'])} in sitemap only"),
        ('Fidelity', 'Text layer', f"{f['text_pct']}% of {f['text_chars']} chars"),
        ('Fidelity', 'Geometry', str(f['geometry'])),
        ('Fidelity', 'Pixel diff', str(f['pixel'])),
        ('Fidelity', 'Fonts', f"{f['fonts']['gate']}" +
         (f" — {'; '.join(f['fonts']['disagreements'])}" if f['fonts']['disagreements'] else '')),
        ('Integrity', 'Assets', f"{i['assets']['mirrored']} mirrored, {i['assets']['bytes']} bytes, "
                                f"{i['assets']['problems']} problems, "
                                f"{len(i['assets']['origin_404s'])} origin 404s"),
        ('Integrity', 'Origin refs', str(i['origin_refs_remaining'])),
        ('Integrity', 'Off-origin requests', str(i['off_origin_requests'])),
        ('Integrity', 'Links', f"{i['links']['wired']} wired, {i['links']['inert']} inert, "
                               f"{i['links']['missing_targets']} missing, "
                               f"{i['links']['bare_hash_hrefs']} bare #"),
        ('Integrity', 'Markup changes', f"{i['markup_changes']['classified']} classified, "
                                        f"{i['markup_changes']['unexplained']} unexplained"),
        ('Runtime', 'Network', f"{r['runtime']['failed_requests']} failed requests"),
        ('Motion', 'motion-diff.py', r['motion']['gate'] +
         (f" — {'; '.join(r['motion']['failures'])}" if r['motion']['failures'] else '')),
        ('Content', 'copy-gate.py', r['content']['gate'] +
         (f" — {'; '.join(r['content']['failures'])}" if r['content']['failures'] else '')),
        ('Design', 'design-gate.py', r['design']['gate'] +
         (f" — {'; '.join(r['design']['failures'])}" if r['design']['failures'] else '')
         + (f" ({len(r['design']['warnings'])} warning(s))" if r['design']['warnings'] else '')),
        ('Honesty', 'Excluded', str(r['honesty']['excluded'])),
        ('Honesty', 'Unresolved', str(r['honesty']['unresolved'])),
    ]
    lines += [f'| {a} | {b} | {str(c).replace("|", "/")} |' for a, b, c in rows]
    return '\n'.join(lines) + '\n'


def skeleton():
    return {
        'fidelity': {
            'text_pct': 'not measured — ', 'text_chars': 'not measured — ',
            'geometry': {'boxes': 'not measured — ', 'exact': 'not measured — ',
                         'worst_delta_px': 'not measured — '},
            # Shape shown, value withheld: a skeleton that pre-fills 0 would be
            # claiming a measured 0% rather than admitting nothing was measured.
            'pixel': [{'breakpoint': 1440, 'similarity_pct': 'not measured — ',
                       'self_ceiling_pct': None}],
            'pixel_by_page': [],
            'fonts': {'reference': {'faces': 0, 'checks': [], 'widths': []},
                      'mirror': {'faces': 0, 'checks': [], 'widths': []}},
        },
        'integrity': {'origin_refs_remaining': 'not measured — ',
                      'off_origin_requests': 'not measured — ',
                      'markup_changes_unexplained': 'not measured — ',
                      'decode_size_mismatches': 'not measured — '},
        'runtime': {'failed_requests': 'not measured — ', 'live_surfaces': {}},
        'motion': {'mechanism': ''},
        'placeholder_content': 'not measured — ',
        'honesty': {'excluded': [], 'unresolved': []},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--init', action='store_true',
                    help='write a measurements skeleton and exit')
    ap.add_argument('--site', default='')
    ap.add_argument('--date', default='')
    ap.add_argument('--mode', default='match', choices=['match', 'adapt'])
    ap.add_argument('--path', default='mirror',
                    choices=['mirror', 'mirror-scripted', 'rebuild'])
    ap.add_argument('--crawl', help='crawl-manifest.json from crawl.py')
    ap.add_argument('--build', help='build-manifest.json from build.py')
    ap.add_argument('--copy', help='output of copy-gate.py --json')
    ap.add_argument('--motion', help='output of motion-diff.py --json')
    ap.add_argument('--design', help='output of design-gate.py --out — the mechanical '
                                     'half of the taste pre-flight')
    ap.add_argument('--measured', help='measurements.json — see --init')
    ap.add_argument('--single-page', action='store_true',
                    help='declare scope as one page (no crawl); a claim, not a default')
    ap.add_argument('--strict', action='store_true',
                    help='treat UNVERIFIED gates as blocking. Off by default: an '
                         'unmeasured gate is reported, never silently passed, but it '
                         'does not fail the run. Turn it on to assert a fully '
                         'verified Match.')
    ap.add_argument('--out', default='REPORT.md')
    ap.add_argument('--json', dest='json_out', default='report.json')
    a = ap.parse_args()

    if a.init:
        with open('measurements.json', 'w', encoding='utf-8') as f:
            json.dump(skeleton(), f, indent=1)
        print('wrote measurements.json — fill every "not measured — " with a value '
              'or a reason.\nEach one left unmeasured leaves its gate UNVERIFIED: '
              'reported, never passed, and blocking under --strict.')
        return

    measured = load(a.measured, '--measured') or {}
    missing = [(p, how) for p, how in REQUIRED if dig(measured, p) is MISSING]
    if missing:
        print('MEASUREMENTS INCOMPLETE — omission is a failure, not a blank cell.\n'
              'Each key below must hold a value or the string "not measured — <why>".\n',
              file=sys.stderr)
        for p, how in missing:
            print(f'  {p:<45} {how}', file=sys.stderr)
        print('\n  python3 report.py --init      # writes the skeleton', file=sys.stderr)
        sys.exit(2)

    r = assemble(a, load(a.crawl, '--crawl'), load(a.build, '--build'),
                 load(a.copy, '--copy'), load(a.motion, '--motion'),
                 load(a.design, '--design'), measured)
    g = gates(r)
    failed, unverified, _ = verdict(g, a.strict)
    blocking = failed + (unverified if a.strict else [])
    r['gates'] = {'passed': not blocking, 'strict': a.strict,
                  'failing': [x['gate'] for x in failed],
                  'unverified': [x['gate'] for x in unverified],
                  'detail': g}

    with open(a.out, 'w', encoding='utf-8') as f:
        f.write(render(r, g, a.strict))
    with open(a.json_out, 'w', encoding='utf-8') as f:
        json.dump(r, f, indent=1)

    for x in g:
        mark = {'pass': 'ok  ', 'FAIL': 'FAIL', 'UNVERIFIED': '????'}[x['status']]
        print(f"  {mark}  {x['gate']}" + (f"  — {x['detail']}" if x['detail'] else ''))
    print(f'\nwrote {a.out} and {a.json_out}')
    if blocking:
        line = 'NOT DONE' if failed else f'NOT DONE — {len(unverified)} UNVERIFIED (--strict)'
    else:
        line = 'PASS' if not unverified else f'PASS, {len(unverified)} UNVERIFIED'
    print('REPLICATION GATE: ' + line)
    if unverified:
        print(f'{len(unverified)} gate(s) were never measured. They are reported, not '
              'passed — do not describe this build as verified until they are, and '
              'carry them into the report\'s honesty rows.'
              + ('' if a.strict else ' Use --strict to make them blocking.'))
    sys.exit(1 if blocking else 0)


if __name__ == '__main__':
    main()
