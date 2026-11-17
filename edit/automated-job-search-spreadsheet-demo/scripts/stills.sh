#!/usr/bin/env bash
# Usage: stills.sh name t1 t2 ...  -> verify/survey/<name>.png (4-wide labelled tile, 480x270 each)
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
SRC=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
name=$1; shift
T=$(mktemp -d)
i=0
for t in "$@"; do
  ffmpeg -hide_banner -nostdin -loglevel error -y -ss "$t" -i "$SRC" -frames:v 1 \
    -vf "scale=480:270,drawtext=text='$t':x=6:y=6:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.7" \
    "$T/$(printf %03d $i).png"
  i=$((i+1))
done
ffmpeg -hide_banner -nostdin -loglevel error -y -pattern_type glob -i "$T/*.png" -vf "tile=4x$(( (i+3)/4 ))" -frames:v 1 "$P/verify/survey/$name.png"
rm -rf "$T"
echo "$P/verify/survey/$name.png"
