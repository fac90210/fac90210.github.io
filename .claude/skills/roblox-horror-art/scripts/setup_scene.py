"""Start a new Roblox asset scene: metric units, the standard collections, and a
4-stud reference cube to check scale against after the first import.

Run:  python setup_scene.py <out.blend>        (python with the bpy module)
  or  blender -b -P setup_scene.py -- <out.blend>
"""
import sys
import bpy

STUD = 0.28  # metres per Roblox stud
COLLECTIONS = ["REF", "HIGH", "LOW", "RIG", "EXPORT"]

out = sys.argv[-1] if sys.argv[-1].endswith(".blend") else None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.fps = 30  # Roblox's Animation Editor works at 30 fps by default

for name in COLLECTIONS:
    scene.collection.children.link(bpy.data.collections.new(name))

# A 4x4x4-stud cube standing on the ground: import it once with the asset and
# compare it to a 4x4x4 Part in Studio to confirm the scale settings.
bpy.ops.mesh.primitive_cube_add(size=4 * STUD, location=(0, 0, 2 * STUD))
ref = bpy.context.object
ref.name = "REF_4StudCube"
for c in ref.users_collection:
    c.objects.unlink(ref)
bpy.data.collections["REF"].objects.link(ref)
ref.display_type = "WIRE"
ref.hide_render = True

if out:
    bpy.ops.wm.save_as_mainfile(filepath=out)
print("scene ready", out or "(not saved)")
