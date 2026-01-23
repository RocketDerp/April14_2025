import json
import re
from html import unescape

# Process Mastodon save file for GitHub Markdown output

# global vars
postcount = 0


def to_github_markdown(html_content):
    if not html_content:
        return ""

    # 1. Handle line breaks: Replace <p> with newlines and <br> with a single newline
    md = html_content.replace('</p><p>', '\n\n')
    md = re.sub(r'<p>|</p>', '', md)
    md = md.replace('<br>', '\n').replace('<br/>', '\n')

    # preserve the CamelCase 
    # 2. Extract Hashtags: Convert to [#tag](hashtags.md#tag) - Preserving Case
    # This targets the specific Mastodon span structure and points to your local file
    hashtag_pattern = r'<a href="[^"]+" class="mention hashtag" rel="tag">#<span>([^<]+)</span></a>'
    
    # \1 represents the captured tag name (e.g., FWakeAge32)
    md = re.sub(hashtag_pattern, r'[#\1](HashTags.md#\1)', md)

    # 3. Regular Links: Convert remaining <a href="URL">text</a> to [text](URL)
    link_pattern = r'<a href="([^"]+)"[^>]*>(.*?)</a>'
    md = re.sub(link_pattern, r'[\2](\1)', md)

    # 4. Clean remaining HTML tags (like <span> used for ellipses in links)
    md = re.sub(r'<.*?>', '', md)

    # 5. Decode HTML entities (like &amp; or &quot;)
    return unescape(md).strip()


def clean_html(raw_html):
    """Removes HTML tags and converts entities (like &amp;) to plain text."""
    if not raw_html:
        return ""
    # Remove tags
    clean_text = re.sub(r'<.*?>', '', raw_html)
    # Decode HTML entities
    return unescape(clean_text)

def parse_mastodon_export(file_path):
    global postcount

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both single objects and full outbox lists
        items = data.get('orderedItems', [data]) if isinstance(data, dict) else []

        for item in items:
            postcount += 1
            # Mastodon posts are usually 'Create' activities containing a 'Note'
            obj = item.get('object', {})
            if isinstance(obj, dict):
                published = obj.get('published', 'Unknown Date')
                url = obj.get('url', 'No URL')
                content = clean_html(obj.get('content', ''))

                print("\n")
                print(f"--- {published} ---   ")
                print(f"URL: {url}   ")
                # print(f"Content: {content}\n")
                print(to_github_markdown(obj.get('content', '')))


    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")

if __name__ == "__main__":
    # Ensure your export file is named 'outbox.json' or update the path here
    parse_mastodon_export('outbox.json')
    print(f"postcount {postcount}")
