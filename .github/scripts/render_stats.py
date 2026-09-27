"""Render the profile README's stats, languages and activity cards as static SVGs.

The public github-readme-stats instance on Vercel went down, so the cards are
built here from the GitHub GraphQL API and committed to assets/ by the
stats workflow. Standard library only, so the workflow needs no pip install.

Usage: GITHUB_TOKEN=... python .github/scripts/render_stats.py
"""

import json
import os
import urllib.request
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

LOGIN = "Elkhan-Isayev"
OUT_DIR = Path(__file__).resolve().parents[2] / "assets"

# Markup, styling and build glue say little about what a repo is written in.
HIDDEN_LANGUAGES = {"HTML", "CSS", "SCSS", "Shell", "Dockerfile", "Makefile", "GDShader"}
TOP_LANGUAGES = 8

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "title": "#58a6ff",
        "text": "#c9d1d9",
        "muted": "#8b949e",
        "track": "#21262d",
        "bar": "#3fb950",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "title": "#0969da",
        "text": "#1f2328",
        "muted": "#656d76",
        "track": "#eaeef2",
        "bar": "#1a7f37",
    },
}

# Primer octicons, 16px.
ICONS = {
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
    "people": "M2 5.5a3.5 3.5 0 1 1 5.898 2.549 5.508 5.508 0 0 1 3.034 4.084.75.75 0 1 1-1.482.235 4 4 0 0 0-7.9 0 .75.75 0 0 1-1.482-.236A5.507 5.507 0 0 1 3.102 8.05 3.493 3.493 0 0 1 2 5.5ZM11 4a3.001 3.001 0 0 1 2.22 5.018 5.01 5.01 0 0 1 2.56 3.012.749.749 0 0 1-.885.954.752.752 0 0 1-.549-.514 3.507 3.507 0 0 0-2.522-2.372.75.75 0 0 1-.574-.73v-.352a.75.75 0 0 1 .416-.672A1.5 1.5 0 0 0 11 5.5.75.75 0 0 1 11 4Zm-5.5-.5a2 2 0 1 0-.001 3.999A2 2 0 0 0 5.5 3.5Z",
}

WIDTH, HEIGHT = 495, 195
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


def graphql(query, **variables):
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": "bearer " + os.environ["GITHUB_TOKEN"],
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch():
    today = datetime.now(timezone.utc).date()
    # The current month plus the eleven before it.
    first_month = date(today.year - (today.month < 12), today.month % 12 + 1, 1)

    user = graphql(
        """
        query($login: String!, $since: DateTime!) {
          user(login: $login) {
            createdAt
            followers { totalCount }
            pullRequests { totalCount }
            issues { totalCount }
            contributionsCollection(from: $since) {
              contributionCalendar { weeks { contributionDays { date contributionCount } } }
            }
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
              totalCount
              nodes {
                stargazerCount
                languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
                  edges { size node { name color } }
                }
              }
            }
          }
        }
        """,
        login=LOGIN,
        since=first_month.isoformat() + "T00:00:00Z",
    )["user"]

    # contributionsCollection spans at most one year, so ask for each year at once.
    first_year = int(user["createdAt"][:4])
    this_year = datetime.now(timezone.utc).year
    years = "\n".join(
        f'y{year}: contributionsCollection(from: "{year}-01-01T00:00:00Z", to: "{year}-12-31T23:59:59Z")'
        " { totalCommitContributions restrictedContributionsCount }"
        for year in range(first_year, this_year + 1)
    )
    collections = graphql(
        f"query($login: String!) {{ user(login: $login) {{ {years} }} }}", login=LOGIN
    )["user"]

    repos = user["repositories"]["nodes"]
    languages = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in HIDDEN_LANGUAGES:
                continue
            entry = languages.setdefault(name, {"size": 0, "color": edge["node"]["color"] or "#8b949e"})
            entry["size"] += edge["size"]

    # The calendar pads its last week with future days, hence the upper bound.
    months = {}
    for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            day_date = date.fromisoformat(day["date"])
            if first_month <= day_date <= today:
                month = day_date.replace(day=1)
                months[month] = months.get(month, 0) + day["contributionCount"]

    return {
        "stars": sum(repo["stargazerCount"] for repo in repos),
        "commits": sum(
            c["totalCommitContributions"] + c["restrictedContributionsCount"]
            for c in collections.values()
        ),
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "repos": user["repositories"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "months": sorted(months.items()),
        "languages": sorted(languages.items(), key=lambda item: -item[1]["size"]),
    }


def card(theme, title, body):
    t = THEMES[theme]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
  text {{ font-family: {FONT}; }}
  .title {{ font-size: 18px; font-weight: 600; fill: {t["title"]}; }}
  .label {{ font-size: 14px; fill: {t["text"]}; }}
  .value {{ font-size: 14px; font-weight: 700; fill: {t["text"]}; }}
  .muted {{ font-size: 12px; fill: {t["muted"]}; }}
  .icon {{ fill: {t["muted"]}; }}
</style>
<rect x="0.5" y="0.5" rx="6" width="{WIDTH - 1}" height="{HEIGHT - 1}" fill="{t["bg"]}" stroke="{t["border"]}"/>
<text x="25" y="38" class="title">{escape(title)}</text>
{body}
</svg>
"""


def stats_card(stats, theme):
    rows = [
        ("star", "Total stars earned", stats["stars"]),
        ("commit", "Total commits", stats["commits"]),
        ("pr", "Pull requests", stats["prs"]),
        ("issue", "Issues opened", stats["issues"]),
        ("repo", "Public repositories", stats["repos"]),
        ("people", "Followers", stats["followers"]),
    ]
    body = []
    for i, (icon, label, value) in enumerate(rows):
        y = 70 + i * 22
        body.append(
            f'<g transform="translate(25,{y - 12})"><path class="icon" d="{ICONS[icon]}"/></g>'
            f'<text x="50" y="{y}" class="label">{escape(label)}:</text>'
            f'<text x="{WIDTH - 25}" y="{y}" class="value" text-anchor="end">{value:,}</text>'
        )
    return card(theme, "GitHub Stats", "\n".join(body))


def languages_card(stats, theme):
    top = stats["languages"][:TOP_LANGUAGES]
    total = sum(entry["size"] for _, entry in top) or 1
    bar_x, bar_width = 25, WIDTH - 50

    body = [
        f'<clipPath id="bar"><rect x="{bar_x}" y="58" width="{bar_width}" height="8" rx="4"/></clipPath>',
        f'<rect x="{bar_x}" y="58" width="{bar_width}" height="8" rx="4" fill="{THEMES[theme]["track"]}"/>',
        '<g clip-path="url(#bar)">',
    ]
    x = bar_x
    for _, entry in top:
        width = bar_width * entry["size"] / total
        body.append(f'<rect x="{x:.2f}" y="58" width="{width + 0.5:.2f}" height="8" fill="{entry["color"]}"/>')
        x += width
    body.append("</g>")

    column_width = bar_width / 2
    for i, (name, entry) in enumerate(top):
        cx = bar_x + (i % 2) * column_width
        cy = 96 + (i // 2) * 24
        share = 100 * entry["size"] / total
        body.append(
            f'<circle cx="{cx + 5:.1f}" cy="{cy - 4}" r="5" fill="{entry["color"]}"/>'
            f'<text x="{cx + 18:.1f}" y="{cy}" class="label">{escape(name)}</text>'
            f'<text x="{cx + column_width - 20:.1f}" y="{cy}" class="muted" text-anchor="end">{share:.1f}%</text>'
        )
    return card(theme, "Most Used Languages", "\n".join(body))


def activity_card(stats, theme):
    t = THEMES[theme]
    months = stats["months"]
    total = sum(count for _, count in months)
    peak = max((count for _, count in months), default=0) or 1

    left, right, baseline, top = 25, WIDTH - 25, 160, 76
    slot = (right - left) / len(months)
    bar_width = slot - 8
    body = [
        f'<text x="{right}" y="38" class="muted" text-anchor="end">{total:,} in the last 12 months</text>',
        f'<line x1="{left}" y1="{baseline + 0.5}" x2="{right}" y2="{baseline + 0.5}" stroke="{t["track"]}"/>',
    ]
    peak_labelled = False
    for i, (month, count) in enumerate(months):
        x = left + i * slot + 4
        label = f"{month:%b}"
        if count:
            height = max(4, (baseline - top) * count / peak)
            y = baseline - height
            # Rounded top, square foot on the baseline.
            body.append(
                f'<path fill="{t["bar"]}" d="M{x:.1f},{baseline} V{y + 4:.1f} Q{x:.1f},{y:.1f} {x + 4:.1f},{y:.1f}'
                f' H{x + bar_width - 4:.1f} Q{x + bar_width:.1f},{y:.1f} {x + bar_width:.1f},{y + 4:.1f} V{baseline} Z">'
                f"<title>{month:%B %Y}: {count} contributions</title></path>"
            )
            if count == peak and not peak_labelled:
                peak_labelled = True
                body.append(
                    f'<text x="{x + bar_width / 2:.1f}" y="{y - 6:.1f}" class="muted" text-anchor="middle">{count}</text>'
                )
        body.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{baseline + 18}" class="muted" text-anchor="middle">{label}</text>'
        )
    return card(theme, "Contribution Activity", "\n".join(body))


def main():
    stats = fetch()
    OUT_DIR.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT_DIR / f"stats-{theme}.svg").write_text(stats_card(stats, theme))
        (OUT_DIR / f"top-langs-{theme}.svg").write_text(languages_card(stats, theme))
        (OUT_DIR / f"activity-{theme}.svg").write_text(activity_card(stats, theme))
    print(json.dumps({k: v for k, v in stats.items() if k not in ("languages", "months")}))


if __name__ == "__main__":
    main()
