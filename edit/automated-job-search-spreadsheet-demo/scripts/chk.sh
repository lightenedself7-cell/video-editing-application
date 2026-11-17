#!/usr/bin/env bash
cd /home/dev/video-editing-application
F=edit/automated-job-search-spreadsheet-demo/automated-job-search-spreadsheet-demo-final.mp4
ffmpeg -hide_banner -nostdin -loglevel error -y -ss 394 -t 9 -i $F -vn -ac 1 -ar 16000 /tmp/chk.wav
.venv/bin/python - <<'PY'
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
segs,_=m.transcribe("/tmp/chk.wav",vad_filter=False,language="en",condition_on_previous_text=False)
print(" ".join(s.text for s in segs))
PY
