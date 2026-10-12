# Rockwood Method — version **motion** (9:16)

Septième itération. Elle ne touche ni à l'image ni au son : elle met le **mouvement**
au niveau motion design. Tout ce qui entre à l'écran est désormais *orchestré* —
courbe choisie, retard calculé, distance proportionnelle, couche assignée.

**Film** : `film/rockwood-method-motion-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps
**29,12 s · −14,0 LUFS / −1,5 dBTP · 9,0 Mb/s · 33 Mo**
**Couverture** : `film/pinterest-cover.jpg` (1000 × 1500, format natif Pinterest)
**Sous-titres** : `subtitles/rockwood-method-motion-9x16.srt`

---

## D'où viennent les règles appliquées

Le travail s'appuie sur la bibliothèque de ressources motion design partagée par
l'utilisateur (Notion « RESSOURCES GRAPHIQUES » — Romain Guillon), et sur deux
prolongements trouvés en ligne : le guide **Jitter « Better Motion »** (staggering,
easing, rythme) et le **motion-design-skill** publié par LottieFiles (tables de
durées, courbes de référence, budget d'overshoot, règles de chorégraphie).

Ce qui a été retenu et appliqué :

| Principe | Règle de référence | Application dans le film |
|---|---|---|
| **Courbes réelles** | jamais de linéaire sur un déplacement ; `ease-out` pour entrer, `ease-in` pour sortir | `bezier()` évalue de vraies cubic-bezier : entrées `(0.16, 1, 0.30, 1)`, déplacements à l'écran `(0.40, 0, 0.20, 1)`, sorties `(0.55, 0, 1, 0.45)` |
| **Sortie plus rapide que l'entrée** | ratio 65-75 % | `EXIT_RATIO = 0.68` sur tous les calques |
| **Orchestration (stagger)** | 50-100 ms entre éléments d'un même groupe, total < 500 ms | scope 0 / 90 / 190 / 261 ms : le kicker annonce, le titre prend la scène, le filet souligne, la légende suit |
| **Suivi (follow-through)** | l'élément secondaire retarde de 50-150 ms | le visuel produit arrive à +306 ms, le médaillon à +216 ms — jamais avec le texte |
| **Durée proportionnelle à la distance** | 50 px = 0,8× · plein cadre = 1,8-2,0× | 26 px de course pour un micro-élément (0,42 s), 44 px pour un bloc héro (0,62 s), push-in plein cadre sur 3,25 s |
| **Trois couches** | primaire + secondaire + ambiante (10-20 % d'amplitude) | primaire : le texte · secondaire : fond reconstruit, produit, médaillon · ambiante : 14 poussières dorées en suspension et le rail de pellicule fixe |
| **Anticipation** | 100-200 ms de « wind-up », 10-20 % de l'amplitude | la caméra pousse de 1 % avant chaque coupe (`cut_kick()`) puis se pose |
| **Budget d'overshoot** | premium : 0 % ; légèrement plus sur les pastilles | 0 % sur le texte, ~3 % sur la pastille dorée, ressort du compteur ramené de 95 % à 45 % |
| **Staging** | un héros par temps fort | la plaque fondue se pose avant la première ligne de texte (+60 ms) |
| **Rythme** | 100-200 ms de respiration entre deux temps | 100 ms de temps mort avant que la scène de coupe ne parle |
| **Arcs** | 10-20 px de décalage perpendiculaire sur un déplacement long | conservé là où il existait (montées en douceur), pas ajouté artificiellement |

## Ce qui change par rapport à la v6 « cinéma + »

| | Avant (v6) | Maintenant (v7) |
|---|---|---|
| Blocs de scène | un seul PNG posé, tout à la fois | 4 parties (`_a` kicker, `_b` titre, `_c` filet, `_d` légende) sur le même canevas, entrée en cascade |
| Carte finale | idem, arrivée d'un bloc | même cascade, avec le titre en 0,70 s |
| Courbes | `1-(1-x)³` partout | 4 courbes distinctes selon la fonction (entrée / écran / sortie / overshoot) |
| Caméra | mouvement lent continu | + anticipation de 1 % avant chaque coupe |
| Ambiance | aucune | poussières dorées (14, 10-30 px/s, opacité 20-50 %) + rail de pellicule fixe avec tick à 100 Hz rendant lisibles les 25 images/s |
| Compteur | ressort de 95 % | ressort de 45 % (« premium », pas « playful ») |
| Carte finale | push-in 5,8 % | 7,5 % + dérive 26 px |

## Spécifications du film

- **Structure** : 8 scènes numérotées en running head (`01 · HOOK` → `08 · THE METHOD`),
  13 coupes alignées sur les respirations de la voix
- **Caméra** : 8 segments (zoom 1,00 → 1,06) + caméra portée + anticipation aux coupes
- **3 scènes de coupe** à 8,00 / 9,70 / 11,00 s : fond reconstruit depuis le plan,
  médaillon du sujet cerclé d'or, visuel produit, fuite de lumière à l'entrée
- **2 plaques surlignées**, **beat 100 %** (17,10 → 19,50 s), **carte finale** 25,85 → 29,10 s
- **Sous-titres** : montée mot à mot, pop du mot prononcé, or → crème, 2 lignes maximum
- **Image** : upscale Lanczos, courbe en S, colorimétrie chaude, vignettage, halation
  dosée, aberration chromatique ±2 px, grain modulé par la luminance
- **Son** : 74 BPM (Am9 → Fmaj7 → Cmaj9 → G6 → Em7), arpèges, sub, grain vinyle,
  whoosh à chaque coupe — **tout synthétisé, aucune licence** ; voix d'origine
  conservée, chaîne de mixage → −14,0 LUFS / −1,5 dBTP

## Structure

```
rockwood-method-motion/
├── BRIEF.md                 ← ce document
├── README.md                ← reconstruction pas à pas
├── tools/
│   ├── plan4.py             ← timeline : scènes, coupes, caméra, calques, produits
│   ├── plan3.py             ← alias (les outils importent `plan4`)
│   ├── composite7.py        ← compositor v7 : courbes, cascades, couches, anticipation
│   ├── make_cine_assets7.py ← blocs typographiques découpés en parties animables
│   ├── make_cover7.py       ← couverture Pinterest 1000 × 1500
│   ├── assets3.py           ← habillage de base (bandeau, cartes, surlignés, pilule…)
│   ├── make_products.py     ← dessine les 3 visuels produit
│   ├── captions3.py         ← sous-titres cinétiques
│   ├── gen_audio3.py        ← musique et SFX synthétisés
│   └── fonts.conf           ← fontconfig local
├── assets/                  ← 52 PNG transparents (dont 16 parties animables)
├── audio/                   ← music3.wav, sfx3.wav, mix3.wav (−14 LUFS), words.json
├── film/                    ← film final + couverture
└── subtitles/               ← SRT
```

## Les sept versions

| | Dossier | Ce qui la définit |
|---|---|---|
| v1 | `../rockwood-method/` | premier montage : cartes à cadre empilées, 84 BPM |
| v2 | `../rockwood-method-editorial/` | système typographique à filets, 7 segments caméra |
| v3 | `../rockwood-method-signature/` | grammaire de film : 8 scènes, coupes, médaillon, halation |
| v4 | `../rockwood-method-premium/` | halation dosée + scènes de coupe habillées par leurs produits |
| v5 | `../rockwood-method-cinema/` | fonds reconstruits depuis le film, plaques de lisibilité, carte finale à plat large |
| v6 | `../rockwood-method-cinema-plus/` | caméra portée, fuites de lumière, beat kinétique du 100 %, push-in final |
| **v7** | **`../rockwood-method-motion/`** | **courbes réelles, entrées en cascade, trois couches, anticipation : le mouvement comme discipline** |

## À confirmer avant publication

- `rockwoodmethod.com/shop` est déduit de la prononciation (« …com shop »).
- La personne à l'écran n'est pas nommée : le film reste sur « The Rockwood Method ».
- Les visuels produit sont des **illustrations** dessinées en code (aucune photo fournie).
