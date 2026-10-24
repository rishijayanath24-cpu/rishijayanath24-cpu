"""Convert a portrait into dense ASCII art for the profile card.

Usage: python scripts/make_ascii.py <image> [--cols 56] [--rows 29]
                                    [--box left,top,right,bottom]

The backdrop is estimated from the image edges and left blank; everything
inside the silhouette is drawn with the full 70-character ramp, so the
figure reads as a solid, textured shape.

Output goes to assets/ascii.txt (dark card, bright areas dense) and
assets/ascii-light.txt (light card, dark areas dense).
"""
import argparse
import bisect
import os

from PIL import Image, ImageFilter, ImageOps

# Densest first.
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'."
FLOOR = 0.3  # lowest density used inside the silhouette


def luminance_grid(path, cols, rows, box):
    img = Image.open(path).convert("L")
    if box:
        img = img.crop(box)
    img = ImageOps.autocontrast(img, cutoff=1)
    img = img.filter(ImageFilter.UnsharpMask(radius=4, percent=120))
    img = img.resize((cols, rows), Image.LANCZOS)
    return [[img.getpixel((x, y)) / 255 for x in range(cols)] for y in range(rows)]


def silhouette(grid, cols, rows):
    """Boolean mask of the subject: cells that differ from a smooth backdrop."""
    left = [(row[0] + row[1]) / 2 for row in grid]
    right = [(row[-1] + row[-2]) / 2 for row in grid]
    last = int(rows * 0.65)  # lower rows reuse an upper row (shoulders reach the edge)
    mask = [[False] * cols for _ in range(rows)]
    for y in range(rows):
        yy = min(y, last)
        for x in range(cols):
            base = left[yy] + (right[yy] - left[yy]) * x / (cols - 1)
            mask[y][x] = abs(grid[y][x] - base) > 0.07
    # Drop isolated specks, then fill each row between its outermost cells.
    kept = [[False] * cols for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            if mask[y][x]:
                n = sum(
                    mask[j][i]
                    for j in range(max(0, y - 1), min(rows, y + 2))
                    for i in range(max(0, x - 1), min(cols, x + 2))
                ) - 1
                kept[y][x] = n >= 3
    for y in range(rows):
        xs = [x for x in range(cols) if kept[y][x]]
        if xs:
            for x in range(xs[0], xs[-1] + 1):
                kept[y][x] = True
    return kept


def render(grid, mask, invert):
    inside = sorted(v for row, mrow in zip(grid, mask) for v, m in zip(row, mrow) if m)
    out = []
    for row, mrow in zip(grid, mask):
        line = ""
        for v, m in zip(row, mrow):
            if not m:
                line += " "
                continue
            t = bisect.bisect_left(inside, v) / len(inside)  # rank = equalized tone
            if invert:
                t = 1 - t
            level = FLOOR + (1 - FLOOR) * t
            line += RAMP[min(int((1 - level) * len(RAMP)), len(RAMP) - 1)]
        out.append(line.rstrip())
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--cols", type=int, default=56)
    ap.add_argument("--rows", type=int, default=29)
    ap.add_argument("--box", type=lambda s: tuple(int(v) for v in s.split(",")))
    a = ap.parse_args()
    grid = luminance_grid(a.image, a.cols, a.rows, a.box)
    mask = silhouette(grid, a.cols, a.rows)
    os.makedirs("assets", exist_ok=True)
    for name, invert in (("ascii.txt", False), ("ascii-light.txt", True)):
        art = render(grid, mask, invert)
        with open(os.path.join("assets", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(art + "\n")
    print(art)


if __name__ == "__main__":
    main()
