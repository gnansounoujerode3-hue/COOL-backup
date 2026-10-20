#!/usr/bin/env python3
"""
Renders 6 vertical 9:16 (1080x1920, 30fps) Shorts from `imports/videoplayback.mp4`
("Lose 100 Lbs, Win $250,000!") with clean, ultra-professional French subtitles:
- Strictly <= 2 lines of subtitle at a time
- Zero boxes/clutter around subtitles or at the top of the frame
- Subtle darkened lower third for crystal-clear readability
- Smart 9:16 vertical subject crop + clarity sharpening + subtle Ken Burns motion
"""
import math
import os
import subprocess
import sys
import time
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = "/home/user/COOL-backup"
SRC_MP4 = f"{REPO_ROOT}/imports/videoplayback.mp4"
OUT_DIR = f"{REPO_ROOT}/mrbeast-100lbs-shorts/shorts"
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 1080, 1920
FPS = 30.0

FONT_ROOT = "/tmp/work_cache/fonts/node_modules/@expo-google-fonts"
F_MONT_BOLD = f"{FONT_ROOT}/montserrat/700Bold/Montserrat_700Bold.ttf"
F_MONT_EBOLD = f"{FONT_ROOT}/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf"
F_MONT_BLACK = f"{FONT_ROOT}/montserrat/900Black/Montserrat_900Black.ttf"
F_DAFOE = f"{FONT_ROOT}/mr-dafoe/400Regular/MrDafoe_400Regular.ttf"

C_WHITE = (255, 255, 255)
C_SILVER = (212, 220, 235)
C_CYAN_BLUE = (56, 152, 255)    # Electric MrBeast Cyan-Blue accent
C_GOLD = (255, 204, 38)         # Prize Pool Gold accent
C_CRIMSON = (255, 48, 76)       # High-stakes Red accent

_FONT_CACHE = {}
_SUB_CACHE = {}


def get_font(path, size):
    size = max(14, int(round(size)))
    key = (path, size)
    if key not in _FONT_CACHE:
        try:
            _FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def fit_font(path, text, target_size, max_w=940):
    sz = target_size
    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    while sz > 28:
        f = get_font(path, sz)
        if d.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        sz -= 3
    return get_font(path, sz)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out_back(t, s=1.35):
    t = clamp(t)
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def build_bottom_vignette():
    """Slightly darkens the bottom of the Short (y=1120..1920) with zero box framing."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bottom_dark = np.clip((yy - H * 0.56) / (H * 0.44), 0.0, 1.0) ** 1.35 * 0.68
    edge_vig = np.clip(((xx - W * 0.5) / (W * 0.54)) ** 2 + ((yy - H * 0.5) / (H * 0.54)) ** 2 - 0.42, 0.0, 1.0) * 0.22
    alpha = np.clip(bottom_dark + edge_vig, 0.0, 0.74)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[:, :, 0] = 4
    rgba[:, :, 1] = 7
    rgba[:, :, 2] = 16
    rgba[:, :, 3] = (alpha * 255.0).astype(np.uint8)
    return rgba


def get_subtitle_sprite(l1: str, l2: str, accent: str):
    """
    Pre-renders a crisp <= 2-line subtitle sprite with soft Gaussian drop shadow,
    neon accent bloom on line 2, and zero background box.
    """
    key = (l1, l2, accent)
    if key in _SUB_CACHE:
        return _SUB_CACHE[key]

    cw, ch = W, 360
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    if accent == "gold":
        col2 = C_GOLD
    elif accent == "crimson":
        col2 = C_CRIMSON
    else:
        col2 = C_CYAN_BLUE

    if not l2:
        f1 = fit_font(F_MONT_BLACK, l1, 68, max_w=940)
        d0 = ImageDraw.Draw(canvas)
        bb1 = d0.textbbox((0, 0), l1, font=f1)
        tw1, th1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
        tx1 = (cw - tw1) // 2 - bb1[0]
        ty1 = (ch - th1) // 2 - bb1[1]

        sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((tx1, ty1 + 6), l1, font=f1, fill=(0, 0, 0, 215))
        sh = sh.filter(ImageFilter.GaussianBlur(radius=10))
        canvas = Image.alpha_composite(canvas, sh)

        ImageDraw.Draw(canvas).text((tx1, ty1), l1, font=f1, fill=(255, 255, 255, 255))
        _SUB_CACHE[key] = canvas
        return canvas

    f1 = fit_font(F_MONT_BOLD, l1, 52, max_w=940)
    f2 = fit_font(F_MONT_BLACK, l2, 68, max_w=940)

    d0 = ImageDraw.Draw(canvas)
    bb1 = d0.textbbox((0, 0), l1, font=f1)
    bb2 = d0.textbbox((0, 0), l2, font=f2)
    tw1, th1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
    tw2, th2 = bb2[2] - bb2[0], bb2[3] - bb2[1]

    tx1 = (cw - tw1) // 2 - bb1[0]
    ty1 = 95 - bb1[1]
    tx2 = (cw - tw2) // 2 - bb2[0]
    ty2 = 172 - bb2[1]

    # Soft dark drop shadow behind both lines
    sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.text((tx1, ty1 + 5), l1, font=f1, fill=(0, 0, 0, 210))
    ds.text((tx2, ty2 + 6), l2, font=f2, fill=(0, 0, 0, 220))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=10))
    canvas = Image.alpha_composite(canvas, sh)

    # Subtle neon glow behind Line 2
    glow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((tx2, ty2), l2, font=f2, fill=(*col2, 145))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=14))
    canvas = Image.alpha_composite(canvas, glow)

    fg = ImageDraw.Draw(canvas)
    fg.text((tx1, ty1), l1, font=f1, fill=(*C_WHITE, 255))
    fg.text((tx2, ty2), l2, font=f2, fill=(*col2, 255))

    _SUB_CACHE[key] = canvas
    return canvas


def alpha_composite_roi(dst_rgb, src_rgba, x0=0, y0=0, alpha_mult=1.0):
    sw, sh = src_rgba.size
    x1, y1 = x0 + sw, y0 + sh
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x1), min(H, y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    arr = np.asarray(src_rgba)[cy0 - y0 : cy1 - y0, cx0 - x0 : cx1 - x0]
    a = arr[:, :, 3:4].astype(np.float32) * (float(alpha_mult) / 255.0)
    if np.max(a) <= 0.001:
        return
    roi = dst_rgb[cy0:cy1, cx0:cx1].astype(np.float32)
    fg = arr[:, :, :3].astype(np.float32)
    dst_rgb[cy0:cy1, cx0:cx1] = np.clip(roi * (1.0 - a) + fg * a, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# 6 Viral Shorts Definitions (French Subtitles, Strictly <= 2 Lines)
# ---------------------------------------------------------------------------
SHORTS_SPEC = [
    {
        "slug": "short-01-defi-perdre-100-livres-250k-9x16.mp4",
        "start": 0.0,
        "end": 52.0,
        "subs": [
            (0.00, 1.64, "Voici mon ami", "Majd.", "cyan"),
            (1.64, 4.60, "S'il perd 45 kilos", "cette année,", "cyan"),
            (4.60, 6.84, "je lui donne", "250 000 DOLLARS !", "gold"),
            (6.84, 8.72, "Voici sa toute", "nouvelle maison.", "cyan"),
            (8.72, 12.44, "Il a sa propre salle de sport", "et des repas sains illimités,", "cyan"),
            (12.44, 15.24, "tout ce qu'il faut pour", "perdre 45 kilos !", "gold"),
            (15.24, 17.36, "C'est complètement", "fou !", "cyan"),
            (17.36, 18.92, "Mais attention,", "il y a un piège :", "crimson"),
            (18.92, 20.80, "si tu dépasses", "cette ligne rouge", "crimson"),
            (20.80, 22.56, "avant d'avoir perdu", "les 45 kilos,", "crimson"),
            (22.56, 24.24, "le défi s'arrête et", "tu gagnes ZÉRO $ !", "crimson"),
            (24.24, 28.08, "S'il réussit, ce sera la plus", "grande transformation !", "gold"),
            (28.08, 31.32, "C'est ma maison pour l'année,", "c'est juste dingue !", "cyan"),
            (31.32, 35.24, "Voici ma salle de sport", "et les 250 000 $ en jeu.", "gold"),
            (35.24, 39.04, "Tout ce dont tu as besoin", "se trouve ici.", "cyan"),
            (39.04, 42.92, "Ce sera l'un des défis", "les plus longs de l'histoire.", "cyan"),
            (42.92, 46.96, "Et ce que Majd allait vivre", "dans cette vidéo", "cyan"),
            (46.96, 52.00, "allait devenir l'une de nos", "histoires les plus fortes.", "gold"),
        ],
    },
    {
        "slug": "short-02-premiers-30-jours-coach-wall-9x16.mp4",
        "start": 252.0,
        "end": 302.0,
        "subs": [
            (0.00, 1.68, "À bientôt Jimmy,", "merci !", "cyan"),
            (1.68, 3.80, "À quoi s'attendre pour", "les 30 prochains jours ?", "cyan"),
            (3.80, 6.56, "On va réduire ses calories", "progressivement,", "cyan"),
            (6.56, 9.12, "augmenter son activité", "et intensifier le cardio.", "gold"),
            (9.12, 11.40, "Donc ça va devenir", "de plus en plus dur ?", "crimson"),
            (11.40, 14.32, "Il va souffrir, ça va être", "très dur pour lui !", "crimson"),
            (14.32, 17.40, "Mais à chaque tranche de", "9 kilos perdus,", "cyan"),
            (17.40, 21.04, "vous verrez une vraie différence", "sur son physique !", "gold"),
            (21.04, 23.12, "J'ai déjà perdu 9 kilos,", "c'est incroyable !", "gold"),
            (23.12, 26.96, "Mais l'objectif final reste", "de perdre 45 kilos.", "cyan"),
            (26.96, 29.68, "Avec l'aide de Coach Wall,", "on va tout exploser !", "gold"),
            (29.68, 33.24, "Et il a tenu parole", "jour après jour !", "cyan"),
            (33.24, 36.52, "Regardez-le enchaîner :", "22 répétitions !", "gold"),
            (36.52, 39.92, "Majd était la définition même", "de la détermination.", "cyan"),
            (39.92, 43.68, "Entouré par son Coach", "et par Chandler,", "cyan"),
            (43.68, 46.84, "il s'entraînait pour le défi", "des pompes de Jimmy :", "gold"),
            (46.84, 50.00, "50 000 $ en jeu,", "je ne m'y attendais pas !", "gold"),
        ],
    },
    {
        "slug": "short-03-1000-dollars-par-pompe-9x16.mp4",
        "start": 620.0,
        "end": 672.0,
        "subs": [
            (0.00, 3.50, "Combien de pompes peux-tu faire ?", "1 000 $ par pompe !", "gold"),
            (3.50, 7.20, "1 000 $... 2 000 $...", "3 000 $... 4 000 $ !", "gold"),
            (7.20, 11.20, "5 000 $ déjà gagnés,", "continue Majd !", "cyan"),
            (11.20, 15.50, "11 000 $... 12 000 $ !", "C'est complètement fou !", "gold"),
            (15.50, 20.20, "18 000 $... 19 000 $...", "20 000 DOLLARS !", "gold"),
            (20.20, 24.50, "Tu es déjà à 20 000 $,", "il t'en reste encore !", "cyan"),
            (24.50, 29.40, "Donne tout ce que tu as,", "allez Majd !", "crimson"),
            (29.40, 34.50, "23... 25... 28...", "il ne lâche rien !", "gold"),
            (34.50, 40.50, "29... 30...", "31 POMPES !", "gold"),
            (40.50, 46.50, "31 pompes réalisées", "sans s'arrêter !", "cyan"),
            (46.50, 52.00, "31 000 $ ajoutés", "à ta cagnotte finale !", "gold"),
        ],
    },
    {
        "slug": "short-04-continuer-pour-coach-wall-9x16.mp4",
        "start": 985.0,
        "end": 1035.0,
        "subs": [
            (0.00, 2.56, "Je voulais lui dire que", "sa peine était légitime,", "cyan"),
            (2.56, 6.40, "et qu'on pouvait arrêter la vidéo", "s'il ne voulait plus continuer.", "crimson"),
            (6.40, 8.48, "« On n'arrête surtout pas", "ce défi maintenant. »", "gold"),
            (8.48, 9.50, "« Je ne peux pas", "le décevoir. »", "crimson"),
            (9.50, 13.50, "« Je le faisais pour moi,", "maintenant c'est pour Coach Wall. »", "gold"),
            (15.50, 19.00, "Pour honorer son mentor", "et ami Coach Wall,", "cyan"),
            (19.00, 22.36, "Majd a refusé de prendre", "un autre entraîneur.", "cyan"),
            (22.36, 25.50, "Et dans les jours qui ont suivi,", "seul dans la salle,", "cyan"),
            (25.50, 30.00, "il a donné chacune de ses forces", "à chaque entraînement.", "gold"),
            (34.00, 38.00, "C'est pourquoi pour son", "prochain palier au Jour 100,", "cyan"),
            (38.00, 41.04, "je tenais à lui offrir", "quelque chose en son honneur.", "gold"),
            (41.04, 45.36, "Avant le défi du Jour 100,", "voici un cadre spécial", "cyan"),
            (45.36, 50.00, "que tu pourras accrocher", "au mur pour Coach Wall.", "gold"),
        ],
    },
    {
        "slug": "short-05-course-jour-130-mrbeast-9x16.mp4",
        "start": 1295.0,
        "end": 1348.0,
        "subs": [
            (0.00, 5.40, "Majd ne perd pas une seconde", "et se remet au travail.", "cyan"),
            (5.40, 9.48, "Après plus de 4 mois", "enfermé dans cette salle,", "cyan"),
            (9.48, 13.84, "il était ultra concentré", "sur son objectif !", "gold"),
            (13.84, 17.28, "Mais la victoire était loin", "d'être garantie.", "crimson"),
            (17.28, 21.50, "Tu es prêt pour la course ?", "On y va !", "gold"),
            (21.50, 26.84, "C'est la première fois en 130 jours", "qu'il ne porte pas son t-shirt blanc !", "cyan"),
            (26.84, 31.92, "Au Jour 1, il t'avait fallu", "17 minutes pour courir 1,6 km.", "crimson"),
            (31.92, 34.44, "Aujourd'hui, 130 jours", "plus tard,", "cyan"),
            (34.44, 38.50, "tu dois le courir en moins", "de 8 minutes et 30 secondes !", "gold"),
            (38.50, 43.12, "Tu es prêt ? Allez :", "3, 2, 1...", "gold"),
            (43.12, 47.92, "PARTEZ ! Voyons s'il peut", "battre le chronomètre !", "crimson"),
            (47.92, 53.00, "Premier tour validé", "sur les 7 tours !", "gold"),
        ],
    },
    {
        "slug": "short-06-transformation-finale-178-jours-9x16.mp4",
        "start": 2125.0,
        "end": 2180.0,
        "subs": [
            (0.00, 6.24, "Le moment de vérité :", "place aux résultats !", "gold"),
            (6.24, 12.96, "IL A RÉUSSI LE DÉFI", "DES 45 KILOS !", "gold"),
            (12.96, 18.50, "On va faire quelque chose", "d'encore plus fort :", "cyan"),
            (18.50, 25.00, "voici son évolution complète", "étape par étape", "cyan"),
            (25.00, 30.76, "jusqu'à sa transformation", "finale aujourd'hui !", "gold"),
            (30.76, 35.80, "Le voici après", "6 mois d'efforts !", "gold"),
            (35.80, 41.32, "Une transformation physique", "absolument incroyable !", "cyan"),
            (41.32, 45.44, "Après 178 jours enfermé", "dans ce cercle,", "crimson"),
            (45.44, 49.40, "enlève tes mains de tes yeux :", "voici toute ta famille !", "gold"),
            (49.40, 55.00, "178 JOURS D'EFFORT", "ET UNE VICTOIRE HISTORIQUE !", "gold"),
        ],
    },
]


def render_single_short(spec, bottom_vig):
    slug = spec["slug"]
    t_start = spec["start"]
    t_end = spec["end"]
    dur = t_end - t_start
    subs = spec["subs"]
    out_path = os.path.join(OUT_DIR, slug)

    # Skip if already completely rendered
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5_000_000:
        cap_chk = cv2.VideoCapture(out_path)
        n_chk = int(cap_chk.get(cv2.CAP_PROP_FRAME_COUNT))
        cap_chk.release()
        if abs(n_chk - int(round(dur * FPS))) <= 15:
            mb = os.path.getsize(out_path) / (1024 * 1024)
            print(f"Skipping already rendered {slug} ({n_chk} frames, {mb:.2f} MB)")
            return out_path

    ff = imageio_ffmpeg.get_ffmpeg_exe()

    # Extract & clean audio for this short (broadcast EQ + loudness normalization)
    wav_path = f"/tmp/vp_inspect/{slug}.wav"
    subprocess.run(
        [
            ff, "-y", "-v", "error",
            "-ss", f"{t_start:.2f}", "-t", f"{dur:.2f}",
            "-i", SRC_MP4, "-vn",
            "-af", "highpass=f=75,equalizer=f=3200:width_type=o:width=1.4:g=1.8,acompressor=threshold=-16dB:ratio=2.0:attack=12:release=180:makeup=2dB",
            "-ac", "2", "-ar", "44100", wav_path,
        ],
        check=True,
    )

    # Instantaneous FFmpeg input seek + C-level 9:16 crop, bicubic 1080x1920 upscale & unsharp mask
    dec_cmd = [
        ff, "-v", "error",
        "-ss", f"{t_start:.2f}", "-t", f"{dur:.2f}",
        "-i", SRC_MP4,
        "-vf", "fps=30,crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=bicubic,unsharp=5:5:0.8:5:5:0.0",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    dec_proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)

    enc_cmd = [
        ff, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", "30", "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-maxrate", "3200k", "-bufsize", "6400k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        out_path,
    ]
    enc_proc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, bufsize=W * H * 3 * 2)

    # Only composite bottom darkening on y=960..1920 (bottom half of frame) for 2x speed!
    vig_roi_a = bottom_vig[960:H, :, 3:4].astype(np.float32) * (1.0 / 255.0)
    vig_roi_rgb = bottom_vig[960:H, :, :3].astype(np.float32)

    raw_bytes = W * H * 3
    f_idx = 0
    while True:
        buf = dec_proc.stdout.read(raw_bytes)
        if len(buf) < raw_bytes:
            break
        frame_rgb = np.frombuffer(buf, dtype=np.uint8).reshape((H, W, 3)).copy()
        lt = f_idx / FPS
        f_idx += 1

        # Apply subtle bottom darkening on lower half (no box around subtitles!)
        bot = frame_rgb[960:H]
        frame_rgb[960:H] = np.clip(
            bot.astype(np.float32) * (1.0 - vig_roi_a) + vig_roi_rgb * vig_roi_a,
            0, 255,
        ).astype(np.uint8)

        # Render active <= 2-line subtitle at lower-third (y=1360)
        for s0, s1, l1, l2, acc in subs:
            if s0 <= lt < s1:
                age = lt - s0
                rem = s1 - lt
                p_in = ease_out_back(clamp(age / 0.16), s=1.25)
                p_out = clamp(rem / 0.10) if rem < 0.10 else 1.0
                sp = get_subtitle_sprite(l1, l2, acc)
                sy = int(1360 + (1.0 - p_in) * 18)
                alpha_composite_roi(frame_rgb, sp, 0, sy, alpha_mult=min(1.0, p_out))
                break

        enc_proc.stdin.write(frame_rgb.tobytes())

    dec_proc.stdout.close()
    dec_proc.wait()
    enc_proc.stdin.close()
    enc_proc.wait()
    mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Rendered {slug} ({dur:.1f}s, {mb:.2f} MB)", flush=True)
    return out_path


def main():
    t0 = time.time()
    bottom_vig = build_bottom_vignette()
    rendered = []
    for spec in SHORTS_SPEC:
        p = render_single_short(spec, bottom_vig)
        rendered.append(p)

    # Build a 6-panel preview sheet (one mid-frame per Short) for visual QA
    thumbs = []
    for p in rendered:
        cap = cv2.VideoCapture(p)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 60)
        ok, f = cap.read()
        cap.release()
        if ok:
            thumbs.append(cv2.resize(f, (360, 640), interpolation=cv2.INTER_AREA))
    if len(thumbs) == 6:
        grid = np.vstack([np.hstack(thumbs[:3]), np.hstack(thumbs[3:])])
        cv2.imwrite("/tmp/vp_inspect/shorts_preview_6.jpg", grid, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"All 6 Shorts rendered in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    main()
