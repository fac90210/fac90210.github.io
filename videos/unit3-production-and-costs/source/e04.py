from lib import *

class E04(Ep):
    chap = 1
    def construct(self):
        TPv = [0, 15, 34, 48, 60, 62, 60]
        MPv = [None, 15, 19, 14, 12, 2, -2]
        APv = [None, "15", "17", "16", "15", "12.4", "10"]
        pl = pill("PRACTICE #1", YELLOW, 24).move_to(UP*2.75 + LEFT*5.3)
        tb = Tbl(["Labor", "Total Product", "Marginal Product", "Average Product"],
                 [[str(i), str(TPv[i]), "–" if i == 0 else str(MPv[i]), "–" if i == 0 else APv[i]] for i in range(7)],
                 cw=[1.3, 1.9, 2.2, 2.1], rh=.62, fs=28, hcolors=[DIM, BLUE, ORANGE, GREEN],
                 hide={(i, c) for i in range(1, 7) for c in (2, 3)})
        tb.move_to(LEFT*3.1 + DOWN*.55)
        self.say("Time for practice. Here's a short-run production table for a firm, with the labor and total product filled in.")
        self.sfx("whoosh"); self.play(FadeIn(pl, shift=RIGHT*.3), FadeIn(tb, shift=UP*.4), run_time=1.1); self.sync()

        panel = card(5.6, 4.9, stroke=PANEL2).move_to(RIGHT*4.0 + DOWN*.55)
        fm = VGroup(T("Marginal Product", 26, ORANGE, True), T("MP = ΔTP ÷ ΔL", 34, TXT, True),
                    T("Average Product", 26, GREEN, True), T("AP = TP ÷ L", 34, TXT, True)).arrange(DOWN, buff=.3)
        fm[1].shift(DOWN*0); fm.move_to(panel.get_center() + UP*.2)
        self.say("Your job is to fill in the marginal product and average product columns. Here are the formulas. Pause the video, and give it a shot.")
        self.play(FadeIn(panel, shift=LEFT*.3), LaggedStart(*[Write(m) for m in fm], lag_ratio=.3), run_time=1.6)
        self.sync()
        pz = T("PAUSE & TRY IT", 30, YELLOW, True).move_to(panel.get_bottom() + UP*.5 + RIGHT*1.0)
        self.play(FadeIn(pz))
        self.countdown(8, pos=panel.get_bottom() + UP*.5 + LEFT*1.6)
        self.sfx("ding"); self.play(FadeOut(pz), FadeOut(fm))

        def work(lines, colors):
            g = VGroup(*[T(l, 28, c, True) for l, c in zip(lines, colors)]).arrange(DOWN, aligned_edge=LEFT, buff=.35)
            return g.move_to(panel.get_center() + UP*.1)
        narr = {1: "Worker one. Marginal product is the change in total product, fifteen minus zero, over one worker. That's fifteen. Average product is fifteen over one, also fifteen.",
                2: "Worker two. Total product goes from fifteen to thirty-four, so marginal product is nineteen. Average product is thirty-four divided by two, which is seventeen.",
                3: "Worker three. Forty-eight minus thirty-four is fourteen. Average product, forty-eight over three, is sixteen.",
                4: "Worker four. Sixty minus forty-eight is twelve. And sixty over four is fifteen.",
                5: "Worker five. Sixty-two minus sixty is only two. And average product is sixty-two over five, which is twelve point four.",
                6: "Worker six. Total product falls from sixty-two to sixty, so marginal product is negative two. Average product is sixty divided by six, ten."}
        cur = None
        for n in range(1, 7):
            mp, ap = MPv[n], APv[n]
            prev = TPv[n-1]
            w = work([f"Worker {n}", f"MP = ({TPv[n]} − {prev}) ÷ 1 = {mp}", f"AP = {TPv[n]} ÷ {n} = {ap}"], [DIM, ORANGE, GREEN])
            h = tb.hl(n, 1, YELLOW)
            self.say(narr[n])
            anims = [FadeIn(w, shift=UP*.2), Create(h)]
            if cur is not None: anims.append(FadeOut(cur))
            self.play(*anims, run_time=.6)
            self.sfx("pop")
            a = tb.reveal(n, 2, RED if mp < 0 else ORANGE); b = tb.reveal(n, 3, GREEN)
            self.play(FadeIn(a, scale=1.6), run_time=.5)
            self.play(FadeIn(b, scale=1.6), run_time=.5)
            self.play(FadeOut(h), run_time=.3)
            cur = w
            if n in (1, 2): self.wait(.2)
        self.sync()
        self.play(FadeOut(cur))
        # takeaways
        h2 = tb.hl(2, 2, ORANGE)
        box_mp = SurroundingRectangle(VGroup(tb.rects[(2, 2)]), color=ORANGE, buff=0, stroke_width=6)
        tk = VGroup(T("What the table tells us", 28, YELLOW, True),
                    T("• MP peaks at worker 2 (19)", 26, ORANGE, True),
                    T("• Diminishing returns begin with worker 3", 26, TXT),
                    T("• At worker 6, MP < 0 so TP falls", 26, RED, True)).arrange(DOWN, aligned_edge=LEFT, buff=.28)
        [t.scale(5.0/t.width) for t in tk if t.width > 5.0]
        tk.arrange(DOWN, aligned_edge=LEFT, buff=.28).move_to(panel.get_center())
        self.say("So what did we learn? Marginal product peaks at worker two, at nineteen. Diminishing returns kick in with worker three, when marginal product starts to fall. And by worker six, marginal product is negative, so total product actually drops.")
        self.play(Create(box_mp), FadeIn(tk[0]))
        self.play(FadeIn(tk[1], shift=RIGHT*.3), run_time=.7)
        self.play(FadeIn(tk[2], shift=RIGHT*.3), Transform(box_mp, SurroundingRectangle(VGroup(tb.rects[(3, 2)]), color=YELLOW, buff=0, stroke_width=6)), run_time=.9)
        self.play(FadeIn(tk[3], shift=RIGHT*.3), Transform(box_mp, SurroundingRectangle(VGroup(tb.rects[(6, 2)]), color=RED, buff=0, stroke_width=6)), run_time=.9)
        self.sync(); self.wait(.5)
        self.fade_all(.7)
