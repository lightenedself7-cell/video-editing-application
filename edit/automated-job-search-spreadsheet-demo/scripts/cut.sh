#!/usr/bin/env bash
# Two cuts on the ORIGINAL timeline: the repeated take 384.80-391.70 s and the false start 405.00-406.59 s
# ("that's why the prompt only look" said twice). Builds the edit source (x264 CRF 12) and a time-shifted transcript.
set -euo pipefail
P=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo
SRC=/home/dev/videos/automated-job-search-spreadsheet-demo.mp4
OUT=/home/dev/videos/automated-job-search-spreadsheet-demo-cut.mp4
A1=384.800; B1=391.700; A2=405.000; B2=406.590
ffmpeg -hide_banner -nostdin -loglevel error -y -i "$SRC" -filter_complex "\
[0:v]trim=0:$A1,setpts=PTS-STARTPTS[v0];[0:v]trim=$B1:$A2,setpts=PTS-STARTPTS[v1];[0:v]trim=start=$B2,setpts=PTS-STARTPTS[v2];\
[0:a]atrim=0:$A1,asetpts=PTS-STARTPTS,afade=t=out:st=$(echo "$A1-0.015"|bc):d=0.015[a0];\
[0:a]atrim=$B1:$A2,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.015,afade=t=out:st=$(echo "$A2-$B1-0.015"|bc):d=0.015[a1];\
[0:a]atrim=start=$B2,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.015[a2];\
[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -r 30 -c:a aac -b:a 256k -ar 44100 -movflags +faststart "$OUT"
sha256sum "$OUT" > "$P/reports/source-cut.sha256"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
/home/dev/video-editing-application/.venv/bin/python - "$P" <<'EOF'
import json, sys
p = sys.argv[1]
CUTS = [(384.8, 391.7), (405.0, 406.59)]
src = json.load(open(f"{p}/prepared/transcripts/section-1.json"))
def T(x):
    return round(x - sum(b - a for a, b in CUTS if x >= b - 0.01), 3)
def conv(w):
    s, e = w["start"], w["end"]
    for a, b in CUTS:
        if s >= a - 0.01 and e <= b + 0.01: return None                # fully inside a cut
        if s < b and e > b + 0.01 and s >= a - 0.3: s = b              # straddles the cut end (the 'looks' of take 2)
    w = dict(w); w["start"], w["end"] = T(s), T(e); return w
for k in ("words", "phrases"):
    src[k] = [x for x in (conv(w) for w in src[k]) if x]
src["cut"] = {"removed": CUTS}
json.dump(src, open(f"{p}/prepared/transcripts/section-1-cut.json", "w"), ensure_ascii=False)
print("words", len(src["words"]))
EOF
echo CUT_DONE