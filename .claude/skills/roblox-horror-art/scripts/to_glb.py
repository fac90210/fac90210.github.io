# Converts model files to GLB for the web viewer and writes models/index.json.
# Usage: python to_glb.py <out_dir> <model files...>
import sys, os, json, time
import bpy
out_dir, sources = sys.argv[1], sys.argv[2:]
index_path = os.path.join(out_dir, "index.json")
index = json.load(open(index_path)) if os.path.exists(index_path) else []
by_name = {m["file"]: m for m in index}
for src in sources:
    name, ext = os.path.splitext(os.path.basename(src))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    {".fbx": lambda: bpy.ops.import_scene.fbx(filepath=src),
     ".obj": lambda: bpy.ops.wm.obj_import(filepath=src),
     ".glb": lambda: bpy.ops.import_scene.gltf(filepath=src),
     ".gltf": lambda: bpy.ops.import_scene.gltf(filepath=src),
     ".stl": lambda: bpy.ops.wm.stl_import(filepath=src),
     ".blend": lambda: bpy.ops.wm.open_mainfile(filepath=src)}[ext.lower()]()
    dg = bpy.context.evaluated_depsgraph_get()
    tris = verts = 0
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
            tris += len(m.loop_triangles); verts += len(m.vertices)
    out = os.path.join(out_dir, name + ".glb")
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True)
    by_name[name + ".glb"] = {"file": name + ".glb", "name": name, "source": os.path.basename(src),
        "format": ext[1:].upper(), "tris": tris, "verts": verts,
        "bytes": os.path.getsize(src), "made": int(os.path.getmtime(src) * 1000)}
json.dump(sorted(by_name.values(), key=lambda m: -m["made"]), open(index_path, "w"), indent=1)
print(json.dumps(list(by_name.values())))
