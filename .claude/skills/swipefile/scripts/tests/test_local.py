#!/usr/bin/env python3
"""Local entry loop: does a fabricating model cost retries, never corruption?

The model here is a fake — an in-process HTTP server speaking Ollama's API,
scripted per scenario by model name. That is the point: the loop's correctness
is retry wiring, feedback routing, gate order, and rollback, none of which need
weights, and a suite that needed a 19 GB model would never run in CI or on a
fresh install. The one thing a fake cannot test — whether a real model
converges — is a measurement to make once, not a regression to re-run.
"""
import json, os, pathlib as _pl, shutil, socket, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
SCRIPTS = str(_pl.Path(__file__).resolve().parent.parent)
LOCAL = os.path.join(SCRIPTS, 'local-entry.py')
LINT = os.path.join(SCRIPTS, 'library-lint.py')
TEMPLATE = os.path.join(os.path.dirname(SCRIPTS), 'library', 'TEMPLATE.md')

CAPTURE = {
    'viewport': '1440x900', 'captured': '2026-08-07', 'path': 'mirror',
    'type': {'families': ['Satoshi 500'], 'scale': 'clamp() pinned to 1440',
             'steps_px': [14, 16, 20, 28, 46]},
    'colour': {'hex': ['#0e0e0e', '#f5f3ef', '#ff6041'], 'system': 'greyscale + accent'},
    'motion': {'easings': [['cubic-bezier(.22,1,.36,1)', 41]],
               'durations_ms': [[300, 38]], 'travel_px': 8, 'stagger_ms': 80},
    'breakpoints': [810, 1200],
}

GOOD = """# meridian.test

**Callable as: Meridian** (aliases: meridian)

A site. Captured 2026-08-07 @ 1440x900.

## Type

Satoshi 500. Scale clamp() pinned to 1440: 14/16/20/28/46px.

## Colour

#0e0e0e ink, #f5f3ef paper, #ff6041 accent — greyscale + accent.

## Motion

**Motion fidelity: partial**

`cubic-bezier(.22,1,.36,1)` (41 uses) @ 300ms, travel 8px, stagger 80ms.
Breakpoints 810 / 1200.
"""

BAD = """# meridian.test

**Callable as: Meridian** (aliases: meridian)

Captured 2023-11-15 @ 1440x900.

## Motion

**Motion fidelity: partial**

Smooth entrance animations with elegant easing throughout.
"""

# Scenarios keyed by the --model string the CLI sends.
SCRIPTS_BY_MODEL = {
    'retry-fab': [BAD, '```markdown\n' + GOOD + '```'],
    'first-good': [GOOD],
    'always-bad': [BAD, BAD, BAD, BAD],
    'wrong-fidelity': [GOOD.replace('**Motion fidelity: partial**',
                                    '**Motion fidelity: spec**'), GOOD],
    'chatter': ['Sure! Here is the entry you asked for:\n\n' + GOOD, GOOD],
}
PROMPTS = {}     # model -> [prompt, ...], recorded for assertions
LOCK = threading.Lock()


class FakeOllama(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/tags':
            return self._send({'models': [{'name': m} for m in SCRIPTS_BY_MODEL]})
        self._send({'error': 'no such endpoint'}, 404)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        model = req.get('model', '')
        if model not in SCRIPTS_BY_MODEL:
            return self._send({'error': f'model "{model}" not found'}, 404)
        with LOCK:
            calls = PROMPTS.setdefault(model, [])
            calls.append(req.get('prompt', ''))
            script = SCRIPTS_BY_MODEL[model]
            text = script[min(len(calls) - 1, len(script) - 1)]
        self._send({'response': text, 'done': True})


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


PORT = free_port()
srv = ThreadingHTTPServer(('127.0.0.1', PORT), FakeOllama)
threading.Thread(target=srv.serve_forever, daemon=True).start()

root = tempfile.mkdtemp(prefix='local-test-')
MEASURED = os.path.join(root, 'capture.json')
json.dump(CAPTURE, open(MEASURED, 'w'))
PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(f'{"PASS" if cond else "FAIL"}  {name}'
          f'{"  — " + str(detail)[:300] if detail and not cond else ""}')


def scaffold_library():
    d = tempfile.mkdtemp(dir=root)
    shutil.copy2(TEMPLATE, os.path.join(d, 'TEMPLATE.md'))
    with open(os.path.join(d, 'INDEX.md'), 'w', encoding='utf-8') as f:
        f.write('# Design library — index\n\nRead this before a capture.\n\n'
                '| Call it | Site | Captured | Path | Motion fidelity · signature '
                '| Notable |\n|---|---|---|---|---|---|\n\n'
                '## Cross-site patterns observed\n\n')
    return d


def run(model, *args, retries=3):
    out = tempfile.mkdtemp(dir=root)
    lib = scaffold_library()
    r = subprocess.run(
        [sys.executable, LOCAL, '--measured', MEASURED, '--domain', 'meridian.test',
         '--name', 'Meridian', '--model', model, '--ollama', f'http://127.0.0.1:{PORT}',
         '--retries', str(retries), '--library', lib, '--out', out, '--json', *args],
        capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except Exception:
        data = None
    return r.returncode, r.stdout + r.stderr, data, out, lib


# ---- a fabricating model costs retries
code, out, data, outdir, lib = run('retry-fab')
check('a fabricating first attempt is rejected and retried, then passes',
      code == 0 and data and data['pass'] and len(data['attempts']) == 2,
      out[-400:])
check('the first attempt failed on provenance, not structure',
      data and any('FABRICATED' in f or 'DROPPED' in f
                   for f in data['attempts'][0]['failures']),
      data and data['attempts'][0])
check('the gate findings were fed back into the retry prompt',
      'REJECTED' in PROMPTS['retry-fab'][1] and 'FABRICATED' in PROMPTS['retry-fab'][1],
      PROMPTS['retry-fab'][1][-400:])
check('the first prompt carried no feedback', 'REJECTED' not in PROMPTS['retry-fab'][0])
check('code fences around the model output are stripped',
      open(os.path.join(outdir, 'meridian.test.md'), encoding='utf-8')
      .read().startswith('# meridian.test'), )
check('the capture JSON itself is in the prompt',
      '#ff6041' in PROMPTS['retry-fab'][0], PROMPTS['retry-fab'][0][:200])

# ---- the clean path, and what --write changes
code, out, data, outdir, lib = run('first-good')
check('a clean first attempt passes in one', code == 0 and len(data['attempts']) == 1,
      out[-300:])
check('without --write the entry stays a draft',
      data and not data['installed']
      and os.path.exists(os.path.join(outdir, 'meridian.test.md')),
      data)
check('and the library is untouched',
      not os.path.exists(os.path.join(lib, 'meridian.test.md')))

code, out, data, outdir, lib = run('first-good', '--write')
check('--write installs the entry', os.path.exists(os.path.join(lib, 'meridian.test.md')),
      out[-300:])
idx = open(os.path.join(lib, 'INDEX.md'), encoding='utf-8').read()
check('--write appends the INDEX row', '[meridian.test](meridian.test.md)' in idx, idx)
check('the row is deterministic, not model-written',
      '**partial** · `cubic-bezier(.22,1,.36,1)` @ 300ms' in idx, idx)
check('the draft is removed after install',
      not os.path.exists(os.path.join(outdir, 'meridian.test.md')))
r = subprocess.run([sys.executable, LINT, lib], capture_output=True, text=True)
check('the installed library passes the real gate', r.returncode == 0,
      r.stdout[-300:])

# ---- exhaustion is a loud failure with the evidence kept
code, out, data, outdir, lib = run('always-bad', retries=2)
check('a model that never converges exits 1', code == 1, out[-200:])
check('after exactly the requested retries', data and len(data['attempts']) == 2,
      data and len(data.get('attempts', [])))
check('the last draft is kept for inspection',
      os.path.exists(os.path.join(outdir, 'meridian.test.md')))
check('nothing reached the library', not os.path.exists(os.path.join(lib, 'meridian.test.md')))

# ---- fidelity is decided by the capture, not the model
code, out, data, outdir, lib = run('wrong-fidelity')
check('an entry declaring a fidelity the capture does not support is rejected',
      code == 0 and len(data['attempts']) == 2, out[-300:])
check('and the rejection says the value was decided from the capture',
      any('decided from the capture' in f for f in data['attempts'][0]['failures']),
      data and data['attempts'][0])

# ---- a preamble is a rejection, not an installed artifact
code, out, data, outdir, lib = run('chatter')
check('model chatter before the entry is rejected and retried',
      code == 0 and len(data['attempts']) == 2, out[-300:])
check('and the rejection names the required first line',
      any('must BEGIN' in f for f in data['attempts'][0]['failures']),
      data and data['attempts'][0])

# ---- the CRITICAL from adversarial review: rollback must restore bytes,
# ---- never delete the entry it just overwrote
HAND_WRITTEN = """# meridian.test

**Callable as: Oldname** (aliases: oldname)

Hand-written. Captured 2026-08-01 @ 1440x900.

## Motion

**Motion fidelity: signature-only**

A precious hand-measured entry that must never be destroyed.
"""
# 'Meridianx' keeps the PRE-state lint-clean (no substring of any existing key)
# while the incoming entry's 'Meridian' is a substring of it — so the collision
# exists only in the post-install state the final belt inspects.
ZETA = HAND_WRITTEN.replace('# meridian.test', '# zeta.com').replace(
    'Oldname** (aliases: oldname)', 'Meridianx** (aliases: zx)')


def lib_with_conflict():
    """meridian.test exists hand-written; zeta.com already claims 'Meridian', so
    installing the model's Meridian entry must fail the final belt."""
    d = scaffold_library()
    for fn, text in (('meridian.test.md', HAND_WRITTEN), ('zeta.com.md', ZETA)):
        open(os.path.join(d, fn), 'w', encoding='utf-8').write(text)
    idx = os.path.join(d, 'INDEX.md')
    content = open(idx, encoding='utf-8').read()
    rows = ('| **Oldname** | [meridian.test](meridian.test.md) | 2026-08-01 | mirror | '
            '**signature-only** · x | y |\n'
            '| **Meridianx** | [zeta.com](zeta.com.md) | 2026-08-01 | mirror | '
            '**signature-only** · x | y |\n')
    open(idx, 'w', encoding='utf-8').write(content.replace('|---|---|---|---|---|---|\n',
                                                           '|---|---|---|---|---|---|\n' + rows))
    return d


lib = lib_with_conflict()
r0 = subprocess.run([sys.executable, LINT, lib], capture_output=True, text=True)
check('the conflict fixture is lint-clean BEFORE install — the collision is latent',
      r0.returncode == 0, r0.stdout[-300:])
before = {fn: open(os.path.join(lib, fn), encoding='utf-8').read()
          for fn in os.listdir(lib)}
out2 = tempfile.mkdtemp(dir=root)
r = subprocess.run(
    [sys.executable, LOCAL, '--measured', MEASURED, '--domain', 'meridian.test',
     '--name', 'Meridian', '--model', 'first-good', '--ollama', f'http://127.0.0.1:{PORT}',
     '--library', lib, '--out', out2, '--write', '--force'],
    capture_output=True, text=True)
after = {fn: open(os.path.join(lib, fn), encoding='utf-8').read()
         for fn in os.listdir(lib)}
check('a name collision at install time fails the run', r.returncode != 0, r.stdout + r.stderr)
check('the hand-written entry survives rollback byte-for-byte',
      after.get('meridian.test.md') == HAND_WRITTEN, after.get('meridian.test.md', '')[:120])
check('the whole library is restored byte-for-byte', before == after,
      [k for k in before if before[k] != after.get(k)])
r2 = subprocess.run([sys.executable, LINT, lib], capture_output=True, text=True)
check('the library is not wedged after rollback — its own gate still passes',
      r2.returncode == 0, r2.stdout[-300:])

# ---- --write over an existing domain refuses without --force
lib = lib_with_conflict()
r = subprocess.run(
    [sys.executable, LOCAL, '--measured', MEASURED, '--domain', 'meridian.test',
     '--name', 'Meridian', '--model', 'first-good', '--ollama', f'http://127.0.0.1:{PORT}',
     '--library', lib, '--out', tempfile.mkdtemp(dir=root), '--write'],
    capture_output=True, text=True)
check('an existing entry is refused without --force, exit 2', r.returncode == 2,
      (r.returncode, r.stderr[-200:]))
check('and the refusal names --force', '--force' in r.stderr, r.stderr[-200:])
check('the existing entry is untouched by the refusal',
      open(os.path.join(lib, 'meridian.test.md'), encoding='utf-8').read() == HAND_WRITTEN)

# ---- --force replaces the row, never stacks a second one
lib = scaffold_library()
open(os.path.join(lib, 'meridian.test.md'), 'w', encoding='utf-8').write(
    HAND_WRITTEN.replace('Oldname** (aliases: oldname)', 'Meridian** (aliases: meridian)'))
idx = os.path.join(lib, 'INDEX.md')
content = open(idx, encoding='utf-8').read()
open(idx, 'w', encoding='utf-8').write(content.replace(
    '|---|---|---|---|---|---|\n',
    '|---|---|---|---|---|---|\n| **Meridian** | [meridian.test](meridian.test.md) | '
    '2026-08-01 | mirror | **signature-only** · x | y |\n'))
r = subprocess.run(
    [sys.executable, LOCAL, '--measured', MEASURED, '--domain', 'meridian.test',
     '--name', 'Meridian', '--model', 'first-good', '--ollama', f'http://127.0.0.1:{PORT}',
     '--library', lib, '--out', tempfile.mkdtemp(dir=root), '--write', '--force'],
    capture_output=True, text=True)
idx_text = open(idx, encoding='utf-8').read()
check('--force replaces an existing entry cleanly', r.returncode == 0, r.stderr[-300:])
check('exactly one INDEX row for the domain after --force',
      idx_text.count('](meridian.test.md)') == 1, idx_text)
check('and it is the new row, not the old one', '**partial**' in idx_text
      and '**signature-only**' not in idx_text, idx_text)

# ---- a domain that is not a hostname never touches the filesystem
r = subprocess.run([sys.executable, LOCAL, '--measured', MEASURED,
                    '--domain', '../escape', '--retries', '1'],
                   capture_output=True, text=True)
check('a path-shaped --domain is refused at exit 2 before any generation',
      r.returncode == 2 and 'hostname' in r.stderr, (r.returncode, r.stderr[-200:]))

# ---- environment failures are exit 2, never confused with bad entries
code, out, data, outdir, lib = run('nope')
check('a model that is not pulled exits 2', code == 2, out[-200:])
check('and the message lists what IS pulled', 'retry-fab' in out, out[-300:])
r = subprocess.run([sys.executable, LOCAL, '--measured', MEASURED, '--domain', 'x.test',
                    '--ollama', 'http://127.0.0.1:9', '--retries', '1'],
                   capture_output=True, text=True, timeout=30)
check('an unreachable Ollama exits 2 with guidance',
      r.returncode == 2 and 'Is it running' in r.stderr, r.stderr[-200:])
r = subprocess.run([sys.executable, LOCAL, '--measured', 'nope.json', '--domain', 'x.test'],
                   capture_output=True, text=True)
check('an unreadable capture exits 2', r.returncode == 2, r.stderr[-200:])

srv.shutdown()
shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
if FAIL:
    print('FAILED:', ', '.join(FAIL))
    sys.exit(1)
