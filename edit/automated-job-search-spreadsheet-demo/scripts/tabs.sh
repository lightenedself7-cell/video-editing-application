#!/usr/bin/env bash
mkdir -p /tmp/tabs; cd /tmp/tabs; rm -f *.png
SRC=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
i=0
for t in $(seq 312 2 350); do
  ffmpeg -hide_banner -nostdin -loglevel error -y -ss $t -i $SRC -frames:v 1 -vf "crop=520:60:0:660,drawtext=text='$t':fontcolor=yellow:fontsize=22:x=480:y=5" s_$(printf %03d $i).png
  i=$((i+1))
done
ffmpeg -hide_banner -nostdin -loglevel error -y -pattern_type glob -i 's_*.png' -filter_complex "tile=2x20" /home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/verify/tabs_strip.png
cat /tmp/cut.log