from feedparser import parse
import httpx
import pathlib
import re

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r'<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->'.format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = '<!-- {} starts -->{}<!-- {} ends -->'.format(marker, chunk, marker)
    return r.sub(chunk, content)

def fetch_weekly():
    response = httpx.get('https://raw.githubusercontent.com/chilohwei/weekly/main/RECENT.md')
    return response.text.split('\n')  # split the text by line

def fetch_blog_entries():
    entries = parse('https://blog.chiloh.cn/feed.xml')['entries']
    return [
        {
            'title': entry['title'],
            'url': entry['link'].split('#')[0],
            'published': entry['published'].split('T')[0],
        }
        for entry in entries
    ]

if __name__ == "__main__":
    readme = root / "README.md"

    # Fetch and update weekly content
    weekly_text = fetch_weekly()
    weekly_text_md = "\n".join([f"* [{line}]()" for line in weekly_text])

    with open(readme, 'r') as f:
        readme_contents = f.read()
    rewritten = replace_chunk(readme_contents, "weekly", weekly_text_md)

    # Fetch and update blog entries
    entries = fetch_blog_entries()[:5]
    entries_md = "\n".join([f"* <a href='{entry['url']}' target='_blank'>{entry['title']}</a> - {entry['published']}" for entry in entries])
    rewritten = replace_chunk(rewritten, "blog", entries_md)

    # Write back to README.md
    with open(readme, 'w') as f:
        f.write(rewritten)