# `teal-spotlight` (Teal Spotlight)

- **Aesthetic**: Livelier explainer. Deep teal ground, one warm marigold pop, tilted labels, bold offset shadows. The lively treatment (tilts, hard shadows, marigold pop) belongs to this theme only.
- **Palette**:
  - Ground: `#0A1F24`, fading up to a teal glow `#11505A`; a faint plus-sign grid on title cards.
  - Teal `#14B8A6` (outlines, bands, check marks), mint `#A7F3D0` (secondary text, brand-tile edges), deep teal `#11505A` (tag fills).
  - Pop: marigold `#FFC83D`. Use it for the key word or phrase in a title, marker highlights, lower-third tag edges and the single bright tile. Never more than one pop per frame region.
  - Text: warm white `#F7FAF9`. Shadow `#03100F`, offset about 6-9 px (at 1280 wide), never blurred.
  - Light explainer cards: white, outline `#CFE3E0`, ink `#0F2A30`, grey skeleton bars `#E3ECEB`, a faint mint/sky/lavender wash along the top edge.
- **Type**: Montserrat for body text; a condensed sans (Ubuntu Sans, width 75, weight 800) in capitals for titles and tags.
- **Motion**: short eased entrances (about 10 frames), slight overshoot on tags and the key-phrase block, wipes from the right for full-screen cards, smooth 20-frame zooms for the spotlight. No linear easing.
- **Do not copy** another creator's watermark or branding. Use the user's own optional wordmark.

## Template components (render with `skills/theme-renderer`)

Put these on directive beats (`component` + `props`); do not write graphics code for them. Props are in
`skills/theme-renderer/themes/teal-spotlight/registry.json` and `skills/theme-renderer/SKILL.md`.

| Component | Treatment | Use for |
|---|---|---|
| `section-title` | FULLSCREEN_MOTION | dark title card: condensed title, key phrase on a tilted marigold block, optional brand tiles joined by plus signs |
| `spotlight-box` | FULLSCREEN_MOTION | zoom into the content being spoken about (boxes in source pixels), dim and blur the rest, glowing outline, optional marker on the key line, pans to a second box |
| `lower-third-tag` | OVERLAY_CARD, SELECTIVE_TEXT | slanted tag (LINK DOWN BELOW, CHAT #1); give its layout box room for the tilt (about 90 px tall) |
| `explainer-card` | OVERLAY_CARD | light card beside the presenter, one row per cue, skeleton bars and a connector line |
| `screen-share` | FULLSCREEN_MOTION | the default demo layout: screen in a large rounded window on a dot grid, presenter in a small card at the left edge (rects are crops of the source frame); hide or restore the card with `presenter_visibility` cues |

Not yet components (hand-build with `custom_graphics` and list under "Promote to library"): split-screen with CHAT #1 / CHAT #2 tags, glitch fast-forward transition,
a glowing line sweep pointing at an item, word-by-word highlighted captions.

## Editorial use

- Spotlight when the narration points at one part of a screen. The footage must be a screen recording; do not spotlight a face.
- Use the title card sparingly, at section starts; keep a clean presenter between graphics.
- One tag at a time. Keep tags short and in capitals.
