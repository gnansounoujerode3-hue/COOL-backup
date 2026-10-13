# Scored tool selection + decision log (B2)

The orchestrator's Step 4 surfaces 2-3 tool options with pros/cons and a human
picks. This adds a **transparent weighted score** behind that step and writes a
**decisions.json** audit trail. The human still decides; the score just makes the
ranking legible and logged. That is the Radical Transparency requirement applied to
tool choice - no black-box "I picked CutSense."

## The rubric (7 dimensions)

Ported from OpenMontage's provider-selection rubric:

| Dimension | Weight | Meaning |
|---|---|---|
| task_fit | 30% | Does this tool handle this `source.type` + `intent`? Computed, not static. |
| quality | 20% | Output quality ceiling for its category |
| control | 15% | How precisely you can direct it (frame-level vs prompt-and-pray) |
| reliability | 15% | How often it returns a usable result first try |
| cost | 10% | 1.0 = free/subscription, 0 = expensive metered |
| latency | 5% | 1.0 = fast, 0 = slow (HeyGen 90-min renders score low) |
| continuity | 5% | Multi-clip consistency (stateless generators score low) |

`score = 0.30*task_fit + 0.20*quality + 0.15*control + 0.15*reliability + 0.10*cost + 0.05*latency + 0.05*continuity`

**task_fit** is derived from the brief:
`0.2 base + 0.5 if source.type in good_for_source + 0.3 if intent in good_for_intent`, capped at 1.0.

The other six are static priors per tool in
[`tool-profiles.json`](tool-profiles.json). They are data, not code, on purpose -
edit them as real results come in.

## Run it

```bash
python tools/select_tool.py --brief <brief.json|brief_id> \
  --candidates cutsense,video-use,hyperframes --output <job>/decisions.json
```

Prints a ranked table and writes `decisions.json`:

```json
{
  "chosen": "cutsense",
  "runner_up": "video-use",
  "separation": 0.08,
  "confidence": "medium",
  "weights": { "task_fit": 0.30, "...": "..." },
  "candidates": [
    { "tool": "cutsense", "score": 0.905, "est_cost_usd": 0.0,
      "dimensions": { "task_fit": 1.0, "quality": 0.85, "...": "..." },
      "rationale": "strongest on task_fit (1.00); weakest on latency (0.70); ..." }
  ],
  "note": "Scored recommendation only. The human approves or overrides. Free-first: prefer the $0 option within one separation band."
}
```

## Confidence

From the score gap between #1 and #2:
- separation >= 0.12 -> **high** (clear winner; default to it)
- separation >= 0.05 -> **medium** (surface both, let the human pick)
- below 0.05 -> **low** (genuinely close; lean free-first and explain the tie)

## How it composes with the existing flow

1. Orchestrator builds candidate list (from `decision-tree.md` as before).
2. `select_tool.py` scores them and writes `decisions.json`.
3. Orchestrator surfaces the top 2-3 with the rationale strings as the pros/cons
   (Step 4), defaulting to `chosen` but **bolding free-first** when a metered tool
   only narrowly outscores a $0 one.
4. Human approves or overrides. The override (if any) is appended to `decisions.json`
   so the log reflects what actually ran.

This does NOT replace human judgment or the 2-3-option UX. It replaces the *unlogged*
guess behind it.

## Free-first tie-break (project decision)

Budget mode default is free-first. When the top metered tool and a $0 tool are within
one confidence band, the selector's `note` tells the orchestrator to lead with the free
option. Spending money to win by 0.03 points is not worth it - say so to the human.
