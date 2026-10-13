# Adapter: enhance (optional finishing pass - upscale / face-restore / bg-remove)

## What this tool does

An optional polish pass run late in the `edit` / `compose` stage: upscale a clip or
frame, restore a soft face, or cut a subject off its background. **Local + free first** -
every operation runs on this machine, $0. There is always an FFmpeg baseline so it works
with no extra installs; the higher-quality engines (Real-ESRGAN, GFPGAN, rembg) activate
only when present.

Engine: [`../tools/enhance.py`](../tools/enhance.py).

## When the orchestrator dispatches here

| Op | Trigger |
|---|---|
| upscale | A generated 720p clip needs to fill a 1080p/4K frame; an old/low-res source; a still that will be Ken-Burned |
| face-restore | A compressed or low-res face in archival footage / an old testimonial |
| bg-remove | A portrait still needs to be composited onto a brand background (image only) |

Not for: fixing a fundamentally bad shot (re-shoot / re-generate), or as a default pass
(enhancement is opt-in - most footage does not need it).

## Commands

```bash
# Upscale (FFmpeg lanczos baseline - always works, no deps):
python tools/enhance.py upscale --in clip.mp4 --scale 2 --out clip_2x.mp4

# Upscale with Real-ESRGAN if installed (sharper; auto-falls back to FFmpeg if not on PATH):
python tools/enhance.py upscale --in frame.png --scale 4 --engine realesrgan --out frame_4x.png

# Background removal (still image; needs rembg):
python tools/enhance.py bg-remove --in portrait.png --out cutout.png

# Face restoration (needs GFPGAN):
python tools/enhance.py face-restore --in face.png --out face_restored.png
```

## Engines + graceful degrade

| Op | Best engine | Install | Fallback |
|---|---|---|---|
| upscale | `realesrgan-ncnn-vulkan` on PATH | [Real-ESRGAN releases](https://github.com/xinntao/Real-ESRGAN/releases) | FFmpeg lanczos (built in) |
| bg-remove | `rembg` | `pip install rembg onnxruntime` | none (exits 3 with hint) |
| face-restore | `gfpgan` | `pip install gfpgan basicsr` | none (FFmpeg cannot fake it; exits 3 with hint) |

Exit `3` means "optional engine not installed" - the tool prints the exact install line
and does not crash. The orchestrator should treat 3 as "polish skipped", not a job failure.
For bg-remove/face-restore there is intentionally **no FFmpeg fake**: a lanczos blur is not
a face restoration, and pretending otherwise would be a silent-failure anti-pattern.

## Video vs image

- **upscale** handles both (video keeps its audio via `-c:a copy`).
- **bg-remove** is image-only here. For per-frame video matting use a dedicated tool
  (backgroundremover, RobustVideoMatting) or a chroma key - do not loop rembg over frames
  for a long clip (slow + flickery). Documented, not wired.
- **face-restore** is image-first (GFPGAN). For video, restore sampled keyframes or run
  GFPGAN's video path offline; not in the default pass.

## Where it sits in the pipeline

`assets -> edit -> [enhance] -> compose`. Enhance operates on already-generated/retrieved
assets, before final compose. In the cinematic pipeline it commonly upscales fal-seedance
720p output to the delivery resolution. Always re-check the post-render QA after enhancing
(upscaling changes file size + can shift loudness if re-encoded).

## Anti-patterns

- Running enhance by default. It is opt-in; most footage does not need it and re-encoding
  costs quality.
- Faking face-restore or bg-remove with FFmpeg. If the engine is missing, skip and say so.
- Upscaling 720p to 4K and claiming "4K". It is upscaled 720p - say that.
- bg-removing every frame of a video with rembg. Use a real matting tool for video.
