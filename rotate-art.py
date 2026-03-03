#!/usr/bin/env python3
"""Rotate natural history art on Inky Impression e-ink displays.

Shows plates from Haeckel's Kunstformen der Natur and Brehm's Tierleben.
Auto-detects display dimensions via inky.auto. Downloads a random plate
from a curated list, avoiding the last shown.
Scales to FIT (not crop), preserving full image with white margins.
Quantizes to 7-colour palette with Floyd-Steinberg dithering.

Usage: python3 rotate-art.py
Designed to run via cron on Pi Zero with Inky Impression attached.
"""

import json
import os
import random
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps
from inky.auto import auto

STATE_FILE = Path.home() / ".haeckel-state.json"

# Curated Haeckel plates — WHITE/LIGHT backgrounds only.
# Aesthetic: "butterfly pinned on a white page" — subject floats in centre.
HAECKEL_PLATES = [
    ("Haeckel_Narcomedusae", "https://upload.wikimedia.org/wikipedia/commons/2/22/Haeckel_Narcomedusae.jpg"),
    ("Haeckel_Muscinae", "https://upload.wikimedia.org/wikipedia/commons/e/ee/Haeckel_Muscinae.jpg"),
    ("Haeckel_Trochilidae", "https://upload.wikimedia.org/wikipedia/commons/8/8e/Haeckel_Trochilidae.jpg"),
    ("Haeckel_Chelonia", "https://upload.wikimedia.org/wikipedia/commons/a/a6/Haeckel_Chelonia.jpg"),
    ("Haeckel_Lacertilia", "https://upload.wikimedia.org/wikipedia/commons/7/7a/Haeckel_Lacertilia.jpg"),
    ("Haeckel_Batrachia", "https://upload.wikimedia.org/wikipedia/commons/a/af/Haeckel_Batrachia.jpg"),
    ("Haeckel_Chiroptera", "https://upload.wikimedia.org/wikipedia/commons/f/fd/Haeckel_Chiroptera.jpg"),
    ("Haeckel_Arachnida", "https://upload.wikimedia.org/wikipedia/commons/c/ca/Haeckel_Arachnida.jpg"),
    ("Haeckel_Nudibranchia", "https://upload.wikimedia.org/wikipedia/commons/e/ea/Haeckel_Nudibranchia.jpg"),
    ("Haeckel_Nepenthaceae", "https://upload.wikimedia.org/wikipedia/commons/7/74/Haeckel_Nepenthaceae.jpg"),
    ("Haeckel_Orchidae", "https://upload.wikimedia.org/wikipedia/commons/2/21/Haeckel_Orchidae.jpg"),
    ("Haeckel_Bryozoa", "https://upload.wikimedia.org/wikipedia/commons/3/33/Haeckel_Bryozoa.jpg"),
    ("Haeckel_Prosobranchia", "https://upload.wikimedia.org/wikipedia/commons/4/44/Haeckel_Prosobranchia.jpg"),
    ("Haeckel_Tineida", "https://upload.wikimedia.org/wikipedia/commons/c/c5/Haeckel_Tineida.jpg"),
    ("Haeckel_Amphoridea", "https://upload.wikimedia.org/wikipedia/commons/7/76/Haeckel_Amphoridea.jpg"),
    ("Haeckel_Stephoidea", "https://upload.wikimedia.org/wikipedia/commons/6/6e/Haeckel_Stephoidea.jpg"),
    ("Haeckel_Leptomedusae", "https://upload.wikimedia.org/wikipedia/commons/d/d7/Haeckel_Leptomedusae.jpg"),
    ("Haeckel_Spumellaria", "https://upload.wikimedia.org/wikipedia/commons/0/0c/Haeckel_Spumellaria.jpg"),
    ("Haeckel_Calcispongiae", "https://upload.wikimedia.org/wikipedia/commons/5/59/Haeckel_Calcispongiae.jpg"),
]

# Curated Brehm's Tierleben plates — 19th century natural history lithographs.
# Mix of colour chromolithographic bird plates and detailed animal drawings.
# Style is more naturalistic (habitat scenes) vs Haeckel's white-background aesthetic.
# All sourced from Wikimedia Commons (public domain).
BREHM_PLATES = [
    # Birds — chromolithographic plates by Gustav Mützel et al.
    ("Brehm_GoldenEagle", "https://upload.wikimedia.org/wikipedia/commons/6/64/GoldenEagleBrehm.jpg"),
    ("Brehm_Gyrfalcon", "https://upload.wikimedia.org/wikipedia/commons/a/a1/GyrfalconBrehm.jpg"),
    ("Brehm_Flamingo", "https://upload.wikimedia.org/wikipedia/commons/0/0a/FlamingoBrehm.jpg"),
    ("Brehm_Roller", "https://upload.wikimedia.org/wikipedia/commons/c/cd/RollerBrehm.jpg"),
    ("Brehm_WhiteStork", "https://upload.wikimedia.org/wikipedia/commons/3/34/WhiteStorkBrehm.jpg"),
    ("Brehm_Lapwing", "https://upload.wikimedia.org/wikipedia/commons/0/0d/LapwingBrehm.jpg"),
    ("Brehm_Woodpeckers", "https://upload.wikimedia.org/wikipedia/commons/6/6c/WoodpeckersBrehm.jpg"),
    ("Brehm_Oriole", "https://upload.wikimedia.org/wikipedia/commons/a/a6/OrioleBrehm.jpg"),
    ("Brehm_Mallard", "https://upload.wikimedia.org/wikipedia/commons/8/85/MallardBrehm.jpg"),
    ("Brehm_Lammergeier", "https://upload.wikimedia.org/wikipedia/commons/1/1d/LammergeierBrehms.jpg"),
    ("Brehm_Pitta", "https://upload.wikimedia.org/wikipedia/commons/6/61/PittaBrachyuraBrehms.jpg"),
    ("Brehm_Owl", "https://upload.wikimedia.org/wikipedia/commons/3/3c/OwlBrehm.jpg"),
    ("Brehm_Cranes", "https://upload.wikimedia.org/wikipedia/commons/7/79/Brehm-Gruidae.jpg"),
    ("Brehm_Redstart", "https://upload.wikimedia.org/wikipedia/commons/0/03/RedstartBrehm.jpg"),
    ("Brehm_GoldfinchChaffinch", "https://upload.wikimedia.org/wikipedia/commons/3/34/GoldfinchChaffinchBrehm.jpg"),
    # Mammals & other — detailed drawings and paintings
    ("Brehm_AfricanElephant", "https://upload.wikimedia.org/wikipedia/commons/3/38/Afrikanischer_Elefant-painting.jpg"),
    ("Brehm_Primates", "https://upload.wikimedia.org/wikipedia/commons/5/54/Primates-drawing.jpg"),
    ("Brehm_Fulmar", "https://upload.wikimedia.org/wikipedia/commons/a/ae/Eissturmvogel-drawing.jpg"),
    ("Brehm_FlyingLemur", "https://upload.wikimedia.org/wikipedia/commons/b/bc/Cynocephalus_volans_Brehm1883.jpg"),
    ("Brehm_Amphibia", "https://upload.wikimedia.org/wikipedia/commons/d/da/Brehm_amphibia.jpg"),
]

# Combined plate list for random selection
PLATES = HAECKEL_PLATES + BREHM_PLATES


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last": None, "rotation_offset": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def pick_plate(state):
    last = state.get("last")
    candidates = [p for p in PLATES if p[0] != last]
    if not candidates:
        candidates = PLATES
    return random.choice(candidates)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Rotate Haeckel art on e-ink displays")
    parser.add_argument("--rotation-offset", type=int, choices=[0, 90, 180, 270],
                        help="Set rotation offset (0/90/180/270) and save to state file")
    parser.add_argument("--plate", type=str, help="Force a specific plate by name (e.g. Haeckel_Trochilidae)")
    args = parser.parse_args()

    state = load_state()

    if args.rotation_offset is not None:
        state["rotation_offset"] = args.rotation_offset
        save_state(state)
        print(f"Rotation offset set to {args.rotation_offset}°")

    if args.plate:
        matches = [p for p in PLATES if p[0] == args.plate]
        if not matches:
            print(f"Unknown plate: {args.plate}")
            print(f"Available: {', '.join(p[0] for p in PLATES)}")
            sys.exit(1)
        name, url = matches[0]
    else:
        name, url = pick_plate(state)

    print(f"Downloading {name}...")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        tmp_path = f.name
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            f.write(resp.read())

    try:
        display = auto()
        w, h = display.resolution  # e.g. (640, 400) or (1600, 1200)

        img = Image.open(tmp_path).convert("RGB")
        iw, ih = img.size

        # Decide orientation: rotate if portrait image on landscape display
        if ih > iw and w > h:
            target = (h, w)  # portrait target
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

        # Apply per-display rotation offset (0, 90, 180, 270) from state file
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
        print(f"Displaying {name} ({w}x{h})...")
        display.show()
        print("Done.")

        state["last"] = name
        save_state(state)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
