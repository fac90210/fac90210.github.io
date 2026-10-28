# Curriculum

Each lesson produces an asset or a skill you'll reuse. Lessons 0–10 take one
hostile entity from nothing to in-game; 11–14 build the environment kit it
haunts. Track progress in the checklist (tick items as they're done).

## Track A: one hostile entity

- [ ] **0. Setup & scale calibration.** Blender scene conventions; export the
  blockout with `--with-ref`, import into Studio, compare the 4-stud cube,
  record the scale in `roblox-notes.md`.
- [ ] **1. Concept & silhouette.** Behaviour archetype, body plan, one
  signature wrongness; 3–5 silhouette variants; choose by testing them as black
  shapes in a dark corridor render.
- [ ] **2. Blockout.** `proportions.py` → `blockout_entity.py`; turntable
  preview; proportions in studs against a 5-stud player.
- [ ] **3. High-poly sculpt.** Big forms → secondary forms → damage and
  tertiary detail; what goes in the normal map and what stays as geometry.
- [ ] **4. Retopology & UVs.** Mid-poly budget, deformation loops, UV seams in
  hidden places, texel density, `finish_mesh.py` checks.
- [ ] **5. Baking.** High → low: normal (OpenGL), AO, curvature; cage
  distance; fixing skew and artefacts.
- [ ] **6. Grunge PBR texturing.** The 8-layer stack from the style guide,
  built as Blender shader nodes and baked to the four maps at 1024.
- [ ] **7. Rigging & skinning.** `rig_entity.py`; pose tests; weight fixes;
  extra bones the design needs.
- [ ] **8. Animation.** Idle, Stalk, Alert, Lunge, Jumpscare; timing chart;
  twitch overlays; contact-sheet reviews.
- [ ] **9. Into Roblox.** Import, SurfaceAppearance, AnimationController,
  Animation Editor import, lighting test under Future lighting.
- [ ] **10. Procedural layer.** Head tracking, camera shake, chase/lunge
  movement along nodes, light flicker on approach, sound cues.

## Track B: environment kit

- [ ] **11. Modular grid & trim sheet.** Wall, floor, ceiling tiles on a stud
  grid; one shared 1024 trim sheet.
- [ ] **12. Doors.** Frame, door leaf, knob, hinges; pivot for opening; a
  numbered door plate; rigged or tweened opening.
- [ ] **13. Hero props.** Wardrobe (hiding spot), lamp, desk, bed: weathering
  passes per material.
- [ ] **14. Dressing a room.** Assemble a room in Studio, lighting pass,
  performance check (triangle and texture memory).
