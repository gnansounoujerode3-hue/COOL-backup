# Rockwood Method — version éditoriale (9:16)

Montage premium du rush `video brut.mp4`, pensé pour un feed Pinterest / Reels :
système typographique éditorial, caméra qui respire, grain argentique, son soigné.

**Film** : `film/rockwood-method-editorial-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High · AAC 192 kbps · **29,12 s** · **−14,0 LUFS / −1,5 dBTP** · 27,9 Mo
**Couverture** : `film/pinterest-cover.jpg` (1000 × 1500, format natif Pinterest)
**Sous-titres** : `subtitles/rockwood-method-editorial-9x16.srt`

---

## Ce qui fait le « rendu Pinterest »

Pinterest récompense les images qui ressemblent à une **page de magazine** : cadrage propre,
typographie serif, grands vides, palette chaude limitée. Six décisions vont dans ce sens.

### 1. Un système typographique, pas des vignettes
Tout l'habillage repose sur trois polices et deux couleurs :
**Instrument Serif italique** pour les titres, **Space Grotesk** pour les micro-libellés
interlettrés, **Inter light** pour le texte courant. Or `#e9bd7c` sur crème `#fdf7ec`.
Plus aucun cadre lourd : la hiérarchie vient des **filets fins** et des espaces.

### 2. Un bandeau de magazine qui vit
En haut : le nom du film à gauche, la mention « self-guided film » à droite, un filet fin
sur toute la largeur — et une **barre d'or qui progresse** dans ce filet pendant 29 s.
C'est le seul élément permanent : il donne un cadre, comme un sommaire de revue.

### 3. La caméra respire (le vrai secret)
Le plan unique est découpé en **7 segments** alignés sur les silences de la voix
(6,55 / 13,45 / 17,05 / 19,55 / 22,55 / 25,85 s). Chaque segment a son cadrage
(zoom 1,00 → 1,066) et **dérive lentement** pendant toute sa durée : la vidéo n'est plus
une prise fixe, c'est un montage.

### 4. Traitement filmique
Upscale Lanczos 720p → 1080p, contraste 1,055, courbe en S douce, colorimétrie chaude
(ombres froides + hautes lumières dorées), **vignettage** et **grain animé**
(`noise=alls=4:allf=t+u`) pour casser la propreté numérique du fond studio.

### 5. Des cartes qui se posent, pas qui clignotent
Chaque bloc apparaît en fondu sur 0,5 s avec une montée de 26 px (ease-out), le tampon
arrive en « slap » (échelle 1,075 → 1,00 en 0,34 s), le grand chiffre en zoom lent.
Les blocs posés sur le sujet sont précédés d'un **panneau noir à bords fondus** : lisibles
sans avoir l'air d'être collés.

### 6. Le son signe aussi le rendu
Lit musical original à **78 BPM** (Am9 – Fmaj7 – Cmaj7 – G6 : nappe, arpèges espacés,
pulsation grave), grain vinyle continu, **riser** avant la carte finale, et des SFX
« papier » (ticks feutrés, tapis posé, impact grave, carillon au CTA) au lieu de bips.

---

## Structure

```
rockwood-method-editorial/
├── BRIEF.md            ← ce document
├── README.md           ← reconstruction et détails techniques
├── tools/              ← scripts (plan2, make_assets2, make_subs2, gen_audio2, composite2, make_cover)
├── assets/             ← 16 PNG d'habillage (panneaux fondus, filets, tampon, pastille)
├── audio/              ← music2.wav, sfx2.wav, words.json (timing mot à mot)
├── film/               ← film final + couverture Pinterest
└── subtitles/          ← SRT
```

## Timeline de l'habillage

| Temps | Écran | Voix |
|---|---|---|
| 0,0 – 3,0 | Bandeau + sous-titres seuls | « Think finance tools… » |
| 3,05 – 4,45 | Autocollant patate (`$0`) posé en haut à droite | « …budgeting with a potato. » |
| 3,95 – 6,40 | **The Rockwood Method** (serif italique) | « Enter the Rockwood Method… » |
| 6,95 → 11,9 | Filets produit 01 → 02 → 03 | « …Playbook, planner bundle, optimizer » |
| 12,50 – 13,70 | Tampon **GAME CHANGER** en bas | « …each a game changer. » |
| 13,75 – 16,95 | **Rock solid.** | « Build a rock-solid foundation… » |
| 17,15 – 19,45 | **100 %** + « self-guided · zero hassle » | « 100% self-guided, zero hassle. » |
| 19,65 – 22,40 | **Less stress. / More savings.** | « Life post-Rockwood… » |
| 22,65 – 25,90 | Pastille CTA dorée | « Grab yours now at… » |
| 25,85 – 29,10 | Carte finale plein cadre + fondu | — |

## Version précédente

`../rockwood-method/` contient le premier montage (28,9 / 29,1 s) : cartes produit
empilées, musique à 84 BPM, même structure de voix. Conservée pour comparaison.
