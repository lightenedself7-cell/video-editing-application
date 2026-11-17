#!/usr/bin/env bash
set -euo pipefail
S=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/scripts
bash "$S/validate.sh"
bash "$S/render.sh"
cat /home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/render/safe.json
