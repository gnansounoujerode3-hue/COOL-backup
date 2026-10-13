# Knowledge packs (Layer 3)

Per-provider deep-usage know-how, separated from the adapters. The three layers:

- **Layer 1 - capability:** the tools + pipelines (what exists). `tools/`, `pipelines/manifest.json`.
- **Layer 2 - conventions:** the adapters + skill rules (how WE use it). `adapters/`, `SKILL.md`.
- **Layer 3 - provider depth (this dir):** how each external provider actually behaves, its
  endpoints, gotchas, and failure modes. Adapters stay thin and link here; the agent pulls the
  depth on demand instead of carrying it in every prompt.

## Packs

| Pack | Backs | Why it exists |
|------|-------|---------------|
| [broll-sources.md](broll-sources.md) | `adapters/broll-retrieval.md`, `tools/broll_corpus.py` | Per-source API shape, license nuances, file-URL resolution, CLIP notes |
| [revision-style.md](revision-style.md) | `adapters/broll-director.md` | The researched "Re:Vision method": b-roll type taxonomy, typography/color presets, hook catalog, the 13-rule b-roll insertion ruleset |
| [elevenlabs-audio.md](elevenlabs-audio.md) | `adapters/music-sfx.md`, `tools/elevenlabs_music.py` | The scoped-key 401 gotcha, sound-generation + music endpoints, ducking/loudness |
| [fal-seedance.md](fal-seedance.md) | `adapters/fal-seedance.md` | The bare-prefix silent failure, poll pattern, caps, Lock Block |
| [heygen.md](heygen.md) | `adapters/heygen.md` | Two-step generate+poll, latency, avatar registry, cloning |

## Adding a pack

1. Drop `knowledge/<provider>.md` here (endpoints, auth, gotchas, failure modes, cost posture).
2. Reference it from the adapter (`See also` or inline link) so the agent can find it.
3. Add a row above.
4. `python tools/check_knowledge.py` confirms every `knowledge/<x>.md` referenced across the
   skill actually exists (run it after adding/renaming a pack).

## Validate

```bash
python tools/check_knowledge.py
```

Exit 0 = every referenced pack exists. Exit 2 = a dangling `knowledge/...` reference (fix the
link or add the pack).
