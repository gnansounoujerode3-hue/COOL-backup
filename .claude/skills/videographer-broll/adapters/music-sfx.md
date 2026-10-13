# Adapter: music-sfx (ElevenLabs Music + SFX, optional Suno)

## What this tool does

Generates a **music bed** (score under a video) and **sound effects / stingers**
(whooshes, impacts, transition hits) from text prompts, via ElevenLabs. Used in the
`edit` / `compose` stage of a pipeline, or any time `brief.output.music == "auto"`.

Engine: [`../tools/elevenlabs_music.py`](../tools/elevenlabs_music.py).
Deep notes + the scoped-key gotcha: [`../knowledge/elevenlabs-audio.md`](../knowledge/elevenlabs-audio.md).

This is the one audio-generation path in the skill. It is **metered** (ElevenLabs
credits), but low cost. Free-first still applies: only generate a bed/stinger when the
piece actually needs one, and prefer a short loop over a long unique track.

## When the orchestrator dispatches here

| Trigger | Notes |
|---|---|
| `brief.output.music == "auto"` | Generate a bed matched to the tone |
| Pipeline `edit` stage needs a score bed (explainer / documentary / cinematic) | Bed under VO, ducked |
| User asks for "a whoosh", "transition sound", "impact", "stinger" | SFX |
| A cut needs energy between shots | SFX stinger on the transition |

Not for: TTS narration (that is the ElevenLabs TTS path used by CutSense / HeyGen audio),
licensed commercial tracks (use a real library), or when the user supplied a music file
(`brief.output.music` is a path - just use it).

## Commands

```bash
# Free reachability check (the smoke - no credits spent):
python tools/elevenlabs_music.py check

# A transition stinger (cheap):
python tools/elevenlabs_music.py sfx --text "cinematic whoosh transition" --duration 2 \
  --out ${VIDEO_JOBS_DIR}/<brief_id>/audio/whoosh.mp3

# A score bed from a prompt:
python tools/elevenlabs_music.py music --prompt "warm lo-fi piano under a flower-shop story, 80 bpm, hopeful" \
  --ms 20000 --out ${VIDEO_JOBS_DIR}/<brief_id>/audio/bed.mp3
```

`check` proves the key authenticates (it lists voices - a free GET). It does NOT use
`/v1/user`, because the account's scoped key lacks `user_read` and would 401 there
while being perfectly valid for generation. See the knowledge pack.

## Inputs read from brief

```jsonc
"output": { "music": "auto" },          // or a path (use as-is) or "none"
"audio": {                               // optional, under provider_specific.music_sfx
  "music_prompt": "warm lo-fi piano, hopeful, 80 bpm",
  "music_length_ms": 20000,
  "loop": true,
  "duck_under_vo_db": -18,               // how far to duck the bed under narration
  "stingers": [
    { "at_transition": 2, "text": "soft whoosh" }
  ]
}
```

## How the bed/stingers get used (edit stage)

This adapter only *generates* the audio files. The edit stage (CutSense / Remotion /
ffmpeg) places them:

- **Bed**: loop to the timeline length, duck `-16` to `-20` dB under the VO (sidechain or
  static gain), fade in/out 0.5s.
- **Stingers**: drop on transition timestamps from the EDL.
- Final mix still passes the post-render **loudness** gate (integrated LUFS to
  `brief.cleanup.loudness_target_lufs`, true peak < -1.0 dBTP). A hot music bed is the
  usual cause of a loudness FAIL - duck harder.

## Suno (optional, not wired)

Suno produces more "song-like" beds (intro/verse/structure) than ElevenLabs Music. It is
documented here but NOT wired: this account has no stable Suno API key. If a piece needs a
structured song rather than a loopable bed, generate it in the Suno app and drop the file
in as `brief.output.music = "<path>"`. Revisit wiring when a Suno API key exists.

## Anti-patterns

- Generating a long unique track when a 15-20s loop would do. Free-first: loop it.
- Forgetting to duck. An un-ducked bed buries the VO and fails the loudness gate.
- Using `/v1/user` to check auth - scoped keys 401 there. Use `check` (it hits /v1/voices).
- Treating SFX as music. `sfx` caps ~22s and is for hits/whooshes; `music` is the bed.
- Burning credits on a bed for a piece that is better silent (a raw testimonial often is).
