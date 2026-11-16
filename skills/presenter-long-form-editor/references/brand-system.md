# Presenter long-form brand system

Use this reference for design and recurring editorial preferences. Adapt the themes, wordmark and presenter geometry to your own channel.

## Visual Themes

Projects support eight distinct visual themes selectable at the beginning of each edit.

Each theme lives in its own file. **Read only the file for the theme chosen for this project, and do not open the other theme files.** The sections below apply to every theme.

- `personal` (Signature — default for intros): [themes/personal.md](themes/personal.md)
- `lime-tech` (Hybrid Tech Theme): [themes/lime-tech.md](themes/lime-tech.md)
- `navy-amber` (Navy Amber Theme): [themes/navy-amber.md](themes/navy-amber.md)
- `dark-sketch` (Dark Sketch Explainer): [themes/dark-sketch.md](themes/dark-sketch.md)
- `warm-paper` (Warm Paper Sketch — default for long-form): [themes/warm-paper.md](themes/warm-paper.md)
- `blackboard-style` (Blackboard Live Pen): [themes/blackboard-style.md](themes/blackboard-style.md)
- `colorful-purple` (Hand-Drawn Infographic): [themes/colorful-purple.md](themes/colorful-purple.md)
- `clean-creator` (Clean Creator): [clean-creator-style.md](clean-creator-style.md)
- `teal-spotlight` (Teal Spotlight): [themes/teal-spotlight.md](themes/teal-spotlight.md)

## Visual character

These apply to every theme except where the sketch motion grammar (`dark-sketch`, `warm-paper`) overrides them.

- Premium educational/editorial rather than futuristic or game-like.
- Clear hierarchy, minimal chrome, and one focal idea per composition.
- Frame-driven fade-and-rise entrances, line draws, node progressions, and restrained sequencing.
- Avoid gradients unless nearly imperceptible, glossy glassmorphism, neon, particles, emojis, stock icons, fake dashboards, and generic AI imagery.
- **Brand icons**: when the narration names a brand (a company, model or product, such as TypeSafe, OpenAI/GPT, Claude, Gemini or Amazon), show its real, current icon. Don't use a drawn stand-in or generic icon, and don't make it text-only. This is the exception to "stock icons" above.
  - Fetch the latest mark, and confirm it has not been replaced by a rebrand. Amazon's 2012 logo was retired in 2025.
  - Prefer the brand's own site icon or SVG. Fall back to the Wikimedia Commons file of the current mark when the site blocks downloads.
  - Never redraw, distort or restyle a logo. A wordmark may be recoloured only to the brand's own dark-on-light version.
  - In the sketch themes, put square icons on a white tile with an 8px ink border and a corner radius of about 24% of the size, at roughly 64% fill. A disc-shaped icon fills about 84%. The brand name goes underneath as a label.
  - At 4K, tiles are 170–250px. Show wide wordmarks such as Amazon bare, at about 1000px wide.
  - Each icon lands on the word that names it.
  - Keep `SOURCES.json` beside the files with the source URL, date, hash and any recolouring.
- Motion exists to explain structure or emphasize a spoken payoff.
- Keep something in motion. An element that fades in and then holds perfectly still for eight to ten seconds reads as a frozen screenshot. Give each element a slow continuing drift of a few pixels after it lands, and a brief accent (a node pop, a line draw) at the moment it arrives.
- Audit gaps between reveals before rendering. Gaps beyond about two seconds, and tails beyond about two and a half seconds after the final reveal, are where a beat goes static; fill them with secondary motion rather than by moving narration-synced reveals.
- Reveal times are synchronised to speech and are not free to move. Increase liveliness through entrance snap, overshoot, accents, and drift, which cost no timing.
- Do not add slide, page, scene, or sequence numbering to full-screen animations, including labels such as `1/4` or `01 / 04`. Avoid decorative numbering that is not part of the spoken content.

## Brand signature

- The wordmark is optional. If the creator supplies one, record its exact text, colours and font here, and display it in the upper-right of every full-screen animation. If none is recorded, leave that corner empty and ask once whether they want one.
- Keep the wordmark fixed in the same position and scale across scenes.
- The wordmark is a restrained signature, not a headline: keep it small, clean, and clear of the scene's primary hierarchy.
- Do not substitute scene numbering, episode numbering, or a generic logo for the signature unless the creator explicitly requests it.

## Presenter protection

- Determine the safe region from representative frames of the actual source footage; do not assume the same composition in every video.
- Measure the protected presenter corridor for each camera setup. For example, with the presenter on the right of a 3840-pixel-wide frame it might begin at about `x=1600`; keep overlay pixels from there to the right edge transparent unless a full-screen cutaway has been explicitly selected.
- Avoid covering the face, eyes, microphone, or meaningful hand gestures even when they temporarily leave the usual corridor.
- Cards should generally stay within the left 40% and use a sufficiently opaque paper surface to remain legible over monitors.

## Editorial rhythm

- Keep presenter-led trust and personality moments visually clean.
- Use concise overlay cards for supporting facts and full-screen motion for concepts that genuinely need space.
- For an approximately 80-second intro, a few purposeful full-screen sequences are usually stronger than constant takeovers. Choose count and duration from the content, not a quota.
- Continue the speaker's narration through full-screen cutaways so the edit feels intentional and connected.
- Prefer natural breath and phrase spacing over rapid jump cuts.

## Long-form rhythm

- Choose a mode per section, not per sentence:
  - Full-frame presenter: the hook, opinions, stories, links between sections, and the call to action. This is where trust comes from.
  - `PRESENTER_INSET`: explanations of about a minute or more that need space while the creator stays present.
  - `FULLSCREEN_MOTION`: short moments that need the viewer's full attention, and every audio-only section.
- As a starting point, keep about half of the camera runtime full-frame. This is a guide, not a quota.
- Exception: when the creator has ruled out full-frame for a camera setup, the stage-size masked window takes the full-frame role. Roughly balance stage and corner time instead (about 40% each).
- Stay in a mode for a whole idea. Avoid entering and leaving the inset within about 30 s.
- A constant inset suits live demos and screen recordings, where the screen is the subject. With authored graphics it reads as a webinar and forces filler graphics.

## Presenter inset and directional entrances

- `PRESENTER_INSET`: animate the entire video from full frame into a corner, preserving its aspect ratio and full image. Keep playback and narration continuous. Use the remaining canvas for a process, comparison, or explanation while the creator stays visible.
- Choose the corner and inset size from the actual composition and graphics layout, keeping the presenter legible. Reserve the inset rectangle throughout the scene; graphics, captions, and branding must not cover it. Keep the upper-right wordmark clear when using the branded explanatory canvas.
- Animate scale and position together with restrained easing, settle the inset before major explanatory reveals, and smoothly return to full frame at the end of the beat. Fit both transitions within the locked timeline.
- Scale the picture about its own centre and move that centre along a single path from screen centre to inset centre. Never combine a corner `transform-origin` with an animated `left`/`top`: the two motions compound, the leading edge races the trailing one, and the picture appears to collapse sideways instead of tucking into the corner.
- Ease the inset move with smootherstep (`6x^5-15x^4+10x^3`), not a cubic ease-in-out. Cubic concentrates travel at the midpoint; on a 4K inset move that reached 277 px in a single frame while the picture was also shrinking, which reads as a lurch. Budget roughly 1.1 s for the move in and 0.75 s out, and check the peak per-frame travel rather than trusting the curve name.
- Give the inset rounded corners and a visible border. Divide the radius and border width by the current scale so both hold a constant on-screen weight through the move instead of ballooning as the picture shrinks.
- Use the muted tone (`#737985`) for the inset border. The `line` tone (`#d7d4cc`) disappears against warm paper.
- Composite every inset and full-screen move in one per-frame pass, with picture, corner radius, border and shadow derived from a single geometry. Never draw moving chrome with FFmpeg `drawbox`: it evaluates its geometry once, and its `t` is thickness, not time, which leaves a frozen ghost box during the move (2026-10-06).
- Ramp the inset chrome (radius, border, shadow) with move progress so that it is exactly zero at full frame. The first and last frames of each move must equal the untouched footage, and the verifier proves this against the source. Avoid segment splices and `enable` switches.
- Give inset and full-screen moves a 180° shutter of motion blur and sub-pixel positioning. Full-screen panels slide over a parallax-pushed, slightly dimmed footage layer, with a soft leading-edge shadow.
- Hold explanatory graphics until the inset has landed, then fade them in (in the sketch themes, build them instantly instead). Derive that timing from the transition duration; hardcoding it desynchronises the moment either one changes, and text arriving mid-move competes with the travelling picture.
- Full-screen animations enter from the right, top, or bottom via a clean slide or wipe. Choose direction to suit the composition and maintain continuity across related scenes; do not randomize it or cycle directions by quota.
- Transition the scene as a coherent composition, then reveal its internal elements in sequence. Keep the brand signature at its established position and scale in the resolved layout. Allow reading time after the entrance and plan the exit back to footage.
- Choose inset when continued presenter presence benefits a spacious explanation; choose full-screen when the visual needs undivided attention or the entire canvas. Neither has a fixed runtime quota.

### Corner moves while floating (long-form)

- While the inset floats, move it to another corner every now and then so the screen feels responsive. Tie each move to a new sub-idea or to a layout that needs the other side, never to a timer.
- Hold each corner for at least about 20 s. Roughly one move per 45–90 s of continuous inset time is enough.
- Move only between sentences, never during a narration-synced reveal.
- Use the corners that the scene title and the wordmark leave free. In the sketch themes the title holds the top-left and the wordmark holds the top-right, so the inset moves between bottom-left and bottom-right.
- Keep the inset's size and edge margins identical in every corner, so a move is a pure translation with constant scale and constant chrome. Default at 4K: 960×540 with 120px margins (bottom-left x=120, y=1500; bottom-right x=2760, y=1500). This applies to the uncropped rectangular inset. A masked presenter uses the "Presenter mask" geometry in [themes/warm-paper.md](themes/warm-paper.md).
- When the presenter gestures or looks to one side, prefer the corner from which that gesture points into the graphics. If they look to one side for the whole recording (an angled laptop camera, for example), keep the window on the side they face and skip side swaps. Moving it to the other side would make them look out of frame.
- Mechanics: move the centre along one straight path with smootherstep, in the same single-pass compositor with a 180° shutter. Budget about 1.3 s along the bottom edge (peak ≈127 px/frame at 4K, 29.97 fps), and audit the peak per-frame travel as for every inset move.
- Keep the travel path clear. Prefer moving during the empty-canvas beat between scenes, then build the next scene around the new corner. If graphics stay on screen during the move, none may intersect the band the inset sweeps through.
- While the inset sits in a bottom corner, keep that side's content above y≈1420 at 4K and put anything tall on the other side.
- In the directive, a move is two contiguous `PRESENTER_INSET` beats with the same inset size and different positions, with `transition_out: "corner-move"` on the first and `transition_in: "corner-move"` on the second. The validator checks this.

## Final-cut input

When the creator provides a final cut, treat it as the locked base: no trimming, take selection, reordering, retiming, or audio changes unless explicitly requested. Add visual animation within its existing duration. Transcription is for visual synchronization, not spoken editing. A long-form cut may arrive as several camera and audio-only sections; see "Audio-only sections".

## Audio-only sections

The creator may supply some sections as audio only. Graphics take the full screen for the whole of each such section.

- Ask for the order of camera and audio-only sections if the creator hasn't given it. Assemble them in that order into one locked program without trimming, reordering, or retiming. An audio-only section gets a plain canvas in the theme background for its full duration.
- Hash every segment and the assembled program. `source` describes the assembled program, directive times are program seconds, and `segments` records each piece (see `editorial-directive.md`).
- Cover every second of an audio-only segment with `FULLSCREEN_MOTION` beats. No presenter, inset, overlay, or selective text inside it. The validator enforces this.
- Enter an audio-only section with the standing full-screen entrance (slide or wipe from the right, top, or bottom). Leave it back to full-frame camera, or straight into the inset when the next section opens with an explanation.
- With no face on screen, the canvas carries the section. Keep the build cadence dense (in the sketch themes, a build every 2–6 s) and use the empty-canvas beat between topics.
- Separately recorded voiceover often differs from camera audio in loudness and room tone. Measure each segment. If they differ by more than about 1 LU, propose per-segment gain to the program target and record it in the directive. Do not EQ or denoise without approval. Listen to and inspect every join for clicks.
- The full-screen share warning counts camera time only; audio-only sections are full-screen by design.

## Diagram geometry

- Give connectors their own measured channel between nodes or cards; do not route a line or arrowhead through typography.
- Keep visible clearance at both connector endpoints. On a 3840-pixel-wide full-screen composition, use roughly 120 pixels or more when the layout permits.
- Prefer a simple line-and-node progression over a decorative arrow when labels are large.
- Inspect the resolved connector state at native delivery resolution, not only in a scaled contact sheet.

## Quality and delivery

- Default to the source's native 4K frame, exact rational frame rate, BT.709 metadata, and 48 kHz audio when those match the source.
- Use a restrained corrective grade and evaluate skin tone before applying it globally.
- Aim for clear YouTube speech around `-14 LUFS` with a `-1 dBTP` ceiling when normalization is needed; measure rather than assume.
- Deliver an upload-ready master plus reusable alpha assets and editable source.
