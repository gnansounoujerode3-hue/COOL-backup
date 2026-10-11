# felix-gray-reference6

Montage complet de `video brut 5 - Copie.mp4` inspiré de la direction artistique, des cutaways dark-mode et des animations 3D/typographiques de `REFERENCE 6.mp4`.

| Caractéristique | Valeur |
|---|---|
| **Film final** | `film/felix-gray-reference6-9x16.mp4` |
| **Format** | 1080 × 1920 (9:16) · 24 fps · H.264 High (`CRF 18`) · AAC 192 kbps (`48 kHz`) |
| **Durée** | 48,79 s (1 171 images) |
| **Loudness** | −14,0 LUFS intégré · −1,5 dBTP · LRA 2,4 LU |
| **Couverture** | `film/cover-9x16.jpg` (1080 × 1920) |
| **Sous-titres** | `subtitles/felix-gray-reference6-9x16.srt` (44 séquences) |

---

## Structure du projet

```text
felix-gray-reference6/
├── BRIEF.md                                  ← Analyse de REFERENCE 6 et découpage temporel
├── README.md                                 ← Documentation technique et commandes de build
├── audio/
│   └── words.json                            ← Transcription horodatée mot-à-mot (197 mots)
├── film/
│   ├── felix-gray-reference6-9x16.mp4        ← Vidéo finale montée (1080×1920, 24 fps)
│   └── cover-9x16.jpg                        ← Miniature / couverture 9:16
├── subtitles/
│   └── felix-gray-reference6-9x16.srt        ← Sous-titres SRT synchronisés
└── tools/
    ├── plan.py                               ← Timeline maîtresse (coupes, caméra, cutaways, palette)
    ├── render_graphics.py                    ← Moteur graphique 2D/3D (Squircle 3D + shatter Voronoï, carte UI, orbite FG, ?, lockups)
    ├── gen_audio.py                          ← Synthèse musicale dark-synth + SFX synchronisés + mixage -14 LUFS
    ├── composite.py                          ← Compositeur 1080×1920 24 fps et encodage H.264
    └── make_cover.py                         ← Génération de la miniature et du fichier SRT
```

---

## Reconstruction complète

```bash
# 1. Générer la bande-son (musique synthétisée + SFX + mastering voix -14 LUFS)
python3 felix-gray-reference6/tools/gen_audio.py

# 2. Générer la couverture 9:16 et les sous-titres SRT
python3 felix-gray-reference6/tools/make_cover.py

# 3. Assembler et encoder le film final (1080x1920 @ 24 fps)
python3 felix-gray-reference6/tools/composite.py
```

---

## Chaîne de mixage audio

1. **Voix originale** : filtre passe-haut (`85 Hz`), nettoyage bas-médium (`250 Hz, -2,4 dB`), présence (`3,2 kHz, +2,4 dB`), air (`7 kHz, +1,2 dB`), compression broadcast (`ratio 2,8:1`) et normalisation `-14 LUFS`.
2. **Musique dark-synth (92 BPM)** : nappes `Cm9 → Abmaj7 → Fm9 → G7sus4`, pulsations sub-bass et arpèges feutrés, duckée par sidechain sous la voix (`ratio 6,5:1`).
3. **Design sonore (SFX)** :
   - *Whooshes* directionnels sur chaque coupe et transition de cutaway ;
   - *UI pops* cristallins sur les entrées typographiques et l'incrémentation `1+ → 99+` ;
   - *Explosion 3D (Shatter)* à `21,74 s` (impact grave + 28 micro-éclats cristallins) ;
   - *Ondes sonar* (`25,20 s – 25,68 s`) et *3 carillons ascendants* (`27,08 s`, `28,22 s`, `29,18 s`) sur l'orbite Felix Gray ;
   - *Impact sub + shimmer* sur le CTA final `'FelixGray.com'` (`46,92 s`).
