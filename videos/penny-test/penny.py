import math, random
from lib import *
import lib
from manim.utils.rate_functions import ease_out_bounce

lib.VOICE = 1
LINES = ["Hi there! I'm Penny, and I run the tastiest pizza shop in town.",
         "But here's a secret. Hire too many cooks, and everything gets worse!",
         "Stick around, and I'll show you why."]
SKIN = "#FFC9A3"; INK = "#4A2C2A"; HAT = "#FFFFFF"; COAT = "#FFFFFF"; RED = "#E8454F"

def sm(x): x = min(1, max(0, x)); return x*x*(3-2*x)

# ---- audio prep ----
paths, durs, envs = [], [], []
for l in LINES:
    p, d = tts(l); paths.append(p); durs.append(d)
    x, sr = sf.read(p); x = x if x.ndim == 1 else x[:, 0]
    hop = int(sr/60); n = len(x)//hop
    r = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)) for i in range(n)])
    r = np.convolve(r, np.ones(3)/3, "same"); envs.append(np.clip(r/np.percentile(r, 92), 0, 1))
S1 = 1.8; S2 = S1 + durs[0] + .7; S3 = S2 + durs[1] + .6
STARTS = [S1, S2, S3]; END = S3 + durs[2]; TOTAL = END + 2.4
T_SHOCK = S2 + durs[1]*.55; T_WAVE = (S1, S1 + 1.5)

def env(t):
    for s, d, e in zip(STARTS, durs, envs):
        if s <= t <= s + d:
            i = min(len(e)-1, int((t - s)*60)); return float(e[i])
    return 0.0

def ell(w, h, x, y, fill, stroke=INK, sw=4, op=1):
    return Ellipse(width=w, height=h, fill_color=fill, fill_opacity=op, stroke_color=stroke, stroke_width=sw).move_to([x, y, 0])

def mouth(e, smile_amt=1.0):
    if e < .12:
        a = ArcBetweenPoints([-.28, .0, 0], [.28, .0, 0], angle=PI/2.6, stroke_color=INK, stroke_width=6)
        return VGroup(a)
    w, h = (.26, .12) if e < .35 else ((.36, .26) if e < .65 else (.44, .42))
    m = Ellipse(width=w, height=h, fill_color="#5A1F2B", fill_opacity=1, stroke_color=INK, stroke_width=4)
    tg = Ellipse(width=w*.6, height=h*.45, fill_color="#FF7A8A", fill_opacity=1, stroke_width=0).move_to(m.get_bottom() + UP*h*.22)
    return VGroup(m, tg) if h > .2 else VGroup(m)

def blink(t):
    ph = (t + .6) % 3.4
    return 1 - 0.95*(math.sin(PI*ph/.16) if ph < .16 else 0)

def build(t):
    g = VGroup()
    u = t/.85
    drop = (1 - ease_out_bounce(min(1, u)))*6.5 if t < .85 else 0
    sq = .22*math.exp(-(t - .62)*7)*math.cos((t - .62)*20) if t > .62 else 0
    e = env(t)
    bob = (.05*math.sin(2*PI*1.2*t) if t > 1 else 0) + .07*e
    # shadow
    g.add(ell(2.4 - .3*drop*.2, .35, 0, -1.95, "#000000", sw=0, op=.22))
    # shoes
    for sx in (-.55, .55): g.add(ell(.8, .38, sx, -1.78, "#3B2A2A", sw=3))
    # torso
    g.add(RoundedRectangle(width=2.0, height=1.9, corner_radius=.55, fill_color=COAT, fill_opacity=1, stroke_color=INK, stroke_width=4).move_to([0, -.88, 0]))
    for by in (-.7, -1.15): g.add(Dot([0, by, 0], radius=.07, color=INK))
    g.add(Polygon([-.45, -.05, 0], [.45, -.05, 0], [0, -.55, 0], fill_color=RED, fill_opacity=1, stroke_color=INK, stroke_width=3))
    # arms
    wave = T_WAVE[0] <= t <= T_WAVE[1]
    ang = 62 + 22*math.sin(2*PI*3.2*t) if wave else 0
    lhand = np.array([-1.35, -1.25 + .04*math.sin(2*PI*1.1*t), 0])
    rs = np.array([1.0, -.35, 0])
    rhand = rs + (np.array([math.cos(math.radians(ang))*1.0, math.sin(math.radians(ang))*1.0 + .2, 0]) if wave else np.array([.35, -.9 + .04*math.sin(2*PI*1.1*t + 1), 0]))
    for s_, h_ in ((np.array([-1.0, -.35, 0]), lhand), (rs, rhand)):
        g.add(Line(s_, h_, stroke_color=INK, stroke_width=16, stroke_opacity=1).set_cap_style(CapStyleType.ROUND))
        g.add(Line(s_, h_, stroke_color=COAT, stroke_width=9).set_cap_style(CapStyleType.ROUND))
        g.add(Dot(h_, radius=.2, color=SKIN).set_stroke(INK, 4))
    # head
    g.add(Circle(radius=1.2, fill_color=SKIN, fill_opacity=1, stroke_color=INK, stroke_width=5).move_to([0, .85, 0]))
    for sx in (-1.18, 1.18): g.add(ell(.35, .42, sx, .8, SKIN, sw=4))
    # hat
    g.add(*[Circle(radius=r_, fill_color=HAT, fill_opacity=1, stroke_color="#BBBBBB", stroke_width=4).move_to([x_, y_, 0]) for x_, y_, r_ in ((-.55, 2.55, .5), (.55, 2.55, .5), (0, 2.8, .58))])
    g.add(RoundedRectangle(width=1.8, height=.55, corner_radius=.12, fill_color=HAT, fill_opacity=1, stroke_color="#BBBBBB", stroke_width=4).move_to([0, 2.05, 0]))
    # cheeks
    for sx in (-.75, .75): g.add(ell(.4, .26, sx, .5, "#FF8FA3", sw=0, op=.55))
    # eyes
    wink = T_END_WINK[0] <= t <= T_END_WINK[1]
    for k, sx in enumerate((-.45, .45)):
        b = blink(t) if not (wink and k == 1) else .08
        g.add(ell(.5, .56*b, sx, 1.0, "#FFFFFF", sw=4))
        if b > .3:
            lx = .06*math.sin(t*.7) ; ly = .02*math.sin(t*1.3)
            g.add(ell(.22, .26*b, sx + lx, 1.0 + ly, "#2A1B2D", sw=0))
            g.add(Dot([sx + lx + .05, 1.05 + ly, 0], radius=.04, color=WHITE))
    # brows
    shock = sm((t - T_SHOCK)/.15) - sm((t - T_SHOCK - 1.3)/.3)
    greet = .08*sm((t - S1)/.3)*(1 - sm((t - S1 - 1.2)/.3))
    for sx, sgn in ((-.45, -1), (.45, 1)):
        by = 1.5 + .22*shock + greet + .05*e
        tilt = .16*shock*sgn
        g.add(Line([sx - .24, by - tilt*(-sgn)*.0 - sgn*(-.0), 0] if False else [sx - .24, by + (tilt if sgn < 0 else -tilt)*-1, 0],
                   [sx + .24, by + (tilt if sgn < 0 else -tilt), 0], stroke_color=INK, stroke_width=8).set_cap_style(CapStyleType.ROUND))
    g.add(ell(.14, .1, 0, .68, "#F2A98A", sw=0))
    m = mouth(e + (.5 if shock > .5 and e < .2 else 0)); m.move_to([0, .22, 0]); g.add(m)
    # transforms
    g.shift(UP*(bob + drop))
    feet = np.array([0, -2.0 + 0, 0])
    g.stretch(1 + sq, 0, about_point=feet); g.stretch(1 - sq, 1, about_point=feet)
    return g

T_END_WINK = (END + .1, END + .75)

class PennyTest(MovingCameraScene):
    def construct(self):
        self.clk = 0.0
        self.add_updater(lambda dt: setattr(self, "clk", self.clk + dt))
        self.camera.background_color = "#F6D9A8"
        bg = VGroup()
        bg.add(Rectangle(width=20, height=12, fill_color="#F7DDB0", fill_opacity=1, stroke_width=0))
        for i in range(-12, 12):
            for j in range(-5, 0):
                pass
        tiles = VGroup(*[Square(.9, fill_color="#F2E8D5" if (i+j) % 2 == 0 else "#E9DCC2", fill_opacity=1, stroke_width=0).move_to([-8 + i*.9, -.45 - j*.9, 0]) for i in range(20) for j in range(0, 5)])
        bg.add(tiles)
        bg.add(Rectangle(width=20, height=3.0, fill_color="#8B5A3C", fill_opacity=1, stroke_width=0).move_to([0, -3.9, 0]))
        bg.add(Rectangle(width=20, height=.22, fill_color="#B07A52", fill_opacity=1, stroke_width=0).move_to([0, -2.5, 0]))
        # window
        win = VGroup(RoundedRectangle(width=2.6, height=2.0, corner_radius=.15, fill_color="#9ED8F5", fill_opacity=1, stroke_color="#7A4A2A", stroke_width=8),
                     Circle(radius=.35, fill_color="#FFE066", fill_opacity=1, stroke_width=0).shift(UP*.3 + RIGHT*.5),
                     Line([0, -1, 0], [0, 1, 0], stroke_color="#7A4A2A", stroke_width=6), Line([-1.3, 0, 0], [1.3, 0, 0], stroke_color="#7A4A2A", stroke_width=6)).move_to([-5.2, 1.8, 0])
        bg.add(win)
        # shelf with jars
        bg.add(Rectangle(width=3.0, height=.18, fill_color="#7A4A2A", fill_opacity=1, stroke_width=0).move_to([-1.6, 2.7, 0]))
        for k, col in enumerate(("#E8454F", "#6BBF59", "#FFB347", "#E8454F")):
            bg.add(RoundedRectangle(width=.5, height=.7, corner_radius=.1, fill_color=col, fill_opacity=1, stroke_color=INK, stroke_width=3).move_to([-2.5 + k*.62, 3.12, 0]))
        # oven
        oven_b = RoundedRectangle(width=3.4, height=3.6, corner_radius=.3, fill_color="#5B4A4A", fill_opacity=1, stroke_color=INK, stroke_width=5).move_to([5.2, -.6, 0])
        door = RoundedRectangle(width=2.2, height=1.5, corner_radius=.2, fill_color="#2B1A1A", fill_opacity=1, stroke_color=INK, stroke_width=4).move_to([5.2, -.9, 0])
        fire = RoundedRectangle(width=1.8, height=1.1, corner_radius=.15, fill_color="#FF7A2F", fill_opacity=.85, stroke_width=0).move_to([5.2, -.9, 0])
        fire.add_updater(lambda m: m.set_fill(opacity=.75 + .15*math.sin(self.clk*7)))
        bg.add(oven_b, door, fire)
        glow = Circle(radius=2.6, fill_color="#FF9A3C", fill_opacity=.12, stroke_width=0).move_to([5.2, -.9, 0])
        glow.add_updater(lambda m: m.set_fill(opacity=.10 + .05*math.sin(self.clk*5)))
        # hanging pans
        for k in range(3):
            bg.add(Line([1.8 + k*.9, 4, 0], [1.8 + k*.9, 3.2, 0], stroke_color=INK, stroke_width=3), Circle(radius=.38, fill_color="#B5B5C3", fill_opacity=1, stroke_color=INK, stroke_width=4).move_to([1.8 + k*.9, 2.85, 0]))
        # pizza on counter
        pz = VGroup(Circle(radius=.8, fill_color="#F2C46B", fill_opacity=1, stroke_color=INK, stroke_width=4), Circle(radius=.62, fill_color="#E8454F", fill_opacity=.9, stroke_width=0),
                    *[Dot([.3*math.cos(a), .3*math.sin(a), 0], radius=.1, color="#FFE066") for a in np.linspace(0, 2*PI, 6, endpoint=False)]).move_to([2.6, -2.35, 0]).scale([1, .45, 1])
        self.add(bg, glow, pz)
        # steam
        steam = VGroup(*[Circle(radius=.2, fill_color=WHITE, fill_opacity=0, stroke_width=0) for _ in range(6)])
        def steam_up(m):
            t = self.clk
            for i, c in enumerate(m):
                u = (t*.35 + i/6) % 1
                c.move_to([5.2 + .35*math.sin(u*6 + i) , 1.4 + u*1.7, 0]).set(width=(.3 + .7*u)).set_fill(WHITE, opacity=.28*(1 - u))
        steam.add_updater(steam_up); self.add(steam)
        # character
        P = always_redraw(lambda: build(self.clk).shift(np.array([-1.7, -1.7, 0])))
        self.add(P)
        # particles: flour puff on landing, sparkles at the end
        rng = random.Random(4)
        puff = [(rng.uniform(.15, PI - .15), rng.uniform(1.6, 3.2), rng.uniform(.1, .22)) for _ in range(18)]
        def fx():
            t = self.clk; g = VGroup()
            tau = t - .7
            if 0 < tau < 1.0:
                for a, sp, r in puff:
                    for side in (-1, 1):
                        g.add(Circle(radius=r*(1 + 2*tau), fill_color="#FFFFFF", fill_opacity=.65*(1 - tau), stroke_width=0)
                              .move_to([-1.7 + side*(.9 + sp*math.cos(a)*tau*.6), -1.55 + sp*math.sin(a)*tau*.6 - 1.2*tau*tau, 0]))
            ts = END - .05; tau = t - ts
            if 0 < tau < 1.6:
                for k in range(14):
                    a = 2*PI*k/14 + .3; sp = 1.2 + (k % 3)*.7
                    c = [YELLOW, "#FFFFFF", "#FF7EC8"][k % 3]
                    st = Star(n=4, outer_radius=.22*(1 - tau/1.8), inner_radius=.07, fill_color=c, fill_opacity=1 - tau/1.6, stroke_width=0).rotate(tau*4 + k)
                    g.add(st.move_to([-1.7 + math.cos(a)*sp*tau*1.4, .9 + math.sin(a)*sp*tau*1.4 + .5, 0]))
                g.add(Circle(radius=.4 + tau*3.5, stroke_color=YELLOW, stroke_width=6, stroke_opacity=max(0, .8 - tau/1.2)).move_to([-1.7, 1.4, 0]))
            tau = t - T_SHOCK
            if 0 < tau < 1.2:   # exclamation badge pops over her head
                s = ease_out_bounce(min(1, tau/.35))
                b = VGroup(Circle(radius=.5, fill_color=RED, fill_opacity=1, stroke_color=INK, stroke_width=5), T("!", 54, WHITE, True)).scale(max(.01, s*(1 - sm((tau - .9)/.3)))).move_to([-.15, 3.25, 0])
                g.add(b)
            return g
        self.add(always_redraw(fx))
        fr = self.camera.frame; w0 = fr.width
        vig = VGroup(*[Annulus(inner_radius=5.0 + .55*i, outer_radius=14, fill_color="#140A1E", fill_opacity=.035, stroke_width=0) for i in range(11)])
        vig.set_z_index(50); vig.add_updater(lambda m: m.move_to(fr.get_center()))
        self.add(vig)
        def cam(m):
            t = self.clk; z = 1 - .09*sm(t/TOTAL)
            sh = max(0, 1 - (t - T_SHOCK)/.35) if t > T_SHOCK else 0
            m.set_width(w0*z); m.move_to([-.5*sm(t/TOTAL) + .07*sh*math.sin(t*90), -.25 + .07*sh*math.cos(t*77), 0])
        fr.add_updater(cam)
        # audio
        self.add_sound("music_loop.wav", time_offset=0, gain=-21)
        for p, s in zip(paths, STARTS): self.add_sound(p, time_offset=s)
        self.add_sound(f"{SFX}/whoosh.wav", time_offset=.05, gain=-7)
        self.add_sound(f"{SFX}/pop.wav", time_offset=.7, gain=-5)
        self.add_sound(f"{SFX}/rise.wav", time_offset=T_SHOCK, gain=-6)
        self.add_sound(f"{SFX}/buzz.wav", time_offset=T_SHOCK + .05, gain=-16)
        self.add_sound(f"{SFX}/ding.wav", time_offset=END - .05, gain=-7)
        self.add_sound(f"{SFX}/tada.wav", time_offset=END - .05, gain=-12)
        self.wait(TOTAL)
