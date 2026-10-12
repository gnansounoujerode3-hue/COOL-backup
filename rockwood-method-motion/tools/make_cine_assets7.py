#!/usr/bin/env python3
"""Habillage v7 : blocs typographiques **découpés en parties animables**.

La v5/v6 livraient chaque bloc (kicker + titre + filet + sous-titre + index) en
un seul PNG : tout arrivait d'un coup, ce qu'un motion designer appelle une
entrée « robotique ». La v7 découpe chaque bloc en parties, toutes dessinées sur
le **même canevas** (donc posées au même endroit par le compositeur) :

  cut{i}_a.png  carré d'accent + kicker
  cut{i}_b.png  titre serif (les deux lignes)
  cut{i}_c.png  filet dégradé
  cut{i}_d.png  sous-titre + index

  endtype_a.png … endtype_d.png  même découpage pour la carte finale

`cut{i}.png` et `endtype.png` (bloc complet, ombre douce incluse) restent
produits : ils servent à caler la plaque de lisibilité.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan4 import (CREAM, GOLD, TERRA, SLATE,  # noqa: E402
                   CUTAWAYS, GOLD_DEEP, X_L, X_R)

OUT = os.path.dirname(os.path.abspath(__file__))
A = os.environ.get("ROCKWOOD_ASSETS",
                   os.path.join(os.path.dirname(OUT), "assets"))
os.makedirs(A, exist_ok=True)

A_ROOT = os.environ.get("ROCKWOOD_WORK",
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NM = os.environ.get("ROCKWOOD_FONTS", os.path.join(A_ROOT, "node_modules")) + "/@expo-google-fonts"
F = {
    "sg400": f"{NM}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
    "sg500": f"{NM}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
    "sg700": f"{NM}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "in300": f"{NM}/inter/300Light/Inter_300Light.ttf",
    "in400": f"{NM}/inter/400Regular/Inter_400Regular.ttf",
    "in500": f"{NM}/inter/500Medium/Inter_500Medium.ttf",
    "isr": f"{NM}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
}


def font(k, s):
    return ImageFont.truetype(F[k], s)


def tw(d, s, f, tr=0):
    return sum(d.textlength(c, font=f) for c in s) + tr * max(0, len(s) - 1)


def track(d, xy, s, f, fill, tr=0, anchor="la"):
    x = xy[0]
    if anchor[0] == "m":
        x -= tw(d, s, f, tr) / 2
    elif anchor[0] == "r":
        x -= tw(d, s, f, tr)
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=f) + tr


def soft_shadow(img, radius=22, alpha=120, offset=(0, 8)):
    pad = radius * 2 + abs(offset[0]) + abs(offset[1]) + 8
    base = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    a = img.split()[3]
    solid = Image.new("RGBA", img.size, (8, 4, 3, alpha))
    solid.putalpha(a.point(lambda v: int(v * alpha / 255)))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sh.paste(solid, (pad + offset[0], pad + offset[1]), solid)
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(radius)))
    base.paste(img, (pad, pad), img)
    return base, pad


def blank(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


# ---------------------------------------------------------------- blocs de coupe
for idx, (t0, t1, num, kicker, l1, l2, sub, accent, px, py, r) in enumerate(CUTAWAYS, start=1):
    Wb, Hb = 880, 470
    _, pad = soft_shadow(blank((Wb, Hb)), radius=20, alpha=95, offset=(0, 6))
    size = (Wb + 2 * pad, Hb + 2 * pad)

    parts = {k: blank(size) for k in "abcd"}
    ink = blank((Wb, Hb))

    # (a) carré d'accent + kicker
    d = ImageDraw.Draw(parts["a"]); di = ImageDraw.Draw(ink)
    for dd in (d, di):
        dd.rectangle((pad, pad + 12, pad + 10, pad + 32), fill=(*accent, 255))
        track(dd, (pad + 28, pad + 6), kicker, font("sg500", 24), (233, 189, 124, 240), tr=8)

    # (b) titre serif
    d = ImageDraw.Draw(parts["b"]); di = ImageDraw.Draw(ink)
    for dd in (d, di):
        dd.text((pad, pad + 64), l1, font=font("isr", 104), fill=CREAM)
        dd.text((pad, pad + 172), l2, font=font("isr", 104), fill=CREAM)

    # (c) filet dégradé
    d = ImageDraw.Draw(parts["c"]); di = ImageDraw.Draw(ink)
    for dd in (d, di):
        for x in range(360):
            a = int(190 * (1 - x / 360) ** 1.4)
            dd.line((pad + x, pad + 296, pad + x, pad + 299), fill=(233, 189, 124, a))

    # (d) sous-titre + index
    d = ImageDraw.Draw(parts["d"]); di = ImageDraw.Draw(ink)
    for dd in (d, di):
        dd.text((pad, pad + 322), sub, font=font("in300", 30), fill=(240, 229, 212, 235))
        track(dd, (pad, pad + Hb - 40), num, font("sg500", 22), (233, 189, 124, 200), tr=6)

    for k in "abcd":
        parts[k].save(os.path.join(A, f"cut{idx:02d}_{k}.png"))

    out, _ = soft_shadow(ink, radius=20, alpha=95, offset=(0, 6))
    out.save(os.path.join(A, f"cut{idx:02d}.png"))
    print(f"  cut{idx:02d} a-d + bloc complet {out.size} (pad {pad})")

# ---------------------------------------------------------------- carte finale
Wb, Hb = 936, 700
_, pad = soft_shadow(blank((Wb, Hb)), radius=22, alpha=110, offset=(0, 7))
size = (Wb + 2 * pad, Hb + 2 * pad)
parts = {k: blank(size) for k in "abcd"}
ink = blank((Wb, Hb))

d = ImageDraw.Draw(parts["a"]); di = ImageDraw.Draw(ink)
for dd in (d, di):
    dd.rectangle((pad, pad + 6, pad + 10, pad + 26), fill=(*GOLD, 255))
    track(dd, (pad + 28, pad), "NO HAND-HOLDING NEEDED", font("sg500", 24), (233, 189, 124, 240), tr=8)

d = ImageDraw.Draw(parts["b"]); di = ImageDraw.Draw(ink)
for dd in (d, di):
    dd.text((pad, pad + 74), "The Rockwood", font=font("isr", 122), fill=CREAM)
    dd.text((pad, pad + 202), "Method", font=font("isr", 122), fill=CREAM)

d = ImageDraw.Draw(parts["c"]); di = ImageDraw.Draw(ink)
for dd in (d, di):
    dd.line((pad, pad + 358, pad + Wb, pad + 358), fill=(233, 189, 124, 170), width=3)

d = ImageDraw.Draw(parts["d"]); di = ImageDraw.Draw(ink)
for dd in (d, di):
    dd.text((pad, pad + 392), "self-guided.  downloadable.  yours.", font=font("isr", 56),
            fill=(242, 231, 214, 245))

for k in "abcd":
    parts[k].save(os.path.join(A, f"endtype_{k}.png"))
out, _ = soft_shadow(ink, radius=22, alpha=110, offset=(0, 7))
out.save(os.path.join(A, "endtype.png"))
print(f"  endtype a-d + bloc complet {out.size} (pad {pad})")

print("Habillage v7 (parties animables) généré.")
