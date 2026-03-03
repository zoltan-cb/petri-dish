#!/usr/bin/env python3
"""Rotate Victorian fake math plates on Inky Impression e-ink displays.

Reads local PNG files from ~/math-plates/, picks a random one (avoiding
the last shown), fits on white canvas, quantizes to 7-colour palette
with Floyd-Steinberg dithering, and displays via inky.auto.

Usage: python3 rotate-math.py
Designed to run via cron on Pi Zero with Inky Impression 4" attached.
"""

import json
import os
import random
import sys
from pathlib import Path

from PIL import Image, ImageOps
from inky.auto import auto

STATE_FILE = Path.home() / ".math-state.json"
PLATES_DIR = Path.home() / "math-plates"


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last": None, "rotation_offset": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def get_plates():
    if not PLATES_DIR.exists():
        print(f"Plates directory not found: {PLATES_DIR}")
        sys.exit(1)
    plates = sorted(PLATES_DIR.glob("*.png"))
    if not plates:
        print(f"No PNG files found in {PLATES_DIR}")
        sys.exit(1)
    return plates


def pick_plate(plates, state):
    last = state.get("last")
    candidates = [p for p in plates if p.name != last]
    if not candidates:
        candidates = plates
    return random.choice(candidates)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Rotate math plates on e-ink displays")
    parser.add_argument("--rotation-offset", type=int, choices=[0, 90, 180, 270],
                        help="Set rotation offset (0/90/180/270) and save to state file")
    parser.add_argument("--plate", type=str, help="Force a specific plate by filename")
    args = parser.parse_args()

    state = load_state()

    if args.rotation_offset is not None:
        state["rotation_offset"] = args.rotation_offset
        save_state(state)
        print(f"Rotation offset set to {args.rotation_offset}°")

    plates = get_plates()

    if args.plate:
        matches = [p for p in plates if p.name == args.plate or p.stem == args.plate]
        if not matches:
            print(f"Unknown plate: {args.plate}")
            print(f"Available: {', '.join(p.name for p in plates)}")
            sys.exit(1)
        plate_path = matches[0]
    else:
        plate_path = pick_plate(plates, state)

    print(f"Loading {plate_path.name}...")

    display = auto()
    w, h = display.resolution

    img = Image.open(plate_path).convert("RGB")
    iw, ih = img.size

    # Decide orientation: rotate if portrait image on landscape display
    if ih > iw and w > h:
        target = (h, w)
        rotate = True
    else:
        target = (w, h)
        rotate = False

    # Scale to FIT — full image visible, white margins
    img = ImageOps.contain(img, target, method=Image.LANCZOS)
    canvas = Image.new("RGB", target, (255, 255, 255))
    offset = ((target[0] - img.size[0]) // 2, (target[1] - img.size[1]) // 2)
    canvas.paste(img, offset)
    img = canvas

    if rotate:
        img = img.rotate(-90, expand=True)

    # Apply per-display rotation offset
    rotation_offset = state.get("rotation_offset", 0)
    if rotation_offset:
        img = img.rotate(rotation_offset, expand=True)

    # Quantize to 7-colour with dithering
    palette_img = Image.new("P", (1, 1))
    palette_data = [
        0, 0, 0,        # black
        255, 255, 255,  # white
        0, 128, 0,      # green
        0, 0, 255,      # blue
        255, 0, 0,      # red
        255, 255, 0,    # yellow
        255, 128, 0,    # orange
    ] + [0] * (256 - 7) * 3
    palette_img.putpalette(palette_data)

    img_q = img.quantize(colors=7, palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)
    img_display = img_q.convert("RGB")

    display.set_image(img_display)
    print(f"Displaying {plate_path.name} ({w}x{h})...")
    display.show()
    print("Done.")

    state["last"] = plate_path.name
    save_state(state)


if __name__ == "__main__":
    main()
