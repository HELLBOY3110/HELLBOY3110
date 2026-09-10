#!/usr/bin/env python3
"""Render a dependency-free GitHub profile telemetry card."""

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path

USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "HELLBOY3110")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = Path(os.environ.get("TELEMETRY_OUTPUT", "assets/telemetry.svg"))


def graphql(query):
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "profile-telemetry"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)["data"]["user"]


def streaks(days):
    active = {date.fromisoformat(day["date"]) for day in days if day["contributionCount"] > 0}
    today = datetime.now(timezone.utc).date()
    cursor = today if today in active else today - timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= timedelta(days=1)
    longest = run = 0
    for day in sorted(days, key=lambda item: item["date"]):
        run = run + 1 if day["contributionCount"] else 0
        longest = max(longest, run)
    return current, longest


def render(user):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    current, longest = streaks(days)
    repos = user["repositories"]["nodes"]
    stars = sum(repo["stargazerCount"] for repo in repos)
    total = calendar["totalContributions"]
    values = [
        ("CONTRIBUTIONS", total), ("PUBLIC REPOS", user["repositories"]["totalCount"]),
        ("TOTAL STARS", stars), ("CURRENT STREAK", current), ("LONGEST STREAK", longest),
    ]
    cells = []
    recent = days[-84:]
    maximum = max([day["contributionCount"] for day in recent] or [1])
    colors = ["#161b22", "#003b10", "#007a21", "#00bd33", "#00ff41"]
    for index, day in enumerate(recent):
        level = 0 if not day["contributionCount"] else min(4, 1 + int(3 * day["contributionCount"] / maximum))
        x, y = 45 + (index // 7) * 68, 202 + (index % 7) * 16
        cells.append(f'<rect x="{x}" y="{y}" width="56" height="10" rx="2" fill="{colors[level]}"><title>{escape(day["date"])}: {day["contributionCount"]} contributions</title></rect>')
    blocks = []
    for index, (label, value) in enumerate(values):
        x = 35 + index * 226
        blocks.append(f'<g transform="translate({x} 70)"><rect width="205" height="92" rx="8" fill="#090d12" stroke="#21262d"/><text x="18" y="31" fill="#8b949e" font-size="12" letter-spacing="1.4">{label}</text><text x="18" y="70" fill="{("#ff3344" if index in (2, 4) else "#00ff41")}" font-size="30" font-weight="700">{value}</text></g>')
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="350" viewBox="0 0 1200 350" role="img" aria-labelledby="title desc">
<title id="title">Live GitHub telemetry for {escape(USER)}</title><desc id="desc">{total} contributions, {stars} stars, current streak {current} days</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0d1117"/><stop offset="1" stop-color="#080203"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<rect x="1" y="1" width="1198" height="348" rx="12" fill="url(#bg)" stroke="#00ff41" stroke-opacity=".35"/><g font-family="Consolas,Monaco,monospace">
<text x="35" y="38" fill="#00ff41" font-size="16" font-weight="700" filter="url(#glow)">● LIVE OPERATOR TELEMETRY</text><text x="1165" y="38" text-anchor="end" fill="#52606d" font-size="11">UPDATED {stamp}</text>
{''.join(blocks)}<text x="35" y="190" fill="#ff3344" font-size="12" letter-spacing="2">84-DAY CONTRIBUTION SIGNAL</text>{''.join(cells)}
<text x="1165" y="326" text-anchor="end" fill="#52606d" font-size="11">SOURCE: GITHUB GRAPHQL API // SELF-HOSTED RENDER</text></g></svg>'''


def main():
    if not TOKEN:
        sys.exit("GITHUB_TOKEN is required")
    query = '''{ user(login: "%s") { repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount nodes { stargazerCount } } contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }''' % USER
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(graphql(query)), encoding="utf-8")


if __name__ == "__main__":
    main()
