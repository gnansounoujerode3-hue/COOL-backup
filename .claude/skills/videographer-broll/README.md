# video-orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-orange.svg)](https://www.claude.com/product/claude-code)
[![Tools wired](https://img.shields.io/badge/tools-6-green.svg)](#which-tool-fits-what)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](#)

**Stop picking the wrong video tool.**

There are so many ways to edit your video, but it can be overwhelming to know which tool to choose and when. 
The FOMO of video editing has never been so difficult. Is this a job for revideo or remotion? For Cutsense or hyperframes? Should I use the claude skill video or maybe a pipeline with a few tools chained together?

All this FOMO ends here and now.

Introducing video-orchestrator.

It asks 3 questions, surfaces 6 tool options with real tradeoffs, and dispatches the right one. Or runs all recommended ones in parallel so you can compare side-by-side.

<p align="center">
  <img src="demo.gif" alt="videographer demo: 3 questions, 6 tool options, parallel dispatch" width="800">
</p>

## Which tool fits what

| You have... | It usually picks... |
|---|---|
| A long talking-head video | **CutSense** (silence/filler removal, brand captions) |
| A URL or website | **website-to-hyperframes** (page capture to animated promo) |
| A script and a portrait image | **HeyGen** or **Hedra** (avatar lipsync) |
| Many takes / raw transcript | **video-use** (LLM-driven cut picking) |
| A branded title card or outro | **Remotion** (pixel-perfect, fast) |
| Three hooks to A/B test | **Fork mode** (all 3 in parallel, compare) |

## Why this exists

Most video edits don't fail at the rendering step. They fail at the planning step. People grab the first tool they think of, render something, then realize a different tool was the better fit. Time spent re-rendering is the most expensive kind. The orchestrator pauses for thirty seconds at the start to ask, surface, and pick deliberately. Total time spent: less.

## Try it

```bash
git clone https://github.com/kivimedia/videographer-skill.git ~/.claude/skills/video-orchestrator
cd ~/.claude/skills/video-orchestrator
cp .env.example local/.env                       # paste your API keys
cp local/personal.json.example local/personal.json   # fill in your name
```

Restart Claude Code. Then say one of:
- `edit a video`
- `cut this video: <path>`
- `make 3 ad variants from this script`
- `turn this into vertical clips`

Full setup including the QA Python venv: see [install.md](install.md).

## What happens when you run it

1. Reads your source (file or URL), runs `ffprobe` if needed
2. Asks 6 batched questions: source type, intent, output count, captions, cleanup level, tool mode
3. Surfaces 3 tool options with one-line pros and cons
4. Builds a brief at `${VIDEO_JOBS_DIR}/<brief_id>/brief.json`
5. Dispatches to the chosen tool's adapter
6. Runs QA gates (face-safety, loudness, timing)
7. Hands back paths plus a `COMPARE.md` index

**Fork mode** spawns N parallel sub-agents in a single turn, each running a different tool against the same brief, then aggregates results into one comparison table.

## QA gates

Every output runs through three automatic checks:

| Gate | Catches |
|---|---|
| Face safety | Captions overlapping a detected face |
| Loudness | LUFS off target, true peak above -1.0 dBTP |
| Timing | Duration off by more than 2s, cuts closer than 0.4s apart |

PASS / WARN / FAIL with remediation hints written into JSON. The QA loop can auto-retry on FAIL.

## Brand packs

Default: [`brand/pack-personal-social.json`](brand/pack-personal-social.json) (cyan + orange, social-feed bold). Override per-job by setting `brief.brand.pack` in the brief. Custom brand pack? Drop it in `local/brand-pack-mine.json` (gitignored) and reference it.

## Cloning your voice + avatar (optional)

The [`cloning/`](cloning/) directory has briefs for a one-time voice clone (ElevenLabs PVC) and avatar clone (HeyGen Avatar IV). Once trained, the IDs go in `local/personal.json` and the orchestrator dispatches to your real face and voice. Equipment, room, framing, scripts, all included.

## Where things live

```
SKILL.md             The orchestration flow Claude reads
adapters/            One adapter per supported tool (incl. broll-retrieval, music-sfx, enhance)
pipelines/           Staged "whole video from a topic" pipelines (explainer / documentary / cinematic)
templates/           Scenario templates
selection/           Scored tool selection (7-dim rubric + tool profiles)
knowledge/           Layer-3 per-provider knowledge packs (pulled on demand)
schemas/             JSON schemas (scene-plan)
render-profiles.json Platform delivery profiles (YouTube / Shorts / Reels / TikTok / LinkedIn / 21:9)
brand/               Default brand packs
remotion-templates/  Standalone Remotion source
qa/                  QA gates: post-render (face-safety, loudness, timing) + pre-compose (slideshow-risk)
tools/               Python helpers (broll corpus, pipeline scaffold, tool selector, profiles, music/sfx, enhance)
cloning/             One-time voice + avatar capture briefs
local/               YOUR config (gitignored)
```

## Configuration

All API keys go in `local/.env` (gitignored). The skill never reads keys from anywhere else.

```env
ELEVENLABS_API_KEY=...
HEDRA_API_KEY=...
HEYGEN_API_KEY=...
GROQ_API_KEY=...
ANTHROPIC_API_KEY=...
VIDEO_JOBS_DIR=...
VIDEO_USE_DIR=...
CUTSENSE_DIR=...
```

Personal identity (your name, default brand pack, avatar / voice IDs) lives in `local/personal.json`. The HeyGen avatar adapter and the cloning briefs read from there.

## What's next

Drop this folder in `~/.claude/skills/`, restart Claude Code, run it on a real video. If a tool doesn't fit your case, [open an issue](https://github.com/kivimedia/videographer-skill/issues) with the brief that didn't work and what you wanted instead.

## License

MIT - see [LICENSE](LICENSE).
