#!/usr/bin/env python3
"""Analyse structurelle d'une archive zip volumineuse, sans extraction complète.

Produit dans _analysis/ :
  SUMMARY.txt   - statistiques globales et marqueurs de projet
  EXT.txt       - répartition par extension
  DIRS.txt      - répartition par dossier (profondeur 1 et 2)
  LARGEST.txt   - plus gros fichiers
  TREE.txt      - arborescence (profondeur 4, compressée)
  PREVIEW.txt   - aperçu du contenu textuel des fichiers importants
"""
import os
import zipfile
import collections
import json

ZIP = "COOL.zip"
OUT = "_analysis"

TEXT_EXT = {
    ".txt", ".md", ".markdown", ".json", ".jsonl", ".js", ".mjs", ".cjs", ".ts",
    ".tsx", ".jsx", ".py", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".env", ".sh", ".bash",
    ".zsh", ".sql", ".php", ".rb", ".go", ".rs", ".java", ".kt", ".c", ".h",
    ".cpp", ".hpp", ".cs", ".swift", ".dart", ".vue", ".svelte", ".astro",
    ".xml", ".gradle", ".lock", ".gitignore", ".gitattributes", ".dockerfile",
    ".editorconfig", ".prettierrc", ".eslintrc", ".bat", ".ps1", ".r", ".m",
    ".lua", ".pl", ".ex", ".exs", ".clj", ".sol", ".tf", ".csv", ".tsv",
}

MARKERS = [
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements.txt", "pyproject.toml", "Pipfile", "poetry.lock",
    "composer.json", "Gemfile", "Cargo.toml", "go.mod", "pom.xml",
    "build.gradle", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "vercel.json", "netlify.toml", "next.config.js", "next.config.mjs",
    "next.config.ts", "vite.config.js", "vite.config.ts", "angular.json",
    "nuxt.config.js", "tailwind.config.js", "tailwind.config.ts",
    "tsconfig.json", "README.md", "readme.md", "README.txt", ".gitignore",
    ".env", ".env.local", ".env.example", "manage.py", "app.py", "main.py",
    "index.html", "index.js", "index.ts", "start.sh", "run.sh",
]

INTERESTING = [
    "package.json", "README.md", "readme.md", "README.txt", "requirements.txt",
    "pyproject.toml", "composer.json", "Dockerfile", "docker-compose.yml",
    ".env.example", "index.html", "app.py", "main.py", "manage.py",
    "next.config.js", "next.config.mjs", "next.config.ts", "vite.config.ts",
    "vite.config.js", "vercel.json", "netlify.toml", "tsconfig.json",
    "app/layout.tsx", "app/page.tsx", "src/App.js", "src/App.tsx",
    "src/main.js", "src/main.ts", "src/index.js", "src/index.ts",
]

MAX_PREVIEW_BYTES = 3_500_000
MAX_FILE_PREVIEW = 60_000
MAX_LISTING_BYTES = 1_800_000

os.makedirs(OUT, exist_ok=True)

zf = zipfile.ZipFile(ZIP)
infos = zf.infolist()

files = [i for i in infos if not i.is_dir()]
dirs = [i for i in infos if i.is_dir()]

total_c = sum(i.compress_size for i in infos)
total_u = sum(i.file_size for i in infos)

s = []
s.append("=" * 78)
s.append(f"ANALYSE DE L'ARCHIVE : {ZIP}")
s.append("=" * 78)
s.append(f"Taille du fichier zip          : {os.path.getsize(ZIP):,} octets "
         f"({os.path.getsize(ZIP) / 1048576:.1f} MiB)")
s.append(f"Entrées dans l'index          : {len(infos)}")
s.append(f"  - fichiers                  : {len(files)}")
s.append(f"  - dossiers                  : {len(dirs)}")
s.append(f"Taille compressée (somme)     : {total_c:,} octets ({total_c / 1048576:.1f} MiB)")
s.append(f"Taille décompressée (somme)   : {total_u:,} octets ({total_u / 1048576:.1f} MiB)")
if total_c:
    s.append(f"Ratio de compression          : {total_u / total_c:.2f}x")
if zf.comment:
    s.append(f"Commentaire de l'archive      : {zf.comment[:300]!r}")

try:
    dates = sorted(i.date_time for i in infos if i.date_time[0] > 1980)
    s.append(f"Date min (interne zip)        : {dates[0]}")
    s.append(f"Date max (interne zip)        : {dates[-1]}")
except Exception:
    pass

# --- chemins ---
paths = [i.filename for i in files]
top = collections.Counter()
for p in paths:
    parts = p.split("/")
    top["/".join(parts[:1])] += 1
s.append("")
s.append("--- Racine: nombre d'entrées par premier niveau (top 40) ---")
for name, cnt in top.most_common(40):
    s.append(f"  {cnt:>8}  {name}")

# --- profondeur ---
maxdepth = max((len(p.rstrip("/").split("/")) for p in paths), default=0)
s.append("")
s.append(f"Profondeur maximale des chemins : {maxdepth}")

# --- cas particuliers ---
n_git = sum(1 for p in paths if "/.git/" in p or p.startswith(".git/"))
n_nm = sum(1 for p in paths if "node_modules/" in p)
n_venv = sum(1 for p in paths if "/venv/" in p or p.startswith("venv/") or "/.venv/" in p)
n_next = sum(1 for p in paths if "/.next/" in p or p.startswith(".next/"))
n_dist = sum(1 for p in paths if "/dist/" in p or p.startswith("dist/"))
n_windows = sum(1 for p in paths if "__MACOSX" in p or "Thumbs.db" in p)
s.append(f"Entrées .git (dépôt git inclus) : {n_git}")
s.append(f"Entrées node_modules           : {n_nm}")
s.append(f"Entrées venv/.venv             : {n_venv}")
s.append(f"Entrées .next (build Next.js)  : {n_next}")
s.append(f"Entrées dist/build             : {n_dist}")
s.append(f"Entrées parasites macOS/Windows: {n_windows}")

# --- extensions ---
ext_counter = collections.Counter()
ext_size = collections.Counter()
for i in files:
    base = os.path.basename(i.filename)
    ext = os.path.splitext(base)[1].lower()
    if base.startswith(".") and base.count(".") == 1:
        ext = base.lower()
    ext = ext or "(sans extension)"
    ext_counter[ext] += 1
    ext_size[ext] += i.file_size

s.append("")
s.append("--- Extensions (top 45 par nombre) ---")
s.append(f"  {'ext':<18} {'nb':>8} {'taille décompressée':>22}")
for ext, cnt in ext_counter.most_common(45):
    s.append(f"  {ext:<18} {cnt:>8} {ext_size[ext]:>22,}")

# --- plus gros fichiers ---
s.append("")
s.append("--- 30 plus gros fichiers ---")
for i in sorted(files, key=lambda x: -x.file_size)[:30]:
    s.append(f"  {i.file_size:>12,}  {i.filename}")

# --- marqueurs de projet ---
bases = collections.defaultdict(list)
for p in paths:
    bases[os.path.basename(p)].append(p)

s.append("")
s.append("--- Fichiers marqueurs détectés (chemin dans l'archive) ---")
found = False
for m in MARKERS:
    if m in bases:
        locs = sorted(bases[m], key=len)[:5]
        s.append(f"  {m:<24} -> {', '.join(locs)}")
        found = True
for extra in ("*.sln", "*.csproj", "*.xcodeproj", "*.apk", "*.exe", "*.db", "*.sqlite", "*.sqlite3", "*.mp4", "*.pdf", "*.docx", "*.xlsx", "*.psd", "*.zip", "*.tar", "*.gz", "*.rar", "*.7z"):
    if extra in ext_counter:
        s.append(f"  {extra:<24} -> {ext_counter[extra]} exemplaire(s)")
        found = True
if not found:
    s.append("  (aucun marqueur classique trouvé)")

# --- signature par extension dominante ---
s.append("")
s.append("--- Interprétation rapide ---")
guesses = []
if ext_counter.get(".tsx") or ext_counter.get(".jsx") or ext_counter.get(".ts") or "next.config.js" in bases or "next.config.mjs" in bases or "next.config.ts" in bases:
    guesses.append("Projet JavaScript/TypeScript (web / Node)")
if ext_counter.get(".py") or "requirements.txt" in bases or "pyproject.toml" in bases:
    guesses.append("Présence de Python")
if ext_counter.get(".php") or "composer.json" in bases:
    guesses.append("Présence de PHP")
if ext_counter.get(".html") and not guesses:
    guesses.append("Site web statique / HTML")
if n_git:
    guesses.append("Contient un dépôt Git complet (.git)")
if n_nm:
    guesses.append("Contient des dépendances node_modules (archive alourdie)")
if ext_counter.get(".mp4") or ext_counter.get(".mov") or ext_counter.get(".avi"):
    guesses.append("Contient des vidéos")
if ext_counter.get(".pdf"):
    guesses.append("Contient des PDF")
if not guesses:
    guesses.append("Type indéterminé à partir des seules extensions")
for g in guesses:
    s.append(f"  - {g}")

with open(os.path.join(OUT, "SUMMARY.txt"), "w", encoding="utf-8", errors="replace") as f:
    f.write("\n".join(s) + "\n")

# --- fichiers annexes ---
with open(os.path.join(OUT, "EXT.txt"), "w", encoding="utf-8", errors="replace") as f:
    for ext, cnt in ext_counter.most_common():
        f.write(f"{ext}\t{cnt}\t{ext_size[ext]}\n")

dir_depth = {1: collections.Counter(), 2: collections.Counter(), 3: collections.Counter()}
dir_size = {1: collections.Counter(), 2: collections.Counter(), 3: collections.Counter()}
for i in files:
    parts = i.filename.split("/")
    for d in (1, 2, 3):
        key = "/".join(parts[:d]) or "(racine)"
        dir_depth[d][key] += 1
        dir_size[d][key] += i.file_size
with open(os.path.join(OUT, "DIRS.txt"), "w", encoding="utf-8", errors="replace") as f:
    for d in (1, 2, 3):
        f.write(f"\n===== PROFONDEUR {d} — top 60 par taille =====\n")
        for k, sz in dir_size[d].most_common(60):
            f.write(f"{sz:>14,}  {dir_depth[d][k]:>7} fichiers  {k}\n")

with open(os.path.join(OUT, "LARGEST.txt"), "w", encoding="utf-8", errors="replace") as f:
    for i in sorted(files, key=lambda x: -x.file_size)[:300]:
        f.write(f"{i.file_size:>14,}\t{i.compress_size:>12,}\t{i.filename}\n")

# --- arborescence (profondeur 4) ---
srt = sorted(paths)
with open(os.path.join(OUT, "TREE.txt"), "w", encoding="utf-8", errors="replace") as f:
    prev = []
    n = 0
    for p in srt:
        parts = p.rstrip("/").split("/")[:4]
        if not p.split("/")[0] or (len(p.split("/")) > 4):
            parts = p.split("/")[:4] + ["..."]
        # écrire uniquement les préfixes nouveaux
        for k in range(1, len(parts) + 1):
            node = parts[:k]
            if node != prev[:k]:
                indent = "  " * (k - 1)
                pfx = node[-1]
                full = "/".join(parts[:k])
                isdir = any(q.startswith(full.rstrip("/") + "/") for q in srt[:1]) or p.count("/") >= k
                f.write(f"{indent}{pfx}{'/' if k < len(parts) else ''}\n")
                n += 1
                if n > 120000:
                    break
        prev = parts
        if n > 120000:
            f.write("...(tronqué)\n")
            break

# --- listing brut (tronqué) ---
with open(os.path.join(OUT, "LISTING.txt"), "w", encoding="utf-8", errors="replace") as f:
    written = 0
    for i in sorted(infos, key=lambda x: x.filename):
        line = f"{i.file_size:>14,}  {i.compress_size:>12,}  {i.date_time}  {i.filename}\n"
        f.write(line)
        written += len(line)
        if written > MAX_LISTING_BYTES:
            f.write("...(listing tronqué)\n")
            break

# --- aperçu textuel ---
order = sorted(paths, key=lambda p: (
    0 if os.path.basename(p) in INTERESTING else 1,
    0 if p.count("/") <= 1 else 1,
    len(p),
))

with open(os.path.join(OUT, "PREVIEW.txt"), "w", encoding="utf-8", errors="replace") as f:
    budget = MAX_PREVIEW_BYTES
    idx = {i.filename: i for i in infos}
    for p in order:
        if budget <= 0:
            break
        i = idx[p]
        ext = os.path.splitext(p)[1].lower()
        base = os.path.basename(p)
        if ext not in TEXT_EXT and not base.startswith("."):
            continue
        if i.file_size == 0 or i.file_size > 400_000:
            continue
        try:
            data = zf.read(p)[:MAX_FILE_PREVIEW]
            txt = data.decode("utf-8")
        except Exception:
            continue
        if "\x00" in txt:
            continue
        head = (f"\n{'=' * 78}\n### {p}  ({i.file_size:,} octets)\n{'=' * 78}\n")
        body = txt if len(txt) <= MAX_FILE_PREVIEW else txt + "\n...(tronqué)\n"
        chunk = head + body
        f.write(chunk)
        budget -= len(chunk)

print("Analyse terminée.")
print(open(os.path.join(OUT, "SUMMARY.txt"), encoding="utf-8").read()[:2000])
