#!/usr/bin/env python3
"""Génère tous les habillages PNG (fond transparent) + manifest.json des positions."""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(OUT, "assets")
os.makedirs(A, exist_ok=True)

NM = "/home/user/work/node_modules/@expo-google-fonts"
F = {
    "sg300": f"{NM}/space-grotesk/300Light/SpaceGrotesk_300Light.ttf",
    "sg400": f"{NM}/space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf",
    "sg500": f"{NM}/space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf",
    "sg600": f"{NM}/space-grotesk/600SemiBold/SpaceGrotesk_600SemiBold.ttf",
    "sg700": f"{NM}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "in300": f"{NM}/inter/300Light/Inter_300Light.ttf",
    "in400": f"{NM}/inter/400Regular/Inter_400Regular.ttf",
    "in500": f"{NM}/inter/500Medium/Inter_500Medium.ttf",
    "in600": f"{NM}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "in700": f"{NM}/inter/700Bold/Inter_700Bold.ttf",
    "in800": f"{NM}/inter/800ExtraBold/Inter_800ExtraBold.ttf",
    "isr": f"{NM}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
}

CREAM = (255, 244, 226)
GOLD = (245, 194, 107)
ESPRESSO = (36, 19, 16)
DARK = (28, 14, 12)
BLUE = (108, 143, 199)
TERRA = (214, 122, 88)

W, H = 1080, 1920
MANIFEST = {}


def font(key, size):
    return ImageFont.truetype(F[key], size)


def tracked(draw, xy, text, fnt, fill, tracking=0, anchor="la", shadow=None):
    """Texte avec interlettrage."""
    if tracking == 0:
        draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)
        return
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x0 = xy[0]
    if anchor[0] == "m":
        x0 -= total / 2
    elif anchor[0] == "r":
        x0 -= total
    x = x0
    for ch, wd in zip(text, widths):
        draw.text((x, xy[1]), ch, font=fnt, fill=fill, anchor="l" + anchor[1])
        x += wd + tracking


def text_w(draw, text, fnt, tracking=0):
    return sum(draw.textlength(c, font=fnt) for c in text) + tracking * max(0, len(text) - 1)


def shadowed(img, radius=26, alpha=150, offset=(0, 14)):
    """Renvoie une image de taille légèrement agrandie avec l'ombre portée derrière."""
    pad = radius * 2 + abs(offset[1]) + abs(offset[0])
    base = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3]
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    solid = Image.new("RGBA", img.size, (10, 5, 4, alpha))
    solid.putalpha(a.point(lambda v: int(v * alpha / 255)))
    sh.paste(solid, (pad + offset[0], pad + offset[1]), solid)
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    base = Image.alpha_composite(base, sh)
    base.paste(img, (pad, pad), img)
    return base


def save(name, img):
    p = os.path.join(A, name + ".png")
    img.save(p)
    print(f"  {name}.png  {img.size}")
    return p


def rounded(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


# ---------------------------------------------------------------- scrim bas
sc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
px = sc.load()
for y in range(H):
    # dégradé sombre progressif dans le tiers bas
    t = max(0.0, (y - int(H * 0.52)) / (H * 0.48))
    a = int(160 * (t ** 1.7))
    if a:
        for x in range(W):
            px[x, y] = (10, 6, 5, a)
save("scrim", sc)

# ---------------------------------------------------------------- pastille chapitre (non utilisée ici)

# ---------------------------------------------------------------- titre
img = Image.new("RGBA", (980, 420), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, 979, 419), radius=34, fill=(24, 12, 10, 190))
d.rounded_rectangle((0, 0, 979, 419), radius=34, outline=(245, 194, 107, 120), width=2)
d.line((54, 96, 926, 96), fill=(245, 194, 107, 90), width=2)
f_eye = font("sg500", 27)
tracked(d, (490, 54), "SELF-GUIDED  ·  DOWNLOADABLE", f_eye, GOLD, tracking=7, anchor="ma")
f_big = font("sg700", 84)
d.text((490, 132), "THE ROCKWOOD", font=f_big, fill=CREAM, anchor="ma")
d.text((490, 224), "METHOD", font=f_big, fill=CREAM, anchor="ma")
f_acc = font("isr", 60)
tracked(d, (490, 330), "finance magic, made simple", f_acc, GOLD, tracking=0, anchor="ma")
save("title", shadowed(img))

# ---------------------------------------------------------------- pomme de terre
img = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# corps
d.ellipse((30, 70, 330, 274), fill=(200, 149, 90))
d.ellipse((30, 70, 330, 274), outline=(126, 88, 46), width=4)
d.ellipse((70, 150, 120, 186), fill=(160, 114, 62))          # yeux de patate
d.ellipse((150, 108, 190, 136), fill=(160, 114, 62))
d.ellipse((228, 168, 268, 196), fill=(160, 114, 62))
d.ellipse((104, 210, 140, 232), fill=(160, 114, 62))
d.ellipse((196, 116, 224, 132), fill=(160, 114, 62))
d.ellipse((74, 92, 150, 120), fill=(228, 186, 132))          # reflet
# étiquette
d.polygon([(296, 92), (392, 60), (416, 132), (320, 168)], fill=CREAM, outline=(36, 19, 16))
d.line((296, 92, 320, 168), fill=(36, 19, 16), width=3)
f_p = font("sg700", 40)
d.text((352, 104), "$0", font=f_p, fill=ESPRESSO, anchor="mm")
save("potato", shadowed(img, radius=18, alpha=130, offset=(0, 10)))

# ---------------------------------------------------------------- cartes produit
def product_card(num, title, sub, accent=GOLD):
    cw, ch = 940, 168
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=26, fill=(26, 13, 11, 232))
    dd.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=26, outline=(*accent, 150), width=2)
    # pastille numéro
    dd.rounded_rectangle((22, 24, 130, 144), radius=20, fill=(*accent, 255))
    dd.text((76, 84), num, font=font("sg700", 62), fill=ESPRESSO, anchor="mm")
    # textes
    dd.text((166, 44), title, font=font("sg700", 46), fill=CREAM, anchor="la")
    dd.text((166, 104), sub, font=font("in400", 27), fill=(214, 196, 176), anchor="la")
    return shadowed(im, radius=18, alpha=140, offset=(0, 12))

save("p1", product_card("01", "Financial Playbook", "the complete guide, step by step"))
save("p2", product_card("02", "Printable Planner Bundle", "budget, debt, goals — print it", accent=TERRA))
save("p3", product_card("03", "AI Income Optimizer", "a plan tuned to your numbers", accent=BLUE))

# ---------------------------------------------------------------- tampon
img = Image.new("RGBA", (620, 250), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((10, 40, 610, 210), radius=18, fill=(0, 0, 0, 0), outline=GOLD, width=6)
d.rounded_rectangle((24, 54, 596, 196), radius=12, outline=(245, 194, 107, 110), width=2)
tracked(d, (310, 118), "GAME CHANGER", font("sg700", 62), GOLD, tracking=3, anchor="mm")
img = img.rotate(-7, resample=Image.BICUBIC, expand=True)
save("stamp", shadowed(img, radius=16, alpha=140, offset=(0, 10)))

# ---------------------------------------------------------------- fondation
img = Image.new("RGBA", (1000, 330), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, 999, 329), radius=32, fill=(24, 12, 10, 200))
d.line((60, 74, 940, 74), fill=(245, 194, 107, 110), width=3)
d.text((500, 128), "A ROCK-SOLID", font=font("sg700", 74), fill=CREAM, anchor="ma")
d.text((500, 208), "FOUNDATION", font=font("sg700", 74), fill=GOLD, anchor="ma")
f_a = font("isr", 44)
d.text((500, 296), "no hand-holding needed", font=f_a, fill=(226, 208, 188), anchor="mm")
save("foundation", shadowed(img))

# ---------------------------------------------------------------- 100 %
img = Image.new("RGBA", (760, 430), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((20, 10, 740, 320), radius=34, fill=(24, 12, 10, 205))
d.text((380, 150), "100%", font=font("sg700", 196), fill=GOLD, anchor="mm")
tracked(d, (380, 280), "SELF-GUIDED", font("sg500", 34), CREAM, tracking=9, anchor="mm")
# chip
d.rounded_rectangle((196, 336, 564, 420), radius=42, fill=(*TERRA, 235))
d.text((380, 378), "ZERO HASSLE", font=font("sg700", 36), fill=(255, 244, 226), anchor="mm")
save("hundred", shadowed(img))

# ---------------------------------------------------------------- split
img = Image.new("RGBA", (900, 340), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, 899, 339), radius=32, fill=(24, 12, 10, 200))
d.text((450, 92), "LESS STRESS", font=font("sg700", 68), fill=CREAM, anchor="mm")
d.line((160, 158, 740, 158), fill=(245, 194, 107, 130), width=3)
d.text((450, 246), "MORE SAVINGS", font=font("sg700", 68), fill=GOLD, anchor="mm")
save("split", shadowed(img))

# ---------------------------------------------------------------- CTA
img = Image.new("RGBA", (900, 210), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((0, 0, 899, 209), radius=105, fill=(*GOLD, 255))
d.text((450, 78), "rockwoodmethod.com/shop", font=font("sg700", 50), fill=ESPRESSO, anchor="mm")
d.text((450, 148), "link in bio", font=font("in600", 30), fill=(74, 40, 24), anchor="mm")
save("cta", shadowed(img, radius=20, alpha=150, offset=(0, 12)))

# ---------------------------------------------------------------- carte finale
ec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ec)
d.rectangle((0, 0, W, H), fill=(20, 10, 9, 232))
d.line((190, 700, 890, 700), fill=(245, 194, 107, 150), width=3)
tracked(d, (540, 596), "NO HAND-HOLDING NEEDED", font("sg500", 30), GOLD, tracking=8, anchor="mm")
d.text((540, 790), "THE ROCKWOOD", font=font("sg700", 82), fill=CREAM, anchor="mm")
d.text((540, 880), "METHOD", font=font("sg700", 82), fill=GOLD, anchor="mm")
d.line((190, 962, 890, 962), fill=(245, 194, 107, 150), width=3)
f_a = font("isr", 56)
d.text((540, 1040), "self-guided. downloadable. yours.", font=f_a, fill=(232, 214, 194), anchor="mm")
d.rounded_rectangle((190, 1120, 890, 1246), radius=63, fill=(*GOLD, 255))
d.text((540, 1183), "rockwoodmethod.com/shop", font=font("sg700", 46), fill=ESPRESSO, anchor="mm")
tracked(d, (540, 1330), "BUILD YOUR FOUNDATION", font("sg400", 26), (196, 172, 150), tracking=6, anchor="mm")
save("endcard", ec)

print("\nAssets OK ->", A)
json.dump(MANIFEST, open(os.path.join(A, "manifest.json"), "w"), indent=1)
