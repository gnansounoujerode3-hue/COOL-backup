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
