# Image -> 3D with TripoSR on CPU. Usage: python run.py <rgba.png> <out.obj> [resolution=256]
import sys, time
import numpy as np
import torch
from PIL import Image
from tsr.system import TSR
from tsr.utils import resize_foreground

src, out = sys.argv[1], sys.argv[2]
res = int(sys.argv[3]) if len(sys.argv) > 3 else 256
torch.set_num_threads(4)
t = time.time()
model = TSR.from_pretrained("weights", config_name="config.yaml", weight_name="model.ckpt")
model.renderer.set_chunk_size(8192)
image = resize_foreground(Image.open(src), 0.85)
a = np.array(image).astype(np.float32) / 255.0
a = a[:, :, :3] * a[:, :, 3:4] + (1 - a[:, :, 3:4]) * 0.5
image = Image.fromarray((a * 255.0).astype(np.uint8))
print("loaded", round(time.time() - t, 1), "s")
with torch.no_grad():
    codes = model([image], device="cpu")
    print("encoded", round(time.time() - t, 1), "s")
    mesh = model.extract_mesh(codes, resolution=res)[0]
print("mesh", len(mesh.vertices), "verts", len(mesh.faces), "faces", round(time.time() - t, 1), "s")
mesh.export(out)
