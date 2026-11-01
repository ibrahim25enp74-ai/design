# -*- coding: utf-8 -*-
"""
Blender: create 4 extra facade cameras automatically.

How to use (Blender 2.8+ / 3.x / 4.x):
  1. Open the "Scripting" tab, click "New", paste this file, press "Run Script".
  2. (Optional) Select only the building objects first, so ground planes, trees,
     etc. are ignored when measuring the building. With nothing selected, all
     visible meshes are used (very large flat ground planes are skipped).
  3. The facade direction is taken from the current scene camera (the camera
     you already render the front with). If there is no camera, the front is
     assumed to face -Y (Blender "Front" view). You can force it with FACADE_DIR.

The cameras are placed in a collection named "Facade_Cameras". Running the
script again replaces them. The active scene camera is not changed.
"""

import bpy
import math
from mathutils import Vector

# ---------------- settings ----------------
FACADE_DIR = None      # e.g. Vector((0, -1, 0)); None = auto (from scene camera)
EYE_HEIGHT = 1.6       # human eye level in meters
MARGIN = 1.15          # empty space around the building in the frame
COLLECTION_NAME = "Facade_Cameras"
# ------------------------------------------

scene = bpy.context.scene


def building_objects():
    sel = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    if sel:
        return sel
    objs = []
    for o in scene.objects:
        if o.type != 'MESH' or o.hide_render or not o.visible_get():
            continue
        d = o.dimensions
        if max(d.x, d.y) > 40 and d.z < 0.3:   # skip big ground planes
            continue
        objs.append(o)
    return objs


objs = building_objects()
if not objs:
    raise RuntimeError("No mesh objects found to frame.")

corners = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
zmin = min(p.z for p in corners)
zmax = max(p.z for p in corners)
H = zmax - zmin
rough_center = sum(corners, Vector()) / len(corners)

# ---- facade direction (unit vector from building toward the viewer) ----
if FACADE_DIR is not None:
    d = Vector((FACADE_DIR.x, FACADE_DIR.y, 0))
elif scene.camera is not None:
    d = scene.camera.matrix_world.translation - rough_center
    d.z = 0
else:
    d = Vector((0, -1, 0))
if d.length < 1e-4:
    d = Vector((0, -1, 0))
d.normalize()
r = Vector((-d.y, d.x, 0))     # viewer's right-hand side

# ---- building extents measured along the facade axes ----
rs = [p.dot(r) for p in corners]
ds = [p.dot(d) for p in corners]
W = max(rs) - min(rs)
D = max(ds) - min(ds)
c = r * ((max(rs) + min(rs)) / 2) + d * ((max(ds) + min(ds)) / 2)
c.z = zmin
zc = zmin + H / 2

rx = scene.render.resolution_x * scene.render.pixel_aspect_x
ry = scene.render.resolution_y * scene.render.pixel_aspect_y
SENSOR = 36.0
if rx >= ry:
    half_w, half_h = SENSOR / 2, SENSOR / 2 * ry / rx
else:
    half_w, half_h = SENSOR / 2 * rx / ry, SENSOR / 2


def fit_distance(lens, width, height):
    return max(width / 2 * MARGIN * lens / half_w,
               height / 2 * MARGIN * lens / half_h)


# ---- collection (replace old cameras on re-run) ----
coll = bpy.data.collections.get(COLLECTION_NAME)
if coll is None:
    coll = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(coll)
for o in list(coll.objects):
    data = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if data is not None and data.users == 0:
        bpy.data.cameras.remove(data)


def make_camera(name, angle_deg, lens, height, dist_scale=1.0,
                straight=True, look_at_height=0.5):
    """angle_deg: 0 = straight in front, + = to the right, - = to the left.
    straight=True keeps vertical lines vertical (architectural lens shift)."""
    a = math.radians(angle_deg)
    dirv = d * math.cos(a) + r * math.sin(a)
    wp = W * abs(math.cos(a)) + D * abs(math.sin(a))
    dp = W * abs(math.sin(a)) + D * abs(math.cos(a))
    dist = fit_distance(lens, wp, H) * dist_scale + dp * 0.3

    pos = c + dirv * dist
    pos.z = zmin + height

    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = SENSOR
    cam.sensor_fit = 'AUTO'
    cam.clip_end = max(1000.0, dist * 10)
    obj = bpy.data.objects.new(name, cam)
    coll.objects.link(obj)
    obj.location = pos

    if straight:
        look = Vector((-dirv.x, -dirv.y, 0))
        obj.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
        cam.shift_y = (zc - pos.z) / dist * lens / SENSOR
    else:
        target = c.copy()
        target.z = zmin + H * look_at_height
        obj.rotation_euler = (target - pos).to_track_quat('-Z', 'Y').to_euler()
    return obj


cams = [
    # 3/4 view from the right at eye level (like the reference image)
    make_camera("CAM_01_3Q_Right", 30, 30, EYE_HEIGHT),
    # 3/4 view from the left at eye level
    make_camera("CAM_02_3Q_Left", -30, 30, EYE_HEIGHT),
    # low, close, wide-angle dramatic shot looking up at the facade
    make_camera("CAM_03_Low_Dramatic", 15, 18, 0.4, dist_scale=0.85,
                straight=False, look_at_height=0.6),
    # elevated 3/4 view (shows boundary walls, entrance and roof)
    make_camera("CAM_04_Elevated", -40, 28, H + 4.0, dist_scale=1.1,
                straight=False, look_at_height=0.35),
]

print("Facade cameras created:", [o.name for o in cams])
print("Building size  W=%.2f  D=%.2f  H=%.2f m" % (W, D, H))
