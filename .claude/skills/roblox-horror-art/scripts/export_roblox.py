"""Check an asset against Roblox's import rules, then export it as FBX with
Roblox's recommended Blender settings. Exports the LOW and RIG collections.

Run:  python export_roblox.py <scene.blend> <out.fbx> [action name] [--with-ref]
With an action name, that one animation is baked in (Roblox takes one
animation per FBX: export each clip to its own file). --with-ref also exports
REF_4StudCube, for the one-time scale check in Studio.
Exits non-zero, exporting nothing, when a rule is broken.
"""
import sys
import bpy

blend = next(a for a in sys.argv if a.endswith(".blend"))
out = next(a for a in sys.argv if a.endswith(".fbx"))
with_ref = "--with-ref" in sys.argv
after = sys.argv[sys.argv.index(out) + 1:]
action_name = next((a for a in after if not a.startswith("--")), None)

bpy.ops.wm.open_mainfile(filepath=blend)
collections = ("LOW", "RIG", "REF") if with_ref else ("LOW", "RIG")
objects = [o for c in collections if c in bpy.data.collections for o in bpy.data.collections[c].all_objects]
problems = []
for o in objects:
    if any(abs(s - 1) > 1e-4 for s in o.scale) or any(abs(r) > 1e-4 for r in o.rotation_euler):
        problems.append(f"{o.name}: apply rotation and scale (Ctrl+A)")
    if o.type == "MESH":
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        if tris > 20000:
            problems.append(f"{o.name}: {tris} tris is over the 20,000 per-mesh limit")
        over = sum(1 for v in o.data.vertices if sum(1 for g in v.groups if g.weight > 0) > 4)
        if over:
            problems.append(f"{o.name}: {over} vertices with more than 4 bone influences")
        if "Root" in o.vertex_groups:
            problems.append(f"{o.name}: the Root bone must not influence the mesh")
    if o.type == "ARMATURE":
        root = o.data.bones.get("Root")
        if root is None or root.parent is not None:
            problems.append(f"{o.name}: needs a parentless bone named Root")
        elif root.head_local.length > 1e-4:
            problems.append(f"{o.name}: Root bone must sit at 0, 0, 0")

if action_name:
    arm = next((o for o in objects if o.type == "ARMATURE"), None)
    action = bpy.data.actions.get(action_name)
    if not arm or not action:
        problems.append(f"no armature or no action named {action_name}")
    else:
        arm.animation_data_create()
        arm.animation_data.action = action
        if action.slots and arm.animation_data.action_slot is None:
            arm.animation_data.action_slot = action.slots[0]  # Blender 4.4+ layered actions
        start, end = (int(v) for v in action.frame_range)
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = start, end

if problems:
    print("NOT EXPORTED:\n  " + "\n  ".join(problems))
    sys.exit(1)

for o in bpy.context.view_layer.objects:
    o.select_set(o in objects)
bpy.ops.export_scene.fbx(
    filepath=out,
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    apply_scale_options="FBX_SCALE_UNITS",   # Roblox's documented setting
    path_mode="COPY", embed_textures=True,    # textures travel inside the FBX
    add_leaf_bones=False,                     # Roblox: leaf bones off
    use_armature_deform_only=True,
    bake_anim=bool(action_name),              # Roblox: bake only for animation exports
    bake_anim_use_all_actions=False,
    bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,            # keep every key: twitches live in single frames
    mesh_smooth_type="FACE",
)
print(f"exported {out}" + (f" with animation {action_name}" if action_name else ""))
