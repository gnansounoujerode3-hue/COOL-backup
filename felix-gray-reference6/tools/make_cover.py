#!/usr/bin/env python3
"""Generates the 1080x1920 cover image (cover-9x16.jpg) and synchronized SRT subtitles."""
import os
import subprocess
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import W, H, BLUE_ELECTRIC, BLUE_GLOW, WHITE, load_words
import render_graphics
from composite import GRADE


def fmt_srt_time(seconds):
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(srt_path):
    words = load_words()
    chunks = []
    cur = []
    for w in words:
        if cur:
            gap = w["s"] - cur[-1]["e"]
            prev_txt = cur[-1]["w"].strip()
            if gap > 0.35 or len(cur) >= 6 or prev_txt.endswith((".", "!", "?", ",")):
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)

    lines = []
    for idx, ch in enumerate(chunks, 1):
        t0 = ch[0]["s"]
        t1 = ch[-1]["e"]
        # Join tokens cleanly (merge '.com' onto previous token)
        txt = ""
        for tok in ch:
            part = tok["w"].strip()
            if part.startswith("."):
                txt += part
            else:
                txt = (txt + " " + part).strip()
        lines.append(f"{idx}\n{fmt_srt_time(t0)} --> {fmt_srt_time(t1)}\n{txt}\n")

    os.makedirs(os.path.dirname(srt_path), exist_ok=True)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Generated SRT:", srt_path, f"({len(chunks)} cues)")


def build_cover(cover_path):
    here = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(here)
    repo_root = os.path.dirname(proj_dir)
    raw_video = os.path.join(repo_root, "video brut 5 - Copie.mp4")

    tmp_png = "/home/user/.cache/fg_cover_base.png"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", "1.85", "-i", raw_video,
        "-frames:v", "1", "-vf", GRADE, tmp_png
    ], check=True)

    canvas = Image.open(tmp_png).convert("RGBA")
    canvas.alpha_composite(render_graphics.get_studio_scrim())

    x_left = 145
    s1 = render_graphics.render_text_layer("Teacher appreciation", "m700", 52, WHITE)
    s2 = render_graphics.render_text_layer("FELIX GRAY", "m800", 110, WHITE)
    s3 = render_graphics.render_text_layer("different", "script", 148, BLUE_ELECTRIC, glow_color=BLUE_GLOW, glow_radius=24)

    render_graphics.paste_sprite(canvas, s1, x_left, 1025, "left")
    render_graphics.paste_sprite(canvas, s2, x_left, 1120, "left")
    render_graphics.paste_sprite(canvas, s3, x_left + 75, 1230, "left")
    render_graphics.draw_squircle_or_shatter(canvas, W // 2, 1500, 1.85, mode="intact", pill_text="99+")

    os.makedirs(os.path.dirname(cover_path), exist_ok=True)
    canvas.convert("RGB").save(cover_path, quality=95)
    print("Generated Cover:", cover_path)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj_dir = os.path.dirname(here)
    build_cover(os.path.join(proj_dir, "film", "cover-9x16.jpg"))
    build_srt(os.path.join(proj_dir, "subtitles", "felix-gray-reference6-9x16.srt"))
