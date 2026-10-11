# Analyse de `COOL.zip` — contenu de la sauvegarde

**Archive** : `COOL.zip` — 276 373 308 octets (**263,6 MiB**)
**SHA-256 (objet LFS)** : `5f82b15fb7855b433b64b0a468f40f3e2e440aaa8d18828b4994b9d66725f602`
**Contenu** : **1 404 fichiers**, aucun dossier vide, ratio de compression **1,00×** (stockage non compressé — les données sont déjà des médias)
**Analysé le** : 11 octobre 2026

---

## 1. En une phrase

> **Ce n'est pas un projet « COOL » : c'est une sauvegarde de l'environnement de travail complet d'un studio vidéo piloté par IA.**

L'archive contient un *home directory* de bac à sable (type Arena.ai sous Linux) : l'outillage, les **skills d'agents** (Claude/agents), **9 projets vidéo** avec leurs sources, leurs rushes, et **8 vidéos finales montées**. Les sources sont en français, les clients sont béninois. Aucun fichier ni dossier ne porte le nom « COOL » — c'est le nom que tu as donné à la sauvegarde.

---

## 2. Vue d'ensemble — répartition

| Dossier | Fichiers | Poids | Rôle |
|---|---:|---:|---|
| `Videos/` | 8 | **153,9 Mo** | ⭐ Les vidéos finales livrées |
| `repro/` | 84 | 28,0 Mo | Projet vidéo (plates, tests, rendus intermédiaires) |
| `uploads/` | 12 | 27,5 Mo | Matière première fournie par le client |
| `glam/` | 51 | 11,1 Mo | Projet vidéo |
| `cobalt/` | 24 | 9,0 Mo | Projet vidéo |
| `pl/` | 336 | 7,6 Mo | Un autre workspace Arena + portfolio « Jrd Design » |
| `leger-video/` | 31 | 6,6 Mo | Projet vidéo |
| `raw5`, `raw1`, `raw4` | 13 | 14,3 Mo | Rushes bruts (entrée / audio / transcription) |
| `.agents/` + `.claude/` | 769 | 9,7 Mo | **Skills d'agents** (même arbre, dupliqué ×2) |
| `rockwood-edit/` | 27 | 4,0 Mo | Projet vidéo |
| `felix/`, `peak/`, `priorities/` | 44 | 4,7 Mo | Projets vidéo |
| `.hyperframes/`, `setup_env.sh` | 5 | 2,8 ko | État de l'outil + script d'installation |

**Par type de fichier** : 168 Mo de vidéo (`.mp4`), 30,8 Mo d'images PNG, 18,4 Mo de MP3, 12,4 Mo de WAV, 5,2 Mo de markdown (656 fichiers !), 5,4 Mo de polices, et 2,5 Mo de scripts Python.

---

## 3. Les 8 vidéos finales (`Videos/`)

| Fichier | Poids | Format |
|---|---:|---|
| `leger-funnel-builder-16x9.mp4` | 34,2 Mo | 1920×1080 |
| `leger-funnel-builder-9x16.mp4` | 33,6 Mo | 1080×1920 |
| `peak-architects-blueprint-9x16.mp4` | 24,0 Mo | 1080×1920 |
| `priorities-studio-paper-9x16.mp4` | 19,0 Mo | 1080×1920 |
| `rockwood-method-montage-v2-9x16.mp4` | 14,7 Mo | 1080×1920 |
| `miss-lumiere-littoral-teaser-9x16.mp4` | 11,4 Mo | 1080×1920 |
| `miss-lumiere-littoral-teaser-4x5.mp4` | 10,2 Mo | 1080×1350 |
| `motivation-discipline-fr-9x16.mp4` | 6,8 Mo | 1080×1920 |

Toutes en H.264 + AAC, 24–30 fps, majoritairement verticales (9:16) — format réseaux sociaux / Reels / TikTok. Un master paysage 16:9 pour Léger.

---

## 4. Les 9 projets de production vidéo

Chaque projet suit **exactement la même méthode**, ce qui révèle un pipeline industrialisé :

```
BRIEF.md          → le brief client (source, style, palette, durées, scènes)
template.html     → la composition animée HTML/CSS/GSAP
build.py          → génère app/ (16:9), app_v/ (9:16) ou app_f/ (4:5)
audio/make_audio.py → musique + SFX synthétisés (aucune licence)
render.sh         → rendu + encodage ffmpeg
raw*/tr.py        → transcription (faster-whisper) → words.json (timing mot à mot)
```

| Projet | Contenu | Durée / format |
|---|---|---|
| **leger-video** | Film « Léger Akodjenou — Funnel Builder », identité reprise de la landing (#0a0a0b / #ff4d00, Space Grotesk + Instrument Serif) | 60 s · 16:9 + 9:16 |
| **peak** | **Peak Architects** — style « planche d'architecte » : cadre fin, cotes, cartes blueprint, vert/crème/cuivre | 22,9 s · 9:16 |
| **felix** | **Felix Gray** — style « scrapbook / journal papier » : carte photo scotchée, notes manuscrites, surligneur beurre | 48,8 s · 9:16 |
| **cobalt** | **Felix Gray (variante)** — affiche éditoriale bleu cobalt #2338ff + vert acide, 5 lames de transition, compteur de chapitres N°xx/16 | 48,8 s · 9:16 |
| **priorities** | Style « studio paper » v5 — inserts papier, texte extrudé, mots 3D X/WIN, sous-titres 2 niveaux | 37,1 s · 9:16 |
| **rockwood-edit** | **Rockwood Method** — montage talking-head : upscale 720p→1080p, punch-ins, overlays calés sur la transcription | 27,6 s · 9:16 |
| **repro** | **Reproduction** d'une vidéo de référence (voix française générée, filigrane de l'auteur original retiré) — 5 scènes (yeux bandés, montres, tournesols, anneau, roi d'échecs) | 23,2 s · 9:16 |
| **glam** | **Miss Lumière Littoral** — teaser de concours de beauté : logo, reine, tickets, date/lieu, partenaires | 30 s · 9:16 + 4:5 |
| **pl** | Workspace Arena distinct + portfolio **« Jrd Design — Graphiste & Designer de Marque »** (site FR, logo-jd.png) | site web |

> Détail technique récurrent et soigné : les BRIEF indiquent les **mesures de loudness** cible (ex. `-14,6 LUFS` pour Peak, `-13,9 LUFS` pour Felix) — signe d'un travail de mixage audio volontaire.

---

## 5. L'outillage : HyperFrames + agents

### `setup_env.sh` — reconstruction de l'environnement
Le script reconstruit tout l'outillage sous `/home/user/.cache` (effacé entre les sessions) :
- **ffmpeg** + **ffprobe** (paquets statiques npm)
- **Node.js v22.12.0** téléchargé depuis nodejs.org

Traduction : l'environnement est **éphémère**, et toute la chaîne est auto-réparable — d'où la nécessité de cette sauvegarde.

### `.hyperframes/` — l'état du moteur de rendu
```json
{ "latestVersion": "0.8.113", "commandCount": 43, "renderSuccessCount": 4,
  "recentRenders": [ 4 rendus réussis les 01–02 octobre 2026 ] }
```
Chaque projet embarque un `package.json` qui appelle **`npx hyperframes@0.8.106`** (preview / check / render / publish).

### `.agents/` + `.claude/` — 769 fichiers de *skills*
Deux copies **identiques** d'un même arbre de compétences, installé depuis **`github.com/heygen-com/hyperframes`** (traçé dans `.agents/.skill-lock.json`, version 3) :

- **`hyperframes-*`** (core, animation, audio, cli, creative, keyframes, registry, studio) — des centaines de *rules* d'animation (glitch chromatique, camera flight 3D, SVG path draw, motion blur…), des *blueprints* (ticker takeover, kinetic type beats, logo assemble…), des *adapters* (GSAP, anime.js, Lottie, Three.js, WAAPI, TypeGPU) et des exemples HTML
- **`general-video`** — sous-agents et scripts de découpage de frames (`.mjs`)
- **`media-use`** — LUTs, audio, références

Le dossier `pl/.../.claude/skills/` contient en plus **55+ skills généralistes** : `video-director`, `canvas-design`, `mcp-builder`, `slack-gif-creator`, `seo-audit`, `frontend-design`, `brainstorming`, `youtube-downloader`, `theme-factory`, etc.

### `pl/.../docs/video-director-skill-spec.md`
Un document de spécification de 12 ko : **« studio vidéo agentique personnel »** — moteurs (HyperFrames, FFmpeg, AssemblyAI, Whisper local, Remotion), workflow canonique en 15 étapes, routage par type de demande. C'est le **cerveau du système** : il explique pourquoi tous les projets partagent la même structure.

---

## 6. Les rushes et `uploads/`

`uploads/` contient la matière fournie, avec une astuce révélatrice : **7 fichiers `.js` qui sont en réalité des vidéos MP4** (les tailles correspondent exactement aux rushes de `raw1/`, `raw4/`, `raw5/`, `repro/`) :

| Dans `uploads/` (renommé `.js`) | Original | Taille |
|---|---|---:|
| `video brut.js` | → Rockwood | 4,95 Mo |
| `video brut4.js` | → Peak (`raw4/in.mp4`) | 2,62 Mo |
| `reference.js` | → référence Priorities | 3,52 Mo |
| `reference1.js` | → référence Rockwood v2 « Our Work » | 2,04 Mo |
| etc. | | |

Le renommage `.mp4` → `.js` était visiblement un moyen de **faire passer les vidéos à travers un filtre d'upload**.

On y trouve aussi `Grande soiree couronnement.jpg` (source du teaser Miss Lumière), des captures d'écran, et des dossiers `raw*/` complets : vidéo d'entrée + audio + planche de contact + script de transcription + `words.json` (horodatage mot à mot pour les sous-titres).

---

## 7. Ce que dit la structure sur l'usage réel

1. **Production vidéo à la chaîne, pilotée par IA** — 9 projets, 8 livrables, un template répété à l'identique. Ce n'est pas de l'exploration : c'est une usine.
2. **Clients locaux et réels** : Miss Lumière Littoral (concours de beauté), Peak Architects, Rockwood Method (coaching immobilier), Léger Akodjenou, Felix Gray, Priorities.
3. **Trois modes de travail** : création depuis un brief (leger, peak, glam), adaptation/reproduction d'une vidéo de référence (repro, priorities, cobalt, rockwood), montage de talking-head (rockwood).
4. **Zéro coût externe** : musique et SFX synthétisés par script Python (`make_audio.py`, `make_music.py`), voix avec faster-whisper en local. C'est exactement ce qu'annonce la spec : « coût externe par défaut : 0 € ».
5. **Tout-vertical** : 7 livrables sur 8 sont en 9:16 (ou 4:5) → contenu social first.
6. **Environnement éphémère** : le `.cache` disparaît, d'où `setup_env.sh` + `rebuild_assets.sh` dans chaque projet.

---

## 8. Ce que l'archive ne contient pas

- ❌ **Aucun `.git`** — pas d'historique de version
- ❌ **Aucun `node_modules`** — pas de dépendances
- ❌ **Aucun fichier `.env`** ni identifiant/secret
- ❌ Aucune archive imbriquée
- ⚠️ Timestamps internes au ZIP tous à **1980-01-02** (horodatage remis à zéro par l'outil qui a créé l'archive)
- ⚠️ `.hyperframes/config.json` contient un `anonymousId` de télémétrie (inoffensif)
- ⚠️ `felix-gray-scrapbook-9x16.mp4` est **référencé** dans `felix/BRIEF.md` mais **absent** de `Videos/` — livrable non conservé ou supprimé

---

## 9. Conclusion

`COOL.zip` = **l'instantané complet de ton studio vidéo IA**, prêt à être restauré : l'outillage (`setup_env.sh`), les compétences des agents (`.agents/`, `.claude/`), la méthode (`video-director-skill-spec.md`), les sources éditables des 9 projets (templates HTML + scripts Python) et les 8 vidéos finies.

**Sa valeur est dans les sources, pas dans les vidéos.** Les 154 Mo de `Videos/` sont des produits finis qu'on peut re-rendre ; les `BRIEF.md`, `template.html` et `build.py` sont ce qui permet de rejouer, corriger et décliner chaque projet.

---

<sub>Analyse produite à partir de l'index de l'archive seule (aucune extraction des médias) : lecture des métadonnées ZIP, du contenu textuel et des briefs. Le contenu LFS a été téléchargé par un runner GitHub Actions, les rapports étant rapatriés via l'API GitHub.</sub>
