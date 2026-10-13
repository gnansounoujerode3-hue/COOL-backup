#!/usr/bin/env python3
"""Capture a reference page's design evidence with Playwright.

Writes to the output directory, per breakpoint width W:
    extraction-W.json  - tokens, keyframes, breakpoints, interaction states, animations
    full-W.png         - full-page screenshot
    scroll-W-N.png     - one screenshot per scroll position
    markup.html        - outerHTML of --selector, taken at the widest breakpoint

Requires: pip install playwright && playwright install chromium

Usage:
    python capture.py https://example.com --out ./capture
    python capture.py https://example.com --selector "main" --breakpoints 390,1440
"""
import argparse
import json
import pathlib
import sys

EXTRACTOR = pathlib.Path(__file__).with_name("extract-console.js")
MAX_SCROLL_SHOTS = 12      # screenshots kept, not how far we scroll
MAX_SCROLL_STEPS = 400     # runaway guard for infinite-scroll pages only

# Headless Chromium falls back to software rendering, which makes a WebGL hero
# capture as a black rectangle - the extraction still "succeeds" and the shot
# looks like a design choice rather than a failed capture. These flags put a
# real GPU path behind the canvas; the swiftshader line is the fallback for
# machines with no usable GPU, so a canvas site degrades to slow-but-correct
# instead of blank. ANGLE backend is platform-specific: d3d11 on Windows,
# metal on macOS, and the default (GL) elsewhere.
_ANGLE = {"win32": "d3d11", "darwin": "metal"}.get(sys.platform)
LAUNCH_ARGS = [
    "--enable-gpu",
    "--ignore-gpu-blocklist",
    "--enable-unsafe-swiftshader",
] + ([f"--use-angle={_ANGLE}"] if _ANGLE else [])

# Probing a canvas' context type can CREATE a context on an unused canvas, so
# this only measures geometry. Size is enough to flag "there is a canvas here,
# go look at the PNG before trusting this capture."
CANVAS_CENSUS_JS = """() => [...document.querySelectorAll('canvas')].map(c => {
  const r = c.getBoundingClientRect();
  return { bufferW: c.width, bufferH: c.height,
           cssW: Math.round(r.width), cssH: Math.round(r.height) };
})"""


def capture_at_width(page, js, width, height, out_dir, scroll_shots):
    """Extract and screenshot at one viewport width. Returns the extraction dict."""
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_timeout(400)  # let responsive layout settle

    # Scroll through before extracting. Scroll-triggered animations don't appear
    # in getAnimations() until they've fired, and lazy sections aren't in the DOM.
    #
    # The scroll must reach the BOTTOM, and that is independent of how many
    # screenshots we keep. Capping the scroll at the screenshot budget leaves
    # every fire-once reveal below that point ungated, so the full-page shot
    # below records those sections blank — which reads as a broken capture and
    # is really an unfinished scroll. Re-read scrollHeight each step: lazy
    # content extends the page as you go, so the initial height is a floor.
    y, steps, shots = 0, 0, 0
    total = page.evaluate("document.body.scrollHeight")
    while y < total and steps < MAX_SCROLL_STEPS:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(700)
        if scroll_shots and shots < MAX_SCROLL_SHOTS:
            page.screenshot(path=out_dir / f"scroll-{width}-{shots}.png")
            shots += 1
        y += height
        steps += 1
        total = page.evaluate("document.body.scrollHeight")

    if y < total:
        print(f"  WARNING: stopped scrolling at {y}px of {total}px after "
              f"{MAX_SCROLL_STEPS} steps — sections below may be un-revealed",
              file=sys.stderr)

    # Land on the bottom and let the last reveals settle before scrolling back:
    # a stagger plus its settle can run past a second on a long section.
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1200)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

    # Run the extractor as a function body and read the global it sets. Prefixing
    # the file with `return` instead hits automatic semicolon insertion on its
    # leading block comment and silently yields undefined.
    data = page.evaluate("() => {" + js + "\n return window.__designCapture }")

    # Canvas census travels with the extraction so the library records that this
    # reference had a canvas at all - a Match built from a capture whose hero was
    # a dead canvas is the failure this catches.
    canvases = page.evaluate(CANVAS_CENSUS_JS)
    data["canvases"] = canvases
    big = [c for c in canvases if c["cssW"] >= 200 and c["cssH"] >= 200]
    if big:
        largest = max(big, key=lambda c: c["cssW"] * c["cssH"])
        print(f"warning: {len(canvases)} canvas element(s) at {width}px, largest "
              f"{largest['cssW']}x{largest['cssH']} CSS px. Canvas/WebGL content is "
              f"NOT described by the extracted tokens - open full-{width}.png and "
              f"confirm it rendered before trusting this capture.", file=sys.stderr)

    (out_dir / f"extraction-{width}.json").write_text(json.dumps(data, indent=2))
    page.screenshot(path=out_dir / f"full-{width}.png", full_page=True)
    return data


def capture(url, out_dir, selector, breakpoints, height, scroll_shots):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")

    if not EXTRACTOR.exists():
        sys.exit(f"missing extractor script: {EXTRACTOR}")

    out_dir.mkdir(parents=True, exist_ok=True)
    js = EXTRACTOR.read_text()
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(args=LAUNCH_ARGS)
        page = browser.new_page(viewport={"width": max(breakpoints), "height": height})
        try:
            page.goto(url, wait_until="networkidle", timeout=60_000)

            # Widest first so markup comes from the desktop layout.
            for width in sorted(breakpoints, reverse=True):
                results[width] = capture_at_width(page, js, width, height, out_dir, scroll_shots)
                if width == max(breakpoints):
                    node = page.query_selector(selector)
                    if node:
                        (out_dir / "markup.html").write_text(node.evaluate("el => el.outerHTML"))
                    else:
                        print(f"warning: selector {selector!r} matched nothing — markup.html not written")
        finally:
            browser.close()

    widest = results[max(breakpoints)]
    print(f"\nwrote {out_dir}/ — {len(breakpoints)} breakpoint(s)")
    print(f"  keyframes:          {len(widest.get('keyframes', []))}")
    print(f"  interaction rules:  {len(widest.get('interactionRules', []))}")
    print(f"  live animations:    {len(widest.get('liveAnimations', []))}")
    print(f"  libraries:          {widest.get('libraries') or 'none detected'}")
    print(f"  media conditions:   {len(widest.get('mediaConditions', []))}")
    for note_key in ("blockedNote", "liveAnimationNote"):
        if widest.get(note_key):
            print(f"  note: {widest[note_key]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("./capture"))
    ap.add_argument("--selector", default="body", help="element whose outerHTML to save")
    ap.add_argument("--breakpoints", default="390,768,1440",
                    help="comma-separated viewport widths (default: 390,768,1440)")
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--no-scroll-shots", action="store_true",
                    help="skip per-scroll-position screenshots, keep full-page only")
    args = ap.parse_args()

    try:
        breakpoints = [int(w.strip()) for w in args.breakpoints.split(",") if w.strip()]
    except ValueError:
        sys.exit(f"--breakpoints must be comma-separated integers, got {args.breakpoints!r}")
    if not breakpoints:
        sys.exit("--breakpoints must contain at least one width")

    capture(args.url, args.out, args.selector, breakpoints, args.height, not args.no_scroll_shots)


if __name__ == "__main__":
    main()
