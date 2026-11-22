#!/usr/bin/env python3
"""Léger Akodjenou — « Vos clics deviennent des clients » · v4 (58,94 s).

Refonte de la v3 pour la **nouvelle landing** :
<https://legerakodjenou.systeme.io/8c1af526>

Même identité que le site (ink #0a0a0b, cream #f4f1ea, ember #ff4d00,
Space Grotesk / Instrument Serif / Inter, dot-grid 34 px, grain, filets 1 px),
mais un film neuf — pas un remontage :

  - 8 plans construits sur les 8 prises de voix off (`v4-s*.mp3`) ;
  - **preuves visuelles neuves** : le tableau de bord de la landing
    (12 422 visiteurs · 4 196 inscrits · 311 clients · 6,8 % · ROAS 4,2×),
    le test A/B « variante B, +38 % d'inscrits », les 5 modules du tunnel,
    la chronologie J+0 → J+14, les 3 paliers (240 € / 540 € / sur devis),
    la garantie 30 jours ;
  - apparitions par masque + échelle, jamais de fondu seul ;
  - coupe franche sur chaque temps fort, flash de 2 images, grain animé.

Aucune donnée n'est inventée : tous les chiffres affichés sont ceux de la page.

    python3 build_leger_film_v4.py --preview /tmp/preview-v4.jpg
    python3 build_leger_film_v4.py
"""
import argparse
import os
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
OUT = os.path.join(FILM_DIR, "leger-akodjenou-vos-clics-deviennent-des-clients-9x16.mp4")
MIX = os.path.join(AUDIO_DIR, "master_mix_v4.wav")
TMP = "/tmp/leger_v4_video.mp4"

CREAM, MUTED, EMBER, EMBER_SOFT = V.CREAM, V.MUTED, V.EMBER, V.EMBER_SOFT
INK, COAL, PANEL, DIM = V.INK, V.COAL, V.PANEL, V.DIM
c_, ac = V.c_, V.ac
F, tl, tracked, para = V.F, V.tl, V.tracked, V.para
chip, button, panel, browser = V.chip, V.button, V.panel, V.browser
fit_size, _alpha = V.fit_size, V._alpha
eo, eob, prog, clamp01 = V.eo, V.eob, V.prog, V.clamp01

# ---------------------------------------------------------------- timeline
SCENES = ["hook", "problem", "build", "tunnel", "days", "solo", "price", "cta"]
CUTS = [0.00, 4.55, 12.10, 21.95, 30.40, 37.90, 44.90, 53.10, 58.94]
TOTAL = CUTS[-1]

CHAPTER = {
    "hook": "—",
    "problem": "(01) Le diagnostic",
    "build": "(02) Ce que je construis",
    "tunnel": "(02) Ce que je construis",
    "days": "(03) La méthode",
    "solo": "(04) Qui construit",
    "price": "(05) Les tarifs",
    "cta": "(07) Dernière étape",
}

# (fichier, début) — chaque prise est posée dans son plan, respiration incluse
AUDIO_GAP = 0.35          # respiration minimale entre deux prises
VO = [
    ("v4-s1.mp3", 0.45),
    ("v4-s2.mp3", 4.95),
    ("v4-s3.mp3", 12.50),
    ("v4-s4.mp3", 22.35),
    ("v4-s5.mp3", 30.80),
    ("v4-s6.mp3", 38.30),
    ("v4-s7.mp3", 45.30),
    ("v4-s8.mp3", 53.50),
]

# ---------------------------------------------------------------- primitives


def hairline(d, y, a=1.0, x0=M, x1=W - M):
    d.line([(x0, y), (x1, y)], fill=c_(CREAM, 23 * a), width=1)


def label(d, text, y, a=1.0, color=MUTED, size=18):
    tracked(d, (M, y), text.upper(), F("i6", size), c_(color, 235 * a), 3.4)


def rise(canvas, im, x, y, p, dist=34):
    """Masque + montée : l'objet arrive, il n'apparaît pas."""
    if p <= 0:
        return
    e = eob(p)
    dy = int((1 - e) * dist)
    ac(canvas, _alpha(im, e), (x, y + dy))


def reveal_text(canvas, text, kind, size, color, x, y, p, tracking=-2.0, mask=True):
    """Ligne de texte révélée par masque vertical (comme le site)."""
    if p <= 0:
        return
    e = eob(p)
    f = F(kind, size)
    lay = Image.new("L", (int(tl(ImageDraw.Draw(Image.new("RGBA", (4, 4))), text, f, tracking)) + 40,
                           int(size * 1.6)), 0)
    tracked(ImageDraw.Draw(lay), (0, int(size * 0.12)), text, f, 255, tracking)
    colm = Image.new("RGBA", lay.size, c_(color, 255))
    colm.putalpha(lay)
    if mask:
        keep = Image.new("L", lay.size, 0)
        ImageDraw.Draw(keep).rectangle([0, 0, lay.width, int(lay.height * min(1, e * 1.06))], fill=255)
        colm.putalpha(ImageChops.multiply(colm.getchannel("A"), keep))
    ac(canvas, colm, (x, y + int((1 - e) * size * 0.18)))


def kpi_card(w, h, value, name, sub, accent=False):
    """Carte chiffre du tableau de bord, style site."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 20,
                        fill=c_(PANEL, 252), outline=(244, 241, 234, 34), width=1)
    d.text((24, 20), name.upper(), font=F("i6", 15),
           fill=c_(MUTED, 225))
    tracked(d, (24, 52), value, F("d7", 58 if len(value) < 7 else 46),
            c_(EMBER if accent else CREAM, 255), -1.8)
    if sub:
        d.text((24, h - 40), sub, font=F("i4", 16), fill=c_(MUTED, 200))
    return im


def check_row(d, y, text, a, size=26):
    if a <= 0:
        return
    d.ellipse([M, y + 4, M + 22, y + 26], outline=c_(EMBER, 235 * a), width=2)
    d.line([(M + 6, y + 15), (M + 11, y + 20), (M + 18, y + 9)], fill=c_(EMBER, 245 * a), width=3)
    d.text((M + 40, y), text, font=F("i4", size), fill=c_(CREAM, 232 * a))


# ---------------------------------------------------------------- scènes
def s_hook(d, canvas, lt, dur):
    """Le titre de la landing, avec le tableau de bord juste derrière."""
    ba = eob(prog(lt, 0.06, 0.45))
    if ba > 0:
        p = chip("Audit offert", size=18, fg=c_(CREAM, 240), bg=(21, 21, 23, 238),
                 pad_x=18, pad_y=11, dot=EMBER)
        rise(canvas, p, M, 286, prog(lt, 0.06, 0.45), 12)

    # tableau de bord flottant (les chiffres de la page)
    da = eob(prog(lt, 0.30, 0.8))
    if da > 0:
        bw, bh = 940, 470
        board = panel(bw, bh, r=24, fill=(16, 16, 18), border=(244, 241, 234, 30))
        bd = ImageDraw.Draw(board)
        bd.rounded_rectangle([0, 0, bw - 1, 54], 24, fill=(21, 21, 23, 255))
        bd.rectangle([0, 40, bw - 1, 54], fill=(21, 21, 23, 255))
        for i, cx in enumerate((28, 50, 72)):
            bd.ellipse([cx, 22, cx + 10, 32], fill=c_(DIM, 255))
        tracked(bd, (110, 19), "EXEMPLE DE TABLEAU DE BORD", F("i6", 13), c_(MUTED, 210), 2.4)
        tracked(bd, (bw - 92, 19), "J+7", F("i6", 13), c_(EMBER, 230), 1.6)
        for i, (v, n, s_) in enumerate([("12 422", "Visiteurs", "+224 % vs ancien site"),
                                       ("4 196", "Inscrits", "Test A/B — variante B"),
                                       ("311", "Clients", "Gagnante +38 % d'inscrits")]):
            card = kpi_card(280, 150, v, n, s_)
            board.alpha_composite(card, (24 + i * 300, 78))
        kpi2 = kpi_card(280, 130, "6,8 %", "Taux de conversion", "", accent=True)
        board.alpha_composite(kpi2, (24, 250))
        kpi3 = kpi_card(280, 130, "4,2×", "ROAS Meta", "")
        board.alpha_composite(kpi3, (324, 250))
        # mini courbe
        cx0, cy0, cw, ch = 640, 258, 272, 108
        bd.rectangle([cx0, cy0, cx0 + cw, cy0 + ch], fill=(13, 13, 15, 255),
                     outline=(244, 241, 234, 22), width=1)
        pts = [(0, .82), (.18, .70), (.34, .74), (.5, .5), (.66, .54), (.82, .26), (1, .12)]
        poly = [(cx0 + 10 + (cw - 20) * u, cy0 + ch - 12 - (ch - 24) * v) for u, v in pts]
        bd.line(poly, fill=c_(EMBER, 255), width=3, joint="curve")
        for px, py in poly:
            bd.ellipse([px - 3, py - 3, px + 3, py + 3], fill=c_(EMBER_SOFT, 255))
        rise(canvas, board, M - 6, 1330, da, 60)

    # titre
    reveal_text(canvas, "Vos clics", "d5", 132, CREAM, M, 400, prog(lt, 0.16, 0.55), -5)
    reveal_text(canvas, "deviennent", "d5", 132, CREAM, M, 528, prog(lt, 0.28, 0.55), -5)
    reveal_text(canvas, "des clients.", "d5", 132, EMBER, M, 656, prog(lt, 0.40, 0.55), -5)

    sa = eo(prog(lt, 0.72, 0.5))
    if sa > 0:
        para(d, "Tunnels de vente sur-mesure. Livrés en 14 jours.\nOptimisés jusqu'à ce que ça convertisse.",
             F("i4", 30), c_(CREAM, 225 * sa), M, 856, 900, lh=1.45)

    ca = eob(prog(lt, 1.10, 0.5))
    if ca > 0:
        b = button("Réserver mon audit offert", w=830, h=108, size=31)
        rise(canvas, b, M, 1030, prog(lt, 1.10, 0.5), 18)
    ta = eo(prog(lt, 1.28, 0.5))
    if ta > 0:
        tracked(d, (M, 1160), "SANS ENGAGEMENT — RÉPONSE SOUS 24 H", F("i6", 15),
                c_(MUTED, 225 * ta), 2.6)


def s_problem(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Le diagnostic", 286, a)

    reveal_text(canvas, "Vous payez Meta", "d5", 104, CREAM, M, 340, prog(lt, 0.10, 0.5), -4)
    reveal_text(canvas, "pour des clics.", "d5", 104, CREAM, M, 442, prog(lt, 0.22, 0.5), -4)
    reveal_text(canvas, "Votre page les", "d5", 104, EMBER, M, 544, prog(lt, 0.34, 0.5), -4)
    reveal_text(canvas, "laisse filer.", "d5", 104, EMBER, M, 646, prog(lt, 0.46, 0.5), -4)

    qa = eo(prog(lt, 0.72, 0.5))
    if qa > 0:
        para(d, "« Le problème n'est presque jamais votre offre, ni votre trafic.\nC'est l'absence de système entre les deux. »",
             F("seri", 42), c_(CREAM, 238 * qa), M, 800, 900, lh=1.32)
        tracked(d, (M, 916), "— LÉGER AKODJENOU", F("i6", 15), c_(MUTED, 215 * qa), 2.6)

    hairline(d, 972, eo(prog(lt, 0.92, 0.45)))

    rows = [("01", "Des pages génériques", "elles ne racontent rien"),
            ("02", "Aucune relance", "chaque visiteur perdu est un euro de pub"),
            ("03", "Un tunnel bricolé", "la confiance s'évapore avant le paiement"),
            ("04", "Zéro donnée", "vous optimisez à l'aveugle")]
    for i, (num, title, sub) in enumerate(rows):
        ra = eob(prog(lt, 1.02 + i * 0.13, 0.45))
        if ra <= 0:
            continue
        y = 1012 + i * 118 + (1 - ra) * 14
        tracked(d, (M, y + 6), num, F("i6", 16), c_(EMBER, 225 * ra), 1.6)
        tracked(d, (M + 66, y), title, F("d5", 38), c_(CREAM, 246 * ra), -1.0)
        d.text((M + 66, y + 48), sub, font=F("i4", 20), fill=c_(MUTED, 215 * ra))
        d.line([(M, y + 96), (W - M, y + 96)], fill=c_(CREAM, 13 * ra), width=1)

    ha = eob(prog(lt, 1.62, 0.55))
    if ha > 0:
        tracked(d, (M, 1540), "LE COÛT", F("i6", 15), c_(MUTED, 220 * ha), 3.0)
        reveal_text(canvas, "−0 %", "d7", 120, CREAM, M, 1570, prog(lt, 1.62, 0.6), -5)
        d.text((M + 380, 1622), "de vos visiteurs repartent\nsans rien acheter.",
               font=F("i4", 26), fill=c_(MUTED, 225 * ha))


def s_build(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Ce que je construis", 286, a)

    reveal_text(canvas, "Un tunnel complet.", "d5", 92, CREAM, M, 338, prog(lt, 0.10, 0.5), -4)
    reveal_text(canvas, "Zéro bricolage.", "d5", 92, EMBER, M, 436, prog(lt, 0.22, 0.5), -4)

    sa = eo(prog(lt, 0.40, 0.5))
    if sa > 0:
        para(d, "Un seul interlocuteur : stratégie, textes, design,\nintégration, tracking. Vous n'avez plus rien à assembler.",
             F("i4", 28), c_(CREAM, 225 * sa), M, 570, 900, lh=1.42)

    mods = [("01", "Stratégie & offre", "positionnement · promesse"),
            ("02", "Copywriting", "sales page · VSL · emails"),
            ("03", "Design & intégration", "mobile-first · checkout"),
            ("04", "Automatisations", "relances · upsells · CRM"),
            ("05", "Tracking & A/B", "pixel Meta · reporting")]
    for i, (num, title, sub) in enumerate(mods):
        ra = eob(prog(lt, 0.62 + i * 0.10, 0.45))
        if ra <= 0:
            continue
        y = 760 + i * 150 + (1 - ra) * 16
        d.rounded_rectangle([M, y, W - M, y + 124], 16,
                            fill=c_(PANEL, 244), outline=(244, 241, 234, 28), width=1)
        d.rectangle([M, y, M + 6, y + 124], fill=c_(EMBER, int(235 * ra)))
        tracked(d, (M + 34, y + 24), num, F("i6", 16), c_(EMBER, 230 * ra), 1.6)
        tracked(d, (M + 96, y + 18), title, F("d5", 34), c_(CREAM, 246 * ra), -1.0)
        d.text((M + 96, y + 68), sub, font=F("i4", 20), fill=c_(MUTED, 210 * ra))

    fa = eo(prog(lt, 1.42, 0.5))
    if fa > 0:
        tracked(d, (M, 1560), "SYSTEME.IO · CLICKFUNNELS · GOHIGHLEVEL", F("i6", 15),
                c_(MUTED, 215 * fa), 2.6)


def s_tunnel(d, canvas, lt, dur):
    """Le tunnel en 5 étages + les chiffres du tableau de bord."""
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "À quoi ça ressemble", 286, a)

    for i, (text, col) in enumerate([("Capture", CREAM), ("Vente", CREAM),
                                     ("Upsell", CREAM), ("Checkout", CREAM),
                                     ("Merci", EMBER)]):
        ra = eob(prog(lt, 0.10 + i * 0.09, 0.45))
        if ra <= 0:
            continue
        w = 300 + i * 120
        x = (W - w) // 2
        y = 360 + i * 104 + (1 - ra) * 14
        d.rounded_rectangle([x, y, x + w, y + 82], 14,
                            fill=c_(EMBER if i == 4 else PANEL, int(248 * ra)),
                            outline=(244, 241, 234, 30), width=1)
        tracked(d, (x + 26, y + 24), text, F("d5", 27),
                c_(INK if i == 4 else CREAM, 245 * ra), -0.4)
        if i < 4:
            cx = W // 2
            d.line([(cx, y + 82), (cx, y + 100)], fill=c_(EMBER, 150 * ra), width=2)

    # trois chiffres clés
    for i, (v, lbl) in enumerate([("6,8 %", "taux de conversion"), ("4,2×", "ROAS Meta"),
                                  ("+38 %", "test A/B gagnant")]):
        ra = eob(prog(lt, 0.70 + i * 0.11, 0.5))
        if ra <= 0:
            continue
        y = 990 + i * 104 + (1 - ra) * 12
        d.line([(M, y - 18), (W - M, y - 18)], fill=c_(CREAM, 15 * ra), width=1)
        tracked(d, (M, y), v, F("d7", 64), c_(EMBER if i < 2 else CREAM, 250 * ra), -2.4)
        d.text((M + 300, y + 18), lbl, font=F("i5", 22), fill=c_(MUTED, 220 * ra))

    ta = eo(prog(lt, 1.20, 0.5))
    if ta > 0:
        tracked(d, (M, 1360), "TEST A/B — VARIANTE B", F("i6", 15), c_(MUTED, 220 * ta), 2.8)
        # deux barres : A puis B
        for i, (name, frac, hot) in enumerate([("A", 0.62, False), ("B", 1.0, True)]):
            ra2 = eob(prog(lt, 1.28 + i * 0.14, 0.5))
            if ra2 <= 0:
                continue
            y = 1400 + i * 92
            bw = int(700 * frac * ra2)
            d.rounded_rectangle([M + 60, y, M + 60 + max(10, bw), y + 62], 10,
                                fill=c_(PANEL, 255), outline=(244, 241, 234, 26), width=1)
            if hot:
                d.rounded_rectangle([M + 60, y, M + 60 + max(10, bw), y + 62], 10, fill=c_(EMBER, 240))
            tracked(d, (M, y + 16), name, F("d6", 26),
                    c_(EMBER if hot else MUTED, 245 * ra2), 0)
            tracked(d, (M + 80, y + 17), "inscrits", F("i5", 20),
                    c_(INK if hot else CREAM, 235 * ra2), 0.2)

    qa = eo(prog(lt, 1.66, 0.5))
    if qa > 0:
        para(d, "« Chaque visiteur perdu est un euro de pub\nqui ne reviendra jamais. »",
             F("seri", 38), c_(CREAM, 232 * qa), M, 1610, 900, lh=1.3)


def s_days(d, canvas, lt, dur):
    """La méthode J+0 → J+14 : liste verticale, lisible en 9:16."""
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "La méthode", 286, a)

    reveal_text(canvas, "Du brief au lancement,", "d5", 70, CREAM, M, 338, prog(lt, 0.10, 0.5), -3)
    reveal_text(canvas, "en 14 jours.", "d5", 70, EMBER, M, 418, prog(lt, 0.22, 0.5), -3)

    steps = [("J+0", "Audit express", "appel 30 min · feuille de route offerte"),
             ("J+2", "Architecture", "pages, pricing, emails — validés ensemble"),
             ("J+7", "Copy + design", "textes, maquettes, intégration"),
             ("J+14", "Live + 30 j", "tracking actif · A/B tests · reporting")]

    top, row = 560, 168
    # rail vertical
    ra = eo(prog(lt, 0.30, 0.5))
    if ra > 0:
        d.line([(M + 26, top + 26), (M + 26, top + 26 + (row * 3 - 20) * ra)],
               fill=c_(CREAM, 26), width=2)

    for i, (day, title, sub) in enumerate(steps):
        # décalage des jours de 0,42 s pour que le titre n'arrive pas sur le jour
        p_ = eob(prog(lt, 0.38 + i * 0.14, 0.5))
        pj = eob(prog(lt, 0.52 + i * 0.14, 0.5))
        if p_ <= 0:
            continue
        y = top + i * row + (1 - p_) * 16
        # pastille du jour
        d.ellipse([M + 26 - 8, y + 26 - 8, M + 26 + 8, y + 26 + 8], fill=c_(EMBER, 255 * p_))
        tracked(d, (M + 44, y - 2), day, F("d7", 30), c_(EMBER, 250 * pj), -1.2)
        tracked(d, (M + 150, y + 2), title, F("d5", 40), c_(CREAM, 246 * p_), -1.2)
        para(d, sub, F("i4", 21), c_(MUTED, 218 * p_), M + 150, y + 58, CW - 170, lh=1.35)
        d.line([(M + 150, y + row - 34), (W - M, y + row - 34)],
               fill=c_(CREAM, 14 * p_), width=1)

    ba = eob(prog(lt, 0.98, 0.55))
    if ba > 0:
        y = 1236
        d.rounded_rectangle([M, y, W - M, y + 196], 20, fill=(20, 16, 14),
                            outline=(255, 77, 0, 110), width=1)
        d.rectangle([M, y, M + 6, y + 196], fill=c_(EMBER, 240 * ba))
        tracked(d, (M + 30, y + 24), "GARANTIE CONVERSION — 30 JOURS", F("i6", 15),
                c_(EMBER, 245 * ba), 2.8)
        para(d, "Si la conversion n'a pas progressé, je continue\nà optimiser gratuitement. C'est dans le contrat.",
             F("i4", 26), c_(CREAM, 232 * ba), M + 30, y + 62, CW - 60, lh=1.42)

    ca = eo(prog(lt, 1.18, 0.5))
    if ca > 0:
        for i, t_ in enumerate(["Appel 30 min", "Feuille de route", "Devis fixe"]):
            p = chip(t_, size=18, fg=c_(CREAM, 235), pad_x=18, pad_y=11)
            ac(canvas, _alpha(p, ca), (M + i * 280, 1482))

    qa = eo(prog(lt, 1.42, 0.5))
    if qa > 0:
        para(d, "« Vous gardez la main à chaque étape —\nsans y passer vos soirées. »",
             F("seri", 36), c_(CREAM, 232 * qa), M, 1560, 900, lh=1.28)


def s_solo(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Qui construit votre tunnel", 286, a)

    # portrait typographique : pas d'image inventée
    pa = eob(prog(lt, 0.10, 0.6))
    if pa > 0:
        box = 300
        x = W - M - box
        im = Image.new("RGBA", (box, box), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle([0, 0, box - 1, box - 1], 24, fill=c_(PANEL, 252),
                             outline=(244, 241, 234, 32), width=1)
        # monogramme
        tracked(dd, (box / 2, box / 2 - 82), "LA", F("d7", 104), c_(CREAM, 245), -6, center=True)
        dd.line([(40, box - 92), (box - 40, box - 92)], fill=c_(EMBER, 200), width=2)
        tracked(dd, (40, box - 76), "COTONOU, BÉNIN", F("i6", 14), c_(MUTED, 215), 2.6)
        rise(canvas, im, x, 340, pa, 30)

    reveal_text(canvas, "Pas une agence.", "d5", 96, CREAM, M, 348, prog(lt, 0.14, 0.5), -4)
    reveal_text(canvas, "Un spécialiste.", "d5", 96, EMBER, M, 448, prog(lt, 0.26, 0.5), -4)

    sa = eo(prog(lt, 0.34, 0.5))
    if sa > 0:
        tracked(d, (M, 590), "LÉGER AKODJENOU", F("i6", 17), c_(MUTED, 225 * sa), 3.2)
        para(d, "Depuis un an, je construis des tunnels de vente.\nMon constat : trop de campagnes meurent sur des pages\nqui n'étaient pas prêtes à recevoir du trafic.",
             F("i4", 29), c_(CREAM, 228 * sa), M, 640, CW - 30, lh=1.42)

    qa = eo(prog(lt, 0.62, 0.5))
    if qa > 0:
        para(d, "« Pas de template recyclé, pas de théorie :\nchaque structure est calibrée sur vos chiffres. »",
             F("seri", 40), c_(CREAM, 236 * qa), M, 830, 900, lh=1.3)
        tracked(d, (M, 946), "— LÉGER", F("i6", 15), c_(MUTED, 215 * qa), 2.6)

    for i, (v, lbl) in enumerate([("1 an", "de tunnels"), ("24 h", "de réponse"),
                                  ("FR · BE · CH", "zone d'intervention")]):
        ra = eob(prog(lt, 0.80 + i * 0.10, 0.5))
        if ra <= 0:
            continue
        y = 1030 + i * 104 + (1 - ra) * 12
        d.line([(M, y - 18), (W - M, y - 18)], fill=c_(CREAM, 15 * ra), width=1)
        tracked(d, (M, y), v, F("d7", 52), c_(EMBER if i == 1 else CREAM, 250 * ra), -2.0)
        d.text((M + 380, y + 14), lbl, font=F("i5", 22), fill=c_(MUTED, 220 * ra))

    ta = eo(prog(lt, 1.18, 0.5))
    if ta > 0:
        tracked(d, (M, 1400), "SYSTEME.IO EXPERT", F("i6", 15), c_(MUTED, 215 * ta), 3.0)
        p = chip("Réponse sous 24 h", size=18, fg=c_(CREAM, 235), pad_x=18, pad_y=11, dot=EMBER)
        ac(canvas, _alpha(p, ta), (M, 1440))

    da = eo(prog(lt, 1.34, 0.5))
    if da > 0:
        tracked(d, (M, 1560), "« CE PORTFOLIO EST LUI-MÊME UN TUNNEL. »", F("i6", 15),
                c_(MUTED, 205 * da), 2.4)


def s_price(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Les tarifs", 286, a)

    reveal_text(canvas, "Un prix. Un tunnel.", "d5", 82, CREAM, M, 338, prog(lt, 0.10, 0.5), -3)
    reveal_text(canvas, "Des clients.", "d5", 82, EMBER, M, 424, prog(lt, 0.22, 0.5), -3)

    sa = eo(prog(lt, 0.30, 0.5))
    if sa > 0:
        tracked(d, (M, 556), "TARIF FIXE APRÈS AUDIT — JAMAIS DE SURPRISE", F("i6", 15),
                c_(MUTED, 222 * sa), 2.6)

    cards = [("Express", "240 €", "ou 2 × 120 €", "Livré en 7 jours", False,
              ["1 page de vente", "Checkout + page merci", "Copywriting complet", "1 cycle de révisions"]),
             ("Performance", "540 €", "ou 3 × 180 €", "Livré en 14 jours", True,
              ["Tunnel complet 5 pages", "5 emails de relance", "Pixel Meta + événements", "A/B tests", "30 j d'optimisations"])]
    for i, (name, price, split, delay, hot, feats) in enumerate(cards):
        ra = eob(prog(lt, 0.44 + i * 0.16, 0.55))
        if ra <= 0:
            continue
        x = M if i == 0 else M + 480
        y = 620
        w = 460
        h = 660 if i == 1 else 620
        im = panel(w, h, r=22, fill=PANEL if not hot else (24, 17, 16),
                   border=(255, 77, 0, 120) if hot else (244, 241, 234, 30))
        dd = ImageDraw.Draw(im)
        if hot:
            dd.rounded_rectangle([24, 22, 190, 58], 18, fill=c_(EMBER, 245))
            tracked(dd, (38, 30), "LE PLUS CHOISI", F("i6", 13), c_(INK, 245), 2.0)
        tracked(dd, (24, 76 if hot else 34), name.upper(), F("i6", 15), c_(MUTED, 225), 3.0)
        tracked(dd, (24, 108 if hot else 66), price, F("d7", 78), c_(CREAM, 255), -3.2)
        dd.text((24, 208 if hot else 166), split, font=F("i4", 20), fill=c_(MUTED, 220))
        dd.text((24, 244 if hot else 202), delay, font=F("i6", 19), fill=c_(EMBER, 235))
        dd.line([(24, 290 if hot else 248), (w - 24, 290 if hot else 248)],
                fill=c_(CREAM, 22), width=1)
        for k, ftxt in enumerate(feats):
            check_row(dd, (322 if hot else 280) + k * 52, ftxt, 1.0, size=21)
        # décalage de la colonne de droite (layout éditorial, pas grille figée)
        rise(canvas, im, x, y + (0 if i == 0 else 10), ra, 40)

    ga = eob(prog(lt, 1.10, 0.5))
    if ga > 0:
        y = 1330
        d.rounded_rectangle([M, y, W - M, y + 150], 18, fill=(20, 16, 14),
                            outline=(255, 77, 0, 110), width=1)
        tracked(d, (M + 28, y + 22), "GARANTIE CONVERSION — 30 JOURS", F("i6", 15),
                c_(EMBER, 245 * ga), 2.8)
        para(d, "La conversion n'a pas bougé ? Je continue\njusqu'à ce que ça bouge. Écrit dans le contrat.",
             F("i4", 25), c_(CREAM, 230 * ga), M + 28, y + 58, CW - 56, lh=1.4)

    ta = eo(prog(lt, 1.32, 0.5))
    if ta > 0:
        tracked(d, (M, 1520), "CROISSANCE TOTALE — SUR DEVIS APRÈS AUDIT", F("i6", 15),
                c_(MUTED, 220 * ta), 2.6)


def s_cta(d, canvas, lt, dur):
    a = eo(prog(lt, 0.04, 0.4))
    label(d, "Dernière étape", 286, a)

    reveal_text(canvas, "Parlez-moi de", "d5", 96, CREAM, M, 348, prog(lt, 0.10, 0.5), -4)
    reveal_text(canvas, "votre projet.", "d5", 96, EMBER, M, 444, prog(lt, 0.22, 0.5), -4)

    sa = eo(prog(lt, 0.34, 0.5))
    if sa > 0:
        para(d, "Trois minutes pour me dire où vous en êtes.\nEn retour : un audit vidéo offert et un plan d'action —\nque vous travailliez avec moi ou non.",
             F("i4", 29), c_(CREAM, 228 * sa), M, 596, CW - 20, lh=1.42)

    for i, (t_, s_) in enumerate([("Réponse < 24 h", "je lis chaque demande personnellement"),
                                  ("Audit vidéo offert", "votre offre et votre tunnel décortiqués"),
                                  ("Plan + devis", "un tarif fixe, puis vous décidez")]):
        ra = eob(prog(lt, 0.58 + i * 0.12, 0.5))
        if ra <= 0:
            continue
        y = 800 + i * 132 + (1 - ra) * 14
        d.line([(M, y - 22), (W - M, y - 22)], fill=c_(CREAM, 15 * ra), width=1)
        tracked(d, (M, y), f"0{i + 1}", F("i6", 16), c_(EMBER, 230 * ra), 1.6)
        tracked(d, (M + 66, y - 8), t_, F("d5", 36), c_(CREAM, 246 * ra), -1.0)
        d.text((M + 66, y + 40), s_, font=F("i4", 20), fill=c_(MUTED, 212 * ra))

    ca = eob(prog(lt, 1.02, 0.55))
    if ca > 0:
        b = button("Demander mon audit offert", w=860, h=112, size=32)
        rise(canvas, b, M, 1240, prog(lt, 1.02, 0.55), 18)
    ta = eo(prog(lt, 1.22, 0.5))
    if ta > 0:
        tracked(d, (M, 1382), "GRATUIT · SANS ENGAGEMENT · RÉPONSE SOUS 24 H", F("i6", 15),
                c_(MUTED, 222 * ta), 2.6)
        d.text((M, 1430), "legerakodjenou6@gmail.com", font=F("i5", 24), fill=c_(CREAM, 225 * ta))
        d.text((M, 1470), "+229 52 09 94 23  ·  WhatsApp", font=F("i4", 21), fill=c_(MUTED, 215 * ta))

    qa = eo(prog(lt, 1.44, 0.5))
    if qa > 0:
        tracked(d, (M, 1570), "LÉGER AKODJENOU", F("d7", 46), c_(CREAM, 248 * qa), -1.6)
        tracked(d, (M, 1630), "DES TUNNELS QUI CONVERTISSENT.", F("i6", 15),
                c_(MUTED, 218 * qa), 3.0)


SCENE_FN = {"hook": s_hook, "problem": s_problem, "build": s_build, "tunnel": s_tunnel,
            "days": s_days, "solo": s_solo, "price": s_price, "cta": s_cta}


# ---------------------------------------------------------------- chrome
def chrome(canvas, t, name):
    d = ImageDraw.Draw(canvas)
    wa = eo(prog(t, 0.15, 0.6))
    if name != "cta":
        tracked(d, (M, 76), "LÉGER©", F("d7", 24), c_(CREAM, 238 * wa), -0.6)
    chap = CHAPTER[name].upper()
    tracked(d, (W - M - tl(d, chap, F("i5", 14), 2.2), 84), chap,
            F("i5", 14), c_(MUTED, 202 * wa), 2.2)
    d.line([(M, 124), (W - M, 124)], fill=c_(CREAM, 15 * wa), width=1)

    # barre de progression en trois segments (le site a 7 sections)
    py = 1846
    d.line([(M, py), (W - M, py)], fill=c_(CREAM, 24), width=2)
    fw = (W - 2 * M) * clamp01(t / TOTAL)
    if fw > 2:
        d.line([(M, py), (M + fw, py)], fill=c_(EMBER, 255), width=2)
    for i in range(1, 7):
        x = M + (W - 2 * M) * i / 7
        d.line([(x, py - 5), (x, py + 5)], fill=c_(CREAM, 90), width=1)


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
    layer = _alpha(layer, eo(prog(lt, 0.0, 0.16)) * (1 - 0.40 * eo(prog(lt, dur - 0.10, 0.10))))

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
    p = subprocess.run([V.__dict__.get("FF", "/tmp/bin/ffmpeg"), "-v", "error", "-i", path,
                        "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"],
                       stdout=subprocess.PIPE, check=True)
    a = np.frombuffer(p.stdout, dtype=np.float32).copy()
    hp = butter(2, 90 / (SR / 2), btype="high", output="sos")
    lp = butter(2, 15000 / (SR / 2), btype="low", output="sos")
    band = butter(2, [1800 / (SR / 2), 5000 / (SR / 2)], btype="band", output="sos")
    a = sosfilt(lp, sosfilt(hp, a))
    a = a + 0.40 * sosfilt(band, a)                     # présence
    idx = np.where(np.abs(a) > 10 ** (-46 / 20))[0]
    if idx.size:
        a = a[max(0, idx[0] - int(.05 * SR)): idx[-1] + int(.06 * SR)]
    return a


def build_score(out_path):
    from scipy.signal import butter, sosfilt
    n = int(TOTAL * SR)
    voice = np.zeros(n, np.float32)

    # --- garde-fou : deux prises ne doivent JAMAIS se superposer ---------
    placed, end_prev = [], 0.0
    for name, at in VO:
        a = decode_vo(os.path.join(AUDIO_DIR, name))
        if at < end_prev + AUDIO_GAP:
            raise SystemExit(
                f"voix {name} @ {at:.2f}s chevauche la prise précédente "
                f"(fin {end_prev:.2f}s) — recalage de la timeline nécessaire")
        a = a / max(float(np.abs(a).max()), 1e-6) * 0.70
        s = int(round(at * SR))
        e = min(n, s + len(a))
        voice[s:e] += a[: e - s]
        end_prev = (s + len(a)) / SR
        placed.append((name, at, end_prev))
        print(f"  voix {name} @ {at:5.2f}s  {len(a) / SR:5.2f} s", flush=True)
    for (n1, a1, e1), (n2, a2, _) in zip(placed, placed[1:]):  # noqa: E501
        print(f"  silence {n1} -> {n2} : {a2 - e1:5.2f} s", flush=True)

    # --- musique : 108 BPM, accordée aux coupes (2 mesures par plan)
    beat, bar = 60 / 108, 60 / 108 * 4
    roots = [55.0, 43.65, 65.41, 49.0]
    mus = np.zeros(n, np.float32)
    t0 = 0.0
    while t0 < TOTAL:
        s = int(t0 * SR); ln = min(n - s, int(.3 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 96 * np.exp(-tt * 15) + 42
            mus[s:s + ln] += (np.sin(2 * np.pi * np.cumsum(f) / SR) *
                              np.exp(-tt * 12) * 0.30).astype(np.float32)
        t0 += beat
    for b in range(int(TOTAL / beat) + 1):
        if b % 4 in (1, 3):
            s = int(b * beat * SR); ln = min(n - s, int(.18 * SR))
            if ln > 0:
                mus[s:s + ln] += (_noise(ln, 1200, 5200, b) *
                                  np.exp(-np.arange(ln) / SR * 26) * 0.11).astype(np.float32)
    b = 0
    while b * beat / 2 < TOTAL:
        s = int(b * beat / 2 * SR); ln = min(n - s, int(.045 * SR))
        if ln > 0:
            mus[s:s + ln] += (_noise(ln, 6500, 15000, b + 50) *
                              np.exp(-np.arange(ln) / SR * 150) *
                              (0.034 if b % 2 == 0 else 0.020)).astype(np.float32)
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
            mus[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * 0.22).astype(np.float32)
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
        mus[s:e_] += (sosfilt(sos, (v * env).astype(np.float32)) * 0.055).astype(np.float32)

    mus /= max(float(np.abs(mus).max()), 1e-6)
    mus *= 0.20                       # lit musical discret, jamais au-dessus de la voix

    # ducking sous la voix
    env = np.abs(voice).astype(np.float32)
    env = sosfilt(butter(1, 3.0 / (SR / 2), btype="low", output="sos"), env)
    env /= max(float(env.max()), 1e-6)
    mus *= 1.0 - 0.62 * np.clip(env * 2.5, 0, 1)

    # SFX : impact sur chaque coupe + riser avant l'offre et le CTA
    sfx = np.zeros(n, np.float32)
    for c in CUTS[1:-1]:
        s = int(c * SR); ln = min(n - s, int(.4 * SR))
        if ln > 0:
            sfx[s:s + ln] += (_noise(ln, 500, 6000, int(c * 10)) *
                              np.linspace(1, 0, ln) ** 2 * 0.16).astype(np.float32)
            tt = np.arange(ln) / SR
            sfx[s:s + ln] += (np.sin(2 * np.pi * (90 * np.exp(-tt * 9) + 45) * tt) *
                              np.exp(-tt * 9) * 0.22).astype(np.float32)
    for t_, g in ((CUTS[6] - 0.9, .14), (TOTAL - 1.2, .16)):
        s = int(t_ * SR); ln = min(n - s, int(1.2 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            sfx[s:s + ln] += (np.sin(2 * np.pi * 1046.5 * tt) * np.exp(-tt * 3.4) * g).astype(np.float32)

    mix = voice + mus + sfx
    peak = float(np.abs(mix).max())
    if peak > 0.97:
        mix *= 0.97 / peak

    pcm = (np.clip(mix, -1, 1) * 32767).astype("<i2")
    with __import__("wave").open(out_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("  mix ->", out_path, flush=True)


def _ffmpeg():
    from imageio_ffmpeg import get_ffmpeg_exe
    return get_ffmpeg_exe()


def render():
    import json
    ff = _ffmpeg()
    nf = int(round(TOTAL * FPS))
    proc = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
                             "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                             "-pix_fmt", "yuv420p", "-movflags", "+faststart", TMP],
                            stdin=subprocess.PIPE)
    for fi in range(nf):
        proc.stdin.write(render_frame(fi).tobytes())
        if fi % 200 == 0:
            print(f"  {fi}/{nf} ({fi / nf * 100:.0f}%)", flush=True)
    proc.stdin.close()
    proc.wait()

    # loudness 2 passes -> -14 LUFS, crête sous -1,5 dBTP
    r = subprocess.run([ff, "-hide_banner", "-i", MIX, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                       stderr=subprocess.PIPE, text=True, check=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:"
          f"measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP, "-i", MIX,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-af", f"{ln},alimiter=limit=0.84:level=disabled,aresample=48000",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "1",
                    "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("Rendered", OUT, f"({os.path.getsize(OUT) / 1e6:.1f} MB)")


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
        d.rectangle([x, y, x + 150, y + 24], fill=(0, 0, 0))
        d.text((x + 5, y + 4), f"{CUTS[k]:05.2f}s {name}", font=F("i6", 15), fill=(255, 255, 255))
    sheet.save(out_path, quality=90)
    print("Saved preview:", out_path)


def main():
    import json  # noqa: F401  (utilisé dans render)
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default=None)
    ap.add_argument("--audio-only", action="store_true")
    a = ap.parse_args()
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
