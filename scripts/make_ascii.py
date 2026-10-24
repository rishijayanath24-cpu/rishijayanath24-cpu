"""Convert an image into ASCII art for the profile card.

Usage: python scripts/make_ascii.py <image> [cols] [rows] [left,top,right,bottom]

The background colour is sampled from the top-left corner and rendered as
blank, so the subject stands out. Output goes to assets/ascii.txt.
"""
import math
import os
import sys

from PIL import Image, ImageEnhance

RAMP = " .:-=+*#%@"


def convert(path, cols, rows, box=None):
    img = Image.open(path).convert("RGB")
    if box:
        img = img.crop(box)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = img.resize((cols, rows), Image.LANCZOS)
    bg = img.getpixel((0, 0))
    out = []
    for y in range(rows):
        line = ""
        for x in range(cols):
            r, g, b = img.getpixel((x, y))
            dist = math.dist((r, g, b), bg) / math.dist((0, 0, 0), (255, 255, 255))
            level = min(int(dist * 2.2 * (len(RAMP) - 1)), len(RAMP) - 1)
            line += RAMP[level]
        out.append(line.rstrip())
    return "\n".join(out)


def main():
    path = sys.argv[1]
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 44
    rows = int(sys.argv[3]) if len(sys.argv) > 3 else 23
    box = tuple(int(v) for v in sys.argv[4].split(",")) if len(sys.argv) > 4 else None
    art = convert(path, cols, rows, box)
    os.makedirs("assets", exist_ok=True)
    with open(os.path.join("assets", "ascii.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(art + "\n")
    print(art)


if __name__ == "__main__":
    main()
