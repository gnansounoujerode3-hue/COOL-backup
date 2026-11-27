# Clipping Studio

Transforme une vidéo longue **16:9 en Shorts 9:16 sous-titrés**, prêts à publier.
Pipeline 100 % local (Python + OpenCV + ffmpeg), aucune API payante.

```
clips/clip-01-9s-9x16.mp4    28,6 s   le passage le plus fort, recadré sur le visage
clips/clip-04-173s-9x16.mp4  29,0 s
clips/clip-06-265s-9x16.mp4  14,6 s
```

## Ce que fait le moteur

1. **Sélection des extraits** (`find_clips`)
   le transcript est découpé en phrases, puis chaque fenêtre de 18–40 s est
   notée : mots de hook (« parce que », « la vérité », « erreur »…), chiffres,
   questions, densité de parole, pronoms d'adresse, **et pénalité si la coupe
   tombe au milieu d'une phrase**. On garde les meilleures fenêtres qui ne se
   chevauchent pas.
2. **Recadrage qui suit le sujet** (`build_crop_track`)
   pas de modèle à télécharger : soustraction du fond temporel (médiane de la
   séquence) + repli sur un barycentre de teintes chair ; lissage par moyenne
   glissante et **plafond de vitesse 110 px/s** pour éviter les à-coups.
   Fenêtre **4:5 (1080×1350)** : le visage est grand, format Reels.
3. **Sous-titres mot à mot** (`draw_captions`)
   chaque mot arrive sur **son** timing (jamais un découpage linéaire), 1–3 mots
   par page, montée en échelle 86 → 100 %, ombre portée, **mot actif en ambre**.
   Les bornes par défaut limitent à 3 mots / 18 caractères (règle « pas plus de
   2 lignes »).
4. **Habillage** — fond flou plein cadre (remplit le 9:16), fenêtre arrondie,
   liseré, badge kicker, marque, barre de progression segmentée, compteur de
   clip.

## Entrées acceptées

- JSON mot-à-mot : `[{"word":"...","start":1.2,"end":1.5}, …]`
- JSON segments : `[{"t0":0,"t1":3,"text":"..."}, …]` (mots répartis au prorata)
- JSON Whisper : `{"segments":[{"start":…,"words":[…]}]}`
- **SRT / VTT** : mots répartis au prorata dans chaque sous-titre

> Pour un karaoké parfait, fournir un transcript **mot-à-mot** (Whisper local
> ou export d'un outil d'alignement). Sans ça, le découpage par sous-titre
> reste régulier mais ne colle pas aux syllabes — c'est le seul compromis.

## Usage

```bash
python3 clip_engine.py --video source.mp4 --transcript words.json --list

python3 clip_engine.py --video source.mp4 --transcript words.json \
    --render-all --count 6 --brand "LÉGER" --kicker "LE CLIP" --outdir clips

# quelques clips seulement
python3 clip_engine.py ... --render-all --only 1,4,6
```

Options utiles : `--count` (nombre de clips), `--target` (durée visée, 26 s par
défaut), `--brand`, `--kicker`.

## Formats de sortie

`1080×1920` · 30 fps · H.264 CRF 21 · AAC 192 kb/s · audio normalisé
`loudnorm I=-14` (norme TikTok/Reels/Shorts).

## Coût

Environ **1,5–2 min de rendu par clip de 30 s** sur le CPU du sandbox
(détection du sujet + composition Pillow). Le fond flou est calculé une fois
toutes les 3 s, pas à chaque image.

## Limites connues

- Pas de détection de visage par réseau de neurones (modèle à télécharger
  bloqué ici) : la soustraction de fond gère bien les vidéos de plateau, moins
  bien un plan où la caméra bouge en continu.
- Pas de transcription audio locale (Whisper impossible à télécharger ici) :
  il faut fournir le transcript.
- Les coupes respectent les phrases du transcript ; si le transcript est
  approximatif, les bornes le sont aussi.
