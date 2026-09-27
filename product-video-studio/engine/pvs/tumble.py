"""Single tumbled / polished stones: an irregular pebble, never a clean ellipsoid,
resting on its flattest side."""
import bpy, bmesh, math
from mathutils import Vector, Matrix, noise as mnoise
from .util import MM, link


def build(spec, mats, rng):
    prod = spec["product"]
    L, W, H = [d * MM for d in prod.get("size_mm", [30, 22, 16])]
    me = bpy.data.meshes.new("stone")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
    o1 = Vector([rng.uniform(-40, 40) for _ in range(3)])
    o2 = Vector([rng.uniform(-40, 40) for _ in range(3)])
    lump = prod.get("irregularity", 1.0)
    p = 2.0 + 2.5 * prod.get("boxiness", 0.4)   # 2 = pebble, 4.5 = rounded box
    for v in bm.verts:
        d = v.co.normalized()
        d = d / (abs(d.x) ** p + abs(d.y) ** p + abs(d.z) ** p) ** (1 / p)
        r = 1 + lump * (0.09 * mnoise.noise(d * 0.9 + o1) + 0.03 * mnoise.noise(d * 2.2 + o2))
        # tumbling rounds the corners but leaves flattish faces
        f = max(abs(d.x), abs(d.y), abs(d.z))
        r *= 1 - 0.05 * lump * (1 - f)
        # unit-size mesh (the object is scaled to the real size) so stone
        # patterns sit at the same scale as on beads
        v.co = Vector((d.x * r, d.y * r * W / L, d.z * r * H / L))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    me.materials.append(mats["stone:" + prod["material"]])
    stone = link(bpy.data.objects.new("stone", me))
    stone.scale = (L / 2,) * 3
    stone.rotation_euler = (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0, 6.28))
    bpy.context.view_layer.update()
    zmin = min((stone.matrix_world @ v.co).z for v in me.vertices)
    root = link(bpy.data.objects.new("Product", None))
    stone.parent = root
    stone.location.z -= zmin
    bpy.context.view_layer.update()
    ext = max(L, W) / 2 * 1.1
    hz = H * 1.05

    def glide_point(t):
        # across the top of the stone, from a side toward the front
        ang = math.radians(-90 + 70 * (1 - t))
        p = Vector((math.cos(ang) * ext * 0.45, math.sin(ang) * ext * 0.45, hz * 0.8))
        return p, ang

    return {
        "root": root, "extent": ext, "height": hz, "center": Vector((0, 0, hz * 0.45)),
        "glide_point": glide_point, "hero_angle": math.radians(-90),
        "front_focus_radius": ext * 0.5, "focus_z": hz * 0.6, "macro_distance": 6.5,
        # a single small object needs more air around it than a bracelet
        "reveal_distance": 12.0, "hero_pull": 2.0, "turntable_distance": 11.0,
    }
