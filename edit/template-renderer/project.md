## STATUS (2026-11-16, later): app-runs-renderer DONE (f298cbd); Step 3 done for the flat themes personal, navy-amber, lime-tech (shared renderer/flat.py)
Teal Spotlight now also has screen-share. NOT templated and still hand-built: warm-paper, dark-sketch, blackboard-style, colorful-purple (handwriting fonts, sketch rendering). Fonts for the flat themes are Montserrat stand-ins for Avenir Next / Plus Jakarta Sans: review visuals against a real clip before relying on them.

## STATUS (2026-11-16): Step 2 DONE (5a690b9), Step 4 DONE for v1: Teal Spotlight built and committed locally
Teal Spotlight has 4 components (section-title, spotlight-box, lower-third-tag, explainer-card). Still hand-built: screen-share framing with presenter card, split labels, glitch transition, glow sweep, word captions. Step 3 (port the other themes) and the app running the renderer itself remain.

# Template renderer: the AI writes the plan, code renders it

## STATUS (2026-11-16): Step 1 DONE and committed locally

Built `skills/theme-renderer/` (see its SKILL.md). Differences from the plan below:
- Python (numpy/PIL/ffmpeg), not Remotion. The proven per-video pipeline (`gfx.py`/`compose.py`) was generalized
  instead: the repo has no Remotion project and the old pipeline already produced verified masters.
- Five Clean Creator components: glass-card, kinetic-keyword, question-beat, side-column-list, recap-window.
- Directive schema: beats take `component` + `props`; `validate_directive.py` checks them against the theme registry.
- Proof: frames from the finished budget-free-website project rendered by the new renderer match the old
  compose.py output to within 1/255 (rounding) on 12 frames across all five components; protected-region
  safety number identical (0.3975); 9 automated tests pass (~30 s); 900 frames render in 22.7 s vs 29.9 s old.
- No low-resolution previews anywhere (the creator's ruling, clean-creator-style.md). An earlier suggestion of a
  proxy preview was wrong for this user; do not build one.
Not done yet: Step 2 (teach the agent and the app prompt to choose components and call the renderer), the
remaining Clean Creator patterns (screen share with bubble, punch-ins, roadmap, phone, chips, compare), Step 3
(other themes), Step 4 (Teal Spotlight, see new-theme-notes.md).

---

Fresh-session handoff. Read this file first, then start with Step 1. Written 2026-11-16.

## Goal

Cut tokens and time per video edit, and make results consistent. Today the agent writes
`editorial-directive.json` (good, small) and then hand-writes new Remotion code for every
graphic in every video (slow, expensive, inconsistent). Change it so the agent writes only
the directive, and a pre-built theme library renders it.

## Already done (commit bb53332, local main)

- Per-theme reference files: `skills/presenter-long-form-editor/references/themes/<id>.md`
  (`clean-creator` is `references/clean-creator-style.md`). The agent reads only the chosen one.
- `app/src/server/prepare.ts`: the app measures loudness and transcribes locally (faster-whisper)
  before the agent starts, writing `<project>/prepared/prepared.json`.
- `av` pinned to 16.1.0 in `.venv` (av 19 broke faster-whisper).

## Facts about the current system

- Directive spec: `skills/presenter-long-form-editor/references/editorial-directive.md`.
  Validator: `skills/presenter-long-form-editor/scripts/validate_directive.py`.
- Treatments: `CLEAN_PRESENTER`, `OVERLAY_CARD`, `FULLSCREEN_MOTION`, `PRESENTER_INSET`,
  `SELECTIVE_TEXT`, `TRANSITION`. Beat fields: `layout`, `on_screen_copy`, `reveal_sync`,
  `transition_in/out`, `presenter_layout`, `protected_regions`, optional `delivery`.
- Eight themes: warm-paper (default), personal, lime-tech, navy-amber, dark-sketch,
  blackboard-style, colorful-purple, clean-creator. Specs live in the theme files above.
- Remotion skills are in `skills/remotion-*`. Rendering/verification invariants: `skills/video-use`.
- The job prompt is built in `app/src/server/prompt.ts`; jobs run via `app/src/server/jobs.ts`.
- Working tree files are CRLF while the git index is LF. Stage specific files, normalize with
  `sed -i 's/\r$//'` before `git add`. Never `git add -A`.

## Plan

### Step 1: Pick one theme and prove the loop (do this first, stop and show the user)
Start with `clean-creator` (the user's newest, presenter-first, minimal motion, so the smallest
component set). Deliver:
1. `renderer/` Remotion project (inside the repo, e.g. `skills/theme-renderer/`), one composition
   `FromDirective` that takes `editorial-directive.json` + the source video path as props.
2. Theme module `themes/clean-creator/` exporting tokens (colors, fonts, easing, safe areas) taken
   from `clean-creator-style.md`, plus components for each treatment the theme uses
   (title, side-column slide, check-mark recap card, ringed number list, named-rule highlight,
   UI/URL zoom-in, transitions). Components are driven only by beat fields. No per-video code.
3. Extend the directive schema minimally with a `component` field per beat (for example
   `"component": "side-column-slide"`) plus `props`, and extend `validate_directive.py` to check
   that the component exists in the chosen theme's registry and its props are valid.
4. A CLI: `render_directive.py <project-dir>` (or node script) that validates, renders the alpha
   graphics layer, and composites over the presenter using the existing video-use render helpers.
5. Test on a short real clip (ask the user for one) and compare the result with the current
   hand-built output. Measure wall-clock time and tokens before/after.

### Step 2: Teach the agent to use it
- Update `SKILL.md` and `editorial-directive.md`: "choose components from the theme registry
  (`themes/<id>/registry.json`), do not write Remotion code unless no component fits".
- Add a fallback: if a beat needs something not in the registry, the agent may add a one-off
  component, and flags it so it can be promoted into the theme library afterwards.
- Update `prompt.ts` to point at the registry for the chosen theme, and `app/` phases
  (`graphics`/`composite`) so the app can run the renderer itself without the agent.
- Extend `feedback-log.md` rule: a lesson about visuals changes the component, not just the notes.

### Step 3: Port the other themes, one per sitting
Order by use: warm-paper, dark-sketch, navy-amber, lime-tech, personal, blackboard-style,
colorful-purple. Each theme is a tokens module + components + registry.json. Keep a snapshot test
per theme (render a fixed sample directive, hash a few frames).

### Step 4: The new theme the user is about to send images for
Build it directly as a template theme (tokens + components + registry), not as prose only.
Also add its `themes/<id>.md`, the theme list in `brand-system.md`, `ThemePreview.tsx`,
`app/src/client/data/themes.ts`, `app/src/server/jobs.ts` allow-list, `validate_directive.py`.
(Follow the footprint of commit 1458361.)

## Rules for the next session

- Commit to main locally. No branches. Do not push unless the user asks (public fork,
  `lightenedself7-cell/video-editing-application`).
- Give the user an ETA and token estimate up front; they are on a $20 plan. Prefer finishing
  Step 1 in one session and stopping.
- Voice-dictated messages: expect misheard words.
- Never modify original footage. Output under `edit/<project>/`.
- Use `.venv/bin/python`. Run app checks with `cd app && npx tsc --noEmit && npx vitest run`
  from a login shell (`bash -l`); calling npx through plain `wsl -- bash -c` can pick the Windows npm.

## Definition of done for Step 1

- `render_directive` turns a valid clean-creator directive into a finished graphics layer with no
  agent-written graphics code.
- Validator rejects unknown components and bad props.
- Tests pass, one real clip rendered, before/after time and token numbers reported to the user.
