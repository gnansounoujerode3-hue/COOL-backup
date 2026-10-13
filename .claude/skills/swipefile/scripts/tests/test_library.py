#!/usr/bin/env python3
"""Library gate: does it catch a silently mis-resolving entry without crying wolf?

Both directions matter, and the second one more than usual here. Every FAIL rule
has zero violators on the real library, so this suite is the only place they are
ever exercised — if the fixtures do not fire them, nothing does. And a clean
library must come back with ZERO findings, warnings included: this gate reads a
corpus that is already correct, so any noise it makes is noise forever.
"""
import json, os, pathlib as _pl, shutil, subprocess, sys, tempfile
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
GATE = os.path.join(SCRIPTS, 'library-lint.py')

SPEC_TABLE = (
    '| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |\n'
    '|---|---|---|---|---|---|---|---|\n'
    '| hero | .hero h1 | load | y 12→0 | 400ms | cubic-bezier(.22,1,.36,1) | 60ms | — |\n')


def entry(name, fidelity='partial', viewport='@ 1440x900', aliases=None,
          body='', callable_line=True, table=''):
    """One library entry. Defaults are deliberately CLEAN — each test breaks one thing."""
    head = f'# {name.lower()}.com\n\n'
    if callable_line:
        head += f'**Callable as: {name}**'
        head += f' (aliases: {aliases})\n\n' if aliases else '\n\n'
    head += f'A site. Captured 2026-08-06 {viewport}.\nStack: hand-built. **Mirror path**.\n\n'
    motion = f'## Motion\n\n**Motion fidelity: {fidelity}**\n\n{table}\n'
    return head + body + motion


def index(rows, extra=''):
    head = ('# Design library — index\n\n'
            '| Call it | Site | Captured | Path | Motion fidelity · signature | Notable |\n'
            '|---|---|---|---|---|---|\n')
    return head + '\n'.join(rows) + '\n\n' + extra + '\n## Cross-site patterns observed\n\n- a\n'


def row(name, slug, fidelity='partial', cells=6):
    base = (f'| **{name}** | [{slug}]({slug}.md) | 2026-08-06 | mirror | '
            f'**{fidelity}** · `cubic-bezier(.22,1,.36,1)` @ .3s | Notable thing |')
    return base if cells == 6 else base.rsplit('|', 2)[0] + '|'


root = tempfile.mkdtemp(prefix='library-test-')
PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:400] if detail and not cond else ""}')


def build(entries, index_text='__default__'):
    """Write a fixture library. entries maps filename -> text."""
    d = tempfile.mkdtemp(dir=root)
    for fn, text in entries.items():
        with open(os.path.join(d, fn), 'w', encoding='utf-8') as f:
            f.write(text)
    if index_text == '__default__':
        index_text = index([row(fn[:-3].split('.')[0].title(), fn[:-3])
                            for fn in entries if fn not in ('INDEX.md', 'TEMPLATE.md')])
    if index_text is not None:
        with open(os.path.join(d, 'INDEX.md'), 'w', encoding='utf-8') as f:
            f.write(index_text)
    return d


def run(entries, index_text='__default__'):
    d = build(entries, index_text) if isinstance(entries, dict) else entries
    r = subprocess.run([sys.executable, GATE, d, '--json'], capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except Exception:
        data = None
    return r.returncode, (r.stdout + r.stderr), data


def fails_of(data):
    return ' || '.join((data or {}).get('failures', []))


def warns_of(data):
    return ' || '.join((data or {}).get('warnings', []))


CLEAN = {'alpha.com.md': entry('Alpha'), 'beta.com.md': entry('Beta')}

# ---- a clean library must be silent, warnings included
code, out, data = run(CLEAN)
check('a clean library passes', code == 0, out[-400:])
check('a clean library raises no failures', data and not data['failures'], fails_of(data))
check('a clean library raises no warnings either', data and not data['warnings'],
      warns_of(data))
check('--json reports the fidelity it parsed',
      data and data['fidelity'] == {'alpha.com.md': 'partial', 'beta.com.md': 'partial'},
      data and data.get('fidelity'))

# ---- the silent promotion: the runtime reads a line the entry did not intend
sneaky = ('# alpha.com\n\n**Callable as: Alpha**\n\nA site. Captured 2026-08-06 @ 1440x900.\n\n'
          '## Notes\n\nThe nav island is `Motion fidelity: spec` in isolation.\n\n'
          '## Motion\n\n**Motion fidelity: partial**\n')
sneaky_lines = sneaky.splitlines()
decl_line = next(i for i, l in enumerate(sneaky_lines, 1) if l.startswith('**Motion fidelity:'))
mention_line = next(i for i, l in enumerate(sneaky_lines, 1) if '`Motion fidelity: spec`' in l)
code, out, data = run({**CLEAN, 'alpha.com.md': sneaky})
check('a fidelity mention ABOVE the declaration fails', code != 0)
check('and the failure names both line numbers, correctly',
      f'at line {decl_line}' in fails_of(data) and f'from line {mention_line}' in fails_of(data),
      f'expected decl={decl_line} mention={mention_line} in: {fails_of(data)}')
check('and says which value the runtime would actually take',
      'would take `spec`' in fails_of(data), fails_of(data))

# The same mention BELOW the declaration is safe today but one reorder from unsafe.
below = ('# alpha.com\n\n**Callable as: Alpha**\n\nA site. Captured 2026-08-06 @ 1440x900.\n\n'
         '## Motion\n\n**Motion fidelity: partial**\n\n'
         '## Notes\n\nThe nav island is `Motion fidelity: spec` in isolation.\n')
code, out, data = run({**CLEAN, 'alpha.com.md': below})
check('a mention below the declaration does not fail', code == 0, fails_of(data))
check('but is warned about as order-dependent',
      'accident of line order' in warns_of(data), warns_of(data))

code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha') + '\n**Motion fidelity: spec**\n'})
check('two page-wide declarations fail', code != 0 and '2 page-wide' in fails_of(data),
      fails_of(data))

# ---- the enum
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='full')})
check('an illegal fidelity value fails', code != 0 and 'not one of' in fails_of(data),
      fails_of(data))
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='Spec')})
check('a title-cased value fails rather than silently reading as `none`',
      code != 0 and 'Spec' in fails_of(data), fails_of(data))
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='partial — no per-animation map')})
check('a trailing rationale clause is legal', code == 0, fails_of(data))

nofid = '# alpha.com\n\n**Callable as: Alpha**\n\nCaptured 2026-08-06 @ 1440x900.\n\n## Motion\n\nIt moves.\n'
code, out, data = run({**CLEAN, 'alpha.com.md': nofid})
check('a missing declaration fails', code != 0 and 'no page-wide' in fails_of(data),
      fails_of(data))

# ---- spec is the only value that licenses building; it must be backed
idx_spec = index([row('Alpha', 'alpha.com', 'spec'), row('Beta', 'beta.com')])
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec')}, idx_spec)
check('spec with no mapping table fails', code != 0 and 'no mapping table' in fails_of(data),
      fails_of(data))
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec', table=SPEC_TABLE)},
                      idx_spec)
check('spec with a real mapping table passes', code == 0, fails_of(data))

header_only = SPEC_TABLE.rsplit('| hero', 1)[0]
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec', table=header_only)},
                      idx_spec)
check('spec with an empty table fails — a header is not a mapping',
      code != 0 and 'no rows' in fails_of(data), fails_of(data))

renamed = SPEC_TABLE.replace('| Trigger |', '| When |')
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec', table=renamed)},
                      idx_spec)
check('spec with renamed columns fails', code != 0 and 'columns are' in fails_of(data),
      fails_of(data))

# partial must NOT be required to carry a table — TEMPLATE defines partial as
# having no per-animation mapping, so demanding one asks for a fabrication.
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='partial')})
check('partial without a table is correct, not a defect', code == 0, fails_of(data))

# ---- names
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', callable_line=False)})
check('a missing Callable line fails', code != 0 and 'no `**Callable as:' in fails_of(data),
      fails_of(data))

dupe = {'alpha.com.md': entry('Alpha'), 'beta.com.md': entry('Alpha')}
code, out, data = run(dupe, index([row('Alpha', 'alpha.com'), row('Beta', 'beta.com')]))
check('two entries claiming one name fail', code != 0 and 'claimed by 2' in fails_of(data),
      fails_of(data))

collide = {'alpha.com.md': entry('Alpha'), 'beta.com.md': entry('Alphabet')}
code, out, data = run(collide, index([row('Alpha', 'alpha.com'), row('Beta', 'beta.com')]))
check('a cross-file substring collision fails', code != 0 and 'substring of' in fails_of(data),
      fails_of(data))

# Within ONE file a short name is by construction a substring of its own slug.
# Firing there would flag every entry in the library.
code, out, data = run({'philllia.com.md': entry('Phillia'), 'beta.com.md': entry('Beta')},
                      index([row('Phillia', 'philllia.com'), row('Beta', 'beta.com')]))
check('a name that is a substring of its OWN slug does not fire', code == 0, fails_of(data))

# motion-spec.py now reads the (aliases: …) parenthetical, so a declared alias
# is reachable and must NOT warn. The check inverts: it warns only if this file's
# key set and the resolver's diverge again.
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', aliases='al, alph')})
check('declared aliases the resolver can now read raise no warning',
      code == 0 and 'cannot reach' not in warns_of(data), warns_of(data))
check('and they are still counted as names for collision purposes',
      code == 0, fails_of(data))
collide_alias = {'alpha.com.md': entry('Alpha', aliases='shared'),
                 'beta.com.md': entry('Beta', aliases='shared')}
code, out, data = run(collide_alias,
                      index([row('Alpha', 'alpha.com'), row('Beta', 'beta.com')]))
check('an alias claimed by two entries is a collision, not a warning',
      code != 0 and 'claimed by 2' in fails_of(data), fails_of(data))

# ---- INDEX is the other resolver over the same fact
code, out, data = run(CLEAN, index([row('Alpha', 'alpha.com')]))
check('an entry with no INDEX row fails', code != 0 and 'no row in INDEX' in fails_of(data),
      fails_of(data))
code, out, data = run(CLEAN, index([row('Alpha', 'alpha.com'), row('Beta', 'beta.com'),
                                    row('Ghost', 'ghost.com')]))
check('an INDEX row pointing at no file fails', code != 0 and 'not on disk' in fails_of(data),
      fails_of(data))
code, out, data = run(CLEAN, index([row('Alpha', 'alpha.com', 'spec'), row('Beta', 'beta.com')]))
check('INDEX and entry disagreeing on fidelity fails',
      code != 0 and 'records `spec`' in fails_of(data), fails_of(data))
code, out, data = run(CLEAN, None)
check('a library with no INDEX.md fails', code != 0 and 'no INDEX.md' in fails_of(data),
      fails_of(data))
code, out, data = run(CLEAN, index([row('Alpha', 'alpha.com', cells=5), row('Beta', 'beta.com')]))
check('a short INDEX row warns', code == 0 and 'cells, not 6' in warns_of(data), warns_of(data))

code, out, data = run(CLEAN, index([row('Alpha', 'alpha.com'), row('Beta', 'beta.com')],
                                   extra='- an orphan pattern bullet\n- another\n'))
check('bullets stranded above the patterns heading warn',
      code == 0 and 'between the table and' in warns_of(data), warns_of(data))

# ---- header
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', viewport='')})
check('a missing capture viewport warns but does not fail',
      code == 0 and 'no capture viewport' in warns_of(data), warns_of(data))

# ---- warnings can never fail the run
noisy = {'alpha.com.md': entry('Alpha', viewport=''),
         'beta.com.md': entry('Beta', viewport='')}
code, out, data = run(noisy, index([row('Alpha', 'alpha.com', cells=5),
                                    row('Beta', 'beta.com')], extra='- orphan\n'))
check('a library with many warnings and no failures still passes',
      code == 0 and len(data['warnings']) >= 4, (code, warns_of(data)))

# ---- "could not run" is not "clean"
empty = tempfile.mkdtemp(dir=root)
r = subprocess.run([sys.executable, GATE, empty], capture_output=True, text=True)
check('an empty library exits 2, not 0', r.returncode == 2, r.stdout + r.stderr)
check('and says a blank library is not a pass', 'not a pass' in (r.stdout + r.stderr),
      r.stdout + r.stderr)
r = subprocess.run([sys.executable, GATE, os.path.join(empty, 'nope')],
                   capture_output=True, text=True)
check('a missing library directory exits 2', r.returncode == 2, r.stdout + r.stderr)

# ---- INDEX.md and TEMPLATE.md are not entries
tmpl = ('# Library entry template\n\n```markdown\n'
        '**Motion fidelity: <spec | partial | signature-only | none>**\n```\n')
code, out, data = run({**CLEAN, 'TEMPLATE.md': tmpl})
check('TEMPLATE.md is skipped, not linted as an entry', code == 0, fails_of(data))
check('and is not counted as an entry', data and data['entries'] == 2, data and data['entries'])

# ---- what counts as a mapping row, and what only looks like one
align_only = SPEC_TABLE.split('\n')[0] + '\n|:---|:---|:---|:---|:---|:---|:---|:---|\n'
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec', table=align_only)},
                      idx_spec)
check('an alignment separator (|:---|) is not a mapping row',
      code != 0 and 'no rows' in fails_of(data), fails_of(data))

borrowed = header_only + '\n## Type\n\n| Step | Size | Line |\n|---|---|---|\n| 1 | 16px | 1.4 |\n'
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec', table=borrowed)},
                      idx_spec)
check('rows from a later, unrelated table are not borrowed as animations',
      code != 0 and 'no rows' in fails_of(data), fails_of(data))

fenced = '```markdown\n' + SPEC_TABLE + '```\n'
code, out, data = run({**CLEAN, 'alpha.com.md': entry('Alpha', fidelity='spec', table=fenced)},
                      idx_spec)
check('a mapping table inside a fence is an example, not a mapping',
      code != 0 and 'no mapping table' in fails_of(data), fails_of(data))

# ---- the lint's regexes must match motion-spec.py's, or it is blind exactly
# ---- where the two resolvers disagree
wrapped = ('# zeta.com\n\n**Callable as: Zeta,\nBeta**\n\nCaptured 2026-08-06 @ 1440x900.\n\n'
           '## Motion\n\n**Motion fidelity: partial**\n')
code, out, data = run({'zeta.com.md': wrapped, 'beta.com.md': entry('Beta')},
                      index([row('Zeta', 'zeta.com'), row('Beta', 'beta.com')]))
check('a callable name that wraps a line is still read, as motion-spec.py reads it',
      code != 0 and 'claimed by 2' in fails_of(data), fails_of(data))

wrapped_reason = ('# alpha.com\n\n**Callable as: Alpha**\n\nCaptured 2026-08-06 @ 1440x900.\n\n'
                  '## Motion\n\n**Motion fidelity: partial — durations and travel measured,\n'
                  'but no per-animation mapping**\n')
code, out, data = run({**CLEAN, 'alpha.com.md': wrapped_reason})
check('a rationale that wraps inside the bold span is legal', code == 0, fails_of(data))
check('and the wrapped value still parses to the bare enum',
      data and data['fidelity']['alpha.com.md'] == 'partial', data and data.get('fidelity'))

# ---- INDEX fidelity comes from the motion column, not from whichever cell bolds first
decoy = ('| **Alpha** | [alpha.com](alpha.com.md) | 2026-08-06 | mirror (**partial** crawl) | '
         '**spec** · `x` @ .3s | Notable |')
code, out, data = run(CLEAN, index([decoy, row('Beta', 'beta.com')]))
check('a fidelity word in the Path cell does not silence the INDEX cross-check',
      code != 0 and 'records `spec`' in fails_of(data), fails_of(data))

innocent = ('| **Alpha** | [alpha.com](alpha.com.md) | 2026-08-06 | mirror | '
            'partial · `x` @ .3s | Motion is **spec**-grade for the nav only |')
code, out, data = run(CLEAN, index([innocent, row('Beta', 'beta.com')]))
check('a fidelity word in the Notable cell does not invent a disagreement',
      code == 0, fails_of(data))

underscored = ('| **Alpha** | [alpha.com](alpha.com.md) | 2026-08-06 | mirror | '
               '__spec__ · `x` @ .3s | Notable |')
code, out, data = run(CLEAN, index([underscored, row('Beta', 'beta.com')]))
check('underscore bold is read as bold, not skipped',
      code != 0 and 'records `spec`' in fails_of(data), fails_of(data))

dotslash = ('| **Alpha** | [alpha.com](./alpha.com.md) | 2026-08-06 | mirror | '
            '**partial** · `x` @ .3s | Notable |')
code, out, data = run(CLEAN, index([dotslash, row('Beta', 'beta.com')]))
check('a ./ relative link resolves rather than reporting a file that exists as missing',
      code == 0, fails_of(data))

# ---- the real library is the strongest fixture there is, when there is one.
# A fresh install ships blank — SKILL.md's "First run / blank library" — and the
# gate exits 2 there. These two checks skip rather than crash, the same way the
# motion suite skips without Chrome.
r = subprocess.run([sys.executable, GATE, '--json'], capture_output=True, text=True)
if r.returncode == 2:
    print('SKIP  shipped library is blank (first-run state) — corpus checks skipped')
    check('a blank shipped library is reported unreadable, not silently passed',
          r.returncode == 2 and 'not a pass' in (r.stdout + r.stderr), r.stdout + r.stderr)
else:
    real = json.loads(r.stdout)
    check('the shipped library passes its own gate', r.returncode == 0, real.get('failures'))
    check('every shipped entry declares a legal fidelity',
          len(real['fidelity']) == real['entries'], (real['fidelity'], real['entries']))

shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
