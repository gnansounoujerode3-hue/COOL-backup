# Knowledge pack: B-roll sources (deep provider notes)

Layer-3 know-how for `adapters/broll-retrieval.md` + `tools/broll_corpus.py`. The
adapter says *what* to do; this says *how each source actually behaves* and where it
bites. Free-first ordering: the no-key sources are listed first.

## Free, no key

### Archive.org (`archive`)
- Search: `advancedsearch.php?q=(<query>) AND mediatype:(movies)&output=json`. Returns
  `response.docs[]` with `identifier`, `title`, `description`, `subject`, `licenseurl`.
- **File URL is NOT in search results.** Resolve lazily: `GET /metadata/<identifier>` ->
  `files[]`, pick the smallest `.mp4/.ogv/.webm`, download from
  `/download/<identifier>/<filename>`. `broll_corpus.py resolve_file_url` does this.
- Thumb: `/services/img/<identifier>` (always works, no resolve).
- License: varies per item - many are CC-BY / CC-BY-SA / public domain, but **check
  `licenseurl`**. Some items are "no known copyright" not "free to reuse". Log it.
- Gotcha: a lot of archival footage is interlaced / low-res / .ogv. Expect to upscale
  (adapters/enhance.md) and deinterlace (`-vf yadif`) old clips.

### Wikimedia Commons (`wikimedia`)
- Search via the MediaWiki API: `action=query&generator=search&gsrnamespace=6&gsrsearch=<q> filetype:video&prop=imageinfo&iiprop=url|size|extmetadata`.
- License is in `extmetadata.LicenseShortName` - usually CC-BY-SA or public domain.
  **CC-BY-SA requires attribution + share-alike** - fine for most uses but log the author.
- Mostly `.webm`/`.ogv`. Direct `imageinfo.url` is the file (no second resolve needed).
- Gotcha: video coverage is thinner than image coverage; for many topics you will get
  more usable *stills* (use `filetype:bitmap`) and Ken-Burns them.

### NASA Images & Video Library (`nasa`)
- Search: `images-api.nasa.gov/search?q=<q>&media_type=video`. Returns `collection.items[]`.
- **Asset URL needs a second hop:** each item's `href` is a `collection.json` listing the
  actual files; pick the `.mp4`. `resolve_file_url` handles it via the stored `_collection`.
- License: **public domain** (NASA material generally is) - cleanest of all sources. Still
  do not imply NASA endorsement.
- Great for: space, earth, science, weather, aircraft, launches. Useless for: people,
  products, everyday life.

## Free, needs a key (in local/.env)

### Pexels (`pexels`, `PEXELS_API_KEY`)
- Video search: `api.pexels.com/videos/search?query=<q>` header `Authorization: <key>`.
- Pick the highest-width entry in `video_files[]`. `image` is the thumbnail. `duration` given.
- License: **Pexels License - free, no attribution required, commercial OK.** Cleanest keyed source.
- Rate limit: 200 req/hour, 20k/month on the free tier. Build a wide corpus once, search it
  many times (the build/search split exists for this).
- Best general-purpose modern B-roll (people, lifestyle, business, product).

### Pixabay (`pixabay`, `PIXABAY_API_KEY`)
- Video search: `pixabay.com/api/videos/?key=<key>&q=<q>`. `hits[].videos.{large,medium,small}.url`.
- License: **Pixabay Content License - free, commercial OK**, no attribution required (some
  trademarks/people may have limits - do not use recognizable faces for endorsement).
- Thumb: derived from `picture_id` via the vimeocdn pattern (best-effort; may 404 - falls back
  to no thumb, which only affects CLIP ranking, not text ranking).

### Unsplash (`unsplash`, `UNSPLASH_ACCESS_KEY`) - STILLS ONLY
- Photo search: `api.unsplash.com/search/photos?query=<q>` header `Authorization: Client-ID <key>`.
- License: **Unsplash License - free, commercial OK**, attribution appreciated not required.
- **Images, not video.** Every Unsplash result MUST get `camera_move: ken-burns` in the scene
  plan or it trips the slideshow-risk `weak_motion` dimension. Use for texture / establishing
  stills, not as the backbone of a montage.

## Ranking: text vs CLIP

- Default ranker is pure-stdlib text relevance over title + tags + description. $0, no deps.
- Install `sentence-transformers pillow` and `broll_corpus.py` auto-switches to CLIP: it
  embeds the query text and each candidate's **thumbnail** with `clip-ViT-B-32` and ranks by
  cosine. Use when the clip must visually match, not just be tagged. First run downloads the
  ~600MB model; cache it once.
- CLIP needs thumbnails. Pixabay's derived thumb sometimes 404s -> that candidate scores 0 on
  CLIP. If a key source has weak thumbs, prefer the text ranker for it.

## Provenance is mandatory

Every cutaway shipped must have its `license` + `page_url` logged in `broll-manifest.json`.
This is both the Radical Transparency rule and an actual rights record. CC-BY / CC-BY-SA need
the author credited somewhere (description / end card); public-domain and Pexels/Pixabay/Unsplash
do not, but log them anyway so the next person knows.
