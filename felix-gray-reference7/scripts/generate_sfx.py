#!/usr/bin/env python3
"""
Generates subtle studio motion-graphic SFX and mixes them underneath the
original voiceover track of `videobrut 7.mp4` (-18dB to -22dB below speech).
"""
import os
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

OUT_DIR = "/home/user/.cache/sfx_ref7"
os.makedirs(OUT_DIR, exist_ok=True)
RAW_VIDEO = "/home/user/COOL-backup/videobrut 7.mp4"
ORIG_WAV = os.path.join(OUT_DIR, "orig_voice.wav")
MIXED_WAV = os.path.join(OUT_DIR, "mixed_audio.wav")

SR = 44100


def butter_bandpass(lowcut, highcut, fs, order=3):
    nyq = 0.5 * fs
    low = max(0.001, min(0.99, lowcut / nyq))
    high = max(low + 0.001, min(0.999, highcut / nyq))
    b, a = butter(order, [low, high], btype="band")
    return b, a


def make_whoosh(duration=0.38, low_f=140, high_f=1800, vol=0.11):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(n)
    b, a = butter_bandpass(low_f, high_f, SR, order=2)
    filtered = lfilter(b, a, noise)
    env = np.sin(np.pi * (t / duration)) ** 2.2
    # Add soft sub-swoosh
    freq = np.linspace(low_f * 1.4, low_f * 0.5, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * env * 0.45
    sig = (filtered / (np.max(np.abs(filtered)) + 1e-6) * 0.55 + sub) * env * vol
    return np.column_stack([sig * 0.95, sig * 1.05])


def make_ui_pop(duration=0.09, f0=520, f1=980, vol=0.085):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = np.linspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = np.exp(-t * 42.0) * (1.0 - np.exp(-t * 400.0))
    sig = (np.sin(phase) + 0.3 * np.sin(2 * phase)) * env * vol
    return np.column_stack([sig, sig])


def make_shatter(duration=0.85, vol=0.14):
    """Crystalline 3D badge shatter + warm sub impact."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    rng = np.random.default_rng(107)

    # 1. Initial crack / sub thump
    sub_freq = 110.0 * np.exp(-t * 9.5) + 36.0
    sub_phase = 2 * np.pi * np.cumsum(sub_freq) / SR
    sub = np.sin(sub_phase) * np.exp(-t * 6.5) * 0.55

    # 2. High-frequency crystalline glass / shardplink impulses
    shards = np.zeros(n)
    shard_times = [0.00, 0.015, 0.032, 0.055, 0.08, 0.11, 0.145, 0.19, 0.24, 0.31, 0.39]
    shard_freqs = [2400, 3100, 1950, 3800, 2750, 4200, 2200, 3450, 2900, 3600, 2500]
    for st, sf in zip(shard_times, shard_freqs):
        idx = int(st * SR)
        rem = n - idx
        if rem <= 0:
            continue
        ts = np.linspace(0, rem / SR, rem, endpoint=False)
        ping = (
            np.sin(2 * np.pi * sf * ts)
            + 0.45 * np.sin(2 * np.pi * (sf * 1.414) * ts)
        ) * np.exp(-ts * 28.0)
        shards[idx:] += ping * 0.18

    # 3. Filtered airy burst
    burst = rng.standard_normal(n)
    b, a = butter_bandpass(1200, 7500, SR, order=2)
    burst_f = lfilter(b, a, burst)
    burst_env = np.exp(-t * 14.0) * (1.0 - np.exp(-t * 250.0))
    burst_sig = burst_f / (np.max(np.abs(burst_f)) + 1e-6) * burst_env * 0.35

    sig_l = (sub + shards * 1.08 + burst_sig * 0.92) * vol
    sig_r = (sub + shards * 0.92 + burst_sig * 1.08) * vol
    return np.column_stack([sig_l, sig_r])


def make_soft_riser(duration=1.2, vol=0.07):
    n = int(SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq = 110.0 + 110.0 * ((t / duration) ** 2)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = (t / duration) ** 2 * np.sin(np.pi * (t / duration))
    sig = (np.sin(phase) + 0.4 * np.sin(1.5 * phase)) * env * vol
    return np.column_stack([sig * 0.95, sig * 1.05])


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
    if data.dtype == np.int16:
        voice = data.astype(np.float32) / 32768.0
    else:
        voice = data.astype(np.float32)
    if voice.ndim == 1:
        voice = np.column_stack([voice, voice])

    mix = voice.copy()

    # 1. Cutaway whooshes
    whoosh_in = make_whoosh(0.36, 150, 1900, vol=0.095)
    whoosh_out = make_whoosh(0.32, 180, 1500, vol=0.080)
    for t_in in [0.02, 4.72, 12.90, 28.20, 44.05, 53.80]:
        add_at(mix, whoosh_in, t_in)
    for t_out in [8.28, 33.40, 47.98]:
        add_at(mix, whoosh_out, t_out)

    # 2. Laptop UI Card Pops (Beat 2: 4.80 - 8.36s)
    for i, t_card in enumerate([5.02, 5.65, 6.28, 6.92]):
        add_at(mix, make_ui_pop(0.085, 480 + i * 45, 920 + i * 55, vol=0.075), t_card)

    # 3. 3D Circular Chest Badge Pops
    badge_times = [16.54, 17.92, 23.96, 25.50, 28.32, 38.92, 39.96, 51.84, 52.80]
    for i, tb in enumerate(badge_times):
        add_at(mix, make_ui_pop(0.095, 420 + (i % 2) * 110, 860 + (i % 2) * 140, vol=0.080), tb)

    # 4. 3D Circle Shatter in Cutaway #2 (29.25s: "lose their jobs")
    add_at(mix, make_shatter(0.88, vol=0.125), 29.24)
    # Crimson lockup reveal whoosh at 30.25s ("You have so much tension in the transition")
    add_at(mix, make_whoosh(0.42, 110, 1200, vol=0.09), 30.24)

    # 5. Cutaway #3 fracture into crimson reveal at 45.95s ("tend to not care so much about the people")
    add_at(mix, make_shatter(0.70, vol=0.095), 45.92)

    # 6. Finale warm swell at 53.85s ("Improve 'The Lives' of all of these people")
    add_at(mix, make_soft_riser(1.1, vol=0.065), 53.60)

    # Gentle soft limiter so peak never clips
    peak = np.max(np.abs(mix))
    if peak > 0.96:
        mix = mix * (0.96 / peak)

    out_pcm = np.clip(mix * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(MIXED_WAV, SR, out_pcm)
    print(f"Saved mixed stereo audio to {MIXED_WAV} ({len(out_pcm)/SR:.2f}s)")


if __name__ == "__main__":
    main()
