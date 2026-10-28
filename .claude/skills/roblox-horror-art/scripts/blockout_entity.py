"""Block out a tall, gaunt humanoid entity as one connected base mesh, using a
Skin modifier over a vertex skeleton. It is a starting silhouette to sculpt and
retopologise from, not a finished model.

Run:  python blockout_entity.py <scene.blend> [height_in_studs=9]
Adds object "LOW_Entity" to the LOW collection and saves the file.
"""
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proportions import EDGES, JOINTS, STUD, world  # noqa: E402

args = [a for a in sys.argv if a.endswith(".blend") or a.replace(".", "").isdigit()]
path = next(a for a in args if a.endswith(".blend"))
height = float(next((a for a in args if not a.endswith(".blend")), 9)) * STUD

bpy.ops.wm.open_mainfile(filepath=path)
h = height
names = [n for n in JOINTS if n != "crown"]
mesh = bpy.data.meshes.new("LOW_Entity")
mesh.from_pydata([world(n, h) for n in names], [(names.index(a), names.index(b)) for a, b in EDGES], [])
obj = bpy.data.objects.new("LOW_Entity", mesh)
bpy.data.collections["LOW"].objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
obj["entity_height"] = h  # read by rig_entity.py

skin = obj.modifiers.new("Skin", "SKIN")
skin.use_smooth_shade = True
for v, n in zip(mesh.skin_vertices[0].data, names):
    r = JOINTS[n][1] * h
    v.radius = (r, r)
mesh.skin_vertices[0].data[names.index("pelvis")].use_root = True
obj.modifiers.new("Subdivision", "SUBSURF").levels = 1
for m in list(obj.modifiers):
    bpy.ops.object.modifier_apply(modifier=m.name)

tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=path)
print(f"LOW_Entity: {len(obj.data.vertices)} verts, {tris} tris, height {height:.2f} m ({height / STUD:.1f} studs)")
