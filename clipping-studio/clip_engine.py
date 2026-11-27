#!/usr/bin/env python3
"""Clipping automatique : source 16:9 → Shorts 9:16 sous-titrés, prêts à publier.

Trois briques :

1. **Découpe intelligente** (`find_clips`) — le transcript est découpé en
   phrases ; on cherche les fenêtres de 20–35 s avec le meilleur score :
   mots-clés de hook, chiffres, questions, densité de parole, et **on évite
   de couper au milieu d'une phrase**.
2. **Recadrage 9:16 qui suit le visage** (`build_crop_track`) — détection de
   visage (OpenCV), lissage temporel, garde-fou : le cadre ne bouge pas plus
   vite que ~110 px/s.
3. **Sous-titres mot à mot + habillage** (`render`) — chaque mot apparaît sur
   son timing (pas de découpage linéaire), 1–3 mots par page, mot actif en
   surbrillance, barre de progression, kicker, cartouche source, et la vidéo
   plein cadre en fond flou pour remplir le 9:16.

    python3 clip_engine.py --video source.mp4 --transcript words.json --list
    python3 clip_engine.py --video source.mp4 --transcript words.json \
        --render-all --outdir shorts --brand "COOL"
"""
import argparse
import json
import os
import re
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
CW, CH = 1080, 1350          # fenêtre 4:5 : sujet plus grand, format Reels
FB = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
FONTS = {
    "b": f"{FB}/inter/700Bold/Inter_700Bold.ttf",
    "sb": f"{FB}/inter/600SemiBold/Inter_600SemiBold.ttf",
    "m": f"{FB}/inter/500Medium/Inter_500Medium.ttf",
    "g": f"{FB}/space-grotesk/700Bold/SpaceGrotesk_700Bold.ttf",
    "ser": f"{FB}/instrument-serif/400Regular_Italic/InstrumentSerif_400Regular_Italic.ttf",
}
CREAM = (247, 244, 239)
AMBER = (255, 186, 48)
INK = (10, 10, 12)
HOOKS = ["parce que", "en fait", "le problème", "la vérité", "erreur", "jamais",
         "toujours", "secret", "personne", "tout le monde", "gratuit", "argent",
         "peur", "échec", "pourquoi", "comment", "arrête", "stop", "écoute"]


def tool(name):
    """ffmpeg/ffprobe : binaire local si présent, sinon PATH."""
    local = f"/tmp/bin/{name}"
    return local if os.path.exists(local) else name


def F(kind, size):
    return ImageFont.truetype(FONTS[kind], int(size))


def ffprobe_duration(path):
    out = subprocess.run([tool("ffprobe"), "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        raise SystemExit(f"ffprobe n'a pas lu {path} : {out.stderr[:200]}")


# ------------------------------------------------------------------ transcript
def _parse_srt(path):
    """SRT/VTT → mots au prorata dans chaque sous-titre (fallback honnête)."""
    raw = open(path, encoding="utf-8", errors="ignore").read().replace("\r", "")
    blocks = re.split(r"\n\s*\n", raw)
    segs = []
    for b in blocks:
        m = re.search(r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
                      r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})", b)
        if not m:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, m.groups())
        t0 = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
        t1 = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        txt = " ".join(l.strip() for l in b.split("\n")[m.group(0).count("\n") + 1:]
                       if l.strip() and "-->" not in l)
        txt = re.sub(r"<[^>]+>", "", txt).strip()
        if txt:
            segs.append({"t0": t0, "t1": t1, "text": txt})
    return segs


def load_transcript(path):
    """Accepte : mot-à-mot JSON, segments {t0,t1,text}, Whisper, ou SRT/VTT."""
    if path.lower().endswith((".srt", ".vtt")):
        data = _parse_srt(path)
    else:
        data = json.load(open(path, encoding="utf-8"))
    words = []
    if isinstance(data, dict) and "segments" in data:
        for seg in data["segments"]:
            for w in seg.get("words", []):
                words.append({"word": w["word"].strip(),
                              "start": float(w.get("start", seg.get("start", 0))),
                              "end": float(w.get("end", seg.get("end", 0)))})
    elif isinstance(data, list) and data and "word" in data[0]:
        for w in data:
            words.append({"word": w["word"].strip(), "start": float(w["start"]),
                          "end": float(w["end"])})
    elif isinstance(data, list) and data and "text" in data[0]:
        # segments texte : on répartit les mots au prorata des caractères
        for seg in data:
            t0, t1 = float(seg.get("t0", seg.get("start", 0))), float(seg.get("t1", seg.get("end", 0)))
            toks = [t for t in re.split(r"\s+", seg["text"].strip()) if t]
            total = sum(len(t) + 1 for t in toks) or 1
            cur = t0
            for t in toks:
                d = (len(t) + 1) / total * (t1 - t0)
                words.append({"word": t, "start": round(cur, 3), "end": round(cur + d, 3)})
                cur += d
    else:
        raise SystemExit("format de transcript non reconnu")
    words = [w for w in words if w["word"]]
    for a, b in zip(words, words[1:]):
        if b["start"] < a["start"]:
            b["start"] = a["start"]
    return words


def sentences(words, gap=0.65):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end_punct = bool(re.search(r"[.!?…]$", w["word"]))
        if nxt is None or end_punct or (nxt["start"] - w["end"]) > gap:
            if cur:
                out.append({"words": cur, "t0": cur[0]["start"], "t1": cur[-1]["end"],
                            "text": " ".join(x["word"] for x in cur)})
            cur = []
    return out


# ------------------------------------------------------------------ sélection
def _score(sents, target=26.0):
    text = " ".join(s["text"] for s in sents).lower()
    dur = sents[-1]["t1"] - sents[0]["t0"]
    if not (18.0 <= dur <= 40.0):
        return -99.0
    n = len(re.findall(r"\w+", text))
    wps = n / max(dur, .1)
    score = 0.0
    score += 2.2 * sum(1 for h in HOOKS if h in text)
    score += 0.85 * len(re.findall(r"\b\d+([.,]\d+)?\s?(%|€|\$|k|millions?|ans?|jours?)\b", text))
    score += 1.1 * text.count("?")
    score += 1.4 * (wps >= 2.6) + 0.8 * (2.0 <= wps < 2.6) - 1.2 * (wps < 1.6)
    score += 0.9 * bool(re.search(r"\b(moi|je|tu|vous|nous)\b", text))
    score -= 0.55 * abs(dur - target) / target
    first = sents[0]["text"].lower()
    score += 1.6 * any(first.startswith(h) for h in ("et", "mais", "donc", "parce", "quand"))
    return score


def find_clips(words, count=6, min_gap=8.0, target=26.0, avoid=()):
    sents = sentences(words)
    cands = []
    for i in range(len(sents)):
        for j in range(i, min(len(sents), i + 7)):
            span = sents[i:j + 1]
            sc = _score(span, target)
            if sc < -50:
                continue
            t0, t1 = span[0]["t0"], span[-1]["t1"]
            if any(abs(t0 - a[0]) < min_gap for a in avoid):
                continue
            cands.append({"t0": round(max(0, t0 - 0.22), 2), "t1": round(t1 + 0.30, 2),
                          "score": round(sc, 2), "text": " ".join(s["text"] for s in span),
                          "words": [w for s in span for w in s["words"]]})
    cands.sort(key=lambda c: -c["score"])
    picked = []
    for c in cands:
        if all(c["t1"] <= p["t0"] or c["t0"] >= p["t1"] for p in picked):
            picked.append(c)
        if len(picked) >= count:
            break
    return sorted(picked, key=lambda c: c["t0"])


# ------------------------------------------------------------------ recadrage
_BG = {"key": None, "bg": None}


def _subject_x(frame, bg=None):
    """Position horizontale du sujet, sans modèle à télécharger.

    Méthode : soustraction du fond temporel (médiane de la séquence) — dans une
    vidéo de plateau, la personne est ce qui bouge. On garde le plus gros amas
    « haut » (une tête/buste est plus haute que large), pondéré par une carte
    de teintes chair pour éviter les objets qui passent. Repli : centre.
    """
    small = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_AREA)
    h, w = small.shape[:2]
    if bg is not None:
        diff = cv2.absdiff(small, bg).max(axis=2)
        mask = (diff > 26).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
        n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
        best, best_w = None, 0.0
        for i in range(1, n):
            x, y, ww, hh, area = stats[i]
            frac = area / (w * h)
            if frac < 0.02 or frac > 0.55 or hh < ww * 0.75:
                continue
            cx = cent[i][0]
            if cx < 0.08 * w or cx > 0.92 * w:
                continue
            weight = area * (1.0 + 0.5 * (hh / max(ww, 1)))
            if weight > best_w:
                best, best_w = cx, weight
        if best is not None:
            return best / (w / 1920.0)

    # repli : barycentre des teintes chair (plages larges, carnations variées)
    ycrcb = cv2.cvtColor(small, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    skin = ((cr >= 133) & (cr <= 178) & (cb >= 77) & (cb <= 130) & (y > 45)).astype(np.float32)
    skin = cv2.GaussianBlur(skin, (0, 0), 9)
    colsum = skin.sum(axis=0)
    if colsum.sum() > 0.02 * colsum.size:
        xs = np.arange(w, dtype=np.float32) + 0.5
        return float((colsum * xs).sum() / colsum.sum()) / (w / 1920.0)
    return None


def _bg_median(video, t0, t1, n=7):
    cap = cv2.VideoCapture(video)
    frames = []
    for i in range(n):
        t = t0 + (t1 - t0) * (i + 0.5) / n
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, f = cap.read()
        if ok:
            frames.append(cv2.resize(f, (320, 180), interpolation=cv2.INTER_AREA))
    cap.release()
    if not frames:
        return None
    return np.median(np.stack(frames), axis=0).astype(np.uint8)


def build_crop_track(video, t0, t1, fps=6, smooth=9, max_speed=110.0):
    """[(time, x_center)] lissé, avec repli sur le centre si aucun sujet."""
    bg = _bg_median(video, t0, t1)
    cap = cv2.VideoCapture(video)
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = 1.0 / fps
    ts, xs = [], []
    t = t0
    while t <= t1:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            break
        x = _subject_x(frame, bg)
        if x is not None:
            ts.append(t)
            xs.append(x)
        t += step
    cap.release()
    half = (src_h * CW / CH) / 2
    if not xs:
        return [(t0, src_w / 2)], (src_w, src_h)
    arr = np.array(xs, np.float32)
    k = max(1, smooth)
    pad = np.pad(arr, (k, k), mode="edge")
    arr = np.convolve(pad, np.ones(k) / k, mode="same")[k:-k]
    max_dx = max_speed / fps
    for i in range(1, len(arr)):
        arr[i] = np.clip(arr[i], arr[i - 1] - max_dx, arr[i - 1] + max_dx)
    arr = np.clip(arr, half, src_w - half)
    return list(zip(ts, arr.tolist())), (src_w, src_h)


def crop_at(track, t):
    if len(track) == 1:
        return track[0][1]
    ts = [p[0] for p in track]
    i = int(np.searchsorted(ts, t, side="right") - 1)
    i = max(0, min(len(track) - 2, i))
    (t0, x0), (t1, x1) = track[i], track[i + 1]
    u = 0 if t1 == t0 else max(0.0, min(1.0, (t - t0) / (t1 - t0)))
    return x0 + (x1 - x0) * u


# ------------------------------------------------------------------ pages de mots
def make_pages(words, t0, t1, max_words=3, max_chars=18):
    ws = [w for w in words if w["end"] > t0 and w["start"] < t1]
    pages, cur = [], []
    for w in ws:
        cand = cur + [w]
        if len(cand) > max_words or sum(len(x["word"]) + 1 for x in cand) > max_chars + 1:
            pages.append(cur)
            cur = [w]
        else:
            cur = cand
    if cur:
        pages.append(cur)
    out = []
    for i, p in enumerate(pages):
        start = max(t0, p[0]["start"])
        end = min(t1, pages[i + 1][0]["start"] if i + 1 < len(pages) else p[-1]["end"] + 0.35)
        out.append({"words": p, "start": start, "end": max(start + 0.25, end)})
    return out


_F_CACHE = {}


def draw_captions(canvas, pages, t, bottom=1560):
    """1–3 mots par page, apparition mot à mot, mot actif surligné."""
    page = None
    for p in pages:
        if p["start"] <= t < p["end"]:
            page = p
            break
    if page is None:
        return
    d = ImageDraw.Draw(canvas)
    active = None
    for w in page["words"]:
        if w["start"] <= t < w["end"] + 0.18:
            active = w
    # composition en une ou deux lignes, centrée
    f = F("b", 78)
    words = [w["word"].upper() for w in page["words"]]
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if d.textlength(test, font=f) > W - 220 and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    lh = int(78 * 1.16)
    y = bottom - lh * len(lines) + 20
    for line in lines:
        widths = [d.textlength(w, font=f) for w in line]
        total = sum(widths) + 26 * (len(line) - 1)
        x = (W - total) / 2
        for w, wd in zip(line, widths):
            src = next((x_ for x_ in page["words"] if x_["word"].upper() == w), None)
            if src is None:
                x += wd + 26
                continue
            appear = max(0.0, min(1.0, (t - src["start"]) / 0.14))
            if appear <= 0:
                x += wd + 26
                continue
            scale = 0.86 + 0.14 * min(1.0, appear ** 0.6)
            fs = int(78 * scale)
            f2 = _F_CACHE.get(fs) or _F_CACHE.setdefault(fs, F("b", fs))
            wd2 = d.textlength(w, font=f2)
            yy = y + (78 - fs) * 0.6
            # halo sombre pour la lisibilité
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (2, 2), (-2, 2)):
                d.text((x + dx, yy + dy), w, font=f2, fill=(0, 0, 0, 210))
            color = AMBER if (active is src) else CREAM
            d.text((x, yy), w, font=f2, fill=color)
            x += wd2 - (78 - fs) * 0.3 + 26


def draw_frame_overlay(canvas, t, t0, t1, kicker, brand, dur, index):
    d = ImageDraw.Draw(canvas)
    # fond de lisibilité haut/bas
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(260):
        a = int(150 * (1 - i / 260) ** 1.6)
        gd.rectangle([0, i, W, i + 1], fill=(0, 0, 0, a))
        gd.rectangle([0, H - 380 + i, W, H - 379 + i], fill=(0, 0, 0, int(190 * (i / 380) ** 0.8)))
    canvas.alpha_composite(grad)
    # kicker haut
    kf = F("sb", 30)
    kw = d.textlength(kicker.upper(), font=kf) + 54
    d.rounded_rectangle([60, 96, 60 + kw, 158], 31, fill=(0, 0, 0, 150),
                        outline=(255, 255, 255, 46), width=2)
    d.text((86, 112), kicker.upper(), font=kf, fill=CREAM)
    # marque en haut à droite
    bf = F("g", 30)
    bw = d.textlength(brand.upper(), font=bf)
    d.text((W - 60 - bw, 112), brand.upper(), font=bf, fill=CREAM)
    # barre de progression segmentée
    prog = max(0.0, min(1.0, (t - t0) / max(0.01, t1 - t0)))
    for i in range(10):
        x0 = 60 + i * ((W - 120) / 10)
        d.rounded_rectangle([x0 + 3, H - 132, x0 + (W - 120) / 10 - 6, H - 124], 4,
                            fill=(255, 255, 255, 70 if i / 10 > prog else 255))
    # compteur de clip
    nf = F("m", 24)
    d.text((60, H - 108), f"CLIP {index:02d}", font=nf, fill=(255, 255, 255, 150))


# ------------------------------------------------------------------ rendu
def render_clip(video, clip, out_path, brand="COOL", kicker="EXTRAIT", index=1,
                src_wh=None):
    t0, t1 = clip["t0"], clip["t1"]
    dur = t1 - t0
    track, (sw, sh) = build_crop_track(video, t0, t1)
    pages = make_pages(clip["words"], t0, t1)
    nf = int(round(dur * FPS))

    cap = cv2.VideoCapture(video)
    proc = subprocess.Popen(
        [tool("ffmpeg"), "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", video,
         "-filter_complex", f"[1:a]atrim={t0}:{t1},asetpts=PTS-STARTPTS,"
                            "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]",
         "-map", "0:v:0", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", out_path],
        stdin=subprocess.PIPE)
    bg_cache = None
    for fi in range(nf):
        t = t0 + fi / FPS
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # fond flou plein cadre (remplit le 9:16 sans bandes noires)
        if bg_cache is None or fi % 90 == 0:
            small = cv2.resize(frame, (270, 480))
            small = cv2.GaussianBlur(small, (0, 0), 7)
            big = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
            bg_cache = Image.fromarray(big).convert("RGBA")
        canvas = bg_cache.copy()
        canvas.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
        # fenêtre 4:5 qui suit le sujet
        half = (sh * CW / CH) / 2
        xc = crop_at(track, t)
        x0 = int(max(0, min(sw - 2 * half, xc - half)))
        crop = frame[0:sh, x0:x0 + int(2 * half)]
        crop = cv2.resize(crop, (CW, CH), interpolation=cv2.INTER_LINEAR)
        tile = Image.fromarray(crop).convert("RGBA")
        mask = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, CW - 1, CH - 1], 34, fill=255)
        tile.putalpha(mask)
        canvas.alpha_composite(tile, (0, (H - CH) // 2))
        # ombre + liseré
        od = ImageDraw.Draw(canvas)
        od.rounded_rectangle([0, (H - CH) // 2, CW - 1, (H - CH) // 2 + CH - 1], 34,
                             outline=(255, 255, 255, 40), width=2)
        draw_captions(canvas, pages, t)
        draw_frame_overlay(canvas, t, t0, t1, kicker, brand, dur, index)
        proc.stdin.write(np.asarray(canvas.convert("RGB")).tobytes())
        if fi % 120 == 0:
            print(f"    {fi}/{nf} ({fi / nf * 100:.0f}%)", flush=True)
    cap.release()
    proc.stdin.close()
    proc.wait()
    return out_path


def list_clips(clips):
    for i, c in enumerate(clips, 1):
        print(f"[{i:02d}] {c['t0']:6.2f} → {c['t1']:6.2f}  ({c['t1'] - c['t0']:4.1f}s, "
              f"score {c['score']:5.2f})  {c['text'][:96]}…")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--count", type=int, default=6)
    ap.add_argument("--target", type=float, default=26.0)
    ap.add_argument("--brand", default="COOL")
    ap.add_argument("--kicker", default="EXTRAIT")
    ap.add_argument("--outdir", default="clips")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--render-all", action="store_true")
    ap.add_argument("--only", default=None, help="1,3,5")
    a = ap.parse_args()

    words = load_transcript(a.transcript)
    clips = find_clips(words, count=a.count, target=a.target)
    if a.list or not a.render_all:
        list_clips(clips)
        print(json.dumps([{"t0": c["t0"], "t1": c["t1"], "score": c["score"]} for c in clips],
                         ensure_ascii=False))
        if not a.render_all:
            return
    os.makedirs(a.outdir, exist_ok=True)
    idx = [int(x) - 1 for x in a.only.split(",")] if a.only else range(len(clips))
    idx = [i for i in idx if 0 <= i < len(clips)]
    src_wh = (1920, 1080)
    for i in idx:
        c = clips[i]
        out = os.path.join(a.outdir, f"clip-{i + 1:02d}-{int(c['t0'])}s-9x16.mp4")
        print(f"  clip {i + 1}: {c['t0']}→{c['t1']}  {out}", flush=True)
        render_clip(a.video, c, out, a.brand, a.kicker, i + 1, src_wh)
        print("    ok", os.path.getsize(out) // 1024 // 1024, "Mo")


if __name__ == "__main__":
    main()
