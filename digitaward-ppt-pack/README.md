# Digitaward — Pack 1 500 modèles PowerPoint · Pub Facebook 9:16

Film publicitaire vertical (Reels / Stories) pour la **prévente** du pack de 1 500 modèles
PowerPoint de Digitaward.

**Livrable** — `film/digitaward-pack-1500-powerpoint-fb-9x16.mp4`
1080 × 1920 · 30 fps · **45,20 s** · h264 High / AAC 48 kHz stéréo · ~6,8 MB
Audio : moyenne **−14,2 dBFS**, crête **−0,2 dBFS** (norme plateformes −14 LUFS).

## Conçu à partir des visuels fournis

Palette mesurée sur les maquettes (aucune couleur inventée) :

| Rôle | Hex |
| --- | --- |
| Fond navy | `#001070` |
| Royal | `#0030D0` |
| Royal clair | `#0040E0` |
| Jaune accent | `#FFC21A` |
| Jaune profond | `#FFB817` |
| Orange PowerPoint | `#D24726` |
| Glace / texte secondaire | `#E8F0FF` / `#B0C2F0` |

Typo : **Poppins** 800/700/600 (titres, chiffres) + **Manrope** 700/600 (corps).
Motifs repris du visuel : vagues lumineuses, grille de points, cartes de diapositives
flottantes, carte logo blanche, CTA pilule jaune avec icône de téléchargement.

## Découpage (8 scènes)

| # | Scène | Temps | Rôle | Voix off |
| --- | --- | --- | --- | --- |
| 1 | Hook | 0,00 – 6,60 | « 3 heures perdues. » + brouillon gris | « Tu ouvres PowerPoint. Trois heures plus tard… » |
| 2 | Pain | 6,60 – 12,80 | slides qui s'empilent + chrono 3 h 12 | « Couleurs, textes, images : tu passes des heures… » |
| 3 | Turn | 12,80 – 17,60 | « Et si… » + 3 atouts + bandeau chiffres | « Et si tu pouvais obtenir un rendu professionnel… » |
| 4 | Reveal | 17,60 – 24,80 | pack 3D + compteur 1 500 + 3 preuves | « Le pack Digitaward : 1 500 modèles… » |
| 5 | Slides | 24,80 – 31,40 | 4 vraies captures + tags d'usage | « Exposé, soutenance, formation, réunion… » |
| 6 | Bénéfice | 31,40 – 35,60 | « Moins de temps à concevoir. » | « Moins de temps à concevoir. Plus de temps pour convaincre. » |
| 7 | Offre | 35,60 – 41,20 | prévente, carte livraison 24 h, 4 bénéfices, CTA | « Commande ton pack dès maintenant. Livraison sous 24 h… » |
| 8 | End card | 41,20 – 45,20 | logo, pack, CTA, marque | (musique seule) |

Rythme : 122 BPM, ducking de la musique à ×0,62 sous la voix, whoosh à chaque transition,
ding sur les deux temps forts (offre + CTA final).

## Conformité à l'offre

Aucun prix, remise, témoignage, note ou chiffre inventé. Seules les promesses fournies sont
affichées : **1 500 modèles**, **animés**, **100 % modifiables**, **15 styles**, **livraison
sous 24 h après confirmation**, marque **« Digitaward · Le savoir à portée de clic. »**

## Régénérer

```bash
# planche de contrôle (8 scènes)
python3 digitaward-ppt-pack/scripts/build_film.py --preview /tmp/preview.jpg

# audio seul + mesure
python3 digitaward-ppt-pack/scripts/build_film.py --audio-only

# rendu complet (≈ 1 min 40)
python3 digitaward-ppt-pack/scripts/build_film.py
```

Prérequis : `poppins` + `manrope` dans `/tmp/work_cache/fonts/node_modules/@expo-google-fonts/`,
`Pillow`, `numpy`, `imageio-ffmpeg`.

## Assets

- `assets/img/box.png` — pack détouré (fond du visuel retiré au masque de luminance + composante connexe).
- `assets/img/slide_*.png` — vraies diapositives recadrées depuis la maquette fournie (inclinées, assumées).
- `assets/img/logo_raw.png` — logo ; **toujours posé sur une carte blanche** (le wordmark est blanc).
- `assets/audio/vo1…vo7.mp3` — 7 prises de voix off FR, coupées puis remises au tempo.


---

# v2 — version anti-slop (pilotée par les skills)

`film/digitaward-pack-1500-powerpoint-fb-9x16-v2.mp4` — 1080×1920 · 30 fps · **45,20 s** ·
18,9 Mo · intégré **−14,1 LUFS**, crête **−2,1 dBFS**, LRA 2,6 LU.

La v1 est conservée intacte. La v2 raconte la même offre avec une mise en scène différente.

## Mesure avant / après

Le contrôle est fait par `.claude/skills/motionmaxxing/scripts/look.py` (gates calculés sur le
rendu, pas sur le code) :

| | v1 | v2 |
|---|---|---|
| coupes détectées | 6 | **22** |
| durée moyenne d'un plan | 6,46 s | **1,97 s** |
| plages figées ≥ 0,6 s | **12** (jusqu'à 5,13 s) | **0** |
| mouvement (Δ luma / image) | 0,33 | **1,39** |
| crête audio | −0,2 dBFS (rouge) | **−2,1 dBFS** |
| coupes synchronisées au son | 4/6 | **15/22** |
| G0 / G2 / G3 | pass / pass / pass | pass / pass / pass |

`G0` décodage + durée + piste son · `G2` aucune image vide · `G3` tenue de fin ≤ 1,4 s.

## Ce qui a changé

1. **Un plateau, pas un fond.** Sol avec ligne d'horizon, flaque de lumière, faisceau
   volumétrique, brume qui dérive, poussière en trois profondeurs, grain animé.
2. **29 plans au lieu de 8.** 1,56 s en moyenne : macro de diapo → ordinateur dans la pénombre →
   time-lapse d'horloge → sélecteur de couleur → image posée de travers → tas de brouillons →
   allumage du pack → macro → pack héro → **les diapos sortent de derrière le pack** →
   travelling → 4 usages → 4 extraits → minuterie qui rembobine → pack qui se referme sur les
   diapos → projection murale → tampon **LIVRAISON 24 H** → macro des preuves → CTA pressé →
   burst → marque → fin.
3. **Aucun chrome.** Plus de logo en coin, plus de barre de progression, plus de sur-titre en
   capitales espacées, plus de mur de chiffres (gate G5).
4. **Arrivées par mouvement.** Masque + échelle + déplacement ; les fondus ne servent plus
   qu'à des objets isolés.
5. **Audio recolé aux nouvelles coupes** : impacts sur 16 coupes structurantes, whooshs courts,
   clic du curseur, tampon, bouton pressé ; voix off et promesses inchangées.

## Régénérer

```bash
python3 digitaward-ppt-pack/scripts/build_film_v2.py --preview /tmp/preview-v2.jpg
python3 digitaward-ppt-pack/scripts/build_film_v2.py --audio-only
python3 digitaward-ppt-pack/scripts/build_film_v2.py
```

Le rendu direct pèse 37 Mo ; la livraison est réencodée en CRF 21 + limiteur (18,9 Mo).

## Contrôle

```bash
PATH=/tmp/bin:$PATH python3 .claude/skills/motionmaxxing/scripts/look.py \
  digitaward-ppt-pack/film/digitaward-pack-1500-powerpoint-fb-9x16-v2.mp4 \
  --out /tmp/look --expect 45.2 --expect-audio --strict
```

Détail des skills installés et de la méthode : `.claude/ANTI-SLOP.md`.


---

# v3 — le plan qui manquait

`film/digitaward-pack-1500-powerpoint-fb-9x16-v3.mp4` — 1080×1920 · 30 fps · **45,20 s** ·
22,8 Mo · intégré **−14,0 LUFS**, crête **−2,0 dBFS**, LRA 2,6 LU · 21 coupes · plan moyen 2,05 s.

La v2 racontait l'offre mais **laissait la phrase clé sans images** : « Moins de temps à
concevoir. Plus de temps pour convaincre. » était dite en voix off par-dessus des captures de
diapositives. C'est le genre de raccord qu'on « sent » sans savoir le nommer — la promesse la plus
forte du film n'avait rien à regarder.

## Ce que la v3 change

| | v2 | v3 |
|---|---|---|
| plans | 29 (dont 2 redondants) | **28**, deux plans morts supprimés |
| plan « bénéfice » | absent | **présent (30,8 → 33,9 s)**, mot à mot |
| mouvement (Δ luma) | 1,39 | **1,78** |
| plage quasi-figée la plus longue | 0,80 s | **0,30 s** |
| images noires | 0 | **0** |
| G0 / G2 / G3 | pass | **pass** |
| loudness | −14,1 LUFS | **−14,0 LUFS** |

Le plan bénéfice est en typographie cinétique : les quatre groupes arrivent sur les temps de la
voix (122 BPM ≈ 0,49 s), montent de 56 px sous un masque, puis un trait jaune se dessine et le
pack se pose en bas — la phrase se termine par le produit.

Ajouts techniques : respiration de lumière sur chaque temps, nappe lumineuse qui balaie le cadre
sur quatre temps, et flou directionnel de 7 images sur les sept coupes structurantes (le cadre est
encore en mouvement quand la coupe tombe).

## Régénérer

```bash
python3 digitaward-ppt-pack/scripts/build_film_v3.py --preview /tmp/preview-v3.jpg
python3 digitaward-ppt-pack/scripts/build_film_v3.py --audio-only
python3 digitaward-ppt-pack/scripts/build_film_v3.py   # rendu + livraison CRF 21
```

## Contrôle

```bash
PATH=/tmp/bin:$PATH python3 .claude/skills/motionmaxxing/scripts/look.py \
  digitaward-ppt-pack/film/digitaward-pack-1500-powerpoint-fb-9x16-v3.mp4 \
  --out /tmp/look_v3 --expect 45.2 --expect-audio --strict
```

## Limite assumée

Le mouvement mesuré (1,78) reste sous la bande des films humains (médiane 6,8). La raison est
structurelle : la moitié du film est composée de plans produit sur fond tenu. Pour franchir ce
seuil il faut du **B-roll réel** (mains sur clavier, écran filmé, salle, téléphone) — pas plus
d'effets. C'est le prochain ingrédient, pas un correctif de code.


---

# v4 — le décor, pas le montage

`film/digitaward-pack-1500-powerpoint-fb-9x16-v4.mp4` — 1080×1920 · 30 fps · **45,2 s** ·
22,8 Mo · intégré **−14,0 LUFS**, crête **−2,0 dBFS**, LRA 2,6 LU · 21 coupes ·
plan moyen 2,05 s · mouvement **1,8 / 255**.

La v3 avait corrigé le rythme. Restait le vrai aveu : le **fond**. Un dégradé parfait, une
poussière régulière, un faisceau en polygone — c'est ça qu'on reconnaît comme « fait par IA »,
pas le montage. La v4 garde le découpage et les compositions de la v3, et remplace le décor
par un **plateau photographique** (`assets/img/plate_studio.jpg`) : vrai faisceau volumétrique,
vraie brume, vraie ligne de sol, liseré chaud.

| | v3 | v4 |
|---|---|---|
| plans | 28 | **28 (identiques)** |
| décor | dégradé calculé + poussière | **photo de studio étalonnée** |
| parallaxe | — | **sujet ≈ 3× plus mobile que le fond** |
| profondeur de champ | — | **flou de fond qui respire (0,18 → 0,40)** |
| caméra | zoom calculé | **tremblement main 3,2 px + dérive** |
| mouvement mesuré | 1,78 | **1,8** |
| G0 / G2 / G3 | pass | **pass** |

## Ce qui est mesuré, sans se flatter

Le mouvement est **stable** (1,78 → 1,8) : le décor ne fabrique pas de mouvement, il fabrique de
la crédibilité. On ne gagne donc pas au chiffre, on gagne au rendu. Le seuil
« humain » (médiane 6,8) ne bougera qu'avec du **B-roll réel** — mains sur clavier, écran filmé,
salle — et il n'y en a pas dans ce dépôt pour Digitaward.

## Détail du pipeline

- `_load_plate()` recadre la photo pour poser la ligne de sol vers **74 %** de la hauteur,
  désature à 55 %, recompose la teinte avec le dégradé de marque (`#001070` → `#0030B0`),
  utilise le faisceau photo comme source lumineuse (mode écran), puis corrige en S.
- Le reflet rectangulaire du caisson sur le plateau est **fondu localement** (flou masqué)
  et le liseré spéculaire est réinjecté net — sinon il se lit comme un rectangle collé.
- `stage_frame()` fait glisser le fond moins vite que le sujet, fait respirer le flou de
  profondeur de champ et laisse dériver le faisceau (`sin(t*0,21)`).
- `camera()` ajoute deux sinus désaccordés (`1,63` / `3,71 Hz`) : la caméra n'est jamais
  parfaitement stable, comme à l'épaule.
- Le grain, le vignettage et l'étalonnage restent dans `finish()` (v2), appliqués en dernier.

## Régénérer

```bash
python3 digitaward-ppt-pack/scripts/build_film_v4.py --preview /tmp/preview-v4.jpg
python3 digitaward-ppt-pack/scripts/build_film_v4.py --audio-only
python3 digitaward-ppt-pack/scripts/build_film_v4.py   # rendu + livraison CRF 21
```

`F()` (dans `build_film.py`) **échoue maintenant explicitement** si Poppins/Manrope manquent :
un repli silencieux vers la bitmap 10 px avait produit un rendu entier avec une typo cassée,
invisible dans les logs et évidente seulement à l'image.

## Contrôle

```bash
PATH=/tmp/bin:$PATH python3 .claude/skills/motionmaxxing/scripts/look.py \
  digitaward-ppt-pack/film/digitaward-pack-1500-powerpoint-fb-9x16-v4.mp4 \
  --out /tmp/look_v4 --expect 45.2 --expect-audio --strict
```
