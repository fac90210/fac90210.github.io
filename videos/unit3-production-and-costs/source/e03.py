from lib import *

MP_PTS = [(.5, 15), (1.5, 19), (2.5, 14), (3.5, 12), (4.5, 2), (5.5, -2)]

class E03(Ep):
    chap = 1
    def construct(self):
        ttl = T("Total, Average & Marginal Product", 46, TXT, True).move_to(UP*2.75)
        self.say("Economists track a firm's productivity using three measures. Let's meet them.")
        self.play(Write(ttl), run_time=1); self.sync()
        specs = [("TP", "Total Product", BLUE, "All the output the firm produces", "TP = Q"),
                 ("AP", "Average Product", GREEN, "Output per worker", "AP = TP ÷ L"),
                 ("MP", "Marginal Product", ORANGE, "Extra output from one more worker", "MP = ΔTP ÷ ΔL")]
        cs = VGroup()
        for k, n, c, d, f in specs:
            cd = card(4.0, 4.3, stroke=c)
            kk = T(k, 80, c, True).move_to(cd.get_top() + DOWN*.9)
            nn = T(n, 28, TXT, True).next_to(kk, DOWN, buff=.2)
            dd = T(d, 22, DIM).next_to(nn, DOWN, buff=.2)
            ff = T(f, 32, c, True).next_to(dd, DOWN, buff=.4)
            for t in (nn, dd, ff):
                if t.width > 3.6: t.scale(3.6/t.width)
            cs.add(VGroup(cd, kk, nn, dd, ff))
        cs.arrange(RIGHT, buff=.4).move_to(DOWN*.5)
        lines = ["Total product is simply everything the firm produces.",
                 "Average product is output per worker. Total product divided by the number of workers.",
                 "And marginal product is the star of the show. It's the extra output you get from one more worker. The change in total product, divided by the change in workers."]
        for c, l in zip(cs, lines):
            self.say(l); self.sfx("pop")
            self.play(FadeIn(c, shift=UP*.5), run_time=.9)
        self.sync()
        # pizza example on MP
        et = T("Pizza shop:  3rd worker takes TP from 34 to 48,  so  MP = 48 − 34 = 14", 26, TXT, True).move_to(DOWN*3.1)
        ex = card(et.width + .9, 1.0, stroke=ORANGE).move_to(et)
        self.say("In our pizza shop, the third worker took total product from thirty-four to forty-eight. So that worker's marginal product is fourteen.")
        self.play(cs.animate.shift(UP*.35), FadeIn(ex, shift=UP*.3), Write(et), run_time=1.2)
        self.sync(); self.wait(.4)
        self.fade_all(.6)

        # ---- three stages
        t2 = T("The Three Stages of Returns", 46, TXT, True).move_to(UP*2.75)
        self.say("Now watch what marginal product does as you keep adding workers. It goes through three stages.")
        self.play(Write(t2), run_time=.9); self.sync()
        ax, g = axes_xy((0, 6.2, 1), (-8, 24, 4), 8.0, 4.4, "workers", "MP", xs=[], ys=[0, 10, 20], lsize=24)
        g.move_to(LEFT*2.5 + DOWN*.7)
        zero = ax.c2p(0, 0)
        self.play(Create(g), run_time=1)
        pts = [(0, 0)] + MP_PTS
        def seg(a, b, col):
            sub = [p for p in pts if a <= p[0] <= b]
            return smooth(ax, sub, col)
        f = lambda x: 20 - 3.5*(1.8 - x)**2 if x < 1.8 else 20 - 1.5*(x - 1.8)**2
        def fc(a, b, col):
            m = ax.plot(f, x_range=[a, b, .05], color=col, stroke_width=7, use_smoothing=False)
            return VGroup(m.copy().set_stroke(col, 18, opacity=.22), m)
        s1 = fc(0, 1.8, GREEN); s2 = fc(1.8, 5.45, YELLOW); s3 = fc(5.45, 6.0, RED)
        regions = [
            (0, 1.8, GREEN, "INCREASING", "each worker adds MORE than the last", "workers specialize & use the oven well"),
            (1.8, 5.45, YELLOW, "DIMINISHING", "each worker adds LESS than the last", "output still rises, just slower"),
            (5.45, 6.2, RED, "NEGATIVE", "MP < 0", "workers get in each other's way"),
        ]
        side = VGroup()
        for i, (a, b, c, h, d1, d2) in enumerate(regions):
            band = Rectangle(width=ax.c2p(b, 0)[0] - ax.c2p(a, 0)[0], height=ax.y_length, fill_color=c, fill_opacity=.1, stroke_width=0)
            band.move_to([(ax.c2p(a, 0)[0] + ax.c2p(b, 0)[0])/2, ax.c2p(0, 8)[1], 0])
            regions[i] = regions[i] + (band,)
        texts = ["Stage one. Increasing marginal returns. Each new worker is more productive than the last, because they specialize and make better use of the oven.",
                 "Stage two. Diminishing marginal returns. Now each new worker adds less than the one before. Total product still rises, just more slowly, because there aren't enough ovens to go around.",
                 "Stage three. Negative marginal returns. Marginal product drops below zero. Extra workers get in the way, and total product actually falls."]
        for (a, b, c, h, d1, d2, band), s, tx in zip(regions, (s1, s2, s3), texts):
            lab = T(h, 22, c, True).move_to([band.get_center()[0], ax.c2p(0, 22.6)[1], 0])
            self.say(tx)
            self.sfx("rise")
            self.play(FadeIn(band), Create(s), FadeIn(lab, shift=DOWN*.2), run_time=1.6)
            card_ = VGroup(T(h.capitalize(), 24, c, True), T(d1, 20, TXT), T(d2, 18, DIM)).arrange(DOWN, aligned_edge=LEFT, buff=.12)
            side.add(card_)
        for s_ in side:
            for t in s_:
                if t.width > 3.9: t.scale(3.9/t.width)
        side.arrange(DOWN, aligned_edge=LEFT, buff=.45).move_to(RIGHT*4.6 + DOWN*.5)
        self.play(LaggedStart(*[FadeIn(s_, shift=LEFT*.3) for s_ in side], lag_ratio=.3))
        self.sync(); self.wait(.4)
        self.fade_all(.6)

        # ---- law
        t3 = T("The Law of Diminishing Returns", 46, YELLOW, True).move_to(UP*2.75)
        qt = T("As variable resources are added to fixed resources,\nthe additional output from each new unit will eventually fall.", 30, TXT, True, line_spacing=1.2).move_to(DOWN*.4)
        bx = card(qt.width + 1.0, 2.3, stroke=YELLOW).move_to(qt)
        self.say("This is so important it has a name: the law of diminishing returns.")
        self.sfx("tada"); self.play(Write(t3), run_time=1); self.sync()
        self.say("As you add variable resources, like workers, to a fixed resource, like the oven, the extra output from each new one will eventually fall. Not might. Will.")
        self.play(FadeIn(bx, scale=.9), Write(qt), run_time=2.2)
        ov = oven(.8).move_to(LEFT*4.5 + DOWN*2.7); pp = VGroup(*[person(BLUE, 1.0) for _ in range(7)]).arrange(RIGHT, buff=.1).next_to(ov, RIGHT, buff=.4)
        fx = T("fixed", 22, ORANGE).next_to(ov, DOWN, buff=.1); vx = T("variable", 22, BLUE).next_to(pp, DOWN, buff=.1)
        self.play(GrowFromCenter(ov), FadeIn(fx), LaggedStart(*[GrowFromCenter(p) for p in pp], lag_ratio=.25), FadeIn(vx))
        self.sync(); self.wait(.6)
        self.fade_all(.7)
