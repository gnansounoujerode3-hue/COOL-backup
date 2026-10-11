#!/usr/bin/env python3
"""Generates dark atmospheric synth music + precision motion-graphics SFX
inspired by REFERENCE 6.mp4, and masters the final mix at -14.0 LUFS.
"""
import os
import subprocess
import sys
import wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import DURATION, TRANSITION_TIMES, load_words

SR = 44100
N = int(SR * DURATION)
CACHE_DIR = "/home/user/.cache/fg_audio"
os.makedirs(CACHE_DIR, exist_ok=True)

rng = np.random.default_rng(108)


def lp(x, cutoff):
    a = np.exp(-2.0 * np.pi * cutoff / SR)
    from scipy.signal import lfilter
    return lfilter([1.0 - a], [1.0, -a], x)


def hp(x, cutoff):
    return x - lp(x, cutoff)


def adsr(n, a, d, sustain, r):
    t = np.arange(n, dtype=np.float32) / SR
    dur = n / SR
    env = np.clip(t / max(a, 1e-4), 0.0, 1.0)
    env *= 1.0 - (1.0 - sustain) * np.clip((t - a) / max(d, 1e-4), 0.0, 1.0)
    rel = np.clip((t - max(0.0, dur - r)) / max(r, 1e-4), 0.0, 1.0)
    return env * (1.0 - rel)


def place(buf, sig, t_start, gain=1.0):
    i0 = max(0, int(round(t_start * SR)))
    i1 = min(len(buf), i0 + len(sig))
    if i1 > i0:
        buf[i0:i1] += sig[:i1 - i0] * gain


def synth_pad_note(freq, dur):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    # Warm detuned dark synth pad (Cm9 / Abmaj7 / Fm9 / G7sus4)
    sig = (
        0.55 * np.sin(2 * np.pi * freq * t)
        + 0.25 * np.sin(2 * np.pi * (freq * 1.003) * t + 0.4)
        + 0.14 * np.sin(2 * np.pi * (freq * 2.0) * t + 1.1)
        + 0.06 * np.sin(2 * np.pi * (freq * 0.5) * t)
    )
    return sig * adsr(n, 0.85, 1.2, 0.72, 1.1)


def synth_pluck(freq, dur=0.55):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = (
        np.sin(2 * np.pi * freq * t)
        + 0.35 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t * 7.5)
        + 0.15 * np.sin(2 * np.pi * freq * 3.0 * t) * np.exp(-t * 12.0)
    )
    return sig * np.exp(-t * 5.2) * np.minimum(t / 0.008, 1.0)


def synth_sub_pulse(freq, dur=0.65):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f_env = freq * (1.0 + 0.45 * np.exp(-t * 24.0))
    sig = np.sin(2 * np.pi * f_env * t) + 0.22 * np.sin(4 * np.pi * freq * t)
    return sig * np.exp(-t * 4.5) * np.minimum(t / 0.006, 1.0)


def build_music():
    music = np.zeros(N, dtype=np.float32)
    bpm = 92.0
    beat = 60.0 / bpm
    bar = 4.0 * beat

    # Cm9 -> Abmaj7 -> Fm9 -> G7sus4 (modern dark editorial progression)
    chords = [
        (65.41, [130.81, 155.56, 196.00, 233.08, 293.66]),
        (51.91, [103.83, 155.56, 196.00, 246.94, 311.13]),
        (43.65, [130.81, 174.61, 207.65, 261.63, 349.23]),
        (49.00, [130.81, 146.83, 196.00, 246.94, 293.66]),
    ]
    arp_pattern = [0, 2, 4, 1, 3, 4, 2, 1]

    t_bar = 0.0
    ci = 0
    while t_bar < DURATION:
        bass_f, notes = chords[ci % len(chords)]
        for k, fn in enumerate(notes):
            place(music, synth_pad_note(fn, bar * 1.08), t_bar + k * 0.04, 0.065)
        # Sub bass on beat 1 and beat 2.5
        place(music, synth_sub_pulse(bass_f, beat * 1.4), t_bar, 0.16)
        place(music, synth_sub_pulse(bass_f, beat * 1.1), t_bar + 2.5 * beat, 0.11)
        # Subtle muted synth arpeggio on eighth notes
        for step in range(8):
            fn = notes[arp_pattern[step] % len(notes)]
            place(music, synth_pluck(fn * 2.0, 0.42), t_bar + step * (beat / 2.0), 0.028)
        t_bar += bar
        ci += 1

    # Fade in & out
    t_all = np.arange(N, dtype=np.float32) / SR
    fade = np.clip(t_all / 0.8, 0.0, 1.0) * np.clip((DURATION - t_all) / 0.9, 0.0, 1.0)
    music *= fade
    return music


def sfx_whoosh(dur=0.36, f_low=180.0, f_high=1100.0):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0.0, 1.0)) ** 2.2
    noise = lp(hp(rng.standard_normal(n).astype(np.float32), f_low), f_high)
    noise /= max(1e-6, np.max(np.abs(noise)))
    sweep = np.sin(2 * np.pi * (140.0 + 360.0 * (t / dur)) * t) * 0.25
    return (noise * 0.75 + sweep) * env


def sfx_ui_pop(freq=680.0, dur=0.09):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f_inst = freq * (1.0 + 0.65 * np.exp(-t * 55.0))
    sig = np.sin(2 * np.pi * f_inst * t) * np.exp(-t * 38.0)
    return sig * np.minimum(t / 0.003, 1.0)


def sfx_chime(freq, dur=1.15):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = (
        0.70 * np.sin(2 * np.pi * freq * t)
        + 0.20 * np.sin(2 * np.pi * freq * 2.756 * t) * np.exp(-t * 4.0)
        + 0.10 * np.sin(2 * np.pi * freq * 5.404 * t) * np.exp(-t * 7.0)
    )
    return sig * np.exp(-t * 2.6) * np.minimum(t / 0.004, 1.0)


def sfx_sonar(freq=392.0, dur=0.75):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    sig = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 1.5 * t)
    return sig * np.exp(-t * 3.8) * np.minimum(t / 0.012, 1.0)


def sfx_shatter(dur=1.15):
    """3D polygon shatter sound: initial low impact + cascading crystalline/polygon debris clicks."""
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    t = np.arange(n, dtype=np.float32) / SR
    # Initial fracture punch
    punch = np.sin(2 * np.pi * (160.0 * np.exp(-t * 22.0) + 48.0) * t) * np.exp(-t * 12.0)
    burst = hp(rng.standard_normal(n).astype(np.float32), 1800.0) * np.exp(-t * 16.0)
    burst /= max(1e-6, np.max(np.abs(burst)))
    out += 0.65 * punch + 0.45 * burst

    # 28 micro-shard clicks scattering over 0.05..0.95s
    for _ in range(28):
        dt = rng.uniform(0.03, 0.88)
        f_shard = rng.uniform(1200.0, 4200.0)
        i0 = int(dt * SR)
        L = int(0.035 * SR)
        if i0 + L < n:
            ts = np.arange(L, dtype=np.float32) / SR
            cl = (
                np.sin(2 * np.pi * f_shard * ts)
                + 0.5 * np.sin(2 * np.pi * f_shard * 1.62 * ts)
            ) * np.exp(-ts * 95.0)
            out[i0:i0 + L] += cl * rng.uniform(0.12, 0.32)
    out /= max(1e-6, np.max(np.abs(out)))
    return out


def build_sfx():
    sfx = np.zeros(N, dtype=np.float32)

    # 1. Whooshes on all transitions and cutaways
    for tc in TRANSITION_TIMES:
        is_cutaway = any(abs(tc - c) < 0.05 for c in (12.10, 16.45, 25.15, 30.05, 42.25, 46.63))
        place(sfx, sfx_whoosh(0.42 if is_cutaway else 0.30), tc - 0.18, 0.34 if is_cutaway else 0.20)

    # 2. UI pops on lockups & counter increments
    pop_times = [
        (0.02, 620), (0.65, 760), (0.72, 920), (1.45, 840), (1.52, 1040),
        (2.85, 640), (3.68, 780), (3.92, 980), (4.30, 880),
        (6.80, 620), (7.72, 720), (8.58, 840), (9.32, 960),
        (10.75, 620), (11.24, 740), (11.52, 520),
        (16.45, 660), (17.70, 780), (18.22, 920),
        (19.15, 620), (20.75, 740), (21.38, 520),
        (23.15, 660), (24.22, 780), (24.58, 920),
        (30.05, 660), (30.95, 780), (31.42, 920),
        (32.05, 640), (32.25, 760), (32.42, 880),
        (33.30, 740), (34.10, 880), (35.60, 760), (36.68, 900),
        (37.80, 720), (39.38, 840), (40.15, 680), (41.35, 920),
    ]
    for tp, fq in pop_times:
        place(sfx, sfx_ui_pop(fq), tp, 0.24)

    # 3. Cutaway #1 notification card chime & counter ticks (12.10 - 16.45s)
    place(sfx, sfx_chime(587.33, 0.9), 12.14, 0.24)
    place(sfx, sfx_chime(880.00, 0.9), 12.22, 0.18)
    for tc_tick in (13.18, 14.25, 15.32):
        place(sfx, sfx_ui_pop(980), tc_tick, 0.18)

    # 4. 3D Squircle Shatter Explosion at 21.74s ("random")
    place(sfx, sfx_shatter(1.15), 21.72, 0.58)

    # 5. Cutaway #2: Central FG Orb Sonar Ripples (25.18 - 26.50s) + 3 Orbital Node Chimes (27.08, 28.22, 29.18s)
    for delay, fq in [(25.20, 261.63), (25.42, 329.63), (25.68, 392.00)]:
        place(sfx, sfx_sonar(fq, 0.85), delay, 0.25)
    place(sfx, sfx_ui_pop(840), 26.85, 0.24)  # Orbit ring draw
    place(sfx, sfx_chime(523.25, 1.1), 27.08, 0.28)  # Node 1: READING
    place(sfx, sfx_chime(659.25, 1.1), 28.22, 0.28)  # Node 2: PLANNING
    place(sfx, sfx_chime(783.99, 1.2), 29.18, 0.30)  # Node 3: LAPTOP

    # 6. Cutaway #3: Question word-by-word subtle ticks (42.60 - 46.26s)
    q_times = [42.60, 42.82, 43.00, 43.24, 43.80, 44.10, 44.26, 44.40, 44.82, 45.20, 45.44, 45.68, 46.00, 46.26]
    for qt in q_times:
        place(sfx, sfx_ui_pop(1120, 0.05), qt, 0.12)

    # 7. Final CTA Lockup Impact + Shimmer (46.66s & 46.92s)
    place(sfx, sfx_ui_pop(740), 46.66, 0.25)
    place(sfx, synth_sub_pulse(55.0, 1.4), 46.92, 0.48)
    for k, fq in enumerate([392.00, 493.88, 587.33, 783.99]):
        place(sfx, sfx_chime(fq, 1.5), 46.94 + k * 0.05, 0.16)
    place(sfx, sfx_ui_pop(920), 48.12, 0.24)

    return sfx


def save_wav(path, sig, peak=0.85):
    m = np.max(np.abs(sig))
    if m > 1e-6:
        sig = sig / m * peak
    stereo = np.stack([sig, sig], axis=1)
    pcm = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    raw_video = os.path.join(repo_root, "video brut 5 - Copie.mp4")

    music_wav = os.path.join(CACHE_DIR, "music.wav")
    sfx_wav = os.path.join(CACHE_DIR, "sfx.wav")
    voice_norm = os.path.join(CACHE_DIR, "voice_norm.wav")
    music_duck = os.path.join(CACHE_DIR, "music_duck.wav")
    mix_wav = os.path.join(CACHE_DIR, "mix.wav")

    print("1/4 Synthesizing dark atmospheric music & precision SFX...")
    save_wav(music_wav, build_music(), peak=0.50)
    save_wav(sfx_wav, build_sfx(), peak=0.65)

    print("2/4 Mastering original voice track (EQ + compression + -14 LUFS)...")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", raw_video,
        "-af", (
            "highpass=f=85,"
            "equalizer=f=250:t=q:w=1.1:g=-2.4,"
            "equalizer=f=3200:t=q:w=1.2:g=2.4,"
            "equalizer=f=7000:t=q:w=1.4:g=1.2,"
            "acompressor=threshold=-20dB:ratio=2.8:attack=6:release=200:makeup=2,"
            "loudnorm=I=-14:TP=-1.5:LRA=10"
        ),
        "-ar", "48000", "-ac", "2", voice_norm
    ], check=True)

    print("3/4 Sidechain-ducking music under voice...")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", music_wav, "-i", voice_norm,
        "-filter_complex",
        "[0:a]aresample=48000,volume=0.30[m];[m][1:a]sidechaincompress=threshold=0.025:ratio=6.5:attack=18:release=400[d]",
        "-map", "[d]", "-ar", "48000", "-ac", "2", music_duck
    ], check=True)

    print("4/4 Final broadcast mix (-14.0 LUFS / -1.5 dBTP)...")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", voice_norm, "-i", music_duck, "-i", sfx_wav,
        "-filter_complex",
        "[2:a]aresample=48000,volume=0.52[s];[0:a][1:a][s]amix=inputs=3:duration=first:normalize=0[mx];"
        "[mx]alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=10[out]",
        "-map", "[out]", "-ar", "48000", "-ac", "2", "-t", str(DURATION), mix_wav
    ], check=True)
    print("Master audio mix ready:", mix_wav)


if __name__ == "__main__":
    main()
