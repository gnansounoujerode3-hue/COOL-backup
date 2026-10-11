# Rockwood Method — version **premium** (9:16)

Quatrième itération du montage. Elle reprend la grammaire de film de la version
« signature » (scènes, coupes, médaillon) et **corrige ses trois défauts**, puis ajoute
ce qui manquait pour que les scènes de coupe racontent quelque chose : **les produits
sont dessinés dans l'image**.

**Film** : `film/rockwood-method-premium-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps
**29,12 s · −14,0 LUFS / −1,5 dBTP · 8,9 Mb/s · 33 Mo**
**Couverture** : `film/pinterest-cover.jpg` (1000 × 1500, format natif Pinterest)
**Sous-titres** : `subtitles/rockwood-method-premium-9x16.srt`

---

## Ce qui a été corrigé par rapport à la v3 « signature »

| Défaut v3 | Correction v4 |
|---|---|
| **Halation trop appuyée** — la peau, le t-shirt et l'écran bavaient dans un halo orange, l'image paraissait « sale » | Seuil d'halation remonté (188 au lieu de 176), dose d'additif divisée par ~1,8 (26 au lieu de 46) et mélange *screen* ramené de 0,30 à 0,17 → un débord chaud subtil qui **ajoute de la matière sans laver l'image** |
| **Le filet du « Less stress. / More savings. » traversait le texte** — on lisait une rature | Placement revu : titre 1 (y 286) → **filet (y 452)** → titre 2 (y 480). Le filet sépare, il ne barre plus |
| **Scènes de coupe vides** — un carton typographique avec un médaillon qui flottait dans du noir ; on ne voyait jamais ce qui était vendu | **Trois visuels produit dessinés à la main dans le code** (aucune image externe) et composés en haut à droite : couverture de livre, double page de planner, carte d'optimiseur |
| Flou de fouet trop long et trop large aux coupes | Durée ramenée à 0,12 s et amplitude à 15 px : la coupe se sent, ne se voit plus |
| Produits sous-titrés en doublon avec le sous-titre | Visuels descendus (y 850–900) : plus aucun chevauchement avec la ligne de sous-titre ni avec le médaillon |

## Les visuels produit (la vraie nouveauté)

| | Objet | Détail |
|---|---|---|
| **01** | **Financial Playbook** | couverture espresso, filet or, titre en Instrument Serif italique, sous-titre, **sceau doré « 01 »** — incliné de −4°, tranche de pages visible |
| **02** | **Printable Planner Bundle** | **double page ouverte** : page gauche « BUDGET » avec 7 postes de dépense lignés, page droite « PLAN » avec cases à cocher et mini-histogramme doré |
| **03** | **AI Income Optimizer** | carte anthracite à liseré bleu ardoise : libellé interlettré, **anneau de progression à 72 + score**, trois barres (income / debt / savings) |

Chacun est ombré, posé sur le fond de la scène, sous le halo d'accent — et le sujet en
médaillon cerclé d'or reste en contre-champ, en bas. La composition raconte donc :
*le produit*, *la marque*, *le visage*.

## Spécifications du film

- **Structure** : 8 scènes numérotées en running head (`01 · HOOK` → `08 · THE METHOD`),
  13 coupes alignées sur les respirations de la voix
- **Caméra** : 8 segments recadrés avec dérive lente (zoom 1,00 → 1,06)
- **3 scènes de coupe plein cadre** à 8,00 / 9,70 / 11,00 s (0,9–1,4 s chacune)
- **Sous-titres composés en Python** : montée mot à mot, pop du mot prononcé,
  or → crème, mots composés fusionnés (`100%`, `self-guided`, `rockwoodmethod.com`),
  14 séquences, 2 lignes maximum, aucun chevauchement
- **Image** : upscale Lanczos, courbe en S, colorimétrie chaude, vignettage,
  halation dosée, aberration chromatique ±2 px, grain modulé par la luminance
- **Son** : 74 BPM (Am9 → Fmaj7 → Cmaj9 → G6 → Em7), arpèges, sub, grain vinyle,
  whoosh à chaque coupe, riser, carillons de scène — **tout synthétisé, aucune licence**

## Structure

```
rockwood-method-premium/
├── BRIEF.md                 ← ce document
├── README.md                ← reconstruction pas à pas
├── tools/
│   ├── plan4.py             ← timeline : scènes, coupes, caméra, calques, produits
│   ├── assets3.py           ← génère l'habillage typographique (bandeau, titres, cartes…)
│   ├── make_products.py     ← dessine les 3 visuels produit + recompose les scènes de coupe
│   ├── captions3.py         ← sous-titres cinétiques (fusion des mots composés)
│   ├── gen_audio3.py        ← musique et SFX synthétisés
│   ├── composite4.py        ← compositor : caméra, whip, halation dosée, grain, encodage
│   ├── make_cover3.py       ← couverture Pinterest 1000 × 1500
│   └── fonts.conf           ← fontconfig local
├── assets/                  ← 35 PNG (3 visuels produit + habillage + 3 scènes de coupe)
├── audio/                   ← music3.wav, sfx3.wav, words.json (timing mot à mot)
├── film/                    ← film final + couverture
└── subtitles/               ← SRT
```

## Les quatre versions

| | Dossier | Ce qui la définit |
|---|---|---|
| v1 | `../rockwood-method/` | premier montage : cartes à cadre empilées, 84 BPM |
| v2 | `../rockwood-method-editorial/` | système typographique à filets, 7 segments caméra, musics 78 BPM |
| v3 | `../rockwood-method-signature/` | grammaire de film : 8 scènes, coupes, médaillon, halation |
| **v4** | **`../rockwood-method-premium/`** | **halation dosée + scènes de coupe habillées par leurs produits** |

## À confirmer avant publication

- `rockwoodmethod.com/shop` est déduit de la prononciation (« …com shop »).
- La personne à l'écran n'est pas nommée : le film reste sur « The Rockwood Method ».
- Les visuels produit sont des **illustrations** (aucune photo de produit fournie) :
  si des visuels officiels existent, il suffit de remplacer les trois PNG dans `assets/`.
