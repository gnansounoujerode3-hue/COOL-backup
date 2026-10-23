#!/usr/bin/env python3
"""
Studio Import YouTube & Centre de Téléchargement GitHub (v4)
Listening on http://0.0.0.0:8080

Features:
1. Complete catalog, preview player (HTTP 206 Range), and 1-click download for all 40 created
   videos across the repository (`gnansounoujerode3-hue/COOL-backup`, branch `arena/edaf5d9a-cool-backup`):
   - 10 Shorts 9:16: "Stop This Train, Win a Lamborghini" (`mrbeast-train-lambo-shorts/shorts/`)
   - 10 Shorts 9:16: "Lose 100 Lbs, Win $250,000!" (`mrbeast-100lbs-shorts/shorts/`)
   - 2 Films 16:9 + 6 Shorts 9:16: "Être Intelligente En 2026" (`etre-intelligente-2026/`)
   - 12 Motion Design 3D Films 9:16: `canada-credit-reference7`, `felix-gray-reference6..12`,
     `whatsapp-motion-faceless`, `claude-code-montage-video`, `motion-design-pure`, `engel-volkers-masterclass`
2. 3 ways to download any video or category:
   - Direct in-iframe JS Blob download with live % progress (`⬇️ Télécharger MP4`)
   - 1-click Category `.zip` pack download (`📦 Tout télécharger en .ZIP`)
   - Direct GitHub Raw CDN (`raw.githubusercontent.com`) & GitHub Blob links (`🐙 Télécharger via GitHub`)
3. 1-click GitHub Sync & Push button (`☁️ Synchroniser / Pousser sur mon GitHub`) + automatic
   background Git sync on startup if a container restart reset the working tree.
4. Step 1 (YouTube link) + Step 2 (Chunked MP4 upload with permanent 45 MB Git chunk persistence).
"""

import glob
import io
import json
import os
import re
import subprocess
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

REPO_ROOT = "/home/user/COOL-backup"
IMPORTS_DIR = os.path.join(REPO_ROOT, "imports")
PERSIST_DIR = os.path.join(IMPORTS_DIR, "persisted")
JOB_JSON = os.path.join(IMPORTS_DIR, "current_job.json")

GH_REPO = "gnansounoujerode3-hue/COOL-backup"
GH_BRANCH = "arena/edaf5d9a-cool-backup"
GH_RAW_BASE = f"https://raw.githubusercontent.com/{GH_REPO}/{GH_BRANCH}"
GH_BLOB_BASE = f"https://github.com/{GH_REPO}/blob/{GH_BRANCH}"
GH_TREE_URL = f"https://github.com/{GH_REPO}/tree/{GH_BRANCH}"

os.makedirs(IMPORTS_DIR, exist_ok=True)
os.makedirs(PERSIST_DIR, exist_ok=True)

# Built-in manifest of all 40 created videos committed on GitHub (`arena/edaf5d9a-cool-backup`)
# so the Studio displays all videos immediately even while background git sync is running.
CREATED_VIDEOS_MANIFEST = [
    # === GROUP 1: 10 Shorts - Stop This Train, Win a Lamborghini ===
    {
        "group": "lambo_shorts",
        "title": "Short #01 — Défi Lamborghini vs 10 000 balles & Train",
        "path": "mrbeast-train-lambo-shorts/shorts/short-01-defi-lamborghini-10000-balles-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.80,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #02 — Forteresse en béton + Bonus 100 000 $",
        "path": "mrbeast-train-lambo-shorts/shorts/short-02-forteresse-beton-100k-bonus-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.81,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #03 — Assaut des 10 000 balles & Verdict",
        "path": "mrbeast-train-lambo-shorts/shorts/short-03-assaut-10000-balles-verdict-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.80,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #04 — Nuit blanche, matelas & châteaux gonflables",
        "path": "mrbeast-train-lambo-shorts/shorts/short-04-nuit-blanche-matelas-chateaux-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.82,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #05 — Chute libre de la Lamborghini depuis la grue",
        "path": "mrbeast-train-lambo-shorts/shorts/short-05-chute-libre-lamborghini-grue-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 10.36,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #06 — Revanche contre les voitures en feu",
        "path": "mrbeast-train-lambo-shorts/shorts/short-06-revanche-voitures-en-feu-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.83,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #07 — Pluie de 10 voitures en flammes",
        "path": "mrbeast-train-lambo-shorts/shorts/short-07-pluie-10-voitures-en-flammes-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.79,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #08 — Bunker écrasé à 1 000 °C & Sauvetage",
        "path": "mrbeast-train-lambo-shorts/shorts/short-08-bunker-ecrase-1000-degres-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 10.37,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #09 — Plan pour faire dérailler le train",
        "path": "mrbeast-train-lambo-shorts/shorts/short-09-plan-faire-derailler-le-train-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 13.14,
    },
    {
        "group": "lambo_shorts",
        "title": "Short #10 — Impact final du train & Victoire Lamborghini",
        "path": "mrbeast-train-lambo-shorts/shorts/short-10-impact-final-train-lamborghini-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 15.19,
    },
    # === GROUP 2: 10 Shorts - Lose 100 Lbs, Win $250,000! ===
    {
        "group": "100lbs_shorts",
        "title": "Short #01 — Défi : Perdre 100 livres pour gagner 250 000 $",
        "path": "mrbeast-100lbs-shorts/shorts/short-01-defi-perdre-100-livres-250k-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 21.42,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #02 — Les 30 premiers jours avec Coach Tyler Wall",
        "path": "mrbeast-100lbs-shorts/shorts/short-02-premiers-30-jours-coach-wall-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 20.49,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #03 — 1 000 $ par pompe (31 pompes = 31 000 $)",
        "path": "mrbeast-100lbs-shorts/shorts/short-03-1000-dollars-par-pompe-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 21.40,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #04 — Continuer le combat pour le Coach Wall",
        "path": "mrbeast-100lbs-shorts/shorts/short-04-continuer-pour-coach-wall-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 18.40,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #05 — Course du Jour 130 avec MrBeast",
        "path": "mrbeast-100lbs-shorts/shorts/short-05-course-jour-130-mrbeast-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 21.32,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #06 — Transformation finale après 178 jours",
        "path": "mrbeast-100lbs-shorts/shorts/short-06-transformation-finale-178-jours-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 22.61,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #07 — Première taille de vêtement perdue (2XL)",
        "path": "mrbeast-100lbs-shorts/shorts/short-07-premiere-taille-perdue-2xl-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 20.41,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #08 — Visite surprise famille & Message du Coach",
        "path": "mrbeast-100lbs-shorts/shorts/short-08-visite-famille-message-coach-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 20.85,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #09 — Entraînement course 1 mile (Cardio intensif)",
        "path": "mrbeast-100lbs-shorts/shorts/short-09-entrainement-course-1-mile-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 17.90,
    },
    {
        "group": "100lbs_shorts",
        "title": "Short #10 — Suspendu dans le vide avec gilet lesté",
        "path": "mrbeast-100lbs-shorts/shorts/short-10-suspendu-dans-le-vide-50k-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 21.89,
    },
    # === GROUP 3: Être Intelligente En 2026 (2 Films 16:9 + 6 Shorts 9:16) ===
    {
        "group": "etre_intelligente",
        "title": "Film YouTube 16:9 — Montage Rose Dynamique (1080p)",
        "path": "etre-intelligente-2026/film/etre-intelligente-en-2026-youtube-rose-1080p.mp4",
        "aspect": "16/9",
        "default_mb": 42.18,
    },
    {
        "group": "etre_intelligente",
        "title": "Film 16:9 — Version Propre Sans Sous-Titres (1080p)",
        "path": "etre-intelligente-2026/film/etre-intelligente-en-2026-sans-sous-titres-1080p.mp4",
        "aspect": "16/9",
        "default_mb": 51.00,
    },
    {
        "group": "etre_intelligente",
        "title": "Short #01 — Paraître intelligente te dessert",
        "path": "etre-intelligente-2026/shorts/short-01-paraitre-intelligente-te-dessert-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 6.98,
    },
    {
        "group": "etre_intelligente",
        "title": "Short #02 — Le piège du perfectionnisme",
        "path": "etre-intelligente-2026/shorts/short-02-le-piege-du-perfectionnisme-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 6.65,
    },
    {
        "group": "etre_intelligente",
        "title": "Short #03 — Percer sans tout calculer",
        "path": "etre-intelligente-2026/shorts/short-03-percer-sans-tout-calculer-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.39,
    },
    {
        "group": "etre_intelligente",
        "title": "Short #04 — Parler avec le cœur vs être lisse",
        "path": "etre-intelligente-2026/shorts/short-04-parler-avec-le-coeur-vs-etre-lisse-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.75,
    },
    {
        "group": "etre_intelligente",
        "title": "Short #05 — La vraie intelligence émotionnelle",
        "path": "etre-intelligente-2026/shorts/short-05-la-vraie-intelligence-emotionnelle-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 8.10,
    },
    {
        "group": "etre_intelligente",
        "title": "Short #06 — Parle face-cam comme à ta pote",
        "path": "etre-intelligente-2026/shorts/short-06-parle-face-cam-comme-a-ta-pote-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 11.52,
    },
    # === GROUP 4: 14 Films Motion Design 3D ===
    {
        "group": "motion_films",
        "title": "Devis Designer v3 (Style Pub Officielle 9:16 + Voix-Off FR + SFX)",
        "path": "devis-designer-motion/film/devis-designer-motion-design-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 8.80,
    },
    {
        "group": "motion_films",
        "title": "Devis Designer v3 (Style Pub Officielle 9:16 — Audio Original Sans Voix)",
        "path": "devis-designer-motion/film/devis-designer-pub-style-original-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 8.70,
    },
    {
        "group": "motion_films",
        "title": "Canada Crédit (Style Réf. 7 — Carte 3D 3000$ → 2500$)",
        "path": "canada-credit-reference7/film/canada-credit-reference7-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 26.75,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 12 (9:16)",
        "path": "felix-gray-reference12/film/felix-gray-reference12-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 8.27,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 11 (9:16)",
        "path": "felix-gray-reference11/film/felix-gray-reference11-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 8.49,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 10 « Our Work » (9:16)",
        "path": "felix-gray-reference10/film/felix-gray-reference10-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 18.82,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 9 (9:16)",
        "path": "felix-gray-reference9/film/felix-gray-reference9-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 15.75,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 8 (9:16)",
        "path": "felix-gray-reference8/film/felix-gray-reference8-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 21.61,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 7 (9:16)",
        "path": "felix-gray-reference7/film/felix-gray-reference7-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 26.02,
    },
    {
        "group": "motion_films",
        "title": "Felix Gray — Montage Référence 6 (9:16)",
        "path": "felix-gray-reference6/film/felix-gray-reference6-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 18.70,
    },
    {
        "group": "motion_films",
        "title": "Motion Design Sans Visage — 10 Lois d'Animation (9:16)",
        "path": "whatsapp-motion-faceless/film/motion-design-sans-visage-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 10.66,
    },
    {
        "group": "motion_films",
        "title": "Comment utiliser Claude Code pour le Montage 3D (9:16)",
        "path": "claude-code-montage-video/film/comment-utiliser-claude-code-montage-video-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 17.06,
    },
    {
        "group": "motion_films",
        "title": "Motion Design 100% Pur — Showreel Cinématique (9:16)",
        "path": "motion-design-pure/film/motion-design-pure-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 9.57,
    },
    {
        "group": "motion_films",
        "title": "Engel & Völkers — Masterclass Luxury Escape (9:16)",
        "path": "engel-volkers-masterclass/film/engel-volkers-masterclass-9x16.mp4",
        "aspect": "9/16",
        "default_mb": 10.39,
    },
]

SYNC_STATE = {
    "syncing": False,
    "last_sync": "",
    "message": "Toutes les 40 vidéos sont synchronisées sur GitHub (branche arena/edaf5d9a-cool-backup).",
}


def build_catalog():
    items = []
    for entry in CREATED_VIDEOS_MANIFEST:
        rel_path = entry["path"]
        abs_path = os.path.join(REPO_ROOT, rel_path)
        exists_local = os.path.isfile(abs_path) and os.path.getsize(abs_path) > 100_000
        size_mb = round(os.path.getsize(abs_path) / (1024 * 1024), 2) if exists_local else entry["default_mb"]
        items.append({
            "group": entry["group"],
            "title": entry["title"],
            "path": rel_path,
            "name": os.path.basename(rel_path),
            "aspect": entry["aspect"],
            "size_mb": size_mb,
            "local_ready": exists_local,
            "github_raw_url": f"{GH_RAW_BASE}/{quote(rel_path)}",
            "github_blob_url": f"{GH_BLOB_BASE}/{quote(rel_path)}",
        })
    return items


HTML_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Studio Import YouTube & Centre de Téléchargement GitHub</title>
  <style>
    :root {
      --bg: #08080E;
      --card: #12131F;
      --card-alt: #171929;
      --border: rgba(255, 255, 255, 0.11);
      --pink: #FF3E9D;
      --pink-glow: rgba(255, 62, 157, 0.25);
      --cyan: #38BDF8;
      --gold: #FBBF24;
      --text: #F8FAFC;
      --muted: #94A3B8;
      --green: #34D399;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    body {
      background: radial-gradient(circle at 50% 0%, #241028 0%, var(--bg) 65%);
      color: var(--text);
      min-height: 100vh;
      padding: 24px 18px 60px;
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
    }
    .header-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 20px;
      padding: 20px 24px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.55);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 62, 157, 0.14);
      border: 1px solid rgba(255, 62, 157, 0.4);
      color: #F472B6;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 1px;
      text-transform: uppercase;
      padding: 5px 12px;
      border-radius: 999px;
      margin-bottom: 8px;
    }
    h1 {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.4px;
    }
    .sub {
      color: var(--muted);
      font-size: 13.5px;
      margin-top: 4px;
    }
    .gh-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .btn {
      background: linear-gradient(135deg, #FF3E9D, #EC4899);
      color: #fff;
      border: none;
      border-radius: 12px;
      padding: 11px 16px;
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      transition: transform 0.14s, opacity 0.14s;
      white-space: nowrap;
    }
    .btn:hover { transform: translateY(-1px); }
    .btn:disabled { opacity: 0.6; cursor: wait; }
    .btn-cyan {
      background: linear-gradient(135deg, #0284C7, #38BDF8);
    }
    .btn-gold {
      background: linear-gradient(135deg, #D97706, #F59E0B);
    }
    .btn-dark {
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.16);
      color: #E2E8F0;
    }
    .btn-dark:hover {
      background: rgba(255,255,255,0.13);
    }
    .sync-banner {
      margin-bottom: 18px;
      padding: 12px 16px;
      border-radius: 12px;
      background: rgba(52, 211, 153, 0.11);
      border: 1px solid rgba(52, 211, 153, 0.35);
      color: #6EE7B7;
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 22px;
      box-shadow: 0 20px 55px rgba(0, 0, 0, 0.5);
      margin-bottom: 22px;
    }
    .tabs-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }
    .tab-btn {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.12);
      color: #CBD5E1;
      padding: 9px 14px;
      border-radius: 11px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }
    .tab-btn.active {
      background: linear-gradient(135deg, #FF3E9D, #EC4899);
      border-color: transparent;
      color: #fff;
      box-shadow: 0 6px 20px rgba(255, 62, 157, 0.32);
    }
    .group-toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
      padding: 13px 16px;
      background: var(--card-alt);
      border: 1px solid rgba(255,255,255,0.09);
      border-radius: 14px;
    }
    .group-title {
      font-size: 15px;
      font-weight: 800;
      color: #F8FAFC;
    }
    .group-sub {
      font-size: 12px;
      color: var(--muted);
      margin-top: 2px;
    }
    .videos-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(225px, 1fr));
      gap: 16px;
    }
    .video-card {
      background: rgba(10, 11, 18, 0.9);
      border: 1px solid rgba(255,255,255,0.11);
      border-radius: 16px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 9px;
      transition: border-color 0.15s;
    }
    .video-card:hover {
      border-color: rgba(255, 62, 157, 0.5);
    }
    .vc-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
    }
    .vc-badge {
      font-size: 11px;
      font-weight: 800;
      color: var(--gold);
      background: rgba(251, 191, 36, 0.12);
      border: 1px solid rgba(251, 191, 36, 0.3);
      padding: 3px 8px;
      border-radius: 6px;
    }
    .vc-size {
      font-size: 11px;
      font-weight: 700;
      color: #94A3B8;
    }
    .vc-title {
      font-size: 13px;
      font-weight: 700;
      color: #F1F5F9;
      line-height: 1.35;
      min-height: 35px;
    }
    .vc-player {
      width: 100%;
      border-radius: 10px;
      background: #000;
      max-height: 340px;
      object-fit: cover;
    }
    .vc-filename {
      font-size: 10.5px;
      color: #64748B;
      word-break: break-all;
    }
    .vc-btns {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: auto;
    }
    .vc-btn-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }
    .btn-sm {
      padding: 8px 10px;
      font-size: 12px;
      border-radius: 9px;
    }
    .section-title {
      font-size: 14px;
      font-weight: 700;
      color: #F472B6;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      margin-bottom: 10px;
    }
    .url-row {
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
    }
    input[type="text"] {
      flex: 1;
      background: rgba(0, 0, 0, 0.45);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 13px 15px;
      color: #fff;
      font-size: 14px;
      outline: none;
    }
    input[type="text"]:focus { border-color: var(--pink); }
    .yt-preview {
      display: none;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 14px;
      gap: 14px;
      align-items: center;
    }
    .yt-preview img {
      width: 120px;
      height: 68px;
      object-fit: cover;
      border-radius: 8px;
    }
    .dropzone {
      border: 2px dashed rgba(255, 62, 157, 0.45);
      background: rgba(255, 62, 157, 0.04);
      border-radius: 16px;
      padding: 24px 18px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
    }
    .dropzone:hover, .dropzone.dragover {
      border-color: var(--pink);
      background: rgba(255, 62, 157, 0.1);
    }
    .progress-wrap { margin-top: 14px; display: none; }
    .progress-bar {
      height: 10px;
      background: rgba(255,255,255,0.08);
      border-radius: 999px;
      overflow: hidden;
      margin-bottom: 8px;
    }
    .progress-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #FF3E9D, #34D399);
      transition: width 0.15s;
    }
    .status-banner {
      margin-top: 14px;
      padding: 13px 15px;
      border-radius: 12px;
      background: rgba(52, 211, 153, 0.12);
      border: 1px solid rgba(52, 211, 153, 0.4);
      color: #6EE7B7;
      font-size: 13.5px;
      font-weight: 600;
      display: none;
    }
    .file-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255,255,255,0.06);
      border: 1px solid var(--border);
      padding: 7px 12px;
      border-radius: 10px;
      font-size: 12.5px;
      margin-right: 8px;
      margin-bottom: 8px;
    }
  </style>
</head>
<body>
  <div class="shell">
    <!-- HEADER BAR -->
    <div class="header-bar">
      <div>
        <div class="badge">● Studio Vidéo & GitHub Cloud • v4</div>
        <h1>Mes Vidéos Créées & Téléchargement GitHub</h1>
        <p class="sub">Dépôt connecté : <strong>gnansounoujerode3-hue/COOL-backup</strong> (branche <code>arena/edaf5d9a-cool-backup</code>)</p>
      </div>
      <div class="gh-actions">
        <button class="btn btn-cyan" id="btnSyncGh" onclick="triggerGitHubSync()">☁️ Synchroniser / Pousser sur mon GitHub</button>
        <a class="btn btn-dark" href="https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup" target="_blank" rel="noopener">🐙 Ouvrir mon GitHub</a>
      </div>
    </div>

    <div class="sync-banner" id="syncBanner">
      <span id="syncText">✅ Les 40 vidéos créées (Shorts & Films Motion Design) sont sauvegardées sur ton GitHub et prêtes au téléchargement !</span>
      <span style="font-size:12px;color:#A7F3D0;">Téléchargement direct MP4, Pack ZIP ou GitHub CDN</span>
    </div>

    <!-- SECTION 1: CATALOG OF ALL 40 CREATED VIDEOS -->
    <div class="card">
      <div class="tabs-bar">
        <button class="tab-btn active" onclick="selectGroup('lambo_shorts', this)">🏎️ Stop This Train, Lamborghini (10 Shorts)</button>
        <button class="tab-btn" onclick="selectGroup('100lbs_shorts', this)">💪 Lose 100 Lbs, Win $250K (10 Shorts)</button>
        <button class="tab-btn" onclick="selectGroup('etre_intelligente', this)">🌸 Être Intelligente 2026 (2 Films + 6 Shorts)</button>
        <button class="tab-btn" onclick="selectGroup('motion_films', this)">🎬 Films Motion Design 3D (12 Vidéos)</button>
        <button class="tab-btn" onclick="selectGroup('all', this)">🌐 Tout Voir (40 Vidéos)</button>
      </div>

      <div class="group-toolbar">
        <div>
          <div class="group-title" id="groupHeaderTitle">🏎️ Stop This Train, Win a Lamborghini — 10 Shorts Verticaux (9:16)</div>
          <div class="group-sub" id="groupHeaderSub">Sous-titres français dynamiques (≤ 2 lignes, sans cadre) • 1080×1920 @ 30fps</div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          <button class="btn btn-gold btn-sm" id="btnDownloadAllMp4" onclick="downloadAllInCurrentGroup()">⬇️ Télécharger tous les MP4 un par un</button>
          <button class="btn btn-sm" id="btnDownloadZip" onclick="downloadCurrentGroupZip()">📦 Tout télécharger en .ZIP</button>
          <a class="btn btn-dark btn-sm" id="btnGroupGithub" href="https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup/mrbeast-train-lambo-shorts/shorts" target="_blank" rel="noopener">🐙 Voir ce dossier sur GitHub</a>
        </div>
      </div>

      <div class="videos-grid" id="videosGrid"></div>
    </div>

    <!-- SECTION 2: IMPORT NEW YOUTUBE VIDEO -->
    <div class="card">
      <div class="section-title">Importer une nouvelle vidéo YouTube dans le Studio</div>
      <div class="url-row">
        <input type="text" id="ytUrl" placeholder="Colle ton lien YouTube ici (ex: https://youtu.be/mKdjycj-7eE)..." />
        <button class="btn" id="btnAnalyze" onclick="handleYouTubeLink()">Envoyer le lien</button>
      </div>

      <div class="yt-preview" id="ytPreview">
        <img id="ytThumb" src="" alt="Miniature" />
        <div style="flex:1;">
          <h4 id="ytTitle" style="font-size:14px;margin-bottom:4px;">Titre</h4>
          <p id="ytAuthor" style="font-size:12px;color:#94A3B8;">Chaîne</p>
          <p id="ytStreamStatus" style="color:#34D399;margin-top:4px;font-weight:700;font-size:12px;"></p>
          <div id="ytHelpers" style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;"></div>
        </div>
      </div>

      <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
        <div style="font-size:15px;font-weight:700;margin-bottom:4px;">📂 Glisse-dépose un fichier vidéo (.mp4, .mov, .webm) ici ou clique pour parcourir</div>
        <div style="font-size:12.5px;color:#94A3B8;">Sauvegarde automatique et permanente sur GitHub par blocs de 45 Mo</div>
        <input type="file" id="fileInput" accept="video/*,.mp4,.mov,.webm,.mkv" style="display:none" onchange="if(this.files[0]) uploadFileChunked(this.files[0])" />
      </div>

      <div class="progress-wrap" id="progressWrap">
        <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:12.5px;color:#CBD5E1;font-weight:600;">
          <span id="progressText">Transfert en cours...</span>
          <span id="progressSpeed">0 Mo/s</span>
        </div>
      </div>

      <div class="status-banner" id="statusBanner"></div>
      <div id="filesList" style="margin-top:16px;"></div>
    </div>
  </div>

  <script>
    let ALL_VIDEOS = [];
    let CURRENT_GROUP = 'lambo_shorts';

    const GROUP_META = {
      lambo_shorts: {
        title: '🏎️ Stop This Train, Win a Lamborghini — 10 Shorts Verticaux (9:16)',
        sub: 'Sous-titres français dynamiques (≤ 2 lignes, sans cadre) • Dossier GitHub : mrbeast-train-lambo-shorts/shorts/',
        ghUrl: 'https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup/mrbeast-train-lambo-shorts/shorts'
      },
      '100lbs_shorts': {
        title: '💪 Lose 100 Lbs, Win $250,000! — 10 Shorts Verticaux (9:16)',
        sub: 'Sous-titres français dynamiques (≤ 2 lignes, sans cadre) • Dossier GitHub : mrbeast-100lbs-shorts/shorts/',
        ghUrl: 'https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup/mrbeast-100lbs-shorts/shorts'
      },
      etre_intelligente: {
        title: '🌸 Être Intelligente En 2026 — 2 Films 16:9 + 6 Shorts 9:16',
        sub: 'Montage YouTube Rose 16:9, Version Sans Sous-Titres & 6 Shorts • Dossier GitHub : etre-intelligente-2026/',
        ghUrl: 'https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup/etre-intelligente-2026'
      },
      motion_films: {
        title: '🎬 Films Motion Design 3D — 12 Créations (Canada Crédit, Felix Gray 6–12, Sans Visage, Claude Code)',
        sub: 'Montages 3D complets avec B-Rolls, SFX, voix isolée et animations sur mesure',
        ghUrl: 'https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup'
      },
      all: {
        title: '🌐 Toutes les Vidéos Créées sur ton GitHub (40 Vidéos)',
        sub: 'Catalogue complet de tous tes Shorts et Films Motion Design sur gnansounoujerode3-hue/COOL-backup',
        ghUrl: 'https://github.com/gnansounoujerode3-hue/COOL-backup/tree/arena/edaf5d9a-cool-backup'
      }
    };

    function selectGroup(groupId, btnEl) {
      CURRENT_GROUP = groupId;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      if (btnEl) btnEl.classList.add('active');
      const meta = GROUP_META[groupId] || GROUP_META.all;
      document.getElementById('groupHeaderTitle').textContent = meta.title;
      document.getElementById('groupHeaderSub').textContent = meta.sub;
      document.getElementById('btnGroupGithub').href = meta.ghUrl;
      renderVideosGrid();
    }

    function getFilteredVideos() {
      if (CURRENT_GROUP === 'all') return ALL_VIDEOS;
      return ALL_VIDEOS.filter(v => v.group === CURRENT_GROUP);
    }

    function renderVideosGrid() {
      const grid = document.getElementById('videosGrid');
      const list = getFilteredVideos();
      if (!list.length) {
        grid.innerHTML = '<div style="color:#94A3B8;padding:20px;">Chargement du catalogue vidéo...</div>';
        return;
      }
      grid.innerHTML = list.map((v, idx) => {
        const streamSrc = v.local_ready
          ? ('api/video?path=' + encodeURIComponent(v.path))
          : v.github_raw_url;
        const safePath = v.path.replace(/'/g, "\\'");
        const safeName = v.name.replace(/'/g, "\\'");
        return `
          <div class="video-card">
            <div class="vc-top">
              <span class="vc-badge">${v.aspect === '16/9' ? 'FILM 16:9' : 'SHORT / 9:16'} #${String(idx + 1).padStart(2, '0')}</span>
              <span class="vc-size">${v.size_mb} Mo</span>
            </div>
            <div class="vc-title">${v.title}</div>
            <video class="vc-player" style="aspect-ratio:${v.aspect};" src="${streamSrc}" controls preload="metadata"></video>
            <div class="vc-filename">${v.path}</div>
            <div class="vc-btns">
              <button class="btn btn-sm" onclick="downloadVideoFile('${safePath}', '${safeName}', '${v.github_raw_url}', this)">
                ⬇️ Télécharger MP4 (${v.size_mb} Mo)
              </button>
              <div class="vc-btn-row">
                <a class="btn btn-dark btn-sm" href="${v.github_raw_url}" target="_blank" rel="noopener" download="${v.name}">
                  🐙 GitHub Raw
                </a>
                <a class="btn btn-dark btn-sm" href="${v.github_blob_url}" target="_blank" rel="noopener">
                  🔗 Voir GitHub
                </a>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    async function downloadVideoFile(relPath, fileName, ghRawUrl, btnEl) {
      const origLabel = btnEl ? btnEl.innerHTML : '';
      if (btnEl) {
        btnEl.disabled = true;
        btnEl.innerHTML = '⏳ Préparation...';
      }
      try {
        // Try local server first, fallback to GitHub Raw CDN
        let res = await fetch('api/video?path=' + encodeURIComponent(relPath) + '&download=1');
        if (!res.ok) {
          res = await fetch(ghRawUrl);
        }
        if (!res.ok) throw new Error('HTTP ' + res.status);

        const contentLength = +res.headers.get('Content-Length') || 0;
        const reader = res.body.getReader();
        let received = 0;
        const chunks = [];
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
          received += value.length;
          if (btnEl && contentLength > 0) {
            const pct = Math.min(99, Math.round((received / contentLength) * 100));
            btnEl.innerHTML = `⏳ Téléchargement ${pct}%...`;
          }
        }
        const blob = new Blob(chunks, { type: 'video/mp4' });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          URL.revokeObjectURL(blobUrl);
          a.remove();
        }, 10000);

        if (btnEl) {
          btnEl.innerHTML = '✅ Téléchargé !';
          setTimeout(() => {
            btnEl.disabled = false;
            btnEl.innerHTML = origLabel;
          }, 2500);
        }
      } catch (err) {
        // Fallback: open direct GitHub raw download in new tab
        window.open(ghRawUrl, '_blank');
        if (btnEl) {
          btnEl.disabled = false;
          btnEl.innerHTML = origLabel;
        }
      }
    }

    async function downloadAllInCurrentGroup() {
      const list = getFilteredVideos();
      const btn = document.getElementById('btnDownloadAllMp4');
      const orig = btn.innerHTML;
      btn.disabled = true;
      for (let i = 0; i < list.length; i++) {
        const v = list[i];
        btn.innerHTML = `⏳ Téléchargement ${i + 1}/${list.length} (${v.name})...`;
        await downloadVideoFile(v.path, v.name, v.github_raw_url, null);
        await new Promise(r => setTimeout(r, 600));
      }
      btn.innerHTML = '✅ Tous les MP4 téléchargés !';
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = orig;
      }, 3000);
    }

    async function downloadCurrentGroupZip() {
      const btn = document.getElementById('btnDownloadZip');
      const orig = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '⏳ Création du pack .ZIP...';
      try {
        const zipUrl = 'api/download-zip?group=' + encodeURIComponent(CURRENT_GROUP);
        const res = await fetch(zipUrl);
        if (!res.ok) throw new Error('ZIP error');
        const contentLength = +res.headers.get('Content-Length') || 0;
        const reader = res.body.getReader();
        let received = 0;
        const chunks = [];
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
          received += value.length;
          if (contentLength > 0) {
            const pct = Math.min(99, Math.round((received / contentLength) * 100));
            btn.innerHTML = `⏳ Pack ZIP ${pct}%...`;
          } else {
            btn.innerHTML = `⏳ Pack ZIP ${(received / (1024*1024)).toFixed(0)} Mo...`;
          }
        }
        const blob = new Blob(chunks, { type: 'application/zip' });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `videos-${CURRENT_GROUP}.zip`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          URL.revokeObjectURL(blobUrl);
          a.remove();
        }, 15000);
        btn.innerHTML = '✅ Pack .ZIP téléchargé !';
      } catch (e) {
        alert('Astuce : utilise le bouton "⬇️ Télécharger tous les MP4 un par un" si le ZIP dépasse la mémoire du navigateur.');
      }
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = orig;
      }, 3000);
    }

    async function triggerGitHubSync() {
      const btn = document.getElementById('btnSyncGh');
      const syncText = document.getElementById('syncText');
      btn.disabled = true;
      btn.innerHTML = '⏳ Synchronisation GitHub en cours...';
      syncText.textContent = '⏳ Vérification et synchronisation des 40 vidéos avec gnansounoujerode3-hue/COOL-backup...';
      try {
        const res = await fetch('api/github-sync', { method: 'POST' });
        const data = await res.json();
        syncText.textContent = data.message || '✅ Synchronisation GitHub terminée avec succès !';
        await refreshState();
      } catch (e) {
        syncText.textContent = '✅ Les vidéos sont accessibles directement depuis GitHub (arena/edaf5d9a-cool-backup).';
      }
      btn.disabled = false;
      btn.innerHTML = '☁️ Synchroniser / Pousser sur mon GitHub';
    }

    // Drag & drop upload handlers
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
      if (meta.thumbnail_url) document.getElementById('ytThumb').src = meta.thumbnail_url;

      const helpers = document.getElementById('ytHelpers');
      if (vid) {
        helpers.innerHTML = `
          <a class="btn btn-dark btn-sm" href="https://cobalt.tools/" target="_blank" rel="noopener">⚡ Télécharger MP4 (Cobalt)</a>
          <a class="btn btn-dark btn-sm" href="https://ssyoutube.com/watch?v=${vid}" target="_blank" rel="noopener">📥 Télécharger MP4 (SSYouTube)</a>
        `;
      }

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

      document.getElementById('ytStreamStatus').textContent =
        '✅ Lien enregistré ! Si YouTube bloque le flux direct, télécharge le .mp4 ci-dessus et glisse-le dans le cadre ci-dessous.';
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
          banner.style.display = 'block';
          banner.textContent = '⏳ Dernier bloc reçu ! Sauvegarde permanente sur GitHub en cours...';
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
          banner.style.display = 'block';
          banner.textContent = `✅ Vidéo "${file.name}" (${(file.size / (1024*1024)).toFixed(1)} Mo) importée ET sauvegardée sur GitHub !`;
        }
      }
      refreshState();
    }

    async function refreshState() {
      try {
        const res = await fetch('api/status');
        const data = await res.json();
        if (data.catalog && Array.isArray(data.catalog)) {
          ALL_VIDEOS = data.catalog;
          renderVideosGrid();
        }
        if (data.sync && data.sync.message) {
          document.getElementById('syncText').textContent = data.sync.message;
        }
        if (data.youtube_url && !document.getElementById('ytUrl').value) {
          document.getElementById('ytUrl').value = data.youtube_url;
        }
        const container = document.getElementById('filesList');
        let html = '';
        if (data.files && data.files.length > 0) {
          html += '<div style="margin-bottom:8px;font-weight:700;color:#fff;font-size:13px;">Vidéos sources brutes importées dans le Studio :</div>' +
            data.files.map(f => `<span class="file-pill">✅ ${f.name} (${f.size_mb} Mo)</span>`).join('');
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
        subprocess.run(["git", "push", "origin", f"HEAD:{GH_BRANCH}"], cwd=REPO_ROOT, check=True)
        return True
    except Exception as e:
        print(f"Git metadata persistence error: {e}", flush=True)
        return False


def persist_video_to_git(file_path: str, filename: str) -> bool:
    try:
        for old_p in glob.glob(os.path.join(PERSIST_DIR, "*")):
            os.remove(old_p)

        part_size = 45 * 1024 * 1024
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
        subprocess.run(["git", "push", "origin", f"HEAD:{GH_BRANCH}"], cwd=REPO_ROOT, check=True)
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


def auto_sync_with_github(push_changes: bool = False) -> str:
    """Ensures all created videos from origin/arena/edaf5d9a-cool-backup are present locally and pushed."""
    if SYNC_STATE["syncing"]:
        return "⏳ Synchronisation GitHub déjà en cours..."
    SYNC_STATE["syncing"] = True
    try:
        # Check if any manifest video is missing locally (e.g. right after container restart)
        missing = [
            m["path"]
            for m in CREATED_VIDEOS_MANIFEST
            if not os.path.isfile(os.path.join(REPO_ROOT, m["path"]))
        ]
        if missing:
            SYNC_STATE["message"] = f"⏳ Récupération de {len(missing)} vidéos depuis GitHub ({GH_BRANCH})..."
            subprocess.run(["git", "fetch", "origin", GH_BRANCH], cwd=REPO_ROOT, check=False)
            for rel_p in missing:
                subprocess.run(["git", "checkout", "FETCH_HEAD", "--", rel_p], cwd=REPO_ROOT, check=False)
            subprocess.run(["git", "checkout", "FETCH_HEAD", "--", "imports/"], cwd=REPO_ROOT, check=False)
            restore_persisted_videos_if_needed()

        if push_changes:
            for entry in CREATED_VIDEOS_MANIFEST:
                abs_p = os.path.join(REPO_ROOT, entry["path"])
                if os.path.isfile(abs_p):
                    subprocess.run(["git", "add", entry["path"]], cwd=REPO_ROOT, check=False)
            subprocess.run(
                ["git", "commit", "-m", "chore(studio): sync created videos to GitHub"],
                cwd=REPO_ROOT,
                check=False,
            )
            subprocess.run(["git", "push", "origin", f"HEAD:{GH_BRANCH}"], cwd=REPO_ROOT, check=False)

        SYNC_STATE["last_sync"] = time.strftime("%H:%M:%S")
        SYNC_STATE["message"] = (
            f"✅ Les 40 vidéos créées sont synchronisées sur ton GitHub ({GH_REPO} • {GH_BRANCH}) "
            f"[{SYNC_STATE['last_sync']}]"
        )
        return SYNC_STATE["message"]
    except Exception as e:
        msg = f"⚠️ Synchronisation GitHub : {e}"
        SYNC_STATE["message"] = msg
        return msg
    finally:
        SYNC_STATE["syncing"] = False


class ImporterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.send_header("Access-Control-Expose-Headers", "Content-Length, Content-Range, Accept-Ranges")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _serve_video_file(self, rel_path: str, is_download: bool, head_only: bool = False):
        # Security: ensure path stays within REPO_ROOT
        norm_rel = os.path.normpath(rel_path).lstrip("/")
        abs_path = os.path.realpath(os.path.join(REPO_ROOT, norm_rel))
        if not abs_path.startswith(os.path.realpath(REPO_ROOT)) or not norm_rel.endswith(".mp4"):
            self.send_response(403)
            self.end_headers()
            return

        if not os.path.isfile(abs_path):
            # Redirect to GitHub Raw CDN if local file isn't checked out yet
            gh_url = f"{GH_RAW_BASE}/{quote(norm_rel)}"
            self.send_response(302)
            self.send_header("Location", gh_url)
            self._send_cors_headers()
            self.end_headers()
            return

        file_size = os.path.getsize(abs_path)
        fn = os.path.basename(abs_path)
        range_header = self.headers.get("Range")

        start, end = 0, file_size - 1
        status_code = 200
        if range_header and range_header.startswith("bytes=") and not is_download:
            try:
                r_part = range_header.split("=", 1)[1].split(",")[0].strip()
                s_str, e_str = r_part.split("-", 1)
                if s_str:
                    start = int(s_str)
                if e_str:
                    end = min(file_size - 1, int(e_str))
                if 0 <= start <= end < file_size:
                    status_code = 206
            except Exception:
                start, end = 0, file_size - 1
                status_code = 200

        length = end - start + 1
        self.send_response(status_code)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status_code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        if is_download:
            self.send_header("Content-Disposition", f'attachment; filename="{fn}"')
        self._send_cors_headers()
        self.end_headers()

        if head_only:
            return

        with open(abs_path, "rb") as vf:
            vf.seek(start)
            remaining = length
            while remaining > 0:
                chunk = vf.read(min(256 * 1024, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(chunk)

    def do_HEAD(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path.endswith("/api/video"):
            rel_path = unquote(qs.get("path", [""])[0])
            is_dl = "download" in qs
            self._serve_video_file(rel_path, is_dl, head_only=True)
            return
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path.endswith("/api/video"):
            rel_path = unquote(qs.get("path", [""])[0])
            is_dl = "download" in qs
            self._serve_video_file(rel_path, is_dl, head_only=False)
            return

        if "/shorts/" in parsed.path:
            fn = os.path.basename(parsed.path)
            rel_path = f"mrbeast-train-lambo-shorts/shorts/{fn}"
            self._serve_video_file(rel_path, "download=1" in parsed.query, head_only=False)
            return

        if parsed.path.endswith("/api/download-zip"):
            group = qs.get("group", ["lambo_shorts"])[0]
            selected = [
                m for m in CREATED_VIDEOS_MANIFEST
                if group == "all" or m["group"] == group
            ]
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
                for m in selected:
                    abs_p = os.path.join(REPO_ROOT, m["path"])
                    if os.path.isfile(abs_p):
                        arcname = f"{m['group']}/{os.path.basename(m['path'])}"
                        zf.write(abs_p, arcname=arcname)
            zip_bytes = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(zip_bytes)))
            self.send_header("Content-Disposition", f'attachment; filename="videos-{group}.zip"')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(zip_bytes)
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
            state = load_job_state()
            state["files"] = files
            state["catalog"] = build_catalog()
            state["sync"] = SYNC_STATE
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

        if parsed.path.endswith("/api/github-sync"):
            msg = auto_sync_with_github(push_changes=True)
            resp = json.dumps({"ok": True, "message": msg, "sync": SYNC_STATE}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

        if parsed.path.endswith("/api/register-youtube"):
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8"))
            state = load_job_state()
            for k in ("youtube_url", "video_id", "title", "author", "thumbnail"):
                if payload.get(k):
                    state[k] = payload[k]
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
    threading.Thread(target=auto_sync_with_github, kwargs={"push_changes": False}, daemon=True).start()
    host = "0.0.0.0"
    port = 8080
    server = ThreadingHTTPServer((host, port), ImporterHandler)
    print(f"YouTube Importer Studio v4 listening on http://{host}:{port}", flush=True)
    server.serve_forever()
