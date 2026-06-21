#!/usr/bin/env python3
"""PyClaw Logo 3D - Generated via cli-anything-blender + SVG import"""
import bpy
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(SCRIPT_DIR, "logo.svg")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "pyclaw_logo_cli.png")

# ── Clear Default Scene ──
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ── Scene Settings ──
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.fps = 24

# ── Render Settings (from CLI) ──
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.cycles.samples = 128
scene.cycles.use_denoising = True

# ── World Settings (from CLI) ──
world = bpy.data.worlds.get('World')
if world is None:
    world = bpy.data.worlds.new('World')
    scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get('Background')
if bg_node:
    bg_node.inputs[0].default_value = (0.02, 0.02, 0.04, 1.0)

# ── Materials (from CLI) ──
mat_blue = bpy.data.materials.new(name='PythonBlue')
mat_blue.use_nodes = True
bsdf = mat_blue.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.216, 0.463, 0.671, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.3
    bsdf.inputs['Roughness'].default_value = 0.35

mat_yellow = bpy.data.materials.new(name='PythonYellow')
mat_yellow.use_nodes = True
bsdf = mat_yellow.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (1.0, 0.831, 0.231, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.25
    bsdf.inputs['Roughness'].default_value = 0.3

mat_base = bpy.data.materials.new(name='BaseMaterial')
mat_base.use_nodes = True
bsdf = mat_base.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.08, 0.08, 0.12, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.2

mat_eye = bpy.data.materials.new(name='EyeBlack')
mat_eye.use_nodes = True
bsdf = mat_eye.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.15

mat_pupil = bpy.data.materials.new(name='PupilBlue')
mat_pupil.use_nodes = True
bsdf = mat_pupil.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.45, 0.82, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.6
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Emission Strength'].default_value = 0.3

# ── Import SVG ──
SVG_PATH = os.path.join(SCRIPT_DIR, "logo.svg")
if os.path.exists(SVG_PATH):
    bpy.ops.import_curve.svg(filepath=SVG_PATH)
else:
    raise FileNotFoundError(f"SVG not found: {SVG_PATH}")

curve_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'CURVE']
print(f"Imported {len(curve_objs)} curves")

# ── Scale up ──
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

    # Convert to mesh
    bpy.ops.object.convert(target='MESH')

    # Extrude
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, EXT_DEPTH)}
    )
    bpy.ops.object.mode_set(mode='OBJECT')

    # Bevel
    mod_bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    mod_bevel.width = BEVEL_RADIUS
    mod_bevel.segments = 4
    mod_bevel.limit_method = 'ANGLE'
    mod_bevel.angle_limit = math.radians(45)

    # Subdivision
    mod_subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    mod_subsurf.levels = 1
    mod_subsurf.render_levels = 2

    # Assign color
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

# ── Base Plate (from CLI) ──
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, -EXT_DEPTH - 2.0))
base = bpy.context.active_object
base.name = 'BasePlate'
base.scale = (80.0, 80.0, 4.0)
base.data.materials.append(mat_base)

# ── Cameras (from CLI) ──
cam_data = bpy.data.cameras.new(name='MainCam')
cam_data.type = 'PERSP'
cam_data.lens = 50.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new('MainCam', cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (55.0, -60.0, 40.0)
cam_obj.rotation_euler = (math.radians(62.0), math.radians(-3.0), math.radians(42.0))
scene.camera = cam_obj

# ── Lights (from CLI) ──
def add_light(name, type_, location, energy, color, size):
    light_data = bpy.data.lights.new(name=name, type=type_)
    light_data.energy = energy
    light_data.color = color
    light_data.size = size
    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = location
    return light_obj

add_light('KeyLight', 'AREA', (40, -40, 50), 800, (1.0, 0.95, 0.85), 30)
add_light('FillLight', 'AREA', (-35, 30, 30), 400, (0.8, 0.85, 1.0), 25)
add_light('RimLight', 'AREA', (0, 50, 20), 300, (0.216, 0.463, 0.671), 20)

# ── Render Output ──
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = OUTPUT_PATH
scene.frame_set(1)

print(f"Rendering to {OUTPUT_PATH}...")
bpy.ops.render.render(write_still=True)
print('Render complete!')
