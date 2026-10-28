"""Finish a mid-poly mesh for Roblox: apply transforms, shade smooth with sharp
edges by angle, add Weighted Normals, and report what Roblox will reject.

Run:  python finish_mesh.py <scene.blend> <object name> [sharp_angle_degrees=40]
"""
import sys
import math
import bpy
import bmesh  # after bpy: the standalone bpy module provides it

path, name = sys.argv[-2], sys.argv[-1]
angle = 40.0
if name.replace(".", "").isdigit():
    path, name, angle = sys.argv[-3], sys.argv[-2], float(sys.argv[-1])

bpy.ops.wm.open_mainfile(filepath=path)
obj = bpy.data.objects[name]
for o in bpy.context.view_layer.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

mesh = obj.data
for p in mesh.polygons:
    p.use_smooth = True
# Edges sharper than the angle stay hard, so trims and panels keep crisp lines.
bm = bmesh.new()
bm.from_mesh(mesh)
for e in bm.edges:
    if len(e.link_faces) == 2 and e.calc_face_angle() > math.radians(angle):
        e.smooth = False
non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
bm.to_mesh(mesh)
bm.free()

if "WeightedNormal" not in obj.modifiers:
    wn = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
    wn.weight = 50

tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
problems = []
if tris > 20000:
    problems.append(f"{tris} tris is over Roblox's 20,000 per-mesh limit")
if non_manifold:
    problems.append(f"{non_manifold} non-manifold edges (Roblox wants watertight meshes)")
if ngons:
    problems.append(f"{ngons} n-gons (use quads and triangles)")
if not mesh.uv_layers:
    problems.append("no UV map yet")
bpy.ops.wm.save_as_mainfile(filepath=path)
print(f"{name}: {tris} tris, sharp angle {angle} deg")
print("OK" if not problems else "FIX: " + "; ".join(problems))
