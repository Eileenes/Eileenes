#!/usr/bin/env python3
"""Generate the animated "skill talent tree" card (dark + light variants).

Static content: edit SKILLS below and re-run to regenerate both SVGs.

    python3 scripts/generate_skill_tree.py

Motion constraints
------------------
GitHub serves this SVG through its image proxy and the README embeds it with
`<img>`. That puts the document in SVG "secure animated" mode:

  * scripts are disabled        -> no JS-driven motion
  * pointer events never fire   -> no :hover / :active
  * external assets are blocked -> no web fonts, no external CSS

So every animation here is declarative, self-contained and auto-playing:
CSS `@keyframes` in an internal <style>, plus geometry that is already correct
without any animation at all (each animated property's resting value is the
final state). If a viewer ignores the <style> block or prefers reduced motion,
the card still renders exactly as designed — just still.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CARD_W = 960
CARD_H = 500
PAD = 24
COL_W = 216
COL_GAP = 16
COL_X = [PAD + i * (COL_W + COL_GAP) for i in range(4)]

SPINE_DX = 9          # spine sits near the left edge of each column
NODE_DX = 26          # node card is indented from the spine
NODE_W = 190
NODE_H = 52
NODE_Y0 = 168
NODE_PITCH = 60

SANS = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', "
    "'Hiragino Sans GB', 'Microsoft YaHei', sans-serif"
)
MONO = "Consolas, Menlo, monospace"

# ---------------------------------------------------------------- content
# level: 1-10, or "MAX" (=10, rendered in gold)
# low:   explicitly flagged as the branch's embarrassing skill (rendered red)
BRANCHES = [
    {
        "key": "product",
        "name": "产品",
        "en": "PRODUCT",
        "note": "主职 · 10 年",
        "skills": [
            ("需求洞察", 9),
            ("PRD 写作", 9),
            ("原型绘制", 8),
            ("数据说话", 7),
            ("忍住不改需求", 2, "low"),
        ],
    },
    {
        "key": "dev",
        "name": "开发",
        "en": "DEV",
        "note": "副职 · 靠 AI 硬啃",
        "skills": [
            ("Vibe Coding", 9),
            ("复制粘贴", 9),
            ("读报错信息", 6),
            ("手写正则", 1, "low"),
            ("凌晨三点提交", "MAX"),
        ],
    },
    {
        "key": "music",
        "name": "音乐",
        "en": "MUSIC",
        "note": "被动天赋 · 已点满",
        "skills": [
            ("Suno 炼丹", 9),
            ("3 秒听辨", "MAX"),
            ("单曲循环 40 遍", "MAX"),
            ("耳机玄学", 8),
            ("唱歌不跑调", 3, "low"),
        ],
    },
    {
        "key": "game",
        "name": "游戏",
        "en": "GAME",
        "note": "隐藏天赋 · 慎点",
        "skills": [
            ("开新坑", "MAX"),
            ("剧情考据", 9),
            ("改键位强迫症", 7),
            ("「最后一把」", "MAX"),
            ("通关闭坑率", 4, "low"),
        ],
    },
]

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "panel": "#161b22",
        "node": "#161b22",
        "node_border": "#30363d",
        "title": "#e6edf3",
        "body": "#c9d1d9",
        "muted": "#8b949e",
        "faint": "#6e7681",
        "spine": "#30363d",
        "track": "#21262d",
        "gold": "#d29922",
        "red": "#f85149",
        "accent": {
            "product": "#2f81f7",
            "dev": "#a371f7",
            "music": "#3fb950",
            "game": "#db6d28",
        },
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "panel": "#f6f8fa",
        "node": "#ffffff",
        "node_border": "#d0d7de",
        "title": "#24292f",
        "body": "#24292f",
        "muted": "#57606a",
        "faint": "#8c959f",
        "spine": "#d0d7de",
        "track": "#eaeef2",
        "gold": "#9a6700",
        "red": "#cf222e",
        "accent": {
            "product": "#0969da",
            "dev": "#8250df",
            "music": "#1a7f37",
            "game": "#bc4c00",
        },
    },
}

# ---------------------------------------------------------------- motion
# Timing budget: the last node starts at ~0.74s, its bar at ~0.86s, and the bar
# takes 0.75s -> the intro is fully settled by ~1.7s.
STYLE = """
    .enter { animation: enter .5s cubic-bezier(.22,1,.36,1) both; }
    @keyframes enter {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .bar {
      transform-box: fill-box;
      transform-origin: left center;
      animation: grow .75s cubic-bezier(.22,1,.36,1) both;
    }
    @keyframes grow {
      from { transform: scaleX(0); }
      to   { transform: scaleX(1); }
    }

    .spineflow { animation: flow 1.2s linear infinite; }
    @keyframes flow {
      from { stroke-dashoffset: 0; }
      to   { stroke-dashoffset: -28px; }
    }

    .glow {
      animation: glow 2.6s ease-in-out infinite;
      transform-box: fill-box;
    }
    @keyframes glow {
      0%, 100% { stroke-opacity: .45; stroke-width: 1.4; }
      50%      { stroke-opacity: 1;   stroke-width: 2.2; }
    }

    .maxtext { animation: maxtext 2.6s ease-in-out infinite; }
    @keyframes maxtext {
      0%, 100% { opacity: 1; }
      50%      { opacity: .5; }
    }

    /* The embarrassing skills twitch once every few seconds. Nothing happens
       for 82% of the cycle, so it reads as a nervous tic, not as noise. */
    .jitter { animation: jitter 4.4s ease-in-out infinite; }
    @keyframes jitter {
      0%, 82%, 100% { transform: translateX(0); }
      84% { transform: translateX(-2.5px); }
      87% { transform: translateX(2.5px); }
      90% { transform: translateX(-1.8px); }
      93% { transform: translateX(1.4px); }
      96% { transform: translateX(-.6px); }
    }

    .warn { animation: warn 1.9s ease-in-out infinite; }
    @keyframes warn {
      0%, 100% { opacity: 1; }
      50%      { opacity: .3; }
    }

    @media (prefers-reduced-motion: reduce) {
      .enter, .bar, .spineflow, .glow, .maxtext, .jitter, .warn {
        animation: none;
      }
    }
"""


# ---------------------------------------------------------------- helpers
def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def level_value(level) -> int:
    return 10 if level == "MAX" else int(level)


def level_label(level) -> str:
    return "MAX" if level == "MAX" else f"Lv.{level}"


def node(skill, theme: dict, accent: str, cx: int, y: int, delay: float) -> list[str]:
    name, level = skill[0], skill[1]
    flag = skill[2] if len(skill) > 2 else None

    is_max = level == "MAX"
    is_low = flag == "low"

    if is_max:
        bar_color, text_color, frame, frame_cls = (
            theme["gold"], theme["gold"], theme["gold"], ' class="glow"',
        )
    elif is_low:
        bar_color, text_color, frame, frame_cls = (
            theme["red"], theme["red"], theme["node_border"], "",
        )
    else:
        bar_color, text_color, frame, frame_cls = (
            accent, theme["muted"], theme["node_border"], "",
        )

    x0 = cx + NODE_DX
    track_w = NODE_W - 24
    fill_w = round(track_w * level_value(level) / 10, 1)

    level_cls = ' class="maxtext"' if is_max else ""

    inner = [
        f'    <line x1="{cx + SPINE_DX}" y1="{y + NODE_H / 2}" '
        f'x2="{x0}" y2="{y + NODE_H / 2}" stroke="{theme["spine"]}" '
        f'stroke-width="2"/>',
        f'    <circle cx="{cx + SPINE_DX}" cy="{y + NODE_H / 2}" r="3" '
        f'fill="{bar_color}"/>',
        f'    <rect x="{x0}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="8" '
        f'fill="{theme["node"]}" stroke="{frame}" stroke-width="1.4"'
        f"{frame_cls}/>",
        f'    <text x="{x0 + 12}" y="{y + 21}" fill="{theme["body"]}" '
        f'font-family="{SANS}" font-size="12" font-weight="600">'
        f"{esc(name)}</text>",
        f'    <text x="{x0 + NODE_W - 12}" y="{y + 21}" fill="{text_color}" '
        f'font-family="{MONO}" font-size="11" text-anchor="end"'
        f'{level_cls}>{esc(level_label(level))}</text>',
        f'    <rect x="{x0 + 12}" y="{y + 31}" width="{track_w}" height="6" '
        f'rx="3" fill="{theme["track"]}"/>',
        f'    <rect x="{x0 + 12}" y="{y + 31}" width="{fill_w}" height="6" '
        f'rx="3" fill="{bar_color}" class="bar" '
        f'style="animation-delay:{delay + .12:.2f}s"/>',
    ]

    out = [f'  <g class="enter" style="animation-delay:{delay:.2f}s">']
    if is_low:
        # Nested on purpose: the tic and the intro slide both animate
        # `transform`, so they must live on different elements or one wins.
        out.append(
            f'    <g class="jitter" style="animation-delay:{delay + 1.2:.2f}s">'
        )
        out += [line.replace("    ", "      ") for line in inner]
        out.append("    </g>")
    else:
        out += inner
    out.append("  </g>")
    return out


def render(theme_name: str) -> str:
    theme = THEMES[theme_name]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" '
        f'height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" '
        f'font-family="{SANS}" role="img" '
        f'aria-label="Duke Yeah 的技能天赋书：产品 / 开发 / 音乐 / 游戏 四条天赋线">',
        "  <title>Duke Yeah · 技能天赋书 / Skill Talent Tree</title>",
        "  <style>" + STYLE + "  </style>",
        f'  <rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" '
        f'rx="12" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        # nameplate
        f'  <g class="enter">',
        f'    <rect x="20" y="18" width="{CARD_W - 40}" height="58" rx="10" '
        f'fill="{theme["panel"]}" stroke="{theme["border"]}"/>',
        f'    <text x="44" y="46" fill="{theme["title"]}" font-size="16" '
        f'font-weight="700">Duke Yeah · 技能天赋书</text>',
        f'    <text x="44" y="63" fill="{theme["faint"]}" font-size="10.5" '
        f'letter-spacing="0.8">SKILL TALENT TREE</text>',
        f'    <text x="{CARD_W - 44}" y="46" fill="{theme["faint"]}" '
        f'font-family="{MONO}" font-size="11" text-anchor="end">'
        f"v1.0 · patch 2026-10</text>",
        f'    <text x="{CARD_W - 44}" y="63" fill="{theme["faint"]}" '
        f'font-size="10.5" text-anchor="end">4 branches · 20 nodes</text>',
        "  </g>",
        # talent points line
        f'  <g class="enter" style="animation-delay:.06s">',
        f'    <text x="44" y="99" fill="{theme["body"]}" font-size="12">'
        f'天赋点 <tspan font-family="{MONO}" font-weight="700">150</tspan>'
        f' / <tspan font-family="{MONO}">160</tspan> 已投 · 剩余 '
        f'<tspan font-family="{MONO}" font-weight="700">10</tspan> 点</text>',
        f'    <text x="{CARD_W - 44}" y="99" fill="{theme["red"]}" '
        f'font-size="12" text-anchor="end" class="warn" '
        f'style="animation-delay:.5s">'
        f"⚠ 系统建议：补在「手写正则」上，Lv.1 已低于行业下限</text>",
        "  </g>",
    ]

    for col, (branch, cx) in enumerate(zip(BRANCHES, COL_X)):
        accent = theme["accent"][branch["key"]]
        base_delay = 0.12 + col * 0.11

        # branch nameplate
        out += [
            f'  <g class="enter" style="animation-delay:{base_delay - .06:.2f}s">',
            f'    <rect x="{cx + 6}" y="110" width="{COL_W - 6}" height="42" '
            f'rx="8" fill="{accent}" fill-opacity="0.10" stroke="{accent}" '
            f'stroke-opacity="0.45"/>',
            f'    <text x="{cx + 18}" y="130" fill="{accent}" font-size="13" '
            f'font-weight="700">{esc(branch["name"])}'
            f'<tspan fill="{theme["faint"]}" font-family="{MONO}" '
            f'font-size="9.5" font-weight="400">  {branch["en"]}</tspan></text>',
            f'    <text x="{cx + 18}" y="145" fill="{theme["muted"]}" '
            f'font-size="10.5">{esc(branch["note"])}</text>',
            "  </g>",
        ]

        # branch spine: a solid rail plus a flowing dashed overlay in the
        # branch colour, so each line reads as "live"
        last_center = NODE_Y0 + (len(branch["skills"]) - 1) * NODE_PITCH + NODE_H / 2
        spine_geom = (
            f'x1="{cx + SPINE_DX}" y1="152" x2="{cx + SPINE_DX}" '
            f'y2="{last_center}"'
        )
        out += [
            f'  <line {spine_geom} stroke="{theme["spine"]}" stroke-width="2"/>',
            f'  <line {spine_geom} stroke="{accent}" stroke-width="2" '
            f'stroke-linecap="round" stroke-dasharray="2 12" opacity="0.85" '
            f'class="spineflow" '
            f'style="animation-delay:{-col * 0.3:.2f}s"/>',
        ]

        for index, skill in enumerate(branch["skills"]):
            y = NODE_Y0 + index * NODE_PITCH
            delay = base_delay + index * 0.09
            out += node(skill, theme, accent, cx, y, delay)

    out.append(
        f'  <text x="{CARD_W / 2}" y="482" fill="{theme["faint"]}" '
        f'font-size="10" text-anchor="middle">'
        f"* 本天赋书由本人自行评定，不接受外部校准</text>"
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    for theme_name in THEMES:
        path = REPO_ROOT / f"skill_tree_{theme_name}.svg"
        path.write_text(render(theme_name), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
