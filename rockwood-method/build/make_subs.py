#!/usr/bin/env python3
"""Génère le fichier ASS : sous-titres mot-à-mot + incrustations PNG animées."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import OVERLAYS, split_cues, DURATION  # noqa: E402

W, H = 1080, 1920
OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")

CREAM = "&H00FFF4E2"      # #fff4e2
GOLD = "&H006BC2F5"       # #f5c26b
OUTLINE = "&H0026120C"    # brun très sombre (bordure)

words = json.load(open(os.path.join(OUT, "..", "words.json"), encoding="utf-8"))
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
Style: Cap,Inter,84,{CREAM},{CREAM},{OUTLINE},&H96000000,1,0,0,0,100,100,0,0,1,6,5,2,60,60,215,1
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
    """[(texte, coller_avant)] — gère '-', '/', '.', '%' accolés au mot précédent."""
    out = []
    for i, w in enumerate(cue):
        txt = esc(w["text"])
        glue = False
        if i > 0:
            prev = cue[i - 1]["text"]
            if txt[:1] in ("-", "/", ".", ",", "%", "'") or prev.endswith("/"):
                glue = True
        out.append((txt, glue))
    return out


def cue_text(cue):
    """Sous-titres : chaque mot terne -> or (mot prononcé) -> crème."""
    t0 = cue[0]["start"]
    segs = []
    for (txt, glue), w in zip(tokens(cue), cue):
        a = max(0.0, (w["start"] - t0) * 1000)
        b = max(0.0, (w["end"] - t0) * 1000)
        segs.append((
            r"{\alpha&HA2&\1c" + CREAM + r"&\b1}"
            r"{\t(" + f"{a:.0f},{a + 90:.0f}" + r",\alpha&H00&,\1c" + GOLD + r"&)}"
            r"{\t(" + f"{b:.0f},{b + 170:.0f}" + r",\1c" + CREAM + r",\alpha&H32&)}"
            + txt + r"{\rCap}",
            glue,
        ))

    # coupes autorisées : uniquement entre deux tokens non collés
    n = len(segs)
    total = sum(len(t) + (0 if g else 1) for t, g in tokens(cue)) - 1
    n_lines = 1 if total <= 26 else (2 if total <= 56 else 3)
    n_lines = min(n_lines, n)

    if n_lines == 1:
        cuts = []
    else:
        target = n / n_lines
        cuts = []
        for k in range(1, n_lines):
            want = round(k * target)
            # cherche la frontière autorisée la plus proche de `want`
            best, best_d = None, 10 ** 6
            for j in range(1, n):
                if not segs[j][1]:           # segs[j][1] = coller_avant
                    d = abs(j - want)
                    if d < best_d and j not in cuts:
                        best, best_d = j, d
            if best is not None:
                cuts.append(best)
        cuts = sorted(set(cuts))

    lines, start = [], 0
    for c in cuts + [n]:
        chunk = segs[start:c]
        line = ""
        for k, (seg, glue) in enumerate(chunk):
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
        r"{\pos(540,1672)\an2}" + cue_text(cue)
    )

for asset, t0, t1, cx, cy, anim in OVERLAYS:
    png = os.path.join(ASSETS, asset + ".png").replace("\\", "/")
    if anim == "static":
        events.append(
            f"Dialogue: 1,{ts(t0)},{ts(t1)},Img,,0,0,0,,"
            rf"{{\pos({cx},{cy})\an5\1img({png})}}"
        )
        continue
    if anim == "rise":
        tags = (rf"\move({cx},{cy + 46},{cx},{cy},0,340)"
                r"\fad(220,180)"
                r"\fscx97\fscy97\t(0,340,\fscx100\fscy100)")
    elif anim == "pop":
        tags = (rf"\pos({cx},{cy})"
                r"\fad(150,170)"
                r"\fscx84\fscy84\t(0,240,\fscx100\fscy100)")
    else:  # zoom lent
        tags = (rf"\pos({cx},{cy})"
                r"\fad(260,420)"
                rf"\fscx100\fscy100\t(0,{int((t1 - t0) * 1000)},\fscx104\fscy104)")
    head = f"Dialogue: 1,{ts(t0)},{ts(t1)},Img,,0,0,0,,"
    events.append(head + "{" + tags + r"\an5\1img(" + png + ")}")

with open(os.path.join(OUT, "subs.ass"), "w", encoding="utf-8") as f:
    f.write(HEAD + "\n".join(events) + "\n")

print(f"subs.ass : {len(cues)} séquences, {len(OVERLAYS)} incrustations")
for cue in cues:
    glued = ""
    for txt, glue in tokens(cue):
        glued += ("" if (glued == "" or glue) else " ") + txt
    print(f"  {ts(cue[0]['start'])} → {ts(cue[-1]['end'])}  {glued}")
