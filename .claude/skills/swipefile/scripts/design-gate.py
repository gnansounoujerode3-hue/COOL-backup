#!/usr/bin/env python3
"""
The design gate — the taste pre-flight as an instrument instead of a checklist.

`design-taste-frontend`'s Section 14 is ~60 boxes an agent ticks about its own
work, in prose, with no measurement behind any of them. This folder has already
paid to learn what that produces. Step 2's motion spec was a written rule an
agent skipped three times in one session, patching each time the user noticed
something static, and it stopped being skipped only when `motion-spec.py` began
refusing to return a spec that did not exist. The lesson recorded there is the
reason this file exists: prose does not stop anything; holding the artifact does.

So the mechanical half of that pre-flight is measured here, on the served page,
by the same CDP instrument the rest of the skill measures with. The judgement
half — is the copy LLM-flavoured, is the motion motivated, does the whole thing
read as templated — is not mechanical and is not faked here; it goes to a
fresh-eyes critique pass that never watched the build being written. See
`references/taste.md`.

    python3 design-gate.py http://127.0.0.1:8791/
    python3 design-gate.py http://127.0.0.1:8791/ --src ../site --brief premium-consumer
    python3 design-gate.py http://127.0.0.1:8791/ --json --out design.json

Three rules it keeps, all inherited from the gates already in this folder:

  Unmeasured is not pass.  A check whose input never arrived is UNVERIFIED. It
                           is reported, never folded into a pass.
  Warnings do not block.   A heuristic that fires on a legitimate build teaches
                           an agent to ignore the gate. Only unambiguous,
                           measured violations FAIL.
  Match is exempt from     Match copy is captured verbatim from the reference;
  the copy checks.         rewriting it to satisfy a house style breaks the
                           Step 4 diff. Copy rules apply to work we author.

Exit 0 when nothing FAILs, 1 otherwise. `--strict` also blocks on UNVERIFIED.
"""
import argparse, collections, json, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(HERE, 'design-gate.js')
CDP = os.path.join(HERE, 'cdp-run.py')

DESKTOP_MIN = 1024
NAV_MAX_PX = 80
NAV_TOLERANCE_PX = 2
HERO_PAD_MAX_PX = 96
RADIUS_SCALE_MAX = 3
ACCENT_STRUCTURAL_USES = 3

# A page where most sections are one flat background-color, no gradient, no
# image, no canvas, is the single tell fresh-eyes critique keeps naming by
# hand: "every card/section is a flat fill with a hairline border." Some flat
# fills are legitimate — a pricing table, a plain footer — so this stays a
# ratio and a WARN, not a count and a FAIL.
FLAT_FILL_RATIO_WARN = 0.6

# Same story for section openings: a repeated eyebrow/heading/subhead/content
# stack reads fine twice or three times and as a template past that. Chosen
# well under the "eight times" a real critique named, so it still fires long
# before a page gets there.
SECTION_OPEN_REPEAT_WARN = 4

# Banned as *default* display serifs by the taste skill — the two the model
# reaches for unprompted. Justified use is a conversation, so this is a FAIL an
# agent can answer for, not a silent rewrite.
BANNED_DISPLAY_SERIFS = ('fraunces', 'instrument serif')

# Native OS faces: legitimately never go through @font-face, so `loaded` is
# meaningless for them and flagging their absence from document.fonts is a
# false positive on every page that uses them on purpose.
SYSTEM_FONTS = {
    '-apple-system', 'blinkmacsystemfont', 'segoe ui', 'system-ui', 'ui-sans-serif',
    'ui-serif', 'ui-monospace', 'ui-rounded', 'sans-serif', 'serif', 'monospace',
    'cursive', 'fantasy', 'arial', 'helvetica', 'helvetica neue', 'roboto',
    'times new roman', 'times', 'georgia', 'cambria', 'courier new', 'courier',
    'verdana', 'tahoma', 'trebuchet ms',
}

# The premium-consumer palette every AI build converges on. Gated on --brief so
# an artisan brand that genuinely names these colours is not fighting the tool.
BANNED_WARM_BG = {'#f5f1ea', '#f7f5f1', '#fbf8f1', '#efeae0', '#ece6db', '#faf7f1', '#e8dfcb'}
BANNED_WARM_ACCENT = {'#b08947', '#b6553a', '#9a2436', '#9c6e2a', '#bc7c3a', '#7d5621'}

# Rendered-text tells. Each one is a literal string the taste skill bans, so a
# regex hit is a fact about the page, not an opinion about it.
TEXT_TELLS = [
    (r'(?im)^\s*(?:↓\s*)?scroll(?:\s+(?:to\s+explore|down|for\s+more))?\s*$', 'scroll cue'),
    (r'(?m)^\s*\d{2,3}\s*[/·—–-]\s*[A-Za-z]', 'section-numbering eyebrow'),
    (r'(?im)^\s*(?:v\s?\d+\.\d+(?:\.\d+)?|build\s+\d{3,})\s*$', 'version footer'),
    (r'(?i)\bjane\s+doe\b|\bjohn\s+doe\b', 'placeholder person'),
    (r'(?i)\bacme\s+(?:inc|corp|co\b)', 'placeholder company'),
    (r'(?i)\blorem\s+ipsum\b', 'lorem ipsum'),
    (r'(?i)quietly\s+in\s+use\s+at', 'AI social-proof cliche'),
]

# Source-level rules. The rendered page cannot see these — a scroll listener and
# a `useScroll` hook produce the same pixels — so they are read from the code.
SRC_RULES = [
    (r'\bh-screen\b', 'FAIL', 'h-screen used — iOS Safari address bar makes it jump; use min-h-[100dvh]'),
    (r'addEventListener\(\s*[\'"]scroll[\'"]', 'FAIL',
     "window scroll listener — use useScroll() / ScrollTrigger / IntersectionObserver"),
    (r'from\s+[\'"]lucide-react[\'"]', 'WARN', 'lucide-react is discouraged; Phosphor / HugeIcons / Radix / Tabler'),
    (r'from\s+[\'"]framer-motion[\'"]', 'WARN', "legacy alias — import from 'motion/react'"),
]
SRC_EXTS = ('.tsx', '.jsx', '.ts', '.js', '.mjs', '.vue', '.svelte', '.astro', '.html', '.css')
SRC_SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', 'out', '__pycache__', 'cdn', '_raw'}

# CTA intents. Two labels in the same set on one page is the duplicate-intent
# failure; it stays a warning because a nav "Log in" beside a hero "Get started"
# is a real pattern and the grouping is a judgement call.
CTA_INTENTS = {
    'contact': ('get in touch', 'contact us', "let's talk", 'lets talk', 'start a project',
                'start something', 'reach out', 'book a call', 'talk to us'),
    'signup': ('try free', 'get started', 'sign up free', 'start free', 'try it free',
               'create account', 'start for free'),
    'portfolio': ('view work', 'see selected work', 'browse projects', 'view projects',
                  'selected work', 'our work'),
}


def run_probe(url, width, height, chrome, settle, timeout):
    cmd = [sys.executable, CDP, url, PROBE, '--width', str(width),
           '--height', str(height), '--settle', str(settle)]
    if chrome:
        cmd += ['--chrome', chrome]
    # PYTHONUTF8 for the child, errors='replace' for us. Without both, a single
    # curly quote in the page's copy makes the probe's stdout undecodable under
    # Windows' cp1252 console default and the run dies looking like a probe bug.
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=timeout, env=env)
    if p.returncode != 0:
        raise SystemExit(f'probe failed at {width}px:\n{(p.stderr or "").strip()[-2000:]}')
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f'probe returned no JSON at {width}px:\n{(p.stdout or "")[:600]}')


def scan_source(root):
    """Source-level rules, per file, with line numbers. Absent root -> None."""
    if not root or not os.path.isdir(root):
        return None
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SRC_SKIP_DIRS and not d.startswith('.')]
        for fn in filenames:
            if not fn.endswith(SRC_EXTS):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                for pattern, tier, message in SRC_RULES:
                    if re.search(pattern, line):
                        hits.append({'file': os.path.relpath(path, root), 'line': i,
                                     'tier': tier, 'message': message})
    return hits


class Checks:
    """pass / FAIL / WARN / UNVERIFIED, kept apart on purpose.

    UNVERIFIED is never folded into pass — report.py already refuses that trade
    and this gate feeds it. WARN exists so the FAIL list stays trustworthy: a
    gate that fires on a legitimate build is a gate an agent learns to skip,
    which is the failure mode this whole file was written against.
    """

    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail='', tier='FAIL', note=''):
        # `detail` describes the violation, so it is only true when there is
        # one. Attaching it to a pass produced rows reading `ok — no
        # prefers-reduced-motion rule anywhere`, which is a gate contradicting
        # itself in the one place an agent is skimming for the word `ok`.
        status = 'pass' if ok else tier
        self.rows.append({'check': name, 'status': status,
                          'detail': str(note if ok else detail)})

    def unverified(self, name, why):
        self.rows.append({'check': name, 'status': 'UNVERIFIED', 'detail': why})

    def by(self, status):
        return [r for r in self.rows if r['status'] == status]


def evaluate(shots, src_hits, mode, brief, strict_hero_visual):
    """shots: {width: probe_json}. Desktop-only rules read the widest >= 1024."""
    c = Checks()
    desktop_w = max([w for w in shots if w >= DESKTOP_MIN] or [max(shots)])
    d = shots[desktop_w]
    authored = mode != 'match'

    # ---- copy, only for work we author -------------------------------------
    if authored:
        em = d['text']['emDashes']
        c.add('zero em-dashes in rendered text', em == 0,
              f"{em} found: {'; '.join(d['text']['emDashSamples'][:3])}" if em else '')
        tells = []
        for pattern, label in TEXT_TELLS:
            for m in re.findall(pattern, d['text']['body'])[:3]:
                tells.append(f'{label}: {(m if isinstance(m, str) else m[0]).strip()[:60]}')
        c.add('no banned filler strings in copy', not tells, '; '.join(tells[:6]))
    else:
        c.rows.append({'check': 'zero em-dashes in rendered text', 'status': 'pass',
                       'detail': 'n/a — Match copy is captured verbatim'})
        c.rows.append({'check': 'no banned filler strings in copy', 'status': 'pass',
                       'detail': 'n/a — Match copy is captured verbatim'})

    # ---- structure ---------------------------------------------------------
    sections = d['sections']
    n_sections = len(sections)
    if n_sections == 0:
        c.unverified('eyebrow budget', 'no content sections resolved — check the served URL')
    else:
        budget = math.ceil(n_sections / 3)
        got = d['eyebrows']['count']
        c.add(f'eyebrow count <= ceil(sections/3) = {budget}', got <= budget,
              f"{got} eyebrows over {n_sections} sections: "
              + '; '.join(e['text'][:24] for e in d['eyebrows']['samples'][:5]),
              note=f'{got} over {n_sections} sections')

    # Flat-fill census: bgImage already catches gradients (CSS puts them on
    # background-image, same property as a url()) and any image sitting
    # behind the section; media catches an img/video/canvas/svg painted
    # inside it. Neither true is a flat solid fill.
    if n_sections == 0:
        c.unverified('flat-fill census: sections vary their background treatment',
                     'no content sections resolved — check the served URL')
    else:
        flat = [s for s in sections if not s['bgImage'] and s['media'] == 0]
        flat_ratio = len(flat) / n_sections
        c.add(f'flat-fill census: <= {int(FLAT_FILL_RATIO_WARN * 100)}% of sections are flat solid colour',
              flat_ratio <= FLAT_FILL_RATIO_WARN,
              f'{len(flat)}/{n_sections} sections ({round(flat_ratio * 100)}%) are a single flat '
              'solid colour with no gradient, image, or canvas behind them — not automatically '
              'wrong, but the single biggest tell of a templated page',
              tier='WARN')

    # Section-opening monotony: a heuristic tag/size/weight/case fingerprint
    # of each section's first few children (design-gate.js openShape), the
    # same signal the eyebrow census above reads, taken per section instead
    # of per page. A shared fingerprint does not prove a copy-paste section —
    # this counts, it does not verdict, the same way the theme-lock crossings
    # below count crossings and leave the call to whoever reads the report.
    opens = [tuple(s['openShape']) for s in sections
             if s.get('openShape') and len(s['openShape']) >= 2]
    if not opens:
        c.unverified('section-opening monotony (heuristic)',
                     'no section-opening fingerprints resolved')
    else:
        counts = collections.Counter(opens)
        top_shape, top_count = counts.most_common(1)[0]
        run_len = longest_run = 1
        for a, b in zip(opens, opens[1:]):
            run_len = run_len + 1 if a == b else 1
            longest_run = max(longest_run, run_len)
        worst_repeat = max(top_count, longest_run)
        c.add(f'section-opening monotony (heuristic): no opening shape repeats '
              f'{SECTION_OPEN_REPEAT_WARN}+ times',
              worst_repeat < SECTION_OPEN_REPEAT_WARN,
              f'{top_count}/{len(opens)} sections open with the same structure '
              f'({" > ".join(top_shape)}), longest consecutive run {longest_run} — a heuristic '
              "fingerprint of each section's first children, not a verdict; read it and judge "
              'whether the repeat is a deliberate rhythm or the templated '
              'eyebrow/heading/subhead/content stack',
              tier='WARN')

    run, worst = 0, 0
    for s in sections:
        run = run + 1 if s['splitImageText'] else 0
        worst = max(worst, run)
    c.add('no 3 consecutive image+text split sections', worst < 3,
          f'{worst} in a row')

    # Theme lock: one deliberate switch is allowed, oscillation is not. Sections
    # sitting on a photograph are skipped — their luminance is the div's, not
    # the image's, and a false FAIL here is exactly the crying-wolf case.
    lums = [s['bgLuminance'] for s in sections if not s['bgImage']]
    crossings = 0
    if lums:
        side = [l > 0.5 for l in lums]
        crossings = sum(1 for a, b in zip(side, side[1:]) if a != b)
    if not lums:
        c.unverified('page theme lock', 'every section sits on a background image')
    else:
        # Zero crossings is a locked theme. One is the "colour block story" the
        # rule allows once per page — worth surfacing, not worth blocking.
        # Two or more is a page that reads as three different websites.
        c.add('page theme lock: no oscillating light/dark sections', crossings == 0,
              f'{crossings} light/dark crossings across {len(lums)} sections',
              tier='FAIL' if crossings > 1 else 'WARN')

    # ---- navigation (desktop) ----------------------------------------------
    nav = d.get('nav')
    if not nav:
        c.unverified('navigation fits one line, <= 80px', 'no header/nav element found')
    else:
        # Tolerance, because the cap is a design rule and 80.2px is not a
        # two-line nav. Sub-pixel layout rounding and a 1px bottom hairline both
        # land here, and failing a build over 0.2px is how a gate loses its
        # reader.
        c.add(f'navigation height <= {NAV_MAX_PX}px at {desktop_w}px',
              nav['height'] <= NAV_MAX_PX + NAV_TOLERANCE_PX,
              f"{nav['height']}px", note=f"{nav['height']}px")
        c.add(f'navigation renders on one line at {desktop_w}px', nav['rows'] <= 1,
              f"{nav['rows']} rows, {nav['items']} items")

    # ---- hero --------------------------------------------------------------
    hero = d.get('hero')
    if not hero:
        c.unverified('hero discipline', 'no hero section resolved')
    else:
        c.add(f'hero top padding <= {HERO_PAD_MAX_PX}px at {desktop_w}px',
              hero['paddingTop'] <= HERO_PAD_MAX_PX, f"{hero['paddingTop']}px")
        if hero['firstCtaTop'] is None:
            c.unverified('hero CTA visible without scrolling', 'no CTA found in the hero')
        else:
            c.add('hero CTA visible without scrolling',
                  hero['firstCtaTop'] < hero['viewportHeight'],
                  f"first CTA at {hero['firstCtaTop']}px, viewport {hero['viewportHeight']}px")
        if hero['headlineLines'] is None:
            c.unverified('hero headline <= 2 lines', 'no hero headline resolved')
        else:
            c.add('hero headline <= 2 lines at desktop', hero['headlineLines'] <= 2,
                  f"{hero['headlineLines']} lines: {(hero['headline'] or '')[:60]}")
        real = hero['realMedia'] + hero['backgroundPhotos']
        c.add('hero carries a real visual (not a gradient blob)', real > 0,
              'no img/video/canvas/photo in the hero'
              + (' — gradient only' if hero['gradientOnly'] else ''),
              tier='FAIL' if strict_hero_visual else 'WARN')
        # The rule's real content: nothing below the CTAs. A raw text-leaf count
        # cannot separate a fifth deliberate element from a wrapper span, but
        # "text below the last CTA, inside the hero" is exactly the tagline /
        # trust-strip / pricing-teaser the rule bans, and it is measurable.
        if hero.get('lastCtaBottom') is None:
            c.unverified('nothing below the hero CTAs', 'no hero CTA to measure against')
        else:
            below = hero['textBelowCtas']
            c.add('nothing below the hero CTAs (tagline / trust strip / teaser)',
                  below == 0,
                  f"{below} text element(s) below the CTAs: "
                  + '; '.join(hero['textBelowCtaSamples'][:3]), tier='WARN')

    # ---- contrast, every viewport -----------------------------------------
    bad_cta, scrim_cta, wrapped = [], [], []
    for w, shot in sorted(shots.items()):
        for b in shot['buttons']:
            if b['overImage']:
                scrim_cta.append(f"{w}px {b['label'][:28]}")
            elif b['contrast'] < b['required']:
                bad_cta.append(f"{w}px \"{b['label'][:28]}\" {b['contrast']}:1 "
                               f"({b['fg']} on {b['bg']}, needs {b['required']})")
    for b in d['buttons']:
        if b['lines'] >= 2 and b['words'] >= 2:
            wrapped.append(f"\"{b['label'][:32]}\" wraps to {b['lines']} lines")
    if not any(shot['buttons'] for shot in shots.values()):
        c.unverified('every CTA clears WCAG AA', 'no buttons found on the page')
    else:
        c.add('every CTA clears WCAG AA', not bad_cta, '; '.join(bad_cta[:5]))
    c.add('no CTA label wraps at desktop', not wrapped, '; '.join(wrapped[:4]))
    if scrim_cta:
        c.add('CTAs over imagery carry a measurable background', False,
              f'{len(scrim_cta)} CTA(s) sit on an image — contrast not computable, '
              f'verify a scrim or stroke: ' + '; '.join(scrim_cta[:3]), tier='WARN')

    bad_form, ph_form, ph_label = [], [], []
    for w, shot in sorted(shots.items()):
        for f in shot['forms']:
            if not f['overImage'] and f['contrast'] < 4.5:
                bad_form.append(f"{w}px {f['name']} {f['contrast']}:1 ({f['fg']} on {f['bg']})")
            if f['placeholderContrast'] is not None and f['placeholderContrast'] < 4.5:
                ph_form.append(f"{w}px {f['name']} placeholder {f['placeholderContrast']}:1")
            if f['placeholderOnlyLabel']:
                ph_label.append(f"{w}px {f['name']}")
    if not any(shot['forms'] for shot in shots.values()):
        c.rows.append({'check': 'every form control clears WCAG AA', 'status': 'pass',
                       'detail': 'n/a — no form controls on the page'})
    else:
        c.add('every form control clears WCAG AA', not bad_form, '; '.join(bad_form[:5]))
        c.add('no placeholder-as-label', not ph_label, '; '.join(sorted(set(ph_label))[:5]))
        if ph_form:
            c.add('placeholder text clears WCAG AA', False,
                  '; '.join(sorted(set(ph_form))[:4]), tier='WARN')

    # ---- consistency locks -------------------------------------------------
    accents = [a for a in d['census']['accents'] if a['uses'] >= ACCENT_STRUCTURAL_USES]
    c.add('one accent colour family', len(accents) <= 1,
          '; '.join(f"hue {a['hue']}deg x{a['uses']} ("
                    + ','.join(s['hex'] for s in a['samples'][:2]) + ')' for a in accents[:4]))

    radii = [r for r in d['census']['radii'] if r['uses'] >= 2]
    radius_census = '; '.join(f"{r['radius']}x{r['uses']}" for r in radii[:8])
    c.add(f'one radius scale (<= {RADIUS_SCALE_MAX} distinct values)',
          len(radii) <= RADIUS_SCALE_MAX, radius_census, note=radius_census)

    painted = [f for f in d['census']['families'] if f['loaded'] and f['uses'] >= 2]
    banned = [f["family"] for f in painted
              if any(b in f['family'].lower() for b in BANNED_DISPLAY_SERIFS)]
    c.add('no banned default display serif', not banned, ', '.join(banned))

    # The opposite failure `painted` was never checked for: a font *declared*
    # with real weight on the page (uses >= 2) that is not a native OS face and
    # never actually loaded. That page is not shipping the wrong font — it is
    # shipping no font at all, silently, on top of a passing report. A 404'd
    # @font-face or a family named in Tailwind config with no font file behind
    # it both land here identically: declared, unloaded, invisible to a
    # screenshot at a glance because the fallback still renders text.
    declared = [f for f in d['census']['families']
                if f['uses'] >= 2 and f['family'].lower() not in SYSTEM_FONTS]
    unloaded = sorted({f['family'] for f in declared if not f['loaded']})
    c.add('every declared font actually renders (no silent system fallback)',
          not unloaded, '; '.join(unloaded))

    warm_bg = {s['bgHex'].lower() for s in sections} & BANNED_WARM_BG
    warm_accent = {a['hex'].lower() for x in d['census']['accents'] for a in x['samples']} \
        & BANNED_WARM_ACCENT
    warm = sorted(warm_bg | warm_accent)
    c.add('not the default premium-consumer beige+brass palette', not warm,
          ', '.join(warm), tier='FAIL' if brief == 'premium-consumer' else 'WARN')

    # ---- motion ------------------------------------------------------------
    m = d['motion']
    animated = m['infiniteAnimations'] > 0 or d['media']['canvases'] > 0
    if m['reducedMotionRules'] == 0 and m['stylesheetsUnreadable'] > 0:
        c.unverified('prefers-reduced-motion present',
                     f"{m['stylesheetsUnreadable']} stylesheet(s) unreadable from the page "
                     '(cross-origin) — serve them same-origin or grep the source')
    else:
        c.add('prefers-reduced-motion present', m['reducedMotionRules'] > 0,
              'no prefers-reduced-motion rule anywhere in the page CSS'
              + ('' if animated else ' (and nothing measured as animating)'),
              tier='FAIL' if authored else 'WARN')
    c.add('at most one marquee per page', m['marquees'] <= 1,
          f"{m['marquees']} infinite horizontal-scroll elements")

    # ---- CTA intent --------------------------------------------------------
    labels = {b['label'].strip().lower() for b in d['buttons']}
    dupes = []
    for intent, phrases in CTA_INTENTS.items():
        hit = sorted({p for p in phrases if any(p == l or p in l for l in labels)})
        if len(hit) > 1:
            dupes.append(f'{intent}: ' + ', '.join(f'"{h}"' for h in hit))
    c.add('no duplicate CTA intent', not dupes, '; '.join(dupes), tier='WARN')

    # ---- source ------------------------------------------------------------
    if src_hits is None:
        c.unverified('source rules (h-screen, scroll listeners, icon family)',
                     'no --src supplied — pass the project source directory')
    else:
        fails = [h for h in src_hits if h['tier'] == 'FAIL']
        warns = [h for h in src_hits if h['tier'] == 'WARN']
        c.add('no h-screen and no window scroll listeners', not fails,
              '; '.join(f"{h['file']}:{h['line']} {h['message']}" for h in fails[:5]))
        if warns:
            c.add('icon/animation imports follow the house list', False,
                  '; '.join(f"{h['file']}:{h['line']} {h['message']}" for h in warns[:5]),
                  tier='WARN')
    return c


def render(c, shots, mode):
    fails, warns, unver = c.by('FAIL'), c.by('WARN'), c.by('UNVERIFIED')
    lines = [f"design gate — {list(shots.values())[0]['url']}",
             f"mode {mode} · viewports {', '.join(str(w) for w in sorted(shots))}", '']
    for r in c.rows:
        mark = {'pass': 'ok  ', 'FAIL': 'FAIL', 'WARN': 'warn', 'UNVERIFIED': '????'}[r['status']]
        lines.append(f"  {mark}  {r['check']}" + (f"  — {r['detail']}" if r['detail'] else ''))
    lines.append('')
    if fails:
        lines.append(f'DESIGN GATE: NOT DONE — {len(fails)} check(s) failing'
                     + (f', {len(unver)} unverified' if unver else '')
                     + (f', {len(warns)} warning(s)' if warns else '') + '.')
    elif unver:
        lines.append(f'DESIGN GATE: PASS on {len(c.rows) - len(unver)} checks — '
                     f'{len(unver)} UNVERIFIED. Reported, not passed.')
    else:
        lines.append('DESIGN GATE: PASS — every mechanical check measured and cleared.')
    if warns:
        lines.append(f'{len(warns)} warning(s) do not block. They are the checks whose '
                     'measurement is a heuristic — read them, decide, say what you decided.')
    lines.append('The judgement half of the pre-flight is NOT in this number. Run the '
                 'fresh-eyes critique pass before calling the page done (references/taste.md).')
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('url', help='the SERVED build — not a file:// path, not the reference')
    ap.add_argument('--width', type=int, action='append', default=None,
                    help='viewport width; repeatable. Default: 1440 and 390')
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--mode', default='adapt', choices=['adapt', 'match'],
                    help='match exempts the copy checks — captured copy is verbatim by design')
    ap.add_argument('--brief', default='', help='e.g. premium-consumer — promotes the '
                                                'palette warning to a failure')
    ap.add_argument('--src', default=None, help='project source dir for the code-level rules')
    ap.add_argument('--strict-hero-visual', action='store_true',
                    help='a hero with no real image FAILs instead of warning')
    ap.add_argument('--settle', type=float, default=2.5)
    ap.add_argument('--timeout', type=float, default=180)
    ap.add_argument('--chrome', default=None)
    ap.add_argument('--strict', action='store_true', help='UNVERIFIED blocks too')
    ap.add_argument('--json', dest='as_json', action='store_true')
    ap.add_argument('--out', default=None, help='write the JSON result here as well')
    a = ap.parse_args()

    # The report names measured colours, curly quotes and section labels back to
    # the user; Windows' cp1252 console default turns those into mojibake and
    # then into a UnicodeEncodeError on the ones it cannot map at all.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')

    widths = a.width or [1440, 390]
    shots = {}
    for w in widths:
        h = a.height if w >= DESKTOP_MIN else 844
        shots[w] = run_probe(a.url, w, h, a.chrome, a.settle, a.timeout)

    c = evaluate(shots, scan_source(a.src), a.mode, a.brief, a.strict_hero_visual)
    fails, warns, unver = c.by('FAIL'), c.by('WARN'), c.by('UNVERIFIED')
    blocking = fails + (unver if a.strict else [])

    result = {
        'pass': not blocking,
        'mode': a.mode,
        'url': shots[max(shots)]['url'],
        'viewports': sorted(shots),
        # report.py reads these three keys off --design, the same shape
        # motion-diff.py and copy-gate.py already emit.
        'failures': [f"{r['check']}: {r['detail']}" if r['detail'] else r['check'] for r in fails],
        'warnings': [f"{r['check']}: {r['detail']}" if r['detail'] else r['check'] for r in warns],
        'unverified': [r['check'] for r in unver],
        'checks': c.rows,
        'coverage': {'sections': len(shots[max(shots)]['sections']),
                     'buttons': len(shots[max(shots)]['buttons']),
                     'forms': len(shots[max(shots)]['forms']),
                     'measured': len(c.rows)},
    }
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=1)
    if a.as_json:
        print(json.dumps(result, indent=1))
    else:
        sys.stdout.write(render(c, shots, a.mode))
        if a.out:
            print(f'wrote {a.out}')
    sys.exit(1 if blocking else 0)


if __name__ == '__main__':
    main()
