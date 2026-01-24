import sys
import json
import re
from html import unescape
from datetime import date


# Process Mastodon save file for GitHub Markdown output
# this app assumes input data is in date order, oldest to newest

# global vars
postcount = 0
out_file_count = 0
stop_after = 500


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
    global stop_after
    global out_file_count

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both single objects and full outbox lists
        items = data.get('orderedItems', [data]) if isinstance(data, dict) else []
        previous_published = "1970-01-01"
        out_batch_count = 0
        output_filename = None

        for item in items:
            postcount += 1
            # Mastodon posts are usually 'Create' activities containing a 'Note'
            obj = item.get('object', {})
            if isinstance(obj, dict):
                # this is a string, not an intelligent ate object
                published = obj.get('published', 'Unknown Date')
                
                # is thi a month crossing?
                # 1970-01-01-
                if published[:8] == previous_published[:8]:
                    # same year, same month
                    out_batch_count += 1
                else:
                    # detected change of month
                    output_filename = f"Roundsparrow_{published[:7]}.md"
                    print("*********************   \n")
                    out_file_count += 1
                    if out_file_count > 1:
                        print(f"*** previous batch items {out_batch_count}   \n")
                    print(f"*** new file {output_filename} file count: {out_file_count}  \n")
                    out_batch_count = 1
                    
                previous_published = published
                
                url = obj.get('url', 'No URL')
                content = clean_html(obj.get('content', ''))

                print("\n")
                print(f"--- {published} ---   ")
                print(f"URL: {url}   ")
                # print(f"Content: {content}\n")
                print(to_github_markdown(obj.get('content', '')))
            else:
                print ("if instance failed");
                
            if postcount >= stop_after:
                print(f"stop on {postcount}")
                print(f"file count {out_file_count} last batch count {out_batch_count}")
                sys.exit(1)                

    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")


if __name__ == "__main__":
    # Ensure your export file is named 'outbox.json' or update the path here
    parse_mastodon_export('outbox.json')
    print(f"postcount {postcount}")
