"""Green sword slash.

Usage: python3 sword.py MODE OUT_DIR [frame ...]
  MODE video    -> 1280x720 frames of the full shot
  MODE flipbook -> 256x256 frames of the slash only, camera faces the slash
  MODE export   -> writes sword.fbx and the two sword textures to OUT_DIR
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from PIL import Image

from common import add_camera, key, look_at, new_material, render_frames, reset_scene

MODE = sys.argv[1]
OUT = sys.argv[2]
FRAMES = [int(a) for a in sys.argv[3:]] or None
END = 60
os.makedirs(OUT, exist_ok=True)

if MODE == "flipbook":
    scene = reset_scene(256, 256, 24, END)
else:
    scene = reset_scene(1280, 720, 48, END)
col = scene.collection
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
random.seed(3)

# ---------------------------------------------------------------- textures
TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "roblox", "sword")
os.makedirs(TEX_DIR, exist_ok=True)
COLOR_PNG = os.path.abspath(os.path.join(TEX_DIR, "sword_color.png"))
EMIT_PNG = os.path.abspath(os.path.join(TEX_DIR, "sword_emissive.png"))


def make_textures():
    size = 512
    rng = np.random.default_rng(5)
    ys, xs = np.mgrid[0:size, 0:size] / (size - 1.0)
    v = 1.0 - ys  # v = 0 at the bottom of the image
    color = np.zeros((size, size, 3))
    emit = np.zeros((size, size, 3))

    # Blade: u 0..0.5. Bright core in the middle, dark emerald body, thin bright edges.
    blade = xs < 0.5
    across = np.abs(xs / 0.5 - 0.5) * 2.0  # 0 at the center line, 1 at the cutting edge
    streak = rng.random((1, size)).repeat(size, 0)
    streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)) / 255.0
    core = np.exp(-(across / 0.16) ** 2)
    pulse = 0.75 + 0.25 * np.sin(v * 60.0) * np.sin(v * 17.0 + 1.0)
    edge = np.clip((across - 0.86) / 0.14, 0, 1) ** 2
    body = np.stack([0.015 + 0.03 * (1 - across), 0.20 + 0.25 * (1 - across), 0.08 + 0.10 * (1 - across)], -1)
    body *= (0.8 + 0.4 * streak)[..., None]
    glow = np.stack([0.45 * core + 0.3 * edge, 1.0 * core * pulse + 0.9 * edge, 0.55 * core + 0.4 * edge], -1)
    color[blade] = np.clip(body + glow, 0, 1)[blade]
    emit[blade] = np.clip(glow, 0, 1)[blade]

    # Guard and pommel metal: u 0.5..0.75.
    guard = (xs >= 0.5) & (xs < 0.75)
    grain = rng.random((size, size)) * 0.03
    metal = np.stack([0.10 + 0.08 * v + grain, 0.115 + 0.09 * v + grain, 0.12 + 0.09 * v + grain], -1)
    color[guard] = metal[guard]

    # Grip wrap: u 0.75..1, v 0..0.5.
    grip = (xs >= 0.75) & (v < 0.5)
    wrap = (np.sin((xs * 40.0 + v * 70.0) * math.pi) > 0).astype(float)
    leather = np.stack([0.025 + 0.03 * wrap, 0.05 + 0.05 * wrap, 0.035 + 0.035 * wrap], -1)
    color[grip] = leather[grip]

    # Gem: u 0.75..1, v 0.5..1.
    gem = (xs >= 0.75) & (v >= 0.5)
    color[gem] = (0.25, 1.0, 0.45)
    emit[gem] = (0.25, 1.0, 0.45)

    for path, data in ((COLOR_PNG, color), (EMIT_PNG, emit)):
        Image.fromarray((np.clip(data, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).save(path)


make_textures()

# ---------------------------------------------------------------- sword mesh
BLADE_LEN = 1.55
mesh = bpy.data.meshes.new("Sword")
bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")


def loft(rings, uv_fn, smooth, cap_start=True, cap_end=True):
    """Join rings of points with quads. uv_fn(co) -> (u, v)."""
    rows = [[bm.verts.new(p) for p in ring] for ring in rings]
    faces = []
    for a, b in zip(rows, rows[1:]):
        count = len(a)
        for i in range(count):
            j = (i + 1) % count
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    if cap_start:
        faces.append(bm.faces.new(list(reversed(rows[0]))))
    if cap_end:
        faces.append(bm.faces.new(rows[-1]))
    for face in faces:
        face.smooth = smooth
        for loop in face.loops:
            loop[uv_layer].uv = uv_fn(loop.vert.co)
    return faces


def ring_xy(z, rx, ry, count, phase=0.0):
    return [Vector((math.cos(math.tau * i / count + phase) * rx,
                    math.sin(math.tau * i / count + phase) * ry, z)) for i in range(count)]


# Blade: diamond section with a ridge. Width on X, thickness on Y.
blade_profile = [(0.06, 0.075, 0.018), (0.11, 0.120, 0.028), (0.30, 0.105, 0.026),
                 (1.05, 0.090, 0.022), (1.30, 0.074, 0.018), (1.45, 0.045, 0.012),
                 (BLADE_LEN, 0.002, 0.002)]
blade_rings = [ring_xy(z, w, t, 4) for z, w, t in blade_profile]
loft(blade_rings, lambda co: (0.25 + co.x / 0.120 * 0.24, 0.02 + co.z / BLADE_LEN * 0.96), smooth=False)

# Guard: swept along X, ends curve toward the blade and get thin.
guard_rings = []
for i in range(13):
    t = i / 12 * 2 - 1
    x = t * 0.34
    z = 0.03 + 0.13 * abs(t) ** 2.2
    thick = 0.048 * (1 - 0.7 * abs(t) ** 1.5) + 0.006
    guard_rings.append([Vector((x, math.cos(math.tau * k / 8 + math.pi / 8) * thick * 0.75,
                                z + math.sin(math.tau * k / 8 + math.pi / 8) * thick)) for k in range(8)])
metal_uv = lambda co: (0.52 + (co.x / 0.34 * 0.5 + 0.5) * 0.21, 0.05 + min(max((co.z + 0.45) / 0.7, 0), 1) * 0.9)
loft(guard_rings, metal_uv, smooth=True)

# Grip.
grip_profile = [(-0.01, 0.030), (-0.08, 0.034), (-0.20, 0.031), (-0.33, 0.027)]
loft([ring_xy(z, r, r * 0.85, 12) for z, r in grip_profile],
     lambda co: (0.76 + (math.atan2(co.y, co.x) / math.tau + 0.5) * 0.23, 0.02 + (-co.z / 0.33) * 0.46),
     smooth=True)

# Pommel.
pommel_profile = [(-0.33, 0.030), (-0.345, 0.050), (-0.375, 0.058), (-0.405, 0.048), (-0.425, 0.022)]
loft([ring_xy(z, r, r, 12) for z, r in pommel_profile], metal_uv, smooth=True)

# Gems on both sides of the guard.
for side in (-1, 1):
    gem_rings = [ring_xy(0.0, r, r, 6) for r in (0.036, 0.022)]
    for depth, ring in zip((0.034, 0.048), gem_rings):
        for p in ring:
            p.y, p.z = side * depth, 0.045 + p.y
    if side == 1:
        gem_rings = [list(reversed(r)) for r in gem_rings]
    loft(gem_rings, lambda co: (0.875 + co.x, 0.75 + (co.z - 0.045)), smooth=False, cap_start=False)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(mesh)
bm.free()

sword = bpy.data.objects.new("Sword", mesh)
col.objects.link(sword)

mat, n, out = new_material("SwordMat")
bsdf = n.new("ShaderNodeBsdfPrincipled")
tex_color = n.new("ShaderNodeTexImage")
tex_color.image = bpy.data.images.load(COLOR_PNG)
tex_emit = n.new("ShaderNodeTexImage")
tex_emit.image = bpy.data.images.load(EMIT_PNG)
n.link(tex_color.outputs["Color"], bsdf.inputs["Base Color"])
n.link(tex_emit.outputs["Color"], bsdf.inputs["Emission Color"])
bsdf.inputs["Emission Strength"].default_value = 1.6
bsdf.inputs["Metallic"].default_value = 0.85
bsdf.inputs["Roughness"].default_value = 0.30
n.link(bsdf.outputs[0], out.inputs["Surface"])
mesh.materials.append(mat)

if MODE == "export":
    bpy.ops.object.select_all(action="DESELECT")
    sword.select_set(True)
    bpy.context.view_layer.objects.active = sword
    bsdf.inputs["Emission Strength"].default_value = 1.0
    target = os.path.join(OUT, "sword.fbx")
    bpy.ops.export_scene.fbx(filepath=target, use_selection=True, object_types={"MESH"},
                             mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True,
                             axis_forward="-Z", axis_up="Y")
    tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
    print(f"EXPORTED {target} triangles={tris}")
    sys.exit(0)

# ---------------------------------------------------------------- animation
THETA0 = math.radians(-118.0)
THETA1 = math.radians(102.0)
SWING_START, SWING_END = 12, 21
GRIP_R = 0.30
TIP_R = GRIP_R + BLADE_LEN


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def swing(frame):
    return smooth((frame - SWING_START) / (SWING_END - SWING_START))


def sword_angle(frame):
    angle = THETA0 + swing(frame) * (THETA1 - THETA0)
    if frame < SWING_START:
        angle += math.radians(14.0) * (1 - smooth(frame / SWING_START))
    if frame > SWING_END:
        angle += math.radians(9.0) * (1 - math.exp(-(frame - SWING_END) / 5.0))
    return angle


plane = bpy.data.objects.new("SlashPlane", None)
col.objects.link(plane)
plane.rotation_euler = (math.radians(-28.0), math.radians(-24.0), math.radians(-16.0))
plane.location = (0.1, 0.0, -0.1)
pivot = bpy.data.objects.new("Pivot", None)
col.objects.link(pivot)
pivot.parent = plane
sword.parent = pivot
sword.location = (0, 0, GRIP_R)
for frame in range(1, END + 1):
    key(pivot, "rotation_euler", frame, (0.0, sword_angle(frame), 0.0))

# ---------------------------------------------------------------- slash trail
mesh = bpy.data.meshes.new("SlashArc")
bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")
SEG_U, SEG_V = 128, 10
grid = []
for i in range(SEG_U + 1):
    u = i / SEG_U
    theta = THETA0 + u * (THETA1 - THETA0)
    r_out = TIP_R + 0.04
    r_in = r_out - (0.06 + 1.25 * math.sin(math.pi * u) ** 0.65)
    row = []
    for j in range(SEG_V + 1):
        v = j / SEG_V
        r = r_in + (r_out - r_in) * v
        row.append((bm.verts.new((r * math.sin(theta), 0.0, r * math.cos(theta))), (u, v)))
    grid.append(row)
for i in range(SEG_U):
    for j in range(SEG_V):
        quad = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
        face = bm.faces.new([q[0] for q in quad])
        for loop, q in zip(face.loops, quad):
            loop[uv_layer].uv = q[1]
bm.to_mesh(mesh)
bm.free()
arc = bpy.data.objects.new("SlashArc", mesh)
col.objects.link(arc)
arc.parent = plane
arc.visible_shadow = False

mat, n, out = new_material("SlashMat")
uv = n.new("ShaderNodeTexCoord").outputs["UV"]
sep = n.new("ShaderNodeSeparateXYZ")
n.link(uv, sep.inputs[0])
u, v = sep.outputs["X"], sep.outputs["Y"]


def tail_value(frame):
    return smooth((frame - 16.0) / 20.0)


def fade_value(frame):
    return 1.0 - smooth((frame - 24.0) / 16.0)


head = n.value("head", [(f, swing(f)) for f in range(1, END + 1)])
tail = n.value("tail", [(f, tail_value(f)) for f in range(1, END + 1)])
fade = n.value("fade", [(f, fade_value(f)) for f in range(1, END + 1)])

span = n.math("MAXIMUM", n.math("SUBTRACT", head, tail), 0.001)
seg = n.math("DIVIDE", n.math("SUBTRACT", u, tail), span, clamp=True)
along = n.math("MULTIPLY", n.math("POWER", seg, 1.4), n.math("LESS_THAN", u, head))
across = n.math("MULTIPLY", n.math("POWER", v, 2.4), n.map_range(v, 1.0, 0.93, 0.0, 1.0, smooth=True))
streak_pos = n.new("ShaderNodeCombineXYZ")
n.link(n.math("MULTIPLY", u, 2.5), streak_pos.inputs[0])
n.link(n.math("MULTIPLY", v, 26.0), streak_pos.inputs[1])
streak = n.noise(streak_pos.outputs[0], 1.0, detail=3.0, dims="2D").outputs["Fac"]
energy = n.math("MULTIPLY", n.math("MULTIPLY", along, across), n.map_range(streak, 0.3, 0.72, 0.2, 1.25))
energy = n.math("MULTIPLY", n.math("MULTIPLY", energy, fade), 1.9)
# A thin bright line on the outer edge, where the tip of the blade passed.
rim = n.math("MULTIPLY", n.math("MULTIPLY", n.map_range(v, 0.86, 0.96, 0.0, 1.0, smooth=True),
                                n.map_range(v, 1.0, 0.97, 0.0, 1.0, smooth=True)),
             n.math("MULTIPLY", n.math("POWER", along, 0.5), fade))
energy = n.math("ADD", energy, n.math("MULTIPLY", rim, 0.9))
colors = n.ramp(energy, [
    (0.00, (0.00, 0.20, 0.05, 1)),
    (0.35, (0.01, 0.85, 0.18, 1)),
    (0.75, (0.30, 1.00, 0.45, 1)),
    (1.00, (0.70, 1.00, 0.75, 1)),
])
emit = n.new("ShaderNodeEmission")
n.link(colors.outputs["Color"], emit.inputs["Color"])
emit.inputs["Strength"].default_value = 1.5
transp = n.new("ShaderNodeBsdfTransparent")
mix = n.new("ShaderNodeMixShader")
n.link(n.math("MULTIPLY", energy, 1.4, clamp=True), mix.inputs[0])
n.link(transp.outputs[0], mix.inputs[1])
n.link(emit.outputs[0], mix.inputs[2])
n.link(mix.outputs[0], out.inputs["Surface"])
mesh.materials.append(mat)

# ---------------------------------------------------------------- sparks
mat, n, out = new_material("SparkMat")
emit = n.new("ShaderNodeEmission")
info = n.new("ShaderNodeObjectInfo")
spark_col = n.ramp(info.outputs["Random"], [
    (0.0, (0.02, 0.9, 0.2, 1)), (0.6, (0.4, 1.0, 0.5, 1)), (1.0, (0.9, 1.0, 0.9, 1))])
n.link(spark_col.outputs["Color"], emit.inputs["Color"])
emit.inputs["Strength"].default_value = 2.2
n.link(emit.outputs[0], out.inputs["Surface"])
spark_mesh = bpy.data.meshes.new("Spark")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
bm.to_mesh(spark_mesh)
bm.free()
spark_mesh.materials.append(mat)

DT = 1.0 / 30.0
for i in range(70):
    birth = random.uniform(SWING_START + 0.5, SWING_END)
    theta = THETA0 + swing(birth) * (THETA1 - THETA0)
    birth = int(round(birth))
    radius = random.uniform(TIP_R - 0.9, TIP_R)
    radial = Vector((math.sin(theta), 0.0, math.cos(theta)))
    tangent = Vector((math.cos(theta), 0.0, -math.sin(theta)))
    pos = radial * radius
    vel = tangent * random.uniform(2.0, 7.0) + radial * random.uniform(0.5, 4.0) \
        + Vector((0, random.uniform(-1.6, 1.6), 0))
    life = random.randint(10, 26)
    size = random.uniform(0.008, 0.02)
    spark = bpy.data.objects.new(f"Spark{i}", spark_mesh)
    col.objects.link(spark)
    spark.parent = plane
    spark.visible_shadow = False
    spark.rotation_mode = "QUATERNION"
    key(spark, "hide_render", birth - 1, True)
    key(spark, "hide_render", birth, False)
    for step in range(life + 1):
        fade_s = 1.0 - step / life
        stretch = max(vel.length * DT * 0.6, size)
        spark.location = pos
        spark.rotation_quaternion = vel.to_track_quat("Z", "Y")
        spark.scale = (size * fade_s, size * fade_s, stretch * (0.3 + 0.7 * fade_s))
        for path in ("location", "rotation_quaternion", "scale"):
            spark.keyframe_insert(path, frame=birth + step)
        vel = vel * 0.90 + Vector((0, 0, -2.5)) * DT
        pos = pos + vel * DT
    key(spark, "hide_render", birth + life, False)
    key(spark, "hide_render", birth + life + 1, True)

# ---------------------------------------------------------------- lights, world, camera
world_nodes = scene.world.node_tree
bg = world_nodes.nodes["Background"]
grad_coord = world_nodes.nodes.new("ShaderNodeTexCoord")
grad_sep = world_nodes.nodes.new("ShaderNodeSeparateXYZ")
grad_ramp = world_nodes.nodes.new("ShaderNodeValToRGB")
grad_ramp.color_ramp.elements[0].position = 0.35
grad_ramp.color_ramp.elements[0].color = (0.01, 0.015, 0.012, 1)
grad_ramp.color_ramp.elements[1].position = 0.9
grad_ramp.color_ramp.elements[1].color = (0.55, 0.75, 0.65, 1)
grad_map = world_nodes.nodes.new("ShaderNodeMapRange")
world_nodes.links.new(grad_coord.outputs["Generated"], grad_sep.inputs[0])
world_nodes.links.new(grad_sep.outputs["Z"], grad_map.inputs[0])
grad_map.inputs[1].default_value = -1.0
grad_map.inputs[2].default_value = 1.0
world_nodes.links.new(grad_map.outputs[0], grad_ramp.inputs[0])
world_nodes.links.new(grad_ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.45

for name, loc, energy, color, size in (
        ("Key", (3.5, -5.0, 4.5), 500, (1.0, 1.0, 1.0), 4.0),
        ("Rim", (-4.0, 3.0, 2.0), 400, (0.3, 1.0, 0.5), 3.0)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.size = size
    light = bpy.data.objects.new(name, data)
    col.objects.link(light)
    light.location = loc
    look_at(light, (0, 0, 0))

if MODE == "flipbook":
    # Camera faces the slash plane, so the result works as a flat sprite.
    sword.hide_render = True
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = (TIP_R + 0.25) * 2
    cam = bpy.data.objects.new("Camera", cam_data)
    col.objects.link(cam)
    cam.parent = plane
    cam.location = (0, -6, 0)
    cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam
else:
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5
    add_camera(scene, (0.3, -8.0, 0.7), (0.1, 0.0, 0.05), lens=50)

render_frames(scene, OUT, FRAMES)
