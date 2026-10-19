import json, numpy as np, time
from multiprocessing import Pool
from fitlib import *
from fit2 import fit_figure
from PIL import Image
CASES = [(385, "red"), (383, "red"), (29, "blue"), (27, "blue"), (298, "red"), (300, "red"), (52, "red"), (58, "red"), (150, "blue"), (157, "blue"), (332, "red"), (334, "red"), (185, "blue"), (140, "red")]
def load(c):
    d, who = c; r, b = masks(Image.open(FR[UNIQ[d]])); return (r, b) if who == "red" else (b, r)
DATA = [load(c) for c in CASES]
def one(args):
    i, prop = args; own, other = DATA[i]; p, l = fit_figure(own, other, prop); return l
def total(prop, pool):
    return float(np.mean(pool.map(one, [(i, prop) for i in range(len(DATA))])))
if __name__ == "__main__":
    prop = json.load(open("prop.json")); pool = Pool(4); t0 = time.time()
    best = total(prop, pool); print("start", round(best, 4), round(time.time() - t0))
    keys = ["thigh", "shin", "torso", "uarm", "farm", "head", "stroke", "neck"]
    for rnd in range(3):
        for k in keys:
            for f in (.88, 1.12, 1.06, .94):
                pr = dict(prop); pr[k] = prop[k]*f; t = total(pr, pool)
                if t < best - 1e-4: best, prop = t, pr
        print("round", rnd, round(best, 4), {k: round(v, 3) for k, v in prop.items()}, round(time.time() - t0), "s", flush=True)
        json.dump(prop, open("prop2.json", "w"))
