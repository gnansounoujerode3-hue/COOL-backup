# Capture paths

Four ways to get evidence out of a browser, best first. Read the section for the
path you actually have.

## 1. chrome-devtools-mcp (best)

Google's official MCP server. Drives a real Chrome via the DevTools Protocol, so
you get computed styles, hover states, breakpoints, and screenshots without
asking the user to do anything.

If it isn't connected, offer the install. It's one command:

```
claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest
```

Configs for Cursor, VS Code, Codex, Gemini CLI and others are in that project's
README. It also ships as a Claude Code plugin bundling MCP plus skills.

Sequence:

1. `new_page` / `navigate_page` to the URL.
2. `evaluate_script` scrolling to the bottom in steps, pausing between, so
   scroll-triggered animations fire and lazy content mounts.
3. `evaluate_script` with the contents of `scripts/extract-console.js`. It parks
   its result on `window.__designCapture`; return that. The `copy()` branch is
   guarded and no-ops outside DevTools.
4. `take_screenshot` at the top, at each major section, and full-page.
5. `resize_page` to each breakpoint the extraction reported, re-running the
   extractor and screenshotting at each. This is the step people skip, and it's
   where guessed mobile layouts come from.
6. `hover` over primary buttons, nav items, and cards, screenshotting each. The
   extractor pulls `:hover` rules from the stylesheets, but hovering shows you
   JS-driven states that no stylesheet contains.
7. `evaluate_script` returning `document.querySelector(sel).outerHTML` for the
   section being rebuilt.

Two optional extras: `emulate` can check reduced-motion and dark-mode variants,
and `screencast_start` / `screencast_stop` records motion as video if the server
was started with `--experimentalScreencast` and ffmpeg is on its PATH. Treat the
screencast as a bonus, not a dependency.

Note that this server exposes whatever is in the browser to the client, so point
it at public reference pages, not tabs holding the user's private data.

## 2. Playwright / Puppeteer

Run `scripts/capture.py` (Playwright, Python). It scrolls, extracts, screenshots
each viewport, and saves markup and JSON to an output directory:

```
python scripts/capture.py https://example.com --out ./capture --selector "main"
```

Requires `pip install playwright && playwright install chromium`. Pass
`--breakpoints`/`--height` and re-run per breakpoint if you need responsive coverage.

## 3. Claude in Chrome or another browser MCP

Same shape as path 1 with whatever the equivalent tools are called. The
non-negotiables are: scroll before extracting, run the extractor script, capture
hover states, and screenshot at more than one width.

## 4. Chat only: the user is your browser

Send everything needed in **one message**. Requesting artifacts one at a time
across several turns is how this workflow stalls out.

Ask for:

1. **The extractor output.** Paste `scripts/extract-console.js` into the message.
   Tell them to scroll the page top to bottom first, then paste it into the
   DevTools console (F12 → Console). It copies JSON to the clipboard.
2. **Markup.** DevTools → right-click the section → Copy → Copy outerHTML.
3. **Screenshots.** Full page, one at mobile width, and start/end frames of any
   animation that matters.
4. **Behavior only they can see.** What triggers each animation; whether scroll
   feels smoothed or native; what changes on hover; how mobile differs.

Then read what came back and name what's missing before building.

## Also fetch the raw stylesheets

The extractor gives you *resolved* values. It does not tell you which selector
produced them, and computed styles cannot show you a rule that did not apply to
the element you sampled. Both gaps are where wrong rebuilds come from.

So pull the source too, and read the actual rules for the selectors you are
rebuilding:

```bash
curl -sL "$PAGE" -o ref.html
grep -oE 'href="[^"]+\.css"' ref.html | sed 's/href="//;s/"//'   # then curl each
python3 - <<'PY'
import re; css = open('ref.css').read()
for sel in ['.card', '.question', '.hero-title']:      # your real selectors
    for m in re.finditer(re.escape(sel) + r'[.\w-]*\s*\{[^}]*\}', css):
        print(m.group(0)[:240], '\n')
PY
```

What only the source shows:

- `:first-child` / `:last-child` / `:nth-*` overrides. Sampling one element
  cannot reveal that the first item drops its border and top padding.
- Whether spacing comes from a `gap`, a margin, or per-item padding. All three
  compute to the same visual rhythm and behave differently when content changes.
- Gradient *type*. A token named `--hero-overlay` may be radial in one theme and
  a linear `to bottom` in the one you are looking at.
- The `clamp()` behind a font size, rather than the one value it happens to
  resolve to at your capture width.

Minified and hashed class names are normal; grep for the unhashed part.

## Assets, for a local Match

If the rebuild is a local study copy, fetch the real fonts and images. A
substituted typeface changes every text width on the page, which puts a
pixel-accurate match out of reach and leaves you tuning values that were never
wrong.

```bash
curl -sL -o assets/img/hero.webp "$SITE/path/hero.webp"
grep -oE 'url\("?[^")]+\.woff2"?\)' ref.css   # resolve against the CSS file's URL
```

Licensed fonts and the site's photography stay local. Say so in the notes, and
see the copying section in `SKILL.md` before anything gets published.

## Full-page screenshots: tile, don't resize

The usual full-page trick (read `document.documentElement.scrollHeight`, set the
viewport to that height, then `captureBeyondViewport`) **re-lays-out every
`100vh` / `min-height: 100dvh` section**, so each becomes a full *page* tall and
the image explodes. Measured twice in one session: a Framer template went
16,740px → 111,780px, and a Divi page 7,907px → 12,943px. Nothing errors. You
just get a very tall image whose proportions no longer match what a visitor sees,
and any geometry read off it is wrong.

Capture **viewport-sized tiles at fixed scroll positions** instead:

1. Set the real viewport (e.g. 1440×900) and navigate.
2. Scroll top→bottom once to prime lazy content and fire reveals, then return to 0.
3. Shoot at `y = 0, h, 2h …`, scrolling between shots and pausing ~0.8s.

Only reach for the resize trick on a page you have confirmed has no viewport
units in its section heights (and confirm, don't assume).

Related, and it costs about twenty minutes every time: `/json/version`'s
`webSocketDebuggerUrl` is the **browser**-level CDP endpoint and has no
`Page`/`Runtime` domains, so every call returns
`-32601 'Page.enable' wasn't found` and reads like a broken script. Attach to a
**page target** from `/json/list` instead.

## Consent banners

A cookie or consent overlay will sit in front of the design and wreck any
comparison. Dismiss it before capturing (choose the decline/reject option, not
accept), and if it cannot be dismissed in your capture path, crop that band off
**both** images before diffing.

## Reading the extraction

`blockedStylesheets` above zero means cross-origin CSS was unreadable;
`cssRules` throws on it. CDN-hosted stylesheets and some font services land here,
so ask about anything the tokens don't explain.

`sampled` values are ordered by frequency, with counts. The top entries are the
system; the long tail is usually one-off content styling. In Adapt mode the
counts matter more than the values: they tell you which sizes and colors carry
structural weight.

`mediaConditions` is the real breakpoint list. Use it to decide which widths to
re-capture at rather than guessing 768/1024.

`fontFaces` shows which typefaces are actually loaded. For a Match that is your
fetch list, not a shortlist of things to find lookalikes for. Substitution is an
Adapt decision, or one forced by an artifact that will be published.

`liveAnimations` is empty if the page wasn't scrolled first. If it's empty and
`keyframes` isn't, that's the likely cause. Scroll and re-run.

## Third-party extractors

There's a small ecosystem of dedicated tools (`dembrandt`, `designlang`,
`extract-design-system`) that wrap Playwright and emit W3C DTCG tokens,
Tailwind configs, and Figma variables, some with their own MCP servers. Several
advertise interaction-state and multi-breakpoint capture.

They may be faster than the bundled scripts for token-heavy work. They are also
unvetted third-party dependencies that run a headless browser against a URL, and
none of them is required. The scripts here cover the same ground with no
install. If you reach for one, say so, and check its output rather than trusting
it wholesale.
