"""Joint layout of the gaunt humanoid entity, shared by the blockout and the
rig so bones land inside the mesh. Positions are fractions of total height:
(x to the figure's left, y forward, z up); radius is the Skin modifier's
thickness, also a fraction of height. Edit here to change the body type.
"""
STUD = 0.28  # metres per Roblox stud

_LEFT = {
    "shoulder": ((0.11, 0.01, 0.79), 0.035),
    "elbow":    ((0.17, 0.02, 0.58), 0.025),
    "wrist":    ((0.20, 0.03, 0.38), 0.020),
    "finger":   ((0.21, 0.04, 0.28), 0.012),  # hands reaching the knees read as wrong
    "hip":      ((0.06, 0.00, 0.47), 0.045),
    "knee":     ((0.07, -0.01, 0.25), 0.032),
    "ankle":    ((0.075, 0.00, 0.04), 0.024),
    "toe":      ((0.08, 0.06, 0.01), 0.018),
}
JOINTS = {
    "pelvis": ((0, 0.00, 0.50), 0.060),
    "chest":  ((0, 0.01, 0.70), 0.075),
    "neck":   ((0, 0.02, 0.83), 0.030),
    "head":   ((0, 0.03, 0.93), 0.065),
    "crown":  ((0, 0.03, 1.00), 0.0),  # top of the skull, for the Head bone's tail only
}
for side, sign in (("L", 1), ("R", -1)):
    for name, ((x, y, z), r) in _LEFT.items():
        JOINTS[f"{name}_{side}"] = ((sign * x, y, z), r)

# Skin-modifier edges of the blockout (the crown is not part of the mesh).
EDGES = [("pelvis", "chest"), ("chest", "neck"), ("neck", "head")]
for s in ("L", "R"):
    EDGES += [("chest", f"shoulder_{s}"), (f"shoulder_{s}", f"elbow_{s}"), (f"elbow_{s}", f"wrist_{s}"),
              (f"wrist_{s}", f"finger_{s}"), ("pelvis", f"hip_{s}"), (f"hip_{s}", f"knee_{s}"),
              (f"knee_{s}", f"ankle_{s}"), (f"ankle_{s}", f"toe_{s}")]

# Bones: name -> (head joint, tail joint, parent). Root sits at the origin.
BONES = {
    "Hips":  ("pelvis", "chest", "Root"),
    "Chest": ("chest", "neck", "Hips"),
    "Neck":  ("neck", "head", "Chest"),
    "Head":  ("head", "crown", "Neck"),
}
for s in ("L", "R"):
    BONES.update({
        f"Shoulder_{s}": ("chest", f"shoulder_{s}", "Chest"),
        f"UpperArm_{s}": (f"shoulder_{s}", f"elbow_{s}", f"Shoulder_{s}"),
        f"LowerArm_{s}": (f"elbow_{s}", f"wrist_{s}", f"UpperArm_{s}"),
        f"Hand_{s}":     (f"wrist_{s}", f"finger_{s}", f"LowerArm_{s}"),
        f"UpperLeg_{s}": (f"hip_{s}", f"knee_{s}", "Hips"),
        f"LowerLeg_{s}": (f"knee_{s}", f"ankle_{s}", f"UpperLeg_{s}"),
        f"Foot_{s}":     (f"ankle_{s}", f"toe_{s}", f"LowerLeg_{s}"),
    })


def world(joint, height):
    """A joint's position in Blender space (Z up, the figure facing -Y)."""
    (x, y, z), _ = JOINTS[joint]
    return (x * height, -y * height, z * height)
