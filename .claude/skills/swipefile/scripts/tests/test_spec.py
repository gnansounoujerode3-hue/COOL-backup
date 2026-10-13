#!/usr/bin/env python3
"""Motion spec resolution: does a name reach the entry it actually names?

This is the gate that stands between an agent and building a page's motion from
nothing, so the way it fails badly is not refusing — it is answering. Two
measured defects lived here: the `(aliases: …)` parenthetical every entry
advertises was never parsed, so twelve declared aliases resolved to NO SUCH
ENTRY; and the fallback was a bare substring with a `break`, so `--name studio`
returned a different site's spec-grade entry at exit 0 and a name matching two
entries silently got whichever sorted first.

Fixtures are miniature libraries with a real copy of motion-spec.py beside them,
because the script resolves its library from its own location.
"""
import json, os, pathlib as _pl, shutil, subprocess, sys, tempfile
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
SPEC = os.path.join(SCRIPTS, 'motion-spec.py')

SPEC_TABLE = (
    '| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |\n'
    '|---|---|---|---|---|---|---|---|\n'
    '| hero | .hero | load | y 12→0 | 400ms | ease | 60ms | — |\n')


def entry(name, aliases=None, fidelity='partial', table=''):
    head = f'# {name.lower()}.com\n\n**Callable as: {name}**'
    head += f' (aliases: {aliases})\n\n' if aliases else '\n\n'
    head += 'A site. Captured 2026-08-07 @ 1440x900.\n\n'
    return head + f'## Motion\n\n**Motion fidelity: {fidelity}**\n\n{table}\n'


root = tempfile.mkdtemp(prefix='spec-test-')
PASS, FAIL = [], []
made = [0]


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:300] if detail and not cond else ""}')


def lib(entries):
    """A miniature skill folder: library/<file>.md plus a real motion-spec.py."""
    made[0] += 1
    d = os.path.join(root, f'skill{made[0]}')
    os.makedirs(os.path.join(d, 'scripts'), exist_ok=True)
    os.makedirs(os.path.join(d, 'library'), exist_ok=True)
    for fn, text in entries.items():
        open(os.path.join(d, 'library', fn), 'w', encoding='utf-8').write(text)
    open(os.path.join(d, 'library', 'INDEX.md'), 'w', encoding='utf-8').write('# index\n')
    open(os.path.join(d, 'library', 'TEMPLATE.md'), 'w', encoding='utf-8').write('# template\n')
    shutil.copy2(SPEC, os.path.join(d, 'scripts', 'motion-spec.py'))
    return d


def run(d, *args):
    r = subprocess.run([sys.executable, os.path.join(d, 'scripts', 'motion-spec.py'), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


CORPUS = {
    'youtube.com.md': entry('YouTube', aliases='youtube, yt'),
    'createstudio.framer.media.md': entry('CreateStudio', aliases='create studio',
                                          fidelity='spec', table=SPEC_TABLE),
    'landonorris.com.md': entry('Lando Norris', aliases='lando, landonorris',
                                fidelity='signature-only'),
}
d = lib(CORPUS)

# ---- the names an entry actually advertises must all resolve
code, out = run(d, '--name', 'YouTube')
check('the bolded callable name resolves', code != 0 and 'NO SUCH ENTRY' not in out, out[-200:])
code, out = run(d, '--name', 'yt')
check('an alias from the (aliases: …) parenthetical resolves',
      'NO SUCH ENTRY' not in out, out[-200:])
code, out = run(d, '--name', 'youtube.com')
check('the filename slug resolves', 'NO SUCH ENTRY' not in out, out[-200:])
code, out = run(d, '--name', 'lando norris')
check('a spaced name resolves against its unspaced slug',
      'NO SUCH ENTRY' not in out, out[-200:])
code, out = run(d, '--name', 'create studio')
check('a multi-word alias resolves', 'NO SUCH ENTRY' not in out, out[-200:])

# ---- and nothing else may
code, out = run(d, '--name', 'studio')
check('a bare substring does NOT silently resolve to a spec-grade entry',
      code == 2 and 'buildable' not in out, out[-200:])
check('and it says no such entry rather than guessing',
      'NO SUCH ENTRY' in out, out[-200:])

amb = lib({'meta.com.md': entry('Meta'), 'metabase.com.md': entry('Metabase')})
code, out = run(amb, '--name', 'meta')
check('an exact name still wins over a longer sibling',
      'NO SUCH ENTRY' not in out and 'AMBIGUOUS' not in out, out[-200:])
code, out = run(amb, '--name', 'met')
check('a prefix matching two entries is reported ambiguous, not guessed',
      code == 2 and 'AMBIGUOUS' in out, out[-200:])
check('and both candidates are named', 'meta.com' in out and 'metabase.com' in out, out[-200:])

# ---- the refusal that is the whole point of the script
code, out = run(d, '--name', 'CreateStudio')
check('a spec-grade entry is buildable at exit 0', code == 0 and '"buildable": true' in out,
      out[-200:])
check('and reports the entry it resolved to', '"name": "createstudio.framer.media"' in out,
      out[-200:])
code, out = run(d, '--name', 'YouTube')
check('a partial entry is REFUSED', code == 1 and 'REFUSED' in out, out[-200:])
code, out = run(d, '--name', 'lando')
check('a signature-only entry is REFUSED', code == 1 and 'REFUSED' in out, out[-200:])

# ---- a blank library is the documented first-run state, not a broken tool
blank = lib({})
code, out = run(blank, '--list')
check('--list on a blank library explains rather than printing nothing',
      code == 0 and 'library is empty' in out.lower(), repr(out))
check('and names the command that starts one', '--url' in out, out)
code, out = run(blank, '--name', 'Anything')
check('--name on a blank library says the library is empty',
      code == 2 and 'EMPTY' in out.upper(), out[-200:])

# ---- --list on a real library
code, out = run(d, '--list')
check('--list marks the spec entry buildable',
      'buildable' in out and 'createstudio.framer.media' in out, out)
check('--list marks the others NOT buildable', 'NOT buildable' in out, out)

shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
