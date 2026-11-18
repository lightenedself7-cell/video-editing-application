#!/bin/bash
# Contact sheets (1 frame / 8 s) and quiet-stretch noise measurement.
cd /home/dev/video-editing-application/edit/hiringcafe-hidden-job-board
SRC=/home/dev/videos/hiringcafe-hidden-job-board.mp4
mkdir -p verify/survey
# 84 frames -> 3 sheets of 28 (7x4), each tile 320x180 with timestamp
for i in 0 1 2; do
  ss=$((i*224))
  ffmpeg -hide_banner -loglevel error -y -ss $ss -t 224 -i "$SRC" \
    -vf "fps=1/8,scale=320:180,drawtext=text='%{pts\:hms\:$ss}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=7x4" \
    -frames:v 1 verify/survey/sheet_$i.png
done
# silence map at -45 dB for noise floor sampling
ffmpeg -hide_banner -nostats -i "$SRC" -vn -af silencedetect=noise=-45dB:d=0.4 -f null - 2>&1 | grep -E "silence_(start|end)" > reports/silences.txt
wc -l reports/silences.txt
# loudness of a few pause stretches = room noise
python3 - <<'EOF'
import re,subprocess
t=open('reports/silences.txt').read()
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',t)]
en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',t)]
pairs=[(s,e) for s,e in zip(st,en) if e-s>0.6][:6]
for s,e in pairs:
    o=subprocess.run(['ffmpeg','-hide_banner','-nostats','-ss',str(s+0.1),'-t',str(e-s-0.2),'-i','/home/dev/videos/hiringcafe-hidden-job-board.mp4','-vn','-af','astats=metadata=0','-f','null','-'],capture_output=True,text=True).stderr
    rms=re.findall(r'RMS level dB: (-?[\d.inf]+)',o)
    print(f"pause {s:.1f}-{e:.1f}s  RMS {rms[-1] if rms else '?'} dB")
EOF
