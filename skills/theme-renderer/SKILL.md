---
name: theme-renderer
description: Render an approved editorial-directive.json with a theme's ready-made components, with no per-video graphics code. Use after the directive is validated, for themes that have a registry (currently clean-creator and teal-spotlight).
---

# Theme renderer

The agent writes the plan; this renders it. Each theme is a template: tokens (colours, fonts, motion timing),
a `registry.json` listing its components and their props, and a `components.py` that draws them.

## Using it

1. Pick components from `themes/<theme>/registry.json` and write them into the directive. A beat names a
   `component` and its `props`:
   ```json
   {"id": "b02", "treatment": "OVERLAY_CARD", "start": 7.4, "end": 23.6, "layout": {"x": 976, "y": 330, "width": 280, "height": 20},
    "component": "glass-card",
    "props": {"rows": [{"text": "Instant on **mobile**", "cue": 7.72}, {"text": "**$0** hosting", "cue": 12.22}]}}
   ```
   `cue` is the source time in seconds when that item appears (on its spoken word). `**bold**` marks the one
   emphasised word per line. Beats with no `component` stay clean presenter.
2. Validate: `.venv/bin/python skills/presenter-long-form-editor/scripts/validate_directive.py <directive>`.
   It rejects unknown components, wrong treatments, unknown or missing props, and cues outside their beat.
3. Render: `.venv/bin/python skills/theme-renderer/render_directive.py <project-dir>` (parallel chunks, audio copied
   from the source, progress lines appended to `ui-progress.jsonl`, safety numbers in `render/safe.json`).
   Check single frames first with `--png <frame> ...` (written to `<project-dir>/render/frames/`).
   Per the creator's ruling, do not make low-resolution previews; the render is full quality.

Agent rule: for a theme with a registry, write components, not graphics code. If a beat has no matching component,
mark it `custom_graphics` (see the long-form skill's "One-off graphics") and hand-build only that beat.

## Clean Creator components (registry v1)

| Component | Treatment | Use for |
|---|---|---|
| `glass-card` | OVERLAY_CARD | up to 5 keyword rows beside the presenter, optional logo header |
| `kinetic-keyword` | SELECTIVE_TEXT | one key word with a small lead-in line |
| `question-beat` | SELECTIVE_TEXT | darkened footage and one caption line with a bold keyword |
| `side-column-list` | PRESENTER_INSET | presenter in a left column, title and check-mark rows |
| `recap-window` | PRESENTER_INSET | presenter window, caption, and check-mark recap cards |

Not yet components (still hand-built per video): screen-share framing with the presenter bubble, punch-ins,
full-screen roadmap and phone panels, chips over screens, compare cards. Add them to the registry as they recur.

## Teal Spotlight components (registry v1)

| Component | Treatment | Use for |
|---|---|---|
| `section-title` | FULLSCREEN_MOTION | dark title card, key phrase on a tilted marigold block, optional brand tiles |
| `spotlight-box` | FULLSCREEN_MOTION | zoom to a box (source pixels), dim and blur the rest, optional marker, up to 3 boxes (pans) |
| `lower-third-tag` | OVERLAY_CARD, SELECTIVE_TEXT | slanted tilted tag with bold shadow; layout box about 90 px tall |
| `explainer-card` | OVERLAY_CARD | light card with cue-timed rows and skeleton bars |

Not yet components: screen-share framing with the presenter card, split-screen labels, glitch transition, glow sweep, word captions.
Titles use a second, condensed font face: tokens `fonts.display` / `display_width`, drawn with `face="display"`.

## Adding a component or a theme

- A component is: an entry in `registry.json` (treatments, `needs`, `props` schema, `touches_presenter`) and a function
  of the same name in `components.py` with the signature `fn(ctx, beat, props, t, out, S)`. A test fails if the two disagree.
- Sizes are written for 1280x720 and multiplied by `kit.u` (width / 1280). Layout comes from the beat (`layout`,
  `presenter_layout`), never from constants tied to one video.
- A new theme is a folder `themes/<id>/` with `tokens.json`, `registry.json`, `components.py` and its `fonts/`.
- Tests: `.venv/bin/python -m unittest discover -s skills/theme-renderer/tests -v` (about 30 s).

## Limits (step 1)

- Delivery size must equal source size.
- A card's soft glow may reach a few pixel levels into the protected region; `render/safe.json` reports the maximum.
