#!/usr/bin/env python3
"""Léger Akodjenou — Funnel Builder · film vertical AVEC VOIX OFF (52,1 s).

Même identité que le portfolio (tokens extraits du site) :
    ink #0a0a0b · coal #101012 · panel #151517 · cream #f4f1ea · muted #97938a
    ember #ff4d00 · line rgba(244,241,234,.09)
    Space Grotesk (display) · Instrument Serif (serif) · Inter (texte)
    dot-grid 34 px · grain animé · filets 1 px · titres contour · easing (.22,1,.36,1)

8 scènes calées sur les 8 clips de voix off déjà générés (voice-02).
Audio : voix off + score original + impacts, ducking sous la voix.

    python3 build_leger_film_v3.py --preview /tmp/preview.jpg
    python3 build_leger_film_v3.py
"""
import argparse
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.signal import butter, sosfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_leger_film_v2 as V  # noqa: E402  (identité visuelle + primitives)

W, H, FPS, SR = V.W, V.H, V.FPS, V.SR
M, CW = V.M, V.CW

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
FILM_DIR = os.path.join(PROJECT, "film")
AUDIO_DIR = os.path.join(PROJECT, "assets", "audio")
OUT = os.path.join(FILM_DIR, "leger-akodjenou-funnel-builder-v3-voix-off-9x16.mp4")
MIX = os.path.join(AUDIO_DIR, "master_mix_v3.wav")
TMP = "/tmp/leger_v3_video.mp4"

CREAM, MUTED, EMBER, EMBER_SOFT = V.CREAM, V.MUTED, V.EMBER, V.EMBER_SOFT
INK, COAL, PANEL, DIM = V.INK, V.COAL, V.PANEL, V.DIM
c_, ac = V.c_, V.ac
F, tl, tracked, para = V.F, V.tl, V.tracked, V.para
chip, button, panel, browser, marquee_strip = V.chip, V.button, V.panel, V.browser, V.marquee_strip
fit_size, _alpha = V.fit_size, V._alpha

SCENES = ["hook", "problem", "reveal", "noirson", "ascension", "horizon", "method", "cta"]
CUTS = [0.00, 5.00, 9.32, 17.43, 24.30, 30.15, 36.27, 42.79, 52.10]
TOTAL = CUTS[-1]

CHAPTER = {
    "hook": "—",
    "problem": "(01) Qui suis-je",
    "reveal": "(01) Qui suis-je",
    "noirson": "(02) Réalisations",
    "ascension": "(02) Réalisations",
    "horizon": "(02) Réalisations",
    "method": "(03) Processus",
    "cta": "(07) Parlons de votre projet",
}

# (fichier, début, tempo) — tempos calculés après nettoyage des silences
VO = [
    ("vo-s1.mp3", CUTS[0] + 0.45, 1.012),
    ("vo-s2.mp3", CUTS[1] + 0.42, 1.000),
    ("vo-s3.mp3", CUTS[2] + 0.42, 1.048),
    ("vo-s4.mp3", CUTS[3] + 0.45, 1.106),
    ("vo-s5.mp3", CUTS[4] + 0.45, 1.163),
    ("vo-s6.mp3", CUTS[5] + 0.45, 1.095),
    ("vo-s7.mp3", CUTS[6] + 0.42, 1.092),
    ("vo-s8.mp3", CUTS[7] + 0.45, 1.044),
]


def hairline(d, y, a=1.0):
    d.line([(M, y), (W - M, y)], fill=c_(CREAM, 23 * a), width=1)


def label(d, text, y, a=1.0, color=MUTED, size=18):
    tracked(d, (M, y), text.upper(), F("i6", size), c_(color, 235 * a), 3.4)


# ---------------------------------------------------------------- scènes
def s_hook(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.05, 0.40))
    ba = V.eob(V.prog(lt, 0.08, 0.45))
    if ba > 0:
        p = chip("Disponible pour nouveaux projets", size=18, fg=c_(CREAM, 240),
                 bg=(21, 21, 23, 235), pad_x=18, pad_y=11, dot=EMBER)
        ac(canvas, _alpha(p, ba), (M, 290 + (1 - ba) * 12))

    lines = [("Du trafic.", CREAM, False), ("Zéro client.", EMBER, False)]
    y = 404
    for i, (text, color, outline) in enumerate(lines):
        ra = V.eob(V.prog(lt, 0.18 + i * 0.14, 0.6))
        if ra <= 0:
            continue
        size = fit_size("d5", text, 150, CW, -6)
        layer = Image.new("L", (W, int(size * 1.7)), 0)
        V.ImageDraw.Draw(layer).text((0, 14), text, font=F("d5", size), fill=255)
        # tracking manuel pour garder l'esprit display du site
        layer = Image.new("L", (W, int(size * 1.7)), 0)
        tracked(ImageDraw.Draw(layer), (0, 14), text, F("d5", size), 255, -6)
        colm = Image.new("RGBA", layer.size, c_(color, 255))
        colm.putalpha(layer)
        keep = Image.new("L", layer.size, 0)
        ImageDraw.Draw(keep).rectangle([0, 0, W, layer.height - int((1 - ra) * size * 1.15)], fill=255)
        colm.putalpha(V.ImageChops.multiply(colm.getchannel("A"), keep))
        ac(canvas, colm, (M, y + (1 - ra) * size * 1.15))
        y += int(size * 1.03)

    la = V.eo(V.prog(lt, 0.62, 0.5))
    if la > 0:
        d.line([(M, 720), (M + 96 * la, 720)], fill=c_(EMBER, 240), width=2)
        tracked(d, (M, 742), "FUNNEL BUILDER — COTONOU, BÉNIN · MONDE ENTIER",
                F("i5", 16), c_(MUTED, 225 * la), 2.6)

    sa = V.eo(V.prog(lt, 0.80, 0.55))
    if sa > 0:
        para(d, "Vos visiteurs arrivent. Puis repartent.",
             F("i4", 30), c_(CREAM, 232 * sa), M, 812, 800, lh=1.5)

    # 3 chiffres clés du portfolio
    stats = [("1 240", "visiteurs / mois"), ("0", "vente"), ("0,8 %", "de conversion")]
    for i, (v, lbl) in enumerate(stats):
        sa2 = V.eob(V.prog(lt, 1.35 + i * 0.11, 0.48))
        if sa2 <= 0:
            continue
        y2 = 1080 + i * 128 + (1 - sa2) * 14
        d.line([(M, y2 - 26), (W - M, y2 - 26)], fill=c_(CREAM, 16 * sa2), width=1)
        tracked(d, (M, y2), v, F("d7", 62), c_(EMBER if i == 2 else CREAM, 250 * sa2), -2.2)
        tracked(d, (M + 330, y2 + 22), lbl.upper(), F("i5", 15), c_(MUTED, 220 * sa2), 2.6)

    if lt > 2.6:
        marquee_strip(canvas, "Scroll · Pour · Convertir", 1560, lt - 2.6,
                      size=21, alpha=150, gap=28, sep="")


def s_problem(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.04, 0.4))
    label(d, "Le vrai problème", 290, a)

    # titre display : plein + contour
    for i, (text, size, outline) in enumerate([("Joli.", 132, False),
                                               ("Mais il ne vend pas.", 92, True)]):
        ra = V.eob(V.prog(lt, 0.12 + i * 0.12, 0.55))
        if ra <= 0:
            continue
        lay = Image.new("L", (W, int(size * 1.7)), 0)
        tracked(ImageDraw.Draw(lay), (0, 12), text, F("d5", size), 255, -5)
        if outline:
            img = V.outline_from_mask(lay, CREAM, 86, 2)
        else:
            img = Image.new("RGBA", lay.size, c_(CREAM, 255))
            img.putalpha(lay)
        ac(canvas, img, (M, 336 + i * 156 + (1 - ra) * 34))

    # citation serif
    qa = V.eo(V.prog(lt, 0.55, 0.55))
    if qa > 0:
        d.text((M, 720), "« Une belle page qui ne vend pas,", font=F("seri", 46),
               fill=c_(CREAM, 245 * qa))
        d.text((M, 780), "c'est de la décoration. »", font=F("seri", 46),
               fill=c_(CREAM, 245 * qa))
        tracked(d, (M, 866), "— LÉGER AKODJENOU", F("i6", 15), c_(EMBER, 230 * qa), 2.6)

    hairline(d, 930, V.eo(V.prog(lt, 0.78, 0.45)))

    # les trois manques
    rows = [("01", "Promesse absente"), ("02", "Zéro preuve"), ("03", "Zéro urgence")]
    for i, (num, title) in enumerate(rows):
        ra = V.eob(V.prog(lt, 0.92 + i * 0.13, 0.5))
        if ra <= 0:
            continue
        y = 985 + i * 108 + (1 - ra) * 14
        tracked(d, (M, y), num, F("i6", 16), c_(EMBER, 225 * ra), 1.6)
        tracked(d, (M + 70, y - 6), title, F("d5", 40), c_(CREAM, 245 * ra), -1.0)
        d.line([(M, y + 62), (W - M, y + 62)], fill=c_(CREAM, 14 * ra), width=1)

    # cible +20 %
    ca = V.eob(V.prog(lt, 1.45, 0.6))
    if ca > 0:
        val = 20 * V.eob(V.prog(lt, 1.45, 0.95))
        tracked(d, (M, 1360), "TAUX DE CONVERSION VISÉ", F("i6", 15), c_(MUTED, 220 * ca), 3.0)
        tracked(d, (M, 1400), f"+{int(round(val))}", F("d7", 120), c_(EMBER, 255 * ca), -5)
        tracked(d, (M + 190, 1452), "%", F("d5", 48), c_(CREAM, 235 * ca), -2)

    if lt > 2.1:
        marquee_strip(canvas, "Zéro hasard", 1650, lt - 2.1, size=21, alpha=145, gap=30, sep="")


def s_reveal(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.04, 0.4))
    label(d, "Le funnel builder", 290, a)

    # nom : plein + contour (le site alterne)
    for i, (text, size, outline) in enumerate([("LÉGER", 138, False),
                                               ("AKODJENOU", 104, True)]):
        ra = V.eob(V.prog(lt, 0.10 + i * 0.13, 0.6))
        if ra <= 0:
            continue
        size = fit_size("d7", text, size, CW, -5)
        lay = Image.new("L", (W, int(size * 1.7)), 0)
        tracked(ImageDraw.Draw(lay), (0, 12), text, F("d7", size), 255, -5)
        if outline:
            img = V.outline_from_mask(lay, CREAM, 88, 2)
        else:
            img = Image.new("RGBA", lay.size, c_(CREAM, 255))
            img.putalpha(lay)
        ac(canvas, img, (M, 336 + i * 172 + (1 - ra) * 30))

    ta = V.eo(V.prog(lt, 0.55, 0.5))
    if ta > 0:
        f = F("i4", 27)
        d.text((M, 700), "Cotonou, Bénin", font=f, fill=c_(MUTED, 235 * ta))
        ax = M + d.textlength("Cotonou, Bénin", font=f) + 14
        d.line([(ax, 716), (ax + 46, 716)], fill=c_(EMBER, 220 * ta), width=2)
        d.polygon([(ax + 52, 716), (ax + 44, 711), (ax + 44, 721)], fill=c_(EMBER, 230 * ta))
        d.text((ax + 64, 700), "monde entier", font=f, fill=c_(MUTED, 235 * ta))

    # +20 % visé
    ka = V.eob(V.prog(lt, 0.80, 0.6))
    if ka > 0:
        val = 20 * V.eob(V.prog(lt, 0.80, 1.0))
        tracked(d, (M, 780), f"+{int(round(val))}", F("d7", 168), c_(CREAM, 255 * ka), -7)
        tracked(d, (M + 300, 872), "%", F("d5", 54), c_(EMBER, 245 * ka), -2)
        tracked(d, (M, 972), "TAUX DE CONVERSION VISÉ", F("i6", 16), c_(MUTED, 225 * ka), 3.0)

    # trois preuves du site
    chips = [("6", "étapes"), ("24 h", "de réponse"), ("14 j", "de support")]
    x = M
    for i, (v, lbl) in enumerate(chips):
        ca = V.eob(V.prog(lt, 1.20 + i * 0.11, 0.45))
        if ca <= 0:
            continue
        p = chip(f"{v} {lbl}", size=18, fg=c_(CREAM, 235), pad_x=18, pad_y=11)
        ac(canvas, _alpha(p, ca), (x, 1052 + (1 - ca) * 12))
        x += p.width + 10

    # outils
    oa = V.eo(V.prog(lt, 1.70, 0.5))
    if oa > 0:
        hairline(d, 1170, oa)
        tracked(d, (M, 1200), "MA BOÎTE À OUTILS", F("i6", 15), c_(MUTED, 220 * oa), 3.0)
    tools = ["Systeme.io", "ClickFunnels", "GoHighLevel", "MailerLite",
             "Brevo", "Stripe", "Zapier", "Meta Ads"]
    x, y = M, 1246
    for i, t_ in enumerate(tools):
        ca = V.eob(V.prog(lt, 1.80 + i * 0.055, 0.4))
        if ca <= 0:
            continue
        p = chip(t_, size=18, fg=c_(CREAM, 230), pad_x=18, pad_y=11)
        if x + p.width > W - M:
            x, y = M, y + 58
        ac(canvas, _alpha(p, ca), (x, y + (1 - ca) * 8))
        x += p.width + 9

    # citation serif du site
    qa = V.eo(V.prog(lt, 3.10, 0.6))
    if qa > 0:
        para(d, "« Le design n'est pas de la décoration.\nC'est un argument de vente. »",
             F("seri", 44), c_(CREAM, 240 * qa), M, 1560, 900, lh=1.28)


def s_noirson(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.04, 0.4))
    label(d, "01 / NOIR·SON — Page de vente", 290, a)

    ma = V.eob(V.prog(lt, 0.12, 0.55))
    if ma > 0:
        mw, mh = 880, 600
        mock = browser(mw, mh, "noirson.funnels.leger.studio", V.noirson_page(mw, mh - 42))
        V.place(canvas, _alpha(mock, ma), (W - mw) / 2, 336 + (1 - ma) * 28)

    ta = V.eo(V.prog(lt, 0.50, 0.5))
    if ta > 0:
        tracked(d, (M, 982), "E-commerce · Audio", F("i4", 21), c_(MUTED, 225 * ta), 0.2)

    ka = V.eob(V.prog(lt, 0.68, 0.58))
    if ka > 0:
        val = 18 * V.eob(V.prog(lt, 0.68, 0.9))
        tracked(d, (M, 1026), f"+{int(round(val))}", F("d7", 176), c_(EMBER, 255 * ka), -7)
        tracked(d, (M + 250, 1128), "%", F("d5", 56), c_(CREAM, 235 * ka), -2)
        tracked(d, (M, 1228), "DE PANIER MOYEN", F("i6", 17), c_(MUTED, 225 * ka), 3.0)

    for i, t_ in enumerate(["Page produit", "Order bump", "Upsell"]):
        ca = V.eob(V.prog(lt, 1.20 + i * 0.10, 0.42))
        if ca > 0:
            p = chip(t_, size=17, fg=c_(CREAM, 232), pad_x=17, pad_y=10)
            ac(canvas, _alpha(p, ca), (M + i * 168, 1290 + (1 - ca) * 10))

    qa = V.eo(V.prog(lt, 1.65, 0.55))
    if qa > 0:
        hairline(d, 1400, qa)
        para(d, "« L'order bump et l'upsell ont augmenté notre panier moyen de 18 %. »",
             F("seri", 40), c_(CREAM, 240 * qa), M, 1430, 920, lh=1.3)
        tracked(d, (M, 1560), "SANDRA M. · E-COMMERÇANTE, NOIR·SON", F("i6", 15),
                c_(MUTED, 215 * qa), 2.4)


def s_ascension(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.03, 0.34))
    label(d, "03 / ASCENSION — Tunnel complet", 286, a)

    ka = V.eob(V.prog(lt, 0.08, 0.5))
    if ka > 0:
        val = 412 * V.eob(V.prog(lt, 0.08, 0.9))
        tracked(d, (M, 340), f"{int(round(val))}", F("d7", 250), c_(CREAM, 255 * ka), -12)
        tracked(d, (M, 620), "INSCRITS EN 14 JOURS", F("i6", 20), c_(EMBER, 245 * ka), 3.2)

    steps = [("Page de capture", 1.00), ("Webinaire", 0.72), ("Séquence e-mail", 0.52),
             ("Page de vente", 0.34), ("Upsell", 0.22)]
    y0 = 726
    for i, (name, frac) in enumerate(steps):
        ra = V.eob(V.prog(lt, 0.38 + i * 0.085, 0.42))
        if ra <= 0:
            continue
        y = y0 + i * 104 + (1 - ra) * 12
        bw = (CW - 40) * frac * ra
        d.rounded_rectangle([M, y, M + max(8, bw), y + 66], 10,
                            fill=c_(PANEL, 255), outline=(244, 241, 234, 28), width=1)
        if i == 0:
            d.rounded_rectangle([M, y, M + max(8, bw), y + 66], 10, fill=c_(EMBER, 235))
        tracked(d, (M + 22, y + 20), name, F("i5", 21),
                c_(INK if i == 0 else CREAM, 240 * ra), 0.2)
        pct = f"{int(frac * 100)} %"
        if i == 0:
            tracked(d, (M + bw - tl(d, pct, F("i6", 16)) - 20, y + 23), pct,
                    F("i6", 16), c_(INK, 240 * ra), 0.4)
        else:
            tracked(d, (M + max(8, bw) + 14, y + 23), pct, F("i6", 16), c_(MUTED, 220 * ra), 0.4)

    fa = V.eo(V.prog(lt, 1.30, 0.55))
    if fa > 0:
        hairline(d, 1290, fa)
        tracked(d, (M, 1322), "7 E-MAILS AUTOMATISÉS", F("d5", 44), c_(CREAM, 245 * fa), -1.4)
        tracked(d, (M, 1382), "1 seul tunnel, du clic à l'achat", F("i4", 22),
                c_(MUTED, 225 * fa), 0.2)

    qa = V.eo(V.prog(lt, 1.75, 0.55))
    if qa > 0:
        para(d, "« 412 inscrits en deux semaines. »", F("seri", 42), c_(CREAM, 240 * qa),
             M, 1490, 900, lh=1.3)
        tracked(d, (M, 1560), "DAVID K. · COACH EN DÉVELOPPEMENT PERSONNEL", F("i6", 14),
                c_(MUTED, 212 * qa), 2.2)


def s_horizon(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.03, 0.34))
    label(d, "04 / HORIZON RETREAT — Réservation", 286, a)

    pairs = [("23", "TAUX DE CONVERSION", 0.08), ("61", "TAUX D'INSCRIPTION", 0.24)]
    for i, (num, lbl, delay) in enumerate(pairs):
        ka = V.eob(V.prog(lt, delay, 0.55))
        if ka <= 0:
            continue
        val = int(round(int(num) * V.eob(V.prog(lt, delay, 0.8))))
        x = M + i * 470
        txt = f"{val:02d}"
        fnum = F("d7", 168)
        tracked(d, (x, 372), txt, fnum, c_(CREAM, 255 * ka), -8)
        tracked(d, (x + tl(d, txt, fnum, -8) + 10, 452), "%", F("d5", 54), c_(EMBER, 245 * ka), -2)
        tracked(d, (x + 4, 578), lbl, F("i6", 15), c_(MUTED, 220 * ka), 2.4)
    d.line([(W / 2, 344), (W / 2, 640)], fill=c_(V.CREAM, 23), width=1)

    ta = V.eo(V.prog(lt, 0.50, 0.45))
    if ta > 0:
        hairline(d, 690, ta)
        tracked(d, (M, 716), "9 % → 23 % APRÈS REFONTE", F("i5", 19), c_(CREAM, 235 * ta), 1.2)
        for i, (lbl, frac, colr) in enumerate([("AVANT", 0.09, DIM), ("APRÈS", 0.23, EMBER)]):
            ra = V.eob(V.prog(lt, 0.62 + i * 0.14, 0.55))
            if ra <= 0:
                continue
            y = 786 + i * 96
            tracked(d, (M, y - 22), lbl, F("i5", 13), c_(MUTED, 210 * ra), 2.4)
            d.rounded_rectangle([M, y + 20, W - M, y + 28], 4, fill=(244, 241, 234, 18))
            d.rounded_rectangle([M, y + 20, M + CW * frac * ra * 2.4, y + 28], 4,
                                fill=c_(colr, 245 * ra))

    ma = V.eob(V.prog(lt, 0.95, 0.55))
    if ma > 0:
        mw, mh = 700, 320
        page = Image.new("RGBA", (mw, mh - 42), (18, 24, 22, 255))
        pd = ImageDraw.Draw(page)
        gg = Image.new("RGBA", page.size, (0, 0, 0, 0))
        ImageDraw.Draw(gg).ellipse([-80, 60, 520, 470], fill=(34, 122, 104, 70))
        page.alpha_composite(gg.filter(ImageFilter.GaussianBlur(46)))
        tracked(pd, (26, 22), "HORIZON RETREAT", F("d6", 14), c_(CREAM, 245), 3.0)
        pd.text((mw - 100, 24), "Réserver", font=F("i4", 11), fill=c_(CREAM, 210))
        pd.text((26, 92), "7 jours pour", font=F("ser", 30), fill=c_(CREAM, 250))
        pd.text((26, 128), "respirer.", font=F("seri", 30), fill=c_(CREAM, 250))
        pd.rounded_rectangle([26, mh - 96, 190, mh - 56], 20, fill=c_(EMBER, 250))
        tracked(pd, (44, mh - 84), "RÉSERVER", F("i6", 10), c_(INK, 255), 0.8)
        mock = browser(mw, mh, "horizonretreat.funnels.leger.studio", page)
        V.place(canvas, _alpha(mock, ma), (W - mw) / 2, 1030 + (1 - ma) * 24, blur=24, alpha=145)

    qa = V.eo(V.prog(lt, 1.30, 0.5))
    if qa > 0:
        tracked(d, (M, 1420), "« 9 % à 23 % de conversion après refonte. »", F("seri", 38),
                c_(CREAM, 238 * qa), 0)
        tracked(d, (M, 1482), "MARIAM S. · FONDATRICE, HORIZON RETREAT", F("i6", 14),
                c_(MUTED, 212 * qa), 2.2)

    # captures liées au tunnel
    for i, t_ in enumerate(["Storytelling", "Acompte en ligne", "Témoignages vidéo"]):
        ca = V.eob(V.prog(lt, 1.70 + i * 0.11, 0.42))
        if ca > 0:
            p = chip(t_, size=17, fg=c_(CREAM, 230), pad_x=17, pad_y=10)
            ac(canvas, _alpha(p, ca), (M + i * 208, 1560 + (1 - ca) * 10))


def s_method(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.04, 0.38))
    label(d, "Processus — 6 étapes", 286, a)

    ha = V.eob(V.prog(lt, 0.10, 0.5))
    if ha > 0:
        tracked(d, (M, 324), "Une méthode,", F("d5", 74), c_(CREAM, 250 * ha), -3.2)
        tracked(d, (M, 402), "zéro hasard.", F("d5", 74), c_(CREAM, 250 * ha), -3.2)

    steps = [("01", "Immersion & audit"), ("02", "Architecture du tunnel"),
             ("03", "Copywriting"), ("04", "Design & intégration"),
             ("05", "Automatisation"), ("06", "Tests & optimisation")]
    y0 = 528
    for i, (num, title) in enumerate(steps):
        ra = V.eob(V.prog(lt, 0.26 + i * 0.095, 0.45))
        if ra <= 0:
            continue
        y = y0 + i * 140 + (1 - ra) * 14
        d.line([(M, y - 16), (W - M, y - 16)], fill=c_(CREAM, 15 * ra), width=1)
        tracked(d, (M, y + 16), num, F("i6", 16), c_(EMBER, 228 * ra), 1.8)
        tracked(d, (M + 78, y + 2), title, F("d5", 42), c_(CREAM, 248 * ra), -1.2)
    d.line([(M, y0 + 6 * 140 - 16), (W - M, y0 + 6 * 140 - 16)], fill=c_(CREAM, 15), width=1)

    fa = V.eob(V.prog(lt, 1.05, 0.5))
    if fa > 0:
        y = 1430 + (1 - fa) * 16
        hairline(d, y, fa)
        tracked(d, (M, y + 26), "DÉLAI DE LIVRAISON", F("i6", 14), c_(MUTED, 220 * fa), 2.8)
        tracked(d, (M, y + 56), "2 à 3 semaines", F("d5", 50), c_(CREAM, 248 * fa), -1.6)
        tracked(d, (M + 400, y + 70), "pour un tunnel complet", F("i4", 20),
                c_(MUTED, 222 * fa), 0.2)

    qa = V.eo(V.prog(lt, 1.55, 0.55))
    if qa > 0:
        tracked(d, (M, 1620), "Appel découverte offert · devis sous 48 h",
                F("i5", 21), c_(EMBER, 230 * qa), 0.4)


def s_cta(d, canvas, lt, dur):
    a = V.eo(V.prog(lt, 0.04, 0.38))
    label(d, "Prêt à convertir ?", 284, a)

    ha = V.eob(V.prog(lt, 0.10, 0.55))
    if ha > 0:
        d.text((M, 330), "Votre tunnel mérite", font=F("ser", 68), fill=c_(CREAM, 250 * ha))
        d.text((M, 406), "mieux qu'un template.", font=F("ser", 68), fill=c_(CREAM, 250 * ha))
    ua = V.eio(V.prog(lt, 0.52, 0.55))
    if ua > 0:
        d.rectangle([M, 490, M + 392 * ua, 494], fill=c_(EMBER, 240))

    oa = V.eob(V.prog(lt, 0.58, 0.55))
    if oa > 0:
        card = panel(CW, 190, 20)
        cd = ImageDraw.Draw(card)
        cd.ellipse([30, 32, 44, 46], fill=c_(EMBER, 255))
        tracked(cd, (58, 28), "DISPONIBLE POUR NOUVEAUX PROJETS", F("i6", 15), c_(EMBER, 240), 2.4)
        tracked(cd, (30, 64), "Appel découverte · 30 min", F("d5", 42), c_(CREAM, 255), -1.3)
        tracked(cd, (30, 124), "Offert · sans engagement · réponse sous 24 h",
                F("i4", 20), c_(MUTED, 230), 0.2)
        ac(canvas, _alpha(card, oa), (M, 560 + (1 - oa) * 18))

    ba = V.eob(V.prog(lt, 0.95, 0.55))
    if ba > 0:
        btn = button("Démarrer un projet", w=CW, size=33)
        glow = btn.filter(ImageFilter.GaussianBlur(26))
        ac(canvas, _alpha(glow, 0.42 * ba), (M, 786))
        ac(canvas, _alpha(btn, ba), (M, 786 + (1 - ba) * 14))

    rows = [("legerakodjenou6@gmail.com", "EMAIL"),
            ("+229 01 52 09 94 23", "WHATSAPP"),
            ("Cotonou, Bénin · monde entier", "BASÉ À")]
    for i, (val, lbl) in enumerate(rows):
        ra = V.eob(V.prog(lt, 1.20 + i * 0.10, 0.45))
        if ra <= 0:
            continue
        y = 946 + i * 74 + (1 - ra) * 10
        tracked(d, (M, y), lbl, F("i6", 13), c_(DIM, 232 * ra), 2.6)
        tracked(d, (M + 128, y - 4), val, F("i5", 23), c_(CREAM, 238 * ra), 0.1)
        d.line([(M, y + 44), (W - M, y + 44)], fill=c_(CREAM, 13 * ra), width=1)

    # garanties du site
    sa = V.eo(V.prog(lt, 1.60, 0.5))
    if sa > 0:
        items = ["Appel de 30 min offert", "Devis sous 48 h", "14 jours de support"]
        x = M
        for i, s_ in enumerate(items):
            ia = V.eob(V.prog(lt, 1.60 + i * 0.10, 0.42))
            tracked(d, (x, 1210), "—", F("i6", 14), c_(EMBER, 200 * ia), 0)
            tracked(d, (x + 22, 1210), s_, F("i4", 18), c_(MUTED, 228 * ia), 0.1)
            x += tl(d, s_, F("i4", 18)) + 58

    # signature
    sig = V.eo(V.prog(lt, 1.95, 0.6))
    if sig > 0:
        hairline(d, 1300, sig)
        tracked(d, (M, 1330), "LÉGER©", F("d7", 78), c_(CREAM, 250 * sig), -3)
        tracked(d, (M, 1428), "FUNNEL BUILDER — SYSTEME.IO", F("i5", 16), c_(MUTED, 220 * sig), 2.8)
        tracked(d, (M, 1462), "legerakodjenou6.systeme.io", F("i4", 18), c_(EMBER, 232 * sig), 0.2)

    # promesse finale + CTA secondaire
    fa = V.eo(V.prog(lt, 2.55, 0.7))
    if fa > 0:
        tracked(d, (W / 2, 1540), "Des tunnels qui convertissent.", F("d5", 36),
                c_(CREAM, 238 * fa), -1.0, center=W / 2)
    ga = V.eo(V.prog(lt, 3.0, 0.7))
    if ga > 0:
        tracked(d, (W / 2, 1610), "Scroll · Pour · Convertir", F("i5", 18),
                c_(EMBER, 210 * ga), 4.0, center=W / 2)


SCENE_FN = {"hook": s_hook, "problem": s_problem, "reveal": s_reveal, "noirson": s_noirson,
            "ascension": s_ascension, "horizon": s_horizon, "method": s_method, "cta": s_cta}


def chrome(canvas, t, name):
    d = ImageDraw.Draw(canvas)
    wa = V.eo(V.prog(t, 0.15, 0.6))
    if name != "cta":
        tracked(d, (M, 76), "LÉGER©", F("d7", 24), c_(CREAM, 238 * wa), -0.6)
    chap = CHAPTER[name].upper()
    tracked(d, (W - M - tl(d, chap, F("i5", 14), 2.2), 84), chap,
            F("i5", 14), c_(MUTED, 202 * wa), 2.2)
    d.line([(M, 124), (W - M, 124)], fill=c_(CREAM, 15 * wa), width=1)

    py = 1846
    d.line([(M, py), (W - M, py)], fill=c_(CREAM, 24), width=2)
    fw = (W - 2 * M) * V.clamp01(t / TOTAL)
    if fw > 2:
        d.line([(M, py), (M + fw, py)], fill=c_(EMBER, 255), width=2)


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
    layer = _alpha(layer, V.eo(V.prog(lt, 0.0, 0.16)) * (1 - 0.40 * V.eo(V.prog(lt, dur - 0.10, 0.10))))

    frame = _BG.copy()
    ac(frame, layer)
    V.grain_shift(frame, t)
    chrome(frame, t, name)
    V.flash(frame, lt)
    return frame.convert("RGB")


# ------------------------------------------------------------------ audio
def _noise(n, lo, hi, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n).astype(np.float32)
    sos = butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], btype="band", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def _read(path):
    with wave.open(path, "rb") as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        raw = w.readframes(n)
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    if sr != SR:
        idx = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(idx, np.arange(len(a)), a)
    return a


def build_score(out_path):
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
    n = int(TOTAL * SR)
    mixm = np.zeros(n, np.float32)
    beat, bar = 60.0 / 108, 60.0 / 108 * 4
    roots = [55.0, 43.65, 65.41, 49.0]

    t0 = 0.0
    while t0 < TOTAL:
        s = int(t0 * SR)
        ln = min(n - s, int(.3 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            f = 96 * np.exp(-tt * 15) + 42
            mixm[s:s + ln] += (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 12) * 0.30).astype(np.float32)
        t0 += beat

    for b in range(int(TOTAL / beat) + 1):
        if b % 4 in (1, 3):
            s = int(b * beat * SR)
            ln = min(n - s, int(.18 * SR))
            if ln > 0:
                mixm[s:s + ln] += (_noise(ln, 1200, 5200, seed=b) * np.exp(-np.arange(ln) / SR * 26) * 0.11).astype(np.float32)

    b = 0
    while b * beat / 2 < TOTAL:
        s = int(b * beat / 2 * SR)
        ln = min(n - s, int(.045 * SR))
        if ln > 0:
            mixm[s:s + ln] += (_noise(ln, 6500, 15000, seed=b + 50) * np.exp(-np.arange(ln) / SR * 150) * (0.034 if b % 2 == 0 else 0.020)).astype(np.float32)
        b += 1

    k = 0
    while k * beat / 2 < TOTAL:
        s = int(k * beat / 2 * SR)
        ln = min(n - s, int(.26 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            r = roots[int((k * beat / 2) / bar) % 4]
            v = np.sin(2 * np.pi * r * tt) + .4 * np.sin(4 * np.pi * r * tt)
            e = np.exp(-tt * 9) * np.minimum(tt / .006, 1)
            sos = butter(2, 180 / (SR / 2), btype="low", output="sos")
            mixm[s:s + ln] += (sosfilt(sos, (v * e).astype(np.float32)) * 0.22).astype(np.float32)
        k += 1

    for bi in range(int(TOTAL / bar) + 1):
        s = int(bi * bar * SR)
        e_ = min(n, int((bi * bar + bar + .6) * SR))
        if s >= n:
            break
        tt = np.arange(e_ - s) / SR
        r = roots[bi % 4] * 4
        env = np.minimum(tt / .5, 1) * np.exp(-np.maximum(tt - bar * .5, 0) * 1.8)
        v = np.sin(2 * np.pi * r * tt) * .5 + np.sin(2 * np.pi * r * 1.5 * tt + .7) * .32
        sos = butter(2, 2600 / (SR / 2), btype="low", output="sos")
        mixm[s:e_] += (sosfilt(sos, (v * env).astype(np.float32)) * 0.075).astype(np.float32)

    step = beat / 4
    k, t0 = 0, CUTS[1]
    while t0 < TOTAL - .2:
        s = int(t0 * SR)
        ln = min(n - s, int(.22 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            note = roots[int(t0 / bar) % 4] * 8 * (2 ** ([0, 7, 12, 3][k % 4] / 12))
            mixm[s:s + ln] += (np.sin(2 * np.pi * note * tt) * np.exp(-tt * 22) * 0.040).astype(np.float32)
        k += 1
        t0 += step

    # impacts sur chaque coupe
    for i, cut in enumerate(CUTS[:-1]):
        s = int(cut * SR)
        ln = min(n - s, int(.9 * SR))
        if ln <= 0:
            continue
        tt = np.arange(ln) / SR
        boom = np.sin(2 * np.pi * (58 * tt - 14 * tt ** 2)) * np.exp(-tt * 6)
        air = _noise(ln, 250, 4000, seed=100 + i) * np.exp(-tt * 9)
        amp = 0.42 if i in (0, 2, 7) else 0.24
        mixm[s:s + ln] += ((boom * .8 + air * .5) * amp).astype(np.float32)

    for cut in (CUTS[2], CUTS[7]):
        d_ = 1.5
        s = max(0, int((cut - d_) * SR))
        ln = min(n - s, int(d_ * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            mixm[s:s + ln] += (_noise(ln, 500, 9000, seed=int(cut)) * (tt / d_) ** 2.2 * 0.15).astype(np.float32)

    # ticks UI
    for tp in (CUTS[1] + 1.5, CUTS[1] + 1.85, CUTS[2] + 0.8, CUTS[3] + 0.7, CUTS[4] + 0.1):
        s = int(tp * SR)
        ln = min(n - s, int(.05 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            mixm[s:s + ln] += (np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 120) * 0.07)

    # voix off (silences nettoyés + tempo), puis ducking
    vo = np.zeros(n, np.float32)
    for k_i, (fname, start, tempo) in enumerate(VO, start=1):
        src = os.path.join(AUDIO_DIR, fname)
        dst = f"/tmp/_v3vo{k_i}.wav"
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", src, "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                        f"areverse,atempo={tempo:.4f}",
                        "-ar", str(SR), "-ac", "1", dst], check=True)
        a = _read(dst)
        s = int(start * SR)
        e = min(n, s + len(a))
        if s < n:
            vo[s:e] += a[:e - s] * 1.05

    env = np.abs(vo)
    win = int(.12 * SR)
    env = np.convolve(env, np.ones(win, np.float32) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 3.4, 0, 1)
    mixm *= (1.0 - 0.62 * env)

    dly = int(.012 * SR)
    left = mixm + vo
    right = np.concatenate([np.zeros(dly, np.float32), (mixm + vo)[:-dly]])
    st = np.stack([left * .97 + right * .09, right * .97 + left * .09], axis=1)
    st = st / (np.abs(st).max() + 1e-9) * 0.90
    raw = "/tmp/_v3_raw.wav"
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    subprocess.run([ff, "-y", "-loglevel", "error", "-i", raw, "-af",
                    "highpass=f=40,equalizer=f=2400:width_type=o:width=1.4:g=2.2,volume=5.5dB,"
                    "alimiter=limit=0.94:level=disabled", "-ar", str(SR), out_path], check=True)
    return out_path


def preview(out_path):
    global _BG
    _BG = V.build_bg()
    sheet = Image.new("RGB", (4 * (432 + 8) + 8, 2 * (768 + 8) + 8), (18, 18, 20))
    sd = ImageDraw.Draw(sheet)
    for i in range(8):
        t = (CUTS[i] + CUTS[i + 1]) / 2
        im = render_frame(int(t * FPS)).resize((432, 768), Image.LANCZOS)
        x, y = 8 + (i % 4) * 440, 8 + (i // 4) * 776
        sheet.paste(im, (x, y))
        sd.rectangle([x, y, x + 150, y + 26], fill=(0, 0, 0))
        sd.text((x + 6, y + 4), f"t={t:05.2f}s", font=F("i5", 17), fill=(255, 255, 255))
    sheet.save(out_path, quality=90)
    print("Saved preview:", out_path)


def render():
    from imageio_ffmpeg import get_ffmpeg_exe
    ff = get_ffmpeg_exe()
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
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", TMP, "-i", MIX,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", OUT], check=True)
    print("Rendered", OUT, f"({os.path.getsize(OUT) / 1e6:.1f} MB)")


def main():
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
