#!/usr/bin/env python3
"""Sous-titres cinétiques rendus en Python.

Style : mots en Inter SemiBold ; mots-clés de la marque en Instrument Serif italique or.
Chaque mot apparaît à l'instant exact où il est prononcé (fondu 90 ms + léger
agrandissement), reste en or pendant sa durée, puis se pose en crème.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan3 import (CREAM, GOLD, GOLD_DEEP, KEYWORDS, CAP_Y, W,  # noqa: E402
                   split_cues, glue_before)

A_ROOT = os.environ.get("ROCKWOOD_WORK", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NM = os.environ.get("ROCKWOOD_FONTS", os.path.join(A_ROOT, "node_modules")) + "/@expo-google-fonts"
FILES = {
    "word": f"{NM}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "key": f"{NM}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
}
SIZES = {"word": 62, "key": 74}
LINE_H = 84
SPACE = 20
ALPHA_STEPS = 24
_cache = {}


def _font(kind):
    return ImageFont.truetype(FILES[kind], SIZES[kind])


def word_image(text, kind, fill, alpha):
    """Image RGBA (texte + ombre douce) du mot, alpha arrondi pour le cache."""
    a = max(0, min(255, int(round(alpha / ALPHA_STEPS) * ALPHA_STEPS)))
    key = (text, kind, fill, a)
    if key in _cache:
        return _cache[key]

    f = _font(kind)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    tw = int(probe.textlength(text, font=f))
    asc, desc = f.getmetrics()
    pad = 30
    im = Image.new("RGBA", (tw + 8 + 2 * pad, asc + desc + 8 + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x, y = pad + 3, pad + 3
    d.text((x, y + 4), text, font=f, fill=(10, 5, 4, 150))
    d.text((x, y + 2), text, font=f, fill=(10, 5, 4, 110))
    d.text((x, y), text, font=f, fill=tuple(fill[:3]) + (255,))
    if a < 255:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a / 255)))

    info = {"img": im, "pad": pad, "tw": tw + 8, "text_x": pad + 3, "asc": asc}
    _cache[key] = info
    return info


def build(words):
    cues = []
    for cue in split_cues(words):
        toks = []
        for k, w in enumerate(cue):
            txt = w["text"].replace("{", "(").replace("}", ")")
            toks.append({
                "text": txt,
                "kw": txt.strip(".,;:!?").lower() in KEYWORDS,
                "glue": glue_before(cue, k),
                "start": w["start"],
                "end": w["end"],
            })

        # fusion des mots collés ('100' + '%' -> '100%', 'self' + '-guided' -> 'self-guided')
        merged = []
        for t in toks:
            if merged and t["glue"]:
                m = merged[-1]
                m["text"] += t["text"]
                m["end"] = t["end"]
                m["kw"] = m["text"].strip(".,;:!?").lower() in KEYWORDS or m["kw"]
            else:
                merged.append(dict(t))
        for k, m in enumerate(merged):
            m["glue"] = (k > 0 and m["text"][:1] in ("-", "/", ".", "%"))
        toks = merged

        probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        for t in toks:
            kind = "key" if t["kw"] else "word"
            t["w"] = int(probe.textlength(t["text"], font=_font(kind))) + 8

        total = sum(t["w"] for t in toks) + SPACE * (len(toks) - 1)
        n_lines = 1 if total <= 780 else 2
        n_lines = min(n_lines, len(toks))

        cuts = []
        if n_lines > 1:
            target = len(toks) / n_lines
            for k in range(1, n_lines):
                want = round(k * target)
                best, bd = None, 10 ** 6
                for j in range(1, len(toks)):
                    if not toks[j]["glue"] and j not in cuts:
                        dd = abs(j - want)
                        if dd < bd:
                            best, bd = j, dd
                if best is not None:
                    cuts.append(best)
            cuts = sorted(set(cuts))

        lines, start = [], 0
        for c in cuts + [len(toks)]:
            items, x = [], 0
            for i, t in enumerate(toks[start:c]):
                if not (i == 0 or t["glue"]):
                    x += SPACE
                items.append({"tok": t, "x": x})
                x += t["w"]
            lines.append({"items": items, "w": x})
            start = c

        cues.append({"t0": cue[0]["start"], "t1": cue[-1]["end"] + 0.22, "lines": lines})

    cues.sort(key=lambda c: c["t0"])
    return cues


def active_index(cues, t):
    for i, c in enumerate(cues):
        if c["t0"] <= t <= c["t1"]:
            return i
    return None


def draw(base, cues, t, idx):
    cue = cues[idx]
    n = len(cue["lines"])
    for li, line in enumerate(cue["lines"]):
        baseline = CAP_Y - (n - 1 - li) * LINE_H
        x0 = int((W - line["w"]) / 2)
        for it in line["items"]:
            tk = it["tok"]
            if t < tk["start"]:
                continue
            kind = "key" if tk["kw"] else "word"

            ramp = min(1.0, (t - tk["start"]) / 0.09)
            alpha = 96 + 159 * ramp
            gold = tk["kw"] or t <= tk["end"] + 0.16
            fill = GOLD if gold else CREAM

            info = word_image(tk["text"], kind, fill, alpha)
            img = info["img"]
            pop = 0.0
            if t <= tk["start"] + 0.26:
                pop = 0.055 * (1 - (t - tk["start"]) / 0.26)

            s = 1.0 + pop
            if s > 1.001:
                scaled = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
            else:
                scaled = img

            left = x0 + it["x"] - info["text_x"] * s - (scaled.width - img.width) / 2
            top = baseline - info["asc"] * s - (scaled.height - img.height) / 2
            base.alpha_composite(scaled, (int(left), int(top)))
