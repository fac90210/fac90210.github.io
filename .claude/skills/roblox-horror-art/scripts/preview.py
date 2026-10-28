"""Render a contact sheet so Claude can check an asset by eye: one row of
frames from an action (or a 4-angle turntable without one), CPU Cycles, no GPU.

Run:  python preview.py <scene.blend> <out.png> [action name] [frames=6]
"""
import os
import sys
import math
import bpy

blend = next(a for a in sys.argv if a.endswith(".blend"))
out = os.path.abspath(next(a for a in sys.argv if a.endswith(".png")))
rest = [a for a in sys.argv[sys.argv.index(out if out in sys.argv else next(a for a in sys.argv if a.endswith(".png"))) + 1:]]
action_name = next((a for a in rest if not a.isdigit()), None)
count = int(next((a for a in rest if a.isdigit()), 6))

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
for c in ("REF",):
    if c in bpy.data.collections:
        bpy.data.collections[c].hide_render = True
meshes = [o for o in scene.objects if o.type == "MESH" and not o.hide_render]
arm = next((o for o in scene.objects if o.type == "ARMATURE"), None)
height = max(o.dimensions.z for o in meshes)

bpy.ops.object.camera_add()
cam = scene.camera = bpy.context.object
cam.data.lens = 50
target = bpy.data.objects.new("PreviewTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, height * 0.5)
cam.constraints.new("TRACK_TO").target = target
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(35)))
bpy.context.object.data.energy = 3.5
world = bpy.data.worlds.new("Preview")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.055, 0.065, 1)
scene.world = world
bpy.ops.mesh.primitive_plane_add(size=height * 6)

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.render.resolution_x, scene.render.resolution_y = 360, 480
frames, angles = [], []
if action_name and arm:
    action = bpy.data.actions[action_name]
    arm.animation_data_create()
    arm.animation_data.action = action
    if action.slots and arm.animation_data.action_slot is None:
        arm.animation_data.action_slot = action.slots[0]
    start, end = action.frame_range
    frames = [round(start + (end - start) * i / count) for i in range(count)]
    angles = [90] * count  # side view shows a walk best
else:
    frames = [scene.frame_current] * 4
    angles = [0, 45, 90, 180]

tiles = []
for i, (f, a) in enumerate(zip(frames, angles)):
    scene.frame_set(f)
    r = height * 2.6
    cam.location = (r * math.sin(math.radians(a)), -r * math.cos(math.radians(a)), height * 0.55)
    path = f"{out[:-4]}_{i}.png"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    tiles.append(path)

# Stitch the tiles left to right into one image.
imgs = [bpy.data.images.load(p) for p in tiles]
w, h = imgs[0].size
sheet = bpy.data.images.new("sheet", w * len(imgs), h)
pixels = [0.0] * (w * len(imgs) * h * 4)
for i, img in enumerate(imgs):
    src = list(img.pixels)
    for y in range(h):
        row = src[y * w * 4:(y + 1) * w * 4]
        start = (y * w * len(imgs) + i * w) * 4
        pixels[start:start + w * 4] = row
sheet.pixels = pixels
sheet.filepath_raw = out
sheet.file_format = "PNG"
sheet.save()
for p in tiles:
    os.remove(p)
print("preview", out, "frames" if action_name else "angles", frames if action_name else angles)
