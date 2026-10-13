"""B-roll retrieval engine for video-orchestrator.

Free-first stock/archive B-roll: build a candidate corpus from open sources,
search it by transcript / scene-intent text, and fetch the chosen clips.

Sources (free, no key):   archive  (Archive.org movies)
                          wikimedia (Wikimedia Commons video)
                          nasa     (NASA image+video library, public domain)
Sources (free key):       pexels   (PEXELS_API_KEY)      video + image
                          pixabay  (PIXABAY_API_KEY)      video
                          unsplash (UNSPLASH_ACCESS_KEY)  image only (stills/Ken Burns)

Search ranking:
  - If `sentence-transformers` (clip-ViT-B-32) is installed, candidates are
    ranked by CLIP cosine between the query text and each candidate's thumbnail
    image (true visual retrieval).
  - Otherwise it falls back to a pure-stdlib text-relevance score over each
    candidate's title + tags + description. The fallback always runs, so a smoke
    test needs no extra deps. CLIP is an opt-in quality upgrade.

This is subscription-first: it spends $0. Stock APIs are free; CLIP runs local.

Usage:
  python broll_corpus.py build  --query "city skyline night" --sources archive,wikimedia --out corpus.json
  python broll_corpus.py search --corpus corpus.json --query "founder at a desk" --topk 5
  python broll_corpus.py find   --query "ocean waves" --sources archive --topk 3        # build+search
  python broll_corpus.py fetch  --corpus corpus.json --id <candidate_id> --out ./broll/

Exit codes: 0 ok, 2 error / no results.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

SKILL_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_ROOT / "local" / ".env"
UA = "video-orchestrator-broll/1.0 (+https://github.com/kivimedia/videographer-skill)"
TIMEOUT = 20

FREE_SOURCES = ("archive", "wikimedia", "nasa")
KEYED_SOURCES = ("pexels", "pixabay", "unsplash")
ALL_SOURCES = FREE_SOURCES + KEYED_SOURCES


# --------------------------------------------------------------------------- #
# env + http helpers
# --------------------------------------------------------------------------- #
def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    # process env wins so callers can override
    for k in ("PEXELS_API_KEY", "PIXABAY_API_KEY", "UNSPLASH_ACCESS_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def http_json(url: str, headers: dict[str, str] | None = None) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def http_bytes(url: str, headers: dict[str, str] | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def q(text: str) -> str:
    return urllib.parse.quote(text)


# --------------------------------------------------------------------------- #
# candidate shape
# --------------------------------------------------------------------------- #
def candidate(
    *,
    source: str,
    cid: str,
    title: str,
    description: str = "",
    tags: Iterable[str] = (),
    media_type: str = "video",
    page_url: str = "",
    file_url: str = "",
    thumb_url: str = "",
    duration_sec: float | None = None,
    width: int | None = None,
    height: int | None = None,
    license: str = "",
) -> dict[str, Any]:
    return {
        "id": f"{source}:{cid}",
        "source": source,
        "title": (title or "").strip(),
        "description": (description or "").strip(),
        "tags": [str(t).strip() for t in tags if str(t).strip()],
        "media_type": media_type,
        "page_url": page_url,
        "file_url": file_url,
        "thumb_url": thumb_url,
        "duration_sec": duration_sec,
        "width": width,
        "height": height,
        "license": license,
    }


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #
def src_archive(query: str, limit: int) -> list[dict[str, Any]]:
    qq = f"({query}) AND mediatype:(movies)"
    url = (
        "https://archive.org/advancedsearch.php?q="
        + q(qq)
        + "&fl[]=identifier&fl[]=title&fl[]=description&fl[]=subject&fl[]=licenseurl"
        + f"&sort[]=downloads+desc&rows={limit}&page=1&output=json"
    )
    out: list[dict[str, Any]] = []
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  archive: {exc}", file=sys.stderr)
        return out
    for d in (data.get("response", {}).get("docs", []) or []):
        ident = d.get("identifier")
        if not ident:
            continue
        subj = d.get("subject")
        tags = subj if isinstance(subj, list) else ([subj] if subj else [])
        desc = d.get("description")
        if isinstance(desc, list):
            desc = " ".join(str(x) for x in desc)
        out.append(
            candidate(
                source="archive",
                cid=ident,
                title=d.get("title", ident),
                description=desc or "",
                tags=tags,
                page_url=f"https://archive.org/details/{ident}",
                file_url="",  # resolved lazily at fetch via metadata API
                thumb_url=f"https://archive.org/services/img/{ident}",
                license=d.get("licenseurl", "Archive.org item (see page)"),
            )
        )
    return out


def src_wikimedia(query: str, limit: int) -> list[dict[str, Any]]:
    url = (
        "https://commons.wikimedia.org/w/api.php?action=query&format=json"
        "&generator=search&gsrnamespace=6"
        f"&gsrsearch={q(query + ' filetype:video')}&gsrlimit={limit}"
        "&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=320"
    )
    out: list[dict[str, Any]] = []
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  wikimedia: {exc}", file=sys.stderr)
        return out
    pages = (data.get("query", {}) or {}).get("pages", {}) or {}
    for page in pages.values():
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {}) or {}
        lic = (meta.get("LicenseShortName", {}) or {}).get("value", "")
        title = page.get("title", "").replace("File:", "")
        out.append(
            candidate(
                source="wikimedia",
                cid=str(page.get("pageid", title)),
                title=title,
                description=re.sub("<[^>]+>", "", (meta.get("ImageDescription", {}) or {}).get("value", "") or ""),
                page_url=ii.get("descriptionurl", ""),
                file_url=ii.get("url", ""),
                thumb_url=ii.get("thumburl", ""),
                width=ii.get("width"),
                height=ii.get("height"),
                license=lic or "see Commons page",
            )
        )
    return out


def src_nasa(query: str, limit: int) -> list[dict[str, Any]]:
    url = f"https://images-api.nasa.gov/search?q={q(query)}&media_type=video&page_size={limit}"
    out: list[dict[str, Any]] = []
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  nasa: {exc}", file=sys.stderr)
        return out
    for item in (data.get("collection", {}).get("items", []) or [])[:limit]:
        d = (item.get("data") or [{}])[0]
        nasa_id = d.get("nasa_id")
        if not nasa_id:
            continue
        links = item.get("links") or []
        thumb = next((l.get("href") for l in links if l.get("render") == "image"), "")
        out.append(
            candidate(
                source="nasa",
                cid=nasa_id,
                title=d.get("title", nasa_id),
                description=d.get("description", ""),
                tags=d.get("keywords", []) or [],
                page_url=f"https://images.nasa.gov/details/{nasa_id}",
                file_url="",  # resolved via collection.json (item.href) at fetch
                thumb_url=thumb,
                license="Public Domain (NASA)",
            )
        )
        out[-1]["_collection"] = item.get("href", "")
    return out


def src_pexels(query: str, limit: int, env: dict[str, str]) -> list[dict[str, Any]]:
    key = env.get("PEXELS_API_KEY")
    if not key:
        print("  pexels: no PEXELS_API_KEY (skipping)", file=sys.stderr)
        return []
    url = f"https://api.pexels.com/videos/search?query={q(query)}&per_page={limit}"
    out: list[dict[str, Any]] = []
    try:
        data = http_json(url, headers={"Authorization": key})
    except Exception as exc:  # noqa: BLE001
        print(f"  pexels: {exc}", file=sys.stderr)
        return out
    for v in (data.get("videos", []) or []):
        files = sorted(v.get("video_files", []) or [], key=lambda f: (f.get("width") or 0))
        # prefer the largest file <= 1920 wide (right-sized for 1080p output, avoids
        # downloading a 4K master); fall back to the smallest available
        capped = [f for f in files if (f.get("width") or 0) <= 1920]
        best = capped[-1] if capped else (files[0] if files else {})
        out.append(
            candidate(
                source="pexels",
                cid=str(v.get("id")),
                title=(v.get("user", {}) or {}).get("name", "Pexels clip"),
                description=v.get("url", ""),
                page_url=v.get("url", ""),
                file_url=best.get("link", ""),
                thumb_url=v.get("image", ""),
                duration_sec=v.get("duration"),
                width=best.get("width"),
                height=best.get("height"),
                license="Pexels License (free, no attribution required)",
            )
        )
    return out


def src_pixabay(query: str, limit: int, env: dict[str, str]) -> list[dict[str, Any]]:
    key = env.get("PIXABAY_API_KEY")
    if not key:
        print("  pixabay: no PIXABAY_API_KEY (skipping)", file=sys.stderr)
        return []
    url = f"https://pixabay.com/api/videos/?key={key}&q={q(query)}&per_page={max(3, min(limit, 200))}"
    out: list[dict[str, Any]] = []
    try:
        data = http_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  pixabay: {exc}", file=sys.stderr)
        return out
    for h in (data.get("hits", []) or []):
        streams = h.get("videos", {}) or {}
        best = streams.get("large") or streams.get("medium") or streams.get("small") or {}
        out.append(
            candidate(
                source="pixabay",
                cid=str(h.get("id")),
                title=(h.get("tags") or "Pixabay clip"),
                description=h.get("pageURL", ""),
                tags=[t.strip() for t in (h.get("tags") or "").split(",")],
                page_url=h.get("pageURL", ""),
                file_url=best.get("url", ""),
                # Pixabay's real per-size thumbnail field (older picture_id/vimeocdn
                # guess was wrong -> blinded CLIP to all Pixabay clips). Often still
                # empty server-side, in which case Pixabay's rich tags carry the text
                # ranker and CLIP is best left to the image-rich sources (Pexels).
                thumb_url=(best.get("thumbnail") or streams.get("large", {}).get("thumbnail") or ""),
                duration_sec=h.get("duration"),
                width=best.get("width"),
                height=best.get("height"),
                license="Pixabay Content License (free)",
            )
        )
    return out


def src_unsplash(query: str, limit: int, env: dict[str, str]) -> list[dict[str, Any]]:
    key = env.get("UNSPLASH_ACCESS_KEY")
    if not key:
        print("  unsplash: no UNSPLASH_ACCESS_KEY (skipping)", file=sys.stderr)
        return []
    url = f"https://api.unsplash.com/search/photos?query={q(query)}&per_page={limit}"
    out: list[dict[str, Any]] = []
    try:
        data = http_json(url, headers={"Authorization": f"Client-ID {key}"})
    except Exception as exc:  # noqa: BLE001
        print(f"  unsplash: {exc}", file=sys.stderr)
        return out
    for p in (data.get("results", []) or []):
        urls = p.get("urls", {}) or {}
        out.append(
            candidate(
                source="unsplash",
                cid=str(p.get("id")),
                title=p.get("description") or p.get("alt_description") or "Unsplash photo",
                description=p.get("alt_description", "") or "",
                tags=[t.get("title", "") for t in (p.get("tags") or [])],
                media_type="image",
                page_url=(p.get("links", {}) or {}).get("html", ""),
                file_url=urls.get("full", "") or urls.get("regular", ""),
                thumb_url=urls.get("small", "") or urls.get("thumb", ""),
                width=p.get("width"),
                height=p.get("height"),
                license="Unsplash License (free; still image - use with Ken Burns / pan)",
            )
        )
    return out


SOURCE_FUNCS = {
    "archive": lambda query, limit, env: src_archive(query, limit),
    "wikimedia": lambda query, limit, env: src_wikimedia(query, limit),
    "nasa": lambda query, limit, env: src_nasa(query, limit),
    "pexels": src_pexels,
    "pixabay": src_pixabay,
    "unsplash": src_unsplash,
}


# --------------------------------------------------------------------------- #
# ranking
# --------------------------------------------------------------------------- #
_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall((text or "").lower()))


def text_score(query: str, cand: dict[str, Any]) -> float:
    """Pure-stdlib relevance: token overlap (Jaccard-ish) + fuzzy ratio."""
    hay = " ".join([cand.get("title", ""), cand.get("description", ""), " ".join(cand.get("tags", []))])
    qt, ht = _tokens(query), _tokens(hay)
    overlap = len(qt & ht) / len(qt) if qt else 0.0
    fuzzy = SequenceMatcher(None, query.lower(), (cand.get("title", "") or "").lower()).ratio()
    return round(0.7 * overlap + 0.3 * fuzzy, 4)


# Sources whose API gives rich descriptive tags/titles -> the text ranker is
# reliable. vs sources with great poster images but useless titles (Pexels titles
# are uploader names) -> CLIP visual ranking is reliable. The 'auto' ranker scores
# each source by its strength. (Learned 2026-06-30: ranking Pexels by its title
# text, or Pixabay by a thumbnail it doesn't provide, both fail.)
TAG_RICH_SOURCES = {"pixabay", "wikimedia", "nasa", "archive"}
IMAGE_RICH_SOURCES = {"pexels", "unsplash"}

_CLIP_MODEL = None
_CLIP_TRIED = False


def _clip_model():
    """Load clip-ViT-B-32 once (cached). None if sentence-transformers is absent."""
    global _CLIP_MODEL, _CLIP_TRIED
    if _CLIP_TRIED:
        return _CLIP_MODEL
    _CLIP_TRIED = True
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        _CLIP_MODEL = SentenceTransformer("clip-ViT-B-32")
    except Exception:  # noqa: BLE001
        _CLIP_MODEL = None
    return _CLIP_MODEL


def _clip_sims(model, query: str, cands: list[dict[str, Any]]) -> dict[str, float]:
    """Cosine(query_text, candidate_thumbnail) per candidate that has a usable
    thumbnail. Candidates with no/failed thumbnail are omitted (caller falls back)."""
    try:
        from io import BytesIO

        from PIL import Image  # type: ignore
        from sentence_transformers import util  # type: ignore
    except Exception:  # noqa: BLE001
        return {}
    qvec = model.encode([query])
    sims: dict[str, float] = {}
    for c in cands:
        if not c.get("thumb_url"):
            continue
        try:
            img = Image.open(BytesIO(http_bytes(c["thumb_url"]))).convert("RGB")
            sims[c["id"]] = float(util.cos_sim(qvec, model.encode([img]))[0][0])
        except Exception:  # noqa: BLE001
            continue
    return sims


def _minmax(vals: dict[str, float]) -> dict[str, float]:
    if not vals:
        return {}
    lo, hi = min(vals.values()), max(vals.values())
    if hi - lo < 1e-9:
        return {k: 0.75 for k in vals}
    return {k: (v - lo) / (hi - lo) for k, v in vals.items()}


def clip_rank(query: str, cands: list[dict[str, Any]], topk: int):
    """All-CLIP ranking (every candidate by thumbnail). None if CLIP unavailable."""
    model = _clip_model()
    if model is None:
        return None
    sims = _clip_sims(model, query, cands)
    scored = [{**c, "score": round(sims.get(c["id"], 0.0), 4), "rank_method": "clip"} for c in cands]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:topk]


def rank(query: str, cands: list[dict[str, Any]], topk: int, mode: str = "auto") -> list[dict[str, Any]]:
    """Rank candidates.

    mode='text' : text relevance over title+tags+description. Fast, $0, no deps.
    mode='clip' : CLIP image relevance for every candidate (needs thumbnails).
    mode='auto' : source-aware (default). Tag-rich sources -> text; image-rich
                  sources (Pexels/Unsplash) -> CLIP by thumbnail. Scores are
                  min-max normalized WITHIN each method, then merged. Ties prefer
                  the text method (tags are trustworthy). Degrades to all-text if
                  CLIP is not installed.
    """
    if not cands:
        return []
    if mode == "text":
        scored = [{**c, "score": text_score(query, c), "rank_method": "text"} for c in cands]
        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored[:topk]
    if mode == "clip":
        return clip_rank(query, cands, topk) or rank(query, cands, topk, mode="text")

    # auto: rank each source by its strength
    model = _clip_model()
    image_grp = [c for c in cands if c["source"] in IMAGE_RICH_SOURCES] if model else []
    clip_raw = _clip_sims(model, query, image_grp) if image_grp else {}
    # everything not CLIP-scored (tag-rich sources + image-source clips with no thumb)
    text_raw = {c["id"]: text_score(query, c) for c in cands if c["id"] not in clip_raw}

    text_norm = _minmax(text_raw)
    clip_norm = _minmax(clip_raw)

    out = []
    for c in cands:
        if c["id"] in clip_norm:
            out.append({**c, "score": round(clip_norm[c["id"]], 4),
                        "raw": round(clip_raw[c["id"]], 4), "rank_method": "clip"})
        else:
            out.append({**c, "score": round(text_norm.get(c["id"], 0.0), 4),
                        "raw": round(text_raw.get(c["id"], 0.0), 4), "rank_method": "text"})
    out.sort(key=lambda c: (c["score"], c["rank_method"] == "text", c.get("raw", 0.0)), reverse=True)
    return out[:topk]


# --------------------------------------------------------------------------- #
# fetch resolution
# --------------------------------------------------------------------------- #
VIDEO_EXTS = (".mp4", ".webm", ".ogv", ".mov", ".m4v")


def resolve_file_url(cand: dict[str, Any]) -> str:
    if cand.get("file_url"):
        return cand["file_url"]
    if cand["source"] == "archive":
        ident = cand["id"].split(":", 1)[1]
        meta = http_json(f"https://archive.org/metadata/{ident}")
        files = meta.get("files", []) or []
        vids = [f for f in files if str(f.get("name", "")).lower().endswith(VIDEO_EXTS)]
        vids.sort(key=lambda f: int(f.get("size", 0) or 0))
        if vids:
            return f"https://archive.org/download/{ident}/{urllib.parse.quote(vids[0]['name'])}"
    if cand["source"] == "nasa" and cand.get("_collection"):
        coll = http_json(cand["_collection"])
        items = coll if isinstance(coll, list) else coll.get("items", [])
        for href in items:
            if isinstance(href, str) and href.lower().endswith(VIDEO_EXTS):
                return href
    return ""


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def do_build(query: str, sources: list[str], limit: int, out: Path, env: dict[str, str]) -> list[dict[str, Any]]:
    cands: list[dict[str, Any]] = []
    print(f"build: query={query!r} sources={','.join(sources)} limit={limit}/source")
    for s in sources:
        fn = SOURCE_FUNCS.get(s)
        if not fn:
            print(f"  unknown source: {s}", file=sys.stderr)
            continue
        got = fn(query, limit, env)
        print(f"  {s}: {len(got)} candidates")
        cands.extend(got)
    corpus = {"query": query, "sources": sources, "count": len(cands), "candidates": cands}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2), encoding="utf-8")
    print(f"build: wrote {len(cands)} candidates -> {out}")
    return cands


def print_ranked(ranked: list[dict[str, Any]]) -> None:
    method = ranked[0]["rank_method"] if ranked else "none"
    print(f"\nranked (method={method}):")
    for i, c in enumerate(ranked, 1):
        dur = f"{c['duration_sec']}s" if c.get("duration_sec") else "?"
        print(f"  {i}. [{c['score']}] ({c['source']}/{c['media_type']}/{dur}) {c['title'][:70]}")
        print(f"       id={c['id']}  lic={c.get('license','')[:40]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="B-roll corpus builder + search")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build")
    pb.add_argument("--query", required=True)
    pb.add_argument("--sources", default="archive,wikimedia,nasa")
    pb.add_argument("--limit", type=int, default=12)
    pb.add_argument("--out", default="corpus.json")

    ps = sub.add_parser("search")
    ps.add_argument("--corpus", required=True)
    ps.add_argument("--query", required=True)
    ps.add_argument("--topk", type=int, default=5)
    ps.add_argument("--out", default="")

    pf = sub.add_parser("find")  # build + search in one
    pf.add_argument("--query", required=True)
    pf.add_argument("--sources", default="archive,wikimedia,nasa")
    pf.add_argument("--limit", type=int, default=12)
    pf.add_argument("--topk", type=int, default=5)
    pf.add_argument("--out", default="")

    pg = sub.add_parser("fetch")
    pg.add_argument("--corpus", required=True)
    pg.add_argument("--id", required=True)
    pg.add_argument("--out", default="./broll/")

    args = ap.parse_args()
    env = load_env()

    if args.cmd in ("build", "find"):
        sources = [s.strip() for s in args.sources.split(",") if s.strip()]
        corpus_path = Path(args.out) if (args.cmd == "build" and args.out) else SKILL_ROOT / "tools" / ".broll-corpus.json"
        cands = do_build(args.query, sources, args.limit, corpus_path, env)
        if args.cmd == "build":
            return 0 if cands else 2
        ranked = rank(args.query, cands, args.topk)
        print_ranked(ranked)
        if args.out:
            Path(args.out).write_text(json.dumps(ranked, indent=2), encoding="utf-8")
            print(f"\nfind: wrote ranked -> {args.out}")
        return 0 if ranked else 2

    if args.cmd == "search":
        corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
        cands = corpus.get("candidates", [])
        if not cands:
            print("search: corpus has no candidates", file=sys.stderr)
            return 2
        ranked = rank(args.query, cands, args.topk)
        print_ranked(ranked)
        if args.out:
            Path(args.out).write_text(json.dumps(ranked, indent=2), encoding="utf-8")
            print(f"\nsearch: wrote ranked -> {args.out}")
        return 0 if ranked else 2

    if args.cmd == "fetch":
        corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
        cand = next((c for c in corpus.get("candidates", []) if c["id"] == args.id), None)
        if not cand:
            print(f"fetch: id not found in corpus: {args.id}", file=sys.stderr)
            return 2
        file_url = resolve_file_url(cand)
        if not file_url:
            print(f"fetch: could not resolve a downloadable file for {args.id}", file=sys.stderr)
            print(f"       open the page manually: {cand.get('page_url','')}", file=sys.stderr)
            return 2
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = next((e for e in VIDEO_EXTS if file_url.lower().split("?")[0].endswith(e)), ".mp4")
        safe = re.sub(r"[^a-z0-9]+", "-", args.id.lower()).strip("-")
        dest = out_dir / f"{safe}{ext}"
        print(f"fetch: {file_url}\n   -> {dest}")
        dest.write_bytes(http_bytes(file_url))
        print(f"fetch: {dest.stat().st_size} bytes. license: {cand.get('license','')}")
        return 0

    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
