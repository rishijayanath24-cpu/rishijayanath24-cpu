"""Build the profile card (dark and light SVGs) with live GitHub stats."""
import json
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "rishijayanath24-cpu"
HANDLE = "rishi@jayanath"

WIDTH = 985
ART_X, ART_FONT, ART_LINE_H, ART_CHAR_W = 20, 12, 13.5, 7.0
INFO_X, INFO_FONT, INFO_LINE_H, INFO_CHARS, INFO_CHAR_W = 420, 16, 20, 62, 8.9
TOP = 36

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7c"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", dots="#a0aab4"),
}

# Static profile rows: ("rule", title) | ("kv", key, value) | ("gap",) | ("stats", ...)
PROFILE = [
    ("kv", "OS", "Windows 11"),
    ("kv", "Host", "Karunya Institute of Technology and Sciences"),
    ("kv", "IDE", "VS Code"),
    ("gap",),
    ("kv", "Languages.Programming", "Python, JavaScript, TypeScript"),
    ("kv", "Languages.Computer", "HTML, CSS"),
    ("gap",),
    ("kv", "Interests.Research", "Medical AI, Fairness in ML, LLM/RAG"),
    ("kv", "Interests.Building", "Applied ML, LLM apps, Web apps"),
    ("gap",),
    ("rule", "Contact"),
    ("kv", "GitHub", USER),
    ("gap",),
    ("rule", "GitHub Stats"),
    ("pair", ("Repos", "repos"), ("Stars", "stars")),
    ("pair", ("Commits", "commits"), ("Followers", "followers")),
]


def request(url, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_stats():
    user = request(f"https://api.github.com/users/{USER}")
    repos = request(f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100")
    stats = {
        "repos": str(user["public_repos"]),
        "followers": str(user["followers"]),
        "stars": str(sum(r["stargazers_count"] for r in repos)),
        "commits": "-",
    }
    query = (
        '{ user(login: "%s") { contributionsCollection '
        "{ totalCommitContributions } } }" % USER
    )
    try:
        out = request("https://api.github.com/graphql", json.dumps({"query": query}).encode())
        n = out["data"]["user"]["contributionsCollection"]["totalCommitContributions"]
        stats["commits"] = f"{n:,}"
    except Exception:
        pass
    return stats


def dotted(key, value, width):
    """Return (prefix, dots, value) filling `width` characters."""
    prefix = f". {key}: "
    dots = max(width - len(prefix) - len(value) - 1, 2)
    return prefix, "." * dots + " ", value


def info_lines(stats):
    half = (INFO_CHARS - 3) // 2
    lines = [("rule", HANDLE)]
    for row in PROFILE:
        kind = row[0]
        if kind == "gap":
            lines.append(("gap",))
        elif kind == "rule":
            lines.append(("rule", row[1]))
        elif kind == "kv":
            lines.append(("kv", *dotted(row[1], row[2], INFO_CHARS)))
        elif kind == "pair":
            left = dotted(row[1][0], stats[row[1][1]], half)
            right = dotted(row[2][0], stats[row[2][1]], half)
            lines.append(("pair", left, right))
    return lines


def tspan(text, color):
    return f'<tspan fill="{color}">{escape(text)}</tspan>'


def render_info(lines, theme, y0):
    out = []
    for i, line in enumerate(lines):
        y = y0 + i * INFO_LINE_H
        kind = line[0]
        if kind == "gap":
            continue
        if kind == "rule":
            head = f"- {line[1]} "
            body = head + "-" * (INFO_CHARS - len(head))
            parts = tspan(body, theme["text"])
        elif kind == "kv":
            parts = tspan(line[1], theme["key"]) + tspan(line[2], theme["dots"]) + tspan(line[3], theme["value"])
        else:
            (lp, ld, lv), (rp, rd, rv) = line[1], line[2]
            parts = (
                tspan(lp, theme["key"]) + tspan(ld, theme["dots"]) + tspan(lv, theme["value"])
                + tspan(" | ", theme["text"])
                + tspan(rp, theme["key"]) + tspan(rd, theme["dots"]) + tspan(rv, theme["value"])
            )
        out.append(
            f'<text x="{INFO_X}" y="{y}" font-size="{INFO_FONT}" xml:space="preserve" '
            f'textLength="{INFO_CHARS * INFO_CHAR_W:.0f}" lengthAdjust="spacing">{parts}</text>'
        )
    return out


def render_art(art, theme, y0):
    out = []
    for i, line in enumerate(art):
        if not line.strip():
            continue
        out.append(
            f'<text x="{ART_X}" y="{y0 + i * ART_LINE_H}" font-size="{ART_FONT}" '
            f'fill="{theme["text"]}" xml:space="preserve" '
            f'textLength="{len(line) * ART_CHAR_W:.0f}" lengthAdjust="spacing">{escape(line)}</text>'
        )
    return out


def build(name, theme, art, lines):
    height = max(len(art) * ART_LINE_H, len(lines) * INFO_LINE_H) + TOP * 2
    body = render_art(art, theme, TOP + ART_FONT) + render_info(lines, theme, TOP + INFO_FONT)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="Consolas, \'DejaVu Sans Mono\', '
        f'\'Courier New\', monospace">\n'
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="{theme["bg"]}"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )
    os.makedirs("assets", exist_ok=True)
    with open(os.path.join("assets", f"card-{name}.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)


def load_art(name):
    with open(os.path.join("assets", name), encoding="utf-8") as f:
        return f.read().rstrip("\n").split("\n")


def main():
    arts = {"dark": load_art("ascii.txt"), "light": load_art("ascii-light.txt")}
    lines = info_lines(fetch_stats())
    for name, theme in THEMES.items():
        build(name, theme, arts[name], lines)


if __name__ == "__main__":
    main()
