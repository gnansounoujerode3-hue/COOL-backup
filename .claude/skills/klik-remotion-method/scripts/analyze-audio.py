#!/usr/bin/env python3
"""Klik method — dependency-free music analysis (discovery §7).

Pure stdlib + ffmpeg (bundled with Remotion / present on most systems).
No numpy, no aubio — by design: this runs anywhere the method runs.

  python3 analyze-audio.py track.mp3 [--fps 30] [--json out.json] [--stems auto|off|<dir>]

OPTIONAL stem separation (--stems auto, the default): if `demucs` is
installed (pip install demucs — needs torch), the track is split into
vocals/drums/bass/guitar/piano/other first and every source is analyzed
separately — kick/snare/hats come from the isolated drums stem, so vocals
and guitar no longer read as percussion. Without demucs the script degrades
gracefully to 3-band splitting and says so. Pre-split stems can be passed
as --stems <dir>.

Two layers of output:

1. THE GRID — BPM (autocorrelation + whole-track grid-alignment refinement),
   first beat & downbeat (seconds AND frames), frames-per-beat constants.
2. THE MUSIC MAP — what klik-anim §A16 / klik-cam CAM-5 consume: sections
   with energy tier (1–5), spectral balance (bass/mid/high), transient
   density, attack & sustain character, and per-source rhythm patterns on a
   16th-note grid (kick/snare/hats/vocals/bass/guitar/piano in stem mode;
   low/mid/high bands otherwise). The JSON adds `events` (per-source
   transient frames) and `levels` (per-frame source energy) — deterministic
   reactive data a composition can consume directly.

Paste the summary into SSOT §7, then VERIFY against a few hand-counted beats
before trusting the grid — and sanity-check the map by ear (does the detected
drop sound like the drop?).
"""
import argparse, array, json, math, os, shutil, subprocess, sys, tempfile, wave

SR = 11025          # full-band decode rate — plenty for onset timing
HOP = 128           # ~86 envelope points/sec → beat timing to ~±12 ms
SR_B = 22050        # band decode rate (high band needs Nyquist > 6 kHz)
HOP_B = 256         # 22050/256 == 11025/128 → band envelopes align 1:1

BANDS = [           # name, ffmpeg filter, what it carries (band-mode fallback)
    ("low",  "lowpass=f=150",                 "kick / bass"),
    ("mid",  "highpass=f=400,lowpass=f=4000", "snare / vocals / melody"),
    ("high", "highpass=f=6000",               "hats / cymbals / sizzle"),
]

# Within the isolated DRUMS stem, the same band trick is now clean:
KIT = [
    ("kick",  "lowpass=f=150"),
    ("snare", "highpass=f=200,lowpass=f=4000"),
    ("hats",  "highpass=f=6000"),
]
STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")
STEM_LABEL = {"kick": "kick (drums stem)", "snare": "snare (drums stem)",
              "hats": "hats (drums stem)", "vocals": "vocals", "bass": "bass",
              "guitar": "guitar", "piano": "piano", "other": "other instr."}


def scan_stem_dir(d):
    found = {}
    for root, _, files in os.walk(d):
        for f in files:
            base, ext = os.path.splitext(f)
            if base.lower() in STEM_NAMES and ext.lower() in (".wav", ".mp3", ".flac"):
                found[base.lower()] = os.path.join(root, f)
    return found


def find_stems(mode, track):
    """Resolve stems: 'off' → band mode · a directory → use its stem files ·
    'auto' → run demucs if installed, else fall back to band mode.

    Stem separation needs an ML model — it can never be stdlib-only, so it is
    an OPTIONAL stage with graceful degradation: without it, band-splitting
    conflates vocals/guitar transients with percussion (a known field defect).
    """
    if mode == "off":
        return None, "band mode (--stems off)"
    if mode != "auto":
        stems = scan_stem_dir(mode)
        if not stems:
            sys.exit(f"--stems {mode}: no vocals/drums/bass/… stem files found there")
        return stems, f"stems from {mode}"
    demucs = os.environ.get("DEMUCS_BIN") or shutil.which("demucs")
    if not demucs:
        return None, ("band mode — demucs not found. For true stems (vocals/"
                      "drums/bass/guitar/piano): pip install demucs, or pass "
                      "--stems <dir> of pre-split files.")
    outdir = tempfile.mkdtemp(prefix="klik-stems-")
    for model in ("htdemucs_6s", "htdemucs"):
        try:
            subprocess.run([demucs, "-n", model, "-o", outdir, track], check=True)
        except subprocess.CalledProcessError:
            continue
        stems = scan_stem_dir(outdir)
        if stems:
            return stems, f"stems via demucs {model} → {outdir}"
    return None, "band mode (demucs ran but produced no stems)"


def decode(path, sr=SR, af=None):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(sr)]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "wav", tmp.name]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("ffmpeg not found on PATH — install it or use `npx remotion ffmpeg`.")
    except subprocess.CalledProcessError:
        sys.exit(f"ffmpeg could not decode {path!r}")
    with wave.open(tmp.name, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    os.unlink(tmp.name)
    samples = array.array("h")
    samples.frombytes(raw)
    return samples


def envelopes(samples, hop=HOP):
    """Per-hop mean |amplitude| (energy) and half-wave-rectified flux (onset)."""
    n = len(samples) // hop
    energy = []
    for i in range(n):
        seg = samples[i * hop:(i + 1) * hop]
        acc = 0
        for s in seg:
            acc += s if s >= 0 else -s
        energy.append(acc / (hop * 32768.0))
    onset = [0.0]
    for i in range(1, n):
        d = energy[i] - energy[i - 1]
        onset.append(d if d > 0.0 else 0.0)
    sm = [0.0] * n                                   # 3-point smooth
    for i in range(n):
        a, b = max(0, i - 1), min(n, i + 2)
        sm[i] = sum(onset[a:b]) / (b - a)
    return sm, energy


def detect_bpm(onset, hps, lo=60.0, hi=200.0):
    n = len(onset)
    mean = sum(onset) / n
    x = [v - mean for v in onset]
    lmin, lmax = int(hps * 60.0 / hi), int(hps * 60.0 / lo) + 2
    scores = {}
    for lag in range(lmin, lmax):
        s = 0.0
        for i in range(n - lag):
            s += x[i] * x[i + lag]
        scores[lag] = s / (n - lag)
    best = max(scores, key=scores.get)

    def refined(lag):                                # parabolic sub-hop peak
        if lag - 1 in scores and lag + 1 in scores:
            y0, y1, y2 = scores[lag - 1], scores[lag], scores[lag + 1]
            den = y0 - 2 * y1 + y2
            if den:
                return lag + 0.5 * (y0 - y2) / den
        return float(lag)

    lag_f = refined(best)
    bpm = 60.0 * hps / lag_f
    folded = bpm
    while folded < 90.0:
        folded *= 2.0
    while folded >= 180.0:
        folded /= 2.0
    conf = scores[best] / (sum(abs(v) for v in scores.values()) / len(scores) + 1e-12)
    return folded, conf


def refine_bpm(onset, hps, bpm0, span=1.5, step=0.01):
    """Full-track grid-alignment refinement around the autocorrelation BPM.

    Tempo error is cumulative — a 0.5% error drifts a full beat by the tail —
    so scoring onset alignment across the WHOLE track disambiguates candidates
    the (windowed, sub-hop-limited) autocorrelation peak cannot. Field case:
    autocorrelation reported 139.36 where truth was 140.000; whole-track
    alignment separates them decisively.
    """
    n = len(onset)
    best_bpm, best_s = bpm0, -1.0
    cand = bpm0 - span
    while cand <= bpm0 + span + 1e-9:
        period = 60.0 * hps / cand
        s_best = -1.0
        off = 0.0
        while off < period:                      # coarse best phase per candidate
            s, t, k = 0.0, off, 0
            while t < n:
                i = int(t + 0.5)
                if i < n:
                    s += onset[i]
                    k += 1
                t += period
            if k:
                s /= k
            if s > s_best:
                s_best = s
            off += period / 8.0
        if s_best > best_s:
            best_s, best_bpm = s_best, cand
        cand += step
    return best_bpm


def align(onset, energy, period):
    """Best beat phase, then best of 4 bar phases → first downbeat."""
    n = len(onset)

    def grid_score(seq, offset, step):
        s, t = 0.0, offset
        while t < n:
            i = int(t + 0.5)
            if i < n:
                s += seq[i]
            t += step
        return s

    best_off, best_s = 0.0, -1.0
    off = 0.0
    while off < period:
        s = grid_score(onset, off, period)
        if s > best_s:
            best_off, best_s = off, s
        off += 0.25
    beat0 = best_off
    best_db, best_e = 0, -1.0
    for db in range(4):
        e = grid_score(energy, beat0 + db * period, period * 4)
        if e > best_e:
            best_db, best_e = db, e
    return beat0, beat0 + best_db * period


# ───────────────────────────── the music map ─────────────────────────────

def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    return sorted_vals[min(len(sorted_vals) - 1, int(p * len(sorted_vals)))]


def find_peaks(onset, energy, min_gap=4, prominence=2.2):
    """Local onset maxima that are real transients → hop indices.

    Three gates, all verified against phantom-pattern failures:
    - relative threshold (0.30 × p95 of flux) — scales to the band's loudness;
    - absolute floor tied to the band's ENERGY (a steady pad has near-zero
      flux; without a floor, quantization ripple becomes an all-16ths pattern);
    - PROMINENCE over the local ±110ms neighborhood — a transient is a flux
      spike sparse in time; a beating/chorused pad produces *continuous* flux
      that clears any level threshold but never stands clear of its own
      surroundings.
    """
    n = len(onset)
    th = max(0.30 * pct(sorted(onset), 0.95),
             0.04 * pct(sorted(energy), 0.95))
    pre = [0.0]                                       # prefix sums → local mean
    for v in onset:
        pre.append(pre[-1] + v)
    out, last = [], -min_gap
    W = 9
    for i in range(2, n - 2):
        v = onset[i]
        if v <= th or v != max(onset[i - 2:i + 3]) or i - last < min_gap:
            continue
        a, b = max(0, i - W), min(n, i + W + 1)
        local_mean = (pre[b] - pre[a]) / (b - a)
        if v > prominence * local_mean:
            out.append(i)
            last = i
    return out


def bar_starts(downbeat, period, n):
    out, t = [], downbeat
    while t + 4 * period <= n:
        out.append(t)
        t += 4 * period
    return out


def attack_ms(onset, peak, hop_ms):
    """Rise time: hops from 20% of peak value up to the peak."""
    v = onset[peak]
    j = peak
    while j > 0 and onset[j - 1] < onset[j] and onset[j - 1] > 0.2 * v:
        j -= 1
    return (peak - j + 1) * hop_ms


def sustain_ms(energy, peak, hop_ms):
    """Time until energy falls below half its value at the peak."""
    v = energy[min(peak, len(energy) - 1)]
    j = peak
    lim = min(len(energy), peak + int(1200 / hop_ms))
    while j < lim and energy[j] > 0.5 * v:
        j += 1
    return (j - peak) * hop_ms


def slot16(h, bar_start, period):
    """Hop index → 16th-note slot 0–15 within its bar."""
    pos = (h - bar_start) / (period / 4.0)
    return int(pos + 0.5) % 16


def pattern_string(band_peaks, bars, period, bar_lo, bar_hi):
    """Presence-per-slot over a bar range → 'X x . .' 16-char pattern."""
    nbars = bar_hi - bar_lo
    if nbars <= 0:
        return "." * 16
    hist = [0] * 16
    lo_h, hi_h = bars[bar_lo], bars[bar_hi - 1] + 4 * period
    for h in band_peaks:
        if lo_h <= h < hi_h:
            b = int((h - bars[bar_lo]) / (4 * period))
            hist[slot16(h, bars[bar_lo] + b * 4 * period, period)] += 1
    out = []
    for c in hist:
        f = c / nbars
        out.append("X" if f >= 0.5 else ("x" if f >= 0.25 else "."))
    return "".join(out)


def build_map(full_onset, full_energy, bands_env, bars, period, hps, fps, down0,
              pattern_env=None):
    """pattern_env: {name: (onset, energy)} used for the per-section rhythm
    patterns. Defaults to the mix bands; in stem mode it's the per-source
    envelopes (kick/snare/hats from the drums stem, vocals, bass, …)."""
    hop_ms = 1000.0 / hps
    nb = len(bars)
    if nb < 2:
        return [], []

    # per-bar features
    def bar_sum(seq, b):
        a, z = int(bars[b]), int(min(len(seq), bars[b] + 4 * period))
        seg = seq[a:z]
        return sum(seg) / max(1, len(seg))

    e_bars = [bar_sum(full_energy, b) for b in range(nb)]
    ranked = sorted(e_bars)
    tiers = []
    for e in e_bars:                                  # energy tier 1–5 by percentile
        t = 1 + sum(1 for q in (0.2, 0.4, 0.6, 0.8) if e > pct(ranked, q))
        tiers.append(t)

    bal = []                                          # low/mid/high fractions per bar
    for b in range(nb):
        vals = [bar_sum(bands_env[name][1], b) for name, _, _ in BANDS]
        tot = sum(vals) + 1e-12
        bal.append([v / tot for v in vals])

    full_peaks = find_peaks(full_onset, full_energy)
    dens = [0.0] * nb                                 # transients/sec per bar
    bar_sec = 4 * period / hps
    for h in full_peaks:
        b = int((h - bars[0]) / (4 * period))
        if 0 <= b < nb:
            dens[b] += 1
    dens = [d / bar_sec for d in dens]

    # section boundaries: sustained change in tier or bass balance
    sections, start = [], 0
    for b in range(2, nb - 1):
        if b - start < 4:
            continue
        t_prev = sum(tiers[max(0, b - 2):b]) / 2.0
        t_next = sum(tiers[b:b + 2]) / 2.0
        l_prev = sum(x[0] for x in bal[max(0, b - 2):b]) / 2.0
        l_next = sum(x[0] for x in bal[b:b + 2]) / 2.0
        if abs(t_next - t_prev) >= 1.5 or abs(l_next - l_prev) >= 0.22:
            sections.append((start, b))
            start = b
    sections.append((start, nb))

    if pattern_env is None:
        pattern_env = {name: bands_env[name] for name, _, _ in BANDS}
    pat_peaks = {name: find_peaks(o, e) for name, (o, e) in pattern_env.items()}

    rows = []
    for lo, hi in sections:
        seg_peaks = [h for h in full_peaks if bars[lo] <= h < bars[hi - 1] + 4 * period]
        if seg_peaks:
            atk = sorted(attack_ms(full_onset, h, hop_ms) for h in seg_peaks)
            sus = sorted(sustain_ms(full_energy, h, hop_ms) for h in seg_peaks)
            a_med, s_med = pct(atk, 0.5), pct(sus, 0.5)
            a_char = "sharp" if a_med < 35 else ("medium" if a_med < 90 else "soft")
            s_char = "staccato" if s_med < 150 else ("held" if s_med < 400 else "sustained")
            attack_str = f"{a_char} (~{int(a_med)}ms)"
            sustain_str = f"{s_char} (~{int(s_med)}ms)"
        else:
            attack_str = sustain_str = "— (no transients: swell/pad territory)"
        t_avg = sum(tiers[lo:hi]) / (hi - lo)
        b_avg = [sum(x[i] for x in bal[lo:hi]) / (hi - lo) for i in range(3)]
        lead = ("bass", "mid", "high")[b_avg.index(max(b_avg))]
        rows.append({
            "bars": [lo, hi],
            "start_s": round(bars[lo] / hps, 3),
            "start_frame": round(bars[lo] / hps * fps),
            "tier": round(t_avg, 1),
            "balance": {"low": round(b_avg[0], 2), "mid": round(b_avg[1], 2), "high": round(b_avg[2], 2)},
            "lead": lead,
            "transients_per_s": round(sum(dens[lo:hi]) / (hi - lo), 2),
            "attack": attack_str,
            "sustain": sustain_str,
            "pattern": {name: pattern_string(pat_peaks[name], bars, period, lo, hi)
                        for name in pattern_env},
        })
    tier_strip = "".join(str(t) for t in tiers)
    return rows, tier_strip


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("track")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--json", help="also write full results to this path")
    ap.add_argument("--stems", default="auto",
                    help="'auto' (run demucs if installed) · 'off' (band mode) "
                         "· or a directory of pre-split stem files "
                         "(vocals/drums/bass/guitar/piano/other .wav)")
    a = ap.parse_args()

    samples = decode(a.track)
    dur = len(samples) / SR
    onset, energy = envelopes(samples)
    hps = SR / HOP
    bpm, conf = detect_bpm(onset, hps)
    bpm = refine_bpm(onset, hps, bpm)                # whole-track grid alignment
    period = 60.0 * hps / bpm
    alt = bpm / 2.0 if bpm / 2.0 >= 45.0 else bpm * 2.0
    beat0_h, down0_h = align(onset, energy, period)
    beat0, down0 = beat0_h / hps, down0_h / hps
    fpb = 60.0 / bpm * a.fps

    bands_env = {}
    for name, af, _ in BANDS:                        # mix bands: balance + fallback
        bands_env[name] = envelopes(decode(a.track, SR_B, af), HOP_B)

    stems, stem_note = find_stems(a.stems, a.track)
    sources = None                                   # {name: (onset, energy)}
    if stems:
        sources = {}
        if "drums" in stems:                         # clean K/S/H from the kit
            for name, af in KIT:
                sources[name] = envelopes(decode(stems["drums"], SR_B, af), HOP_B)
        for name in ("bass", "vocals", "guitar", "piano", "other"):
            if name in stems:
                sources[name] = envelopes(decode(stems[name], SR_B), HOP_B)

    bars = bar_starts(down0_h, period, len(onset))
    e_bars = []
    t = down0_h
    while t + 4 * period <= len(energy):
        seg = energy[int(t):int(t + 4 * period)]
        e_bars.append(sum(seg) / max(1, len(seg)))
        t += 4 * period
    drops = sorted(
        ({"bar": i, "time_s": round(down0 + i * 4 * 60.0 / bpm, 2),
          "delta": round(e_bars[i] - e_bars[i - 1], 4)}
         for i in range(1, len(e_bars))),
        key=lambda d: -d["delta"])[:3]

    map_rows, tier_strip = build_map(onset, energy, bands_env, bars, period,
                                     hps, a.fps, down0, pattern_env=sources)

    # Deterministic reactive data for builds (JSON only): transient frames per
    # source + per-video-frame normalized levels. Lets a comp light up on the
    # SAME detections the map was built from — pure function of frame (A0).
    react_env = sources if sources else {name: bands_env[name] for name, _, _ in BANDS}
    react_peaks = {name: find_peaks(o, e) for name, (o, e) in react_env.items()}
    nframes = int(dur * a.fps)

    def levels(seq):
        peak = max(seq) or 1.0
        return [round(seq[min(len(seq) - 1, int(f / a.fps * hps))] / peak, 3)
                for f in range(nframes)]

    events = {name: [round(h / hps * a.fps) for h in react_peaks[name]]
              for name in react_env}
    events["full"] = [round(h / hps * a.fps) for h in
                      find_peaks(onset, energy)]
    levels_out = {name: levels(react_env[name][1]) for name in react_env}
    levels_out["full"] = levels(energy)

    out = {
        "track": os.path.basename(a.track), "duration_s": round(dur, 2),
        "bpm": round(bpm, 2), "alt_bpm": round(alt, 2),
        "confidence": round(conf, 2), "fps": a.fps,
        "first_beat_s": round(beat0, 3), "first_downbeat_s": round(down0, 3),
        "first_beat_frame": round(beat0 * a.fps),
        "first_downbeat_frame": round(down0 * a.fps),
        "frames_per_beat": round(fpb, 4),
        "drops": [dict(d, frame=round(d["time_s"] * a.fps)) for d in drops],
        "energy_tier_per_bar": tier_strip,
        "mode": "stems" if sources else "bands",
        "stem_note": stem_note,
        "music_map": map_rows,
        "events": events,
        "levels": levels_out,
    }
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=2)

    print(f"track          {out['track']}  ({out['duration_s']}s)")
    print(f"BPM            {out['bpm']}  (alternate: {out['alt_bpm']}, confidence {out['confidence']})")
    print(f"first beat     {out['first_beat_s']}s  → f{out['first_beat_frame']} @ {a.fps:g}fps")
    print(f"first downbeat {out['first_downbeat_s']}s  → f{out['first_downbeat_frame']}")
    print(f"motion.ts      FRAMES_PER_BEAT = {out['frames_per_beat']}; "
          f"beat(n) = round({out['first_downbeat_frame']} + n * FRAMES_PER_BEAT)")
    for d in out["drops"]:
        print(f"energy jump    bar {d['bar']}  @ {d['time_s']}s (f{d['frame']})  ΔE {d['delta']}")

    print(f"\nSOURCES        {stem_note}")
    print(f"MUSIC MAP      (energy tier per bar: {tier_strip})")
    band_carries = {name: carries for name, _, carries in BANDS}
    for r in map_rows:
        b = r["balance"]
        print(f"  bars {r['bars'][0]:>2}–{r['bars'][1]:<2} @ {r['start_s']:>7.2f}s f{r['start_frame']:<6}"
              f" tier {r['tier']}  lead {r['lead']:<4} (L{b['low']:.2f}/M{b['mid']:.2f}/H{b['high']:.2f})"
              f"  {r['transients_per_s']}/s  attack {r['attack']}  sustain {r['sustain']}")
        for name, pat in r["pattern"].items():
            label = STEM_LABEL.get(name, band_carries.get(name, name))
            print(f"      {name:<6} |{pat}|  ({label})")
    print("\n16th-grid legend: X ≥50% of bars · x ≥25% · slots 1–16, downbeat first.")
    print("Feed the map to klik-anim §A16 (motion character) and klik-cam CAM-5")
    print("(camera). VERIFY: hand-count 4 beats at two points; check the loudest")
    print("detected section IS the drop by ear before building to it. Bar phase")
    print("(which slot is beat 1) is a guess when the intro lacks accents — the")
    print("patterns may be rotated by a constant offset; confirm against the kick.")
    if out["confidence"] < 1.5:
        print("NOTE: low confidence — ambient/sparse track; confirm BPM by ear.")


if __name__ == "__main__":
    main()
