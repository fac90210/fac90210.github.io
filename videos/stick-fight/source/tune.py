import math, itertools, numpy as np
import rig
from rig import *

def seg_dist(p, q, r, s):
    def pt(a, b, c):
        ab = b - a; t = max(0, min(1, np.dot(c - a, ab)/max(1e-9, np.dot(ab, ab)))); return np.linalg.norm(a + ab*t - c)
    # sample-based (cheap & robust)
    best = 1e9
    for u in np.linspace(0, 1, 40):
        best = min(best, pt(r, s, p + (q - p)*u))
    for u in np.linspace(0, 1, 40):
        best = min(best, pt(p, q, r + (s - r)*u))
    return best

def tune(keyidx, spear_t, s_on_blade, label):
    t, kind, base = KK[keyidx]
    ss = st_s(spear_t); cutpt = ss["butt"] + ss["d"]*CUT_S; shaft = (cutpt, cutpt + ss["d"]*.001)
    best = None
    for dgx, dgy, dw in itertools.product(np.linspace(-.3, .3, 7), np.linspace(-.5, .5, 11), np.linspace(-45, 45, 31)):
        p = dict(base); p["gx"] += dgx; p["gy"] += dgy; p["w"] += dw
        st = state(p, 1, "katana")
        blade = (st["butt"] + st["d"]*.45, st["tip"])
        # contact point along blade must be near s_on_blade*1.5 from guard
        dist = seg_dist(blade[0], blade[1], shaft[0], shaft[1])
        # keep contact point near the requested place on the blade
        cp = min(((np.linalg.norm((blade[0] + (blade[1]-blade[0])*u) - (shaft[0] + (shaft[1]-shaft[0])*v)), u) for u in np.linspace(0,1,25) for v in np.linspace(0,1,25)))
        cost = dist*10 + abs(cp[1] - s_on_blade)*2 + (abs(dgx)*1.5 + abs(dgy)*1.5 + abs(dw)/60)
        if best is None or cost < best[0]: best = (cost, dgx, dgy, dw, dist, cp[1])
    c, dgx, dgy, dw, dist, u = best
    print(f"{label}: key t={t}: gx {base['gx']:.2f}->{base['gx']+dgx:.2f}  gy {base['gy']:.2f}->{base['gy']+dgy:.2f}  w {base['w']:.0f}->{base['w']+dw:.0f}   gap={dist:.3f} contact@blade {u:.2f}")
if __name__ == "__main__":
    idx = {k[0]: i for i, k in enumerate(KK)}
    tune(idx[3.30], 3.30, .75, "clash 1 (parry)")
    tune(idx[4.30], 4.30, .85, "clash 2 (block)")
    tune(idx[6.50], 6.50, .8, "clash 3 (cut) at 6.50 key")
