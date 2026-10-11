# Rockwood Method — version **cinéma +** (9:16)

Sixième itération. La v5 avait réglé la matière (fonds reconstruits depuis le plan,
plaques de lisibilité) ; celle-ci s'occupe du **mouvement et du rythme** — ce qui
sépare un montage posé sur un trépied virtuel d'un montage qui respire.

**Film** : `film/rockwood-method-cinema-plus-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps
**29,12 s · −14,0 LUFS / −1,5 dBTP · 8,9 Mb/s · 33 Mo**
**Couverture** : `film/pinterest-cover.jpg` (1000 × 1500, format natif Pinterest)
**Sous-titres** : `subtitles/rockwood-method-cinema-plus-9x16.srt`

---

## Ce qui a été ajouté par rapport à la v5 « cinéma »

| Ajout | Détail |
|---|---|
| **Caméra portée** | Micro-mouvements organiques sur **toute** l'image : deux sinusoïdes incommensurables (≈ 0,3 Hz et 0,1 Hz) donnent ±5,6 px de dérive, plus une rotation de ±0,11°. Appliqué à l'image **seule** — l'habillage, les plaques et les sous-titres restent nets et stables. C'est le contraste entre un plan qui bouge et une typo qui ne bouge pas qui « fait film » |
| **Fuites de lumière aux coupes** | Flash chaud diffus (cœur + traînée anamorphique) de 0,16 s aux entrées de coupe (8,00 / 9,70 / 11,00 / 12,00 s) et à l'entrée de la carte finale, monté **sur** le fouet de coupe existant : la coupe se sent avant de se voir |
| **Beat kinétique du 100 %** | Le chiffre arrive à **1,95× sa taille** puis converge sur sa position finale en ressort amorti (`e^(−6,2t)·cos(8,4t)`), pendant que le compteur court jusqu'à 100 % en 0,80 s. Au verrouillage, un **halo doré** s'allume derrière le chiffre — le sous-titre « 100 % self-guided » tombe exactement sur la fin du ressort |
| **Push-in de la carte finale** | Zoom final porté de 3 % à **5,8 %** avec une dérive verticale de 18 px vers le visage : la carte n'est plus un fond, c'est un plan qui avance |
| **Fonds de coupe plus respirants** | Souffle de zoom des scènes de coupe passé de 2,2 % à **3,4 %** sur leur durée |

## Spécifications du film

- **Structure** : 8 scènes numérotées en running head (`01 · HOOK` → `08 · THE METHOD`),
  13 coupes alignées sur les respirations de la voix
- **Caméra** : 8 segments recadrés avec dérive lente (zoom 1,00 → 1,06) **+ caméra portée**
- **3 scènes de coupe plein cadre** à 8,00 / 9,70 / 11,00 s : fond reconstruit depuis le
  plan, médaillon du sujet cerclé d'or, visuel produit flottant, fuite de lumière à l'entrée
- **2 plaques surlignées** (« The Rockwood Method » 3,95 s, « Rock solid. » 13,70 s)
- **Beat 100 %** 17,10 → 19,50 s (compteur + halo)
- **Carte finale** 25,85 → 29,10 s : plan large flouté, push-in, serif pleine largeur, pilule d'appel
- **Sous-titres composés en Python** : montée mot à mot, pop du mot prononcé,
  or → crème, mots composés fusionnés (`100%`, `self-guided`, `rockwoodmethod.com`)
- **Image** : upscale Lanczos, courbe en S, colorimétrie chaude, vignettage,
  halation dosée (seuil 188, dose 26), aberration chromatique ±2 px, grain modulé
- **Son** : 74 BPM (Am9 → Fmaj7 → Cmaj9 → G6 → Em7), arpèges, sub, grain vinyle,
  whoosh à chaque coupe, riser, carillons — **tout synthétisé, aucune licence** ;
  voix d'origine conservée, chaîne de mixage → −14,0 LUFS / −1,5 dBTP

## Structure

```
rockwood-method-cinema-plus/
├── BRIEF.md                 ← ce document
├── README.md                ← reconstruction pas à pas
├── tools/
│   ├── plan4.py             ← timeline : scènes, coupes, caméra, calques, produits
│   ├── plan3.py             ← alias (les outils v6 importent `plan4`)
│   ├── composite6.py        ← compositor v6 : caméra portée, fuites, beat 100 %, carte finale
│   ├── make_cover5.py       ← couverture Pinterest 1000 × 1500
│   ├── make_cine_assets.py  ← blocs typographiques transparents (cut01-03, endtype)
│   ├── assets3.py           ← habillage de base (bandeau, cartes, surlignés, pilule…)
│   ├── make_products.py     ← dessine les 3 visuels produit
│   ├── captions3.py         ← sous-titres cinétiques
│   ├── gen_audio3.py        ← musique et SFX synthétisés
│   └── fonts.conf           ← fontconfig local
├── assets/                  ← 36 PNG transparents
├── audio/                   ← music3.wav, sfx3.wav, mix3.wav (−14 LUFS), words.json
├── film/                    ← film final + couverture
└── subtitles/               ← SRT
```

## Les six versions

| | Dossier | Ce qui la définit |
|---|---|---|
| v1 | `../rockwood-method/` | premier montage : cartes à cadre empilées, 84 BPM |
| v2 | `../rockwood-method-editorial/` | système typographique à filets, 7 segments caméra, musique 78 BPM |
| v3 | `../rockwood-method-signature/` | grammaire de film : 8 scènes, coupes, médaillon, halation |
| v4 | `../rockwood-method-premium/` | halation dosée + scènes de coupe habillées par leurs produits |
| v5 | `../rockwood-method-cinema/` | fonds reconstruits depuis le film, plaques de lisibilité, carte finale à plat large |
| **v6** | **`../rockwood-method-cinema-plus/`** | **caméra portée, fuites de lumière, beat kinétique du 100 %, push-in final** |

## À confirmer avant publication

- `rockwoodmethod.com/shop` est déduit de la prononciation (« …com shop »).
- La personne à l'écran n'est pas nommée : le film reste sur « The Rockwood Method ».
- Les visuels produit sont des **illustrations** dessinées en code (aucune photo fournie) :
  remplacer les PNG `assets/prod_*.png` suffit à les actualiser.
