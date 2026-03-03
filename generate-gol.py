#!/usr/bin/env python3
"""Generate a Game of Life cellular automaton image for Inky Impression 4" (640x400, 7-colour)."""

import argparse
import numpy as np
from PIL import Image

WIDTH, HEIGHT = 640, 400

# Inky 7-colour palette (RGB)
PALETTE = {
    'black':  (0, 0, 0),
    'white':  (255, 255, 255),
    'red':    (220, 30, 30),
    'green':  (0, 140, 60),
    'blue':   (0, 60, 180),
    'yellow': (230, 200, 0),
    'orange': (230, 120, 0),
}

# Age -> colour mapping
AGE_THRESHOLDS = [(3, 'red'), (8, 'orange'), (20, 'yellow'), (50, 'green')]

def age_to_colour_array(age_grid):
    """Vectorised age-to-colour mapping returning an RGB image array."""
    h, w = age_grid.shape
    img = np.zeros((h, w, 3), dtype=np.uint8)  # black background
    alive = age_grid > 0
    # Default ancient = blue for all alive
    for ch in range(3):
        img[:, :, ch] = np.where(alive, PALETTE['blue'][ch], 0)
    # Override from highest threshold down
    for threshold, colour_name in reversed(AGE_THRESHOLDS):
        mask = alive & (age_grid <= threshold)
        for ch in range(3):
            img[:, :, ch] = np.where(mask, PALETTE[colour_name][ch], img[:, :, ch])
    return img

def run():
    parser = argparse.ArgumentParser(description='Generate Game of Life e-ink art')
    parser.add_argument('--cell-size', type=int, default=1, help='Pixels per cell (default: 1)')
    parser.add_argument('--generations', type=int, default=120, help='Number of generations')
    parser.add_argument('--density', type=float, default=0.35, help='Initial density')
    parser.add_argument('--output', type=str, default='/tmp/eink-art.png', help='Output path')
    args = parser.parse_args()

    cell_size = args.cell_size
    cols, rows = WIDTH // cell_size, HEIGHT // cell_size

    # Random seed
    grid = (np.random.random((rows, cols)) < args.density).astype(np.int32)
    age = grid.copy()

    for gen in range(args.generations):
        neighbours = sum(
            np.roll(np.roll(grid, dy, axis=0), dx, axis=1)
            for dy in (-1, 0, 1) for dx in (-1, 0, 1)
            if not (dy == 0 and dx == 0)
        )
        new_grid = ((grid == 1) & ((neighbours == 2) | (neighbours == 3)) |
                    (grid == 0) & (neighbours == 3)).astype(np.int32)
        age = np.where(new_grid == 1, age + 1, 0)
        grid = new_grid

    # Render
    rgb = age_to_colour_array(age)
    if cell_size > 1:
        rgb = np.repeat(np.repeat(rgb, cell_size, axis=0), cell_size, axis=1)
    img = Image.fromarray(rgb[:HEIGHT, :WIDTH])
    img.save(args.output)
    print(f"Generated {img.size[0]}x{img.size[1]} image ({cols}x{rows} grid, {cell_size}px cells, {args.generations} gens)")
    print(f"Live cells: {np.count_nonzero(age)}/{rows*cols}")

if __name__ == '__main__':
    run()
