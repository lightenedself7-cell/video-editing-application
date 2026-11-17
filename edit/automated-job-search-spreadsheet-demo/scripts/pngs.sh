#!/usr/bin/env bash
# Usage: pngs.sh sec1 sec2 ...  (cut-timeline seconds) -> render/frames/*.png via the renderer
set -euo pipefail
R=/home/dev/video-editing-application
P=$R/edit/automated-job-search-spreadsheet-demo
cd "$R"
args=""
for s in "$@"; do args="$args $(python3 -c "print(round($s*30))")"; done
.venv/bin/python skills/theme-renderer/render_directive.py "$P" --png $args
ls "$P/render/frames"
