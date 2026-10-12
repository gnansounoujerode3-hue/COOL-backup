#!/usr/bin/env python3
"""Génère l'habillage v3 : bandeau, running head, scènes de coupe, médaillon, cartes.

Tout est dessiné par script (aucune image tierce).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan3 import (CREAM, GOLD, GOLD_DEEP, TERRA, SLATE, ESPRESSO, INK,  # noqa: E402
                   CUTAWAYS, SCENES, W, H, X_L, X_R, RULE_Y)

OUT = os.path.dirname(os.path.abspath(__file__))
A = os.environ.get("ROCKWOOD_ASSETS",
                   os.path.join(os.path.dirname(OUT), "assets"))
os.makedirs(A, exist_ok=True)

A_ROOT = os.environ.get("ROCKWOOD_WORK", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NM = os.environ.get("ROCKWOOD_FONTS", os.path.join(A_ROOT, "node_modules")) + "/@expo-google-fonts"
F = {
    "sg300": f"{NM}/space-grotesk/300Light/SpaceGrotesk_300Light.ttf",
    "sg400": f"{NM}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
    "sg500": f"{NM}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
    "sg700": f"{NM}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "in300": f"{NM}/inter/300Light/Inter_300Light.ttf",
    "in400": f"{NM}/inter/400Regular/Inter_400Regular.ttf",
    "in500": f"{NM}/inter/500Medium/Inter_500Medium.ttf",
    "in600": f"{NM}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "in700": f"{NM}/inter/700Bold/Inter_700Bold.ttf",
    "isr": f"{NM}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
    "is": f"{NM}/instrument-serif/400Regular/InstrumentSerif_400Regular.ttf",
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


def save(name, img):
    img.save(os.path.join(A, name + ".png"))
    print(f"  {name}.png {img.size}")


def shadowed(img, radius=30, alpha=140, offset=(0, 12)):
    pad = radius * 2 + abs(offset[0]) + abs(offset[1]) + 8
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    a = img.split()[3]
    solid = Image.new("RGBA", img.size, (10, 5, 4, alpha))
    solid.putalpha(a.point(lambda v: int(v * alpha / 255)))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste(solid, (pad + offset[0], pad + offset[1]), solid)
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(radius)))
    out.paste(img, (pad, pad), img)
    return out, pad


def paneled(inner, pad_extra=28, blur=26, top=112, bottom=188):
    w, h = inner.width, inner.height
    pad = blur * 2 + pad_extra
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dc = ImageDraw.Draw(core)
    for y in range(h):
        t = y / max(1, h - 1)
        dc.line((0, y, w, y), fill=(20, 11, 9, int(top + (bottom - top) * t)))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=30, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    core.putalpha(Image.composite(core.split()[3], Image.new("L", (w, h), 0), mask))
    out.alpha_composite(core, (pad, pad))
    out.alpha_composite(inner, (pad, pad))
    return out, pad


def gradient_fill(size, c1, c2, vertical=True):
    w, h = size
    im = Image.new("RGB", size, c1)
    px = im.load()
    n = h if vertical else w
    for i in range(n):
        t = i / max(1, n - 1)
        col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        if vertical:
            for x in range(w):
                px[x, i] = col
        else:
            for y in range(h):
                px[i, y] = col
    return im


def dot_grid(size, step=44, alpha=16, off=0):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(off, size[1], step):
        for x in range(off, size[0], step):
            d.point((x, y), fill=(253, 247, 236, alpha))
    return im


# ================================================================== bandeau
mh = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
d = ImageDraw.Draw(mh)
track(d, (X_L, 100), "ROCKWOOD METHOD", font("sg500", 26), CREAM, tr=7)
d.line((X_L, RULE_Y, X_R, RULE_Y), fill=(253, 247, 236, 58), width=2)
save("masthead", mh)

# running head (changements de scène)
for i, (t0, t1, label) in enumerate(SCENES):
    im = Image.new("RGBA", (520, 60), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    track(dd, (520, 12), label, font("sg400", 21), (233, 189, 124, 235), tr=7, anchor="ra")
    save(f"head{i}", im)

# barre de progression
prog = Image.new("RGBA", (X_R - X_L, 8), (0, 0, 0, 0))
dp = ImageDraw.Draw(prog)
dp.rounded_rectangle((0, 0, X_R - X_L - 1, 7), radius=4, fill=GOLD + (255,))
save("progress", prog)

# ================================================================== dégradés
def vgrad(name, h, a0, a1, power=1.6, col=(16, 9, 7)):
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        a = int(a0 + (a1 - a0) * ((y / max(1, h - 1)) ** power))
        if a <= 0:
            continue
        row = col + (a,)
        for x in range(W):
            px[x, y] = row
    return im


save("scrim_top", vgrad("x", 420, 130, 0, 1.35))
save("scrim_bottom", vgrad("x", 680, 0, 172, 1.95))

glow = Image.new("RGBA", (1300, 1300), (0, 0, 0, 0))
dg = ImageDraw.Draw(glow)
cx, cy = 1300 * 0.6, 1300 * 0.38
for i in range(30, 0, -1):
    t = i / 30
    r = int(650 * t)
    a = int(24 * (1 - t) ** 2.4)
    if a > 0:
        dg.ellipse((cx - r, cy - r * 0.9, cx + r, cy + r * 0.9), fill=(233, 189, 124, a))
save("glow", glow.filter(ImageFilter.GaussianBlur(58)))

# ================================================================== blocs de titre
def headline(kicker, lines, sub=None):
    tmp = Image.new("RGBA", (10, 10))
    dt = ImageDraw.Draw(tmp)
    f_k, f_h, f_s = font("sg500", 22), font("isr", 86), font("in300", 28)
    w = max([tw(dt, kicker, f_k, 8)] + [dt.textlength(l, font=f_h) for l in lines]
            + ([tw(dt, sub, f_s)] if sub else []))
    h = 34 + len(lines) * 92 + 30 + (52 if sub else 0)
    im = Image.new("RGBA", (int(w) + 90, int(h) + 40), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    xr = im.width - 24
    y = 20
    track(dd, (xr, y), kicker, f_k, GOLD, tr=8, anchor="ra")
    y += 44
    for ln in lines:
        dd.text((xr, y), ln, font=f_h, fill=CREAM, anchor="ra")
        y += 92
    y += 6
    dd.line((xr - 200, y, xr, y), fill=(233, 189, 124, 210), width=3)
    y += 30
    if sub:
        dd.text((xr, y), sub, font=f_s, fill=(240, 228, 210), anchor="ra")
    return im


out, _ = shadowed(headline("THE METHOD", ["The Rockwood", "Method"], "self-guided  ·  downloadable"))
save("hl_title", out)
out, _ = shadowed(headline("THE FOUNDATION", ["Rock solid."], "no hand-holding needed"))
save("hl_foundation", out)

# ================================================================== cartes produit (plan caméra)
def card(num, name, sub, accent):
    inner = Image.new("RGBA", (620, 112), (0, 0, 0, 0))
    dd = ImageDraw.Draw(inner)
    dd.line((0, 0, 620, 0), fill=(253, 247, 236, 80), width=2)
    track(dd, (0, 24), num, font("sg500", 24), accent, tr=5)
    dd.text((74, 16), name, font="", fill=CREAM) if False else None
    dd.text((74, 16), name, font=font("in600", 40), fill=CREAM)
    dd.text((74, 66), sub, font=font("in300", 26), fill=(238, 224, 205, 225))
    dd.line((0, 111, 620, 111), fill=accent + (215,), width=3)
    return inner


for tag, args in {
    "card01": ("01", "Financial Playbook", "the complete guide, step by step", GOLD),
    "card02": ("02", "Planner Bundle", "budget, debt, goals — print it", TERRA),
    "card03": ("03", "AI Income Optimizer", "a plan tuned to your numbers", SLATE),
}.items():
    out, _ = paneled(card(*args))
    save(tag, out)

# ================================================================== autocollant
st = Image.new("RGBA", (330, 250), (0, 0, 0, 0))
d = ImageDraw.Draw(st)
d.rounded_rectangle((6, 6, 324, 244), radius=30, fill=(253, 247, 236, 252))
d.rounded_rectangle((6, 6, 324, 244), radius=30, outline=(23, 13, 10, 45), width=2)
d.ellipse((44, 74, 190, 190), outline=(23, 13, 10, 235), width=5)
for cx, cy in ((78, 108), (120, 92), (132, 140), (92, 152)):
    d.ellipse((cx, cy, cx + 20, cy + 18), fill=(23, 13, 10, 215))
d.polygon([(196, 96), (286, 74), (300, 132), (210, 154)], fill=GOLD + (255,),
          outline=(23, 13, 10, 225))
d.text((248, 114), "$0", font=font("sg700", 34), fill=INK, anchor="mm")
out, _ = shadowed(st.rotate(-8, resample=Image.BICUBIC, expand=True), 20, 140, (0, 10))
save("sticker", out)

# ================================================================== tampon
sp = Image.new("RGBA", (520, 150), (0, 0, 0, 0))
d = ImageDraw.Draw(sp)
d.rounded_rectangle((4, 4, 516, 146), radius=14, outline=GOLD + (255,), width=5)
d.rounded_rectangle((18, 18, 502, 132), radius=8, outline=(233, 189, 124, 130), width=2)
track(d, (260, 75), "GAME CHANGER", font("sg700", 46), GOLD, tr=2, anchor="mm")
out, _ = paneled(sp.rotate(3, resample=Image.BICUBIC, expand=True), 24, 22)
save("stamp", out)

# ================================================================== compteur (base)
cnt = Image.new("RGBA", (760, 300), (0, 0, 0, 0))
d = ImageDraw.Draw(cnt)
d.line((560, 214, 736, 214), fill=(233, 189, 124, 210), width=3)
track(d, (736, 232), "SELF-GUIDED  ·  ZERO HASSLE", font("sg500", 26), CREAM, tr=7, anchor="ra")
out, _ = paneled(cnt, 30, 26)
save("count_base", out)

# ================================================================== split
def split_line(text, color, size=74):
    im = Image.new("RGBA", (760, 110), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.text((0, 8), text, font=font("isr", size), fill=color)
    return im


out, _ = shadowed(split_line("Less stress.", CREAM), 24, 130, (0, 8))
save("split_top", out)
out, _ = shadowed(split_line("More savings.", GOLD), 24, 130, (0, 8))
save("split_bot", out)

rule = Image.new("RGBA", (420, 10), (0, 0, 0, 0))
ImageDraw.Draw(rule).rounded_rectangle((0, 2, 419, 7), radius=3, fill=GOLD + (235,))
save("split_rule", rule)

# ================================================================== pastille CTA
pill = Image.new("RGBA", (780, 132), (0, 0, 0, 0))
d = ImageDraw.Draw(pill)
d.rounded_rectangle((0, 0, 779, 131), radius=66, fill=GOLD + (255,))
d.text((340, 66), "rockwoodmethod.com/shop", font=font("sg500", 40), fill=INK, anchor="mm")
out, _ = shadowed(pill, 24, 150, (0, 10))
save("pill", out)

# flèche du CTA (animée en x)
ar = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
d = ImageDraw.Draw(ar)
d.ellipse((0, 0, 109, 109), fill=INK)
d.polygon([(36, 34), (80, 55), (36, 76)], fill=GOLD)
out, _ = shadowed(ar, 16, 120, (0, 6))
save("arrow", out)

# ================================================================== médaillon
ring = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
d = ImageDraw.Draw(ring)
d.ellipse((10, 10, 409, 409), outline=GOLD + (215,), width=5)
d.ellipse((24, 24, 395, 395), outline=(233, 189, 124, 70), width=2)
save("ring", ring)

mask = Image.new("L", (400, 400), 0)
ImageDraw.Draw(mask).ellipse((0, 0, 399, 399), fill=255)
save("mask_circle", mask.convert("RGBA"))

# ================================================================== scènes de coupe
for t0, t1, idx, kicker, l1, l2, sub, accent, px, py, r in CUTAWAYS:
    bg = gradient_fill((W, H), (34, 20, 16), (16, 9, 7)).convert("RGBA")
    bg.alpha_composite(dot_grid((W, H), 46, 21, 10))
    d = ImageDraw.Draw(bg)
    # filet d'accent vertical en haut à gauche + kicker
    d.line((X_L, 250, X_L, 330), fill=accent + (230,), width=5)
    track(d, (X_L + 26, 276), kicker, font("sg500", 25), accent, tr=9)
    # titre serif
    d.text((X_L, 380), l1, font=font("isr", 132), fill=CREAM)
    d.text((X_L, 520), l2, font=font("isr", 132), fill=CREAM)
    # filet
    d.line((X_L, 700, X_L + 330, 700), fill=accent + (225,), width=4)
    d.text((X_L, 736), sub, font=font("in300", 33), fill=(238, 226, 208, 235))
    # chiffre fantôme en fond (signature éditoriale) — calque séparé, alpha maîtrisé
    ghost_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg2 = ImageDraw.Draw(ghost_layer)
    dg2.text((W - 40, 980), idx.split()[0], font=ImageFont.truetype(F["is"], 520),
             fill=(233, 189, 124, 255), anchor="rm")
    ghost_layer.putalpha(ghost_layer.getchannel("A").point(lambda v: int(v * 0.115)))
    bg.alpha_composite(ghost_layer)
    # arc graphique
    arc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(arc)
    da.arc((X_L - 260, 880, X_L + 700, 1840), 180, 360, fill=(233, 189, 124, 70), width=3)
    da.arc((X_L - 200, 940, X_L + 640, 1780), 180, 360, fill=(233, 189, 124, 34), width=2)
    bg.alpha_composite(arc)
    # index
    track(d, (X_L, H - 132), idx, font("sg400", 24), (233, 189, 124, 225), tr=6)
    # halo d'accent derrière le médaillon
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dh = ImageDraw.Draw(halo)
    for i in range(26, 0, -1):
        t = i / 26
        rr = int(r * 2.4 * t)
        dh.ellipse((px - rr, py - rr, px + rr, py + rr),
                   fill=accent + (int(9 * (1 - t) ** 1.8),))
    bg.alpha_composite(halo.filter(ImageFilter.GaussianBlur(40)))
    d.line((X_L, H - 168, X_R, H - 168), fill=(253, 247, 236, 55), width=2)
    save(f"cutaway_{idx.split()[0]}", bg)

# ================================================================== carte finale
ec = gradient_fill((W, H), (32, 18, 14), (14, 8, 6)).convert("RGBA")
ec.alpha_composite(dot_grid((W, H), 46, 20, 12))
d = ImageDraw.Draw(ec)
d.line((X_L, 300, X_L, 380), fill=GOLD + (230,), width=5)
track(d, (X_L + 26, 326), "NO HAND-HOLDING NEEDED", font("sg500", 25), GOLD, tr=9)
d.text((X_L, 470), "The Rockwood", font=font("isr", 122), fill=CREAM)
d.text((X_L, 604), "Method", font=font("isr", 122), fill=CREAM)
d.line((X_L, 780, X_L + 420, 780), fill=GOLD + (225,), width=4)
d.text((X_L, 816), "self-guided.  downloadable.  yours.", font=font("isr", 52),
       fill=(240, 228, 210))
d.rounded_rectangle((X_L, 960, X_R, 960 + 128), radius=64, fill=GOLD + (255,))
d.text(((X_L + X_R) / 2, 960 + 64), "rockwoodmethod.com/shop",
       font=font("sg500", 42), fill=INK, anchor="mm")
d.text((X_L, 1136), "link in bio", font=font("in300", 30), fill=(226, 210, 190, 235))
track(d, (X_L, H - 132), "BUILD YOUR FOUNDATION", font("sg400", 22), (233, 189, 124, 215), tr=8)
d.line((X_L, H - 168, X_R, H - 168), fill=(253, 247, 236, 55), width=2)
save("endcard", ec)

# ================================================================== couverture
cov_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dc = ImageDraw.Draw(cov_ov)
for y in range(560):
    dc.line((0, y, W, y), fill=(17, 9, 7, int(150 * (1 - y / 560) ** 1.5)))
for y in range(720):
    dc.line((0, H - 720 + y, W, H - 720 + y), fill=(17, 9, 7, int(228 * (y / 720) ** 1.35)))
save("cover_overlay", cov_ov)
print("\nHabillage v3 complet ->", A)
