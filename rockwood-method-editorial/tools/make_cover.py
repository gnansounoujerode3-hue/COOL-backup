#!/usr/bin/env python3
"""Couverture Pinterest (1000x1500) : image étalonnée + système typographique éditorial."""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
WORK = "/home/user/work2"
NM = f"{WORK}/node_modules/@expo-google-fonts"
W, H = 1000, 1500
CREAM = (253, 247, 236)
GOLD = (233, 189, 124)
INK = (23, 13, 10)

# --- image de base : même étalonnage que le film
src = os.path.join(WORK, "AIDE-CHATGPT-main/video brut.mp4")
subprocess.run([
    FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", "7.60", "-i", src,
    "-frames:v", "1", "-update", "1",
    "-vf", ("scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:3:3:0.0,"
            "eq=contrast=1.055:brightness=0.006:saturation=1.05:gamma=0.985,"
            "curves=master='0/0 0.22/0.20 0.5/0.52 0.78/0.81 1/1',"
            "colorbalance=rs=-0.012:gs=-0.006:bs=0.018:rm=0.010:gm=0.005:bm=-0.012:"
            "rh=0.028:gh=0.013:bh=-0.026"),
    "/tmp/cover_base.png"], check=True)

base = Image.open("/tmp/cover_base.png").convert("RGB")
# recadrage 2:3 centré sur le sujet (visage vers le haut du cadre)
tw, th = 1000, 1500
sw, sh = base.size
scale = max(tw / sw, th / sh)
rz = base.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
px = (rz.width - tw) // 2
py = int((rz.height - th) * 0.30)
poster = rz.crop((px, py, px + tw, py + th)).convert("RGBA")

# vignettage
vig = Image.new("L", (tw, th), 0)
dv = ImageDraw.Draw(vig)
for i in range(60, 0, -1):
    t = i / 60
    dv.ellipse((-tw * 0.35 * t, -th * 0.25 * t, tw + tw * 0.35 * t, th + th * 0.25 * t),
               fill=int(255 * (1 - t) ** 1.5 * 0.55))
poster = Image.composite(Image.new("RGBA", (tw, th), (14, 8, 6, 255)), poster,
                         vig.filter(ImageFilter.GaussianBlur(80)))

# dégradés haut / bas
ov = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
dov = ImageDraw.Draw(ov)
for y in range(560):
    dov.line((0, y, tw, y), fill=(17, 9, 7, int(150 * (1 - y / 560) ** 1.5)))
for y in range(700):
    a = int(226 * (y / 700) ** 1.35)
    dov.line((0, th - 700 + y, tw, th - 700 + y), fill=(17, 9, 7, a))
poster = Image.alpha_composite(poster, ov)

# --- typographie
d = ImageDraw.Draw(poster)
M = 74


def font(k, s):
    return ImageFont.truetype(f"{NM}/{k}", s)


def track(xy, s, f, fill, tr=0, anchor="la"):
    x = xy[0]
    if anchor[0] == "m":
        x -= sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)
        x += (sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)) / 2
        x -= (sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)) / 2
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=f) + tr


track((M, 92), "SELF-GUIDED FILM", font("space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf", 25),
      (233, 189, 124, 235), tr=8)
d.line((M, 146, W - M, 146), fill=(253, 247, 236, 70), width=2)

# bloc titre bas
d.text((M, 940), "A rock-solid", font=font("instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf", 92), fill=CREAM)
d.text((M, 1032), "financial foundation.", font=font("instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf", 92), fill=CREAM)
d.line((M, 1170, W - M, 1170), fill=(233, 189, 124, 200), width=3)
d.text((M, 1204), "The Rockwood Method — self-guided, downloadable.",
       font=font("inter/300Light/Inter_300Light.ttf", 30), fill=(238, 226, 208))
d.rounded_rectangle((M, 1276, W - M, 1276 + 116), radius=58, fill=(233, 189, 124, 255))
d.text((W / 2, 1276 + 58), "rockwoodmethod.com/shop",
       font=font("space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf", 40), fill=INK, anchor="mm")

track((M, H - 52), "BUILD YOUR FOUNDATION", font("space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf", 22),
      (233, 189, 124, 210), tr=8)

poster.convert("RGB").save("/tmp/pinterest-cover.jpg", quality=94)
print("couverture Pinterest 1000x1500 générée")
