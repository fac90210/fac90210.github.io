# Style guide: stylised mid-poly horror

The target is what DOORS does: shapes simple enough to run on a phone, made to
look rich by smooth shading, good normals and heavy, believable grime. The
budgets below are this skill's working targets, not numbers from DOORS.

## 1. Modelling: stylised mid-poly

**Silhouette first.** Every asset must read as a flat black shape. Horror
entities read through *wrong proportions* more than through detail: limbs a
bit too long, a head a bit too small or too still, a hunch, too many joints.
Exaggerate one or two of those per entity, not all of them.

**Detail scale.** Model forms down to about 2 cm. Anything finer (stitching,
pores, small cracks, screw heads) goes in the normal map. No micro-geometry.

**Triangle budgets** (Roblox hard limit: 20,000 per mesh):

| Asset | Target tris | Notes |
|---|---|---|
| Hero entity (body) | 4,000–10,000 | single skinned mesh; split head/body only if over 20k |
| Simple entity (floating, rushing) | 1,000–4,000 | silhouette and VFX do the work |
| Door with frame | 1,200–3,000 | knob and hinges: separate small meshes |
| Hero prop (lamp, wardrobe, desk) | 500–2,500 | |
| Small prop (book, key, vase) | 50–500 | |
| Modular wall/floor tile | 20–300 | trims and baseboards carry the detail |
| Trim strip (moulding, skirting) | 50–400 per 4 studs | |

**Topology.**
- Quads in deforming areas; edge loops around every joint (3 loops at
  elbows/knees, 5 at shoulders/hips/neck) and around eyes/mouth if they move.
- Spend polygons on the silhouette, never on flat areas that face the camera.
- Support loops or bevels (one 2-segment bevel) on hard edges so Weighted
  Normals can keep flat faces flat.

**Shading.** Shade smooth everywhere, mark sharp edges above ~40°, then add a
Weighted Normal modifier (Keep Sharp on, Weight 50). This is what makes a
mid-poly box look like a machined object. `scripts/finish_mesh.py` applies it.
Export with smoothing on (`mesh_smooth_type="FACE"`).

**Environment kits.** Build on a stud grid: wall tiles 4 or 8 studs wide,
storey height 12–14 studs, door openings about 4.5 × 8 studs. Pivots go at a
bottom corner, so pieces snap together in Studio. Proportions are realistic, then
pushed slightly: thicker mouldings, deeper door frames, oversized knobs and
hinges. Players must read them in a dark room by flashlight.

**Naming.** `LOW_<Asset>` for the game mesh, `HIGH_<Asset>` for the sculpt,
`RIG_<Asset>` for the armature, `REF_*` for references.

## 2. Texturing: grungy stylised PBR

**Maps per material** (all 1024 px, see SKILL.md for the Roblox rules):
Albedo/Color, Normal (OpenGL Y+), Roughness, Metalness, and Emissive mask
where something glows.

**Texel density.** About 512 px per 4 studs (≈ 460 px/m) for the environment;
entities get more (one 1024 sheet per entity body). Trim sheets for
architecture: one 1024 sheet of mouldings, panels and edges shared across
the whole kit.

**Albedo.** Mid-value, desaturated base colours; no pure black (keep
values ≥ 30/255) or pure white (≤ 230/255). Darkness comes from lighting,
not from black albedo. No baked lighting in albedo except the subtle AO
multiply below.

**The grunge stack**, bottom to top. Each layer is masked by a baked map:

1. **Base material**: colour + roughness value (painted wood 0.55, varnish 0.35,
   wallpaper 0.8, bare metal 0.4 with metalness 1).
2. **Colour variation**: low-frequency noise, ±6% value, slight hue drift.
3. **Ambient occlusion**: multiply baked AO into albedo at 30–50%; it gives
   the dirty, lived-in contact shadows.
4. **Cavity dirt**: dark brown-grey in crevices (curvature concave + AO),
   rougher (+0.15).
5. **Edge wear**: convex curvature reveals the under-material (bare wood
   under paint, bright metal under paint), smoother (−0.15), metalness 1 on
   metal.
6. **Scratches**: fine directional strokes on high-contact faces (door
   push areas, knobs, floors in walking lanes).
7. **Stains & drips**: vertical gravity gradients from top edges: water
   streaks (darker, smoother), rust bleeding from metal parts (orange-brown,
   rough), slime (desaturated green-yellow, very smooth: roughness 0.1–0.2,
   so a flashlight catches it).
8. **Dust**: upward-facing mask (world normal Z), lighter and rougher.

**Roughness carries the look.** Wet, slimy and polished-metal areas must be
clearly smoother than their surroundings, or flashlights won't pick them out.
Check every material under a SpotLight.

**Entity skin.** Desaturated, slightly translucent-looking (fake it with a
warmer, brighter cavity colour), with roughness breakup so it shines wet in
spots. Eyes and mouth interiors: emissive mask or near-black with very low
roughness.

## 3. Lighting test (do it for every asset)

Test under the lighting the game will use: `Lighting.Technology = Future`,
low ambient (≈ 20,20,25), one warm PointLight (2700 K-ish, Range 16) and a
player-flashlight SpotLight (Angle 45, Range 40, Brightness 2). The asset passes
when:
- its silhouette reads with only the flashlight on;
- metal and wet areas throw a clear specular highlight;
- grime reads in the falloff and doesn't turn to flat mud.

In Blender, `preview.py` approximates this; the real test is in Studio.
