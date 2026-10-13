# ElevenLabs Professional Voice Clone (PVC) - Recording Brief

## What you're producing

A pristine 30-45 min monologue recording of you reading [pvc-script.md](pvc-script.md). ElevenLabs trains a voice model from this, takes ~3-4 weeks, returns a `voice_id` that talks exactly like you.

## Why this brief is strict

PVC quality is bottlenecked by your *worst* 5 seconds, not your best. One reverb-y room sound or one mouth click in the training set bakes into the model and shows up in every output. Spend the time once.

## Equipment minimum

- **Microphone**: USB minimum. Recommended (cheap to good): Samson Q2U ($60), Rode NT-USB+ ($170), Shure MV7 ($250). XLR + interface if you have it. NEVER laptop built-in mic.
- **Pop filter**: Foam ball or mesh on mic. Removes plosives.
- **Mic stand or arm**: Hold-in-hand introduces handling noise. Get it fixed.
- **Headphones**: For monitoring. Open-back or earbuds OK. NOT speakers (they leak into the mic).

## Room treatment (most-overlooked)

Goal: kill reflections so the recording sounds like you in a soft place, not in a tile bathroom.

- Walk-in closet with clothes is the cheap pro hack
- Bedroom with blankets / duvets draped over chairs around the mic
- Avoid: kitchens, tiled rooms, large empty rooms, rooms with window AC
- Quiet hour: pick a time when fridge cycle is off if possible, no street noise, no AC, no kids/pets, phones in another room

**Test before committing**: record 30 seconds, listen with headphones eyes closed. If you hear ANY room (echo, hollowness), retreat to a softer space.

## Mic technique

- **Distance**: 6-8 inches from mouth (a hand-span)
- **Off-axis 15 degrees**: Mouth aimed slightly past the mic, not directly at it. Reduces plosives further.
- **Gain**: Peaks at -6 dB, average around -18 to -12 dB. Never red-line. Never under -30 dB.
- **Posture**: Sit upright, mic at mouth level. No "looking down at notes" voice.

## Recording session structure

**Total time**: 90 minutes (45 min recording + 45 min for retakes, breaks, file ops)

1. **5 min warm-up** - read first paragraph 2x, settle into pace
2. **15 min Section A** (phonetic warmup) - read pvc-script.md Part 1
3. **5 min break** - water, no coffee/dairy (mucus), no shouting
4. **15 min Section B** (your voice content) - pvc-script.md Part 2
5. **5 min break**
6. **10 min Section C** (emotional range) - pvc-script.md Part 3, do each register section
7. **5 min Section D** (technical terms) - pvc-script.md Part 4

## File format

ElevenLabs accepts: MP3, WAV, FLAC, M4A. They prefer:
- **WAV 48kHz / 24-bit / mono** (or 44.1kHz / 16-bit acceptable)
- **One single file** (not split). Concat segments before upload.
- **No processing**: NO compression, NO EQ, NO noise reduction, NO normalization. Send dry.
- **Naming**: `<your-slug>-pvc-<YYYYMMDD>-take-NN.wav`

## Self-QA checklist (before upload)

Open the file in Audacity (free) and check:
- [ ] Waveform never clips (no flat tops at top/bottom)
- [ ] Average loudness around -18 to -12 dB (not too quiet, not red)
- [ ] Spectrogram is "clean" - no constant horizontal lines (= AC hum, fridge, fan)
- [ ] No reverb on tails of words ("you" should die immediately, not echo)
- [ ] No background voices, doors, traffic, dogs
- [ ] Total duration >= 30 minutes (45 ideal, more is fine)
- [ ] One single voice (you), no laugh tracks, no music
- [ ] You sound like you - not "voiceover voice"; your normal speaking voice

If ANY of these fail, redo the affected section. The model bakes in flaws.

## Upload flow

1. Go to https://elevenlabs.io/app/voice-lab
2. Click "Add Voice" -> "Professional Voice Cloning"
3. Confirm consent (you own the rights to your voice)
4. Upload the WAV(s)
5. Submit name: `<Your Name> PVC`
6. Submit description: brief one-line note describing your typical speaking tone (e.g., "Conversational, mid-tempo, no em-dashes")
7. Wait 3-4 weeks for ElevenLabs to train
8. When ready, find the `voice_id` in the dashboard (looks like `21m00Tcm4TlvDq8ikWAM`)
9. Save it to your local config:

```
local/personal.json -> voice.elevenlabs_pvc_voice_id = "<voice_id-here>"
local/personal.json -> voice.elevenlabs_pvc_status = "ready"
```

## After it's trained

Use it via the ElevenLabs key from your `local/.env`. Example API call:

```bash
curl -X POST https://api.elevenlabs.io/v1/text-to-speech/<voice_id> \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test. One, two, three.",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
  }' \
  --output test.mp3
```

## Why not Instant Clone instead

Instant Voice Clone (1-3 min audio, immediate) is genuinely good. PVC is *unmistakably you*. For any branded content where listeners know your voice, PVC matters. For dispensable Reel narration, Instant is fine. PVC is the better long-term ROI if you plan to publish at scale.
