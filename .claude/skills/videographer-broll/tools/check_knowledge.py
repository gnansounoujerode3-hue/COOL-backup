"""Knowledge-pack link checker for video-orchestrator (C5).

Scans the skill for references to knowledge/<name>.md and confirms each referenced
pack exists. Keeps adapters honest: a thin adapter that links to a missing pack is a
dangling reference. Also reports packs that exist but are not referenced anywhere
(informational - unreferenced packs are allowed, just flagged).

Usage:
  python check_knowledge.py

Exit codes: 0 = every referenced pack exists, 2 = at least one dangling reference.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
KNOW_DIR = SKILL_ROOT / "knowledge"
SCAN_DIRS = ["adapters", "pipelines", "qa", "selection", "knowledge", "templates", "tools"]
SCAN_FILES = ["SKILL.md", "README.md"]
REF_RE = re.compile(r"knowledge/([a-z0-9][a-z0-9-]*)\.md")


def gather_scan_targets() -> list[Path]:
    targets: list[Path] = []
    for d in SCAN_DIRS:
        p = SKILL_ROOT / d
        if p.is_dir():
            targets.extend(sorted(p.rglob("*.md")))
            targets.extend(sorted(p.rglob("*.py")))
    for f in SCAN_FILES:
        fp = SKILL_ROOT / f
        if fp.is_file():
            targets.append(fp)
    return targets


def main() -> int:
    if not KNOW_DIR.is_dir():
        print(f"check_knowledge: no knowledge/ dir at {KNOW_DIR}", file=sys.stderr)
        return 2

    existing = {p.stem for p in KNOW_DIR.glob("*.md") if p.stem.upper() != "INDEX"}
    referenced: dict[str, list[str]] = {}

    for fpath in gather_scan_targets():
        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue
        for m in REF_RE.findall(text):
            if m.upper() == "INDEX":
                continue
            referenced.setdefault(m, []).append(str(fpath.relative_to(SKILL_ROOT)))

    missing = {name: srcs for name, srcs in referenced.items() if name not in existing}
    orphan = sorted(existing - set(referenced))

    print(f"check_knowledge: {len(existing)} packs, {len(referenced)} referenced, "
          f"{len(missing)} dangling, {len(orphan)} unreferenced")
    print("\npacks present:")
    for name in sorted(existing):
        refs = referenced.get(name, [])
        mark = "ok " if refs else "(unreferenced)"
        print(f"  {mark} knowledge/{name}.md  <- {len(refs)} ref(s)")

    if missing:
        print("\nDANGLING references (pack does not exist):", file=sys.stderr)
        for name, srcs in sorted(missing.items()):
            print(f"  MISSING knowledge/{name}.md  referenced by: {', '.join(sorted(set(srcs)))}", file=sys.stderr)
        return 2

    if orphan:
        print("\nunreferenced packs (allowed, listed in knowledge/INDEX.md):")
        for name in orphan:
            print(f"  - knowledge/{name}.md")

    print("\nOK: every referenced knowledge pack exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
