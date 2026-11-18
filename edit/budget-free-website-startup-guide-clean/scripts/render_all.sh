#!/bin/bash
D=/home/dev/video-editing-application/edit/budget-free-website-startup-guide-clean
PY=/home/dev/video-editing-application/.venv/bin/python
N=21881; K=8; STEP=$(( (N + K - 1) / K ))
cd $D
pids=()
for i in $(seq 0 $((K-1))); do
  a=$((i*STEP)); b=$(( (i+1)*STEP )); [ $b -gt $N ] && b=$N
  $PY scripts/compose.py $a $b render/chunks/c$i.mp4 > render/chunks/c$i.log 2>&1 &
  pids+=($!)
done
last=0
while true; do
  alive=0; for p in "${pids[@]}"; do kill -0 $p 2>/dev/null && alive=1; done
  done_fr=0; for i in $(seq 0 $((K-1))); do f=render/chunks/c$i.mp4.progress; [ -f $f ] && done_fr=$((done_fr + $(cat $f))); done
  now=$(date +%s)
  if [ $((now-last)) -ge 90 ]; then
    pct=$((done_fr*100/N)); echo "{\"t\":\"$(date -u +%FT%TZ)\",\"phase\":\"composite\",\"percent\":$pct,\"message\":\"Rendered ~$done_fr of $N frames\"}" >> ui-progress.jsonl; last=$now
  fi
  [ $alive -eq 0 ] && break
  sleep 10
done
fail=0; for p in "${pids[@]}"; do wait $p || fail=1; done
echo "ALL DONE fail=$fail"
