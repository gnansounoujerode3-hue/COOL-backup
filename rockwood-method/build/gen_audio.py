#!/usr/bin/env python3
"""Musique originale (aucune licence) + SFX, synthétisés en numpy."""
import os
import sys

import numpy as np
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import OVERLAYS  # noqa: E402

SR = 44100
DUR = 29.1
OUT = os.path.dirname(os.path.abspath(__file__))
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def note(f, start, dur, amp=0.2, kind="pad"):
    i0, i1 = int(start * SR), int(min(DUR, start + dur) * SR)
    if i1 <= i0:
        return np.zeros(0)
    n = i1 - i0
    tt = np.arange(n) / SR
    if kind == "pad":
        env = np.minimum(1, tt / 0.9) * np.exp(-tt * 0.28)
        sig = (np.sin(2 * np.pi * f * tt) * 0.6
               + np.sin(2 * np.pi * f * 2 * tt) * 0.16
               + np.sin(2 * np.pi * f * 3.001 * tt) * 0.07)
        sig += 0.012 * rng.standard_normal(n)          # légère texture
    elif kind == "pluck":
        env = np.exp(-tt * 3.4) * np.minimum(1, tt / 0.004)
        sig = (np.sin(2 * np.pi * f * tt)
               + 0.42 * np.sin(2 * np.pi * f * 2.01 * tt) * np.exp(-tt * 2.2)
               + 0.18 * np.sin(2 * np.pi * f * 3.02 * tt) * np.exp(-tt * 3.0))
    elif kind == "sub":
        env = np.minimum(1, tt / 0.5) * np.exp(-tt * 0.16)
        sig = np.sin(2 * np.pi * f * tt)
    else:  # air
        env = np.minimum(1, tt / 2.0) * np.minimum(1, (DUR - start - tt) / 2.0)
        sig = rng.standard_normal(n)
    return amp * env * sig


# --- lit musical : Am - F - C - G (4 mesures, 84 BPM) -----------------------
bpm = 84.0
beat = 60 / bpm
bar = 4 * beat
CH = [
    (110.00, [220.00, 261.63, 329.63]),   # Am
    (87.31, [174.61, 220.00, 261.63]),    # F
    (130.81, [261.63, 329.63, 392.00]),   # C
    (98.00, [196.00, 246.94, 293.66]),    # G
]
music = np.zeros(N)
bar_i = 0.0
ci = 0
while bar_i < DUR:
    root, chord = CH[ci % 4]
    for k, f in enumerate(chord):
        seg = note(f, bar_i + k * 0.06, bar * 0.98, amp=0.055, kind="pad")
        music[:len(seg)] += seg if bar_i == 0 else 0
        i0 = int(bar_i * SR)
        j = min(N, i0 + len(seg))
        music[i0:j] += seg[:j - i0]
    for k in range(4):
        i0 = int((bar_i + k * beat) * SR)
        seg = note(root * 2, bar_i + k * beat, 1.1, amp=0.05, kind="pluck")
        j = min(N, i0 + len(seg))
        music[i0:j] += seg[:j - i0]
    i0 = int(bar_i * SR)
    seg = note(root / 2, bar_i, bar * 0.98, amp=0.09, kind="sub")
    j = min(N, i0 + len(seg))
    music[i0:j] += seg[:j - i0]
    bar_i += bar
    ci += 1

air = note(1, 0, DUR, amp=0.006, kind="air")
music += air

# --- SFX --------------------------------------------------------------------
sfx = np.zeros(N)


def blip(freqs, start, dur, amp=0.35, decay=26, click=True):
    i0 = int(start * SR)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt * decay)
    sig = sum(np.sin(2 * np.pi * f * tt) * g for f, g in freqs) * env
    if click:
        cn = int(0.006 * SR)
        sig[:cn] += rng.standard_normal(cn) * np.linspace(0.6, 0, cn)
    j = min(N, i0 + n)
    sfx[i0:j] += amp * sig[:j - i0]


# ticks sur chaque apparition de carte
for asset, t0, t1, cx, cy, anim in OVERLAYS:
    if asset == "scrim":
        continue
    if asset == "stamp":
        blip([(70, 1.0), (140, 0.4)], t0, 0.45, amp=0.5, decay=11, click=True)
    elif asset == "potato":
        blip([(520, 1.0), (780, 0.5)], t0, 0.22, amp=0.3, decay=16)
    elif asset == "cta":
        blip([(660, 1.0), (880, 0.7), (1320, 0.35)], t0, 0.5, amp=0.3, decay=9)
    elif asset == "endcard":
        blip([(110, 1.0), (220, 0.5)], t0, 0.9, amp=0.42, decay=4.5)
        blip([(880, 1.0), (1100, 0.5)], t0 + 0.05, 0.4, amp=0.16, decay=10)
    else:
        blip([(720, 1.0), (1080, 0.45)], t0, 0.18, amp=0.22, decay=22)

# swoosh léger avant le titre et avant la carte finale
for st in (3.75, 25.6):
    i0 = int(st * SR)
    n = int(0.75 * SR)
    tt = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(tt / 0.75, 0, 1)) ** 2
    ns = rng.standard_normal(n)
    # bruit filtré passe-haut simple
    hp = np.concatenate([[0], np.diff(ns)])
    j = min(N, i0 + n)
    sfx[i0:j] += 0.16 * (env * hp)[:j - i0]


def write(path, sig, peak=0.5):
    m = np.abs(sig).max()
    if m > 0:
        sig = sig / m * peak
    st = np.stack([sig, sig], axis=1)
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    print(f"  {os.path.basename(path)}  {len(sig) / SR:.2f}s  pic={peak}")


write(os.path.join(OUT, "music.wav"), music, peak=0.42)
write(os.path.join(OUT, "sfx.wav"), sfx, peak=0.62)
print("Audio synthétisé.")
