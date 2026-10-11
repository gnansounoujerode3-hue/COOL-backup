# rockwood-method-signature

Version finale du montage Rockwood Method — grammaire de film + finitions filmiques.
C'est la version à publier.

| | |
|---|---|
| **Film** | `film/rockwood-method-signature-9x16.mp4` |
| **Format** | 1080 × 1920 · 25 fps · H.264 High (CRF 17 / preset slow) · AAC 192 kbps |
| **Durée** | 29,12 s |
| **Débit** | 8,9 Mb/s (32,5 Mo) |
| **Loudness** | −14,0 LUFS intégré · pic vrai −1,5 dBFS |
| **Couverture** | `film/pinterest-cover.jpg` — 1000 × 1500, format natif Pinterest |
| **Sous-titres** | incrustés + `subtitles/rockwood-method-signature-9x16.srt` |

## Pipeline

```
1. ffmpeg  : upscale Lanczos + unsharp + eq + curve en S + colorbalance + vignette -> RGB brut
2. Python  : caméra (8 segments) → flou de fouet (13 coupes) → aberration chromatique
             → halation ambrée → grain modulé par la luminance
             → scènes de coupe + médaillon du sujet → habillage → sous-titres → chrome
3. ffmpeg  : fondu de sortie + mixage audio + encodage
```

Rendu complet : ≈ 4 min 10 pour 728 images.

## Fichiers clés

- **`tools/plan3.py`** — source de vérité : scènes, coupes, segments caméra, cutaways, sous-titres.
  C'est le seul fichier à toucher pour retoucher le rythme.
- `tools/assets3.py` — dessine les 26 PNG d'habillage (bandeau, running heads, cutaways, médaillon).
- `tools/captions3.py` — moteur de sous-titres (mots fusionnés, montée mot à mot, or → crème).
- `tools/composite3.py` — compositeur : caméra, flou de fouet, halation, aberration, grain, scènes.
- `tools/gen_audio3.py` — synthèse musicale et SFX (aucune licence).
- `tools/make_cover3.py` — couverture Pinterest avec le même grade.

## Reconstruction

```bash
cd rockwood-method-signature
export FONTCONFIG_FILE=$PWD/tools/fonts.conf
python3 tools/assets3.py        # habillage
python3 tools/gen_audio3.py     # musique + SFX
# mixage (voir ci-dessous) -> tools/mix3.wav
python3 tools/composite3.py film/rockwood-method-signature-9x16.mp4
python3 tools/make_cover3.py    # couverture
```

Le rush source doit être à `../AIDE-CHATGPT-main/video brut.mp4` (variable `src` dans
`composite3.py` et `make_cover3.py`).

### Mixage (chaîne exacte)

```bash
# 1. voix : passe-haut + EQ (creux 260 Hz, présence 3,3 kHz) + compression + −14 LUFS
ffmpeg -i voix.wav -af "highpass=f=85,equalizer=f=260:t=q:w=1.1:g=-2.2,\
equalizer=f=3300:t=q:w=1.2:g=2.2,equalizer=f=7200:t=q:w=1.4:g=1.1,\
equalizer=f=180:t=q:w=1.0:g=1.2,acompressor=threshold=-20dB:ratio=2.6:attack=6:release=200:makeup=2,\
loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -ac 2 voice_norm.wav

# 2. musique duckée sous la voix
ffmpeg -i music3.wav -i voice_norm.wav -filter_complex \
"[0:a]volume=0.32[m];[m][1:a]sidechaincompress=threshold=0.026:ratio=7:attack=20:release=420[d]" \
-map "[d]" music_duck.wav

# 3. mix final (voix + musique + SFX) avec limiteur et normalisation
ffmpeg -i voice_norm.wav -i music_duck.wav -i sfx3.wav -filter_complex \
"[2:a]volume=0.5[s];[0:a][1:a][s]amix=inputs=3:duration=longest:normalize=0[mx];\
[mx]alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[out]" -map "[out]" mix3.wav
```

## Réglages rapides

| Envie | Où |
|---|---|
| Moins / plus de grain | `composite3.py`, `grain()` → `5.2` (amplitude) |
| Halation plus discrète | `composite3.py`, `halation()` → `46.0` (ajout) et `0.30` (screen) |
| Push-in plus marqué | `composite3.py`, `camera()` → `1 + 0.014 * p` et zooms de `SEGMENTS` |
| Flou de fouet plus court | `composite3.py`, `whip()` → `0.17` |
| Autres mots-clés en or | `plan3.py`, `KEYWORDS` |
| Décliner en 4:5 / 1:1 | `plan3.py`, `W, H` + les positions d'ancre (le reste suit) |

## Crédits et droits

- Voix : originale, extraite du rush fourni.
- Musique et SFX : synthétisés par `tools/gen_audio3.py` — libres de toute licence.
- Polices : Space Grotesk, Inter, Instrument Serif (SIL Open Font License).

## À confirmer avant publication

- `rockwoodmethod.com/shop` est déduit de la prononciation (« …com shop »).
- La personne à l'écran n'est pas nommée : le film reste sur « The Rockwood Method ».
