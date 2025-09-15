please create a python shell program to process this file an verify the links have the specified comments. https://github.com/RocketDerp/April14_2025/blob/main/Quotes_Pile/Reddit2025A/Today_Reddit_Comment.md
ChatGPT said:

Here’s a Python shell/CLI program that will:

Read the Markdown file (Today_Reddit_Comment.md)

Parse out all links

For each link, check (via HTTP GET) that it is valid (status 200, etc.)

Also check that each link has the “specified comments” (you’ll need to clarify what “specified comments” means — e.g. some text after the link, or a comment in Reddit? I’ll assume you mean that after the link in the file there is a comment line matching some pattern)

Report any broken links or missing/incorrect comments

I’ll write a version that is modular so you can adjust the “specified comment” criteria.

#!/usr/bin/env python3

import re
import sys
import argparse
import requests

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

def extract_links(lines):
    """
    Returns a list of (line_no, link, line_text) for Markdown links.
    Markdown link format: [text](url)
    Also handles bare URLs if needed.
    """
    link_pattern = re.compile(r'\[.*?\]\((https?://[^\s\)]+)\)')
    bare_url_pattern = re.compile(r'(https?://[^\s\)]+)')
    results = []
    for i, line in enumerate(lines, start=1):
        for m in link_pattern.finditer(line):
            url = m.group(1)
            results.append( (i, url, line.strip()) )
        # Optionally, detect bare URLs:
        # for m in bare_url_pattern.finditer(line):
        #     url = m.group(1)
        #     results.append( (i, url, line.strip()) )
    return results

def check_link(url, timeout=10):
    """
    Returns (ok, status_code or exception_str)
    """
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        # Some servers don't respond well to HEAD; optionally fallback to GET
        if resp.status_code >= 400 or resp.status_code < 200:
            # try GET
            resp2 = requests.get(url, allow_redirects=True, timeout=timeout)
            return (resp2.status_code == 200, resp2.status_code)
        return (True, resp.status_code)
    except Exception as e:
        return (False, str(e))

def check_specified_comment_after(lines, link_line_no, pattern, max_lookahead=3):
    """
    After the line containing the link, look in the next max_lookahead lines
    to see if there's a comment matching `pattern` (regex).
    Returns True if found, False otherwise.
    """
    pat = re.compile(pattern)
    for offset in range(1, max_lookahead+1):
        idx = link_line_no -1 + offset
        if idx < len(lines):
            if pat.search(lines[idx]):
                return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Verify links in Markdown file have specified comments")
    parser.add_argument("mdfile", help="Path to the markdown file")
    parser.add_argument("--comment-pattern", help="Regex pattern that must appear after each link", required=True)
    parser.add_argument("--max-lookahead", type=int, default=3, help="How many lines after link to search for comment")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout for link checking")
    args = parser.parse_args()

    lines = read_file(args.mdfile)
    links = extract_links(lines)

    if not links:
        print("No links found.")
        sys.exit(0)

    bad_links = []
    missing_comments = []

    print(f"Found {len(links)} links. Checking...")

    for (lineno, url, line_text) in links:
        ok, status = check_link(url, timeout=args.timeout)
        if not ok:
            bad_links.append( (lineno, url, status) )

        has_comment = check_specified_comment_after(lines, lineno, args.comment_pattern, args.max_lookahead)
        if not has_comment:
            missing_comments.append( (lineno, url) )

    print("\n=== Results ===\n")

    if bad_links:
        print("Broken links or non-200 responses:")
        for (lineno, url, status) in bad_links:
            print(f"  Line {lineno}: {url} --> {status}")
    else:
        print("All links returned OK status.")

    if missing_comments:
        print("\nLinks missing specified comment pattern within next"
              f" {args.max_lookahead} lines:")
        for (lineno, url) in missing_comments:
            print(f"  Line {lineno}: {url}")
    else:
        print("All links have the specified comment pattern following.")

    # Exit code: non-zero if any errors
    if bad_links or missing_comments:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

How to adapt/use:

Place this script in a file, e.g. verify_links.py

Make it executable (chmod +x verify_links.py)

Run it like:

./verify_links.py Today_Reddit_Comment.md --comment-pattern="YourRequiredPatternHere"


Replace "YourRequiredPatternHere" with the regex that defines what the “specified comments” should look like.
For example, if every link should be followed by a line starting with > Comment: then you might use ^> Comment: as the pattern.

You can adjust --max-lookahead to control how many lines after the link you want to search for the comment.

The script uses requests library so make sure you have it installed (pip install requests).

If you tell me exactly what “specified comments” means in your case (e.g. “every link must have the Reddit comment’s author & score in the next line”, or “must have a line with ‘Commented by: ...’ after link”, or something else), I can adjust this script to match that more precisely. Do you want me to build that specific version for your file?


&nbsp;

&nbsp;

&nbsp;

&nbsp;

To answer your question at the end.  there is a &nbsp , then a link to old.reddit.com line, then a line with Reddit username and Reddit account creation date, then the next lines are quoted (") of the comment. Then an optional RoundSparrow_Commentary section on a * bullet
ChatGPT said:

Thanks for the clarification. Based on your structure, here's how the file content appears to be formatted:

File Format Structure:

A line containing &nbsp;

Next line: A Reddit comment link (https://old.reddit.com/...)

Next line: A Reddit username and account creation date

Following lines: One or more lines starting with " — these are quoted Reddit comments

Optionally: A bullet point * line for RoundSparrow_Commentary

🎯 Goal:

Write a Python script that:

Finds each Reddit comment link

Verifies:

It's preceded by &nbsp; (or nearby)

Followed by:

A username and account creation date line

At least one line that starts with "

(Optional) A bullet line starting with * for RoundSparrow commentary

Validates the Reddit link works (e.g. responds with status 200)

✅ Here's the Python Shell Script:
#!/usr/bin/env python3

import re
import sys
import requests

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

def is_reddit_link(line):
    return 'https://old.reddit.com/' in line

def check_reddit_link(url, timeout=10):
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        return r.status_code == 200
    except:
        return False

def process_blocks(lines):
    i = 0
    errors = []

    while i < len(lines):
        line = lines[i].strip()

        # Look for the Reddit link
        if is_reddit_link(line):
            link = line
            context = {"link_line": i+1, "link": link}

            # Check for &nbsp; within the last 2 lines
            if i >= 1 and '&nbsp' in lines[i-1]:
                context["nbsp"] = True
            elif i >= 2 and '&nbsp' in lines[i-2]:
                context["nbsp"] = True
            else:
                context["nbsp"] = False

            # Check the username/date line
            if i+1 < len(lines):
                context["username_line"] = lines[i+1].strip()
                context["has_username_line"] = True
            else:
                context["has_username_line"] = False

            # Collect comment quote lines
            comment_lines = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith('"'):
                comment_lines.append(lines[j].strip())
                j += 1
            context["quoted_lines"] = comment_lines
            context["has_comment"] = len(comment_lines) > 0

            # Optional: RoundSparrow commentary on a bullet line
            if j < len(lines) and lines[j].strip().startswith("*"):
                context["has_commentary"] = True
            else:
                context["has_commentary"] = False

            # Check if the link is valid
            context["link_ok"] = check_reddit_link(link)

            # Report any issues
            issues = []
            if not context["nbsp"]:
                issues.append("Missing &nbsp; before link")
            if not context["has_username_line"]:
                issues.append("Missing username/date line")
            if not context["has_comment"]:
                issues.append("Missing quoted comment lines")
            if not context["link_ok"]:
                issues.append("Reddit link not accessible (broken?)")

            if issues:
                errors.append((context["link_line"], link, issues))

            # Move to the next block
            i = j
        else:
            i += 1

    return errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 verify_reddit_md.py Today_Reddit_Comment.md")
        sys.exit(1)

    filepath = sys.argv[1]
    lines = read_file(filepath)
    errors = process_blocks(lines)

    if not errors:
        print("✅ All Reddit comment blocks look valid.")
    else:
        print("❌ Issues found in the following blocks:\n")
        for lineno, link, issues in errors:
            print(f"Line {lineno}: {link}")
            for issue in issues:
                print(f"  - {issue}")
            print()

if __name__ == "__main__":
    main()

🛠 How to Use

Save it as verify_reddit_md.py

Install dependencies:

pip install requests


Run:

python3 verify_reddit_md.py Today_Reddit_Comment.md

🔄 Example Output
Line 142: https://old.reddit.com/r/...
  - Missing &nbsp; before link
  - Reddit link not accessible (broken?)


Would you like this script to also download the Markdown directly from GitHub instead of needing a local file?

&nbsp;

&nbsp;

&nbsp;
