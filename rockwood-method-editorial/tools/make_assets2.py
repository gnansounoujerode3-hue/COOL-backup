#!/usr/bin/env python3
"""Habillage éditorial v2 : système typographique à filets fins, sans cadres lourds.

Génère des PNG transparents dans build2/assets2/ :
  masthead      bandeau haut (nom + filet + libellé droit)
  progress      barre d'or du filet (recadrée image par image)
  scrim_top     dégradé haut (lisibilité du bandeau)
  scrim_bottom  dégradé bas (lisibilité des sous-titres)
  glow          halo chaud (moments forts)
  hl_*          blocs de titre alignés à droite (zone droite haute)
  rows          cartes produit en filets
  sticker       autocollant patate
  stamp         tampon GAME CHANGER
  big           grand chiffre 100 %
  split         less stress / more savings
  pill          pastille CTA
  endcard       carte finale
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(OUT, "assets2")
os.makedirs(A, exist_ok=True)

NM = "/home/user/work2/node_modules/@expo-google-fonts"
F = {
    "sg300": f"{NM}/space-grotesk/300Light/SpaceGrotesk_300Light.ttf",
    "sg400": f"{NM}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
    "sg500": f"{NM}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
    "sg700": f"{NM}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "in300": f"{NM}/inter/300Light/Inter_300Light.ttf",
    "in400": f"{NM}/inter/400Regular/Inter_400Regular.ttf",
    "in500": f"{NM}/inter/500Medium/Inter_500Medium.ttf",
    "in600": f"{NM}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "isr": f"{NM}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
}
CREAM = (253, 247, 236)
GOLD = (233, 189, 124)
INK = (23, 13, 10)
W, H = 1080, 1920
X_L, X_R = 72, 1008          # marges du système
RULE_Y = 168                  # filet du bandeau
RIGHT_ZONE = (X_R, 250, 560)  # (bord droit, y haut, y bas max) des blocs de titre


def font(k, s):
    return ImageFont.truetype(F[k], s)


def tw(d, s, f, tr=0):
    return sum(d.textlength(c, font=f) for c in s) + tr * max(0, len(s) - 1)


def track(d, xy, s, f, fill, tr=0, anchor="la"):
    if not tr:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    x = xy[0]
    if anchor[0] == "m":
        x -= tw(d, s, f, tr) / 2
    elif anchor[0] == "r":
        x -= tw(d, s, f, tr)
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=f) + tr


MANIFEST = {}


def save(name, img, pad=0):
    img.save(os.path.join(A, name + ".png"))
    MANIFEST[name] = {"w": img.width, "h": img.height, "pad": pad}
    print(f"  {name}.png {img.size}")


# ------------------------------------------------------------------ bandeau
mh_h = 210
mh = Image.new("RGBA", (W, mh_h), (0, 0, 0, 0))
d = ImageDraw.Draw(mh)
track(d, (X_L, 100), "ROCKWOOD METHOD", font("sg500", 26), CREAM, tr=7)
track(d, (X_R, 104), "SELF-GUIDED FILM", font("sg400", 22), (233, 189, 124, 210), tr=6, anchor="ra")
d.line((X_L, RULE_Y, X_R, RULE_Y), fill=(253, 247, 236, 60), width=2)
save("masthead", mh)

# barre de progression (recadrée en largeur image par image)
prog = Image.new("RGBA", (X_R - X_L, 8), (0, 0, 0, 0))
dp = ImageDraw.Draw(prog)
dp.rounded_rectangle((0, 0, X_R - X_L - 1, 7), radius=4, fill=GOLD + (255,))
save("progress", prog)

# ------------------------------------------------------------------ dégradés
def gradient(name, top_alpha, bottom_alpha, h, power=1.7):
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        t = y / max(1, h - 1)
        a = int(top_alpha + (bottom_alpha - top_alpha) * (t ** power))
        if a <= 0:
            continue
        row = (16, 9, 7, a)
        for x in range(W):
            px[x, y] = row
    return im

save("scrim_top", gradient("x", 128, 0, 420, power=1.35))
save("scrim_bottom", gradient("x", 0, 168, 660, power=1.9))

# halo chaud (coins haut-droit)
g = 1400
glow = Image.new("RGBA", (g, g), (0, 0, 0, 0))
dg = ImageDraw.Draw(glow)
cx, cy = g * 0.62, g * 0.36
for i in range(30, 0, -1):
    t = i / 46
    r = int(g * 0.5 * t)
    a = int(26 * (1 - t) ** 2.4)
    if a <= 0:
        continue
    dg.ellipse((cx - r, cy - r * 0.9, cx + r, cy + r * 0.9), fill=(233, 189, 124, a))
glow = glow.filter(ImageFilter.GaussianBlur(60))
save("glow", glow)


def shadowed(img, radius=30, alpha=135, offset=(0, 12)):
    pad = radius * 2 + abs(offset[0]) + abs(offset[1]) + 8
    shadowed.last_pad = pad
    base = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3]
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    solid = Image.new("RGBA", img.size, (12, 6, 4, alpha))
    solid.putalpha(a.point(lambda v: int(v * alpha / 255)))
    sh.paste(solid, (pad + offset[0], pad + offset[1]), solid)
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(radius)))
    base.paste(img, (pad, pad), img)
    return base


# ------------------------------------------------------------------ blocs de titre
def soft_panel(w, h, radius=34, top=118, bottom=196):
    """Panneau sombre à bords fondus : lisibilité sans lourdeur."""
    blur = 26
    pad = blur * 2 + 6
    panel = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dc = ImageDraw.Draw(core)
    for y in range(h):
        t = y / max(1, h - 1)
        dc.line((0, y, w, y), fill=(20, 11, 9, int(top + (bottom - top) * t)))
    dc.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=None, outline=None)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    core.putalpha(Image.composite(core.split()[3], Image.new("L", (w, h), 0), mask))
    panel.alpha_composite(core, (pad, pad))
    return panel, pad


def paneled(inner, pad_extra=26, blur=24):
    """Compose un panneau sombre doux derrière un bloc (bords fondus)."""
    w, h = inner.width, inner.height
    pad = blur * 2 + pad_extra
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dc = ImageDraw.Draw(core)
    for y in range(h):
        t = y / max(1, h - 1)
        dc.line((0, y, w, y), fill=(18, 10, 8, int(96 + 76 * t)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=30, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    core.putalpha(Image.composite(core.split()[3], Image.new("L", (w, h), 0), mask))
    out.alpha_composite(core, (pad, pad))
    out.alpha_composite(inner, (pad, pad))
    return out, pad


def save_paneled(name, inner):
    out, pad = paneled(inner)
    out.save(os.path.join(A, name + ".png"))
    print(f"  {name}.png {out.size} (panneau {pad})")


def headline_block(kicker, lines, sub=None, rule=True):
    """Bloc aligné à droite : kicker tracked, titre serif italique, filet, sous-titre."""
    pad = 26
    tmp = Image.new("RGBA", (10, 10))
    dt = ImageDraw.Draw(tmp)
    f_k, f_h, f_s = font("sg500", 22), font("isr", 86), font("in300", 28)
    w = max([tw(dt, kicker, f_k, 9)] + [dt.textlength(l, font=f_h) for l in lines]
            + ([tw(dt, sub, f_s)] if sub else []))
    h = 34 + len(lines) * 92 + (30 if rule else 0) + (52 if sub else 0)

    im = Image.new("RGBA", (int(w) + 2 * pad + 30, int(h) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    xr = im.width - pad
    y = pad
    track(d, (xr, y), kicker, f_k, GOLD, tr=8, anchor="ra")
    y += 44
    for ln in lines:
        d.text((xr, y), ln, font=f_h, fill=CREAM, anchor="ra")
        y += 92
    if rule:
        y += 6
        d.line((xr - 200, y, xr, y), fill=(233, 189, 124, 210), width=3)
        y += 30
    if sub:
        d.text((xr, y), sub, font=f_s, fill=(240, 228, 210), anchor="ra")
    return shadowed(im, radius=26, alpha=120, offset=(0, 10))


save("hl_method", headline_block(
    "THE METHOD", ["The Rockwood", "Method"], "self-guided  ·  downloadable"))
save("hl_foundation", headline_block(
    "THE FOUNDATION", ["Rock solid."], "no hand-holding needed"))
save("hl_after", headline_block(
    "AFTER ROCKWOOD", ["Less stress.", "More savings."]))

# ------------------------------------------------------------------ 100 %
big = Image.new("RGBA", (600, 232), (0, 0, 0, 0))
d = ImageDraw.Draw(big)
d.text((600 - 24, 0), "100%", font=font("sg700", 136), fill=GOLD, anchor="ra")
d.line((600 - 24 - 190, 186, 600 - 24, 186), fill=(233, 189, 124, 205), width=3)
track(d, (600 - 24, 202), "SELF-GUIDED  ·  ZERO HASSLE", font("sg500", 26), CREAM, tr=7, anchor="ra")
save_paneled("big100", big)

# ------------------------------------------------------------------ cartes produit (filets)
def product_rows(items):
    im = Image.new("RGBA", (620, 116 * len(items) + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (num, name, sub) in enumerate(items):
        y = i * 116
        d.line((0, y, 620, y), fill=(253, 247, 236, 90), width=2)
        track(d, (0, y + 26), num, font("sg500", 24), GOLD, tr=5)
        d.text((74, y + 18), name, font=font("in600", 40), fill=CREAM)
        d.text((74, y + 68), sub, font=font("in300", 26), fill=(238, 224, 205, 220))
    d.line((0, 116 * len(items), 620, 116 * len(items)), fill=(233, 189, 124, 200), width=3)
    return shadowed(im, radius=22, alpha=150, offset=(0, 8))


save_paneled("rows01", product_rows([("01", "Financial Playbook", "the complete guide, step by step")]))
save_paneled("rows02", product_rows([("01", "Financial Playbook", "the complete guide, step by step"),
                             ("02", "Planner Bundle", "budget, debt, goals — print it")]))
save_paneled("rows03", product_rows([("01", "Financial Playbook", "the complete guide, step by step"),
                             ("02", "Planner Bundle", "budget, debt, goals — print it"),
                             ("03", "AI Income Optimizer", "a plan tuned to your numbers")]))

# ------------------------------------------------------------------ autocollant patate
st = Image.new("RGBA", (330, 250), (0, 0, 0, 0))
d = ImageDraw.Draw(st)
d.rounded_rectangle((6, 6, 324, 244), radius=30, fill=(253, 247, 236, 252))
d.rounded_rectangle((6, 6, 324, 244), radius=30, outline=(23, 13, 10, 40), width=2)
# dessin au trait
d.ellipse((44, 74, 190, 190), outline=(23, 13, 10, 235), width=5)
d.ellipse((78, 108, 100, 126), fill=(23, 13, 10, 210))
d.ellipse((120, 92, 140, 110), fill=(23, 13, 10, 210))
d.ellipse((132, 140, 152, 158), fill=(23, 13, 10, 210))
d.ellipse((92, 152, 108, 168), fill=(23, 13, 10, 210))
# étiquette prix
d.polygon([(196, 96), (286, 74), (300, 132), (210, 154)], fill=(233, 189, 124, 255),
          outline=(23, 13, 10, 225))
d.text((248, 114), "$0", font=font("sg700", 34), fill=INK, anchor="mm")
st = st.rotate(-8, resample=Image.BICUBIC, expand=True)
save("sticker", shadowed(st, radius=20, alpha=140, offset=(0, 10)))

# ------------------------------------------------------------------ tampon
sp = Image.new("RGBA", (520, 150), (0, 0, 0, 0))
d = ImageDraw.Draw(sp)
d.rounded_rectangle((4, 4, 516, 146), radius=14, outline=(233, 189, 124, 255), width=5)
d.rounded_rectangle((18, 18, 502, 132), radius=8, outline=(233, 189, 124, 130), width=2)
track(d, (260, 75), "GAME CHANGER", font("sg700", 46), GOLD, tr=2, anchor="mm")
save_paneled("stamp", sp.rotate(3, resample=Image.BICUBIC, expand=True))

# ------------------------------------------------------------------ pastille CTA
pill = Image.new("RGBA", (760, 132), (0, 0, 0, 0))
d = ImageDraw.Draw(pill)
d.rounded_rectangle((0, 0, 759, 131), radius=66, fill=(233, 189, 124, 255))
d.text((330, 66), "rockwoodmethod.com/shop", font=font("sg500", 40), fill=INK, anchor="mm")
d.ellipse((610, 26, 690, 106), fill=INK)
d.polygon([(636, 56), (674, 66), (636, 76)], fill=GOLD)
save("pill", shadowed(pill, radius=24, alpha=150, offset=(0, 10)))

# ------------------------------------------------------------------ carte finale
ec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ec)
# voile dégradé (plus élégant qu'un aplat)
for y in range(H):
    t = y / H
    a = int(206 * min(1, (t - 0.035) / 0.5) ** 1.15) if t > 0.035 else 0
    a = min(236, a)
    if a:
        d.line((0, y, W, y), fill=(20, 11, 9, a))
track(d, (X_L, 430), "NO HAND-HOLDING NEEDED", font("sg400", 24), GOLD, tr=9)
d.line((X_L, 486, X_R, 486), fill=(253, 247, 236, 70), width=2)
d.text((X_L, 560), "The Rockwood", font=font("isr", 118), fill=CREAM)
d.text((X_L, 692), "Method", font=font("isr", 118), fill=CREAM)
d.line((X_L, 850, X_R, 850), fill=(233, 189, 124, 190), width=3)
d.text((X_L, 894), "self-guided.  downloadable.  yours.", font=font("isr", 52),
       fill=(240, 228, 210))
d.rounded_rectangle((X_L, 1010, X_R, 1010 + 128), radius=64, fill=(233, 189, 124, 255))
d.text(((X_L + X_R) / 2, 1010 + 64), "rockwoodmethod.com/shop",
       font=font("sg500", 42), fill=INK, anchor="mm")
d.text((X_L, 1186), "link in bio", font=font("in300", 30),
       fill=(226, 210, 190, 235))
track(d, (X_L, 1840), "BUILD YOUR FOUNDATION", font("sg400", 22),
      (233, 189, 124, 200), tr=8)
save("endcard", ec)

import json as _json
_json.dump(MANIFEST, open(os.path.join(A, "manifest.json"), "w"), indent=1)
print("\nHabillage v2 complet ->", A)
