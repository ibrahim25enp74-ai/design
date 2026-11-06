"""Builds the 3D model of the skylight (rev 2) in Blender.

On your computer:  Blender -> Scripting tab -> Open this file -> Run Script.
Or from a terminal: blender --python blender_skylight.py
Units: metres. X = along the 15 m, Y = across (legs at y=0 and y=6.70), Z = up (0 = top of parapet).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

# ----------------------------------------------------------------- design data (m)
PAR_AX, LEG_OFF = 6.0, 0.35
SPAN = PAR_AX + 2 * LEG_OFF           # 6.70
LENGTH, BAY = 15.0, 1.5
FX = [i * BAY for i in range(11)]
N_CELL = 10
PX = [i * SPAN / N_CELL for i in range(N_CELL + 1)]
MX = [x + BAY / 2 for x in FX[:-1]]          # mid-bay glazing bars -> 0.75 x 0.67 cells
B = 0.08
PH = 0.50                             # house roof below top of parapet
YE, YR, YS = 0.60, 1.10, 0.10         # eave, ridge, sill rail (centre lines)
SLOPE = math.atan((YR - YE) / (SPAN / 2))
COPE_W, COPE_H, BRICK = 0.40, 0.10, 0.24
CX = (PX[4], PX[6])                   # collar tie ends
OVER, SHEET_T = 0.10, 0.016
HOUSE_H = 3.5


def top_y(y):
    return YE + (YR - YE) * (1 - abs(y - SPAN / 2) / (SPAN / 2))


def top_face(y):
    return top_y(y) + B / 2 / math.cos(SLOPE)


# ----------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


def mat(name, rgb, alpha=1.0, rough=0.5, metal=0.0, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if transmission:
        p.inputs["Transmission Weight"].default_value = transmission
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    m.diffuse_color = (*rgb, alpha)
    return m


M = {
    "steel": mat("Steel SHS (painted)", (0.18, 0.2, 0.22), rough=0.45, metal=0.6),
    "pc": mat("Polycarbonate 16mm black smoke", (0.015, 0.016, 0.018), alpha=0.82, rough=0.12, transmission=0.35),
    "alu": mat("Aluminium", (0.75, 0.76, 0.78), rough=0.3, metal=1.0),
    "glass": mat("Window glass black", (0.01, 0.01, 0.012), alpha=0.85, rough=0.05, transmission=0.3),
    "conc": mat("Concrete / plaster", (0.78, 0.75, 0.7), rough=0.9),
    "brick": mat("Brick parapet", (0.72, 0.6, 0.45), rough=0.9),
    "floor": mat("Courtyard tiles", (0.6, 0.57, 0.52), rough=0.8),
    "rod": mat("Bracing rod", (0.35, 0.2, 0.4), rough=0.4, metal=0.7),
}

COLL = {}


def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        COLL[name] = c
    return COLL[name]


def put(obj, collection, material):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll(collection).objects.link(obj)
    obj.data.materials.append(M[material])
    return obj


def box(name, x0, x1, y0, y1, z0, z1, collection, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    bpy.ops.object.transform_apply(scale=True)
    return put(o, collection, material)


def beam(name, p1, p2, w, h, collection, material, roll=0.0):
    """rectangular bar from p1 to p2 (centre line), local Z kept as close to world up as possible"""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(p1 + p2) / 2)
    o = bpy.context.active_object
    o.name = name
    o.scale = (d.length, w, h)
    up = "Z" if abs(d.normalized().z) < 0.99 else "Y"
    q = d.to_track_quat("X", up)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = q
    if roll:
        o.rotation_mode = "XYZ"
        o.rotation_euler.rotate_axis("X", roll)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return put(o, collection, material)


def rod(name, p1, p2, r, collection, material):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, vertices=12, location=(p1 + p2) / 2)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return put(o, collection, material)


# ----------------------------------------------------------------- houses + parapets + courtyard
for i, (y_far, y_face, ax) in enumerate(((-5.0, LEG_OFF + BRICK / 2, LEG_OFF),
                                          (SPAN + 5.0, SPAN - LEG_OFF - BRICK / 2, SPAN - LEG_OFF))):
    n = f"House {i + 1}"
    box(f"{n} - building", -1.5, LENGTH + 1.5, min(y_far, y_face), max(y_far, y_face), -PH - HOUSE_H, -PH,
        "Houses", "conc")
    box(f"{n} - parapet brick", -1.5, LENGTH + 1.5, ax - BRICK / 2, ax + BRICK / 2, -PH, -COPE_H, "Houses", "brick")
    box(f"{n} - parapet coping", -1.5, LENGTH + 1.5, ax - COPE_W / 2, ax + COPE_W / 2, -COPE_H, 0, "Houses", "conc")
box("Courtyard floor", -1.5, LENGTH + 1.5, LEG_OFF, SPAN - LEG_OFF, -PH - HOUSE_H - 0.05, -PH - HOUSE_H,
    "Houses", "floor")

# ----------------------------------------------------------------- frames
for k, x in enumerate(FX):
    n = f"Frame {k + 1:02d}"
    for y in (0.0, SPAN):
        beam(f"{n} leg", (x, y, -PH + 0.012), (x, y, YE + B / 2), B, B, "Steel frames", "steel")
        box(f"{n} base plate", x - 0.1, x + 0.1, y - 0.1, y + 0.1, -PH, -PH + 0.012, "Steel frames", "steel")
    for y0, y1 in ((0.0, SPAN / 2), (SPAN, SPAN / 2)):
        beam(f"{n} rafter", (x, y0, YE), (x, y1, YR), B, B, "Steel frames", "steel")
    beam(f"{n} collar tie", (x, CX[0], top_y(CX[0])), (x, CX[1], top_y(CX[1])), B, B, "Steel frames", "steel")

# ----------------------------------------------------------------- purlins, sills, bracing
for j, y in enumerate(PX):
    roll = 0.0 if abs(y - SPAN / 2) < 1e-6 else (SLOPE if y < SPAN / 2 else -SLOPE)
    beam(f"Purlin {j + 1:02d}", (0, y, top_y(y)), (LENGTH, y, top_y(y)), B, B, "Purlins + rails", "steel", roll)
for k, x in enumerate(MX):
    for j in range(N_CELL):
        y0, y1 = PX[j], PX[j + 1]
        beam(f"Mid-bay bar {k + 1:02d}", (x, y0, top_y(y0)), (x, y1, top_y(y1)), B, B, "Purlins + rails", "steel")
for y in (0.0, SPAN):
    beam(f"Sill rail y={y:.2f}", (0, y, YS), (LENGTH, y, YS), B, B, "Purlins + rails", "steel")
for a, b in ((FX[0], FX[1]), (FX[-2], FX[-1])):
    for y0, y1 in ((0.0, SPAN / 2), (SPAN / 2, SPAN)):
        rod("Bracing rod", (a, y0, top_y(y0)), (b, y1, top_y(y1)), 0.006, "Bracing", "rod")
        rod("Bracing rod", (a, y1, top_y(y1)), (b, y0, top_y(y0)), 0.006, "Bracing", "rod")

# ----------------------------------------------------------------- polycarbonate + ridge cap
n_ = lambda side: Vector((0, -math.sin(SLOPE) * side, math.cos(SLOPE)))
for side, y_e in ((1, 0.0), (-1, SPAN)):
    a = Vector((LENGTH / 2, y_e - side * OVER, top_face(y_e) - OVER * math.tan(SLOPE)))
    b = Vector((LENGTH / 2, SPAN / 2 - side * 0.025, top_face(SPAN / 2 - side * 0.025)))
    off = n_(side) * (SHEET_T / 2 + 0.004)
    beam(f"Polycarbonate {'side A' if side > 0 else 'side B'}", a + off, b + off, LENGTH + 0.08, SHEET_T,
         "Glazing", "pc")
    c0 = Vector((LENGTH / 2, SPAN / 2, top_face(SPAN / 2) + SHEET_T + 0.02))
    beam("Ridge cap", c0, c0 + Vector((0, -side * 0.17, -0.17 * math.tan(SLOPE))), LENGTH + 0.08, 0.003,
         "Glazing", "alu")

# ----------------------------------------------------------------- vent windows (both 15 m sides)
for y, s in ((0.0, -1), (SPAN, 1)):
    yw = y + s * (B / 2 + 0.025)
    for a, b in zip(FX, FX[1:]):
        x0, x1, z0, z1 = a + B / 2, b - B / 2, YS + B / 2, YE - B / 2
        t = 0.04
        for p, q in (((x0, yw, z0 + t / 2), (x1, yw, z0 + t / 2)), ((x0, yw, z1 - t / 2), (x1, yw, z1 - t / 2)),
                     ((x0 + t / 2, yw, z0), (x0 + t / 2, yw, z1)), ((x1 - t / 2, yw, z0), (x1 - t / 2, yw, z1))):
            beam("Window frame", p, q, 0.05, t, "Vent windows", "alu")
        box("Window glass", x0 + t, x1 - t, yw - 0.003, yw + 0.003, z0 + t, z1 - t, "Vent windows", "glass")

# ----------------------------------------------------------------- light, camera, render settings
world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(-35))
scene.collection.objects.link(sun)
# name, camera location, target, focal length (mm)
FLOOR = -PH - HOUSE_H
SHOTS = [
    ("01_aerial", (-6.5, -7.5, 6.0), (LENGTH / 2, SPAN / 2, -0.6), 28),
    ("02_courtyard_looking_up", (1.2, SPAN / 2 - 0.8, FLOOR + 1.6), (LENGTH * 0.75, SPAN / 2 + 0.3, 0.9), 18),
    ("03_rooftop_side_windows", (3.0, -4.5, 1.1), (9.0, 0.0, 0.2), 24),
    ("04_end_view", (-9.0, SPAN / 2, 1.6), (LENGTH / 2, SPAN / 2, -0.3), 35),
    ("05_leg_parapet_closeup", (2.6, -1.3, 0.35), (1.5, 0.15, -0.15), 30),
    ("06_aerial_top", (LENGTH / 2 + 0.01, SPAN / 2 - 9.0, 14.0), (LENGTH / 2, SPAN / 2, 0.0), 30),
]
cams = []
for name, loc, tgt, lens in SHOTS:
    cam = bpy.data.objects.new(f"Cam {name}", bpy.data.cameras.new(f"Cam {name}"))
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    cam.location = loc
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y")
    coll("Cameras").objects.link(cam)
    cams.append((name, cam))
scene.camera = cams[0][1]
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.engine = "CYCLES"
scene.cycles.samples = 40
scene.cycles.use_denoising = True

# ----------------------------------------------------------------- save / export / preview
here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if "--no-save" not in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, "SKYLIGHT_6x15.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(here, "SKYLIGHT_6x15.glb"), export_format="GLB")
if "--render" in sys.argv:
    os.makedirs(os.path.join(here, "renders"), exist_ok=True)
    for name, cam in cams:
        scene.camera = cam
        scene.render.filepath = os.path.join(here, "renders", f"shot_{name}.png")
        bpy.ops.render.render(write_still=True)
    scene.camera = cams[0][1]
