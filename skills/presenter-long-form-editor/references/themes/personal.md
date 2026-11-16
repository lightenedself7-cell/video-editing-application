# `personal` (Signature — default for intros)
- **Aesthetic**: Premium editorial, warm paper and cobalt signal.
- **Palette**:
  - Warm paper canvas: `#F5F3EE`
  - Ink (primary typography): `#151922`
  - Muted text: `#737985`
  - Line / structural borders: `#D7D4CC` (soft line: `#E7E4DE`)
  - Accent: Cobalt `#3659E3` (used as a precise signal, not a heavy wash)
  - Card surface: `#FFFFFF` with subtle paper drop shadows (`rgba(21, 25, 34, 0.14)`)
- **Typography**: Avenir Next (fallback: Avenir, Helvetica Neue, sans-serif).
  - 4K canvas (3840w): body/list 90–100px, sub-heads 110–130px, headlines 140–195px.
  - 1080p canvas: body/list 45–50px, sub-heads 55–65px, headlines 70–98px.
- **Ornaments & Structure**:
  - Thin structural connector lines and round nodes.
  - Optional wordmark in the top right (see "Brand signature"): the first word in Cobalt, the rest in Ink.

## Template components (render with `skills/theme-renderer`)

This theme is rendered by ready-made components; put `component` + `props` on directive beats and write no graphics code
for them. Look comes from `skills/theme-renderer/themes/personal/tokens.json`; the shared component pack is `renderer/flat.py`.
Fonts: Montserrat stands in for Avenir Next / Plus Jakarta Sans. Ornament: a thin connector rule with round cobalt nodes across the top. Highlight: cobalt underline bar.

| Component | Treatment | Use for |
|---|---|---|
| `title-scene` | FULLSCREEN_MOTION | full-screen title with the corner ornaments; optional subtitle and key phrase |
| `checklist-scene` | FULLSCREEN_MOTION | numbered list on the canvas, up to 6 white cards, one per cue |
| `card-overlay` | OVERLAY_CARD | white card beside the presenter with bullet rows |
| `keyword-pill` | SELECTIVE_TEXT | one key word on an accent pill beside the presenter |
| `inset-checklist` | PRESENTER_INSET | presenter in a rounded window on the left, numbered cards on the canvas |

Not yet templated (hand-build with `custom_graphics`, list under "Promote to library"): typewriter reveals, node-and-connector diagrams, the optional wordmark.
