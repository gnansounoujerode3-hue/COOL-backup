#!/usr/bin/env python3
"""
Library gate — does the library still say what its readers think it says?

The library is the one artifact this skill claims compounds, and the claim rests
on structure: "Uniform structure is what makes the library trainable — a
freeform library is just notes." Nothing checked that. Worse, two readers parse
the same fact and neither validates it. `motion-spec.py` reads `Motion
fidelity:` with an unanchored regex that takes the FIRST hit anywhere in the
file, so a component-scoped `spec` note sitting above the page-wide declaration
silently promotes a `partial` entry to buildable — the refusal that exists to
prevent "correct type, correct colour, dead page" hands over a green light
instead. Meanwhile Step 0 routes the agent through `INDEX.md`, which
`motion-spec.py` never opens, so the two can disagree forever.

Every FAIL rule here has ZERO violators on the current library. That is the
point: this is a regression guard on failures that are invisible where they
happen, not a cleanup of a corpus that is already fine. Rules that would fire on
half the corpus are warnings or were left out — a gate that cries wolf gets
ignored, which is the failure this whole folder keeps paying for.

    python3 library-lint.py
    python3 library-lint.py ../library      # a specific library
    python3 library-lint.py --json

Exit 0 means the entries still parse the way motion-spec.py and Step 0 assume.
Exit 1 means one of them would now silently mis-resolve. Exit 2 means there was
no library to read, which is not the same as a clean one.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), 'library')
SKIP = ('INDEX.md', 'TEMPLATE.md')

FIDELITY = ('spec', 'partial', 'signature-only', 'none')
BUILDABLE = 'spec'
# The value that licenses building motion without re-capturing, and therefore
# the only one whose mapping table has to exist.
SPEC_COLUMNS = ['Name', 'Target', 'Trigger', 'From → To', 'Duration', 'Easing',
                'Stagger', 'Scroll start/end']

# The page-wide declaration, anchored to the start of a line and to bold. A
# backticked or indented mention cannot match this — which is the whole point,
# because it is exactly what the runtime regex below CAN match.
DECLARATION = re.compile(r'^\*\*Motion fidelity:\s*([^*]+?)\s*\*\*', re.M)
# motion-spec.py:40, copied verbatim. Not imported: if that file changes, this
# gate must be updated deliberately rather than silently tracking a new bug.
RUNTIME = re.compile(r'Motion fidelity:\s*\**\s*([a-z-]+)')
MENTION = re.compile(r'Motion fidelity:')
CALLABLE = re.compile(r'\*\*Callable as:\s*([^*]+?)\s*\*\*')
ALIASES = re.compile(r'\*\*Callable as:[^*]+\*\*\s*\(aliases:([^)]*)\)')
SPEC_HEADER = re.compile(r'^\|\s*Name\s*\|.*$', re.M)
VIEWPORT = re.compile(r'@\s*\d{3,4}\s*[x×]\s*\d{3,4}')


def line_of(text, pos):
    return text.count('\n', 0, pos) + 1


def read_entries(lib):
    """(filename, text) for every entry, skipping INDEX and TEMPLATE.

    The skip is not tidiness: TEMPLATE.md's fenced example carries a literal
    `**Motion fidelity: <spec | partial | signature-only | none>**`, which fails
    the enum rule. motion-spec.py:36 skips the same two files.
    """
    out = []
    for fn in sorted(os.listdir(lib)):
        if not fn.endswith('.md') or fn in SKIP:
            continue
        with open(os.path.join(lib, fn), encoding='utf-8') as f:
            out.append((fn, f.read()))
    return out


def keys_for(fn, text):
    """Every name this entry answers to, built the way motion-spec.py builds it."""
    keys = {fn[:-3].lower()}
    m = CALLABLE.search(text)
    if m:
        keys |= {p.strip().lower() for p in re.split(r'[,/]', m.group(1)) if p.strip()}
    al = ALIASES.search(text)
    if al:
        keys |= {p.strip().lower() for p in al.group(1).split(',') if p.strip()}
    return keys


def index_rows(lib):
    """Data rows of INDEX.md as (lineno, cells, link_target, fidelity_token)."""
    path = os.path.join(lib, 'INDEX.md')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        text = f.read()
    rows = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s.startswith('|') or set(s) <= set('|- '):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if cells and cells[0] == 'Call it':
            continue
        link = re.search(r'\]\(([^)]+\.md)\)', s)
        # Column 4 is `Motion fidelity · signature`. Scanning every cell lets a
        # `**partial**` in the Path or Notable text answer for the motion column,
        # which both hides real disagreements and invents fake ones.
        motion_cell = cells[4] if len(cells) > 4 else ''
        m = re.search(r'(?:\*\*|__)([a-z-]+)(?:\*\*|__)', motion_cell)
        fid = m.group(1) if m and m.group(1) in FIDELITY else None
        target = os.path.basename(link.group(1)) if link else None
        rows.append((i, cells, target, fid))
    return rows, text


def check_fidelity(fn, text, fails, warns):
    """The declaration is authoritative, legal, and the one the runtime reads."""
    decls = list(DECLARATION.finditer(text))
    if not decls:
        fails.append(f'MOTION: {fn} has no page-wide `**Motion fidelity: <value>**` '
                     f'declaration. motion-spec.py defaults a missing one to `none` '
                     f'and refuses to build from the entry — silently, and for the '
                     f'wrong reason. Add it under `## Motion` per library/TEMPLATE.md.')
        return None
    if len(decls) > 1:
        fails.append(f'MOTION: {fn} has {len(decls)} page-wide fidelity declarations '
                     f'(lines {", ".join(str(line_of(text, d.start())) for d in decls)}). '
                     f'Exactly one is authoritative; delete or rescope the rest.')
    decl = decls[0]
    value = ' '.join(re.split(r'[—–]', decl.group(1))[0].split())
    if value not in FIDELITY:
        fails.append(f'MOTION: {fn} declares `Motion fidelity: {value}`, which is not one '
                     f'of {", ".join(FIDELITY)}. motion-spec.py matches case-sensitively '
                     f'and falls back to `none`, so this entry reads as unmeasured no '
                     f'matter what it actually holds.')
        return None

    hit = RUNTIME.search(text)
    if hit and line_of(text, hit.start()) != line_of(text, decl.start()):
        fails.append(
            f'MOTION: {fn} declares `{value}` at line {line_of(text, decl.start())}, but '
            f'motion-spec.py reads the FIRST "Motion fidelity:" in the file and would '
            f'take `{hit.group(1)}` from line {line_of(text, hit.start())}. Move the '
            f'component-scoped mention below the page-wide declaration.')
    elif len(MENTION.findall(text)) > 1:
        warns.append(
            f'MOTION: {fn} mentions "Motion fidelity:" '
            f'{len(MENTION.findall(text))} times. The runtime takes the first by file '
            f'order, so this entry is correct only by accident of line order — one '
            f'addendum reordered above line {line_of(text, decl.start())} flips it.')
    return value


def without_fences(text):
    """Fenced blocks are examples. A table nobody renders is not a mapping."""
    return re.sub(r'^```.*?^```', '', text, flags=re.S | re.M)


def check_spec_table(fn, text, value, fails):
    """`spec` is the only value that licenses building without re-capturing.

    motion-spec.py gates on the string alone and never looks for the mapping, so
    a spec claim with no table returns buildable:true and the agent builds from
    nothing. Deliberately NOT extended to `partial`: TEMPLATE defines partial as
    having no per-animation mapping, so requiring the table there would punish
    four entries for declining to fabricate one.
    """
    if value != BUILDABLE:
        return
    text = without_fences(text)
    m = SPEC_HEADER.search(text)
    if not m:
        fails.append(f'MOTION: {fn} declares `spec` but carries no mapping table. '
                     f'`spec` is the only value that licenses building motion from the '
                     f'entry; without the table there is no target, trigger, from/to or '
                     f'stagger to build. Downgrade to `partial` or add the table.')
        return
    cells = [c.strip() for c in m.group(0).strip().strip('|').split('|')]
    if cells != SPEC_COLUMNS:
        fails.append(f'MOTION: {fn} declares `spec` but its mapping table columns are '
                     f'{cells}, not {SPEC_COLUMNS}. The column names are the '
                     f'references/motion.md vocabulary; a renamed column is a spec '
                     f'nobody can read back.')
        return
    rows = []
    # `$` stops before the newline, so the slice opens with one empty line that
    # would otherwise end the scan before it began.
    tail = text[m.end():]
    for line in (tail[1:] if tail.startswith('\n') else tail).splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            break                      # the table ends at the first non-table line
        if set(stripped) <= set('|-: '):
            continue                   # separator, including `|:---|` alignment rows
        rows.append(stripped)
    if not rows:
        fails.append(f'MOTION: {fn} declares `spec` and has the mapping table header but '
                     f'no rows under it. An empty table is a `signature-only` entry '
                     f'claiming to be buildable.')


def check_names(entries, fails):
    """No name may resolve to two entries, and none may shadow another's."""
    owners = {}
    for fn, text in entries:
        if not CALLABLE.search(text):
            fails.append(f'NAME: {fn} has no `**Callable as: <Name>**` line. Entries are '
                         f'ordered by name ("reference: Lando Norris"); an unnamed entry '
                         f'is reachable only by its domain slug.')
        for k in keys_for(fn, text):
            owners.setdefault(k, set()).add(fn)
    for key, files in sorted(owners.items()):
        if len(files) > 1:
            fails.append(f'NAME: "{key}" is claimed by {len(files)} entries '
                         f'({", ".join(sorted(files))}). motion-spec.py assigns into a '
                         f'plain dict with no collision check, so the last one read wins '
                         f'and the others become unreachable.')
    # Within one file `phillia` ⊂ `philllia` is normal; across files it means a
    # substring query silently resolves to somebody else's entry.
    flat = sorted(owners)
    for a in flat:
        for b in flat:
            if a is b or owners[a] & owners[b]:
                continue
            if a.replace(' ', '') in b.replace(' ', '').replace('.', ''):
                fails.append(f'NAME: "{a}" ({", ".join(sorted(owners[a]))}) is a substring '
                             f'of "{b}" ({", ".join(sorted(owners[b]))}). motion-spec.py '
                             f'falls back to substring matching and breaks on the first '
                             f'hit, so one of these silently answers for the other.')


def check_aliases_resolve(entries, warns):
    """Every declared alias must resolve through motion-spec.py's own parser.

    This once reported 12 dead aliases across the library and correctly blamed
    the script rather than the entries: `[^*]+` stopped at the closing `**`, so
    the `(aliases: …)` parenthetical every entry advertises was never read.
    motion-spec.py now reads it, so the check inverts — it re-derives the
    resolver's key set and warns only if an entry declares a name the resolver
    still cannot reach. A gate that keeps warning after its bug is fixed teaches
    people to ignore it.
    """
    dead = []
    for fn, text in entries:
        resolvable = {fn[:-3].lower()}
        m = CALLABLE.search(text)
        if m:
            resolvable |= {p.strip().lower() for p in re.split(r'[,/]', m.group(1)) if p.strip()}
        al = ALIASES.search(text)
        if al:
            resolvable |= {p.strip().lower().strip('"\'') for p in al.group(1).split(',')
                           if p.strip()}
        for k in sorted(keys_for(fn, text) - resolvable):
            dead.append(f'{k} ({fn})')
    if dead:
        warns.append(f'NAME: {len(dead)} declared name(s) the resolver cannot reach — '
                     f'{", ".join(dead[:8])}{" …" if len(dead) > 8 else ""}. Compare '
                     f'keys_for() here against entries() in motion-spec.py; the two '
                     f'must agree or a name resolves in one and not the other.')


def check_index(lib, entries, declared, fails, warns):
    """INDEX and the entries are two resolvers over one fact, with no cross-check."""
    got = index_rows(lib)
    if got is None:
        fails.append('INDEX: no INDEX.md. Step 0 reads it before every capture, and it is '
                     'the only place a reference is resolvable by name.')
        return
    rows, text = got
    linked = {t for _, _, t, _ in rows if t}
    files = {fn for fn, _ in entries}
    for missing in sorted(files - linked):
        fails.append(f'INDEX: {missing} has no row in INDEX.md. Step 0 reads the index, '
                     f'not the directory, so an unlisted entry is one nobody can order.')
    for orphan in sorted(linked - files):
        fails.append(f'INDEX: a row links to {orphan}, which is not on disk.')
    for lineno, cells, target, fid in rows:
        if len(cells) != 6:
            warns.append(f'INDEX: line {lineno} has {len(cells)} cells, not 6 '
                         f'(Call it | Site | Captured | Path | Motion fidelity · '
                         f'signature | Notable).')
        if target and target in declared and fid and fid != declared[target]:
            fails.append(f'INDEX: line {lineno} records `{fid}` for {target}, but the '
                         f'entry declares `{declared[target]}`. Step 0 plans motion off '
                         f'this cell and motion-spec.py never opens this file, so the '
                         f'disagreement is invisible at the point it matters.')
        if target and target in declared and not fid:
            warns.append(f'INDEX: line {lineno} ({target}) has no bolded fidelity token '
                         f'in its motion cell. SKILL.md reads fidelity off this column '
                         f'at Step 0 to pick a donor.')
    # Bullets stranded between the table and the next heading are invisible to a
    # heading-anchored reader — the cross-site patterns are the compounding part.
    lines = text.splitlines()
    last_row = max((i for i, l in enumerate(lines) if l.strip().startswith('| ')), default=-1)
    nxt = next((i for i, l in enumerate(lines) if i > last_row and l.startswith('## ')), None)
    if nxt is not None:
        orphans = [i + 1 for i in range(last_row + 1, nxt) if lines[i].startswith('- ')]
        if orphans:
            warns.append(f'INDEX: {len(orphans)} bullet(s) sit between the table and the '
                         f'next heading (lines {orphans[0]}-{orphans[-1]}). A reader that '
                         f'locates cross-site patterns by their heading misses them.')


def check_header(fn, text, warns):
    """Header facts scoped to the block above the first heading, not to one line."""
    head = text.split('\n## ', 1)[0]
    if not VIEWPORT.search(head):
        warns.append(f'HEADER: {fn} records no capture viewport (`@ 1440x900`). Every px '
                     f'in the entry is uninterpretable without the width it was measured '
                     f'at, and the entry is meant to stand alone.')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('library', nargs='?', default=LIB,
                    help='library directory (default: the one beside this skill; '
                         'overridable so the test suite can point at a fixture)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if not os.path.isdir(a.library):
        print(f'no library at {a.library}', file=sys.stderr)
        sys.exit(2)
    entries = read_entries(a.library)
    if not entries:
        print(f'{a.library} holds no entries — nothing to check. A blank library is the '
              f'documented first-run state, not a pass.', file=sys.stderr)
        sys.exit(2)

    fails, warns, notes = [], [], []
    declared = {}
    for fn, text in entries:
        value = check_fidelity(fn, text, fails, warns)
        if value:
            declared[fn] = value
            check_spec_table(fn, text, value, fails)
        check_header(fn, text, warns)
    check_names(entries, fails)
    check_aliases_resolve(entries, warns)
    check_index(a.library, entries, declared, fails, warns)

    buildable = sorted(fn for fn, v in declared.items() if v == BUILDABLE)
    notes.append(f'{len(buildable)} of {len(entries)} entries are `{BUILDABLE}`-grade and '
                 f'can carry motion without re-capture: {", ".join(buildable) or "none"}')

    ok = not fails
    if a.json:
        print(json.dumps({'pass': ok, 'library': a.library, 'entries': len(entries),
                          'failures': fails, 'warnings': warns, 'notes': notes,
                          'fidelity': declared}, indent=1))
    else:
        print(f'{a.library}  —  {len(entries)} entries')
        for x in notes:
            print(f'  note  {x}')
        for x in warns:
            print(f'  WARN  {x}')
        for x in fails:
            print(f'  FAIL  {x}')
        print('\nLIBRARY GATE: ' + ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
