#!/usr/bin/env bash
set -euo pipefail
R=/home/dev/video-editing-application
P=$R/edit/automated-job-search-spreadsheet-demo
cd "$R"
time .venv/bin/python skills/theme-renderer/render_directive.py "$P"
echo RENDER_DONE
ls -la "$P"/*.mp4 "$P/reports/checks.json" 2>/dev/null || true
