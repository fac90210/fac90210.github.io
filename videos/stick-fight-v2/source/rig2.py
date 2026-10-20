import math
import numpy as np

GY = -2.3                      # ground y
S_FIG = 3.35
THIGH, SHIN, TORSO, NECK, HEAD_R = .211*S_FIG, .22*S_FIG, .193*S_FIG, .045*S_FIG, .085*S_FIG
UARM, FARM = .143*S_FIG, .224*S_FIG
STROKE = .073*S_FIG
FPS = 24.0
WEAPONS = {"katana": dict(L=2.05, s_main=.42, s_off=.12), "spear": dict(L=3.6, s_main=1.05, s_off=2.0)}
CUT_S = 2.15                     # spear snaps this far from the butt

def ease(u, kind):
    u = min(1, max(0, u))
    if kind == "lin": return u
    if kind == "in": return u**2.0          # accelerate through the move (reference dive)
    if kind == "out": return 1-(1-u)**3
    if kind == "snap": return 1-(1-u)**4.5   # near-instant pop (reference flip launch)
    if kind == "over":
        c1 = 1.6; c3 = c1+1; return 1 + c3*(u-1)**3 + c1*(u-1)**2
    return u*u*(3-2*u)

DEF = dict(px=0, h=1.31, air=0, lean=6, head=0, walk=0, amp=.5, ffx=.6, ffl=0, bfx=-.55, bfl=0, gx=.7, gy=-.2, w=30)
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
    head = top + np.array([math.sin(lh)*f, math.cos(lh)])*(HEAD_R + NECK)
    wk = p["walk"]; ph = p["px"]*f*2.3
    fx = p["ffx"]*(1-wk) + wk*p["amp"]*math.sin(ph); bx = p["bfx"]*(1-wk) + wk*p["amp"]*math.sin(ph + math.pi)
    fl = p["ffl"] + wk*.3*max(0, math.cos(ph))*min(1, p["amp"]/.45); bl = p["bfl"] + wk*.3*max(0, math.cos(ph + math.pi))*min(1, p["amp"]/.45)
    ff = np.array([p["px"] + f*fx, GY + fl]); bf = np.array([p["px"] + f*bx, GY + bl])
    kf, ff = two_bone(pel, ff, THIGH, SHIN, f); kb, bf = two_bone(pel, bf, THIGH, SHIN, f)
    wd = WEAPONS[weapon]
    wa = math.radians(p["w"] if f == 1 else 180 - p["w"]); d = np.array([math.cos(wa), math.sin(wa)])
    A = top + np.array([f*p["gx"], p["gy"]]); v = A - top; n = np.linalg.norm(v); reach = (UARM + FARM)*.97
    if n > reach: A = top + v/n*reach
    sB = wd["s_off"] - wd["s_main"]; B = A + d*sB
    if np.linalg.norm(B - top) > reach:
        best = None
        for sx in np.linspace(0, sB, 30):
            C = A + d*sx
            if np.linalg.norm(C - top) <= reach: best = C
        B = best if best is not None else A
    butt = A - d*wd["s_main"]; tip = butt + d*wd["L"]
    ea, A2 = two_bone(top, A, UARM, FARM, -f); eb, B2 = two_bone(top, B, UARM, FARM, -f)
    return dict(pel=pel, top=top, head=head, ff=ff, bf=bf, kf=kf, kb=kb, A=A2, B=B2, ea=ea, eb=eb, butt=butt, tip=tip, d=d, f=f)

# ------------------------------------------------------------------ choreography (seconds, 24 fps on ones)
K_RAW = [
 (0.00, "s",    dict(px=-7.6, h=1.308, lean=8, walk=1, amp=.5, gx=0.531, gy=-0.649, w=-45)),
 (2.30, "lin",  dict(px=-3.9)),
 (2.75, "out",  dict(px=-3.7, walk=0, ffx=0.654, bfx=-0.545, h=1.221, lean=8, gx=0.850, gy=-0.212, w=30)),
 (3.00, "s",    dict()),
 (3.14, "out",  dict(px=-3.5, h=1.145, lean=14, gx=1.003, gy=-0.118, w=12, ffx=0.872)),
 (3.30, "snap", dict(px=-3.2, h=1.145, lean=14, gx=1.080, gy=-0.531, w=-32)),
 (3.62, "s",    dict(px=-3.4, h=1.221, lean=6, gx=0.944, gy=-0.472, w=-45)),
 (3.95, "out",  dict(px=-3.3, h=1.177, lean=2, gx=0.413, gy=0.531, w=125, ffx=0.763)),
 (4.10, "in",   dict(px=-3.3, h=1.090, lean=-2, gx=0.295, gy=0.708, w=140, ffx=0.763)),
 (4.30, "snap", dict(px=-1.7, h=1.036, lean=28, gx=1.121, gy=0.000, w=31, ffx=1.363, bfx=-0.763)),
 (4.75, "s",    dict(px=-2.1, h=1.221, lean=8, gx=0.944, gy=-0.236, w=30, ffx=0.709, bfx=-0.600)),
 (5.35, "s",    dict(px=-2.3, h=1.199, lean=10, gx=0.944, gy=-0.295, w=20)),
 (5.60, "out",  dict(px=-2.3, h=0.926, lean=14, gx=0.590, gy=-0.118, w=70, ffx=0.382, bfx=-0.382)),
 (5.85, "snap", dict(px=-1.9, h=1.254, air=1.417, lean=10, gx=0.354, gy=0.472, w=135, ffx=0.545, ffl=2.398, bfx=-0.545, bfl=1.962)),
 (6.35, "lin",  dict(px=-1.4, h=1.254, air=1.581, lean=18, gx=0.354, gy=0.531, w=135, ffl=2.780, bfl=2.562)),
 (6.50, "snap", dict(px=-1.0, h=1.254, air=0.926, lean=34, gx=0.840, gy=-0.730, w=-101, ffx=0.872, ffl=1.308, bfx=-0.654, bfl=1.090)),
 (6.95, "out",  dict(px=.0, h=1.2, air=0, lean=14, gx=1.06, gy=-.236, w=-10, ffx=.98, ffl=0, bfx=-.76, bfl=0)),
 (7.55, "s",    dict(px=.1, h=1.22, lean=8, gx=.94, gy=-.24, w=30, ffx=.76, bfx=-.65)),
 (7.90, "out",  dict(px=.1, h=1.0, lean=8, gx=.8, gy=-.1, w=60, ffx=.7, bfx=-.6)),
 (8.15, "snap", dict(px=-1.6, h=1.22, air=1.0, lean=-8, gx=.7, gy=.1, w=45, ffx=.5, ffl=1.7, bfx=-.5, bfl=1.4)),
 (8.50, "out",  dict(px=-3.7, h=1.1, air=0, lean=6, gx=.9, gy=-.2, w=35, ffx=.9, ffl=0, bfx=-.7, bfl=0)),
 (8.80, "s",    dict(px=-3.8, h=1.15, lean=10, gx=.75, gy=-.25, w=30, ffx=.7, bfx=-.6)),
 (9.00, "in",   dict(px=-3.6, walk=1, amp=.95, h=1.12, lean=30, gx=.45, gy=-.62, w=165)),
 (10.00, "lin", dict(px=-.5, walk=1, amp=.95, h=1.12, lean=34, gx=.45, gy=-.62, w=165)),
 (10.12, "snap",dict(px=.2, walk=0, h=1.02, lean=26, gx=1.2, gy=-.18, w=-4, ffx=1.4, bfx=-.85)),
 (10.60, "s",    dict(px=.25, h=1.06, lean=26, gx=1.25, gy=-.18, w=-2)),
 (11.30, "s",    dict(px=.45, h=1.25, lean=8, gx=.8, gy=-.35, w=-30, ffx=.65, bfx=-.6)),
 (11.65, "snap", dict(px=.4, h=1.3, lean=4, gx=1.0, gy=.12, w=42)),
 (12.80, "out",  dict(px=.2, h=1.3, lean=0, gx=.5, gy=-.7, w=-62, ffx=.45, bfx=-.45)),
 (13.60, "s",    dict(px=-.1, walk=1, amp=.5, h=1.3, lean=2, gx=.5, gy=-.7, w=-70)),
 (17.00, "lin",  dict(px=-4.2)),
]
S_RAW = [
 (0.00, "s",    dict(px=3.9, h=1.254, lean=8, ffx=0.654, bfx=-0.600, gx=0.472, gy=-0.472, w=8)),
 (2.85, "s",    dict()),
 (3.00, "out",  dict(px=4.1, h=1.068, lean=14, gx=-0.236, gy=-0.531, w=5, ffx=0.545, bfx=-0.654)),
 (3.22, "in",   dict(px=1.9, h=1.112, lean=30, gx=1.003, gy=-0.354, w=2, ffx=1.199, bfx=-0.763)),
 (3.55, "over", dict(px=2.1, h=1.145, lean=38, gx=0.944, gy=-0.649, w=-22, ffx=1.090, bfx=-0.763)),
 (3.90, "s",    dict(px=2.8, h=1.221, lean=16, gx=0.354, gy=0.059, w=-5, ffx=0.763, bfx=-0.654)),
 (4.12, "out",  dict(px=3.0, h=1.145, lean=8, gx=0.590, gy=0.531, w=0, ffx=0.654, bfx=-0.600)),
 (4.45, "snap", dict(px=3.0, h=1.090, lean=-4, gx=0.590, gy=0.590, w=-3, ffx=0.491, bfx=-0.763)),
 (4.85, "s",    dict(px=3.9, h=1.221, lean=12, gx=0.354, gy=-0.236, w=8, ffx=0.763, bfx=-0.654)),
 (5.35, "s",    dict(px=3.3, h=1.145, lean=14, gx=0.354, gy=-0.413, w=6)),
 (5.55, "out",  dict(px=3.3, h=0.894, lean=18, gx=-0.354, gy=-0.885, w=-6, ffx=0.872, bfx=-0.218)),
 (5.85, "snap", dict(px=1.9, h=0.850, lean=22, gx=1.062, gy=-0.944, w=-3, ffx=1.308, bfx=-0.218)),
 (6.45, "s",    dict(px=1.9, h=0.894, lean=22, gx=1.062, gy=-0.944, w=-3)),
 (6.95, "out",  dict(px=3.0, h=1.2, lean=10, gx=.47, gy=-.12, w=8, ffx=.65, bfx=-.65)),
 (7.90, "s",    dict(px=3.1, h=1.22, lean=10, gx=.41, gy=-.24, w=8)),
 (8.30, "out",  dict(px=2.8, h=1.2, lean=12, gx=.4, gy=-.2, w=6, ffx=.6, bfx=-.6)),
 (9.20, "s",    dict(px=2.5, h=1.18, lean=12, gx=.4, gy=-.2, w=6)),
 (9.85, "out",  dict(px=2.5, h=1.08, lean=16, gx=-.25, gy=-.2, w=6, ffx=.55, bfx=-.65)),
 (10.04,"snap", dict(px=2.25, h=1.1, lean=26, gx=.9, gy=-.15, w=4, ffx=1.2, bfx=-.75)),
 (10.14,"s",    dict(px=2.3, h=1.1, lean=14, gx=.7, gy=-.1, w=8, ffx=1.1)),
 (10.60,"out",  dict(px=2.9, h=1.1, lean=-18, gx=-.1, gy=.3, w=70, ffx=.3, bfx=-.9, ffl=.15)),
 (11.20,"out",  dict(px=3.6, h=.9, lean=-46, gx=-.3, gy=-.2, w=140, ffx=.2, bfx=-1.0)),
 (12.20,"in",   dict(px=4.9, h=.33, lean=-84, gx=-.6, gy=-.5, w=175, ffx=.1, bfx=-1.1, ffl=0, bfl=0)),
 (17.00,"s",    dict()),
]
KK, SK = build_keys(K_RAW), build_keys(S_RAW)
T_CUT = 6.50
IMPACT_T = 10.12          # final slash lands (single burst, as in the reference)
CLASHES = [(3.30, "k", .83), (4.30, "k", .88), (T_CUT, "k", 1.0)]   # (time, who, s along blade)
TOTAL = 16.2

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

def bump(t, t0, dur=.45): return max(0.0, 1 - abs(t - t0)/dur)
DASH = (8.95, 10.02)
def cam(t):
    k, sp = st_k(t), st_s(t); mx = (k["pel"][0] + sp["pel"][0])/2
    zoom = 1.0 - .04*min(1, t/10)
    for tc, a in ((3.30, .12), (4.30, .14), (T_CUT, .16)): zoom -= a*bump(t, tc)
    cx, cy = mx*.8, .5; wide = False
    if DASH[0] <= t < DASH[1]:
        n = int(round((t - DASH[0])*24)); ph = n % 6
        if ph < 4: zoom = .58; cx = k["pel"][0] + 1.4; cy = GY + 1.9          # close-up on the runner
        else: zoom = 1.55; cx = (k["pel"][0] + sp["pel"][0])/2; cy = .3; wide = True   # wide whip shot
    elif IMPACT_T - .05 <= t < IMPACT_T + 1.0:
        zoom = .62; cx = (k["pel"][0] + sp["pel"][0])/2; cy = GY + 1.9
    elif IMPACT_T + 1.0 <= t < IMPACT_T + 2.2:
        u = (t - IMPACT_T - 1.0)/1.2; zoom = .62 + (1.05 - .62)*u*u*(3 - 2*u); cx = (k["pel"][0] + sp["pel"][0])/2*(1 - u) + mx*.8*u; cy = GY + 1.9 + (.5 - GY - 1.9)*u
    return cx, cy, zoom
def cam_wide(t):
    return DASH[0] <= t < DASH[1] and int(round((t - DASH[0])*24)) % 6 >= 4
