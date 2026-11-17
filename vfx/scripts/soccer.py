"""Soccer cutscene with the R6 rig: kick-ups, freestyle, slow-motion volley, galactic VFX.

Usage: python3 soccer.py RIG_BLEND OUT_DIR [--scale 1.0] [--spp 32] [--frames a:b:step]
                         [--cam shot|side|front] [--save file.blend] [--fast]
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from PIL import Image

from common import Nodes, new_material
from soccer_motion import (ATT_IN, ATT_OUT, FPS, R_BALL, T_C, T_END, Motion, TimeWarp, smooth)

ap = argparse.ArgumentParser()
ap.add_argument("rig")
ap.add_argument("out")
ap.add_argument("--scale", type=float, default=1.0)
ap.add_argument("--spp", type=int, default=32)
ap.add_argument("--frames", default="")
ap.add_argument("--cam", default="shot")
ap.add_argument("--save", default="")
ap.add_argument("--fast", action="store_true", help="no motion blur or depth of field")
args = ap.parse_args()

motion = Motion()
warp = TimeWarp()
N_FRAMES = int(math.ceil(warp.total * FPS))
S_IN = warp.s_of_t(ATT_IN)       # screen time: foot meets ball
S_REL = warp.s_of_t(ATT_OUT)     # screen time: ball leaves foot
FX_END = S_REL + 2.1
KICK = motion.kick_dir
P_C = motion.contact_point
P_R = motion.release_point
print(f"FRAMES {N_FRAMES}  contact frame {S_IN * FPS + 1:.1f}  release frame {S_REL * FPS + 1:.1f}  "
      f"fx end frame {FX_END * FPS + 1:.1f}  kick dir {tuple(round(v, 2) for v in KICK)}  "
      f"contact {tuple(round(v, 2) for v in P_C)}", flush=True)

# ================================================================ scene setup
bpy.ops.wm.open_mainfile(filepath=args.rig, use_scripts=False)
scene = bpy.context.scene
for obj in [o for o in scene.objects if o.type in {"CAMERA", "LIGHT"}]:
    bpy.data.objects.remove(obj)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.spp
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.05
scene.cycles.use_denoising = True
scene.cycles.denoising_prefilter = "FAST"
scene.cycles.max_bounces = 3
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 2
scene.cycles.transparent_max_bounces = 24
scene.cycles.volume_bounces = 0
scene.cycles.volume_biased = True
scene.cycles.volume_step_rate = 2.5
scene.cycles.volume_max_steps = 256
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.resolution_x = int(1280 * args.scale)
scene.render.resolution_y = int(536 * args.scale)
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = N_FRAMES
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.use_motion_blur = not args.fast
scene.render.motion_blur_shutter = 0.5
scene.render.motion_blur_position = "START"


def collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


COL_ENV = collection("COL_Environment")
COL_FX = collection("COL_FX_Volley")
COL_CAM = collection("COL_Cameras")

PALETTE = {
    "indigo": (0.05, 0.02, 0.30), "violet": (0.38, 0.08, 1.00), "magenta": (1.00, 0.12, 0.75),
    "pink": (1.00, 0.45, 0.85), "cyan": (0.10, 0.85, 1.00), "teal": (0.00, 0.55, 0.75),
    "white": (0.95, 0.97, 1.00), "gold": (1.00, 0.75, 0.30),
}
PAL_ARRAY = np.array([PALETTE[k] for k in ("violet", "magenta", "pink", "cyan", "cyan", "teal", "white", "gold", "indigo")])

# ---------------------------------------------------------------- the dummy
arm = bpy.data.objects["__Rig_Armature"]
mat, n, out = new_material("MAT_Dummy")
bsdf = n.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (0.50, 0.51, 0.53, 1)
bsdf.inputs["Roughness"].default_value = 0.42
n.link(bsdf.outputs[0], out.inputs["Surface"])
for obj in scene.objects:
    if obj.type == "MESH":
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            poly.use_smooth = obj.name == "Head"

# ---------------------------------------------------------------- the ball
def ball_texture(path, width=1024, height=512):
    phi = (1 + 5 ** 0.5) / 2
    verts = []
    for a in (-1, 1):
        for b in (-phi, phi):
            verts += [(0, a, b), (a, b, 0), (b, 0, a)]
    verts = np.array(verts, float)
    verts /= np.linalg.norm(verts, axis=1)[:, None]
    faces = []
    for i in range(12):
        for j in range(i + 1, 12):
            for k in range(j + 1, 12):
                if all(verts[x] @ verts[y] > 0.4 for x, y in ((i, j), (j, k), (i, k))):
                    c = verts[i] + verts[j] + verts[k]
                    faces.append(c / np.linalg.norm(c))
    centers = np.vstack([verts, np.array(faces)])            # 12 pentagons, 20 hexagons
    reach = np.array([2.327] * 12 + [2.267] * 20)
    v, u = np.mgrid[0:height, 0:width]
    lon = (u + 0.5) / width * 2 * np.pi
    lat = (0.5 - (v + 0.5) / height) * np.pi
    p = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    score = (p @ centers.T) / reach
    order = np.sort(score, -1)
    best = np.argmax(score, -1)
    img = np.where((best < 12)[..., None], np.array([0.035, 0.035, 0.04]), np.array([0.92, 0.92, 0.90]))
    seam = (order[..., -1] - order[..., -2]) < 0.0035
    img = np.where(seam[..., None], np.array([0.10, 0.10, 0.11]), img)
    Image.fromarray((img ** (1 / 2.2) * 255).astype(np.uint8)).save(path)


os.makedirs(args.out, exist_ok=True)
BALL_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "roblox", "soccer", "ball_texture.png")
os.makedirs(os.path.dirname(BALL_PNG), exist_ok=True)
ball_texture(BALL_PNG)

bpy.ops.mesh.primitive_uv_sphere_add(radius=R_BALL, segments=40, ring_count=20)
ball = bpy.context.active_object
ball.name = "SM_Ball"
bpy.ops.object.shade_smooth()
mat, n, out = new_material("MAT_Ball")
bsdf = n.new("ShaderNodeBsdfPrincipled")
tex = n.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(os.path.abspath(BALL_PNG))
n.link(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.35
bsdf.inputs["Emission Color"].default_value = (0.45, 0.9, 1.0, 1)
bsdf.inputs["Emission Strength"].default_value = 0.0
BALL_BSDF = bsdf
n.link(bsdf.outputs[0], out.inputs["Surface"])
ball.data.materials.append(mat)
ball_rig = bpy.data.objects.new("EMPTY_BallSquash", None)
scene.collection.objects.link(ball_rig)
ball.parent = ball_rig
ball.rotation_mode = ball_rig.rotation_mode = "QUATERNION"

# ---------------------------------------------------------------- pitch, sky, lights
bpy.ops.mesh.primitive_plane_add(size=600)
ground = bpy.context.active_object
ground.name = "SM_Pitch"
mat, n, out = new_material("MAT_Pitch")
coords = n.new("ShaderNodeTexCoord").outputs["Object"]
sep = n.new("ShaderNodeSeparateXYZ")
n.link(coords, sep.inputs[0])
x, y = sep.outputs["X"], sep.outputs["Y"]
stripe = n.math("GREATER_THAN", n.math("PINGPONG", n.math("ADD", y, 4.5), 9.0), 4.5)
radius = n.vmath("LENGTH", coords)
circle = n.map_range(n.math("ABSOLUTE", n.math("SUBTRACT", radius, 14.0)), 0.16, 0.22, 1.0, 0.0)
halfway = n.map_range(n.math("ABSOLUTE", y), 0.16, 0.22, 1.0, 0.0)
spot = n.map_range(radius, 0.42, 0.50, 1.0, 0.0)
lines = n.math("MAXIMUM", n.math("MAXIMUM", circle, halfway), spot)
blades = n.noise(coords, 9.0, detail=3.0, dims="3D").outputs["Fac"]
grass = n.new("ShaderNodeMix")
grass.data_type = "RGBA"
n.link(stripe, grass.inputs[0])
grass.inputs[6].default_value = (0.012, 0.050, 0.020, 1)
grass.inputs[7].default_value = (0.018, 0.072, 0.026, 1)
shade = n.new("ShaderNodeMix")
shade.data_type = "RGBA"
shade.blend_type = "MULTIPLY"
shade.inputs[0].default_value = 1.0
n.link(grass.outputs[2], shade.inputs[6])
n.link(n.map_range(blades, 0.3, 0.7, 0.6, 1.3), shade.inputs[7])
paint = n.new("ShaderNodeMix")
paint.data_type = "RGBA"
n.link(lines, paint.inputs[0])
n.link(shade.outputs[2], paint.inputs[6])
paint.inputs[7].default_value = (0.55, 0.57, 0.55, 1)
bsdf = n.new("ShaderNodeBsdfPrincipled")
n.link(paint.outputs[2], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
bsdf.inputs["Specular IOR Level"].default_value = 0.12
n.link(bsdf.outputs[0], out.inputs["Surface"])
ground.data.materials.append(mat)

world = bpy.data.worlds.new("World")
world.use_nodes = True
scene.world = world
wn = Nodes(world.node_tree)
bg = world.node_tree.nodes["Background"]
view = wn.new("ShaderNodeTexCoord").outputs["Generated"]
wsep = wn.new("ShaderNodeSeparateXYZ")
wn.link(view, wsep.inputs[0])
sky = wn.ramp(wn.map_range(wsep.outputs["Z"], -0.05, 0.9), [
    (0.0, (0.014, 0.020, 0.055, 1)), (0.25, (0.006, 0.008, 0.030, 1)), (1.0, (0.001, 0.0015, 0.008, 1))])
star_noise = wn.noise(view, 260.0, detail=0.0, dims="3D").outputs["Fac"]
stars = wn.math("MULTIPLY", wn.map_range(star_noise, 0.80, 0.815, 0.0, 1.2),
                wn.map_range(wsep.outputs["Z"], 0.02, 0.25))
sky_sum = wn.vmath("ADD", sky.outputs["Color"], wn.vmath("SCALE", (0.8, 0.85, 1.0), scale=stars))
wn.link(sky_sum, bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

for name, direction, energy, color in (
        ("LGT_Key", (-0.45, -0.55, 0.70), 2.3, (1.0, 0.93, 0.84)),
        ("LGT_Rim", (0.60, 0.65, 0.45), 1.9, (0.45, 0.62, 1.0)),
        ("LGT_Fill", (0.75, -0.50, 0.45), 0.3, (0.75, 0.80, 1.0))):
    data = bpy.data.lights.new(name, "SUN")
    data.energy = energy
    data.color = color
    data.angle = math.radians(2.0)
    light = bpy.data.objects.new(name, data)
    COL_ENV.objects.link(light)
    light.rotation_euler = Vector(direction).to_track_quat("Z", "Y").to_euler()

# Far floodlights: bright cards that give the background some depth.
mat, n, out = new_material("MAT_Floodlight")
emit = n.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (0.9, 0.95, 1.0, 1)
emit.inputs["Strength"].default_value = 40.0
n.link(emit.outputs[0], out.inputs["Surface"])
flood_mesh = bpy.data.meshes.new("SM_Floodlight")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
bm.to_mesh(flood_mesh)
bm.free()
flood_mesh.materials.append(mat)
for i in range(10):
    ang = math.radians(18 + i * 36)
    for row in range(2):
        for cell in range(-2, 3):
            lamp = bpy.data.objects.new(f"SM_Floodlight_{i}_{row}_{cell}", flood_mesh)
            COL_ENV.objects.link(lamp)
            dist = 150.0
            side = Vector((-math.sin(ang), math.cos(ang), 0))
            lamp.location = Vector((math.cos(ang) * dist, math.sin(ang) * dist, 34 + row * 2.6)) + side * cell * 2.6
            lamp.rotation_euler = (math.radians(90), 0, ang + math.radians(90))
            lamp.scale = (1.0, 1.0, 1.0)
            lamp.visible_diffuse = lamp.visible_glossy = lamp.visible_shadow = False

# ================================================================ camera
cam_data = bpy.data.cameras.new("CAM_Cutscene")
cam = bpy.data.objects.new("CAM_Cutscene", cam_data)
COL_CAM.objects.link(cam)
cam.rotation_mode = "QUATERNION"
scene.camera = cam
cam_data.sensor_width = 36.0
cam_data.dof.use_dof = not args.fast


def lerp(a, b, u):
    return a + (b - a) * u


def orbit(center, angle_deg, radius, height):
    a = math.radians(angle_deg)
    return Vector((center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius, height))


def torso_center(t):
    return motion.pose(t)["Torso"] @ Vector((0, 0, 3.0))


def soft_ball(t, window=0.25):
    """Ball position, smoothed so the camera does not shake at each touch."""
    total = Vector()
    for k in range(-3, 4):
        total += motion.ball(max(0.0, t + k * window / 6))
    return total / 7


S_E0 = warp.s_of_t(T_C - 0.30)       # cut to the slow-motion close-up
S_F0 = S_REL + 0.14                  # cut to the wide reverse angle
S_TOTAL = warp.total


def camera_state(s):
    """Returns position, target, lens (mm), f-stop for screen time s."""
    t = warp.t_of_s(s)
    if args.cam == "side":
        c = torso_center(t)
        return Vector((30, c.y + 1, 4.5)), Vector((0, c.y + 1, 4.5)), 24, 16
    if args.cam == "front":
        return Vector((0.5, 30, 4.5)), Vector((0.5, 0, 4.5)), 24, 16
    if s < 1.95:                                              # A: low dolly, ball in the foreground
        u = smooth(s / 1.95)
        pos = Vector((3.6, 9.0, 0.45)).lerp(Vector((2.5, 7.2, 0.8)), u)
        return pos, Vector((0.3, 0.5, 2.5)), 18, 4.0
    if s < 5.62:                                              # B: orbit around the kick-ups
        u = (s - 1.95) / (5.62 - 1.95)
        pos = orbit((0, 0), lerp(62, 148, smooth(u)), lerp(16.5, 14.0, u), lerp(2.6, 4.2, u))
        target = torso_center(t).lerp(soft_ball(t), 0.25)
        target.z = max(target.z + 0.4, 3.5)
        return pos, target, 30, 5.6
    if s < 9.18:                                              # C: low and close for the freestyle
        u = (s - 5.62) / (9.18 - 5.62)
        pos = orbit((0, 0), lerp(40, -18, smooth(u)), lerp(13.5, 11.5, u), lerp(1.0, 2.2, u))
        target = torso_center(t).lerp(soft_ball(t, 0.4), 0.28)
        target.z = max(target.z, 3.1)
        return pos, target, 26, 4.0
    if s < S_E0:                                              # D: from behind, tilt up with the lob
        u = (s - 9.18) / (S_E0 - 9.18)
        pos = Vector((-6.5, -12.5, 0.45)).lerp(Vector((-5.0, -10.5, 1.3)), smooth(u))
        target = torso_center(t).lerp(soft_ball(t, 0.12), 0.5)
        return pos, target, 23, 5.6
    if s < S_F0:                                              # E: bullet-time arc around the contact
        u = (s - S_E0) / (S_F0 - S_E0)
        side = Vector((KICK.y, -KICK.x, 0)).normalized()      # to the kicker's right
        start = P_C + side * 11.0 - KICK * 1.5 + Vector((0, 0, 1.0))
        end = P_C + side * 6.5 + KICK * 7.0 + Vector((0, 0, -1.2))
        mid = P_C + (start.lerp(end, 0.5) - P_C).normalized() * 10.5
        e = smooth(u)
        pos = start.lerp(mid, e).lerp(mid.lerp(end, e), e)
        target = motion.ball(min(t, ATT_OUT + 0.004)) - side * 0.9 - Vector((0, 0, 0.3))
        return pos, target, lerp(34, 42, e), 2.8
    u = (s - S_F0) / max(S_TOTAL - S_F0, 1e-3)               # F: wide reverse, ball flies past
    side = Vector((KICK.y, -KICK.x, 0)).normalized()
    flat = Vector((KICK.x, KICK.y, 0)).normalized()
    pos = (flat * 31.0 + side * 6.5 + Vector((0, 0, 1.3))).lerp(flat * 25.0 + side * 5.2 + Vector((0, 0, 1.7)), smooth(u))
    shake = math.exp(-(s - S_F0) * 3.5) * 0.10
    pos += Vector((math.sin(s * 71.0), 0, math.cos(s * 93.0))) * shake
    return pos, Vector((0.0, 0.0, 3.1)), 62, 4.0


def camera_matrix(s):
    pos, target, lens, fstop = camera_state(s)
    quat = (target - pos).to_track_quat("-Z", "Y")
    return pos, quat, lens, fstop, (target - pos).length


# ================================================================ bake body, ball, camera
REST = {b.name: b.matrix_local.copy() for b in arm.data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
prev_quat = {}
spin = Quaternion()
prev_t = 0.0
ball_states = {}


def key_quat(owner, key, quat, frame):
    last = prev_quat.get(key)
    if last is not None and last.dot(quat) < 0:
        quat = -quat
    prev_quat[key] = quat.copy()
    owner.rotation_quaternion = quat
    owner.keyframe_insert("rotation_quaternion", frame=frame)


for frame in range(1, N_FRAMES + 1):
    s = (frame - 1) / FPS
    t = warp.t_of_s(s)
    mats = motion.pose(t)
    mats["HumanoidRootPart"] = Matrix.Identity(4)
    for name, pb in arm.pose.bones.items():
        parent = PARENT[name]
        m_parent = mats[parent] if parent else Matrix.Identity(4)
        basis = REST[name].inverted() @ m_parent.inverted() @ mats[name] @ REST[name]
        loc, quat, _ = basis.decompose()
        if name == "Torso":
            pb.location = loc
            pb.keyframe_insert("location", frame=frame)
        key_quat(pb, name, quat, frame)

    # Ball: the parent empty squashes along the kick direction, the child spins.
    pos = motion.ball(t)
    dt = t - prev_t
    vel = (motion.ball(t + 1e-3) - motion.ball(t - 1e-3)) / 2e-3 if t > 1e-3 else Vector()
    if vel.length > 0.5 and not (ATT_IN <= t <= ATT_OUT):
        axis = Vector((0, 0, 1)).cross(vel)
        axis = axis.normalized() if axis.length > 0.3 else Vector((1, 0, 0))
        rate = -6.0 if t < ATT_IN else -28.0          # backspin, then a fast spin after the kick
        spin = Quaternion(axis, rate * dt) @ spin
    prev_t = t
    align = KICK.to_track_quat("Z", "Y")
    sq = motion.squash(t)
    ball_rig.location = pos
    ball_rig.scale = (1.0 / math.sqrt(sq), 1.0 / math.sqrt(sq), sq)
    ball_rig.keyframe_insert("location", frame=frame)
    ball_rig.keyframe_insert("scale", frame=frame)
    key_quat(ball_rig, "ballrig", align, frame)
    key_quat(ball, "ball", align.inverted() @ spin, frame)

    cpos, cquat, lens, fstop, focus = camera_matrix(s)
    cam.location = cpos
    cam.keyframe_insert("location", frame=frame)
    key_quat(cam, "cam", cquat, frame)
    cam_data.lens = lens
    cam_data.dof.focus_distance = focus
    cam_data.dof.aperture_fstop = fstop
    cam_data.keyframe_insert("lens", frame=frame)
    cam_data.dof.keyframe_insert("focus_distance", frame=frame)
    cam_data.dof.keyframe_insert("aperture_fstop", frame=frame)

# Camera cuts must not blend: make keys on both sides of a cut constant.
CUTS = [round(c * FPS) + 1 for c in (1.95, 5.62, 9.18, S_E0, S_F0)]
for owner in (cam, cam_data):
    anim = owner.animation_data
    if not anim or not anim.action:
        continue
    action = anim.action
    curves = []
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves += list(bag.fcurves)
    except AttributeError:
        curves = list(action.fcurves)
    for curve in curves:
        for point in curve.keyframe_points:
            if any(abs(point.co.x - (c - 1)) < 0.5 for c in CUTS):
                point.interpolation = "CONSTANT"
print("BAKED", flush=True)

# ================================================================ VFX (galactic, only at the kick)
E1 = Vector((0, 0, 1)).cross(KICK).normalized()      # two axes of the plane that faces the kick
E2 = KICK.cross(E1).normalized()
DISC_ROT = Matrix((E1, E2, KICK)).transposed().to_4x4()


def fx_material(name):
    """Emission with color and alpha from the 'Col' attribute, soft falloff from UV."""
    mat, n, out = new_material(name)
    attr = n.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    uv = n.new("ShaderNodeTexCoord").outputs["UV"]
    sep = n.new("ShaderNodeSeparateXYZ")
    n.link(uv, sep.inputs[0])
    fall_u = n.math("EXPONENT", n.math("MULTIPLY", n.math("POWER", n.math("ABSOLUTE", sep.outputs["X"]), 1.5), -4.5))
    fall_v = n.math("EXPONENT", n.math("MULTIPLY", n.math("POWER", n.math("ABSOLUTE", sep.outputs["Y"]), 1.5), -4.5))
    alpha = n.math("MULTIPLY", n.math("MULTIPLY", fall_u, fall_v), attr.outputs["Alpha"], clamp=True)
    emit = n.new("ShaderNodeEmission")
    n.link(attr.outputs["Color"], emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 5.0
    transp = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    n.link(alpha, mix.inputs[0])
    n.link(transp.outputs[0], mix.inputs[1])
    n.link(emit.outputs[0], mix.inputs[2])
    n.link(mix.outputs[0], out.inputs["Surface"])
    return mat


def fx_object(name, material):
    mesh = bpy.data.meshes.new(name)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    COL_FX.objects.link(obj)
    obj.visible_shadow = obj.visible_diffuse = False
    return obj


def set_quads(obj, verts, colors, uvs):
    """verts (N,4,3), colors (N,4) rgba per quad, uvs (N,4,2)."""
    mesh = obj.data
    mesh.clear_geometry()
    count = len(verts)
    if count == 0:
        return
    mesh.vertices.add(count * 4)
    mesh.loops.add(count * 4)
    mesh.polygons.add(count)
    mesh.vertices.foreach_set("co", np.asarray(verts, np.float32).reshape(-1))
    mesh.loops.foreach_set("vertex_index", np.arange(count * 4, dtype=np.int32))
    mesh.polygons.foreach_set("loop_start", np.arange(0, count * 4, 4, dtype=np.int32))
    mesh.polygons.foreach_set("loop_total", np.full(count, 4, dtype=np.int32))
    mesh.update()
    layer = mesh.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    layer.data.foreach_set("color", np.repeat(np.asarray(colors, np.float32), 4, axis=0).reshape(-1))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", np.asarray(uvs, np.float32).reshape(-1))


FX_MAT = fx_material("MAT_FX_Stars")
fx_stars = fx_object("FX_Stars", FX_MAT)
fx_trail = fx_object("FX_Trail", FX_MAT)
QUAD_UV = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], np.float32)

rng = np.random.default_rng(11)

# --- particle sets (all analytic, so slow motion and scrubbing need no simulation)
N_GATHER = 320
gather = dict(
    born=rng.uniform(0.0, max(S_REL - S_IN - 0.25, 0.3), N_GATHER),
    life=rng.uniform(0.45, 0.75, N_GATHER),
    radius=rng.uniform(2.4, 6.0, N_GATHER),
    angle=rng.uniform(0, math.tau, N_GATHER),
    turns=rng.uniform(0.6, 1.4, N_GATHER),
    depth=rng.normal(0, 0.5, N_GATHER),
    size=rng.uniform(0.035, 0.085, N_GATHER),
    color=PAL_ARRAY[rng.integers(0, len(PAL_ARRAY), N_GATHER)],
)
N_BURST = 900
cone = rng.random(N_BURST) < 0.62
theta = np.where(cone, rng.uniform(0, 0.95, N_BURST) ** 1.3, rng.uniform(1.1, 2.3, N_BURST))
phi = rng.uniform(0, math.tau, N_BURST)
dirs = (np.outer(np.cos(theta), np.array(KICK)) + np.outer(np.sin(theta) * np.cos(phi), np.array(E1))
        + np.outer(np.sin(theta) * np.sin(phi), np.array(E2)))
burst = dict(
    delay=rng.uniform(0.0, 0.07, N_BURST),
    life=rng.uniform(0.7, 1.9, N_BURST),
    vel=dirs * np.where(cone, rng.uniform(14, 52, N_BURST), rng.uniform(7, 24, N_BURST))[:, None],
    drag=rng.uniform(2.2, 4.0, N_BURST),
    size=rng.uniform(0.04, 0.13, N_BURST),
    twinkle=rng.uniform(0, math.tau, N_BURST),
    color=PAL_ARRAY[rng.integers(0, len(PAL_ARRAY), N_BURST)],
)
N_SHED = 320
shed_t = np.sort(rng.uniform(ATT_OUT, ATT_OUT + 0.42, N_SHED))
shed = dict(
    t=shed_t,
    s=np.array([warp.s_of_t(v) for v in shed_t]),
    pos=np.array([motion.ball(v) for v in shed_t]) + rng.normal(0, 0.28, (N_SHED, 3)),
    vel=rng.normal(0, 1.4, (N_SHED, 3)),
    life=rng.uniform(0.5, 1.1, N_SHED),
    size=rng.uniform(0.05, 0.14, N_SHED),
    color=PAL_ARRAY[rng.integers(0, len(PAL_ARRAY), N_SHED)],
)


def star_quads(pos, vel, size, color, alpha, cam_pos, cross):
    """Camera-facing streak along the velocity; 'cross' adds a second quad to make a sparkle."""
    if len(pos) == 0:
        return np.zeros((0, 4, 3)), np.zeros((0, 4)), np.zeros((0, 4, 2))
    to_cam = cam_pos[None, :] - pos
    to_cam /= np.linalg.norm(to_cam, axis=1)[:, None] + 1e-9
    speed = np.linalg.norm(vel, axis=1)
    along = np.where(speed[:, None] > 1e-3, vel / (speed[:, None] + 1e-9), np.array([[0, 0, 1.0]]))
    along = along - to_cam * np.sum(along * to_cam, axis=1)[:, None]
    norm = np.linalg.norm(along, axis=1)[:, None]
    up = np.cross(to_cam, np.array([[0.3, 0.2, 1.0]]))
    along = np.where(norm > 1e-3, along / (norm + 1e-9), up / (np.linalg.norm(up, axis=1)[:, None] + 1e-9))
    across = np.cross(along, to_cam)
    length = np.maximum(size * 2.2, speed * 0.018)[:, None]
    width = (size * 0.9)[:, None]

    def quad(a_vec, a_len, b_vec, b_len):
        return np.stack([pos - a_vec * a_len - b_vec * b_len, pos + a_vec * a_len - b_vec * b_len,
                         pos + a_vec * a_len + b_vec * b_len, pos - a_vec * a_len + b_vec * b_len], axis=1)

    verts = [quad(along, length, across, width)]
    rgba = np.concatenate([color, alpha[:, None]], axis=1)
    cols = [rgba]
    if cross:
        verts.append(quad(across, length * 0.8, along, width * 0.7))
        cols.append(rgba)
    verts = np.concatenate(verts)
    cols = np.concatenate(cols)
    return verts, cols, np.repeat(QUAD_UV[None], len(verts), axis=0)


def build_stars(s, t, cam_pos, power):
    sigma = s - S_IN
    parts = []
    center = np.array(motion.ball(t))
    e1, e2, kd = np.array(E1), np.array(E2), np.array(KICK)
    # gather: stars spiral into the ball while the foot is on it
    tau = sigma - gather["born"]
    live = (tau > 0) & (tau < gather["life"]) & (s < S_REL + 0.05)
    if live.any():
        u = (tau / gather["life"])[live]

        def spiral(uu):
            r = gather["radius"][live] * (1 - uu) ** 1.4 + 0.5
            a = gather["angle"][live] + gather["turns"][live] * math.tau * uu ** 0.8
            return (center[None] + e1[None] * (np.cos(a) * r)[:, None] + e2[None] * (np.sin(a) * r)[:, None]
                    + kd[None] * (gather["depth"][live] * (1 - uu))[:, None])

        pos = spiral(u)
        vel = (spiral(np.minimum(u + 0.02, 1.0)) - pos) / (0.02 * gather["life"][live])[:, None]
        alpha = np.sin(np.pi * u) ** 0.6 * power
        parts.append(star_quads(pos, vel, gather["size"][live], gather["color"][live], alpha, cam_pos, True))
    # burst: stars fly out when the ball leaves the foot
    tau = (s - S_REL) - burst["delay"]
    live = (tau > 0) & (tau < burst["life"])
    if live.any():
        tl, k = tau[live], burst["drag"][live]
        decay = np.exp(-k * tl)
        pos = np.array(P_R)[None] + burst["vel"][live] * ((1 - decay) / k)[:, None]
        pos[:, 2] -= 1.6 * tl * tl
        vel = burst["vel"][live] * decay[:, None]
        u = tl / burst["life"][live]
        alpha = (1 - u) ** 1.4 * (0.65 + 0.35 * np.sin(tl * 30 + burst["twinkle"][live])) * power
        parts.append(star_quads(pos, vel, burst["size"][live] * (1 - 0.5 * u), burst["color"][live], alpha, cam_pos, True))
    # shed: sparkles left behind on the path of the ball
    tau = s - shed["s"]
    live = (t >= shed["t"]) & (tau < shed["life"])
    if live.any():
        tl = tau[live]
        pos = shed["pos"][live] + shed["vel"][live] * tl[:, None]
        u = tl / shed["life"][live]
        alpha = (1 - u) ** 1.2 * power
        parts.append(star_quads(pos, shed["vel"][live] * 0.2, shed["size"][live] * (1 - 0.6 * u),
                                shed["color"][live], alpha, cam_pos, True))
    if not parts:
        set_quads(fx_stars, [], [], [])
        return
    set_quads(fx_stars, np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts]),
              np.concatenate([p[2] for p in parts]))


def build_trail(s, t, power):
    """Comet tail behind the ball, with two spiral arms around it."""
    if t <= ATT_OUT or power <= 0.001:
        set_quads(fx_trail, [], [], [])
        return
    steps, span = 56, 0.26
    times = [t - span * k / steps for k in range(steps + 1)]
    times = [v for v in times if v >= ATT_OUT]
    if len(times) < 2:
        set_quads(fx_trail, [], [], [])
        return
    pts = np.array([motion.ball(v) for v in times])
    e1, e2 = np.array(E1), np.array(E2)
    verts, cols, uvs = [], [], []
    ring = 10
    head = np.array(PALETTE["white"])
    mid = np.array(PALETTE["cyan"])
    tail = np.array(PALETTE["violet"])

    def tail_color(u):
        return head + (mid - head) * min(u * 3, 1) if u < 0.33 else mid + (tail - mid) * min((u - 0.33) * 1.5, 1)

    for k in range(len(times) - 1):
        u0, u1 = k / steps, (k + 1) / steps
        r0, r1 = R_BALL * 0.98 * (1 - u0) ** 0.6, R_BALL * 0.98 * (1 - u1) ** 0.6
        for j in range(ring):
            a0, a1 = math.tau * j / ring, math.tau * (j + 1) / ring
            c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            verts.append([pts[k] + (e1 * c0 + e2 * s0) * r0, pts[k] + (e1 * c1 + e2 * s1) * r0,
                          pts[k + 1] + (e1 * c1 + e2 * s1) * r1, pts[k + 1] + (e1 * c0 + e2 * s0) * r1])
            cols.append(list(tail_color(u0)) + [(1 - u0) ** 1.3 * 0.85 * power])
            uvs.append([[0, 0]] * 4)
        for arm_index, name in enumerate(("magenta", "cyan", "gold")):
            base = math.tau * arm_index / 3 + s * 9.0

            def helix(index, uu):
                a = base + uu * 13.0
                rad = 0.75 + 2.4 * uu ** 0.8
                return pts[index] + (e1 * math.cos(a) + e2 * math.sin(a)) * rad, (e1 * math.cos(a) + e2 * math.sin(a))

            p0, n0 = helix(k, u0)
            p1, n1 = helix(k + 1, u1)
            w0, w1 = 0.30 * (1 - u0) + 0.05, 0.30 * (1 - u1) + 0.05
            verts.append([p0 - n0 * w0, p0 + n0 * w0, p1 + n1 * w1, p1 - n1 * w1])
            cols.append(list(PALETTE[name]) + [(1 - u0) ** 1.1 * power])
            uvs.append([[0, -1], [0, 1], [0, 1], [0, -1]])
    set_quads(fx_trail, np.array(verts), np.array(cols), np.array(uvs))


# --- galaxy disc: a spiral that spins around the ball while the foot is on it
mat, n, out = new_material("MAT_FX_Galaxy")
uv = n.new("ShaderNodeTexCoord").outputs["UV"]
p = n.vmath("SCALE", n.vmath("SUBTRACT", uv, (0.5, 0.5, 0.0)), scale=2.0)
sep = n.new("ShaderNodeSeparateXYZ")
n.link(p, sep.inputs[0])
r = n.vmath("LENGTH", p)
ang = n.math("ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
swirl = n.math("MULTIPLY", n.math("LOGARITHM", n.math("ADD", r, 0.04), math.e), 4.2)
arms = n.math("ADD", n.math("MULTIPLY", n.math("COSINE", n.math("SUBTRACT", n.math("MULTIPLY", ang, 2.0), swirl)), 0.5), 0.5)
arms2 = n.math("ADD", n.math("MULTIPLY", n.math("COSINE", n.math("SUBTRACT", n.math("MULTIPLY", ang, 5.0), n.math("MULTIPLY", swirl, 2.3))), 0.5), 0.5)
arms = n.math("ADD", n.math("POWER", arms, 2.6), n.math("MULTIPLY", n.math("POWER", arms2, 3.0), 0.35))
clouds = n.noise(p, 5.5, detail=5.0, roughness=0.65, dims="3D").outputs["Fac"]
dots = n.map_range(n.noise(p, 70.0, detail=0.0, dims="3D").outputs["Fac"], 0.70, 0.76, 0.0, 1.0)
edge = n.map_range(r, 1.0, 0.25, 0.0, 1.0, smooth=True)
core = n.math("EXPONENT", n.math("MULTIPLY", n.math("POWER", n.math("DIVIDE", r, 0.13), 2.0), -1.0))
GAL_POWER = n.new("ShaderNodeValue")
body = n.math("MULTIPLY", n.math("MULTIPLY", arms, n.map_range(clouds, 0.25, 0.75, 0.15, 1.3)), edge)
body = n.math("ADD", body, n.math("MULTIPLY", n.math("MULTIPLY", dots, edge), 0.9))
bright = n.math("MULTIPLY", n.math("ADD", body, n.math("MULTIPLY", core, 1.0)), GAL_POWER.outputs[0])
gal_colors = n.ramp(r, [
    (0.00, (1.00, 1.00, 1.00, 1)), (0.10, (0.55, 0.95, 1.00, 1)), (0.28, (0.10, 0.80, 1.00, 1)),
    (0.48, (0.40, 0.10, 1.00, 1)), (0.72, (1.00, 0.12, 0.75, 1)), (1.00, (0.06, 0.02, 0.35, 1))])
emit = n.new("ShaderNodeEmission")
n.link(gal_colors.outputs["Color"], emit.inputs["Color"])
n.link(n.math("MULTIPLY", bright, 4.0), emit.inputs["Strength"])
transp = n.new("ShaderNodeBsdfTransparent")
mix = n.new("ShaderNodeMixShader")
n.link(n.math("MULTIPLY", bright, 1.0, clamp=True), mix.inputs[0])
n.link(transp.outputs[0], mix.inputs[1])
n.link(emit.outputs[0], mix.inputs[2])
n.link(mix.outputs[0], out.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=2.0)
fx_galaxy = bpy.context.active_object
fx_galaxy.name = "FX_GalaxyDisc"
fx_galaxy.data.materials.append(mat)
for c in list(fx_galaxy.users_collection):
    c.objects.unlink(fx_galaxy)
COL_FX.objects.link(fx_galaxy)
fx_galaxy.visible_shadow = fx_galaxy.visible_diffuse = False


# --- rings: ripples during contact, shock waves at release
def make_ring(name, color):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    seg = 96
    inner = [bm.verts.new((math.cos(math.tau * i / seg) * 0.80, math.sin(math.tau * i / seg) * 0.80, 0)) for i in range(seg)]
    outer = [bm.verts.new((math.cos(math.tau * i / seg), math.sin(math.tau * i / seg), 0)) for i in range(seg)]
    for i in range(seg):
        j = (i + 1) % seg
        face = bm.faces.new((inner[i], outer[i], outer[j], inner[j]))
        for loop, (uu, vv) in zip(face.loops, ((i / seg, 0), (i / seg, 1), ((i + 1) / seg, 1), ((i + 1) / seg, 0))):
            loop[uv_layer].uv = (uu, vv)
    bm.to_mesh(mesh)
    bm.free()
    mat, n, out = new_material("MAT_" + name)
    uv = n.new("ShaderNodeTexCoord").outputs["UV"]
    sep = n.new("ShaderNodeSeparateXYZ")
    n.link(uv, sep.inputs[0])
    v = sep.outputs["Y"]
    across = n.math("MULTIPLY", n.math("POWER", v, 2.5), n.map_range(v, 1.0, 0.90, 0.0, 1.0, smooth=True))
    pos = n.new("ShaderNodeCombineXYZ")
    n.link(n.math("MULTIPLY", sep.outputs["X"], 70.0), pos.inputs[0])
    n.link(n.math("MULTIPLY", v, 1.5), pos.inputs[1])
    streak = n.noise(pos.outputs[0], 1.0, detail=3.0, dims="2D").outputs["Fac"]
    power = n.new("ShaderNodeValue")
    alpha = n.math("MULTIPLY", n.math("MULTIPLY", across, n.map_range(streak, 0.3, 0.7, 0.3, 1.2)), power.outputs[0])
    hot = n.new("ShaderNodeMix")
    hot.data_type = "RGBA"
    n.link(n.math("POWER", across, 2.0, clamp=True), hot.inputs[0])
    hot.inputs[6].default_value = (*color, 1)
    hot.inputs[7].default_value = (0.9, 0.97, 1.0, 1)
    emit = n.new("ShaderNodeEmission")
    n.link(hot.outputs[2], emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 3.0
    transp = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    n.link(n.math("MULTIPLY", alpha, 0.8, clamp=True), mix.inputs[0])
    n.link(transp.outputs[0], mix.inputs[1])
    n.link(emit.outputs[0], mix.inputs[2])
    n.link(mix.outputs[0], out.inputs["Surface"])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    COL_FX.objects.link(obj)
    obj.visible_shadow = obj.visible_diffuse = False
    return obj, power.outputs[0]


RIPPLES = [make_ring(f"FX_Ripple_{i}", PALETTE[c]) for i, c in enumerate(("cyan", "magenta", "violet", "pink", "cyan"))]
SHOCKS = [make_ring(f"FX_Shock_{i}", PALETTE[c]) for i, c in enumerate(("cyan", "magenta", "violet", "gold"))]
SHOCK_SPEC = [(0.00, 0.0, 15.0), (0.06, 2.0, 10.0), (0.13, 4.5, 7.0), (0.20, 7.5, 4.5)]   # delay, offset on axis, size

# --- flare: a camera-facing star glare at contact and at release
mat, n, out = new_material("MAT_FX_Flare")
uv = n.new("ShaderNodeTexCoord").outputs["UV"]
p = n.vmath("SCALE", n.vmath("SUBTRACT", uv, (0.5, 0.5, 0.0)), scale=2.0)
sep = n.new("ShaderNodeSeparateXYZ")
n.link(p, sep.inputs[0])
ax, ay = n.math("ABSOLUTE", sep.outputs["X"]), n.math("ABSOLUTE", sep.outputs["Y"])
r = n.vmath("LENGTH", p)


def streak_term(a, b, sharp, reach):
    return n.math("MULTIPLY", n.math("EXPONENT", n.math("MULTIPLY", b, -sharp)),
                  n.math("EXPONENT", n.math("MULTIPLY", a, -reach)))


d1 = n.math("ABSOLUTE", n.math("MULTIPLY", n.math("ADD", sep.outputs["X"], sep.outputs["Y"]), 0.7071))
d2 = n.math("ABSOLUTE", n.math("MULTIPLY", n.math("SUBTRACT", sep.outputs["X"], sep.outputs["Y"]), 0.7071))
glare = n.math("ADD", streak_term(ax, ay, 70.0, 3.2), streak_term(ay, ax, 70.0, 4.5))
glare = n.math("ADD", glare, n.math("MULTIPLY", n.math("ADD", streak_term(d1, d2, 90.0, 6.0), streak_term(d2, d1, 90.0, 6.0)), 0.6))
glare = n.math("ADD", glare, n.math("MULTIPLY", n.math("EXPONENT", n.math("MULTIPLY", n.math("POWER", r, 2.0), -28.0)), 1.6))
glare = n.math("MULTIPLY", glare, n.map_range(r, 1.0, 0.6, 0.0, 1.0, smooth=True))
FLARE_POWER = n.new("ShaderNodeValue")
bright = n.math("MULTIPLY", glare, FLARE_POWER.outputs[0])
flare_colors = n.ramp(n.map_range(r, 0.0, 0.9), [
    (0.0, (1.0, 1.0, 1.0, 1)), (0.25, (0.6, 0.95, 1.0, 1)), (0.6, (0.6, 0.3, 1.0, 1)), (1.0, (1.0, 0.2, 0.8, 1))])
emit = n.new("ShaderNodeEmission")
n.link(flare_colors.outputs["Color"], emit.inputs["Color"])
n.link(n.math("MULTIPLY", bright, 6.0), emit.inputs["Strength"])
transp = n.new("ShaderNodeBsdfTransparent")
mix = n.new("ShaderNodeMixShader")
n.link(n.math("MULTIPLY", bright, 1.0, clamp=True), mix.inputs[0])
n.link(transp.outputs[0], mix.inputs[1])
n.link(emit.outputs[0], mix.inputs[2])
n.link(mix.outputs[0], out.inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=2.0)
fx_flare = bpy.context.active_object
fx_flare.name = "FX_Flare"
fx_flare.data.materials.append(mat)
for c in list(fx_flare.users_collection):
    c.objects.unlink(fx_flare)
COL_FX.objects.link(fx_flare)
fx_flare.visible_shadow = fx_flare.visible_diffuse = fx_flare.visible_glossy = False

# --- nebula: layered glowing cloud cards that expand along the kick when the ball leaves
mat, n, out = new_material("MAT_FX_Nebula")
coords = n.new("ShaderNodeTexCoord").outputs["Object"]
info = n.new("ShaderNodeObjectInfo")
seed = n.vmath("SCALE", (7.3, 3.1, 5.7), scale=info.outputs["Random"])
NEB_POWER = n.new("ShaderNodeValue")
NEB_CHURN = n.new("ShaderNodeValue")
NEB_ERODE = n.new("ShaderNodeValue")
p_seed = n.vmath("ADD", coords, seed)
warp_n = n.noise(p_seed, 1.4, w=NEB_CHURN.outputs[0], detail=2.0)
p_w = n.vmath("ADD", coords, n.vmath("SCALE", n.vmath("SUBTRACT", warp_n.outputs["Color"], (0.5, 0.5, 0.5)), scale=0.7))
rr = n.vmath("LENGTH", p_w)
lumps = n.noise(p_seed, 2.6, w=NEB_CHURN.outputs[0], detail=5.0, roughness=0.65).outputs["Fac"]
shell = n.map_range(n.math("ADD", rr, n.math("MULTIPLY", n.math("SUBTRACT", lumps, 0.5), 0.8)), 0.80, 0.25, 0.0, 1.0, smooth=True)
shell = n.math("MULTIPLY", shell, n.map_range(n.vmath("LENGTH", coords), 1.0, 0.7, 0.0, 1.0, smooth=True))
wisps = n.map_range(lumps, NEB_ERODE.outputs[0], n.math("ADD", NEB_ERODE.outputs[0], 0.25), 0.0, 1.0, smooth=True)
hue = n.noise(p_seed, 1.1, w=n.math("MULTIPLY", NEB_CHURN.outputs[0], 0.5), detail=1.0).outputs["Fac"]
neb_colors = n.ramp(n.map_range(hue, 0.30, 0.70), [
    (0.00, (0.06, 0.03, 0.45, 1)), (0.25, (0.40, 0.08, 1.00, 1)), (0.50, (1.00, 0.12, 0.75, 1)),
    (0.75, (0.10, 0.80, 1.00, 1)), (1.00, (0.90, 0.95, 1.00, 1))])
neb_alpha = n.math("MULTIPLY", n.math("MULTIPLY", shell, wisps), NEB_POWER.outputs[0])
emit = n.new("ShaderNodeEmission")
n.link(neb_colors.outputs["Color"], emit.inputs["Color"])
emit.inputs["Strength"].default_value = 2.2
transp = n.new("ShaderNodeBsdfTransparent")
mix = n.new("ShaderNodeMixShader")
n.link(n.math("MULTIPLY", neb_alpha, 1.0, clamp=True), mix.inputs[0])
n.link(transp.outputs[0], mix.inputs[1])
n.link(emit.outputs[0], mix.inputs[2])
n.link(mix.outputs[0], out.inputs["Surface"])
neb_mesh = bpy.data.meshes.new("FX_NebulaCard")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
bm.to_mesh(neb_mesh)
bm.free()
neb_mesh.materials.append(mat)
NEBULA = []
for i in range(7):
    card = bpy.data.objects.new(f"FX_Nebula_{i}", neb_mesh)
    COL_FX.objects.link(card)
    card.visible_shadow = card.visible_diffuse = card.visible_glossy = False
    NEBULA.append(card)
NEB_SPEC = [(0.0, 1.00, 0.0, 0.0), (1.5, 0.85, 1.2, 0.4), (3.0, 0.75, -1.0, 0.8), (4.5, 0.62, 0.8, -0.9),
            (6.0, 0.50, -0.6, -0.5), (-1.2, 0.80, -1.4, -0.3), (2.2, 0.55, 0.3, 1.3)]   # along axis, size, side offsets

# --- colored lights on the dummy and the pitch
light_data = bpy.data.lights.new("LGT_FX_Kick", "POINT")
light_data.shadow_soft_size = 0.6
fx_light = bpy.data.objects.new("LGT_FX_Kick", light_data)
COL_FX.objects.link(fx_light)
light2_data = bpy.data.lights.new("LGT_FX_Burst", "POINT")
light2_data.shadow_soft_size = 2.0
fx_light2 = bpy.data.objects.new("LGT_FX_Burst", light2_data)
COL_FX.objects.link(fx_light2)

FX_OBJECTS = [fx_stars, fx_trail, fx_galaxy, fx_flare, fx_light, fx_light2] + NEBULA + [r[0] for r in RIPPLES + SHOCKS]


def pulse(x, attack, decay):
    if x < 0:
        return 0.0
    return min(x / attack, 1.0) * math.exp(-max(x - attack, 0.0) / decay)


def color_cycle(x):
    keys = [PALETTE["violet"], PALETTE["cyan"], PALETTE["magenta"], PALETTE["cyan"]]
    i = int(x) % len(keys)
    a, b = Vector(keys[i]), Vector(keys[(i + 1) % len(keys)])
    return a.lerp(b, smooth(x - int(x)))


def apply_vfx(frame):
    """Sets every effect for this frame. Nothing is visible before the foot meets the ball."""
    s = (frame - 1) / FPS
    t = warp.t_of_s(s)
    active = S_IN <= s <= FX_END
    for obj in FX_OBJECTS:
        obj.hide_render = not active
    BALL_BSDF.inputs["Emission Strength"].default_value = 0.0
    if not active:
        return
    sigma = s - S_IN                       # screen seconds since contact
    rel = s - S_REL                        # screen seconds since release (negative during contact)
    hold = S_REL - S_IN
    fade = 1.0 - smooth((s - (S_REL + 1.15)) / 0.95)
    cam_pos, cam_quat, _, _, _ = camera_matrix(s)
    cam_np = np.array(cam_pos)
    center = motion.ball(t)

    # ball glow: builds while the foot is on it, then cools
    charge = smooth(sigma / hold) if rel < 0 else math.exp(-rel * 1.6)
    BALL_BSDF.inputs["Emission Strength"].default_value = 1.3 * charge * fade
    BALL_BSDF.inputs["Emission Color"].default_value = (*color_cycle(sigma * 1.7).lerp(Vector(PALETTE["white"]), 0.45), 1)

    # galaxy disc
    if rel < 0:
        grow = 1.0 - math.exp(-sigma * 3.2)
        gal_scale = 0.6 + 4.6 * grow + 0.25 * math.sin(sigma * 9.0)
        gal_power = min(sigma / 0.12, 1.0) * (0.9 + 0.25 * math.sin(sigma * 13.0))
    else:
        gal_scale = 5.2 + 26.0 * (1 - math.exp(-rel * 5.0))
        gal_power = math.exp(-rel * 4.2) * 0.9
    fx_galaxy.hide_render = gal_power < 0.004
    spin_angle = -sigma * 3.4 - max(rel, 0) * 4.0
    fx_galaxy.matrix_world = (Matrix.Translation(center - KICK * 0.55 if rel < 0 else P_R + KICK * (1.0 + rel * 6.0))
                              @ DISC_ROT @ Matrix.Rotation(spin_angle, 4, "Z") @ Matrix.Scale(gal_scale, 4))
    GAL_POWER.outputs[0].default_value = gal_power * fade

    # ripples during contact
    period = hold / (len(RIPPLES) - 0.5)
    for i, (obj, power) in enumerate(RIPPLES):
        age = sigma - i * period
        life = 0.75
        show = 0 < age < life and i * period < hold
        obj.hide_render = not show
        if show:
            u = age / life
            obj.matrix_world = (Matrix.Translation(center + KICK * (0.1 + 0.3 * i)) @ DISC_ROT
                                @ Matrix.Scale(0.7 + 5.5 * (1 - (1 - u) ** 2), 4))
            power.default_value = (1 - u) ** 1.5 * 1.3

    # shock waves at release
    for (obj, power), (delay, offset, size) in zip(SHOCKS, SHOCK_SPEC):
        age = rel - delay
        life = 1.0
        show = 0 < age < life
        obj.hide_render = not show
        if show:
            u = age / life
            obj.matrix_world = (Matrix.Translation(P_R + KICK * (offset + 2.0 * u)) @ DISC_ROT
                                @ Matrix.Scale(0.6 + size * (1 - (1 - u) ** 2.4), 4))
            power.default_value = (1 - u) ** 1.6 * 1.2 * fade

    # flare
    flare_power = 0.9 * pulse(sigma, 0.03, 0.16) + 0.55 * pulse(rel, 0.03, 0.16) + (0.07 * charge if rel < 0 else 0.0)
    fx_flare.hide_render = flare_power < 0.01
    flare_pos = center if rel < 0 else P_R
    toward = (cam_pos - flare_pos).normalized()
    flare_size = 2.2 + 1.6 * pulse(sigma, 0.03, 0.2) + (4.0 * pulse(rel, 0.03, 0.3) if rel > 0 else 0.0)
    fx_flare.matrix_world = (Matrix.Translation(flare_pos + toward * 0.9) @ cam_quat.to_matrix().to_4x4()
                             @ Matrix.Scale(flare_size, 4))
    FLARE_POWER.outputs[0].default_value = flare_power

    # nebula
    neb_power = pulse(rel, 0.07, 0.62) * 1.25 * fade if rel > 0 else 0.0
    grow = 1 - math.exp(-max(rel, 0) * 2.6)
    size = 1.6 + 7.5 * grow
    face = cam_quat.to_matrix().to_4x4()
    for card, (axis_pos, card_size, off1, off2) in zip(NEBULA, NEB_SPEC):
        card.hide_render = neb_power < 0.004
        where = P_R + KICK * (1.0 + (2.0 + axis_pos) * grow) + (E1 * off1 + E2 * off2) * grow * 1.6
        card.matrix_world = Matrix.Translation(where) @ face @ Matrix.Scale(size * card_size, 4)
    NEB_POWER.outputs[0].default_value = neb_power * 0.6
    NEB_CHURN.outputs[0].default_value = max(rel, 0) * 0.9
    NEB_ERODE.outputs[0].default_value = 0.22 + 0.5 * smooth(max(rel, 0) / 1.7)

    # lights
    fx_light.location = center + Vector((0, 0, 0.2)) - KICK * 0.3
    light_data.color = color_cycle(sigma * 1.7)
    light_data.energy = (1800.0 * charge + 4000.0 * pulse(sigma, 0.03, 0.12)) * fade
    fx_light2.location = P_R + KICK * (2.0 + 5.0 * grow) + Vector((0, 0, 0.5))
    light2_data.color = color_cycle(1.0 + max(rel, 0) * 2.2)
    light2_data.energy = 7000.0 * pulse(rel, 0.04, 0.5) * fade if rel > 0 else 0.0

    build_stars(s, t, cam_np, fade)
    build_trail(s, t, fade)


# ================================================================ render
if args.save:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save))
    print("SAVED", args.save, flush=True)

if args.frames:
    parts = [int(v) for v in args.frames.split(":")]
    start, stop, step = parts[0], (parts[1] if len(parts) > 1 else parts[0]), (parts[2] if len(parts) > 2 else 1)
    frames = range(start, min(stop, N_FRAMES) + 1, step)
else:
    frames = range(1, N_FRAMES + 1)
for frame in frames:
    path = os.path.join(args.out, f"{frame:04d}.png")
    if os.path.exists(path):
        continue
    scene.frame_set(frame)
    apply_vfx(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"FRAME_DONE {frame}", flush=True)
