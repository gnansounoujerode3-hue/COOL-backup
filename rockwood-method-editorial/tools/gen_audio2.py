#!/usr/bin/env python3
"""Bande son v2 : nappe chaude à accords enrichis, arpèges espacés, grain vinyle,
riser avant la carte finale, SFX « papier » plutôt que bips.

Aucune licence : tout est synthétisé (numpy).
"""
import os
import sys

import numpy as np
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan2 import OVERLAYS, DURATION  # noqa: E402

SR = 44100
N = int(SR * DURATION)
OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(11)


def env_adsr(n, a, d, s, r, sustain=0.7):
    """Enveloppe simple en secondes."""
    t = np.arange(n) / SR
    e = np.ones(n)
    e *= np.clip(t / max(a, 1e-4), 0, 1)
    e *= np.where(t < a, 1.0, 1.0)
    dec = np.clip((t - a) / max(d, 1e-4), 0, 1)
    e *= 1 - (1 - sustain) * dec
    rel = np.clip((t - (n / SR - r)) / max(r, 1e-4), 0, 1)
    e *= 1 - rel
    return np.clip(e, 0, 1)


def onepole_lp(x, cutoff):
    """Filtre passe-bas une pole (vectorisé par récursion simple sur blocs)."""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def voice(freq, n, kind="pad", amp=0.1):
    t = np.arange(n) / SR
    if kind == "pad":
        sig = (np.sin(2 * np.pi * freq * t) * 0.62
               + np.sin(2 * np.pi * freq * 2 * t + 0.3) * 0.14
               + np.sin(2 * np.pi * freq * 3 * t + 1.1) * 0.05
               + np.sin(2 * np.pi * freq * 0.5 * t) * 0.06)
        e = env_adsr(n, 1.5, 2.0, 0.75, 1.6)
    elif kind == "pluck":
        sig = (np.sin(2 * np.pi * freq * t)
               + 0.38 * np.sin(2 * np.pi * freq * 2.001 * t) * np.exp(-t * 3.0)
               + 0.14 * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 4.5))
        e = env_adsr(n, 0.006, 0.5, 0.28, 0.9, sustain=0.22)
    elif kind == "chime":
        sig = (np.sin(2 * np.pi * freq * t) * 0.7
               + np.sin(2 * np.pi * freq * 2.76 * t) * 0.2
               + np.sin(2 * np.pi * freq * 5.4 * t) * 0.08)
        e = env_adsr(n, 0.004, 1.2, 0.2, 1.4, sustain=0.1)
    else:  # thump
        sig = np.sin(2 * np.pi * freq * t * np.exp(-t * 2.5))
        e = env_adsr(n, 0.004, 0.35, 0.2, 0.5, sustain=0.15)
    return amp * e * sig


def place(buf, sig, start):
    i0 = int(start * SR)
    j = min(N, i0 + len(sig))
    if j > i0:
        buf[i0:j] += sig[:j - i0]


# ---------------------------------------------------------------- musique
music = np.zeros(N)
bpm = 78.0
beat = 60 / bpm
bar = 4 * beat

# Am9 / Fmaj7 / Cmaj9 / G6  (accords enrichis, registre grave + médium)
CHORDS = [
    (110.00, [220.00, 261.63, 329.63, 493.88]),   # Am9
    (87.31,  [174.61, 220.00, 261.63, 329.63]),   # Fmaj7
    (130.81, [196.00, 261.63, 329.63, 392.00]),   # Cmaj7/9
    (98.00,  [196.00, 246.94, 293.66, 392.00]),   # G6
]
ARP = [0, 2, 1, 3, 2, 1]

bi, ci = 0.0, 0
while bi < DURATION:
    root, chord = CHORDS[ci % 4]
    # nappe : accord tenu, deux octaves
    for k, f in enumerate(chord):
        place(music, voice(f, int((bar * 1.02) * SR), "pad", amp=0.052), bi + k * 0.05)
    place(music, voice(root / 2, int(bar * 1.02 * SR), "pad", amp=0.075), bi)
    # arpège espacé (croches)
    for k in range(6):
        f = chord[ARP[k] % len(chord)] * (2 if k in (3, 5) else 1)
        place(music, voice(f, int(1.6 * SR), "pluck", amp=0.042), bi + k * (beat / 2))
    # pulsation grave
    place(music, voice(root / 2, int(1.1 * SR), "thump", amp=0.055), bi)
    bi += bar
    ci += 1

# lit de vinyle : bruit filtré + modulation lente
air_n = rng.standard_normal(N)
air = onepole_lp(air_n, 3200) - onepole_lp(air_n, 220)
air = air / (np.abs(air).max() + 1e-9)
air *= 0.010 * (1 + 0.25 * np.sin(2 * np.pi * 0.11 * np.arange(N) / SR))

# riser avant la carte finale (25,5 → 25,9 s)
ris = np.zeros(N)
i0, i1 = int(25.30 * SR), int(25.95 * SR)
tt = np.arange(i1 - i0) / SR
noise = rng.standard_normal(i1 - i0)
noise = noise - onepole_lp(noise, 400)          # passe-haut
ris[i0:i1] = noise * (tt / tt.max()) ** 2.4 * 0.16

music = music + air + ris

# ---------------------------------------------------------------- SFX
sfx = np.zeros(N)


def noise_hit(start, dur, amp=0.3, hz=2500, decay=22.0):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = x - onepole_lp(x, hz)                    # garde les hautes fréquences
    e = np.exp(-np.arange(n) / SR * decay)
    place(sfx, amp * x * e / (np.abs(x).max() + 1e-9), start)


for asset, t0, t1, *_ in OVERLAYS:
    if asset in ("scrim_top", "scrim_bottom", "glow"):
        continue
    if asset == "sticker":
        place(sfx, voice(180, int(0.5 * SR), "thump", amp=0.34), t0)      # tapis posé
        noise_hit(t0, 0.14, amp=0.20, hz=4200, decay=40)
    elif asset == "stamp":
        place(sfx, voice(120, int(0.6 * SR), "thump", amp=0.40), t0)
        noise_hit(t0, 0.18, amp=0.26, hz=3200, decay=30)
    elif asset == "pill":
        place(sfx, voice(1046.5, int(1.1 * SR), "chime", amp=0.16), t0)
        place(sfx, voice(1568.0, int(0.9 * SR), "chime", amp=0.09), t0 + 0.06)
    elif asset == "endcard":
        place(sfx, voice(65.41, int(1.8 * SR), "thump", amp=0.42), t0)
        for k, f in enumerate([261.63, 329.63, 392.00, 523.25]):
            place(sfx, voice(f, int(2.4 * SR), "chime", amp=0.085), t0 + 0.10 + k * 0.05)
    elif asset.startswith("rows") or asset.startswith("hl_"):
        noise_hit(t0, 0.10, amp=0.13, hz=5200, decay=55)   # tick papier
    elif asset == "big100":
        noise_hit(t0, 0.12, amp=0.15, hz=4800, decay=45)
        place(sfx, voice(220, int(0.4 * SR), "thump", amp=0.18), t0)


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
    print(f"  {os.path.basename(path)}  {len(sig) / SR:.2f}s  pic={peak}")


write(os.path.join(OUT, "music2.wav"), music, peak=0.40)
write(os.path.join(OUT, "sfx2.wav"), sfx, peak=0.58)
print("Bande son v2 synthétisée.")
