import json, sys, numpy as np, time, os
from multiprocessing import Pool
from fitlib import *
from fit2 import fit_figure
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
prop = json.load(open("prop.json")); os.makedirs("ov", exist_ok=True)
def ground_row(a):
    g = a.sum(2) < 200; rows = np.nonzero(g.sum(1) > a.shape[1]*.45)[0]
    return float(rows.mean()) if len(rows) else None
def draw_overlay(img, fits):
    d = ImageDraw.Draw(img)
    for who, col in (("red", (255, 220, 0)), ("blue", (0, 230, 230))):
        f = fits.get(who)
        if not f: continue
        j = joints(f["p"], prop)
        for a, b in (("hip", "sh"), ("hip", "kA"), ("kA", "fA"), ("hip", "kB"), ("kB", "fB"), ("sh", "eA"), ("eA", "hA"), ("sh", "eB"), ("eB", "hB")):
            d.line([tuple(j[a]), tuple(j[b])], fill=col, width=2)
        hr = prop["head"]*f["p"][2]; hc = j["head"]; d.ellipse([hc[0]-hr, hc[1]-hr, hc[0]+hr, hc[1]+hr], outline=col, width=2)
        for q in j.values(): d.ellipse([q[0]-2, q[1]-2, q[0]+2, q[1]+2], fill=(0, 0, 0))
    return img
def work(rng_):
    a, b = rng_; prev = {"red": None, "blue": None}; last = {"red": -99, "blue": -99}; out = []
    for dI in range(a, b):
        img = Image.open(FR[UNIQ[dI]]).convert("RGB"); arr = np.asarray(img); r, bl = masks(img); rec = {"d": dI, "t": UNIQ[dI]/59.94, "gy": ground_row(arr.astype(int))}
        fits = {}
        for who, own, other in (("red", r, bl), ("blue", bl, r)):
            ok = own.sum() > 120
            if ok:
                dtmax = ndi.distance_transform_edt(own).max()
                ok = dtmax >= 4.0
            if not ok: rec[who] = None; prev[who] = None; continue
            pv = prev[who] if (dI - last[who]) <= 5 else None
            p, l = fit_figure(own, other, prop, pv)
            rec[who] = {"p": [float(x) for x in p], "loss": float(l)}; fits[who] = rec[who]; prev[who] = p; last[who] = dI
        draw_overlay(img, fits).save(f"ov/o_{dI:03d}.png"); out.append(rec)
    return out
if __name__ == "__main__":
    n = len(UNIQ); chunks = [(i*n//4, (i+1)*n//4) for i in range(4)]; t0 = time.time()
    with Pool(4) as pool: res = pool.map(work, chunks)
    allr = [r for c in res for r in c]; json.dump(allr, open("fits.json", "w"))
    ls = [r[w]["loss"] for r in allr for w in ("red", "blue") if r[w]]
    print("fitted", len(ls), "figure-frames in", round(time.time() - t0), "s; mean loss", round(float(np.mean(ls)), 3), "median", round(float(np.median(ls)), 3), " <.3:", round(float(np.mean(np.array(ls) < .3)), 2), " <.5:", round(float(np.mean(np.array(ls) < .5)), 2))
