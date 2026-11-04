#!/usr/bin/env python3
"""Rebuild the ASCII portrait from the checked-in GitHub avatar snapshot.

One-time authoring dependency: Pillow (python3 -m pip install Pillow).
The daily profile-card workflow only reads the generated JSON; it needs no
image libraries and never downloads a different avatar behind the user's back.

    python3 scripts/generate_avatar_ascii.py
"""

from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets/avatar-reference.png"
COLS, ROWS = 100, 60  # 3.6 x 6 px cells preserve the square source proportions.
RAMP = " .:-=+*#%@"


def remove_background(image: Image.Image) -> Image.Image:
    """Remove the coral backdrop connected to the top edge.

    This mask is specific to the saved source portrait. Do not seed the
    bottom edge: the orange shirt shares the backdrop's hue and must stay.
    """
    image = image.convert("RGBA")
    width, height = image.size
    pixels = image.load()
    visited = set()
    queue = deque((x, 0) for x in range(width))
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
            continue
        visited.add((x, y))
        r, g, b, _ = pixels[x, y]
        if not (r > 225 and 90 < g < 170 and 55 < b < 155
                and r - g > 75 and g - b > 7):
            continue
        pixels[x, y] = (r, g, b, 0)
        queue.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    return image


def main() -> None:
    small = remove_background(Image.open(SOURCE)).resize(
        (COLS, ROWS), Image.Resampling.LANCZOS
    )
    # Tone is represented only by character density, never by source colors.
    output = {
        "version": 2,
        "mode": "monochrome",
        "source": "avatar-reference.png",
        "source_url": "https://avatars.githubusercontent.com/u/228040956?v=4&s=1024",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "columns": COLS,
        "rows": ROWS,
        "themes": {},
    }
    for theme in ("dark", "light"):
        lines = []
        for y in range(ROWS):
            line = ""
            for x in range(COLS):
                r, g, b, alpha = small.getpixel((x, y))
                if alpha <= 100:
                    line += " "
                    continue
                light = (.2126 * r + .7152 * g + .0722 * b) / 255
                density = (.18 + .82 * light ** .85) if theme == "dark" else (
                    .20 + .80 * (1 - light) ** .80
                )
                line += RAMP[min(len(RAMP) - 1, round(density * (len(RAMP) - 1)))]
            lines.append(line)
        output["themes"][theme] = {"characters": lines}
        (ROOT / f"assets/avatar-ascii-{theme}.txt").write_text(
            "\n".join(line.rstrip() for line in lines) + "\n", encoding="ascii"
        )
    target = ROOT / "assets/avatar-ascii.json"
    target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)} ({COLS} x {ROWS} ASCII cells)")


if __name__ == "__main__":
    main()
