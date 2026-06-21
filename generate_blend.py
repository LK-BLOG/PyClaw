#!/usr/bin/env python3
"""Generate pyclaw-logo.blend from CLI project + SVG import"""
import bpy
import math
import os

SCRIPT_DIR = "/home/claw/.openclaw/workspace/pyclaw"
SVG_PATH = os.path.join(SCRIPT_DIR, "logo.svg")
BLEND_PATH = os.path.join(SCRIPT_DIR, "pyclaw_logo.blend")

# ── Clear Default Scene ──
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ── Scene Settings ──
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.fps = 24

# ── Render Settings ──
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.cycles.samples = 128
scene.cycles.use_denoising = True

# ── World ──
world = bpy.data.worlds.get('World')
if world is None:
    world = bpy.data.worlds.new('World')
    scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get('Background')
if bg_node:
    bg_node.inputs[0].default_value = (0.02, 0.02, 0.04, 1.0)

# ── Materials ──
def make_mat(name, base_color, metallic, roughness, emission=None, emission_strength=0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = base_color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if emission:
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat

mat_blue = make_mat("PythonBlue", (0.216, 0.463, 0.671, 1.0), 0.3, 0.35)
mat_yellow = make_mat("PythonYellow", (1.0, 0.831, 0.231, 1.0), 0.25, 0.3)
mat_base = make_mat("BaseMaterial", (0.08, 0.08, 0.12, 1.0), 0.9, 0.2)
mat_eye = make_mat("EyeBlack", (0.05, 0.05, 0.05, 1.0), 0.8, 0.15)
mat_pupil = make_mat("PupilBlue", (0.45, 0.82, 1.0, 1.0), 0.6, 0.1,
                      emission=(0.45, 0.82, 1.0, 1.0), emission_strength=0.3)

# ── Import SVG ──
bpy.ops.import_curve.svg(filepath=SVG_PATH)
curve_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'CURVE']
print(f"Imported {len(curve_objs)} curves")

# ── Scale & extrude ──
SCALE = 2000.0
EXT_DEPTH = 12.0
BEVEL_RADIUS = 0.8

for obj in curve_objs:
    obj.scale = (SCALE, SCALE, SCALE)
bpy.context.view_layer.update()

sorted_objs = sorted(curve_objs, key=lambda o: o.name)
fully_blue = ["Curve", "Curve.002", "Curve.004"]
fully_yellow = ["Curve.001", "Curve.003", "Curve.005"]

for obj in sorted_objs:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, EXT_DEPTH)}
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='BEVEL')
    obj.modifiers["Bevel"].width = BEVEL_RADIUS
    obj.modifiers["Bevel"].segments = 4
    obj.modifiers["Bevel"].limit_method = 'ANGLE'
    obj.modifiers["Bevel"].angle_limit = math.radians(45)
    bpy.ops.object.modifier_add(type='SUBSURF')
    obj.modifiers["Subdivision"].levels = 1
    obj.modifiers["Subdivision"].render_levels = 2
    name = obj.name
    if name in fully_blue:
        obj.data.materials.append(mat_blue.copy())
    elif name in fully_yellow:
        obj.data.materials.append(mat_yellow.copy())
    elif "Pupil" in name:
        obj.data.materials.append(mat_pupil.copy())
    elif "Eye" in name:
        obj.data.materials.append(mat_eye.copy())
    obj.select_set(False)

# ── Base Plate ──
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, -EXT_DEPTH - 2.0))
base = bpy.context.active_object
base.name = 'BasePlate'
base.scale = (80.0, 80.0, 4.0)
base.data.materials.append(mat_base)

# ── Cameras ──
cam_data = bpy.data.cameras.new(name='MainCam')
cam_data.type = 'PERSP'
cam_data.lens = 50.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new('MainCam', cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (55.0, -60.0, 40.0)
cam_obj.rotation_euler = (math.radians(62.0), math.radians(-3.0), math.radians(42.0))
scene.camera = cam_obj

# ── Lights ──
for name, type_, loc, energy, color, size in [
    ('KeyLight', 'AREA', (40, -40, 50), 800, (1.0, 0.95, 0.85), 30),
    ('FillLight', 'AREA', (-35, 30, 30), 400, (0.8, 0.85, 1.0), 25),
    ('RimLight', 'AREA', (0, 50, 20), 300, (0.216, 0.463, 0.671), 20),
]:
    ld = bpy.data.lights.new(name=name, type=type_)
    ld.energy = energy
    ld.color = color
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc

# ── Save .blend ──
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(f"Saved .blend to {BLEND_PATH}")
