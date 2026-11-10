"""Reusable rendering + audio helpers for the Léger Akodjenou marketing film.

Everything is drawn natively with Pillow / numpy: glass cards, browser mockups,
vector icons, gradient glows and a synthetic score (no licensed assets needed).
"""
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
SR = 48000

FONT_BASE = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
FONT_PATHS = {
    "xb": f"{FONT_BASE}/plus-jakarta-sans/800ExtraBold/PlusJakartaSans_800ExtraBold.ttf",
    "b": f"{FONT_BASE}/plus-jakarta-sans/700Bold/PlusJakartaSans_700Bold.ttf",
    "sb": f"{FONT_BASE}/plus-jakarta-sans/600SemiBold/PlusJakartaSans_600SemiBold.ttf",
    "m": f"{FONT_BASE}/plus-jakarta-sans/500Medium/PlusJakartaSans_500Medium.ttf",
    "ir": f"{FONT_BASE}/inter/400Regular/Inter_400Regular.ttf",
    "im": f"{FONT_BASE}/inter/500Medium/Inter_500Medium.ttf",
    "isb": f"{FONT_BASE}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "ib": f"{FONT_BASE}/inter/700Bold/Inter_700Bold.ttf",
}

# ---------------------------------------------------------------- palette
INK = (7, 6, 14)
VIOLET = (124, 92, 255)
VIOLET_SOFT = (150, 124, 255)
MINT = (34, 211, 166)
AMBER = (255, 184, 77)
ROSE = (255, 104, 148)
TEXT = (245, 243, 255)
MUTED = (160, 155, 186)
DIM = (108, 103, 134)

# ---------------------------------------------------------------- easing


def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def lerp(a, b, t):
    return a + (b - a) * t


def eo(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ei(t):
    t = clamp01(t)
    return t ** 3


def eio(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def eob(t):
    """Strong ease-out (quint) for snappy entrances."""
    t = clamp01(t)
    return 1 - (1 - t) ** 5


def spring(t):
    t = clamp01(t)
    return 1 - math.exp(-7.5 * t) * math.cos(13.0 * t)


def prog(lt, start, dur):
    """Normalised 0..1 progress of an event starting at `start`."""
    return clamp01((lt - start) / max(dur, 1e-4))


def col(c, a=255):
    return (c[0], c[1], c[2], int(max(0, min(255, a))))


def mix(c1, c2, t):
    t = clamp01(t)
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# ---------------------------------------------------------------- fonts
_FONTS = {}


def F(kind, size):
    size = max(8, int(round(size)))
    key = (kind, size)
    if key not in _FONTS:
        try:
            _FONTS[key] = ImageFont.truetype(FONT_PATHS[kind], size)
        except Exception:
            _FONTS[key] = ImageFont.load_default()
    return _FONTS[key]


def tlen(d, text, f, tracking=0.0):
    if not text:
        return 0.0
    return sum(d.textlength(ch, font=f) + tracking for ch in text) - tracking


def tracked(d, xy, text, f, fill, tracking=0.0, center=None):
    """Draw text with letter-spacing. `center` = x centre for centring."""
    if center is None:
        x, y = xy
    else:
        x = center - tlen(d, text, f, tracking) / 2
        y = xy[1]
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tracking
    return x


def para(d, text, f, fill, x, y, maxw, lh=1.32, center=False, tracking=0.0):
    """Word-wrapped paragraph. Returns the height used. Respects \\n."""
    lines = []
    for block in text.split("\n"):
        words = block.split(" ")
        cur = ""
        for w_ in words:
            test = (cur + " " + w_).strip()
            if tlen(d, test, f, tracking) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
    lh_px = int(f.size * lh)
    for i, line in enumerate(lines):
        yy = y + i * lh_px
        if center:
            tracked(d, (0, yy), line, f, fill, tracking, center=x + maxw / 2)
        else:
            tracked(d, (x, yy), line, f, fill, tracking)
    return len(lines) * lh_px


# ---------------------------------------------------------------- masks / cards
def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    return m


def glass_card(w, h, r=30, top_a=30, bot_a=9, border_a=40, tint=(255, 255, 255), highlight=True):
    """Vertical-gradient frosted panel with a hairline border."""
    ys = np.linspace(0, 1, h)[:, None]
    alpha = top_a + (bot_a - top_a) * ys
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = tint
    arr[..., 3] = np.repeat(alpha.astype(np.uint8), w, axis=1)
    mask = np.array(rounded_mask(w, h, r), np.float32) / 255.0
    arr[..., 3] = (arr[..., 3].astype(np.float32) * mask).astype(np.uint8)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, outline=(255, 255, 255, border_a), width=2)
    if highlight:
        d.line([(r, 1), (w - r, 1)], fill=(255, 255, 255, min(150, border_a + 70)), width=2)
    return im


def dark_card(w, h, r=30, fill=(14, 12, 26), border=(255, 255, 255, 26)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=fill, outline=border, width=2)
    return im


_SHADOW_CACHE = {}


def _shadow(w, h, r, blur, alpha):
    key = (w, h, r, blur, alpha)
    if key not in _SHADOW_CACHE:
        pad = blur * 2
        im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle(
            [pad, pad, pad + w - 1, pad + h - 1], r, fill=(0, 0, 0, alpha)
        )
        _SHADOW_CACHE[key] = im.filter(ImageFilter.GaussianBlur(blur))
    return _SHADOW_CACHE[key]


def place(canvas, im, x, y, shadow=True, blur=26, alpha=120, r=30, dy=16):
    if shadow:
        sh = _shadow(int(im.width), int(im.height), r, blur, alpha)
        canvas.alpha_composite(sh, (int(x) - blur * 2, int(y) - blur * 2 + dy))
    canvas.alpha_composite(im, (int(x), int(y)))


def pill(text, kind="isb", size=26, fg=TEXT, bg=(255, 255, 255, 16), border=(255, 255, 255, 34),
         pad_x=26, pad_y=14, tracking=0.5, dot=None, dot_col=MINT):
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    f = F(kind, size)
    tw_ = tlen(tmp, text, f, tracking)
    h = int(size * 1.55) + pad_y * 2
    w = int(tw_ + pad_x * 2 + (size * 0.85 if dot else 0))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=bg, outline=border, width=2)
    x = pad_x
    if dot:
        cy = h // 2
        d.ellipse([x, cy - size * 0.24, x + size * 0.48, cy + size * 0.24], fill=col(dot_col, 255))
        x += int(size * 0.85)
    tracked(d, (x, (h - size * 1.28) / 2 - 1), text, f, fg, tracking)
    return im


def glow_text(text, kind, size, color, alpha=200, radius=22, spread=1.0):
    """Text image with a coloured bloom baked in."""
    f = F(kind, size)
    tw_ = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    wpx = int(tlen(tw_, text, f) + radius * 4)
    hpx = int(size * 1.55 + radius * 4)
    im = Image.new("RGBA", (wpx, hpx), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((radius * 2, radius * 2), text, font=f, fill=col(color, alpha))
    blur = im.filter(ImageFilter.GaussianBlur(radius * spread))
    out = Image.new("RGBA", (wpx, hpx), (0, 0, 0, 0))
    out.alpha_composite(blur)
    out.alpha_composite(im)
    return out


def icon_mail(d, x, y, s, color):
    d.rounded_rectangle([x, y, x + s, y + s * 0.72], s * 0.10, outline=color, width=2)
    d.line([(x + 2, y + 3), (x + s / 2, y + s * 0.42), (x + s - 2, y + 3)], fill=color, width=2)


def icon_phone(d, x, y, s, color):
    d.rounded_rectangle([x + s * 0.18, y, x + s * 0.82, y + s], s * 0.16, outline=color, width=2)
    d.line([(x + s * 0.40, y + s * 0.82), (x + s * 0.60, y + s * 0.82)], fill=color, width=2)


def icon_pin(d, x, y, s, color):
    d.ellipse([x + s * 0.18, y, x + s * 0.82, y + s * 0.64], outline=color, width=2)
    d.ellipse([x + s * 0.42, y + s * 0.22, x + s * 0.58, y + s * 0.38], fill=color)
    d.line([(x + s * 0.32, y + s * 0.56), (x + s * 0.5, y + s), (x + s * 0.68, y + s * 0.56)],
           fill=color, width=2)


def arrow_h(d, x, y, length, color, width=3, head=10):
    d.line([(x, y), (x + length - head * 0.7, y)], fill=color, width=width)
    d.polygon([(x + length, y), (x + length - head, y - head * 0.62),
               (x + length - head, y + head * 0.62)], fill=color)


def arrow_v(d, x, y, length, color, width=3, head=10):
    d.line([(x, y), (x, y + length - head * 0.7)], fill=color, width=width)
    d.polygon([(x, y + length), (x - head * 0.62, y + length - head),
               (x + head * 0.62, y + length - head)], fill=color)


def sparkline(d, pts, color, width=4, fill_area=None):
    d.line(pts, fill=color, width=width, joint="curve")
    if fill_area:
        base = fill_area
        poly = pts + [(pts[-1][0], base), (pts[0][0], base)]
        d.polygon(poly, fill=col(color, 0))


# ---------------------------------------------------------------- background
def _orb(img, cx, cy, r, color, strength, power=1.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)
    g = np.exp(-d2 * power) * strength
    img += g[..., None] * np.array(color, np.float32)


def build_bg():
    """Static stage: deep indigo gradient + three coloured orbs + grid + grain."""
    ys = np.linspace(0, 1, H, dtype=np.float32)
    stops_y = [0.0, 0.30, 0.62, 1.0]
    stops_c = [(8, 7, 18), (13, 10, 28), (9, 7, 20), (4, 3, 10)]
    img = np.zeros((H, W, 3), np.float32)
    for ch in range(3):
        img[..., ch] = np.interp(ys, stops_y, [c[ch] for c in stops_c])[:, None]

    # coloured atmosphere
    _orb(img, 905, 250, 780, VIOLET, 0.30, 1.7)
    _orb(img, 130, 1640, 700, (14, 140, 160), 0.20, 1.8)
    _orb(img, 980, 1180, 520, AMBER, 0.075, 2.2)
    _orb(img, 300, 640, 620, (90, 60, 220), 0.13, 2.0)

    # fine grid
    grid = np.zeros((H, W), np.float32)
    grid[np.arange(H) % 96 < 1, :] = 1.0
    grid[:, np.arange(W) % 96 < 1] = 1.0
    img += (grid * 5.5)[..., None]

    # vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx - W / 2) / (W * 0.72)
    dy = (yy - H / 2) / (H * 0.72)
    vig = np.clip(1.0 - 0.42 * (dx * dx + dy * dy) ** 0.85, 0.30, 1.0)
    img *= vig[..., None]

    # grain
    rng = np.random.default_rng(7)
    img += rng.normal(0, 2.4, (H, W, 1)).astype(np.float32)

    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    return out


def dust(canvas, t, n=26):
    """Slow drifting specks for cinematic depth."""
    rng = np.random.default_rng(21)
    xs = rng.random(n)
    ys = rng.random(n)
    rad = rng.random(n) * 2.2 + 0.8
    spd = rng.random(n) * 0.5 + 0.25
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(n):
        x = (xs[i] * W + math.sin(t * 0.25 + i) * 26) % W
        y = (ys[i] * H - t * spd[i] * 26) % H
        a = 30 + 34 * (0.5 + 0.5 * math.sin(t * 0.9 + i * 1.7))
        d.ellipse([x - rad[i], y - rad[i], x + rad[i], y + rad[i]], fill=(210, 205, 255, int(a)))
    canvas.alpha_composite(layer)


# ---------------------------------------------------------------- image fx
def with_alpha(im, a):
    if a >= 0.999:
        return im
    arr = np.array(im)
    arr[..., 3] = (arr[..., 3].astype(np.float32) * clamp01(a)).astype(np.uint8)
    return Image.fromarray(arr)


def grayscale(im, amount):
    if amount <= 0:
        return im
    g = Image.new("RGBA", im.size)
    gray = Image.new("L", im.size)
    gray.paste(im.convert("L"))
    g.paste(gray.convert("RGB"), (0, 0))
    g.putalpha(im.getchannel("A"))
    from PIL import Image as _I
    return _I.blend(im, g, clamp01(amount))


def rotate_soft(im, angle, resample=Image.BICUBIC):
    return im.rotate(angle, resample=resample, expand=True)


# ---------------------------------------------------------------- audio
def _read_wav(path):
    with wave.open(path, "rb") as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        idx = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(idx, np.arange(len(a)), a)
    return a


def decode_vo(src, dst, tempo):
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", src,
                    "-filter:a", f"atempo={tempo:.4f}", "-ar", str(SR), "-ac", "1", dst],
                   check=True)
    return _read_wav(dst)


def _env(x, attack=0.005, release=0.06):
    n = len(x)
    a = max(1, int(attack * SR))
    r = max(1, int(release * SR))
    e = np.ones(n, np.float32)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return x * e


def _bp_noise(n, lo, hi, seed=0):
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n).astype(np.float32)
    sos = butter(2, [lo / (SR / 2), min(hi / (SR / 2), 0.99)], btype="band", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def sfx_whoosh(dur=0.5, amp=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    lo = _bp_noise(n, 180, 700, seed=3)
    hi = _bp_noise(n, 900, 5200, seed=4)
    x = lo * (1 - t / dur) + hi * (t / dur) ** 1.6
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.4
    return (x * e * amp).astype(np.float32)


def sfx_pop(amp=0.13):
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    f = 780 + 1150 * np.exp(-t * 34)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 26)
    click = np.random.default_rng(9).normal(0, 1, n) * np.exp(-t * 260) * 0.25
    return ((x + click) * amp).astype(np.float32)


def sfx_tick(amp=0.05):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 2100 * t) * np.exp(-t * 90)
    return (x * amp).astype(np.float32)


def sfx_ding(amp=0.16):
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 1318.5 * t) * 0.6 + np.sin(2 * np.pi * 1975.5 * t) * 0.4)
    x *= np.exp(-t * 4.2)
    return (x * amp).astype(np.float32)


def build_score(total, vo_clips, scene_starts, sfx_events, out_path):
    """Ambient score + VO + UI sfx, ducked and normalised."""
    n = int(total * SR)
    music = np.zeros(n, np.float32)

    bpm = 92.0
    beat = 60.0 / bpm
    bar = beat * 4
    roots = [146.83, 116.54, 174.61, 130.81]  # Dm Bb F C
    chords = [(0, 3, 7), (0, 4, 7), (0, 4, 7), (0, 4, 7)]
    pad = np.zeros(n, np.float32)
    nb = int(math.ceil(total / bar)) + 1
    for b in range(nb):
        root = roots[b % 4]
        third = root * (2 ** (chords[b % 4][1] / 12))
        fifth = root * (2 ** (chords[b % 4][2] / 12))
        s = int(b * bar * SR)
        e = min(n, int((b * bar + bar + 1.4) * SR))
        if s >= n:
            break
        tt = np.arange(e - s) / SR
        env = np.minimum(tt / 0.55, 1.0) * np.exp(-np.maximum(tt - bar * 0.55, 0) * 1.5)
        v = (np.sin(2 * np.pi * root * tt) * 0.55
             + np.sin(2 * np.pi * third * tt + 0.6) * 0.30
             + np.sin(2 * np.pi * fifth * tt + 1.2) * 0.24
             + np.sin(2 * np.pi * root * 2.0 * tt + 0.3) * 0.16
             + np.sin(2 * np.pi * root * 0.5 * tt) * 0.22)
        pad[s:e] += (v * env).astype(np.float32)
    from scipy.signal import butter, sosfilt
    sos = butter(2, 2400 / (SR / 2), btype="low", output="sos")
    pad = sosfilt(sos, pad).astype(np.float32)
    music += pad * 0.085

    # soft pulse on each beat
    kick = np.zeros(n, np.float32)
    t0 = 0.0
    while t0 < total:
        s = int(t0 * SR)
        ln = min(n - s, int(0.28 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 92 * np.exp(-tt * 16) + 44
            k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 15)
            kick[s:s + ln] += (k * 0.11).astype(np.float32)
        t0 += beat
    music += kick

    # off-beat airy hats
    hats = np.zeros(n, np.float32)
    t0 = beat / 2
    while t0 < total:
        s = int(t0 * SR)
        ln = min(n - s, int(0.05 * SR))
        if ln > 0:
            h = _bp_noise(ln, 5000, 12000, seed=int(t0 * 10)) * np.exp(-np.arange(ln) / SR * 120)
            hats[s:s + ln] += (h * 0.03).astype(np.float32)
        t0 += beat
    music += hats

    # arpeggio sparkle in the second half
    arp = np.zeros(n, np.float32)
    step = beat / 2
    k = 0
    t0 = 8.0
    while t0 < total - 1.0:
        root = roots[(int(t0 / bar)) % 4] * 2
        note = root * (2 ** ([0, 7, 12, 7][k % 4] / 12))
        s = int(t0 * SR)
        ln = min(n - s, int(0.5 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            a = np.sin(2 * np.pi * note * tt) * np.exp(-tt * 7) * 0.035
            arp[s:s + ln] += a.astype(np.float32)
        k += 1
        t0 += step
    music += arp

    # riser into the finale
    r_start = scene_starts[-1] - 2.2
    s = max(0, int(r_start * SR))
    ln = n - s
    if ln > 0:
        r = _bp_noise(ln, 400, 6000, seed=17)
        tt = np.arange(ln) / SR
        music[s:] += (r * (tt / max(ln / SR, 1e-3)) ** 2 * 0.05).astype(np.float32)

    # VO track + envelope for ducking
    vo = np.zeros(n, np.float32)
    for (path, start, tempo) in vo_clips:
        a = decode_vo(path, f"/tmp/_vo_{os.path.basename(path)}.wav", tempo)
        s = int(start * SR)
        e = min(n, s + len(a))
        if s < n:
            vo[s:e] += a[: e - s]
    env = np.abs(vo)
    win = int(0.12 * SR)
    kernel = np.ones(win, np.float32) / win
    env = np.convolve(env, kernel, mode="same")
    env = np.clip(env / (env.max() + 1e-6) * 3.2, 0, 1)
    duck = 1.0 - 0.58 * env
    music *= duck

    sfx = np.zeros(n, np.float32)
    for (kind, t_at, amp, pan) in sfx_events:
        if kind == "whoosh":
            a = sfx_whoosh(0.55, amp)
        elif kind == "pop":
            a = sfx_pop(amp)
        elif kind == "tick":
            a = sfx_tick(amp)
        elif kind == "ding":
            a = sfx_ding(amp)
        else:
            continue
        s = int(t_at * SR)
        e = min(n, s + len(a))
        if s < n:
            sfx[s:e] += a[: e - s]

    mono = music + vo * 1.0 + sfx
    # gentle stereo width from a short delay
    dly = int(0.012 * SR)
    left = mono.copy()
    right = np.concatenate([np.zeros(dly, np.float32), mono[:-dly]])
    st = np.stack([left * 0.97 + right * 0.10, right * 0.97 + left * 0.10], axis=1)

    peak = np.abs(st).max() + 1e-9
    st = st / peak * 0.89
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path
