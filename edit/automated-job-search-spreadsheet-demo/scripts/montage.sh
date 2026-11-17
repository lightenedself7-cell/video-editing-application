#!/usr/bin/env bash
F=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/render/frames
O=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/verify
mk() { out=$1; shift; args=""; n=0; for f in "$@"; do args="$args -i $F/f$f.png"; n=$((n+1)); done
 ffmpeg -hide_banner -nostdin -loglevel error -y $args -filter_complex "$(for i in $(seq 0 $((n-1))); do echo -n "[$i:v]scale=640:360[s$i];"; done)$(for i in $(seq 0 $((n-1))); do echo -n "[s$i]"; done)xstack=inputs=$n:layout=$(for i in $(seq 0 $((n-1))); do echo -n "$(( (i%3)*640 ))_$(( (i/3)*360 ))|"; done | sed 's/|$//')" $O/$out; }
mk m1.png 00045 00150 00420 00630 00990 01350
mk m2.png 01980 02115 02760 03360 03750 08100
mk m3.png 08880 09495 09624 09930 10050 10860