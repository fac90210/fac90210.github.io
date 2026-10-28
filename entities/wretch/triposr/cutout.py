# Cuts each view out of the concept sheet: background is a flat grey, the creature isn't.
# Usage: python cutout.py <sheet> <out_prefix>
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

sheet = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32)
h, w, _ = sheet.shape
for i, name in enumerate(("front", "side", "back")):
    view = sheet[:, i * w // 3:(i + 1) * w // 3]
    # Background colour per row from the view's left and right edges (handles the vignette).
    edge = np.concatenate([view[:, :12], view[:, -12:]], axis=1)
    bg = np.median(edge, axis=1, keepdims=True)
    dist = np.linalg.norm(view - bg, axis=2)
    sat = view.max(axis=2) - view.min(axis=2)
    mask = (dist > 22) | (sat > 18)
    # The floor shadow is darker grey but colourless; the feet are greener and darker.
    # Near the floor, keep only pixels that are tinted or much darker than the shadow.
    value = view.mean(axis=2)
    floor = np.zeros_like(mask)
    floor[int(h * 0.86):] = True
    mask &= ~(floor & (sat < 14) & (value > 62))
    mask = ndimage.binary_opening(mask, iterations=1)
    labels, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    keep = np.isin(labels, 1 + np.flatnonzero(sizes > sizes.max() * 0.02))  # body plus detached claws
    keep = ndimage.binary_closing(keep, iterations=2)
    # Fill only pinholes; big enclosed gaps (between the legs) are background.
    holes, nh = ndimage.label(ndimage.binary_fill_holes(keep) & ~keep)
    hole_sizes = ndimage.sum(np.ones_like(keep), holes, range(1, nh + 1))
    keep |= np.isin(holes, 1 + np.flatnonzero(hole_sizes < 400))
    alpha = ndimage.gaussian_filter(keep.astype(np.float32), 0.8)
    rgba = np.dstack([view, alpha * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgba).save(f"{sys.argv[2]}_{name}.png")
    print(name, "coverage", round(keep.mean() * 100, 1), "%")
