"""Purple explosion. Usage: python3 explosion.py OUT_DIR [RES] [SAMPLES] [frame ...]"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bmesh
from mathutils import Vector

from common import Nodes, add_camera, key, new_material, render_frames, reset_scene

OUT = sys.argv[1]
RES = int(sys.argv[2]) if len(sys.argv) > 2 else 640
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 48
FRAMES = [int(a) for a in sys.argv[4:]] or None
END = 64

scene = reset_scene(RES, RES, SAMPLES, END)
col = scene.collection
scene.cycles.volume_biased = True
scene.cycles.volume_step_rate = 2.0
scene.cycles.volume_max_steps = 512
scene.cycles.denoising_prefilter = "FAST"
random.seed(7)


def ease_keys(obj, path, keys):
    for frame, value in keys:
        key(obj, path, frame, value)


# ---------------------------------------------------------------- fireball
def build_fireball(name, seed_offset, scale_keys, loc_keys, heat_mul=1.0):
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    dom = bpy.context.active_object
    dom.name = name
    mat, n, out = new_material(name + "Mat")

    coords = n.new("ShaderNodeTexCoord").outputs["Object"]
    p = n.vmath("ADD", coords, (seed_offset, seed_offset * 0.37, -seed_offset * 0.71))

    churn = n.value("churn", [(1, 0.0), (10, 0.55), (END, 1.7)])
    erode = n.value("erode", [(1, -0.6), (9, -0.45), (40, 0.26), (END, 0.60)])
    heat = n.value("heat", [(1, 2.6 * heat_mul), (5, 2.0 * heat_mul), (12, 1.25 * heat_mul),
                            (26, 0.55 * heat_mul), (42, 0.10), (52, 0.0)])
    dens = n.value("dens", [(1, 3.0), (8, 4.5), (30, 3.2), (END, 2.2)])

    # Warp the lookup position so the shape billows instead of staying a ball.
    warp = n.noise(p, 1.15, w=churn, detail=2.0)
    warp_v = n.vmath("SUBTRACT", warp.outputs["Color"], (0.5, 0.5, 0.5))
    p_warp = n.vmath("ADD", coords, n.vmath("SCALE", warp_v, scale=0.85))
    r = n.vmath("LENGTH", p_warp)

    lumps = n.noise(p, 2.4, w=churn, detail=5.0, roughness=0.62).outputs["Fac"]
    rd = n.math("ADD", r, n.math("MULTIPLY", n.math("SUBTRACT", lumps, 0.5), 0.95))
    shape = n.map_range(rd, 0.78, 0.50, 0.0, 1.0, smooth=True)

    holes = n.noise(p, 4.3, w=n.math("MULTIPLY", churn, 1.6), detail=4.0, roughness=0.6).outputs["Fac"]
    # Erosion starts from the outside, so the core lasts longer.
    holes = n.math("SUBTRACT", holes, n.math("MULTIPLY", rd, 0.25))
    eroded = n.map_range(holes, erode, n.math("ADD", erode, 0.22), 0.0, 1.0, smooth=True)
    body = n.math("MULTIPLY", shape, eroded)

    core = n.map_range(rd, 0.80, 0.0, 0.0, 1.0)
    temp = n.math("MULTIPLY", n.math("POWER", core, 0.8), heat)
    temp = n.math("MULTIPLY", temp, n.map_range(holes, 0.15, 0.6, 0.35, 1.3))
    temp = n.math("MULTIPLY", temp, eroded)

    fire = n.ramp(n.map_range(temp, 0.0, 1.6), [
        (0.00, (0.0, 0.0, 0.0, 1)),
        (0.10, (0.10, 0.0, 0.22, 1)),
        (0.30, (0.42, 0.02, 0.85, 1)),
        (0.52, (0.80, 0.08, 1.00, 1)),
        (0.76, (1.00, 0.40, 0.95, 1)),
        (1.00, (1.00, 0.85, 1.00, 1)),
    ])
    fire_strength = n.math("MULTIPLY", n.math("POWER", n.math("MAXIMUM", temp, 0.0), 2.3), 22.0)
    # Fire is thin; smoke is thick. Hot parts absorb less so the core stays visible.
    density = n.math("MULTIPLY", n.math("MULTIPLY", body, dens),
                     n.map_range(temp, 0.2, 1.2, 1.0, 0.25))

    # No light scattering (fast). A direction-based tint gives the smoke its shading.
    lit = n.map_range(n.vmath("DOT_PRODUCT", p_warp, (0.35, -0.45, 0.82)), -0.7, 0.7, 0.0, 1.0)
    smoke = n.ramp(lit, [(0.0, (0.012, 0.004, 0.03, 1)), (0.6, (0.07, 0.025, 0.15, 1)),
                         (1.0, (0.11, 0.045, 0.22, 1))])
    smoke_strength = n.math("MULTIPLY", n.math("MULTIPLY", density, 0.9),
                            n.map_range(holes, 0.1, 0.6, 0.3, 1.25))
    color = n.vmath("ADD", n.vmath("SCALE", fire.outputs["Color"], scale=fire_strength),
                    n.vmath("SCALE", smoke.outputs["Color"], scale=smoke_strength))

    absorb = n.new("ShaderNodeVolumeAbsorption")
    absorb.inputs["Color"].default_value = (0, 0, 0, 1)
    n.link(density, absorb.inputs["Density"])
    emit = n.new("ShaderNodeEmission")
    n.link(color, emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 1.0
    add = n.new("ShaderNodeAddShader")
    n.link(absorb.outputs[0], add.inputs[0])
    n.link(emit.outputs[0], add.inputs[1])
    n.link(add.outputs[0], out.inputs["Volume"])

    dom.data.materials.append(mat)
    for frame, s in scale_keys:
        key(dom, "scale", frame, (s, s, s))
    for frame, loc in loc_keys:
        key(dom, "location", frame, loc)
    return dom


build_fireball("Fireball", 0.0,
               [(1, 0.35), (4, 1.55), (9, 2.15), (22, 2.65), (END, 3.2)],
               [(1, (0, 0, 0)), (END, (0, 0, 0.55))])
# Secondary bursts make the outline less regular.
for i in range(2):
    ang = i * math.tau / 2 + 0.5
    d = Vector((math.cos(ang) * 1.25, math.sin(ang) * 0.6, 0.35 * math.sin(i * 2.1) + 0.15))
    start = 2 + i
    build_fireball(f"Burst{i}", 11.3 * (i + 1),
                   [(1, 0.0), (start, 0.05), (start + 4, 0.85), (start + 10, 1.2), (END, 1.6)],
                   [(start, tuple(d * 0.2)), (start + 8, tuple(d)), (END, tuple(d * 1.35 + Vector((0, 0, 0.4))))],
                   heat_mul=0.85)

# ---------------------------------------------------------------- flash
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24)
flash = bpy.context.active_object
flash.name = "Flash"
bpy.ops.object.shade_smooth()
mat, n, out = new_material("FlashMat")
facing = n.new("ShaderNodeLayerWeight")
facing.inputs["Blend"].default_value = 0.5
soft = n.math("POWER", n.math("SUBTRACT", 1.0, facing.outputs["Facing"]), 4.0)
power = n.value("flash", [(1, 1.0), (3, 0.8), (7, 0.0)])
emit = n.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (0.6, 0.18, 1.0, 1)
emit.inputs["Strength"].default_value = 3.0
transp = n.new("ShaderNodeBsdfTransparent")
mix = n.new("ShaderNodeMixShader")
n.link(n.math("MULTIPLY", soft, power), mix.inputs[0])
n.link(transp.outputs[0], mix.inputs[1])
n.link(emit.outputs[0], mix.inputs[2])
n.link(mix.outputs[0], out.inputs["Surface"])
flash.data.materials.append(mat)
flash.visible_shadow = False
for frame, s in [(1, 0.8), (3, 2.2), (7, 3.0)]:
    key(flash, "scale", frame, (s, s, s))
key(flash, "hide_render", 7, False)
key(flash, "hide_render", 8, True)

# ---------------------------------------------------------------- shockwave ring
mesh = bpy.data.meshes.new("Ring")
bm = bmesh.new()
SEG = 96
uv_layer = bm.loops.layers.uv.new("UVMap")
inner, outer = [], []
for i in range(SEG):
    a = math.tau * i / SEG
    inner.append(bm.verts.new((math.cos(a) * 0.72, math.sin(a) * 0.72, 0)))
    outer.append(bm.verts.new((math.cos(a), math.sin(a), 0)))
for i in range(SEG):
    j = (i + 1) % SEG
    face = bm.faces.new((inner[i], outer[i], outer[j], inner[j]))
    us = (i / SEG, i / SEG, (i + 1) / SEG, (i + 1) / SEG)
    vs = (0.0, 1.0, 1.0, 0.0)
    for loop, u, v in zip(face.loops, us, vs):
        loop[uv_layer].uv = (u, v)
bm.to_mesh(mesh)
bm.free()
ring = bpy.data.objects.new("Shockwave", mesh)
col.objects.link(ring)
mat, n, out = new_material("RingMat")
uv = n.new("ShaderNodeTexCoord").outputs["UV"]
sep = n.new("ShaderNodeSeparateXYZ")
n.link(uv, sep.inputs[0])
across = n.math("MULTIPLY", n.math("POWER", sep.outputs["Y"], 3.0),
                n.map_range(sep.outputs["Y"], 1.0, 0.93, 0.0, 1.0, smooth=True))
streak_pos = n.new("ShaderNodeCombineXYZ")
n.link(n.math("MULTIPLY", sep.outputs["X"], 60.0), streak_pos.inputs[0])
n.link(n.math("MULTIPLY", sep.outputs["Y"], 1.5), streak_pos.inputs[1])
streaks = n.noise(streak_pos.outputs[0], 1.0, detail=3.0, dims="2D").outputs["Fac"]
ring_power = n.value("ring", [(1, 0.0), (2, 1.0), (10, 0.75), (24, 0.0)])
alpha = n.math("MULTIPLY", n.math("MULTIPLY", across, n.map_range(streaks, 0.3, 0.7, 0.35, 1.0)), ring_power, clamp=True)
emit = n.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (0.55, 0.12, 1.0, 1)
emit.inputs["Strength"].default_value = 3.5
transp = n.new("ShaderNodeBsdfTransparent")
mix = n.new("ShaderNodeMixShader")
n.link(alpha, mix.inputs[0])
n.link(transp.outputs[0], mix.inputs[1])
n.link(emit.outputs[0], mix.inputs[2])
n.link(mix.outputs[0], out.inputs["Surface"])
ring.data.materials.append(mat)
ring.visible_shadow = False
ring.location = (0, 0, -0.25)
for frame, s in [(1, 0.4), (5, 2.0), (12, 3.0), (24, 3.6)]:
    key(ring, "scale", frame, (s, s, s))
key(ring, "hide_render", 24, False)
key(ring, "hide_render", 25, True)

# ---------------------------------------------------------------- sparks
mat, n, out = new_material("SparkMat")
emit = n.new("ShaderNodeEmission")
info = n.new("ShaderNodeObjectInfo")
spark_col = n.ramp(info.outputs["Random"], [
    (0.0, (0.55, 0.12, 1.0, 1)), (0.6, (0.95, 0.45, 1.0, 1)), (1.0, (1.0, 0.92, 1.0, 1))])
n.link(spark_col.outputs["Color"], emit.inputs["Color"])
emit.inputs["Strength"].default_value = 9.0
n.link(emit.outputs[0], out.inputs["Surface"])
spark_mat = mat

spark_mesh = bpy.data.meshes.new("Spark")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
bm.to_mesh(spark_mesh)
bm.free()
spark_mesh.materials.append(spark_mat)

GRAVITY = Vector((0, 0, -4.5))
for i in range(90):
    direction = Vector((random.gauss(0, 1), random.gauss(0, 0.8), random.gauss(0.25, 0.8))).normalized()
    speed = random.uniform(4.0, 10.0)
    life = random.randint(16, 40)
    birth = random.randint(1, 4)
    size = random.uniform(0.02, 0.045)
    spark = bpy.data.objects.new(f"Spark{i}", spark_mesh)
    col.objects.link(spark)
    spark.visible_shadow = False
    spark.rotation_mode = "QUATERNION"
    pos = direction * 0.4
    vel = direction * speed
    dt = 1.0 / 30.0
    key(spark, "hide_render", birth - 1, True)
    key(spark, "hide_render", birth, False)
    for step in range(life + 1):
        frame = birth + step
        fade = 1.0 - step / life
        stretch = max(vel.length * dt * 0.55, size)
        spark.location = pos
        spark.rotation_quaternion = vel.to_track_quat("Z", "Y")
        spark.scale = (size * fade, size * fade, stretch * (0.3 + 0.7 * fade))
        for path in ("location", "rotation_quaternion", "scale"):
            spark.keyframe_insert(path, frame=frame)
        vel = vel * 0.90 + GRAVITY * dt
        pos = pos + vel * dt
    key(spark, "hide_render", birth + life, False)
    key(spark, "hide_render", birth + life + 1, True)

# ---------------------------------------------------------------- lights and camera
light_data = bpy.data.lights.new("Key", "AREA")
light_data.energy = 2500
light_data.size = 6
light_data.color = (0.75, 0.6, 1.0)
light = bpy.data.objects.new("Key", light_data)
col.objects.link(light)
light.location = (5, -6, 8)
from common import look_at
look_at(light, (0, 0, 0.3))

cam = add_camera(scene, (0, -11.5, 1.9), (0, 0, 0.35), lens=50)
cam.data.sensor_fit = "HORIZONTAL"

render_frames(scene, OUT, FRAMES)
