from feedparser import parse
import httpx
import pathlib
import re
import os

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)

def fetch_weekly():
    return httpx.get(
        "https://raw.githubusercontent.com/chilohwei/weekly/main/RECENT.md"
    )

def fetch_blog_entries():
    entries = parse("https://blog.chiloh.cn/feed.xml")["entries"]
    return [
        {
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": entry["published"].split("T")[0],
        }
        for entry in entries
    ]

if __name__ == "__main__":
    readme = root / "README.md"

    # Fetch and update weekly content
    weekly_text = "\n" + fetch_weekly().text
    readme_contents = readme.open().read()
    rewritten = replace_chunk(readme_contents, "weekly", weekly_text)

    # Fetch and update blog entries
    entries = fetch_blog_entries()[:5]
    entries_md = "\n".join(
        ["* <a href='{url}' target='_blank'>{title}</a> - {published}".format(**entry) for entry in entries]
    )
    rewritten = replace_chunk(rewritten, "blog", entries_md)

    # Write back to README.md
    readme.open("w").write(rewritten)
