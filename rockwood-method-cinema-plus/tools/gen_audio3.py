#!/usr/bin/env python3
"""Bande son v3 : nappe 74 BPM à accords enrichis, arpèges, sub, grain vinyle,
whooshes sur chaque coupe, risers, SFX papier et carillons. Tout est synthétisé."""
import os
import sys

import numpy as np
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan3 import CUTS, CUTAWAYS, DURATION, OVERLAYS  # noqa: E402

SR = 44100
N = int(SR * DURATION)
OUT = os.path.dirname(os.path.abspath(__file__))
AUD = os.environ.get("ROCKWOOD_AUDIO", os.path.join(os.path.dirname(OUT), "audio"))
os.makedirs(AUD, exist_ok=True)
rng = np.random.default_rng(77)


def adsr(n, a, d, s, r, sustain=0.7):
    t = np.arange(n) / SR
    e = np.clip(t / max(a, 1e-4), 0, 1)
    e *= 1 - (1 - sustain) * np.clip((t - a) / max(d, 1e-4), 0, 1)
    rel = np.clip((t - (n / SR - r)) / max(r, 1e-4), 0, 1)
    return np.clip(e * (1 - rel), 0, 1)


def lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def tone(freq, n, kind, amp):
    t = np.arange(n) / SR
    if kind == "pad":
        sig = (np.sin(2 * np.pi * freq * t) * 0.62
               + np.sin(2 * np.pi * freq * 2 * t + 0.3) * 0.13
               + np.sin(2 * np.pi * freq * 3 * t + 1.1) * 0.045
               + np.sin(2 * np.pi * freq * 0.5 * t) * 0.055)
        e = adsr(n, 1.7, 2.2, 0.78, 1.8)
    elif kind == "pluck":
        sig = (np.sin(2 * np.pi * freq * t)
               + 0.36 * np.sin(2 * np.pi * freq * 2.001 * t) * np.exp(-t * 3.1)
               + 0.13 * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 4.6))
        e = adsr(n, 0.006, 0.55, 0.26, 0.95, sustain=0.2)
    elif kind == "chime":
        sig = (np.sin(2 * np.pi * freq * t) * 0.7
               + np.sin(2 * np.pi * freq * 2.76 * t) * 0.19
               + np.sin(2 * np.pi * freq * 5.4 * t) * 0.07)
        e = adsr(n, 0.004, 1.3, 0.18, 1.5, sustain=0.08)
    else:
        sig = np.sin(2 * np.pi * freq * t * np.exp(-t * 2.4))
        e = adsr(n, 0.004, 0.35, 0.2, 0.5, sustain=0.14)
    return amp * e * sig


def place(buf, sig, start):
    i0 = int(start * SR)
    j = min(N, i0 + len(sig))
    if j > i0:
        buf[i0:j] += sig[:j - i0]


# ---------------------------------------------------------------- musique
music = np.zeros(N)
bpm = 74.0
beat = 60 / bpm
bar = 4 * beat

# Am9 · Fmaj7 · Cmaj9 · G6 · Em7 · Fmaj7 · Cmaj9 · G6
CHORDS = [
    (110.00, [220.00, 261.63, 329.63, 493.88]),
    (87.31, [174.61, 220.00, 261.63, 349.23]),
    (130.81, [196.00, 261.63, 329.63, 392.00]),
    (98.00, [196.00, 246.94, 293.66, 392.00]),
    (82.41, [164.81, 196.00, 246.94, 329.63]),
    (87.31, [174.61, 220.00, 261.63, 349.23]),
    (130.81, [196.00, 261.63, 329.63, 392.00]),
    (98.00, [196.00, 246.94, 293.66, 392.00]),
]
ARP = [0, 2, 1, 3, 2, 3]

bi, ci = 0.0, 0
while bi < DURATION:
    root, chord = CHORDS[ci % len(CHORDS)]
    for k, f in enumerate(chord):
        place(music, tone(f, int(bar * 1.03 * SR), "pad", 0.05), bi + k * 0.05)
    place(music, tone(root / 2, int(bar * 1.05 * SR), "pad", 0.072), bi)
    for k in range(6):
        f = chord[ARP[k] % len(chord)] * (2 if k in (3, 5) else 1)
        place(music, tone(f, int(1.7 * SR), "pluck", 0.04), bi + k * (beat / 2))
    place(music, tone(root / 2, int(1.2 * SR), "thump", 0.05), bi)
    bi += bar
    ci += 1

air = rng.standard_normal(N)
air = lp(air, 3200) - lp(air, 240)
air = air / (np.abs(air).max() + 1e-9) * 0.009 * (1 + 0.3 * np.sin(2 * np.pi * 0.09 * np.arange(N) / SR))

# risers avant les moments forts
ris = np.zeros(N)
for start, end, amp in ((2.55, 3.00, 0.12), (6.20, 6.55, 0.11), (12.15, 12.50, 0.10),
                        (13.10, 13.45, 0.11), (16.70, 17.05, 0.13), (25.30, 25.85, 0.15)):
    i0, i1 = int(start * SR), int(end * SR)
    if i1 <= i0:
        continue
    tt = np.arange(i1 - i0) / SR
    ns = rng.standard_normal(i1 - i0)
    ns = ns - lp(ns, 420)
    ris[i0:i1] += ns * (tt / tt.max()) ** 2.3 * amp

music = music + air + ris

# ---------------------------------------------------------------- SFX
sfx = np.zeros(N)


def noise_hit(start, dur, amp, hz=4800, decay=40):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = x - lp(x, hz)
    e = np.exp(-np.arange(n) / SR * decay)
    place(sfx, amp * x * e / (np.abs(x).max() + 1e-9), start)


def whoosh(start, dur=0.55, amp=0.22, reverse=False):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    x = rng.standard_normal(n)
    x = x - lp(x, 900)
    if reverse:
        env = env[::-1]
    place(sfx, amp * env * x / (np.abs(x).max() + 1e-9), start)


# whoosh léger à chaque coupe
for c in CUTS:
    whoosh(c - 0.26, 0.5, 0.10 if c not in (3.0, 6.55) else 0.13)

for name, t0, t1, anchor, x, y, anim in OVERLAYS:
    if name in ("scrim_top", "scrim_bottom", "glow"):
        continue
    if name == "sticker":
        place(sfx, tone(180, int(0.5 * SR), "thump", 0.32), t0)
        noise_hit(t0, 0.14, 0.19, 4200, 42)
    elif name == "stamp":
        place(sfx, tone(120, int(0.6 * SR), "thump", 0.38), t0)
        noise_hit(t0, 0.18, 0.24, 3200, 30)
    elif name == "pill":
        place(sfx, tone(1046.5, int(1.1 * SR), "chime", 0.15), t0)
        place(sfx, tone(1568.0, int(0.9 * SR), "chime", 0.085), t0 + 0.06)
    elif name.startswith(("card", "hl_")):
        noise_hit(t0, 0.10, 0.12, 5200, 55)

# carillons d'ouverture de chaque scène de coupe
for c in CUTAWAYS:
    t0 = c[0]
    place(sfx, tone(523.25, int(1.6 * SR), "chime", 0.11), t0 + 0.02)
    place(sfx, tone(659.25, int(1.4 * SR), "chime", 0.07), t0 + 0.10)
    whoosh(t0 - 0.22, 0.42, 0.16)

# carte finale
place(sfx, tone(65.41, int(2.0 * SR), "thump", 0.42), 25.85)
for k, f in enumerate([261.63, 329.63, 392.00, 523.25]):
    place(sfx, tone(f, int(2.6 * SR), "chime", 0.075), 25.95 + k * 0.06)


def write(path, sig, peak):
    m = np.abs(sig).max()
    if m > 0:
        sig = sig / m * peak
    st = np.stack([sig, sig], axis=1)
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    print(f"  {os.path.basename(path)} {len(sig) / SR:.2f}s pic={peak}")


write(os.path.join(AUD, "music3.wav"), music, 0.40)
write(os.path.join(AUD, "sfx3.wav"), sfx, 0.55)
print("Bande son v3 OK.")
