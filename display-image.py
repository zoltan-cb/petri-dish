#!/usr/bin/env python3
"""Display an image on Inky Impression e-ink display (7-colour).

Usage: python3 display-image.py <image_path> [--rotate 0|90|180|270] [--mode fit|fill]

Designed to run ON the Pi Zero. For remote use, SCP the image first then SSH to run this.
"""

import argparse
import sys
from PIL import Image, ImageOps
from inky.auto import auto


def main():
    parser = argparse.ArgumentParser(description="Display image on Inky Impression")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270],
                        help="Rotation in degrees (default: 0)")
    parser.add_argument("--mode", default="fit", choices=["fit", "fill"],
                        help="fit = scale to fit with white margins (default); fill = center-crop to fill")
    args = parser.parse_args()

    display = auto()
    img = Image.open(args.image).convert("RGB")

    if args.rotate in (90, 270):
        target = (display.resolution[1], display.resolution[0])
    else:
        target = display.resolution

    if args.mode == "fill":
        img = ImageOps.fit(img, target, method=Image.LANCZOS)
    else:
        # Scale to fit entirely within target, white margins
        img = ImageOps.contain(img, target, method=Image.LANCZOS)
        canvas = Image.new("RGB", target, (255, 255, 255))
        offset = ((target[0] - img.size[0]) // 2, (target[1] - img.size[1]) // 2)
        canvas.paste(img, offset)
        img = canvas

    if args.rotate != 0:
        img = img.rotate(args.rotate, expand=True)

    display.set_image(img)
    print(f"Displaying {args.image} ({display.resolution[0]}x{display.resolution[1]}, rotate={args.rotate}, mode={args.mode})...")
    display.show()
    print("Done.")


if __name__ == '__main__':
    main()
