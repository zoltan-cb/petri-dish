#!/usr/bin/env python3
"""Display an image on Inky Impression 4" (640x400, 7-colour).

Usage: python3 display-image.py <image_path> [--rotate 0|90|180|270]

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
    parser.add_argument("--no-fit", action="store_true",
                        help="Use simple resize instead of center-crop fit (may letterbox)")
    args = parser.parse_args()

    display = auto()
    img = Image.open(args.image)

    if args.rotate in (90, 270):
        target = (display.resolution[1], display.resolution[0])  # 400x640
    else:
        target = display.resolution  # 640x400

    if args.no_fit:
        img = img.resize(target)
    else:
        # Center crop to fill — no letterboxing, no unused space
        img = ImageOps.fit(img, target, method=Image.LANCZOS)

    if args.rotate != 0:
        img = img.rotate(args.rotate, expand=True)

    display.set_image(img)
    print(f"Displaying {args.image} ({display.resolution[0]}x{display.resolution[1]}, rotate={args.rotate})...")
    display.show()
    print("Done.")


if __name__ == '__main__':
    main()
