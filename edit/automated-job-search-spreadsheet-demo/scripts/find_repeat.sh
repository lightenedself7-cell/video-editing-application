#!/usr/bin/env bash
cd /home/dev/video-editing-application
ffmpeg -hide_banner -nostdin -loglevel error -y -ss 404.5 -t 4.5 -i /home/dev/videos/automated-job-search-spreadsheet-demo.mp4 -vn -ac 1 -ar 16000 /tmp/rep.wav
.venv/bin/python - <<'PY'
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
segs,_=m.transcribe("/tmp/rep.wav",word_timestamps=True,vad_filter=False,language="en",condition_on_previous_text=False)
for s in segs:
    for w in s.words: print(round(w.start+404.5,2),round(w.end+404.5,2),w.word)
PY
ffmpeg -hide_banner -nostdin -loglevel error -i /tmp/rep.wav -af "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=/tmp/rms.txt" -f null -
.venv/bin/python - <<'PY'
import re
t=open("/tmp/rms.txt").read().split("\n")
out=[];ts=None
for l in t:
    if l.startswith("frame"): ts=float(re.search(r"pts_time:([\d.]+)",l).group(1))
    elif "RMS_level" in l:
        v=l.split("=")[1]; out.append((round(ts+404.5,2), v))
print(" ".join(f"{a}:{b[:5]}" for a,b in out))
PY