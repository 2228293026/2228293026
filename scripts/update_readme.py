#!/usr/bin/env python3
import os, re, json, urllib.request
from datetime import datetime, timezone

USERNAME = "2228293026"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

LANG_BADGE = {
    "C#":         ("C%23",       "239120", "csharp"),
    "C++":        ("C%2B%2B",    "00599C", "cplusplus"),
    "C":          ("C",          "A8B9CC", "c"),
    "Java":       ("Java",       "ED8B00", "openjdk"),
    "TypeScript": ("TypeScript", "3178C6", "typescript"),
    "JavaScript": ("JavaScript", "F7DF1E", "javascript"),
    "Python":     ("Python",     "3776AB", "python"),
    "Kotlin":     ("Kotlin",     "7F52FF", "kotlin"),
    "Rust":       ("Rust",       "CE422B", "rust"),
    "Go":         ("Go",         "00ADD8", "go"),
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

def gh_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def fetch_all_repos():
    repos, page = [], 1
    while True:
        batch = gh_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&type=public")
        if not batch: break
        repos.extend(batch)
        page += 1
    return repos

def build_lang_badges(repos):
    counts = {}
    for r in repos:
        if r.get("language"):
            counts[r["language"]] = counts.get(r["language"], 0) + 1
    lines = []
    for lang in sorted(counts, key=lambda l: -counts[l]):
        if lang in LANG_BADGE:
            label, color, logo = LANG_BADGE[lang]
            lines.append(f"![{lang}](https://img.shields.io/badge/{label}-{color}?style=for-the-badge&logo={logo}&logoColor=white)")
        else:
            label = lang.replace(" ", "%20").replace("#", "%23").replace("+", "%2B")
            lines.append(f"![{lang}](https://img.shields.io/badge/{label}-555555?style=for-the-badge)")
    return "\n".join(lines)

def build_repo_badges(repos):
    sorted_repos = sorted(repos, key=lambda r: (-r["stargazers_count"], r["name"]))
    sorted_repos = [r for r in sorted_repos if r["name"] != USERNAME]
    lines = []
    for r in sorted_repos:
        name  = r["name"]
        url   = r["html_url"]
        stars = r["stargazers_count"]
        # encode name for badge label
        label = name.replace("-", "--").replace("_", "__").replace(" ", "%20")
        badge = f"[![{name}](https://img.shields.io/badge/{label}-⭐%20{stars}-2d1b69?style=for-the-badge&labelColor=1a0533&color=2d1b69)]({url})"
        lines.append(badge)
    return "\n".join(lines)

def inject(content, marker, replacement):
    pattern = rf"(<!-- {marker}_START -->).*?(<!-- {marker}_END -->)"
    return re.sub(pattern, rf"\1\n{replacement}\n\2", content, flags=re.DOTALL)

def main():
    print(f"Fetching repos for {USERNAME}...")
    repos = fetch_all_repos()
    print(f"  {len(repos)} repos found.")

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = inject(content, "LANG_BADGES", build_lang_badges(repos))
    content = inject(content, "REPO_BADGES", build_repo_badges(repos))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = content.replace("<!-- LAST_UPDATED -->", now)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Done. Updated at {now}.")

if __name__ == "__main__":
    main()
