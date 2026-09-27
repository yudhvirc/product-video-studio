---
name: product-video
description: Create a photoreal 3D product video (cinematic ad + seamless 360° turntable) of a jewelry or crystal product from its photos, using Blender. Use when the user asks for a 3D video, 3D render, turntable, product spin, reel or video ad of a bracelet, anklet, mala, charm, tumble stone, crystal or similar product shown in photos. Interviews the user, builds a spec, and runs a preview → proof → final pipeline.
argument-hint: "[product folder or photo path]"
---

# Product Video Studio: single product

Turn product photos into a photoreal 3D **ad** (default 15 s) and a seamless **turntable loop** (default 8 s),
matched to the real piece, including its imperfections.

Everything lives in the plugin:
- `${CLAUDE_PLUGIN_ROOT}/engine/`: Blender scene builder (`build.py` + `pvs/`), driven by a `spec.json`
- `${CLAUDE_PLUGIN_ROOT}/tools/`: `check_env.sh`, `sample_palette.py`, `render.sh`, `checks.sh`, `batch.sh`
- `${CLAUDE_PLUGIN_ROOT}/templates/`: `stones.json` (stone look library), `spec.example.json`
- `reference/` next to this file: the interview, the spec format, the quality checklist, custom products

Run the tools with **bash** (Git Bash on Windows). Blender runs on the CPU. Expect about 2 s/frame for proofs
and about 12 s/frame for finals on a 16-core CPU. A 15 s + 8 s pair at 30 fps is 690 frames: roughly 25 min
for a proof and 2–3 h for a final.

## Ground rules (learned the hard way)

1. **Match the real piece, flaws included.** CG-perfect is a failure. Keep the realism defaults on: lumpy beads,
   drill holes, uneven gaps with the cord visible, crimped rondelles, hand-set stones, cast-metal lumpiness,
   polish waviness, a relaxed lopsided loop, handheld drift, and film grain. The user rejected "too perfect" renders.
2. **Never guess a component from a blurry wide shot.** If a charm, spacer or pendant isn't clearly visible, ask
   for a close-up photo before modeling it. An earlier attempt modeled a "tag" that turned out to be a butterfly.
3. **Charms and pendants come from their photo** (`photo_charm`). Don't hand-model decorative detail. Photo-relief
   reproduces the real casting. Always run `checks.sh <dir> charms` and compare side by side.
4. **Colours are confirmed by eye, side by side with the photo.** Measurements help, but pixel filters bias them.
   Use `sample_palette.py` for a start, then iterate with preview stills.
5. **All metals on one piece should match** unless the user says otherwise (e.g. rondelles vs charm).
6. **Gates:** stills → user OK → proof video → user OK → final. Never start a long render without an explicit go.
   Always state the time estimate. Never edit a script while a render is using it.
7. **Never delete or overwrite anything in the user's project or product folders**, including files you made
   earlier. The tools already write each run to a new version folder (`previews/vN`, `proofs/vN`, `final/vN`)
   and keep frames and .blend files in a cache outside the project (`%LOCALAPPDATA%/pvs_work/<slug>`). When
   re-encoding or fixing, write alongside and never on top. If a cleanup seems really needed, ask first. (The
   user explicitly asked for this.)

## Workflow

### 0. Environment
`bash ${CLAUDE_PLUGIN_ROOT}/tools/check_env.sh`. If Blender or ffmpeg is missing it prints install steps
(portable Blender from a mirror with SHA-256 check; `winget install Gyan.FFmpeg`). Ask before installing.

### 1. Look at everything first
Create or confirm the product folder: `<products_root>/<slug>/photos/` (copy the user's photos in). **Read every
photo.** Identify the family (strung / tumble / other), count beads, measure relative sizes, and list every
non-bead component and its position in the sequence. Note which photos show true colour.

### 2. Interview
Follow `reference/interview.md`. Ask only what the photos can't answer, at most 4 questions per round, and
usually 2–3 rounds. Put a recommended default first. The questions that matter most, in order:
use/format → look/backdrop → what the videos should show → quality/time budget → product truth
(stone, bead size/count, sequence, the "front" piece, finishing) → missing close-ups.

### 3. Spec
Write `<slug>/spec.json` (format: `reference/spec-reference.md`, example: `templates/spec.example.json`).
- Stones: use `"from_library": "<stone>"` when `templates/stones.json` or `<root>/_library/stones.json` has it.
  Otherwise sample: `"$PVS_BLENDER" -b --python ${CLAUDE_PLUGIN_ROOT}/tools/sample_palette.py -- <photo> x0 y0 x1 y1 [--white ...]`.
  Pick the box by viewing the photo. Take the stone only, the most typical and well-lit part, avoiding reflections
  of coloured cloth.
- Photo charms: `width_mm` is the real size across the photo's horizontal. Set `thread` to the direction the
  cord runs in the photo. Add `body` for a raised centre body.
- Unsupported product type → `reference/custom-products.md`.

### 4. Preview stills (≈1–2 min)
`bash ${CLAUDE_PLUGIN_ROOT}/tools/render.sh <dir> stills` (writes `previews/vN/`), then `checks.sh <dir> sheet` and
`checks.sh <dir> charms` (both add files to the latest `previews/vN`).
Read the images and go through `reference/quality-checklist.md` yourself **before** showing the user. Fix and
re-render until it passes, then show the user the sheet plus the side-by-sides. Expect 1–3 rounds for a new
stone type.

### 5. Proof videos (≈25 min for 15 s + 8 s)
Only after the user OKs the stills: `render.sh <dir> proof` in the background, then `checks.sh <dir> proofsheet`,
review, and hand the user the latest `proofs/vN/*.mp4`. Mention that proofs are half-res and slightly noisy by design.

### 6. Final
Only on an explicit go with the frame rate confirmed: `render.sh <dir> final` in the background (use `high` only
if asked). Check progress with `batch.sh <products_root> status` (it counts cached frames). When it finishes, verify with ffprobe
(duration, frame count, resolution) and look at a few frames. Then deliver the latest `final/vN/*.mp4` with a short summary.
If interrupted, re-run the same command and it resumes.

### 7. Capture what was learned
If the user approved a new stone look, add it to `<products_root>/_library/stones.json` (with a `status` note) so
batch runs reuse it. Record user preferences (backdrop, vignette, fps) in the products root `README` or memory.
