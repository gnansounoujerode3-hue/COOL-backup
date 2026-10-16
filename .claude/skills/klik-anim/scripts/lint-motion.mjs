#!/usr/bin/env node
/**
 * klik-anim motion lint — the craft laws that a machine can check.
 *
 *   node lint-motion.mjs [paths...] [--strict] [--json]
 *
 * Defaults to scanning `src`. Zero dependencies; Node 18+.
 *
 * This catches ONLY the mechanical laws — determinism, easing hygiene, the
 * layout-property ban, the perspective/filter conflict, and a heuristic for
 * unvaried device reuse. Everything that needs eyes (hierarchy, gaze path,
 * reading holds, copy discipline, material) is still the A9 look-pass and the
 * Part D checklist. A clean lint is not a pre-flight pass.
 *
 * Waivers, when a law is being broken deliberately:
 *   // klik-lint-disable-next-line animated-layout-prop — deliberate container morph (A7)
 *   // klik-lint-disable inline-curve                     (file scope, anywhere in the file)
 * Use `*` for the rule id to waive every rule. Always give a reason.
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";

const SOURCE_EXT = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs"]);
const SKIP_DIR = new Set([
  "node_modules", "dist", "build", "out", "coverage",
  ".git", ".next", ".cache", "public", "assets", "out-tsc",
]);

/* ------------------------------------------------------------------ *
 * Source blanking — comments become spaces, so a rule never fires on
 * `// never call Math.random()`. Offsets and line numbers are preserved
 * exactly, so both variants share one set of line numbers.
 *
 *   blankNonCode(src)        → comments AND string contents blanked.
 *                              Use for anything that must not match a
 *                              literal: determinism, timers, easing.
 *   blankNonCode(src, false) → comments only, strings intact. Use where
 *                              the evidence legitimately lives inside a
 *                              string or template: `blur(...)`,
 *                              'cubic-bezier(...)'.
 * ------------------------------------------------------------------ */

function blankNonCode(src, blankStrings = true) {
  const out = src.split("");
  const tpl = []; // brace depth per open template interpolation
  let mode = "code";
  let i = 0;

  const space = (n) => { if (out[n] !== "\n") out[n] = " "; };
  const spaceString = (n) => { if (blankStrings) space(n); };

  while (i < src.length) {
    const c = src[i];
    const d = src[i + 1];

    if (mode === "code") {
      if (c === "/" && d === "/") { space(i); space(i + 1); mode = "line"; i += 2; continue; }
      if (c === "/" && d === "*") { space(i); space(i + 1); mode = "block"; i += 2; continue; }
      if (c === "'") { mode = "single"; i++; continue; }
      if (c === '"') { mode = "double"; i++; continue; }
      if (c === "`") { mode = "template"; i++; continue; }
      if (tpl.length) {
        if (c === "{") tpl[tpl.length - 1]++;
        else if (c === "}") {
          if (tpl[tpl.length - 1] === 0) { tpl.pop(); mode = "template"; i++; continue; }
          tpl[tpl.length - 1]--;
        }
      }
      i++; continue;
    }

    if (mode === "line") {
      if (c === "\n") { mode = "code"; i++; continue; }
      space(i); i++; continue;
    }

    if (mode === "block") {
      if (c === "*" && d === "/") { space(i); space(i + 1); mode = "code"; i += 2; continue; }
      space(i); i++; continue;
    }

    // inside a string literal
    if (c === "\\") { spaceString(i); if (i + 1 < src.length) spaceString(i + 1); i += 2; continue; }
    if (mode === "single" && c === "'") { mode = "code"; i++; continue; }
    if (mode === "double" && c === '"') { mode = "code"; i++; continue; }
    if (mode === "template") {
      if (c === "`") { mode = "code"; i++; continue; }
      if (c === "$" && d === "{") { tpl.push(0); mode = "code"; i += 2; continue; }
    }
    spaceString(i); i++;
  }

  return out.join("");
}

/* ------------------------------------------------------------------ *
 * Small scanning helpers
 * ------------------------------------------------------------------ */

function lineIndex(src) {
  const starts = [0];
  for (let i = 0; i < src.length; i++) if (src[i] === "\n") starts.push(i + 1);
  return (offset) => {
    let lo = 0, hi = starts.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (starts[mid] <= offset) lo = mid; else hi = mid - 1;
    }
    return { line: lo + 1, col: offset - starts[lo] + 1 };
  };
}

/** Text between `from` (index of the opening char) and its balanced close. */
function balanced(src, from, open, close) {
  let depth = 0;
  for (let i = from; i < src.length; i++) {
    if (src[i] === open) depth++;
    else if (src[i] === close) {
      depth--;
      if (depth === 0) return { text: src.slice(from, i + 1), end: i };
    }
  }
  return { text: src.slice(from), end: src.length - 1 };
}

/** The value of an object property: from after `:` to the next top-level `,` or `}`. */
function propValue(src, colonIdx) {
  let depth = 0;
  for (let i = colonIdx + 1; i < src.length; i++) {
    const c = src[i];
    if (c === "(" || c === "[" || c === "{") depth++;
    else if (c === ")" || c === "]") depth--;
    else if (c === "}") { if (depth === 0) return src.slice(colonIdx + 1, i); depth--; }
    else if (c === "," && depth === 0) return src.slice(colonIdx + 1, i);
  }
  return src.slice(colonIdx + 1);
}

const FRAME_DERIVED = /\binterpolate\s*\(|\bspring\s*\(|\buseCurrentFrame\s*\(|\bframe\b/;

/**
 * Names bound to a frame-derived value, so indirection doesn't hide a
 * violation: `const w = interpolate(frame, …)` … `style={{width: w}}`.
 * One pass, one level deep — enough for the shape this actually takes.
 */
function frameDerivedNames(code) {
  const names = new Set();
  const re = /\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=/g;
  let m;
  while ((m = re.exec(code))) {
    let depth = 0;
    let end = m.index + m[0].length;
    while (end < code.length) {
      const c = code[end];
      if (c === "(" || c === "[" || c === "{") depth++;
      else if (c === ")" || c === "]" || c === "}") { if (depth === 0) break; depth--; }
      else if ((c === ";" || c === "\n") && depth === 0) break;
      end++;
    }
    if (FRAME_DERIVED.test(code.slice(m.index + m[0].length, end))) names.add(m[1]);
  }
  return names;
}

/* ------------------------------------------------------------------ *
 * Rules
 * ------------------------------------------------------------------ */

const MOTION_MODULE = /(^|[\\/])motion(\.(t|j)sx?)?([\\/]|$)/;

const RULES = [
  {
    id: "nondeterministic-source",
    level: "error",
    law: "A0",
    run(ctx) {
      const re = /\b(Math\.random|Date\.now|performance\.now)\s*\(|\bnew\s+Date\s*\(/g;
      return matches(ctx, re, (m) => {
        const call = (m[1] || "new Date") + "()";
        return `${call} in composition code — same frame will not produce the same pixels, so parallel renders flicker. Use Remotion's seeded random("seed"), or frame-based noise.`;
      });
    },
  },
  {
    id: "wall-clock-timer",
    level: "error",
    law: "A0",
    run(ctx) {
      const re = /\b(setTimeout|setInterval|requestAnimationFrame)\s*\(/g;
      return matches(ctx, re, (m) =>
        `${m[1]}() drives motion from wall-clock time, not from the frame. Components are pure functions of their props — derive the value from useCurrentFrame() instead.`);
    },
  },
  {
    id: "linear-easing",
    level: "error",
    law: "A1",
    run(ctx) {
      const re = /\bEasing\.linear\b/g;
      return matches(ctx, re, () =>
        `Easing.linear — the house default is thin-peak velocity (wind-up → fast burst → soft settle). Linear is only ever correct for genuinely constant motion (a marquee, a rotating rig).`);
    },
  },
  {
    id: "inline-curve",
    level: "error",
    law: "A1",
    run(ctx) {
      if (MOTION_MODULE.test(ctx.file)) return [];
      // Strings intact: the CSS form lives inside a quoted literal.
      const re = /cubic-bezier\s*\(|\bEasing\.bezier\s*\(/g;
      return matches({ code: ctx.text }, re, () =>
        `Curve defined inline. Curves are defined once in src/motion.ts (EASE / EASE_OUT / EASE_IN) and imported — a curve redefined at the call site is how a piece ends up with six near-identical eases and no consistent feel.`);
    },
  },
  {
    id: "unclamped-interpolate",
    level: "warn",
    law: "A1",
    run(ctx) {
      const out = [];
      const re = /\binterpolate\s*\(/g;
      let m;
      while ((m = re.exec(ctx.code))) {
        const open = ctx.code.indexOf("(", m.index);
        const { text } = balanced(ctx.code, open, "(", ")");
        if (/extrapolate(Left|Right)?\s*:/.test(text)) continue;
        out.push({
          offset: m.index,
          message: `interpolate() without extrapolateLeft/Right — Remotion extends the curve past its range by default, so values keep drifting outside the window. Clamp unless the overshoot is deliberate.`,
        });
      }
      return out;
    },
  },
  {
    id: "animated-layout-prop",
    level: "error",
    law: "A7",
    run(ctx) {
      const out = [];
      const animated = frameDerivedNames(ctx.code);
      const viaName = animated.size
        ? new RegExp(`\\b(${[...animated].join("|")})\\b`)
        : null;
      // Style-object form only (`width:`), never the JSX-attribute form
      // (`width={…}`) — SVG geometry attributes are legitimate to animate.
      const re = /(?<![A-Za-z0-9_$.])(width|height|top|left|right|bottom|minWidth|maxWidth|minHeight|maxHeight|margin|marginTop|marginRight|marginBottom|marginLeft|padding|paddingTop|paddingRight|paddingBottom|paddingLeft|flexBasis|gap)\s*:/g;
      let m;
      while ((m = re.exec(ctx.code))) {
        const colon = m.index + m[0].length - 1;
        const value = propValue(ctx.code, colon);
        if (!FRAME_DERIVED.test(value) && !(viaName && viaName.test(value))) continue;
        out.push({
          offset: m.index,
          message: `\`${m[1]}\` is animated from the frame — layout properties trigger layout + paint every frame. Animate transform / opacity / filter instead. If this is a deliberate container morph, waive it with a reason.`,
        });
      }
      return out;
    },
  },
  {
    id: "blur-on-perspective",
    level: "error",
    law: "A5",
    run(ctx) {
      const out = [];
      // Strings intact: `filter: \`blur(${x}px)\`` hides its evidence in a template.
      const src = ctx.text;
      const re = /\bperspective\s*:/g;
      let m;
      while ((m = re.exec(src))) {
        // Widen to the enclosing object literal, then look for a filter on it.
        const objStart = src.lastIndexOf("{", m.index);
        if (objStart === -1) continue;
        const { text } = balanced(src, objStart, "{", "}");
        if (!/\b(filter|backdropFilter)\s*:/.test(text)) continue;
        if (!/\b(blur|url)\s*\(/.test(text)) continue;
        out.push({
          offset: m.index,
          message: `A filter and \`perspective\` on the same element — a CSS filter flattens the 3D space it is applied to, collapsing every depth plane inside it. Apply blur to the individual planes, never to the shared perspective wrapper.`,
        });
      }
      return out;
    },
  },
];

/** Cross-file heuristic: the same device, called identically, everywhere. */
const BUILT_IN_COMPONENTS = new Set([
  "AbsoluteFill", "Sequence", "Series", "Composition", "Still", "Folder",
  "Audio", "Video", "OffthreadVideo", "Img", "IFrame", "Loop", "Freeze",
  "Player", "Thumbnail", "Fragment", "Suspense", "StrictMode", "ErrorBoundary",
]);

function collectDeviceUses(ctx, registry) {
  const re = /<([A-Z][A-Za-z0-9_.]*)/g;
  let m;
  while ((m = re.exec(ctx.code))) {
    const name = m[1];
    if (BUILT_IN_COMPONENTS.has(name) || BUILT_IN_COMPONENTS.has(name.split(".").pop())) continue;

    let i = m.index + m[0].length;
    let depth = 0;
    while (i < ctx.code.length) {
      const c = ctx.code[i];
      if (c === "{") depth++;
      else if (c === "}") depth--;
      else if (c === ">" && depth === 0) break;
      i++;
    }
    const props = ctx.code.slice(m.index + m[0].length, i).replace(/\/$/, "").trim();
    if (!props.includes("=")) continue; // generics and bare tags carry no props

    const key = `${name}|${props.replace(/\s+/g, " ")}`;
    if (!registry.has(key)) registry.set(key, { name, uses: [] });
    registry.get(key).uses.push({ file: ctx.file, ...ctx.at(m.index) });
  }
}

/* ------------------------------------------------------------------ *
 * Engine
 * ------------------------------------------------------------------ */

function matches(ctx, re, message) {
  const out = [];
  let m;
  while ((m = re.exec(ctx.code))) out.push({ offset: m.index, message: message(m) });
  return out;
}

function readWaivers(raw) {
  const file = new Set();
  const byLine = new Map();
  raw.split("\n").forEach((text, idx) => {
    const next = text.match(/klik-lint-disable-next-line\s+([\w-*,\s]+)/);
    if (next) {
      const set = byLine.get(idx + 2) || new Set();
      next[1].split(/[,\s]+/).filter(Boolean).forEach((r) => set.add(r));
      byLine.set(idx + 2, set);
      return;
    }
    const whole = text.match(/klik-lint-disable\s+([\w-*,\s]+)/);
    if (whole) whole[1].split(/[,\s]+/).filter(Boolean).forEach((r) => file.add(r));
  });
  return { file, byLine };
}

function waived(waivers, rule, line) {
  if (waivers.file.has(rule) || waivers.file.has("*")) return true;
  const set = waivers.byLine.get(line);
  return !!set && (set.has(rule) || set.has("*"));
}

function walk(target, acc) {
  let stat;
  try { stat = statSync(target); } catch { return acc; }
  if (stat.isFile()) {
    if (SOURCE_EXT.has(target.slice(target.lastIndexOf(".")))) acc.push(target);
    return acc;
  }
  if (!stat.isDirectory()) return acc;
  for (const entry of readdirSync(target)) {
    if (entry.startsWith(".") && entry !== ".") continue;
    if (SKIP_DIR.has(entry)) continue;
    walk(join(target, entry), acc);
  }
  return acc;
}

function lint(paths) {
  const files = [];
  for (const p of paths) walk(resolve(p), files);

  const findings = [];
  const devices = new Map();

  for (const file of files.sort()) {
    const raw = readFileSync(file, "utf8");
    const code = blankNonCode(raw);
    const text = blankNonCode(raw, false);
    const rel = relative(process.cwd(), file) || file;
    const at = lineIndex(raw);
    const waivers = readWaivers(raw);
    const ctx = { file: rel, code, text, at };

    for (const rule of RULES) {
      for (const hit of rule.run(ctx)) {
        const { line, col } = at(hit.offset);
        if (waived(waivers, rule.id, line)) continue;
        findings.push({ file: rel, line, col, rule: rule.id, level: rule.level, law: rule.law, message: hit.message });
      }
    }
    collectDeviceUses(ctx, devices);
  }

  for (const { name, uses } of devices.values()) {
    if (uses.length < 3) continue;
    const where = uses.map((u) => `${u.file}:${u.line}`).join(", ");
    findings.push({
      file: uses[0].file,
      line: uses[0].line,
      col: uses[0].col,
      rule: "repeated-device",
      level: "warn",
      law: "A14",
      message: `<${name}> is used ${uses.length}× with byte-identical props (${where}). No device is reused unvaried — direction, magnitude and period must differ between uses. Parameterising is not varying: verify the variation reaches the render, not just the call site.`,
    });
  }

  findings.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line || a.col - b.col);
  return { files: files.length, findings };
}

/* ------------------------------------------------------------------ *
 * Reporting
 * ------------------------------------------------------------------ */

const tty = process.stdout.isTTY;
const paint = (code, s) => (tty ? `\x1b[${code}m${s}\x1b[0m` : s);
const red = (s) => paint("31", s);
const yellow = (s) => paint("33", s);
const dim = (s) => paint("2", s);
const bold = (s) => paint("1", s);

function report({ files, findings }, strict) {
  const errors = findings.filter((f) => f.level === "error").length;
  const warns = findings.length - errors;

  if (!findings.length) {
    console.log(`${bold("klik-anim motion lint")} — clean across ${files} file${files === 1 ? "" : "s"}.`);
    console.log(dim("Mechanical laws only. The A9 look-pass and Part D still apply."));
    return 0;
  }

  console.log(`${bold("klik-anim motion lint")} — ${red(`${errors} error${errors === 1 ? "" : "s"}`)}, ${yellow(`${warns} warning${warns === 1 ? "" : "s"}`)} across ${files} file${files === 1 ? "" : "s"}\n`);

  let current = null;
  for (const f of findings) {
    if (f.file !== current) { current = f.file; console.log(bold(current)); }
    const tag = f.level === "error" ? red("error") : yellow(" warn");
    console.log(`  ${dim(`${f.line}:${f.col}`.padEnd(8))} ${tag}  ${f.rule} ${dim(`[${f.law}]`)}`);
    console.log(`           ${f.message}\n`);
  }

  const failing = errors > 0 || (strict && warns > 0);
  console.log(failing
    ? red("Fix before rendering — Part D gates on these (items 1, 2, 11).")
    : yellow("Warnings only. Review each; waive with a reason if deliberate."));
  return failing ? 1 : 0;
}

/* ------------------------------------------------------------------ *
 * CLI
 * ------------------------------------------------------------------ */

const argv = process.argv.slice(2);
if (argv.includes("--help") || argv.includes("-h")) {
  console.log(`klik-anim motion lint — the craft laws a machine can check.

  node lint-motion.mjs [paths...] [--strict] [--json]

  paths     files or directories to scan (default: src)
  --strict  warnings fail the run too
  --json    machine-readable output

Rules: nondeterministic-source [A0] · wall-clock-timer [A0] · linear-easing [A1]
       inline-curve [A1] · unclamped-interpolate [A1] · animated-layout-prop [A7]
       blur-on-perspective [A5] · repeated-device [A14]

Waive a deliberate violation, always with a reason:
  // klik-lint-disable-next-line animated-layout-prop — deliberate container morph`);
  process.exit(0);
}

const strict = argv.includes("--strict");
const json = argv.includes("--json");
const targets = argv.filter((a) => !a.startsWith("--"));
const result = lint(targets.length ? targets : ["src"]);

if (json) {
  console.log(JSON.stringify(result, null, 2));
  const errors = result.findings.filter((f) => f.level === "error").length;
  process.exit(errors > 0 || (strict && result.findings.length > errors) ? 1 : 0);
}

process.exit(report(result, strict));
