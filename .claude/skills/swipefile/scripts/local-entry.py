#!/usr/bin/env python3
"""
Local entry writer — a local model drafts library entries, behind two gates.

Writing an entry is the one Step 5 job that is labor rather than judgment: the
measurements already exist, the template already prescribes the shape, and the
gates already define correct. That makes it the right job for a local model —
free, private, and repeatable — and the wrong job to trust one on unsupervised:
measured on this machine, a 7B handed a capture JSON invented a capture date
and dropped every hex and curve while producing perfect structure. So nothing a
model writes here reaches the library on its own word. Every draft must clear
`library-lint.py` (the resolver can read it) AND `provenance.py` (every number
traces to the capture), and a failed draft is retried with the gate output fed
back into the prompt — a fabricating model costs retries, never corruption.

    python3 local-entry.py --measured capture.json --domain example.com
    python3 local-entry.py --measured capture.json --domain example.com --write
    python3 local-entry.py --measured capture.json --domain example.com \\
        --name Meridian --aliases "meridian, the coffee one" --retries 4

Fidelity is decided HERE, deterministically from what the capture holds — the
model is told the value and checked against it, never asked to judge it:
`spec` needs a per-animation mapping in the capture; easings without one is
`partial`; curves alone is `signature-only`; no motion data is `none`.

Without --write the accepted entry is left in the output directory for review.
With --write it lands in library/ plus an INDEX row, and the whole library is
re-linted afterwards — if that final belt fails, both changes roll back.

Exit 0 is an entry that cleared both gates. Exit 1 means every retry failed
(last gate output shown), or installing made the real library fail its gate and
the library was restored byte-for-byte. Exit 2 is environment or operator:
Ollama unreachable, the model not pulled, inputs unreadable, or the domain
already has an entry and --force was not given.
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys, tempfile
import urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), 'library')
DEFAULT_MODEL = 'qwen3-coder:30b'
DOMAIN_OK = re.compile(r'^[A-Za-z0-9][A-Za-z0-9.-]*$')
SPEC_COLUMNS = '| Name | Target | Trigger | From → To | Duration | Easing | Stagger | Scroll start/end |'


def decide_fidelity(capture):
    """The one judgment call in the pipeline, and it is not the model's."""
    motion = capture.get('motion')
    motion = motion if isinstance(motion, dict) else {}
    animations = motion.get('animations') or []
    if animations and all(isinstance(x, dict) and x.get('target') and x.get('trigger')
                          for x in animations):
        return 'spec'
    numeric = [k for k in ('durations_ms', 'travel_px', 'stagger_ms') if motion.get(k)]
    if motion.get('easings') and not numeric:
        return 'signature-only'
    if motion.get('easings') or numeric:
        return 'partial'
    return 'none'


def build_prompt(capture, domain, name, aliases, date, fidelity, feedback):
    rules = f"""Write a swipefile library entry as markdown. It will be MACHINE-CHECKED
against the rules below and against the capture JSON; a violation is rejected
and you will be asked again, so follow them exactly.

STRUCTURE:
- line 1: `# {domain}`
- line 3 exactly: `**Callable as: {name}** (aliases: {aliases})`
- a header line containing: Captured {date} @ {capture.get('viewport', 'the measured viewport')}.
- sections with `## ` headings covering, in this order where the capture has
  data for them: Type, Layout, Colour, Motion, Interaction states.
- the `## Motion` section contains exactly this line, verbatim:
  `**Motion fidelity: {fidelity}**`

TRUTH:
- Use ONLY values present in the capture JSON below. Every number, hex colour,
  easing curve, and date you write is diffed against it; anything it does not
  contain is a rejection.
- Include EVERY hex colour and EVERY cubic-bezier the capture holds.
- Describe the system in words (what the scale does, what role each colour
  plays), but EVERY number you write — including any ratio — must literally
  appear in the capture JSON. If a ratio is not in the JSON, describe it
  without digits.
- Nothing about the site may be invented, estimated, or recalled from your
  training data. If the capture does not measure it, the entry does not say it.
"""
    if fidelity == 'spec':
        rules += f"""- After the fidelity line, emit the mapping table with header
  `{SPEC_COLUMNS}`
  and one row per item of motion.animations, using only that item's values.
"""
    prompt = rules + f'\nCAPTURE JSON:\n{json.dumps(capture, indent=1)}\n'
    if feedback:
        prompt += ('\nYOUR PREVIOUS ATTEMPT WAS REJECTED by the machine gates. '
                   'The exact findings, each of which must be fixed:\n'
                   + '\n'.join(f'- {f}' for f in feedback)
                   + '\nRegenerate the complete entry with these corrected.\n')
    prompt += '\nOutput ONLY the markdown entry. No commentary, no code fences.\n'
    return prompt


def die(msg):
    """Environment failure: nothing was generated. Exit 2, never 1 — the caller
    must be able to tell 'the model wrote a bad entry' from 'there is no model'."""
    print(msg, file=sys.stderr)
    sys.exit(2)


def ollama(url, payload, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        die(f'{url} returned non-JSON ({body[:120]!r}) — a proxy or a streaming '
            f'endpoint, not the Ollama API.')


def generate(base, model, prompt):
    try:
        out = ollama(f'{base}/api/generate',
                     {'model': model, 'prompt': prompt, 'stream': False,
                      'options': {'temperature': 0.2, 'num_ctx': 8192,
                                  'num_predict': 2000}})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        if 'not found' in body.lower():
            try:
                tags = json.loads(urllib.request.urlopen(f'{base}/api/tags',
                                                         timeout=10).read())
                have = ', '.join(m['name'] for m in tags.get('models', [])) or 'none'
            except OSError:
                have = 'unknown'
            die(f'model "{model}" is not pulled. Installed: {have}.\n'
                f'  ollama pull {model}')
        die(f'ollama returned an error: {body[:300]}')
    except OSError as e:
        die(f'cannot reach Ollama at {base} ({e}). Is it running? '
            f'Start the Ollama app or `ollama serve`.')
    text = out.get('response')
    if not isinstance(text, str):
        die(f'ollama returned no text response (got {type(text).__name__}) — '
            f'is {model} a text model?')
    lines = text.strip().splitlines()
    if lines and lines[0].startswith('```'):
        lines = lines[1:]                    # wrapper fence; inner blocks survive
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines).strip() + '\n'


def index_row(domain, name, date, fidelity, capture):
    motion = capture.get('motion')
    motion = motion if isinstance(motion, dict) else {}
    easings = motion.get('easings') or []
    durations = motion.get('durations_ms') or []
    top_curve = easings[0][0] if easings and isinstance(easings[0], list) else None
    top_ms = durations[0][0] if durations and isinstance(durations[0], list) else None
    sig = f'`{top_curve}` @ {top_ms}ms' if top_curve and top_ms else (
        f'`{top_curve}`' if top_curve else '—')
    path = capture.get('path', 'capture only')
    notable = capture.get('notable', 'written by local-entry.py; verify on first use')
    return (f'| **{name}** | [{domain}]({domain}.md) | {date} | {path} | '
            f'**{fidelity}** · {sig} | {notable} |')


def gate(entry_path, capture_path, date, lib_template, index_line, domain):
    """Both gates against a scaffold library. Returns the combined failure list."""
    failures = []
    with tempfile.TemporaryDirectory(prefix='local-entry-') as tmp:
        shutil.copy2(lib_template, os.path.join(tmp, 'TEMPLATE.md'))
        with open(os.path.join(tmp, 'INDEX.md'), 'w', encoding='utf-8') as f:
            f.write('# Design library — index\n\n'
                    '| Call it | Site | Captured | Path | Motion fidelity · signature '
                    '| Notable |\n|---|---|---|---|---|---|\n'
                    f'{index_line}\n\n## Cross-site patterns observed\n\n')
        shutil.copy2(entry_path, os.path.join(tmp, f'{domain}.md'))
        for script, args in (('library-lint.py', [tmp, '--json']),
                             ('provenance.py', [os.path.join(tmp, f'{domain}.md'),
                                                capture_path, '--allow', date, '--json'])):
            r = subprocess.run([sys.executable, os.path.join(HERE, script), *args],
                               capture_output=True, text=True)
            try:
                failures += json.loads(r.stdout).get('failures', [])
            except json.JSONDecodeError:
                failures.append(f'{script} did not return JSON: '
                                f'{(r.stderr or r.stdout)[:200]}')
    return failures


def install(entry_path, index_line, lib, domain, force):
    """Into the real library, with the whole library re-linted as the final belt.

    Rollback restores BYTES, not intentions: adversarial review produced a run
    where the old rollback deleted a pre-existing hand-written entry it had just
    overwritten, printed "rolled back", and left the INDEX pointing at a file
    that no longer existed — wedging every later --write. So the previous entry
    content is snapshotted alongside the INDEX, an existing entry is refused
    outright without --force, and --force replaces the old INDEX row rather
    than stacking a second one.
    """
    dest = os.path.join(lib, f'{domain}.md')
    index_path = os.path.join(lib, 'INDEX.md')
    original_index = open(index_path, encoding='utf-8').read()
    original_entry = (open(dest, encoding='utf-8').read()
                      if os.path.exists(dest) else None)
    has_row = f']({domain}.md)' in original_index
    if (original_entry is not None or has_row) and not force:
        die(f'{domain} already has an entry in {lib}. Re-run with --force to replace '
            f'it (the old INDEX row is replaced too), or pick another domain.')

    lines = [l for l in original_index.splitlines(keepends=True)
             if f']({domain}.md)' not in l]           # --force replaces, never stacks
    at = max((i for i, l in enumerate(lines) if l.lstrip().startswith('|')),
             default=None)
    if at is None:
        die(f'{index_path} has no table to append to — is it an index?')
    if not lines[at].endswith('\n'):
        lines[at] += '\n'
    lines.insert(at + 1, index_line + '\n')
    shutil.copy2(entry_path, dest)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(''.join(lines))
    r = subprocess.run([sys.executable, os.path.join(HERE, 'library-lint.py'), lib],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if original_entry is None:
            os.remove(dest)
        else:
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(original_entry)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(original_index)
        raise SystemExit('installing this entry made the REAL library fail its gate, '
                         'so the library was restored byte-for-byte:\n'
                         + '\n'.join(l for l in r.stdout.splitlines()
                                     if l.lstrip().startswith('FAIL'))[:600])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--measured', required=True, help='capture JSON for one site')
    ap.add_argument('--domain', required=True, help='e.g. example.com — names the entry file')
    ap.add_argument('--name', help='callable name; default: first domain label, capitalised')
    ap.add_argument('--aliases', help='comma-separated; default: the domain label')
    ap.add_argument('--model', default=DEFAULT_MODEL)
    ap.add_argument('--ollama', default='http://localhost:11434')
    ap.add_argument('--date', help='capture date; default: the JSON\'s `captured`, else today')
    ap.add_argument('--retries', type=int, default=3)
    ap.add_argument('--library', default=LIB,
                    help='library to install into (default: the one beside this skill)')
    ap.add_argument('--out', default='.', help='where the draft is left without --write')
    ap.add_argument('--write', action='store_true',
                    help='install into the library on success; default leaves a draft')
    ap.add_argument('--force', action='store_true',
                    help='with --write: replace an existing entry for this domain '
                         '(and its INDEX row) instead of refusing')
    ap.add_argument('--json', dest='json_out', action='store_true')
    a = ap.parse_args()

    try:
        capture = json.load(open(a.measured, encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        print(f'cannot read {a.measured}: {e}', file=sys.stderr)
        sys.exit(2)
    if not DOMAIN_OK.match(a.domain):
        print(f'--domain {a.domain!r} is not a bare hostname. It becomes a filename '
              f'and an INDEX cell, so only [A-Za-z0-9.-] is safe — pass the host, '
              f'not a URL or a path.', file=sys.stderr)
        sys.exit(2)
    if not isinstance(capture, dict):
        print(f'{a.measured} is not a JSON object — a capture is one site\'s '
              f'measurements, not a list.', file=sys.stderr)
        sys.exit(2)
    lib_template = os.path.join(a.library, 'TEMPLATE.md')
    if not os.path.exists(lib_template):
        print(f'no TEMPLATE.md in {a.library} — not a library', file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(os.path.join(a.library, 'INDEX.md')):
        print(f'no INDEX.md in {a.library} — create the scaffold first (see SKILL.md '
              f'"First run / blank library").', file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(a.out):
        print(f'--out {a.out} is not a directory.', file=sys.stderr)
        sys.exit(2)

    label = a.domain.split('.')[0]
    name = a.name or label.capitalize()
    aliases = a.aliases or label
    date = a.date or capture.get('captured') or datetime.date.today().isoformat()
    fidelity = decide_fidelity(capture)
    row = index_row(a.domain, name, date, fidelity, capture)
    draft = os.path.join(a.out, f'{a.domain}.md')

    feedback, attempts = [], []
    for attempt in range(1, a.retries + 1):
        prompt = build_prompt(capture, a.domain, name, aliases, date, fidelity, feedback)
        text = generate(a.ollama, a.model, prompt)
        with open(draft, 'w', encoding='utf-8') as f:
            f.write(text)
        failures = []
        if not text.startswith(f'# {a.domain}'):
            failures.append(f'the output must BEGIN with `# {a.domain}` — no preamble, '
                            f'no commentary, no fences.')
        if f'**Motion fidelity: {fidelity}**' not in text:
            failures.append(f'the entry must declare `**Motion fidelity: {fidelity}**` '
                            f'verbatim — that value was decided from the capture, '
                            f'not by you.')
        failures += gate(draft, a.measured, date, lib_template, row, a.domain)
        attempts.append({'attempt': attempt, 'failures': failures})
        print(f'attempt {attempt}/{a.retries}: '
              + ('both gates PASS' if not failures else f'{len(failures)} gate failure(s)'),
              file=sys.stderr)
        if not failures:
            break
        for f_ in failures[:6]:
            print(f'    {f_[:160]}', file=sys.stderr)
        feedback = failures
    else:
        if a.json_out:
            print(json.dumps({'pass': False, 'attempts': attempts, 'draft': draft}, indent=1))
        else:
            print(f'\nLOCAL ENTRY: FAIL — {a.retries} attempt(s) exhausted. Last draft '
                  f'kept at {draft} for inspection.')
        sys.exit(1)

    installed = False
    if a.write:
        install(draft, row, a.library, a.domain, a.force)
        os.remove(draft)
        installed = True
    if a.json_out:
        print(json.dumps({'pass': True, 'attempts': attempts, 'fidelity': fidelity,
                          'installed': installed,
                          'entry': os.path.join(a.library, f'{a.domain}.md')
                          if installed else draft, 'indexRow': row}, indent=1))
    else:
        where = (f'installed into {a.library}' if installed
                 else f'draft at {draft} — re-run with --write to install')
        print(f'\nLOCAL ENTRY: PASS after {len(attempts)} attempt(s) — {where}')
    sys.exit(0)


if __name__ == '__main__':
    main()
