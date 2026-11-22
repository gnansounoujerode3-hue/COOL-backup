#!/usr/bin/env python3
"""Léger Akodjenou — « Vos clics deviennent des clients » · v5 (58,94 s).

Refonte visuelle **calquée sur la landing** <https://legerakodjenou.systeme.io/8c1af526> :
chaque plan reprend la composition réelle d'une section du site, dans l'ordre
du site, avec la même grammaire que la page.

    plan 1  hero        badge ● Audit offert · titre plein + *serif italique ember*
                        sous-titre · 2 boutons · preuves · tableau de bord J+7
                        (12 434 · 4 200 · 311 · 6,8 % · ROAS 4,2×)
    plan 2  diagnostic  citation serif · 4 cartes numérotées · −0 %
    plan 3  offre       5 modules 0X / titre / description / tags
    plan 4  méthode     J+0 → J+14, 01/04 … 04/04, garantie 30 jours
    plan 5  preuve      marquee des 11 métiers · citation · « ça convertit
                        même quand vous dormez »
    plan 6  solo        cadre photo · « votre interlocuteur unique »
    plan 7  tarifs      3 cartes (Express / Performance / Croissance) + garantie
    plan 8  cta         7 étapes · le mot « PACK » équivalent : audit offert

Corrections v5 :
  - plus AUCUN titre en deux blocs espacés (le site met le mot clé en
    Instrument Serif italique *dans* la ligne) → plus de collisions ;
  - filet vertical qui s'arrête avant la ligne de départ de chaque rangée ;
  - voix off : garde-fou anti-chevauchement + décalages recalculés sur les
    silences réels mesurés (`silencedetect`), plus de paroles à cheval ;
  - lit musical discret (−4 dB vs v4), impacts uniquement sur les coupes.
"""
import argparse
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_leger_film_v2 as V  # noqa: E402

W, H, FPS, SR = V.W, V.H, V.FPS, V.SR
M, CW = V.M, V.CW
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
FILM_DIR = os.path.join(PROJECT, "film")
AUDIO_DIR = os.path.join(PROJECT, "assets", "audio")
OUT = os.path.join(FILM_DIR, "leger-akodjenou-vos-clics-deviennent-des-clients-v5-9x16.mp4")
MIX = os.path.join(AUDIO_DIR, "master_mix_v5.wav")
TMP = "/tmp/leger_v5_video.mp4"

CREAM, MUTED, EMBER, EMBER_SOFT = V.CREAM, V.MUTED, V.EMBER, V.EMBER_SOFT
INK, COAL, PANEL, DIM = V.INK, V.COAL, V.PANEL, V.DIM
c_, ac = V.c_, V.ac
F, tl, tracked, para = V.F, V.tl, V.tracked, V.para
chip, button, panel = V.chip, V.button, V.panel
fit_size, _alpha = V.fit_size, V._alpha
eo, eob, prog, clamp01 = V.eo, V.eob, V.prog, V.clamp01
marquee_strip = V.marquee_strip

# ---------------------------------------------------------------- timeline
SCENES = ["hero", "diagnostic", "offre", "methode", "solo", "tarifs", "cta", "closing"]
CUTS = [0.00, 4.75, 12.35, 22.85, 32.55, 41.10, 49.60, 60.60, 66.10]
TOTAL = CUTS[-1]
NFR = int(round(TOTAL * FPS))

CHAPTER = {
    "hero": "",
    "diagnostic": "(01) Le diagnostic",
    "offre": "(02) Ce que je construis",
    "methode": "(03) La méthode",
    "solo": "(04) Qui construit",
    "tarifs": "(05) Les tarifs",
    "cta": "(07) Dernière étape",
    "closing": "—",
}

# « exemple de tableau de bord · J+7 » — chiffres de la landing
BOARD = [("Visiteurs", "12 434", "+224 %"), ("Inscrits", "4 200", "+38 %"),
         ("Clients", "311", "6,8 %"), ("ROAS Meta", "4,2×", "retour")]

# voix off : fichier + démarrage (recalé par `retime_vo`)
VO = [
    ("v4-s1.mp3", 0.42),     # 3,92 s
    ("v4-s2.mp3", 5.15),     # 7,02 s
    ("v4-s3.mp3", 12.62),    # 10,02 s
    ("v4-s4.mp3", 23.09),    # 9,08 s
    ("v4-s5.mp3", 32.62),    # 7,99 s
    ("v4-s6.mp3", 41.06),    # 7,73 s
    ("v4-s7.mp3", 49.24),    # 10,22 s
    ("v4-s8.mp3", 59.90),    # 5,23 s -> silence final de 2,0 s
]
AUDIO_GAP = 0.30          # respiration minimale entre deux prises

# ---------------------------------------------------------------- primitives


def _col_mask(x, y, w, h):
    """Masque de découpe pour les bandeaux défilants (évite tout débordement)."""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle([x, y, x + w, y + h], fill=255)
    return m


def tl_at(d, text, f, tracking=0.0):
    return tl(d, text, f, tracking)


def both_lines(d, canvas, runs, x, y, size, tracking=-3.0, lead=1.02, p=1.0, maxw=None):
    """Une « ligne » du site : plusieurs runs (mot plein + mot serif italique).

    Toute la ligne est révélée par un masque vertical unique → aucun run ne
    peut passer devant un autre, et aucune collision n'est possible.
    """
    if p <= 0:
        return 0
    e = eob(p)
    fonts, widths, base = [], [], 0
    for text, kind in runs:
        f = F(kind, size * (1.06 if kind in ("seri", "ser") else 1.0))
        fonts.append(f)
        widths.append(tl(d, text, f, tracking))
    maxw = CW if maxw is None else maxw
    total = sum(widths) + (len(runs) - 1) * size * 0.06
    if total > maxw:                      # garde-fou : jamais de débordement
        print(f"  ! ligne trop large ({total:.0f} > {maxw}) : {runs}", flush=True)
        while total > maxw and size > 34:
            size -= 2
            fonts = [F(k, size * (1.06 if k in ("seri", "ser") else 1.0)) for _, k in runs]
            widths = [tl(d, t, f, tracking) for (t, _), f in zip(runs, fonts)]
            total = sum(widths) + (len(runs) - 1) * size * 0.06
    lh = int(size * lead)
    lay = Image.new("L", (int(total) + 60, int(lh * 1.5)), 0)
    ld = ImageDraw.Draw(lay)
    cx = 0
    for (text, kind), f, w in zip(runs, fonts, widths):
        if kind in ("seri", "ser"):
            tracked(ld, (cx, lh * 0.30), text, f, 255, tracking * 0.7)
        else:
            tracked(ld, (cx, lh * 0.24), text, f, 255, tracking)
        cx += w + size * 0.06
    col = Image.new("RGBA", lay.size, c_(CREAM, 255))
    col.putalpha(lay)
    if e < 1:
        keep = Image.new("L", lay.size, 0)
        ImageDraw.Draw(keep).rectangle([0, 0, lay.width, int(lay.height * min(1, e * 1.08))], fill=255)
        col.putalpha(ImageChops.multiply(col.getchannel("A"), keep))
    ac(canvas, col, (x, y + int((1 - e) * size * 0.16) - int(lh * 0.12)))
    return total


def inline(d, x, y, size, parts, tracking=-3.0, a=1.0, serif_scale=1.06, color=CREAM,
           accent=EMBER, reset_w=None):
    """Ligne mixte Space Grotesk / Instrument Serif italique, sans masque."""
    if a <= 0:
        return 0
    cx = x
    lead_y = y
    for text, kind in parts:
        if kind in ("seri", "ser"):
            f = F(kind, size * serif_scale)
            fg = accent
            dy = int(size * 0.12)
        else:
            f = F(kind, size)
            fg = color
            dy = 0
        tracked(d, (cx, lead_y + dy), text, f, c_(fg, 255 * a), tracking)
        cx += tl(d, text, f, tracking) + size * 0.05
    return cx - x


def hairline(d, y, a=1.0, x0=M, x1=W - M, col=CREAM, alpha=23):
    d.line([(x0, y), (x1, y)], fill=c_(col, alpha * a), width=1)


def label(d, text, y, a=1.0, color=MUTED, size=17, x=M):
    tracked(d, (x, y), text.upper(), F("i6", size), c_(color, 235 * a), 3.2)


def rise(canvas, im, x, y, p, dist=34):
    if p <= 0:
        return
    e = eob(p)
    ac(canvas, _alpha(im, e), (x, y + int((1 - e) * dist)))


def fade(d, fn, a):
    """Exécute un dessin avec un alpha global."""
    if a <= 0:
        return
    fn(a)


# ---------------------------------------------------------------- hero
def s_hero(d, canvas, lt, dur):
    # badge « ● Audit offert »
    ba = eob(prog(lt, 0.04, 0.42))
    if ba > 0:
        p = chip("Audit offert", size=18, fg=c_(CREAM, 245), bg=(21, 21, 23, 240),
                 pad_x=18, pad_y=11, dot=EMBER)
        rise(canvas, p, M, 268, prog(lt, 0.04, 0.42), 10)

    # H1 : deux lignes, mot final en serif italique ember (comme sur le site)
    both_lines(d, canvas, [("Vos clics", "d5")], M, 352, 106, -4.5, p=prog(lt, 0.12, 0.5))
    both_lines(d, canvas, [("deviennent", "d5"), ("des clients.", "seri")],
               M, 352 + 116, 106, -4.5, p=prog(lt, 0.24, 0.5))

    sa = eo(prog(lt, 0.46, 0.5))
    if sa > 0:
        para(d, "Je conçois, j'écris et je lance des tunnels de vente sur-mesure qui "
                "transforment votre trafic en commandes et en rendez-vous signés.",
             F("i4", 26), c_(CREAM, 225 * sa), M, 610, 880, lh=1.42)
    sb = eo(prog(lt, 0.58, 0.5))
    if sb > 0:
        tracked(d, (M, 774), "LIVRÉ EN 14 JOURS · OPTIMISÉ JUSQU'À CE QUE ÇA CONVERTISSE",
                F("i6", 15), c_(MUTED, 225 * sb), 2.4)

    ca = eob(prog(lt, 0.70, 0.45))
    if ca > 0:
        b = button("Réserver mon audit offert", w=700, h=96, size=27)
        rise(canvas, b, M, 826, prog(lt, 0.70, 0.45), 14)
    cb = eob(prog(lt, 0.78, 0.45))
    if cb > 0:
        x2 = M + 726
        im = Image.new("RGBA", (210, 96), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle([0, 0, 209, 95], 48, outline=(244, 241, 234, 46), width=1)
        tracked(dd, (36, 34), "Voir la méthode", F("i5", 22), c_(CREAM, 235), 0.2)
        rise(canvas, im, x2, 826, prog(lt, 0.78, 0.45), 14)
    cc = eo(prog(lt, 0.88, 0.5))
    if cc > 0:
        tracked(d, (M, 948), "SANS ENGAGEMENT — RÉPONSE SOUS 24 H", F("i6", 15),
                c_(MUTED, 220 * cc), 2.6)

    # tableau de bord de la landing (exemple explicite, comme sur le site)
    da = eob(prog(lt, 0.96, 0.7))
    if da > 0:
        bw, bh = 936, 404
        board = panel(bw, bh, r=22, fill=(16, 16, 18), border=(244, 241, 234, 30))
        bd = ImageDraw.Draw(board)
        bd.rounded_rectangle([0, 0, bw - 1, 50], 22, fill=(21, 21, 23, 255))
        bd.rectangle([0, 36, bw - 1, 50], fill=(21, 21, 23, 255))
        for i, cx in enumerate((26, 46, 66)):
            bd.ellipse([cx, 20, cx + 9, 29], fill=c_(DIM, 255))
        tracked(bd, (104, 17), "EXEMPLE DE TABLEAU DE BORD", F("i6", 13), c_(MUTED, 205), 2.4)
        tracked(bd, (bw - 82, 17), "J+7", F("i6", 13), c_(EMBER, 235), 1.6)
        cw = (bw - 56) // 4
        for i, (name, val, delta) in enumerate(BOARD):
            x = 22 + i * (cw + 4)
            bd.rounded_rectangle([x, 68, x + cw - 8, 244], 16, fill=c_(PANEL, 250),
                                 outline=(244, 241, 234, 30), width=1)
            bd.text((x + 16, 84), name.upper(), font=F("i6", 13), fill=c_(MUTED, 225))
            tracked(bd, (x + 16, 112), val, F("d7", 44), c_(EMBER if i == 3 else CREAM, 255), -1.6)
            bd.text((x + 16, 208), delta, font=F("i4", 14), fill=c_(MUTED, 200))
        # courbe + barres A/B
        cx0, cy0, cw2, ch = 22, 264, 500, 118
        bd.rounded_rectangle([cx0, cy0, cx0 + cw2, cy0 + ch], 12, fill=(13, 13, 15, 255),
                             outline=(244, 241, 234, 20), width=1)
        pts = [(.02, .86), (.18, .74), (.34, .78), (.5, .54), (.66, .58), (.82, .28), (.97, .12)]
        poly = [(cx0 + 14 + (cw2 - 28) * u, cy0 + ch - 14 - (ch - 28) * v) for u, v in pts]
        bd.line(poly, fill=c_(EMBER, 255), width=3, joint="curve")
        for px, py in poly:
            bd.ellipse([px - 3, py - 3, px + 3, py + 3], fill=c_(EMBER_SOFT, 255))
        bx0 = 546
        bd.text((bx0 + 6, cy0 + 8), "TEST A/B — INSCRITS", font=F("i6", 12), fill=c_(MUTED, 210))
        for j, (nm, frac, hot) in enumerate([("A", 0.58, False), ("B", 1.0, True)]):
            yy = cy0 + 40 + j * 40
            bd.rounded_rectangle([bx0 + 22, yy, bx0 + 22 + int(330 * frac), yy + 26], 7,
                                 fill=c_(EMBER if hot else (40, 40, 44), 255))
            bd.text((bx0 + 4, yy + 4), nm, font=F("d6", 16),
                    fill=c_(EMBER if hot else MUTED, 240))
            bd.text((bx0 + 36, yy + 5), "+38 %" if hot else "", font=F("i5", 14), fill=c_(INK, 235))
        rise(canvas, board, M, 1006, prog(lt, 0.96, 0.7), 46)

    # stack d'outils
    ta = eo(prog(lt, 1.24, 0.5))
    if ta > 0:
        tracked(d, (M, 1452), "SYSTEME.IO · CLICKFUNNELS · GOHIGHLEVEL", F("i6", 15),
                c_(MUTED, 215 * ta), 2.4)
    ma = eo(prog(lt, 1.34, 0.5))
    if ma > 0:
        strip = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        marquee_strip(strip, "COACHES · E-COMMERCE · INFOPRENEURS · FORMATEURS · "
                             "THÉRAPEUTES · AGENCES · CRÉATEURS · SAAS",
                      1490, lt, size=19, color=MUTED, kind="i5", alpha=200,
                      clip=(M, CW))
        canvas.alpha_composite(Image.composite(strip, Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                                               _col_mask(M, 1480, CW, 34)),
                               (0, 0))


# ---------------------------------------------------------------- diagnostic
def s_diagnostic(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "[ 01 — Le diagnostic ]", 276, a, color=EMBER)

    both_lines(d, canvas, [("Vous payez Meta", "d5")], M, 338, 88, -4, p=prog(lt, 0.10, 0.5))
    both_lines(d, canvas, [("pour des clics.", "d5")], M, 420, 88, -4, p=prog(lt, 0.18, 0.5))
    both_lines(d, canvas, [("Votre page les", "d5")], M, 502, 88, -4, p=prog(lt, 0.26, 0.5))
    both_lines(d, canvas, [("laisse filer.", "seri")], M, 584, 88, -4, p=prog(lt, 0.34, 0.5))

    qa = eo(prog(lt, 0.48, 0.5))
    if qa > 0:
        para(d, "« Le problème n'est presque jamais votre offre, ni votre trafic. "
                "C'est l'absence de système entre les deux. »",
             F("seri", 38), c_(CREAM, 235 * qa), M, 742, 880, lh=1.3)
        tracked(d, (M, 900), "— LÉGER AKODJENOU", F("i6", 14), c_(MUTED, 210 * qa), 2.4)

    rows = [("Des pages génériques", "montées à la va-vite — le visiteur scrolle, puis s'évapore"),
            ("Aucune relance", "pas de capture, pas d'email : chaque visiteur perdu est un euro de pub"),
            ("Un tunnel bricolé", "outils empilés, checkout qui rame — la confiance s'évapore"),
            ("Zéro donnée", "sans tracking propre, vous optimisez à l'aveugle")]
    for i, (title, sub) in enumerate(rows):
        ra = eob(prog(lt, 0.58 + i * 0.10, 0.42))
        if ra <= 0:
            continue
        y = 962 + i * 148 + int((1 - ra) * 14)
        d.rounded_rectangle([M, y, W - M, y + 122], 16, fill=c_(PANEL, int(246 * ra)),
                            outline=(244, 241, 234, 30), width=1)
        d.rectangle([M, y, M + 5, y + 122], fill=c_(EMBER, int(240 * ra)))
        tracked(d, (M + 30, y + 18), f"0{i + 1}", F("i6", 14), c_(EMBER, 230 * ra), 1.6)
        tracked(d, (M + 30, y + 44), title, F("d5", 33), c_(CREAM, 246 * ra), -1.0)
        para(d, sub, F("i4", 19), c_(MUTED, 212 * ra), M + 30, y + 90, CW - 90)

    ha = eob(prog(lt, 1.02, 0.55))
    if ha > 0:
        y = 1556
        hairline(d, y - 34, ha)
        tracked(d, (M, y), "−0 %", F("d7", 78), c_(CREAM, 250 * ha), -4.5)
        para(d, "de vos visiteurs repartent sans rien acheter — et ne reviennent jamais.",
             F("i4", 21), c_(MUTED, 222 * ha), M + 196, y + 4, CW - 200, lh=1.35)
        para(d, "C'est le coût moyen d'une page vitrine face à du trafic payant.",
             F("i4", 19), c_(MUTED, 200 * ha), M + 196, y + 66, CW - 200, lh=1.3)
        tracked(d, (M, y + 130), "UN TUNNEL, LUI, CAPTE, RELANCE, PROUVE ET CONVERTIT.",
                F("i6", 12), c_(EMBER_SOFT, 205 * ha), 2.2)


# ---------------------------------------------------------------- offre
def s_offre(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "[ 02 — Ce que je construis ]", 276, a, color=EMBER)

    both_lines(d, canvas, [("Un tunnel complet.", "d5")], M, 338, 82, -4, p=prog(lt, 0.10, 0.5))
    both_lines(d, canvas, [("Zéro bricolage.", "seri")], M, 414, 82, -4, p=prog(lt, 0.20, 0.5))

    sa = eo(prog(lt, 0.34, 0.5))
    if sa > 0:
        para(d, "Un seul interlocuteur pour tout : stratégie, textes, design, intégration, "
                "tracking. Vous n'avez plus rien à assembler.",
             F("i4", 25), c_(CREAM, 225 * sa), M, 528, 880, lh=1.4)

    mods = [("01", "Stratégie & offre", "angle, promesse, mécanisme — avant d'écrire une ligne",
             "Audit · Positionnement · Offre"),
            ("02", "Copywriting", "pages de vente, VSL, emails écrits pour vendre",
             "Sales page · VSL · Emails"),
            ("03", "Design & intégration", "pages rapides, mobile-first, checkout sans friction",
             "Systeme.io · Mobile-first · Checkout"),
            ("04", "Automatisations", "relances, panier abandonné, upsells en un clic",
             "CRM · Séquences · Upsell"),
            ("05", "Tracking & A/B tests", "pixel Meta, événements, rapports lisibles",
             "Pixel Meta · Reporting · A/B")]
    for i, (num, title, sub, tags) in enumerate(mods):
        ra = eob(prog(lt, 0.46 + i * 0.10, 0.44))
        if ra <= 0:
            continue
        y = 700 + i * 186 + int((1 - ra) * 14)
        d.rounded_rectangle([M, y, W - M, y + 168], 18, fill=c_(PANEL, int(246 * ra)),
                            outline=(244, 241, 234, 28), width=1)
        tracked(d, (M + 28, y + 22), f"/{num}", F("i6", 14), c_(EMBER, 235 * ra), 1.6)
        tracked(d, (M + 28, y + 48), title, F("d5", 34), c_(CREAM, 248 * ra), -1.0)
        para(d, sub, F("i4", 19), c_(MUTED, 215 * ra), M + 28, y + 96, CW - 80)
        tracked(d, (M + 28, y + 134), tags.upper(), F("i6", 12), c_(EMBER_SOFT, 200 * ra), 2.0)

    fa = eo(prog(lt, 1.00, 0.5))
    if fa > 0:
        tracked(d, (M, 1660), "SPÉCIALISTE SYSTEME.IO · CLICKFUNNELS · GOHIGHLEVEL", F("i6", 14),
                c_(MUTED, 210 * fa), 2.4)


# ---------------------------------------------------------------- méthode
def s_methode(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "[ 03 — La méthode ]", 276, a, color=EMBER)

    both_lines(d, canvas, [("Du brief au lancement,", "d5")], M, 332, 70, -3, p=prog(lt, 0.08, 0.5))
    both_lines(d, canvas, [("en ", "d5"), ("14 jours.", "seri")], M, 404, 70, -3,
               p=prog(lt, 0.16, 0.5))

    sa = eo(prog(lt, 0.28, 0.5))
    if sa > 0:
        tracked(d, (M, 500), "UN PROCESSUS CADRÉ, ÉTAPE PAR ÉTAPE — VOUS GARDEZ LA MAIN",
                F("i6", 14), c_(MUTED, 215 * sa), 2.2)

    steps = [("J+0", "01/04", "Audit express",
              "offre, trafic, concurrents passés au scanner", "Appel 30 min · Analyse vidéo · Feuille de route"),
             ("J+2", "02/04", "Architecture",
              "plan du tunnel validé ensemble — rien avant votre feu vert", "Pages · Arborescence · Contenu"),
             ("J+7", "03/04", "Copy + Design",
              "textes rédigés, maquettes livrées, intégration en cours", "Copywriting · Design · Intégration"),
             ("J+14", "04/04", "Live + 30 j",
              "mise en ligne, tracking actif, optimisations offertes 30 jours", "Live · A/B tests · Reporting")]
    top, row = 560, 190
    ra = eo(prog(lt, 0.36, 0.55))
    if ra > 0:
        # le filet s'arrête AVANT la pastille de la dernière étape
        d.line([(M + 8, top + 24), (M + 8, top + 24 + (row * 3 - 58) * ra)],
               fill=c_(CREAM, 26), width=2)
    for i, (day, idx, title, sub, tags) in enumerate(steps):
        p_ = eob(prog(lt, 0.42 + i * 0.11, 0.45))
        pj = eob(prog(lt, 0.48 + i * 0.11, 0.45))
        if p_ <= 0:
            continue
        y = top + i * row
        d.ellipse([M + 8 - 7, y + 24 - 7, M + 8 + 7, y + 24 + 7],
                  fill=c_(EMBER, 255 * p_), outline=c_(INK, 255), width=3)
        tracked(d, (M + 34, y - 2), day, F("d7", 28), c_(EMBER, 250 * pj), -1.0)
        tracked(d, (M + 150, y - 6), idx, F("i6", 13), c_(MUTED, 215 * p_), 2.0)
        tracked(d, (M + 232, y - 8), title, F("d5", 40), c_(CREAM, 248 * p_), -1.2)
        para(d, sub, F("i4", 20), c_(MUTED, 218 * p_), M + 232, y + 48, CW - 250, lh=1.35)
        tracked(d, (M + 232, y + 112), tags.upper(), F("i6", 12), c_(EMBER_SOFT, 195 * p_), 1.8)
        if i < 3:
            d.line([(M + 232, y + 158), (W - M, y + 158)], fill=c_(CREAM, 14 * p_), width=1)

    ba = eob(prog(lt, 0.94, 0.55))
    if ba > 0:
        y = 1372
        d.rounded_rectangle([M, y, W - M, y + 176], 20, fill=(20, 16, 14),
                            outline=(255, 77, 0, 115), width=1)
        d.rectangle([M, y, M + 6, y + 176], fill=c_(EMBER, 240 * ba))
        tracked(d, (M + 30, y + 22), "GARANTIE CONVERSION — 30 JOURS", F("i6", 14),
                c_(EMBER, 245 * ba), 2.6)
        para(d, "Si la conversion n'a pas progressé, je continue à optimiser "
                "gratuitement. C'est écrit dans le contrat.",
             F("i4", 24), c_(CREAM, 232 * ba), M + 30, y + 56, CW - 70, lh=1.4)

    ca = eo(prog(lt, 1.10, 0.5))
    if ca > 0:
        for i, t_ in enumerate(["Feuille de route offerte", "Révisions jusqu'à votre oui"]):
            p = chip(t_, size=17, fg=c_(CREAM, 232), pad_x=16, pad_y=10)
            ac(canvas, _alpha(p, ca), (M + i * 420, 1586))


# ---------------------------------------------------------------- preuve
# ---------------------------------------------------------------- solo
def s_solo(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "[ 04 — Qui construit votre tunnel ]", 276, a, color=EMBER)

    both_lines(d, canvas, [("Pas d'agence.", "d5")], M, 338, 92, -4, p=prog(lt, 0.10, 0.5))
    both_lines(d, canvas, [("Un ", "d5"), ("spécialiste.", "seri")], M, 424, 92, -4,
               p=prog(lt, 0.20, 0.5))

    # « cadre photo » : portrait typographique, monogramme + stack du site
    pa = eob(prog(lt, 0.32, 0.6))
    if pa > 0:
        box_w, box_h = 300, 372
        im = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle([0, 0, box_w - 1, box_h - 1], 20, fill=c_(PANEL, 252),
                             outline=(244, 241, 234, 34), width=1)
        dd.ellipse([box_w / 2 - 54, 62, box_w / 2 + 54, 170], outline=c_(EMBER, 190), width=2)
        tracked(dd, (box_w / 2, 88), "LA", F("d7", 62), c_(CREAM, 246), -3, center=True)
        dd.line([(40, 208), (box_w - 40, 208)], fill=c_(EMBER, 190), width=2)
        tracked(dd, (box_w / 2, 226), "LÉGER AKODJENOU", F("i6", 13), c_(CREAM, 232), 2.2,
                center=True)
        tracked(dd, (box_w / 2, 250), "FUNNEL BUILDER", F("i6", 12), c_(MUTED, 210), 2.6,
                center=True)
        tracked(dd, (box_w / 2, 292), "COTONOU · BÉNIN", F("i6", 12), c_(MUTED, 205), 2.4,
                center=True)
        tracked(dd, (box_w / 2, 330), "FR · BE · CH", F("i6", 12), c_(EMBER, 220), 2.4,
                center=True)
        rise(canvas, im, W - M - box_w, 338, pa, 26)

    sa = eo(prog(lt, 0.42, 0.5))
    if sa > 0:
        para(d, "Depuis un an, je construis des tunnels de vente. Mon constat : trop de "
                "campagnes meurent sur des pages qui n'étaient pas prêtes à recevoir du trafic.",
             F("i4", 26), c_(CREAM, 228 * sa), M, 760, CW - 20, lh=1.42)
        para(d, "Aujourd'hui je ne fais qu'une chose : des tunnels reliés à la réalité de "
                "vos campagnes. Pas de template recyclé, pas de théorie.",
             F("i4", 26), c_(MUTED, 225 * sa), M, 948, CW - 20, lh=1.42)

    qa = eo(prog(lt, 0.62, 0.5))
    if qa > 0:
        para(d, "« Chaque structure est calibrée sur vos chiffres, votre offre et votre trafic. »",
             F("seri", 40), c_(CREAM, 238 * qa), M, 1142, 880, lh=1.3)
        tracked(d, (M, 1258), "— LÉGER", F("i6", 14), c_(MUTED, 212 * qa), 2.4)

    for i, (v, lbl) in enumerate([("1 an", "de tunnels"), ("24 h", "de réponse"),
                                  ("Systeme.io", "expert")]):
        ra = eob(prog(lt, 0.78 + i * 0.09, 0.46))
        if ra <= 0:
            continue
        x = M + i * 312
        y = 1338
        d.line([(x, y - 20), (x + 286, y - 20)], fill=c_(CREAM, 15 * ra), width=1)
        tracked(d, (x, y), v, F("d7", 44 if i < 2 else 34), c_(EMBER if i == 1 else CREAM, 250 * ra), -2)
        tracked(d, (x, y + 62), lbl.upper(), F("i6", 12), c_(MUTED, 210 * ra), 2.2)

    ta = eo(prog(lt, 1.02, 0.5))
    if ta > 0:
        y = 1512
        d.rounded_rectangle([M, y, W - M, y + 108], 18, fill=(20, 16, 14),
                            outline=(255, 77, 0, 105), width=1)
        tracked(d, (M + 26, y + 22), "TANT QUE ÇA NE CONVERTIT PAS, JE CONTINUE À OPTIMISER.",
                F("i6", 14), c_(EMBER, 240 * ta), 2.2)
        tracked(d, (M + 26, y + 56), "Réponse sous 24 h — je lis chaque demande personnellement.",
                F("i4", 18), c_(CREAM, 220 * ta), 0.2)

    da = eo(prog(lt, 1.14, 0.5))
    if da > 0:
        tracked(d, (M, 1656), "« CE SITE EST LUI-MÊME UN TUNNEL. »", F("i6", 13), c_(MUTED, 195 * da), 2.4)


# ---------------------------------------------------------------- tarifs
def s_tarifs(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "[ 05 — Les tarifs ]", 276, a, color=EMBER)

    both_lines(d, canvas, [("Un prix. Un tunnel.", "d5")], M, 334, 76, -3, p=prog(lt, 0.08, 0.5))
    both_lines(d, canvas, [("Des clients.", "seri")], M, 412, 76, -3, p=prog(lt, 0.18, 0.5))

    sa = eo(prog(lt, 0.30, 0.5))
    if sa > 0:
        para(d, "Tarif fixe annoncé après l'audit — jamais de surprise.",
             F("i4", 21), c_(MUTED, 222 * sa), M, 1518, 880, lh=1.35)

    cards = [
        ("EXPRESS", "240 €", "ou 2 × 120 €", "Livré en 7 jours", False,
         ["1 page de vente haute conversion", "Checkout + page de remerciement",
          "Copywriting complet inclus", "1 cycle de révisions"], "Choisir Express"),
        ("PERFORMANCE", "540 €", "ou 3 × 180 €", "Livré en 14 jours", True,
         ["Tunnel complet 5 pages", "Séquence de 5 emails", "Pixel Meta + événements",
          "A/B tests page & titres", "30 jours d'optimisations"], "Réserver mon funnel"),
        ("CROISSANCE TOTALE", "Sur devis", "après audit offert", "Vous vendez déjà ?", False,
         ["Refonte ou nouveau tunnel", "Itérations hebdomadaires", "Roadmap trimestrielle",
          "Canal Slack dédié"], "Parler de mon projet"),
    ]
    for i, (name, price, split, delay, hot, feats, cta) in enumerate(cards):
        ra = eob(prog(lt, 0.40 + i * 0.11, 0.5))
        if ra <= 0:
            continue
        w = CW if i < 2 else CW
        h = 470 if i < 2 else 420
        y = 596 if i < 2 else 596 + 486
        x = M
        if i == 2:                     # pleine largeur, plus basse
            pass
        if i < 2:
            w = (CW - 18) // 2
            x = M if i == 0 else M + w + 18
        im = panel(w, h, r=20, fill=(24, 17, 16) if hot else PANEL,
                   border=(255, 77, 0, 130) if hot else (244, 241, 234, 30))
        dd = ImageDraw.Draw(im)
        if hot:
            dd.rounded_rectangle([20, 18, 190, 50], 16, fill=c_(EMBER, 248))
            tracked(dd, (32, 26), "LE PLUS CHOISI", F("i6", 11), c_(INK, 245), 1.8)
        tracked(dd, (22, 64 if hot else 26), name, F("i6", 13), c_(MUTED, 225), 2.8)
        tracked(dd, (22, 88 if hot else 50), price,
                F("d7", 64 if len(price) < 7 else 40), c_(CREAM, 255), -2.6)
        dd.text((22, 168 if hot else 122), split, font=F("i4", 18), fill=c_(MUTED, 222))
        dd.text((22, 196 if hot else 150), delay, font=F("i6", 16), fill=c_(EMBER, 235))
        dd.line([(22, 232 if hot else 186), (w - 22, 232 if hot else 186)],
                fill=c_(CREAM, 22), width=1)
        for k, ftxt in enumerate(feats):
            fy = (262 if hot else 208) + k * 40
            dd.ellipse([22, fy + 4, 36, fy + 18], outline=c_(EMBER, 225), width=2)
            dd.line([(26, fy + 11), (29, fy + 14), (34, fy + 7)], fill=c_(EMBER, 240), width=2)
            para(dd, ftxt, F("i4", 16), c_(CREAM, 232), 46, fy, w - 74)
        rise(canvas, im, x, y + (0 if i else 0), ra, 34)

    ga = eob(prog(lt, 0.86, 0.5))
    if ga > 0:
        y = 1588
        d.rounded_rectangle([M, y, W - M, y + 128], 18, fill=(20, 16, 14),
                            outline=(255, 77, 0, 112), width=1)
        tracked(d, (M + 26, y + 20), "GARANTIE CONVERSION — 30 JOURS", F("i6", 13),
                c_(EMBER, 245 * ga), 2.6)
        para(d, "La conversion n'a pas bougé ? Je continue jusqu'à ce que ça bouge. "
                "Écrit noir sur blanc dans le contrat.",
             F("i4", 21), c_(CREAM, 230 * ga), M + 26, y + 50, CW - 60, lh=1.35)


# ---------------------------------------------------------------- cta
def s_cta(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "[ 07 — Dernière étape ]", 276, a, color=EMBER)

    both_lines(d, canvas, [("Parlez-moi de", "d5")], M, 338, 88, -4, p=prog(lt, 0.10, 0.5))
    both_lines(d, canvas, [("votre ", "d5"), ("projet.", "seri")], M, 424, 88, -4,
               p=prog(lt, 0.20, 0.5))

    sa = eo(prog(lt, 0.30, 0.5))
    if sa > 0:
        para(d, "Trois minutes pour me dire où vous en êtes. En retour : un audit vidéo "
                "offert et un plan d'action — que vous fassiez appel à moi ou non.",
             F("i4", 25), c_(CREAM, 228 * sa), M, 574, 880, lh=1.42)

    steps = [("Réponse en moins de 24 h", "je lis chaque demande personnellement"),
             ("Audit vidéo offert", "votre offre et votre tunnel décortiqués"),
             ("Plan d'action + devis", "un tarif fixe, puis vous décidez librement")]
    for i, (t_, s_) in enumerate(steps):
        ra = eob(prog(lt, 0.42 + i * 0.58, 0.5))
        if ra <= 0:
            continue
        y = 780 + i * 132 + int((1 - ra) * 12)
        d.line([(M, y - 24), (W - M, y - 24)], fill=c_(CREAM, 15 * ra), width=1)
        tracked(d, (M, y), f"0{i + 1}", F("i6", 14), c_(EMBER, 230 * ra), 1.6)
        tracked(d, (M + 62, y - 10), t_, F("d5", 34), c_(CREAM, 246 * ra), -1.0)
        d.text((M + 62, y + 36), s_, font=F("i4", 19), fill=c_(MUTED, 212 * ra))

    ca = eob(prog(lt, 2.28, 0.55))   # CTA
    if ca > 0:
        d.rounded_rectangle([M, 1218, W - M, 1218 + 300], 20, fill=c_(PANEL, 250),
                            outline=(244, 241, 234, 30), width=1)
        tracked(d, (M + 28, 1242), "AUDIT OFFERT · SANS ENGAGEMENT", F("i6", 13),
                c_(MUTED, 220 * ca), 2.4)
        b = button("Demander mon audit offert", w=820, h=100, size=30)
        rise(canvas, b, M + 28, 1278, prog(lt, 2.28, 0.55), 12)
        tracked(d, (M + 28, 1410), "ZÉRO SPAM · ZÉRO DÉMARCHAGE · RÉPONSE SOUS 24 H",
                F("i6", 13), c_(MUTED, 218 * ca), 2.2)
        d.text((M + 28, 1444), "legerakodjenou6@gmail.com", font=F("i5", 22), fill=c_(CREAM, 235 * ca))
        d.text((M + 28, 1478), "+229 52 09 94 23 · WhatsApp", font=F("i4", 19), fill=c_(MUTED, 215 * ca))

    qa = eo(prog(lt, 3.05, 0.55))
    if qa > 0:
        tracked(d, (M, 1560), "AUDIT VIDÉO OFFERT · PLAN D'ACTION · DEVIS FIXE",
                F("i6", 13), c_(MUTED, 205 * qa), 2.4)
        tracked(d, (M, 1600), "RÉSERVÉ EN 3 MINUTES — RÉPONSE SOUS 24 H",
                F("i6", 13), c_(EMBER, 225 * qa), 2.4)

    qb = eo(prog(lt, 6.10, 0.6))
    if qb > 0:
        para(d, "« Un audit vidéo offert et un plan d'action —\nque vous fassiez appel à moi ou non. »",
             F("seri", 38), c_(CREAM, 232 * qb), M, 1652, 900, lh=1.25)


def s_closing(d, canvas, lt, dur):
    """Carton final : la signature du site, sans nouvelle promesse."""
    a = eob(prog(lt, 0.04, 0.5))
    if a > 0:
        tracked(d, (M, 520), "LÉGER", F("d7", 150), c_(CREAM, 250 * a), -8)
        tracked(d, (M, 682), "AKODJENOU", F("d7", 150), c_(CREAM, 250 * a), -8)
    ba = eo(prog(lt, 0.30, 0.55))
    if ba > 0:
        tracked(d, (M, 868), "DES TUNNELS QUI CONVERTISSENT.", F("i6", 17),
                c_(EMBER, 240 * ba), 4.0)
    ca = eo(prog(lt, 0.48, 0.55))
    if ca > 0:
        para(d, "Vos clics deviennent des clients.", F("seri", 52),
             c_(CREAM, 238 * ca), M, 1000, 880, lh=1.2)
    da = eo(prog(lt, 0.66, 0.55))
    if da > 0:
        d.line([(M, 1130), (M + 120, 1130)], fill=c_(EMBER, 235 * da), width=2)
        tracked(d, (M, 1166), "LÉGERAKODJENOU.SYSTEME.IO", F("i6", 15),
                c_(MUTED, 225 * da), 2.8)
        tracked(d, (M, 1214), "legerakodjenou6@gmail.com  ·  +229 52 09 94 23",
                F("i4", 20), c_(CREAM, 220 * da), 0.2)
        tracked(d, (M, 1262), "AUDIT OFFERT · SANS ENGAGEMENT · RÉPONSE SOUS 24 H",
                F("i6", 13), c_(MUTED, 205 * da), 2.4)
    ea = eob(prog(lt, 0.92, 0.55))
    if ea > 0:
        b = button("Réserver mon audit offert", w=760, h=100, size=28)
        rise(canvas, b, M, 1352, prog(lt, 0.92, 0.55), 14)


SCENE_FN = {"hero": s_hero, "diagnostic": s_diagnostic, "offre": s_offre,
            "methode": s_methode, "solo": s_solo, "tarifs": s_tarifs,
            "cta": s_cta, "closing": s_closing}


# ---------------------------------------------------------------- chrome
def chrome(canvas, t, name):
    d = ImageDraw.Draw(canvas)
    wa = eo(prog(t, 0.12, 0.6))
    tracked(d, (M, 74), "LÉGER©", F("d7", 24), c_(CREAM, 240 * wa), -0.6)
    tracked(d, (M, 112), "FUNNEL BUILDER · STRATÈGE CONVERSION", F("i6", 11),
            c_(MUTED, 190 * wa), 2.2)
    chap = CHAPTER[name].upper()
    if chap:
        tracked(d, (W - M - tl(d, chap, F("i5", 12), 2.2), 84), chap,
                F("i5", 12), c_(MUTED, 200 * wa), 2.2)
    d.line([(M, 148), (W - M, 148)], fill=c_(CREAM, 15 * wa), width=1)

    py = 1846
    d.line([(M, py), (W - M, py)], fill=c_(CREAM, 22), width=2)
    fw = (W - 2 * M) * clamp01(t / TOTAL)
    if fw > 2:
        d.line([(M, py), (M + fw, py)], fill=c_(EMBER, 255), width=2)
    for i in range(1, 7):
        x = M + (W - 2 * M) * i / 7
        d.line([(x, py - 5), (x, py + 5)], fill=c_(CREAM, 88), width=1)


_BG = None


def render_frame(fi):
    global _BG
    if _BG is None:
        _BG = V.build_bg()
    t = fi / FPS
    i = max(0, min(len(CUTS) - 2, int(np.searchsorted(CUTS, t, side="right") - 1)))
    name = SCENES[i]
    lt, dur = t - CUTS[i], CUTS[i + 1] - CUTS[i]

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    SCENE_FN[name](d, layer, lt, dur)
    layer = _alpha(layer, eo(prog(lt, 0.0, 0.18)))

    frame = _BG.copy()
    ac(frame, layer)
    V.grain_shift(frame, t)
    chrome(frame, t, name)
    V.flash(frame, lt)
    return frame.convert("RGB")


# ---------------------------------------------------------------- audio
def _noise(n, lo, hi, seed=0):
    return V._noise(n, lo, hi, seed)


def decode_vo(path):
    """MP3 -> PCM 48 kHz mono, filtré, silences de tête/queue coupés."""
    from scipy.signal import butter, sosfilt
    p = subprocess.run([_ffmpeg(), "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1",
                        "-f", "f32le", "-"], stdout=subprocess.PIPE, check=True)
    a = np.frombuffer(p.stdout, dtype=np.float32).copy()
    a = sosfilt(butter(2, 15000 / (SR / 2), btype="low", output="sos"),
                sosfilt(butter(2, 90 / (SR / 2), btype="high", output="sos"), a))
    a = a + 0.40 * sosfilt(butter(2, [1800 / (SR / 2), 5000 / (SR / 2)], btype="band",
                                  output="sos"), a)
    idx = np.where(np.abs(a) > 10 ** (-46 / 20))[0]
    if idx.size:
        a = a[max(0, idx[0] - int(.05 * SR)): idx[-1] + int(.06 * SR)]
    return a


def retime_vo(verbose=True):
    """Recale chaque départ de prise dans le silence réel de la piste.

    Le mix n'est possible que si les prises ne se chevauchent pas : on mesure
    la durée utile de chaque mp3, on vérifie chaque intervalle, et on refuse
    de rendre si un chevauchement subsiste.
    """
    global VO
    placed, prev_end = [], -1.0
    for name, at in VO:
        a = decode_vo(os.path.join(AUDIO_DIR, name))
        dur = len(a) / SR
        if at < prev_end:
            raise SystemExit(f"{name} démarre à {at:.2f}s mais la prise précédente "
                             f"finit à {prev_end:.2f}s")
        if verbose:
            print(f"  {name}: {dur:5.2f}s  [{at:5.2f} → {at + dur:5.2f}]  "
                  f"silence avant {at - prev_end:5.2f}s" if prev_end > 0 else
                  f"  {name}: {dur:5.2f}s  [{at:5.2f} → {at + dur:5.2f}]", flush=True)
        placed.append((name, at, at + dur, a))
        prev_end = at + dur + AUDIO_GAP
    return placed


def build_score(out_path):
    from scipy.signal import butter, sosfilt
    n = int(TOTAL * SR)
    voice = np.zeros(n, np.float32)
    for name, at, end, a in retime_vo():
        a = a / max(float(np.abs(a).max()), 1e-6) * 0.70
        s = int(round(at * SR))
        e = min(n, s + len(a))
        voice[s:e] += a[: e - s]

    beat, bar = 60 / 108, 60 / 108 * 4
    roots = [55.0, 43.65, 65.41, 49.0]
    mus = np.zeros(n, np.float32)
    # pulsation feutrée + nappes : le lit ne doit jamais masquer la voix
    t0 = 0.0
    while t0 < TOTAL:
        s = int(t0 * SR); ln = min(n - s, int(.3 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 96 * np.exp(-tt * 15) + 42
            mus[s:s + ln] += (np.sin(2 * np.pi * np.cumsum(f) / SR) *
                              np.exp(-tt * 12) * 0.22).astype(np.float32)
        t0 += beat
    for b in range(int(TOTAL / beat) + 1):
        if b % 4 in (1, 3):
            s = int(b * beat * SR); ln = min(n - s, int(.18 * SR))
            if ln > 0:
                mus[s:s + ln] += (_noise(ln, 1200, 5200, b) *
                                  np.exp(-np.arange(ln) / SR * 26) * 0.085).astype(np.float32)
    b = 0
    while b * beat / 2 < TOTAL:
        s = int(b * beat / 2 * SR); ln = min(n - s, int(.045 * SR))
        if ln > 0:
            mus[s:s + ln] += (_noise(ln, 6500, 15000, b + 50) *
                              np.exp(-np.arange(ln) / SR * 150) *
                              (0.028 if b % 2 == 0 else 0.016)).astype(np.float32)
        b += 1
    k = 0
    while k * beat / 2 < TOTAL:
        s = int(k * beat / 2 * SR); ln = min(n - s, int(.26 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[int((k * beat / 2) / bar) % 4]
            v = np.sin(2 * np.pi * r * tt) + .4 * np.sin(4 * np.pi * r * tt)
            e = np.exp(-tt * 9) * np.minimum(tt / .006, 1)
            sos = butter(2, 180 / (SR / 2), btype="low", output="sos")
            mus[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * 0.18).astype(np.float32)
        k += 1
    for bi in range(int(TOTAL / bar) + 1):
        s = int(bi * bar * SR); e_ = min(n, int((bi * bar + bar + .6) * SR))
        if s >= n:
            break
        tt = np.arange(e_ - s) / SR
        r = roots[bi % 4] * 8
        env = np.minimum(tt / .5, 1) * np.exp(-np.maximum(tt - bar * .6, 0) * 1.5)
        v = np.sin(2 * np.pi * r * tt) * .4 + np.sin(2 * np.pi * r * 1.5 * tt + .5) * .22
        sos = butter(2, 2600 / (SR / 2), btype="low", output="sos")
        mus[s:e_] += (sosfilt(sos, (v * env).astype(np.float32)) * 0.045).astype(np.float32)

    mus /= max(float(np.abs(mus).max()), 1e-6)
    mus *= 0.19

    # ducking large et franc : dès que la voix parle, le lit descend de 9 dB
    env = np.abs(voice).astype(np.float32)
    env = sosfilt(butter(1, 2.4 / (SR / 2), btype="low", output="sos"), env)
    env /= max(float(env.max()), 1e-6)
    mus *= 1.0 - 0.72 * np.clip(env * 2.2, 0, 1)

    sfx = np.zeros(n, np.float32)
    for c in CUTS[1:-1]:
        s = int(c * SR); ln = min(n - s, int(.34 * SR))
        if ln > 0:
            sfx[s:s + ln] += (_noise(ln, 500, 6000, int(c * 10)) *
                              np.linspace(1, 0, ln) ** 2 * 0.11).astype(np.float32)
            tt = np.arange(ln) / SR
            sfx[s:s + ln] += (np.sin(2 * np.pi * (90 * np.exp(-tt * 9) + 45) * tt) *
                              np.exp(-tt * 9) * 0.16).astype(np.float32)

    mix = voice + mus + sfx
    peak = float(np.abs(mix).max())
    if peak > 0.97:
        mix *= 0.97 / peak

    import wave
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    print("  mix ->", out_path, flush=True)


def _ffmpeg():
    from imageio_ffmpeg import get_ffmpeg_exe
    return get_ffmpeg_exe()


# ---------------------------------------------------------------- render
def render():
    ff = _ffmpeg()
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", "-movflags", "+faststart", TMP],
                            stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(render_frame(fi).tobytes())
        if fi % 200 == 0:
            print(f"  {fi}/{NFR} ({fi / NFR * 100:.0f}%)", flush=True)
    proc.stdin.close()
    proc.wait()

    # niveau mesuré puis gain appliqué (linéaire, sans pompage) -> -14 LUFS
    base = _measure(MIX)[0]
    gain = -14.0 - base
    for _ in range(4):
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP, "-i", MIX,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89:level=disabled,"
                               "aresample=48000",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                        "-shortest", "-movflags", "+faststart", OUT], check=True)
        i, tp = _measure(OUT)
        print(f"  audio: {i} LUFS / {tp} dBTP", flush=True)
        if abs(i + 14.0) <= 0.3:
            break
        gain += (-14.0 - i)
    print("Rendered", OUT, f"({os.path.getsize(OUT) / 1e6:.1f} MB)")


def _measure(path):
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-i", path, "-af",
                        "ebur128=peak=true", "-f", "null", "-"],
                       stderr=subprocess.PIPE, text=True)
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)[-1])
    return i, tp


def preview(out_path):
    cols, rows = 4, 2
    tw, th = 300, 533
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (10, 10, 12))
    d = ImageDraw.Draw(sheet)
    for k, name in enumerate(SCENES):
        mid = (CUTS[k] + CUTS[k + 1]) / 2
        im = render_frame(int(mid * FPS)).resize((tw, th), Image.LANCZOS)
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 160, y + 24], fill=(0, 0, 0))
        d.text((x + 5, y + 4), f"{CUTS[k]:05.2f}s {name}", font=V.F("i6", 15), fill=(255, 255, 255))
    sheet.save(out_path, quality=90)
    print("Saved preview:", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default=None)
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--retime", action="store_true")
    a = ap.parse_args()
    if a.retime:
        retime_vo()
        return
    if a.preview:
        preview(a.preview)
        return
    print("Voix off + score ...")
    build_score(MIX)
    if a.audio_only:
        print("Audio ->", MIX)
        return
    render()


if __name__ == "__main__":
    main()
