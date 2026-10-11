#!/usr/bin/env python3
"""Habillage v5 « cinématographique » : blocs typographiques transparents.

Les fonds des scènes de coupe et de la carte finale ne sont plus des aplats :
ils sont fabriqués à partir de l'image du film (voir composite5.cine_bg).
Ici on ne produit que le TEXTE, en PNG transparents.

  cut01/02/03.png  bloc de scène de coupe : carré d'accent, kicker, titre serif, sous-titre, index
  endtype.png      bloc de la carte finale : kicker, titre serif, filet pleine largeur, tagline
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan4 import (CREAM, GOLD, GOLD_DEEP, TERRA, SLATE,  # noqa: E402
                   CUTAWAYS, X_L, X_R)

OUT = os.path.dirname(os.path.abspath(__file__))
A = os.environ.get("ROCKWOOD_ASSETS",
                   os.path.join(os.path.dirname(OUT), "assets"))
os.makedirs(A, exist_ok=True)

A_ROOT = os.environ.get("ROCKWOOD_WORK", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


# ---------------------------------------------------------------- blocs de coupe
for idx, (t0, t1, num, kicker, l1, l2, sub, accent, px, py, r) in enumerate(CUTAWAYS, start=1):
    Wb, Hb = 880, 470
    im = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 6
    # carré d'accent + kicker
    d.rectangle((0, y + 6, 10, y + 26), fill=(*accent, 255))
    track(d, (28, y), kicker, font("sg500", 24), (233, 189, 124, 240), tr=8)
    y += 58
    # titre serif
    d.text((0, y), l1, font=font("isr", 104), fill=CREAM)
    y += 108
    d.text((0, y), l2, font=font("isr", 104), fill=CREAM)
    y += 124
    # filet dégradé
    for x in range(360):
        a = int(190 * (1 - x / 360) ** 1.4)
        d.line((x, y, x, y + 3), fill=(233, 189, 124, a))
    y += 26
    d.text((0, y), sub, font=font("in300", 30), fill=(240, 229, 212, 235))
    # index en bas
    track(d, (0, Hb - 40), num, font("sg500", 22), (233, 189, 124, 200), tr=6)

    out, pad = soft_shadow(im, radius=20, alpha=95, offset=(0, 6))
    out.save(os.path.join(A, f"cut{idx:02d}.png"))
    print(f"  cut{idx:02d}.png {out.size} (pad {pad})")

# ---------------------------------------------------------------- carte finale
Wb, Hb = 936, 700
im = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
y = 0
d.rectangle((0, y + 6, 10, y + 26), fill=(*GOLD, 255))
track(d, (28, y), "NO HAND-HOLDING NEEDED", font("sg500", 24), (233, 189, 124, 240), tr=8)
y += 74
d.text((0, y), "The Rockwood", font=font("isr", 122), fill=CREAM)
y += 128
d.text((0, y), "Method", font=font("isr", 122), fill=CREAM)
y += 156
# filet pleine largeur (déborde des marges : « breaking the grid »)
d.line((0, y, Wb, y), fill=(233, 189, 124, 170), width=3)
y += 34
d.text((0, y), "self-guided.  downloadable.  yours.", font=font("isr", 56),
       fill=(242, 231, 214, 245))
out, pad = soft_shadow(im, radius=22, alpha=110, offset=(0, 7))
out.save(os.path.join(A, "endtype.png"))
print(f"  endtype.png {out.size} (pad {pad})")

print("Habillage v5 (transparent) généré.")
