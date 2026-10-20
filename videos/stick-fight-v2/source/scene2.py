import math, random
import numpy as np
import soundfile as sf
from manim import *
import rig2
from rig2 import *

BLK = "#111111"; SR = 44100
def P3(a): return [float(a[0]), float(a[1]), 0]
def chain(pts, w, col=BLK, op=1.0):
    m = VMobject(stroke_color=col, stroke_width=w, stroke_opacity=op, joint_type=LineJointType.ROUND, cap_style=CapStyleType.ROUND)
    m.set_points_as_corners([P3(p) for p in pts]); m.set_fill(opacity=0); return m
W_LIMB = STROKE*100

def draw_fig(st, weapon, col=BLK, op=1.0, cut=False):
    g = VGroup(); f = st["f"]
    g.add(chain([st["pel"], st["kf"], st["ff"]], W_LIMB, col, op)); g.add(chain([st["pel"], st["kb"], st["bf"]], W_LIMB, col, op))
    g.add(chain([st["pel"], st["top"], st["head"]], W_LIMB*1.18, col, op))
    g.add(chain([st["top"], st["ea"], st["A"]], W_LIMB, col, op)); g.add(chain([st["top"], st["eb"], st["B"]], W_LIMB, col, op))
    g.add(Circle(radius=HEAD_R, fill_color=col, fill_opacity=op, stroke_width=0).move_to(P3(st["head"])))
    d, butt = st["d"], st["butt"]; perp = np.array([-d[1], d[0]])
    if weapon == "katana":
        gd = butt + d*.5
        g.add(chain([butt, gd], W_LIMB*.62, col, op)); g.add(chain([gd - perp*.2, gd + perp*.2], W_LIMB*.5, col, op))
        pts = [gd + d*(1.55*t) + perp*(.08*math.sin(math.pi*t)) for t in np.linspace(0, 1, 11)]
        g.add(chain(pts, W_LIMB*.38, col, op))
    else:
        end = butt + d*(CUT_S if cut else 3.15); g.add(chain([butt, end], W_LIMB*.4, col, op))
        if not cut:
            base = butt + d*3.15; tip = butt + d*3.6
            g.add(Polygon(P3(base + perp*.13), P3(tip), P3(base - perp*.13), P3(base - d*.2), fill_color=col, fill_opacity=op, stroke_color=col, stroke_width=3, stroke_opacity=op))
    return g

# ------------------------------------------------------------------ audio
def _norm(x, g): return (x/(np.max(np.abs(x)) + 1e-9)*g).astype(np.float32)
def clang(dur=.9, f0=1.0, g=.8):
    t = np.arange(int(SR*dur))/SR; x = np.zeros_like(t)
    for fr, dc, a in ((1900, 7, 1), (2860, 10, .8), (4300, 14, .6), (6200, 20, .4), (880, 5, .6)): x += a*np.sin(2*np.pi*fr*f0*t)*np.exp(-t*dc)
    x += np.random.RandomState(2).randn(len(t))*np.exp(-t*220)*.9; return _norm(x, g)
def whoosh(dur=.35, lo=300, hi=2600, g=.5):
    t = np.arange(int(SR*dur))/SR; n = np.random.RandomState(5).randn(len(t)); fc = lo + (hi - lo)*(t/dur); y = np.zeros_like(t); lp = 0.0
    for i in range(len(t)):
        a = min(.95, 2*np.pi*fc[i]/SR); lp += a*(n[i] - lp); y[i] = lp
    return _norm(y*np.sin(np.pi*t/dur)**1.5, g)
def thud(dur=.3, f=80, g=.8):
    t = np.arange(int(SR*dur))/SR; x = np.sin(2*np.pi*(f + 90*np.exp(-t*25))*t)*np.exp(-t*14) + np.random.RandomState(7).randn(len(t))*np.exp(-t*60)*.3; return _norm(x, g)
def crack(dur=.25, g=.8):
    t = np.arange(int(SR*dur))/SR; x = np.random.RandomState(9).randn(len(t))*np.exp(-t*35) + np.sin(2*np.pi*300*t)*np.exp(-t*30)*.8; return _norm(x, g)
def shing(dur=.5, g=.6):
    t = np.arange(int(SR*dur))/SR; x = np.sin(2*np.pi*(5200 - 2500*t/dur)*t)*np.exp(-t*7) + np.sin(2*np.pi*3100*t)*np.exp(-t*9)*.5; return _norm(x, g)
def tap(g=.5):
    t = np.arange(int(SR*.06))/SR; return _norm(np.sin(2*np.pi*140*t)*np.exp(-t*60) + np.random.RandomState(3).randn(len(t))*np.exp(-t*120)*.4, g)
def foot_plants():
    out = []; prev = {"K": [0, 0], "S": [0, 0]}
    for i in range(int(TOTAL*240)):
        t = i/240
        for who, fn, face in (("K", pose_k, 1), ("S", pose_s, -1)):
            p = fn(t)
            if p["walk"] < .5: prev[who] = [0, 0]; continue
            ph = p["px"]*face*2.3; lifts = [max(0, math.cos(ph)), max(0, math.cos(ph + math.pi))]
            for j in (0, 1):
                if prev[who][j] > .05 and lifts[j] <= .05: out.append((t, p["amp"]))
            prev[who] = lifts
    return out
def mix_audio(path):
    out = np.zeros(int(SR*(TOTAL + 1)), dtype=np.float32)
    def put(x, t, g=1.0):
        i = int(t*SR)
        if 0 <= i < len(out): j = min(len(out), i + len(x)); out[i:j] += x[:j-i]*g
    tt = np.arange(len(out))/SR
    wind = np.convolve(np.random.RandomState(1).randn(len(out)).astype(np.float32), np.ones(150)/150, "same")*(.55 + .45*np.sin(tt*.6)); out += _norm(wind, .05)
    for t, amp in foot_plants(): put(tap(.6), t, .35 + .5*min(1, amp))
    for t, lo, hi, g in ((3.0, 400, 2800, .8), (3.95, 200, 3200, .9), (5.45, 300, 1600, .7), (5.8, 250, 2800, .8), (6.3, 300, 3000, .8), (7.9, 300, 1600, .6), (8.1, 250, 2600, .8), (9.85, 300, 3000, .8), (10.0, 200, 3400, .95), (11.6, 400, 2200, .8)):
        put(whoosh(.32, lo, hi, g), t, 1.0)
    put(clang(.9, 1.0, .8), 3.30, .9); put(clang(1.1, .85, 1.0), 4.30, 1.0); put(thud(.3, 70), 4.3, .5)
    put(shing(.5, .8), T_CUT, 1.0); put(crack(.3, .9), T_CUT + .02, .9)
    put(thud(.35, 70), 6.95, .7); put(thud(.3, 80), 8.55, .5)
    put(shing(.6, .9), IMPACT_T, 1.0); put(thud(.4, 60), IMPACT_T + .03, 1.0); put(clang(.8, .7, .4), IMPACT_T + .02, .5)
    put(thud(.5, 55), 11.35, .8); put(thud(.5, 55), 12.25, .9); put(thud(.25, 90), 12.45, .4)
    sf.write(path, out, SR)

# ------------------------------------------------------------------ scene
class Fight2(MovingCameraScene):
    def construct(self):
        self.clk = 0.0
        self.add_updater(lambda dt: setattr(self, "clk", self.clk + dt))
        self.camera.background_color = "#FFFFFF"
        mix_audio("fight2_sfx.wav")
        ground = Line([-90, GY - .03, 0], [90, GY - .03, 0], stroke_color=BLK, stroke_width=9)
        ticks = VGroup(*[Line([x, GY - .03, 0], [x - .3, GY - .55, 0], stroke_color="#D2D2D2", stroke_width=3) for x in np.arange(-70, 70, 1.9)])
        self.add(ticks, ground)
        fr = self.camera.frame; w0 = fr.width
        def camu(m):
            cx, cy, z = cam(self.clk); m.set_width(w0*z); m.move_to([cx, cy, 0])
        fr.add_updater(camu)
        def rel_speed(fn, face, wp, t):
            a = state(fn(t), face, wp); b = state(fn(max(0, t - 2/FPS)), face, wp)
            return np.linalg.norm((a["A"] - a["pel"]) - (b["A"] - b["pel"])) + .5*np.linalg.norm(a["pel"] - b["pel"])
        def world():
            t = self.clk; g = VGroup()
            for who, fn, face, wp in (("K", pose_k, 1, "katana"), ("S", pose_s, -1, "spear")):
                v = rel_speed(fn, face, wp, t)
                if v > 1.9:
                    for k, op in ((2, .10), (1, .20)):
                        tk = max(0, t - k/FPS); g.add(draw_fig(state(fn(tk), face, wp), wp, "#555555", op, cut=(wp == "spear" and tk > T_CUT)))
                if wp == "katana":
                    pts = [state(fn(max(0, t - k/(FPS*4))), face, wp) for k in range(0, 9)]
                    tipsp = np.linalg.norm((pts[0]["tip"] - pts[0]["pel"]) - (pts[4]["tip"] - pts[4]["pel"]))
                    if tipsp > 1.3:
                        for k in range(8):
                            a, b = pts[k], pts[k+1]
                            g.add(Polygon(P3(a["butt"] + a["d"]*.5), P3(a["tip"]), P3(b["tip"]), P3(b["butt"] + b["d"]*.5), fill_color="#666666", fill_opacity=.30*(1 - k/8)*min(1, (tipsp - 1.3)/1.2), stroke_width=0))
                g.add(draw_fig(state(fn(t), face, wp), wp, BLK, 1.0, cut=(wp == "spear" and t > T_CUT)))
            if t > T_CUT:
                i = min(len(TRAJ) - 1, int((t - T_CUT)*240)); c, ang = TRAJ[i]; d = np.array([math.cos(ang), math.sin(ang)]); perp = np.array([-d[1], d[0]])
                a = c - d*PL/2; b = c + d*PL/2
                g.add(chain([a, b - d*.45], W_LIMB*.4)); g.add(Polygon(P3(b - d*.45 + perp*.13), P3(b), P3(b - d*.45 - perp*.13), P3(b - d*.65), fill_color=BLK, fill_opacity=1, stroke_color=BLK, stroke_width=3))
            return g
        def fx():
            t = self.clk; g = VGroup(); cx, cy, z = cam(t)
            for tc, who, s in CLASHES:
                dt = t - tc
                if 0 <= dt < 2/FPS:
                    st = st_k(tc); pos = st["butt"] + st["d"]*(.5 + s*1.55*.75)
                    for k in range(6):
                        a = 2*PI*k/6 + .4; r0 = .12 + dt*3; r1 = r0 + .4
                        g.add(chain([pos + np.array([math.cos(a), math.sin(a)])*r0, pos + np.array([math.cos(a), math.sin(a)])*r1], 5, "#333333"))
            dt = t - IMPACT_T
            if 0 <= dt < 4/FPS:
                ss = st_s(IMPACT_T); ks = st_k(IMPACT_T); pos = (ss["top"] + ss["pel"])/2; fr_ = dt/(4/FPS)
                for r, op in ((1.2, .09), (.8, .11), (.5, .15)): g.add(Circle(radius=r*(1 - fr_*.5), fill_color="#555555", fill_opacity=op*(1 - fr_), stroke_width=0).move_to(P3(pos)))
                for k in range(9):
                    a = 2*PI*k/9 + .2; r0 = .55 + fr_*2.2; r1 = r0 + 1.0*(1 - fr_*.4)
                    g.add(chain([pos + np.array([math.cos(a), math.sin(a)])*r0, pos + np.array([math.cos(a), math.sin(a)])*r1], 5*(1 - fr_) + 1.5, "#333333", 1 - fr_*.6))
            if DASH[0] <= t < DASH[1]:
                ks = st_k(t); rng = random.Random(int(t*FPS)*5 + 1); wide = cam_wide(t)
                yc = (ks["top"][1] + ks["pel"][1])/2
                for k in range(16 if wide else 9):
                    y0 = yc + rng.uniform(-.55, .55)
                    if wide: x1 = cx + rng.uniform(-9, 3); ln = rng.uniform(5, 15)
                    else: x1 = ks["pel"][0] - .7; ln = rng.uniform(1.2, 3.6)
                    g.add(chain([[x1 - ln, y0], [x1, y0]], rng.choice([2, 3, 4]), "#777777", .8))
            op = max(max(0, 1 - t/.3), max(0, (t - (TOTAL - .8))/.8))
            if op > 0: g.add(Rectangle(width=60, height=36, fill_color="#FFFFFF", fill_opacity=min(1, op), stroke_width=0).move_to([cx, cy, 0]))
            return g
        self.add(always_redraw(world)); top = always_redraw(fx); top.set_z_index(50); self.add(top)
        self.add_sound("fight2_sfx.wav", time_offset=0); self.wait(TOTAL)
