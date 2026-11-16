# `navy-amber` (Navy Amber Theme)
- **Aesthetic**: Architectural engineering tech presentation, sophisticated and un-bold.
- **Palette**:
  - Canvas: Pure White `#FFFFFF` with subtle engineering graph grid (`#EEF1F6` 1.5px lines at 48px pitch).
  - Primary Corporate Tone: Royal Navy `#1D2070` (headings, badges, primary icons).
  - Accent: Golden Amber `#FEAF1D` (alternating rows, accents, active tabs).
  - Amber Text: Rich high-contrast `#C87500` (WCAG AA compliant against white).
  - Cards: White `#FFFFFF` with border `#E8EEF5` and soft navy shadow (`rgba(29, 32, 112, 0.06)`).
- **Typography (Un-bold Classy Standard)**:
  - Typeface: Plus Jakarta Sans or Avenir Next.
  - Checklist & Item Titles: `fontSize: 48px` (96px in 4K), `fontWeight: 500` (medium weight, un-bold, classy).
  - Headlines: `fontSize: 76px` (152px in 4K), `fontWeight: 600`.
  - Number Badges: `fontSize: 32px`, `fontWeight: 650`.
  - Typewriter reveal: Use steady linear pacing (`1 char / ~1.7 frames`). Avoid cubic ease-out truncation which stalls on the final character. Text lands squarely on the final character without pause.
- **Ornaments & Structure**:
  - Corner Geometric Balls: Enlarged overlapping circles at top-right and bottom-left inside 350×350 containers (Navy circle `r=142`, Amber circle `r=115`) with organic micro-floating drift (`±5px`).
  - Navigation Bar: Top bar with brand chevron identity and section tabs (`Overview`, `Checklist`, `Public Build`) with dynamic amber active underline.
  - Icons: Custom dual-tone vector line-art in Navy and Amber.

## Template components (render with `skills/theme-renderer`)

This theme is rendered by ready-made components; put `component` + `props` on directive beats and write no graphics code
for them. Look comes from `skills/theme-renderer/themes/navy-amber/tokens.json`; the shared component pack is `renderer/flat.py`.
Fonts: Montserrat stands in for Avenir Next / Plus Jakarta Sans. Ornament: overlapping navy and amber circles at top-right and bottom-left with a slight drift; a faint graph grid. Highlight: amber underline bar.

| Component | Treatment | Use for |
|---|---|---|
| `title-scene` | FULLSCREEN_MOTION | full-screen title with the corner ornaments; optional subtitle and key phrase |
| `checklist-scene` | FULLSCREEN_MOTION | numbered list on the canvas, up to 6 white cards, one per cue |
| `card-overlay` | OVERLAY_CARD | white card beside the presenter with bullet rows |
| `keyword-pill` | SELECTIVE_TEXT | one key word on an accent pill beside the presenter |
| `inset-checklist` | PRESENTER_INSET | presenter in a rounded window on the left, numbered cards on the canvas |

Not yet templated (hand-build with `custom_graphics`, list under "Promote to library"): the top navigation bar with section tabs, dual-tone line icons, typewriter reveals.
