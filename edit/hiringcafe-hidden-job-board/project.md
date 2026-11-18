# hiringcafe-hidden-job-board

## Session 1: 2026-11-14/15

**Strategy:** Locked final cut (664.0 s, 1280x720, 30 fps) styled in clean-creator. The creator APPROVED the
full plan in director-treatment.md (all 35 beats), including real brand logos (LinkedIn, Indeed,
HiringCafe, Claude, Google Sheets) fetched from their own sites, and YouTube-style subscribe, like and
share buttons in theme colours (not YouTube red).

**Done:**
- Source copied to /home/dev/videos/hiringcafe-hidden-job-board.mp4 (sha in reports/source.sha256).
- Audio: scripts/audio.sh -> audio/voice_enhanced.wav (-14.0 LUFS, -1.4 dBTP, LRA 3.2). Final mux uses this.
- Transcript: transcripts/hiringcafe-hidden-job-board.json (word-level), segments.txt.
- Shots: reports/shots.json. Camera 0-88.8, 176.13-204.27, 508.63-515.77, 582.23-664; the rest is screen
  with a baked presenter bubble (bottom-right until ~508, bottom-left 515-582).
- Engine: reuse ../budget-free-website-startup-guide-clean/scripts/gfx.py + compose.py pattern (numpy/PIL
  per-frame, chunked x264 CRF 16, then concat + mux audio).

**Not done yet:** brand/fonts and scripts/gfx.py are NOT copied yet (the copy command failed). Copy them
from ../budget-free-website-startup-guide-clean/ first.

**Gotchas from session 1 (save tokens):**
- From Windows PowerShell, `wsl -- bash -c '...'` breaks on quotes, parentheses and `|` inside the string.
  Write a .sh or .py file and run `wsl -d Ubuntu-24.04 -- bash /path/script.sh`. Simplest of all:
  open the new session directly in WSL (`cd /home/dev/video-editing-application && claude`).
- faster-whisper's PyAV loader crashes here (`metadata_errors` TypeError). transcribe.py already loads
  the WAV with numpy; no need to transcribe again.
- Use the venv python: /home/dev/video-editing-application/.venv/bin/python (cv2, PIL, numpy, librosa).
- The machine has 16 cores and 7 GB RAM in WSL: render about 6-8 chunks in parallel, not more.
- The creator ruled: no previews or low-res copies. Render full quality (CRF 16) directly.
- Deliver the final MP4 to C:\Users\16046\Downloads\ (/mnt/c/Users/16046/Downloads/).

**Next (resume here):** fetch logos -> bubble geometry -> zoom/highlight coordinates from frames ->
scripts/compose.py with all beats -> render chunks in parallel -> mux voice_enhanced.wav -> verify
(frames at every entrance/exit, loudness, decode) -> deliver to Downloads.

## Session 2: 2026-11-15 (progress)

**Done:**
- Copied brand/fonts (Montserrat) and scripts/gfx.py from ../budget-free-website-startup-guide-clean/.
- Logos fetched into brand/ with sources and hashes in brand/SOURCES.json: linkedin_512.png and
  indeed_wordmark_800.png (Wikimedia SVGs, rasterised with cairosvg, which the creator approved installing
  into .venv), hiringcafe.png, claude.png, sheets.png (brand sites), plus small favicon fallbacks.
  The Indeed wordmark is navy: put it on a light rounded tile on the burgundy ground (no recolouring).
- Bubble survey (reports/bubble_raw.json, bubble_layouts.json, scripts/bubble_lib.py, bubble_track.py,
  bubble_layouts.py): 10 stable layouts, but several are ROUNDED SQUARES, not circles (about 158, 170, 217,
  432, 527 s). **Decision: do not track or redraw the bubble.** Keep it baked inside the framed screen
  (scaled with the screen), no extra ring. Use the layouts only to keep chips and zooms clear of it.
  Layouts (cx, cy, r of the fitted circle): 88.8-152 R(1176,616,87); 152-164 L(62,624,106);
  165-176 L(108,640,70); 204-230 R(1190,593,78); 231-273 R(1149,577,78); 274-355 R(1170,576,78);
  356-508 L(104,637,75); 516-538 L(122,630,83); 538-569 L(107,639,72); 570-582 L(93,626,87).
- Letterbox: around 156 s and 520 s the source has black rows 0-19 and 714-719. Crop them when framing.
- The venv python needs `-I` only for untrusted data; project scripts run with .venv/bin/python as usual.

**Next:** build scripts/compose.py (all 35 beats) on gfx.py, with zoom/highlight coordinates read from
frames; render 6-8 chunks in parallel at CRF 16; mux audio/voice_enhanced.wav; verify; deliver to Downloads.

## Session 3 result (2026-11-15)
- Full 664.0 s master rendered (8 chunks, CRF 16), voice_enhanced.wav muxed, verified (19920 frames, no decode errors, -14.0 LUFS, -1.4 dBTP), delivered to Downloads. See render-receipt.json.
- Gotcha: b11 bottom scrim started at y=490 and darkened the chin inside the face core; now h=160 (starts y=560). Keep scrims below y=560 on camera stretches.
- The verify.py protected delta (137) comes from the b13 click cursor in the wide body box, not the face; face core delta is 0.

## Revision 1 (2026-11-15, creator feedback on b17)
- Feedback: the zoom at ~277-284 s cut off "Apply now" / "Save Job", and the tracker zoom path (278-324 s) left out the left pane.
- Fix (compose.py, ZP.path for b17 only): one steady 1.45x crop on the job-panel buttons (centre 900,250), then tracker views that start at the left edge (440,395 @1.3 and 400,430 @1.4) so the left nav, status tabs and first card stay in frame.
- Only chunk c3 re-rendered. v1 kept in backup_v1/. v2 delivered as hiringcafe-hidden-job-board-v2.mp4 in Downloads.
- Lesson: before placing a zoom, look at where the NAMED control sits in the source frame (job-panel buttons are top-right, x~714-1267, y~138). Keep tab strips below the step bar (crop y0 <= ~140).
