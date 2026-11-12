# Skills « anti-slop » installés

Le problème : une vidéo motion faite par IA se reconnaît. Pas à cause d'un outil, mais à cause
d'un **vocabulaire par défaut** : sept plans de 6 s, une barre de progression, un logo en coin,
des cartes qui apparaissent en fondu, des sur-titres en capitales espacées, un mur de chiffres,
un sol qui n'existe pas. C'est ce que trois skills installés dans ce dépôt savent mesurer et corriger.

## Ce qui a été installé

| Skill | Source | Ce qu'il apporte |
|---|---|---|
| `.claude/skills/motionmaxxing/` | `Tejashmakwana/motionmaxxing` (Apache-2.0) | Direction artistique + **gates calculés** sur le rendu : `scripts/look.py` (coupes, images figées, tenue de fin, loudness, sync son/image, mouvement), `scripts/lint.mjs` (chrome d'interface), 12 lois de craft mesurées sur 53 moments pro |
| `.claude/skills/business-motion-film/` | `echris6/motion-video-kit` (MIT) | Le **Gauntlet loop** : construire ≠ juger, critique frais à chaque passe, barre de qualité, audio, offres business |
| `.claude/skills/hallmark/` | `Nutlope/hallmark` (MIT) | Le plancher de design (tokens, pas de chrome, pas de métrique inventée) + `scripts/sloplint.mjs` — références seules (les images de thème ne sont pas embarquées) |

Les 502 skills déjà présents (`animation-design-rules`, `no-ai-design-slop`,
`audit-ai-design-slop`, `cut-the-curve`, `embedded-captions`, `klik-*`, `motion-doctrine`, …)
restent la bibliothèque de référence ; ces trois-là apportent **l'exécution et la mesure**.

## Ce que la mesure a trouvé sur le film v1

`look.py` exécuté sur `digitaward-pack-1500-powerpoint-fb-9x16.mp4` :

```
cuts        6   ·  shot length mean 6.46 s  (min 4.00, max 11.00)
still       12 plages figées, dont 5.13 s, 4.97 s, 4.63 s, 3.17 s, 2.73 s
motion      mean frame-to-frame luma change 0.3/255   (humain : médiane 6.8, IQR 4.4–9.8)
audio       intégré -12.1 LUFS, crête -0.2 dBFS (au-dessus de -1 dBTP)
```

Traduction : **le film était un diaporama**. Sept plans, jusqu'à 5 s sans qu'un pixel bouge,
et un mouvement 20× sous la bande humaine. Aucun de ces défauts ne se voit en regardant une
image fixe — c'est exactement pour ça qu'il faut un script.

## Ce que la v2 change

| Défaut v1 | Correctif v2 | Résultat mesuré |
|---|---|---|
| 7 plans de 6,5 s | **29 plans, 1,56 s de moyenne** | 22 coupes détectées, moyenne 1,97 s |
| 12 plages figées (jusqu'à 5,1 s) | chaque plan a une caméra, une poussière, un grain animé | `still: no frozen stretch >= 0.6s` |
| mouvement 0,3/255 | poussée de caméra + tremblement + parallaxe | 1,3/255 (×4) |
| cartes qui apparaissent en fondu | arrivées par **masque, échelle et déplacement** | — |
| décor absent (cartes sur du vide) | **un plateau** : sol, horizon, faisceau, brume qui dérive, poussière en 3 profondeurs | — |
| logo en coin + barre de progression | supprimés (c'était du chrome, gate G5) | — |
| sol peint en disque bleu | reflet court + ombre douce + flaque de lumière | — |
| crête -0,2 dBFS | limiteur à 0,88 | **-1,1 dBFS** |
| aucun son sur les coupes | impacts sur les 16 coupes structurantes | 15/22 coupes à ±80 ms |

Les 7 prises de voix off, les 1 500 modèles, la livraison 24 h et la marque sont **inchangés** :
seule la mise en scène a changé.

## Comment rejouer le contrôle

```bash
# ffmpeg/ffprobe : le sandbox n'a que le binaire d'imageio-ffmpeg et pas ffprobe
mkdir -p /tmp/bin
ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" /tmp/bin/ffmpeg
# /tmp/bin/ffprobe : petit wrapper PyAV (paquet `av`) qui sort le JSON attendu

PATH=/tmp/bin:$PATH python3 .claude/skills/motionmaxxing/scripts/look.py \
  digitaward-ppt-pack/film/digitaward-pack-1500-powerpoint-fb-9x16-v2.mp4 \
  --out /tmp/look_v2 --expect 45.2 --expect-audio --strict
```

Sortie attendue : `G0 PASS`, `G2 PASS`, `G3 PASS`, aucune plage figée, crête sous -1 dBTP.

## La règle à retenir

> Une vidéo ne paraît pas faite par une IA parce qu'elle est mal rendue.
> Elle le paraît parce qu'elle **tient** au lieu de **bouger**, et parce qu'elle
> décore au lieu de raconter. Corriger ça, c'est couper plus court, éclairer un
> monde, et faire arriver les choses par le mouvement.

## Ce que la v4 a appris : le décor est le vrai aveu

La v3 passait tous les gates (mouvement 1,78 ; aucune plage figée ; coupes calées) et pourtant
elle « sentait » encore la machine. Le montage n'était pas en cause : **le fond l'était**.
Un dégradé parfait, une poussière régulière et un faisceau en polygone ne se rencontrent pas
dans une vraie prise de vue — l'œil les reconnaît avant de savoir pourquoi.

Correction appliquée (`build_film_v4.py`) :

1. **Plateau photographique** plutôt que calculé : le fond vient d'une image de studio
   (faisceau, brume, ligne de sol, liseré), étalonnée aux bleus de marque.
2. **Parallaxe** : le fond glisse à ~1/3 de la vitesse du sujet ; les objets ne sont plus
   « collés » à un décor immobile.
3. **Profondeur de champ** : le fond respire entre net et flou (0,18 → 0,40) au lieu d'être
   uniformément net, ce qui est la signature d'un plan tourné.
4. **Caméra à l'épaule** : deux sinus désaccordés (1,63 / 3,71 Hz) plutôt qu'un zoom linéaire.
5. **Nettoyage du plate** : le reflet rectangulaire du caisson (bords rectilignes) est fondu
   localement, puis le liseré spéculaire est réinjecté net. Sans ça, le rectangle se lit comme
   un calque collé — exactement le défaut qu'on veut éliminer.

Résultat mesuré : `motion 1,8/255` (contre 1,78 en v3), `−14,0 LUFS`, `−2,0 dBTP`,
21 coupes, plan moyen 2,05 s, **aucune plage figée**, G0/G2/G3 PASS.

**Le chiffre ne monte pas, et c'est normal.** Un décor photographique lisse produit moins de
changement de luma qu'un champ de bulles. Le gain est au rendu, pas à la métrique. Le seuil
« humain » (médiane 6,8) ne s'atteindra qu'avec du **B-roll réel**.

## Piège outillage : le repli de police silencieux

Après un reset de sandbox, `/tmp/work_cache/fonts` disparaît. `F()` retombait alors sur
`ImageFont.load_default()` (bitmap 10 px) : le film entier se rendait avec une typo cassée,
sans une ligne d'erreur. `F()` **lève maintenant `FileNotFoundError`** avec la commande
d'installation. Vérifier les polices avant tout rendu long.
