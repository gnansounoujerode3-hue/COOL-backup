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

---

# Version voix off — offre « 1 500 modèles · 7 000 FCFA »

`Infographic_Blue__Light_1_voix-off.mp4` — **4 min 25,98 s** · 852 × 480 · 30,30 fps ·
31,6 Mo · vidéo **recopiée sans réencodage** (flux H.264 identique à la source, empreinte
MD5 `eb63d2cc…` sur les deux fichiers) · audio AAC 48 kHz stéréo.

Script complet et timecodes : `voix-off/script.md` · montage reproductible :
`voix-off/build_vo.py` · prises : `voix-off/seg01…seg10.mp3`.

## Découpage de la voix

| # | Timecode | Rôle |
| --- | --- | --- |
| 1 | 0:03 | accroche |
| 2 | 0:18 | « ce sont de vraies diapositives » |
| 3 | 0:44 | la douleur : 3 heures sur une présentation |
| 4 | 1:16 | le pack : 1 500 modèles déjà animés |
| 5 | 1:46 | la variété des mises en page |
| 6 | 2:18 | les usages : exposé, soutenance, réunion… |
| 7 | 2:44 | l'objection « je ne suis pas graphiste » |
| 8 | 3:10 | l'offre : 7 000 FCFA, livraison 24 h, CTA |
| 9 | 3:46 | pont vers les cartes |
| 10 | 4:06 | signature |

## Mesures

- Loudness intégrée **−16,0 LUFS**, LRA **5,5 LU**, crête **−1,4 dBTP** (norme parole).
- Niveau des dix blocs : **−15,8 à −16,4 dBFS RMS** — aucune phrase ne domine.
- Silences entre les blocs : **numériques** (aucun souffle résiduel, aucune boucle de fond).
- Durée audio **265,94 s** = durée image **265,98 s** (écart de 4 centièmes, arrondi AAC).

## Traitement appliqué à la voix

`highpass 85 Hz` (retire le rumble), `lowpass 15 kHz` (retire le souffle de synthèse),
compression douce 3,5:1, coupe des silences de tête/queue, fondu 8 ms, égalisation de niveau
par prise, puis master `loudnorm −16 LUFS / −1,5 dBTP`.

## À valider par toi

Le numéro, le lien ou le canal de commande n'était pas précisé : la voix dit
**« envoie simplement le mot PACK en message privé »**. Si tu vends plutôt par WhatsApp,
par un lien de paiement ou par un commentaire, dis-le et je réenregistre la phrase finale
(une seule prise) — aucune autre ligne ne change.
