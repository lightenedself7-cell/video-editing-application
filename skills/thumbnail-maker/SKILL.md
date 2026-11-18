---
name: thumbnail-maker
description: Make YouTube thumbnails. Option A builds an on-brand thumbnail from a theme plus a photo of the creator (free, local). Option B recreates a competitor's outlier thumbnail with the creator's face via Gemini (needs GEMINI_API_KEY). Use when asked for a thumbnail.
---

# Thumbnail maker

Run from the repo root with `.venv` active. Output is 1280x720.

## Option A - themed thumbnail (default, free)
`python skills/thumbnail-maker/make_thumbnail.py --photo PHOTO --text "WORDS|*HIGHLIGHT* WORD" --theme teal-spotlight --out OUT.png`

- `--text`: 3-4 words. `*word*` uses the theme highlight colour, `|` breaks a line.
- `--theme`: any folder under `skills/theme-renderer/themes/` that has tokens.json (clean-creator, teal-spotlight, ...).
- `--chip "FREE"` adds a small badge. `--variants 3` writes layout variants (person left/right, bigger).
- Photo: a clear head-and-shoulders shot with a strong expression works best. Background removal uses the
  small `u2net_human_seg` model (the rembg default is ~1GB and runs out of memory in WSL).
- Quote text containing `$` in single quotes so the shell keeps it.

## Option B - recreate an outlier thumbnail with your face (needs a key)
`pip install google-genai` once, add `GEMINI_API_KEY=...` to `.env`, then:
`python skills/thumbnail-maker/recreate_thumbnail.py --youtube URL --refs photo1.jpg photo2.jpg -n 3 --out edit/thumbs/idea`
Edit pass: `--edit IMAGE --prompt "Change the text to 'FREE AI SITE'"`. About $0.14-0.24 per image. Not yet tested
end to end (no key at build time).

## Workflow
1. Pick an idea in the Outliers sheet; use its "Thumbnail Text" and "Thumbnail Concept" columns.
2. Make 2-3 Option A variants. If the concept copies a proven outlier layout, also try Option B.
3. Choose one, and keep the text readable at phone size (about 4 words max).
