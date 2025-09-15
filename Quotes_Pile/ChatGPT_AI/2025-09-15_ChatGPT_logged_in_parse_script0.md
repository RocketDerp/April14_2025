please create a python shell program to process this file an verify the links have the specified comments. https://github.com/RocketDerp/April14_2025/blob/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md

ChatGPT said:

It looks like I can’t open that GitHub link directly. Could you either:

Upload the Today_Reddit_Comment.md file here, or

Paste a sample of its contents (maybe 10–20 lines),

so I can see the format?

Once I know how the links and comments are structured, I’ll create a Python shell program that reads the file, extracts the links, and verifies that each one has the specified comment.

Do you want the verification to mean:

that the comment text exists directly after the link in the file, or

that the actual Reddit link contains that comment when fetched online?

You said:
Can you access this file? https://github.com/RocketDerp/April14_2025/blob/main/Quotes_Pile/ChatGPT_AI/sample_Reddit_Quotes0.md
ChatGPT said:

I got a view of the file page, but the raw contents aren’t visible in the snippet I saw. I couldn’t inspect the actual Markdown text (links, comments, etc.).

If you want, I can try fetching the raw content, or you could paste a few lines here, and I’ll write the Python script based on that format. Do you want me to fetch the raw or go ahead with sample lines you provide?

You said:
Here is raw link: https://raw.githubusercontent.com/RocketDerp/April14_2025/refs/heads/main/Quotes_Pile/ChatGPT_AI/sample_Reddit_Quotes0.md
ChatGPT said:

Here’s a Python shell (CLI) program you can use to process files like sample_Reddit_Quotes0.md, extract links, and verify that each link in a Reddit quote block has an associated “commentary” (or “specified comment”) in a specified format. I’ll also include notes / assumptions so you can adapt as needed.

Assumptions

Looking at your sample file, I see lines like:

https://old.reddit.com/.../ne61y29/ HeyItsBobaTime 2018-07-24 "..."   https://old.reddit.com/.../necqt11/ AggravatingSpace5854 2025-08-05 (sometimes commentary about the account goes here.
...
* :::=== RoundSparrow_Commentary : Monomyth fiction patterns.
...


So some patterns:

Each quote has a Reddit link, a username, a date, then the quote text in quotes.

There may be an optional commentary line associated with a quote, starting with something like * :::=== CommentaryName : text… or :::=== ... etc.

Sometimes other extra lines (image, etc.).

You want to verify “the links have the specified comments.” I interpret that as: for each Reddit link, there should be a commentary (or some comment text) present in the file associated with that quote.

We’ll write a script that:

Reads the file

Finds all Reddit links (old.reddit.com or reddit.com/r/...)

Groups them per quote (we’ll assume that whenever a link is followed by the quote text and ends before the next link, that block is one quote)

Checks whether there is a commentary line in that block

Reports links (or quote identifiers) missing commentary

You can adjust what counts as “commentary” by the regex.

Python Program

Save this script (e.g. verify_quotes.py), run as e.g. python verify_quotes.py path/to/sample_Reddit_Quotes0.md

#!/usr/bin/env python3
import re
import sys

def extract_quote_blocks(lines):
    """
    Splits the file into blocks, each block corresponding roughly to one quote.
    A block starts at a line containing a Reddit comment link, and continues
    until the next such line.
    Returns list of blocks, each block is list of lines.
    """
    blocks = []
    current = []
    link_pattern = re.compile(r'https?://(?:old\.)?reddit\.com/r/[^ ]+')
    for line in lines:
        if link_pattern.search(line):
            # if we already have a block in progress, start a new one
            if current:
                blocks.append(current)
                current = []
        current.append(line)
    if current:
        blocks.append(current)
    return blocks

def find_links(block):
    """Return all reddit links in a block."""
    link_pattern = re.compile(r'(https?://(?:old\.)?reddit\.com/r/[^ )"\']+)')
    links = link_pattern.findall(" ".join(block))
    return links

def has_commentary(block):
    """
    Determine if block has commentary. Define commentary as a line
    that matches something like:
        * :::=== SomeName_Commentary : text...
    or
        :::=== SomeName_Commentary : text...
    Adjust regex if your format differs.
    """
    commentary_pattern = re.compile(r':::+\s*[A-Za-z0-9_]+_Commentary\s*:')
    for line in block:
        if commentary_pattern.search(line):
            return True
    return False

def main(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = extract_quote_blocks(lines)
    missing = []  # list of (block_index, links) for blocks missing commentary

    for i, block in enumerate(blocks):
        links = find_links(block)
        if not has_commentary(block):
            missing.append( (i, links) )

    if not missing:
        print("All quote blocks have commentary.")
    else:
        print(f"Found {len(missing)} quote block(s) missing commentary:")
        for idx, links in missing:
            print(f" Block #{idx+1}: links ->")
            for l in links:
                print(f"    {l}")
        sys.exit(1)  # non-zero exit code if missing

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_quotes.py <path_to_md_file>")
        sys.exit(1)
    filepath = sys.argv[1]
    main(filepath)

How to Adapt / Improve

Changing what counts as a “commentary”: You may have other formats (maybe not _Commentary, maybe Commentary without underscore, or other markers). You can adjust the commentary_pattern regex accordingly.

Dealing with multiple links in one block: The script finds all Reddit links in a block; you may want to ensure each link (or maybe only the first) has a commentary.

Handling edge cases:

If a quote spans multiple lines, or commentary is embedded in the same line, etc.

If link lines are broken, etc.

Online verification: If by “verify links” you meant to fetch each Reddit link over HTTP to see if it’s valid (returns 200), then you could add an requests.get(link) check.

Better block segmentation: The “block” definition here is simplistic; depending on your real file format you may want to detect start and end more precisely.

If you like, I can build a more robust version for your exact file format (including more sample files), or include fetching the link to check whether the link is valid / live. Do you want me to prepare that?

You said:
the commentary is optional, not on every entry. The start of the entry is the old.redditc.com URL link
ChatGPT said:

Got it 👍 thanks for clarifying.
So:

Every entry begins with an old.reddit.com URL.

Each entry may contain metadata (username, date, quote text, etc.).

A commentary line is optional, so the script should not treat “missing commentary” as an error—just report whether it exists or not.

Here’s a revised Python shell program:

#!/usr/bin/env python3
import re
import sys

ENTRY_START = re.compile(r'^https?://old\.reddit\.com/')

def parse_entries(lines):
    """
    Split file into entries. Each entry starts with a line beginning
    with an old.reddit.com URL and continues until the next such line.
    """
    entries = []
    current = []
    for line in lines:
        if ENTRY_START.match(line.strip()):
            if current:
                entries.append(current)
                current = []
        current.append(line.rstrip("\n"))
    if current:
        entries.append(current)
    return entries

def get_link(entry):
    """Return the first reddit link in the entry."""
    for line in entry:
        m = ENTRY_START.match(line.strip())
        if m:
            return line.strip()
    return None

def has_commentary(entry):
    """
    Check if an entry has commentary.
    We define commentary as any line that starts with ':::' or '* :::'
    and contains the word 'Commentary'.
    """
    commentary_pattern = re.compile(r':::+.*Commentary', re.IGNORECASE)
    for line in entry:
        if commentary_pattern.search(line):
            return True
    return False

def main(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = parse_entries(lines)

    for idx, entry in enumerate(entries, start=1):
        link = get_link(entry)
        commentary_flag = has_commentary(entry)
        print(f"Entry {idx}: {link}")
        print("  Commentary:", "YES" if commentary_flag else "NO")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_reddit_file.py <path_to_md_file>")
        sys.exit(1)
    main(sys.argv[1])

Example Output

If your file has 3 entries, the program might print:

Entry 1: https://old.reddit.com/r/example/comments/abc123/xyz/
  Commentary: NO
Entry 2: https://old.reddit.com/r/example/comments/def456/qwe/
  Commentary: YES
Entry 3: https://old.reddit.com/r/example/comments/ghi789/rty/
  Commentary: NO


Would you also like me to extend this so it checks if each Reddit link is still live (HTTP 200), or is it enough to just parse the Markdown file and report the presence/absence of commentary?

You said:
yes, and compare the current comment off live Reddit with the one in the markdown file
ChatGPT said:

Perfect, thanks for clarifying. That means the script now has to do three jobs per entry:

Parse the Markdown file → get the Reddit link, the quoted text, and any optional commentary.

Fetch the live Reddit comment text (via requests or httpx) from the link.

Compare the stored quote text vs. the live comment text, and report whether they match.

⚠️ A couple of important notes about Reddit:

Old-style Reddit comment permalinks like https://old.reddit.com/r/.../comments/.../id/ will render HTML, not JSON. To reliably fetch the raw comment text, you can append .json to the permalink (Reddit serves structured JSON with the comment body).

Example:

https://www.reddit.com/r/<sub>/comments/<postid>/<slug>/<commentid>.json


Without authentication, Reddit’s API limits requests. If you’ll be checking many comments, you may want to insert a short delay between requests.

Full Python Script
#!/usr/bin/env python3
import re
import sys
import requests
import time

ENTRY_START = re.compile(r'^https?://old\.reddit\.com/')

def parse_entries(lines):
    """
    Split file into entries. Each entry starts with a line beginning
    with an old.reddit.com URL and continues until the next such line.
    """
    entries = []
    current = []
    for line in lines:
        if ENTRY_START.match(line.strip()):
            if current:
                entries.append(current)
                current = []
        current.append(line.rstrip("\n"))
    if current:
        entries.append(current)
    return entries

def get_link(entry):
    """Return the first reddit link in the entry."""
    for line in entry:
        if ENTRY_START.match(line.strip()):
            return line.strip()
    return None

def extract_quote_text(entry):
    """
    Extract the quoted text inside quotes "..."
    (first occurrence). Returns None if not found.
    """
    joined = " ".join(entry)
    m = re.search(r'"([^"]+)"', joined)
    if m:
        return m.group(1).strip()
    return None

def has_commentary(entry):
    """
    Check if an entry has commentary.
    """
    commentary_pattern = re.compile(r':::+.*Commentary', re.IGNORECASE)
    for line in entry:
        if commentary_pattern.search(line):
            return True
    return False

def fetch_live_comment_text(link):
    """
    Fetch the live comment text from Reddit by appending .json to the permalink.
    Returns the body text if found, else None.
    """
    # Convert old.reddit.com -> www.reddit.com
    url = link.replace("old.reddit.com", "www.reddit.com")
    if not url.endswith(".json"):
        if url.endswith("/"):
            url = url + ".json"
        else:
            url = url + ".json"

    headers = {"User-Agent": "RedditVerifier/0.1 by YourName"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Drill down: [post, [comment]]
        if isinstance(data, list) and len(data) > 1:
            comments = data[1].get("data", {}).get("children", [])
            if comments:
                body = comments[0]["data"].get("body")
                return body.strip() if body else None
    except Exception as e:
        print(f"  [Error fetching {url}: {e}]")
    return None

def main(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = parse_entries(lines)

    for idx, entry in enumerate(entries, start=1):
        link = get_link(entry)
        stored_quote = extract_quote_text(entry)
        commentary_flag = has_commentary(entry)

        print(f"\nEntry {idx}: {link}")
        print("  Commentary:", "YES" if commentary_flag else "NO")
        print("  Stored quote:", f"\"{stored_quote}\"" if stored_quote else "None found")

        if link:
            live_comment = fetch_live_comment_text(link)
            if live_comment:
                # Normalize whitespace for comparison
                norm_stored = " ".join(stored_quote.split()) if stored_quote else ""
                norm_live = " ".join(live_comment.split())
                match = (norm_stored == norm_live)
                print("  Live comment fetched:", f"\"{live_comment}\"")
                print("  Match:", "YES" if match else "NO")
            else:
                print("  Could not fetch live comment.")

            time.sleep(1)  # politeness delay

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_reddit_file.py <path_to_md_file>")
        sys.exit(1)
    main(sys.argv[1])

What it Does

Splits the Markdown into entries.

For each entry:

Prints the Reddit link.

Shows if commentary exists.

Extracts the stored quote ("...").

Fetches the live comment body via Reddit’s JSON API.

Compares stored vs. live text (ignoring extra whitespace).

Do you want me to also make it tolerant of partial matches (e.g., check if the stored quote is a substring of the live comment), in case the markdown file only keeps an excerpt instead of the full text?

You said:
stick to the html link parsing, not JSON
ChatGPT said:

Got it 👍 — you want to stick to parsing the HTML pages instead of using Reddit’s .json API.

That means:

Fetch the permalink (old.reddit.com/...) directly.

Parse the HTML to extract the comment body.

Compare that text with the stored quote in your Markdown.

We can do this cleanly with BeautifulSoup (bs4) to extract the <div class="md"> or <div class="usertext-body"> inside the comment element.

Python Program (HTML Parsing)
#!/usr/bin/env python3
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

ENTRY_START = re.compile(r'^https?://old\.reddit\.com/')

def parse_entries(lines):
    """
    Split file into entries. Each entry starts with a line beginning
    with an old.reddit.com URL and continues until the next such line.
    """
    entries = []
    current = []
    for line in lines:
        if ENTRY_START.match(line.strip()):
            if current:
                entries.append(current)
                current = []
        current.append(line.rstrip("\n"))
    if current:
        entries.append(current)
    return entries

def get_link(entry):
    """Return the first reddit link in the entry."""
    for line in entry:
        if ENTRY_START.match(line.strip()):
            return line.strip()
    return None

def extract_quote_text(entry):
    """
    Extract the quoted text inside quotes "..."
    (first occurrence). Returns None if not found.
    """
    joined = " ".join(entry)
    m = re.search(r'"([^"]+)"', joined)
    if m:
        return m.group(1).strip()
    return None

def has_commentary(entry):
    """Check if an entry has commentary."""
    commentary_pattern = re.compile(r':::+.*Commentary', re.IGNORECASE)
    for line in entry:
        if commentary_pattern.search(line):
            return True
    return False

def fetch_live_comment_text(link):
    """
    Fetch the live Reddit comment text by scraping HTML.
    Returns the first comment body text, or None if not found.
    """
    headers = {"User-Agent": "RedditVerifier/0.1 by YourName"}
    try:
        r = requests.get(link, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # On old.reddit.com, comment bodies are in div.usertext-body > div.md
        body_divs = soup.select("div.comment div.usertext-body div.md")
        if body_divs:
            # Get plain text of the first one
            return body_divs[0].get_text(" ", strip=True)
    except Exception as e:
        print(f"  [Error fetching {link}: {e}]")
    return None

def main(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = parse_entries(lines)

    for idx, entry in enumerate(entries, start=1):
        link = get_link(entry)
        stored_quote = extract_quote_text(entry)
        commentary_flag = has_commentary(entry)

        print(f"\nEntry {idx}: {link}")
        print("  Commentary:", "YES" if commentary_flag else "NO")
        print("  Stored quote:", f"\"{stored_quote}\"" if stored_quote else "None found")

        if link:
            live_comment = fetch_live_comment_text(link)
            if live_comment:
                # Normalize whitespace for comparison
                norm_stored = " ".join(stored_quote.split()) if stored_quote else ""
                norm_live = " ".join(live_comment.split())
                match = (norm_stored == norm_live)
                print("  Live comment fetched:", f"\"{live_comment}\"")
                print("  Match:", "YES" if match else "NO")
            else:
                print("  Could not fetch live comment.")

            time.sleep(1)  # politeness delay

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_reddit_file_html.py <path_to_md_file>")
        sys.exit(1)
    main(sys.argv[1])

What This Does

Reads your Markdown file.

Each entry = starts with an old.reddit.com link → collects until next one.

Extracts the quote ("...").

Fetches the HTML page for that Reddit comment.

Finds the <div class="md"> text for the first comment in that thread.

Compares normalized text (ignores extra whitespace).

Do you want me to make the comparison less strict (e.g., treat the Markdown quote as a substring of the live comment) instead of requiring an exact match? That might help when you only store excerpts.


&nbsp;

&nbsp;

&nbsp;

# copy code blocks

```python
#!/usr/bin/env python3
import re
import sys

def extract_quote_blocks(lines):
    """
    Splits the file into blocks, each block corresponding roughly to one quote.
    A block starts at a line containing a Reddit comment link, and continues
    until the next such line.
    Returns list of blocks, each block is list of lines.
    """
    blocks = []
    current = []
    link_pattern = re.compile(r'https?://(?:old\.)?reddit\.com/r/[^ ]+')
    for line in lines:
        if link_pattern.search(line):
            # if we already have a block in progress, start a new one
            if current:
                blocks.append(current)
                current = []
        current.append(line)
    if current:
        blocks.append(current)
    return blocks

def find_links(block):
    """Return all reddit links in a block."""
    link_pattern = re.compile(r'(https?://(?:old\.)?reddit\.com/r/[^ )"\']+)')
    links = link_pattern.findall(" ".join(block))
    return links

def has_commentary(block):
    """
    Determine if block has commentary. Define commentary as a line
    that matches something like:
        * :::=== SomeName_Commentary : text...
    or
        :::=== SomeName_Commentary : text...
    Adjust regex if your format differs.
    """
    commentary_pattern = re.compile(r':::+\s*[A-Za-z0-9_]+_Commentary\s*:')
    for line in block:
        if commentary_pattern.search(line):
            return True
    return False

def main(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = extract_quote_blocks(lines)
    missing = []  # list of (block_index, links) for blocks missing commentary

    for i, block in enumerate(blocks):
        links = find_links(block)
        if not has_commentary(block):
            missing.append( (i, links) )

    if not missing:
        print("All quote blocks have commentary.")
    else:
        print(f"Found {len(missing)} quote block(s) missing commentary:")
        for idx, links in missing:
            print(f" Block #{idx+1}: links ->")
            for l in links:
                print(f"    {l}")
        sys.exit(1)  # non-zero exit code if missing

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_quotes.py <path_to_md_file>")
        sys.exit(1)
    filepath = sys.argv[1]
    main(filepath)

```

&nbsp;

&nbsp;

second code block:

```python
#!/usr/bin/env python3
import re
import sys

ENTRY_START = re.compile(r'^https?://old\.reddit\.com/')

def parse_entries(lines):
    """
    Split file into entries. Each entry starts with a line beginning
    with an old.reddit.com URL and continues until the next such line.
    """
    entries = []
    current = []
    for line in lines:
        if ENTRY_START.match(line.strip()):
            if current:
                entries.append(current)
                current = []
        current.append(line.rstrip("\n"))
    if current:
        entries.append(current)
    return entries

def get_link(entry):
    """Return the first reddit link in the entry."""
    for line in entry:
        m = ENTRY_START.match(line.strip())
        if m:
            return line.strip()
    return None

def has_commentary(entry):
    """
    Check if an entry has commentary.
    We define commentary as any line that starts with ':::' or '* :::'
    and contains the word 'Commentary'.
    """
    commentary_pattern = re.compile(r':::+.*Commentary', re.IGNORECASE)
    for line in entry:
        if commentary_pattern.search(line):
            return True
    return False

def main(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = parse_entries(lines)

    for idx, entry in enumerate(entries, start=1):
        link = get_link(entry)
        commentary_flag = has_commentary(entry)
        print(f"Entry {idx}: {link}")
        print("  Commentary:", "YES" if commentary_flag else "NO")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_reddit_file.py <path_to_md_file>")
        sys.exit(1)
    main(sys.argv[1])

```

&nbsp;

&nbsp;

&nbsp;

&nbsp;

# Start over

&nbsp;

Start over, focus on the old.reddit.com link  being the start of each entry
ChatGPT said:

Perfect — let’s start fresh and keep it focused.
We’ll treat your file as a list of entries, where:

Each entry begins with a line containing an old.reddit.com link.

The entry continues until the next old.reddit.com link or the end of file.

Inside the entry we can capture:

the stored quote (the first "..." block of text, if present),

whether commentary exists (look for lines like ::: containing Commentary),

and then we’ll fetch the live comment text from Reddit (scraping HTML, as you asked).

Finally, we’ll compare stored quote vs. live comment.

Python Script
#!/usr/bin/env python3
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

# --- Regex to detect entry start
ENTRY_START = re.compile(r'^https?://old\.reddit\.com/')

def parse_entries(lines):
    """
    Split the file into entries.
    Each entry starts with an old.reddit.com link.
    """
    entries = []
    current = []
    for line in lines:
        if ENTRY_START.match(line.strip()):
            if current:
                entries.append(current)
                current = []
        current.append(line.rstrip("\n"))
    if current:
        entries.append(current)
    return entries

def get_link(entry):
    """Return the entry's first reddit link (the header)."""
    for line in entry:
        if ENTRY_START.match(line.strip()):
            return line.strip()
    return None

def extract_quote(entry):
    """Extract the first quoted string ("...") in the entry."""
    text = " ".join(entry)
    m = re.search(r'"([^"]+)"', text)
    return m.group(1).strip() if m else None

def has_commentary(entry):
    """Check if commentary is present in the entry."""
    for line in entry:
        if "Commentary" in line and ":::=" in line:
            return True
    return False

def fetch_comment_html(link):
    """
    Fetch the live comment text from an old.reddit.com permalink.
    Returns plain text of the first comment body, or None.
    """
    headers = {"User-Agent": "RedditVerifier/0.1"}
    try:
        r = requests.get(link, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Old reddit: comment bodies live in div.comment > div.usertext-body > div.md
        div = soup.select_one("div.comment div.usertext-body div.md")
        if div:
            return div.get_text(" ", strip=True)
    except Exception as e:
        print(f"  [Error fetching {link}: {e}]")
    return None

def compare_text(stored, live):
    """
    Compare stored vs. live text with whitespace normalization.
    """
    if not stored or not live:
        return False
    norm_stored = " ".join(stored.split())
    norm_live = " ".join(live.split())
    return norm_stored == norm_live

def main(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = parse_entries(lines)

    for idx, entry in enumerate(entries, 1):
        link = get_link(entry)
        stored_quote = extract_quote(entry)
        commentary = has_commentary(entry)

        print(f"\nEntry {idx}")
        print(f"  Link       : {link}")
        print(f"  Commentary : {'YES' if commentary else 'NO'}")
        print(f"  Stored     : \"{stored_quote}\"" if stored_quote else "  Stored     : None")

        if link:
            live_text = fetch_comment_html(link)
            if live_text:
                match = compare_text(stored_quote, live_text)
                print(f"  Live       : \"{live_text}\"")
                print(f"  Match      : {'YES' if match else 'NO'}")
            else:
                print("  Live       : Could not fetch")

        time.sleep(1)  # politeness delay

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_reddit_entries.py <path_to_md_file>")
        sys.exit(1)
    main(sys.argv[1])

What it does

Splits your Markdown file into entries (old.reddit.com link = start).

For each entry, it shows:

The link

Whether commentary exists

The stored quote (first "..." in entry)

The live comment text (scraped from HTML)

Whether they match

Do you want the comparison to require exact match (as in now), or should it be relaxed to allow the stored quote to be just an excerpt / substring of the live comment?

&nbsp;

&nbsp;

# Code block from start over

&nbsp;

```python
#!/usr/bin/env python3
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

# --- Regex to detect entry start
ENTRY_START = re.compile(r'^https?://old\.reddit\.com/')

def parse_entries(lines):
    """
    Split the file into entries.
    Each entry starts with an old.reddit.com link.
    """
    entries = []
    current = []
    for line in lines:
        if ENTRY_START.match(line.strip()):
            if current:
                entries.append(current)
                current = []
        current.append(line.rstrip("\n"))
    if current:
        entries.append(current)
    return entries

def get_link(entry):
    """Return the entry's first reddit link (the header)."""
    for line in entry:
        if ENTRY_START.match(line.strip()):
            return line.strip()
    return None

def extract_quote(entry):
    """Extract the first quoted string ("...") in the entry."""
    text = " ".join(entry)
    m = re.search(r'"([^"]+)"', text)
    return m.group(1).strip() if m else None

def has_commentary(entry):
    """Check if commentary is present in the entry."""
    for line in entry:
        if "Commentary" in line and ":::=" in line:
            return True
    return False

def fetch_comment_html(link):
    """
    Fetch the live comment text from an old.reddit.com permalink.
    Returns plain text of the first comment body, or None.
    """
    headers = {"User-Agent": "RedditVerifier/0.1"}
    try:
        r = requests.get(link, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Old reddit: comment bodies live in div.comment > div.usertext-body > div.md
        div = soup.select_one("div.comment div.usertext-body div.md")
        if div:
            return div.get_text(" ", strip=True)
    except Exception as e:
        print(f"  [Error fetching {link}: {e}]")
    return None

def compare_text(stored, live):
    """
    Compare stored vs. live text with whitespace normalization.
    """
    if not stored or not live:
        return False
    norm_stored = " ".join(stored.split())
    norm_live = " ".join(live.split())
    return norm_stored == norm_live

def main(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = parse_entries(lines)

    for idx, entry in enumerate(entries, 1):
        link = get_link(entry)
        stored_quote = extract_quote(entry)
        commentary = has_commentary(entry)

        print(f"\nEntry {idx}")
        print(f"  Link       : {link}")
        print(f"  Commentary : {'YES' if commentary else 'NO'}")
        print(f"  Stored     : \"{stored_quote}\"" if stored_quote else "  Stored     : None")

        if link:
            live_text = fetch_comment_html(link)
            if live_text:
                match = compare_text(stored_quote, live_text)
                print(f"  Live       : \"{live_text}\"")
                print(f"  Match      : {'YES' if match else 'NO'}")
            else:
                print("  Live       : Could not fetch")

        time.sleep(1)  # politeness delay

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_reddit_entries.py <path_to_md_file>")
        sys.exit(1)
    main(sys.argv[1])
```
