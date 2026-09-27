# spec.json reference

One file per product: `<products_root>/<slug>/spec.json`. Relative paths resolve against that folder.
Working example: `${CLAUDE_PLUGIN_ROOT}/templates/spec.example.json` (the approved sunstone butterfly bracelet).

```jsonc
{
  "name": "Sunstone Butterfly Bracelet",
  "seed": 7,                          // change to reshuffle bead variation / loop shape
  "product": { ... },                 // see the product types below
  "materials": { "<stone>": { ... } },
  "look":   {"backdrop": "studio_white" | "velvet" | "linen",
             "backdrop_color": "royal_blue" | "burgundy" | "mustard" | "teal" | "emerald" | "purple" | "black" | "cream" | [r,g,b],
             "folds": 1.6,             // velvet fold height (0 = flat)
             "light": 1.0, "exposure": 0.0, "world_strength": 0.35,
             "grain": true, "vignette": false},
  "output": {"aspect": "16:9" | "9:16" | "1:1" | "4:5", "fps": 30, "zoom": 1.0},
  "videos": {"ad": {"seconds": 15}, "turntable": {"seconds": 8}},
  "turntable": {"elevation_deg": 31}
}
```

## product.type = "bracelet" | "anklet" | "strung"

```jsonc
"product": {
  "type": "bracelet",
  "sequence": ["bead:sunstone x10", "rondelle", "bead:sunstone x2", "charm:butterfly",
               "bead:sunstone x2", "rondelle", "bead:sunstone x4"],   // order around the loop
  "front": "charm:butterfly",           // piece that faces the camera (ad ends on it)
  "beads": {"sunstone": {"diameter_mm": 10, "material": "sunstone",
                         "hole_mm": 1.0, "variants": 5, "lumpiness": 1.0, "facets": 0}},
  "parts": {
    "rondelle":  {"type": "rondelle", "od_mm": 8, "thick_mm": 4, "stones": 9, "metal": "antique_brass"},
    "goldball":  {"type": "metal_ball", "diameter_mm": 6, "metal": "bright_gold"},
    "butterfly": {"type": "photo_charm", "photo": "photos/butterfly_closeup.png",
                  "width_mm": 11.3, "thread": "vertical",           // cord direction in the photo
                  "axis_x_px": 232, "axis_y_px": 172,                // optional: cord axis in px (default bbox centre)
                  "body": {"width_mm": 2.24, "length_mm": 7.1, "height_mm": 0.95, "offset_mm": -0.55},
                  "relief_mm": 0.5, "back_mm": 0.7, "shadow_lum": 0.24,
                  "segment": "saturation" | "distance",             // auto: neutral bg -> saturation
                  "metal": "antique_brass"}
  },
  "cord": {"diameter_mm": 0.9, "color": [0.85, 0.83, 0.78], "visible_gaps": 3, "show": true},
  "ovality": 0.045                     // how lopsided the relaxed loop is
}
```
Sequence tokens: `bead:<beadname> xN`, `<partname>`, `charm:<partname>` (the prefix is only a label; the name is
looked up in `parts`). Mixed-stone bracelets list several bead names.

Metals: `bright_gold`, `antique_brass`, `brass`, `rose_gold`, `silver`, `antique_silver`, `copper`, `gunmetal`, or `[r,g,b]`.

## product.type = "tumble"

```jsonc
"product": {"type": "tumble", "size_mm": [26, 22, 17], "material": "amethyst",
            "irregularity": 1.0, "boxiness": 0.5}     // 0 = pebble, 1 = rounded box
```

## product.type = "custom"

```jsonc
"product": {"type": "custom", "builder": "builder.py", ...anything the builder reads}
```
See `custom-products.md`.

## materials.<name>

Either `{"from_library": "amethyst", ...overrides}` or a full definition:

| key | meaning |
|---|---|
| `palette` | `[[pos, [r,g,b]], ...]`, linear RGB, pos 0–1, from `sample_palette.py` |
| `pattern` | fibrous · banded · crystalline · clear · mottled · speckled · metallic · porous |
| `flecks` | `{"density": 0–1, "color": [r,g,b]}` glitter (sunstone, aventurine) |
| `translucency`, `sss_radius` | subsurface glow and its colour falloff |
| `transmission`, `cloudiness`, `ior` | clear stones |
| `veins`, `fractures` | crystalline only (defaults 0.22 / 0.08) |
| `tone_variation` | per-bead light/dark variation (0.2) |
| `inclusions`, `inclusion_color` | dark specks (0.25) |
| `gloss` | coat roughness (0.03) |
| `realism` | 0–1 polish waviness, scratches and pits (1). Don't lower it unless asked. |
