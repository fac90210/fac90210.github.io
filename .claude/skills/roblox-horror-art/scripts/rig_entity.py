"""Rig a single-mesh entity for Roblox skinning: build the armature from
proportions.py, bind with automatic weights, then clean the weights to Roblox's
rules (at most 4 influences per vertex, normalised, nothing on the root).

Run:  python rig_entity.py <scene.blend> [mesh name=LOW_Entity]
Adds armature "RIG_Entity" (Root bone at the origin) and saves the file.
"""
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proportions import BONES, world  # noqa: E402

MAX_INFLUENCES = 4
path = next(a for a in sys.argv if a.endswith(".blend"))
name = sys.argv[-1] if not sys.argv[-1].endswith(".blend") else "LOW_Entity"

bpy.ops.wm.open_mainfile(filepath=path)
mesh_obj = bpy.data.objects[name]
height = mesh_obj.get("entity_height") or mesh_obj.dimensions.z

arm_data = bpy.data.armatures.new("RIG_Entity")
arm = bpy.data.objects.new("RIG_Entity", arm_data)
bpy.data.collections["RIG"].objects.link(arm)
bpy.context.view_layer.objects.active = arm
for o in bpy.context.view_layer.objects:
    o.select_set(o == arm)

bpy.ops.object.mode_set(mode="EDIT")
root = arm_data.edit_bones.new("Root")
root.head, root.tail = (0, 0, 0), (0, 0, height * 0.1)
for bone_name, (head, tail, parent) in BONES.items():
    b = arm_data.edit_bones.new(bone_name)
    b.head, b.tail = world(head, height), world(tail, height)
    b.roll = 0
    b.parent = arm_data.edit_bones[parent]
    # Chain bones connect so they rotate cleanly; shoulders/legs start off-centre.
    b.use_connect = parent != "Root" and tuple(b.head) == tuple(arm_data.edit_bones[parent].tail)
bpy.ops.object.mode_set(mode="OBJECT")

# Bind: mesh parented to the armature with automatic (heat) weights.
for o in bpy.context.view_layer.objects:
    o.select_set(o in (mesh_obj, arm))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")

# Roblox: no influence on the root, at most 4 per vertex, weights summing to 1.
groups = mesh_obj.vertex_groups
if "Root" in groups:
    groups.remove(groups["Root"])
index_name = {g.index: g.name for g in groups}
trimmed = unweighted = 0
for v in mesh_obj.data.vertices:
    ws = sorted(((g.weight, g.group) for g in v.groups if g.weight > 0), reverse=True)
    for _, gi in ws[MAX_INFLUENCES:]:
        groups[index_name[gi]].remove([v.index])
        trimmed += 1
    keep = ws[:MAX_INFLUENCES]
    total = sum(w for w, _ in keep)
    if total == 0:
        unweighted += 1
        continue
    for w, gi in keep:
        groups[index_name[gi]].add([v.index], w / total, "REPLACE")

bpy.ops.wm.save_as_mainfile(filepath=path)
print(f"RIG_Entity: {len(arm_data.bones)} bones; trimmed {trimmed} extra influences; "
      f"{unweighted} vertices with no weight" + (" (FIX: weight-paint them)" if unweighted else ""))
