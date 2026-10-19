from lib import *

class E08(Ep):
    chap = 2
    def construct(self):
        TC = [40, 65, 85, 100, 120, 150, 190]
        pl = pill("PRACTICE #2", YELLOW, 24).move_to(UP*3.0 + LEFT*5.3)
        intro = T("The Apple Farm", 40, TXT, True).move_to(UP*2.85 + LEFT*1.0)
        tb = Tbl(["Bushels", "TC ($)"], [[str(i), str(TC[i])] for i in range(7)], cw=[1.7, 1.7], rh=.58, fs=27, hcolors=[DIM, BLUE])
        tb.move_to(LEFT*5.0 + DOWN*.55)
        panel = card(9.3, 5.2, stroke=PANEL2).move_to(RIGHT*2.1 + DOWN*.55)
        qs = [("a.  What is the farm's fixed cost?", "At 0 bushels, TC is all fixed:  FC = 40", "$40", 0, [(0, 1)]),
              ("b.  Marginal cost of the 2nd bushel?", "MC = ΔTC ÷ ΔQ = (85 − 65) ÷ 1", "$20", 1, [(1, 1), (2, 1)]),
              ("c.  Variable cost at 3 bushels?", "VC = TC − FC = 100 − 40", "$60", 2, [(3, 1)]),
              ("d.  Average total cost at 4 bushels?", "ATC = TC ÷ Q = 120 ÷ 4", "$30", 3, [(4, 1)]),
              ("e.  Average fixed cost at 5 bushels?", "AFC = FC ÷ Q = 40 ÷ 5", "$8", 4, [(5, 1)]),
              ("f.  Average variable cost at 6 bushels?", "AVC = (190 − 40) ÷ 6 = 150 ÷ 6", "$25", 5, [(6, 1)])]
        rows = VGroup()
        for q, w, a, i, hl in qs:
            qt = T(q, 25, TXT, True); wt = T(w, 22, ORANGE).next_to(qt, DOWN, aligned_edge=LEFT, buff=.1)
            at = pill(a, GREEN, 28, .3, .12)
            row = VGroup(qt, wt); row.wt = wt; row.ans = at; rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=.2).move_to(panel.get_center() + LEFT*.4)
        for r in rows:
            r.ans.move_to([panel.get_right()[0] - 1.1, r[0].get_center()[1] - .1, 0]); r.wt.set_opacity(0)

        self.say("Practice problem number two. A small farm grows apples, and we've got its total cost at each level of output. Let's answer six questions.")
        self.sfx("whoosh")
        self.play(FadeIn(pl, shift=RIGHT*.3), FadeIn(tb, shift=UP*.3), FadeIn(panel, shift=LEFT*.3), run_time=1)
        self.play(LaggedStart(*[FadeIn(r[0], shift=RIGHT*.2) for r in rows], lag_ratio=.15), run_time=1.4); self.sync()
        self.say("Pause the video and try them all. Then we'll go through them together.")
        pz = T("PAUSE & TRY IT", 26, YELLOW, True).move_to(RIGHT*3.2 + UP*2.95)
        self.play(FadeIn(pz)); self.countdown(10, pos=RIGHT*6.1 + UP*2.95)
        self.sfx("ding"); self.play(FadeOut(pz), run_time=.3)

        narr = ["Part a. Fixed costs are what you pay even when you produce nothing. At zero bushels, total cost is forty. So fixed cost is forty dollars.",
                "Part b. Marginal cost is the extra cost of one more unit. Going from one bushel to two, total cost rises from sixty-five to eighty-five. That's twenty dollars.",
                "Part c. Variable cost is total cost minus fixed cost. At three bushels, a hundred minus forty gives sixty dollars.",
                "Part d. Average total cost is total cost divided by quantity. A hundred twenty divided by four is thirty dollars.",
                "Part e. Average fixed cost is fixed cost over quantity. Forty divided by five is eight dollars.",
                "Part f. Average variable cost is variable cost over quantity. At six bushels, variable cost is a hundred fifty. Divide by six, and you get twenty-five dollars."]
        for (q, w, a, i, hl), n in zip(qs, narr):
            r = rows[i]
            boxes = VGroup(*[tb.hl(*h, YELLOW) for h in hl])
            self.say(n)
            self.play(Create(boxes), r[0].animate.set_color(YELLOW), run_time=.5)
            self.play(r.wt.animate.set_opacity(1), run_time=.6)
            self.sfx("pop"); self.play(FadeIn(r.ans, scale=1.5), run_time=.5)
            self.play(FadeOut(boxes), r[0].animate.set_color(TXT), run_time=.3)
        self.sync(); self.wait(.4)
        self.say("Nice. Now let's fill in every column for this farm, because we're about to graph it.")
        self.fade_all(.6)

        # ---- full table
        H = ["Q", "TC", "FC", "VC", "MC", "AFC", "AVC", "ATC"]
        cols = [DIM, BLUE, TEAL, YELLOW, RED, TEAL, YELLOW, PURPLE]
        data = [["0", "40", "40", "0", "–", "–", "–", "–"],
                ["1", "65", "40", "25", "25", "40", "25", "65"],
                ["2", "85", "40", "45", "20", "20", "22.5", "42.5"],
                ["3", "100", "40", "60", "15", "13.3", "20", "33.3"],
                ["4", "120", "40", "80", "20", "10", "20", "30"],
                ["5", "150", "40", "110", "30", "8", "22", "30"],
                ["6", "190", "40", "150", "40", "6.7", "25", "31.7"]]
        hide = {(r, c) for r in range(7) for c in range(2, 8)}
        full = Tbl(H, data, cw=[1.0, 1.5, 1.5, 1.5, 1.5, 1.6, 1.6, 1.6], rh=.6, fs=27, hcolors=cols, hide=hide).move_to(DOWN*.5)
        t2 = T("The Full Cost Table", 44, TXT, True).move_to(UP*2.75)
        self.play(Write(t2), FadeIn(full, shift=UP*.3), run_time=1.2)
        steps = [(2, "Fixed cost never changes. Forty, every row."),
                 (3, "Variable cost is total cost minus forty."),
                 (4, "Marginal cost is the change in total cost each step. Look at that: it falls to fifteen, then climbs back up."),
                 (5, "Average fixed cost shrinks every row, because the same forty dollars is spread across more bushels."),
                 (6, "Average variable cost, variable cost over quantity."),
                 (7, "And average total cost, total cost over quantity. Notice it falls, then starts rising again.")]
        for c, n in steps:
            self.say(n)
            cells = [full.reveal(r, c, cols[c]) for r in range(7) if (r, c) in hide]
            self.sfx("pop")
            self.play(LaggedStart(*[FadeIn(x, scale=1.5) for x in cells], lag_ratio=.12), run_time=1.2)
        self.sync()
        self.say("Keep an eye on those last four columns. Next, we'll graph them.")
        self.sync(); self.wait(.4)
        self.fade_all(.7)
