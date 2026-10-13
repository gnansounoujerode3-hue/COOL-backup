# threeui.com

**Callable as: ThreeUI** (aliases: threeui, three ui, designcode threeui, @designcodeio/threeui)

**This entry is a different kind of thing from every other one in the library. Read this paragraph before using it.** Every other entry measures one live site's design system by capture, because the values have to be re-derived (the reference's assets aren't ours to use). ThreeUI is the opposite case: it's an MIT-licensed (Community tier), npm-installable **component source**, explicitly built "for agents" ("Copyable as prompts" is the site's own tagline). There is no single Type/Layout/Colour/Motion system to measure: it's 220 independently-authored components, each its own micro-system, and the actual source code is legally reusable, not just informative. Treat this as a **donor catalog**, not a site to Match or Adapt.

Surveyed 2026-08-21 via the public GitHub repo (`MengTo/threeui`, MIT, 1112 stars): README, file tree, and full source read for several components. Live `/browse` gallery structurally read (220 components, category filters: Landing Pages, Hero, Three.js, Backgrounds, Buttons, Text Animation, UI Elements, CSS, Motion Design, Sections) but **not visually screenshotted**. The in-app Browser pane hit this library's own documented "pane is not a measurement instrument" failure (`computer{screenshot}` errored "not displayed, so the page is not compositing frames"). Evidence here is source-level, not pixel-level; a future pass through CDP/headless would add the visual side.

**Cloned locally 2026-08-28 to `E:\New Claude\threeui`** (141 MB, shallow). The
2026-08-21 pass read the repo through the GitHub API; this one has the whole
tree on disk, which settled the tier question below and corrected two things
this note previously had to infer. Grep the clone rather than re-fetching.

## What it actually is

- **Stack**: React + Three.js + TypeScript + Vite. Install: `npm install @designcodeio/threeui`, then `import { AtTheHorizon } from "@designcodeio/threeui"`.
- **License**: MIT for application code and every Community-tier component. Bundled fonts under SIL OFL 1.1. **Pro and Beta components are excluded from the public repo**: only Community-tagged results on the site are actually in the GitHub source / npm package. Don't try to source a Premium-tagged component from the repo; it isn't there.
- **How to settle "is *this* component redistributable?" in one step** (added 2026-08-28): the public repo is **generated, not curated**. `scripts/sync-community-from-main.mjs` takes a private source snapshot and copies out only the Community items. So *presence in the public repo is itself the tier proof*: if a component's file is there, it is Community and MIT; if it isn't, it's Premium/Beta. Cross-check by name in `src/data/shaders.tsx`, where every Community entry is registered as `CommunityRendererN`. This replaced a genuine blocker: the Kage landing page had been mirrored (`swipefile-builds/kage-mirror`) and flagged do-not-publish for two days purely because its individual tier couldn't be confirmed from outside. `KageLandingPage` is `CommunityRenderer1`. Don't re-derive this from the live site's badges. Read the repo.
- **Component imagery ships with the components.** Not just code: e.g. Kage's ten foreground cutouts and four generated stills are in `public/landing-pages/secret-pathways-assets/`, and the README's MIT grant explicitly covers "ThreeUI-authored Community imagery". The one carve-out is catalog thumbnails/previews served from `threeui.com`, which the repo does *not* redistribute; those are the grid's own preview images, not any component's assets.
- **Scale**: 50 Community parent components, 111 routes, 164 browseable results. The full commercial catalog (220, including Premium) is larger than what's redistributable.
- **Shape on disk**: `src/package-components/*.ts` (the published, importable components: `AtTheHorizon`, `BrandOrbs`, `CloudField`, `DotMatrixBackground`, `FlowField`, `GenerateButton`, `LiquidMetalButton`, etc.) and `src/shaders/<name>/` (one self-contained `.html` + a React `.tsx` wrapper per effect: `liquid-metal-button`, `condensation`, `energy-orb`, `globe`, `dot-matrix`, `ribbon-field`, `portal-field`, `fluid-field-background`, `koi-studies`, and more).

## Structural patterns worth naming

Read one component's full source (`LiquidMetalButton.tsx` + its `liquid-metal-button.html`) end to end. Three techniques generalise well beyond this one component:

- **Explicit-clock scrubbing instead of a free-running `requestAnimationFrame` loop.** The shader HTML exposes `window.__seek(v)`: external code sets the clock value and the component renders that exact frame, rather than ticking its own rAF internally. **This is the same seek-safe/deterministic-render discipline HyperFrames' own `THREEJS-PATTERN.md` had to hand-roll for the Systo video builds** (a WebGL scene must be keyed off the timeline's own seek, never an independent clock, or an arbitrary-timestamp screenshot/render shows the wrong frame). Independent confirmation, in unrelated production code with no connection to HyperFrames, that this is the correct pattern for any embeddable/scrubbable Three.js component, worth citing directly if `hyperframes-keyframes` or a future video build needs to justify the approach to someone unfamiliar with why a plain rAF loop is wrong here. **Strengthened 2026-08-28 by the local clone:** this was originally read off one component and generalised; `grep -rl "__seek" src/` returns **10 files** across unrelated effects (japanese-tower, liquid-metal-button, audio-wordmark, creator-studio-intro, epilude-footer, gallery-heading, thinking-button, inner-green-3d). It's a house convention there, not a one-off.
- **iframe + `postMessage` config bridge.** Each shader effect ships as a self-contained HTML document (its own `<canvas>`, its own inline WebGL/GLSL, zero React/build-tool coupling) and is configured post-mount by posting a message into the iframe (`{ liquidMetalButton: { text, pillWidthUnits, embedded } }`). This isolates the heavy WebGL runtime completely from the host page's bundle and DOM: genuinely easy to drop into any stack (a Framer mirror, a Next.js site, a plain static page) regardless of what that stack's own JS framework is, since the component never touches the parent's React tree at all.
- **One reference-unit variable drives the whole component's scale**, exactly the `--u` pattern already in this library from Sylva (`library/sylva.md`): a second, independent confirmation of "one fluid constant pinned to an explicit reference measurement" in completely unrelated production code. Here: `--h` is the one ergonomic knob (button height), and every other dimension is `calc(N * var(--u))` where `--u: calc(var(--h) / 516)`, 516 being the reference artwork's own measured height. Change `--h`, the whole button rescales losslessly.
- **Physically-reasoned shadow/glow layering, explained in comments, not tuned by eye.** `LiquidMetalButton`'s CSS comments justify each shadow layer by what it represents physically ("A shadow needs something to fall on: a soft ambient pool lifts the ground just off black", "deepen it while the metal is lit, so the bright face keeps its edge"): the same why-not-what comment discipline this project holds code to, applied to visual design decisions. Worth modeling future glassmorphism/metal/glow work on this reasoning style rather than a flat "looks about right" value.

## Notable components by category (non-exhaustive, from the Community tier)

- **Buttons / interactive**: `LiquidMetalButton` (pill / circle / play variants, colored or monotone rendering), `GenerateButton`, `DotBorderButton`, `CircleButtons`, `FloatingDotsCta`.
- **Backgrounds / fields**: `FlowField`, `DotMatrixBackground`, `CloudField`, `BellFieldBackground`, `FluidFieldBackground`, `ElementsBackground`, `EmeraldHorizonBackground`, `CondensationBackground`, `CrtBackground`, `DimensionalField`, `ExpanseField`, `RibbonField` (shader dir), `PortalField` (shader dir).
- **Data / abstract 3D**: `ConstellationField`, `ConnectivityGraph`, `DataField`, `DiagnosticsPanel`, `DefenseLines`, `EnergyOrb` (shader dir), `Globe` (shader dir).
- **Character / showcase**: `CharacterCarousel`, `CharacterFilmstrip`, `CharacterWave`, `BallStudy`, `ClothStudy`, `BookshelfScene`, `Gallery`.
- **Brand / identity**: `BrandOrbs`, `AudioWordmark`, `EngravedCertificate`, `AtTheHorizon`.

Category filters on the live browse grid (`/browse`), useful search terms when looking for a donor by job rather than by name: Landing Pages, Hero, Three.js, Backgrounds, Buttons, Text Animation, UI Elements, CSS, Motion Design, Sections.

## Where the reusable 3D craft actually is (added 2026-08-28, from the clone)

The catalog's *reputation* is its backgrounds and buttons. Its most transferable
engineering is not in either.

- **`src/shaders/bookshelf/bookshelfRenderer.js` (4,241 lines) is the one to read
  for a lit interior.** `RoomEnvironment` + `PMREMGenerator` for image-based
  lighting (line 4121), `RectAreaLightUniformsLib` for window-shaped light, 16
  `MeshPhysicalMaterial`, 39 roughness / 20 metalness / 8 clearcoat assignments,
  OrbitControls, and a complete pointer/drag/orbit/disposal lifecycle. If a brief
  needs a room, a product on a surface, or anything where physical materials sit
  under real environment light, start here rather than from a three.js tutorial.
- **`src/shaders/temple-night/templeNightRenderer.js` (2,536 lines) is the one to
  read for mood**, the Kage scene. But know what it is before budgeting from it:
  a single hard-baked night. `timeOfDay` and `sunPosition` appear **zero** times in
  it (and zero times in the bookshelf and japanese-tower renderers too). One
  `FogExp2(0x050a0e, 0.0168)`, a fixed `MOON = {x, y, z, r}` constant, hand-tuned
  `hdr()` colour literals, 1 hemisphere + 2 directional + 6 point lights placed for
  that one moment. **Nothing in this catalog is parameterised by time of day.** Any
  brief wanting a day/night dial is building it, not importing it.
- **The transferable idea in the temple is fog-as-colour-grade.** Its comment at
  line 1089 records the actual experiment: darkening the timber and tiles moved the
  hall 0.18 of a luminance unit, but moving the *fog colour* graded the scene
  properly. The constants don't travel; the mechanism does, and it's the natural
  thing for a time-of-day control to drive.
- **Version reality**: the bookshelf pins a vendored `three165` (three@0.165.0)
  with its own OrbitControls/RoomEnvironment/RectAreaLightUniformsLib copies; the
  package peer range is `>=0.149 <1`. Our own three.js builds are ahead (0.184 in
  systo-commerce, 0.185 in Systo Cars). Lifting a file wholesale drags r165 in.
  Porting the technique is the better path; and the riskiest call,
  `new RoomEnvironment()` then `pmremGenerator.fromScene(env, 0.04)`, has an
  unchanged signature in current three, so it moves across cleanly.

## Motion

**Motion fidelity: none**

Not "unmeasured" in the usual sense: the gate's four-value scale (`spec` /
`partial` / `signature-only` / `none`) is for *measured* motion on a site
whose animation has to be re-derived from a live capture. `none` is the
correct, honest value here, and `motion-spec.py`'s refusal to build from it is
correct behavior too: this entry never stood in for measuring, because the
actual source (every tween, easing, and timing constant) is directly readable
in the repo and importable via the npm package. There is nothing to
re-measure and nothing this entry could hand `motion-spec.py` as a mapping.
**Do not re-capture this "site" to try to promote it to `spec`**. Read the
specific component's own source before using it, the same as reading any
other dependency's code.

## What this entry is good for

The first place to check (before hand-authoring a CSS/SVG approximation or reaching for a generic gradient) whenever a brief's ambition reads as "premium," "wow," or calls for a specific expressive 3D/WebGL moment (a hero background, an animated button, a data-visualization field, a brand mark reveal) and the register isn't obviously served by the site's own existing system. Pairs with the "wow ambition" check in `SKILL.md` alongside Sylva: Sylva shows *that* a bespoke three.js register can carry a whole page with zero DOM color; ThreeUI supplies actual, licensed, ready components to build that register from, in minutes rather than from scratch.

Poor fit for: anything that needs to match an *existing* brand's measured system exactly (this is a donor catalog, not a brand system; see `references/adaptation.md`'s ownership line before landing one of these components into a client build with no license/attribution check), and anything where the "wow" budget doesn't justify a real WebGL dependency (bundle size, GPU cost) over a cheaper CSS effect.

## Gotchas hit while surveying

1. **The in-app Browser pane could not screenshot or composite this page**: same documented failure as everywhere else in this library (`computer{screenshot}` → "the Browser pane is not displayed, so the page is not compositing frames"). Used `read_page` (accessibility tree) plus the GitHub REST API and raw `githubusercontent.com` file fetches instead. If a future job needs actual pixel screenshots of a specific component's live render (not just its source), route through CDP/headless per this library's standing rule, not the pane.
2. **`/browse` redirected to `/` in the pane's navigation**: the site is a client-rendered SPA; the route resolved fine (page title and content matched `/browse`'s content) but the tab's reported URL didn't update. Not investigated further since source-reading answered the actual question; worth knowing if a future capture pass tries to script navigation by URL rather than by clicking.
3. **Only Community-tagged results are real for sourcing purposes.** The live grid interleaves Community and Premium/Beta labels in the same list (e confirmed via `read_page`, e.g. "Sylva — Living Green... Community component" next to "Sylva — Sakura Sunset... Premium component"). Don't assume every visually-similar result is available in the public repo just because a sibling variant is.

## Verification achieved

Source-level only: README claims cross-checked against the actual repo file tree (component/shader directory listings via the GitHub Contents API) and one full component read end-to-end (`LiquidMetalButton.tsx` + `liquid-metal-button.html`, 895 lines) to confirm code quality and extract the structural patterns above. Not verified: visual rendering quality of any component (screenshot capture failed, not retried through CDP), whether every category-filter count on the live site matches the repo's actual file count, and the exact terms/pricing of the Premium tier (irrelevant to this entry, which only concerns the redistributable Community tier).

**2026-08-28 clone pass.** Verified on the full tree on disk: the licence chain
(LICENSE + README grant + the generated-repo mechanism + `CommunityRenderer1`),
that Kage's image assets ship in-repo with filenames matching our mirror, the
`__seek` count across 10 files, the absence of `timeOfDay`/`sunPosition`
anywhere in the three largest scene renderers, the bookshelf's lighting and
material inventory, and the three.js version gap against our own builds. Still
not verified, and unchanged from above: the visual rendering quality of any
component; nothing in this catalog has been looked at, only read. Every claim
in this note is a claim about source code, not about how anything looks.
