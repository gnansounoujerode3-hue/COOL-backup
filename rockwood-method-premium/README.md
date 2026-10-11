# rockwood-method-premium

Version premium du montage Rockwood Method — 4ᵉ itération, destinée au feed Pinterest / Reels.

| | |
|---|---|
| **Film** | `film/rockwood-method-premium-9x16.mp4` |
| **Format** | 1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps |
| **Durée** | 29,12 s · 8,9 Mb/s · 33 Mo |
| **Loudness** | −14,0 LUFS intégré · pic vrai −1,5 dBFS |
| **Couverture** | `film/pinterest-cover.jpg` — 1000 × 1500 |
| **Sous-titres** | incrustés + `subtitles/rockwood-method-premium-9x16.srt` |

## Chaîne de rendu

```
1. ffmpeg  : upscale Lanczos, unsharp, courbe en S, colorimétrie chaude, vignettage
             -> flux RGB brut 1080x1920 @ 25 fps
2. Python  : caméra (8 segments + dérive), flou de fouet aux coupes, aberration
             chromatique, halation dosée, grain modulé par la luminance,
             3 scènes de coupe avec visuel produit + médaillon du sujet,
             habillage typographique, sous-titres cinétiques, chrome (bandeau + progression)
3. ffmpeg  : fondu de sortie, mixage audio, encodage H.264 CRF 17 preset slow
```

≈ 4 min 40 s pour 728 images.

## Reconstruction

```bash
cd rockwood-method-premium
export FONTCONFIG_FILE=$PWD/tools/fonts.conf
python3 tools/assets3.py        # habillage typographique (bandeau, titres, cartes, scènes)
python3 tools/make_products.py  # 3 visuels produit + recomposition des scènes de coupe
python3 tools/gen_audio3.py     # musique et SFX (numpy, sans licence)
# mixage (nécessite le rush source) — chaîne ci-dessous
python3 tools/composite4.py film/rockwood-method-premium-9x16.mp4
python3 tools/make_cover3.py    # couverture Pinterest
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

Le rush source est attendu à `../AIDE-CHATGPT-main/video brut.mp4`
(constante `src` dans `tools/composite4.py`).

## Où toucher pour retoucher

| Envie | Fichier | Quoi |
|---|---|---|
| changer un cadrage / une coupe | `tools/plan4.py` | `CAMERA`, `CUTS`, `SCENES` |
| déplacer un bloc, un visuel produit | `tools/plan4.py` | `OVERLAYS`, `PRODUCTS` |
| remplacer un visuel produit par une vraie photo | `assets/prod_*.png` | même nom de fichier, fond transparent |
| moins / plus de grain, d'halation | `tools/composite4.py` | `grain()`, `halation()` |
| autre musique | `tools/gen_audio3.py` | `CHORDS`, `bpm` |

## Notes

- Le dossier `assets/` contient 35 PNG : les visuels produit sont des **illustrations**
  dessinées par `tools/make_products.py` (aucune banque d'images, aucun droit tiers).
- Polices : Space Grotesk, Inter, Instrument Serif (SIL OFL) ; ffmpeg statique via
  `imageio-ffmpeg` ; musique et SFX synthétisés — **coût externe : 0 €**.
- Versions précédentes : `../rockwood-method/` (v1), `../rockwood-method-editorial/` (v2),
  `../rockwood-method-signature/` (v3).
