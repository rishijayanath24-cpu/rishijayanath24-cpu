"""Regenerate the dynamic section of README.md from the GitHub API."""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USER = "rishijayanath24-cpu"
README = "README.md"
START = "<!-- recent:start -->"
END = "<!-- recent:end -->"
LIMIT = 5


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def ago(iso):
    then = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - then).days
    if days < 1:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 31:
        return f"{days} days ago"
    months = days // 30
    return f"{months} month{'s' if months != 1 else ''} ago"


def render():
    repos = api(f"/users/{USER}/repos?type=owner&sort=pushed&per_page=50")
    repos = [r for r in repos if not r["fork"] and r["name"] != USER]
    rows = ["| Repository | Language | Last push |", "|---|---|---|"]
    for r in repos[:LIMIT]:
        lang = r["language"] or "-"
        rows.append(f"| [{r['name']}]({r['html_url']}) | {lang} | {ago(r['pushed_at'])} |")
    return "\n".join(rows)


def main():
    with open(README, encoding="utf-8") as f:
        text = f.read()
    block = f"{START}\n{render()}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)


if __name__ == "__main__":
    main()
