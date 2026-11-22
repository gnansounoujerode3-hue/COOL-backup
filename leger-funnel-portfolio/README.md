# Léger Akodjenou — Funnel Builder · Vidéo Marketing 9:16

Vidéo marketing verticale construite **à partir du portfolio** :
<https://legerakodjenou6.systeme.io/47e3d8ba>

| | |
|---|---|
| Fichier | `film/leger-akodjenou-funnel-builder-9x16.mp4` |
| Format | `1080 × 1920` (`9:16`) · `30 fps` · H.264 + AAC |
| Durée | `52,10 s` (1563 images) |
| Poids | ~11 Mo |
| Audio | Voix-off française + score original + SFX UI (pic `-0,7 dBFS`, RMS `-17,3 dBFS`) |

## Pourquoi ce format

Le portfolio est diffusé depuis un lien Instagram (`utm_source=ig`, `link_in_bio`).
Le `9:16` plein écran est donc le format natif : Reels, TikTok, Shorts, Stories —
aucun recadrage, aucun texte coupé.

## Les 8 scènes

| # | Temps | Scène | Contenu issu du portfolio |
|---|---|---|---|
| 1 | `0,00 – 5,00 s` | Le problème | `1 240` visiteurs, `0` vente, `0,8 %` de conversion |
| 2 | `5,00 – 9,32 s` | Le vrai problème | « Une belle page qui ne vend pas, c'est de la décoration. » + les 3 manques |
| 3 | `9,32 – 17,43 s` | Qui je suis | Léger Akodjenou, Cotonou → monde entier, `+20 %` visé, 8 compétences, 8 outils |
| 4 | `17,43 – 24,30 s` | NOIR·SON | Page produit premium → `+18 %` de panier moyen (Sandra M.) |
| 5 | `24,30 – 30,15 s` | ASCENSION | Tunnel complet → `412` inscrits en 14 jours (David K.) |
| 6 | `30,15 – 36,27 s` | HORIZON Retreat | `23 %` de conversion, `61 %` d'inscription (Mariam S., 9 % → 23 %) |
| 7 | `36,27 – 42,79 s` | La méthode | Immersion, architecture, copywriting, design, automatisation, tests |
| 8 | `42,79 – 52,10 s` | Appel à l'action | Appel découverte 30 min offert · réponse 24 h · `legerakodjenou6@gmail.com` |

## Direction artistique

- Fond indigo nuit, grille fine, grain et poussière lumineuse (profondeur cinéma).
- Trois orbes colorées : violet `#7C5CFF`, menthe `#22D3A6`, ambre `#FFB84D`.
- Verre dépoli, bordures filaires, ombres douces, compteurs animés en ease-out.
- Une seule animation focale par écran, transitions par balayage lumineux, aucune répétition.
- Nom de marque, numéro de chapitre et barre de progression présents sur toutes les images.

## Structure du dépôt

```
leger-funnel-portfolio/
├── assets/audio/          # vo-s1..s8.mp3 (voix-off) + master_mix.wav
├── film/                  # le MP4 livré
└── scripts/
    ├── film_lib.py                  # rendu (verre, orbes, icônes, easing) + moteur audio
    └── build_leger_portfolio_video.py  # les 8 scènes + assemblage
```

## Régénérer

```bash
# dépendances (une fois)
pip install --break-system-packages numpy pillow opencv-python-headless imageio-ffmpeg scipy
npm install --prefix /tmp/work_cache/fonts @expo-google-fonts/plus-jakarta-sans @expo-google-fonts/inter

# aperçu (8 vignettes)
python3 scripts/build_leger_portfolio_video.py --preview /tmp/preview.jpg

# rendu complet
python3 scripts/build_leger_portfolio_video.py
```

La police est Plus Jakarta Sans (titres) + Inter (textes), via les paquets
`@expo-google-fonts` (licence OFL). Toutes les illustrations, icônes, maquettes
de pages et le score sont générés en code : aucune image ni musique sous licence.

---

# v2 — « identité du site, sans voix off »

`film/leger-akodjenou-funnel-builder-v2-motion-9x16.mp4`
`1080 × 1920` · `30 fps` · **`33,33 s`** · audio = score original + impacts (aucune voix)

## Identité visuelle — tokens réels du portfolio

Extraits du CSS du site (`legerakodjenou6.systeme.io/47e3d8ba`), pas d'interprétation :

| Token | Valeur | Usage |
|---|---|---|
| `ink` | `#0a0a0b` | fond |
| `coal` | `#101012` | surfaces |
| `panel` | `#151517` | cartes |
| `cream` | `#f4f1ea` | texte principal |
| `muted` | `#97938a` | texte secondaire |
| `ember` | `#ff4d00` | accent unique |
| `ember-soft` | `#ff7a3d` | dégradés |
| `line` | `rgba(244,241,234,.09)` | filets |

- **Display** Space Grotesk (500/700) · **Serif** Instrument Serif (+ italique) · **Texte** Inter.
- Fond `#0a0a0b` + `radial-gradient(1200px 800px at 85% -10%, rgba(255,77,0,.08))`.
- **Dot-grid 34 px**, **grain animé** (opacité `.055`, 10 pas), vignettage.
- Titres alternés : plein / **contour** (`-webkit-text-stroke: 1px rgba(244,241,234,.32)`) / ember.
- Numérotation de chapitre identique au site : `(01) Qui suis-je`, `(02) Réalisations`,
  `(03) Processus`, `(05) Ils ont converti`, `(07) Parlons de votre projet`.
- Easings `cubic-bezier(.22,1,.36,1)`, révélations par masque `translateY(110 %)`, marquee.
- Wordmark `LÉGER©`, barre de progression ember.

## Découpage — 108 BPM, coupes sur la mesure

| Plan | Temps | Contenu | Sections du site |
|---|---|---|---|
| 1 | `0,00 – 4,44 s` | « Des tunnels / qui convertissent / à +20 % » + badge + 3 stats | Hero |
| 2 | `4,44 – 8,89 s` | Citation serif + Promesse absente / Zéro preuve / Zéro urgence + compteur `+20 %` | (01) |
| 3 | `8,89 – 13,33 s` | NOIR·SON : maquette + `+18 %` de panier moyen | (02) |
| 4 | `13,33 – 15,56 s` | ASCENSION : `412` inscrits + entonnoir 5 étapes | (02) |
| 5 | `15,56 – 17,78 s` | HORIZON : `23 %` / `61 %` + barres 9 % → 23 % | (02) |
| 6 | `17,78 – 22,22 s` | Les 6 étapes de la méthode + délai `2 à 3 semaines` | (03) |
| 7 | `22,22 – 26,67 s` | `5+ / 24 h / 14 j`, 8 outils, citation | (05) |
| 8 | `26,67 – 33,33 s` | CTA : appel découverte 30 min, e-mail, WhatsApp, `LÉGER©` | (07) |

## Audio (sans voix)

Kick 108 BPM, claps sur 2 & 4, hats 1/8, basse A–F–C–G, pad aigu, arpèges 16ᵉ,
**impact sur chaque coupe**, risers avant les plans 3 et 8, ticks de compteurs, ding final.

Mastering : `highpass 34 Hz`, `-2,5 dB @180 Hz`, `+4 dB @3,2 kHz`, `+8 dB`, limiteur `0,94`.
Résultat : crête `-0,5 dBFS`, RMS `-16,5 dBFS`, homogène sur les 8 plans.

```bash
python3 scripts/build_leger_film_v2.py --preview /tmp/preview.jpg   # 8 vignettes
python3 scripts/build_leger_film_v2.py --audio-only                 # juste le mix
python3 scripts/build_leger_film_v2.py                              # rendu complet
```

---

# v3 — « voix off + identité du site » (version finale)

`film/leger-akodjenou-funnel-builder-v3-voix-off-9x16.mp4`
`1080 × 1920` · `30 fps` · **`52,10 s`** · voix off FR (`voice-02`) + score + impacts

C'est la v1 (avec voix off) **refaite dans l'identité du portfolio** — mêmes tokens,
mêmes polices, même grammaire visuelle que la v2, mais au rythme d'un film narré.

## Calage voix / image

Les 8 clips ont été nettoyés de leurs silences (`silenceremove`) puis ajustés
individuellement (×1,01 à ×1,16, imperceptible) pour tenir dans leur scène :

| Scène | Intervalle | Tempo | Sujet |
|---|---|---|---|
| 1 | `0,00 – 5,00 s` | ×1,012 | Le problème : trafic oui, clients non |
| 2 | `5,00 – 9,32 s` | ×1,000 | « Une belle page qui ne vend pas… » |
| 3 | `9,32 – 17,43 s` | ×1,048 | Qui je suis, +20 %, outils, citation |
| 4 | `17,43 – 24,30 s` | ×1,106 | NOIR·SON, +18 % de panier moyen |
| 5 | `24,30 – 30,15 s` | ×1,163 | ASCENSION, 412 inscrits |
| 6 | `30,15 – 36,27 s` | ×1,095 | HORIZON, 23 % / 61 % |
| 7 | `36,27 – 42,79 s` | ×1,092 | Les 6 étapes + délais |
| 8 | `42,79 – 52,10 s` | ×1,044 | Appel découverte + contacts |

## Différences par rapport à la v1

- Fonds `#0a0a0b` (au lieu du violet), accent unique `#ff4d00`, frise `LÉGER©`.
- Space Grotesk / Instrument Serif / Inter partout ; plus de titres JetBrains/Poppins.
- Dot-grid, grain animé, filets 1 px, numérotation `(01) … (07)` du site.
- Titres alternés plein / contour, citations en Instrument Serif italique.
- Chapitres du site en filigrane à droite, barre de progression ember.
- Ducking de la musique à −62 % sous la voix ; crête `−0,3 dBFS`, moyenne `−14,3 dB`.

## Correctif

Le glyphe `→` n'existe pas dans Instrument Serif : la citation « 9 % → 23 % »
affichait un carré vide. Remplacé par « 9 % à 23 % » partout où la serif est utilisée.

```bash
python3 scripts/build_leger_film_v3.py --preview /tmp/preview.jpg
python3 scripts/build_leger_film_v3.py --audio-only
python3 scripts/build_leger_film_v3.py
```

---

# v4 — « vos clics deviennent des clients » (film de la landing page)

`film/leger-akodjenou-vos-clics-deviennent-des-clients-9x16.mp4`
`1080 × 1920` · `30 fps` · **`58,94 s`** · voix off FR (`voice-03`) + score + impacts

Film écrit pour la page **`https://legerakodjenou.systeme.io/8c1af526`** : chaque
chiffre, prix et promesse vient de la page, rien n'est inventé. Les chiffres du
tableau de bord (12 422 · 4 196 · 311 · 6,8 % · ROAS 4,2× · A/B +38 %) sont
affichés sous le label **« EXEMPLE DE TABLEAU DE BORD »**, comme sur le site.

## Les 8 plans

| # | Intervalle | Sujet |
|---|---|---|
| 1 | `0,00 – 4,55 s` | Hook : « Vos clics deviennent des clients. » + audit offert |
| 2 | `4,55 – 12,10 s` | Diagnostic : 4 fuites, coût `−0 %` |
| 3 | `12,10 – 21,95 s` | Ce que je construis : 5 prestations |
| 4 | `21,95 – 30,40 s` | Le tunnel en 5 étapes + preuves `6,8 % / 4,2× / +38 %` |
| 5 | `30,40 – 37,90 s` | La méthode : J+0 · J+2 · J+7 · J+14 (+ 30 j) |
| 6 | `37,90 – 44,90 s` | Un spécialiste, pas une agence : 1 an · 24 h · FR·BE·CH |
| 7 | `44,90 – 53,10 s` | Tarifs : 240 € · 540 € · sur devis + garantie 30 j |
| 8 | `53,10 – 58,94 s` | Réservation : 3 étapes, e-mail, WhatsApp |

## Audio

Voix off calée à `0,45 / 4,95 / 12,50 / 22,35 / 30,80 / 38,30 / 45,30 / 53,50 s`,
ducking du score `1 − 0,62 · clip(env × 2,5)`, impacts sur les 7 coupes,
normalisation `volume` mesurée en boucle + `alimiter` → **−14,2 LUFS / −3,4 dBTP**.

```bash
python3 scripts/build_leger_film_v4.py --preview /tmp/preview.jpg
python3 scripts/build_leger_film_v4.py --audio-only
python3 scripts/build_leger_film_v4.py
```

---

# v5 — refonte « identité de la landing »

`film/leger-akodjenou-vos-clics-deviennent-des-clients-v5-9x16.mp4`
`1080 × 1920` · `30 fps` · **`66,10 s`** · voix off FR (`voice-03`) + score ducké

Reprise de la v4 demandée par le client : **« inspire-toi exactement de
l'identité visuelle du lien »** et **« évite les voix qui se chevauchent »**.

## Ce qui change par rapport à la v4

| | v4 | v5 |
|---|---|---|
| composition | intertitres en gros blocs | **chaque plan reprend une section réelle du site** |
| titres | « mot / mot » sur 2 lignes | mot plein + **mot en Instrument Serif italique ember** dans la même ligne |
| sections | 8 plans libres | 8 plans = badge → diagnostic → offre → méthode → solo → tarifs → CTA → carton |
| marquee métiers | absent | les 11 métiers du site défilent, **coupés dans la colonne** |
| chevauchements voix | oui (s2/s3, s3/s4, s4/s5, s6/s7, s7/s8) | **non** : 8 prises, 8 plans, garde-fou bloquant |
| durée | 58,94 s | 66,10 s |

## Anti-chevauchement (garanti par le code)

`retime_vo()` mesure la durée utile de chaque mp3 après nettoyage des silences,
refuse de rendre si une prise démarre avant la fin de la précédente + `0,30 s`,
et `build_score()` lève une `SystemExit` en cas de collision. Sortie du contrôle :

```
v4-s1  0,42 →  4,34   (plan 1 : hero)
v4-s2  5,15 → 12,17   (plan 2 : diagnostic)
v4-s3 12,62 → 22,64   (plan 3 : offre)
v4-s4 23,09 → 32,17   (plan 4 : méthode)
v4-s5 32,62 → 40,61   (plan 5 : solo)
v4-s6 41,06 → 48,79   (plan 6 : tarifs)
v4-s7 49,24 → 59,46   (plan 7 : CTA)
v4-s8 59,90 → 65,13   (plan 8 : carton final)
```

Écarts : `0,81 / 0,45 / 0,45 / 0,45 / 0,45 / 0,45 / 0,44 s` — aucun mot à cheval.
Le lit musical descend de 11 dB sous la voix (`ducking 1 − 0,72 · env`).

## Faits affichés (tous issus de la page)

`12 434` visiteurs · `4 200` inscrits · `311` clients · `6,8 %` · `ROAS 4,2×` ·
`+224 %` · `+38 %` (sous « EXEMPLE DE TABLEAU DE BORD ») — `240 €` (2 × 120) ·
`540 €` (3 × 180) · `Sur devis` · garantie conversion `30 jours` ·
`legerakodjenou6@gmail.com` · `+229 52 09 94 23`.

```bash
python3 scripts/build_leger_film_v5.py --retime        # contrôle des départs de voix
python3 scripts/build_leger_film_v5.py --preview /tmp/p.jpg
python3 scripts/build_leger_film_v5.py --audio-only
python3 scripts/build_leger_film_v5.py
```
