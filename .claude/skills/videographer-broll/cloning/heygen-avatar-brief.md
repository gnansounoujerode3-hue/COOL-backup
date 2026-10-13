# HeyGen Avatar IV - Recording Brief

## What you're producing

A 2-3 minute video of you reading the consent statement plus your natural-talk content (see [heygen-avatar-script.md](heygen-avatar-script.md)). HeyGen trains an Avatar IV model from this and gives you back an `avatar_id` that can speak any script in your face, your voice cadence, your exact head/hand movements.

## Why HeyGen Avatar IV (not Hedra)

You picked HeyGen. Quick reminder why this was the right call for "clone myself":

- **HeyGen Avatar IV** clones a real person. Your face, your eyes, your voice, your hands moving as you talk. The output looks like you sitting at your desk on a Zoom call. This is what you want for explainers, sales videos, course intros, podcast trailers where you appear.
- **Hedra Character-3** generates novel characters from a single image. Better for stylized avatars, NPC-style mascots, fantasy characters. NOT a "clone yourself" tool.

## Equipment minimum

- **Camera**: Smartphone is fine. iPhone 13+ or any modern Android shoots 4K. Webcam acceptable if it's 1080p+ (Logitech Brio, MX Brio, Insta360 Link). Avoid built-in laptop webcams (the angle is bad and quality is poor).
- **Tripod or stand**: Camera CANNOT shake. Phone tripod, laptop on books, anything stable. No hand-holding.
- **Light**: One soft key light in front of you, slightly above eye level. Ring light is fine. Window with daylight (NOT direct sun) is fine. Two lights (key + fill) is better. Avoid: overhead fluorescent only, single side light (creates harsh shadow), backlight (you become a silhouette).
- **Microphone**: HeyGen extracts voice from the video, so mic quality matters here too. Use the same mic from your PVC session if you have it set up. Lapel mic clipped to shirt is great. Phone built-in mic is acceptable but adds room sound.
- **Headphones**: NO headphones on camera. They look weird on the trained avatar.

## Wardrobe and grooming (this is a permanent decision)

The clothes you wear become your avatar's "always look." Pick once, pick well.

- **Top**: Solid color, mid-tone (not pure white, not pure black). Navy, charcoal, sage green, burgundy all work. Plain crew neck, polo, or button-down. NO logos, NO text, NO busy patterns, NO tight stripes (moiré on camera).
- **Hair**: Style as you usually wear it. The avatar will replicate this style every time. Do not record after a fresh radical haircut.
- **Glasses**: Wear them if you wear them daily. Otherwise don't. Do not switch on/off mid-recording.
- **Beard**: Same logic. Whatever you usually have. Trim it as you usually trim it.
- **Background**: Solid wall, not too busy, not pure white. A plant or one piece of art is fine. NO clutter, NO open doorway, NO windows behind you (light direction).

## Camera framing

- **Headroom**: Top of your head about an inch from the top of frame
- **Crop**: Mid-chest up. Both shoulders fully in frame. Some space on each side of shoulders.
- **Eye line**: Camera lens at eye level. NOT looking up at the camera, NOT looking down.
- **Distance**: 3-4 feet (1 meter) from the lens.
- **Lens**: Avoid wide-angle (distorts face). Phone main camera, NOT ultra-wide. Webcam standard FOV.
- **Format**: Landscape 16:9 (NOT portrait). HeyGen processes both but landscape is universal.

## On-camera technique

- **Eye contact with the lens**, not with yourself in the preview. Tape a small arrow above the lens if needed.
- **Move naturally**. Don't sit frozen. Use your hands as you usually do when talking. The avatar will replicate your gestures, so you want your real range. Don't OVER-gesture; just speak.
- **Speak at your normal pace**. Not slower, not faster. The avatar's lipsync trains on your real speech rhythm.
- **Smile genuinely at moments that warrant it**, not constantly.
- **Pause at end of thoughts**. Two-second silences let HeyGen segment cleanly.

## Recording session structure

**Total time**: 30 minutes (15 min for setup and lighting, 5 min recording, 10 min for retakes)

1. **Setup (15 min)**: Tripod, light, mic, framing test. Record 30 seconds, watch back, adjust.
2. **Consent statement (1 min)**: Read aloud as written in heygen-avatar-script.md Part 1. HeyGen requires this verbatim and it MUST be the first segment.
3. **Natural-talk content (2 min)**: Read heygen-avatar-script.md Part 2. Don't memorize, just have the script visible above or behind the camera. Glance at it; do not read it like a teleprompter.
4. **Pickup takes if needed (10 min)**: Re-record any segment that has bad audio, misframing, or stiff delivery.

## Self-QA checklist (before upload)

Watch the recording fullscreen with sound. Check:
- [ ] Face is well-lit, no harsh shadow on one side
- [ ] Eyes are visible (not lost in glasses glare or shadow)
- [ ] Audio is clear, no room echo, no AC hum, no traffic
- [ ] You speak naturally - not stiff, not exaggerated
- [ ] Hands are visible at least sometimes (frame allows it)
- [ ] Camera does NOT move during the recording
- [ ] Background is consistent throughout
- [ ] Total length over 90 seconds, under 5 minutes (sweet spot 2-3 min)
- [ ] You read the consent statement word-for-word
- [ ] No coughs, sneezes, mid-sentence interruptions

If ANY of these fail, redo the affected segment. The model bakes in flaws.

## File format

HeyGen accepts: MP4, MOV. Recommended:
- **MP4 H.264 / 1080p or 4K / 30fps**
- **One single file** (concat segments before upload)
- **Naming**: `<your-slug>-heygen-<YYYYMMDD>-take-NN.mp4`

If your file is over 500MB, re-encode with ffmpeg before upload to keep things smooth:

```
ffmpeg -i input.mov -c:v libx264 -preset slow -crf 20 -c:a aac -b:a 192k -movflags +faststart output.mp4
```

## Upload flow

1. Go to https://app.heygen.com/avatars
2. Click "Create Avatar" -> "Instant Avatar" or "Avatar IV" (pick Avatar IV - the higher-quality one)
3. Upload the MP4
4. HeyGen will detect your face and prompt you to crop/confirm framing
5. Upload the consent video segment (or trim from the same file)
6. Wait for HeyGen verification (they manually review the consent statement)
7. Training takes 30-60 minutes after approval
8. Find the `avatar_id` in dashboard (looks like `Daisy_Sitting_Sofa_Front_public`)
9. Find the matching `voice_id` they extracted (you can also override with your ElevenLabs PVC voice once it's trained)
10. Save both to your local config:

```
local/personal.json ->
  avatar.heygen_avatar_id = "<heygen-avatar-id>"
  avatar.heygen_voice_id  = "<heygen-or-pvc-voice-id>"
  avatar.heygen_status    = "ready"
```

Optionally keep a registry file for multiple avatars:

```
local/heygen-avatar-registry.md ->
| avatar_id | voice_id | description | recorded | wardrobe |
|---|---|---|---|---|
| <heygen-avatar-id> | <heygen-or-pvc-voice-id> | Main personal avatar | YYYY-MM-DD | <wardrobe note> |
```

## Combining with ElevenLabs PVC voice

When your PVC voice trains (3-4 weeks after you record voice), you can use the HeyGen avatar's video with the ElevenLabs voice for higher voice quality:

1. Generate audio from ElevenLabs PVC: `POST /v1/text-to-speech/<pvc-voice-id>`
2. Upload that audio file to HeyGen as a "custom voice" for the avatar
3. Render the video with avatar + custom voice

The orchestrator's `heygen.md` adapter handles this automatically when both `voice_id` and `avatar_id` are set in the brief.

## After it's trained - test render

Send one test script to confirm it speaks like you:

```
curl -X POST https://api.heygen.com/v2/video/generate \
  -H "X-Api-Key: <heygen-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "video_inputs": [{
      "character": {"type": "avatar", "avatar_id": "<your-avatar-id>", "avatar_style": "normal"},
      "voice": {"type": "text", "input_text": "Hello, this is a test. One, two, three.", "voice_id": "<your-voice-id>"}
    }],
    "dimension": {"width": 1920, "height": 1080}
  }'
```

Watch the result. If the lips sync, the head moves naturally, and the voice sounds like you - the avatar is ready. Save the IDs and the orchestrator will dispatch to it.

## What can go wrong + recovery

| Symptom | Fix |
|---|---|
| HeyGen rejects the consent video | You misread the statement. Re-record the consent segment word-for-word. |
| Avatar looks waxy / overly smooth | Your light was too flat (no shadows = no depth). Re-record with a softer key light at 30 degrees off-axis. |
| Eyes look dead in output | You stared at the screen instead of the lens. Re-record with eye contact directly into the lens. |
| Lipsync is off | Audio was out of sync in the upload (rare). Re-encode with ffmpeg flag `-async 1`. |
| Avatar's voice doesn't sound like you | HeyGen's voice extraction was poor. Use your ElevenLabs PVC voice instead once it's ready. |
