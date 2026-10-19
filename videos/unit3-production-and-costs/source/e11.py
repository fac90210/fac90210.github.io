from lib import *

def c_of_m(m): return 7.0 + .2*max(0, abs(m - 5.2) - 1.0)**2
K = .7
def srac(m): return lambda q: c_of_m(m) + K*(q - m)**2
MS = [1.6, 3.4, 5.2, 7.0, 8.8]
def lrac(q): return min(srac(m)(q) for m in np.arange(.3, 11, .02))

class E11(Ep):
    chap = 3
    def construct(self):
        t = T("Long-Run Costs", 46, TXT, True).move_to(UP*2.75)
        self.say("Chapter three: the long run. Here, every input is flexible, including the size of the plant itself.")
        self.play(Write(t), run_time=.9); self.sync()
        ax, g = axes_xy((0, 10.4, 1), (0, 14, 2), 9.4, 4.4, "output (Q)", "unit cost", xs=[], ys=[], lsize=22)
        place(ax, g, -6.6, -3.0)
        self.play(Create(g), run_time=1)
        cols = [BLUE, TEAL, GREEN, ORANGE, RED]
        names = ["SRAC 1", "SRAC 2", "SRAC 3", "SRAC 4", "SRAC 5"]
        curves = []
        def draw_sr(m, col, w=6):
            f = srac(m)
            return ax.plot(f, x_range=[max(.15, m - 2.3), min(10.3, m + 2.3), .05], color=col, stroke_width=w, use_smoothing=False)
        narr = ["Each plant size has its own short-run average cost curve. Here's a small plant. It can't specialize or use mass production, so even at its best, cost per unit is high.",
                "Build a bigger plant, and cost per unit drops.",
                "Bigger again, and we hit the lowest cost.",
                "But keep growing...",
                "...and the plant becomes too big to manage. Cost per unit climbs again."]
        labs = []
        for i, (m, col, nm, nr) in enumerate(zip(MS, cols, names, narr)):
            c = draw_sr(m, col); curves.append(c)
            self.say(nr)
            lab = T(nm, 22, col, True).next_to(ax.c2p(m, c_of_m(m)), DOWN, buff=.15) if False else T(nm, 22, col, True).move_to(ax.c2p(m, c_of_m(m) - 1.9))
            labs.append(lab)
            self.sfx("pop"); self.play(Create(c), FadeIn(lab, shift=UP*.2), run_time=1.1)
        self.sync()
        # envelope
        qs = np.arange(.3, 10.3, .05)
        env = VMobject().set_points_as_corners([ax.c2p(q, lrac(q)) for q in qs]).set_stroke(WHITE, 8).set_fill(opacity=0)
        glow = env.copy().set_stroke(WHITE, 20, opacity=.2)
        self.say("In the long run, the firm gets to choose whichever plant gives it the lowest cost for each level of output. So the long-run average cost curve is the lower edge of all those short-run curves. Add more and more plant sizes, and the edge smooths into one curve.")
        extra = VGroup(*[draw_sr(m, GREY_B, 2).set_stroke(opacity=.55) for m in (.9, 2.5, 4.3, 6.1, 7.9, 9.6)])
        self.play(FadeIn(extra), run_time=1.0)
        self.sfx("rise"); self.play(Create(env), FadeIn(glow), run_time=2.6)
        lr = T("LRATC", 30, WHITE, True).next_to(ax.c2p(9.6, lrac(9.6)), UP, buff=.2).shift(RIGHT*.1)
        self.play(FadeIn(lr)); self.sync()
        self.play(FadeOut(extra), *[c.animate.set_stroke(opacity=.35) for c in curves], *[FadeOut(l) for l in labs], run_time=.7)

        # regions
        def reg(a, b, col, nm, desc, y):
            xa, xb = ax.c2p(a, 0)[0], ax.c2p(b, 0)[0]
            band = Rectangle(width=xb - xa, height=ax.y_length, fill_color=col, fill_opacity=.12, stroke_width=0).move_to([(xa+xb)/2, ax.c2p(0, 7)[1], 0])
            return band
        b1 = reg(.15, 4.2, GREEN, "", "", 0); b2 = reg(4.2, 6.2, YELLOW, "", "", 0); b3 = reg(6.2, 10.3, RED, "", "", 0)
        r_info = [("ECONOMIES OF SCALE", GREEN, "LRATC falls as output grows", 2.2),
                  ("CONSTANT RETURNS", YELLOW, "LRATC is at its lowest", 5.2),
                  ("DISECONOMIES OF SCALE", RED, "LRATC rises as output grows", 8.2)]
        labels = []
        for (nm, col, d, x) in r_info:
            tt = VGroup(T(nm, 20, col, True), T(d, 18, TXT)).arrange(DOWN, buff=.08).move_to(ax.c2p(x, 12.9 if x != 5.2 else 3.0))
            labels.append(tt)
        txts = ["Where the curve slopes down, we have economies of scale. Bigger is cheaper per unit, thanks to specialization and mass production.",
                "Along the flat bottom, costs per unit stay the same. That's constant returns to scale. The smallest output where the curve reaches this bottom is called the minimum efficient scale.",
                "And where the curve slopes up, there are diseconomies of scale. The firm is too big, too hard to manage, and cost per unit rises."]
        for b, l, tx in zip((b1, b2, b3), labels, txts):
            self.say(tx); self.sfx("pop")
            self.play(FadeIn(b), FadeIn(l, shift=DOWN*.2), run_time=1)
            if b is b2:
                mes = DashedLine(ax.c2p(4.2, 0), ax.c2p(4.2, lrac(4.2)), color=YELLOW, stroke_width=4)
                md = Dot(ax.c2p(4.2, lrac(4.2)), radius=.14, color=YELLOW).set_stroke(WHITE, 3)
                ml = T("MES", 26, YELLOW, True).next_to(ax.c2p(4.2, 0), DOWN, buff=.2)
                self.play(Create(mes), FadeIn(md, scale=2), FadeIn(ml)); 
        self.sync(); self.wait(.6)
        self.fade_all(.7)

        # ---------- returns to scale
        t = T("Returns to Scale", 46, TXT, True).move_to(UP*2.75)
        self.say("Economies of scale have a twin from the production side: returns to scale. Imagine the firm doubles every single input. What happens to output?")
        self.play(Write(t), run_time=.9); self.sync()
        rows = [("Output MORE than doubles", 2.5, GREEN, "Increasing returns to scale", "→ economies of scale"),
                ("Output exactly doubles", 2.0, YELLOW, "Constant returns to scale", "→ LRATC stays flat"),
                ("Output LESS than doubles", 1.5, RED, "Decreasing returns to scale", "→ diseconomies of scale")]
        grp = VGroup()
        for lbl, mult, col, nm, eff in rows:
            cd = card(12.6, 1.35, stroke=col)
            tl = T(lbl, 24, col, True).move_to(cd.get_left() + RIGHT*2.5 + UP*.25)
            nl = T(nm, 22, TXT).move_to(cd.get_left() + RIGHT*2.5 + DOWN*.25)
            ref = Rectangle(width=2.0*1.4, height=.28, fill_color=PANEL2, fill_opacity=1, stroke_width=0)
            ref.move_to(cd.get_center() + RIGHT*.5 + UP*.25).align_to(cd.get_center() + RIGHT*.1, LEFT)
            out = Rectangle(width=mult*1.4, height=.28, fill_color=col, fill_opacity=.95, stroke_width=0).align_to(ref, LEFT).move_to(cd.get_center() + UP*.25 + RIGHT*.1, coor_mask=[0, 1, 0]).align_to(ref, LEFT)
            eg = T(eff, 22, col, True).move_to(cd.get_right() + LEFT*2.3 + DOWN*.3)
            m_ = T(f"output × {mult:g}", 22, TXT, True).next_to(out, RIGHT, buff=.25)
            i_ = T("inputs × 2", 20, DIM).align_to(ref, LEFT).move_to(cd.get_center() + DOWN*.3 + RIGHT*.1).align_to(ref, LEFT)
            grp.add(VGroup(cd, tl, nl, ref, out, eg, m_, i_))
        grp.arrange(DOWN, buff=.3).move_to(DOWN*.5)
        narr = ["If output more than doubles, that's increasing returns to scale. Cost per unit falls, which is economies of scale.",
                "If output exactly doubles, that's constant returns to scale, and cost per unit stays the same.",
                "And if output less than doubles, those are decreasing returns to scale. Cost per unit rises: diseconomies of scale."]
        for r, n in zip(grp, narr):
            self.say(n); self.sfx("pop")
            outbar = r[4]; w = outbar.width
            self.play(FadeIn(VGroup(r[0], r[1], r[2], r[3], r[7]), shift=UP*.3), run_time=.7)
            outbar.save_state(); outbar.stretch_to_fit_width(.01, about_edge=LEFT)
            self.play(Restore(outbar), FadeIn(r[6]), run_time=1.0); self.play(FadeIn(r[5], shift=LEFT*.3))
        self.sync(); self.wait(.6)
        self.fade_all(.7)
        mcq(self, "Assume a firm doubles its usage of each input, resulting in a doubling of the firm's output. Which of the following describes this result?",
            ["Increasing total cost", "Diminishing marginal returns", "Decreasing returns to scale", "Constant returns to scale", "Increasing returns to scale"], 3,
            "Every input doubled and output doubled exactly: that's constant returns to scale. Diminishing marginal returns is a short-run idea, where one input is held fixed.",
            "Let's test that. A firm doubles every input, and its output exactly doubles. What do we call that? Pause and choose.",
            "The answer is D, constant returns to scale. Output grew in exact proportion to inputs. And notice that diminishing marginal returns can't be right, because that's a short-run idea where at least one input is fixed. Here, everything changed.", secs=7)
