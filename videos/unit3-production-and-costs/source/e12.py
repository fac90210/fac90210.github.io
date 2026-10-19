from lib import *

AVC = lambda q: 6 + .5*(q - 3.5)**2
ATC = lambda q: AVC(q) + 20.0/q
MC  = lambda q: 6 + .5*(q - 3.5)**2 + q*(q - 3.5)

class E12(Ep):
    chap = 3
    def construct(self):
        TP = [0, 6, 14, 24, 32, 39, 42]
        MP = ["–", "6", "8", "10", "8", "7", "3"]
        pl = pill("EXAM-STYLE PROBLEM", PINK, 22).move_to(UP*3.0 + LEFT*4.6)
        tb = Tbl(["Labor", "Total Product", "MP"], [[str(i), str(TP[i]), MP[i]] for i in range(7)], cw=[1.3, 2.0, 1.2], rh=.56, fs=26,
                 hcolors=[DIM, BLUE, ORANGE], hide={(i, 2) for i in range(1, 7)})
        tb.move_to(LEFT*4.6 + DOWN*.45)
        panel = card(8.2, 5.4, stroke=PANEL2).move_to(RIGHT*2.8 + DOWN*.45)
        intro = T("A widget firm uses one fixed input (capital)\nand one variable input (labor).", 24, TXT, line_spacing=1.2).move_to(UP*2.55 + RIGHT*2.7)
        self.say("Let's put it all together with an exam-style free response question. A firm makes widgets using one fixed input, capital, and one variable input, labor. Here's its production table. There are four parts.")
        self.sfx("whoosh"); self.play(FadeIn(pl, shift=RIGHT*.3), FadeIn(tb, shift=UP*.3), FadeIn(panel, shift=LEFT*.3), run_time=1)
        self.sync()
        qa = VGroup(T("(a)  Calculate the marginal product of the 6th worker. Show your work.", 23, TXT, True),
                    T("(b)  Does the production function show diminishing returns? Explain.", 23, TXT, True),
                    T("(c)  When marginal product is falling, what happens to marginal cost?", 23, TXT, True),
                    T("(d)  Graph the firm's ATC, AVC, and MC curves.", 23, TXT, True)).arrange(DOWN, aligned_edge=LEFT, buff=.45).move_to(panel)
        sc_ = min(1, 7.8/max(q.width for q in qa))
        for q in qa: q.scale(sc_)
        qa.arrange(DOWN, aligned_edge=LEFT, buff=.45).move_to(panel)
        self.play(LaggedStart(*[FadeIn(q, shift=RIGHT*.3) for q in qa], lag_ratio=.3), run_time=2)
        self.say("Pause the video, and try writing your own answers.")
        pz = T("PAUSE & TRY IT", 24, YELLOW, True).move_to(RIGHT*3.7 + UP*3.0)
        self.play(FadeIn(pz)); self.countdown(10, pos=RIGHT*6.2 + UP*3.0); self.play(FadeOut(pz), run_time=.3)
        self.sfx("ding")
        self.play(FadeOut(qa), run_time=.4)

        def part(letter, head, lines, narr, colors=None):
            hh = pill(f"PART {letter}", YELLOW, 22).move_to(panel.get_top() + DOWN*.5 + LEFT*3.2)
            ts = VGroup(*[T(l, 27, (colors[i] if colors else TXT), True) for i, l in enumerate(lines)]).arrange(DOWN, aligned_edge=LEFT, buff=.35)
            for x in ts:
                if x.width > 7.6: x.scale(7.6/x.width)
            ts.arrange(DOWN, aligned_edge=LEFT, buff=.35).move_to(panel.get_center() + DOWN*.2)
            ts.align_to(panel, LEFT).shift(RIGHT*.5)
            return hh, ts
        # part a
        hh, ts = part("A", "", ["MP of 6th worker", "= TP(6) − TP(5)", "= 42 − 39", "= 3"], None, [DIM, TXT, TXT, ORANGE])
        self.say("Part a. Marginal product of the sixth worker is the change in total product. Forty-two minus thirty-nine. That's three.")
        self.play(FadeIn(hh)); hA = VGroup(tb.hl(6, 1, YELLOW), tb.hl(5, 1, YELLOW)); self.play(Create(hA))
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT*.2) for x in ts], lag_ratio=.4), run_time=2.0)
        self.sfx("pop"); self.play(Indicate(ts[-1], color=ORANGE, scale_factor=1.3)); self.sync()
        self.play(FadeOut(ts), FadeOut(hh), FadeOut(hA), run_time=.3)
        # part b
        hh, ts = part("B", "", ["MP: 6, 8, 10, 8, 7, 3", "MP rises through worker 3,", "then falls from worker 4 on.", "Yes: diminishing returns begin with the 4th worker."],
                      None, [ORANGE, TXT, TXT, GREEN])
        self.say("Part b. Let's fill in marginal product for every worker. It rises: six, eight, ten. Then it falls: eight, seven, three. So yes, the production function shows diminishing returns, starting with the fourth worker, because that's where marginal product begins to fall.")
        self.play(FadeIn(hh))
        self.play(LaggedStart(*[FadeIn(tb.reveal(i, 2, ORANGE), scale=1.5) for i in range(1, 7)], lag_ratio=.25), run_time=2.0)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT*.2) for x in ts], lag_ratio=.5), run_time=2.5)
        self.play(Create(tb.hl(4, 2, GREEN))); self.sync()
        self.play(FadeOut(ts), FadeOut(hh), run_time=.3)
        # part c
        hh, ts = part("C", "", ["When MP falls, MC rises.", "Each extra worker costs the same wage,", "but adds less output,", "so each extra unit of output costs more."],
                      None, [RED, TXT, TXT, TXT])
        self.say("Part c. When marginal product is falling, marginal cost is rising. Each extra worker still costs the same wage, but adds less output, so each extra unit gets more expensive to produce.")
        self.play(FadeIn(hh)); self.play(LaggedStart(*[FadeIn(x, shift=RIGHT*.2) for x in ts], lag_ratio=.45), run_time=2.5); self.sync()
        self.play(FadeOut(ts), FadeOut(hh), run_time=.3)
        # part d
        self.say("And part d. Draw a correctly labeled graph with ATC, AVC, and MC. This is where most points are won or lost, so let's draw it step by step.")
        self.sync()
        self.fade_all(.6)
        ax, g = axes_xy((0, 7, 1), (0, 30, 10), 8.0, 4.6, "quantity", "cost ($)", xs=[], ys=[], lsize=24)
        place(ax, g, -6.3, -3.0)
        qq = np.arange(.05, 1, 1)
        def pl_(f, a, b, col):
            m = ax.plot(f, x_range=[a, b, .05], color=col, stroke_width=7, use_smoothing=False)
            return VGroup(m.copy().set_stroke(col, 18, opacity=.22), m)
        cA = pl_(ATC, 1.3, 6.4, PURPLE); cV = pl_(AVC, .6, 6.4, YELLOW); cM = pl_(MC, .55, 5.9, RED)
        lA = T("ATC", 26, PURPLE, True).next_to(ax.c2p(6.4, ATC(6.4)), RIGHT, buff=.15)
        lV = T("AVC", 26, YELLOW, True).next_to(ax.c2p(6.4, AVC(6.4)), RIGHT, buff=.15).shift(DOWN*.25)
        lM = T("MC", 26, RED, True).next_to(ax.c2p(5.9, MC(5.9)), RIGHT, buff=.15)
        tq = np.arange(1.5, 6.4, .01); qa_ = float(tq[np.argmin([ATC(x) for x in tq])])
        self.play(Create(g), run_time=1)
        self.say("First, label both axes: quantity on the horizontal, cost in dollars on the vertical. Next, draw ATC: a U shape.")
        self.play(Create(cA), FadeIn(lA), run_time=1.5)
        self.say("Then AVC, also U-shaped, and always below ATC. The gap between them is average fixed cost.")
        self.play(Create(cV), FadeIn(lV), run_time=1.5)
        self.say("Finally MC. It falls, then rises, and it must cross both ATC and AVC at their lowest points.")
        self.play(Create(cM), FadeIn(lM), run_time=1.5)
        p1 = Dot(ax.c2p(3.5, AVC(3.5)), radius=.13, color=WHITE); p2 = Dot(ax.c2p(qa_, ATC(qa_)), radius=.13, color=WHITE)
        self.sfx("pop"); self.play(FadeIn(p1, scale=2), FadeIn(p2, scale=2), Indicate(p1, color=YELLOW), Indicate(p2, color=YELLOW)); self.sync()
        ck = card(4.6, 3.8, stroke=GREEN).move_to(RIGHT*4.7 + UP*.2)
        items = ["Both axes labeled", "Every curve labeled", "ATC & AVC U-shaped", "AVC below ATC", "MC through both minimums"]
        cks = VGroup(T("EARNS THE POINTS", 22, GREEN, True), *[T("✓  " + s, 22, TXT, True) for s in items]).arrange(DOWN, aligned_edge=LEFT, buff=.28).move_to(ck)
        self.say("Here's your checklist for full credit: both axes labeled, every curve labeled, ATC and AVC U-shaped with AVC below ATC, and marginal cost passing through the minimum of each.")
        self.play(FadeIn(ck, shift=LEFT*.3))
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT*.2) for x in cks], lag_ratio=.7), run_time=3.5)
        self.sync(); self.wait(.8)
        self.fade_all(.7)
