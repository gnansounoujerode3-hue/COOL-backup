#!/usr/bin/env python3
"""
Generates subtle luxury minimalist studio SFX and mixes them underneath the
original voiceover track of `Video brut 8.mp4` (-18dB to -22dB below speech).
"""
import os
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

OUT_DIR = "/tmp/work_cache/sfx_ref8"
os.makedirs(OUT_DIR, exist_ok=True)
RAW_VIDEO = "/home/user/COOL-backup/Video brut 8.mp4"
ORIG_WAV = os.path.join(OUT_DIR, "orig_voice.wav")
MIXED_WAV = os.path.join(OUT_DIR, "mixed_audio.wav")

SR = 44100


def butter_bandpass(lowcut, highcut, fs, order=3):
    nyq = 0.5 * fs
    low = max(0.001, min(0.99, lowcut / nyq))
    high = max(low + 0.001, min(0.999, highcut / nyq))
    b, a = butter(order, [low, high], btype="band")
    return b, a


def make_soft_whoosh(duration=0.34, low_f=160, high_f=1900, vol=0.085):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(71)
    noise = rng.standard_normal(n)
    b, a = butter_bandpass(low_f, high_f, SR, order=2)
    filtered = lfilter(b, a, noise)
    env = np.sin(np.pi * (t / duration)) ** 2.2
    freq = np.linspace(low_f * 1.5, low_f * 0.55, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * env * 0.45
    sig = (filtered / (np.max(np.abs(filtered)) + 1e-6) * 0.55 + sub) * env * vol
    return np.column_stack([sig * 0.96, sig * 1.04])


def make_marker_swipe(duration=0.18, vol=0.065):
    """Soft felt/brush swipe for the lime-green highlight bar wipe."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(33)
    noise = rng.standard_normal(n)
    b, a = butter_bandpass(450, 2800, SR, order=2)
    f_noise = lfilter(b, a, noise)
    env = np.sin(np.pi * (t / duration)) ** 1.8
    tone = np.sin(2 * np.pi * np.linspace(320, 540, n) * t) * 0.35
    sig = (f_noise / (np.max(np.abs(f_noise)) + 1e-6) * 0.65 + tone) * env * vol
    return np.column_stack([sig * 1.05, sig * 0.95])


def make_minimal_snap(duration=0.14, vol=0.095):
    """Crisp editorial snap + warm low thump for Stark White & Burgundy Poster cuts."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    sub_f = 135.0 * np.exp(-t * 18.0) + 42.0
    sub = np.sin(2 * np.pi * np.cumsum(sub_f) / SR) * np.exp(-t * 16.0) * 0.65
    click = np.sin(2 * np.pi * 1650.0 * t) * np.exp(-t * 85.0) * 0.35
    sig = (sub + click) * vol
    return np.column_stack([sig, sig])


def make_luxury_swell(duration=1.6, vol=0.070):
    """Warm luxury harmonic chord swell for the Dark Espresso-Gold Orbital scenes."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    env = np.sin(np.pi * (t / duration)) ** 1.6
    # Warm A-minor9 / D-maj7 luxury pad intervals
    f1, f2, f3 = 110.0, 164.81, 246.94
    pad_l = (np.sin(2 * np.pi * f1 * t) + 0.45 * np.sin(2 * np.pi * f2 * t) + 0.25 * np.sin(2 * np.pi * f3 * t)) * env * vol
    pad_r = (np.sin(2 * np.pi * f1 * t) + 0.45 * np.sin(2 * np.pi * (f2 * 1.003) * t) + 0.25 * np.sin(2 * np.pi * (f3 * 0.998) * t)) * env * vol
    return np.column_stack([pad_l, pad_r])


def make_icon_pop(duration=0.11, f0=440, f1=880, vol=0.080):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = np.exp(-t * 36.0) * (1.0 - np.exp(-t * 380.0))
    sig = (np.sin(phase) + 0.28 * np.sin(2 * phase)) * env * vol
    return np.column_stack([sig, sig])


def add_at(mix, clip, t_sec):
    idx = int(t_sec * SR)
    if idx < 0 or idx >= len(mix):
        return
    end = min(len(mix), idx + len(clip))
    mix[idx:end] += clip[: end - idx]


def main():
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            RAW_VIDEO,
            "-vn",
            "-ac",
            "2",
            "-ar",
            str(SR),
            "-f",
            "wav",
            ORIG_WAV,
        ],
        check=True,
    )
    sr, data = wavfile.read(ORIG_WAV)
    voice = data.astype(np.float32) / 32768.0 if data.dtype == np.int16 else data.astype(np.float32)
    if voice.ndim == 1:
        voice = np.column_stack([voice, voice])

    mix = voice.copy()

    # 1. Lime-green highlight bar wipes
    swipe = make_marker_swipe(0.18, vol=0.060)
    for tw in [1.58, 3.06, 4.96, 5.94, 7.90, 8.92, 9.90, 17.14, 30.04, 35.48, 40.02, 41.80, 45.24, 55.14, 65.82]:
        add_at(mix, swipe, tw)

    # 2. Stark White Screen & Burgundy Editorial Poster snaps + whooshes
    snap = make_minimal_snap(0.14, vol=0.090)
    whoosh = make_soft_whoosh(0.32, 160, 1800, vol=0.080)
    for tc in [12.06, 13.86, 15.76, 23.94, 29.32, 60.10, 64.92]:
        add_at(mix, snap, tc)
        add_at(mix, whoosh, max(0.0, tc - 0.06))

    # 3. Dark Luxury Espresso-Gold Orbital swells (19.22 - 23.96s & 49.75 - 53.85s)
    swell = make_luxury_swell(2.1, vol=0.062)
    for ts in [19.20, 21.36, 49.75, 51.80]:
        add_at(mix, swell, ts)
        add_at(mix, whoosh, ts)

    # 4. 3D Yellow Key & 3D Yellow Brain diagonal bridge icon pops
    for idx, ti in enumerate([32.96, 46.50, 58.90, 68.50]):
        add_at(mix, make_icon_pop(0.12, 420 + (idx % 2) * 90, 860 + (idx % 2) * 120, vol=0.082), ti)

    peak = np.max(np.abs(mix))
    if peak > 0.96:
        mix = mix * (0.96 / peak)

    out_pcm = np.clip(mix * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(MIXED_WAV, SR, out_pcm)
    print(f"Saved mixed stereo audio to {MIXED_WAV} ({len(out_pcm)/SR:.2f}s)")


if __name__ == "__main__":
    main()
