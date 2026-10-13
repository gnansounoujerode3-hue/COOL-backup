# Library entry template

Every `<slug>.md` follows this shape. Uniformity is the point: entries are read by
agents that have never seen the creative and cannot open it. Every value is
**measured, not estimated**. No assets, no body copy, no imagery — knowledge only.

Omit a section only when it genuinely does not apply, and say why in one line
("No photography: fully illustrated"). An empty heading beats an invented value.

---

```markdown
# <slug>

**Callable as: <Name>** (aliases: <other names someone would say>)

<One line: what the creative is and what it sells.> Measured <date>.
Source: <native WxH, ratio>. Origin: <photographed | 3D render | AI-generated | vector>.

## Fidelity — <spec | partial | signature-only | none>

- `spec` — every reused element carries box, tilt and surface colour. Only this
  value licenses a recut from the entry without re-opening the source.
- `partial` — some elements measured. Saves most of a re-measure, replaces none.
- `signature-only` — palette and character. A vocabulary.
- `none` — recorded but not measured.

Never promote this line without re-measuring.

## Composition — <the idea in five words>

<Reading order, and what carries it. Which element is the focal point and how the
eye is led there. The structural move worth stealing, in one or two sentences.>

## Frame and grid

<Native ratio. Margins. Content measure. Column or stack mechanism. Where the
optical centre sits versus the geometric one. Safe zones if the creative was built
for a platform that crops.>

## Type

<Scale as a system: sizes, weights, tracking, leading, the ratio between steps.
Named families if identifiable, and their roles. Whether type is live or lifted.>

## Colour

<Palette with exact sampled values AND the system: which is field, which is
surface, which is accent, and the alpha relationships. Surface colours must be
sampled from the interior, not read off a brand guide - a rendered creative drifts
from its own tokens.>

## Element inventory

| Element | Box (l,t,w,h) | Tilt | Class | Notes |
|---|---|---|---|---|
| <name> | <x,y,w,h> | <deg> | re-authorable / liftable / photographic | <what breaks if mishandled> |

<Tilt is the measured slope from `measure.mjs --tilt`, not an eyeball. Class
decides whether it is rebuilt or lifted - see SKILL.md.>

## Photography

<What the scene is, where the subject sits, and how it must be reframed for a
taller or wider target. Which crop keeps the focal point. What must never be cut.>

## Ratios produced

| Ratio | Size | What changed | Gotcha |
|---|---|---|---|
| <9:16> | <1080x1920> | <the re-layout move> | <what nearly broke> |

## Licence and provenance

<Who owns it. Whether the assets can be reused, and by whom. If any third-party
logos appear, list them: they are liftable for the owner's own creative and not
transferable to anyone else's.>
```
