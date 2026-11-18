# auto-cleanup-and-shortform (HANDOFF, read this first)

Goal (user, 2026-11-17): give raw footage + script, get a finished video with no manual cutting: silences, ums/ers, false starts and repeated takes
removed automatically, then the existing motion-graphics pipeline, then output. Both LONG-FORM and SHORT-FORM (vertical Reels) eventually.
Local commits only until the user says push (see memory: career-ops / video-app notes). Run WSL work from PowerShell with script files (the Bash tool is Git Bash).

## Inspiration (read only, do not copy files)
- Nick Saraev's public folder https://drive.google.com/drive/folders/1bOQ0EY2eLk7BNnQ9PAwD-x5C6y7x-Fz- (directives/ jump_cut_vad.md, smart_video_edit.md; execution/*.py).
  Ideas taken: Silero VAD silence cut with min-silence 0.5 s, min-speech 0.25 s, padding 100 ms, merge-gap 0.3 s; "cut cut" restart phrase; audio chain
  (highpass 80, lowpass 12k, EQ -1 dB@200, +2 dB@3k, gentle compression, loudnorm); optional LUT colour grade; hardware encoding (his is Mac, we are WSL: check NVENC).
- Jai Arora Vuyyuru reel (short-form): one-sentence look changes ("moody", "aesthetic"), storyboard BEFORE render, one-sentence revisions.
- We already have: skills/video-use (transcribe, pack_transcripts, render, grade, subtitles), presenter-long-form-editor + theme-renderer (9 themes, storyboard =
  director-treatment.md), presenter-intro-editor, remotion-* skills (captions). Spreadsheet-demo project (edit/automated-job-search-spreadsheet-demo) is the worked example.

USER DECISION (2026-11-17): short-form (step 4) is DEFERRED, not today. Build steps 1-3 and 5 only; revisit short-form when the user asks.

## STATUS (2026-11-17): steps 1, 2, 3, 5 built, local commit only
- Step 1 DONE: skills/presenter-long-form-editor/scripts/auto_clean.py (`analyze` -> cuts.json + cuts.md, `apply --approved [--drop N] [--voice-chain]` -> cleaned mp4, transcript-cut.json, cut-map.json; `make_T` shifts times). Tests: `.venv/bin/python -m unittest discover -s skills/presenter-long-form-editor/tests` (instant).
  Real test on the spreadsheet video (test-run/): found the repeated take (6:19.8-6:26.8, kept the LAST take, flagged for review), encode checked (decode OK, duration exact).
  KNOWN LIMITS: Whisper smooths immediate repeats, so the 405.0 s false start ("that's why the prompt only look" twice) is NOT visible to word-level detection (try `--model medium` or review by ear). This speaker is fluent, so few pauses; threshold 0.5 s, keep 0.3 s, cuts under 0.25 s ignored. Silent screen demos: use `--protect a-b` or the ⚠ flag.
- Step 2 DONE on the agent side: SKILL.md steps 1b/1c. NOT done: app UI (prepare.ts does not run the cleanup or show cuts.md for approval; a cut-approval screen in the app is a separate build).
- Step 3 DONE: scripts/look.py (moody, aesthetic, cinematic, clean, natural -> registry theme + mild grade; `resolve`, `grade`, `list`). Grade is applied to the cleaned source before graphics.
- Step 5 RESULT: GPU encode is NOT possible here (WSL has libd3d12 but no libcuda, so NVENC fails; VAAPI has no display). Use CPU: cleaned intermediate now defaults to `-preset veryfast -crf 12` (447 s video encoded in 3m17 vs roughly double at slow). Render time of the final theme video is unchanged (about 9-10 min).
- Short-form (step 4) still deferred.

## Build order
1. **Cleanup step (long-form first).** New script, e.g. skills/video-use/helpers/auto_clean.py or skills/presenter-long-form-editor/scripts/auto_clean.py:
   - transcribe with faster-whisper, word timestamps, KEEP fillers (initial_prompt with "um, uh, er"), vad_filter on (Silero is built in; venv av pinned 16.1.0, do not upgrade).
   - cut list: pauses over a threshold (default keep 0.3 s), fillers, false starts and repeated takes (compare consecutive phrases, and against the user's script if given),
     optional "cut cut" marker. Find cut points on word edges AND audio dips (lesson: the 405.0-406.59 s cut in the spreadsheet video needed an RMS dip check).
   - WRITE THE CUT LIST FIRST (cuts.json + a readable cuts.md with before/after text) and wait for the user's approval; only then encode.
   - generalise edit/automated-job-search-spreadsheet-demo/scripts/cut.sh (N cuts, 15 ms audio fades, shifted transcript) and build_directive.py T() (shift for every cut).
2. **Hook into the pipeline:** cleaned source -> existing prepare.ts (loudness + whisper) -> director-treatment storyboard -> directive -> validate -> theme-renderer.
3. **Look presets by one sentence:** map "moody / warm / aesthetic" to a theme + a colour-grade preset (grade.py presets or .cube LUT) at render; same beats, different theme.
   Themes share the same components (section-title, spotlight-box, lower-third-tag, explainer-card, screen-share, pipeline, focus-points).
4. **Short-form (later):** 9:16 1080x1920 layout, big word-by-word captions (remotion-captions or our renderer), faster pacing, hook in first 2 s. Decide: new theme-renderer
   frame size vs Remotion. Ask the user for a sample raw reel + script before building.
5. **Speed:** check GPU encode in WSL (ffmpeg -encoders | grep nvenc); current CPU render of 446 s video takes about 9-10 min.

## Rules and lessons from the spreadsheet video (apply every time)
- No low-resolution previews, ever (user ruling). Single-frame stills via pngs.sh are fine.
- Face region protected: graphics must not change pixels inside protected_regions. Current region x300 y0 w660 h440 (face/head only); room 1 (pink wall) graphics go left-centre,
  room 2 and screen stretches right-centre; tags at y466 (above the player bar). Left cards x8 w250 (shadows reach about 40 px).
- Batch all feedback before a render (each round = a full render). Give ETAs and short progress updates (user is on voice dictation, expects misheard words).
- Component tests: .venv/bin/python -m unittest discover -s skills/theme-renderer/tests (about 100 s). Validate: scripts/validate.sh in the project.
- Pipeline of scripts per project: cut.sh, build_directive.py, validate.sh, pngs.sh, render.sh, finish.sh, run_all.sh (render then two-pass -14 LUFS, copies to Downloads).

## Estimates to tell the user up front
Cleanup step build: roughly 150-250k tokens, 1-1.5 h. A normal video after that: roughly 150-300k tokens, 30-60 min incl. one 10 min render. Short-form build: separate, similar size.
Start in a FRESH session from this file.
