# rockwood-method

Montage complet du rush talking-head **Rockwood Method**, réalisé depuis la source
déposée dans le dépôt `AIDE-CHATGPT`.

| | |
|---|---|
| **Fichier final** | `out/rockwood-method-montage-9x16.mp4` |
| **Format** | 1080 × 1920 (9:16) · 25 fps · H.264 High / AAC 192 kbps |
| **Durée** | 29,12 s (rush 27,60 s + réserve finale) |
| **Loudness** | −14,0 LUFS intégré · pic vrai −1,5 dBFS |
| **Sous-titres** | incrustés (AST) + `subtitles/rockwood-method-montage-9x16.srt` |
| **Musique** | originale et synthétisée — aucune licence, aucun coût |

## Pipeline

1. **Diagnostic** — ffprobe sur le rush : 720×1280, 25 fps, 27,6 s, audio HE-AACv2 64 kb/s.
2. **Découpage** — la structure est calée sur les pauses réelles de la voix off (relevées par analyse RMS) :
   accroche 0–4,2 s · méthode 4,2–13,3 s · fondation 13,7–16,9 s · preuve 17,3–19,4 s · bénéfice 19,8–22,3 s · CTA 22,7–27,6 s · carte finale 27,6–29,1 s.
3. **Image** — upscale Lanczos, unsharp léger, étalonnage chaud.
4. **Habillage** — 12 calques PNG dessinés par script (aucune image tierce), animés en Python.
5. **Sous-titres** — ASS avec karaoké mot à mot (terne → or → crème), 1 à 2 lignes, aucun chevauchement.
6. **Son** — nettoyage de la voix, musique duckée par sidechain, SFX calés sur chaque apparition, limiteur + loudness −14 LUFS.

## Fichiers

- `build/plan.py` — source de vérité de la timeline (calques, coupes, position des sous-titres).
- `build/make_assets.py` — génère les PNG (`assets/`).
- `build/make_subs.py` — génère `build/subs.ass`.
- `build/gen_audio.py` — synthétise `audio/music.wav` et `audio/sfx.wav`.
- `build/composite.py` — compositeur image par image + encodage final.
- `build/render.sh` — mixage audio (voix → ducking → mix).
- `BRIEF.md` — direction artistique et détail du travail.

## Reconstruire

```bash
export FONTCONFIG_FILE=$PWD/build/fonts.conf
python3 build/make_assets.py && python3 build/make_subs.py && python3 build/gen_audio.py
bash build/render.sh                                     # nécessite le rush source
python3 build/composite.py out/rockwood-method-montage-9x16.mp4
```

## Crédits et droits

- Voix : originale, extraite du rush fourni.
- Musique et SFX : synthétisés par `build/gen_audio.py` (numpy) — libres de toute licence.
- Polices : Space Grotesk, Inter, Instrument Serif (SIL Open Font License).
- Polices et ffmpeg statique récupérés via npm / PyPI ; aucune donnée tierce incorporée.
