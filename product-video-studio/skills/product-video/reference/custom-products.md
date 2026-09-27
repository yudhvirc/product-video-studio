# Custom products (no built-in builder yet)

Built in: **strung** (bracelets, anklets) and **tumble** (single polished stones). Everything else uses
`"type": "custom"` with a small builder module in the product folder. It gets the same studio, lights, camera
moves, render presets, encoding and review tools for free.

## Builder contract

`<slug>/builder.py`, referenced as `"product": {"type": "custom", "builder": "builder.py", ...}`:

```python
import bpy, math, sys, os
from mathutils import Vector
# the engine's helpers are importable: from pvs.util import MM, link, sphere_mesh, revolve_mesh, bead_mesh, tube_curve
# from pvs import parts, materials as M      (parts.build_photo_charm, M.stone_material, M.plated_metal_material, ...)

def build(spec, mats, rng):
    root = link(bpy.data.objects.new("Product", None))
    ...  # build at real size in metres; parent everything to root; rest it on z = 0
    E = ...  # radius of the product's footprint (m)
    H = ...  # height (m)
    def glide_point(t):               # t 0 -> 1: where the opening close-up travels over the product
        ang = math.radians(-90 + 60 * (1 - t))
        return Vector((math.cos(ang) * E * 0.5, math.sin(ang) * E * 0.5, H * 0.7)), ang
    return {"root": root, "extent": E, "height": H, "center": Vector((0, 0, H * 0.45)),
            "glide_point": glide_point, "hero_angle": math.radians(-90),
            "front_focus_radius": E * 0.5, "focus_z": H * 0.6,
            "macro_distance": 6.0}      # opening distance in units of E (4 = very close, 7 = relaxed)
```
Materials in `mats` are built from `spec.materials` as `mats["stone:<name>"]`. For metals, call
`M.plated_metal_material(name, M.metal_rgb("bright_gold"))`.

Tall products (trees, Shivling): the rig assumes a low product, so raise `turntable.elevation_deg` to 15–20
and check the framing in stills. Set `output.zoom` below 1 to pull back.

## Recipes for the Tathastu catalogue

| Product | Approach |
|---|---|
| **Mala** (108 beads + guru bead + tassel) | Reuse `strung.build` with a long sequence, but lay the loop as a coil or teardrop. Write a custom `loop_pt` path. Guru bead: a larger bead. Tassel: 150–300 `tube_curve` strands (0.15 mm) with random length and droop, gathered by a wrapped cap. Ask for a photo of the tassel and guru bead. |
| **Crystal ring in box** | Ring band: `revolve_mesh` of a D-profile in the metal colour. Bezel with prongs: small tubes. Oval cabochon: an ellipsoid dome with the stone material. White box: a rounded box with a slot cushion (velvet material in cream). Hero = the stone. Ask for ring size and stone size (mm). |
| **Gem tree** (300 chips) | Trunk and branches: twisted wire as bundles of `tube_curve` with bark-brown metallic wire. Chips: 300 small irregular tumble meshes (reuse `tumble.build`'s shape code, 4–8 mm) at branch tips. Base: a wooden disc slice (bark-ring texture) or a stone cluster. Tall: see above. |
| **Pyrite pyramid / orgonite** | Square pyramid with resin (clear material with low transmission and tint), embedded chips and copper coil (`tube_curve` helix). Base plate: selenite (fibrous white, high translucency). |
| **Parad Shivling** | Lathe profile (`revolve_mesh`) for the lingam and a yoni with spout. Silvery mercury alloy: metal `antique_silver`, low roughness, soft smudges. |
| **Selenite charging plate / bowl** | Plate: extruded square with an engraved design from a photo (use photo-relief on the engraving photo, with the relief inverted). Bowl: lathe profile with a gold scalloped rim (reuse the rondelle scallop wave). Selenite: `fibrous` white palette, translucency 0.6. |
| **Pendant** (heart on chain) | Pendant: tumble shape with `boxiness` 0 plus a heart outline (or photo charm). Chain: a torus-link array along a curve. Bail: a small bent tube. |
| **Door hanging** | Mostly beads on cord (strung) plus charms from photos. Hang it vertically: rotate the root and hide the floor, or keep velvet behind. |
| **Safed Sarso** (seeds in a glass bowl) | Glass bowl lathe profile (clear, IOR 1.5). About 3,000 small spheres scattered by a simple drop-and-settle heap (a stacked random packing is enough). |

Always keep the realism rules: irregular shapes, varied parts, worn metal, and photo-derived details.
