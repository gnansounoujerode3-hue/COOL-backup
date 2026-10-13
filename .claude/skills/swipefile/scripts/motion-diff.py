#!/usr/bin/env python3
"""
Motion parity gate — does the build actually animate like the reference?

Step 4's pixel diff compares screenshots, and a screenshot cannot see motion. A
build can measure 99% similarity and have no animation at all, so the number
says "nearly done" about a page that is visibly dead the moment it loads. This
is the gate that closes that hole, and it is mechanical for the same reason the
font gate is: the failure it catches is invisible to judgement.

The failure mode it exists to stop, observed twice in one session:

    "I described those tiles as 'drifting' in my capture notes but never
     measured it, then built them static."

Prose is the tell. "Drifts", "lifts", "floats", "settles" carry no values, so a
build composed from them has nothing to implement and silently ships static.

Capture both sides with the SAME instrument, then compare:

    python3 cdp-run.py https://reference.com  motion-extract.js --pre motion-extract.js --out ref.json
    python3 cdp-run.py http://127.0.0.1:8791/ motion-extract.js --pre motion-extract.js --out build.json
    python3 motion-diff.py ref.json build.json

Exits non-zero when the gate fails, so it can sit in a build script.
"""
import argparse, json, sys
from collections import Counter

# Properties that carry a visible reveal. A group is identified by what it moves
# and roughly how long it takes — not by selector, which legitimately differs
# between a reference and a re-branded build.
CARRIERS = ('opacity', 'transform', 'clip-path', 'clipPath', 'filter',
            'translate', 'scale', 'rotate', 'color', 'background-color')


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def carriers_of(anim):
    vals = (anim.get('values') or {})
    keys = set(vals.get('from') or {}) | set(vals.get('to') or {})
    prop = anim.get('property')
    if prop:
        keys.add(prop)
    return {k for k in keys if k in CARRIERS} or ({prop} if prop else set())


def bucket(ms, tol):
    """Group durations so 300 and 310 are the same intent, 300 and 800 are not."""
    if not ms:
        return None
    return round(ms / max(1.0, ms * tol)) * max(1.0, ms * tol)


def profile(d, tol):
    anims = d.get('animations', [])
    easings = Counter(str(a.get('easing')) for a in anims if a.get('easing'))
    durations = Counter(int(a['duration']) for a in anims if a.get('duration'))
    props = Counter(p for a in anims for p in carriers_of(a))
    staggers = sorted({s for l in d.get('ladders', []) for s in (l.get('stagger') or [])})
    return {
        'count': len(anims),
        'scrollTriggered': d.get('scrollTriggered', 0),
        'easings': easings,
        'durations': durations,
        'props': props,
        'staggers': staggers,
        'reducedMotion': (d.get('reducedMotion') or {}).get('mediaQueryPresent'),
    }


def close(a, b, tol):
    return abs(a - b) <= max(16, a * tol)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('reference', help='motion-extract JSON for the reference')
    ap.add_argument('build', help='motion-extract JSON for the build')
    ap.add_argument('--tolerance', type=float, default=0.15,
                    help='fractional duration tolerance (default 0.15)')
    ap.add_argument('--min-share', type=float, default=0.05,
                    help='a reference duration/ladder below this share of total firings is '
                         'decoration, not the system, and is reported rather than gated')
    ap.add_argument('--min-coverage', type=float, default=0.6,
                    help='fraction of reference motion that must be reproduced (default 0.6)')
    ap.add_argument('--adapt', action='store_true',
                    help='Adapt mode: durations/curves must still transfer verbatim, but '
                         'animation COUNT may differ because the content differs')
    ap.add_argument('--json', action='store_true', help='emit machine-readable result')
    a = ap.parse_args()

    ref, bld = load(a.reference), load(a.build)
    R, B = profile(ref, a.tolerance), profile(bld, a.tolerance)
    failures, warnings, notes = [], [], []

    # --- 1. Does the build animate at all? The 'built it static' case.
    if R['count'] > 0 and B['count'] == 0:
        failures.append(
            f"BUILD HAS NO MOTION: reference runs {R['count']} animations, build runs 0. "
            "This is the 'described it in prose, built it static' failure.")

    # --- 2. Signature curves. The most common reason a rebuild feels wrong is a
    # custom cubic-bezier replaced with a keyword.
    ref_curves = [e for e, _ in R['easings'].most_common() if 'cubic-bezier' in e or 'linear(' in e]
    missing_curves = [c for c in ref_curves if c not in B['easings']]
    if missing_curves:
        failures.append('SIGNATURE CURVE MISSING: ' + '; '.join(c[:60] for c in missing_curves[:4]))

    # --- 3. Durations, weighted by use. The library's own rule for colour applies
    # to motion: a duration used 490 times is the system, one used 14 times is
    # decoration. Gating on decoration produces false alarms, and a gate that
    # cries wolf gets ignored — which is the failure this whole file exists to
    # stop. So only structural tiers are required.
    total = sum(R['durations'].values()) or 1
    structural = [d for d, n in R['durations'].items() if n / total >= a.min_share]
    decoration = [d for d, n in R['durations'].items() if n / total < a.min_share]
    missing_dur = [d for d in structural
                   if not any(close(d, b, a.tolerance) for b in B['durations'])]
    if missing_dur:
        failures.append('STRUCTURAL DURATIONS ABSENT: '
                        + ', '.join(f'{d}ms ({R["durations"][d]}x in ref)'
                                    for d in sorted(missing_dur)[:8]))
    minor_missing = [d for d in decoration
                     if not any(close(d, b, a.tolerance) for b in B['durations'])]
    if minor_missing:
        notes.append('minor durations not reproduced (decoration, not gated): '
                     + ', '.join(f'{d}ms' for d in sorted(minor_missing)[:8]))

    # --- 4. Stagger ladders — "staggered left to right" with no interval is not a
    # spec. Weighted the same way: only ladders carrying real volume are required.
    lad_total = sum(l.get('count', 0) for l in ref.get('ladders', [])) or 1
    key_stag = sorted({s for l in ref.get('ladders', [])
                       if l.get('count', 0) / lad_total >= a.min_share
                       for s in (l.get('stagger') or [])})
    missing_stag = [s for s in key_stag
                    if not any(close(s, b, a.tolerance) for b in B['staggers'])]
    if key_stag and missing_stag:
        (warnings if B['staggers'] else failures).append(
            'STAGGER MISSING: reference ' + ', '.join(f'{s}ms' for s in key_stag[:6])
            + f" | build {B['staggers'][:6] or 'none'}")
    elif key_stag:
        notes.append(f'stagger ladder reproduced: {key_stag[:6]}')

    # --- 5. What moves. A page that fades where the reference also travels or
    # unmasks has the vocabulary but not the character.
    missing_props = [p for p, n in R['props'].most_common() if p not in B['props'] and n >= 2]
    if missing_props:
        warnings.append('PROPERTIES NOT ANIMATED: ' + ', '.join(missing_props[:6]))

    # --- 6. Volume, unless Adapt (different content legitimately means fewer nodes)
    coverage = (B['count'] / R['count']) if R['count'] else 1.0
    if not a.adapt and R['count'] and coverage < a.min_coverage:
        failures.append(f'MOTION COVERAGE {coverage:.0%} < {a.min_coverage:.0%} '
                        f"({B['count']} vs {R['count']} animations)")
    elif a.adapt:
        notes.append(f'Adapt mode: coverage {coverage:.0%} not gated; curves/durations still are.')

    # --- 7. Reduced motion is ship-blocking regardless of the reference.
    if not B['reducedMotion']:
        failures.append('NO prefers-reduced-motion IN THE BUILD. Ship-blocking even when the '
                        'reference omits it.')

    ok = not failures
    if a.json:
        print(json.dumps({
            'pass': ok, 'failures': failures, 'warnings': warnings, 'notes': notes,
            'reference': {k: (dict(v) if isinstance(v, Counter) else v) for k, v in R.items()},
            'build': {k: (dict(v) if isinstance(v, Counter) else v) for k, v in B.items()},
            'coverage': round(coverage, 3),
        }, indent=1))
    else:
        print(f'reference : {R["count"]:>4} animations, {len(R["easings"])} curves, '
              f'durations {sorted(R["durations"])[:6]}, staggers {R["staggers"][:5]}')
        print(f'build     : {B["count"]:>4} animations, {len(B["easings"])} curves, '
              f'durations {sorted(B["durations"])[:6]}, staggers {B["staggers"][:5]}')
        print(f'coverage  : {coverage:.0%}')
        for n in notes:
            print(f'  note  {n}')
        for w in warnings:
            print(f'  WARN  {w}')
        for f in failures:
            print(f'  FAIL  {f}')
        print('\nMOTION GATE: ' + ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
