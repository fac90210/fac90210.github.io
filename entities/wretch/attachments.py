"""Claws, fangs and dorsal spikes for the Wretch, added as real geometry where
TripoSR left the hands as mittens, the mouth closed and the spine smooth.

Each part is found on the mesh itself: hand tips are the lowest points of each
arm, toe tips the front of each foot, the mouth and spine by casting rays onto
the head and back. Parts are built in world space (Z up, the creature facing -Y).
"""
import math
import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _curved_spike(bm, base, direction, curl, length, radius, rings=5, sides=7):
    """A tapering horn from `base` along `direction`, bending towards `curl`."""
    d = direction.normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize()
    up = side.cross(d).normalized()
    ctrl = base + d * length * 0.55
    tip = base + (d + curl * 0.9).normalized() * length
    prev_ring = None
    for k in range(rings + 1):
        t = k / rings
        # Quadratic Bezier base -> ctrl -> tip gives the curve; radius tapers to a point.
        c = base * (1 - t) ** 2 + ctrl * 2 * (1 - t) * t + tip * t * t
        if k == rings:
            point = bm.verts.new(c)
            for a in range(sides):
                bm.faces.new((prev_ring[a], prev_ring[(a + 1) % sides], point))
            break
        r = radius * (1 - t) ** 0.8
        ring = [bm.verts.new(c + (side * math.cos(2 * math.pi * a / sides) + up * math.sin(2 * math.pi * a / sides)) * r)
                for a in range(sides)]
        if prev_ring is None:
            bm.faces.new(list(reversed(ring)))  # cap buried in the body
        else:
            for a in range(sides):
                bm.faces.new((prev_ring[a], prev_ring[(a + 1) % sides], ring[(a + 1) % sides], ring[a]))
        prev_ring = ring


def add_attachments(body, height):
    """Builds every attachment into one new object and returns it (not joined)."""
    H = height
    co = np.array([v.co[:] for v in body.data.vertices])
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new()
    counts = {}

    def ray(origin, direction):
        loc, normal, _, _ = bvh.ray_cast(Vector(origin), Vector(direction).normalized(), 5.0)
        return loc, normal

    # --- Hand claws: four long, inward-curling claws at the bottom of each hand. ---
    for s in (1, -1):
        # The hands are the outermost part of the body between hip and knee height;
        # anything within 6% of height of that outer edge belongs to the hand.
        band = co[(co[:, 0] * s > 0) & (co[:, 2] > 0.15 * H) & (co[:, 2] < 0.50 * H)]
        if len(band) == 0:
            continue
        reach = (band[:, 0] * s).max()
        arm = band[band[:, 0] * s > reach - 0.06 * H]
        zmin = arm[:, 2].min()
        tip = arm[arm[:, 2] < zmin + 0.035 * H]
        cx = tip[:, 0].mean()
        y0, y1 = np.percentile(tip[:, 1], 10), np.percentile(tip[:, 1], 90)
        for i, t in enumerate(np.linspace(0.05, 0.95, 4)):
            y = y0 + (y1 - y0) * t
            base = Vector((cx, y, zmin + 0.012 * H))
            down = Vector((-s * 0.12, -0.05, -1))
            curl = Vector((-s * 0.55, -0.15, 0.25))        # towards the body, hooked up
            _curved_spike(bm, base, down, curl, 0.050 * H, 0.0055 * H)
        # Thumb claw: shorter, on the inner front edge, higher up.
        _curved_spike(bm, Vector((cx - s * 0.010 * H, y0, zmin + 0.04 * H)), Vector((-s * 0.4, -0.5, -0.8)),
                      Vector((-s * 0.3, 0.2, 0.3)), 0.030 * H, 0.0045 * H)
        counts["hand claws"] = counts.get("hand claws", 0) + 5

    # --- Toe claws: three heavy talons at the front of each foot, digging down. ---
    for s in (1, -1):
        foot = co[(co[:, 0] * s > 0.0) & (co[:, 2] < 0.05 * H)]
        if len(foot) == 0:
            continue
        ymin = foot[:, 1].min()
        front = foot[foot[:, 1] < ymin + 0.03 * H]
        x0, x1 = np.percentile(front[:, 0], 8), np.percentile(front[:, 0], 92)
        for t in np.linspace(0.1, 0.9, 3):
            x = x0 + (x1 - x0) * t
            base = Vector((x, ymin + 0.012 * H, 0.016 * H))
            _curved_spike(bm, base, Vector((0, -1, -0.25)), Vector((0, -0.1, -0.9)), 0.042 * H, 0.0075 * H)
        counts["toe claws"] = counts.get("toe claws", 0) + 3

    # --- Fangs: rows along the front of the muzzle, upper ones hanging down,
    # lower ones pointing up, longest at the corners like the concept. ---
    head = co[co[:, 2] > 0.80 * H]
    hz0, hz1 = head[:, 2].min(), head[:, 2].max()
    mouth_top, mouth_bottom = hz0 + (hz1 - hz0) * 0.58, hz0 + (hz1 - hz0) * 0.12
    for row, z, pointing in (("upper", mouth_top, -1), ("lower", mouth_bottom, 1)):
        for x in np.linspace(-0.022 * H, 0.022 * H, 7):
            loc, normal = ray((x, -1.0, z), (0, 1, 0))
            if loc is None:
                continue
            corner = abs(x) / (0.022 * H)
            length = (0.020 + 0.022 * corner) * H if row == "upper" else (0.014 + 0.012 * corner) * H
            base = loc + Vector((0, 0.004 * H, 0))       # rooted just inside the skin
            _curved_spike(bm, base, Vector((0, -0.25, pointing)), Vector((0, 0.35, 0)), length, 0.0042 * H, rings=4, sides=6)
            counts["fangs"] = counts.get("fangs", 0) + 1

    # --- Dorsal ridge: spikes down the spine and over the skull. ---
    top = co[:, 2].max()
    for k, z in enumerate(np.linspace(0.97, 0.56, 16)):
        loc, normal = ray((0, 2.0, z * H), (0, -1, 0))   # from behind
        if loc is None or normal.y < 0.1:
            continue
        size = (0.020 - 0.008 * k / 15) * H
        _curved_spike(bm, loc - normal * size * 0.25, normal + Vector((0, 0.5, 0.4)), Vector((0, 0.4, 0.3)), size, size * 0.38, rings=3, sides=6)
        counts["ridge spikes"] = counts.get("ridge spikes", 0) + 1
    for k, y in enumerate(np.linspace(-0.06, 0.02, 4)):   # over the crown, front to back
        loc, normal = ray((0, y * H, top + 0.5), (0, 0, -1))
        if loc is None:
            continue
        size = 0.014 * H
        _curved_spike(bm, loc - normal * size * 0.25, normal + Vector((0, 0.6, 0)), Vector((0, 0.5, 0)), size, size * 0.38, rings=3, sides=6)
        counts["ridge spikes"] = counts.get("ridge spikes", 0) + 1

    mesh = bpy.data.meshes.new("Wretch_Attachments")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Wretch_Attachments", mesh)
    for p in mesh.polygons:
        p.use_smooth = True
    print("attachments:", ", ".join(f"{n} {c}" for n, c in counts.items()))
    return obj
