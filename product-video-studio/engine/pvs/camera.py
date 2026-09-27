"""Camera moves, expressed in units of the product's extent E so they work for
any product size. Timing is expressed as fractions of the clip."""
import bpy, math
from mathutils import Vector, noise as mnoise
from .util import link, smooth, lerp

ASPECTS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}


def _rig():
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.sensor_width = 36
    cam_data.clip_start = 0.002
    cam_data.clip_end = 50
    cam = link(bpy.data.objects.new("Camera", cam_data))
    bpy.context.scene.camera = cam
    aim = link(bpy.data.objects.new("aim", None))
    focus = link(bpy.data.objects.new("focus", None))
    tr = cam.constraints.new('TRACK_TO')
    tr.target = aim; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    cam_data.dof.use_dof = True
    cam_data.dof.focus_object = focus
    cam_data.dof.aperture_blades = 7
    return cam, cam_data, aim, focus


def _sph(c, az, el, d):
    return c + d * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))


def fit_factor(spec):
    w, h = ASPECTS[spec.get("output", {}).get("aspect", "16:9")]
    f = max(1.0, (16 / 9) / (w / h)) ** 0.8
    return f / spec.get("output", {}).get("zoom", 1.0)


def turntable(spec, info, frames):
    cam, cd, aim, focus = _rig()
    E, c = info["extent"], info["center"]
    k = fit_factor(spec)
    cam.location = _sph(c, math.radians(-90), math.radians(spec.get("turntable", {}).get("elevation_deg", 31)),
                        info.get("turntable_distance", 7.8) * E * k)
    cd.lens = 85
    aim.location = c + Vector((0, 0, -0.03 * E))
    focus.location = Vector((0, -info["front_focus_radius"] * 0.64, info["focus_z"]))
    cd.dof.aperture_fstop = 32
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
    root = info["root"]
    root.rotation_euler = (0, 0, 0); root.keyframe_insert("rotation_euler", frame=0)
    root.rotation_euler = (0, 0, 2 * math.pi); root.keyframe_insert("rotation_euler", frame=frames)


def ad(spec, info, frames):
    """One continuous move: close glide along the product to the hero detail,
    pull back and rise to reveal it all, slow eased orbit to front-on, with a
    touch of handheld drift."""
    cam, cd, aim, focus = _rig()
    E, c = info["extent"], info["center"]
    k = fit_factor(spec)
    F = frames - 1
    rad = math.radians
    for f in range(frames):
        x = f / F
        slide = smooth(x / 0.467)
        gp, gang = info["glide_point"](slide)
        rev = smooth((x - 0.289) / 0.511)
        drift = -rad(0.05) * min(f, 0.622 * F) * (450 / frames)
        hero = smooth((x - 0.622) / 0.376)
        az = gang + rad(30) + drift + rad(19) * rev - rad(35) * hero
        el = lerp(rad(12), rad(35), rev)
        d = (lerp(info.get("macro_distance", 4.1) * E, info.get("reveal_distance", 8.2) * E, rev)
             - info.get("hero_pull", 1.5) * E * hero) * lerp(1.0, k, rev)
        tgt = gp.lerp(c, rev)
        shake = Vector([mnoise.noise(Vector((f * 0.018 * 450 / frames, 7.3 * i, 1.1))) for i in range(3)])
        cam.location = _sph(tgt, az, el, d) + shake * d * 0.0035
        aim.location = tgt + Vector([mnoise.noise(Vector((f * 0.012 * 450 / frames, 3.1 * i, 9.4))) for i in range(3)]) * d * 0.0015
        horiz = Vector((cam.location.x, cam.location.y, 0)).normalized()
        front = horiz * info["front_focus_radius"] + Vector((0, 0, info["focus_z"]))
        focus.location = gp.lerp(front, rev)
        cd.lens = lerp(100, 85, rev)
        cd.dof.aperture_fstop = lerp(10.0, 30.0, smooth((x - 0.333) / 0.444))
        for o in (cam, aim, focus):
            o.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
        cd.dof.keyframe_insert("aperture_fstop", frame=f)
