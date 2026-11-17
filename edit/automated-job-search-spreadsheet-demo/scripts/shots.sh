#!/usr/bin/env bash
# Scene cuts (score > 0.25) with timestamps -> reports/scenes.txt
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
SRC=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
ffmpeg -hide_banner -nostdin -i "$SRC" -an -vf "scale=320:-2,select='gt(scene,0.25)',metadata=print:file=$P/reports/scenes_raw.txt" -f null - 2>/dev/null
grep -o 'pts_time:[0-9.]*' "$P/reports/scenes_raw.txt" | cut -d: -f2 > "$P/reports/scenes.txt"
tr '\n' ' ' < "$P/reports/scenes.txt"; echo
