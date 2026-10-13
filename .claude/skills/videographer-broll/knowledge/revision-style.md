# Knowledge: the "Re:Vision method" b-roll/animation style

Backs: `adapters/broll-director.md`. Source study: 18 videos (14 from
revision-prod.co.il, 4 from Instagram `@itzyehuda`) run through Gemini's agentic
video understanding (`gemini-3.8-flash`, `"processing":"agentic"` on
`POST /v1beta/interactions`) on 2026-09-07, 125 b-roll inserts catalogued with
timestamps (counted directly from the raw insert arrays - the analysis agents'
own self-reported synthesis tallies said 117, which was wrong; trust the script
count, not the model's arithmetic). Raw JSON: `E:/FromC/projects/testimonial editor/plans/revision-research/revision-yt-analysis.json` and `revision-ig-analysis.json` in that same folder.

Who: Re:Vision Studio (Holon, Israel), founder Yehuda Chanimov. Sells a combined
"cinematic content + paid campaigns" system to Israeli SMBs (fitness studios,
barbershops, DJs, real-estate/solar, aesthetics clinics). Site is a pure lead-gen
funnel; the actual portfolio lives in 14 embedded YouTube (unlisted) videos plus
his personal-brand Instagram, which doubles as an agency demo reel.

## Two registers, not one style

**Client-facing site videos** (5 testimonials + 9 showcase reels): restrained,
professional, accent color matched to the CLIENT's niche/brand, not a fixed
house color. Real client footage, real numbers, real product shots.

**Personal Instagram** (`@itzyehuda`): a fixed house signature (gold/yellow +
cyan/mint), far more aggressive pattern-interrupts, and outright VFX set-pieces
(a talking cigarette, a superhero lightning transformation, a stadium crowd
composited behind a scooter). This track exists to prove production capability
as much as to teach - treat IG-track techniques as the "wow" tier, site-track as
the "credible proof" tier. A new client's testimonial should default to the
site-track restraint; a house/Kivi demo reel can borrow the IG-track energy.

## B-roll type taxonomy + combined frequency (125 inserts, 18 videos)

| broll_type | site (14 vids) | IG (4 vids) | total | what it is |
|---|---|---|---|---|
| activity_broll | 21 | 20 | 41 | Real behind-the-scenes/real-life footage of the subject doing the thing (gym reps, crew filming, barber cutting) - the single most-used technique everywhere |
| motion_graphic | 23 | 0* | 23 | 2D/3D animated metaphor or schematic (funnel, pyramid, growth chart, crowd of avatars) - **100% full-screen, talking head never visible during these** |
| graphic_card | 18 | 3 | 21 | Typographic card: ID badge, numbered list item, stat card, end card - a mix of full-bleed cards (~12 of 21) and lower-third/badge overlays on the still-visible speaker (~8 of 21) |
| prop_cutaway | 12 | 3 | 15 | A physical object (product, brain model, DJ controller, business card) shot or 3D-rendered in isolation |
| vfx_composite | 0* | 9 | 9 | Full compositing: crowd generated behind the subject, lightning/superhero effects, stadium/tornado set-pieces - **100% full-screen animated environment** |
| screen_recording | 9 | 0 | 9 | Real UI capture - Instagram profile scroll, software dashboard, phone mockup |
| second_angle | 3 | 1 | 4 | Cut to a genuinely different camera angle on the SAME subject/moment (no new asset needed) |
| before_after_split | 2 | 0 | 2 | Split-screen or scrolling comparison of two real photos/states |
| finished_product_broll | 0 | 1 | 1 | Cut to the polished FINAL deliverable itself (a client's finished video-within-the-video) |

\* `motion_graphic` and `vfx_composite` are the same underlying idea (an invented
visual, not literal footage) — the site track keeps it as flat 2D/3D graphic
design; the IG track escalates it to full photoreal VFX compositing. Route both

## Full-screen animation takeovers are their own placement mode, not just a cutaway flavor

~44 of 125 inserts (35%) — every `motion_graphic`, every `vfx_composite`, and
about 12 of 21 `graphic_card` inserts — don't cut AWAY from the talking head
alongside it, they REPLACE the frame entirely with a designed animation or VFX
environment, timed to land on the exact word or phrase it illustrates. Proof
this is content-driven, not decorative: "videos reaching 40,000, 200,000 views"
lands on a full-frame counter animating 40,000→200,000; "wanted something that
would generate customer traffic" lands on a full-frame 3D funnel with client
silhouettes tumbling in. The remaining ~8 `graphic_card` inserts are the gentler
pattern - a lower-third badge or stat overlaid on the still-visible speaker, not
a takeover.

For `broll-director`, this means the dispatch table needs a real branch for
"full-screen replacement" (render a standalone HyperFrames scene, cut to it,
cut back) distinct from "overlay/insert" (composite on top of the existing
shot) - they're mechanically different render jobs, not two flavors of the same
cutaway.
through the same decision branch in the adapter, pick the tier by budget/brand.

## Typography system

**Site-track (client-matched accent):** ultra-bold geometric Hebrew sans-serif
(Heebo/Ploni-style weight), centered lower-third to vertical-center. Solid white
body text, bold accent color on the emphasized/trigger word only (not the whole
line). Accent color is picked per client register, not fixed:
- cyan/teal `#00F5D4` - tech, analytical, real-estate/solar, "system" pitches
- lime/mint green `#10B981` / `#00FFCC` - fitness, DJ/nightlife-adjacent business content
- magenta/purple `#FF007F`-ish gradient - provocative-question hooks, insurance/finance, nightlife
- olive/toxic green - military/combat-fitness niche
Motion: pop-in with a small scale-bounce (100% -> ~108% -> 100%), synced to
speech transients, plus a whoosh/click SFX. Numbers/metrics render as animated
roll-up counters, not static text.

**IG house signature:** ultra-bold gold/yellow `#FFD700` headline type with
heavy black drop shadow, white medium-weight body copy, both centered, NO pill
boxes or background shapes. A distinct secondary convention: asterisk-bracketed
"chapter tags" for BTS/vlog narration (`*בריף לצילום*`, `*אקשן!*`) sitting at the
top of frame while conversational subtitles run at the bottom with selective
yellow karaoke-highlight on key words. Listicle-format videos (the "10 things"
reel) use ZERO word-by-word captions - each shot gets one static, ultra-high-
contrast title-card block instead.

## Color grading signature

Baseline: punchy commercial contrast, deep-but-not-crushed blacks, warm/flattering
skin tones, cool complementary background (teal/cyan practicals or shadow tint).
Shallow depth of field with a soft vignette pulling focus to the face. VFX/showcase
pieces pivot to a stylized blockbuster grade: desaturated neutral environment
(cracked desert, overcast sky, hospital-green barbershop parody) punched through
with one saturated emissive color (electric cyan or magenta neon).

## Hook pattern catalog (9 patterns seen)

1. **Shock metric / number pop** - open on the speaker while a huge number
   (`117K`, `503.5K`, `₪1,700,000`) scales in with an SFX hit before context is given.
2. **Provocative question** - direct contrarian/pain-point question as the first
   line, paired with a big kinetic-type card (`"עשתה עליכם קומבינה?"`).
3. **UI/profile scroll** - open directly on a real Instagram/TikTok screen
   recording scrolling before wiping to the talking head.
4. **High-production BTS action hook** - open on a gimbal/softbox shoot in
   progress (over-the-shoulder), establishing "we are a real production" before
   a word is spoken.
5. **POV immersion + humor** - first-person walk into a real location (a
   barbershop) with ambient banter, a `POV:` title, then a comedic fisheye
   lens-lean into camera.
6. **Contrarian opinion + pattern interrupt** - direct eye contact, an
   immediately provocative claim, rapid zoom-punches and neon graphic pops.
7. **Diegetic prop -> supernatural VFX crescendo** - handle a mundane real
   object (a business card) which then triggers a full VFX escalation.
8. **High-concept parody cold open** - drop the viewer into an absurd scenario
   with zero preamble (barbers dressed as surgeons, a talking cigarette).
9. **Dynamic staging / action walk-in** - subject enters frame mid-motion or
   holding a tangible prop, immediately breaking "static talking head" framing.

## The b-roll insertion ruleset (engineering rules for `broll-director`)

1. **IF** the speaker introduces themself/their business in the first 1-10s
   **THEN** show a lower-third ID badge (name, age, role) for 3-5s over the
   PRIMARY shot - don't cut away, just overlay.
2. **IF** the speaker states a number/KPI/metric **THEN** cut to an animated
   roll-up counter or floating metric card, 2.0-3.5s.
3. **IF** the speaker names a concrete tool/product/object **THEN** cut to a
   prop cutaway or 3D render of that object, 1.5-3.0s.
4. **IF** the speaker describes an abstract process/system/workflow **THEN**
   cut to a schematic or metaphor animation (funnel, pyramid, conveyor), 3-6s.
5. **IF** the speaker references the filming/production itself ("shoot day",
   "the crew", "the camera") **THEN** cut to real BTS activity footage, 2-4s.
   This one CANNOT be stock-sourced - it needs the client's own behind-the-
   scenes footage or a generic film-crew archival clip as a weaker fallback.
6. **IF** the speaker contrasts two things (before/after, us/them, this/that)
   **THEN** cut to a split-screen or dual-column graphic, 2.5-4.0s.
7. **IF** the speaker claims a client outcome/result **THEN** cut to a real
   before/after photo pair/scroll with measurement-style framing, 2-3.5s. Never
   fabricate the photos - this rule only fires when the client supplied them.
8. **IF** the speaker makes an abstract/emotional claim with no literal noun
   ("you're not alone", "reach the right people") **THEN** invent a visual
   metaphor (a crowd, a spotlight, a rising light) rather than reaching for
   generic stock - this is the single biggest gap between "generic AI b-roll"
   and Re:Vision's actual craft.
9. **IF** unbroken talking-head dialogue exceeds ~4.5s with none of the above
   triggers firing **THEN** fall back to a punch-zoom (10-15% crop-in, pure
   FFmpeg, no new asset) or a second camera angle if one exists. This is the
   idle-timer safety net that keeps a shot from ever visually flatlining.
10. **IF** it's the final 3-6s of the video **THEN** cut to a brand end-card
    (logo, CTA arrow, instruction), holding to the out-point.
11. **Density floor:** force at least one visual change (new angle, cutaway, or
    graphic) at least every 5-7 seconds even mid-scene, regardless of whether a
    semantic trigger fired. This is what separates the corpus from generic
    talking-head content, more than any single graphic choice.
12. **Density ceiling:** never fire two overlapping cutaways, and don't cut
    faster than ~1.2-1.5s sustained (outside of a deliberate rapid-montage beat)
    - reads as frantic rather than energetic.
13. **Accent-color-to-register match:** pick the graphic accent color by content
    register (see Typography system above), not a single fixed brand color -
    cyan for analytical/technical, green for fitness/energy, magenta for
    provocative/nightlife, gold for authority/listicle framing.

## Representative timestamped examples (verify by scrubbing)

- Metric-pop rule in action: `https://www.youtube.com/watch?v=FOOdkm2ZQ40&t=54s`
  (view counters rolling 40,000 -> 200,000) and `t=0s` (117K/51K frosted cards).
- Process/system schematic: `https://www.youtube.com/watch?v=FOOdkm2ZQ40&t=12s`
  (3D stone "marketing cauldron" funnel).
- BTS/production self-reference: `https://www.youtube.com/watch?v=BuUdCVzv9gk&t=40s`.
- Abstract-claim VFX metaphor (rule 8): Instagram reel `DUTX3gtDdGE` at 00:18 -
  speaker composited into a stadium crowd while saying "get attention from as
  many people as possible."
- Idle-timer punch zoom cadence: Instagram reel `DLP-IvJMgss` - a 25s reel with a
  new title-card graphic roughly every 1.0-1.5s, average cut interval ~2.0s.
- Before/after: `https://www.youtube.com/watch?v=aNQgeGCS5uo&t=28s` (aesthetics
  clinic, dashed-line measurement framing on real patient photos).

## What NOT to copy literally

- Don't fabricate metrics, before/afters, or client counts - every numeric/photo
  b-roll in the corpus is a REAL client asset. The adapter must only fire rules
  2 and 7 when real data/photos exist; otherwise skip to a softer fallback.
- The IG-track VFX set-pieces (lightning, tornado, talking objects) are a house
  personal-brand device, not a template to force onto every client testimonial -
  they read as a big creative swing specifically because they're rare even in
  this corpus (9 of 125 inserts, concentrated in 1 of 18 videos).
