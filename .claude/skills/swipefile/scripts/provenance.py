#!/usr/bin/env python3
"""
Provenance gate — every number in an entry traces to a capture, or the entry fails.

TEMPLATE.md's first rule is "Measured or absent. No value goes in that was not
read off the live page." Nothing enforced it, and the failure is exactly the
shape a language model produces: measured on this machine, qwen2.5:7b was handed
a capture JSON and returned a structurally perfect entry in 2.8 seconds that
invented a capture date (2023-11-15, present nowhere in the input) and dropped
every hex value and easing curve — and library-lint.py passed it, because that
gate protects the RESOLVER, not the truth. A library of plausible fiction is
worse than no library: the next build trusts it.

So this gate diffs the entry against the capture it was generated from, in both
directions:

  Fabrication (FAIL)  — a number, hex colour, cubic-bezier, or date asserted in
                        the entry that the capture never measured.
  Coverage    (FAIL)  — a hex or bezier the capture measured that the entry
                        dropped. The palette and the signature curve are the two
                        most reusable things in an entry; an entry without them
                        is notes wearing a template.

Numbers are matched by ROLE, not by bag: a token written as `500ms` must match
a time-role measurement, not the font weight 500 sitting in a family string —
adversarial review demonstrated that the weight ladder (400/500/600) collides
with invented durations in essentially every capture, and that list lengths
legitimised `3s` via any 3-item array. Unitless tokens stay loose, because a
bare `38` may honestly cite a use count. What stays OUT of scope, deliberately:
prose claims — numbers as words, named colours, easing keywords, font or
library names. Those are the reviewing agent's to judge; this gate checks the
four token classes and nothing else, and says so.

    python3 provenance.py entry.md capture.json
    python3 provenance.py entry.md capture.json --allow 2026-08-07 365daily.com
    python3 provenance.py entry.md capture.json --json

Exit 0 means every asserted value is measured and the measured essentials are
present. Exit 1 is a fabrication or a dropped essential. Exit 2 means the
inputs could not be read, which is not a clean entry.
"""
import argparse, json, re, sys

# Unitless integers below this are prose ("2 palettes", "3 breakpoints"), not
# measurements. Anything carrying a unit is checked regardless of size.
SMALL_INT = 5
TIME_UNITS = {'s': 1000.0, 'ms': 1.0}
LEN_UNITS = {'px'}
UNIT = re.compile(r'\s?(ms|px|vw|vh|rem|em|deg|%|s)(?![A-Za-z])')
NUMBER = re.compile(r'(?<![\w.#])-?(?:\d+\.?\d*|\.\d+)')
BEZIER = re.compile(r'cubic-bezier\(([^)]+)\)')
HEX = re.compile(r'#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGB = re.compile(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*[,)]')
ISO_DATE = re.compile(r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b')
MONTHS = ('january february march april may june july august september '
          'october november december').split()
MONTH_DATE = re.compile(r'\b(' + '|'.join(MONTHS) + r')\s+(\d{4})\b', re.I)
YEAR = re.compile(r'\b(?:19|20)\d{2}\b')
LIST_MARKER = re.compile(r'^\s{0,7}\d+\.\s', re.M)
THOUSANDS = re.compile(r'\b\d{1,3}(?:,\d{3})+\b')
# '1440x900' is two measurements joined by a dimension separator, not a word —
# without this split the lookbehind that keeps digits out of identifiers also
# keeps the 900 out of the measured set.
DIMENSION = re.compile(r'(?<=\d)[x×](?=\d)')
# ROLE assignment from JSON key names. A duration and a breakpoint are both
# "a number" only to a bag; to the page they are different physical claims.
ROLE_TIME = re.compile(r'_ms$|_s$|duration|stagger|delay|dwell|settle|time', re.I)
ROLE_LEN = re.compile(r'_px$|px|width|height|travel|step|gutter|container|rhythm|'
                      r'breakpoint|offset|radius|margin|padding', re.I)


def norm_hex(h):
    h = h.lower()
    return ''.join(c * 2 for c in h) if len(h) == 3 else h


def rgb_hex(r, g, b):
    if max(int(r), int(g), int(b)) > 255:
        return None
    return f'{int(r):02x}{int(g):02x}{int(b):02x}'


def parse_bezier(body):
    try:
        parts = [round(float(p), 4) for p in body.split(',')]
        return tuple(parts) if len(parts) == 4 else None
    except ValueError:
        return None


def role_of(key):
    if ROLE_TIME.search(key):
        return 'time'
    if ROLE_LEN.search(key):
        return 'len'
    return None


class Measured:
    """Everything the capture holds, harvested by role."""

    def __init__(self):
        self.nums = {'time': set(), 'len': set(), 'other': set()}
        self.counts, self.hexes, self.beziers, self.blobs = set(), set(), set(), []

    def all_nums(self):
        return self.nums['time'] | self.nums['len'] | self.nums['other']

    def add_string(self, s, role):
        self.blobs.append(s)
        for m in BEZIER.finditer(s):
            b = parse_bezier(m.group(1))
            if b:
                self.beziers.add(b)
                self.nums['other'].update(b)
        for m in HEX.finditer(s):
            self.hexes.add(norm_hex(m.group(1)))
        for m in RGB.finditer(s):
            h = rgb_hex(*m.groups())
            if h:
                self.hexes.add(h)
        s = DIMENSION.sub(' ', BEZIER.sub(' ', HEX.sub(' ', s)))
        for m in NUMBER.finditer(s):
            unit = UNIT.match(s[m.end():m.end() + 4])
            u = unit.group(1) if unit else None
            r = 'time' if u in TIME_UNITS else ('len' if u in LEN_UNITS else role)
            self.nums[r or 'other'].add(round(float(m.group(0)), 4))

    def walk(self, v, role=None):
        if isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            self.nums[role or 'other'].add(round(float(v), 4))
        elif isinstance(v, str):
            self.add_string(v, role)
        elif isinstance(v, list):
            self.counts.add(float(len(v)))
            # The canonical tally shape is [value, count]. The value carries the
            # key's role; the count is a count, never a duration or a length —
            # that distinction is what stops "38ms" passing via a use count.
            if (len(v) == 2 and isinstance(v[1], (int, float))
                    and not isinstance(v[1], bool) and role is not None):
                self.walk(v[0], role)
                self.walk(v[1], None)
            else:
                for item in v:
                    self.walk(item, role)
        elif isinstance(v, dict):
            for k, item in v.items():
                r = role_of(k) or role
                self.add_string(k, r)
                self.walk(item, r)


def harvest_entry(text):
    """What the entry asserts, each class removed before the next is read so a
    bezier's floats or a date's year are never re-flagged as bare numbers."""
    beziers = set()

    def sub_bezier(m):
        b = parse_bezier(m.group(1))
        if b:
            beziers.add(b)
            return ' '
        return m.group(1)          # a garbled curve still gets its numbers checked

    text = BEZIER.sub(sub_bezier, text)
    hexes = {norm_hex(m.group(1)) for m in HEX.finditer(text)}
    text = HEX.sub(' ', text)
    rgbs = [rgb_hex(*m.groups()) for m in RGB.finditer(text)]
    hexes |= {h for h in rgbs if h}
    text = RGB.sub(' ', text)

    dates = [(m.group(0), f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}')
             for m in ISO_DATE.finditer(text)]
    text = ISO_DATE.sub(' ', text)
    month_dates = [(m.group(0), f'{m.group(2)}-{MONTHS.index(m.group(1).lower()) + 1:02d}')
                   for m in MONTH_DATE.finditer(text)]
    text = MONTH_DATE.sub(' ', text)
    years = set(YEAR.findall(text))
    text = YEAR.sub(' ', text)
    text = LIST_MARKER.sub(' ', text)
    text = THOUSANDS.sub(lambda m: m.group(0).replace(',', ''), text)
    text = DIMENSION.sub(' ', text)

    numbers = []
    for m in NUMBER.finditer(text):
        raw = m.group(0)
        value = round(float(raw), 4)
        unit_m = UNIT.match(text[m.end():m.end() + 4])
        unit = unit_m.group(1) if unit_m else None
        if unit == 's' and '.' not in raw and abs(value) >= 60:
            continue               # "a <source> that 404s" is a verb, not a duration
        numbers.append((raw.strip(), value, unit))
    return numbers, hexes, beziers, dates, month_dates, years


def matches(value, unit, cand, decimals):
    variants = {value}
    if unit == 's':
        variants.add(round(value * 1000, 4))
    elif unit == 'ms':
        variants.add(round(value / 1000, 4))
    if unit == '%':
        variants.add(round(value / 100, 4))
    if variants & cand:
        return True
    # Precision rescue: "8.33vw" honestly cites a measured 8.3333 at fewer
    # digits. The measured value rounded to the token's own precision must agree.
    return any(round(n, decimals) in variants for n in cand)


def check(entry_text, capture, allow):
    j = Measured()
    j.walk(capture)
    for token in allow:
        j.add_string(token, None)      # --allow legitimises numbers and hexes too
    e_numbers, e_hexes, e_beziers, e_dates, e_months, e_years = harvest_entry(entry_text)
    blob = ' '.join(j.blobs)
    fails, warns, notes, fabricated = [], [], [], []

    loose = j.all_nums() | j.counts
    for raw, value, unit in e_numbers:
        if unit is None and value < SMALL_INT and value >= 0 and value == int(value):
            continue
        if unit in TIME_UNITS:
            cand = j.nums['time']
        elif unit in LEN_UNITS:
            cand = j.nums['len']
        elif unit is not None:
            cand = j.all_nums()
        else:
            cand = loose
        decimals = len(raw.split('.')[1]) if '.' in raw else 0
        if not matches(value, unit, cand, decimals):
            fabricated.append(f'{raw}{unit or ""}')

    fabricated += [f'#{h}' for h in sorted(e_hexes - j.hexes)]
    fabricated += ['cubic-bezier(' + ','.join(str(v) for v in b) + ')'
                   for b in sorted(e_beziers - j.beziers)]
    for raw, padded in e_dates:
        if raw not in blob and padded not in blob:
            fabricated.append(raw)
    for raw, year_month in e_months:
        if year_month not in blob:
            fabricated.append(raw)
    for y in sorted(e_years):
        if y not in blob and float(y) not in j.all_nums():
            fabricated.append(y)     # a bare 1920 may be a measured breakpoint

    if fabricated:
        fails.append(f'FABRICATED: {len(fabricated)} value(s) asserted that the capture '
                     f'never measured — {", ".join(fabricated[:10])}'
                     f'{" …" if len(fabricated) > 10 else ""}. Every one must be deleted '
                     f'or replaced with a value from the capture JSON.')

    missing_hex = sorted(j.hexes - e_hexes)
    if missing_hex:
        fails.append(f'DROPPED PALETTE: the capture measured {len(j.hexes)} colour(s) and '
                     f'the entry carries {len(e_hexes)} — missing '
                     f'{", ".join("#" + h for h in missing_hex)}.')
    missing_bez = sorted(j.beziers - e_beziers)
    if missing_bez:
        fails.append(f'DROPPED CURVES: {len(missing_bez)} measured easing curve(s) absent '
                     f'from the entry — the signature curve is the single most reusable '
                     f'thing in an entry: '
                     + ', '.join('cubic-bezier(' + ','.join(str(v) for v in b) + ')'
                                 for b in missing_bez))

    meaningful = {n for n in j.all_nums() if abs(n) >= SMALL_INT}
    said = set()
    for raw, v, u in e_numbers:
        said.add(v)
        if u in TIME_UNITS:
            said.add(round(v * TIME_UNITS[u], 4))
            if u == 'ms':
                said.add(round(v / 1000, 4))
    coverage = len(meaningful & said) / len(meaningful) if meaningful else 1.0
    notes.append(f'number coverage: {coverage:.0%} of {len(meaningful)} measured values '
                 f'appear in the entry')
    if coverage < 0.3:
        warns.append(f'THIN: only {coverage:.0%} of measured values made it into the '
                     f'entry. Not a failure — an entry summarises — but below this the '
                     f'entry is closer to prose than to measurements.')

    return fails, warns, notes, {'fabricated': fabricated,
                                 'missingHex': missing_hex,
                                 'missingBezier': [list(b) for b in missing_bez],
                                 'numberCoverage': round(coverage, 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('entry', help='the generated library entry (.md)')
    ap.add_argument('capture', help='the measured capture JSON it was generated from')
    ap.add_argument('--allow', nargs='*', default=[],
                    help='extra legitimate tokens — dates the caller stamped, the domain '
                         'itself if it contains digits. Numbers, hexes and dates in these '
                         'are all honoured.')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    try:
        entry_text = open(a.entry, encoding='utf-8').read()
        capture = json.load(open(a.capture, encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        print(f'cannot read inputs: {e}', file=sys.stderr)
        sys.exit(2)

    fails, warns, notes, detail = check(entry_text, capture, a.allow)
    ok = not fails
    if a.json:
        print(json.dumps({'pass': ok, 'entry': a.entry, 'capture': a.capture,
                          'failures': fails, 'warnings': warns, 'notes': notes,
                          **detail}, indent=1))
    else:
        print(f'{a.entry}  vs  {a.capture}')
        for x in notes:
            print(f'  note  {x}')
        for x in warns:
            print(f'  WARN  {x}')
        for x in fails:
            print(f'  FAIL  {x}')
        print('\nPROVENANCE GATE: ' + ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
