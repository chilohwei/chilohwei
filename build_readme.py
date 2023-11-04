from feedparser import parse
import httpx
import pathlib
import re

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
    response = httpx.get("https://raw.githubusercontent.com/chilohwei/weekly/main/RECENT.md")
    print("Weekly fetched successfully.")  # Add debug print
    return response

def fetch_blog_entries():
    entries = parse("https://blog.chiloh.cn/feed.xml")["entries"]
    print(f"Fetched {len(entries)} blog entries.")  # Add debug print
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
    with open(readme, 'r') as f:
        readme_contents = f.read()
    rewritten = replace_chunk(readme_contents, "weekly", weekly_text)
    print("Weekly content updated.")  # Add debug print

    # Fetch and update blog entries
    entries = fetch_blog_entries()[:5]
    entries_md = "\n".join(
        ["* <a href='{url}' target='_blank'>{title}</a> - {published}".format(**entry) for entry in entries]
    )
    rewritten = replace_chunk(rewritten, "blog", entries_md)
    print("Blog entries updated.")  # Add debug print

    # Write back to README.md
    with open(readme, 'w') as f:
        f.write(rewritten)
    print("README.md updated successfully.")  # Add debug print