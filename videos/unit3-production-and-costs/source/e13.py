from lib import *

class E13(Ep):
    def construct(self):
        t = T("Recap", 60, TXT, True).move_to(UP*2.8)
        self.say("Let's wrap up with everything you need to remember.")
        self.play(Write(t), run_time=.9); self.sync()
        cols = [BLUE, ORANGE, PURPLE]
        data = [("1  Production", ["TP, AP = TP ÷ L, MP = ΔTP ÷ ΔL", "Law of diminishing returns", "MP crosses AP at AP's max"]),
                ("2  Short-run costs", ["TC = FC + VC", "ATC = TC ÷ Q = AFC + AVC", "MC cuts ATC & AVC at their minimums"]),
                ("3  Long-run costs", ["LRATC = lower edge of the SRAC curves", "Economies & diseconomies of scale", "Minimum efficient scale"])]
        cs = VGroup()
        for c, (h, bl) in zip(cols, data):
            cd = card(4.0, 4.6, stroke=c)
            hh = T(h, 28, c, True).move_to(cd.get_top() + DOWN*.6)
            bs = VGroup(*[T(b, 20, TXT) for b in bl])
            for b in bs:
                if b.width > 3.5: b.scale(3.5/b.width)
            bs.arrange(DOWN, aligned_edge=LEFT, buff=.55).move_to(cd.get_center() + DOWN*.35)
            cs.add(VGroup(cd, hh, bs))
        cs.arrange(RIGHT, buff=.35).move_to(DOWN*.4)
        sc = [
         "First, production. Marginal product is the extra output from one more worker. It rises, then falls because of diminishing returns, and it crosses average product at average product's peak.",
         "Second, short-run costs. Total cost is fixed plus variable. Average total cost is total cost over quantity, which is also AFC plus AVC. And marginal cost always cuts through the bottom of ATC and AVC.",
         "Third, long-run costs. The long-run average cost curve is the lower edge of all the short-run curves. It falls with economies of scale, and rises with diseconomies of scale."]
        for c, s in zip(cs, sc):
            self.say(s); self.sfx("pop")
            self.play(FadeIn(c, shift=UP*.5), run_time=.9)
            self.play(LaggedStart(*[Indicate(b, color=YELLOW, scale_factor=1.06) for b in c[2]], lag_ratio=.5), run_time=2.0)
        self.sync(); self.wait(.5)
        self.fade_all(.7)
        # outro
        o1 = T("Nice work.", 96, TXT, True).set_color_by_gradient(BLUE, PURPLE, PINK).move_to(UP*.8)
        o2 = T("Next up: how firms use these costs to decide how much to produce.", 30, DIM).next_to(o1, DOWN, buff=.5)
        o3 = pill("Like  ·  Subscribe  ·  Keep practicing", YELLOW, 28).next_to(o2, DOWN, buff=.6)
        self.say("Nice work. You now understand production, short-run costs, and long-run costs. Practice those problems again until the cost curves feel natural. Next up, we'll see how firms use these costs to decide how much to produce. See you there.")
        self.sfx("tada"); self.play(Write(o1), run_time=1.4)
        self.play(FadeIn(o2, shift=UP*.3), run_time=.8); self.play(FadeIn(o3, shift=UP*.3), run_time=.8)
        self.sync(); self.wait(1.5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.2)
