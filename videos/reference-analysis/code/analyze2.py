import json, math, numpy as np
from fitlib import *
prop = json.load(open("prop.json")); fits = json.load(open("fits.json")); N = len(fits)
T = np.array([f["t"] for f in fits]); R = np.load("red.npy"); B = np.load("blue.npy")
def pts(P):
    out = np.full((N, 7, 2), np.nan)   # head, hip, handA, handB, footA, footB, shoulder
    for d in range(N):
        if np.isnan(P[d, 0]): continue
        j = joints(P[d], prop); out[d] = [j["head"], j["hip"], j["hA"], j["hB"], j["fA"], j["fB"], j["sh"]]
    return out
PR, PB = pts(R), pts(B)
loss = lambda who: np.array([f[who]["loss"] if f[who] else np.nan for f in fits])
LR, LB = loss("red"), loss("blue")
sr, sb = R[:, 2], B[:, 2]
# --- camera zoom proxy: scale s of whichever figure is present (red preferred), relative to median of first standing frames
base = np.nanmedian(np.where(np.arange(N) < 30, sr, np.nan))
zoom = np.where(~np.isnan(sr), sr, sb)/base
print("camera scale s relative to opening (1.0): min %.2f max %.2f" % (np.nanmin(zoom), np.nanmax(zoom)))
zd = np.abs(np.diff(zoom)); big = [(int(d+1), round(float(zoom[d]), 2), round(float(zoom[d+1]), 2)) for d in range(N-1) if zd[d] > .45 and not np.isnan(zd[d])]
print("abrupt zoom cuts (>0.45 change between consecutive drawings):", len(big)); print(big[:40])
# --- speeds per drawing normalised by figure size
def speed(Pt, s):
    v = np.full(N, np.nan)
    for d in range(1, N):
        if not np.isnan(Pt[d]).any() and not np.isnan(Pt[d-1]).any(): v[d] = np.hypot(*(Pt[d] - Pt[d-1]))/s[d]
    return v
S = {}
for nm, idx in (("head", 0), ("hip", 1), ("handA", 2), ("handB", 3), ("footA", 4), ("footB", 5)):
    S[("red", nm)] = speed(PR[:, idx], sr); S[("blue", nm)] = speed(PB[:, idx], sb)
for who in ("red", "blue"):
    for nm in ("head", "hip", "handA", "handB", "footA", "footB"):
        v = S[(who, nm)]; v = v[~np.isnan(v)]
        print(who, nm, "median %.3f p90 %.3f p99 %.3f max %.3f  (body-heights/drawing)" % (np.median(v), np.percentile(v, 90), np.percentile(v, 99), v.max()))
# --- torso lean (deg from vertical, sign: + toward opponent)
def lean(P, Q):
    out = np.full(N, np.nan)
    for d in range(N):
        if np.isnan(P[d, 0]): continue
        ang = P[d, 3]; dev = ((ang - 90 + 180) % 360) - 180   # + = leaning toward -x? math angle: >90 leans left
        if not np.isnan(Q[d, 0]): sign = 1 if Q[d, 0] > P[d, 0] else -1
        else: sign = 1
        out[d] = -dev*sign     # + = leaning toward opponent
    return out
LNr, LNb = lean(R, B), lean(B, R)
for nm, v in (("red", LNr), ("blue", LNb)):
    vv = v[~np.isnan(v)]; print(nm, "torso lean deg (toward opponent): p5 %.0f median %.0f p95 %.0f" % (np.percentile(vv, 5), np.median(vv), np.percentile(vv, 95)))
np.save("zoom.npy", zoom); np.save("lean_r.npy", LNr)
json.dump({"zoom": [None if np.isnan(x) else round(float(x), 3) for x in zoom], "t": [round(float(t), 3) for t in T]}, open("camera.json", "w"))
# --- effective holds: runs of drawings where all end-effector positions move < 0.004 H
mv = np.zeros(N)
for d in range(1, N):
    m = 0
    for P_, s_ in ((PR, sr), (PB, sb)):
        if not np.isnan(P_[d]).any() and not np.isnan(P_[d-1]).any(): m = max(m, np.max(np.hypot(*(P_[d] - P_[d-1]).T))/s_[d])
    mv[d] = m
holds = []; d = 1
while d < N:
    if mv[d] < .02:
        e = d
        while e + 1 < N and mv[e+1] < .02: e += 1
        if e - d + 1 >= 4: holds.append((d-1, e, round(float((T[e]-T[d-1])), 2)))
        d = e + 1
    else: d += 1
print("effective holds (all figures still, >=4 drawings): start_d, end_d, seconds"); print(holds)
