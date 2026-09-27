"""Backdrop, world and lighting. Light rig is scaled to the product size so a
tumble stone, a bracelet and a gem tree all get the same look."""
import bpy, bmesh, math, os, random
from mathutils import Vector, noise as mnoise
from .util import link, smooth
from . import materials as M

REF_EXTENT = 0.0364        # the rig below was tuned on a 10 mm-bead bracelet
LIGHT = 0.04


def _world(strength=0.35):
    world = bpy.data.worlds.new("Studio")
    bpy.context.scene.world = world
    wn = world.node_tree
    for n in list(wn.nodes):
        wn.nodes.remove(n)
    out = wn.nodes.new("ShaderNodeOutputWorld")
    bg = wn.nodes.new("ShaderNodeBackground")
    env = wn.nodes.new("ShaderNodeTexEnvironment")
    hdr = os.path.join(bpy.utils.resource_path('LOCAL'), "datafiles", "studiolights", "world", "studio.exr")
    env.image = bpy.data.images.load(hdr)
    bg.inputs["Strength"].default_value = strength
    wn.links.new(env.outputs["Color"], bg.inputs["Color"])
    wn.links.new(bg.outputs[0], out.inputs["Surface"])


def _area(name, loc, target, size, power, s, size_y=None, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size = size * s
    ld.size_y = (size_y or size) * s
    ld.energy = power * LIGHT * s * s * bpy.context.scene.get("pvs_light", 1.0)
    ld.color = color
    o = link(bpy.data.objects.new(name, ld))
    o.location = Vector(loc) * s
    o.rotation_euler = (Vector(target) * s - o.location).to_track_quat('-Z', 'Y').to_euler()
    return o


VELVET = {   # linear RGB, matched to the shop photo backdrops (velvet reads darker than it looks)
    "royal_blue": (0.006, 0.014, 0.13), "burgundy": (0.10, 0.004, 0.022), "mustard": (0.42, 0.20, 0.015),
    "teal": (0.0, 0.06, 0.08), "emerald": (0.004, 0.055, 0.02), "purple": (0.045, 0.006, 0.11),
    "black": (0.006, 0.006, 0.007), "cream": (0.62, 0.55, 0.42),
}


def _color(c, table):
    return table[c] if isinstance(c, str) else tuple(c)


def _cloth(name, mat, E, rng, fold_amp, rise=True):
    """Draped cloth: flat under the product, folds growing with distance and a
    soft rise behind, like the shop's velvet photos."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    # folds have a physical size (a few cm) whatever the product size;
    # only the flat area under the product scales with it
    Ef = max(E, 0.036)
    n, half = 260, 40 * Ef
    off = [rng.uniform(0, 6.28) for _ in range(6)]
    dirs = [Vector((math.cos(a), math.sin(a), 0)) for a in (rng.uniform(0, 3.14) for _ in range(3))]
    grid = []
    for iy in range(n + 1):
        row = []
        for ix in range(n + 1):
            x = -half + 2 * half * ix / n
            y = -half * 0.8 + 2 * half * iy / n
            p = Vector((x, y, 0))
            r = p.length
            a = fold_amp * Ef * smooth((r - 2.5 * E) / (6 * Ef))
            warp = mnoise.noise(p / (6 * Ef) + Vector((off[0], off[1], 0))) * 2.0
            z = a * (0.6 * math.sin(p.dot(dirs[0]) / (2.2 * Ef) + warp + off[2])
                     + 0.3 * math.sin(p.dot(dirs[1]) / (1.3 * Ef) + warp * 0.7 + off[3])
                     + 0.25 * mnoise.noise(p / (3 * Ef)))
            if rise:
                z += 14 * Ef * smooth((y - 3 * E - 4 * Ef) / (18 * Ef)) ** 2
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for iy in range(n):
        for ix in range(n):
            f = bm.faces.new((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))
            f.smooth = True
    bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    return link(bpy.data.objects.new(name, me))


def build(spec, info, rng):
    look = spec.get("look", {})
    E = info["extent"]
    s = E / REF_EXTENT
    bpy.context.scene["pvs_light"] = look.get("light", 1.0)
    backdrop = look.get("backdrop", "studio_white")
    if backdrop == "studio_white":
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=4.0 * max(1, s), fill_type='NGON')
        fl = bpy.context.active_object; fl.name = "floor"
        fl.data.materials.append(M.studio_white_material())
    elif backdrop == "velvet":
        _cloth("velvet", M.velvet_material(_color(look.get("backdrop_color", "royal_blue"), VELVET)), E, rng,
               look.get("folds", 1.6))
    elif backdrop == "linen":
        _cloth("linen", M.linen_material(_color(look.get("backdrop_color", (0.78, 0.72, 0.62)), VELVET)), E, rng,
               look.get("folds", 0.9))
    else:
        raise ValueError(f"unknown backdrop {backdrop}")
    _world(look.get("world_strength", 0.35))
    # big overhead softbox, key front-left, rim strip back-right, small sparkle spot
    _area("top_softbox", (0.0, 0.05, 0.75), (0, 0, 0), 0.9, 260, s)
    _area("key", (-0.35, -0.35, 0.32), (0, 0, 0.005), 0.30, 55, s, color=(1.0, 0.97, 0.93))
    _area("rim_strip", (0.30, 0.38, 0.16), (0, 0, 0.005), 0.08, 30, s, size_y=0.45)
    sp = bpy.data.lights.new("sparkle", 'SPOT')
    sp.energy = 6 * LIGHT * s * s * look.get("light", 1.0)
    sp.shadow_soft_size = 0.004 * s
    sp.spot_size = math.radians(25); sp.spot_blend = 0.6
    spo = link(bpy.data.objects.new("sparkle", sp)); spo.location = Vector((0.12, -0.25, 0.22)) * s
    spo.rotation_euler = (Vector((0, 0, 0.005)) * s - spo.location).to_track_quat('-Z', 'Y').to_euler()
