import os, hashlib, math
import numpy as np
import soundfile as sf
from manim import *

ROOT = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(ROOT, "audio"); SFX = os.path.join(ROOT, "sfx")
TTS_DIR = "/tmp/claude-0/tts/kokoro-en-v0_19/"
os.makedirs(AUD, exist_ok=True); os.makedirs(SFX, exist_ok=True)

BG = "#0B1020"; PANEL = "#151C36"; PANEL2 = "#1D2647"; TXT = "#EEF2FF"; DIM = "#8E99C0"
BLUE = "#4DA3FF"; ORANGE = "#FF9F43"; GREEN = "#2ED8A3"; RED = "#FF5C7A"
PURPLE = "#B084FF"; YELLOW = "#FFD84D"; TEAL = "#3DD6D0"; PINK = "#FF7EC8"
FONT = "Inter"
VOICE, SPEED = 6, 1.0
config.background_color = BG

# ---------------------------------------------------------------- TTS
_tts = None
def tts(text):
    global _tts
    h = hashlib.md5(f"{VOICE}|{SPEED}|{text}".encode()).hexdigest()[:16]
    p = f"{AUD}/{h}.wav"
    if not os.path.exists(p):
        import sherpa_onnx
        if _tts is None:
            d = TTS_DIR
            c = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(),
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
                    data_dir=d + "espeak-ng-data"), num_threads=2))
            _tts = sherpa_onnx.OfflineTts(c)
        a = _tts.generate(text, sid=VOICE, speed=SPEED)
        sf.write(p, a.samples, a.sample_rate)
    return p, sf.info(p).duration

# ---------------------------------------------------------------- SFX (synthesised)
def _w(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.8
    sf.write(f"{SFX}/{name}.wav", x.astype(np.float32), 44100)
def make_sfx():
    sr = 44100
    t = np.linspace(0, .14, int(sr * .14), False)
    _w("pop", np.sin(2*np.pi*(500+3000*t)*t) * np.exp(-t*28))
    t = np.linspace(0, .7, int(sr * .7), False)
    n = np.random.RandomState(1).randn(len(t))
    k = np.convolve(n, np.ones(60)/60, "same") * np.sin(np.pi * t / .7) ** 2
    _w("whoosh", k)
    t = np.linspace(0, 1.0, sr, False)
    _w("ding", (np.sin(2*np.pi*880*t) + .5*np.sin(2*np.pi*1320*t)) * np.exp(-t*4.5))
    t = np.linspace(0, .5, int(sr*.5), False)
    _w("buzz", np.sign(np.sin(2*np.pi*110*t)) * np.exp(-t*5) * .5)
    t = np.linspace(0, .05, int(sr*.05), False)
    _w("tick", np.sin(2*np.pi*1800*t) * np.exp(-t*90))
    t = np.linspace(0, .35, int(sr*.35), False)
    _w("rise", np.sin(2*np.pi*(300+900*t/.35)*t) * np.sin(np.pi*t/.35))
    t = np.linspace(0, .6, int(sr*.6), False)
    _w("tada", sum(np.sin(2*np.pi*f*t) for f in (523, 659, 784, 1047)) * np.exp(-t*5))
if not os.path.exists(f"{SFX}/pop.wav"): make_sfx()

# ---------------------------------------------------------------- mobject helpers
def T(s, size=36, color=TXT, bold=False, **kw):
    return Text(s, font=FONT, font_size=size, color=color, weight=BOLD if bold else NORMAL, **kw)

def card(w, h, fill=PANEL, stroke=PANEL2, r=0.25):
    return RoundedRectangle(width=w, height=h, corner_radius=r, fill_color=fill, fill_opacity=1,
                            stroke_color=stroke, stroke_width=2)

def pill(s, color, size=26, padx=0.5, pady=0.2):
    t = T(s, size, BG, True)
    r = RoundedRectangle(width=t.width + padx*2, height=t.height + pady*2, corner_radius=0.3,
                         fill_color=color, fill_opacity=1, stroke_width=0)
    t.move_to(r); return VGroup(r, t)

def person(color=BLUE, s=1.0):
    head = Circle(radius=.15*s, fill_color=color, fill_opacity=1, stroke_width=0)
    body = RoundedRectangle(width=.4*s, height=.42*s, corner_radius=.17*s, fill_color=color,
                            fill_opacity=1, stroke_width=0)
    body.next_to(head, DOWN, buff=.04*s)
    return VGroup(head, body)

def oven(s=1.0):
    b = RoundedRectangle(width=1.8*s, height=1.3*s, corner_radius=.2*s, fill_color="#3A2A2A",
                         fill_opacity=1, stroke_color=ORANGE, stroke_width=3)
    w = RoundedRectangle(width=1.1*s, height=.6*s, corner_radius=.12*s, fill_color="#FF7A2F",
                         fill_opacity=.9, stroke_width=0).shift(DOWN*.1*s)
    return VGroup(b, w)

class Tbl(VGroup):
    """Grid table. rows: list of lists of str. hide: set of (r,c) body cells revealed later."""
    def __init__(self, headers, rows, cw=1.9, rh=.62, fs=28, hcolors=None, hide=(), **kw):
        super().__init__(**kw)
        self.cw, self.rh, self.fs = cw, rh, fs
        n = len(headers)
        self.rects, self.txt, self.hidden = {}, {}, {}
        W = cw * n if not isinstance(cw, (list, tuple)) else sum(cw)
        ws = cw if isinstance(cw, (list, tuple)) else [cw]*n
        xs = np.cumsum([0] + list(ws))
        for c, h in enumerate(headers):
            col = (hcolors or [BLUE]*n)[c]
            r = Rectangle(width=ws[c], height=rh*1.15, fill_color=col, fill_opacity=.95, stroke_color=BG, stroke_width=2)
            r.move_to([xs[c] + ws[c]/2, 0, 0]); t = T(h, fs*.82, BG, True).move_to(r)
            if t.width > ws[c]-.2: t.scale((ws[c]-.2)/t.width)
            self.rects[(-1, c)] = r; self.txt[(-1, c)] = t; self.add(r, t)
        for i, row in enumerate(rows):
            for c, v in enumerate(row):
                r = Rectangle(width=ws[c], height=rh, fill_color=PANEL if i % 2 == 0 else PANEL2, fill_opacity=1,
                              stroke_color=BG, stroke_width=2)
                r.move_to([xs[c] + ws[c]/2, -(rh*1.15/2 + rh/2 + i*rh), 0])
                t = T(v, fs, TXT).move_to(r)
                self.rects[(i, c)] = r; self.add(r)
                if (i, c) in hide: self.hidden[(i, c)] = t
                else: self.txt[(i, c)] = t; self.add(t)
        self.move_to(ORIGIN)
        # hidden texts were positioned before move_to; shift them identically
        # (recompute by aligning to their rect)
        for k, t in self.hidden.items(): t.move_to(self.rects[k])
    def reveal(self, r, c, color=None):
        t = self.hidden[(r, c)]
        t.move_to(self.rects[(r, c)])
        if color: t.set_color(color)
        return t
    def row_rects(self, r):
        return VGroup(*[v for (i, c), v in self.rects.items() if i == r])
    def hl(self, r, c, color=YELLOW):
        return self.rects[(r, c)].copy().set_fill(opacity=0).set_stroke(color, 5)

def axes_xy(xr, yr, w, h, xl, yl, xcol=DIM, ycol=DIM, xs=None, ys=None, nums=True, lsize=26, xbase=None):
    ax = Axes(x_range=[xr[0], xr[1], xr[2]], y_range=[yr[0], yr[1], yr[2]], x_length=w, y_length=h,
              axis_config=dict(color=DIM, stroke_width=3, include_tip=True, tip_width=.16, tip_height=.16,
                               include_ticks=True, tick_size=.06, include_numbers=False),
              tips=True)
    g = VGroup(ax)
    if nums:
        for x in (xs if xs is not None else np.arange(xr[0] + xr[2], xr[1] + 1e-6, xr[2])):
            g.add(T(f"{x:g}", 20, DIM).next_to(ax.c2p(x, xbase if xbase is not None else (0 if yr[0] < 0 else yr[0])), DOWN, buff=.12))
        for y in (ys if ys is not None else np.arange(yr[0] + yr[2], yr[1] + 1e-6, yr[2])):
            g.add(T(f"{y:g}", 20, DIM).next_to(ax.c2p(xr[0], y), LEFT, buff=.12))
    g.add(T(xl, lsize, xcol).next_to(ax.c2p(xr[1], yr[0]), DOWN, buff=.45 if nums else .15).align_to(ax.c2p(xr[1], yr[0]), RIGHT))
    g.add(T(yl, lsize, ycol).next_to(ax.y_axis.get_end(), UP, buff=.15).shift(RIGHT*.3))
    return ax, g

def smooth(ax, pts, color, w=7, glow=True):
    from scipy.interpolate import PchipInterpolator
    xs, ys = zip(*pts)
    f = PchipInterpolator(xs, ys)
    xx = np.linspace(xs[0], xs[-1], 160)
    m = VMobject().set_points_as_corners([ax.c2p(x, f(x)) for x in xx]).set_stroke(color, w).set_fill(opacity=0)
    m.f = f
    if not glow: return m
    g = m.copy().set_stroke(color, w*2.6, opacity=.22)
    out = VGroup(g, m); out.f = f; out.line = m
    return out

def dots(ax, pts, color, r=.09):
    return VGroup(*[Dot(ax.c2p(*p), radius=r, color=color) for p in pts])

def num_t(v, size=40, color=TXT, bold=True):
    return T(v, size, color, bold)

# ---------------------------------------------------------------- base scene
CHAPTERS = ["Production", "Short-run costs", "Long-run costs"]
class Ep(Scene):
    chap = 0           # 0 = none, 1..3 shows chapter dots
    def setup(self):
        self._aend = 0.0
        # ambient drifting colour blobs
        self.blobs = VGroup()
        for i, (col, p) in enumerate([(BLUE, (-5, 2)), (PURPLE, (5, -2)), (TEAL, (0, -3.5))]):
            b = Circle(radius=3.2, fill_color=col, fill_opacity=.07, stroke_width=0).move_to([*p, 0])
            b.base = np.array([*p, 0.0]); b.ph = i * 2.1
            b.add_updater(lambda m, dt=0: m.move_to(m.base + np.array([1.2*math.sin(self.renderer.time*.25 + m.ph),
                                                                       .8*math.cos(self.renderer.time*.2 + m.ph), 0])))
            self.blobs.add(b)
        self.add(self.blobs)
        if self.chap:
            g = VGroup()
            for i, nm in enumerate(CHAPTERS, 1):
                on = i == self.chap
                d = Circle(radius=.09, fill_color=BLUE if on else DIM, fill_opacity=1 if on else .35, stroke_width=0)
                t = T(f"{i}  {nm}", 20, TXT if on else DIM, on)
                g.add(VGroup(d, t.next_to(d, RIGHT, buff=.15)))
            g.arrange(RIGHT, buff=.5).to_corner(UL, buff=.25)
            self.add(g); self.chapbar = g
    # --- narration
    def say(self, text, pad=.3):
        self.sync()
        p, d = tts(text)
        self.add_sound(p)
        self._aend = self.renderer.time + d + pad
        return d
    def sync(self):
        r = self._aend - self.renderer.time
        if r > .01: self.wait(r)
    def sfx(self, name, delay=0, gain=-9):
        self.add_sound(f"{SFX}/{name}.wav", time_offset=delay, gain=gain)
    def countdown(self, secs, pos=None, color=YELLOW):
        tr = ValueTracker(secs)
        ring = always_redraw(lambda: VGroup(
            Circle(radius=.55, stroke_color=PANEL2, stroke_width=8),
            Arc(radius=.55, start_angle=PI/2, angle=TAU*tr.get_value()/secs, stroke_color=color, stroke_width=8),
            T(str(max(0, math.ceil(tr.get_value()-1e-6))), 34, TXT, True)).move_to(pos if pos is not None else ORIGIN))
        self.add(ring)
        for s in range(int(secs)):
            self.sfx("tick", s, -14)
        self.play(tr.animate.set_value(0), run_time=secs, rate_func=linear)
        self.remove(ring)
    def fade_all(self, t=.6):
        keep = [self.blobs] + ([self.chapbar] if self.chap else [])
        self.play(*[FadeOut(m) for m in self.mobjects if m not in keep], run_time=t)
    def title(self, s, color=TXT, size=54, y=3.1):
        t = T(s, size, color, True).move_to(UP*y)
        return t


import textwrap
def mcq(sc, question, options, correct, why, narr_q, narr_a, secs=10, qsize=30):
    """Quiz-show style multiple choice. options: list of 5 strings, correct: index."""
    tag = pill("QUICK CHECK", PINK, 22).move_to(UP*3.05 + LEFT*5.6)
    q = T(textwrap.fill(question, 72), 27, TXT, True, line_spacing=1.2)
    if q.width > 12.6: q.scale(12.6/q.width)
    q.move_to(UP*1.75)
    sc.say(narr_q)
    sc.sfx("whoosh"); sc.play(FadeIn(tag, shift=RIGHT*.3), Write(q), run_time=1.6)
    rows = VGroup()
    for i, o in enumerate(options):
        t = T(textwrap.fill(o, 78), 23, TXT)
        if t.width > 10.4: t.scale(10.4/t.width)
        h = max(.6, t.height + .26)
        bx = card(11.6, h, fill=PANEL, stroke=PANEL2, r=.18)
        ltr = T("ABCDE"[i], 24, BG, True)
        c = Circle(radius=.24, fill_color=DIM, fill_opacity=1, stroke_width=0)
        ltr.move_to(c)
        cc = VGroup(c, ltr).move_to(bx.get_left() + RIGHT*.5)
        t.next_to(cc, RIGHT, buff=.35)
        rows.add(VGroup(bx, cc, t))
    rows.arrange(DOWN, buff=.1).move_to(DOWN*.9)
    sc.play(LaggedStart(*[FadeIn(r, shift=UP*.25) for r in rows], lag_ratio=.18), run_time=1.6)
    sc.sync()
    pz = T("PAUSE & PICK", 26, YELLOW, True).move_to(RIGHT*3.9 + UP*3.0)
    sc.play(FadeIn(pz))
    sc.countdown(secs, pos=RIGHT*6.1 + UP*3.0)
    sc.play(FadeOut(pz), run_time=.3)
    sc.say(narr_a)
    for i, r in enumerate(rows):
        if i != correct: sc.play(r.animate.set_opacity(.28), run_time=.12)
    sc.sfx("ding")
    r = rows[correct]
    chk = VGroup(Line(LEFT*.14 + UP*.0, DOWN*.12 + LEFT*.04, color=BG, stroke_width=7),
                 Line(DOWN*.12 + LEFT*.04, RIGHT*.18 + UP*.14, color=BG, stroke_width=7))
    sc.play(r[0].animate.set_stroke(GREEN, 5).set_fill(PANEL2), r[1][0].animate.set_color(GREEN),
            Indicate(r, color=GREEN, scale_factor=1.03), run_time=.8)
    chk.move_to(r[1][0]); sc.play(FadeOut(r[1][1]), Create(chk), run_time=.4)
    wh = card(11.6, 1.3, stroke=GREEN)
    wt = T(textwrap.fill(why, 100), 21, TXT, line_spacing=1.2)
    if wt.width > 10.8: wt.scale(10.8/wt.width)
    wh = card(11.6, wt.height + .45, stroke=GREEN).move_to(DOWN*3.3); wt.move_to(wh)
    sc.play(FadeIn(wh, shift=UP*.3), Write(wt), run_time=1.5)
    sc.sync(); sc.wait(.6)
    sc.fade_all(.6)

def place(ax, g, x0, ybot):
    """shift axes group so the plot box's bottom-left corner sits at (x0, ybot)"""
    p = ax.c2p(ax.x_range[0], ax.y_range[0])
    g.shift(np.array([x0 - p[0], ybot - p[1], 0]))
