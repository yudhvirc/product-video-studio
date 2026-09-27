# Quality checklist: run it yourself before the user sees anything

Read `previews/_sheet.png`, the full-size stills, and every `previews/compare_*_vs_photo.png`.

## Truth to the product
- [ ] Bead count, sizes and **sequence** match the photos, and the right piece faces front.
- [ ] Every component is present (compare against each photo; missing charms are the #1 miss).
- [ ] Stone colour **side by side** with the true-colour photo: hue, depth, saturation, pattern scale.
      Beads vary bead to bead like real stones. The pattern isn't zebra stripes or a uniform flat colour.
- [ ] Photo charms: silhouette, relief and patina match the close-up. No dark fringe or black bleeding past
      the edge, no pixel staircase on the outline, no floating flecks.
- [ ] Metals match each other (unless specified) and read as the right metal (plated vs antique).
- [ ] Crystals in rondelles read clear or white with sparkle, not gold-tinted.

## Realism (not "too perfect")
- [ ] Loop is a relaxed irregular oval. Gaps are uneven and the cord shows in a few.
- [ ] Beads are slightly out of round, with drill holes visible where the view allows.
- [ ] Highlights wobble a little. Metal shows smudges and tarnish, and castings are lumpy.
- [ ] Nothing floats above or sinks into the surface (check contact shadows).

## Image
- [ ] Exposure: studio white background ≈ 0.93–0.96 (not grey, not clipped). Velvet is deep, with visible sheen.
- [ ] Opening macro is in focus on the glided-to detail, and the final hero frame is sharp on the front piece.
- [ ] Framing: the product fills the frame sensibly for the aspect ratio (adjust `output.zoom`).
- [ ] No texture swimming. Any scaled "unit" meshes have their scale baked in (photo charms are fine).

## Motion (proofs)
- [ ] Glide → reveal → hero is continuous, with no stops or jumps (`checks.sh proofsheet`, one frame/sec).
- [ ] Turntable loops seamlessly (frame N == frame 0).
- [ ] Ad fades in and out (white on studio white, black on velvet or linen).

## Known engine pitfalls
- Blender `Image.pixels` values for JPG/PNG behave like display values. `sample_palette.py` is calibrated for
  that. Always confirm colours by eye.
- Procedural textures use object coordinates. A mesh built in metres but textured like a unit sphere shows as
  flat colour. Build unit-size meshes and scale the object.
- Don't edit `render.sh` while it runs (bash reads scripts incrementally).
