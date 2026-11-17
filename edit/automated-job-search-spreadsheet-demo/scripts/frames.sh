#!/usr/bin/env bash
# Usage: frames.sh t1 t2 ... -> verify/survey/full_<t>.png at source size with a 100 px grid for measuring
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
SRC=${SRC:-/home/dev/videos/automated-job-search-spreadsheet-demo.mp4}
for t in "$@"; do
  ffmpeg -hide_banner -nostdin -loglevel error -y -ss "$t" -i "$SRC" -frames:v 1 \
    -vf "drawgrid=w=100:h=100:t=1:c=red@0.35,drawtext=text='$t':x=1180:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.7" \
    "$P/verify/survey/full_$t.png"
done
echo FRAMES_DONE
