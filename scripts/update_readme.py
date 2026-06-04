#!/usr/bin/env python3
"""
update_readme.py
Fetches all public repos for USERNAME via GitHub API,
sorts by stargazers, injects a Markdown table and language badges into README.md.
"""

import os
import re
import json
import urllib.request
from datetime import datetime, timezone

USERNAME = "2228293026"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

# Map GitHub language names → shields.io badge params
LANG_BADGE = {
    "C#":         ("C%23",       "239120", "csharp"),
    "C++":        ("C%2B%2B",    "00599C", "cplusplus"),
    "Java":       ("Java",       "ED8B00", "openjdk"),
    "Python":     ("Python",     "3776AB", "python"),
    "JavaScript": ("JavaScript", "F7DF1E", "javascript"),
    "TypeScript": ("TypeScript", "3178C6", "typescript"),
    "Kotlin":     ("Kotlin",     "7F52FF", "kotlin"),
    "Rust":       ("Rust",       "000000", "rust"),
    "Go":         ("Go",         "00ADD8", "go"),
    "Ruby":       ("Ruby",       "CC342D", "ruby"),
    "Swift":      ("Swift",      "FA7343", "swift"),
    "Dart":       ("Dart",       "0175C2", "dart"),
    "Lua":        ("Lua",        "2C2D72", "lua"),
    "Shell":      ("Shell",      "4EAA25", "gnubash"),
}

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "readme-updater",
}

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"Bearer {token}"


def gh_get(url: str) -> list | dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_all_repos() -> list[dict]:
    repos, page = [], 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=public"
        )
        batch = gh_get(url)
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def build_repo_table(repos: list[dict]) -> str:
    # Sort by stars desc, then name asc
    sorted_repos = sorted(repos, key=lambda r: (-r["stargazers_count"], r["name"]))

    lines = [
        "| Repository | Description | Language | Stars | Forks |",
        "|:-----------|:------------|:--------:|:-----:|:-----:|",
    ]
    for r in sorted_repos:
        name     = r["name"]
        url      = r["html_url"]
        desc     = (r["description"] or "—").replace("|", "\\|")
        lang     = r["language"] or "—"
        stars    = r["stargazers_count"]
        forks    = r["forks_count"]
        archived = " *(archived)*" if r.get("archived") else ""
        lines.append(
            f"| [{name}]({url}){archived} | {desc} | `{lang}` | ⭐ {stars} | 🍴 {forks} |"
        )
    return "\n".join(lines)


def build_lang_badges(repos: list[dict]) -> str:
    # Count bytes per language across all repos that expose it
    lang_counts: dict[str, int] = {}
    for r in repos:
        if r.get("language"):
            lang_counts[r["language"]] = lang_counts.get(r["language"], 0) + 1

    # Sort by frequency
    sorted_langs = sorted(lang_counts, key=lambda l: -lang_counts[l])

    badges = []
    for lang in sorted_langs:
        if lang in LANG_BADGE:
            label, color, logo = LANG_BADGE[lang]
            badge = (
                f"![{lang}](https://img.shields.io/badge/{label}-{color}"
                f"?style=for-the-badge&logo={logo}&logoColor=white)"
            )
        else:
            # Fallback: plain badge without logo
            label = lang.replace(" ", "%20").replace("#", "%23").replace("+", "%2B")
            badge = (
                f"![{lang}](https://img.shields.io/badge/{label}-555555"
                f"?style=for-the-badge)"
            )
        badges.append(badge)

    return "\n".join(
        ["<div align=\"center\">", ""]
        + badges
        + ["", "</div>"]
    )


def inject(content: str, marker: str, replacement: str) -> str:
    pattern = rf"(<!-- {marker}_START -->).*?(<!-- {marker}_END -->)"
    repl = rf"\1\n{replacement}\n\2"
    return re.sub(pattern, repl, content, flags=re.DOTALL)


def main():
    print(f"Fetching repos for {USERNAME}...")
    repos = fetch_all_repos()
    print(f"  {len(repos)} public repos found.")

    table  = build_repo_table(repos)
    badges = build_lang_badges(repos)
    now    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = inject(content, "REPO_TABLE",    table)
    content = inject(content, "LANG_BADGES",   badges)
    content = content.replace("<!-- LAST_UPDATED -->", now)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  README updated at {now}.")


if __name__ == "__main__":
    main()
