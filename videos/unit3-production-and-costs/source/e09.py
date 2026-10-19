from lib import *

QP = range(1, 7)
MCp = [(1, 25), (2, 20), (3, 15), (4, 20), (5, 30), (6, 40)]
AVCp = [(1, 25), (2, 22.5), (3, 20), (4, 20), (5, 22), (6, 25)]
ATCp = [(1, 65), (2, 42.5), (3, 33.3), (4, 30), (5, 30), (6, 31.7)]

class E09(Ep):
    chap = 2
    def construct(self):
        t = T("The Cost Curves", 46, TXT, True).move_to(UP*2.75)
        self.say("Now for the main event. Let's graph the farm's costs.")
        self.play(Write(t), run_time=.9); self.sync()
        ax, g = axes_xy((0, 7, 1), (0, 70, 10), 8.0, 4.5, "quantity", "cost ($)", xs=[1, 2, 3, 4, 5, 6], ys=[20, 40, 60], lsize=22)
        place(ax, g, -6.4, -3.05)
        self.play(Create(g), run_time=1.2)
        atc = smooth(ax, ATCp, PURPLE); avc = smooth(ax, AVCp, YELLOW); mc = smooth(ax, MCp, RED)
        la = T("ATC", 26, PURPLE, True).next_to(ax.c2p(6, 31.7), RIGHT, buff=.15).shift(UP*.15)
        lv = T("AVC", 26, YELLOW, True).next_to(ax.c2p(6, 25), RIGHT, buff=.15).shift(DOWN*.2)
        lm = T("MC", 26, RED, True).next_to(ax.c2p(6, 40), RIGHT, buff=.15)
        self.say("Average total cost and average variable cost are both U-shaped. They fall at first, as workers specialize, then rise once diminishing returns kick in.")
        self.sfx("rise"); self.play(Create(atc), FadeIn(la), run_time=1.6)
        self.play(Create(avc), FadeIn(lv), run_time=1.6); self.sync()
        self.say("Marginal cost is U-shaped too, only steeper. It dips, then climbs.")
        self.play(Create(mc), FadeIn(lm), run_time=1.8); self.sync()

        # AFC gap
        def gap(q, a, b):
            return VGroup(DoubleArrow(ax.c2p(q, a), ax.c2p(q, b), buff=0, color=TEAL, stroke_width=5, tip_length=.15),
                          T(f"AFC = {b-a:g}", 20, TEAL, True).next_to(ax.c2p(q, (a+b)/2), RIGHT, buff=.15))
        g1, g2 = gap(2, 22.5, 42.5), gap(5, 22, 30)
        self.say("See the gap between ATC and AVC? That's average fixed cost. At two bushels it's twenty dollars. At five it's only eight. The gap keeps shrinking, because the fixed cost is spread over more units.")
        self.play(FadeIn(g1, scale=.8), run_time=.8); self.play(FadeIn(g2, scale=.8), run_time=.8); self.sync()
        self.play(FadeOut(g1), FadeOut(g2), run_time=.4)

        # MC crossing minima
        p1 = Dot(ax.c2p(4, 20), radius=.13, color=WHITE); p2 = Dot(ax.c2p(5, 30), radius=.13, color=WHITE)
        r1 = Circle(radius=.35, color=WHITE, stroke_width=4).move_to(p1); r2 = Circle(radius=.35, color=WHITE, stroke_width=4).move_to(p2)
        card_ = card(4.6, 2.4, stroke=RED).move_to(RIGHT*4.8 + UP*.7)
        ct = VGroup(T("THE KEY RULE", 24, RED, True), T("MC always cuts through the\nlowest point of ATC and AVC", 21, TXT, True)).arrange(DOWN, buff=.25).move_to(card_)
        self.say("Here's the rule you absolutely must remember. Marginal cost always crosses through the very bottom of both the AVC curve and the ATC curve.")
        self.sfx("pop"); self.play(FadeIn(p1, scale=2), Create(r1), FadeIn(p2, scale=2), Create(r2), FadeIn(card_, shift=LEFT*.3), Write(ct), run_time=1.6)
        self.play(Indicate(p1, color=YELLOW, scale_factor=1.8), Indicate(p2, color=YELLOW, scale_factor=1.8)); self.sync()

        # test score analogy
        self.play(FadeOut(card_), FadeOut(ct), run_time=.4)
        an = card(4.8, 4.4, stroke=YELLOW).move_to(RIGHT*4.7 + DOWN*.3)
        hd = T("WHY? Think test scores", 26, YELLOW, True).move_to(an.get_top() + DOWN*.5)
        l1 = T("Your average: 80", 28, PURPLE, True)
        l2 = T("Next test: 95", 26, RED, True); l2b = T("average goes UP ↑", 26, GREEN, True)
        l3 = T("Next test: 60", 26, RED, True); l3b = T("average goes DOWN ↓", 26, RED, True)
        l4 = T("MC = next test, ATC = average", 22, TXT, True)
        gr = VGroup(l1, VGroup(l2, l2b).arrange(RIGHT, buff=.3), VGroup(l3, l3b).arrange(RIGHT, buff=.3), l4).arrange(DOWN, buff=.4).move_to(an.get_center() + DOWN*.3)
        for x in gr:
            if x.width > 4.3: x.scale(4.3/x.width)
        self.say("Why? Think about test scores. Your average is eighty. If your next test is a ninety-five, your average goes up. If it's a sixty, it drops. Marginal cost is the next test. Average cost is your running average. So when MC is below ATC, ATC falls. When MC is above ATC, ATC rises. And right where they meet is the bottom of the U.")
        self.play(FadeIn(an, shift=LEFT*.3), Write(hd), run_time=1)
        self.play(FadeIn(gr[0], shift=UP*.2)); self.play(FadeIn(gr[1], shift=UP*.2)); self.play(FadeIn(gr[2], shift=UP*.2)); self.play(FadeIn(gr[3], shift=UP*.2))
        self.sync(); self.wait(.8)
        self.fade_all(.7)

        # ---------- MP and MC mirror
        t = T("Marginal Product vs. Marginal Cost", 44, TXT, True).move_to(UP*2.75)
        self.say("One last connection. Marginal cost and marginal product are two sides of the same coin: input and output.")
        self.play(Write(t), run_time=1); self.sync()
        fmp = lambda x: 20 - 3.5*(1.8 - x)**2 if x < 1.8 else 20 - 1.5*(x - 1.8)**2
        fmc = lambda x: 100.0 / fmp(x)
        a1, g1_ = axes_xy((0, 5.4, 1), (0, 24, 8), 7.8, 2.1, "workers (output)", "MP", ORANGE, ORANGE, nums=False, lsize=20)
        a2, g2_ = axes_xy((0, 5.4, 1), (0, 12, 4), 7.8, 2.1, "output", "MC", RED, RED, nums=False, lsize=20)
        place(a1, g1_, -6.5, .05); place(a2, g2_, -6.5, -3.3)
        c1 = a1.plot(fmp, x_range=[.3, 4.3, .05], color=ORANGE, stroke_width=7, use_smoothing=False)
        c2 = a2.plot(fmc, x_range=[.3, 4.3, .05], color=RED, stroke_width=7, use_smoothing=False)
        self.play(Create(g1_), Create(g2_), run_time=1.2)
        tr = ValueTracker(.3)
        vl = always_redraw(lambda: DashedLine(a1.c2p(tr.get_value(), 24), a2.c2p(tr.get_value(), 0), color=YELLOW, stroke_width=3, dash_length=.1))
        d1 = always_redraw(lambda: Dot(a1.c2p(tr.get_value(), fmp(tr.get_value())), radius=.13, color=ORANGE).set_stroke(WHITE, 3))
        d2 = always_redraw(lambda: Dot(a2.c2p(tr.get_value(), fmc(tr.get_value())), radius=.13, color=RED).set_stroke(WHITE, 3))
        side = card(4.4, 3.8, stroke=PANEL2).move_to(RIGHT*4.8 + DOWN*.6)
        fm = VGroup(T("MC = wage ÷ MP", 32, YELLOW, True), T("MP rises  →  MC falls", 26, GREEN, True), T("MP falls  →  MC rises", 26, RED, True),
                    T("They're mirror images.", 24, TXT)).arrange(DOWN, buff=.4).move_to(side)
        self.say("When each extra worker produces more, the extra output costs less, so marginal cost falls. Once diminishing returns set in and marginal product falls, each extra unit of output costs more. Marginal product's hill becomes marginal cost's valley.")
        self.play(Create(c1), Create(c2), FadeIn(side, shift=LEFT*.3), run_time=1.4)
        self.add(vl, d1, d2)
        self.play(tr.animate.set_value(4.3), run_time=6.5, rate_func=linear)
        self.play(FadeIn(fm, lag_ratio=.3), run_time=1.5)
        self.sync(); self.wait(.8)
        self.fade_all(.7)
