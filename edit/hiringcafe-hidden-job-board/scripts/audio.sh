#!/bin/bash
# Voice enhancement + loudness normalisation (creator approved "enhance audio, even volume", 2026-11-14).
set -e
cd /home/dev/video-editing-application/edit/hiringcafe-hidden-job-board
SRC=/home/dev/videos/hiringcafe-hidden-job-board.mp4
mkdir -p audio
CHAIN="highpass=f=75:poles=2,afftdn=nr=14:nf=-58:tn=1,agate=threshold=0.004:ratio=2:range=0.18:attack=8:release=300:knee=3,deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=-26dB:ratio=2.5:attack=12:release=180:knee=4:makeup=4dB"
# pass 1: measure after the chain
ffmpeg -hide_banner -nostats -i "$SRC" -vn -af "$CHAIN,loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json" -f null - 2> audio/pass1.log
read MI MTP MLRA MTH OFF < <(python3 - <<'EOF'
import json,re
t=open('audio/pass1.log').read(); j=json.loads(t[t.rindex('{'):t.rindex('}')+1])
print(j['input_i'],j['input_tp'],j['input_lra'],j['input_thresh'],j['target_offset'])
EOF
)
# pass 2: linear normalisation with measured values, 48 kHz
ffmpeg -hide_banner -loglevel error -y -i "$SRC" -vn \
  -af "$CHAIN,loudnorm=I=-14:TP=-1.5:LRA=7:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true,aresample=48000" \
  -c:a pcm_s24le audio/voice_enhanced.wav
echo "== before"; ffmpeg -hide_banner -nostats -i "$SRC" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):"
echo "== after";  ffmpeg -hide_banner -nostats -i audio/voice_enhanced.wav -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):"
echo "== pause noise before/after (164.6-165.1 s)"
for f in "$SRC" audio/voice_enhanced.wav; do ffmpeg -hide_banner -nostats -ss 164.6 -t 0.5 -i "$f" -vn -af astats=metadata=0 -f null - 2>&1 | grep "RMS level dB" | tail -1; done
