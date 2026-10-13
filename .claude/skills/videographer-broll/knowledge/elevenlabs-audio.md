# Knowledge pack: ElevenLabs audio (music + SFX)

Layer-3 know-how for `adapters/music-sfx.md` + `tools/elevenlabs_music.py`.

## Auth + the scoped-key gotcha (READ THIS)

- Header is `xi-api-key: <key>` (NOT `Authorization: Bearer`).
- The account's key is a **scoped key**. It is valid for generation (TTS, sound-generation,
  music, voices) but **lacks the `user_read` permission**, so:
  - `GET /v1/user` -> **401** (and `GET /v1/user/subscription` -> 401)
  - `GET /v1/voices` -> **200** (124 voices)
- Therefore the auth check (`elevenlabs_music.py check`) hits `/v1/voices`, not `/v1/user`.
  A 401 on `/v1/user` does NOT mean the key is dead - confirmed live 2026-06-30.
- Key lives in `local/.env` as `ELEVENLABS_API_KEY`. It is the user-level key also recorded
  in the memory `api-keys.md`. If it ever truly dies (`/v1/voices` 401s), rotate in the
  ElevenLabs dashboard (login in `api-keys.md`) and update `local/.env`.

## Sound effects (`sfx`)

- `POST /v1/sound-generation`, body `{ "text", "duration_seconds", "prompt_influence" }`,
  `Accept: audio/mpeg`. Returns mp3 bytes.
- `duration_seconds`: ~0.5 to 22. `prompt_influence` ~0.3 (higher = literal, lower = creative).
- Use for: whooshes, impacts, risers, transition stingers, UI clicks, ambience hits.
- Cheap. A 2s stinger is a few credits.

## Music bed (`music`)

- The Music API endpoint/params move faster than the rest of ElevenLabs. The wrapper defaults
  to `POST /v1/music` with `{ "prompt", "music_length_ms" }` and is **endpoint-overridable**
  (`--endpoint`). If you get a 404/422, confirm the current path/params in the ElevenLabs docs
  (Music / "compose") and pass `--endpoint`. Do not hardcode assumptions - the wrapper is
  deliberately thin so the endpoint can be corrected without touching code.
- `music_length_ms`: keep it short and loop. A 15-20s loopable bed beats a 90s unique track
  for cost and for editing (loop to length, duck, fade).

## Mixing guidance (the part that actually matters)

- **Duck the bed** under VO by -16 to -20 dB (sidechain compression or static gain). An
  un-ducked bed buries narration and fails the post-render `loudness` gate.
- Final mix targets `brief.cleanup.loudness_target_lufs` (per platform via render-profiles:
  -14 YouTube/TikTok, -16 IG/LinkedIn) with true peak < -1.0 dBTP.
- Fade bed in/out ~0.5s. Place stingers exactly on transition timestamps from the EDL.

## Cost posture (free-first)

ElevenLabs audio is the one metered path wired into the skill. It is low cost, but still:
generate a bed only when the piece needs one, loop rather than make it long, and skip music
entirely when silence serves (a raw testimonial usually plays better dry). TTS narration is a
separate ElevenLabs path (used by CutSense / HeyGen audio), not this adapter.

## Voices (FYI)

- 124 voices reachable. Default premade: Rachel `21m00Tcm4TlvDq8ikWAM`. The account has no
  custom cloned voices - use premade IDs. Voice work belongs to the TTS path, not music-sfx.
