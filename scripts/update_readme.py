#!/usr/bin/env python3
import os
import re
import json
import urllib.request
from datetime import datetime, timezone

USERNAME = "2228293026"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

# 语言徽章映射（标签, logo）
LANG_BADGE = {
    "C#":         ("Csharp",      "csharp"),
    "C++":        ("C%2B%2B",     "cplusplus"),
    "C":          ("C",           "c"),
    "Java":       ("Java",        "openjdk"),
    "TypeScript": ("TypeScript",  "typescript"),
    "JavaScript": ("JavaScript",  "javascript"),
    "Python":     ("Python",      "python"),
    "Kotlin":     ("Kotlin",      "kotlin"),
    "Rust":       ("Rust",        "rust"),
    "Go":         ("Go",          "go"),
    "Lua":        ("Lua",         "lua"),
    "Shell":      ("Shell",       "gnubash"),
    "Ruby":       ("Ruby",        "ruby"),
    "Swift":      ("Swift",       "swift"),
    "Dart":       ("Dart",        "dart"),
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
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

def build_lang_badges(repos):
    """生成语言徽章（按使用次数排序）"""
    counts = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    lines = []
    for lang in sorted(counts, key=lambda l: -counts[l]):
        if lang in LANG_BADGE:
            label, logo = LANG_BADGE[lang]
            lines.append(f"![{lang}](https://img.shields.io/badge/{label}-c9c8e4.svg?&style=for-the-badge&logo={logo}&logoColor=4200a0)")
        else:
            # 未知语言，只显示名称
            safe_label = lang.replace(" ", "%20").replace("#", "%23").replace("+", "%2B")
            lines.append(f"![{lang}](https://img.shields.io/badge/{safe_label}-c9c8e4.svg?&style=for-the-badge)")
    return "\n".join(lines)

def build_repo_cards(repos):
    """
    生成项目卡片（两列布局），按 star 降序排序，跳过同名仓库。
    使用 github-readme-stats 的 pin 接口。
    """
    # 过滤掉个人主页仓库
    filtered = [r for r in repos if r["name"] != USERNAME]
    # 按 star 数量降序
    sorted_repos = sorted(filtered, key=lambda r: (-r["stargazers_count"], r["name"]))
    
    cards = []
    for repo in sorted_repos:
        name = repo["name"]
        # 描述可能为 None
        description = repo.get("description") or ""
        # 转义 & 等字符
        desc_encoded = description.replace("&", "&amp;").replace("#", "%23")
        # 卡片链接参数
        base_url = "https://github-readme-stats.vercel.app/api/pin/"
        params = (
            f"?username={USERNAME}&repo={name}"
            f"&theme=midnight-purple&hide_border=true"
            f"&bg_color=0d0d18&title_color=c084fc&icon_color=a78bfa&text_color=e2d9f3"
            f"&description={desc_encoded}"
        )
        card_img = f"{base_url}{params}"
        # 使用 Markdown 图片链接，点击跳转到仓库
        cards.append(f'<a href="{repo["html_url"]}"><img src="{card_img}" width="49%" /></a>')
    
    # 将卡片分成两列：每两个一组，放在同一行
    lines = []
    for i in range(0, len(cards), 2):
        row = cards[i:i+2]
        lines.append('<div align="center">')
        lines.append("  " + "  ".join(row))
        lines.append('</div>')
    return "\n".join(lines)

def inject(content, marker, replacement):
    """替换两个标记之间的内容"""
    pattern = rf"(<!-- {marker}_START -->).*?(<!-- {marker}_END -->)"
    return re.sub(pattern, rf"\1\n{replacement}\n\2", content, flags=re.DOTALL)

def main():
    print(f"Fetching repos for {USERNAME}...")
    repos = fetch_all_repos()
    print(f"  Found {len(repos)} repos.")

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    content = inject(content, "LANG_BADGES", build_lang_badges(repos))
    content = inject(content, "REPO_CARDS", build_repo_cards(repos))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = content.replace("<!-- LAST_UPDATED -->", now)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Done. Updated at {now}.")

if __name__ == "__main__":
    main()
