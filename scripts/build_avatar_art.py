#!/usr/bin/env python3
"""Rebuild scripts/avatar_art.py from the live GitHub avatar.

The header card draws the portrait as a grid of coloured rectangles. That is
the only way to keep it recognisable inside the card's 390px column: the
avatar is a saturated 3D illustration whose identity lives entirely in colour,
and a single-tone glyph ramp throws that away.

    python3 scripts/build_avatar_art.py            # fetch + rewrite
    python3 scripts/build_avatar_art.py --preview  # also dump a PNG

Run this whenever the GitHub avatar changes, then commit the result.
"""

from __future__ import annotations

import argparse
import io
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

USER = "Eileenes"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "scripts" / "avatar_art.py"

# 60 x 30 at 5.0 x 10.0 px per cell fills 300 x 300 px — a circle that sits
# comfortably in the card's 390 px left column without crowding the text panel.
GRID_W, GRID_H = 60, 30
PALETTE_SIZE = 128
# Two hex characters per cell (00..7f) — readable in the generated module and
# wide enough for a 128-entry palette. Two spaces mean "outside the circle".
CELL_W = 2


def fetch_avatar(size: int = 460) -> Image.Image:
    url = f"https://github.com/{USER}.png?size={size}"
    request = urllib.request.Request(url, headers={"User-Agent": "eileenes-profile-card"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return Image.open(io.BytesIO(response.read())).convert("RGB")


def circular_crop(img: Image.Image) -> Image.Image:
    """Square-crop, resize, then blank everything outside the inscribed circle
    so the portrait matches how GitHub displays the avatar."""
    side = min(img.size)
    img = img.crop(((img.width - side) // 2, (img.height - side) // 2,
                    (img.width + side) // 2, (img.height + side) // 2))
    return img.resize((GRID_W, GRID_H), Image.LANCZOS)


def build(img: Image.Image) -> tuple[list[str], list[str]]:
    small = circular_crop(img)
    quantised = small.quantize(colors=PALETTE_SIZE, method=Image.MEDIANCUT,
                               dither=Image.NONE)
    indices = np.asarray(quantised)
    palette = quantised.getpalette()[: PALETTE_SIZE * 3]

    colours = [
        "#%02x%02x%02x" % (palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2])
        for i in range(PALETTE_SIZE)
    ]

    yy, xx = np.mgrid[0:GRID_H, 0:GRID_W]
    inside = np.hypot((xx - (GRID_W - 1) / 2) / (GRID_W / 2),
                      (yy - (GRID_H - 1) / 2) / (GRID_H / 2)) <= 1.0

    rows = []
    for y in range(GRID_H):
        row = "".join(
            f"{indices[y, x]:02x}" if inside[y, x] else "  "
            for x in range(GRID_W)
        )
        rows.append(row)
    return colours, rows


def write_module(colours: list[str], rows: list[str]) -> None:
    body = [
        '"""Pixel data for the header portrait. Generated — do not edit by hand.',
        "",
        "Regenerate with:  python3 scripts/build_avatar_art.py",
        f"Grid: {GRID_W} x {GRID_H}. Each cell is two hex digits = PALETTE index;",
        'two spaces mean "outside the circle, leave the card background showing".',
        '"""',
        "",
        "GRID_W = %d" % GRID_W,
        "GRID_H = %d" % GRID_H,
        "",
        "CELL_W = %d" % CELL_W,
        "",
        "PALETTE = [",
    ]
    for i in range(0, len(colours), 6):
        body.append("    " + " ".join(f'"{c}",' for c in colours[i:i + 6]))
    body.append("]")
    body.append("")
    body.append("ROWS = [")
    body.extend(f'    "{r}",' for r in rows)
    body.append("]")
    OUT.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({len(rows)} rows, {len(colours)} colours)")


def preview(colours: list[str], rows: list[str], out: Path) -> None:
    from PIL import ImageDraw

    cw, ch, fs = 6.0, 11.5, 10
    img = Image.new("RGB", (960, 460), "#0d1117")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 959, 459], 10, fill="#0d1117", outline="#30363d")
    for y, row in enumerate(rows):
        for x in range(GRID_W):
            cell = row[x * CELL_W:(x + 1) * CELL_W]
            if cell.strip() == "":
                continue
            c = colours[int(cell, 16)]
            d.rectangle([25 + x * cw, 40 - fs + y * ch,
                         25 + (x + 1) * cw, 40 - fs + (y + 1) * ch], fill=c)
    img.save(out)
    print(f"preview -> {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--source", help="use a local image instead of the live avatar")
    args = ap.parse_args()

    img = Image.open(args.source).convert("RGB") if args.source else fetch_avatar()
    colours, rows = build(img)
    write_module(colours, rows)
    if args.preview:
        preview(colours, rows, Path("/tmp/avatar_preview.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
