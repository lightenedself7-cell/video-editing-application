#!/bin/bash
D=/home/dev/video-editing-application/edit/budget-free-website-startup-guide-clean
L=$D/reports/transcribe.log; P=$D/ui-progress.jsonl; last=0
while true; do
  t=$(grep -E '^[0-9.]+s$' "$L" | tail -1 | tr -d s); t=${t%.*}; t=${t:-0}
  if [ $((t-last)) -ge 120 ]; then
    pct=$((10+t*85/729))
    echo "{\"t\":\"$(date -u +%FT%TZ)\",\"phase\":\"transcribe\",\"percent\":$pct,\"message\":\"Transcribed ${t}s of 729s\"}" >> "$P"
    echo "progress ${t}s"; last=$t
  fi
  if grep -qE '^done|Traceback|Error|Killed' "$L"; then tail -2 "$L"; exit 0; fi
  if ! pgrep -f transcribe_local.py >/dev/null; then echo "process gone"; tail -3 "$L"; exit 1; fi
  sleep 5
done
