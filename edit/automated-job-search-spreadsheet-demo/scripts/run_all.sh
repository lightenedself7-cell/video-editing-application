#!/usr/bin/env bash
set -e
B=/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/scripts
bash $B/render.sh && bash $B/finish.sh
echo ALL_DONE
