#!/usr/bin/env python3
"""
Self-test for the mirror engine. Run it once on a new machine.

Each suite stands up a synthetic origin, runs the real script against it, and
asserts on the artifacts — no network, no Playwright, no fixtures to download.
Every case corresponds to a failure that was measured on a real capture and
recorded in library/INDEX.md, so a pass means the engine still does the thing
the library paid to learn.

  python3 selftest.py            # all suites
  python3 selftest.py serve      # one suite

Playwright is NOT required: capture.py's scroll loop is exercised with a stub
page, because the failure it guards against is loop termination, not rendering.
The `motion` suite does need real Chrome plus `websockets`, because the bugs it
guards against only occur in a real browser; it skips cleanly without them.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(HERE, 'tests')
SUITES = [
    ('serve', 'test_serve.py', '?range= slicing, MIME, magic-byte typing'),
    ('build', 'test_build.py', 'asset mirroring, rewriting, cdn symlink, SRI, #inert'),
    ('crawl', 'test_crawl.py', 'boundaries, sitemap coverage, skip reasons'),
    ('capture', 'test_capture_scroll.py', 'scroll reaches the page bottom'),
    ('library', 'test_library.py', 'entry contract, name collisions, INDEX/entry fidelity agreement'),
    ('spec', 'test_spec.py', 'name resolution: aliases resolve, substrings do not'),
    ('provenance', 'test_provenance.py', 'every number in an entry traces to its capture'),
    ('local', 'test_local.py', 'the local-model loop: retries, feedback, rollback'),
    ('motion', 'test_motion.py', 'per-animation spec: trigger, from/to, stagger, load-time'),
    ('font', 'test_font.py', 'canvas A/B tells a real face from a silent fallback'),
    ('copy', 'test_copy.py', 'AI-writing tells, SEO essentials, JSON-LD structured data'),
    ('report', 'test_report.py', 'the replication gates; unverified is never passed'),
    ('design', 'test_design.py', 'the taste pre-flight, measured: contrast, eyebrows, locks'),
    ('package', 'test_package.py', 'the distributable carries no captured entry or artifact'),
]


def main():
    want = sys.argv[1:]
    suites = [s for s in SUITES if not want or s[0] in want]
    if not suites:
        raise SystemExit(f'no such suite; choose from {[s[0] for s in SUITES]}')

    results = []
    for name, filename, blurb in suites:
        print(f'\n{"=" * 68}\n{name}  —  {blurb}\n{"=" * 68}')
        # Do not leave __pycache__ behind: a packaged bundle is a folder someone
        # verifies with `package.py --verify`, and bytecode dropped by this run
        # would have that gate accuse them of shipping a build artifact.
        # encoding='utf-8' here, plus PYTHONUTF8=1 for the child: this codebase
        # prints em-dashes throughout, and on Windows the ambient locale
        # encoding is commonly cp1252, which cannot represent five particular
        # byte values at all. A suite that happened to relay one of those
        # bytes crashed the *entire* run with a decode error having nothing to
        # do with what was being tested. PYTHONUTF8=1 cascades to every
        # subprocess a suite spawns in turn (build.py, report.py, ...), so
        # the whole tree writes and reads UTF-8 consistently; errors='replace'
        # is the last-resort net if something still isn't valid UTF-8.
        r = subprocess.run([sys.executable, os.path.join(TESTS, filename)],
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace',
                           env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                                'PYTHONUTF8': '1'})
        tail = [l for l in r.stdout.splitlines() if l.startswith(('PASS', 'FAIL'))]
        print('\n'.join(tail) or r.stdout[-800:])
        if r.returncode != 0 and r.stderr:
            print(r.stderr[-800:], file=sys.stderr)
        # 'FAIL  <name>' is a result line; the suites' trailing 'FAILED: a, b'
        # summary is not, and counting it inflated every failing tally by one.
        results.append((name, r.returncode == 0,
                        sum(l.startswith('PASS  ') for l in tail),
                        sum(l.startswith('FAIL  ') for l in tail)))

    print(f'\n{"=" * 68}')
    total_ok = total_bad = 0
    for name, ok, npass, nfail in results:
        total_ok += npass
        total_bad += nfail
        print(f'  {"ok  " if ok else "FAIL"}  {name:<9} {npass:>3} passed  {nfail:>3} failed')
    print(f'{"=" * 68}\n{total_ok} passed, {total_bad} failed')
    sys.exit(1 if any(not ok for _, ok, _, _ in results) else 0)


if __name__ == '__main__':
    main()
