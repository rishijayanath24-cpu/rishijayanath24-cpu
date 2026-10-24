"""Convert an image into ASCII art for the profile card.

Usage: python scripts/make_ascii.py <image> [--cols 44] [--rows 23]
                                    [--box left,top,right,bottom] [--mode tone|subject]

Modes:
  tone     brightness maps to character density (suits photos).
  subject  the background colour, sampled from the top-left corner, is blank
           (suits flat illustrations).

Output goes to assets/ascii.txt (dark card) and assets/ascii-light.txt (light card).
"""
import argparse
import math
import os

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

GAMMA = float(os.environ.get("ASCII_GAMMA", "0.7"))
GAMMA_LIGHT = float(os.environ.get("ASCII_GAMMA_LIGHT", "1.8"))
RAMP = " .:-=+*#%@"


def convert(path, cols, rows, box=None, mode="tone", invert=False):
    img = Image.open(path).convert("RGB")
    if box:
        img = img.crop(box)
    if mode == "tone":
        gray = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
        img = gray.filter(ImageFilter.UnsharpMask(radius=4, percent=120)).convert("RGB")
    else:
        img = ImageEnhance.Contrast(img).enhance(1.4)
    img = img.resize((cols, rows), Image.LANCZOS)
    bg = img.getpixel((0, 0))
    out = []
    for y in range(rows):
        line = ""
        for x in range(cols):
            px = img.getpixel((x, y))
            if mode == "tone":
                nx, ny = (x + 0.5) / cols * 2 - 1, (y + 0.5) / rows * 2 - 1
                fade = max(0.0, min(1.0, (1.1 - math.hypot((nx + 0.05) / 0.72, ny / 1.0)) / 0.3))
                tone = 1 - px[0] / 255 if invert else px[0] / 255
                level = tone ** (GAMMA_LIGHT if invert else GAMMA) * fade * (len(RAMP) - 1)
            else:
                dist = math.dist(px, bg) / math.dist((0, 0, 0), (255, 255, 255))
                level = dist * 2.2 * (len(RAMP) - 1)
            line += RAMP[min(int(level), len(RAMP) - 1)]
        out.append(line.rstrip())
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--cols", type=int, default=44)
    ap.add_argument("--rows", type=int, default=23)
    ap.add_argument("--box", type=lambda s: tuple(int(v) for v in s.split(",")))
    ap.add_argument("--mode", choices=["tone", "subject"], default="tone")
    a = ap.parse_args()
    os.makedirs("assets", exist_ok=True)
    # Dark card: bright areas are dense. Light card: dark areas are dense.
    for name, invert in (("ascii.txt", False), ("ascii-light.txt", a.mode == "tone")):
        art = convert(a.image, a.cols, a.rows, a.box, a.mode, invert)
        with open(os.path.join("assets", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(art + "\n")
    print(art)


if __name__ == "__main__":
    main()
