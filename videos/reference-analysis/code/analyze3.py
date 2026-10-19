import json, numpy as np
from fitlib import *
from PIL import Image
from scipy import ndimage as ndi
prop = json.load(open("prop.json")); fits = json.load(open("fits.json")); N = len(fits); T = np.array([f["t"] for f in fits])
R = np.load("red.npy"); B = np.load("blue.npy"); zoom = np.load("zoom.npy")
# ---------- relative-pose holds (body-relative joint offsets, independent of camera)
def rel(P):
    out = np.full((N, 12), np.nan)
    for d in range(N):
        if np.isnan(P[d, 0]): continue
        j = joints(P[d], prop); s = P[d, 2]; hip = j["hip"]
        out[d] = np.concatenate([(j[k] - hip)/s for k in ("head", "hA", "hB", "fA", "fB", "kA")[:6]])
    return out
RR, RB = rel(R), rel(B)
def hold_runs(Rl, thr=.02, minlen=4):
    runs = []; d = 1
    while d < N:
        a, b = Rl[d], Rl[d-1]
        if not np.isnan(a).any() and not np.isnan(b).any() and np.abs(a - b).max() < thr:
            e = d
            while e + 1 < N and not np.isnan(Rl[e+1]).any() and np.abs(Rl[e+1] - Rl[e]).max() < thr: e += 1
            if e - d + 1 >= minlen: runs.append((d-1, e, round(float(T[e] - T[d-1]), 2)))
            d = e + 1
        else: d += 1
    return runs
print("RED pose holds (start_d, end_d, seconds):", hold_runs(RR)); print("BLUE pose holds:", hold_runs(RB))
# ---------- effects
fx = []
for d in range(N):
    img = Image.open(FR[UNIQ[d]]).convert("RGB"); a = np.asarray(img).astype(int); r_, g_, b_ = a[..., 0], a[..., 1], a[..., 2]
    red, blue = masks(img); strong = ndi.binary_dilation(red | blue, iterations=3)
    light_blue = (b_ > 150) & (b_ - r_ > 14) & (b_ - g_ > 8) & ~strong
    light_red = (r_ > 170) & (r_ - g_ > 25) & (r_ - b_ > 25) & ~strong
    # speed lines: long horizontal runs of light-blue
    rows = 0
    for y in range(0, H, 2):
        row = light_blue[y]
        if row.sum() > 120:
            lab, n = ndi.label(row)
            if n and max(ndi.sum(row, lab, range(1, n+1))) > 110: rows += 1
    lb_area = int(ndi.binary_opening(light_blue, iterations=2).sum()); lr_area = int(ndi.binary_opening(light_red, iterations=2).sum())
    fx.append(dict(d=d, speedrows=rows, ghost_blue=lb_area, ghost_red=lr_area))
sl = [f["d"] for f in fx if f["speedrows"] >= 5]
print("SPEED-LINE drawings:", sl, " total", len(sl))
gb = [f["d"] for f in fx if f["ghost_blue"] > 200 and f["speedrows"] < 5]; gr = [f["d"] for f in fx if f["ghost_red"] > 200 and f["speedrows"] < 5]
print("BLUE ghost/swoosh drawings:", gb); print("RED ghost/swoosh drawings:", gr)
json.dump(fx, open("effects.json", "w"))
