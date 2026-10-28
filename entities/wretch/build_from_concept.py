"""Turn the TripoSR mesh of the Wretch into a textured, Roblox-ready model.

1. Stand the mesh up (TripoSR writes Z-up, facing +X), scale it to 9 studs.
2. Keep it as HIGH_Wretch; decimate a copy to LOW_Wretch and UV-unwrap it.
3. Bake LOW's surface position, normal and TripoSR vertex colour into maps.
4. Project the concept sheet's front, back and side views onto every texel,
   weighting each view by how squarely the surface faces it and skipping
   texels another part of the body hides from that view (ray test). Texels no
   view sees keep TripoSR's colour.
5. Bake HIGH -> LOW normals and add fine detail from the colour map's
   luminance, write roughness and metalness, and save everything.

Run:  python build_from_concept.py <tsr.obj> <cutout prefix> <out dir> [turn_degrees=-90]
"""
import os
import sys
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

src, cut_prefix, out_dir = sys.argv[-4], sys.argv[-3], sys.argv[-2]
turn = float(sys.argv[-1])
os.makedirs(out_dir, exist_ok=True)
STUD = 0.28
HEIGHT = 9 * STUD
TEX = 1024
LOW_TRIS = 14000

# ---------- 1. Import and stand up ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30
for name in ("REF", "HIGH", "LOW", "RIG", "EXPORT"):
    scene.collection.children.link(bpy.data.collections.new(name))
bpy.ops.wm.obj_import(filepath=src, forward_axis="Y", up_axis="Z")
high = bpy.context.selected_objects[0]
high.name = high.data.name = "HIGH_Wretch"
for c in high.users_collection:
    c.objects.unlink(high)
bpy.data.collections["HIGH"].objects.link(high)
bpy.context.view_layer.objects.active = high
high.rotation_euler = (0, 0, math.radians(turn))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
s = HEIGHT / high.dimensions.z
high.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
co = np.array([v.co[:] for v in high.data.vertices])
offset = Vector((-(co[:, 0].max() + co[:, 0].min()) / 2, -(co[:, 1].max() + co[:, 1].min()) / 2, -co[:, 2].min()))
high.data.transform(__import__("mathutils").Matrix.Translation(offset))
high.data.update()
for p in high.data.polygons:
    p.use_smooth = True
# The scikit-image marching cubes winds faces opposite to TripoSR's own, so the
# normals point inward; recompute them to face outward.
for o in bpy.context.view_layer.objects:
    o.select_set(o == high)
bpy.context.view_layer.objects.active = high
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")

# ---------- 2. LOW: decimated copy with UVs ----------
low = high.copy()
low.data = high.data.copy()
low.name = low.data.name = "LOW_Wretch"
bpy.data.collections["LOW"].objects.link(low)
for c in list(low.users_collection):
    if c.name != "LOW":
        c.objects.unlink(low)
for o in bpy.context.view_layer.objects:
    o.select_set(o == low)
bpy.context.view_layer.objects.active = low
dec = low.modifiers.new("Decimate", "DECIMATE")
dec.ratio = LOW_TRIS / len(low.data.polygons)
bpy.ops.object.modifier_apply(modifier="Decimate")
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")
print("LOW tris", sum(len(p.vertices) - 2 for p in low.data.polygons))


# ---------- 3. Bake helper maps ----------
def image(name, float_buffer=True, color=(0, 0, 0, 0)):
    img = bpy.data.images.new(name, TEX, TEX, alpha=True, float_buffer=float_buffer)
    img.generated_color = color
    if float_buffer:
        img.colorspace_settings.name = "Non-Color"
    return img


scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 1
scene.render.bake.margin = 0  # only real texels; seams are dilated in numpy


def bake_emit(obj, build, img):
    """Bakes an emission shader (built by `build(nodes, links, emission)`) into img."""
    mat = bpy.data.materials.new(f"bake_{img.name}")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    emit = nt.nodes.new("ShaderNodeEmission")
    outp = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(emit.outputs[0], outp.inputs[0])
    build(nt.nodes, nt.links, emit)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.nodes.active = tex
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for o in bpy.context.view_layer.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type="EMIT")


def as_array(img):
    a = np.empty(TEX * TEX * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(TEX, TEX, 4)


pos_img, nrm_img, vc_img = image("pos"), image("nrm"), image("vc")


# Bakes clamp negative values, so vectors are packed into 0..1 and unpacked after:
# positions as p * 0.25 + 0.5 (covers -2..2 m), normals as n * 0.5 + 0.5.
def packed(output, scale):
    def build(nodes, links, emit):
        g = nodes.new("ShaderNodeNewGeometry")
        m = nodes.new("ShaderNodeVectorMath")
        m.operation = "MULTIPLY_ADD"
        m.inputs[1].default_value = (scale, scale, scale)
        m.inputs[2].default_value = (0.5, 0.5, 0.5)
        links.new(g.outputs[output], m.inputs[0])
        links.new(m.outputs["Vector"], emit.inputs["Color"])
    return build


geo_position, geo_normal = packed("Position", 0.25), packed("True Normal", 0.5)


def vertex_colour(nodes, links, emit):
    a = nodes.new("ShaderNodeVertexColor")
    a.layer_name = low.data.color_attributes[0].name
    links.new(a.outputs["Color"], emit.inputs["Color"])


bake_emit(low, geo_position, pos_img)
bake_emit(low, geo_normal, nrm_img)
bake_emit(low, vertex_colour, vc_img)
pos, nrm, vc = as_array(pos_img), as_array(nrm_img), as_array(vc_img)
covered = pos[..., :3].sum(axis=2) > 1e-4  # packed values are never 0; unbaked texels are
pos[..., :3] = (pos[..., :3] - 0.5) / 0.25
nrm[..., :3] = (nrm[..., :3] - 0.5) / 0.5
print("texels on the mesh", int(covered.sum()))

# ---------- 4. Project the concept views ----------
from PIL import Image  # noqa: E402  (installed in the Blender venv for this step)


def load_view(name):
    a = np.asarray(Image.open(f"{cut_prefix}_{name}.png").convert("RGBA")).astype(np.float32) / 255
    ys, xs = np.nonzero(a[..., 3] > 0.5)
    return a, (xs.min(), xs.max(), ys.min(), ys.max())


views = {n: load_view(n) for n in ("front", "back", "side")}
mesh_co = np.array([v.co[:] for v in high.data.vertices])
lo, hi = mesh_co.min(axis=0), mesh_co.max(axis=0)
bvh = BVHTree.FromObject(high, bpy.context.evaluated_depsgraph_get())

# Each projection: which mesh axis runs across the image, whether it is flipped,
# the direction towards that view's camera, and which normal component faces it.
PROJ = [
    ("front", 0, False, Vector((0, -1, 0)), lambda n: np.clip(-n[..., 1], 0, None)),
    ("back", 0, True, Vector((0, 1, 0)), lambda n: np.clip(n[..., 1], 0, None)),
    ("side", 1, False, Vector((1, 0, 0)), lambda n: np.clip(n[..., 0], 0, None)),   # its left side
    ("side", 1, True, Vector((-1, 0, 0)), lambda n: np.clip(-n[..., 0], 0, None)),  # right: mirrored
]

idx = np.argwhere(covered)
P, N = pos[covered][:, :3], nrm[covered][:, :3]
N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
acc = np.zeros((len(P), 3), dtype=np.float32)
wsum = np.zeros(len(P), dtype=np.float32)


def sample(a, u, v):
    """Bilinear sample of image a at pixel coords (u, v); returns rgb and alpha."""
    h, w = a.shape[:2]
    u = np.clip(u, 0, w - 1.001)
    v = np.clip(v, 0, h - 1.001)
    u0, v0 = u.astype(int), v.astype(int)
    fu, fv = (u - u0)[:, None], (v - v0)[:, None]
    c = (a[v0, u0] * (1 - fu) * (1 - fv) + a[v0, u0 + 1] * fu * (1 - fv)
         + a[v0 + 1, u0] * (1 - fu) * fv + a[v0 + 1, u0 + 1] * fu * fv)
    return c[:, :3], c[:, 3]


for name, axis, flip, toward, facing in PROJ:
    img, (x0, x1, y0, y1) = views[name]
    w = facing(N) ** 3
    across = (P[:, axis] - lo[axis]) / (hi[axis] - lo[axis])
    if flip:
        across = 1 - across
    up = (P[:, 2] - lo[2]) / (hi[2] - lo[2])
    u = x0 + across * (x1 - x0)
    v = y1 - up * (y1 - y0)
    rgb, alpha = sample(img, u, v)
    w = w * (alpha > 0.5)
    # Occlusion: a texel only takes this view if nothing of the body is in front of it.
    # LOW sits a few mm inside or outside HIGH after decimation, so hits within
    # SELF of the start are its own surface, not something in front of it.
    SELF = 0.012 * HEIGHT
    for i in np.flatnonzero(w > 0.02):
        start = Vector(P[i]) + toward * SELF
        if bvh.ray_cast(start, toward, 3.0)[0] is not None:
            w[i] = 0
    acc += rgb * w[:, None]
    wsum += w
    print(f"projected {name}{' (mirrored)' if flip and name == 'side' else ''}: {int((w > 0.02).sum())} texels")

fallback = vc[covered][:, :3]
blend = np.clip(wsum / 0.15, 0, 1)[:, None]  # weak coverage fades into TripoSR's colour
colour = np.where(wsum[:, None] > 0, acc / np.maximum(wsum[:, None], 1e-6), fallback)
colour = colour * blend + fallback * (1 - blend)
print("texels no view saw (TripoSR colour):", int((wsum <= 0).sum()))

albedo = np.zeros((TEX, TEX, 4), dtype=np.float32)
albedo[idx[:, 0], idx[:, 1], :3] = colour
albedo[idx[:, 0], idx[:, 1], 3] = 1


def dilate(a, mask, steps=8):
    """Grows texels outward across UV seams so mipmaps don't bleed background."""
    from scipy import ndimage
    a, mask = a.copy(), mask.copy()
    for _ in range(steps):
        grown = ndimage.binary_dilation(mask)
        new = grown & ~mask
        if not new.any():
            break
        total = np.zeros_like(a[..., :3])
        count = np.zeros(mask.shape, dtype=np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            m = np.roll(mask, (dy, dx), axis=(0, 1))
            total += np.roll(a[..., :3], (dy, dx), axis=(0, 1)) * m[..., None]
            count += m
        fill = new & (count > 0)
        a[fill, :3] = total[fill] / count[fill][:, None]
        a[fill, 3] = 1
        mask |= fill
    return a


albedo = dilate(albedo, covered, 12)
# The concept already has its studio lighting painted in; the game lights it again,
# so lift it towards a flatter, brighter albedo.
albedo[..., :3] = np.clip(albedo[..., :3] * 1.35 + 0.02, 0, 1)


def save(arr, name, srgb=True):
    """Saves a top-down numpy image (row 0 = top) as PNG."""
    rgb = arr[..., :3] if arr.ndim == 3 else np.repeat(arr[..., None], 3, axis=2)
    data = np.clip(rgb, 0, 1)
    if not srgb:
        data = data
    Image.fromarray((data[::-1] * 255).round().astype(np.uint8)).save(os.path.join(out_dir, name))


# Blender images are bottom-up; numpy rows here follow Blender, so flip on save.
save(albedo, "Wretch_Color.png")

# ---------- 5. Normal, roughness, metalness ----------
nm_img = image("normal_bake", float_buffer=False, color=(0.5, 0.5, 1, 1))
nm_img.colorspace_settings.name = "Non-Color"
mat = bpy.data.materials.new("bake_normal")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = nm_img
mat.node_tree.nodes.active = tex
low.data.materials.clear()
low.data.materials.append(mat)
for o in bpy.context.view_layer.objects:
    o.select_set(o in (low, high))
bpy.context.view_layer.objects.active = low
scene.render.bake.use_selected_to_active = True
scene.render.bake.cage_extrusion = 0.01 * HEIGHT
scene.render.bake.max_ray_distance = 0.03 * HEIGHT
scene.render.bake.normal_space = "TANGENT"
scene.render.bake.margin = 8
bpy.ops.object.bake(type="NORMAL")  # Blender bakes OpenGL (Y+), what Roblox reads
normal = as_array(nm_img)[..., :3]

# Fine detail: treat the colour map's darkness as cavities (scales, ribs, wrinkles).
luma = albedo[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
from scipy import ndimage  # noqa: E402
height = ndimage.gaussian_filter(luma, 1.0) - ndimage.gaussian_filter(luma, 6.0)
gy, gx = np.gradient(height)
strength = 6.0
detail = np.dstack([-gx * strength, -gy * strength, np.ones_like(gx)])
detail /= np.linalg.norm(detail, axis=2, keepdims=True)
base = normal * 2 - 1
combined = np.dstack([base[..., 0] + detail[..., 0], base[..., 1] + detail[..., 1], base[..., 2]])
combined /= np.maximum(np.linalg.norm(combined, axis=2, keepdims=True), 1e-6)
save(combined * 0.5 + 0.5, "Wretch_Normal.png")

# Roughness: scaly skin is mid-rough, darker cavities rougher; red wet areas (mouth,
# tongue, gums) and the bright bone of claws/teeth are smoother.
r, g, b = albedo[..., 0], albedo[..., 1], albedo[..., 2]
wet = np.clip((r - np.maximum(g, b)) * 4, 0, 1)
bone = np.clip((luma - 0.45) * 4, 0, 1)
rough = 0.62 + (0.25 - luma) * 0.4 - 0.4 * wet - 0.2 * bone
save(np.clip(rough, 0.08, 0.95), "Wretch_Roughness.png", srgb=False)
save(np.zeros_like(rough), "Wretch_Metalness.png", srgb=False)
# Emissive mask: the glowing red eyes, the brightest saturated red.
eyes = np.clip((r - 0.45) * 5, 0, 1) * np.clip((r - 2.2 * g) * 5, 0, 1)
save(eyes, "Wretch_Emissive.png", srgb=False)

# ---------- Final material on LOW, save ----------
scene.render.bake.use_selected_to_active = False
mat = bpy.data.materials.new("Wretch")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]


def tex_node(file, non_color=False):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(out_dir, file))
    if non_color:
        t.image.colorspace_settings.name = "Non-Color"
    return t


nt.links.new(tex_node("Wretch_Color.png").outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tex_node("Wretch_Roughness.png", True).outputs["Color"], bsdf.inputs["Roughness"])
nt.links.new(tex_node("Wretch_Metalness.png", True).outputs["Color"], bsdf.inputs["Metallic"])
nmap = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tex_node("Wretch_Normal.png", True).outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
em = tex_node("Wretch_Emissive.png", True)
nt.links.new(em.outputs["Color"], bsdf.inputs["Emission Strength"])
bsdf.inputs["Emission Color"].default_value = (1.0, 0.08, 0.02, 1)
low.data.materials.clear()
low.data.materials.append(mat)
high.hide_render = True
low["entity_height"] = HEIGHT
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "Wretch.blend"))
print("saved", os.path.join(out_dir, "Wretch.blend"))
