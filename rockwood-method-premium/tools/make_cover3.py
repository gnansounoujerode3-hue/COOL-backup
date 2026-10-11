#!/usr/bin/env python3
"""Couverture Pinterest 1000×1500 avec le grade v3 (halation comprise)."""
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
WORK = "/home/user/w3"
A = os.path.join(WORK, "tools3/assets3")
NM = f"{WORK}/node_modules/@expo-google-fonts"
W, H = 1000, 1500
CREAM = (253, 247, 236)
GOLD = (233, 189, 124)
INK = (20, 11, 9)

GRADE = ("scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:3:3:0.0,"
         "eq=contrast=1.075:brightness=0.004:saturation=1.04:gamma=0.98,"
         "curves=master='0/0 0.18/0.155 0.5/0.52 0.8/0.84 1/1',"
         "colorbalance=rs=-0.016:gs=-0.008:bs=0.024:rm=0.012:gm=0.005:bm=-0.014:"
         "rh=0.034:gh=0.016:bh=-0.030,vignette=angle=PI/4.8:mode=forward")

subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-ss", "7.60",
                "-i", f"{WORK}/AIDE-CHATGPT-main/video brut.mp4", "-frames:v", "1",
                "-update", "1", "-vf", GRADE, "/tmp/c3.png"], check=True)

base = Image.open("/tmp/c3.png").convert("RGB")


def halation(im):
    a = np.asarray(im, dtype=np.float32)
    luma = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    hi = np.clip((luma - 188.0) / 67.0, 0, 1)
    small = Image.fromarray((hi * 255).astype(np.uint8)).resize((a.shape[1] // 4, a.shape[0] // 4),
                                                                Image.BILINEAR)
    bloom = small.filter(ImageFilter.GaussianBlur(22)).resize((a.shape[1], a.shape[0]),
                                                              Image.BILINEAR)
    b = np.asarray(bloom, dtype=np.float32) / 255.0
    tint = np.array([1.0, 0.62, 0.36], dtype=np.float32)
    a2 = 255.0 - (255.0 - a) * (1.0 - 0.30 * b[..., None])
    a2 = a2 + (b * 46.0)[..., None] * tint
    return Image.fromarray(np.clip(a2, 0, 255).astype(np.uint8))


base = halation(base)

# grain film
rng = np.random.default_rng(9)
g = np.clip(rng.standard_normal(base.size[1] * base.size[0]).reshape(base.size[1], base.size[0]),
            -2.6, 2.6) / 2.6
g = np.asarray(Image.fromarray(((g + 1) * 127.5).astype(np.uint8)).resize(base.size, Image.BILINEAR),
               dtype=np.float32)
base = Image.fromarray(np.clip(np.asarray(base, dtype=np.float32) + (g[..., None] - 127.5) / 127.5 * 5.0,
                               0, 255).astype(np.uint8))

# recadrage 2:3
sw, sh = base.size
scale = max(W / sw, H / sh)
rz = base.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
px = (rz.width - W) // 2
py = int((rz.height - H) * 0.30)
poster = rz.crop((px, py, px + W, py + H)).convert("RGBA")

# dégradés haut / bas
ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
for y in range(520):
    d.line((0, y, W, y), fill=(17, 9, 7, int(146 * (1 - y / 520) ** 1.5)))
for y in range(720):
    d.line((0, H - 720 + y, W, H - 720 + y), fill=(17, 9, 7, int(230 * (y / 720) ** 1.35)))
poster = Image.alpha_composite(poster, ov)


def font(path, size):
    return ImageFont.truetype(f"{NM}/{path}", size)


def track(xy, s, f, fill, tr, anchor="la"):
    x = xy[0]
    if anchor[0] == "r":
        x -= sum(d.textlength(c, font=f) for c in s) + tr * (len(s) - 1)
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(c, font=f) + tr


d = ImageDraw.Draw(poster)
M = 74

track((M, 88), "SELF-GUIDED FILM", font("space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf", 24),
      GOLD + (235,), 8)
d.line((M, 142, W - M, 142), fill=(253, 247, 236, 66), width=2)

f_serif = font("instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf", 96)
d.text((M, 900), "A rock-solid", font=f_serif, fill=CREAM)
d.text((M, 1000), "financial foundation.", font=f_serif, fill=CREAM)
d.line((M, 1146, W - M, 1146), fill=GOLD + (215,), width=3)
d.text((M, 1180), "The Rockwood Method — self-guided, downloadable.",
       font=font("inter/300Light/Inter_300Light.ttf", 29), fill=(238, 226, 208))
d.rounded_rectangle((M, 1256, W - M, 1256 + 114), radius=57, fill=GOLD + (255,))
d.text((W / 2, 1256 + 57), "rockwoodmethod.com/shop",
       font=font("space-grotesk/500Medium/SpaceGrotesk_500Medium.ttf", 40), fill=INK, anchor="mm")

track((M, H - 54), "BUILD YOUR FOUNDATION",
      font("space-grotesk/400Regular/SpaceGrotesk_400Regular.ttf", 22), GOLD + (215,), 8)

poster.convert("RGB").save(f"{WORK}/out3/pinterest-cover.jpg", quality=95)
print("couverture Pinterest v3 générée")
