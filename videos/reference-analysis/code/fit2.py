import math, json, glob
import numpy as np
from PIL import Image, ImageDraw
from fitlib import *

def small_canvas(pts, sw, extra=0):
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]; m = sw + 3 + extra
    x0, x1 = int(max(0, min(xs) - m)), int(min(W, max(xs) + m + 1)); y0, y1 = int(max(0, min(ys) - m)), int(min(H, max(ys) + m + 1))
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)

def draw_chain(pts, sw, box):
    x0, y0, w, h = box; im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im); r = sw/2
    for a, b in zip(pts[:-1], pts[1:]):
        d.line([(a[0]-x0, a[1]-y0), (b[0]-x0, b[1]-y0)], fill=255, width=int(round(sw)))
    for q in pts: d.ellipse([q[0]-x0-r, q[1]-y0-r, q[0]-x0+r, q[1]-y0+r], fill=255)
    return np.asarray(im) > 0

def chain_score(root, a1, l1, a2, l2, sw, own_rem, free, bias=1.0):
    mid = root + vec(a1)*l1; end = mid + vec(a2)*l2; box = small_canvas([root, mid, end], sw)
    r = draw_chain([root, mid, end], sw, box); x0, y0, w, h = box
    o = own_rem[y0:y0+h, x0:x0+w]; f = free[y0:y0+h, x0:x0+w]
    if o.shape != r.shape: return -1e9
    return (r & o).sum() - bias*(r & ~f).sum()

def best_chain(root, l1, l2, sw, own_rem, free, step1=20, step2=20, bias=1.0, prev=None):
    best = (-1e9, 0, 0)
    for a1 in range(-180, 180, step1):
        for a2 in range(-180, 180, step2):
            sc = chain_score(root, a1, l1, a2, l2, sw, own_rem, free, bias)
            if prev is not None: sc -= .02*(abs(((a1 - prev[0] + 180) % 360) - 180) + abs(((a2 - prev[1] + 180) % 360) - 180))
            if sc > best[0]: best = (sc, a1, a2)
    sc, a1, a2 = best
    for st in (8, 3, 1):   # local refinement
        for _ in range(2):
            cand = [(a1 + i*st, a2 + j*st) for i in (-1, 0, 1) for j in (-1, 0, 1)]
            scs = [chain_score(root, c[0], l1, c[1], l2, sw, own_rem, free, bias) for c in cand]
            k = int(np.argmax(scs)); a1, a2 = cand[k]; sc = scs[k]
    return sc, a1, a2

def fit_figure(own, other, prop, prev=None, headc=None):
    """returns params list (12) + loss; own/other bool masks"""
    free = own | other
    exp_r = (prop["head"]*prev[2]) if prev is not None else None
    pc = tuple(joints(prev, prop)["head"]) if prev is not None else None
    hd = head_of(own, exp_r, pc)
    ys, xs = np.nonzero(own)
    if hd is not None and hd[2] > 3: hcx, hcy, hr = hd
    else: hcx = hcy = hr = None
    if hr is not None and hr > 3: s = hr/prop["head"]
    elif prev is not None: s = prev[2]
    else: s = (ys.max() - ys.min())*1.1
    if hr is None or hr < .5*prop["head"]*s:       # occluded head: trust previous
        if prev is not None:
            pj = joints(prev, prop); hcx, hcy = pj["head"]; s = prev[2]
        else: hcx, hcy = xs.mean(), ys.min() + .1*s
    # torso angle by overlap score
    best = (-1e9, 90)
    for tor in range(-180, 180, 5):
        sh = np.array([hcx, hcy]) - vec(tor)*(prop["neck"] + prop["head"])*s; hip = sh - vec(tor)*prop["torso"]*s
        sw = prop["stroke"]*s; box = small_canvas([hip, sh], sw); r = draw_chain([hip, sh], sw, box); x0, y0, w, h = box
        sc = (r & own[y0:y0+h, x0:x0+w]).sum() - 1.5*(r & ~free[y0:y0+h, x0:x0+w]).sum()
        if prev is not None: sc -= .15*abs(((tor - prev[3] + 180) % 360) - 180)
        if sc > best[0]: best = (sc, tor)
    tor = best[1]
    for st in (3, 1):
        for _ in range(2):
            cand = [tor + i*st for i in (-1, 0, 1)]; scs = []
            for c in cand:
                sh = np.array([hcx, hcy]) - vec(c)*(prop["neck"] + prop["head"])*s; hip = sh - vec(c)*prop["torso"]*s
                sw = prop["stroke"]*s; box = small_canvas([hip, sh], sw); r = draw_chain([hip, sh], sw, box); x0, y0, w, h = box
                scs.append((r & own[y0:y0+h, x0:x0+w]).sum() - 1.5*(r & ~free[y0:y0+h, x0:x0+w]).sum())
            tor = cand[int(np.argmax(scs))]
    sh = np.array([hcx, hcy]) - vec(tor)*(prop["neck"] + prop["head"])*s; hip = sh - vec(tor)*prop["torso"]*s
    sw = prop["stroke"]*s; rem = own.copy()
    # remove trunk+head pixels from remaining target
    base = [hip, sh]; box = (0, 0, W, H); tr = draw_chain(base, sw, box); rem &= ~tr
    hr_px = prop["head"]*s; im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).ellipse([hcx-hr_px, hcy-hr_px, hcx+hr_px, hcy+hr_px], fill=255); rem &= ~(np.asarray(im) > 0)
    out = [hip[0], hip[1], s, tor]; l_th, l_sh = prop["thigh"]*s, prop["shin"]*s; l_ua, l_fa = prop["uarm"]*s, prop["farm"]*s
    pv = lambda i: (prev[i], prev[i+1]) if prev is not None else None
    limbs = []
    for (root, l1, l2, idx) in ((hip, l_th, l_sh, 4), (hip, l_th, l_sh, 6), (sh, l_ua, l_fa, 8), (sh, l_ua, l_fa, 10)):
        sc, a1, a2 = best_chain(root, l1, l2, sw, rem, free, prev=pv(idx))
        mid = root + vec(a1)*l1; end = mid + vec(a2)*l2; rem &= ~draw_chain([root, mid, end], sw, (0, 0, W, H)); limbs += [a1, a2]
    p = np.array(out + limbs, float)
    p, l = refine(p, own, other, prop, 900, .3, (hcx, hcy), np.random.RandomState(0))
    return p, l

if __name__ == "__main__":
    import sys, time
    prop = json.load(open("prop.json")); tiles = []; t0 = time.time()
    for d, who in [(385, "red"), (29, "blue"), (298, "red"), (185, "blue"), (52, "red"), (325, "red"), (200, "blue"), (140, "red")]:
        img = Image.open(FR[UNIQ[d]]).convert("RGB"); r, b = masks(img); own, other = (r, b) if who == "red" else (b, r)
        p, l = fit_figure(own, other, prop)
        rr = render(p, prop); a = np.asarray(img).copy(); a[rr & own] = (0, 160, 0); a[rr & ~own & ~other] = (255, 200, 0); a[own & ~rr] = (200, 0, 120)
        ys2, xs2 = np.nonzero(own | rr); x0, x1, y0, y1 = max(0, xs2.min()-15), min(W, xs2.max()+15), max(0, ys2.min()-15), min(H, ys2.max()+15)
        tiles.append(Image.fromarray(a[y0:y1, x0:x1]).resize(((x1-x0)*3, (y1-y0)*3))); print(d, who, "loss", round(l, 3), "s", round(p[2], 1), round(time.time() - t0, 1), "s")
    Wt = sum(t.size[0] for t in tiles) + 10*len(tiles); Ht = max(t.size[1] for t in tiles)
    m = Image.new("RGB", (Wt, Ht), "white"); x = 0
    for t in tiles: m.paste(t, (x, 0)); x += t.size[0] + 10
    m.thumbnail((2200, 700)); m.save("viewfit2.png")
