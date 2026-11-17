"""Finish the cutscene frames: bloom, vignette and cinema bars.

  python3 soccer_post.py IN_DIR OUT_DIR
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

IN_DIR, OUT_DIR = sys.argv[1], sys.argv[2]
os.makedirs(OUT_DIR, exist_ok=True)
OUT_W, OUT_H = 1280, 720


def blur(rgb, radius):
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius))).astype(np.float32) / 255.0


vignette = None
for name in sorted(f for f in os.listdir(IN_DIR) if f.endswith(".png")):
    target = os.path.join(OUT_DIR, name)
    if os.path.exists(target):
        continue
    rgb = np.asarray(Image.open(os.path.join(IN_DIR, name)).convert("RGB")).astype(np.float32) / 255.0
    h, w = rgb.shape[:2]
    peak = rgb.max(-1, keepdims=True)
    bright = rgb * np.clip((peak - 0.72) / 0.28, 0, 1)
    glow = 0.50 * blur(bright, 4) + 0.40 * blur(bright, 14) + 0.30 * blur(bright, 40)
    out = 1.0 - (1.0 - rgb) * (1.0 - np.clip(glow * 0.85, 0, 1))        # screen blend
    if vignette is None:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot((xs - w / 2) / (w / 2), (ys - h / 2) / (h / 2) * 0.8)
        vignette = (1.0 - 0.32 * np.clip(d - 0.45, 0, 1) ** 1.6)[..., None]
    out = np.clip(out * vignette, 0, 1)
    frame = np.zeros((OUT_H, OUT_W, 3), np.float32)
    top = (OUT_H - h) // 2
    frame[top:top + h, :w] = out
    Image.fromarray((frame * 255).astype(np.uint8)).save(target)
