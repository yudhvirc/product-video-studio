"""Shared helpers: scene linking, node-building shorthands and mesh generators.
Everything is built at real-world scale in metres."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise as mnoise

MM = 0.001


def scene():
    return bpy.context.scene


def link(obj):
    scene().collection.objects.link(obj)
    return obj


def new_mat(name):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def rgba(c):
    c = list(c)
    return tuple(c + [1.0]) if len(c) == 3 else tuple(c)


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (x * 6 - 15) + 10)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- meshes
def sphere_mesh(name, radius, segs=24, rings=12, scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=radius)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    return me


def revolve_mesh(name, profile, segs=144, wave=None):
    """Lathe a closed (r, z) profile around Z. wave(r, z, phi) -> (r, z) for scallops."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for s in range(segs):
        phi = 2 * math.pi * s / segs
        ring = []
        for r, z in profile:
            if wave:
                r, z = wave(r, z, phi)
            ring.append(bm.verts.new((r * math.cos(phi), r * math.sin(phi), z)))
        rings.append(ring)
    m = len(profile)
    for s in range(segs):
        a, b = rings[s], rings[(s + 1) % segs]
        for k in range(m):
            f = bm.faces.new((a[k], b[k], b[(k + 1) % m], a[(k + 1) % m]))
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return me


def tube_curve(name, pts, radius, cyclic=False, radii=None):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for k, (p, c) in enumerate(zip(sp.points, pts)):
        p.co = (c[0], c[1], c[2], 1)
        if radii:
            p.radius = radii[k]
    sp.use_cyclic_u = cyclic
    sp.use_smooth = True
    return cu


def chaton_mesh(name):
    """Pointed-back rhinestone: table + crown in glass (material 0), pavilion
    silvered (material 1) like a foil-backed crystal. Girdle radius 1, facing +Z."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    n = 8
    table = [bm.verts.new((0.55 * math.cos(2 * math.pi * i / n + math.pi / n),
                           0.55 * math.sin(2 * math.pi * i / n + math.pi / n), 0.42)) for i in range(n)]
    gird = [bm.verts.new((math.cos(2 * math.pi * i / (2 * n)),
                          math.sin(2 * math.pi * i / (2 * n)), 0.0)) for i in range(2 * n)]
    culet = bm.verts.new((0, 0, -0.95))
    bm.faces.new(table)
    for i in range(n):
        t0, t1 = table[i], table[(i + 1) % n]
        g0, g1, g2 = gird[2 * i + 1], gird[(2 * i + 2) % (2 * n)], gird[(2 * i + 3) % (2 * n)]
        bm.faces.new((t0, g0, g1)); bm.faces.new((t0, g1, t1)); bm.faces.new((t1, g1, g2))
    for i in range(2 * n):
        f = bm.faces.new((gird[(i + 1) % (2 * n)], gird[i], culet))
        f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return me


def bead_mesh(name, seed, hole=0.1, segs=96, rings=46, lumpiness=1.0, facets=0):
    """Hand-polished round bead of radius 1: slightly lumpy and out of round,
    drilled along Z with a hole whose rim is a little chipped.
    facets > 0 gives a faceted-cut bead (flat-shaded, that many facets around)."""
    rnd = random.Random(seed)
    o1, o2, o3 = (Vector([rnd.uniform(-50, 50) for _ in range(3)]) for _ in range(3))
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    th0 = math.asin(hole * 1.25)
    if facets:
        segs, rings = facets, max(4, facets // 2)
    grid = []
    for i in range(rings + 1):
        th = th0 + (math.pi - 2 * th0) * i / rings
        row = []
        for j in range(segs):
            ph = 2 * math.pi * j / segs + (math.pi / segs if facets and i % 2 else 0)
            d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
            r = 1 + lumpiness * (0.007 * mnoise.noise(d * 1.3 + o1) + 0.0025 * mnoise.noise(d * 4.0 + o2))
            if i in (0, rings):   # chipped drill-hole rim
                r *= 1 - 0.03 * max(0.0, mnoise.noise(d * 9.0 + o3))
            row.append(bm.verts.new(d * r))
        grid.append(row)
    zc = math.cos(th0)
    for z, rad in ((zc - 0.04, hole), (0.0, hole * 1.05), (-(zc - 0.04), hole)):
        grid.append([bm.verts.new((rad * math.cos(2 * math.pi * j / segs),
                                   rad * math.sin(2 * math.pi * j / segs), z)) for j in range(segs)])
    order = list(range(rings + 1)) + [rings + 3, rings + 2, rings + 1]
    for a, b in zip(order, order[1:] + order[:1]):
        A, B = grid[a], grid[b]
        for j in range(segs):
            f = bm.faces.new((A[j], A[(j + 1) % segs], B[(j + 1) % segs], B[j]))
            f.smooth = not facets
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return me


def assembly_points(holder):
    """Holder-local vertex cloud of an assembly (evaluated, so curves count)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for c in holder.children:
        ev = c.evaluated_get(dg)
        me = ev.to_mesh()
        mw = c.matrix_local
        pts += [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return pts


def nest_distance(pts, rb, direction):
    """Centre distance along local Z for a sphere of radius rb resting against the part."""
    best = 0.0
    for p in pts:
        rho2 = p.x * p.x + p.y * p.y
        if rho2 < rb * rb:
            best = max(best, direction * p.z + math.sqrt(rb * rb - rho2))
    return best
