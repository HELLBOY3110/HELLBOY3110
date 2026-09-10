#!/usr/bin/env python3
"""Add a GitHub-style month timeline and legend to Platane/snk SVGs."""

import re
import sys
from datetime import date, timedelta
from pathlib import Path


def month_columns(today):
    # snk renders 53 Sunday-based contribution weeks, matching GitHub's grid.
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    labels = []
    previous_x = -100
    for column in range(53):
        week = start + timedelta(days=column * 7)
        if week.day <= 7:
            x = column * 16
            if x - previous_x >= 42:
                labels.append((x, week.strftime("%b").upper()))
                previous_x = x
    return labels


def decorate(path):
    svg = path.read_text(encoding="utf-8")
    if "snake-timeline" in svg:
        return

    dark = "dark" in path.stem
    text = "#8b949e" if dark else "#57606a"
    muted = "#30363d" if dark else "#d0d7de"
    # Reserve a footer band below snk's animation path for the legend.
    svg = re.sub(
        r'viewBox="(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"',
        lambda match: f'viewBox="{match.group(1)} {match.group(2)} {match.group(3)} {float(match.group(4)) + 40:g}"',
        svg,
        count=1,
    )
    svg = re.sub(
        r'height="(\d+(?:\.\d+)?)"',
        lambda match: f'height="{float(match.group(1)) + 40:g}"',
        svg,
        count=1,
    )
    labels = "".join(
        f'<text x="{x}" y="-17">{label}</text>'
        for x, label in month_columns(date.today())
    )
    overlay = f'''<g id="snake-timeline" font-family="Consolas,Monaco,monospace" font-size="10" fill="{text}" letter-spacing="0.7">
  {labels}
  <line x1="0" y1="-10" x2="848" y2="-10" stroke="{muted}" stroke-width="1" opacity="0.8"/>
  <line x1="0" y1="168" x2="848" y2="168" stroke="{muted}" stroke-width="1" opacity="0.55"/>
  <text x="0" y="190" fill="#ff3344">LESS</text>
  <rect x="38" y="181" width="10" height="10" rx="2" fill="{muted}"/>
  <rect x="53" y="181" width="10" height="10" rx="2" fill="#003b10"/>
  <rect x="68" y="181" width="10" height="10" rx="2" fill="#007a21"/>
  <rect x="83" y="181" width="10" height="10" rx="2" fill="#00bd33"/>
  <rect x="98" y="181" width="10" height="10" rx="2" fill="#00ff41"/>
  <text x="115" y="190" fill="#00ff41">MORE</text>
  <text x="848" y="190" text-anchor="end">CONTRIBUTION TIMELINE // LIVE</text>
</g>'''
    svg = re.sub(r"</svg>\s*$", overlay + "\n</svg>\n", svg)
    path.write_text(svg, encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: decorate_snake.py SVG [SVG ...]")
    for filename in sys.argv[1:]:
        decorate(Path(filename))


if __name__ == "__main__":
    main()
