import math, random
import numpy as np
import soundfile as sf
from manim import *
import rig
from rig import *

BLK = "#111111"
SR = 44100
def P3(a): return [float(a[0]), float(a[1]), 0]
def seg(a, b, col, w, op=1):
    return Line(P3(a), P3(b), stroke_color=col, stroke_width=w, stroke_opacity=op).set_cap_style(CapStyleType.ROUND)

def draw_fig(st, weapon, col, op=1.0, cut=False):
    g = VGroup(); f = st["f"]
    for a, b in ((st["pel"], st["top"]), (st["pel"], st["kf"]), (st["kf"], st["ff"]), (st["pel"], st["kb"]), (st["kb"], st["bf"]),
                 (st["top"], st["ea"]), (st["ea"], st["A"]), (st["top"], st["eb"]), (st["eb"], st["B"])):
        g.add(seg(a, b, col, 18, op))
    for foot in ("ff", "bf"): g.add(seg(st[foot], st[foot] + np.array([.2*f, 0]), col, 18, op))
    g.add(Circle(radius=HEAD_R, fill_color=col, fill_opacity=op, stroke_width=0).move_to(P3(st["head"])))
    d, butt = st["d"], st["butt"]; perp = np.array([-d[1], d[0]])
    if weapon == "katana":
        gd = butt + d*.45
        g.add(seg(butt, gd, col, 12, op)); g.add(seg(gd - perp*.17, gd + perp*.17, col, 9, op))
        pts = [gd + d*(1.5*u) + perp*(.07*math.sin(math.pi*u)) for u in np.linspace(0, 1, 10)]
        for a, b in zip(pts[:-1], pts[1:]): g.add(seg(a, b, col, 7, op))
    else:
        end = butt + d*(CUT_S if cut else 3.0); g.add(seg(butt, end, col, 9, op))
        if not cut:
            tip = butt + d*3.4; base = butt + d*3.0
            g.add(Polygon(P3(base + perp*.12), P3(tip), P3(base - perp*.12), P3(base - d*.2), fill_color=col, fill_opacity=op, stroke_color=col, stroke_width=3, stroke_opacity=op))
    return g

# ------------------------------------------------------------------ audio
def _norm(x, g): return (x/(np.max(np.abs(x)) + 1e-9)*g).astype(np.float32)
def clang(dur=.9, f0=1.0, g=.8):
    t = np.arange(int(SR*dur))/SR; x = np.zeros_like(t)
    for fr, dc, a in ((1900, 7, 1), (2860, 10, .8), (4300, 14, .6), (6200, 20, .4), (880, 5, .6)): x += a*np.sin(2*np.pi*fr*f0*t)*np.exp(-t*dc)
    x += np.random.RandomState(2).randn(len(t))*np.exp(-t*220)*.9
    return _norm(x, g)
def whoosh(dur=.35, lo=300, hi=2600, g=.5):
    t = np.arange(int(SR*dur))/SR; n = np.random.RandomState(5).randn(len(t)); fc = lo + (hi - lo)*(t/dur); y = np.zeros_like(t); lp = 0.0
    for i in range(len(t)):
        a = min(.95, 2*np.pi*fc[i]/SR); lp += a*(n[i] - lp); y[i] = lp
    return _norm(y*np.sin(np.pi*t/dur)**1.5, g)
def thud(dur=.3, f=80, g=.8):
    t = np.arange(int(SR*dur))/SR; x = np.sin(2*np.pi*(f + 90*np.exp(-t*25))*t)*np.exp(-t*14) + np.random.RandomState(7).randn(len(t))*np.exp(-t*60)*.3
    return _norm(x, g)
def crack(dur=.25, g=.8):
    t = np.arange(int(SR*dur))/SR; x = np.random.RandomState(9).randn(len(t))*np.exp(-t*35) + np.sin(2*np.pi*300*t)*np.exp(-t*30)*.8
    return _norm(x, g)
def shing(dur=.5, g=.6):
    t = np.arange(int(SR*dur))/SR; x = np.sin(2*np.pi*(5200 - 2500*t/dur)*t)*np.exp(-t*7) + np.sin(2*np.pi*3100*t)*np.exp(-t*9)*.5
    return _norm(x, g)
def tap(g=.5):
    t = np.arange(int(SR*.06))/SR; return _norm(np.sin(2*np.pi*140*t)*np.exp(-t*60) + np.random.RandomState(3).randn(len(t))*np.exp(-t*120)*.4, g)

def foot_plants():
    out = []; prev = {"K": [0, 0], "S": [0, 0]}
    for i in range(int(14/ (1/240))):
        t = i/240
        for who, fn, face in (("K", pose_k, 1), ("S", pose_s, -1)):
            p = fn(t)
            if p["walk"] < .5: prev[who] = [0, 0]; continue
            ph = p["px"]*face*2.3; lifts = [max(0, math.cos(ph)), max(0, math.cos(ph + math.pi))]
            for j in (0, 1):
                if prev[who][j] > .05 and lifts[j] <= .05: out.append(t)
            prev[who] = lifts
    return out

def mix_audio(path):
    out = np.zeros(int(SR*(TOTAL + 1)), dtype=np.float32)
    def put(x, t, g=1.0):
        i = int(t*SR); j = min(len(out), i + len(x));
        if i < len(out): out[i:j] += x[:j-i]*g
    tt = np.arange(len(out))/SR
    wind = np.convolve(np.random.RandomState(1).randn(len(out)).astype(np.float32), np.ones(150)/150, "same")*(.55 + .45*np.sin(tt*.6))
    out += _norm(wind, .06)
    for t in foot_plants(): put(tap(.5), t, .5)
    put(whoosh(.3, 400, 2800, .6), 3.05, .8); put(clang(.9, 1.0, .8), 3.30, .9)
    put(whoosh(.3, 200, 3200, .7), 4.0, .9); put(clang(1.1, .85, 1.0), 4.30, 1.0); put(thud(.3, 70), 4.3, .4)
    put(whoosh(.35, 300, 1600), 5.5, .7); put(whoosh(.4, 250, 2800, .8), 5.85, .8); put(thud(.2, 100), 5.95, .3)
    put(whoosh(.3, 300, 3000, .8), 6.3, .9); put(shing(.5, .8), T_CUT, 1.0); put(crack(.3, .9), T_CUT + .02, .9)
    put(thud(.35, 70), 6.95, .7); put(thud(.2, 120), 7.0, .4)
    put(whoosh(.3, 300, 1600), 8.1, .6); put(whoosh(.5, 200, 3400, .9), 8.2, 1.0)
    put(shing(.6, .9), IMPACT_T, 1.0); put(thud(.4, 60), IMPACT_T + .03, 1.0)
    put(whoosh(.4, 400, 2200), 9.95, .8); put(thud(.5, 55), 10.2, .9); put(thud(.25, 90), 10.4, .4)
    sf.write(path, out, SR)

# ------------------------------------------------------------------ scene
class StickFight(MovingCameraScene):
    def construct(self):
        self.clk = 0.0
        self.add_updater(lambda dt: setattr(self, "clk", self.clk + dt))
        self.camera.background_color = "#FFFFFF"
        mix_audio("stick_sfx.wav")
        ground = Line([-80, GY - .03, 0], [80, GY - .03, 0], stroke_color=BLK, stroke_width=7)
        ticks = VGroup(*[Line([x, GY - .03, 0], [x - .3, GY - .5, 0], stroke_color="#CFCFCF", stroke_width=3) for x in np.arange(-60, 60, 1.7)])
        self.add(ticks, ground)
        fr = self.camera.frame; w0 = fr.width
        def camu(m):
            cx, cy, z = cam(self.clk); m.set_width(w0*z); m.move_to([cx, cy, 0])
        fr.add_updater(camu)

        def speed(fn, face, weapon, t):
            a = state(fn(t), face, weapon); b = state(fn(max(0, t - 2/FPS)), face, weapon)
            return np.linalg.norm(a["A"] - b["A"]) + np.linalg.norm(a["pel"] - b["pel"])*.6

        def world():
            t = self.clk; g = VGroup()
            for who, fn, face, wp in (("K", pose_k, 1, "katana"), ("S", pose_s, -1, "spear")):
                cutf = (wp == "spear" and t > T_CUT)
                # ghosts (2 lagging copies) when moving fast
                v = speed(fn, face, wp, t)
                if v > 1.5:
                    for k, op in ((2, .12), (1, .22)):
                        tk = max(0, t - k/FPS); g.add(draw_fig(state(fn(tk), face, wp), wp, "#555555", op, cut=(wp == "spear" and tk > T_CUT)))
                # blade sweep (swoosh) from recent weapon positions
                if wp == "katana" and v > 1.2:
                    pts = [state(fn(max(0, t - k/(FPS*4))), face, wp) for k in range(0, 9)]
                    for k in range(8):
                        a, b = pts[k], pts[k+1]
                        g.add(Polygon(P3(a["butt"] + a["d"]*.45), P3(a["tip"]), P3(b["tip"]), P3(b["butt"] + b["d"]*.45), fill_color="#666666", fill_opacity=.30*(1 - k/8), stroke_width=0))
                g.add(draw_fig(state(fn(t), face, wp), wp, BLK, 1.0, cut=cutf))
            if t > T_CUT:
                i = min(len(TRAJ) - 1, int((t - T_CUT)*240)); c, ang = TRAJ[i]; d = np.array([math.cos(ang), math.sin(ang)]); perp = np.array([-d[1], d[0]])
                a = c - d*PL/2; b = c + d*PL/2
                g.add(seg(a, b - d*.4, BLK, 9))
                g.add(Polygon(P3(b - d*.4 + perp*.12), P3(b), P3(b - d*.4 - perp*.12), P3(b - d*.6), fill_color=BLK, fill_opacity=1, stroke_color=BLK, stroke_width=3))
            return g

        def fx():
            t = self.clk; g = VGroup()
            for tc, who, s in CLASHES:
                dt = t - tc
                if 0 <= dt < 2/FPS:
                    st = st_k(tc); pos = st["butt"] + st["d"]*(.45 + s*1.5*.75)
                    for k in range(6):
                        a = 2*PI*k/6 + .4; r0 = .12 + dt*3; r1 = r0 + .35
                        g.add(seg(pos + np.array([math.cos(a), math.sin(a)])*r0, pos + np.array([math.cos(a), math.sin(a)])*r1, "#333333", 5))
            dt = t - IMPACT_T
            if 0 <= dt < 2/FPS:
                ks = st_k(IMPACT_T); ss = st_s(IMPACT_T); pos = (ss["top"] + ss["pel"])/2
                for r, op in ((.9, .10), (.6, .12), (.35, .16)): g.add(Circle(radius=r, fill_color="#555555", fill_opacity=op, stroke_width=0).move_to(P3(pos)))
                for k in range(8):
                    a = 2*PI*k/8 + .2; r0 = .5 + dt*2; r1 = r0 + .9
                    g.add(seg(pos + np.array([math.cos(a), math.sin(a)])*r0, pos + np.array([math.cos(a), math.sin(a)])*r1, "#333333", 4))
            # speed lines on the two dash-slashes
            for ta, tb in ((4.22, 4.42), (8.30, 8.50)):
                if ta <= t <= tb:
                    cx, cy, z = cam(t); rng = random.Random(int(t*FPS))
                    for k in range(14):
                        y = cy + rng.uniform(-1.8, 1.8); x0 = cx + rng.uniform(-7, 3); ln = rng.uniform(2.5, 6.5)
                        g.add(seg([x0, y], [x0 + ln, y], "#888888", rng.choice([2, 3, 4]), .7))
            # fade in / out
            cx, cy, z = cam(t); op = max(max(0, 1 - t/.35), max(0, (t - (TOTAL - .8))/.8))
            if op > 0: g.add(Rectangle(width=40, height=24, fill_color="#FFFFFF", fill_opacity=min(1, op), stroke_width=0).move_to([cx, cy, 0]))
            return g
        self.add(always_redraw(world)); top = always_redraw(fx); top.set_z_index(50); self.add(top)
        self.add_sound("stick_sfx.wav", time_offset=0)
        self.wait(TOTAL)
