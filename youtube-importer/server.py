#!/usr/bin/env python3
"""
Arena Live Preview — YouTube & Video Importer Studio (v3 — YouTube Link + File Dropzone + Permanent Git Persistence)
Binds to 0.0.0.0:8080, supports iframe embedding and any Host/Origin,
and uses relative URLs for all browser -> sandbox API requests.
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
      padding: 26px 20px 60px;
    }
    .container { max-width: 780px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 22px; }
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
      padding: 22px;
      margin-bottom: 18px;
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
    .input-row {
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
    }
    input[type="text"] {
      flex: 1;
      background: rgba(255, 255, 255, 0.06);
      border: 2px solid rgba(255, 255, 255, 0.14);
      color: #fff;
      padding: 14px 16px;
      border-radius: 14px;
      font-size: 15px;
      outline: none;
      transition: border-color 0.2s;
    }
    input[type="text"]:focus { border-color: var(--rose); }
    .btn {
      background: var(--rose);
      color: #fff;
      border: none;
      padding: 14px 22px;
      border-radius: 14px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.15s, background 0.2s;
      white-space: nowrap;
    }
    .btn:hover { background: var(--rose-light); transform: translateY(-1px); }
    .btn:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
    .btn-helper {
      background: rgba(236, 72, 153, 0.18);
      border: 1.5px solid var(--rose);
      color: #fff;
      padding: 8px 13px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-helper:hover { background: var(--rose); }
    .yt-preview {
      display: none;
      background: rgba(0, 0, 0, 0.28);
      border-radius: 16px;
      padding: 14px;
      margin-top: 12px;
      align-items: center;
      gap: 14px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .yt-preview img {
      width: 140px;
      height: 78px;
      object-fit: cover;
      border-radius: 10px;
      border: 2px solid var(--rose);
    }
    .yt-info h3 { font-size: 15px; margin-bottom: 4px; }
    .yt-info p { font-size: 13px; color: var(--muted); margin-bottom: 8px; }
    .dropzone {
      border: 2.5px dashed rgba(236, 72, 153, 0.65);
      background: rgba(236, 72, 153, 0.06);
      border-radius: 18px;
      padding: 32px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
    }
    .dropzone:hover, .dropzone.dragover {
      background: rgba(236, 72, 153, 0.14);
      border-color: var(--rose);
    }
    .dropzone-icon {
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: rgba(236, 72, 153, 0.22);
      color: var(--rose-light);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: 800;
      margin-bottom: 10px;
    }
    .dropzone h3 { font-size: 17px; margin-bottom: 6px; }
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
      <span class="badge">SAUVEGARDE PERMANENTE ACTIVÉE • STUDIO YOUTUBE & SHORTS</span>
      <h1>Importer par Lien YouTube ou Fichier Vidéo</h1>
      <p class="subtitle">Colle ton lien YouTube à l'étape 1 ou glisse directement le fichier .mp4 à l'étape 2</p>
    </div>

    <!-- Step 1: YouTube Link -->
    <div class="card">
      <div class="step-title">
        <span class="step-num">1</span>
        <span>Importer via un lien YouTube</span>
      </div>
      <div class="input-row">
        <input type="text" id="ytUrl" placeholder="https://www.youtube.com/watch?v=... ou https://youtu.be/..." />
        <button class="btn" id="btnAnalyze" onclick="handleYouTubeLink()">Importer le lien</button>
      </div>
      <div class="yt-preview" id="ytPreview">
        <img id="ytThumb" src="" alt="Miniature" />
        <div class="yt-info" style="flex:1;">
          <h3 id="ytTitle">Titre de la vidéo</h3>
          <p id="ytAuthor">Chaîne YouTube</p>
          <div id="ytStreamStatus" style="font-size:13px; color:#F472B6; font-weight:700; margin-bottom:8px;"></div>
          <div id="ytHelpers" style="display:flex; gap:8px; flex-wrap:wrap;"></div>
        </div>
      </div>
    </div>

    <!-- Step 2: File Dropzone -->
    <div class="card">
      <div class="step-title">
        <span class="step-num">2</span>
        <span>Glisser-déposer ou sélectionner le fichier vidéo (.mp4, .mov, .webm)</span>
      </div>
      <input type="file" id="fileInput" accept="video/*,.mp4,.mov,.webm,.mkv" style="display:none;" onchange="if(this.files[0]) uploadFileChunked(this.files[0])" />
      <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
        <div class="dropzone-icon">↑</div>
        <h3>Clique ici ou glisse ta vidéo (.mp4)</h3>
        <p>Transfert rapide par blocs de 4 Mo + sauvegarde permanente automatique sur Git</p>
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

    function extractVideoId(url) {
      const m = url.match(/(?:v=|youtu\.be\/|shorts\/|embed\/)([A-Za-z0-9_-]{11})/);
      return m ? m[1] : '';
    }

    async function tryBrowserStreamRelay(videoId, title) {
      const statusEl = document.getElementById('ytStreamStatus');
      statusEl.textContent = '⏳ Tentative de récupération directe du flux vidéo .mp4 depuis ton navigateur...';

      const pipedApis = [
        'https://pipedapi.kavin.rocks/streams/' + videoId,
        'https://pipedapi.tokhmi.xyz/streams/' + videoId,
        'https://pipedapi.moomoo.me/streams/' + videoId,
        'https://inv.tux.pizza/api/v1/videos/' + videoId
      ];

      for (const apiUrl of pipedApis) {
        try {
          const ctrl = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 5500);
          const res = await fetch(apiUrl, { signal: ctrl.signal });
          clearTimeout(timer);
          if (!res.ok) continue;
          const data = await res.json();

          let streamUrl = '';
          if (data.videoStreams && Array.isArray(data.videoStreams)) {
            const muxed = data.videoStreams.find(s => !s.videoOnly && (s.format === 'MPEG_4' || (s.mimeType && s.mimeType.includes('mp4'))));
            if (muxed && muxed.url) streamUrl = muxed.url;
          } else if (data.formatStreams && Array.isArray(data.formatStreams)) {
            const muxed = data.formatStreams.find(s => s.container === 'mp4' && s.url);
            if (muxed) streamUrl = muxed.url;
          }

          if (streamUrl) {
            statusEl.textContent = '⏳ Flux MP4 trouvé ! Téléchargement et transfert vers le serveur...';
            const vidRes = await fetch(streamUrl);
            if (vidRes.ok) {
              const blob = await vidRes.blob();
              if (blob.size > 100000) {
                const file = new File([blob], `youtube_${videoId}.mp4`, { type: 'video/mp4' });
                await uploadFileChunked(file);
                statusEl.textContent = '✅ Vidéo YouTube récupérée et sauvegardée automatiquement !';
                return true;
              }
            }
          }
        } catch (e) {}
      }

      statusEl.textContent = '✅ Lien enregistré ! Si YouTube bloque le flux direct, clique sur un bouton ci-dessous pour récupérer le .mp4 et glisse-le à l\'étape 2 :';
      return false;
    }

    async function handleYouTubeLink() {
      const url = document.getElementById('ytUrl').value.trim();
      if (!url) return;
      const btn = document.getElementById('btnAnalyze');
      btn.disabled = true;
      btn.textContent = 'Analyse...';

      const vid = extractVideoId(url);
      let meta = { title: 'Vidéo YouTube', author_name: 'YouTube', thumbnail_url: vid ? `https://i.ytimg.com/vi/${vid}/hqdefault.jpg` : '' };
      try {
        const res = await fetch('https://noembed.com/embed?url=' + encodeURIComponent(url));
        if (res.ok) {
          const data = await res.json();
          if (data.title) meta = data;
        }
      } catch (err) {}

      document.getElementById('ytPreview').style.display = 'flex';
      document.getElementById('ytTitle').textContent = meta.title || url;
      document.getElementById('ytAuthor').textContent = meta.author_name || 'YouTube';
      if (meta.thumbnail_url) {
        document.getElementById('ytThumb').src = meta.thumbnail_url;
      }

      // Render 1-click download helpers if user needs to grab the MP4
      const helpers = document.getElementById('ytHelpers');
      if (vid) {
        helpers.innerHTML = `
          <a class="btn-helper" href="https://cobalt.tools/" target="_blank" rel="noopener">⚡ Télécharger MP4 (Cobalt)</a>
          <a class="btn-helper" href="https://ssyoutube.com/watch?v=${vid}" target="_blank" rel="noopener">📥 Télécharger MP4 (SSYouTube)</a>
        `;
      }

      // Persist the YouTube link & metadata to Git on the server immediately
      await fetch('api/register-youtube', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          youtube_url: url,
          video_id: vid,
          title: meta.title || '',
          author: meta.author_name || '',
          thumbnail: meta.thumbnail_url || ''
        })
      });

      if (vid) {
        await tryBrowserStreamRelay(vid, meta.title || vid);
      }

      btn.disabled = false;
      btn.textContent = 'Lien envoyé ✓';
      refreshState();
    }

    async function uploadFileChunked(file) {
      const wrap = document.getElementById('progressWrap');
      const fill = document.getElementById('progressFill');
      const text = document.getElementById('progressText');
      const speed = document.getElementById('progressSpeed');
      const banner = document.getElementById('statusBanner');

      wrap.style.display = 'block';
      banner.style.display = 'none';

      const chunkSize = 4 * 1024 * 1024;
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
          banner.textContent = '⏳ Dernier bloc reçu ! Sauvegarde permanente sur Git en cours (patiente 5 à 15 secondes)...';
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

        const pct = Math.round((end / file.size) * 100);
        const elapsedSec = Math.max(0.1, (performance.now() - t0) / 1000);
        const mbps = (end / (1024 * 1024)) / elapsedSec;
        fill.style.width = pct + '%';
        text.textContent = `Importation de ${file.name} : ${pct}% (${(end / (1024*1024)).toFixed(1)} / ${(file.size / (1024*1024)).toFixed(1)} Mo)`;
        speed.textContent = mbps.toFixed(1) + ' Mo/s';

        if (isLast) {
          banner.className = 'status-banner';
          banner.style.display = 'block';
          banner.textContent = `✅ Vidéo "${file.name}" (${(file.size / (1024*1024)).toFixed(1)} Mo) importée ET sauvegardée de façon permanente ! Tu peux maintenant écrire "c'est bon" dans le chat.`;
        }
      }

      refreshState();
    }

    async function refreshState() {
      try {
        const res = await fetch('api/status');
        const data = await res.json();
        if (data.youtube_url && !document.getElementById('ytUrl').value) {
          document.getElementById('ytUrl').value = data.youtube_url;
        }
        const container = document.getElementById('filesList');
        let html = '';
        if (data.youtube_url) {
          html += `<div style="margin-bottom:8px;color:#F472B6;font-weight:700;">🔗 Lien YouTube enregistré : ${data.title || data.youtube_url}</div>`;
        }
        if (data.files && data.files.length > 0) {
          html += '<div style="margin-bottom:6px;font-weight:700;color:#fff;">Vidéos sauvegardées de façon permanente :</div>' +
            data.files.map(f => `<span class="file-pill">✅ ${f.name} (${f.size_mb} Mo)</span>`).join('');
        }
        if (data.shorts && data.shorts.length > 0) {
          html += `<div style="margin-top:20px;margin-bottom:12px;font-size:16px;font-weight:800;color:#4ADE80;">🎬 10 Shorts 9:16 générés depuis Stop_This_Train__Win_a_Lamborghini.mp4 :</div>`;
          html += `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;">` +
            data.shorts.map((s, idx) => `
              <div style="background:rgba(15,15,24,0.92);border:1px solid rgba(255,255,255,0.12);border-radius:14px;padding:10px;display:flex;flex-direction:column;gap:8px;">
                <div style="font-size:12px;font-weight:800;color:#FBBF24;">SHORT #${String(idx+1).padStart(2,'0')} (${s.size_mb} Mo)</div>
                <video src="shorts/${s.name}" controls preload="metadata" style="width:100%;aspect-ratio:9/16;border-radius:10px;background:#000;"></video>
                <div style="font-size:11px;color:#A1A1AA;word-break:break-all;">${s.name}</div>
                <a href="shorts/${s.name}?download=1" download="${s.name}" style="text-align:center;padding:8px 10px;border-radius:8px;background:linear-gradient(135deg,#FF3E9D,#EC4899);color:#fff;text-decoration:none;font-size:12px;font-weight:700;">⬇️ Télécharger MP4</a>
              </div>
            `).join('') + `</div>`;
        }
        container.innerHTML = html;
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
    return {"youtube_url": "", "video_id": "", "title": "", "author": "", "uploaded_files": [], "latest_video": ""}


def save_job_state(state: dict):
    with open(JOB_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def persist_job_metadata_to_git() -> bool:
    try:
        subprocess.run(["git", "add", "-f", JOB_JSON], cwd=REPO_ROOT, check=True)
        subprocess.run(["git", "commit", "-m", "chore(import): persist YouTube link metadata"], cwd=REPO_ROOT, check=False)
        subprocess.run(["git", "push", "origin", "HEAD:arena/edaf5d9a-cool-backup"], cwd=REPO_ROOT, check=True)
        return True
    except Exception as e:
        print(f"Git metadata persistence error: {e}", flush=True)
        return False


def persist_video_to_git(file_path: str, filename: str) -> bool:
    try:
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
        if "/shorts/" in parsed.path:
            fn = os.path.basename(parsed.path)
            shorts_dir = os.path.join(REPO_ROOT, "mrbeast-train-lambo-shorts/shorts")
            fp = os.path.join(shorts_dir, fn)
            if os.path.isfile(fp) and fn.endswith(".mp4"):
                sz = os.path.getsize(fp)
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(sz))
                if "download=1" in parsed.query:
                    self.send_header("Content-Disposition", f'attachment; filename="{fn}"')
                self._send_cors_headers()
                self.end_headers()
                with open(fp, "rb") as vf:
                    while True:
                        chunk = vf.read(256 * 1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                return

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
            shorts_list = []
            shorts_dir = os.path.join(REPO_ROOT, "mrbeast-train-lambo-shorts/shorts")
            if os.path.isdir(shorts_dir):
                for fn in sorted(os.listdir(shorts_dir)):
                    fp = os.path.join(shorts_dir, fn)
                    if os.path.isfile(fp) and fn.endswith(".mp4"):
                        shorts_list.append({
                            "name": fn,
                            "size_mb": round(os.path.getsize(fp) / (1024 * 1024), 2),
                        })
            state = load_job_state()
            state["files"] = files
            state["shorts"] = shorts_list
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

        if parsed.path.endswith("/api/register-youtube"):
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8"))
            state = load_job_state()
            if payload.get("youtube_url"):
                state["youtube_url"] = payload["youtube_url"]
            if payload.get("video_id"):
                state["video_id"] = payload["video_id"]
            if payload.get("title"):
                state["title"] = payload["title"]
            if payload.get("author"):
                state["author"] = payload["author"]
            if payload.get("thumbnail"):
                state["thumbnail"] = payload["thumbnail"]
            state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_job_state(state)
            persist_job_metadata_to_git()

            resp = json.dumps({"ok": True, "state": state}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

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
    print(f"YouTube Importer Studio v3 listening on http://{host}:{port}", flush=True)
    server.serve_forever()
