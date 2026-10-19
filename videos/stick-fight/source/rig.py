import math
import numpy as np

GY = -2.3                      # ground y
LEG, ARM, TORSO, HEAD_R = .65, .5, .85, .3
FPS = 24.0
WEAPONS = {"katana": dict(L=1.95, s_main=.40, s_off=.12), "spear": dict(L=3.4, s_main=1.0, s_off=1.9)}
CUT_S = 2.6                     # spear snaps this far from the butt

def ease(u, kind):
    u = min(1, max(0, u))
    if kind == "lin": return u
    if kind == "in": return u**2.0          # accelerate through the move (reference dive)
    if kind == "out": return 1-(1-u)**3
    if kind == "snap": return 1-(1-u)**4.5   # near-instant pop (reference flip launch)
    if kind == "over":
        c1 = 1.6; c3 = c1+1; return 1 + c3*(u-1)**3 + c1*(u-1)**2
    return u*u*(3-2*u)

DEF = dict(px=0, h=1.2, air=0, lean=6, head=0, walk=0, amp=.5, ffx=.6, ffl=0, bfx=-.55, bfl=0, gx=.7, gy=-.2, w=30)
def build_keys(raw):
    keys, cur = [], dict(DEF)
    for t, kind, kw in raw:
        cur = dict(cur); cur.update(kw); keys.append((t, kind, cur))
    return keys
def pose_at(keys, t):
    if t <= keys[0][0]: return dict(keys[0][2])
    for i in range(len(keys)-1):
        t0, _, a = keys[i]; t1, k1, b = keys[i+1]
        if t0 <= t < t1:
            u = ease((t - t0)/(t1 - t0), k1)
            return {k: a[k] + (b[k] - a[k])*u for k in a}
    return dict(keys[-1][2])

def two_bone(root, target, l1, l2, bend):
    d = target - root; L = np.linalg.norm(d)
    if L < 1e-6: d = np.array([0., -1.]); L = 1e-6
    u = d/np.linalg.norm(d); L = min(L, l1 + l2 - 1e-3)
    a = (l1*l1 - l2*l2 + L*L)/(2*L); hh = math.sqrt(max(0, l1*l1 - a*a))
    perp = np.array([-u[1], u[0]])
    return root + u*a + perp*hh*bend, root + u*L

def state(p, face, weapon):
    f = face
    pel = np.array([p["px"], GY + p["h"] + p["air"]])
    lean = math.radians(p["lean"]); lh = lean + math.radians(p["head"])
    top = pel + np.array([math.sin(lean)*f, math.cos(lean)])*TORSO
    head = top + np.array([math.sin(lh)*f, math.cos(lh)])*(HEAD_R + .12)
    # gait
    wk = p["walk"]
    ph = p["px"]*f*2.3
    fx = p["ffx"]*(1-wk) + wk*p["amp"]*math.sin(ph)
    bx = p["bfx"]*(1-wk) + wk*p["amp"]*math.sin(ph + math.pi)
    fl = p["ffl"] + wk*.3*max(0, math.cos(ph))*min(1, p["amp"]/.45)
    bl = p["bfl"] + wk*.3*max(0, math.cos(ph + math.pi))*min(1, p["amp"]/.45)
    ff = np.array([p["px"] + f*fx, GY + fl]); bf = np.array([p["px"] + f*bx, GY + bl])
    kf, ff = two_bone(pel, ff, LEG, LEG, f); kb, bf = two_bone(pel, bf, LEG, LEG, f)
    # weapon
    wd = WEAPONS[weapon]
    wa = math.radians(p["w"] if f == 1 else 180 - p["w"]); d = np.array([math.cos(wa), math.sin(wa)])
    A = top + np.array([f*p["gx"], p["gy"]])
    v = A - top; n = np.linalg.norm(v)
    if n > .95: A = top + v/n*.95
    sB = wd["s_off"] - wd["s_main"]
    B = A + d*sB
    if np.linalg.norm(B - top) > .97:           # slide second hand along the weapon so both stay connected
        best = None
        for s in np.linspace(0, sB, 30):
            C = A + d*s
            if np.linalg.norm(C - top) <= .97: best = C
        B = best if best is not None else A
    butt = A - d*wd["s_main"]; tip = butt + d*wd["L"]
    ea, A2 = two_bone(top, A, ARM, ARM, -f); eb, B2 = two_bone(top, B, ARM, ARM, -f)
    return dict(pel=pel, top=top, head=head, ff=ff, bf=bf, kf=kf, kb=kb, A=A2, B=B2, ea=ea, eb=eb, butt=butt, tip=tip, d=d, f=f)

# ------------------------------------------------------------------ choreography (seconds, 24 fps on ones)
K_RAW = [
 (0.00, "s",    dict(px=-7.6, h=1.2, lean=8, walk=1, amp=.5, gx=.45, gy=-.55, w=-45)),
 (2.30, "lin",  dict(px=-3.9)),
 (2.75, "out",  dict(px=-3.7, walk=0, ffx=.6, bfx=-.5, h=1.12, lean=8, gx=.72, gy=-.18, w=30)),
 (3.00, "s",    dict()),
 (3.14, "out",  dict(px=-3.5, h=1.05, lean=14, gx=.85, gy=-.1, w=12, ffx=.8)),
 (3.30, "snap", dict(px=-3.2, h=1.05, lean=14, gx=1.0, gy=-.45, w=-41)),
 (3.62, "s",    dict(px=-3.4, h=1.12, lean=6, gx=.8, gy=-.4, w=-45)),
 (3.95, "out",  dict(px=-3.3, h=1.08, lean=2, gx=.35, gy=.45, w=125, ffx=.7)),
 (4.10, "in",   dict(px=-3.3, h=1.0, lean=-2, gx=.25, gy=.6, w=140, ffx=.7)),
 (4.30, "snap", dict(px=-1.7, h=.95, lean=28, gx=.95, gy=0.0, w=25, ffx=1.25, bfx=-.7)),
 (4.75, "s",    dict(px=-2.1, h=1.12, lean=8, gx=.8, gy=-.2, w=30, ffx=.65, bfx=-.55)),
 (5.35, "s",    dict(px=-2.3, h=1.1, lean=10, gx=.8, gy=-.25, w=20)),
 (5.60, "out",  dict(px=-2.3, h=.85, lean=14, gx=.5, gy=-.1, w=70, ffx=.35, bfx=-.35)),
 (5.85, "snap", dict(px=-1.9, h=1.15, air=1.3, lean=10, gx=.3, gy=.4, w=135, ffx=.5, ffl=.9+1.3, bfx=-.5, bfl=.5+1.3)),
 (6.35, "lin",  dict(px=-1.4, h=1.15, air=1.45, lean=18, gx=.3, gy=.45, w=135, ffl=1.1+1.45, bfl=.9+1.45)),
 (6.50, "snap", dict(px=-1.0, h=1.15, air=.85, lean=34, gx=.8, gy=-.7, w=-122, ffx=.8, ffl=1.2, bfx=-.6, bfl=1.0)),
 (6.95, "out",  dict(px=.0, h=1.1, air=0, lean=14, gx=.9, gy=-.2, w=-10, ffx=.9, ffl=0, bfx=-.7, bfl=0)),
 (7.55, "s",    dict(px=.1, h=1.12, lean=8, gx=.8, gy=-.2, w=30, ffx=.7, bfx=-.6)),
 (8.05, "s",    dict(px=.1, h=1.1, lean=8, gx=.8, gy=-.2, w=35)),
 (8.24, "out",  dict(px=-.5, h=1.1, lean=-20, gx=.5, gy=-.1, w=55, ffx=.4, bfx=-.8)),
 (8.40, "snap", dict(px=.35, h=1.0, lean=24, gx=.95, gy=-.15, w=-5, ffx=1.25, bfx=-.75)),
 (8.85, "s",    dict(px=.45, h=1.05, lean=26, gx=1.0, gy=-.15, w=-2)),
 (9.50, "s",    dict(px=1.15, h=1.15, lean=8, gx=.7, gy=-.3, w=-30, ffx=.6, bfx=-.55)),
 (9.95, "snap", dict(px=1.1, h=1.2, lean=4, gx=.9, gy=.1, w=40)),
 (11.0, "out",  dict(px=1.0, h=1.2, lean=0, gx=.5, gy=-.6, w=-60, ffx=.4, bfx=-.4)),
 (12.4, "s",    dict(px=-.2, walk=1, amp=.5, h=1.2, lean=2, gx=.5, gy=-.6, w=-70)),
 (15.0, "lin",  dict(px=-3.5)),
]
S_RAW = [
 (0.00, "s",    dict(px=3.9, h=1.15, lean=8, ffx=.6, bfx=-.55, gx=.4, gy=-.4, w=8)),
 (2.85, "s",    dict()),
 (3.00, "out",  dict(px=4.1, h=.98, lean=14, gx=-.2, gy=-.45, w=5, ffx=.5, bfx=-.6)),
 (3.22, "in",   dict(px=1.9, h=1.02, lean=30, gx=.85, gy=-.3, w=2, ffx=1.1, bfx=-.7)),
 (3.55, "over", dict(px=2.1, h=1.05, lean=38, gx=.8, gy=-.55, w=-22, ffx=1.0, bfx=-.7)),
 (3.90, "s",    dict(px=2.8, h=1.12, lean=16, gx=.3, gy=.05, w=-5, ffx=.7, bfx=-.6)),
 (4.12, "out",  dict(px=3.0, h=1.05, lean=8, gx=.5, gy=.45, w=0, ffx=.6, bfx=-.55)),
 (4.45, "snap", dict(px=3.0, h=1.0, lean=-4, gx=.5, gy=.5, w=-3, ffx=.45, bfx=-.7)),
 (4.85, "s",    dict(px=3.9, h=1.12, lean=12, gx=.3, gy=-.2, w=8, ffx=.7, bfx=-.6)),
 (5.35, "s",    dict(px=3.3, h=1.05, lean=14, gx=.3, gy=-.35, w=6)),
 (5.55, "out",  dict(px=3.3, h=.82, lean=18, gx=-.3, gy=-.75, w=-6, ffx=.8, bfx=-.2)),
 (5.85, "snap", dict(px=1.9, h=.78, lean=22, gx=.9, gy=-.8, w=-3, ffx=1.2, bfx=-.2)),
 (6.45, "s",    dict(px=1.9, h=.82, lean=22, gx=.9, gy=-.8, w=-3)),
 (6.95, "out",  dict(px=3.0, h=1.1, lean=10, gx=.4, gy=-.1, w=8, ffx=.6, bfx=-.6)),
 (7.90, "s",    dict(px=3.1, h=1.12, lean=10, gx=.35, gy=-.2, w=8)),
 (8.08, "out",  dict(px=3.3, h=1.0, lean=14, gx=-.2, gy=-.2, w=6, ffx=.5, bfx=-.6)),
 (8.32, "snap", dict(px=2.9, h=1.0, lean=26, gx=.75, gy=-.15, w=4, ffx=1.1)),
 (8.52, "over", dict(px=2.95, h=1.02, lean=10, gx=.6, gy=-.1, w=10, ffx=1.0)),
 (8.85, "out",  dict(px=3.4, h=1.0, lean=-26, gx=-.1, gy=.3, w=70, ffx=.3, bfx=-.9, ffl=.15)),
 (9.40, "out",  dict(px=3.8, h=.8, lean=-48, gx=-.3, gy=-.2, w=140, ffx=.2, bfx=-1.0)),
 (10.2, "in",   dict(px=4.5, h=.3, lean=-84, gx=-.6, gy=-.5, w=175, ffx=.1, bfx=-1.1, ffl=0, bfl=0)),
 (15.0, "s",    dict()),
]
KK, SK = build_keys(K_RAW), build_keys(S_RAW)
T_CUT = 6.50
IMPACT_T = 8.50          # final slash lands (single burst, as in the reference)
CLASHES = [(3.30, "k", .83), (4.30, "k", .88), (T_CUT, "k", 1.0)]   # (time, who, s along blade)
TOTAL = 14.6

def pose_k(t): return pose_at(KK, t)
def pose_s(t): return pose_at(SK, t)
def st_k(t): return state(pose_k(t), 1, "katana")
def st_s(t): return state(pose_s(t), -1, "spear")

def piece_traj():
    s0 = st_s(T_CUT); butt, d = s0["butt"], s0["d"]; p0 = butt + d*CUT_S
    s1 = st_s(T_CUT + .04); v = (s1["butt"] + s1["d"]*CUT_S - p0)/.04
    L = 3.4 - CUT_S; ang = math.atan2(d[1], d[0]); c = p0 + d*L/2
    vel = np.array(v) + np.array([-1.5, 3.4]); om = 6.0; out = []; dt = 1/240
    for i in range(int(5/dt)):
        vel = vel + np.array([0, -15.])*dt; c = c + vel*dt; ang += om*dt
        low = min(c[1] + math.sin(ang)*L/2, c[1] - math.sin(ang)*L/2)
        if low < GY:
            c[1] += GY - low; vel = np.array([vel[0]*.6, -vel[1]*.3]); om *= .4
            if abs(vel[1]) < .8: vel[1] = 0; om *= .5
        out.append((c.copy(), ang))
    return out, L
TRAJ, PL = piece_traj()

def cam(t):
    k, s = st_k(t), st_s(t)
    mx = (k["pel"][0] + s["pel"][0])/2
    zoom = 1.0 - .05*min(1, t/10) + (.1*math.exp(-((t - 8.6)/.5)**2))
    cx = mx*.75
    return cx, .45, zoom
