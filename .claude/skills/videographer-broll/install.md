# Install

One-time setup for the video-orchestrator skill. Run on first use.

## 1. Output directory

```bash
mkdir -p "${VIDEO_JOBS_DIR}"
```

This is where every job lands at `<brief_id>/<tool>/out_NN.mp4`. Set `VIDEO_JOBS_DIR` in `local/.env` (copy from `.env.example` at skill root).

## 2. QA Python environment

QA needs Python 3.11 or 3.12 (mediapipe wheels do NOT ship for 3.13 or 3.14). On many machines `python` resolves to a newer version that won't work, so point at 3.11/3.12 explicitly.

Plus opencv-python (mediapipe needs it for video frame I/O).

```bash
python3.11 -m venv "<skill_root>/qa/.venv"
"<skill_root>/qa/.venv/Scripts/python.exe" -m pip install --upgrade pip
"<skill_root>/qa/.venv/Scripts/python.exe" -m pip install mediapipe opencv-python pyloudnorm soundfile numpy
```

Verify:

```bash
"<skill_root>/qa/.venv/Scripts/python.exe" -c "import mediapipe, cv2, pyloudnorm, soundfile, numpy; print('QA deps OK')"
```

If Python 3.11 isn't on this machine: install from python.org or via winget (`winget install Python.Python.3.11`), then re-run.

## 3. video-use repo (lazy install on first dispatch)

Only needed when the orchestrator dispatches to the video-use adapter. Skip if you're sticking with CutSense + HyperFrames.

```bash
git clone https://github.com/browser-use/video-use "${VIDEO_USE_DIR}"
cd "${VIDEO_USE_DIR}"
uv sync
```

Then create `${VIDEO_USE_DIR}/.env`:

```
ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
GROQ_API_KEY=${GROQ_API_KEY}
# Set both in local/.env (copy from .env.example at skill root) - never hardcode keys.
```

## 4. CutSense (already installed)

Verify: `cutsense --version`. If missing, see your local CutSense clone's `CLAUDE.md` for setup.

## 5. HyperFrames (already installed)

Verify: `npx hyperframes doctor`. Should report green.

## 6. HeyGen + Hedra (API-only, no install)

Keys live in `local/.env` (copy from `.env.example` at skill root). Required: `HEYGEN_API_KEY`, `HEDRA_API_KEY`.

Avatar registry at `local/heygen-avatar-registry.md` - create on first avatar template use, one line per persona: `<avatar_id> | <voice_id> | <description>`.

## 7. Sanity test (optional but recommended)

```bash
cd "<skill_root>"
.venv/Scripts/python qa/run-qa.py 2026-04-26-podcast-acme-launch
```

(Will report missing brief/output, not a failure - just confirms the script runs.)

## What does NOT need install

- Brand pack (already at `brand/pack-personal-social.json`)
- Slash command (already at `~/.claude/commands/edit-video.md`)
- Skill auto-trigger (already registered when SKILL.md was created)
- Templates and adapters (markdown only, no install needed)
