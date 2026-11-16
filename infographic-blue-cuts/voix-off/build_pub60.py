#!/usr/bin/env python3
"""Pub 60 s — Infographic Blue / 1 500 modèles PowerPoint, 7 000 FCFA.

La vidéo d'origine fait 4 min 26. Ici on n'en garde que **8 extraits**, remontés en
60 s, avec pour chaque plan :

  - un recadrage serré sur le graphique (le template respire au lieu de flotter
    dans du blanc), un zoom qui ne s'arrête jamais et change de sens à chaque plan ;
  - une accélération de 1,25× : on traverse le mouvement au lieu de le subir ;
  - une plaque-titre diagonale (navy / jaune) qui entre en 9 images, du côté
    opposé au graphique ;
  - un flash de 2 images sur les coupes fortes.

Audio : voix off réécrite pour 60 s, musique instrumentale générée à 132 BPM,
ducking de −8 dB sous la voix, whooshs sur chaque coupe, impacts sur les cartes
fortes, cloche sur l'offre. Master −14 LUFS / −1,5 dBTP.

    python3 infographic-blue-cuts/voix-off/build_pub60.py --preview
    python3 infographic-blue-cuts/voix-off/build_pub60.py
"""
import argparse
import math
import os
import subprocess
import sys
import wave as wavemod

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "imports", "Infographic_Blue__Light_1.mp4")
OUT = os.path.join(ROOT, "infographic-blue-cuts", "pub-60s-infographic-1500-pwp.mp4")
AUD = os.path.join(HERE, "pub60")
MIX = os.path.join(AUD, "pub60_mix.wav")

W, H, FPS = 852, 480, 30
SR = 48000
TOTAL = 60.0
SRC_FPS = 30.30
SPEED = 1.25                     # on accélère la source de 25 %

FF = "/tmp/bin/ffmpeg"
if not os.path.exists(FF):
    from imageio_ffmpeg import get_ffmpeg_exe
    FF = get_ffmpeg_exe()

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# tempo de la musique : 132 BPM -> un temps = 0,4545 s
BPM = 132.0
BEAT = 60 / BPM

# prise voix off (n°) -> début en secondes (mesuré sur les prises)
VO_TAKES = [
    (1, 0.80),
    (2, 6.90),
    (3, 14.40),
    (4, 18.20),
    (5, 23.80),
    (6, 32.60),
    (7, 41.00),
    (8, 53.20),
]

# (t_in source, libellé de la plaque, côté, force)
# Le plan démarre 1,25× plus loin dans la source que sa durée finale :
# il traverse donc plus de mouvement qu'un simple ralenti.
SHOTS = [
    (23.6, "1 500 modèles\nPowerPoint", "R", 2),
    (37.5, "déjà animés", "L", 1),
    (47.0, "15 styles", "R", 2),
    (63.5, "", "L", 1),
    (91.0, "100 % modifiables", "R", 2),
    (102.5, "fini les\n3 heures perdues", "L", 1),
    (137.0, "", "R", 1),
    (149.5, "chaque idée\nsa forme", "L", 2),
    (173.5, "", "R", 1),
    (204.5, "7 000 FCFA", "L", 2),
    (209.5, "", "R", 1),
    (208.5, "livraison\nsous 24 h", "R", 2),
    (225.0, "", "L", 1),
    (234.6, "", "R", 1),
]

NAVY, ROYAL = (10, 32, 92), (0, 84, 224)
YELLOW, ICE = (255, 194, 26), (232, 240, 255)


def _font(size):
    try:
        return ImageFont.truetype(FONT_BOLD, size)
    except Exception:
        return ImageFont.load_default()


# --------------------------------------------------------------- timeline
def vo_durations():
    out = {}
    for i in range(1, 9):
        p = os.path.join(AUD, f"seg{i:02d}.mp3")
        r = subprocess.run([FF, "-hide_banner", "-i", p], stderr=subprocess.PIPE, text=True)
        d = 0.0
        for line in r.stderr.splitlines():
            if "Duration:" in line:
                h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
                d = int(h) * 3600 + int(m) * 60 + float(s)
        out[i] = d
    return out


def timeline():
    """14 plans de 60/14 s : la coupe tombe toujours sur le même pas."""
    step = TOTAL / len(SHOTS)
    cuts = [round(i * step, 3) for i in range(len(SHOTS) + 1)]
    cuts[-1] = TOTAL
    dur = vo_durations()
    starts = {n: t for n, t in VO_TAKES}
    return cuts, dur, starts


# --------------------------------------------------------------- image
def iter_source(t_in, dur_src):
    """Décode [t_in, t_in+dur_src] et renvoie les frames une à une (flux)."""
    p = subprocess.Popen(
        [FF, "-v", "error", "-ss", f"{t_in:.3f}", "-t", f"{dur_src:.3f}", "-i", SRC,
         "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    fs = W * H * 3
    while True:
        buf = p.stdout.read(fs)
        if len(buf) < fs:
            break
        yield np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3)
    p.stdout.close()
    p.wait()



def subject_box(t_in, dur_src):
    """Boîte du graphique dans le plan (tout ce qui n'est pas le fond blanc)."""
    best = None
    for k, fr in enumerate(iter_source(t_in, min(dur_src, 1.2))):
        a = fr.astype(np.float32) / 255
        lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
        sat = a.max(axis=2) - a.min(axis=2)
        mask = (sat > 0.16) | ((lum < 0.55) & (sat > 0.04))
        ys, xs = np.where(mask)
        if xs.size < 400:
            if k > 18:
                break
            continue
        # on ignore les pixels isolés du fond
        x0, x1 = np.percentile(xs, 1), np.percentile(xs, 99)
        y0, y1 = np.percentile(ys, 1), np.percentile(ys, 99)
        box = (x0, y0, x1, y1, int(xs.size))
        if best is None or box[4] > best[4]:
            best = box
        if k > 20:
            break
    if best is None:
        return 0.5, 0.5, 1.12
    x0, y0, x1, y1, _ = best
    bw, bh = max(x1 - x0, 40), max(y1 - y0, 40)
    z = min(2.4, max(1.05, min(W / (bw / 0.80), H / (bh / 0.80))))
    return float((x0 + x1) / 2 / W), float((y0 + y1) / 2 / H), z

def crop_zoom(img, zoom, tx, ty):
    if zoom <= 1.0005:
        return img
    w, h = int(W / zoom), int(H / zoom)
    x0 = max(0, min(W - w, int(W * tx) - w // 2))
    y0 = max(0, min(H - h, int(H * ty) - h // 2))
    return img.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)


VIGNETTE = 1.0 - 0.20 * (((np.linspace(-1, 1, W)[None, :] ** 2) * 0.6 +
                          (np.linspace(-1, 1, H)[:, None] ** 2) * 0.4))


def punch(img, k):
    """Coup de zoom de 4 images à chaque coupe : l'œil sent la rupture."""
    if k >= 4:
        return img
    z = 1.0 + 0.07 * (1 - k / 4)
    return crop_zoom(img, z, 0.5, 0.5)


def card(label, side, t_in):
    """Plaque diagonale : entrée en glissé, ligne jaune sous le dernier mot."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = label.split("\n")
    size = 40 if max(len(l) for l in lines) <= 16 else 34
    f = _font(size)
    tw = max(d.textlength(l, font=f) for l in lines)
    lh = size * 1.12
    bw, bh = int(tw + 56), int(lh * len(lines) + 56)
    x = 22 if side == "R" else W - bw - 22
    y = 22 if side == "R" else H - bh - 22
    e = min(1.0, t_in / (9 / FPS))
    e = 1 - (1 - e) ** 3
    x += int((1 - e) * (-34 if side == "R" else 34))
    skew = 14
    poly = [(x + skew, y), (x + bw, y), (x + bw - skew, y + bh), (x, y + bh)]
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.polygon(poly, fill=NAVY + (240,))
    pd.line(poly + [poly[0]], fill=ROYAL + (255,), width=3)
    img.alpha_composite(plate.filter(ImageFilter.GaussianBlur(14)), (0, 10))
    img.alpha_composite(plate)
    for i, ln in enumerate(lines):
        fill = YELLOW if (i == len(lines) - 1 and len(lines) > 1) else ICE
        d.text((x + 30, y + 18 + i * lh), ln, font=f, fill=fill + (255,))
    # trait jaune qui se dessine
    q = min(1.0, max(0.0, (t_in - 0.18) / 0.3))
    if q > 0:
        yy = y + bh - 20
        d.line([(x + 30, yy), (x + 30 + int((bw - 70) * q), yy)],
               fill=YELLOW + (255,), width=4)
    return img


def end_card(alpha):
    """CTA de fin : l'offre et le mot à envoyer."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1, f2 = _font(34), _font(21)
    t1 = "1 500 modèles · 7 000 FCFA"
    t2 = "Commande : envoie le mot PACK en message privé"
    w = int(max(d.textlength(t1, font=f1), d.textlength(t2, font=f2)) + 64)
    h = 104
    x, y = (W - w) // 2, H - h - 24
    d.rounded_rectangle([x, y, x + w, y + h], 16, fill=NAVY + (232,))
    d.rectangle([x, y, x + 6, y + h], fill=YELLOW + (255,))
    d.text((x + 30, y + 16), t1, font=f1, fill=YELLOW + (255,))
    d.text((x + 30, y + 62), t2, font=f2, fill=ICE + (255,))
    if alpha < 1:
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    return img


def pill(alpha):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = _font(22)
    txt = "1 500 MODÈLES POWERPOINT  ·  7 000 FCFA"
    tw = d.textlength(txt, font=f)
    w = int(tw + 40)
    x, y = (W - w) // 2, 16
    d.rounded_rectangle([x, y, x + w, y + 40], 20, fill=NAVY + (230,))
    d.text((x + 20, y + 9), txt, font=f, fill=ICE + (255,))
    if alpha < 1:
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    return img


def style(frame, i, j, block_t, focus):
    """Zoom continu sur le graphique + punch de coupe + vignette + saturation."""
    cx, cy, z0 = focus
    p = j / max(i - 1, 1)
    # le zoom ne s'arrête jamais et change de sens d'un plan à l'autre
    z = (z0 + 0.16 * p) if (block_t % 2 == 0) else (z0 + 0.16 - 0.16 * p)
    tx = min(0.94, max(0.06, cx + 0.02 * math.sin(block_t * 1.7)))
    ty = min(0.94, max(0.06, cy + 0.02 * math.cos(block_t * 1.3)))
    img = crop_zoom(Image.fromarray(frame).convert("RGB"), z, tx, ty)
    img = punch(img, j)
    a = np.asarray(img).astype(np.float32)
    # saturation + contraste légers : le bleu du template doit claquer
    g = a.mean(axis=2, keepdims=True)
    a = g + (a - g) * 1.16
    a = (a - 128) * 1.05 + 128
    a *= VIGNETTE[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def render_all(cuts, dur):
    """Écrit les frames dans ffmpeg au fil de l'eau (mémoire constante)."""
    raw = "/tmp/pub60_video.mp4"
    p = subprocess.Popen(
        [FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", raw], stdin=subprocess.PIPE)

    total_frames = 0
    for b, (t_in, label, side, force) in enumerate(SHOTS):
        block = cuts[b + 1] - cuts[b]
        # bornes en images : le total tombe pile sur 60 s
        f0, f1 = round(cuts[b] * FPS), round(cuts[b + 1] * FPS)
        n_out = f1 - f0
        need = block + 1.0                      # marge de décodage
        src_frames = max(2, int(need * SRC_FPS))
        # ratio source -> sortie : on consomme SPEED × n_out images de source
        step = min(1.30, SPEED * (src_frames / max(n_out, 1)) / (block / max(block, 1e-6)))
        step = SPEED
        focus = subject_box(t_in + min(0.8, block * 0.55 * SPEED), 1.0)
        src_iter = iter_source(t_in, block * SPEED + 0.6)
        cur, frame = -1, None
        for j in range(n_out):
            # on traverse SPEED × la durée du plan dans la source
            want = int(j * SPEED * SRC_FPS / FPS)
            while cur < want:
                try:
                    frame = next(src_iter)
                except StopIteration:
                    break
                cur += 1
            if frame is None:
                break
            img = style(frame, n_out, j, b, focus)
            if label:
                img.alpha_composite(card(label, side, j / FPS))
            if b == len(SHOTS) - 1:
                img.alpha_composite(end_card(min(1.0, max(0.0, (j - 12) / 12))))
            if j < 2 and force == 2:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 80 if j == 0 else 38)))
            p.stdin.write(img.convert("RGB").tobytes())
            total_frames += 1
        print(f"  plan {b + 1}/{len(SHOTS)}  {block:4.2f} s  ({n_out} images)  "
              f"« {(label or '—').replace(chr(10), ' / ')} »", flush=True)
    p.stdin.close()
    p.wait()
    print(f"  {total_frames} images / {total_frames / FPS:.2f} s", flush=True)
    return raw


# --------------------------------------------------------------- audio
def _noise(n, lo, hi, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n).astype(np.float32)
    sos = butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], btype="band", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def music(n):
    """Instrumental 132 BPM : kick, clap, hats 1/16, basse, pad, arpèges."""
    bar = BEAT * 4
    roots = [65.41, 87.31, 98.0, 73.42]         # C F G D
    m = np.zeros(n, np.float32)

    t0 = 0.0
    while t0 < n / SR:
        s = int(t0 * SR); ln = min(n - s, int(.26 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 122 * np.exp(-tt * 22) + 46
            m[s:s + ln] += (np.sin(2 * np.pi * np.cumsum(f) / SR) *
                            np.exp(-tt * 15) * .36).astype(np.float32)
        t0 += BEAT

    for b in range(int(n / SR / BEAT) + 1):
        if b % 4 in (1, 3):
            s = int(b * BEAT * SR); ln = min(n - s, int(.18 * SR))
            if ln > 0:
                m[s:s + ln] += (_noise(ln, 1500, 6500, b) *
                                np.exp(-np.arange(ln) / SR * 26) * .17).astype(np.float32)

    k = 0
    while k * BEAT / 4 < n / SR:
        s = int(k * BEAT / 4 * SR); ln = min(n - s, int(.04 * SR))
        if ln > 0:
            m[s:s + ln] += (_noise(ln, 8000, 16000, k + 7) *
                            np.exp(-np.arange(ln) / SR * 180) *
                            (.05 if k % 4 == 0 else .026)).astype(np.float32)
        k += 1

    k = 0
    while k * BEAT / 2 < n / SR:
        s = int(k * BEAT / 2 * SR); ln = min(n - s, int(.22 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[int((k * BEAT / 2) / bar) % 4]
            v = np.sin(2 * np.pi * r * tt) + .3 * np.sin(4 * np.pi * r * tt)
            e = np.exp(-tt * 11) * np.minimum(tt / .005, 1)
            sos = butter(2, 210 / (SR / 2), btype="low", output="sos")
            m[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * .27).astype(np.float32)
        k += 1

    for bi in range(int(n / SR / bar) + 1):
        s = int(bi * bar * SR); e = min(n, int((bi * bar + bar + .4) * SR))
        if s >= n:
            break
        tt = np.arange(e - s) / SR
        r = roots[bi % 4] * 4
        env = np.minimum(tt / .35, 1) * np.exp(-np.maximum(tt - bar * .5, 0) * 1.8)
        v = np.sin(2 * np.pi * r * tt) * .5 + np.sin(2 * np.pi * r * 1.5 * tt + .6) * .28
        sos = butter(2, 3000 / (SR / 2), btype="low", output="sos")
        m[s:e] += (sosfilt(sos, (v * env).astype(np.float32)) * .075).astype(np.float32)

    step = BEAT / 4
    k, t0 = 0, 3.0
    while t0 < n / SR - .2:
        s = int(t0 * SR); ln = min(n - s, int(.18 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            note = roots[int(t0 / bar) % 4] * 8 * (2 ** ([0, 7, 12, 15][k % 4] / 12))
            m[s:s + ln] += (np.sin(2 * np.pi * note * tt) * np.exp(-tt * 26) * .045).astype(np.float32)
        k += 1
        t0 += step
    return m


def presence(a, sr=SR):
    """Petit boost 1,8–5 kHz : la voix passe devant la musique."""
    sos = butter(2, [1800 / (sr / 2), 5000 / (sr / 2)], btype="band", output="sos")
    return a + 0.45 * sosfilt(sos, a)


def decode_vo(path):
    p = subprocess.run([FF, "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1",
                        "-f", "f32le", "-"], stdout=subprocess.PIPE, check=True)
    a = np.frombuffer(p.stdout, dtype=np.float32).copy()
    sos_hp = butter(2, 90 / (SR / 2), btype="high", output="sos")
    sos_lp = butter(2, 15000 / (SR / 2), btype="low", output="sos")
    a = sosfilt(sos_lp, sosfilt(sos_hp, a))
    a = presence(a)
    # coupe les silences de tête/queue
    idx = np.where(np.abs(a) > 10 ** (-46 / 20))[0]
    if idx.size:
        a = a[max(0, idx[0] - int(.05 * SR)): idx[-1] + int(.06 * SR)]
    return a


def build_audio(cuts):
    n = int(TOTAL * SR)
    vo = np.zeros(n, np.float32)
    for num, st in VO_TAKES:
        a = decode_vo(os.path.join(AUD, f"seg{num:02d}.mp3"))
        a = a / max(float(np.abs(a).max()), 1e-6) * 0.70
        s = int(st * SR); e = min(n, s + len(a))
        vo[s:e] += a[: e - s]
        print(f"    voix {num} @ {st:5.2f}s  {len(a) / SR:4.2f} s", flush=True)

    mus = music(n)
    mus /= max(float(np.abs(mus).max()), 1e-6)
    mus *= 0.22

    # ducking : creux de ~9 dB sous la voix, ouverture/fermeture douces
    env = np.abs(vo).astype(np.float32)
    env = sosfilt(butter(1, 3.0 / (SR / 2), btype="low", output="sos"), env)
    env /= max(float(env.max()), 1e-6)
    mus *= 1.0 - 0.66 * np.clip(env * 2.6, 0, 1)

    sfx = np.zeros(n, np.float32)
    for b, cut in enumerate(cuts[:-1]):
        s = int(cut * SR)
        ln = min(n - s, int(.45 * SR))
        if ln > 0:
            w = _noise(ln, 600, 6000, 200 + b) * np.linspace(1, 0, ln) ** 2
            sfx[s:s + ln] += (w * (.22 if b else .14)).astype(np.float32)
        if b < len(SHOTS) and SHOTS[b][3] == 2 and ln > 0:
            tt = np.arange(ln) / SR
            sfx[s:s + ln] += (np.sin(2 * np.pi * (90 * np.exp(-tt * 9) + 45) * tt) *
                              np.exp(-tt * 9) * .34).astype(np.float32)

    for t, g in ((VO_TAKES[6][1] - 0.05, .18), (TOTAL - 0.9, .16)):
        s = int(t * SR); ln = min(n - s, int(1.5 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            sfx[s:s + ln] += (np.sin(2 * np.pi * 1046.5 * tt) * np.exp(-tt * 3.2) * g).astype(np.float32)

    # largeur stéréo sur la musique seule : la voix reste au centre
    d = int(0.009 * SR)
    mus_l = mus
    mus_r = np.concatenate([np.zeros(d, np.float32), mus[:-d]]) * 0.95
    left = vo + mus_l + sfx
    right = vo + mus_r + sfx
    mix = np.stack([left, right], axis=1)
    peak = float(np.abs(mix).max())
    if peak > 0.97:
        mix *= 0.97 / peak
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with wavemod.open(MIX, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("  mix ->", MIX, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--audio-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(AUD, exist_ok=True)
    cuts, dur, starts = timeline()
    print("  coupes :", " ".join(f"{c:.2f}" for c in cuts))

    if a.preview:
        sheet = Image.new("RGB", (4 * 284 + 50, 4 * 190 + 40), (12, 18, 40))
        d = ImageDraw.Draw(sheet)
        for b in range(len(SHOTS)):
            mid = (cuts[b] + cuts[b + 1]) / 2
            t_in = SHOTS[b][0] + (cuts[b + 1] - cuts[b]) * 0.45 * SPEED
            frames = []
            for k, fr in enumerate(iter_source(t_in - 0.2, 0.3)):
                frames.append(fr)
                if k > 12:
                    break
            img = Image.fromarray(frames[6]).convert("RGB")
            fx = subject_box(t_in - 0.1, 0.6)
            img = crop_zoom(img, fx[2], fx[0], fx[1])
            img = img.convert("RGBA")
            if SHOTS[b][1]:
                img.alpha_composite(card(SHOTS[b][1], SHOTS[b][2], 1.0))
            if b == len(SHOTS) - 1:
                img.alpha_composite(end_card(1.0))
            im = img.convert("RGB").resize((284, 160), Image.LANCZOS)
            x, y = 10 + (b % 4) * 294, 10 + (b // 4) * 190
            sheet.paste(im, (x, y))
            d.text((x + 4, y + 164), f"plan {b + 1} — {mid:.1f}s — {SHOTS[b][1].replace(chr(10), ' / ')}",
                   font=_font(13), fill=(255, 255, 255))
        sheet.save("/tmp/pub60_preview.jpg", quality=90)
        print("  planche : /tmp/pub60_preview.jpg")
        return

    raw = "/tmp/pub60_video.mp4"
    if not a.audio_only or not os.path.exists(raw):
        raw = render_all(cuts, dur)
    build_audio(cuts)
    # mesure loudness (2 passages) : la cible -14 LUFS doit être atteinte pour de vrai
    r = subprocess.run(
        [FF, "-hide_banner", "-i", MIX, "-af",
         "loudnorm=I=-13.4:TP=-1.2:LRA=9:print_format=json", "-f", "null", "-"],
        stderr=subprocess.PIPE, text=True, check=True)
    import json
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln = (f"loudnorm=I=-13.4:TP=-1.2:LRA=9:measured_I={js['input_i']}:"
          f"measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(
        [FF, "-y", "-v", "error", "-i", raw, "-i", MIX,
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-af", f"{ln},alimiter=limit=0.80:level=disabled,aresample=48000",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-shortest", "-movflags", "+faststart", OUT], check=True)
    print(f"Rendu : {OUT} ({os.path.getsize(OUT) / 1e6:.2f} Mo)")


if __name__ == "__main__":
    main()
