#!/usr/bin/env bash
# Mirror of app/src/server/prepare.ts: copy source, hash, loudness, local word-level transcript.
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
SRC="/mnt/c/Users/16046/Downloads/Automated Job-Search Spreadsheet Demo.mp4"
DST=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
PY=/home/dev/video-editing-application/.venv/bin/python
mkdir -p /home/dev/videos "$P/prepared/transcripts" "$P/reports"
[ -f "$DST" ] || cp "$SRC" "$DST"
sha256sum "$DST" > "$P/reports/source.sha256"
ffmpeg -hide_banner -nostdin -i "$DST" -vn -af loudnorm=print_format=json -f null - 2> "$P/reports/loudness-source.txt" || true
tail -n 14 "$P/reports/loudness-source.txt"
"$PY" "$P/scripts/whisper.py" "$DST" "$P/prepared/transcripts/section-1.json"
echo PREP_DONE
