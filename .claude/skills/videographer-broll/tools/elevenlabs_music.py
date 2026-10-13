"""Music + SFX generator for video-orchestrator (C1), wrapping ElevenLabs.

Two real generators plus a free auth check:
  check : GET /v1/user  - proves the key works + shows tier/credits. $0. (the smoke)
  sfx   : POST /v1/sound-generation - a transition stinger / whoosh / impact. cheap.
  music : POST /v1/music - a score bed from a text prompt. (confirm endpoint/params
          against the current ElevenLabs Music docs - see knowledge/elevenlabs-audio.md;
          endpoint is overridable with --endpoint.)

Subscription-first: the smoke test is `check` (no generation, no spend). Actual
`sfx` / `music` calls cost credits and only run when you invoke them explicitly.

Key: ELEVENLABS_API_KEY from local/.env (or env). Optional Suno is documented in
the adapter, not wired here (Suno has no stable public API key for this account yet).

Usage:
  python elevenlabs_music.py check
  python elevenlabs_music.py sfx   --text "cinematic whoosh transition" --duration 2 --out sfx.mp3
  python elevenlabs_music.py music --prompt "warm lo-fi piano under a flower-shop story" --ms 20000 --out bed.mp3

Exit codes: 0 ok, 2 error (missing key, http error).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_ROOT / "local" / ".env"
BASE = "https://api.elevenlabs.io"


def die(msg: str) -> None:
    print(f"elevenlabs: {msg}", file=sys.stderr)
    sys.exit(2)


def get_key() -> str:
    import os

    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ELEVENLABS_API_KEY=") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    die("no ELEVENLABS_API_KEY in env or local/.env")
    return ""


def post(url: str, key: str, payload: dict, expect_audio: bool) -> bytes:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg" if expect_audio else "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def get(url: str, key: str) -> bytes:
    req = urllib.request.Request(url, headers={"xi-api-key": key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def cmd_check(key: str) -> int:
    # /v1/voices is a free GET that proves the key authenticates. We do NOT use
    # /v1/user here: scoped keys (which this account uses) commonly lack the
    # user_read permission and 401 on /v1/user while still being fully valid for
    # generation endpoints. A 200 here = the key is live and authorized.
    try:
        raw = get(f"{BASE}/v1/voices", key)
    except urllib.error.HTTPError as exc:
        die(f"auth check failed: HTTP {exc.code} {exc.reason} (key invalid or revoked)")
    except Exception as exc:  # noqa: BLE001
        die(f"auth check failed: {exc}")
    voices = json.loads(raw.decode("utf-8", "replace")).get("voices", [])
    # subscription is best-effort (needs user_read scope); never fatal
    tier = "unknown (scoped key, user_read not granted)"
    try:
        sub = json.loads(get(f"{BASE}/v1/user/subscription", key).decode("utf-8", "replace"))
        tier = sub.get("tier", tier)
    except Exception:  # noqa: BLE001
        pass
    print("elevenlabs: auth OK (key is live)")
    print(f"  voices reachable: {len(voices)}")
    print(f"  tier: {tier}")
    print("  music + sfx generation endpoints use this same key. (no generation run - free-first)")
    return 0


def cmd_sfx(key: str, text: str, duration: float, out: Path) -> int:
    payload = {"text": text, "duration_seconds": max(0.5, min(duration, 22.0)), "prompt_influence": 0.3}
    try:
        audio = post(f"{BASE}/v1/sound-generation", key, payload, expect_audio=True)
    except urllib.error.HTTPError as exc:
        die(f"sfx failed: HTTP {exc.code} {exc.reason}: {exc.read().decode('utf-8','replace')[:200]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"elevenlabs sfx: {out} ({len(audio)} bytes)")
    return 0


def cmd_music(key: str, prompt: str, ms: int, out: Path, endpoint: str) -> int:
    payload = {"prompt": prompt, "music_length_ms": int(ms)}
    try:
        audio = post(f"{BASE}{endpoint}", key, payload, expect_audio=True)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        die(f"music failed: HTTP {exc.code} {exc.reason}: {body}\n"
            f"  if this is a 404/422, confirm the Music endpoint/params in knowledge/elevenlabs-audio.md "
            f"and pass --endpoint. The wrapper is endpoint-agnostic on purpose.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"elevenlabs music: {out} ({len(audio)} bytes)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ElevenLabs music + SFX")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    ps = sub.add_parser("sfx")
    ps.add_argument("--text", required=True)
    ps.add_argument("--duration", type=float, default=2.0)
    ps.add_argument("--out", default="sfx.mp3")
    pm = sub.add_parser("music")
    pm.add_argument("--prompt", required=True)
    pm.add_argument("--ms", type=int, default=20000)
    pm.add_argument("--out", default="bed.mp3")
    pm.add_argument("--endpoint", default="/v1/music")
    args = ap.parse_args()

    key = get_key()
    if args.cmd == "check":
        return cmd_check(key)
    if args.cmd == "sfx":
        return cmd_sfx(key, args.text, args.duration, Path(args.out))
    if args.cmd == "music":
        return cmd_music(key, args.prompt, args.ms, Path(args.out), args.endpoint)
    return 2


if __name__ == "__main__":
    sys.exit(main())
