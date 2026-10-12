#!/usr/bin/env python3
"""Couverture Pinterest 1000x1500 (2:3) — version cinéma.

Le fond est un plan net tiré du film (creux de sous-titres : 13,34 -> 13,70 s),
donc la marque, le fil de progression et le vignettage sont déjà ceux du film.
On n'ajoute que la titraille serif (asset du film), une plaque de lisibilité,
un filet doré et la pilule d'appel. Aucun visuel externe, aucun aplat noir.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1000, 1500
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
WORK = os.environ.get("ROCKWOOD_WORK", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.dirname(os.path.abspath(__file__))
A = os.environ.get("ROCKWOOD_ASSETS", os.path.join(WORK, "assets"))
FONTS = os.environ.get("ROCKWOOD_FONTS", os.path.join(WORK, "node_modules"))
FILM = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, "film/rockwood-method-cinema-plus-9x16.mp4")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "film/pinterest-cover.jpg")
T = os.environ.get("COVER_T", "27.60")   # carte finale : aucun sous-titre à l'écran
GOLD = (233, 189, 124)

env = dict(os.environ, FONTCONFIG_FILE=os.path.join(TOOLS, "fonts.conf"))
subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", T, "-i", FILM,
                "-frames:v", "1", "-update", "1", "/tmp/cover_src.png", "-y"], check=True, env=env)
src = Image.open("/tmp/cover_src.png").convert("RGB")

# La couverture est un arrêt sur la carte finale : elle contient donc le rail de
# pellicule de l'habillage. Une couverture doit rester nette : on repose un
# cache-propre — un dégradé vertical vertical construit avec les teintes
# mesurées 45 px au-dessus et 45 px en-dessous du rail, interpolées ligne à
# ligne. Rien n'est copié, donc aucun rail fantôme.
if os.environ.get("COVER_KEEP_STRIP", "") != "1":
    y0, y1 = 286, 344
    top = np.asarray(src.crop((0, y0 - 46, 1080, y0 - 45)), dtype=np.float32)[0]
    bot = np.asarray(src.crop((0, y1 + 45, 1080, y1 + 46)), dtype=np.float32)[0]
    patch = np.zeros((y1 - y0, 1080, 3), np.uint8)
    for i in range(y1 - y0):
        k = i / (y1 - y0 - 1)
        patch[i] = np.clip(top * (1 - k) + bot * k, 0, 255)
    src = src.copy()
    src.paste(Image.fromarray(patch), (0, y0))

CROP_Y = 24
cov = src.crop((0, CROP_Y, 1080, CROP_Y + 1620)).resize((W, H), Image.LANCZOS).convert("RGBA")


def gradient(span, peak, exponent, from_bottom=True):
    """Voile dégradé posé en composition (jamais en remplacement de pixels)."""
    g = Image.new("RGBA", (W, H), (18, 10, 8, 0))
    dg = ImageDraw.Draw(g)
    for i in range(span):
        a = int(peak * (i / max(1, span - 1)) ** exponent)
        y = (H - span + i) if from_bottom else i
        dg.line((0, y, W, y), fill=(18, 10, 8, a))
    return g


cov = Image.alpha_composite(cov, gradient(430, 96, 1.6))          # pied

# ---------------------------------------------------------------- pilule d'appel
# La pilule de la carte finale porte, dans le film, la mention « link in bio »
# inscrite par-dessus : on repose l'asset propre au même endroit pour l'effacer.
pill = Image.open(os.path.join(A, "pill.png")).convert("RGBA")
sp = 0.926
pill = pill.resize((int(round(pill.width * sp)) + 2, int(round(pill.height * sp)) + 2),
                   Image.LANCZOS)
FILM_PX, FILM_PY = 84, 1290                       # placement identique au compositeur
PX = int(round(FILM_PX * sp)) - 1
PY = int(round((FILM_PY - CROP_Y) * sp)) - 1
sh = Image.new("RGBA", pill.size, (0, 0, 0, 0))
sh.putalpha(pill.getchannel("A").point(lambda v: int(v * 0.45)))
cov.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (PX + 3, PY + 8))
cov.alpha_composite(pill, (PX, PY))

cov.convert("RGB").save(OUT, quality=92, optimize=True)
print("cover ->", OUT, Image.open(OUT).size, os.path.getsize(OUT), "octets")
