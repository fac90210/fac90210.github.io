# Horror animation: kinematic, uncanny, exaggerated

## What makes motion scary

- **Wrong timing, not wrong poses.** A human-looking pose is fine. Horror comes
  from holding still too long, then moving too fast, or from parts moving at
  different rhythms.
- **The head is the anchor.** Keep it level and locked toward its target
  while the body heaves (the stalk cycle does this). Stillness against
  motion reads as attention.
- **Weight.** Heavy entities settle: impact frame, 2–4 frames of
  compression, slow recovery. Light entities have no settle at all, which is
  also eerie.
- **Break arcs on purpose.** Natural motion moves in arcs. An occasional linear,
  mechanical move (head snaps along a straight line) reads as inhuman.
- **Twitches**: 1–2-frame rotations of 5–15° on the head, a hand or a shoulder,
  at irregular intervals (never evenly spaced), then back.

## Timing chart (30 fps)

| Motion | Frames | Shape |
|---|---|---|
| Heavy stalk step | 20–28 per step | contact hold 3–4 f, slow lift, fast plant |
| Idle breathe | 60–120 loop | chest/shoulders only, 1–3° |
| Twitch overlay | 1–2 f out, 2–4 f back | random gaps 20–90 f |
| Head snap to target | 2–4 f | linear, overshoot 5°, settle 6 f |
| Lunge anticipation | 6–12 f | coil back and down, hold 2–4 f |
| Lunge strike | 3–5 f | near-linear, arms leading |
| Lunge recovery | 12–20 f | overshoot, then slow straighten |
| Death / despawn | 8–15 f | collapse or fold faster than gravity |

## Clip list for a hostile entity

Make each one its own Blender action, and export each to its own FBX
(`export_roblox.py <blend> <name>.fbx <Action>`):

1. **Idle**: loop; breathing + sparse twitches.
2. **Stalk**: loop; `scripts/anim_stalk_cycle.py` is the starting template.
3. **Alert**: one-shot; the head snaps first, then the body follows 6–10 f later.
4. **Lunge/Attack**: one-shot; anticipation → strike → recovery.
5. **Jumpscare**: one-shot, 15–30 f, built for a close camera.

Rushers (entities that fly down corridors) often need no skeletal clip
beyond a vibrating idle. Their motion is procedural: position along path
nodes, plus camera shake and light flicker in Luau.

## Mixing keyed and procedural motion in Roblox

The Animator writes each Bone's `Transform`. Scripts should leave
`Transform` alone and offset the **Bone's `CFrame`** (its rest offset),
which the Animator never writes. Then the animation plays on top of the script's
offset, and neither fights the other. `luau/HeadTracking.luau` does this for
neck and head look-at. `luau/CameraShake.luau` shakes the player's camera by
proximity. The Model's root position (chasing, lunging along a corridor)
is scripted on the Model's pivot with `PivotTo`, never baked into clips.

Smooth procedural motion with frame-rate-independent damping
(`alpha = 1 - math.exp(-speed * dt)`), not fixed lerp factors. Smoothing
that depends on frame rate looks different on every device.
