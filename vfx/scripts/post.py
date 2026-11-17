"""Add glow to rendered RGBA frames, then make video frames and flipbook sheets.

  python3 post.py video    IN_DIR OUT_DIR WIDTH HEIGHT LABEL
  python3 post.py flipbook IN_DIR OUT_PNG GRID first_frame step
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def load(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0


def blur(rgb, radius):
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius))).astype(np.float32) / 255.0


def with_glow(rgba, amount=1.0):
    """Returns premultiplied color and alpha with a soft glow around bright areas."""
    alpha = rgba[..., 3:4]
    premult = rgba[..., :3] * alpha
    scale = rgba.shape[0] / 640.0
    bright = premult * np.clip((premult.max(-1, keepdims=True) - 0.35) / 0.4, 0, 1)
    glow = 0.55 * blur(bright, 5 * scale) + 0.45 * blur(bright, 18 * scale) + 0.35 * blur(bright, 48 * scale)
    glow *= amount
    color = premult + glow * (1.0 - 0.6 * premult)
    alpha = np.clip(np.maximum(alpha, glow.max(-1, keepdims=True)), 0, 1)
    return np.clip(color, 0, 1), alpha


def background(width, height):
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    d = np.hypot((xs - width / 2) / width, (ys - height / 2) / height)
    shade = np.clip(1.0 - d * 1.5, 0, 1)[..., None]
    return np.array([0.030, 0.030, 0.042], np.float32) + shade * np.array([0.050, 0.050, 0.065], np.float32)


def video(in_dir, out_dir, width, height, label):
    os.makedirs(out_dir, exist_ok=True)
    bg = background(width, height)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for name in sorted(f for f in os.listdir(in_dir) if f[0].isdigit() and f.endswith(".png")):
        rgba = load(os.path.join(in_dir, name))
        color, alpha = with_glow(rgba)
        h, w = color.shape[:2]
        if h != height:  # fit the frame height, keep the aspect ratio
            new_w = round(w * height / h)
            both = np.concatenate([color, alpha], -1)
            both = np.asarray(Image.fromarray((both * 255).astype(np.uint8)).resize((new_w, height), Image.LANCZOS)) / 255.0
            color, alpha = both[..., :3], both[..., 3:4]
            w = new_w
        frame = bg.copy()
        x0 = (width - w) // 2
        frame[:, x0:x0 + w] = frame[:, x0:x0 + w] * (1 - alpha) + color
        img = Image.fromarray((np.clip(frame, 0, 1) * 255).astype(np.uint8))
        ImageDraw.Draw(img).text((28, height - 48), label, fill=(170, 170, 185), font=font)
        img.save(os.path.join(out_dir, name))


def flipbook(in_dir, out_png, grid, first, step):
    cell = 1024 // grid
    sheet = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    for index in range(grid * grid):
        path = os.path.join(in_dir, f"{first + index * step:04d}.png")
        if not os.path.exists(path):
            continue
        color, alpha = with_glow(load(path))
        straight = np.where(alpha > 1e-4, color / np.maximum(alpha, 1e-4), 0)
        rgba = np.concatenate([np.clip(straight, 0, 1), alpha], -1)
        img = Image.fromarray((rgba * 255).astype(np.uint8)).resize((cell, cell), Image.LANCZOS)
        sheet.paste(img, ((index % grid) * cell, (index // grid) * cell))
    sheet.save(out_png)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "video":
        video(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    else:
        flipbook(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
