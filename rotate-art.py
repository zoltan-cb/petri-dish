#!/usr/bin/env python3
"""Rotate Haeckel art on Inky Impression e-ink displays.

Auto-detects display dimensions via inky.auto. Downloads a random plate
from a curated list, avoiding the last shown. Quantizes to 7-colour palette
with Floyd-Steinberg dithering.

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

# Curated Haeckel plates from Wikimedia Commons — high-res scans
PLATES = [
    ("Haeckel_Siphonophorae", "https://upload.wikimedia.org/wikipedia/commons/c/cb/Haeckel_Siphonophorae_7.jpg"),
    ("Haeckel_Trochilidae", "https://upload.wikimedia.org/wikipedia/commons/8/8e/Haeckel_Trochilidae.jpg"),
    ("Haeckel_Chelonia", "https://upload.wikimedia.org/wikipedia/commons/a/a6/Haeckel_Chelonia.jpg"),
    ("Haeckel_Discomedusae_8", "https://upload.wikimedia.org/wikipedia/commons/d/de/Haeckel_Discomedusae_8.jpg"),
    ("Haeckel_Actiniae", "https://upload.wikimedia.org/wikipedia/commons/a/a9/Haeckel_Actiniae.jpg"),
    ("Haeckel_Orchidae", "https://upload.wikimedia.org/wikipedia/commons/2/21/Haeckel_Orchidae.jpg"),
    ("Haeckel_Filicinae", "https://upload.wikimedia.org/wikipedia/commons/4/42/Haeckel_Filicinae.jpg"),
    ("Haeckel_Muscinae", "https://upload.wikimedia.org/wikipedia/commons/e/ee/Haeckel_Muscinae.jpg"),
    ("Haeckel_Anthomedusae", "https://upload.wikimedia.org/wikipedia/commons/a/a1/Haeckel_Anthomedusae.jpg"),
    ("Haeckel_Chaetopoda", "https://upload.wikimedia.org/wikipedia/commons/4/4d/Haeckel_Chaetopoda.jpg"),
    ("Haeckel_Lacertilia", "https://upload.wikimedia.org/wikipedia/commons/7/7a/Haeckel_Lacertilia.jpg"),
    ("Haeckel_Nepenthaceae", "https://upload.wikimedia.org/wikipedia/commons/7/74/Haeckel_Nepenthaceae.jpg"),
    ("Haeckel_Chiroptera", "https://upload.wikimedia.org/wikipedia/commons/f/fd/Haeckel_Chiroptera.jpg"),
    ("Haeckel_Nudibranchia", "https://upload.wikimedia.org/wikipedia/commons/e/ea/Haeckel_Nudibranchia.jpg"),
    ("Haeckel_Batrachia", "https://upload.wikimedia.org/wikipedia/commons/a/af/Haeckel_Batrachia.jpg"),
    ("Haeckel_Arachnida", "https://upload.wikimedia.org/wikipedia/commons/c/ca/Haeckel_Arachnida.jpg"),
    ("Haeckel_Stephoidea", "https://upload.wikimedia.org/wikipedia/commons/6/6e/Haeckel_Stephoidea.jpg"),
    ("Haeckel_Ascidiae", "https://upload.wikimedia.org/wikipedia/commons/2/22/Haeckel_Ascidiae.jpg"),
    ("Haeckel_Coniferae", "https://upload.wikimedia.org/wikipedia/commons/1/1a/Haeckel_Coniferae.jpg"),
    ("Haeckel_Decapoda", "https://upload.wikimedia.org/wikipedia/commons/4/44/Haeckel_Decapoda.jpg"),
]


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last": None}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def pick_plate(state):
    last = state.get("last")
    candidates = [p for p in PLATES if p[0] != last]
    if not candidates:
        candidates = PLATES
    return random.choice(candidates)


def main():
    state = load_state()
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

        # Decide orientation: use rotation if portrait image on landscape display
        # would waste too much space
        landscape_fit = ImageOps.fit(img, (w, h), method=Image.LANCZOS)
        portrait_fit = ImageOps.fit(img, (h, w), method=Image.LANCZOS)

        # Use portrait (rotated) if the image is taller than wide and display is landscape
        if ih > iw and w > h:
            img = portrait_fit.rotate(90, expand=True)
        else:
            img = landscape_fit

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
