# Product Video Studio (Claude Code plugin)

Photoreal 3D product videos of jewelry and crystal products from ordinary product photos:
a **15 s cinematic ad** (close glide → reveal → hero) and a **seamless 8 s turntable loop**,
rendered with Blender Cycles. Products are matched to the real piece, including its imperfections.

## Install

```text
/plugin marketplace add C:\temp\tathastumedia\plugins
/plugin install product-video-studio@tathastu-tools
```
After editing the plugin, run `/reload-plugins` (or `/plugin marketplace update tathastu-tools`).
Validate with `claude plugin validate C:\temp\tathastumedia\plugins`.

Requirements (checked by `tools/check_env.sh`): Blender 5.x (the portable build in `C:\tools` is fine),
ffmpeg, Node.js, and bash (Git Bash on Windows).

## Use

| You say | Skill |
|---|---|
| "Make a 3D video of the green onyx bracelet in products\green-onyx" | `/product-video-studio:product-video` |
| "Make videos for all the new products in C:\temp\tathastumedia\products" | `/product-video-studio:product-video-batch` |
| "How far along is the batch render?" | batch (runs `batch.sh status`) |

Both skills interview you first, show preview stills and side-by-sides with your photos, then a quick proof
video, and only then run the multi-hour final render.

## Products folder

```
products/
  _library/stones.json          approved stone looks (reused across products)
  <slug>/photos/                overview + close-up of every charm/spacer + a daylight shot
  <slug>/spec.json              product description (the skill writes it)
  <slug>/previews/vN proofs/vN final/vN     every run adds a new version; nothing is ever overwritten
                                            (frames/.blend cache: %LOCALAPPDATA%\pvs_work\<slug>)
```

## What's built in

- **Strung** bracelets and anklets: beads (any stone), rhinestone rondelles, metal balls, and photo-relief
  charms built from a close-up photo. A relaxed irregular loop with the cord showing in some gaps.
- **Tumble stones**: irregular polished pebbles, from pebble-round to rounded-box.
- **Stone patterns:** fibrous · banded · crystalline · clear · mottled · speckled · metallic · porous,
  with a library of starting looks.
- **Backdrops:** studio white, and velvet or linen in the shop's colours (royal blue, burgundy, mustard, teal,
  emerald, purple, black, cream).
- **Aspects:** 16:9, 9:16, 1:1, 4:5. **Quality:** proof (about 2 s/frame), final (about 12 s/frame), high
  (about 30 s/frame), measured on a 16-core CPU.
- **Custom products** (rings, gem trees, malas, pyramids, Shivling, selenite): a builder hook plus recipes in
  `skills/product-video/reference/custom-products.md`.

## Command-line tools (what the skills run)

```bash
tools/check_env.sh                                   # find Blender / ffmpeg
tools/render.sh   <product_dir> stills|proof|final|high [ad|turntable|both]
tools/checks.sh   <product_dir> charms|sheet|proofsheet
tools/batch.sh    <products_root> status|stills|proof|final|contact [slug ...]
blender -b --python tools/sample_palette.py -- <photo> x0 y0 x1 y1 [--white x0 y0 x1 y1]
```
Renders are resumable: re-run the same command after an interruption.
