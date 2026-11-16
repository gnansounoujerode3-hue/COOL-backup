#!/usr/bin/env python3
"""Monte la voix off sur la vidéo complète Infographic_Blue__Light_1.mp4.

- découpe chaque prise en PCM 48 kHz stéréo, filtre (passe-haut, passe-bas,
  compression douce : la voix synthétique gagne en présence et perd le souffle),
- recale chaque bloc sur un timecode calé sur les séquences du template,
- normalise le niveau de chaque prise pour qu'aucune phrase ne domine,
- masterise l'ensemble à -16 LUFS / -1,5 dBTP (norme « parole seule »),
- remuxe la vidéo **sans réencodage** (`-c:v copy`) : l'image d'origine est intacte.

    python3 infographic-blue-cuts/voix-off/build_vo.py
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FF = "/tmp/bin/ffmpeg"
if not os.path.exists(FF):
    from imageio_ffmpeg import get_ffmpeg_exe
    FF = get_ffmpeg_exe()

SRC = os.path.join(ROOT, "imports", "Infographic_Blue__Light_1.mp4")
OUT = os.path.join(ROOT, "infographic-blue-cuts", "Infographic_Blue__Light_1_voix-off.mp4")
MIX = os.path.join(HERE, "mix_voix-off.wav")
SR = 48000

# (fichier, timecode de départ) — calé sur les séquences du template
PLAN = [
    ("seg01.mp3", 3.0),     # ouverture, logo qui se dessine
    ("seg02.mp3", 18.0),    # réseau d'hexagones
    ("seg03.mp3", 44.0),    # cercles / réseaux : la douleur
    ("seg04.mp3", 76.0),    # processus, flèches : le pack
    ("seg05.mp3", 106.0),   # SEO, puzzles, frise : la variété
    ("seg06.mp3", 138.0),   # quatre cartes : les usages
    ("seg07.mp3", 164.0),   # mind map, camemberts : l'objection
    ("seg08.mp3", 190.0),   # cartes, nuage : l'offre
    ("seg10.mp3", 226.0),   # pont vers les cartes du monde
    ("seg09.mp3", 246.0),   # signature
]

RMS_TARGET = 0.085   # ≈ -21 dBFS RMS sur les zones parlées, avant loudnorm


def decode(path):
    p = subprocess.run(
        [FF, "-v", "error", "-i", path, "-af",
         "highpass=f=85,lowpass=f=15000,"
         "acompressor=threshold=-20dB:ratio=3.5:attack=5:release=120:makeup=1.5dB",
         "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"],
        check=True, stdout=subprocess.PIPE)
    a = np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, 2).copy()
    return a


def trim_silence(a, thr_db=-46.0, keep=0.06):
    """Coupe les silences de tête et de queue laissés par la synthèse."""
    mono = np.abs(a).max(axis=1)
    thr = 10 ** (thr_db / 20)
    idx = np.where(mono > thr)[0]
    if idx.size == 0:
        return a
    pad = int(keep * SR)
    s = max(0, idx[0] - pad)
    e = min(len(a), idx[-1] + pad)
    return a[s:e]


def fade(a, ms=8):
    n = int(ms / 1000 * SR)
    if len(a) < 2 * n:
        return a
    w = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    a = a.copy()
    a[:n] *= w
    a[-n:] *= w[::-1]
    return a


def main():
    total = 265.98
    n_total = int(round(total * SR)) + SR // 10
    mix = np.zeros((n_total, 2), dtype=np.float32)
    levels = []

    for name, at in PLAN:
        a = fade(trim_silence(decode(os.path.join(HERE, name))))
        rms = float(np.sqrt((a ** 2).mean()))
        g = min(RMS_TARGET / max(rms, 1e-6), 4.0)
        a = a * g
        start = int(round(at * SR))
        end = start + len(a)
        if end > n_total:
            raise SystemExit(f"{name} dépasse la durée de la vidéo ({end / SR:.2f} s)")
        mix[start:end] += a
        levels.append((name, at, len(a) / SR, rms, g))

    # sécurité : crête locale sous 0 dBFS avant le master
    peak = float(np.abs(mix).max())
    if peak > 0.98:
        mix *= 0.98 / peak

    # WAV 48 kHz stéréo (float -> pcm16)
    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    import wave as wavemod
    with wavemod.open(MIX, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    # master : -16 LUFS, crête -1,5 dBTP, puis mux sans réencodage vidéo
    subprocess.run(
        [FF, "-y", "-v", "error", "-i", SRC, "-i", MIX,
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-shortest", "-movflags", "+faststart", OUT],
        check=True)

    print(f"Vidéo  : {OUT} ({os.path.getsize(OUT) / 1e6:.2f} Mo)")
    for name, at, d, rms, g in levels:
        print(f"  {name}  @ {int(at) // 60}:{at % 60:05.2f}  {d:5.2f} s  gain ×{g:.2f}")


if __name__ == "__main__":
    main()
