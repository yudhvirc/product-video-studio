"""Build a product scene from a spec and save it as a .blend.

  blender -b --python build.py -- <spec.json> <ad|turntable> <out.blend> [proof|final|high]

Relative paths inside the spec (photos) resolve against the spec's folder.
Also writes <out.blend>.json with frame count and scene facts for the tools."""
import bpy, json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pvs import materials as M, strung, tumble, studio, camera, render  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
spec_path, kind, out_blend = args[0], args[1], args[2]
quality = args[3] if len(args) > 3 else "final"
spec_dir = os.path.dirname(os.path.abspath(spec_path))
with open(spec_path, encoding="utf-8") as fh:
    spec = json.load(fh)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
rng = random.Random(spec.get("seed", 7))
prod = spec["product"]

# ---------------------------------------------------------------- materials
def load_library():
    """Approved stone looks: <products_root>/_library/stones.json overrides the
    plugin's templates/stones.json."""
    lib = {}
    for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "stones.json"),
              os.path.join(spec_dir, "..", "_library", "stones.json")):
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                lib.update({k: v for k, v in json.load(fh).items() if not k.startswith("_")})
    return lib


library = load_library()
mats = {}
for name, cfg in spec.get("materials", {}).items():
    if "from_library" in cfg:
        base = dict(library[cfg["from_library"]])
        base.update({k: v for k, v in cfg.items() if k != "from_library"})
        cfg = base
    mats["stone:" + name] = M.stone_material(name, cfg)
metal_cache = {}


def metal(color_spec, kind="plated"):
    key = (str(color_spec), kind)
    if key not in metal_cache:
        c = M.metal_rgb(color_spec)
        metal_cache[key] = (M.plated_metal_material if kind == "plated" else M.photo_metal_material)(
            f"{kind}_{color_spec}", c)
    return metal_cache[key]


gem, foil = M.rhinestone_material(), M.foil_material()
for pname, pd in prod.get("parts", {}).items():
    if pd["type"] == "photo_charm":
        pd["photo"] = os.path.join(spec_dir, pd["photo"]) if not os.path.isabs(pd["photo"]) else pd["photo"]
        mats["part:" + pname] = {"photo_metal": metal(pd.get("metal", "antique_brass"), "photo")}
    else:
        mats["part:" + pname] = {"metal": metal(pd.get("metal", "antique_brass")), "gem": gem, "foil": foil}
mats["cord"] = M.cord_material(prod.get("cord", {}).get("color", (0.85, 0.83, 0.78)))

# ---------------------------------------------------------------- product
ptype = prod["type"]
if ptype in ("bracelet", "anklet", "strung"):
    info = strung.build(spec, mats, rng)
elif ptype in ("tumble", "tumble_stone"):
    info = tumble.build(spec, mats, rng)
elif ptype == "custom":
    # product-specific builder module: build(spec, mats, rng) -> info dict (see custom-products.md)
    import importlib.util
    bp = os.path.join(spec_dir, prod["builder"])
    mod_spec = importlib.util.spec_from_file_location("pvs_custom_builder", bp)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    info = mod.build(spec, mats, rng)
else:
    raise SystemExit(f"product.type {ptype!r} has no builder yet: model it as a custom scene "
                     f"(see skills/product-video/reference/custom-products.md)")

studio.build(spec, info, rng)

# ---------------------------------------------------------------- camera + timing
fps = spec.get("output", {}).get("fps", 30)
vid = spec.get("videos", {}).get(kind, {})
secs = vid.get("seconds", 15 if kind == "ad" else 8)
frames = int(round(secs * fps))
sc.render.fps = fps
sc.frame_start, sc.frame_end = 0, frames - 1
if kind == "turntable":
    camera.turntable(spec, info, frames)   # frame N == frame 0: seamless loop
elif kind == "ad":
    camera.ad(spec, info, frames)
else:
    raise SystemExit(f"unknown video kind {kind}")
render.configure(spec, quality)

bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
with open(out_blend + ".json", "w") as fh:
    json.dump({"frames": frames, "fps": fps, "seconds": secs, "extent_mm": info["extent"] * 1000,
               "kind": kind, "quality": quality}, fh)
print(f"PVS built {kind}: {frames} frames @ {fps} fps, extent {info['extent'] * 1000:.1f} mm -> {out_blend}")
