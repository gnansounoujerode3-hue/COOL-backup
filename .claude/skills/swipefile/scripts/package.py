#!/usr/bin/env python3
"""
Packager — builds the distributable, and proves it carries nothing captured.

SKILL.md makes a promise on the user's behalf: "Nothing captured ever leaves the
machine that captured it — not mirrors, not library entries." Until now that
promise was a manual step ("when packaging the skill for distribution,
`library/` is reset to its scaffold") sitting in a paragraph, on a folder that
currently holds ten real sites. A manual reset is a reset somebody eventually
forgets, and the failure is silent in the worst way: the bundle looks fine, and
the leak is discovered by whoever receives it.

So the bundle is assembled from an ALLOWLIST, never by deleting things from a
copy. A denylist ships every artifact type nobody thought of — a stray
`report.json`, a `site/` mirror, a `BUILDS.md`. An allowlist ships nothing it
was not told to ship, and the audit below then re-checks the result as if the
allowlist were untrusted.

    python3 package.py                    # -> dist/swipefile/ and dist/swipefile.skill
    python3 package.py --out /tmp/ship
    python3 package.py --verify dist/swipefile    # audit a bundle, build nothing
    python3 package.py --json

Exit 0 means the bundle is clean and passed its own test suite in place. Exit 1
means it would have leaked, or it does not work. Warnings name traces of this
machine's corpus that are not entries — an example command naming a real site —
and never block, because refusing to package over an illustrative name is the
crying-wolf failure this folder keeps paying for.
"""
import argparse, fnmatch, json, os, re, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NAME = os.path.basename(ROOT)

# Everything the distributable is allowed to contain. Adding an artifact type
# here is a deliberate act; forgetting to exclude one is not possible.
ALLOW = (
    ('', ('SKILL.md', 'README.md', 'SOURCE.txt')),
    # Enumerated, not wildcarded: a de-identified measurements dump saved as
    # references/tokens.md is invisible to any content check (motion.md itself
    # legitimately carries six cubic-beziers), so a new doc costs one reviewed
    # line here and is named in the NOT SHIPPED warning until it gets one.
    ('references', ('adaptation.md', 'capture.md', 'copy.md', 'crawl.md',
                    'mirror.md', 'motion.md', 'report.md', 'taste.md', 'verify.md')),
    ('scripts', ('*.py', '*.js')),
    ('scripts/tests', ('*.py',)),
    ('library', ('TEMPLATE.md',)),          # INDEX.md is regenerated, never copied
)
# Artifacts that mean a capture or a build happened here. Matched by exact
# basename and by path component, never as a substring of the path: `REPORT.md`
# is a mirror's audit and must not ship, while `references/report.md` is the
# engine's own documentation and must. A substring match cannot tell them apart.
ARTIFACT_FILES = {'crawl-manifest.json', 'build-manifest.json', 'report.json',
                  'measurements.json', 'REPORT.md', 'BUILDS.md', '.DS_Store'}
ARTIFACT_DIRS = {'_raw', 'cdn', 'site', 'dist', '__pycache__', '.claude', '.git',
                 '.pytest_cache', '.ruff_cache', '.mypy_cache', 'node_modules', '.venv'}
ARTIFACT_EXTS = ('.pyc', '.pyo', '.skill', '.zip')
# Repository plumbing: correctly absent from a .skill bundle, and not a
# candidate for shipping, so it must not appear in the NOT SHIPPED report.
REPO_FILES = {'.gitignore', '.gitattributes', '.editorconfig', 'LICENSE'}
INDEX_HEADER = '| Call it |'
# A bundle missing these is not a skill, however clean it audits.
REQUIRED_IN_BUNDLE = ('SKILL.md', 'scripts/selftest.py',
                      'library/INDEX.md', 'library/TEMPLATE.md')

# What makes a file a library entry is its CONTENT, not the directory it sits
# in. An entry copied into references/ is the same leak as one left in library/,
# and a directory-name test cannot see it. TEMPLATE.md carries both fields as
# placeholders — `<Name>`, `<spec | partial | …>` — so the test is a REAL value:
# angle brackets are excluded from the name, and the fidelity must be a literal
# enum member.
# Braces are excluded for the same reason, and it is not hypothetical: the entry
# line appears in local-entry.py as the format string `{name}` it writes entries
# WITH, and the gate accused the generator of being one of the things it
# generates. A placeholder is not a capture, whichever syntax spells it.
ENTRY_CALLABLE = re.compile(r'\*\*Callable as:\s*([^*\n<>{}]+?)\s*\*\*')
ENTRY_FIDELITY = re.compile(r'\*\*Motion fidelity:\s*(?:spec|partial|signature-only|none)\b')
# Fixtures under here are synthetic entries by design — the suite cannot test an
# entry gate without writing entry-shaped files. They are still corpus-scanned.
FIXTURE_DIR = 'scripts/tests/'


def entry_marker(text):
    """Why this file is a captured library entry, or None."""
    m = ENTRY_FIDELITY.search(text)
    if m:
        return f'it declares `{m.group(0).strip("*")}`'
    m = ENTRY_CALLABLE.search(text)
    if m:
        return f'it names a callable entry ("{m.group(1)}")'
    return None


def allowed(rel):
    """Is this a path the allowlist would have produced?

    --verify audits bundles this process did not build, so the audit needs its
    own answer to "what belongs here" rather than trusting that a build happened.
    """
    path = rel.replace(os.sep, '/')
    if path == 'library/INDEX.md':
        return True                     # regenerated, never copied, so not in ALLOW
    subdir, _, base = path.rpartition('/')
    return any(subdir == d and any(fnmatch.fnmatch(base, pat) for pat in pats)
               for d, pats in ALLOW)


def source_corpus(lib):
    """Names of every site captured on THIS machine, for the leak scan."""
    names = set()
    for fn in sorted(os.listdir(lib)) if os.path.isdir(lib) else []:
        if not fn.endswith('.md') or fn in ('INDEX.md', 'TEMPLATE.md'):
            continue
        names.add(fn[:-3])
        slug = fn[:-3].split('.')[0]
        if len(slug) > 3:
            names.add(slug)
        with open(os.path.join(lib, fn), encoding='utf-8') as f:
            m = re.search(r'\*\*Callable as:\s*([^*]+?)\s*\*\*', f.read())
        if m:
            names |= {p.strip() for p in re.split(r'[,/]', m.group(1)) if len(p.strip()) > 3}
    return sorted(names, key=len, reverse=True)


def scaffold_index(text):
    """The index's instructions, with every captured row dropped.

    The prose above the table explains what belongs in a library and is part of
    the engine. The rows below it, and the cross-site patterns beneath them, are
    the accumulated corpus and belong to the machine that measured them.
    """
    head = []
    for line in text.splitlines():
        if line.startswith(INDEX_HEADER) or line.startswith('## '):
            break               # intro paragraphs only; added sections are corpus
        # A table-shaped line above the header is an example, and copying it
        # produces a scaffold this script's own row check then refuses.
        if line.strip().startswith('|'):
            continue
        head.append(line)
    while head and not head[-1].strip():
        head.pop()
    return '\n'.join(head) + f'''

{INDEX_HEADER} Site | Captured | Path | Motion fidelity · signature | Notable |
|---|---|---|---|---|---|

## Cross-site patterns observed

*Empty by design.* A pattern earns a line here once **two or more** entries
support it, each cited by name — see SKILL.md "Step 0 — Consult the library".
'''


def staged_files():
    """(source_path, bundle_relative_path) for everything the allowlist permits."""
    import fnmatch
    out = []
    for subdir, patterns in ALLOW:
        src_dir = os.path.join(ROOT, subdir) if subdir else ROOT
        if not os.path.isdir(src_dir):
            continue
        for fn in sorted(os.listdir(src_dir)):
            path = os.path.join(src_dir, fn)
            if not os.path.isfile(path):
                continue
            if any(fnmatch.fnmatch(fn, p) for p in patterns):
                out.append((path, os.path.join(subdir, fn) if subdir else fn))
    return out


def dropped_files(exclude=None):
    """Everything in the source tree the allowlist did not stage.

    Reported, never guessed at: a silent omission is the one failure auditing
    the OUTPUT can never detect, because the bundle looks entirely consistent
    and only breaks later, for the recipient.
    """
    staged = {os.path.abspath(src) for src, _ in staged_files()}
    # The bundle is often written inside the source tree; it is output, not
    # dropped input, and counting it buries the real drops under its own files.
    skip = os.path.abspath(exclude) + os.sep if exclude else None
    out = []
    for base, dirs, files in os.walk(ROOT):
        if skip and (os.path.abspath(base) + os.sep).startswith(skip):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in ARTIFACT_DIRS]
        for fn in files:
            path = os.path.join(base, fn)
            rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
            # library/ entries are excluded on purpose and reported separately.
            if (os.path.abspath(path) in staged or rel.startswith('library/')
                    or fn in REPO_FILES):
                continue
            out.append(rel)
    return sorted(out)


def build(out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    for src, rel in staged_files():
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
    index_src = os.path.join(ROOT, 'library', 'INDEX.md')
    text = open(index_src, encoding='utf-8').read() if os.path.exists(index_src) else ''
    os.makedirs(os.path.join(out_dir, 'library'), exist_ok=True)
    with open(os.path.join(out_dir, 'library', 'INDEX.md'), 'w', encoding='utf-8') as f:
        f.write(scaffold_index(text))
    return out_dir


def audit(bundle, corpus, fails, warns, notes):
    """Re-check the bundle as if the allowlist could not be trusted."""
    # Every path collected here ends up either compared against the allowlist
    # (which is written in forward slashes) or printed straight into a warning
    # a person reads. os.path.relpath returns native separators, so on Windows
    # this was silently building backslash paths — allowlist entries never
    # matched, and CORPUS TRACE lines named a file that didn't look like
    # anything else in the report. Normalize once, at the source.
    to_posix = lambda p: os.path.relpath(p, bundle).replace(os.sep, '/')
    present, links = [], []
    for base, dirs, files in os.walk(bundle):
        for d in dirs:
            if os.path.islink(os.path.join(base, d)):
                links.append(to_posix(os.path.join(base, d)))
        for fn in files:
            path = os.path.join(base, fn)
            rel = to_posix(path)
            (links if os.path.islink(path) else present).append(rel)
    present.sort()

    for rel in sorted(links):
        fails.append(f'SYMLINK: {rel} is a symlink. os.walk does not descend into one, '
                     f'so whatever it points at is invisible to this audit and absent '
                     f'from the archive while still sitting in the bundle directory. '
                     f'A distributable is self-contained or it is not one.')

    for rel in present:
        parts = rel.replace(os.sep, '/').split('/')
        base = parts[-1]
        why = None
        if base in ARTIFACT_FILES:
            why = f'named {base}'
        elif set(parts[:-1]) & ARTIFACT_DIRS:
            why = f'inside {"/".join(sorted(set(parts[:-1]) & ARTIFACT_DIRS))}/'
        elif base.endswith(ARTIFACT_EXTS):
            why = f'extension {os.path.splitext(base)[1]}'
        if why:
            fails.append(f'ARTIFACT: {rel} is a capture or build artifact ({why}) '
                         f'and must not ship.')
        elif not allowed(rel):
            fails.append(f'UNEXPECTED: {rel} is not a path the allowlist produces. '
                         f'A bundle holds exactly what was staged; anything else '
                         f'arrived by some route nobody audited.')

    # Content, not directory. An entry pasted into TEMPLATE.md or copied into
    # references/ shipped clean under the old directory-name test.
    for rel in present:
        if rel.replace(os.sep, '/').startswith(FIXTURE_DIR):
            continue
        with open(os.path.join(bundle, rel), encoding='utf-8', errors='replace') as f:
            why = entry_marker(f.read())
        if why:
            fails.append(f'LIBRARY: {rel} is a captured library entry — {why}. The '
                         f'library ships blank: "nothing captured ever leaves the '
                         f'machine that captured it".')

    idx = os.path.join(bundle, 'library', 'INDEX.md')
    if not os.path.exists(idx):
        fails.append('LIBRARY: the bundle has no library/INDEX.md scaffold to grow into.')
    else:
        rows = [l for l in open(idx, encoding='utf-8').read().splitlines()
                if l.strip().startswith('|') and not set(l.strip()) <= set('|-: ')
                and not l.startswith(INDEX_HEADER)]
        for r in rows:
            fails.append(f'LIBRARY: INDEX.md still carries a captured row: {r[:70]}')

    # Traces of this machine's corpus that are not entries. Reported, never
    # blocking: an example command naming a real site is a documentation choice,
    # and a fresh install where that name resolves to nothing is merely stale.
    if corpus:
        hits = []
        # Bounded, not bare substrings: "apple" otherwise matches AppleWebKit in
        # build.py's user-agent string, and a warning that cries wolf about its
        # own source code is one nobody reads.
        pattern = re.compile('(?<![A-Za-z0-9])(?:'
                             + '|'.join(re.escape(n) for n in corpus)
                             + ')(?![A-Za-z0-9])', re.I)
        for rel in present:
            with open(os.path.join(bundle, rel), encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f, 1):
                    m = pattern.search(line)
                    if m:
                        hits.append(f'{rel}:{i} "{m.group(0)}"')
        if hits:
            warns.append(f'CORPUS TRACE: {len(hits)} mention(s) of sites captured on this '
                         f'machine survive in the bundle — {"; ".join(hits[:6])}'
                         f'{" …" if len(hits) > 6 else ""}. These are names, not entries, '
                         f'so they leak no measurements; but they name a corpus the '
                         f'recipient will not have. Genericise them if the bundle is going '
                         f'to a stranger.')
    for req in REQUIRED_IN_BUNDLE:
        # present is posix-normalized above (to_posix); REQUIRED_IN_BUNDLE's
        # own literals are already forward-slash, so no conversion is needed
        # here — converting to os.sep, as this used to, is exactly backwards
        # now and fails every required-file check on Windows.
        if req not in present:
            fails.append(f'BUNDLE: {req} is missing. A bundle without it is not a '
                         f'usable skill, however clean the rest of it audits.')

    notes.append(f'{len(present)} files staged from an allowlist of '
                 f'{len(ALLOW)} directories')
    return present


def selftest(bundle, fails, notes):
    """A bundle that cannot pass its own suite is not a distributable."""
    st = os.path.join(bundle, 'scripts', 'selftest.py')
    if not os.path.exists(st):
        fails.append('BUNDLE: no scripts/selftest.py — the bundle cannot verify itself.')
        return
    # Without this the run compiles the bundle's own modules and leaves
    # scripts/__pycache__ inside the artifact being shipped.
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    r = subprocess.run([sys.executable, st], capture_output=True, text=True,
                       cwd=bundle, env=env)
    tail = [l for l in r.stdout.splitlines() if 'passed,' in l]
    if r.returncode != 0:
        detail = tail[-1] if tail else (r.stderr.strip() or r.stdout.strip()
                                        or f'no output, exit {r.returncode}')[-300:]
        fails.append(f'BUNDLE: the packaged suite does not pass in place — {detail}')
    else:
        notes.append(f'packaged suite passes in place: {tail[-1] if tail else "ok"}')


def zip_bundle(bundle, dest):
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(bundle):
            for fn in sorted(files):
                path = os.path.join(base, fn)
                z.write(path, os.path.join(NAME, os.path.relpath(path, bundle)))
    return os.path.getsize(dest)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'),
                    help='directory to build into (default: ./dist, itself never bundled)')
    ap.add_argument('--verify', metavar='BUNDLE',
                    help='audit an existing bundle directory and build nothing')
    ap.add_argument('--no-selftest', action='store_true',
                    help='skip running the packaged suite in place')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    fails, warns, notes = [], [], []
    corpus = source_corpus(os.path.join(ROOT, 'library'))
    if a.verify:
        bundle, archive = os.path.abspath(a.verify), None
        if not os.path.isdir(bundle):
            print(f'no bundle at {bundle}', file=sys.stderr)
            sys.exit(2)
    else:
        out_root = os.path.abspath(a.out)
        bundle = build(os.path.join(out_root, NAME))
        archive = os.path.join(out_root, f'{NAME}.skill')

    # Order matters: the suite runs first, then the audit inspects whatever the
    # directory looks like afterwards. Auditing first passed a bundle whose
    # __pycache__ was created by the very run meant to verify it.
    if not a.no_selftest:
        selftest(bundle, fails, notes)
    present = audit(bundle, corpus, fails, warns, notes)
    if not a.verify:
        skipped = dropped_files(out_root)
        if skipped:
            warns.append(f'NOT SHIPPED: {len(skipped)} file(s) in the source tree fall '
                         f'outside the allowlist and were dropped — '
                         f'{", ".join(skipped[:8])}{" …" if len(skipped) > 8 else ""}. '
                         f'Add the pattern to ALLOW if the skill needs any of them; a '
                         f'drop nobody states is a bundle that breaks for the recipient.')
    if archive and not fails:
        notes.append(f'wrote {archive} ({zip_bundle(bundle, archive):,} bytes)')
    elif archive:
        notes.append('archive NOT written — the bundle did not pass its audit')

    ok = not fails
    if a.json:
        print(json.dumps({'pass': ok, 'bundle': bundle, 'files': present,
                          'corpus_on_this_machine': corpus,
                          'failures': fails, 'warnings': warns, 'notes': notes}, indent=1))
    else:
        print(f'{bundle}  —  {len(present)} files')
        for x in notes:
            print(f'  note  {x}')
        for x in warns:
            print(f'  WARN  {x}')
        for x in fails:
            print(f'  FAIL  {x}')
        print('\nPACKAGE GATE: ' + ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
