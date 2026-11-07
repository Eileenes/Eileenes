#!/usr/bin/env python3
"""Generate the neofetch-style GitHub profile card (dark + light variants).

Reads live data from the public GitHub API so the numbers never go stale.
Run by .github/workflows/update-profile-card.yml once a day.

    python3 scripts/generate_profile_card.py

Set GITHUB_TOKEN to raise the API rate limit (the CI job passes the default token).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

USER = "Eileenes"
REPO_ROOT = Path(__file__).resolve().parent.parent
CARD_WIDTH = 960
CARD_HEIGHT = 481

# The portrait is sampled from the saved reference image, not hand-drawn.
# Rebuild it with scripts/generate_avatar_ascii.py when the source changes.
PORTRAIT_PATH = REPO_ROOT / "assets/avatar-ascii.json"

# ---------------------------------------------------------------- theme tokens
THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "art": "#d5d5d5",
        "accent": "#58a6ff",
        "label": "#ffa657",
        "dots": "#484f58",
        "value": "#c9d1d9",
        "muted": "#8b949e",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "art": "#3f3f3f",
        "accent": "#0969da",
        "label": "#953800",
        "dots": "#afb8c1",
        "value": "#24292f",
        "muted": "#57606a",
    },
}

# Geometry, tuned against the original hand-written card.
ART_X = 32
ART_TOP = 52
ART_WIDTH = 360
ART_HEIGHT = 360
COL_X = 415
ROW_Y0 = 50
ROW_DY = 21

SINGLE_FIELD_WIDTH = 32   # label + dots + gap, in monospace characters
PAIRED_FIELD_WIDTH = 18   # each half of a two-column stats row
PAIRED_VALUE_WIDTH = 3    # pad numbers so both stats rows line up


# ---------------------------------------------------------------- data fetching
def github_api(path: str):
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "eileenes-profile-card",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_stats() -> dict:
    user = github_api(f"/users/{USER}")

    repos, page = [], 1
    while True:
        batch = github_api(f"/users/{USER}/repos?per_page=100&page={page}")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    # The commit search index is capped, but it is the only public endpoint that
    # reports a user-wide commit total. `is:public` is pinned on purpose: without
    # it an authenticated run also counts commits in private repos (578 vs 232),
    # which is a number nobody can verify. The card only advertises what is
    # publicly visible.
    try:
        commits = github_api(
            f"/search/commits?q=author:{USER}+is:public&per_page=1"
        )["total_count"]
    except urllib.error.HTTPError:
        commits = None

    return {
        "repos": user["public_repos"],
        "stars": stars,
        "followers": user["followers"],
        "commits": commits,
    }


# ---------------------------------------------------------------- rendering
def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def single_row(y: int, label: str, value: str, theme: dict) -> str:
    """`Label: ......... value` — dots auto-padded so every value starts at the
    same column."""
    prefix = f"{label}: "
    dots = "." * max(SINGLE_FIELD_WIDTH - len(prefix) - 1, 1)
    return (
        f'  <text x="{COL_X}" y="{y}" xml:space="preserve">'
        f'<tspan fill="{theme["label"]}">{esc(prefix)}</tspan>'
        f'<tspan fill="{theme["dots"]}">{dots} </tspan>'
        f'<tspan fill="{theme["value"]}">{esc(value)}</tspan>'
        f"</text>"
    )


def pair_row(y: int, left: tuple, right: tuple, theme: dict) -> str:
    """`Repos: ..... 12  | Stars: ..... 32` — both halves use the same character
    budget, and the numbers are right-padded so the two stats rows align."""
    parts = []
    for label, value in (left, right):
        prefix = f"{label}: "
        dots = "." * max(PAIRED_FIELD_WIDTH - len(prefix) - 1, 1)
        padded = f"{value:<{PAIRED_VALUE_WIDTH}}"
        parts.append(
            f'<tspan fill="{theme["label"]}">{esc(prefix)}</tspan>'
            f'<tspan fill="{theme["dots"]}">{dots} </tspan>'
            f'<tspan fill="{theme["value"]}">{esc(padded)}</tspan>'
        )
    return (
        f'  <text x="{COL_X}" y="{y}" xml:space="preserve">'
        + f'<tspan fill="{theme["dots"]}"> | </tspan>'.join(parts)
        + "</text>"
    )


def section_row(y: int, title: str, theme: dict, rule_width: int) -> str:
    return (
        f'  <text x="{COL_X}" y="{y}" xml:space="preserve">'
        f'<tspan fill="{theme["accent"]}">─ {esc(title)} </tspan>'
        f'<tspan fill="{theme["dots"]}">{"─" * rule_width}</tspan>'
        f"</text>"
    )


def render_portrait(theme_name: str) -> str:
    portrait = json.loads(PORTRAIT_PATH.read_text(encoding="utf-8"))
    theme = portrait["themes"][theme_name]
    cell_width = ART_WIDTH / portrait["columns"]
    cell_height = ART_HEIGHT / portrait["rows"]
    pieces = [
        f'  <g id="ascii-avatar" fill="{THEMES[theme_name]["art"]}" '
        'font-size="6px" font-weight="700" '
        'xml:space="preserve">',
        '    <title>ASCII portrait sampled from Eileenes’s avatar</title>',
        '    <desc>Monochrome portrait with wavy hair, glasses and a striped shirt, '
        'with a panda on the left and a pepper on the right. '
        'Made entirely of ASCII text, on a 100 by 60 grid.</desc>',
    ]
    for row, line in enumerate(theme["characters"]):
        y = ART_TOP + row * cell_height + cell_height * .85
        # Place each nonblank run explicitly: SVG viewers may trim whitespace.
        for match in re.finditer(r"\S+", line):
            text = match.group()
            x = ART_X + match.start() * cell_width
            pieces.append(
                f'    <text x="{x:.1f}" y="{y:.1f}" '
                f'textLength="{len(text) * cell_width:.1f}" '
                f'lengthAdjust="spacingAndGlyphs">{esc(text)}</text>'
            )
    pieces.append("  </g>")
    return "\n".join(pieces)


def render(theme_name: str, stats: dict) -> str:
    theme = THEMES[theme_name]
    commits = stats["commits"]
    commits_text = "n/a" if commits is None else str(commits)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" '
        f'height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" '
        f'font-family="Consolas, Menlo, monospace" font-size="13px">',
        f'  <rect x="0.5" y="0.5" width="{CARD_WIDTH - 1}" '
        f'height="{CARD_HEIGHT - 1}" rx="10" fill="{theme["bg"]}" '
        f'stroke="{theme["border"]}"/>',
    ]

    lines.append(render_portrait(theme_name))

    lines.append(
        section_row(ROW_Y0, f"{USER}@github", theme, 54)
    )

    y = ROW_Y0 + 2 * ROW_DY
    for label, value in [
        ("OS", "macOS · Apple Silicon"),
        ("Uptime", "since Aug 2025"),
        ("Host", f"{USER} · Independent Maker"),
        ("Kernel", "10-year Product Manager"),
        ("IDE", "VSCode, Codex, Pi, WorkBuddy"),
    ]:
        lines.append(single_row(y, label, value, theme))
        y += ROW_DY

    y += ROW_DY
    for label, value in [
        ("Languages.Programming", "TypeScript, Python, Go, React"),
        ("Languages.Real", "中文 (Chinese), English"),
        ("Hobbies", "Music · Building · Travel"),
    ]:
        lines.append(single_row(y, label, value, theme))
        y += ROW_DY

    y += ROW_DY
    lines.append(section_row(y, "Contact", theme, 62))
    y += ROW_DY
    lines.append(single_row(y, "Email", "taoyeyeah@gmail.com", theme))
    y += ROW_DY
    lines.append(single_row(y, "GitHub", f"github.com/{USER}", theme))
    y += ROW_DY
    lines.append(single_row(y, "X", "x.com/Eileeness160708", theme))

    y += 2 * ROW_DY
    lines.append(section_row(y, "GitHub Stats", theme, 57))
    y += ROW_DY
    lines.append(
        pair_row(y, ("Repos", stats["repos"]), ("Stars", stats["stars"]), theme)
    )
    y += ROW_DY
    lines.append(
        pair_row(
            y,
            ("Commits", commits_text),
            ("Followers", stats["followers"]),
            theme,
        )
    )

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> int:
    stats = collect_stats()
    print(f"stats: {stats}", file=sys.stderr)
    for theme_name in THEMES:
        path = REPO_ROOT / f"{theme_name}_mode.svg"
        path.write_text(render(theme_name, stats), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
