# petri-dish

Generative art for e-ink displays — Haeckel plates, cellular automata, strange attractors.

## Hardware

- **13.3" Inky Impression** (1600×1200, 7-colour Spectra 6) on Pi Zero 2W (`eink-13-pi-0.local`)
- **4" Inky Impression** (640×400, 7-colour) on Pi Zero 2W (`eink-4-pi-0.local`)

## Scripts

- `display-image.py` — Display any image on an Inky Impression. Auto-detects display size, supports rotation, uses `ImageOps.fit()` for zero wasted space.
- `rotate-art.py` — Cron-driven art rotation. Downloads random Haeckel plates from Wikimedia Commons, quantizes to 7-colour palette with Floyd-Steinberg dithering, displays them. Tracks last shown to avoid repeats.
- `generate-gol.py` — Game of Life pattern generator for e-ink.

## Setup

Each Pi Zero runs `rotate-art.py` via cron every 4 hours:

```
0 */4 * * * /usr/bin/python3 /home/trevor/rotate-art.py >> /tmp/rotate-art.log 2>&1
```

## Dependencies

```bash
sudo apt-get install python3-pip python3-pil python3-numpy python3-spidev python3-smbus2 libopenblas0
pip3 install --break-system-packages inky[rpi]
```
