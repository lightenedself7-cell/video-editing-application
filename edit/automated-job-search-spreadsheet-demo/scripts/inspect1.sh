#!/usr/bin/env bash
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
PY=/home/dev/video-editing-application/.venv/bin/python
SRC=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
IMG=/mnt/c/Users/16046/AppData/Local/Temp/claude/524165d26fe63cca/6d0d4c73-44b7-4f94-a241-7b2d81009e14/images
mkdir -p "$P/brand/user"
for n in 24 25 26 27 28 29; do cp "$IMG/$n.png" "$P/brand/user/img$n.png"; done
"$PY" - <<'EOF'
import json
from PIL import Image
P="/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo"
for n in range(24,30):
    im=Image.open(f"{P}/brand/user/img{n}.png"); print(n, im.size, im.mode)
d=json.load(open(f"{P}/prepared/transcripts/section-1.json"))
print([(w["w"],w["start"]) for w in d["words"] if 398.4<w["start"]<412.5])
EOF
# re-listen to the passage without VAD to see whether a repeat was swallowed
ffmpeg -hide_banner -nostdin -loglevel error -y -ss 396 -t 18 -i "$SRC" -vn -ac 1 -ar 16000 "$P/prepared/seg_396.wav"
"$PY" - <<'EOF'
from faster_whisper import WhisperModel
P="/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo"
m=WhisperModel("small",device="auto",compute_type="auto")
s,_=m.transcribe(f"{P}/prepared/seg_396.wav",word_timestamps=True,vad_filter=False,condition_on_previous_text=False,temperature=0)
for x in s:
    print(round(x.start+396,2),round(x.end+396,2),x.text)
EOF
