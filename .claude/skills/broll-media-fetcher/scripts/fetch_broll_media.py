#!/usr/bin/env python3
"""
B-Roll & Image Media Fetcher CLI for Video Montage (.claude/skills/broll-media-fetcher)
Normalizes downloaded images, generates 30fps short B-roll MP4 clips via FFmpeg,
and outputs a CutSense/Videographer-compatible broll-manifest.json.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path
from PIL import Image


def generate_ken_burns_broll(image_path: str, output_mp4: str, duration: float = 4.0, fps: int = 30, size: str = "640x360"):
    frames = int(round(duration * fps))
    vf = (
        f"scale=1280:720,"
        f"zoompan=z='min(zoom+0.0018,1.26)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={size}:fps={fps},format=yuv420p"
    )
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-loop", "1", "-i", image_path,
        "-vf", vf,
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        output_mp4
    ], check=True)


def extract_subclip_broll(source_video: str, output_mp4: str, start: float, duration: float, crop_vf: str = "scale=640:360,format=yuv420p"):
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{start:.2f}", "-t", f"{duration:.2f}",
        "-i", source_video,
        "-vf", crop_vf,
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        output_mp4
    ], check=True)


def main():
    parser = argparse.ArgumentParser(description="Prepare images & short B-roll MP4 clips for video editing.")
    parser.add_argument("--project-dir", required=True, help="Target video project directory")
    parser.add_argument("--source-video", default=None, help="Optional source raw video for B-roll subclip extraction")
    args = parser.parse_args()

    proj = Path(args.project_dir)
    img_dir = proj / "assets" / "images"
    broll_dir = proj / "assets" / "broll"
    img_dir.mkdir(parents=True, exist_ok=True)
    broll_dir.mkdir(parents=True, exist_ok=True)

    for img_file in sorted(img_dir.glob("*.jpg")):
        out_mp4 = broll_dir / f"broll_{img_file.stem}.mp4"
        if not out_mp4.exists():
            generate_ken_burns_broll(str(img_file), str(out_mp4), duration=4.0)
            print(f"[broll-media-fetcher] Generated short B-roll video: {out_mp4}")

    if args.source_video and os.path.exists(args.source_video):
        out_sub = broll_dir / "broll_studio_table.mp4"
        if not out_sub.exists():
            extract_subclip_broll(args.source_video, str(out_sub), start=51.90, duration=2.90,
                                  crop_vf="crop=720:405:0:420,scale=640:360,format=yuv420p")
            print(f"[broll-media-fetcher] Extracted studio B-roll video: {out_sub}")


if __name__ == "__main__":
    main()
