import sys, math
import numpy as np
from PIL import Image, ImageDraw
import rig
from rig import *

def render(t, W=560, H=315, ghost=True):
    im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im)
    cx, cy, z = cam(t); fw = 14.222*z; sc = W/fw
    def P(a): return ((a[0] - cx)*sc + W/2, H/2 - (a[1] - cy)*sc)
    dr.line([P((-90, GY)), P((90, GY))], fill="#111", width=3)
    def line(a, b, w, col="#111"):
        x0, y0 = P(a); x1, y1 = P(b); dr.line([x0, y0, x1, y1], fill=col, width=int(w))
        r = w/2
        for x, y in ((x0, y0), (x1, y1)): dr.ellipse([x-r, y-r, x+r, y+r], fill=col)
    def fig(st, weapon, cut):
        sw = .18*sc
        for a, b in ((st["pel"], st["top"]), (st["pel"], st["kf"]), (st["kf"], st["ff"]), (st["pel"], st["kb"]), (st["kb"], st["bf"]),
                     (st["top"], st["ea"]), (st["ea"], st["A"]), (st["top"], st["eb"]), (st["eb"], st["B"])):
            line(a, b, sw)
        for foot in ("ff", "bf"): line(st[foot], st[foot] + np.array([.2*st["f"], 0]), sw)
        x, y = P(st["head"]); r = HEAD_R*sc; dr.ellipse([x-r, y-r, x+r, y+r], fill="#111")
        d, butt = st["d"], st["butt"]; perp = np.array([-d[1], d[0]])
        if weapon == "katana":
            g = butt + d*.45; line(butt, g, 7); line(g - perp*.15, g + perp*.15, 5)
            pts = [g + d*(1.5*u) + perp*(.07*math.sin(math.pi*u)) for u in np.linspace(0, 1, 9)]
            for a, b in zip(pts[:-1], pts[1:]): line(a, b, 3.5)
        else:
            end = butt + d*(CUT_S if cut else 3.0); line(butt, end, 5)
            if not cut:
                tip = butt + d*3.4; base = butt + d*3.0
                dr.polygon([P(base + perp*.11), P(tip), P(base - perp*.11), P(base - d*.18)], fill="#111")
    fig(st_k(t), "katana", False); fig(st_s(t), "spear", t > T_CUT)
    if t > T_CUT:
        i = min(len(TRAJ) - 1, int((t - T_CUT)*240)); c, ang = TRAJ[i]; d = np.array([math.cos(ang), math.sin(ang)])
        a = c - d*PL/2; b = c + d*PL/2; line(a, b, 5)
    dr.text((6, 4), f"{t:.2f}s", fill="#c00")
    return im

if __name__ == "__main__":
    ts = [float(x) for x in sys.argv[2:]]; cols = 3
    ims = [render(t) for t in ts]; W, H = ims[0].size; rows = (len(ims) + cols - 1)//cols
    m = Image.new("RGB", (W*cols, H*rows), "white")
    for i, im in enumerate(ims): m.paste(im, ((i % cols)*W, (i//cols)*H))
    m.save(sys.argv[1]); print(m.size)
