# Rockwood Method — version « signature » (9:16)

Troisième et dernière itération du montage : vraie grammaire de film (scènes, coupes,
médaillon), finitions filmiques et typographie éditoriale.

**Film** : `film/rockwood-method-signature-9x16.mp4`
1080 × 1920 · 25 fps · H.264 High (CRF 17, preset slow) · AAC 192 kbps
**29,12 s · −14,0 LUFS / −1,5 dBTP · 32,5 Mo · 8,9 Mb/s**
**Couverture** : `film/pinterest-cover.jpg` (1000 × 1500)
**Sous-titres** : `subtitles/rockwood-method-signature-9x16.srt`

---

## Ce qui change par rapport aux deux versions précédentes

| | v1 `rockwood-method` | v2 `-editorial` | **v3 `-signature`** |
|---|---|---|---|
| Structure | plan unique habillé | 7 segments caméra | **8 scènes + 3 scènes de coupe plein cadre** |
| Caméra | fixe | recadrages + dérive | recadrages + dérive **+ flou de fouet aux coupes** |
| Sujet | plein cadre | plein cadre | **médaillon cerclé d'or** sur les scènes produit |
| Habillage | 11 cartes à cadre | 16 calques à filets | filets + **chiffre fantôme**, arc graphique, grille de points |
| Sous-titres | ASS mot-à-mot | ASS + mots-clés serif | **rendus en Python** : montée mot à mot, pop du mot prononcé, or → crème |
| Image | contraste/saturation | + courbe S, vignettage, grain | **+ halation ambrée, aberration chromatique, grain modulé par la luminance** |
| Son | 84 BPM, bips | 78 BPM, taps papier | **74 BPM, whooshes à chaque coupe, risers, carillons de scène** |

## Les six signatures qui font le rendu

**1. Une grammaire de montage.** Huit scènes numérotées (`01 · HOOK` → `08 · THE METHOD`)
affichées en running head, et **13 coupes** alignées sur les respirations de la voix.
À chaque coupe : flou directionnel horizontal de 0,17 s et whoosh. Le plan n'est plus
habillé, il est monté.

**2. Trois respirations plein cadre.** Les trois produits n'apparaissent plus en cartes
superposées mais en **scènes entières** : fond espresso, grille de points, arc graphique,
chiffre fantôme en fond, titre serif italique 132 px, filet d'accent — et **le sujet en
médaillon cerclé d'or** en bas, en contre-champ du carton. C'est la mise en page qu'on
voit dans les bons carrousels éditoriaux.

**3. Finitions filmiques.** Halation ambrée sur les hautes lumières (la peau et l'écran
débordent d'un halo chaud, comme sur un scan argentique), légère **aberration chromatique**
latérale (±2 px), **grain animé modulé par la luminance** (plus marqué dans les tons moyens,
invisible dans les noirs et les blancs — c'est ce qui distingue un grain film d'un bruit vidéo).

**4. Sous-titres composés, pas incrustés.** Rendu en Python, pas en ASS : chaque mot monte
en 90 ms, le mot prononcé grossit de 5 %, passe en **or** puis se pose en crème. Les mots
collés (`100%`, `self-guided`, `rockwoodmethod.com`) sont **fusionnés en un seul jeton** —
plus de césure au milieu d'un mot composé. 14 séquences, 2 lignes maximum, aucune inférieure
à 0,7 s.

**5. Typographie tenue.** Instrument Serif italique pour tous les titres, Space Grotesk pour
les micro-libellés interlettrés, Inter pour les sous-titres et le courant. Trois polices,
deux couleurs, aucune exception.

**6. Bande son.** 74 BPM, huit accords enrichis (Am9 → Fmaj7 → Cmaj9 → G6 → Em7 …), arpèges
espacés, sub, grain vinyle continu, **whoosh à chaque coupe**, riser avant chaque moment fort,
carillon de scène sur les cutaways, impact grave + carillon sur la carte finale.

## Structure

```
rockwood-method-signature/
├── BRIEF.md          ← ce document
├── README.md         ← pipeline, mixage, reconstruction
├── tools/            ← plan3, assets3, captions3, composite3, gen_audio3, make_cover3
├── assets/           ← 26 PNG (bandeau, running heads, cutaways, cartons, médaillon, progression)
├── audio/            ← music3.wav, sfx3.wav, words.json
├── film/             ← film final + couverture Pinterest
└── subtitles/        ← SRT
```

## Repères de la timeline

| Temps | Scène | À l'écran |
|---|---|---|
| 0,00 – 3,00 | 01 · HOOK | bandeau + sous-titres |
| 3,02 – 4,45 | 02 · THE PROMISE | autocollant patate `$0` |
| 3,95 – 6,40 | | titre *The Rockwood Method* |
| 6,85 – 8,00 | 03 · THE TOOLKIT | carton 01 (playbook) |
| **8,00 – 9,40** | | **scène plein cadre — Financial Playbook + médaillon** 01 |
| 9,55 – 10,70 | | **scène plein cadre — Printable Bundle** 02 |
| 11,00 – 12,00 | | **scène plein cadre — AI Income Optimizer** 03 |
| 12,45 – 13,60 | | tampon GAME CHANGER |
| 13,70 – 17,00 | 04 · THE FOUNDATION | *Rock solid.* |
| 17,10 – 19,50 | 05 · THE PROOF | compteur **0 → 100 %** (synchro voix) + pastille |
| 19,62 – 22,45 | 06 · THE OUTCOME | *Less stress. / More savings.* (glissés) |
| 22,60 – 25,90 | 07 · THE OFFER | pastille dorée + flèche animée |
| 25,85 – 29,10 | 08 · THE METHOD | carte finale + fondu |

## Historique

- `../rockwood-method/` — v1, montage habillé, plan fixe.
- `../rockwood-method-editorial/` — v2, caméra + système typographique + grain.
- `rockwood-method-signature/` — **v3, version recommandée**.
