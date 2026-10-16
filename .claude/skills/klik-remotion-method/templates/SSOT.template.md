# <project_name> — Animation SSOT

Status: DRAFT
<!-- The single source of truth. Every downstream agent (storyboard, execution
     plan, build, QA) works from THIS file with no other context — if it isn't
     written here, it doesn't exist. The user's approval flips DRAFT → APPROVED;
     never flip it yourself. After approval, changes are appended as dated
     amendments, never silent edits. -->

## Intake sequence
<!-- The questionnaire state machine. Resume rule: the next question is always
     the first ⬜ below. The user may answer anything ahead of time — record it,
     then RETURN HERE and continue in order. ✅ only when its section is filled
     AND confirmed with the user. -->
| # | Item | Status |
|---|---|---|
| 1 | Objective, platform & spec | ⬜ |
| 2 | Style references | ⬜ |
| 3 | Mood | ⬜ |
| 4 | Brand guide | ⬜ |
| 5 | Visual assets | ⬜ |
| 6 | Copy & script | ⬜ |
| 7 | Music | ⬜ |
| 8 | Camera & pacing dials · composition model | ⬜ |

---

## 1 · Objective, platform & spec

- **Purpose:** <!-- launch / explain / convert / hype -->
- **Audience:**
- **Platform(s):** <!-- IG / TikTok / FB → vertical, ~20–30s max · YouTube / website → landscape, longer OK -->
- **Dialogue or pure motion graphics:** <!-- THE FORK — drives 6.1 vs 6.2 and how music is used in 7 -->
- **Format & length:** <!-- RECOMMEND from platform, but ALWAYS let the user choose. Record who chose. -->

**Hard numbers (no code until these are filled):**
| Item | Value |
|---|---|
| Resolution | <!-- e.g. 1080×1920 --> |
| fps | <!-- must match any host timeline exactly --> |
| Duration → total frames | |
| Deliverable / handoff | <!-- mp4 · chroma-key slice (key value?) · ProRes 4444 alpha --> |
| Safe zones | <!-- vertical platforms: UI overlays eat top/bottom/right — state margins or n/a --> |

## 2 · Style references

<!-- The user's direction, elicited — never proposed first. Named references
     beat adjectives: "Apple keynote typography", "VOX explainer", "grunge
     paper-cutout". Every supplied ref gets the extraction + per-item confirm
     pass in references/reference-analysis.md before it enters the table. -->
- **Direction (user's words):**

| Reference | Type | Confirmed takeaways (dial/motif terms) | Explicitly NOT taking |
|---|---|---|---|
| | <!-- video/image/site --> | | |

- **Anti-references:** <!-- looks to avoid — extracted precisely, same vocabulary -->

## 3 · Mood

- **Mood:** <!-- high-impact / fast / dramatic · premium / calm / explainer -->
- **Pacing feel in one sentence:**

## 4 · Brand guide

| Element | Value |
|---|---|
| Primary colors | <!-- hex --> |
| Secondary / full palette | <!-- hex --> |
| Primary font | |
| Secondary font | |
| **Font deviation allowance** | <!-- none / weights-only / AI may pick complementary faces --> |
| Color deviation allowance | <!-- tints-shades-only / strict hex only --> |

**Logo inventory** <!-- SVG strongly preferred; else high-res PNG. Path per variant. -->
| Variant | File | Format |
|---|---|---|
| Full (with name) | | |
| Mark only | | |
| Inverted / mono | | |

- **Logo rules from brand guide:** <!-- clear space, min size, forbidden treatments -->

## 5 · Visual assets

- **Existing sources:** <!-- product site (pull HTML), Figma (export SVGs), screenshots, footage. Ask FIRST — critical for software showcases. -->
- **If none for a needed visual:** build it as **HTML/CSS with frontend-design
  craft** (ports ~1:1 into Remotion markup) — generative AI images only for
  textures/backgrounds that will never need to be re-rendered exactly.

**Asset log** <!-- EVERY asset is viewed before it enters this table (klik-anim §A9). Clean = no burned-in captions, watermarks, third-party logos. -->
| Asset | Path | Source | Viewed? | Clean? | Usable res |
|---|---|---|---|---|---|
| | | | | | |

## 6 · Copy & script

- **Author:** <!-- user's own copy (RECOMMEND this) / AI-drafted, user-approved -->
- **Copy law (klik-anim §A8):** the lines below are the ONLY words that may appear
  on screen, plus supplied brand marks. Nothing else, ever.

### 6.1 · If dialogue: transcript
<!-- Ask for the stitched a-roll + transcript (.srt / .txt / .md) for word-level
     timestamps. OFFER auto-transcription (remotion-captions skill) — never make
     the user hand-transcribe. If audio isn't recorded yet, take the script but
     flag timing as provisional. -->
- **Transcript file:** · **Word timestamps:** yes / provisional

### 6.2 · If no dialogue: segmented script
<!-- Line-spacing convention — single break = sequential, same scene (line B
     replaces line A); blank line between = new scene with a text-free gap.
     Parse the user's script, then ECHO THE TABLE BACK for confirmation before
     marking ✅ — pasted text is full of accidental breaks.
     Emphasis (6.3): **bold** marks high-emphasis words — they land on strong
     beats and linger. Mark inline here, nowhere else. -->
| Scene | Line(s) | Flow | Emphasis words |
|---|---|---|---|
| 1 | | <!-- sequential / gap-after --> | |

- **Visual-only scenes:** <!-- scenes with no copy (product showcase etc.) — place them in the scene order above -->
- **Feasibility (klik-anim §A12 — computed at discovery, before the gate):**
  Σ per-line `max(0.70s, 0.25s + chars ÷ 17)` = ___ f  vs  duration ___ f.
  <!-- Over budget → cut lines or extend duration WITH THE USER, now. -->

## 7 · Music

- **Timing role:** <!-- no dialogue → music DRIVES timing (BPM/energy grid) · dialogue → background mood only, animation follows speech -->
- **Track:** <!-- file/link · WHO supplies it · licensed for this use? (real blocker for client work) -->
- **Grid:** <!-- run scripts/analyze-audio.py → BPM · first downbeat frame · frames-per-beat. Paste here; verify vs hand-counted beats. -->
- **Music map** <!-- paste the analyzer's MUSIC MAP; verify by ear (drop = drop? bar phase right?).
     One row per section — this is what klik-anim §A16 (element motion character)
     and klik-cam CAM-5 (camera activity) build from. -->
| Section (bars) | Frames | Tier 1–5 | Lead (bass/mid/high) | Attack · sustain | Pattern notes (K/S/H) | Motion directive |
|---|---|---|---|---|---|---|
| | | | | | | <!-- e.g. "tier 5 bass drop → hero device + camera hit" — filled with the user at storyboard --> |
- **If no track yet:** internal pulse grid at <!-- e.g. 30f --> ; re-time when the track lands (note the cost).

## 8 · Camera & pacing dials · composition model

<!-- Two 1–5 dials, set once as GLOBAL defaults for the first draft. Mechanics
     live in the skills (klik-cam C0 camera, klik-anim C0.5 pacing) — record
     VALUES here. Per-scene overrides are allowed later but must be recorded,
     never improvised. -->
- **Camera movement (klik-cam C0): <1–5>** — <!-- one-line rationale tied to brand energy -->
- **Pacing (klik-anim C0.5): <1–5>** — <!-- how fast & steep every curve is, motion and camera alike -->
- **Composition model (klik-anim `references/layout.md`): <fixed anchor | accretion artboard | growing line | world-space | annotation layer>** — <!-- default: fixed anchor. Anything else changes the downstream hold arithmetic (accretion budgets in the reading pocket and excludes demoted copy) and may add a production dependency (world-space needs a 3D/live plate; annotation needs a plate worth annotating). -->
- **Energy arc (klik-anim §A18): <music-map tier curve | ramp | wave | cold open | plateau-drop>** — <!-- ONE shape for the whole piece. Music-driven → the map's tier row above IS the arc. No music → pick a shape and sketch it per section (e.g. "1-2-3-5-2"). Holds concentrate in its valleys; hero devices spend at its peaks; C0.5 local overrides are its slope. QA measures the render against this row (scripts/measure-motion.py). -->
- **Local overrides:** <!-- none yet / "scene N: pacing 2 — slow reveal (arc valley)" -->

---

## Open questions
<!-- ⬜ = tracked risk. Anything guessed above is marked (inferred) and listed here. -->
- ⬜

## Amendments
<!-- post-approval changes only: date — what changed — why — user-approved -->
