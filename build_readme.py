"""Regenerate the README blog list from blog.chiloh.com RSS."""

from __future__ import annotations

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


def main() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    entries = fetch_blog_entries()[:POST_LIMIT]
    block = format_blog_list(entries)
    README_PATH.write_text(replace_chunk(text, "blog", block), encoding="utf-8", newline="\n")
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
