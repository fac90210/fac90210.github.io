import json, math, numpy as np
from fitlib import *
prop = json.load(open("prop.json")); fits = json.load(open("fits.json")); N = len(fits)
T = np.array([f["t"] for f in fits])
def angdiff(a, b): return ((a - b + 180) % 360) - 180
series = {}
for who in ("red", "blue"):
    P = np.full((N, 12), np.nan)
    for d, f in enumerate(fits):
        if f[who]: P[d] = f[who]["p"]
    # resolve A/B limb swaps by continuity
    for d in range(1, N):
        if np.isnan(P[d, 0]) or np.isnan(P[d-1, 0]): continue
        for (i, j) in ((4, 6), (8, 10)):
            cur = (P[d, i:i+2], P[d, j:j+2]); prv = (P[d-1, i:i+2], P[d-1, j:j+2])
            keep = sum(abs(angdiff(cur[0][k], prv[0][k])) + abs(angdiff(cur[1][k], prv[1][k])) for k in range(2))
            swap = sum(abs(angdiff(cur[1][k], prv[0][k])) + abs(angdiff(cur[0][k], prv[1][k])) for k in range(2))
            if swap + 20 < keep: P[d, i:i+2], P[d, j:j+2] = cur[1].copy(), cur[0].copy()
    series[who] = P
np.save("red.npy", series["red"]); np.save("blue.npy", series["blue"])
out = {}
JN = ["torso", "thighA", "shinA", "thighB", "shinB", "uarmA", "farmA", "uarmB", "farmB"]
for who in ("red", "blue"):
    P = series[who]; valid = ~np.isnan(P[:, 0]); out[who] = {"drawings": int(valid.sum())}
    # angular speed per drawing (deg/drawing) for consecutive valid drawings
    cols = [3, 4, 5, 6, 7, 8, 9, 10, 11]; sp = []
    for d in range(1, N):
        if valid[d] and valid[d-1]: sp.append([abs(angdiff(P[d, c], P[d-1, c])) for c in cols])
    sp = np.array(sp)
    out[who]["ang_speed_deg_per_drawing"] = {JN[i]: dict(median=round(float(np.median(sp[:, i])), 1), p90=round(float(np.percentile(sp[:, i], 90)), 1), p99=round(float(np.percentile(sp[:, i], 99)), 1), max=round(float(sp[:, i].max()), 1)) for i in range(9)}
    # hip speed normalised by figure scale s (body-heights per drawing)
    v = []
    for d in range(1, N):
        if valid[d] and valid[d-1]: v.append(np.hypot(P[d, 0] - P[d-1, 0], P[d, 1] - P[d-1, 1])/P[d, 2])
    v = np.array(v); out[who]["hip_speed_Hper_drawing"] = dict(median=round(float(np.median(v)), 3), p90=round(float(np.percentile(v, 90)), 3), max=round(float(v.max()), 3))
json.dump(out, open("stats1.json", "w"), indent=1)
print(json.dumps(out, indent=1))
