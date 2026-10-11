# rockwood-method-editorial

Version éditoriale du montage Rockwood Method — rendu « magazine » pour Pinterest / Reels.

| | |
|---|---|
| **Film** | `film/rockwood-method-editorial-9x16.mp4` |
| **Format** | 1080 × 1920 · 25 fps · H.264 High (CRF 17) · AAC 192 kbps |
| **Durée** | 29,12 s |
| **Loudness** | −14,0 LUFS intégré · pic vrai −1,5 dBFS |
| **Couverture** | `film/pinterest-cover.jpg` — 1000 × 1500 |
| **Sous-titres** | incrustés + `subtitles/rockwood-method-editorial-9x16.srt` |

## Différences avec la v1 (`../rockwood-method/`)

| | v1 | v2 éditoriale |
|---|---|---|
| Habillage | cartes à cadre, 11 calques | système à filets fins, 16 calques, panneaux fondus |
| Caméra | plan fixe | 7 segments recadrés + dérive lente |
| Étalonnage | contraste / saturation | + courbe en S, colorimétrie chaude, vignettage, grain |
| Bandeau | — | masthead permanent + barre de progression |
| Sous-titres | mot-à-mot crème | mot-à-mot + **mots-clés en serif italique or** |
| Musique | 84 BPM, 4 accords | 78 BPM, accords enrichis, grain vinyle, riser |
| SFX | blips | ticks papier, tapis, impact grave, carillon |
| Encodage | CRF 18 / preset medium | CRF 17 / preset slow |

## Pipeline technique

```
1. ffmpeg  : upscale Lanczos + unsharp + eq + curves + colorbalance + vignette + noise
             -> flux RGB brut (1080x1920, 25 fps)
2. Python  : recadrage caméra par segment, composition des 16 calques (Pillow)
             + masthead persistant + barre de progression recadrée
3. ffmpeg  : sous-titres ASS (mots-clés serif or), fondu de sortie, mixage, H.264
```

Le rendu complet prend ≈ 3 minutes pour 728 images.

## Reconstruire

```bash
cd rockwood-method-editorial
export FONTCONFIG_FILE=$PWD/tools/fonts.conf
python3 tools/make_assets2.py     # 16 PNG d'habillage
python3 tools/make_subs2.py       # sous-titres ASS
python3 tools/gen_audio2.py       # musique + SFX synthétisés
# mixage (nécessite le rush source)
ffmpeg -i "<rush>" -vn -ac 2 -ar 44100 -c:a pcm_s16le tools/voix.wav
... (voir la section « mixage » ci-dessous)
python3 tools/composite2.py film/rockwood-method-editorial-9x16.mp4
python3 tools/make_cover.py       # couverture Pinterest
```

### Mixage (chaîne exacte)

```bash
# voix : passe-haut + EQ + compression + normalisation
ffmpeg -i voix.wav -af "highpass=f=85,\
equalizer=f=250:t=q:w=1.1:g=-2.2,equalizer=f=3200:t=q:w=1.2:g=2.2,\
equalizer=f=7000:t=q:w=1.4:g=1.2,\
acompressor=threshold=-20dB:ratio=2.8:attack=8:release=220:makeup=2,\
loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -ac 2 voice_norm.wav

# musique duckée sous la voix
ffmpeg -i music2.wav -i voice_norm.wav -filter_complex \
"[0:a]volume=0.30[m];[m][1:a]sidechaincompress=threshold=0.028:ratio=7:attack=22:release=440[d]" \
-map "[d]" music_duck.wav

# mix final
ffmpeg -i voice_norm.wav -i music_duck.wav -i sfx2.wav -filter_complex \
"[2:a]volume=0.46[s];[0:a][1:a][s]amix=inputs=3:duration=longest:normalize=0[mx];\
[mx]alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[out]" -map "[out]" mix2.wav
```

## Notes

- Le rush source doit être à `../AIDE-CHATGPT-main/video brut.mp4` (chemin dans `tools/composite2.py`),
  ou adaptez la variable `src`.
- `tools/composite2.py` contient la table `SEGMENTS` (découpage caméra) et `PAD` (marges d'ombre
  des PNG) : ce sont les deux endroits à toucher pour retoucher le cadrage.
- Polices : Space Grotesk, Inter, Instrument Serif (SIL OFL) ; musique et SFX synthétisés par
  `tools/gen_audio2.py` — aucune licence, aucun coût.

## À confirmer avant publication

- `rockwoodmethod.com/shop` est déduit de la prononciation (« …com shop »).
- La personne à l'écran n'est pas nommée : le film reste sur « The Rockwood Method ».
