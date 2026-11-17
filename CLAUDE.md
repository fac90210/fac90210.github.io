# Blender work in this repository

## Skills

The Blender skill pack from https://github.com/arjun988/blender-skills (version 1.3.0, MIT)
is installed in `.claude/skills/`. For every task that involves Blender, 3D assets, VFX,
materials, rendering or game-engine export, invoke the applicable skills with the Skill
tool before you start work, without waiting for the user to ask:

- Start with `blender-director` for any new Blender task.
- Use `vfx-fx` for effects (explosions, fire, smoke, sparks, trails, slashes).
- Use `export-pipeline` and the shared `references/` files before any export.
- Add the specialist skills that the task needs (materials, lighting, rendering,
  compositing, geometry-nodes, hard-surface, and so on).

## Blender in cloud sessions is headless

There is no Blender window and no Blender MCP server here. The skills say "execute via
MCP"; in this environment, do the same operations with Python scripts instead:

- Install with `pip install bpy` (Blender as a Python module), then `import bpy`.
- Render with Cycles on CPU. EEVEE needs a GPU display and is not available.
- Existing scripts are in `vfx/scripts/`; `common.py` has the shared setup helpers.

## Roblox target

VFX made here must be usable in Roblox, but Roblox must not change how they look.
Deliver flipbook sheets (1024 x 1024, 4x4 or 8x8 grid, transparent) for particle
effects, and FBX meshes with textures for models.

## Check the result visually

There is no live viewport. To see the scene, render frames to PNG files and open them
with the Read tool. Do this before you deliver:

- Render a few key frames at low resolution first (start, peak, end of the effect).
- Put several frames on one contact sheet with ffmpeg to compare them in one image.
- Look at the final video frames and the flipbook sheets, not only the test frames.
