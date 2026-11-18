#!/bin/bash
# Renders the full edit in K parallel chunks (CRF 16), then waits. Re-run with CHUNKS="2 5" to redo only some chunks.
D=/home/dev/video-editing-application/edit/hiringcafe-hidden-job-board
PY=/home/dev/video-editing-application/.venv/bin/python
N=19920; K=8; STEP=$(( (N + K - 1) / K ))
cd $D; mkdir -p render/chunks
CHUNKS=${CHUNKS:-$(seq 0 $((K-1)))}
pids=()
for i in $CHUNKS; do
  a=$((i*STEP)); b=$(( (i+1)*STEP )); [ $b -gt $N ] && b=$N
  $PY scripts/compose.py $a $b render/chunks/c$i.mp4 > render/chunks/c$i.log 2>&1 &
  pids+=($!)
done
fail=0; for p in "${pids[@]}"; do wait $p || fail=1; done
echo "ALL DONE fail=$fail"
