# Infographic Blue & Light — découpe brute en 9 × 30 s

**Source** : `imports/Infographic_Blue__Light_1.mp4` — 28,09 Mo · **4 min 25,98 s** ·
852 × 480 (DAR 71:40) · **30,30 fps** · H.264 Constrained Baseline · 844 kb/s · sans piste audio.

**Ce que c'est** : la vidéo telle quelle, coupée toutes les 30 secondes. Pas de recadrage, pas de
mise en 9:16, pas de sous-titre, pas de zoom, pas de musique, pas de raccourci « short viral ».
Chaque fichier garde la **résolution, le format, la cadence et la durée d'origine des plans**.

| Fichier | Source | Durée |
| --- | --- | --- |
| `Infographic_Blue__Light_1_part-00.mp4` | 00:00 → 00:30 | 30,03 s |
| `Infographic_Blue__Light_1_part-01.mp4` | 00:30 → 01:00 | 30,00 s |
| `Infographic_Blue__Light_1_part-02.mp4` | 01:00 → 01:30 | 30,00 s |
| `Infographic_Blue__Light_1_part-03.mp4` | 01:30 → 02:00 | 30,00 s |
| `Infographic_Blue__Light_1_part-04.mp4` | 02:00 → 02:30 | 30,00 s |
| `Infographic_Blue__Light_1_part-05.mp4` | 02:30 → 03:00 | 30,00 s |
| `Infographic_Blue__Light_1_part-06.mp4` | 03:00 → 03:30 | 30,00 s |
| `Infographic_Blue__Light_1_part-07.mp4` | 03:30 → 04:00 | 30,00 s |
| `Infographic_Blue__Light_1_part-08.mp4` | 04:00 → 04:25,98 | 25,97 s |

Total : **265,97 s** = durée de la source, aucune image perdue.

## Commande utilisée

```bash
ffmpeg -i imports/Infographic_Blue__Light_1.mp4 \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -force_key_frames "expr:gte(t,n_forced*30)" \
  -f segment -segment_time 30 -reset_timestamps 1 -segment_format mp4 \
  "infographic-blue-cuts/Infographic_Blue__Light_1_part-%02d.mp4"
```

- `-force_key_frames` : une keyframe **exactement** à chaque multiple de 30 s, donc la coupe tombe
  sur une image-clé et aucun plan n'est dupliqué ni sauté au raccord.
- `-reset_timestamps 1` : chaque fichier repart de 00:00 (lecture propre sur téléphone, Drive, etc.).
- `-crf 18` : qualitativement transparent pour une source à 844 kb/s (l'original ne peut pas être
  dégradé par un encodage plus fin que lui).
- Remux final `-c copy -movflags +faststart` : l'atome `moov` est en tête de fichier, la lecture
  démarre sans attendre tout le téléchargement.

## Vérifications faites

- **Durées** : 8 × 30,00 s + 30,03 s + 25,97 s = 265,97 s (mesurées sur les fichiers produits).
- **Résolution / cadence** : 852 × 480 et 30,30 fps sur les 9 fichiers, identiques à la source.
- **Fidélité** : images extraites à 1 s de chaque partie comparées à la source au même instant →
  écart moyen **0,21 à 0,60 / 255** (différence d'encodage uniquement).
- **Pas de piste audio** : la source n'en a pas, aucune n'a été ajoutée.
- **Contenu** : `contact-sheet.jpg` (1 vignette par partie, prises à 15 s).

À savoir : vers 00:31–00:32 et 02:13–02:15, le template lui-même passe par des écrans presque
blancs (moins de 8 % de la vidéo est dans ce cas). C'est dans **la source**, pas un défaut de
découpe.

## Studio

Les 9 parties sont déclarées dans `youtube-importer/server.py` sous le groupe
`infographic_cuts` (onglet « 🧩 Infographic Blue (9 × 30 s, taille d'origine) »), lisibles en
streaming HTTP 206 et téléchargeables à l'unité ou en `.zip`.
