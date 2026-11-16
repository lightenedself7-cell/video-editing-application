# `lime-tech` (Hybrid Tech Theme)
- **Aesthetic**: High-contrast modern tech aesthetic with continuous kinetic motion.
- **Palette**:
  - Canvas: Light grey `#F5F5F5` (or `#EEEEEE`)
  - Accent & Badges: Neon Lime `#E8FF72`
  - Contrast & Details: Solid Black `#000000`
  - Cards: Crisp White `#FFFFFF` or translucent frosted white `#FFFFFFD0`
- **Typography**: Avenir Next / geometric sans.
  - Un-bold, clean executive weight (`fontWeight: 500` for titles, `fontWeight: 600` for headlines).
  - High-contrast black text (`#000000`) over lime pills and white cards.
- **Corner Ornaments (Continuous Motion)**:
  - Continuously rotating 8-spoke black flower wheels at canvas corners:
    - Top-left: `cx=38, cy=70`, rotating counter-clockwise (`-frame * 0.42` deg).
    - Bottom-right: `cx=2010, cy=1094`, rotating clockwise (`+frame * 0.38` deg).
    - Wheel geometry: center circle `r=46`, 8 spokes with length 320px, stroke width 58px.

## Template components (render with `skills/theme-renderer`)

This theme is rendered by ready-made components; put `component` + `props` on directive beats and write no graphics code
for them. Look comes from `skills/theme-renderer/themes/lime-tech/tokens.json`; the shared component pack is `renderer/flat.py`.
Fonts: Montserrat stands in for Avenir Next / Plus Jakarta Sans. Ornament: the two continuously rotating 8-spoke black wheels in opposite corners. Highlight: neon-lime pill.

| Component | Treatment | Use for |
|---|---|---|
| `title-scene` | FULLSCREEN_MOTION | full-screen title with the corner ornaments; optional subtitle and key phrase |
| `checklist-scene` | FULLSCREEN_MOTION | numbered list on the canvas, up to 6 white cards, one per cue |
| `card-overlay` | OVERLAY_CARD | white card beside the presenter with bullet rows |
| `keyword-pill` | SELECTIVE_TEXT | one key word on an accent pill beside the presenter |
| `inset-checklist` | PRESENTER_INSET | presenter in a rounded window on the left, numbered cards on the canvas |

Not yet templated (hand-build with `custom_graphics`, list under "Promote to library"): frosted translucent cards, icon tiles, typewriter reveals.
