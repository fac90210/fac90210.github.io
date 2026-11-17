"""Shared helpers for the VFX scenes (Blender 5.x, Cycles on CPU)."""
import bpy


def reset_scene(res_x, res_y, samples, frame_end, fps=30):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.cycles.volume_bounces = 1
    scene.cycles.transparent_max_bounces = 16
    scene.render.threads_mode = "AUTO"
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scene.world = world
    return scene


class Nodes:
    """Small wrapper to build shader node graphs with less text."""

    def __init__(self, tree):
        self.tree = tree
        self.nodes = tree.nodes
        self.links = tree.links

    def new(self, kind, **props):
        node = self.nodes.new(kind)
        for key, value in props.items():
            setattr(node, key, value)
        return node

    def link(self, src, dst):
        self.links.new(src, dst)

    def _set(self, socket, value):
        if hasattr(value, "is_linked") or isinstance(value, bpy.types.NodeSocket):
            self.link(value, socket)
        else:
            socket.default_value = value

    def math(self, op, a, b=None, c=None, clamp=False):
        node = self.new("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._set(node.inputs[0], a)
        if b is not None:
            self._set(node.inputs[1], b)
        if c is not None:
            self._set(node.inputs[2], c)
        return node.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        node = self.new("ShaderNodeVectorMath", operation=op)
        self._set(node.inputs[0], a)
        if b is not None:
            self._set(node.inputs[1], b)
        if scale is not None:
            self._set(node.inputs["Scale"], scale)
        return node.outputs["Value"] if op in ("LENGTH", "DOT_PRODUCT") else node.outputs[0]

    def map_range(self, value, from_min, from_max, to_min=0.0, to_max=1.0, smooth=False):
        node = self.new("ShaderNodeMapRange")
        node.interpolation_type = "SMOOTHSTEP" if smooth else "LINEAR"
        node.clamp = True
        for index, item in enumerate((value, from_min, from_max, to_min, to_max)):
            self._set(node.inputs[index], item)
        return node.outputs[0]

    def noise(self, vector, scale, w=None, detail=4.0, roughness=0.55, dims="4D"):
        node = self.new("ShaderNodeTexNoise", noise_dimensions=dims)
        self._set(node.inputs["Vector"], vector)
        self._set(node.inputs["Scale"], scale)
        if w is not None and dims == "4D":
            self._set(node.inputs["W"], w)
        self._set(node.inputs["Detail"], detail)
        self._set(node.inputs["Roughness"], roughness)
        return node

    def ramp(self, fac, stops, interpolation="LINEAR"):
        node = self.new("ShaderNodeValToRGB")
        ramp = node.color_ramp
        ramp.interpolation = interpolation
        while len(ramp.elements) < len(stops):
            ramp.elements.new(0.5)
        for element, (pos, color) in zip(ramp.elements, stops):
            element.position = pos
            element.color = color
        self._set(node.inputs[0], fac)
        return node

    def value(self, name, keys):
        """Animated value node. keys = [(frame, value), ...]"""
        node = self.new("ShaderNodeValue")
        node.label = node.name = name
        for frame, val in keys:
            node.outputs[0].default_value = val
            node.outputs[0].keyframe_insert("default_value", frame=frame)
        return node.outputs[0]


def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nodes = Nodes(mat.node_tree)
    out = nodes.new("ShaderNodeOutputMaterial")
    return mat, nodes, out


def key(obj, path, frame, value, index=-1):
    setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame, index=index)


def look_at(obj, target):
    from mathutils import Vector
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(scene, location, target, lens=50.0):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = location
    look_at(cam, target)
    scene.camera = cam
    return cam


def render_frames(scene, out_dir, frames=None):
    import os
    os.makedirs(out_dir, exist_ok=True)
    frames = frames or range(scene.frame_start, scene.frame_end + 1)
    for frame in frames:
        path = os.path.join(out_dir, f"{frame:04d}.png")
        if os.path.exists(path):
            continue
        scene.frame_set(frame)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"FRAME_DONE {frame}", flush=True)
