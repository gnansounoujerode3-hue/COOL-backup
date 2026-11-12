#!/usr/bin/env python3
"""Digitaward — Pack 1 500 modèles PowerPoint · pub Facebook 9:16 · v4.

La v3 tenait le rythme (21 coupes, 1,78 de mouvement) mais son décor était **synthétisé** :
dégradé calculé, bulles de poussière, faisceau en polygone. C'est ce qui trahit le plus
une vidéo générée — pas le mouvement, le fond.

La v4 garde tout le découpage et les compositions de la v3, et remplace le décor par un
**plate photographique** (studio réel : faisceau, brume, hauteur de sol, liseré chaud),
étalonné aux bleus de la marque, avec :

  - **parallaxe** : le plateau glisse moins vite que le sujet (0,35×) et le halo plus encore ;
  - **profondeur de champ** : flou de plateau qui respire ;
  - **lumière réelle** qui traverse les plans, au lieu d'un blob calculé.

    python3 build_film_v4.py --preview /tmp/preview-v4.jpg
    python3 build_film_v4.py
"""
import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_film_v3 as v3  # noqa: E402
import build_film_v2 as v2  # noqa: E402
from build_film import (  # noqa: E402
    W, H, FPS, TOTAL, AUD, FILM, IMG, YELLOW,
    F, c_, clamp01, prog, eob,
)

OUT4 = os.path.join(FILM, "digitaward-pack-1500-powerpoint-fb-9x16-v4.mp4")
MIX4 = os.path.join(AUD, "master_mix_v4.wav")
PLATE = os.path.join(IMG, "plate_studio.jpg")

_SHOTS = v3.SHOTS
_SCENE_FN = v3.SCENE_FN


# ---------------------------------------------------------------- plateau
def _load_plate():
    """Plate 1080x1920 étalonné : structure photo conservée, couleur de marque."""
    im = Image.open(PLATE).convert("RGB")
    # recadrage couvrant : la ligne de sol doit tomber vers 74 % de la hauteur
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    left = (im.width - W) // 2
    top = int(im.height * 0.60) - int(H * 0.72)
    top = max(0, min(top, im.height - H))
    im = im.crop((left, top, left + W, top + H))

    a = np.asarray(im).astype(np.float32) / 255

    # 1. désaturation partielle : on garde la texture, pas la teinte teal
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    a = a * 0.55 + lum[..., None] * 0.45

    # 2. remise en couleur : bleu royal en bas, navy en haut
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    grad = np.zeros((H, W, 3), np.float32)
    for ch, (top_c, bot_c) in enumerate([((0, 16, 92), (0, 40, 176)),
                                        ((0, 30, 132), (0, 66, 232)),
                                        ((4, 58, 190), (0, 48, 196))]):
        grad[..., ch] = top_c[ch] + (bot_c[ch] - top_c[ch]) * (1 - yy[..., 0])
    a = a * 0.30 + (grad / 255) * 0.70

    # 3. le faisceau photo redevient la source de lumière : on l'utilise en écran
    beam = np.clip((lum - 0.16) / 0.6, 0, 1)[..., None]
    a = a + beam * np.array([0.24, 0.40, 0.70], np.float32) * 0.42

    # 4. contraste en S doux + léger lift
    a = np.clip((a - 0.5) * 1.10 + 0.5 + 0.030, 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8)).convert("RGB")

    # 5. le reflet du caisson sur le plateau a des bords rectilignes : une fois
    #    étalonné, il se lit comme un rectangle collé. On le fond localement dans
    #    la brume (flou masqué) puis on réinjecte le liseré spéculaire, seule
    #    structure nette qu'on veut garder.
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle([int(W * .24), int(H * .515),
                                    int(W * .83), int(H * .747)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(95))
    sharp = out
    blurred = out.filter(ImageFilter.GaussianBlur(42))
    out = Image.composite(blurred, sharp, mask)

    lum = np.asarray(sharp.convert("L")).astype(np.float32) / 255
    yy = np.arange(H)[:, None]
    line = (lum > .58) & (yy > H * .625) & (yy < H * .79)
    line_img = Image.fromarray((line * 255).astype(np.uint8))
    line_img = line_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.0))
    line_img = Image.composite(line_img, Image.new("L", (W, H), 0), mask)
    out = Image.composite(sharp, out, line_img)  # le liseré reste net
    return out.convert("RGBA")


_PLATE = None
_SOFT = None
_FAR = None


def plate():
    global _PLATE
    if _PLATE is None:
        _PLATE = _load_plate()
    return _PLATE


def plate_soft():
    """Version légèrement défocalisée : profondeur de champ."""
    global _SOFT
    if _SOFT is None:
        _SOFT = plate().filter(ImageFilter.GaussianBlur(7))
    return _SOFT


def stage_frame(t, flare=0.0):
    """Plateau avec parallaxe : le fond glisse lentement, le sujet plus vite."""
    base = plate().copy()
    # respiration : la profondeur de champ oscille très lentement
    k = 0.5 + 0.5 * math.sin(t * 0.55)
    soft = plate_soft()
    base = Image.blend(base, soft, 0.18 + 0.22 * k)

    # halo de projecteur qui dérive (2ᵉ plan, moins vite que le sujet)
    beam = Image.new("RGBA", (1500, 2400), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    dx = math.sin(t * 0.21) * 90
    bd.polygon([(900 + dx, -200), (1500 + dx, -200), (640 + dx, 2400), (-140 + dx, 2400)],
               fill=(150, 200, 255, 26))
    base.alpha_composite(beam.filter(ImageFilter.GaussianBlur(140)), (-210, -240))

    # poussière dans le faisceau, uniquement là où la lumière passe
    d = ImageDraw.Draw(base)
    for x0, y0, r, sp, ph, a in v2.dust():
        y = (y0 - t * sp * .55) % H
        x = (x0 + math.sin(t * .35 + ph) * 26) % W
        if 120 < x < 980:
            d.ellipse([x, y, x + r, y + r], fill=(200, 222, 255, int(a * .8)))

    # sol : la ligne du plateau photo est déjà là, on l'accentue à peine
    if flare > 0:
        v2.glow_blob(base, W * .5, H * .46, 420, (255, 236, 170), int(90 * flare), 150)
    return base


def camera(img, zoom=1.0, dx=0.0, dy=0.0, t=0.0, handheld=1.0):
    v2.camera.__globals__  # touch
    sx = (3.2 * math.sin(t * 1.63) + 1.6 * math.sin(t * 3.71)) * handheld
    sy = (2.6 * math.cos(t * 1.27) + 1.2 * math.sin(t * 4.31)) * handheld
    a = 1.0 / zoom
    cx, cy = W / 2, H / 2
    return img.transform((W, H), Image.AFFINE,
                         (a, 0, cx - a * cx - dx - sx,
                          0, a, cy - a * cy - dy - sy),
                         resample=Image.BICUBIC)


def _shot_at(t):
    return v3._shot_at(t)


def render_frame(fi):
    t = fi / FPS
    i, name, lt, dur = _shot_at(t)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _SCENE_FN[name](layer, lt, dur)

    z = v2.FRAMING.get(name, 1.0)
    if z:
        sx_, sy_ = v2.FRAMING_SHIFT.get(name, (0, 0))
        layer = layer.transform((W, H), Image.AFFINE,
                                (1 / z, 0, W / 2 - W / (2 * z) - sx_,
                                 0, 1 / z, H / 2 - H / (2 * z) - sy_),
                                resample=Image.BICUBIC)

    base = stage_frame(t, flare=(1.0 if name == "burst" else 0.0))
    base = v3.beat_light(base, t)

    # parallaxe : le sujet se déplace ~3× plus que le plateau
    px = math.sin(t * .37) * 16
    py = math.cos(t * .29) * 10
    if abs(px) > .5 or abs(py) > .5:
        layer = layer.transform((W, H), Image.AFFINE,
                                (1, 0, -px, 0, 1, -py), resample=Image.BICUBIC)
    base.alpha_composite(layer)

    p = clamp01(lt / max(dur, 1e-4))
    zoom = 1.045 + .050 * p
    if name == "pack_hero":
        zoom = 1.16 - .13 * eob(prog(lt, 0, .6))
    if name == "open_macro":
        zoom = 1.10 - .06 * p
    if name == "benefit":
        zoom = 1.02 + .06 * p
    if name == "claim":
        zoom = 1.06 - .04 * p

    img = camera(base, zoom, 0, 0, t)
    m = v3.cut_motion(t)
    if m:
        img = v3.smear(img, abs(m), 1 if m > 0 else -1)
    img = v2.finish(img, t)
    return img.convert("RGB")


def preview(path):
    cols, rows = 4, 4
    tw, th = 336, 597
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (8, 10, 26))
    sd = ImageDraw.Draw(sheet)
    picks = [((a + b) / 2, n) for n, a, b in _SHOTS if n != "end"][:cols * rows]
    for k, (t, n) in enumerate(picks):
        im = render_frame(int(t * FPS)).resize((tw, th), Image.LANCZOS)
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)
        sheet.paste(im, (x, y))
        sd.rectangle([x, y, x + 132, y + 22], fill=(0, 0, 0))
        sd.text((x + 4, y + 4), f"{t:05.2f}s {n}", font=F("sb", 15), fill=(255, 255, 255))
    sheet.save(path, quality=90)
    print("Saved preview:", path)


def build_audio():
    v2.MIX2 = MIX4
    v2.AUDIO_CUTS = v3.AUDIO_CUTS
    return v2.build_audio_v2()


def render():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    nf = int(round(TOTAL * FPS))
    tmp = "/tmp/dw_v4_video.mp4"
    p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
                         stdin=subprocess.PIPE)
    for fi in range(nf):
        p.stdin.write(render_frame(fi).tobytes())
        if fi % 200 == 0:
            print(f"  {fi}/{nf} ({fi / nf * 100:.0f}%)", flush=True)
    p.stdin.close()
    p.wait()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", tmp, "-i", MIX4,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-pix_fmt", "yuv420p",
                    "-af", "volume=-1.4dB,alimiter=limit=0.82:level=disabled",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", OUT4], check=True)
    print("Rendered", OUT4, f"({os.path.getsize(OUT4) / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--frame", type=int)
    a = ap.parse_args()
    if a.frame is not None:
        render_frame(a.frame).save(f"/tmp/dw_v4_f{a.frame}.jpg", quality=92)
        print("frame", a.frame)
        return
    if a.preview:
        preview(a.preview)
        return
    print("Voix off + musique ...")
    build_audio()
    if a.audio_only:
        print("Audio ->", MIX4)
        return
    render()


if __name__ == "__main__":
    main()
