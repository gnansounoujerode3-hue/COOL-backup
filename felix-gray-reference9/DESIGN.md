# Direction Artistique & Architecture Motion Design — `video brut 9.mp4` (Inspiré par `reference9.mp4` & `MOTION-DESIGN.md`)

## 1. Intégration de la Méthodologie `MOTION-DESIGN.md` (COOL)

Conformément à `MOTION-DESIGN.md` sur `main`, toutes les animations de `felix-gray-reference9-9x16.mp4` respectent les principes suivants :

1. **Intention & Hiérarchie (« Une animation principale par écran »)** :
   - Chaque séquence possède **un seul mouvement principal** qui guide le regard ou relie deux états (recul de caméra Z-space, glissement de sélection de texte par curseur, empilement de pilules UI, tracé progressif de ligne SVG, ou recul de fenêtre finale), tandis que les éléments secondaires restent discrets et cohérents.
2. **Courbe d'accélération/décélération douce (`cubic-bezier(0.2, 0.8, 0.2, 1.0)`) & suppression des rebonds agressifs** :
   - Tous les rebonds agressifs (`ease_out_back` avec overshoot) sont remplacés par l'implémentation mathématique exacte de `--motion-ease-out: cubic-bezier(0.2, 0.8, 0.2, 1.0)`.
   - Les apparitions suivent le motif `[data-reveal]` de `MOTION-DESIGN.md` : combinaison pure de `opacity: 0 -> 1` et d'une légère montée directionnelle `transform: translateY(14px) -> translateY(0)` (mise à l'échelle proportionnelle `28px` en `1080×1920`).
3. **Repères de rythme normalisés (`MOTION-DESIGN.md`)** :
   - **Retour d’appui ou activation (`:active`, `scale(0.98)`)** : `140 ms` (dans la plage `100–180 ms`, `--motion-fast: 180ms`).
   - **Survol / focus d’un contrôle (`:hover` `translateY(-2px)`, `:focus-visible` `outline: 3px solid currentColor; outline-offset: 3px`)** : `180 ms` (plage `150–220 ms`).
   - **Transition d’état ou petite apparition** : `280–360 ms` (plage `220–400 ms`).
   - **Entrée d’une section importante (`--motion-enter`)** : `480 ms` (plage `400–650 ms`).
   - **Séquence narrative / mouvement de caméra ou tracé SVG (`GSAP DrawSVG`)** : `600–850 ms` (plage `500–900 ms`).
   - **Décalage en cascade (`stagger`) des éléments secondaires** : `60 ms` (plage `40–80 ms`).
4. **Motifs UI inspirés de `Uiverse`, `Magic UI`, `Aceternity UI` et `GSAP`** :
   - **Tracé progressif des courbes vectorielles (`GSAP DrawSVG`)** : les courbes topographiques dorées (`#D9A441`) et terracotta (`#D8432E`) se dessinent progressivement le long de leur chemin.
   - **Sélection de texte interactive pilotée par le curseur** : la poignée droite `o|` de la boîte de sélection bleue suit en temps réel le déplacement du curseur filaire qui sélectionne le texte de gauche à droite, suivi d'un état `:active` (`scale(0.98)`, `140 ms`) et d'un anneau `:focus-visible`.
   - **Reflet lumineux (`Shimmer` / `Border Beam` de `Magic UI` & `Aceternity UI`)** : un reflet subtil traverse les pilules UI et le cadre filaire lors de leur validation d'état.

---

## 2. Chorégraphie Séquentielle (`0,00 s – 54,85 s`, `1646` images @ `30,00 fps`)

| Séquence | Temps (`s`) | Audio (`video brut 9.mp4`) | Animation Principale (`reference9.mp4` + `MOTION-DESIGN.md`) |
| :--- | :--- | :--- | :--- |
| **1** | `0,00 – 5,65 s` | *« I got into architecture—my dad taught construction at a local technical college, »* | **Caméra Z-Space (`650 ms`) & Révélations `[data-reveal]` (`480 ms`, `cubic-bezier(.2,.8,.2,1)`)** : Apparition sans rebond (`translateY(28px) -> 0` + `opacity`) de `i got into` $\rightarrow$ `architecture.` $\rightarrow$ `construction / my dad taught` (`stagger 60 ms`) $\rightarrow$ `at a local / technical college.`. La courbe SVG dorée se trace progressivement à partir de `1,65 s` (`750 ms`), accompagnée des pilules UI avec reflet `Shimmer` et du flash bleu cobalt final (`5,25–5,65 s`). |
| **2** | `5,65 – 10,75 s` | *« so I'd always been aware of the construction sector, and was dragged onto sites »* | **Talking Head (`5,65–8,30 s`) + Cutaway Projecteurs & Connecteurs 3D (`8,30–10,75 s`, inspiré de `4,60–6,10 s` dans `reference9.mp4`)** : `from day one` monte doucement (`translateY`), deux connecteurs 3D s'assemblent vers le double faisceau lumineux central pendant que `dragged onto` $\rightarrow$ **`building sites.`** se révèle avec un décalage de `60 ms`. |
| **3** | `10,75 – 17,30 s` | *« when I was young, I was kicking my heels during summer holidays, he used to take me onto sites and I used to be as like a helper, »* | **Cutaway Papier Crème (`#F7F0D8`) + Portail Noir & 3 Pilules UI (`10,75–14,10 s`, inspiré de `11,60–13,40 s` dans `reference9.mp4`)** : Tracé progressif des lignes SVG terracotta (`650 ms`). Les 3 pilules bleues (`When I was young`, `Kicking my heels...`, `During summer holidays!`) entrent en `translateY(24px) -> 0` (`320 ms`, `cubic-bezier(.2,.8,.2,1)`) avec états `:hover` (`translateY(-2px)`), `:active` (`scale(.98)`) et `:focus-visible` + reflet `Shimmer`. **Talking Head (`14,10–17,30 s`)**. |
| **4** | `17,30 – 20,55 s` | *« and it gave me very early awareness of what the construction process is. »* | **Ruban Néon Diagonal (`17,30–17,65 s`, réplique de `t=8,20 s`) + Sélection de Texte Pilotée par Curseur (`17,30–18,85 s`) + Transition d'État en Cadre Filaire (`18,85–20,55 s`, réplique de `t=9,60–10,85 s`)** : Le curseur filaire tire la sélection bleue `|early awareness|` de gauche à droite (`450 ms`), puis le cadre filaire trace son contour rouge (`600 ms`) et relie l'état initial `what the` (`18,90–19,35 s`) à l'état final `the construction` / **`PROCESS`** (`19,35–20,55 s`). |
| **5** | `20,55 – 30,35 s` | *« I was quite artistic at school... Happened upon the term 'architect' without quite knowing what an architect did, »* | **Talking Head (`20,55–26,85 s`)** $\rightarrow$ **Cutaway Papier Crème #2 (`26,85–30,35 s`, réplique de `t=16,95–17,85 s` dans `reference9.mp4`)** : `the term` apparaît sur fond crème avec la courbe SVG dorée (`26,85 s`), puis la ligne SVG terracotta se trace en bas pendant que **`ARCHI`** $\rightarrow$ **`ARCHITECT`** se révèle en cascade (`stagger 60 ms`) avec les silhouettes sombres glissant dans les angles, suivi de `without knowing` / **`WHAT IT MEANT`** et du faisceau lumineux diagonal ambre-rouge (`30,10–30,35 s`, réplique exacte de `t=17,85 s`). |
| **6** | `30,35 – 43,40 s` | *« and the more I sort of investigated... The idea of having the technical skills, but also the creative, and having a management role as well and driving the process, »* | **Talking Head (`30,35–35,30 s`)** $\rightarrow$ **Sélection Interactive `|technical skills|` + Cadre Filaire `plus the` / `CREATIVE` (`35,30–38,45 s`)** $\rightarrow$ **Talking Head (`38,45–43,40 s`)** avec sous-titres progressifs et light leak. |
| **7** | `43,40 – 54,85 s` | *« was something that really appealed to me from a very early age. So I think I even said when I was probably about 14 years old that I wanted to become an architect. »* + `[B-roll peakarchitects]` | **Talking Head (`43,40–48,95 s`)** $\rightarrow$ **Recul de Fenêtre (`580 ms` `cubic-bezier(.2,.8,.2,1)`) sur Fond Noir + Titres Chrome Métallisé `"AGE 14"` / `"ARCHITECT"` (`48,95–51,80 s`)** $\rightarrow$ **B-Roll d'Atelier `peakarchitects` encadré par le HUD (`51,80–54,85 s`)**. |
