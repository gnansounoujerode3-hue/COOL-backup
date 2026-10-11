#!/usr/bin/env python3
"""V4 : visuels produit dessinés (aucune image externe) pour les scènes de coupe.

Lit plan4.PRODUCTS et écrit :
  assets3/prod_playbook.png   couverture de livre (portrait, filet or, sceau)
  assets3/prod_planner.png    double page de planner (lignes, cases, barres)
  assets3/prod_optimizer.png  carte sombre (anneau de progression, barres, libellés)

Puis recompose les scènes de coupe avec le visuel intégré.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan3 import (CUTAWAYS, GOLD, H, SLATE, TERRA, W, X_L, X_R)  # noqa: E402

WORK = "/home/user/w3"
A = os.path.join(WORK, "tools3/assets3")
NM = f"{WORK}/node_modules/@expo-google-fonts"
CREAM = (253, 247, 236)
ESPRESSO = (28, 16, 13)
INK = (20, 11, 9)


def F(k):
    return {
        "isr": f"{NM}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
        "is": f"{NM}/instrument-serif/400Regular/InstrumentSerif_400Regular.ttf",
        "sg400": f"{NM}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
        "sg500": f"{NM}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
        "sg700": f"{NM}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
        "in300": f"{NM}/inter/300Light/Inter_300Light.ttf",
        "in500": f"{NM}/inter/500Medium/Inter_500Medium.ttf",
    }[k]


def font(k, s):
    return ImageFont.truetype(F(k), s)


def track(d, xy, s, f, fill, tr=0, anchor="la"):
    x = xy[0]
    if tr:
        total = sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)
        if anchor[0] == "m":
            x -= total / 2
        elif anchor[0] == "r":
            x -= total
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=f) + tr


def shadow(img, radius=30, alpha=140, off=(0, 16)):
    pad = radius * 2 + abs(off[0]) + abs(off[1]) + 6
    base = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    a = img.split()[3]
    solid = Image.new("RGBA", img.size, (8, 4, 3, alpha))
    solid.putalpha(a.point(lambda v: int(v * alpha / 255)))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sh.paste(solid, (pad + off[0], pad + off[1]), solid)
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(radius)))
    base.paste(img, (pad, pad), img)
    return base, pad


# ------------------------------------------------------------------ 01 playbook
def playbook():
    cw, ch = 400, 520
    pg = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(pg)
    # tranche de pages
    d.rounded_rectangle((6, 12, cw - 12, ch - 6), radius=10, fill=(236, 226, 206, 255))
    # couverture
    d.rounded_rectangle((0, 0, cw - 18, ch - 18), radius=10, fill=ESPRESSO + (255,))
    d.rounded_rectangle((16, 16, cw - 34, ch - 34), radius=6,
                        outline=(233, 189, 124, 150), width=2)
    track(d, (40, 52), "THE ROCKWOOD METHOD", font("sg400", 15), (233, 189, 124, 220), tr=5)
    d.text((40, 116), "Financial", font=font("isr", 62), fill=CREAM)
    d.text((40, 184), "Playbook", font=font("isr", 62), fill=CREAM)
    d.line((40, 268, cw - 74, 268), fill=(233, 189, 124, 210), width=3)
    d.text((40, 292), "the complete guide,", font=font("in300", 22), fill=(236, 224, 205))
    d.text((40, 320), "step by step.", font=font("in300", 22), fill=(236, 224, 205))
    # sceau doré
    d.ellipse((cw - 168, ch - 190, cw - 68, ch - 90), outline=(233, 189, 124, 235), width=3)
    d.ellipse((cw - 158, ch - 180, cw - 78, ch - 100), outline=(233, 189, 124, 120), width=1)
    d.text((cw - 118, ch - 145), "01", font=font("sg700", 30), fill=GOLD)
    pg = pg.rotate(-4, resample=Image.BICUBIC, expand=True)
    out, pad = shadow(pg, 26, 150, (0, 18))
    return out, pad


# ------------------------------------------------------------------ 02 planner
def planner():
    pw, ph = 460, 330
    pg = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(pg)
    for i, x0 in enumerate((0, pw // 2 + 8)):
        wpx = pw // 2 - 8
        d.rounded_rectangle((x0, 0, x0 + wpx, ph), radius=8, fill=(243, 235, 218, 255))
        d.rounded_rectangle((x0, 0, x0 + wpx, ph), radius=8, outline=(206, 190, 166, 255), width=2)
    # page gauche : budget
    d.text((26, 22), "BUDGET", font=font("sg500", 19), fill=INK)
    d.line((26, 50, 200, 50), fill=(180, 150, 110, 255), width=2)
    for i in range(7):
        y = 66 + i * 30
        d.line((26, y, 196, y), fill=(214, 200, 176, 255), width=1)
        d.text((26, y - 20), ["income", "fixed", "variable", "debt", "savings",
                              "goals", "review"][i], font=font("in300", 17),
               fill=(120, 104, 86))
    # page droite : checklist + mini barres
    d.text((pw // 2 + 34, 22), "PLAN", font=font("sg500", 19), fill=INK)
    d.line((pw // 2 + 34, 50, pw - 26, 50), fill=(180, 150, 110, 255), width=2)
    for i in range(4):
        y = 72 + i * 34
        d.rounded_rectangle((pw // 2 + 34, y, pw // 2 + 52, y + 18), radius=4,
                            outline=(150, 130, 105, 255), width=2)
        d.line((pw // 2 + 62, y + 9, pw - 30, y + 9), fill=(214, 200, 176, 255), width=2)
    for i, hgt in enumerate((26, 40, 58, 34)):
        x = pw // 2 + 40 + i * 34
        d.rounded_rectangle((x, ph - 40 - hgt, x + 20, ph - 40), radius=4,
                            fill=(198, 152, 92, 235))
    out, pad = shadow(pg, 26, 150, (0, 18))
    return out, pad


# ------------------------------------------------------------------ 03 optimizer
def optimizer():
    cw, ch = 460, 330
    pg = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(pg)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18, fill=(22, 28, 34, 255))
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18,
                        outline=(129, 159, 178, 130), width=2)
    track(d, (26, 24), "AI INCOME OPTIMIZER", font("sg500", 18), (170, 200, 216), tr=5)
    d.line((26, 56, cw - 26, 56), fill=(129, 159, 178, 90), width=2)
    # anneau de progression
    rx, ry, rr = 108, 190, 62
    d.arc((rx - rr, ry - rr, rx + rr, ry + rr), -90, -90 + 258,
          fill=(233, 189, 124, 255), width=9)
    d.arc((rx - rr, ry - rr, rx + rr, ry + rr), -90 + 258, 270,
          fill=(129, 159, 178, 90), width=9)
    d.text((rx, ry - 6), "72", font=font("sg700", 44), fill=CREAM, anchor="mm")
    d.text((rx, ry + 36), "score", font=font("in300", 18), fill=(170, 200, 216), anchor="mm")
    # barres
    labels = (("income", 0.86), ("debt", 0.54), ("savings", 0.68))
    for i, (lab, val) in enumerate(labels):
        y = 96 + i * 46
        d.text((208, y), lab, font=font("in300", 19), fill=(206, 220, 230))
        bw = 190
        d.rounded_rectangle((208, y + 26, 208 + bw, y + 36), radius=5, fill=(40, 52, 60, 255))
        d.rounded_rectangle((208, y + 26, 208 + int(bw * val), y + 36), radius=5,
                            fill=(233, 189, 124, 235))
    out, pad = shadow(pg, 26, 150, (0, 18))
    return out, pad


BUILD = {"prod_playbook": playbook, "prod_planner": planner, "prod_optimizer": optimizer}
for name, fn in BUILD.items():
    img, pad = fn()
    img.save(os.path.join(A, name + ".png"))
    print(f"  {name}.png {img.size} (pad {pad})")

# ------------------------------------------------------------------ recomposition des scènes de coupe
from plan4 import PRODUCTS  # noqa: E402

# les helpers proviennent de assets3 (import : régénère les assets d'origine)
import assets3 as A3  # noqa: E402

gradient_fill, dot_grid = A3.gradient_fill, A3.dot_grid

for t0, t1, idx, kicker, l1, l2, sub, accent, px, py, r in CUTAWAYS:
    bg = gradient_fill((W, H), (34, 20, 16), (16, 9, 7)).convert("RGBA")
    bg.alpha_composite(dot_grid((W, H), 46, 21, 10))
    d = ImageDraw.Draw(bg)
    # filet d'accent + kicker
    d.line((X_L, 250, X_L, 330), fill=accent + (230,), width=5)
    track(d, (X_L + 26, 276), kicker, font("sg500", 25), accent, tr=9)
    # titre serif
    d.text((X_L, 370), l1, font=font("isr", 126), fill=CREAM)
    d.text((X_L, 498), l2, font=font("isr", 126), fill=CREAM)
    d.line((X_L, 668, X_L + 300, 668), fill=accent + (225,), width=4)
    d.text((X_L, 700), sub, font=font("in300", 32), fill=(238, 226, 208, 235))
    # chiffre fantôme
    ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(ghost)
    dg.text((W - 36, 1060), idx.split()[0], font=ImageFont.truetype(F("is"), 480),
            fill=(233, 189, 124, 255), anchor="rm")
    ghost.putalpha(ghost.getchannel("A").point(lambda v: int(v * 0.10)))
    bg.alpha_composite(ghost)
    # arc graphique
    arc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(arc)
    da.arc((X_L - 260, 880, X_L + 700, 1840), 180, 360, fill=(233, 189, 124, 62), width=3)
    da.arc((X_L - 200, 940, X_L + 640, 1780), 180, 360, fill=(233, 189, 124, 30), width=2)
    bg.alpha_composite(arc)
    # index + filet bas
    track(d, (X_L, H - 132), idx, font("sg400", 24), (233, 189, 124, 225), tr=6)
    d.line((X_L, H - 168, X_R, H - 168), fill=(253, 247, 236, 55), width=2)
    # halo + visuel produit
    pname, pxa, pya, _anim = PRODUCTS[t0]
    prod = Image.open(os.path.join(A, pname + ".png")).convert("RGBA")
    # halo d'accent derrière le médaillon
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dh = ImageDraw.Draw(halo)
    for i in range(26, 0, -1):
        t = i / 26
        rr = int(r * 2.4 * t)
        dh.ellipse((px - rr, py - rr, px + rr, py + rr),
                   fill=accent + (int(9 * (1 - t) ** 1.8),))
    bg.alpha_composite(halo.filter(ImageFilter.GaussianBlur(40)))
    sc = 0.88
    prod = prod.resize((int(prod.width * sc), int(prod.height * sc)), Image.LANCZOS)
    bg.alpha_composite(prod, (pxa - prod.width, pya))
    save_name = f"cutaway_{idx.split()[0]}"
    bg.save(os.path.join(A, save_name + ".png"))
    print(f"  {save_name}.png + {pname}")
print("scènes de coupe recomposées")
