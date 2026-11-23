# DISCIPLINE — « La discipline bat la motivation »

`film/discipline-bat-la-motivation-9x16.mp4`
`1080 × 1920` · `30 fps` · **`56,40 s`** · voix off FR (`voice-04`) + musique + SFX

Commande : *« une vidéo composée de plusieurs vidéos, images, GIF, motion design
recherchés sur le net, montée de façon cohérente avec une voix off sur la
discipline — chaque groupe de mots ou phrase doit être animé »*.

## Matière

| type | source |
|---|---|
| 16 photos | recherche d'images web (voir `assets/photos/SOURCES.md`) |
| 1 GIF | boucle de pluie sur vitre (Giphy), 12 fps, surimpression colorisée |
| motion design | 100 % généré (Pillow + numpy) : compteurs, grilles, barres, molette |
| graphisme | Space Grotesk / Instrument Serif italique / Inter, ambre `#ff7a2e` |

Aucun rush du dépôt n'est utilisé. Les deux images comportant un filigrane
(`dreamstime` lisible) ont été écartées après contrôle visuel.

## Découpage (8 plans, coupes sur la voix)

| # | intervalle | visuel | texte animé |
|---|---|---|---|
| 1 | 0,00 – 8,40 | passage piéton, petit matin | « La motivation *va et vient.* » + compteur **1/3** |
| 2 | 8,40 – 18,60 | bureau de nuit + GIF pluie | « Une décision que tu répètes *quand personne ne regarde.* » |
| 3 | 18,60 – 28,40 | motion design pur (poids flouté) | « Tu ne gagnes pas avec de la volonté. » + 3 règles |
| 4 | 28,40 – 37,40 | course dans le brouillard | « Chaque jour où tu tiens… » + grille **J+1 → J+30** |
| 5 | 37,40 – 44,00 | barre au sol | « …de répétitions. » + compteur ×1 ×3 ×7 ×14 ×30 |
| 6 | 44,00 – 52,40 | carnet à la bougie | checklist qui se coche, bloc « la seule promesse » |
| 7 | 52,40 – 56,40 | route au brouillard | carton final « La discipline *bat la motivation.* » |

## Animation du texte (exigence « chaque groupe de mots animé »)

- `words_in()` : chaque mot entre par **masque vertical** + montée, décalage 40–80 ms ;
- `big_line()` / `amber_serif()` : les mots-clés en Instrument Serif italique ambre,
  révélés dans la même ligne que le grotesk ;
- transitions : **whip-pan** (flou directionnel) + flash ambre 2 images à chaque coupe ;
- motion design synchronisé sur le sens : les 3 cases se remplissent, la grille
  J+1→J+30 se remplit en 1,5 s, les 5 barres de répétitions montent en escalier,
  les coches tombent sur les temps de la voix.

## Audio

Voix off calée à `0,55 / 8,75 / 18,85 / 28,65 / 37,60 / 44,20 s` (écart ≥ 1,2 s,
aucun chevauchement), lit musical 92 BPM (nappe + pulsation + shimmer) ducké de
14 dB sous la voix, whoosh sur chaque coupe, ticks sur les cases et les coches.
**−14,1 LUFS / −3,5 dBTP**.

```bash
python3 scripts/build_discipline.py --preview /tmp/p.jpg
python3 scripts/build_discipline.py --audio-only
python3 scripts/build_discipline.py
```
