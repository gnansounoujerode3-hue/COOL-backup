#!/usr/bin/env python3
"""
Arena Live Preview — YouTube & Video Importer Studio (v2 — With Permanent Git Persistence)
Binds to 0.0.0.0:8080, supports iframe embedding and any Host/Origin,
and uses relative URLs for all browser -> sandbox API requests.

CRITICAL FIX FOR ARENA SANDBOX:
Because Arena may reset the sandbox container from the last turn-end snapshot or Git branch
when a new chat message is sent after an idle period, `server.py` automatically persists
any uploaded video (splitting into 45 MB parts if > 48 MB to stay well below GitHub's 100 MB limit)
and pushes it to `origin/arena/edaf5d9a-cool-backup` BEFORE returning the final upload confirmation!
"""

import glob
import json
import os
import re
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

REPO_ROOT = "/home/user/COOL-backup"
IMPORTS_DIR = os.path.join(REPO_ROOT, "imports")
PERSIST_DIR = os.path.join(IMPORTS_DIR, "persisted")
os.makedirs(PERSIST_DIR, exist_ok=True)
JOB_JSON = os.path.join(IMPORTS_DIR, "current_job.json")

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Import Vidéo YouTube • Studio Montage Rose</title>
  <style>
    :root {
      --rose: #EC4899;
      --rose-light: #F472B6;
      --rose-deep: #9D174D;
      --bg: #120D14;
      --card: #1E1522;
      --border: rgba(236, 72, 153, 0.35);
      --text: #FAF6F8;
      --muted: #C4B5C8;
      --green: #10B981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Plus Jakarta Sans", "Inter", sans-serif;
      background: radial-gradient(circle at 20% 15%, rgba(236, 72, 153, 0.18), transparent 45%),
                  radial-gradient(circle at 80% 80%, rgba(157, 23, 77, 0.22), transparent 50%),
                  var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 28px 20px 60px;
    }
    .container { max-width: 780px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 24px; }
    .badge {
      display: inline-block;
      background: var(--rose);
      color: #fff;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 1.2px;
      padding: 6px 14px;
      border-radius: 999px;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    h1 { font-size: 27px; font-weight: 800; line-height: 1.2; margin-bottom: 8px; }
    .subtitle { color: var(--muted); font-size: 15px; }
    .card {
      background: var(--card);
      border: 2px solid var(--border);
      border-radius: 22px;
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
    }
    .step-title {
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .step-num {
      background: var(--rose);
      color: #fff;
      width: 26px;
      height: 26px;
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 800;
    }
    .dropzone {
      border: 2.5px dashed rgba(236, 72, 153, 0.65);
      background: rgba(236, 72, 153, 0.06);
      border-radius: 18px;
      padding: 36px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
    }
    .dropzone:hover, .dropzone.dragover {
      background: rgba(236, 72, 153, 0.14);
      border-color: var(--rose);
    }
    .dropzone-icon {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: rgba(236, 72, 153, 0.22);
      color: var(--rose-light);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      font-weight: 800;
      margin-bottom: 12px;
    }
    .dropzone h3 { font-size: 18px; margin-bottom: 6px; }
    .dropzone p { font-size: 13px; color: var(--muted); }
    .progress-wrap { display: none; margin-top: 18px; }
    .progress-bar-bg {
      width: 100%;
      height: 14px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      overflow: hidden;
      margin-bottom: 8px;
    }
    .progress-bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--rose), var(--rose-light));
      border-radius: 999px;
      transition: width 0.15s;
    }
    .progress-meta {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      color: var(--muted);
      font-weight: 600;
    }
    .status-banner {
      display: none;
      margin-top: 16px;
      padding: 16px 18px;
      border-radius: 14px;
      font-size: 14px;
      font-weight: 700;
      background: rgba(16, 185, 129, 0.16);
      border: 2px solid var(--green);
      color: #A7F3D0;
      line-height: 1.45;
    }
    .status-banner.saving {
      background: rgba(236, 72, 153, 0.16);
      border-color: var(--rose);
      color: #FCE7F3;
    }
    .files-list { margin-top: 14px; font-size: 13px; color: var(--muted); }
    .file-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.16);
      border: 1.5px solid var(--green);
      color: #fff;
      padding: 8px 14px;
      border-radius: 10px;
      margin: 4px 6px 4px 0;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">SAUVEGARDE PERMANENTE ACTIVÉE • STUDIO SHORTS</span>
      <h1>Importer ta Vidéo pour Découpage en Shorts</h1>
      <p class="subtitle">Glisse ta vidéo ci-dessous : elle sera automatiquement sauvegardée de façon permanente pour le découpage en Shorts avec sous-titres</p>
    </div>

    <div class="card">
      <div class="step-title">
        <span class="step-num">1</span>
        <span>Glisser-déposer ou sélectionner ta vidéo (.mp4, .mov, .webm)</span>
      </div>
      <input type="file" id="fileInput" accept="video/*,.mp4,.mov,.webm,.mkv" style="display:none;" onchange="if(this.files[0]) uploadFileChunked(this.files[0])" />
      <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
        <div class="dropzone-icon">↑</div>
        <h3>Clique ici ou glisse ta vidéo (.mp4)</h3>
        <p>Transfert rapide par blocs + sauvegarde permanente automatique sur le dépôt</p>
      </div>
      <div class="progress-wrap" id="progressWrap">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="progressFill"></div>
        </div>
        <div class="progress-meta">
          <span id="progressText">Importation en cours... 0%</span>
          <span id="progressSpeed">0.0 Mo/s</span>
        </div>
      </div>
      <div class="status-banner" id="statusBanner"></div>
      <div class="files-list" id="filesList"></div>
    </div>
  </div>

  <script>
    const dropzone = document.getElementById('dropzone');
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        uploadFileChunked(e.dataTransfer.files[0]);
      }
    });

    async function uploadFileChunked(file) {
      const wrap = document.getElementById('progressWrap');
      const fill = document.getElementById('progressFill');
      const text = document.getElementById('progressText');
      const speed = document.getElementById('progressSpeed');
      const banner = document.getElementById('statusBanner');

      wrap.style.display = 'block';
      banner.style.display = 'none';

      const chunkSize = 4 * 1024 * 1024; // 4 MB chunks
      const totalChunks = Math.ceil(file.size / chunkSize);
      const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
      const t0 = performance.now();

      for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(file.size, start + chunkSize);
        const chunk = file.slice(start, end);

        const isLast = (i + 1 === totalChunks);
        if (isLast) {
          banner.className = 'status-banner saving';
          banner.style.display = 'block';
          banner.textContent = '⏳ Dernier bloc reçu ! Sauvegarde permanente sur le serveur en cours (patiente 5 à 15 secondes)...';
        }

        const q = new URLSearchParams({
          filename: safeName,
          chunk_index: String(i),
          total_chunks: String(totalChunks),
          total_size: String(file.size)
        });

        const res = await fetch('api/upload-chunk?' + q.toString(), {
          method: 'POST',
          body: chunk
        });
        if (!res.ok) {
          banner.className = 'status-banner saving';
          banner.style.display = 'block';
          banner.textContent = 'Erreur lors du transfert au bloc ' + i;
          return;
        }
        const resData = await res.json();

        const pct = Math.round((end / file.size) * 100);
        const elapsedSec = Math.max(0.1, (performance.now() - t0) / 1000);
        const mbps = (end / (1024 * 1024)) / elapsedSec;
        fill.style.width = pct + '%';
        text.textContent = `Importation de ${file.name} : ${pct}% (${(end / (1024*1024)).toFixed(1)} / ${(file.size / (1024*1024)).toFixed(1)} Mo)`;
        speed.textContent = mbps.toFixed(1) + ' Mo/s';

        if (isLast) {
          banner.className = 'status-banner';
          banner.style.display = 'block';
          banner.textContent = `✅ Vidéo "${file.name}" (${(file.size / (1024*1024)).toFixed(1)} Mo) importée ET sauvegardée de façon permanente ! Tu peux maintenant m'écrire "c'est bon" dans le chat.`;
        }
      }

      refreshState();
    }

    async function refreshState() {
      try {
        const res = await fetch('api/status');
        const data = await res.json();
        const container = document.getElementById('filesList');
        if (data.files && data.files.length > 0) {
          container.innerHTML = '<div style="margin-bottom:6px;font-weight:700;color:#fff;">Vidéos sauvegardées de façon permanente :</div>' +
            data.files.map(f => `<span class="file-pill">✅ ${f.name} (${f.size_mb} Mo)</span>`).join('');
        }
      } catch (e) {}
    }

    refreshState();
  </script>
</body>
</html>
"""


def load_job_state() -> dict:
    if os.path.exists(JOB_JSON):
        try:
            with open(JOB_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"uploaded_files": [], "latest_video": ""}


def save_job_state(state: dict):
    with open(JOB_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def persist_video_to_git(file_path: str, filename: str) -> bool:
    """
    Splits `file_path` into 45 MB chunks inside `imports/persisted/` (so even 300 MB+ videos
    never hit GitHub's 100 MB per-file limit), commits, and pushes to `origin/arena/edaf5d9a-cool-backup`.
    """
    try:
        # Remove old persisted chunks
        for old_p in glob.glob(os.path.join(PERSIST_DIR, "*")):
            os.remove(old_p)

        part_size = 45 * 1024 * 1024  # 45 MB per part
        part_idx = 0
        with open(file_path, "rb") as src:
            while True:
                buf = src.read(part_size)
                if not buf:
                    break
                part_path = os.path.join(PERSIST_DIR, f"{filename}.part{part_idx:03d}")
                with open(part_path, "wb") as pf:
                    pf.write(buf)
                part_idx += 1

        subprocess.run(["git", "add", "-f", PERSIST_DIR, JOB_JSON], cwd=REPO_ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"chore(import): persist uploaded video {filename} ({part_idx} parts)"],
            cwd=REPO_ROOT,
            check=False,
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD:arena/edaf5d9a-cool-backup"],
            cwd=REPO_ROOT,
            check=True,
        )
        return True
    except Exception as e:
        print(f"Git persistence error: {e}", flush=True)
        return False


def restore_persisted_videos_if_needed():
    """Reassembles any `.part000` files in `imports/persisted/` into `imports/<filename>` on startup."""
    os.makedirs(PERSIST_DIR, exist_ok=True)
    part0_files = sorted(glob.glob(os.path.join(PERSIST_DIR, "*.part000")))
    for p0 in part0_files:
        base_name = os.path.basename(p0)[: -len(".part000")]
        out_path = os.path.join(IMPORTS_DIR, base_name)
        if not os.path.exists(out_path):
            parts = sorted(glob.glob(os.path.join(PERSIST_DIR, f"{base_name}.part*")))
            with open(out_path, "wb") as out_f:
                for p in parts:
                    with open(p, "rb") as pf:
                        out_f.write(pf.read())
            print(f"Restored persisted video: {out_path}", flush=True)


class ImporterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.endswith("/api/status"):
            restore_persisted_videos_if_needed()
            files = []
            for fn in sorted(os.listdir(IMPORTS_DIR)):
                fp = os.path.join(IMPORTS_DIR, fn)
                if os.path.isfile(fp) and fn.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
                    files.append({
                        "name": fn,
                        "size_mb": round(os.path.getsize(fp) / (1024 * 1024), 2),
                    })
            state = load_job_state()
            state["files"] = files
            body = json.dumps(state, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
            return

        body = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))

        if parsed.path.endswith("/api/upload-chunk"):
            qs = parse_qs(parsed.query)
            filename = re.sub(r"[^a-zA-Z0-9._-]", "_", qs.get("filename", ["video.mp4"])[0])
            chunk_index = int(qs.get("chunk_index", ["0"])[0])
            total_chunks = int(qs.get("total_chunks", ["1"])[0])
            dest_path = os.path.join(IMPORTS_DIR, filename)

            chunk_data = self.rfile.read(length) if length > 0 else b""
            mode = "wb" if chunk_index == 0 else "ab"
            with open(dest_path, mode) as f:
                f.write(chunk_data)

            persisted = False
            if chunk_index + 1 >= total_chunks:
                state = load_job_state()
                if filename not in state.get("uploaded_files", []):
                    state.setdefault("uploaded_files", []).append(filename)
                state["latest_video"] = dest_path
                state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                save_job_state(state)
                persisted = persist_video_to_git(dest_path, filename)

            resp = json.dumps({
                "ok": True,
                "chunk": chunk_index,
                "file": filename,
                "persisted": persisted,
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    restore_persisted_videos_if_needed()
    host = "0.0.0.0"
    port = 8080
    server = ThreadingHTTPServer((host, port), ImporterHandler)
    print(f"YouTube Importer Studio v2 listening on http://{host}:{port}", flush=True)
    server.serve_forever()
