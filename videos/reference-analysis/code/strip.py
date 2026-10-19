import sys, json, subprocess, numpy as np, os
from PIL import Image, ImageDraw
t0, t1, n = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]); cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
out = sys.argv[5] if len(sys.argv) > 5 else "strip.png"
d = np.load("diffs.npy"); uniq = [0] + [i+1 for i, x in enumerate(d) if x >= .02]
cand = [u for u in uniq if t0 <= u/59.94 <= t1]
idx = [cand[int(i)] for i in np.linspace(0, len(cand)-1, n)] if len(cand) > n else cand
sel = "+".join(f"eq(n\\,{k})" for k in idx)
os.makedirs("tmp", exist_ok=True)
for f in os.listdir("tmp"): os.remove("tmp/"+f)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "ref.mov", "-vf", f"select='{sel}'", "-vsync", "0", "tmp/s_%03d.png"], check=True)
ims = [Image.open(f"tmp/s_{i+1:03d}.png").convert("RGB") for i in range(len(idx))]
# auto crop: union bbox of non-white/non-ground pixels
bb = None
for im in ims:
    a = np.asarray(im).astype(int); nz = (np.abs(a - 255).sum(2) > 120); nz[int(.80*a.shape[0]):int(.82*a.shape[0]) + 14, :] = False
    ys, xs = np.nonzero(nz)
    if len(xs) == 0: continue
    b = (xs.min(), ys.min(), xs.max(), ys.max()); bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
pad = 20; W, H = ims[0].size
bb = (max(0, bb[0]-pad), max(0, bb[1]-pad), min(W, bb[2]+pad), min(H, int(.84*H)))
crops = [im.crop(bb) for im in ims]; cw, ch = crops[0].size
sc = min(1.0, 460/cw) if cw > 460 else min(2.5, 460/cw)
cw2, ch2 = int(cw*sc), int(ch*sc); rows = (len(crops) + cols - 1)//cols
m = Image.new("RGB", (cw2*cols, ch2*rows), "white"); dr = ImageDraw.Draw(m)
for i, c in enumerate(crops):
    x, y = (i % cols)*cw2, (i//cols)*ch2; m.paste(c.resize((cw2, ch2)), (x, y)); dr.rectangle([x, y, x+cw2-1, y+ch2-1], outline="#cccccc")
    dr.text((x+6, y+4), f"{idx[i]/59.94:.2f}s #{idx[i]}", fill="black")
m.save(out); print(m.size, [round(k/59.94, 2) for k in idx])
