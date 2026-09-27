"""Face-on render of every photo-relief charm in a built scene, for a side-by-side
check against the reference photo.

  blender -b <scene.blend> --python charm_check.py -- <out_dir>
Writes <out_dir>/charm_<name>.png (thread runs vertically, like the photo)."""
import bpy, sys, os
from mathutils import Vector, Matrix

out_dir = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
cam = sc.camera
for o in (cam, cam.data):
    o.animation_data_clear()
for n in ("aim", "focus"):
    bpy.data.objects[n].animation_data_clear()
cam.constraints.clear()
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 900, 900, 100
sc.render.use_motion_blur = False
for h in [o for o in bpy.data.objects if o.type == 'EMPTY' and o.name.startswith("charm_")]:
    bpy.context.view_layer.update()
    M = h.matrix_world
    front = (M.to_3x3() @ Vector((1, 0, 0))).normalized()
    up = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    c = M.translation
    cam.location = c + front * 0.05
    cam.rotation_mode = 'QUATERNION'
    # camera looks straight at the face, rolled so the thread is vertical in frame
    zc = (cam.location - c).normalized()
    yc = (up - zc * up.dot(zc)).normalized()
    xc = yc.cross(zc)
    cam.rotation_quaternion = Matrix((xc, yc, zc)).transposed().to_quaternion()
    cam.data.lens = 100
    cam.data.dof.use_dof = False
    sc.frame_set(0)
    sc.render.filepath = os.path.join(out_dir, f"{h.name}.png")
    bpy.ops.render.render(write_still=True)
    print("CHARM_CHECK", sc.render.filepath)
