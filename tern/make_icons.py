"""Draw Tern's icon (a tern in flight on the editor's navy) at every size Chromium needs.

Usage: python -I make_icons.py <out dir>      (needs Pillow)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

NAVY = (27, 32, 42, 255)
BIRD = (95, 208, 199, 255)
S = 1024  # drawn large, then scaled down


def bird():
    # A tern seen from below: long swept wings and a forked tail, as one outline
    # on a 0..100 grid.
    pts = [(50, 38), (60, 30), (78, 22), (95, 20), (80, 32), (64, 44), (58, 50),
           (60, 66), (66, 84), (55, 70), (50, 62),
           (45, 70), (34, 84), (40, 66), (42, 50),
           (36, 44), (20, 32), (5, 20), (22, 22), (40, 30)]
    return [(x * S / 100, (y + 8) * S / 100) for x, y in pts]


def draw():
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 0.22, fill=NAVY)
    d.polygon(bird(), fill=BIRD)
    d.ellipse([S * 0.455, S * 0.40, S * 0.545, S * 0.49], fill=BIRD)  # head
    return img


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    big = draw()
    for size in (16, 24, 32, 48, 64, 128, 256):
        big.resize((size, size), Image.LANCZOS).save(out / f'product_logo_{size}.png')
    big.resize((256, 256), Image.LANCZOS).save(
        out / 'tern.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])
    print(f'icons written to {out}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
