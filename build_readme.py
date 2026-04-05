"""Regenerate the README blog list and pinned repos."""

from __future__ import annotations

import json
import os
import urllib.request
from html import escape
import pathlib
import re

from feedparser import parse

ROOT = pathlib.Path(__file__).parent.resolve()
README_PATH = ROOT / "README.md"
BLOG_FEED_URL = "https://blog.chiloh.com/feed.xml"
POST_LIMIT = 5
TITLE_MAX_LEN = 28
DATE_IN_URL = re.compile(r"\d{4}-\d{2}-\d{2}")
GITHUB_USERNAME = "chilohwei"

LANG_COLORS: dict[str, str] = {
    "JavaScript": "🟡",
    "TypeScript": "🔵",
    "Python": "🔵",
    "HTML": "🔴",
    "CSS": "🟣",
    "Rust": "🟠",
    "Go": "🔵",
    "Shell": "🟢",
}


def replace_chunk(content: str, marker: str, chunk: str) -> str:
    pattern = re.compile(
        rf"<!-- {re.escape(marker)} starts -->.*?<!-- {re.escape(marker)} ends -->",
        re.DOTALL,
    )
    if pattern.search(content) is None:
        raise ValueError(f"README is missing <!-- {marker} starts/ends --> block.")
    replacement = f"<!-- {marker} starts -->\n{chunk}\n<!-- {marker} ends -->"
    return pattern.sub(replacement, content, count=1)


def truncate_title(title: str, max_length: int = TITLE_MAX_LEN) -> str:
    if len(title) <= max_length:
        return title
    return f"{title[: max_length - 3].rstrip()}..."


def date_from_entry_link(link: str) -> str:
    match = DATE_IN_URL.search(link)
    if match is None:
        raise ValueError(f"Entry link has no YYYY-MM-DD segment: {link!r}")
    return match.group(0)


def fetch_blog_entries() -> list[dict[str, str]]:
    feed = parse(BLOG_FEED_URL)
    entries = feed.get("entries") or []
    if not entries:
        raise RuntimeError(f"Empty feed or parse failed: {BLOG_FEED_URL}")

    result: list[dict[str, str]] = []
    for entry in entries:
        title = entry.get("title")
        raw_link = entry.get("link") or ""
        link = raw_link.split("#")[0]
        if not title or not link:
            raise ValueError(f"Incomplete feed entry: title={title!r} link={link!r}")
        result.append(
            {
                "title": truncate_title(title),
                "url": link,
                "published": date_from_entry_link(link),
            }
        )
    print(f"Fetched {len(result)} blog entries.")
    return result


def format_blog_list(entries: list[dict[str, str]]) -> str:
    lines = []
    for entry in entries:
        lines.append(
            '- <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a> - {published}'.format(
                published=entry["published"],
                url=escape(entry["url"], quote=True),
                title=escape(entry["title"]),
            )
        )
    return "\n".join(lines)


def fetch_pinned_repos() -> list[dict[str, str | int | None]]:
    """Fetch pinned repos via GitHub GraphQL API."""
    token = os.environ.get("GITHUB_TOKEN", "")
    query = """
    {
      user(login: "%s") {
        pinnedItems(first: 6, types: REPOSITORY) {
          nodes {
            ... on Repository {
              name
              description
              url
              homepageUrl
              stargazerCount
              forkCount
              primaryLanguage { name }
            }
          }
        }
      }
    }
    """ % GITHUB_USERNAME

    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"bearer {token}"

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    nodes = data["data"]["user"]["pinnedItems"]["nodes"]
    repos: list[dict[str, str | int | None]] = []
    for node in nodes:
        name = node["name"]
        desc = node.get("description") or ""
        repos.append({
            "name": name,
            "description": desc,
            "url": node["url"],
            "homepage": node.get("homepageUrl") or "",
            "stars": node.get("stargazerCount", 0),
            "forks": node.get("forkCount", 0),
            "language": (node.get("primaryLanguage") or {}).get("name", ""),
        })
    print(f"Fetched {len(repos)} pinned repos.")
    return repos


def format_pinned_repos(repos: list[dict[str, str | int | None]]) -> str:
    lines: list[str] = []
    for repo in repos:
        lang = str(repo.get("language") or "")
        emoji = LANG_COLORS.get(lang, "⚪")
        meta: list[str] = []
        if lang:
            meta.append(f"{emoji} {lang}")
        stars = int(repo.get("stars") or 0)
        forks = int(repo.get("forks") or 0)
        if stars:
            meta.append(f"⭐ {stars}")
        if forks:
            meta.append(f"🍴 {forks}")
        suffix = f" · {' · '.join(meta)}" if meta else ""
        name = repo["name"]
        url = repo["url"]
        lines.append(f"- **[{name}]({url})** — {repo['description']}{suffix}")
    return "\n".join(lines)


def main() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    entries = fetch_blog_entries()[:POST_LIMIT]
    text = replace_chunk(text, "blog", format_blog_list(entries))

    repos = fetch_pinned_repos()
    text = replace_chunk(text, "pinned", format_pinned_repos(repos))

    README_PATH.write_text(text, encoding="utf-8", newline="\n")
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
