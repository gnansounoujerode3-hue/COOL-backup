# Cloning Setup

Recording briefs for cloning your voice (ElevenLabs PVC) and persona (HeyGen Avatar IV). Both are one-time captures that produce reusable assets the orchestrator can dispatch to.

## Files

- [elevenlabs-pvc-brief.md](elevenlabs-pvc-brief.md) - Voice recording: equipment, room, pacing, file specs
- [pvc-script.md](pvc-script.md) - The 30-45 min script template to read aloud for PVC training (customize Parts 2 and 4 with your own content first)
- [heygen-avatar-brief.md](heygen-avatar-brief.md) - Persona video recording: camera, lighting, framing, on-camera prompt
- [heygen-avatar-script.md](heygen-avatar-script.md) - The 2-3 min on-camera content brief (substitute your name + your block content first)

## Workflow

1. **Pick a recording day**. Block 90 min for voice (allows pickups), 30 min for video.
2. **Read the briefs end-to-end first** - some setup decisions are ordered (room treatment before recording, etc.).
3. **Customize the scripts** - replace `<YOUR FULL NAME>` and the placeholder content blocks with your own text BEFORE pressing record.
4. **Record voice first**. Easier to redo, no makeup/wardrobe variables.
5. **Record video second**. Wear what you'd want your AI avatar to "always wear" (this becomes your canonical AI look).
6. **QA your own recordings** before uploading. The briefs include a checklist.
7. **Upload + start training**:
   - ElevenLabs PVC: dashboard, manual upload, ~3-4 weeks training
   - HeyGen Avatar IV: dashboard, upload + consent video + verification, 30-60 min training
8. **Save the IDs to your local config**:
   - ElevenLabs `voice_id` -> `local/personal.json` -> `voice.elevenlabs_pvc_voice_id`
   - HeyGen `avatar_id` + `voice_id` -> `local/personal.json` -> `avatar.heygen_avatar_id` and `avatar.heygen_voice_id`

## After IDs are saved

The orchestrator's `avatar-explainer.md` template and `heygen.md` adapter will read the avatar/voice IDs from `local/personal.json`. You can then say "make me an avatar video saying X" and it dispatches HeyGen with your trained avatar + voice.

For Reels/Shorts narration in your voice (no on-camera): the ElevenLabs PVC voice plugs into HyperFrames TTS, video-use animation slots, or any TTS-driven template. Use `voice_id=<your-pvc-id>` in `brief.provider_specific.hyperframes.voice_id` etc.
