"""Strung parts. Every builder returns an empty ("holder") whose local Z axis is
the thread direction and local X is the part's front (face normal)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise as mnoise
from .util import MM, link, revolve_mesh, sphere_mesh, chaton_mesh


# ---------------------------------------------------------------- rhinestone rondelle
def build_rondelle(tag, seed, cfg, mats):
    """Two dished, scallop-edged metal flanges with a band of foil-backed
    crystals between, stamped and hand-set (never perfectly regular).
    cfg: od_mm (8), thick_mm (4), stones (auto), metal material in mats['metal']"""
    od, th = cfg.get("od_mm", 8.0), cfg.get("thick_mm", 4.0)
    sr, sz = od / 8.0, th / 4.0
    rnd = random.Random(seed)

    def z_up(r):
        return (1.25 + 0.75 * (max(r - 1.05, 0.0) / 2.95) ** 1.3)

    prof = [(r, z_up(r)) for r in [1.05 + 2.9 * i / 16 for i in range(17)]]
    prof += [(4.02, z_up(4.0) - 0.10), (3.98, z_up(4.0) - 0.26)]
    prof += [(r, z_up(r) - 0.32) for r in [3.9 - 2.85 * i / 16 for i in range(17)]]
    prof = [(r * sr * MM, z * sz * MM) for r, z in prof]
    nlobes = max(6, round(9 * sr))
    amps = [rnd.uniform(0.05, 0.14) for _ in range(nlobes)]
    ph0 = rnd.uniform(0, 6.28)
    wob = Vector([rnd.uniform(-20, 20) for _ in range(3)])

    def scallop(sign):
        def w(r, z, phi):
            k = max(0.0, (r / (sr * MM) - 1.05) / 2.95) ** 3
            lobe = int(((phi + ph0) % (2 * math.pi)) / (2 * math.pi) * nlobes) % nlobes
            a = (amps[lobe] + amps[(lobe + 1) % nlobes]) / 2
            dz = a * math.cos(nlobes * phi + ph0) + 0.04 * mnoise.noise(Vector((math.cos(phi), math.sin(phi), 0)) * 2 + wob)
            dr = 0.03 * mnoise.noise(Vector((math.cos(phi), math.sin(phi), 1)) * 3 + wob)
            return r + dr * MM * k, z + sign * dz * sz * MM * k
        return w

    h = link(bpy.data.objects.new(f"rondelle_{tag}", None))
    top = revolve_mesh(f"flange_top_{tag}", prof, wave=scallop(1))
    bot = revolve_mesh(f"flange_bot_{tag}", [(r, -z) for r, z in reversed(prof)], wave=scallop(-1))
    core = revolve_mesh(f"core_{tag}", [(1.05 * sr * MM, -1.3 * sz * MM), (2.35 * sr * MM, -1.3 * sz * MM),
                                        (2.35 * sr * MM, 1.3 * sz * MM), (1.05 * sr * MM, 1.3 * sz * MM)], segs=72)
    for me in (top, bot, core):
        me.materials.append(mats["metal"])
        o = link(bpy.data.objects.new(me.name, me)); o.parent = h
        if me is not core:   # flanges crimped slightly out of true
            o.rotation_euler = (rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0)
    gem = chaton_mesh(f"chaton_{tag}")
    gem.materials.append(mats["gem"]); gem.materials.append(mats["foil"])
    prong = sphere_mesh(f"prong_{tag}", 0.28 * sz * MM, 12, 6)
    prong.materials.append(mats["metal"])
    n = cfg.get("stones", max(6, round(9 * sr)))
    gr, rc = 1.25 * sz * MM, 3.6 * sr * MM
    for k in range(n):
        phi = 2 * math.pi * k / n + rnd.uniform(-0.035, 0.035)
        radial = Vector((math.cos(phi), math.sin(phi), 0))
        rot = Matrix((Vector((0, 0, 1)), radial.cross(Vector((0, 0, 1))), radial)).transposed().to_4x4()
        wobm = (Matrix.Rotation(rnd.uniform(-0.12, 0.12), 4, 'X') @ Matrix.Rotation(rnd.uniform(-0.12, 0.12), 4, 'Y')
                @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, 'Z'))
        g = link(bpy.data.objects.new(f"gem_{tag}_{k}", gem))
        g.matrix_basis = (Matrix.Translation(radial * (rc + rnd.uniform(-0.07, 0.05) * MM)) @ rot @ wobm
                          @ Matrix.Scale(gr * rnd.uniform(0.94, 1.04), 4))
        g.parent = h
        mid = Vector((math.cos(phi + math.pi / n), math.sin(phi + math.pi / n), 0))
        for zs in (-1, 1):
            p = link(bpy.data.objects.new(f"prong_{tag}_{k}_{zs}", prong))
            p.location = mid * (3.72 * sr + rnd.uniform(-0.06, 0.06)) * MM + Vector((0, 0, zs * (1.2 * sz + rnd.uniform(-0.08, 0.08)) * MM))
            p.scale = (rnd.uniform(0.8, 1.2),) * 3
            p.parent = h
    h["sag_mm"] = 0.35
    return h


# ---------------------------------------------------------------- metal ball / round spacer
def build_metal_ball(tag, seed, cfg, mats):
    """Plated metal bead (e.g. the gold spacer balls in mixed-stone bracelets).
    cfg: diameter_mm (6), dents (True)"""
    d = cfg.get("diameter_mm", 6.0) * MM
    rnd = random.Random(seed)
    me = sphere_mesh(f"ball_{tag}", d / 2, 64, 32)
    bm = bmesh.new(); bm.from_mesh(me)
    off = Vector([rnd.uniform(-30, 30) for _ in range(3)])
    for v in bm.verts:
        n = v.co.normalized()
        v.co += n * d * 0.006 * mnoise.noise(n * 3 + off)
        if abs(n.z) > 0.93:   # drilled ends are flattened
            v.co.z = math.copysign(min(abs(v.co.z), d / 2 * 0.94), v.co.z)
    bm.to_mesh(me); bm.free()
    me.materials.append(mats["metal"])
    h = link(bpy.data.objects.new(f"ball_{tag}", None))
    o = link(bpy.data.objects.new(me.name, me)); o.parent = h
    return h


# ---------------------------------------------------------------- photo-relief charm
def _np_morph():
    import numpy as np

    def dilate(m, r):
        out = m.copy()
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
        return out

    def erode(m, r):
        return ~dilate(~m, r)
    return np, dilate, erode


def _flood(np, mask, seeds, passable):
    h, w = mask.shape
    out = np.zeros_like(mask)
    stack = list(seeds)
    while stack:
        y, x = stack.pop()
        if 0 <= y < h and 0 <= x < w and passable[y, x] and not out[y, x]:
            out[y, x] = True
            stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return out


def build_photo_charm(tag, cfg, mats):
    """Metal charm built straight from a close-up photo of the real part: the
    silhouette is the outline, brightness is the relief (bright metal = raised,
    grime = recessed) and drives the patina, so every lump and irregularity of
    the actual casting is reproduced.

    cfg: photo (path), width_mm (real size across the photo's horizontal),
         thread ('vertical' = thread runs up/down in the photo, or 'horizontal'),
         axis_x_px / axis_y_px (thread axis position in px; default bbox centre),
         relief_mm (0.5), back_mm (0.7),
         body {width_mm, length_mm, height_mm, offset_mm}  optional rounded body
         along the thread (like a butterfly's body)."""
    np, dilate, erode = _np_morph()
    img = bpy.data.images.load(cfg["photo"])
    w, h = img.size
    a = np.array(img.pixels[:]).reshape(h, w, 4)[::-1, :, :3]
    if cfg.get("thread", "vertical") == "horizontal":
        a = np.ascontiguousarray(np.rot90(a))
        h, w = a.shape[:2]
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / (mx + 1e-6)
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    border = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    bg = np.median(border, 0)
    bg_sat = (bg.max() - bg.min()) / (bg.max() + 1e-6)
    dist_bg = np.linalg.norm(a - bg, axis=2)
    mode = cfg.get("segment", "saturation" if bg_sat < 0.08 else "distance")
    if mode == "saturation":
        # metal photographed on a neutral (grey/white) background: metal and its
        # grime are coloured, background gradients and shadows are not
        fg = (sat > cfg.get("sat_threshold", 0.12)) | (lum < 0.12)
    else:
        # coloured background (e.g. velvet): distance from the background colour
        fg = (dist_bg > cfg.get("bg_distance", 0.25)) | (lum < 0.12)
    fg = erode(dilate(fg, 3), 3)
    border_seeds = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for x in range(w) for y in (0, h - 1)]
    outside = _flood(np, fg, border_seeds, ~fg)
    mask = erode(~outside, 2)
    # peel shadow: dark pixels touching the outside are the photo's shadowed
    # notches, not metal; strip them until the silhouette reaches real metal
    dark_t = cfg.get("shadow_lum", 0.24)
    for _ in range(26):
        edge = mask & ~erode(mask, 1)
        de = edge & (lum < dark_t)
        if not de.any():
            break
        mask &= ~de
    mask = dilate(erode(mask, 2), 2)
    ys, xs = np.nonzero(mask)
    x0 = cfg.get("axis_x_px", (xs.min() + xs.max()) / 2)
    y0 = cfg.get("axis_y_px", (ys.min() + ys.max()) / 2)
    cy, cx = int(y0), int(x0)
    if not mask[cy, cx]:
        k = np.argmin((ys - cy) ** 2 + (xs - cx) ** 2); cy, cx = ys[k], xs[k]
    mask = _flood(np, mask, [(cy, cx)], mask)     # drop detached flecks
    ys, xs = np.nonzero(mask)
    px_mm = cfg["width_mm"] / float(xs.max() - xs.min() + 1)

    blur = sum(np.roll(np.roll(lum, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9
    lo, hi = np.percentile(lum[mask], 4), np.percentile(lum[mask], 97)
    hgt = np.clip((blur - lo) / (hi - lo), 0, 1) ** 0.8
    shade = np.clip((lum - lo) / (hi - lo), 0, 1)
    dist = np.zeros(mask.shape)
    m = mask.copy()
    for k in range(1, 7):
        m = erode(m, 1)
        dist[mask & ~m & (dist == 0)] = k
    band = mask & (dist > 0) & (dist <= 5)
    soft = mask.astype(float)
    for _ in range(3):
        soft = sum(np.roll(np.roll(soft, dy, 0), dx, 1) for dy in range(-2, 3) for dx in range(-2, 3)) / 25
    rim = np.clip((soft - 0.35) / 0.6, 0, 1) ** 0.5
    hgt = np.where(band, np.maximum(hgt, 0.75 * rim), hgt)   # metal rim runs to the edge
    shade = np.where(band, np.maximum(shade, 0.62), shade)

    yy, xx = np.mgrid[0:h, 0:w]
    vv = (xx - x0) * px_mm
    uu = (y0 - yy) * px_mm
    body = cfg.get("body")
    dome = np.zeros(mask.shape)
    if body:
        across = np.clip(1 - (vv / (body["width_mm"] / 2)) ** 2, 0, None) ** 0.5
        along = np.clip(1 - ((uu - body.get("offset_mm", 0.0)) / (body["length_mm"] / 2)) ** 2, 0, None) ** 0.35
        dome = body.get("height_mm", 0.95) * across * along

    relief, back = cfg.get("relief_mm", 0.5), cfg.get("back_mm", 0.7)

    def P(v, u, wv):   # (span, along, normal) mm -> local metres (X=front, Y=span, Z=thread)
        return Vector((wv * MM, v * MM, u * MM))

    me = bpy.data.meshes.new(f"charm_{tag}")
    bm = bmesh.new()
    lay = bm.verts.layers.float.new("lum")
    vid = {}
    for y, x in zip(*np.nonzero(mask)):
        bv = bm.verts.new(P(vv[y, x], uu[y, x], relief * float(hgt[y, x]) + float(dome[y, x])))
        bv[lay] = float(shade[y, x])
        vid[(y, x)] = bv
    top = []
    for (y, x), v00 in vid.items():
        v01, v11, v10 = vid.get((y, x + 1)), vid.get((y + 1, x + 1)), vid.get((y + 1, x))
        if v01 and v11 and v10:
            f = bm.faces.new((v00, v10, v11, v01)); f.smooth = True
            top.append(f)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    rim_v = [v for v in bm.verts if v.is_boundary]
    for _ in range(25):
        bmesh.ops.smooth_vert(bm, verts=rim_v, factor=0.5, use_axis_x=False, use_axis_y=True, use_axis_z=True)
    band_v = [bv for (y, x), bv in vid.items() if bv.is_valid and 0 < dist[y, x] <= 6 and not bv.is_boundary]
    for _ in range(10):
        bmesh.ops.smooth_vert(bm, verts=band_v, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    ext = bmesh.ops.extrude_face_region(bm, geom=top, use_keep_orig=True)
    for g in ext["geom"]:
        if isinstance(g, bmesh.types.BMVert):
            g.co.x = -back * MM
            g[lay] = 0.62
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.materials.append(mats["photo_metal"])
    hobj = link(bpy.data.objects.new(f"charm_{tag}", None))
    o = link(bpy.data.objects.new(me.name, me)); o.parent = hobj
    hobj["faces_out"] = True
    print(f"charm {tag}: {mask.sum()} px, {px_mm:.4f} mm/px, size {cfg['width_mm']:.1f} x "
          f"{(ys.max() - ys.min() + 1) * px_mm:.1f} mm")
    return hobj


PART_BUILDERS = {
    "rondelle": build_rondelle,
    "metal_ball": build_metal_ball,
}
