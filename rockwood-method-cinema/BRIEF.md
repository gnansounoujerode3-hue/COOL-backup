# Rockwood Method — version **cinéma** (9:16)

Cinquième itération du montage. Elle part d'un constat sur la v4 « premium » :
ses scènes de coupe et sa carte finale étaient **des aplats noirs**. Diagnostic :
les PNG `cutaway_*.png` et `endcard.png` livrés avec la v4 portent un fond noir
**opaque** incrusté (plus de 99 % de pixels opaques) — le carton peint recouvrait
donc toute l'image au lieu de se poser dessus.

La v5 abandonne les cartons. Les fonds sont **fabriqués à partir de l'image du film
elle-même**, et l'habillage n'est plus que du texte transparent.

**Film** : `film/rockwood-method-cinema-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps
**29,12 s · −14,0 LUFS / −1,5 dBTP · 9,2 Mb/s · 33 Mo**
**Couverture** : `film/pinterest-cover.jpg` (1000 × 1500, format natif Pinterest)
**Sous-titres** : `subtitles/rockwood-method-cinema-9x16.srt`

---

## Ce qui a été corrigé par rapport à la v4 « premium »

| Défaut v4 | Correction v5 |
|---|---|
| **Scènes de coupe = aplats noirs.** Les trois scènes (Playbook, Planner, Optimizer) étaient posées sur un fond noir opaque : plus de matière, plus de lumière, la vidéo « s'éteignait » trois fois | **Le fond est reconstruit depuis le plan** (`cine_bg()`) : image réduite ÷7 → flou 26 → miroir vertical 22 % → bokeh doré → vignettage → voile + lumière haut-droite. On garde la carnation, le bois, le cuir et la lumière de la prise : la coupe devient un **plan de coupe**, pas un carton |
| **Carte finale « dans la boîte »** — même cause | **Carte finale = plan large flouté** (même recette) + typographie serif pleine largeur + pilule d'appel et mention *link in bio* |
| **Type illisible sur les zones claires** — à 9,9 s le titre « Printable Bundle » se perdait dans le portable et la chemise | **Plaques de lisibilité** (`make_plate()`) : rectangle arrondi (rayon 34 %) calé sur l'encre du bloc, flouté à 94 px, fond espresso ~45 % au cœur, **disparition totale sur les bords** (canevas élargi de 3 × le flou pour que le dégradé ne soit jamais coupé) |
| **Compteur désynchronisé du sous-titre** : à 18,4 s on lisait « 100 % self-guided » sous un compteur encore à 98 % | Compteur recalé : 0 → 100 % en **0,80 s** (17,14 → 17,94 s). Le chiffre est à 100 % avant que la voix ne dise « 100 % » |
| Mention *link in bio* en gris dans la pilule dorée | Reposée proprement sous la pilule, dans la couleur de la charte |
| Visuels produit détourés à la main dans du noir | Les mêmes visuels, mais **posés dans la lumière chaude** du fond reconstruit, avec ombre douce |

## La recette des fonds (le cœur de la v5)

```
plan étalonné 1080 x 1920
        ↓ réduction ÷7 puis agrandissement (le flou devient une matière, pas un lissage)
flou gaussien 26
        ↓ miroir vertical des 22 % supérieurs (le fond « répond » au sujet)
bokeh doré #e9bd7c en haut à droite
        ↓ vignettage + voile espresso dégradé
lumière d'appoint, puis le bloc typographique transparent + sa plaque
```

Résultat : chaque scène de coupe a **son** fond (celui du moment qu'elle interrompt),
et la carte finale garde le visage en flou profond sous la typographie.

## Spécifications du film

- **Structure** : 8 scènes numérotées en running head (`01 · HOOK` → `08 · THE METHOD`),
  13 coupes alignées sur les respirations de la voix
- **Caméra** : 8 segments recadrés avec dérive lente (zoom 1,00 → 1,06)
- **3 scènes de coupe plein cadre** à 8,00 / 9,70 / 11,00 s, fond reconstruit,
  médaillon du sujet cerclé d'or, visuel produit flottant, souffle de zoom lent
- **2 plaques surlignées** (« The Rockwood Method » 3,95 s, « Rock solid. » 13,70 s)
  posées sur leur plaque fondue
- **Carte finale** 25,85 → 29,10 s : plan large flouté, serif pleine largeur, pilule d'appel
- **Sous-titres composés en Python** : montée mot à mot, pop du mot prononcé,
  or → crème, mots composés fusionnés (`100%`, `self-guided`, `rockwoodmethod.com`),
  2 lignes maximum, aucun chevauchement
- **Image** : upscale Lanczos, courbe en S, colorimétrie chaude, vignettage,
  halation dosée (seuil 188, dose 26), aberration chromatique ±2 px, grain modulé
- **Son** : 74 BPM (Am9 → Fmaj7 → Cmaj9 → G6 → Em7), arpèges, sub, grain vinyle,
  whoosh à chaque coupe, riser, carillons — **tout synthétisé, aucune licence** ;
  voix d'origine conservée, chaîne de mixage → −14,0 LUFS / −1,5 dBTP

## Structure

```
rockwood-method-cinema/
├── BRIEF.md                 ← ce document
├── README.md                ← reconstruction pas à pas
├── tools/
│   ├── plan4.py             ← timeline : scènes, coupes, caméra, calques, produits
│   ├── plan3.py             ← alias (les outils v5 importent `plan4`)
│   ├── make_cine_assets.py  ← blocs typographiques TRANSPARENTS (cut01-03, endtype)
│   ├── composite5.py        ← compositor v5 : fonds reconstruits, plaques, carte finale
│   ├── make_cover5.py       ← couverture Pinterest 1000 × 1500
│   ├── assets3.py           ← habillage de base (bandeau, cartes, surlignés, pilule…)
│   ├── make_products.py     ← dessine les 3 visuels produit
│   ├── captions3.py         ← sous-titres cinétiques
│   ├── gen_audio3.py        ← musique et SFX synthétisés
│   └── fonts.conf           ← fontconfig local
├── assets/                  ← 32 PNG transparents (habillage + 3 blocs de coupe + carte finale)
├── audio/                   ← music3.wav, sfx3.wav, mix3.wav (−14 LUFS), words.json
├── film/                    ← film final + couverture
└── subtitles/               ← SRT
```

## Les cinq versions

| | Dossier | Ce qui la définit |
|---|---|---|
| v1 | `../rockwood-method/` | premier montage : cartes à cadre empilées, 84 BPM |
| v2 | `../rockwood-method-editorial/` | système typographique à filets, 7 segments caméra, musique 78 BPM |
| v3 | `../rockwood-method-signature/` | grammaire de film : 8 scènes, coupes, médaillon, halation |
| v4 | `../rockwood-method-premium/` | halation dosée + scènes de coupe habillées par leurs produits |
| **v5** | **`../rockwood-method-cinema/`** | **fonds reconstruits depuis le film, plaques de lisibilité, carte finale à plat large** |

## À confirmer avant publication

- `rockwoodmethod.com/shop` est déduit de la prononciation (« …com shop »).
- La personne à l'écran n'est pas nommée : le film reste sur « The Rockwood Method ».
- Les visuels produit sont des **illustrations** dessinées en code (aucune photo fournie) :
  remplacer les PNG `assets/prod_*.png` suffit à les actualiser.
