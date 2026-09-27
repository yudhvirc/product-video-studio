"""Sample a stone colour palette from a product photo.

  blender -b --python sample_palette.py -- <image> <x0> <y0> <x1> <y1> [--white wx0 wy0 wx1 wy1]

(x0,y0)-(x1,y1): pixel box over the stone only (one bead or the tumble stone,
no background). Optional --white box over white paper / a white card normalises
exposure; without it the brightest neutral pixels in the photo are used.

Prints a `palette` JSON ready for spec.materials.<name>.palette. The colours are
pre-compensated for how the renderer brightens polished, translucent stone
(exponent 1.6 - calibrated on the sunstone bracelet); always confirm with a
preview still next to the photo and nudge if needed."""
import bpy, sys, json
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
path = a[0]
x0, y0, x1, y1 = map(int, a[1:5])
white = None
if "--white" in a:
    i = a.index("--white")
    white = list(map(int, a[i + 1:i + 5]))
img = bpy.data.images.load(path)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[::-1, :, :3]   # top row first; linear
crop = px[min(y0, y1):max(y0, y1), min(x0, x1):max(x0, x1)].reshape(-1, 3)
if white:
    ref = px[white[1]:white[3], white[0]:white[2]].reshape(-1, 3).mean(0)
else:
    mx, mn = px.max(2), px.min(2)
    neutral = px[((mx - mn) / (mx + 1e-6) < 0.08)]
    ref = np.percentile(neutral, 97, axis=0) if len(neutral) > 100 else np.array([0.9, 0.9, 0.9])
alb = np.clip(crop / ref * 0.85, 0, 1)
lum = alb @ np.array([0.2126, 0.7152, 0.0722])
keep = (lum > np.percentile(lum, 3)) & (lum < np.percentile(lum, 96))   # drop specular highlights / deep shadow
alb, lum = alb[keep], lum[keep]
sat = (alb.max(1) - alb.min(1)) / (alb.max(1) + 1e-6)
# The stone's own colour is its most saturated pixels; greyish ones are mostly
# reflections of the surroundings (e.g. a coloured cloth bouncing onto the stone)
# or shadow. Dark-to-mid stops take their hue from the saturated half; the top
# stop (veins / highlights of the pattern) keeps its natural paleness.
chroma = sat >= np.median(sat)
stops = []
for pos, q in zip([0.30, 0.42, 0.52, 0.62, 0.76], [8, 30, 50, 70, 94]):
    t = np.percentile(lum, q)
    near = np.abs(lum - t) < 0.03
    sel = alb[near & chroma] if q < 90 and (near & chroma).sum() > 20 else alb[near]
    c = sel.mean(0) if len(sel) else alb[np.argmin(np.abs(lum - t))]
    stops.append([pos, [round(float(v) ** 1.6, 3) for v in c]])
print("PALETTE_JSON " + json.dumps(stops))
mx, mn = alb.max(1), alb.min(1)
print(f"# median saturation {np.median((mx - mn) / (mx + 1e-6)):.2f}, luminance spread {lum.std():.3f}, "
      f"pixels {len(alb)}, white ref {np.round(ref, 3).tolist()}")
