#!/usr/bin/env bash
cd /home/dev/video-editing-application
F=edit/automated-job-search-spreadsheet-demo/automated-job-search-spreadsheet-demo-final.mp4
ffmpeg -hide_banner -nostdin -loglevel error -y -ss 402 -t 8 -i $F -vn -ac 1 -ar 16000 /tmp/chk.wav
.venv/bin/python - <<'PY'
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
segs,_=m.transcribe("/tmp/chk.wav",vad_filter=False,language="en",condition_on_previous_text=False)
print(" ".join(s.text for s in segs))
PY
git -c safe.directory='*' add skills/theme-renderer edit/automated-job-search-spreadsheet-demo/scripts edit/automated-job-search-spreadsheet-demo/project.md edit/automated-job-search-spreadsheet-demo/brand edit/automated-job-search-spreadsheet-demo/editorial-directive.json
git -c safe.directory='*' commit -q -m "Spreadsheet demo round 2: double cut, tab marks, sharper screen-share, extra graphics

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" && git log --oneline | head -1