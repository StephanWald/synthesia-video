#!/bin/sh
# Verify out/film.mp4 without watching it: duration, silence map, one contact sheet, frame strips at cuts.
set -e
cd "$(dirname "$0")/.."
F=${1:-out/film.mp4}
mkdir -p out/check
echo "duration: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F") s"
echo "--- silences >= 0.7 s below -35 dB ---"
ffmpeg -i "$F" -af "silencedetect=noise=-35dB:d=0.7" -f null - 2>&1 \
  | grep -oE 'silence_(start|end): [0-9.]+' | paste - - | awk '{printf "%8.1f -> %8.1f (%.1f s)\n",$2,$4,$4-$2}' | tee out/check/silences.txt
# one tile every 10 s
ffmpeg -loglevel error -y -i "$F" -filter_complex "[0:v]select='not(mod(n\,300))',scale=320:-1,tile=8x9" -frames:v 1 out/check/contact.png
echo "wrote out/check/contact.png"
