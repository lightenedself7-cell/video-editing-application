# automated-job-search-spreadsheet-demo  (HANDOFF, read this first)

Theme teal-spotlight, 1280x720 30 fps. Original: ~/Downloads "Automated Job-Search Spreadsheet Demo.mp4" (454.8 s).
Edit source: /home/dev/videos/automated-job-search-spreadsheet-demo-cut.mp4 (repeat 384.8-391.7 s removed, 447.867 s).

## Status
V1 DELIVERED: ~/Downloads "Automated Job-Search Spreadsheet Demo - Teal Spotlight.mp4" (-14.0 LUFS, checks pass).
User reviewed it and sent round-2 feedback (below). Nothing of round 2 is built yet. User times are FINAL-video times;
final = original - 6.9 s after 384.8 s original. Reuse the pipeline in scripts/ (build_directive.py holds every beat; cues snap
to transcript words; T() shifts times after the cut). Then validate.sh, pngs.sh (single frames), render.sh (about 20-28 min, run in
background), finish.sh (two-pass -14 LUFS, copies to Downloads). Run WSL work via: wsl -d Ubuntu-24.04 -- bash <script.sh>
(write a .sh file; inline quotes break). Local commits only, do not push.

## Round-2 feedback (to do)
1. ~6:35 final (about 402-412 s original): "That's why the prompt only look(s)..." is said TWICE (false start "that's why the prompt only look", then
   "that's why the prompt only looks at the last 24 hours"). Transcript words: That's 405.06, prompt 405.48, only 405.74, looks 406.14, at 406.6,
   the 408.0. No-VAD whisper confirms the repeat. Find the exact cut points on the audio (silence/word edges) and remove the first take.
   build_directive.py needs a SECOND cut (cut.sh builds the cut source from one cut; extend to two cuts, shift every later time by both).
2. Split-screen section (285.3-313.9 s original, screen-share with screen rect x641 y191 w638 h338) looks BLURRY (1.9x upscale of a small panel).
   Fix: in skills/theme-renderer/themes/teal-spotlight/components.py screen_share, use cv2.INTER_LANCZOS4 + mild unsharp mask when upscaling >1.3x
   (also fix the component so all later videos get it). Ask the user whether a higher-resolution original of that screen recording exists.
3. Jobs tab zoom (about 5:17 final, 314-322 s original): highlight the WHOLE row "Customer Success Manager ... Medium" (title column was not visible).
   Use box x0 y240 w1280 h100 (no real zoom) with marker over the full row: row 3 y282 h18 x2 w1195 (Medium, cue about 316.9), row 2 (Technical PM,
   High, y264) at cue about 320.3. Sheet scrolls sideways at about 322.5 s, so end that beat before it.
4. When the sheet switches tabs (Config, Jobs, Rejected, Log) the TAB NAMES at the bottom must be visible and the active tab glowing/highlighted.
   Problem: screen-share crop y20..700 cuts the tab bar off in the 318-377 stretch (tab bar at y about 705 there; at 237 s it is at y 686).
   Use the full 720 height for those screen rects. Find the tab-switch times by grabbing bottom-left strips every 2 s from 312-350 s, then add a short
   spotlight-box on the tab bar (box x0,y690,w420,h30, marker on the active tab) at each switch. Tab positions differ per scene, measure each.
5. 0-20 s has no graphics. Plan: tag "THE BORING PART / not applying" 0.3-2.7; explainer-card 2.8-7.7 rows Filtering (funnel icon), Matching every job to
   your CV, Shortlisting the few worth your time; tag "AUTOMATE IT TODAY" 7.8-10; section-title 10.1-19.2 with tiles Claude (cue 10.24) and a custom
   "hiringcafe.com" tile (HiringCafe logo + the text hiringcafe.com, build it with PIL into brand/hiringcafe_com.png) at cue 12.38 ("Haring Cafe").
6. "Link is up here" (about 20.5 s original): a video cannot hold a clickable link. Use a YouTube CARD (Studio, Editor, Cards, Video) at about 0:21 so it is
   clickable, plus the video link in the description and pinned comment. On screen: tag "LINK UP HERE / tap the card" at the top right (x 960, y 130; the card teaser
   shows at the top right) to point at it. Tell the user this; they do not need to share the link with me.
7. Say "hiringcafe.com" -> show it on screen (see 5; the robots.txt page and other mentions: keep a tag when she says the site name).
8. Show app icons when named: Claude (60.66 and 10.24), HiringCafe (64.18), Google Sheets (68.74; extend the "What you need" title to about 72.3 with a 3rd tile,
   fetch a proper Sheets icon, the existing brand/sheets.png is 16 px), Apify (87.9), ChatGPT (110.84, brand copy in ../hiringcafe-hidden-job-board/brand/chatgpt.png).
9. User images (copied to brand/user/): img24 Claude icon (240x203), img25 pink funnel icon, img26 Apify triangles icon, img27 Apify wordmark (square grey),
   img28 "Job Opportunity" newspaper+magnifier (295x160), img29 "How To Scrape Jobs" robot hand (302x162). Planned use: funnel = "Filtering" row in the hook card;
   Apify wordmark + scrape image + HiringCafe as tiles in a title for the Apify scraper story (86-98.6 s original, 12 s face-only today); Apify icon on the
   "Scrapers can get blocked" row; Job Opportunity image in a "Sound familiar?" card over the face-only stretch 256.5-281.3 s original (rows: 40 minutes later /
   same posting 3 times / months-old postings). Row icon prop: icon = path relative to the project (check how explainer-card draws non-square images).
   Face-only stretches today: 0-19.4 (fixed by 5), 31-55.1, 85.9-98.7 (fixed by 9), 257-281, 415-424 (originals approx).

## Gotchas
- Cards are CENTRED on layout y (4-row card needs y about 320). Layout must not intersect protected region x260-960,y0-600 (card at x976).
- Protected-region check: v1 first failed (16/255) because a card edge sat at x960; keep x 976.
- Component tests: .venv/bin/python -m unittest discover -s skills/theme-renderer/tests -v (30 s) after any components.py change.
- Venv python: /home/dev/video-editing-application/.venv/bin/python. Do not run two ffmpeg-heavy jobs while rendering (file searches time out).
- Deviations kept from v1: split-screen uses screen-share not a card; docs page 130.8-144.8 is a plain window (page scrolls).

## ROUND 2 STATUS (2026-11-17)
All 9 items built in scripts/ (cut.sh = two cuts 384.8-391.7 and 405.0-406.59; build_directive.py has T() for both and every new beat; make_assets.py builds
brand/sheets_icon.png, hiringcafe_com.png, chatgpt.png). Components updated (also for later videos): screen_share Lanczos+unsharp on >1.3x upscale and `tab_marks`;
spotlight_box `keep` + `tab_marks`; section_title tile `scale`; lower_third_tag `size` + `align:right`. registry.json updated. Extra graphics added beyond the
list because the user said there was less motion graphics: hands-off card 31, no-bored tag, "Not just Claude" card, "Built for this" tag, Sound familiar card +
"That's scrolling" tag, "When your search changes" card. Full render + finish run via scripts/run_all.sh, delivered as "... Teal Spotlight v2.mp4" in Downloads.
Still to tell the user: YouTube card at 0:21 (item 6) and ask for a higher-res split-screen recording (item 2).