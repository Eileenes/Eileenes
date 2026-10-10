#!/usr/bin/env python3
"""Local-only preview builder: renders README.md the way GitHub would, with the
theme-appropriate SVG inlined so it can be screenshotted with a headless browser.

Not part of the published profile. Run from the repo root:

    python3 scripts/build_preview.py ../preview_light.html ../preview_dark.html
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"

PICTURE_RE = re.compile(
    r"<picture>\s*"
    r'<source media="\(prefers-color-scheme: dark\)" srcset="([^"]+)">\s*'
    r'<source media="\(prefers-color-scheme: light\)" srcset="([^"]+)">\s*'
    r'<img[^>]*>\s*'
    r"</picture>",
    re.DOTALL,
)

CSS = """
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 16px 80px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
               Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  font-size: 16px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
.markdown-body { max-width: 1012px; margin: 0 auto; }
.markdown-body h1, .markdown-body h2 {
  padding-bottom: .3em; border-bottom: 1px solid var(--border);
  font-weight: 600; line-height: 1.25;
}
.markdown-body h2 { font-size: 1.5em; margin: 32px 0 16px; }
.markdown-body hr { height: 4px; margin: 32px 0; border: 0; background: var(--border); }
.markdown-body p, .markdown-body ul { margin: 0 0 16px; }
.markdown-body li { margin: 4px 0; }
.markdown-body a { color: var(--link); text-decoration: none; }
.markdown-body a:hover { text-decoration: underline; }
.markdown-body blockquote {
  margin: 0 0 16px; padding: 0 1em; color: var(--muted);
  border-left: .25em solid var(--border);
}
.markdown-body code {
  padding: .2em .4em; margin: 0; font-size: 85%; border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  background: var(--code-bg);
}
.markdown-body sub { font-size: 12px; color: var(--muted); }
.markdown-body details {
  margin: 8px 0 16px; padding: 8px 12px; border: 1px solid var(--border);
  border-radius: 6px; background: var(--panel);
}
.markdown-body summary { cursor: pointer; font-size: 14px; }
.markdown-body details > p { margin: 12px 0 0; font-size: 14px; color: var(--muted); }
.markdown-body img, .markdown-body svg { max-width: 100%; }
.markdown-body picture, .markdown-body svg { display: block; }
.caption-note {
  font-size: 12px; color: var(--muted); margin: -6px 0 20px;
  font-style: italic; opacity: .85;
}
"""

THEMES = {
    "light": {
        "bg": "#ffffff",
        "fg": "#1f2328",
        "muted": "#59636e",
        "border": "#d1d9e0",
        "link": "#0969da",
        "code-bg": "rgba(129,139,152,0.12)",
        "panel": "#f6f8fa",
    },
    "dark": {
        "bg": "#0d1117",
        "fg": "#f0f6fc",
        "muted": "#9198a1",
        "border": "#3d444d",
        "link": "#4493f8",
        "code-bg": "rgba(101,108,118,0.4)",
        "panel": "#151b23",
    },
}


def inline_svg(file_name: str) -> str:
    svg = (REPO_ROOT / file_name).read_text(encoding="utf-8")
    return svg.replace("<svg ", '<svg style="border-radius:12px" ', 1)


def build(theme_name: str) -> str:
    raw = README.read_text(encoding="utf-8")

    toggle = {"light": 2, "dark": 1}[theme_name]
    cards: list[str] = []

    def stash(match: re.Match) -> str:
        # Pull the SVG out before markdown runs. The ASCII avatar is full of
        # `*` and `_`, which the parser happily turns into <em>/<strong> and
        # wrecks the SVG tree. Placeholder in, real SVG back after.
        cards.append(inline_svg(match.group(toggle)))
        return f"\n\n@@CARD{len(cards) - 1}@@\n\n"

    raw = PICTURE_RE.sub(stash, raw)

    body = markdown.markdown(
        raw,
        extensions=["md_in_html", "tables", "fenced_code", "attr_list"],
    )

    for index, svg in enumerate(cards):
        body = body.replace(f"<p>@@CARD{index}@@</p>", svg)
        body = body.replace(f"@@CARD{index}@@", svg)

    theme = THEMES[theme_name]
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="{theme_name}">
<head>
<meta charset="utf-8">
<title>Eileenes profile · {theme_name} preview</title>
<style>
:root {{
{chr(10).join(f"  --{k}: {v};" for k, v in theme.items())}
}}
html, body {{ background: {theme["bg"]}; color: {theme["fg"]}; }}
{CSS}
</style>
</head>
<body>
<article class="markdown-body">
{body}
</article>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    targets = {
        "light": Path(argv[1]) if len(argv) > 1 else REPO_ROOT.parent / "preview_light.html",
        "dark": Path(argv[2]) if len(argv) > 2 else REPO_ROOT.parent / "preview_dark.html",
    }
    for theme_name, path in targets.items():
        path.write_text(build(theme_name), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
