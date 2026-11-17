"""Choreography for the soccer cutscene: body poses, ball path and slow motion.

Everything here is a pure function of real time t (seconds). The scene script
maps screen time to real time with TimeWarp, so the slow motion needs no extra keys.

Character space: faces +Y, right side is +X, up is +Z. Units are Roblox studs.
"""
import bisect
import math

import numpy as np
from mathutils import Matrix, Vector

FPS = 30
R_BALL = 0.45
GRAVITY = 45.0

T_C = 10.45                 # the volley
ATT_IN = T_C - 0.012        # foot meets ball
ATT_OUT = T_C + 0.030       # ball leaves foot
T_END = 12.25
KICK_SPEED = 72.0

PIVOT = {
    "Torso": Vector((0, 0, 2.0)),
    "Head": Vector((0, 0, 4.0)),
    "Right Arm": Vector((1, 0, 3.5)),
    "Left Arm": Vector((-1, 0, 3.5)),
    "Right Leg": Vector((1, 0, 2.0)),
    "Left Leg": Vector((-1, 0, 2.0)),
}
LEG_BOX = {"Right Leg": ((0, -0.5, 0), (1, 0.5, 2)), "Left Leg": ((-1, -0.5, 0), (0, 0.5, 2))}


def rot(axis, degrees):
    return Matrix.Rotation(math.radians(degrees), 4, axis)


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


class Channels:
    """Named animation channels. Each channel eases between its own keys."""

    def __init__(self):
        self.keys = {}
        self.ready = False

    def K(self, t, **values):
        for name, value in values.items():
            self.keys.setdefault(name, []).append((float(t), float(value)))
        self.ready = False

    def _prepare(self):
        self.times = {}
        for name, items in self.keys.items():
            merged = {}
            for t, v in items:          # a later key at the same time wins
                merged[round(t, 4)] = v
            items[:] = sorted(merged.items())
            self.times[name] = [t for t, _ in items]
        self.ready = True

    def get(self, name, t):
        if not self.ready:
            self._prepare()
        items = self.keys.get(name)
        if not items:
            return 0.0
        times = self.times[name]
        if t <= times[0]:
            return items[0][1]
        if t >= times[-1]:
            return items[-1][1]
        i = bisect.bisect_right(times, t)
        (t0, v0), (t1, v1) = items[i - 1], items[i]
        return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))


def limb_rotation(ch, prefix, side, t):
    g = lambda name: ch.get(prefix + "_" + name, t)
    return rot("Z", g("s")) @ rot("Y", -side * g("o")) @ rot("X", g("f")) @ rot("Z", g("t"))


def part_matrices(ch, t, look_target=None):
    """World matrix for each body part at time t. Limb angles ignore torso lean."""
    yaw = ch.get("yaw", t)
    r_yaw = rot("Z", yaw)
    r_torso = r_yaw @ rot("Y", ch.get("roll", t)) @ rot("X", -ch.get("lean", t))
    base = Matrix.Translation((ch.get("x", t), ch.get("y", t), 0.0))
    piv = PIVOT["Torso"]
    m_torso = base @ Matrix.Translation(piv) @ r_torso @ Matrix.Translation(-piv)
    out = {"Torso": m_torso}

    for name, prefix, side in (("Right Arm", "ra", 1), ("Left Arm", "la", -1),
                               ("Right Leg", "rl", 1), ("Left Leg", "ll", -1)):
        joint = m_torso @ PIVOT[name]
        out[name] = (Matrix.Translation(joint) @ r_yaw @ limb_rotation(ch, prefix, side, t)
                     @ Matrix.Translation(-PIVOT[name]))

    head_yaw, head_up = ch.get("hd_yaw", t), -ch.get("hd_nod", t)
    weight = ch.get("look", t)
    if look_target is not None and weight > 0.001:
        joint = m_torso @ PIVOT["Head"]
        v = r_torso.to_3x3().inverted() @ (Vector(look_target) - joint - Vector((0, 0, 0.5)))
        want_yaw = max(-75.0, min(75.0, math.degrees(math.atan2(-v.x, v.y))))
        want_up = max(-45.0, min(60.0, math.degrees(math.atan2(v.z, math.hypot(v.x, v.y)))))
        head_yaw += (want_yaw - head_yaw) * weight
        head_up += (want_up - head_up) * weight
    out["Head"] = (m_torso @ Matrix.Translation(PIVOT["Head"]) @ rot("Z", head_yaw) @ rot("X", head_up)
                   @ Matrix.Translation(-PIVOT["Head"]))

    # Put the lowest foot corner on the ground, then add the jump height.
    lowest = 1e9
    for name, (lo, hi) in LEG_BOX.items():
        for x in (lo[0], hi[0]):
            for y in (lo[1], hi[1]):
                lowest = min(lowest, (out[name] @ Vector((x, y, lo[2]))).z)
    lift = Matrix.Translation((0, 0, ch.get("h", t) - lowest))
    return {name: lift @ m for name, m in out.items()}


# ---------------------------------------------------------------- choreography
INSTEP = Vector((0.5, 0.5, 0.3))
THIGH = Vector((0.5, 0.5, 1.35))
FRONT = Vector((0, 1, 0))


def build_channels():
    ch = Channels()
    K = ch.K
    K(0.0, x=0, y=0, h=0, yaw=0, lean=2, roll=0, hd_yaw=0, hd_nod=20, look=1,
      ra_f=0, ra_o=6, ra_s=0, la_f=0, la_o=6, la_s=0,
      rl_f=0, rl_o=0, rl_s=0, rl_t=0, ll_f=0, ll_o=0, ll_s=0, ll_t=0)
    touches = []   # (t_in, t_out, part, point, normal, gravity for the flight that follows)

    def leg(side):
        return ("rl", "Right Leg", 1) if side > 0 else ("ll", "Left Leg", -1)

    def hop(t, height, before=0.26, after=0.22):
        K(t - before, h=0)
        K(t - 0.02, h=height)
        K(t + after, h=0)

    def foot_touch(t, side, peak=50, pre=0.24, ret=True, hop_h=0.14, g=GRAVITY):
        p, part, sgn = leg(side)
        K(t - pre, **{p + "_f": 4, p + "_o": 0})
        K(t + 0.07, **{p + "_f": peak + 6})
        if ret:
            K(t + 0.30, **{p + "_f": 4})
        hop(t, hop_h)
        K(t - 0.25, lean=0)
        K(t, lean=-5, roll=-3 * sgn)
        K(t + 0.3, lean=0, roll=0)
        arm_a, arm_b = ("la", "ra") if side > 0 else ("ra", "la")
        K(t - 0.25, **{arm_a + "_f": 0, arm_b + "_f": 0, "ra_o": 14, "la_o": 14})
        K(t, **{arm_a + "_f": 24, arm_b + "_f": -18, "ra_o": 22, "la_o": 22})
        K(t + 0.3, **{arm_a + "_f": 0, arm_b + "_f": 0, "ra_o": 14, "la_o": 14})
        touches.append((t, t, part, Vector((sgn * 0.5, 0.5, 0.3)), FRONT, g))

    def thigh_touch(t, side, g=GRAVITY):
        p, part, sgn = leg(side)
        K(t - 0.24, **{p + "_f": 8, p + "_o": 0})
        K(t + 0.06, **{p + "_f": 94})
        K(t + 0.30, **{p + "_f": 6})
        hop(t, 0.10)
        K(t - 0.25, lean=0)
        K(t, lean=-9)
        K(t + 0.3, lean=0)
        K(t - 0.25, ra_o=16, la_o=16)
        K(t, ra_o=34, la_o=34)
        K(t + 0.3, ra_o=16, la_o=16)
        touches.append((t, t, part, Vector((sgn * 0.5, 0.5, 1.35)), FRONT, g))

    def head_touch(t, g=GRAVITY):
        hop(t, 0.55, before=0.28, after=0.28)
        K(t - 0.30, look=1)
        K(t - 0.12, look=0, hd_nod=-10, hd_yaw=0)
        K(t + 0.12, look=0, hd_nod=-10)
        K(t + 0.30, look=1)
        K(t - 0.28, ra_o=14, la_o=14, lean=0)
        K(t, ra_o=40, la_o=40, lean=-6)
        K(t + 0.28, ra_o=14, la_o=14, lean=0)
        touches.append((t, t, "Head", Vector((0, 0.12, 5.1)), Vector((0, 0, 1)), g))

    # --- 1. look at the ball, then scoop it up with the right foot
    K(0.55, lean=4, ra_o=9, la_o=9)
    K(1.05, lean=2, rl_f=0, ra_f=0, la_f=0)
    K(1.32, rl_f=-28, lean=9, ra_f=26, la_f=-20)
    K(1.66, rl_f=56, lean=-4, ra_f=-22, la_f=24)
    K(1.95, rl_f=4, lean=0, ra_f=0, la_f=0)
    hop(1.62, 0.12)
    touches.append((1.50, 1.60, "Right Leg", Vector((0.5, 0.5, 0.15)), FRONT, GRAVITY))

    # --- 2. kick-ups: feet, thighs, head
    foot_touch(2.22, 1)
    foot_touch(2.80, -1)
    thigh_touch(3.38, 1)
    thigh_touch(3.93, -1)
    head_touch(4.50)
    head_touch(5.10)

    # --- 3. freestyle: around the world, crossover, spin
    foot_touch(5.85, 1, peak=52, ret=False, g=30.0)
    K(6.03, rl_f=34, rl_o=42)
    K(6.17, rl_f=78, rl_o=34)
    K(6.29, rl_f=86, rl_o=-18)
    K(6.40, rl_f=38, rl_o=-16)
    K(6.20, h=0.4)
    K(6.46, h=0)
    foot_touch(6.60, 1, pre=0.16)
    K(6.60, x=0.0)
    K(6.88, x=0.35)
    foot_touch(7.15, -1)
    K(7.42, x=0.0)
    foot_touch(7.70, 1, peak=60)
    # 360 spin under the high ball
    K(7.72, look=1)
    K(7.82, look=0, hd_nod=0, hd_yaw=0)
    K(7.76, yaw=0)
    K(8.60, yaw=360)
    K(7.74, h=0)
    K(8.15, h=1.0)
    K(8.56, h=0)
    K(7.95, ra_f=45, la_f=45, ra_o=4, la_o=4)
    K(8.35, ra_f=45, la_f=45, ra_o=4, la_o=4)
    K(8.60, ra_f=0, la_f=0, ra_o=38, la_o=38)
    K(8.52, look=0)
    K(8.66, look=1)
    thigh_touch(8.75, 1)
    foot_touch(9.30, 1, peak=62, ret=False)

    # --- 4. the volley
    K(9.62, rl_f=0, lean=-8, ra_o=26, la_o=26, ra_f=0, la_f=0, yaw=360)
    K(10.03, lean=14, ra_f=-38, la_f=-38, ra_o=18, la_o=18, yaw=335, roll=0,
      rl_o=0, rl_s=0, rl_f=0, ll_f=0, ll_o=0)
    K(10.05, h=0)
    K(10.45, h=1.7)
    K(10.86, h=0)
    K(10.30, roll=-35, yaw=330, lean=0, rl_o=70, rl_s=-75, rl_f=0, ll_f=-10, ll_o=5,
      ra_o=60, ra_f=-30, la_o=50, la_f=40)
    K(10.58, roll=-62, yaw=405, rl_o=88, rl_s=50, ll_f=-35, ll_o=10,
      ra_o=95, ra_f=-50, la_o=70, la_f=20)
    K(10.92, roll=0, yaw=420, lean=22, rl_o=10, rl_s=0, rl_f=36, ll_f=-30, ll_o=0,
      ra_o=50, ra_f=-20, la_o=35, la_f=30)
    K(11.50, yaw=380, lean=6, rl_f=10, ll_f=-8, rl_o=4, ra_o=18, la_o=18, ra_f=0, la_f=0)
    K(12.00, yaw=375, lean=0, rl_f=0, ll_f=0, rl_o=0, ra_o=150, la_o=10)
    touches.append((ATT_IN, ATT_OUT, "Right Leg", INSTEP.copy(), FRONT, 6.0))
    return ch, touches


class Motion:
    def __init__(self):
        self.ch, self.touches = build_channels()
        first = self._anchor(0, self.touches[0][0])
        self.rest = Vector((first.x, first.y, R_BALL))
        self.rest_until = self.touches[0][0] - 0.05
        out_m = part_matrices(self.ch, ATT_OUT)["Right Leg"]
        self.kick_dir = (out_m.to_3x3() @ FRONT).normalized()
        self.kick_vel = self.kick_dir * KICK_SPEED + Vector((0, 0, 4.0))
        self.contact_point = self._anchor(len(self.touches) - 1, ATT_IN)
        self.release_point = self._anchor(len(self.touches) - 1, ATT_OUT)

    def _anchor(self, index, t):
        _, _, part, point, normal, _ = self.touches[index]
        m = part_matrices(self.ch, t)[part]
        return m @ point + (m.to_3x3() @ normal).normalized() * R_BALL

    def ball(self, t):
        """Ball center at real time t."""
        touches = self.touches
        if t <= self.rest_until:
            return self.rest.copy()
        if t < touches[0][0]:
            u = smooth((t - self.rest_until) / (touches[0][0] - self.rest_until))
            return self.rest.lerp(self._anchor(0, touches[0][0]), u)
        last = len(touches) - 1
        if t >= touches[last][1]:
            tau = t - touches[last][1]
            p = self.release_point + self.kick_vel * tau
            p.z -= 0.5 * touches[last][5] * tau * tau
            return p
        for i, (t_in, t_out, *_rest) in enumerate(touches):
            if t_in <= t <= t_out:
                return self._anchor(i, t)
            if t < t_in:
                a_out, g = touches[i - 1][1], touches[i - 1][5]
                p0, p1 = self._anchor(i - 1, a_out), self._anchor(i, t_in)
                span = t_in - a_out
                tau = t - a_out
                p = p0.lerp(p1, tau / span)
                p.z += 0.5 * g * tau * (span - tau)
                return p
        return self.release_point.copy()

    def pose(self, t):
        return part_matrices(self.ch, t, look_target=self.ball(t))

    def squash(self, t):
        """1 = round ball. Less than 1 while the foot presses into it."""
        if ATT_IN <= t <= ATT_OUT:
            u = (t - ATT_IN) / (ATT_OUT - ATT_IN)
            return 1.0 - 0.34 * math.sin(math.pi * u) ** 0.8
        if t > ATT_OUT:  # wobble after release
            tau = t - ATT_OUT
            return 1.0 + 0.16 * math.exp(-tau * 22.0) * math.sin(tau * 130.0)
        return 1.0


class TimeWarp:
    """Screen time s <-> real time t. Real time almost stops around the volley."""

    def __init__(self, v_min=0.045):
        dt = 1e-4
        t = np.arange(0.0, T_END + dt, dt)
        down = np.clip((t - (T_C - 0.20)) / ((ATT_IN - 0.004) - (T_C - 0.20)), 0, 1)
        up = np.clip((t - (ATT_OUT + 0.004)) / ((T_C + 0.30) - (ATT_OUT + 0.004)), 0, 1)
        w = down * down * (3 - 2 * down) * (1 - up * up * (3 - 2 * up))
        speed = 1.0 - (1.0 - v_min) * w
        self.t = t
        self.s = np.concatenate([[0.0], np.cumsum(dt / speed[:-1])])
        self.total = float(self.s[-1])

    def t_of_s(self, s):
        return float(np.interp(s, self.s, self.t))

    def s_of_t(self, t):
        return float(np.interp(t, self.t, self.s))
