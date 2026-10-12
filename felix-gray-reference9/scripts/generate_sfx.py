#!/usr/bin/env python3
"""
Synthesizes subtle spatial whooshes, UI selection ticks, pill pop cues, and
warm atmospheric swells synchronized to the visual transitions of
`felix-gray-reference9-9x16.mp4`.
"""
import os
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100


def lowpass(sig, cutoff, sr=SR, order=3):
    b, a = butter(order, cutoff / (0.5 * sr), btype="low")
    return lfilter(b, a, sig)


def bandpass(sig, low, high, sr=SR, order=2):
    b, a = butter(order, [low / (0.5 * sr), high / (0.5 * sr)], btype="band")
    return lfilter(b, a, sig)


def place(mix, seg, t_sec, gain=1.0, pan=0.0):
    start = int(round(t_sec * SR))
    if start >= len(mix):
        return
    end = min(len(mix), start + len(seg))
    seg_part = seg[: end - start]
    l_gain = gain * np.cos((pan + 1.0) * np.pi / 4.0)
    r_gain = gain * np.sin((pan + 1.0) * np.pi / 4.0)
    mix[start:end, 0] += seg_part * l_gain
    mix[start:end, 1] += seg_part * r_gain


def make_whoosh(dur=0.28, f0=180, f1=900):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(int(dur * 1000 + f0))
    noise = rng.standard_normal(n)
    noise = bandpass(noise, min(f0, f1), max(f0, f1))
    env = np.sin(np.pi * (t / dur)) ** 2.0
    sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(f0 * 0.4, f1 * 0.3, n)) / SR)
    return (noise * 0.65 + sweep * 0.35) * env * 0.08


def make_pop(freq=560, dur=0.065):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    f = np.linspace(freq * 0.75, freq * 1.35, n)
    phase = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t * 42.0) * (1.0 - np.exp(-t * 450.0))
    return np.sin(phase) * env * 0.09


def make_click(freq=1350):
    dur = 0.024
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    env = np.exp(-t * 150.0)
    return (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2.1 * t)) * env * 0.065


def make_sub_drop(dur=0.65, f_start=92, f_end=38):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    f = np.linspace(f_start, f_end, n)
    phase = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t * 4.5) * np.minimum(1.0, t / 0.015)
    return np.sin(phase) * env * 0.11


def build_audio(raw_video_path: str, out_wav_path: str, duration: float = 54.85):
    tmp_orig = "/tmp/work_cache/brut9_orig_44k.wav"
    os.makedirs("/tmp/work_cache", exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            raw_video_path,
            "-vn",
            "-ac",
            "2",
            "-ar",
            str(SR),
            tmp_orig,
        ],
        check=True,
    )
    sr_read, orig_data = wavfile.read(tmp_orig)
    if orig_data.dtype == np.int16:
        orig = orig_data.astype(np.float32) / 32768.0
    else:
        orig = orig_data.astype(np.float32)

    total_samples = int(np.ceil(duration * SR))
    if len(orig) < total_samples:
        pad = np.zeros((total_samples - len(orig), 2), dtype=np.float32)
        orig = np.vstack([orig, pad])
    else:
        orig = orig[:total_samples]

    sfx = np.zeros_like(orig)

    # 1. Opening 3D Z-space pops & whooshes (0.00 - 5.65s)
    for t_pop, f in [(0.05, 520), (0.54, 620), (1.58, 560), (2.90, 680), (3.98, 600)]:
        place(sfx, make_pop(f), t_pop, gain=0.80, pan=-0.12)
    place(sfx, make_whoosh(0.32, 220, 980), 0.52, gain=0.75, pan=0.1)
    place(sfx, make_whoosh(0.30, 260, 880), 2.85, gain=0.75, pan=-0.1)
    place(sfx, make_sub_drop(0.45, 95, 42), 5.25, gain=0.85)

    # 2. Cutaway transitions & light leaks
    for t_cut in [5.65, 8.30, 10.75, 14.10, 17.30, 20.55, 26.85, 30.35, 35.30, 38.45, 48.95, 51.80]:
        place(sfx, make_whoosh(0.28, 200, 920), max(0.0, t_cut - 0.06), gain=0.82)

    # 3. Cream drafting-paper 3 blue pills popping in (11.05s, 12.30s, 13.10s)
    for idx, t_p in enumerate([11.05, 12.30, 13.10]):
        place(sfx, make_pop(540 + idx * 80, 0.075), t_p, gain=0.95, pan=(-0.15 + 0.15 * idx))

    # 4. UI selection box handles & cursor clicks (17.35s, 18.90s, 35.35s, 36.85s)
    for t_c in [17.38, 17.75, 18.92, 26.95, 27.60, 35.38, 36.90]:
        place(sfx, make_click(1420), t_c, gain=0.85)

    # 5. Pull-back window-in-black finale ("14" / "ARCHITECT", 48.95s & 50.50s)
    place(sfx, make_sub_drop(0.60, 96, 38), 48.95, gain=0.95)
    place(sfx, make_pop(680, 0.08), 49.40, gain=0.90)
    place(sfx, make_pop(740, 0.08), 50.50, gain=0.90)

    combined = orig * 1.04 + sfx * 0.85
    peak = np.max(np.abs(combined))
    if peak > 0.98:
        combined = combined * (0.98 / peak)

    out_i16 = np.clip(combined * 32767.0, -32768, 32767).astype(np.int16)
    os.makedirs(os.path.dirname(out_wav_path), exist_ok=True)
    wavfile.write(out_wav_path, SR, out_i16)
    print(f"Wrote mixed stereo audio to {out_wav_path} ({duration:.2f}s)")


if __name__ == "__main__":
    build_audio(
        "/home/user/COOL-backup/video brut 9.mp4",
        "/tmp/work_cache/felix_ref9_audio.wav",
    )
