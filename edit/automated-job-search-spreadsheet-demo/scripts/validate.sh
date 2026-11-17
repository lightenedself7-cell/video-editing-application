#!/usr/bin/env bash
set -euo pipefail
R=/home/dev/video-editing-application
P=$R/edit/automated-job-search-spreadsheet-demo
mkdir -p "$P/brand"
cp -n $R/edit/hiringcafe-hidden-job-board/brand/claude.png $R/edit/hiringcafe-hidden-job-board/brand/hiringcafe.png "$P/brand/"
cd "$R"
.venv/bin/python "$P/scripts/build_directive.py"
.venv/bin/python skills/presenter-long-form-editor/scripts/validate_directive.py "$P/editorial-directive.json"
