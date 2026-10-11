# rockwood-method-cinema-plus

Version cinéma + — 6ᵉ itération du montage Rockwood Method, destinée au feed Pinterest / Reels.

| | |
|---|---|
| **Film** | `film/rockwood-method-cinema-plus-9x16.mp4` |
| **Format** | 1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps |
| **Durée** | 29,12 s · 8,9 Mb/s · 33 Mo |
| **Loudness** | −14,0 LUFS intégré · pic vrai −1,5 dBFS |
| **Couverture** | `film/pinterest-cover.jpg` — 1000 × 1500 |
| **Sous-titres** | incrustés + `subtitles/rockwood-method-cinema-plus-9x16.srt` |

## Chaîne de rendu

```
1. ffmpeg  : upscale Lanczos, unsharp, courbe en S, colorimétrie chaude, vignettage
             -> flux RGB brut 1080x1920 @ 25 fps
2. Python  : caméra (8 segments + dérive), flou de fouet, caméra portée, aberration
             chromatique, halation dosée, grain modulé par la luminance,
             fuites de lumière aux coupes, 3 scènes de coupe à fond reconstruit,
             beat kinétique du 100 % avec halo, carte finale à push-in,
             habillage, sous-titres cinétiques, chrome (bandeau + progression)
3. ffmpeg  : fondu de sortie, mixage audio, encodage H.264 CRF 17 preset slow
```

≈ 5 min 50 s pour 728 images.

## Dépendances

```bash
pip install --break-system-packages pillow numpy imageio-ffmpeg
# polices (SIL OFL) : Space Grotesk, Inter, Instrument Serif
npm install @expo-google-fonts/space-grotesk @expo-google-fonts/inter @expo-google-fonts/instrument-serif
```

Le binaire ffmpeg utilisé est celui d'`imageio-ffmpeg` ; le chemin est
surchargeable par `FFMPEG_BIN`. Le dossier `node_modules/` est attendu à la racine
de la version (surchargeable par `ROCKWOOD_FONTS`).

## Reconstruction

```bash
cd rockwood-method-cinema-plus
export FONTCONFIG_FILE=$PWD/tools/fonts.conf

python3 tools/assets3.py          # habillage de base (bandeau, cartes, surlignés, pilule…)
python3 tools/make_products.py    # 3 visuels produit
python3 tools/make_cine_assets.py # blocs typographiques transparents (cut01-03, endtype)
python3 tools/gen_audio3.py       # musique et SFX (numpy, sans licence)
python3 tools/composite6.py film/rockwood-method-cinema-plus-9x16.mp4
python3 tools/make_cover5.py      # couverture Pinterest 1000 × 1500
```

Le rush source est attendu à `../AIDE-CHATGPT-main/video brut.mp4`
(surchargeable par `ROCKWOOD_RUSH`).

Variables reconnues : `ROCKWOOD_WORK`, `ROCKWOOD_ASSETS`, `ROCKWOOD_FONTS`,
`ROCKWOOD_MIX`, `ROCKWOOD_WORDS`, `ROCKWOOD_RUSH`, `FFMPEG_BIN`
— ainsi que `V6_QC_TIMES` / `V6_QC_OUT` pour ne rendre qu'une planche de contrôle,
sans encoder la vidéo (les temps doivent tomber sur des multiples exacts de 1/25 s) :

```bash
V6_QC_TIMES=8.00,8.08,17.28,17.96,27.60 V6_QC_OUT=qc.jpg \
  python3 tools/composite6.py /tmp/inutile.mp4
```

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

| Envie | Fichier | Quoi |
|---|---|---|
| plus / moins de caméra portée | `tools/composite6.py` | `handheld()` — `amp`, `deg`, `zoom` et les fréquences |
| durée ou force des fuites de lumière | `tools/composite6.py` | `LEAK`, `LEAK_AT` (gain par coupe), `LEAK_DUR` |
| le beat du 100 % | `tools/composite6.py` | `draw_count()` (ressort `0,95·e^(−6,2u)·cos(8,4u)`) + `HALO` |
| push-in de la carte finale | `tools/composite6.py` | `draw_endcard()` — `sc`, `drift` |
| changer un cadrage / une coupe | `tools/plan4.py` | `CAMERA`, `CUTS`, `SCENES` |
| un fond de scène plus sombre / plus flou | `tools/composite6.py` | `cine_bg()` |
| un type plus ou moins détaché du fond | `tools/composite6.py` | `make_plate()` et `PLATE_CUT`, `PLATE_END`, `PLATE[…]` |
| remplacer un visuel produit par une vraie photo | `assets/prod_*.png` | même nom de fichier, fond transparent |
| refaire la couverture | `tools/make_cover5.py` | `COVER_T` (temps du plan), `CROP_Y`, position de la pilule |
| autre musique | `tools/gen_audio3.py` | `CHORDS`, `bpm` |

## Notes

- **Aucune image externe** : portraits, produits, bokeh, plaques, flashs et halo sont
  calculés en code (numpy + Pillow).
- La v6 est une **surcouche de mouvement** : tout ce qui fait la v5 (fonds reconstruits,
  plaques, carte finale) est inchangé — seul le rendu du mouvement et du rythme évolue.
- Polices : Space Grotesk, Inter, Instrument Serif (SIL OFL) ; ffmpeg statique via
  `imageio-ffmpeg` ; musique et SFX synthétisés — **coût externe : 0 €**.
- Versions précédentes : `../rockwood-method/` (v1), `../rockwood-method-editorial/` (v2),
  `../rockwood-method-signature/` (v3), `../rockwood-method-premium/` (v4),
  `../rockwood-method-cinema/` (v5).
