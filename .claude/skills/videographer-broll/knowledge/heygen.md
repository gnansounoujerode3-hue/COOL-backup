# Knowledge pack: HeyGen (avatar lipsync)

Layer-3 depth behind `adapters/heygen.md`. Avatar talking-head from a script, no camera.

## Auth + shape

- Header `X-Api-Key: <HEYGEN_API_KEY>`. V2 endpoints under `https://api.heygen.com/v2/...`.
- Two-step: `POST /v2/video/generate` with `{ video_inputs: [{ character, voice, background }] }`
  -> `{ video_id }`; then poll `GET /v1/video_status.get?video_id=...` until `status: completed`,
  which returns the `video_url`. Download promptly.

## Inputs from brief

- `provider_specific.heygen.avatar_id` - from the registry `local/heygen-avatar-registry.md`.
  If empty, the orchestrator routes to Hedra instead (avatar_id present -> HeyGen, else Hedra).
- `provider_specific.heygen.voice_id` - premade or cloned (ElevenLabs voice if using the audio
  path; HeyGen native voice otherwise).
- `provider_specific.heygen.script` - the narration text.

## Behaviour / limits

- Slow: renders can take many minutes to ~90 min depending on length + queue. Score it low on
  latency in selection; do not block a session waiting - dispatch and check back.
- Continuity across clips is moderate: the same avatar_id + voice_id keeps the presenter
  consistent, but framing/background drift between separate generations - pin background + ratio.
- Cost: metered per clip/minute. Free-first applies: an avatar explainer is justified when no
  on-camera talent exists; otherwise prefer real footage (CutSense) or kinetic type (HyperFrames).

## Cloning (Avatar IV)

One-time avatar capture brief lives in `../cloning/heygen-avatar-brief.md`; once trained the
avatar_id goes in `local/personal.json` and the registry. Pair with the ElevenLabs PVC voice
clone for a matched face+voice.

## When to pick HeyGen vs alternatives

- HeyGen: clean corporate presenter, premade or cloned avatar, script-to-talking-head.
- Hedra: more emotive/expressive face, alternate when HeyGen feels stiff.
- HyperFrames + TTS: no avatar at all - kinetic typography over narration. Cheaper, no
  uncanny-valley risk, but no human face.

## See also

- Adapter: `../adapters/heygen.md`
- Multi-clip consistency: `../brand/consistency-rules.md`
