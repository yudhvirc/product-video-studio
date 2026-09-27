"""Strung products (bracelets, anklets): beads and parts on a cord, lying
relaxed on a surface as a lopsided oval, with uneven gaps where the cord shows."""
import bpy, math, random, re
from mathutils import Vector, Matrix
from .util import MM, link, bead_mesh, tube_curve, assembly_points, nest_distance
from . import parts as P


def expand_sequence(seq):
    """["bead:sunstone x10", "rondelle", "charm:butterfly", ...] -> list of (kind, name)."""
    out = []
    for tok in seq:
        m = re.match(r"^\s*([a-z_]+)(?::([\w\-]+))?\s*(?:x\s*(\d+))?\s*$", tok)
        if not m:
            raise ValueError(f"bad sequence token: {tok!r}")
        kind, name, n = m.group(1), m.group(2), int(m.group(3) or 1)
        out += [(kind, name or kind)] * n
    return out


def build(spec, mats, rng):
    prod = spec["product"]
    items = expand_sequence(prod["sequence"])
    N = len(items)
    beads_def = prod["beads"]
    parts_def = prod.get("parts", {})
    root = link(bpy.data.objects.new("Product", None))

    # bead mesh variants per bead type (shape + hole variation)
    bead_meshes = {}
    for bname, bd in beads_def.items():
        hole = bd.get("hole_mm", 1.0) / bd["diameter_mm"]
        bead_meshes[bname] = []
        for k in range(bd.get("variants", 5)):
            me = bead_mesh(f"bead_{bname}_{k}", rng.randint(0, 10 ** 6), hole=hole,
                           lumpiness=bd.get("lumpiness", 1.0), facets=bd.get("facets", 0))
            me.materials.append(mats["stone:" + bd["material"]])
            bead_meshes[bname].append(me)
    radii = [beads_def[n]["diameter_mm"] / 2 * MM * rng.uniform(0.98, 1.02) if k == "bead" else None
             for k, n in items]

    holders, clouds = {}, {}
    for i, (kind, name) in enumerate(items):
        if kind == "bead":
            continue
        pd = parts_def[name]
        pm = mats["part:" + name]
        if pd["type"] == "photo_charm":
            holders[i] = P.build_photo_charm(f"{name}_{i}", pd, pm)
        else:
            holders[i] = P.PART_BUILDERS[pd["type"]](f"{name}_{i}", rng.randint(0, 10 ** 6), pd, pm)
        clouds[i] = assembly_points(holders[i])

    cord = prod.get("cord", {})
    gaps = [rng.uniform(0.00005, 0.00035) for _ in items]
    for k in rng.sample(range(N), min(N, cord.get("visible_gaps", 3))):
        gaps[k] = rng.uniform(0.0006, 0.0009)

    def spacing(i, j):
        if items[i][0] == "bead" and items[j][0] == "bead":
            return radii[i] + radii[j] + gaps[i]
        if items[i][0] != "bead" and items[j][0] != "bead":
            return (nest_distance(clouds[i], 0.0015, +1) + nest_distance(clouds[j], 0.0015, -1)) + gaps[i]
        if items[i][0] != "bead":
            return nest_distance(clouds[i], radii[j], +1) + gaps[i]
        return nest_distance(clouds[j], radii[i], -1) + gaps[i]

    chords = [spacing(i, (i + 1) % N) for i in range(N)]
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    ovality = prod.get("ovality", 0.045)

    def loop_pt(t, k):
        rho = 1 + 0.02 * math.sin(2 * t + ph[0]) + 0.012 * math.sin(3 * t + ph[1]) + 0.006 * math.sin(5 * t + ph[2])
        return Vector((k * (1 + ovality) * rho * math.cos(t), k * (1 - ovality) * rho * math.sin(t), 0))

    def walk(k):
        ts = [0.0]
        for c in chords:
            t0 = ts[-1]; p0 = loop_pt(t0, k)
            lo, hi = t0, t0 + 1.5
            for _ in range(50):
                mid = (lo + hi) / 2
                if (loop_pt(mid, k) - p0).length < c:
                    lo = mid
                else:
                    hi = mid
            ts.append((lo + hi) / 2)
        return ts

    lo, hi = 0.005, 0.5
    for _ in range(70):
        k = (lo + hi) / 2
        if walk(k)[-1] > 2 * math.pi:
            lo = k
        else:
            hi = k
    pts = [loop_pt(t, k) for t in walk(k)[:-1]]

    # which element faces the viewer
    hero = prod.get("front")
    hero_i = N // 2
    if hero:
        cand = [i for i, (kind, name) in enumerate(items) if f"{kind}:{name}" == hero or name == hero]
        hero_i = cand[0] if cand else hero_i
    spin = -math.pi / 2 - math.atan2(pts[hero_i].y, pts[hero_i].x)
    pts = [Matrix.Rotation(spin, 3, 'Z') @ p for p in pts]

    centres, bead_mats = [None] * N, {}
    for i, (kind, name) in enumerate(items):
        if kind != "bead":
            continue
        tangent = (pts[(i + 1) % N] - pts[i - 1]).normalized()
        zc = (tangent + Vector([rng.uniform(-0.06, 0.06) for _ in range(3)])).normalized()
        xc = zc.cross(Vector((0, 0, 1))).normalized()
        xc = Matrix.Rotation(rng.uniform(0, 6.28), 3, zc) @ xc
        yc = zc.cross(xc)
        R3 = Matrix((xc, yc, zc)).transposed()
        sc = [radii[i] * rng.uniform(0.985, 1.015), radii[i] * rng.uniform(0.985, 1.015), radii[i]]
        zmin = math.sqrt(sum((R3[2][c] * sc[c]) ** 2 for c in range(3)))
        centres[i] = Vector((pts[i].x, pts[i].y, zmin))
        bead_mats[i] = Matrix.Translation(centres[i]) @ R3.to_4x4() @ Matrix.Diagonal((*sc, 1))
    for i, (kind, _) in enumerate(items):
        if kind != "bead":
            nb = [centres[j % N] for j in (i - 1, i + 1) if centres[j % N] is not None]
            z = sum(c.z for c in nb) / len(nb) if nb else 0.004
            centres[i] = Vector((pts[i].x, pts[i].y, z))

    for i, (kind, name) in enumerate(items):
        pos = centres[i]
        tangent = (centres[(i + 1) % N] - centres[i - 1]).normalized()
        radial = Vector((tangent.y, -tangent.x, 0)).normalized()
        if kind == "bead":
            o = link(bpy.data.objects.new(f"bead_{i:03d}", rng.choice(bead_meshes[name])))
            o.matrix_basis = bead_mats[i]
            o.parent = root
            continue
        h = holders[i]
        x_ax = radial
        pos = pos - Vector((0, 0, h.get("sag_mm", 0.0) * MM))   # loose holes sag on the cord
        if h.get("faces_out"):
            # a flat charm faces outward (as worn); lying flat it rests tilted up
            # toward the viewer: the smallest tilt that keeps it above the table
            cloud = clouds[i]
            for tdeg in range(10, 90):
                t = math.radians(tdeg)
                if min(pos.z + math.sin(t) * p.x - math.cos(t) * p.y for p in cloud[::5]) > 0.00004:
                    break
            x_ax = radial * math.cos(t) + Vector((0, 0, math.sin(t)))
        z_ax = tangent
        x_ax = (x_ax - z_ax * x_ax.dot(z_ax)).normalized()
        y_ax = z_ax.cross(x_ax)
        h.matrix_basis = Matrix.Translation(pos) @ Matrix((x_ax, y_ax, z_ax)).transposed().to_4x4()
        h.parent = root

    if cord.get("show", True):
        cu = tube_curve("cord", list(centres), cord.get("diameter_mm", 0.9) / 2 * MM, cyclic=True)
        cu.materials.append(mats["cord"])
        c = link(bpy.data.objects.new("cord", cu)); c.parent = root

    # --- info for the studio and camera
    rmax = max(Vector((c.x, c.y)).length for c in centres)
    bead_r = max(r for r in radii if r) if any(radii) else 0.004
    polar = sorted((math.atan2(c.y, c.x), Vector((c.x, c.y)).length) for c in centres)

    def ring_point(ang, z):
        a = math.atan2(math.sin(ang), math.cos(ang))
        pl = polar + [(polar[0][0] + 2 * math.pi, polar[0][1])]
        prev = (pl[-2][0] - 2 * math.pi, pl[-2][1])
        r = pl[0][1]
        for cur in pl:
            if a <= cur[0]:
                t = (a - prev[0]) / max(1e-9, cur[0] - prev[0])
                r = prev[1] + (cur[1] - prev[1]) * t
                break
            prev = cur
        return Vector((r * math.cos(ang), r * math.sin(ang), z))

    angles = [math.atan2(c.y, c.x) for c in centres]
    hero_ang = angles[hero_i]
    # the glide starts past the nearest non-bead part after the hero (or 3 beads on)
    sec = next((j for j in range(hero_i + 1, hero_i + N) if items[j % N][0] != "bead" and j % N != hero_i), None)
    sec_ang = angles[sec % N] if sec is not None and (sec - hero_i) <= N // 3 else hero_ang + math.radians(45)
    while sec_ang < hero_ang:
        sec_ang += 2 * math.pi
    glide_from = sec_ang + math.radians(28)

    def glide_point(t):
        ang = glide_from + (hero_ang - glide_from) * t
        return ring_point(ang, bead_r * 0.9), ang

    print(f"strung: {N} items, loop scale {k * 1000:.1f} mm, extent {rmax * 1000:.1f} mm")
    return {
        "root": root, "extent": rmax + bead_r, "height": 2 * bead_r,
        "center": Vector((0, 0, bead_r * 0.6)),
        "glide_point": glide_point, "hero_angle": hero_ang,
        "front_focus_radius": rmax * 0.55, "focus_z": bead_r, "macro_distance": 4.1,
    }
