from lib import *

class E01(Ep):
    def construct(self):
        tp = [0, 15, 34, 48, 60, 62, 60]
        floor = card(7.6, 5.4).move_to(LEFT*3.2 + DOWN*.2)
        ov = oven(1.25).move_to(floor.get_center() + UP*1.2)
        ovl = T("1 oven (fixed)", 26, ORANGE).next_to(ov, DOWN, buff=.2)
        ctr = card(4.4, 5.4).move_to(RIGHT*4.4 + DOWN*.2)
        cl = T("PIZZAS PER HOUR", 26, DIM, True).move_to(ctr.get_top() + DOWN*.55)
        cnt = T("0", 150, TXT, True).move_to(ctr.get_center() + UP*.1)
        wl = T("WORKERS: 0", 28, BLUE, True).move_to(ctr.get_bottom() + UP*.6)

        self.say("You run a pizza shop. You've got one oven, and business is booming. So you start hiring.")
        self.play(FadeIn(floor, shift=UP*.3), FadeIn(ctr, shift=UP*.3), run_time=.8)
        self.sfx("whoosh")
        self.play(GrowFromCenter(ov), FadeIn(ovl), Write(cl), FadeIn(cnt), FadeIn(wl), run_time=1)
        self.sync()

        lines = ["Worker number one makes fifteen pizzas an hour. Nice.",
                 "Worker two? Nineteen more! They split up the jobs and get faster. Teamwork!",
                 "Worker three adds fourteen. Still good, but not quite as good.",
                 "Worker four, twelve more.",
                 "Worker five adds just two more pizzas. Hmm.",
                 "And worker six? Pizzas per hour actually go down. They're just getting in the way."]
        ppl = VGroup()
        slots = [floor.get_center() + np.array([-2.75 + 1.1*i, -1.3, 0]) for i in range(6)]
        prev = 0
        for n in range(1, 7):
            col = BLUE if n < 6 else RED
            p = person(col, 1.7).move_to(slots[n-1])
            ppl.add(p)
            d = tp[n] - tp[n-1]
            self.say(lines[n-1])
            newc = T(str(tp[n]), 150, RED if d < 0 else TXT, True).move_to(cnt)
            delta = T(f"{d:+d}", 54, GREEN if d > 0 else RED, True).next_to(cnt, UP, buff=.05).shift(RIGHT*1.25)
            neww = T(f"WORKERS: {n}", 28, BLUE, True).move_to(wl)
            self.sfx("pop" if d > 0 else "buzz")
            self.play(GrowFromCenter(p), Transform(cnt, newc), Transform(wl, neww),
                      FadeIn(delta, shift=UP*.4), run_time=.9)
            self.play(delta.animate.shift(UP*.5).set_opacity(0), run_time=.7)
            self.remove(delta)
            if n == 6:
                self.play(Indicate(cnt, color=RED, scale_factor=1.15), p.animate.shift(UP*.2), run_time=.8)
        self.sync()
        self.say("So hiring more and more eventually backfires. When does it happen, why, and what does it do to your costs? That's what this video is about.")
        self.sync()
        self.sfx("whoosh")
        self.fade_all(.7)

        # ---- title card
        t1 = T("PRODUCTION", 110, TXT, True).set_color_by_gradient(BLUE, PURPLE)
        t2 = T("& COSTS", 110, TXT, True).set_color_by_gradient(PURPLE, PINK)
        tt = VGroup(t1, t2).arrange(DOWN, buff=.15).move_to(UP*.7)
        sub = pill("AP MICROECONOMICS  ·  UNIT 3.1 – 3.3", YELLOW, 28).next_to(tt, DOWN, buff=.55)
        self.sfx("rise")
        self.play(LaggedStart(Write(t1), Write(t2), lag_ratio=.4), run_time=1.6)
        self.play(FadeIn(sub, shift=UP*.3), run_time=.6)
        self.say("Here's the plan. First, production: how output responds to workers. Second, short-run costs, where those famous U-shaped curves come from. And third, long-run costs, and why a bigger firm can be cheaper, or clumsier. We'll practice real problems the whole way, so grab a pencil.")
        self.wait(2.2)
        self.play(tt.animate.scale(.45).to_edge(UP, buff=.5), FadeOut(sub), run_time=.8)
        cols = [BLUE, ORANGE, PURPLE]
        names = [("1", "Production", "Inputs, output & diminishing returns"),
                 ("2", "Short-run costs", "Fixed, variable, average & marginal"),
                 ("3", "Long-run costs", "Economies of scale & the LRATC")]
        cs = VGroup()
        for c, (n, a, b) in zip(cols, names):
            cd = card(3.7, 3.6, stroke=c)
            num = T(n, 90, c, True).move_to(cd.get_top() + DOWN*1.0)
            h = T(a, 32, TXT, True).next_to(num, DOWN, buff=.3)
            s = T(b, 24, DIM).next_to(h, DOWN, buff=.25)
            if s.width > 3.4: s.scale(3.4/s.width)
            cs.add(VGroup(cd, num, h, s))
        cs.arrange(RIGHT, buff=.45).move_to(DOWN*.7)
        self.sfx("whoosh")
        self.play(LaggedStart(*[FadeIn(c, shift=UP*.6) for c in cs], lag_ratio=.35), run_time=1.6)
        self.sync(); self.wait(.6)
        self.fade_all(.7)
