# Repacks GLB files as glTF JSON with the binary buffer embedded as a data URI,
# so they can be served as .json; updates models/index.json to point at them.
# Usage: python glb_to_json.py <models dir>
import sys, os, json, struct, base64
d = sys.argv[1]
index_path = os.path.join(d, "index.json")
index = json.load(open(index_path))
for m in index:
    if not m["file"].endswith(".glb"):
        continue
    data = open(os.path.join(d, m["file"]), "rb").read()
    offset, gltf, binary = 12, None, b""
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8: offset + 8 + length]
        if kind == 0x4E4F534A: gltf = json.loads(chunk)
        elif kind == 0x004E4942: binary = chunk
        offset += 8 + length
    if binary:
        gltf["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binary).decode()
    out = m["file"][:-4] + ".gltf.json"
    json.dump(gltf, open(os.path.join(d, out), "w"), separators=(",", ":"))
    os.remove(os.path.join(d, m["file"]))
    m["file"] = out
json.dump(index, open(index_path, "w"), indent=1)
print([m["file"] for m in index])
