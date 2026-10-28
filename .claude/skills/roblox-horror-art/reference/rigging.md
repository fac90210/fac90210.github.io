# Rigging and skinning for Roblox

## Rig layout

Roblox skinned meshes import as a MeshPart with `Bone` instances under it.
Monsters that aren't player avatars don't need the R15 layout. Use your own
bone names and drive the model with an **AnimationController + Animator**,
not a Humanoid, unless you want Humanoid pathfinding and physics.

Rules (Roblox specifications):
- One parentless bone, **`Root`, at 0,0,0, with no weights**. Everything
  parents to it. Move the whole entity by moving the Model, not by animating
  Root, unless the clip itself must travel (a lunge that ends somewhere else).
- **≤ 4 influences per vertex**, weights normalised.
- Armature object: rotation 0, scale 1, applied. Bones: rest pose frozen.
- Symmetric names (`_L` / `_R`) and symmetric weights.

`scripts/rig_entity.py` builds this for the humanoid body plan in
`proportions.py`:

```
Root
└ Hips ─ Chest ─ Neck ─ Head
   │       └ Shoulder_L ─ UpperArm_L ─ LowerArm_L ─ Hand_L   (and _R)
   └ UpperLeg_L ─ LowerLeg_L ─ Foot_L                       (and _R)
```

Add bones per design: extra spine segments for a creature that undulates,
jaw and eyelid bones for a face that moves, finger chains when hands grab,
tendrils as 4–8-bone chains. Each extra bone costs animation work. Add one only
when something must move on its own.

## Weights

1. Bind with automatic weights (`ARMATURE_AUTO`), as the script does.
2. Pose-test: rotate every joint to its extreme (elbow 140°, knee 140°, neck
   ±60° yaw, spine ±30°) with `preview.py`, or ask the user to look in Blender.
3. Fix the usual problems:
   - **Candy-wrapper twist** at wrists/forearms: spread the twist over the
     LowerArm with a gradient, or add a twist bone.
   - **Collapsing elbows/knees**: needs the 3 edge loops; smooth weights
     across them.
   - **Armpit/groin pulling**: chest/hip weights bleeding into arms/legs.
     Normalise them back toward the body.
   - **Head pulling the shoulders**: limit Neck/Head weights above the
     collarbone line.
4. Re-run the clean-up in `rig_entity.py` (cap at 4, normalise, strip Root)
   after any hand painting. `export_roblox.py` refuses an export that breaks
   the rules.

## Organic single-mesh entities

Floating or snake-like entities (a mass of limbs, a hanging creature, a
crawling torso) are still one mesh and one bone hierarchy:
- Spine chains of 6–12 bones let a body ripple; animate them with offset
  sine waves (follow-through) plus a few hand-keyed accents.
- Use Blender constraints (IK, Damped Track, Spline IK) while animating, but
  **bake to plain keys** before export. Roblox only reads bone transforms.

## In Studio

1. Import the FBX with the 3D Importer. Check the rig shows Bones under the
   MeshPart. If the scale is wrong, see the calibration step in SKILL.md.
2. Put the MeshPart in a Model, add `AnimationController` → `Animator`.
3. Import each clip FBX in the Animation Editor (Import → From FBX
   Animation), publish it, and play it from a script with
   `Animator:LoadAnimation`.
4. Bone axes may differ from Blender's after import. Before writing
   procedural bone code, rotate a bone's CFrame by 30° about each axis in
   the command bar and note which axis is yaw/pitch. Record it in
   `roblox-notes.md` and in the Luau config.
