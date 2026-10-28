"""Key a heavy, rhythmic stalking walk on RIG_Entity: long planted steps, a
spine that sags on each footfall, and a head that stays locked forward and
lags the body. Pure FK rotations, so it is a template to time and tweak.

Run:  python anim_stalk_cycle.py <scene.blend> [frames_per_step=24]
Creates action "Stalk" (two steps, loops) and saves the file.
"""
import sys
import math
import bpy
from bpy_extras.anim_utils import action_get_channelbag_for_slot

path = next(a for a in sys.argv if a.endswith(".blend"))
step = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 24  # 30 fps: 0.8 s a step reads heavy

bpy.ops.wm.open_mainfile(filepath=path)
arm = bpy.data.objects["RIG_Entity"]
arm.animation_data_create()
action = bpy.data.actions.new("Stalk")
action.use_fake_user = True
arm.animation_data.action = action
cycle = step * 2
bpy.context.scene.frame_start, bpy.context.scene.frame_end = 0, cycle


def key(bone, frame, x=0.0, y=0.0, z=0.0):
    """Keys a bone's rotation in degrees about its own X (bend), Y (twist), Z (side)."""
    pb = arm.pose.bones[bone]
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
    pb.keyframe_insert("rotation_euler", frame=frame)


for f in range(0, cycle + 1, step // 4):
    t = (f % cycle) / cycle * 2 * math.pi          # one full cycle = two steps
    swing = math.sin(t)
    for side, phase in (("L", 0.0), ("R", math.pi)):
        s = math.sin(t + phase)
        lift = max(0.0, math.sin(t + phase - math.pi / 2))  # knee only bends while the leg swings
        key(f"UpperLeg_{side}", f, x=-28 * s)
        key(f"LowerLeg_{side}", f, x=55 * lift)
        key(f"Foot_{side}", f, x=-15 * lift)
        # Arms hang and drag: small, late counter-swing.
        key(f"UpperArm_{side}", f, x=10 * math.sin(t + phase + math.pi + 0.6), z=-4)
        key(f"LowerArm_{side}", f, x=-8 - 6 * lift)
    sag = abs(math.cos(t))                           # 1 at each footfall
    key("Hips", f, y=6 * swing, x=4 * sag)
    key("Chest", f, x=8 + 6 * sag, y=-5 * swing)    # hunched, dipping on impact
    key("Neck", f, x=-10 - 6 * sag, y=3 * swing)    # neck fights the hunch
    key("Head", f, x=-6 * sag, y=2 * swing)         # head stays level: the eerie part

# Blender 4.4+ keeps an action's curves per slot, in a channelbag.
fcurves = action_get_channelbag_for_slot(action, arm.animation_data.action_slot).fcurves
for fc in fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "BEZIER"
    fc.modifiers.new("CYCLES")  # loops seamlessly in Blender; Roblox loops via Animation.Looped

bpy.ops.wm.save_as_mainfile(filepath=path)
print(f"Stalk: {cycle} frames ({cycle / 30:.2f} s at 30 fps), {len(fcurves)} curves")
