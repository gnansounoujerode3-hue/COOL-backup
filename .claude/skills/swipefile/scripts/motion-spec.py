#!/usr/bin/env python3
"""
Resolve a motion spec for a reference — or refuse, and say exactly how to get one.

This exists because the rule was not enough. The skill already said a `partial`
library entry cannot be built from. An agent built from one anyway, three times
in a session, patching by hand each time the user noticed, and then wrote:

    "I built this section's motion off a partial entry plus ad-hoc probes,
     three times. The skill has a purpose-built instrument I haven't used once."

The rule was correct and quoted accurately the moment the file was finally read.
Prose cannot stop anything. So the spec becomes an artifact you must HOLD before
you build motion, and this is the only thing that hands one over.

    python3 motion-spec.py --name Phenomenon              # from the library
    python3 motion-spec.py --url https://example.com      # fresh capture
    python3 motion-spec.py --name OneFin                  # refuses, prints the fix

Exit 0 means you have a spec and may build motion. Non-zero means you do not.
Verify afterwards with motion-diff.py; this gate is the input, that one the output.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), 'library')
BUILDABLE = 'spec'


def entries():
    """Callable name -> (path, fidelity) from the library."""
    out = {}
    if not os.path.isdir(LIB):
        return out
    for fn in sorted(os.listdir(LIB)):
        if not fn.endswith('.md') or fn in ('INDEX.md', 'TEMPLATE.md'):
            continue
        path = os.path.join(LIB, fn)
        text = open(path, encoding='utf-8').read()
        m = re.search(r'Motion fidelity:\s*\**\s*([a-z-]+)', text)
        fidelity = m.group(1) if m else 'none'
        names = {fn[:-3].lower()}
        n = re.search(r'\*\*Callable as:\s*([^*]+)\*\*', text)
        if n:
            names |= {p.strip().lower() for p in re.split(r'[,/]', n.group(1)) if p.strip()}
        # `[^*]+` stops at the closing `**`, so the `(aliases: …)` parenthetical
        # every entry advertises was never read: `--name yt` missed a file that
        # literally records `yt`. Twelve aliases across nine entries were dead.
        al = re.search(r'\*\*Callable as:[^*]+\*\*\s*\(aliases:([^)]*)\)', text)
        if al:
            names |= {p.strip().lower().strip('"\'') for p in al.group(1).split(',')
                      if p.strip()}
        for name in names:
            out[name] = (path, fidelity, fn[:-3])
    return out


def resolve(reg, name):
    """Exact name, then an unambiguous PREFIX. Never a bare substring.

    The old fallback was `key in k` with a `break`, which answered `--name
    studio` with createstudio's spec-grade entry at exit 0 and, when two entries
    matched, returned whichever happened to sort first. A confident wrong answer
    is worse here than no answer: the caller builds a page's motion from another
    site's spec and nothing downstream can tell.

    Returns (hit, ambiguous) — exactly one of which is meaningful.
    """
    key = name.strip().lower()
    if key in reg:
        return reg[key], None
    flat = key.replace(' ', '').replace('.', '')
    if len(flat) < 3:
        return None, None
    cands = {}
    for k, v in reg.items():
        kf = k.replace(' ', '').replace('.', '')
        if kf.startswith(flat) or flat.startswith(kf):
            cands.setdefault(v[2], v)
    if len(cands) == 1:
        return next(iter(cands.values())), None
    return None, sorted(cands) or None


def from_library(name):
    reg = entries()
    if not reg:
        print('THE LIBRARY IS EMPTY — nothing to resolve a name against.', file=sys.stderr)
        print('That is the documented first-run state, not a fault. Capture the site:',
              file=sys.stderr)
        print('  python3 motion-spec.py --url <the site url>', file=sys.stderr)
        return 2
    hit, ambiguous = resolve(reg, name)
    if ambiguous:
        print(f'AMBIGUOUS: "{name}" matches {len(ambiguous)} entries — '
              + ', '.join(ambiguous), file=sys.stderr)
        print('Name one of them exactly. Guessing here would build one site\'s motion '
              'from another\'s spec.', file=sys.stderr)
        return 2
    if not hit:
        known = sorted({v[2] for v in reg.values()})
        print(f'NO SUCH ENTRY: "{name}"', file=sys.stderr)
        print('The library holds: ' + ', '.join(known), file=sys.stderr)
        print('\nCapture it instead:\n  python3 motion-spec.py --url <the site url>', file=sys.stderr)
        return 2

    path, fidelity, slug = hit
    if fidelity == BUILDABLE:
        print(json.dumps({
            'source': 'library', 'entry': path, 'name': slug,
            'fidelity': fidelity, 'buildable': True,
            'note': 'Spec-grade entry. Build motion from its spec table; '
                    'verify with motion-diff.py before showing anything.',
        }, indent=1))
        return 0

    print(f'REFUSED — "{slug}" is Motion fidelity: {fidelity}, not `{BUILDABLE}`.',
          file=sys.stderr)
    print(file=sys.stderr)
    print('A non-spec entry has no per-animation mapping: no target, no trigger, no', file=sys.stderr)
    print('from/to, no stagger, no scroll offset. Building motion from it produces a', file=sys.stderr)
    print('page with correct type, correct colour and no animation — and no still', file=sys.stderr)
    print('screenshot will show you that. Do NOT probe individual elements by hand to', file=sys.stderr)
    print('fill the gap; a per-element selector misses whatever it does not match, and', file=sys.stderr)
    print('you will not know what you missed.', file=sys.stderr)
    print(file=sys.stderr)
    print('Capture the whole page once, with the instrument built for it:', file=sys.stderr)
    print(f'\n  python3 {os.path.join(HERE, "motion-spec.py")} --url <url of {slug}>\n',
          file=sys.stderr)
    print(f'Then upgrade {path} per library/TEMPLATE.md and re-run this.', file=sys.stderr)
    return 1


def from_url(url, out, width, height, settle):
    cdp = os.path.join(HERE, 'cdp-run.py')
    extract = os.path.join(HERE, 'motion-extract.js')
    for p in (cdp, extract):
        if not os.path.exists(p):
            print(f'missing {p}', file=sys.stderr)
            return 2
    cmd = [sys.executable, cdp, url, extract, '--pre', extract,
           '--width', str(width), '--height', str(height), '--settle', str(settle)]
    if out:
        cmd += ['--out', out]
    print('capturing: ' + ' '.join(cmd[1:]), file=sys.stderr)
    r = subprocess.run(cmd, capture_output=not out, text=True)
    if r.returncode != 0:
        print('capture failed', file=sys.stderr)
        return 2
    if out:
        d = json.load(open(out, encoding='utf-8'))
    else:
        d = json.loads(r.stdout)
        print(r.stdout)
    n = d.get('animationsSeen', 0)
    print(f'\ncaptured {n} animations, {d.get("scrollTriggered", 0)} scroll-triggered',
          file=sys.stderr)
    if n == 0:
        print('WARNING: zero animations. Either the page genuinely has none, or it mounts '
              'late — re-run with a larger --settle before concluding it is static.',
              file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--name', help='callable library name, e.g. Phenomenon')
    g.add_argument('--url', help='capture a fresh spec from a live page')
    g.add_argument('--list', action='store_true', help='show every entry and its fidelity')
    ap.add_argument('--out', help='write the captured spec here')
    ap.add_argument('--width', type=int, default=1440)
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--settle', type=float, default=3.0)
    a = ap.parse_args()

    if a.list:
        seen = {}
        for path, fid, slug in entries().values():
            seen[slug] = fid
        if not seen:
            # Printing nothing reads as "the tool is broken", not "you have not
            # captured anything yet" — and a fresh install is always here.
            print('The library is empty. That is the documented first-run state:')
            print('  every capture writes library/<domain>.md and a row in INDEX.md.')
            print('  Start one with:  python3 motion-spec.py --url <the site url>')
            return 0
        for slug, fid in sorted(seen.items(), key=lambda kv: (kv[1] != 'spec', kv[0])):
            mark = 'buildable' if fid == BUILDABLE else 'NOT buildable'
            print(f'  {fid:<16} {mark:<14} {slug}')
        return 0
    return from_library(a.name) if a.name else from_url(a.url, a.out, a.width, a.height, a.settle)


if __name__ == '__main__':
    sys.exit(main())
