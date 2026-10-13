---
name: motion-brief
description: Turn a motion-graphics reference into a script and direction document before anything gets built. Use when someone shares a video reference (YouTube, Pinterest, Vimeo, a local file) and wants "something like this" for their brand; when asked to write a script, beat sheet, storyboard, treatment or direction for a promo, explainer, brand film or sizzle reel; when a film needs its runtime, pacing or sound specced; or when a build is about to start from a one-line brief and a link. Produces the document a Remotion/HyperFrames/After Effects build then follows. Not for building the film itself.
---

# Motion brief

A reference link is not a brief. This skill turns "make me something like this"
into a document someone can actually build from, and, more importantly, catches
the two things that sink these projects:

1. **The reference's palette is almost never the client's palette.** Copying it
   produces a film that is off-brand in frame one.
2. **What people think they hear in a reference is usually not what is there.**
   Measure the audio. Every time.

Write the document. Get it approved. Then build. Building first and briefing
afterwards means discovering the direction was wrong after a full render.

---

## Step 0, Load the brand before you watch anything

Read the project's brand document first (`brand/BRAND.md`, a tokens file, a
design system, whatever exists). You need the palette, the type stack, the voice
and **especially the don'ts** in your head *before* the reference biases you.

If there is no brand doc, ask for one or derive it from the live site, but say
which you did.

Also read any project state (`docs/project/STATE.md` and similar). It is where
you find out that a headline stat is unsourced, or that a claim is contested,
before you put it in a film that is harder to correct than a web page.

---

## Step 1, Get the file

**YouTube.** `yt-dlp` regularly 403s on the default client. Work down this chain
until one succeeds, `android` is usually the one that works when the others don't:

```bash
for c in android ios mweb web_embedded web_safari; do
  yt-dlp -q --no-warnings --extractor-args "youtube:player_client=$c" \
    -f "b[height<=720]/bv*[height<=720]+ba/b" --merge-output-format mp4 \
    -o "ref.%(ext)s" "<URL>" 2>&1 | tail -2
  [ -f ref.mp4 ] && echo "OK: $c" && break
done
```

**Pinterest.** Video pins hide an HLS stream. Open the pin in the browser pane and
pull it out of the DOM, then let ffmpeg do the rest:

```js
JSON.stringify([...document.querySelectorAll('video')].map(v => ({src: v.src, poster: v.poster})))
```

```bash
ffmpeg -y -i "<the .m3u8>" -c copy ref.mp4
```

Expect `Invalid NAL unit size` warnings on Pinterest HLS. Ignore them if the file
probes clean.

**Always probe before trusting it.** A 2 MB download of a 91-second video is a
360p fallback, which is fine for reading composition and useless for reading type.

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate \
  -show_entries format=duration,bit_rate -of default=noprint_wrappers=1 ref.mp4
```

---

## Step 2, Watch it as contact sheets

Never sample one frame at a time. Tile them and read the sheets with vision,
you see pacing and repetition that individual frames hide.

```bash
ffmpeg -y -loglevel error -i ref.mp4 \
  -vf "fps=1/2,scale=380:-1,tile=5x3:padding=4:color=0x666666" sheet_%02d.jpg
```

- `fps=1` for pieces under ~60s, `fps=1/2` for longer.
- 15 tiles per sheet keeps each one readable at vision resolution.
- Time is **row-major**: tile *n* on sheet *s* is at `((s-1)*15 + (n-1)) * interval` seconds.

Two Windows gotchas that will waste a cycle each:

- **`-pattern_type glob` is not supported** in the common Windows ffmpeg builds.
  Copy to numbered files (`t_01.png`…) and use `-i "t_%02d.png"`.
- **`drawtext` needs fontconfig**, which usually isn't present. Don't burn
  timestamps in; infer them from tile position instead.

Then zoom on anything ambiguous rather than guessing:

```bash
ffmpeg -y -ss <sec> -i ref.mp4 -frames:v 1 -vf "crop=W:H:X:Y,scale=1100:-1" zoom.png
```

---

## Step 3, Measure the audio. Do not guess.

This is the step that pays for the skill. People ask for "the sounds" imagining
whooshes and impacts; references in restrained registers often contain none at
all, and adding them breaks the piece.

```bash
# Loudness and dynamics
ffmpeg -hide_banner -i ref.mp4 -af ebur128=framelog=quiet -f null - 2>&1 | tail -12

# Instrumentation and whether sound design exists
ffmpeg -y -i ref.mp4 -lavfi "showspectrumpic=s=1600x420:mode=combined:legend=1:scale=log" spec.png

# Arrangement: where it builds, where it drops
ffmpeg -y -i ref.mp4 -filter_complex "showwavespic=s=1900x260:colors=0xFF532E" wave.png
```

Reading them:

| What you see | What it means |
|---|---|
| Integrated ≈ −22 LUFS, LRA > 7 | Deliberately quiet and dynamic. Editorial register. Do not master this at −14. |
| Integrated ≈ −12 LUFS, LRA < 5 | Loudness-maximised. Trailer/social register. |
| Regular evenly-spaced vertical striations across the band | A struck or plucked instrument played steadily, piano family. |
| Broadband bursts that ramp then stop | Whooshes and risers. **Actual sound design.** |
| Sharp full-height spikes | Impacts and hits. |
| Hard shelf around 15-16 kHz | Lossy codec bandwidth limit from the download, *not* a creative choice. Don't report it as one. |

State every audio claim as measured, with the number. "No impacts" is only
credible if you say you checked the spectrogram for them.

---

## Step 4, Name the register

Write a comparison table. If there is a previous reference for the same client,
compare against that; otherwise compare against the obvious default the client
might have expected. The table is what stops the build inheriting instincts from
the wrong film.

Compare on: **type treatment, cut rhythm, colour count, motion character, sound,
density.** Then reduce the reference to its actual vocabulary, most good pieces
run on three to five devices and nothing else. List them. That list becomes the
build's entire toolkit.

---

## Step 5, The brand collision check (never skip)

Put the reference's system and the client's side by side and map every value:

| Reference | Brand | Where it goes |
|---|---|---|

Then **name the departures out loud**, with reasons. Common ones:

- Reference is cold/neon, brand is warm → remap, and say the hue arc is reversed.
- Reference uses pure `#000`, brand forbids it → use the brand's near-black.
- Reference signals emphasis with opacity → a brand with a strong accent should
  signal it with colour instead. One accent word per line. This is usually the
  single best translation move available, and it gives the film a brand signature
  the reference had no need for.
- Reference sets type microscopically → if the client sells to non-technical
  buyers watching on phones, go larger and **say you did and why**. Matching the
  reference exactly can look more like the reference and convert worse.

Drop the brand's secondary accent if the register won't carry two.

---

## Step 6, Write the script

Default structure unless told otherwise: **problem → solution → what we do → CTA.**

- **Write for the ear.** Short fragments, one idea per line, the way you'd say it.
- **Kill adjectives.** "Powerful, intuitive platform" gives nothing to animate.
- **Ask about numbers before including them.** Stats break a restrained register
  in one frame. In a punchy register they're the best thing you have. If the
  client says no numbers, that also means no counters, no percentages, no stat row.
- **One emphasis device per line**, applied consistently, the accent word.
- **Write a callback.** Answer a complaint from Act I in Act III's own words.
  That single move is what makes a script feel written rather than assembled.
- **Name the load-bearing line**, the promise being sold, the one competitors
  can't copy, and hold it longest.
- **Never lift the reference's copy.** Register and technique are fair game;
  the words are theirs. Write original lines.

Mark the accent word in every line so the reviewer sees the device working.

---

## Step 7, Budget runtime with wordless beats

The mistake is assuming a longer film needs more lines. It doesn't.

**Restrained films are long because of silence, not density.** In a quiet
editorial reference, roughly a fifth of the runtime has no words on screen at
all, passages where the visual vocabulary performs alone, or the frame simply
sits empty. Those beats are what earn the register.

So when a runtime grows, spend it on wordless beats first, and add lines only
when a line earns its place on merit. Then publish a segment table:

| # | Segment | In | Out | Runs | Frames |

Give every segment a frame range at the target fps, mark which are wordless, and
let line pacing **accelerate slightly** across the film, a few tenths of a second
per act. That acceleration is what stops a long, restrained piece reading as slow.

Flag the boldest beat explicitly. An empty frame held five seconds is the thing
most likely to feel wrong on a first watch and right on a third, and it is the
first thing a nervous reviewer cuts. Say so in the document, and give the floor
below which it reads as a mistake rather than a choice.

---

## Step 8, Spec the sound from the measurements

Layers: **bed, drone, build, SFX, silence, master.** Fill each from what you
measured, not from what the genre usually does.

- **Build by adding voices, not by getting louder** in restrained registers.
- **Name where the silence goes.** It is usually the most valuable second.
- **Master target:** −16 LUFS integrated, true peak −1 dBTP for web, and keep LRA
  ≥ 6 if the reference was dynamic. If the reference is far quieter than that,
  say you're deliberately going louder and why.
- **Tell them to audition tracks against the hardest beat**, the wordless one.
  If a track can't hold that, it can't hold the film.
- **Licensing is theirs to sort.** Point at Musicbed / Artlist / Epidemic with
  the search terms. Never imply the reference's own track is available.

---

## Step 9, Separate your calls from theirs

End with the decisions that belong to the client, not to you. Typically:

- Lines that are deliberately sharp and might read as snarky.
- CTA wording, when the film could afford something warmer than the site button.
- Any beat you expect them to want to cut.

Three is about right. More than four and you've pushed your job onto them.

Also add a short **"left out on purpose"** section. Saying what you excluded and
why prevents a reviewer re-adding it in the next round.

---

## Deliverable

A markdown document in the repo (`docs/motion/SCRIPT-<runtime>.md`) as the source
of truth. If the client will review it rather than a developer, also publish it
as an artifact, a script reads far better with each act set on the ground colour
it will actually be shot on, and the accent word live in the type.

Open the document with **"For review. Nothing is built yet."** Ambiguity about
whether a thing exists yet costs a whole round of correspondence.

## Hard rules

- Do not reproduce the reference's script copy, in whole or lightly reworded.
- Do not state an audio characteristic you did not measure.
- Do not silently fix a brand collision, name every departure and its reason.
- Do not put an unsourced claim or contested stat into a film. Check project
  state first; a film is far harder to correct than a page.
- If the client asked for something the reference cannot support, whooshes in a
  film that has none, say so plainly, offer the alternative, and let them choose.
  It can't be both.
