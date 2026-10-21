#!/usr/bin/env python3
"""
Generator for 10 Viral Vertical 9:16 Shorts (1080x1920 @ 30fps)
from `imports/Stop_This_Train__Win_a_Lamborghini.mp4`
("Stop This Train, Win a Lamborghini" - MrBeast)

Strict compliance with user instructions:
- "Le lien de la vidéo est dans le studio coupe le en 10 short"
- "Stop_This_Train__Win_a_Lamborghini.mp4 est maintenant dans le studio"
- "Faire moi plusieurs short pour les reseau sociaux juste avec des sous titres"
- "pas plus de 2 ligne de sous-titre" (strictly <= 2 lines at a time)
- Zero rectangle/box around subtitles, zero black stroke outlines (`stroke_width=0`),
  soft multi-layer Gaussian drop shadow + kinetic pop-in easing (`ease_out_back`).
"""

import os
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

W, H = 1080, 1920
FPS = 30.0
ROI_Y0 = 1160  # Lower region where vignette + subtitles live (y=1160..1920)
ROI_H = H - ROI_Y0

REPO_ROOT = "/home/user/COOL-backup"
SRC_MP4 = os.path.join(REPO_ROOT, "imports/Stop_This_Train__Win_a_Lamborghini.mp4")
OUT_DIR = os.path.join(REPO_ROOT, "mrbeast-train-lambo-shorts/shorts")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs("/tmp/lambo_inspect", exist_ok=True)

FONT_DIR = "/tmp/work_cache/fonts/node_modules"
F_MONT_BLACK = f"{FONT_DIR}/@expo-google-fonts/montserrat/900Black/Montserrat_900Black.ttf"
F_MONT_BOLD = f"{FONT_DIR}/@expo-google-fonts/montserrat/700Bold/Montserrat_700Bold.ttf"

# Signature palette for Line 2 emphasis
C_WHITE = (255, 255, 255)
C_GOLD = (255, 212, 59)
C_CYAN_BLUE = (56, 189, 248)
C_CRIMSON = (255, 92, 119)

_FONT_CACHE = {}
_SUB_SPRITE_CACHE = {}
_BAKED_OVERLAY_CACHE = {}


def get_font(path: str, size: int):
    k = (path, size)
    if k not in _FONT_CACHE:
        _FONT_CACHE[k] = ImageFont.truetype(path, size)
    return _FONT_CACHE[k]


def fit_font(path: str, text: str, max_size: int, max_w: int = 960, min_size: int = 28):
    sz = max_size
    dummy = Image.new("RGBA", (16, 16))
    d = ImageDraw.Draw(dummy)
    while sz >= min_size:
        f = get_font(path, sz)
        if d.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        sz -= 2
    return get_font(path, min_size)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out_back(t, s=1.35):
    t = clamp(t)
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def build_bottom_vignette_roi():
    """Smoothly darkens the lower part of the Short (y=1160..1920) with zero box framing."""
    yy, xx = np.mgrid[ROI_Y0:H, 0:W].astype(np.float32)
    bottom_dark = np.clip((yy - H * 0.60) / (H * 0.40), 0.0, 1.0) ** 1.35 * 0.68
    edge_vig = np.clip(((xx - W * 0.5) / (W * 0.54)) ** 2 + ((yy - H * 0.5) / (H * 0.54)) ** 2 - 0.42, 0.0, 1.0) * 0.20
    alpha = np.clip(bottom_dark + edge_vig, 0.0, 0.74)
    rgba = np.zeros((ROI_H, W, 4), dtype=np.uint8)
    rgba[:, :, 0] = 4
    rgba[:, :, 1] = 7
    rgba[:, :, 2] = 16
    rgba[:, :, 3] = (alpha * 255.0).astype(np.uint8)
    return rgba


VIG_ROI_RGBA = build_bottom_vignette_roi()


def bake_uint16_overlay(rgba_roi: np.ndarray):
    """Precomputes (inv_a_u16, premul_rgb_u16) for ultra-fast uint16 blending."""
    a_u16 = rgba_roi[:, :, 3:4].astype(np.uint16)
    inv_a = 256 - a_u16
    premul_rgb = rgba_roi[:, :, :3].astype(np.uint16) * a_u16
    return inv_a, premul_rgb


VIG_ONLY_BAKED = bake_uint16_overlay(VIG_ROI_RGBA)


def get_subtitle_sprite(l1: str, l2: str, accent: str) -> Image.Image:
    """
    Pre-renders a crisp <= 2-line subtitle sprite (1080x360) with soft Gaussian
    drop shadow, neon accent glow on line 2, and zero background box.
    """
    key = (l1, l2, accent)
    if key in _SUB_SPRITE_CACHE:
        return _SUB_SPRITE_CACHE[key]

    cw, ch = W, 360
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    if accent == "gold":
        col2 = C_GOLD
    elif accent == "crimson":
        col2 = C_CRIMSON
    else:
        col2 = C_CYAN_BLUE

    f1 = fit_font(F_MONT_BOLD, l1, 50, max_w=950)
    f2 = fit_font(F_MONT_BLACK, l2, 66, max_w=950)

    d0 = ImageDraw.Draw(canvas)
    bb1 = d0.textbbox((0, 0), l1, font=f1)
    bb2 = d0.textbbox((0, 0), l2, font=f2)
    tw1 = bb1[2] - bb1[0]
    tw2 = bb2[2] - bb2[0]

    tx1 = (cw - tw1) // 2 - bb1[0]
    ty1 = 95 - bb1[1]
    tx2 = (cw - tw2) // 2 - bb2[0]
    ty2 = 172 - bb2[1]

    # Soft dark drop shadow behind both lines
    sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.text((tx1, ty1 + 5), l1, font=f1, fill=(0, 0, 0, 215))
    ds.text((tx2, ty2 + 6), l2, font=f2, fill=(0, 0, 0, 225))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=10))
    canvas = Image.alpha_composite(canvas, sh)

    # Subtle neon glow behind Line 2
    glow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((tx2, ty2), l2, font=f2, fill=(*col2, 85))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=14))
    canvas = Image.alpha_composite(canvas, glow)

    # Crisp foreground text (Line 1 pure white, Line 2 accent color)
    df = ImageDraw.Draw(canvas)
    df.text((tx1, ty1), l1, font=f1, fill=(*C_WHITE, 255))
    df.text((tx2, ty2), l2, font=f2, fill=(*col2, 255))

    _SUB_SPRITE_CACHE[key] = canvas
    return canvas


def get_baked_steady_overlay(l1: str, l2: str, accent: str):
    """Returns pre-composited (vignette + steady subtitle) uint16 arrays on y=1160..1920."""
    key = (l1, l2, accent)
    if key in _BAKED_OVERLAY_CACHE:
        return _BAKED_OVERLAY_CACHE[key]

    vig_pil = Image.fromarray(VIG_ROI_RGBA, mode="RGBA")
    sp = get_subtitle_sprite(l1, l2, accent)
    # Subtitle sits at y=1360 in full frame -> y = 1360 - 1160 = 200 in ROI
    vig_pil.alpha_composite(sp, (0, 1360 - ROI_Y0))
    combined = np.array(vig_pil, dtype=np.uint8)
    baked = bake_uint16_overlay(combined)
    _BAKED_OVERLAY_CACHE[key] = baked
    return baked


# ==============================================================================
# 10 VIRAL SHORTS DEFINITIONS (Each ~50-58s, <= 2 lines per subtitle)
# ==============================================================================
SHORTS = [
    {
        "slug": "short-01-defi-lamborghini-10000-balles-9x16.mp4",
        "start": 0.0,
        "end": 50.0,
        "subs": [
            (0.00, 4.00, "Posée sur ces rails se trouve", "une Lamborghini à 250 000 $ !", "gold"),
            (4.00, 7.20, "Et un train géant fonce", "droit sur elle en ce moment même.", "crimson"),
            (7.20, 12.30, "Mais avant l'impact,", "j'offre cette Lamborghini à Blake !", "cyan"),
            (12.30, 17.18, "Et 8 soldats vont aussi tirer", "10 000 balles sur ta voiture !", "crimson"),
            (17.18, 21.00, "« C'est la chose la plus", "terrifiante que j'aie jamais vue ! »", "gold"),
            (21.00, 25.28, "Tu as exactement 24 heures", "pour construire ta défense.", "cyan"),
            (25.28, 30.44, "Première ligne : un mur de béton,", "puis des conteneurs maritimes,", "gold"),
            (30.44, 36.22, "remplis de réfrigérateurs,", "et une rangée de voitures !", "cyan"),
            (36.22, 42.02, "Tu penses que tout ça suffira", "pour arrêter 10 000 balles ?", "crimson"),
            (42.02, 50.00, "Blake dévalise trois magasins", "et dépense 28 000 $ de matériaux !", "gold"),
        ],
    },
    {
        "slug": "short-02-forteresse-beton-100k-bonus-9x16.mp4",
        "start": 110.0,
        "end": 160.0,
        "subs": [
            (0.00, 4.48, "Il empile des blocs de béton", "et des conteneurs avec une grue !", "gold"),
            (4.48, 9.00, "En voyant sa forteresse terminée,", "j'étais franchement impressionné.", "cyan"),
            (9.00, 15.96, "« J'ai construit le mur le plus haut", "face aux mitrailleuses lourdes. »", "crimson"),
            (15.96, 20.00, "Avec les conteneurs métalliques", "et les citernes d'eau devant,", "cyan"),
            (20.00, 25.36, "sa Lamborghini est bien à l'abri", "tout au fond du bunker !", "gold"),
            (25.36, 29.44, "Tu penses que ça va vraiment", "bloquer toutes les balles ?", "cyan"),
            (29.44, 33.44, "Je te donne 50 % de chances :", "c'est ton meilleur pronostic !", "gold"),
            (33.44, 37.00, "Mais avant de tirer les 10 000 balles,", "viens voir ta Lamborghini...", "crimson"),
            (37.00, 43.96, "Tu ne joues pas que la voiture :", "il y a 100 000 $ en cash dedans !", "gold"),
            (43.96, 50.00, "LES 24 HEURES SONT ÉCOULÉES :", "OUVREZ LE FEU !", "crimson"),
        ],
    },
    {
        "slug": "short-03-assaut-10000-balles-verdict-9x16.mp4",
        "start": 225.0,
        "end": 275.0,
        "subs": [
            (0.00, 5.80, "Il suffit d'une seule balle", "qui traverse le mur...", "crimson"),
            (5.80, 12.08, "et elle finit directement", "dans sa Lamborghini !", "gold"),
            (12.08, 18.84, "Les dernières rafales", "transpercent les barils d'eau !", "crimson"),
            (18.84, 24.52, "« Pitié, faites qu'elle soit intacte,", "faites qu'elle soit intacte ! »", "cyan"),
            (24.52, 31.12, "La fumée se dissipe enfin :", "il court vérifier la carrosserie...", "gold"),
            (31.12, 36.28, "10 000 balles tirées :", "PAS UN SEUL IMPACT sur la voiture !", "gold"),
            (36.28, 41.08, "Blake avait déjà perdu deux fois", "dans nos précédentes vidéos,", "cyan"),
            (41.08, 45.36, "mais aujourd'hui, c'est son", "ultime chance de tout gagner !", "gold"),
            (45.36, 50.00, "Prêt pour l'étape 2 ? Regarde", "cette grue géante qui arrive...", "crimson"),
        ],
    },
    {
        "slug": "short-04-nuit-blanche-matelas-chateaux-9x16.mp4",
        "start": 340.0,
        "end": 390.0,
        "subs": [
            (0.00, 4.60, "Son plan : des coussins, du papier", "bulle et des châteaux gonflables !", "gold"),
            (4.60, 10.56, "« Mon plus gros problème :", "je n'ai que du béton et du métal, »", "crimson"),
            (10.56, 14.36, "« rien de tout ça ne peut", "amortir une chute libre ! »", "cyan"),
            (14.36, 19.96, "Blake envoie son équipe acheter", "tous les matelas de la ville.", "gold"),
            (19.96, 24.84, "Épuisé, il se demande :", "« Pourquoi je fais ça déjà ? »", "cyan"),
            (24.84, 27.84, "« Ah oui : ma Lamborghini est", "suspendue dans le ciel ! »", "gold"),
            (27.84, 33.88, "Après plus de 24 heures sans dormir,", "Blake tombe de fatigue à 4h du matin.", "crimson"),
            (33.88, 41.56, "Tellement épuisé qu'il dort", "beaucoup plus longtemps que prévu !", "cyan"),
            (41.56, 46.16, "« Blake ! Il est sérieux là ?", "Qu'est-ce qu'il fabrique ?! »", "crimson"),
            (46.16, 50.00, "Endormi sur les matelas", "alors que le chrono tourne !", "gold"),
        ],
    },
    {
        "slug": "short-05-chute-libre-lamborghini-grue-9x16.mp4",
        "start": 495.0,
        "end": 548.0,
        "subs": [
            (0.00, 5.00, "24 heures de travail résumées à ça :", "3, 2, 1... LÂCHEZ LA LAMBORGHINI !", "crimson"),
            (5.00, 13.88, "La voiture tombe de 30 mètres", "droit sur les châteaux gonflables !", "gold"),
            (13.88, 19.88, "Elle rebondit violemment", "et s'enfonce dans les cartons...", "crimson"),
            (19.88, 24.68, "« Ce bruit n'était pas rassurant...", "Pitié, faites qu'elle n'ait rien ! »", "cyan"),
            (24.68, 30.64, "Il dégage la grue et les cartons", "pour découvrir l'état de la voiture.", "gold"),
            (30.64, 35.80, "Incroyable : les phares fonctionnent", "et le pare-brise est intact !", "cyan"),
            (35.80, 39.92, "Le château gonflable de princesse", "a sauvé toute la Lamborghini !", "gold"),
            (39.92, 43.52, "Tu es la première personne de l'histoire", "à rattraper une Lamborghini en vol !", "cyan"),
            (43.52, 48.64, "Voyons si le moteur démarre...", "Attention, moment de vérité...", "gold"),
            (48.64, 53.00, "LE MOTEUR RUGIT :", "ELLE A SURVÉCU À LA CHUTE !", "gold"),
        ],
    },
    {
        "slug": "short-06-revanche-voitures-en-feu-9x16.mp4",
        "start": 570.0,
        "end": 620.0,
        "subs": [
            (0.00, 6.44, "Voici son pire cauchemar : le défi", "des voitures en feu qui l'avait éliminé !", "crimson"),
            (6.44, 10.00, "« Waouh, ça c'est vraiment", "un coup bas Jimmy ! »", "gold"),
            (10.00, 14.10, "Et cette fois, on double la mise :", "deux fois plus de voitures larguées !", "crimson"),
            (14.10, 17.40, "« J'ai une revanche à prendre :", "c'est le jour de la rédemption ! »", "cyan"),
            (17.40, 25.32, "Toute la nuit, Blake démonte", "l'ancienne structure pour l'étape 3.", "gold"),
            (25.32, 31.04, "Réveil à 8h du matin :", "voici son nouveau plan de défense !", "cyan"),
            (31.04, 35.88, "Il découpe un conteneur en acier", "pour le poser autour de la voiture,", "gold"),
            (35.88, 40.96, "puis incline deux autres conteneurs", "en triangle juste au-dessus !", "cyan"),
            (40.96, 45.96, "Et surtout : AUCUN matériau", "inflammable cette fois-ci !", "crimson"),
            (45.96, 50.00, "Son équipe retire la moindre", "planche de bois du chantier.", "gold"),
        ],
    },
    {
        "slug": "short-07-pluie-10-voitures-en-flammes-9x16.mp4",
        "start": 695.0,
        "end": 745.0,
        "subs": [
            (0.00, 5.12, "Tu avais perdu 500 000 $ sur", "ce même défi : comment tu te sens ?", "crimson"),
            (5.12, 9.88, "« Franchement confiant : cette fois,", "je n'ai mis aucun bois à l'intérieur ! »", "cyan"),
            (9.88, 14.68, "« C'était la plus grosse erreur", "de toute ma vie la dernière fois. »", "gold"),
            (14.68, 20.12, "Trois conteneurs, de la terre, du béton", "et un toit métallique en pointe...", "cyan"),
            (20.12, 24.88, "CONTRE 10 VOITURES EN FLAMMES", "larguées depuis les airs !", "crimson"),
            (24.88, 29.12, "Mettez le feu à la première voiture", "et montez-la tout là-haut !", "gold"),
            (29.12, 34.60, "Blake va-t-il repartir avec", "la Lamborghini et les 100 000 $,", "cyan"),
            (34.60, 39.96, "ou tout perdre dans les flammes ?", "3, 2, 1... LÂCHEZ-LA !", "crimson"),
            (39.96, 45.12, "BOUM ! La première voiture", "s'écrase en plein sur le sommet !", "gold"),
            (45.12, 50.00, "« Aïe, ça me rappelle", "de très mauvais souvenirs ! »", "crimson"),
        ],
    },
    {
        "slug": "short-08-bunker-ecrase-1000-degres-9x16.mp4",
        "start": 850.0,
        "end": 903.0,
        "subs": [
            (0.00, 6.12, "On largue voiture après voiture,", "et Blake devient de plus en plus nerveux.", "crimson"),
            (6.12, 13.28, "Sous la violence des impacts,", "le conteneur du bas commence à plier !", "gold"),
            (13.28, 19.52, "La structure qui protège la Lamborghini", "s'affaisse sous le poids et les flammes.", "crimson"),
            (19.52, 24.12, "« J'ai cauchemardé de ce moment", "chaque jour depuis la dernière vidéo ! »", "cyan"),
            (24.12, 30.04, "Voici la 10e et dernière voiture :", "elle écrase le toit dans un brasier !", "crimson"),
            (30.04, 34.24, "« Il doit faire 1 000 degrés là-dedans,", "sa voiture est en train de fondre ! »", "gold"),
            (34.24, 39.40, "Les pompiers éteignent l'incendie", "et Blake fonce dans la fumée...", "cyan"),
            (39.40, 45.08, "Comment elle est ?! « ELLE EST INTACTE !", "ELLE N'A ABSOLUMENT RIEN ! »", "gold"),
            (45.08, 49.64, "Une voiture de plus et le plafond", "se serait effondré sur le toit !", "crimson"),
            (49.64, 53.00, "10 000 balles, une chute libre", "et 10 voitures en feu : SURVÉCU !", "gold"),
        ],
    },
    {
        "slug": "short-09-plan-faire-derailler-le-train-9x16.mp4",
        "start": 925.0,
        "end": 975.0,
        "subs": [
            (0.00, 6.44, "Blake sait que le train lancé à pleine", "vitesse sera l'attaque la plus mortelle.", "crimson"),
            (6.44, 11.72, "« La meilleure façon d'arrêter un train,", "c'est de le faire dérailler ! »", "gold"),
            (11.72, 17.28, "Il coince des traverses en bois", "en biais tout le long des rails.", "cyan"),
            (17.28, 23.36, "« Si je répète ça une centaine de fois,", "le train ne pourra jamais passer ! »", "gold"),
            (23.36, 27.20, "« Ces traverses m'avaient fait perdre :", "aujourd'hui elles vont me sauver ! »", "cyan"),
            (27.20, 31.96, "Il suffit de soulever les roues", "de 5 centimètres pour qu'il déraille.", "crimson"),
            (31.96, 37.20, "Puis il recouvre les rails", "avec d'énormes blocs de béton !", "gold"),
            (37.20, 43.50, "Toute la nuit, Blake et son équipe", "érigent trois murs géants devant la voiture.", "cyan"),
            (43.50, 50.00, "24 heures d'effort acharné", "avant l'impact final du train !", "gold"),
        ],
    },
    {
        "slug": "short-10-impact-final-train-lamborghini-9x16.mp4",
        "start": 1065.0,
        "end": 1123.0,
        "subs": [
            (0.00, 5.80, "C'est le plus grand moment de sa vie :", "« LÂCHEZ LE TRAIN ! »", "crimson"),
            (5.80, 12.60, "Le train accélère jusqu'à 55 km/h", "et fonce droit vers la Lamborghini !", "gold"),
            (12.60, 18.00, "« Il va dérailler, il va dérailler !", "Attention à l'impact ! »", "crimson"),
            (18.00, 26.00, "CRASH MONUMENTAL : le train explose", "le premier mur et sort des rails !", "gold"),
            (26.00, 33.00, "La locomotive s'arrête net", "dans un nuage de poussière géant !", "cyan"),
            (33.00, 38.00, "« ATTENDEZ ! IL S'EST ARRÊTÉ !", "Je n'ai jamais vu un truc pareil ! »", "gold"),
            (38.00, 45.00, "« OH MON DIEU, J'AI RÉUSSI ! »", "Le train a déraillé juste devant !", "cyan"),
            (45.00, 52.00, "Voici ta nouvelle Lamborghini Blake,", "ET les 100 000 $ en liquide !", "gold"),
            (52.00, 58.00, "UN TRAIN ARRÊTÉ ET UNE VICTOIRE", "LÉGENDAIRE POUR BLAKE !", "gold"),
        ],
    },
]


def render_single_short(spec):
    slug = spec["slug"]
    t_start = spec["start"]
    t_end = spec["end"]
    dur = t_end - t_start
    subs = spec["subs"]
    out_path = os.path.join(OUT_DIR, slug)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 4_000_000:
        cap_chk = cv2.VideoCapture(out_path)
        n_chk = int(cap_chk.get(cv2.CAP_PROP_FRAME_COUNT))
        cap_chk.release()
        if abs(n_chk - int(round(dur * FPS))) <= 15:
            mb = os.path.getsize(out_path) / (1024 * 1024)
            print(f"Skipping already rendered {slug} ({n_chk} frames, {mb:.2f} MB)")
            return out_path

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    t0_short = time.time()

    # Pre-warm steady subtitle caches for this short
    for _, _, l1, l2, acc in subs:
        get_baked_steady_overlay(l1, l2, acc)

    # Extract & master audio for this short
    wav_path = f"/tmp/lambo_inspect/{slug}.wav"
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

    # Instantaneous FFmpeg input seek + 9:16 center crop & 1080x1920 upscale from 1280x720 HD
    dec_cmd = [
        ff, "-v", "error",
        "-ss", f"{t_start:.2f}", "-t", f"{dur:.2f}",
        "-i", SRC_MP4,
        "-vf", "fps=30,crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=bicubic",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    dec_proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)

    enc_cmd = [
        ff, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", "30", "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-maxrate", "2000k", "-bufsize", "4000k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        out_path,
    ]
    enc_proc = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE, bufsize=W * H * 3 * 2)

    vig_inv_a, vig_premul = VIG_ONLY_BAKED
    raw_bytes = W * H * 3
    f_idx = 0

    while True:
        buf = dec_proc.stdout.read(raw_bytes)
        if len(buf) < raw_bytes:
            break
        frame_rgb = np.frombuffer(buf, dtype=np.uint8).reshape((H, W, 3)).copy()
        lt = f_idx / FPS
        f_idx += 1

        active_sub = None
        for s0, s1, l1, l2, acc in subs:
            if s0 <= lt < s1:
                active_sub = (s0, s1, l1, l2, acc)
                break

        roi = frame_rgb[ROI_Y0:H]
        if active_sub is None:
            frame_rgb[ROI_Y0:H] = ((roi.astype(np.uint16) * vig_inv_a + vig_premul) >> 8).astype(np.uint8)
        else:
            s0, s1, l1, l2, acc = active_sub
            dt = lt - s0
            if dt >= 0.18:
                # Fast path (96% of frames): single uint16 blend of vignette + steady subtitle
                inv_a, premul = get_baked_steady_overlay(l1, l2, acc)
                frame_rgb[ROI_Y0:H] = ((roi.astype(np.uint16) * inv_a + premul) >> 8).astype(np.uint8)
            else:
                # First 5 frames of subtitle: kinetic pop-in easing
                frame_rgb[ROI_Y0:H] = ((roi.astype(np.uint16) * vig_inv_a + vig_premul) >> 8).astype(np.uint8)
                sp = get_subtitle_sprite(l1, l2, acc)
                p = clamp(dt / 0.18)
                sc = 0.88 + 0.12 * ease_out_back(p, 1.35)
                nw = max(1, int(sp.width * sc))
                nh = max(1, int(sp.height * sc))
                sp_s = sp.resize((nw, nh), Image.Resampling.BILINEAR)
                arr = np.array(sp_s, dtype=np.uint8)
                arr[:, :, 3] = (arr[:, :, 3].astype(np.uint16) * int(p * 255) >> 8).astype(np.uint8)
                px = (W - nw) // 2
                py = 1360 + (sp.height - nh) // 2
                x0, y0 = max(0, px), max(0, py)
                x1, y1 = min(W, px + nw), min(H, py + nh)
                sub_crop = arr[y0 - py : y1 - py, x0 - px : x1 - px]
                sa = sub_crop[:, :, 3:4].astype(np.uint16)
                s_inv = 256 - sa
                s_pre = sub_crop[:, :, :3].astype(np.uint16) * sa
                dst = frame_rgb[y0:y1, x0:x1]
                frame_rgb[y0:y1, x0:x1] = ((dst.astype(np.uint16) * s_inv + s_pre) >> 8).astype(np.uint8)

        enc_proc.stdin.write(frame_rgb.tobytes())

    dec_proc.stdout.close()
    dec_proc.wait()
    enc_proc.stdin.close()
    enc_proc.wait()

    mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Rendered {slug} ({dur:.1f}s, {mb:.2f} MB) in {time.time() - t0_short:.1f}s", flush=True)
    return out_path


def main():
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(render_single_short, SHORTS))
    print(f"All {len(SHORTS)} Lamborghini Shorts rendered in {time.time() - t0:.1f}s!")


if __name__ == "__main__":
    main()
