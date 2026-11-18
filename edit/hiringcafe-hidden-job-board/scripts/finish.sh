#!/bin/bash
# Concatenate chunks, mux the enhanced voice, and write receipt inputs.
set -e
D=/home/dev/video-editing-application/edit/hiringcafe-hidden-job-board; cd $D
N=19920; K=8
: > render/concat.txt; for i in $(seq 0 $((K-1))); do echo "file 'chunks/c$i.mp4'" >> render/concat.txt; done
ffmpeg -v error -y -f concat -safe 0 -i render/concat.txt -c copy render/video_only.mp4
ffmpeg -v error -y -i render/video_only.mp4 -i audio/voice_enhanced.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart hiringcafe-hidden-job-board-master.mp4
echo "muxed"
