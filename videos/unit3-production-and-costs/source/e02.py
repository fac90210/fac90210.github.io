from lib import *

def flow_dots(a, b, color, n=3, speed=.45):
    ds = VGroup()
    for i in range(n):
        d = Dot(radius=.07, color=color)
        d.ph = i / n
        d.add_updater(lambda m, a=a, b=b, sp=speed: m.move_to(a + (b - a) * ((m.ph + self_time()*sp) % 1)))
        ds.add(d)
    return ds
_T = [0.0]
def self_time(): return _T[0]

def padlock(s=1.0, color=RED):
    body = RoundedRectangle(width=.5*s, height=.4*s, corner_radius=.06*s, fill_color=color, fill_opacity=1, stroke_width=0)
    sh = Arc(radius=.16*s, start_angle=0, angle=PI, stroke_color=color, stroke_width=5*s).next_to(body, UP, buff=-.02)
    return VGroup(sh, body)

class E02(Ep):
    chap = 1
    def setup(self):
        super().setup()
        self.add_updater(lambda dt: _T.__setitem__(0, self.renderer.time))
    def construct(self):
        ttl = T("The Vocabulary", 46, TXT, True).move_to(UP*2.75)
        self.say("Before any math, let's lock in some vocabulary.")
        self.play(Write(ttl), run_time=.9); self.sync()

        xs = [-5.25, -1.75, 1.75, 5.25]
        specs = [("INPUTS", BLUE, "land · labor · capital", "tomatoes, flour, ovens, cooks"),
                 ("THE FIRM", PURPLE, "turns inputs into goods", "the pizza parlor"),
                 ("OUTPUT", GREEN, "finished goods & services", "pizzas"),
                 ("REVENUE", YELLOW, "Price × Quantity", "money from sales")]
        nodes = []
        for x, (h, c, d, e) in zip(xs, specs):
            cd = card(2.85, 2.6, stroke=c)
            hh = T(h, 32, c, True).move_to(cd.get_top() + DOWN*.5)
            dd = T(d, 21, TXT).next_to(hh, DOWN, buff=.3)
            ee = T(e, 20, DIM).next_to(dd, DOWN, buff=.25)
            for t in (dd, ee):
                if t.width > 2.6: t.scale(2.6/t.width)
            g = VGroup(cd, hh, dd, ee).move_to([x, .4, 0]); nodes.append(g)
        arrows = [Arrow(nodes[i].get_right(), nodes[i+1].get_left(), buff=.08, color=DIM, stroke_width=5,
                        max_tip_length_to_length_ratio=.4) for i in range(3)]

        self.say("A firm takes inputs: resources like land, labor, and capital. For a pizza parlor, that's tomatoes, flour, ovens, and cooks.")
        self.sfx("pop"); self.play(FadeIn(nodes[0], shift=RIGHT*.4)); self.sync()
        self.say("It pays money to get those inputs, and that money is called cost. Want workers? You've got to pay wages.")
        cost = pill("COSTS = money spent on inputs", RED, 24).move_to([-3.4, -1.7, 0])
        self.sfx("pop"); self.play(FadeIn(cost, shift=UP*.3)); self.sync()
        self.say("The firm then turns those inputs into output: the finished goods and services it produces.")
        self.sfx("whoosh")
        self.play(GrowArrow(arrows[0]), FadeIn(nodes[1], shift=RIGHT*.4), GrowArrow(arrows[1]), FadeIn(nodes[2], shift=RIGHT*.4))
        fl = [flow_dots(nodes[i].get_right(), nodes[i+1].get_left(), c) for i, c in zip(range(3), (BLUE, PURPLE, GREEN))]
        self.add(*fl)
        self.sync()
        self.say("And when it sells that output, it earns revenue. Revenue is simply price times quantity.")
        self.sfx("pop")
        self.play(GrowArrow(arrows[2]), FadeIn(nodes[3], shift=RIGHT*.4)); self.sync()

        eq = T("Toy company:  $10 × 100 dolls  =  $1,000 revenue", 30, TXT, True).move_to(DOWN*3.0)
        ex = card(eq.width + .9, 1.2, stroke=YELLOW).move_to(eq)
        eq[22:].set_color(YELLOW) if False else None
        self.say("Sell a hundred dolls at ten dollars each, and your revenue is one thousand dollars.")
        self.play(FadeIn(ex, shift=UP*.3), Write(eq), run_time=1.4); self.sync(); self.wait(.5)

        self.fade_all(.6); self.remove(*fl)
        # ---- short run vs long run
        t2 = T("Short Run  vs  Long Run", 46, TXT, True).move_to(UP*2.75)
        self.say("Now, one distinction that matters for everything in this unit. The short run, versus the long run.")
        self.play(Write(t2), run_time=.9); self.sync()
        L = card(6.4, 4.7, stroke=ORANGE).move_to(LEFT*3.6 + DOWN*.6)
        R = card(6.4, 4.7, stroke=TEAL).move_to(RIGHT*3.6 + DOWN*.6)
        lh = T("SHORT RUN", 34, ORANGE, True).move_to(L.get_top() + DOWN*.5)
        rh = T("LONG RUN", 34, TEAL, True).move_to(R.get_top() + DOWN*.5)
        ls = T("At least ONE input is fixed", 26, TXT).next_to(lh, DOWN, buff=.2)
        rs = T("ALL inputs can be changed", 26, TXT).next_to(rh, DOWN, buff=.2)
        ov1 = oven(.9).move_to(L.get_center() + LEFT*1.6 + DOWN*.35)
        lock = padlock(1.1).move_to(ov1.get_top() + UP*.1 + RIGHT*.8)
        wk = VGroup(*[person(BLUE, 1.2) for _ in range(3)]).arrange(RIGHT, buff=.15).next_to(ov1, RIGHT, buff=.7)
        capL = T("oven is locked in\nworkers can change", 22, DIM).move_to(L.get_bottom() + UP*.7)

        self.say("In the short run, at least one input is fixed. You can hire more workers, or order more dough tomorrow, but you can't build a bigger kitchen overnight.")
        self.sfx("whoosh"); self.play(FadeIn(L, shift=RIGHT*.4), Write(lh), FadeIn(ls)); 
        self.play(GrowFromCenter(ov1), LaggedStart(*[GrowFromCenter(p) for p in wk], lag_ratio=.3))
        self.sfx("pop"); self.play(FadeIn(lock, scale=2), FadeIn(capL))
        extra = person(BLUE, 1.2).next_to(wk, RIGHT, buff=.15)
        self.play(FadeIn(extra, scale=.3)); self.sync()
        self.say("In the long run, every input can change. Bigger kitchen, more ovens, a whole new location. Nothing is locked in. And notice, the long run isn't a number of months. It's just a period long enough for the firm to change everything.")
        self.sfx("whoosh"); self.play(FadeIn(R, shift=LEFT*.4), Write(rh), FadeIn(rs))
        base = R.get_center() + DOWN*.3
        o_a = oven(.7).move_to(base + LEFT*2.0)
        self.play(GrowFromCenter(o_a))
        o_b = oven(1.0).move_to(base + LEFT*.2); o_c = oven(1.3).move_to(base + RIGHT*2.0)
        self.sfx("rise")
        self.play(ReplacementTransform(o_a.copy(), o_b), ReplacementTransform(o_a.copy(), o_c), run_time=1.2)
        capR = T("everything is flexible", 22, DIM).move_to(R.get_bottom() + UP*.7)
        self.play(FadeIn(capR)); self.sync(); self.wait(.8)
        self.fade_all(.7)
