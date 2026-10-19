from lib import *

class E07(Ep):
    chap = 2
    def construct(self):
        # ---------------- explicit vs implicit
        t = T("What Counts as a Cost?", 46, TXT, True).move_to(UP*2.75)
        self.say("Welcome to chapter two: costs. First, a quick question. What actually counts as a cost?")
        self.play(Write(t), run_time=.9); self.sync()
        ex = Rectangle(width=2.2, height=3.0, fill_color=RED, fill_opacity=.9, stroke_width=0)
        im = Rectangle(width=2.2, height=.9, fill_color=ORANGE, fill_opacity=.25, stroke_color=ORANGE, stroke_width=4)
        a = VGroup(ex.copy())
        bar1 = Rectangle(width=2.8, height=3.0, fill_color=RED, fill_opacity=.9, stroke_width=0).move_to(LEFT*4.7 + DOWN*1.3)
        bar2a = Rectangle(width=2.8, height=3.0, fill_color=RED, fill_opacity=.9, stroke_width=0).move_to(LEFT*0.9 + DOWN*1.3)
        bar2b = Rectangle(width=2.8, height=.9, fill_color=ORANGE, fill_opacity=.3, stroke_color=ORANGE, stroke_width=4).next_to(bar2a, UP, buff=0)
        l1 = T("Accounting cost", 28, RED, True).next_to(bar1, DOWN, buff=.3)
        l2 = T("Economic cost", 28, ORANGE, True).next_to(bar2a, DOWN, buff=.3)
        e_lab = T("Explicit\n$500,000", 26, TXT, True).move_to(bar1)
        e_lab2 = T("Explicit\n$500,000", 26, TXT, True).move_to(bar2a)
        i_lab = T("Implicit $60,000", 22, ORANGE, True).move_to(bar2b)
        side = card(5.2, 4.3, stroke=PANEL2).move_to(RIGHT*4.3 + DOWN*1.0)
        sd = VGroup(T("Explicit costs", 26, RED, True), T("out-of-pocket payments\n(ink, machines, wages)", 22, TXT),
                    T("Implicit costs", 26, ORANGE, True), T("opportunity cost of what you\ngive up (your old salary)", 22, TXT)).arrange(DOWN, aligned_edge=LEFT, buff=.2)
        sd[2].shift(DOWN*.2); sd.move_to(side)
        self.say("Say a graphic designer quits a sixty thousand dollar job to start a T-shirt business. The bills she pays out of pocket, for ink, machines, and so on, are explicit costs. Say those come to five hundred thousand dollars. Accountants only count those.")
        self.play(GrowFromEdge(bar1, DOWN), FadeIn(e_lab), FadeIn(l1), FadeIn(side, shift=LEFT*.3), FadeIn(sd[:2]), run_time=1.5); self.sync()
        self.say("But economists also count implicit costs: the opportunity cost of what you gave up. That sixty thousand dollar salary is a real cost of running the shop. Explicit plus implicit gives you the economic cost: five hundred sixty thousand dollars.")
        self.play(GrowFromEdge(bar2a, DOWN), FadeIn(e_lab2), FadeIn(l2), run_time=.8)
        self.sfx("pop"); self.play(GrowFromEdge(bar2b, DOWN), FadeIn(i_lab), FadeIn(sd[2:]), run_time=1.2)
        tot = T("= $560,000", 30, YELLOW, True).next_to(bar2b, UP, buff=.25)
        self.play(FadeIn(tot, scale=1.4)); self.sync(); self.wait(.5)
        self.fade_all(.6)

        # ---------------- fixed vs variable
        FC = 40; VC = [0, 25, 45, 60, 80, 110, 150]
        t = T("Fixed, Variable & Total Cost", 46, TXT, True).move_to(UP*2.75)
        self.say("Now let's split costs into two groups, using a small apple farm as our example.")
        self.play(Write(t), run_time=.9); self.sync()
        sc = 3.5/190; x0 = -6.0; base = -3.0
        bars = VGroup(); qlabs = VGroup()
        axl = Line([x0 - .5, base, 0], [x0 + 7*1.05 + .2, base, 0], color=DIM, stroke_width=3)
        fcs, vcs = [], []
        for q in range(7):
            x = x0 + q*1.05 + .4
            f = Rectangle(width=.75, height=FC*sc, fill_color=TEAL, fill_opacity=.95, stroke_width=0).move_to([x, base + FC*sc/2, 0])
            fcs.append(f)
            if VC[q]:
                v = Rectangle(width=.75, height=VC[q]*sc, fill_color=YELLOW, fill_opacity=.95, stroke_width=0).move_to([x, base + FC*sc + VC[q]*sc/2, 0])
                vcs.append(v)
            qlabs.add(T(str(q), 22, DIM).move_to([x, base - .3, 0]))
        xl = T("quantity of output (bushels)", 22, DIM).move_to([x0 + 3.5, base - .75, 0])
        key = VGroup(VGroup(Square(.25, fill_color=TEAL, fill_opacity=1, stroke_width=0), T("Fixed cost (FC)", 24, TEAL, True)).arrange(RIGHT, buff=.2),
                     VGroup(Square(.25, fill_color=YELLOW, fill_opacity=1, stroke_width=0), T("Variable cost (VC)", 24, YELLOW, True)).arrange(RIGHT, buff=.2)).arrange(DOWN, aligned_edge=LEFT, buff=.25).move_to(RIGHT*4.7 + UP*1.5)
        self.say("Fixed costs don't change with output. Rent, insurance, salaries. Even if the farm grows zero apples, they're still due. Here, fixed cost is forty dollars at every level of output.")
        self.play(Create(axl), FadeIn(qlabs), FadeIn(xl), FadeIn(key[0], shift=LEFT*.3), run_time=.8)
        self.play(LaggedStart(*[GrowFromEdge(f, DOWN) for f in fcs], lag_ratio=.12), run_time=1.6); self.sync()
        self.say("Variable costs change with output. Electricity, hourly wages, shipping. The more you produce, the higher they get.")
        self.play(FadeIn(key[1], shift=LEFT*.3))
        self.sfx("rise")
        self.play(LaggedStart(*[GrowFromEdge(v, DOWN) for v in vcs], lag_ratio=.25), run_time=3.0); self.sync()
        tcb = Brace(VGroup(fcs[6], vcs[-1]), RIGHT, color=BLUE)
        tcl = T("TC = $190", 28, BLUE, True).next_to(tcb, RIGHT, buff=.2)
        eqc = card(5.2, 1.3, stroke=BLUE).move_to(RIGHT*4.7 + DOWN*.1)
        eqt = T("TC = FC + VC", 40, BLUE, True).move_to(eqc)
        self.say("Add them together and you get total cost. Total cost equals fixed cost plus variable cost. At six bushels, that's forty plus a hundred fifty, or one ninety.")
        self.play(GrowFromCenter(tcb), FadeIn(tcl), FadeIn(eqc, shift=LEFT*.3), Write(eqt), run_time=1.5)
        self.sync(); self.wait(.5)
        self.fade_all(.6)

        # ---------------- per-unit formulas
        t = T("Four More Costs to Know", 46, TXT, True).move_to(UP*2.75)
        self.say("Finally, four per-unit measures. You'll use these constantly.")
        self.play(Write(t), run_time=.9); self.sync()
        specs = [("AFC", "Average Fixed Cost", "FC ÷ Q", TEAL),
                 ("AVC", "Average Variable Cost", "VC ÷ Q", YELLOW),
                 ("ATC", "Average Total Cost", "TC ÷ Q   or   AFC + AVC", PURPLE),
                 ("MC", "Marginal Cost", "ΔTC ÷ ΔQ", RED)]
        cs = []
        for k, n, f, c in specs:
            cd = card(5.9, 2.0, stroke=c)
            kk = T(k, 48, c, True).move_to(cd.get_left() + RIGHT*1.1)
            nn = T(n, 24, TXT, True).move_to(cd.get_center() + RIGHT*.9 + UP*.4)
            ff = T(f, 30, c, True).move_to(cd.get_center() + RIGHT*.9 + DOWN*.35)
            for tt in (nn, ff):
                if tt.width > 3.5: tt.scale(3.5/tt.width)
            cs.append(VGroup(cd, kk, nn, ff))
        grid = VGroup(*cs).arrange_in_grid(2, 2, buff=.4).move_to(DOWN*.4)
        lines = ["Average fixed cost is fixed cost divided by quantity. It shrinks as you produce more, because you're spreading the same bill over more units.",
                 "Average variable cost is variable cost divided by quantity.",
                 "Average total cost is total cost divided by quantity, which is also just AFC plus AVC.",
                 "And marginal cost: the extra cost of producing one more unit. The change in total cost, divided by the change in quantity."]
        for c, l in zip(cs, lines):
            self.say(l); self.sfx("pop"); self.play(FadeIn(c, shift=UP*.4), run_time=.8)
        self.sync(); self.wait(.5)
        self.fade_all(.7)
