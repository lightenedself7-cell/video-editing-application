#!/usr/bin/env bash
# Survey frames: one every 15 s tiled into a contact sheet (labelled), plus full-size stills for layout measuring.
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
SRC=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
mkdir -p "$P/verify/survey"
ffmpeg -hide_banner -nostdin -loglevel error -y -i "$SRC" \
  -vf "fps=1/15,scale=426:240,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=5x7" \
  -frames:v 1 "$P/verify/survey/contact.png"
for t in 5 60 120 200 300 400; do
  ffmpeg -hide_banner -nostdin -loglevel error -y -ss $t -i "$SRC" -frames:v 1 "$P/verify/survey/f$t.png"
done
echo SURVEY_DONE
