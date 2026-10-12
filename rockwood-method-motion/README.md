# rockwood-method-motion

Version motion (v7) — le montage Rockwood Method mis au niveau motion design, pour le feed Pinterest / Reels.

| | |
|---|---|
| **Film** | `film/rockwood-method-motion-9x16.mp4` |
| **Format** | 1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps |
| **Durée** | 29,12 s · 9,0 Mb/s · 33 Mo |
| **Loudness** | −14,0 LUFS intégré · pic vrai −1,5 dBFS |
| **Couverture** | `film/pinterest-cover.jpg` — 1000 × 1500 |
| **Sous-titres** | incrustés + `subtitles/rockwood-method-motion-9x16.srt` |

## Chaîne de rendu

```
1. ffmpeg  : upscale Lanczos, unsharp, courbe en S, colorimétrie chaude, vignettage
             -> flux RGB brut 1080x1920 @ 25 fps
2. Python  : caméra (8 segments + dérive + anticipation aux coupes), flou de fouet,
             caméra portée, aberration chromatique, halation dosée, grain modulé,
             fuites de lumière, poussières dorées, 3 scènes de coupe à fond reconstruit
             (texte en cascade + produit + médaillon), beat du 100 % en ressort,
             rail de pellicule, carte finale à push-in (texte en cascade), sous-titres
3. ffmpeg  : fondu de sortie, mixage audio, encodage H.264 CRF 17 preset slow
```

≈ 5 min 25 s pour 728 images.

## Dépendances

```bash
pip install --break-system-packages pillow numpy imageio-ffmpeg
# polices (SIL OFL) : Space Grotesk, Inter, Instrument Serif
npm install @expo-google-fonts/space-grotesk @expo-google-fonts/inter @expo-google-fonts/instrument-serif
```

Le binaire ffmpeg utilisé est celui d'`imageio-ffmpeg` (surchargeable par `FFMPEG_BIN`).
Le dossier `node_modules/` est attendu à la racine de la version (surchargeable par
`ROCKWOOD_FONTS`).

## Reconstruction

```bash
cd rockwood-method-motion
export FONTCONFIG_FILE=$PWD/tools/fonts.conf

python3 tools/assets3.py           # habillage de base (bandeau, cartes, surlignés, pilule…)
python3 tools/make_products.py     # 3 visuels produit
python3 tools/make_cine_assets7.py # blocs typographiques découpés en 4 parties animables
python3 tools/gen_audio3.py        # musique et SFX (numpy, sans licence)
python3 tools/composite7.py        # -> film/rockwood-method-motion-9x16.mp4
python3 tools/make_cover7.py       # couverture Pinterest 1000 × 1500
```

Le rush source est attendu à `../AIDE-CHATGPT-main/video brut.mp4`
(surchargeable par `ROCKWOOD_RUSH`).

## Mode contrôle (planche de frames)

Rend une planche sans encoder la vidéo : indispensable pour régler du mouvement
(les temps doivent tomber sur des multiples exacts de 1/25 s).

```bash
ROCKWOOD_RUSH="../AIDE-CHATGPT-main/video brut.mp4" \
V7_QC_TIMES=8.00,8.08,8.16,8.32,26.00,26.16 \
V7_QC_OUT=qc.jpg python3 tools/composite7.py /tmp/inutile.mp4
```

≈ 10 frames en 45 s au lieu de 5 min 25 pour les 728.

Variables reconnues : `ROCKWOOD_WORK`, `ROCKWOOD_ASSETS`, `ROCKWOOD_FONTS`,
`ROCKWOOD_MIX`, `ROCKWOOD_WORDS`, `ROCKWOOD_RUSH`, `FFMPEG_BIN`,
`V7_QC_TIMES`, `V7_QC_OUT` (et `COVER_KEEP_STRIP=1` pour garder le rail de
pellicule dans la couverture, retiré par défaut).

### Mixage (chaîne exacte)

```bash
ffmpeg -i voix.wav -af "highpass=f=85,\
equalizer=f=250:t=q:w=1.1:g=-2.2,equalizer=f=3200:t=q:w=1.2:g=2.2,\
equalizer=f=7000:t=q:w=1.4:g=1.2,\
acompressor=threshold=-20dB:ratio=2.8:attack=8:release=220:makeup=2,\
loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -ac 2 voice_norm.wav

ffmpeg -i music3.wav -i voice_norm.wav -filter_complex \
"[0:a]volume=0.30[m];[m][1:a]sidechaincompress=threshold=0.028:ratio=7:attack=22:release=440[d]" \
-map "[d]" music_duck.wav

ffmpeg -i voice_norm.wav -i music_duck.wav -i sfx3.wav -filter_complex \
"[2:a]volume=0.46[s];[0:a][1:a][s]amix=inputs=3:duration=longest:normalize=0[mx];\
[mx]alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[out]" -map "[out]" -ac 2 -ar 48000 mix3.wav
```

Contrôle : `ffmpeg -i mix3.wav -filter_complex ebur128=peak=true -f null -`
→ **I : −14,0 LUFS · Peak : −1,5 dBFS**.

## Où toucher pour retoucher

### Le mouvement (tout est dans `tools/composite7.py`)

| Envie | Quoi |
|---|---|
| adoucir / durcir toutes les entrées | `EASE_ENTER` (cubic-bezier des entrées) |
| changer le rythme de la cascade | `STAGGER` (90 ms) et `HOLD` (100 ms de temps mort) |
| entrées plus longues / plus courtes | `DUR_MICRO`, `DUR_HERO` |
| sorties plus lentes | `EXIT_RATIO` (0,68) |
| courses plus amples | `D_MICRO`, `D_HERO` (26 px / 44 px) |
| anticipation des coupes | `cut_kick()` (1 % de zoom, 200 ms avant, 260 ms après) |
| caméra portée | `handheld()` — `amp`, `deg`, `zoom`, fréquences |
| cascades (délais par partie) | `draw_cine_scene()` et `draw_endcard()`, tuples `(key, delay, dist, dur)` |
| poussières dorées | bloc `MOTES` (`_rng`, comptage, vitesses, opacités) |
| rail de pellicule | `draw_strips()` (position, libellé, tick) |
| ressort du compteur | `draw_count()` — `0,45·e^(−7,6u)·cos(8,4u)` |
| anticipation, suivi produit, médaillon | mêmes fonctions, constantes `HOLD` / `STAGGER` |

### Le reste

| Envie | Fichier | Quoi |
|---|---|---|
| changer un cadrage / une coupe | `tools/plan4.py` | `CAMERA`, `CUTS`, `SCENES` |
| un fond de scène plus sombre / plus flou | `tools/composite7.py` | `cine_bg()` |
| un type plus ou moins détaché du fond | `tools/composite7.py` | `make_plate()`, `PLATE_CUT`, `PLATE_END` |
| d'autres textes de scène de coupe | `tools/plan4.py` + `tools/make_cine_assets7.py` | `CUTAWAYS` puis les 4 parties |
| push-in de la carte finale | `tools/composite7.py` | `draw_endcard()` — `sc`, `drift` |
| refaire la couverture | `tools/make_cover7.py` | `COVER_T`, `CROP_Y`, nettoyage du rail (`y0, y1 = 286, 344`) |
| remplacer un visuel produit par une vraie photo | `assets/prod_*.png` | même nom, fond transparent |
| autre musique | `tools/gen_audio3.py` | `CHORDS`, `bpm` |

## Notes

- Les blocs de texte sont livrés **découpés** (`cut01_a…d.png`, `endtype_a…d.png`)
  pour permettre la cascade : les recomposer en un seul PNG supprime l'orchestration.
- `cut0*.png` et `endtype.png` (blocs entiers) restent livrés : ils servent à caler
  la plaque de lisibilité.
- **Aucune image externe** : portraits, produits, bokeh, plaques, flashs, halo et
  poussières sont calculés en code (numpy + Pillow).
- Polices : Space Grotesk, Inter, Instrument Serif (SIL OFL) ; ffmpeg statique via
  `imageio-ffmpeg` ; musique et SFX synthétisés — **coût externe : 0 €**.
- Versions précédentes : `../rockwood-method/` (v1), `../rockwood-method-editorial/` (v2),
  `../rockwood-method-signature/` (v3), `../rockwood-method-premium/` (v4),
  `../rockwood-method-cinema/` (v5), `../rockwood-method-cinema-plus/` (v6).
