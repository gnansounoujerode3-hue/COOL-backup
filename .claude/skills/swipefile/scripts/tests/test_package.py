#!/usr/bin/env python3
"""Packager: does the bundle carry anything the machine captured?

The promise being kept here is "nothing captured ever leaves the machine that
captured it", and the way it breaks is silent — a bundle that looks right and is
discovered to be wrong by whoever receives it. So every case below plants
something that must not ship and asserts the gate refuses, and the clean case
asserts the bundle both excludes the corpus AND still works.

The fixtures are whole miniature skill folders with a real copy of package.py
inside them, because the script resolves what to ship from its own location —
testing it any other way would test a different program.
"""
import json, os, pathlib as _pl, shutil, subprocess, sys, tempfile, zipfile
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
PACKAGE = os.path.join(SCRIPTS, 'package.py')

OK_SELFTEST = "print('1 passed, 0 failed')\n"
BAD_SELFTEST = "print('0 passed, 1 failed')\nimport sys; sys.exit(1)\n"
# Imports a sibling so the run would compile it — the case that put a
# scripts/__pycache__ inside a shipped archive.
PYC_SELFTEST = ("import os, sys\n"
                "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n"
                "import helper\nprint('1 passed, 0 failed')\n")

INDEX = '''# Design library — index

One line per site captured. Read this before a capture; append to it after.

**What does not belong:** body copy, imagery, logos, or any asset.

| Call it | Site | Captured | Path | Motion fidelity · signature | Notable |
|---|---|---|---|---|---|
| **Alpha** | [alpha.com](alpha.com.md) | 2026-08-06 | mirror | **spec** · `x` | Notable |

## Cross-site patterns observed

- scroll-reveal is usually a two-class gate (alpha.com, beta.com)
'''

ENTRY = '''# alpha.com

**Callable as: Alpha** (aliases: alpha)

A site. Captured 2026-08-06 @ 1440x900.

## Colour

Accent `#ff6041` over a greyscale ramp.
'''

root = tempfile.mkdtemp(prefix='package-test-')
PASS, FAIL = [], []
made = [0]


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:400] if detail and not cond else ""}')


def skill(selftest=OK_SELFTEST, extra=None):
    """A miniature skill folder with one captured entry in its library."""
    made[0] += 1
    d = os.path.join(root, f'skill{made[0]}')
    for sub in ('references', 'scripts/tests', 'library'):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    write = lambda rel, text: open(os.path.join(d, rel), 'w', encoding='utf-8').write(text)
    write('SKILL.md', '# Swipefile\n\nBuild a site, reference: Alpha.\n')
    write('SOURCE.txt', 'SOURCE: test fixture\n')
    write('references/capture.md', '# Capture\n\nSome guidance.\n')
    write('scripts/selftest.py', selftest)
    write('scripts/helper.py', 'VALUE = 1\n')
    write('scripts/extract.js', '// probe\n')
    write('scripts/tests/test_x.py', 'print("1 passed, 0 failed")\n')
    write('library/INDEX.md', INDEX)
    write('library/TEMPLATE.md', '# Library entry template\n\nShape.\n')
    write('library/alpha.com.md', ENTRY)
    shutil.copy2(PACKAGE, os.path.join(d, 'scripts', 'package.py'))
    for rel, text in (extra or {}).items():
        os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
        open(os.path.join(d, rel), 'w', encoding='utf-8').write(text)
    return d


def run(d, *args):
    out_dir = os.path.join(d, 'out')
    r = subprocess.run([sys.executable, os.path.join(d, 'scripts', 'package.py'),
                        '--out', out_dir, '--json', *args], capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except Exception:
        data = None
    return r.returncode, r.stdout + r.stderr, data, os.path.join(out_dir, os.path.basename(d))


def fails_of(d):
    return ' || '.join((d or {}).get('failures', []))


def warns_of(d):
    return ' || '.join((d or {}).get('warnings', []))


def tree(bundle):
    # Every check in this file compares against forward-slash literals
    # ('library/TEMPLATE.md'), but os.path.relpath returns native separators —
    # backslashes on Windows — so every membership test failed there while the
    # file was genuinely present. Normalize once, here, rather than at each
    # call site.
    out = []
    for base, _, files in os.walk(bundle):
        out += [os.path.relpath(os.path.join(base, f), bundle).replace(os.sep, '/')
                 for f in files]
    return sorted(out)


# ---- the clean build
d = skill()
code, out, data, bundle = run(d)
check('a clean skill packages', code == 0, fails_of(data))
files = tree(bundle)
check('the captured entry is not in the bundle', 'library/alpha.com.md' not in files, files)
check('the template ships', 'library/TEMPLATE.md' in files, files)
check('the index ships', 'library/INDEX.md' in files, files)
check('scripts and references ship',
      'scripts/helper.py' in files and 'references/capture.md' in files, files)
check('non-allowlisted extensions do not ship — only .py and .js under scripts/',
      all(f.endswith(('.py', '.js')) for f in files if f.startswith('scripts')), files)

idx = open(os.path.join(bundle, 'library', 'INDEX.md'), encoding='utf-8').read()
check('the scaffold keeps the index instructions',
      'One line per site captured' in idx, idx[:200])
check('the scaffold keeps the table header', '| Call it |' in idx, idx)
check('the scaffold carries no captured row', 'alpha.com.md' not in idx, idx)
check('the scaffold empties the cross-site patterns',
      'two-class gate' not in idx and 'Empty by design' in idx, idx)

# ---- an entry planted into a built bundle must be caught by the audit alone
shutil.copy2(os.path.join(d, 'library', 'alpha.com.md'),
             os.path.join(bundle, 'library', 'alpha.com.md'))
r = subprocess.run([sys.executable, os.path.join(d, 'scripts', 'package.py'),
                    '--verify', bundle, '--json', '--no-selftest'],
                   capture_output=True, text=True)
data = json.loads(r.stdout)
check('--verify catches a captured entry planted in a bundle', r.returncode != 0)
check('and names it as a captured entry',
      'is a captured library entry' in fails_of(data), fails_of(data))

# ---- every artifact class the audit is supposed to refuse
for rel, needle in (('library/REPORT.md', 'named REPORT.md'),
                    ('crawl-manifest.json', 'named crawl-manifest.json'),
                    ('scripts/__pycache__/x.cpython-314.pyc', 'inside __pycache__/'),
                    ('site/index.html', 'inside site/'),
                    ('_raw/index.html', 'inside _raw/'),
                    ('references/notes.pyc', 'extension .pyc')):
    d2 = skill()
    code, out, data, b2 = run(d2)
    path = os.path.join(b2, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write('x')
    r = subprocess.run([sys.executable, os.path.join(d2, 'scripts', 'package.py'),
                        '--verify', b2, '--json', '--no-selftest'],
                       capture_output=True, text=True)
    got = json.loads(r.stdout)
    check(f'audit refuses {rel}', r.returncode != 0 and needle in fails_of(got),
          fails_of(got))

# references/report.md is the engine's own documentation and shares a name with
# a mirror's audit file. A substring matcher failed this and blocked every build.
d3 = skill(extra={'references/report.md': '# The replication report\n'})
code, out, data, b3 = run(d3)
check('references/report.md is documentation, not a mirror audit — it ships',
      code == 0 and 'references/report.md' in tree(b3), fails_of(data))

# ---- a corpus name outside library/ is a warning, never a failure
d4 = skill()
code, out, data, b4 = run(d4)
check('a captured site name surviving in SKILL.md is reported',
      'CORPUS TRACE' in warns_of(data), warns_of(data))
check('the corpus trace names the file and line', 'SKILL.md:' in warns_of(data),
      warns_of(data))
check('but a name is not an entry, so the build still passes', code == 0, fails_of(data))

# ---- the bundle must work, and verifying it must not spoil it
d5 = skill(selftest=BAD_SELFTEST)
code, out, data, b5 = run(d5)
check('a bundle whose own suite fails is refused', code != 0)
check('and says so as a bundle failure', 'does not pass in place' in fails_of(data),
      fails_of(data))
check('no archive is written for a refused bundle',
      not os.path.exists(os.path.join(d5, 'out', f'{os.path.basename(d5)}.skill')))

d6 = skill(selftest=PYC_SELFTEST)
code, out, data, b6 = run(d6)
check('running the packaged suite leaves no bytecode in the bundle',
      code == 0 and not any('__pycache__' in f or f.endswith('.pyc') for f in tree(b6)),
      tree(b6))

# ---- the archive
d7 = skill()
code, out, data, b7 = run(d7)
archive = os.path.join(d7, 'out', f'{os.path.basename(d7)}.skill')
check('an archive is written for a clean bundle', os.path.exists(archive), out[-300:])
names = zipfile.ZipFile(archive).namelist()
check('the archive carries no captured entry',
      not any('alpha.com.md' in n for n in names), names)
check('the archive is rooted at the skill name',
      all(n.startswith(os.path.basename(d7) + '/') for n in names), names[:5])
check('the archive holds exactly the bundle files', len(names) == len(tree(b7)),
      (len(names), len(tree(b7))))

# ---- a captured entry is recognised by CONTENT, wherever it is hiding.
# A directory-name test called library/ the whole problem; these three all
# shipped clean under it.
d8 = skill()
open(os.path.join(d8, 'library', 'TEMPLATE.md'), 'a', encoding='utf-8').write('\n' + ENTRY)
code, out, data, b8 = run(d8, '--no-selftest')
check('an entry pasted into TEMPLATE.md is caught', code != 0, fails_of(data))
check('and is named as a captured entry, not as a stray file',
      'is a captured library entry' in fails_of(data), fails_of(data))

# references/ is enumerated, not wildcarded, because a de-identified
# measurements dump has no content signature that motion.md's own six
# cubic-beziers would not also trip. An unlisted doc is never staged at all.
d9 = skill(extra={'references/donor.md': ENTRY})
code, out, data, b9 = run(d9, '--no-selftest')
check('an unlisted references/ doc never reaches the bundle',
      'references/donor.md' not in tree(b9), tree(b9))
check('and its exclusion is stated, not silent',
      'references/donor.md' in warns_of(data), warns_of(data))
check('the untouched template is not mistaken for an entry',
      'TEMPLATE.md is a captured' not in fails_of(data), fails_of(data))

# An entry pasted into a doc that IS on the list is still caught by content.
d9b = skill(extra={'references/capture.md': ENTRY})
code, out, data, b9b = run(d9b, '--no-selftest')
check('an entry pasted into an allowlisted reference doc is caught',
      code != 0 and 'is a captured library entry' in fails_of(data), fails_of(data))

d10 = skill(extra={'scripts/steal.py': f'"""\n{ENTRY}\n"""\n'})
code, out, data, b10 = run(d10, '--no-selftest')
check('an entry hidden in a script docstring is caught', code != 0, fails_of(data))

# The suite cannot test an entry gate without writing entry-shaped fixtures, so
# scripts/tests/ is exempt by design. Assert the exemption exists and is narrow.
d11 = skill(extra={'scripts/tests/test_fixtures.py': f'ENTRY = """{ENTRY}"""\n'})
code, out, data, b11 = run(d11, '--no-selftest')
check('entry-shaped fixtures under scripts/tests/ are not treated as leaks',
      code == 0, fails_of(data))

# ---- the audit must not depend on the allowlist having been honoured
d12 = skill()
code, out, data, b12 = run(d12, '--no-selftest')
os.makedirs(os.path.join(b12, 'donors'), exist_ok=True)
open(os.path.join(b12, 'donors', 'x.md'), 'w', encoding='utf-8').write(ENTRY)
r = subprocess.run([sys.executable, os.path.join(d12, 'scripts', 'package.py'),
                    '--verify', b12, '--json', '--no-selftest'], capture_output=True, text=True)
got = json.loads(r.stdout)
check('--verify refuses a path the allowlist would never produce',
      r.returncode != 0 and 'not a path the allowlist produces' in fails_of(got),
      fails_of(got))

d13 = skill()
code, out, data, b13 = run(d13, '--no-selftest')
try:
    # A real symlink, not a copy or a Windows junction: package.py's own gate
    # checks os.path.islink(), which a junction does not satisfy (different
    # reparse-point type), so only an actual symlink exercises this path.
    os.symlink(os.path.join(d13, 'library'), os.path.join(b13, 'entries'))
except OSError:
    # Windows raises WinError 1314 here without Developer Mode or admin. Same
    # posture as the Chrome-dependent suites: skip cleanly, verify less, don't
    # fail a machine for lacking a privilege unrelated to what's being tested.
    print('SKIP  a symlinked directory in a bundle is refused, not walked past'
          ' — no symlink privilege on this machine')
else:
    r = subprocess.run([sys.executable, os.path.join(d13, 'scripts', 'package.py'),
                        '--verify', b13, '--json', '--no-selftest'], capture_output=True, text=True)
    got = json.loads(r.stdout)
    check('a symlinked directory in a bundle is refused, not walked past',
          r.returncode != 0 and 'is a symlink' in fails_of(got), fails_of(got))

# ---- the corpus scan must read the library files that actually ship
d14 = skill()
idx_path = os.path.join(d14, 'library', 'INDEX.md')
text = open(idx_path, encoding='utf-8').read()
open(idx_path, 'w', encoding='utf-8').write(
    text.replace('One line per site captured.',
                 'One line per site captured. Try "reference: Alpha".'))
code, out, data, b14 = run(d14, '--no-selftest')
check('a corpus name in the index prose is reported, not shipped unread',
      'library/INDEX.md' in warns_of(data), warns_of(data))
check('and it is a warning, since a name is not an entry', code == 0, fails_of(data))

# ---- a relative --out must work: selftest() runs with cwd=bundle, so a
# relative bundle path re-resolves against the new cwd and the suite never runs
d15 = skill()
r = subprocess.run([sys.executable, os.path.join(d15, 'scripts', 'package.py'),
                    '--out', 'reldist', '--json'], capture_output=True, text=True, cwd=d15)
got = json.loads(r.stdout) if r.stdout.startswith('{') else None
check('a relative --out builds and passes', r.returncode == 0, fails_of(got) or r.stderr[-300:])
check('and the packaged suite actually ran',
      got and any('passes in place' in n for n in got['notes']), got and got.get('notes'))
check('the archive lands beside the bundle',
      os.path.exists(os.path.join(d15, 'reldist', f'{os.path.basename(d15)}.skill')))

# ---- an allowlist drops silently by construction; say what was dropped
d16 = skill(extra={'references/diagram.svg': '<svg/>', 'config.json': '{}'})
code, out, data, b16 = run(d16, '--no-selftest')
check('files outside the allowlist are reported, not dropped in silence',
      'NOT SHIPPED' in warns_of(data), warns_of(data))
check('and each one is named',
      'references/diagram.svg' in warns_of(data) and 'config.json' in warns_of(data),
      warns_of(data))
check('a silent drop is a warning, not a failure — the allowlist is deliberate',
      code == 0, fails_of(data))
check('a tool cache is an artifact, not a candidate for shipping',
      'pytest_cache' not in warns_of(skill(extra={'scripts/.pytest_cache/v': 'x'}) and
                                     run(skill(extra={'scripts/.pytest_cache/v': 'x'}),
                                         '--no-selftest')[2] or {}),
      'a cache dir should not appear in NOT SHIPPED')

# ---- a bundle missing its own entry point is not a skill
d17 = skill()
code, out, data, b17 = run(d17, '--no-selftest')
os.remove(os.path.join(b17, 'SKILL.md'))
r = subprocess.run([sys.executable, os.path.join(d17, 'scripts', 'package.py'),
                    '--verify', b17, '--json', '--no-selftest'], capture_output=True, text=True)
got = json.loads(r.stdout)
check('a bundle with no SKILL.md is refused',
      r.returncode != 0 and 'SKILL.md is missing' in fails_of(got), fails_of(got))

# ---- an example row in the index prose must not survive into the scaffold,
# ---- where this script's own row check would then refuse it
d18 = skill()
idx_path = os.path.join(d18, 'library', 'INDEX.md')
text = open(idx_path, encoding='utf-8').read()
open(idx_path, 'w', encoding='utf-8').write(text.replace(
    '| Call it | Site |',
    '| **Example** | [example.com](example.com.md) | 2026-01-01 | mirror | **spec** | x |\n\n| Call it | Site |'))
code, out, data, b18 = run(d18, '--no-selftest')
check('an example row above the table header does not survive scaffolding',
      code == 0, fails_of(data))
check('and the scaffold is genuinely rowless',
      'example.com' not in open(os.path.join(b18, 'library', 'INDEX.md'),
                                encoding='utf-8').read(),
      open(os.path.join(b18, 'library', 'INDEX.md'), encoding='utf-8').read()[-300:])

# A '## ' section added above the index table is corpus, not instruction, and
# must not be copied into the shipped scaffold.
d19 = skill()
idx = os.path.join(d19, 'library', 'INDEX.md')
text = open(idx, encoding='utf-8').read()
open(idx, 'w', encoding='utf-8').write(text.replace(
    '| Call it | Site |',
    '## Quick picks\n\n- settle curve `cubic-bezier(.16,1,.3,1)` @ 420ms\n\n| Call it | Site |'))
code, out, data, b19 = run(d19, '--no-selftest')
scaffold = open(os.path.join(b19, 'library', 'INDEX.md'), encoding='utf-8').read()
check('a section added above the table is not copied into the scaffold',
      'Quick picks' not in scaffold and 'cubic-bezier' not in scaffold, scaffold[-300:])
check('while the intro paragraphs still survive',
      'One line per site captured' in scaffold, scaffold[:200])

# ---- could-not-run is not clean
r = subprocess.run([sys.executable, PACKAGE, '--verify', os.path.join(root, 'nope')],
                   capture_output=True, text=True)
check('--verify on a missing bundle exits 2', r.returncode == 2, r.stdout + r.stderr)

shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
