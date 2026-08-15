#!/usr/bin/env python3.11
"""Regenerate the YouTube cover from SVG source of truth.

Rule (do not break):
  rsvg-convert -w 1280 -h 720 thumbnail.svg -o thumbnail.png

Never screenshot, export, Pillow letterbox, or re-scale an existing PNG.
The artwork must be full-bleed 1280x720. See docs/video/youtube/UPLOAD.md.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "video" / "youtube"
SVG = ROOT / "thumbnail.svg"
PNG = ROOT / "thumbnail.png"


def main() -> None:
    if not SVG.is_file():
        sys.exit(f"missing source of truth: {SVG}")
    subprocess.check_call(
        ["rsvg-convert", "-w", "1280", "-h", "720", str(SVG), "-o", str(PNG)]
    )
    # Refuse a letterboxed/wrong-size render silently shipping.
    from PIL import Image

    im = Image.open(PNG)
    if im.size != (1280, 720):
        sys.exit(f"refusing {PNG}: got {im.size}, expected (1280, 720)")
    print(f"wrote {PNG} {im.size[0]}x{im.size[1]} from {SVG.name}")


if __name__ == "__main__":
    main()
