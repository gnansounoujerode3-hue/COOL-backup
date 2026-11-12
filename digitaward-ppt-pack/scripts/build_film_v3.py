#!/usr/bin/env python3
"""Digitaward — Pack 1 500 modèles PowerPoint · publicité Facebook 9:16 · v3.

Troisième passe, toujours pilotée par les skills (`motionmaxxing`, `business-motion-film`).

Ce que la v3 corrige par rapport à la v2, mesuré par `look.py` :

  1. **La phrase clé n'avait aucun plan.** « Moins de temps à concevoir. Plus de temps
     pour convaincre. » était dite par la voix off par-dessus des diapositives. Elle a
     maintenant son plan, en typographie cinétique calée sur le rythme de la voix.
  2. **Le mouvement restait sous la bande humaine.** Ajout d'une respiration de lumière
     sur chaque temps (122 BPM), d'un balayage de barre, et de vrais flous de
     déménagement (whip) de 7 images à chaque coupe structurante.
  3. **Deux plans redundants supprimés** (projection murale, pack qui se referme) pour
     laisser la place au plan « bénéfice » et à la minuterie qui rembobine.

    python3 build_film_v3.py --preview /tmp/preview-v3.jpg
    python3 build_film_v3.py --audio-only
    python3 build_film_v3.py
"""
import argparse
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_film_v2 as v2  # noqa: E402
from build_film import (  # noqa: E402
    W, H, FPS, SR, AUD, FILM, TOTAL, VO, YELLOW, WHITE, ICE, NAVY,
    F, tl, tracked, c_, clamp01, prog, eo, eob,
)

OUT3 = os.path.join(FILM, "digitaward-pack-1500-powerpoint-fb-9x16-v3.mp4")
MIX3 = os.path.join(AUD, "master_mix_v3.wav")

BPM = 122.0
BEAT = 60.0 / BPM

# (nom, début, fin) — 28 plans
SHOTS = [
    ("open_macro",  0.00,  1.55),
    ("room",        1.55,  3.10),
    ("timelapse",   3.10,  4.70),
    ("draft",       4.70,  6.60),
    ("picker",      6.60,  7.90),
    ("fonts",       7.90,  9.20),
    ("image",       9.20, 10.60),
    ("mess",       10.60, 12.80),
    ("power_on",   12.80, 14.50),
    ("pack_rise",  14.50, 16.10),
    ("pack_macro", 16.10, 17.60),
    ("pack_hero",  17.60, 19.30),
    ("pack_open",  19.30, 21.20),
    ("fan_track",  21.20, 22.70),
    ("use_cases",  22.70, 24.80),
    ("slide_a",    24.80, 26.40),
    ("slide_b",    26.40, 27.90),
    ("slide_c",    27.90, 29.40),
    ("slide_d",    29.40, 30.80),
    ("benefit",    30.80, 33.90),
    ("rewind",     33.90, 35.60),
    ("claim",      35.60, 37.10),
    ("stamp",      37.10, 38.80),
    ("proof_macro",38.80, 39.60),
    ("cta_press",  39.60, 40.80),
    ("burst",      40.80, 41.60),
    ("brand",      41.60, 43.80),
    ("end",        43.80, 45.20),
]

AUDIO_CUTS = [1.55, 4.70, 6.60, 10.60, 12.80, 14.50, 17.60, 19.30,
              22.70, 24.80, 30.80, 33.90, 35.60, 37.10, 39.60, 41.60]

HEAVY_CUTS = {6.60, 12.80, 17.60, 24.80, 30.80, 35.60, 41.60}


# ------------------------------------------------------------ typographie cinétique
def s_benefit(layer, lt, dur):
    """Le bénéfice, mot à mot, sur le rythme de la voix (122 BPM ≈ 0,49 s)."""
    lines = [("Moins de temps", WHITE, 0.15),
             ("à concevoir.", WHITE, 0.62),
             ("Plus de temps", YELLOW, 1.10),
             ("pour convaincre.", YELLOW, 1.58)]
    y = 640
    for txt, col, start in lines:
        p = prog(lt, start, .62)
        if p <= 0:
            continue
        f = F("xb", 84)
        v2.words(layer, txt, f, c_(col, 255), 76, y, p, stagger=.055, rise=56)
        y += 126

    # le trait jaune se dessine sous la dernière ligne, puis respire
    q = eob(prog(lt, 2.05, .45))
    if q > 0:
        d = ImageDraw.Draw(layer)
        x0, x1 = 80, 80 + int(560 * q)
        d.line([(x0, 1160), (x1, 1160)], fill=c_(YELLOW, 225), width=5)

    # le pack arrive en bas, petit, comme la conclusion de la phrase
    a = eob(prog(lt, 2.15, .7))
    if a > 0:
        box = v2.load("box.png")
        bw = 300
        bh = int(box.height * bw / box.width)
        v2.glow_blob(layer, W / 2, 1620, 250, (120, 180, 255), 60, 110)
        v2.place(layer, v2.alpha(box.resize((bw, bh), Image.LANCZOS), a),
                 (W - bw) / 2, 1400 + (1 - a) * 34, r=8, blur=30, sa=150, dy=24)


SCENE_FN = {}
for n, _, _ in SHOTS:
    SCENE_FN[n] = s_benefit if n == "benefit" else getattr(v2, "s_" + n)


# ------------------------------------------------------------ caméra / texture
def beat_light(img, t):
    """Respiration de lumière sur chaque temps : le plan ne gèle jamais."""
    ph = (t % BEAT) / BEAT
    pulse = math.exp(-ph * 5.5)
    if pulse > .02:
        img.alpha_composite(Image.new("RGBA", (W, H),
                                      (198, 224, 255, int(10 * pulse))))
    # balayage de barre : une nappe qui traverse le cadre sur deux temps
    bar = (t % (BEAT * 4)) / (BEAT * 4)
    if bar < .55:
        u = bar / .55
        x = -600 + u * (W + 1200)
        band = Image.new("RGBA", (900, H), (0, 0, 0, 0))
        ImageDraw.Draw(band).polygon([(0, 0), (300, 0), (900, H), (600, H)],
                                     fill=(180, 210, 255, 12))
        band = band.filter(ImageFilter.GaussianBlur(90))
        v2.ac(img, band, (int(x), 0))
    return img


def smear(img, amt, direction):
    """Flou directionnel de déménagement : le cadre est encore en train de bouger."""
    if amt <= 0.01:
        return img
    out = img
    for off, a in ((30, .55), (66, .34), (110, .18)):
        shifted = img.transform((W, H), Image.AFFINE,
                                (1, 0, -direction * off * amt, 0, 1, 0),
                                resample=Image.BILINEAR)
        out = Image.blend(out, shifted, a * amt)
    return out


def cut_motion(t):
    """Amplitude du flou de coupe à l'instant t, et sa direction."""
    for i, c in enumerate(sorted(HEAVY_CUTS)):
        d = abs(t - c)
        if d < .13:
            w = 1.0 - d / .13
            return w * (1.0 if i % 2 == 0 else -1.0)
    return 0.0


def render_frame(fi):
    t = fi / FPS
    i, name, lt, dur = v2.shot_at(t) if False else _shot_at(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    SCENE_FN[name](layer, lt, dur)

    z = v2.FRAMING.get(name, 1.0)
    if z:
        sx_, sy_ = v2.FRAMING_SHIFT.get(name, (0, 0))
        layer = layer.transform((W, H), Image.AFFINE,
                                (1 / z, 0, W / 2 - W / (2 * z) - sx_,
                                 0, 1 / z, H / 2 - H / (2 * z) - sy_),
                                resample=Image.BICUBIC)

    base = v2.stage_frame(t, flare=(1.0 if name == "burst" else 0.0))
    base = beat_light(base, t)
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

    img = v2.camera(base, zoom, 0, 0, t)
    m = cut_motion(t)
    if m:
        img = smear(img, abs(m), 1 if m > 0 else -1)
    img = v2.finish(img, t)
    return img.convert("RGB")


def _shot_at(t):
    for i, (n, a, b) in enumerate(SHOTS):
        if a <= t < b:
            return i, n, t - a, b - a
    return len(SHOTS) - 1, SHOTS[-1][0], t - SHOTS[-1][1], SHOTS[-1][2] - SHOTS[-1][1]


def preview(path):
    cols, rows = 4, 4
    tw, th = 336, 597
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (8, 10, 26))
    sd = ImageDraw.Draw(sheet)
    picks = [((a + b) / 2, n) for n, a, b in SHOTS]
    picks = [p for p in picks if p[1] != "end"][:cols * rows]
    for k, (t, n) in enumerate(picks):
        im = render_frame(int(t * FPS)).resize((tw, th), Image.LANCZOS)
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)
        sheet.paste(im, (x, y))
        sd.rectangle([x, y, x + 132, y + 22], fill=(0, 0, 0))
        sd.text((x + 4, y + 4), f"{t:05.2f}s {n}", font=F("sb", 15), fill=(255, 255, 255))
    sheet.save(path, quality=90)
    print("Saved preview:", path)


# ------------------------------------------------------------ audio / rendu
def build_audio():
    v2.AUDIO_CUTS = AUDIO_CUTS
    v2.MIX2 = MIX3
    return v2.build_audio_v2()


def render():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    nf = int(round(TOTAL * FPS))
    tmp = "/tmp/dw_v3_video.mp4"
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
    # livraison : réencodage unique, 1080p, audio normalisé sous -2 dBTP
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", tmp, "-i", MIX3,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-pix_fmt", "yuv420p",
                    "-af", "volume=-1.4dB,alimiter=limit=0.82:level=disabled",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", OUT3], check=True)
    print("Rendered", OUT3, f"({os.path.getsize(OUT3) / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--frame", type=int)
    a = ap.parse_args()
    if a.frame is not None:
        render_frame(a.frame).save(f"/tmp/dw_v3_f{a.frame}.jpg", quality=92)
        print("frame", a.frame)
        return
    if a.preview:
        preview(a.preview)
        return
    print("Voix off + musique ...")
    build_audio()
    if a.audio_only:
        print("Audio ->", MIX3)
        return
    render()


if __name__ == "__main__":
    main()
