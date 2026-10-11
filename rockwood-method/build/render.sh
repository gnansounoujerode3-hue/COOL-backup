#!/bin/bash
# Rendu complet : nettoyage voix -> musique duckée -> mix -> montage image + sous-titres
set -e
cd /home/user/work
FF=/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
export FONTCONFIG_FILE=/home/user/work/fonts.conf
mkdir -p out

echo "== 1/4 voix : EQ + compression + normalisation -14 LUFS"
$FF -hide_banner -y -i build/voix.wav -af "\
highpass=f=85,\
equalizer=f=250:t=q:w=1.1:g=-2.5,\
equalizer=f=3000:t=q:w=1.2:g=2.5,\
equalizer=f=6500:t=q:w=1.4:g=1.5,\
acompressor=threshold=-20dB:ratio=3:attack=8:release=220:makeup=2,\
loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -ac 2 build/voice_norm.wav 2>&1 | tail -2

echo "== 2/4 musique : ducking sous la voix"
$FF -hide_banner -y -i build/music.wav -i build/voice_norm.wav \
  -filter_complex "[0:a]volume=0.34[m];[m][1:a]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=420[duck]" \
  -map "[duck]" -ar 48000 -ac 2 build/music_duck.wav 2>&1 | tail -1

echo "== 3/4 mix final"
$FF -hide_banner -y -i build/voice_norm.wav -i build/music_duck.wav -i build/sfx.wav \
  -filter_complex "[2:a]volume=0.5[s];[0:a][1:a][s]amix=inputs=3:duration=longest:normalize=0[mx];[mx]alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11[out]" \
  -map "[out]" -ar 48000 -ac 2 -t 29.1 build/mix.wav 2>&1 | tail -1

echo "== 4/4 rendu vidéo 1080x1920 (habillage + sous-titres)"
python3 build/make_filter.py
ARGS=()
while IFS=$'\t' read -r f d z; do
  [ -z "$f" ] && continue
  ARGS+=(-loop 1 -framerate 25 -t "$d" -i "$f")
done < build/inputs.txt
NP=$(grep -c . build/inputs.txt)
AIDX=$((1 + NP))
GRAPH=$(tr '\n' ' ' < build/graph.txt)
$FF -hide_banner -y -i "AIDE-CHATGPT-main/video brut.mp4" "${ARGS[@]}" -i build/mix.wav \
  -filter_complex "$GRAPH" \
  -map "[vout]" -map "${AIDX}:a" -r 25 -t 29.1 \
  -c:v libx264 -preset medium -crf 18 -profile:v high -level 4.0 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  out/rockwood-method-montage-9x16.mp4 2>&1 | tail -3

echo
ls -la out/
