# Adapter: Veo 3 (Google DeepMind)

> **Status: documented, NOT yet wired into the orchestrator's default tool table.**
> Veo 3 is captured here as a reference adapter. It is **not** in [`../SKILL.md`](../SKILL.md)'s "Available tools" table on purpose — fal-seedance remains the default for `none` source. Add the row when you decide to make Veo 3 a first-class option. Until then, the orchestrator only routes here on explicit user request ("use veo3", "veo 3", "use Google's video model").

## What this tool does

Veo 3 generates a fresh video clip with **native synchronized audio** (dialogue, sfx, ambient sound) from a text prompt and optional image. Hosted by Google via Vertex AI / Gemini API and via Google Flow consumer UI. Strengths vs fal-seedance: native multilingual dialogue with mouth-sync, stronger physics on environment shots, longer-form sequences via Flow's Scene Builder.

## When the orchestrator dispatches here

Currently only on **explicit user request**. Candidate row to add to the dispatch tables when ready (see "Promotion checklist" at bottom):

| Source type | Intent | Why Veo 3 over fal-seedance |
|---|---|---|
| `none` | `dialogue_with_native_audio` | Veo 3 is the only supported tool that lipsyncs spoken dialogue inside the generated clip itself (no separate ElevenLabs + lipsync step). |
| `none` | `multilingual_ad`, `hebrew_dialogue_clip` | Hebrew dialogue trick (see below) produces authentic Israeli-sounding speech without forcing Hebrew text rendering. |
| `image` | `start_frame_only` (long sequence) | Veo 3 via Flow's Scene Builder can extend a clip by carrying a frame forward as the next start frame, useful for sequences that exceed Seedance's 15s cap. |

## Inputs read from brief

- `brief.prompt` — the prompt body. Veo 3 responds best to **JSON-formatted prompts** (see "Structured prompt format" below).
- `brief.output.aspect` — Veo 3 supports 16:9 and 9:16 natively
- `brief.output.length_target_sec` — Veo 3 default ~8s clip length per generation; chain via Flow's Scene Builder for longer
- `brief.source.image_url` — for image-to-video mode (start frame)
- `brief.notes.dialogue` — if dialogue is required, place spoken lines here (see Hebrew trick)

## Structured prompt format (the JSON template)

Veo 3 reportedly produces noticeably more coherent output when the prompt is supplied as a structured JSON object rather than free-form prose. Empirical claim from the Guy Aga 2025/2026 course (Module 5, Video Generation), worth A/B testing on your own briefs before committing.

```json
{
  "subject": "...",
  "action": "...",
  "environment": "...",
  "camera_movement": "...",
  "lighting": "...",
  "audio": "...",
  "dialogue": "...",
  "style_notes": "..."
}
```

Field semantics:

- **subject**: who or what is on camera. Include physical description.
- **action**: verb-phrase, what subject does over the clip duration.
- **environment**: location, time of day, weather, background details.
- **camera_movement**: named camera moves (push-in, dolly left, crane up, handheld, locked-off). Avoid vague "cinematic camera."
- **lighting**: named recipes (Rembrandt, Loop, Split, golden hour, neon practicals, hard rim).
- **audio**: ambient and effect sounds. Veo 3 will generate these natively.
- **dialogue**: spoken lines (see Hebrew trick if applicable).
- **style_notes**: film stock, lens choice, color grade reference, aspect intent.

Pass the JSON object stringified into the prompt field. Some Veo 3 surfaces accept it as a literal JSON object; others want it as a JSON-formatted string. Test both on first call.

## Hebrew dialogue trick

Naively asking Veo 3 to "say in Hebrew: שלום עולם" produces broken Hebrew that fails lipsync because the model's training data on Hebrew speech is sparse. The reliable workaround:

> **Append `"says in English with Hebrew accent"` to the dialogue line, with the actual content written in English.**

Example:

```json
{
  "dialogue": "Welcome to our store, says in English with Hebrew accent",
  ...
}
```

Produces authentic Israeli-sounding spoken English that reads naturally to Hebrew-speaking audiences. For dubbed Hebrew dialogue specifically (the line must be in Hebrew on screen and on audio), generate the clip with English dialogue + accent, then dub in post via ElevenLabs Hebrew voice clone — the lipsync drift is small enough on Israeli-accented English that the dub reads correctly.

Source for both the JSON trick and the Hebrew accent trick: Guy Aga, *"יישומי בינה מלאכותית - שימוש מעשי"* (2025/2026), Module 5 Video Generation. Empirically verified by the instructor; not yet independently A/B-tested in this skill.

## Endpoints

Veo 3 has two practical access paths. Pick based on whether you need API automation or a richer manual edit surface:

1. **Vertex AI / Gemini API** (programmatic). Requires Google Cloud project with billing + Vertex AI access. Standard Google Cloud auth (service account or OAuth). Endpoint shape: `POST https://us-central1-aiplatform.googleapis.com/v1/projects/<PROJECT_ID>/locations/us-central1/publishers/google/models/veo-3:predict` (subject to GA renaming — confirm against current Google docs at runtime).
2. **Flow consumer UI** (`flow.google.com`). Bundled with Google Pro / Ultra subscription. Manual UI driving via Orellius MCP browser bridge is feasible for one-off clips; not appropriate for batch automation. Strength here is the Scene Builder for chaining clips (carry-forward frame).

For batch / brief-driven dispatch from this orchestrator, use Vertex. For exploratory / first-time-with-Veo-3 work, use Flow manually first.

## Pre-flight checks

1. Google Cloud auth configured: `gcloud auth application-default login` has produced valid credentials, OR a service account JSON path is in `local/.env` as `GOOGLE_APPLICATION_CREDENTIALS`.
2. Vertex AI API enabled on the project (`gcloud services list --enabled | grep aiplatform`).
3. Veo 3 model is available in the chosen region (region availability has shifted between previews and GA — check first).
4. `<brief.output_dir>/veo3/` exists.
5. ffmpeg on PATH (for any post-processing).

## Output location

- Raw generated clip: `<brief.output_dir>/veo3/raw_NN.mp4`
- Captioned final: `<brief.output_dir>/veo3/out_NN.mp4`

## Failure modes + recovery

1. **Generation request rejected for safety** (a generic content policy hit on people, brands, real-world settings). Reword the subject or environment to avoid the trigger; never bypass with synonym tricks.
2. **Mouth movement does not match the spoken line** — Veo 3 is sensitive to dialogue length vs clip length. Shorten the dialogue or extend the clip. The Hebrew accent trick is more sensitive to this than English.
3. **JSON prompt rejected** — some Veo 3 surfaces want plain prose. Fall back to flattening the JSON to a single paragraph: `"<subject>, <action>, in <environment>, shot with <camera_movement>, lit by <lighting>, audio: <audio>."`
4. **Aspect ratio drift** in 9:16 portrait outputs (subject too small, too much headroom). Add `"framing: medium close-up, eyes at upper third"` to `style_notes`.

## Brief field -> request mapping

| Brief field | Request field / behavior |
|---|---|
| `prompt` | `instances[0].prompt` (stringified JSON or flattened prose) |
| `output.aspect` | `parameters.aspectRatio` (`"16:9"` / `"9:16"`) |
| `output.length_target_sec` | `parameters.durationSeconds` (clamped to model's supported range) |
| `source.image_url` | `instances[0].image.bytesBase64Encoded` (download + base64 first) |
| `notes.dialogue` | embedded inside the JSON prompt's `dialogue` field |
| `output.count` | one request per output (Veo 3 returns one clip per call) |

## Multi-clip consistency

The same multi-clip discipline applies as for fal-seedance and HeyGen — read [`../brand/consistency-rules.md`](../brand/consistency-rules.md) before any multi-clip dispatch. Veo 3 is stateless across calls; clothing, props, and setting will drift between clips unless byte-identical Lock blocks are pasted into every prompt's `subject` + `style_notes` fields.

## Promotion checklist (before adding to SKILL.md tool table)

When ready to make Veo 3 a default option for new dispatches, do all of these in order:

1. Add a row to `<skill_root>/SKILL.md` "Available tools" table.
2. Add the matching row(s) to `<skill_root>/decision-tree.md`.
3. Pick or create the matching template(s) in `<skill_root>/templates/`.
4. Update `<skill_root>/templates/INDEX.md` if a new template was added.
5. Run a smoke test: a 1-clip and a 2-clip multi-shot brief with the Lock block discipline.
6. Set the env vars in `local/.env`: `GOOGLE_APPLICATION_CREDENTIALS` (path), `GCP_PROJECT_ID`, `GCP_REGION`.
7. Run `python qa/run-qa.py <brief_id>` and confirm it passes the standard duration + audio + face-safety checks on a Veo 3 output.

Until promoted, Veo 3 only fires on explicit user request and reads this file as the source of truth.

## Notes for fork mode

Veo 3 generation latency is comparable to HeyGen / Hedra (60-180s typical, longer at peak). When forked alongside fal-seedance, the user should expect parity in wall-time. Quality differs in audio coherence (Veo 3 wins on synced dialogue) and in subject realism on close-ups (depends on prompt — neither dominates).

## Reference

- Course source for the JSON template + Hebrew accent trick: `C:\Users\raviv\Downloads\courseiq-package\courseiq\outputs\guyaga_manual_2026-05-03\deliverables\course_gems.md` (item Tier 1 #3).
- Original course: Guy Aga, *"יישומי בינה מלאכותית - שימוש מעשי קורס דיגיטלי מקיף"* (2025/2026), Module 5 - Video Generation, lessons on VEO 3.
- Google's official Veo prompt guide changes frequently. Always cross-check the latest Google DeepMind / Vertex AI documentation before committing to the JSON field names above.
