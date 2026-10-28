"""Blockout of the Wretch: a gaunt, scaly, long-armed stalker with a forward-
thrust reptile head, open fanged jaw, hanging tongue, dorsal ridge, clawed
hands and feet, and a torn hip wrap.

The body is clay-like metaballs (ellipsoids for ribcage, pelvis, skull;
chains of balls for limbs), voxel-remeshed into one even surface and reduced to
a mid-poly budget. Claws, teeth, ridge spikes and eyes are placed by casting
rays onto that surface, so they sit on it rather than near it.

Run:  python build_blockout.py <out.blend> [height_in_studs=9]
"""
import os
import sys
import math
import random
import bpy
from mathutils import Vector

SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.claude/skills/roblox-horror-art/scripts")
sys.path.insert(0, os.path.normpath(SKILL))
from proportions import STUD  # noqa: E402

out = next(a for a in sys.argv if a.endswith(".blend"))
H = (float(sys.argv[-1]) if sys.argv[-1].replace(".", "").isdigit() else 9) * STUD
TRIS = 9000          # body budget after reduction (claws, teeth, wrap come on top)
VOXEL = 0.0022 * H   # fine enough to keep fingers (about 0.005 H thick)
BALL = 0.575         # a metaball's surface sits at 0.575 x its radius (threshold 0.6, stiffness 2)
random.seed(7)


def W(x, f, z):
    """Fractions of height (x to its left, forward, up) to Blender space: Z up, facing -Y."""
    return Vector((x * H, -f * H, z * H))


# ---------- Skeleton: joint positions as fractions of height ----------
P = {
    "pelvis": (0, 0.000, 0.500), "waist": (0, 0.006, 0.565), "ribs": (0, 0.010, 0.650),
    "chest": (0, 0.012, 0.720), "neck_base": (0, 0.020, 0.772), "neck_mid": (0, 0.050, 0.818),
    "skull": (0, 0.078, 0.872), "brow": (0, 0.114, 0.872), "snout": (0, 0.158, 0.846),
    "jaw_root": (0, 0.090, 0.842), "jaw_mid": (0, 0.118, 0.800), "jaw_tip": (0, 0.138, 0.772),
    "tongue_root": (0, 0.100, 0.830), "tongue_a": (0, 0.132, 0.782),
    "tongue_b": (0, 0.144, 0.722), "tongue_tip": (0, 0.138, 0.668),
}
for side, s in (("L", 1), ("R", -1)):
    P.update({
        f"shoulder_{side}": (s * 0.074, 0.000, 0.752), f"elbow_{side}": (s * 0.104, 0.000, 0.548),
        f"wrist_{side}": (s * 0.120, 0.010, 0.396), f"palm_{side}": (s * 0.125, 0.013, 0.360),
        f"thumb_a_{side}": (s * 0.113, 0.028, 0.350), f"thumb_b_{side}": (s * 0.106, 0.042, 0.322),
        f"hip_{side}": (s * 0.044, 0.000, 0.478), f"knee_{side}": (s * 0.052, 0.026, 0.330),
        f"ankle_{side}": (s * 0.058, -0.016, 0.078), f"ball_{side}": (s * 0.060, 0.042, 0.026),
    })
    for i, dx in enumerate((-0.013, 0.0, 0.013)):
        P[f"f{i}a_{side}"] = (s * (0.125 + dx), 0.015, 0.343)
        P[f"f{i}b_{side}"] = (s * (0.127 + dx * 1.3), 0.021, 0.305)
        P[f"f{i}c_{side}"] = (s * (0.129 + dx * 1.5), 0.029, 0.273)
    for i, dx in enumerate((-0.026, 0.0, 0.026)):
        P[f"toe{i}_{side}"] = (s * (0.060 + dx * 1.2), 0.112 - abs(dx), 0.013)

# ---------- Scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30
for name in ("REF", "HIGH", "LOW", "RIG", "EXPORT"):
    scene.collection.children.link(bpy.data.collections.new(name))
low = bpy.data.collections["LOW"]


def material(name, color, rough=0.6, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = 8
    m.diffuse_color = (*color, 1)
    return m


SKIN = material("Skin", (0.075, 0.10, 0.045), 0.55)
FLESH = material("Flesh", (0.32, 0.05, 0.045), 0.25)
BONE = material("Bone", (0.55, 0.50, 0.38), 0.4)
CLOTH = material("Cloth", (0.11, 0.09, 0.07), 0.9)
EYE = material("Eye", (0.8, 0.05, 0.02), 0.2, emit=(1.0, 0.08, 0.02))

# ---------- Body volume: metaballs ----------
mb = bpy.data.metaballs.new("WretchClay")
mb.resolution = mb.render_resolution = VOXEL * 0.8
clay = bpy.data.objects.new("WretchClay", mb)
scene.collection.objects.link(clay)


def ball(at, r, size=(1, 1, 1), rot=None):
    """A blob whose surface reaches `r` (fraction of height), stretched by `size`."""
    e = mb.elements.new(type="ELLIPSOID" if size != (1, 1, 1) else "BALL")
    e.co = at
    e.radius = r * H / BALL
    if size != (1, 1, 1):
        e.size_x, e.size_y, e.size_z = size
    if rot is not None:
        e.rotation = rot
    return e


def limb(a, b, ra, rb, bulge=0.0):
    """Balls along a segment, radius `ra` to `rb`; `bulge` swells the middle (muscle)."""
    pa, pb = W(*P[a]) if isinstance(a, str) else a, W(*P[b]) if isinstance(b, str) else b
    length = (pb - pa).length / H
    n = max(2, math.ceil(length / (min(ra, rb) * 0.55)))
    for i in range(n + 1):
        t = i / n
        ball(pa.lerp(pb, t), ra + (rb - ra) * t + bulge * math.sin(math.pi * t))


def heading(a, b):
    """Rotation turning an ellipsoid's +X axis along the segment a -> b."""
    return Vector((1, 0, 0)).rotation_difference((W(*P[b]) - W(*P[a])).normalized())


# Torso: a narrow waist between a deep ribcage and a bony pelvis; the shoulder
# blades push the upper back out into a hunch.
ball(W(0, 0.000, 0.505), 0.045, (1.00, 1.00, 0.95))                     # pelvis
ball(W(0, 0.006, 0.565), 0.034, (1.0, 0.95, 1.4))                       # waist
ball(W(0, 0.004, 0.648), 0.054, (1.00, 1.02, 1.25))                     # lower ribs
ball(W(0, -0.008, 0.712), 0.052, (1.08, 1.00, 0.95))                    # upper ribs: pushed back, the hunch
for s in (1, -1):
    ball(W(s * 0.030, -0.040, 0.728), 0.022, (1.1, 0.55, 1.3))          # shoulder blades, flat
    ball(W(s * 0.060, 0.010, 0.750), 0.019)                             # shoulder caps
    ball(W(s * 0.018, -0.014, 0.776), 0.017, (1.0, 1.0, 1.3))           # neck muscles into the hunch
limb("neck_base", "neck_mid", 0.028, 0.023)
limb("neck_mid", "skull", 0.023, 0.024)
# Head: long skull tapering into the upper jaw; lower jaw hangs open.
ball(W(*P["skull"]), 0.042, (1.30, 1.20, 0.95), heading("skull", "snout"))
limb("brow", "snout", 0.034, 0.019)
limb("skull", "brow", 0.040, 0.034)
for s in (1, -1):  # cheekbones widen the face seen from the front
    ball(W(s * 0.020, 0.105, 0.862), 0.020)
limb("jaw_root", "jaw_mid", 0.023, 0.018)
limb("jaw_mid", "jaw_tip", 0.018, 0.012)
# Gullet: flesh closing the back of the open mouth, so it reads dark red, not hollow.
GULLET = [W(0, 0.100, 0.838), W(0, 0.112, 0.825)]
for g in GULLET:
    ball(g, 0.018, (1.0, 1.3, 1.0))
limb("tongue_root", "tongue_a", 0.0075, 0.007)
limb("tongue_a", "tongue_b", 0.007, 0.006)
limb("tongue_b", "tongue_tip", 0.006, 0.003)
for side in ("L", "R"):
    limb(f"shoulder_{side}", f"elbow_{side}", 0.015, 0.011, bulge=0.003)
    ball(W(*P[f"elbow_{side}"]) + Vector((0, 0.006 * H, 0)), 0.013)       # elbow knob
    limb(f"elbow_{side}", f"wrist_{side}", 0.012, 0.009, bulge=0.003)
    limb(f"wrist_{side}", f"palm_{side}", 0.012, 0.015)
    for i in range(3):
        limb(f"palm_{side}", f"f{i}a_{side}", 0.012, 0.0065)
        limb(f"f{i}a_{side}", f"f{i}b_{side}", 0.0065, 0.0055)
        limb(f"f{i}b_{side}", f"f{i}c_{side}", 0.0055, 0.0045)
    limb(f"palm_{side}", f"thumb_a_{side}", 0.011, 0.0058)
    limb(f"thumb_a_{side}", f"thumb_b_{side}", 0.0058, 0.0045)
    limb(f"hip_{side}", f"knee_{side}", 0.026, 0.020, bulge=0.003)
    ball(W(*P[f"knee_{side}"]) + Vector((0, -0.008 * H, 0)), 0.022)       # kneecap
    limb(f"knee_{side}", f"ankle_{side}", 0.021, 0.013, bulge=0.006)   # calf
    limb(f"ankle_{side}", f"ball_{side}", 0.016, 0.021)
    for i in range(3):
        limb(f"ball_{side}", f"toe{i}_{side}", 0.016, 0.0095)

# Metaballs -> mesh -> voxel remesh (one closed, even surface) -> reduce.
dg = bpy.context.evaluated_depsgraph_get()
body_mesh = bpy.data.meshes.new_from_object(clay.evaluated_get(dg))
body = bpy.data.objects.new("LOW_Wretch", body_mesh)
low.objects.link(body)
bpy.data.objects.remove(clay)
bpy.context.view_layer.objects.active = body
body.select_set(True)
body.data.remesh_voxel_size = VOXEL
bpy.ops.object.voxel_remesh()
dec = body.modifiers.new("Decimate", "DECIMATE")
dec.ratio = min(1.0, TRIS / max(1, sum(len(p.vertices) - 2 for p in body.data.polygons)))
bpy.ops.object.modifier_apply(modifier="Decimate")
body.data.materials.append(SKIN)
body.data.materials.append(FLESH)
tongue = [W(*P[n]) for n in ("tongue_root", "tongue_a", "tongue_b", "tongue_tip")] + GULLET
for poly in body.data.polygons:
    if min((poly.center - p).length for p in tongue) < 0.016 * H:
        poly.material_index = 1


def hit(origin, direction):
    """Where a ray from `origin` (Blender space) first meets the body, with its normal."""
    ok, loc, normal, _ = body.ray_cast(origin, direction.normalized())
    return (loc, normal) if ok else (None, None)


parts = []


def spike(name, base, tip, radius, mat, verts=6):
    d = tip - base
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=0, depth=d.length,
                                    location=(base + tip) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    low.objects.link(o)
    parts.append(o)


# Claws: grow from just inside each finger and toe tip, curving down.
for side in ("L", "R"):
    tips = [(f"f{i}c_{side}", f"f{i}b_{side}", 0.032, 0.0042) for i in range(3)]
    tips += [(f"thumb_b_{side}", f"thumb_a_{side}", 0.022, 0.0040)]
    tips += [(f"toe{i}_{side}", f"ball_{side}", 0.036, 0.0075) for i in range(3)]
    for tip, prev, length, r in tips:
        a, b = W(*P[prev]), W(*P[tip])
        d = (b - a).normalized()
        base = b - d * r * H * 0.5
        spike(f"Claw_{tip}", base, base + d * length * H + Vector((0, 0, -0.35 * length * H)), r * H, BONE)

# Teeth: rays from inside the open mouth up to the upper jaw and down to the lower one.
for side in (1, -1):
    for i in range(7):
        t = 0.1 + i * 0.13
        inside = W(*P["jaw_root"]).lerp(W(*P["snout"]), t) + Vector((side * 0.012 * H * (1 - 0.5 * t), 0, -0.025 * H))
        loc, _ = hit(inside, Vector((0, 0, 1)))
        if loc is not None:
            spike(f"ToothU{i}_{side}", loc + Vector((0, 0, 0.004 * H)), loc + Vector((0, -0.004 * H, -(0.030 - 0.01 * t) * H)), 0.0035 * H, BONE, 5)
    for i in range(6):
        t = 0.15 + i * 0.14
        inside = W(*P["jaw_root"]).lerp(W(*P["jaw_tip"]), t) + Vector((side * 0.010 * H * (1 - 0.4 * t), 0, 0.03 * H))
        loc, _ = hit(inside, Vector((0, 0, -1)))
        if loc is not None:
            spike(f"ToothL{i}_{side}", loc - Vector((0, 0, 0.004 * H)), loc + Vector((0, -0.005 * H, (0.024 - 0.006 * t) * H)), 0.003 * H, BONE, 5)

# Dorsal ridge: rays find the surface along the top of the head and down the back.
for k in range(15):
    if k < 4:  # over the skull and neck: cast down onto the top
        loc, normal = hit(W(0, 0.110 - k * 0.022, 1.05), Vector((0, 0, -1)))
    else:      # down the spine: cast forward from behind (+Y is behind)
        loc, normal = hit(W(0, -0.3, 0.835 - (k - 4) * 0.025), Vector((0, -1, 0)))
    if loc is None:
        continue
    size = (0.017 if k < 7 else 0.017 - (k - 7) * 0.0013) * H
    spike(f"Ridge{k}", loc - normal * size * 0.3, loc + (normal + Vector((0, 0.5, 0.35))).normalized() * size, size * 0.42, SKIN, 5)

# Eyes: small, sunk into the sides of the brow.
for side in (1, -1):
    loc, normal = hit(W(side * 0.08, 0.30, 0.880), Vector((-side * 0.28, 1, 0)))
    if loc is None:
        continue
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.0062 * H, location=loc - normal * 0.003 * H)
    eye = bpy.context.object
    eye.name = f"Eye_{'L' if side > 0 else 'R'}"
    eye.data.materials.append(EYE)
    for c in eye.users_collection:
        c.objects.unlink(eye)
    low.objects.link(eye)
    parts.append(eye)

# Hip wrap: a band plus a ragged skirt, longer at the back, given thickness.
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=1, depth=1, end_fill_type="NOTHING")
wrap = bpy.context.object
wrap.name = "Wrap"
for v in wrap.data.vertices:
    ang = math.atan2(v.co.y, v.co.x)
    top = v.co.z > 0
    # Long rags at front and back, short at the hips' sides, torn unevenly.
    z = 0.565 if top else 0.385 + 0.065 * abs(math.cos(ang)) + random.uniform(-0.035, 0.02)
    flare = 1.0 if top else 1.06
    v.co.x *= 0.056 * flare * H
    v.co.y *= 0.052 * flare * H
    v.co.z = z * H
wrap.data.materials.append(CLOTH)
wrap.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.004 * H
bpy.context.view_layer.objects.active = wrap
bpy.ops.object.modifier_apply(modifier="Solidify")
for c in wrap.users_collection:
    c.objects.unlink(wrap)
low.objects.link(wrap)
parts.append(wrap)

# One object: the creature is a single skinned mesh.
for o in bpy.context.view_layer.objects:
    o.select_set(o in parts or o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
bpy.ops.object.shade_smooth()
body["entity_height"] = H
body["joints"] = {k: list(W(*v)) for k, v in P.items()}  # for the rig script

tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=out)
print(f"LOW_Wretch blockout: {len(body.data.vertices)} verts, {tris} tris, {H:.2f} m ({H / STUD:.1f} studs), "
      f"{len(parts)} attached parts")
