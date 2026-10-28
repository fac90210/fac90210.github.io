# Image to 3D with TripoSR (CPU)

How the Wretch's base mesh was made from `../concept_sheet.webp`.

1. Get TripoSR's code from the Hugging Face Space `stabilityai/TripoSR`
   (the `tsr/` folder) and the weights from the model repo
   `stabilityai/TripoSR` (`config.yaml`, `model.ckpt`, 1.7 GB) into `weights/`.
2. Install CPU PyTorch plus `omegaconf einops "transformers<4.50" trimesh
   huggingface-hub imageio scikit-image scipy pillow`.
3. Two patches, since `torchmcubes` and `rembg` need builds from GitHub:
   - `tsr/models/isosurface.py`: replace `from torchmcubes import marching_cubes`
     with a wrapper around `skimage.measure.marching_cubes` that returns
     `verts[:, [2, 1, 0]]` and the faces as int64 tensors. Its faces wind the
     other way, so `build_from_concept.py` recomputes outward normals.
   - `tsr/utils.py`: make `import rembg` optional (`cutout.py` removes the
     background instead).
4. `python cutout.py concept_sheet.webp cut` writes `cut_front/side/back.png`.
5. `python run.py cut_front.png wretch_front.obj 320` (about a minute on 4 CPUs).
6. `python ../build_from_concept.py wretch_front.obj cut <out dir> -90` (Blender's
   `bpy` venv with pillow and scipy) builds the textured Roblox mesh.
