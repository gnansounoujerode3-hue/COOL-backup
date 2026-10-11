#!/usr/bin/env python3
"""Sous-titres v2 : mots-clés en serif italique or, reste en sans-serif crème.

Chaque mot non prononcé est atténué puis s'allume au moment exact où il est dit.
Les mots-clés de la marque restent en Instrument Serif italique (or).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan2 import KEYWORDS, DURATION, split_cues, ALPHA_DIM  # noqa: E402

W, H = 1080, 1920
OUT = os.path.dirname(os.path.abspath(__file__))
FONTS = "/home/user/work2/fonts"

CREAM = "&HECF7FD"     # #fdf7ec
GOLD = "&H7CBDE9"      # #e9bd7c
OUTLINE = "&H330A0D1A"  # espresso 80 %

words = json.load(open(os.path.join(os.path.dirname(OUT), "words.json"), encoding="utf-8"))
cues = split_cues(words)

HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter,78,{CREAM},{CREAM},{OUTLINE},&H00000000,0,0,0,0,100,100,0.4,0,1,4,3,2,72,72,215,1
Style: Img,,10,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    return f"{h:d}:{m:02d}:{t % 60:05.2f}"


def esc(s):
    return s.replace("{", "(").replace("}", ")")


def tokens(cue):
    """[(texte, coller_avant, est_mot_cle)]"""
    out = []
    for i, w in enumerate(cue):
        txt = esc(w["text"])
        glue = False
        if i > 0:
            prev = cue[i - 1]["text"]
            if txt[:1] in ("-", "/", ".", ",", "%", "'") or prev.endswith("/"):
                glue = True
        key = txt.strip(".,;:!?").lower()
        out.append((txt, glue, key in KEYWORDS))
    return out


def cue_text(cue):
    t0 = cue[0]["start"]
    segs = []
    for (txt, glue, is_kw), w in zip(tokens(cue), cue):
        a = max(0.0, (w["start"] - t0) * 1000)
        b = max(0.0, (w["end"] - t0) * 1000)
        if is_kw:
            base = rf"{{\alpha{ALPHA_DIM}\fnInstrument Serif\i1\fs86\1c{GOLD}&}}"
        else:
            base = rf"{{\alpha{ALPHA_DIM}\1c{CREAM}&}}"
        anim = rf"{{\t({a:.0f},{a + 110:.0f},\alpha&H00&)}}"
        segs.append((base + anim + txt + r"{\rCap}", glue, is_kw))

    n = len(segs)
    total = sum(len(t) + (0 if g else 1) for t, g, _ in tokens(cue)) - 1
    n_lines = 1 if total <= 26 else (2 if total <= 58 else 3)
    n_lines = min(n_lines, n)

    if n_lines == 1:
        cuts = []
    else:
        target = n / n_lines
        cuts = []
        for k in range(1, n_lines):
            want = round(k * target)
            best, bd = None, 10 ** 6
            for j in range(1, n):
                if not segs[j][1] and j not in cuts:
                    d = abs(j - want)
                    if d < bd:
                        best, bd = j, d
            if best is not None:
                cuts.append(best)
        cuts = sorted(set(cuts))

    lines, start = [], 0
    for c in cuts + [n]:
        line = ""
        for k, (seg, glue, _) in enumerate(segs[start:c]):
            line += ("" if (k and glue) else ("" if k == 0 else " ")) + seg
        lines.append(line)
        start = c
    return r"\N".join(lines)


events = []
for i, cue in enumerate(cues):
    nxt = cues[i + 1][0]["start"] if i + 1 < len(cues) else DURATION
    end = min(cue[-1]["end"] + 0.22, nxt - 0.03)
    if end <= cue[0]["start"] + 0.05:
        end = cue[-1]["end"]
    events.append(
        f"Dialogue: 0,{ts(cue[0]['start'])},{ts(end)},Cap,,0,0,0,,"
        r"{\pos(540,1668)\an2}" + cue_text(cue)
    )

with open(os.path.join(OUT, "subs2.ass"), "w", encoding="utf-8") as f:
    f.write(HEAD + "\n".join(events) + "\n")

print(f"subs2.ass : {len(cues)} séquences, mots-clés en serif or")
for cue in cues[:6]:
    print(f"  {ts(cue[0]['start'])} → {ts(cue[-1]['end'])}  "
          + " ".join(w["text"] for w in cue))
