from lib import *

TPp = [(0, 0), (1, 15), (2, 34), (3, 48), (4, 60), (5, 62), (6, 60)]
MPp = [(.5, 15), (1.5, 19), (2.5, 14), (3.5, 12), (4.5, 2), (5.5, -2)]
APp = [(1, 15), (2, 17), (3, 16), (4, 15), (5, 12.4), (6, 10)]

class E05(Ep):
    chap = 1
    def construct(self):
        X0, W = -6.3, 7.8
        axT, gT = axes_xy((0, 6.5, 1), (0, 70, 20), W, 2.5, "workers", "TP", BLUE, BLUE, xs=[], ys=[0, 20, 40, 60], lsize=22)
        axM, gM = axes_xy((0, 6.5, 1), (-6, 22, 4), W, 2.5, "workers", "MP · AP", ORANGE, ORANGE, xs=[1, 2, 3, 4, 5, 6], ys=[0, 10, 20], lsize=22, xbase=-6)
        place(axT, gT, X0, -.35 + 0.0); place(axM, gM, X0, -3.55)
        tpc = smooth(axT, TPp, BLUE); mpc = smooth(axM, MPp, ORANGE); apc = smooth(axM, APp, GREEN)
        lb_tp = T("TP", 28, BLUE, True).next_to(axT.c2p(6, 60), RIGHT, buff=.15)
        lb_mp = T("MP", 28, ORANGE, True).next_to(axM.c2p(5.5, -2), RIGHT, buff=.15).shift(DOWN*.15)
        lb_ap = T("AP", 28, GREEN, True).next_to(axM.c2p(6, 10), RIGHT, buff=.15)

        self.say("Let's graph our practice problem. Total product goes on top. Marginal and average product go underneath, sharing the same horizontal axis: the number of workers.")
        self.play(Create(gT), Create(gM), run_time=1.6); self.sync()
        self.say("Total product first climbs steeply, then flattens out, peaks at five workers, and then turns down.")
        self.play(Create(tpc), FadeIn(lb_tp), run_time=2.0)
        self.play(FadeIn(dots(axT, TPp, BLUE, .08), lag_ratio=.1)); self.sync()
        self.say("Marginal product, in orange, rises to a peak and then falls, even below zero. Average product, in green, follows a similar hump, but a little behind.")
        self.play(Create(mpc), FadeIn(lb_mp), run_time=1.6)
        self.play(Create(apc), FadeIn(lb_ap), run_time=1.6); self.sync()

        # tracker
        tr = ValueTracker(0.0)
        def fMP(x): return float(mpc.f(min(5.5, max(.5, x))))
        vline = always_redraw(lambda: DashedLine(axT.c2p(tr.get_value(), 70), axM.c2p(tr.get_value(), -6), color=YELLOW, stroke_width=3, dash_length=.1))
        dTP = always_redraw(lambda: Dot(axT.c2p(tr.get_value(), float(tpc.f(tr.get_value()))), radius=.13, color=BLUE).set_stroke(WHITE, 3))
        dMP = always_redraw(lambda: Dot(axM.c2p(tr.get_value(), fMP(tr.get_value())), radius=.13, color=ORANGE).set_stroke(WHITE, 3))
        panel = card(4.5, 3.0, stroke=PANEL2).move_to(RIGHT*4.6 + UP*.9)
        def stage():
            x = tr.get_value()
            if x < 1.5: s, c, d = "INCREASING", GREEN, "MP rising → TP gets steeper"
            elif x < 5.0: s, c, d = "DIMINISHING", YELLOW, "MP falling → TP flattens"
            else: s, c, d = "NEGATIVE", RED, "MP < 0 → TP falls"
            g = VGroup(T(s, 30, c, True), T(d, 22, TXT)).arrange(DOWN, buff=.3)
            return g.move_to(panel.get_center())
        st = always_redraw(stage)
        self.say("Now watch the two graphs together. The slope of total product, how steep it is, is exactly marginal product.")
        self.add(vline, dTP, dMP); self.play(FadeIn(panel, shift=LEFT*.3)); self.add(st)
        self.sfx("rise")
        self.play(tr.animate.set_value(1.5), run_time=3.2, rate_func=linear)
        self.say("While marginal product is rising, total product gets steeper and steeper.")
        self.play(tr.animate.set_value(1.5), run_time=.01)
        self.sync()
        self.say("Once marginal product starts falling, diminishing returns, total product keeps rising, but it flattens out.")
        self.play(tr.animate.set_value(5.0), run_time=5.0, rate_func=linear); self.sync()
        self.say("And when marginal product goes negative, total product actually falls.")
        self.play(tr.animate.set_value(6.0), run_time=3.0, rate_func=linear); self.sync()
        self.play(FadeOut(vline), FadeOut(dTP), FadeOut(dMP), FadeOut(st), FadeOut(panel))

        # MP / AP intersection
        px, py = 1.93, 17.0
        pt = Dot(axM.c2p(px, py), radius=.15, color=YELLOW).set_stroke(WHITE, 3)
        ring = Circle(radius=.35, color=YELLOW, stroke_width=4).move_to(pt)
        c1 = card(4.6, 2.9, stroke=YELLOW).move_to(RIGHT*4.6 + UP*.9)
        rules = VGroup(T("MP pulls AP along", 28, YELLOW, True),
                       T("MP > AP  →  AP rises", 24, GREEN, True),
                       T("MP < AP  →  AP falls", 24, RED, True),
                       T("MP crosses AP at AP's max", 24, TXT, True)).arrange(DOWN, aligned_edge=LEFT, buff=.3)
        rules.scale(4.0/rules.width).move_to(c1)
        self.say("One more thing. Marginal product crosses average product right at the top of the average product curve. When MP is above AP, it pulls the average up. When MP drops below AP, it drags the average down.")
        self.play(FadeIn(pt, scale=2), Create(ring), FadeIn(c1, shift=LEFT*.3), run_time=1)
        self.sfx("pop")
        for r_ in rules:
            self.play(FadeIn(r_, shift=RIGHT*.3), run_time=.7)
        self.play(Indicate(pt, scale_factor=1.6, color=YELLOW), run_time=1)
        self.sync(); self.wait(.6)
        self.fade_all(.7)
