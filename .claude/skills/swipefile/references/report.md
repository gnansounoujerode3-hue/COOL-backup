# The replication report

Every Match ends with this report. No exceptions. It is how the user knows the
accuracy of what they got without trusting adjectives. Produce it three ways
from the same numbers:

1. **In chat**: the table below, so the result is legible at handover.
2. **`REPORT.md`** beside the mirror, so the artifact carries its own audit.
3. **`report.json`**: the same values, machine-readable, so tooling and the
   library can consume them.

**Do not assemble it by hand. `scripts/report.py` is the instrument**, for the
same reason `motion-spec.py` is: this page was prose for the whole life of the
Match path, and a written rule is the thing that gets skipped while being quoted
back correctly.

```bash
python3 report.py --init                       # skeleton: every metric, blank
python3 report.py --site example.com --mode match --path mirror \
    --crawl crawl-manifest.json --build build-manifest.json \
    --copy copy.json --motion motion.json --measured measurements.json
```

It aggregates rather than measures. `crawl.py` supplies scope, `build.py`
supplies assets, links and classified markup changes, `copy-gate.py --json` and
`motion-diff.py --json` supply their own verdicts; `measurements.json` holds
what only a browser pass can produce. Three refusals are the point:

- **Omission is a failure.** A metric absent from `measurements.json` exits 2
  and names the command that produces it. `not measured — <why>` is always
  available and is a legitimate answer; a blank cell is not.
- **Unmeasured is never passed.** A gate whose input was never measured reads
  `UNVERIFIED`. It does not block (an automated mirror should still be able to
  produce a report), but it never renders as cleared: the headline carries the
  count, `report.json` lists them under `gates.unverified`, and they belong in
  the honesty rows. `--strict` makes them blocking, which is what claiming a
  **fully verified** Match requires. A build with unverified gates is reported,
  not verified, and must not be described as the latter.
- **Placeholders void the score.** A similarity number computed over
  placeholder content fails outright rather than carrying a footnote.

Numbers only enter the report if they were **measured on the built artifact**.
A metric you did not measure is listed as `not measured — <why>`, never
omitted and never estimated. An impressive report with a silent gap is worth
less than a modest one that names its gaps.

## The table

| Group | Check | What is reported | Gate |
|---|---|---|---|
| Scope | Pages built | built / total in sitemap, with the excluded sections named and counted (e.g. "89 built; 368 blog excluded as bulk"), plus the sitemap/crawl set-difference in both directions | every sitemap URL built, or listed with a reason |
| Fidelity | Text layer | % of characters identical to the reference DOM text, per page and overall, plus total chars compared | 100% for mirror-path Match |
| Fidelity | Geometry | boxes compared / exact matches / worst delta in px, at each verified breakpoint | worst delta explained or zero |
| Fidelity | Pixel diff | % similarity per breakpoint under identical headless capture; reference-vs-itself ceiling stated when a region is animated; for any multi-page mirror the full per-page table, every page scored against its own ceiling | ≥95% floor; 100% target; no page more than 0.5 points below its own ceiling |
| Fidelity | Fonts | `scripts/font-gate.js` run on **both sides** at the same viewport, values side by side: `document.fonts.size`, `check()` per family/weight, canvas width A/B vs a forced `sans-serif`, probe target the display face | **the two sides agree**: equal face count, same `check()` per face, widths within ~1px. `false` on both sides is declared-but-unused: a pass. `check()` alone is insufficient (SRI case: check() true, page in Times); a UI-sans A/B alone is insufficient (metric-compatible `<Family> Placeholder` faces read identical on a loaded page) |
| Motion | `motion-diff.py ref.json build.json` | **0 gate failures**: signature curve present, structural durations reproduced, stagger ladder present, `prefers-reduced-motion` in the build. A pixel diff cannot see motion; this is the only thing that can. |
| Content | `copy-gate.py index.html` (`--match` for captured copy) | AI-writing tells in copy *we* wrote, one `<h1>`, `<title>` and meta description present, `lang`, `alt` on every `<img>`, JSON-LD structured data present; warnings listed separately from failures | **0 failures**: Match runs `--match`, which skips the prose checks because captured copy is not ours to rewrite; SEO/GEO findings on a mirror describe the reference and belong in the honesty rows, not in an edit |
| Integrity | Assets | mirrored count, total bytes, cache hits, integrity problems (HTML-404 bodies, truncated files), failures that 404 on the reference's own origin (listed separately, not your defect) | 0 integrity problems |
| Integrity | Assets (format/decode) | `content-type` and `naturalWidth`/`naturalHeight` per image against the reference fetched under Chrome's `Accept` string; a clean network log does not prove the right bytes arrived | 0 content-type mismatches, 0 decode-size mismatches |
| Integrity | Origin refs | live references to the reference's origin remaining across all built pages | **must be 0** |
| Integrity | Off-origin requests | `performance.getEntriesByType('resource')` filtered to entries outside `location.origin`, measured on several served pages at every breakpoint | **must be 0**: `grep` is the cheap pre-check, this is the authority |
| Integrity | Links | internal links wired / inert, wired targets missing | **0 missing targets** |
| Integrity | Markup changes | count of deliberate changes vs the reference markup, each classified (script-strip, `sri-strip` of `integrity`/`crossorigin`, URL relocalisation, href neutering to `#inert`, stamp); unexplained changes | **0 unexplained**, and 0 bare `#` hrefs |
| Runtime | Network | failed requests on load of the built pages; live runtime surfaces counted (WebGL contexts, Rive/Lottie canvases, videos playing) | 0 failed requests |
| Motion | Motion systems | easing curves extracted vs implemented; reveal/choreography mechanism named and verified live | mechanism verified, not assumed |
| Honesty | Excluded | everything left out, with reason and the command to extend; the crawler's `skipped` map tabulated by reason, with every `auth-gated` URL re-probed for 200-without-login-redirect | always present |
| Honesty | Unresolved | deltas whose cause was not found; randomised regions that cap the ceiling (with how the ceiling was measured and which runtime params were pinned identically on both sides); motion residuals the two-wait test reproduces as animation phase rather than defects | always present, even when empty; "none" is a finding |

Expand freely beyond these rows when a site warrants it (per-template diff
scores, per-breakpoint tables, JS-error counts). Never contract below them.

## report.json

Same values, stable keys, one object:

```json
{
  "site": "example.com",
  "date": "YYYY-MM-DD",
  "mode": "match | adapt",
  "path": "mirror | mirror-scripted | rebuild",
  "scope":     { "built": 0, "sitemap_total": 0, "sitemap_only": [], "crawl_only": [],
                 "excluded": [{"section": "", "count": 0, "reason": ""}] },
  "fidelity":  { "text_pct": 0, "text_chars": 0,
                 "geometry": {"boxes": 0, "exact": 0, "worst_delta_px": 0},
                 "node_count": {"reference": 0, "mirror": 0},
                 "pixel": [{"breakpoint": 0, "similarity_pct": 0, "self_ceiling_pct": null}],
                 "pixel_by_page": [{"slug": "", "breakpoint": 0, "similarity_pct": 0, "self_ceiling_pct": null, "gap_points": 0}],
                 "fonts": {"gate": "pass | fail", "disagreements": [],
                           "reference": {"faces": 0, "checks": [{"family": "", "weight": "", "ok": true}], "widths": [{"family": "", "real": 0, "fallback": 0, "delta": 0}]},
                           "mirror":    {"faces": 0, "checks": [{"family": "", "weight": "", "ok": true}], "widths": [{"family": "", "real": 0, "fallback": 0, "delta": 0}]} } },
  "integrity": { "assets": {"mirrored": 0, "bytes": 0, "problems": 0, "origin_404s": [],
                            "content_type_mismatches": 0, "decode_size_mismatches": 0},
                 "origin_refs_remaining": 0,
                 "off_origin_requests": 0,
                 "links": {"wired": 0, "inert": 0, "missing_targets": 0, "bare_hash_hrefs": 0},
                 "markup_changes": {"total": 0, "classified": 0, "unexplained": 0,
                                    "classes": {"script-strip": 0, "sri-strip": 0, "url-relocalisation": 0, "href-inert": 0, "stamp": 0}} },
  "runtime":   { "failed_requests": 0, "live_surfaces": {"webgl": 0, "rive": 0, "lottie": 0, "video": 0} },
  "motion":    { "curves_extracted": 0, "curves_implemented": 0, "mechanism": "" },
  "honesty":   { "excluded": [], "unresolved": [] },
  "gates":     { "passed": true, "failing": [] }
}
```

## The gates

A Match is **not done** while any of these holds, and the report must say so in
its first line rather than bury it:

- origin refs remaining > 0, or any off-origin request measured at runtime
- failed requests on load of the built pages > 0
- missing wired link targets > 0, or any bare `#` href surviving in a built page
- unexplained markup changes > 0
- the font gate's two sides disagree: unequal `document.fonts.size`, a `check()`
  that differs between reference and mirror, or a canvas width A/B outside ~1px
- any asset whose `content-type` or decode size does not match the reference
- any sitemap URL neither built nor listed with a reason
- any page more than 0.5 points below its own reference-vs-itself ceiling
- any similarity score computed against placeholder content (forbidden outright)

## Why the two honesty rows exist

The report's credibility comes from what it admits. "1,186 markup changes, all
classified, 0 unexplained" is a strong claim *because* the classification can be
audited. "Randomised hero, ceiling measured at 99.1% reference-vs-itself" turns
an excuse into a measurement. Write the report so that a skeptical stranger
could re-run every number.
