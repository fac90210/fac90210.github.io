import math, json, glob
import numpy as np
from PIL import Image, ImageDraw
REF = "/tmp/claude-0/ref"
FR = sorted(glob.glob(REF + "/frames/f_*.png")); UNIQ = json.load(open(REF + "/uniq.json"))
W, H = 644, 354
# proportions as fractions of s (s = standing figure height in px)
PROP = dict(torso=.27, thigh=.245, shin=.235, uarm=.115, farm=.115, head=.10, stroke=.062, neck=.06)
NAMES = ["hx", "hy", "s", "tor", "thA", "shA", "thB", "shB", "uaA", "faA", "uaB", "faB"]

def masks(img):
    a = np.asarray(img.convert("RGB")).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 85) & (r - g > 70) & (r - b > 70)
    blue = (b > 110) & (b - r > 38) & (b - g > 30) & (r < 150)
    return red, blue

def vec(a):  # math angle (deg, CCW from +x, y up) -> image delta (y down)
    r = math.radians(a); return np.array([math.cos(r), -math.sin(r)])

def joints(p, prop=PROP):
    hx, hy, s, tor, thA, shA, thB, shB, uaA, faA, uaB, faB = p
    hip = np.array([hx, hy]); sh = hip + vec(tor)*prop["torso"]*s
    head = sh + vec(tor)*(prop["neck"] + prop["head"])*s
    kA = hip + vec(thA)*prop["thigh"]*s; fA = kA + vec(shA)*prop["shin"]*s
    kB = hip + vec(thB)*prop["thigh"]*s; fB = kB + vec(shB)*prop["shin"]*s
    eA = sh + vec(uaA)*prop["uarm"]*s; hA = eA + vec(faA)*prop["farm"]*s
    eB = sh + vec(uaB)*prop["uarm"]*s; hB = eB + vec(faB)*prop["farm"]*s
    return dict(hip=hip, sh=sh, head=head, kA=kA, fA=fA, kB=kB, fB=fB, eA=eA, hA=hA, eB=eB, hB=hB)

def render(p, prop=PROP, size=(W, H)):
    j = joints(p, prop); s = p[2]; sw = max(2, prop["stroke"]*s); im = Image.new("L", size, 0); d = ImageDraw.Draw(im)
    def bone(a, b):
        d.line([tuple(a), tuple(b)], fill=255, width=int(round(sw))); r = sw/2
        for q in (a, b): d.ellipse([q[0]-r, q[1]-r, q[0]+r, q[1]+r], fill=255)
    for a, b in (("hip", "sh"), ("hip", "kA"), ("kA", "fA"), ("hip", "kB"), ("kB", "fB"), ("sh", "eA"), ("eA", "hA"), ("sh", "eB"), ("eB", "hB")): bone(j[a], j[b])
    hr = prop["head"]*s; hc = j["head"]; d.ellipse([hc[0]-hr, hc[1]-hr, hc[0]+hr, hc[1]+hr], fill=255)
    return np.asarray(im) > 0

def loss(p, own, other, prop=PROP, headhint=None):
    r = render(p, prop)
    fn = (own & ~r).sum(); fp = (r & ~(own | other)).sum()
    L = (fn + fp)/max(1, own.sum())
    if headhint is not None:
        hc = joints(p, prop)["head"]; L += .5*np.hypot(hc[0]-headhint[0], hc[1]-headhint[1])/max(10, p[2])
    return L

def head_of(mask, exp_r=None, prev_c=None):
    from scipy import ndimage as ndi
    if mask.sum() < 30: return None
    dt = ndi.distance_transform_edt(mask)
    cy, cx = np.unravel_index(np.argmax(dt), dt.shape); v = float(dt[cy, cx])
    if exp_r is None or (.5*exp_r <= v <= 2.4*exp_r):
        return (float(cx), float(cy), v)
    # global max implausible: choose the plausible disc nearest the previous head
    cand = dt >= .5*exp_r
    if not cand.any(): return None
    lab, n = ndi.label(cand); best = None
    for k in range(1, n + 1):
        reg = lab == k; vv = dt[reg].max()
        if vv > 2.4*exp_r: continue
        yy, xx = np.unravel_index(np.argmax(np.where(reg, dt, 0)), dt.shape)
        d = 0 if prev_c is None else np.hypot(xx - prev_c[0], yy - prev_c[1])
        sc = d*.1 + abs(vv - exp_r)/exp_r*5
        if best is None or sc < best[0]: best = (sc, float(xx), float(yy), float(vv))
    return None if best is None else (best[1], best[2], best[3])

def refine(p0, own, other, prop, iters=1500, sig0=1.0, headhint=None, rng=None):
    rng = rng or np.random.RandomState(0)
    p = np.array(p0, float); best = loss(p, own, other, prop, headhint)
    scale = np.array([4, 4, 5, 8, 12, 12, 12, 12, 14, 14, 14, 14])
    for it in range(iters):
        sig = sig0*(1 - it/iters)**1.5 + .04
        q = p.copy()
        k = rng.choice(12, rng.randint(1, 4), replace=False)
        q[k] += rng.randn(len(k))*scale[k]*sig
        q[2] = max(30, q[2])
        l = loss(q, own, other, prop, headhint)
        if l < best: p, best = q, l
    return p, best
