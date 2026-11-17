#!/usr/bin/env bash
F=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/render/frames
O=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/verify
mk() { out=$1; shift; args=""; n=0; for f in "$@"; do args="$args -i $F/f$f.png"; n=$((n+1)); done
 ffmpeg -hide_banner -nostdin -loglevel error -y $args -filter_complex "$(for i in $(seq 0 $((n-1))); do echo -n "[$i:v]scale=640:360[s$i];"; done)$(for i in $(seq 0 $((n-1))); do echo -n "[s$i]"; done)xstack=inputs=$n:layout=$(for i in $(seq 0 $((n-1))); do echo -n "$(( (i%3)*640 ))_$(( (i/3)*360 ))|"; done | sed 's/|$//')" $O/$out; }
mk r3a.png 00045 01092 01410 03390 05010 06360
mk r3b.png 08490 09465 10995 08130 04500 00045