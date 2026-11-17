#!/usr/bin/env bash
# Two-pass loudness to -14 LUFS / -1.4 dBTP on the master's audio, video stream copied untouched, then deliver.
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
M=$P/automated-job-search-spreadsheet-demo-master.mp4
OUT=$P/automated-job-search-spreadsheet-demo-final.mp4
DL="/mnt/c/Users/16046/Downloads/Automated Job-Search Spreadsheet Demo - Teal Spotlight v2.mp4"
I=-14; TP=-1.4; LRA=7
J=$(ffmpeg -hide_banner -nostdin -i "$M" -vn -af loudnorm=I=$I:TP=$TP:LRA=$LRA:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
AF="loudnorm=I=$I:TP=$TP:LRA=$LRA:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
ffmpeg -hide_banner -nostdin -loglevel error -y -i "$M" -map 0:v -map 0:a -c:v copy -af "$AF" -c:a aac -b:a 256k -ar 44100 -movflags +faststart "$OUT"
echo "--- final loudness"
ffmpeg -hide_banner -nostdin -i "$OUT" -vn -af loudnorm=print_format=json -f null - 2>&1 | grep -E '"input_(i|tp|lra)"'
echo "--- full decode"
ffmpeg -v error -i "$OUT" -f null - && echo "decode OK"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact "$OUT"
cp "$OUT" "$DL"
sha256sum "$OUT" > "$P/reports/final.sha256"
ls -la "$DL"
echo FINISH_DONE
