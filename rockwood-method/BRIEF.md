# Rockwood Method — montage talking-head (9:16)

Montage complet du rush `video brut.mp4` fourni dans le dépôt `AIDE-CHATGPT`
(4 952 006 octets — vidéo identique à `uploads/video brut.js` de la sauvegarde COOL).

**Sortie** : `out/rockwood-method-montage-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High + AAC 192 kbps · 29,12 s · **−14,0 LUFS / pic −1,5 dBFS** · 19,5 Mo

![couverture](out/cover.jpg)

---

## Ce qui a été fait

| Étape | Détail |
|---|---|
| **Diagnostic du rush** | 720×1280 (9:16), 25 fps, 27,60 s, H.264 1365 kb/s, audio AAC HE-v2 44,1 kHz stéréo 64 kb/s |
| **Analyse audio** | voix de 0 à 25,9 s (−22,1 dBFS moyen, pic −3,6 dB) ; pauses nettes à 2,25 / 8,0 / 13,5 / 17,05 / 19,6 / 22,5 s → points de coupe naturels |
| **Transcription** | horodatage **mot à mot** (72 mots) réutilisé depuis `words.json` du projet `rockwood-edit` ; vérifié par échantillonnage audio |
| **Image** | upscale Lanczos 720p → 1080p + léger unsharp ; étalonnage `contrast 1,035 / saturation 1,06 / brightness +0,008` |
| **Sous-titres** | mot-à-mot calé sur la parole : chaque mot passe de terne → **or** (mot prononcé) → crème ; 16 séquences, 1 à 2 lignes |
| **Habillage** | 11 incrustations : pomme de terre, titre, 3 cartes produit, tampon « Game changer », fondation, 100 %, split, CTA, carte finale |
| **Son** | voix : passe-haut 85 Hz + 2 corrections EQ + compression + normalisation −14 LUFS ; musique **originale synthétisée** (Am–F–C–G, 84 BPM) duckée sous la voix ; 12 SFX calés sur les apparitions |
| **Fin** | dernière image gelée 1,5 s sous la carte finale, fondu de sortie 0,48 s |

## Direction artistique

Palette tirée de la vidéo : **brun espresso #241310**, **or #f5c26b**, **crème #fff4e2**, accents terracotta et bleu.

Typographie : **Space Grotesk** (titres et pastilles), **Inter** (sous-titres et libellés), **Instrument Serif italique** (accents). Les trois polices sont sous licence OFL et embarquées dans le build.

Aucun logo, chiffre ou marque inventé : le seul élément textuel externe est l'URL `rockwoodmethod.com/shop`, prononcée dans la voix off au CTA.

## Structure

```
rockwood-method/
├── BRIEF.md                  ← ce document
├── README.md                 ← notice de reconstruction
├── build/
│   ├── plan.py               ← timeline : 12 calques + découpage des sous-titres
│   ├── make_assets.py        ← génère les 12 PNG d'habillage (Pillow)
│   ├── make_subs.py          ← génère subs.ass (sous-titres ASS animés)
│   ├── gen_audio.py          ← synthétise musique + SFX (numpy, sans licence)
│   ├── composite.py          ← compositor image par image + rendu final
│   ├── render.sh             ← chaîne audio : EQ → ducking → mix → rendu
│   └── fonts.conf            ← fontconfig local
├── assets/                   ← 12 PNG d'habillage (fond transparent)
├── audio/                    ← music.wav, sfx.wav, words.json (timing mot à mot)
├── subtitles/                ← SRT exportable pour le client
└── out/                      ← vidéo finale + couverture
```

## Reconstruction

```bash
cd rockwood-method
export FONTCONFIG_FILE=$PWD/build/fonts.conf
# 1) habillage + sous-titres + audio
python3 build/make_assets.py && python3 build/make_subs.py && python3 build/gen_audio.py
# 2) mixage de la voix (nécessite le rush source)
bash build/render.sh
# 3) rendu final 1080x1920
python3 build/composite.py out/rockwood-method-montage-9x16.mp4
```

Le rush source `video brut.mp4` doit être placé à `../AIDE-CHATGPT-main/video brut.mp4`
relativement au dossier de travail (chemin défini dans `build/composite.py`).

## Notes techniques

- Le build a été fait avec **ffmpeg 7.0.2** (binaire statique) et **Pillow / numpy** ; les polices proviennent des paquets npm `@expo-google-fonts/*`.
- `\1img` d'ASS n'est pas supporté par le build libass utilisé : les incrustations sont composées **côté Python** (`composite.py`), ce qui permet en plus des animations plus fines (ease-out, pop, zoom) que ce qu'autorise ASS.
- Le texte de la vidéo est en **anglais** (langue de la voix off) ; l'habillage l'est aussi par cohérence — la carte CTA porte « link in bio ».

## À vérifier avant publication

- L'URL `rockwoodmethod.com/shop` est **déduite de l'audio** (« …com shop ») — à confirmer.
- La personne à l'écran n'est pas nommée dans la vidéo : garder le titre « The Rockwood Method » évite toute invention.
