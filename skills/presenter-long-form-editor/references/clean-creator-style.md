# Clean Creator style (reference-inspired)

A style guide for presenter-led explainers: crisp, minimal, one idea at a time. It is distilled from the
creator's own reference screenshots and a 46 s reference clip. It describes a look and a rhythm. It does
not copy any third party's graphics, logos, music or wording. Use it when the creator's notes say
"Clean Creator style". Everything not listed here follows the rest of brand-system.md.

## Principles
- The presenter is the show. Graphics support one idea at a time and never compete with the face.
- Minimal motion: no particles, stock footage, shaking, spinning or fake 3D. Elements appear one at a
  time, on the spoken word, then hold long enough to read.
- One accent colour family per section. Dark ground, glowing white type.
- Text is short: a title of 1-3 words, body lines under about 12 words.

## Layouts (map to the directive modes)
1. **Full-frame presenter** (`CLEAN_PRESENTER`): hook, opinion, story, transitions. No overlays except the
   rare stat card below. This is the default and should carry most of the runtime.
2. **Side-column explainer** (`PRESENTER_INSET`, with `presenter_layout` as a full-height column): the
   presenter fills a left column about 30% of the frame width, uncropped from the chest up, crisp, with
   eyes in the upper third. The slide fills the remaining ~70%. Use it whenever the narration walks
   through steps, lists or a screen. Keep the column on the same side for the whole video; do not swap
   sides.
3. **Question beat** (`SELECTIVE_TEXT`): at a question or turn in the argument, darken and blur the
   footage and centre one thin white caption line with a single bold keyword, for example
   "how do you actually write a **banger hook** that crushes every single time?".
4. **Full-screen title or diagram** (`FULLSCREEN_MOTION`): short, for a big idea or comparison. Huge
   uppercase heavy title with a soft glow, rounded outlined label chips with a light description under
   each, and a slow horizontal pan from item to item. Cards that hold a clip get a glowing outline.
5. **Recap** (`PRESENTER_INSET`, window variant): the presenter in a rounded-corner window with a thin
   glowing border, about 60% of the frame, on the left. A caption line in italics under the window names
   the video. On the right, a stack of 3-5 cards, one per covered topic, each getting a large check mark
   as the narration reaches it. Use it at the end of a section and at the end of the video.
6. **Portrait window** (`PRESENTER_INSET`, window variant): the presenter in a tall rounded rectangle
   (about 9:16, roughly 360x560 on a 1280x720 canvas, cropped from the chest up so the face stays large
   and centred), with a thin glowing raspberry outline. A short label chip sits above the window and a
   one-line light description under or beside it. Use it where the motion graphic is a framed example,
   a quote, or one of several comparisons: put one window per item and pan slowly between them, with
   the next item entering from the side. The window may hold the presenter live or a clip of them. Keep
   the face inside the window, never cropped at the forehead or chin.
7. **Stat card** (`OVERLAY_CARD`, rare): a small translucent glass card, with a rounded outline and a
   soft glow, for one fact. Never more than one on screen. Official logos are fetched, never drawn.

## Screen shares (observed in the reference)
- The screen sits in a floating window with rounded corners, a thin outline and a soft glow, with
  generous margins, over the dark gradient ground. Never edge to edge.
- The presenter is either absent (the screen fills the stage), or in a small portrait rounded bubble in
  a bottom corner with a matching glowing outline, about 13% of the frame width. Pick one corner and
  keep it for the section.
- Do not show the whole window for long. Digitally zoom into the part being discussed, then scroll or
  pan smoothly to the next part.
- To point at a line, dim the rest of the screen and light that one row in bright white, or use a small
  glowing pill. Do not draw arrows or add shapes.
- A screen share usually runs 8-30 s. Cut back to the presenter between shares.

## Look
- **Palette (matched to the creator's own footage, sampled from the video):**
  - ground: deep burgundy-black `#210A12`, with one soft gradient orb in a corner fading from raspberry
    `#92205A` to dusty rose `#8C3D5D`;
  - accent: raspberry `#92205A` for chips, badges, outlines and the glow, lighter rose `#E25C8E` for
    check marks and highlights;
  - text: warm white `#FAF9F8`. Never pure black or pure white on screen except the screen recordings
    themselves.
  These come from the pink wall and red sweater in the footage, so graphics and room agree. Do not use
  blue or purple unless the creator asks. Light grid lines are allowed at very low contrast.
- **Screen recordings** (white website UI): show them inside a rounded frame with a thin raspberry glow
  border, never edge to edge, so a bright white screen does not dominate a dark layout.
- **Type:** a geometric sans (Montserrat or similar). Titles are heavy and uppercase with a soft warm-white
  glow. Body is light weight, sentence case. Only one word per line may be bold for emphasis.
- **Cleanliness:** when in doubt, show less. Prefer the presenter alone over a decorative graphic. At
  most one graphic idea on screen, and no more than about a third of the runtime covered by graphics.
- **Badges:** numbered circles with an outlined glow, then a light-weight label.
- **Corners:** large radius on cards and the presenter window. Thin glowing 1-2 px borders.
- **Depth:** in the opening shot a big title may sit behind the presenter's head. Only when the
  footage can be cleanly masked.

## Motion
- Entrances: fade and a short slide (about 12 frames) from the side the next item sits on. Check marks
  pop in with a small scale. Pans between items are slow and eased. No bounce, no spin.
- Reveal list items one at a time on their spoken word; do not show the whole list first.
- Hold every resolved state for at least as long as it takes to read it twice.
- Never move more than one primary element at once.

## Pace and rhythm
- Cut dead air: pauses over about 0.5 s are shortened to about 0.3-0.4 s. A tight, confident delivery.
- Hooks and intros are the fastest part (the reference's opening runs near 240 words per minute). Do
  not retime the creator's speech; only trim the pauses. Match the energy by cutting, not by speeding
  the audio.
- Vary the treatment every 20-45 s at natural breaks: full-frame, then side-column, then full-screen,
  never the same treatment twice in a row for long. Do not add a graphic only to fill time.

## Rhythm budget (long-form must not feel like a static talking head, or a busy one)
- Measured on one reference video (24 min, screen-share heavy): presenter full-frame about 42%, framed
  screen shares and full-screen graphics about 54%, presenter bubble over a screen about 4%. Layouts
  lasted 11.5 s on average, from 1 s to 44 s; full-frame stretches were mostly 2-18 s. One video only,
  so treat these as a starting point.
- Graphics and screens cover about 35-45% of a talk-led video, up to about 55% when the narration walks
  through screens or tools. Report the actual share per treatment in director-treatment.md.
- Second reference, a 61-minute talk-led video, first 6 minutes measured: presenter full-frame about
  35%, presenter in a floating window or split about 25%, presenter small over graphics about 10%,
  graphics only about 30%. So the presenter is on screen about 70% of the time, but rarely as a plain
  full-frame shot for long. Layouts changed every 10.5 s on average (range 3-29 s).
- Keep plain full-frame presenter stretches to about 15 s, 20 s at most. Between graphics, keep the
  presenter alive with small changes from the attention toolkit below. Quiet changes do not count
  towards the graphics share.
- Clean does not mean static: the reference changes something small every few seconds. The restraint is
  in how big and how decorative each change is, not in how often something changes.
- Spend graphics where they teach: steps, lists, comparisons, numbers, screens and recaps. Leave
  stories, opinions and the hook as clean presenter.
- One primary treatment at a time, held 8-25 s. Short beats only for a single keyword or a check mark.
- Every graphic must pass this test: if it were removed, would the viewer lose something? If not, cut it.
- Open and close strong: the first 15 s and the final recap may use the richest treatment. The middle
  stays restrained.

## Attention toolkit (from the second reference; the answer to "face-only is boring")
Use these on presenter stretches and as the content of graphic beats. Each is small. Never combine more
than two at once.
- **Punch-in:** alternate the normal framing with a tighter digital zoom of about 110-115% every 4-8 s
  on a jump cut at a natural break. Never zoom during a word; never crop the forehead or chin.
- **Kinetic keyword:** one key word or short phrase appears next to the presenter's gesture or head,
  scaling from 90% to 100% with a springy ease, held 2-4 s, then a clean fade. Bold white, one accent
  word at most. Text may sit behind the head, see below.
- **Micro-overlay:** a small floating badge, icon or one-line lower-third bullet, 2-5 s.
- **Glass card:** a frosted translucent panel slides in from the side with a spring ease, holds for the
  length of the spoken point (4-8 s), then leaves the way it came. Raspberry outline, blurred dark fill.
- **Roadmap marker:** a recurring diagram of the video's steps as numbered nodes joined by a glowing
  path. At the start of each step the matching node lights up (2-5 s, full screen or inset), so the
  viewer always knows where they are. Build it from the video's actual chapters or steps. At most 5-6
  nodes. It returns before each step, and a final time at the recap.
- **Phone mockup:** a vertical 9:16 phone frame with rounded edges and a thin glow, showing a mobile
  view or a short example, with the presenter in a small portrait bubble in the bottom corner. Use it
  whenever the narration talks about phones, mobile visitors or short clips.
- **Neon pointers:** a small glowing arrow, circle or box on a screen or example, only where the
  narration points at that exact thing.
- **Window layouts:** a large rounded presenter window with 1-2 px glowing outline and about 24 px
  radius on the left, with stacked content cards on the right. Or the reverse, with the cards swapping
  as each point is made.
- Frequency guide for a presenter stretch of 60 s: 1 layout change, 2-3 punch-ins, 1-2 kinetic
  keywords, at most one micro-overlay. It must still read as calm.

## Text behind the presenter (use sparingly)
- A big title sits behind the presenter's head and shoulders, with the presenter cut out in front, so
  the head overlaps the letters, as in an opening hook shot.
- Default for talking-only stretches (user ruling 2026-11-07, shown with a reference frame: huge glowing
  warm-white "HOOKS" behind the head, small lead-in line above it, small caption below right, a 3D
  object such as a hook beside it). On any presenter-only stretch longer than about 12 s, make the key
  idea of that stretch a behind-the-head title: 1-2 words very large (about 40% of frame height), a soft
  white glow, a small lead-in line above and a small qualifier line below, optionally one small
  object or icon on the free side. Springs in on the key word, holds 3-5 s, leaves. About one per
  talking stretch, not one per sentence. Keep the old limit (opening plus once or twice) only for beats
  where the matte fails the checks below.
- Original rule, still true for the opening title. Short, 1-3 words, heavy uppercase,
  warm white, no glow stronger than the other titles.
- Needs a clean per-frame cut-out of the presenter (a person matte, rendered as an alpha layer).
  Inspect the edges on the actual footage: hair, hands and moving gestures. If the matte flickers or
  eats into hair or hands, do not use this treatment for that beat; use a normal title instead.
- Keep the face and eyes clear of the letters: the text may touch the head's outline but never sit
  over the face.
- The word must stay readable: the head and hair may cover at most one letter, or the title is moved
  or shortened. Check the first and last frame of the beat, not only the middle.
- Order inside a section: statement in full frame, then the side-column or full-screen explainer, then
  a one-line recap card when the section ends.

## Presenter-over-text treatments (user rulings 2026-11-07, from reference frames)
Talking stretches must never be static, and the presenter's face and room stay visible in all of these.
- **Split-word title:** one phrase behind the head, with a small lead-in line above it (for example
  "I'm going to" over "BREAK | DOWN"). The head sits in the gap between two words, or covers at most one
  letter. Heavy uppercase, warm white, soft white glow. Presenter cut-out in front.
- **Ringed number list over the presenter:** up to 3 items stacked in one side column (left by default),
  each a raspberry ring with a number, a short line (2-4 words) and an optional small italic sub-line.
  The presenter is framed slightly tighter and offset to the other side so the face is clear of the text.
  Items appear on the spoken words, hold, then leave together. Use for steps, rules and "what you will get".
- **Glow-focus roadmap (full screen):** blurred ground, a vertical glowing rail with numbered nodes, the
  active node larger and brighter with a rounded icon tile, a bold uppercase title and one line of
  description; other nodes dimmed and blurred. Raspberry and rose instead of the reference's purple.
  This is the look of the roadmap marker beat.
- **Named-rule highlight:** when the presenter says a named rule or principle ("the golden rule of
  building with AI Studio"), show that phrase on screen as a title line while it is spoken: warm white,
  the key words in rose, glow, held until the sentence ends (about 3-5 s). Applies to any "golden rule",
  "the one thing", "the rule" style phrase.
- **Two-sided compare over the presenter (for "A vs B"):** keep the presenter full-frame and centred.
  A glass heading and 2-3 short lines on the left, the same on the right, in the side margins only
  (head and shoulders keep the middle). No dimming or blurring of the presenter. Light one side on its
  closing line.
- **Simplify copy:** on-screen text is keywords. 1-4 words per line, at most 3 lines per card, no
  sentences. Turn a spoken list into its nouns (for example "Your facts", "Real photos", "Maps link",
  "WhatsApp and phone", "2 hours and domain price").

## UI click targets (user ruling 2026-11-07)
- When the narration or cursor points at a small control in a screen recording, zoom into it: digital
  zoom 160-220% centred on the control, 0.4 s ease in, hold while it is explained, 0.4 s ease out.
  Examples in this project: the angle bracket next to Preview, Export, Download as zip, the + in
  Upload, Restore version, the version control, Claim, Cloudflare Drop target, Settings.
- Zoom lands on the word ("click this", "angle bracket"), before the click, and stays until the result
  appears. Keep the cursor in frame. Use the same rounded framed window, only the content moves.
- Angle bracket, Export and Download as zip are one connected zoom that pans between the controls.
- **Website addresses:** when the presenter says a site (aistudio.google.com, cloudflare, pagespeed.web.dev,
  a domain), zoom to the address bar or page header for 2-3 s at 160-180% (the footage is 720p, so do
  not go further), but only on a frame where the address is visible. If it is too soft, add a crisp
  one-line text pill with the URL. Do not show the user's real domain unless they approve it.
- Optional: a thin rose ring pulses once on the control. No arrows.
- Never zoom while the page is scrolling or loading; wait for the settled frame.
- List each zoom in director-treatment.md with start, end, centre point and zoom level.

## Motion-graphics pattern library (HiringCafe video, 2026-11-15)
Patterns built and approved for the HiringCafe video. Reuse them for other creators: pick the pattern
by what the narration says, not by the topic. All use the theme colours (raspberry accent, cream text,
dark plum ground), never platform red. Keep each one different from the last video's set.

| Spoken cue | Pattern | How it looks |
|---|---|---|
| Reading an article aloud | Article zoom + highlighter | Zoom 1.6-2x into the article; a rose underline sweeps under each fact as it is spoken |
| A website address | Address zoom + URL pill | Zoom about 170% on the address bar, then a crisp one-line pill with the URL |
| The one line to remember | Centred quote card | Footage dims and blurs in place, large centred quote, key words in rose |
| "Like, comment, subscribe" | Subscribe animation | Like, Comment and SUBSCRIBE pill in theme colours; cursor click turns it to Subscribed and rings the bell |
| "Send them this video" | Share animation | Share button with arrow and a cursor click |
| A named product or site | Brand icon chip | The real logo (fetched from the brand's own site, hashes in brand/SOURCES.json) on a glass chip; use a light tile when the logo is dark |
| "X killed Y" | Strike-through logos | Logos land in the side margins, a rose strike line crosses each on the verb |
| Long talking stretch about a process | Presenter-off flow diagram | Presenter hidden; boxes and arrows draw on in order, one highlighted shortcut path |
| Point-by-point passage | Ringed step list / vertical glow rail | Numbered steps appear as each is spoken; a glowing rail connects them |
| A number | Kinetic counter | Counts up to the spoken value, dims when the sentence moves on |
| Two options or two sides | Two-sided compare | Two labelled columns, one item per column per sentence |
| A prompt the creator reads out | Typed prompt card | Glass card that types the spoken words as spoken (show the meaning where the transcript misheard) |
| A time or schedule idea | Timeline | 24 h bar with windows; the relevant window lights up |
| One thing becoming many | Split cards | One card splitting into several |

Rules learned while building it:
- Presenter-off cutaways only on long talking stretches (20 s or more); keep the voice untouched.
- Every claim shown must match what is spoken; show the spoken number if the screen differs.
- Measure the side margins on the footage first and use backing glass where the wall is bright.
- Keep the baked presenter bubble on screen recordings untouched; use its position only to keep chips and zooms clear of it.
- Zoom paths (the pan between held crops): look at where the NAMED control sits in the source frame
  before choosing a centre. Keep the whole control in frame with margin, and keep fixed side panes
  (left nav, tab strip) in frame when the narration walks through them. Keep tab strips below the step bar.
- Use one steady wider crop instead of a tight crop that then needs to move.
- Description and chapters: see youtube-description-template.md.

## Revisions and previews
- A revision names a time range. Re-render only the chunks that overlap it and splice them into the
  existing master. Everything outside the range, and all audio, stays byte for byte.
- Do NOT make previews or low-resolution copies (user ruling 2026-11-07). Render the real
  full-quality (source resolution, CRF 16) output straight away. Check frames yourself while building,
  but deliver only the final file.

## Audio
- Voice first, clean and even. Match tone across takes. Target about -14 LUFS, true peak under -1 dBTP.
- The reference uses a low-volume, steady electronic music bed under the speech and subtle sound
  effects (soft whooshes, UI clicks, pops) on text pop-ins and card moves. Both are optional here: add
  them only if the creator asks. If used, the bed sits at least 20 dB under the voice and the effects
  stay quiet and rare.
- Captions in the reference are animated word-by-word, centred or in the lower third, in clean white
  sans-serif. Burn them in only when the creator asks, last and inside the safe area.

## Limits of this guide
Derived from still frames and 46 s of audio. Sound design and the exact easing curves were not
observable. Ask the creator, or keep them minimal, when unsure.
